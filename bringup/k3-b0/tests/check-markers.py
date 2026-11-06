#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Validate B0 console markers from a QEMU or K3 serial capture.

The capture may contain firmware and Linux output before B0 runs, carriage
returns from the SBI console, and partial final lines. Only text from each
``BE_B0:`` marker to the end of its line is interpreted.
"""

import argparse
import json
import re
import sys

PASS_SEQUENCE = ("01", "02", "03", "04", "05", "06", "07")
HEX = r"0x[0-9a-f]{16}"
PATTERNS = {
    "01": re.compile(
        rf"^BE_B0:01 ENTRY hart=(?P<hart>{HEX}) base=(?P<base>{HEX}) "
        rf"fdt=(?P<fdt>{HEX}) bss_zero=(?P<bss_zero>[01])$"),
    "02": re.compile(
        rf"^BE_B0:02 SBI spec=(?P<spec>{HEX}) impl=(?P<impl>{HEX}) "
        rf"impl_version=(?P<impl_version>{HEX})$"),
    "03": re.compile(
        r"^BE_B0:03 EXT dbcn=(?P<dbcn>[01]) srst=(?P<srst>[01]) "
        r"hsm=(?P<hsm>[01])$"),
    "04": re.compile(
        rf"^BE_B0:04 HS satp=(?P<satp>{HEX}) sstatus=(?P<sstatus>{HEX}) "
        rf"hstatus=(?P<hstatus>{HEX}) sp=(?P<sp>{HEX}) "
        rf"stack=(?P<stack>{HEX})$"),
    "05": re.compile(
        rf"^BE_B0:05 FDT (?:skipped|magic=(?P<fdt_magic>{HEX}) "
        rf"totalsize=(?P<fdt_totalsize>{HEX}))$"),
    "06": re.compile(
        rf"^BE_B0:06 BE-K3-L0BOOT PASS image_end=(?P<image_end>{HEX})$"),
    "07": re.compile(r"^BE_B0:07 SRST_SHUTDOWN$"),
}
TRAP = re.compile(
    rf"^BE_B0:FAIL TRAP scause=(?P<scause>{HEX}) sepc=(?P<sepc>{HEX}) "
    rf"stval=(?P<stval>{HEX})$")


def extract(text):
    """Return every complete B0 marker line, in capture order."""
    markers = []
    for raw in text.replace("\r", "").split("\n"):
        start = raw.find("BE_B0:")
        if start >= 0:
            markers.append(raw[start:].rstrip())
    return markers


def evaluate(markers, expect, base=None, hart=None, sequence=PASS_SEQUENCE):
    """Return (ok, findings, fields) for one capture."""
    findings = []
    fields = {}
    failures = [line for line in markers if line.startswith("BE_B0:FAIL")]

    if expect == "pass":
        numbered = [line for line in markers
                    if re.match(r"^BE_B0:\d\d ", line)]
        ids = [line[6:8] for line in numbered]
        if tuple(ids) != sequence:
            findings.append(f"marker sequence {ids} != {list(sequence)}")
        for line in numbered:
            pattern = PATTERNS.get(line[6:8])
            match = pattern.match(line) if pattern else None
            if match is None:
                findings.append(f"malformed marker: {line!r}")
                continue
            fields.update({k: v for k, v in match.groupdict().items()
                           if v is not None})
        if failures:
            findings.append(f"failure markers present: {failures}")
        if fields.get("bss_zero") != "1":
            findings.append("BSS was not observed zero")
        if fields.get("dbcn") != "1" or fields.get("srst") != "1":
            findings.append("DBCN and SRST must both be available")
        if fields.get("satp") not in (None, "0x" + "0" * 16):
            findings.append(f"satp is not Bare: {fields.get('satp')}")
        if "fdt_magic" in fields and fields["fdt_magic"] != "0x00000000d00dfeed":
            findings.append(f"FDT magic mismatch: {fields['fdt_magic']}")
        if base is not None and fields.get("base") != f"0x{base:016x}":
            findings.append(f"base {fields.get('base')} != 0x{base:016x}")
        if hart is not None and fields.get("hart") != f"0x{hart:016x}":
            findings.append(f"hart {fields.get('hart')} != 0x{hart:016x}")
        if "sp" in fields and "stack" in fields and "image_end" in fields:
            sp = int(fields["sp"], 16)
            if not int(fields["stack"], 16) < sp <= int(fields["image_end"], 16):
                findings.append("sp lies outside the private B0 stack")
    elif expect == "trap":
        traps = [TRAP.match(line) for line in failures]
        traps = [match for match in traps if match is not None]
        if not traps:
            findings.append("no BE_B0:FAIL TRAP marker")
        else:
            fields.update(traps[0].groupdict())
        if any(line.startswith("BE_B0:06 ") for line in markers):
            findings.append("PASS marker present in an expected-trap run")
    else:
        findings.append(f"unknown expectation {expect!r}")
    return (not findings, findings, fields)


def boot_marker(markers, base=None, hart=None):
    """Judge B0 through the boot marker alone (BE_B0:01-06), so a K3 run
    whose SRST shutdown later returns or stalls still shows whether the
    boot marker was reached with every earlier check satisfied."""
    for index, line in enumerate(markers):
        if line.startswith("BE_B0:06 "):
            return evaluate(markers[:index + 1], "pass", base, hart,
                            PASS_SEQUENCE[:6])[0]
    return False


def terminal(markers):
    """Classify how the run ended after the boot marker."""
    if any(line.startswith("BE_B0:FAIL SRST_RETURNED") for line in markers):
        return "srst-returned"
    if any(line.startswith("BE_B0:FAIL") for line in markers):
        return "fail-marker"
    if "BE_B0:07 SRST_SHUTDOWN" in markers:
        return "srst-shutdown-requested"
    return "none"


def self_test():
    good = (
        "OpenSBI noise\r\n"
        "BE_B0:01 ENTRY hart=0x0000000000000000 base=0x0000000102200000 "
        "fdt=0x00000002f7659000 bss_zero=1\r\n"
        "BE_B0:02 SBI spec=0x0000000002000000 impl=0x0000000000000001 "
        "impl_version=0x0000000000010006\r\n"
        "BE_B0:03 EXT dbcn=1 srst=1 hsm=1\r\n"
        "BE_B0:04 HS satp=0x0000000000000000 sstatus=0x0000000200000000 "
        "hstatus=0x0000000200000000 sp=0x0000000102206f90 "
        "stack=0x0000000102203000\r\n"
        "BE_B0:05 FDT magic=0x00000000d00dfeed "
        "totalsize=0x00000000000098a0\r\n"
        "BE_B0:06 BE-K3-L0BOOT PASS image_end=0x0000000102207000\r\n"
        "BE_B0:07 SRST_SHUTDOWN\r\n")
    cases = [
        ("pass capture", good, "pass", 0x102200000, True),
        ("wrong base", good, "pass", 0x80200000, False),
        ("missing marker", good.replace("BE_B0:05", "BE_B0:5x"), "pass",
         None, False),
        ("fail marker", good + "BE_B0:FAIL SRST_RETURNED error="
         "0xfffffffffffffffe\r\n", "pass", None, False),
        ("dirty bss", good.replace("bss_zero=1", "bss_zero=0"), "pass",
         None, False),
        ("trap capture",
         "BE_B0:01 ENTRY ...\nBE_B0:FAIL TRAP scause=0x0000000000000002 "
         "sepc=0x0000000080200b2c stval=0x0000000060002573\n",
         "trap", None, True),
        ("pass is not trap", good, "trap", None, False),
    ]
    failed = 0
    for name, text, expect, base, wanted in cases:
        ok, findings, _ = evaluate(extract(text), expect, base=base)
        status = "ok  " if ok == wanted else "FAIL"
        if ok != wanted:
            failed += 1
        print(f"{status} {name}: ok={ok} findings={findings}")
    returned = good.replace("BE_B0:07 SRST_SHUTDOWN\r\n",
                            "BE_B0:07 SRST_SHUTDOWN\r\nBE_B0:FAIL SRST_RETURNED "
                            "error=0xfffffffffffffffe\r\n")
    stalled = good.replace("BE_B0:07 SRST_SHUTDOWN\r\n", "")
    split = [
        ("clean run", good, True, "srst-shutdown-requested"),
        ("srst returned", returned, True, "srst-returned"),
        ("stalled after boot", stalled, True, "none"),
        ("dirty bss", good.replace("bss_zero=1", "bss_zero=0"), False,
         "srst-shutdown-requested"),
        ("fail before boot", good.replace(
            "BE_B0:06", "BE_B0:FAIL FDT_MAGIC\r\nBE_B0:06"), False,
         "fail-marker"),
    ]
    for name, text, wanted_boot, wanted_terminal in split:
        markers = extract(text)
        got = (boot_marker(markers, 0x102200000), terminal(markers))
        status = "ok  " if got == (wanted_boot, wanted_terminal) else "FAIL"
        if got != (wanted_boot, wanted_terminal):
            failed += 1
        print(f"{status} {name}: boot_marker={got[0]} terminal={got[1]}")
    print("BE_B0_MARKER_SELF_TEST: " + ("PASS" if failed == 0 else "FAIL"))
    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", nargs="?")
    parser.add_argument("--expect", choices=("pass", "trap"), default="pass")
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
        text = handle.read().decode("utf-8", errors="replace")
    markers = extract(text)
    ok, findings, fields = evaluate(markers, args.expect, args.base, args.hart)
    result = {
        "capture": args.capture,
        "expect": args.expect,
        "result": "PASS" if ok else "FAIL",
        "boot_marker": "PASS" if boot_marker(markers, args.base, args.hart)
        else "FAIL",
        "terminal": terminal(markers),
        "findings": findings,
        "fields": fields,
        "markers": markers,
    }
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
    for line in markers:
        print(line)
    for finding in findings:
        print(f"finding: {finding}")
    if args.expect == "pass":
        print(f"BE_B0_BOOT_MARKER: {result['boot_marker']} "
              f"terminal={result['terminal']}")
    print(f"BE_B0_MARKERS[{args.expect}]: {result['result']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
