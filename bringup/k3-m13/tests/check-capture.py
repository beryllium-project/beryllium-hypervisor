#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""
check-capture.py --image N --mode qemu|board|host --expect FILE
                 [--qemu-harts H] [--image-file IMG] [--expect-end WORD]
                 CAPTURE
check-capture.py --sample --image N --expect FILE
check-capture.py --self-test --image N --expect FILE

The M13-4 probe images' capture check (planning/mvp-m13-3-review-point.md,
sections 2 and 3). The capture's bytes, carriage returns dropped, are cut
into lines; the first that holds `BE_K3_M13: ` starts the image's, and
every later line that is not blank must be a line of the image's grammar,
printable ASCII, at most 120 characters, with the prefix once. The image's
lines are judged against the expected list FILE (tests/m13list.py) by
walking it as the image's program does, each outcome (a value, a fault,
an HSM state) taken from the capture, so that every line that the image
must print is required in its place, and nothing else. The end word is the
capture's: end (END), fail-entry, fail-sbi, fail-hart, fail-trap,
fail-table (that FAIL line), stopped (lines that stop before either), none
(no line of the image's).

qemu: before the image's lines, OpenSBI v1.6's banner once, SBI 2.0, and
the boot hart that ENTRY names; ENTRY's base 0x80200000; SBI's spec 2.0
and impl 1; a read in [0x80000000, 0x80200000) (v1.6's memory) faults
with scause 5 and stval its address, a read in [0x80210000, 0x90000000)
(RAM above the image) does not; no P7 write; --qemu-harts 3: every HSM
line done; 1: every one not-started. board (--image-file the staged
image), each rule from the board's own lines in the MVP's public records
(mvp/results/20261030-com260-rc2/, 20261031-com260-rc3/,
20261105-com260-rc4/): a leading stamp dropped, one autoboot line; after
it, once each and in order, IMG's size read, its MD5 from 0x140000000,
its move to 0x102200000 with its end, the blob, the blob booted, the
device tree loaded to F, `Starting kernel ...`; after that only blank
lines, a stamp alone, and the BSP's two lines; ENTRY's base 0x102200000
and its fdt F. host (the host test's): no line before the image's; the
base is not judged.

It prints `finding: ...` lines, naming capture lines by number and
entries by index, never a line's text, a value, or a path, then
BE_K3_M13_CAPTURE: PASS|FAIL image=N mode=M end=WORD lines=K, and exits 0
when there is no finding and the end is --expect-end's (default end), 1
otherwise, 2 on a usage or list error. Each finding starts with its
rule: [form], [walk], [after], [host], [qemu], or [board]. --sample prints
the lines alone that image N prints on the board when every read gives 0
(entry hart 0, the other harts done), for a stand-in board to play.
--self-test generates runs from the list (that sample, guards passing,
the else branch, faults, a FAIL trap, a stopped run, and for image 1 a
hart timed out and one not started), each wrapped for each mode (the board's
from the RC4 record's loader lines, its size, MD5, and move made the
stand-in image's), requires each to pass with its end, then each mutation
to fail with its own rule.

Trust: test-only and read-only.
"""

import argparse
import hashlib
import importlib.util
import pathlib
import re
import sys

PREFIX = "BE_K3_M13: "
LINE_MAX = 120
STATES = ("done", "timeout", "not-started", "refused", "trapped")
ENDS = ("end", "fail-entry", "fail-sbi", "fail-hart", "fail-trap",
        "fail-table", "stopped", "none")
FIELDS = {"x": r"(0x[0-9a-f]{16})", "d": r"([0-9])",
          "n": r"([A-Za-z0-9_.()\[\]]{1,23})", "w": r"([a-z-]+)"}
FORMS = {
    "entry": "ENTRY image={d} hart={x} base={x} fdt={x}",
    "sbi": "SBI spec={x} impl={x} impl_version={x}",
    "ext": "EXT dbcn=1 srst={d} hsm={d} satp={x}",
    "hsm": "HSM hart={x} error={x} state={w}",
    "value": "P{d} {n} {w} a={x} w={d} value={x}",
    "wrote": "P{d} {n} {w} a={x} w={d} wrote={x}",
    "fault": "P{d} {n} {w} a={x} w={d} fault={x} tval={x}",
    "guard": "P{d} {n} guard expect={x} {w}",
    "end": "END image={d} accesses={x} faults={x}",
    "fail-entry": "FAIL entry hart={x}",
    "fail-sbi": "FAIL sbi srst={d} hsm={d} satp={x}",
    "fail-hart": "FAIL hart hart={x} a0={x}",
    "fail-trap": "FAIL trap hart={x} scause={x} sepc={x} stval={x}",
    "fail-table": "FAIL table index={x}",
}
SPLIT = re.compile(r"\{([xdnw])\}")
PATTERNS = {kind: (re.compile("".join(
    FIELDS[part] if odd else re.escape(part)
    for odd, part in ((i % 2, p) for i, p in enumerate(SPLIT.split(form))))),
    SPLIT.findall(form)) for kind, form in FORMS.items()}
BOARD_BASE, QEMU_BASE, LOAD, FDT = 0x102200000, 0x80200000, 0x140000000, \
    0x2FBD5D000
STAMP = re.compile(r"^\[ *[0-9]+\.[0-9]{3}\] ?")
AUTOBOOT = re.compile(r"Autoboot in [0-9]+ seconds|Hit any key to stop "
                      r"autoboot")
NOISE = ("", "fail to get alias node efuse_power",
         "Removing MTD device #0 (nor0) with use count 1")
RECORD = "mvp/results/20261105-com260-rc4/20261105T222530Z/handoff-excerpt.log"
QEMU_BANNER = re.compile(r"OpenSBI v1\.6")
QEMU_SBI = re.compile(r"Runtime SBI Version\s*: 2\.0")
QEMU_HART = re.compile(r"Boot HART ID\s*: ([0-9]+)")


class Done(Exception):
    """The run's last line was taken: its end word."""


class Wrong(Exception):
    """The line last taken breaks the list's or the program's rules."""


def render(kind, values):
    parts = SPLIT.split(FORMS[kind])
    text = parts[0]
    for key, value, literal in zip(parts[1::2], values, parts[2::2]):
        text += (f"0x{value:016x}" if key == "x" else str(value)) + literal
    return PREFIX + text


def parse_body(body):
    for kind, (pattern, keys) in PATTERNS.items():
        match = pattern.fullmatch(body)
        if match:
            return kind, tuple(int(g, 16) if k == "x" else
                               int(g) if k == "d" else g
                               for k, g in zip(keys, match.groups()))
    return None, None


class Judge:
    """Takes each line from the capture, requiring it to be one of the
    lines that the program may print there."""

    def __init__(self, lines):
        self.lines = lines
        self.position = 0
        self.last = 0
        self.trap_hart = None

    def take(self, wants, where):
        if self.position >= len(self.lines):
            raise Done("stopped")
        number, kind, values = self.lines[self.position]
        self.position += 1
        self.last = number
        want = wants.get(kind)
        if want is not None and all(w is None or w == v
                                    for w, v in zip(want, values)):
            return kind, values
        # After EXT, FAIL trap (the entry hart's) or FAIL table may stand
        # in for any line, and ends the run.
        if self.trap_hart is not None and (
                kind == "fail-table" or
                kind == "fail-trap" and values[0] == self.trap_hart):
            raise Done(kind)
        raise Wrong(f"not {where}")


class Sample:
    """Takes each line as a run of chosen outcomes makes it: entry hart 0
    at BASE, the FDT at RC4's, OpenSBI 1.6's SBI, every read VALUES' (0 by
    default) or a fault if FAULTS has its entry, each other hart done or as
    STATES has it, a FAIL trap in place of entry TRAP. The defaults are
    --sample's."""

    def __init__(self, base=BOARD_BASE, values=None, faults=(), trap=None,
                 states=None):
        self.lines, self.trap_hart = [], None
        self.base, self.values, self.faults = base, values or {}, faults
        self.trap, self.states = trap, states or {}

    def take(self, wants, where):
        index = int(where.split()[1]) if where.startswith("entry ") else None
        if index is not None and index == self.trap:
            self.lines.append(render("fail-trap", (0, 2, self.base, 0)))
            raise Done("fail-trap")
        kind = "fault" if index in self.faults and "fault" in wants else \
            next((k for k in ("entry", "value", "wrote") if k in wants),
                 next(iter(wants)))
        want = wants[kind]
        fill = {"entry": lambda: (None, 0, self.base, FDT),
                "sbi": lambda: (0x2000000, 1, 0x10006),
                "ext": lambda: (1, 1, 0),
                "value": lambda: want[:5] + (self.values.get(index, 0),),
                "fault": lambda: want[:5] + (5 if want[2] == "read" else 7,
                                             want[3]),
                "hsm": lambda: (want[0],) + self.states.get(want[0],
                                                            (0, "done"))}
        values = tuple(w if w is not None else f for w, f in
                       zip(want, fill.get(kind, lambda: want)()))
        self.lines.append(render(kind, values))
        return kind, values


def access(taker, entry, counts, results):
    wants = {"fault": (entry.probe, entry.name, entry.op, entry.address,
                       entry.width, None, None)}
    if entry.op == "read":
        wants["value"] = (entry.probe, entry.name, "read", entry.address,
                          entry.width, None)
    else:
        wants["wrote"] = (entry.probe, entry.name, "write", entry.address,
                          entry.width, entry.value)
    kind, values = taker.take(wants, f"entry {entry.index}")
    counts[0] += 1
    if kind == "fault":
        counts[1] += 1
        results[entry.index] = None
    else:
        results[entry.index] = values[5]


def p1_block(listing, taker, hart, counts):
    """Image 1's P1 (the design's section 2.4): in hart order, an HSM line
    for each hart but the entry hart, then P1's lines for it, if it is the
    entry hart or done."""
    p1 = [e for e in listing.entries if e.probe == 1]
    for other in range(3):
        if other != hart:
            _, (_, error, state) = taker.take({"hsm": (other, None, None)},
                                              f"the HSM line of hart {other}")
            if state not in STATES or (error != 0) != (state == "not-started"):
                raise Wrong("an HSM line's state does not agree with its "
                            "error")
            if state in ("refused", "trapped"):
                kind = "fail-hart" if state == "refused" else "fail-trap"
                taker.take({kind: (other,) + (None,) * (1 if state ==
                                                        "refused" else 3)},
                           f"the FAIL line of hart {other}")
                raise Done(kind)
            if state != "done":
                continue
        for entry in (e for e in p1 if e.hart == other):
            kind = "value" if entry.op == "csrr" else "wrote"
            taker.take({kind: (1, entry.name, entry.op, entry.address, 8,
                               None if kind == "value" else entry.value)},
                       f"entry {entry.index}")
            counts[0] += 1
    return p1[-1].index + 1


def probe_end(entries, index):
    probe = entries[index].probe
    while index < len(entries) and entries[index].probe == probe:
        index += 1
    return index


def walk(listing, taker):
    """The run that the image's program makes for LISTING (the design's
    section 3.2), each line taken from TAKER; raises Done at its end."""
    kind, values = taker.take({"entry": (listing.image, None, None, None),
                               "fail-entry": (None,)}, "ENTRY")
    if kind == "fail-entry":
        if values[0] <= 2:
            raise Wrong("FAIL entry names a hart of 0 to 2")
        raise Done(kind)
    hart = values[1]
    if hart > 2:
        raise Wrong("ENTRY names a hart above 2")
    taker.take({"sbi": (None,) * 3}, "SBI")
    _, (srst, hsm, satp) = taker.take({"ext": (None,) * 3}, "EXT")
    if srst > 1 or hsm > 1:
        raise Wrong("EXT's srst or hsm is not 0 or 1")
    if not srst or satp or listing.harts == 3 and not hsm:
        taker.take({"fail-sbi": (srst, hsm, satp)}, "FAIL sbi")
        raise Done("fail-sbi")
    taker.trap_hart = hart
    counts, results, entries, index = [0, 0], {}, listing.entries, 0
    while index < len(entries):
        entry = entries[index]
        if entry.op in ("csrr", "csrw"):
            index = p1_block(listing, taker, hart, counts)
        elif entry.op in ("read", "write"):
            access(taker, entry, counts, results)
            index += 1
        else:
            passed = results.get(entry.ref) == entry.value
            taker.take({"guard": (entry.probe, entry.name, entry.value,
                                  "pass" if passed else "fail")},
                       f"entry {entry.index}")
            if passed:
                index += 1 if entry.op == "guard-end" else 2
            elif entry.op == "guard-end":
                index = probe_end(entries, index)
            else:
                access(taker, entries[index + 1], counts, results)
                index = probe_end(entries, index + 1)
    taker.take({"end": (listing.image, counts[0], counts[1])}, "END")
    raise Done("end")


def cut(data, findings):
    """The capture's lines before the image's, and the image's lines that
    are not blank, each (number, kind, values)."""
    data = data.replace(b"\r", b"")
    raw = data.split(b"\n")
    if raw[-1]:
        findings.append(f"[form] line {len(raw)}: the last line is not whole")
    else:
        raw.pop()
    start = next((i for i, line in enumerate(raw) if PREFIX.encode() in line),
                 len(raw))
    loader = [line.decode("latin-1").strip() for line in raw[:start]]
    lines = []
    for number, line in enumerate(raw[start:], start + 1):
        if not line:
            continue
        kind = values = None
        if not line.startswith(PREFIX.encode()) or \
                line.count(PREFIX.encode()) != 1 or len(line) > LINE_MAX or \
                any(byte < 0x20 or byte > 0x7E for byte in line):
            findings.append(f"[form] line {number}: not a whole line of the "
                            "image's of printable ASCII, at most 120 "
                            "characters")
        else:
            kind, values = parse_body(line.decode("ascii")[len(PREFIX):])
            if kind is None:
                findings.append(f"[form] line {number}: not of the image's "
                                "grammar")
        lines.append((number, kind, values))
    return loader, lines


def end_word(lines):
    if not lines:
        return "none"
    kind = lines[-1][1]
    return "end" if kind == "end" else kind if kind in ENDS else "stopped"


def mode_rules(mode, harts, image, loader, lines, findings):
    entry = next((v for _, k, v in lines if k == "entry"), None)
    if mode == "host":
        if loader:
            findings.append("[host] line 1: a line before the image's")
        return
    if mode == "board":
        board_rules(image, loader, entry, findings)
        return
    banner = [m for m in (QEMU_HART.fullmatch(t) for t in loader) if m]
    if sum(1 for t in loader if QEMU_BANNER.fullmatch(t)) != 1 or \
            sum(1 for t in loader if QEMU_SBI.fullmatch(t)) != 1 or \
            len(banner) != 1 or entry is not None and \
            int(banner[0].group(1)) != entry[1]:
        findings.append("[qemu] OpenSBI v1.6's banner, SBI 2.0, and the boot "
                        "hart are not there once each, or not ENTRY's hart")
    for number, kind, values in lines:
        if kind == "entry" and values[2] != QEMU_BASE:
            findings.append(f"[qemu] line {number}: ENTRY's base is not "
                            "QEMU's")
        if kind == "sbi" and values[:2] != (0x2000000, 1):
            findings.append(f"[qemu] line {number}: SBI is not OpenSBI's 2.0")
        if kind in ("value", "fault") and values[2] == "read":
            address, faulted = values[3], kind == "fault"
            if 0x80000000 <= address < 0x80200000 and \
                    (not faulted or values[5:] != (5, address)):
                findings.append(f"[qemu] line {number}: a read of v1.6's "
                                "memory that did not fault, scause 5")
            if 0x80210000 <= address < 0x90000000 and faulted:
                findings.append(f"[qemu] line {number}: a read of RAM that "
                                "faulted")
        if kind in ("wrote", "fault") and values[0] == 7 and \
                values[2] == "write":
            findings.append(f"[qemu] line {number}: a P7 write under QEMU")
        if kind == "hsm" and values[2] != ("done" if harts == 3 else
                                           "not-started"):
            findings.append(f"[qemu] line {number}: an HSM state other than "
                            "QEMU's harts give")


def board_rules(image, loader, entry, findings):
    """U-Boot's boot of the staged IMAGE as the board prints it (the RC
    records' handoff excerpts, lines 1 to 26), then ENTRY's base and fdt."""
    texts = [STAMP.sub("", line, count=1).strip() for line in loader]
    autoboot = [i for i, text in enumerate(texts) if AUTOBOOT.fullmatch(text)]
    if len(autoboot) != 1:
        findings.append("[board] not one autoboot line: one boot a capture")
    size, digest = len(image), hashlib.md5(image).hexdigest()
    forms = ((f"{size} bytes read in [0-9]+ ms(?: \\(.*\\))?", "the size"),
             (f"md5 for {LOAD:x} \\.\\.\\. {LOAD + size - 1:x} ==> {digest}",
              "the MD5"),
             (f"Moving Image from 0x{LOAD:x} to 0x{BOARD_BASE:x}, "
              f"end={BOARD_BASE + size:x}", "the move"),
             ("## Flattened Device Tree blob at ([0-9a-f]+)", "the blob"),
             ("Booting using the fdt blob at 0x([0-9a-f]+)", "the blob booted"),
             ("Loading Device Tree to ([0-9a-f]{16}), end [0-9a-f]{16} "
              "\\.\\.\\. OK", "the device tree"),
             ("Starting kernel \\.\\.\\.", "Starting kernel"))
    at, found = autoboot[0] if autoboot else len(texts), []
    for form, name in forms:
        hits = [i for i in range(at + 1, len(texts))
                if re.fullmatch(form, texts[i])]
        if len(hits) != 1 or [i for i in range(
                autoboot[0] if autoboot else 0, len(texts))
                if re.fullmatch(form, texts[i])] != hits:
            findings.append(f"[board] {name}: not once, in order, after the "
                            "autoboot line")
            found.append(None)
        else:
            at = hits[0]
            found.append(re.fullmatch(form, texts[at]))
    if found[3] and found[4] and found[3].group(1) != found[4].group(1):
        findings.append("[board] the blob booted is not the blob")
    findings += [f"[board] line {i + 1}: a line between Starting kernel and "
                 "the image's" for i in range(at + 1, len(texts))
                 if found[6] and texts[i] not in NOISE]
    if entry and (entry[2] != BOARD_BASE or found[5] and
                  entry[3] != int(found[5].group(1), 16)):
        findings.append("[board] ENTRY's base is not the board's, or its fdt "
                        "not U-Boot's device tree")


def judge(listing, mode, harts, image, data):
    """FINDINGS, END, and the image's line count for a capture's DATA."""
    findings = []
    loader, lines = cut(data, findings)
    if lines:
        taker = Judge(lines)
        try:
            walk(listing, taker)
        except Done:
            if taker.position < len(lines):
                findings.append(f"[after] line {lines[taker.position][0]}: "
                                "a line after the run's last")
        except Wrong as wrong:
            findings.append(f"[walk] line {taker.last}: {wrong}")
    mode_rules(mode, harts, image, loader, lines, findings)
    return findings, end_word(lines), len(lines)


def generate(listing, sample, cut_after=None):
    try:
        walk(listing, sample)
    except Done:
        pass
    return sample.lines[:cut_after]


def at(lines, kind, nth=0):
    hits = [i for i, line in enumerate(lines) if line.startswith(PREFIX) and
            parse_body(line[len(PREFIX):])[0] == kind]
    return hits[nth] if len(hits) > nth else None


def edit(lines, kind, field, change, nth=0):
    """LINES with the NTH line of KIND's FIELD changed, or None."""
    i = at(lines, kind, nth)
    if i is None:
        return None
    values = parse_body(lines[i][len(PREFIX):])[1]
    values = values[:field] + (change(values[field]),) + values[field + 1:]
    return lines[:i] + [render(kind, values)] + lines[i + 1:]


def swap(lines, find, change):
    """LINES with the first line holding FIND changed, or None."""
    i = next((i for i, line in enumerate(lines) if find in line), None)
    return None if i is None else lines[:i] + change(lines[i]) + \
        lines[i + 1:]


def self_test(listing):
    """The runs and mutations of the docstring; 0 if every one holds."""
    image = bytes(range(256)) * 96
    size, digest = len(image), hashlib.md5(image).hexdigest()
    record = (pathlib.Path(__file__).resolve().parents[3] / RECORD) \
        .read_text().splitlines()
    loader = record[:next(i for i, line in enumerate(record)
                          if line.startswith("BE_"))]
    failed = []
    for pattern, replacement in (
            (r"\] [0-9]+ bytes read", f"] {size} bytes read"),
            (r"\.\.\. [0-9a-f]+ ==> [0-9a-f]{32}",
             f"... {LOAD + size - 1:x} ==> {digest}"),
            (r"to 0x[0-9a-f]+, end=[0-9a-f]+",
             f"to 0x{BOARD_BASE:x}, end={BOARD_BASE + size:x}")):
        hits = [i for i, line in enumerate(loader) if re.search(pattern, line)]
        if len(hits) != 1:
            failed.append(f"the record's loader lines: {pattern}")
            continue
        loader[hits[0]] = re.sub(pattern, replacement, loader[hits[0]])
    banner = ["OpenSBI v1.6", "Runtime SBI Version         : 2.0",
              "Boot HART ID                : 0"]
    guards = [e for e in listing.entries if e.op.startswith("guard")]
    passing = {e.ref: e.value for e in guards}
    reads = [e.index for e in listing.entries if e.op == "read"]
    accesses = [e.index for e in listing.entries if e.op in ("read", "write")]
    qemu_faults = {e.index for e in listing.entries if e.op == "read" and
                   not 0x80210000 <= e.address < 0x90000000}
    runs = [("sample", "end", {}, ("host", "board")),
            ("guards pass", "end", {"values": passing}, ("host", "board")),
            ("the else branch", "end", {"values": {**passing, **{
                e.ref: e.value ^ 1 for e in guards
                if e.op == "guard-else"}}}, ("host", "board")),
            ("faults", "end", {"faults": set(reads)}, ("host", "board")),
            ("QEMU's", "end", {"faults": qemu_faults}, ("qemu",)),
            ("a FAIL trap", "fail-trap", {"trap": accesses[0]},
             ("host", "board", "qemu")),
            ("stopped", "stopped", {"faults": qemu_faults},
             ("host", "board", "qemu"))]
    if listing.harts == 3:
        runs.append(("harts", "end", {"states": {
            1: (0, "timeout"), 2: ((1 << 64) - 3, "not-started")}},
            ("host", "board")))
    harts = 3 if listing.harts == 3 else 1
    wraps = {"host": [], "board": loader, "qemu": banner}
    captures = {}
    for name, end, options, modes in runs:
        for mode in modes:
            body = generate(listing, Sample(
                QEMU_BASE if mode == "qemu" else BOARD_BASE, **options),
                4 if end == "stopped" else None)
            capture = wraps[mode] + body
            captures[mode, name] = capture
            got = judge(listing, mode, harts, image,
                        ("\n".join(capture) + "\n").encode("latin-1"))
            if got[0] or got[1] != end:
                failed.append(f"{name} ({mode}): {got[1]}, {got[0][:1]}")
    write = next((e for e in listing.entries if e.op == "write"), None)
    wrote = render("wrote", (write.probe, write.name, "write", write.address,
                             write.width, write.value)) if write else None
    vm = next((e for e in listing.entries if e.op == "read" and
               0x80000000 <= e.address < 0x80200000), None)
    ram = next((e for e in listing.entries if e.op == "read" and
                0x80210000 <= e.address < 0x90000000), None)
    common = [
        ("121 characters", "form", lambda c: swap(
            c, PREFIX + "SBI", lambda l: [l + "x" * (121 - len(l))])),
        ("a byte not ASCII", "form", lambda c: swap(
            c, PREFIX + "SBI", lambda l: [l[:-1] + "\xe9"])),
        ("text before the prefix", "form", lambda c: swap(
            c, PREFIX + "SBI", lambda l: ["x" + l])),
        ("a line after END", "after", lambda c: c + [c[at(c, "entry")]]),
        ("a line twice", "walk", lambda c: swap(
            c, PREFIX + "SBI", lambda l: [l, l])),
        ("a line missing", "walk", lambda c: swap(
            c, PREFIX + "EXT", lambda l: [])),
        ("two lines swapped", "walk", lambda c: c[:at(c, "sbi")] + [
            c[at(c, "ext")], c[at(c, "sbi")]] + c[at(c, "ext") + 1:]),
        ("a guard that disagrees", "walk", lambda c: edit(
            c, "guard", 3, lambda v: "fail" if v == "pass" else "pass")),
        ("a wrote not the entry's", "walk", lambda c: edit(
            c, "wrote", 5, lambda v: v ^ 1)),
        ("END's counts", "walk", lambda c: edit(c, "end", 1,
                                                lambda v: v + 1)),
        ("ENTRY's image", "walk", lambda c: edit(c, "entry", 0,
                                                 lambda v: v % 3 + 1)),
        ("an HSM done without P1's lines", "walk", lambda c: None if at(
            c, "hsm") is None else c[:at(c, "hsm") + 1] + c[at(c, "hsm") +
                                                           6:]),
        ("a write after a failed guard", "walk", lambda c: None if not wrote
         or at(c, "guard") is None or "fail" not in c[at(c, "guard")] else
         c[:at(c, "guard") + 1] + [wrote] + c[at(c, "guard") + 1:])]
    special = [
        ("board", "the MD5", lambda c: swap(c, "==>", lambda l: [
            l[:-1] + ("0" if l[-1] != "0" else "1")])),
        ("board", "the size", lambda c: swap(c, "bytes read", lambda l: [
            l.replace(f"] {size} ", f"] {size + 1} ")])),
        ("board", "the move's target", lambda c: swap(
            c, "Moving Image", lambda l: [l.replace("to 0x102200000",
                                                    "to 0x108000000")])),
        ("board", "Starting kernel missing", lambda c: swap(
            c, "Starting kernel", lambda l: [])),
        ("board", "a line before ENTRY", lambda c: c[:at(c, "entry")] + [
            "U-Boot 2022.10"] + c[at(c, "entry"):]),
        ("board", "two autoboot lines", lambda c: swap(
            c, "Autoboot", lambda l: [l, l])),
        ("board", "ENTRY's fdt", lambda c: edit(c, "entry", 3,
                                                lambda v: v + 0x1000)),
        ("board", "ENTRY's base", lambda c: edit(c, "entry", 2,
                                                 lambda v: QEMU_BASE)),
        ("board", "the blob booted", lambda c: swap(
            c, "Booting using", lambda l: [l[:-1] + "f"])),
        ("board", "the device tree missing", lambda c: swap(
            c, "Loading Device Tree", lambda l: [])),
        ("host", "a line before the image's", lambda c: ["U-Boot"] + c),
        ("qemu", "SBI not OpenSBI's", lambda c: edit(c, "sbi", 1,
                                                     lambda v: v + 1)),
        ("qemu", "an HSM line not done", lambda c: edit(
            c, "hsm", 2, lambda v: "timeout")),
        ("qemu", "a RAM read that faulted", lambda c: None if ram is None
         else swap(c, f"{ram.name} read a=", lambda l: [render(
             "fault", (ram.probe, ram.name, "read", ram.address, ram.width,
                       5, ram.address))])),
        ("qemu", "no banner", lambda c: swap(c, "OpenSBI v1.6",
                                             lambda l: [])),
        ("qemu", "the boot hart", lambda c: swap(
            c, "Boot HART ID", lambda l: [l[:-1] + "1"])),
        ("qemu", "ENTRY's base", lambda c: edit(c, "entry", 2,
                                                lambda v: BOARD_BASE)),
        ("qemu", "a v1.6 read that did not fault", lambda c: None if vm is
         None else swap(c, f"{vm.name} read a=", lambda l: [render(
             "value", (vm.probe, vm.name, "read", vm.address, vm.width, 0))])),
        ("qemu", "a P7 write", lambda c: None if not wrote or
         write.probe != 7 else c[:at(c, "end")] + [wrote] + c[at(c, "end"):])]
    cases = [(mode, name, tag, change, "guards pass" if mode != "qemu" else
              "QEMU's") for name, tag, change in common
             for mode in ("host", "board", "qemu")]
    cases += [(mode, name, mode, change, "guards pass" if mode != "qemu"
               else "QEMU's") for mode, name, change in special]
    count = 0
    for mode, name, tag, change, base in cases:
        base_capture = captures[mode, base]
        if name == "a write after a failed guard":
            base_capture = captures.get((mode, "sample"), base_capture)
        mutated = change(list(base_capture))
        if mutated is None:
            continue
        count += 1
        got = judge(listing, mode, harts, image,
                    ("\n".join(mutated) + "\n").encode("latin-1"))
        if not any(f.startswith(f"[{tag}]") for f in got[0]):
            failed.append(f"{name} ({mode}): no [{tag}] finding")
    for line in failed:
        print(f"finding: self-test {line}")
    verdict = "FAIL" if failed else "PASS"
    print(f"BE_K3_M13_CAPTURE_SELF_TEST: {verdict} image={listing.image} "
          f"runs={len(captures)} cases={count}")
    return 1 if failed else 0


def load_lists():
    path = pathlib.Path(__file__).resolve().with_name("m13list.py")
    spec = importlib.util.spec_from_file_location("m13list", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv):
    parser = argparse.ArgumentParser(prog="check-capture.py")
    parser.add_argument("--image", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--mode", choices=("qemu", "board", "host"))
    parser.add_argument("--expect", required=True)
    parser.add_argument("--qemu-harts", type=int, choices=(1, 3))
    parser.add_argument("--image-file")
    parser.add_argument("--expect-end", choices=ENDS, default="end")
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("capture", nargs="?")
    args = parser.parse_args(argv)
    lists = load_lists()
    try:
        listing = lists.parse(args.expect)
    except OSError:
        print("BE_K3_M13_CAPTURE: FAIL the list cannot be read")
        return 2
    except lists.ListError as error:
        print(f"BE_K3_M13_CAPTURE: FAIL the list: {error}")
        return 2
    if listing.image != args.image:
        print(f"BE_K3_M13_CAPTURE: FAIL the list is not image {args.image}'s")
        return 2
    if args.sample:
        print("\n".join(generate(listing, Sample())))
        return 0
    if args.self_test:
        return self_test(listing)
    if args.mode is None or args.capture is None or \
            (args.mode == "qemu") != (args.qemu_harts is not None) or \
            (args.mode == "board") != (args.image_file is not None):
        parser.error("--mode and CAPTURE; --qemu-harts in qemu mode and "
                     "--image-file in board mode, alone")
    try:
        data = pathlib.Path(args.capture).read_bytes()
        image = pathlib.Path(args.image_file).read_bytes() \
            if args.image_file else b""
    except OSError:
        print("BE_K3_M13_CAPTURE: FAIL the capture or the image cannot be "
              "read")
        return 2
    findings, end, count = judge(listing, args.mode, args.qemu_harts, image,
                                 data)
    for finding in findings:
        print(f"finding: {finding}")
    verdict = "PASS" if not findings and end == args.expect_end else "FAIL"
    print(f"BE_K3_M13_CAPTURE: {verdict} image={args.image} mode={args.mode} "
          f"end={end} lines={count}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
