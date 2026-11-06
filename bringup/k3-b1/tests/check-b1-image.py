#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Check B1 images: the ported R4 layout at the K3 base.

  check-b1-image.py --base B --image TOOLCHAIN:ELF:BIN [--image ...]

For each image: little-endian RV64 ET_EXEC; entry == be_reset == base; the
six accepted PT_LOAD segments with vaddr == paddr inside [base,
base + 0x34000) and the accepted permissions (no segment both writable and
executable); the fixed layout symbols at their accepted QEMU addresses plus
0x81e00000; be_b1_quiesce inside monitor text; and a flat binary that is
exactly the loaded span with every segment's file bytes in place. All images
must share one layout.
"""

import argparse
import hashlib
import struct
import sys

SPAN = 0x34000
DELTA = 0x81E00000
PF_X, PF_W, PF_R = 1, 2, 4
# Accepted R4 segment permissions, in address order.
SEGMENT_FLAGS = (PF_R | PF_X, PF_R, PF_R | PF_W, PF_R | PF_W, PF_R | PF_X,
                 PF_R | PF_X)
# Accepted QEMU addresses of the fixed layout symbols (r4-beryllium.lds).
QEMU_SYMBOLS = {
    "be_reset": 0x80200000,
    "__be_monitor_code_start": 0x80200000,
    "__be_monitor_data_start": 0x80208000,
    "__be_diagnostic_start": 0x8020F000,
    "__be_monitor_data_end": 0x80210000,
    "__be_root_management_start": 0x80214000,
    "__be_root_protected_start": 0x8021C000,
    "__be_stack_management_start": 0x80225000,
    "__be_stack_management_end": 0x80227000,
    "__be_stack_protected_start": 0x80228000,
    "__be_saved_management_start": 0x8022B000,
    "__be_saved_protected_start": 0x8022C000,
    "__be_private_management_start": 0x8022E000,
    "__be_private_protected_start": 0x8022F000,
    "__be_shared_start": 0x80230000,
    "__be_guest_management_start": 0x80232000,
    "be_r4_management_guest_start": 0x80232000,
    "__be_guest_protected_start": 0x80233000,
    "__be_guest_protected_end": 0x80234000,
}


class ImageError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ImageError(message)


def parse_elf(data):
    require(data[:7] == b"\x7fELF\x02\x01\x01", "not little-endian ELF64")
    e_type, e_machine = struct.unpack_from("<HH", data, 16)
    require(e_type == 2 and e_machine == 243, "not a RISC-V ET_EXEC")
    entry, phoff, shoff = struct.unpack_from("<QQQ", data, 24)
    phentsize, phnum, shentsize, shnum, shstrndx = struct.unpack_from(
        "<HHHHH", data, 54)
    segments = []
    for index in range(phnum):
        (p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz,
         _align) = struct.unpack_from("<IIQQQQQQ", data, phoff + index * phentsize)
        if p_type == 1:
            segments.append((p_vaddr, p_paddr, p_offset, p_filesz, p_memsz,
                             p_flags))
    sections = []
    for index in range(shnum):
        sections.append(struct.unpack_from("<IIQQQQIIQQ", data,
                                           shoff + index * shentsize))
    symbols = {}
    for sh_name, sh_type, *_rest in sections:
        if sh_type != 2:  # SHT_SYMTAB
            continue
        _, _, _, _, sym_offset, sym_size, sym_link, _, _, _ = \
            sections[sections.index((sh_name, sh_type, *_rest))]
        strtab_offset = sections[sym_link][4]
        for entry_offset in range(sym_offset, sym_offset + sym_size, 24):
            st_name, _, _, _, st_value, _ = struct.unpack_from(
                "<IBBHQQ", data, entry_offset)
            end = data.index(b"\0", strtab_offset + st_name)
            name = data[strtab_offset + st_name:end].decode()
            if name:
                symbols[name] = st_value
    return entry, segments, symbols


def check_image(base, elf_path, bin_path):
    data = open(elf_path, "rb").read()
    flat = open(bin_path, "rb").read()
    entry, segments, symbols = parse_elf(data)
    require(entry == base, f"entry 0x{entry:x} != base 0x{base:x}")
    require(len(segments) == len(SEGMENT_FLAGS),
            f"{len(segments)} PT_LOAD segments, expected {len(SEGMENT_FLAGS)}")
    for (vaddr, paddr, offset, filesz, memsz, flags), wanted in zip(
            sorted(segments), SEGMENT_FLAGS):
        require(vaddr == paddr, f"segment 0x{vaddr:x} has paddr 0x{paddr:x}")
        require(base <= paddr and paddr + memsz <= base + SPAN,
                f"segment 0x{paddr:x}+0x{memsz:x} leaves the span")
        require(not (flags & PF_W and flags & PF_X),
                f"segment 0x{paddr:x} is writable and executable")
        require(flags == wanted,
                f"segment 0x{paddr:x} flags {flags} != accepted {wanted}")
        require(flat[paddr - base:paddr - base + filesz] ==
                data[offset:offset + filesz],
                f"flat binary differs from segment 0x{paddr:x}")
    require(len(flat) == SPAN, f"flat binary is 0x{len(flat):x} bytes")
    for name, qemu_address in QEMU_SYMBOLS.items():
        require(symbols.get(name) == qemu_address + DELTA,
                f"{name} at 0x{symbols.get(name, 0):x}, expected "
                f"0x{qemu_address + DELTA:x}")
    quiesce = symbols.get("be_b1_quiesce", 0)
    require(base <= quiesce < symbols["__be_monitor_data_start"],
            "be_b1_quiesce is outside monitor text")
    return {name: symbols[name] for name in QEMU_SYMBOLS}, quiesce


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=lambda value: int(value, 0),
                        required=True)
    parser.add_argument("--image", action="append", required=True)
    args = parser.parse_args(argv[1:])
    layouts = []
    try:
        for spec in args.image:
            toolchain, elf_path, bin_path = spec.split(":")
            layout, quiesce = check_image(args.base, elf_path, bin_path)
            layouts.append(layout)
            print(f"{toolchain}: entry=0x{args.base:x} be_b1_quiesce=0x{quiesce:x} "
                  f"bin_sha256={hashlib.sha256(open(bin_path, 'rb').read()).hexdigest()}")
        require(all(layout == layouts[0] for layout in layouts),
                "toolchain layouts differ")
    except (ImageError, OSError, ValueError) as error:
        print(f"BE_B1_IMAGE_CHECK: FAIL {error}")
        return 1
    print(f"BE_B1_IMAGE_CHECK: PASS images={len(layouts)} "
          f"span=0x{args.base:x}-0x{args.base + SPAN:x}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
