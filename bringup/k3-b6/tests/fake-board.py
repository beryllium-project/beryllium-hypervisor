#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""A stand-in COM260 Fedora host for tests/run-tool-dry-run.sh.

  fake-board.py ssh [SSH OPTIONS] [--] HOST [COMMAND...]
  fake-board.py scp [SCP OPTIONS] [--] SOURCE HOST:/tmp/NAME
  fake-board.py feed CAPTURE SERIAL_LOG

Purpose: let the dry run drive scripts/k3-run.sh, k3-campaign.sh, and
         k3-preflight.sh end to end without a board. The dry run puts `ssh`
         and `scp` wrappers that exec this script first on PATH and names a
         host that cannot resolve, so no command can reach the real board.
         Each command the B6 board tools send is answered as Fedora on the
         COM260 would: identity and /tmp facts; files copied into the
         board's /tmp; sha256sum; the B6 kexec loader, the very copy staged
         in /tmp (or the copy streamed on stdin, for the preflight), run
         with only the kernel interfaces faked (the kexec syscalls,
         /proc/iomem, /sys/firmware/fdt, /sys/kernel/kexec_loaded, the
         machine name); and `systemctl kexec`, which feeds a capture into
         the serial log in chunks from a detached process and, by default,
         stands for the human reset by giving the board a new boot ID. The
         preflight's remote script is answered with the facts B5 and B0
         recorded on the COM260 (bringup/k3-b5/results/20261007-com260 and
         bringup/k3-b0/results/20261006-com260 preflight.txt files).
Trust:   test-only; it never runs a command it receives, and anything it
         does not recognize fails with status 127.
Scope:   B6 board-tool dry run. The board is the directory named by
         FAKE_K3_BOARD: config.json (the scenario), state.json, tmp/ (the
         board's /tmp), commands.log (every command received), and
         kexec-segments.json (the last kexec_load). config.json keys: host,
         iomem (System RAM lines; default B0's record), fdt_reserved (list
         of [low, high)), fdt_bytes, tmp_fstype, sstc_hart0, corrupt_image
         (flip one byte of a copied .img), kexec_capture (a file fed to
         serial_log on `systemctl kexec`; empty: nothing), serial_log, and
         reboot_on_kexec.
"""

import ctypes
import errno
import hashlib
import json
import os
import pathlib
import shlex
import subprocess
import sys
import time
import types

HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE.parents[1]
B0_PREFLIGHT = RESULTS / "k3-b0" / "results" / "20261006-com260" / \
    "preflight.txt"
B5_PREFLIGHT = RESULTS / "k3-b5" / "results" / "20261007-com260" / \
    "preflight.txt"
KERNEL = "7.1.5-201.0.riscv64.omni.fc44.riscv64"
LOCKDOWN = "[none] integrity confidentiality"
SSH_FLAGS = set("nfNtTqv46AaCgKkMsXxYyG")
SSH_VALUES = set("opilOFEJLRDSWwbcemBIQ")
SCP_FLAGS = set("qrpvBCT346")
SCP_VALUES = set("oPiFlcSJ")
FEED_CHUNK = 512


def board():
    path = os.environ.get("FAKE_K3_BOARD")
    if not path:
        sys.exit("fake-board: FAKE_K3_BOARD is not set")
    return pathlib.Path(path)


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def save_json(path, value):
    temporary = path.with_name(path.name + ".new")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def recorded_iomem():
    """B0's recorded System RAM block of /proc/iomem (preflight.txt:18-38)."""
    lines = B0_PREFLIGHT.read_text(encoding="ascii").splitlines()
    start = lines.index("102000000-2ffffffff : System RAM")
    block = [lines[start]]
    for line in lines[start + 1:]:
        if not line.startswith(" "):
            break
        block.append(line)
    return block


def config(root):
    settings = {
        "host": "fedora@fake-k3-board.invalid",
        "iomem": recorded_iomem(),
        "fdt_reserved": [],
        "fdt_bytes": 41088,
        "tmp_fstype": "tmpfs",
        "sstc_hart0": True,
        "corrupt_image": False,
        "kexec_capture": "",
        "serial_log": "",
        "reboot_on_kexec": True,
    }
    settings.update(load_json(root / "config.json", {}))
    return settings


def state(root):
    return load_json(root / "state.json", {
        "boot_id": "00000000-0000-4000-8000-000000000001",
        "boots": 1, "kexec_loaded": 0})


def board_path(root, path):
    """The board-side path inside the fake board, or None."""
    fixed = {
        "/proc/iomem": root / "iomem",
        "/sys/firmware/fdt": root / "fdt",
        "/sys/kernel/kexec_loaded": root / "kexec_loaded",
        "/proc/sys/kernel/kexec_load_disabled": root / "kexec_load_disabled",
    }
    if path in fixed:
        return fixed[path]
    if path.startswith("/tmp/") and "/" not in path[5:] and path[5:]:
        return root / "tmp" / path[5:]
    return None


def prepare(root, settings, current):
    """Write the files the faked kernel interfaces read."""
    (root / "tmp").mkdir(parents=True, exist_ok=True)
    (root / "iomem").write_text("\n".join(settings["iomem"]) + "\n",
                                encoding="ascii")
    (root / "fdt").write_bytes(b"\xd0\x0d\xfe\xed" +
                               bytes(settings["fdt_bytes"] - 4))
    (root / "kexec_loaded").write_text(f"{current['kexec_loaded']}\n",
                                       encoding="ascii")
    (root / "kexec_load_disabled").write_text("0\n", encoding="ascii")


def run_loader(root, settings, current, source, argv):
    """Run the B6 loader's main(ARGV) with faked kernel interfaces."""
    prepare(root, settings, current)
    module = types.ModuleType("kexec_load_on_the_fake_board")
    module.__file__ = argv[0]
    exec(compile(source, argv[0], "exec"), module.__dict__)
    real_open = open

    def board_open(path, *args, **kwargs):
        mapped = board_path(root, str(path))
        if mapped is None:
            raise FileNotFoundError(errno.ENOENT, "not on the fake board",
                                    str(path))
        return real_open(mapped, *args, **kwargs)

    def fake_syscall(number, *args):
        if number == module.SYS_KEXEC_LOAD:
            entry, count, segments, flags = args
            if flags == module.KEXEC_ARCH_X86_64:
                return -1, errno.EINVAL
            if count == 0:
                current["kexec_loaded"] = 0
                return 0, 0
            loaded = [{"mem": f"0x{segments[index].mem:x}",
                       "memsz": f"0x{segments[index].memsz:x}",
                       "bufsz": segments[index].bufsz,
                       "sha256": hashlib.sha256(ctypes.string_at(
                           segments[index].buf,
                           segments[index].bufsz)).hexdigest()}
                      for index in range(count)]
            save_json(root / "kexec-segments.json",
                      {"entry": f"0x{entry:x}", "segments": loaded})
            current["kexec_loaded"] = 1
            return 0, 0
        if number == module.SYS_KEXEC_FILE_LOAD:
            flags = args[-1]
            if flags == module.KEXEC_FILE_PROBE_FLAG:
                return -1, errno.EINVAL
            if flags == module.KEXEC_FILE_UNLOAD:
                current["kexec_loaded"] = 0
                return 0, 0
        return -1, errno.ENOSYS

    module.open = board_open
    module.syscall = fake_syscall
    module.platform = types.SimpleNamespace(machine=lambda: "riscv64",
                                            release=lambda: KERNEL)
    module.fdt_reserved = lambda fdt: [tuple(pair) for pair in
                                       settings["fdt_reserved"]]
    # kexec_loaded() reads the file, which must follow the faked syscalls.
    module.kexec_loaded = lambda: str(current["kexec_loaded"])
    return module.main(argv)


def preflight_answer(settings):
    """The preflight's remote script, answered from the COM260 records."""
    b5 = B5_PREFLIGHT.read_text(encoding="ascii").splitlines()
    b0 = B0_PREFLIGHT.read_text(encoding="ascii").splitlines()
    out = [line for line in b5 if line.split("=", 1)[0] in (
        "captured_utc", "hostname", "kernel", "boot_id", "online_cpus",
        "timebase_frequency")]
    for line in b5:
        if line.startswith(("dt_cpu ", "dt_cpu_extensions ", "cpuinfo ")):
            if not settings["sstc_hart0"] and (
                    line.startswith("dt_cpu node=cpu@0 ") or
                    line.startswith("cpuinfo processor=0 hart=0 ")):
                line = line.replace(" sstc=yes", " sstc=no")
            out.append(line)
    for line in b0:
        key = line.split("=", 1)[0]
        if key in ("machine", "cmdline", "lockdown", "kexec_loaded",
                   "kexec_tool", "python3", "sudo_noninteractive") or \
                line.startswith("CONFIG_"):
            out.append(line)
        elif key == "tmp_fstype":
            out.append(f"tmp_fstype={settings['tmp_fstype']}")
    out.append("iomem_system_ram_begin")
    out += settings["iomem"]
    out.append("iomem_system_ram_end")
    out += [line for line in b0 if line.startswith("[ ")]
    return "\n".join(out) + "\n"


def split_options(args, flags, values):
    """(options, rest) of an ssh or scp argument list."""
    options = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            return options, args[index + 1:]
        if not arg.startswith("-") or len(arg) < 2:
            break
        letter = arg[1]
        if letter in values:
            if len(arg) > 2:
                options.append(arg)
            else:
                options += [arg, args[index + 1]]
                index += 1
        elif all(char in flags for char in arg[1:]):
            options.append(arg)
        else:
            raise SystemExit(f"fake-board: unknown option {arg}")
        index += 1
    return options, args[index:]


def log(root, words):
    with open(root / "commands.log", "a", encoding="utf-8") as handle:
        handle.write(shlex.join(words) + "\n")


def unsupported(command):
    print(f"fake-board: unsupported command: {command}", file=sys.stderr)
    return 127


def ssh(args):
    root = board()
    settings = config(root)
    current = state(root)
    options, rest = split_options(args, SSH_FLAGS, SSH_VALUES)
    log(root, ["ssh"] + args)
    if not rest or rest[0] != settings["host"]:
        print(f"fake-board: ssh to an unexpected host {rest[:1]}",
              file=sys.stderr)
        return 255
    words = rest[1:]
    if "-N" in options or "-O" in options:
        return 0
    command = " ".join(words)
    privileged = command
    for prefix in ("sudo -n ", "sudo "):
        if privileged.startswith(prefix):
            privileged = privileged[len(prefix):]
            break
    status = 0
    if command == "cat /proc/sys/kernel/random/boot_id":
        print(current["boot_id"])
    elif command == "uname -r":
        print(KERNEL)
    elif command == ("cat /sys/kernel/security/lockdown 2>/dev/null || "
                     "echo unavailable"):
        print(LOCKDOWN)
    elif command == "findmnt -n -o FSTYPE /tmp":
        print(settings["tmp_fstype"])
    elif command == "cat /sys/kernel/kexec_loaded":
        print(current["kexec_loaded"])
    elif command.startswith("sha256sum -- "):
        for path in command.split()[2:]:
            mapped = board_path(root, path)
            if mapped is None or not mapped.is_file():
                print(f"sha256sum: {path}: No such file or directory",
                      file=sys.stderr)
                status = 1
                continue
            digest = subprocess.run(["sha256sum", "--", str(mapped)],
                                    capture_output=True, text=True,
                                    check=True).stdout.split()[0]
            print(f"{digest}  {path}")
    elif privileged.startswith("python3 -I /tmp/"):
        # The launcher's isolated interpreter (2026-11-01, rows A and D of
        # the RC3 snapshot reviews): -I is required, so a launcher that
        # drops it is refused here as it would be reviewed there; the fake
        # board runs the staged loader in-process and cannot model the
        # isolation itself (tests/test-kexec-load.py does, on the host).
        words = privileged.split()[2:]
        source = board_path(root, words[0])
        if source is None or not source.is_file():
            print(f"python3: can't open file {words[0]!r}", file=sys.stderr)
            return 2
        status = run_loader(root, settings, current,
                            source.read_text(encoding="utf-8"), words)
    elif privileged.startswith("python3 /tmp/"):
        print("fake-board: the loader must run under python3 -I "
              "(the isolated interpreter); refusing", file=sys.stderr)
        return 126
    elif command == ("if sudo -n true 2>/dev/null; then sudo -n python3 - "
                     "probe; else python3 - probe; fi"):
        status = run_loader(root, settings, current, sys.stdin.read(),
                            ["-", "probe"])
    elif command == "bash -s":
        script = sys.stdin.read()
        if "iomem_system_ram_begin" not in script:
            return unsupported("bash -s without the B6 preflight script")
        sys.stdout.write(preflight_answer(settings))
    elif privileged == "systemctl kexec":
        if current["kexec_loaded"] != 1:
            print("Cannot find the ESP partition mount point.",
                  file=sys.stderr)
            return 1
        if settings["kexec_capture"]:
            subprocess.Popen([sys.executable, "-B", __file__, "feed",
                              settings["kexec_capture"],
                              settings["serial_log"]],
                             stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             start_new_session=True)
        current["kexec_loaded"] = 0
        if settings["reboot_on_kexec"]:
            current["boots"] += 1
            current["boot_id"] = f"00000000-0000-4000-8000-" \
                f"{current['boots']:012d}"
    else:
        return unsupported(command)
    save_json(root / "state.json", current)
    return status


def scp(args):
    root = board()
    settings = config(root)
    _, rest = split_options(args, SCP_FLAGS, SCP_VALUES)
    log(root, ["scp"] + args)
    if len(rest) != 2 or not rest[1].startswith(settings["host"] + ":"):
        print(f"fake-board: unexpected scp {rest}", file=sys.stderr)
        return 1
    target = board_path(root, rest[1][len(settings["host"]) + 1:])
    if target is None or not target.parent.name == "tmp":
        print(f"fake-board: scp refused outside /tmp: {rest[1]}",
              file=sys.stderr)
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray(pathlib.Path(rest[0]).read_bytes())
    if settings["corrupt_image"] and target.suffix == ".img":
        data[len(data) // 2] ^= 0x01
    target.write_bytes(bytes(data))
    return 0


def feed(capture, serial_log):
    """Append CAPTURE to SERIAL_LOG in chunks, as a UART would."""
    data = pathlib.Path(capture).read_bytes()
    time.sleep(0.5)
    with open(serial_log, "ab") as handle:
        for start in range(0, len(data), FEED_CHUNK):
            handle.write(data[start:start + FEED_CHUNK])
            handle.flush()
            time.sleep(0.05)
    return 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "ssh":
        return ssh(argv[2:])
    if len(argv) >= 2 and argv[1] == "scp":
        return scp(argv[2:])
    if len(argv) == 4 and argv[1] == "feed":
        return feed(argv[2], argv[3])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
