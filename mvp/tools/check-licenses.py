#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""
check-licenses.py check [--root DIR]
check-licenses.py --self-test --scratch DIR

Every SPDX-License-Identifier a tracked file's header names must have its
text under LICENSES/ and be named in the root COPYING (row L of the RC3
snapshot reviews, 2026-11-01: the one GPL-2.0-only file had no text).

check reads the first three lines of every tracked file (`git ls-files`
where the root is a repository's top level; elsewhere, as in the clean
evaluator's mount, every regular file under the root but .git, build, and
node_modules), after a
YAML front matter where there is one (the skills' SKILL.md), parses the
SPDX-License-Identifier expression there (a line that is the tag and an
expression and nothing else but a comment opener and closer; OR, AND,
WITH, and parentheses are the operators; the exception after WITH is not
a licence; a sentence that mentions the tag is not a header), and
requires, for each identifier found, LICENSES/<identifier> with a
`Valid-License-Identifier: <identifier>` line and a `License-Text:` line
(the Linux kernel's LICENSES/ form), and the identifier's mention in
COPYING. A mention of an identifier later in a file (a plan's prose, a
checker's code) is not a use. The guest userland's external inputs
(planning/mvp-m7-plan.md, D-9), BusyBox and musl, are never committed,
but each `source` line of the tracked guest pins (mvp/guest/pins.txt)
names its input's licence (license=), and that is a use too, with the
same requirements; so is each `licence` line of the tracked licence
manifest (mvp/docs/licence-manifest.md, which mvp/tools/licence-manifest.py
generates: the firmware's and the guests' components, planning/
mvp-m10-plan.md, D-5). It prints one line per identifier with its file,
external-input, and manifest counts, then BE_MVP_LICENSES: PASS|FAIL
identifiers=<n> files=<m> texts=<k> source=git|walk external=<e>
manifest=<l>, and exits 1 on FAIL.

--self-test builds trees under --scratch and checks that each refusal
fires for its own reason and that the good tree passes.

Trust: test-only and read-only; it opens no file beyond its first 4 KiB
but the guest pins.
"""

import argparse
import pathlib
import re
import subprocess
import sys

# A header line is the tag and an expression and nothing else, but a
# comment opener before and a comment closer after (the Linux kernel's
# placements); a sentence that mentions the tag is not one.
SPDX = re.compile(r"^\s*(?:#|//|/\*|\(\*|\*|<!--|;|--|dnl|%|@c|\.\\\")?\s*"
                  r"SPDX-License-Identifier:\s*([A-Za-z0-9.+()\s-]+?)\s*"
                  r"(?:-->|\*/|\*\)|\})?\s*$")
IDENTIFIER = re.compile(r"[A-Za-z0-9.+-]*[A-Za-z0-9+]")
OPERATORS = {"OR", "AND", "WITH", "or", "and", "with"}
HEADER_LINES, HEADER_BYTES = 3, 4096
SKIP_DIRS = {".git", "build", "node_modules"}
LICENSES, COPYING = "LICENSES", "COPYING"
# The guest pins, whose `source` lines name the external inputs' licences.
EXTERNAL_PINS = "mvp/guest/pins.txt"
SOURCE_LICENCE = re.compile(r"^source (\S+) (?:\S+ )*license=(\S+)(?: |$)")
# The licence manifest, whose `licence` lines name its components' licences.
MANIFEST = "mvp/docs/licence-manifest.md"
MANIFEST_LICENCE = re.compile(r"^licence (\S+) ([A-Za-z0-9.+()\s-]+)$")


def git_toplevel(root):
    """The repository whose top level is ROOT, or None (no git, no
    repository, or ROOT inside one: a scratch tree under build/)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True, check=False)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    top = result.stdout.decode("utf-8").strip()
    return top if top and pathlib.Path(top).resolve() == root else None


def tracked_files(root, walk=False):
    """(paths, source): git's tracked files, or a walk where git finds no
    repository with ROOT as its top level, or when WALK says so."""
    if not walk and git_toplevel(root) is not None:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--full-name"],
            capture_output=True, check=True)
        names = [name for name in result.stdout.decode("utf-8").split("\0")
                 if name]
        return [root / name for name in names], "git"
    paths = []
    for directory, dirs, files in root.walk():
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        paths += [directory / name for name in sorted(files)]
    return paths, "walk"


def identifiers_in(expression):
    """The licence identifiers of an SPDX expression, exceptions left out."""
    tokens = expression.replace("(", " ").replace(")", " ").split()
    found, after_with = [], False
    for token in tokens:
        if token in OPERATORS:
            after_with = token.lower() == "with"
            continue
        if not IDENTIFIER.fullmatch(token):
            return []
        if not after_with:
            found.append(token)
        after_with = False
    return found


def header_identifiers(path):
    """The identifiers an SPDX line in PATH's first lines names, or []."""
    try:
        with open(path, "rb") as handle:
            head = handle.read(HEADER_BYTES)
    except OSError:
        return []
    if b"\0" in head:
        return []
    lines = head.decode("latin-1").splitlines()
    # A YAML front matter (the skills' SKILL.md) precedes the header.
    if lines and lines[0].strip() == "---":
        closing = next((i for i, line in enumerate(lines[1:], 1)
                        if line.strip() == "---"), None)
        if closing is not None:
            lines = lines[closing + 1:]
    for line in lines[:HEADER_LINES]:
        match = SPDX.search(line)
        if match:
            return identifiers_in(match.group(1))
    return []


def external_licences(root, paths):
    """[(identifier, where)]: each licence a `source` line of the guest pins
    names, when the pins are among PATHS; a malformed licence stands for
    itself, so that its text is missing."""
    pins = root / EXTERNAL_PINS
    if pins not in paths or not pins.is_file():
        return []
    found = []
    for line in pins.read_text(encoding="utf-8").splitlines():
        match = SOURCE_LICENCE.match(line)
        if match:
            for identifier in identifiers_in(match.group(2)) or \
                    [match.group(2)]:
                found.append((identifier, f"{EXTERNAL_PINS} (source "
                                          f"{match.group(1)})"))
    return found


def manifest_licences(root, paths):
    """[(identifier, where)]: each licence a `licence` line of the licence
    manifest names, when the manifest is among PATHS; a malformed licence
    stands for itself, so that its text is missing."""
    manifest = root / MANIFEST
    if manifest not in paths or not manifest.is_file():
        return []
    found = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = MANIFEST_LICENCE.match(line)
        if match:
            for identifier in identifiers_in(match.group(2)) or \
                    [match.group(2)]:
                found.append((identifier, f"{MANIFEST} (licence "
                                          f"{match.group(1)})"))
    return found


def text_valid(root, identifier):
    """Why LICENSES/<identifier> is not a licence text, or None."""
    path = root / LICENSES / identifier
    if not path.is_file():
        return f"{LICENSES}/{identifier} is missing"
    text = path.read_text(encoding="utf-8", errors="replace")
    if f"Valid-License-Identifier: {identifier}\n" not in text:
        return (f"{LICENSES}/{identifier} has no "
                f"'Valid-License-Identifier: {identifier}' line")
    if "\nLicense-Text:\n" not in text:
        return f"{LICENSES}/{identifier} has no 'License-Text:' line"
    return None


def check(root, walk=False):
    """(lines, findings): the per-identifier lines and the findings."""
    root = pathlib.Path(root).resolve()
    paths, source = tracked_files(root, walk)
    uses, external, manifest, files = {}, {}, {}, 0
    for path in paths:
        if not path.is_file() or path.is_symlink():
            continue
        if path.parent == root / LICENSES:
            continue
        found = header_identifiers(path)
        if found:
            files += 1
        for identifier in found:
            uses.setdefault(identifier, []).append(
                path.relative_to(root).as_posix())
    for identifier, where in external_licences(root, set(paths)):
        external.setdefault(identifier, []).append(where)
    for identifier, where in manifest_licences(root, set(paths)):
        manifest.setdefault(identifier, []).append(where)
    findings = []
    copying = root / COPYING
    copying_text = copying.read_text(encoding="utf-8") \
        if copying.is_file() else None
    if copying_text is None:
        findings.append(f"{COPYING} is missing at the root")
    lines = []
    for identifier in sorted(set(uses) | set(external) | set(manifest)):
        users = uses.get(identifier, []) + external.get(identifier, []) + \
            manifest.get(identifier, [])
        lines.append(f"{identifier}: files={len(uses.get(identifier, []))} "
                     f"external={len(external.get(identifier, []))} "
                     f"manifest={len(manifest.get(identifier, []))} "
                     f"first={users[0]}")
        problem = text_valid(root, identifier)
        if problem:
            findings.append(f"{problem} (used by {len(users)}, first "
                            f"{users[0]})")
        if copying_text is not None and identifier not in copying_text:
            findings.append(f"{COPYING} does not name {identifier} "
                            f"(used by {users[0]})")
    texts = sorted(p.name for p in (root / LICENSES).iterdir()
                   if p.is_file()) if (root / LICENSES).is_dir() else []
    for name in texts:
        if name not in uses and name not in external and name not in manifest:
            findings.append(f"{LICENSES}/{name} is used by no tracked file, "
                            "external input, or licence manifest row")
    summary = (f"BE_MVP_LICENSES: {'FAIL' if findings else 'PASS'} "
               f"identifiers={len(set(uses) | set(external) | set(manifest))}"
               f" files={files} texts={len(texts)} source={source} "
               f"external={sum(len(items) for items in external.values())} "
               f"manifest={sum(len(items) for items in manifest.values())}")
    return lines + [f"finding: {f}" for f in findings] + [summary], findings


def self_test(scratch):
    scratch = pathlib.Path(scratch)
    gpl3 = ("Valid-License-Identifier: GPL-3.0-only\n"
            "SPDX-URL: https://spdx.org/licenses/GPL-3.0.html\n"
            "License-Text:\n\n(the text)\n")

    def tree(name, files):
        root = scratch / name
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return root

    good = {
        "LICENSES/GPL-3.0-only": gpl3,
        "COPYING": "Beryllium is GPL-3.0-only.\n",
        "a.c": "// SPDX-License-Identifier: GPL-3.0-only\nint x;\n",
        "b.md": "<!-- SPDX-License-Identifier: GPL-3.0-only -->\n# b\n",
        "c.sh": "#!/bin/sh\n# SPDX-License-Identifier: GPL-3.0-only\n",
        "r.v": "(* SPDX-License-Identifier: GPL-3.0-only *)\nTheorem t.\n",
        # A mention past the header is not a use, nor is a sentence in
        # the header lines that names the tag (a COPYING's).
        "d.txt": "one\ntwo\nthree\nSPDX-License-Identifier: MIT\n",
        "COPYING-like.txt": "Licensed under the GPL, version 3 only\n"
                            "(SPDX-License-Identifier: MIT). The text is\n",
        "e.json": "{}\n",
        "SKILL.md": "---\nname: s\ndescription: d\n---\n\n"
                    "<!-- SPDX-License-Identifier: GPL-3.0-only -->\n",
    }
    cases = [
        ("good", {}, None),
        ("a text that is missing",
         {"f.c": "// SPDX-License-Identifier: GPL-2.0-only\n"},
         "LICENSES/GPL-2.0-only is missing"),
        ("a text without its identifier line",
         {"f.c": "// SPDX-License-Identifier: GPL-2.0-only\n",
          "LICENSES/GPL-2.0-only": gpl3,
          "COPYING": "GPL-3.0-only and GPL-2.0-only.\n"},
         "has no 'Valid-License-Identifier: GPL-2.0-only' line"),
        ("a text without License-Text",
         {"f.c": "// SPDX-License-Identifier: GPL-2.0-only\n",
          "LICENSES/GPL-2.0-only": "Valid-License-Identifier: GPL-2.0-only\n",
          "COPYING": "GPL-3.0-only and GPL-2.0-only.\n"},
         "has no 'License-Text:' line"),
        ("COPYING not naming a licence in use",
         {"f.c": "// SPDX-License-Identifier: GPL-2.0-only\n",
          "LICENSES/GPL-2.0-only": gpl3.replace("3.0", "2.0")},
         "COPYING does not name GPL-2.0-only"),
        ("no COPYING", {"COPYING": None}, "COPYING is missing at the root"),
        ("an OR expression with an unknown licence",
         {"f.c": "// SPDX-License-Identifier: (GPL-3.0-only OR MIT)\n"},
         "LICENSES/MIT is missing"),
        ("a text no file uses",
         {"LICENSES/MIT": gpl3.replace("GPL-3.0-only", "MIT")},
         "LICENSES/MIT is used by no tracked file"),
        ("an external input's licence without its text",
         {EXTERNAL_PINS: "source musl version=1.2.6 license=MIT\n"},
         "LICENSES/MIT is missing (used by 1, first mvp/guest/pins.txt "
         "(source musl))"),
        ("an external input's licence that COPYING does not name",
         {EXTERNAL_PINS: "source musl version=1.2.6 license=MIT\n",
          "LICENSES/MIT": gpl3.replace("GPL-3.0-only", "MIT")},
         "COPYING does not name MIT (used by mvp/guest/pins.txt (source "
         "musl))"),
        ("an external input's licence, its text, and COPYING",
         {EXTERNAL_PINS: "source musl version=1.2.6 license=MIT\n",
          "LICENSES/MIT": gpl3.replace("GPL-3.0-only", "MIT"),
          "COPYING": "GPL-3.0-only; the guest's musl is MIT.\n"}, None),
        ("a licence the licence manifest names without its text",
         {MANIFEST: "licence opensbi BSD-2-Clause\n"},
         "LICENSES/BSD-2-Clause is missing (used by 1, first "
         "mvp/docs/licence-manifest.md (licence opensbi))"),
        ("a licence the licence manifest names that COPYING does not name",
         {MANIFEST: "licence opensbi BSD-2-Clause\n",
          "LICENSES/BSD-2-Clause": gpl3.replace("GPL-3.0-only",
                                                "BSD-2-Clause")},
         "COPYING does not name BSD-2-Clause (used by "
         "mvp/docs/licence-manifest.md (licence opensbi))"),
        ("a text only the licence manifest uses, and COPYING",
         {MANIFEST: "licence opensbi BSD-2-Clause\n",
          "LICENSES/BSD-2-Clause": gpl3.replace("GPL-3.0-only",
                                                "BSD-2-Clause"),
          "COPYING": "GPL-3.0-only; OpenSBI is BSD-2-Clause.\n"}, None),
    ]
    failed = 0
    for name, changes, expected in cases:
        files = dict(good)
        for relative, content in changes.items():
            if content is None:
                files.pop(relative)
            else:
                files[relative] = content
        root = tree(name.replace(" ", "-"), files)
        # The scratch trees lie inside a repository or outside any: the
        # walk, which the clean evaluator's mount also takes.
        lines, findings = check(root, walk=True)
        if expected is None:
            external = 1 if EXTERNAL_PINS in changes else 0
            manifest = 1 if MANIFEST in changes else 0
            ok = not findings and lines[-1] == (
                f"BE_MVP_LICENSES: PASS identifiers={1 + external + manifest}"
                f" files=5 texts={1 + external + manifest} source=walk "
                f"external={external} manifest={manifest}")
        else:
            ok = any(expected in f for f in findings)
        print(f"{'PASS' if ok else 'FAIL'} {name}")
        if not ok:
            failed += 1
            for line in lines:
                print(f"  | {line}")
    # The expression parser alone.
    parsed = identifiers_in("(GPL-2.0-only WITH Linux-syscall-note) OR MIT")
    ok = parsed == ["GPL-2.0-only", "MIT"]
    print(f"{'PASS' if ok else 'FAIL'} WITH drops the exception: {parsed}")
    failed += 0 if ok else 1
    ok = identifiers_in("GPL-3.0-only. The text") == []
    print(f"{'PASS' if ok else 'FAIL'} a sentence is not an expression")
    failed += 0 if ok else 1
    print(f"BE_MVP_LICENSES_SELF_TEST: {'FAIL' if failed else 'PASS'} "
          f"cases={len(cases) + 2}")
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("command", nargs="?", default="check")
    parser.add_argument("--root", default=None)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch", default=None)
    args = parser.parse_args()
    if args.self_test:
        if not args.scratch:
            print("--self-test needs --scratch DIR", file=sys.stderr)
            return 2
        return self_test(args.scratch)
    if args.command != "check":
        print(__doc__.strip(), file=sys.stderr)
        return 2
    root = args.root or pathlib.Path(__file__).resolve().parents[2]
    lines, findings = check(root)
    print("\n".join(lines))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
