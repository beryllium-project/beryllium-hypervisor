#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Host tests for scripts/kexec-load.py: purgatory analysis, kernel
containers, FDT reservations, classic placement, and Image validation."""

import gzip
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


K3_IOMEM = """\
100000000-101ffffff : Reserved
102000000-2fdffffff : System RAM
  102200000-1045fffff : Kernel image
    102200000-103ffffff : Kernel code
    104000000-1045fffff : Kernel data
2fe000000-2ffffffff : Reserved
d4017000-d40170ff : serial
"""

LAUNCHER_REMOTE_IMAGE = "remote_image=/tmp/be-k3-b0-image.img"
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
def classic_layout_avoids_kernel_and_reservations():
    layout = kexec_load.classic_layout(K3_IOMEM, [], 0x7000, 0xA000)
    assert layout == (0x102000000, 0x102007000), [hex(x) for x in layout]
    layout = kexec_load.classic_layout(
        K3_IOMEM, [(0x102000000, 0x102001000), (0x104600000, 0x104601000),
                   (0x104800000, 0x104A00000)], 0x7000, 0xA000)
    assert layout == (0x104A00000, 0x104A07000), [hex(x) for x in layout]


@check
def classic_layout_respects_range_end():
    iomem = "80200000-805fffff : System RAM\n  80200000-803fffff : Kernel image\n"
    assert kexec_load.classic_layout(iomem, [], 0x7000, 0x1000) == \
        (0x80400000, 0x80407000)
    assert kexec_load.classic_layout(iomem, [], 0x200000, 0x1000) is None


@check
def hidden_iomem_is_refused():
    hidden = "00000000-00000000 : System RAM\n  00000000-00000000 : Kernel image\n"
    try:
        kexec_load.classic_layout(hidden, [], 0x7000, 0x1000)
    except PermissionError:
        return
    raise AssertionError("hidden /proc/iomem accepted")


# The COM260's /proc/iomem from the 2026-10-06 preflight (abridged).
K3_PREFLIGHT_IOMEM = """\
102000000-2ffffffff : System RAM
  102200000-102201fff : Reserved
  102202000-105c058f7 : Kernel image
    102202000-103501909 : Kernel code
  2fe000000-2ffffffff : Reserved
"""


def raw_refused(iomem, reserved, address, memsz, fdt_memsz):
    try:
        kexec_load.raw_layout(iomem, reserved, address, memsz, fdt_memsz)
    except ValueError:
        return True
    return False


@check
def raw_layout_places_b1_window():
    assert kexec_load.raw_layout(K3_PREFLIGHT_IOMEM, [], 0x102000000,
                                 0x34000, 0xB000) == (0x102000000, 0x102100000)


@check
def raw_layout_refuses_busy_and_bad_ranges():
    iomem = K3_PREFLIGHT_IOMEM
    assert raw_refused(iomem, [], 0x102100000, 0x34000, 0xB000)  # kernel
    assert raw_refused(iomem, [(0x102020000, 0x102021000)], 0x102000000,
                       0x34000, 0xB000)                         # FDT resv
    assert raw_refused(iomem, [(0x102100000, 0x102101000)], 0x102000000,
                       0x34000, 0xB000)                         # FDT slot
    assert raw_refused(iomem, [], 0x100000000, 0x34000, 0xB000)  # not RAM
    assert raw_refused(iomem, [], 0x2ffff0000, 0x1000, 0x1000)   # past end
    assert raw_refused(iomem, [], 0x102000800, 0x34000, 0xB000)  # unaligned
    assert raw_refused(iomem, [], 0x102000000, 0x200000, 0xB000)  # > 1 MiB
    try:
        kexec_load.raw_layout("0-0 : System RAM\n", [], 0x102000000,
                              0x34000, 0xB000)
    except PermissionError:
        return
    raise AssertionError("hidden /proc/iomem accepted")


@check
def image_header_is_validated():
    header = bytearray(64)
    struct.pack_into("<QQ", header, 8, 0x200000, 0x6100)
    header[48:56] = b"RISCV\0\0\0"
    header[56:60] = b"RSC\x05"
    assert kexec_load.image_memsz(bytes(header)) == 0x7000
    for corrupt in (bytes(64), bytes(header[:60])):
        try:
            kexec_load.image_memsz(corrupt)
        except ValueError:
            continue
        raise AssertionError("bad Image header accepted")


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
    if len(argv) == 2:
        image = pathlib.Path(argv[1]).read_bytes()
        memsz = kexec_load.image_memsz(image)
        assert memsz % 0x1000 == 0 and memsz >= len(image), hex(memsz)
        report = kexec_load.analyze_purgatory(image)
        assert report["purgatory"] == "absent", report
        print(f"PASS published image footprint {memsz:#x}")
    if shutil.which("zstd") is None:
        print("note: zstd CLI absent; stdlib zstd covers efi-zboot-zstd")
    for function in CHECKS:
        function()
        print(f"PASS {function.__name__}")
    print(f"kexec-load self-test: {len(CHECKS)}/{len(CHECKS)} PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
