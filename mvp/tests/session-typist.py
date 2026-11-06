#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""The QEMU typist (planning/mvp-m7-plan.md, M7-4; D-11, Q8, Q15): a
console variant's session typed into its image under QEMU, the run judged
by tests/check-capture.py.

  session-typist.py run --qemu QEMU --firmware FW --elf BOOT_ELF
      --expect EXPECT --session SESSION --output DIR --toolchain T
      [--report REPORT] [--kernel IMAGE --dtb DTB] [--attempts N]
      [--step-timeout S] [--run-timeout S]
  session-typist.py suite --qemu QEMU --firmware FW --build BUILD
      --scenarios DIR --output ROOT [--toolchains "gcc clang"]
  session-typist.py --self-test

Purpose: run boots BOOT_ELF as tests/run-qemu.sh boots a variant (QEMU
virt k3-like, eight harts, 8 GiB, FW as -bios, the ELF as -kernel), its
UART a stdio chardev on the typist's pipes whose log, QEMU's own, is the
run's console.log, the bytes tests/run-qemu.sh's file chardev would hold
(the typist requires the bytes it read to be the same). It waits for
EXPECT's console_input ready lines (BE_MVP:15 INPUT_ARMED, BE_MVP:16 FOCUS
none, each shell's MVPINIT 11 line), then takes each step of the session
as the generator wrote it into EXPECT (tools/gen-scenario.py,
session_plan()): it types the step's bytes, one key per 10 ms, NONCE
replaced by the run's nonce, 16 hex digits from os.urandom (Q15), after
0.5 s of quiet for a typed line; then waits, each within 30 s, for the
step's lines in order: a focus pair's BE_MVP:16 FOCUS line, a line's echo
from its focused domain and the text the session expects, a negative's
BE_MVP:17 INPUT_DROP line (the reason's first) or, for a literal ~~, the
guest's echo. Then it waits for the run's end, hart 0's BE_MVP:14 or a
failure, and QEMU's exit, within the run's timeout (300 s by default,
inside the run budget of 2^32 ticks, 429 s at QEMU's timebase), and runs
the checker on console.log with typed.txt, nonce.txt, and the session.
A run whose boot hart is a domain hart (the checker's REFUSED, Plan
revision M0-A.2) is made again, up to --attempts (8) in all.

Records, in DIR/attempt-N/: console.log (QEMU's log of the UART),
stdout.log (the bytes the typist read), qemu.txt (the command line, then
QEMU's messages), exit.txt (QEMU's status), typed.txt (every key with
its time after QEMU's start, its UTC time, its step, and its byte),
steps.txt (each wait's line and time), nonce.txt, session.txt (the
session's file and SHA-256, the expectation's, and the ELF's), check.txt
and result.json (the checker's); in DIR, attempts.tsv and result.txt, last
its BE_MVP_SESSION[TOOLCHAIN/IMAGE]: line.

suite runs every console variant whose expectation the generator wrote
(BUILD/gen/expect, BUILD/gen/te-poc/expect, BUILD/gen/anchor/expect: each
with a console_input section) for each toolchain in --toolchains its
expectation names, its image BUILD/variants/TOOLCHAIN/IMAGE/
be-mvp-boot.elf, its session under --scenarios, its scenario's authority
report, and anchor's measured domain's kernel and DTB as built, into
ROOT/TOOLCHAIN/IMAGE; then ROOT/sessions.tsv, every attempt's row, and
ROOT/sessions.txt, each run's line and last BE_MVP_SESSIONS: PASS|FAIL
sessions=N attempts=A refused=R. Exit 0 PASS, 1 FAIL, 2 usage.

Trust: a test driver; it writes only under DIR or ROOT, types only the
expectation's bytes, and reads no path from a record.
"""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import select
import shlex
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
CHECKER = HERE / "check-capture.py"
# tests/run-qemu.sh's k3-like machine and CPU, and its terminal markers.
MACHINE = "virt,aia=aplic-imsic,aia-guests=7"
CPU = ("rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,"
       "smstateen=true")
TERMINAL = re.compile(r"^(?:BE_MVP:14 SHUTDOWN|BE_MVP:FAIL|BE_K3_B3: FAIL)")
PREFIX = re.compile(r"^BE_MVP_G([0-9]): ")
NONCE = "NONCE"
NONCE_BYTES = 8
KEY_DELAY, SETTLE = 0.01, 0.5
STEP_TIMEOUT, BOOT_TIMEOUT, RUN_TIMEOUT, GRACE = 30.0, 120.0, 300.0, 10.0
ATTEMPTS = 8
# The generated scenarios the suite reads, BUILD-relative, and anchor's
# measured domain's inputs (tests/run-qemu.sh's).
GENERATED = ("gen", "gen/te-poc", "gen/anchor")
MEASURED = ("guest/Image", "guest/mvp-guest-g1-anchor.dtb")
REPORT = "authority-report.json"
ATTEMPT_COLUMNS = ("toolchain", "run", "attempt", "boot_hart", "qemu_exit",
                   "verdict", "capture_sha256", "elf", "elf_sha256", "keys",
                   "steps", "seconds")
NAME = re.compile(r"[a-z0-9][a-z0-9.-]{0,63}")


class Stop(Exception):
    """A wait that did not end as the session needs."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    now = datetime.datetime.now(datetime.timezone.utc)
    return f"{now:%Y-%m-%dT%H:%M:%S}.{now.microsecond // 1000:03d}Z"


class Lines:
    """The capture's complete lines as they arrive: each (stream, text),
    stream None for hart 0's and the loader's, else the domain whose
    prefix the line begins with, its text after the prefix."""

    def __init__(self):
        self.pending = b""
        self.rows = []

    def feed(self, data):
        self.pending += data
        *done, self.pending = self.pending.split(b"\n")
        for raw in done:
            text = raw.decode("utf-8", "replace").rstrip("\r")
            match = PREFIX.match(text)
            self.rows.append((int(match.group(1)), text[match.end():])
                             if match else (None, text))

    def find(self, wait, start, nonce):
        """The index of the first row at or after START that WAIT names,
        NONCE in place of the session's token; or None."""
        value = (wait.get("monitor") or wait.get("line") or
                 wait.get("contains")).replace(NONCE, nonce)
        for index in range(start, len(self.rows)):
            stream, text = self.rows[index]
            if "monitor" in wait:
                if stream is None and text == value:
                    return index
            elif stream == wait["domain"] and (
                    text == value if "line" in wait else value in text):
                return index
        return None

    def terminal(self):
        return any(stream is None and TERMINAL.match(text)
                   for stream, text in self.rows)


class Console:
    """The typist's side of QEMU's stdio chardev: what it reads, logged."""

    def __init__(self, qemu, log):
        self.qemu, self.log = qemu, log
        self.lines = Lines()
        self.data = bytearray()
        self.closed = False

    def write(self, data):
        os.write(self.qemu.stdin.fileno(), data)

    def read_some(self, timeout):
        if self.closed:
            time.sleep(timeout)
            return
        ready, _, _ = select.select([self.qemu.stdout], [], [], timeout)
        if not ready:
            return
        chunk = os.read(self.qemu.stdout.fileno(), 65536)
        if not chunk:
            self.closed = True
            return
        self.data += chunk
        self.log.write(chunk)
        self.log.flush()
        self.lines.feed(chunk)

    def wait(self, test, timeout, stage):
        deadline = time.monotonic() + timeout
        while True:
            found = test()
            if found is not None:
                return found
            if self.closed:
                raise Stop(f"{stage}: QEMU exited")
            if self.lines.terminal():
                raise Stop(f"{stage}: the run ended")
            if time.monotonic() >= deadline:
                raise Stop(f"{stage}: not within {timeout:g} s")
            self.read_some(0.05)

    def quiet(self, seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            self.read_some(max(0.0, min(0.05, deadline - time.monotonic())))


class Record:
    """typed.txt and steps.txt."""

    def __init__(self, directory, started):
        self.typed = open(directory / "typed.txt", "w", encoding="ascii")
        self.typed.write("# session-typist.py's keys: seconds after QEMU's "
                         "start, UTC, the session step, the byte\n")
        self.steps = open(directory / "steps.txt", "w", encoding="utf-8")
        self.started = started
        self.keys = 0

    def stamp(self):
        return f"+{time.monotonic() - self.started:.3f} {utc()}"

    def key(self, step, byte):
        self.typed.write(f"{self.stamp()} step={step} key=0x{byte:02x}\n")
        self.typed.flush()
        self.keys += 1

    def note(self, text):
        self.steps.write(f"{self.stamp()} {text}\n")
        self.steps.flush()

    def close(self):
        self.typed.close()
        self.steps.close()


def type_bytes(console, record, step, data, delay):
    for byte in data:
        console.write(bytes([byte]))
        record.key(step, byte)
        time.sleep(delay)


def run_steps(console, record, section, nonce, args):
    """The ready lines, then every step: its keys, then its waits."""
    lines = console.lines
    cursor = 0
    for wait in section["ready"]:
        found = console.wait(lambda: lines.find(wait, 0, nonce),
                             args.boot_timeout, f"ready {wait}")
        record.note(f"ready line={found + 1} {json.dumps(wait)}")
        cursor = max(cursor, found + 1)
    for step in section["steps"]:
        typed = step["typed"].replace(NONCE, nonce).encode("ascii")
        if typed:
            if step["kind"] in ("send", "negative"):
                console.quiet(args.settle)
            cursor = len(lines.rows)
            record.note(f"step={step['index']} {step['kind']} "
                        f"{json.dumps(step['value'])} keys={len(typed)}")
            type_bytes(console, record, step["index"], typed, args.key_delay)
        for wait in step["waits"]:
            found = console.wait(
                lambda: lines.find(wait, cursor, nonce), args.step_timeout,
                f"step {step['index']} ({step['kind']} "
                f"{step['value']!r}) {wait}")
            record.note(f"step={step['index']} line={found + 1} "
                        f"{json.dumps(wait)}")
            cursor = found + 1


def stop(process, grace=0.0):
    """PROCESS's exit status, after GRACE seconds for it to exit (its
    stdout closes as it exits), and after killing it if it still runs."""
    try:
        return str(process.wait(timeout=grace))
    except subprocess.TimeoutExpired:
        pass
    process.kill()
    try:
        return f"killed:{process.wait(timeout=10)}"
    except subprocess.TimeoutExpired:
        return "killed:none"


def attempt(args, expect, directory, session_sha, elf_sha):
    """One QEMU boot through the session into DIRECTORY; (QEMU's exit,
    the error that ended it early or None, keys, seconds)."""
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    nonce = os.urandom(NONCE_BYTES).hex()
    (directory / "nonce.txt").write_text(nonce + "\n", encoding="ascii")
    section = expect["console_input"]
    (directory / "session.txt").write_text(
        f"session={section['session']['file']} name="
        f"{section['session']['name']} sha256={session_sha} "
        f"steps={len(section['steps'])}\n"
        f"expect={pathlib.Path(args.expect).name} image={expect['image']} "
        f"sha256={sha256(pathlib.Path(args.expect).read_bytes())}\n"
        f"elf={args.elf} sha256={elf_sha}\n", encoding="utf-8")
    argv = [args.qemu, "-machine", MACHINE, "-cpu", CPU, "-smp", "8", "-m",
            "8G", "-bios", args.firmware, "-kernel", args.elf, "-display",
            "none", "-monitor", "none", "-no-reboot", "-chardev",
            f"stdio,id=uart0,signal=off,logfile={directory / 'console.log'},"
            "logappend=off", "-serial", "chardev:uart0"]
    error, status = None, "none"
    with open(directory / "qemu.txt", "wb") as qemu_out, \
            open(directory / "stdout.log", "wb") as log:
        qemu_out.write(f"argv: {shlex.join(argv)}\n".encode())
        qemu_out.flush()
        started = time.monotonic()
        record = Record(directory, started)
        qemu = subprocess.Popen(argv, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=qemu_out)
        console = Console(qemu, log)
        try:
            try:
                run_steps(console, record, section, nonce, args)
                record.note("session typed")
            except Stop as stopped:
                error = str(stopped)
                record.note(f"stopped: {error}")
            deadline = started + args.run_timeout
            ended = None
            while not console.closed and time.monotonic() < deadline:
                console.read_some(0.1)
                if ended is None and console.lines.terminal():
                    ended = time.monotonic()
                if ended is not None and time.monotonic() - ended >= GRACE:
                    break
            if not console.closed:
                record.note("QEMU still runs after the run's end or its "
                            "timeout")
        finally:
            status = stop(qemu, GRACE if console.closed else 0.0)
            while not console.closed:
                console.read_some(0.1)
            for pipe in (qemu.stdin, qemu.stdout):
                try:
                    pipe.close()
                except OSError:
                    pass
            record.close()
    (directory / "exit.txt").write_text(status + "\n", encoding="ascii")
    seconds = time.monotonic() - started
    logged = (directory / "console.log").read_bytes()
    if logged != bytes(console.data):
        error = (error or "") + " QEMU's log of the UART is not the bytes " \
            "the typist read"
    return status, error, record.keys, seconds


def judge(args, directory, session):
    """The checker on DIRECTORY's capture: its verdict, the boot hart."""
    command = [sys.executable, "-B", str(CHECKER),
               str(directory / "console.log"), "--expect", args.expect,
               "--mode", "direct", "--sbi-version", "2.0", "--toolchain",
               args.toolchain, "--json", str(directory / "result.json"),
               "--typed", str(directory / "typed.txt"), "--nonce",
               str(directory / "nonce.txt"), "--session", str(session)]
    if args.report:
        command += ["--report", args.report]
    if args.kernel:
        command += ["--kernel", args.kernel, "--dtb", args.dtb]
    with open(directory / "check.txt", "wb") as out:
        subprocess.run(command, stdout=out, stderr=subprocess.STDOUT,
                       check=False)
    text = (directory / "check.txt").read_text(encoding="utf-8")
    verdict = re.search(r"^BE_MVP_RESULT: ([A-Z]+) ", text, re.M)
    try:
        fields = json.loads((directory / "result.json").read_text(
            encoding="utf-8"))["fields"]
    except (OSError, ValueError, KeyError):
        fields = {}
    return (verdict.group(1) if verdict else "none",
            fields.get("boot_hart", "none"),
            text.rstrip().splitlines()[-1] if text.strip() else "")


def run(args):
    """One session's run: attempts until one is not refused."""
    expect = json.loads(pathlib.Path(args.expect).read_text(encoding="utf-8"))
    section = expect.get("console_input")
    if not section:
        raise SystemExit(f"{args.expect} declares no console input")
    session = pathlib.Path(args.session)
    session_sha = sha256(session.read_bytes())
    if session_sha != section["session"]["sha256"]:
        raise SystemExit(f"{session} is not the session {args.expect} was "
                         f"generated from")
    elf_sha = sha256(pathlib.Path(args.elf).read_bytes())
    out = pathlib.Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    # A former run's records, and only those, go first.
    for old in out.glob("attempt-*"):
        if old.is_dir():
            shutil.rmtree(old)
    for name in ("attempts.tsv", "result.txt"):
        (out / name).unlink(missing_ok=True)
    label = f"{args.toolchain}/{expect['image']}"
    rows, verdict, refused, check, total = [], "none", 0, "", 0.0
    for number in range(1, args.attempts + 1):
        directory = out / f"attempt-{number}"
        status, error, keys, seconds = attempt(args, expect, directory,
                                               session_sha, elf_sha)
        verdict, hart, check = judge(args, directory, session)
        total += seconds
        if status != "0" and verdict == "PASS":
            verdict, check = "FAIL", f"QEMU's exit {status}"
        if error and verdict == "PASS":
            verdict, check = "FAIL", error
        rows.append((args.toolchain, expect["image"], str(number), hart,
                     status, verdict,
                     sha256((directory / "console.log").read_bytes()),
                     getattr(args, "elf_label", None) or args.elf, elf_sha,
                     str(keys),
                     str(len(section["steps"])), f"{seconds:.1f}"))
        if verdict != "REFUSED":
            break
        refused += 1
    if verdict == "REFUSED":
        verdict, check = "FAIL", "every attempt refused"
    (out / "attempts.tsv").write_text("\n".join(
        "\t".join(row) for row in [ATTEMPT_COLUMNS] + rows) + "\n",
        encoding="utf-8")
    line = (f"BE_MVP_SESSION[{label}]: {verdict} attempts={len(rows)} "
            f"refused={refused} steps={len(section['steps'])} "
            f"keys={rows[-1][9]} seconds={rows[-1][11]} ({check})")
    (out / "result.txt").write_text(line + "\n", encoding="utf-8")
    print(line, flush=True)
    return verdict == "PASS", rows


def suite(args):
    """Every console variant's session, for each toolchain."""
    build, root = pathlib.Path(args.build), pathlib.Path(args.output)
    toolchains = args.toolchains.split()
    runs = []
    for generated in GENERATED:
        directory = build / generated
        for path in sorted((directory / "expect").glob("*.json")):
            expect = json.loads(path.read_text(encoding="utf-8"))
            if "console_input" not in expect:
                continue
            report = directory / REPORT
            for toolchain in toolchains:
                if toolchain not in expect["toolchains"]:
                    continue
                runs.append((toolchain, expect, path, report if
                             report.is_file() else None))
    if not runs:
        raise SystemExit(f"no console variant's expectation under {build}")
    for name in ("sessions.txt", "sessions.tsv"):
        (root / name).unlink(missing_ok=True)
    passed, rows, lines = 0, [], []
    for toolchain, expect, path, report in runs:
        image, scenario = expect["image"], expect["scenario"]
        if not NAME.fullmatch(image) or not NAME.fullmatch(scenario):
            raise SystemExit(f"{path} names image {image!r}")
        one = argparse.Namespace(**vars(args))
        one.toolchain, one.expect = toolchain, str(path)
        # The ELF as the evidence bundle binds it: BUILD-relative.
        one.elf_label = f"variants/{toolchain}/{image}/be-mvp-boot.elf"
        one.elf = str(build / one.elf_label)
        one.session = str(pathlib.Path(args.scenarios) / scenario /
                          expect["console_input"]["session"]["file"])
        one.report = str(report) if report else None
        one.kernel = one.dtb = None
        if "measurement" in expect:
            one.kernel, one.dtb = (str(build / name) for name in MEASURED)
        one.output = str(root / toolchain / image)
        ok, run_rows = run(one)
        passed += ok
        rows += run_rows
        lines.append((root / toolchain / image / "result.txt").read_text(
            encoding="utf-8").rstrip())
    refused = sum(row[5] == "REFUSED" for row in rows)
    verdict = "PASS" if passed == len(runs) else "FAIL"
    last = (f"BE_MVP_SESSIONS: {verdict} sessions={len(runs)} "
            f"attempts={len(rows)} refused={refused}" +
            ("" if verdict == "PASS" else f" failed={len(runs) - passed}"))
    root.mkdir(parents=True, exist_ok=True)
    (root / "sessions.tsv").write_text("\n".join(
        "\t".join(row) for row in [ATTEMPT_COLUMNS] + rows) + "\n",
        encoding="utf-8")
    (root / "sessions.txt").write_text("\n".join(lines + [last]) + "\n",
                                       encoding="utf-8")
    print(last)
    return 0 if verdict == "PASS" else 1


def self_test():
    """The line tracker and the waits on a synthetic capture, and the key
    record's form, as tests/check-capture.py reads it."""
    failed = 0
    lines = Lines()
    lines.feed(b"OpenSBI v1.6\r\nBE_MVP:15 INPUT_ARMED grants=g0,g1 prefix")
    lines.feed(b"=0x7e\nBE_MVP:16 FOCUS none\nBE_MVP_G0: # echo 0123456789abcd"
               b"ef\nBE_MVP_G1: 0123456789abcdef\nBE_MVP_G0: 0123456789abcdef"
               b"\nBE_MVP_G1: BE_MVP:16 FOCUS g1\nBE_MVP:16 FOCUS g1\nBE_MVP_G")
    nonce = "0123456789abcdef"
    cases = (
        ("the rows so far", len(lines.rows) == 8 and lines.pending ==
         b"BE_MVP_G"),
        ("a monitor line", lines.find({"monitor": "BE_MVP:16 FOCUS none"},
                                      0, nonce) == 2),
        ("a monitor line is never a domain's", lines.find(
            {"monitor": "BE_MVP:16 FOCUS g1"}, 0, nonce) == 7),
        ("an echo, the nonce in place", lines.find(
            {"domain": 0, "line": "# echo NONCE"}, 0, nonce) == 3),
        ("a domain's text, its own", lines.find(
            {"domain": 0, "contains": "NONCE"}, 4, nonce) == 5),
        ("not before START", lines.find(
            {"domain": 1, "contains": "NONCE"}, 5, nonce) is None),
        ("the loader's lines", lines.rows[0] == (None, "OpenSBI v1.6")),
        ("no terminal line", not lines.terminal()))
    lines.feed(b"0: x\nBE_MVP:14 SHUTDOWN type=0 reason=0\n")
    cases += (("the end", lines.terminal() and lines.rows[-2] == (0, "x")),)
    for name, ok in cases:
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}")
    total = len(cases)
    scratch = pathlib.Path(os.environ.get("TMPDIR", ".")) / \
        f"session-typist-self-test-{os.getpid()}"
    scratch.mkdir(parents=True, exist_ok=True)
    try:
        record = Record(scratch, time.monotonic())
        record.key(3, 0x7e)
        record.key(3, 0x0d)
        record.close()
        rows = [line for line in (scratch / "typed.txt").read_text(
            encoding="ascii").splitlines() if not line.startswith("#")]
        ok = len(rows) == 2 and all(re.fullmatch(
            r"\+[0-9]+\.[0-9]{3} [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}\."
            r"[0-9]{3}Z step=3 key=0x(?:7e|0d)", row) for row in rows)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    failed += not ok
    total += 1
    print(f"{'ok  ' if ok else 'FAIL'} typed.txt's rows")
    print(f"BE_MVP_SESSION_TYPIST_SELF_TEST: {'PASS' if not failed else 'FAIL'}"
          f" cases={total} failed={failed}")
    return 0 if not failed else 1


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    commands = parser.add_subparsers(dest="command")
    for name in ("run", "suite"):
        command = commands.add_parser(name)
        command.add_argument("--qemu", required=True)
        command.add_argument("--firmware", required=True)
        command.add_argument("--output", required=True)
        command.add_argument("--attempts", type=int, default=ATTEMPTS)
        command.add_argument("--step-timeout", type=float,
                             default=STEP_TIMEOUT)
        command.add_argument("--boot-timeout", type=float,
                             default=BOOT_TIMEOUT)
        command.add_argument("--run-timeout", type=float, default=RUN_TIMEOUT)
        command.add_argument("--key-delay", type=float, default=KEY_DELAY)
        command.add_argument("--settle", type=float, default=SETTLE)
        if name == "run":
            command.add_argument("--elf", required=True)
            command.add_argument("--expect", required=True)
            command.add_argument("--session", required=True)
            command.add_argument("--toolchain", required=True,
                                 choices=("gcc", "clang"))
            command.add_argument("--report")
            command.add_argument("--kernel")
            command.add_argument("--dtb")
        else:
            command.add_argument("--build", required=True)
            command.add_argument("--scenarios", required=True)
            command.add_argument("--toolchains", default="gcc clang")
    args = parser.parse_args(argv[1:])
    if args.self_test:
        return self_test()
    if args.command is None:
        parser.error("run, suite, or --self-test")
    if args.attempts < 1:
        parser.error("--attempts must be at least 1")
    if args.command == "run":
        if bool(args.kernel) != bool(args.dtb):
            parser.error("--kernel and --dtb go together")
        return 0 if run(args)[0] else 1
    return suite(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
