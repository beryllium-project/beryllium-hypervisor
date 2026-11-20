#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""M11-B's board images and records (planning/mvp-m11-board-addendum.md,
B-1, B-10, B-11; mvp/k3/breach.mk, tree.mk).

  only-table --nm NM --base HEX --board DIR --candidate DIR
  banner --image NAME --dtb DTB --firmware-elf ELF --nm NM --readelf R
         --console LOG
  holds-tree --nm NM --build DIR --tree DTB
  board --build BUILD --platform F --extensions-on L --extensions-off L
        --shutdown NAME --image NAME:SITTING:STAGED:BOARD:EXPECT:REF ...
  --self-test --scratch DIR

only-table: a board hostile-monitor image (DIR's be-mvp.elf, be-mvp.bin,
be-mvp-boot.img) is the candidate's but in its table: the table at the
same address and of the same size in both ELFs, the flat images equal
outside it and not inside it, and the boot image the candidate's with its
flat image, found once there, replaced.

banner: the k3-like platform's root OpenSBI domain's regions, as
tools/partition-backend.py writes them (banner(), sorted_regions(), its
device rows marked MMIO, as the firmware marks a device's and the board's
rows are), equal in number, order, and text to the Domain0 RegionNN values
of a run's banner; then one mark, one address, and two rows swapped in the
banner, each refused.

holds-tree: a gate firmware build (firmware/build.sh's) whose record
names the tree's SHA-256 as fdt_sha256, and whose fw_dynamic.bin holds the
tree's bytes at its ELF's fw_fdt_bin.

board: each image's board.json under k3/gate/images/IMAGE/, every path in
it from BUILD (the form that tests/check-capture.py, tools/k3-card.py, and
tools/k3-sitting.py read), its parts bound to each other (the check
record's tree, tables, root file, and identity; the root file's
firmware); then each image's firmware announced, and the gate's step line.

It shares tools/partition-backend.py's FDT reader and helpers, loaded as a
module. Exit 0 pass, 1 fail or refused, 2 usage.
"""

import argparse
import dataclasses
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TABLE, SCHEMA = "be_mvp_breach_attempts", "be-mvp-k3-board-v1"
REGION = re.compile(r"Domain0 Region(\d\d) +: (.*)")
# The staged name: tools/k3-env.sh's image form, GCC's.
STAGED = re.compile(r"be-mvp-[a-z0-9]+(?:-[a-z0-9]+)*-gcc\.img")
ROLES = {0: "control", 1: "vs-domain", 2: "vs-domain"}


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BACKEND = load("partition_backend", "partition-backend.py")
Refused, require = BACKEND.Refused, BACKEND.require


def listed(nm, elf, names):
    """{name: (address, size)} of each of NAMES, defined once in ELF."""
    result = subprocess.run([str(nm), "-S", str(elf)], capture_output=True,
                            text=True, check=False)
    require(result.returncode == 0, f"nm -S failed on {elf}")
    found = {}
    for fields in map(str.split, result.stdout.splitlines()):
        if len(fields) in (3, 4) and fields[-1] in names:
            require(fields[-1] not in found, f"{elf} has two {fields[-1]}")
            found[fields[-1]] = (int(fields[0], 16), int(
                fields[1], 16) if len(fields) == 4 else 0)
    require(set(found) == set(names), f"{elf} does not define "
            f"{sorted(set(names) - set(found))}")
    return found


# ------------------------------------------------------------ only-table
def only_table(tables, flats, boots, base):
    """TABLES, FLATS, BOOTS: the table's (address, size), the flat image,
    and the boot image, the board's then the candidate's. Returns the
    bytes changed and the flat image's offset in the boot image."""
    require(tables[0] == tables[1], f"the table is {tables[0]} in the "
            f"board's ELF and {tables[1]} in the candidate's")
    (at, size), (board, candidate) = tables[0], flats
    low, high = at - base, at - base + size
    require(len(board) == len(candidate) and 0 <= low < high <= len(board),
            "the flat images differ in size, or the table is outside them")
    require(board[:low] == candidate[:low] and board[high:] ==
            candidate[high:], "the flat images differ outside the table")
    changed = sum(a != b for a, b in zip(board[low:high],
                                         candidate[low:high]))
    require(changed, "the board's table is the candidate's")
    where = boots[1].find(candidate)
    require(where >= 0 and boots[1].find(candidate, where + 1) < 0,
            "the candidate's flat image is not once in its boot image")
    require(boots[0] == boots[1][:where] + board +
            boots[1][where + len(candidate):],
            "the boot images differ outside the flat image")
    return changed, where


def only_table_files(args):
    tables, flats, boots = [], [], []
    for directory in (args.board, args.candidate):
        tables.append(listed(args.nm, directory / "be-mvp.elf",
                             (TABLE,))[TABLE])
        flats.append((directory / "be-mvp.bin").read_bytes())
        boots.append((directory / "be-mvp-boot.img").read_bytes())
    changed, where = only_table(tables, flats, boots, int(args.base, 16))
    return [f"BE_MVP_K3_BREACH_IMAGE: PASS image={args.board.name} "
            f"candidate={args.candidate.name} table=0x{tables[0][0]:x}+"
            f"0x{tables[0][1]:x} changed={changed} offset=0x{where:x}"]


# ---------------------------------------------------------------- banner
def model(rows):
    """ROWS (the backend's platform()) as the banner prints them."""
    rows = [row if row.firmware or row.order == 64 else
            dataclasses.replace(row, mmio=True) for row in rows]
    return [BACKEND.banner(row) for row in BACKEND.sorted_regions(rows)]


def printed(text):
    """The Domain0 RegionNN values of a console's banner, in order."""
    values = []
    for line in text.replace("\r", "").split("\n"):
        match = REGION.fullmatch(line)
        if match:
            require(int(match.group(1)) == len(values),
                    f"Domain0 Region{match.group(1)} is out of order")
            values.append(match.group(2))
    require(values, "the console prints no Domain0 region")
    return values


def compare(made, shown):
    require(len(made) == len(shown), f"the model has {len(made)} root "
            f"regions, the banner {len(shown)}")
    for index, (left, right) in enumerate(zip(made, shown)):
        require(left == right, f"Region{index:02d}: the model's {left!r}, "
                f"the banner's {right!r}")


def mutations(shown):
    """SHOWN with one mark, one address, and two rows changed."""
    marked = next(at for at, value in enumerate(shown) if "(I," in value)
    first, digit = shown[0], shown[0].index("0x") + 10
    return {"one mark": shown[:marked] + [shown[marked].replace(
        "(I,", "(", 1)] + shown[marked + 1:],
            "one address": [first[:digit] + "98"[first[digit] == "9"] +
                            first[digit + 1:]] + shown[1:],
            "two rows swapped": shown[1::-1] + shown[2:]}


def banner_check(made, shown, image):
    compare(made, shown)
    for name, changed in mutations(shown).items():
        try:
            compare(made, changed)
        except Refused:
            continue
        raise Refused(f"the banner with {name} changed is admitted")
    return [f"BE_MVP_K3_BANNER: PASS image={image} regions={len(made)} "
            f"mutations=3"]


def banner_files(args):
    rows = BACKEND.platform(BACKEND.parse_fdt(args.dtb.read_bytes()),
                            BACKEND.firmware_symbols(
                                args.firmware_elf, args.nm, args.readelf))
    return banner_check(model(rows), printed(args.console.read_bytes(
    ).decode("utf-8", "replace")), args.image)


# ------------------------------------------------------------ holds-tree
def holds_tree(record, binary, at, tree):
    digest = hashlib.sha256(tree).hexdigest()
    require(f"fdt_sha256={digest}" in record.splitlines(),
            "the build's record does not name the tree's SHA-256")
    require(binary[at:at + len(tree)] == tree,
            "the binary does not hold the tree at fw_fdt_bin")
    return [f"BE_MVP_K3_TREE_BUILT_IN: PASS fdt_sha256={digest} "
            f"at=0x{at:x} bytes={len(tree)}"]


def holds_tree_files(args):
    firmware = args.build / "platform" / "generic" / "firmware"
    found = listed(args.nm, firmware / "fw_dynamic.elf",
                   ("_fw_start", "fw_fdt_bin"))
    return holds_tree((args.build / "FIRMWARE-BUILD.txt").read_text(
        encoding="ascii"), (firmware / "fw_dynamic.bin").read_bytes(),
                      found["fw_fdt_bin"][0] - found["_fw_start"][0],
                      args.tree.read_bytes())


# ----------------------------------------------------------------- board
def entry(build, relative):
    """{file, sha256} of BUILD/RELATIVE, RELATIVE a plain path under it."""
    path = pathlib.PurePosixPath(relative)
    require(not path.is_absolute() and ".." not in path.parts and
            (build / path).is_file(), f"{relative} is not a file under "
            f"the build")
    return {"file": str(path), "sha256": BACKEND.sha(build / path)}


def relative(build, path):
    path = pathlib.Path(path)
    require(path.is_relative_to(build), f"{path} is not under {build}")
    return str(path.relative_to(build))


def board(build, platform, spec, extensions, shutdown):
    """One image's board.json, from SPEC's parts and the gate's outputs."""
    image, sitting, staged, board_image, expect, reference = spec
    here = f"k3/gate/images/{image}"
    value = BACKEND.board_facts(platform)
    expectation = json.loads((build / expect).read_bytes())
    boundary = expectation.get("boundary")
    require(sitting in ("first", "second") and STAGED.fullmatch(staged) and
            expectation.get("image") == image and (boundary is None or
                                                   isinstance(boundary,
                                                              dict)),
            f"{image}: its sitting, staged name, or expectation")
    files = {key: entry(build, f"{here}/{name}") for key, name in (
        ("tree", f"{image}.dtb"), ("root", f"{image}-root.json"),
        ("check", f"{image}-check.json"),
        ("tables", f"{image}-pmp.json" if boundary else None))
        if name}
    check = json.loads((build / files["check"]["file"]).read_bytes())
    root = json.loads((build / files["root"]["file"]).read_bytes())
    elf = entry(build, f"{here}/fw_dynamic.elf")
    require(check.get("dtb_sha256") == files["tree"]["sha256"] and
            check.get("root_sha256") == files["root"]["sha256"] and
            root.get("firmware_sha256") == elf["sha256"] and
            check.get("image") == root.get("image") == image and
            check.get("boundary") == ("on" if boundary else "off"),
            f"{image}: the check record, root file, and firmware differ")
    authority, digest = None, None
    if boundary:
        authority = entry(build, f"gen/partition/"
                          f"{expectation['scenario']}/authority-report.json")
        rows = [row["identity"] for row in json.loads((
            build / authority["file"]).read_bytes())["descriptors"]
                if row["image"] == boundary.get("pair")]
        require(len(rows) == 1 and check.get("identity") == rows[0] and
                check.get("tables_sha256") == files["tables"]["sha256"],
                f"{image}: the pair's identity or tables differ")
        digest = rows[0] if boundary.get("record") else None
    fdt = BACKEND.parse_fdt((build / files["tree"]["file"]).read_bytes())
    harts = BACKEND.harts_by_reg(fdt, value["harts"]["count"])
    binary = entry(build, f"{here}/fw_dynamic.bin")
    load_at = value["firmware"]["load"]
    standard, experimental = extensions[bool(boundary)].split(" ")
    return {
        "schema": SCHEMA, "image": image, "sitting": sitting,
        "toolchain": "gcc", "boundary": "on" if boundary else "off",
        "digest": digest, "staged_name": staged,
        "board_image": entry(build, board_image),
        "expectation": entry(build, expect),
        "reference": entry(build, reference) if reference else None,
        "tables": files.get("tables"), "partition_authority": authority,
        "tree": files["tree"], "root": files["root"],
        "check": files["check"],
        "firmware": dict(binary, bytes=(build / binary["file"]).stat(
        ).st_size, load=load_at, entry=load_at, elf=elf),
        "sbi_version": "3.0",
        "sbi_extensions": {"standard": standard,
                           "experimental": experimental},
        "reset_device": {"reboot": "---", "shutdown": shutdown},
        "platform_name": BACKEND.prop(fdt, "/", "model").rstrip(
            b"\0").decode("ascii"),
        "product_name": value["product"]["value"],
        "root_regions": root["regions"],
        "harts": [{"hartid": hart, "role": ROLES.get(hart, "parked")}
                  for path in fdt.order for hart, node in harts.items()
                  if node == path]}


def board_files(args):
    build = args.build.resolve()
    lines, made = [], []
    for spec in args.image:
        parts = spec.split(":")
        require(len(parts) == 6, f"--image {spec!r} is not NAME:SITTING:"
                f"STAGED:BOARD:EXPECT:REFERENCE")
        parts[3:] = [relative(build, part) if part else "" for part in
                     parts[3:]]
        made.append(board(build, args.platform, parts,
                          (args.extensions_off, args.extensions_on),
                          args.shutdown))
    for value in made:
        BACKEND.write_new(build / "k3" / "gate" / "images" /
                          value["image"] / "board.json", (json.dumps(
                              value, indent=1, sort_keys=True) +
                              "\n").encode())
    for value in made:
        firmware = value["firmware"]
        lines.append(f"BE_MVP_K3_FIRMWARE: PASS image={value['image']} "
                     f"sitting={value['sitting']} file={firmware['file']} "
                     f"sha256={firmware['sha256']} "
                     f"bytes={firmware['bytes']}")
    return lines + [f"BE_MVP_K3_GATE[k3-gate-board]: PASS "
                    f"images={len(made)}"]


# ------------------------------------------------------------- self-test
def self_test(scratch, dtc):
    """Each rule on stand-ins (every value made up): its pass, and each
    defect refused by its own reason."""
    shutil.rmtree(scratch, ignore_errors=True)
    results = []

    def case(name, call, want=None):
        try:
            call()
            ok, detail = want is None, "passes"
        except (Refused, KeyError, ValueError, OSError) as error:
            ok, detail = want is not None and want in str(error), str(error)
        results.append(ok)
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")

    flat = bytes(64) + b"T" * 16 + bytes(64)
    board_flat = flat[:64] + b"t" + flat[65:]
    boot, early = b"shim" + flat + b"guest", b"x" + board_flat[1:]

    def table(tables=((0x1040, 16),) * 2, flats=(board_flat, flat),
              boots=(b"shim" + board_flat + b"guest", boot)):
        return only_table(tables, flats, boots, 0x1000)
    case("only-table: the board's table alone differs", table)
    for name, change, want in (
            ("the table elsewhere", {"tables": ((0x1040, 16), (0x1040, 8))},
             "in the candidate's"),
            ("a byte outside the table", {"flats": (
                board_flat[:-1] + b"x", flat)}, "outside the table"),
            ("a byte before the table", {"flats": (early, flat), "boots": (
                b"shim" + early + b"guest", boot)}, "outside the table"),
            ("a table past the flat image", {"tables": ((0x1040, 0x60),) * 2},
             "is outside them"),
            ("the candidate's table", {"flats": (flat, flat), "boots": (
                boot, boot)}, "is the candidate's"),
            ("the flat image twice", {"boots": (
                b"shim" + board_flat + b"guest", boot + flat)}, "not once"),
            ("another shim", {"boots": (b"shin" + board_flat + b"guest",
                                        boot)}, "outside the flat image")):
        case(f"only-table refused: {name}", lambda: table(**change), want)

    rows = [BACKEND.Region("all-addresses", 0, 1 << 64, (), ("read",
                                                            "write")),
            BACKEND.Region("uart", 0x3000, 0x1000, ("read", "write"),
                           ("read", "write"), shared=True),
            BACKEND.Region("rw", 0x8000, 0x4000, ("read", "write"),
                           firmware=True),
            BACKEND.Region("rx", 0x4000, 0x4000, ("read", "execute"),
                           firmware=True)]
    shown = ["0x0000000000004000-0x0000000000007fff M: (F,R,X) S/U: ()",
             "0x0000000000008000-0x000000000000bfff M: (F,R,W) S/U: ()",
             "0x0000000000003000-0x0000000000003fff M: (I,R,W) S/U: (R,W)",
             "0x0000000000000000-0xffffffffffffffff M: () S/U: (R,W)"]
    text = "".join(f"Domain0 Region{at:02d}            : {value}\r\n"
                   for at, value in enumerate(shown))
    case("banner: the model's regions are the banner's", lambda: (
        banner_check(model(rows), printed("OpenSBI\r\n" + text), "x")))
    case("banner refused: the device rows not marked MMIO", lambda: (
        banner_check([BACKEND.banner(row) for row in BACKEND.sorted_regions(
            rows)], shown, "x")), "Region02")
    case("banner refused: one region fewer", lambda: banner_check(
        model(rows)[:3], shown, "x"), "3 root regions")
    for name, value, want in (
            ("a region out of order", text.replace("Region01", "Region02"),
             "Region02 is out of order"),
            ("no region", "OpenSBI\n", "no Domain0 region")):
        case(f"banner refused: {name}", lambda: printed(value), want)
    for name, changed in mutations(shown).items():
        case(f"banner's mutation refused: {name}", lambda: compare(
            model(rows), changed), "the banner's")

    tree = b"\xd0\x0d\xfe\xed tree"
    record = f"with=X\nfdt_sha256={hashlib.sha256(tree).hexdigest()}\n"
    binary = b"code" * 4 + tree + b"rest"
    case("holds-tree: the tree at fw_fdt_bin", lambda: holds_tree(
        record, binary, 16, tree))
    case("holds-tree refused: another tree's digest", lambda: holds_tree(
        record.replace("=", "=0", 2), binary, 16, tree), "SHA-256")
    case("holds-tree refused: the tree elsewhere", lambda: holds_tree(
        record, binary, 12, tree), "at fw_fdt_bin")

    build = scratch / "build"
    board_cases(case, build, dtc)
    print(f"BE_MVP_K3_BOARD_SELF_TEST: {'PASS' if all(results) else 'FAIL'}"
          f" cases={len(results)}")
    return 0 if all(results) else 1


def board_cases(case, build, dtc):
    """board on a stand-in build: an image with the boundary on and one
    with it off, the stand-in step 3 their tree; then each binding of the
    record refused."""
    fixtures = HERE.parent / "k3" / "fixtures" / "partition"
    platform = fixtures / "platform.json"

    def put(relative, data):
        path = build / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else (
            json.dumps(data) + "\n").encode())
        return BACKEND.sha(path)
    here = "k3/gate/images/"
    (build / here).mkdir(parents=True)
    subprocess.run([str(dtc), "-q", "-I", "dts", "-O", "dtb", "-o",
                    str(build / "step3.dtb"), str(fixtures / "step3.dts")],
                   check=True)
    tree = (build / "step3.dtb").read_bytes()
    identity = "ab" * 32
    put("gen/partition/anchor/authority-report.json", {"descriptors": [
        {"image": "pair", "identity": identity}]})
    for image, boundary in (("on", {"pair": "pair", "record": True}),
                            ("off", None)):
        expect = {"image": image, "scenario": "anchor"}
        if boundary:
            expect["boundary"] = boundary
        put(f"expect/{image}.json", expect)
        put(f"images/{image}.img", b"image")
        elf = put(f"{here}{image}/fw_dynamic.elf", b"elf")
        put(f"{here}{image}/fw_dynamic.bin", b"binary")
        root = put(f"{here}{image}/{image}-root.json", {
            "firmware_sha256": elf, "image": image, "regions": ["one",
                                                               "two"]})
        check = {"boundary": "on" if boundary else "off", "image": image,
                 "root_sha256": root,
                 "dtb_sha256": put(f"{here}{image}/{image}.dtb", tree)}
        if boundary:
            check.update(identity=identity, tables_sha256=put(
                f"{here}{image}/{image}-pmp.json", {"tables": 1}))
        put(f"{here}{image}/{image}-check.json", check)

    def made(image="on", sitting="second", staged=None, reference=""):
        return board(build, platform, (
            image, sitting, staged or f"be-mvp-anchor-{image}-gcc.img",
            f"images/{image}.img", f"expect/{image}.json", reference),
            ("std-off exp-off", "std-on exp-on"), "halt")
    keys = {"schema", "image", "sitting", "toolchain", "boundary", "digest",
            "staged_name", "board_image", "expectation", "reference",
            "tree", "root", "check", "tables", "partition_authority",
            "firmware", "sbi_version", "sbi_extensions", "reset_device",
            "platform_name", "product_name", "root_regions", "harts"}

    def form(image, digest, tables):
        value = made(image)
        require(set(value) == keys and value["digest"] == digest and
                (value["tables"] is None) != tables and value[
                    "sbi_extensions"]["standard"] == f"std-{image}" and
                value["harts"][:4] == [{"hartid": 0, "role": "control"}, {
                    "hartid": 1, "role": "vs-domain"}, {
                        "hartid": 2, "role": "vs-domain"}, {
                            "hartid": 3, "role": "parked"}] and
                len(value["harts"]) == 16 and value["root_regions"] ==
                ["one", "two"] and value["platform_name"] ==
                "stand-in board", f"{image}: {value}")
    case("board: the boundary on, with its digest and tables", lambda: form(
        "on", identity, True))
    case("board: the boundary off, with neither", lambda: form(
        "off", None, False))
    # Each change: new bytes, keys replaced in the file's JSON, or none.
    pair = {"image": "pair", "identity": identity}
    for name, path, data, want in (
            ("a tree edited after its check", f"{here}on/on.dtb",
             tree + b"x", "differ"),
            ("the root file of another firmware", f"{here}on/fw_dynamic.elf",
             b"other", "differ"),
            ("the root file edited after its check", f"{here}on/on-root.json",
             {"regions": ["one"]}, "differ"),
            ("the tables edited after their check", f"{here}on/on-pmp.json",
             {"tables": 2}, "tables differ"),
            ("another identity", "gen/partition/anchor/authority-report.json",
             {"descriptors": [dict(pair, identity="cd" * 32)]}, "identity"),
            ("two rows for the pair", "gen/partition/anchor/"
             "authority-report.json", {"descriptors": [pair, pair]},
             "identity"),
            ("a check record of another image", f"{here}on/on-check.json",
             {"image": "x"}, "differ"),
            ("a check record of the boundary off", f"{here}on/on-check.json",
             {"boundary": "off"}, "differ"),
            ("an expectation of another image", "expect/on.json",
             {"image": "x"}, "or expectation"),
            ("no tables", f"{here}on/on-pmp.json", None, "is not a file")):
        old = (build / path).read_bytes()
        _ = (build / path).unlink() if data is None else put(path, data if (
            isinstance(data, bytes)) else dict(json.loads(old), **data))
        case(f"board refused: {name}", made, want)
        put(path, old)
    for name, call, want in (
            ("a staged name not of k3-env.sh's form", lambda: made(
                staged="be-mvp-anchor--on-gcc.img"), "staged name"),
            ("a sitting neither first nor second", lambda: made(
                sitting="third"), "its sitting")):
        case(f"board refused: {name}", call, want)
    case("board: a reference given, its file and SHA-256", lambda: require(
        made(reference="images/on.img")["reference"] == entry(
            build, "images/on.img"), "the reference is not its file's"))
    old = (build / "expect" / "on.json").read_bytes()
    put("expect/on.json", dict(json.loads(old), boundary={"pair": "pair"}))
    case("board: a boundary without a record, its digest null",
         lambda: form("on", None, True))
    put("expect/on.json", old)
    (build.parent / "x").write_bytes(b"outside")
    case("board refused: a path outside the build", lambda: entry(
        build, "../x"), "is not a file under")


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    for option in ("--scratch", "--dtc"):
        parser.add_argument(option, type=pathlib.Path)
    commands = parser.add_subparsers(dest="command")
    for name, options in (
            ("only-table", "nm! base! board! candidate!"),
            ("banner", "image! dtb! firmware-elf! nm! readelf! console!"),
            ("holds-tree", "nm! build! tree!"),
            ("board", "build! platform! extensions-on! extensions-off! "
             "shutdown!")):
        command = commands.add_parser(name)
        for option in options.split():
            command.add_argument("--" + option.rstrip("!"), required=True,
                                 type=str if option in (
                                     "base!", "image!", "shutdown!") or
                                 option.startswith("extensions") else
                                 pathlib.Path)
    commands.choices["board"].add_argument("--image", action="append",
                                           required=True)
    args = parser.parse_args(argv[1:])
    if args.self_test == bool(args.command) or args.self_test and None in (
            args.scratch, args.dtc):
        parser.error("give a command, or --self-test --scratch DIR --dtc DTC")
    if args.self_test:
        return self_test(args.scratch.resolve(), args.dtc)
    try:
        lines = {"only-table": only_table_files, "banner": banner_files,
                 "holds-tree": holds_tree_files,
                 "board": board_files}[args.command](args)
    except (Refused, OSError, ValueError, KeyError, TypeError,
            IndexError) as error:
        print(f"BE_MVP_K3_BOARD: FAIL refused: {error}")
        return 1
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
