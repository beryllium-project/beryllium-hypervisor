#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Check the B0 Linux RISC-V Image header, size, and position independence.

Every ``--variant BASE:BIN:ELF`` is the same objects linked at BASE. The raw
images must be byte-identical (no embedded absolute address), each ELF must
start at its base with no relocation sections, and the published image must
equal the variants and carry a header that U-Boot booti and Linux
kexec_file_load accept.
"""

import argparse
import hashlib
import struct
import sys

HEADER = struct.Struct("<IIQQQIIQ8s4sI")
IMAGE_LIMIT = 1 << 20
SHT_RELA = 4
SHT_REL = 9


def jal_target(word):
    """Decode a JAL; return (rd, byte offset) or None."""
    if word & 0x7F != 0x6F:
        return None
    rd = (word >> 7) & 0x1F
    imm = (((word >> 31) & 0x1) << 20) | (((word >> 12) & 0xFF) << 12) | \
        (((word >> 20) & 0x1) << 11) | (((word >> 21) & 0x3FF) << 1)
    if imm & (1 << 20):
        imm -= 1 << 21
    return rd, imm


def check_header(data, findings):
    if len(data) < HEADER.size:
        findings.append(f"image shorter than the {HEADER.size}-byte header")
        return {}
    (code0, code1, text_offset, image_size, flags, version, res1, res2,
     magic, magic2, res3) = HEADER.unpack_from(data)
    jump = jal_target(code0)
    if jump is None or jump[0] != 0:
        findings.append(f"code0 0x{code0:08x} is not `j` (jal x0)")
    elif not HEADER.size <= jump[1] < len(data):
        findings.append(f"code0 jumps to +0x{jump[1]:x}, outside the image")
    if code1 != 0:
        findings.append(f"code1 0x{code1:08x} != 0")
    if text_offset != 0x200000:
        findings.append(f"text_offset 0x{text_offset:x} != 0x200000")
    if not len(data) <= image_size <= IMAGE_LIMIT or image_size % 4096:
        findings.append(f"image_size 0x{image_size:x} invalid for "
                        f"{len(data)}-byte file")
    if flags != 0:
        findings.append(f"flags 0x{flags:x} != 0 (little endian)")
    if version != 2:
        findings.append(f"header version 0x{version:x} != 0x2")
    if res1 or res2 or res3:
        findings.append("reserved header fields are nonzero")
    if magic != b"RISCV\0\0\0":
        findings.append(f"magic {magic!r} != b'RISCV\\0\\0\\0'")
    if magic2 != b"RSC\x05":
        findings.append(f"magic2 {magic2!r} != b'RSC\\x05'")
    return {
        "entry_offset": jump[1] if jump else None,
        "image_size": image_size,
        "text_offset": text_offset,
    }


def check_elf(path, base, findings):
    with open(path, "rb") as handle:
        elf = handle.read()
    if elf[:4] != b"\x7fELF" or elf[4] != 2 or elf[5] != 1:
        findings.append(f"{path}: not a little-endian ELF64")
        return
    (e_type, e_machine, _, e_entry, _, e_shoff, _, _, _, _, e_shentsize,
     e_shnum, _) = struct.unpack_from("<HHIQQQIHHHHHH", elf, 16)
    if e_type != 2 or e_machine != 243:
        findings.append(f"{path}: not a RISC-V ET_EXEC image")
    if e_entry != base:
        findings.append(f"{path}: entry 0x{e_entry:x} != base 0x{base:x}")
    for index in range(e_shnum):
        sh_type = struct.unpack_from(
            "<I", elf, e_shoff + index * e_shentsize + 4)[0]
        if sh_type in (SHT_RELA, SHT_REL):
            findings.append(f"{path}: carries a relocation section")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--variant", action="append", default=[],
                        metavar="BASE:BIN:ELF")
    args = parser.parse_args()

    findings = []
    with open(args.image, "rb") as handle:
        image = handle.read()
    header = check_header(image, findings)
    digest = hashlib.sha256(image).hexdigest()

    bases = []
    for variant in args.variant:
        base_text, binary, elf = variant.split(":", 2)
        base = int(base_text, 0)
        bases.append(base)
        with open(binary, "rb") as handle:
            if handle.read() != image:
                findings.append(f"{binary} (base 0x{base:x}) differs from "
                                "the published image")
        check_elf(elf, base, findings)
    if len(set(bases)) < 2:
        findings.append("position independence needs at least two bases")

    print(f"image={args.image}")
    print(f"sha256={digest}")
    print(f"file_bytes={len(image)}")
    for key, value in header.items():
        print(f"{key}={value if value is None else hex(value)}")
    print("identical_bases=" + ",".join(hex(base) for base in bases))
    for finding in findings:
        print(f"finding: {finding}")
    print("BE_B0_IMAGE_CHECK: " + ("FAIL" if findings else "PASS"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
