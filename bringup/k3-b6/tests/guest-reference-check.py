#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Judge the console of the K3 B6 guest's QEMU reference boot
(planning/k3-b6-plan.md, Build, pins, and reproducibility).

  guest-reference-check.py --console LOG [--banner TEXT] [--memory-kib N]
                           [--sbi-version V] [--json OUT]
  guest-reference-check.py --self-test

The reference boot runs the pinned Image under plain OpenSBI with the
reference DTB and no monitor, so the console holds OpenSBI's banner, then
the kernel's log and the init's lines, untagged; carriage returns are
dropped. It passes when:
  - OpenSBI reports the runtime SBI version --sbi-version (default 2.0, as
    OpenSBI v1.6 does; QEMU's bundled 1.7 reports 3.0);
  - from the kernel banner on, these lines appear in order, with any other
    lines between them: exactly one banner, equal to --banner when given;
    the plan's command line; the Sstc timer line; a Memory line whose total
    is --memory-kib (default 65536); `Run /init as init process`; the five
    B6INIT lines with pid=1, release=7.2.0, machine=riscv64, 1000-1999 ms
    and ok=1, and RESULT pass; and `reboot: Power down` as the last line;
  - no line from the banner on holds a rejected pattern of the plan's
    Markers section; "panic" is allowed only in the command line.
With stock OpenSBI the kernel finds more SBI extensions than B6 offers;
that is not judged here.
"""

import argparse
import json
import pathlib
import re
import sys

COMMAND_LINE = ("Kernel command line: earlycon=sbi console=hvc0 panic=-1 "
                "oops=panic panic_on_warn=1")
SSTC = "riscv-timer: Timer interrupt in S-mode is available via sstc extension"
REJECTED = ("panic", "Oops", "WARN", "BUG:", "kernel BUG",
            "Attempted to kill init", "cut here", "Call Trace:",
            "Unable to handle kernel", "rcu: INFO:", "soft lockup",
            "blocked for more than", "segfault", "unhandled signal",
            "extension is not available in SBI", "sbi_srst_reset",
            "No working init found", "Failed to execute", "Out of memory",
            "RESULT fail")
KERNEL = re.compile(r"^\[\s*\d+\.\d+\] (.*)$")
SBI_VERSION = re.compile(r"^Runtime SBI Version\s*:\s*(\S+)\s*$")
SLEEP_MIN_MS, SLEEP_MAX_MS = 1000, 1999


def required(banner, memory_kib):
    """(name, source, pattern): source is 'kernel' (after the printk time)
    or 'init' (a whole untimestamped line)."""
    return [
        ("banner", "kernel", re.escape(banner) if banner
         else r"Linux version .+"),
        ("command line", "kernel", re.escape(COMMAND_LINE)),
        ("sstc timer", "kernel", re.escape(SSTC)),
        ("memory", "kernel", rf"Memory: \d+K/{memory_kib}K available .*"),
        ("run init", "kernel", re.escape("Run /init as init process")),
        ("init start", "init", r"B6INIT 01 START pid=1"),
        ("init uname", "init",
         r"B6INIT 02 UNAME release=7\.2\.0 machine=riscv64"),
        ("init sleep", "init",
         r"B6INIT 03 SLEEP requested_ms=1000 elapsed_ms=(\d+) ok=1"),
        ("init result", "init", r"B6INIT 04 RESULT pass"),
        ("init power-off", "init", r"B6INIT 05 POWER_OFF"),
        ("power down", "kernel", re.escape("reboot: Power down")),
    ]


def evaluate(text, banner=None, memory_kib=65536, sbi_version="2.0"):
    """Return (findings, matched lines, elapsed_ms)."""
    lines = text.replace("\r", "").split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    findings, matched, elapsed = [], [], None
    versions = [m.group(1) for m in map(SBI_VERSION.match, lines) if m]
    if versions != [sbi_version]:
        findings.append(f"firmware SBI versions {versions}, not "
                        f"[{sbi_version!r}]")
    banners = [index for index, line in enumerate(lines)
               if (m := KERNEL.match(line)) and
               m.group(1).startswith("Linux version ")]
    if len(banners) != 1:
        findings.append(f"{len(banners)} kernel banners, not 1")
        return findings, matched, elapsed
    log = lines[banners[0]:]
    for number, line in enumerate(log, banners[0] + 1):
        for pattern in REJECTED:
            if pattern in line and not (pattern == "panic" and
                                        line.endswith(COMMAND_LINE)):
                findings.append(f"line {number}: rejected {pattern!r}: "
                                f"{line!r}")
    position = 0
    for name, source, pattern in required(banner, memory_kib):
        regex = re.compile(pattern + r"$")
        for index in range(position, len(log)):
            body = log[index]
            if source == "kernel":
                stamped = KERNEL.match(body)
                if not stamped:
                    continue
                body = stamped.group(1)
            found = regex.match(body)
            if found:
                matched.append(log[index])
                if name == "init sleep":
                    elapsed = int(found.group(1))
                    if not SLEEP_MIN_MS <= elapsed <= SLEEP_MAX_MS:
                        findings.append(f"elapsed_ms={elapsed} is outside "
                                        f"{SLEEP_MIN_MS}-{SLEEP_MAX_MS}")
                position = index + 1
                break
        else:
            findings.append(f"missing or out of order: {name}")
            return findings, matched, elapsed
    if position != len(log):
        findings.append(f"{len(log) - position} lines after the power-down "
                        f"line, first {log[position]!r}")
    return findings, matched, elapsed


# ------------------------------------------------------------- self-test
BANNER = ("Linux version 7.2.0 (be@beryllium) (riscv64-linux-gnu-gcc) "
          "#1 PREEMPT Sun Aug 16 21:32:26 UTC 2026")
PASS_LOG = f"""
OpenSBI v1.6
Runtime SBI Version         : 2.0
Domain0 SysReset            : yes
[    0.000000] {BANNER}
[    0.000000] Machine model: Beryllium K3 B6 guest
[    0.000000] {COMMAND_LINE}
[    0.003000] {SSTC}
[    0.100000] Memory: 61944K/65536K available (694K kernel code, 2964K reserved)
[    0.300000] Run /init as init process
B6INIT 01 START pid=1
B6INIT 02 UNAME release=7.2.0 machine=riscv64
B6INIT 03 SLEEP requested_ms=1000 elapsed_ms=1003 ok=1
B6INIT 04 RESULT pass
B6INIT 05 POWER_OFF
[    1.300000] reboot: Power down
""".replace("\n", "\r\n")


def self_test():
    failures, cases = [], 0

    def expect(text, passes, name, **options):
        nonlocal cases
        cases += 1
        findings, _, _ = evaluate(text, **options)
        if passes == bool(findings):
            failures.append(f"{name}: findings {findings}")

    lines = PASS_LOG.split("\r\n")
    expect(PASS_LOG, True, "pass", banner=BANNER)
    expect(PASS_LOG, True, "pass without a banner pin")
    expect(PASS_LOG, False, "banner pin", banner=BANNER + "x")
    expect(PASS_LOG, False, "memory size", memory_kib=131072)
    expect(PASS_LOG, False, "SBI 3.0", sbi_version="3.0")
    for index, line in enumerate(lines):
        if line.startswith(("[", "B6INIT")) and "Machine model" not in line:
            expect("\r\n".join(lines[:index] + lines[index + 1:]), False,
                   f"without {line!r}")
    expect("\r\n".join(line for line in lines if "Machine model" not in line),
           True, "without an optional line")
    swapped = PASS_LOG.replace("B6INIT 01 START pid=1\r\nB6INIT 02 UNAME "
                               "release=7.2.0 machine=riscv64",
                               "B6INIT 02 UNAME release=7.2.0 machine=riscv64"
                               "\r\nB6INIT 01 START pid=1")
    expect(swapped, False, "order")
    for old, new in (("elapsed_ms=1003", "elapsed_ms=999"),
                     ("elapsed_ms=1003", "elapsed_ms=2000"),
                     ("ok=1", "ok=0"), ("pid=1", "pid=2"),
                     ("release=7.2.0", "release=7.2.0+"),
                     ("RESULT pass", "RESULT fail"),
                     ("Power down", "Restarting system"),
                     ("Runtime SBI Version         : 2.0",
                      "Runtime SBI Version         : 3.0")):
        expect(PASS_LOG.replace(old, new), False, f"{old} -> {new}")
    power = "[    1.300000] reboot: Power down"
    for pattern in REJECTED:
        expect(PASS_LOG.replace(power, f"[    1.200000] x {pattern} y\r\n"
                                + power), False, f"rejected {pattern!r}")
    expect(PASS_LOG.replace(power, power + "\r\nextra"), False, "trailing")
    expect(PASS_LOG.replace(f"[    0.000000] {BANNER}",
                            f"[    0.000000] {BANNER}\r\n"
                            f"[    0.000000] {BANNER}"), False, "two banners")
    expect(PASS_LOG + "\r\n\r\n", True, "trailing blank lines")
    for failure in failures:
        print(f"BE_B6_REFERENCE_SELF_TEST: FAIL {failure}")
    status = "FAIL" if failures else "PASS"
    print(f"BE_B6_REFERENCE_SELF_TEST: {status} cases={cases}")
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--console", type=pathlib.Path)
    parser.add_argument("--banner")
    parser.add_argument("--memory-kib", type=int, default=65536)
    parser.add_argument("--sbi-version", default="2.0")
    parser.add_argument("--json", type=pathlib.Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.console:
        parser.error("--console is required")
    text = args.console.read_bytes().decode("ascii", errors="replace")
    findings, matched, elapsed = evaluate(text, args.banner, args.memory_kib,
                                          args.sbi_version)
    for line in matched:
        print(line)
    for finding in findings:
        print(f"BE_B6_REFERENCE: FAIL {finding}")
    if args.json:
        args.json.write_text(json.dumps({
            "result": "fail" if findings else "pass",
            "findings": findings, "elapsed_ms": elapsed,
            "matched": matched}, indent=2) + "\n", encoding="utf-8")
    if findings:
        return 1
    print(f"BE_B6_REFERENCE: PASS lines={len(matched)} elapsed_ms={elapsed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
