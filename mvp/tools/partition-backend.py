#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""Render an OpenSBI device tree and expected PMP tables from a descriptor.

--control-hart boot (M11-7, step 1) renders no OpenSBI domain for hart 0,
which stays in be_boot; confined (M11-8, step 2), the default, renders
M11-5's tree, with be_control. The tables name their step either way
("control_hart").

--platform k3-com260 (M11-B, B-3) is the board, from the facts of
--platform-file (mvp/k3/platform.json): --board-tree renders onto the
recipe's step 3, --board-tables writes the board's plain-PMP tables and
the root OpenSBI domain's regions as its banner prints them, and
--self-test runs the board's cases. The default, k3-like, is unchanged."""

import argparse
import contextlib
import dataclasses
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
FDT_MAGIC = 0xD00DFEED
FDT_BEGIN_NODE, FDT_END_NODE, FDT_PROP, FDT_NOP, FDT_END = 1, 2, 3, 4, 9
PMP_A_NAPOT, PMP_R, PMP_W, PMP_X, PMP_L = 0x18, 1, 2, 4, 0x80
TABLE_SCHEMA = "be-pmp-tables-v1"
ROOT_SCHEMA = "be-mvp-k3-root-v1"
HEX = re.compile(r"0x(?:0|[1-9a-f][0-9a-f]*)\Z")


class Refused(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Refused(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) +
            "\n").encode()


def sha(path):
    value = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def private_directory(path):
    path = pathlib.Path(path)
    require(not path.exists(), f"output {path} already exists")
    path.mkdir(mode=0o700, parents=True)
    require(path.stat().st_mode & 0o077 == 0, f"output {path} is not private")
    return path


def write_new(path, data):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "wb") as output:
        output.write(data)


def run(command, cwd=None):
    result = subprocess.run(command, cwd=cwd, check=False,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(result.returncode == 0, f"{command[0]} failed: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}")
    return result


def warning_set(data):
    out = []
    for line in data.decode("utf-8", "replace").splitlines():
        if "Warning " in line:
            out.append("Warning " + line.split("Warning ", 1)[1])
        elif line.strip():
            out.append(line.strip())
    return sorted(out)


def align4(value):
    return (value + 3) & ~3


def cstring(data, offset):
    end = data.find(b"\0", offset)
    require(end >= 0, "FDT string has no terminator")
    return data[offset:end].decode("ascii")


def strings(value):
    require(value.endswith(b"\0"), "FDT string list is not terminated")
    return [item.decode("ascii") for item in value[:-1].split(b"\0")]


def cells(value):
    require(len(value) % 4 == 0, "FDT cell property has partial cell")
    return list(struct.unpack(f">{len(value) // 4}I", value))


@dataclasses.dataclass
class Property:
    value: bytes
    start: int
    end: int


@dataclasses.dataclass
class Fdt:
    data: bytes
    nodes: dict
    order: list
    reserves: list
    struct_offset: int


def parse_fdt(data):
    require(len(data) >= 40, "FDT header is short")
    header = struct.unpack_from(">10I", data)
    magic, total, struct_at, strings_at, reserve_at, version, last, _, \
        strings_size, struct_size = header
    require(magic == FDT_MAGIC and total == len(data) and version >= 17 and
            last <= version and struct_at + struct_size <= total and
            strings_at + strings_size <= total and reserve_at < total,
            "FDT header is malformed")
    reserves, at = [], reserve_at
    while True:
        require(at + 16 <= total, "FDT reserve map is truncated")
        address, size = struct.unpack_from(">QQ", data, at)
        at += 16
        if not address and not size:
            break
        reserves.append((address, size))
    names = data[strings_at:strings_at + strings_size]
    at, end, stack, nodes, order = struct_at, struct_at + struct_size, [], {}, []
    while at < end:
        token_at = at
        token, = struct.unpack_from(">I", data, at)
        at += 4
        if token == FDT_BEGIN_NODE:
            name = cstring(data, at)
            at = align4(at + len(name) + 1)
            stack.append(name)
            path = "/" + "/".join(item for item in stack if item)
            require(path not in nodes, f"FDT duplicate node {path}")
            nodes[path] = {}
            order.append(path)
        elif token == FDT_END_NODE:
            require(stack, "FDT unmatched end node")
            stack.pop()
        elif token == FDT_PROP:
            require(stack and at + 8 <= end, "FDT property outside node")
            length, name_at = struct.unpack_from(">II", data, at)
            at += 8
            require(name_at < len(names) and at + length <= end,
                    "FDT property is out of bounds")
            name = cstring(names, name_at)
            path = "/" + "/".join(item for item in stack if item)
            require(name not in nodes[path],
                    f"FDT duplicate property {path}:{name}")
            finish = align4(at + length)
            nodes[path][name] = Property(data[at:at + length], token_at, finish)
            at = finish
        elif token == FDT_NOP:
            continue
        elif token == FDT_END:
            require(not stack, "FDT ended inside a node")
            break
        else:
            raise Refused(f"FDT unknown token {token:#x}")
    require(token == FDT_END and at == end, "FDT has data after its end token")
    return Fdt(data, nodes, order, reserves, struct_at)


def without_rng(data):
    fdt = parse_fdt(data)
    seed = fdt.nodes.get("/chosen", {}).get("rng-seed")
    require(seed is not None and len(seed.value) == 32,
            "BASE-RNG: no one 32-byte /chosen/rng-seed")
    patched = bytearray(data)
    for at in range(seed.start, seed.end, 4):
        struct.pack_into(">I", patched, at, FDT_NOP)
    return bytes(patched)


def after_end(data):
    _, total, struct_at, strings_at, _, _, _, _, _, struct_size = \
        struct.unpack_from(">10I", data)
    at = struct_at + struct_size
    out = bytearray(data[:at] + struct.pack(">I", FDT_NOP) + data[at:])
    struct.pack_into(">I", out, 4, total + 4)
    struct.pack_into(">I", out, 12, strings_at + 4)
    struct.pack_into(">I", out, 36, struct_size + 4)
    return bytes(out)


def prop(fdt, path, name, required=True):
    row = fdt.nodes.get(path, {}).get(name)
    if required:
        require(row is not None, f"FDT lacks {path}:{name}")
    return None if row is None else row.value


def parent(path):
    return path.rsplit("/", 1)[0] or "/"


def cell_count(fdt, path, name, default):
    value = prop(fdt, path, name, False)
    if value is None:
        return default
    row = cells(value)
    require(len(row) == 1, f"{path}:{name} is not one cell")
    return row[0]


def reg(fdt, path):
    values = cells(prop(fdt, path, "reg"))
    p = parent(path)
    ac, sc = cell_count(fdt, p, "#address-cells", 2), \
        cell_count(fdt, p, "#size-cells", 1)
    width = ac + sc
    require(width and len(values) % width == 0, f"{path}:reg has wrong cells")

    def word(row):
        value = 0
        for cell in row:
            value = value << 32 | cell
        return value

    return [(word(values[at:at + ac]), word(values[at + ac:at + width]))
            for at in range(0, len(values), width)]


def compatible(fdt, path):
    value = prop(fdt, path, "compatible", False)
    return [] if value is None else strings(value)


def node_for_range(fdt, base, compatible_part):
    found = []
    for path in fdt.order:
        if compatible_part not in "\0".join(compatible(fdt, path)):
            continue
        try:
            ranges = reg(fdt, path)
        except Refused:
            continue
        if any(address == base for address, _ in ranges):
            found.append((path, ranges))
    require(len(found) == 1, f"base tree has {len(found)} {compatible_part} "
            f"nodes at {base:#x}")
    return found[0]


def node_in_window(fdt, base, size, compatible_part):
    found = []
    for path in fdt.order:
        if compatible_part not in "\0".join(compatible(fdt, path)):
            continue
        try:
            ranges = reg(fdt, path)
        except Refused:
            continue
        if ranges and all(base <= address and address + length <= base + size
                          for address, length in ranges):
            found.append((path, ranges))
    require(len(found) == 1, f"base tree has {len(found)} {compatible_part} "
            f"nodes in {base:#x}+{size:#x}")
    return found[0]


def normalize_dtb(raw, dtc, output, warnings, scratch):
    data = pathlib.Path(raw).read_bytes()
    patched = without_rng(data)
    scratch = private_directory(scratch)
    raw_name = scratch / "base.dtb"
    dts_name = scratch / "base.dts"
    write_new(raw_name, patched)
    result = run([str(dtc), "-I", "dtb", "-O", "dts", "-o",
                  dts_name.name, raw_name.name], cwd=scratch)
    text = dts_name.read_text(encoding="utf-8")
    header = ("// SPDX-License-Identifier: GPL-3.0-only\n"
              "// Copyright (C) 2026 James Morris <jmorris@namei.org>\n")
    write_new(output, (header + text).encode())
    compiled = scratch / "roundtrip.dtb"
    compile_result = run([str(dtc), "-I", "dts", "-O", "dtb", "-o",
                          compiled.name, str(pathlib.Path(output).resolve())],
                         cwd=scratch)
    write_new(warnings, canonical({
        "copyright": "Copyright (C) 2026 James Morris <jmorris@namei.org>",
        "compile": warning_set(compile_result.stderr),
        "decompile": warning_set(result.stderr),
        "spdx": "GPL-3.0-only",
    }))
    shutil.rmtree(scratch)


def check_normalized_base(raw, committed, expected_warnings, dtc, scratch):
    scratch = pathlib.Path(scratch)
    if scratch.exists():
        shutil.rmtree(scratch)
    generated = scratch.parent / f"{scratch.name}-generated.dts"
    warnings = scratch.parent / f"{scratch.name}-generated.warnings"
    for path in (generated, warnings):
        if path.exists():
            path.unlink()
    normalize_dtb(raw, dtc, generated, warnings, scratch)
    require(generated.read_bytes() == pathlib.Path(committed).read_bytes(),
            "fresh normalized base tree differs from the committed tree")
    require(warnings.read_bytes() ==
            pathlib.Path(expected_warnings).read_bytes(),
            "fresh base-tree dtc warning set differs")
    generated.unlink()
    warnings.unlink()
    print(f"BE_MVP_PARTITION_BASE: PASS tree={pathlib.Path(committed).name}")


@dataclasses.dataclass(frozen=True)
class Region:
    name: str
    base: int
    size: int
    m: tuple = ()
    su: tuple = ()
    firmware: bool = False
    shared: bool = False
    mmio: bool = False

    @property
    def order(self):
        return 64 if self.size == 1 << 64 else self.size.bit_length() - 1

    @property
    def flags(self):
        return self.m, self.su, self.firmware, self.shared


def memregion(address, size):
    require(size > 0 and address + size > address, "empty/wrapping region")
    order = (size - 1).bit_length()
    while order <= 64:
        if order == 64:
            return 0, 1 << 64
        base = address & ~((1 << order) - 1)
        if address + size <= base + (1 << order):
            return base, 1 << order
        order += 1
    raise Refused("region cannot be represented")


def dwarf_size(elf, readelf, type_name):
    text = run([str(readelf), "--debug-dump=info", str(elf)]).stdout.decode(
        "utf-8", "replace")
    blocks = re.split(r"(?=^\s*<[0-9]+><[0-9a-f]+>:)", text, flags=re.M)
    found = []
    for block in blocks:
        if "DW_TAG_structure_type" not in block or type_name not in block:
            continue
        name = re.search(r"DW_AT_name\s*:\s*(?:\([^)]*\):\s*)?([A-Za-z0-9_]+)",
                         block)
        size = re.search(r"DW_AT_byte_size\s*:\s*(0x[0-9a-f]+|[0-9]+)",
                         block)
        if name and name.group(1) == type_name and size:
            found.append(int(size.group(1), 0))
    unique = set(found)
    require(len(unique) == 1, f"firmware DWARF has sizes {sorted(unique)} "
            f"for {type_name}")
    return unique.pop()


def firmware_symbols(elf, nm, readelf):
    result = run([str(nm), "-n", str(elf)])
    wanted = {}
    for line in result.stdout.decode("ascii").splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[2] in (
                "_fw_start", "_fw_rw_start", "_fw_end"):
            require(fields[2] not in wanted, f"duplicate {fields[2]}")
            wanted[fields[2]] = int(fields[0], 16)
    require(set(wanted) == {"_fw_start", "_fw_rw_start", "_fw_end"} and
            wanted["_fw_start"] == 0 < wanted["_fw_rw_start"] <
            wanted["_fw_end"],
            "firmware ELF has no one ordered layout-symbol set")
    wanted["_tlb_info_size"] = dwarf_size(elf, readelf, "sbi_tlb_info")
    return wanted


def reset_regmap(fdt, target):
    """Whether OpenSBI adds TARGET's page to the root OpenSBI domain,
    TARGET an enabled syscon (QEMU's test device): it does when an enabled
    syscon-poweroff or syscon-reboot node's regmap names TARGET
    (lib/utils/reset/fdt_reset_syscon.c,
    lib/utils/regmap/fdt_regmap_syscon.c), and not otherwise."""
    handles = {cells(value)[0] for value in (
        prop(fdt, target, name, False) for name in ("phandle",
                                                    "linux,phandle"))
        if value is not None and len(value) == 4}
    for path in fdt.order:
        status, regmap = (prop(fdt, path, name, False)
                          for name in ("status", "regmap"))
        if regmap is not None and len(regmap) >= 4 and \
                cells(regmap[:4])[0] in handles and \
                (status is None or status.startswith(b"ok")) and \
                {"syscon-poweroff", "syscon-reboot"} & set(
                    compatible(fdt, path)):
            return True
    return False


def firmware_regions(firmware, load, harts):
    """The root OpenSBI domain's two firmware regions: the build's layout
    symbols at LOAD, and HARTS harts' stacks and heap after _fw_end
    (platform/generic/platform.c, fw_platform_calculate_heap_size)."""
    start, rw, linked_end = (firmware[name] + load for name in (
        "_fw_start", "_fw_rw_start", "_fw_end"))
    stack = harts * 8192
    heap = 0x8000 + 0x1000 * harts + \
        firmware["_tlb_info_size"] * harts * harts
    heap = (heap + 1023) & ~1023
    end = linked_end + stack + heap
    rx_base, rx_size = memregion(start, rw - start)
    rw_base, rw_size = memregion(rw, end - rw)
    return [Region("firmware-rw", rw_base, rw_size, ("read", "write"),
                   firmware=True),
            Region("firmware-rx", rx_base, rx_size, ("read", "execute"),
                   firmware=True)]


def platform(fdt, firmware):
    memory = [path for path in fdt.order
              if prop(fdt, path, "device_type", False) == b"memory\0"]
    require(len(memory) == 1, "base tree does not have one memory node")
    ram = reg(fdt, memory[0])[0]
    require(ram == (0x80000000, 0x200000000),
            f"base tree RAM is {ram}, not k3-like's")
    test_path, _ = node_for_range(fdt, 0x100000, "sifive,test")
    uart_path, _ = node_for_range(fdt, 0x10000000, "ns16550")
    aplic_path, aplic_regs = node_for_range(fdt, 0x0C000000, "riscv,aplic")
    imsic_path, imsic_regs = node_for_range(fdt, 0x24000000, "riscv,imsics")
    timer_path, timer_regs = node_in_window(fdt, 0x02000000, 0x10000,
                                            "riscv,clint0")
    require(reg(fdt, test_path)[0][1] <= 0x1000 and
            reg(fdt, uart_path)[0][1] <= 0x1000,
            "test or UART device exceeds its OpenSBI page")
    aplic_size = next(size for base, size in aplic_regs if base == 0x0C000000)
    imsic_size = next(size for base, size in imsic_regs if base == 0x24000000)
    timer_end = max(base + size for base, size in timer_regs)
    require(aplic_size == 0x8000 and imsic_size == 0x8000 and
            timer_end <= 0x2010000, "k3-like interrupt ranges changed")
    rows = firmware_regions(firmware, ram[0], 8) + [
        Region("test-device", 0x100000, 0x1000, ("read", "write"),
               ("read", "write"), shared=True),
        Region("uart", 0x10000000, 0x1000, ("read", "write"),
               ("read", "write"), shared=True),
        Region("aplic-m", 0x0C000000, aplic_size, ("read", "write")),
        Region("imsic-m", 0x24000000, imsic_size, ("read", "write")),
        Region("aclint-mtimer", 0x02000000, 0x10000, ("read", "write")),
        Region("all-addresses", 0, 1 << 64, (), ("read", "write", "execute")),
    ]
    return [row for row in rows
            if row.name != "test-device" or reset_regmap(fdt, test_path)]


def board_facts(path):
    """The board's description, mvp/k3/platform.json's form (B-3), read
    as data: the backend takes its harts, memory, firmware, and root
    devices."""
    value = json.loads(pathlib.Path(path).read_bytes())
    require(isinstance(value, dict) and
            value.get("schema") == "be-mvp-k3-platform-v1",
            f"{path} is not a board description")
    return value


def number(text):
    require(isinstance(text, str) and HEX.match(text),
            f"{text!r} is not a hex number")
    return int(text, 16)


def harts_by_reg(fdt, count):
    """{hart: CPU node}: each enabled CPU node by its reg, as the generic
    platform counts harts; they must be harts 0 to COUNT - 1."""
    out = {}
    for path in fdt.order:
        if parent(path) == "/cpus" and prop(
                fdt, path, "device_type", False) == b"cpu\0" and prop(
                    fdt, path, "status", False) in (None, b"okay\0",
                                                    b"ok\0"):
            rows = reg(fdt, path)
            require(len(rows) == 1 and rows[0][0] not in out,
                    f"{path} is not one hart of its own")
            out[rows[0][0]] = path
    require(sorted(out) == list(range(count)),
            f"the tree's harts are not 0 to {count - 1}")
    return out


def board_devices(fdt, facts):
    """The root devices' regions on the board's tree, as the firmware base
    makes them (lib/utils/serial/uart8250.c, irqchip/aplic.c and
    imsic.c, timer/aclint_mtimer.c): the console's page, shared; the
    M-level APLIC and IMSIC, each its reg's one region; the CLINT's
    64 KiB; each found by compatible at its fact's base and path. The
    tree's one memory node must be the board's memory, and no enabled
    syscon reset node may name a regmap, whose page the firmware would add
    to the root OpenSBI domain (lane F's rule finds none)."""
    memory = [path for path in fdt.order
              if prop(fdt, path, "device_type", False) == b"memory\0"]
    require(len(memory) == 1 and reg(fdt, memory[0]) == [(number(
        facts["memory"]["base"]), number(facts["memory"]["size"]))],
            "the tree's memory is not the board's")
    require(not any(prop(fdt, path, "regmap", False) is not None and
                    prop(fdt, path, "status", False) in (None, b"okay\0",
                                                         b"ok\0") and
                    {"syscon-poweroff", "syscon-reboot"} &
                    set(compatible(fdt, path)) for path in fdt.order),
            "the tree has a syscon reset node")
    rows = []
    for key, name in (("console", "uart"), ("aplic-m", "aplic-m"),
                      ("imsic-m", "imsic-m"), ("clint", "aclint-mtimer")):
        fact = facts["root_devices"][key]
        base = number(fact["base"])
        path, ranges = node_in_window(
            fdt, base, 0x10000, fact["compatible"]) if key == "clint" \
            else node_for_range(fdt, base, fact["compatible"])
        size = {"console": 0x1000, "clint": 0x10000}.get(key) or next(
            length for address, length in ranges if address == base)
        require(path == fact["path"] and ranges[0][1] <= size and
                size & (size - 1) == 0 and base % size == 0,
                f"{key} at {path} is not one region of the board's")
        rows.append(Region(name, base, size, ("read", "write"), (
            "read", "write") if key == "console" else (),
                           shared=key == "console", mmio=True))
    return rows


def platform_k3(fdt, firmware, facts):
    """The root OpenSBI domain's regions on the board, as platform() gives
    k3-like's: the firmware's two at its load address, with the board's
    harts, ending by firmware.end_max; the root devices; and every
    address, S/U RWX."""
    count = facts["harts"]["count"]
    harts_by_reg(fdt, count)
    rows = firmware_regions(firmware, number(facts["firmware"]["load"]),
                            count)
    require(all(row.base + row.size <= number(facts["firmware"]["end_max"])
                for row in rows), "the firmware's regions pass end_max")
    return rows + board_devices(fdt, facts) + [
        Region("all-addresses", 0, 1 << 64, (), ("read", "write", "execute"))]


def banner(row):
    """ROW as the firmware's banner prints a region of an OpenSBI domain,
    after its name (lib/sbi/sbi_domain.c, sbi_domain_dump)."""
    def marks(first, rights):
        return "(" + ",".join(first + [mark for right, mark in (
            ("read", "R"), ("write", "W"), ("execute", "X"))
            if right in rights]) + ")"
    end = (1 << 64) - 1 if row.order == 64 else row.base + row.size - 1
    return (f"0x{row.base:016x}-0x{end:016x} M: " +
            marks(["I"] * row.mmio + ["F"] * row.firmware, row.m) +
            " S/U: " + marks([], row.su))


def board_compile(dtc, source, output, include=None):
    """dtc's warning set for SOURCE compiled to OUTPUT: each warning's
    "also defined at" lines, which a node defined twice draws, read as
    the warning's own."""
    result = run([str(dtc), "-I", "dts", "-O", "dtb"] + (
        ["-i", str(include)] if include else []) + ["-o", str(output),
                                                    str(source)])
    return warning_set(b"\n".join(
        line for line in result.stderr.splitlines()
        if not line.startswith(b"  also defined at ")))


def board_base(dtc, base, output):
    """Step 3 compiled alone in OUTPUT, a new private directory: its
    warning set and tree."""
    output = private_directory(output)
    warnings = board_compile(dtc, base, output / "base.dtb")
    fdt = parse_fdt((output / "base.dtb").read_bytes())
    (output / "base.dtb").unlink()
    return output, warnings, fdt


def board_tree(descriptor_path, image, base, facts, dtc, output, control):
    """Step 4 (B-3): the descriptor rendered onto the recipe's step 3, its
    harts the board's CPU nodes by reg, be_park the descriptor's parked
    harts and every hart of the board beyond its own; the joined tree may
    change no dtc warning of step 3's, found in the same run."""
    value, identity = strict_descriptor(descriptor_path)
    name, base = image or value["image"], pathlib.Path(base).resolve()
    output, expected, fdt = board_base(dtc, base, output)
    count = facts["harts"]["count"]
    cpus = harts_by_reg(fdt, count)
    board_devices(fdt, facts)
    park = [row["hart"] for row in value["harts"] if row["role"] ==
            "parked"] + list(range(len(value["harts"]), count))
    source = output / f"{name}.dts"
    write_new(source, render_tree(value, identity, base.name, control, cpus,
                                  park).encode())
    require(board_compile(dtc, source, output / f"{name}.dtb", base.parent)
            == expected, "the joined tree's dtc warnings differ from step 3's")
    parse_fdt((output / f"{name}.dtb").read_bytes())
    print(f"BE_MVP_PARTITION_BACKEND: PASS board-tree image={name} "
          f"identity={identity[:12]} park={park[0]}-{park[-1]}")


def board_tables(descriptor_path, image, base, facts, firmware_elf, dtc,
                 nm, readelf, output, control):
    """The board's expected tables, plain PMP alone (B-6), for every hart
    of the board, with a descriptor; and always the root OpenSBI domain's
    regions as the banner prints them: from the build's own ELF and the
    recipe's step 3."""
    value, identity = strict_descriptor(descriptor_path) if \
        descriptor_path else (None, None)
    name, base = image or value["image"], pathlib.Path(base).resolve()
    symbols = firmware_symbols(firmware_elf, nm, readelf)
    output, _, fdt = board_base(dtc, base, output)
    roots = platform_k3(fdt, symbols, facts)
    hashes = sha(firmware_elf), sha(base)
    if value is not None:
        write_new(output / f"{name}-pmp.json", canonical(expected_tables(
            value, identity, roots, *hashes, control,
            facts["harts"]["count"], ("plain",))))
    regions = [banner(row) for row in sorted_regions(roots)]
    write_new(output / f"{name}-root.json", canonical({
        "schema": ROOT_SCHEMA, "image": name, "firmware_sha256": hashes[0],
        "base_tree_sha256": hashes[1], "regions": regions}))
    print(f"BE_MVP_PARTITION_BACKEND: PASS board-tables image={name} "
          f"tables={'no' if value is None else 'plain'} "
          f"root_regions={len(regions)}")


def strict_descriptor(path):
    data = pathlib.Path(path).read_bytes()
    value = json.loads(data)
    require(value.get("schema") == "be-partition-v1" and
            canonical(value) == data, "descriptor is not canonical v1")
    return value, hashlib.sha256(data).hexdigest()


def combine(profile, extents):
    rows = [Region(row["extent"], int(extents[row["extent"]]["base"], 16),
                   int(extents[row["extent"]]["size"], 16), (),
                   tuple(row["rights"])) for row in profile["access"]]
    rows.sort(key=lambda row: (row.base, row.size, row.name))
    changed = True
    while changed:
        changed, out, at = False, [], 0
        while at < len(rows):
            if at + 1 < len(rows):
                left, right = rows[at:at + 2]
                size = left.size + right.size
                if (left.su == right.su and left.base + left.size ==
                        right.base and size & (size - 1) == 0 and
                        left.base % size == 0):
                    out.append(Region(f"{left.name}+{right.name}", left.base,
                                      size, (), left.su))
                    at += 2
                    changed = True
                    continue
            out.append(rows[at])
            at += 1
        rows = out
    return rows


def sorted_regions(rows):
    rows = sorted(rows, key=lambda row: (
        0 if row.firmware else 1, row.order, row.base))
    out = []
    for at, row in enumerate(rows):
        if any(row.flags == later.flags and
               later.base <= row.base and
               row.base + row.size <= later.base + later.size
               for later in rows[at + 1:]):
            continue
        out.append(row)
    return out


def pmp_address(region):
    if region.order == 64:
        return (1 << 64) - 1
    mask = (1 << (region.order - 2)) - 1
    return ((region.base >> 2) & ~mask) | (mask >> 1)


def config(region, mode):
    rights = {"read": PMP_R, "write": PMP_W, "execute": PMP_X}
    if mode == "plain":
        return PMP_A_NAPOT | sum(rights[right] for right in region.su)
    if region.shared:
        require(region.m == ("read", "write") and
                region.su == ("read", "write"), "unsupported shared region")
        return PMP_A_NAPOT | PMP_W | PMP_X
    if region.m and not region.su:
        return PMP_A_NAPOT | PMP_L | sum(rights[right] for right in region.m)
    require(region.su and not region.m, "unsupported Smepmp region")
    return PMP_A_NAPOT | sum(rights[right] for right in region.su)


def table(rows, mode):
    entries = []
    if mode == "smepmp":
        entries.append({"index": 0, "config": "0x00",
                        "address": "not-compared", "region": "reserved"})
    for row in sorted_regions(rows):
        require(len(entries) < 16, "profile exceeds sixteen PMP entries")
        entries.append({"index": len(entries), "config":
                        f"0x{config(row, mode):02x}",
                        "address": hex(pmp_address(row)), "region": row.name})
    while len(entries) < 16:
        entries.append({"index": len(entries), "config": "0x00",
                        "address": "not-compared", "region": "off"})
    return entries


def zero_table():
    return [{"index": index, "config": "0x00",
             "address": "not-compared", "region": "off"}
            for index in range(16)]


def expected_tables(value, identity, roots, firmware_sha, base_sha,
                    control="confined", harts=8, modes=("plain", "smepmp")):
    extents = {row["name"]: row for row in value["extents"]}
    profiles = {row["hart"]: combine(row, extents)
                for row in value["profiles"]}
    require(all(len(rows) <= 10 for rows in profiles.values()),
            "an own profile exceeds ten entries")
    inherited = [row for row in roots if row.firmware or
                 (row.m and not row.su)]
    result = {"schema": TABLE_SCHEMA, "descriptor_identity": identity,
              "firmware_sha256": firmware_sha, "base_tree_sha256": base_sha,
              "control_hart": control, "modes": {}}
    for mode in modes:
        boot = table(roots, mode)
        tables = []
        for hart in range(harts):
            tables.append({"hart": hart, "state": "never-started",
                           "entries": zero_table()})
            if hart in profiles:
                tables += [
                    {"hart": hart, "state": "boot", "entries": boot},
                    {"hart": hart, "state": "confined",
                     "profile": next(row["name"] for row in value["profiles"]
                                     if row["hart"] == hart),
                     "entries": table(profiles[hart] + inherited, mode)},
                ][:1 if (hart, control) == (0, "boot") else 2]
        result["modes"][mode] = tables
    return result


def access_bits(rights):
    return sum({"read": 0x8, "write": 0x10, "execute": 0x20}[right]
               for right in rights)


def cells64(value):
    return f"<0x{value >> 32:x} 0x{value & 0xffffffff:x}>"


def render_tree(value, identity, base_name, control="confined", cpus=None,
                parked=(3, 4, 5, 6, 7)):
    extents = {row["name"]: row for row in value["extents"]}
    profiles = {row["hart"]: combine(row, extents)
                for row in value["profiles"]}
    unique = {(row.base, row.size): row for hart, rows in profiles.items()
              if (hart, control) != (0, "boot") for row in rows}
    park = extents["park-entry"]
    unique[(int(park["base"], 16), int(park["size"], 16))] = Region(
        "park-entry", int(park["base"], 16), int(park["size"], 16), (),
        ("execute",))
    regions = sorted(unique.values(), key=lambda row: (row.base, row.size,
                                                       row.name))
    labels = {(row.base, row.size): f"be_region_{index:02d}"
              for index, row in enumerate(regions)}
    lifecycle = {row["hart"]: row for row in value["lifecycle"]}
    calls = {row["role"]: row["allow"] for row in value["calls"]}

    def cpu(hart):
        return f"&{{{cpus[hart]}}}" if cpus else f"&{{/cpus/cpu@{hart}}}"

    def region_list(hart):
        return ", ".join(f"<&{labels[(row.base, row.size)]} "
                         f"0x{access_bits(row.su):x}>"
                         for row in profiles[hart])

    digest_cells = " ".join(f"0x{int(identity[at:at + 8], 16):08x}"
                            for at in range(0, 64, 8))
    lines = [f'/include/ "{base_name}"', "/ {", "\tchosen {",
             "\t\topensbi-config {", '\t\t\tcompatible = "opensbi,config";',
             f"\t\t\tcold-boot-harts = <{cpu(0)}>;", "\t\t};",
             "\t\topensbi-domains {",
             '\t\t\tcompatible = "opensbi,domain,config";',
             f"\t\t\tconfig-digest = <{digest_cells}>;"]
    for row in regions:
        label = labels[(row.base, row.size)]
        lines += [f"\t\t\t{label}: {label} {{",
                  '\t\t\t\tcompatible = "opensbi,domain,memregion";',
                  f"\t\t\t\tbase = {cells64(row.base)};",
                  f"\t\t\t\torder = <{row.order}>;", "\t\t\t};"]

    def instance(name, harts, boot, order, regions_text=None, resume=None,
                 argument=0, allow=None, reset=False, inherit="m-only"):
        out = [f"\t\t\t{name} {{",
               '\t\t\t\tcompatible = "opensbi,domain,instance";',
               "\t\t\t\tpossible-harts = <" +
               " ".join(cpu(hart) for hart in harts) + ">;",
               f'\t\t\t\troot-regions-inheritance = "{inherit}";',
               f"\t\t\t\tboot-hart = <{cpu(boot)}>;",
               f"\t\t\t\tinit-order = <{order}>;"]
        if regions_text:
            out.append(f"\t\t\t\tregions = {regions_text};")
        if resume is not None:
            out += [f"\t\t\t\tnext-addr = {cells64(resume)};",
                    f"\t\t\t\tnext-arg1 = {cells64(argument)};",
                    "\t\t\t\tnext-mode = <0x1>;"]
        if reset:
            out.append("\t\t\t\tsystem-reset-allowed;")
        if allow is not None:
            values = []
            for call in allow:
                argument = 0xffffffff if call["argument"] == "any" else \
                    call["argument"]
                values += [int(call["extension"], 16),
                           int(call["function"], 16), argument,
                           int(call["maximum"], 16)]
            out.append("\t\t\t\tecall-allowlist" + (
                " = <" + " ".join(f"0x{item:x}" for item in values) + ">;"
                if values else ";"))
        return out + ["\t\t\t};"]

    lines += instance("be_boot", [0, 1, 2], 0, 1, reset=True,
                      inherit="all")
    if control == "confined":
        lines += instance("be_control", [0], 0, 10, region_list(0),
                          int(lifecycle[0]["resume"], 16), 0,
                          calls["control"], True)
    for index, hart in enumerate((1, 2)):
        private = extents[f"g{index}-private"]
        lines += instance(f"be_g{index}", [hart], hart, 11 + index,
                          region_list(hart),
                          int(lifecycle[hart]["resume"], 16),
                          int(private["base"], 16), calls["vs-domain"])
    park_region = labels[(int(park["base"], 16), int(park["size"], 16))]
    lines += instance("be_park", parked, 0, 100,
                      f"<&{park_region} 0x20>", int(park["base"], 16))
    lines += ["\t\t};", "\t};", "};", ""]
    return "\n".join(lines)


def check_base_source(base, expected_warnings, dtc, scratch):
    scratch = private_directory(scratch)
    output = scratch / "base.dtb"
    result = run([str(dtc), "-I", "dts", "-O", "dtb", "-o", output.name,
                  str(pathlib.Path(base).resolve())], cwd=scratch)
    expected = json.loads(pathlib.Path(expected_warnings).read_bytes())
    require(expected.get("compile") == warning_set(result.stderr),
            "base dtc warning set changed")
    fdt = parse_fdt(output.read_bytes())
    shutil.rmtree(scratch)
    return fdt


def generate(descriptor_path, base, expected_warnings, firmware_elf, dtc,
             nm, readelf, output, control):
    value, identity = strict_descriptor(descriptor_path)
    output = private_directory(output)
    fdt = check_base_source(base, expected_warnings, dtc,
                            output / "base-check")
    symbols = firmware_symbols(firmware_elf, nm, readelf)
    roots = platform(fdt, symbols)
    source = render_tree(value, identity, pathlib.Path(base).name, control)
    source_path = output / f"{value['image']}.dts"
    write_new(source_path, source.encode())
    dtb_path = output / f"{value['image']}.dtb"
    result = run([str(dtc), "-I", "dts", "-O", "dtb", "-i",
                  str(pathlib.Path(base).resolve().parent), "-o",
                  dtb_path.name, source_path.name], cwd=output)
    expected = json.loads(pathlib.Path(expected_warnings).read_bytes())
    require(expected.get("compile") == warning_set(result.stderr),
            "joined dtc warning set differs from the base")
    parse_fdt(dtb_path.read_bytes())
    tables = expected_tables(value, identity, roots, sha(firmware_elf),
                             sha(base), control)
    write_new(output / f"{value['image']}-pmp.json", canonical(tables))
    print(f"BE_MVP_PARTITION_BACKEND: PASS image={value['image']} "
          f"identity={identity[:12]}")


def render_only(descriptor_path, base_name, output, control):
    value, identity = strict_descriptor(descriptor_path)
    write_new(output, render_tree(value, identity, base_name,
                                  control).encode())


def test_tables(descriptor_path, base_dtb, firmware, base_dts, output,
                control):
    value, identity = strict_descriptor(descriptor_path)
    symbols = {"_fw_start": 0, "_fw_rw_start": 0x40000,
               "_fw_end": 0x48000, "_tlb_info_size": 32}
    roots = platform(parse_fdt(pathlib.Path(base_dtb).read_bytes()), symbols)
    write_new(output, canonical(expected_tables(
        value, identity, roots, sha(firmware), sha(base_dts), control)))


def synthetic_base():
    return """/dts-v1/;
/ {
 #address-cells = <2>; #size-cells = <2>;
 memory@80000000 { device_type = "memory"; reg = <0 0x80000000 2 0>; };
 cpus { #address-cells = <1>; #size-cells = <0>;
  cpu@0 { device_type = "cpu"; reg = <0>; };
  cpu@1 { device_type = "cpu"; reg = <1>; };
  cpu@2 { device_type = "cpu"; reg = <2>; };
  cpu@3 { device_type = "cpu"; reg = <3>; };
  cpu@4 { device_type = "cpu"; reg = <4>; };
  cpu@5 { device_type = "cpu"; reg = <5>; };
  cpu@6 { device_type = "cpu"; reg = <6>; };
  cpu@7 { device_type = "cpu"; reg = <7>; };
 };
 test@100000 { compatible = "sifive,test1"; reg = <0 0x100000 0 0x1000>; };
 uart@10000000 { compatible = "ns16550a"; reg = <0 0x10000000 0 0x100>; };
 aplic@c000000 { compatible = "riscv,aplic"; reg = <0 0xc000000 0 0x8000>; };
 imsic@24000000 { compatible = "riscv,imsics"; reg = <0 0x24000000 0 0x8000>; };
 timer@2000000 { compatible = "riscv,clint0"; reg = <0 0x2000000 0 0x10000>; };
 chosen { rng-seed = [00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f]; };
};
"""


def self_test(descriptor, dtc, scratch):
    value, identity = strict_descriptor(descriptor)
    scratch = pathlib.Path(scratch)
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(mode=0o700, parents=True)
    source = scratch / "raw.dts"
    raw = scratch / "raw.dtb"
    source.write_text(synthetic_base(), encoding="utf-8")
    run([str(dtc), "-I", "dts", "-O", "dtb", "-o", raw.name, source.name],
        cwd=scratch)
    seed_source = scratch / "seed.dts"
    seed_raw = scratch / "seed.dtb"
    seed_source.write_text(synthetic_base().replace("00 01 02", "ff 01 02"),
                           encoding="utf-8")
    run([str(dtc), "-I", "dts", "-O", "dtb", "-o", seed_raw.name,
         seed_source.name], cwd=scratch)
    require(without_rng(raw.read_bytes()) == without_rng(seed_raw.read_bytes()),
            "BASE-RNG: rng-seed-only change was refused")
    other_source = scratch / "other.dts"
    other_raw = scratch / "other.dtb"
    other_source.write_text(synthetic_base().replace(
        'reg = <0 0x10000000 0 0x100>', 'reg = <0 0x10001000 0 0x100>'),
        encoding="utf-8")
    run([str(dtc), "-I", "dts", "-O", "dtb", "-o", other_raw.name,
         other_source.name], cwd=scratch)
    require(without_rng(raw.read_bytes()) != without_rng(other_raw.read_bytes()),
            "BASE-OTHER: non-seed base-tree change was accepted")
    try:
        parse_fdt(after_end(raw.read_bytes()))
    except Refused as error:
        require(str(error).startswith("FDT has data after"),
                "BASE-END: wrong refusal")
    else:
        raise Refused("BASE-END: data after end was accepted")
    fdt = parse_fdt(raw.read_bytes())
    roots = platform(fdt, {"_fw_start": 0, "_fw_rw_start": 0x40000,
                           "_fw_end": 0x48000, "_tlb_info_size": 32})
    tables = expected_tables(value, identity, roots, "0" * 64, "1" * 64)
    require(all(len(row["entries"]) == 16
                for mode in tables["modes"].values() for row in mode),
            "a table is not sixteen entries")
    require(all(sum(row["state"] == state for row in
                    tables["modes"]["plain"]) == count
                for state, count in (("never-started", 8), ("boot", 3),
                                     ("confined", 3))), "state table counts")
    tree = render_tree(value, identity, "base.dts")
    require("ecall-allowlist;" in tree and "config-digest" in tree and
            "cold-boot-harts" in tree, "rendered tree lacks the interface")
    step = expected_tables(value, identity, roots, "0" * 64, "1" * 64, "boot")
    require(step["control_hart"] == "boot" and
            tables["control_hart"] == "confined"
            and [sum(row["state"] == state for row in step["modes"][mode])
                 for mode in step["modes"] for state in ("never-started",
                                                         "boot", "confined")]
            == [8, 3, 2] * 2 and not any(row["hart"] == 0 and row["state"] ==
                                         "confined" for row in
                                         step["modes"]["smepmp"]),
            "step-1 tables")
    require("be_control" in tree and "be_control" not in render_tree(
        value, identity, "base.dts", "boot"), "step-1 tree")
    shutil.rmtree(scratch)
    print("BE_MVP_PARTITION_BACKEND_SELF_TEST: PASS cases=9")


def board_self_test(descriptor, facts, base, dtc, scratch):
    """The board platform's cases (B-3) on a stand-in step 3 and its
    description, every value made up: each passing form, and each refusal
    by its own rule."""
    scratch = pathlib.Path(scratch)
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(mode=0o700, parents=True)
    text, results, runs = pathlib.Path(base).read_text(
        encoding="utf-8"), [], iter(range(1 << 16))
    _, _, fdt = board_base(dtc, base, scratch / "base")
    symbols = {"_fw_start": 0, "_fw_rw_start": 0x80000, "_fw_end": 0x90000,
               "_tlb_info_size": 32}
    value, identity = strict_descriptor(descriptor)

    def edited(old, new):
        require(old in text, f"the stand-in lacks {old!r}")
        path = scratch / f"base-{next(runs)}.dts"
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return path

    def tree(path=base, board=facts):
        out = scratch / f"out-{next(runs)}"
        board_tree(descriptor, "k3-x", path, board, dtc, out, "confined")
        return (out / "k3-x.dts").read_text(encoding="utf-8")

    def changed(key, field, new):
        board = json.loads(json.dumps(facts))
        board[key][field] = new
        return board

    def case(label, action, refusal=None):
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                action()
            passed = refusal is None
        except Refused as error:
            passed = refusal is not None and refusal in str(error)
        results.append(passed)
        print(f"{'ok  ' if passed else 'FAIL'} board: {label}")

    def called(argv, text):
        with contextlib.redirect_stdout(io.StringIO()) as said:
            code = main(["--platform", "k3-com260", "--dtc", str(dtc)] + argv)
        require(code == 1 and text in said.getvalue(), f"{argv} passed")

    (scratch / "facts.json").write_text(json.dumps(facts), encoding="utf-8")
    files = ["--platform-file", str(scratch / "facts.json"), "--base-dts",
             str(base)]

    harts = harts_by_reg(fdt, 16)
    chosen = '\tchosen {\n\t\tstdout-path = "serial0";\n'
    cells = chosen + ("\t\t#address-cells = <0x01>;\n"
                      "\t\t#size-cells = <0x00>;\n")
    roots = [
        "0x0000000080000000-0x000000008007ffff M: (F,R,X) S/U: ()",
        "0x0000000080080000-0x00000000800fffff M: (F,R,W) S/U: ()",
        "0x0000000030000000-0x0000000030000fff M: (I,R,W) S/U: (R,W)",
        "0x0000000032000000-0x0000000032003fff M: (I,R,W) S/U: ()",
        "0x0000000031000000-0x000000003100ffff M: (I,R,W) S/U: ()",
        "0x0000000033000000-0x000000003300ffff M: (I,R,W) S/U: ()",
        "0x0000000000000000-0xffffffffffffffff M: () S/U: (R,W,X)"]
    rows = expected_tables(value, identity, platform_k3(fdt, symbols, facts),
                           "0" * 64, "1" * 64, "confined", 16, ("plain",))
    for label, action, refusal in (
            ("be_park is harts 3 to 15, each CPU node by its reg",
             lambda: require(re.search(
                 r"be_park \{[^}]*possible-harts = <([^>]*)>", tree()).group(
                     1).split() == [f"&{{{harts[hart]}}}" for hart in range(
                         3, 16)] and harts[10] == "/cpus/cpu@a", "be_park"),
             None),
            ("tables of plain PMP alone, harts 0 to 15", lambda: require(
                list(rows["modes"]) == ["plain"] and [sum(
                    row["state"] == state for row in rows["modes"]["plain"])
                    for state in ("never-started", "boot", "confined")] ==
                [16, 3, 3], "tables"), None),
            ("the root regions as the banner prints them", lambda: require(
                [banner(row) for row in sorted_regions(platform_k3(
                    fdt, symbols, facts))] == roots, "root regions"), None),
            ("a warning of a node that the render defines again",
             lambda: tree(edited(chosen + "\t\tboot-hartid = <0x00>;\n",
                                 cells + "boot-hartid = <0x00>;\nx {\n};\n")),
             None),
            ("a warning that the joined tree adds", lambda: tree(edited(
                chosen, cells)), "the joined tree's dtc warnings differ"),
            ("two CPU nodes of one hart", lambda: tree(edited(
                "reg = <0x0f>;", "reg = <0x0e>;")), "is not one hart"),
            ("a hart disabled", lambda: tree(edited(
                "reg = <0x0f>;", 'reg = <0x0f>;\nstatus = "disabled";')),
             "the tree's harts are not 0 to 15"),
            ("memory other than the board's", lambda: tree(board=changed(
                "memory", "size", "0x40000000")), "memory is not the board's"),
            ("a syscon reset node", lambda: tree(edited(chosen, (
                'poweroff {\ncompatible = "syscon-poweroff";\n'
                "regmap = <0x40>;\n};\n") + chosen)), "a syscon reset node"),
            ("a root device at another path", lambda: tree(board=changed(
                "root_devices", "console", dict(facts["root_devices"][
                    "console"], path="/soc/x"))), "console at /soc/serial"),
            ("an APLIC of more than one region", lambda: tree(edited(
                "0x32000000 0x00 0x4000", "0x32000000 0x00 0x3000")),
             "aplic-m at /soc/interrupt-controller@32000000 is not one"),
            ("a console of more than a page", lambda: tree(edited(
                "0x30000000 0x00 0x100", "0x30000000 0x00 0x2000")),
             "console at /soc/serial@30000000 is not one"),
            ("an IMSIC off its size's alignment", lambda: tree(edited(
                "0x33000000 0x00 0x10000", "0x33008000 0x00 0x10000"),
                changed("root_devices", "imsic-m", dict(facts[
                    "root_devices"]["imsic-m"], base="0x33008000"))),
             "imsic-m at /soc/interrupt-controller@33000000 is not one"),
            ("a firmware past end_max", lambda: platform_k3(
                fdt, symbols, changed("firmware", "end_max", "0x800c0000")),
             "the firmware's regions pass end_max"),
            ("a fact not a hex number", lambda: platform_k3(
                fdt, symbols, changed("firmware", "end_max", "2097152")),
             "'2097152' is not a hex number"),
            ("not a board description", lambda: board_facts(descriptor),
             "is not a board description"),
            ("arguments: no description or base", lambda: called(
                [], "needs --platform-file and --base-dts"), None),
            ("arguments: a tree without --out", lambda: called(files + [
                "--board-tree", "--descriptor", str(descriptor)],
                "board-tree arguments"), None),
            ("arguments: tables of no image", lambda: called(files + [
                "--board-tables", "--firmware-elf", "x", "--nm", "x",
                "--readelf", "x", "--out", "x"], "board-table arguments"),
             None),
            ("arguments: no mode", lambda: called(files, "the board takes"),
             None)):
        case(label, action, refusal)
    shutil.rmtree(scratch)
    print(f"BE_MVP_PARTITION_BOARD_SELF_TEST: "
          f"{'PASS' if all(results) else 'FAIL'} cases={len(results)}")
    return 0 if all(results) else 1


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--descriptor")
    parser.add_argument("--base-dts")
    parser.add_argument("--base-warnings")
    parser.add_argument("--firmware-elf")
    parser.add_argument("--dtc", required=True)
    parser.add_argument("--nm")
    parser.add_argument("--readelf")
    parser.add_argument("--out")
    parser.add_argument("--normalize-base", action="store_true")
    parser.add_argument("--check-base", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--test-tables", action="store_true")
    parser.add_argument("--base-name")
    parser.add_argument("--base-dtb")
    parser.add_argument("--out-tables")
    parser.add_argument("--raw-dtb")
    parser.add_argument("--out-dts")
    parser.add_argument("--out-warnings")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch")
    parser.add_argument("--control-hart", choices=("boot", "confined"),
                        default="confined")
    parser.add_argument("--platform", choices=("k3-like", "k3-com260"),
                        default="k3-like")
    parser.add_argument("--platform-file")
    parser.add_argument("--board-tree", action="store_true")
    parser.add_argument("--board-tables", action="store_true")
    parser.add_argument("--image")
    args = parser.parse_args(argv)
    try:
        if args.platform == "k3-com260":
            require(args.platform_file and args.base_dts,
                    "the board needs --platform-file and --base-dts")
            facts = board_facts(args.platform_file)
            if args.board_tree:
                require(args.descriptor and args.out,
                        "board-tree arguments are missing")
                board_tree(args.descriptor, args.image, args.base_dts, facts,
                           args.dtc, args.out, args.control_hart)
            elif args.board_tables:
                require((args.descriptor or args.image) and all((
                    args.firmware_elf, args.nm, args.readelf, args.out)),
                        "board-table arguments are missing")
                board_tables(args.descriptor, args.image, args.base_dts,
                             facts, args.firmware_elf, args.dtc, args.nm,
                             args.readelf, args.out, args.control_hart)
            else:
                require(args.self_test and args.descriptor and args.scratch,
                        "the board takes --board-tree, --board-tables, or "
                        "--self-test with --descriptor and --scratch")
                return board_self_test(args.descriptor, facts, args.base_dts,
                                       args.dtc, args.scratch)
        elif args.normalize_base:
            require(args.raw_dtb and args.out_dts and args.out_warnings and
                    args.scratch, "base normalization arguments are missing")
            normalize_dtb(args.raw_dtb, args.dtc, args.out_dts,
                          args.out_warnings, args.scratch)
        elif args.check_base:
            require(args.raw_dtb and args.base_dts and args.base_warnings and
                    args.scratch, "base check arguments are missing")
            check_normalized_base(args.raw_dtb, args.base_dts,
                                  args.base_warnings, args.dtc, args.scratch)
        elif args.render:
            require(args.descriptor and args.base_name and args.out_dts,
                    "render arguments are missing")
            render_only(args.descriptor, args.base_name, args.out_dts,
                        args.control_hart)
        elif args.test_tables:
            require(args.descriptor and args.base_dtb and args.firmware_elf and
                    args.base_dts and args.out_tables,
                    "test-table arguments are missing")
            test_tables(args.descriptor, args.base_dtb, args.firmware_elf,
                        args.base_dts, args.out_tables, args.control_hart)
        elif args.self_test:
            require(args.descriptor and args.scratch,
                    "self-test needs --descriptor and --scratch")
            self_test(args.descriptor, args.dtc, args.scratch)
        else:
            require(all((args.descriptor, args.base_dts,
                         args.base_warnings, args.firmware_elf, args.nm,
                         args.readelf,
                         args.out)), "backend generation arguments missing")
            generate(args.descriptor, args.base_dts, args.base_warnings,
                     args.firmware_elf, args.dtc, args.nm, args.readelf,
                     args.out, args.control_hart)
        return 0
    except (Refused, OSError, ValueError, KeyError, TypeError,
            subprocess.SubprocessError) as error:
        print(f"BE_MVP_PARTITION_BACKEND: FAIL {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
