#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Build the self-report-flip variant (planning/mvp-m9-plan.md, D-4;
mvp/docs/log-profile.md, 3.2) from a scenario's built image, after the
link: flip one bit of the inert constant be_mvp_log_canary in the MVP
region's constants, in every file that holds the image's bytes.

  flip-canary.py --symbol NAME --bit N --elf MONITOR_ELF --map MONITOR_MAP
      --bin FLAT --boot-elf BOOT_ELF --boot-img BOOT_IMG --base B
      --staging L --monitor-offset O --out DIR

The symbol is located through the monitor ELF's symbol table, never by a
guessed offset: it must be one 16-byte object inside .mvp.rodata, whose
bytes are the same in the ELF's section, in the flat image at
symbol - B, in the boot image at O + symbol - B, and in the boot ELF's
PT_LOAD segment that holds L + O + symbol - B. Bit N, 0 to 127, is bit
N % 8 of the object's byte N // 8. Each copy is flipped and written to
DIR as be-mvp.elf, be-mvp.bin, be-mvp-boot.elf, and be-mvp-boot.img, with
be-mvp.sha256 and be-mvp-boot.sha256 as the build writes them, and the
link map copied as be-mvp.map, since the flip moves no address; each
output differs from its input in exactly that one bit, which the tool
checks before it writes. DIR/self-report-flip.json, the variant's
metadata, records the symbol, its address and size, the bit, each file's
offset of the flipped byte, and each file's nominal and mutated SHA-256,
the boot image's as nominal_image_sha256 and mutated_image_sha256: the
reference stays the nominal build's, and the checker expects the image's
hash to differ by that record and the mvp-rodata self-report alone to
differ (D-4). DIR must not exist.
"""

import argparse
import hashlib
import json
import pathlib
import struct
import sys

CANARY_BYTES = 16
SECTION = ".mvp.rodata"


class FlipError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise FlipError(message)


def elf_tables(data):
    """An ELF64 little-endian RISC-V file's sections {name: (offset,
    address, size)}, its PT_LOAD segments [(address, offset, filesz)], and
    its symbols {name: [(value, size)]}."""
    require(len(data) >= 64 and data[:4] == b"\x7fELF" and data[4] == 2 and
            data[5] == 1, "not an ELF64 little-endian file")
    machine = struct.unpack_from("<H", data, 18)[0]
    require(machine == 243, f"ELF machine {machine} is not RISC-V")
    (phoff, shoff) = struct.unpack_from("<QQ", data, 32)
    (phentsize, phnum, shentsize, shnum, shstrndx) = struct.unpack_from(
        "<HHHHH", data, 54)
    require(shentsize == 64 and phentsize == 56 and shstrndx < shnum,
            "ELF header sizes are not ELF64's")
    headers = [struct.unpack_from("<IIQQQQIIQQ", data, shoff + 64 * index)
               for index in range(shnum)]
    names = headers[shstrndx]

    def name_at(table, at):
        start = table[4] + at
        end = data.index(b"\0", start)
        return data[start:end].decode("ascii")

    sections = {}
    symbols = {}
    for header in headers:
        name = name_at(names, header[0])
        sections[name] = (header[4], header[3], header[5])
        if header[1] == 2:  # SHT_SYMTAB
            strings = headers[header[6]]
            for at in range(header[4], header[4] + header[5], 24):
                (name_index, _, _, _, value, size) = struct.unpack_from(
                    "<IBBHQQ", data, at)
                if name_index:
                    symbols.setdefault(name_at(strings, name_index),
                                       []).append((value, size))
    segments = []
    for index in range(phnum):
        (kind, _, offset, address, _, filesz, _, _) = struct.unpack_from(
            "<IIQQQQQQ", data, phoff + 56 * index)
        if kind == 1:  # PT_LOAD
            segments.append((address, offset, filesz))
    return sections, segments, symbols


def segment_offset(segments, address, size):
    """The file offset of [address, address + size) in one PT_LOAD."""
    found = [offset + address - start for start, offset, filesz in segments
             if start <= address and address + size <= start + filesz]
    require(len(found) == 1,
            f"0x{address:x} is not in exactly one PT_LOAD segment")
    return found[0]


def flipped(data, offset, bit):
    """DATA with bit BIT of byte OFFSET flipped, checked to differ from
    DATA in that bit alone."""
    out = bytearray(data)
    out[offset] ^= 1 << bit
    changed = [index for index in range(len(data))
               if data[index] != out[index]]
    require(changed == [offset] and data[offset] ^ out[offset] == 1 << bit,
            "the flip changed more than one bit")
    return bytes(out)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def flip(args):
    inputs = {"elf": args.elf, "bin": args.bin, "boot_elf": args.boot_elf,
              "boot_img": args.boot_img}
    data = {key: pathlib.Path(path).read_bytes()
            for key, path in inputs.items()}
    link_map = pathlib.Path(args.map).read_bytes()
    out = pathlib.Path(args.out)
    require(not out.exists(), f"{out} exists")
    require(0 <= args.bit < 8 * CANARY_BYTES,
            f"bit {args.bit} is outside the {CANARY_BYTES}-byte constant")
    sections, _, symbols = elf_tables(data["elf"])
    entries = symbols.get(args.symbol, [])
    require(len(entries) == 1, f"{args.symbol} is not one symbol")
    address, size = entries[0]
    require(size == CANARY_BYTES,
            f"{args.symbol} is {size} bytes, not {CANARY_BYTES}")
    require(SECTION in sections, f"the monitor has no {SECTION}")
    section_offset, section_address, section_size = sections[SECTION]
    require(section_address <= address and
            address + size <= section_address + section_size,
            f"{args.symbol} at 0x{address:x} is not inside {SECTION}")
    byte, bit = args.bit // 8, args.bit % 8
    flat_at = address - args.base
    require(0 <= flat_at and flat_at + size <= len(data["bin"]),
            f"{args.symbol} is outside the flat image")
    _, boot_segments, _ = elf_tables(data["boot_elf"])
    offsets = {
        "elf": section_offset + address - section_address,
        "bin": flat_at,
        "boot_img": args.monitor_offset + flat_at,
        "boot_elf": segment_offset(boot_segments, args.staging +
                                   args.monitor_offset + address -
                                   args.base, size),
    }
    canary = data["elf"][offsets["elf"]:offsets["elf"] + size]
    for key, at in offsets.items():
        require(data[key][at:at + size] == canary,
                f"{inputs[key]} does not hold {args.symbol}'s bytes at "
                f"0x{at:x}")
    mutated = {key: flipped(data[key], offsets[key] + byte, bit)
               for key in offsets}
    names = {"elf": "be-mvp.elf", "bin": "be-mvp.bin",
             "boot_elf": "be-mvp-boot.elf", "boot_img": "be-mvp-boot.img"}
    out.mkdir(parents=True)
    for key, name in names.items():
        (out / name).write_bytes(mutated[key])
    (out / "be-mvp.map").write_bytes(link_map)
    for sums, keys in (("be-mvp.sha256", ("bin", "elf")),
                       ("be-mvp-boot.sha256", ("boot_img", "boot_elf"))):
        (out / sums).write_text("".join(
            f"{sha256(mutated[key])}  {names[key]}\n" for key in keys),
            encoding="ascii")
    record = {
        "variant": "self-report-flip",
        "symbol": args.symbol,
        "address": f"0x{address:x}",
        "bytes": size,
        "bit": args.bit,
        "byte_offsets": {names[key]: f"0x{offsets[key] + byte:x}"
                         for key in names},
        "files": {names[key]: {"nominal_sha256": sha256(data[key]),
                               "mutated_sha256": sha256(mutated[key])}
                  for key in names},
        "nominal_image_sha256": sha256(data["boot_img"]),
        "mutated_image_sha256": sha256(mutated["boot_img"]),
    }
    (out / "self-report-flip.json").write_text(
        json.dumps(record, indent=1, sort_keys=True) + "\n",
        encoding="ascii")
    print(f"BE_MVP_FLIP: PASS {args.symbol}=0x{address:x} bit={args.bit} "
          f"image={record['mutated_image_sha256'][:12]}")


def number(text):
    return int(text, 0)


def main(argv):
    parser = argparse.ArgumentParser(add_help=False)
    for name in ("--symbol", "--elf", "--map", "--bin", "--boot-elf",
                 "--boot-img", "--out"):
        parser.add_argument(name, required=True)
    for name in ("--bit", "--base", "--staging", "--monitor-offset"):
        parser.add_argument(name, required=True, type=number)
    args = parser.parse_args(argv)
    try:
        flip(args)
    except (FlipError, OSError, ValueError, struct.error) as error:
        print(f"BE_MVP_FLIP: FAIL {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
