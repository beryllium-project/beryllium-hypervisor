#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""M11-B's recipe (planning/mvp-m11-board-addendum.md, B-3): the board
firmware's device tree, made from the tree that the vendor's published
U-Boot FIT carries for the board's product, and its tests.

  extract --fit F --pins F --platform F --dtc DTC --out DIR [--twice DIR]
  platform --platform F --dir DIR --out F
  tree --dir DIR --tree DTB [--qemu-tree DTB --descriptor F
       --identity-header F]
  room --dir DIR --platform F DTB...
  --self-test --dtc DTC --fixtures DIR --scratch DIR

extract copies the FIT into DIR, a new private directory, checks the copy
against its pin, and takes the tree of the one configuration that
platform.json's product describes, as the SPL does (step 0). Steps 1 to 3
(the SPL's memory node and boot-hartid; the SPI flash's controller
disabled; the RPMI mailbox and its clients disabled) are each dtc source
over the step before, compiled and read back by the lock's dtc; each must
be its input with its own changes made and nothing else, and draw no dtc
warning that its input does not. --twice makes all again elsewhere and
requires the same bytes. platform checks platform.json's tree facts and
writes the tree's devices with their kinds. tree checks a board tree: step
3 with the descriptor's OpenSBI nodes added, the descriptor's identity, and
the QEMU tree's OpenSBI domains, but be_park's harts beyond QEMU's; with
the boundary off, step 3 itself. room checks that each tree, put after
U-Boot's image, leaves the firmware's fixups 8 KiB.

It shares tools/partition-backend.py's FDT reader and file helpers, loaded
as a module; tools/check-partition.py shares no code with either. Exit 0
pass, 1 fail or refused, 2 usage.
"""

import argparse
import copy
import importlib.util
import json
import os
import pathlib
import re
import shutil
import stat
import struct
import subprocess
import sys
import zlib

HERE = pathlib.Path(__file__).resolve().parent
TAG, FIT_NAME, SPARE = "BE_MVP_K3_RECIPE", "u-boot.itb", 8192
MEMORY = re.compile(r"/memory(?:@[^/]*)?")
CONFIG, DOMAINS = "/chosen/opensbi-config", "/chosen/opensbi-domains"
REFS = ("possible-harts", "boot-hart", "cold-boot-harts")
# A device's kind in platform.json: B-10's devices, those that hold
# persistent state, and any other.
KINDS = {"console", "interrupt-file-m", "interrupt-file-s",
         "interrupt-controller-m", "timer", "spi-flash-controller", "efuse",
         "i2c", "power-management", "storage", "other"}


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FDT = load("partition_backend", "partition-backend.py")
FRAME = load("k3_frame", "k3-frame.py")
Refused, require = FDT.Refused, FDT.require


def strict_json(path):
    def pairs(rows):
        require(len(dict(rows)) == len(rows), f"{path} repeats a key")
        return dict(rows)
    return json.loads(pathlib.Path(path).read_bytes(),
                      object_pairs_hook=pairs)


def number(text):
    require(isinstance(text, str) and FDT.HEX.match(text),
            f"{text!r} is not a hex number")
    return int(text, 16)


def read_regular(path):
    """A published file's bytes, opened as the frame's first step opens
    it."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise Refused(f"PIN: {path} is not a regular file")
    with os.fdopen(descriptor, "rb") as file:
        return file.read()


def dtc(tool, source, output):
    """dtc's warnings, each without its place, from compiling a .dts or
    reading back a .dtb. Any other line that it prints, but a warning's
    "also defined at", is refused."""
    back = source.suffix == ".dtb"
    said = FDT.run([str(tool), "-I", "dtb" if back else "dts", "-O",
                    "dts" if back else "dtb", "-o", str(output),
                    str(source)]).stderr.decode("utf-8", "replace")
    for line in said.splitlines():
        require("Warning (" in line or line.startswith("  also defined ")
                or not line.strip(), f"dtc said: {line}")
    return {line[line.index("Warning ("):] for line in said.splitlines()
            if "Warning (" in line}


def nodes(fdt):
    return {path: {name: row.value for name, row in rows.items()}
            for path, rows in fdt.nodes.items()}


def handles(fdt):
    return {FDT.cells(rows["phandle"].value)[0]: path
            for path, rows in fdt.nodes.items() if "phandle" in rows}


def enabled(fdt, path):
    """PATH and each of its ancestors have no status, "okay", or "ok"."""
    return FDT.prop(fdt, path, "status", False) in (
        None, b"okay\0", b"ok\0") and (path == "/" or enabled(
            fdt, FDT.parent(path)))


def cpus(fdt):
    """{hart: CPU node}, each hart by its node's reg."""
    out = {}
    for path in fdt.order:
        if FDT.parent(path) == "/cpus" and FDT.prop(
                fdt, path, "device_type", False) == b"cpu\0":
            rows = FDT.reg(fdt, path)
            require(len(rows) == 1 and rows[0][0] not in out,
                    f"{path} is not one hart of its own")
            out[rows[0][0]] = path
    return out


def bases(fdt, path):
    return [base for base, _ in FDT.reg(fdt, path)]


def dts(value):
    """A property's value as dtc source, and as the tree's bytes."""
    if isinstance(value, str):
        return f'"{value}"', value.encode() + b"\0"
    return ("<" + " ".join(f"{cell:#x}" for cell in value) + ">",
            struct.pack(f">{len(value)}I", *value))


def take_tree(fit, product):
    """The SPL's choice (U-Boot's common/common_fit.c, with the board's
    hook, which names the product): the one configuration that the
    product's name describes, naming no firmware; its one tree, flat_dt,
    CRC-32 checked; its one loadable, U-Boot; each inline, uncompressed."""
    conf = [path for path in fit.order
            if FDT.parent(path) == "/configurations" and FDT.prop(
                fit, path, "description", False) == product.encode() + b"\0"]
    require(len(conf) == 1, f"FIT: {len(conf)} configurations are {product}")
    require(FDT.prop(fit, conf[0], "firmware", False) is None,
            "FIT: the configuration names a firmware")
    names = [FDT.strings(FDT.prop(fit, conf[0], key)) for key in (
        "fdt", "loadables")]
    require([len(row) for row in names] == [1, 1],
            "FIT: not one tree and one loadable")
    tree, loadable = (f"/images/{row[0]}" for row in names)
    for path in (tree, loadable):
        rows = fit.nodes.get(path, {})
        require("data" in rows and not [name for name in rows
                                        if name.startswith("data-")],
                f"FIT: no inline {path}")
        require(FDT.prop(fit, path, "compression") == b"none\0",
                f"FIT: {path} is compressed")
    data, load = FDT.prop(fit, tree, "data"), FDT.prop(fit, loadable, "load")
    require(FDT.prop(fit, tree, "type") == b"flat_dt\0" and FDT.prop(
        fit, tree + "/hash-1", "algo", False) == b"crc32\0" and FDT.prop(
            fit, tree + "/hash-1", "value", False) == struct.pack(
                ">I", zlib.crc32(data)) and len(load) in (4, 8),
            "FIT: the tree's type or CRC-32, or U-Boot's load, differs")
    return data, {"configuration": conf[0], "tree": tree, "tree_bytes": len(
        data), "crc32": f"{zlib.crc32(data):08x}", "loadable": loadable,
                  "load": hex(int.from_bytes(load, "big")),
                  "loadable_bytes": len(FDT.prop(fit, loadable, "data"))}


def memory(fdt, facts):
    """Step 1, as the SPL's arch_fixup_fdt writes it (U-Boot's
    arch/riscv/lib/fdt_fixup.c): the root's memory node replaced by one
    bank of the board's memory; /chosen/boot-hartid."""
    old = [path for path in fdt.order if MEMORY.fullmatch(path)]
    base, size = (number(facts["memory"][key]) for key in ("base", "size"))
    hart = facts["boot_hart"]["value"]
    require(type(hart) is int and 0 <= hart < 1 << 32,
            "STEP1: the boot hart is not a hart's number")
    require([FDT.cell_count(fdt, "/", f"#{name}-cells", None) for name in (
        "address", "size")] == [2, 2], "STEP1: the root's cells are not 2")
    require(len(old) == 1 and "/chosen" in fdt.nodes,
            f"STEP1: {len(old)} root memory nodes, or no /chosen")
    require(size > 0 and size & (size - 1) == 0,
            "STEP1: the memory's size is not a power of two (two banks)")
    reg = [base >> 32, base & 0xFFFFFFFF, size >> 32, size & 0xFFFFFFFF]
    return old, {f"/memory@{base:x}": {"device_type": "memory", "reg": reg},
                 "/chosen": {"boot-hartid": [hart]}}, []


def flash(fdt, facts):
    """Step 2 (QB1): the SPI NOR flash's controller disabled, so that the
    vendor's U-Boot, which this tree configures, has no flash device."""
    found = [path for path in fdt.order
             if "jedec,spi-nor" in FDT.compatible(fdt, path)]
    parents = sorted({FDT.parent(path) for path in found})
    on = [path for path in parents if enabled(fdt, path)]
    require(found and "/" not in parents,
            "STEP2: no jedec,spi-nor node under a controller")
    require(len(on) == 1, f"STEP2: {len(on)} enabled flash controllers")
    return [], {on[0]: {"status": "disabled"}}, found


def mailbox(fdt, facts):
    """Step 3 (QB6): the RPMI mailbox, and every node whose mboxes names it,
    disabled, so that the firmware finds no RPMI device."""
    box = [path for path in fdt.order
           if "riscv,rpmi-shmem-mbox" in FDT.compatible(fdt, path)]
    require(len(box) == 1, f"STEP3: {len(box)} RPMI mailboxes")
    found, clients = handles(fdt), []
    for path in fdt.order:
        row = FDT.cells(FDT.prop(fdt, path, "mboxes", False) or b"")
        while row:
            require(row[0] in found, f"STEP3: {path}:mboxes names no node")
            width = FDT.cell_count(fdt, found[row[0]], "#mbox-cells", None)
            require(width is not None, f"STEP3: {found[row[0]]} has no "
                    "#mbox-cells")
            require(len(row) > width,
                    f"STEP3: {path}:mboxes ends inside a specifier")
            clients += [path] if found[row[0]] == box[0] else []
            row = row[1 + width:]
    require(clients, "STEP3: no node names the RPMI mailbox")
    return [], {path: {"status": "disabled"} for path in box + clients
                if FDT.prop(fdt, path, "status", False) != b"disabled\0"}, \
        box + clients


def step(out, tool, index, before, rule, facts, previous, extra=""):
    """Step INDEX as dtc source over the step before, compiled, read back,
    and required to be its input with its changes made, and nothing else."""
    deleted, changes, off = rule(before, facts)
    gone = {path for path in before.order for top in deleted
            if path == top or path.startswith(top + "/")}
    expect = {path: rows for path, rows in nodes(before).items()
              if path not in gone}
    lines = [f'/include/ "step{index - 1}.dts"'] + [
        f"/delete-node/ &{{{path}}};" for path in deleted]
    for path, values in changes.items():
        body = [f"\t{name} = {dts(value)[0]};" for name, value in
                values.items()]
        lines += [f"&{{{path}}} {{", *body, "};"] if path in expect else [
            "/ {", f"\t{path[1:]} {{", *["\t" + row for row in body],
            "\t};", "};"]
        expect.setdefault(path, {}).update(
            {name: dts(value)[1] for name, value in values.items()})
    source, tree = out / f"step{index}-change.dts", out / f"step{index}.dtb"
    FDT.write_new(source, "\n".join(lines + [extra, ""]).encode())
    warned = (dtc(tool, source, tree),
              dtc(tool, tree, out / f"step{index}.dts"))
    after = FDT.parse_fdt(tree.read_bytes())
    actual = nodes(after)
    bad = sorted(path for path in set(expect) | set(actual)
                 if expect.get(path) != actual.get(path)) + [""]
    require(bad == [""], f"STEP{index}: {bad[0]} differs from its changes")
    require([path for path in after.order if path in before.nodes and
             path not in gone] == [path for path in before.order
                                   if path not in gone] and
            after.reserves == before.reserves,
            f"STEP{index}: the nodes' order or the reserve map changed")
    require(not [path for path in off if enabled(after, path)],
            f"STEP{index}: a node that it disables is enabled")
    require(warned[0] <= previous[0] and warned[1] <= previous[1],
            f"STEP{index}: dtc warns of what step {index - 1} does not")
    return after, warned, (f"step{index}: PASS sha256={FDT.sha(tree)} "
                           f"changes={len(deleted) + len(changes)}")


def same_files(first, second):
    names = sorted(path.name for path in first.iterdir())
    require(names == sorted(path.name for path in second.iterdir()) and all(
        (first / name).read_bytes() == (second / name).read_bytes()
        for name in names), f"RECIPE: {second} differs from {first}")
    return names


def extract(fit, pins, facts, tool, out, twice=None, extra=None):
    """Steps 0 to 3 into OUT, a new private directory."""
    out = FDT.private_directory(out)
    copied = out / FIT_NAME
    FDT.write_new(copied, read_regular(fit))
    require(FRAME.pins(pathlib.Path(pins), "published", True).get(FIT_NAME)
            == (FDT.sha(copied), copied.stat().st_size),
            f"PIN: the copy of {FIT_NAME} is not its pin's")
    data, record = take_tree(FDT.parse_fdt(copied.read_bytes()),
                             facts["product"]["value"])
    FDT.write_new(out / "step0.dtb", data)
    before, back = FDT.parse_fdt(data), dtc(tool, out / "step0.dtb",
                                            out / "step0.dts")
    warned = (dtc(tool, out / "step0.dts", out / "step0-again.dtb"), back)
    again = FDT.parse_fdt((out / "step0-again.dtb").read_bytes())
    require((nodes(again), again.order, again.reserves) == (
        nodes(before), before.order, before.reserves),
            "STEP0: the tree does not survive dtc's round trip")
    record["step0"] = FDT.sha(out / "step0.dtb")
    lines = [f"fit: PASS configuration={record['configuration']} "
             f"tree={record['tree']} sha256={FDT.sha(copied)}",
             f"step0: PASS sha256={record['step0']}"]
    for index, rule in enumerate((memory, flash, mailbox), 1):
        before, warned, line = step(out, tool, index, before, rule, facts,
                                    warned, (extra or {}).get(index, ""))
        record[f"step{index}"] = FDT.sha(out / f"step{index}.dtb")
        lines.append(line)
    FDT.write_new(out / "recipe.json", FDT.canonical(record))
    if twice is not None:
        extract(fit, pins, facts, tool, twice, extra=extra)
        lines.append(f"twice: PASS files={len(same_files(out, twice))}")
    return lines + [f"{TAG}: PASS extract step3_sha256={record['step3']}"]


def devices(fdt):
    """Each node with a reg in the CPUs' address space (every ancestor's
    ranges empty), CPU and memory nodes aside, in the tree's order."""
    out = []
    for path in fdt.order[1:]:
        up = FDT.parent(path)
        while up != "/" and FDT.prop(fdt, up, "ranges", False) == b"":
            up = FDT.parent(up)
        if up == "/" and "reg" in fdt.nodes[path] and FDT.prop(
                fdt, path, "device_type", False) not in (b"cpu\0",
                                                         b"memory\0"):
            out.append({"path": path, "compatible": (FDT.compatible(
                fdt, path) + [""])[0], "reg": [[hex(base), hex(size)] for
                                             base, size in FDT.reg(fdt, path)],
                        "status": "okay" if enabled(fdt, path) else
                        "disabled"})
    return out


def platform(facts, work, out):
    """platform.json's tree facts against steps 0 and 3: (findings, lines);
    with no finding, the tree's devices with their kinds into OUT."""
    zero, three = (FDT.parse_fdt((work / f"step{index}.dtb").read_bytes())
                   for index in (0, 3))
    harts, roots, breach = (facts[key] for key in (
        "harts", "root_devices", "breach"))
    console, imsic, scratch = roots["console"]["path"], breach["imsic_s"], \
        breach["console_scratch"]
    names = {index: set(FDT.strings(FDT.prop(
        three, path, "riscv,isa-extensions"))) for index, path in
             cpus(three).items()}
    entries = [int.from_bytes(rows["fw_boot_entry"].value, "big")
               for rows in three.nodes.values() if "fw_boot_entry" in rows]

    def found(node, compatible, base):
        return "reg" in three.nodes.get(node, {}) and compatible in \
            FDT.compatible(three, node) and number(base) in bases(three, node)

    def banks(key, tree):
        return [FDT.reg(tree, path) for path in tree.order if
                MEMORY.fullmatch(path)] == [[(number(facts[key]["base"]),
                                             number(facts[key]["size"]))]]

    bad = [finding for condition, finding in [
        (facts.get("schema") == "be-mvp-k3-platform-v1", "SCHEMA"),
        *[(isinstance(facts[key], dict) and isinstance(facts[key].get(
            "source"), str) and facts[key]["source"] != "", f"SOURCE: {key}")
          for key in sorted(set(facts) - {"schema", "platform", "purpose"})],
        (FDT.prop(zero, "/", "model", False) == facts["model"][
            "value"].encode() + b"\0", "MODEL"),
        ([FDT.cell_count(zero, "/", f"#{key}-cells", None) for key in (
            "address", "size")] == [facts["cells"][key] for key in (
                "address", "size")], "CELLS"),
        (banks("tree_memory", zero), "TREE_MEMORY"),
        (banks("memory", three), "MEMORY"),
        (sorted(names) == list(range(harts["count"])), "HARTS: ids"),
        (sorted(index for index, row in names.items() if "h" in row) ==
         harts["hypervisor"], "HARTS: hypervisor"),
        (not [row for row in names.values() if "smepmp" in row],
         "HARTS: smepmp"),
        ({FDT.prop(three, path, f"riscv,{kind}-block-size", False) for path
          in cpus(three).values() for kind in ("cbom", "cboz")} ==
         {struct.pack(">I", harts["cache_block"])}, "HARTS: cache block"),
        (entries and min(entries) == number(facts["firmware"]["end_max"]),
         "FIRMWARE: end_max"),
        *[(found(row["path"], row["compatible"], row["base"]) and enabled(
            three, row["path"]), f"ROOT: {name}")
          for name, row in roots.items() if name != "source"],
        (number(scratch["offset"]) == 7 << FDT.cell_count(
            three, console, "reg-shift", 0) and scratch["width"] ==
         FDT.cell_count(three, console, "reg-io-width", 1),
         "BREACH: console_scratch"),
        (found(imsic["path"], "riscv,imsics", imsic["base"]) and number(
            imsic["stride"]) == 0x1000 << FDT.cell_count(
                three, imsic["path"], "riscv,guest-index-bits", 0),
         "BREACH: imsic_s"),
        (breach["timer_width"] == (4 if "clint,has-no-64bit-mmio" in
                                   three.nodes.get(roots["clint"]["path"],
                                                   {}) else 8),
         "BREACH: timer_width")] if not condition]
    listed = devices(three)
    named = {row["path"]: row for row in facts["devices"]["list"]}
    bad += [] if len(named) == len(facts["devices"]["list"]) else [
        "DEVICES: a path named twice"]
    for row in listed:
        mine = named.pop(row["path"], {})
        row["kind"] = mine.get("kind")
        bad += [] if mine == row else [f"DEVICES: {row['path']} " + (
            "differs" if mine else "is not named")]
        bad += [] if not mine or row["kind"] in KINDS else [
            f"KIND: {row['path']}"]
    bad += [f"DEVICES: {', '.join(named)} not in the tree"] if named else []
    if not bad:
        FDT.write_new(out, FDT.canonical({"schema": "be-mvp-k3-devices-v1",
                                          "list": listed}))
    return bad, [f"other: {row['path']} {row['compatible']}"
                 for row in listed if row["kind"] == "other"]


def view(fdt):
    """The OpenSBI nodes: hart references as harts, regions as (node,
    access) pairs, the phandles' own values aside."""
    found, out = handles(fdt), {}
    harts = {path: index for index, path in cpus(fdt).items()}
    for path in fdt.order:
        if path not in (CONFIG, DOMAINS) and not path.startswith(
                DOMAINS + "/"):
            continue
        out[path] = rows = {}
        for name, row in fdt.nodes[path].items():
            cells = FDT.cells(row.value) if name in REFS or \
                name == "regions" else []
            if name in REFS:
                rows[name] = [harts[found[cell]] for cell in cells]
            elif name == "regions":
                rows[name] = [(found[cell], access) for cell, access in zip(
                    cells[::2], cells[1::2])]
            elif name != "phandle":
                rows[name] = row.value
    return out


def tree(work, path, qemu=None, descriptor=None, header=None):
    """Step 4's test (B-3): a board tree against step 3 and the QEMU tree
    of the same descriptor; without one, the boundary-off tree."""
    data, base_data = path.read_bytes(), (work / "step3.dtb").read_bytes()
    if descriptor is None:
        require(data == base_data, "TREE: the boundary-off tree is not step 3")
        return [f"{TAG}: PASS tree off sha256={FDT.sha(path)}"]
    base, board = FDT.parse_fdt(base_data), FDT.parse_fdt(data)
    was, now, cpu_nodes = nodes(base), nodes(board), set(cpus(base).values())
    require(set(was) <= set(now) and DOMAINS in now and all(
        node in was or node in (CONFIG, DOMAINS) or node.startswith(
            DOMAINS + "/") for node in now), "TREE: a node of step 3 gone, "
            "or one beyond the descriptor's added")
    for node, rows in was.items():
        mine = {name: value for name, value in now[node].items() if name !=
                "phandle" or node not in cpu_nodes or "phandle" in rows}
        require(mine == rows, f"TREE: {node} differs from step 3")
    require([node for node in board.order if node in was] == base.order and
            board.reserves == base.reserves,
            "TREE: step 3's order of nodes or reserve map changed")
    identity, other = FDT.sha(descriptor), FDT.parse_fdt(qemu.read_bytes())
    require(FDT.prop(board, DOMAINS, "config-digest") == bytes.fromhex(
        identity) == FDT.prop(other, DOMAINS, "config-digest", False),
            "IDENTITY: a config-digest is not the descriptor's SHA-256")
    require(re.findall(r'#define BE_MVP_PARTITION_IDENTITY_HEX "(\w+)"',
                       header.read_text(encoding="utf-8")) == [identity],
            "IDENTITY: the identity header is not the descriptor's")
    expect = view(other)
    park = expect.get(DOMAINS + "/be_park", {}).get("possible-harts")
    require(park is not None, "TREE: the QEMU tree has no be_park")
    park += range(len(cpus(other)), len(cpus(board)))
    require(view(board) == expect,
            "TREE: the OpenSBI domains differ from the QEMU tree's")
    return [f"{TAG}: PASS tree identity={identity} sha256={FDT.sha(path)}"]


def room(work, facts, trees):
    """The SPL puts its tree right after U-Boot's image: each tree there,
    with 8 KiB for the firmware's fixups, must end by spl_tree.room_end."""
    record = strict_json(work / "recipe.json")
    end = number(record["load"]) + record["loadable_bytes"] + SPARE
    for path in trees:
        FDT.parse_fdt(path.read_bytes())
        require(end + path.stat().st_size <= number(
            facts["spl_tree"]["room_end"]), f"ROOM: {path.name} does not fit")
    return [f"room {path.name}: PASS sha256={FDT.sha(path)}" for path in
            trees] + [f"{TAG}: PASS room trees={len(trees)}"]


def self_test(tool, fixtures, scratch):
    """Each rule's seeded defect, on the stand-ins, fails by that rule."""
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True)
    facts, results = strict_json(fixtures / "platform.json"), []
    runs, work = iter(range(1000)), scratch / "work"

    def expect(name, action, tag=None):
        try:
            action()
            said = None
        except (Refused, FRAME.Refused) as error:
            said = str(error)
        results.append(said is None if tag is None else
                       str(said).startswith(tag))
        print(f"ok   {name}" if results[-1] else f"FAIL {name}: {said}")

    def text(name, old="", new=""):
        source = (fixtures / name).read_text(encoding="utf-8")
        require(old in source, f"self-test: {name} lacks {old!r}")
        return source.replace(old, new) if old else source

    def published(board=None, fit=None):
        top = scratch / f"published-{next(runs)}"
        top.mkdir()
        (top / "board.dts").write_text(board or text("board.dts"))
        dtc(tool, top / "board.dts", top / "board.dtb")
        (top / "fit.dts").write_text((fit or text("fit.dts")).replace(
            "@PRODUCT@", facts["product"]["value"]).replace("@CRC@", hex(
                zlib.crc32((top / "board.dtb").read_bytes()))))
        dtc(tool, top / "fit.dts", top / FIT_NAME)
        (top / "pins.txt").write_text(
            f"published {FIT_NAME} sha256={FDT.sha(top / FIT_NAME)} "
            f"bytes={(top / FIT_NAME).stat().st_size}\n")
        return top

    def extracted(top, pins=None, changed=None, extra=None):
        out = scratch / f"out-{next(runs)}"
        extract(top / FIT_NAME, pins or top / "pins.txt", changed or facts,
                tool, out, None, extra)
        return out

    good = published()
    expect("extract: steps 0 to 3, twice, the same bytes", lambda: extract(
        good / FIT_NAME, good / "pins.txt", facts, tool, work,
        scratch / "again"))
    for name, old, new, tag in (
            ("no configuration is the product's", '"@PRODUCT@"', '"x"',
             "FIT: 0 configurations"),
            ("two configurations are the product's", '"other-product"',
             '"@PRODUCT@"', "FIT: 2 configurations"),
            ("the configuration names a firmware", 'fdt = "fdt_2";',
             'fdt = "fdt_2";\nfirmware = "uboot";', "FIT: the configuration"),
            ("its tree names no image", '"fdt_2";', '"fdt_9";',
             "FIT: no inline /images/fdt_9"),
            ("its tree's data outside the FIT", '/incbin/("board.dtb")',
             "<0x0>;\ndata-offset = <0x0>", "FIT: no inline /images/fdt_2"),
            ("its tree's CRC-32 differs", "<@CRC@>", "<0x1>",
             "FIT: the tree's type or CRC-32"),
            ("its tree not flat_dt", 'fdt_2 {\n\t\t\ttype = "flat_dt"',
             'fdt_2 {\ntype = "x"', "FIT: the tree's type or CRC-32"),
            ("U-Boot's load in three cells", "<0x00 0x80200000>",
             "<0x0 0x0 0x80200000>", "FIT: the tree's type or CRC-32"),
            ("two loadables", '"uboot";\n\t\t\tfdt = "fdt_2"',
             '"uboot", "fdt_1";\nfdt = "fdt_2"', "FIT: not one tree"),
            ("its tree compressed", 'none";\n\t\t\tdata = /incbin/',
             'gzip";\ndata = /incbin/', "FIT: /images/fdt_2 is compressed")):
        expect(f"FIT: {name}", lambda: extracted(published(
            fit=text("fit.dts", old, new))), tag)
    (scratch / "wrong.txt").write_text(
        f"published {FIT_NAME} sha256={'0' * 64} bytes=1\n")
    expect("PIN: a copy that is not its pin's", lambda: extracted(
        good, pins=scratch / "wrong.txt"), "PIN: the copy")
    for name, old, new, tag in (
            ("STEP1: no root memory node", "memory@80000000 {", "m@8 {",
             "STEP1: 0 root memory nodes"),
            ("STEP1: two root memory nodes", "\tchosen {",
             'memory@c0000000 {\ndevice_type = "memory";\n'
             "reg = <0x0 0xc0000000 0x0 0x1000>;\n};\nchosen {",
             "STEP1: 2 root memory nodes"),
            ("STEP1: 32-bit root cells", "#address-cells = <0x02>;\n\t#size",
             "#address-cells = <0x01>;\n\t#size", "STEP1: the root's cells"),
            ("STEP1: no /chosen", "\tchosen {", "x {",
             "STEP1: 1 root memory nodes, or no /chosen"),
            ("STEP2: no jedec,spi-nor node", '"jedec,spi-nor"', '"x,nor"',
             "STEP2: no jedec,spi-nor"),
            ("STEP2: a flash node under the root", "\tsoc {",
             'flash@0 {\ncompatible = "jedec,spi-nor";\nreg = <0x0 0x0 0x0 '
             '0x1>;\n};\nsoc {', "STEP2: no jedec,spi-nor"),
            ("STEP2: two enabled flash controllers", "\t\t\teeprom@50 {",
             'flash@1 {\ncompatible = "jedec,spi-nor";\nreg = <0x01>;\n};\n'
             "eeprom@50 {", "STEP2: 2 enabled"),
            ("STEP3: no RPMI mailbox", '"riscv,rpmi-shmem-mbox"', '"x,box"',
             "STEP3: 0 RPMI"),
            ("STEP3: two RPMI mailboxes", "\t\tfuse@37000000 {",
             'mailbox@36100000 {\ncompatible = "riscv,rpmi-shmem-mbox";\n};\n'
             "fuse@37000000 {", "STEP3: 2 RPMI"),
            ("STEP3: no node names the mailbox", "mboxes", "x,boxes",
             "STEP3: no node names"),
            ("STEP3: mboxes names no node", "<0x40 0x01>", "<0x41 0x01>",
             "STEP3: /soc/clock@0:mboxes names no node"),
            ("STEP3: mboxes ends inside a specifier", "<0x40 0x01>",
             "<0x40>", "STEP3: /soc/clock@0:mboxes ends"),
            ("STEP3: a mailbox with no #mbox-cells", "#mbox-cells = <0x01>;",
             "", "STEP3: /soc/mailbox@36000000 has no")):
        expect(name, lambda: extracted(published(
            board=text("board.dts", old, new))), tag)
    for name, key, field, value, tag in (
            ("STEP1: a memory of two banks", "memory", "size", "0x60000000",
             "STEP1: the memory's size"),
            ("STEP1: a boot hart that is not a number", "boot_hart", "value",
             "0", "STEP1: the boot hart"),
            ("a number not in hex", "memory", "base", "4096",
             "'4096' is not a hex number")):
        odd = copy.deepcopy(facts)
        odd[key][field] = value
        expect(name, lambda: extracted(good, changed=odd), tag)
    expect("STEP2: a change that is not the step's", lambda: extracted(
        good, extra={2: "&{/soc/serial@30000000} { reg-shift = <0x0>; };"}),
           "STEP2: /soc/serial@30000000 differs")
    expect("dtc: a source that it refuses", lambda: extracted(
        good, extra={1: "&{/x} { };"}), f"{tool} failed")

    def alone(rule, edit=None):
        lone = FDT.private_directory(scratch / f"lone-{next(runs)}")
        shutil.copyfile(work / "step0.dts", lone / "step0.dts")
        before = FDT.parse_fdt((work / "step0.dtb").read_bytes())
        if edit:
            edit(before)
        return step(lone, tool, 1, before, rule, facts, (set(), set()))

    for name, rule, edit, tag in (
            ("a dtc warning that step 0 does not draw", memory, None,
             "STEP1: dtc warns"),
            ("the nodes' order changed", memory, lambda fdt:
             fdt.order.reverse(), "STEP1: the nodes' order"),
            ("the reserve map changed", memory, lambda fdt:
             fdt.reserves.append((0, 1)), "STEP1: the nodes' order"),
            ("a node that it disables left enabled", lambda fdt, facts: (
                [], {}, ["/soc/serial@30000000"]), None,
             "STEP1: a node that")):
        expect(f"STEP1: {name}", lambda: alone(rule, edit), tag)

    def fake(name, line):
        (scratch / name).write_text(f'#!/bin/sh\n{line}\nexec {tool} "$@"\n')
        (scratch / name).chmod(0o700)
        return scratch / name

    expect("dtc: a line that is not a warning", lambda: dtc(fake(
        "dtc-says", "echo said >&2"), fixtures / "qemu.dts", scratch / "x"),
           "dtc said: said")
    expect("STEP0: a tree that the round trip changes", lambda: extract(
        good / FIT_NAME, good / "pins.txt", facts, fake(
            "dtc-sorts", f'case "$*" in *again*) exec {tool} -s "$@";; esac'),
        scratch / "sorted"), "STEP0:")
    expect("PIN: a FIT that is not a regular file", lambda: extract(
        scratch, good / "pins.txt", facts, tool, scratch / "irregular"),
           f"PIN: {scratch} is not")
    expect("RECIPE: two runs that differ", lambda: same_files(
        work, fixtures), "RECIPE:")
    (scratch / "twice.json").write_text('{"a": 1, "a": 2}')
    expect("JSON: a key given twice", lambda: strict_json(
        scratch / "twice.json"), f"{scratch / 'twice.json'} repeats")
    bad, others = platform(facts, work, scratch / "devices.json")
    expect("platform: the stand-in's facts; its other devices", lambda:
           require(not bad and "other: /soc/gpio@39000000 made-up,gpio" in
                   others, f"{bad} {others}"))

    def device(changed, path):
        return next(row for row in changed["devices"]["list"]
                    if row["path"] == path)

    for name, edit, tag in (
            ("the schema", lambda f: f.update(schema="x"), "SCHEMA"),
            ("a fact with no source", lambda f: f["model"].pop("source"),
             "SOURCE: model"),
            ("the model", lambda f: f["model"].update(value="x"), "MODEL"),
            ("the root's cells", lambda f: f["cells"].update(address=1),
             "CELLS"),
            ("the tree's memory", lambda f: f["tree_memory"].update(
                size="0x20000000"), "TREE_MEMORY"),
            ("the board's memory", lambda f: f["memory"].update(
                size="0x40000000"), "MEMORY"),
            ("the hart count", lambda f: f["harts"].update(count=15),
             "HARTS: ids"),
            ("the harts with h", lambda f: f["harts"]["hypervisor"].pop(),
             "HARTS: hypervisor"),
            ("the cache block", lambda f: f["harts"].update(cache_block=32),
             "HARTS: cache block"),
            ("the firmware's end", lambda f: f["firmware"].update(
                end_max="0x80200000"), "FIRMWARE"),
            ("a root device's base", lambda f: f["root_devices"][
                "console"].update(base="0x30000100"), "ROOT: console"),
            ("a root device disabled", lambda f: f["root_devices"][
                "aplic-m"].update(path="/soc/gpio@39000000", base="0x39000000",
                                  compatible="made-up,gpio"), "ROOT: aplic-m"),
            ("the console's scratch register", lambda f: f["breach"][
                "console_scratch"].update(offset="0x7"),
             "BREACH: console_scratch"),
            ("the S-level files' stride", lambda f: f["breach"][
                "imsic_s"].update(stride="0x1000"), "BREACH: imsic_s"),
            ("the timer's width", lambda f: f["breach"].update(
                timer_width=8), "BREACH: timer_width"),
            ("an enabled device not named", lambda f: f["devices"][
                "list"].pop(), "DEVICES: /soc/usb@0/dwc@3a000000 is not"),
            ("a device the tree lacks", lambda f: f["devices"][
                "list"].append({"path": "/x@1"}), "DEVICES: /x@1 not in"),
            ("a device's status", lambda f: device(
                f, "/soc/fuse@37000000").update(status="disabled"),
             "DEVICES: /soc/fuse@37000000 differs"),
            ("a kind that is not B-10's", lambda f: device(
                f, "/soc/serial@30000000").update(kind="x"),
             "KIND: /soc/serial@30000000"),
            ("a path named twice", lambda f: f["devices"]["list"].append(
                f["devices"]["list"][0]), "DEVICES: a path named twice")):
        changed = copy.deepcopy(facts)
        edit(changed)
        bad = platform(changed, work, scratch / f"devices-{next(runs)}")[0]
        expect(f"platform: {name}", lambda: require(
            len(bad) == 1 and bad[0].startswith(tag), f"{bad}"))
    old = 'reg = <0x04>;\n\t\t\triscv,isa-extensions = "'
    bad = platform(facts, extracted(published(board=text(
        "board.dts", old, old + 'smepmp", "'))), scratch / "smepmp")[0]
    expect("platform: a hart that lists smepmp", lambda: require(
        bad == ["HARTS: smepmp"], f"{bad}"))
    expect("platform: two CPU nodes of one hart", lambda: platform(
        facts, extracted(published(board=text(
            "board.dts", "<0x0f>", "<0x0e>"))), scratch / "twice"),
           "/cpus/cpu@15 is not one hart")
    identity = FDT.sha(fixtures / "descriptor.json")
    (scratch / "identity.h").write_text(
        f'#define BE_MVP_PARTITION_IDENTITY_HEX "{identity}"\n')

    def rendered(base, park, old="", new=""):
        top = scratch / f"render-{next(runs)}"
        top.mkdir()
        shutil.copyfile(base, top / "base.dts")
        (top / "tree.dts").write_text('/include/ "base.dts"\n' + text(
            "render.dtsi", old, new).replace("@DIGEST@", " ".join(
                "0x" + identity[at:at + 8] for at in range(0, 64, 8))).replace(
                    "@PARK@", " ".join(f"&{{/cpus/cpu@{index}}}" for index
                                       in park)))
        dtc(tool, top / "tree.dts", top / "tree.dtb")
        return top / "tree.dtb"

    step3, park = work / "step3.dts", range(3, 16)
    board = rendered(step3, park)
    qemu = rendered(fixtures / "qemu.dts", range(3, 8))

    def tried(path, qemu=qemu, descriptor=fixtures / "descriptor.json",
              header=scratch / "identity.h"):
        return tree(work, path, qemu, descriptor, header)

    sorted_ = scratch / "sorted.dtb"
    FDT.run([str(tool), "-s", "-I", "dts", "-O", "dtb", "-o", str(sorted_),
             str(board.parent / "tree.dts")])
    reserved = scratch / "reserved.dts"
    reserved.write_text(step3.read_text(encoding="utf-8").replace(
        "/dts-v1/;\n", "/dts-v1/;\n/memreserve/ 0x80000000 0x1000;\n", 1),
        encoding="utf-8")

    for name, action, tag in (
            ("the descriptor's nodes alone", lambda: tried(board), None),
            ("a node of step 3 gone", lambda: tried(rendered(
                step3, park, "/ {\n\tchosen {", "/delete-node/ &{/soc/fuse@"
                "37000000};\n/ {\n\tchosen {")), "TREE: a node of step 3"),
            ("step 3's order changed", lambda: tried(sorted_),
             "TREE: step 3's"),
            ("step 3's reserve map changed", lambda: tried(rendered(
                reserved, park)), "TREE: step 3's"),
            ("a QEMU tree without be_park", lambda: tried(board, qemu=rendered(
                fixtures / "qemu.dts", range(3, 8), "be_park {", "x {")),
             "TREE: the QEMU tree has no be_park"),
            ("a node beyond the descriptor's", lambda: tried(rendered(
                step3, park, "\t\topensbi-domains {",
                "x {\n};\nopensbi-domains {")), "TREE: a node"),
            ("a property of step 3 changed", lambda: tried(rendered(
                step3, park, "\tchosen {", 'chosen {\nstdout-path = "x";')),
             "TREE: /chosen differs"),
            ("another descriptor", lambda: tried(
                board, descriptor=fixtures / "platform.json"),
             "IDENTITY: a config-digest"),
            ("another identity header", lambda: tried(
                board, header=fixtures / "descriptor.json"),
             "IDENTITY: the identity header"),
            ("be_park without hart 15", lambda: tried(rendered(
                step3, range(3, 15))), "TREE: the OpenSBI domains"),
            ("a region's access differs", lambda: tried(rendered(
                step3, park, "0x38>", "0x30>")), "TREE: the OpenSBI domains"),
            ("boundary off: step 3", lambda: tree(work, work / "step3.dtb"),
             None),
            ("boundary off: another tree", lambda: tree(work, board),
             "TREE: the boundary-off")):
        expect(f"tree: {name}", action, tag)
    record = strict_json(work / "recipe.json")
    end = number(record["load"]) + record["loadable_bytes"] + SPARE + \
        board.stat().st_size
    for name, last, tag in (("a tree that fits to the byte", end, None),
                            ("a tree a byte too large", end - 1, "ROOM")):
        changed = copy.deepcopy(facts)
        changed["spl_tree"]["room_end"] = hex(last)
        expect(f"room: {name}", lambda: room(work, changed, [board]), tag)
    print(f"{TAG}: {'PASS' if all(results) else 'FAIL'} self-test "
          f"cases={len(results)}")
    return 0 if all(results) else 1


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    for option in ("--dtc", "--fixtures", "--scratch"):
        parser.add_argument(option, type=pathlib.Path)
    commands = parser.add_subparsers(dest="command")
    for name, options in (
            ("extract", "fit! pins! platform! dtc! out! twice"),
            ("platform", "platform! dir! out!"),
            ("tree", "dir! tree! qemu-tree descriptor identity-header"),
            ("room", "dir! platform!")):
        command = commands.add_parser(name)
        for option in options.split():
            command.add_argument("--" + option.rstrip("!"), type=pathlib.Path,
                                 required=option.endswith("!"))
    commands.choices["room"].add_argument("trees", nargs="+",
                                          type=pathlib.Path)
    args = parser.parse_args(argv[1:])
    if args.self_test == bool(args.command) or args.self_test and None in (
            args.dtc, args.fixtures, args.scratch):
        parser.error("give one of extract, platform, tree, room, or "
                     "--self-test --dtc DTC --fixtures DIR --scratch DIR")
    try:
        if args.self_test:
            return self_test(args.dtc, args.fixtures.resolve(),
                             args.scratch.resolve())
        facts = strict_json(args.platform) if getattr(
            args, "platform", None) else None
        if args.command == "extract":
            lines = extract(args.fit, args.pins, facts, args.dtc, args.out,
                            args.twice)
        elif args.command == "platform":
            bad, lines = platform(facts, args.dir, args.out)
            lines = [f"finding: {row}" for row in bad] + lines + [
                f"{TAG}: {'FAIL' if bad else 'PASS'} platform "
                f"findings={len(bad)} other={len(lines)}"]
        elif args.command == "tree":
            given = (args.qemu_tree, args.descriptor, args.identity_header)
            require(given.count(None) in (0, 3), "give --qemu-tree, "
                    "--descriptor, and --identity-header, or none")
            lines = tree(args.dir, args.tree, *given)
        else:
            lines = room(args.dir, facts, args.trees)
    except (Refused, FRAME.Refused, OSError, ValueError, KeyError, TypeError,
            IndexError, struct.error, subprocess.SubprocessError) as error:
        print(f"{TAG}: FAIL refused: {error}")
        return 1
    print("\n".join(lines))
    return 1 if lines[-1].startswith(f"{TAG}: FAIL") else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
