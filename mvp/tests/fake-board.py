#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# A copy of B7's tests/fake-board.py (accepted at 7b6b846b) with the
# counted changes listed in mvp/README.md.
"""A stand-in COM260 Fedora host for tests/run-tool-dry-run.sh.

  fake-board.py ssh [SSH OPTIONS] [--] HOST [COMMAND...]
  fake-board.py scp [SCP OPTIONS] [--] SOURCE... HOST:/tmp/PATH
  fake-board.py tool NAME [ARG...]

Purpose: let the dry run drive tools/k3-preflight.sh, k3-stage.sh, and
         k3-env.sh's ssh steps end to end without a board. The dry run puts
         `ssh` and `scp` wrappers that exec this script first on PATH and
         names a host that cannot resolve, so no command can reach the real
         board. Fedora answers only while it is up (state.json; the fake
         U-Boot, tests/fake-uboot.py, brings it up at a boot of the human's
         bootcmd and down at a reset); otherwise every ssh fails as for a
         board that has left Fedora (`connect to host ... No route to host`,
         or down_message, status 255). Each command the board tools send is
         answered as Fedora on the COM260 would: `true`; the boot ID; files
         copied into the board's /tmp; the preflight's remote script, with
         the facts B7 recorded on the COM260 (bringup/k3-b7/results/
         20261008-com260/preflight.txt), each hart's h and Sstc and HSM's
         detection derived from that record (and its firmware identity, or
         sbi_implementation's), its cpu-map, cache, and sysfs topology lines
         this script's own synthetic stand-ins, since B7 recorded none, and
         the Beryllium partition's and env_k3.txt's lines; the platform
         probe streamed on stdin, tools/platform-probe.py itself, run with
         its FDT and machine faked; the staging script of tools/k3-stage.sh,
         run with bash with its /tmp the board's and its blkid, findmnt,
         mount, umount, sudo, and sync these `tool`s, which mount the
         partition as the directory FAKE_K3_BOARD/partition; and `systemctl
         reboot` or `systemctl poweroff`, which take Fedora down and ask
         the fake U-Boot (FAKE_K3_BOARD/poweroff, holding the command) to
         print Linux's last lines: after a reboot the board halts at
         `reboot: Restarting system` and a reset boots it, as the COM260
         does; after a poweroff it is off and a reset does nothing, as
         the COM260 is (2026-10-30).
         With FAKE_K3_HOSTILE, a directory of hostile modules (tests/
         run-tool-dry-run.sh's), the board account's shell runs from it
         with it on PYTHONPATH, as a board account's could (the release's
         security review, S-05): the platform probe's command is run as
         the board would run it, its sudo a pass-through, its output
         dropped (on this host the probe refuses a machine that is not
         riscv64), so that a Python it starts without -I imports a hostile
         module, which the dry run's hostile log records; and so is the
         staging script.
Trust:   test-only; it runs no command it receives but the staging script
         and the platform probe's command, each only inside the fake board;
         anything it does not recognize fails with status 127.
Scope:   MVP board-tool dry run. The board is the directory named by
         FAKE_K3_BOARD: config.json (the scenario), state.json, tmp/ (the
         board's /tmp), partition/ (the Beryllium partition's files),
         commands.log (every command received), and mounts.log. config.json
         keys: host, iomem (System RAM lines; default B7's record),
         fdt_reserved (list of [low, high); default B7's record), fdt_bytes,
         sstc_hart0, h_hart2, hsm_detected, sbi_implementation (the firmware
         identity in Fedora's log; default B7's record's), partition
         (null for no filesystem labelled beryllium, or the type), env_k3
         (the variables env_k3.txt sets), corrupt_after_sync (an image the
         staging's sync flips a byte of), and down_message.
"""

import errno
import hashlib
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE.parents[1] / "bringup"
B7_PREFLIGHT = RESULTS / "k3-b7" / "results" / "20261008-com260" / \
    "preflight.txt"
KERNEL = "7.1.5-201.0.riscv64.omni.fc44.riscv64"
LOCKDOWN = "[none] integrity confidentiality"
SSH_FLAGS = set("nfNtTqv46AaCgKkMsXxYyG")
SSH_VALUES = set("opilOFEJLRDSWwbcemBIQ")
SCP_FLAGS = set("qrpvBCT346")
SCP_VALUES = set("oPiFlcSJ")
DEVICE = "/dev/nvme0n1p6"
UUID = "66666666-7777-4888-9999-000000000006"
# Fedora's root filesystem UUID in the kernel command line, which B7's
# record holds redacted: the fake board prints one, so a record that copies
# the preflight after the session without B0's redaction fails the dry run.
ROOT_UUID = "0f0f0f0f-1111-4222-8333-444444444444"
# The platform probe's command: any that streams it to a python3 (the
# tools' is `cd / && ... /usr/bin/python3 -I -B - probe ...`).
PROBE = re.compile(r".*\bpython3\b.* - probe\b.*")
STAGE_PREPARE = "rm -rf /tmp/be-mvp-stage && mkdir -m 0700 /tmp/be-mvp-stage"


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
    """B7's recorded System RAM block of /proc/iomem (preflight.txt:85-105)."""
    lines = B7_PREFLIGHT.read_text(encoding="ascii").splitlines()
    start = lines.index("102000000-2ffffffff : System RAM")
    block = [lines[start]]
    for line in lines[start + 1:]:
        if not line.startswith(" "):
            break
        block.append(line)
    return block


def recorded_reservations():
    """B7's recorded FDT reservations (preflight.txt:140), [low, high)."""
    lines = B7_PREFLIGHT.read_text(encoding="ascii").splitlines()
    value = next(line for line in lines if line.startswith("fdt_reserved="))
    return [[int(low, 16), int(high, 16)] for low, high in
            (item.split("-") for item in
             value[len("fdt_reserved="):].split(","))]


def config(root):
    settings = {
        "host": "fedora@fake-k3-board.invalid",
        "iomem": recorded_iomem(),
        "fdt_reserved": recorded_reservations(),
        "fdt_bytes": 41088,
        "sstc_hart0": True,
        "h_hart2": True,
        "hsm_detected": True,
        "sbi_implementation": None,
        "partition": "ext4",
        # The UUID blkid reports for the partition: the preflight's by
        # default; another models a filesystem that carries the label but
        # not the stored UUID (a labelled stick), which staging refuses.
        "partition_uuid": UUID,
        # Whether the fake kernel accepts nosymfollow: false models an
        # older kernel, where the staging falls back and records it.
        "mount_nosymfollow": True,
        "env_k3": [],
        "corrupt_after_sync": None,
        "down_message": "",
    }
    settings.update(load_json(root / "config.json", {}))
    return settings


def state(root):
    return load_json(root / "state.json", {
        "boot_id": "00000000-0000-4000-8000-000000000001", "boots": 1,
        "fedora": "up"})


def down(settings):
    """What ssh says while the board is not in Fedora."""
    return settings["down_message"] or (
        f"ssh: connect to host {settings['host'].partition('@')[2]} port "
        "22: No route to host")


def board_path(root, path):
    """The board-side path inside the fake board's /tmp, or None."""
    parts = path.split("/")
    if parts[:2] == ["", "tmp"] and 3 <= len(parts) <= 4 and \
            all(part and part not in (".", "..") for part in parts[2:]):
        return root / "tmp" / "/".join(parts[2:])
    return None


def tools_dir(root):
    """The board's blkid, findmnt, mount, umount, sudo, and sync: this
    script's tools, each run in isolated mode."""
    tools = root / "bin"
    tools.mkdir(exist_ok=True)
    for name in ("blkid", "findmnt", "mount", "umount", "sudo", "sync"):
        (tools / name).write_text(
            f"#!/usr/bin/env bash\nexec {shlex.quote(sys.executable)} -I -B "
            f"{shlex.quote(__file__)} tool {name} \"$@\"\n", encoding="ascii")
        (tools / name).chmod(0o755)
    return tools


def account(root):
    """The board account's working directory and PYTHONPATH, with
    FAKE_K3_HOSTILE: (its directory, its environment's PYTHONPATH); else
    the board's root and none."""
    hostile = os.environ.get("FAKE_K3_HOSTILE")
    if hostile:
        return pathlib.Path(hostile), {"PYTHONPATH": hostile}
    return root, {}


def probe_as_sent(root, command, source):
    """The platform probe's COMMAND as the board's shell runs it, from the
    account's directory, its sudo a pass-through and its output dropped:
    a Python it starts without -I imports the hostile modules there."""
    directory, extra = account(root)
    if not extra:
        return
    environment = {"PATH": f"{tools_dir(root)}:/usr/bin", "LC_ALL": "C",
                   "LANG": "C", "HOME": str(directory),
                   "FAKE_K3_BOARD": str(root), **extra}
    subprocess.run(["bash", "-c", command], input=source, text=True,
                   cwd=directory, env=environment, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=False)


def run_probe(root, settings, source):
    """tools/platform-probe.py, streamed on stdin, with the FDT and the
    machine faked."""
    module = types.ModuleType("platform_probe_on_the_fake_board")
    exec(compile(source, "platform-probe.py", "exec"), module.__dict__)

    def board_open(path, *args, **kwargs):
        if str(path) != "/sys/firmware/fdt":
            raise FileNotFoundError(errno.ENOENT, "not on the fake board",
                                    str(path))
        return open(root / "fdt", *args, **kwargs)
    (root / "fdt").write_bytes(b"\xd0\x0d\xfe\xed" +
                               bytes(settings["fdt_bytes"] - 4))
    module.open = board_open
    module.platform = types.SimpleNamespace(machine=lambda: "riscv64")
    module.fdt_reserved = lambda fdt: [tuple(pair) for pair in
                                       settings["fdt_reserved"]]
    return module.main(["-", "probe"])


# Synthetic stand-ins for the topology lines B7 did not record: one
# cluster of eight cores and one shared cache (not K3 facts).
SYNTHETIC_TOPOLOGY = (
    [f"dt_cpu_map path=cluster0/core{cpu}/cpu cpu_phandle={cpu + 1}"
     for cpu in range(8)] +
    ["dt_cache node=/cpus/l2-cache phandle=9 level=2 size=fake "
     "line_size=64 next_level_cache="] +
    [f"cpu_topology cpu={cpu} physical_package_id=0 cluster_id=0 "
     f"core_id={cpu} cluster_cpus_list=0-7 core_cpus_list={cpu} "
     f"package_cpus_list=0-7" for cpu in range(8)])


def preflight_answer(settings):
    """The preflight's remote script, answered from B7's COM260 record (its
    lines before the streamed probe's, but its kexec facts): each hart's h
    and Sstc from its recorded extensions and isa line, HSM's detection
    from the recorded log, the synthetic topology lines, and the
    partition's and env_k3.txt's lines."""
    record = B7_PREFLIGHT.read_text(encoding="ascii").splitlines()
    end = record.index("iomem_system_ram_end")
    extensions = {line.split()[1][len("node="):]: line.split()[2:]
                  for line in record if line.startswith("dt_cpu_extensions ")}
    out = []
    for line in record[:record.index("iomem_system_ram_begin")]:
        if line.startswith("dt_cpu node="):
            node = line.split()[1][len("node="):]
            has_h = "h" in extensions.get(node, ()) and not (
                node == "cpu@2" and not settings["h_hart2"])
            line += f" h={'yes' if has_h else 'no'}"
            out.append(line)
            out.append(f"dt_cpu_links node={node} phandle="
                       f"{int(node[4:]) + 1} next_level_cache=9")
            if not settings["sstc_hart0"] and node == "cpu@0":
                out[-2] = out[-2].replace(" sstc=yes", " sstc=no")
            continue
        if line.startswith("cpuinfo processor=") and " isa=" in line:
            hart = line.split()[2]
            base = line.split(" isa=", 1)[1].split("_", 1)[0]
            has_h = "h" in base[4:] and not (
                hart == "hart=2" and not settings["h_hart2"])
            line = line.replace(" isa=", f" h={'yes' if has_h else 'no'} "
                                "isa=", 1)
            if not settings["sstc_hart0"] and hart == "hart=0":
                line = line.replace(" sstc=yes", " sstc=no")
        elif line.startswith(("kexec_", "tmp_fstype=", "CONFIG_KEXEC")):
            continue
        elif line.startswith("cmdline="):
            line = line.replace("root=UUID=<redacted>",
                                f"root=UUID={ROOT_UUID}", 1)
        out.append(line)
    out += SYNTHETIC_TOPOLOGY + partition_lines(settings)
    out.append("iomem_system_ram_begin")
    out += settings["iomem"]
    out.append("iomem_system_ram_end")
    log = []
    for line in record[end + 1:]:
        if not line.startswith("["):
            break
        if settings["sbi_implementation"] is not None:
            line = line.replace("SBI implementation ID=0x1 Version=0x10006",
                                "SBI implementation "
                                f"{settings['sbi_implementation']}")
        if settings["hsm_detected"] or "SBI HSM" not in line:
            log.append(line)
    out.append(f"hsm_detected="
               f"{sum('SBI HSM extension detected' in line for line in log)}")
    return "\n".join(out + log) + "\n"


def partition_lines(settings):
    """The preflight's Beryllium partition and env_k3.txt lines."""
    lines = ["partition_label=beryllium"]
    if settings["partition"]:
        lines += [f"partition_device={DEVICE}", "partition_number=6",
                  f"partition_fstype={settings['partition']}",
                  "partition_bytes=1073741824", "partition_mounted=no",
                  f"partition_uuid={UUID}"]
    else:
        lines.append("partition_device=absent")
    text = "".join(f"{name}=x\n" for name in settings["env_k3"]) + \
        "baudrate=115200\n"
    return lines + [
        "env_k3_device=/dev/sda2", "env_k3_source=debugfs",
        f"env_k3_bytes={len(text)}",
        f"env_k3_sha256={hashlib.sha256(text.encode()).hexdigest()}",
        f"env_k3_sets={','.join(settings['env_k3']) or 'none'}"]


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
    if current["fedora"] != "up":
        print(down(settings), file=sys.stderr)
        return 255
    command = " ".join(rest[1:])
    if command == "true":
        return 0
    if command == "cat /proc/sys/kernel/random/boot_id":
        print(current["boot_id"])
    elif command == "uname -r":
        print(KERNEL)
    elif command == "bash -s":
        if "iomem_system_ram_begin" not in sys.stdin.read():
            return unsupported("bash -s without the MVP preflight script")
        sys.stdout.write(preflight_answer(settings))
    elif PROBE.fullmatch(command):
        source = sys.stdin.read()
        probe_as_sent(root, command, source)
        return run_probe(root, settings, source)
    elif command == STAGE_PREPARE:
        target = root / "tmp" / "be-mvp-stage"
        subprocess.run(["rm", "-rf", "--", str(target)], check=True)
        target.mkdir(mode=0o700, parents=True)
    elif command.startswith("sudo=") and \
            " bash -s -- /tmp/be-mvp-stage " in command:
        script = sys.stdin.read()
        if not script.startswith("# be-mvp k3-stage remote"):
            return unsupported("bash -s without the staging script")
        names = command.split(" bash -s -- /tmp/be-mvp-stage ", 1)[1].split()
        return stage(root, script, names)
    elif command in ("sudo -n systemctl reboot", "sudo -n systemctl poweroff"):
        current["fedora"] = "down"
        save_json(root / "state.json", current)
        (root / "poweroff").write_text(command.rsplit(" ", 1)[1] + "\n",
                                       encoding="ascii")
    else:
        return unsupported(command)
    return 0


def stage(root, script, names):
    """The staging script under bash, inside the fake board, from the
    account's directory: its /tmp the board's, and blkid, findmnt, mount,
    umount, sudo, and sync this script's tools."""
    tools = tools_dir(root)
    (root / "partition").mkdir(exist_ok=True)
    directory, extra = account(root)
    environment = {"PATH": f"{tools}:/usr/bin", "LC_ALL": "C", "LANG": "C",
                   "HOME": str(root), "TMPDIR": str(root / "tmp"),
                   "FAKE_K3_BOARD": str(root), "sudo": "sudo -n", **extra}
    return subprocess.run(
        ["bash", "-s", "--", str(root / "tmp" / "be-mvp-stage"), *names],
        input=script, text=True, cwd=directory, env=environment,
        check=False).returncode


def tool(name, args):
    """The staging script's privileged and block-device commands."""
    root = board()
    settings = config(root)
    log(root, ["tool", name] + args)
    if name == "sudo":
        args = args[1:] if args[:1] == ["-n"] else args
        os.execvp(args[0], args)
    if name == "blkid":
        if args == ["-L", "beryllium"] and settings["partition"]:
            print(DEVICE)
            return 0
        if len(args) == 2 and args[0] == "-U" and settings["partition"] \
                and args[1] == settings["partition_uuid"]:
            print(DEVICE)
            return 0
        if args == ["-o", "value", "-s", "TYPE", DEVICE]:
            print(settings["partition"])
            return 0
        if args == ["-o", "value", "-s", "LABEL", DEVICE]:
            print("beryllium")
            return 0
        if args == ["-o", "value", "-s", "UUID", DEVICE]:
            print(settings["partition_uuid"])
            return 0
        return 2
    if name == "findmnt":
        return 1
    if name == "mount" and len(args) == 4 and args[2] == DEVICE:
        if "nosymfollow" in args[1].split(",") and \
                not settings["mount_nosymfollow"]:
            print("mount: bad option; nosymfollow is not supported",
                  file=sys.stderr)
            return 32
        directory = pathlib.Path(args[3])
        directory.rmdir()
        directory.symlink_to(root / "partition")
        with open(root / "mounts.log", "a", encoding="ascii") as handle:
            handle.write(f"mount {args[1]}\n")
        return 0
    if name == "umount" and len(args) == 1:
        directory = pathlib.Path(args[0])
        if not directory.is_symlink():
            return 32
        directory.unlink()
        directory.mkdir()
        return 0
    if name == "sync":
        victim = settings["corrupt_after_sync"]
        if victim and (root / "partition" / victim).is_file():
            data = bytearray((root / "partition" / victim).read_bytes())
            data[len(data) // 2] ^= 0x01
            (root / "partition" / victim).write_bytes(bytes(data))
        return 0
    return unsupported(f"{name} {shlex.join(args)}")


def scp(args):
    root = board()
    settings = config(root)
    current = state(root)
    _, rest = split_options(args, SCP_FLAGS, SCP_VALUES)
    log(root, ["scp"] + args)
    if len(rest) < 2 or not rest[-1].startswith(settings["host"] + ":"):
        print(f"fake-board: unexpected scp {rest}", file=sys.stderr)
        return 1
    if current["fedora"] != "up":
        print(down(settings), file=sys.stderr)
        return 255
    target = board_path(root, rest[-1][len(settings["host"]) + 1:]
                        .rstrip("/"))
    if target is None or (len(rest) > 2 and not target.is_dir()):
        print(f"fake-board: scp refused outside /tmp: {rest[-1]}",
              file=sys.stderr)
        return 1
    for source in rest[:-1]:
        path = target / pathlib.Path(source).name if target.is_dir() \
            else target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pathlib.Path(source).read_bytes())
    return 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "ssh":
        return ssh(argv[2:])
    if len(argv) >= 2 and argv[1] == "scp":
        return scp(argv[2:])
    if len(argv) >= 3 and argv[1] == "tool":
        return tool(argv[2], argv[3:])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
