#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# A copy of B3's tests/check-b3-capture.py (accepted at 9b4860a0) with the
# counted changes listed in bringup/k3-b5/README.md.
"""Validate a B5 serial capture (QEMU or K3): U-Boot booti, the B3 shim
(reused unchanged), then the B5 markers.

  check-b5-capture.py CAPTURE [--expect pass|overlap] [--ram-base B]
                      [--load-address A] [--image IMAGE] [--json F]
  check-b5-capture.py --check-image TOOLCHAIN:IMG:BIN [--ram-base B]
                      [--load-address A]
  check-b5-capture.py --self-test

--expect pass (the default) requires, in this order:

- exactly one U-Boot `Moving Image from 0x<load> to 0x<moved>, end=<end>`
  (cmd/booti.c), with load == --load-address (default 0x1_4000_0000),
  moved == --ram-base (default 0x1_0200_0000, the COM260; QEMU virt's
  U-Boot uses 0x8000_0000) + the image's text_offset, and end == moved +
  image_size;
- U-Boot's report of where it put the device tree, `Loading Device Tree to
  <fdt>` or `Using Device Tree in place at <fdt>` (boot/image-fdt.c);
- exactly one `Starting kernel ...` (arch/riscv/lib/bootm.c);
- exactly one BE_K3_B3 line, `BE_K3_B3: SHIM hart=0x<16 hex> shim=0x<16>
  fdt=0x<16> dest=0x<16> bytes=0x<16>`, with hart 0, shim == moved,
  fdt == U-Boot's device tree address, dest 0x1_0200_0000, and bytes
  0x34000;
- then exactly the 22 B5 lines and nothing after them, as
  tests/check-b5-markers.py requires for base dest and hart 0;
- no U-Boot failure report (bad magic, aborted download, device tree or
  overlap errors, an unhandled exception, ...).

--expect overlap requires the same U-Boot evidence, then exactly one
`BE_K3_B3: FAIL overlap shim=0x<moved>` whose image range does overlap
[0x1_0200_0000, 0x1_0203_4000), and no SHIM line and no B5 marker at all.

--image IMAGE takes text_offset and image_size from the image header and
requires any YMODEM `## Total Size` to equal the file size, and any U-Boot
`crc32 for <load> ... <end> ==> <crc>` (an optional operator diagnostic) to
cover exactly the file at the load address with its CRC-32; without it,
the B3 board values (0x200000, 0x35000) are assumed. The total is checked
only when present: a terminal program can lose U-Boot's last loady lines
while the sender still holds the port.

--check-image checks a B5 board image before it is offered to the
operator: bringup/k3-b3/tests/check-b3-image.py's image and COM260
placement checks (imported unchanged), with the payload required to equal
BIN, the same toolchain's 0x34000-byte flat B5 image that
tests/check-b5-image.py checks.

The JSON keeps the B5 marker checker's record (result, boot_marker,
terminal, findings, fields, markers) for bringup/k3-b0/tests/
summarize-runs.py and retain-results.py. fields adds hart, base (the
shim's running address, where booti entered), and fdt, which
summarize-runs.py shows as columns, plus dest, bytes, and the U-Boot
values; `b3` holds the parsed evidence.
"""

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import struct
import sys
import zlib

sys.dont_write_bytecode = True
B5_CHECKER = pathlib.Path(__file__).resolve().parent / "check-b5-markers.py"
_SPEC = importlib.util.spec_from_file_location("check_b5_markers", B5_CHECKER)
b5 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(b5)
B3_IMAGE_CHECKER = pathlib.Path(__file__).resolve().parents[2] / "k3-b3" / \
    "tests" / "check-b3-image.py"
_SPEC = importlib.util.spec_from_file_location("check_b3_image",
                                               B3_IMAGE_CHECKER)
b3image = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(b3image)

DEST = 0x102000000
BYTES = 0x34000
TEXT_OFFSET = 0x200000
IMAGE_SIZE = 0x35000
K3_RAM_BASE = 0x102000000
LOAD_ADDRESS = 0x140000000
B3_TAG = "BE_K3_B3: "
SHIM = re.compile(r"^BE_K3_B3: SHIM hart=0x([0-9a-f]{16}) shim=0x([0-9a-f]{16})"
                  r" fdt=0x([0-9a-f]{16}) dest=0x([0-9a-f]{16}) "
                  r"bytes=0x([0-9a-f]{16})$")
FAIL_OVERLAP = re.compile(r"^BE_K3_B3: FAIL overlap shim=0x([0-9a-f]{16})$")
MOVING = re.compile(r"Moving Image from 0x([0-9a-fA-F]+) to "
                    r"0x([0-9a-fA-F]+), end=([0-9a-fA-F]+)")
FDT_PLACED = re.compile(r"(?:Loading Device Tree to|Using Device Tree in "
                        r"place at) ([0-9a-fA-F]+), end ([0-9a-fA-F]+)")
STARTING = re.compile(r"Starting kernel \.\.\.")
TOTAL = re.compile(r"## Total Size\s*= 0x([0-9a-fA-F]+) = (\d+) Bytes")
READY = re.compile(r"## Ready for binary \(ymodem\) download to "
                   r"0x([0-9a-fA-F]+) at (\d+) bps")
START_ADDR = re.compile(r"## Start Addr\s*= 0x([0-9a-fA-F]+)")
FDT_BLOB = re.compile(r"Booting using the fdt blob at (0x[0-9a-fA-F]+)")
COMMAND = re.compile(r"loady 0x[0-9a-fA-F]+ && booti .*")
BANNER = re.compile(r"U-Boot (?!SPL)\d{4}\.\d{2}\S* \(.*")
WATCHDOG = re.compile(r"WDT:\s+(.*)")
CRC32 = re.compile(r"crc32 for ([0-9a-fA-F]+) \.\.\. ([0-9a-fA-F]+) ==> "
                   r"([0-9a-fA-F]{8})")
UBOOT_FAILURES = (
    "Bad Linux RISCV Image magic",
    "Image lacks image_size field",
    "Binary (ymodem) download aborted",
    "Ramdisk image is corrupt or invalid",
    "RD image overlaps OS image",
    "Could not find a valid device tree",
    "FDT image overlaps OS image",
    "FDT creation failed",
    "Device tree not found or missing FDT support",
    "device tree - allocation error",
    "Failed using fdt_high value",
    "ERROR: booting os",
    "subcommand not supported",
    "Unhandled exception",
    "kernel_comp_addr_r or kernel_comp_size is not provided",
)
HEADER = struct.Struct("<IIQQ")


def image_facts(path):
    """text_offset, image_size, bytes, and SHA-256 of a B3 image file."""
    data = pathlib.Path(path).read_bytes()
    if len(data) < HEADER.size:
        raise ValueError(f"{path} is shorter than an Image header")
    _, _, text_offset, image_size = HEADER.unpack_from(data)
    return {"path": str(path), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "crc32": f"{zlib.crc32(data):08x}",
            "text_offset": text_offset, "image_size": image_size}


def uimage_findings(data, payload, ram_base=K3_RAM_BASE,
                    load_address=LOAD_ADDRESS):
    """(findings, facts) for a B5 board image around the flat image."""
    findings, facts = b3image.check_image(
        data, b3image.TEXT_OFFSET, hashlib.sha256(payload).hexdigest())
    findings = [finding.replace("the accepted B2 image", "the flat B5 image")
                for finding in findings]
    if len(payload) != BYTES:
        findings.append(f"flat B5 image is 0x{len(payload):x} bytes, not "
                        f"0x{BYTES:x}")
    b3image.check_placement(ram_base, b3image.TEXT_OFFSET, load_address,
                            findings)
    return findings, facts


# The B5 lines of the self-test's synthetic passing captures.
PASS_LINES = b5.pass_sequence(b5.EXPECTED_EXITS
                              if b5.EXPECTED_EXITS is not None else 55)


def lines_of(text):
    return text.replace("\r", "").split("\n")


def b3_lines(lines):
    """(index, text) of every BE_K3_B3 line, from the tag to the end."""
    found = []
    for index, raw in enumerate(lines):
        position = raw.find(B3_TAG)
        if position >= 0:
            found.append((index, raw[position:].rstrip()))
    return found


def first_marker_index(lines):
    for index, raw in enumerate(lines):
        if any(tag in raw for tag in b5.TAGS):
            return index
    return None


def all_matches(pattern, lines):
    return [(index, match) for index, raw in enumerate(lines)
            for match in [pattern.search(raw)] if match]


def evaluate(text, expect, ram_base=K3_RAM_BASE, load_address=LOAD_ADDRESS,
             image=None):
    """Return (ok, findings, evidence, markers) for one capture."""
    findings = []
    lines = lines_of(text)
    text_offset = image["text_offset"] if image else TEXT_OFFSET
    image_size = image["image_size"] if image else IMAGE_SIZE
    moved_expected = ram_base + text_offset
    evidence = {"expect": expect, "ram_base": f"0x{ram_base:x}",
                "load_address": f"0x{load_address:x}",
                "text_offset": f"0x{text_offset:x}",
                "image_size": f"0x{image_size:x}"}
    if image:
        evidence["image"] = {key: image[key] for key in
                             ("bytes", "sha256", "crc32")}

    for raw in lines:
        for failure in UBOOT_FAILURES:
            if failure in raw:
                findings.append(f"U-Boot reported {raw.strip()!r}")

    for key, pattern in (("uboot_banner", BANNER),
                         ("uboot_watchdog", WATCHDOG)):
        found = all_matches(pattern, lines)
        if found:
            evidence[key] = found[-1][1].group(0).strip()
    command = all_matches(COMMAND, lines)
    if command:
        evidence["command"] = command[-1][1].group(0).strip()
    ready = all_matches(READY, lines)
    if ready:
        address = int(ready[-1][1].group(1), 16)
        evidence["ymodem_load"] = f"0x{address:x}"
        evidence["ymodem_bps"] = ready[-1][1].group(2)
        if address != load_address:
            findings.append(f"loady address 0x{address:x} != "
                            f"0x{load_address:x}")
    totals = all_matches(TOTAL, lines)
    if totals:
        total = int(totals[-1][1].group(2))
        evidence["ymodem_total"] = str(total)
        if int(totals[-1][1].group(1), 16) != total:
            findings.append("YMODEM total size is inconsistent")
        if image and total != image["bytes"]:
            findings.append(f"YMODEM total {total} != image size "
                            f"{image['bytes']}")
    for _, match in all_matches(CRC32, lines):
        first, last, crc = (int(match.group(group), 16) for group in
                            (1, 2, 3))
        evidence["uboot_crc32"] = f"{crc:08x}"
        if first != load_address:
            findings.append(f"crc32 starts at 0x{first:x}, not "
                            f"0x{load_address:x}")
        if image and (last - first + 1 != image["bytes"] or
                      f"{crc:08x}" != image["crc32"]):
            findings.append(f"U-Boot crc32 {crc:08x} over 0x{first:x}-"
                            f"0x{last:x} is not the image's "
                            f"{image['crc32']} over {image['bytes']} bytes")
    start = all_matches(START_ADDR, lines)
    if start:
        evidence["ymodem_start"] = f"0x{int(start[-1][1].group(1), 16):x}"

    moving = all_matches(MOVING, lines)
    moved = None
    moving_index = None
    if len(moving) != 1:
        findings.append(f"{len(moving)} U-Boot 'Moving Image' lines, "
                        f"expected 1")
    else:
        moving_index, match = moving[0]
        load, moved, end = (int(match.group(group), 16) for group in
                            (1, 2, 3))
        evidence.update(uboot_load=f"0x{load:x}", uboot_moved=f"0x{moved:x}",
                        uboot_end=f"0x{end:x}")
        if load != load_address:
            findings.append(f"booti load 0x{load:x} != 0x{load_address:x}")
        if moved != moved_expected:
            findings.append(f"booti moved the image to 0x{moved:x}, not RAM "
                            f"base 0x{ram_base:x} + text_offset "
                            f"0x{text_offset:x}")
        if end != moved + image_size:
            findings.append(f"booti end 0x{end:x} != 0x{moved:x} + image "
                            f"size 0x{image_size:x}")

    fdt_lines = all_matches(FDT_PLACED, lines)
    uboot_fdt = None
    if len(fdt_lines) != 1:
        findings.append(f"{len(fdt_lines)} U-Boot device tree placement "
                        f"lines, expected 1")
    else:
        uboot_fdt = int(fdt_lines[0][1].group(1), 16)
        evidence["uboot_fdt"] = f"0x{uboot_fdt:x}"
        if moving_index is not None and fdt_lines[0][0] < moving_index:
            findings.append("device tree placed before booti moved the image")
    blob = all_matches(FDT_BLOB, lines)
    if blob:
        evidence["fdt_blob"] = blob[-1][1].group(1)

    starting = all_matches(STARTING, lines)
    starting_index = None
    if len(starting) != 1:
        findings.append(f"{len(starting)} 'Starting kernel ...' lines, "
                        f"expected 1")
    else:
        starting_index = starting[0][0]
        if moving_index is not None and starting_index < moving_index:
            findings.append("'Starting kernel ...' precedes 'Moving Image'")

    b3 = b3_lines(lines)
    evidence["b3_lines"] = [line for _, line in b3]
    markers = b5.extract(text)
    marker_index = first_marker_index(lines)
    shim = None
    if expect == "pass":
        if len(b3) != 1 or not SHIM.match(b3[0][1]):
            findings.append(f"BE_K3_B3 lines {evidence['b3_lines']}, "
                            f"expected exactly one well-formed SHIM line")
        else:
            before = len(findings)
            index, line = b3[0]
            hart, base, fdt, dest, size = (int(value, 16) for value in
                                           SHIM.match(line).groups())
            shim = {"hart": hart, "base": base, "fdt": fdt, "dest": dest,
                    "bytes": size}
            evidence["shim"] = {key: f"0x{value:016x}" for key, value in
                                shim.items()}
            if hart != b5.B5_HART:
                findings.append(f"shim ran on hart {hart}, not 0")
            if moved is not None and base != moved:
                findings.append(f"shim ran at 0x{base:x}, not booti's "
                                f"0x{moved:x}")
            if uboot_fdt is not None and fdt != uboot_fdt:
                findings.append(f"shim fdt 0x{fdt:x} != U-Boot's "
                                f"0x{uboot_fdt:x}")
            if dest != DEST:
                findings.append(f"shim destination 0x{dest:x} != "
                                f"0x{DEST:x}")
            if size != BYTES:
                findings.append(f"shim copied 0x{size:x} bytes, not "
                                f"0x{BYTES:x}")
            if starting_index is None or index < starting_index:
                findings.append("SHIM line precedes 'Starting kernel ...'")
            if marker_index is not None and marker_index < index:
                findings.append("a B5 marker precedes the SHIM line")
            evidence["shim_ok"] = len(findings) == before
        _, marker_findings = b5.evaluate(
            text, "pass", shim["dest"] if shim else None,
            shim["hart"] if shim else None)
        findings += [f"B5: {finding}" for finding in marker_findings]
    elif expect == "overlap":
        if len(b3) != 1 or not FAIL_OVERLAP.match(b3[0][1]):
            findings.append(f"BE_K3_B3 lines {evidence['b3_lines']}, "
                            f"expected exactly one overlap failure")
        else:
            index, line = b3[0]
            base = int(FAIL_OVERLAP.match(line).group(1), 16)
            evidence["overlap_shim"] = f"0x{base:016x}"
            if moved is not None and base != moved:
                findings.append(f"refusing shim ran at 0x{base:x}, not "
                                f"booti's 0x{moved:x}")
            if not (base < DEST + BYTES and DEST < base + image_size):
                findings.append(f"shim at 0x{base:x} does not overlap the "
                                f"destination, yet refused")
            if starting_index is None or index < starting_index:
                findings.append("failure line precedes 'Starting kernel'")
        if markers:
            findings.append(f"B5 ran after an overlap refusal: {markers[:3]}")
    else:
        findings.append(f"unknown expectation {expect!r}")
    return not findings, findings, evidence, markers


def terminal(markers, evidence):
    if any(line.startswith("BE_K3_B3: FAIL")
           for line in evidence["b3_lines"]):
        return "fail-marker"
    return b5.terminal(markers)


def result_record(capture, expect, ok, findings, evidence, markers):
    record = b5.result_record(capture, expect, markers, ok, findings)
    shim_ok = expect == "pass" and evidence.get("shim_ok", False)
    record["boot_marker"] = "PASS" if shim_ok and \
        b5.full_sequence_reached(markers) else "FAIL"
    record["terminal"] = terminal(markers, evidence)
    fields = record["fields"]
    shim = evidence.get("shim")
    if shim:
        fields.update(hart=shim["hart"], base=shim["base"], fdt=shim["fdt"],
                      dest=shim["dest"], bytes=shim["bytes"])
    if "overlap_shim" in evidence:
        fields["overlap_shim"] = evidence["overlap_shim"]
    for key in ("uboot_load", "uboot_moved", "uboot_end", "uboot_fdt",
                "ymodem_total", "uboot_crc32"):
        if key in evidence:
            fields[key] = evidence[key]
    for line in evidence["b3_lines"]:
        if line.startswith("BE_K3_B3: FAIL") and "failure" not in fields:
            fields["failure"] = line[len(B3_TAG):]
    record["b3"] = evidence
    return record


def capture(ram_base=K3_RAM_BASE, moved=0x102200000, fdt=0x2f7659000,
            in_place=False, shim=None, markers=PASS_LINES,
            total=IMAGE_SIZE, extra_after=""):
    """A synthetic COM260-style capture (timestamps, CRLF), for tests."""
    if shim is None:
        shim = (f"BE_K3_B3: SHIM hart=0x{0:016x} shim=0x{moved:016x} "
                f"fdt=0x{fdt:016x} dest=0x{DEST:016x} bytes=0x{BYTES:016x}")
    placed = (f"   Using Device Tree in place at {fdt:016x}, end "
              f"{fdt + 0x4fff:016x}" if in_place else
              f"   Loading Device Tree to {fdt:016x}, end {fdt + 0xc87f:016x}"
              f" ... OK")
    lines = [
        "[   1.938] load env_k3.txt from bootfs successful",
        "[   1.943] Autoboot in 3 seconds",
        "=> loady 0x140000000 && booti 0x140000000 - ${fdtcontroladdr}",
        "## Ready for binary (ymodem) download to 0x140000000 at 115200 "
        "bps...",
        f"CCC## Total Size      = 0x{total:08x} = {total} Bytes",
        "## Start Addr      = 0x140000000",
        f"[  41.426] Moving Image from 0x140000000 to 0x{moved:x}, "
        f"end={moved + IMAGE_SIZE:x}",
        "[  41.442] ## Flattened Device Tree blob at fffd2000",
        "[  41.444]    Booting using the fdt blob at 0xfffd2000",
        placed,
        "[  41.681] ",
        "Starting kernel ...",
        "",
        "[  41.681] Removing MTD device #0 (nor0) with use count 1",
    ]
    if shim:
        lines.append(shim)
    lines += list(markers)
    return "\r\n".join(lines) + "\r\n" + extra_after


def self_test():
    qemu = dict(ram_base=0x80000000, moved=0x80200000, fdt=0xff73a250,
                in_place=True)
    good = capture()
    overlap_line = f"BE_K3_B3: FAIL overlap shim=0x{0x102000000:016x}"
    overlap = capture(moved=0x102000000, shim=overlap_line, markers=())
    overlap_image = {"path": "x", "bytes": IMAGE_SIZE, "sha256": "0",
                     "crc32": "00000000", "text_offset": 0x82000000,
                     "image_size": IMAGE_SIZE}
    board_image = dict(overlap_image, text_offset=TEXT_OFFSET,
                       crc32="b1859da5")
    crc_line = ("=> crc32 0x140000000 ${filesize}\r\n"
                "crc32 for 140000000 ... 140034fff ==> b1859da5\r\n")
    with_crc = good.replace("Moving Image", "x\r\n" + crc_line + "Moving "
                            "Image", 1)
    lines = list(PASS_LINES)
    parts = good.split("\r\n")
    qemu_overlap = {"image": overlap_image, "ram_base": 0x80000000}
    cases = [
        ("COM260 pass", good, "pass", {}, True),
        ("COM260 pass, LF only", good.replace("\r", ""), "pass", {}, True),
        ("COM260 pass with image", good, "pass", {"image": board_image},
         True),
        ("QEMU pass", capture(**qemu), "pass", {"ram_base": 0x80000000},
         True),
        ("COM260 capture at QEMU RAM base", good, "pass",
         {"ram_base": 0x80000000}, False),
        ("missing SHIM line", capture(shim=""), "pass", {}, False),
        ("wrong shim address",
         good.replace("shim=0x0000000102200000", "shim=0x0000000102201000"),
         "pass", {}, False),
        ("shim on hart 1", good.replace("hart=0x0000000000000000",
                                        "hart=0x0000000000000001"),
         "pass", {}, False),
        ("shim fdt differs", good.replace("fdt=0x00000002f7659000",
                                          "fdt=0x00000002f765a000"),
         "pass", {}, False),
        ("shim destination", good.replace("dest=0x0000000102000000",
                                          "dest=0x0000000102200000"),
         "pass", {}, False),
        ("shim byte count", good.replace("bytes=0x0000000000034000",
                                         "bytes=0x0000000000033000"),
         "pass", {}, False),
        ("unformatted shim digit", good.replace("fdt=0x00000002f7659000",
                                                "fdt=0x00000002f765900?"),
         "pass", {}, False),
        ("failure marker", capture(extra_after="BE_B5:FAIL resume\r\n"),
         "pass", {}, False),
        ("overlap failure", capture(shim=overlap_line), "pass", {}, False),
        ("extra SHIM line", capture(extra_after=parts[14] + "\r\n"),
         "pass", {}, False),
        ("missing Moving Image line",
         "\r\n".join(line for line in good.split("\r\n")
                     if "Moving Image" not in line), "pass", {}, False),
        ("two Moving Image lines", good.replace(
            "## Start Addr", "Moving Image from 0x140000000 to 0x102200000, "
            "end=102235000\r\n## Start Addr"), "pass", {}, False),
        ("booti end inconsistent", good.replace("end=102235000",
                                                "end=102234000"),
         "pass", {}, False),
        ("loaded elsewhere", good.replace("from 0x140000000",
                                          "from 0x138000000"),
         "pass", {}, False),
        ("missing Starting kernel",
         good.replace("Starting kernel ...", "Starting"), "pass", {}, False),
        ("missing device tree placement",
         good.replace("Loading Device Tree", "Loading Device Tre"), "pass",
         {}, False),
        ("extra marker", capture(extra_after="BE_B5:07 EXTRA\r\n"), "pass",
         {}, False),
        ("markers truncated", capture(markers=lines[:-1]), "pass", {},
         False),
        ("marker before SHIM", capture(
            shim="", markers=[lines[0]] + [
                f"BE_K3_B3: SHIM hart=0x{0:016x} shim=0x{0x102200000:016x} "
                f"fdt=0x{0x2f7659000:016x} dest=0x{DEST:016x} "
                f"bytes=0x{BYTES:016x}"] + lines[1:]), "pass", {}, False),
        ("SHIM before Starting kernel", "\r\n".join(
            parts[:10] + [parts[14]] + parts[10:14] + parts[15:]), "pass",
         {}, False),
        ("U-Boot exception", capture(
            extra_after="Unhandled exception: Store/AMO access fault\r\n"),
         "pass", {}, False),
        ("YMODEM total differs from image", capture(total=0x34fff), "pass",
         {"image": board_image}, False),
        ("U-Boot crc32 matches", with_crc, "pass", {"image": board_image},
         True),
        ("U-Boot crc32 differs", with_crc.replace("==> b1859da5",
                                                  "==> b1859da6"), "pass",
         {"image": board_image}, False),
        ("U-Boot crc32 short", with_crc.replace("140034fff", "140034ffb"),
         "pass", {"image": board_image}, False),
        ("overlap refused", overlap, "overlap", qemu_overlap, True),
        ("overlap refused, COM260 RAM base", overlap, "overlap",
         {"image": overlap_image}, False),
        ("overlap refusal then B5", capture(moved=0x102000000,
                                            shim=overlap_line), "overlap",
         qemu_overlap, False),
        ("overlap expected, SHIM seen", good, "overlap", {}, False),
        ("refusal without overlap", capture(
            shim=f"BE_K3_B3: FAIL overlap shim=0x{0x102200000:016x}",
            markers=()), "overlap", {}, False),
        ("refusal at the wrong address", overlap.replace(
            "shim=0x0000000102000000", "shim=0x0000000102001000"), "overlap",
         qemu_overlap, False),
        ("B5 guest line without the prefix", capture(
            markers=lines[:11] + [lines[11][len(b5.GUEST_PREFIX):]] +
            lines[12:]), "pass", {}, False),
        ("B5 noise among the markers", capture(
            markers=lines[:12] + ["fail to get alias node"] + lines[12:]),
         "pass", {}, False),
    ]
    failed = 0
    for name, text, expect, options, wanted in cases:
        ok, findings, _, _ = evaluate(text, expect, **options)
        failed += ok != wanted
        print(f"{'ok  ' if ok == wanted else 'FAIL'} {name}: ok={ok} "
              f"findings={findings}")
    records = [
        ("record pass", good, "pass", {}, "PASS", "PASS",
         "shutdown-requested"),
        ("record failure marker",
         capture(extra_after="BE_B5:FAIL resume\r\n"), "pass", {}, "FAIL",
         "FAIL", "fail-marker"),
        ("record missing SHIM", capture(shim=""), "pass", {}, "FAIL", "FAIL",
         "shutdown-requested"),
        ("record overlap", overlap, "overlap", qemu_overlap, "PASS", "FAIL",
         "fail-marker"),
        ("record truncated", capture(markers=lines[:5]), "pass", {}, "FAIL",
         "FAIL", "none"),
    ]
    for name, text, expect, options, result, boot, end in records:
        ok, findings, evidence, markers = evaluate(text, expect, **options)
        record = result_record("x", expect, ok, findings, evidence, markers)
        got = (record["result"], record["boot_marker"], record["terminal"])
        wanted = (result, boot, end)
        failed += got != wanted
        print(f"{'ok  ' if got == wanted else 'FAIL'} {name}: "
              f"result/boot_marker/terminal={got}")
    ok, findings, evidence, markers = evaluate(good, "pass")
    record = result_record("x", "pass", ok, findings, evidence, markers)
    fields = record["fields"]
    wanted_fields = {"hart": "0x0000000000000000",
                     "base": "0x0000000102200000",
                     "fdt": "0x00000002f7659000",
                     "dest": "0x0000000102000000",
                     "bytes": "0x0000000000034000",
                     "uboot_moved": "0x102200000",
                     "guest_timer": "cause=0x8000000000000005 "
                                    "after_deadline=1 cleared=1"}
    for key, value in wanted_fields.items():
        if fields.get(key) != value:
            print(f"FAIL field {key}: {fields.get(key)!r}")
            failed += 1
    if not all(isinstance(value, str) for value in fields.values()) or \
            record["markers"] != list(PASS_LINES):
        print(f"FAIL record fields/markers {fields}")
        failed += 1
    json.dumps(record)
    payload = b"\xa5" * BYTES
    images = [
        ("image around the flat image", bytes(b3image.synthetic()), payload,
         True),
        ("image around another payload", bytes(b3image.synthetic()),
         b"\x5a" * BYTES, False),
        ("flat image short", bytes(b3image.synthetic()), payload[:-8],
         False),
        ("image with a variant text_offset",
         bytes(b3image.synthetic(0x82200000)), payload, False),
    ]
    for name, data, flat, wanted in images:
        image_findings, _ = uimage_findings(data, flat)
        ok = not image_findings
        failed += ok != wanted
        print(f"{'ok  ' if ok == wanted else 'FAIL'} {name}: ok={ok} "
              f"findings={image_findings}")
    total = len(cases) + len(records) + len(images)
    print(f"BE_B5_CAPTURE_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
          f"cases={total}")
    return 0 if not failed else 1


def number(value):
    return int(value, 0)


def check_image(spec, ram_base, load_address):
    """--check-image TOOLCHAIN:IMG:BIN: the board image before a run."""
    toolchain, _, rest = spec.partition(":")
    path, _, flat = rest.partition(":")
    data = pathlib.Path(path).read_bytes()
    payload = pathlib.Path(flat).read_bytes()
    findings, facts = uimage_findings(data, payload, ram_base, load_address)
    if toolchain not in ("gcc", "clang"):
        findings.append(f"unknown toolchain {toolchain!r}")
    for finding in findings:
        print(f"finding[{toolchain}]: {finding}")
    print(f"BE_B5_UIMAGE[{toolchain}]: {'PASS' if not findings else 'FAIL'} "
          f"{path} bytes=0x{facts['bytes']:x} sha256={facts['sha256']} "
          f"crc32={facts['crc32']} payload_sha256={facts['payload_sha256']}")
    return 0 if not findings else 1


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("capture", nargs="?")
    parser.add_argument("--expect", choices=("pass", "overlap"),
                        default="pass")
    parser.add_argument("--ram-base", type=number, default=K3_RAM_BASE)
    parser.add_argument("--load-address", type=number, default=LOAD_ADDRESS)
    parser.add_argument("--image")
    parser.add_argument("--json")
    parser.add_argument("--check-image", metavar="TOOLCHAIN:IMG:BIN")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.check_image:
        return check_image(args.check_image, args.ram_base,
                           args.load_address)
    if args.capture is None:
        parser.error("a capture file is required")
    image = image_facts(args.image) if args.image else None
    with open(args.capture, "rb") as handle:
        text = handle.read().decode("utf-8", errors="replace")
    ok, findings, evidence, markers = evaluate(
        text, args.expect, args.ram_base, args.load_address, image)
    record = result_record(args.capture, args.expect, ok, findings, evidence,
                           markers)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
    for key in ("uboot_banner", "uboot_watchdog", "command", "ymodem_load",
                "ymodem_total", "ymodem_start", "uboot_crc32", "uboot_load",
                "uboot_moved", "uboot_end", "uboot_fdt"):
        if key in evidence:
            print(f"{key}={evidence[key]}")
    for line in evidence["b3_lines"]:
        print(line)
    for line in markers:
        print(line)
    for finding in findings:
        print(f"finding: {finding}")
    if args.expect == "pass":
        print(f"BE_B5_RESULT: {record['boot_marker']} "
              f"terminal={record['terminal']}")
    print(f"BE_B5_CAPTURE[{args.expect}]: {record['result']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
