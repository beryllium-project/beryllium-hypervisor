#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Check B2's K3 images before B4 extracts anything from them.

  check-images.py ROOT     check ROOT/build/k3-b2/{gcc,clang}/be-k3-b2.*

For each toolchain the flat image's SHA-256 must be B2's accepted value
(bringup/k3-b2, accepted at 898af4e0); the ELF's SHA-256 is recorded as an
observed run identity only, because the accepted R5 recipes embed the build
path (DW_AT_comp_dir). From the ELF's own symbol table, read independently
of the B4 extractor, it records be_reset, be_b1_quiesce, and the two named
C cut points (be_r5_trap_dispatch, be_r5_runtime_terminal), and requires
be_reset at the K3 base and be_b1_quiesce outside the eleven scoped symbols.
"""

import hashlib
import pathlib
import struct
import sys

# B2's accepted flat-image SHA-256 values (bringup/k3-b2/README.md).
ACCEPTED_BIN_SHA256 = {
    "gcc": "9c145f000067d36035a18cc27c53bbbf231d41cb2088a7765ed5742323a08c79",
    "clang": "47be17e39350b468b528d09bd37ed8897b2eeaae575363cc7dff0252c16c54fe",
}
K3_BASE = 0x102000000
RECORDED = ["be_reset", "be_b1_quiesce", "be_r5_trap_dispatch",
            "be_r5_runtime_terminal"]
SCOPED = [
    "be_r3_arch_reset_state", "be_r3_arch_install_management",
    "be_r3_arch_enter_management", "be_r5_arch_reset_state",
    "be_r5_trap_vector", "be_r5_arch_read_controls",
    "be_r5_arch_install_root", "be_r5_arch_reset_target",
    "be_r5_arch_restore_active", "be_r5_switch_tail",
    "be_r5_enter_guest_tail",
]


class ImageError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ImageError(message)


def symbols(data):
    """{name: [(value, size)]} from the single SHT_SYMTAB of an ELF64."""
    require(data[:7] == b"\x7fELF\x02\x01\x01", "not a little-endian ELF64")
    require(struct.unpack_from("<HH", data, 16) == (2, 243),
            "not a RISC-V ET_EXEC")
    shoff = struct.unpack_from("<Q", data, 40)[0]
    shentsize, shnum = struct.unpack_from("<HH", data, 58)
    sections = [struct.unpack_from("<IIQQQQIIQQ", data, shoff + i * shentsize)
                for i in range(shnum)]
    tables = [s for s in sections if s[1] == 2]
    require(len(tables) == 1, f"{len(tables)} symbol tables, expected 1")
    _, _, _, _, offset, size, link, _, _, entsize = tables[0]
    require(entsize == 24, "unexpected symbol entry size")
    strtab = sections[link][4]
    found = {}
    for entry in range(offset + 24, offset + size, 24):
        name_offset, _, _, _, value, length = struct.unpack_from(
            "<IBBHQQ", data, entry)
        end = data.index(b"\0", strtab + name_offset)
        name = data[strtab + name_offset:end].decode()
        found.setdefault(name, []).append((value, length))
    return found


def check(root, toolchain):
    directory = root / "build" / "k3-b2" / toolchain
    flat = (directory / "be-k3-b2.bin").read_bytes()
    elf = (directory / "be-k3-b2.elf").read_bytes()
    bin_sha256 = hashlib.sha256(flat).hexdigest()
    require(bin_sha256 == ACCEPTED_BIN_SHA256[toolchain],
            f"{toolchain}: flat image SHA-256 {bin_sha256} is not B2's "
            f"accepted {ACCEPTED_BIN_SHA256[toolchain]}")
    table = symbols(elf)
    values = {}
    for name in RECORDED + SCOPED:
        entries = table.get(name, [])
        require(len(entries) == 1,
                f"{toolchain}: {name} is defined {len(entries)} times")
        values[name] = entries[0]
    require(values["be_reset"][0] == K3_BASE,
            f"{toolchain}: be_reset is not at 0x{K3_BASE:x}")
    quiesce = values["be_b1_quiesce"][0]
    for name in SCOPED:
        start, size = values[name]
        require(not start <= quiesce < start + size,
                f"{toolchain}: be_b1_quiesce lies inside {name}")
    fields = " ".join(f"{name}=0x{values[name][0]:x}" for name in RECORDED)
    return (f"{toolchain} bin_sha256={bin_sha256} "
            f"elf_sha256={hashlib.sha256(elf).hexdigest()} "
            f"elf_bytes={len(elf)} {fields}")


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    root = pathlib.Path(argv[1])
    try:
        lines = [check(root, toolchain) for toolchain in ACCEPTED_BIN_SHA256]
    except (ImageError, OSError, ValueError, struct.error) as error:
        print(f"BE_B4_R7_IMAGES: FAIL {error}")
        return 1
    for line in lines:
        print(line)
    print("BE_B4_R7_IMAGES: PASS images=2 flat=b2-accepted "
          "elf=recorded-run-identity")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
