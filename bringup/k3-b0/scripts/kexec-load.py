#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Load the B0 RISC-V Image into RAM for a Linux kexec on the K3 host.

  kexec-load.py analyze KERNEL        offline: check KERNEL's kexec_file purgatory
  kexec-load.py probe [KERNEL]        report which kexec path can start B0
  kexec-load.py auto IMAGE [KERNEL]   probe, then load through that path
  kexec-load.py classic IMAGE [FDT]   kexec_load(2): B0 + FDT, no purgatory
  kexec-load.py file IMAGE            kexec_file_load(2): kernel Image loader
  kexec-load.py raw IMAGE ADDRESS     kexec_load(2): headerless image at a
                                      fixed address, entered at its first
                                      byte, FDT copy 1 MiB above it
  kexec-load.py unload                drop any loaded kexec image

kexec_load (CONFIG_KEXEC) is preferred: Linux's relocation code copies the
two segments and jumps straight to B0 with a0 = hart ID and a1 = FDT. The
destination is the lowest 2 MiB-aligned System RAM window that avoids the
running kernel, every other /proc/iomem child, and every FDT reservation.

kexec_file_load (CONFIG_KEXEC_FILE) runs the kernel's RISC-V purgatory first.
Linux's purgatory relocator patches the instruction after each
R_RISCV_PCREL_HI20 and ignores R_RISCV_PCREL_LO12_I, so a compiler that
separates such a pair yields a purgatory whose SHA-256 check fails and loops
forever. It is used only when the purgatory in KERNEL has no separated pair.

Everything stays in RAM: nothing is written to firmware, the U-Boot
environment, flash, or the boot configuration.
"""

import ctypes
import errno
import os
import platform
import struct
import subprocess
import sys
import zlib

SYS_KEXEC_LOAD = 104       # asm-generic numbers, used by riscv64
SYS_KEXEC_FILE_LOAD = 294
KEXEC_ARCH_X86_64 = 62 << 16
KEXEC_FILE_UNLOAD = 0x1
KEXEC_FILE_NO_INITRAMFS = 0x4
KEXEC_FILE_PROBE_FLAG = 1 << 30  # never valid: makes the probe a no-op
R_RISCV_PCREL_LO12_I = 24
R_RISCV_PCREL_LO12_S = 25
PAGE = 0x1000
IMAGE_ALIGN = 0x200000
RAW_FDT_OFFSET = 0x100000
FDT_MAGIC = 0xD00DFEED
FDT_SOURCE = "/sys/firmware/fdt"
IOMEM = "/proc/iomem"


class KexecSegment(ctypes.Structure):
    _fields_ = [("buf", ctypes.c_void_p), ("bufsz", ctypes.c_size_t),
                ("mem", ctypes.c_void_p), ("memsz", ctypes.c_size_t)]


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


def classic_layout(iomem_text, reserved, image_memsz, fdt_memsz):
    """Lowest 2 MiB-aligned System RAM window clear of all busy ranges."""
    parsed = parse_iomem(iomem_text)
    if not parsed or all(entry[0] == 0 for entry, _ in parsed):
        raise PermissionError("/proc/iomem addresses are hidden; run as root")
    need = image_memsz + fdt_memsz
    for (start, end, name), children in parsed:
        if name != "System RAM":
            continue
        busy = [(low, high) for low, high, _ in children] + list(reserved)
        base = align_up(start, IMAGE_ALIGN)
        while base + need <= end:
            clashes = [high for low, high in busy
                       if low < base + need and base < high]
            if not clashes:
                return base, base + image_memsz
            base = align_up(max(clashes), IMAGE_ALIGN)
    return None


def raw_layout(iomem_text, reserved, address, image_memsz, fdt_memsz):
    """Check a fixed-address image and its FDT copy: both inside one System
    RAM range and clear of every /proc/iomem child and FDT reservation."""
    parsed = parse_iomem(iomem_text)
    if not parsed or all(entry[0] == 0 for entry, _ in parsed):
        raise PermissionError("/proc/iomem addresses are hidden; run as root")
    if address % PAGE or image_memsz > RAW_FDT_OFFSET:
        raise ValueError(f"raw image at 0x{address:x} (0x{image_memsz:x} "
                         "bytes) is unaligned or overlaps its FDT slot")
    fdt_address = address + RAW_FDT_OFFSET
    end = fdt_address + fdt_memsz
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


def image_memsz(image):
    """Validate the RISC-V Image header; return its page-rounded footprint."""
    if len(image) < 64 or image[48:56] != b"RISCV\0\0\0" \
            or image[56:60] != b"RSC\x05":
        raise ValueError("not a RISC-V Image (header magic)")
    size, = struct.unpack_from("<Q", image, 16)
    return align_up(max(size, len(image)), PAGE)


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


def probe(kernel):
    report = analyze_kernel(kernel)
    report["kexec_load"] = classic_status()
    report["kexec_file_load"] = file_status()
    report["kexec_load_disabled"] = sysctl("kexec_load_disabled")
    report["kexec_loaded"] = kexec_loaded()
    if report["kexec_load"] == "available":
        report["viable"] = "kexec_load"
    elif report["kexec_file_load"] == "available" \
            and report["kexec_file_purgatory"] == "safe":
        report["viable"] = "kexec_file_load"
    else:
        report["viable"] = "none"
    return report


def load_classic(image_path, fdt_path=FDT_SOURCE):
    image = read_bytes(image_path)
    fdt = read_bytes(fdt_path)
    memsz = image_memsz(image)
    fdt_memsz = align_up(len(fdt), PAGE)
    with open(IOMEM, encoding="ascii") as handle:
        layout = classic_layout(handle.read(), fdt_reserved(fdt), memsz,
                                fdt_memsz)
    if layout is None:
        print("loader=none: no free System RAM window for kexec_load")
        return 1
    entry, fdt_address = layout
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


def load_raw(image_path, address_text, fdt_path=FDT_SOURCE):
    image = read_bytes(image_path)
    fdt = read_bytes(fdt_path)
    address = int(address_text, 0)
    memsz = align_up(len(image), PAGE)
    fdt_memsz = align_up(len(fdt), PAGE)
    reserved = fdt_reserved(fdt)
    with open(IOMEM, encoding="ascii") as handle:
        try:
            entry, fdt_address = raw_layout(
                handle.read(), reserved, address, memsz, fdt_memsz)
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


def load_file(image_path):
    image_memsz(read_bytes(image_path))
    descriptor = os.open(image_path, os.O_RDONLY | os.O_CLOEXEC)
    try:
        result, error = syscall(SYS_KEXEC_FILE_LOAD, descriptor, -1, 0, None,
                                KEXEC_FILE_NO_INITRAMFS)
    finally:
        os.close(descriptor)
    if result != 0:
        print(f"kexec_file_load failed: {os.strerror(error)} (errno {error})")
        return 1
    print(f"loader=kexec_file_load kexec_loaded={kexec_loaded()}")
    return 0


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
    if command not in ("probe", "auto", "classic", "file", "raw", "unload"):
        print(__doc__)
        return 2
    if platform.machine() != "riscv64":
        print(f"refusing: machine is {platform.machine()}, not riscv64")
        return 2
    if command == "probe" and len(args) <= 1:
        emit(probe(args[0] if args else default_kernel()))
        return 0
    if command == "auto" and 1 <= len(args) <= 2:
        report = probe(args[1] if len(args) == 2 else default_kernel())
        emit(report)
        if report["viable"] == "kexec_load":
            return load_classic(args[0])
        if report["viable"] == "kexec_file_load":
            return load_file(args[0])
        print("loader=none: kexec cannot start B0 here; use U-Boot booti")
        return 3
    if command == "classic" and 1 <= len(args) <= 2:
        return load_classic(*args)
    if command == "file" and len(args) == 1:
        return load_file(args[0])
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
