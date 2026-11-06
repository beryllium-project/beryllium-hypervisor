#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# A copy of B3's tests/run-qemu-uboot.py (accepted at 9b4860a0) with the
# counted changes listed in bringup/k3-b5/README.md.
"""Rehearse the B5 board procedure under QEMU through a real U-Boot.

  run-qemu-uboot.py --firmware FW_DYNAMIC --uboot U_BOOT_BIN --checker PY
                    --ram-base B --output DIR SCENARIO:EXPECT:IMAGE...

Each scenario boots QEMU virt as the B5 plan's k3-like scenario does
(AIA/IMSIC with 7 guest interrupt lines; `-cpu rv64` with Sstc, Svade
without Svadu, Sv39 only, and Smstateen; 8 GiB; one hart): OpenSBI
fw_dynamic as -bios and
U-Boot as -kernel, held paused (-S) until the UART's PTY is open. The
harness then does what the operator does at the board, through that PTY:

  1. at U-Boot's autoboot countdown, presses a key;
  2. at the `=> ` prompt, types the operator's command
     `loady 0x140000000 && booti 0x140000000 - ${fdtcontroladdr}`;
  3. at `## Ready for binary (ymodem) download`, runs
     `sz -vv --ymodem -k IMAGE` with stdin and stdout on the PTY, exactly
     the command picocom's C-a C-s runs, and reads nothing itself until sz
     exits, as picocom does;
  4. reads on until the terminal marker, then until QEMU exits.

Outputs per scenario under DIR: NAME.console.log (what the harness read,
like a picocom log), NAME.uart.log (QEMU's log of every byte the guest
wrote, including what sz consumed), NAME.qemu.txt, NAME.sz.txt,
NAME.status.txt, and the checker's NAME.check.txt/NAME.result.json for the
console log and NAME.uart-check.txt for the full log. EXPECT is pass or
overlap. A scenario passes when sz and QEMU exit 0 (SRST shutdown powers
QEMU off), the firmware reported SBI 2.0, and both logs pass the checker
with --expect EXPECT --ram-base B --image IMAGE. Every wait is bounded;
QEMU is killed on any failure.
"""

import argparse
import os
import re
import select
import signal
import subprocess
import sys
import termios
import time
import tty

COMMAND = b"loady 0x140000000 && booti 0x140000000 - ${fdtcontroladdr}"
AUTOBOOT = re.compile(rb"Hit any key to stop autoboot|Autoboot in")
PROMPT = re.compile(rb"=> $")
READY = re.compile(rb"## Ready for binary \(ymodem\) download to "
                   rb"0x140000000 at \d+ bps\.\.\.")
TERMINAL = re.compile(rb"BE_B5:06 SHUTDOWN|BE_B5:FAIL|BE_K3_B3: FAIL")
PTY_PATH = re.compile(rb"char device redirected to (/dev/pts/\d+)")
SBI_VERSION = re.compile(rb"Runtime SBI Version\s*:\s*(\S+)")
MACHINE = "virt,aia=aplic-imsic,aia-guests=7"
CPU = "rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,"\
    "smstateen=true"
SBI = b"2.0"


class StageError(Exception):
    pass


class Console:
    """The harness's side of the UART PTY, logging what it reads."""

    def __init__(self, fd, log, qemu):
        self.fd = fd
        self.log = log
        self.qemu = qemu
        self.data = bytearray()
        self.closed = False

    def read_some(self, timeout):
        if self.closed:
            time.sleep(timeout)
            return
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return
        try:
            chunk = os.read(self.fd, 4096)
        except OSError:
            chunk = b""
        if not chunk:
            # QEMU closed the PTY (it exited).
            self.closed = True
            return
        self.data += chunk
        self.log.write(chunk)
        self.log.flush()

    def wait_for(self, pattern, start, timeout, stage):
        """Read until pattern matches data[start:]; return the match end."""
        deadline = time.monotonic() + timeout
        while True:
            match = pattern.search(self.data, start)
            if match:
                return match.end()
            if time.monotonic() >= deadline:
                raise StageError(f"{stage}: no {pattern.pattern!r} in "
                                 f"{timeout}s")
            if self.closed:
                raise StageError(f"{stage}: QEMU exited "
                                 f"(status {self.qemu.poll()})")
            self.read_some(0.1)

    def type(self, text):
        # A key at a time, as an operator types.
        for byte in text:
            os.write(self.fd, bytes([byte]))
            time.sleep(0.01)


def wait_file(path, pattern, timeout, process):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with open(path, "rb") as handle:
            match = pattern.search(handle.read())
        if match:
            return match.group(1)
        if process.poll() is not None:
            break
        time.sleep(0.05)
    return None


def stop(process):
    if process.poll() is None:
        process.kill()
    try:
        return process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        return None


def run_scenario(args, name, expect, image):
    stem = os.path.join(args.output, name)
    paths = {kind: f"{stem}.{kind}" for kind in
             ("console.log", "uart.log", "qemu.txt", "sz.txt", "status.txt",
              "check.txt", "result.json", "uart-check.txt",
              "uart-result.json")}
    for path in paths.values():
        if os.path.exists(path):
            os.unlink(path)
    argv = [args.qemu, "-machine", MACHINE, "-cpu", CPU, "-smp", "1",
            "-m", "8G", "-bios", args.firmware, "-kernel", args.uboot,
            "-display", "none", "-chardev",
            f"pty,id=uart0,logfile={paths['uart.log']},logappend=off",
            "-serial", "chardev:uart0", "-monitor", "stdio", "-no-reboot",
            "-S"]
    status = {"scenario": name, "expect": expect, "image": image,
              "qemu_exit": "none", "sz_exit": "none", "firmware_sbi": "none",
              "stage": "start"}
    started = time.monotonic()
    fd = None
    with open(paths["qemu.txt"], "wb") as qemu_out, \
            open(paths["console.log"], "wb") as console_log:
        qemu = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=qemu_out,
                                stderr=subprocess.STDOUT)
        try:
            status["stage"] = "pty"
            pty = wait_file(paths["qemu.txt"], PTY_PATH, 20, qemu)
            if pty is None:
                raise StageError("pty: QEMU reported no PTY")
            fd = os.open(pty, os.O_RDWR | os.O_NOCTTY)
            # Raw 115200 8N1, as picocom configures the USB serial adapter.
            tty.setraw(fd)
            attributes = termios.tcgetattr(fd)
            attributes[4] = attributes[5] = termios.B115200
            termios.tcsetattr(fd, termios.TCSANOW, attributes)
            console = Console(fd, console_log, qemu)
            qemu.stdin.write(b"cont\n")
            qemu.stdin.flush()

            status["stage"] = "autoboot"
            position = console.wait_for(AUTOBOOT, 0, args.boot_timeout,
                                        "autoboot")
            console.type(b"\r")
            status["stage"] = "prompt"
            position = console.wait_for(PROMPT, position, 15, "prompt")
            # Let the prompt settle, then type the operator's command.
            time.sleep(0.2)
            console.type(COMMAND + b"\r")
            status["stage"] = "loady"
            position = console.wait_for(READY, position, 15, "loady")

            status["stage"] = "ymodem"
            with open(paths["sz.txt"], "wb") as sz_log:
                try:
                    sz = subprocess.run(
                        ["sz", "-vv", "--ymodem", "-k", image], stdin=fd,
                        stdout=fd, stderr=sz_log, timeout=args.sz_timeout,
                        check=False)
                    status["sz_exit"] = str(sz.returncode)
                except subprocess.TimeoutExpired:
                    status["sz_exit"] = "timeout"
            if status["sz_exit"] != "0":
                raise StageError(f"ymodem: sz exit {status['sz_exit']}")

            status["stage"] = "terminal"
            console.wait_for(TERMINAL, position, args.run_timeout, "terminal")
            status["stage"] = "exit"
            deadline = time.monotonic() + args.exit_timeout
            while qemu.poll() is None and time.monotonic() < deadline:
                console.read_some(0.1)
            # Drain what QEMU wrote before it exited.
            while not console.closed:
                before = len(console.data)
                console.read_some(0.2)
                if len(console.data) == before:
                    break
            status["stage"] = "done"
        except StageError as error:
            status["error"] = str(error)
        finally:
            if qemu.poll() is None:
                status["qemu_exit"] = f"killed:{stop(qemu)}"
            else:
                status["qemu_exit"] = str(qemu.wait())
            if fd is not None:
                os.close(fd)
    status["seconds"] = f"{time.monotonic() - started:.1f}"
    with open(paths["uart.log"], "rb") as handle:
        match = SBI_VERSION.search(handle.read())
    if match:
        status["firmware_sbi"] = match.group(1).decode()
    checks = {}
    for log, check, result in (("console.log", "check.txt", "result.json"),
                               ("uart.log", "uart-check.txt",
                                "uart-result.json")):
        with open(paths[check], "wb") as check_out:
            checks[log] = subprocess.run(
                [sys.executable, "-B", args.checker, paths[log], "--expect",
                 expect, "--ram-base", args.ram_base, "--image", image,
                 "--json", paths[result]],
                stdout=check_out, stderr=subprocess.STDOUT,
                check=False).returncode
        status[f"check_{log.split('.')[0]}"] = str(checks[log])
    with open(paths["status.txt"], "w", encoding="utf-8") as handle:
        for key, value in status.items():
            handle.write(f"{key}={value}\n")
    ok = (status["stage"] == "done" and status["qemu_exit"] == "0" and
          status["sz_exit"] == "0" and status["firmware_sbi"] == SBI.decode()
          and not any(checks.values()))
    with open(paths["check.txt"], encoding="utf-8") as handle:
        report = handle.read()
    shim = re.search(r"^BE_K3_B3: .*$", report, re.M)
    markers = len(re.findall(r"^(?:BE_R[0-9]:|BE_B5:|BE_B5_GUEST: )", report,
                             re.M))
    line = (f"BE_B5_QEMU_UBOOT[{name}]: {'PASS' if ok else 'FAIL'} "
            f"({expect}; {markers} markers; SBI {status['firmware_sbi']}; "
            f"sz_exit={status['sz_exit']} qemu_exit={status['qemu_exit']}; "
            f"{status['seconds']}s)")
    print(line, flush=True)
    print(f"  {shim.group(0) if shim else 'no BE_K3_B3 line'}", flush=True)
    if not ok:
        print(f"  stage={status['stage']} error={status.get('error', '-')}",
              file=sys.stderr)
        sys.stderr.write(report)
    return ok, line


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--firmware", required=True)
    parser.add_argument("--uboot", required=True)
    parser.add_argument("--checker", required=True)
    parser.add_argument("--ram-base", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--qemu", default=os.environ.get(
        "QEMU", "qemu-system-riscv64"))
    parser.add_argument("--boot-timeout", type=float, default=60)
    parser.add_argument("--sz-timeout", type=float, default=180)
    parser.add_argument("--run-timeout", type=float, default=60)
    parser.add_argument("--exit-timeout", type=float, default=15)
    parser.add_argument("scenarios", nargs="+",
                        metavar="SCENARIO:EXPECT:IMAGE")
    args = parser.parse_args()
    for path in (args.firmware, args.uboot, args.checker):
        if not os.access(path, os.R_OK):
            parser.error(f"{path} is not readable")
    os.makedirs(args.output, exist_ok=True)
    # A SIGTERM still runs the cleanup in run_scenario.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    summary = []
    failed = 0
    for spec in args.scenarios:
        name, expect, image = spec.split(":", 2)
        if expect not in ("pass", "overlap"):
            parser.error(f"{spec}: EXPECT must be pass or overlap")
        ok, line = run_scenario(args, name, expect, os.path.abspath(image))
        failed += not ok
        summary.append(line)
    summary.append(f"BE_B5_QEMU_UBOOT: {'PASS' if not failed else 'FAIL'} "
                   f"scenarios={len(args.scenarios)} failed={failed}")
    print(summary[-1])
    with open(os.path.join(args.output, "summary.txt"), "w",
              encoding="utf-8") as handle:
        handle.write("\n".join(summary) + "\n")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
