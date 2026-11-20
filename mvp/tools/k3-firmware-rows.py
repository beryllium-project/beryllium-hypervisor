#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""M11-B's firmware rows: the board's firmware build as QEMU's rows boot
it, the rows' expectations, and the tree without reset devices.

  k3-firmware-rows.py board --pins FILE [--name NAME] --build DIR
                            --out DIR [--like ELF --nm NM]
  k3-firmware-rows.py expect --source DIR --out DIR
  k3-firmware-rows.py tree-check --base FILE --no-reset FILE --dtc DTC
                                 --scratch DIR
  k3-firmware-rows.py --self-test --scratch DIR --base FILE
                      --no-reset FILE --dtc DTC

Purpose: planning/mvp-m11-board-addendum.md, B-2's two tests, run as
rows of tests/run-qemu.sh (mvp/k3/firmware.mk).

board requires the build's fw_dynamic.bin (DIR/platform/generic/
firmware/) to have the SHA-256 and the size of the pins file's one
`firmware NAME` line (NAME board by default), and copies it, its ELF,
DIR's FIRMWARE-BUILD.txt, and the tree built in (DIR/fdt/board.dtb, as
board.dtb), if any, into OUT, a new directory. With --like, the build's
_fw_start, _fw_rw_start, and _fw_end (nm's) must be ELF's: a tree built
in that moved the firmware's regions is refused.

expect derives the rows' expectations from the generated ones under
--source (tools/gen-scenario.py's, which it never changes): k3-halt
from two-guests, under the board's firmware, whose one reset device
halts; k3-reset-absent from two-guests, with firmware-version's failure
at the monitor's first check, under a firmware with no reset device;
k3-halt-fallback from two-guests-off, under the board's firmware where
QEMU's own reset devices are present; and the sittings' two forms, each
under a build with its tree built in and QEMU's own tree handed over:
k3-first from two-guests-off, with a top-level halt mark (its firmware
halts with the boundary off), and k3-second from k3-halt, its boundary's
tree built in. Each is for GCC and QEMU alone. Sources of another form
are refused. OUT, a new directory,
gets expect/NAME.json and, beside expect/, the scenario header that
tools/gen-reference.py reads there.

tree-check compiles both trees with the lock's dtc and decompiles them
sorted: the tree without reset devices must be the plain base with its
poweroff and reboot nodes removed, its console named intel,xscale-uart,
then ns16550a, as tools/k3-recipe.py's step 4 names the board's, and
nothing else changed.

Trust: it reads its inputs, runs dtc on the two trees, and writes only
OUT or its scratch. Scope: M11-B, B-2's tests. Exit 0 pass, 1 fail or
refused, 2 usage.
"""

import argparse
import copy
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys

TAG = "BE_MVP_K3_FIRMWARE"
PIN = re.compile(r"firmware ([\w.-]+) sha256=([0-9a-f]{64}) "
                 r"bytes=([1-9][0-9]*)")
FIRMWARE = pathlib.PurePosixPath("platform/generic/firmware")
SOURCES = ("two-guests", "firmware-version", "two-guests-off")
ROWS = ("k3-halt", "k3-reset-absent", "k3-halt-fallback", "k3-first",
        "k3-second")
LAYOUT = ("_fw_start", "_fw_rw_start", "_fw_end")
NM_LINE = re.compile(r"([0-9a-f]+) [A-Za-z] (\S+)")
REMOVED = ("poweroff", "reboot")
# QEMU's console under soc: its node, its name in the base, and its names
# in the tree without reset devices.
CONSOLE = ("\t\tserial@10000000 {", '\t\t\tcompatible = "ns16550a";',
           '\t\t\tcompatible = "intel,xscale-uart", "ns16550a";')
CONFINED = {"0": "confined", "1": "confined", "2": "confined"}
CHANGES = {
    "k3-halt": "the board's firmware configuration (the candidate's with "
    "CONFIG_SBI_SYSTEM_RESET_HALT), built without a tree, on QEMU's "
    "k3-like tree without its reset devices: the halt device is the one "
    "reset device, so the run ends in M-mode's halt after the commit "
    "records (planning/mvp-m11-board-addendum.md, B-2)",
    "k3-reset-absent": "the candidate's pinned firmware on the same tree: "
    "the board's configuration is the candidate's with the one option "
    "CONFIG_SBI_SYSTEM_RESET_HALT, so this firmware is that configuration "
    "without the addition; it finds no reset device and offers no SRST, "
    "and the monitor's first check fails (B-2)",
    "k3-halt-fallback": "the board's firmware configuration with "
    "two-guests-off under QEMU's own tree, whose syscon reset devices "
    "the base prefers to the halt device: the run ends with QEMU's "
    "shutdown (B-2)",
    "k3-first": "the first sitting's form: the board's firmware "
    "configuration with the tree without reset devices built in, no "
    "descriptor, and two-guests-off, under QEMU's own tree, which the "
    "firmware replaces with its own: the run ends in M-mode's halt after "
    "the monitor's last line (B-1 to B-3)",
    "k3-second": "the second sitting's form: the board's firmware "
    "configuration with k3-halt's tree built in, and two-guests, under "
    "QEMU's own tree, which the firmware replaces with its own: k3-halt's "
    "end, against that build's tables (B-1 to B-3)",
}


class Refused(Exception):
    """An input of another form than this tool accepts."""


def require(condition, message):
    if not condition:
        raise Refused(message)


def new_directory(path):
    """PATH made afresh: it must not exist, and its parent must."""
    path = pathlib.Path(path)
    require(not path.exists() and not path.is_symlink(), f"{path} exists")
    path.mkdir(mode=0o700)
    return path


def regular(path):
    require(path.is_file() and not path.is_symlink(),
            f"{path} is not a regular file")
    return path


def pin(pins, name):
    """The SHA-256 and size that the pins file's one line for NAME gives."""
    found = []
    for line in regular(pathlib.Path(pins)).read_text(
            encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        match = PIN.fullmatch(line)
        require(match is not None, f"{pins}: not a pin line: {line!r}")
        if match.group(1) == name:
            found.append((match.group(2), int(match.group(3))))
    require(len(found) == 1,
            f"{pins} pins firmware {name} {len(found)} times, not once")
    return found[0]


def layout(listing):
    """_fw_start, _fw_rw_start, and _fw_end, each defined once in nm's
    LISTING."""
    found = {}
    for line in listing.splitlines():
        match = NM_LINE.fullmatch(line.strip())
        if match and match.group(2) in LAYOUT:
            require(match.group(2) not in found,
                    f"{match.group(2)} is defined twice")
            found[match.group(2)] = int(match.group(1), 16)
    require(set(found) == set(LAYOUT), "the ELF does not define " +
            ", ".join(sorted(set(LAYOUT) - set(found))))
    return found


def same_layout(mine, like):
    """MINE's firmware regions, from nm's listing, are LIKE's."""
    mine, like = layout(mine), layout(like)
    require(mine == like, "the tree built in moves the firmware's regions: " +
            ", ".join(f"{name} 0x{mine[name]:x}, not 0x{like[name]:x}"
                      for name in LAYOUT if mine[name] != like[name]))


def listed(nm, elf):
    done = subprocess.run([nm, "--", str(elf)], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)
    require(done.returncode == 0, f"nm failed on {elf}")
    return done.stdout.decode("ascii", "replace")


def board(args):
    digest, size = pin(args.pins, args.name)
    build = pathlib.Path(args.build)
    binary = build / FIRMWARE / "fw_dynamic.bin"
    files = [regular(path) for path in (binary, binary.with_suffix(".elf"),
                                        build / "FIRMWARE-BUILD.txt")]
    tree = build / "fdt" / "board.dtb"
    if tree.exists() or tree.is_symlink():
        files.append(regular(tree))
    data = binary.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    require(actual == digest and len(data) == size,
            f"{binary} has SHA-256 {actual} and {len(data)} bytes, not "
            f"the pin's {digest} and {size}")
    if args.like:
        same_layout(listed(args.nm, files[1]), listed(args.nm, args.like))
    out = new_directory(args.out)
    for path in files:
        shutil.copyfile(path, out / path.name)
    print(f"{TAG}: PASS {args.name} sha256={digest} bytes={size}")


def load(path):
    try:
        value = json.loads(regular(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Refused(f"{path}: {error}") from error
    require(isinstance(value, dict), f"{path} is not an object")
    return value


def derived(source, image):
    value = copy.deepcopy(source)
    value.update(image=image, toolchains=["gcc"], where=["qemu"],
                 change=CHANGES[image])
    return value


def rows(pair, earlier, off):
    """The rows' expectations, from two-guests's, firmware-version's, and
    two-guests-off's."""
    boundary = pair.get("boundary")
    require(isinstance(boundary, dict), "two-guests declares no boundary")
    require(boundary.get("pair") == "two-guests",
            "two-guests's boundary pair is not two-guests")
    require(boundary.get("control_hart") == "confined" and
            boundary.get("harts") == CONFINED,
            "two-guests's harts are not all confined")
    require(boundary.get("record") is True,
            "two-guests's boundary has no commit record")
    require(not {"firmware", "reset", "tree"} & set(boundary),
            "two-guests's boundary already names its firmware, reset, or "
            "tree")
    require(pair.get("outcome") == {"pass": True}, "two-guests does not pass")
    log = earlier.get("log")
    require(earlier.get("outcome") == {"fail": "boot", "after": "none"} and
            isinstance(log, dict) and log.get("run") == "pre-measurement"
            and log.get("terminal") == "none",
            "firmware-version is not the failure at the first check")
    require("boundary" not in off and "halt" not in off and
            off.get("outcome") == {"pass": True},
            "two-guests-off is not a passing run without the boundary")
    halt = derived(pair, "k3-halt")
    halt["boundary"].update(firmware="board", reset="halt")
    absent = derived(pair, "k3-reset-absent")
    absent["boundary"].update(reset="absent", harts={
        "0": "boot", "1": "never-started", "2": "never-started"})
    absent["outcome"] = dict(earlier["outcome"])
    absent["log"].update(run=log["run"], terminal=log["terminal"])
    first = derived(off, "k3-first")
    first["halt"] = {"firmware": "board", "tree": "built-in"}
    second = derived(pair, "k3-second")
    second["boundary"].update(firmware="board", reset="halt",
                              tree="built-in")
    return halt, absent, derived(off, "k3-halt-fallback"), first, second


def expect(args):
    source = pathlib.Path(args.source)
    values = rows(*(load(source / "expect" / f"{name}.json")
                    for name in SOURCES))
    header = regular(source / "mvp-scenario.h")
    out = new_directory(args.out)
    (out / "expect").mkdir(mode=0o700)
    for value in values:
        (out / "expect" / f"{value['image']}.json").write_text(
            json.dumps(value, indent=1, sort_keys=True) + "\n",
            encoding="utf-8")
    shutil.copyfile(header, out / header.name)
    print(f"{TAG}: PASS expect images={','.join(ROWS)}")


def decompiled(dtc, source, scratch, name):
    """SOURCE compiled with its own directory on the include path, then
    decompiled with its nodes sorted."""
    source = pathlib.Path(source)
    dtb, dts = scratch / f"{name}.dtb", scratch / f"{name}.dts"
    for argv in ([dtc, "-q", "-I", "dts", "-O", "dtb", "-i",
                  str(source.parent), "-o", str(dtb), str(source)],
                 [dtc, "-q", "-s", "-I", "dtb", "-O", "dts", "-o", str(dts),
                  str(dtb)]):
        done = subprocess.run(argv, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=False)
        require(done.returncode == 0, f"dtc failed on {source}: " +
                done.stderr.decode("utf-8", "replace").strip())
    return dts.read_text(encoding="utf-8")


def top_nodes(text):
    """A decompiled tree's root children, each by name with its lines, and
    the root's other lines that hold anything."""
    lines, children, rest, index = text.splitlines(), {}, [], 0
    while index < len(lines):
        match = re.fullmatch(r"\t([^\s{}]+) \{", lines[index])
        if match:
            require("\t};" in lines[index:], f"node {match.group(1)} is "
                    "not closed")
            end = lines.index("\t};", index)
            require(match.group(1) not in children,
                    f"node {match.group(1)} twice")
            children[match.group(1)] = lines[index:end + 1]
            index = end + 1
            continue
        if lines[index].strip():
            rest.append(lines[index])
        index += 1
    return children, rest


def console(children):
    """The index, in soc's lines, of the compatible of QEMU's console."""
    soc = children.get("soc", [])
    require(CONSOLE[0] in soc, "the tree has no soc/serial@10000000")
    start = soc.index(CONSOLE[0])
    found = [index for index in range(start, soc.index("\t\t};", start))
             if soc[index].startswith("\t\t\tcompatible = ")]
    require(len(found) == 1, "the console has not one compatible")
    return found[0]


def tree_check(base, no_reset, dtc, scratch):
    """The number of root children that the tree without reset devices
    keeps, each the base's but for the console's names."""
    scratch = new_directory(scratch)
    whole, whole_rest = top_nodes(decompiled(dtc, base, scratch, "base"))
    cut, cut_rest = top_nodes(decompiled(dtc, no_reset, scratch, "no-reset"))
    for name in REMOVED:
        require(name in whole, f"the base has no {name} node")
        require(name not in cut,
                f"the tree without reset devices keeps {name}")
    lost = sorted(set(whole) - set(cut) - set(REMOVED))
    require(not lost, "the tree without reset devices also removes " +
            ", ".join(lost))
    added = sorted(set(cut) - set(whole))
    require(not added, "the tree without reset devices adds " +
            ", ".join(added))
    at, now = console(whole), console(cut)
    require(whole["soc"][at] == CONSOLE[1],
            "the base's console is not named ns16550a alone")
    require(cut["soc"][now] == CONSOLE[2], "the tree without reset devices "
            "does not name its console intel,xscale-uart, then ns16550a")
    whole["soc"][at] = CONSOLE[2]
    changed = sorted(name for name in cut if cut[name] != whole[name])
    require(not changed, "the tree without reset devices changes " +
            ", ".join(changed))
    require(cut_rest == whole_rest,
            "the tree without reset devices changes the root's properties")
    return len(cut)


def tree_command(args):
    kept = tree_check(args.base, args.no_reset, args.dtc, args.scratch)
    print(f"{TAG}: PASS tree-check removed={','.join(REMOVED)} kept={kept}")


def self_test(args):
    scratch = new_directory(args.scratch)
    passed = failed = 0

    def case(name, function, wanted=None):
        """FUNCTION passes, or, with WANTED, is refused with it."""
        nonlocal passed, failed
        try:
            function()
            ok, detail = wanted is None, "accepted"
        except Refused as error:
            ok, detail = wanted is not None and wanted in str(error), \
                str(error)
        passed, failed = passed + ok, failed + (not ok)
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")

    # board: a stand-in build and its pin.
    build = scratch / "build"
    (build / FIRMWARE).mkdir(parents=True)
    binary = build / FIRMWARE / "fw_dynamic.bin"
    binary.write_bytes(b"a firmware\n")
    binary.with_suffix(".elf").write_bytes(b"its ELF\n")
    (build / "FIRMWARE-BUILD.txt").write_text("binary=x\n", encoding="ascii")
    digest = hashlib.sha256(b"a firmware\n").hexdigest()
    good = f"firmware board sha256={digest} bytes=11"
    runs = iter(range(1000))

    def board_case(lines, out=None, remove=None, name="board"):
        pins = scratch / f"pins-{next(runs)}.txt"
        pins.write_text("# header\n" + "".join(f"{line}\n" for line in lines),
                        encoding="ascii")
        if remove:
            remove.rename(remove.with_name(remove.name + ".away"))
        target = out or scratch / f"out-{next(runs)}"
        try:
            board(argparse.Namespace(pins=pins, name=name, build=build,
                                     out=target, like=None, nm=None))
        finally:
            if remove:
                remove.with_name(remove.name + ".away").rename(remove)
        require((target / "fw_dynamic.bin").read_bytes() == b"a firmware\n",
                "the copy is not the build's")

    other = good.replace("firmware board", "firmware other")
    case("board: the build has its pin", lambda: board_case([other, good]))
    case("board: no pin line for board", lambda: board_case(
        [other]), "pins firmware board 0 times")
    case("board: two pin lines for board", lambda: board_case(
        [good, good]), "pins firmware board 2 times")
    case("board: another SHA-256", lambda: board_case(
        [good.replace(digest, "0" * 64)]), "not the pin's")
    case("board: another size", lambda: board_case(
        [good.replace("bytes=11", "bytes=12")]), "not the pin's")
    case("board: a line of another form", lambda: board_case(
        [good + " extra"]), "not a pin line")
    case("board: no ELF beside the binary", lambda: board_case(
        [good], remove=binary.with_suffix(".elf")),
         "fw_dynamic.elf is not a regular file")
    (scratch / "taken").mkdir()
    case("board: OUT exists", lambda: board_case(
        [good], out=scratch / "taken"), "taken exists")
    case("board: the pin of another name", lambda: board_case(
        [good, other.replace(digest, "0" * 64)], name="other"),
         "not the pin's")

    def with_tree():
        (build / "fdt").mkdir()
        (build / "fdt" / "board.dtb").write_bytes(b"a tree\n")
        try:
            board_case([good], out=scratch / "tree-out")
        finally:
            shutil.rmtree(build / "fdt")
        require((scratch / "tree-out" / "board.dtb").read_bytes() ==
                b"a tree\n", "the tree built in is not copied")

    case("board: the tree built in, copied", with_tree)
    listing = ("0000000000000000 T _fw_start\n"
               "0000000000040000 A _fw_rw_start\n"
               "0000000000047000 A _fw_end\n")
    for name, mine, wanted in (
            ("the regions unmoved", listing, None),
            ("_fw_rw_start moved", listing.replace("40000 A", "80000 A"),
             "_fw_rw_start 0x80000, not 0x40000"),
            ("_fw_end missing", listing.replace(" _fw_end", " _fw_tail"),
             "does not define _fw_end"),
            ("_fw_end twice", listing + "0000000000047000 A _fw_end\n",
             "_fw_end is defined twice")):
        case(f"board --like: {name}", lambda mine=mine: same_layout(
            mine, listing), wanted)

    # expect: stand-ins of the three generated expectations.
    pair = {"image": "two-guests", "toolchains": ["gcc", "clang"],
            "outcome": {"pass": True},
            "log": {"run": "complete", "terminal": "before-shutdown"},
            "boundary": {"pair": "two-guests", "control_hart": "confined",
                         "harts": dict(CONFINED), "record": True}}
    earlier = {"image": "firmware-version", "where": ["qemu"],
               "outcome": {"fail": "boot", "after": "none"},
               "log": {"run": "pre-measurement", "terminal": "none"}}
    off = {"image": "two-guests-off", "where": ["qemu"],
           "outcome": {"pass": True},
           "log": {"run": "complete", "terminal": "before-shutdown"}}

    def made():
        halt, absent, fallback, first, second = rows(pair, earlier, off)
        require(halt["boundary"] == dict(pair["boundary"], firmware="board",
                                         reset="halt"), "k3-halt's boundary")
        require(absent["boundary"]["harts"] == {
            "0": "boot", "1": "never-started", "2": "never-started"} and
            absent["boundary"]["reset"] == "absent" and
            "firmware" not in absent["boundary"], "k3-reset-absent's boundary")
        require(absent["outcome"] == earlier["outcome"] and
                absent["log"] == earlier["log"], "k3-reset-absent's failure")
        require("boundary" not in fallback and fallback["outcome"] ==
                {"pass": True}, "k3-halt-fallback's form")
        require("boundary" not in first and first["halt"] == {
            "firmware": "board", "tree": "built-in"} and
            first["outcome"] == {"pass": True}, "k3-first's form")
        require(second["boundary"] == dict(halt["boundary"],
                                           tree="built-in"),
                "k3-second's boundary")
        for value, name in zip((halt, absent, fallback, first, second),
                               ROWS):
            require(value["image"] == name and value["toolchains"] == ["gcc"]
                    and value["where"] == ["qemu"] and
                    value["change"] == CHANGES[name], f"{name}'s fields")
        require(pair["image"] == "two-guests" and "reset" not in
                pair["boundary"], "a source was changed")

    case("expect: the five rows", made)

    def spoilt(source, change):
        def run():
            values = {"pair": copy.deepcopy(pair),
                      "earlier": copy.deepcopy(earlier),
                      "off": copy.deepcopy(off)}
            change(values[source])
            rows(values["pair"], values["earlier"], values["off"])
        return run

    for name, source, change, wanted in (
            ("no boundary", "pair", lambda v: v.pop("boundary"),
             "declares no boundary"),
            ("another pair", "pair",
             lambda v: v["boundary"].update(pair="te-poc"),
             "pair is not two-guests"),
            ("a hart not confined", "pair",
             lambda v: v["boundary"]["harts"].update({"2": "started"}),
             "not all confined"),
            ("the control hart not confined", "pair",
             lambda v: v["boundary"].update(control_hart="boot"),
             "not all confined"),
            ("no record", "pair",
             lambda v: v["boundary"].update(record=False),
             "has no commit record"),
            ("a reset already named", "pair",
             lambda v: v["boundary"].update(reset="halt"),
             "already names"),
            ("a tree already named", "pair",
             lambda v: v["boundary"].update(tree="built-in"),
             "already names"),
            ("two-guests failing", "pair",
             lambda v: v.update(outcome={"fail": "boot", "after": "none"}),
             "two-guests does not pass"),
            ("another failure", "earlier",
             lambda v: v.update(outcome={"fail": "launch", "after": "none"}),
             "not the failure at the first check"),
            ("a measured failure", "earlier",
             lambda v: v["log"].update(run="complete"),
             "not the failure at the first check"),
            ("an off copy with a boundary", "off",
             lambda v: v.update(boundary={"pair": "two-guests"}),
             "not a passing run without the boundary"),
            ("an off copy with a halt mark", "off",
             lambda v: v.update(halt={"firmware": "board"}),
             "not a passing run without the boundary")):
        case(f"expect: {name}", spoilt(source, change), wanted)

    source = scratch / "gen"
    (source / "expect").mkdir(parents=True)
    for name, value in zip(SOURCES, (pair, earlier, off)):
        (source / "expect" / f"{name}.json").write_text(
            json.dumps(value), encoding="utf-8")

    def written():
        expect(argparse.Namespace(source=source, out=scratch / "rows"))
        names = sorted(path.name for path in
                       (scratch / "rows" / "expect").iterdir())
        require(names == sorted(f"{name}.json" for name in ROWS),
                "the rows' files")

    case("expect: no scenario header", written, "mvp-scenario.h")
    (source / "mvp-scenario.h").write_text("#define X 1\n", encoding="ascii")
    case("expect: the files, and the header beside them", written)

    # tree-check: the committed rule, and wrong forms of it beside a copy
    # of the base.
    trees = scratch / "trees"
    trees.mkdir()
    base = pathlib.Path(args.base)
    shutil.copyfile(base, trees / base.name)
    rule = pathlib.Path(args.no_reset).read_text(encoding="utf-8")
    deleted = "\t/delete-node/ poweroff;\n\t/delete-node/ reboot;\n"
    require(rule.count(deleted) == 1, "the rule's two deletions")
    names = '"intel,xscale-uart", "ns16550a"'
    named = "&{/soc/serial@10000000} {\n\tcompatible = " + names + ";\n};\n"
    require(rule.count(named) == 1, "the rule's console")
    count = iter(range(1000))

    def tree_case(text):
        def run():
            index = next(count)
            path = trees / f"rule-{index}.dts"
            path.write_text(text, encoding="utf-8")
            tree_check(trees / base.name, path, args.dtc,
                       scratch / f"tree-{index}")
        return run

    case("tree-check: the committed rule", tree_case(rule))
    for name, text, wanted in (
            ("reboot kept", rule.replace("\t/delete-node/ reboot;\n", ""),
             "keeps reboot"),
            ("a third node removed",
             rule.replace(deleted, deleted + "\t/delete-node/ chosen;\n"),
             "also removes chosen"),
            ("a node added",
             rule.replace(deleted, deleted + "\textra {\n\t};\n"),
             "adds extra"),
            ("another node changed",
             rule.replace(deleted, deleted + "\tchosen {\n"
                          "\t\tbootargs = \"x\";\n\t};\n"),
             "changes chosen"),
            ("a root property changed",
             rule.replace(deleted, "\tmodel = \"x\";\n" + deleted),
             "changes the root's properties"),
            ("the console named as QEMU's alone", rule.replace(named, ""),
             "does not name its console"),
            ("the console's two names swapped", rule.replace(
                names, '"ns16550a", "intel,xscale-uart"'),
             "does not name its console")):
        case(f"tree-check: {name}", tree_case(text), wanted)

    print(f"{TAG}_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
          f"cases={passed + failed}")
    return 0 if not failed else 1


def main(argv):
    parser = argparse.ArgumentParser(prog="k3-firmware-rows.py")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch")
    parser.add_argument("--base")
    parser.add_argument("--no-reset")
    parser.add_argument("--dtc")
    commands = parser.add_subparsers(dest="command")
    command = commands.add_parser("board")
    command.add_argument("--pins", required=True)
    command.add_argument("--name", default="board")
    command.add_argument("--build", required=True)
    command.add_argument("--out", required=True)
    command.add_argument("--like")
    command.add_argument("--nm")
    command = commands.add_parser("expect")
    command.add_argument("--source", required=True)
    command.add_argument("--out", required=True)
    command = commands.add_parser("tree-check")
    for name in ("--base", "--no-reset", "--dtc", "--scratch"):
        command.add_argument(name, required=True)
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            if args.command or not all((args.scratch, args.base,
                                        args.no_reset, args.dtc)):
                parser.error("--self-test takes --scratch, --base, "
                             "--no-reset, and --dtc alone")
            return self_test(args)
        if args.command is None:
            parser.error("a command, or --self-test")
        if args.command == "board" and (args.like is None) != (args.nm is
                                                                None):
            parser.error("board: --like and --nm go together")
        {"board": board, "expect": expect,
         "tree-check": tree_command}[args.command](args)
        return 0
    except (Refused, OSError) as error:
        print(f"{TAG}: FAIL {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
