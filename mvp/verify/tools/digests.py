#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""
digests.py --write [--record FILE] --target COMMIT
digests.py --check [--record FILE]
digests.py --list
digests.py --self-test [--scratch DIR]

Purpose: the pilot's "leaf unchanged" record (planning/mvp-m8-plan.md, D-7
item 3, D-2's re-proof rule, D-5; specification Revision 1, SHA-256
aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b at
93a8d136; the first freeze ade32fa6... at 004f31ae is stage 1's): for
Leaf A's and Leaf B's translation units, mvp/src/mvp-sbi.c and
mvp/src/mvp-ring.c, the SHA-256 of each and of every header each includes
transitively, found by following each #include under the compile's own
search path (the including file's directory first for a quoted name, then
the -I directories in order; the generated port's headers under
build/mvp/port, which `make -C mvp port` re-derives byte for byte, are
marked as equal to the tree's include/be/ file or as the port's rewrite);
the flags mvp/Makefile compiles them with (the recipe of its
mvp_target_object rule and the assignments it expands, verbatim, then the
expanded compile flags, the defines, and the -I set); the host tests'
flags (the equivalence oracle's); and the pins: the specification, the
verifier's closure, and its sources.txt. --write records them in
mvp/verify/target-digests.txt, refusing unless the tree's mvp/src and
mvp/Makefile equal COMMIT's (the target commit; git on the host);
--check recomputes them and compares the tree with the record, line by
line, printing BE_MVP_TARGET_DIGESTS: PASS files=N or the first
difference; --list prints the recomputed record. The specification's pin
hashes its text at the pinned commit, which git gives on the host; in the
verifier image, which has no git and no worktree's repository, the copy
of that text verify.sh exported on the host (MVP_VERIFIER_SPECIFICATION)
is hashed in its place.
Trust: the record is the target commit's reading; a later tree that
differs in a proved translation unit, a header, a flag, or a pin fails
--check until the re-proof rule has been run and the record re-written on
the responsible human's direction. The include walk follows every
#include, whatever conditional surrounds it, so it may list more headers
than one configuration reads, never fewer.
Exit status: 0 PASS; 1 FAIL (a difference, a missing file, a variable
assigned twice); 2 usage.
"""

import argparse
import hashlib
import importlib.util
import os
import pathlib
import re
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
TAG = "BE_MVP_TARGET_DIGESTS"
RECORD = REPO / "mvp" / "verify" / "target-digests.txt"
MAKEFILE = REPO / "mvp" / "Makefile"
UNITS = (("A", "mvp/src/mvp-sbi.c"), ("B", "mvp/src/mvp-ring.c"))
PINS = (("verifier_closure", "mvp/tools/verifier/closure.txt"),
        ("verifier_sources", "mvp/tools/verifier/sources.txt"))
# The specification is frozen by the SHA-256 of its text at its accepted
# commit (planning/mvp-m8-plan.md, D-6: "committed as its own exact
# commit, its SHA-256 recorded"), not of the working file, whose later
# acceptance and status edits do not move the frozen hash: the pin is the
# blob `git show COMMIT:PATH` hashes. Revision 1 (93a8d136, accepted
# 2026-11-03) re-froze it; the first freeze (004f31ae) is stage 1's.
SPECIFICATION_PATH = "planning/mvp-m8-specifications.md"
SPECIFICATION_COMMIT = "93a8d136d38547a8c581197315f7607b5eef7bad"
SPECIFICATION_SHA256 = ("aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf"
                        "8a484c69693b8b")
# Where git cannot give that blob (the verifier image has no git, and a
# worktree's repository is not mounted there), the file this variable
# names: the text verify.sh exported on the host with `git show
# COMMIT:PATH` before the suites. Its hash must equal the pin like the
# blob's, so a wrong file fails the check.
EXPORT = "MVP_VERIFIER_SPECIFICATION"
# The make variables the leaves' compile reads, and those it refers to.
VARIABLES = ("WARNINGS", "MARCH", "TARGET_FLAGS", "MVP_OPT", "HOST_FLAGS",
             "CROSS_COMPILE", "CC_gcc", "CC_clang", "HOST_CC_gcc",
             "HOST_CC_clang")
# Directory variables, tree-relative.
DIRECTORIES = {"MVP_DIR": "mvp", "REPO_ROOT": ".", "BUILD": "build/mvp",
               "PORT": "build/mvp/port", "GEN": "build/mvp/gen"}
RECIPE = "$$(CC_$(2)) $$(TARGET_FLAGS) $$(MVP_OPT) -c $$< -o $$@"
MARKER = ".digests-self-test"
HEADER = """\
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# The target digests of the pilot's leaves (planning/mvp-m8-plan.md, D-2,
# D-5, D-7 item 3), written by mvp/verify/tools/digests.py --write and
# checked by digests.py --check in ./mvp/mvp verify: the translation units,
# every header each includes, the compile's flags as mvp/Makefile states
# them, and the pins. A proved result holds for these bytes only; a merge
# that changes one of them without the re-proof rule run first is stop (i)
# (D-2). Re-written only on the responsible human's direction.
"""


class Refusal(Exception):
    """A file, a variable, or the record refused."""


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LEXER = load("token_equal", REPO / "mvp" / "verify" / "tools" /
             "token-equal.py")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def specification_sha256(root, git="git", environment=None):
    """The frozen specification's SHA-256: the text at its accepted commit
    (the blob `git show COMMIT:PATH`), which the working file's later
    acceptance edits do not move; without git or the commit, the text
    EXPORT names (the verifier image's case); else, a tree that is not a
    repository holding that commit (a synthetic tree), its file."""
    environment = os.environ if environment is None else environment
    try:
        done = subprocess.run([git, "-C", str(root), "show",
                               f"{SPECIFICATION_COMMIT}:{SPECIFICATION_PATH}"],
                              capture_output=True, check=False)
    except OSError:
        done = None
    if done is not None and done.returncode == 0:
        return hashlib.sha256(done.stdout).hexdigest()
    if environment.get(EXPORT):
        return sha256(pathlib.Path(environment[EXPORT]))
    return sha256(root / SPECIFICATION_PATH)


def relative(path, root):
    return str(path.resolve().relative_to(root.resolve()))


def logical_lines(text):
    """TEXT's lines with backslash continuations joined by one space."""
    lines, current = [], ""
    for line in text.split("\n"):
        if line.endswith("\\"):
            current += line[:-1].rstrip() + " "
            continue
        lines.append((current + line.lstrip() if current else line))
        current = ""
    return lines


def assignments(text):
    """{name: value} of VARIABLES' `NAME := value` lines; a variable among
    them assigned any other way, or twice, is refused."""
    found = {}
    for line in logical_lines(text):
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(:=|::=|=|\+=|\?=|!=)"
                         r"\s*(.*)$", line)
        if not match or match[1] not in VARIABLES:
            continue
        if match[2] != ":=" or match[1] in found:
            raise Refusal(f"mvp/Makefile assigns {match[1]} with {match[2]}"
                          f"{' again' if match[1] in found else ''}")
        found[match[1]] = re.sub(r"\s+", " ", match[3].strip())
    missing = sorted(set(VARIABLES) - set(found))
    if missing:
        raise Refusal(f"mvp/Makefile does not assign {', '.join(missing)}")
    return found


def expand(value, values, depth=0):
    """VALUE with $(NAME) of VALUES and DIRECTORIES expanded."""
    if depth > 8:
        raise Refusal("a make variable refers to itself")

    def one(match):
        name = match[1]
        if name in DIRECTORIES:
            return DIRECTORIES[name]
        if name in values:
            return expand(values[name], values, depth + 1)
        raise Refusal(f"$({name}) is not a variable digests.py expands")
    return re.sub(r"\$\(([A-Za-z_][A-Za-z0-9_]*)\)", one, value)


def flags(text):
    """[(key, value)] of the compile's flags, verbatim and expanded."""
    values = assignments(text)
    if f"\t{RECIPE}" not in text.split("define mvp_target_object", 1)[-1] \
            .split("endef", 1)[0]:
        raise Refusal("mvp/Makefile's mvp_target_object recipe is not "
                      f"`{RECIPE}`")
    target = expand("$(TARGET_FLAGS) $(MVP_OPT)", values).split()
    host = expand("$(HOST_FLAGS)", values).split()
    rows = [("recipe", RECIPE)]
    rows += [(f"make {name}", values[name]) for name in VARIABLES]
    rows.append(("compile_flags", " ".join(target)))
    rows.append(("defines", " ".join(f for f in target
                                     if f.startswith(("-D", "-U"))) or
                 "none"))
    rows.append(("include_dirs", " ".join(
        f[2:] for f in target if f.startswith("-I"))))
    rows.append(("host_test_flags", " ".join(host)))
    return rows, [f[2:] for f in target if f.startswith("-I")]


def includes(path):
    """[(quoted, name)] of PATH's #include directives."""
    found = []
    for token in LEXER.tokens_of(path.read_bytes().decode("latin-1")):
        if token.kind != "directive" or not token.text.startswith(
                "# include "):
            continue
        name = token.text[len("# include "):]
        match = re.fullmatch(r'"([^"]+)"|< ?(.+?) ?>', name)
        if not match:
            raise Refusal(f"{path.name}: #include {name} is not a header "
                          "name")
        found.append((match[1] is not None,
                      (match[1] or match[2]).replace(" ", "")))
    return found


def resolve_header(including, quoted, name, directories, root):
    """The file #include NAME in INCLUDING reads, or a refusal."""
    candidates = ([including.parent] if quoted else []) + \
        [root / directory for directory in directories]
    for directory in candidates:
        if (directory / name).is_file():
            return (directory / name).resolve()
    raise Refusal(f"{relative(including, root)}: {name} is in no -I "
                  "directory" + (" (build the port: make -C mvp port)" if
                                 name.startswith("be/") else ""))


def closure(unit, directories, root):
    """Every header UNIT includes, transitively, in the order found."""
    seen, order, queue = set(), [], [unit]
    while queue:
        current = queue.pop(0)
        for quoted, name in includes(current):
            header = resolve_header(current, quoted, name, directories, root)
            if header not in seen:
                seen.add(header)
                order.append(header)
                queue.append(header)
    return order


def compute(root=REPO, makefile=MAKEFILE):
    """The record's lines but its header, and the number of files."""
    rows, directories = flags(makefile.read_text(encoding="utf-8"))
    lines, users = [], {}
    for leaf, unit in UNITS:
        path = root / unit
        lines.append(f"unit leaf={leaf} file={unit} sha256={sha256(path)}")
        for header in closure(path, directories, root):
            users.setdefault(header, []).append(leaf)
    for header in sorted(users, key=lambda h: relative(h, root)):
        name = relative(header, root)
        where = ""
        if name.startswith("build/mvp/port/include/"):
            tree = root / "include" / name[len("build/mvp/port/include/"):]
            where = (f" port=equal-to:{relative(tree, root)}" if
                     tree.is_file() and sha256(tree) == sha256(header) else
                     " port=rewrite")
        lines.append(f"header file={name} sha256={sha256(header)} "
                     f"included_by={','.join(users[header])}{where}")
    lines += [f"flag {key}={value}" for key, value in rows]
    lines.append(f"pin specification file={SPECIFICATION_PATH} "
                 f"commit={SPECIFICATION_COMMIT} "
                 f"sha256={specification_sha256(root)}")
    for name, pin in PINS:
        lines.append(f"pin {name} file={pin} sha256={sha256(root / pin)}")
    count = len(UNITS) + len(users)
    lines.append(f"files={count}")
    return lines, count


def record_lines(path):
    return [line for line in path.read_text(encoding="utf-8").split("\n")
            if line and not line.startswith("#")]


def check(record, root=REPO, makefile=MAKEFILE):
    lines, count = compute(root, makefile)
    recorded = record_lines(record)
    for index in range(max(len(lines), len(recorded))):
        now = lines[index] if index < len(lines) else "(nothing)"
        then = recorded[index] if index < len(recorded) else "(nothing)"
        if now != then:
            print(f"{TAG}: FAIL the tree differs from {record.name}: "
                  f"recorded {then!r}, now {now!r}")
            return 1
    print(f"{TAG}: PASS files={count} record={relative(record, REPO)}")
    return 0


def write(record, target):
    status = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--quiet", target, "--",
         "mvp/src", "mvp/Makefile"], check=False)
    if status.returncode != 0:
        raise Refusal(f"the tree's mvp/src or mvp/Makefile differs from "
                      f"{target}, or {target} is not a commit")
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse",
                             "--verify", f"{target}^{{commit}}"],
                            capture_output=True, text=True, check=True)
    lines, count = compute()
    with open(record.with_suffix(".new"), "x", encoding="utf-8") as stream:
        stream.write(HEADER + f"# Target commit: {commit.stdout.strip()} "
                     "(its mvp/src and mvp/Makefile equal this tree's)\n" +
                     "\n".join(lines) + "\n")
    record.with_suffix(".new").replace(record)
    print(f"{TAG}: RECORDED files={count} record={relative(record, REPO)}")
    return 0


# ---------------------------------------------------------------- self-test
def self_test(scratch):
    scratch, label = scratch.resolve(), f"{TAG}_SELF_TEST"
    if REPO.is_relative_to(scratch) or (scratch.is_relative_to(REPO) and
                                        not scratch.is_relative_to(
                                            REPO / "build")):
        print(f"{label}: FAIL {scratch} would hold the source")
        return 1
    if scratch.is_dir() and any(scratch.iterdir()) and \
            not (scratch / MARKER).is_file():
        print(f"{label}: FAIL {scratch} is not empty and not its own")
        return 1
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True, mode=0o700)
    (scratch / MARKER).touch(exist_ok=False)
    results = []

    def case(name, passed, detail=""):
        results.append(bool(passed))
        print(f"{'ok  ' if passed else 'FAIL'} {name}"
              f"{'' if passed else ': ' + str(detail).strip()[-600:]}")

    # A synthetic tree in the layout the tool reads.
    tree = scratch / "tree"
    for directory in ("mvp/src", "build/mvp/port/include/be", "include/be",
                      "build/mvp/gen", "mvp/tools/verifier", "planning"):
        (tree / directory).mkdir(parents=True)
    files = {
        "mvp/src/mvp-sbi.c": '#include "mvp.h"\n#include "mvp-sbi.h"\n'
                             '/* #include "absent.h" */\nint a;\n',
        "mvp/src/mvp-ring.c": '#include "mvp-ring.h"\nint b;\n',
        "mvp/src/mvp.h": "#include <be/r4.h>\n#if 0\n#include \"mvp-sbi.h\""
                         "\n#endif\n",
        "mvp/src/mvp-sbi.h": "#include <be/types.h>\n",
        "mvp/src/mvp-ring.h": '#include "mvp.h"\n',
        "build/mvp/port/include/be/r4.h": "#include <be/types.h>\nr4\n",
        "build/mvp/port/include/be/types.h": "types\n",
        "include/be/r4.h": "#include <be/types.h>\nr4 in the tree\n",
        "include/be/types.h": "types\n",
        "mvp/tools/verifier/closure.txt": "closure\n",
        "mvp/tools/verifier/sources.txt": "sources\n",
        "planning/mvp-m8-specifications.md": "specification\n"}
    for name, text in files.items():
        (tree / name).write_text(text, encoding="utf-8")
    makefile = tree / "mvp" / "Makefile"
    makefile_text = MAKEFILE.read_text(encoding="utf-8")
    makefile.write_text(makefile_text, encoding="utf-8")
    record = scratch / "record.txt"
    try:
        lines, count = compute(tree, makefile)
        record.write_text(HEADER + "\n".join(lines) + "\n", encoding="utf-8")
    except Refusal as why:
        lines, count = [], 0
        case("the synthetic tree computes", False, why)
    headers = [line.split()[1] for line in lines if line.startswith(
        "header ")]
    case("the include walk", headers == [
        "file=build/mvp/port/include/be/r4.h",
        "file=build/mvp/port/include/be/types.h", "file=mvp/src/mvp-ring.h",
        "file=mvp/src/mvp-sbi.h", "file=mvp/src/mvp.h"] and count == 7,
         (headers, count))
    case("a port header equal to the tree's, and a rewrite", any(
        "be/types.h" in line and "port=equal-to:include/be/types.h" in line
        for line in lines) and any("be/r4.h" in line and "port=rewrite" in
                                   line for line in lines), lines)
    case("the units' users", any(
        line.startswith("header file=mvp/src/mvp.h") and
        "included_by=A,B" in line for line in lines), lines)
    case("the flags as the Makefile states them", any(
        line.startswith("flag include_dirs=build/mvp/port/include "
                        "build/mvp/port/arch/riscv/be mvp/src build/mvp/gen")
        for line in lines) and "flag defines=none" in lines and any(
            line.startswith("flag compile_flags=-std=gnu11 ") and
            line.endswith(" -Os") for line in lines), lines)

    def checked(change=None, path=None):
        if change:
            target = tree / path
            saved = target.read_bytes()
            target.write_bytes(change(saved))
        try:
            done = subprocess.run(
                [sys.executable, "-I", "-B", "-c",
                 "import sys, pathlib, importlib.util; "
                 f"spec = importlib.util.spec_from_file_location('d', "
                 f"{str(pathlib.Path(__file__).resolve())!r}); "
                 "m = importlib.util.module_from_spec(spec); "
                 "spec.loader.exec_module(m); "
                 f"sys.exit(m.check(pathlib.Path({str(record)!r}), "
                 f"pathlib.Path({str(tree)!r}), "
                 f"pathlib.Path({str(makefile)!r})))"],
                capture_output=True, text=True, check=False)
            return done.returncode, done.stdout + done.stderr
        finally:
            if change:
                target.write_bytes(saved)
    code, out = checked()
    case("the tree equals its record", code == 0 and out.startswith(
        f"{TAG}: PASS files=7"), out)
    for name, path, change, wanted in (
            ("a changed unit", "mvp/src/mvp-ring.c",
             lambda b: b + b"/* a comment */\n", "unit leaf=B"),
            ("a changed header", "mvp/src/mvp-sbi.h",
             lambda b: b.replace(b"types", b"r4"), "header file="),
            ("a changed port header", "build/mvp/port/include/be/types.h",
             lambda b: b + b"x\n", "header file=build/mvp/port/include/be/"
             "types.h"),
            ("a new include", "mvp/src/mvp-ring.h",
             lambda b: b + b'#include "mvp-sbi.h"\n', "header file="),
            ("a changed flag", "mvp/Makefile",
             lambda b: b.replace(b"MVP_OPT := -Os", b"MVP_OPT := -O2"),
             "flag make MVP_OPT"),
            ("a define added to the recipe", "mvp/Makefile",
             lambda b: b.replace(RECIPE.encode(), RECIPE.replace(
                 "$$(MVP_OPT)", "$$(MVP_OPT) -DX").encode()),
             "mvp_target_object recipe"),
            ("a variable assigned twice", "mvp/Makefile",
             lambda b: b + b"\nMVP_OPT := -O0\n", "assigns MVP_OPT"),
            ("a changed pin", "mvp/tools/verifier/closure.txt",
             lambda b: b + b"x\n", "pin verifier_closure"),
            ("a header in no -I directory", "mvp/src/mvp.h",
             lambda b: b + b'#include "absent.h"\n', "absent.h is in no"),
            ("the port not built", "build/mvp/port/include/be/r4.h",
             None, "make -C mvp port")):
        if change is None:
            moved = tree / path
            moved.rename(moved.with_suffix(".moved"))
            code, out = checked()
            moved.with_suffix(".moved").rename(moved)
        else:
            code, out = checked(change, path)
        case(name, code == 1 and wanted in out, out)
    code, out = checked()
    case("the tree restored equals its record", code == 0, out)
    # The specification's text without git: the export, else the file.
    export = scratch / "exported.md"
    export.write_bytes(b"the accepted text\n")
    absent = str(scratch / "no-git")
    case("without git, the exported text is hashed", specification_sha256(
        tree, absent, {EXPORT: str(export)}) == hashlib.sha256(
            b"the accepted text\n").hexdigest())
    case("without git or an export, the tree's file is hashed",
         specification_sha256(tree, absent, {}) == sha256(
             tree / SPECIFICATION_PATH))
    if all(results):
        shutil.rmtree(scratch)
    print(f"{label}: {'PASS' if all(results) else 'FAIL'} "
          f"cases={len(results)}"
          f"{'' if all(results) else f' failed={results.count(False)}'}")
    return 0 if all(results) else 1


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--list", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    parser.add_argument("--record", type=pathlib.Path, default=RECORD)
    parser.add_argument("--target")
    parser.add_argument("--scratch", type=pathlib.Path)
    args = parser.parse_args(argv[1:])
    if args.self_test:
        return self_test(args.scratch or REPO / "build/mvp/tmp/"
                         "digests-self-test")
    if bool(args.target) != args.write or args.scratch:
        parser.error("--write needs --target COMMIT; --scratch is the "
                     "self-test's")
    try:
        if args.write:
            return write(args.record.resolve(), args.target)
        if args.check:
            return check(args.record.resolve())
        lines, _ = compute()
        print("\n".join(lines))
        return 0
    except (OSError, Refusal, subprocess.CalledProcessError,
            LEXER.Refusal) as why:
        print(f"{TAG}: FAIL {why}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
