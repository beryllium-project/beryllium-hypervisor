#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Check B3 booti images: Linux RISC-V Image header, descriptor, payload.

  check-b3-image.py --image TOOLCHAIN:IMG[:ELF] [--image ...]
                    [--variant NAME:TOOLCHAIN:TEXT_OFFSET:EXPECT:IMG ...]
                    [--ram-base B] [--load-address A] [--qemu-ram-base Q]
  check-b3-image.py --check-payload TOOLCHAIN:B2_BIN [--check-payload ...]
  check-b3-image.py --self-test

Every image must be exactly 0x35000 bytes:

- a 64-byte Linux RISC-V Image header (Documentation/arch/riscv/
  boot-image-header.rst): code0 a `j` (jal x0) to the stub entry inside
  the first page, code1 0, text_offset 0x200000 (a variant's own value),
  image_size equal to the file size, flags 0 (little-endian), version 0x2,
  res1/res2/res3 0, magic "RISCV\\0\\0\\0", and magic2 "RSC\\x05", which is
  the only magic U-Boot v2022.10 booti_setup() checks;
- the descriptor at 0x40 that the stub reads: magic "BEK3B3D1",
  destination 0x1_0200_0000, length 0x34000, payload offset 0x1000;
- both report-line templates in the stub page;
- at 0x1000, a payload byte-identical to the accepted B2 flat image of the
  image's toolchain (SHA-256 pinned below; B2 accepted at 898af4e0).

Placement on the COM260: booti moves an Image loaded inside RAM to the RAM
base (--ram-base, default 0x1_0200_0000) plus text_offset. The moved image
must not overlap the destination, must end below the load address
(--load-address, default 0x1_4000_0000), and the destination must lie in
System RAM above OpenSBI. A variant (QEMU only) states whether its
placement at --qemu-ram-base (default 0x8000_0000, QEMU virt) overlaps the
destination (EXPECT overlap) or not (EXPECT pass).

With an ELF, its entry must be the header, and no PT_LOAD may be both
writable and executable. --check-payload checks a B2 flat image against the
pin before the build wraps it.
"""

import argparse
import hashlib
import struct
import sys
import zlib

IMAGE_SIZE = 0x35000
STUB_PAGE = 0x1000
TEXT_OFFSET = 0x200000
DEST = 0x102000000
PAYLOAD_SIZE = 0x34000
PAYLOAD_OFFSET = 0x1000
K3_RAM_BASE = 0x102000000
K3_SYSTEM_RAM = (0x102000000, 0x300000000)
K3_OPENSBI = (0x100000000, 0x102000000)
LOAD_ADDRESS = 0x140000000
QEMU_RAM_BASE = 0x80000000
HEADER = struct.Struct("<IIQQQIIQ8s4sI")
DESCRIPTOR = struct.Struct("<8sQQQ")
DESCRIPTOR_OFFSET = 0x40
DESCRIPTOR_MAGIC = b"BEK3B3D1"
UBOOT_MAGIC_OFFSET = 0x38
UBOOT_MAGIC = 0x05435352
TEMPLATES = (
    b"BE_K3_B3: SHIM hart=0x" + b"?" * 16 + b" shim=0x" + b"?" * 16 +
    b" fdt=0x" + b"?" * 16 + b" dest=0x" + b"?" * 16 + b" bytes=0x" +
    b"?" * 16 + b"\n",
    b"BE_K3_B3: FAIL overlap shim=0x" + b"?" * 16 + b"\n",
)
# Accepted B2 flat images (bringup/k3-b2/README.md, accepted at 898af4e0).
B2_SHA256 = {
    "gcc": "9c145f000067d36035a18cc27c53bbbf231d41cb2088a7765ed5742323a08c79",
    "clang": "47be17e39350b468b528d09bd37ed8897b2eeaae575363cc7dff0252c16c54fe",
}
PT_LOAD = 1
PF_X = 1
PF_W = 2


def sha256(data):
    return hashlib.sha256(data).hexdigest()


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


def overlaps(start, size, other_start, other_size):
    return start < other_start + other_size and other_start < start + size


def check_header(data, text_offset, findings):
    if len(data) < HEADER.size:
        findings.append(f"image shorter than the {HEADER.size}-byte header")
        return None
    (code0, code1, offset, image_size, flags, version, res1, res2, magic,
     magic2, res3) = HEADER.unpack_from(data)
    jump = jal_target(code0)
    entry = None
    if jump is None or jump[0] != 0:
        findings.append(f"code0 0x{code0:08x} is not `j` (jal x0)")
    elif not HEADER.size + DESCRIPTOR.size <= jump[1] < STUB_PAGE or \
            jump[1] % 4:
        findings.append(f"code0 jumps to +0x{jump[1]:x}, outside the stub")
    else:
        entry = jump[1]
    if code1 != 0:
        findings.append(f"code1 0x{code1:08x} != 0")
    if offset != text_offset:
        findings.append(f"text_offset 0x{offset:x} != 0x{text_offset:x}")
    if image_size != len(data):
        findings.append(f"image_size 0x{image_size:x} != file size "
                        f"0x{len(data):x}")
    if flags != 0:
        findings.append(f"flags 0x{flags:x} != 0 (little-endian)")
    if version != 2:
        findings.append(f"header version 0x{version:x} != 0x2")
    if res1 or res2 or res3:
        findings.append("reserved header fields are nonzero")
    if magic != b"RISCV\0\0\0":
        findings.append(f"magic {magic!r} != b'RISCV\\x00\\x00\\x00'")
    if magic2 != b"RSC\x05":
        findings.append(f"magic2 {magic2!r} != b'RSC\\x05'")
    uboot_magic = struct.unpack_from("<I", data, UBOOT_MAGIC_OFFSET)[0]
    if uboot_magic != UBOOT_MAGIC or image_size == 0:
        findings.append("U-Boot v2022.10 booti_setup() would reject it")
    return {"entry": entry, "text_offset": offset, "image_size": image_size}


def check_descriptor(data, findings):
    if len(data) < DESCRIPTOR_OFFSET + DESCRIPTOR.size:
        findings.append("image shorter than the descriptor")
        return
    magic, dest, size, offset = DESCRIPTOR.unpack_from(data,
                                                       DESCRIPTOR_OFFSET)
    if magic != DESCRIPTOR_MAGIC:
        findings.append(f"descriptor magic {magic!r} != {DESCRIPTOR_MAGIC!r}")
    if dest != DEST:
        findings.append(f"descriptor destination 0x{dest:x} != 0x{DEST:x}")
    if size != PAYLOAD_SIZE:
        findings.append(f"descriptor length 0x{size:x} != 0x{PAYLOAD_SIZE:x}")
    if offset != PAYLOAD_OFFSET:
        findings.append(f"descriptor payload offset 0x{offset:x} != "
                        f"0x{PAYLOAD_OFFSET:x}")


def check_image(data, text_offset, payload_sha256):
    """Return (findings, facts) for one image's bytes."""
    findings = []
    if len(data) != IMAGE_SIZE:
        findings.append(f"file size 0x{len(data):x} != 0x{IMAGE_SIZE:x}")
    header = check_header(data, text_offset, findings)
    check_descriptor(data, findings)
    stub = data[:STUB_PAGE]
    for template in TEMPLATES:
        if stub.count(template) != 1:
            findings.append(f"stub page lacks the template {template[:24]!r}")
    payload = data[PAYLOAD_OFFSET:PAYLOAD_OFFSET + PAYLOAD_SIZE]
    if sha256(payload) != payload_sha256 or len(payload) != PAYLOAD_SIZE:
        findings.append("payload is not the accepted B2 image")
    facts = {
        "bytes": len(data),
        "sha256": sha256(data),
        "crc32": f"{zlib.crc32(data):08x}",
        "stub_sha256": sha256(stub),
        "payload_sha256": sha256(payload),
        "entry": header["entry"] if header else None,
        "text_offset": header["text_offset"] if header else None,
    }
    return findings, facts


def check_placement(ram_base, text_offset, load_address, findings):
    """booti's move of an image loaded at load_address on the COM260."""
    relocated = ram_base + text_offset
    if overlaps(relocated, IMAGE_SIZE, DEST, PAYLOAD_SIZE):
        findings.append(f"moved image 0x{relocated:x}+0x{IMAGE_SIZE:x} "
                        f"overlaps the destination 0x{DEST:x}")
    if relocated + IMAGE_SIZE > load_address:
        findings.append(f"moved image ends above the load address "
                        f"0x{load_address:x}")
    if relocated < K3_SYSTEM_RAM[0] or \
            relocated + IMAGE_SIZE > K3_SYSTEM_RAM[1]:
        findings.append("moved image is outside COM260 System RAM")
    if DEST < K3_SYSTEM_RAM[0] or DEST + PAYLOAD_SIZE > K3_SYSTEM_RAM[1]:
        findings.append("destination is outside COM260 System RAM")
    if overlaps(DEST, PAYLOAD_SIZE, K3_OPENSBI[0],
                K3_OPENSBI[1] - K3_OPENSBI[0]):
        findings.append("destination overlaps the OpenSBI region")
    return relocated


def check_elf(path, findings):
    with open(path, "rb") as handle:
        elf = handle.read()
    if elf[:4] != b"\x7fELF" or elf[4] != 2 or elf[5] != 1:
        findings.append(f"{path}: not a little-endian ELF64")
        return None
    (e_type, e_machine, _, e_entry, e_phoff, _, _, _, e_phentsize,
     e_phnum, _, _, _) = struct.unpack_from("<HHIQQQIHHHHHH", elf, 16)
    if e_type != 2 or e_machine != 243:
        findings.append(f"{path}: not a RISC-V ET_EXEC image")
    loads = []
    for index in range(e_phnum):
        (p_type, p_flags, _, p_vaddr, p_paddr, _, p_memsz,
         _) = struct.unpack_from("<IIQQQQQQ", elf, e_phoff + index * e_phentsize)
        if p_type != PT_LOAD:
            continue
        loads.append((p_vaddr, p_memsz, p_flags))
        if p_flags & PF_W and p_flags & PF_X:
            findings.append(f"{path}: PT_LOAD at 0x{p_vaddr:x} is W+X")
        if p_vaddr != p_paddr:
            findings.append(f"{path}: PT_LOAD vaddr != paddr")
    if not loads or e_entry != min(start for start, _, _ in loads):
        findings.append(f"{path}: entry 0x{e_entry:x} is not the header")
    elif max(start + size for start, size, _ in loads) - e_entry != \
            IMAGE_SIZE:
        findings.append(f"{path}: PT_LOAD span is not 0x{IMAGE_SIZE:x}")
    return e_entry


def check_payload(spec):
    toolchain, _, path = spec.partition(":")
    with open(path, "rb") as handle:
        data = handle.read()
    ok = toolchain in B2_SHA256 and sha256(data) == B2_SHA256[toolchain] \
        and len(data) == PAYLOAD_SIZE
    print(f"BE_B3_PAYLOAD[{toolchain}]: {'PASS' if ok else 'FAIL'} "
          f"{path} sha256={sha256(data)} bytes=0x{len(data):x}")
    return ok


def synthetic(text_offset=TEXT_OFFSET, payload=b"\xa5" * PAYLOAD_SIZE):
    """A well-formed image around a stand-in payload, for the self-test."""
    entry = HEADER.size + DESCRIPTOR.size
    imm = entry
    code0 = 0x6F | (((imm >> 20) & 1) << 31) | (((imm >> 1) & 0x3FF) << 21) \
        | (((imm >> 11) & 1) << 20) | (((imm >> 12) & 0xFF) << 12)
    header = HEADER.pack(code0, 0, text_offset, IMAGE_SIZE, 0, 2, 0, 0,
                         b"RISCV\0\0\0", b"RSC\x05", 0)
    descriptor = DESCRIPTOR.pack(DESCRIPTOR_MAGIC, DEST, PAYLOAD_SIZE,
                                 PAYLOAD_OFFSET)
    stub = header + descriptor + b"\x13\x00\x00\x00" * 8 + b"".join(TEMPLATES)
    return bytearray(stub.ljust(STUB_PAGE, b"\0") + payload)


def self_test():
    payload = b"\xa5" * PAYLOAD_SIZE
    pin = sha256(payload)

    def mutate(offset, value):
        image = synthetic()
        image[offset:offset + len(value)] = value
        return bytes(image)

    cases = [
        ("valid", bytes(synthetic()), TEXT_OFFSET, True),
        ("variant text_offset", bytes(synthetic(0x82000000)), 0x82000000,
         True),
        ("wrong text_offset", bytes(synthetic(0x82000000)), TEXT_OFFSET,
         False),
        ("truncated", bytes(synthetic())[:-8], TEXT_OFFSET, False),
        ("padded", bytes(synthetic()) + b"\0" * 8, TEXT_OFFSET, False),
        ("code0 not jal", mutate(0, struct.pack("<I", 0x00000013)),
         TEXT_OFFSET, False),
        ("code0 jal with link", mutate(0, struct.pack("<I", 0x060000EF)),
         TEXT_OFFSET, False),
        ("code0 into descriptor", mutate(0, struct.pack("<I", 0x0400006F)),
         TEXT_OFFSET, False),
        ("code1 nonzero", mutate(4, b"\x01"), TEXT_OFFSET, False),
        ("image_size wrong", mutate(0x10, struct.pack("<Q", 0x34000)),
         TEXT_OFFSET, False),
        ("flags big-endian", mutate(0x18, b"\x01"), TEXT_OFFSET, False),
        ("version 1", mutate(0x20, b"\x01"), TEXT_OFFSET, False),
        ("res2 nonzero", mutate(0x28, b"\x01"), TEXT_OFFSET, False),
        ("bad magic", mutate(0x30, b"RISCW"), TEXT_OFFSET, False),
        ("bad magic2", mutate(0x38, b"RSC\x04"), TEXT_OFFSET, False),
        ("res3 nonzero", mutate(0x3C, b"\x01"), TEXT_OFFSET, False),
        ("descriptor magic", mutate(0x40, b"X"), TEXT_OFFSET, False),
        ("descriptor destination", mutate(0x48, struct.pack("<Q",
                                                            0x102200000)),
         TEXT_OFFSET, False),
        ("descriptor length", mutate(0x50, struct.pack("<Q", 0x34008)),
         TEXT_OFFSET, False),
        ("descriptor payload offset", mutate(0x58, struct.pack("<Q", 0x2000)),
         TEXT_OFFSET, False),
        ("template damaged", mutate(0x80 + 5, b"X"), TEXT_OFFSET, False),
        ("payload byte flipped", mutate(PAYLOAD_OFFSET + 0x1234, b"\x5a"),
         TEXT_OFFSET, False),
    ]
    failed = 0
    for name, data, text_offset, wanted in cases:
        findings, _ = check_image(data, text_offset, pin)
        ok = not findings
        failed += ok != wanted
        print(f"{'ok  ' if ok == wanted else 'FAIL'} {name}: ok={ok} "
              f"findings={findings}")
    placements = [
        ("COM260 text_offset", K3_RAM_BASE, TEXT_OFFSET, True),
        ("text_offset 0 overlaps", K3_RAM_BASE, 0, False),
        ("end overlaps", K3_RAM_BASE - 0x34000, 0, False),
        ("below RAM, in OpenSBI", K3_RAM_BASE - IMAGE_SIZE, 0, False),
        ("just above", K3_RAM_BASE, PAYLOAD_SIZE, True),
        ("past the load address", K3_RAM_BASE, 0x3e000000, False),
    ]
    for name, ram_base, text_offset, wanted in placements:
        findings = []
        check_placement(ram_base, text_offset, LOAD_ADDRESS, findings)
        ok = not findings
        failed += ok != wanted
        print(f"{'ok  ' if ok == wanted else 'FAIL'} placement {name}: "
              f"ok={ok} findings={findings}")
    total = len(cases) + len(placements)
    print(f"BE_B3_IMAGE_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
          f"cases={total}")
    return 0 if not failed else 1


def number(value):
    return int(value, 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.
                                     RawDescriptionHelpFormatter)
    parser.add_argument("--image", action="append", default=[])
    parser.add_argument("--variant", action="append", default=[])
    parser.add_argument("--check-payload", action="append", default=[])
    parser.add_argument("--ram-base", type=number, default=K3_RAM_BASE)
    parser.add_argument("--load-address", type=number, default=LOAD_ADDRESS)
    parser.add_argument("--qemu-ram-base", type=number, default=QEMU_RAM_BASE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.check_payload:
        results = [check_payload(spec) for spec in args.check_payload]
        return 0 if all(results) else 1
    if not args.image and not args.variant:
        parser.error("nothing to check")
    failed = 0
    for spec in args.image:
        toolchain, _, rest = spec.partition(":")
        path, _, elf = rest.partition(":")
        findings = []
        if toolchain not in B2_SHA256:
            findings.append(f"unknown toolchain {toolchain!r}")
            pin = ""
        else:
            pin = B2_SHA256[toolchain]
        with open(path, "rb") as handle:
            data = handle.read()
        image_findings, facts = check_image(data, TEXT_OFFSET, pin)
        findings += image_findings
        relocated = check_placement(args.ram_base, TEXT_OFFSET,
                                    args.load_address, findings)
        if elf:
            entry = check_elf(elf, findings)
            if entry is not None and entry != relocated:
                findings.append(f"{elf}: linked at 0x{entry:x}, not the "
                                f"COM260 booti address 0x{relocated:x}")
        for finding in findings:
            print(f"finding[{toolchain}]: {finding}")
        print(f"BE_B3_IMAGE[{toolchain}]: {'PASS' if not findings else 'FAIL'}"
              f" {path} bytes=0x{facts['bytes']:x} sha256={facts['sha256']} "
              f"crc32={facts['crc32']}")
        print(f"  header: j +0x{facts['entry'] or 0:x}, text_offset="
              f"0x{facts['text_offset']:x}, image_size=0x{len(data):x}; "
              f"stub page sha256={facts['stub_sha256']}")
        print(f"  payload: +0x{PAYLOAD_OFFSET:x} 0x{PAYLOAD_SIZE:x} bytes "
              f"sha256={facts['payload_sha256']} (accepted B2 {toolchain})")
        print(f"  COM260: booti 0x{args.load_address:x} -> 0x{relocated:x}-"
              f"0x{relocated + IMAGE_SIZE:x}; copy to 0x{DEST:x}-"
              f"0x{DEST + PAYLOAD_SIZE:x}")
        failed += bool(findings)
    for spec in args.variant:
        name, toolchain, text_offset, expect, path = spec.split(":", 4)
        text_offset = int(text_offset, 0)
        with open(path, "rb") as handle:
            data = handle.read()
        findings, facts = check_image(data, text_offset,
                                      B2_SHA256.get(toolchain, ""))
        relocated = args.qemu_ram_base + text_offset
        overlap = overlaps(relocated, IMAGE_SIZE, DEST, PAYLOAD_SIZE)
        if expect not in ("pass", "overlap") or \
                overlap != (expect == "overlap"):
            findings.append(f"QEMU placement 0x{relocated:x} gives "
                            f"overlap={overlap}, expected {expect}")
        for finding in findings:
            print(f"finding[{name}]: {finding}")
        print(f"BE_B3_VARIANT[{name}]: {'PASS' if not findings else 'FAIL'} "
              f"text_offset=0x{text_offset:x} qemu_booti=0x{relocated:x} "
              f"overlap={'yes' if overlap else 'no'} sha256={facts['sha256']}")
        failed += bool(findings)
    print(f"BE_B3_IMAGES: {'PASS' if not failed else 'FAIL'} "
          f"images={len(args.image)} variants={len(args.variant)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
