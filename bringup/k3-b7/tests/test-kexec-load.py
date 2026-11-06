#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# A copy of B6's tests/test-kexec-load.py (accepted at e20c55df) with the
# counted changes listed in bringup/k3-b7/README.md.
"""Host tests for scripts/kexec-load.py: purgatory analysis, kernel
containers, FDT reservations, the B7 layout header, raw placement and the
preflight region check (the staging region and both guest windows) on the
COM260's /proc/iomem and FDT reservations as B6 recorded them
(bringup/k3-b6/results/20261008-com260/preflight.txt) and on synthetic
overlaps, and boot-image validation.

  test-kexec-load.py [BOOT_IMAGE...]

Each BOOT_IMAGE (a built B7 board image) must also pass the loader's header
check and place at L, with its FDT slot after it, on the recorded map."""

import gzip
import hashlib
import importlib.util
import pathlib
import shutil
import struct
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "kexec_load", HERE.parent / "scripts" / "kexec-load.py")
kexec_load = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kexec_load)

LO12_I, LO12_S = 24, 25
LAYOUT_HEADER = HERE.parent / "src" / "b7-layout.h"
LAYOUT = kexec_load.read_layout(LAYOUT_HEADER)
L = LAYOUT["STAGING_HPA"]
FDT_ALIGN = LAYOUT["KEXEC_FDT_ALIGN"]
WINDOW = LAYOUT["G0_HPA"]
WINDOW1 = LAYOUT["G1_HPA"]
# B6's read-only COM260 preflight (accepted at e20c55df): lines 85-105 hold
# every System RAM line of /proc/iomem, read as root, and line 140 the FDT
# reservations.
B6_PREFLIGHT = HERE.parents[1] / "k3-b6" / "results" / "20261008-com260" / \
    "preflight.txt"
B6_PREFLIGHT_SHA256 = \
    "b285193ad0603af03d73c1a22432fe04fe85163dd8c071c6532224007984129c"
# The FDT size B6's COM260 load checks recorded (fdt_bytes=41088).
BOARD_FDT_BYTES = 41088
# B7's boot image (the plan's estimate: the kernel and two DTBs).
B7_IMAGE_MEMSZ = 0x1B3000


def purgatory_elf(relocations, labels):
    """Minimal ET_REL RISC-V ELF: null, .symtab, .rela.text sections."""
    symtab = bytes(24) + b"".join(
        struct.pack("<IBBHQQ", 0, 0, 0, 1, value, 0) for value in labels)
    rela = b"".join(struct.pack("<QQq", offset, (symbol << 32) | kind, 0)
                    for offset, symbol, kind in relocations)
    body_offset = 64
    symtab_offset = body_offset
    rela_offset = symtab_offset + len(symtab)
    shoff = rela_offset + len(rela)

    def section(sh_type, offset, size, link):
        return struct.pack("<IIQQQQIIQQ", 0, sh_type, 0, 0, offset, size,
                           link, 0, 8, 24)

    header = b"\x7fELF\x02\x01\x01" + bytes(9) + struct.pack(
        "<HHIQQQIHHHHHH", 1, 243, 1, 0, 0, shoff, 0, 64, 0, 0, 64, 3, 0)
    return (header + symtab + rela + bytes(64) +
            section(2, symtab_offset, len(symtab), 0) +
            section(4, rela_offset, len(rela), 1))


def kernel_with(purgatory):
    return b"\x6f\x00\x00\x00" + bytes(4092) + purgatory + bytes(256)


def zboot(method, payload):
    header = bytearray(64)
    header[0:2] = b"MZ"
    header[4:8] = b"zimg"
    struct.pack_into("<II", header, 8, 64, len(payload))
    header[24:24 + len(method)] = method.encode()
    return bytes(header) + payload


def fdt_blob(reservations, reserved_nodes, address_cells=2, size_cells=2):
    strings = bytearray()
    offsets = {}
    block = bytearray()

    def name(text):
        if text not in offsets:
            offsets[text] = len(strings)
            strings.extend(text.encode() + b"\0")
        return offsets[text]

    def padded(data):
        return data + bytes(-len(data) % 4)

    def begin(text):
        block.extend(struct.pack(">I", 1) + padded(text.encode() + b"\0"))

    def prop(text, value):
        block.extend(struct.pack(">III", 3, len(value), name(text)) +
                     padded(value))

    def end():
        block.extend(struct.pack(">I", 2))

    def encode(value, count):
        return b"".join(struct.pack(">I", (value >> (32 * shift)) & 0xFFFFFFFF)
                        for shift in reversed(range(count)))

    begin("")
    prop("#address-cells", struct.pack(">I", 2))
    begin("memory@100000000")
    prop("reg", encode(0x100000000, 2) + encode(0x200000000, 2))
    end()
    begin("reserved-memory")
    prop("#address-cells", struct.pack(">I", address_cells))
    prop("#size-cells", struct.pack(">I", size_cells))
    prop("ranges", b"")
    for index, (address, size) in enumerate(reserved_nodes):
        begin(f"region@{index}")
        prop("reg", encode(address, address_cells) + encode(size, size_cells))
        prop("no-map", b"")
        end()
    end()
    end()
    block.extend(struct.pack(">I", 9))
    rsvmap = b"".join(struct.pack(">QQ", address, size)
                      for address, size in reservations) + bytes(16)
    off_rsvmap = 40
    off_struct = off_rsvmap + len(rsvmap)
    off_strings = off_struct + len(block)
    total = off_strings + len(strings)
    header = struct.pack(">10I", 0xD00DFEED, total, off_struct, off_strings,
                         off_rsvmap, 17, 16, 0, len(strings), len(block))
    return header + rsvmap + bytes(block) + bytes(strings)


def recorded_preflight():
    """B6's recorded preflight text, pinned."""
    data = B6_PREFLIGHT.read_bytes()
    assert hashlib.sha256(data).hexdigest() == B6_PREFLIGHT_SHA256, \
        f"{B6_PREFLIGHT} differs from the accepted B6 record"
    return data.decode("ascii")


def recorded_iomem():
    """The System RAM block of B6's recorded /proc/iomem, pinned."""
    lines = recorded_preflight().splitlines()
    start = lines.index("102000000-2ffffffff : System RAM")
    block = [lines[start]]
    for line in lines[start + 1:]:
        if not line.startswith(" "):
            break
        block.append(line)
    assert len(block) == 21, len(block)
    return "\n".join(block) + "\n"


B6_IOMEM = recorded_iomem()


def recorded_reservations():
    """The FDT reservations B6's preflight recorded (its fdt_reserved=)."""
    values = [line[len("fdt_reserved="):] for line in
              recorded_preflight().splitlines()
              if line.startswith("fdt_reserved=")]
    assert len(values) == 1, values
    reserved = kexec_load.parse_reserved(values[0])
    assert len(reserved) == 11, reserved
    return reserved


B6_RESERVED = recorded_reservations()


def with_child(low, high, name="Reserved", iomem=B6_IOMEM):
    """B6's map with one more System RAM child [low, high)."""
    return iomem + f"  {low:x}-{high - 1:x} : {name}\n"


def boot_header(size, text_offset=None, magic2=b"RSC\x05"):
    """A B7 board image of SIZE bytes: B3's header, the rest zero."""
    if text_offset is None:
        text_offset = L - LAYOUT["UBOOT_RAM_BASE"]
    image = bytearray(size)
    struct.pack_into("<IIQQ", image, 0, 0x6F, 0, text_offset, size)
    image[48:56] = b"RISCV\0\0\0"
    image[56:60] = magic2
    return bytes(image)


def preflight_text(iomem=B6_IOMEM, reserved="none", section=True):
    """A k3-preflight.sh record around B6's facts."""
    lines = ["hostname=k3e", "kexec_load=available", "viable=kexec_load"]
    if reserved is not None:
        lines.append(f"fdt_reserved={reserved}")
    if section:
        lines += [kexec_load.IOMEM_BEGIN] + iomem.splitlines() + \
            [kexec_load.IOMEM_END]
    return "\n".join(lines) + "\n"


LAUNCHER_REMOTE_IMAGE = "remote_image=/tmp/be-k3-b7-image.img"
CHECKS = []


def check(function):
    CHECKS.append(function)
    return function


@check
def adjacent_pairs_are_safe():
    elf = purgatory_elf([(0x14, 1, LO12_I), (0x24, 2, LO12_I)], [0x10, 0x20])
    report = kexec_load.analyze_purgatory(kernel_with(elf))
    assert report["kexec_file_purgatory"] == "safe", report
    assert (report["adjacent"], report["separated"]) == (2, 0), report


@check
def separated_pair_is_unsafe():
    elf = purgatory_elf([(0x14, 1, LO12_I), (0x30, 2, LO12_I)], [0x10, 0x20])
    report = kexec_load.analyze_purgatory(kernel_with(elf))
    assert report["kexec_file_purgatory"] == "unsafe", report
    assert (report["adjacent"], report["separated"]) == (1, 1), report


@check
def pcrel_store_is_unsafe():
    elf = purgatory_elf([(0x14, 1, LO12_I), (0x24, 2, LO12_S)], [0x10, 0x20])
    report = kexec_load.analyze_purgatory(kernel_with(elf))
    assert report["kexec_file_purgatory"] == "unsafe", report
    assert report["pcrel_lo12_s"] == 1, report


@check
def missing_purgatory_is_unknown():
    report = kexec_load.analyze_purgatory(bytes(8192))
    assert report == {"purgatory": "absent",
                      "kexec_file_purgatory": "unknown"}, report


@check
def kernel_containers_unpack():
    image = kernel_with(purgatory_elf([(0x14, 1, LO12_I)], [0x10]))
    cases = [("image", image), ("gzip", gzip.compress(image)),
             ("efi-zboot-gzip", zboot("gzip", gzip.compress(image)))]
    try:
        from compression import zstd
        cases.append(("efi-zboot-zstd", zboot("zstd", zstd.compress(image))))
    except ImportError:
        pass
    for container, data in cases:
        assert kexec_load.kernel_payload(data) == (container, image), container


@check
def fdt_reservations_are_collected():
    fdt = fdt_blob([(0x101000000, 0x1000)],
                   [(0x2FE000000, 0x2000000), (0x108000000, 0x400000)])
    assert kexec_load.fdt_reserved(fdt) == [
        (0x101000000, 0x101001000), (0x2FE000000, 0x300000000),
        (0x108000000, 0x108400000)]
    narrow = fdt_blob([], [(0x88000000, 0x100000)], 1, 1)
    assert kexec_load.fdt_reserved(narrow) == [(0x88000000, 0x88100000)]


@check
def corrupt_fdt_is_rejected():
    for blob in (bytes(64), fdt_blob([], [])[:-8]):
        try:
            kexec_load.fdt_reserved(blob)
        except ValueError:
            continue
        raise AssertionError("corrupt FDT accepted")


@check
def layout_comes_from_the_header():
    text = LAYOUT_HEADER.read_text(encoding="ascii")
    assert kexec_load.parse_layout(text) == LAYOUT
    assert L - LAYOUT["UBOOT_RAM_BASE"] > 0 and L % FDT_ALIGN == 0
    assert L + kexec_load.align_up(LAYOUT["BOOT_IMAGE_MAX"], FDT_ALIGN) + \
        LAYOUT["KEXEC_FDT_MAX"] <= WINDOW
    assert WINDOW + LAYOUT["GUEST_BYTES"] <= WINDOW1
    assert kexec_load.lower_window(LAYOUT) == WINDOW
    for name, broken in (
            ("missing", text.replace("BE_B7_STAGING_HPA", "BE_B7_X")),
            ("G1 window missing", text.replace("BE_B7_G1_HPA", "BE_B7_X")),
            ("twice", text + "#define BE_B7_G0_HPA\tBE_B7_C(0x1)\n"),
            ("not a literal", text.replace(
                f"BE_B7_C(0x{WINDOW:x})", "BE_B7_C(BE_B7_STAGING_HPA)"))):
        try:
            kexec_load.parse_layout(broken)
        except ValueError:
            continue
        raise AssertionError(f"layout header {name} accepted")


@check
def recorded_map_places_the_boot_image_at_l():
    for memsz, fdt in ((0x1000, L + FDT_ALIGN),
                       (B7_IMAGE_MEMSZ, L + FDT_ALIGN),
                       (FDT_ALIGN, L + FDT_ALIGN),
                       (FDT_ALIGN + 0x1000, L + 2 * FDT_ALIGN),
                       (LAYOUT["BOOT_IMAGE_MAX"],
                        L + LAYOUT["BOOT_IMAGE_MAX"])):
        placed = kexec_load.raw_layout(B6_IOMEM, B6_RESERVED, LAYOUT,
                                       memsz, BOARD_FDT_BYTES)
        assert placed == (L, fdt), (hex(memsz), [hex(x) for x in placed])
    placed = kexec_load.raw_layout(B6_IOMEM, B6_RESERVED, LAYOUT,
                                   LAYOUT["BOOT_IMAGE_MAX"],
                                   LAYOUT["KEXEC_FDT_MAX"])
    assert placed == (L, L + LAYOUT["BOOT_IMAGE_MAX"]), placed


def raw_refused(iomem=B6_IOMEM, reserved=(), layout=None,
                memsz=B7_IMAGE_MEMSZ,
                fdt_bytes=BOARD_FDT_BYTES):
    try:
        kexec_load.raw_layout(iomem, list(reserved), layout or LAYOUT, memsz,
                              fdt_bytes)
    except ValueError:
        return True
    return False


@check
def raw_layout_refuses_busy_and_bad_ranges():
    fdt = L + FDT_ALIGN
    assert raw_refused(with_child(L + 0x100000, L + 0x101000))  # image
    assert raw_refused(with_child(fdt, fdt + 0x1000))           # FDT slot
    assert raw_refused(with_child(L - 0x1000, L + 0x1000))      # straddles L
    assert raw_refused(reserved=[(L + 0x1000, L + 0x2000)])     # FDT resv
    assert raw_refused(reserved=[(fdt + 0x8000, fdt + 0x9000)])
    assert raw_refused(memsz=LAYOUT["BOOT_IMAGE_MAX"] + 0x1000)  # > 4 MiB
    assert raw_refused(memsz=0)
    assert raw_refused(memsz=B7_IMAGE_MEMSZ + 0x800)            # not paged
    assert raw_refused(fdt_bytes=LAYOUT["KEXEC_FDT_MAX"] + 1)   # > 2 MiB
    assert raw_refused(fdt_bytes=0)
    # Clear of the slots, a child or reservation does not matter.
    assert not raw_refused(with_child(fdt + 0x100000, fdt + 0x101000))
    assert not raw_refused(reserved=[(L - 0x1000, L)])
    # L outside System RAM, the FDT leaving it, an unaligned L, the FDT
    # reaching either window (G0's is the lower).
    assert raw_refused(iomem=f"{L + 0x1000:x}-2ffffffff : System RAM\n")
    assert raw_refused(iomem=f"102000000-{fdt + 0x1000:x} : System RAM\n")
    assert raw_refused(layout=dict(LAYOUT, STAGING_HPA=L + 0x800))
    assert raw_refused(layout=dict(LAYOUT, STAGING_HPA=L + 0x1000))
    assert raw_refused(layout=dict(LAYOUT, G0_HPA=fdt + 0x8000))
    assert not raw_refused(layout=dict(LAYOUT, G0_HPA=fdt + 0xB000))
    assert raw_refused(layout=dict(LAYOUT, G0_HPA=WINDOW1 + 0x4000000,
                                   G1_HPA=fdt + 0x8000))
    assert not raw_refused(layout=dict(LAYOUT, G0_HPA=WINDOW1 + 0x4000000,
                                       G1_HPA=fdt + 0xB000))
    # The recorded FDT reservations leave both slots clear.
    assert not raw_refused(reserved=B6_RESERVED)
    try:
        kexec_load.raw_layout("0-0 : System RAM\n", [], LAYOUT,
                              B7_IMAGE_MEMSZ, BOARD_FDT_BYTES)
    except PermissionError:
        return
    raise AssertionError("hidden /proc/iomem accepted")


@check
def recorded_map_leaves_staging_and_windows_free():
    staging_end = L + kexec_load.align_up(LAYOUT["BOOT_IMAGE_MAX"],
                                          FDT_ALIGN) + LAYOUT["KEXEC_FDT_MAX"]
    for reserved in ([], B6_RESERVED):
        findings, report = kexec_load.region_findings(B6_IOMEM, reserved,
                                                      LAYOUT)
        assert not findings, findings
        assert report == [
            f"region staging=0x{L:x}-0x{staging_end:x} result=free",
            f"region g0-window=0x{WINDOW:x}-"
            f"0x{WINDOW + LAYOUT['GUEST_BYTES']:x} result=free",
            f"region g1-window=0x{WINDOW1:x}-"
            f"0x{WINDOW1 + LAYOUT['GUEST_BYTES']:x} result=free",
            f"system_ram_children=20 fdt_reservations={len(reserved)}"], \
            report


@check
def recorded_preflight_passes_the_region_check():
    findings, report = kexec_load.region_report(recorded_preflight(), LAYOUT)
    assert not findings and len(report) == 4, (findings, report)
    assert report[-1] == "system_ram_children=20 fdt_reservations=11", report


def region_stops(iomem=B6_IOMEM, reserved=()):
    findings, _ = kexec_load.region_findings(iomem, list(reserved), LAYOUT)
    return bool(findings)


@check
def region_check_stops_on_any_overlap():
    staging_end = L + kexec_load.align_up(LAYOUT["BOOT_IMAGE_MAX"],
                                          FDT_ALIGN) + LAYOUT["KEXEC_FDT_MAX"]
    window_end = WINDOW + LAYOUT["GUEST_BYTES"]
    window1_end = WINDOW1 + LAYOUT["GUEST_BYTES"]
    # Children: in the staging region (even past a small image's FDT), in
    # either window, at any region's edge, across the windows' boundary.
    for low, high in ((L, L + 0x1000), (staging_end - 0x1000, staging_end),
                      (L + 0x500000, L + 0x501000), (WINDOW, WINDOW + 0x1000),
                      (window_end - 0x1000, window_end),
                      (WINDOW - 0x1000, WINDOW + 0x1000),
                      (WINDOW1, WINDOW1 + 0x1000),
                      (WINDOW1 + 0x2000000, WINDOW1 + 0x2001000),
                      (window1_end - 0x1000, window1_end),
                      (window1_end - 0x1000, window1_end + 0x1000),
                      (window_end - 0x1000, WINDOW1 + 0x1000)):
        assert region_stops(with_child(low, high)), (hex(low), hex(high))
        assert region_stops(reserved=[(low, high)]), (hex(low), hex(high))
    # Next to the regions, nothing stops.
    for low, high in ((L - 0x1000, L), (staging_end, staging_end + 0x1000),
                      (WINDOW - 0x1000, WINDOW),
                      (window1_end, window1_end + 0x1000)):
        assert not region_stops(with_child(low, high)), hex(low)
        assert not region_stops(reserved=[(low, high)]), hex(low)
    # A region outside one System RAM range; hidden addresses.
    assert region_stops(f"102000000-{WINDOW + 0x100000:x} : System RAM\n")
    assert region_stops(f"102000000-{window1_end - 0x1000:x} : System RAM\n")
    assert region_stops(f"102000000-{WINDOW1 + 0x1000000 - 1:x} : System "
                        f"RAM\n{WINDOW1 + 0x1000000:x}-2ffffffff : System "
                        f"RAM\n")
    # Each region need only lie inside one range of its own.
    assert not region_stops(f"102000000-{window_end - 1:x} : System RAM\n"
                            f"{window_end:x}-2ffffffff : System RAM\n")
    assert region_stops(f"102000000-{L + 0x100000:x} : System RAM\n"
                        f"{L + 0x100000:x}-2ffffffff : System RAM\n")
    assert region_stops("0-0 : System RAM\n  0-0 : Kernel image\n")


@check
def preflight_record_is_read():
    findings, report = kexec_load.region_report(preflight_text(), LAYOUT)
    assert not findings and len(report) == 4, (findings, report)
    assert kexec_load.parse_reserved("0x1-0x2,0x3-0x4") == [(1, 2), (3, 4)]
    window = f"0x{WINDOW + 0x2000:x}-0x{WINDOW + 0x3000:x}"
    window1 = f"0x{WINDOW1 + 0x2000:x}-0x{WINDOW1 + 0x3000:x}"
    for text in (preflight_text(reserved=None),
                 preflight_text(reserved="none") + "fdt_reserved=none\n",
                 preflight_text(reserved="unreadable-needs-root"),
                 preflight_text(reserved="0x1-"),
                 preflight_text(reserved=f"0x1000-0x2000,{window}"),
                 preflight_text(reserved=f"0x1000-0x2000,{window1}"),
                 preflight_text(section=False),
                 preflight_text(iomem=with_child(L, L + 0x1000)),
                 preflight_text(iomem=with_child(WINDOW1 + 0x1000,
                                                 WINDOW1 + 0x2000))):
        findings, _ = kexec_load.region_report(text, LAYOUT)
        assert findings, text


@check
def boot_image_header_is_validated():
    image = boot_header(B7_IMAGE_MEMSZ)
    assert kexec_load.image_memsz(image, LAYOUT) == B7_IMAGE_MEMSZ
    odd = bytearray(boot_header(B7_IMAGE_MEMSZ + 0x800))
    assert kexec_load.image_memsz(bytes(odd), LAYOUT) == \
        B7_IMAGE_MEMSZ + 0x1000
    struct.pack_into("<Q", odd, 16, B7_IMAGE_MEMSZ)
    for name, corrupt in (
            ("no header", bytes(64)), ("short", image[:60]),
            ("magic2", boot_header(B7_IMAGE_MEMSZ, magic2=b"RSC\x04")),
            ("image_size not the file", bytes(odd)),
            ("B5's text_offset", boot_header(B7_IMAGE_MEMSZ, 0x200000)),
            ("QEMU's k3-address text_offset",
             boot_header(B7_IMAGE_MEMSZ, L - 0x80000000))):
        try:
            kexec_load.image_memsz(corrupt, LAYOUT)
        except ValueError:
            continue
        raise AssertionError(f"bad boot image accepted: {name}")


def published_image(path):
    image = pathlib.Path(path).read_bytes()
    memsz = kexec_load.image_memsz(image, LAYOUT)
    assert memsz % 0x1000 == 0 and memsz >= len(image), hex(memsz)
    report = kexec_load.analyze_purgatory(image)
    assert report["purgatory"] == "absent", report
    placed = kexec_load.raw_layout(B6_IOMEM, B6_RESERVED, LAYOUT, memsz,
                                   BOARD_FDT_BYTES)
    assert placed == (L, L + kexec_load.align_up(memsz, FDT_ALIGN)), placed
    print(f"PASS published image {path}: footprint {memsz:#x}, entry "
          f"{placed[0]:#x}, FDT {placed[1]:#x}")


@check
def launcher_runs_the_loader_isolated():
    """Rows A and D of the RC3 snapshot reviews (2026-11-01): the board
    launcher runs the staged loader under python3 -I, so a module planted
    beside it in the board's shared /tmp (sys.path[0] is the script's
    directory without -I) is never imported as root; the staged image has
    a fixed remote name; and no remote command interpolates a bare
    variable. Demonstrated on the host with a planted ctypes.py that
    leaves a marker when imported: the plain interpreter imports it, the
    isolated one does not."""
    launcher = (HERE.parent / "scripts" / "k3-run.sh").read_text(
        encoding="utf-8")
    campaign = (HERE.parent / "scripts" / "k3-campaign.sh").read_text(
        encoding="utf-8")
    invocations = [line for line in launcher.splitlines()
                   if "python3" in line and "remote_loader" in line]
    assert len(invocations) == 2, invocations
    for line in invocations:
        assert 'python3 -I "$remote_loader"' in line, line
        assert "remote_command" in line, line
    assert "python3 $remote_loader" not in launcher
    assert "$sudo_prefix python3" not in launcher
    assert "$sudo_prefix systemctl" not in launcher
    assert "$load_command" not in launcher
    assert 'remote_image=/tmp/$(basename' not in launcher
    assert LAUNCHER_REMOTE_IMAGE in launcher, LAUNCHER_REMOTE_IMAGE
    for text in (launcher, campaign):
        assert 'BE_KEXEC_APPROVED' in text
    with tempfile.TemporaryDirectory() as scratch:
        shared = pathlib.Path(scratch)
        loader = shared / "kexec-load.py"
        shutil.copyfile(SPEC.origin, loader)
        marker = shared / "imported-as-root"
        (shared / "ctypes.py").write_text(
            "import pathlib\n"
            f"pathlib.Path({str(marker)!r}).write_text('planted')\n"
            "class Structure: pass\n"
            "c_void_p = c_size_t = object\n", encoding="utf-8")
        environment = {"PATH": os.environ.get("PATH", "/usr/bin"),
                       "LC_ALL": "C"}
        plain = subprocess.run([sys.executable, str(loader)],
                               capture_output=True, text=True,
                               env=environment, check=False)
        assert marker.exists(), ("the plain interpreter did not import the "
                                 "planted module", plain.stderr[-400:])
        marker.unlink()
        isolated = subprocess.run([sys.executable, "-I", str(loader)],
                                  capture_output=True, text=True,
                                  env=environment, check=False)
        assert not marker.exists(), "python3 -I imported the planted module"
        assert isolated.returncode == 2, (isolated.returncode,
                                          isolated.stderr[-400:])
        assert "usage" in isolated.stdout.lower() or "kexec" in \
            isolated.stdout.lower(), isolated.stdout[:200]


def main(argv):
    for path in argv[1:]:
        published_image(path)
    if shutil.which("zstd") is None:
        print("note: zstd CLI absent; stdlib zstd covers efi-zboot-zstd")
    for function in CHECKS:
        function()
        print(f"PASS {function.__name__}")
    print(f"kexec-load self-test: {len(CHECKS)}/{len(CHECKS)} PASS "
          f"images={len(argv) - 1}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
