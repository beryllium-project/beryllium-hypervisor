#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""The guest shell's smoke test (planning/mvp-m7-plan.md, M7-2's exit and
D-9): the guest Image booted directly under QEMU and plain OpenSBI, with no
monitor, through /init-shell, its console typed into.

  guest-shell-smoke.py --qemu QEMU --firmware FW --firmware-sha256 HEX
      --kernel IMAGE --output DIR [--timeout S]

Purpose: each of BOOTS runs IMAGE under FW on QEMU virt with one hart, its
UART on QEMU's stdin and stdout, the kernel reading and writing it through
OpenSBI's console (hvc0's SBI driver), with rdinit=/init-shell and a
scenario's role arguments. reader: te-poc's reader in 64 MiB, the size of
an MVP guest's window, so that the channel page and the unmapped address
lie outside RAM, where QEMU's bus answers an access as the monitor's
G-stage does, with an access fault. writer and host: te-poc's writer and
anchor's host in 128 MiB of which mem=64M gives Linux the window's 64 MiB,
so that the pages above it are RAM that /dev/mem maps (no fault, no peer:
the channel's text read back, and a request no protected domain answers).
At each prompt the driver types the step's line a key at a time (10 ms
apart), sends Enter once the terminal's echo is exactly the line, and
waits for the step's expected lines; the last step, exit, must end the
shell with status 0, the init's RESULT pass and POWER_OFF, and QEMU's exit
with status 0. No boot's console may hold "unhandled signal", "Kernel
panic", or "Oops".
Trust:   test-only; it judges a guest that no monitor isolates.
Outputs in DIR/<boot>/: console.log (every byte read), uart.log (QEMU's
own log of the UART), qemu.txt (the command line, then QEMU's messages),
and typed.txt (each line typed, its UTC time, and its echo's verdict); in
DIR, smoke.txt (each step's verdict, then BE_MVP_GUEST_SHELL_SMOKE:
PASS|FAIL). Exit 0 PASS, 1 FAIL, 2 usage.
"""

import argparse
import datetime
import hashlib
import os
import pathlib
import re
import select
import shlex
import subprocess
import sys
import time

BOOTARGS = "earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1"
PROMPT = b"# "
EXIT = ("exit", [r"MVPINIT 11 SHELL exit=0", r"MVPINIT 05 RESULT pass",
                 r"MVPINIT 06 POWER_OFF"])
# Each step: the typed line, and the lines (regular expressions, in order,
# each a whole line) its output must hold.
READER = (
    ("echo hello-m7", [r"hello-m7"]),
    ("echo $BE_ARGS",
     [r"be\.guest=1 be\.role=reader be\.channel=0x84000000 "
      r"be\.deny=store@0x84000ff8,load@0x90000000"]),
    ("ls -1 /bin | wc -l", [r" *18"]),
    ("printf 'BEM7' | hexdump -C | head -n 1",
     [r"00000000  42 45 4d 37 +\|BEM7\|"]),
    ("be-deny load-unmapped",
     [r"MVPINIT 08 DENIED n=2 kind=load gpa=0x90000000 va=0x[0-9a-f]+ "
      r"pc=0x[0-9a-f]+ signo=11 code=2 observed=1"]),
    ("be-deny bogus; echo status=$?",
     [r"usage: be-deny load-unmapped \| be-deny store-shared",
      r"status=2"]),
    ("be-anchor request 1; echo status=$?",
     [r"be-anchor: BE_ARGS names no host \(be\.role=host\)", r"status=2"]),
    EXIT,
)
WRITER = (
    ("be-chan read; echo status=$?",
     [r"MVPINIT 12 CHAN read gpa=0x84000000 empty=1", r"status=1"]),
    ("be-chan write hello from the writer",
     [r"MVPINIT 12 CHAN write gpa=0x84000000 bytes=21 "
      r"text=hello from the writer"]),
    ("be-chan read",
     [r"MVPINIT 12 CHAN read gpa=0x84000000 bytes=21 "
      r"text=hello from the writer"]),
    ("be-deny store-shared; echo status=$?",
     [r"be-deny: be.deny names no store", r"status=2"]),
    EXIT,
)
HOST = (
    ("be-anchor request 7; echo status=$?",
     [r"MVPINIT 09 REQUEST n=7 timeout=1", r"status=1"]),
    ("be-anchor request 01; echo status=$?",
     [r"usage: be-anchor request N \(1 to 999999999\)", r"status=2"]),
    ("be-chan write x; echo status=$?",
     [r"be-chan write: BE_ARGS names no channel writer \(be\.role=writer\)",
      r"status=2"]),
    EXIT,
)
# (name, memory, kernel arguments, the init's arguments, steps)
BOOTS = (
    ("reader", "64M", "", "be.guest=1 be.role=reader be.channel=0x84000000 "
     "be.deny=store@0x84000ff8,load@0x90000000", READER),
    ("writer", "128M", " mem=64M", "be.guest=0 be.role=writer "
     "be.channel=0x84000000 be.deny=load@0x84001000", WRITER),
    ("host", "128M", " mem=64M", "be.guest=0 be.role=host "
     "be.pages=0x84000000,0x84001000,0x84002000 "
     "be.deny=store@0x84001ff8,load@0x84002000", HOST),
)
REJECTED = (b"unhandled signal", b"Kernel panic", b"Oops")


class Stop(Exception):
    """The smoke test cannot go on."""


def pinned_firmware(args):
    """Refuse the firmware before each boot unless it still has its pin."""
    digest = hashlib.sha256(args.firmware.read_bytes()).hexdigest()
    if digest != args.firmware_sha256:
        print(f"--firmware {args.firmware} has SHA-256 {digest}, "
              "not the lock's MVP_PIN_FIRMWARE_BIN_SHA256 "
              f"{args.firmware_sha256}: refused", file=sys.stderr)
        raise SystemExit(2)


class Console:
    """QEMU's stdin and stdout, every byte read logged."""

    def __init__(self, qemu, log):
        self.qemu, self.log = qemu, log
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
        chunk = os.read(self.qemu.stdout.fileno(), 4096)
        if not chunk:
            self.closed = True
            return
        self.data += chunk
        self.log.write(chunk)
        self.log.flush()

    def wait(self, test, timeout, stage):
        deadline = time.monotonic() + timeout
        while True:
            found = test()
            if found is not None:
                return found
            if self.closed:
                raise Stop(f"{stage}: QEMU exited")
            if time.monotonic() >= deadline:
                raise Stop(f"{stage}: not within {timeout:g} s")
            self.read_some(0.1)

    def find(self, pattern, start, timeout, stage):
        """The end of PATTERN's first match at or after START."""
        return self.wait(lambda: next((match.end() for match in [
            pattern.search(self.data, start)] if match), None), timeout, stage)


def type_line(console, typed, line, start, timeout):
    """LINE at the prompt ending at START, a key at a time, then Enter once
    the terminal's echo is exactly LINE; the echo's end."""
    text = line.encode("ascii")
    for byte in text:
        console.write(bytes([byte]))
        time.sleep(0.01)

    def echoed():
        echo = bytes(console.data[start:])
        if not text.startswith(echo):
            raise Stop(f"echo {echo!r} for {line!r}")
        return True if echo == text else None

    try:
        console.wait(echoed, timeout, f"echo of {line!r}")
    except Stop:
        typed.write(f"{utc()} mismatch {line}\n")
        raise
    typed.write(f"{utc()} ok {line}\n")
    console.write(b"\r")
    return start + len(text)


def utc():
    now = datetime.datetime.now(datetime.timezone.utc)
    return f"{now:%Y-%m-%dT%H:%M:%S}.{now.microsecond // 1000:03d}Z"


def expect_lines(console, start, patterns, timeout, stage):
    """Each pattern as a whole line, in order, after START; the end of the
    last."""
    for pattern in patterns:
        start = console.find(re.compile(rb"(?m)^" + pattern.encode() +
                                        rb"\r*$"), start, timeout, stage)
    return start


def run(args, boot):
    """One boot; its verdicts, each "ok STEP" or "FAIL WHY"."""
    pinned_firmware(args)
    name, memory, kernel_args, init_args, steps = boot
    directory = args.output / name
    directory.mkdir(parents=True, exist_ok=True)
    paths = {item: directory / item for item in
             ("console.log", "uart.log", "qemu.txt", "typed.txt")}
    role = re.search(r"be\.role=([a-z]+)", init_args).group(1)
    # The tty and OpenSBI each make LF CR LF, so a line ends in CR CR LF.
    shell_line = re.compile(rb"MVPINIT 11 SHELL tty=/dev/hvc0 role=" +
                            role.encode() + rb"\r*\n")
    argv = [args.qemu, "-machine", "virt", "-cpu", "rv64", "-smp", "1",
            "-m", memory, "-bios", str(args.firmware), "-kernel",
            str(args.kernel), "-append",
            f"{BOOTARGS}{kernel_args} rdinit=/init-shell -- {init_args}",
            "-display", "none", "-monitor", "none", "-no-reboot", "-chardev",
            f"stdio,id=uart0,signal=off,logfile={paths['uart.log']},"
            "logappend=off", "-serial", "chardev:uart0"]
    verdicts = []
    with open(paths["qemu.txt"], "wb") as qemu_out, \
            open(paths["console.log"], "wb") as log, \
            open(paths["typed.txt"], "w", encoding="utf-8") as typed:
        qemu_out.write(f"argv: {shlex.join(argv)}\n".encode())
        qemu_out.flush()
        typed.write("# UTC, the echo's verdict, the line typed (Enter after "
                    "an exact echo)\n")
        qemu = subprocess.Popen(argv, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=qemu_out)
        console = Console(qemu, log)
        try:
            position = console.find(shell_line, 0, args.timeout, "the shell")
            for line, patterns in steps:
                position = console.find(re.compile(re.escape(PROMPT)),
                                        position, args.timeout,
                                        f"the prompt before {line!r}")
                position = type_line(console, typed, line, position,
                                     args.timeout)
                position = expect_lines(console, position, patterns,
                                        args.timeout, line)
                verdicts.append(f"ok {name}: {line}")
            console.wait(lambda: True if console.closed else None,
                         args.timeout, "QEMU's exit after the power-off")
        except Stop as stop:
            verdicts.append(f"FAIL {name}: {stop}")
        finally:
            # QEMU closes its output before it exits.
            try:
                status = qemu.wait(timeout=10)
            except subprocess.TimeoutExpired:
                qemu.kill()
                status = qemu.wait(timeout=10)
        verdicts.append(f"{'ok' if status == 0 else 'FAIL'} {name}: "
                        f"qemu_exit={status}")
        for word in REJECTED:
            if word in console.data:
                verdicts.append(f"FAIL {name}: the console holds "
                                f"{word.decode()!r}")
    return verdicts


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--qemu", required=True)
    parser.add_argument("--firmware", required=True, type=pathlib.Path)
    parser.add_argument("--firmware-sha256", required=True)
    parser.add_argument("--kernel", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{64}", args.firmware_sha256):
        parser.error("--firmware-sha256 is not a lowercase SHA-256")
    args.output.mkdir(parents=True, exist_ok=True)
    verdicts = []
    for boot in BOOTS:
        verdicts += run(args, boot)
    failed = any(item.startswith("FAIL") for item in verdicts)
    summary = (f"BE_MVP_GUEST_SHELL_SMOKE: {'FAIL' if failed else 'PASS'} "
               f"boots={len(BOOTS)} steps={sum(len(boot[4]) for boot in BOOTS)} "
               f"kernel={args.kernel}")
    (args.output / "smoke.txt").write_text(
        "\n".join(verdicts + [summary]) + "\n", encoding="utf-8")
    print("\n".join(verdicts + [summary]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
