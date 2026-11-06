#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Generate the MVP monitor's payload layout from the staged payload.

  gen-payload.py header KERNEL DTB0 DTB1 OUT  write the payload-layout header
  gen-payload.py alter-magic2 KERNEL OUT      write the payload variant's kernel

The MVP boot image (planning/mvp-m0-plan.md, "Memory and load paths", and
Plan revision M0-A.1; B7's scripts/gen-payload.py with MVP names) holds B3's
shim page, the monitor's 0xa4000-byte flat image at 0x1000, the kernel Image
at 0xa5000 (src/mvp-layout.h's BE_MVP_BOOT_KERNEL_OFFSET), G0's 4 KiB DTB at
the next 4 KiB boundary, and G1's 4 KiB DTB right after it, which ends the
image. The monitor takes the payload's
sizes and offsets from link-time constants; `header` derives them from the
actual payload files after an independent shape check (the kernel's RISC-V
Image header and each DTB's FDT header, as the monitor checks them) and the
budgets in src/mvp-layout.h, and writes them as BE_MVP_C() literals.

`alter-magic2` copies a kernel Image with magic2 "RSC\\x05" changed to
"RSC\\x00", the plan's `payload` negative variant: the monitor must refuse it
with BE_MVP:FAIL payload before it touches either domain window.
"""

import hashlib
import pathlib
import re
import struct
import sys

HERE = pathlib.Path(__file__).resolve()
LAYOUT_H = HERE.parents[1] / "src" / "mvp-layout.h"
IMAGE_HEADER = struct.Struct("<IIQQQIIQ8s4sI")
FDT_HEADER = struct.Struct(">10I")
FDT_MAGIC = 0xD00DFEED
PAGE = 0x1000


class PayloadError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise PayloadError(message)


def layout_constants(path=LAYOUT_H):
    """Every BE_MVP_* literal in mvp-layout.h, as integers."""
    text = path.read_text(encoding="utf-8")
    values = {name: int(value, 0) for name, value in re.findall(
        r"^#define\s+(BE_MVP_\w+)\s+BE_MVP_C\((0x[0-9a-fA-F]+|\d+)\)", text,
        re.M)}
    require("BE_MVP_BOOT_KERNEL_OFFSET" in values,
            f"{path} defines no BE_MVP_BOOT_KERNEL_OFFSET")
    return values


def kernel_facts(data, constants):
    """Independent RISC-V Image header checks; (bytes, image_size)."""
    require(len(data) >= IMAGE_HEADER.size, "kernel is shorter than its header")
    (_, _, text_offset, image_size, flags, _, _, _, magic, magic2,
     _) = IMAGE_HEADER.unpack_from(data)
    require(magic == b"RISCV\0\0\0", f"kernel magic {magic!r}")
    require(magic2 == b"RSC\x05", f"kernel magic2 {magic2!r}")
    require(text_offset == constants["BE_MVP_KERNEL_TEXT_OFFSET"],
            f"kernel text_offset 0x{text_offset:x}")
    require(flags & 1 == 0, "kernel is big-endian")
    require(len(data) <= constants["BE_MVP_KERNEL_FILE_MAX"],
            f"kernel file 0x{len(data):x} exceeds its budget")
    require(len(data) <= image_size <=
            constants["BE_MVP_KERNEL_IMAGE_SIZE_MAX"],
            f"kernel image_size 0x{image_size:x} is below the file or over "
            f"its budget")
    span_end = constants["BE_MVP_KERNEL_GPA"] + image_size
    require(span_end <= constants["BE_MVP_DTB_GPA"],
            f"kernel span ends at 0x{span_end:x}, past the DTB slot")
    return len(data), image_size


def dtb_facts(data, constants):
    """Independent FDT header checks; the DTB's size."""
    require(len(data) == constants["BE_MVP_DTB_BYTES"],
            f"DTB is 0x{len(data):x} bytes, not 0x"
            f"{constants['BE_MVP_DTB_BYTES']:x}")
    (magic, total, off_struct, off_strings, off_rsvmap, version, _, _,
     size_strings, size_struct) = FDT_HEADER.unpack_from(data)
    require(magic == FDT_MAGIC, f"DTB magic 0x{magic:x}")
    require(total == len(data), f"DTB totalsize 0x{total:x}")
    require(version == 17, f"DTB version {version}")
    for name, offset, size, alignment in (
            ("reserve map", off_rsvmap, 16, 8),
            ("structure block", off_struct, size_struct, 4),
            ("strings block", off_strings, size_strings, 1)):
        require(FDT_HEADER.size <= offset and offset + size <= total and
                offset % alignment == 0, f"DTB {name} leaves the blob")
    return len(data)


def layout(kernel, dtbs, constants):
    kernel_bytes, image_size = kernel_facts(kernel, constants)
    dtb_bytes = [dtb_facts(dtb, constants) for dtb in dtbs]
    require(len(dtb_bytes) == constants["BE_MVP_DOMAINS"],
            f"{len(dtb_bytes)} DTBs for {constants['BE_MVP_DOMAINS']} domains")
    kernel_offset = constants["BE_MVP_BOOT_KERNEL_OFFSET"]
    dtb0_offset = (kernel_offset + kernel_bytes + PAGE - 1) // PAGE * PAGE
    dtb1_offset = dtb0_offset + dtb_bytes[0]
    image_bytes = dtb1_offset + dtb_bytes[1]
    require(image_bytes <= constants["BE_MVP_BOOT_IMAGE_MAX"],
            f"boot image 0x{image_bytes:x} exceeds its budget")
    return {
        "KERNEL_BYTES": kernel_bytes,
        "KERNEL_IMAGE_SIZE": image_size,
        "DTB0_OFFSET": dtb0_offset,
        "DTB1_OFFSET": dtb1_offset,
        "IMAGE_BYTES": image_bytes,
    }


def header(kernel_path, dtb_paths, out_path):
    kernel = pathlib.Path(kernel_path).read_bytes()
    dtbs = [pathlib.Path(path).read_bytes() for path in dtb_paths]
    values = layout(kernel, dtbs, layout_constants())
    lines = [
        "/* SPDX-License-Identifier: GPL-3.0-only */",
        "/*",
        " * Generated by mvp/tools/gen-payload.py; do not edit.",
        " * The staged payload's link-time layout (src/mvp-payload.h):",
        f" *   kernel {pathlib.Path(kernel_path).name} sha256 "
        f"{hashlib.sha256(kernel).hexdigest()}",
    ]
    for guest, (path, dtb) in enumerate(zip(dtb_paths, dtbs)):
        lines.append(f" *   dtb{guest} {pathlib.Path(path).name} sha256 "
                     f"{hashlib.sha256(dtb).hexdigest()}")
    lines += [
        " */",
        "",
        "#ifndef BE_MVP_PAYLOAD_LAYOUT_H",
        "#define BE_MVP_PAYLOAD_LAYOUT_H",
        "",
        '#include "mvp-layout.h"',
        "",
    ]
    for name, value in values.items():
        lines.append(f"#define BE_MVP_PAYLOAD_{name}\tBE_MVP_C(0x{value:x})")
    lines += ["", "#endif", ""]
    pathlib.Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    print("BE_MVP_PAYLOAD: PASS " + " ".join(
        f"{name.lower()}=0x{value:x}" for name, value in values.items()))


def alter_magic2(kernel_path, out_path):
    data = bytearray(pathlib.Path(kernel_path).read_bytes())
    require(data[0x38:0x3C] == b"RSC\x05", "kernel magic2 is not RSC\\x05")
    data[0x3B] = 0
    pathlib.Path(out_path).write_bytes(bytes(data))
    print(f"BE_MVP_PAYLOAD: VARIANT magic2={bytes(data[0x38:0x3C])!r} "
          f"sha256={hashlib.sha256(data).hexdigest()}")


def main(argv):
    try:
        if len(argv) == 6 and argv[1] == "header":
            header(argv[2], argv[3:5], argv[5])
            return 0
        if len(argv) == 4 and argv[1] == "alter-magic2":
            alter_magic2(argv[2], argv[3])
            return 0
    except (OSError, PayloadError, struct.error) as error:
        print(f"BE_MVP_PAYLOAD: FAIL {error}")
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
