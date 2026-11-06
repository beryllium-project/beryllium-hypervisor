#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Validate B1 console markers from a QEMU or K3 serial capture.

B1 runs the K3 port of the accepted R4 image: the accepted R3 boot and first
management VS entry (BE_R3:01-07), then R4's two checked VS exits
(BE_R4:01-03). After BE_R4:03 the guest spins in VS mode, as accepted R4
does, so the success capture ends there without a shutdown marker.

  check-b1-markers.py CAPTURE [--expect pass|reject] [--base B] [--json F]
  check-b1-markers.py --self-test

--expect pass requires exactly the ten accepted lines in order and no failure
marker. --expect reject requires a fail-closed R4 terminal report
(BE_R4:FAIL) before BE_R3:04, as a firmware mismatch produces. --base, when
given (k3-run.sh passes the kexec entry), must equal the B1 load address.
"""

import argparse
import json
import sys

B1_BASE = 0x102000000
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
)
MILESTONE = PASS_SEQUENCE[-1]


def extract(text):
    """Every BE_R3/BE_R4 marker line, from the marker to the end of line."""
    markers = []
    for raw in text.replace("\r", "").split("\n"):
        positions = [raw.find(tag) for tag in ("BE_R3:", "BE_R4:")]
        positions = [position for position in positions if position >= 0]
        if positions:
            markers.append(raw[min(positions):].rstrip())
    return markers


def terminal(markers):
    if any(":FAIL" in line for line in markers):
        return "fail-marker"
    if markers and markers[-1] == MILESTONE:
        return "guest-spinning"
    return "none"


def evaluate(markers, expect, base=None):
    findings = []
    if base is not None and base != B1_BASE:
        findings.append(f"base 0x{base:x} != B1 base 0x{B1_BASE:x}")
    if expect == "pass":
        if tuple(markers) != PASS_SEQUENCE:
            findings.append(f"marker sequence differs: {markers}")
    elif expect == "reject":
        failures = [line for line in markers if line.startswith("BE_R4:FAIL ")]
        if not failures:
            findings.append("no BE_R4:FAIL terminal report")
        if PASS_SEQUENCE[3] in markers:
            findings.append("rejected run still reached BE_R3:04")
    else:
        findings.append(f"unknown expectation {expect!r}")
    return not findings, findings


def result_record(capture, expect, markers, ok, findings):
    milestone = "PASS" if MILESTONE in markers and not any(
        ":FAIL" in line for line in markers) else "FAIL"
    fields = {}
    for line in markers:
        if line.startswith("BE_R4:02 "):
            fields["denied_load"] = line.split(" ", 2)[2]
        elif line.startswith("BE_R4:03 "):
            fields["private_event"] = line.split(" ", 2)[2]
        elif line.startswith("BE_R4:FAIL "):
            fields["failure"] = line.split(" ", 1)[1]
    return {
        "capture": capture,
        "expect": expect,
        "result": "PASS" if ok else "FAIL",
        "boot_marker": milestone,
        "terminal": terminal(markers),
        "findings": findings,
        "fields": fields,
        "markers": markers,
    }


def self_test():
    good = ("OpenSBI v1.6\r\n" + "\r\n".join(PASS_SEQUENCE) + "\r\n")
    noisy = "[  228.5] Bye...\n" + "\n".join(PASS_SEQUENCE[:5]) + \
        "\nlogin: " + "\n".join(PASS_SEQUENCE[5:]) + "\n"
    rejected = "BE_R3:01 BOOT_VALIDATED\nBE_R4:FAIL r3-state\n" \
        "BE_R4:SRST_RETURNED\n"
    cases = [
        ("pass", good, "pass", None, True),
        ("pass with noise", noisy, "pass", None, True),
        ("pass at base", good, "pass", B1_BASE, True),
        ("wrong base", good, "pass", 0x80200000, False),
        ("missing exit", good.replace(PASS_SEQUENCE[8] + "\r\n", ""),
         "pass", None, False),
        ("reordered", "\n".join(PASS_SEQUENCE[:8] + PASS_SEQUENCE[9:] +
                                PASS_SEQUENCE[8:9]), "pass", None, False),
        ("forged extra", good + "BE_R4:04 EXTRA\n", "pass", None, False),
        ("failure after pass", good + "BE_R4:FAIL invalid-phase\n", "pass",
         None, False),
        ("rejected", rejected, "reject", None, True),
        ("pass is not reject", good, "reject", None, False),
        ("late failure is not reject", good.replace(
            PASS_SEQUENCE[9], "BE_R4:FAIL cause"), "reject", None, False),
    ]
    failed = 0
    for name, text, expect, base, wanted in cases:
        ok, findings = evaluate(extract(text), expect, base)
        status = "ok  " if ok == wanted else "FAIL"
        failed += ok != wanted
        print(f"{status} {name}: ok={ok} findings={findings}")
    record = result_record("x", "pass", extract(good), True, [])
    if record["terminal"] != "guest-spinning" or record["boot_marker"] != "PASS":
        print("FAIL result record")
        failed += 1
    print(f"BE_B1_MARKER_SELF_TEST: {'PASS' if failed == 0 else 'FAIL'} "
          f"cases={len(cases)}")
    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", nargs="?")
    parser.add_argument("--expect", choices=("pass", "reject"), default="pass")
    parser.add_argument("--base", type=lambda value: int(value, 0))
    parser.add_argument("--hart", type=lambda value: int(value, 0))
    parser.add_argument("--json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.capture is None:
        parser.error("a capture file is required")
    with open(args.capture, "rb") as handle:
        markers = extract(handle.read().decode("utf-8", errors="replace"))
    ok, findings = evaluate(markers, args.expect, args.base)
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
        print(f"BE_B1_RESULT: {record['boot_marker']} "
              f"terminal={record['terminal']}")
    print(f"BE_B1_MARKERS[{args.expect}]: {record['result']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
