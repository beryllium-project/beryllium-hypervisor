#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# A copy of B5's tests/check-b5-markers.py (accepted at 82956239) with the
# counted changes listed in bringup/k3-b6/README.md.
"""Validate B6 console markers from a QEMU or K3 serial capture.

B6 enters through B3's shim (one `BE_K3_B3: SHIM` line), runs the accepted
R3 boot through BE_R3:06, installs the B6 G-stage and guest controls
(BE_B6:01-07), runs an unmodified uniprocessor Linux whose console lines
the monitor tags with `BE_B6_GUEST: `, and ends with the guest's SRST
shutdown (BE_B6:08-09). The expected lines are the Markers section of the
accepted plan planning/k3-b6-plan.md (e34ef378); the R3 lines are the
marker literals of accepted R5 arch/riscv/be/r5-runtime.c (165f4d00), of
which B6 drops BE_R3:07. Every address and size comes from
bringup/k3-b6/src/b6-layout.h.

  check-b6-markers.py --capture FILE [--expect-fail CLASS] [--after LINE]
                      [--cause N] [--fault-above-window] [--sbi-time]
                      [--pins FILE | --kernel-bytes N --image-size S
                       --banner TEXT] [--toolchain gcc|clang] [--json F]
  check-b6-markers.py --self-test
  check-b6-markers.py --check-sources REPO_ROOT [--require-runtime]

Marker lines run from a tag (BE_K3_B3:, BE_R3:, BE_R4:, BE_R5:, BE_B6:, or
`BE_B6_GUEST: `) to the end of the line; trailing CRs are dropped. Only
loader output may precede the first marker line, which must be B3's SHIM
line: hart 0, shim at the staging address L, dest the monitor image, and
bytes its size. From there to the end of the capture every non-blank line
must be a marker line that starts with its tag and is printable ASCII
(0x20-0x7e); a guest line must not hold any tag after its prefix; and no
untagged line may hold an init (`B6INIT NN `) line.

Without --expect-fail, the capture must pass: the SHIM line, BE_R3:01-06,
BE_B6:01-07, then only guest lines until BE_B6:08, then BE_B6:09 and
nothing after it. The guest lines must hold the plan's required kernel,
init, and power-down lines in order, each init line exactly once and no
other init line, and no rejected pattern (`panic` only inside the pinned
`Kernel command line` line). <K>, <S>, and <banner> come from the guest
pins (default bringup/k3-b6/guest/pins.txt, or the options); <T> is hex,
<N> decimal, <e> 1000-1999, <m> at most the window in KiB. BE_B6:08 needs
exits = base + time + dbcn_write + dbcn_read + dbcn_byte + srst +
refused, at most the exit ceiling, with srst=1, refused=0, dbcn_byte=0,
and time=0; --sbi-time instead needs time above 0, and, as the sbi-time
guest's DTB has no sstc, refuses the Sstc riscv-timer line it otherwise
requires.

--expect-fail CLASS requires exactly one `BE_B6:FAIL CLASS`, CLASS one of
the plan's classes, after the SHIM line. The BE_R3/BE_B6 lines before it
must be a prefix of the pass sequence; guest lines may appear only between
BE_B6:07 and BE_B6:08 and are not otherwise fixed (a failing guest may
panic). The guest-exit classes (interrupt, guest-page-fault,
virtual-instruction, access-fault, illegal-instruction) need the plan's
`BE_B6:DETAIL` line next, with a cause that fits the class; the other
guest-run classes may have it; boot, gstage, sstc, controls, payload, and
shutdown-returned must not. A controls failure after arming may instead
carry the two `BE_B6:DETAIL controls` readback lines. At most
`BE_B6:SRST_RETURNED` may follow.

hedeleg is WARL (responsible-human direction fix-warl, 2026-10-08): the
BE_B6:04 hedeleg readback may lack causes 0, 4, and 6 of the written
0xb15d, but must hold causes 2, 3, 8, 12, 13, and 15 and no other bit.
--after LINE names the last BE_R3/BE_B6 line before the failure (`none`
for none); --cause N requires the DETAIL cause; --fault-above-window
requires the faulting GPA (htval << 2) at or above the end of the guest
window.

--check-sources reads accepted r5-runtime.c, the accepted plan, and
accepted B5 tests/run-qemu.sh (for the R5 CPU) with `git -C REPO_ROOT show
COMMIT:PATH`, each SHA-256 pinned, and requires the R3 literals, the
Markers block, the classes, the terminal regex, the rejected patterns, the
DETAIL format, the SHIM values, the negative variants, and the scenario
flags to match this checker and the B6 run tools. When
bringup/k3-b6/src/b6-runtime.c is present it must hold every BE_R3 line,
the fixed text and field names of every BE_B6 line, and the failure
literals, and bringup/k3-b6/src/ must name the guest tag and every class
and no numbered marker outside the plan; when it is absent the check says
so and skips it (--require-runtime makes that a finding). When
bringup/k3-b6/guest/init.c is present, its literals must name B6INIT and
hold no tag.

The JSON keeps B5's record (result, boot_marker, terminal, findings,
fields, markers) for bringup/k3-b0/tests/summarize-runs.py; fields holds
the SHIM values (hart, base, fdt, dest, bytes), each BE_B6 marker's
arguments, exits, elapsed_ms, and any failure, detail, and srst_returned.
"""

import argparse
import ast
import collections
import hashlib
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
B6_DIR = HERE.parent
LAYOUT_HEADER = B6_DIR / "src" / "b6-layout.h"
DEFAULT_PINS = B6_DIR / "guest" / "pins.txt"
LAYOUT_DEFINE = re.compile(r"^#define[ \t]+BE_B6_([A-Z0-9_]+)[ \t]+"
                           r"BE_B6_C\(([0-9a-fA-Fx]+)\)[ \t]*$", re.M)
LAYOUT_NAMES = ("MONITOR_HPA", "MONITOR_BYTES", "POOL_HPA", "HGATP",
                "STAGING_HPA", "GUEST_GPA", "GUEST_HPA", "GUEST_BYTES",
                "GUEST_LEAVES", "KERNEL_GPA", "KERNEL_TEXT_OFFSET",
                "KERNEL_FILE_MAX", "KERNEL_IMAGE_SIZE_MAX", "DTB_GPA",
                "DTB_BYTES", "GUEST_HART", "EXIT_CEILING", "SBI_IMPL_ID",
                "SBI_IMPL_VERSION")


def parse_layout(text, source, names=LAYOUT_NAMES):
    """{NAME: value} for every `#define BE_B6_NAME BE_B6_C(literal)`."""
    layout = {}
    for name, literal in LAYOUT_DEFINE.findall(text):
        if name in layout:
            raise ValueError(f"{source}: BE_B6_{name} is defined twice")
        layout[name] = int(literal, 0)
    missing = [name for name in names if name not in layout]
    if missing:
        raise ValueError(f"{source}: no BE_B6_C value for "
                         f"{', '.join('BE_B6_' + name for name in missing)}")
    return layout


def read_layout(path=LAYOUT_HEADER):
    return parse_layout(pathlib.Path(path).read_text(encoding="utf-8"), path)


LAYOUT = read_layout()
# The accepted R3 boot contract admits only hart 0.
BOOT_HART = 0
SHIM_TAG = "BE_K3_B3:"
GUEST_PREFIX = "BE_B6_GUEST: "
TAGS = (SHIM_TAG, "BE_R3:", "BE_R4:", "BE_R5:", "BE_B6:", GUEST_PREFIX)
# Tags guest output must never hold after its prefix.
GUEST_FORBIDDEN = TAGS
SHIM = re.compile(r"BE_K3_B3: SHIM hart=0x([0-9a-f]{16}) shim=0x([0-9a-f]{16})"
                  r" fdt=0x([0-9a-f]{16}) dest=0x([0-9a-f]{16}) "
                  r"bytes=0x([0-9a-f]{16})")
# The SHIM values the plan fixes (Markers): L, the monitor image, its size.
SHIM_FIXED = (f"shim=0x{LAYOUT['STAGING_HPA']:016x}",
              f"dest=0x{LAYOUT['MONITOR_HPA']:016x}",
              f"bytes=0x{LAYOUT['MONITOR_BYTES']:016x}")
R3_SEQUENCE = (
    "BE_R3:01 BOOT_VALIDATED",
    "BE_R3:02 R1_DERIVED",
    "BE_R3:03 R2_BUILT_REWALKED",
    "BE_R3:04 HS_VS_STATE_VERIFIED",
    "BE_R3:05 BINDING_PREPARED",
    "BE_R3:06 HGATP_FENCED_PUBLISHED",
)
# The accepted R3 line B6 drops: no management entry happens.
R3_DROPPED = "BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000"
# The guest controls the monitor arms and reads back (plan, Guest state and
# controls): henvcfg.STCE; hstatus SPV and SPVP; KVM's hedeleg plus
# misaligned load and store (Q5); VSTI; TM; FS and VS Off; vstimecmp ~0.
HENVCFG = 1 << 63
HSTATUS_CONTROLS = 0x180
HEDELEG = 0xb15d
# The readback may lack causes 0, 4, and 6 (bit 0 is read-only zero when
# IALIGN=16; K3 performs misaligned accesses in hardware); these causes
# must stick.
HEDELEG_REQUIRED = 0xb10c
HIDELEG = 0x40
HCOUNTEREN = 0x2
VSTIMECMP_ARMED = (1 << 64) - 1
B6_ENTRY = (
    f"BE_B6:01 GSTAGE_BUILT_REWALKED gpa=0x{LAYOUT['GUEST_GPA']:x} "
    f"hpa=0x{LAYOUT['GUEST_HPA']:x} size=0x{LAYOUT['GUEST_BYTES']:x} "
    f"leaves={LAYOUT['GUEST_LEAVES']} pool=0x{LAYOUT['POOL_HPA']:x}",
    f"BE_B6:02 HGATP_INSTALLED hgatp=0x{LAYOUT['HGATP']:x}",
    f"BE_B6:03 SSTC_STCE_READBACK henvcfg=0x{HENVCFG:x}",
    f"BE_B6:04 GUEST_CONTROLS_CHECKED hstatus_controls=0x"
    f"{HSTATUS_CONTROLS:x} hedeleg=0x{HEDELEG:x} hideleg=0x{HIDELEG:x} "
    f"hcounteren=0x{HCOUNTEREN:x} fs=0x0 vs=0x0 "
    f"vstimecmp=0x{VSTIMECMP_ARMED:x}",
    f"BE_B6:05 GUEST_RAM_CLEARED gpa=0x{LAYOUT['GUEST_GPA']:x} "
    f"size=0x{LAYOUT['GUEST_BYTES']:x} ticks=<T>",
    f"BE_B6:06 PAYLOAD_PLACED kernel=0x{LAYOUT['KERNEL_GPA']:x} "
    f"kernel_bytes=<K> image_size=<S> dtb=0x{LAYOUT['DTB_GPA']:x} "
    f"dtb_bytes=0x{LAYOUT['DTB_BYTES']:x} ticks=<T>",
    f"BE_B6:07 ENTER_GUEST pc=0x{LAYOUT['KERNEL_GPA']:x} "
    f"a0=0x{LAYOUT['GUEST_HART']:x} a1=0x{LAYOUT['DTB_GPA']:x}",
)
RELEASE = "7.2.0"
COMMAND_LINE = "earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1"
TIMESTAMP = "[<s>] "
# The required kernel lines (printk), the init's lines, and the power-down.
KERNEL_LINES = (
    f"Linux version {RELEASE} <banner>",
    f"SBI implementation ID=0x{LAYOUT['SBI_IMPL_ID']:x} "
    f"Version=0x{LAYOUT['SBI_IMPL_VERSION']:x}",
    f"Kernel command line: {COMMAND_LINE}",
    "riscv-timer: Timer interrupt in S-mode is available via sstc extension",
    f"Memory: <m>K/{LAYOUT['GUEST_BYTES'] // 1024}K available <rest>",
    "Run /init as init process",
)
INIT_LINES = (
    "B6INIT 01 START pid=1",
    f"B6INIT 02 UNAME release={RELEASE} machine=riscv64",
    "B6INIT 03 SLEEP requested_ms=1000 elapsed_ms=<e> ok=1",
    "B6INIT 04 RESULT pass",
    "B6INIT 05 POWER_OFF",
)
POWER_DOWN = "reboot: Power down"
GUEST_TEMPLATE = tuple(GUEST_PREFIX + TIMESTAMP + line
                       for line in KERNEL_LINES) + \
    tuple(GUEST_PREFIX + line for line in INIT_LINES) + \
    (GUEST_PREFIX + TIMESTAMP + POWER_DOWN,)
COMMAND_LINE_AT = KERNEL_LINES.index(f"Kernel command line: {COMMAND_LINE}")
MEMORY_AT = [line.startswith("Memory: ") for line in KERNEL_LINES].index(True)
# The sbi-time guest's DTB has no sstc, so Linux takes its timer through SBI
# TIME and must not report the Sstc timer.
SSTC_AT = [line.startswith("riscv-timer: ")
           for line in KERNEL_LINES].index(True)
COUNTERS = ("exits", "base", "time", "dbcn_write", "dbcn_read", "dbcn_byte",
            "srst", "refused")
EXITS_TEXT = "BE_B6:08 GUEST_SHUTDOWN type=0 reason=0 exits="
GUEST_SHUTDOWN = (f"{EXITS_TEXT}<N> base=<N> time=0 dbcn_write=<N> "
                  f"dbcn_read=<N> dbcn_byte=0 srst=1 refused=0 ticks=<T>")
SHUTDOWN = "BE_B6:09 SHUTDOWN type=0 reason=0"
PASS_TEMPLATE = R3_SEQUENCE + B6_ENTRY + GUEST_TEMPLATE + \
    (GUEST_SHUTDOWN, SHUTDOWN)
# BE_R3/BE_B6 lines in pass order; guest lines run after MONITOR[GUEST_AT - 1].
MONITOR = R3_SEQUENCE + B6_ENTRY + (GUEST_SHUTDOWN, SHUTDOWN)
GUEST_AT = len(R3_SEQUENCE) + len(B6_ENTRY)
LINE_IDS = ("none",) + tuple(line.split(" ", 1)[0] for line in MONITOR)
HEX = r"0x(?:0|[1-9a-f][0-9a-f]{0,15})"
HEDELEG_FIELD = re.compile(rf"(?<= hedeleg=)({HEX})(?= )")
DEC = r"(?:0|[1-9][0-9]*)"
# Placeholder -> pattern; <K>, <S>, and <banner> come from the pins.
PLACEHOLDERS = {
    "<T>": HEX,
    "<N>": DEC,
    "[<s>]": r"\[ *[0-9]+\.[0-9]{6}\]",
    "<m>": r"[1-9][0-9]*",
    "<rest>": r"\S.*",
    "<e>": r"1[0-9]{3}",
}
PLACEHOLDER = re.compile(r"\[<s>\]|<[A-Za-z]+>")
GUEST_SHUTDOWN_RE = re.compile(
    re.escape(EXITS_TEXT) + " ".join(
        [f"({DEC})"] + [f"{name}=({DEC})" for name in COUNTERS[1:]] +
        [f"ticks=({HEX})"]))
FAIL_PREFIX = "BE_B6:FAIL "
DETAIL_PREFIX = "BE_B6:DETAIL "
# After a controls failure, every guest-control readback in two lines.
CONTROLS_DETAIL_PREFIX = "BE_B6:DETAIL controls "
CONTROLS_DETAIL_FIELDS = (
    ("hip", "hstatus", "hedeleg", "hideleg", "hie", "hvip", "hcounteren",
     "htimedelta"),
    ("henvcfg", "hgeie", "vstimecmp", "sie", "sstatus", "hgatp", "vsatp",
     "sscratch"))
SRST_RETURNED = "BE_B6:SRST_RETURNED"
DETAIL_FIELDS = ("cause", "pc", "tval", "htval", "htinst", "spvp", "vsatp",
                 "exits")
DETAIL_TEMPLATE = ("BE_B6:DETAIL cause=0x\u2026 pc=0x\u2026 tval=0x\u2026 "
                   "htval=0x\u2026 htinst=0x\u2026 spvp=<0|1> "
                   "vsatp=0x\u2026 exits=<N>")
DETAIL = re.compile(rf"BE_B6:DETAIL cause=({HEX}) pc=({HEX}) tval=({HEX}) "
                    rf"htval=({HEX}) htinst=({HEX}) spvp=([01]) "
                    rf"vsatp=({HEX}) exits=({DEC})")
CONTROLS_DETAIL = tuple(
    re.compile(CONTROLS_DETAIL_PREFIX + " ".join(f"{name}=({HEX})"
                                                  for name in names))
    for names in CONTROLS_DETAIL_FIELDS)
CLASSES = ("boot", "gstage", "sstc", "controls", "payload", "interrupt",
           "guest-page-fault", "virtual-instruction", "access-fault",
           "illegal-instruction", "exception", "exit-budget", "guest-timeout",
           "resume", "console", "guest-failure", "guest-reboot",
           "shutdown-returned")
# A terminal guest exit names its cause; the other guest-run classes may.
DETAIL_REQUIRED = ("interrupt", "guest-page-fault", "virtual-instruction",
                   "access-fault", "illegal-instruction")
DETAIL_OPTIONAL = ("exception", "exit-budget", "guest-timeout", "resume",
                   "console", "guest-failure", "guest-reboot")
INTERRUPT = 1 << 63
TERMINAL_REGEX = "BE_B6:09 SHUTDOWN|BE_B6:FAIL|BE_K3_B3: FAIL"
# The plan's rejected patterns, case-sensitive, in any guest line.
REJECTED = ("panic", "Oops", "WARN", "BUG:", "kernel BUG",
            "Attempted to kill init", "cut here", "Call Trace:",
            "Unable to handle kernel", "rcu: INFO:", "soft lockup",
            "blocked for more than", "segfault", "unhandled signal",
            "extension is not available in SBI", "sbi_srst_reset",
            "No working init found", "Failed to execute", "Out of memory",
            "RESULT fail")
UNPREFIXED_INIT = re.compile(r"B6INIT [0-9]{2} ")
# Argument-bearing marker -> JSON field holding its arguments.
FIELD_PREFIXES = (
    ("BE_B6:01 ", "gstage"),
    ("BE_B6:02 ", "hgatp"),
    ("BE_B6:03 ", "sstc_readback"),
    ("BE_B6:04 ", "guest_controls"),
    ("BE_B6:05 ", "guest_ram"),
    ("BE_B6:06 ", "payload"),
    ("BE_B6:07 ", "guest_entry"),
    ("BE_B6:08 ", "guest_shutdown"),
    ("BE_B6:09 ", "shutdown"),
)
Pins = collections.namedtuple("Pins", "kernel_bytes image_size banner")


def read_pins(path):
    return parse_pins(pathlib.Path(path).read_text(encoding="utf-8"), path)


def parse_pins(text, path):
    """Pins from guest/pins.txt: the `file` line named Image, and the
    `kernel image_size=`, `kernel text_offset=`, and `kernel banner=`
    lines. Other lines are not this checker's."""
    kernel_bytes = image_size = text_offset = banner = None
    for number, raw in enumerate(text.split("\n"), 1):
        line = raw.rstrip("\r")
        where = f"{path}:{number}"
        if line.startswith("file "):
            match = re.fullmatch(r"file (\S+) sha256=[0-9a-f]{64} "
                                 r"bytes=([0-9]+)", line)
            if not match:
                raise ValueError(f"{where}: malformed file pin {line!r}")
            if pathlib.PurePosixPath(match.group(1)).name == "Image":
                if kernel_bytes is not None:
                    raise ValueError(f"{where}: a second Image pin")
                kernel_bytes = int(match.group(2))
        elif line.startswith(("kernel image_size=", "kernel text_offset=")):
            match = re.fullmatch(r"kernel (image_size|text_offset)="
                                 r"0x([0-9a-f]+)", line)
            if not match:
                raise ValueError(f"{where}: malformed kernel pin {line!r}")
            if match.group(1) == "image_size":
                image_size = int(match.group(2), 16)
            else:
                text_offset = int(match.group(2), 16)
        elif line.startswith("kernel banner="):
            banner = line[len("kernel banner="):]
    missing = [name for name, value in (
        ("file Image", kernel_bytes), ("kernel image_size", image_size),
        ("kernel text_offset", text_offset), ("kernel banner", banner))
        if value is None]
    if missing:
        raise ValueError(f"{path} has no {', '.join(missing)} pin")
    if text_offset != LAYOUT["KERNEL_TEXT_OFFSET"]:
        raise ValueError(f"{path}: text_offset 0x{text_offset:x} != "
                         f"0x{LAYOUT['KERNEL_TEXT_OFFSET']:x}")
    return checked_pins(Pins(kernel_bytes, image_size, banner), path)


def checked_pins(pins, source):
    """The pins, after the plan's budgets and the banner's release."""
    if not 0 < pins.kernel_bytes <= LAYOUT["KERNEL_FILE_MAX"]:
        raise ValueError(f"{source}: Image is {pins.kernel_bytes} bytes, "
                         f"outside 1-{LAYOUT['KERNEL_FILE_MAX']}")
    if not pins.kernel_bytes <= pins.image_size <= \
            LAYOUT["KERNEL_IMAGE_SIZE_MAX"]:
        raise ValueError(f"{source}: image_size 0x{pins.image_size:x} is "
                         f"below the file or above 0x"
                         f"{LAYOUT['KERNEL_IMAGE_SIZE_MAX']:x}")
    if not pins.banner.startswith(f"Linux version {RELEASE} ") or \
            any(not " " <= char <= "~" for char in pins.banner):
        raise ValueError(f"{source}: banner {pins.banner!r} is not a "
                         f"printable `Linux version {RELEASE} ` line")
    return pins


def template_pattern(line, pins):
    """A compiled full-line pattern for one plan template line."""
    parts = []
    position = 0
    for match in PLACEHOLDER.finditer(line):
        parts.append(re.escape(line[position:match.start()]))
        token = match.group(0)
        if token == "<K>":
            parts.append(re.escape(f"0x{pins.kernel_bytes:x}") if pins
                         else HEX)
        elif token == "<S>":
            parts.append(re.escape(f"0x{pins.image_size:x}") if pins
                         else HEX)
        elif token == "<banner>":
            prefix = f"Linux version {RELEASE} "
            parts.append(re.escape(pins.banner[len(prefix):]) if pins
                         else r"\S.*")
        else:
            parts.append(PLACEHOLDERS[token])
        position = match.end()
    parts.append(re.escape(line[position:]))
    return re.compile("".join(parts))


def uses_pins(line):
    return any(token in line for token in ("<K>", "<S>", "<banner>"))


def scan(text):
    """(markers, problems): every marker line, and line-structure findings."""
    markers = []
    problems = []
    started = False
    for number, raw in enumerate(text.split("\n"), 1):
        line = raw.rstrip("\r")
        positions = [line.find(tag) for tag in TAGS]
        positions = [position for position in positions if position >= 0]
        if not positions:
            if UNPREFIXED_INIT.search(line):
                problems.append(f"line {number}: init line without the "
                                f"{GUEST_PREFIX!r} prefix: {line[:80]!r}")
            elif started and line.strip():
                problems.append(f"line {number}: untagged text among or "
                                f"after the markers: {line[:80]!r}")
            continue
        start = min(positions)
        marker = line[start:]
        if started and start:
            problems.append(f"line {number}: text before the marker: "
                            f"{line[:80]!r}")
        started = True
        markers.append(marker)
        odd = [char for char in marker if not " " <= char <= "~"]
        if odd:
            problems.append(f"line {number}: non-printable {odd[0]!r} in "
                            f"{marker[:80]!r}")
        if marker.startswith(GUEST_PREFIX):
            body = marker[len(GUEST_PREFIX):]
            forged = [tag for tag in GUEST_FORBIDDEN if tag in body]
            if forged:
                problems.append(f"line {number}: guest output holds "
                                f"{forged[0]!r}: {marker[:80]!r}")
    return markers, problems


def extract(text):
    """Every marker line, from its tag to the end of the line."""
    return scan(text)[0]


def is_failure(line):
    return line.startswith((FAIL_PREFIX, DETAIL_PREFIX)) or \
        line == SRST_RETURNED


def shim_findings(markers):
    """(findings, the markers after the SHIM line, SHIM values or None)."""
    if not markers or not markers[0].startswith(SHIM_TAG):
        return ["no B3 SHIM line before the first marker"], markers, None
    line = markers[0]
    match = SHIM.fullmatch(line)
    if not match:
        return [f"malformed SHIM line {line!r}"], markers[1:], None
    values = dict(zip(("hart", "base", "fdt", "dest", "bytes"),
                      (int(value, 16) for value in match.groups())))
    findings = []
    if values["hart"] != BOOT_HART:
        findings.append(f"the shim ran on hart {values['hart']}, not "
                        f"{BOOT_HART}")
    for fixed in SHIM_FIXED:
        if f" {fixed}" not in line:
            findings.append(f"SHIM line lacks {fixed}: {line!r}")
    return findings, markers[1:], values


def counter_findings(line, sbi_time=False):
    """(counters, findings) for a BE_B6:08 line."""
    match = GUEST_SHUTDOWN_RE.fullmatch(line)
    if not match:
        return None, [f"malformed BE_B6:08 line {line!r}"]
    counters = dict(zip(COUNTERS, (int(value) for value in
                                   match.groups()[:len(COUNTERS)])))
    findings = []
    total = sum(counters[name] for name in COUNTERS[1:])
    if counters["exits"] != total:
        findings.append(f"exits={counters['exits']} is not the sum {total} "
                        f"of the other counters")
    if not 1 <= counters["exits"] <= LAYOUT["EXIT_CEILING"]:
        findings.append(f"exits={counters['exits']} is outside 1-"
                        f"{LAYOUT['EXIT_CEILING']}")
    for name, wanted in (("srst", 1), ("refused", 0), ("dbcn_byte", 0)):
        if counters[name] != wanted:
            findings.append(f"{name}={counters[name]}, expected {wanted}")
    if sbi_time and counters["time"] == 0:
        findings.append("time=0, but the sbi-time guest must use SBI TIME")
    if not sbi_time and counters["time"] != 0:
        findings.append(f"time={counters['time']}, but the guest must use "
                        f"its own Sstc timer")
    return counters, findings


def hedeleg_ok(value):
    """Whether a hedeleg readback is a WARL reading of HEDELEG."""
    return value & ~HEDELEG == 0 and \
        value & HEDELEG_REQUIRED == HEDELEG_REQUIRED


def warl_normalized(line):
    """BE_B6:04 with a WARL hedeleg readback shown as the written value."""
    match = HEDELEG_FIELD.search(line) if line.startswith("BE_B6:04 ") \
        else None
    if match and hedeleg_ok(int(match.group(1), 16)):
        return f"{line[:match.start()]}0x{HEDELEG:x}{line[match.end():]}"
    return line


def monitor_findings(line, slot, pins, sbi_time):
    """Findings when LINE is not MONITOR[slot] (placeholders filled)."""
    wanted = MONITOR[slot]
    if wanted == GUEST_SHUTDOWN:
        if not line.startswith(EXITS_TEXT):
            return [f"{line!r} is not {GUEST_SHUTDOWN!r}"]
        return counter_findings(line, sbi_time)[1]
    if not template_pattern(wanted, pins).fullmatch(warl_normalized(line)):
        return [f"{line!r} is not {wanted!r}"]
    if pins is None and uses_pins(wanted):
        return [f"{line!r} needs the kernel pins (guest/pins.txt, or "
                f"--kernel-bytes, --image-size, and --banner)"]
    return []


def pass_prefix(lines, pins=None, sbi_time=False, first=2):
    """(last BE_R3/BE_B6 line ID, findings, guest lines) for the lines after
    the SHIM line: they must follow the pass order, and guest lines may
    appear only between BE_B6:07 and BE_B6:08. Findings number the marker
    lines from FIRST (the SHIM line is marker 1)."""
    findings = []
    guest = []
    slot = 0
    for index, line in enumerate(lines, first):
        if line.startswith(GUEST_PREFIX):
            if slot != GUEST_AT:
                findings.append(f"marker {index}: guest line {line!r} is "
                                f"outside the guest run")
                break
            guest.append(line)
            continue
        if slot == len(MONITOR):
            findings.append(f"marker {index}: {line!r} follows "
                            f"{SHUTDOWN!r}")
            break
        problems = monitor_findings(line, slot, pins, sbi_time)
        if problems:
            findings += [f"marker {index}: {problem}"
                         for problem in problems]
            if not line.startswith(MONITOR[slot].split(" ", 1)[0] + " "):
                break
        slot += 1
    return LINE_IDS[slot], findings, guest


def guest_findings(guest, pins, sbi_time=False):
    """The required guest lines in order, each init line once, no other
    init line, and no rejected pattern. With sbi_time the Sstc timer line
    is not required but refused."""
    findings = []
    patterns = [template_pattern(line, pins) for line in GUEST_TEMPLATE]
    command_line = patterns[COMMAND_LINE_AT]
    init_patterns = patterns[len(KERNEL_LINES):len(KERNEL_LINES) +
                             len(INIT_LINES)]
    required = list(GUEST_TEMPLATE)
    if sbi_time:
        sstc = patterns.pop(SSTC_AT)
        del required[SSTC_AT]
        findings += [f"the sbi-time guest reported the Sstc timer: {line!r}"
                     for line in guest if sstc.fullmatch(line)]
    position = 0
    for line in guest:
        body = line[len(GUEST_PREFIX):]
        exempt = ("panic",) if command_line.fullmatch(line) else ()
        for pattern in REJECTED:
            if pattern in body and pattern not in exempt:
                findings.append(f"rejected {pattern!r} in guest line "
                                f"{line!r}")
        if body.startswith("B6INIT ") and \
                not any(init.fullmatch(line) for init in init_patterns):
            findings.append(f"unexpected init line {line!r}")
        if position < len(patterns) and patterns[position].fullmatch(line):
            position += 1
    if position < len(patterns):
        findings.append(f"missing required guest line "
                        f"{required[position]!r} (or a later one is "
                        f"out of order)")
    for template, init in zip(INIT_LINES, init_patterns):
        count = sum(1 for line in guest if init.fullmatch(line))
        if count > 1:
            findings.append(f"init line {template!r} appears {count} times")
    window_k = LAYOUT["GUEST_BYTES"] // 1024
    memory = template_pattern(GUEST_TEMPLATE[MEMORY_AT], pins)
    for line in guest:
        if memory.fullmatch(line):
            available = int(re.search(r"Memory: ([0-9]+)K/", line).group(1))
            if available > window_k:
                findings.append(f"{available}K available exceeds the "
                                f"{window_k}K window: {line!r}")
    if pins is None:
        findings.append("no kernel pins: give guest/pins.txt, --pins, or "
                        "--kernel-bytes, --image-size, and --banner")
    return findings


def pass_findings(markers, pins=None, sbi_time=False):
    """Findings for a capture that must pass (its marker lines)."""
    findings, rest, _ = shim_findings(markers)
    failures = [line for line in rest if is_failure(line)]
    if failures:
        findings.append(f"failure lines in a pass capture: {failures[:3]}")
    reached, prefix, guest = pass_prefix(rest, pins, sbi_time,
                                         len(markers) - len(rest) + 1)
    findings += prefix
    if reached != LINE_IDS[-1]:
        findings.append(f"the sequence stops after {reached}; missing "
                        f"{MONITOR[LINE_IDS.index(reached)]!r}")
    findings += guest_findings(guest, pins, sbi_time)
    return findings


def full_sequence_reached(markers, pins=None, sbi_time=False):
    """The pass sequence through BE_B6:09, and no failure line anywhere."""
    if any(is_failure(line) for line in markers):
        return False
    if SHUTDOWN in markers:
        markers = markers[:markers.index(SHUTDOWN) + 1]
    return not pass_findings(markers, pins, sbi_time)


def terminal(markers):
    if any(is_failure(line) or line.startswith("BE_K3_B3: FAIL")
           for line in markers):
        return "fail-marker"
    if markers and markers[-1] == SHUTDOWN:
        return "shutdown-requested"
    return "none"


def cause_finding(klass, cause):
    """A finding when an exit's cause does not fit its class."""
    fits = {
        "interrupt": bool(cause & INTERRUPT),
        "guest-page-fault": cause in (20, 21, 23),
        "virtual-instruction": cause == 22,
        "access-fault": cause in (1, 5, 7),
        "illegal-instruction": cause == 2,
        "exception": not cause & INTERRUPT and
        cause not in (1, 2, 5, 7, 10, 20, 21, 22, 23),
    }.get(klass, True)
    if not fits:
        return f"cause 0x{cause:x} does not fit class {klass}"
    return None


def failure_findings(markers, klass, pins=None, after=None, cause=None,
                     above_window=False):
    if klass not in CLASSES:
        return [f"unknown failure class {klass!r}"]
    findings, rest, _ = shim_findings(markers)
    failures = [index for index, line in enumerate(rest)
                if line.startswith(FAIL_PREFIX)]
    if not failures:
        return findings + ["no BE_B6:FAIL line"]
    if len(failures) > 1:
        findings.append(f"{len(failures)} BE_B6:FAIL lines")
    first = failures[0]
    seen = rest[first][len(FAIL_PREFIX):]
    if seen != klass:
        findings.append(f"failure class {seen!r}, expected {klass!r}")
    reached, prefix, _ = pass_prefix(rest[:first], pins,
                                     first=len(markers) - len(rest) + 1)
    findings += prefix
    if after is not None and reached != after:
        findings.append(f"the failure follows {reached}, expected {after}")
    tail = rest[first + 1:]
    if klass == "controls" and tail and \
            tail[0].startswith(CONTROLS_DETAIL_PREFIX):
        for pattern in CONTROLS_DETAIL:
            if not tail or not pattern.fullmatch(tail[0]):
                findings.append(f"malformed controls readback {tail[:1]}")
                break
            tail = tail[1:]
    detail = None
    if tail and tail[0].startswith(DETAIL_PREFIX):
        match = DETAIL.fullmatch(tail[0])
        if match:
            detail = dict(zip(DETAIL_FIELDS,
                              (int(value, 0) for value in match.groups())))
        else:
            findings.append(f"malformed detail {tail[0]!r}")
        if klass not in DETAIL_REQUIRED + DETAIL_OPTIONAL:
            findings.append(f"class {klass} takes no BE_B6:DETAIL line")
        tail = tail[1:]
    elif klass in DETAIL_REQUIRED:
        findings.append(f"class {klass} needs a BE_B6:DETAIL line")
    if tail[:1] == [SRST_RETURNED]:
        tail = tail[1:]
    if tail:
        findings.append(f"lines after the failure: {tail[:3]}")
    if detail:
        finding = cause_finding(klass, detail["cause"])
        if finding:
            findings.append(finding)
    if cause is not None:
        if detail is None:
            findings.append(f"no detail cause to compare with 0x{cause:x}")
        elif detail["cause"] != cause:
            findings.append(f"cause 0x{detail['cause']:x}, expected "
                            f"0x{cause:x}")
    if above_window:
        end = LAYOUT["GUEST_GPA"] + LAYOUT["GUEST_BYTES"]
        if detail is None:
            findings.append("no detail htval to compare with the window end")
        elif detail["htval"] << 2 < end:
            findings.append(f"faulting GPA 0x{detail['htval'] << 2:x} "
                            f"(htval << 2) is below the window end "
                            f"0x{end:x}")
    return findings


def evaluate(text, expect_fail=None, pins=None, sbi_time=False, after=None,
             cause=None, above_window=False):
    """(ok, findings) for one capture's text."""
    markers, findings = scan(text)
    if expect_fail is None:
        if after is not None or cause is not None or above_window:
            findings.append("--after, --cause, and --fault-above-window "
                            "apply to --expect-fail only")
        findings += pass_findings(markers, pins, sbi_time)
    else:
        if sbi_time:
            findings.append("--sbi-time applies to a pass only")
        findings += failure_findings(markers, expect_fail, pins, after, cause,
                                     above_window)
    return not findings, findings


def parse_fields(markers):
    """The SHIM values, each BE_B6 marker's arguments, and failure facts."""
    fields = {}
    match = SHIM.fullmatch(markers[0]) if markers else None
    if match:
        fields.update(zip(("hart", "base", "fdt", "dest", "bytes"),
                          (f"0x{value}" for value in match.groups())))
    for line in markers:
        if line.startswith(GUEST_PREFIX):
            body = line[len(GUEST_PREFIX):]
            elapsed = re.fullmatch(r"B6INIT 03 SLEEP requested_ms=1000 "
                                   r"elapsed_ms=([0-9]+) ok=[01]", body)
            if elapsed and "elapsed_ms" not in fields:
                fields["elapsed_ms"] = elapsed.group(1)
            continue
        parts = line.split(" ", 2)
        for prefix, name in FIELD_PREFIXES:
            if line.startswith(prefix) and name not in fields and \
                    len(parts) == 3:
                fields[name] = parts[2]
        if line.startswith(FAIL_PREFIX) and "failure" not in fields:
            fields["failure"] = line[len(FAIL_PREFIX):]
        elif line.startswith(DETAIL_PREFIX) and "detail" not in fields:
            fields["detail"] = line[len(DETAIL_PREFIX):]
        elif line == SRST_RETURNED:
            fields["srst_returned"] = "yes"
        exits = GUEST_SHUTDOWN_RE.fullmatch(line)
        if exits and "exits" not in fields:
            fields["exits"] = exits.group(1)
    return fields


def result_record(capture, expect, markers, ok, findings, toolchain=None,
                  pins=None, sbi_time=False):
    return {
        "capture": capture,
        "expect": expect,
        "toolchain": toolchain or "-",
        "result": "PASS" if ok else "FAIL",
        "boot_marker": "PASS" if full_sequence_reached(
            markers, pins, sbi_time) else "FAIL",
        "terminal": terminal(markers),
        "findings": findings,
        "fields": parse_fields(markers),
        "markers": markers,
    }


def exits_report(markers):
    """The line that prints a capture's guest counters, or None."""
    for line in markers:
        counters, _ = counter_findings(line) if \
            line.startswith(EXITS_TEXT) else (None, None)
        if counters:
            return "BE_B6_EXITS: " + " ".join(
                f"{name}={counters[name]}" for name in COUNTERS)
    return None


# Source checks: the accepted inputs, the B6 run tools, and the B6 sources.
ACCEPTED_R5 = "165f4d001a2b59b582b397bdea79ec4826168fdb"
R5_RUNTIME = "arch/riscv/be/r5-runtime.c"
R5_RUNTIME_SHA256 = \
    "a221ce8ebb77e3feaa9d7799e3eb296fb8cd7aa9190e20f1970d7e9c95bcc6e4"
ACCEPTED_PLAN = "e34ef378b6279300ba5f3aeb8b6102941b432454"
PLAN = "planning/k3-b6-plan.md"
PLAN_SHA256 = \
    "ac53bbfa6e8538c8ac0067fa2ec91dda3bbfd6bd1b72a18fcbac811fc91ada7a"
ACCEPTED_B5 = "829562395bf14fedbeea0beb82b30da15ec5f7cf"
B5_RUNNER = "bringup/k3-b5/tests/run-qemu.sh"
B5_RUNNER_SHA256 = \
    "bffc7b304367a69576acda37a93450dbfe8b480f05a0c2d4731fcd000670f811"
B6_RUNTIME = "bringup/k3-b6/src/b6-runtime.c"
B6_INIT = "bringup/k3-b6/guest/init.c"
B6_SRC = "bringup/k3-b6/src"
RUN_TOOLS = (HERE / "run-qemu.sh", HERE / "run-qemu-uboot.py",
             HERE / "kexec-rehearsal.sh",
             B6_DIR / "scripts" / "k3-uboot-run.sh",
             B6_DIR / "scripts" / "k3-run.sh")
ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'",
           "?": "?", "a": "\a", "b": "\b", "f": "\f", "v": "\v"}


def fixed_text(line):
    """A marker's fixed text: up to and including its first `=`."""
    return line[:line.index("=") + 1] if "=" in line else line


def field_names(line):
    """` name=` for every field after a marker's first."""
    return tuple(f" {name}=" for name in
                 re.findall(r" ([a-z0-9_]+)=", line[len(fixed_text(line)):]))


def read_quoted(source, index):
    """(decoded text, index after the closing quote) of a C literal."""
    quote = source[index]
    out = []
    index += 1
    while index < len(source):
        char = source[index]
        if char == quote:
            return "".join(out), index + 1
        if char == "\n":
            break
        if char != "\\":
            out.append(char)
            index += 1
            continue
        escape = source[index + 1:index + 2]
        if escape in ESCAPES:
            out.append(ESCAPES[escape])
            index += 2
        elif escape == "x":
            digits = re.match(r"[0-9a-fA-F]+", source[index + 2:])
            if not digits:
                break
            out.append(chr(int(digits.group(0), 16) & 0xFF))
            index += 2 + len(digits.group(0))
        elif escape and escape in "01234567":
            digits = re.match(r"[0-7]{1,3}", source[index + 1:]).group(0)
            out.append(chr(int(digits, 8) & 0xFF))
            index += 1 + len(digits)
        else:
            out.append(escape)
            index += 2
    raise ValueError(f"unterminated literal at offset {index}")


def c_literals(source):
    """Every C string literal, adjacent literals joined as C joins them."""
    source = source.replace("\\\n", "")
    literals = []
    parts = None
    index = 0
    while index < len(source):
        char = source[index]
        if source.startswith("//", index):
            end = source.find("\n", index)
            index = len(source) if end < 0 else end
        elif source.startswith("/*", index):
            end = source.find("*/", index + 2)
            index = len(source) if end < 0 else end + 2
        elif char in "\"'":
            text, index = read_quoted(source, index)
            if char == '"':
                parts = (parts or []) + [text]
            elif parts is not None:
                literals.append("".join(parts))
                parts = None
        else:
            if parts is not None and not char.isspace():
                literals.append("".join(parts))
                parts = None
            index += 1
    if parts is not None:
        literals.append("".join(parts))
    return literals


def literal_findings(name, literals, required):
    return [f"{name} has no string literal holding {text!r}"
            for text in required
            if not any(text in literal for literal in literals)]


def b6_source_findings(runtime, init, sources, require_runtime=False):
    """(findings, notes) for the B6 monitor and init sources (None when
    missing). sources holds every bringup/k3-b6/src/*.[ch] text."""
    findings = []
    notes = []
    monitor = B6_ENTRY + (GUEST_SHUTDOWN, SHUTDOWN)
    if runtime is None and require_runtime:
        findings.append(f"{B6_RUNTIME} is missing (--require-runtime)")
    elif runtime is None:
        notes.append(f"{B6_RUNTIME} is missing, so the BE_B6 source check "
                     f"is skipped")
    else:
        required = R3_SEQUENCE + tuple(fixed_text(line) for line in monitor)
        for line in monitor:
            required += field_names(line)
        required += (FAIL_PREFIX, "BE_B6:DETAIL cause=", SRST_RETURNED)
        required += tuple(f" {name}=" for name in DETAIL_FIELDS[1:])
        findings += literal_findings("b6-runtime.c", c_literals(runtime),
                                     tuple(dict.fromkeys(required)))
        # The tagger and the exit classes may live in any monitor source.
        literals = [literal for text in sources
                    for literal in c_literals(text)]
        findings += literal_findings(B6_SRC, literals, (GUEST_PREFIX,))
        for klass in CLASSES:
            token = re.compile(rf"(?<![\w-]){re.escape(klass)}(?![\w-])")
            if not any(token.search(literal) for literal in literals):
                findings.append(f"no literal in {B6_SRC} names the class "
                                f"{klass!r}")
        known = {line.split(" ", 1)[0]: line for line in R3_SEQUENCE}
        known.update((line.split(" ", 1)[0], fixed_text(line))
                     for line in monitor)
        for literal in literals:
            for match in re.finditer(r"BE_(?:R[0-9]|B[0-9]):[0-9]{2}",
                                     literal):
                wanted = known.get(match.group(0))
                if wanted is None or \
                        not literal.startswith(wanted, match.start()):
                    findings.append(f"{B6_SRC} literal {literal!r} holds a "
                                    f"marker outside the plan")
    if init is None:
        notes.append(f"{B6_INIT} is missing, so the init source check is "
                     f"skipped")
    else:
        literals = c_literals(init)
        findings += literal_findings("init.c", literals, ("B6INIT",))
        for literal in literals:
            forged = [tag for tag in GUEST_FORBIDDEN if tag in literal]
            if forged:
                findings.append(f"init.c literal {literal!r} holds the tag "
                                f"{forged[0]!r}")
    return findings, notes


def plan_markers(plan):
    match = re.search(r"^## Markers\n.*?^```text\n(.*?)^```", plan,
                      re.M | re.S)
    return tuple(match.group(1).splitlines()) if match else ()


def plan_classes(plan):
    """(classes, terminal regex) from the plan's Markers section."""
    match = re.search(r"^- Classes: (.*?)The run tools'\s+terminal regex\s+"
                      r"is `([^`]*)`", plan, re.M | re.S)
    if not match:
        return (), None
    text = re.sub(r"\([^)]*\)", "", match.group(1))
    return tuple(re.findall(r"`([^`]+)`", text)), match.group(2)


def plan_rejected(plan):
    match = re.search(r"\*\*Rejected\*\* in any guest line, as "
                      r"case-sensitive\s+substrings:(.*?)Also rejected",
                      plan, re.S)
    if not match:
        return ()
    return tuple(re.findall(r"`([^`]+)`",
                            re.sub(r"\([^)]*\)", "", match.group(1))))


def plan_detail(plan):
    match = re.search(r"`(BE_B6:DETAIL [^`]*)`", plan)
    return match.group(1) if match else None


def plan_shim(plan):
    match = re.search(r"prints B3's `SHIM` line, which must show\s+"
                      r"`(shim=[^`]*)`,\s+`(dest=[^`]*)`, and\s+"
                      r"`(bytes=[^`]*)`", plan)
    return match.groups() if match else ()


def plan_variants(plan):
    """(variant, class, cause, after, above_window) rows of the plan's
    negative-variant table; cause and after None when not given."""
    start = plan.find("**Negative variants**")
    end = plan.find("## Markers", start)
    rows = re.findall(r"^\| `([a-z-]+)` \| [^|\n]+ \| `BE_B6:FAIL "
                      r"([a-z-]+)`([^|\n]*)\|$", plan[start:end], re.M)
    variants = []
    for name, klass, rest in rows:
        cause = re.search(r"cause (\d+)", rest)
        after = re.search(r"after `(BE_[A-Z0-9]+:[0-9]{2})`", rest)
        variants.append((name, klass, int(cause.group(1)) if cause else None,
                         after.group(1) if after else None,
                         "at or above the window end" in rest))
    return tuple(variants)


def plan_scenarios(plan):
    """{scenario: (machine, cpu)} for the plan rows that name both."""
    return {name: (machine, cpu) for name, machine, cpu in re.findall(
        r"^\| `([a-z0-9.-]+)` \| `([^`]+)`; `([^`]+)` \|", plan, re.M)}


def runner_variants(runner):
    """(variant, class, after, cause, check) from run-qemu.sh's variants."""
    match = re.search(r"^variants=\(\n(.*?)^\)", runner, re.M | re.S)
    rows = re.findall(r"^\t'([a-z-]+) ([a-z-]+) ([A-Z0-9_:]+|none) "
                      r"([0-9]+|-) ([a-z-]+|-)'$",
                      match.group(1), re.M) if match else []
    return tuple((name, klass, after, None if cause == "-" else int(cause),
                  None if check == "-" else check)
                 for name, klass, after, cause, check in rows)


def python_strings(text, names):
    """The string constants a Python source assigns to NAMES."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ()
    return tuple(node.value.value for node in tree.body
                 if isinstance(node, ast.Assign) and
                 isinstance(node.value, ast.Constant) and
                 isinstance(node.value.value, str) and
                 any(isinstance(target, ast.Name) and target.id in names
                     for target in node.targets))


def plan_outcomes(plan):
    """{scenario: (class, after)} for the plan's failing QEMU scenarios;
    `before BE_R3:01` is after `none`."""
    start = plan.find("**QEMU scenarios**")
    end = plan.find("**Copied tools**", start)
    outcomes = {}
    for name, klass, where, line in re.findall(
            r"^\| `([a-z0-9.-]+)` \|[^\n]*\| `BE_B6:FAIL ([a-z-]+)` "
            r"(after|before) `(BE_[A-Z0-9]+:[0-9]{2})` \|$",
            plan[start:end], re.M):
        if line not in LINE_IDS:
            continue
        index = LINE_IDS.index(line)
        outcomes[name] = (klass, line if where == "after" else
                          LINE_IDS[index - 1] if index else "?")
    return outcomes


def plan_tool_findings(r5_runtime, plan, b5_runner, tools):
    """Findings for the accepted inputs against this checker and the tools.

    tools maps a run-tool name to its text (None when missing)."""
    findings = []
    literals = re.findall(r'"(BE_R3:[^"\\]*)\\n"', r5_runtime)
    if tuple(literals) != R3_SEQUENCE + (R3_DROPPED,):
        findings.append(f"accepted r5-runtime.c BE_R3 literals differ: "
                        f"{literals}")
    if plan_markers(plan) != PASS_TEMPLATE:
        findings.append(f"the plan's Markers block differs: "
                        f"{plan_markers(plan)}")
    classes, regex = plan_classes(plan)
    if classes != CLASSES:
        findings.append(f"the plan's classes differ: {classes}")
    if regex != TERMINAL_REGEX:
        findings.append(f"the plan's terminal regex differs: {regex!r}")
    if plan_rejected(plan) != REJECTED:
        findings.append(f"the plan's rejected patterns differ: "
                        f"{plan_rejected(plan)}")
    if plan_detail(plan) != DETAIL_TEMPLATE:
        findings.append(f"the plan's DETAIL line differs: "
                        f"{plan_detail(plan)!r}")
    if plan_shim(plan) != SHIM_FIXED:
        findings.append(f"the plan's SHIM values differ: {plan_shim(plan)}")
    variants = plan_variants(plan)
    if len(variants) != 6:
        findings.append(f"the plan's variant table has {len(variants)} rows")
    runner = tools.get("run-qemu.sh") or ""
    ran = runner_variants(runner)
    if [row[:3] for row in variants] != \
            [(name, klass, cause) for name, klass, _, cause, _ in ran]:
        findings.append(f"run-qemu.sh variants {ran} differ from the "
                        f"plan's {variants}")
    else:
        for (name, _, _, after, above), (_, _, ran_after, _, check) in \
                zip(variants, ran):
            if after is not None and ran_after != after:
                findings.append(f"run-qemu.sh runs {name} after {ran_after}"
                                f", the plan after {after}")
            if above != (check == "above-window"):
                findings.append(f"run-qemu.sh's window check for {name} "
                                f"differs from the plan")
    scenarios = plan_scenarios(plan)
    if set(scenarios) != {"k3-like", "rva23", "plic"}:
        findings.append(f"the plan's scenario rows differ: {scenarios}")
    minimal = re.search(r"^minimal='([^']+)'$", b5_runner, re.M)
    if not minimal or "sstc=false" not in minimal.group(1):
        findings.append("accepted B5 run-qemu.sh lost its R5 CPU string")
    for name, text in tools.items():
        if text is None:
            findings.append(f"run tool {name} is missing")
        elif TERMINAL_REGEX not in text:
            findings.append(f"{name} lacks the terminal regex "
                            f"{TERMINAL_REGEX!r}")
    wanted = [(name, value) for name, pair in sorted(scenarios.items())
              for value in pair]
    wanted.append(("no-sstc", "virt,aia=none"))
    if minimal:
        wanted.append(("no-sstc", minimal.group(1)))
    for name, value in wanted:
        if f"'{value}'" not in runner and f" {value} " not in runner:
            findings.append(f"run-qemu.sh lacks the {name} value {value!r}")
    normalized = re.sub(r"\\\n\s*", " ", runner)
    outcomes = plan_outcomes(plan)
    if set(outcomes) != {"no-sstc", "sbi-3.0"}:
        findings.append(f"the plan's failing scenarios differ: {outcomes}")
    for name, (klass, after) in sorted(outcomes.items()):
        if not re.search(rf"^\s*run {re.escape(name)} .* {re.escape(klass)} "
                         rf"{re.escape(after)} ", normalized, re.M):
            findings.append(f"run-qemu.sh does not run {name} as "
                            f"{klass} after {after}")
    uboot = tools.get("run-qemu-uboot.py") or ""
    rehearsal = tools.get("kexec-rehearsal.sh") or ""
    for value in scenarios.get("k3-like", ()):
        if value not in python_strings(uboot, ("MACHINE", "CPU")):
            findings.append(f"run-qemu-uboot.py lacks the k3-like value "
                            f"{value!r}")
        if f"'{value}'" not in rehearsal:
            findings.append(f"kexec-rehearsal.sh lacks the k3-like value "
                            f"{value!r}")
    return findings


def git_show(root, commit, path, pin, findings):
    """PATH as committed at COMMIT, checked against its pin (None: unread)."""
    shown = subprocess.run(["git", "-C", str(root), "show",
                            f"{commit}:{path}"], capture_output=True,
                           check=False)
    if shown.returncode != 0:
        findings.append(f"cannot read {path} at {commit[:8]} with git show "
                        f"from {root}")
        return None
    if hashlib.sha256(shown.stdout).hexdigest() != pin:
        findings.append(f"{path} at {commit[:8]} differs from its pin")
    return shown.stdout.decode("utf-8", errors="replace")


def read_optional(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None


def check_sources(root, require_runtime=False):
    root = pathlib.Path(root)
    findings = []
    r5_runtime = git_show(root, ACCEPTED_R5, R5_RUNTIME, R5_RUNTIME_SHA256,
                          findings)
    plan = git_show(root, ACCEPTED_PLAN, PLAN, PLAN_SHA256, findings)
    b5_runner = git_show(root, ACCEPTED_B5, B5_RUNNER, B5_RUNNER_SHA256,
                         findings)
    tools = {path.name: read_optional(path) for path in RUN_TOOLS}
    if None not in (r5_runtime, plan, b5_runner):
        findings += plan_tool_findings(r5_runtime, plan, b5_runner, tools)
    runtime = read_optional(root / B6_RUNTIME)
    init = read_optional(root / B6_INIT)
    source_dir = root / B6_SRC
    sources = [path.read_text(encoding="utf-8", errors="replace")
               for path in sorted(source_dir.glob("*.[ch]"))] \
        if source_dir.is_dir() else []
    notes = []
    try:
        source_findings, notes = b6_source_findings(runtime, init, sources,
                                                    require_runtime)
        findings += source_findings
    except ValueError as error:
        findings.append(f"cannot parse the B6 sources: {error}")
    for note in notes:
        print(f"note: {note}")
    for finding in findings:
        print(f"finding: {finding}")

    def state(text):
        return "present" if text is not None else "missing (skipped)"

    print(f"BE_B6_MARKER_SOURCES: {'PASS' if not findings else 'FAIL'} "
          f"lines={len(PASS_TEMPLATE)} r3=r5-runtime.c@{ACCEPTED_R5[:8]} "
          f"plan={ACCEPTED_PLAN[:8]} b6-runtime.c={state(runtime)} "
          f"init.c={state(init)}")
    return 0 if not findings else 1


# Self-test fixtures: their own pins (the research Image's sizes) and
# captures built from the plan's lines.
FIXTURE_PINS = Pins(
    1553332, 0x1af628,
    f"Linux version {RELEASE} (b6@fixture) (riscv64-linux-gnu-gcc (GCC) "
    f"16.2.1 20260819, GNU ld version 2.46.1-1.fc44) #1 2026-08-16")
FIXTURE_FDT = 0xbfe00000
FIXTURE_COUNTERS = {"base": 14, "time": 0, "dbcn_write": 89, "dbcn_read": 35,
                    "dbcn_byte": 0, "srst": 1, "refused": 0}
BANNER = ("\r\nOpenSBI v1.6\r\n"
          "Platform Name               : riscv-virtio,qemu\r\n"
          "Runtime SBI Version         : 2.0\r\n"
          f"Domain0 Next Address        : 0x{LAYOUT['STAGING_HPA']:016x}"
          "\r\n\r\n")


def shim_line(hart=BOOT_HART, base=None, fdt=FIXTURE_FDT, dest=None,
              size=None):
    values = (hart, LAYOUT["STAGING_HPA"] if base is None else base, fdt,
              LAYOUT["MONITOR_HPA"] if dest is None else dest,
              LAYOUT["MONITOR_BYTES"] if size is None else size)
    return ("BE_K3_B3: SHIM hart=0x{:016x} shim=0x{:016x} fdt=0x{:016x} "
            "dest=0x{:016x} bytes=0x{:016x}".format(*values))


def entry_lines(pins=FIXTURE_PINS):
    return [line.replace("<T>", ticks)
            .replace("<K>", f"0x{pins.kernel_bytes:x}")
            .replace("<S>", f"0x{pins.image_size:x}")
            for line, ticks in zip(B6_ENTRY, ("",) * 4 + ("0x6a5f3c",
                                                          "0x18f04e", ""))]


def stamp(seconds):
    return f"[{seconds:12.6f}] "


def guest_lines(pins=FIXTURE_PINS, elapsed=1003):
    """A research-like Linux log, tagged, with the required lines."""
    window = LAYOUT["GUEST_BYTES"] // 1024
    body = [
        stamp(0) + pins.banner,
        stamp(0) + "Machine model: Beryllium K3 B6 guest",
        stamp(0) + "SBI specification v2.0 detected",
        stamp(0) + KERNEL_LINES[1],
        stamp(0) + "SBI TIME extension detected",
        stamp(0) + "SBI SRST extension detected",
        stamp(0) + "SBI DBCN extension detected",
        stamp(0) + "earlycon: sbi0 at I/O port 0x0 (options '')",
        stamp(0) + "printk: legacy bootconsole [sbi0] enabled",
        stamp(0) + KERNEL_LINES[2],
        stamp(0) + "riscv-intc: 64 local interrupts mapped",
        stamp(0.003873) + KERNEL_LINES[3],
        stamp(0.147324) + f"Memory: {window - 3592}K/{window}K available "
        f"(694K kernel code, 553K rwdata, 119K rodata, 145K init, 205K bss, "
        f"2964K reserved, 0K cma-reserved)",
        stamp(0.247249) + "printk: legacy console [hvc0] enabled",
        stamp(0.247249) + "printk: legacy console [hvc0] enabled",
        stamp(0.248995) + "printk: legacy bootconsole [sbi0] disabled",
        stamp(0.327393) + KERNEL_LINES[5],
        INIT_LINES[0],
        INIT_LINES[1],
        INIT_LINES[2].replace("<e>", str(elapsed)),
        INIT_LINES[3],
        INIT_LINES[4],
        stamp(1.388986) + POWER_DOWN,
    ]
    return [GUEST_PREFIX + line for line in body]


def shutdown_line(ticks="ticks=0x2f3e8a1", **changes):
    counters = dict(FIXTURE_COUNTERS, **changes)
    exits = counters.pop("exits", sum(counters.values()))
    return EXITS_TEXT + " ".join(
        [str(exits)] + [f"{name}={counters[name]}" for name in COUNTERS[1:]] +
        [ticks])


def pass_lines(pins=FIXTURE_PINS, **changes):
    return [shim_line()] + list(R3_SEQUENCE) + entry_lines(pins) + \
        guest_lines(pins) + [shutdown_line(**changes), SHUTDOWN]


def sample(lines, banner=BANNER, eol="\r\n", after=""):
    """A synthetic capture: a firmware banner, then the lines."""
    return banner + eol.join(lines) + eol + after


def detail(cause, htval=0, pc=0x80201234, tval=0, htinst=0, spvp=1,
           vsatp=0x8000000000081234, exits=57):
    return (f"BE_B6:DETAIL cause=0x{cause:x} pc=0x{pc:x} tval=0x{tval:x} "
            f"htval=0x{htval:x} htinst=0x{htinst:x} spvp={spvp} "
            f"vsatp=0x{vsatp:x} exits={exits}")


def capture_cases():
    """(name, text, options, wanted) for the capture self-test."""
    lines = pass_lines()
    good = sample(lines)
    at = {line.split(" ", 1)[0]: index for index, line in enumerate(lines)
          if not line.startswith(GUEST_PREFIX)}
    first_guest = at["BE_B6:07"] + 1
    exits_at = at["BE_B6:08"]
    pins = {"pins": FIXTURE_PINS}

    def edit(index, line):
        return sample(lines[:index] + [line] + lines[index + 1:])

    def insert(index, *extra):
        return sample(lines[:index] + list(extra) + lines[index:])

    def guest_edit(old, new):
        return sample([new if line == old else line for line in lines])

    noise = GUEST_PREFIX + stamp(0.2) + "clk: Disabling unused clocks"
    kexec = ("[ 4208.994539] kexec_core: Starting new kernel\r\n"
             "[ 4209.068232] Will call new kernel at 108000000 from hart id "
             "0\r\n[ 4209.071298] FDT image at 108200000\r\n"
             "[ 4209.074905] Bye...\r\n")
    cases = [
        ("pass", good, pins, True),
        ("pass, LF only", good.replace("\r", ""), pins, True),
        ("pass after U-Boot noise", sample(
            lines, banner="=> loady 0x140000000\r\nStarting kernel ...\r\n"
            "\r\n"), pins, True),
        ("pass after the kexec handoff", sample(lines, banner=kexec), pins,
         True),
        ("pass with a blank line", edit(first_guest, "\r\n" +
                                        lines[first_guest]), pins, True),
        ("pass with guest noise", insert(exits_at - 1, noise), pins, True),
        ("pass at elapsed 1000", guest_edit(
            GUEST_PREFIX + INIT_LINES[2].replace("<e>", "1003"),
            GUEST_PREFIX + INIT_LINES[2].replace("<e>", "1000")), pins, True),
        ("pass at elapsed 1999", guest_edit(
            GUEST_PREFIX + INIT_LINES[2].replace("<e>", "1003"),
            GUEST_PREFIX + INIT_LINES[2].replace("<e>", "1999")), pins, True),
        ("elapsed 999", guest_edit(
            GUEST_PREFIX + INIT_LINES[2].replace("<e>", "1003"),
            GUEST_PREFIX + INIT_LINES[2].replace("<e>", "999")), pins, False),
        ("elapsed 2000", guest_edit(
            GUEST_PREFIX + INIT_LINES[2].replace("<e>", "1003"),
            GUEST_PREFIX + INIT_LINES[2].replace("<e>", "2000")), pins,
         False),
        ("sleep not ok", guest_edit(
            GUEST_PREFIX + INIT_LINES[2].replace("<e>", "1003"),
            GUEST_PREFIX + INIT_LINES[2].replace("<e>", "1003").replace(
                "ok=1", "ok=0")), pins, False),
        ("sbi-time pass", sample([
            shutdown_line(time=12) if index == exits_at else line
            for index, line in enumerate(lines)
            if not line.endswith(KERNEL_LINES[SSTC_AT])]),
         dict(pins, sbi_time=True), True),
        ("sbi-time with the Sstc timer line", edit(
            exits_at, shutdown_line(time=12)), dict(pins, sbi_time=True),
         False),
        ("sbi-time counters without --sbi-time", edit(
            exits_at, shutdown_line(time=12)), pins, False),
        ("--sbi-time with time=0", good, dict(pins, sbi_time=True), False),
        ("no pins", good, {}, False),
        ("other kernel bytes", good, {"pins": FIXTURE_PINS._replace(
            kernel_bytes=FIXTURE_PINS.kernel_bytes + 1)}, False),
        ("other image_size", good, {"pins": FIXTURE_PINS._replace(
            image_size=FIXTURE_PINS.image_size + 0x1000)}, False),
        ("other banner", good, {"pins": FIXTURE_PINS._replace(
            banner=FIXTURE_PINS.banner + " SMP")}, False),
        ("missing SHIM line", sample(lines[1:]), pins, False),
        ("SHIM at another address", edit(0, shim_line(
            base=LAYOUT["STAGING_HPA"] + 0x1000)), pins, False),
        ("SHIM destination", edit(0, shim_line(
            dest=LAYOUT["MONITOR_HPA"] + 0x200000)), pins, False),
        ("SHIM byte count", edit(0, shim_line(
            size=LAYOUT["MONITOR_BYTES"] - 0x1000)), pins, False),
        ("SHIM on hart 1", edit(0, shim_line(hart=1)), pins, False),
        ("SHIM in upper case", edit(0, lines[0].replace(
            "fdt=0x00000000bfe00000", "fdt=0x00000000BFE00000")), pins,
         False),
        ("two SHIM lines", insert(1, lines[0]), pins, False),
        ("SHIM after BE_R3:01", sample([lines[1], lines[0]] + lines[2:]),
         pins, False),
        ("untagged text after the SHIM line", insert(1, "OpenSBI hello"),
         pins, False),
        ("untagged text among the guest lines", insert(
            exits_at - 1, "[    0.5] Linux line without a tag"), pins,
         False),
        ("text after BE_B6:09", sample(lines, after="sbi_hart: halted\r\n"),
         pins, False),
        ("marker after BE_B6:09", sample(lines + ["BE_B6:10 EXTRA"]), pins,
         False),
        ("guest line after BE_B6:09", sample(lines + [noise]), pins, False),
        ("guest line before BE_B6:07", insert(first_guest - 1, noise), pins,
         False),
        ("guest line between BE_B6:08 and BE_B6:09", insert(
            exits_at + 1, noise), pins, False),
        ("BE_R3:07 kept", insert(at["BE_R3:06"] + 1, R3_DROPPED), pins,
         False),
        ("R4 marker", insert(at["BE_B6:01"], "BE_R4:01 ENTRY_ARMED_IMPORTED"),
         pins, False),
        ("failure after pass", sample(lines + [FAIL_PREFIX + "resume"]),
         pins, False),
        ("SRST returned after pass", sample(lines + [SRST_RETURNED]), pins,
         False),
        ("no shutdown", sample(lines[:-1]), pins, False),
        ("reordered required guest lines", sample(
            lines[:first_guest] + [lines[first_guest + 3]] +
            lines[first_guest:first_guest + 3] + lines[first_guest + 4:]),
         pins, False),
        ("duplicated init line", insert(exits_at - 1, GUEST_PREFIX +
                                        INIT_LINES[3]), pins, False),
        ("unexpected init line", insert(exits_at - 1, GUEST_PREFIX +
                                        "B6INIT 06 EXTRA"), pins, False),
        ("init line without the prefix", insert(
            exits_at - 1, "B6INIT 05 POWER_OFF"), pins, False),
        ("init line with a damaged prefix", guest_edit(
            GUEST_PREFIX + INIT_LINES[0], "BE_B6_GUES: " + INIT_LINES[0]),
         pins, False),
        ("another panic word on the command line", guest_edit(
            GUEST_PREFIX + stamp(0) + KERNEL_LINES[2],
            GUEST_PREFIX + stamp(0) + KERNEL_LINES[2] + " panic_print=1"),
         pins, False),
        ("more memory than the window", guest_edit(
            next(line for line in lines if "Memory: " in line),
            next(line for line in lines if "Memory: " in line).replace(
                "61944K/", f"{LAYOUT['GUEST_BYTES'] // 1024 + 1}K/")),
         pins, False),
        ("a larger memory total", guest_edit(
            next(line for line in lines if "Memory: " in line),
            next(line for line in lines if "Memory: " in line).replace(
                f"/{LAYOUT['GUEST_BYTES'] // 1024}K",
                f"/{LAYOUT['GUEST_BYTES'] // 512}K")), pins, False),
        ("escape in a guest line", insert(exits_at - 1, GUEST_PREFIX +
                                          "\x1b[2Jclear"), pins, False),
        ("tab in a guest line", insert(exits_at - 1, GUEST_PREFIX + "a\tb"),
         pins, False),
        ("mid-line CR", insert(exits_at - 1, GUEST_PREFIX + "a\rb"), pins,
         False),
        ("undecodable byte", insert(exits_at - 1, GUEST_PREFIX + "\ufffd"),
         pins, False),
        ("exits not the sum", edit(exits_at, shutdown_line(exits=140)), pins,
         False),
        ("exits above the ceiling", edit(exits_at, shutdown_line(
            dbcn_write=LAYOUT["EXIT_CEILING"])), pins, False),
        ("srst=2", edit(exits_at, shutdown_line(srst=2)), pins, False),
        ("refused call", edit(exits_at, shutdown_line(refused=1)), pins,
         False),
        ("DBCN write_byte call", edit(exits_at, shutdown_line(dbcn_byte=1)),
         pins, False),
        ("exits with a leading zero", edit(exits_at, lines[exits_at].replace(
            "exits=139", "exits=0139")), pins, False),
        ("exits in hex", edit(exits_at, lines[exits_at].replace(
            "exits=139", "exits=0x8b")), pins, False),
        ("ticks in decimal", edit(exits_at, shutdown_line(
            ticks="ticks=49539233")), pins, False),
        ("ticks with a leading zero", edit(at["BE_B6:05"], lines[
            at["BE_B6:05"]].replace("ticks=0x6a5f3c", "ticks=0x06a5f3c")),
         pins, False),
        ("ticks in upper case", edit(at["BE_B6:05"], lines[
            at["BE_B6:05"]].replace("ticks=0x6a5f3c", "ticks=0x6A5F3C")),
         pins, False),
        ("forged hedeleg", edit(at["BE_B6:04"], lines[at["BE_B6:04"]].replace(
            "hedeleg=0xb15d", "hedeleg=0xb17d")), pins, False),
        ("hedeleg without page faults", edit(at["BE_B6:04"], lines[
            at["BE_B6:04"]].replace("hedeleg=0xb15d", "hedeleg=0x315d")),
         pins, False),
        ("hedeleg with a leading zero", edit(at["BE_B6:04"], lines[
            at["BE_B6:04"]].replace("hedeleg=0xb15d", "hedeleg=0x0b15c")),
         pins, False),
        ("WARL hedeleg without cause 0", edit(at["BE_B6:04"], lines[
            at["BE_B6:04"]].replace("hedeleg=0xb15d", "hedeleg=0xb15c")),
         pins, True),
        ("WARL hedeleg without causes 0, 4, and 6", edit(at["BE_B6:04"], lines[
            at["BE_B6:04"]].replace("hedeleg=0xb15d", "hedeleg=0xb10c")),
         pins, True),
        ("another pool", edit(at["BE_B6:01"], lines[at["BE_B6:01"]].replace(
            "pool=0x102034000", "pool=0x102038000")), pins, False),
        ("another DTB size", edit(at["BE_B6:06"], lines[at["BE_B6:06"]]
                                  .replace("dtb_bytes=0x1000",
                                           "dtb_bytes=0x2000")), pins, False),
        ("another a1", edit(at["BE_B6:07"], lines[at["BE_B6:07"]].replace(
            "a1=0x83e00000", "a1=0x0")), pins, False),
        ("--after on a pass", good, dict(pins, after="BE_B6:07"), False),
    ]
    # Dropping any required line fails; dropping guest noise does not.
    patterns = [template_pattern(line, FIXTURE_PINS)
                for line in GUEST_TEMPLATE]
    for index, line in enumerate(lines):
        required = not line.startswith(GUEST_PREFIX) or \
            any(pattern.fullmatch(line) for pattern in patterns)
        cases.append((f"without line {index + 1} "
                      f"({'required' if required else 'noise'})",
                      sample(lines[:index] + lines[index + 1:]), pins,
                      not required))
    for pattern in REJECTED:
        cases.append((f"rejected {pattern!r}", insert(
            exits_at - 1, GUEST_PREFIX + stamp(0.9) + f"x {pattern} y"), pins,
            False))
    for tag in GUEST_FORBIDDEN:
        cases.append((f"guest line holding {tag!r}", insert(
            exits_at - 1, GUEST_PREFIX + f"echo {tag}"), pins, False))
    return lines, good, cases


# A controls readback as the monitor prints it (hedeleg off its WARL set).
CONTROLS_READBACK = (
    "BE_B6:DETAIL controls hip=0x0 hstatus=0x200000180 hedeleg=0xb17d "
    "hideleg=0x40 hie=0x0 hvip=0x0 hcounteren=0x2 htimedelta=0x0",
    "BE_B6:DETAIL controls henvcfg=0x8000000000000000 hgeie=0x0 "
    "vstimecmp=0xffffffffffffffff sie=0x0 sstatus=0x200000000 "
    "hgatp=0x8000000000102034 vsatp=0x0 sscratch=0x102027000",
)


def failure_cases(lines):
    """(name, text, options, wanted) for --expect-fail."""
    at = {line.split(" ", 1)[0]: index for index, line in enumerate(lines)
          if not line.startswith(GUEST_PREFIX)}
    head = lines[:at["BE_B6:07"] + 1]
    guest_run = head + guest_lines()[:6]
    pins = {"pins": FIXTURE_PINS}
    sbi30 = "\r\nOpenSBI v1.7\r\nRuntime SBI Version : 3.0\r\n\r\n"
    window_end = LAYOUT["GUEST_GPA"] + LAYOUT["GUEST_BYTES"]
    beyond = detail(21, htval=(window_end + 0x1000) >> 2, tval=0xff60000)
    inside = detail(21, htval=(LAYOUT["GUEST_GPA"] + 0x1000) >> 2)
    panic = [GUEST_PREFIX + stamp(0.33) + "Kernel panic - not syncing: "
             "Attempted to kill init! exitcode=0x00000000",
             GUEST_PREFIX + stamp(0.33) + "---[ end Kernel panic - not "
             "syncing: Attempted to kill init! exitcode=0x00000000 ]---"]

    def fail(klass, before, *after, **options):
        return sample(before + [FAIL_PREFIX + klass] + list(after)), \
            dict(pins, expect_fail=klass, **options)

    def case(name, built, wanted):
        return (name, built[0], built[1], wanted)

    shim = [lines[0]]
    r3 = shim + list(R3_SEQUENCE)
    return [
        ("sbi-3.0 boot refusal", sample(shim + [FAIL_PREFIX + "boot"],
                                        banner=sbi30),
         dict(pins, expect_fail="boot", after="none"), True),
        case("boot refusal, SRST returned", fail(
            "boot", shim, SRST_RETURNED, after="none"), True),
        case("boot refusal without the SHIM line", fail(
            "boot", [], after="none"), False),
        case("boot failure after BE_R3:03", fail(
            "boot", shim + list(R3_SEQUENCE[:3]), after="BE_R3:03"), True),
        case("boot failure after BE_R3:03 is not before BE_R3:01", fail(
            "boot", shim + list(R3_SEQUENCE[:3]), after="none"), False),
        case("gstage", fail("gstage", r3, after="BE_R3:06"), True),
        case("no-sstc", fail("sstc", head[:at["BE_B6:02"] + 1],
                             after="BE_B6:02"), True),
        case("sstc with a detail", fail(
            "sstc", head[:at["BE_B6:02"] + 1], detail(2), after="BE_B6:02"),
            False),
        case("sstc after BE_B6:03", fail(
            "sstc", head[:at["BE_B6:03"] + 1], after="BE_B6:02"), False),
        case("controls", fail("controls", head[:at["BE_B6:03"] + 1],
                              after="BE_B6:03"), True),
        case("controls with its readback", fail(
            "controls", head[:at["BE_B6:03"] + 1], *CONTROLS_READBACK,
            after="BE_B6:03"), True),
        case("controls with half its readback", fail(
            "controls", head[:at["BE_B6:03"] + 1], CONTROLS_READBACK[0],
            after="BE_B6:03"), False),
        case("controls readback out of order", fail(
            "controls", head[:at["BE_B6:03"] + 1], CONTROLS_READBACK[1],
            CONTROLS_READBACK[0], after="BE_B6:03"), False),
        case("controls with an exit detail", fail(
            "controls", head[:at["BE_B6:03"] + 1], detail(2),
            after="BE_B6:03"), False),
        case("payload with a controls readback", fail(
            "payload", head[:at["BE_B6:04"] + 1], *CONTROLS_READBACK,
            after="BE_B6:04"), False),
        case("payload variant", fail("payload", head[:at["BE_B6:04"] + 1],
                                     after="BE_B6:04"), True),
        case("payload with a detail", fail(
            "payload", head[:at["BE_B6:04"] + 1], detail(2),
            after="BE_B6:04"), False),
        case("memory variant", fail(
            "guest-page-fault", guest_run, beyond, after="BE_B6:07",
            above_window=True), True),
        case("memory variant, fault inside the window", fail(
            "guest-page-fault", guest_run, inside, after="BE_B6:07",
            above_window=True), False),
        case("memory variant, htval 0", fail(
            "guest-page-fault", guest_run, detail(21), after="BE_B6:07",
            above_window=True), False),
        case("guest-page fault without detail", fail(
            "guest-page-fault", guest_run, after="BE_B6:07"), False),
        case("guest-page fault with cause 22", fail(
            "guest-page-fault", guest_run, detail(22)), False),
        case("rdcycle variant", fail(
            "virtual-instruction", guest_run, detail(22), after="BE_B6:07",
            cause=22), True),
        case("rdcycle variant, cause 2", fail(
            "virtual-instruction", guest_run, detail(2), cause=22), False),
        case("access fault", fail("access-fault", guest_run, detail(5)),
             True),
        case("access fault with cause 13", fail(
            "access-fault", guest_run, detail(13)), False),
        case("illegal instruction", fail(
            "illegal-instruction", guest_run, detail(2)), True),
        case("interrupt", fail("interrupt", guest_run,
                               detail(INTERRUPT | 5)), True),
        case("interrupt without the interrupt bit", fail(
            "interrupt", guest_run, detail(5)), False),
        case("VU ecall exception", fail("exception", guest_run, detail(8)),
             True),
        case("exception with a guest-page cause", fail(
            "exception", guest_run, detail(21)), False),
        case("exception without detail", fail("exception", guest_run),
             True),
        case("exit-budget variant", fail(
            "exit-budget", guest_run, detail(10), after="BE_B6:07"), True),
        case("exit-budget without detail", fail("exit-budget", guest_run),
             True),
        case("guest-timeout variant", fail(
            "guest-timeout", guest_run, detail(10), after="BE_B6:07"), True),
        case("init-exit variant: Linux panics, then reboots", fail(
            "guest-reboot", guest_run + panic, detail(10),
            after="BE_B6:07"), True),
        case("resume", fail("resume", guest_run), True),
        case("console", fail("console", guest_run, detail(10)), True),
        case("guest failure", fail("guest-failure", guest_run), True),
        case("shutdown returned", fail(
            "shutdown-returned", lines, SRST_RETURNED,
            after="BE_B6:09"), True),
        case("detail without exits", fail(
            "virtual-instruction", guest_run,
            detail(22).rsplit(" ", 1)[0]), False),
        case("detail in upper case", fail(
            "virtual-instruction", guest_run,
            detail(22).replace("0x16", "0X16")), False),
        case("detail with spvp=2", fail(
            "virtual-instruction", guest_run,
            detail(22).replace("spvp=1", "spvp=2")), False),
        ("class differs", sample(r3 + [FAIL_PREFIX + "gstage"]),
         dict(pins, expect_fail="sstc"), False),
        ("unknown class", sample(r3 + [FAIL_PREFIX + "bogus"]),
         dict(pins, expect_fail="bogus"), False),
        ("class with trailing text", sample(r3 + [FAIL_PREFIX + "gstage x"]),
         dict(pins, expect_fail="gstage"), False),
        case("failure after a skipped line", fail(
            "boot", shim + [R3_SEQUENCE[0], R3_SEQUENCE[2]]), False),
        case("guest line before BE_B6:07", fail(
            "sstc", head[:at["BE_B6:02"] + 1] + guest_lines()[:1]), False),
        case("two SRST returned", fail(
            "gstage", r3, SRST_RETURNED, SRST_RETURNED), False),
        case("marker after the failure", fail(
            "gstage", r3, B6_ENTRY[0]), False),
        case("two failures", fail("gstage", r3, FAIL_PREFIX + "gstage"),
             False),
        ("detail before the failure", sample(guest_run + [
            detail(21), FAIL_PREFIX + "guest-page-fault"]),
         dict(pins, expect_fail="guest-page-fault"), False),
        ("noise after the failure", sample(r3 + [FAIL_PREFIX + "gstage"],
                                           after="garbage\r\n"),
         dict(pins, expect_fail="gstage"), False),
        ("pass is not a failure", sample(lines),
         dict(pins, expect_fail="gstage"), False),
        ("--sbi-time on a failure", sample(r3 + [FAIL_PREFIX + "gstage"]),
         dict(pins, expect_fail="gstage", sbi_time=True), False),
        ("failure after BE_B6:06 without pins", sample(
            head + [FAIL_PREFIX + "exit-budget"]),
         {"expect_fail": "exit-budget"}, False),
        ("failure before BE_B6:06 without pins", sample(
            head[:at["BE_B6:04"] + 1] + [FAIL_PREFIX + "payload"]),
         {"expect_fail": "payload"}, True),
    ]


# A realistic fixture: the B6-1 reference boot's Linux log, tagged, among
# the plan's monitor lines (see its header). Its pins are its own lines.
REALISTIC = HERE / "fixtures" / "qemu-k3-like.console.log"


def realistic_pins(text):
    """Pins from a capture's own BE_B6:06 and `Linux version` lines."""
    sizes = re.search(r"kernel_bytes=(0x[0-9a-f]+) image_size=(0x[0-9a-f]+) ",
                      text)
    banner = re.search(rf"{re.escape(GUEST_PREFIX)}\[ *[0-9.]+\] "
                       rf"(Linux version {re.escape(RELEASE)} [ -~]+)", text)
    return Pins(int(sizes.group(1), 16), int(sizes.group(2), 16),
                banner.group(1))


def realistic_cases():
    """(name, text, options, wanted) for the realistic fixture."""
    # The file has LF line ends; serial captures have CRLF.
    text = REALISTIC.read_bytes().decode("ascii").replace("\n", "\r\n")
    pins = {"pins": realistic_pins(text)}
    run_init = GUEST_PREFIX + "[    0.111487] Run /init as init process"
    warning = (GUEST_PREFIX + "[    0.112000] WARNING: CPU: 0 PID: 1 at "
               "init/main.c:1 kernel_init+0x0/0x0")
    reference_tail = text[:text.index(EXITS_TEXT)]
    return [
        ("realistic QEMU capture", text, pins, True),
        ("realistic, LF only", text.replace("\r", ""), pins, True),
        ("realistic, the reference boot's SBI identity", text.replace(
            "ID=0x4245 Version=0x2", "ID=0x1 Version=0x10006"), pins, False),
        ("realistic, an untagged kernel line", text.replace(
            run_init, run_init[len(GUEST_PREFIX):]), pins, False),
        ("realistic, a WARNING splat", text.replace(
            run_init, run_init + "\r\n" + warning), pins, False),
        ("realistic, ending as the reference boot did", reference_tail, pins,
         False),
        ("realistic, other pins", text, {"pins": FIXTURE_PINS}, False),
    ]


# Self-test fixtures for the source checks (the real check reads the
# accepted plan and the B6 sources).
FIXTURE_K3 = ("virt,aia=aplic-imsic,aia-guests=7",
              "rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,"
              "sv57=off,smstateen=true")
FIXTURE_R5_CPU = ("rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,"
                  "sv57=off,sstc=false,smstateen=false,svadu=false,"
                  "debug=false")
FIXTURE_VARIANTS = (
    ("payload", "payload", "BE_B6:04", None, None),
    ("memory", "guest-page-fault", "BE_B6:07", None, "above-window"),
    ("init-exit", "guest-reboot", "BE_B6:07", None, None),
    ("rdcycle", "virtual-instruction", "BE_B6:07", 22, None),
    ("exit-budget", "exit-budget", "BE_B6:07", None, None),
    ("guest-timeout", "guest-timeout", "BE_B6:07", None, None),
)
FIXTURE_PLAN_ROWS = {
    "payload": " after `BE_B6:04` ",
    "memory": ", faulting GPA (`htval` << 2) at or above the window end ",
    "rdcycle": ", cause 22 ",
}


def runtime_fixture():
    monitor = B6_ENTRY + (GUEST_SHUTDOWN, SHUTDOWN)
    out = ["/* BE_B6:10 FUTURE is a comment, not a literal */",
           '#include "b6.h"']
    out += [f'static const char r3_{index}[] = "{line}\\n";'
            for index, line in enumerate(R3_SEQUENCE)]
    for index, line in enumerate(monitor):
        fixed = fixed_text(line)
        if index == 1:
            # Adjacent literals with a comment between them, joined by C.
            fixed = f'{fixed[:12]}" /* joined */\n\t"{fixed[12:]}'
        out.append(f'static const char b6_{index}[] = "{fixed}";')
        out += [f'static const char b6_{index}_{field}[] = "{name}";'
                for field, name in enumerate(field_names(line))]
    texts = (GUEST_PREFIX, FAIL_PREFIX, "BE_B6:DETAIL cause=",
             SRST_RETURNED + "\\n") + tuple(f" {name}=" for name in
                                             DETAIL_FIELDS[1:])
    out += [f'static const char text_{index}[] = "{text}";'
            for index, text in enumerate(texts)]
    out.append("static const char *const classes[] = { " +
               ", ".join(f'"{klass}"' for klass in CLASSES) + " };")
    out.append("static const char quote = '\"';")
    return "\n".join(out) + "\n"


def init_fixture():
    return ('#include "init.h"\n'
            'static const char prefix[] = "B6INIT ";\n'
            'static const char start[] = "01 START pid=";\n'
            'static const char failed[] = "04 RESULT fail\\n";\n')


def plan_fixture():
    rows = "\n".join(
        f"| `{name}` | change | `BE_B6:FAIL {klass}`"
        f"{FIXTURE_PLAN_ROWS.get(name, ' ')}|"
        for name, klass, _, _, _ in FIXTURE_VARIANTS)
    classes = ", ".join(f"`{klass}`" for klass in CLASSES)
    rejected = ", ".join(f"`{pattern}`" for pattern in REJECTED)
    shim = SHIM_FIXED
    return (f"**Negative variants**, each one change:\n\n"
            f"| Variant | Change | Expected |\n| --- | --- | --- |\n"
            f"{rows}\n\n## Markers\n\nEach run first prints B3's `SHIM` "
            f"line, which must show\n`{shim[0]}`, `{shim[1]}`, and\n"
            f"`{shim[2]}`. Lines:\n\n```text\n" +
            "\n".join(PASS_TEMPLATE) + "\n```\n\n"
            f"- **Rejected** in any guest line, as case-sensitive\n"
            f"  substrings: {rejected.replace('`Oops`', '(x) `Oops`')}. "
            f"Also rejected: more.\n"
            f"- A failure adds\n\n  `{DETAIL_TEMPLATE}`.\n\n"
            f"- Classes: {classes} (as R5 uses `import`). The run tools'\n"
            f"  terminal regex is `{TERMINAL_REGEX}`.\n\n"
            f"**QEMU scenarios** use QEMU.\n\n"
            f"| `k3-like` | `{FIXTURE_K3[0]}`; `{FIXTURE_K3[1]}` | GCC | x |\n"
            f"| `rva23` | `virt,aia=aplic-imsic`; `rva23s64` | GCC | x |\n"
            f"| `plic` | `virt`; `rv64,h=true` | GCC | x |\n"
            f"| `no-sstc` | `virt,aia=none` with the R5 CPU | GCC | "
            f"`BE_B6:FAIL sstc` after `BE_B6:02` |\n"
            f"| `sbi-3.0` | `k3-like` with OpenSBI 1.7 | GCC | "
            f"`BE_B6:FAIL boot` before `BE_R3:01` |\n\n**Copied tools**\n")


def tools_fixture():
    variants = "\n".join(
        f"\t'{name} {klass} {after} {cause or '-'} {check or '-'}'"
        for name, klass, after, cause, check in FIXTURE_VARIANTS)
    return {
        "run-qemu.sh": (
            f"terminal_regex='{TERMINAL_REGEX}'\n"
            f"k3_machine='{FIXTURE_K3[0]}'\nk3_cpu='{FIXTURE_K3[1]}'\n"
            f"minimal='{FIXTURE_R5_CPU}'\nvariants=(\n{variants}\n)\n"
            "\trun rva23 $tc $elf virt,aia=aplic-imsic rva23s64 x\n"
            "\trun plic $tc $elf virt rv64,h=true x\n"
            '\trun no-sstc $tc $elf virt,aia=none "$minimal" $fw 2.0 \\\n'
            "\t\tsstc BE_B6:02 - - || failed=1\n"
            '\trun sbi-3.0 $tc $elf "$k3_machine" "$k3_cpu" default 3.0 '
            "boot none - -\n"),
        "run-qemu-uboot.py": (
            f'TERMINAL = re.compile(rb"{TERMINAL_REGEX}")\n'
            f'MACHINE = "{FIXTURE_K3[0]}"\n'
            f'CPU = "{FIXTURE_K3[1][:34]}"\\\n    "{FIXTURE_K3[1][34:]}"\n'),
        "kexec-rehearsal.sh": (
            f"terminal_regex='{TERMINAL_REGEX}|BE_B6_KEXEC: FAIL'\n"
            f"k3_machine='{FIXTURE_K3[0]}'\nk3_cpu='{FIXTURE_K3[1]}'\n"),
        "k3-uboot-run.sh": f"terminal_regex='{TERMINAL_REGEX}'\n",
        "k3-run.sh": f"terminal_regex='{TERMINAL_REGEX}'\n",
    }


def source_cases():
    runtime = runtime_fixture()
    init = init_fixture()
    r5 = "\n".join(f'"{line}\\n"' for line in R3_SEQUENCE + (
        R3_DROPPED, "BE_R4:01 ENTRY_ARMED_IMPORTED")) + '\n"BE_R5:FAIL "\n'
    plan = plan_fixture()
    b5 = f"minimal='{FIXTURE_R5_CPU}'\n"
    tools = tools_fixture()

    def tool(name, text):
        return dict(tools, **{name: text})

    header = f'#define TAG "{GUEST_PREFIX}"\n'
    untagged = runtime.replace(GUEST_PREFIX, "TAG: ")

    def b6_case(name, runtime_text, init_text, wanted, headers=(),
                require=False):
        sources = ([runtime_text] if runtime_text else []) + list(headers)
        return name, (runtime_text, init_text, sources, require), wanted

    b6 = [
        b6_case("B6 sources complete", runtime, init, True),
        b6_case("guest tag only in a header", untagged, init, True,
                [header]),
        b6_case("b6-runtime.c missing: skipped", None, init, True),
        b6_case("b6-runtime.c missing, --require-runtime", None, init, False,
                require=True),
        b6_case("init.c missing: skipped", runtime, None, True),
        b6_case("no guest tag literal", untagged, init, False),
        b6_case("BE_B6:05 misspelt", runtime.replace(
            "RAM_CLEARED", "RAM_CLEAR"), init, False),
        b6_case("a field name missing", runtime.replace(
            '" hedeleg="', '" hdeleg="'), init, False),
        b6_case("a detail field missing", runtime.replace(
            '" htinst="', '" inst="'), init, False),
        b6_case("BE_R3:07 kept", runtime + f'"{R3_DROPPED}\\n";\n', init,
                False),
        b6_case("a B5 marker left over", runtime +
                '"BE_B5:01 SSTC_STCE_READBACK henvcfg=";\n', init, False),
        b6_case("an extra BE_B6 marker in a header", runtime, init, False,
                ['#define EXTRA "BE_B6:10 EXTRA\\n"\n']),
        b6_case("a fixed text only in a comment", runtime.replace(
            '"BE_B6:03 SSTC_STCE_READBACK henvcfg=";', "0; /* BE_B6:03 "
            "SSTC_STCE_READBACK henvcfg= */"), init, False),
        b6_case("a class without a literal", runtime.replace(
            '"guest-timeout", ', ""), init, False),
        b6_case("init source forging a tag", runtime,
                init + '"BE_B6:09 SHUTDOWN";\n', False),
        b6_case("init source without B6INIT", runtime,
                init.replace("B6INIT", "INIT"), False),
    ]
    plans = [
        ("accepted inputs and tools agree", (r5, plan, b5, tools), True),
        ("an R3 literal differs", (r5.replace("R1_DERIVED", "R1"), plan, b5,
                                   tools), False),
        ("BE_R3:07 not in the accepted source", (r5.replace(
            R3_DROPPED, "BE_R3:08 X"), plan, b5, tools), False),
        ("the Markers block differs", (r5, plan.replace(
            "a1=0x83e00000", "a1=0x83f00000"), b5, tools), False),
        ("a class differs", (r5, plan.replace("`console`", "`uart`"), b5,
                             tools), False),
        ("the terminal regex differs", (r5, plan.replace(
            "BE_K3_B3: FAIL`", "BE_K3_B3:FAIL`"), b5, tools), False),
        ("a rejected pattern differs", (r5, plan.replace(
            "`segfault`", "`segv`"), b5, tools), False),
        ("the DETAIL line differs", (r5, plan.replace(
            "spvp=<0|1>", "spv=<0|1>"), b5, tools), False),
        ("a SHIM value differs", (r5, plan.replace(
            SHIM_FIXED[1], "dest=0x0000000102200000"), b5, tools), False),
        ("a variant class differs", (r5, plan, b5, tool(
            "run-qemu.sh", tools["run-qemu.sh"].replace(
                "'rdcycle virtual-instruction", "'rdcycle illegal-instruction"
            ))), False),
        ("a variant cause differs", (r5, plan, b5, tool(
            "run-qemu.sh", tools["run-qemu.sh"].replace(
                "BE_B6:07 22 -", "BE_B6:07 2 -"))), False),
        ("the payload variant after another line", (r5, plan, b5, tool(
            "run-qemu.sh", tools["run-qemu.sh"].replace(
                "'payload payload BE_B6:04", "'payload payload BE_B6:05"))),
         False),
        ("the memory variant without the window check", (r5, plan, b5, tool(
            "run-qemu.sh", tools["run-qemu.sh"].replace(
                "above-window'", "-'"))), False),
        ("the no-sstc run after another line", (r5, plan, b5, tool(
            "run-qemu.sh", tools["run-qemu.sh"].replace(
                "sstc BE_B6:02", "sstc BE_B6:03"))), False),
        ("the sbi-3.0 run after BE_R3:01", (r5, plan, b5, tool(
            "run-qemu.sh", tools["run-qemu.sh"].replace(
                "boot none", "boot BE_R3:01"))), False),
        ("the U-Boot CPU differs", (r5, plan, b5, tool(
            "run-qemu-uboot.py", tools["run-qemu-uboot.py"].replace(
                "svade=true,", ""))), False),
        ("the rehearsal machine differs", (r5, plan, b5, tool(
            "kexec-rehearsal.sh", tools["kexec-rehearsal.sh"].replace(
                "aia-guests=7", "aia-guests=5"))), False),
        ("the R5 CPU differs", (r5, plan, b5, tool(
            "run-qemu.sh", tools["run-qemu.sh"].replace(
                "debug=false", "debug=true"))), False),
        ("the plic row is missing from the runner", (r5, plan, b5, tool(
            "run-qemu.sh", tools["run-qemu.sh"].replace(
                "virt rv64,h=true", "virt rv64"))), False),
        ("a board tool lacks the regex", (r5, plan, b5, tool(
            "k3-run.sh", "terminal_regex='BE_B6:09'\n")), False),
        ("a run tool is missing", (r5, plan, b5, tool("k3-uboot-run.sh",
                                                      None)), False),
    ]
    return b6, plans


def pins_text(pins=FIXTURE_PINS, **changes):
    lines = {
        "image": f"file build/k3-b6/guest/linux/Image sha256={'a' * 64} "
                 f"bytes={pins.kernel_bytes}",
        "init": f"file init sha256={'b' * 64} bytes=4096",
        "image_size": f"kernel image_size=0x{pins.image_size:x}",
        "text_offset": f"kernel text_offset=0x"
                       f"{LAYOUT['KERNEL_TEXT_OFFSET']:x}",
        "banner": f"kernel banner={pins.banner}",
    }
    lines.update(changes)
    return "# B6 guest pins\n" + "\n".join(
        line for line in lines.values() if line is not None) + "\n"


def helper_checks(lines, good):
    """(name, ok) for the parsers, records' fields, and the templates."""
    checks = []
    record = result_record("x", "pass", extract(good), True, [], "gcc",
                           FIXTURE_PINS)
    fields = record["fields"]
    checks.append(("pass fields", fields.get("hart") == "0x" + "0" * 16 and
                   fields.get("base") == f"0x{LAYOUT['STAGING_HPA']:016x}"
                   and fields.get("fdt") == f"0x{FIXTURE_FDT:016x}" and
                   fields.get("exits") == "139" and
                   fields.get("elapsed_ms") == "1003" and
                   fields.get("hgatp") == f"hgatp=0x{LAYOUT['HGATP']:x}" and
                   fields.get("shutdown") == "type=0 reason=0" and
                   all(isinstance(value, str) for value in fields.values())))
    denied = sample(lines[:lines.index(B6_ENTRY[-1]) + 1] + [
        FAIL_PREFIX + "guest-page-fault", detail(21), SRST_RETURNED])
    fields = result_record("x", "fail", extract(denied), True,
                           [])["fields"]
    checks.append(("failure fields", fields.get("failure") ==
                   "guest-page-fault" and fields.get("detail") ==
                   detail(21)[len(DETAIL_PREFIX):] and
                   fields.get("srst_returned") == "yes"))
    checks.append(("exits printed", exits_report(extract(good)) ==
                   "BE_B6_EXITS: exits=139 base=14 time=0 dbcn_write=89 "
                   "dbcn_read=35 dbcn_byte=0 srst=1 refused=0"))
    checks.append(("27 template lines, 15 monitor lines",
                   len(PASS_TEMPLATE) == 27 and len(MONITOR) == 15 and
                   GUEST_AT == 13 and len(LINE_IDS) == 16))
    checks.append(("pins file", parse_pins(pins_text(), "x") ==
                   FIXTURE_PINS))
    bad_pins = {
        "no banner": pins_text(banner=None),
        "no Image": pins_text(image=None),
        "other text_offset": pins_text(text_offset="kernel text_offset="
                                       "0x400000"),
        "two Images": pins_text(init=f"file Image sha256={'c' * 64} "
                                     f"bytes=10"),
        "malformed file pin": pins_text(init="file init bytes=1"),
        "Image above its budget": pins_text(
            image=f"file Image sha256={'a' * 64} bytes="
                  f"{LAYOUT['KERNEL_FILE_MAX'] + 1}"),
        "image_size below the file": pins_text(
            image_size="kernel image_size=0x1000"),
        "another release": pins_text(banner="kernel banner=Linux version "
                                     "6.18.0 (x) #1"),
    }
    for name, text in bad_pins.items():
        try:
            parse_pins(text, "x")
            checks.append((f"pins refused: {name}", False))
        except ValueError:
            checks.append((f"pins refused: {name}", True))
    header = LAYOUT_HEADER.read_text(encoding="utf-8")
    layout = parse_layout(header, "x")
    checks.append(("layout relations", layout["POOL_HPA"] ==
                   layout["MONITOR_HPA"] + layout["MONITOR_BYTES"] and
                   layout["GUEST_LEAVES"] * 0x200000 ==
                   layout["GUEST_BYTES"] and layout["DTB_GPA"] ==
                   layout["GUEST_GPA"] + layout["GUEST_BYTES"] - 0x200000))
    for name, text in (("missing", header.replace("BE_B6_HGATP", "X")),
                       ("twice", header + "#define BE_B6_HGATP\t"
                                          "BE_B6_C(0x1)\n")):
        try:
            parse_layout(text, "x")
            checks.append((f"layout refused: {name}", False))
        except ValueError:
            checks.append((f"layout refused: {name}", True))
    patterns = [template_pattern(line, FIXTURE_PINS)
                for line in PASS_TEMPLATE]
    checks.append(("the fixture fills every template line", all(
        any(pattern.fullmatch(line) for line in lines)
        for pattern in patterns[:-2]) and
        counter_findings(lines[-2]) == (dict(FIXTURE_COUNTERS, exits=139),
                                        []) and lines[-1] == SHUTDOWN))
    checks.append(("C literals", c_literals(
        '"a\\x41\\102\\n" "b" /* "c" */ "d" \'"\' "e" // "f"\n"g"') ==
        ["aAB\nbd", "eg"]))
    try:
        c_literals('x = "abc')
        checks.append(("unterminated literal", False))
    except ValueError:
        checks.append(("unterminated literal", True))
    checks.append(("field names", field_names(GUEST_SHUTDOWN) == (
        " reason=", " exits=", " base=", " time=", " dbcn_write=",
        " dbcn_read=", " dbcn_byte=", " srst=", " refused=", " ticks=")))
    plan = plan_fixture()
    checks.append(("plan parsers", plan_markers(plan) == PASS_TEMPLATE and
                   plan_classes(plan) == (CLASSES, TERMINAL_REGEX) and
                   plan_rejected(plan) == REJECTED and
                   plan_detail(plan) == DETAIL_TEMPLATE and
                   plan_shim(plan) == SHIM_FIXED and
                   [row[:3] for row in plan_variants(plan)] == [
                       (name, klass, cause) for name, klass, _, cause, _ in
                       FIXTURE_VARIANTS] and
                   plan_outcomes(plan) == {"no-sstc": ("sstc", "BE_B6:02"),
                                           "sbi-3.0": ("boot", "none")} and
                   runner_variants(tools_fixture()["run-qemu.sh"]) ==
                   FIXTURE_VARIANTS and
                   plan_scenarios(plan)["k3-like"] == FIXTURE_K3))
    return checks


def self_test():
    lines, good, cases = capture_cases()
    cases += failure_cases(lines)
    cases += realistic_cases()
    failed = 0
    for name, text, options, wanted in cases:
        ok, findings = evaluate(text, **options)
        failed += ok != wanted
        print(f"{'ok  ' if ok == wanted else 'FAIL'} {name}: ok={ok} "
              f"findings={findings[:4]}")
    records = [
        ("record pass", good, None, "PASS", "PASS", "shutdown-requested"),
        ("record failure after pass", sample(lines + [
            FAIL_PREFIX + "resume"]), None, "FAIL", "FAIL", "fail-marker"),
        ("record truncated", sample(lines[:-1]), None, "FAIL", "FAIL",
         "none"),
        ("record guest stopped", sample(lines[:20]), None, "FAIL", "FAIL",
         "none"),
        ("record forged extra", sample(lines + ["BE_B6:10 EXTRA"]), None,
         "FAIL", "PASS", "none"),
        ("record no-sstc", sample(lines[:lines.index(B6_ENTRY[1]) + 1] + [
            FAIL_PREFIX + "sstc"]), "sstc", "PASS", "FAIL", "fail-marker"),
    ]
    for name, text, expect_fail, result, boot, end in records:
        markers = extract(text)
        ok, findings = evaluate(text, expect_fail, FIXTURE_PINS)
        record = result_record("x", expect_fail or "pass", markers, ok,
                               findings, "gcc", FIXTURE_PINS)
        got = (record["result"], record["boot_marker"], record["terminal"])
        wanted = (result, boot, end)
        failed += got != wanted
        print(f"{'ok  ' if got == wanted else 'FAIL'} {name}: "
              f"result/boot_marker/terminal={got}")
    checks = helper_checks(lines, good)
    for name, ok in checks:
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}")
    b6_cases, plan_cases = source_cases()
    for name, arguments, wanted in b6_cases:
        findings, notes = b6_source_findings(*arguments)
        failed += (not findings) != wanted
        print(f"{'ok  ' if (not findings) == wanted else 'FAIL'} sources: "
              f"{name}: findings={findings[:3]} notes={notes}")
    for name, arguments, wanted in plan_cases:
        findings = plan_tool_findings(*arguments)
        failed += (not findings) != wanted
        print(f"{'ok  ' if (not findings) == wanted else 'FAIL'} plan and "
              f"tools: {name}: findings={findings[:3]}")
    total = len(cases) + len(records) + len(checks) + len(b6_cases) + \
        len(plan_cases)
    print(f"BE_B6_MARKER_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
          f"cases={total} failed={failed}")
    return 0 if not failed else 1


def number(value):
    return int(value, 0)


def options_pins(args, parser):
    """The pins from --pins, the three options, or the default file."""
    given = (args.kernel_bytes, args.image_size, args.banner)
    if any(value is not None for value in given):
        if None in given or args.pins:
            parser.error("give --kernel-bytes, --image-size, and --banner "
                         "together, without --pins")
        return checked_pins(Pins(*given), "the options")
    path = pathlib.Path(args.pins) if args.pins else DEFAULT_PINS
    if args.pins or path.exists():
        return read_pins(path)
    return None


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--capture")
    parser.add_argument("--expect-fail", choices=CLASSES, metavar="CLASS")
    parser.add_argument("--after", choices=LINE_IDS)
    parser.add_argument("--cause", type=number)
    parser.add_argument("--fault-above-window", action="store_true")
    parser.add_argument("--sbi-time", action="store_true")
    parser.add_argument("--pins")
    parser.add_argument("--kernel-bytes", type=number)
    parser.add_argument("--image-size", type=number)
    parser.add_argument("--banner")
    parser.add_argument("--toolchain", choices=("gcc", "clang"))
    parser.add_argument("--json")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check-sources", metavar="REPO_ROOT")
    parser.add_argument("--require-runtime", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.check_sources:
        return check_sources(args.check_sources, args.require_runtime)
    if args.capture is None:
        parser.error("--capture FILE is required")
    try:
        pins = options_pins(args, parser)
    except (OSError, ValueError) as error:
        parser.error(f"pins: {error}")
    with open(args.capture, "rb") as handle:
        text = handle.read().decode("utf-8", errors="replace")
    markers = extract(text)
    ok, findings = evaluate(text, args.expect_fail, pins, args.sbi_time,
                            args.after, args.cause, args.fault_above_window)
    expect = f"fail:{args.expect_fail}" if args.expect_fail else "pass"
    record = result_record(args.capture, expect, markers, ok, findings,
                           args.toolchain, pins, args.sbi_time)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
    for line in markers:
        print(line)
    for finding in findings:
        print(f"finding: {finding}")
    report = exits_report(markers)
    if report:
        print(report)
    if not args.expect_fail:
        print(f"BE_B6_MARKER_RESULT: {record['boot_marker']} "
              f"terminal={record['terminal']}")
    print(f"BE_B6_MARKERS[{args.toolchain or '-'}/{expect}]: "
          f"{record['result']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
