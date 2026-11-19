#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""Judge one boundary-on run's end state against its declaration.

  check-boundary.py check --oracle STEM.oracle.json --console CAPTURE
      --expect IMAGE.json --tables PAIR-pmp.json --pmp-mode plain|smepmp
      --partition-authority REPORT --firmware-elf FW_ELF --nm NM
      --layout mvp-layout.h [--boundary-header mvp-boundary.h]
      --out STEM.boundary.txt
  check-boundary.py words --expect IMAGE.json --layout mvp-layout.h
      [--boundary-header mvp-boundary.h] [--extra WORDS] --out WORDS
  check-boundary.py not-applicable --out STEM.boundary.txt
  check-boundary.py gate --expect IMAGE.json --record RECORD --dtb DTB
      --tables PAIR-pmp.json
  check-boundary.py breach --plan PLAN --oracle STEM.oracle.json
      --out STEM.breach.txt
  check-boundary.py halt --oracle STEM.oracle.json --console CAPTURE
      --expect IMAGE.json --firmware-elf FW_ELF --nm NM --out STEM.halt.txt
  check-boundary.py --self-test --scratch DIR

Purpose: D-10's four checks of a boundary-on run (planning/mvp-m11-plan.md,
D-10; M11-7's step 1, the VS-domain harts confined and the control hart
not, and M11-8's step 2, the control hart confined too), from what the
QEMU oracle (tests/qemu_oracle.py) read with the machine stopped and what
M-mode printed:

  1. Tables. Harts 0 to 2 each in the state the expectation's boundary
     section declares: confined, the backend's confined table of the
     paired image for the run's PMP mode, equal to M-mode's readback as
     read from its commit record and as printed, menvcfg.CBIE zero in both,
     and mseccfg equal to the record's with MML set under Smepmp, absent
     with the record's zero under plain PMP; boot, the backend's boot
     table and not committed; never-started, every entry off and not
     committed; started (a VS-domain hart of an outcome that fails after
     BE_MVP:07, :08, or :09, by rule), by the capture's lines for it: with
     its BE_MVP:09 HART_READY, every rule of confined; with its BE_MVP:08
     HART_STARTED alone, the confined rules when the read says committed
     and no comparison of the entries when it does not, the printed record
     never committed where the read is not, and both readbacks equal when
     both are; with neither, never-started's. A hart declared confined has
     its READY line in the capture, one declared never-started no start
     line, and one declared boot its start line alone. The control hart
     (hart 0) is boot under a step-1 tree; under a step-2 tree it is
     declared boot only where the run failed in boot code (a FAIL of class
     boundary or hart-start, or no BE_MVP:07), and confined only where the
     capture holds both VS-domain harts' BE_MVP:08 lines and no FAIL of
     either class (C-1, M11-8). Configuration bytes
     are compared for all sixteen entries, an address only where the entry
     is not off. The committed harts are the ones so judged confined, and
     a started one only where the read says so.
  2. Harts 3 to 7: every entry off, not committed, and each one's program
     counter inside the firmware, [_fw_start, _fw_end) from RAM's base.
  3. Identity: the banner's configuration digest is the partition
     authority's identity of the image the declaration names (the paired
     image's, unless a negative names another), and equals BE_MVP:02's
     identity where the monitor printed one.
  4. Counts: each hart's PMP faults, blocked calls, and failed calls, as
     read and as printed, are the declared ones, zero unless declared.

Where a declaration names VS domains in "phase" (ring-full), each one's
state word (phase, low half; failure class, high half) is read from its
private-state extent by the oracle, at the offset mvp-boundary.h states,
and must be FAILED with the class ring. `words` writes that oracle words
file (with --extra's words and device registers added). A run that
cannot be judged (an input missing, malformed, or refused) still has its
record: the one line `BE_MVP_BOUNDARY: FAIL <reason>`.

--fallthrough checks a run under the tree of the expectation's pair in
which no monitor ran (the U-Boot rehearsal's fall-through): the
expectation's declaration with harts 1 and 2 never started and hart 0
boot (no monitor confined it), the banner's digest and no printed record
(the run ends with no reset).

M11-B (planning/mvp-m11-board-addendum.md, B-2): a declaration's "reset"
names a run whose machine halts. `halt`, for the board's firmware
("firmware": "board", whose tables are made from its own ELF, as the
base's are): the banner's one shutdown device is halt and its one reboot
device none (---), and hart 0's program counter lies inside
sbi_hart_hang, by its place and size in the run's firmware ELF (the
lock's nm -S; an ELF with the symbol absent, twice, or without a size is
refused). `absent`, for the base firmware on a tree that holds a digest:
the banner shows neither device, and M-mode prints no record, having no
reset device to report at. "tree": "built-in" (the board's firmware
alone) marks a firmware that carries the run's tree.

`halt` judges a boundary-off run whose firmware halts (the expectation's
top-level halt mark; its boundary record stays not applicable): the run
ended at its halt line; the banner's one reboot device none and one
shutdown device halt; no digest, no record; hart 0 inside sbi_hart_hang
and every other hart inside sbi_hsm_init, the base's HSM wait.

`breach` judges a breach image's run (M11-7; D-10's hostile-monitor rows)
by its plan (tools/gen-breach.py plan): the hook's record, which the
oracle read where the plan places it (the hooked VS-domain hart's
mailbox, or since M11-8 the control hart's control tail), done once,
every row run, and no unexpected trap; each row's slot, its trap's cause
and stval, the value it kept, and the call's error, as the plan has them
for a boundary-on or an -off run; each witness word and device register
at its value; and writes STEM.breach.txt, one line per row and the
verdict line `BE_MVP_BREACH: PASS` or `FAIL`, or the one line
`BE_MVP_BREACH: FAIL <reason>` when the run cannot be judged.

`judge_board()` judges a boundary-on boot of the board from a card
(M11-B, planning/mvp-m11-board-addendum.md, B-8) for tests/check-capture.py
--mode card: no oracle reads the board, so the printed records alone are
judged, against the declaration, the gate's board.json, the tables' plain
PMP mode, and the partition authority, and its line claims no reading
(`witness=printed`; `hook=not-read` for a breach image, whose hook keeps
its record in memory).

`gate` is the run harness's admission of a boundary-on run's device tree
(D-3, D-10): the run starts only if the partition checker's record of the
paired image (tests/check-partition.py --record) passed, names the
declaration's control hart, and gives this tree's and these tables'
SHA-256; or, for a
run whose declaration names a boundary negative and the checker's refusal
of its tree (M11-7, A-9), only by that tree's own record
(tests/boundary-negatives.py record), which names that negative, the
refusal declared, the declaration's step, and this tree's and these
tables' SHA-256. A negative's record admits no other run. It prints `BE_MVP_BOUNDARY_GATE: ADMIT` or
`REFUSE <reason>` and exits 0 or 1.

Every artifact names its tree's step: the declaration's control_hart,
boot (step 1) or confined (step 2), must be the tables document's, and the
result line says it. A boundary-off run's file is the one line
`BE_MVP_BOUNDARY: NOT-APPLICABLE boundary=off`.

Trust: a test checker; it reads its inputs once, runs only the lock's nm
on the firmware's ELF, and writes only --out. Scope: QEMU's k3-like
machine, eight harts, the M11 firmware's commit records (struct
sbi_dcommit_hart), and the backend's tables (tools/partition-backend.py).
"""

import argparse
import contextlib
import hashlib
import io
import json
import pathlib
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qemu_oracle  # noqa: E402 pylint: disable=wrong-import-position

HARTS = 8
VS_HARTS = (1, 2)
STATES = ("confined", "boot", "never-started", "started")
# M11-8: a tree's step, by its control hart's state; the classes that only
# the control hart's boot code prints after the barrier (C-1 for hart 0).
CONTROL_HART = ("boot", "confined")
BOOT_FAILURES = ("boundary", "hart-start")
FAIL_CLASS = re.compile(r"BE_MVP:FAIL ([a-z0-9-]+)")
BARRIER = "BE_MVP:07 "
# A-1 and C-1 (M11-7's review): a VS-domain hart may be declared started,
# between its start and its confinement when the run ends, only where the
# outcome fails after the barrier and before both READY lines; the
# capture's BE_MVP:08 and BE_MVP:09 lines for it then decide its rules.
STARTING = ("BE_MVP:07", "BE_MVP:08", "BE_MVP:09")
LIFE = re.compile(r"BE_MVP:(?:(08) HART_STARTED|(09) HART_READY) "
                  r"hart=([0-9]+) ")
COUNTS = ("pmp_faults", "blocked_calls", "failed_calls")
FIELDS = ("committed",) + COUNTS + ("menvcfg", "mseccfg")
PMP_A_MASK = 0x18
MSECCFG_MML = 0x1
MENVCFG_CBIE = 0x30
DIGEST = re.compile(r"Domain commit digest\s*:\s*([0-9a-f]{64})")
RECORD = re.compile(r"Domain commit hart([0-9]+): (.*)")
COUNTS_FORM = re.compile(r"committed=([01]) pmp_faults=([0-9]+) "
                         r"blocked_calls=([0-9]+) failed_calls=([0-9]+)")
CONTROL_FORM = re.compile(r"menvcfg=0x([0-9a-f]{16}) mseccfg=0x([0-9a-f]{16})")
CFG_FORM = re.compile(r"pmpcfg=([0-9a-f]{32})")
ADDR_FORM = re.compile(r"pmpaddr(0|8)=((?:0x[0-9a-f]{16},){7}0x[0-9a-f]{16})")
FIRMWARE_ON = re.compile(r"BE_MVP:02 FIRMWARE_PROBED .* "
                         r"identity=(none|[0-9a-f]{64})")
EXPECTED_DETAIL = re.compile(r"BE_MVP:DETAIL boundary=1 expected=([0-9a-f]{64})")
DEFINE = re.compile(r"^#define\s+BE_MVP_(\w+)\s+BE_MVP_C\((0x[0-9a-fA-F]+|"
                    r"[0-9]+)\)", re.M)
NOT_APPLICABLE = "BE_MVP_BOUNDARY: NOT-APPLICABLE boundary=off\n"
TABLE_SCHEMA = "be-pmp-tables-v1"
# M11-B: the firmware a run boots, how its machine halts, the banner's
# reset devices, and the symbol in which the halt-only device stops hart 0.
FIRMWARES = ("base", "no-boundary", "board")
RESETS = ("halt", "absent")
DEVICE_LINE = re.compile(r"Platform (Reboot|Shutdown) Device\s*: (\S+)")
HANG = "sbi_hart_hang"
HSM_WAIT = "sbi_hsm_init"
HALT_MARK = {"firmware": "board", "tree": "built-in"}
NM_SIZED = re.compile(r"([0-9a-f]+) ([0-9a-f]+) [A-Za-z] (\S+)")


class Refused(Exception):
    """An input the checker cannot judge."""


def defines(path):
    return {name: int(value, 0) for name, value in
            DEFINE.findall(pathlib.Path(path).read_text(encoding="utf-8"))}


def sized_symbol(text, name):
    """NAME's address and size in TEXT, nm -S's output: defined once, with a
    size (C-2)."""
    found = []
    for line in text.splitlines():
        if line.split()[-1:] != [name]:
            continue
        match = NM_SIZED.fullmatch(line.strip())
        if not match or not int(match.group(2), 16):
            raise Refused(f"{name} has no size in the firmware's ELF")
        found.append((int(match.group(1), 16), int(match.group(2), 16)))
    if len(found) != 1:
        raise Refused(f"{name} is defined {len(found)} times in the "
                      f"firmware's ELF, not once")
    return found[0]


def declaration(expect):
    """The expectation's boundary section, its form checked."""
    boundary = expect.get("boundary")
    if not isinstance(boundary, dict):
        raise Refused("the expectation declares no boundary")
    known = {"control_hart", "pair", "identity", "record", "firmware",
             "harts", "counts", "phase", "negative", "refusal",
             "fallthrough", "reset", "tree"}
    if set(boundary) - known or not {"control_hart", "pair", "record",
                                     "harts"} <= set(boundary):
        raise Refused("the boundary section is not of its form")
    harts = boundary["harts"]
    if not isinstance(harts, dict) or set(harts) != {"0", "1", "2"} or \
            any(state not in STATES for state in harts.values()):
        raise Refused("the boundary section declares no state for harts 0 "
                      "to 2")
    if boundary["control_hart"] not in CONTROL_HART:
        raise Refused(f"the boundary section's control_hart "
                      f"{boundary['control_hart']!r} is not boot or "
                      f"confined")
    if harts["0"] not in CONTROL_HART:
        raise Refused(f"the boundary section declares hart 0 "
                      f"{harts['0']}; the control hart is boot or confined")
    if boundary["control_hart"] == "boot" and harts["0"] != "boot":
        raise Refused(f"the boundary section declares hart 0 {harts['0']} "
                      f"under a step-1 tree, which leaves it boot")
    firmware, reset = boundary.get("firmware", "base"), boundary.get("reset")
    if firmware not in FIRMWARES or reset not in RESETS + (None,):
        raise Refused(f"the boundary section's firmware {firmware!r} or "
                      f"reset {reset!r} is not of its form")
    if boundary.get("tree", "built-in") != "built-in" or \
            ("tree" in boundary and firmware != "board"):
        raise Refused(f"the boundary section's tree "
                      f"{boundary['tree']!r} is not the board firmware's "
                      f"built-in one")
    if (reset == "halt" and firmware != "board") or \
            (reset == "absent" and (firmware != "base" or
                                    not boundary["record"])):
        raise Refused(f"the boundary section declares reset {reset} for "
                      f"the {firmware} firmware" + (
                          "" if boundary["record"] else
                          " on a tree that holds no digest"))
    return boundary


def record_words(record, table):
    """{hart: [24 words]} from the oracle's t<hart>-<index> words, each at
    its place in the firmware's table."""
    words = {item["name"]: item for item in record["words"]}
    out, findings = {}, []
    for hart in range(HARTS):
        values = []
        for index in range(qemu_oracle.RECORD_WORDS):
            item = words.get(f"t{hart}-{index}")
            address = table + 8 * (hart * qemu_oracle.RECORD_WORDS + index)
            if item is None:
                raise Refused(f"the oracle read no t{hart}-{index}")
            if int(item["address"], 16) != address:
                findings.append(f"t{hart}-{index} was read at "
                                f"{item['address']}, not 0x{address:016x}")
            values.append(int(item["value"], 16))
        out[hart] = values
    return out, findings


def decode(values):
    """One hart's commit record: its fields, configuration bytes, and
    addresses (struct sbi_dcommit_hart)."""
    fields = dict(zip(FIELDS, values[:6]))
    cfg = list(values[6].to_bytes(8, "little") +
               values[7].to_bytes(8, "little"))
    return fields, cfg, values[8:24]


def registers(hart):
    cfg = list(int(hart["pmpcfg0"], 16).to_bytes(8, "little") +
               int(hart["pmpcfg2"], 16).to_bytes(8, "little"))
    return cfg, [int(value, 16) for value in hart["pmpaddr"]]


def printed(text):
    """The banner's digest lines and M-mode's printed records, by hart."""
    digests, records = [], {}
    for line in text.replace("\r", "").split("\n"):
        match = DIGEST.fullmatch(line)
        if match:
            digests.append(match.group(1))
        match = RECORD.fullmatch(line)
        if match:
            records.setdefault(int(match.group(1)), []).append(
                match.group(2))
    return digests, records


def lifecycle(text):
    """Each hart's BE_MVP:08 and BE_MVP:09 lines in the capture, hart 0's
    own at a line's start: {hart: {"08", "09"}}."""
    seen = {}
    for line in text.replace("\r", "").split("\n"):
        match = LIFE.match(line)
        if match:
            seen.setdefault(int(match.group(3)), set()).add(
                match.group(1) or match.group(2))
    return seen


def effective_states(expect, states, seen, findings):
    """The state each hart is judged in: a started hart's by its lines in
    the capture (its READY, confined; its start alone, started; neither,
    never started); each other VS-domain hart's declared state checked
    against them."""
    outcome = expect.get("outcome") or {}
    starting = "fail" in outcome and outcome.get("after") in STARTING
    out = dict(states)
    for hart in VS_HARTS:
        lines, state = seen.get(hart, set()), states[hart]
        what = f"hart {hart} ({state})"
        if state == "started":
            if not starting:
                findings.append(f"{what}: started is declared only where "
                                f"the outcome fails after BE_MVP:07, :08, "
                                f"or :09")
            out[hart] = "confined" if "09" in lines else \
                "started" if "08" in lines else "never-started"
        elif state == "confined" and "09" not in lines:
            findings.append(f"{what}: the capture has no BE_MVP:09 "
                            f"HART_READY for it")
        elif state == "never-started" and "08" in lines:
            findings.append(f"{what}: the capture has its BE_MVP:08 "
                            f"HART_STARTED")
        elif state == "boot" and lines != {"08"}:
            findings.append(f"{what}: the capture's BE_MVP:08 and :09 "
                            f"lines for it are {sorted(lines)}, not its "
                            f"BE_MVP:08 alone")
    return out


def control_findings(boundary, text, seen):
    """C-1 for the control hart (M11-8), from the run's own lines (under
    a step-1 tree it is boot, which declaration() requires): under a
    step-2 tree, declared boot, the run failed in its boot code (its first
    FAIL of class boundary or hart-start, or no BE_MVP:07 line); declared
    confined, both VS-domain harts' BE_MVP:08 lines are in the capture and
    no FAIL of either class."""
    state = boundary["harts"]["0"]
    if boundary["control_hart"] == "boot":
        return []
    lines = text.replace("\r", "").split("\n")
    failed = [match.group(1) for match in map(FAIL_CLASS.match, lines)
              if match]
    barrier = any(line.startswith(BARRIER) for line in lines)
    what = f"hart 0 ({state})"
    if state == "boot":
        if barrier and not (failed and failed[0] in BOOT_FAILURES):
            return [f"{what}: the capture passed BE_MVP:07 and its first "
                    f"FAIL is {failed[0] if failed else 'none'}, not "
                    f"boundary or hart-start"]
        return []
    findings = []
    if any("08" not in seen.get(hart, set()) for hart in VS_HARTS):
        findings.append(f"{what}: the capture has not both VS-domain harts' "
                        f"BE_MVP:08 HART_STARTED")
    if any(klass in BOOT_FAILURES for klass in failed):
        findings.append(f"{what}: the capture has a FAIL of class "
                        f"{next(k for k in failed if k in BOOT_FAILURES)}, "
                        f"which only boot code prints")
    return findings


def printed_record(lines):
    """One hart's printed lines as (fields, cfg, addr), or None if not of
    the patch's form; cfg and addr are None for an uncommitted hart."""
    match = COUNTS_FORM.fullmatch(lines[0]) if lines else None
    if not match:
        return None
    fields = dict(zip(("committed",) + COUNTS,
                      (int(value) for value in match.groups())))
    if not fields["committed"]:
        return (fields, None, None) if len(lines) == 1 else None
    if len(lines) != 5:
        return None
    control, cfg, low, high = (CONTROL_FORM.fullmatch(lines[1]),
                               CFG_FORM.fullmatch(lines[2]),
                               ADDR_FORM.fullmatch(lines[3]),
                               ADDR_FORM.fullmatch(lines[4]))
    if not (control and cfg and low and high and low.group(1) == "0" and
            high.group(1) == "8"):
        return None
    fields["menvcfg"] = int(control.group(1), 16)
    fields["mseccfg"] = int(control.group(2), 16)
    addresses = [int(value, 16) for value in
                 (low.group(2) + "," + high.group(2)).split(",")]
    return fields, list(bytes.fromhex(cfg.group(1))), addresses


def table_of(tables, mode, hart, state):
    rows = [row for row in tables["modes"][mode]
            if row["hart"] == hart and row["state"] == state]
    if len(rows) != 1:
        raise Refused(f"the tables have no one {state} table for hart "
                      f"{hart} under {mode}")
    return rows[0]["entries"]


def against_table(what, cfg, addr, entries):
    findings = []
    for index, entry in enumerate(entries):
        wanted = int(entry["config"], 16)
        if cfg[index] != wanted:
            findings.append(f"{what}: pmp{index}cfg 0x{cfg[index]:02x}, "
                            f"expected 0x{wanted:02x}")
        elif wanted & PMP_A_MASK:
            if entry["address"] == "not-compared":
                findings.append(f"{what}: entry {index} is active but the "
                                f"table names no address")
            elif addr[index] != int(entry["address"], 16):
                findings.append(f"{what}: pmpaddr{index} 0x{addr[index]:x}, "
                                f"expected {entry['address']}")
    return findings


def same_readback(what, cfg, addr, other_cfg, other_addr):
    findings = []
    for index in range(16):
        if cfg[index] != other_cfg[index]:
            findings.append(f"{what}: pmp{index}cfg 0x{cfg[index]:02x} and "
                            f"0x{other_cfg[index]:02x}")
        elif cfg[index] & PMP_A_MASK and addr[index] != other_addr[index]:
            findings.append(f"{what}: pmpaddr{index} 0x{addr[index]:x} and "
                            f"0x{other_addr[index]:x}")
    return findings


def confined_findings(hart, mode, oracle_hart, fields, cfg, addr, shown,
                      entries):
    """D-10's rules for a confined hart (and a started one read
    committed): the oracle's table, the record's readback, and what M-mode
    printed of it."""
    what = f"hart {hart}"
    read_cfg, read_addr = registers(oracle_hart)
    findings = against_table(f"{what} as read", read_cfg, read_addr, entries)
    findings += same_readback(f"{what} read and its commit record", read_cfg,
                              read_addr, cfg, addr)
    menvcfg = oracle_hart["menvcfg"]
    if not menvcfg.startswith("0x") or int(menvcfg, 16) & MENVCFG_CBIE:
        findings.append(f"{what}: menvcfg {menvcfg} as read has CBIE set")
    if fields["menvcfg"] & MENVCFG_CBIE:
        findings.append(f"{what}: the record's menvcfg "
                        f"0x{fields['menvcfg']:x} has CBIE set")
    mseccfg = oracle_hart["mseccfg"]
    if mode == "smepmp":
        if not mseccfg.startswith("0x") or \
                int(mseccfg, 16) != fields["mseccfg"] or \
                not fields["mseccfg"] & MSECCFG_MML:
            findings.append(f"{what}: mseccfg {mseccfg} as read, "
                            f"0x{fields['mseccfg']:x} recorded, not equal "
                            f"with MML set")
    elif mseccfg != "absent" or fields["mseccfg"]:
        findings.append(f"{what}: under plain PMP mseccfg is {mseccfg} as "
                        f"read and 0x{fields['mseccfg']:x} recorded")
    if shown is not None and shown[1] is not None:
        shown_fields, shown_cfg, shown_addr = shown
        findings += same_readback(f"{what} printed and read", shown_cfg,
                                  shown_addr, cfg, addr)
        for name in ("menvcfg", "mseccfg"):
            if shown_fields[name] != fields[name]:
                findings.append(f"{what}: printed {name} "
                                f"0x{shown_fields[name]:x}, recorded "
                                f"0x{fields[name]:x}")
    return findings


def judge(expect, record, text, tables, mode, authority, symbols,
          layout=None, header=None, hang=None):
    """(findings, facts) of D-10's four checks for one run; HANG,
    sbi_hart_hang's place and size in the run's firmware, for a run whose
    machine halts (M11-B)."""
    boundary = declaration(expect)
    if tables.get("schema") != TABLE_SCHEMA:
        raise Refused(f"the tables are not of schema {TABLE_SCHEMA}")
    image = expect["image"]
    findings, facts = [], {"image": image, "pair": boundary["pair"],
                           "pmp_mode": mode,
                           "control_hart": boundary["control_hart"]}
    if tables.get("control_hart") != boundary["control_hart"]:
        findings.append(f"the declaration's control_hart "
                        f"{boundary['control_hart']!r} is not the tables' "
                        f"{tables.get('control_hart')!r}")
    if record.get("result", {}).get("verdict") != "PASS":
        raise Refused("the oracle's read did not complete")
    classes = record["register_classes"]
    if mode not in ("plain", "smepmp") or classes["mseccfg"] != (
            "readable" if mode == "smepmp" else "absent"):
        raise Refused(f"PMP mode {mode} does not fit the oracle's mseccfg "
                      f"class {classes['mseccfg']}")
    oracle_harts = {int(hart["mhartid"], 16): hart
                    for hart in record["harts"]}
    if sorted(oracle_harts) != list(range(HARTS)) or any(
            int(hart["cpu_index"], 16) != number
            for number, hart in oracle_harts.items()):
        raise Refused("the oracle did not read harts 0 to 7 in order")
    table = qemu_oracle.FIRMWARE_BASE + symbols[qemu_oracle.RECORD_SYMBOL]
    words, found = record_words(record, table)
    findings += found
    digests, shown_lines = printed(text)
    shown = {}
    reset = boundary.get("reset")
    # A fall-through ends with no reset, and a firmware with no reset device
    # resets nothing, so M-mode prints no record in either.
    if boundary["record"] and not boundary.get("fallthrough") and \
            reset != "absent":
        if sorted(shown_lines) != list(range(HARTS)):
            findings.append(f"M-mode printed records for harts "
                            f"{sorted(shown_lines)}, not 0 to 7")
        for hart, lines in shown_lines.items():
            shown[hart] = printed_record(lines)
            if shown[hart] is None:
                findings.append(f"hart {hart}'s printed record is not of "
                                f"its form")
    elif shown_lines:
        findings.append("M-mode printed a commit record, but the tree holds "
                        "no digest" if not boundary["record"] else
                        "M-mode printed a commit record, but the run's "
                        "firmware has no reset device" if reset == "absent"
                        else "M-mode printed a commit record in a "
                        "fall-through")
    elif digests and not boundary["record"]:
        findings.append("M-mode printed a digest, but the tree holds no "
                        "digest")
    if reset is not None:
        devices = [match.groups() for match in map(
            DEVICE_LINE.fullmatch, text.replace("\r", "").split("\n"))
            if match]
        for kind, wanted in (("Reboot", "---"), ("Shutdown", "halt" if
                                                 reset == "halt" else "---")):
            found = [name for line, name in devices if line == kind]
            if found != [wanted]:
                findings.append(f"the banner's {kind.lower()} devices are "
                                f"{found}, not [{wanted!r}]")
    if reset == "halt":
        if hang is None:
            raise Refused(f"a run whose machine halts needs {HANG}'s place "
                          f"and size")
        pc, start = int(oracle_harts[0]["pc"], 16), \
            qemu_oracle.FIRMWARE_BASE + hang[0]
        if not start <= pc < start + hang[1]:
            findings.append(f"hart 0: pc 0x{pc:x} outside {HANG} "
                            f"[0x{start:x}, 0x{start + hang[1]:x})")
    declared_states = {int(hart): state
                       for hart, state in boundary["harts"].items()}
    declared_states.update({hart: "never-started"
                            for hart in range(3, HARTS)})
    seen = lifecycle(text)
    states = effective_states(expect, declared_states, seen, findings)
    findings += control_findings(boundary, text, seen)
    committed = set()
    for hart in range(HARTS):
        fields, cfg, addr = decode(words[hart])
        state, oracle_hart = states[hart], oracle_harts[hart]
        what = f"hart {hart} ({state})"
        mine = shown.get(hart)
        if fields["committed"] not in (0, 1):
            findings.append(f"{what}: committed={fields['committed']}")
        if fields["committed"]:
            committed.add(hart)
        if mine is not None and mine[0]["committed"] and \
                not fields["committed"]:
            findings.append(f"{what}: printed committed but read not")
        if state == "confined" or (state == "started" and
                                   fields["committed"]):
            findings += confined_findings(
                hart, mode, oracle_hart, fields, cfg, addr, mine,
                table_of(tables, mode, hart, "confined"))
            if state == "confined" and mine is not None and \
                    not mine[0]["committed"]:
                findings.append(f"{what}: printed not committed")
        elif state in ("boot", "never-started"):
            read_cfg, read_addr = registers(oracle_hart)
            findings += against_table(f"{what} as read", read_cfg, read_addr,
                                      table_of(tables, mode, hart, state))
            if fields["committed"]:
                findings.append(f"{what}: committed")
        wanted = boundary.get("counts", {}).get(str(hart), {})
        for name in COUNTS:
            value = wanted.get(name, 0)
            if fields[name] != value:
                findings.append(f"{what}: {name}={fields[name]} as read, "
                                f"declared {value}")
            if mine is not None and mine[0][name] != fields[name]:
                findings.append(f"{what}: {name}={mine[0][name]} printed, "
                                f"{fields[name]} read")
        if hart >= 3:
            pc = int(oracle_hart["pc"], 16)
            start = qemu_oracle.FIRMWARE_BASE + symbols["_fw_start"]
            end = qemu_oracle.FIRMWARE_BASE + symbols["_fw_end"]
            if not start <= pc < end:
                findings.append(f"{what}: pc 0x{pc:x} outside the firmware "
                                f"[0x{start:x}, 0x{end:x})")
    declared = {hart for hart, state in states.items() if state == "confined"}
    maybe = {hart for hart, state in states.items() if state == "started"}
    if not declared <= committed <= declared | maybe:
        findings.append(f"committed harts {sorted(committed)}, declared "
                        f"{sorted(declared)}")
    identities = {row["image"]: row["identity"]
                  for row in authority["descriptors"]}
    named = boundary.get("identity", boundary["pair"])
    for name in {boundary["pair"], named}:
        if name not in identities:
            raise Refused(f"the partition authority names no {name}")
    if "negative" not in boundary and \
            tables.get("descriptor_identity") != identities[boundary["pair"]]:
        findings.append(f"the tables are not the paired image "
                        f"{boundary['pair']}'s")
    facts["identity"] = identities[named]
    if boundary["record"]:
        if digests != [identities[named]]:
            findings.append(f"the banner's digests {digests}, expected "
                            f"{named}'s {identities[named]}")
        for line in text.replace("\r", "").split("\n"):
            match = FIRMWARE_ON.search(line)
            if match and match.group(1) != "none" and \
                    match.group(1) not in digests:
                findings.append(f"BE_MVP:02's identity {match.group(1)} is "
                                f"not the banner's")
    if named != boundary["pair"]:
        # The monitor's DETAIL names its own identity, the paired image's.
        shown_expected = EXPECTED_DETAIL.findall(text)
        if shown_expected != [identities[boundary["pair"]]]:
            findings.append(f"the DETAIL's expected identities "
                            f"{shown_expected}, not {boundary['pair']}'s "
                            f"{identities[boundary['pair']]}")
    for domain in boundary.get("phase", ()):
        if layout is None or header is None:
            raise Refused("phase words need the layout and mvp-boundary.h")
        address, value = phase_word(domain, layout, header)
        item = next((word for word in record["words"]
                     if word["name"] == f"phase-g{domain}"), None)
        if item is None or int(item["address"], 16) != address:
            findings.append(f"VS domain {domain}'s state word was not read "
                            f"at 0x{address:x}")
        elif int(item["value"], 16) != value:
            findings.append(f"VS domain {domain}'s state word "
                            f"{item['value']}, expected 0x{value:016x} "
                            f"(FAILED, ring)")
    facts["harts"] = ",".join(
        f"{hart}:{declared_states[hart]}" + (
            f">{states[hart]}" if states[hart] != declared_states[hart]
            else "") for hart in range(3))
    return findings, facts


# M11-B: what a board image never declares (no such run is made on the
# board), so a declaration that names one cannot be judged by judge_board().
BOARD_REFUSED = ("identity", "phase", "negative", "refusal", "fallthrough")


def board_refusal(expect, tables, authority):
    """Why a boundary-on boot of the board cannot be judged with EXPECT,
    TABLES, and the partition AUTHORITY, or None: a declaration not of its
    form or naming what BOARD_REFUSED lists; tables not of their schema,
    without the plain PMP mode (the board's, B-6), of another step, or
    without a confined table for a hart declared confined or started; an
    authority with no row for the declared pair."""
    try:
        boundary = declaration(expect)
    except Refused as error:
        return str(error)
    odd = [key for key in BOARD_REFUSED if key in boundary]
    if odd:
        return f"the boundary section declares {', '.join(odd)}, which " \
            f"no board image does"
    if not isinstance(tables, dict) or tables.get("schema") != TABLE_SCHEMA:
        return f"the tables are not of schema {TABLE_SCHEMA}"
    if "plain" not in (tables.get("modes") or {}):
        return "the tables have no plain PMP mode, the board's (B-6)"
    if tables.get("control_hart") != boundary["control_hart"]:
        return f"the tables' control_hart {tables.get('control_hart')!r} " \
            f"is not the declaration's {boundary['control_hart']!r}"
    try:
        for hart, state in boundary["harts"].items():
            if state in ("confined", "started"):
                table_of(tables, "plain", int(hart), "confined")
    except Refused as error:
        return str(error)
    except (KeyError, TypeError, AttributeError):
        return "the tables' plain PMP mode is not of its form"
    if not authority_rows(authority).get(boundary["pair"]):
        return f"the partition authority names no {boundary['pair']}"
    return None


def authority_rows(authority):
    """The partition authority's identities, by image, of its rows that
    are of their form."""
    rows = authority.get("descriptors") if isinstance(authority, dict) \
        else None
    return {row["image"]: row["identity"] for row in rows or ()
            if isinstance(row, dict) and isinstance(row.get("image"), str)
            and isinstance(row.get("identity"), str)}


def judge_board(expect, board, text, tables, authority):
    """(findings, facts) of a boundary-on boot of the board from a card
    (M11-B, B-8; tests/check-capture.py --mode card), from TEXT, the whole
    capture, and BOARD, the gate's board.json. No oracle reads the board:
    what M-mode printed is the only source, and the facts claim no reading.
    Each record of the control hart and the VS-domain harts by its
    declared state (C-1's, by the capture's lines, as judge() has it):
    confined, committed, with its plain PMP confined table's configuration
    bytes, an address where the entry is not off, menvcfg.CBIE clear, and
    mseccfg zero; a started hart, those rules where it printed committed;
    any other, not committed. Each parked hart's, not committed (B-3). Each
    count the declared sum, zero unless declared. The committed harts the
    declared ones. The tables the paired image's; board.json's digest, the
    banner's, and BE_MVP:02's identity the partition authority's of the
    pair. The records' form, number, and order are the capture checker's
    (record_block()); a hart with no record of that form is left to it."""
    why = board_refusal(expect, tables, authority)
    if why:
        raise Refused(why)
    boundary, findings = expect["boundary"], []
    identity = authority_rows(authority)[boundary["pair"]]
    digests, shown_lines = printed(text)
    declared = {int(hart): state for hart, state in boundary["harts"].items()}
    seen = lifecycle(text)
    states = effective_states(expect, declared, seen, findings)
    findings += control_findings(boundary, text, seen)
    roles = {hart["hartid"]: hart["role"] for hart in board["harts"]}
    committed, others = set(), {}
    for hart, role in roles.items():
        shown = printed_record(shown_lines.get(hart, []))
        state = "parked" if role == "parked" else states[hart]
        if role == "parked":
            kind = "unprinted" if shown is None else "committed" if \
                shown[0]["committed"] else "uncommitted"
            others[kind] = others.get(kind, 0) + 1
        if shown is None:
            continue
        fields, cfg, addr = shown
        what = f"hart {hart} ({state})"
        committed |= {hart} if fields["committed"] else set()
        if state == "confined" and not fields["committed"]:
            findings.append(f"{what}: printed not committed")
        elif state in ("confined", "started") and fields["committed"]:
            findings += against_table(f"{what} printed", cfg, addr, table_of(
                tables, "plain", hart, "confined"))
            if fields["menvcfg"] & MENVCFG_CBIE:
                findings.append(f"{what}: the printed menvcfg "
                                f"0x{fields['menvcfg']:016x} has CBIE set")
            if fields["mseccfg"]:
                findings.append(f"{what}: under plain PMP the printed "
                                f"mseccfg is 0x{fields['mseccfg']:x}, not 0")
        elif fields["committed"]:
            findings.append(f"{what}: printed committed")
        wanted = boundary.get("counts", {}).get(str(hart), {})
        findings += [f"{what}: {name}={fields[name]} printed, declared "
                     f"{wanted.get(name, 0)}" for name in COUNTS
                     if fields[name] != wanted.get(name, 0)]
    confined = {hart for hart, state in states.items() if state == "confined"}
    started = {hart for hart, state in states.items() if state == "started"}
    if not confined <= committed <= confined | started:
        findings.append(f"committed harts {sorted(committed)}, declared "
                        f"{sorted(confined)}")
    if tables.get("descriptor_identity") != identity:
        findings.append(f"the tables are not the paired image "
                        f"{boundary['pair']}'s")
    if board.get("digest") != identity:
        findings.append(f"board.json's digest {board.get('digest')} is not "
                        f"the partition authority's identity of "
                        f"{boundary['pair']}, {identity}")
    if digests != [identity]:
        findings.append(f"the banner's digests {digests}, expected "
                        f"{boundary['pair']}'s {identity}")
    for line in text.replace("\r", "").split("\n"):
        match = FIRMWARE_ON.search(line)
        if match and match.group(1) != "none" and \
                match.group(1) not in digests:
            findings.append(f"BE_MVP:02's identity {match.group(1)} is not "
                            f"the banner's")
    facts = {"image": expect["image"], "pair": boundary["pair"],
             "pmp_mode": "plain", "control_hart": boundary["control_hart"],
             "harts": ",".join(f"{hart}:{declared[hart]}" + (
                 f">{states[hart]}" if states[hart] != declared[hart]
                 else "") for hart in range(3)),
             "others": ",".join(f"{count}:{kind}" for kind, count in
                                sorted(others.items())) or "none",
             "witness": "printed", "identity": identity[:12]}
    # The hook keeps its record in memory, which nothing reads on the board.
    facts.update({"hook": "not-read"} if "breach" in expect else {})
    return findings, facts


def board_line(findings, facts):
    """judge_board()'s verdict line, which says what M-mode printed."""
    return f"BE_MVP_BOUNDARY: {'FAIL' if findings else 'PASS'} " + " ".join(
        f"{key}={value}" for key, value in facts.items())


BREACH_PLAN = "be-mvp-breach-plan-v1"
BREACH_FIELDS = ("cause", "stval", "value", "error")
BREACH_SLOT_BYTES = 32
BREACH_STATES = {0: "never ran", 1: "did not finish", 2: "done",
                 3: "ran again"}


def breach_name(*parts):
    """A breach word's name, as tools/gen-breach.py's word_name() gives it
    to the oracle: lower case, by tests/qemu_oracle.py's NAME."""
    return "-".join(("breach",) + tuple(str(part) for part in parts)).lower()


def judge_breach(plan, record):
    """(findings, lines, facts) of a breach image's run against its PLAN:
    the hook's record, each row's slot, each witness word, and each device
    register, as the oracle read them."""
    if plan.get("schema") != BREACH_PLAN:
        raise Refused(f"the plan is not of schema {BREACH_PLAN}")
    if record.get("result", {}).get("verdict") != "PASS":
        raise Refused("the oracle's read did not complete")
    words = {}
    for item in record.get("words", []):
        words[item["name"]] = int(item["value"], 16)

    def word(name):
        if name not in words:
            raise Refused(f"the oracle read no {name}")
        return words[name]

    def wanted(text, row):
        if isinstance(text, dict):
            return word(breach_name(row, "end"))
        return {"none": int(plan["no_trap"], 16),
                "sentinel": int(plan["sentinel"], 16)}.get(text) \
            if text in ("none", "sentinel") else int(text, 16)
    findings, lines = [], []
    header = [word(breach_name("header", index))
              for index in range(plan["header_words"])]
    magic, state, rows, domain, slot = header[:5]
    resume, cause, sepc, stval = header[5:9]
    last = int(plan["record"], 16) + 8 * plan["header_words"] + \
        BREACH_SLOT_BYTES * (len(plan["rows"]) - 1)
    if magic != int(plan["magic"], 16):
        findings.append(f"the record's magic is 0x{magic:x}, not the "
                        f"hook's")
    if state != plan["done"]:
        findings.append(f"the hook {BREACH_STATES.get(state, 'is in state')}"
                        f" ({state})")
    if rows != len(plan["rows"]):
        findings.append(f"the hook ran {rows} rows, not "
                        f"{len(plan['rows'])}")
    if domain != plan["domain"]:
        # M11-8: the control hart's hook names its role's word.
        findings.append(f"the hook's record names 0x{domain:x}, not the "
                        f"control role's 0x{plan['domain']:x}"
                        if plan.get("role") == "control" else
                        f"the hook ran on VS domain {domain}, not "
                        f"{plan['domain']}")
    if resume or cause or sepc or stval:
        findings.append(f"an unexpected trap: cause 0x{cause:x} at sepc "
                        f"0x{sepc:x}, stval 0x{stval:x}, continuation "
                        f"0x{resume:x}")
    if slot != last:
        findings.append(f"the frame's last slot is 0x{slot:x}, not the "
                        f"last row's 0x{last:x}")
    if any(header[9:]):
        findings.append("the record's header holds words past its frame")
    for row in plan["rows"]:
        name = row["row"]
        bad = []
        for field in BREACH_FIELDS:
            got, want = word(breach_name(name, field)), \
                wanted(row[field], name)
            if got != want:
                bad.append(f"{field} 0x{got:x}, expected 0x{want:x}")
        findings += [f"row {name}: {item}" for item in bad]
        lines.append(f"row {name} {row['outcome']} cause={row['cause']} "
                     f"stval={row['stval']} "
                     f"{'FAIL' if bad else 'ok'}")
    for item in plan["words"]:
        got = word(breach_name("word", item["address"]))
        if got != int(item["expected"], 16):
            findings.append(f"row {item['row']}'s word {item['address']} "
                            f"is 0x{got:x}, expected {item['expected']}")
    for item in plan["devices"]:
        got = word(breach_name("device", item["row"]))
        if got != int(item["expected"], 16):
            findings.append(f"row {item['row']}'s device register "
                            f"{item['address']} is 0x{got:x}, expected "
                            f"{item['expected']}")
    outcomes = [row["outcome"] for row in plan["rows"]]
    # M11-8: a listed call the firmware rejected, or of no byte, where the
    # plan has one.
    kinds = ("denied", "illegal", "refused", "allowed") + tuple(
        outcome for outcome in ("rejected", "zero") if outcome in outcomes)
    facts = {"image": plan["image"], "boundary": plan["boundary"],
             "hart": plan["hart"], "rows": len(outcomes),
             "outcomes": " ".join(f"{outcome}={outcomes.count(outcome)}"
                                  for outcome in kinds),
             "words": len(plan["words"]), "devices": len(plan["devices"])}
    return findings, lines, facts


def breach_text(findings, lines, facts):
    verdict = "FAIL" if findings else "PASS"
    return "".join(f"finding {item}\n" for item in findings) + \
        "".join(f"{line}\n" for line in lines) + (
            f"BE_MVP_BREACH: {verdict} image={facts['image']} "
            f"boundary={facts['boundary']} hart={facts['hart']} "
            f"rows={facts['rows']} {facts['outcomes']} "
            f"words={facts['words']} devices={facts['devices']}\n")


NEGATIVE_RECORD = "be-boundary-negative-v1"


def gate(expect, record, dtb, tables):
    """The reasons a boundary-on run of EXPECT may not start under the tree
    DTB with the tables TABLES (bytes), by the partition RECORD: the
    checker's passing record of the paired image's tree; or, for a run that
    declares a boundary negative's refused tree (M11-7, A-9), that tree's
    own record (tests/boundary-negatives.py), naming that negative and the
    declared refusal."""
    boundary = declaration(expect)
    reasons = []
    wanted = {"result": "pass", "control_hart": boundary["control_hart"],
              "image": boundary["pair"],
              "dtb_sha256": hashlib.sha256(dtb).hexdigest(),
              "tables_sha256": hashlib.sha256(tables).hexdigest()}
    if "refusal" in boundary:
        wanted.update(schema=NEGATIVE_RECORD, result="refused",
                      negative=boundary.get("negative"),
                      reason=boundary["refusal"])
    elif record.get("schema") == NEGATIVE_RECORD:
        reasons.append("the record is a boundary negative's, which this run "
                       "does not declare")
    for key, value in wanted.items():
        if record.get(key) != value:
            reasons.append(f"the partition record's {key} is "
                           f"{record.get(key)!r}, not {value!r}")
    return reasons


def phase_word(domain, layout, header):
    """VS domain DOMAIN's state word: its address, and its value when the
    domain failed with the class ring."""
    block = layout[f"G{domain}_BLOCK_HPA"]
    address = block + layout["BLOCK_STATE_OFFSET"] + \
        header["BOUNDARY_PHASE_OFFSET"]
    value = header["BOUNDARY_CLASS_RING"] << 32 | \
        header["BOUNDARY_PHASE_FAILED"]
    return address, value


def words_document(expect, layout, header, extra=None):
    """The oracle's --words file for one run: the declared phase words,
    then --extra's words and devices."""
    boundary = declaration(expect)
    words = []
    for domain in boundary.get("phase", ()):
        address, _ = phase_word(domain, layout, header)
        words.append({"name": f"phase-g{domain}",
                      "address": f"0x{address:x}", "expected": None})
    devices = []
    if extra is not None:
        if extra.get("schema") != qemu_oracle.WORDS_SCHEMA:
            raise Refused("the extra words are not of their schema")
        words += extra["words"]
        devices += extra["devices"]
    return {"schema": qemu_oracle.WORDS_SCHEMA, "words": words,
            "devices": devices}


def result_text(findings, facts):
    """The record: each finding, then the verdict line, whose harts= gives
    harts 0 to 2's declared states, DECLARED>JUDGED where the capture's
    lines decided a started hart's rules (C-1)."""
    verdict = "FAIL" if findings else "PASS"
    return "".join(f"finding {item}\n" for item in findings) + (
        f"BE_MVP_BOUNDARY: {verdict} image={facts['image']} "
        f"pair={facts['pair']} pmp_mode={facts['pmp_mode']} "
        f"control_hart={facts['control_hart']} harts={facts['harts']},"
        f"3-7:never-started identity={facts['identity'][:12]}\n")


def write_new(path, text):
    with open(path, "x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def unjudged(path, line):
    """The record of a run that cannot be judged: LINE alone."""
    try:
        write_new(path, " ".join(line.split()) + "\n")
    except OSError as error:
        print(f"BE_MVP_BOUNDARY: FAIL no record written to {path}: {error}")


def fallthrough(expect):
    """EXPECT's declaration for a run under its pair's tree in which no
    monitor ran (the U-Boot rehearsal's fall-through, --fallthrough): the
    VS-domain harts never started, the control hart boot (no monitor ran,
    so none confined it), no state word is read, and, as the run ends with
    no reset, M-mode prints no record."""
    boundary = dict(declaration(expect), fallthrough=True, harts=dict(
        declaration(expect)["harts"], **{"0": "boot", "1": "never-started",
                                         "2": "never-started"}))
    boundary.pop("phase", None)
    return dict(expect, image="fallthrough", boundary=boundary)


def halt_judge(expect, record, text, hang, wait):
    """A boundary-off run whose firmware halts: (findings, image)."""
    # "board" names the firmware's configuration, not the harness's role.
    if "boundary" in expect or expect.get("halt") != HALT_MARK:
        raise Refused("the expectation's halt mark is not of its form")
    if record.get("result", {}).get("verdict") != "PASS":
        raise Refused("the oracle's read did not complete")
    if record.get("end") != {"kind": "stopped-by-harness",
                             "reason": qemu_oracle.HALT_LINE}:
        raise Refused("the run did not end at its halt line")
    findings = []
    devices = [match.groups() for match in map(
        DEVICE_LINE.fullmatch, text.replace("\r", "").split("\n")) if match]
    for kind, wanted in (("Reboot", "---"), ("Shutdown", "halt")):
        found = [name for line, name in devices if line == kind]
        if found != [wanted]:
            findings.append(f"the banner's {kind.lower()} devices are "
                            f"{found}, not [{wanted!r}]")
    digests, shown = printed(text)
    if digests or shown:
        findings.append("M-mode printed a digest or a commit record, but "
                        "the tree holds no digest")
    harts = record.get("harts")
    if not isinstance(harts, list) or len(harts) != HARTS:
        raise Refused(f"the oracle's read holds no {HARTS} harts")
    for hart, entry in enumerate(harts):
        (place, size), name = (hang, HANG) if hart == 0 else (wait, HSM_WAIT)
        pc, start = int(entry["pc"], 16), qemu_oracle.FIRMWARE_BASE + place
        if not start <= pc < start + size:
            findings.append(f"hart {hart}: pc 0x{pc:x} outside {name} "
                            f"0x{start:x}+0x{size:x}")
    return findings, expect["image"]


def halt_text(findings, image):
    return "".join(f"finding {item}\n" for item in findings) + (
        f"BE_MVP_HALT: {'FAIL' if findings else 'PASS'} image={image} "
        f"boundary=off harts=0:{HANG},1-7:{HSM_WAIT}\n")


def halt_check(args):
    listed = subprocess.run([args.nm, "-S", args.firmware_elf],
                            capture_output=True, text=True, check=False)
    if listed.returncode:
        raise Refused("nm -S failed on the firmware's ELF")
    findings, image = halt_judge(
        read_json(args.expect), read_json(args.oracle),
        pathlib.Path(args.console).read_bytes().decode("utf-8", "replace"),
        sized_symbol(listed.stdout, HANG),
        sized_symbol(listed.stdout, HSM_WAIT))
    output = halt_text(findings, image)
    write_new(args.out, output)
    print(output.splitlines()[-1])
    return 1 if findings else 0


def check(args):
    expect = read_json(args.expect)
    if args.fallthrough:
        expect = fallthrough(expect)
    boundary = declaration(expect)
    tables = read_json(args.tables)
    symbols = qemu_oracle.symbol_addresses(
        args.nm, args.firmware_elf,
        ("_fw_start", "_fw_end", qemu_oracle.RECORD_SYMBOL))
    if boundary.get("firmware", "base") in ("base", "board") and \
            hashlib.sha256(pathlib.Path(args.firmware_elf).read_bytes()
                           ).hexdigest() != tables["firmware_sha256"]:
        raise Refused("the firmware's ELF is not the tables' firmware")
    hang = None
    if boundary.get("reset") == "halt":
        listed = subprocess.run([args.nm, "-S", args.firmware_elf],
                                capture_output=True, text=True, check=False)
        if listed.returncode:
            raise Refused("nm -S failed on the firmware's ELF")
        hang = sized_symbol(listed.stdout, HANG)
    text = pathlib.Path(args.console).read_bytes().decode("utf-8", "replace")
    findings, facts = judge(
        expect, read_json(args.oracle), text, tables, args.pmp_mode,
        read_json(args.partition_authority), symbols, defines(args.layout),
        defines(args.boundary_header) if args.boundary_header else None,
        hang)
    output = result_text(findings, facts)
    write_new(args.out, output)
    print(output, end="")
    return 1 if findings else 0


# ------------------------------------------------------------ self-test

def synthetic_tables(control_hart="boot"):
    """Two modes' tables: hart 0's boot table (and under a step-2 tree its
    confined one), harts 1 and 2's boot and confined ones, every hart's
    never-started one."""
    def entries(rows):
        out = [{"index": index, "config": f"0x{config:02x}",
                "address": f"0x{address:x}", "region": f"r{index}"}
               for index, (config, address) in enumerate(rows)]
        return out + [{"index": index, "config": "0x00",
                       "address": "not-compared", "region": "off"}
                      for index in range(len(out), 16)]
    boot = [(0x18, 0x20000fff), (0x1f, (1 << 64) - 1)]
    confined = {0: [(0x1d, 0x408013ff), (0x19, 0x40800bff), (0x18,
                                                             0x20000fff)],
                1: [(0x1b, 0x40801fff), (0x19, 0x40803fff), (0x18,
                                                             0x20000fff)],
                2: [(0x1b, 0x40805fff), (0x19, 0x40807fff), (0x18,
                                                             0x20000fff)]}
    modes = {}
    for mode in ("plain", "smepmp"):
        rows = []
        for hart in range(HARTS):
            rows.append({"hart": hart, "state": "never-started",
                         "entries": entries([])})
            if hart <= 2:
                rows.append({"hart": hart, "state": "boot",
                             "entries": entries(boot)})
            if hart in VS_HARTS or (hart == 0 and
                                    control_hart == "confined"):
                rows.append({"hart": hart, "state": "confined",
                             "profile": f"g{hart - 1}" if hart else
                             "control",
                             "entries": entries(confined[hart])})
        modes[mode] = rows
    return {"schema": TABLE_SCHEMA, "control_hart": control_hart,
            "descriptor_identity": "a" * 64, "firmware_sha256": "f" * 64,
            "base_tree_sha256": "b" * 64, "modes": modes}


SYMBOLS = {"_fw_start": 0, "_fw_end": 0x52000,
           qemu_oracle.RECORD_SYMBOL: 0x41230}
HANG_PLACE = (0x77d2, 0x12)
LAYOUT = {"G0_BLOCK_HPA": 0x102060000, "G1_BLOCK_HPA": 0x102064000,
          "BLOCK_STATE_OFFSET": 0x3000}
HEADER = {"BOUNDARY_PHASE_OFFSET": 0x130, "BOUNDARY_PHASE_FAILED": 2,
          "BOUNDARY_CLASS_RING": 22}


def synthetic_run(mode, states, record=True, counts=None, seen=None,
                  control_hart="boot"):
    """A passing run's oracle record and console for STATES under a tree
    of CONTROL_HART's step: each hart's registers its declared table's,
    its commit record what M-mode keeps, and the console's banner,
    BE_MVP:02, BE_MVP:07, each VS-domain hart's BE_MVP:08 and BE_MVP:09
    lines (SEEN's, or by its state: confined, both; boot or started, its
    start alone), and the printed records."""
    tables = synthetic_tables(control_hart)
    counts = counts or {}
    harts, words, lines = [], [], []
    identity = "a" * 64
    table = qemu_oracle.FIRMWARE_BASE + SYMBOLS[qemu_oracle.RECORD_SYMBOL]
    for hart in range(HARTS):
        state = states.get(hart, "never-started")
        committed = state in ("confined", "started")
        entries = table_of(tables, mode, hart, "confined" if committed
                           else state)
        cfg = [int(entry["config"], 16) for entry in entries]
        addr = [int(entry["address"], 16) if entry["address"] !=
                "not-compared" else 0 for entry in entries]
        mseccfg = 0x7 if mode == "smepmp" and committed else 0
        menvcfg = 0x80000000000000c0 if committed else 0
        harts.append({
            "cpu_index": qemu_oracle.hex64(hart),
            "mhartid": qemu_oracle.hex64(hart),
            "pc": qemu_oracle.hex64(0x80001000 if hart >= 3 else
                                    0x102070000),
            "pmpcfg0": qemu_oracle.hex64(int.from_bytes(bytes(cfg[:8]),
                                                        "little")),
            "pmpcfg2": qemu_oracle.hex64(int.from_bytes(bytes(cfg[8:]),
                                                        "little")),
            "pmpaddr": [qemu_oracle.hex64(value) for value in addr],
            "menvcfg": qemu_oracle.hex64(menvcfg),
            "mseccfg": (qemu_oracle.hex64(mseccfg) if mode == "smepmp"
                        else "absent")})
        values = [int(committed)] + list(counts.get(hart, (0, 0, 0))) + \
            [menvcfg if committed else 0, mseccfg]
        values += [int.from_bytes(bytes(cfg[:8]), "little"),
                   int.from_bytes(bytes(cfg[8:]), "little")] if committed \
            else [0, 0]
        values += addr if committed else [0] * 16
        for index, value in enumerate(values):
            words.append({"name": f"t{hart}-{index}",
                          "address": qemu_oracle.hex64(
                              table + 8 * (hart * 24 + index)),
                          "value": qemu_oracle.hex64(value),
                          "expected": None})
        tag = f"Domain commit hart{hart}: "
        lines.append(tag + f"committed={int(committed)} " + " ".join(
            f"{name}={value}" for name, value in zip(
                COUNTS, counts.get(hart, (0, 0, 0)))))
        if committed:
            lines += [tag + f"menvcfg=0x{menvcfg:016x} "
                      f"mseccfg=0x{mseccfg:016x}",
                      tag + "pmpcfg=" + bytes(cfg).hex(),
                      tag + "pmpaddr0=" + ",".join(f"0x{value:016x}"
                                                   for value in addr[:8]),
                      tag + "pmpaddr8=" + ",".join(f"0x{value:016x}"
                                                   for value in addr[8:])]
    oracle = {"schema": qemu_oracle.SCHEMA,
              "result": {"verdict": "PASS", "detail": "read complete"},
              "end": {"kind": "guest-shutdown", "reason": "guest-shutdown"},
              "register_classes": {
                  "pmp": "readable", "menvcfg": "readable",
                  "mseccfg": "readable" if mode == "smepmp" else "absent"},
              "status_before": None, "harts": harts, "words": words,
              "status_after": None, "qemu_exit": "0x00000000"}
    text = (f"Domain commit digest        : {identity}\n" if record else "")
    text += ("BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 boundary=1 "
             f"status=1:1,2:1 started=none identity={identity}\n")
    text += ("BE_MVP:07 BLOCKS_PUBLISHED region=0x102060000 bytes=0x8000 "
             "generation=1 budget_ticks=0x1\n")
    for hart in VS_HARTS:
        state = states.get(hart, "never-started")
        shown = (seen or {}).get(hart, {"confined": ("08", "09"),
                                        "boot": ("08",),
                                        "started": ("08",)}.get(state, ()))
        if "08" in shown:
            text += (f"BE_MVP:08 HART_STARTED hart={hart} domain={hart - 1} "
                     f"result=0 ticks=0x1\n")
        if "09" in shown:
            text += (f"BE_MVP:09 HART_READY hart={hart} domain={hart - 1} "
                     f"hgatp=0x0\n")
    text += "BE_MVP:14 SHUTDOWN type=0 reason=0\n"
    if record:
        text += "\n".join(lines) + "\n"
    return oracle, text, tables


def synthetic_breach():
    """A small breach plan, as tools/gen-breach.py writes one, and the
    oracle's read of a run that went as planned."""
    record = 0x102048100
    rows = [
        {"row": "A1", "slot": 0, "outcome": "denied", "cause": "0x5",
         "stval": "0x117e00000", "value": "sentinel", "error": "sentinel"},
        {"row": "M1", "slot": 1, "outcome": "refused", "cause": "none",
         "stval": "0x0", "value": "0x0", "error": "0xfffffffffffffffc"},
        {"row": "D5", "slot": 2, "outcome": "allowed", "cause": "none",
         "stval": "0x0", "value": {"end": "0x102084000"},
         "error": "sentinel"},
        {"row": "A2", "slot": 3, "outcome": "denied", "cause": "0x7",
         "stval": "0x117e00008", "value": "sentinel", "error": "sentinel"}]
    plan = {"schema": BREACH_PLAN, "image": "breach-g0", "domain": 0,
            "hart": 1, "boundary": "on", "record": f"0x{record:x}",
            "header_words": 16, "magic": "0x4843414552424542", "done": 2,
            "no_trap": "0xffffffffffffffff",
            "sentinel": "0x5eb55eb55eb55eb5", "rows": rows,
            "words": [{"row": "A2", "address": "0x117e00008",
                       "expected": "0x0"}],
            "devices": [{"row": "I1", "address": "0x10000007", "width": 1,
                         "expected": "0x0"}],
            "counts": {"pmp_faults": 2, "blocked_calls": 1,
                       "failed_calls": 0}}
    header = [0x4843414552424542, 2, 4, 0, record + 128 + 32 * 3] + \
        [0] * 11
    values = {breach_name("header", index): value
              for index, value in enumerate(header)}
    sentinel, none = 0x5eb55eb55eb55eb5, (1 << 64) - 1
    for name, slot in (("A1", (5, 0x117e00000, sentinel, sentinel)),
                       ("M1", (none, 0, 0, 0xfffffffffffffffc)),
                       ("D5", (none, 0, 0x1122334455667788, sentinel)),
                       ("A2", (7, 0x117e00008, sentinel, sentinel))):
        for field, value in zip(BREACH_FIELDS, slot):
            values[breach_name(name, field)] = value
    values["breach-d5-end"] = 0x1122334455667788
    values["breach-word-0x117e00008"] = 0
    values["breach-device-i1"] = 0
    oracle = {"result": {"verdict": "PASS"},
              "words": [{"name": name, "address": "0x0",
                         "value": qemu_oracle.hex64(value),
                         "expected": None}
                        for name, value in values.items()]}
    return plan, oracle


def breach_cases(scratch, cases):
    """The breach judge's cases, appended to CASES."""
    def run(name, change=None, want=None):
        plan, oracle = synthetic_breach()
        if change:
            change(plan, oracle)
        try:
            findings, _, _ = judge_breach(plan, oracle)
        except Refused as error:
            findings = [f"refused: {error}"]
        ok = (not findings) if want is None else \
            any(want in finding for finding in findings)
        cases.append((f"breach: {name}", ok,
                      findings[0] if findings else "passes"))

    def word(name, value):
        def change(plan, oracle):
            item = next(item for item in oracle["words"]
                        if item["name"] == name)
            item["value"] = qemu_oracle.hex64(value)
        return change

    def unread(name):
        def change(plan, oracle):
            oracle["words"] = [item for item in oracle["words"]
                               if item["name"] != name]
        return change
    run("a boundary-on run as planned")
    run("a denied load that was not denied",
        word("breach-a1-cause", (1 << 64) - 1),
        want="row A1: cause 0xffffffffffffffff, expected 0x5")
    run("a denial at another address", word("breach-a2-stval", 0x117e00000),
        want="row A2: stval 0x117e00000, expected 0x117e00008")
    run("a denied load that kept a value", word("breach-a1-value", 0),
        want="row A1: value 0x0, expected 0x5eb55eb55eb55eb5")
    run("a call that was not refused", word("breach-m1-error", 0),
        want="row M1: error 0x0, expected 0xfffffffffffffffc")
    run("an end read that differs from the word at the end",
        word("breach-d5-end", 0x1122334455667789),
        want="row D5: value 0x1122334455667788, expected "
        "0x1122334455667789")
    run("a witness word written", word("breach-word-0x117e00008", 0xb5ea),
        want="row A2's word 0x117e00008 is 0xb5ea, expected 0x0")
    run("a device register written", word("breach-device-i1", 0xa5),
        want="row I1's device register 0x10000007 is 0xa5")
    run("the hook ran again", word("breach-header-1", 3),
        want="the hook ran again (3)")
    run("the hook did not finish", word("breach-header-1", 1),
        want="the hook did not finish (1)")
    run("the record's magic", word("breach-header-0", 0),
        want="the record's magic is 0x0")
    run("fewer rows run", word("breach-header-2", 3),
        want="the hook ran 3 rows, not 4")
    run("the hook on the other VS domain", word("breach-header-3", 1),
        want="the hook ran on VS domain 1, not 0")
    run("an unexpected trap", word("breach-header-6", 0xd),
        want="an unexpected trap: cause 0xd")
    run("a continuation left set", word("breach-header-5", 0x102011000),
        want="continuation 0x102011000")
    run("the frame's last slot", word("breach-header-4", 0x102048180),
        want="the frame's last slot is 0x102048180")
    run("a header word past the frame", word("breach-header-12", 1),
        want="the record's header holds words past its frame")
    run("a slot word unread", unread("breach-a2-error"),
        want="refused: the oracle read no breach-a2-error")
    run("an end word unread", unread("breach-d5-end"),
        want="refused: the oracle read no breach-d5-end")
    run("the oracle's read not complete",
        lambda plan, oracle: oracle["result"].update(verdict="FAIL"),
        want="refused: the oracle's read did not complete")

    def as_control(plan, oracle):
        """M11-8: the plan and the read as the control hart's: its role's
        record word, and a listed call the firmware rejected and one of no
        byte."""
        plan.update(image="breach-c", domain=0xC0, role="control", hart=0)
        none = (1 << 64) - 1
        for name, outcome, error in (("R1", "rejected", (-3) & none),
                                     ("Z1", "zero", 0)):
            plan["rows"].append({"row": name, "slot": len(plan["rows"]),
                                 "outcome": outcome, "cause": "none",
                                 "stval": "0x0", "value": "0x0",
                                 "error": f"0x{error:x}"})
            oracle["words"] += [
                {"name": breach_name(name, field), "address": "0x0",
                 "value": qemu_oracle.hex64(value), "expected": None}
                for field, value in zip(BREACH_FIELDS, (none, 0, 0, error))]
        last = int(plan["record"], 16) + 128 + \
            BREACH_SLOT_BYTES * (len(plan["rows"]) - 1)
        for index, value in ((2, len(plan["rows"])), (3, 0xC0), (4, last)):
            word(f"breach-header-{index}", value)(plan, oracle)

    def then(*changes):
        def change(plan, oracle):
            for item in changes:
                item(plan, oracle)
        return change
    run("the control hart's run as planned", as_control)
    run("the control hart's record naming a VS domain",
        then(as_control, word("breach-header-3", 0)),
        want="the hook's record names 0x0, not the control role's 0xc0")
    run("a listed call refused where the firmware rejects it",
        then(as_control, word("breach-r1-error", (-4) & ((1 << 64) - 1))),
        want="row R1: error 0xfffffffffffffffc, expected "
        "0xfffffffffffffffd")
    plan, oracle = synthetic_breach()
    as_control(plan, oracle)
    last = breach_text(*judge_breach(plan, oracle)).splitlines()[-1]
    cases.append(("breach: the control hart's verdict counts its rejected "
                  "and no-byte calls", last == (
                      "BE_MVP_BREACH: PASS image=breach-c boundary=on "
                      "hart=0 rows=6 denied=2 illegal=0 refused=1 "
                      "allowed=1 rejected=1 zero=1 words=1 devices=1"),
                  last))
    run("another plan schema",
        lambda plan, oracle: plan.update(schema="be-mvp-breach-plan-v0"),
        want="refused: the plan is not of schema")
    plan, oracle = synthetic_breach()
    (scratch / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    (scratch / "oracle.json").write_text(json.dumps(oracle),
                                         encoding="utf-8")
    for name, inputs, status, start in (
            ("a run as planned", ("plan.json", "oracle.json"), 0,
             "row A1 denied"),
            ("a run that cannot be judged", ("plan.json", "missing"), 1,
             "BE_MVP_BREACH: FAIL ")):
        out = scratch / f"{name.replace(' ', '-')}.breach.txt"
        with contextlib.redirect_stdout(io.StringIO()):
            got = main(["check-boundary.py", "breach", "--plan",
                        str(scratch / inputs[0]), "--oracle",
                        str(scratch / inputs[1]), "--out", str(out)])
        text = out.read_text(encoding="utf-8") if out.is_file() else ""
        ok = got == status and text.startswith(start) and (
            status or text.splitlines()[-1].startswith(
                "BE_MVP_BREACH: PASS image=breach-g0 boundary=on hart=1 "
                "rows=4 denied=2 illegal=0 refused=1 allowed=1"))
        cases.append((f"breach: the command, {name}", ok,
                      text.strip().splitlines()[-1] if text else
                      "no record"))


def self_test(scratch):
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True)
    authority = {"descriptors": [
        {"image": "two-guests", "identity": "a" * 64},
        {"image": "two-guests-shell", "identity": "c" * 64}]}
    base_states = {0: "boot", 1: "confined", 2: "confined"}
    cases = []

    def expectation(image="two-guests", harts=None, outcome=None,
                    control_hart="boot", **extra):
        harts = harts or {"0": "boot", "1": "confined", "2": "confined"}
        return {"image": image, "outcome": outcome or {"pass": True},
                "boundary": dict(
                    {"control_hart": control_hart, "pair": "two-guests",
                     "record": True, "harts": harts}, **extra)}

    def run(name, change=None, mode="plain", states=None, expect=None,
            want=None, record=True, counts=None, header=HEADER, seen=None,
            control_hart="boot", hang=None):
        oracle, text, tables = synthetic_run(mode, states or base_states,
                                             record, counts, seen,
                                             control_hart)
        expect = expect or expectation()
        if change:
            text = change(oracle, tables, expect, text) or text
        try:
            findings, _ = judge(expect, oracle, text, tables, mode,
                                authority, SYMBOLS, LAYOUT, header, hang)
        except Refused as error:
            findings = [f"refused: {error}"]
        ok = (not findings) if want is None else \
            any(want in finding for finding in findings)
        cases.append((name, ok, findings[0] if findings else "passes"))

    def oracle_hart(number, key, value):
        def change(oracle, tables, expect, text):
            oracle["harts"][number][key] = value
        return change

    def word(name, value):
        def change(oracle, tables, expect, text):
            item = next(item for item in oracle["words"]
                        if item["name"] == name)
            item["value"] = qemu_oracle.hex64(value)
        return change

    run("step 1, plain")
    run("step 1, Smepmp", mode="smepmp")
    run("an entry off by one bit", oracle_hart(1, "pmpcfg0",
                                               "0x0000000000181b1a"),
        want="hart 1 as read: pmp0cfg")
    run("a stale address in an off entry is ignored",
        oracle_hart(1, "pmpaddr", ["0x0000000040801fff", "0x0000000040803fff",
                                   "0x0000000020000fff"] +
                    ["0x00000000deadbeef"] * 13))
    run("a parked hart's pc outside the firmware",
        oracle_hart(5, "pc", "0x0000000102070000"),
        want="hart 5 (never-started): pc")
    run("a nonzero count", counts={1: (1, 0, 0)},
        want="hart 1 (confined): pmp_faults=1 as read, declared 0")
    run("a declared count", counts={1: (1, 0, 0)},
        expect=expectation(counts={"1": {"pmp_faults": 1}}))
    run("a committed set that differs", word("t2-0", 0),
        want="committed harts [1], declared [1, 2]")
    run("a printed digest that differs",
        lambda oracle, tables, expect, text: text.replace(
            "Domain commit digest        : " + "a" * 64,
            "Domain commit digest        : " + "c" * 64),
        want="the banner's digests")
    run("BE_MVP:02's identity is not the banner's",
        lambda oracle, tables, expect, text: text.replace(
            "identity=" + "a" * 64, "identity=" + "d" * 64),
        want="BE_MVP:02's identity")
    run("a printed record that differs from the read",
        lambda oracle, tables, expect, text: text.replace(
            "Domain commit hart1: pmpaddr0=0x0000000040801fff",
            "Domain commit hart1: pmpaddr0=0x0000000040801ffe"),
        want="hart 1 printed and read: pmpaddr0")
    run("a commit record that differs from the read",
        word("t1-8", 0x40801ffe),
        want="hart 1 read and its commit record: pmpaddr0")
    run("a record word read at another address",
        lambda oracle, tables, expect, text: next(
            item for item in oracle["words"] if item["name"] == "t3-0"
        ).update(address="0x0000000000000000"),
        want="t3-0 was read at")
    run("menvcfg.CBIE set as read", oracle_hart(2, "menvcfg",
                                                "0x80000000000000f0"),
        want="hart 2: menvcfg 0x80000000000000f0 as read has CBIE set")
    run("Smepmp without MML", word("t1-5", 0x6), mode="smepmp",
        want="hart 1: mseccfg")
    run("plain PMP with a recorded mseccfg", word("t2-5", 0x1),
        want="under plain PMP mseccfg")
    run("hart 0 committed", word("t0-0", 1),
        want="hart 0 (boot): committed")
    run("a boot hart's table differs", oracle_hart(0, "pmpaddr",
                                                   ["0x0000000020000ffe"] +
                                                   ["0x0"] * 15),
        want="hart 0 (boot) as read: pmpaddr0")
    run("the tables of step 2 for a step-1 declaration",
        lambda oracle, tables, expect, text:
        tables.update(control_hart="confined"),
        want="the declaration's control_hart 'boot' is not the tables' "
        "'confined'")
    # M11-8: step 2, the control hart confined, and C-1 for hart 0.
    step2 = {0: "confined", 1: "confined", 2: "confined"}

    def second(harts=None, outcome=None, **extra):
        return expectation(harts=harts or {"0": "confined", "1": "confined",
                                           "2": "confined"},
                           outcome=outcome, control_hart="confined", **extra)
    run("step 2, plain", states=step2, expect=second(),
        control_hart="confined")
    run("step 2, Smepmp", mode="smepmp", states=step2, expect=second(),
        control_hart="confined")
    run("step 2: hart 0's table differs", oracle_hart(
        0, "pmpaddr", ["0x00000000408013fe"] + ["0x0"] * 15), states=step2,
        expect=second(), control_hart="confined",
        want="hart 0 as read: pmpaddr0")
    run("step 2: hart 0 printed committed, read not", word("t0-0", 0),
        states=step2, expect=second(), control_hart="confined",
        want="hart 0 (confined): printed committed but read not")
    run("step 2: hart 0 with a fault", counts={0: (1, 0, 0)}, states=step2,
        expect=second(), control_hart="confined",
        want="hart 0 (confined): pmp_faults=1 as read, declared 0")
    run("step 2: hart 0 with its declared fault", counts={0: (1, 0, 0)},
        states=step2, control_hart="confined",
        expect=second(counts={"0": {"pmp_faults": 1}},
                      outcome={"fail": "exception", "after": "BE_MVP:08"}),
        change=lambda oracle, tables, expect, text:
        text + "BE_MVP:FAIL exception\n")
    run("step 2: hart 0 declared boot, the run's lines confined",
        states={0: "boot", 1: "confined", 2: "confined"}, control_hart=
        "confined", expect=second({"0": "boot", "1": "confined",
                                   "2": "confined"}),
        want="hart 0 (boot): the capture passed BE_MVP:07 and its first "
        "FAIL is none")
    run("step 2: hart 0 declared confined, the run failed at a start",
        states=step2, expect=second(), control_hart="confined",
        change=lambda oracle, tables, expect, text:
        text + "BE_MVP:FAIL hart-start\n",
        want="hart 0 (confined): the capture has a FAIL of class "
        "hart-start")
    run("step 2: hart 0 declared confined, a VS-domain hart's start "
        "missing", states={0: "confined", 1: "confined", 2: "never-started"},
        seen={1: ("08", "09"), 2: ()}, control_hart="confined",
        expect=second({"0": "confined", "1": "confined",
                       "2": "never-started"}),
        want="hart 0 (confined): the capture has not both VS-domain harts' "
        "BE_MVP:08")
    run("step 2: a refused confine, hart 0 boot, both harts started",
        states={0: "boot", 1: "confined", 2: "confined"},
        seen={1: ("08",), 2: ("08",)}, control_hart="confined",
        expect=second({"0": "boot", "1": "started", "2": "started"},
                      {"fail": "boundary", "after": "BE_MVP:08"}),
        change=lambda oracle, tables, expect, text:
        text + "BE_MVP:FAIL boundary\n")
    run("step 2: a failure before the barrier, hart 0 boot",
        states={0: "boot", 1: "never-started", 2: "never-started"},
        seen={1: (), 2: ()}, control_hart="confined",
        expect=second({"0": "boot", "1": "never-started",
                       "2": "never-started"},
                      {"fail": "payload", "after": "BE_MVP:03"}),
        change=lambda oracle, tables, expect, text:
        text.replace("BE_MVP:07 ", "BE_MVP:FAIL payload ", 1))
    run("step 1: hart 0 declared confined",
        expect=expectation(harts={"0": "confined", "1": "confined",
                                  "2": "confined"}),
        want="refused: the boundary section declares hart 0 confined under "
        "a step-1 tree")
    run("step 2: hart 0 declared never-started", states=step2,
        control_hart="confined", expect=second(
            {"0": "never-started", "1": "confined", "2": "confined"}),
        want="refused: the boundary section declares hart 0 never-started")
    run("step 2 declared, the tables step 1's", states=base_states,
        expect=second({"0": "boot", "1": "confined", "2": "confined"},
                      {"fail": "boundary", "after": "BE_MVP:08"}),
        change=lambda oracle, tables, expect, text:
        text + "BE_MVP:FAIL boundary\n",
        want="the declaration's control_hart 'confined' is not the tables' "
        "'boot'")
    run("a control hart neither boot nor confined",
        expect=expectation(control_hart="parked"),
        want="refused: the boundary section's control_hart 'parked'")
    run("step 2, the fall-through: no monitor ran, hart 0 boot",
        lambda oracle, tables, expect, text: "=> no monitor ran\n",
        states={0: "boot", 1: "never-started", 2: "never-started"},
        control_hart="confined", record=False,
        expect=fallthrough(second(record=False)))
    run("the tables of another image", lambda oracle, tables, expect, text:
        tables.update(descriptor_identity="e" * 64),
        want="not the paired image")
    run("tables of another schema", lambda oracle, tables, expect, text:
        tables.update(schema="be-partition-tables-v1"),
        want="refused: the tables are not of schema be-pmp-tables-v1")
    run("an incomplete read",
        lambda oracle, tables, expect, text: oracle["result"].update(
            verdict="FAIL"), want="refused: the oracle's read")
    run("a mode that does not fit the read", mode="plain",
        change=lambda oracle, tables, expect, text: oracle[
            "register_classes"].update(mseccfg="readable"),
        want="refused: PMP mode plain")
    run("a hart's printed record of another form",
        lambda oracle, tables, expect, text: text.replace(
            "Domain commit hart4: committed=0",
            "Domain commit hart4: committed=0 extra=1"),
        want="hart 4's printed record is not of its form")
    run("no printed record where the tree holds a digest",
        lambda oracle, tables, expect, text: text.split(
            "Domain commit hart0:")[0],
        want="printed records for harts []")
    run("no digest: nothing printed, counts from the read", record=False,
        expect=expectation(record=False))
    run("a printed record where the tree holds no digest",
        expect=expectation(record=False),
        want="the tree holds no digest")
    def another_identity(expected):
        def change(oracle, tables, expect, text):
            return text.replace("a" * 64, "c" * 64) + \
                f"BE_MVP:DETAIL boundary=1 expected={expected}\n"
        return change
    run("another image's identity, as declared",
        another_identity("a" * 64),
        expect=expectation(identity="two-guests-shell"))
    run("another image's identity, the DETAIL not the image's own",
        another_identity("c" * 64),
        expect=expectation(identity="two-guests-shell"),
        want="the DETAIL's expected identities")
    def records_cut(oracle, tables, expect, text):
        return text.split("Domain commit hart0:")[0]
    run("the fall-through: no VS-domain hart started, no record printed",
        records_cut, states={0: "boot", 1: "never-started",
                             2: "never-started"},
        expect=fallthrough(expectation(phase=[0, 1])))
    run("a printed digest alone where the tree holds none", records_cut,
        expect=expectation(record=False),
        want="printed a digest, but the tree holds no digest")
    run("the fall-through with a printed record",
        states={0: "boot", 1: "never-started", 2: "never-started"},
        expect=fallthrough(expectation()),
        want="a commit record in a fall-through")
    run("the fall-through's read under the scenario's declaration",
        states={0: "boot", 1: "never-started", 2: "never-started"},
        want="committed harts [], declared [1, 2]")
    # A-1 and C-1: a started hart's rules follow the capture's lines.
    started_harts = {"0": "boot", "1": "started", "2": "never-started"}
    at_start = {"fail": "hart-start", "after": "BE_MVP:07"}

    def started(harts=None, outcome=None):
        return expectation("hart-start", harts or started_harts,
                           outcome or at_start)
    alone, ready = {1: ("08",)}, {1: ("08", "09")}
    committed_one = {0: "boot", 1: "confined", 2: "never-started"}

    def printed_uncommitted(oracle, tables, expect, text):
        lines = text.split("\n")
        return "\n".join(
            "Domain commit hart1: committed=0 pmp_faults=0 blocked_calls=0 "
            "failed_calls=0" if line.startswith("Domain commit hart1: "
                                                "committed=") else line
            for line in lines if not (
                line.startswith("Domain commit hart1: ") and
                "committed=" not in line))
    run("started, its start alone: read committed, its confined table",
        states=committed_one, seen=alone, expect=started())
    run("started, its start alone: read not committed, entries not "
        "compared", lambda oracle, tables, expect, text: oracle["harts"][
            1].update(pmpcfg0="0x000000000000001f"),
        states={0: "boot", 1: "boot", 2: "never-started"}, seen=alone,
        expect=started())
    run("started, its start alone: read committed, printed not",
        printed_uncommitted, states=committed_one, seen=alone,
        expect=started())
    run("started, its start alone: read committed with a wrong table",
        oracle_hart(1, "pmpaddr", ["0x0000000040801ffe"] + ["0x0"] * 15),
        states=committed_one, seen=alone, expect=started(),
        want="hart 1 as read: pmpaddr0")
    run("started, its start alone: printed committed, read not",
        word("t1-0", 0), states=committed_one, seen=alone,
        expect=started(), want="printed committed but read not")
    run("started, its start alone: a nonzero count", counts={1: (0, 1, 0)},
        states=committed_one, seen=alone, expect=started(),
        want="blocked_calls=1 as read, declared 0")
    run("started, its READY line: the rules of confined",
        states=committed_one, seen=ready, expect=started())
    run("started, its READY line: not committed",
        states={0: "boot", 1: "boot", 2: "never-started"}, seen=ready,
        expect=started(), want="committed harts [], declared [1]")
    run("started, its READY line: a wrong table",
        oracle_hart(1, "pmpaddr", ["0x0000000040801ffe"] + ["0x0"] * 15),
        states=committed_one, seen=ready, expect=started(),
        want="hart 1 as read: pmpaddr0")
    run("started, its READY line: printed not committed",
        printed_uncommitted, states=committed_one, seen=ready,
        expect=started(), want="hart 1 (confined): printed not committed")
    run("started, neither line: the rules of never-started",
        states={0: "boot", 1: "never-started", 2: "never-started"},
        seen={1: ()}, expect=started())
    run("started, neither line: committed",
        states=committed_one, seen={1: ()}, expect=started(),
        want="hart 1 (never-started): committed")
    run("run-timeout: both started, one ready, one at its start alone",
        states={0: "boot", 1: "confined", 2: "boot"},
        seen={1: ("08", "09"), 2: ("08",)},
        expect=started({"0": "boot", "1": "started", "2": "started"},
                       {"fail": "run-timeout", "after": "BE_MVP:07"}))
    run("confined declared without its READY line", seen=alone,
        want="hart 1 (confined): the capture has no BE_MVP:09 HART_READY")
    run("never-started declared with its BE_MVP:08",
        states=committed_one, seen={1: ("08", "09"), 2: ("08",)},
        expect=started(), want="hart 2 (never-started): the capture has "
        "its BE_MVP:08")
    run("boot declared for a VS-domain hart: its start alone",
        states={0: "boot", 1: "boot", 2: "boot"},
        expect=expectation(harts={"0": "boot", "1": "boot", "2": "boot"},
                           outcome={"fail": "hart-ready",
                                    "after": "BE_MVP:08"}))
    run("boot declared for a VS-domain hart with its READY line",
        states={0: "boot", 1: "boot", 2: "boot"},
        seen={1: ("08", "09"), 2: ("08",)},
        expect=expectation(harts={"0": "boot", "1": "boot", "2": "boot"},
                           outcome={"fail": "hart-ready",
                                    "after": "BE_MVP:08"}),
        want="hart 1 (boot): the capture's BE_MVP:08 and :09 lines for it "
        "are ['08', '09']")
    for label, outcome in (
            ("a passing expectation", {"pass": True}),
            ("a failure after BE_MVP:10", {"fail": "ring",
                                           "after": "BE_MVP:10"}),
            ("a failure before the barrier", {"fail": "payload",
                                              "after": "BE_MVP:03"})):
        run(f"started declared in {label}", states=committed_one,
            seen=alone, expect=started(outcome=outcome),
            want="started is declared only where the outcome fails after")

    def phase(value):
        def change(oracle, tables, expect, text):
            expect["boundary"]["phase"] = [0, 1]
            for domain in (0, 1):
                address, wanted = phase_word(domain, LAYOUT, HEADER)
                oracle["words"].append({
                    "name": f"phase-g{domain}",
                    "address": qemu_oracle.hex64(address),
                    "value": qemu_oracle.hex64(value if value is not None
                                               else wanted),
                    "expected": None})
        return change
    run("ring-full: both VS domains failed with ring", phase(None))
    run("ring-full: a VS domain's phase not failed",
        phase(22 << 32 | 1), want="VS domain 0's state word")
    run("ring-full: the state word unread",
        lambda oracle, tables, expect, text: expect["boundary"].update(
            phase=[1]), want="VS domain 1's state word was not read")

    # M11-B: a run whose machine halts, under the board's firmware (the
    # halt-only device) or the base on a tree without reset devices.
    devices = ("Platform Reboot Device      : ---\n"
               "Platform Shutdown Device    : {}\n")

    def halted(pc=0x800077d4, shutdown="halt", extra=""):
        def change(oracle, tables, expect, text):
            oracle["harts"][0]["pc"] = qemu_oracle.hex64(pc)
            return devices.format(shutdown) + extra + text
        return change

    def no_device(shutdown="---", records=False):
        def change(oracle, tables, expect, text):
            text = text.replace("BE_MVP:07 ", "BE_MVP:FAIL boot ", 1)
            return devices.format(shutdown) + (
                text if records else text.split("Domain commit hart0:")[0])
        return change
    halts = second(firmware="board", reset="halt")
    unstarted = {0: "boot", 1: "never-started", 2: "never-started"}
    absent = second({"0": "boot", "1": "never-started",
                     "2": "never-started"}, {"fail": "boot", "after": "none"},
                    reset="absent")
    for name, change, want, hang in (
            ("hart 0 in sbi_hart_hang", halted(), None, HANG_PLACE),
            ("hart 0 past sbi_hart_hang", halted(0x800077e4),
             "hart 0: pc 0x800077e4 outside sbi_hart_hang", HANG_PLACE),
            ("a shutdown device other than halt",
             halted(shutdown="syscon-poweroff"),
             "the banner's shutdown devices are ['syscon-poweroff']",
             HANG_PLACE),
            ("two reboot device lines",
             halted(extra="Platform Reboot Device      : ---\n"),
             "the banner's reboot devices are ['---', '---']", HANG_PLACE),
            ("no place for sbi_hart_hang", halted(),
             "refused: a run whose machine halts needs sbi_hart_hang", None)):
        run(f"halt: {name}", change, states=step2, expect=halts,
            control_hart="confined", hang=hang, want=want)
    for name, change, want in (
            ("no reset device, no record", no_device(), None),
            ("a printed record", no_device(records=True),
             "the run's firmware has no reset device"),
            ("a shutdown device", no_device("syscon-poweroff"),
             "the banner's shutdown devices are ['syscon-poweroff'], "
             "not ['---']")):
        run(f"absent: {name}", change, states=unstarted, expect=absent,
            seen={1: (), 2: ()}, control_hart="confined", want=want)
    for name, extra, want in (
            ("reset halt for the base firmware", {"reset": "halt"},
             "reset halt for the base firmware"),
            ("reset absent for the board's firmware",
             {"reset": "absent", "firmware": "board"},
             "reset absent for the board firmware"),
            ("reset absent on a tree without a digest",
             {"reset": "absent", "record": False},
             "on a tree that holds no digest"),
            ("an unknown reset", {"reset": "reboot"},
             "reset 'reboot' is not of its form"),
            ("an unknown firmware", {"firmware": "vendor"},
             "firmware 'vendor' or reset None is not of its form"),
            ("a tree built in for the base firmware", {"tree": "built-in"},
             "is not the board firmware's built-in one"),
            ("a tree of another kind", {"firmware": "board", "reset": "halt",
                                        "tree": "vendor"},
             "is not the board firmware's built-in one")):
        run(f"declaration: {name}", states=step2, control_hart="confined",
            expect=second(**extra), want=want)
    run("halt: a tree built in", halted(), states=step2,
        expect=second(firmware="board", reset="halt", tree="built-in"),
        control_hart="confined", hang=HANG_PLACE)
    listing = ("0000000000000000 T _fw_start\n"
               "00000000000077d2 0000000000000012 t sbi_hart_hang\n")
    for name, text, want in (
            ("its place and size", listing, None),
            ("absent", listing.replace("sbi_hart_hang", "sbi_hart_wake"),
             "sbi_hart_hang is defined 0 times"),
            ("defined twice", listing + "0000000000008000 0000000000000012 "
             "t sbi_hart_hang\n", "sbi_hart_hang is defined 2 times"),
            ("without a size", listing.replace("0000000000000012 t", "t"),
             "sbi_hart_hang has no size")):
        try:
            place, detail = sized_symbol(text, HANG), None
        except Refused as error:
            place, detail = None, str(error)
        cases.append((f"nm -S: {HANG} {name}", place == HANG_PLACE
                      if want is None else want in (detail or ""),
                      detail or f"0x{place[0]:x}+0x{place[1]:x}"))
    # halt: a boundary-off run whose firmware halts (k3-first).
    first = {"image": "k3-first", "halt": dict(HALT_MARK)}
    record_line = ("Domain commit hart7: committed=0 pmp_faults=0 "
                   "blocked_calls=0 failed_calls=0\n")
    for name, change, want in (
            ("hart 0 halted, the others waiting", {}, None),
            ("a hart outside the HSM wait", {"pcs": {3: 0x80000000}},
             "hart 3: pc 0x80000000 outside sbi_hsm_init"),
            ("hart 0 outside sbi_hart_hang", {"pcs": {0: 0x800185c0}},
             "hart 0: pc 0x800185c0 outside sbi_hart_hang"),
            ("a printed record", {"text": devices.format("halt") +
                                  record_line}, "printed a digest or"),
            ("a printed digest", {"text": devices.format("halt") +
                                  "Domain commit digest        : " + "ab" * 32
                                  + "\n"}, "printed a digest or"),
            ("a shutdown device other than halt",
             {"text": devices.format("syscon-poweroff")},
             "the banner's shutdown devices are ['syscon-poweroff']"),
            ("an end by the grace", {"end": "grace period after terminal "
                                     "marker"}, "did not end at its halt"),
            ("an incomplete read", {"verdict": "FAIL"}, "did not complete"),
            ("a mark naming the role", {"expect": dict(first, halt={
                "firmware": "first", "tree": "built-in"})},
             "halt mark is not of its form"),
            ("a boundary section too", {"expect": dict(first, boundary={})},
             "halt mark is not of its form")):
        pcs = {hart: 0x800185c0 for hart in range(HARTS)}
        pcs[0] = 0x800077d4
        pcs.update(change.get("pcs", {}))
        record = {"result": {"verdict": change.get("verdict", "PASS")},
                  "end": {"kind": "stopped-by-harness",
                          "reason": change.get("end", qemu_oracle.HALT_LINE)},
                  "harts": [{"pc": qemu_oracle.hex64(pcs[hart])}
                            for hart in range(HARTS)]}
        try:
            findings, _ = halt_judge(change.get("expect", first), record,
                                     change.get("text", devices.format(
                                         "halt")), HANG_PLACE, (0x185b6, 0xea))
            ok = not findings if want is None else \
                any(want in item for item in findings)
            detail = "; ".join(findings) or "accepted"
        except Refused as error:
            ok, detail = want is not None and want in str(error), str(error)
        cases.append((f"halt mode: {name}", ok, detail))
    def words_case():
        expect = expectation(phase=[0, 1])
        document = words_document(expect, LAYOUT, HEADER, {
            "schema": qemu_oracle.WORDS_SCHEMA, "words": [],
            "devices": [{"name": "uart-scratch", "address": "0x10000007",
                         "expected": "0xa5"}]})
        return document["words"][0]["address"] == "0x102063130" and \
            len(document["devices"]) == 1, json.dumps(document)
    try:
        ok, detail = words_case()
    except (Refused, KeyError) as error:
        ok, detail = False, str(error)
    cases.append(("the words file of a ring-full run", ok, detail))

    def unjudged_case(name, expect):
        out = scratch / f"{name}.boundary.txt"
        (scratch / "expect.json").write_text(json.dumps(expect),
                                             encoding="utf-8")
        missing = str(scratch / "missing")
        with contextlib.redirect_stdout(io.StringIO()):
            status = main(["check-boundary.py", "check", "--oracle", missing,
                           "--console", missing, "--expect",
                           str(scratch / "expect.json"), "--tables", missing,
                           "--partition-authority", missing,
                           "--firmware-elf", missing, "--nm", missing,
                           "--layout", missing, "--pmp-mode", "plain",
                           "--out", str(out)])
        text = out.read_text(encoding="utf-8") if out.is_file() else ""
        return (status == 1 and text.startswith("BE_MVP_BOUNDARY: FAIL ")
                and text.count("\n") == 1), text.strip() or "no record"
    for name, expect in (
            ("an input missing", expectation()),
            ("a declaration refused", {"image": "two-guests"})):
        ok, detail = unjudged_case(name.replace(" ", "-"), expect)
        cases.append((f"a run that cannot be judged ({name}) has its "
                      f"record", ok, detail))
    dtb, tables = b"\xd0\x0d\xfe\xed tree", b'{"schema": "tables"}'
    passed = {"result": "pass", "control_hart": "boot", "image": "two-guests",
              "dtb_sha256": hashlib.sha256(dtb).hexdigest(),
              "tables_sha256": hashlib.sha256(tables).hexdigest()}
    for name, edit, want in (
            ("the checker's passing record of this tree", {}, None),
            ("a record that did not pass", {"result": "fail"}, "result"),
            ("a record of step 2's tree for step 1's declaration",
             {"control_hart": "confined"}, "control_hart"),
            ("another image's record", {"image": "two-guests-shell"},
             "image"),
            ("a record of another tree", {"dtb_sha256": "0" * 64},
             "dtb_sha256"),
            ("a record of other tables", {"tables_sha256": "0" * 64},
             "tables_sha256")):
        reasons = gate(expectation(), dict(passed, **edit), dtb, tables)
        ok = not reasons if want is None else \
            len(reasons) == 1 and f"record's {want} is" in reasons[0]
        cases.append((f"the gate: {name}", ok, "; ".join(reasons) or
                      "admitted"))
    # M11-8: a step-2 declaration, by a step-2 record only.
    for name, edit, want in (
            ("step 2's record of this tree for step 2's declaration",
             {"control_hart": "confined"}, None),
            ("step 1's record for step 2's declaration", {},
             "control_hart")):
        reasons = gate(expectation(control_hart="confined", harts={
            "0": "confined", "1": "confined", "2": "confined"}),
            dict(passed, **edit), dtb, tables)
        ok = not reasons if want is None else \
            len(reasons) == 1 and f"record's {want} is" in reasons[0]
        cases.append((f"the gate: {name}", ok, "; ".join(reasons) or
                      "admitted"))
    # A-9: a refused tree, admitted only for the run that declares its
    # negative and reason, by its own record.
    refused = dict(passed, schema=NEGATIVE_RECORD, result="refused",
                   negative="boundary-no-list", reason="be_g0: allow differs")
    declared = expectation(negative="boundary-no-list",
                           refusal="be_g0: allow differs")
    for name, expect, edit, want in (
            ("a refused tree, declared, by its own record", declared, {},
             None),
            ("a refused tree for a run that declares no negative",
             expectation(), {}, "does not declare"),
            ("another negative's record", declared,
             {"negative": "boundary-two-narrow"}, "record's negative is"),
            ("a negative's record of another tree", declared,
             {"dtb_sha256": "0" * 64}, "record's dtb_sha256 is"),
            ("a negative's record with another refusal", declared,
             {"reason": "be_g0: harts differs"}, "record's reason is"),
            ("a negative's record of another step", declared,
             {"control_hart": "confined"}, "record's control_hart is"),
            ("a passing record for a declared refusal", declared,
             {"schema": None, "result": "pass", "negative": None,
              "reason": None}, "record's schema is")):
        reasons = gate(expect, dict(refused, **edit), dtb, tables)
        ok = not reasons if want is None else \
            any(want in reason for reason in reasons)
        cases.append((f"the gate: {name}", ok, "; ".join(reasons) or
                      "admitted"))
    breach_cases(scratch, cases)
    failures = 0
    for name, ok, detail in cases:
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")
    print(f"BE_MVP_BOUNDARY_SELF_TEST: {'PASS' if not failures else 'FAIL'} "
          f"cases={len(cases)}")
    return 1 if failures else 0


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch")
    commands = parser.add_subparsers(dest="command")
    checked = commands.add_parser("check")
    for name in ("oracle", "console", "expect", "tables",
                 "partition-authority", "firmware-elf", "nm", "layout",
                 "out"):
        checked.add_argument(f"--{name}", required=True)
    checked.add_argument("--pmp-mode", choices=("plain", "smepmp"),
                         required=True)
    checked.add_argument("--boundary-header")
    checked.add_argument("--fallthrough", action="store_true")
    words = commands.add_parser("words")
    for name in ("expect", "layout", "out"):
        words.add_argument(f"--{name}", required=True)
    words.add_argument("--boundary-header")
    words.add_argument("--extra")
    absent = commands.add_parser("not-applicable")
    absent.add_argument("--out", required=True)
    admit = commands.add_parser("gate")
    for name in ("expect", "record", "dtb", "tables"):
        admit.add_argument(f"--{name}", required=True)
    breach = commands.add_parser("breach")
    for name in ("plan", "oracle", "out"):
        breach.add_argument(f"--{name}", required=True)
    halted = commands.add_parser("halt")
    for name in ("oracle", "console", "expect", "firmware-elf", "nm",
                 "out"):
        halted.add_argument(f"--{name}", required=True)
    args = parser.parse_args(argv[1:])
    try:
        if args.self_test:
            if not args.scratch:
                parser.error("--self-test requires --scratch")
            return self_test(pathlib.Path(args.scratch))
        if args.command == "check":
            return check(args)
        if args.command == "words":
            document = words_document(
                read_json(args.expect), defines(args.layout),
                defines(args.boundary_header) if args.boundary_header
                else {}, read_json(args.extra) if args.extra else None)
            write_new(args.out, json.dumps(document, indent=1) + "\n")
            return 0
        if args.command == "not-applicable":
            write_new(args.out, NOT_APPLICABLE)
            return 0
        if args.command == "gate":
            reasons = gate(read_json(args.expect), read_json(args.record),
                           pathlib.Path(args.dtb).read_bytes(),
                           pathlib.Path(args.tables).read_bytes())
            print("BE_MVP_BOUNDARY_GATE: " + (
                f"REFUSE {'; '.join(reasons)}" if reasons else "ADMIT"))
            return 1 if reasons else 0
        if args.command == "breach":
            findings, lines, facts = judge_breach(read_json(args.plan),
                                                  read_json(args.oracle))
            text = breach_text(findings, lines, facts)
            write_new(args.out, text)
            print(text.splitlines()[-1])
            return 1 if findings else 0
        if args.command == "halt":
            return halt_check(args)
        parser.error("check, words, not-applicable, gate, breach, halt, or "
                     "--self-test")
    except (Refused, qemu_oracle.OracleError, OSError, ValueError,
            KeyError, TypeError, IndexError) as error:
        line = "BE_MVP_" + {"breach": "BREACH", "halt": "HALT"}.get(
            args.command, "BOUNDARY") + f": FAIL {error}"
        print(line)
        if args.command in ("check", "breach", "halt"):
            unjudged(args.out, line)
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
