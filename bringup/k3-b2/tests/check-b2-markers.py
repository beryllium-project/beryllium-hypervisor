#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Validate B2 console markers from a QEMU or K3 serial capture.

B2 runs the K3 port of the accepted R5 image: the accepted R3 boot and first
management VS entry (BE_R3:01-07), the accepted R4 management prelude with
its two checked exits (BE_R4:01-03), then R5's checked switch to the
protected domain, three checked protected exits, the checked return switch,
the management completion event, and the allowlisted SBI SRST shutdown
(BE_R5:01-12). The marker strings are those of the accepted
arch/riscv/be/r5-runtime.c and tests/r5/check-qemu-artifacts.mjs.

  check-b2-markers.py CAPTURE [--expect pass|reject] [--base B] [--hart H]
                      [--json F]
  check-b2-markers.py --self-test
  check-b2-markers.py --check-sources R5_RUNTIME_C R5_QEMU_CHECKER_MJS

--expect pass requires exactly the 22 accepted lines in order and nothing
else: no failure marker, no SRST return, no repeated or forged line.
--expect reject requires a fail-closed R5 terminal report before BE_R3:04,
as a firmware mismatch produces: an exact prefix of the accepted lines that
stops before BE_R3:04, then `BE_R5:FAIL import` (R5 reports every boot,
R1, R2, and HS/VS-state prerequisite failure as `import`), then at most
`BE_R5:SRST_RETURNED`. --base, when given (k3-run.sh passes the kexec
entry), must equal the B2 load address. --hart, when given, must be 0: the
accepted R3 boot contract admits only hart 0, so a passing capture implies
it. --check-sources re-derives the expected lines from the accepted (and
ported, unchanged) r5-runtime.c marker literals and the accepted R5 QEMU
checker's expectedConsole, each SHA-256 pinned, and requires them to equal
PASS_SEQUENCE.
"""

import argparse
import hashlib
import json
import re
import sys

B2_BASE = 0x102000000
B2_HART = 0
TAGS = ("BE_R3:", "BE_R4:", "BE_R5:")
FAIL_TAGS = ("BE_R3:FAIL", "BE_R4:FAIL", "BE_R5:FAIL")
SRST_RETURNED = "BE_R5:SRST_RETURNED"
REJECT_FAILURE = "BE_R5:FAIL import"
PASS_SEQUENCE = (
    "BE_R3:01 BOOT_VALIDATED",
    "BE_R3:02 R1_DERIVED",
    "BE_R3:03 R2_BUILT_REWALKED",
    "BE_R3:04 HS_VS_STATE_VERIFIED",
    "BE_R3:05 BINDING_PREPARED",
    "BE_R3:06 HGATP_FENCED_PUBLISHED",
    "BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000",
    "BE_R4:01 ENTRY_ARMED_IMPORTED",
    "BE_R4:02 EXPECTED_DENIED_LOAD pc=0x40010014 resume=0x40010018",
    "BE_R4:03 PRIVATE_EVENT pc=0x40010030 resume=0x40010034",
    "BE_R5:01 R4_COMPLETE_IMPORTED sepc=0x40010034",
    "BE_R5:02 PENDING_PROTECTED direction=management-to-protected",
    "BE_R5:03 PROTECTED_HGATP_WRITTEN_FENCED_READBACK",
    "BE_R5:04 PROTECTED_TARGET_VERIFIED pc=0x40011000",
    "BE_R5:05 EXPECTED_DENIED_LOAD pc=0x40011014 resume=0x40011018",
    "BE_R5:06 EXPECTED_DENIED_SHARED_STORE pc=0x40011024 resume=0x40011028",
    "BE_R5:07 SWITCH_EVENT pc=0x40011030 saved=0x40011034",
    "BE_R5:08 PENDING_MANAGEMENT direction=protected-to-management",
    "BE_R5:09 MANAGEMENT_HGATP_WRITTEN_FENCED_READBACK",
    "BE_R5:10 MANAGEMENT_TARGET_VERIFIED pc=0x40010034",
    "BE_R5:11 FINAL_EVENT pc=0x40010038 s0=17 a0=17 a1=34 shared=34 "
    "protected=51",
    "BE_R5:12 SHUTDOWN type=0 reason=0",
)
MILESTONE = PASS_SEQUENCE[-1]
HS_VS_STATE = PASS_SEQUENCE.index("BE_R3:04 HS_VS_STATE_VERIFIED")
# Accepted R5 (165f4d00) sources of PASS_SEQUENCE; port.py copies
# r5-runtime.c unchanged.
R5_RUNTIME_SHA256 = \
    "a221ce8ebb77e3feaa9d7799e3eb296fb8cd7aa9190e20f1970d7e9c95bcc6e4"
R5_QEMU_CHECKER_SHA256 = \
    "6d730b9ba3bb87529c882bb3773d597e03595995c3d95cec2f1b90e91ab3ef52"
# Argument-bearing marker -> JSON field holding its arguments.
FIELD_PREFIXES = (
    ("BE_R3:07 ", "management_entry"),
    ("BE_R4:02 ", "management_denied_load"),
    ("BE_R4:03 ", "management_private_event"),
    ("BE_R5:01 ", "r4_import"),
    ("BE_R5:02 ", "outbound_switch"),
    ("BE_R5:04 ", "protected_entry"),
    ("BE_R5:05 ", "protected_denied_load"),
    ("BE_R5:06 ", "protected_denied_shared_store"),
    ("BE_R5:07 ", "protected_switch_event"),
    ("BE_R5:08 ", "return_switch"),
    ("BE_R5:10 ", "management_reentry"),
    ("BE_R5:11 ", "final_event"),
    ("BE_R5:12 ", "shutdown"),
)


def extract(text):
    """Every BE_R3/BE_R4/BE_R5 marker line, from the marker to the end."""
    markers = []
    for raw in text.replace("\r", "").split("\n"):
        positions = [raw.find(tag) for tag in TAGS]
        positions = [position for position in positions if position >= 0]
        if positions:
            markers.append(raw[min(positions):].rstrip())
    return markers


def is_failure(line):
    return line.startswith(FAIL_TAGS) or line == SRST_RETURNED


def full_sequence_reached(markers):
    """The accepted lines through BE_R5:12, in order, and no failure."""
    if any(is_failure(line) for line in markers):
        return False
    return tuple(markers[:len(PASS_SEQUENCE)]) == PASS_SEQUENCE


def terminal(markers):
    if any(is_failure(line) for line in markers):
        return "fail-marker"
    if markers and markers[-1] == MILESTONE:
        return "shutdown-requested"
    return "none"


def first_divergence(markers):
    for index, wanted in enumerate(PASS_SEQUENCE):
        if index >= len(markers):
            return f"missing {wanted!r} (line {index + 1})"
        if markers[index] != wanted:
            return f"line {index + 1} is {markers[index]!r}, expected {wanted!r}"
    extra = markers[len(PASS_SEQUENCE)]
    return f"unexpected line {len(PASS_SEQUENCE) + 1} {extra!r}"


def evaluate(markers, expect, base=None, hart=None):
    findings = []
    if base is not None and base != B2_BASE:
        findings.append(f"base 0x{base:x} != B2 base 0x{B2_BASE:x}")
    if hart is not None and hart != B2_HART:
        findings.append(f"hart {hart} != {B2_HART}, the only hart R3 admits")
    if expect == "pass":
        if tuple(markers) != PASS_SEQUENCE:
            findings.append(f"marker sequence differs: {first_divergence(markers)}")
    elif expect == "reject":
        failures = [index for index, line in enumerate(markers)
                    if is_failure(line)]
        if not failures:
            findings.append("no BE_R5:FAIL terminal report")
        else:
            first = failures[0]
            if markers[first] != REJECT_FAILURE:
                findings.append(f"first failure is {markers[first]!r}, "
                                f"expected {REJECT_FAILURE!r}")
            if first > HS_VS_STATE or \
                    tuple(markers[:first]) != PASS_SEQUENCE[:first]:
                findings.append("failure is not preceded by an accepted "
                                "prefix that stops before BE_R3:04")
            if markers[first + 1:] not in ([], [SRST_RETURNED]):
                findings.append(f"lines after the failure: {markers[first + 1:]}")
        if PASS_SEQUENCE[HS_VS_STATE] in markers:
            findings.append("rejected run still reached BE_R3:04")
    else:
        findings.append(f"unknown expectation {expect!r}")
    return not findings, findings


def parse_fields(markers):
    """Each argument-bearing marker's arguments, e.g. pc=... resume=..."""
    fields = {}
    for line in markers:
        parts = line.split(" ", 2)
        for prefix, name in FIELD_PREFIXES:
            if line.startswith(prefix) and name not in fields and \
                    len(parts) == 3:
                fields[name] = parts[2]
        if line.startswith("BE_R5:FAIL ") and "failure" not in fields:
            fields["failure"] = line[len("BE_R5:FAIL "):]
        elif line.startswith(FAIL_TAGS) and "failure" not in fields:
            fields["failure"] = line
        if line == SRST_RETURNED:
            fields["srst_returned"] = "yes"
    return fields


def result_record(capture, expect, markers, ok, findings):
    return {
        "capture": capture,
        "expect": expect,
        "result": "PASS" if ok else "FAIL",
        "boot_marker": "PASS" if full_sequence_reached(markers) else "FAIL",
        "terminal": terminal(markers),
        "findings": findings,
        "fields": parse_fields(markers),
        "markers": markers,
    }


def self_test():
    good = "OpenSBI v1.6\r\n" + "\r\n".join(PASS_SEQUENCE) + "\r\n"
    noisy = ("[  228.5] reboot: Restarting system\n[  228.6] Bye...\n" +
             "\n".join(PASS_SEQUENCE[:9]) + "\nlogin: " +
             "\n".join(PASS_SEQUENCE[9:]) + "\n")
    lines = list(PASS_SEQUENCE)
    reordered = lines[:14] + [lines[15], lines[14]] + lines[16:]
    forged_values = [line.replace("a1=34", "a1=68") for line in lines]
    rejected = "OpenSBI v1.7\nBE_R5:FAIL import\n"
    cases = [
        ("pass", good, "pass", None, None, True),
        ("pass with noise", noisy, "pass", None, None, True),
        ("pass at base on hart 0", good, "pass", B2_BASE, 0, True),
        ("wrong base", good, "pass", 0x80200000, None, False),
        ("wrong hart", good, "pass", None, 1, False),
        ("missing denied shared store",
         "\n".join(lines[:15] + lines[16:]), "pass", None, None, False),
        ("reordered protected exits", "\n".join(reordered), "pass", None,
         None, False),
        ("repeated marker", "\n".join(lines[:15] + lines[14:]), "pass", None,
         None, False),
        ("forged extra", good + "BE_R5:13 EXTRA\n", "pass", None, None,
         False),
        ("forged final values", "\n".join(forged_values), "pass", None, None,
         False),
        ("no shutdown", "\n".join(lines[:-1]), "pass", None, None, False),
        ("R4 prelude only", "\n".join(lines[:10]), "pass", None, None, False),
        ("failure after pass", good + "BE_R5:FAIL invalid-phase\n", "pass",
         None, None, False),
        ("SRST returned after pass", good + SRST_RETURNED + "\n", "pass",
         None, None, False),
        ("rejected", rejected, "reject", None, None, True),
        ("rejected, SRST returned", rejected + SRST_RETURNED + "\n",
         "reject", None, None, True),
        ("rejected after boot validation",
         "BE_R3:01 BOOT_VALIDATED\nBE_R5:FAIL import\n", "reject", None,
         None, True),
        ("pass is not reject", good, "reject", None, None, False),
        ("late failure is not reject",
         "\n".join(lines[:4]) + "\nBE_R5:FAIL import\n", "reject", None,
         None, False),
        ("wrong reject reason", "BE_R5:FAIL hart\n", "reject", None, None,
         False),
        ("R4 failure form is not an R5 reject", "BE_R4:FAIL r3-state\n",
         "reject", None, None, False),
        ("forged line before reject", "BE_R3:02 R1_DERIVED\n"
         "BE_R5:FAIL import\n", "reject", None, None, False),
    ]
    failed = 0
    for name, text, expect, base, hart, wanted in cases:
        ok, findings = evaluate(extract(text), expect, base, hart)
        status = "ok  " if ok == wanted else "FAIL"
        failed += ok != wanted
        print(f"{status} {name}: ok={ok} findings={findings}")
    records = [
        ("record pass", good, "pass", "PASS", "PASS", "shutdown-requested"),
        ("record noise", noisy, "pass", "PASS", "PASS", "shutdown-requested"),
        ("record failure after pass", good + "BE_R5:FAIL backing\n", "pass",
         "FAIL", "FAIL", "fail-marker"),
        ("record truncated", "\n".join(lines[:-1]), "pass", "FAIL", "FAIL",
         "none"),
        ("record forged extra", good + "BE_R5:13 EXTRA\n", "pass", "FAIL",
         "PASS", "none"),
        ("record reject", rejected, "reject", "PASS", "FAIL", "fail-marker"),
    ]
    for name, text, expect, result, boot, end in records:
        markers = extract(text)
        ok, findings = evaluate(markers, expect)
        record = result_record("x", expect, markers, ok, findings)
        wanted = (result, boot, end)
        got = (record["result"], record["boot_marker"], record["terminal"])
        status = "ok  " if got == wanted else "FAIL"
        failed += got != wanted
        print(f"{status} {name}: result/boot_marker/terminal={got}")
    fields = result_record("x", "pass", extract(good), True, [])["fields"]
    expected_fields = {
        "protected_denied_load": "pc=0x40011014 resume=0x40011018",
        "protected_denied_shared_store": "pc=0x40011024 resume=0x40011028",
        "protected_switch_event": "pc=0x40011030 saved=0x40011034",
        "final_event": "pc=0x40010038 s0=17 a0=17 a1=34 shared=34 "
                       "protected=51",
        "shutdown": "type=0 reason=0",
    }
    for name, value in expected_fields.items():
        if fields.get(name) != value:
            print(f"FAIL field {name}: {fields.get(name)!r}")
            failed += 1
    if len(fields) != len(FIELD_PREFIXES) or \
            not all(isinstance(value, str) for value in fields.values()):
        print(f"FAIL fields {fields}")
        failed += 1
    reject_fields = result_record("x", "reject", extract(rejected), True,
                                  [])["fields"]
    if reject_fields != {"failure": "import"}:
        print(f"FAIL reject fields {reject_fields}")
        failed += 1
    total = len(cases) + len(records)
    print(f"BE_B2_MARKER_SELF_TEST: {'PASS' if failed == 0 else 'FAIL'} "
          f"cases={total}")
    return 0 if failed == 0 else 1


def check_sources(runtime_path, qemu_checker_path):
    """Require PASS_SEQUENCE to equal the accepted R5 marker sources."""
    findings = []
    runtime = open(runtime_path, "rb").read()
    checker = open(qemu_checker_path, "rb").read()
    for path, data, pin in ((runtime_path, runtime, R5_RUNTIME_SHA256),
                            (qemu_checker_path, checker,
                             R5_QEMU_CHECKER_SHA256)):
        if hashlib.sha256(data).hexdigest() != pin:
            findings.append(f"{path} is not the accepted R5 file")
    literals = re.findall(r'"(BE_R[345]:[^"\\]*)(\\n)?"', runtime.decode())
    emitted = tuple(text for text, newline in literals
                    if newline and text != SRST_RETURNED)
    if emitted != PASS_SEQUENCE:
        findings.append(f"r5-runtime.c success markers differ: {emitted}")
    if ("BE_R5:FAIL ", "") not in literals or \
            (SRST_RETURNED, "\\n") not in literals:
        findings.append("r5-runtime.c lost its failure markers")
    match = re.search(r"export const expectedConsole = \[(.*?)\n\]",
                      checker.decode(), re.S)
    expected = tuple(re.findall(r"'([^']*)'", match.group(1))) if match else ()
    if expected != PASS_SEQUENCE:
        findings.append(f"check-qemu-artifacts.mjs expectedConsole differs: "
                        f"{expected}")
    for finding in findings:
        print(f"finding: {finding}")
    print(f"BE_B2_MARKER_SOURCES: {'PASS' if not findings else 'FAIL'} "
          f"lines={len(PASS_SEQUENCE)} runtime=r5-runtime.c "
          f"qemu_checker=check-qemu-artifacts.mjs")
    return 0 if not findings else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", nargs="?")
    parser.add_argument("--expect", choices=("pass", "reject"), default="pass")
    parser.add_argument("--base", type=lambda value: int(value, 0))
    parser.add_argument("--hart", type=lambda value: int(value, 0))
    parser.add_argument("--json")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check-sources", nargs=2,
                        metavar=("R5_RUNTIME_C", "R5_QEMU_CHECKER_MJS"))
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.check_sources:
        return check_sources(*args.check_sources)
    if args.capture is None:
        parser.error("a capture file is required")
    with open(args.capture, "rb") as handle:
        markers = extract(handle.read().decode("utf-8", errors="replace"))
    ok, findings = evaluate(markers, args.expect, args.base, args.hart)
    record = result_record(args.capture, args.expect, markers, ok, findings)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
    for line in markers:
        print(line)
    for finding in findings:
        print(f"finding: {finding}")
    if args.expect == "pass":
        print(f"BE_B2_RESULT: {record['boot_marker']} "
              f"terminal={record['terminal']}")
    print(f"BE_B2_MARKERS[{args.expect}]: {record['result']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
