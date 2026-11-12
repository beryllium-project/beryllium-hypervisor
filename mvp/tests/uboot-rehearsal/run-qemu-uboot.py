#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""One attempt of the MVP's U-Boot rehearsal in QEMU, and its own checks.

  run-qemu-uboot.py session --label LABEL --firmware FW --uboot UBOOT
      --uboot-elf UBOOT_ELF --disk DISK --image QEMU_IMG --file NAME
      (--expect EXPECT | --fallthrough) --machine MACHINE --cpu CPU
      --output DIR
      [--qemu QEMU] [--boot-timeout S] [--run-timeout S] [--exit-timeout S]
  run-qemu-uboot.py derive BOARD_IMG OUT
  run-qemu-uboot.py relation BOARD_IMG QEMU_IMG
  run-qemu-uboot.py self-test

Purpose: the driver of tests/uboot-rehearsal.sh (planning/mvp-m5-plan.md,
"The U-Boot rehearsal in QEMU (M5-3)"), after B3's tests/run-qemu-uboot.py
(accepted at 9b4860a0). `session` boots QEMU virt with MACHINE and CPU,
eight harts, and 8 GiB: OpenSBI as -bios, U-Boot as -kernel, and DISK as a
virtio block device, with the UART on QEMU's stdin and stdout, which QEMU
also logs. Through them it does what the session does at the board's
prompt: at `Hit any key to stop autoboot` a space; at each `=> ` one
session line, typed a key at a time (B3's pace), with Enter only once
U-Boot's echo is exactly the line; after `boot`, for a scenario, it reads to the expectation's terminal
marker and the guest's shutdown. The QEMU oracle then reads all eight
harts, U-Boot's entry word, and the moved boot image's header word while
the machine is stopped, and quits QEMU. For the fall-through, the harness
stops the machine after the stand-in command's FALLTHROUGH line and the
prompt, the oracle reads the harts and U-Boot's entry word, and quits
QEMU. A pipe, unlike B3's PTY, keeps the last UART bytes.

The session lines (session_lines) are the M5 plan's be_* lines and bootcmd
with `virtio` in place of `nvme` (QEMU has no NVMe here) and `crc32` in
place of the board's `md5sum` (upstream's qemu-riscv64_smode_defconfig has
no md5sum; the board's BSP U-Boot has one, and its crc32 prints nothing),
without be_boot's leading `nvme scan;`, and with a stand-in
be_orig_bootcmd that prints FALLTHROUGH; they are set in RAM and run by a
typed `boot`, since QEMU's U-Boot has no saved environment and no reset
that reads one back. The board never types `boot`.

Outputs in DIR: console.log, every byte the driver read (the capture);
uart.log, QEMU's own log of every byte the UART sent, which must equal it;
qemu.txt, the command line, then QEMU's own messages; typed.txt, each key
and line sent, with its time after QEMU's start and in UTC and its echo's
verdict; session.txt, the session's facts, the findings, and last
`BE_MVP_UBOOT_SESSION[LABEL]: PASS|REFUSED|FAIL ...`; and oracle.json.
Exit 0 PASS, 3 REFUSED, 1 FAIL, 2 usage.

The rehearsal's own checks (judge), independent of tests/check-capture.py
and kept beside it: OpenSBI's banner names one boot hart and SBI 3.0; one
U-Boot banner and one autoboot line; the prompt lines are exactly the typed
lines in order (and, for the fall-through, a fresh prompt last); then, for
a scenario, after `boot`, once each and in order: `N bytes read` with N the
image's size; `crc32 for 140000000 ... E ==> C` with E = 0x140000000 + N - 1
and C the image's CRC-32; `Moving Image from 0x140000000 to L, end=` L plus
the header's image_size; `## Flattened Device Tree blob at A`; `Booting
using the fdt blob at 0xA`; `Using Device Tree in place at F, end E` with
F = A; `Starting kernel ...`; then the markers: the shim's start-rule line
when the boot hart B is not 0, B equal to OpenSBI's boot hart, then the
SHIM line with shim = L and fdt = F; no FALLTHROUGH line; a whole last line;
and the outcome: a boot hart that is one of the run's domain harts (its
BE_MVP:01 line) with `BE_MVP:FAIL firmware` first and no BE_MVP:14 is
REFUSED, the precondition Plan revision M0-A.2 declares; otherwise a pass
or probe image ends with BE_MVP:14 SHUTDOWN and no BE_MVP:FAIL, and a
failing image's first BE_MVP:FAIL is its declared class. For the
fall-through: none of those boot lines, no marker, and exactly one
FALLTHROUGH line after `boot`.

`derive` writes the QEMU-only image of a board image (M5 plan, "Tool
changes (M5-2)"): the same bytes but header bytes 8 to 15, text_offset, set
to BE_MVP_QEMU_TEXT_OFFSET (src/mvp-layout.h) little-endian, so that booti
places it at L from QEMU's RAM base as the board's text_offset does from
the board's; it refuses an image without B3's header, the board's
text_offset, and image_size equal to its size. `relation` requires
QEMU_IMG to be exactly BOARD_IMG's derivation. Both print the QEMU-only
image's facts as KEY=VALUE lines. `self-test` runs judge on synthetic
captures (a scenario, boot hart 0, a refusal, a declared failure, the
fall-through, and each seeded single defect), derive on a synthetic board
image and three it must refuse, and session_lines on be_image names it
must refuse.
Trust: a test driver; it runs only QEMU and writes only DIR or OUT. Every
wait is bounded, and QEMU is killed on any failure.
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
import signal
import struct
import subprocess
import sys
import time
import zlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import qemu_oracle  # noqa: E402 pylint: disable=wrong-import-position

LAYOUT_H = HERE.parents[1] / "src" / "mvp-layout.h"
# The plan's literal load address (Q2), which be_ld and be_go type.
LOAD = 0x140000000
# B3's RISC-V Image header (bringup/k3-b3/tests/check-b3-image.py): code0,
# code1, text_offset (bytes 8 to 15), image_size, flags, version, res1,
# res2, magic, magic2, res3.
HEADER = struct.Struct("<IIQQQIIQ8s4sI")
FILE_NAME = re.compile(r"[a-z0-9][a-z0-9.-]{0,46}\.img")
FALLTHROUGH = "BE_UBOOT_REHEARSAL: FALLTHROUGH"
AUTOBOOT = re.compile(rb"Hit any key to stop autoboot")
PROMPT = re.compile(rb"=> $")
FALLEN = re.compile(rb"^" + FALLTHROUGH.encode() + rb"\r?\n", re.M)
SBI_LINE = re.compile(r"Runtime SBI Version\s*:\s*(\S+)")
BOOT_HART = re.compile(r"Boot HART ID\s*:\s*([0-9]+)")
BANNER = re.compile(r"U-Boot 20[0-9]{2}\.[0-9]{2}.*")
AUTOBOOT_LINE = re.compile(r"Hit any key to stop autoboot:.*")
# U-Boot v2022.10's lines from be_ld and be_go, in their order.
BOOT_LINES = (
    ("bytes read", re.compile(r"([0-9]+) bytes read in [0-9]+ ms(?: \(.*\))?")),
    ("crc32", re.compile(r"crc32 for 140000000 \.\.\. ([0-9a-f]+) ==> "
                         r"([0-9a-f]{8})")),
    ("Moving Image", re.compile(r"Moving Image from 0x140000000 to "
                                r"0x([0-9a-f]+), end=([0-9a-f]+)")),
    ("Flattened Device Tree", re.compile(r"## Flattened Device Tree blob at "
                                         r"([0-9a-f]+)")),
    ("Booting using", re.compile(r"   Booting using the fdt blob at "
                                 r"0x([0-9a-f]+)")),
    ("Using Device Tree", re.compile(r"   Using Device Tree in place at "
                                     r"([0-9a-f]{16}), end ([0-9a-f]{16})")),
    ("Starting kernel", re.compile(r"Starting kernel \.\.\.")),
)
MARKER = re.compile(r"BE_MVP_SHIM: |BE_K3_B3: |BE_R3:|BE_MVP:|BE_MVP_G[0-9]+: ")
RULE = re.compile(r"BE_MVP_SHIM: boot_hart=0x([1-9a-f][0-9a-f]*) "
                  r"starting hart 0")
SHIM = re.compile(r"BE_K3_B3: SHIM hart=0x[0-9a-f]{16} shim=0x([0-9a-f]{16}) "
                  r"fdt=0x([0-9a-f]{16}) dest=0x[0-9a-f]{16} "
                  r"bytes=0x[0-9a-f]{16}")
VERDICT_STATUS = {"PASS": 0, "FAIL": 1, "REFUSED": 3}


class Refused(Exception):
    """An input the driver will not use."""


class Stop(Exception):
    """A session stage that did not complete."""


def layout(path=LAYOUT_H):
    """Every BE_MVP_* literal of mvp-layout.h (as tests/check-capture.py
    reads them); QEMU's RAM base plus its text_offset must be L."""
    values = {name: int(value, 0) for name, value in re.findall(
        r"^#define\s+BE_MVP_(\w+)\s+BE_MVP_C\((0x[0-9a-fA-F]+|\d+)\)",
        pathlib.Path(path).read_text(encoding="utf-8"), re.M)}
    if values["QEMU_RAM_BASE"] + values["QEMU_TEXT_OFFSET"] != \
            values["STAGING_HPA"]:
        raise Refused("QEMU's RAM base plus BE_MVP_QEMU_TEXT_OFFSET is not L")
    return values


def session_lines(name):
    """The lines typed at the prompt, `boot` last, for be_image NAME."""
    if not FILE_NAME.fullmatch(name):
        raise Refused(f"be_image {name!r} is not a plain .img file name")
    return ["setenv be_part 1", f"setenv be_image {name}",
            "setenv be_ld 'load virtio 0:${be_part} 0x140000000 "
            "/${be_image} && crc32 0x140000000 ${filesize}'",
            "setenv be_go 'booti 0x140000000 - ${fdtcontroladdr}'",
            "setenv be_boot 'if run be_ld; then run be_go; fi'",
            f"setenv be_orig_bootcmd 'echo {FALLTHROUGH}; sleep 1'",
            "setenv bootcmd 'run be_boot; run be_orig_bootcmd'", "boot"]


def qemu_image(board, values):
    """The QEMU-only image of the board image BOARD (bytes)."""
    if len(board) < HEADER.size:
        raise Refused("the board image is shorter than B3's header")
    fields = HEADER.unpack_from(board)
    if fields[8] != b"RISCV\0\0\0" or fields[9] != b"RSC\x05":
        raise Refused("the board image has no RISC-V Image header")
    if fields[2] != values["UBOOT_TEXT_OFFSET"] or fields[3] != len(board):
        raise Refused(f"the board image's text_offset 0x{fields[2]:x} and "
                      f"image_size 0x{fields[3]:x} are not the board's "
                      f"0x{values['UBOOT_TEXT_OFFSET']:x} and its size "
                      f"0x{len(board):x}")
    return board[:8] + struct.pack("<Q", values["QEMU_TEXT_OFFSET"]) + \
        board[16:]


def domain_harts(expect):
    """The run's domain harts, as its BE_MVP:01 line names them."""
    for entry in expect["control_lines"]:
        match = re.search(r"^BE_MVP:01 .* harts=([0-9,]+) ", entry["template"])
        if match:
            return [int(hart) for hart in match.group(1).split(",")[1:]]
    raise Refused("the expectation has no BE_MVP:01 line naming its harts")


def judge(data, lines, image, values, expect=None):
    """The rehearsal's own checks on the capture DATA of a session that
    typed LINES and loaded IMAGE: (verdict, findings, facts). EXPECT, the
    image's expectation, judges a scenario; None, the fall-through."""
    rows = data.decode("latin-1").replace("\r", "").split("\n")
    findings, facts = [], {}

    def hits(pattern):
        return [(number, match) for number, row in enumerate(rows)
                for match in [pattern.fullmatch(row)] if match]

    def single(pattern, what):
        found = hits(pattern)
        if len(found) != 1:
            findings.append(f"{len(found)} {what} lines, expected 1")
            return None
        return found[0][1]

    sbi = single(SBI_LINE, "OpenSBI 'Runtime SBI Version'")
    if sbi:
        facts["sbi_version"] = sbi.group(1)
        if sbi.group(1) != "3.0":
            findings.append(f"the firmware's SBI version is {sbi.group(1)}, "
                            f"not the firmware base's 3.0")
    hart = single(BOOT_HART, "OpenSBI 'Boot HART ID'")
    if hart:
        facts["boot_hart"] = hart.group(1)
    banner = single(BANNER, "U-Boot banner")
    if banner:
        facts["uboot"] = banner.group(0)
    single(AUTOBOOT_LINE, "autoboot")
    prompts = [(number, row[3:]) for number, row in enumerate(rows)
               if row.startswith("=> ")]
    typed = [text for _, text in prompts]
    want = list(lines) + ([] if expect else [""])
    if typed != want:
        findings.append(f"the prompt lines {typed} are not the typed lines "
                        f"{want}")
    boot = next((number for number, text in prompts if text == "boot"),
                len(rows))
    found = {}
    for name, pattern in BOOT_LINES:
        matched = hits(pattern)
        if expect is None:
            if matched:
                findings.append(f"a {name!r} line in the fall-through")
        elif len(matched) != 1 or matched[0][0] < boot:
            findings.append(f"{len(matched)} {name!r} lines, expected 1 "
                            f"after `boot`")
        else:
            found[name] = matched[0]
    first = next((number for number, row in enumerate(rows)
                  if MARKER.search(row)), None)
    fallen = [number for number, row in enumerate(rows) if row == FALLTHROUGH]
    if expect is None:
        if first is not None:
            findings.append(f"a marker line in the fall-through: "
                            f"{rows[first][:60]!r}")
        if len(fallen) != 1 or fallen[0] < boot:
            findings.append(f"{len(fallen)} {FALLTHROUGH!r} lines after "
                            f"`boot`, expected 1")
        return ("FAIL" if findings else "PASS"), findings, facts
    numbers = [found[name][0] for name, _ in BOOT_LINES if name in found]
    if numbers != sorted(numbers):
        findings.append("U-Boot's boot lines are out of order")
    size, base = len(image), values["STAGING_HPA"]
    fdt = None
    if "bytes read" in found:
        facts["bytes_read"] = found["bytes read"][1].group(1)
        if int(facts["bytes_read"]) != size:
            findings.append(f"U-Boot read {facts['bytes_read']} bytes, not "
                            f"the image's {size}")
    if "crc32" in found:
        end, facts["crc32"] = found["crc32"][1].groups()
        if int(end, 16) != LOAD + size - 1 or \
                int(facts["crc32"], 16) != zlib.crc32(image):
            findings.append(f"crc32 ... {end} ==> {facts['crc32']} is not the "
                            f"image's {LOAD + size - 1:x} ==> "
                            f"{zlib.crc32(image):08x}")
    if "Moving Image" in found:
        dest, end = (int(value, 16) for value in
                     found["Moving Image"][1].groups())
        image_size = HEADER.unpack_from(image)[3]
        if dest != base or end != base + image_size:
            findings.append(f"booti moved the image to 0x{dest:x}, end "
                            f"{end:x}, not L 0x{base:x}, end "
                            f"{base + image_size:x}")
    if {"Flattened Device Tree", "Booting using",
            "Using Device Tree"} <= set(found):
        blob = int(found["Flattened Device Tree"][1].group(1), 16)
        fdt, fdt_end = (int(value, 16) for value in
                        found["Using Device Tree"][1].groups())
        facts.update(fdt=f"0x{fdt:x}", fdt_end=f"0x{fdt_end:x}")
        if int(found["Booting using"][1].group(1), 16) != blob or \
                fdt != blob or fdt_end <= fdt:
            findings.append(f"the device tree blob 0x{blob:x}, the one booted "
                            f"with, and the one in place 0x{fdt:x} differ")
    if first is None or "Starting kernel" not in found or \
            first < found["Starting kernel"][0]:
        findings.append("the markers do not follow `Starting kernel ...`")
    markers = rows[first:] if first is not None else []
    if not data.endswith(b"\n"):
        findings.append("the capture ends mid-line")
    elif markers:
        markers.pop()
    rule = 0
    if markers and markers[0].startswith("BE_MVP_SHIM: "):
        match = RULE.fullmatch(markers.pop(0))
        if match:
            rule = int(match.group(1), 16)
        else:
            findings.append("a malformed start-rule line")
    facts["rule_hart"] = str(rule)
    if hart and int(hart.group(1)) != rule:
        findings.append(f"OpenSBI's boot hart {hart.group(1)} is not the "
                        f"shim's {rule}")
    shim = SHIM.fullmatch(markers[0]) if markers else None
    if not shim:
        findings.append("no SHIM line opens the markers")
    else:
        facts["shim_fdt"] = f"0x{int(shim.group(2), 16):x}"
        if int(shim.group(1), 16) != base or int(shim.group(2), 16) != fdt:
            findings.append(f"the SHIM line's shim 0x{shim.group(1)} or fdt "
                            f"0x{shim.group(2)} is not L or U-Boot's device "
                            f"tree")
    if fallen:
        findings.append(f"a {FALLTHROUGH!r} line in a booted run")
    monitor = [row for row in markers if row.startswith("BE_MVP:")]
    fails = [row for row in monitor if row.startswith("BE_MVP:FAIL ")]
    terminal = re.compile(expect["terminal_regex"])
    facts["terminal"] = next((row for row in monitor if terminal.search(row)),
                             "none")
    outcome = expect["outcome"]
    if rule in domain_harts(expect):
        if fails[:1] != ["BE_MVP:FAIL firmware"] or \
                any(row.startswith("BE_MVP:14 ") for row in monitor):
            findings.append(f"the boot hart {rule} is a domain hart, but the "
                            f"run is no refusal")
        elif not findings:
            return "REFUSED", findings, facts
    elif "fail" in outcome:
        if fails[:1] != [f"BE_MVP:FAIL {outcome['fail']}"]:
            findings.append(f"the first failure {fails[:1]} is not the "
                            f"declared BE_MVP:FAIL {outcome['fail']}")
    elif fails or not markers or \
            not markers[-1].startswith("BE_MVP:14 SHUTDOWN"):
        findings.append(f"the run ends {markers[-1:]}, with failures {fails}, "
                        f"not with BE_MVP:14 SHUTDOWN")
    return ("FAIL" if findings else "PASS"), findings, facts


# ------------------------------------------------------------- the session
class Console:
    """The driver's side of the UART, QEMU's stdin and stdout, logging
    what it reads."""

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
            self.closed = True  # QEMU exited
            return
        self.data += chunk
        self.log.write(chunk)
        self.log.flush()

    def wait(self, test, timeout, stage):
        """Read until test() is not None; return it."""
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

    def drain(self):
        """Read until 0.2 s pass with nothing new, or QEMU's end."""
        while not self.closed:
            before = len(self.data)
            self.read_some(0.2)
            if len(self.data) == before:
                break


class Typed:
    """typed.txt: each key or line sent, its times, and its echo."""

    def __init__(self, path):
        self.handle = open(path, "w", encoding="utf-8")
        self.handle.write("# seconds after QEMU's start, UTC, what, echo, "
                          "text; a line is typed a key at a time, then Enter "
                          "once its echo matched\n")
        self.started = time.monotonic()

    def record(self, what, echo, text):
        now = datetime.datetime.now(datetime.timezone.utc)
        self.handle.write(f"+{time.monotonic() - self.started:.3f} "
                          f"{now:%Y-%m-%dT%H:%M:%S}."
                          f"{now.microsecond // 1000:03d}Z {what} {echo} "
                          f"{text}\n")
        self.handle.flush()


def type_line(console, typed, line, start):
    """LINE at the prompt that ends at START, a key at a time (B3's pace),
    then Enter once U-Boot's echo is exactly LINE; the echo's end."""
    text = line.encode("ascii")
    time.sleep(0.2)
    for byte in text:
        console.write(bytes([byte]))
        time.sleep(0.01)

    def echoed():
        echo = bytes(console.data[start:])
        if not text.startswith(echo):
            typed.record("line", "mismatch", line)
            raise Stop(f"echo: {echo!r} for {line!r}")
        return True if echo == text else None

    console.wait(echoed, 10, f"echo of {line!r}")
    typed.record("line", "ok", line)
    console.write(b"\r")
    return start + len(text)


def run_session(args, paths, lines, expect, status, config):
    """QEMU through the session into PATHS; STATUS records how far it got."""
    argv = [args.qemu, "-machine", args.machine, "-cpu", args.cpu, "-smp", "8",
            "-m", "8G", "-bios", args.firmware, "-kernel", args.uboot,
            "-display", "none", "-no-reboot", "-drive",
            f"file={args.disk},format=raw,if=none,id=d0", "-device",
            "virtio-blk-device,drive=d0", "-chardev",
            f"stdio,id=uart0,signal=off,logfile={paths['uart.log']},"
            "logappend=off", "-serial", "chardev:uart0"]
    terminal = re.compile(expect["terminal_regex"].encode()) if expect \
        else None
    with open(paths["qemu.txt"], "wb") as qemu_out, \
            open(paths["console.log"], "wb") as log:
        qemu_out.write(f"argv: {shlex.join(argv)}\n".encode())
        qemu_out.flush()
        typed = Typed(paths["typed.txt"])
        try:
            oracle = qemu_oracle.OracleProcess.launch(
                argv, config, paths["oracle.json"], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=qemu_out)
        except (qemu_oracle.OracleError, OSError):
            qemu_oracle.write_failure_record(
                paths["oracle.json"], "QEMU or QMP setup failed")
            status["error"] = "oracle: QEMU or QMP setup failed"
            status["qemu_exit"] = "killed:none"
            typed.handle.close()
            return
        qemu = oracle.process
        console = Console(qemu, log)
        end_state, harness_reason, harness_pass = None, None, False
        try:
            status["stage"] = "autoboot"
            position = console.find(AUTOBOOT, 0, args.boot_timeout, "autoboot")
            console.write(b" ")
            typed.record("key", "-", "<space>")
            position = console.find(PROMPT, position, 15, "prompt")
            for number, line in enumerate(lines, 1):
                status["stage"] = f"line-{number}"
                position = type_line(console, typed, line, position)
                if line != "boot":
                    position = console.find(PROMPT, position, 15,
                                            f"prompt after {line!r}")
            if expect:
                status["stage"] = "run"
                console.find(terminal, position, args.run_timeout, "run")
                status["stage"] = "exit"
                deadline = time.monotonic() + args.exit_timeout
                while not console.closed and time.monotonic() < deadline:
                    try:
                        end_state = oracle.poll_end()
                    except qemu_oracle.OracleError as error:
                        raise Stop(f"oracle: {error}") from None
                    if end_state is not None:
                        break
                    console.read_some(0.1)
                if end_state is None:
                    harness_reason = (f"exit limit {args.exit_timeout:g} s "
                                      "after the terminal marker")
            else:
                status["stage"] = "fallthrough"
                position = console.find(FALLEN, position, 60, "fallthrough")
                console.find(PROMPT, position, 15, "prompt after FALLTHROUGH")
                time.sleep(1)
                harness_reason = "fallthrough complete"
                harness_pass = True
            console.drain()
            status["stage"] = "done"
        except (Stop, OSError) as error:
            status["error"] = str(error)
            harness_reason = harness_reason or \
                f"session stopped at {status['stage']}"
        finally:
            outcome = oracle.finish(end=end_state,
                                    harness_reason=harness_reason,
                                    harness_pass=harness_pass)
            status["oracle_verdict"] = "PASS" if outcome.passed else "FAIL"
            status["oracle"] = outcome.detail
            if not outcome.passed:
                status["error"] = (
                    f"{status['error']}; " if status["error"] != "-" else ""
                ) + f"oracle: {outcome.detail}"
            status["qemu_exit"] = qemu_oracle.launcher_exit(qemu.returncode)
            console.drain()
            for pipe in (qemu.stdin, qemu.stdout):
                try:
                    pipe.close()
                except OSError:
                    pass
            typed.handle.close()


def session(args):
    values = layout()
    lines = session_lines(args.file)
    expect = json.loads(pathlib.Path(args.expect).read_text(
        encoding="utf-8")) if args.expect else None
    image = pathlib.Path(args.image).read_bytes()
    words = [qemu_oracle.word_from_binary_elf(
        "u-boot-entry", args.uboot, args.uboot_elf)]
    if expect:
        words.append(qemu_oracle.word_from_image(
            "boot-image-header", args.image, values["STAGING_HPA"]))
    config = qemu_oracle.OracleConfig(
        8, "k3-like", False, "readable", "readable", "absent",
        0x80000000, 0x200000000, tuple(words))
    config.validate()
    out = pathlib.Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    paths = {name: out / name for name in (
        "console.log", "uart.log", "qemu.txt", "typed.txt", "session.txt",
        "oracle.json")}
    for path in paths.values():
        if path.exists():
            path.unlink()
    status = {"label": args.label,
              "kind": "scenario" if expect else "fallthrough",
              "file": args.file, "stage": "start", "error": "-",
              "qemu_exit": "none"}
    started = time.monotonic()
    try:
        run_session(args, paths, lines, expect, status, config)
    except OSError as error:
        status["error"] = f"QEMU: {error}"
    status["seconds"] = f"{time.monotonic() - started:.1f}"
    data = paths["console.log"].read_bytes() \
        if paths["console.log"].exists() else b""
    verdict, findings, facts = judge(data, lines, image, values, expect)
    if status["stage"] != "done":
        findings.insert(0, f"the session stopped at {status['stage']}: "
                        f"{status['error']}")
    if status.get("oracle_verdict") != "PASS":
        findings.insert(0, status.get("error", "the oracle did not pass"))
    wanted = "0"
    if status["qemu_exit"] != wanted:
        findings.append(f"QEMU's exit {status['qemu_exit']}, not {wanted}")
    uart = paths["uart.log"].read_bytes() if paths["uart.log"].exists() \
        else b""
    if uart != data:
        findings.append(f"console.log ({len(data)} bytes) is not QEMU's "
                        f"uart.log ({len(uart)} bytes)")
    verdict = "FAIL" if findings else verdict
    status.update(facts)
    status.update(console_bytes=str(len(data)),
                  console_sha256=hashlib.sha256(data).hexdigest())
    detail = (f"fdt={facts.get('fdt', 'none')} "
              f"crc32={facts.get('crc32', 'none')}" if expect else
              f"fallthrough={'no' if findings else 'yes'}")
    line = (f"BE_MVP_UBOOT_SESSION[{args.label}]: {verdict} "
            f"boot_hart={facts.get('boot_hart', 'none')} "
            f"qemu_exit={status['qemu_exit']} "
            f"oracle={status.get('oracle_verdict', 'FAIL')} {detail} "
            f"seconds={status['seconds']}")
    paths["session.txt"].write_text(
        "".join(f"{key}={value}\n" for key, value in status.items())
        + "".join(f"finding: {finding}\n" for finding in findings)
        + line + "\n", encoding="utf-8")
    print(line, flush=True)
    for finding in findings[:8]:
        print(f"  finding: {finding}", file=sys.stderr)
    return VERDICT_STATUS[verdict]


# --------------------------------------------------------------- self-test
def synthetic(lines, image, values, rule=3, opensbi=None, fdt=0xff7383d0,
              tail=("BE_MVP:14 SHUTDOWN type=0 reason=0",)):
    """A scenario capture of the shape QEMU's U-Boot and the MVP print."""
    base, size = values["STAGING_HPA"], len(image)
    rows = ["OpenSBI", "Runtime SBI Version         : 3.0",
            f"Domain0 Boot HART           : {rule}",
            f"Boot HART ID                : "
            f"{rule if opensbi is None else opensbi}",
            "", "U-Boot 2022.10 (Oct 03 2022 - 19:25:32 +0000)",
            "Hit any key to stop autoboot:  2 \b\b\b 0 "]
    rows += [f"=> {line}" for line in lines]
    rows += [f"{size} bytes read in 3 ms (821.6 MiB/s)",
             f"crc32 for 140000000 ... {LOAD + size - 1:x} ==> "
             f"{zlib.crc32(image):08x}",
             f"Moving Image from 0x140000000 to 0x{base:x}, "
             f"end={base + size:x}",
             f"## Flattened Device Tree blob at {fdt:08x}",
             f"   Booting using the fdt blob at 0x{fdt:08x}",
             f"   Using Device Tree in place at {fdt:016x}, end "
             f"{fdt + 0x6a08:016x}", "", "Starting kernel ...", ""]
    if rule:
        rows.append(f"BE_MVP_SHIM: boot_hart=0x{rule:x} starting hart 0")
    rows += [f"BE_K3_B3: SHIM hart=0x{0:016x} shim=0x{base:016x} "
             f"fdt=0x{fdt:016x} dest=0x{0x102000000:016x} "
             f"bytes=0x{0xa4000:016x}", "BE_R3:01 BOOT_VALIDATED",
             "BE_MVP:01 SCENARIO name=x domains=2 harts=0,1,2 of=8",
             "BE_MVP_G0: MVPINIT 01 START guest=0 pid=1", *tail]
    return ("\r\n".join(rows) + "\r\n").encode("latin-1")


def self_test():
    values = layout()
    failures, cases = [], 0
    body = bytes(range(256)) * 12
    board = HEADER.pack(0x0400006f, 0, values["UBOOT_TEXT_OFFSET"],
                        HEADER.size + len(body), 0, 2, 0, 0, b"RISCV\0\0\0",
                        b"RSC\x05", 0) + body
    image = qemu_image(board, values)
    size, crc = len(image), zlib.crc32(image)
    lines = session_lines("two-guests-gcc.img")
    missing = session_lines("missing.img")
    expect = {"control_lines": [{"template": "BE_MVP:01 SCENARIO name=x "
                                 "domains=2 harts=0,1,2 of=8 ring_bytes=x"}],
              "outcome": {"pass": True},
              "terminal_regex": "BE_MVP:14 SHUTDOWN|BE_MVP:FAIL|BE_K3_B3: FAIL"}
    good = synthetic(lines, image, values)

    def case(name, data, verdict, wanted=None, test_expect=expect,
             typed=lines):
        nonlocal cases
        cases += 1
        got, findings, _ = judge(data, typed, image, values, test_expect)
        if got != verdict or (wanted and not any(wanted in finding
                                                 for finding in findings)):
            failures.append(f"{name}: {got} {findings[:3]}")

    def refused(name, action):
        nonlocal cases
        cases += 1
        try:
            action()
            failures.append(f"{name}: not refused")
        except Refused:
            pass

    def swap(old, new, data=good):
        if old.encode("latin-1") not in data:
            raise KeyError(old)
        return data.replace(old.encode("latin-1"), new.encode("latin-1"), 1)

    case("a scenario capture", good, "PASS")
    case("boot hart 0, no start-rule line", synthetic(
        lines, image, values, rule=0), "PASS")
    rows = good.decode("latin-1").split("\r\n")
    for name, pattern in BOOT_LINES:
        row = next(row for row in rows if pattern.fullmatch(row))
        case(f"no {name!r} line", swap(row + "\r\n", ""), "FAIL", name)
        case(f"two {name!r} lines", swap(row, row + "\r\n" + row), "FAIL",
             name)
    base = values["STAGING_HPA"]
    for name, old, new, wanted in (
            ("a wrong size", f"{size} bytes", f"{size + 1} bytes", "read"),
            ("a wrong CRC", f"==> {crc:08x}", f"==> {crc ^ 1:08x}", "crc32"),
            ("a wrong relocation", f"to 0x{base:x}",
             f"to 0x{base - 0x2000000:x}", "moved"),
            ("a device tree not in place", "in place at 00000000ff7383d0",
             "in place at 00000000ff7393d0", "differ"),
            ("the shim's fdt not U-Boot's", "fdt=0x00000000ff7383d0",
             "fdt=0x00000000ff7393d0", "SHIM line"),
            ("a second U-Boot banner", "Hit any key",
             "U-Boot 2022.10 (Oct 03 2022)\r\nHit any key", "U-Boot banner"),
            ("SBI 2.0", ": 3.0", ": 2.0", "SBI version"),
            ("an echo that differs", "=> setenv be_part 1",
             "=> setenv be_part 2", "typed lines"),
            ("a fall-through in a booted run", "Starting kernel ...",
             f"{FALLTHROUGH}\r\nStarting kernel ...", "booted run"),
            ("a BE_MVP:FAIL", "BE_MVP:14 SHUTDOWN",
             "BE_MVP:FAIL ring\r\nBE_MVP:14 SHUTDOWN", "failures"),
            ("a marker before Starting kernel", "Starting kernel ...",
             "BE_R3:01 BOOT_VALIDATED\r\nStarting kernel ...", "follow")):
        case(name, swap(old, new), "FAIL", wanted)
    case("no BE_MVP:14", synthetic(lines, image, values, tail=()), "FAIL",
         "BE_MVP:14")
    case("a capture cut mid-line", good[:-2], "FAIL", "mid-line")
    case("OpenSBI's boot hart not the shim's", synthetic(
        lines, image, values, opensbi=4), "FAIL", "not the shim's")
    refusal = ("BE_MVP:02 FIRMWARE_PROBED started=1", "BE_MVP:FAIL firmware")
    case("a domain boot hart refused", synthetic(
        lines, image, values, rule=1, tail=refusal), "REFUSED")
    case("a refused run with a broken preamble", swap(
        "Starting kernel ...", "Starting kernel ...\r\nStarting kernel ...",
        synthetic(lines, image, values, rule=1, tail=refusal)), "FAIL")
    case("a domain boot hart that ran", synthetic(
        lines, image, values, rule=2), "FAIL", "no refusal")
    failing = dict(expect, outcome={"after": "BE_MVP:03", "fail": "payload"})
    case("a declared failure", synthetic(
        lines, image, values, tail=("BE_MVP:FAIL payload",)), "PASS",
        test_expect=failing)
    case("an undeclared failure", synthetic(
        lines, image, values, tail=("BE_MVP:FAIL gstage",)), "FAIL",
        "declared", failing)
    head = good.split(b"=> setenv")[0].decode("latin-1")
    fall = (head + "".join(f"=> {line}\r\n" for line in missing)
            + "** File not found /missing.img **\r\nFailed to load "
            f"'/missing.img'\r\n{FALLTHROUGH}\r\n=> ").encode("latin-1")
    case("the fall-through", fall, "PASS", test_expect=None, typed=missing)
    for name, old, new, wanted in (
            ("a boot after the fall-through", f"{FALLTHROUGH}\r\n",
             f"{FALLTHROUGH}\r\nStarting kernel ...\r\n", "Starting kernel"),
            ("no FALLTHROUGH line", f"\r\n{FALLTHROUGH}\r\n", "\r\n",
             "FALLTHROUGH"),
            ("a load", "** File not found /missing.img **",
             f"{size} bytes read in 3 ms", "bytes read"),
            ("a marker", f"{FALLTHROUGH}\r\n",
             f"{FALLTHROUGH}\r\nBE_K3_B3: SHIM\r\n", "marker"),
            ("no prompt after it", f"{FALLTHROUGH}\r\n=> ",
             f"{FALLTHROUGH}\r\n", "typed lines")):
        case(name, swap(old, new, fall), "FAIL", wanted, None, missing)
    cases += 1
    if image != board[:8] + struct.pack("<Q", values["QEMU_TEXT_OFFSET"]) + \
            board[16:] or image[8:16] == board[8:16]:
        failures.append("the QEMU-only image is not the board image with "
                        "only bytes 8 to 15 set")
    for name, data in (("an image at QEMU's text_offset", image),
                       ("a wrong image_size", board[:16] + struct.pack(
                           "<Q", len(board) + 1) + board[24:]),
                       ("an image without the magic", board[:48] + bytes(8)
                        + board[56:])):
        refused(f"deriving {name}", lambda data=data: qemu_image(data, values))
    for name in ("a/b.img", "x.img;reset", "UPPER.img", "x.bin"):
        refused(f"be_image {name!r}", lambda name=name: session_lines(name))
    for failure in failures:
        print(f"BE_MVP_UBOOT_REHEARSAL_SELF_TEST: FAIL {failure}")
    print(f"BE_MVP_UBOOT_REHEARSAL_SELF_TEST: "
          f"{'FAIL' if failures else 'PASS'} cases={cases}")
    return 1 if failures else 0


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("session")
    for option in ("--label", "--firmware", "--uboot", "--uboot-elf",
                   "--disk", "--image", "--file", "--machine", "--cpu",
                   "--output"):
        run.add_argument(option, required=True)
    kind = run.add_mutually_exclusive_group(required=True)
    kind.add_argument("--expect")
    kind.add_argument("--fallthrough", action="store_true")
    run.add_argument("--qemu", default="qemu-system-riscv64")
    run.add_argument("--boot-timeout", type=float, default=60)
    run.add_argument("--run-timeout", type=float, default=300)
    run.add_argument("--exit-timeout", type=float, default=15)
    derive = commands.add_parser("derive")
    derive.add_argument("board")
    derive.add_argument("out")
    relation = commands.add_parser("relation")
    relation.add_argument("board")
    relation.add_argument("qemu_image")
    commands.add_parser("self-test")
    args = parser.parse_args(argv[1:])
    # A SIGTERM still runs the session's cleanup, which kills QEMU.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        if args.command == "self-test":
            return self_test()
        if args.command == "session":
            for path in (args.firmware, args.uboot, args.uboot_elf, args.disk,
                         args.image):
                if not os.access(path, os.R_OK):
                    parser.error(f"{path} is not readable")
            return session(args)
        values = layout()
        data = qemu_image(pathlib.Path(args.board).read_bytes(), values)
        if args.command == "derive":
            pathlib.Path(args.out).write_bytes(data)
        elif pathlib.Path(args.qemu_image).read_bytes() != data:
            raise Refused(f"{args.qemu_image} is not {args.board} with only "
                          f"its text_offset set to "
                          f"0x{values['QEMU_TEXT_OFFSET']:x}")
        print(f"qemu_image_bytes={len(data)}\n"
              f"qemu_image_sha256={hashlib.sha256(data).hexdigest()}\n"
              f"qemu_image_crc32={zlib.crc32(data):08x}\n"
              f"qemu_text_offset=0x{values['QEMU_TEXT_OFFSET']:x}")
        return 0
    except (Refused, qemu_oracle.OracleError, OSError, KeyError,
            ValueError) as error:
        print(f"BE_MVP_UBOOT_REHEARSAL: FAIL {args.command}: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
