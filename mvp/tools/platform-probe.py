#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# tools/kexec-load.py's read-only probe and layout rule, kept when M5
# removed its loading code (planning/mvp-m5-plan.md, Q6).
"""The MVP's read-only platform probe and layout rule.

  platform-probe.py probe             report the board's FDT reservations
  platform-probe.py region-check LAYOUT PREFLIGHT
                                      offline: are the MVP's extents free in a
                                      preflight record

probe reads /sys/firmware/fdt (as root, through tools/k3-preflight.sh) and
prints one line, fdt_reserved=: every range of the FDT's reservation block
and of /reserved-memory's reg properties, `none`, or why it could not be
read. It reads nothing else and writes nothing; it calls no kexec
interface (S3-A policy item 2: kexec is not used).

The layout rule (planning/mvp-m0-plan.md, "Hart region"; Plan revision
M0-A.1) covers every MVP extent the shim and the monitor write: the
core [BE_MVP_MONITOR_HPA, + BE_MVP_CORE_BYTES) (M6: the flat image's
first 0x34000 bytes, the MVP's own layout), the pool, the hart region,
the MVP region, the staging reserve [L, L + BE_MVP_STAGING_BYTES) (the
image's maximum rounded up to 2 MiB plus the 2 MiB slot the kexec era
kept after it, unchanged in extent), both domain windows, and the shared pages
[BE_MVP_SHARED_PAGES_HPA, + BE_MVP_SHARED_PAGES_BYTES)
(planning/mvp-m2-plan.md, Q1 and "Memory and load paths"), three pages
whose first is M1's channel page (planning/mvp-m1-plan.md, Q1), which
every image's layout holds whether or not its scenario maps them. The
staging region keeps the slot after the image that the kexec loader gave
the FDT copy (the scenarios' kexec_fdt object): under U-Boot's booti it is
reserved and unused, and the extent list is unchanged (Q6). Each extent
must lie inside one System RAM range, clear of its children and of every
FDT reservation. region-check reads a k3-preflight.sh record (its
fdt_reserved= line and its iomem_system_ram_begin/_end section of every
System RAM range and child) and stops on any finding.
"""

import platform
import re
import struct
import sys

PAGE = 0x1000
FDT_MAGIC = 0xD00DFEED
FDT_SOURCE = "/sys/firmware/fdt"
LAYOUT_DEFINE = re.compile(r"^#define[ \t]+BE_MVP_([A-Z0-9_]+)[ \t]+"
                           r"BE_MVP_C\(([0-9a-fA-Fx]+)\)[ \t]*$", re.M)
LAYOUT_NAMES = ("STAGING_HPA", "BOOT_IMAGE_MAX", "STAGING_BYTES",
                "G0_HPA", "G1_HPA", "GUEST_BYTES",
                "UBOOT_RAM_BASE", "MONITOR_HPA", "CORE_BYTES",
                "POOL_HPA", "POOL_BYTES", "HART_REGION_HPA",
                "HART_REGION_BYTES", "REGION_HPA", "REGION_BYTES",
                "SHARED_PAGES_HPA", "SHARED_PAGES_BYTES")
IOMEM_BEGIN = "iomem_system_ram_begin"
IOMEM_END = "iomem_system_ram_end"


def parse_layout(text, source="layout"):
    """{NAME: value} for every `#define BE_MVP_NAME BE_MVP_C(literal)`."""
    layout = {}
    for name, literal in LAYOUT_DEFINE.findall(text):
        if name in layout:
            raise ValueError(f"{source}: BE_MVP_{name} is defined twice")
        layout[name] = int(literal, 0)
    missing = [name for name in LAYOUT_NAMES if name not in layout]
    if missing:
        raise ValueError(f"{source}: no BE_MVP_C value for "
                         f"{', '.join('BE_MVP_' + name for name in missing)}")
    return layout


def read_layout(path):
    with open(path, encoding="ascii") as handle:
        return parse_layout(handle.read(), path)


def align_up(value, alignment):
    return (value + alignment - 1) & ~(alignment - 1)


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def parse_iomem(text):
    """Top-level /proc/iomem ranges, each with all nested child ranges."""
    ranges = []
    for line in text.splitlines():
        if not line.strip():
            continue
        depth = len(line) - len(line.lstrip(" "))
        span, _, name = line.strip().partition(" : ")
        low, _, high = span.partition("-")
        entry = (int(low, 16), int(high, 16) + 1, name)
        if depth == 0:
            ranges.append((entry, []))
        elif ranges:
            ranges[-1][1].append(entry)
    return ranges


def cells(value):
    result = 0
    for index in range(0, len(value), 4):
        result = (result << 32) | struct.unpack_from(">I", value, index)[0]
    return result


def fdt_reserved(fdt):
    """Ranges in the FDT reservation block and /reserved-memory reg."""
    magic, totalsize, off_struct, off_strings, off_rsvmap = \
        struct.unpack_from(">5I", fdt, 0)
    if magic != FDT_MAGIC or totalsize > len(fdt):
        raise ValueError("not a complete flattened device tree")
    ranges = []
    position = off_rsvmap
    while True:
        address, size = struct.unpack_from(">QQ", fdt, position)
        position += 16
        if address == 0 and size == 0:
            break
        ranges.append((address, address + size))
    position = off_struct
    path = []
    address_cells, size_cells = 2, 2
    while True:
        token, = struct.unpack_from(">I", fdt, position)
        position += 4
        if token == 1:  # FDT_BEGIN_NODE
            end = fdt.index(b"\0", position)
            path.append(fdt[position:end].decode("ascii", "replace"))
            position = align_up(end + 1, 4)
        elif token == 2:  # FDT_END_NODE
            path.pop()
        elif token == 3:  # FDT_PROP
            length, name_offset = struct.unpack_from(">II", fdt, position)
            value = fdt[position + 8:position + 8 + length]
            position = align_up(position + 8 + length, 4)
            start = off_strings + name_offset
            name = fdt[start:fdt.index(b"\0", start)].decode("ascii")
            in_reserved = len(path) >= 2 and path[1] == "reserved-memory"
            if in_reserved and len(path) == 2 and name == "#address-cells":
                address_cells = cells(value)
            elif in_reserved and len(path) == 2 and name == "#size-cells":
                size_cells = cells(value)
            elif in_reserved and len(path) == 3 and name == "reg":
                step = 4 * (address_cells + size_cells)
                split = 4 * address_cells
                for offset in range(0, length - step + 1, step):
                    address = cells(value[offset:offset + split])
                    size = cells(value[offset + split:offset + step])
                    ranges.append((address, address + size))
        elif token == 4:  # FDT_NOP
            continue
        elif token == 9:  # FDT_END
            return ranges
        else:
            raise ValueError(f"bad FDT token {token:#x}")


def reservations(fdt_path=FDT_SOURCE):
    """fdt_reserved= value: every FDT reservation, none, or unreadable."""
    try:
        ranges = fdt_reserved(read_bytes(fdt_path))
    except PermissionError:
        return "unreadable-needs-root"
    except (OSError, ValueError, struct.error) as error:
        return f"unreadable-{type(error).__name__}"
    return ",".join(f"0x{low:x}-0x{high:x}" for low, high in ranges) or "none"


def system_ram_text(text):
    """The /proc/iomem System RAM lines a preflight record holds."""
    lines = text.splitlines()
    if IOMEM_BEGIN not in lines or IOMEM_END not in lines:
        return None
    return "\n".join(lines[lines.index(IOMEM_BEGIN) + 1:
                           lines.index(IOMEM_END)])


def staging_regions(layout):
    """(name, low, high) of every MVP extent: the flat image's core,
    pool, hart region, and MVP region, the staging reserve, both domain
    windows, and the shared pages."""
    staging = layout["STAGING_HPA"]
    return (("core", layout["MONITOR_HPA"],
             layout["MONITOR_HPA"] + layout["CORE_BYTES"]),
            ("pool", layout["POOL_HPA"],
             layout["POOL_HPA"] + layout["POOL_BYTES"]),
            ("hart-region", layout["HART_REGION_HPA"],
             layout["HART_REGION_HPA"] + layout["HART_REGION_BYTES"]),
            ("mvp-region", layout["REGION_HPA"],
             layout["REGION_HPA"] + layout["REGION_BYTES"]),
            ("staging", staging, staging + layout["STAGING_BYTES"]),
            ("g0-window", layout["G0_HPA"],
             layout["G0_HPA"] + layout["GUEST_BYTES"]),
            ("g1-window", layout["G1_HPA"],
             layout["G1_HPA"] + layout["GUEST_BYTES"]),
            ("shared-pages", layout["SHARED_PAGES_HPA"],
             layout["SHARED_PAGES_HPA"] + layout["SHARED_PAGES_BYTES"]))


def region_findings(iomem_text, reserved, layout):
    """(findings, report lines) for every MVP extent (the layout rule):
    each inside one System RAM range, clear of its children and of every
    FDT reservation."""
    parsed = parse_iomem(iomem_text)
    if not parsed or all(entry[0] == 0 for entry, _ in parsed):
        return ["/proc/iomem addresses are hidden or absent; read it as "
                "root"], []
    findings = []
    report = []
    for name, low, high in staging_regions(layout):
        before = len(findings)
        ram = [(entry, children) for entry, children in parsed
               if entry[2] == "System RAM" and entry[0] <= low and
               high <= entry[1]]
        if not ram:
            findings.append(f"{name} 0x{low:x}-0x{high:x} is not inside one "
                            f"System RAM range")
            children = []
        else:
            children = ram[0][1]
        for child_low, child_high, child in children:
            if child_low < high and low < child_high:
                findings.append(f"{name} 0x{low:x}-0x{high:x} holds the "
                                f"/proc/iomem child {child!r} "
                                f"0x{child_low:x}-0x{child_high:x}")
        for reserved_low, reserved_high in reserved:
            if reserved_low < high and low < reserved_high:
                findings.append(f"{name} 0x{low:x}-0x{high:x} holds the FDT "
                                f"reservation 0x{reserved_low:x}-"
                                f"0x{reserved_high:x}")
        report.append(f"region {name}=0x{low:x}-0x{high:x} "
                      f"result={'free' if len(findings) == before else 'busy'}")
    children = sum(len(children) for entry, children in parsed
                   if entry[2] == "System RAM")
    report.append(f"system_ram_children={children} "
                  f"fdt_reservations={len(reserved)}")
    return findings, report


def parse_reserved(value):
    """The ranges of an fdt_reserved= value (ValueError if unreadable)."""
    if value == "none":
        return []
    ranges = []
    for item in value.split(","):
        low, separator, high = item.partition("-")
        if not separator or not low.startswith("0x") or \
                not high.startswith("0x"):
            raise ValueError(f"FDT reservations are {value!r}")
        ranges.append((int(low, 16), int(high, 16)))
    return ranges


def region_report(text, layout):
    """(findings, report lines) for a k3-preflight.sh record's text."""
    values = [line[len("fdt_reserved="):] for line in text.splitlines()
              if line.startswith("fdt_reserved=")]
    iomem_text = system_ram_text(text)
    findings = []
    reserved = []
    if len(values) != 1:
        findings.append(f"{len(values)} fdt_reserved= lines, expected 1")
    else:
        try:
            reserved = parse_reserved(values[0])
        except ValueError as error:
            findings.append(str(error))
    if iomem_text is None:
        findings.append(f"no {IOMEM_BEGIN}/{IOMEM_END} section (System RAM "
                        f"read as root)")
        return findings, []
    more, report = region_findings(iomem_text, reserved, layout)
    return findings + more, report


def region_check(layout_path, preflight_path):
    """region-check: every MVP extent in a preflight record."""
    layout = read_layout(layout_path)
    with open(preflight_path, encoding="utf-8", errors="replace") as handle:
        findings, report = region_report(handle.read(), layout)
    for line in report:
        print(line)
    for finding in findings:
        print(f"stop: {finding}")
    print(f"region_check={'PASS' if not findings else 'STOP'}")
    return 0 if not findings else 1


def emit(report):
    for key, value in report.items():
        print(f"{key}={value}")


def main(argv):
    command, args = (argv[1], argv[2:]) if len(argv) > 1 else ("", [])
    if command == "region-check" and len(args) == 2:
        return region_check(*args)
    if command != "probe" or args:
        print(__doc__)
        return 2
    if platform.machine() != "riscv64":
        print(f"refusing: machine is {platform.machine()}, not riscv64")
        return 2
    emit({"fdt_reserved": reservations()})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
