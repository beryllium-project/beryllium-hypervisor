#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""The capture checker's card mode (M11-B), on synthetic captures.

  test-k3-form.py --build-root BUILD --fixtures DIR --scratch DIR
                  --report REPORT --kernel IMAGE --dtb DTB
  test-k3-form.py --write-card-fixtures OUT --memory SIZE --build-root BUILD
                  [--fixtures DIR] --report REPORT --kernel IMAGE --dtb DTB
                  IMAGE=EXPECT:BOARD_IMAGE[:REFERENCE] ...

Purpose: planning/mvp-m11-board-addendum.md, B-8 and B-10: the form for a
boot of the board from a card under the project's firmware, as
tests/check-capture.py --mode card judges it, on captures built here from
parts, so that no log of a real boot is copied anywhere. The monitor's
lines are the checker's own stand-ins (current_log_standin(), from the
build's references, in the board's form by uboot_form()); the boot ROM's,
the SPL's, the firmware banner's, U-Boot's, and the vendor's lines are
made up around the stand-in board.json and observed facts under DIR (the
vendor's lines as its source prints them); the commit records are written
from tests/check-boundary.py's synthetic tables, which with a stand-in
partition authority are the inputs of their judgement (judge_board()).
Three shapes pass: the boundary off (two-guests-off), on (anchor), and on
under a hostile-monitor image's declaration (breach-g1's). Each mutation
of a shape fails with its own finding and stop, each variant passes, each
input that board_refusal() refuses is refused, and each refused input of
the command line exits 2, names itself on standard error, and writes no
record; rom_lines() and boot_medium() give their values on whole, cut,
and changed captures; and captures of boots cut at each stage give their
stops exactly, the earliest stage that the boot did not reach first, with
the product name and hart count that they show. REPORT, IMAGE, and DTB
are anchor's authority report and measured inputs.

--write-card-fixtures (the writer, for the sittings' dry run) makes OUT,
under BUILD, afresh: OUT/observed.json, the stand-in facts with SIZE as
U-Boot's memory, the same for every image; and for each IMAGE, under
OUT/IMAGE/, serial.log, a whole passing capture of a boot from a card
whose load is BOARD_IMAGE's size and MD5 and whose log is rendered from
REFERENCE (or the build's) and BOARD_IMAGE; board.json, a stand-in naming
BOARD_IMAGE's SHA-256, with the stand-in tables and partition authority
beside it, its paths from BUILD; and card-args.json, the checker's
arguments after the capture's path (the second sitting's naming
OUT/observed.json). Every value of the hardware's is made up. The test
writes the four images of its build so and requires that each capture
passes the form with its own arguments.

Trust: a test; it runs the checker in this process, and as a child for the
command line's cases, and writes only under --scratch (or OUT), which it
makes afresh. Scope: the rows C1 to C11 (rows()), the stops' order
(stop_cases()), the boot's medium, and the writer. Exit 0 pass, 1 fail,
2 usage.
"""

import argparse
import contextlib
import copy
import hashlib
import io
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import zlib

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
ORDER = ("rom", "spl", "banner", "uboot", "load", "monitor", "records")
# Each shape: its expectation under the build, the retained fixture whose
# stand-in gives its monitor's lines, and its board.json stand-in.
SHAPES = {"off": ("gen/expect/two-guests-off.json", "qemu-two-guests-gcc-m9",
                  "board-off.json"),
          "on": ("gen/anchor/expect/anchor.json", "qemu-anchor-gcc-m9",
                 "board-on.json"),
          "hostile": ("gen/anchor/expect/breach-g1.json",
                      "qemu-anchor-gcc-m9", "board-on.json")}
OTHER = "sbi_stand_in: a line of no field"
UBOOT = "U-Boot 2022.10 (Jan 01 2026 - 00:00:00 +0000)"
NO_DEVICE = "Could not find a valid device for stand-in.spi"
# The power chip's line as the board's reboot driver prints it.
PMIC = "spacemit reboot: read PMIC reg 0xab value 0x{:x}"
RECORD, QUIET = "Domain commit hart", \
    "pmp_faults=0 blocked_calls=0 failed_calls=0"
# The environment's line in its second shape: the card's driver prints
# while the load initialises the card (made-up lines), then OK alone.
TUNED = ("Loading Environment from MMC... sdhci@stand-in: tuning",
         "sdhci@stand-in: tuned", "OK")


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CC = load("check_capture", "check-capture.py")
CB = load("check_boundary", "check-boundary.py")
PINS = CC.read_pins()


def field(label, value):
    """A banner line as the firmware prints it (label padded to 28)."""
    return f"{label:<28}: {value}"


def banner(board, observed, version, art):
    """The firmware's banner for BOARD and OBSERVED: the root OpenSBI
    domain; with the boundary on, one for the monitor's harts at boot and
    the parked harts' own."""
    facts, devices = observed["firmware"], observed["firmware"]["devices"]
    ids = [hart["hartid"] for hart in board["harts"]]
    parked = [hart["hartid"] for hart in board["harts"]
              if hart["role"] == "parked"]
    on = board["boundary"] == "on"
    out = ["", version] + art + [""] + ([field(
        "Domain commit digest", board["digest"])] if board["digest"] else [])
    out += [field(f"Platform {label}", value) for label, value in (
        ("Name", board["platform_name"]), ("Features", "medeleg"),
        ("HART Count", len(ids)), ("HART Protection", "pmp"))]
    out += [field(f"Platform {name} Device", devices[name.lower()])
            for name in ("IPI", "Timer", "Console", "HSM", "PMU")]
    out += [field("Platform Reboot Device", board["reset_device"]["reboot"]),
            field("Platform Shutdown Device",
                  board["reset_device"]["shutdown"]),
            field("Platform Suspend Device", devices["suspend"]),
            field("Platform CPPC Device", devices["cppc"])]
    out += [field(f"Firmware {label}", value) for label, value in (
        ("Base", board["firmware"]["load"]), ("Size", "300 KB"),
        ("RW Offset", "0x40000"), ("RW Size", "60 KB"),
        ("Heap Offset", "0x48000"), ("Heap Size", "32 KB (total)"),
        ("Scratch Size", "4096 B (total)"))]
    out += [field("Runtime SBI Version", board["sbi_version"]),
            field("Standard SBI Extensions",
                  board["sbi_extensions"]["standard"]),
            field("Experimental SBI Extensions",
                  board["sbi_extensions"]["experimental"]), ""]
    domains = [("root", [] if on else ids, ids, board["root_regions"])]
    domains += [("be_boot", [0, 1, 2], [0, 1, 2], board["root_regions"]),
                ("be_park", parked, parked, [
                    "0x0000000000001000-0x0000000000001fff M: () S/U: (X)"])
                ] if on else []
    for number, (name, assigned, listed, regions) in enumerate(domains):
        out += [field(f"Domain{number} Name", name),
                field(f"Domain{number} HARTs", ",".join(
                    f"0x{hart:x}{'*' * (hart in assigned)}"
                    for hart in listed))]
        out += [field(f"Domain{number} Region{index:02d}", region)
                for index, region in enumerate(regions)]
        out += [field(f"Domain{number} Next Mode", "S-mode"), ""]
    out += [field("Boot HART ID", 0),
            field("Boot HART Domain", "be_boot" if on else "root")]
    out += [field(label, facts[key])
            for key, label in CC.CARD_HARDWARE.items()]
    return out + [field("Boot HART MIDELEG", "0x0000000000000222"),
                  field("Boot HART MEDELEG", "0x000000000000b109")]


def records(board, expect):
    """M-mode's commit records of board.json's harts, in its order: those
    declared confined with the synthetic tables' entries and the declared
    counts; none where the tree holds no digest."""
    boundary = expect.get("boundary") or {}
    if not boundary.get("record"):
        return []
    tables, out = CB.synthetic_tables("confined"), []
    for hart in (hart["hartid"] for hart in board["harts"]):
        tag, counts = f"Domain commit hart{hart}: ", boundary.get(
            "counts", {}).get(str(hart), {})
        confined = boundary["harts"].get(str(hart)) == "confined"
        out.append(f"{tag}committed={int(confined)} " + " ".join(
            f"{name}={counts.get(name, 0)}" for name in CB.COUNTS))
        if confined:
            entries = CB.table_of(tables, "plain", hart, "confined")
            cfg = bytes(int(entry["config"], 16) for entry in entries)
            addr = [int(entry["address"], 16) if entry["address"] !=
                    "not-compared" else 0 for entry in entries]
            out += [tag + line for line in (
                "menvcfg=0x80000000000000c0 mseccfg=0x0000000000000000",
                "pmpcfg=" + cfg.hex(),
                "pmpaddr0=" + ",".join(f"0x{word:016x}" for word in addr[:8]),
                "pmpaddr8=" + ",".join(f"0x{word:016x}" for word in addr[8:]))]
    return out


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def standin_tables():
    """The tables that records() writes from, the stand-in digest's."""
    return dict(CB.synthetic_tables("confined"),
                descriptor_identity=CC.STANDIN_DIGEST)


def standin_authority(expect):
    """A partition authority whose row for EXPECT's pair is the stand-in
    digest's."""
    return {"schema": "be-partition-authority-v1", "descriptors": [{
        "file": "stand-in", "image": expect["boundary"]["pair"],
        "identity": CC.STANDIN_DIGEST}]}


def base(shape, args):
    """SHAPE's capture as sections, and its context: the expectation, the
    stand-in board.json, observed facts, tables, and partition authority,
    the report, the options, and the paths of its reference and image."""
    expect_path, fixture, board_name = SHAPES[shape]
    root = args.build_root
    expect = read(root / expect_path)
    board = dict(read(args.fixtures / board_name), image=expect["image"])
    observed = read(args.fixtures / "observed-standin.json")
    paths = CC.LOG.default_paths(root, "gcc", expect)
    parts, (size, crc, md5) = capture(
        root, expect, board, observed, paths[1].read_bytes(), fixture,
        environment=TUNED if shape == "on" else None)
    on = "boundary" in expect
    options = {"toolchain": "gcc", "build_root": str(root),
               "image_bytes": size, "image_crc32": crc, "image_md5": md5,
               "measured": (args.kernel.read_bytes(), args.dtb.read_bytes())}
    context = {"expect": expect, "board": board, "reference": None,
               "standin": observed, "expect_path": root / expect_path,
               "memory": observed["uboot"]["memory"], "options": options,
               "report": args.report.read_bytes() if "report" in expect
               else None, "paths": paths,
               "tables": standin_tables() if on else None,
               "authority": standin_authority(expect) if on else None}
    context["observed"] = judge(parts, context)[1]["observed"]
    return parts, context


def capture(root, expect, board, observed, boot, fixture, paths=None,
            environment=None):
    """A passing capture of a boot of EXPECT's image from a card, as
    sections: the boot ROM's, SPL's, firmware banner's, and U-Boot's lines
    from BOARD and OBSERVED, the environment's in the first shape unless
    ENVIRONMENT gives its lines; the load of BOOT, the board image's bytes;
    the monitor's lines, FIXTURE's stand-in, its log rendered by PATHS
    (reference, boot image; the build's if none); and the records. (The
    sections, (BOOT's size, CRC-32, MD5).)"""
    size, crc, md5 = len(boot), zlib.crc32(boot), hashlib.md5(boot).hexdigest()
    standin = CC.current_log_standin(CC.fixture(fixture), expect, root,
                                     paths)
    top = standin.replace("\r", "").split("\n")
    version = next(index for index, line in enumerate(top)
                   if CC.CARD_FIRMWARE.fullmatch(line.strip()))
    art = top[version + 1:top.index("", version + 1)]
    form = CC.uboot_form(CC.hart_zero(standin), size, crc, md5).split("\n")
    first = next(index for index, line in enumerate(form)
                 if line.startswith((CC.RULE_TAG, CC.SHIM_TAG)))
    autoboot = next(index for index, line in enumerate(form)
                    if "Autoboot in" in line)
    monitor = [line for line in form[first:]
               if not line.startswith(CC.RECORD_TAG)]
    while monitor and not monitor[-1]:
        monitor.pop()
    parts = {
        "rom": ["\0\0" + observed["rom"][0]] + observed["rom"][1:],
        "spl": ["U-Boot SPL 2022.10 (Jan 01 2026 - 00:00:00 +0000)",
                "spl: a stand-in line"],
        "banner": banner(board, observed, top[version].strip(), art),
        "uboot": ["", "", UBOOT, "", f"DRAM:  {observed['uboot']['memory']}",
                  *(environment or ["Loading Environment from MMC... OK"]),
                  "video devices not found or not probed yet: -19",
                  "display devices not found or not probed yet: -19",
                  "Found 2 valid MAC addresses.",
                  f"TLV item: product_name = {board['product_name']}",
                  "save DDR training info", NO_DEVICE, PMIC.format(0),
                  "NO partition bootfs in card", "Autoboot in 0 seconds"],
        "load": form[autoboot + 1:autoboot + 7] + [
            CC.CARD_NOISE[0], "Starting kernel ...", ""],
        "monitor": monitor, "records": records(board, expect)}
    return parts, (size, crc, md5)


def text(parts):
    return "\n".join(line for name in ORDER for line in parts[name]) + "\n"


def judge(parts, context):
    options = dict(context["options"], card_board=context["board"],
                   card_memory=context["memory"],
                   card_observed=context["reference"],
                   card_tables=context["tables"],
                   card_authority=context["authority"])
    return CC.evaluate(text(parts), context["expect"], "card", PINS,
                       context["report"], **options)


# ------------------------------------------------------------------ edits
def sub(section, old, new):
    """An edit: OLD, in SECTION's first line that holds it, becomes NEW."""
    def edit(parts, context):
        lines = parts[section]
        index = next(index for index, line in enumerate(lines)
                     if old in line)
        lines[index] = lines[index].replace(old, new, 1)
    return edit


def recorded(hart, like=None):
    """An edit: hart HART's record becomes hart LIKE's lines, retagged (a
    committed hart's five), or with no LIKE one line, not committed."""
    def edit(parts, context):
        lines, tag = parts["records"], f"{RECORD}{hart}: "
        new = [tag + line.split(": ", 1)[1] for line in lines
               if line.startswith(f"{RECORD}{like}: ")] if like is not None \
            else [f"{tag}committed=0 {QUIET}"]
        at = [index for index, line in enumerate(lines)
              if line.startswith(tag)]
        lines[at[0]:at[-1] + 1] = new
    return edit


def swap(section, old, *new):
    """An edit: SECTION's first line that starts with OLD (NULs aside)
    becomes NEW's lines; with none, it goes."""
    def edit(parts, context):
        lines = parts[section]
        index = next(index for index, line in enumerate(lines)
                     if line.lstrip("\0").startswith(old))
        lines[index:index + 1] = list(new)
    return edit


def add(section, *new, at=None):
    """An edit: NEW's lines into SECTION, at its end, or before index AT, or
    before its first line that starts with AT."""
    def edit(parts, context):
        lines = parts[section]
        index = len(lines) if at is None else at if isinstance(at, int) \
            else next(index for index, line in enumerate(lines)
                      if line.startswith(at))
        lines[index:index] = list(new)
    return edit


def both(*edits):
    def edit(parts, context):
        for one in edits:
            one(parts, context)
    return edit


def refer(*edits):
    """EDITS, judged with the shape's own facts as the first sitting's."""
    def edit(parts, context):
        context["reference"] = copy.deepcopy(context["observed"])
        both(*edits)(parts, context)
    return edit


def setting(**values):
    def edit(parts, context):
        for key, value in values.items():
            context[key] = value(context[key]) if callable(value) else value
    return edit


def reorder(section, first, second):
    """An edit: the lines of SECTION that start with FIRST and SECOND, the
    one where the other was."""
    def edit(parts, context):
        lines = parts[section]
        one, two = (next(index for index, line in enumerate(lines)
                         if line.startswith(prefix))
                    for prefix in (first, second))
        lines[one], lines[two] = lines[two], lines[one]
    return edit


def banner_after_uboot(parts, context):
    parts["uboot"] += parts.pop("banner")
    parts["banner"] = []


def other_line(reference):
    """A line of no banner field among the banner's fields; with REFERENCE,
    judged against the first sitting's (which had none)."""
    edit = add("banner", OTHER, at="Platform HART Count")
    return refer(edit) if reference else edit


def domain(number, name, listed):
    return [field(f"Domain{number} Name", name),
            field(f"Domain{number} HARTs", listed), ""]


def harts(first, end):
    """A HARTs field's value: harts FIRST to END, less one, assigned."""
    return ",".join(f"0x{hart:x}*" for hart in range(first, end))


def put(label, value):
    """An edit: the banner's LABEL line with VALUE."""
    return swap("banner", label, field(label, value))


def rows():
    """(name, shape, edit, the finding's text or None for a variant, its
    stop or None for the sitting's) for C1 to C10."""
    nor, record, quiet = "a boot from the NOR", RECORD, QUIET
    count, ext = "Platform HART Count", "Experimental SBI Extensions"
    first, pmic = "the first sitting's", PMIC.split(" value")[0]
    out = [(f"the {shape} shape", shape, None, None, None)
           for shape in SHAPES]
    out += [("the on shape, its own facts the first sitting's", "on",
             refer(), None, None),
            ("C1: no boot ROM line", "off", lambda parts, context:
             parts.update(rom=[]), "no boot ROM line", None),
            ("C1: other ROM lines than the first sitting's", "on", refer(
                swap("rom", "rom: stand-in line 2", "rom: another")),
             f"the boot ROM's lines are not {first}", None)]
    out += [(f"C1: {line}", "off", add("rom", line), nor, "B4")
            for line in ("bm:4", "nor m:0x00 d:0x0000", "ERROR:   sd f! l:0")]
    out += [
        ("C2: no SPL banner", "off", swap("spl", "U-Boot SPL"),
         "0 U-Boot SPL banner lines", "B4"),
        ("C2: two SPL banners", "off", add("spl", "U-Boot SPL 2022.10 (x)"),
         "2 U-Boot SPL banner lines", "B3"),
        ("C2: the SPL's environment", "off",
         add("spl", "has init env successful"), "the SPL loaded", "B4"),
        ("C3.1: no firmware banner", "off", swap("banner", "OpenSBI v"),
         "0 firmware banner lines", None),
        ("C3.1: two firmware banners", "off", add(
            "banner", "OpenSBI v1.9", at="Platform Name"),
         "2 firmware banner lines", "B3"),
        ("C3.2: a field missing", "off", swap("banner", count),
         f"0 '{count}' lines in the firmware's banner", None),
        ("C3.2: a field twice", "off", add(
            "banner", field(count, 16), at="Platform HART Protection"),
         f"2 '{count}' lines in the firmware's banner", None),
        ("C3.2: fields out of order", "off",
         reorder("banner", "Platform Name", "Platform Features"),
         "fields are out of order", None),
        ("C3.3: another line, the first sitting", "off", other_line(False),
         None, OTHER),
        ("C3.3: another line than the first sitting's", "on",
         other_line(True), f"other lines are not {first}", None),
        ("C3.5: a digest, the boundary off", "off", add(
            "banner", field("Domain commit digest", "5a" * 32),
            at="Platform Name"), "commit digest or record before the "
         "markers of a boundary-off run", None),
        ("C3.5: no digest, the boundary on", "on",
         swap("banner", "Domain commit digest"),
         "0 configuration digest lines", None),
        ("C3.5: another digest", "on", put("Domain commit digest",
                                           "5b" * 32),
         "is not board.json's", None),
        ("C3.6: the root's name", "off", put("Domain0 Name", "first"),
         "the first OpenSBI domain's names are ['first']", None),
        ("C3.6: a root region", "on", put(
            "Domain0 Region02", "0x0000000010000000-0x0000000010000fff M: "
            "(I,R,W) S/U: (R)"), "Domain0 Region02 '0x0000000010000000-"
         "0x0000000010000fff M: (I,R,W) S/U: (R)' is not board.json's",
         None),
        ("C3.6: a root region fewer", "on", swap("banner", "Domain0 Region04"),
         "the root OpenSBI domain has 4 regions, board.json's 5", None),
        ("C3.7: a second OpenSBI domain, the boundary off", "off", add(
            "banner", *domain(1, "stand-in", "0x0"), at="Boot HART ID"),
         "a boundary-off banner shows 2 OpenSBI domains", None),
        ("C3.7: a parked hart in none", "on", put("Domain2 HARTs", harts(
            3, 15)), "hart 15 is assigned to 0 OpenSBI domains", None),
        ("C3.7: a VS-domain hart parked too", "on", put(
            "Domain2 HARTs", harts(1, 16)),
         "the parked harts' OpenSBI domain is assigned harts [1, 2] too",
         None)]
    # C3.4 and C3.8: a field of the build's, or past B-6's thresholds.
    out += [(f"C3.4/8: {label} {value!r}", shape, put(label, value),
             f"the banner's {label} is {value!r}{finding}", None)
            for label, value, shape, finding in (
                ("Platform Name", "x", "off", ""), (count, "8", "off", ""),
                ("Platform HART Protection", "epmp", "on", ", not 'pmp'"),
                ("Platform Reboot Device", "halt", "off", ", not '---'"),
                ("Platform Shutdown Device", "---", "off", ", not 'halt'"),
                ("Firmware Base", "0x80000000", "off", ", not board.json's"),
                ("Runtime SBI Version", "2.0", "off", ", not '3.0'"),
                (ext, "", "on", ", not 'dcommit'"),
                ("Boot HART ID", "1", "off", ", not '0'"),
                ("Boot HART PMP Count", "13", "off", ", not at least 14"),
                ("Boot HART PMP Granularity", "13 bits", "off",
                 ", not a grain of at most 4 KiB"),
                ("Boot HART Priv Version", "v1.11", "off",
                 ", not v1.12 or later"))]
    out += [(f"C3.9: {label}, not {first}", "on", refer(put(
        label, "stand-in other")), f"{label} 'stand-in other' is not {first}",
             None) for label in [*CC.CARD_HARDWARE.values(),
                                 *CC.CARD_DEVICES.values()]]
    # C4 and C5: U-Boot's banner, and each line required after it, missing.
    out += [(f"C4/5: no {line!r} line", "off", swap("uboot", line), finding,
             stop) for line, finding, stop in (
                 ("U-Boot 2022", "0 U-Boot banner lines before the markers, "
                  "expected 1", None),
                 ("DRAM:", "0 'DRAM:' lines", None),
                 ("Loading Environment", "0 'Loading Environment from' "
                  "lines", "B3"),
                 ("TLV item", "0 'TLV item: product_name' lines", None),
                 ("save DDR", "0 'save DDR training info' lines", None),
                 ("Could not find", "the vendor's save of the training "
                  "record without its line that no valid flash device was "
                  "found", "B2"),
                 (pmic, "0 'read PMIC reg 0xab' lines", None),
                 ("NO partition", "0 'NO partition bootfs in card' lines",
                  None))]
    out += [(f"C4: {line!r}", "off", swap("uboot", prefix, line), finding,
             stop) for prefix, line, finding, stop in (
                 ("DRAM:", "DRAM:  2 GiB", "U-Boot's memory '2 GiB' is not "
                  "the sitting's '4 GiB'", None),
                 ("Loading Environment", "Loading Environment from mtdENV"
                  "... OK", "came from mtdENV, not from the card's MMC",
                  "B3"),
                 ("Loading Environment", "Loading Environment from MMC... "
                  "*** Warning - bad CRC, using default environment",
                  "did not end in OK", "B3"),
                 ("TLV item", "TLV item: product_name = other",
                  "product name 'other' is not the board's", "B3"),
                 (pmic, PMIC.format(9), "0x9: its flag sends U-Boot into its "
                  "download mode over USB", "B11"))]
    out += [
        ("C4.4: the environment's second shape", "off", swap(
            "uboot", "Loading Environment", *TUNED), None, None),
        ("C4.4: the second shape with no OK", "on", swap("uboot", "OK"),
         "did not end in OK", "B3"),
        ("C4.4: its OK after the product name's line", "on", both(
            swap("uboot", "OK"), add("uboot", "OK", at="save DDR")),
         "did not end in OK", "B3"),
        ("C4.4: another source in the second shape", "on", sub(
            "uboot", "from MMC...", "from mtdENV..."), "came from mtdENV",
         "B3"),
        ("C4.4: the warning inside the second shape", "on", add(
            "uboot", "*** Warning - bad CRC, using default environment",
            at="OK"), "a bad environment", "B3"),
        ("C4.2: another memory than the first sitting's", "on", both(
            refer(), setting(reference=lambda reference: dict(
                reference, uboot={"memory": "8 GiB"}))),
         f"U-Boot's memory '4 GiB' is not {first} '8 GiB'", None),
        ("C5.2: two no-device lines", "off", add("uboot", NO_DEVICE,
                                                 at=pmic),
         "2 'Could not find a valid device for' lines", None),
        ("C5.2: the no-device line before the save", "off",
         reorder("uboot", "save DDR", "Could not find"),
         "out of order: 'Could not find a valid device for' before 'save",
         None),
        ("C5.4: the power chip's register, its flag clear", "off",
         swap("uboot", pmic, PMIC.format(0x48)), None, None),
        ("C5.4: the power chip's line after the no-partition line", "off",
         reorder("uboot", pmic, "NO partition"), "out of order: 'NO "
         "partition bootfs in card' before 'read PMIC reg 0xab'", None)]
    out += [(f"C6: {line}", "off", add("uboot", line, at=-1), finding, stop)
            for line, finding, stop in (
                ("SF: Detected stand-in with page size 256 Bytes",
                 "a flash was detected", "B2"),
                ("write 38912byte to spinor @offset 65536",
                 "a write to the NOR", "B2"),
                ("Removing MTD device #0 (nor0) with use count 1",
                 "U-Boot had an MTD device", "B2"),
                ("reset tlv data", "a rewrite of the identity EEPROM", "B3"),
                ("write to tlv_data fail", "a write to the identity EEPROM",
                 "B3"),
                ("generate 4 random ethaddr.", "a new MAC address", "B3"),
                ("*** Warning - bad CRC, using default environment",
                 "a bad environment", "B3"),
                ("find_valid_gpt: *** ERROR: Invalid GPT ***",
                 "a partition table's error", "B3"),
                ("find_valid_gpt: ***        Using Backup GPT ***",
                 "a partition table's error", "B3"),
                ("write 38912byte to block device(0) @address 65536",
                 "a write of the training record", "B3"),
                ("find_valid_gpt: ERROR: Can't allocate 0x4000 bytes for GPT "
                 "Entries", "a partition table's error", "B3"),
                *((line, "the power chip's flag was not read and cleared",
                   "B11") for line in (
                       f"{pmic.split(':')[0]}: get PMIC device failed: -19",
                       f"{pmic.split(':')[0]}: PMIC read failed",
                       f"{pmic.split(':')[0]}: PMIC write failed")),
                *((line, "U-Boot tried its download mode over USB", "B11")
                  for line in ("USB init failed: -19", "TCPM init failed: "
                               "-110", "\rUSB cable not detected.")),
                ("Saving Environment to MMC... OK",
                 "something saved the environment", "B11"),
                ("Can NOT find partition table partition_universal.json in "
                 "card", "the vendor's flash from a card looked in", "B3"),
                ("Cannot find partition: bootfs", "a splash ran", "B3"),
                ("Failed to get partition index for bootfs", "a splash ran",
                 "B3"),
                ("Net:   No ethernet found.", "the network started", "B3"),
                ('## Error: "be_boot" not defined', "a run of a variable "
                 "that the environment lacks", "B3"),
                ("Try to boot from mmc0 ...", "the vendor's boot flows",
                 "B3"),
                ("load env_k3.txt from bootfs successful", "an environment "
                 "file imported over the card's", "B3"))]
    out += [
        ("C7: the firmware's banner after U-Boot's", "off",
         banner_after_uboot, "out of order: U-Boot's banner before the "
         "firmware's banner", None),
        ("C8: a second autoboot line", "off",
         add("uboot", "Autoboot in 0 seconds", at=-1),
         "2 U-Boot autoboot lines", None),
        ("C8: another MD5", "off", lambda parts, context: parts[
            "load"].__setitem__(1, parts["load"][1][:-32] + "0" * 32),
         "is not the image's", None),
        ("C8: U-Boot's tree in G0's window", "off", lambda parts, context:
         parts["load"].__setitem__(5, "[   5.018]    Loading Device Tree to "
                                      "0000000110000000, end 0000000110001000"
                                      " ... OK"), "overlaps G0's window",
         None),
        ("C8: a line after Starting kernel", "off",
         add("load", "stand-in: a line", at=-1),
         "between 'Starting kernel ...' and the markers", None),
        ("C9: no shutdown line", "off", lambda parts, context: parts[
            "monitor"].pop(), "the sequence stops before", None),
        ("C9: a start rule's line", "off", add(
            "monitor", "BE_MVP_SHIM: boot_hart=0x1 starting hart 0", at=0),
         "a board boot enters the shim on hart 0", None),
        ("C10: fifteen records", "on", lambda parts, context: parts[
            "records"].pop(), "the commit record holds 15 harts, not 16",
         None),
        ("C10: two records out of order", "on",
         reorder("records", f"{record}4:", f"{record}5:"),
         "not the firmware's commit-record line 0 of hart 4", None),
        ("C10: a record before the monitor's last line", "on", add(
            "monitor", f"{record}0: committed=0 {quiet}", at=-1),
         "a commit-record line before the monitor's last line", None),
        ("C10: a seventeenth record", "on", add(
            "records", f"{record}16: committed=0 {quiet}"),
         "a commit record beyond the 16 harts", None),
        ("C10: a record, the boundary off", "off", add(
            "records", f"{record}0: committed=0 {quiet}"),
         "M-mode's commit record in a boundary-off run", None)]
    # C11: the records' values (tests/check-boundary.py's judge_board()).
    menvcfg, standin = "menvcfg=0x80000000000000c0", CC.STANDIN_DIGEST
    out += [
        ("C11: a configuration byte", "on", sub(
            "records", f"{record}1: pmpcfg=1b19", f"{record}1: pmpcfg=1b1d"),
         "hart 1 (confined) printed: pmp1cfg 0x1d, expected 0x19", None),
        ("C11: an address", "on", sub(
            "records", f"{record}2: pmpaddr0=0x0000000040805fff",
            f"{record}2: pmpaddr0=0x0000000040805ffe"),
         "hart 2 (confined) printed: pmpaddr0 0x40805ffe, expected "
         "0x40805fff", None),
        ("C11: a confined hart not committed", "on", recorded(2),
         "hart 2 (confined): printed not committed", None),
        ("C11: CBIE set", "on", sub(
            "records", f"{record}0: {menvcfg}",
            f"{record}0: menvcfg=0x80000000000000f0"),
         "hart 0 (confined): the printed menvcfg 0x80000000000000f0 has "
         "CBIE set", None),
        ("C11: mseccfg under plain PMP", "on", sub(
            "records", f"{record}1: {menvcfg} mseccfg=0x0000000000000000",
            f"{record}1: {menvcfg} mseccfg=0x0000000000000007"),
         "hart 1 (confined): under plain PMP the printed mseccfg is 0x7, "
         "not 0", None),
        ("C11: a parked hart committed", "on", recorded(9, 1),
         "hart 9 (parked): printed committed", None),
        ("C11: a parked hart's count", "on", sub(
            "records", f"{record}12: committed=0 pmp_faults=0",
            f"{record}12: committed=0 pmp_faults=1"),
         "hart 12 (parked): pmp_faults=1 printed, declared 0", None),
        ("C11: a scenario's count", "on", sub(
            "records", f"{record}1: committed=1 pmp_faults=0 blocked_calls=0",
            f"{record}1: committed=1 pmp_faults=0 blocked_calls=1"),
         "hart 1 (confined): blocked_calls=1 printed, declared 0", None),
        ("C11: a hostile image's sum", "hostile", sub(
            "records", f"{record}2: committed=1 pmp_faults=76",
            f"{record}2: committed=1 pmp_faults=75"),
         "hart 2 (confined): pmp_faults=75 printed, declared 76", None),
        ("C11: BE_MVP:02's identity", "on", sub(
            "monitor", f"identity={standin}", f"identity={'5b' * 32}"),
         f"BE_MVP:02's identity {'5b' * 32} is not the banner's", None),
        ("C11: hart 1's BE_MVP:09", "on", swap(
            "monitor", "BE_MVP:09 HART_READY hart=1 "),
         "hart 1 (confined): the capture has no BE_MVP:09 HART_READY",
         None),
        ("C11: hart 2's BE_MVP:08", "on", swap(
            "monitor", "BE_MVP:08 HART_STARTED hart=2 "), "hart 0 "
         "(confined): the capture has not both VS-domain harts' BE_MVP:08",
         None),
        ("C11: the authority's identity", "on", setting(
            authority=lambda authority: dict(authority, descriptors=[dict(
                authority["descriptors"][0], identity="5c" * 32)])),
         f"board.json's digest {standin} is not the partition authority's "
         f"identity of anchor", None),
        ("C11: the tables of another image", "on", setting(
            tables=lambda tables: dict(tables, descriptor_identity="5d" * 32)),
         "the tables are not the paired image anchor's", None)]
    return out


def witnessed(shape, card, board):
    """A shape's boundary line and the facts that it records beside the
    form: NOT-APPLICABLE with the boundary off; with it on PASS and
    witness=printed, and hook=not-read for the hostile image alone; the
    power chip's flag, the MAC addresses' count, and the product name and
    hart count, BOARD's."""
    line, facts = card["boundary"], card["facts"]
    return facts["pmic"] == "0x0" and facts["mac_addresses"] == "2" and \
        facts["environment_lines"] == ("2" if shape == "on" else "0") and \
        facts["product"] == board["product_name"] and \
        facts["harts"] == str(len(board["harts"])) and (
        line == CB.NOT_APPLICABLE.strip() if shape == "off" else
        line.startswith("BE_MVP_BOUNDARY: PASS ") and "witness=printed" in
        line and ("hook=not-read" in line) == (shape == "hostile"))


def case(name, shape, edit, finding, stop, bases):
    """One row judged: a variant passes, with no stop (a shape, writing out
    its stand-in's facts and its boundary line; with STOP, a note and an
    other line of STOP's); a mutation fails, with a finding that holds
    FINDING, and STOP (or its sitting's) among its stops."""
    parts, context = copy.deepcopy(bases[shape])
    if edit is not None:
        edit(parts, context)
    verdict, record = judge(parts, context)
    stops, notes = record["card"]["stops"], record["card"]["notes"]
    if finding is None:
        facts = record["observed"]
        good = verdict == "PASS" and not stops and (
            facts == context["standin"] and witnessed(
                shape, record["card"], context["board"])
            if edit is None else stop is None or
            any(stop in note for note in notes) and
            facts["firmware"]["other_lines"] == [stop])
    else:
        good = verdict == "FAIL" and any(
            finding in item for item in record["findings"]) and (
                stop or CC.CARD_SITTINGS[record["card"]["sitting"]]) in stops
    print(f"{'ok  ' if good else 'FAIL'} {name} ({shape}): {verdict} "
          f"stops={','.join(stops) or 'none'}" + (
              "" if good else f" {record['findings'][:4]}"))
    return good


def keep(*sections):
    """An edit: the capture cut to SECTIONS, the others left empty."""
    def edit(parts, context):
        for name in ORDER:
            parts[name] = parts[name] if name in sections else []
    return edit


def uboot_until(prefix, *after):
    """An edit: U-Boot's lines up to its first that starts with PREFIX, then
    AFTER's."""
    def edit(parts, context):
        lines = parts["uboot"]
        end = next(index for index, line in enumerate(lines)
                   if line.startswith(prefix))
        parts["uboot"] = lines[:end + 1] + list(after)
    return edit


def stop_cases(bases):
    """Captures judged whole, each refused: its stops exactly (the earliest
    stage that the boot did not reach first, then by number), each finding
    that names a stop (a part of its text, and the stop), and the product
    name and hart count of its card facts, as the capture shows them or
    none."""
    ddr = ("DDR Part Number: stand-in, Size: 0MB, Data Rate: 0MT/s",
           "DDR training consume 0ms")
    first = both(keep("rom", "spl"), swap("spl", "spl: a stand-in line",
                                          *ddr))
    later = keep("rom", "spl", "uboot", "load", "monitor", "records")
    to_uboot, environment = keep("rom", "spl", "banner", "uboot"), \
        "Loading Environment from MMC... OK"
    absent = [("0 'Loading Environment from'", "B3")]
    out = []
    for name, shape, edit, stops, named, facts in (
            ("the boot ROM's lines, the SPL's, then nothing", "off", first,
             ["B5"], [("0 firmware banner", "B5")], ("none", "none")),
            ("the same in the second sitting", "on", both(refer(), first),
             ["B6"], [("0 firmware banner", "B6")], ("none", "none")),
            ("cut after the firmware's banner", "off", keep(
                "rom", "spl", "banner"), ["B5"],
             [("0 U-Boot banner", "B5")], ("none", "16")),
            ("the boot ROM's lines alone", "off", keep("rom"),
             ["B4", "B5"], [("0 U-Boot SPL banner", "B4")], ("none", "none")),
            ("no firmware banner, a flash after U-Boot's", "off", both(
                later, add("uboot", "SF: Detected stand-in with page size "
                           "256 Bytes", at=-1)), ["B5", "B2"],
             [("0 firmware banner", "B5"), ("a flash was detected", "B2")],
             ("stand_in_product", "none")),
            ("a boot from the NOR with no firmware banner", "off", both(
                later, add("rom", "bm:4")), ["B4", "B5"],
             [("a boot from the NOR", "B4")], ("stand_in_product", "none")),
            ("cut after U-Boot's banner", "off", both(
                to_uboot, uboot_until("U-Boot 2022")), ["B5"], [],
             ("none", "16")),
            ("cut after U-Boot's DRAM line", "off", both(
                to_uboot, uboot_until("DRAM:")), ["B5"], [], ("none", "16")),
            ("U-Boot's lines to its product name's, not its environment's",
             "off", both(to_uboot, swap("uboot", "Loading Environment"),
                         uboot_until("TLV item")), ["B3", "B5"], absent,
             ("stand_in_product", "16")),
            ("U-Boot's DRAM line, then its autoboot line", "off", both(
                to_uboot, uboot_until("DRAM:", "Autoboot in 0 seconds")),
             ["B3", "B5"], absent, ("none", "16")),
            ("U-Boot's environment's line twice, then nothing", "off", both(
                to_uboot, uboot_until("Loading Environment", environment)),
             ["B3", "B5"], [("2 'Loading Environment from'", "B3")],
             ("none", "16")),
            ("no U-Boot banner, its lines to its product name's, not its "
             "environment's", "off", both(
                 to_uboot, swap("uboot", "U-Boot 2022"),
                 swap("uboot", "Loading Environment"),
                 uboot_until("TLV item")), ["B5"],
             [("0 U-Boot banner", "B5")], ("stand_in_product", "16")),
            ("U-Boot's DRAM line, then its no-partition line", "off", both(
                to_uboot, uboot_until("DRAM:", "NO partition bootfs in card")),
             ["B3", "B5"], absent, ("none", "16")),
            ("another product name", "off", sub(
                "uboot", "= stand_in_product", "= other"), ["B3"],
             [("product name 'other'", "B3")], ("other", "16"))):
        parts, context = copy.deepcopy(bases[shape])
        edit(parts, context)
        verdict, record = judge(parts, context)
        card = record["card"]
        tagged = [finding for finding in record["findings"]
                  if re.search(r" \(stop B[0-9]+\)$", finding)]
        good = verdict == "FAIL" and card["stops"] == stops and \
            len(tagged) == len(named) and all(
                part in finding and finding.endswith(f"(stop {stop})")
                for (part, stop), finding in zip(named, tagged)) and (
                    card["facts"]["product"], card["facts"]["harts"]) == facts
        print(f"{'ok  ' if good else 'FAIL'} {name} ({shape}): {verdict} "
              f"stops={','.join(card['stops']) or 'none'} product="
              f"{card['facts']['product']} harts={card['facts']['harts']}" + (
                  "" if good else f" {tagged}"))
        out.append(good)
    return out


def medium_cases(bases):
    """rom_lines() and boot_medium() on the off shape's capture, whole,
    cut where tools/k3-uboot.py may ask, and changed: each result, and
    nothing printed."""
    parts, rom = bases["off"][0], bases["off"][1]["standin"]["rom"]
    whole, banner = text(parts), parts["spl"][0] + "\n"
    cut = whole.index(banner)
    spaced = ["\0\0" + rom[0].replace(" ", "   ") + "\r", "",
              f"  {rom[1]}  \r"]
    out = []
    for name, capture, lines, medium in (
            ("a whole capture", whole, rom, "card"),
            ("cut after the SPL banner", whole[:cut + len(banner)], rom,
             "card"),
            ("cut before it", whole[:cut], [], "none"),
            ("a boot from the NOR", text(dict(parts, rom=parts["rom"] + [
                "bm:4"])), rom + ["bm:4"], "nor"),
            ("no boot ROM line", text(dict(parts, rom=[])), [], "none"),
            ("NULs, CRs, blank lines, spaces", text(dict(parts, rom=spaced)),
             rom, "card")):
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            got = CC.rom_lines(capture), CC.boot_medium(capture)
        good = got == (lines, medium) and not printed.getvalue()
        print(f"{'ok  ' if good else 'FAIL'} {name}: medium={got[1]}")
        out.append(good)
    return out


def refusal_cases(bases):
    """board_refusal()'s refusals of the on shape's records' inputs: a
    declaration that no board image has, tables that are not the board's,
    and an authority without the pair."""
    context = bases["on"][1]
    expect, tables, authority = (context[key] for key in (
        "expect", "tables", "authority"))
    plain = tables["modes"]["plain"]
    out = []
    for name, inputs, wanted in (
            *((f"a declaration with {key}", (dict(expect, boundary=dict(
                expect["boundary"], **{key: value})), tables, authority),
               f"declares {key}") for key, value in (
                   ("identity", "anchor"), ("phase", [0]), ("negative", "x"),
                   ("refusal", "x"), ("fallthrough", True))),
            ("tables of another schema", (expect, dict(
                tables, schema="other"), authority), "not of schema"),
            ("tables without plain PMP", (expect, dict(tables, modes={
                "smepmp": plain}), authority), "no plain PMP mode"),
            ("tables of the other step", (expect, dict(
                tables, control_hart="boot"), authority), "control_hart"),
            ("tables without hart 1's confined table", (expect, dict(
                tables, modes={"plain": [row for row in plain if (
                    row["hart"], row["state"]) != (1, "confined")]}),
                authority), "no one confined table for hart 1"),
            ("an authority without the pair", (expect, tables, dict(
                authority, descriptors=[])), "names no anchor")):
        why = CB.board_refusal(*inputs)
        good = why is not None and wanted in why
        print(f"{'ok  ' if good else 'FAIL'} refused, {name}" + (
            "" if good else f": {why!r}"))
        out.append(good)
    return out


def relative(path, root):
    """PATH from ROOT, the build root, as board.json names its files."""
    name = os.path.relpath(path, root)
    if name == ".." or name.startswith("../"):
        raise ValueError(f"{path} is not under the build root {root}")
    return name


def write_card(out, root, parts, context, args, observed):
    """One image's files, under OUT, made afresh: serial.log, PARTS'
    capture; board.json, CONTEXT's stand-in, naming its board image's
    SHA-256, and with the boundary on the stand-in tables and partition
    authority written beside it, its paths from ROOT; and card-args.json,
    the checker's arguments after the capture's path, OBSERVED (the first
    sitting's facts) among them in the second sitting. The arguments."""
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(mode=0o700, parents=True)
    reference, image = context["paths"]
    board = copy.deepcopy(context["board"])
    board["board_image"] = {"file": relative(image, root), "sha256":
                            hashlib.sha256(image.read_bytes()).hexdigest()}
    for key, name in (("tables", "tables"),
                      ("partition_authority", "authority")):
        if context[name] is not None:
            data = (json.dumps(context[name], indent=1) + "\n").encode()
            (out / f"{name}.json").write_bytes(data)
            board[key] = {"file": relative(out / f"{name}.json", root),
                          "sha256": hashlib.sha256(data).hexdigest()}
    (out / "board.json").write_text(json.dumps(board, indent=1) + "\n",
                                    encoding="utf-8")
    (out / "serial.log").write_text(text(parts), encoding="utf-8")
    arguments = ["--mode", "card", "--expect", str(context["expect_path"]),
                 "--board", str(out / "board.json"), "--memory",
                 context["memory"], "--image", str(image), "--reference",
                 str(reference), "--toolchain", "gcc", "--build-root",
                 str(root), "--kernel", str(args.kernel), "--dtb",
                 str(args.dtb)]
    arguments += ["--report", str(args.report)] \
        if "report" in context["expect"] else []
    arguments += ["--observed", str(observed)] \
        if board["sitting"] == "second" else []
    (out / "card-args.json").write_text(json.dumps(arguments, indent=1) +
                                        "\n", encoding="utf-8")
    return arguments


def write_card_fixtures(args, parser):
    """OUT/observed.json, the stand-in facts with --memory as U-Boot's
    memory, and for each IMAGE=EXPECT:BOARD_IMAGE[:REFERENCE] its files
    (write_card()): a whole passing capture of a boot from a card, its log
    rendered from REFERENCE (or the build's) and BOARD_IMAGE."""
    out, root = args.write_card_fixtures.resolve(), args.build_root
    if relative(out, root) == ".":
        raise ValueError(f"{out} is the build root itself")
    observed = dict(read(args.fixtures / "observed-standin.json"),
                    uboot={"memory": args.memory})
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(mode=0o700, parents=True)
    (out / "observed.json").write_text(json.dumps(observed, indent=1) + "\n",
                                       encoding="utf-8")
    for spec in args.images:
        name, _, rest = spec.partition("=")
        files = [pathlib.Path(item).resolve() for item in rest.split(":")]
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) or \
                len(files) not in (2, 3):
            parser.error(f"{spec!r} is not IMAGE=EXPECT:BOARD_IMAGE"
                         f"[:REFERENCE]")
        expect = read(files[0])
        if expect["image"] != name:
            parser.error(f"{spec!r}: its expectation is {expect['image']}'s")
        on = "boundary" in expect
        board = dict(read(args.fixtures / f"board-{'on' if on else 'off'}"
                          ".json"), image=name)
        paths = (files[2] if len(files) == 3 else CC.LOG.default_paths(
            root, "gcc", expect)[0], files[1])
        parts, _ = capture(root, expect, board, observed,
                           files[1].read_bytes(),
                           f"qemu-{expect['scenario']}-gcc-m9", paths)
        write_card(out / name, root, parts, {
            "expect": expect, "expect_path": files[0], "board": board,
            "paths": paths, "memory": args.memory,
            "tables": standin_tables() if on else None,
            "authority": standin_authority(expect) if on else None}, args,
            out / "observed.json")
    print(f"BE_MVP_K3_CARD_FIXTURES: PASS images={len(args.images)}")
    return 0


def child(name, words, status, wanted, result, stops=None):
    """The checker as a child with WORDS: its exit STATUS; with 2, WANTED on
    standard error and no RESULT; else its last line ending in WANTED, a
    RESULT with the card mode's keys, the STOPS list there if given, and
    its card.boundary line printed once."""
    run = subprocess.run([sys.executable, "-I", "-B",
                          str(HERE / "check-capture.py"), *words, "--json",
                          str(result)], capture_output=True, text=True,
                         check=False)
    last = (run.stdout.strip().splitlines() or [""])[-1]
    good = run.returncode == status and (
        wanted in run.stderr and not result.exists() if status == 2
        else last.endswith(wanted) and result.is_file() and judged(
            run.stdout, read(result), stops))
    print(f"{'ok  ' if good else 'FAIL'} the command line, {name}: exit "
          f"{run.returncode}" + ("" if good else
                                 f" {last!r} {run.stderr[-200:]!r}"))
    return good


def judged(printed, record, stops):
    """A card run's RECORD (result.json) beside what it PRINTED: the card
    mode's keys, its boundary line printed exactly once, and STOPS, if
    given, its list of stops."""
    return {"observed", "card", "inputs"} <= set(record) and \
        printed.splitlines().count(record["card"]["boundary"]) == 1 and \
        stops in (None, record["card"]["stops"])


def command_line(args, bases):
    """The checker as a child, on the off and on shapes' captures, written
    by write_card(): each passing, a boot from the NOR
    failing by its last line, and each refused input by its exit 2, its
    name on standard error, and no record; each of board.json's keys, gone,
    in turn among them."""
    root, cli = args.build_root, args.scratch / "cli"
    cli.mkdir(mode=0o700)
    (cli / "observed.json").write_text(json.dumps(bases["on"][1][
        "observed"]), encoding="utf-8")
    words = {shape: write_card(cli / shape, root, *bases[shape], args,
                               cli / "observed.json") for shape in ("off",
                                                                    "on")}
    logs = {shape: str(cli / shape / "serial.log") for shape in words}
    boards = {shape: cli / shape / "board.json" for shape in words}

    def changed(shape, name, edit):
        """SHAPE's words with a file NAME in place of its board.json (EDIT,
        on its data) or its expectation (EDIT on the expectation's)."""
        path = cli / shape / name
        which = boards[shape] if name.startswith("board") else \
            bases[shape][1]["expect_path"]
        data = read(which)
        edit(data)
        path.write_text(json.dumps(data), encoding="utf-8")
        return [str(path) if word == str(which) else word
                for word in words[shape]]

    def entry(key, value):
        return lambda board: board[key].update(sha256=value)
    (cli / "off" / "nor.log").write_text(text(dict(bases["off"][0], rom=bases[
        "off"][0]["rom"] + ["bm:4"])), encoding="utf-8")
    uboot = bases["off"][0]["uboot"]
    (cli / "off" / "stops.log").write_text(text(dict(bases["off"][0], uboot=[
        *uboot[:-1], "Saving Environment to MMC... OK", "Net:   none",
        uboot[-1]])), encoding="utf-8")
    (cli / "observed-bad.json").write_text(json.dumps(dict(
        bases["off"][1]["observed"], firmware={})), encoding="utf-8")
    off, on = words["off"], words["on"]
    cases = [
        ("a passing capture", logs["off"], off, 0, "stops=none"),
        ("a boot from the NOR", str(cli / "off" / "nor.log"), off, 1,
         "stops=B4"),
        ("no --board", logs["off"], off[:4] + off[6:], 2,
         "--mode card needs --board"),
        ("--board in uboot mode", logs["off"], [
            "uboot" if word == "card" else word for word in off], 2,
         "are the card mode's"),
        ("a board.json of another schema", logs["off"], changed(
            "off", "board-schema.json", lambda board: board.update(
                schema="other")), 2, "--board"),
        ("a board.json whose boundary is not the expectation's", logs["off"],
         changed("off", "board-boundary.json", lambda board: board.update(
             boundary="on")), 2, "boundary"),
        ("an image that is not board.json's", logs["off"], [
            on[on.index("--image") + 1] if word == off[off.index("--image") +
                                                       1] else word
            for word in off], 2, "--image"),
        ("a memory size not as U-Boot prints it", logs["off"], [
            "4GiB" if word == "4 GiB" else word for word in off], 2,
         "--memory"),
        ("an observed.json not of its form", logs["off"], off + [
            "--observed", str(cli / "observed-bad.json")], 2, "--observed"),
        ("two stops, in their order", str(cli / "off" / "stops.log"), off,
         1, "stops=B3,B11", ["B3", "B11"]),
        ("a passing capture, the boundary on", logs["on"], on, 0,
         "stops=none"),
        ("the second sitting without --observed", logs["on"], on[:-2], 2,
         "--observed"),
        ("tables not of their SHA-256", logs["on"], changed(
            "on", "board-tables.json", entry("tables", "0" * 64)), 2,
         "its tables"),
        ("an authority not of its SHA-256", logs["on"], changed(
            "on", "board-authority.json", entry("partition_authority",
                                                "0" * 64)), 2,
         "its partition_authority"),
        ("tables outside the build root", logs["on"], changed(
            "on", "board-outside.json", lambda board: board["tables"].update(
                file="../tables.json")), 2, ": tables not of its form"),
        ("a declaration that no board image has", logs["on"], changed(
            "on", "phase.json", lambda expect: expect["boundary"].update(
                phase=[0])), 2, "declares phase")]
    board = read(boards["on"])
    cases += [(f"board.json without {key}", logs["on"], changed(
        "on", f"board-without-{key}.json", lambda data, key=key: data.pop(
            key)), 2,
        f": {key} not of its form") for key in CC.card_board_problem(
            board, bases["on"][1]["expect"], "gcc", keys=True)]
    return [child(name, [capture_, *items], status, wanted,
                  cli / f"result-{number}.json", *stops)
            for number, (name, capture_, items, status, wanted, *stops) in
            enumerate(cases)]


def written_cases(args):
    """The writer as a child, for the four images of this build (anchor's
    two hostile-monitor images under QEMU's expectations in the place of
    the board's), then each written capture judged by the checker as a
    child with its own arguments: each passes, with no stop."""
    root, out = args.build_root, args.scratch / "written"
    specs = {"two-guests-off": ("gen/expect/two-guests-off.json",
                                "variants/gcc/two-guests-off/be-mvp-boot.img"),
             "anchor": ("gen/anchor/expect/anchor.json",
                        "gcc/anchor/be-mvp-boot.img"),
             "breach-g1": ("gen/anchor/expect/breach-g1.json",
                           "variants/gcc/breach-g1/be-mvp-boot.img",
                           "references/gcc/breach-g1.json"),
             "breach-c": ("gen/anchor/expect/breach-c.json",
                          "variants/gcc/breach-c/be-mvp-boot.img")}
    fake = args.scratch / "fake-root"
    fake.mkdir()
    (fake / "kept").write_text("", encoding="utf-8")

    def writer(out, root):
        return subprocess.run([
            sys.executable, "-I", "-B", str(HERE / "test-k3-form.py"),
            "--write-card-fixtures", str(out), "--build-root", str(root),
            "--memory", "8 GiB", "--fixtures", str(args.fixtures), "--report",
            str(args.report), "--kernel", str(args.kernel), "--dtb",
            str(args.dtb), *(f"{name}=" + ":".join(str(root / item)
                                                    for item in files)
                             for name, files in specs.items())],
            capture_output=True, text=True, check=False)
    refused = writer(fake, fake)
    kept = refused.returncode == 2 and "is the build root itself" in \
        refused.stderr and (fake / "kept").is_file()
    print(f"{'ok  ' if kept else 'FAIL'} writer, OUT the build root itself: "
          f"exit {refused.returncode}")
    run = writer(out, root)
    good = run.returncode == 0
    print(f"{'ok  ' if good else 'FAIL'} the writer: exit "
          f"{run.returncode}" + ("" if good else f" {run.stderr[-300:]!r}"))
    return [kept, good] + [child(
        f"the writer's {name}", [str(out / name / "serial.log"), *read(
            out / name / "card-args.json")], 0, "stops=none",
        out / name / "result.json") if good else False for name in specs]


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--write-card-fixtures", type=pathlib.Path)
    parser.add_argument("--memory")
    parser.add_argument("--scratch", type=pathlib.Path)
    parser.add_argument("--fixtures", type=pathlib.Path,
                        default=HERE.parent / "k3" / "fixtures" / "form")
    for name in ("--build-root", "--report", "--kernel", "--dtb"):
        parser.add_argument(name, type=pathlib.Path, required=True)
    parser.add_argument("images", nargs="*",
                        metavar="IMAGE=EXPECT:BOARD_IMAGE[:REFERENCE]")
    args = parser.parse_args(argv[1:])
    for name in ("build_root", "report", "kernel", "dtb", "fixtures"):
        setattr(args, name, getattr(args, name).resolve())
    if args.write_card_fixtures:
        if args.scratch or not args.images or not CC.CARD_MEMORY.fullmatch(
                args.memory or ""):
            parser.error("--write-card-fixtures OUT needs --memory SIZE, as "
                         "U-Boot prints it, and IMAGE=EXPECT:BOARD_IMAGE"
                         "[:REFERENCE] ...")
        try:
            return write_card_fixtures(args, parser)
        except (OSError, ValueError, KeyError) as error:
            parser.error(f"--write-card-fixtures: {error}")
    if not args.scratch or args.images or args.memory:
        parser.error("the test needs --scratch, and takes no IMAGE and no "
                     "--memory")
    args.scratch = args.scratch.resolve()
    shutil.rmtree(args.scratch, ignore_errors=True)
    args.scratch.mkdir(mode=0o700, parents=True)
    bases = {shape: base(shape, args) for shape in SHAPES}
    table = rows()
    results = [case(*row, bases) for row in table]
    variants = sum(row[3] is None for row in table)
    inputs, medium = command_line(args, bases), medium_cases(bases)
    refusals, written = refusal_cases(bases), written_cases(args)
    stopped = stop_cases(bases)
    passed = all(results + inputs + medium + refusals + written + stopped)
    print(f"BE_MVP_K3_FORM: {'PASS' if passed else 'FAIL'} "
          f"shapes={len(SHAPES)} mutations={len(table) - variants} "
          f"variants={variants} inputs={len(inputs)} medium={len(medium)} "
          f"refusals={len(refusals)} written={len(written)} "
          f"stops={len(stopped)}")
    return int(not passed)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
