#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""
litmus.py --run [--out DIR]
litmus.py --check-sequences [--scratch DIR]
litmus.py --write --target COMMIT [--scratch DIR]
litmus.py --self-test

Purpose: the ordering premises L1 to L5 of MVP M8's stage 1 as litmus
tests on the compiled code (planning/mvp-m8-plan.md, D-3, D-9, work package
M8-4, Q3; specification SHA-256
ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d, section
1): mvp/verify/litmus/L1.litmus to L5.litmus, each the two harts'
instruction sequences as the monitor's two toolchains compiled them,
reduced to the accesses, fences, and branches of its pattern, with the
outcome the protocol forbids in its exists clause. The sequences they
mirror are recorded in mvp/verify/litmus/sequences.txt and the lines each
test mirrors in sequences/<symbol>-<toolchain>.s.
--run (in the verifier image): herd7 -model riscv.cat on each test, killed
after 60 s, its Observation line read as qualify.py reads it; writes
DIR/litmus.txt (default build/mvp/verify): a line per test, `premise=L1
file=... expected=Never observed=Never ok=yes states=N`, and last
`BE_MVP_LITMUS: PASS premises=N never=N sometimes=N not_run=N`; and
DIR/litmus/TEST/ with each run's command and output. PASS means every test
ran and is recorded, or herd7 is absent (not_run, with the reason);
sometimes counts Sometimes and Always. An observed outcome is the plan's
stop 2 (a defect found by a litmus test): its line has ok=no and the exit
status is 1. A run without a verdict (no Observation line, another test's,
no execution, a timeout) is FAIL.
--check-sequences (on the host, in ./mvp/mvp verify as its first suite;
the image has no RISC-V binutils): re-derives sequences.txt from
build/mvp/{gcc,clang}/be-mvp.elf with the MVP tool lock's
riscv64-linux-gnu-objdump and objcopy, each checked against the lock's
SHA-256, and compares it with the record: each ELF's SHA-256 without its
debug sections, each symbol's binding, section, address, size, and bytes,
each excerpt line with the disassembly at its address. A changed compile
fails it, naming the first symbol that differs as SYMBOL@TOOLCHAIN, until
the re-proof rule (D-2) re-derives the record and the tests.
The ELF file's own SHA-256 is reported, not compared: its DWARF names the
tree's absolute path, so a checkout at another path links other bytes for
the same code.
--write: the record re-derived and written, refused unless the monitors'
tracked inputs in the tree (INPUTS: the MVP's sources and Makefile, the
scenarios and their generators, the tool lock, the guest build, the port's
script and B2's pinned port) equal COMMIT's (git); only on the responsible
human's direction, under the re-proof rule.
--self-test (on the host, with no herd7 and no ELF): the five tests'
structure (the first line, the licence lines, the plan's words for the
premise, the specification's hash, each cited digest in sequences.txt, the
exists or forall clause), the record and its excerpts, herd7's outputs
(Never, Sometimes, Always, none), the derivation against a fake objdump,
and planted defects refused.
Trust: objdump and objcopy run by the lock's absolute paths with PATH,
LC_ALL, and LANG alone, their outputs in a scratch directory under build/
that only this tool writes.
Exit status: 0 PASS; 1 FAIL or an observed outcome; 2 usage.
"""

import argparse
import datetime
import hashlib
import importlib.util
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[3]
VERIFY = REPO / "mvp" / "verify"
LITMUS = VERIFY / "litmus"
SEQUENCES = LITMUS / "sequences.txt"
EXCERPTS = LITMUS / "sequences"
PLAN = REPO / "planning" / "mvp-m8-plan.md"
LOCK = REPO / "mvp" / "tools" / "lock" / "tool-lock.conf"
SCRATCH = REPO / "build" / "mvp" / "tmp" / "litmus-sequences"
TAG = "BE_MVP_LITMUS"
SPECIFICATION_SHA256 = ("ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f"
                        "4c542ecc9dc53d")
TOOLCHAINS = ("gcc", "clang")
ELFS = {toolchain: f"build/mvp/{toolchain}/be-mvp.elf"
        for toolchain in TOOLCHAINS}
ROLES = ("cross_objdump", "cross_objcopy")
# The two-guests monitors' tracked inputs, which --write's target must
# hold as the tree does.
INPUTS = ("mvp/src", "mvp/Makefile", "mvp/scenarios",
          "mvp/tools/gen-scenario.py", "mvp/tools/gen-dts.py",
          "mvp/tools/policy-check.py", "mvp/tools/port.py", "mvp/tools/lock",
          "mvp/guest", "bringup/k3-b2")
PREMISES = ("L1", "L2", "L3", "L4", "L5")
LICENCE = ("SPDX-License-Identifier: GPL-3.0-only",
           "Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>")
SCRATCH_MARKER = ".litmus-scratch"
RUN_MARKER = ".litmus-run"
ENVIRONMENT = {"PATH": "/usr/bin", "LC_ALL": "C", "LANG": "C"}
HEADER = f"""\
# {LICENCE[0]}
# {LICENCE[1]}
#
# The compiled sequences the ordering premises' litmus tests mirror
# (planning/mvp-m8-plan.md, D-3, D-9, work package M8-4; specification
# SHA-256 {SPECIFICATION_SHA256}),
# written by mvp/verify/tools/litmus.py --write and checked by litmus.py
# --check-sequences in ./mvp/mvp verify: the MVP tool lock's objdump and
# objcopy; each toolchain's monitor ELF, the two-guests scenario's (its
# make rule, build/mvp/TOOLCHAIN/be-mvp.elf), with its SHA-256 as built
# here (reported, not compared: its DWARF names the tree's absolute path)
# and without its debug sections (objcopy --strip-debug; compared); and
# each symbol the tests cite, with its binding, section, address, size,
# the SHA-256 of its bytes, and its excerpt of the lines the tests mirror,
# each compared with the disassembly. A changed compile fails the check,
# naming the first symbol that differs, until the re-proof rule (D-2)
# re-derives this record and the tests. Re-written only on the responsible
# human's direction.
""" + (
    "# Bound: this record covers the two-guests monitors only; te-poc's and "
    "anchor's own call sites (deny's DENIAL publish in both; anchor's "
    "wait_serve, mgmt_call's MGMT_REQUEST publish, and post_inbound's "
    "MGMT_RESULT, PAUSE, and TERMINATE posts), scanned read-only in their "
    "ELFs when it was written, have the same fence shapes and are not "
    "recorded.\n")
# One instruction line of objdump -d: address, encoding, instruction.
INSN = re.compile(r"^\s*([0-9a-f]+):\t([0-9a-f]+)\s*\t(.+)$")
SECTION = re.compile(r"^\s*\d+ (\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+"
                     r"[0-9a-f]+\s+[0-9a-f]+\s+2\*\*\d+$")
SYMBOL = re.compile(r"^([0-9a-f]{16}) (.{7}) (\S+)\t([0-9a-f]{16}) (\S+)$")
NAME = r"[A-Za-z_][A-Za-z0-9_.]*"
TEST = re.compile(r"^L([1-5])(?:-(gcc|clang))?$")
CITATION = re.compile(rf"\b({NAME})@(gcc|clang) sha256=([0-9a-f]{{64}})\b")
CONDITION = re.compile(r"^(?:~?exists|forall) \(.+\)$")


class Refusal(Exception):
    """A record, an excerpt, a test, a tool, or a directory refused."""


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


QUALIFY = load("qualify", VERIFY / "tools" / "qualify.py")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normal(address, encoding, instruction):
    """One objdump -d line, its whitespace collapsed."""
    return f"{address:x}: {encoding} {' '.join(instruction.split())}"


# ------------------------------------------------------------- binutils
def lock_tools(text):
    """{role: (command, sha256)} of the lock's objdump and objcopy, each
    file the one the lock pins."""
    values = dict(line.split("=", 1) for line in text.split("\n")
                  if line.startswith("MVP_TOOL_") and "=" in line)
    tools = {}
    for role in ROLES:
        command = values.get(f"MVP_TOOL_{role}_command", "")
        digest = values.get(f"MVP_TOOL_{role}_sha256", "")
        path = pathlib.Path(command)
        if not path.is_absolute() or not re.fullmatch(r"[0-9a-f]{64}",
                                                      digest):
            raise Refusal(f"the tool lock names no {role} by absolute path "
                          "and SHA-256")
        if not path.is_file() or sha256(path.read_bytes()) != digest:
            raise Refusal(f"{command} is not the lock's {role} (absent, or "
                          "another SHA-256)")
        tools[role] = (command, digest)
    return tools


def parse_sections(text):
    """{name: (address, size)} of objdump -h's section table."""
    return {match[1]: (int(match[3], 16), int(match[2], 16))
            for match in map(SECTION.match, text.split("\n")) if match}


def parse_symbols(text):
    """[(name, address, size, binding, section)] of objdump -t's function
    symbols, a local's binding naming the file symbol before it."""
    symbols, source = [], "-"
    for match in map(SYMBOL.match, text.split("\n")):
        if not match:
            continue
        flags = match[2]
        if flags[6] == "f":
            source = match[5]
        elif flags[6] == "F":
            symbols.append((match[5], int(match[1], 16), int(match[4], 16),
                            f"local:{source}" if flags[0] == "l" else
                            "global", match[3]))
    return symbols


def parse_disassembly(text):
    """{address: line} of objdump -d's instruction lines, normalised."""
    lines = {}
    for match in map(INSN.match, text.split("\n")):
        if match:
            address = int(match[1], 16)
            lines[address] = normal(address, match[2], match[3])
    return lines


class Binutils:
    """The lock's objdump and objcopy; objcopy's outputs in SCRATCH."""

    def __init__(self, scratch):
        self.tools = lock_tools(LOCK.read_text(encoding="utf-8"))
        self.scratch = scratch

    def run(self, role, *arguments):
        command = [self.tools[role][0], *map(str, arguments)]
        done = subprocess.run(command, capture_output=True, env=ENVIRONMENT,
                              check=False)
        if done.returncode != 0:
            raise Refusal(f"{' '.join(command)}: "
                          f"{done.stderr.decode('utf-8', 'replace')[-300:]}")
        return done.stdout.decode("utf-8", "replace")

    def output(self, name, *arguments):
        path = self.scratch / name
        if path.exists() or path.is_symlink():
            raise Refusal(f"{path} exists")
        self.run("cross_objcopy", *arguments, path)
        data = path.read_bytes()
        path.unlink()
        return data

    def file_digest(self, elf):
        if not elf.is_file():
            raise Refusal(f"{elf.relative_to(REPO)} is not built (make -C "
                          "mvp image)")
        return sha256(elf.read_bytes())

    def nodebug_digest(self, elf):
        return sha256(self.output("nodebug.elf", "--strip-debug", elf))

    def sections(self, elf):
        return parse_sections(self.run("cross_objdump", "-h", elf))

    def symbols(self, elf):
        return parse_symbols(self.run("cross_objdump", "-t", elf))

    def disassembly(self, elf):
        return parse_disassembly(self.run("cross_objdump", "-d", elf))

    def contents(self, elf, section):
        return self.output("section.bin", "-O", "binary",
                           f"--only-section={section}", elf)


def scratch_directory(path):
    """PATH emptied and owned by this tool, under build/, mode 0700."""
    if path.is_symlink():
        raise Refusal(f"{path} is a symbolic link")
    path = path.resolve()
    if not path.is_relative_to(REPO / "build"):
        raise Refusal(f"{path} is not under build/")
    if path.exists() and (not path.is_dir() or (
            any(path.iterdir()) and not (path / SCRATCH_MARKER).is_file())):
        raise Refusal(f"{path} is not empty and not this tool's")
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, mode=0o700)
    (path / SCRATCH_MARKER).touch(exist_ok=False)
    return path


# -------------------------------------------------------------- excerpts
def load_excerpt(path, text):
    """(symbol, toolchain, [(address, line)]) of one excerpt file."""
    match = re.fullmatch(rf"({NAME})-(gcc|clang)\.s", path.name)
    if not match:
        raise Refusal(f"{path.name} is not SYMBOL-gcc.s or SYMBOL-clang.s")
    lines = text.split("\n")
    if lines[:2] != [f"# {LICENCE[0]}", f"# {LICENCE[1]}"] or \
            not any(line.startswith("#") and SPECIFICATION_SHA256 in line
                    for line in lines):
        raise Refusal(f"{path.name} lacks the licence lines or the "
                      "specification's SHA-256")
    rows = []
    for number, line in enumerate(lines, 1):
        if not line or line.startswith("#"):
            continue
        insn = INSN.match(line)
        if not insn:
            raise Refusal(f"{path.name}:{number} is neither a comment nor "
                          "an objdump -d line")
        address = int(insn[1], 16)
        if any(address == seen for seen, _ in rows):
            raise Refusal(f"{path.name}:{number} repeats {address:x}")
        rows.append((address, normal(address, insn[2], insn[3])))
    if not rows:
        raise Refusal(f"{path.name} holds no instruction line")
    return match[1], match[2], rows


def load_excerpts(directory=EXCERPTS):
    return [(path,) + load_excerpt(path, path.read_text(encoding="utf-8"))
            for path in sorted(directory.glob("*.s"))]


# ---------------------------------------------------------------- record
def derive(binutils, tools, excerpts, elfs=ELFS, root=REPO):
    """The record's lines: the tools; per toolchain its ELF and the symbols
    its excerpts name, each excerpt line found in the disassembly inside
    its symbol; the counts."""
    lines = [f"tool role={role} command={command} sha256={digest}"
             for role, (command, digest) in tools.items()]
    total = 0
    for toolchain, relative in elfs.items():
        elf = root / relative
        lines.append(f"elf toolchain={toolchain} file={relative} "
                     f"file_sha256={binutils.file_digest(elf)} "
                     f"nodebug_sha256={binutils.nodebug_digest(elf)}")
        sections, symbols = binutils.sections(elf), binutils.symbols(elf)
        code, contents, rows = binutils.disassembly(elf), {}, []
        for path, name, chain, excerpt in excerpts:
            if chain != toolchain:
                continue
            first, symbol = excerpt[0][0], f"{name}@{toolchain}"
            found = [entry for entry in symbols if entry[0] == name and
                     entry[1] <= first < entry[1] + entry[2]]
            if len(found) != 1:
                raise Refusal(f"{symbol}: {len(found)} symbols {name} hold "
                              f"{first:x} in {relative} ({path.name})")
            _, address, size, binding, section = found[0]
            for at, line in excerpt:
                if not address <= at < address + size:
                    raise Refusal(f"{symbol}: {at:x} lies outside {name} "
                                  f"({path.name})")
                if code.get(at) != line:
                    raise Refusal(f"{symbol}: {relative} holds "
                                  f"{code.get(at)!r} at {at:x}, not {line!r} "
                                  f"({path.name})")
            if section not in sections:
                raise Refusal(f"{symbol}: {relative} has no section "
                              f"{section}")
            if section not in contents:
                contents[section] = binutils.contents(elf, section)
            start = address - sections[section][0]
            data = contents[section][start:start + size]
            if start < 0 or len(data) != size:
                raise Refusal(f"{symbol}: lies outside {section} in "
                              f"{relative}")
            rows.append((name, address, f"symbol toolchain={toolchain} "
                         f"name={name} bind={binding} section={section} "
                         f"address=0x{address:x} size=0x{size:x} "
                         f"sha256={sha256(data)} excerpt="
                         f"{path.relative_to(root)} lines={len(excerpt)}"))
            total += len(excerpt)
        lines += [row for _, _, row in sorted(rows)]
    lines.append(f"symbols={len(excerpts)} lines={total}")
    return lines


def record_lines(text):
    return [line for line in text.split("\n")
            if line and not line.startswith("#")]


def line_fields(line):
    return dict(word.split("=", 1) for word in line.split()[1:]
                if "=" in word)


def recorded_symbols(text):
    """{(toolchain, name): sha256} of the record's symbol lines, each
    (toolchain, name) once."""
    symbols = {}
    for line in record_lines(text):
        if not line.startswith("symbol "):
            continue
        fields = line_fields(line)
        key = (fields.get("toolchain"), fields.get("name"))
        if key in symbols or not re.fullmatch(r"[0-9a-f]{64}",
                                              fields.get("sha256", "")):
            raise Refusal(f"sequences.txt: {line!r} repeats a symbol or "
                          "has no SHA-256")
        symbols[key] = fields["sha256"]
    if not symbols:
        raise Refusal("sequences.txt records no symbol")
    return symbols


def without_file_digest(line):
    return re.sub(r" file_sha256=\S+", "", line)


SYMBOL_FIELDS = ("bind", "section", "address", "size", "sha256", "excerpt",
                 "lines")


def differences(then, now):
    """The record's differences from the derived lines: the first symbol
    that differs, in the record's order, named SYMBOL@TOOLCHAIN with its
    changed fields, then a count of the rest; the ELF files' own digests
    apart (path-dependent). None when they agree."""
    def split(lines):
        symbols, others = {}, []
        for line in lines:
            if line.startswith("symbol "):
                fields = line_fields(line)
                symbols[f"{fields.get('name')}@"
                        f"{fields.get('toolchain')}"] = fields
            else:
                others.append(without_file_digest(line))
        return symbols, others

    old, old_others = split(then)
    new, new_others = split(now)
    found = []
    for name in list(old) + [name for name in new if name not in old]:
        if name not in new:
            found.append(f"{name} differs from sequences.txt: recorded, "
                         "and no excerpt in the tree names it")
        elif name not in old:
            found.append(f"{name} differs from sequences.txt: an excerpt "
                         "names it, and it is not recorded")
        elif old[name] != new[name]:
            found.append(f"{name} differs from sequences.txt: " + "; ".join(
                f"{key} {old[name].get(key)} now {new[name].get(key)}"
                for key in SYMBOL_FIELDS
                if old[name].get(key) != new[name].get(key)))
    others = [f"recorded {recorded!r}, now {current!r}"
              for recorded, current in zip(old_others, new_others)
              if recorded != current]
    if len(old_others) != len(new_others):
        others.append(f"{len(old_others)} other lines recorded, "
                      f"{len(new_others)} now")
    if not found and not others:
        return None
    if not found:
        return f"no recorded symbol differs, but {others[0]}" + (
            f" (and {len(others) - 1} more lines)" if len(others) > 1 else "")
    rest = len(found) - 1 + len(others)
    return found[0] + (f" (and {rest} more lines: re-derive under the "
                       "re-proof rule)" if rest else "")


def check(record, binutils, excerpts):
    """0 when the tree's ELFs derive RECORD's lines, the ELF files' own
    digests apart; else 1, naming the first symbol that differs."""
    now = derive(binutils, binutils.tools, excerpts)
    then = record_lines(record.read_text(encoding="utf-8"))
    found = differences(then, now)
    if found:
        print(f"{TAG}_SEQUENCES: FAIL {found}")
        return 1
    elf_files = "equal" if [line for line in then if line.startswith(
        "elf ")] == [line for line in now if line.startswith("elf ")] else \
        "differ(path-dependent)"
    print(f"{TAG}_SEQUENCES: PASS elfs={len(ELFS)} {now[-1]} "
          f"elf_files={elf_files} record={record.relative_to(REPO)}")
    return 0


def write(target, binutils, excerpts):
    status = subprocess.run(["git", "-C", str(REPO), "diff", "--quiet",
                             target, "--", *INPUTS], check=False)
    if status.returncode != 0:
        raise Refusal(f"the tree's inputs to the monitors ({' '.join(INPUTS)})"
                      f" differ from {target}'s, or {target} is not a commit")
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--verify",
                             f"{target}^{{commit}}"], capture_output=True,
                            text=True, check=True).stdout.strip()
    lines = derive(binutils, binutils.tools, excerpts)
    new = SEQUENCES.with_suffix(".new")
    with open(new, "x", encoding="utf-8") as stream:
        stream.write(HEADER + f"# Target commit: {commit} (its "
                     f"{', '.join(INPUTS)} equal this tree's)\n" +
                     "\n".join(lines) + "\n")
    new.replace(SEQUENCES)
    print(f"{TAG}_SEQUENCES: RECORDED {lines[-1]} "
          f"record={SEQUENCES.relative_to(REPO)}")
    return 0


# ----------------------------------------------------------------- tests
def premise_rows(text):
    """{premise: the plan's words for it} of D-3's premise table."""
    section = text.split("\n### D-3 ", 1)[-1].split("\n### ", 1)[0]
    rows = dict(re.findall(r"^\| (L[1-5]) \| (.+?) \| .+? \|$", section,
                           re.M))
    if sorted(rows) != list(PREMISES):
        raise Refusal("planning/mvp-m8-plan.md's D-3 table does not name "
                      "L1 to L5")
    return rows


def parse_test(text, name, symbols, premises):
    """(premise, citations) of the test NAME, once TEXT has the shape the
    tests share; else a Refusal."""
    match = TEST.fullmatch(name)
    if not match:
        raise Refusal(f"{name}.litmus is not L<1-5>[-gcc|-clang].litmus")
    premise, only = f"L{match[1]}", match[2]
    lines = text.split("\n")
    if lines[0] != f"RISCV {name}":
        raise Refusal(f"{name}.litmus's first line is not `RISCV {name}`")
    if lines[1:3] != [f"(* {line} *)" for line in LICENCE]:
        raise Refusal(f"{name}.litmus's lines 2 and 3 are not its licence")
    end = next((index for index in range(3, len(lines)) if
                lines[index].rstrip().endswith("*)")), None)
    if not lines[3].startswith("(*") or end is None:
        raise Refusal(f"{name}.litmus has no comment block after its "
                      "licence")
    comment = " ".join(" ".join(lines[3:end + 1]).split())
    if "{" in comment or "}" in comment:
        raise Refusal(f"{name}.litmus's comment holds a brace, which herd7's "
                      "splitter reads as the initial state")
    if f"Premise {premise}: " not in comment or " ".join(
            premises[premise].split()) not in comment:
        raise Refusal(f"{name}.litmus does not quote the plan's D-3 words "
                      f"for {premise}")
    if SPECIFICATION_SHA256 not in comment:
        raise Refusal(f"{name}.litmus does not cite the specification's "
                      "SHA-256")
    citations = CITATION.findall(comment)
    for symbol, toolchain, digest in citations:
        if symbols.get((toolchain, symbol)) != digest:
            raise Refusal(f"{name}.litmus cites {symbol}@{toolchain} "
                          f"sha256={digest}, which sequences.txt does not "
                          "record")
    wanted = {only} if only else set(TOOLCHAINS)
    if {toolchain for _, toolchain, _ in citations} != wanted:
        raise Refusal(f"{name}.litmus cites no digest of, or one beyond, "
                      f"{', '.join(sorted(wanted))}")
    body = [line.strip() for line in lines[end + 1:] if line.strip()]
    if "{" not in body or "}" not in body or body.index("{") != 0:
        raise Refusal(f"{name}.litmus has no initial state after its "
                      "comment")
    threads = body[body.index("}") + 1].rstrip(";").split("|")
    if [thread.strip() for thread in threads] != ["P0", "P1"]:
        raise Refusal(f"{name}.litmus's program is not two harts, P0 and P1")
    if not CONDITION.match(body[-1]):
        raise Refusal(f"{name}.litmus does not end in an exists or forall "
                      "clause")
    return premise, citations


def discover(directory=LITMUS):
    """[(name, path)] of the tests: one per premise, or one per toolchain."""
    tests, kinds = [], {}
    for path in sorted(directory.glob("*.litmus")):
        match = TEST.fullmatch(path.stem)
        if not match:
            raise Refusal(f"{path.name} is not L<1-5>[-gcc|-clang].litmus")
        tests.append((path.stem, path))
        kinds.setdefault(f"L{match[1]}", set()).add(match[2] or "both")
    for premise in PREMISES:
        if kinds.get(premise) not in ({"both"}, set(TOOLCHAINS)):
            raise Refusal(f"{premise} needs one test, or one per toolchain")
    return tests


def load_tests(directory=LITMUS, record=SEQUENCES, plan=PLAN):
    """[(name, path, premise, citations)], every recorded symbol cited."""
    symbols = recorded_symbols(record.read_text(encoding="utf-8"))
    premises = premise_rows(plan.read_text(encoding="utf-8"))
    tests = [(name, path) + parse_test(path.read_text(encoding="utf-8"),
                                       name, symbols, premises)
             for name, path in discover(directory)]
    cited = {(toolchain, symbol) for *_, citations in tests
             for symbol, toolchain, _ in citations}
    if set(symbols) - cited:
        raise Refusal("no test cites " + ", ".join(
            f"{symbol}@{toolchain}" for toolchain, symbol in
            sorted(set(symbols) - cited)))
    return tests


# ------------------------------------------------------------------- run
def verdict(output, name):
    """(observed, states, positive, negative) of herd7's OUTPUT for the
    test NAME: the Observation line read by qualify.py's parse_herd, Never,
    Sometimes, or Always; or error (no such line, another test's, no
    execution, no States line)."""
    observed, detail, _ = QUALIFY.parse_herd(output, "known-pass")
    names = re.findall(r"^Observation (\S+) ", output, re.M)
    states = re.search(r"^States (\d+)$", output, re.M)
    if observed == "error" or names != [name] or not states:
        return "error", 0, 0, 0
    word, positive, negative = re.fullmatch(
        r"observation=(\w+) positive=(\d+) negative=(\d+)", detail).groups()
    return word, int(states[1]), int(positive), int(negative)


def prepare(out):
    runs = out / "litmus"
    if runs.is_symlink() or (runs.exists() and not runs.is_dir()):
        raise Refusal(f"{runs} is a symbolic link or not a directory")
    if runs.is_dir() and any(runs.iterdir()) and \
            not (runs / RUN_MARKER).is_file():
        raise Refusal(f"{runs} is not empty and not this tool's")
    shutil.rmtree(runs, ignore_errors=True)
    runs.mkdir(parents=True)
    (runs / RUN_MARKER).touch()
    return runs


def run(out):
    tests = load_tests()
    out.mkdir(parents=True, exist_ok=True)
    runs = prepare(out)
    started = time.monotonic()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    herd = shutil.which("herd7")
    version = QUALIFY.first_line(["herd7", "-version"]) if herd else \
        "not in the image"
    rows, counts = [], {"Never": 0, "sometimes": 0, "not-run": 0, "error": 0}
    for name, path, premise, _ in tests:
        relative = path.relative_to(REPO)
        if herd is None:
            observed, states, positive, negative, seconds = (
                "not-run", 0, 0, 0, 0)
        else:
            directory = runs / name
            directory.mkdir()
            command = ["herd7", "-model", "riscv.cat", str(path)]
            status, output, seconds = QUALIFY.execute(
                command, directory, dict(os.environ, TMPDIR=str(directory)),
                QUALIFY.GOAL_SECONDS)
            (directory / "command.txt").write_text(
                " ".join(command) + f"\nlimit_seconds={QUALIFY.GOAL_SECONDS}"
                f"\nstatus={status}\nseconds={seconds}\n", encoding="utf-8")
            (directory / "output.log").write_text(output, encoding="utf-8")
            observed, states, positive, negative = (
                ("error", 0, 0, 0) if status == "timeout" else
                verdict(output, name))
        ok = {"Never": "yes", "not-run": "not-run"}.get(observed, "no")
        counts[observed if observed in counts else "sometimes"] += 1
        rows.append(f"premise={premise} file={relative} expected=Never "
                    f"observed={observed} ok={ok} states={states} "
                    f"positive={positive} negative={negative} "
                    f"seconds={seconds} test_sha256="
                    f"{sha256(path.read_bytes())}" +
                    (" reason=herd7-is-not-in-the-image" if herd is None
                     else ""))
        print(f"{TAG}: {rows[-1]}", flush=True)
    final = (f"{TAG}: {'FAIL' if counts['error'] else 'PASS'} "
             f"premises={len({row[2] for row in tests})} "
             f"never={counts['Never']} sometimes={counts['sometimes']} "
             f"not_run={counts['not-run']}" +
             (f" error={counts['error']}" if counts["error"] else ""))
    header = ["# MVP M8 ordering premises under herd7 (planning/"
              "mvp-m8-plan.md, D-3, D-9; M8-4)",
              f"specification_sha256={SPECIFICATION_SHA256}",
              f"sequences_sha256={sha256(SEQUENCES.read_bytes())}",
              f"started={stamp} seconds={round(time.monotonic() - started)}",
              f"goal_seconds={QUALIFY.GOAL_SECONDS}",
              f"probe version_herd7={version}"]
    (out / "litmus.txt").write_text("\n".join(header + rows + [final]) +
                                    "\n", encoding="utf-8")
    print(final)
    return 1 if counts["error"] or counts["sometimes"] else 0


# ------------------------------------------------------------- self-test
HERD = ("Test {name} Allowed\nStates 3\n0:x5=1; 1:x5=0;\nNo\nWitnesses\n"
        "Positive: {positive} Negative: {negative}\nCondition exists "
        "(0:x5=2)\nObservation {name} {word} {positive} {negative}\n"
        "Time {name} 0.00\n")
FAKE_SECTIONS = """\
Idx Name          Size      VMA               LMA               File off  Algn
  0 .mvp.text     00000020  0000000000001000  0000000000001000  00001000  2**4
                  CONTENTS, ALLOC, LOAD, READONLY, CODE
"""
FAKE_SYMBOLS = """\
SYMBOL TABLE:
0000000000000000 l    df *ABS*\t0000000000000000 mvp-ring.c
0000000000001000 l     F .mvp.text\t0000000000000008 load_le
0000000000000000 l    df *ABS*\t0000000000000000 mvp-payload.c
0000000000001008 l     F .mvp.text\t0000000000000008 load_le
0000000000001010 g     F .mvp.text\t0000000000000010 be_mvp_ring_publish
"""
FAKE_CODE = """\
0000000000001000 <load_le>:
    1000:\t00054703          \tlbu\ta4,0(a0)
    1004:\t8082                \tret
0000000000001010 <be_mvp_ring_publish>:
    1010:\te31c                \tsd\ta5,0(a4)
    1012:\t8082                \tret
"""


class Fake:
    """objdump and objcopy's answers for a synthetic ELF."""

    tools = {role: (f"/usr/bin/fake-{role}", "0" * 64) for role in ROLES}

    def __init__(self, code=FAKE_CODE, data=bytes(range(32))):
        self.code, self.data = code, data

    def file_digest(self, elf):
        return "f" * 64

    def nodebug_digest(self, elf):
        return "d" * 64

    def sections(self, elf):
        return parse_sections(FAKE_SECTIONS)

    def symbols(self, elf):
        return parse_symbols(FAKE_SYMBOLS)

    def disassembly(self, elf):
        return parse_disassembly(self.code)

    def contents(self, elf, section):
        return self.data


def self_test():
    results = []

    def case(name, passed, detail=""):
        results.append(bool(passed))
        print(f"{'ok  ' if passed else 'FAIL'} {name}"
              f"{'' if passed else ': ' + str(detail)[-600:]}")

    def refused(name, action, wanted):
        try:
            action()
        except Refusal as why:
            case(name, wanted in str(why), why)
        else:
            case(name, False, "not refused")

    # The committed record, excerpts, and tests.
    text = SEQUENCES.read_text(encoding="utf-8")
    symbols = recorded_symbols(text)
    excerpts = load_excerpts()
    case("each excerpt has one symbol line, each symbol line one excerpt",
         sorted((chain, name) for _, name, chain, _ in excerpts) ==
         sorted(symbols) and len(excerpts) == len(symbols))
    lines = record_lines(text)
    case("the record states the lock's two tools, two ELFs, and its counts",
         [line.split()[0] for line in lines[:2]] == ["tool", "tool"] and
         sum(line.startswith("elf ") for line in lines) == 2 and
         lines[-1] == f"symbols={len(excerpts)} lines="
         f"{sum(len(rows) for *_, rows in excerpts)}", lines[-1])
    spans = {}
    for line in lines:
        if line.startswith("symbol "):
            fields = dict(word.split("=", 1) for word in line.split()[1:])
            start = int(fields["address"], 16)
            spans[(fields["toolchain"], fields["name"])] = (
                start, start + int(fields["size"], 16), fields["excerpt"])
    case("each excerpt line lies inside its symbol, as the record names it",
         all(spans[(chain, name)][0] <= at < spans[(chain, name)][1] and
             spans[(chain, name)][2] == str(path.relative_to(REPO))
             for path, name, chain, rows in excerpts for at, _ in rows))
    try:
        tests = load_tests()
    except Refusal as why:
        case("the five tests load, each citing recorded digests", False, why)
        tests = []
    case("the five tests load, each citing recorded digests",
         [premise for _, _, premise, _ in tests] == list(PREMISES),
         [name for name, *_ in tests])
    premises = premise_rows(PLAN.read_text(encoding="utf-8"))
    first = (LITMUS / "L1.litmus").read_text(encoding="utf-8")
    digest = CITATION.search(first)[3]
    flipped = digest[:-1] + ("0" if digest[-1] != "0" else "1")
    for name, planted, wanted in (
            ("a planted bad digest", first.replace(digest, flipped, 1),
             "which sequences.txt does not record"),
            ("a symbol the record lacks", re.sub(
                r"\b(\w+)@gcc sha256", "no_such_symbol@gcc sha256", first,
                count=1), "which sequences.txt does not record"),
            ("another first line", first.replace("RISCV L1", "RISCV L9", 1),
             "first line"),
            ("no licence line", first.replace(f"(* {LICENCE[0]} *)",
                                              "(* *)", 1), "licence"),
            ("the premise's words changed", first.replace(
                "a domain hart that reads", "a domain hart reading", 1),
             "D-3 words"),
            ("no specification hash", first.replace(
                SPECIFICATION_SHA256, "0" * 64), "specification's"),
            ("no condition", re.sub(r"\nexists [^\n]*\n?$", "\n", first),
             "exists or forall"),
            ("a brace in the comment", first.replace(
                "build/mvp/gcc/be-mvp.elf and build/mvp/clang/be-mvp.elf",
                "build/mvp/{gcc,clang}/be-mvp.elf", 1), "a brace"),
            ("one toolchain's citations alone", re.sub(
                r"\b\w+@clang sha256=[0-9a-f]{64}", "", first),
             "cites no digest")):
        refused(name, lambda text=planted: parse_test(
            text, "L1", symbols, premises), wanted)
    refused("a test name outside L1 to L5", lambda: parse_test(
        first, "L6", symbols, premises), "L<1-5>")
    # herd7's outputs, read as qualify.py reads them.
    for name, output, wanted in (
            ("herd7 Never", HERD.format(name="L1", word="Never", positive=0,
                                        negative=3), ("Never", 3, 0, 3)),
            ("herd7 Sometimes", HERD.format(name="L1", word="Sometimes",
                                            positive=1, negative=2),
             ("Sometimes", 3, 1, 2)),
            ("herd7 Always", HERD.format(name="L1", word="Always",
                                         positive=3, negative=0),
             ("Always", 3, 3, 0)),
            ("herd7 with no Observation line", "Warning: File \"L1.litmus\""
             ": RISCV operation bltu is not implemented (yet)\n",
             ("error", 0, 0, 0)),
            ("herd7 with no execution", HERD.format(
                name="L1", word="Never", positive=0, negative=0),
             ("error", 0, 0, 0)),
            ("herd7 on another test", HERD.format(
                name="L2", word="Never", positive=0, negative=3),
             ("error", 0, 0, 0))):
        case(name, verdict(output, "L1") == wanted, verdict(output, "L1"))
    # The derivation against a fake objdump and objcopy.
    elfs = {"gcc": "build/mvp/gcc/be-mvp.elf"}
    ring = (EXCERPTS / "load_le-gcc.s", "load_le", "gcc",
            [(0x1000, normal(0x1000, "00054703", "lbu a4,0(a0)"))])
    publish = (EXCERPTS / "be_mvp_ring_publish-gcc.s",
               "be_mvp_ring_publish", "gcc",
               [(0x1010, normal(0x1010, "e31c", "sd a5,0(a4)"))])
    try:
        derived = derive(Fake(), Fake.tools, [ring, publish], elfs)
    except Refusal as why:
        derived = [str(why)] * 6
    case("the derivation: a local resolved by its address, its bytes, the "
         "counts", derived[2] == "elf toolchain=gcc file=build/mvp/gcc/"
         f"be-mvp.elf file_sha256={'f' * 64} nodebug_sha256={'d' * 64}" and
         derived[3:] == [
             "symbol toolchain=gcc name=be_mvp_ring_publish bind=global "
             f"section=.mvp.text address=0x1010 size=0x10 sha256="
             f"{sha256(bytes(range(16, 32)))} excerpt=mvp/verify/litmus/"
             "sequences/be_mvp_ring_publish-gcc.s lines=1",
             "symbol toolchain=gcc name=load_le bind=local:mvp-ring.c "
             f"section=.mvp.text address=0x1000 size=0x8 sha256="
             f"{sha256(bytes(range(8)))} excerpt=mvp/verify/litmus/"
             "sequences/load_le-gcc.s lines=1", "symbols=2 lines=2"],
         derived)
    changed = bytearray(range(32))
    changed[0x12] ^= 1
    moved = derive(Fake(data=bytes(changed)), Fake.tools, [ring, publish],
                   elfs)
    case("a changed byte changes its symbol's digest alone",
         moved[3] != derived[3] and moved[4] == derived[4], moved)
    relocated = derived[:2] + [derived[2].replace("d" * 64, "e" * 64)] + \
        moved[3:]
    found = differences(derived, relocated) or ""
    case("a difference names the first symbol that differs, before the ELF",
         found.startswith("be_mvp_ring_publish@gcc differs from "
                          "sequences.txt: sha256 ") and
         found.endswith("(and 1 more lines: re-derive under the re-proof "
                        "rule)"), found)
    found = differences(derived, derived[:2] + [derived[2].replace(
        "d" * 64, "e" * 64)] + derived[3:]) or ""
    case("an ELF that differs where no recorded symbol does is named",
         found.startswith("no recorded symbol differs, but recorded 'elf "
                          "toolchain=gcc"), found)
    case("the ELF file's own digest, path-dependent, is no difference",
         differences(derived, derived[:2] + [derived[2].replace(
             "f" * 64, "9" * 64)] + derived[3:]) is None)
    refused("an excerpt line the ELF does not hold", lambda: derive(
        Fake(code=FAKE_CODE.replace("a4,0(a0)", "a4,1(a0)")), Fake.tools,
        [ring], elfs), "not '1000: 00054703 lbu a4,0(a0)'")
    refused("an excerpt line outside its symbol", lambda: derive(
        Fake(), Fake.tools, [ring[:3] + (ring[3] + [(0x1010, normal(
            0x1010, "e31c", "sd a5,0(a4)"))],)], elfs),
        "1010 lies outside load_le")
    refused("an excerpt naming no symbol at its address", lambda: derive(
        Fake(), Fake.tools, [(ring[0], "store_le") + ring[2:]], elfs),
        "0 symbols store_le")
    refused("an excerpt without its licence", lambda: load_excerpt(
        pathlib.Path("drain-gcc.s"), "# drain\n    1000:\t8082\tret\n"),
        "licence")
    refused("an excerpt line that is not objdump's", lambda: load_excerpt(
        pathlib.Path("drain-gcc.s"), f"# {LICENCE[0]}\n# {LICENCE[1]}\n"
        f"# {SPECIFICATION_SHA256}\nfence w,w\n"), "neither a comment")
    lock = LOCK.read_text(encoding="utf-8")
    refused("a lock that pins another objdump", lambda: lock_tools(re.sub(
        r"(MVP_TOOL_cross_objdump_sha256=)[0-9a-f]{64}", r"\g<1>" + "0" * 64,
        lock)), "is not the lock's cross_objdump")
    print(f"{TAG}_SELF_TEST: {'PASS' if all(results) else 'FAIL'} "
          f"cases={len(results)}"
          f"{'' if all(results) else f' failed={results.count(False)}'}")
    return 0 if all(results) else 1


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--check-sequences", action="store_true")
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--scratch", type=pathlib.Path)
    parser.add_argument("--target")
    args = parser.parse_args(argv[1:])
    if (args.out and not args.run) or (bool(args.target) != args.write) or (
            args.scratch and not (args.check_sequences or args.write)):
        parser.error("--out is --run's, --target COMMIT --write's, and "
                     "--scratch --check-sequences' and --write's")
    if args.self_test:
        return self_test()
    try:
        if args.run:
            return run((args.out or REPO / "build" / "mvp" /
                        "verify").resolve())
        excerpts = load_excerpts()
        scratch = scratch_directory(args.scratch or SCRATCH)
        try:
            binutils = Binutils(scratch)
            if args.write:
                return write(args.target, binutils, excerpts)
            return check(SEQUENCES, binutils, excerpts)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
    except (OSError, Refusal, subprocess.CalledProcessError) as why:
        print(f"{TAG}{'' if args.run else '_SEQUENCES'}: FAIL {why}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
