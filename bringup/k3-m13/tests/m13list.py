#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""
m13list.py: the parser of the M13-4 expected lists (tests/expect-N.txt;
planning/mvp-m13-3-review-point.md, sections 2 and 3), shared by
tests/check-image.py and tests/check-capture.py, which load it by path.

A list has one statement a line; `#` starts a comment:

    image N                       the first statement: 1 to 3
    harts H                       1, or 3 (image 1: P1 on harts 0 to 2)
    probes PROBE...               the probes, in their order: P1 to P7
    PROBE read NAME ADDRESS WIDTH
    PROBE write NAME ADDRESS WIDTH VALUE
    PROBE csrr NAME 0x607 8
    PROBE csrw NAME 0x607 8 VALUE
    PROBE guard-end NAME VALUE    the latest earlier read of NAME, in this
                                  probe, read VALUE; else the probe ends
    PROBE guard-else NAME VALUE   the same; unless it did, the next entry,
                                  a write of the probe, is made, and the
                                  probe ends
    repeat COUNT STRIDE [LABEL...]
    ...                           the lines up to `end`, COUNT times: the
    end                           k-th time each ADDRESS plus k times
                                  STRIDE, `{i}` in a NAME k in decimal,
                                  `{l}` the k-th LABEL

It refuses an unknown statement; a probe outside P1 to P7, undeclared, or
out of the declared order; a width other than 4 or 8; a read's or write's
address not aligned to its width; a write of another width than 4 (the
image's access routine makes no other); a csrr or csrw outside P1, of
another CSR than 0x607 or another width than 8, or named other than
hartH.hgeie, H its hart; a P1 that is not, for each of harts 0, 1, and 2
in order, csrr, csrw all ones, csrr, csrw 0, csrr (what the image's
be_m13_p1 makes), a P1 that is not first, or P1 without harts 3; a name outside
[A-Za-z0-9_.()[\\]]{1,23}; a guard with no earlier read of its name in its
probe; a guard-else not followed by a write of its probe; a guard or a
nested block in a repeat; a repeat whose labels are not COUNT; more than
128 entries.

Trust: test-only and read-only: it reads the one list that it is given.
"""

import re

ENTRIES_MAX = 128
NAME_MAX = 23
CSR_HGEIE = 0x607
ALL_ONES = (1 << 64) - 1
OPS = {"read": 1, "write": 2, "csrr": 3, "csrw": 4, "guard-end": 5,
       "guard-else": 6}
NAME = re.compile(r"[A-Za-z0-9_.()\[\]]{1,%d}" % NAME_MAX)
HEX = re.compile(r"0x[0-9a-f]{1,16}")
DECIMAL = re.compile(r"[0-9]{1,4}")
PROBE = re.compile(r"P[1-7]")
P1_PATTERN = (("csrr", None), ("csrw", ALL_ONES), ("csrr", None),
              ("csrw", 0), ("csrr", None))


class ListError(Exception):
    """A list that the parser refuses, with its line's number."""


class Entry:
    """One entry of an expanded list, as the image's table holds it."""

    __slots__ = ("index", "probe", "op", "name", "address", "width",
                 "value", "hart", "ref", "line")

    def __init__(self, line, probe, op, name, address=0, width=0, value=0):
        self.index = 0
        self.probe = probe
        self.op = op
        self.name = name
        self.address = address
        self.width = width
        self.value = value
        self.hart = 0
        self.ref = 0
        self.line = line


class Listing:
    """A parsed list: image, harts, probes (numbers, in order), entries."""

    def __init__(self):
        self.image = None
        self.harts = None
        self.probes = None
        self.entries = []


def number(text, line, what, form=HEX):
    if form.fullmatch(text) is None:
        raise ListError(f"line {line}: {what} is not a number of its form")
    return int(text, 0)


def stride_number(text, line):
    if DECIMAL.fullmatch(text) is None and HEX.fullmatch(text) is None:
        raise ListError(f"line {line}: a stride is not a number")
    return int(text, 0)


def access(words, line, offset, labels, stride):
    """An entry from WORDS, OFFSET the k of a repeat (None outside one)."""
    probe, op = words[0], words[1]
    if PROBE.fullmatch(probe) is None:
        raise ListError(f"line {line}: no probe P1 to P7")
    if op not in OPS:
        raise ListError(f"line {line}: an unknown statement")
    name = words[2] if len(words) > 2 else ""
    if offset is not None:
        if op.startswith("guard"):
            raise ListError(f"line {line}: a guard inside a repeat")
        if "{l}" in name and not labels:
            raise ListError(f"line {line}: {{l}} with no labels")
        name = name.replace("{i}", str(offset))
        if labels:
            name = name.replace("{l}", labels[offset])
    if NAME.fullmatch(name) is None:
        raise ListError(f"line {line}: a name outside the name form")
    if op.startswith("guard"):
        if len(words) != 4:
            raise ListError(f"line {line}: a guard is PROBE OP NAME VALUE")
        return Entry(line, int(probe[1]), op, name,
                     value=number(words[3], line, "a value"))
    wants = 6 if op in ("write", "csrw") else 5
    if len(words) != wants:
        raise ListError(f"line {line}: {op} takes {wants - 2} operands")
    address = number(words[3], line, "an address")
    if offset is not None:
        address += offset * stride
    width = number(words[4], line, "a width", DECIMAL)
    value = number(words[5], line, "a value") if wants == 6 else 0
    if width not in (4, 8):
        raise ListError(f"line {line}: a width other than 4 or 8")
    if address > ALL_ONES or value > ALL_ONES:
        raise ListError(f"line {line}: a number above 64 bits")
    entry = Entry(line, int(probe[1]), op, name, address, width, value)
    if op in ("csrr", "csrw"):
        match = re.fullmatch(r"hart([0-2])\.hgeie", name)
        if entry.probe != 1 or address != CSR_HGEIE or width != 8 or \
                match is None:
            raise ListError(f"line {line}: a CSR access other than P1's "
                            "hartH.hgeie, 0x607, width 8")
        entry.hart = int(match.group(1))
    else:
        if address % width:
            raise ListError(f"line {line}: an address not aligned to its "
                            "width")
        if op == "write" and width != 4:
            raise ListError(f"line {line}: a write of another width than 4")
    return entry


def parse_text(text):
    listing = Listing()
    block = None
    for line, raw in enumerate(text.splitlines(), 1):
        words = raw.split("#", 1)[0].split()
        if not words:
            continue
        if listing.image is None:
            if words[0] != "image" or len(words) != 2 or \
                    words[1] not in ("1", "2", "3"):
                raise ListError(f"line {line}: the first statement is not "
                                "image 1 to 3")
            listing.image = int(words[1])
        elif words[0] == "harts":
            if listing.harts is not None or listing.entries or \
                    len(words) != 2 or words[1] not in ("1", "3"):
                raise ListError(f"line {line}: harts is once, 1 or 3, before "
                                "the entries")
            listing.harts = int(words[1])
        elif words[0] == "probes":
            if listing.probes is not None or listing.entries or \
                    len(words) < 2 or \
                    any(PROBE.fullmatch(w) is None for w in words[1:]) or \
                    len(set(words[1:])) != len(words) - 1:
                raise ListError(f"line {line}: probes is once, distinct "
                                "P1 to P7, before the entries")
            listing.probes = [int(w[1]) for w in words[1:]]
        elif words[0] == "repeat":
            if block is not None:
                raise ListError(f"line {line}: a repeat inside a repeat")
            if len(words) < 3:
                raise ListError(f"line {line}: repeat COUNT STRIDE [LABEL...]")
            count = number(words[1], line, "a count", DECIMAL)
            labels = words[3:]
            if not 1 <= count <= ENTRIES_MAX or labels and \
                    len(labels) != count:
                raise ListError(f"line {line}: a repeat's count or labels")
            block = (count, stride_number(words[2], line), labels, [])
        elif words[0] == "end":
            if block is None or len(words) != 1:
                raise ListError(f"line {line}: an end with no repeat")
            count, stride, labels, body = block
            for offset in range(count):
                for body_line, body_words in body:
                    add(listing, access(body_words, body_line, offset,
                                        labels, stride))
            block = None
        elif block is not None:
            block[3].append((line, words))
        else:
            add(listing, access(words, line, None, None, 0))
    if block is not None:
        raise ListError("a repeat with no end")
    finish(listing)
    return listing


def add(listing, entry):
    if listing.harts is None or listing.probes is None:
        raise ListError(f"line {entry.line}: an entry before harts and "
                        "probes")
    if entry.probe not in listing.probes:
        raise ListError(f"line {entry.line}: an undeclared probe")
    seen = [e.probe for e in listing.entries]
    if seen and entry.probe != seen[-1] and (
            entry.probe in seen or listing.probes.index(entry.probe) <
            listing.probes.index(seen[-1])):
        raise ListError(f"line {entry.line}: a probe out of its order")
    if listing.entries and listing.entries[-1].op == "guard-else" and (
            entry.op != "write" or entry.probe != listing.entries[-1].probe):
        raise ListError(f"line {entry.line}: a guard-else not followed by a "
                        "write of its probe")
    entry.index = len(listing.entries)
    if entry.op.startswith("guard"):
        reads = [e for e in listing.entries if e.op == "read" and
                 e.probe == entry.probe and e.name == entry.name]
        if not reads:
            raise ListError(f"line {entry.line}: a guard with no earlier read "
                            "of its name")
        entry.ref = reads[-1].index
    listing.entries.append(entry)
    if len(listing.entries) > ENTRIES_MAX:
        raise ListError(f"line {entry.line}: more than {ENTRIES_MAX} entries")


def finish(listing):
    if listing.image is None or listing.harts is None or \
            listing.probes is None or not listing.entries:
        raise ListError("a list with no image, harts, probes, or entries")
    if listing.entries[-1].op == "guard-else":
        raise ListError("a guard-else not followed by a write of its probe")
    if [p for p in listing.probes if
            p not in {e.probe for e in listing.entries}]:
        raise ListError("a declared probe with no entry")
    p1 = [e for e in listing.entries if e.probe == 1]
    if (listing.harts == 3) != bool(p1):
        raise ListError("P1 without harts 3, or harts 3 without P1")
    if p1 and (p1[0].index != 0 or [
            (e.hart, e.op, e.value if e.op == "csrw" else None)
            for e in p1] != [(hart, op, value) for hart in range(3)
                             for op, value in P1_PATTERN]):
        raise ListError("P1 is not first, or not csrr, csrw all ones, csrr, "
                        "csrw 0, csrr on each of harts 0, 1, and 2 in order")
    if [e for e in listing.entries if e.probe != 1 and
            e.op in ("csrr", "csrw")]:
        raise ListError("a CSR access outside P1")


def parse(path):
    with open(path, "rb") as stream:
        data = stream.read()
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as error:
        raise ListError("a list that is not ASCII") from error
    return parse_text(text)
