#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Check the K3 B6 guest outputs against guest/pins.txt (planning/k3-b6-plan.md,
Build, pins, and reproducibility), and the facts behind the pins.

  guest-pins.py --check --pins PINS --dir DIR --layout H [--gcc GCC]
  guest-pins.py --print --dir DIR --layout H [--gcc GCC]
  guest-pins.py --match NAME [--match NAME ...] --pins PINS --dir DIR
  guest-pins.py --self-test --layout H

--check re-hashes every output in DIR against its pin and checks:
  - the toolchain: the first line of `GCC --version` equals the pinned one,
    since the pins hold for one cross toolchain;
  - init: a static RV64 soft-float ELF executable, with no interpreter and
    no dynamic section;
  - Image: the RISC-V Image header (magic, magic2, little-endian flag,
    version 0.2), text_offset equal to BE_B6_KERNEL_TEXT_OFFSET and the pin,
    image_size equal to the pin, at least the file size, at most
    BE_B6_KERNEL_IMAGE_SIZE_MAX, and ending below the DTB slot; the file at
    most BE_B6_KERNEL_FILE_MAX; and exactly one `Linux version` banner, equal
    to the pinned one;
  - every DTB: exactly BE_B6_DTB_BYTES, a version-17 FDT header with an
    empty reservation map, and a decoded tree with exactly the plan's nodes
    and the values scripts/gen-dts.py gives its variant.
--print makes the same fact checks without pins and prints the pin lines of
DIR's outputs, for a deliberate pin update. --match checks only the named
files' SHA-256 and size. --self-test runs the checks on generated inputs
and in-memory defects.
"""

import argparse
import hashlib
import importlib.util
import pathlib
import re
import struct
import subprocess
import sys

DTB_FILES = {
    "base": "b6-guest.dtb",
    "memory": "b6-guest-memory.dtb",
    "init-exit": "b6-guest-init-exit.dtb",
    "rdcycle": "b6-guest-rdcycle.dtb",
    "sbi-time": "b6-guest-sbi-time.dtb",
    "reference": "b6-guest-reference.dtb",
}
FILES = ("init", "Image") + tuple(DTB_FILES.values())
LAYOUT_NAMES = ("KERNEL_FILE_MAX", "KERNEL_IMAGE_SIZE_MAX",
                "KERNEL_TEXT_OFFSET", "KERNEL_GPA", "DTB_GPA", "DTB_BYTES")
FILE_LINE = re.compile(r"^file (\S+) sha256=([0-9a-f]{64}) bytes=([0-9]+)$")
KERNEL_LINE = re.compile(r"^kernel (image_size|text_offset)=(0x[0-9a-f]+)$")
BANNER_LINE = re.compile(r"^kernel banner=(Linux version [ -~]+)$")
TOOLCHAIN_LINE = re.compile(r"^toolchain gcc=([ -~]+)$")
BANNER = b"Linux version "
IMAGE_MAGIC = b"RISCV\0\0\0"
IMAGE_MAGIC2 = b"RSC\x05"
IMAGE_VERSION = 0x2
FDT_MAGIC = 0xd00dfeed
FDT_BEGIN_NODE, FDT_END_NODE, FDT_PROP, FDT_NOP, FDT_END = 1, 2, 3, 4, 9
ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
ELF_PHDR = struct.Struct("<IIQQQQQQ")
EM_RISCV = 243
PT_LOAD, PT_DYNAMIC, PT_INTERP = 1, 2, 3
U32 = 0xffffffff


class Finding(Exception):
    """One output or pin breaks a rule."""


def load_gen_dts():
    path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "gen-dts.py"
    spec = importlib.util.spec_from_file_location("b6_gen_dts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN_DTS = load_gen_dts()


def parse_layout(text):
    layout = GEN_DTS.parse_layout(text)
    for name in LAYOUT_NAMES:
        if name not in layout:
            raise Finding(f"BE_B6_{name} is missing from the layout")
    return layout


def parse_pins(text):
    """Return ({name: (sha256, bytes)}, {kernel/toolchain key: value})."""
    files, facts = {}, {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        match = FILE_LINE.match(line)
        if match:
            name, sha, size = match.groups()
            if name not in FILES or name in files:
                raise Finding(f"pins line {number}: unexpected file {name}")
            files[name] = (sha, int(size))
            continue
        for pattern, key in ((KERNEL_LINE, None), (BANNER_LINE, "banner"),
                             (TOOLCHAIN_LINE, "gcc")):
            match = pattern.match(line)
            if match:
                key = key or match.group(1)
                if key in facts:
                    raise Finding(f"pins line {number}: {key} repeated")
                facts[key] = match.groups()[-1]
                break
        else:
            raise Finding(f"pins line {number}: not a pin: {line!r}")
    missing = [name for name in FILES if name not in files]
    missing += [key for key in ("image_size", "text_offset", "banner", "gcc")
                if key not in facts]
    if missing:
        raise Finding(f"pins lack {', '.join(missing)}")
    return files, facts


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_init(data):
    if len(data) < ELF_HEADER.size or data[:4] != b"\x7fELF":
        raise Finding("init: not an ELF file")
    (ident, e_type, machine, _version, entry, phoff, _shoff, flags, _ehsize,
     phentsize, phnum, _shentsize, _shnum, _shstrndx) = \
        ELF_HEADER.unpack_from(data, 0)
    if ident[4] != 2 or ident[5] != 1:
        raise Finding("init: not ELF64 little-endian")
    if e_type != 2 or machine != EM_RISCV:
        raise Finding("init: not a RISC-V executable (ET_EXEC)")
    if flags & 0x6:
        raise Finding("init: not the soft-float ABI (lp64)")
    if phentsize != ELF_PHDR.size or phoff + phnum * phentsize > len(data):
        raise Finding("init: bad program headers")
    executable = False
    for index in range(phnum):
        p_type, p_flags, _offset, vaddr, _paddr, _filesz, memsz, _align = \
            ELF_PHDR.unpack_from(data, phoff + index * phentsize)
        if p_type in (PT_INTERP, PT_DYNAMIC):
            raise Finding("init: not static (PT_INTERP or PT_DYNAMIC)")
        if p_type == PT_LOAD and p_flags & 1 and vaddr <= entry < vaddr + memsz:
            executable = True
    if not executable:
        raise Finding("init: the entry is not in an executable segment")


def kernel_facts(data, layout):
    """Check the Image header and budgets; return (image_size, offset, banner)."""
    if len(data) < 64:
        raise Finding("Image: shorter than its 64-byte header")
    (_code0, _code1, text_offset, image_size, flags, version, _res1, _res2,
     magic, magic2, _res3) = struct.unpack_from("<IIQQQIIQ8s4sI", data, 0)
    if magic != IMAGE_MAGIC or magic2 != IMAGE_MAGIC2:
        raise Finding("Image: bad magic or magic2")
    if flags & 1:
        raise Finding("Image: not little-endian")
    if version != IMAGE_VERSION:
        raise Finding(f"Image: header version {version:#x}, not 0.2")
    if text_offset != layout["KERNEL_TEXT_OFFSET"]:
        raise Finding(f"Image: text_offset {text_offset:#x}, not "
                      f"{layout['KERNEL_TEXT_OFFSET']:#x}")
    if len(data) > layout["KERNEL_FILE_MAX"]:
        raise Finding(f"Image: {len(data)} bytes, over the "
                      f"{layout['KERNEL_FILE_MAX']:#x}-byte budget")
    if not len(data) <= image_size <= layout["KERNEL_IMAGE_SIZE_MAX"]:
        raise Finding(f"Image: image_size {image_size:#x} is below the file "
                      f"or over {layout['KERNEL_IMAGE_SIZE_MAX']:#x}")
    if layout["KERNEL_GPA"] + image_size > layout["DTB_GPA"]:
        raise Finding("Image: image_size reaches the DTB slot")
    if data.count(BANNER) != 1:
        raise Finding(f"Image: {data.count(BANNER)} '{BANNER.decode()}' strings")
    start = data.index(BANNER)
    end = data.find(b"\n", start)
    banner = data[start:end]
    if end < 0 or not all(0x20 <= byte <= 0x7e for byte in banner):
        raise Finding("Image: the banner is not one printable line")
    return image_size, text_offset, banner.decode("ascii")


def fdt_tree(data, size):
    """Decode a flattened device tree into {path: {property: value}}."""
    if len(data) < 40:
        raise Finding("shorter than an FDT header")
    (magic, total, off_struct, off_strings, off_rsv, version, last_comp,
     boot_cpu, size_strings, size_struct) = struct.unpack_from(">10I", data, 0)
    if magic != FDT_MAGIC or version != 17 or last_comp != 16 or boot_cpu:
        raise Finding("bad FDT magic, version, or boot CPU")
    if len(data) != size or total != size:
        raise Finding(f"{len(data)} bytes, totalsize {total}, not {size}")
    if (off_rsv < 40 or off_rsv % 8 or off_struct % 4 or
            off_rsv + 16 > total or off_struct + size_struct > total or
            off_strings + size_strings > total):
        raise Finding("FDT blocks out of bounds")
    if data[off_rsv:off_rsv + 16] != bytes(16):
        raise Finding("the FDT reservation map is not empty")

    def cstring(offset, limit):
        end = data.find(b"\0", offset, limit)
        if end < 0:
            raise Finding("unterminated FDT string")
        return data[offset:end].decode("ascii"), end + 1

    nodes, path = {}, []
    position, limit = off_struct, off_struct + size_struct
    while True:
        if position + 4 > limit:
            raise Finding("FDT structure overruns its block")
        token = struct.unpack_from(">I", data, position)[0]
        position += 4
        if token == FDT_BEGIN_NODE:
            name, position = cstring(position, limit)
            position = (position + 3) & ~3
            path.append(name)
            key = "/" + "/".join(path[1:])
            if key in nodes:
                raise Finding(f"FDT node {key} repeated")
            nodes[key] = {}
        elif token == FDT_PROP:
            length, name_offset = struct.unpack_from(">II", data, position)
            value = data[position + 8:position + 8 + length]
            position = (position + 8 + length + 3) & ~3
            name, _ = cstring(off_strings + name_offset,
                              off_strings + size_strings)
            if not path or name in nodes["/" + "/".join(path[1:])]:
                raise Finding(f"FDT property {name} misplaced or repeated")
            nodes["/" + "/".join(path[1:])][name] = value
        elif token == FDT_END_NODE:
            if not path:
                raise Finding("unbalanced FDT end of node")
            path.pop()
        elif token == FDT_END:
            break
        elif token != FDT_NOP:
            raise Finding(f"bad FDT token {token:#x}")
    if path:
        raise Finding("unterminated FDT node")
    return nodes


def expected_tree(layout, variant):
    """The decoded tree scripts/gen-dts.py renders for one variant."""
    values = GEN_DTS.values(layout, variant)
    reg = [int(cell, 16) for cell in values["MEMORY_REG"].split()]
    isa = re.findall(r'"([^"]*)"', values["ISA_EXTENSIONS"])
    return {
        "/": {"#address-cells": struct.pack(">I", 2),
              "#size-cells": struct.pack(">I", 2),
              "compatible": b"beryllium,k3-b6-guest\0",
              "model": b"Beryllium K3 B6 guest\0"},
        "/chosen": {"bootargs": values["BOOTARGS"].encode() + b"\0"},
        "/cpus": {"#address-cells": struct.pack(">I", 1),
                  "#size-cells": struct.pack(">I", 0),
                  "timebase-frequency": struct.pack(
                      ">I", int(values["TIMEBASE_HZ"]))},
        "/cpus/cpu@0": {"device_type": b"cpu\0",
                        "reg": struct.pack(">I", 0),
                        "compatible": b"riscv\0",
                        "mmu-type": b"riscv,sv39\0",
                        "riscv,isa-base": b"rv64i\0",
                        "riscv,isa-extensions":
                            b"".join(name.encode() + b"\0" for name in isa)},
        "/cpus/cpu@0/interrupt-controller": {
            "compatible": b"riscv,cpu-intc\0",
            "interrupt-controller": b"",
            "#interrupt-cells": struct.pack(">I", 1)},
        "/memory@" + values["MEMORY_UNIT"]: {
            "device_type": b"memory\0", "reg": struct.pack(">4I", *reg)},
    }


def check_dtb(name, data, layout, variant):
    try:
        tree = fdt_tree(data, layout["DTB_BYTES"])
    except Finding as finding:
        raise Finding(f"{name}: {finding}") from None
    expected = expected_tree(layout, variant)
    if tree != expected:
        nodes = sorted(set(tree) ^ set(expected))
        props = sorted(path for path in set(tree) & set(expected)
                       if tree[path] != expected[path])
        raise Finding(f"{name}: tree differs from the {variant} DTS "
                      f"(nodes {nodes}, properties in {props})")


def gcc_version(gcc):
    result = subprocess.run([gcc, "--version"], capture_output=True,
                            text=True, check=True)
    return result.stdout.splitlines()[0].strip()


def read_outputs(directory, names=FILES):
    outputs = {}
    for name in names:
        path = directory / name
        if not path.is_file():
            raise Finding(f"{path} is missing")
        outputs[name] = path.read_bytes()
    return outputs


def facts(outputs, layout):
    """Check every output's facts; return the kernel facts."""
    check_init(outputs["init"])
    kernel = kernel_facts(outputs["Image"], layout)
    for variant, name in DTB_FILES.items():
        check_dtb(name, outputs[name], layout, variant)
    return kernel


def pin_lines(outputs, kernel, gcc):
    image_size, text_offset, banner = kernel
    lines = [f"file {name} sha256={digest(outputs[name])} "
             f"bytes={len(outputs[name])}" for name in FILES]
    lines += [f"kernel image_size={image_size:#x}",
              f"kernel text_offset={text_offset:#x}",
              f"kernel banner={banner}",
              f"toolchain gcc={gcc}"]
    return lines


def check(pins_text, outputs, layout, gcc):
    files, pinned = parse_pins(pins_text)
    if gcc is not None and gcc != pinned["gcc"]:
        raise Finding(f"the pins hold for '{pinned['gcc']}', not '{gcc}'")
    kernel = facts(outputs, layout)
    match(pins_text, outputs, FILES)
    image_size, text_offset, banner = kernel
    if (f"{image_size:#x}", f"{text_offset:#x}", banner) != (
            pinned["image_size"], pinned["text_offset"], pinned["banner"]):
        raise Finding("the Image header or banner does not match its pins")
    return kernel


def match(pins_text, outputs, names):
    files, _ = parse_pins(pins_text)
    for name in names:
        data = outputs[name]
        if (digest(data), len(data)) != files[name]:
            raise Finding(f"{name} does not match its pin "
                          f"(sha256={digest(data)} bytes={len(data)})")


# ------------------------------------------------------------- self-test
def fdt_blob(tree, size):
    """Serialize {path: {property: value}} (parents first) as an FDT."""
    strings, offsets, body = bytearray(), {}, bytearray()

    def string_offset(name):
        if name not in offsets:
            offsets[name] = len(strings)
            strings.extend(name.encode() + b"\0")
        return offsets[name]

    def emit(path):
        name = path.rsplit("/", 1)[-1] if path != "/" else ""
        body.extend(struct.pack(">I", FDT_BEGIN_NODE) + name.encode() + b"\0")
        body.extend(bytes(-len(body) % 4))
        for prop, value in tree[path].items():
            body.extend(struct.pack(">III", FDT_PROP, len(value),
                                    string_offset(prop)) + value)
            body.extend(bytes(-len(body) % 4))
        prefix = path.rstrip("/") + "/"
        for child in tree:
            if child.startswith(prefix) and "/" not in child[len(prefix):] \
                    and child != path:
                emit(child)
        body.extend(struct.pack(">I", FDT_END_NODE))

    emit("/")
    body.extend(struct.pack(">I", FDT_END))
    off_rsv = 40
    off_struct = off_rsv + 16
    off_strings = off_struct + len(body)
    blob = bytearray(size)
    struct.pack_into(">10I", blob, 0, FDT_MAGIC, size, off_struct, off_strings,
                     off_rsv, 17, 16, 0, len(strings), len(body))
    blob[off_struct:off_struct + len(body)] = body
    blob[off_strings:off_strings + len(strings)] = strings
    return bytes(blob)


def fake_image(layout, banner=b"Linux version 7.2.0 (be@beryllium) (gcc) #1 X\n",
               **fields):
    values = dict(text_offset=layout["KERNEL_TEXT_OFFSET"], image_size=0x3000,
                  flags=0, version=IMAGE_VERSION, magic=IMAGE_MAGIC,
                  magic2=IMAGE_MAGIC2)
    values.update(fields)
    header = struct.pack("<IIQQQIIQ8s4sI", 0, 0, values["text_offset"],
                         values["image_size"], values["flags"],
                         values["version"], 0, 0, values["magic"],
                         values["magic2"], 0)
    return header + banner + bytes(0x2000 - len(header) - len(banner))


def fake_init(interp=False):
    header = ELF_HEADER.pack(b"\x7fELF\x02\x01\x01" + bytes(9), 2, EM_RISCV, 1,
                             0x10078, 64, 0, 0x1, 64, ELF_PHDR.size,
                             2 if interp else 1, 64, 0, 0)
    load = ELF_PHDR.pack(PT_LOAD, 5, 0, 0x10000, 0x10000, 0x100, 0x100, 0x1000)
    extra = ELF_PHDR.pack(PT_INTERP, 4, 0, 0, 0, 0, 0, 1) if interp else b""
    return header + load + extra + bytes(0x100)


def fake_outputs(layout):
    outputs = {"Image": fake_image(layout), "init": fake_init()}
    for variant, name in DTB_FILES.items():
        outputs[name] = fdt_blob(expected_tree(layout, variant),
                                 layout["DTB_BYTES"])
    return outputs


def self_test(layout_text):
    layout = parse_layout(layout_text)
    failures, cases = [], 0

    def expect_ok(name, action):
        nonlocal cases
        cases += 1
        try:
            action()
        except Finding as finding:
            failures.append(f"{name}: unexpected finding: {finding}")

    def expect_finding(name, action, text):
        nonlocal cases
        cases += 1
        try:
            action()
        except Finding as finding:
            if text not in str(finding):
                failures.append(f"{name}: finding '{finding}' lacks '{text}'")
        else:
            failures.append(f"{name}: no finding")

    good = fake_outputs(layout)
    kernel = facts(good, layout)
    lines = pin_lines(good, kernel, "gcc 1")
    pins = "\n".join(["# self-test"] + lines)
    expect_ok("pass", lambda: check(pins, good, layout, "gcc 1"))
    expect_ok("match", lambda: match(pins, good, ["Image", "init"]))
    expect_finding("toolchain", lambda: check(pins, good, layout, "gcc 2"),
                   "pins hold for")
    pin_cases = [
        ("missing file", "\n".join(lines[1:]), "lack init"),
        ("malformed", pins + "\nfile init sha256=00 bytes=1", "not a pin"),
        ("repeated", pins + "\n" + lines[-1], "repeated"),
        ("unknown file", pins + "\nfile x sha256=" + "0" * 64 + " bytes=1",
         "unexpected file"),
    ]
    for name, text, finding in pin_cases:
        expect_finding(f"pins {name}", lambda t=text: parse_pins(t), finding)
    expect_finding("banner pin",
                   lambda: check(pins.replace("#1 X", "#1 Y"), good, layout,
                                 "gcc 1"), "banner")
    image_cases = [
        ("magic2", dict(magic2=b"RSC\x06"), "magic"),
        ("big-endian", dict(flags=1), "little-endian"),
        ("header version", dict(version=1), "not 0.2"),
        ("text_offset", dict(text_offset=0), "text_offset"),
        ("image_size below file", dict(image_size=0x100), "image_size"),
        ("image_size over budget",
         dict(image_size=layout["KERNEL_IMAGE_SIZE_MAX"] + 1), "image_size"),
        ("two banners", dict(banner=b"Linux version a\nLinux version b\n"),
         "2 'Linux version"),
        ("unterminated banner", dict(banner=b"Linux version \x01\n"),
         "printable"),
    ]
    for name, fields, finding in image_cases:
        data = fake_image(layout, **fields)
        expect_finding(f"Image {name}", lambda d=data: kernel_facts(d, layout),
                       finding)
    big = fake_image(layout) + bytes(layout["KERNEL_FILE_MAX"])
    expect_finding("Image file over budget", lambda: kernel_facts(big, layout),
                   "budget")
    flipped = dict(good)
    flipped["Image"] = bytes([good["Image"][0] ^ 1]) + good["Image"][1:]
    expect_finding("Image byte flip", lambda: match(pins, flipped, ["Image"]),
                   "Image does not match")
    flipped = dict(good)
    flipped["b6-guest-reference.dtb"] = good["b6-guest.dtb"]
    expect_finding("DTB swap", lambda: check(pins, flipped, layout, "gcc 1"),
                   "b6-guest-reference.dtb: tree differs")
    expect_finding("init interpreter",
                   lambda: check_init(fake_init(interp=True)), "static")
    expect_finding("init not ELF", lambda: check_init(bytes(64)), "not an ELF")
    base = expected_tree(layout, "base")
    size = layout["DTB_BYTES"]
    bad_magic = bytearray(fdt_blob(base, size))
    bad_magic[0] ^= 1
    reserved = bytearray(fdt_blob(base, size))
    reserved[40 + 8] = 1
    dtb_cases = [
        ("short", fdt_blob(base, size - 8), "bytes"),
        ("variant swap", fdt_blob(expected_tree(layout, "memory"), size),
         "differs"),
        ("extra node", fdt_blob(dict(base, **{"/uart@10000000": {}}), size),
         "differs"),
        ("magic", bytes(bad_magic), "magic"),
        ("reservation", bytes(reserved), "reservation"),
    ]
    for name, data, finding in dtb_cases:
        expect_finding(f"DTB {name}",
                       lambda d=data: check_dtb("dtb", d, layout, "base"),
                       finding)
    for failure in failures:
        print(f"BE_B6_GUEST_PINS_SELF_TEST: FAIL {failure}")
    status = "FAIL" if failures else "PASS"
    print(f"BE_B6_GUEST_PINS_SELF_TEST: {status} cases={cases}")
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--print", action="store_true")
    mode.add_argument("--match", action="append", choices=FILES)
    mode.add_argument("--self-test", action="store_true")
    parser.add_argument("--pins", type=pathlib.Path)
    parser.add_argument("--dir", type=pathlib.Path)
    parser.add_argument("--layout", type=pathlib.Path)
    parser.add_argument("--gcc")
    args = parser.parse_args()
    try:
        if args.match:
            if not args.pins or not args.dir:
                parser.error("--match needs --pins and --dir")
            match(args.pins.read_text(encoding="utf-8"),
                  read_outputs(args.dir, args.match), args.match)
            print(f"BE_B6_GUEST_PINS: MATCH {' '.join(args.match)}")
            return 0
        if not args.layout:
            parser.error("--layout is required")
        layout = parse_layout(args.layout.read_text(encoding="ascii"))
        if args.self_test:
            return self_test(args.layout.read_text(encoding="ascii"))
        if not args.dir:
            parser.error("--dir is required")
        gcc = gcc_version(args.gcc) if args.gcc else None
        outputs = read_outputs(args.dir)
        if args.print:
            kernel = facts(outputs, layout)
            print("\n".join(pin_lines(outputs, kernel, gcc or "unknown")))
            return 0
        if not args.pins:
            parser.error("--check needs --pins")
        kernel = check(args.pins.read_text(encoding="utf-8"), outputs, layout,
                       gcc)
    except Finding as finding:
        print(f"BE_B6_GUEST_PINS: FAIL {finding}", file=sys.stderr)
        return 1
    except (GEN_DTS.LayoutError, ValueError, OSError,
            subprocess.CalledProcessError) as error:
        print(f"BE_B6_GUEST_PINS: FAIL {error}", file=sys.stderr)
        return 1
    image_size, text_offset, banner = kernel
    print(f"BE_B6_GUEST_PINS: PASS files={len(FILES)} "
          f"image_bytes={len(outputs['Image'])} image_size={image_size:#x} "
          f"text_offset={text_offset:#x} init_bytes={len(outputs['init'])} "
          f"dtb_bytes={layout['DTB_BYTES']}")
    print(f"BE_B6_GUEST_PINS: banner={banner}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
