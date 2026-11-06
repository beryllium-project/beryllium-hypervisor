#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# A copy of B6's tests/check-b6-markers.py (accepted at e20c55df) with the
# counted changes listed in bringup/k3-b7/README.md.
"""Validate B7 console markers from a QEMU or K3 serial capture.

B7 enters through B3's shim (one `BE_K3_B3: SHIM` line), runs the accepted
R3 boot through BE_R3:06, builds and installs both guests' G-stage roots,
arms the shared guest controls and the scheduler (BE_B7:01-07), and enters
G0 (BE_B7:08 guest=0). Two unmodified uniprocessor Linux guests then share
hart 0: the monitor writes each guest's whole console lines with its
prefix (`BE_B7_G0: ` or `BE_B7_G1: `), enters G1 at the first switch
(BE_B7:08 guest=1), prints BE_B7:09 after each guest's SRST shutdown, and
ends with BE_B7:10-11. The expected lines are the Markers section of the
accepted plan planning/k3-b7-plan.md (026974fb); the R3 lines are the
marker literals of accepted R5 arch/riscv/be/r5-runtime.c (165f4d00), of
which B7 drops BE_R3:07. Every address and size comes from
bringup/k3-b7/src/b7-layout.h.

  check-b7-markers.py --capture FILE [--expect-fail CLASS] [--after LINE]
                      [--guest G] [--cause N] [--tval-not-wfi]
                      [--sbi-time] [--pins FILE | --kernel-bytes N
                       --image-size S --banner TEXT]
                      [--toolchain gcc|clang] [--json F]
  check-b7-markers.py --self-test
  check-b7-markers.py --check-sources REPO_ROOT [--require-runtime]

Marker lines run from a tag (BE_K3_B3:, BE_R3:, BE_R4:, BE_R5:, BE_B6:,
BE_B7:, `BE_B7_G0: `, or `BE_B7_G1: `) to the end of the line; trailing
CRs are dropped. Only loader output may precede the first marker line,
which must be B3's SHIM line: hart 0, shim at the staging address L, dest
the monitor image, and bytes its size. From there to the end of the
capture every non-blank line must be a marker line that starts with its
tag and is printable ASCII (0x20-0x7e); a guest line must hold no tag
after its prefix, no `B7INIT` and no kernel timestamp after its start (a
mixed line), and at most 256 bytes after its prefix (the monitor's line
buffer); and no untagged line may hold an init (`B7INIT NN `) line.

Without --expect-fail, the capture must pass: the SHIM line, BE_R3:01-06,
BE_B7:01-08 in the plan's order (G0's entry last), then the guest run, then
BE_B7:10, BE_B7:11, and nothing after it. In the guest run only guest
lines and three monitor lines may appear: BE_B7:08 guest=1 once, before
any G1 line, and BE_B7:09 once per guest, after that guest's last line.
Each guest's lines must hold the plan's required kernel, init, and
power-down lines in order, with its own ID (`be.guest=<g>` and `guest=<g>`
equal to its prefix), the eight `03 STEP` lines n=1/8 to n=8/8 with t_ms
rising, each init line once and no other init line, and no rejected
pattern (`panic` only inside the pinned `Kernel command line` line). <K>,
<S>, and <banner> come from the guest pins (default
bringup/k3-b7/guest/pins.txt, or the options); <T> and <h> are hex, <N>,
<r>, and <t> decimal, <e> 1000-1999, <m> at most the window in KiB.
BE_B7:04's hedeleg is a WARL reading of 0xb15d (holding 0xb10c).

Interleaving (Q5): at least 8 alternations between consecutive guest lines
(monitor lines ignored); a G1 `03 STEP` line between G0's first and last
`03 STEP` lines, and a G0 one within G1's; and wfi_switches and
slice_switches each at least 1. Counters: per guest, exits = sbi + wfi +
slice, at most the exit ceiling, sbi = base + time + dbcn_write +
dbcn_read + dbcn_byte + srst + refused, srst=1, refused=0, dbcn_byte=0,
time=0 (--sbi-time: above 0 for each guest, and the Sstc riscv-timer line
refused); switches = wfi_switches + slice_switches + stop_switches,
stop_switches=1, wfi_switches + slice_switches at most the guests' wfi and
slice exits, idle_ticks at most ticks, each guest's ticks at most the
run's, and the run's at most the time budget.

--expect-fail CLASS requires exactly one `BE_B7:FAIL CLASS`, CLASS one of
the plan's 20 classes, after the SHIM line. The lines before it must be a
prefix of the pass order; guest lines may appear only in the guest run
and are not otherwise fixed (a failing guest may panic). An exit failure
(interrupt, guest-page-fault, virtual-instruction, access-fault,
illegal-instruction, exit-budget, guest-timeout, guest-reboot,
guest-failure, scheduler) needs the exit `BE_B7:DETAIL guest=<g> ...` line
next, naming an entered guest, with a cause that fits the class (an
interrupt other than the supervisor timer; cause 22 but not a VS wfi);
exception may have it; switch needs `BE_B7:DETAIL switch guest=<g>
register=<name> wanted=0x.. readback=0x..` with two different values; a
controls failure after arming may carry the two `BE_B7:DETAIL controls`
readback lines; boot, gstage, sstc, payload, resume, console, and
shutdown-returned take no DETAIL line. At most `BE_B7:SRST_RETURNED` may
follow. --after LINE names the last fixed line before the failure (`none`
for none; `BE_B7:08` for G0's entry, so any failure in the guest run;
`BE_B7:01/g1` and so on for the per-guest lines); --guest G, --cause N,
and --tval-not-wfi (tval not 0x10500073) check the DETAIL line.

--check-sources reads accepted r5-runtime.c, the accepted B7 plan, the
accepted B6 plan (the classes, rejected patterns, DETAIL format, SHIM
values, and machines and CPUs B7 takes from it), and accepted B5
tests/run-qemu.sh (the R5 CPU) with `git -C REPO_ROOT show COMMIT:PATH`,
each SHA-256 pinned, and requires the R3 literals, both Markers blocks, the
guest-run lines, the classes, K, the terminal regex, the rejected
patterns, the DETAIL format, the SHIM values, the QEMU scenarios and
variants, and the scenario flags to match this checker and the B7 run
tools. When bringup/k3-b7/src/b7-runtime.c is present it must hold every
BE_R3 line, the fixed text and field names of every BE_B7 line, and the
failure literals, and bringup/k3-b7/src/ must name both guest tags and
every class and no numbered marker outside the plan; when it is absent the
check says so and skips it (--require-runtime makes that a finding). When
bringup/k3-b7/guest/b7-init.c is present, its literals must hold the fixed
text of every init line and no tag.

The JSON keeps B6's record (result, boot_marker, terminal, findings,
fields, markers) for bringup/k3-b0/tests/summarize-runs.py; fields holds
the SHIM values (hart, base, fdt, dest, bytes), each BE_B7 marker's
arguments (per guest where the line names one), each guest's exits and
elapsed_ms, the switch counts, the alternations, and any failure, detail,
and srst_returned.
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
B7_DIR = HERE.parent
LAYOUT_HEADER = B7_DIR / "src" / "b7-layout.h"
DEFAULT_PINS = B7_DIR / "guest" / "pins.txt"
LAYOUT_DEFINE = re.compile(r"^#define[ \t]+BE_B7_([A-Z0-9_]+)[ \t]+"
                           r"BE_B7_C\(([0-9a-fA-Fx]+)\)[ \t]*$", re.M)
LAYOUT_NAMES = ("MONITOR_HPA", "MONITOR_BYTES", "POOL_HPA", "GUESTS",
                "G0_ROOT_HPA", "G1_ROOT_HPA", "G0_HGATP", "G1_HGATP",
                "STAGING_HPA", "GUEST_GPA", "G0_HPA", "G1_HPA",
                "GUEST_BYTES", "GUEST_LEAVES", "KERNEL_GPA",
                "KERNEL_TEXT_OFFSET", "KERNEL_FILE_MAX",
                "KERNEL_IMAGE_SIZE_MAX", "DTB_GPA", "DTB_BYTES", "GUEST_HART",
                "SLICE_TICKS", "EXIT_CEILING", "GUEST_TIME_BUDGET",
                "SBI_IMPL_ID", "SBI_IMPL_VERSION")


def parse_layout(text, source, names=LAYOUT_NAMES):
    """{NAME: value} for every `#define BE_B7_NAME BE_B7_C(literal)`."""
    layout = {}
    for name, literal in LAYOUT_DEFINE.findall(text):
        if name in layout:
            raise ValueError(f"{source}: BE_B7_{name} is defined twice")
        layout[name] = int(literal, 0)
    missing = [name for name in names if name not in layout]
    if missing:
        raise ValueError(f"{source}: no BE_B7_C value for "
                         f"{', '.join('BE_B7_' + name for name in missing)}")
    return layout


def read_layout(path=LAYOUT_HEADER):
    return parse_layout(pathlib.Path(path).read_text(encoding="utf-8"), path)


LAYOUT = read_layout()
# The accepted R3 boot contract admits only hart 0.
BOOT_HART = 0
GUESTS = (0, 1)
if LAYOUT["GUESTS"] != len(GUESTS):
    raise ValueError(f"{LAYOUT_HEADER}: BE_B7_GUESTS is not 2")
WINDOWS = (LAYOUT["G0_HPA"], LAYOUT["G1_HPA"])
ROOTS = (LAYOUT["G0_ROOT_HPA"], LAYOUT["G1_ROOT_HPA"])
HGATPS = (LAYOUT["G0_HGATP"], LAYOUT["G1_HGATP"])
SHIM_TAG = "BE_K3_B3:"
GUEST_PREFIXES = ("BE_B7_G0: ", "BE_B7_G1: ")
TAGS = (SHIM_TAG, "BE_R3:", "BE_R4:", "BE_R5:", "BE_B6:", "BE_B6_GUEST: ",
        "BE_B7:") + GUEST_PREFIXES
# Tags guest output must never hold after its prefix.
GUEST_FORBIDDEN = TAGS
# The monitor's per-guest line buffer (plan, Markers: Console).
LINE_BYTES_MAX = 256
SHIM = re.compile(r"BE_K3_B3: SHIM hart=0x([0-9a-f]{16}) shim=0x([0-9a-f]{16})"
                  r" fdt=0x([0-9a-f]{16}) dest=0x([0-9a-f]{16}) "
                  r"bytes=0x([0-9a-f]{16})")
# The SHIM values B6's plan fixes and B7's keeps: L, the monitor, its size.
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
# The accepted R3 line B7 drops: no management entry happens.
R3_DROPPED = "BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000"
# The guest controls the monitor arms and reads back (plan, Guest
# controls): henvcfg.STCE; hstatus SPV, SPVP, and VTW; B6's hedeleg (WARL);
# VSTI; TM; sie.STIE; FS and VS Off; vstimecmp ~0.
HENVCFG = 1 << 63
HSTATUS_CONTROLS = 0x200180
HEDELEG = 0xb15d
# The readback may lack causes 0, 4, and 6 (B6's fix-warl direction); these
# causes must stick.
HEDELEG_REQUIRED = 0xb10c
HIDELEG = 0x40
HCOUNTEREN = 0x2
SIE = 0x20
VSTIMECMP_ARMED = (1 << 64) - 1
WFI = 0x10500073
INTERRUPT = 1 << 63
SUPERVISOR_TIMER = INTERRUPT | 5


def window_line(guest):
    return (f"gpa=0x{LAYOUT['GUEST_GPA']:x} hpa=0x{WINDOWS[guest]:x} "
            f"size=0x{LAYOUT['GUEST_BYTES']:x} "
            f"leaves={LAYOUT['GUEST_LEAVES']} root=0x{ROOTS[guest]:x}")


def entry_line(guest):
    return (f"BE_B7:08 ENTER_GUEST guest={guest} "
            f"pc=0x{LAYOUT['KERNEL_GPA']:x} a0=0x{LAYOUT['GUEST_HART']:x} "
            f"a1=0x{LAYOUT['DTB_GPA']:x}")


# The fixed lines before the guest run, in order (the plan's first block).
PRE_RUN = (
    f"BE_B7:01 GSTAGE_BUILT_REWALKED guest=0 {window_line(0)}",
    f"BE_B7:01 GSTAGE_BUILT_REWALKED guest=1 {window_line(1)}",
    f"BE_B7:02 HGATP_INSTALLED g1=0x{HGATPS[1]:x} g0=0x{HGATPS[0]:x}",
    f"BE_B7:03 SSTC_STCE_READBACK henvcfg=0x{HENVCFG:x}",
    f"BE_B7:04 GUEST_CONTROLS_CHECKED hstatus_controls=0x"
    f"{HSTATUS_CONTROLS:x} hedeleg=<h> hideleg=0x{HIDELEG:x} "
    f"hcounteren=0x{HCOUNTEREN:x} sie=0x{SIE:x} fs=0x0 vs=0x0 "
    f"vstimecmp=0x{VSTIMECMP_ARMED:x}",
) + tuple(
    f"BE_B7:05 GUEST_RAM_CLEARED guest={guest} "
    f"gpa=0x{LAYOUT['GUEST_GPA']:x} size=0x{LAYOUT['GUEST_BYTES']:x} "
    f"ticks=<T>" for guest in GUESTS) + tuple(
    f"BE_B7:06 PAYLOAD_PLACED guest={guest} "
    f"kernel=0x{LAYOUT['KERNEL_GPA']:x} kernel_bytes=<K> image_size=<S> "
    f"dtb=0x{LAYOUT['DTB_GPA']:x} dtb_bytes=0x{LAYOUT['DTB_BYTES']:x} "
    f"ticks=<T>" for guest in GUESTS) + (
    f"BE_B7:07 SCHEDULER_ARMED guests={len(GUESTS)} "
    f"slice_ticks=0x{LAYOUT['SLICE_TICKS']:x} first=0",
    entry_line(0),
)
# The guest run's monitor lines (plan, Markers, the paragraph after the
# first block): G1's entry, and each guest's shutdown.
ENTER_G1 = entry_line(1)
COUNTERS = ("exits", "sbi", "wfi", "slice", "base", "time", "dbcn_write",
            "dbcn_read", "dbcn_byte", "srst", "refused")
SBI_CLASSES = COUNTERS[4:]
SHUTDOWN_TEXT = "BE_B7:09 GUEST_SHUTDOWN guest="
GUEST_SHUTDOWN = (f"{SHUTDOWN_TEXT}<g> exits=<N> sbi=<N> wfi=<N> "
                  f"slice=<N> base=<N> time=0 dbcn_write=<N> dbcn_read=<N> "
                  f"dbcn_byte=0 srst=1 refused=0 ticks=<T>")
RUN_FIELDS = ("switches", "wfi_switches", "slice_switches", "stop_switches",
              "idle_waits", "idle_ticks", "ticks")
RUN_COMPLETE = ("BE_B7:10 RUN_COMPLETE switches=<N> wfi_switches=<N> "
                "slice_switches=<N> stop_switches=1 idle_waits=<N> "
                "idle_ticks=<T> ticks=<T>")
SHUTDOWN = "BE_B7:11 SHUTDOWN type=0 reason=0"
POST_RUN = (RUN_COMPLETE, SHUTDOWN)
# Every fixed BE_R3/BE_B7 line in pass order; the guest run lies between
# FIXED[RUN_AT - 1] (G0's entry) and FIXED[RUN_AT] (BE_B7:10).
FIXED = R3_SEQUENCE + PRE_RUN + POST_RUN
RUN_AT = len(R3_SEQUENCE) + len(PRE_RUN)
MONITOR_TEMPLATE = FIXED


def slot_id(line):
    """A fixed line's ID: its tag, and /g<guest> for the per-guest pairs."""
    tag = line.split(" ", 1)[0]
    guest = re.search(r" guest=([01]) ", line)
    if tag in ("BE_B7:01", "BE_B7:05", "BE_B7:06") and guest:
        return f"{tag}/g{guest.group(1)}"
    return tag


LINE_IDS = ("none",) + tuple(slot_id(line) for line in FIXED)
if len(set(LINE_IDS)) != len(LINE_IDS):
    raise ValueError("the fixed lines' IDs are not unique")
RELEASE = "7.2.0"
COMMAND_LINE = "earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1"
TIMESTAMP = "[<s>] "
STEPS = 8
# The required kernel lines (printk), the init's lines, and the power-down,
# as the plan's second block gives them.
KERNEL_LINES = (
    f"Linux version {RELEASE} <banner>",
    f"SBI implementation ID=0x{LAYOUT['SBI_IMPL_ID']:x} "
    f"Version=0x{LAYOUT['SBI_IMPL_VERSION']:x}",
    f"Kernel command line: {COMMAND_LINE} -- be.guest=<g>",
    "riscv-timer: Timer interrupt in S-mode is available via sstc extension",
    f"Memory: <m>K/{LAYOUT['GUEST_BYTES'] // 1024}K available <rest>",
    "Run /init as init process",
)
INIT_LINES = (
    "B7INIT 01 START guest=<g> pid=1",
    f"B7INIT 02 UNAME release={RELEASE} machine=riscv64",
    f"B7INIT 03 STEP n=<i>/{STEPS} rounds=<r> t_ms=<t>",
    "B7INIT 04 SLEEP requested_ms=1000 elapsed_ms=<e> ok=1",
    "B7INIT 05 RESULT pass",
    "B7INIT 06 POWER_OFF",
)
POWER_DOWN = "reboot: Power down"
GUEST_TEMPLATE = tuple(TIMESTAMP + line for line in KERNEL_LINES) + \
    INIT_LINES + (TIMESTAMP + POWER_DOWN,)
COMMAND_LINE_AT = 2
SSTC_AT = 3
MEMORY_AT = 4
STEP_AT = len(KERNEL_LINES) + 2
STEP = re.compile(rf"B7INIT 03 STEP n=([1-{STEPS}])/{STEPS} "
                  r"rounds=([1-9][0-9]*) t_ms=(0|[1-9][0-9]*)")
# Where a guest names its ID (each must equal its prefix's).
ID_PATTERNS = (re.compile(r"\] Kernel command line: .* be\.guest=(\S*)"),
               re.compile(r"^B7INIT 01 START guest=(\S*)"))


def guest_template(guest):
    """GUEST_TEMPLATE for GUEST: <g> filled, the STEP line once per step."""
    lines = []
    for line in GUEST_TEMPLATE:
        line = line.replace("<g>", str(guest))
        if "<i>" in line:
            lines += [line.replace("<i>", str(step))
                      for step in range(1, STEPS + 1)]
        else:
            lines.append(line)
    return tuple(lines)


HEX = r"0x(?:0|[1-9a-f][0-9a-f]{0,15})"
DEC = r"(?:0|[1-9][0-9]*)"
HEDELEG_FIELD = re.compile(rf"(?<= hedeleg=)({HEX})(?= )")
STAMP = r"\[ *[0-9]+\.[0-9]{6}\]"
STAMP_RE = re.compile(STAMP)
# Placeholder -> pattern; <K>, <S>, and <banner> come from the pins, <g>
# and <i> from the guest and step.
PLACEHOLDERS = {
    "<T>": HEX,
    "<h>": HEX,
    "<N>": DEC,
    "[<s>]": STAMP,
    "<m>": r"[1-9][0-9]*",
    "<rest>": r"\S.*",
    "<e>": r"1[0-9]{3}",
    "<r>": r"[1-9][0-9]*",
    "<t>": DEC,
    "<g>": r"[01]",
    "<i>": rf"[1-{STEPS}]",
}
PLACEHOLDER = re.compile(r"\[<s>\]|<[A-Za-z]+>")
GUEST_SHUTDOWN_RE = re.compile(
    re.escape(SHUTDOWN_TEXT) + "([01]) " + " ".join(
        [f"{name}=({DEC})" for name in COUNTERS] + [f"ticks=({HEX})"]))
RUN_COMPLETE_RE = re.compile(
    "BE_B7:10 RUN_COMPLETE " + " ".join(
        [f"{name}=({DEC})" for name in RUN_FIELDS[:5]] +
        [f"{name}=({HEX})" for name in RUN_FIELDS[5:]]))
# At least K alternations between consecutive guest lines (Q5).
ALTERNATIONS_MIN = 8
FAIL_PREFIX = "BE_B7:FAIL "
DETAIL_PREFIX = "BE_B7:DETAIL "
SRST_RETURNED = "BE_B7:SRST_RETURNED"
# B6's exit DETAIL with the guest first (plan, Markers: Failures).
DETAIL_FIELDS = ("guest", "cause", "pc", "tval", "htval", "htinst", "spvp",
                 "vsatp", "exits")
DETAIL_TEMPLATE = ("BE_B7:DETAIL guest=<g> cause=0x\u2026 pc=0x\u2026 "
                   "tval=0x\u2026 htval=0x\u2026 htinst=0x\u2026 spvp=<0|1> "
                   "vsatp=0x\u2026 exits=<N>")
# The accepted B6 DETAIL line, which B7's extends with guest=<g>.
B6_DETAIL_TEMPLATE = ("BE_B6:DETAIL cause=0x\u2026 pc=0x\u2026 tval=0x\u2026 "
                      "htval=0x\u2026 htinst=0x\u2026 spvp=<0|1> "
                      "vsatp=0x\u2026 exits=<N>")
DETAIL = re.compile(rf"BE_B7:DETAIL guest=([01]) cause=({HEX}) pc=({HEX}) "
                    rf"tval=({HEX}) htval=({HEX}) htinst=({HEX}) "
                    rf"spvp=([01]) vsatp=({HEX}) exits=({DEC})")
# A switch readback mismatch names the guest switched to and the register.
SWITCH_DETAIL_PREFIX = "BE_B7:DETAIL switch "
SWITCH_REGISTERS = ("hgatp", "vsstatus", "vsie", "vstvec", "vsscratch",
                    "vsepc", "vscause", "vstval", "vsatp", "vstimecmp",
                    "scounteren", "senvcfg")
SWITCH_DETAIL = re.compile(
    rf"BE_B7:DETAIL switch guest=([01]) "
    rf"register=({'|'.join(SWITCH_REGISTERS)}) wanted=({HEX}) "
    rf"readback=({HEX})")
# After a controls failure, every guest-control readback in two lines.
CONTROLS_DETAIL_PREFIX = "BE_B7:DETAIL controls "
CONTROLS_DETAIL_FIELDS = (
    ("hip", "hstatus", "hedeleg", "hideleg", "hie", "hvip", "hcounteren",
     "htimedelta"),
    ("henvcfg", "hgeie", "vstimecmp", "sie", "sstatus", "hgatp", "vsatp",
     "sscratch"))
CONTROLS_DETAIL = tuple(
    re.compile(CONTROLS_DETAIL_PREFIX + " ".join(f"{name}=({HEX})"
                                                  for name in names))
    for names in CONTROLS_DETAIL_FIELDS)
# B6's 18 classes (accepted B6 plan), then the two B7 adds.
B6_CLASSES = ("boot", "gstage", "sstc", "controls", "payload", "interrupt",
              "guest-page-fault", "virtual-instruction", "access-fault",
              "illegal-instruction", "exception", "exit-budget",
              "guest-timeout", "resume", "console", "guest-failure",
              "guest-reboot", "shutdown-returned")
CLASSES = B6_CLASSES + ("switch", "scheduler")
# A failure decided on a guest exit names the guest and its exit; an
# exception may come from a bad trusted stack, with no exit to name.
DETAIL_REQUIRED = ("interrupt", "guest-page-fault", "virtual-instruction",
                   "access-fault", "illegal-instruction", "exit-budget",
                   "guest-timeout", "guest-reboot", "guest-failure",
                   "scheduler")
DETAIL_OPTIONAL = ("exception",)
TERMINAL_REGEX = "BE_B7:11 SHUTDOWN|BE_B7:FAIL|BE_K3_B3: FAIL"
# B6's rejected patterns (accepted B6 plan), case-sensitive, in any guest
# line.
REJECTED = ("panic", "Oops", "WARN", "BUG:", "kernel BUG",
            "Attempted to kill init", "cut here", "Call Trace:",
            "Unable to handle kernel", "rcu: INFO:", "soft lockup",
            "blocked for more than", "segfault", "unhandled signal",
            "extension is not available in SBI", "sbi_srst_reset",
            "No working init found", "Failed to execute", "Out of memory",
            "RESULT fail")
UNPREFIXED_INIT = re.compile(r"B7INIT [0-9]{2} ")
# Argument-bearing marker -> JSON field holding its arguments (per guest
# where the line names one).
FIELD_PREFIXES = (
    ("BE_B7:01 ", "gstage"),
    ("BE_B7:02 ", "hgatp"),
    ("BE_B7:03 ", "sstc_readback"),
    ("BE_B7:04 ", "guest_controls"),
    ("BE_B7:05 ", "guest_ram"),
    ("BE_B7:06 ", "payload"),
    ("BE_B7:07 ", "scheduler"),
    ("BE_B7:08 ", "guest_entry"),
    ("BE_B7:09 ", "guest_shutdown"),
    ("BE_B7:10 ", "run_complete"),
    ("BE_B7:11 ", "shutdown"),
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


def guest_of(line):
    """0 or 1 for a guest line, by its prefix; None for any other line."""
    for guest, prefix in enumerate(GUEST_PREFIXES):
        if line.startswith(prefix):
            return guest
    return None


def mixed(body):
    """Why a guest line's text mixes two lines, or None: an init line or a
    kernel timestamp after its start."""
    if body.find("B7INIT", 1) >= 0:
        return "an init line inside it"
    if STAMP_RE.search(body, 1):
        return "a kernel timestamp inside it"
    return None


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
                problems.append(f"line {number}: init line without a guest "
                                f"prefix: {line[:80]!r}")
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
        guest = guest_of(marker)
        if guest is None:
            continue
        body = marker[len(GUEST_PREFIXES[guest]):]
        forged = [tag for tag in GUEST_FORBIDDEN if tag in body]
        if forged:
            problems.append(f"line {number}: guest output holds "
                            f"{forged[0]!r}: {marker[:80]!r}")
        why = mixed(body)
        if why:
            problems.append(f"line {number}: mixed guest line, {why}: "
                            f"{marker[:80]!r}")
        if len(body) > LINE_BYTES_MAX:
            problems.append(f"line {number}: guest line of {len(body)} "
                            f"bytes, above the {LINE_BYTES_MAX}-byte line "
                            f"buffer: {marker[:80]!r}")
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


def shutdown_counters(line, sbi_time=False):
    """(counters, findings) for a BE_B7:09 line; counters holds the guest,
    the eleven counters, and ticks."""
    match = GUEST_SHUTDOWN_RE.fullmatch(line)
    if not match:
        return None, [f"malformed BE_B7:09 line {line!r}"]
    values = match.groups()
    counters = {"guest": int(values[0])}
    counters.update(zip(COUNTERS, (int(value) for value in values[1:-1])))
    counters["ticks"] = int(values[-1], 16)
    guest = counters["guest"]
    findings = []
    total = counters["sbi"] + counters["wfi"] + counters["slice"]
    if counters["exits"] != total:
        findings.append(f"G{guest}: exits={counters['exits']} is not sbi + "
                        f"wfi + slice = {total}")
    calls = sum(counters[name] for name in SBI_CLASSES)
    if counters["sbi"] != calls:
        findings.append(f"G{guest}: sbi={counters['sbi']} is not the sum "
                        f"{calls} of the call classes")
    if not 1 <= counters["exits"] <= LAYOUT["EXIT_CEILING"]:
        findings.append(f"G{guest}: exits={counters['exits']} is outside 1-"
                        f"{LAYOUT['EXIT_CEILING']}")
    for name, wanted in (("srst", 1), ("refused", 0), ("dbcn_byte", 0)):
        if counters[name] != wanted:
            findings.append(f"G{guest}: {name}={counters[name]}, expected "
                            f"{wanted}")
    if sbi_time and counters["time"] == 0:
        findings.append(f"G{guest}: time=0, but the sbi-time guests must use "
                        f"SBI TIME")
    if not sbi_time and counters["time"] != 0:
        findings.append(f"G{guest}: time={counters['time']}, but the guest "
                        f"must use its own Sstc timer")
    if counters["ticks"] > LAYOUT["GUEST_TIME_BUDGET"]:
        findings.append(f"G{guest}: ticks=0x{counters['ticks']:x} is above "
                        f"the time budget 0x"
                        f"{LAYOUT['GUEST_TIME_BUDGET']:x}")
    return counters, findings


def run_counters(line):
    """(counters, findings) for a BE_B7:10 line."""
    match = RUN_COMPLETE_RE.fullmatch(line)
    if not match:
        return None, [f"{line!r} is not {RUN_COMPLETE!r}"]
    values = match.groups()
    counters = dict(zip(RUN_FIELDS[:5], (int(value) for value in
                                          values[:5])))
    counters.update(zip(RUN_FIELDS[5:], (int(value, 16) for value in
                                          values[5:])))
    findings = []
    total = counters["wfi_switches"] + counters["slice_switches"] + \
        counters["stop_switches"]
    if counters["switches"] != total:
        findings.append(f"switches={counters['switches']} is not "
                        f"wfi_switches + slice_switches + stop_switches = "
                        f"{total}")
    if counters["stop_switches"] != 1:
        findings.append(f"stop_switches={counters['stop_switches']}, "
                        f"expected 1")
    if counters["idle_ticks"] > counters["ticks"]:
        findings.append(f"idle_ticks=0x{counters['idle_ticks']:x} is above "
                        f"ticks=0x{counters['ticks']:x}")
    if counters["ticks"] > LAYOUT["GUEST_TIME_BUDGET"]:
        findings.append(f"ticks=0x{counters['ticks']:x} is above the time "
                        f"budget 0x{LAYOUT['GUEST_TIME_BUDGET']:x}")
    return counters, findings


def hedeleg_ok(value):
    """Whether a hedeleg readback is a WARL reading of HEDELEG."""
    return value & ~HEDELEG == 0 and \
        value & HEDELEG_REQUIRED == HEDELEG_REQUIRED


def monitor_findings(line, slot, pins):
    """Findings when LINE is not FIXED[slot] (placeholders filled)."""
    wanted = FIXED[slot]
    if wanted == RUN_COMPLETE:
        return run_counters(line)[1]
    if not template_pattern(wanted, pins).fullmatch(line):
        return [f"{line!r} is not {wanted!r}"]
    if pins is None and uses_pins(wanted):
        return [f"{line!r} needs the kernel pins (guest/pins.txt, or "
                f"--kernel-bytes, --image-size, and --banner)"]
    match = HEDELEG_FIELD.search(line) if line.startswith("BE_B7:04 ") \
        else None
    if match and not hedeleg_ok(int(match.group(1), 16)):
        return [f"hedeleg={match.group(1)} in {line!r} is not a WARL "
                f"reading of 0x{HEDELEG:x} holding 0x{HEDELEG_REQUIRED:x}"]
    return []


class Walk:
    """The pass order followed through a capture's markers after the SHIM
    line: slot counts the FIXED lines matched; guest holds each guest's
    (marker number, body) lines; order the guest of each guest line;
    entered and stopped the guest-run state; run the BE_B7:10 counters."""

    def __init__(self):
        self.slot = 0
        self.findings = []
        self.guest = ([], [])
        self.order = []
        self.entered = [False, False]
        self.stopped = [None, None]
        self.run = None

    @property
    def reached(self):
        return LINE_IDS[self.slot]


def walk(lines, pins=None, sbi_time=False, first=2):
    """Follow the pass order through LINES. Guest lines may appear only in
    the guest run, G1's only after BE_B7:08 guest=1 and each guest's only
    before its BE_B7:09; the run's other lines are G1's entry and the two
    shutdowns. Findings number the marker lines from FIRST (the SHIM line
    is marker 1); a structural finding ends the walk."""
    state = Walk()
    for index, line in enumerate(lines, first):
        where = f"marker {index}"
        guest = guest_of(line)
        if guest is not None:
            if state.slot != RUN_AT:
                state.findings.append(f"{where}: guest line {line[:80]!r} "
                                      f"is outside the guest run")
                break
            if not state.entered[guest]:
                state.findings.append(f"{where}: G{guest} line before "
                                      f"{entry_line(guest)!r}")
                break
            if state.stopped[guest] is not None:
                state.findings.append(f"{where}: G{guest} line after its "
                                      f"BE_B7:09: {line[:80]!r}")
                break
            state.guest[guest].append(
                (index, line[len(GUEST_PREFIXES[guest]):]))
            state.order.append(guest)
            continue
        if state.slot == RUN_AT and not line.startswith("BE_B7:10 "):
            if line == ENTER_G1 and not state.entered[1]:
                state.entered[1] = True
                continue
            if line.startswith(SHUTDOWN_TEXT):
                counters, problems = shutdown_counters(line, sbi_time)
                if counters is None or not state.entered[
                        counters["guest"]] or \
                        state.stopped[counters["guest"]] is not None:
                    state.findings.append(
                        f"{where}: {line!r} is not one BE_B7:09 of an "
                        f"entered guest" if counters else
                        f"{where}: {problems[0]}")
                    break
                state.findings += [f"{where}: {problem}"
                                   for problem in problems]
                state.stopped[counters["guest"]] = counters
                continue
            state.findings.append(f"{where}: {line!r} is not a guest line, "
                                  f"{ENTER_G1!r} once, or one BE_B7:09 per "
                                  f"guest")
            break
        if state.slot == RUN_AT:
            missing = [guest for guest in GUESTS
                       if state.stopped[guest] is None]
            if missing:
                state.findings.append(
                    f"{where}: BE_B7:10 before "
                    f"{', '.join(f'G{guest}' for guest in missing)}'s "
                    f"BE_B7:09")
        if state.slot == len(FIXED):
            state.findings.append(f"{where}: {line!r} follows {SHUTDOWN!r}")
            break
        problems = monitor_findings(line, state.slot, pins)
        if problems:
            state.findings += [f"{where}: {problem}" for problem in problems]
            if not line.startswith(FIXED[state.slot].split(" ", 1)[0] + " "):
                break
        if state.slot == RUN_AT:
            state.run = run_counters(line)[0]
        state.slot += 1
        if state.slot == RUN_AT:
            state.entered[0] = True
    return state


def guest_findings(guest, entries, pins, sbi_time=False):
    """One guest's lines (bodies after its prefix): the required lines in
    order, its own ID wherever it names one, each init line once, no other
    init line, t_ms rising over the steps, no rejected pattern, and memory
    within the window. With sbi_time the Sstc timer line is not required
    but refused."""
    findings = []
    name = f"G{guest}"
    bodies = [body for _, body in entries]
    template = list(guest_template(guest))
    patterns = [template_pattern(line, pins) for line in template]
    command_line = patterns[COMMAND_LINE_AT]
    init_patterns = [pattern for line, pattern in zip(template, patterns)
                     if line.startswith("B7INIT ")]
    if sbi_time:
        sstc = patterns.pop(SSTC_AT)
        del template[SSTC_AT]
        findings += [f"the sbi-time {name} reported the Sstc timer: {body!r}"
                     for body in bodies if sstc.fullmatch(body)]
    position = 0
    for body in bodies:
        exempt = ("panic",) if command_line.fullmatch(body) else ()
        for pattern in REJECTED:
            if pattern in body and pattern not in exempt:
                findings.append(f"rejected {pattern!r} in {name} line "
                                f"{body!r}")
        if body.startswith("B7INIT ") and \
                not any(init.fullmatch(body) for init in init_patterns):
            findings.append(f"unexpected {name} init line {body!r}")
        for id_pattern in ID_PATTERNS:
            named = id_pattern.search(body)
            if named and named.group(1) != str(guest):
                findings.append(f"{name} line names guest "
                                f"{named.group(1)!r}: {body!r}")
        if position < len(patterns) and patterns[position].fullmatch(body):
            position += 1
    if position < len(patterns):
        findings.append(f"{name} lacks the required line "
                        f"{template[position]!r} (or a later one is out of "
                        f"order)")
    for line, init in zip([line for line in template
                           if line.startswith("B7INIT ")], init_patterns):
        count = sum(1 for body in bodies if init.fullmatch(body))
        if count > 1:
            findings.append(f"{name} init line {line!r} appears {count} "
                            f"times")
    times = [int(step.group(3)) for step in map(STEP.fullmatch, bodies)
             if step]
    if any(later <= earlier for earlier, later in zip(times, times[1:])):
        findings.append(f"{name} step times t_ms={times} do not rise")
    window_k = LAYOUT["GUEST_BYTES"] // 1024
    memory = template_pattern(GUEST_TEMPLATE[MEMORY_AT], pins)
    for body in bodies:
        if memory.fullmatch(body):
            available = int(re.search(r"Memory: ([0-9]+)K/", body).group(1))
            if available > window_k:
                findings.append(f"{name}: {available}K available exceeds "
                                f"the {window_k}K window: {body!r}")
    return findings


def alternations(order):
    """Guest lines followed by the other guest's next line."""
    return sum(1 for before, after in zip(order, order[1:])
               if before != after)


def interleave_findings(state):
    """The plan's interleaving floors (Q5) and the counters across lines."""
    findings = []
    count = alternations(state.order)
    if count < ALTERNATIONS_MIN:
        findings.append(f"{count} alternations between the guests' lines, "
                        f"fewer than {ALTERNATIONS_MIN}")
    steps = [[index for index, body in state.guest[guest]
              if STEP.fullmatch(body)] for guest in GUESTS]
    for guest in GUESTS:
        own, other = steps[guest], steps[1 - guest]
        if len(own) < 2 or not any(own[0] < index < own[-1]
                                   for index in other):
            findings.append(f"G{1 - guest} prints no 03 STEP line between "
                            f"G{guest}'s first and last 03 STEP lines")
    run = state.run
    if run is None:
        return findings
    for name in ("wfi_switches", "slice_switches"):
        if run[name] < 1:
            findings.append(f"{name}={run[name]}, expected at least 1")
    stopped = [counters for counters in state.stopped if counters]
    if len(stopped) == len(GUESTS):
        exits = sum(counters["wfi"] + counters["slice"]
                    for counters in stopped)
        if run["wfi_switches"] + run["slice_switches"] > exits:
            findings.append(f"wfi_switches + slice_switches = "
                            f"{run['wfi_switches'] + run['slice_switches']} "
                            f"is above the guests' {exits} wfi and slice "
                            f"exits")
        for counters in stopped:
            if counters["ticks"] > run["ticks"]:
                findings.append(f"G{counters['guest']}'s ticks=0x"
                                f"{counters['ticks']:x} is above the run's "
                                f"ticks=0x{run['ticks']:x}")
    return findings


def pass_findings(markers, pins=None, sbi_time=False):
    """Findings for a capture that must pass (its marker lines)."""
    findings, rest, _ = shim_findings(markers)
    failures = [line for line in rest if is_failure(line)]
    if failures:
        findings.append(f"failure lines in a pass capture: {failures[:3]}")
    state = walk(rest, pins, sbi_time, len(markers) - len(rest) + 1)
    findings += state.findings
    if state.reached != LINE_IDS[-1]:
        findings.append(f"the sequence stops after {state.reached}; missing "
                        f"{FIXED[state.slot]!r}")
    if not state.entered[1]:
        findings.append(f"no {ENTER_G1!r} line")
    for guest in GUESTS:
        findings += guest_findings(guest, state.guest[guest], pins, sbi_time)
    findings += interleave_findings(state)
    if pins is None:
        findings.append("no kernel pins: give guest/pins.txt, --pins, or "
                        "--kernel-bytes, --image-size, and --banner")
    return findings


def full_sequence_reached(markers, pins=None, sbi_time=False):
    """The pass sequence through BE_B7:11, and no failure line anywhere."""
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


def cause_finding(klass, detail):
    """A finding when an exit's cause does not fit its class."""
    cause = detail["cause"]
    wfi = cause == 22 and detail["tval"] == WFI and detail["spvp"] == 1
    fits = {
        "interrupt": bool(cause & INTERRUPT) and cause != SUPERVISOR_TIMER,
        "guest-page-fault": cause in (20, 21, 23),
        "virtual-instruction": cause == 22 and not wfi,
        "access-fault": cause in (1, 5, 7),
        "illegal-instruction": cause == 2,
        "exception": not cause & INTERRUPT and
        cause not in (1, 2, 5, 7, 10, 20, 21, 22, 23),
    }.get(klass, True)
    if not fits:
        why = " (a VS wfi is an idle exit)" if wfi else \
            " (the supervisor timer is the slice)" \
            if cause == SUPERVISOR_TIMER else ""
        return f"cause 0x{cause:x} does not fit class {klass}{why}"
    return None


def failure_findings(markers, klass, pins=None, after=None, guest=None,
                     cause=None, tval_not_wfi=False):
    if klass not in CLASSES:
        return [f"unknown failure class {klass!r}"]
    findings, rest, _ = shim_findings(markers)
    failures = [index for index, line in enumerate(rest)
                if line.startswith(FAIL_PREFIX)]
    if not failures:
        return findings + ["no BE_B7:FAIL line"]
    if len(failures) > 1:
        findings.append(f"{len(failures)} BE_B7:FAIL lines")
    first = failures[0]
    seen = rest[first][len(FAIL_PREFIX):]
    if seen != klass:
        findings.append(f"failure class {seen!r}, expected {klass!r}")
    state = walk(rest[:first], pins, first=len(markers) - len(rest) + 1)
    findings += state.findings
    if after is not None and state.reached != after:
        findings.append(f"the failure follows {state.reached}, expected "
                        f"{after}")
    tail = rest[first + 1:]
    if klass == "controls" and tail and \
            tail[0].startswith(CONTROLS_DETAIL_PREFIX):
        for pattern in CONTROLS_DETAIL:
            if not tail or not pattern.fullmatch(tail[0]):
                findings.append(f"malformed controls readback {tail[:1]}")
                break
            tail = tail[1:]
    named = None
    detail = None
    if klass == "switch":
        match = SWITCH_DETAIL.fullmatch(tail[0]) if tail else None
        if match:
            named = int(match.group(1))
            if match.group(3) == match.group(4):
                findings.append(f"switch DETAIL {tail[0]!r} reads back the "
                                f"wanted value")
            tail = tail[1:]
        else:
            findings.append(f"class switch needs a {SWITCH_DETAIL_PREFIX}"
                            f"line, not {tail[:1]}")
            if tail and tail[0].startswith(SWITCH_DETAIL_PREFIX):
                tail = tail[1:]
    elif tail and tail[0].startswith(DETAIL_PREFIX):
        match = DETAIL.fullmatch(tail[0])
        if match:
            detail = dict(zip(DETAIL_FIELDS,
                              (int(value, 0) for value in match.groups())))
            named = detail["guest"]
        else:
            findings.append(f"malformed detail {tail[0]!r}")
        if klass not in DETAIL_REQUIRED + DETAIL_OPTIONAL:
            findings.append(f"class {klass} takes no BE_B7:DETAIL line")
        tail = tail[1:]
    elif klass in DETAIL_REQUIRED:
        findings.append(f"class {klass} needs a BE_B7:DETAIL line")
    if tail[:1] == [SRST_RETURNED]:
        tail = tail[1:]
    if tail:
        findings.append(f"lines after the failure: {tail[:3]}")
    if detail:
        finding = cause_finding(klass, detail)
        if finding:
            findings.append(finding)
        if not state.entered[detail["guest"]]:
            findings.append(f"the DETAIL names G{detail['guest']}, which was "
                            f"never entered")
    if guest is not None and named is None:
        findings.append(f"no DETAIL names a guest to compare with {guest}")
    elif guest is not None and named != guest:
        findings.append(f"the DETAIL names guest {named}, expected {guest}")
    if cause is not None:
        if detail is None:
            findings.append(f"no detail cause to compare with 0x{cause:x}")
        elif detail["cause"] != cause:
            findings.append(f"cause 0x{detail['cause']:x}, expected "
                            f"0x{cause:x}")
    if tval_not_wfi:
        if detail is None:
            findings.append("no detail tval to compare with the wfi "
                            "encoding")
        elif detail["tval"] == WFI:
            findings.append(f"tval 0x{WFI:x} is the wfi encoding")
    return findings


def evaluate(text, expect_fail=None, pins=None, sbi_time=False, after=None,
             guest=None, cause=None, tval_not_wfi=False):
    """(ok, findings) for one capture's text."""
    markers, findings = scan(text)
    if expect_fail is None:
        if after is not None or guest is not None or cause is not None or \
                tval_not_wfi:
            findings.append("--after, --guest, --cause, and --tval-not-wfi "
                            "apply to --expect-fail only")
        findings += pass_findings(markers, pins, sbi_time)
    else:
        if sbi_time:
            findings.append("--sbi-time applies to a pass only")
        findings += failure_findings(markers, expect_fail, pins, after, guest,
                                     cause, tval_not_wfi)
    return not findings, findings


def parse_fields(markers):
    """The SHIM values, each BE_B7 marker's arguments, the counts, and the
    failure facts; every value a string."""
    fields = {}
    match = SHIM.fullmatch(markers[0]) if markers else None
    if match:
        fields.update(zip(("hart", "base", "fdt", "dest", "bytes"),
                          (f"0x{value}" for value in match.groups())))
    order = []
    for line in markers:
        guest = guest_of(line)
        if guest is not None:
            order.append(guest)
            body = line[len(GUEST_PREFIXES[guest]):]
            elapsed = re.fullmatch(r"B7INIT 04 SLEEP requested_ms=1000 "
                                   r"elapsed_ms=([0-9]+) ok=[01]", body)
            if elapsed and f"elapsed_ms_g{guest}" not in fields:
                fields[f"elapsed_ms_g{guest}"] = elapsed.group(1)
            continue
        parts = line.split(" ", 2)
        named = re.match(r"guest=([01]) ", parts[2] + " ") \
            if len(parts) == 3 else None
        for prefix, name in FIELD_PREFIXES:
            key = f"{name}_g{named.group(1)}" if named else name
            if line.startswith(prefix) and key not in fields and \
                    len(parts) == 3:
                fields[key] = parts[2]
        if line.startswith(FAIL_PREFIX) and "failure" not in fields:
            fields["failure"] = line[len(FAIL_PREFIX):]
        elif line.startswith(DETAIL_PREFIX) and "detail" not in fields:
            fields["detail"] = line[len(DETAIL_PREFIX):]
        elif line == SRST_RETURNED:
            fields["srst_returned"] = "yes"
        counters, _ = shutdown_counters(line) if \
            line.startswith(SHUTDOWN_TEXT) else (None, None)
        if counters and f"exits_g{counters['guest']}" not in fields:
            fields[f"exits_g{counters['guest']}"] = str(counters["exits"])
        run, _ = run_counters(line) if line.startswith("BE_B7:10 ") \
            else (None, None)
        if run:
            for name in ("switches", "wfi_switches", "slice_switches"):
                fields.setdefault(name, str(run[name]))
    if order:
        fields["alternations"] = str(alternations(order))
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


def counts_report(markers):
    """The line that prints a capture's guest and switch counters, or None
    when it holds neither guest's BE_B7:09 nor BE_B7:10."""
    words = []
    for guest in GUESTS:
        for line in markers:
            counters, _ = shutdown_counters(line) if \
                line.startswith(SHUTDOWN_TEXT) else (None, None)
            if counters and counters["guest"] == guest:
                words += [f"g{guest}_{name}={counters[name]}"
                          for name in COUNTERS[:4]]
                break
    for line in markers:
        run, _ = run_counters(line) if line.startswith("BE_B7:10 ") \
            else (None, None)
        if run:
            words += [f"{name}={run[name]}" for name in RUN_FIELDS[:5]]
            break
    if not words:
        return None
    order = [guest_of(line) for line in markers
             if guest_of(line) is not None]
    return "BE_B7_COUNTS: " + " ".join(words) + \
        f" alternations={alternations(order)}"


# Source checks: the accepted inputs, the B7 run tools, and the B7 sources.
ACCEPTED_R5 = "165f4d001a2b59b582b397bdea79ec4826168fdb"
R5_RUNTIME = "arch/riscv/be/r5-runtime.c"
R5_RUNTIME_SHA256 = \
    "a221ce8ebb77e3feaa9d7799e3eb296fb8cd7aa9190e20f1970d7e9c95bcc6e4"
ACCEPTED_PLAN = "026974fb619295482b93a7ae8cffdc4f552825ea"
PLAN = "planning/k3-b7-plan.md"
PLAN_SHA256 = \
    "0f55e3953628532fd1de58f307efa6c5d02a7b55c33cc8d321f75c64bdbd708b"
ACCEPTED_B6_PLAN = "e34ef378b6279300ba5f3aeb8b6102941b432454"
B6_PLAN = "planning/k3-b6-plan.md"
B6_PLAN_SHA256 = \
    "ac53bbfa6e8538c8ac0067fa2ec91dda3bbfd6bd1b72a18fcbac811fc91ada7a"
ACCEPTED_B5 = "829562395bf14fedbeea0beb82b30da15ec5f7cf"
B5_RUNNER = "bringup/k3-b5/tests/run-qemu.sh"
B5_RUNNER_SHA256 = \
    "bffc7b304367a69576acda37a93450dbfe8b480f05a0c2d4731fcd000670f811"
B7_RUNTIME = "bringup/k3-b7/src/b7-runtime.c"
B7_INIT = "bringup/k3-b7/guest/b7-init.c"
B7_SRC = "bringup/k3-b7/src"
RUN_TOOLS = (HERE / "run-qemu.sh", HERE / "kexec-rehearsal.sh",
             B7_DIR / "scripts" / "k3-run.sh")
ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'",
           "?": "?", "a": "\a", "b": "\b", "f": "\f", "v": "\v"}
# The plan sentences that make B6's values B7's.
PLAN_INHERITS = (
    "A passing capture holds B3's `SHIM` line (as in B6)",
    "**Rejected:** B6's rejected substrings in any guest line",
    "then a `DETAIL` line with `guest=<g>`",
    "**QEMU scenarios:** B6's machines and CPUs",
)
# The fixed text of every init line, as the init prints it (guest/b7-init.c).
INIT_TEXTS = ("B7INIT 01 START guest=", " pid=", "B7INIT 02 UNAME release=",
              " machine=", "B7INIT 03 STEP n=", " rounds=", " t_ms=",
              "B7INIT 04 SLEEP requested_ms=", " elapsed_ms=", " ok=",
              "B7INIT 05 RESULT ", "B7INIT 06 POWER_OFF")
# The monitor lines whose literals b7-runtime.c must hold.
RUNTIME_LINES = PRE_RUN + (ENTER_G1, GUEST_SHUTDOWN) + POST_RUN
FAILURE_TEXTS = (FAIL_PREFIX, "BE_B7:DETAIL guest=") + tuple(
    f" {name}=" for name in DETAIL_FIELDS[1:]) + (
    "BE_B7:DETAIL switch guest=", " register=", " wanted=", " readback=",
    CONTROLS_DETAIL_PREFIX + "hip=", CONTROLS_DETAIL_PREFIX + "henvcfg=",
    SRST_RETURNED)


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


def b7_source_findings(runtime, init, sources, require_runtime=False):
    """(findings, notes) for the B7 monitor and init sources (None when
    missing). sources holds every bringup/k3-b7/src/*.[ch] text."""
    findings = []
    notes = []
    if runtime is None and require_runtime:
        findings.append(f"{B7_RUNTIME} is missing (--require-runtime)")
    elif runtime is None:
        notes.append(f"{B7_RUNTIME} is missing, so the BE_B7 source check "
                     f"is skipped")
    else:
        required = R3_SEQUENCE + tuple(fixed_text(line)
                                       for line in RUNTIME_LINES)
        for line in RUNTIME_LINES:
            required += field_names(line)
        required += FAILURE_TEXTS
        findings += literal_findings("b7-runtime.c", c_literals(runtime),
                                     tuple(dict.fromkeys(required)))
        # The tags and the exit classes may live in any monitor source.
        literals = [literal for text in sources
                    for literal in c_literals(text)]
        findings += literal_findings(B7_SRC, literals, GUEST_PREFIXES)
        # A DETAIL line's text (`BE_B7:DETAIL switch ...`) names no class.
        names = [literal for literal in literals
                 if not literal.startswith(DETAIL_PREFIX)]
        for klass in CLASSES:
            token = re.compile(rf"(?<![\w-]){re.escape(klass)}(?![\w-])")
            if not any(token.search(literal) for literal in names):
                findings.append(f"no literal in {B7_SRC} names the class "
                                f"{klass!r}")
        known = {line.split(" ", 1)[0]: line for line in R3_SEQUENCE}
        known.update((line.split(" ", 1)[0], fixed_text(line))
                     for line in RUNTIME_LINES)
        for literal in literals:
            for match in re.finditer(r"BE_(?:R[0-9]|B[0-9]):[0-9]{2}",
                                     literal):
                wanted = known.get(match.group(0))
                if wanted is None or \
                        not literal.startswith(wanted, match.start()):
                    findings.append(f"{B7_SRC} literal {literal!r} holds a "
                                    f"marker outside the plan")
    if init is None:
        notes.append(f"{B7_INIT} is missing, so the init source check is "
                     f"skipped")
    else:
        literals = c_literals(init)
        findings += literal_findings("b7-init.c", literals, INIT_TEXTS)
        for literal in literals:
            forged = [tag for tag in GUEST_FORBIDDEN if tag in literal]
            if forged:
                findings.append(f"b7-init.c literal {literal!r} holds the tag "
                                f"{forged[0]!r}")
    return findings, notes


def plan_markers(plan):
    """The ```text blocks of the plan's Markers section, as line tuples."""
    match = re.search(r"^## Markers\n(.*?)^## ", plan, re.M | re.S)
    if not match:
        return ()
    return tuple(tuple(block.splitlines()) for block in re.findall(
        r"^```text\n(.*?)^```", match.group(1), re.M | re.S))


def plan_run_lines(plan):
    """G1's entry and the shutdown line, from the paragraph after the first
    Markers block (whitespace joined)."""
    lines = []
    for start in ("BE_B7:08 ENTER_GUEST guest=1", SHUTDOWN_TEXT):
        match = re.search(rf"`({re.escape(start)}[^`]*)`", plan)
        lines.append(" ".join(match.group(1).split()) if match else None)
    return tuple(lines)


def plan_b7_classes(plan):
    """(the classes B7 adds to B6's, the terminal regex, K) from the plan."""
    match = re.search(r"The classes are B6's,(.*?)The run tools'\s+terminal "
                      r"regex is\s+`([^`]*)`", plan, re.S)
    added = tuple(re.findall(r"plus `([a-z-]+)` and `([a-z-]+)`",
                             match.group(1))[0]) if match and re.search(
        r"plus `([a-z-]+)` and `([a-z-]+)`", match.group(1)) else ()
    k = re.search(r"at least K = ([0-9]+) alternations", plan)
    return added, match.group(2) if match else None, \
        int(k.group(1)) if k else None


def plan_b6_classes(plan):
    """(classes, terminal regex) from the B6 plan's Markers section."""
    match = re.search(r"^- Classes: (.*?)The run tools'\s+terminal regex\s+"
                      r"is `([^`]*)`", plan, re.M | re.S)
    if not match:
        return (), None
    text = re.sub(r"\([^)]*\)", "", match.group(1))
    return tuple(re.findall(r"`([^`]+)`", text)), match.group(2)


def plan_rejected(plan):
    """The B6 plan's rejected patterns."""
    match = re.search(r"\*\*Rejected\*\* in any guest line, as "
                      r"case-sensitive\s+substrings:(.*?)Also rejected",
                      plan, re.S)
    if not match:
        return ()
    return tuple(re.findall(r"`([^`]+)`",
                            re.sub(r"\([^)]*\)", "", match.group(1))))


def plan_detail(plan):
    """The B6 plan's DETAIL line."""
    match = re.search(r"`(BE_B6:DETAIL [^`]*)`", plan)
    return match.group(1) if match else None


def plan_shim(plan):
    """The B6 plan's fixed SHIM values."""
    match = re.search(r"prints B3's `SHIM` line, which must show\s+"
                      r"`(shim=[^`]*)`,\s+`(dest=[^`]*)`, and\s+"
                      r"`(bytes=[^`]*)`", plan)
    return match.groups() if match else ()


def plan_scenarios(plan):
    """{scenario: (machine, cpu)} for the B6 plan rows that name both."""
    return {name: (machine, cpu) for name, machine, cpu in re.findall(
        r"^\| `([a-z0-9.-]+)` \| `([^`]+)`; `([^`]+)` \|", plan, re.M)}


Outcome = collections.namedtuple(
    "Outcome", "toolchains expect after guest cause check")


def outcome_text(expected):
    """An Outcome (without toolchains) from a plan Expected cell."""
    if expected.startswith("Pass"):
        check = "sbi-time" if "`time` above 0" in expected else None
        return "pass", None, None, None, check
    match = re.match(r"`BE_B7:FAIL ([a-z-]+)`", expected)
    if not match:
        return None, None, None, None, None
    after = re.search(r"(after|before) `(BE_[A-Z0-9]+:[0-9]{2})`", expected)
    line = None
    if after:
        index = [slot.split("/")[0] for slot in LINE_IDS].index(
            after.group(2)) if after.group(2) in \
            [slot.split("/")[0] for slot in LINE_IDS] else None
        if index is None:
            line = "?"
        elif after.group(1) == "after":
            line = LINE_IDS[index]
        else:
            line = LINE_IDS[index - 1] if index else "?"
    guest = re.search(r"`guest=([01])`", expected)
    cause = re.search(r"cause ([0-9]+)", expected)
    check = "tval-not-wfi" if "`tval` not `wfi`" in expected else None
    return match.group(1), line, int(guest.group(1)) if guest else None, \
        int(cause.group(1)) if cause else None, check


def plan_qemu(plan):
    """{scenario: Outcome} from the B7 plan's QEMU scenarios table."""
    start = plan.find("**QEMU scenarios:**")
    end = plan.find("## ", start)
    outcomes = {}
    for names, toolchains, expected in re.findall(
            r"^\| (`[^|]*?) \| ([A-Za-z, ]+) \| ([^|\n]+) \|$",
            plan[start:end], re.M):
        names = re.findall(r"`([a-z0-9.-]+)`", names.split("(")[0])
        chains = tuple(sorted(word.strip().lower()
                              for word in toolchains.split(",")))
        for name in names:
            outcomes[name] = Outcome(chains, *outcome_text(expected))
    return outcomes


def runner_assignments(runner):
    """{name: value} of the runner's single-quoted top-level assignments."""
    return dict(re.findall(r"^([a-z_0-9]+)='([^']*)'$", runner, re.M))


def runner_table(runner, name):
    """The rows of a runner array NAME, one string each, quotes dropped."""
    match = re.search(rf"^{name}=\(\n(.*?)^\)", runner, re.M | re.S)
    return [row.strip().strip("'\"") for row in
            match.group(1).splitlines() if row.strip()] if match else []


def runner_scenarios(runner):
    """{scenario: (Outcome, machine, cpu, firmware, sbi)} from run-qemu.sh's
    scenarios (both toolchains) and variants (GCC, on k3-like) tables."""
    values = runner_assignments(runner)

    def value(word):
        return values.get(word[1:], word) if word.startswith("$") else word

    def none(word):
        return None if word == "-" else word

    found = {}
    for row in runner_table(runner, "scenarios"):
        words = row.split()
        if len(words) != 10:
            found[words[0] if words else "?"] = None
            continue
        name, machine, cpu, firmware, sbi, expect, after, guest, cause, \
            check = words
        found[name] = (Outcome(
            ("clang", "gcc"), expect, none(after),
            int(guest) if guest != "-" else None,
            int(cause) if cause != "-" else None, none(check)),
            value(machine), value(cpu), firmware, sbi)
    for row in runner_table(runner, "variants"):
        words = row.split()
        if len(words) != 6:
            found[words[0] if words else "?"] = None
            continue
        name, expect, after, guest, cause, check = words
        found[name] = (Outcome(
            ("gcc",), expect, none(after),
            int(guest) if guest != "-" else None,
            int(cause) if cause != "-" else None, none(check)),
            values.get("k3_machine"), values.get("k3_cpu"), "opensbi", "2.0")
    return found


def plan_tool_findings(r5_runtime, plan, b6_plan, b5_runner, tools):
    """Findings for the accepted inputs against this checker and the tools.

    tools maps a run-tool name to its text (None when missing)."""
    findings = []
    literals = re.findall(r'"(BE_R3:[^"\\]*)\\n"', r5_runtime)
    if tuple(literals) != R3_SEQUENCE + (R3_DROPPED,):
        findings.append(f"accepted r5-runtime.c BE_R3 literals differ: "
                        f"{literals}")
    blocks = plan_markers(plan)
    if blocks[:1] != (MONITOR_TEMPLATE,):
        findings.append(f"the plan's first Markers block differs: "
                        f"{blocks[:1]}")
    if blocks[1:2] != (GUEST_TEMPLATE,):
        findings.append(f"the plan's guest-line block differs: "
                        f"{blocks[1:2]}")
    if len(blocks) != 2:
        findings.append(f"the plan's Markers section has {len(blocks)} text "
                        f"blocks, expected 2")
    if plan_run_lines(plan) != (ENTER_G1, GUEST_SHUTDOWN):
        findings.append(f"the plan's guest-run lines differ: "
                        f"{plan_run_lines(plan)}")
    for sentence in PLAN_INHERITS:
        if sentence not in " ".join(plan.split()):
            findings.append(f"the plan lacks {sentence!r}")
    added, regex, k = plan_b7_classes(plan)
    b6_classes, _ = plan_b6_classes(b6_plan)
    if b6_classes != B6_CLASSES or b6_classes + added != CLASSES:
        findings.append(f"the plans' classes differ: B6 {b6_classes}, B7 "
                        f"adds {added}")
    if regex != TERMINAL_REGEX:
        findings.append(f"the plan's terminal regex differs: {regex!r}")
    if k != ALTERNATIONS_MIN:
        findings.append(f"the plan's K differs: {k}")
    if plan_rejected(b6_plan) != REJECTED:
        findings.append(f"the B6 plan's rejected patterns differ: "
                        f"{plan_rejected(b6_plan)}")
    detail = plan_detail(b6_plan)
    if detail != B6_DETAIL_TEMPLATE or DETAIL_TEMPLATE != detail.replace(
            "BE_B6:DETAIL ", "BE_B7:DETAIL guest=<g> "):
        findings.append(f"the B6 plan's DETAIL line differs: {detail!r}")
    if plan_shim(b6_plan) != SHIM_FIXED:
        findings.append(f"the B6 plan's SHIM values differ: "
                        f"{plan_shim(b6_plan)}")
    machines = plan_scenarios(b6_plan)
    if set(machines) != {"k3-like", "rva23", "plic"}:
        findings.append(f"the B6 plan's scenario rows differ: {machines}")
    minimal = re.search(r"^minimal='([^']+)'$", b5_runner, re.M)
    if not minimal or "sstc=false" not in minimal.group(1):
        findings.append("accepted B5 run-qemu.sh lost its R5 CPU string")
    for name, text in tools.items():
        if text is None:
            findings.append(f"run tool {name} is missing")
        elif TERMINAL_REGEX not in text:
            findings.append(f"{name} lacks the terminal regex "
                            f"{TERMINAL_REGEX!r}")
    runner = tools.get("run-qemu.sh") or ""
    planned = plan_qemu(plan)
    if set(planned) != {"k3-like", "rva23", "plic", "no-sstc", "sbi-3.0",
                        "sbi-time", "payload", "init-exit", "rdcycle",
                        "exit-budget", "guest-timeout"}:
        findings.append(f"the plan's QEMU scenarios differ: "
                        f"{sorted(planned)}")
    ran = runner_scenarios(runner)
    if set(ran) != set(planned):
        findings.append(f"run-qemu.sh runs {sorted(ran)}, the plan "
                        f"{sorted(planned)}")
    k3_like = machines.get("k3-like")
    wanted = dict(machines)
    if k3_like:
        wanted.update({"no-sstc": ("virt,aia=none",
                                   minimal.group(1) if minimal else None),
                       "sbi-3.0": k3_like})
    for name in sorted(set(ran) & set(planned)):
        if ran[name] is None:
            findings.append(f"run-qemu.sh's {name} row is malformed")
            continue
        outcome, machine, cpu, firmware, sbi = ran[name]
        plan_outcome = planned[name]
        for field in ("toolchains", "expect", "guest", "cause", "check"):
            if getattr(outcome, field) != getattr(plan_outcome, field):
                findings.append(f"run-qemu.sh's {name} {field} "
                                f"{getattr(outcome, field)!r}, the plan's "
                                f"{getattr(plan_outcome, field)!r}")
        if plan_outcome.after is not None and \
                outcome.after != plan_outcome.after:
            findings.append(f"run-qemu.sh runs {name} after "
                            f"{outcome.after}, the plan after "
                            f"{plan_outcome.after}")
        if outcome.after is not None and outcome.after not in LINE_IDS:
            findings.append(f"run-qemu.sh's {name} names no fixed line "
                            f"{outcome.after!r}")
        if (machine, cpu) != wanted.get(name, k3_like):
            findings.append(f"run-qemu.sh runs {name} on {machine} {cpu}, "
                            f"expected {wanted.get(name, k3_like)}")
        sbi_3 = name == "sbi-3.0"
        if (firmware, sbi) != (("default", "3.0") if sbi_3 else
                               ("opensbi", "2.0")):
            findings.append(f"run-qemu.sh runs {name} on firmware "
                            f"{firmware} {sbi}")
    rehearsal = tools.get("kexec-rehearsal.sh") or ""
    for value in machines.get("k3-like", ()):
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
    b6_plan = git_show(root, ACCEPTED_B6_PLAN, B6_PLAN, B6_PLAN_SHA256,
                       findings)
    b5_runner = git_show(root, ACCEPTED_B5, B5_RUNNER, B5_RUNNER_SHA256,
                         findings)
    tools = {path.name: read_optional(path) for path in RUN_TOOLS}
    if None not in (r5_runtime, plan, b6_plan, b5_runner):
        findings += plan_tool_findings(r5_runtime, plan, b6_plan, b5_runner,
                                       tools)
    runtime = read_optional(root / B7_RUNTIME)
    init = read_optional(root / B7_INIT)
    source_dir = root / B7_SRC
    sources = [path.read_text(encoding="utf-8", errors="replace")
               for path in sorted(source_dir.glob("*.[ch]"))] \
        if source_dir.is_dir() else []
    notes = []
    try:
        source_findings, notes = b7_source_findings(runtime, init, sources,
                                                    require_runtime)
        findings += source_findings
    except ValueError as error:
        findings.append(f"cannot parse the B7 sources: {error}")
    for note in notes:
        print(f"note: {note}")
    for finding in findings:
        print(f"finding: {finding}")

    def state(text):
        return "present" if text is not None else "missing (skipped)"

    print(f"BE_B7_MARKER_SOURCES: {'PASS' if not findings else 'FAIL'} "
          f"lines={len(MONITOR_TEMPLATE) + len(GUEST_TEMPLATE) + 2} "
          f"r3=r5-runtime.c@{ACCEPTED_R5[:8]} plan={ACCEPTED_PLAN[:8]} "
          f"b6-plan={ACCEPTED_B6_PLAN[:8]} b7-runtime.c={state(runtime)} "
          f"b7-init.c={state(init)}")
    return 0 if not findings else 1


# Self-test fixtures: their own pins (the research Image's sizes) and
# captures built from the plan's lines.
FIXTURE_PINS = Pins(
    1553332, 0x1af628,
    f"Linux version {RELEASE} (b7@fixture) (riscv64-linux-gnu-gcc (GCC) "
    f"16.2.1 20260819, GNU ld version 2.46.1-1.fc44) #1 2026-08-16")
FIXTURE_FDT = 0xbfe00000
FIXTURE_COUNTERS = (
    {"wfi": 262, "slice": 31, "base": 14, "time": 0, "dbcn_write": 160,
     "dbcn_read": 35, "dbcn_byte": 0, "srst": 1, "refused": 0},
    {"wfi": 258, "slice": 29, "base": 14, "time": 0, "dbcn_write": 158,
     "dbcn_read": 35, "dbcn_byte": 0, "srst": 1, "refused": 0},
)
FIXTURE_SHUTDOWN_TICKS = (0x3a1b2c0, 0x3c8e1a0)
FIXTURE_RUN = {"wfi_switches": 233, "slice_switches": 27, "stop_switches": 1,
               "idle_waits": 41, "idle_ticks": 0x1c9c380, "ticks": 0x3ca8f00}
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
    ticks = iter(("0x6a5f3c", "0x6a6104", "0x18f04e", "0x18f20a"))
    out = []
    for line in PRE_RUN:
        if "<T>" in line:
            line = line.replace("<T>", next(ticks))
        out.append(line.replace("<K>", f"0x{pins.kernel_bytes:x}")
                   .replace("<S>", f"0x{pins.image_size:x}")
                   .replace("<h>", f"0x{HEDELEG:x}"))
    return out


def stamp(seconds):
    return f"[{seconds:12.6f}] "


def guest_lines(guest, pins=FIXTURE_PINS, elapsed=1003):
    """A research-like Linux log of one guest, without its prefix."""
    window = LAYOUT["GUEST_BYTES"] // 1024
    kernel = [
        stamp(0) + pins.banner,
        stamp(0) + "Machine model: Beryllium K3 B7 guest",
        stamp(0) + "SBI specification v2.0 detected",
        stamp(0) + KERNEL_LINES[1],
        stamp(0) + "SBI TIME extension detected",
        stamp(0) + "SBI SRST extension detected",
        stamp(0) + "SBI DBCN extension detected",
        stamp(0) + "earlycon: sbi0 at I/O port 0x0 (options '')",
        stamp(0) + "printk: legacy bootconsole [sbi0] enabled",
        stamp(0) + KERNEL_LINES[2].replace("<g>", str(guest)),
        stamp(0) + "riscv-intc: 64 local interrupts mapped",
        stamp(0.003873) + KERNEL_LINES[3],
        stamp(0.147324) + f"Memory: {window - 3592}K/{window}K available "
        f"(694K kernel code, 553K rwdata, 119K rodata, 145K init, 205K bss, "
        f"2964K reserved, 0K cma-reserved)",
        stamp(0.247249) + "printk: legacy console [hvc0] enabled",
        stamp(0.248995) + "printk: legacy bootconsole [sbi0] disabled",
        stamp(0.327393) + KERNEL_LINES[5],
    ]
    init = [INIT_LINES[0].replace("<g>", str(guest)), INIT_LINES[1]]
    init += [f"B7INIT 03 STEP n={step}/{STEPS} rounds={1700 + 37 * step} "
             f"t_ms={350 + 80 * step + 3 * guest}"
             for step in range(1, STEPS + 1)]
    init += [INIT_LINES[3].replace("<e>", str(elapsed)), INIT_LINES[4],
             INIT_LINES[5]]
    return kernel + init + [stamp(2.461337 + 0.01 * guest) + POWER_DOWN]


def shutdown_line(guest, ticks=None, **changes):
    counters = dict(FIXTURE_COUNTERS[guest], **changes)
    counters.setdefault("sbi", sum(counters[name] for name in SBI_CLASSES))
    counters.setdefault("exits", counters["sbi"] + counters["wfi"] +
                        counters["slice"])
    ticks = FIXTURE_SHUTDOWN_TICKS[guest] if ticks is None else ticks
    return f"{SHUTDOWN_TEXT}{guest} " + " ".join(
        [f"{name}={counters[name]}" for name in COUNTERS] +
        [f"ticks=0x{ticks:x}"])


def run_complete_line(**changes):
    counters = dict(FIXTURE_RUN, **changes)
    counters.setdefault("switches", counters["wfi_switches"] +
                        counters["slice_switches"] +
                        counters["stop_switches"])
    return "BE_B7:10 RUN_COMPLETE " + " ".join(
        [f"{name}={counters[name]}" for name in RUN_FIELDS[:5]] +
        [f"{name}=0x{counters[name]:x}" for name in RUN_FIELDS[5:]])


def default_order(bodies):
    """G0's first three lines, then the guests' lines one by one, G1's
    last."""
    pairs = len(bodies[0]) - 3
    return (0, 0, 0) + (1, 0) * pairs + (1,) * (len(bodies[1]) - pairs)


def run_lines(bodies, order=None, shutdowns=None):
    """The guest run: each guest's lines (BODIES) prefixed and taken in
    ORDER, G1's entry before its first line, and each guest's BE_B7:09
    after its last line."""
    order = order or default_order(bodies)
    if [order.count(guest) for guest in GUESTS] != \
            [len(bodies[guest]) for guest in GUESTS]:
        raise ValueError("the order does not take every line once")
    shutdowns = shutdowns or tuple(shutdown_line(guest) for guest in GUESTS)
    taken = [0, 0]
    out = []
    for guest in order:
        if guest == 1 and not taken[1]:
            out.append(ENTER_G1)
        out.append(GUEST_PREFIXES[guest] + bodies[guest][taken[guest]])
        taken[guest] += 1
        if taken[guest] == len(bodies[guest]):
            out.append(shutdowns[guest])
    return out


def pass_lines(pins=FIXTURE_PINS, order=None, bodies=None,
               shutdowns=None, run=None):
    bodies = bodies or (guest_lines(0, pins), guest_lines(1, pins))
    return [shim_line()] + list(R3_SEQUENCE) + entry_lines(pins) + \
        run_lines(bodies, order, shutdowns) + \
        [run or run_complete_line(), SHUTDOWN]


def sample(lines, banner=BANNER, eol="\r\n", after=""):
    """A synthetic capture: a firmware banner, then the lines."""
    return banner + eol.join(lines) + eol + after


def detail(cause, guest=0, htval=0, pc=0x80201234, tval=0, htinst=0,
           spvp=1, vsatp=0x8000000000081234, exits=57):
    return (f"BE_B7:DETAIL guest={guest} cause=0x{cause:x} pc=0x{pc:x} "
            f"tval=0x{tval:x} htval=0x{htval:x} htinst=0x{htinst:x} "
            f"spvp={spvp} vsatp=0x{vsatp:x} exits={exits}")


def switch_detail(guest=1, register="hgatp", wanted=None, readback=0):
    wanted = HGATPS[guest] if wanted is None else wanted
    return (f"BE_B7:DETAIL switch guest={guest} register={register} "
            f"wanted=0x{wanted:x} readback=0x{readback:x}")


def steps_apart():
    """An order with many alternations whose 03 STEP phases do not
    overlap: the kernel lines one by one, G0's init lines, G1's init
    lines, then the power-downs."""
    kernel = len(guest_lines(0)) - len(INIT_LINES) - STEPS
    init = len(INIT_LINES) + STEPS - 1
    return (0, 1) * kernel + (0,) * init + (1,) * init + (0, 1)


def blocks(*runs):
    """An order from (guest, lines) runs."""
    order = []
    for guest, count in runs:
        order += [guest] * count
    return tuple(order)


# Each guest has 16 kernel lines, then START and UNAME, the eight steps
# (its lines 18-25), then four more lines. Runs of lines give exact
# alternation counts with 03 STEP phases that overlap both ways (8 and 7)
# or one way only (10).
ORDER_8 = blocks((0, 3), (1, 3), (0, 3), (1, 3), (0, 13), (1, 14), (0, 7),
                 (1, 10), (0, 4))
ORDER_7 = blocks((0, 3), (1, 3), (0, 3), (1, 3), (0, 13), (1, 14), (0, 11),
                 (1, 10))
ORDER_ONE_WAY = blocks((0, 3), (1, 3), (0, 3), (1, 3), (0, 3), (1, 3),
                       (0, 3), (1, 3), (0, 7), (1, 18), (0, 11))


def capture_cases():
    """(name, text, options, wanted) for the capture self-test."""
    lines = pass_lines()
    good = sample(lines)
    at = {}
    for index, line in enumerate(lines):
        if guest_of(line) is None and line.startswith("BE_"):
            key = slot_id(line) if line in FIXED or line.startswith(
                ("BE_B7:05 ", "BE_B7:06 ")) else line.split(" ", 1)[0]
            if line == ENTER_G1:
                key = "BE_B7:08/g1"
            elif line.startswith(SHUTDOWN_TEXT):
                key = f"BE_B7:09/g{line[len(SHUTDOWN_TEXT)]}"
            at.setdefault(key, index)
    g0 = [index for index, line in enumerate(lines) if guest_of(line) == 0]
    g1 = [index for index, line in enumerate(lines) if guest_of(line) == 1]
    pins = {"pins": FIXTURE_PINS}
    sbi = {"pins": FIXTURE_PINS, "sbi_time": True}

    def edit(index, line):
        return sample(lines[:index] + [line] + lines[index + 1:])

    def insert(index, *extra):
        return sample(lines[:index] + list(extra) + lines[index:])

    def move(index, to):
        moved = lines[:index] + lines[index + 1:]
        to = to - 1 if to > index else to
        return sample(moved[:to] + [lines[index]] + moved[to:])

    def body_edit(guest, old, new):
        prefix = GUEST_PREFIXES[guest]
        return sample([prefix + new if line == prefix + old else line
                       for line in lines])

    def bodies(edit0=None, edit1=None):
        return tuple((edit or (lambda body: body))(guest_lines(guest))
                     for guest, edit in zip(GUESTS, (edit0, edit1)))

    def replace_body(old, new):
        return lambda body: [new if line == old else line for line in body]

    noise = GUEST_PREFIXES[0] + stamp(0.2) + "clk: Disabling unused clocks"
    kexec = ("[ 4208.994539] kexec_core: Starting new kernel\r\n"
             "[ 4209.068232] Will call new kernel at 108000000 from hart id "
             "0\r\n[ 4209.071298] FDT image at 108200000\r\n"
             "[ 4209.074905] Bye...\r\n")
    sleep = INIT_LINES[3].replace("<e>", "1003")
    step = [line for line in guest_lines(0) if STEP.fullmatch(line)]
    step1 = [line for line in guest_lines(1) if STEP.fullmatch(line)]
    sstc_line = stamp(0.003873) + KERNEL_LINES[SSTC_AT]
    no_sstc = bodies(*([lambda body: [line for line in body
                                      if line != sstc_line]] * 2))
    sbi_shutdowns = (shutdown_line(0, time=12), shutdown_line(1, time=9))
    command = stamp(0) + KERNEL_LINES[COMMAND_LINE_AT]
    memory = next(line for line in guest_lines(0) if "Memory: " in line)
    window = LAYOUT["GUEST_BYTES"] // 1024
    hedeleg = lines[at["BE_B7:04"]]
    cases = [
        ("pass", good, pins, True),
        ("pass, LF only", good.replace("\r", ""), pins, True),
        ("pass after loader noise", sample(
            lines, banner="[ 4209.074905] Bye...\r\nunrelated loader text"
            "\r\n\r\n"), pins, True),
        ("pass after the kexec handoff", sample(lines, banner=kexec), pins,
         True),
        ("pass with a blank line", edit(g0[5], "\r\n" + lines[g0[5]]),
         pins, True),
        ("pass with guest noise", insert(g0[20], noise), pins, True),
        ("pass, G1 stops first", sample(pass_lines(order=blocks(
            (0, 3), (1, 6)) + (0, 1) * 24 + (0, 0, 0))), pins, True),
        ("pass, G1 prints first", sample(pass_lines(order=(1, 0) * 30)),
         pins, True),
        ("pass with exactly 8 alternations", sample(pass_lines(
            order=ORDER_8)), pins, True),
        ("7 alternations", sample(pass_lines(order=ORDER_7)), pins, False),
        ("03 STEP phases apart", sample(pass_lines(order=steps_apart())),
         pins, False),
        ("03 STEP phases overlapping one way", sample(pass_lines(
            order=ORDER_ONE_WAY)), pins, False),
        ("pass at elapsed 1000", body_edit(
            0, sleep, sleep.replace("1003", "1000")), pins, True),
        ("pass at elapsed 1999", body_edit(
            1, sleep, sleep.replace("1003", "1999")), pins, True),
        ("G0 elapsed 999", body_edit(0, sleep, sleep.replace("1003", "999")),
         pins, False),
        ("G1 elapsed 2000", body_edit(
            1, sleep, sleep.replace("1003", "2000")), pins, False),
        ("G1 sleep not ok", body_edit(1, sleep, sleep.replace("ok=1",
                                                              "ok=0")),
         pins, False),
        ("sbi-time pass", sample(pass_lines(bodies=no_sstc,
                                            shutdowns=sbi_shutdowns)), sbi,
         True),
        ("sbi-time with G1's Sstc timer line", sample(pass_lines(
            bodies=(no_sstc[0], guest_lines(1)), shutdowns=sbi_shutdowns)),
         sbi, False),
        ("sbi-time counters without --sbi-time", sample(pass_lines(
            bodies=no_sstc, shutdowns=sbi_shutdowns)), pins, False),
        ("--sbi-time with G0's time=0", sample(pass_lines(
            bodies=no_sstc, shutdowns=(shutdown_line(0), sbi_shutdowns[1]))),
         sbi, False),
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
            g1[10], "[    0.5] Linux line without a tag"), pins, False),
        ("text after BE_B7:11", sample(lines, after="sbi_hart: halted\r\n"),
         pins, False),
        ("marker after BE_B7:11", sample(lines + ["BE_B7:12 EXTRA"]), pins,
         False),
        ("guest line after BE_B7:11", sample(lines + [noise]), pins, False),
        ("guest line before G0's BE_B7:08", insert(at["BE_B7:08"], noise),
         pins, False),
        ("guest line between BE_B7:10 and BE_B7:11", insert(
            at["BE_B7:11"], noise), pins, False),
        ("BE_R3:07 kept", insert(at["BE_R3:06"] + 1, R3_DROPPED), pins,
         False),
        ("R4 marker", insert(at["BE_B7:01/g0"],
                             "BE_R4:01 ENTRY_ARMED_IMPORTED"), pins, False),
        ("B6 marker", insert(at["BE_B7:01/g0"], "BE_B6:01 GSTAGE_BUILT_"
                             "REWALKED gpa=0x80000000"), pins, False),
        ("a fixed line repeated in the guest run", insert(
            g0[10], lines[at["BE_B7:07"]]), pins, False),
        ("failure after pass", sample(lines + [FAIL_PREFIX + "resume"]),
         pins, False),
        ("SRST returned after pass", sample(lines + [SRST_RETURNED]), pins,
         False),
        ("no shutdown", sample(lines[:-1]), pins, False),
        ("G1 line before its entry", move(at["BE_B7:08/g1"],
                                          g1[0] + 1), pins, False),
        ("G1 entered twice", insert(g1[5], ENTER_G1), pins, False),
        ("G1 entered at another pc", edit(at["BE_B7:08/g1"],
                                          ENTER_G1.replace("pc=0x80200000",
                                                           "pc=0x80000000")),
         pins, False),
        ("G0 entered again in the run", insert(g1[5], entry_line(0)), pins,
         False),
        ("G0 line after its BE_B7:09", move(g0[-1], at["BE_B7:09/g0"] + 1),
         pins, False),
        ("one shutdown only", sample(lines[:at["BE_B7:09/g1"]] +
                                     lines[at["BE_B7:09/g1"] + 1:]),
         pins, False),
        ("two BE_B7:09 for G0", insert(g1[-1] + 1, lines[at[
            "BE_B7:09/g0"]]), pins, False),
        ("G1's BE_B7:09 before its entry", sample(
            lines[:at["BE_B7:08/g1"]] + [lines[at["BE_B7:09/g1"]]] +
            [line for line in lines[at["BE_B7:08/g1"]:]
             if not line.startswith(SHUTDOWN_TEXT + "1")]), pins, False),
        ("BE_B7:10 before G1's BE_B7:09", move(at["BE_B7:09/g1"],
                                               at["BE_B7:10"] + 1), pins,
         False),
        ("BE_B7:05 for G1 before G0's", sample(
            lines[:at["BE_B7:05/g0"]] + [lines[at["BE_B7:05/g1"]],
                                          lines[at["BE_B7:05/g0"]]] +
            lines[at["BE_B7:05/g1"] + 1:]), pins, False),
        ("BE_B7:02 with the roots swapped", edit(at["BE_B7:02"], lines[
            at["BE_B7:02"]].replace("g1=", "gx=").replace("g0=", "g1=")
            .replace("gx=", "g0=")), pins, False),
        ("G1's root at G0's window", edit(at["BE_B7:01/g1"], lines[
            at["BE_B7:01/g1"]].replace("hpa=0x114000000",
                                       "hpa=0x110000000")), pins, False),
        ("another slice", edit(at["BE_B7:07"], lines[at["BE_B7:07"]]
                               .replace("0x3a980", "0x3a981")), pins, False),
        ("G0 entered with another a1", edit(at["BE_B7:08"], lines[
            at["BE_B7:08"]].replace("a1=0x83e00000", "a1=0x0")), pins,
         False),
        ("forged hedeleg", edit(at["BE_B7:04"], hedeleg.replace(
            "hedeleg=0xb15d", "hedeleg=0xb17d")), pins, False),
        ("hedeleg without page faults", edit(at["BE_B7:04"], hedeleg.replace(
            "hedeleg=0xb15d", "hedeleg=0x315d")), pins, False),
        ("hedeleg with a leading zero", edit(at["BE_B7:04"], hedeleg.replace(
            "hedeleg=0xb15d", "hedeleg=0x0b15c")), pins, False),
        ("WARL hedeleg without cause 0", edit(at["BE_B7:04"], hedeleg.replace(
            "hedeleg=0xb15d", "hedeleg=0xb15c")), pins, True),
        ("WARL hedeleg without causes 0, 4, and 6", edit(
            at["BE_B7:04"], hedeleg.replace("hedeleg=0xb15d",
                                            "hedeleg=0xb10c")), pins, True),
        ("sie without STIE", edit(at["BE_B7:04"], hedeleg.replace(
            "sie=0x20", "sie=0x0")), pins, False),
        ("G1's command line names guest 0", body_edit(
            1, command.replace("<g>", "1"), command.replace("<g>", "0")),
         pins, False),
        ("G1's START names guest 0", body_edit(
            1, INIT_LINES[0].replace("<g>", "1"),
            INIT_LINES[0].replace("<g>", "0")), pins, False),
        ("G0's START names no guest", body_edit(
            0, INIT_LINES[0].replace("<g>", "0"),
            INIT_LINES[0].replace("<g>", "none")), pins, False),
        ("G0's command line without its ID", body_edit(
            0, command.replace("<g>", "0"),
            stamp(0) + f"Kernel command line: {COMMAND_LINE}"), pins, False),
        ("G0 line holding G1's tag", insert(g0[12], GUEST_PREFIXES[0] +
                                            stamp(0.2) + "clk: Disab" +
                                            GUEST_PREFIXES[1] + "ling"),
         pins, False),
        ("G0 line holding an init line", insert(
            g0[12], GUEST_PREFIXES[0] + stamp(0.2) + "clk: Disab" + step1[0]),
         pins, False),
        ("G0 line holding a second timestamp", insert(
            g0[12], GUEST_PREFIXES[0] + stamp(0.2) + "clk: Disab" +
            stamp(0.21) + "Run /init as init process"), pins, False),
        ("G1 line of 256 bytes", insert(g1[12], GUEST_PREFIXES[1] +
                                        stamp(0.3) + "x" * 241), pins, True),
        ("G1 line of 257 bytes", insert(g1[12], GUEST_PREFIXES[1] +
                                        stamp(0.3) + "x" * 242), pins,
         False),
        ("zero wfi switches", edit(at["BE_B7:10"], run_complete_line(
            wfi_switches=0)), pins, False),
        ("zero slice switches", edit(at["BE_B7:10"], run_complete_line(
            slice_switches=0)), pins, False),
        ("switches not the sum", edit(at["BE_B7:10"], run_complete_line(
            switches=FIXTURE_RUN["wfi_switches"] + 1)), pins, False),
        ("stop_switches=0", edit(at["BE_B7:10"], run_complete_line(
            stop_switches=0)), pins, False),
        ("stop_switches=2", edit(at["BE_B7:10"], run_complete_line(
            stop_switches=2)), pins, False),
        ("idle_ticks above ticks", edit(at["BE_B7:10"], run_complete_line(
            idle_ticks=FIXTURE_RUN["ticks"] + 1)), pins, False),
        ("run ticks above the budget", edit(at["BE_B7:10"],
                                            run_complete_line(
                                                ticks=LAYOUT[
                                                    "GUEST_TIME_BUDGET"] + 1)),
         pins, False),
        ("G1's ticks above the run's", edit(at["BE_B7:09/g1"], shutdown_line(
            1, ticks=FIXTURE_RUN["ticks"] + 1)), pins, False),
        ("switches above the wfi and slice exits", edit(
            at["BE_B7:10"], run_complete_line(wfi_switches=600)), pins,
         False),
        ("run complete with idle_waits in hex", edit(
            at["BE_B7:10"], lines[at["BE_B7:10"]].replace(
                "idle_waits=41", "idle_waits=0x29")), pins, False),
        ("G0 exits not the sum", edit(at["BE_B7:09/g0"], shutdown_line(
            0, exits=500)), pins, False),
        ("G1 sbi not the sum of the classes", edit(
            at["BE_B7:09/g1"], shutdown_line(1, sbi=200)), pins, False),
        ("G0 srst=2", edit(at["BE_B7:09/g0"], shutdown_line(0, srst=2)),
         pins, False),
        ("G1 refused call", edit(at["BE_B7:09/g1"], shutdown_line(
            1, refused=1)), pins, False),
        ("G0 DBCN write_byte call", edit(at["BE_B7:09/g0"], shutdown_line(
            0, dbcn_byte=1)), pins, False),
        ("G1 time without --sbi-time", edit(at["BE_B7:09/g1"], shutdown_line(
            1, time=3)), pins, False),
        ("G0 exits above the ceiling", edit(at["BE_B7:09/g0"], shutdown_line(
            0, dbcn_write=LAYOUT["EXIT_CEILING"])), pins, False),
        ("G0 exits with a leading zero", edit(at["BE_B7:09/g0"], lines[
            at["BE_B7:09/g0"]].replace(" exits=", " exits=0")), pins, False),
        ("G1 shutdown ticks in decimal", edit(at["BE_B7:09/g1"], lines[
            at["BE_B7:09/g1"]].replace(f"ticks=0x{FIXTURE_SHUTDOWN_TICKS[1]:x}",
                                       f"ticks={FIXTURE_SHUTDOWN_TICKS[1]}")),
         pins, False),
        ("BE_B7:09 naming guest 2", edit(at["BE_B7:09/g1"], lines[
            at["BE_B7:09/g1"]].replace("guest=1", "guest=2")), pins, False),
        ("ticks with a leading zero", edit(at["BE_B7:05/g0"], lines[
            at["BE_B7:05/g0"]].replace("ticks=0x6a5f3c", "ticks=0x06a5f3c")),
         pins, False),
        ("ticks in upper case", edit(at["BE_B7:05/g0"], lines[
            at["BE_B7:05/g0"]].replace("ticks=0x6a5f3c", "ticks=0x6A5F3C")),
         pins, False),
        ("G0 steps 1 and 2 swapped", sample(pass_lines(bodies=bodies(
            lambda body: [step[1] if line == step[0] else step[0]
                          if line == step[1] else line for line in body])))),
        ("G1 step 3 twice", insert(g1[20] + 1, GUEST_PREFIXES[1] +
                                   step1[2]), pins, False),
        ("G0 step 9 of 8", insert(g0[25], GUEST_PREFIXES[0] +
                                  "B7INIT 03 STEP n=9/8 rounds=1 t_ms=999"),
         pins, False),
        ("G1 step times not rising", sample(pass_lines(bodies=bodies(
            None, replace_body(step1[4], step1[4].replace(
                "t_ms=753", "t_ms=600")))))),
        ("G0 step with no rounds", sample(pass_lines(bodies=bodies(
            replace_body(step[0], step[0].replace("rounds=1737",
                                                  "rounds=0")))))),
        ("duplicated init line", insert(g0[-1], GUEST_PREFIXES[0] +
                                        INIT_LINES[4]), pins, False),
        ("unexpected init line", insert(g0[-1], GUEST_PREFIXES[0] +
                                        "B7INIT 07 EXTRA"), pins, False),
        ("init line without a prefix", insert(g0[-1],
                                              "B7INIT 06 POWER_OFF"), pins,
         False),
        ("init line with a damaged prefix", body_edit(
            0, INIT_LINES[1], INIT_LINES[1]).replace(
            GUEST_PREFIXES[0] + INIT_LINES[1], "BE_B7_G: " + INIT_LINES[1]),
         pins, False),
        ("another panic word on the command line", body_edit(
            0, command.replace("<g>", "0"), command.replace(
                "<g>", "0") + " panic_print=1"), pins, False),
        ("more memory than the window", body_edit(0, memory, memory.replace(
            f"{window - 3592}K/", f"{window + 1}K/")), pins, False),
        ("a larger memory total", body_edit(1, memory, memory.replace(
            f"/{window}K", f"/{window * 2}K")), pins, False),
        ("escape in a guest line", insert(g0[-1], GUEST_PREFIXES[0] +
                                          "\x1b[2Jclear"), pins, False),
        ("tab in a guest line", insert(g1[-1], GUEST_PREFIXES[1] + "a\tb"),
         pins, False),
        ("mid-line CR", insert(g0[-1], GUEST_PREFIXES[0] + "a\rb"), pins,
         False),
        ("undecodable byte", insert(g1[-1], GUEST_PREFIXES[1] + "\ufffd"),
         pins, False),
        ("--after on a pass", good, dict(pins, after="BE_B7:08"), False),
        ("--guest on a pass", good, dict(pins, guest=0), False),
    ]
    # The cases above that build their own capture take the pins.
    cases = [case if len(case) == 4 else case + (pins, False)
             for case in cases]
    # Dropping any required line fails; dropping guest noise does not.
    patterns = [[template_pattern(line, FIXTURE_PINS)
                 for line in guest_template(guest)] for guest in GUESTS]
    for index, line in enumerate(lines):
        guest = guest_of(line)
        required = guest is None or any(
            pattern.fullmatch(line[len(GUEST_PREFIXES[guest]):])
            for pattern in patterns[guest])
        cases.append((f"without line {index + 1} "
                      f"({'required' if required else 'noise'})",
                      sample(lines[:index] + lines[index + 1:]), pins,
                      not required))
    for pattern in REJECTED:
        for guest, where in ((0, g0[20]), (1, g1[20])):
            cases.append((f"rejected {pattern!r} in a G{guest} line", insert(
                where, GUEST_PREFIXES[guest] + stamp(0.9) + f"x {pattern} y"),
                pins, False))
    for tag in GUEST_FORBIDDEN:
        for guest, where in ((0, g0[20]), (1, g1[20])):
            cases.append((f"G{guest} line holding {tag!r}", insert(
                where, GUEST_PREFIXES[guest] + f"echo {tag}"), pins, False))
    return lines, good, cases


# A controls readback as the monitor prints it (hedeleg off its WARL set).
CONTROLS_READBACK = (
    "BE_B7:DETAIL controls hip=0x0 hstatus=0x200200180 hedeleg=0xb17d "
    "hideleg=0x40 hie=0x0 hvip=0x0 hcounteren=0x2 htimedelta=0x0",
    "BE_B7:DETAIL controls henvcfg=0x8000000000000000 hgeie=0x0 "
    "vstimecmp=0xffffffffffffffff sie=0x20 sstatus=0x200000000 "
    "hgatp=0x8000100000102034 vsatp=0x0 sscratch=0x102027000",
)
# rdcycle a0 in VU mode: cause 22 with the instruction in tval.
RDCYCLE = 0xc0002573


def failure_cases(lines):
    """(name, text, options, wanted) for --expect-fail."""
    index_of = {slot_id(line): index for index, line in enumerate(lines)
                if line in FIXED}
    entry = lines.index(entry_line(0))
    head = lines[:entry + 1]
    controls = next(index for index, line in enumerate(lines)
                    if line.startswith("BE_B7:04 "))
    payload = [index for index, line in enumerate(lines)
               if line.startswith("BE_B7:06 ")]
    # A guest run with both guests entered, and one with G0 alone.
    run = lines[entry + 1:]
    both = head + run[:run.index(ENTER_G1) + 4]
    g0_only = head + run[:3]
    pins = {"pins": FIXTURE_PINS}
    sbi30 = "\r\nOpenSBI v1.7\r\nRuntime SBI Version : 3.0\r\n\r\n"
    panic = [GUEST_PREFIXES[1] + stamp(0.33) + "Kernel panic - not syncing: "
             "Attempted to kill init! exitcode=0x00000000",
             GUEST_PREFIXES[1] + stamp(0.33) + "---[ end Kernel panic - not "
             "syncing: Attempted to kill init! exitcode=0x00000000 ]---"]

    def fail(klass, before, *after, **options):
        return sample(before + [FAIL_PREFIX + klass] + list(after)), \
            dict(pins, expect_fail=klass, **options)

    def case(name, built, wanted):
        return (name, built[0], built[1], wanted)

    shim = [lines[0]]
    r3 = shim + list(R3_SEQUENCE)
    armed = lines[:controls + 1]
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
        case("gstage after G0's root", fail(
            "gstage", lines[:index_of["BE_B7:01/g0"] + 1],
            after="BE_B7:01/g0"), True),
        case("gstage after G0's root is not after G1's", fail(
            "gstage", lines[:index_of["BE_B7:01/g0"] + 1],
            after="BE_B7:01/g1"), False),
        case("no-sstc", fail("sstc", lines[:index_of["BE_B7:02"] + 1],
                             after="BE_B7:02"), True),
        case("sstc with a detail", fail(
            "sstc", lines[:index_of["BE_B7:02"] + 1], detail(2),
            after="BE_B7:02"), False),
        case("sstc after BE_B7:03", fail(
            "sstc", lines[:index_of["BE_B7:03"] + 1], after="BE_B7:02"),
            False),
        case("controls", fail("controls", lines[:index_of["BE_B7:03"] + 1],
                              after="BE_B7:03"), True),
        case("controls with its readback", fail(
            "controls", lines[:index_of["BE_B7:03"] + 1], *CONTROLS_READBACK,
            after="BE_B7:03"), True),
        case("controls with half its readback", fail(
            "controls", lines[:index_of["BE_B7:03"] + 1],
            CONTROLS_READBACK[0], after="BE_B7:03"), False),
        case("controls readback out of order", fail(
            "controls", lines[:index_of["BE_B7:03"] + 1],
            CONTROLS_READBACK[1], CONTROLS_READBACK[0], after="BE_B7:03"),
            False),
        case("controls with an exit detail", fail(
            "controls", lines[:index_of["BE_B7:03"] + 1], detail(2),
            after="BE_B7:03"), False),
        case("payload with a controls readback", fail(
            "payload", armed, *CONTROLS_READBACK, after="BE_B7:04"), False),
        case("payload variant", fail("payload", armed, after="BE_B7:04"),
             True),
        case("payload with a detail", fail("payload", armed, detail(2),
                                           after="BE_B7:04"), False),
        case("switch at arming", fail(
            "switch", armed, switch_detail(0, "vsstatus", 0x200000000, 0),
            after="BE_B7:04", guest=0), True),
        case("switch in the guest run", fail(
            "switch", both, switch_detail(1), after="BE_B7:08", guest=1),
            True),
        case("switch, SRST returned", fail(
            "switch", both, switch_detail(0, "vstimecmp", 0x5a5a, 0x5a5b),
            SRST_RETURNED), True),
        case("switch without its detail", fail("switch", armed), False),
        case("switch with an exit detail", fail(
            "switch", both, detail(22)), False),
        case("switch reading back the wanted value", fail(
            "switch", both, switch_detail(1, readback=HGATPS[1])), False),
        case("switch naming another register", fail(
            "switch", both, switch_detail(1, "hstatus", 0x200180, 0)), False),
        case("switch naming guest 0, expected 1", fail(
            "switch", both, switch_detail(0), guest=1), False),
        case("payload after G0's placement", fail(
            "payload", lines[:payload[0] + 1], after="BE_B7:06/g0"), True),
        case("init-exit variant: G1 panics, then reboots", fail(
            "guest-reboot", both + panic, detail(10, guest=1, exits=88),
            after="BE_B7:08", guest=1), True),
        case("init-exit naming G0", fail(
            "guest-reboot", both + panic, detail(10, guest=0),
            after="BE_B7:08", guest=1), False),
        case("init-exit naming G1 before its entry", fail(
            "guest-reboot", g0_only, detail(10, guest=1), after="BE_B7:08"),
            False),
        case("guest-reboot without detail", fail("guest-reboot", both),
             False),
        case("rdcycle variant", fail(
            "virtual-instruction", both, detail(22, tval=RDCYCLE, spvp=0),
            after="BE_B7:08", guest=0, cause=22, tval_not_wfi=True), True),
        case("rdcycle variant, a VS wfi", fail(
            "virtual-instruction", both, detail(22, tval=WFI, spvp=1),
            after="BE_B7:08", guest=0, cause=22), False),
        case("VU wfi as a virtual-instruction failure", fail(
            "virtual-instruction", both, detail(22, tval=WFI, spvp=0),
            after="BE_B7:08", guest=0, cause=22), True),
        case("VU wfi with --tval-not-wfi", fail(
            "virtual-instruction", both, detail(22, tval=WFI, spvp=0),
            tval_not_wfi=True), False),
        case("rdcycle variant, cause 2", fail(
            "virtual-instruction", both, detail(2, tval=RDCYCLE), cause=22),
            False),
        case("rdcycle variant naming G1", fail(
            "virtual-instruction", both, detail(22, guest=1, tval=RDCYCLE),
            guest=0), False),
        case("guest-page fault", fail("guest-page-fault", both,
                                      detail(21, htval=0x20100000)), True),
        case("guest-page fault without detail", fail(
            "guest-page-fault", both), False),
        case("guest-page fault with cause 22", fail(
            "guest-page-fault", both, detail(22)), False),
        case("access fault", fail("access-fault", both, detail(5)), True),
        case("access fault with cause 13", fail(
            "access-fault", both, detail(13)), False),
        case("illegal instruction", fail("illegal-instruction", both,
                                         detail(2, guest=1)), True),
        case("interrupt", fail("interrupt", both, detail(INTERRUPT | 9)),
             True),
        case("interrupt: the supervisor timer", fail(
            "interrupt", both, detail(SUPERVISOR_TIMER)), False),
        case("interrupt without the interrupt bit", fail(
            "interrupt", both, detail(5)), False),
        case("VU ecall exception", fail("exception", both, detail(8)), True),
        case("exception with a guest-page cause", fail(
            "exception", both, detail(21)), False),
        case("exception without detail", fail("exception", both), True),
        case("exit-budget variant", fail(
            "exit-budget", g0_only, detail(10, exits=65), after="BE_B7:08"),
            True),
        case("exit-budget without detail", fail("exit-budget", both),
             False),
        case("guest-timeout variant", fail(
            "guest-timeout", both, detail(10, guest=1), after="BE_B7:08"),
            True),
        case("guest-timeout without detail", fail("guest-timeout", both),
             False),
        case("scheduler", fail("scheduler", both, detail(10)), True),
        case("scheduler without detail", fail("scheduler", both), False),
        case("guest failure", fail("guest-failure", both, detail(10)), True),
        case("guest failure without detail", fail("guest-failure", both),
             False),
        case("resume", fail("resume", both), True),
        case("resume with a detail", fail("resume", both, detail(10)),
             False),
        case("console", fail("console", both), True),
        case("console with a detail", fail("console", both, detail(10)),
             False),
        case("shutdown returned", fail(
            "shutdown-returned", lines, SRST_RETURNED, after="BE_B7:11"),
            True),
        case("detail without exits", fail(
            "virtual-instruction", both,
            detail(22, tval=RDCYCLE).rsplit(" ", 1)[0]), False),
        case("detail in upper case", fail(
            "virtual-instruction", both,
            detail(22, tval=RDCYCLE).replace("0x16", "0X16")), False),
        case("detail with spvp=2", fail(
            "virtual-instruction", both,
            detail(22, tval=RDCYCLE).replace("spvp=1", "spvp=2")), False),
        case("detail without its guest (B6's format)", fail(
            "virtual-instruction", both,
            detail(22, tval=RDCYCLE).replace("guest=0 ", "")), False),
        ("class differs", sample(r3 + [FAIL_PREFIX + "gstage"]),
         dict(pins, expect_fail="sstc"), False),
        ("unknown class", sample(r3 + [FAIL_PREFIX + "bogus"]),
         dict(pins, expect_fail="bogus"), False),
        ("class with trailing text", sample(r3 + [FAIL_PREFIX + "gstage x"]),
         dict(pins, expect_fail="gstage"), False),
        case("failure after a skipped line", fail(
            "boot", shim + [R3_SEQUENCE[0], R3_SEQUENCE[2]]), False),
        case("guest line before G0's BE_B7:08", fail(
            "sstc", lines[:index_of["BE_B7:02"] + 1] +
            [GUEST_PREFIXES[0] + stamp(0) + FIXTURE_PINS.banner]), False),
        case("G1 line before its entry in a failure", fail(
            "exit-budget", g0_only + [GUEST_PREFIXES[1] + "early"],
            detail(10)), False),
        case("two SRST returned", fail(
            "gstage", r3, SRST_RETURNED, SRST_RETURNED), False),
        case("marker after the failure", fail(
            "gstage", r3, PRE_RUN[0]), False),
        case("guest line after the failure", fail(
            "exit-budget", both, detail(10), GUEST_PREFIXES[0] + "late"),
            False),
        case("two failures", fail("gstage", r3, FAIL_PREFIX + "gstage"),
             False),
        ("detail before the failure", sample(both + [
            detail(21), FAIL_PREFIX + "guest-page-fault"]),
         dict(pins, expect_fail="guest-page-fault"), False),
        ("noise after the failure", sample(r3 + [FAIL_PREFIX + "gstage"],
                                           after="garbage\r\n"),
         dict(pins, expect_fail="gstage"), False),
        ("pass is not a failure", sample(lines),
         dict(pins, expect_fail="gstage"), False),
        ("--sbi-time on a failure", sample(r3 + [FAIL_PREFIX + "gstage"]),
         dict(pins, expect_fail="gstage", sbi_time=True), False),
        ("--guest without a detail", sample(
            lines[:index_of["BE_B7:02"] + 1] + [FAIL_PREFIX + "sstc"]),
         dict(pins, expect_fail="sstc", guest=0), False),
        ("failure after BE_B7:06 without pins", sample(
            head + [FAIL_PREFIX + "exit-budget", detail(10)]),
         {"expect_fail": "exit-budget"}, False),
        ("failure before BE_B7:06 without pins", sample(
            armed + [FAIL_PREFIX + "payload"]),
         {"expect_fail": "payload"}, True),
    ]


# Self-test fixtures for the source checks (the real check reads the
# accepted plans and the B7 sources).
FIXTURE_K3 = ("virt,aia=aplic-imsic,aia-guests=7",
              "rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,"
              "sv57=off,smstateen=true")
FIXTURE_R5_CPU = ("rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,"
                  "sv57=off,sstc=false,smstateen=false,svadu=false,"
                  "debug=false")
FIXTURE_SCENARIOS = (
    "k3-like $k3_machine $k3_cpu opensbi 2.0 pass - - - -",
    "rva23 virt,aia=aplic-imsic rva23s64 opensbi 2.0 pass - - - -",
    "plic virt rv64,h=true opensbi 2.0 pass - - - -",
    "no-sstc virt,aia=none $minimal opensbi 2.0 sstc BE_B7:02 - - -",
    "sbi-3.0 $k3_machine $k3_cpu default 3.0 boot none - - -",
)
FIXTURE_VARIANTS = (
    "sbi-time pass - - - sbi-time",
    "payload payload BE_B7:04 - - -",
    "init-exit guest-reboot BE_B7:08 1 - -",
    "rdcycle virtual-instruction BE_B7:08 0 22 tval-not-wfi",
    "exit-budget exit-budget BE_B7:08 - - -",
    "guest-timeout guest-timeout BE_B7:08 - - -",
)


def runtime_fixture():
    out = ["/* BE_B7:12 FUTURE is a comment, not a literal */",
           '#include "b7.h"']
    out += [f'static const char r3_{index}[] = "{line}\\n";'
            for index, line in enumerate(R3_SEQUENCE)]
    for index, line in enumerate(RUNTIME_LINES):
        fixed = fixed_text(line)
        if index == 1:
            # Adjacent literals with a comment between them, joined by C.
            fixed = f'{fixed[:12]}" /* joined */\n\t"{fixed[12:]}'
        out.append(f'static const char b7_{index}[] = "{fixed}";')
        out += [f'static const char b7_{index}_{field}[] = "{name}";'
                for field, name in enumerate(field_names(line))]
    out += [f'static const char text_{index}[] = "{text}";'
            for index, text in enumerate(FAILURE_TEXTS)]
    out += [f'static const char tag_{guest}[] = "{prefix}";'
            for guest, prefix in enumerate(GUEST_PREFIXES)]
    out.append("static const char *const classes[] = { " +
               ", ".join(f'"{klass}"' for klass in CLASSES) + " };")
    out.append("static const char quote = '\"';")
    return "\n".join(out) + "\n"


def init_fixture():
    return ('#include "b7-guest-id.h"\n'
            'static void lines(void)\n{\n'
            '\tsay("B7INIT 01 START guest=%d pid=%d", guest, pid);\n'
            '\tsay("B7INIT 02 UNAME release=%s machine=%s", r, m);\n'
            '\tsay("B7INIT 03 STEP n=%lu/%lu rounds=%lu t_ms=%lu", n, s,\n'
            '\t    rounds, now);\n'
            '\tsay("B7INIT 04 SLEEP requested_ms=%lu elapsed_ms=%lu "\n'
            '\t    "ok=%d", ms, elapsed, ok);\n'
            '\tsay("B7INIT 05 RESULT %s", failed ? "fail" : "pass");\n'
            '\tsay("B7INIT 06 POWER_OFF");\n}\n')


def plan_fixture():
    """A B7 plan with the parts the source check reads."""
    shutdown = GUEST_SHUTDOWN.split(" base=")
    entry = ENTER_G1.split(" a1=")
    return (
        "## Markers\n\nA passing capture holds B3's `SHIM` line (as in B6), "
        "then these lines in\nthis order:\n\n```text\n" +
        "\n".join(MONITOR_TEMPLATE) + "\n```\n\nBetween G0's `BE_B7:08` "
        f"and `BE_B7:10` come both guests' lines and three\nmore monitor "
        f"lines: `{entry[0]}\na1={entry[1]}` before G1's first line, "
        f"and after each guest's last line\n`{shutdown[0]}\nbase="
        f"{shutdown[1]}`. Each guest's lines must hold:\n\n```text\n" +
        "\n".join(GUEST_TEMPLATE) + "\n```\n\n"
        "- **Interleaving (Q5):**\n  - at least K = 8 alternations, where "
        "an alternation is a guest line\n"
        "- **Rejected:** B6's rejected substrings in any guest line; more.\n"
        "- **Failures:** `BE_B7:FAIL <class>`, then a `DETAIL` line with "
        "`guest=<g>`\n  where a guest is involved. The classes are B6's,\n"
        "  with `interrupt` now meaning any interrupt but the supervisor "
        "timer,\n  plus `switch` and `scheduler`. The run tools' terminal "
        f"regex is\n  `{TERMINAL_REGEX}`.\n\n## Tests and evidence\n\n"
        "**QEMU scenarios:** B6's machines and CPUs, QEMU 10.2.2.\n\n"
        "| Scenario | Toolchains | Expected |\n| --- | --- | --- |\n"
        "| `k3-like`, `rva23`, `plic` | GCC, Clang | Pass |\n"
        "| `no-sstc` (the accepted R5 CPU, as in B5 and B6) | GCC, Clang | "
        "`BE_B7:FAIL sstc` after `BE_B7:02` |\n"
        "| `sbi-3.0` (QEMU's OpenSBI 1.7) | GCC, Clang | `BE_B7:FAIL boot` "
        "before `BE_R3:01` |\n"
        "| `sbi-time` (both DTBs without `sstc`) | GCC | Pass, with `time` "
        "above 0 for each guest |\n"
        "| `payload` (kernel `magic2` altered) | GCC | `BE_B7:FAIL payload` "
        "after `BE_B7:04` |\n"
        "| `init-exit` (G1 `rdinit=/init-exit`) | GCC | `BE_B7:FAIL "
        "guest-reboot`, `guest=1` |\n"
        "| `rdcycle` (G0 `rdinit=/init-rdcycle`) | GCC | `BE_B7:FAIL "
        "virtual-instruction`, `guest=0`, cause 22, `tval` not `wfi` |\n"
        "| `exit-budget` (per-guest ceiling 64) | GCC | `BE_B7:FAIL "
        "exit-budget` |\n"
        "| `guest-timeout` (budget 2^20 ticks) | GCC | `BE_B7:FAIL "
        "guest-timeout` |\n\nB6's `memory` variant is not carried over.\n\n"
        "## Accepted decisions B7 departs from\n")


def b6_plan_fixture():
    """A B6 plan with the parts B7 takes from it."""
    classes = ", ".join(f"`{klass}`" for klass in B6_CLASSES)
    rejected = ", ".join(f"`{pattern}`" for pattern in REJECTED)
    shim = SHIM_FIXED
    return (f"| `k3-like` | `{FIXTURE_K3[0]}`; `{FIXTURE_K3[1]}` | GCC | x |\n"
            f"| `rva23` | `virt,aia=aplic-imsic`; `rva23s64` | GCC | x |\n"
            f"| `plic` | `virt`; `rv64,h=true` | GCC | x |\n\n"
            f"## Markers\n\nEach run first prints B3's `SHIM` "
            f"line, which must show\n`{shim[0]}`, `{shim[1]}`, and\n"
            f"`{shim[2]}`.\n\n"
            f"- **Rejected** in any guest line, as case-sensitive\n"
            f"  substrings: {rejected.replace('`Oops`', '(x) `Oops`')}. "
            f"Also rejected: more.\n"
            f"- A failure adds\n\n  `{B6_DETAIL_TEMPLATE}`.\n\n"
            f"- Classes: {classes} (as R5 uses `import`). The run tools'\n"
            f"  terminal regex is `BE_B6:09 SHUTDOWN|BE_B6:FAIL|BE_K3_B3: "
            f"FAIL`.\n")


def tools_fixture():
    scenarios = "\n".join(f'\t"{row}"' for row in FIXTURE_SCENARIOS)
    variants = "\n".join(f"\t'{row}'" for row in FIXTURE_VARIANTS)
    return {
        "run-qemu.sh": (
            f"terminal_regex='{TERMINAL_REGEX}'\n"
            f"k3_machine='{FIXTURE_K3[0]}'\nk3_cpu='{FIXTURE_K3[1]}'\n"
            f"minimal='{FIXTURE_R5_CPU}'\nscenarios=(\n{scenarios}\n)\n"
            f"variants=(\n{variants}\n)\n"),
        "kexec-rehearsal.sh": (
            f"terminal_regex='{TERMINAL_REGEX}|BE_B7_KEXEC: FAIL'\n"
            f"k3_machine='{FIXTURE_K3[0]}'\nk3_cpu='{FIXTURE_K3[1]}'\n"),
        "k3-run.sh": f"terminal_regex='{TERMINAL_REGEX}'\n",
    }


def source_cases():
    runtime = runtime_fixture()
    init = init_fixture()
    r5 = "\n".join(f'"{line}\\n"' for line in R3_SEQUENCE + (
        R3_DROPPED, "BE_R4:01 ENTRY_ARMED_IMPORTED")) + '\n"BE_R5:FAIL "\n'
    plan = plan_fixture()
    b6_plan = b6_plan_fixture()
    b5 = f"minimal='{FIXTURE_R5_CPU}'\n"
    tools = tools_fixture()

    def tool(name, text):
        return dict(tools, **{name: text})

    def runner(old, new):
        return tool("run-qemu.sh", tools["run-qemu.sh"].replace(old, new))

    header = f'#define TAG0 "{GUEST_PREFIXES[0]}"\n'
    untagged = runtime.replace(GUEST_PREFIXES[0], "TAG: ")

    def b7_case(name, runtime_text, init_text, wanted, headers=(),
                require=False):
        sources = ([runtime_text] if runtime_text else []) + list(headers)
        return name, (runtime_text, init_text, sources, require), wanted

    b7 = [
        b7_case("B7 sources complete", runtime, init, True),
        b7_case("G0's tag only in a header", untagged, init, True,
                [header]),
        b7_case("b7-runtime.c missing: skipped", None, init, True),
        b7_case("b7-runtime.c missing, --require-runtime", None, init, False,
                require=True),
        b7_case("b7-init.c missing: skipped", runtime, None, True),
        b7_case("no G0 tag literal", untagged, init, False),
        b7_case("BE_B7:05 misspelt", runtime.replace(
            "RAM_CLEARED", "RAM_CLEAR"), init, False),
        b7_case("a field name missing", runtime.replace(
            '" idle_ticks="', '" idle="'), init, False),
        b7_case("a detail field missing", runtime.replace(
            '" htinst="', '" inst="'), init, False),
        b7_case("the switch detail missing", runtime.replace(
            '" register="', '" reg="'), init, False),
        b7_case("BE_R3:07 kept", runtime + f'"{R3_DROPPED}\\n";\n', init,
                False),
        b7_case("a B6 marker left over", runtime +
                '"BE_B6:08 GUEST_SHUTDOWN type=";\n', init, False),
        b7_case("an extra BE_B7 marker in a header", runtime, init, False,
                ['#define EXTRA "BE_B7:12 EXTRA\\n"\n']),
        b7_case("a fixed text only in a comment", runtime.replace(
            '"BE_B7:03 SSTC_STCE_READBACK henvcfg=";', "0; /* BE_B7:03 "
            "SSTC_STCE_READBACK henvcfg= */"), init, False),
        b7_case("the scheduler class without a literal", runtime.replace(
            ', "scheduler"', ""), init, False),
        b7_case("the switch class without a literal", runtime.replace(
            '"switch", ', ""), init, False),
        b7_case("init source forging a tag", runtime,
                init + '"BE_B7_G1: B7INIT 01 START";\n', False),
        b7_case("init source without its step line", runtime, init.replace(
            "B7INIT 03 STEP", "B7INIT 03 STEPS"), False),
        b7_case("init source without the result line", runtime, init.replace(
            "B7INIT 05 RESULT %s", "B7INIT 05 %s"), False),
    ]
    plans = [
        ("accepted inputs and tools agree", (r5, plan, b6_plan, b5, tools),
         True),
        ("an R3 literal differs", (r5.replace("R1_DERIVED", "R1"), plan,
                                   b6_plan, b5, tools), False),
        ("BE_R3:07 not in the accepted source", (r5.replace(
            R3_DROPPED, "BE_R3:08 X"), plan, b6_plan, b5, tools), False),
        ("the first Markers block differs", (r5, plan.replace(
            "slice_ticks=0x3a980", "slice_ticks=0x3a981"), b6_plan, b5,
            tools), False),
        ("the guest block differs", (r5, plan.replace(
            "B7INIT 06 POWER_OFF", "B7INIT 06 POWEROFF"), b6_plan, b5,
            tools), False),
        ("G1's entry line differs", (r5, plan.replace(
            "a1=0x83e00000` before", "a1=0x83f00000` before"), b6_plan, b5,
            tools), False),
        ("the shutdown line differs", (r5, plan.replace(
            "refused=0\n", "refused=1\n").replace(
            "refused=0 ticks", "refused=1 ticks"), b6_plan, b5, tools),
         False),
        ("a third Markers block", (r5, plan.replace(
            "## Tests and evidence", "```text\nx\n```\n\n## Tests and "
            "evidence"), b6_plan, b5, tools), False),
        ("an added class differs", (r5, plan.replace(
            "`scheduler`", "`sched`"), b6_plan, b5, tools), False),
        ("a B6 class differs", (r5, plan, b6_plan.replace(
            "`console`", "`uart`"), b5, tools), False),
        ("K differs", (r5, plan.replace("K = 8", "K = 6"), b6_plan, b5,
                       tools), False),
        ("the terminal regex differs", (r5, plan.replace(
            "BE_K3_B3: FAIL`", "BE_K3_B3:FAIL`"), b6_plan, b5, tools), False),
        ("an inherited sentence missing", (r5, plan.replace(
            "B6's rejected substrings", "these substrings"), b6_plan, b5,
            tools), False),
        ("a rejected pattern differs", (r5, plan, b6_plan.replace(
            "`segfault`", "`segv`"), b5, tools), False),
        ("the B6 DETAIL line differs", (r5, plan, b6_plan.replace(
            "spvp=<0|1>", "spv=<0|1>"), b5, tools), False),
        ("a SHIM value differs", (r5, plan, b6_plan.replace(
            SHIM_FIXED[1], "dest=0x0000000102200000"), b5, tools), False),
        ("a plan scenario differs", (r5, plan.replace(
            "`BE_B7:FAIL payload` after `BE_B7:04`",
            "`BE_B7:FAIL payload` after `BE_B7:05`"), b6_plan, b5, tools),
         False),
        ("the plan drops a scenario", (r5, plan.replace(
            "| `guest-timeout` (budget", "| guest-timeout (budget"),
            b6_plan, b5, tools), False),
        ("a variant class differs", (r5, plan, b6_plan, b5, runner(
            "'rdcycle virtual-instruction", "'rdcycle illegal-instruction")),
         False),
        ("a variant cause differs", (r5, plan, b6_plan, b5, runner(
            "BE_B7:08 0 22", "BE_B7:08 0 2")), False),
        ("a variant guest differs", (r5, plan, b6_plan, b5, runner(
            "guest-reboot BE_B7:08 1", "guest-reboot BE_B7:08 0")), False),
        ("the rdcycle tval check missing", (r5, plan, b6_plan, b5, runner(
            "22 tval-not-wfi", "22 -")), False),
        ("the sbi-time check missing", (r5, plan, b6_plan, b5, runner(
            "'sbi-time pass - - - sbi-time'", "'sbi-time pass - - - -'")),
         False),
        ("the payload variant after another line", (r5, plan, b6_plan, b5,
                                                    runner(
            "'payload payload BE_B7:04", "'payload payload BE_B7:05")),
         False),
        ("a variant after an unknown line", (r5, plan, b6_plan, b5, runner(
            "exit-budget BE_B7:08", "exit-budget BE_B7:09")), False),
        ("the no-sstc run after another line", (r5, plan, b6_plan, b5,
                                                runner("sstc BE_B7:02",
                                                       "sstc BE_B7:03")),
         False),
        ("the sbi-3.0 run after BE_R3:01", (r5, plan, b6_plan, b5, runner(
            "boot none", "boot BE_R3:01")), False),
        ("the sbi-3.0 run on OpenSBI 1.6", (r5, plan, b6_plan, b5, runner(
            "default 3.0", "opensbi 3.0")), False),
        ("a scenario on GCC only", (r5, plan, b6_plan, b5, runner(
            '\t"plic virt rv64,h=true opensbi 2.0 pass - - - -"\n', "")),
         False),
        ("a malformed scenario row", (r5, plan, b6_plan, b5, runner(
            "plic virt rv64,h=true opensbi", "plic virt rv64,h=true")),
         False),
        ("an extra variant", (r5, plan, b6_plan, b5, runner(
            "\t'payload payload", "\t'memory guest-page-fault BE_B7:08 - - "
            "-'\n\t'payload payload")), False),
        ("the R5 CPU differs", (r5, plan, b6_plan, b5, runner(
            "debug=false", "debug=true")), False),
        ("the k3-like CPU differs", (r5, plan, b6_plan, b5, runner(
            "svade=true,", "")), False),
        ("the plic row on another CPU", (r5, plan, b6_plan, b5, runner(
            "plic virt rv64,h=true", "plic virt rv64")), False),
        ("the rehearsal machine differs", (r5, plan, b6_plan, b5, tool(
            "kexec-rehearsal.sh", tools["kexec-rehearsal.sh"].replace(
                "aia-guests=7", "aia-guests=5"))), False),
        ("a board tool lacks the regex", (r5, plan, b6_plan, b5, tool(
            "k3-run.sh", "terminal_regex='BE_B7:11'\n")), False),
        ("a run tool is missing", (r5, plan, b6_plan, b5, tool(
            "kexec-rehearsal.sh", None)), False),
    ]
    return b7, plans


def pins_text(pins=FIXTURE_PINS, **changes):
    lines = {
        "image": f"file build/k3-b7/guest/linux/Image sha256={'a' * 64} "
                 f"bytes={pins.kernel_bytes}",
        "init": f"file init sha256={'b' * 64} bytes=4096",
        "image_size": f"kernel image_size=0x{pins.image_size:x}",
        "text_offset": f"kernel text_offset=0x"
                       f"{LAYOUT['KERNEL_TEXT_OFFSET']:x}",
        "banner": f"kernel banner={pins.banner}",
    }
    lines.update(changes)
    return "# B7 guest pins\n" + "\n".join(
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
                   fields.get("exits_g0") == "503" and
                   fields.get("exits_g1") == "495" and
                   fields.get("elapsed_ms_g0") == "1003" and
                   fields.get("elapsed_ms_g1") == "1003" and
                   fields.get("switches") == "261" and
                   fields.get("wfi_switches") == "233" and
                   fields.get("slice_switches") == "27" and
                   fields.get("alternations") == "55" and
                   fields.get("hgatp") == f"g1=0x{HGATPS[1]:x} "
                   f"g0=0x{HGATPS[0]:x}" and
                   fields.get("gstage_g1") == f"guest=1 {window_line(1)}" and
                   fields.get("guest_entry_g1") == ENTER_G1.split(" ", 2)[2]
                   and fields.get("shutdown") == "type=0 reason=0" and
                   all(isinstance(value, str) for value in fields.values())))
    entry = lines.index(entry_line(0))
    failed = sample(lines[:entry + 3] + [
        FAIL_PREFIX + "exit-budget", detail(10, exits=65), SRST_RETURNED])
    fields = result_record("x", "fail", extract(failed), True,
                           [])["fields"]
    checks.append(("failure fields", fields.get("failure") ==
                   "exit-budget" and fields.get("detail") ==
                   detail(10, exits=65)[len(DETAIL_PREFIX):] and
                   fields.get("srst_returned") == "yes" and
                   fields.get("alternations") == "0"))
    checks.append(("counts printed", counts_report(extract(good)) ==
                   "BE_B7_COUNTS: g0_exits=503 g0_sbi=210 g0_wfi=262 "
                   "g0_slice=31 g1_exits=495 g1_sbi=208 g1_wfi=258 "
                   "g1_slice=29 switches=261 wfi_switches=233 "
                   "slice_switches=27 stop_switches=1 idle_waits=41 "
                   "alternations=55"))
    checks.append(("no counts before the run", counts_report(
        extract(failed)) is None))
    checks.append(("19 fixed lines, 13 guest lines, 20 line IDs",
                   len(FIXED) == 19 and RUN_AT == 17 and
                   len(GUEST_TEMPLATE) == 13 and len(LINE_IDS) == 20 and
                   len(guest_template(0)) == 20 and
                   LINE_IDS[RUN_AT] == "BE_B7:08" and
                   LINE_IDS[2 + len(R3_SEQUENCE)] == "BE_B7:01/g1"))
    checks.append(("20 classes, 10 with an exit detail",
                   len(CLASSES) == 20 and len(set(CLASSES)) == 20 and
                   len(DETAIL_REQUIRED) == 10 and
                   set(DETAIL_REQUIRED + DETAIL_OPTIONAL) < set(CLASSES)))
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
                   layout["G0_ROOT_HPA"] == layout["POOL_HPA"] and
                   layout["G1_HPA"] == layout["G0_HPA"] +
                   layout["GUEST_BYTES"] and
                   layout["GUEST_LEAVES"] * 0x200000 ==
                   layout["GUEST_BYTES"] and layout["DTB_GPA"] ==
                   layout["GUEST_GPA"] + layout["GUEST_BYTES"] - 0x200000 and
                   layout["G0_HGATP"] >> 44 & 0x3fff == 1 and
                   layout["G1_HGATP"] >> 44 & 0x3fff == 2 and
                   layout["SLICE_TICKS"] * 100 == 24000000))
    for name, text in (("missing", header.replace("BE_B7_G1_HGATP", "X")),
                       ("twice", header + "#define BE_B7_G0_HGATP\t"
                                          "BE_B7_C(0x1)\n")):
        try:
            parse_layout(text, "x")
            checks.append((f"layout refused: {name}", False))
        except ValueError:
            checks.append((f"layout refused: {name}", True))
    patterns = [template_pattern(line, FIXTURE_PINS) for line in FIXED]
    checks.append(("the fixture fills every fixed line", all(
        any(pattern.fullmatch(line) for line in lines)
        for pattern in patterns[:-2]) and
        run_counters(lines[-2]) == (dict(FIXTURE_RUN, switches=261), []) and
        lines[-1] == SHUTDOWN))
    checks.append(("the fixture fills every guest line", all(
        any(template_pattern(line, FIXTURE_PINS).fullmatch(body)
            for body in guest_lines(guest))
        for guest in GUESTS for line in guest_template(guest))))
    checks.append(("shutdown counters", shutdown_counters(
        shutdown_line(1)) == (dict(FIXTURE_COUNTERS[1], guest=1, sbi=208,
                                   exits=495,
                                   ticks=FIXTURE_SHUTDOWN_TICKS[1]), [])))
    checks.append(("alternations", alternations((0, 0, 1, 1, 0, 1)) == 3 and
                   alternations(()) == 0 and alternations(ORDER_8) == 8 and
                   alternations(ORDER_7) == 7))
    checks.append(("mixed lines", mixed("[    0.1] a") is None and
                   mixed("B7INIT 01 x") is None and
                   mixed("[    0.1] aB7INIT 01") is not None and
                   mixed("x[    0.100000] y") is not None and
                   mixed("printk: console [hvc0] enabled") is None))
    checks.append(("C literals", c_literals(
        '"a\\x41\\102\\n" "b" /* "c" */ "d" \'"\' "e" // "f"\n"g"') ==
        ["aAB\nbd", "eg"]))
    try:
        c_literals('x = "abc')
        checks.append(("unterminated literal", False))
    except ValueError:
        checks.append(("unterminated literal", True))
    checks.append(("field names", field_names(GUEST_SHUTDOWN) == (
        " exits=", " sbi=", " wfi=", " slice=", " base=", " time=",
        " dbcn_write=", " dbcn_read=", " dbcn_byte=", " srst=", " refused=",
        " ticks=")))
    plan = plan_fixture()
    tools = tools_fixture()
    checks.append(("plan parsers", plan_markers(plan) == (
        MONITOR_TEMPLATE, GUEST_TEMPLATE) and
        plan_run_lines(plan) == (ENTER_G1, GUEST_SHUTDOWN) and
        plan_b7_classes(plan) == (("switch", "scheduler"), TERMINAL_REGEX,
                                  ALTERNATIONS_MIN) and
        plan_b6_classes(b6_plan_fixture())[0] == B6_CLASSES and
        plan_rejected(b6_plan_fixture()) == REJECTED and
        plan_detail(b6_plan_fixture()) == B6_DETAIL_TEMPLATE and
        plan_shim(b6_plan_fixture()) == SHIM_FIXED and
        plan_scenarios(b6_plan_fixture())["k3-like"] == FIXTURE_K3))
    planned = plan_qemu(plan)
    ran = runner_scenarios(tools["run-qemu.sh"])
    checks.append(("QEMU table parsers", len(planned) == 11 and
                   planned["rdcycle"] == Outcome(("gcc",),
                                                 "virtual-instruction", None,
                                                 0, 22, "tval-not-wfi") and
                   planned["sbi-3.0"] == Outcome(("clang", "gcc"), "boot",
                                                 "none", None, None, None) and
                   planned["no-sstc"].after == "BE_B7:02" and
                   planned["sbi-time"].check == "sbi-time" and
                   ran["no-sstc"][1:] == ("virt,aia=none", FIXTURE_R5_CPU,
                                          "opensbi", "2.0") and
                   ran["init-exit"][0].guest == 1 and
                   ran["k3-like"][1:3] == FIXTURE_K3))
    return checks


# A realistic fixture: one QEMU k3-like run of the GCC B7 image (see its
# header). Its pins are its own lines.
REALISTIC = HERE / "fixtures" / "qemu-k3-like.console.log"


def realistic_pins(text):
    """Pins from a capture's own BE_B7:06 and `Linux version` lines."""
    sizes = re.search(r"kernel_bytes=(0x[0-9a-f]+) image_size=(0x[0-9a-f]+) ",
                      text)
    banner = re.search(rf"{re.escape(GUEST_PREFIXES[0])}\[ *[0-9.]+\] "
                       rf"(Linux version {re.escape(RELEASE)} [ -~]+)", text)
    return Pins(int(sizes.group(1), 16), int(sizes.group(2), 16),
                banner.group(1))


def realistic_cases():
    """(name, text, options, wanted) for the realistic fixture."""
    # The file has LF line ends; serial captures have CRLF.
    text = REALISTIC.read_bytes().decode("ascii").replace("\n", "\r\n")
    pins = {"pins": realistic_pins(text)}
    run_init = next(line for line in text.split("\r\n")
                    if line.startswith(GUEST_PREFIXES[1]) and
                    line.endswith("Run /init as init process"))
    warning = (GUEST_PREFIXES[1] + "[    0.112000] WARNING: CPU: 0 PID: 1 at "
               "init/main.c:1 kernel_init+0x0/0x0")
    swapped = text.replace(GUEST_PREFIXES[0], "SWAP").replace(
        GUEST_PREFIXES[1], GUEST_PREFIXES[0]).replace("SWAP",
                                                      GUEST_PREFIXES[1])
    return [
        ("realistic QEMU capture", text, pins, True),
        ("realistic, LF only", text.replace("\r", ""), pins, True),
        ("realistic, B6's SBI identity", text.replace(
            "ID=0x4245 Version=0x3", "ID=0x4245 Version=0x2"), pins, False),
        ("realistic, an untagged kernel line", text.replace(
            run_init, run_init[len(GUEST_PREFIXES[1]):]), pins, False),
        ("realistic, a WARNING splat", text.replace(
            run_init, run_init + "\r\n" + warning), pins, False),
        ("realistic, ending before the run completes",
         text[:text.index("BE_B7:10 ")], pins, False),
        ("realistic, the guests' prefixes swapped", swapped, pins, False),
        ("realistic, other pins", text, {"pins": FIXTURE_PINS}, False),
    ]


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
    entry = lines.index(entry_line(0))
    records = [
        ("record pass", good, None, "PASS", "PASS", "shutdown-requested"),
        ("record failure after pass", sample(lines + [
            FAIL_PREFIX + "resume"]), None, "FAIL", "FAIL", "fail-marker"),
        ("record truncated", sample(lines[:-1]), None, "FAIL", "FAIL",
         "none"),
        ("record guests stopped mid-run", sample(lines[:entry + 30]), None,
         "FAIL", "FAIL", "none"),
        ("record forged extra", sample(lines + ["BE_B7:12 EXTRA"]), None,
         "FAIL", "PASS", "none"),
        ("record no-sstc", sample(lines[:lines.index(PRE_RUN[2]) + 1] + [
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
    b7_cases, plan_cases = source_cases()
    for name, arguments, wanted in b7_cases:
        findings, notes = b7_source_findings(*arguments)
        failed += (not findings) != wanted
        print(f"{'ok  ' if (not findings) == wanted else 'FAIL'} sources: "
              f"{name}: findings={findings[:3]} notes={notes}")
    for name, arguments, wanted in plan_cases:
        findings = plan_tool_findings(*arguments)
        failed += (not findings) != wanted
        print(f"{'ok  ' if (not findings) == wanted else 'FAIL'} plan and "
              f"tools: {name}: findings={findings[:3]}")
    total = len(cases) + len(records) + len(checks) + len(b7_cases) + \
        len(plan_cases)
    print(f"BE_B7_MARKER_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
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
    parser.add_argument("--guest", type=int, choices=GUESTS)
    parser.add_argument("--cause", type=number)
    parser.add_argument("--tval-not-wfi", action="store_true")
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
                            args.after, args.guest, args.cause,
                            args.tval_not_wfi)
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
    report = counts_report(markers)
    if report:
        print(report)
    if not args.expect_fail:
        print(f"BE_B7_MARKER_RESULT: {record['boot_marker']} "
              f"terminal={record['terminal']}")
    print(f"BE_B7_MARKERS[{args.toolchain or '-'}/{expect}]: "
          f"{record['result']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
