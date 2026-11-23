#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""M13-2's read tool: the board's Linux, read over SSH by a fixed list.

  k3-read.py run ROOT

Purpose: planning/mvp-m13-plan.md, M13-2 and rule 5. Each read of the list
beside this file (k3-read-list.txt, pinned by LIST_SHA256) is sent once, in
its order, to K3_SSH ([user@]host, from the environment): an account read
as `timeout -k 5 SECONDS sh -c 'COMMAND'`, a superuser read as `timeout -k 5
SECONDS sudo -n COMMAND`, COMMAND one of rule 5's six (SUPERUSER). Here it
is killed at SECONDS + MARGIN, and its output and error stream are each cut
at MAX_BYTES. A superuser read that sudo refuses (exit 1, the error stream
beginning `sudo:`) means no superuser, and no later one is made. The two
summaries are made only if /proc/mounts shows the debug file system at
/sys/kernel/debug, which nothing here mounts; the PCI form once for each
function that pci-devices lists. Last, each function's configuration space
is decoded here, into pci-capabilities.txt.
Records: ROOT, made with mode 0700 in a directory of this account's of mode
0700, outside this checkout: list.txt; record.tsv, a line for each fact as
it is known; NAME.out and NAME.err for each read. Each file is created
exclusively, mode 0600, never through a link, before its command is sent.
They hold the board's identifiers (rule 8): standard output holds statuses,
counts, and the list's SHA-256 alone.
Refused before any command, with nothing made (exit 5): K3_SSH not of its
form; K3_SSH_OPTIONS set; a list not the pinned one, or a line not of its
form (form_problem()); ROOT not absolute or not of its form, inside this
checkout, in a directory not private, or existing. A stop sends no further
command (exit 1): a pci-devices or mounts line outside its form, an output
that exists, SSH's own failure (exit 255: the board does not answer, the
plan's stop 4), an interrupt. A read that fails, runs out of time, or
exceeds its bound is recorded, and the run goes on; nothing is retried.
Exit status: 0 every read made and ok; 1 incomplete or stopped; 2 usage.
"""

import contextlib
import hashlib
import os
import pathlib
import re
import signal
import stat
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
TREE = HERE.parent.parent
LIST = HERE / "k3-read-list.txt"
LIST_SHA256 = "9d79f5f7d6f485840d511d342330eea14d80ec8f39cb527176fb179fb039acfb"
TAG = "BE_MVP_K3_READ"
# No known_hosts entry, control socket, local command, or forwarding.
SSH = ("ssh", "-n", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
       "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
       "-o", "PermitLocalCommand=no", "-o", "ClearAllForwardings=yes",
       "-o", "ForwardAgent=no", "-o", "ForwardX11=no",
       "-o", "ControlPath=none")
MARGIN = 15  # the connection's 10 s and the board's kill 5 s later
SUPERUSER = ("cat /proc/iomem", "dmesg", "journalctl -k -b 0 --no-pager",
             "cat /sys/kernel/debug/pm_genpd/pm_genpd_summary",
             "cat /sys/kernel/debug/clk/clk_summary",
             "cat /sys/bus/pci/devices/{pci}/config")
SUMMARY, PCI = "cat /sys/kernel/debug/", SUPERUSER[5]
FIXED = {"mounts": "cat /proc/mounts",
         "pci-devices": "ls -1 /sys/bus/pci/devices"}
# What rule 5 keeps out of every command, as written or as a whole word.
BARRED = re.compile(r"/dev/mem|/dev/port|regmap|nvmem|/resource|/rom|/vpd|"
                    r"modprobe|insmod|rmmod|/bind|/unbind|"
                    r"(?<!\w)(?:u?mount|dd|sudo)(?!\w)")
NAME = re.compile(r"[a-z][a-z0-9-]{0,31}")
DESTINATION = re.compile(r"(?:[a-z_][a-z0-9_-]{0,31}@)?"
                         r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}")
ROOT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
ADDRESS = re.compile(rb"[0-9a-f]{4}:[0-9a-f]{2}:[01][0-9a-f]\.[0-7]")
MOUNT = re.compile(rb"(?:[\x21-\x7e\x80-\xff]+ ){4}[0-9]+ [0-9]+")
STANDARD = {1: "power-management", 5: "msi", 0x10: "pcie", 0x11: "msi-x",
            0x13: "advanced-features"}
EXTENDED = {1: "aer", 3: "serial-number", 0xd: "acs", 0xe: "ari",
            0xf: "ats", 0x10: "sr-iov", 0x13: "pri", 0x1b: "pasid"}
PORTS = ("endpoint", "legacy-endpoint", "2", "3", "root-port",
         "upstream-port", "downstream-port", "pcie-to-pci-bridge",
         "pci-to-pcie-bridge", "rc-endpoint", "rc-event-collector")


class Refused(Exception):
    """Nothing is made, and no command is sent."""


class Stop(Exception):
    """No further command is sent."""


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def measure(descriptor):
    """(bytes, SHA-256) of the open file DESCRIPTOR."""
    hasher, offset = hashlib.sha256(), 0
    while chunk := os.pread(descriptor, 1 << 20, offset):
        hasher.update(chunk)
        offset += len(chunk)
    return offset, hasher.hexdigest()


def form_problem(fields, reads):
    """Why FIELDS, a line of the list after READS, is not of its form."""
    if len(fields) != 5 or not NAME.fullmatch(fields[0]):
        return "not NAME WHO SECONDS MAX_BYTES COMMAND"
    name, who, seconds, size, command = fields
    names, whos = [read[0] for read in reads], [read[1] for read in reads]
    if name in names:
        return f"{name} twice"
    if who not in ("account", "superuser") or not re.fullmatch(
            r"[1-9][0-9]{0,2}", seconds) or not re.fullmatch(
                r"[1-9][0-9]{0,7}", size) or int(size) > 1 << 26:
        return "WHO, SECONDS, or MAX_BYTES not of its form"
    if "'" in command or not command.isascii() or not command.isprintable():
        return "a command not of printable ASCII without '"
    if BARRED.search(command) or ">" in command.replace("2>/dev/null", ""):
        return "a command that names what rule 5 keeps out, or writes"
    if (who == "superuser") != (command in SUPERUSER):
        return "a superuser read not one of rule 5's six, or one as account"
    if name in FIXED and (who, command) != ("account", FIXED[name]):
        return f"{name} not the account's `{FIXED[name]}`"
    if who == "account" and "superuser" in whos:
        return "an account read after a superuser read"
    if command.startswith(SUMMARY) and "mounts" not in names:
        return "a summary before mounts"
    if command == PCI and "pci-devices" not in names:
        return "the PCI form before pci-devices"
    return None


def load_list():
    """(bytes, reads) of the pinned list: each read (NAME, WHO, SECONDS,
    MAX_BYTES, COMMAND), of its form; Refused otherwise."""
    data = LIST.read_bytes()
    if hashlib.sha256(data).hexdigest() != LIST_SHA256:
        raise Refused(f"{LIST.name} is not the list that this tool pins")
    reads = []
    for number, line in enumerate(
            data.decode("ascii", "replace").splitlines(), 1):
        if line.strip() and not line.startswith("#"):
            fields = [field.strip() for field in line.split(None, 4)]
            problem = form_problem(fields, reads)
            if problem:
                raise Refused(f"{LIST.name} line {number}: {problem}")
            reads.append((*fields[:2], int(fields[2]), int(fields[3]),
                          fields[4]))
    return data, reads


def private_problem(info, uid):
    """Why a directory, by its stat INFO, may not hold a run root: it must
    be a directory of UID's, of mode 0700; or None."""
    if not stat.S_ISDIR(info.st_mode):
        return "is not a directory"
    if info.st_uid != uid:
        return "is not this account's"
    mode = stat.S_IMODE(info.st_mode)
    return None if mode == 0o700 else f"has mode {mode:04o}, not 0700"


def make_root(path):
    """The descriptor of ROOT, PATH, made with mode 0700 in its directory,
    which must be private, outside this checkout."""
    name, parent = os.path.basename(path), os.path.dirname(path)
    if not os.path.isabs(path) or not ROOT_NAME.fullmatch(name):
        raise Refused(f"ROOT {path!r}: not absolute, or its name not "
                      f"{ROOT_NAME.pattern}")
    tree = os.path.realpath(TREE)
    if os.path.commonpath([os.path.realpath(parent), tree]) == tree:
        raise Refused(f"ROOT {path} is inside this checkout, and its files "
                      "will hold the board's identifiers")
    try:
        directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY |
                            os.O_NOFOLLOW)
    except OSError as error:
        raise Refused(f"ROOT's directory {parent}: " + (
            "a symbolic link" if os.path.islink(parent) else
            error.strerror)) from None
    problem = private_problem(os.fstat(directory), os.geteuid())
    if problem:
        raise Refused(f"ROOT's directory {parent} {problem}: not private")
    try:
        os.mkdir(name, 0o700, dir_fd=directory)
    except FileExistsError:
        raise Refused(f"ROOT {path} exists") from None
    root = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                   dir_fd=directory)
    os.close(directory)
    if private_problem(os.fstat(root), os.geteuid()):
        raise Refused(f"ROOT {path}, made, is not private")
    return root


def create(root, name):
    """NAME under ROOT, created exclusively, mode 0600, never through a
    link, open to read and write; Stop if it exists."""
    try:
        return os.open(name, os.O_RDWR | os.O_CREAT | os.O_EXCL |
                       os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=root)
    except FileExistsError:
        raise Stop("output-exists", f"{name} exists") from None


def remote(destination, sent, seconds, size, out, err):
    """(status, exit) of SENT over SSH, its streams into OUT and ERR, each
    cut at SIZE bytes, its process group killed at SECONDS + MARGIN."""
    environment = {name: os.environ[name] for name in
                   ("PATH", "HOME", "SSH_AUTH_SOCK") if name in os.environ}
    process = subprocess.Popen(
        (*SSH, "--", destination, sent), stdin=subprocess.DEVNULL,
        stdout=out, stderr=err, env={**environment, "LC_ALL": "C",
                                     "LANG": "C"}, start_new_session=True)
    deadline, status = time.monotonic() + seconds + MARGIN, None
    try:
        while process.poll() is None and status is None:
            if max(os.fstat(out).st_size, os.fstat(err).st_size) > size:
                status = "oversize"
            elif time.monotonic() > deadline:
                status = "killed"
            else:
                with contextlib.suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=0.2)
    finally:
        for number, wait in ((signal.SIGTERM, 2), (signal.SIGKILL, None)):
            if process.poll() is None:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, number)
                with contextlib.suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=wait)
    for descriptor in (out, err):
        if os.fstat(descriptor).st_size > size:
            os.ftruncate(descriptor, size)
            status = "oversize"
    code = process.returncode
    return status or {0: "ok", 124: "timeout", 137: "timeout",
                      255: "ssh-error"}.get(code, "failed"), code


def parsed(descriptor, form, what):
    """The output's lines, each of FORM; Stop WHAT otherwise, naming the
    line by its number alone, since its text stays in ROOT."""
    lines = os.pread(descriptor, 1 << 26, 0).split(b"\n")
    lines = lines[:-1] if lines[-1] == b"" else lines
    bad = [number for number, line in enumerate(lines, 1)
           if not form.fullmatch(line)]
    if bad:
        raise Stop(what, f"line {bad[0]} of its output is outside its form")
    return lines


class Session:
    """The run's record.tsv, a line at a time, and each read's status."""

    def __init__(self, root):
        self.root, self.record, self.results = root, create(root,
                                                            "record.tsv"), []

    def line(self, *fields):
        os.write(self.record, ("\t".join(map(str, fields)) + "\n").encode())

    def report(self, label, who, status, reason, sent, made=None):
        """The read line of LABEL, MADE (exit, start, end, out, err) or
        not, in the record and on standard output."""
        size, digest = measure(made[3]) if made else (0, "-")
        self.line("read", label, who, status, *(
            made[:3] if made else ("-", utc(), utc())), size, digest,
            measure(made[4])[0] if made else 0,
            f"{label}.out" if made else "-", reason or "-", sent)
        self.results.append((label, status))
        print(f"{TAG}: {len(self.results)} {label} {status} " +
              (reason or f"bytes={size}"), flush=True)


def run(path):
    destination = os.environ.get("K3_SSH", "")
    if not DESTINATION.fullmatch(destination):
        raise Refused("K3_SSH, the board's [user@]host, is unset or not of "
                      "its form")
    if os.environ.get("K3_SSH_OPTIONS"):
        raise Refused("K3_SSH_OPTIONS is set: this tool's SSH options are "
                      "fixed")
    data, reads = load_list()
    root = make_root(path)
    with os.fdopen(create(root, "list.txt"), "wb") as file:
        file.write(data)
    session = Session(root)
    session.line("be-mvp-k3-read", 1)
    session.line("tool", hashlib.sha256(pathlib.Path(__file__)
                                        .read_bytes()).hexdigest())
    session.line("list", LIST_SHA256, f"reads={len(reads)}")
    session.line("destination", destination)
    session.line("started", utc())
    state = {"superuser": "unknown", "debugfs": "unknown", "pci": None}
    functions, stop, files = [], None, contextlib.ExitStack()
    try:
        for name, who, seconds, size, command in reads:
            addresses = state["pci"] if command == PCI else None
            for label, address in [(name, "{pci}")] if addresses is None \
                    else [(f"{name}-{one}", one) for one in addresses]:
                sent = (f"timeout -k 5 {seconds} sudo -n "
                        f"{command.replace('{pci}', address)}"
                        if who == "superuser" else
                        f"timeout -k 5 {seconds} sh -c '{command}'")
                reason = "no-superuser" if who == "superuser" and \
                    state["superuser"] == "no" else \
                    f"debugfs-{state['debugfs']}" if command.startswith(
                        SUMMARY) and state["debugfs"] != "mounted" else \
                    "no-pci-list" if command == PCI and addresses is None \
                    else None
                if reason:
                    session.report(label, who, "not-made", reason, sent)
                    continue
                out = create(root, f"{label}.out")
                files.callback(os.close, out)
                err = create(root, f"{label}.err")
                files.callback(os.close, err)
                start = utc()
                status, code = remote(destination, sent, seconds, size, out,
                                      err)
                if who == "superuser" and status == "failed" and code == 1 \
                        and os.pread(err, 5, 0) == b"sudo:":
                    reason = "no-superuser"
                session.report(label, who, status, reason, sent,
                               (code, start, utc(), out, err))
                if reason or status == "ok" and who == "superuser" and \
                        state["superuser"] == "unknown":
                    state["superuser"] = "no" if reason else "yes"
                    session.line("superuser", state["superuser"])
                if command == PCI:
                    functions.append((address, label, status))
                if status == "ssh-error":
                    raise Stop("ssh-error", "SSH's own failure: the board "
                               "does not answer (the plan's stop 4)")
                if name == "mounts":
                    state["debugfs"] = "unknown" if status != "ok" else \
                        "mounted" if [line.split(b" ")[2] for line in parsed(
                            out, MOUNT, "mounts") if line.split(b" ")[1] ==
                            b"/sys/kernel/debug"][-1:] == [b"debugfs"] \
                        else "not-mounted"
                    session.line("debugfs", state["debugfs"])
                if name == "pci-devices" and status == "ok":
                    state["pci"] = [line.decode() for line in
                                    parsed(out, ADDRESS, "pci-address")]
                    session.line("pci", len(state["pci"]))
                files.close()
    except Stop as error:
        stop = error
    except KeyboardInterrupt:
        stop = Stop("interrupted", "an interrupt")
    except OSError as error:
        stop = Stop("tool", str(error))
    finally:
        files.close()
    decoded(session, functions)
    undone = [label for label, status in session.results if status != "ok"]
    verdict = "STOP" if stop else "INCOMPLETE" if undone else "PASS"
    session.line("ended", utc())
    session.line("verdict", verdict, *(f"stop={arg}" for arg in
                                       (stop.args[:1] if stop else ())))
    print(f"{TAG}: {verdict} reads={len(session.results)} ok="
          f"{len(session.results) - len(undone)} superuser="
          f"{state['superuser']} debugfs={state['debugfs']} pci="
          f"{len(state['pci'] or [])} list={LIST_SHA256}" +
          (f" undone={','.join(undone)}" if undone else "") +
          (f" stop={stop.args[0]} {stop.args[1]}" if stop else ""))
    return 0 if verdict == "PASS" else 1


# -------------------------------------------------- the configuration space
def word(data, at, size=2):
    return int.from_bytes(data[at:at + size], "little")


def capabilities(data):
    """(offset, kind, ID) of each capability in DATA, a function's
    configuration space, standard then extended; ID None at a bad pointer,
    which ends its walk."""
    found, seen = [], set()
    at, step = (data[0x34] & 0xfc if data[6] & 0x10 else 0), None
    for kind, low, size in (("cap", 0x40, 2), ("ext", 0x100, 4)):
        if kind == "ext":
            at = 0x100 if word(data, 0x100, 4) not in (0, 0xffffffff) else 0
        while at:
            if at < low or at + size > len(data) or at in seen:
                found.append((at, kind, None))
                break
            seen.add(at)
            step = word(data, at, size)
            found.append((at, kind, step & (0xff if size == 2 else 0xffff)))
            at = (step >> 8 if size == 2 else step >> 20) & 0xffc
    return found


def fields(name, data, at):
    """The bits of capability NAME at AT that M13's questions need."""
    def get(offset, size=2):
        return word(data, at + offset, size)
    wide, kind = get(2) >> 7 & 1, get(2) >> 4 & 0xf
    return {
        "power-management":
            f"state=D{get(4) & 3} no_soft_reset={get(4) >> 3 & 1}",
        "msi": f"enabled={get(2) & 1} 64bit={wide} vectors_capable="
               f"{1 << (get(2) >> 1 & 7)} vectors_enabled="
               f"{1 << (get(2) >> 4 & 7)} address=0x"
               f"{get(4, 4) | (get(8, 4) << 32 if wide else 0):x} "
               f"data=0x{get(12 if wide else 8):04x}",
        "pcie": f"type={PORTS[kind] if kind < len(PORTS) else kind} "
                f"flr={get(4, 4) >> 28 & 1}",
        "msi-x": f"enabled={get(2) >> 15} function_mask={get(2) >> 14 & 1} "
                 f"table_size={(get(2) & 0x7ff) + 1} table=bar"
                 f"{get(4, 4) & 7}+0x{get(4, 4) & ~7:x} pba=bar"
                 f"{get(8, 4) & 7}+0x{get(8, 4) & ~7:x}",
        "advanced-features": f"flr={get(3, 1) >> 1 & 1}",
        "acs": f"capability=0x{get(4):04x} control=0x{get(6):04x}",
        "ats": f"capability=0x{get(4):04x} enabled={get(6) >> 15}",
        "pri": f"enabled={get(4) & 1}",
        "pasid": f"enabled={get(6) & 1} execute={get(4) >> 1 & 1} "
                 f"privileged={get(4) >> 2 & 1} width={get(4) >> 8 & 0x1f}",
        "sr-iov": f"total_vfs={get(0x0e)}",
        "serial-number": "value-not-shown"}.get(name, "")


def decode(address, data):
    """pci-capabilities.txt's lines for the function ADDRESS."""
    if len(data) < 64:
        return [f"pci {address} bytes={len(data)} too-short"]
    lines = [f"pci {address} bytes={len(data)} vendor=0x{word(data, 0):04x} "
             f"device=0x{word(data, 2):04x} class=0x{word(data, 9, 3):06x} "
             f"header={data[0x0e] & 0x7f} command=0x{word(data, 4):04x} "
             f"bus_master={word(data, 4) >> 2 & 1}"]
    for at, kind, ident in capabilities(data):
        name = None if ident is None else (
            STANDARD if kind == "cap" else EXTENDED).get(ident, hex(ident))
        lines.append(f"pci {address} {kind} malformed at 0x{at:x}" if name
                     is None else f"pci {address} {kind} 0x{at:x} {name} "
                     f"{fields(name, data, at)}".rstrip())
    return lines


def decoded(session, functions):
    """pci-capabilities.txt from each function read, and its record line;
    a failure here is recorded, and changes no verdict. Each file that it
    opens is closed on every path."""
    try:
        lines = []
        for address, label, status in functions:
            if status != "ok":
                lines.append(f"pci {address} not-decoded status={status}")
                continue
            descriptor = os.open(f"{label}.out", os.O_RDONLY | os.O_NOFOLLOW,
                                 dir_fd=session.root)
            try:
                lines += decode(address, os.pread(descriptor, 1 << 16, 0))
            finally:
                os.close(descriptor)
        if lines:
            descriptor = create(session.root, "pci-capabilities.txt")
            try:
                os.write(descriptor, "".join(f"{line}\n" for line in lines)
                         .encode())
                session.line("decode", "pci-capabilities.txt",
                             *measure(descriptor))
            finally:
                os.close(descriptor)
    except (OSError, Stop, ValueError, IndexError) as error:
        session.line("decode", f"failed: {error}")


def interrupted(*_):
    raise KeyboardInterrupt


def main(argv):
    if len(argv) != 3 or argv[1] != "run":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    os.umask(0o077)
    signal.signal(signal.SIGTERM, interrupted)
    try:
        return run(argv[2])
    except Refused as error:
        print(f"{TAG}: REFUSED {error}")
        return 5


if __name__ == "__main__":
    sys.exit(main(sys.argv))
