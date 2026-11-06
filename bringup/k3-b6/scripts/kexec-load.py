#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# A copy of B0's scripts/kexec-load.py (as accepted with B1 at b44c3c6b)
# with the counted changes listed in bringup/k3-b6/README.md.
"""Load the B6 boot image into RAM for a Linux kexec on the K3 host.

  kexec-load.py analyze KERNEL        offline: check KERNEL's kexec_file purgatory
  kexec-load.py probe [KERNEL]        report the kexec facts B6 depends on
  kexec-load.py raw IMAGE LAYOUT      kexec_load(2): the B6 boot image at the
                                      staging address L of the B6 layout
                                      header LAYOUT, entered at its first
                                      byte, the FDT copy after it
  kexec-load.py unload                drop any loaded kexec image
  kexec-load.py region-check LAYOUT PREFLIGHT
                                      offline: are B6's staging region and
                                      guest window free in a preflight record

B6 uses only kexec_load (CONFIG_KEXEC), in raw layout: Linux's relocation
code copies two segments and jumps straight to the image's first byte (B3's
shim) with a0 = hart ID and a1 = FDT; no purgatory runs. Every address
comes from bringup/k3-b6/src/b6-layout.h, read from LAYOUT: the image (B3's
RISC-V Image header, text_offset placing it at L under U-Boot booti too,
image_size equal to the file, at most BE_B6_BOOT_IMAGE_MAX bytes) at L,
and a copy of /sys/firmware/fdt (at most BE_B6_KEXEC_FDT_MAX bytes) at L
plus the image rounded up to BE_B6_KEXEC_FDT_ALIGN, ending at or below the
guest window BE_B6_GUEST_HPA. Both segments must be page aligned, inside
one System RAM range, and clear of every /proc/iomem child and every FDT
reservation; anything else refuses the load.

probe also reports the FDT reservations (fdt_reserved=). region-check
reads a k3-preflight.sh record (its fdt_reserved= line and its
iomem_system_ram_begin/_end section of every System RAM range and child)
and stops on any child or reservation inside the staging region [L, L +
BE_B6_BOOT_IMAGE_MAX rounded up to BE_B6_KEXEC_FDT_ALIGN +
BE_B6_KEXEC_FDT_MAX) or the guest window [BE_B6_GUEST_HPA, +
BE_B6_GUEST_BYTES), or on either region outside one System RAM range.

Everything stays in RAM: nothing is written to firmware, the U-Boot
environment, flash, or the boot configuration.
"""

import ctypes
import errno
import os
import platform
import re
import struct
import subprocess
import sys
import zlib

SYS_KEXEC_LOAD = 104       # asm-generic numbers, used by riscv64
SYS_KEXEC_FILE_LOAD = 294
KEXEC_ARCH_X86_64 = 62 << 16
KEXEC_FILE_UNLOAD = 0x1
KEXEC_FILE_PROBE_FLAG = 1 << 30  # never valid: makes the probe a no-op
R_RISCV_PCREL_LO12_I = 24
R_RISCV_PCREL_LO12_S = 25
PAGE = 0x1000
FDT_MAGIC = 0xD00DFEED
FDT_SOURCE = "/sys/firmware/fdt"
IOMEM = "/proc/iomem"
LAYOUT_DEFINE = re.compile(r"^#define[ \t]+BE_B6_([A-Z0-9_]+)[ \t]+"
                           r"BE_B6_C\(([0-9a-fA-Fx]+)\)[ \t]*$", re.M)
LAYOUT_NAMES = ("STAGING_HPA", "BOOT_IMAGE_MAX", "KEXEC_FDT_ALIGN",
                "KEXEC_FDT_MAX", "GUEST_HPA", "GUEST_BYTES", "UBOOT_RAM_BASE")
IOMEM_BEGIN = "iomem_system_ram_begin"
IOMEM_END = "iomem_system_ram_end"


class KexecSegment(ctypes.Structure):
    _fields_ = [("buf", ctypes.c_void_p), ("bufsz", ctypes.c_size_t),
                ("mem", ctypes.c_void_p), ("memsz", ctypes.c_size_t)]


def parse_layout(text, source="layout"):
    """{NAME: value} for every `#define BE_B6_NAME BE_B6_C(literal)`."""
    layout = {}
    for name, literal in LAYOUT_DEFINE.findall(text):
        if name in layout:
            raise ValueError(f"{source}: BE_B6_{name} is defined twice")
        layout[name] = int(literal, 0)
    missing = [name for name in LAYOUT_NAMES if name not in layout]
    if missing:
        raise ValueError(f"{source}: no BE_B6_C value for "
                         f"{', '.join('BE_B6_' + name for name in missing)}")
    return layout


def read_layout(path):
    with open(path, encoding="ascii") as handle:
        return parse_layout(handle.read(), path)


def syscall(number, *args):
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    converted = []
    for arg in args:
        if arg is None:
            converted.append(ctypes.c_void_p(None))
        elif isinstance(arg, int):
            converted.append(ctypes.c_long(arg) if arg < 0
                             else ctypes.c_ulong(arg))
        else:
            converted.append(arg)
    result = libc.syscall(ctypes.c_long(number), *converted)
    return result, ctypes.get_errno()


def align_up(value, alignment):
    return (value + alignment - 1) & ~(alignment - 1)


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def decompress(method, payload):
    if method == "gzip":
        return zlib.decompress(payload, 16 + zlib.MAX_WBITS)
    if method == "zstd":
        try:
            from compression import zstd
            return zstd.decompress(payload)
        except ImportError:
            return subprocess.run(["zstd", "-dcq"], input=payload,
                                  stdout=subprocess.PIPE, check=True).stdout
    raise ValueError(f"unsupported kernel compression {method}")


def kernel_payload(data):
    """Return (container, Image bytes) for a plain, gzip, or EFI zboot file."""
    if data[:2] == b"MZ" and data[4:8] == b"zimg":
        offset, size = struct.unpack_from("<II", data, 8)
        method = data[24:32].split(b"\0")[0].decode("ascii", "replace")
        return f"efi-zboot-{method}", decompress(
            method, data[offset:offset + size])
    if data[:2] == b"\x1f\x8b":
        return "gzip", decompress("gzip", data)
    return "image", data


def find_purgatory(data):
    """Offset of the embedded little-endian RISC-V ET_REL purgatory ELF."""
    position = 0
    while True:
        position = data.find(b"\x7fELF\x02\x01\x01", position)
        if position < 0:
            return None
        e_type, e_machine = struct.unpack_from("<HH", data, position + 16)
        if e_type == 1 and e_machine == 243:
            return position
        position += 4


def analyze_purgatory(data):
    """Count PCREL_LO12 relocations that do not follow their auipc."""
    base = find_purgatory(data)
    if base is None:
        return {"purgatory": "absent", "kexec_file_purgatory": "unknown"}
    e_shoff, = struct.unpack_from("<Q", data, base + 0x28)
    e_shentsize, e_shnum = struct.unpack_from("<HH", data, base + 0x3A)
    sections = []
    for index in range(e_shnum):
        header = base + e_shoff + index * e_shentsize
        sh_type, = struct.unpack_from("<I", data, header + 4)
        sh_offset, sh_size = struct.unpack_from("<QQ", data, header + 0x18)
        sh_link, = struct.unpack_from("<I", data, header + 0x28)
        sections.append((sh_type, sh_offset, sh_size, sh_link))
    pairs = adjacent = separated = stores = 0
    for sh_type, sh_offset, sh_size, sh_link in sections:
        if sh_type != 4:  # SHT_RELA
            continue
        _, symbols, symbols_size, _ = sections[sh_link]
        for entry in range(sh_size // 24):
            r_offset, r_info = struct.unpack_from(
                "<QQ", data, base + sh_offset + entry * 24)
            r_type = r_info & 0xFFFFFFFF
            if r_type == R_RISCV_PCREL_LO12_S:
                stores += 1
                continue
            symbol = r_info >> 32
            if r_type != R_RISCV_PCREL_LO12_I or symbol * 24 >= symbols_size:
                continue
            label, = struct.unpack_from(
                "<Q", data, base + symbols + symbol * 24 + 8)
            pairs += 1
            if r_offset == label + 4:
                adjacent += 1
            else:
                separated += 1
    safe = pairs > 0 and separated == 0 and stores == 0
    return {
        "purgatory": "present",
        "pcrel_lo12_i": pairs,
        "adjacent": adjacent,
        "separated": separated,
        "pcrel_lo12_s": stores,
        "kexec_file_purgatory": "safe" if safe else "unsafe",
    }


def analyze_kernel(path):
    try:
        container, image = kernel_payload(read_bytes(path))
    except (OSError, ValueError, zlib.error,
            subprocess.CalledProcessError) as error:
        return {"kernel": path, "container": f"unreadable-{error}",
                "kexec_file_purgatory": "unknown"}
    report = {"kernel": path, "container": container}
    report.update(analyze_purgatory(image))
    return report


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


def raw_layout(iomem_text, reserved, layout, image_memsz, fdt_bytes):
    """Place the boot image at L and its FDT copy after it, 2 MiB aligned,
    below the guest window: both inside one System RAM range and clear of
    every /proc/iomem child and FDT reservation."""
    parsed = parse_iomem(iomem_text)
    if not parsed or all(entry[0] == 0 for entry, _ in parsed):
        raise PermissionError("/proc/iomem addresses are hidden; run as root")
    address = layout["STAGING_HPA"]
    if address % PAGE or not 0 < image_memsz <= layout["BOOT_IMAGE_MAX"] \
            or image_memsz % PAGE:
        raise ValueError(f"raw image at 0x{address:x} (0x{image_memsz:x} "
                         f"bytes) is unaligned or above "
                         f"0x{layout['BOOT_IMAGE_MAX']:x} bytes")
    if not 0 < fdt_bytes <= layout["KEXEC_FDT_MAX"]:
        raise ValueError(f"FDT of {fdt_bytes} bytes is empty or above "
                         f"0x{layout['KEXEC_FDT_MAX']:x}")
    fdt_address = address + align_up(image_memsz, layout["KEXEC_FDT_ALIGN"])
    if fdt_address % layout["KEXEC_FDT_ALIGN"]:
        raise ValueError(f"FDT slot 0x{fdt_address:x} is not "
                         f"0x{layout['KEXEC_FDT_ALIGN']:x} aligned")
    end = fdt_address + align_up(fdt_bytes, PAGE)
    if end > layout["GUEST_HPA"]:
        raise ValueError(f"FDT slot 0x{fdt_address:x}-0x{end:x} reaches the "
                         f"guest window 0x{layout['GUEST_HPA']:x}")
    for (start, stop, name), children in parsed:
        if name != "System RAM" or not start <= address < stop:
            continue
        if end > stop:
            raise ValueError(f"0x{address:x}-0x{end:x} leaves System RAM")
        busy = [(low, high) for low, high, _ in children] + list(reserved)
        for low, high in ((address, address + image_memsz),
                          (fdt_address, end)):
            clashes = [(b_low, b_high) for b_low, b_high in busy
                       if b_low < high and low < b_high]
            if clashes:
                raise ValueError(f"0x{low:x}-0x{high:x} overlaps busy "
                                 f"0x{clashes[0][0]:x}-0x{clashes[0][1]:x}")
        return address, fdt_address
    raise ValueError(f"0x{address:x} is not System RAM")


def image_memsz(image, layout):
    """Validate the B6 boot image's RISC-V Image header (B3's): its magic,
    image_size equal to the file, and the text_offset that makes U-Boot
    booti place the same file at L. Return its page-rounded footprint."""
    if len(image) < 64 or image[48:56] != b"RISCV\0\0\0" \
            or image[56:60] != b"RSC\x05":
        raise ValueError("not a RISC-V Image (header magic)")
    text_offset, size = struct.unpack_from("<QQ", image, 8)
    if size != len(image):
        raise ValueError(f"image_size 0x{size:x} is not the file size "
                         f"0x{len(image):x}")
    wanted = layout["STAGING_HPA"] - layout["UBOOT_RAM_BASE"]
    if text_offset != wanted:
        raise ValueError(f"text_offset 0x{text_offset:x} != 0x{wanted:x}: "
                         f"not the B6 board image")
    return align_up(size, PAGE)


def kexec_loaded():
    try:
        with open("/sys/kernel/kexec_loaded", encoding="ascii") as handle:
            return handle.read().strip()
    except OSError:
        return "unavailable"


def describe(error):
    return {errno.EINVAL: "available", errno.ENOSYS: "absent",
            errno.EPERM: "not-permitted"}.get(error, f"errno-{error}")


def classic_status():
    """kexec_load with a foreign arch: EINVAL proves support, loads nothing."""
    result, error = syscall(SYS_KEXEC_LOAD, 0, 0, None, KEXEC_ARCH_X86_64)
    return "unexpected-success" if result == 0 else describe(error)


def file_status():
    """kexec_file_load with an invalid flag: EINVAL proves support."""
    result, error = syscall(SYS_KEXEC_FILE_LOAD, -1, -1, 0, None,
                            KEXEC_FILE_PROBE_FLAG)
    return "unexpected-success" if result == 0 else describe(error)


def default_kernel():
    release = platform.release()
    for path in (f"/lib/modules/{release}/vmlinuz", f"/boot/vmlinuz-{release}"):
        if os.access(path, os.R_OK):
            return path
    return f"/lib/modules/{release}/vmlinuz"


def sysctl(name):
    try:
        with open(f"/proc/sys/kernel/{name}", encoding="ascii") as handle:
            return handle.read().strip()
    except OSError:
        return "unavailable"


def reservations(fdt_path=FDT_SOURCE):
    """fdt_reserved= value: every FDT reservation, none, or unreadable."""
    try:
        ranges = fdt_reserved(read_bytes(fdt_path))
    except PermissionError:
        return "unreadable-needs-root"
    except (OSError, ValueError, struct.error) as error:
        return f"unreadable-{type(error).__name__}"
    return ",".join(f"0x{low:x}-0x{high:x}" for low, high in ranges) or "none"


def probe(kernel):
    report = analyze_kernel(kernel)
    report["kexec_load"] = classic_status()
    report["kexec_file_load"] = file_status()
    report["kexec_load_disabled"] = sysctl("kexec_load_disabled")
    report["kexec_loaded"] = kexec_loaded()
    report["fdt_reserved"] = reservations()
    report["viable"] = "kexec_load" if report["kexec_load"] == "available" \
        else "none"
    return report


def load_raw(image_path, layout_path, fdt_path=FDT_SOURCE):
    layout = read_layout(layout_path)
    image = read_bytes(image_path)
    fdt = read_bytes(fdt_path)
    fdt_memsz = align_up(len(fdt), PAGE)
    reserved = fdt_reserved(fdt)
    print(f"layout={layout_path} staging={layout['STAGING_HPA']:#x} "
          f"image_max={layout['BOOT_IMAGE_MAX']:#x} "
          f"fdt_align={layout['KEXEC_FDT_ALIGN']:#x} "
          f"fdt_max={layout['KEXEC_FDT_MAX']:#x} "
          f"window={layout['GUEST_HPA']:#x}")
    with open(IOMEM, encoding="ascii") as handle:
        try:
            memsz = image_memsz(image, layout)
            entry, fdt_address = raw_layout(
                handle.read(), reserved, layout, memsz, len(fdt))
        except ValueError as error:
            print(f"loader=none: {error}")
            return 1
    image_buffer = ctypes.create_string_buffer(image, len(image))
    fdt_buffer = ctypes.create_string_buffer(fdt, len(fdt))
    segments = (KexecSegment * 2)(
        KexecSegment(ctypes.cast(image_buffer, ctypes.c_void_p).value,
                     len(image), entry, memsz),
        KexecSegment(ctypes.cast(fdt_buffer, ctypes.c_void_p).value,
                     len(fdt), fdt_address, fdt_memsz))
    result, error = syscall(SYS_KEXEC_LOAD, entry, 2, segments, 0)
    if result != 0:
        print(f"kexec_load failed: {os.strerror(error)} (errno {error})")
        return 1
    print(f"loader=kexec_load entry={entry:#x} fdt={fdt_address:#x} "
          f"image_memsz={memsz:#x} fdt_bytes={len(fdt)} "
          f"kexec_loaded={kexec_loaded()}")
    return 0


def system_ram_text(text):
    """The /proc/iomem System RAM lines a preflight record holds."""
    lines = text.splitlines()
    if IOMEM_BEGIN not in lines or IOMEM_END not in lines:
        return None
    return "\n".join(lines[lines.index(IOMEM_BEGIN) + 1:
                           lines.index(IOMEM_END)])


def staging_regions(layout):
    """(name, low, high) of the staging region and the guest window."""
    staging = layout["STAGING_HPA"]
    return (("staging", staging,
             staging + align_up(layout["BOOT_IMAGE_MAX"],
                                layout["KEXEC_FDT_ALIGN"]) +
             layout["KEXEC_FDT_MAX"]),
            ("window", layout["GUEST_HPA"],
             layout["GUEST_HPA"] + layout["GUEST_BYTES"]))


def region_findings(iomem_text, reserved, layout):
    """(findings, report lines) for B6's staging region and guest window:
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
    """region-check: the staging region and window in a preflight record."""
    layout = read_layout(layout_path)
    with open(preflight_path, encoding="utf-8", errors="replace") as handle:
        findings, report = region_report(handle.read(), layout)
    for line in report:
        print(line)
    for finding in findings:
        print(f"stop: {finding}")
    print(f"region_check={'PASS' if not findings else 'STOP'}")
    return 0 if not findings else 1


def unload():
    result, error = syscall(SYS_KEXEC_FILE_LOAD, -1, -1, 0, None,
                            KEXEC_FILE_UNLOAD)
    if result != 0 and error == errno.ENOSYS:
        result, error = syscall(SYS_KEXEC_LOAD, 0, 0, None, 0)
    print(f"unload={'ok' if result == 0 else describe(error)} "
          f"kexec_loaded={kexec_loaded()}")
    return 0 if result == 0 else 1


def emit(report):
    for key, value in report.items():
        print(f"{key}={value}")


def main(argv):
    command, args = (argv[1], argv[2:]) if len(argv) > 1 else ("", [])
    if command == "analyze" and len(args) == 1:
        report = analyze_kernel(args[0])
        emit(report)
        return {"safe": 0, "unsafe": 1}.get(report["kexec_file_purgatory"], 2)
    if command == "region-check" and len(args) == 2:
        return region_check(*args)
    if command not in ("probe", "raw", "unload"):
        print(__doc__)
        return 2
    if platform.machine() != "riscv64":
        print(f"refusing: machine is {platform.machine()}, not riscv64")
        return 2
    if command == "probe" and len(args) <= 1:
        emit(probe(args[0] if args else default_kernel()))
        return 0
    if command == "raw" and len(args) == 2:
        report = probe(default_kernel())
        emit(report)
        if report["kexec_load"] != "available":
            print("loader=none: kexec_load is unavailable for a raw image")
            return 3
        return load_raw(args[0], args[1])
    if command == "unload" and not args:
        return unload()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
