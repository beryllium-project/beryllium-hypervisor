#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# tests/test-kexec-load.py's probe and layout-rule tests, kept when M5
# removed the kexec loader (planning/mvp-m5-plan.md, Q6).
"""Host tests for tools/platform-probe.py: FDT reservations, the MVP layout
header, the probe's one line, and the layout rule (every MVP extent: the
accepted image, the pool, the hart region, the MVP region, the staging
region, both domain windows, and the shared pages, M1's channel page their
first) on the COM260's /proc/iomem and FDT reservations as B7 recorded them
(bringup/k3-b7/results/20261008-com260/preflight.txt) and as M0's board
record holds them (mvp/results/20261025-com260/preflight.txt), and on
synthetic overlaps.

  test-platform-probe.py"""

import hashlib
import importlib.util
import pathlib
import struct
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "platform_probe", HERE.parent / "tools" / "platform-probe.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)

LAYOUT_HEADER = HERE.parent / "src" / "mvp-layout.h"
LAYOUT = probe.read_layout(LAYOUT_HEADER)
L = LAYOUT["STAGING_HPA"]
WINDOW = LAYOUT["G0_HPA"]
WINDOW1 = LAYOUT["G1_HPA"]
# The flat image's three MVP extents after the accepted image (M0-A.1).
POOL = (LAYOUT["POOL_HPA"], LAYOUT["POOL_HPA"] + LAYOUT["POOL_BYTES"])
HARTS = (LAYOUT["HART_REGION_HPA"],
         LAYOUT["HART_REGION_HPA"] + LAYOUT["HART_REGION_BYTES"])
REGION = (LAYOUT["REGION_HPA"], LAYOUT["REGION_HPA"] + LAYOUT["REGION_BYTES"])
MONITOR = (LAYOUT["MONITOR_HPA"],
           LAYOUT["MONITOR_HPA"] + LAYOUT["CORE_BYTES"])
# The shared pages (planning/mvp-m2-plan.md, Q1): three pages directly
# above G1's window, M1's channel page their first, an MVP extent in every
# image's layout.
SHARED = (LAYOUT["SHARED_PAGES_HPA"],
          LAYOUT["SHARED_PAGES_HPA"] + LAYOUT["SHARED_PAGES_BYTES"])
# B7's read-only COM260 preflight (accepted at 7b6b846b): lines 85-105 hold
# every System RAM line of /proc/iomem, read as root, and line 140 the FDT
# reservations.
B7_PREFLIGHT = HERE.parents[1] / "bringup" / "k3-b7" / "results" / \
    "20261008-com260" / "preflight.txt"
B7_PREFLIGHT_SHA256 = \
    "c9c27c229128689c32d2780b3ddb68f800ccd6b8a01a273a388cd84818e0867e"
# M0's read-only COM260 preflight of 2026-10-24, in M0's accepted board
# record (its MANIFEST.sha256 pins it): the Fedora 45 kernel's map.
M0_PREFLIGHT = HERE.parent / "results" / "20261025-com260" / "preflight.txt"
M0_PREFLIGHT_SHA256 = \
    "6f6eb0b850d658e7859e662eae24dc6a6fc9e36162db583a2bfe1625377c639f"
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
    """B7's recorded preflight text, pinned."""
    data = B7_PREFLIGHT.read_bytes()
    assert hashlib.sha256(data).hexdigest() == B7_PREFLIGHT_SHA256, \
        f"{B7_PREFLIGHT} differs from the accepted B7 record"
    return data.decode("ascii")


def recorded_iomem():
    """The System RAM block of B7's recorded /proc/iomem, pinned."""
    lines = recorded_preflight().splitlines()
    start = lines.index("102000000-2ffffffff : System RAM")
    block = [lines[start]]
    for line in lines[start + 1:]:
        if not line.startswith(" "):
            break
        block.append(line)
    assert len(block) == 21, len(block)
    return "\n".join(block) + "\n"


B7_IOMEM = recorded_iomem()


def recorded_reservations():
    """The FDT reservations B7's preflight recorded (its fdt_reserved=)."""
    values = [line[len("fdt_reserved="):] for line in
              recorded_preflight().splitlines()
              if line.startswith("fdt_reserved=")]
    assert len(values) == 1, values
    reserved = probe.parse_reserved(values[0])
    assert len(reserved) == 11, reserved
    return reserved


B7_RESERVED = recorded_reservations()


def with_child(low, high, name="Reserved", iomem=B7_IOMEM):
    """B7's map with one more System RAM child [low, high)."""
    return iomem + f"  {low:x}-{high - 1:x} : {name}\n"


def preflight_text(iomem=B7_IOMEM, reserved="none", section=True):
    """A k3-preflight.sh record around B7's facts."""
    lines = ["hostname=k3e", "kernel=7.3.0-65.1.riscv64.omni.fc45.riscv64"]
    if reserved is not None:
        lines.append(f"fdt_reserved={reserved}")
    if section:
        lines += [probe.IOMEM_BEGIN] + iomem.splitlines() + \
            [probe.IOMEM_END]
    return "\n".join(lines) + "\n"


CHECKS = []


def check(function):
    CHECKS.append(function)
    return function


@check
def fdt_reservations_are_collected():
    fdt = fdt_blob([(0x101000000, 0x1000)],
                   [(0x2FE000000, 0x2000000), (0x108000000, 0x400000)])
    assert probe.fdt_reserved(fdt) == [
        (0x101000000, 0x101001000), (0x2FE000000, 0x300000000),
        (0x108000000, 0x108400000)]
    narrow = fdt_blob([], [(0x88000000, 0x100000)], 1, 1)
    assert probe.fdt_reserved(narrow) == [(0x88000000, 0x88100000)]


@check
def corrupt_fdt_is_rejected():
    for blob in (bytes(64), fdt_blob([], [])[:-8]):
        try:
            probe.fdt_reserved(blob)
        except ValueError:
            continue
        raise AssertionError("corrupt FDT accepted")


@check
def layout_comes_from_the_header():
    text = LAYOUT_HEADER.read_text(encoding="ascii")
    assert probe.parse_layout(text) == LAYOUT
    assert L - LAYOUT["UBOOT_RAM_BASE"] > 0 and L % 0x200000 == 0
    assert LAYOUT["BOOT_IMAGE_MAX"] <= LAYOUT["STAGING_BYTES"]
    assert L + LAYOUT["STAGING_BYTES"] <= WINDOW
    assert WINDOW + LAYOUT["GUEST_BYTES"] <= WINDOW1
    for name, broken in (
            ("missing", text.replace("BE_MVP_STAGING_HPA", "BE_MVP_X")),
            ("G1 window missing", text.replace("BE_MVP_G1_HPA", "BE_MVP_X")),
            ("twice", text + "#define BE_MVP_G0_HPA\tBE_MVP_C(0x1)\n"),
            ("not a literal", text.replace(
                f"BE_MVP_C(0x{WINDOW:x})", "BE_MVP_C(BE_MVP_STAGING_HPA)"))):
        try:
            probe.parse_layout(broken)
        except ValueError:
            continue
        raise AssertionError(f"layout header {name} accepted")


@check
def recorded_map_leaves_every_extent_free():
    staging_end = L + LAYOUT["STAGING_BYTES"]
    for reserved in ([], B7_RESERVED):
        findings, report = probe.region_findings(B7_IOMEM, reserved,
                                                      LAYOUT)
        assert not findings, findings
        assert report == [
            f"region core=0x{MONITOR[0]:x}-0x{MONITOR[1]:x} "
            f"result=free",
            f"region pool=0x{POOL[0]:x}-0x{POOL[1]:x} result=free",
            f"region hart-region=0x{HARTS[0]:x}-0x{HARTS[1]:x} result=free",
            f"region mvp-region=0x{REGION[0]:x}-0x{REGION[1]:x} result=free",
            f"region staging=0x{L:x}-0x{staging_end:x} result=free",
            f"region g0-window=0x{WINDOW:x}-"
            f"0x{WINDOW + LAYOUT['GUEST_BYTES']:x} result=free",
            f"region g1-window=0x{WINDOW1:x}-"
            f"0x{WINDOW1 + LAYOUT['GUEST_BYTES']:x} result=free",
            f"region shared-pages=0x{SHARED[0]:x}-0x{SHARED[1]:x} "
            f"result=free",
            f"system_ram_children=20 fdt_reservations={len(reserved)}"], \
            report
    # The hart region and the MVP region: inside the recorded System RAM
    # range, below Fedora's kernel image, clear of OpenSBI's reservation.
    kernel_low = min(low for low, _, name in probe.parse_iomem(
        B7_IOMEM)[0][1] if name == "Kernel image")
    opensbi_high = max(high for low, high in B7_RESERVED if high <= MONITOR[0])
    assert opensbi_high <= MONITOR[0] < HARTS[0] < REGION[1] <= kernel_low


@check
def recorded_preflight_passes_the_region_check():
    findings, report = probe.region_report(recorded_preflight(), LAYOUT)
    assert not findings and len(report) == 9, (findings, report)
    assert report[-1] == "system_ram_children=20 fdt_reservations=11", report


def region_stops(iomem=B7_IOMEM, reserved=()):
    findings, _ = probe.region_findings(iomem, list(reserved), LAYOUT)
    return bool(findings)


@check
def region_check_stops_on_any_overlap():
    staging_end = L + LAYOUT["STAGING_BYTES"]
    window_end = WINDOW + LAYOUT["GUEST_BYTES"]
    window1_end = WINDOW1 + LAYOUT["GUEST_BYTES"]
    # Children: in the staging reserve (even past a small image), in
    # either window, at any region's edge, across the windows' boundary, in
    # the accepted image, the pool, the hart region, or the MVP region, and
    # across their boundaries.
    for low, high in ((MONITOR[0], MONITOR[0] + 0x1000),
                      (POOL[0] - 0x1000, POOL[0] + 0x1000),
                      (HARTS[0], HARTS[0] + 0x1000),
                      (HARTS[1] - 0x1000, HARTS[1] + 0x1000),
                      (REGION[0] + 0x20000, REGION[0] + 0x21000),
                      (REGION[1] - 0x1000, REGION[1]),
                      (L, L + 0x1000), (staging_end - 0x1000, staging_end),
                      (L + 0x500000, L + 0x501000), (WINDOW, WINDOW + 0x1000),
                      (window_end - 0x1000, window_end),
                      (WINDOW - 0x1000, WINDOW + 0x1000),
                      (WINDOW1, WINDOW1 + 0x1000),
                      (WINDOW1 + 0x2000000, WINDOW1 + 0x2001000),
                      (window1_end - 0x1000, window1_end),
                      (window1_end - 0x1000, window1_end + 0x1000),
                      (window_end - 0x1000, WINDOW1 + 0x1000),
                      (window1_end, window1_end + 0x1000)):
        assert region_stops(with_child(low, high)), (hex(low), hex(high))
        assert region_stops(reserved=[(low, high)]), (hex(low), hex(high))
    # Next to the regions, nothing stops; above G1's window, that is above
    # the shared pages, which lie directly on it.
    for low, high in ((MONITOR[0] - 0x1000, MONITOR[0]),
                      (REGION[1], REGION[1] + 0x1000),
                      (L - 0x1000, L), (staging_end, staging_end + 0x1000),
                      (WINDOW - 0x1000, WINDOW),
                      (SHARED[1], SHARED[1] + 0x1000)):
        assert not region_stops(with_child(low, high)), hex(low)
        assert not region_stops(reserved=[(low, high)]), hex(low)
    # A region outside one System RAM range; hidden addresses.
    assert region_stops(f"102000000-{WINDOW + 0x100000:x} : System RAM\n")
    assert region_stops(f"102000000-{HARTS[0] + 0xfff:x} : System RAM\n"
                        f"{HARTS[0] + 0x1000:x}-2ffffffff : System RAM\n")
    assert region_stops(f"102001000-2ffffffff : System RAM\n")
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
    findings, report = probe.region_report(preflight_text(), LAYOUT)
    assert not findings and len(report) == 9, (findings, report)
    assert probe.parse_reserved("0x1-0x2,0x3-0x4") == [(1, 2), (3, 4)]
    window = f"0x{WINDOW + 0x2000:x}-0x{WINDOW + 0x3000:x}"
    window1 = f"0x{WINDOW1 + 0x2000:x}-0x{WINDOW1 + 0x3000:x}"
    for text in (preflight_text(reserved=None),
                 preflight_text(reserved="none") + "fdt_reserved=none\n",
                 preflight_text(reserved="unreadable-needs-root"),
                 preflight_text(reserved="0x1-"),
                 preflight_text(reserved=f"0x1000-0x2000,{window}"),
                 preflight_text(reserved=f"0x1000-0x2000,{window1}"),
                 preflight_text(reserved=f"0x{HARTS[0] + 0x8000:x}-"
                                f"0x{HARTS[0] + 0x9000:x}"),
                 preflight_text(iomem=with_child(REGION[0], REGION[0] +
                                                 0x1000)),
                 preflight_text(section=False),
                 preflight_text(iomem=with_child(L, L + 0x1000)),
                 preflight_text(iomem=with_child(WINDOW1 + 0x1000,
                                                 WINDOW1 + 0x2000))):
        findings, _ = probe.region_report(text, LAYOUT)
        assert findings, text


def m0_preflight():
    """M0's recorded preflight text, pinned."""
    data = M0_PREFLIGHT.read_bytes()
    assert hashlib.sha256(data).hexdigest() == M0_PREFLIGHT_SHA256, \
        f"{M0_PREFLIGHT} differs from M0's accepted board record"
    return data.decode("ascii")


@check
def shared_pages_are_an_mvp_extent():
    """The shared pages (planning/mvp-m2-plan.md, "Memory and load
    paths"), M1's channel page their first: free on both recorded COM260
    maps, and any /proc/iomem child or FDT reservation over any of their
    three pages stops the preflight's region check, while their neighbours
    above stay free."""
    assert SHARED == (WINDOW1 + LAYOUT["GUEST_BYTES"],
                      WINDOW1 + LAYOUT["GUEST_BYTES"] + 0x3000), SHARED
    assert LAYOUT["CHANNEL_HPA"] == SHARED[0]
    line = f"region shared-pages=0x{SHARED[0]:x}-0x{SHARED[1]:x} "
    # Positive: B7's record and M0's (the Fedora 45 kernel's), whole.
    for name, text in (("B7", recorded_preflight()), ("M0", m0_preflight())):
        findings, report = probe.region_report(text, LAYOUT)
        assert not findings, (name, findings)
        assert line + "result=free" in report, (name, report)
    m0_text = m0_preflight()
    m0_iomem = probe.system_ram_text(m0_text) + "\n"
    assert m0_iomem.count("\n  ") == 20, m0_iomem
    # Refusals: a child or a reservation over the pages, straddling either
    # edge, or inside each page, on either recorded map.
    for iomem in (B7_IOMEM, m0_iomem):
        for low, high in ((SHARED[0], SHARED[1]),
                          (SHARED[0] - 0x1000, SHARED[0] + 0x1000),
                          (SHARED[1] - 0x800, SHARED[1] + 0x800),
                          (SHARED[0] + 0x400, SHARED[0] + 0x800),
                          (SHARED[0] + 0x1000, SHARED[0] + 0x2000),
                          (SHARED[0] + 0x2800, SHARED[0] + 0x2c00)):
            child = with_child(low, high, iomem=iomem)
            findings, report = probe.region_findings(child, [], LAYOUT)
            assert any(finding.startswith(
                f"shared-pages 0x{SHARED[0]:x}-0x{SHARED[1]:x} holds the "
                f"/proc/iomem child") for finding in findings), findings
            assert line + "result=busy" in report, report
            findings, _ = probe.region_report(
                preflight_text(iomem=child), LAYOUT)
            assert findings, (hex(low), hex(high))
            findings, _ = probe.region_report(preflight_text(
                iomem=iomem, reserved=f"0x{low:x}-0x{high:x}"), LAYOUT)
            assert any("shared-pages" in finding for finding in findings)
        # The pages alone are busy: just above them nothing stops.
        above = with_child(SHARED[1], SHARED[1] + 0x1000, iomem=iomem)
        assert not region_stops(above)
        assert not region_stops(iomem, [(SHARED[1], SHARED[1] + 0x1000)])
    # A System RAM range that ends at G1's window, or inside the pages,
    # leaves them outside.
    assert region_stops(f"102000000-{SHARED[0] - 1:x} : System RAM\n")
    assert region_stops(f"102000000-{SHARED[0] + 0x7ff:x} : System RAM\n")
    assert region_stops(f"102000000-{SHARED[1] - 0x1001:x} : System RAM\n")
    # The pages are a layout name: a header without them is refused.
    text = LAYOUT_HEADER.read_text(encoding="ascii")
    for name in ("BE_MVP_SHARED_PAGES_HPA", "BE_MVP_SHARED_PAGES_BYTES"):
        try:
            probe.parse_layout(text.replace(name, "BE_MVP_X"))
        except ValueError:
            continue
        raise AssertionError(f"a layout header without {name} accepted")


@check
def probe_reports_the_fdt_reservations():
    """probe prints one line, the FDT's reservations, and refuses a host
    that is not RISC-V."""
    fdt = fdt_blob([(0x101000000, 0x1000)], [(0x2FE000000, 0x2000000)])
    lines, read = [], probe.read_bytes
    machine = probe.platform.machine
    probe.print, probe.read_bytes = lines.append, lambda path: fdt
    try:
        probe.platform.machine = lambda: "riscv64"
        status = probe.main(["platform-probe.py", "probe"])
        probe.platform.machine = lambda: "x86_64"
        refused = probe.main(["platform-probe.py", "probe"])
    finally:
        probe.platform.machine, probe.read_bytes = machine, read
        del probe.print
    assert (status, refused) == (0, 2), (status, refused)
    assert lines[0] == ("fdt_reserved=0x101000000-0x101001000,"
                        "0x2fe000000-0x300000000"), lines
    assert lines[1].startswith("refusing: machine is x86_64"), lines


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    for function in CHECKS:
        function()
        print(f"PASS {function.__name__}")
    print(f"platform-probe self-test: {len(CHECKS)}/{len(CHECKS)} PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
