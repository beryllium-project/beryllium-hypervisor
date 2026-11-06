#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Validate B5 console markers from a QEMU or K3 serial capture.

B5 runs the accepted R3 boot and first entry (BE_R3:01-07), checks and arms
the guest controls (BE_B5:01-04), runs the separately built B5 guest, whose
console lines the monitor tags with `BE_B5_GUEST: ` (guest lines 01-09),
and ends with the guest's SRST shutdown (BE_B5:05-06). The expected lines
are the Markers block of the accepted plan planning/k3-b5-plan.md
(c3f8ef51); the R3 lines are the marker literals of accepted R5
arch/riscv/be/r5-runtime.c (165f4d00).

  check-b5-markers.py --capture FILE --expect pass|fail:CLASS
                      [--toolchain gcc|clang] [--after LINE] [--cause N]
                      [--json F]
  check-b5-markers.py --self-test
  check-b5-markers.py --check-sources REPO_ROOT

Marker lines run from a tag (BE_R3:, BE_R4:, BE_R5:, BE_B5:, or
`BE_B5_GUEST: `) to the end of the line; trailing CRs are dropped. From the
first marker line to the end of the capture, every non-blank line must be a
marker line that starts with its tag; every marker line must be printable
ASCII (0x20-0x7e); a guest line must not hold any tag after its prefix; and
no line may hold an untagged guest line.

--expect pass requires exactly the 22 lines of the Markers block, in order,
and nothing after BE_B5:06. `exits=<N>` is decimal, from 1 to the exit
budget of 1024; EXPECTED_EXITS pins it once integration has fixed it (None:
any such N passes, and the checker prints it).

--expect fail:CLASS requires exactly one `BE_B5:FAIL CLASS`, CLASS one of
the plan's classes. The BE_R3/BE_B5 lines before it must be a prefix of the
pass sequence; guest lines may appear only between BE_B5:04 and BE_B5:05
and are not otherwise fixed. The four guest-exit classes (interrupt,
guest-page-fault, virtual-instruction, illegal-instruction) need
`BE_B5:DETAIL cause=0x.. pc=0x.. tval=0x.. htval=0x..` next, with a cause
that fits the class and, for a guest-page fault, htval 0 or tval >> 2.
exception, exit-budget, resume, and console may have it: exception has it
for any other guest exit, and lacks it when a monitor integrity check (a
trap on a bad stack, or a frame that is not the management saved page)
fails with no guest exit to describe. The other classes must not have it.
At most `BE_B5:SRST_RETURNED` may follow. --after LINE requires the last
BE_R3/BE_B5 line before the failure to be LINE (for example BE_R3:07 or
BE_B5:04; `none` when no such line precedes it); --cause N requires the
DETAIL cause N.

--check-sources reads accepted r5-runtime.c, the accepted plan, and accepted
B2 tests/run-qemu.sh (for the R5 CPU) with `git -C REPO_ROOT show
COMMIT:PATH`, each SHA-256 pinned, and requires the R3 literals, the
Markers block, the class list, the terminal regex, the negative variants,
and the scenario flags to match this checker and the B5 run tools. It then
requires that bringup/k3-b5/src/b5-runtime.c holds every BE_R3 line, the
fixed text of every BE_B5 line (up to and including its first `=`, or the
whole line), and the failure literals; that bringup/k3-b5/guest/guest.c
holds the fixed text of every guest line and no tag; and that the literals
of bringup/k3-b5/src/ hold the guest tag and every class name, and no
numbered BE_R3/BE_B5 marker outside the plan. A missing B5 source is
reported as missing.

The JSON keeps B2's record (result, boot_marker, terminal, findings,
fields, markers), adding toolchain; fields holds each marker's arguments,
exits, and any failure, detail, and srst_returned.
"""

import argparse
import ast
import hashlib
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
B5_BASE = 0x102000000
B5_HART = 0
GUEST_PREFIX = "BE_B5_GUEST: "
TAGS = ("BE_R3:", "BE_R4:", "BE_R5:", "BE_B5:", GUEST_PREFIX)
# Tags guest output must never hold after its prefix.
GUEST_FORBIDDEN = TAGS + ("BE_K3_B3:",)
R3_SEQUENCE = (
    "BE_R3:01 BOOT_VALIDATED",
    "BE_R3:02 R1_DERIVED",
    "BE_R3:03 R2_BUILT_REWALKED",
    "BE_R3:04 HS_VS_STATE_VERIFIED",
    "BE_R3:05 BINDING_PREPARED",
    "BE_R3:06 HGATP_FENCED_PUBLISHED",
    "BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000",
)
B5_ENTRY = (
    "BE_B5:01 SSTC_STCE_READBACK henvcfg=0x8000000000000000",
    "BE_B5:02 GUEST_CONTROLS_CHECKED hstatus_controls=0x300180 "
    "hideleg=0x40 hcounteren=0x2 vstimecmp=0xffffffffffffffff",
    "BE_B5:03 GUEST_RAM_CLEARED private=0x40000000 shared=0x40002000",
    "BE_B5:04 ENTER_GUEST pc=0x40010000 sp=0x40001000",
)
# The guest writes these without the prefix; the monitor's tagger adds it.
GUEST_LINES = (
    "01 START hart=0x0 dtb=0x0",
    "02 BASE spec=0x2000000 impl=0x4245 version=0x1 mvendorid=0x0 "
    "marchid=0x0 mimpid=0x0",
    "03 PROBE base=1 time=1 dbcn=1 srst=1 hsm=0 ipi=0 rfence=0 legacy=0",
    "04 UNSUPPORTED eid=-2 fid=-2 legacy_putchar=-2",
    "05 DBCN_REFUSED unmapped=-3 cross=-3 high=-3 wrap=-3 read=-4",
    "06 WRITE_BYTE ok",
    "07 SRST_REFUSED type=-3 reason=-3 reboot=-2",
    "08 TIMER cause=0x8000000000000005 after_deadline=1 cleared=1",
    "09 RESULT pass",
)
GUEST_SEQUENCE = tuple(GUEST_PREFIX + line for line in GUEST_LINES)
EXITS_TEXT = "BE_B5:05 GUEST_SHUTDOWN type=0 reason=0 exits="
SHUTDOWN = "BE_B5:06 SHUTDOWN type=0 reason=0"
PASS_TEMPLATE = R3_SEQUENCE + B5_ENTRY + GUEST_SEQUENCE + \
    (EXITS_TEXT + "<N>", SHUTDOWN)
EXITS = re.compile(r"BE_B5:05 GUEST_SHUTDOWN type=0 reason=0 "
                   r"exits=([1-9][0-9]*)")
EXIT_BUDGET = 1024
# The guest exit count <N> of a pass run, pinned at integration (plan B5-4):
# the GCC and Clang guests both make 53 exits. None would mean not pinned:
# any N from 1 to EXIT_BUDGET passes, and the checker prints it.
EXPECTED_EXITS = 53
FAIL_PREFIX = "BE_B5:FAIL "
DETAIL_PREFIX = "BE_B5:DETAIL "
SRST_RETURNED = "BE_B5:SRST_RETURNED"
HEX = r"0x(?:0|[1-9a-f][0-9a-f]{0,15})"
DETAIL = re.compile(rf"BE_B5:DETAIL cause=({HEX}) pc=({HEX}) "
                    rf"tval=({HEX}) htval=({HEX})")
CLASSES = ("boot", "sstc", "controls", "interrupt", "guest-page-fault",
           "virtual-instruction", "illegal-instruction", "exception",
           "exit-budget", "resume", "console", "guest-failure",
           "shutdown-returned")
DETAIL_REQUIRED = ("interrupt", "guest-page-fault", "virtual-instruction",
                   "illegal-instruction")
DETAIL_OPTIONAL = ("exception", "exit-budget", "resume", "console")
INTERRUPT = 1 << 63
TERMINAL_REGEX = "BE_B5:06 SHUTDOWN|BE_B5:FAIL|BE_K3_B3: FAIL"
# BE_R3/BE_B5 lines in pass order; guest lines run after MONITOR[GUEST_AT - 1].
MONITOR = R3_SEQUENCE + B5_ENTRY + (EXITS_TEXT, SHUTDOWN)
GUEST_AT = len(R3_SEQUENCE) + len(B5_ENTRY)
LINE_IDS = ("none",) + tuple(line.split(" ", 1)[0] for line in MONITOR)
UNPREFIXED_GUEST = re.compile(
    r"(?<![0-9A-Za-z_])(?:" + "|".join(
        re.escape(" ".join(line.split(" ", 2)[:2])) for line in GUEST_LINES)
    + r")(?![0-9A-Za-z_])")
# Argument-bearing marker -> JSON field holding its arguments.
FIELD_PREFIXES = (
    ("BE_R3:07 ", "management_entry"),
    ("BE_B5:01 ", "sstc_readback"),
    ("BE_B5:02 ", "guest_controls"),
    ("BE_B5:03 ", "guest_ram"),
    ("BE_B5:04 ", "guest_entry"),
    ("BE_B5:05 ", "guest_shutdown"),
    ("BE_B5:06 ", "shutdown"),
)
GUEST_FIELDS = ("guest_start", "guest_base", "guest_probe",
                "guest_unsupported", "guest_dbcn_refused", "guest_write_byte",
                "guest_srst_refused", "guest_timer", "guest_result")


def pass_sequence(exits=None):
    """The 22 pass lines, with exits=<N> filled in when N is given."""
    count = "<N>" if exits is None else str(exits)
    return R3_SEQUENCE + B5_ENTRY + GUEST_SEQUENCE + \
        (EXITS_TEXT + count, SHUTDOWN)


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
            if UNPREFIXED_GUEST.search(line):
                problems.append(f"line {number}: guest line without the "
                                f"{GUEST_PREFIX!r} prefix: {line[:80]!r}")
            elif started and line.strip():
                problems.append(f"line {number}: non-marker text among or "
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


def exits_of(markers, expected_exits=EXPECTED_EXITS):
    """(N or None, findings) from the BE_B5:05 line, when there is one."""
    lines = [line for line in markers if line.startswith("BE_B5:05 ")]
    if not lines:
        return None, []
    match = EXITS.fullmatch(lines[0])
    if not match:
        return None, [f"BE_B5:05 exits is not a decimal count: "
                      f"{lines[0]!r}"]
    exits = int(match.group(1))
    findings = []
    if exits > EXIT_BUDGET:
        findings.append(f"exits={exits} exceeds the exit budget "
                        f"{EXIT_BUDGET}")
    if expected_exits is not None and exits != expected_exits:
        findings.append(f"exits={exits}, but EXPECTED_EXITS pins "
                        f"{expected_exits}")
    return exits, findings


def full_sequence_reached(markers, expected_exits=EXPECTED_EXITS):
    """The 22 pass lines, in order, and no failure line."""
    if any(is_failure(line) for line in markers):
        return False
    exits, findings = exits_of(markers, expected_exits)
    if exits is None or findings:
        return False
    return tuple(markers[:len(PASS_TEMPLATE)]) == pass_sequence(exits)


def terminal(markers):
    if any(is_failure(line) for line in markers):
        return "fail-marker"
    if markers and markers[-1] == SHUTDOWN:
        return "shutdown-requested"
    return "none"


def first_divergence(markers, wanted):
    for index, line in enumerate(wanted):
        if index >= len(markers):
            return f"missing {line!r} (line {index + 1})"
        if markers[index] != line:
            return f"line {index + 1} is {markers[index]!r}, expected {line!r}"
    extra = markers[len(wanted)]
    return f"unexpected line {len(wanted) + 1} {extra!r}"


def pass_prefix(lines, expected_exits=EXPECTED_EXITS):
    """(last BE_R3/BE_B5 line ID, findings) for the lines before a failure.

    They must follow the pass order; guest lines, not otherwise fixed, may
    appear only between BE_B5:04 and BE_B5:05."""
    findings = []
    slot = 0
    for index, line in enumerate(lines):
        if line.startswith(GUEST_PREFIX):
            if slot != GUEST_AT:
                findings.append(f"guest line {index + 1} {line!r} is outside "
                                f"the guest run")
                break
            continue
        if slot == len(MONITOR):
            findings.append(f"line {index + 1} {line!r} follows {SHUTDOWN!r}")
            break
        wanted = MONITOR[slot]
        if wanted == EXITS_TEXT:
            if not line.startswith("BE_B5:05 "):
                findings.append(f"line {index + 1} is {line!r}, expected "
                                f"{EXITS_TEXT + '<N>'!r}")
                break
            findings += exits_of([line], expected_exits)[1]
        elif line != wanted:
            findings.append(f"line {index + 1} is {line!r}, expected "
                            f"{wanted!r}")
            break
        slot += 1
    return LINE_IDS[slot], findings


def cause_finding(klass, cause, tval, htval):
    """A finding when an exit's cause or htval does not fit its class."""
    fits = {
        "interrupt": bool(cause & INTERRUPT),
        "guest-page-fault": cause in (20, 21, 23),
        "virtual-instruction": cause == 22,
        "illegal-instruction": cause == 2,
        "exception": not cause & INTERRUPT and
        cause not in (2, 10, 20, 21, 22, 23),
    }.get(klass, True)
    if not fits:
        return f"cause 0x{cause:x} does not fit class {klass}"
    if klass == "guest-page-fault" and htval not in (0, tval >> 2):
        return (f"htval 0x{htval:x} is neither 0 nor tval 0x{tval:x} >> 2 "
                f"(bare vsatp)")
    return None


def failure_findings(markers, klass, expected_exits=EXPECTED_EXITS,
                     after=None, cause=None):
    if klass not in CLASSES:
        return [f"unknown failure class {klass!r}"]
    failures = [index for index, line in enumerate(markers)
                if line.startswith(FAIL_PREFIX)]
    if not failures:
        return ["no BE_B5:FAIL line"]
    findings = []
    if len(failures) > 1:
        findings.append(f"{len(failures)} BE_B5:FAIL lines")
    first = failures[0]
    seen = markers[first][len(FAIL_PREFIX):]
    if seen != klass:
        findings.append(f"failure class {seen!r}, expected {klass!r}")
    reached, prefix = pass_prefix(markers[:first], expected_exits)
    findings += prefix
    if after is not None and reached != after:
        findings.append(f"the failure follows {reached}, expected {after}")
    rest = markers[first + 1:]
    detail = None
    if rest and rest[0].startswith(DETAIL_PREFIX):
        match = DETAIL.fullmatch(rest[0])
        if match:
            detail = tuple(int(value, 16) for value in match.groups())
        else:
            findings.append(f"malformed detail {rest[0]!r}")
        if klass not in DETAIL_REQUIRED + DETAIL_OPTIONAL:
            findings.append(f"class {klass} takes no BE_B5:DETAIL line")
        rest = rest[1:]
    elif klass in DETAIL_REQUIRED:
        findings.append(f"class {klass} needs a BE_B5:DETAIL line")
    if rest[:1] == [SRST_RETURNED]:
        rest = rest[1:]
    if rest:
        findings.append(f"lines after the failure: {rest}")
    if detail:
        finding = cause_finding(klass, detail[0], detail[2], detail[3])
        if finding:
            findings.append(finding)
    if cause is not None:
        if detail is None:
            findings.append(f"no detail cause to compare with 0x{cause:x}")
        elif detail[0] != cause:
            findings.append(f"cause 0x{detail[0]:x}, expected 0x{cause:x}")
    return findings


def evaluate(text, expect, base=None, hart=None,
             expected_exits=EXPECTED_EXITS, after=None, cause=None):
    """(ok, findings) for one capture's text."""
    markers, findings = scan(text)
    if base is not None and base != B5_BASE:
        findings.append(f"base 0x{base:x} != B5 base 0x{B5_BASE:x}")
    if hart is not None and hart != B5_HART:
        findings.append(f"hart {hart} != {B5_HART}, the only hart R3 admits")
    if expect == "pass":
        if after is not None or cause is not None:
            findings.append("--after and --cause apply to fail:CLASS only")
        exits, exit_findings = exits_of(markers, expected_exits)
        findings += exit_findings
        wanted = pass_sequence(exits)
        if tuple(markers) != wanted:
            findings.append(f"marker sequence differs: "
                            f"{first_divergence(markers, wanted)}")
    elif expect.startswith("fail:"):
        findings += failure_findings(markers, expect[len("fail:"):],
                                     expected_exits, after, cause)
    else:
        findings.append(f"unknown expectation {expect!r}")
    return not findings, findings


def parse_fields(markers):
    """Each argument-bearing marker's arguments, and any failure facts."""
    fields = {}
    for line in markers:
        if line.startswith(GUEST_PREFIX):
            parts = line[len(GUEST_PREFIX):].split(" ", 2)
            if parts[0].isdigit() and 1 <= int(parts[0]) <= len(GUEST_FIELDS):
                name = GUEST_FIELDS[int(parts[0]) - 1]
                if name not in fields and len(parts) == 3:
                    fields[name] = parts[2]
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
        match = EXITS.fullmatch(line)
        if match and "exits" not in fields:
            fields["exits"] = match.group(1)
    return fields


def result_record(capture, expect, markers, ok, findings, toolchain=None,
                  expected_exits=EXPECTED_EXITS):
    return {
        "capture": capture,
        "expect": expect,
        "toolchain": toolchain or "-",
        "result": "PASS" if ok else "FAIL",
        "boot_marker": "PASS" if full_sequence_reached(
            markers, expected_exits) else "FAIL",
        "terminal": terminal(markers),
        "findings": findings,
        "fields": parse_fields(markers),
        "markers": markers,
    }


# Source checks: the accepted inputs, the B5 run tools, and the B5 sources.
ACCEPTED_R5 = "165f4d001a2b59b582b397bdea79ec4826168fdb"
R5_RUNTIME = "arch/riscv/be/r5-runtime.c"
R5_RUNTIME_SHA256 = \
    "a221ce8ebb77e3feaa9d7799e3eb296fb8cd7aa9190e20f1970d7e9c95bcc6e4"
ACCEPTED_PLAN = "c3f8ef518850b55341cfd4ee0876b7f9ecf33859"
PLAN = "planning/k3-b5-plan.md"
PLAN_SHA256 = \
    "2c17462024a976d9b6deac03abb8423bbf6e571c8215e42e7ba4babc0cf1a937"
ACCEPTED_B2 = "898af4e02fd36744a93b0eef99bc159955409d25"
B2_RUNNER = "bringup/k3-b2/tests/run-qemu.sh"
B2_RUNNER_SHA256 = \
    "18d0f9bb97d1104e75c63f4247955200d019b7285361d543c4a616c956ea9402"
B5_RUNTIME = "bringup/k3-b5/src/b5-runtime.c"
B5_GUEST = "bringup/k3-b5/guest/guest.c"
B5_SRC = "bringup/k3-b5/src"
RUN_TOOLS = (HERE / "run-qemu.sh", HERE / "run-qemu-uboot.py",
             HERE.parent / "scripts" / "k3-uboot-run.sh")
ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'",
           "?": "?", "a": "\a", "b": "\b", "f": "\f", "v": "\v"}


def fixed_text(line):
    """A marker's fixed text: up to and including its first `=`."""
    return line[:line.index("=") + 1] if "=" in line else line


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


def b5_source_findings(runtime, guest, sources):
    """Findings for the B5 monitor and guest sources (None when missing).

    sources holds every bringup/k3-b5/src/*.[ch] text, b5-runtime.c too."""
    findings = []
    monitor = B5_ENTRY + (EXITS_TEXT, SHUTDOWN)
    if runtime is None:
        findings.append(f"{B5_RUNTIME} is missing: the B5 monitor source is "
                        f"not in this tree")
    else:
        findings += literal_findings(
            "b5-runtime.c", c_literals(runtime),
            R3_SEQUENCE + tuple(fixed_text(line) for line in monitor) +
            (FAIL_PREFIX, "BE_B5:DETAIL cause=", SRST_RETURNED))
    if guest is None:
        findings.append(f"{B5_GUEST} is missing: the B5 guest source is not "
                        f"in this tree")
    else:
        literals = c_literals(guest)
        findings += literal_findings(
            "guest.c", literals,
            tuple(fixed_text(line) for line in GUEST_LINES))
        for literal in literals:
            forged = [tag for tag in GUEST_FORBIDDEN if tag in literal]
            if forged:
                findings.append(f"guest.c literal {literal!r} holds the tag "
                                f"{forged[0]!r}")
    if not sources:
        return findings
    # The tagger and the exit classes may live in any monitor source.
    literals = [literal for text in sources for literal in c_literals(text)]
    findings += literal_findings(B5_SRC, literals, (GUEST_PREFIX,))
    for klass in CLASSES:
        token = re.compile(rf"(?<![\w-]){re.escape(klass)}(?![\w-])")
        if not any(token.search(literal) for literal in literals):
            findings.append(f"no literal in {B5_SRC} names the class "
                            f"{klass!r}")
    known = {line.split(" ", 1)[0]: line for line in R3_SEQUENCE}
    known.update((line.split(" ", 1)[0], fixed_text(line))
                 for line in monitor)
    for literal in literals:
        for match in re.finditer(r"BE_(?:R[0-9]|B5):[0-9]{2}", literal):
            wanted = known.get(match.group(0))
            if wanted is None or \
                    not literal.startswith(wanted, match.start()):
                findings.append(f"{B5_SRC} literal {literal!r} holds a "
                                f"marker outside the plan")
    return findings


def plan_markers(plan):
    match = re.search(r"^## Markers\n.*?^```text\n(.*?)^```", plan,
                      re.M | re.S)
    return tuple(match.group(1).splitlines()) if match else ()


def plan_classes(plan):
    """(classes, terminal regex) from the plan's Markers section."""
    match = re.search(r"^- Classes: (.*?)The run tools' terminal regex\s+"
                      r"is `([^`]*)`", plan, re.M | re.S)
    if not match:
        return (), None
    text = re.sub(r"\([^)]*\)", "", match.group(1))
    return tuple(re.findall(r"`([^`]+)`", text)), match.group(2)


def plan_variants(plan):
    """(variant, class, cause or None) rows of the negative-variant table."""
    start = plan.find("**Negative variants**")
    end = plan.find("## Markers", start)
    rows = re.findall(r"^\| `([a-z-]+)` \| [^|\n]+ \| `BE_B5:FAIL ([a-z-]+)`"
                      r"(?:, cause (\d+))?", plan[start:end], re.M)
    return tuple((name, klass, int(cause) if cause else None)
                 for name, klass, cause in rows)


def plan_scenarios(plan):
    """{scenario: (machine, cpu)} for the plan rows that name both."""
    return {name: (machine, cpu) for name, machine, cpu in re.findall(
        r"^\| `([a-z0-9.-]+)` \| `([^`]+)`; `([^`]+)` \|", plan, re.M)}


def runner_variants(runner):
    """(variant, class, cause or None) from run-qemu.sh's variants array."""
    match = re.search(r"^variants=\(\n(.*?)^\)", runner, re.M | re.S)
    rows = re.findall(r"^\t'([a-z-]+) ([a-z-]+) ([0-9]+|-)'$",
                      match.group(1), re.M) if match else []
    return tuple((name, klass, None if cause == "-" else int(cause))
                 for name, klass, cause in rows)


def plan_tool_findings(r5_runtime, plan, b2_runner, tools):
    """Findings for the accepted inputs against this checker and the tools.

    tools maps a run-tool name to its text (None when missing)."""
    findings = []
    literals = re.findall(r'"(BE_R3:[^"\\]*)\\n"', r5_runtime)
    if tuple(literals) != R3_SEQUENCE:
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
    variants = plan_variants(plan)
    if len(variants) != 7:
        findings.append(f"the plan's variant table has {len(variants)} rows")
    scenarios = plan_scenarios(plan)
    if set(scenarios) != {"k3-like", "rva23", "plic"}:
        findings.append(f"the plan's scenario rows differ: {scenarios}")
    minimal = re.search(r"^minimal='([^']+)'$", b2_runner, re.M)
    if not minimal or "sstc=false" not in minimal.group(1):
        findings.append("accepted B2 run-qemu.sh lost its R5 CPU string")
    for name, text in tools.items():
        if text is None:
            findings.append(f"run tool {name} is missing")
            continue
        if TERMINAL_REGEX not in text:
            findings.append(f"{name} lacks the terminal regex "
                            f"{TERMINAL_REGEX!r}")
    runner = tools.get("run-qemu.sh") or ""
    uboot = tools.get("run-qemu-uboot.py") or ""
    if runner_variants(runner) != variants:
        findings.append(f"run-qemu.sh variants {runner_variants(runner)} "
                        f"differ from the plan's {variants}")
    wanted = [(name, value) for name, pair in sorted(scenarios.items())
              for value in pair]
    wanted.append(("no-sstc", "virt,aia=none"))
    if minimal:
        wanted.append(("no-sstc", minimal.group(1)))
    for name, value in wanted:
        if f"'{value}'" not in runner and f" {value} " not in runner:
            findings.append(f"run-qemu.sh lacks the {name} value {value!r}")
    for value in scenarios.get("k3-like", ()):
        if value not in python_strings(uboot, ("MACHINE", "CPU")):
            findings.append(f"run-qemu-uboot.py lacks the k3-like value "
                            f"{value!r}")
    return findings


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


def check_sources(root):
    root = pathlib.Path(root)
    findings = []
    r5_runtime = git_show(root, ACCEPTED_R5, R5_RUNTIME, R5_RUNTIME_SHA256,
                          findings)
    plan = git_show(root, ACCEPTED_PLAN, PLAN, PLAN_SHA256, findings)
    b2_runner = git_show(root, ACCEPTED_B2, B2_RUNNER, B2_RUNNER_SHA256,
                         findings)
    tools = {path.name: read_optional(path) for path in RUN_TOOLS}
    if None not in (r5_runtime, plan, b2_runner):
        findings += plan_tool_findings(r5_runtime, plan, b2_runner, tools)
    runtime = read_optional(root / B5_RUNTIME)
    guest = read_optional(root / B5_GUEST)
    source_dir = root / B5_SRC
    sources = [path.read_text(encoding="utf-8", errors="replace")
               for path in sorted(source_dir.glob("*.[ch]"))] \
        if source_dir.is_dir() else []
    try:
        findings += b5_source_findings(runtime, guest, sources)
    except ValueError as error:
        findings.append(f"cannot parse the B5 sources: {error}")
    for finding in findings:
        print(f"finding: {finding}")
    print(f"BE_B5_MARKER_SOURCES: {'PASS' if not findings else 'FAIL'} "
          f"lines={len(PASS_TEMPLATE)} r3=r5-runtime.c@{ACCEPTED_R5[:8]} "
          f"plan={ACCEPTED_PLAN[:8]} "
          f"b5-runtime.c={'present' if runtime is not None else 'missing'} "
          f"guest.c={'present' if guest is not None else 'missing'}")
    return 0 if not findings else 1


def exits_report(markers, expected_exits=EXPECTED_EXITS):
    """The line that prints a capture's exit count, or None."""
    exits, _ = exits_of(markers, None)
    if exits is None:
        return None
    pin = "not pinned" if expected_exits is None else \
        f"pinned {expected_exits}"
    return f"BE_B5_EXITS: {exits} ({pin})"


BANNER = ("\r\nOpenSBI v1.6\r\n"
          "Platform Name               : riscv-virtio,qemu\r\n"
          "Runtime SBI Version         : 2.0\r\n"
          "Domain0 Next Address        : 0x0000000102000000\r\n\r\n")


def sample(lines, banner=BANNER, eol="\r\n", after=""):
    """A synthetic capture: a firmware banner, then the lines."""
    return banner + eol.join(lines) + eol + after


def detail(cause, pc=0x40010024, tval=0, htval=0):
    return (f"BE_B5:DETAIL cause=0x{cause:x} pc=0x{pc:x} tval=0x{tval:x} "
            f"htval=0x{htval:x}")


def capture_cases():
    count = EXPECTED_EXITS if EXPECTED_EXITS is not None else 55
    lines = list(pass_sequence(count))
    good = sample(lines)

    def edit(index, line):
        return sample(lines[:index] + [line] + lines[index + 1:])

    def exits(text):
        return edit(20, EXITS_TEXT + text)

    guest_run = list(R3_SEQUENCE + B5_ENTRY) + [GUEST_SEQUENCE[0]]
    unpinned = {"expected_exits": None}
    fail = "BE_B5:FAIL "
    denied = guest_run + [fail + "guest-page-fault",
                          detail(21, tval=0x40001000, htval=0x10000400)]
    vi = guest_run + [fail + "virtual-instruction", detail(22)]
    sbi30 = "\r\nOpenSBI v1.7\r\nRuntime SBI Version : 3.0\r\n\r\n"
    after_r3 = {"after": "BE_R3:07"}
    after_entry = {"after": "BE_B5:04"}
    return count, lines, good, [
        # Pass captures.
        ("pass", good, "pass", {}, True),
        ("pass, LF only", good.replace("\r", ""), "pass", {}, True),
        ("pass after U-Boot and shim noise", sample(
            lines, banner="=> loady 0x140000000\r\nStarting kernel ...\r\n"
            "BE_K3_B3: SHIM hart=0x0000000000000000\r\n"), "pass", {}, True),
        ("pass with a blank line", edit(11, "\r\n" + lines[11]), "pass", {},
         True),
        ("pass at base on hart 0", good, "pass",
         {"base": B5_BASE, "hart": 0}, True),
        ("wrong base", good, "pass", {"base": 0x80200000}, False),
        ("wrong hart", good, "pass", {"hart": 1}, False),
        ("missing guest line 06",
         sample(lines[:16] + lines[17:]), "pass", {}, False),
        ("reordered guest lines", sample(
            lines[:14] + [lines[15], lines[14]] + lines[16:]), "pass", {},
         False),
        ("duplicated BE_B5:03",
         sample(lines[:10] + lines[9:]), "pass", {}, False),
        ("marker after BE_B5:06", sample(lines + ["BE_B5:07 EXTRA"]),
         "pass", {}, False),
        ("text after BE_B5:06", sample(lines, after="sbi_hart: halted\r\n"),
         "pass", {}, False),
        ("noise between markers", edit(12, "OpenSBI warning\r\n" + lines[12]),
         "pass", {}, False),
        ("noise before a later marker", edit(12, "x " + lines[12]), "pass",
         {}, False),
        ("guest line without the prefix", edit(11, GUEST_LINES[0]), "pass",
         {}, False),
        ("guest line with a damaged prefix", edit(11, "BE_B5_GUES: " +
                                                  GUEST_LINES[0]), "pass",
         {}, False),
        ("guest output forging BE_B5:06", sample(
            lines[:20] + [GUEST_PREFIX + SHUTDOWN] + lines[20:]), "pass", {},
         False),
        ("guest output forging BE_R3:", edit(19, GUEST_PREFIX + "09 RESULT "
                                             "pass BE_R3:01"), "pass", {},
         False),
        ("guest output forging the shim", edit(
            19, GUEST_PREFIX + "BE_K3_B3: SHIM"), "pass", {}, False),
        ("escape in a guest line", edit(16, GUEST_PREFIX +
                                        "06 WRITE_BYTE \x1b[2Jok"), "pass",
         {}, False),
        ("tab in a marker", edit(16, GUEST_PREFIX + "06 WRITE_BYTE\tok"),
         "pass", {}, False),
        ("mid-line CR", edit(16, GUEST_PREFIX + "06 WRITE_BYTE ok\rok"),
         "pass", {}, False),
        ("undecodable byte", edit(16, GUEST_PREFIX + "06 WRITE_BYTE \ufffd"),
         "pass", {}, False),
        ("exits with a leading zero", exits("055"), "pass", unpinned, False),
        ("exits in hex", exits("0x37"), "pass", unpinned, False),
        ("exits empty", exits(""), "pass", unpinned, False),
        ("exits zero", exits("0"), "pass", unpinned, False),
        ("exits negative", exits("-1"), "pass", unpinned, False),
        ("exits with a trailing space", exits("55 "), "pass", unpinned,
         False),
        ("exits above the budget", exits("1025"), "pass", unpinned, False),
        ("exits 1, unpinned", exits("1"), "pass", unpinned, True),
        ("exits at the budget, unpinned", exits("1024"), "pass", unpinned,
         True),
        ("exits pinned and equal", exits("55"), "pass",
         {"expected_exits": 55}, True),
        ("exits pinned and different", exits("56"), "pass",
         {"expected_exits": 55}, False),
        ("forged hideleg", edit(8, B5_ENTRY[1].replace("hideleg=0x40",
                                                       "hideleg=0x440")),
         "pass", {}, False),
        ("upper-case hex", edit(7, B5_ENTRY[0].upper()), "pass", {}, False),
        ("timer not after the deadline", edit(18, GUEST_SEQUENCE[7].replace(
            "after_deadline=1", "after_deadline=0")), "pass", {}, False),
        ("guest result fail", edit(19, GUEST_PREFIX + "09 RESULT fail"),
         "pass", {}, False),
        ("R4 marker", sample(lines[:11] + ["BE_R4:01 ENTRY_ARMED_IMPORTED"] +
                             lines[11:]), "pass", {}, False),
        ("failure after pass", sample(lines + [fail + "resume"]), "pass", {},
         False),
        ("SRST returned after pass", sample(lines + [SRST_RETURNED]), "pass",
         {}, False),
        ("no shutdown", sample(lines[:-1]), "pass", {}, False),
        ("--after on a pass", good, "pass", after_entry, False),
        # Fail captures.
        ("sbi-3.0 boot refusal", sample([fail + "boot"], banner=sbi30),
         "fail:boot", {"after": "none"}, True),
        ("boot refusal, SRST returned", sample(
            [fail + "boot", SRST_RETURNED], banner=sbi30), "fail:boot",
         {"after": "none"}, True),
        ("boot failure after BE_R3:03", sample(
            list(R3_SEQUENCE[:3]) + [fail + "boot"]), "fail:boot", {}, True),
        ("boot failure after BE_R3:03 is not before BE_R3:01", sample(
            list(R3_SEQUENCE[:3]) + [fail + "boot"]), "fail:boot",
         {"after": "none"}, False),
        ("no-sstc", sample(list(R3_SEQUENCE) + [fail + "sstc"]),
         "fail:sstc", after_r3, True),
        ("sstc with a detail", sample(list(R3_SEQUENCE) + [
            fail + "sstc", detail(2)]), "fail:sstc", after_r3, False),
        ("sstc after BE_B5:01", sample(list(R3_SEQUENCE + B5_ENTRY[:1]) + [
            fail + "sstc"]), "fail:sstc", after_r3, False),
        ("denied load", sample(denied), "fail:guest-page-fault",
         dict(after_entry, cause=21), True),
        ("denied load, htval 0", sample(denied[:-1] + [
            detail(21, tval=0x40001000)]), "fail:guest-page-fault",
         dict(after_entry, cause=21), True),
        ("denied load, wrong htval", sample(denied[:-1] + [
            detail(21, tval=0x40001000, htval=0x40001000)]),
         "fail:guest-page-fault", after_entry, False),
        ("denied load, other cause expected", sample(denied),
         "fail:guest-page-fault", dict(after_entry, cause=23), False),
        ("guest-page fault without detail", sample(denied[:-1]),
         "fail:guest-page-fault", after_entry, False),
        ("guest-page fault with cause 22", sample(denied[:-1] + [detail(22)]),
         "fail:guest-page-fault", after_entry, False),
        ("detail in upper case", sample(denied[:-1] + [denied[-1].replace(
            "0x15", "0X15")]), "fail:guest-page-fault", after_entry, False),
        ("detail with a leading zero", sample(denied[:-1] + [
            denied[-1].replace("0x15", "0x015")]), "fail:guest-page-fault",
         after_entry, False),
        ("detail without htval", sample(denied[:-1] + [
            denied[-1].rsplit(" ", 1)[0]]), "fail:guest-page-fault",
         after_entry, False),
        ("virtual instruction", sample(vi), "fail:virtual-instruction",
         after_entry, True),
        ("virtual instruction with cause 2", sample(vi[:-1] + [detail(2)]),
         "fail:virtual-instruction", after_entry, False),
        ("illegal instruction", sample(guest_run + [
            fail + "illegal-instruction", detail(2)]),
         "fail:illegal-instruction", after_entry, True),
        ("interrupt", sample(guest_run + [
            fail + "interrupt", detail(INTERRUPT | 5)]), "fail:interrupt",
         after_entry, True),
        ("interrupt without the interrupt bit", sample(guest_run + [
            fail + "interrupt", detail(5)]), "fail:interrupt", after_entry,
         False),
        ("other exception", sample(guest_run + [
            fail + "exception", detail(5)]), "fail:exception", after_entry,
         True),
        ("exception with an illegal-instruction cause", sample(guest_run + [
            fail + "exception", detail(2)]), "fail:exception", after_entry,
         False),
        ("exception without detail (monitor integrity check)", sample(
            guest_run + [fail + "exception"]), "fail:exception", after_entry,
         True),
        ("exit budget", sample(guest_run + [fail + "exit-budget"]),
         "fail:exit-budget", after_entry, True),
        ("exit budget with detail", sample(guest_run + [
            fail + "exit-budget", detail(10)]), "fail:exit-budget",
         after_entry, True),
        ("guest failure", sample(
            list(R3_SEQUENCE + B5_ENTRY + GUEST_SEQUENCE[:8]) + [
                GUEST_PREFIX + "09 RESULT fail", fail + "guest-failure"]),
         "fail:guest-failure", after_entry, True),
        ("guest failure with detail", sample(guest_run + [
            fail + "guest-failure", detail(10)]), "fail:guest-failure",
         after_entry, False),
        ("shutdown returned", sample(lines + [
            fail + "shutdown-returned", SRST_RETURNED]),
         "fail:shutdown-returned", {"after": "BE_B5:06"}, True),
        ("class differs", sample(list(R3_SEQUENCE) + [fail + "controls"]),
         "fail:sstc", {}, False),
        ("unknown class", sample(list(R3_SEQUENCE) + [fail + "bogus"]),
         "fail:bogus", {}, False),
        ("class with trailing text", sample(list(R3_SEQUENCE) + [
            fail + "sstc now"]), "fail:sstc", {}, False),
        ("failure after a skipped line", sample([
            R3_SEQUENCE[0], R3_SEQUENCE[2], fail + "boot"]), "fail:boot", {},
         False),
        ("guest line before BE_B5:04", sample(list(R3_SEQUENCE) + [
            GUEST_SEQUENCE[0], fail + "sstc"]), "fail:sstc", {}, False),
        ("guest line after BE_B5:05", sample(lines[:21] + [
            GUEST_SEQUENCE[0], fail + "shutdown-returned"]),
         "fail:shutdown-returned", {}, False),
        ("two SRST returned", sample(list(R3_SEQUENCE) + [
            fail + "sstc", SRST_RETURNED, SRST_RETURNED]), "fail:sstc", {},
         False),
        ("marker after the failure", sample(list(R3_SEQUENCE) + [
            fail + "sstc", B5_ENTRY[0]]), "fail:sstc", {}, False),
        ("two failures", sample(list(R3_SEQUENCE) + [
            fail + "sstc", fail + "sstc"]), "fail:sstc", {}, False),
        ("detail before the failure", sample(guest_run + [
            detail(21), fail + "guest-page-fault"]), "fail:guest-page-fault",
         {}, False),
        ("noise after the failure", sample(
            list(R3_SEQUENCE) + [fail + "sstc"], after="garbage\r\n"),
         "fail:sstc", {}, False),
        ("guest escape before the failure", sample(guest_run[:-1] + [
            GUEST_PREFIX + "01 \x07", fail + "exit-budget"]),
         "fail:exit-budget", {}, False),
        ("pass is not a failure", good, "fail:sstc", {}, False),
        ("unknown expectation", good, "reject", {}, False),
    ]


# Self-test fixtures for the source checks (the real check reads the
# accepted plan and the B5 sources).
FIXTURE_K3 = ("virt,aia=aplic-imsic,aia-guests=7",
              "rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,"
              "sv57=off,smstateen=true")
FIXTURE_R5_CPU = ("rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,"
                  "sv57=off,sstc=false,smstateen=false,svadu=false,"
                  "debug=false")
FIXTURE_VARIANTS = (("denied-load", "guest-page-fault", 21),
                    ("code-store", "guest-page-fault", 23),
                    ("satp-write", "virtual-instruction", None),
                    ("fp", "illegal-instruction", None),
                    ("wfi", "virtual-instruction", None),
                    ("exit-budget", "exit-budget", None),
                    ("guest-fail", "guest-failure", None))


def runtime_fixture():
    monitor = B5_ENTRY + (EXITS_TEXT, SHUTDOWN)
    out = ["/* BE_B5:07 FUTURE is a comment, not a literal */",
           '#include "b5.h"']
    out += [f'static const char r3_{index}[] = "{line}\\n";'
            for index, line in enumerate(R3_SEQUENCE)]
    for index, line in enumerate(monitor):
        fixed = fixed_text(line)
        if index == 1:
            # Adjacent literals with a comment between them, joined by C.
            fixed = f'{fixed[:12]}" /* joined */\n\t"{fixed[12:]}'
        out.append(f'static const char b5_{index}[] = "{fixed}";')
    out += [f'static const char text_{index}[] = "{text}";' for index, text
            in enumerate((GUEST_PREFIX, FAIL_PREFIX, "BE_B5:DETAIL cause=",
                          SRST_RETURNED + "\\n"))]
    out.append("static const char *const classes[] = { " +
                ", ".join(f'"{klass}"' for klass in CLASSES) + " };")
    out.append("static const char quote = '\"';")
    return "\n".join(out) + "\n"


def guest_fixture():
    out = ['#include "sbi.h"']
    out += [f'static const char line_{index}[] = "{fixed_text(line)}";'
            for index, line in enumerate(GUEST_LINES)]
    out.append('static const char failed[] = "09 RESULT fail\\n";')
    return "\n".join(out) + "\n"


def plan_fixture():
    rows = "\n".join(
        f"| `{name}` | action | `BE_B5:FAIL {klass}`" +
        (f", cause {cause}" if cause else "") + " |"
        for name, klass, cause in FIXTURE_VARIANTS)
    classes = ", ".join(f"`{klass}`" for klass in CLASSES)
    return (f"**Negative variants**, one switch each:\n\n"
            f"| Variant | Guest action | Expected |\n| --- | --- | --- |\n"
            f"{rows}\n\n## Markers\n\nLines:\n\n```text\n" +
            "\n".join(PASS_TEMPLATE) + "\n```\n\n"
            f"- Classes: {classes} (as R5 uses `import`). The run tools' "
            f"terminal regex\n  is `{TERMINAL_REGEX}`.\n\n"
            f"| `k3-like` | `{FIXTURE_K3[0]}`; `{FIXTURE_K3[1]}` | GCC | x |\n"
            f"| `rva23` | `virt,aia=aplic-imsic`; `rva23s64` | GCC | x |\n"
            f"| `plic` | `virt`; `rv64,h=true` | GCC | x |\n"
            f"| `no-sstc` | `virt,aia=none`; the R5 CPU | GCC | x |\n")


def tools_fixture():
    variants = "\n".join(f"\t'{name} {klass} {cause or '-'}'"
                         for name, klass, cause in FIXTURE_VARIANTS)
    return {
        "run-qemu.sh": (
            f"terminal_regex='{TERMINAL_REGEX}'\n"
            f"k3_machine='{FIXTURE_K3[0]}'\nk3_cpu='{FIXTURE_K3[1]}'\n"
            f"minimal='{FIXTURE_R5_CPU}'\nvariants=(\n{variants}\n)\n"
            "run rva23 $tc $elf virt,aia=aplic-imsic rva23s64 x\n"
            "run plic $tc $elf virt rv64,h=true x\n"
            'run no-sstc $tc $elf virt,aia=none "$minimal" x\n'),
        "run-qemu-uboot.py": (
            f'TERMINAL = re.compile(rb"{TERMINAL_REGEX}")\n'
            f'MACHINE = "{FIXTURE_K3[0]}"\n'
            f'CPU = "{FIXTURE_K3[1][:34]}"\\\n    "{FIXTURE_K3[1][34:]}"\n'),
        "k3-uboot-run.sh": f"terminal_regex='{TERMINAL_REGEX}'\n",
    }


def source_cases():
    runtime = runtime_fixture()
    guest = guest_fixture()
    r5 = "\n".join(f'"{line}\\n"' for line in R3_SEQUENCE + (
        "BE_R4:01 ENTRY_ARMED_IMPORTED",)) + '\n"BE_R5:FAIL "\n'
    plan = plan_fixture()
    b2 = f"minimal='{FIXTURE_R5_CPU}'\n"
    tools = tools_fixture()

    def tool(name, text):
        return dict(tools, **{name: text})

    header = f'#define TAG "{GUEST_PREFIX}"\n'
    untagged = runtime.replace(GUEST_PREFIX, "TAG: ")

    def b5_case(name, runtime_text, guest_text, wanted, headers=()):
        sources = ([runtime_text] if runtime_text else []) + list(headers)
        return name, (runtime_text, guest_text, sources), wanted

    b5 = [
        b5_case("B5 sources complete", runtime, guest, True),
        b5_case("guest tag only in a header", untagged, guest, True,
                [header]),
        b5_case("b5-runtime.c missing", None, guest, False),
        b5_case("guest.c missing", runtime, None, False),
        b5_case("no guest tag literal", untagged, guest, False),
        b5_case("BE_B5:03 misspelt", runtime.replace(
            "RAM_CLEARED", "RAM_CLEAR"), guest, False),
        b5_case("an extra BE_B5 marker", runtime +
                '"BE_B5:07 EXTRA\\n";\n', guest, False),
        b5_case("an extra BE_B5 marker in a header", runtime, guest, False,
                ['#define EXTRA "BE_B5:07 EXTRA\\n"\n']),
        b5_case("an R5 marker", runtime + '"BE_R5:12 SHUTDOWN type=0 '
                'reason=0\\n";\n', guest, False),
        b5_case("an R3 marker misspelt", runtime.replace(
            "BE_R3:05 BINDING_PREPARED", "BE_R3:05 BINDING"), guest, False),
        b5_case("a fixed text only in a comment", runtime.replace(
            '"BE_B5:01 SSTC_STCE_READBACK henvcfg=";', "0; /* BE_B5:01 "
            "SSTC_STCE_READBACK henvcfg= */"), guest, False),
        b5_case("a guest line misspelt", runtime, guest.replace(
            "08 TIMER", "08 TIME"), False),
        b5_case("guest source forging a tag", runtime,
                guest + '"BE_B5:05 x";\n', False),
        b5_case("a class without a literal", runtime.replace(
            '"console", ', ""), guest, False),
    ]
    plans = [
        ("accepted inputs and tools agree", (r5, plan, b2, tools), True),
        ("an R3 literal differs", (r5.replace("R1_DERIVED", "R1"), plan, b2,
                                   tools), False),
        ("the Markers block differs", (r5, plan.replace(
            "sp=0x40001000", "sp=0x40002000"), b2, tools), False),
        ("a class differs", (r5, plan.replace("`console`", "`uart`"), b2,
                             tools), False),
        ("the terminal regex differs", (r5, plan.replace(
            "BE_K3_B3: FAIL`", "BE_K3_B3:FAIL`"), b2, tools), False),
        ("a variant class differs", (r5, plan, b2, tool(
            "run-qemu.sh", tools["run-qemu.sh"].replace(
                "'wfi virtual-instruction -'",
                "'wfi illegal-instruction -'"))), False),
        ("a variant cause differs", (r5, plan, b2, tool(
            "run-qemu.sh", tools["run-qemu.sh"].replace(
                "guest-page-fault 23", "guest-page-fault 21"))), False),
        ("the U-Boot CPU differs", (r5, plan, b2, tool(
            "run-qemu-uboot.py", tools["run-qemu-uboot.py"].replace(
                "svade=true,", ""))), False),
        ("the R5 CPU differs", (r5, plan, b2, tool(
            "run-qemu.sh", tools["run-qemu.sh"].replace(
                "debug=false", "debug=true"))), False),
        ("the plic row is missing from the runner", (r5, plan, b2, tool(
            "run-qemu.sh", tools["run-qemu.sh"].replace(
                "virt rv64,h=true", "virt rv64"))), False),
        ("the board tool lacks the regex", (r5, plan, b2, tool(
            "k3-uboot-run.sh", "terminal_regex='BE_B5:06'\n")), False),
        ("a run tool is missing", (r5, plan, b2, tool("run-qemu.sh", None)),
         False),
    ]
    return b5, plans


def self_test():
    count, lines, good, cases = capture_cases()
    failed = 0
    for name, text, expect, options, wanted in cases:
        ok, findings = evaluate(text, expect, **options)
        failed += ok != wanted
        print(f"{'ok  ' if ok == wanted else 'FAIL'} {name}: ok={ok} "
              f"findings={findings}")
    fail = "BE_B5:FAIL "
    records = [
        ("record pass", good, "pass", "PASS", "PASS", "shutdown-requested"),
        ("record failure after pass", sample(lines + [fail + "resume"]),
         "pass", "FAIL", "FAIL", "fail-marker"),
        ("record truncated", sample(lines[:-1]), "pass", "FAIL", "FAIL",
         "none"),
        ("record guest stopped", sample(lines[:15]), "pass", "FAIL", "FAIL",
         "none"),
        ("record forged extra", sample(lines + ["BE_B5:07 EXTRA"]), "pass",
         "FAIL", "PASS", "none"),
        ("record no-sstc", sample(list(R3_SEQUENCE) + [fail + "sstc"]),
         "fail:sstc", "PASS", "FAIL", "fail-marker"),
    ]
    for name, text, expect, result, boot, end in records:
        markers = extract(text)
        ok, findings = evaluate(text, expect)
        record = result_record("x", expect, markers, ok, findings, "gcc")
        got = (record["result"], record["boot_marker"], record["terminal"])
        wanted = (result, boot, end)
        failed += got != wanted
        print(f"{'ok  ' if got == wanted else 'FAIL'} {name}: "
              f"result/boot_marker/terminal={got}")
    checks = []
    fields = result_record("x", "pass", extract(good), True, [])["fields"]
    checks.append(("pass fields", fields.get("guest_timer") ==
                   "cause=0x8000000000000005 after_deadline=1 cleared=1" and
                   fields.get("exits") == str(count) and
                   fields.get("guest_shutdown") ==
                   f"type=0 reason=0 exits={count}" and
                   fields.get("guest_write_byte") == "ok" and
                   fields.get("guest_result") == "pass" and
                   fields.get("management_entry") == "pc=0x40010000" and
                   len(fields) == len(FIELD_PREFIXES) + len(GUEST_FIELDS) + 1
                   and all(isinstance(value, str)
                           for value in fields.values())))
    denied = sample(list(R3_SEQUENCE + B5_ENTRY) + [
        fail + "guest-page-fault", detail(21, tval=0x40001000), SRST_RETURNED])
    fields = result_record("x", "fail:guest-page-fault", extract(denied),
                           True, [])["fields"]
    checks.append(("failure fields", fields.get("failure") ==
                   "guest-page-fault" and fields.get("detail") ==
                   "cause=0x15 pc=0x40010024 tval=0x40001000 htval=0x0" and
                   fields.get("srst_returned") == "yes"))
    # EXPECTED_EXITS: None prints any count; a pin is printed and enforced.
    checks.append(("exits printed, not pinned", exits_report(
        extract(good), None) == f"BE_B5_EXITS: {count} (not pinned)"))
    checks.append(("exits printed, pinned", exits_report(
        extract(good), count) == f"BE_B5_EXITS: {count} (pinned {count})"))
    checks.append(("pin enforced in the boot marker",
                   full_sequence_reached(extract(good), count) and
                   not full_sequence_reached(extract(good), count + 1)
                   and full_sequence_reached(extract(good), None)))
    checks.append(("C literals", c_literals(
        '"a\\x41\\102\\n" "b" /* "c" */ "d" \'"\' "e" // "f"\n"g"') ==
        ["aAB\nbd", "eg"]))
    try:
        c_literals('x = "abc')
        checks.append(("unterminated literal", False))
    except ValueError:
        checks.append(("unterminated literal", True))
    plan = plan_fixture()
    checks.append(("plan parsers", plan_markers(plan) == PASS_TEMPLATE and
                   plan_classes(plan) == (CLASSES, TERMINAL_REGEX) and
                   plan_variants(plan) == FIXTURE_VARIANTS and
                   runner_variants(tools_fixture()["run-qemu.sh"]) ==
                   FIXTURE_VARIANTS and
                   plan_scenarios(plan)["k3-like"] == FIXTURE_K3))
    for name, ok in checks:
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}")
    b5_cases, plan_cases = source_cases()
    for name, arguments, wanted in b5_cases:
        findings = b5_source_findings(*arguments)
        failed += (not findings) != wanted
        print(f"{'ok  ' if (not findings) == wanted else 'FAIL'} sources: "
              f"{name}: findings={findings}")
    for name, arguments, wanted in plan_cases:
        findings = plan_tool_findings(*arguments)
        failed += (not findings) != wanted
        print(f"{'ok  ' if (not findings) == wanted else 'FAIL'} plan and "
              f"tools: {name}: findings={findings}")
    total = len(cases) + len(records) + len(checks) + len(b5_cases) + \
        len(plan_cases)
    print(f"BE_B5_MARKER_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
          f"cases={total}")
    return 0 if not failed else 1


def expectation(value):
    if value == "pass" or (value.startswith("fail:") and
                           value[len("fail:"):] in CLASSES):
        return value
    raise argparse.ArgumentTypeError(
        f"{value!r} is not pass or fail:CLASS, CLASS one of "
        f"{', '.join(CLASSES)}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--capture")
    parser.add_argument("--expect", type=expectation, default="pass")
    parser.add_argument("--toolchain", choices=("gcc", "clang"))
    parser.add_argument("--after", choices=LINE_IDS)
    parser.add_argument("--cause", type=lambda value: int(value, 0))
    parser.add_argument("--json")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check-sources", metavar="REPO_ROOT")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.check_sources:
        return check_sources(args.check_sources)
    if args.capture is None:
        parser.error("--capture FILE is required")
    with open(args.capture, "rb") as handle:
        text = handle.read().decode("utf-8", errors="replace")
    markers = extract(text)
    ok, findings = evaluate(text, args.expect, after=args.after,
                            cause=args.cause)
    record = result_record(args.capture, args.expect, markers, ok, findings,
                           args.toolchain)
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
    if args.expect == "pass":
        print(f"BE_B5_MARKER_RESULT: {record['boot_marker']} "
              f"terminal={record['terminal']}")
    print(f"BE_B5_MARKERS[{args.toolchain or '-'}/{args.expect}]: "
          f"{record['result']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
