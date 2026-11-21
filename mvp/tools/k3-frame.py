#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""M11-B's frame: the source policy of mvp/k3/ and of the board's new
tools, and the board gate's first step and record.

  k3-frame.py check [--root DIR]
  k3-frame.py published --pins FILE --dir DIR --out FILE
  k3-frame.py record --gate DIR --pins FILE STEP...
  k3-frame.py --self-test --scratch DIR

Purpose: planning/mvp-m11-board-addendum.md (B-1, B-10) puts M11-B's
tests in two tiers: tier 1 inside check, which reads no file of the board
vendor's, and tier 2, the board gate (mvp/k3/frame.mk), which reads the
vendor's published release files from the directory K3_PUBLISHED names.

check (tier 1, k3-frame-check) requires of the tree at --root: mvp/tools.mk's
one include directive, as tools/make-control.py --fragments reads it for
mvp/mvp and the Make controls; each fragment it names present, and no
other .mk under mvp/k3/; each fragment opening with the header and
tools.mk's guard naming itself, with no ?= and no include directive,
assigning only K3B_ and k3b_ names and using no export, unexport,
override, undefine, or vpath, and making rules only for k3- names and
paths under K3B_ variables, joining .PHONY, tools-check, and qemu-test
by k3- prerequisites alone; under
mvp/k3/, no symbolic link, executable, or script, and outside fixtures/
only .mk and .txt files with the header and .json files that parse; the
pins files' lines of their forms (sitting-pins.txt's `firmware` and `card`
lines), each name of a kind once, and published-pins.txt pinning at
least one file; observed.json named by no fragment but
session.mk, and sitting-pins.txt by none but card.mk; the header in each
new mvp/tools/k3-* and mvp/tests/test-k3-*; and, in all of these but the
fixtures, none of the words that the claim's phrasing rules keep out.

published (the gate's first step) reports each pinned file under --dir as
missing, not a regular file, of another size, or of another SHA-256, or
as passing, into --out, a new file. record (k3-board-gate) requires each
named step's record, ending in its PASS line, and no other; then writes
images.sha256, gate.txt, and MANIFEST.sha256 beside them.

Trust: it opens the published files read-only, without blocking on one
that is not a regular file, and writes only its outputs and its scratch.
Scope: M11-B's frame. Exit 0 pass, 1 fail or refused, 2 usage.
"""

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TAG = "BE_MVP_K3_FRAME"
FIRST = "k3-gate-published"
HEADER = ("SPDX-License-Identifier: GPL-3.0-only",
          "Copyright (C) 2026 James Morris <jmorris@namei.org>")
GUARD = ("ifneq ($(origin MVP_MAKE_CONTROL),file)",
         "$(error mvp/k3/{} is read through mvp/Makefile: make -C mvp "
         "TARGET)", "endif")
# MVP 1.0's board tools, which keep the header of their time.
EARLIER = {f"tools/k3-{name}" for name in (
    "campaign.sh", "console.sh", "env.sh", "input-characterize.sh",
    "make-partition.sh", "preflight.sh", "run.sh", "stage.sh",
    "uboot.py")} | {"tests/test-k3-make-partition.sh"}
OPTIONAL = re.compile(r" *(?:(?:override|export) +)*[A-Za-z_][\w.-]* *\?=")
# The words, written in parts so that this file holds none of them whole.
WORDS = re.compile(r"(?<![A-Za-z0-9_])(?:(?i:veri(?:fied)|isola(?:ted)|"
                   r"sandbo(?:xed)|certi(?:fied))|T(?:EE)|S(?:D))"
                   r"(?![A-Za-z0-9_])")
PIN = re.compile(r"(published|firmware|card) ([\w.-]+(?:/[\w.-]+)*) "
                 r"sha256=([0-9a-f]{64}) bytes=([1-9][0-9]*)")
PINS = {"published-pins.txt": "published",
        "sitting-pins.txt": ("firmware", "card"),
        "firmware-pins.txt": "firmware"}
NAMED_BY = {"observed.json": "session.mk", "sitting-pins.txt": "card.mk"}
STEP = re.compile(r"k3-gate-[a-z0-9]+(?:-[a-z0-9]+)*")
# A fragment's own targets, and the existing ones that it may join.
OWN = re.compile(r"k3-[a-z0-9]+(?:-[a-z0-9]+)*|\$\(K3B_[A-Z0-9_]+\)\S*")
JOINED = (".PHONY", "tools-check", "qemu-test")
# The names a fragment may assign, and the directives it may not use.
NAMED = re.compile(r"(?:K3B_|k3b_)\S*")
BARRED = ("export", "unexport", "override", "undefine", "vpath")
SKIPPED = re.compile(r" *(?:ifn?eq|ifn?def|else|endif|endef|export|"
                     r"unexport|override|vpath|-?include|sinclude)"
                     r"(?:[ \t(]|$)")
OPERATOR = re.compile(r":::?=|::?=|[?+!]?=|::?")


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTROL = load("make_control", "make-control.py")
EVIDENCE = load("evidence", "evidence.py")


class Refused(Exception):
    """An input the gate cannot be run on."""


def pins(path, kind, required=False):
    """{name: (SHA-256, bytes)} of PATH's `KIND NAME sha256=HEX bytes=N`
    lines, or {(KIND, name): ...} when KIND is a tuple of kinds; comments
    and blank lines aside, any other line is refused."""
    kinds, found = kind if isinstance(kind, tuple) else (kind,), {}
    for number, line in enumerate(path.read_text(
            encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        match = PIN.fullmatch(line)
        if not match or match.group(1) not in kinds or \
                {".", ".."} & set(match.group(2).split("/")):
            raise Refused(f"{path.name} line {number} is not " + " or ".join(
                f"`{each} NAME sha256=HEX bytes=N`" for each in kinds))
        key = match.group(1, 2) if isinstance(kind, tuple) else \
            match.group(2)
        if key in found:
            shown = " ".join(key) if isinstance(key, tuple) else key
            raise Refused(f"{path.name} names {shown} twice")
        found[key] = (match.group(3), int(match.group(4)))
    if required and not found:
        raise Refused(f"{path.name} pins no file")
    return found


def headed(text, exact=False):
    """Whether TEXT opens with the header: as its first two lines, each
    `# PART` (EXACT), or among its first five, in a comment's marks."""
    lines = text.splitlines()
    if exact:
        return lines[:2] == [f"# {part}" for part in HEADER]
    return all(part in [line.strip("#/* ") for line in lines[:5]]
               for part in HEADER)


def masked(line):
    """LINE with each variable reference, the references and parentheses
    nested in it included, written as `x`s: what is left is Make's own."""
    out, depth, at = list(line), 0, 0
    while at < len(line):
        if line[at] == "$":
            depth += line[at + 1:at + 2] in ("(", "{")
            out[at:at + 2], at = "xx"[:len(line) - at], at + 2
            continue
        if depth:
            depth += (line[at] in "({") - (line[at] in ")}")
            out[at] = "x"
        at += 1
    return "".join(out)


def joins(text):
    """The problems of TEXT's statements: a directive of BARRED; a name
    assigned (by an assignment, a define, or a target-specific variable)
    that NAMED does not match; a target that is not a `k3-` name or a
    path under a K3B_ variable, unless it is one of JOINED, and that one
    joined other than by `k3-` prerequisites alone, with no recipe.
    Bodies of `define` are not read."""
    lines, depth, problems = re.sub(r"\\\n", " ", text).split("\n"), 0, []
    for at, line in enumerate(lines):
        words = [] if line.startswith("\t") or depth else line.split()
        if words[:1] and words[0] in BARRED:
            problems.append(f"uses {words[0]}")
        head = re.sub(r"^ *(?:(?:override|export) +)*", "", line).split()
        if head[:1] == ["define"] or depth:
            name = (head + [""])[1]
            if not depth and not NAMED.fullmatch(name):
                problems.append(f"defines {name}, which is not a K3B_ or "
                                "k3b_ name")
            depth += (head[:1] == ["define"]) - (head[:1] == ["endef"])
            continue
        code = masked(line).split("#", 1)[0]
        found = OPERATOR.search(code)
        if line.startswith("\t") or SKIPPED.match(line) or not found:
            continue
        rule = found.group(0) in (":", "::")
        late = OPERATOR.search(code, found.end()) if rule else found
        if late and late.group(0) not in (":", "::"):
            name = (line[found.end():late.start()] if rule else
                    line[:found.start()]).strip()
            if not NAMED.fullmatch(name):
                problems.append(f"assigns {name}{' for a target' * rule}, "
                                "which is not a K3B_ or k3b_ name")
        if not rule:
            continue
        targets = line[:found.start()].split()
        problems += [f"joins {target}, which is not M11-B's"
                     for target in targets
                     if target not in JOINED and not OWN.fullmatch(target)]
        if not set(targets) & set(JOINED):
            continue
        later = next((each for each in lines[at + 1:] if each.strip() and
                      not each.lstrip(" ").startswith("#") and
                      not SKIPPED.match(each)), "")
        if len(targets) > 1 or found.group(0) != ":" or later[:1] == "\t" \
                or not all(OWN.fullmatch(word) for word in
                           line[found.end():len(code)].split()):
            problems.append(f"joins {targets[0]} other than by k3- "
                            "prerequisites alone")
    return problems


def fragment(path, text):
    """The problems of a fragment's own rules."""
    lines = text.splitlines()
    code = [line for line in lines if line.strip() and line[0] != "#"]
    problems = [] if code[:3] == [GUARD[0], GUARD[1].format(path.name),
                                  GUARD[2]] else [
        "does not open with tools.mk's guard naming it"]
    for line in lines:
        if not line.startswith("\t") and OPTIONAL.match(line):
            problems.append("assigns with ?=")
        if not line.startswith("\t") and CONTROL.DIRECTIVE.match(line):
            problems.append("holds an include directive")
    return problems + joins(text) + [
        f"names {name}, which only {owner} may"
        for name, owner in NAMED_BY.items()
        if name in text and path.name != owner]


def kept(path, top):
    """The problems of a file under mvp/k3/ but its fixtures; TOP, whether
    it lies in mvp/k3/ itself."""
    text = path.read_text(encoding="utf-8")
    problems = [f"holds {match.group(0)!r}, a word kept out"
                for match in WORDS.finditer(text)]
    if path.suffix not in (".mk", ".txt", ".json"):
        problems.append("is not a .mk, .txt, or .json file")
    elif path.suffix != ".json" and not headed(text, exact=True):
        problems.append("does not open with the header")
    elif path.suffix == ".json":
        try:
            json.loads(text)
        except ValueError:
            problems.append("does not parse as JSON")
    if top and path.suffix == ".mk":
        problems += fragment(path, text)
    if top and path.name in PINS:
        try:
            pins(path, PINS[path.name], path.name == "published-pins.txt")
        except Refused as error:
            problems.append(str(error))
    return problems


def check(root):
    """(findings, counts) of the frame's rules on the tree at ROOT."""
    mvp, findings, files = root / "mvp", [], 0
    k3 = mvp / "k3"
    try:
        named = CONTROL.fragments(mvp)
    except CONTROL.Refused as error:
        findings.append(str(error))
        named = None
    if named is not None:
        findings += [f"mvp/k3/{name} is named by mvp/tools.mk but missing"
                     for name in named if not (k3 / name).is_file()]
        findings += [f"{path.relative_to(root)} is not named by "
                     "mvp/tools.mk" for path in sorted(k3.rglob("*.mk"))
                     if path.relative_to(k3).parts[0] != "fixtures" and
                     path.relative_to(k3).as_posix() not in named]
    if not (k3 / "published-pins.txt").is_file():
        findings.append("mvp/k3/published-pins.txt is missing")
    for path in sorted(k3.rglob("*")):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            findings.append(f"{path.relative_to(root)} is a symbolic link "
                            "or special file")
            continue
        if path.is_dir():
            continue
        files += 1
        problems = ["is executable"] if path.stat().st_mode & 0o111 else []
        if path.suffix in (".py", ".sh"):
            problems.append("is a script, which lives under mvp/tools/ or "
                            "mvp/tests/")
        elif path.relative_to(k3).parts[0] != "fixtures":
            problems += kept(path, path.parent == k3)
        findings += [f"{path.relative_to(root)} {problem}"
                     for problem in problems]
    tools = [path for path in sorted((mvp / "tools").glob("k3-*")) +
             sorted((mvp / "tests").glob("test-k3-*"))
             if str(path.relative_to(mvp)) not in EARLIER]
    for path in tools:
        text = path.read_text(encoding="utf-8")
        if not headed(text):
            findings.append(f"{path.relative_to(root)} does not open with "
                            "the header")
        findings += [f"{path.relative_to(root)} holds {match.group(0)!r}, "
                     "a word kept out" for match in WORDS.finditer(text)]
    return findings, (f"fragments={len(named or [])} files={files} "
                      f"tools={len(tools)}")


def measure(path):
    """(bytes, SHA-256) of PATH, following a symbolic link, or why not."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    except FileNotFoundError:
        return "missing"
    except OSError as error:
        return f"unreadable ({error.strerror})"
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        return "not a regular file"
    with os.fdopen(descriptor, "rb") as file:
        digest, size = hashlib.sha256(), 0
        for block in iter(lambda: file.read(1 << 20), b""):
            digest.update(block)
            size += len(block)
    return size, digest.hexdigest()


def published(pins_path, directory, out):
    """The gate's first step, each pinned file reported; True if all pass."""
    known = pins(pins_path, "published", required=True)
    if not directory.is_absolute() or not directory.is_dir():
        raise Refused(f"{directory} is not an absolute path to a directory")
    lines = []
    for name, (digest, size) in known.items():
        found = measure(directory / name)
        if isinstance(found, str):
            lines.append(f"file {name}: FAIL {found}")
        elif found[0] != size:
            lines.append(f"file {name}: FAIL bytes={found[0]}, pinned {size}")
        elif found[1] != digest:
            lines.append(f"file {name}: FAIL sha256={found[1]}, pinned "
                         f"{digest}")
        else:
            lines.append(f"file {name}: PASS bytes={size} sha256={digest}")
    failed = sum(": FAIL " in line for line in lines)
    lines.append(f"BE_MVP_K3_GATE[{FIRST}]: {'FAIL' if failed else 'PASS'} "
                 f"files={len(known)}" + (f" failed={failed}" if failed
                                          else "") +
                 f" pins_sha256={EVIDENCE.file_sha(pins_path)}")
    text = "\n".join(lines) + "\n"
    try:
        with open(out, "x", encoding="ascii") as file:
            file.write(text)
    except FileExistsError as error:
        raise Refused(f"{out} exists; the gate removes its outputs "
                      "first") from error
    print(text, end="")
    return not failed


def record(gate, pins_path, steps):
    """The gate's record, written once every named step has passed."""
    if FIRST not in steps or len(set(steps)) != len(steps) or \
            not all(STEP.fullmatch(step) for step in steps):
        raise Refused(f"the steps are not distinct k3-gate-* steps among "
                      f"them {FIRST}: {' '.join(steps)}")
    directory = gate / "record"
    others = sorted(path.name for path in (directory / "steps").iterdir()
                    if path.name not in {f"{step}.txt" for step in steps})
    if others:
        raise Refused(f"steps/{others[0]} is the record of no named step")
    verdicts = []
    for step in steps:
        path = directory / "steps" / f"{step}.txt"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        last = text.splitlines()[-1] if text.strip() else ""
        if not re.fullmatch(rf"BE_MVP_K3_GATE\[{step}\]: PASS(?: .*)?", last):
            raise Refused(f"step {step} did not pass: {last!r}")
        verdicts.append(f"step_{step}={last}")
    pinned = EVIDENCE.file_sha(pins_path)
    if not verdicts[steps.index(FIRST)].endswith(f" pins_sha256={pinned}"):
        raise Refused(f"step {FIRST} checked other pins than "
                      f"{pins_path.name}'s")
    images = sorted(path for path in (gate / "images").rglob("*")
                    if path.is_file())
    commit, tree = EVIDENCE.source_state()
    last = f"BE_MVP_K3_GATE: PASS steps={len(steps)} images={len(images)}"
    texts = {"images.sha256": "".join(
        f"{EVIDENCE.file_sha(path)}  {path.relative_to(gate.parent.parent)}"
        "\n" for path in images), "gate.txt": "\n".join([
            "schema=be-mvp-k3-gate-v1", f"source_commit={commit}",
            f"source_tree={tree}", f"published_pins_sha256={pinned}",
            "steps=" + ",".join(steps), *verdicts, f"images={len(images)}",
            last]) + "\n"}
    for name, text in texts.items():
        with open(directory / name, "x", encoding="ascii") as file:
            file.write(text)
    EVIDENCE.write_manifest(directory)
    print(last)


def self_test(scratch):
    """Each rule's seeded defect fails by that rule alone."""
    shutil.rmtree(scratch, ignore_errors=True)
    mvp, results, runs = HERE.parent, [], iter(range(1000))

    def case(name, condition):
        results.append(bool(condition))
        print(f"{'ok  ' if condition else 'FAIL'} {name}")

    def tree(name):
        top = scratch / "check" / name
        shutil.copytree(mvp / "k3", top / "mvp" / "k3", symlinks=True)
        for path in [mvp / "tools.mk"] + sorted(
                (mvp / "tools").glob("k3-*")) + sorted(
                    (mvp / "tests").glob("test-k3-*")):
            target = top / "mvp" / path.relative_to(mvp)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        return top

    def edit(path, old, new):
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return old in text

    def put(path, data, mode=0o644):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode("utf-8") if isinstance(data, str)
                         else data)
        path.chmod(mode)
        return True

    head = "".join(f"# {part}\n" for part in HEADER)
    word, k3, mk = "S" + "D", "mvp/k3/", "mvp/tools.mk"
    pinned = (mvp / "k3" / "published-pins.txt").read_text(encoding="utf-8")
    first = next(line for line in pinned.splitlines()
                 if line.startswith("published "))
    name = first.split()[1]
    # A made-up image's pins. The two cases that use them write the copied
    # sitting-pins.txt whole, so that each rests on its own lines alone,
    # whatever images the tree's file pins.
    card = f"card x sha256={'0' * 64} bytes=1\n"
    mutations = [
        ("the tree as committed", None, None),
        ("a word in a fixture, and MVP 1.0's tools", lambda t: put(
            t / k3 / "fixtures/x/capture.txt", word), None),
        ("fragments found by a wildcard", lambda t: edit(
            t / mk, "$(addprefix", "$(wildcard"), "one include directive"),
        ("a second include directive", lambda t: edit(
            t / mk, "\ninclude ", "\n-include $(MVP_DIR)/k3/x.mk\ninclude "),
         "one include directive"),
        ("common.mk not named first", lambda t: edit(
            t / mk, "common.mk frame.mk", "frame.mk common.mk"),
         "one include directive"),
        ("a fragment named twice", lambda t: edit(
            t / mk, "frame.mk ", "frame.mk frame.mk "),
         "one include directive"),
        ("an unnamed fragment", lambda t: put(
            t / k3 / "extra.mk", head + "\n".join(GUARD).format("extra.mk")),
         "extra.mk is not named"),
        ("an unnamed .mk below mvp/k3/", lambda t: put(
            t / k3 / "breach/extra.mk", head), "breach/extra.mk is not"),
        ("a named fragment missing", lambda t: (
            t / k3 / "session.mk").unlink() is None, "session.mk is named"),
        ("a fragment without the header", lambda t: edit(
            t / k3 / "tree.mk", "# " + HEADER[0], "#"),
         "tree.mk does not open with the header"),
        ("a fragment without the guard", lambda t: edit(
            t / k3 / "tree.mk", "),file)", "),undefined)"), "guard"),
        ("a guard naming another fragment", lambda t: edit(
            t / k3 / "tree.mk", "k3/tree.mk is", "k3/card.mk is"), "guard"),
        ("a ?= in a fragment", lambda t: edit(
            t / k3 / "tree.mk", "\nendif\n", "\nendif\nK3B_X ?= 1\n"),
         "assigns with ?="),
        ("an include directive in a fragment", lambda t: edit(
            t / k3 / "tree.mk", "\nendif\n", "\nendif\ninclude x.mk\n"),
         "holds an include directive"),
        ("a fragment joining an existing target", lambda t: edit(
            t / k3 / "breach.mk", "\nendif\n",
            "\nendif\nimage: k3-frame-check\n"), "joins image, which is not"),
        ("tools-check joined with a recipe", lambda t: edit(
            t / k3 / "frame.mk", "tools-check: k3-frame-check\n",
            "tools-check: k3-frame-check\n\t@true\n"),
         "joins tools-check other than"),
        ("qemu-test joined with a variable", lambda t: edit(
            t / k3 / "tree.mk", "\nendif\n",
            "\nendif\nqemu-test: K3B_X := 1\n"), "joins qemu-test other"),
        ("an existing variable assigned", lambda t: edit(
            t / k3 / "tree.mk", "\nendif\n", "\nendif\nPYTHON := x\n"),
         "assigns PYTHON, which is not"),
        ("an existing variable defined", lambda t: edit(
            t / k3 / "tree.mk", "\nendif\n",
            "\nendif\ndefine PYTHON\nx\nendef\n"), "defines PYTHON, which"),
        ("an existing variable for one target", lambda t: edit(
            t / k3 / "tree.mk", "\nendif\n",
            "\nendif\nk3-recipe-check: PYTHON := x\n"),
         "assigns PYTHON for a target,"),
        ("an export directive", lambda t: edit(
            t / k3 / "tree.mk", "\nendif\n", "\nendif\nexport K3B_X := 1\n"),
         "uses export"),
        ("observed.json named by another fragment", lambda t: edit(
            t / k3 / "tree.mk", "\nendif\n", "\nendif\n# observed.json\n"),
         "names observed.json, which only session.mk may"),
        ("sitting-pins.txt named by another fragment", lambda t: edit(
            t / k3 / "session.mk", "\nendif\n",
            "\nendif\n# sitting-pins.txt\n"),
         "names sitting-pins.txt, which only card.mk may"),
        ("a script under mvp/k3/", lambda t: put(
            t / k3 / "fixtures/x/run.py", "print()\n"), "is a script"),
        ("an executable file", lambda t: put(
            t / k3 / "notes.txt", head, 0o755), "notes.txt is executable"),
        ("a symbolic link", lambda t: (t / k3 / "link.txt").symlink_to(
            "published-pins.txt") is None, "link.txt is a symbolic link"),
        ("another kind of file", lambda t: put(t / k3 / "notes.md", head),
         "notes.md is not a .mk"),
        ("a .txt file without the header", lambda t: edit(
            t / k3 / "sitting-pins.txt", "# " + HEADER[1], "#"),
         "sitting-pins.txt does not open with the header"),
        ("a .json file that does not parse", lambda t: put(
            t / k3 / "platform.json", "{\n"), "does not parse as JSON"),
        ("the published pins missing", lambda t: (
            t / k3 / "published-pins.txt").unlink() is None,
         "published-pins.txt is missing"),
        ("a pin not of its form", lambda t: edit(
            t / k3 / "published-pins.txt", first,
            first.replace("sha256=", "sha256=x")), "is not `published NAME"),
        ("a pin naming a parent directory", lambda t: edit(
            t / k3 / "published-pins.txt", first,
            first.replace(" ", " ../", 1)), "is not `published NAME"),
        ("a file pinned twice", lambda t: edit(
            t / k3 / "published-pins.txt", first, f"{first}\n{first}"),
         f"names {name} twice"),
        ("no published file pinned", lambda t: put(
            t / k3 / "published-pins.txt", head), "pins no file"),
        ("a sitting pin of another kind", lambda t: edit(
            t / k3 / "sitting-pins.txt", head, head + first + "\n"),
         "is not `firmware NAME"),
        ("a firmware pin and a card pin for one image", lambda t: put(
            t / k3 / "sitting-pins.txt",
            head + card.replace("card", "firmware", 1) + card), None),
        ("a second card pin for one image", lambda t: put(
            t / k3 / "sitting-pins.txt", head + card + card),
         "names card x twice"),
        ("a card pin among the published ones", lambda t: edit(
            t / k3 / "published-pins.txt", first,
            "card" + first[len("published"):]), "is not `published NAME"),
        ("a new tool without the header", lambda t: put(
            t / "mvp/tools/k3-new.py", "print()\n"),
         "k3-new.py does not open with the header"),
        ("a word in a new tool", lambda t: put(
            t / "mvp/tests/test-k3-new.sh", head + f"# an {word} card\n"),
         "a word kept out"),
        ("a word under mvp/k3/", lambda t: edit(
            t / k3 / "tree.mk", "\nendif\n", f"\nendif\n# an {word} card\n"),
         "tree.mk holds"),
    ]
    for label, mutate, expected in mutations:
        top = tree(re.sub(r"\W+", "-", label))
        changed = mutate(top) if mutate else True
        findings = check(top)[0]
        case(f"check: {label}", changed and (
            findings == [] if expected is None else
            len(findings) == 1 and expected in findings[0]))

    release, files = scratch / "release", {"a.bin": b"first\n",
                                           "sub/b.bin": b"second file\n"}
    for name, data in files.items():
        put(release / name, data)
    shutil.copytree(release, scratch / "other")
    good = scratch / "pins.txt"
    put(good, head + "".join(
        f"published {name} sha256={hashlib.sha256(data).hexdigest()} "
        f"bytes={len(data)}\n" for name, data in files.items()))

    def step(directory=release, pins_path=good, out=None):
        out = out or scratch / f"step-{next(runs)}.txt"
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                passed = published(pins_path, directory, out)
        except Refused as error:
            return f"refused {error}"
        return "PASS" if passed else out.read_text(encoding="ascii")

    case("published: the pinned files pass", step() == "PASS")
    (release / "a.bin").unlink()
    (release / "a.bin").symlink_to(scratch / "other" / "a.bin")
    case("published: a symbolic link to a pinned file passes",
         step() == "PASS")
    (release / "a.bin").unlink()
    report = step()
    case("published: a missing file fails, and every file is reported",
         "file a.bin: FAIL missing\nfile sub/b.bin: PASS " in report and
         " files=2 failed=1 " in report)
    for label, change, expected in (
            ("a file of another size", lambda path: put(path, "first!\n"),
             "FAIL bytes=7, pinned 6"),
            ("a file with another SHA-256", lambda path: put(path, "FIRST\n"),
             "FAIL sha256="),
            ("a directory in a file's place", lambda path: path.mkdir(),
             "FAIL not a regular file"),
            ("a FIFO in a file's place, never read", os.mkfifo,
             "FAIL not a regular file")):
        change(release / "a.bin")
        case(f"published: {label}: fails", f"file a.bin: {expected}" in
             step())
        if (release / "a.bin").is_dir():
            (release / "a.bin").rmdir()
        else:
            (release / "a.bin").unlink()
    put(release / "a.bin", files["a.bin"])
    for label, directory, text, out, expected in (
            ("a directory that does not exist", scratch / "absent", None,
             None, "not an absolute path to a directory"),
            ("a relative directory", pathlib.Path("release"), None, None,
             "not an absolute path"),
            ("pins not of their form", release, head + first + "x", None,
             "is not `published NAME"),
            ("pins of no file", release, head, None, "pins no file"),
            ("an existing record", release, None, good, "exists")):
        pins_path = good
        if text is not None:
            pins_path = scratch / f"pins-{next(runs)}.txt"
            put(pins_path, text)
        case(f"published: {label}: refused",
             expected in step(directory, pins_path, out))

    def gate(steps, extra=None, pins_path=good):
        top = scratch / "record" / str(next(runs)) / "k3" / "gate"
        put(top / "images" / "two-guests-off" / "board.json", "{}\n")
        steps_directory = top / "record" / "steps"
        steps_directory.mkdir(parents=True)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                published(good, release, steps_directory / f"{FIRST}.txt")
                for name, text in (extra or {}).items():
                    put(steps_directory / name, text)
                record(top, pins_path, steps)
        except Refused as error:
            return top, str(error)
        return top, ""

    passing = {"k3-gate-x.txt": "BE_MVP_K3_GATE[k3-gate-x]: PASS\n"}
    top, error = gate([FIRST, "k3-gate-x"], passing)
    text = "" if error else (top / "record" / "gate.txt").read_text(
        encoding="ascii")
    case("record: each step's verdict, every image, and a manifest that "
         "verifies", "\nstep_k3-gate-x=BE_MVP_K3_GATE[k3-gate-x]: PASS\n" in
         text and text.endswith("\nBE_MVP_K3_GATE: PASS steps=2 images=1\n")
         and (top / "record" / "images.sha256").read_text(
             encoding="ascii").endswith(
                 "  k3/gate/images/two-guests-off/board.json\n") and
         EVIDENCE.verify(top / "record") == [])
    other = scratch / "other-pins.txt"
    put(other, good.read_text(encoding="utf-8") + "# changed\n")
    for label, steps, extra, pins_path, expected in (
            ("a named step without its record", [FIRST, "k3-gate-x"], None,
             good, "step k3-gate-x did not pass"),
            ("a step that failed", [FIRST, "k3-gate-x"],
             {"k3-gate-x.txt": "BE_MVP_K3_GATE[k3-gate-x]: FAIL\n"}, good,
             "step k3-gate-x did not pass"),
            ("a step's record that no step names", [FIRST], passing, good,
             "steps/k3-gate-x.txt is the record of no named step"),
            ("a gate without its first step", ["k3-gate-x"], passing, good,
             "among them k3-gate-published"),
            ("a first step of other pins", [FIRST], None, other,
             "checked other pins")):
        case(f"record: {label}: refused",
             expected in gate(steps, extra, pins_path)[1])

    wrapper = scratch / "wrapper" / "mvp"
    (wrapper / "tools").mkdir(parents=True)
    shutil.copy2(mvp / "mvp", wrapper / "mvp")
    shutil.copy2(mvp / "tools" / "make-control.py", wrapper / "tools")
    put(wrapper / "Makefile", "MVP_DIR := $(abspath $(dir $(lastword "
        "$(MAKEFILE_LIST))))\ninclude $(MVP_DIR)/tools.mk\n")
    put(wrapper / "tools.mk",
        "include $(addprefix $(MVP_DIR)/k3/,common.mk frame.mk)\n")
    put(wrapper / "k3" / "common.mk", "\n")
    target = "k3-board-gate:\n\t@echo BE_MVP_K3_FRAME: reached\n"

    def wrap():
        result = subprocess.run(
            ["/usr/bin/bash", str(wrapper / "mvp"), "k3-board-gate",
             "K3_PUBLISHED=/nonexistent"], capture_output=True, text=True,
            env={"PATH": "/usr/bin", "HOME": str(scratch)}, check=False)
        return result.returncode, result.stdout + result.stderr

    put(wrapper / "k3" / "frame.mk", target)
    case("mvp/mvp: a target in a named fragment is run",
         wrap() == (0, "BE_MVP_K3_FRAME: reached\n"))
    put(wrapper / "k3" / "frame.mk", "\n")
    put(wrapper / "k3" / "other.mk", target)
    status, output = wrap()
    case("mvp/mvp: a target in an unnamed fragment is not run", status == 3
         and "not-implemented-until-M11-B1 k3-board-gate" in output)
    edit(wrapper / "tools.mk", "$(addprefix", "$(wildcard")
    status, output = wrap()
    case("mvp/mvp: an include other than the frame's is refused",
         status == 2 and "BE_MVP_MAKE_CONTROL: FAIL" in output)

    shutil.rmtree(scratch, ignore_errors=True)
    failed = results.count(False)
    print(f"{TAG}_SELF_TEST: {'FAIL' if failed else 'PASS'} "
          f"cases={len(results)}")
    return 1 if failed else 0


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch", type=pathlib.Path)
    commands = parser.add_subparsers(dest="command")
    command = commands.add_parser("check")
    command.add_argument("--root", type=pathlib.Path, default=HERE.parents[1])
    command = commands.add_parser("published")
    for option in ("--pins", "--dir", "--out"):
        command.add_argument(option, type=pathlib.Path, required=True)
    command = commands.add_parser("record")
    command.add_argument("--gate", type=pathlib.Path, required=True)
    command.add_argument("--pins", type=pathlib.Path, required=True)
    command.add_argument("steps", nargs="+")
    args = parser.parse_args(argv[1:])
    if args.self_test == bool(args.command) or \
            args.self_test != bool(args.scratch):
        parser.error("give one of check, published, record, or "
                     "--self-test --scratch DIR")
    try:
        if args.self_test:
            return self_test(args.scratch.resolve())
        if args.command == "published":
            return 0 if published(args.pins, args.dir, args.out) else 1
        if args.command == "record":
            record(args.gate, args.pins, args.steps)
            return 0
    except (Refused, OSError) as error:
        print(f"BE_MVP_K3_GATE: FAIL refused: {error}")
        return 1
    findings, counts = check(args.root.resolve())
    print("".join(f"finding: {finding}\n" for finding in findings), end="")
    print(f"{TAG}: {'FAIL' if findings else 'PASS'} {counts}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
