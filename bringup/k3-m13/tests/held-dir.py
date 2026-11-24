#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""
held-dir.py check DIR ROOT
held-dir.py --self-test --scratch DIR

The third probe image's held directory (mvp/tools.mk, k3-m13-held;
planning/mvp-m13-3-review-point.md, section 4), checked before anything is
made: DIR is absolute, a directory and not a link, this account's, mode
0700, outside the checkout ROOT, and holds table-3.S and expect-3.txt as
regular files. check prints BE_K3_M13_HELD_DIR: PASS, or FAIL with the
rule, never DIR, and exits 0 or 1. --self-test makes --scratch (mode 0700;
refused if it exists) and its cases there, against a stand-in checkout,
and requires each refusal for its own reason; "this account's" has no case
(another account's directory cannot be made).

Trust: test-only; check reads DIR's metadata alone.
"""

import argparse
import os
import pathlib
import stat
import sys

FILES = ("table-3.S", "expect-3.txt")


def problem(directory, root):
    path = pathlib.Path(directory)
    if not path.is_absolute():
        return "not absolute"
    try:
        info = os.lstat(path)
    except OSError:
        return "not there"
    if not stat.S_ISDIR(info.st_mode):
        return "not a directory"
    if info.st_uid != os.geteuid():
        return "not this account's"
    if stat.S_IMODE(info.st_mode) != 0o700:
        return "not mode 0700"
    real, top = path.resolve(), pathlib.Path(root).resolve()
    if real == top or top in real.parents:
        return "inside the checkout"
    for name in FILES:
        try:
            if not stat.S_ISREG(os.lstat(path / name).st_mode):
                return f"{name} not a regular file"
        except OSError:
            return f"no {name}"
    return None


def self_test(scratch):
    base = pathlib.Path(scratch)
    base.mkdir(mode=0o700)
    root = base / "checkout"
    root.mkdir(mode=0o700)

    def held(name, mode=0o700, files=FILES, parent=base):
        path = parent / name
        path.mkdir(mode=mode)
        path.chmod(mode)
        for file in files:
            (path / file).write_text("x\n")
        return path
    (base / "link").symlink_to(held("good"))
    linked = held("table-link", files=FILES[1:])
    (linked / FILES[0]).symlink_to(base / "good" / FILES[0])
    cases = [("good", base / "good", None),
             ("relative", "good", "not absolute"),
             ("missing", base / "none", "not there"),
             ("a link", base / "link", "not a directory"),
             ("mode 0755", held("open", 0o755), "not mode 0700"),
             ("inside the checkout", held("inside", parent=root),
              "inside the checkout"),
             ("no table", held("no-table", files=FILES[1:]),
              "no table-3.S"),
             ("no list", held("no-list", files=FILES[:1]),
              "no expect-3.txt"),
             ("the table a link", linked, "table-3.S not a regular file")]
    failed = [name for name, path, want in cases
              if problem(str(path), root) != want]
    for name in failed:
        print(f"finding: self-test {name}")
    print(f"BE_K3_M13_HELD_DIR_SELF_TEST: {'FAIL' if failed else 'PASS'} "
          f"cases={len(cases)}")
    return 1 if failed else 0


def main(argv):
    parser = argparse.ArgumentParser(prog="held-dir.py")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch")
    parser.add_argument("words", nargs="*")
    args = parser.parse_args(argv)
    if args.self_test:
        if not args.scratch or args.words:
            parser.error("--self-test takes --scratch DIR alone")
        return self_test(args.scratch)
    if len(args.words) != 3 or args.words[0] != "check":
        parser.error("check DIR ROOT")
    found = problem(args.words[1], args.words[2])
    print("BE_K3_M13_HELD_DIR: PASS" if found is None else
          f"BE_K3_M13_HELD_DIR: FAIL K3_M13_HELD is {found}")
    return 0 if found is None else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
