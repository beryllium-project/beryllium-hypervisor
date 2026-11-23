#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""M13-2's read tool, mvp/tools/k3-read.py, against a stand-in board.

  test-k3-read.py --self-test --scratch DIR
  test-k3-read.py fake-ssh BOARD ARGUMENT...

Purpose: each case copies the tool and its list into DIR/CASE/repo/mvp/
tools/ (some with the list changed and the copy's pin set to it) and runs
`run DIR/CASE/private/run` with, first on PATH, an `ssh` that execs
fake-ssh, the stand-in board. That takes only the tool's fixed options and
the destination fedora@fake-k3-read.invalid, which cannot resolve; logs
every invocation; and answers each command of the case's list from
BOARD/board.json (a /proc/mounts with the debug file system, three PCI
functions with made-up configuration spaces, and a line for every other
read, unless the case says otherwise), anything else with status 127.
The cases: a whole run, with its commands, record, files, and decode; each
refusal before any command (ROOT existing, not private, or in the
checkout; K3_SSH and K3_SSH_OPTIONS; a list not the pinned one; each line
of a refused form, rule 5's words among them); each stop, with no later
command (a PCI address or a mounts line outside its form, an output that
exists, SSH's own failure); each read recorded with the run going on and
nothing sent twice (out of time on the board and here, oversize, sudo's
refusal and iomem's other failure, the debug file system not mounted);
and mvp/mvp's k3-read. DIR is made again, and removed after a pass.
What it misses: a real ssh, the board's own files, timeout, and sudo.
Exit 0 pass, 1 fail, 2 usage.
"""

import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
TOOL, LIST = HERE.parent / "tools" / "k3-read.py", \
    HERE.parent / "tools" / "k3-read-list.txt"
PYTHON, DESTINATION, TAG = ("/usr/bin/python3", "fedora@fake-k3-read.invalid",
                            "BE_MVP_K3_READ")
OPTIONS = ["-n", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
           "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
           "-o", "PermitLocalCommand=no", "-o", "ClearAllForwardings=yes",
           "-o", "ForwardAgent=no", "-o", "ForwardX11=no",
           "-o", "ControlPath=none", "--", DESTINATION]
PIN = re.compile(r'LIST_SHA256 = "([0-9a-f]{64})"')
DEBUG = "debugfs /sys/kernel/debug debugfs rw,nosuid,nodev,noexec 0 0\n"
MOUNTS = ("sysfs /sys sysfs rw,nosuid,nodev,noexec,relatime 0 0\n" + DEBUG +
          "tracefs /sys/kernel/debug/tracing tracefs rw,relatime 0 0\n"
          "/dev/nvme0n1p3 / ext4 rw,relatime 0 0\n")
SERIAL = 0x0123456789abcdef
DECODED = """\
pci 0000:00:00.0 bytes=4096 vendor=0x1111 device=0x0000 class=0x000000 \
header=1 command=0x0000 bus_master=0
pci 0000:00:00.0 cap 0x40 pcie type=root-port flr=0
pci 0000:00:00.0 ext 0x100 aer
pci 0000:00:00.0 ext 0x140 acs capability=0x005f control=0x001d
pci 0000:01:00.0 bytes=4096 vendor=0x2222 device=0x0000 class=0x000000 \
header=0 command=0x0406 bus_master=1
pci 0000:01:00.0 cap 0x40 power-management state=D0 no_soft_reset=1
pci 0000:01:00.0 cap 0x50 msi enabled=0 64bit=1 vectors_capable=32 \
vectors_enabled=4 address=0xe0400000 data=0x0021
pci 0000:01:00.0 cap 0x70 pcie type=endpoint flr=1
pci 0000:01:00.0 cap 0xb0 msi-x enabled=1 function_mask=0 table_size=33 \
table=bar0+0x3000 pba=bar0+0x2000
pci 0000:01:00.0 ext 0x100 aer
pci 0000:01:00.0 ext 0x148 serial-number value-not-shown
pci 0000:01:00.0 ext 0x158 ats capability=0x0020 enabled=0
pci 0000:01:00.0 ext 0x160 pri enabled=0
pci 0000:01:00.0 ext 0x170 pasid enabled=0 execute=1 privileged=1 width=20
pci 0000:02:00.0 bytes=256 vendor=0x3333 device=0x0000 class=0x000000 \
header=0 command=0x0000 bus_master=0
pci 0000:02:00.0 cap 0x48 msi enabled=0 64bit=0 vectors_capable=1 \
vectors_enabled=1 address=0x0 data=0x0000
pci 0000:02:00.0 cap malformed at 0x48
"""
# Rule 5's words, each in an account read of its own.
WORDS = (("/dev/mem", "cat /dev/mem"), ("/dev/port", "cat /dev/port"),
         ("regmap", "cat /sys/kernel/debug/regmap/x/registers"),
         ("nvmem", "cat /sys/bus/nvmem/devices/x/nvmem"),
         ("/resource", "cat /sys/bus/pci/devices/0000:00:00.0/resource0"),
         ("/rom", "cat /sys/bus/pci/devices/0000:00:00.0/rom"),
         ("/vpd", "cat /sys/bus/pci/devices/0000:00:00.0/vpd"),
         ("modprobe", "modprobe -n x"), ("insmod", "insmod x.ko"),
         ("rmmod", "rmmod x"), ("/bind", "cat /sys/bus/platform/drivers/x/bind"),
         ("/unbind", "cat /sys/bus/platform/drivers/x/unbind"),
         ("mount", "mount -t debugfs none /sys/kernel/debug"),
         ("umount", "umount /mnt"), ("dd", "dd if=/proc/iomem"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def insert(line):
    """An edit of the list: LINE before its first read."""
    return lambda text: re.sub(r"^uname ", f"{line}\nuname ", text, count=1,
                               flags=re.M)


def drop(name):
    return lambda text: re.sub(rf"^{name} .*\n", "", text, flags=re.M)


FORMS = [
    ("a superuser read not one of rule 5's six", lambda text: text.replace(
        "1048576 cat /proc/iomem", "1048576 cat /proc/version")),
    ("an account read that names sudo",
     insert("x account 10 4096 sudo -n cat /proc/iomem")),
    ("a redirection", insert("x account 10 4096 printf 1 > /sys/x")),
    ("a quote", insert("x account 10 4096 cat '/proc/version'")),
    ("a name twice", insert("uname account 10 4096 uname -a")),
    ("a WHO of neither kind", insert("x root 10 4096 uname -a")),
    ("SECONDS not of its form", insert("x account 0 4096 uname -a")),
    ("MAX_BYTES not of its form", insert("x account 10 999999999 uname -a")),
    ("mounts with another command", lambda text: text.replace(
        "cat /proc/mounts", "cat /proc/self/mounts")),
    ("an account read after a superuser read",
     lambda text: text + "x account 10 4096 uname -a\n"),
    ("a summary before mounts", drop("mounts")),
    ("the PCI form before pci-devices", drop("pci-devices")),
] + [(f"the word {word}", insert(f"x account 10 4096 {command}"))
     for word, command in WORDS]


def parse(text):
    """The list's reads, (NAME, WHO, SECONDS, MAX_BYTES, COMMAND)."""
    return [fields for fields in (line.split(None, 4) for line in
                                  text.splitlines() if line.strip() and
                                  not line.startswith("#"))
            if len(fields) == 5]


def expected(text, addresses):
    """The commands that the tool must send for TEXT, in its order."""
    return [f"timeout -k 5 {seconds} sudo -n "
            f"{command.replace('{pci}', address)}" if who == "superuser"
            else f"timeout -k 5 {seconds} sh -c '{command}'"
            for _, who, seconds, _, command in parse(text)
            for address in (addresses if "{pci}" in command else ["-"])]


def spaces():
    """Three made-up functions: a root port with PCI Express, AER, and ACS;
    an endpoint with every capability that the decode names; one of 256
    bytes whose capability list loops."""
    port, end, loop = bytearray(4096), bytearray(4096), bytearray(256)
    for data, at, value, size in (
            (port, 0, 0x1111, 2), (end, 0, 0x2222, 2), (loop, 0, 0x3333, 2),
            (port, 6, 0x10, 2), (end, 6, 0x10, 2), (loop, 6, 0x10, 2),
            (port, 0x0e, 1, 1), (port, 0x34, 0x40, 1), (port, 0x40, 0x10, 2),
            (port, 0x42, 0x42, 2), (port, 0x100, 0x14010001, 4),
            (port, 0x140, 0x1000d, 4), (port, 0x144, 0x1d005f, 4),
            (end, 4, 0x406, 2), (end, 0x34, 0x40, 1), (end, 0x40, 0x5001, 2),
            (end, 0x44, 8, 2), (end, 0x50, 0x7005, 2), (end, 0x52, 0xaa, 2),
            (end, 0x54, 0xe0400000, 4), (end, 0x5c, 0x21, 2),
            (end, 0x70, 0xb010, 2), (end, 0x72, 2, 2), (end, 0x74, 1 << 28, 4),
            (end, 0xb0, 0x11, 2), (end, 0xb2, 0x8020, 2), (end, 0xb4, 0x3000, 4),
            (end, 0xb8, 0x2000, 4), (end, 0x100, 0x14810001, 4),
            (end, 0x148, 0x15810003, 4), (end, 0x14c, SERIAL, 8),
            (end, 0x158, 0x1601000f, 4), (end, 0x15c, 0x20, 2),
            (end, 0x160, 0x17010013, 4), (end, 0x170, 0x1001b, 4),
            (end, 0x174, 0x1406, 2), (loop, 0x34, 0x48, 1),
            (loop, 0x48, 0x4805, 2)):
        data[at:at + size] = value.to_bytes(size, "little")
    return {"0000:00:00.0": port, "0000:01:00.0": end, "0000:02:00.0": loop}


def make(scratch, label, functions, edit=None, repin=True, answers=None):
    """DIR/LABEL: the tool and its list (EDIT changes the list, and with
    REPIN the copy's pin follows), the stand-in board, and its ssh."""
    top = scratch / label
    tools = top / "repo" / "mvp" / "tools"
    tools.mkdir(parents=True)
    text, source = LIST.read_text(), TOOL.read_text()
    if edit:
        text = edit(text)
        if repin:
            source = source.replace(PIN.search(source).group(1),
                                    sha(text.encode()))
    (tools / "k3-read.py").write_text(source)
    (tools / "k3-read-list.txt").write_text(text)
    for name in ("private", "board", "bin"):
        (top / name).mkdir(mode=0o700)
    (top / "private").chmod(0o700)
    reads = parse(text)
    board = {"names": {command.strip(): name for name, *_, command in reads},
             "answers": {name: {"out": f"stand-in output of {name}\n"}
                         for name, *_ in reads}}
    board["answers"].update({"mounts": {"out": MOUNTS}, "pci-devices": {
        "out": "".join(f"{address}\n" for address in functions)}})
    board["answers"].update({f"pci-config {address}": {"hex": data.hex()}
                             for address, data in functions.items()})
    board["answers"].update(answers or {})
    (top / "board" / "board.json").write_text(json.dumps(board))
    (top / "bin" / "ssh").write_text(
        f"#!/usr/bin/bash\nexec {PYTHON} -I -B {shlex.quote(str(__file__))} "
        f"fake-ssh {shlex.quote(str(top / 'board'))} \"$@\"\n")
    (top / "bin" / "ssh").chmod(0o755)
    return top


def run(top, root=None, env=None, limit=60):
    """(status, output, commands sent) of the case's tool, `run ROOT`."""
    environment = {"PATH": f"{top / 'bin'}:/usr/bin", "HOME": str(top),
                   "LC_ALL": "C", "LANG": "C", "K3_SSH": DESTINATION,
                   **(env or {})}
    try:
        result = subprocess.run(
            [PYTHON, "-I", "-B", str(top / "repo/mvp/tools/k3-read.py"),
             "run", str(root or top / "private" / "run")],
            env={k: v for k, v in environment.items() if v is not None},
            capture_output=True, text=True, timeout=limit, check=False)
        status, output = result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        status, output = None, "the case's own time limit"
    log = top / "board" / "commands.log"
    return status, output, [json.loads(line) for line in log.read_text()
                            .splitlines()] if log.exists() else []


def record(top):
    """The record's read lines by label, each its fields."""
    path = top / "private" / "run" / "record.tsv"
    rows = [line.split("\t") for line in path.read_text().splitlines()]
    return {row[1]: row for row in rows if row[0] == "read"}


def fake_ssh(board, args):
    """The stand-in board's ssh: every invocation logged; each command of
    the case's list answered from board.json, anything else 127."""
    config = json.loads((board / "board.json").read_text())
    with open(board / "commands.log", "a", encoding="utf-8") as log:
        log.write(json.dumps(args) + "\n")
    words, key = shlex.split(args[-1]) if args[:-1] == OPTIONS else [], None
    if words[:3] == ["timeout", "-k", "5"] and words[4:6] == ["sh", "-c"] \
            and len(words) == 7:
        key = config["names"].get(words[6])
    elif words[:3] == ["timeout", "-k", "5"] and words[4:6] == ["sudo", "-n"]:
        text = " ".join(words[6:])
        match = re.fullmatch(r"cat /sys/bus/pci/devices/(.+)/config", text)
        key = f"pci-config {match.group(1)}" if match else \
            config["names"].get(text)
        key = "sudo" if key and "sudo" in config["answers"] else key
    answer = config["answers"].get(key)
    if answer is None:
        print(f"fake-ssh: unknown: {args[-1]}", file=sys.stderr)
        return 127
    time.sleep(answer.get("sleep", 0))
    sys.stdout.buffer.write(bytes.fromhex(answer.get("hex", "")) +
                            answer.get("out", "").encode())
    sys.stderr.write(answer.get("err", ""))
    return answer.get("exit", 0)


def self_test(scratch):
    results = []

    def case(name, condition, detail=""):
        results.append(bool(condition))
        print(f"{'ok  ' if condition else 'FAIL'} {name}")
        if not condition and detail:
            print(detail)

    def refused(label, top, root=None, env=None, word=""):
        status, output, sent = run(top, root, env)
        case(f"refused, nothing sent: {label}", status == 5 and
             f"{TAG}: REFUSED" in output and word in output and not sent,
             output)

    functions, text = spaces(), LIST.read_text()
    full, pinned = expected(text, list(functions)), PIN.search(
        TOOL.read_text()).group(1)
    case("the tool pins its list", pinned == sha(LIST.read_bytes()))
    top = make(scratch, "whole", functions)
    status, output, sent = run(top)
    root, reads = top / "private" / "run", record(top)
    case("whole: PASS", status == 0 and f"{TAG}: PASS reads={len(full)} ok="
         f"{len(full)} superuser=yes debugfs=mounted pci=3 list={pinned}"
         in output, output)
    case("whole: each command once, in the list's order, with the fixed "
         "options and destination", [one[-1] for one in sent] == full and
         all(one[:-1] == OPTIONS for one in sent), sent)
    case("whole: the record, each read's file by its size and SHA-256",
         len(reads) == len(full) and all(
             row[3] == "ok" and row[12] == command and sha(
                 (root / row[10]).read_bytes()) == row[8] and
             (root / row[10]).stat().st_size == int(row[7])
             for row, command in zip(reads.values(), full)) and
         f"list\t{pinned}\treads=28\n" in (root / "record.tsv").read_text())
    case("whole: ROOT 0700, its files 0600, list.txt the list",
         stat.S_IMODE(root.stat().st_mode) == 0o700 and all(
             stat.S_IMODE(path.lstat().st_mode) == 0o600 and path.is_file()
             for path in root.iterdir()) and
         (root / "list.txt").read_bytes() == LIST.read_bytes())
    case("whole: no output's digest on standard output",
         not any(row[8] in output for row in reads.values()))
    case("whole: the decode, the serial number not shown",
         (root / "pci-capabilities.txt").read_text() == DECODED)
    top = make(scratch, "exists", functions)
    (top / "private" / "run").mkdir()
    refused("a run root that exists", top, word="exists")
    for mode in (0o750, 0o777):
        top = make(scratch, f"mode-{mode:o}", functions)
        (top / "private").chmod(mode)
        refused(f"ROOT in a directory of mode {mode:04o}", top,
                word="not private")
    top = make(scratch, "link", functions)
    (top / "link").symlink_to(top / "private")
    refused("ROOT in a directory reached by a link", top,
            top / "link" / "run", word="a symbolic link")
    top = make(scratch, "tree", functions)
    (top / "repo" / "private").mkdir(mode=0o700)
    refused("ROOT inside the checkout", top, top / "repo/private/run",
            word="inside this checkout")
    spec = importlib.util.spec_from_file_location("k3_read", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case("a directory of another account's is not private",
         module.private_problem(os.stat_result(
             (stat.S_IFDIR | 0o700, 0, 0, 1, os.geteuid() + 1, 0, 0, 0, 0,
              0)), os.geteuid()) == "is not this account's")
    top = make(scratch, "destination", functions)
    for env in ({"K3_SSH": None}, {"K3_SSH": "-oProxyCommand=x"},
                {"K3_SSH": "fedora@k3;reboot"}, {"K3_SSH": "fedora@"},
                {"K3_SSH_OPTIONS": "-p 22"}):
        refused(f"{env}", top, env=env, word="K3_SSH")
    refused("a read added to the list, its pin not moved", make(
        scratch, "outside", functions, insert(
            "version account 10 4096 cat /proc/version"), repin=False),
        word="not the list that this tool pins")
    for number, (label, edit) in enumerate(FORMS):
        refused(f"the list: {label}", make(scratch, f"form-{number}",
                                           functions, edit),
                word="k3-read-list.txt line")
    for number, line in enumerate(("0000:01:00.0/../../../x", "0000:01:20.0",
                                   "0000:1:00.0")):
        status, output, sent = run(make(scratch, f"address-{number}",
                                        functions, answers={"pci-devices": {
                                            "out": f"0000:00:00.0\n{line}\n"}}))
        case(f"the listed {line!r}: STOP after pci-devices, never named",
             status == 1 and "STOP" in output and "stop=pci-address" in
             output and [one[-1] for one in sent] == full[:3] and
             line not in output, output)
    status, output, sent = run(make(scratch, "mounts", functions, answers={
        "mounts": {"out": MOUNTS + "debugfs /sys/kernel/debug debugfs rw 0\n"}}))
    case("a mounts line of five fields: STOP after mounts", status == 1 and
         "stop=mounts" in output and [one[-1] for one in sent] == full[:2],
         output)
    status, output, sent = run(make(scratch, "twice", functions, answers={
        "pci-devices": {"out": "0000:00:00.0\n0000:00:00.0\n"}}))
    case("a function listed twice: its read sent once, then STOP",
         status == 1 and "stop=output-exists" in output and
         [one[-1] for one in sent] == full[:-2], output)
    status, output, sent = run(make(scratch, "ssh-error", functions, answers={
        "interrupts": {"exit": 255, "err": "ssh: connect: timed out\n"}}))
    last = full.index("timeout -k 5 10 sh -c 'cat /proc/interrupts'")
    case("SSH's own failure: STOP, nothing later", status == 1 and
         "stop=ssh-error" in output and
         [one[-1] for one in sent] == full[:last + 1], output)
    for label, answers, row, check in (
            ("out of time on the board", {"cpuinfo": {"exit": 124}},
             "cpuinfo", ("timeout", "-")),
            ("beyond its bound", {"uname": {"out": "x" * 5000}}, "uname",
             ("oversize", "-")),
            ("refused by sudo, no superuser", {"sudo": {
                "err": "sudo: a password is required\n", "exit": 1}},
             "iomem", ("failed", "no-superuser")),
            ("failing otherwise, still superuser", {"iomem": {
                "err": "cat: /proc/iomem: Permission denied\n", "exit": 1}},
             "iomem", ("failed", "-"))):
        top = make(scratch, f"go-on-{row}-{check[1]}", functions,
                   answers=answers)
        status, output, sent = run(top)
        reads, sudo = record(top), "no-superuser" in check
        made = [command for command in full if not sudo or "sudo" not in
                command or "/proc/iomem" in command]
        case(f"{row} {label}: recorded, the run goes on, nothing twice",
             status == 1 and "INCOMPLETE" in output and
             (reads[row][3], reads[row][11]) == check and
             [one[-1] for one in sent] == made and
             f"superuser={'no' if sudo else 'yes'}" in output and all(
                 (one[3], one[11]) == ("not-made", "no-superuser")
                 for one in list(reads.values())[-7:]) == sudo and
             (row != "uname" or (top / "private/run/uname.out").stat()
              .st_size == 4096), output)
    quick = lambda text: re.sub(r"^(cpuinfo +account +)10 ", r"\g<1>1 ",
                                text, flags=re.M)
    top = make(scratch, "here", functions, quick,
               answers={"cpuinfo": {"sleep": 60}})
    begun = time.monotonic()
    status, output, sent = run(top, limit=45)
    case("cpuinfo out of time here: killed at 16 s, recorded, the run goes "
         "on, nothing twice", status == 1 and 15 < time.monotonic() -
         begun < 40 and record(top)["cpuinfo"][3] == "killed" and
         [one[-1] for one in sent] == expected(quick(text), list(functions)),
         output)
    for number, mounts in enumerate((
            MOUNTS.replace(DEBUG, ""), MOUNTS.replace(
                " /sys/kernel/debug debugfs", " /mnt/debug debugfs"),
            MOUNTS + "tracefs /sys/kernel/debug tracefs rw 0 0\n")):
        top = make(scratch, f"debugfs-{number}", functions,
                   answers={"mounts": {"out": mounts}})
        status, output, sent = run(top)
        case(f"the debug file system not mounted ({number}): no summary "
             "sent, the other reads made", status == 1 and
             "debugfs=not-mounted" in output and
             [one[-1] for one in sent] == [command for command in full if
                                           "/kernel/debug/" not in command]
             and record(top)["clk-summary"][11] == "debugfs-not-mounted",
             output)
    wrapper = scratch / "wrapper"
    wrapper.mkdir()
    shutil.copy2(HERE.parent / "mvp", wrapper / "mvp")
    (wrapper / "Makefile").write_text(
        "k3-read:\n\t@echo goal=$@ K3_RUN_ROOT=$(K3_RUN_ROOT) "
        "K3_SSH=$$K3_SSH >>ran.log\n")
    ran = []
    for arguments in (["K3_RUN_ROOT=/x/r"], ["K3_FOO=1"]):
        ran.append(subprocess.run(
            [str(wrapper / "mvp"), "k3-read", *arguments], capture_output=True,
            text=True, check=False, env={"PATH": "/usr/bin", "HOME": str(
                scratch), "K3_SSH": DESTINATION}))
    log = (wrapper / "ran.log").read_text() if (wrapper / "ran.log").exists() \
        else ""
    case("mvp/mvp k3-read: K3_RUN_ROOT and K3_SSH reach make; another "
         "variable refused, make not run", ran[0].returncode == 0 and
         ran[1].returncode == 2 and "refused" in ran[1].stderr and
         log == f"goal=k3-read K3_RUN_ROOT=/x/r K3_SSH={DESTINATION}\n",
         ran[0].stderr + ran[1].stderr + log)
    return results


def main(argv):
    if len(argv) > 3 and argv[1] == "fake-ssh":
        return fake_ssh(pathlib.Path(argv[2]), argv[3:])
    if len(argv) != 4 or argv[1:3] != ["--self-test", "--scratch"]:
        print(__doc__, file=sys.stderr)
        return 2
    scratch = pathlib.Path(argv[3]).resolve()
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True, mode=0o700)
    results = self_test(scratch)
    failed = results.count(False)
    if not failed:
        shutil.rmtree(scratch, ignore_errors=True)
    print(f"BE_MVP_K3_READ_TEST: {'FAIL' if failed else 'PASS'} "
          f"cases={len(results)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
