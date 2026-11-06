#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Judge the console of a K3 B7 guest's QEMU reference boot
(planning/k3-b7-plan.md, Guest software, Markers, and Tests and evidence;
B6's tests/guest-reference-check.py with the B7 init's lines and a guest ID).

  guest-reference-check.py --console LOG --guest G [--banner TEXT]
                           [--memory-kib N] [--sbi-version V] [--json OUT]
  guest-reference-check.py --self-test

The reference boot runs the pinned Image under plain OpenSBI with guest G's
reference DTB and no monitor, so the console holds OpenSBI's banner, then
the kernel's log and the init's lines, untagged; carriage returns are
dropped. It passes when:
  - OpenSBI reports the runtime SBI version --sbi-version (default 2.0, as
    OpenSBI v1.6 does; QEMU's bundled 1.7 reports 3.0);
  - from the kernel banner on, these lines appear in order, with any other
    lines between them: exactly one banner, equal to --banner when given;
    the plan's command line for guest G (B6's, then `-- be.guest=G`); the
    Sstc timer line; a Memory line whose total is --memory-kib (default
    65536); `Run /init as init process`; the B7INIT lines in the plan's
    formats: 01 START with guest=G and pid=1, 02 UNAME with release=7.2.0
    and machine=riscv64, eight 03 STEP lines n=1/8 to n=8/8, each with
    rounds above 0 and a t_ms at least 75 ms (25 ms of compute and a 50 ms
    sleep) past the step before, 04 SLEEP with 1000-1999 ms and ok=1,
    05 RESULT pass, and 06 POWER_OFF; and `reboot: Power down` as the last
    line;
  - no line from the banner on holds a rejected pattern of the plan's
    Markers section (B6's); "panic" is allowed only in the command line.
With stock OpenSBI the kernel finds more SBI extensions than B7 offers;
that is not judged here.
"""

import argparse
import json
import pathlib
import re
import sys

COMMAND_LINE = ("Kernel command line: earlycon=sbi console=hvc0 panic=-1 "
                "oops=panic panic_on_warn=1 -- be.guest={guest}")
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
STEPS = 8
STEP_MIN_MS = 75


def required(guest, banner, memory_kib):
    """(name, source, pattern): source is 'kernel' (after the printk time)
    or 'init' (a whole untimestamped line)."""
    steps = [(f"init step {n}", "init",
              rf"B7INIT 03 STEP n={n}/{STEPS} rounds=([1-9]\d*) "
              r"t_ms=(\d+)") for n in range(1, STEPS + 1)]
    return [
        ("banner", "kernel", re.escape(banner) if banner
         else r"Linux version .+"),
        ("command line", "kernel",
         re.escape(COMMAND_LINE.format(guest=guest))),
        ("sstc timer", "kernel", re.escape(SSTC)),
        ("memory", "kernel", rf"Memory: \d+K/{memory_kib}K available .*"),
        ("run init", "kernel", re.escape("Run /init as init process")),
        ("init start", "init", rf"B7INIT 01 START guest={guest} pid=1"),
        ("init uname", "init",
         r"B7INIT 02 UNAME release=7\.2\.0 machine=riscv64"),
    ] + steps + [
        ("init sleep", "init",
         r"B7INIT 04 SLEEP requested_ms=1000 elapsed_ms=(\d+) ok=1"),
        ("init result", "init", r"B7INIT 05 RESULT pass"),
        ("init power-off", "init", r"B7INIT 06 POWER_OFF"),
        ("power down", "kernel", re.escape("reboot: Power down")),
    ]


def evaluate(text, guest, banner=None, memory_kib=65536, sbi_version="2.0"):
    """Return (findings, matched lines, elapsed_ms)."""
    lines = text.replace("\r", "").split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    findings, matched, elapsed, step_ms = [], [], None, None
    command_line = COMMAND_LINE.format(guest=guest)
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
                                        line.endswith(command_line)):
                findings.append(f"line {number}: rejected {pattern!r}: "
                                f"{line!r}")
    position = 0
    for name, source, pattern in required(guest, banner, memory_kib):
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
                if name.startswith("init step"):
                    now = int(found.group(2))
                    if step_ms is not None and now < step_ms + STEP_MIN_MS:
                        findings.append(f"{name}: t_ms={now} is not "
                                        f"{STEP_MIN_MS} ms past {step_ms}")
                    step_ms = now
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
STEP_LINES = "\n".join(f"B7INIT 03 STEP n={n}/8 rounds={4000 + n} "
                       f"t_ms={100 + 80 * n}" for n in range(1, 9))


def pass_log(guest):
    return f"""
OpenSBI v1.6
Runtime SBI Version         : 2.0
Domain0 SysReset            : yes
[    0.000000] {BANNER}
[    0.000000] Machine model: Beryllium K3 B7 guest
[    0.000000] {COMMAND_LINE.format(guest=guest)}
[    0.003000] {SSTC}
[    0.100000] Memory: 61944K/65536K available (694K kernel code, 2964K reserved)
[    0.300000] Run /init as init process
B7INIT 01 START guest={guest} pid=1
B7INIT 02 UNAME release=7.2.0 machine=riscv64
{STEP_LINES}
B7INIT 04 SLEEP requested_ms=1000 elapsed_ms=1003 ok=1
B7INIT 05 RESULT pass
B7INIT 06 POWER_OFF
[    1.900000] reboot: Power down
""".replace("\n", "\r\n")


def self_test():
    failures, cases = [], 0

    def expect(text, passes, name, guest=1, **options):
        nonlocal cases
        cases += 1
        findings, _, _ = evaluate(text, guest, **options)
        if passes == bool(findings):
            failures.append(f"{name}: findings {findings}")

    log = pass_log(1)
    lines = log.split("\r\n")
    expect(log, True, "pass", banner=BANNER)
    expect(pass_log(0), True, "pass G0", guest=0, banner=BANNER)
    expect(log, True, "pass without a banner pin")
    expect(log, False, "G1's log as G0's", guest=0)
    expect(log.replace("START guest=1", "START guest=0"), False,
           "the init's ID differs from the command line's")
    expect(log.replace("be.guest=1", "be.guest=0"), False,
           "the command line's ID differs from the init's")
    expect(log, False, "banner pin", banner=BANNER + "x")
    expect(log, False, "memory size", memory_kib=131072)
    expect(log, False, "SBI 3.0", sbi_version="3.0")
    for index, line in enumerate(lines):
        if line.startswith(("[", "B7INIT")) and "Machine model" not in line:
            expect("\r\n".join(lines[:index] + lines[index + 1:]), False,
                   f"without {line!r}")
    expect("\r\n".join(line for line in lines if "Machine model" not in line),
           True, "without an optional line")
    swapped = log.replace("B7INIT 01 START guest=1 pid=1\r\nB7INIT 02 UNAME "
                          "release=7.2.0 machine=riscv64",
                          "B7INIT 02 UNAME release=7.2.0 machine=riscv64"
                          "\r\nB7INIT 01 START guest=1 pid=1")
    expect(swapped, False, "order")
    steps = log.replace("n=3/8 rounds=4003 t_ms=340", "n=x").replace(
        "n=4/8 rounds=4004 t_ms=420", "n=3/8 rounds=4003 t_ms=340").replace(
        "n=x", "n=4/8 rounds=4004 t_ms=420")
    expect(steps, False, "steps out of order")
    for old, new in (("elapsed_ms=1003", "elapsed_ms=999"),
                     ("elapsed_ms=1003", "elapsed_ms=2000"),
                     ("ok=1", "ok=0"), ("pid=1", "pid=2"),
                     ("guest=1 pid", "guest=none pid"),
                     ("guest=1 pid", "guest=2 pid"),
                     ("release=7.2.0", "release=7.2.0+"),
                     ("n=8/8", "n=8/9"), ("n=8/8", "n=9/8"),
                     ("rounds=4005", "rounds=0"), ("rounds=4005", "rounds="),
                     ("t_ms=500", "t_ms=494"), ("t_ms=500", "t_ms=419"),
                     ("RESULT pass", "RESULT fail"),
                     ("Power down", "Restarting system"),
                     ("Runtime SBI Version         : 2.0",
                      "Runtime SBI Version         : 3.0")):
        expect(log.replace(old, new), False, f"{old} -> {new}")
    expect(log.replace("t_ms=500", "t_ms=495"), True, "steps 75 ms apart")
    power = "[    1.900000] reboot: Power down"
    for pattern in REJECTED:
        expect(log.replace(power, f"[    1.200000] x {pattern} y\r\n"
                           + power), False, f"rejected {pattern!r}")
    expect(log.replace(power, power + "\r\nextra"), False, "trailing")
    expect(log.replace(f"[    0.000000] {BANNER}",
                       f"[    0.000000] {BANNER}\r\n"
                       f"[    0.000000] {BANNER}"), False, "two banners")
    expect(log + "\r\n\r\n", True, "trailing blank lines")
    for failure in failures:
        print(f"BE_B7_REFERENCE_SELF_TEST: FAIL {failure}")
    status = "FAIL" if failures else "PASS"
    print(f"BE_B7_REFERENCE_SELF_TEST: {status} cases={cases}")
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--console", type=pathlib.Path)
    parser.add_argument("--guest", type=int, choices=(0, 1))
    parser.add_argument("--banner")
    parser.add_argument("--memory-kib", type=int, default=65536)
    parser.add_argument("--sbi-version", default="2.0")
    parser.add_argument("--json", type=pathlib.Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.console or args.guest is None:
        parser.error("--console and --guest are required")
    text = args.console.read_bytes().decode("ascii", errors="replace")
    findings, matched, elapsed = evaluate(text, args.guest, args.banner,
                                          args.memory_kib, args.sbi_version)
    for line in matched:
        print(line)
    for finding in findings:
        print(f"BE_B7_REFERENCE: FAIL guest={args.guest} {finding}")
    if args.json:
        args.json.write_text(json.dumps({
            "result": "fail" if findings else "pass", "guest": args.guest,
            "findings": findings, "elapsed_ms": elapsed,
            "matched": matched}, indent=2) + "\n", encoding="utf-8")
    if findings:
        return 1
    print(f"BE_B7_REFERENCE: PASS guest={args.guest} lines={len(matched)} "
          f"elapsed_ms={elapsed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
