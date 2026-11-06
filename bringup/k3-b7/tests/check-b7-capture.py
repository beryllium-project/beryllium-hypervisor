#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# A copy of B6's tests/check-b6-capture.py (accepted at e20c55df) with the
# counted changes listed in bringup/k3-b7/README.md.
"""Validate a B7 serial capture (QEMU or K3): Linux's kexec handoff, the
B3 shim (reused unchanged) at the staging address L, then the B7 markers
of both guests. B7 has no U-Boot run (plan, Q4: kexec only).

  check-b7-capture.py CAPTURE --mode kexec [--image IMAGE]
                      [--kexec-fdt F] [--pins FILE | --kernel-bytes N
                       --image-size S --banner TEXT]
                      [--toolchain gcc|clang] [--json F]
  check-b7-capture.py --check-image TOOLCHAIN:IMG[:BIN] [--pins FILE ...]
  check-b7-capture.py --write-fixtures DIR [--pins FILE]
  check-b7-capture.py --self-test

--mode kexec requires Fedora's kexec handoff, each line exactly once and
in this order (kernel/kexec_core.c, arch/riscv/kernel/machine_kexec.c):
`kexec_core: Starting new kernel`; `Will call new kernel at <L> from hart
id 0`; `FDT image at <fdt>`, with <fdt> the loader's address (--kexec-fdt,
k3-run.sh's loader line) and L plus the image rounded up to
BE_B7_KEXEC_FDT_ALIGN (--image), or, without either, an aligned slot after
L that ends below the guest windows; and `Bye...`.

Exactly one BE_K3_B3 line follows the handoff, `BE_K3_B3: SHIM
hart=0x<16 hex> shim=0x<16> fdt=0x<16> dest=0x<16> bytes=0x<16>`, with
hart 0, shim == L, fdt == the handoff's device tree, dest the B7 monitor
image, and bytes its size; no B7 marker precedes it; and the capture must
pass tests/check-b7-markers.py, with the guest pins from
bringup/k3-b7/guest/pins.txt or the options.

--check-image checks a B7 boot image before it is offered to the loader:
bringup/k3-b3/tests/check-b3-image.py's header (with text_offset L minus
the COM260 RAM base, which the kexec loader also requires), descriptor,
and report-line templates (imported unchanged); a file of at most
BE_B7_BOOT_IMAGE_MAX bytes, a 4 KiB multiple, with image_size equal to it;
at BE_B7_BOOT_MONITOR_OFFSET the flat monitor image, equal to BIN when
given; at BE_B7_BOOT_KERNEL_OFFSET a RISC-V Image header with text_offset
0x200000 (with pins, the pinned image_size, and G0's DTB right after the
pinned file size); the last 8 KiB G0's and then G1's 4 KiB DTB, which
differ; and the B7 placement: [L, L + size) inside COM260 System RAM and
clear of the monitor and its pool and both guest windows, with the kexec
FDT slot below the windows.

--write-fixtures DIR writes a synthetic B7 boot image, flat monitor image,
and a passing COM260 kexec capture for them, with the guest pins (--pins,
default bringup/k3-b7/guest/pins.txt), for tests/run-tool-dry-run.sh.

The JSON keeps the marker checker's record (result, boot_marker, terminal,
findings, fields, markers) for bringup/k3-b0/tests/summarize-runs.py and
retain-results.py; fields (the SHIM's hart, base, and fdt, which
summarize-runs.py shows as columns) gain the loader's values, and
`handoff` holds the parsed evidence.
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
HERE = pathlib.Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


b7 = load("check_b7_markers", HERE / "check-b7-markers.py")
b3image = load("check_b3_image", HERE.parents[1] / "k3-b3" / "tests" /
               "check-b3-image.py")
LAYOUT = b7.parse_layout(
    b7.LAYOUT_HEADER.read_text(encoding="utf-8"), b7.LAYOUT_HEADER,
    b7.LAYOUT_NAMES + ("POOL_BYTES", "BOOT_MONITOR_OFFSET",
                       "BOOT_KERNEL_OFFSET", "BOOT_IMAGE_MAX",
                       "PAYLOAD_ALIGN", "UBOOT_RAM_BASE",
                       "UBOOT_TEXT_OFFSET", "KEXEC_FDT_ALIGN",
                       "KEXEC_FDT_MAX"))
STAGING = LAYOUT["STAGING_HPA"]
DEST = LAYOUT["MONITOR_HPA"]
BYTES = LAYOUT["MONITOR_BYTES"]
K3_RAM_BASE = LAYOUT["UBOOT_RAM_BASE"]
WINDOWS = tuple((base, base + LAYOUT["GUEST_BYTES"]) for base in b7.WINDOWS)
LOWER_WINDOW = min(base for base, _ in WINDOWS)
PAGE = 0x1000
# B3's shim descriptor fixes the copy; it must be B7's monitor image.
if (b3image.DEST, b3image.PAYLOAD_SIZE, b3image.PAYLOAD_OFFSET) != \
        (DEST, BYTES, LAYOUT["BOOT_MONITOR_OFFSET"]):
    raise ValueError("B3's shim descriptor differs from the B7 layout")
B3_TAG = "BE_K3_B3: "
SHIM = re.compile(r"^BE_K3_B3: SHIM hart=0x([0-9a-f]{16}) shim=0x([0-9a-f]{16})"
                  r" fdt=0x([0-9a-f]{16}) dest=0x([0-9a-f]{16}) "
                  r"bytes=0x([0-9a-f]{16})$")
# Linux's kexec handoff, in order (kexec_core.c; riscv machine_kexec.c).
KEXEC_STARTING = re.compile(r"kexec_core: Starting new kernel")
KEXEC_CALL = re.compile(r"Will call new kernel at ([0-9a-f]+) from hart id "
                        r"([0-9a-f]+)")
KEXEC_FDT = re.compile(r"FDT image at ([0-9a-f]+)")
KEXEC_BYE = re.compile(r"Bye\.\.\.")
HEADER = struct.Struct("<IIQQ")
IMAGE_MAGIC2_OFFSET = 0x38
FDT_MAGIC = 0xD00DFEED


def align_up(value, alignment):
    return (value + alignment - 1) & ~(alignment - 1)


def kexec_fdt_for(image_bytes):
    """Where kexec-load.py puts the FDT for an image of IMAGE_BYTES."""
    return STAGING + align_up(image_bytes, LAYOUT["KEXEC_FDT_ALIGN"])


def image_facts(path):
    """text_offset, image_size, bytes, and SHA-256 of a B7 boot image."""
    data = pathlib.Path(path).read_bytes()
    if len(data) < HEADER.size:
        raise ValueError(f"{path} is shorter than an Image header")
    _, _, text_offset, image_size = HEADER.unpack_from(data)
    return {"path": str(path), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "crc32": f"{zlib.crc32(data):08x}",
            "text_offset": text_offset, "image_size": image_size}


def overlaps(start, end, other_start, other_end):
    return start < other_end and other_start < end


def placement_findings(size, text_offset):
    """The B7 placement of a SIZE-byte boot image (plan, Memory and load
    paths): kexec-load.py stages it at L, which B3's header names too (the
    COM260 RAM base plus text_offset), with the FDT slot after it, clear of
    the monitor and its pool and below both guest windows."""
    findings = []
    moved = K3_RAM_BASE + text_offset
    if moved != STAGING:
        findings.append(f"the header places the image at 0x{moved:x} (RAM "
                        f"base 0x{K3_RAM_BASE:x} + text_offset "
                        f"0x{text_offset:x}), not L 0x{STAGING:x}")
    end = STAGING + size
    fdt_end = kexec_fdt_for(size) + LAYOUT["KEXEC_FDT_MAX"]
    monitor_end = LAYOUT["POOL_HPA"] + LAYOUT["POOL_BYTES"]
    if overlaps(STAGING, end, DEST, monitor_end):
        findings.append("the staged image overlaps the monitor or its pool")
    for guest, window in enumerate(WINDOWS):
        if overlaps(STAGING, fdt_end, *window):
            findings.append(f"the staged image or its kexec FDT slot (to "
                            f"0x{fdt_end:x}) reaches G{guest}'s window "
                            f"0x{window[0]:x}")
    ram = b3image.K3_SYSTEM_RAM
    if STAGING < ram[0] or fdt_end > ram[1] or \
            any(window[1] > ram[1] for window in WINDOWS):
        findings.append("the staged image, FDT slot, or a window is outside "
                        "COM260 System RAM")
    return findings


def boot_image_findings(data, payload=None, pins=None):
    """(findings, facts) for a B7 boot image's bytes."""
    findings = []
    text_offset = STAGING - K3_RAM_BASE
    header = b3image.check_header(data, text_offset, findings)
    b3image.check_descriptor(data, findings)
    stub = data[:b3image.STUB_PAGE]
    for template in b3image.TEMPLATES:
        if stub.count(template) != 1:
            findings.append(f"stub page lacks the template {template[:24]!r}")
    size = len(data)
    if size > LAYOUT["BOOT_IMAGE_MAX"]:
        findings.append(f"file size 0x{size:x} is above "
                        f"0x{LAYOUT['BOOT_IMAGE_MAX']:x}")
    if size % LAYOUT["PAYLOAD_ALIGN"]:
        findings.append(f"file size 0x{size:x} is not a multiple of "
                        f"0x{LAYOUT['PAYLOAD_ALIGN']:x}")
    monitor = data[LAYOUT["BOOT_MONITOR_OFFSET"]:
                   LAYOUT["BOOT_MONITOR_OFFSET"] + BYTES]
    if payload is not None and (monitor != payload or len(payload) != BYTES):
        findings.append(f"the monitor at 0x{LAYOUT['BOOT_MONITOR_OFFSET']:x} "
                        f"is not the 0x{BYTES:x}-byte flat image given")
    kernel_at = LAYOUT["BOOT_KERNEL_OFFSET"]
    kernel = data[kernel_at:kernel_at + 64]
    if len(kernel) < 64 or kernel[IMAGE_MAGIC2_OFFSET:
                                  IMAGE_MAGIC2_OFFSET + 4] != b"RSC\x05":
        findings.append(f"no RISC-V Image header at 0x{kernel_at:x}")
    else:
        _, _, kernel_offset, kernel_size = HEADER.unpack_from(kernel)
        if kernel_offset != LAYOUT["KERNEL_TEXT_OFFSET"]:
            findings.append(f"kernel text_offset 0x{kernel_offset:x} != "
                            f"0x{LAYOUT['KERNEL_TEXT_OFFSET']:x}")
        if pins and kernel_size != pins.image_size:
            findings.append(f"kernel image_size 0x{kernel_size:x} != the "
                            f"pinned 0x{pins.image_size:x}")
    dtb_bytes = LAYOUT["DTB_BYTES"]
    dtbs = (size - 2 * dtb_bytes, size - dtb_bytes)
    if pins and dtbs[0] != align_up(kernel_at + pins.kernel_bytes,
                                    LAYOUT["PAYLOAD_ALIGN"]):
        findings.append(f"G0's DTB at 0x{dtbs[0]:x} does not follow the "
                        f"pinned {pins.kernel_bytes}-byte kernel")
    for guest, dtb_at in enumerate(dtbs):
        if dtb_at < kernel_at + 64 or struct.unpack_from(
                ">II", data, dtb_at) != (FDT_MAGIC, dtb_bytes):
            findings.append(f"G{guest}'s 0x{dtb_bytes:x} bytes at "
                            f"0x{dtb_at:x} are not a 0x{dtb_bytes:x}-byte "
                            f"DTB")
    if dtbs[0] >= kernel_at + 64 and \
            data[dtbs[0]:dtbs[1]] == data[dtbs[1]:]:
        findings.append("G0's and G1's DTBs are the same bytes")
    findings += placement_findings(size, text_offset)
    facts = {
        "bytes": size,
        "sha256": hashlib.sha256(data).hexdigest(),
        "crc32": f"{zlib.crc32(data):08x}",
        "payload_sha256": hashlib.sha256(monitor).hexdigest(),
        "text_offset": header["text_offset"] if header else None,
        "kexec_fdt": kexec_fdt_for(size),
    }
    return findings, facts


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
    """The first line holding a B7 marker tag (the SHIM's excluded)."""
    for index, raw in enumerate(lines):
        if any(tag in raw for tag in b7.TAGS if tag != b7.SHIM_TAG):
            return index
    return None


def all_matches(pattern, lines):
    return [(index, match) for index, raw in enumerate(lines)
            for match in [pattern.search(raw)] if match]


def one(pattern, lines, name, findings):
    """(index, match) of the single line matching, or (None, None)."""
    found = all_matches(pattern, lines)
    if len(found) != 1:
        findings.append(f"{len(found)} {name} lines, expected 1")
        return None, None
    return found[0]


def kexec_handoff(lines, image, kexec_fdt, evidence, findings):
    """(handoff index, FDT) from Linux's kexec handoff lines."""
    indexes = []
    for pattern, name in ((KEXEC_STARTING, "'kexec_core: Starting new "
                                           "kernel'"),
                          (KEXEC_CALL, "'Will call new kernel'"),
                          (KEXEC_FDT, "'FDT image at'"),
                          (KEXEC_BYE, "'Bye...'")):
        index, match = one(pattern, lines, name, findings)
        indexes.append((index, match, name))
    order = [index for index, _, _ in indexes if index is not None]
    if order != sorted(order):
        findings.append("the kexec handoff lines are out of order")
    _, call, _ = indexes[1]
    if call:
        entry, hart = int(call.group(1), 16), int(call.group(2), 16)
        evidence.update(kexec_entry=f"0x{entry:x}", kexec_hart=str(hart))
        if entry != STAGING:
            findings.append(f"kexec entry 0x{entry:x} is not L "
                            f"0x{STAGING:x}")
        if hart != b7.BOOT_HART:
            findings.append(f"kexec from hart {hart}, not {b7.BOOT_HART}")
    _, fdt_match, _ = indexes[2]
    fdt = None
    if fdt_match:
        fdt = int(fdt_match.group(1), 16)
        evidence["kexec_fdt"] = f"0x{fdt:x}"
        wanted = kexec_fdt if kexec_fdt is not None else \
            kexec_fdt_for(image["bytes"]) if image else None
        if wanted is not None and fdt != wanted:
            findings.append(f"kexec FDT 0x{fdt:x} != 0x{wanted:x}")
        slot_end = fdt + LAYOUT["KEXEC_FDT_MAX"]
        if fdt % LAYOUT["KEXEC_FDT_ALIGN"] or \
                not kexec_fdt_for(1) <= fdt <= \
                kexec_fdt_for(LAYOUT["BOOT_IMAGE_MAX"]) or \
                slot_end > LOWER_WINDOW:
            findings.append(f"kexec FDT 0x{fdt:x} is not an aligned slot "
                            f"after L below the guest windows")
    return indexes[3][0], fdt


def evaluate(text, mode, image=None, kexec_fdt=None, pins=None):
    """Return (ok, findings, evidence, markers) for one capture."""
    findings = []
    lines = lines_of(text)
    evidence = {"mode": mode}
    if image:
        evidence["image"] = {key: image[key] for key in
                             ("bytes", "sha256", "crc32")}
    before = len(findings)
    if mode == "kexec":
        handoff, fdt = kexec_handoff(lines, image, kexec_fdt, evidence,
                                     findings)
    else:
        return False, [f"unknown mode {mode!r}"], evidence, []
    evidence["handoff_ok"] = len(findings) == before
    b3 = b3_lines(lines)
    evidence["b3_lines"] = [line for _, line in b3]
    markers = b7.extract(text)
    marker_index = first_marker_index(lines)
    before = len(findings)
    if len(b3) != 1 or not SHIM.match(b3[0][1]):
        findings.append(f"BE_K3_B3 lines {evidence['b3_lines']}, expected "
                        f"exactly one well-formed SHIM line")
    else:
        index, line = b3[0]
        hart, base, shim_fdt, dest, size = (int(value, 16) for value in
                                            SHIM.match(line).groups())
        evidence["shim"] = {key: f"0x{value:016x}" for key, value in zip(
            ("hart", "base", "fdt", "dest", "bytes"),
            (hart, base, shim_fdt, dest, size))}
        if hart != b7.BOOT_HART:
            findings.append(f"shim ran on hart {hart}, not {b7.BOOT_HART}")
        if base != STAGING:
            findings.append(f"shim ran at 0x{base:x}, not L 0x{STAGING:x}")
        if fdt is not None and shim_fdt != fdt:
            findings.append(f"shim fdt 0x{shim_fdt:x} != the handoff's "
                            f"0x{fdt:x}")
        if dest != DEST:
            findings.append(f"shim destination 0x{dest:x} != 0x{DEST:x}")
        if size != BYTES:
            findings.append(f"shim copied 0x{size:x} bytes, not "
                            f"0x{BYTES:x}")
        if handoff is None or index <= handoff:
            findings.append("the SHIM line does not follow the handoff")
        if marker_index is not None and marker_index < index:
            findings.append("a B7 marker precedes the SHIM line")
    evidence["shim_ok"] = len(findings) == before
    _, marker_findings = b7.evaluate(text, pins=pins)
    findings += [f"B7: {finding}" for finding in marker_findings]
    return not findings, findings, evidence, markers


def result_record(capture, ok, findings, evidence, markers, toolchain=None,
                  pins=None):
    record = b7.result_record(capture, "pass", markers, ok, findings,
                              toolchain, pins)
    record["boot_marker"] = "PASS" if evidence.get("handoff_ok") and \
        evidence.get("shim_ok") and \
        b7.full_sequence_reached(markers, pins) else "FAIL"
    fields = record["fields"]
    for key in ("kexec_entry", "kexec_hart", "kexec_fdt"):
        if key in evidence:
            fields[key] = evidence[key]
    for line in evidence.get("b3_lines", ()):
        if line.startswith("BE_K3_B3: FAIL") and "failure" not in fields:
            fields["failure"] = line[len(B3_TAG):]
    record["handoff"] = evidence
    return record


# Synthetic inputs: the self-test's and --write-fixtures' boot image,
# around a stand-in monitor and kernel of the fixture pins' sizes.
FIXTURE_PINS = b7.FIXTURE_PINS
FIXTURE_PAYLOAD = bytes(range(256)) * (BYTES // 256)


def synthetic_kernel(pins=FIXTURE_PINS):
    """A stand-in RISC-V Image of the pinned size, image_size, and banner."""
    header = struct.pack("<IIQQQIIQ8s4sI", 0x0000006F | (0x40 << 20), 0,
                         LAYOUT["KERNEL_TEXT_OFFSET"], pins.image_size, 0, 2,
                         0, 0, b"RISCV\0\0\0", b"RSC\x05", 0)
    body = header + pins.banner.encode("ascii") + b"\n\0"
    return body + bytes(pins.kernel_bytes - len(body))


def synthetic_dtb(guest):
    """A stand-in 4 KiB DTB; the guests' differ in one padding byte, as
    the real pair differs in its bootargs."""
    blob = struct.pack(">10I", FDT_MAGIC, LAYOUT["DTB_BYTES"], 0x38, 0x48,
                       0x28, 17, 16, 0, 0, 0x10)
    blob += bytes(16) + struct.pack(">4I", 1, 0, 2, 9) + bytes([0x30 + guest])
    return blob + bytes(LAYOUT["DTB_BYTES"] - len(blob))


def synthetic_image(text_offset=None, payload=FIXTURE_PAYLOAD,
                    pins=FIXTURE_PINS):
    """A well-formed B7 boot image: B3's stub page and payload, the kernel,
    and G0's and G1's DTBs, with image_size covering the whole file."""
    if text_offset is None:
        text_offset = LAYOUT["UBOOT_TEXT_OFFSET"]
    image = b3image.synthetic(text_offset, payload)
    image += synthetic_kernel(pins)
    image += bytes(-len(image) % LAYOUT["PAYLOAD_ALIGN"]) + \
        synthetic_dtb(0) + synthetic_dtb(1)
    struct.pack_into("<Q", image, 16, len(image))
    return bytes(image)


def facts_of(data):
    _, _, text_offset, image_size = HEADER.unpack_from(data)
    return {"path": "x", "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "crc32": f"{zlib.crc32(data):08x}",
            "text_offset": text_offset, "image_size": image_size}


def shim_text(fdt, base=STAGING, hart=0):
    return (f"BE_K3_B3: SHIM hart=0x{hart:016x} shim=0x{base:016x} "
            f"fdt=0x{fdt:016x} dest=0x{DEST:016x} bytes=0x{BYTES:016x}")


# Fedora's shutdown before a kexec (systemd colour codes included).
FEDORA_NOISE = (
    "\x1b[0;1;39m         Stopping\x1b[0m session-3.scope - Session 3 of "
    "User fedora...",
    "[\x1b[0;32m  OK  \x1b[0m] Stopped target \x1b[0;1;39mmulti-user.target"
    "\x1b[0m - Multi-User System.",
    "[  OK  ] Finished systemd-kexec.service - Reboot via kexec.",
    "[  OK  ] Reached target kexec.target - Reboot via kexec.",
    "[ 4206.214011] watchdog: watchdog0: watchdog did not stop!",
    "[ 4206.511219] systemd-shutdown[1]: Syncing filesystems and block "
    "devices.",
    "[ 4207.902114] systemd-shutdown[1]: Rebooting with kexec.",
    "[ 4208.871002] reboot: Restarting system",
)


def kexec_capture(image_bytes, fdt=None, shim=None, markers=None,
                  handoff=None, extra_after="", harts=8):
    """A synthetic COM260-style kexec capture (Fedora's log, CRLF)."""
    fdt = kexec_fdt_for(image_bytes) if fdt is None else fdt
    if shim is None:
        shim = shim_text(fdt)
    if markers is None:
        markers = b7.pass_lines()[1:]
    if handoff is None:
        handoff = (["[ 4208.994539] kexec_core: Starting new kernel"] +
                   [f"[ 4209.0{index}2886] CPU{index}: off"
                    for index in range(1, harts)] +
                   [f"[ 4209.068232] Will call new kernel at {STAGING:08x} "
                    f"from hart id 0",
                    f"[ 4209.071298] FDT image at {fdt:08x}",
                    "[ 4209.074905] Bye..."])
    lines = list(FEDORA_NOISE) + handoff
    if shim:
        lines.append(shim)
    lines += list(markers)
    return "\r\n".join(lines) + "\r\n" + extra_after


def write_fixtures(directory, pins_path=b7.DEFAULT_PINS):
    """The dry run's synthetic inputs, written under DIRECTORY: a board
    image and flat monitor image, and a passing COM260 kexec capture for
    them, with the guest pins (by default guest/pins.txt, so the board
    tools check them as a board run would)."""
    out = pathlib.Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    pins = b7.read_pins(pins_path)
    image = synthetic_image(pins=pins)
    markers = b7.pass_lines(pins)[1:]
    files = {
        "be-k3-b7.bin": FIXTURE_PAYLOAD,
        "be-k3-b7-boot.img": image,
        "kexec.console.log": kexec_capture(
            len(image), markers=markers).encode("ascii"),
    }
    for name, data in files.items():
        (out / name).write_bytes(data)
    print(f"BE_B7_CAPTURE_FIXTURES: {out} image_bytes={len(image)} "
          f"kexec_fdt=0x{kexec_fdt_for(len(image)):x} pins={pins_path}")
    return 0


def capture_cases():
    """(name, text, options, wanted) for the capture self-test."""
    image = synthetic_image()
    board = facts_of(image)
    size = len(image)
    lines = b7.pass_lines()[1:]
    pins = {"pins": FIXTURE_PINS}
    with_image = dict(pins, image=board)
    kexec = kexec_capture(size)
    fdt = kexec_fdt_for(size)
    parts = kexec.split("\r\n")
    call = next(index for index, line in enumerate(parts)
                if "Will call" in line)
    g1 = [index for index, line in enumerate(lines)
          if line.startswith(b7.GUEST_PREFIXES[1])]
    noise = b7.GUEST_PREFIXES[0] + "[    0.900000] "
    cases = [
        ("Fedora kexec pass", kexec, pins, True),
        ("Fedora kexec pass, LF only", kexec.replace("\r", ""), pins, True),
        ("Fedora kexec pass with the image", kexec, with_image, True),
        ("Fedora kexec pass with the loader's FDT", kexec,
         dict(pins, kexec_fdt=fdt), True),
        ("QEMU kexec pass, one hart, LF only", kexec_capture(
            size, harts=1).replace("\r", ""), with_image, True),
        ("missing SHIM line", kexec_capture(size, shim=""), pins, False),
        ("shim not at L", kexec_capture(size, shim=shim_text(
            fdt, base=STAGING + 0x1000)), pins, False),
        ("shim on hart 1", kexec_capture(size, shim=shim_text(
            fdt, hart=1)), pins, False),
        ("shim destination", kexec.replace(f"dest=0x{DEST:016x}",
                                           f"dest=0x{DEST + 0x200000:016x}"),
         pins, False),
        ("shim byte count", kexec.replace(f"bytes=0x{BYTES:016x}",
                                          f"bytes=0x{BYTES - 0x1000:016x}"),
         pins, False),
        ("failure marker", kexec_capture(
            size, extra_after="BE_B7:FAIL resume\r\n"), pins, False),
        ("overlap refusal", kexec_capture(
            size, shim=f"BE_K3_B3: FAIL overlap shim=0x{STAGING:016x}",
            markers=()), pins, False),
        ("extra SHIM line", kexec_capture(
            size, extra_after=shim_text(fdt) + "\r\n"), pins, False),
        ("markers truncated", kexec_capture(size, markers=lines[:-1]), pins,
         False),
        ("marker before SHIM", kexec_capture(size, shim="", markers=[
            lines[0], shim_text(fdt)] + lines[1:]), pins, False),
        ("FDT not the loader's", kexec, dict(pins, kexec_fdt=fdt + 0x200000),
         False),
        ("FDT not after the image", kexec_capture(
            size, fdt=fdt + 0x200000), with_image, False),
        ("FDT unaligned", kexec_capture(size, fdt=fdt + 0x1000), pins,
         False),
        ("FDT past the largest image", kexec_capture(
            size, fdt=STAGING + LAYOUT["BOOT_IMAGE_MAX"] +
            LAYOUT["KEXEC_FDT_ALIGN"]), pins, False),
        ("kexec entry elsewhere", kexec.replace(
            f"new kernel at {STAGING:08x}", f"new kernel at {DEST:08x}"),
         pins, False),
        ("kexec from hart 1", kexec.replace("hart id 0", "hart id 1"),
         pins, False),
        ("no 'Starting new kernel'", kexec.replace(
            "kexec_core: Starting new kernel", "kexec_core: x"), pins,
         False),
        ("no 'Bye...'", kexec.replace("Bye...", "Bye"), pins, False),
        ("two 'Bye...' lines", kexec.replace("Bye...", "Bye...\r\nBye..."),
         pins, False),
        ("handoff out of order", "\r\n".join(
            parts[:call] + [parts[call + 1], parts[call]] +
            parts[call + 2:]), pins, False),
        ("SHIM before 'Bye...'", "\r\n".join(
            parts[:call + 2] + [parts[call + 3], parts[call + 2]] +
            parts[call + 4:]), pins, False),
        ("shim fdt not the kexec FDT", kexec_capture(
            size, shim=shim_text(fdt + 0x200000)), pins, False),
        ("a G1 line without its prefix", kexec_capture(
            size, markers=lines[:g1[3]] + [lines[g1[3]][len(
                b7.GUEST_PREFIXES[1]):]] + lines[g1[3] + 1:]), pins, False),
        ("a G1 required line with G0's prefix", kexec_capture(
            size, markers=lines[:g1[3]] + [b7.GUEST_PREFIXES[0] + lines[
                g1[3]][len(b7.GUEST_PREFIXES[1]):]] + lines[g1[3] + 1:]),
         pins, False),
        ("G1's START with G0's prefix", kexec_capture(
            size, markers=[b7.GUEST_PREFIXES[0] + line[len(
                b7.GUEST_PREFIXES[1]):] if line.startswith(
                b7.GUEST_PREFIXES[1] + "B7INIT 01 ") else line
                for line in lines]), pins, False),
        ("B7 noise among the markers", kexec_capture(
            size, markers=lines[:12] + ["fail to get alias node"] +
            lines[12:]), pins, False),
        ("guest Linux noise", kexec_capture(
            size, markers=lines[:30] + [noise + "workingset: timestamp_"
                                        "bits=62"] + lines[30:]),
         pins, True),
        ("a U-Boot booti capture", "\r\n".join(
            ["=> loady 0x140000000 && booti 0x140000000 - ${fdtcontroladdr}",
             f"Moving Image from 0x140000000 to 0x{STAGING:x}, end="
             f"{STAGING + size:x}", "Starting kernel ...",
             shim_text(0x2f7659000)] + lines) + "\r\n", pins, False),
        ("without pins", kexec, {}, False),
    ]
    for pattern in b7.REJECTED:
        cases.append((f"rejected {pattern!r} in a guest line",
                      kexec_capture(size, markers=lines[:30] + [
                          noise + pattern] + lines[30:]), pins, False))
    # The realistic fixture's monitor and Linux lines behind the handoff.
    realistic = b7.REALISTIC.read_bytes().decode("ascii")
    real_pins = {"pins": b7.realistic_pins(realistic)}
    real_markers = [line for line in b7.extract(realistic)
                    if not line.startswith(B3_TAG)]
    cases += [
        ("realistic Linux logs after the kexec handoff", kexec_capture(
            size, markers=real_markers), real_pins, True),
        ("realistic Linux logs, fixture pins", kexec_capture(
            size, markers=real_markers), pins, False),
    ]
    return image, kexec, cases


def image_cases(image):
    """(name, data, payload, options, wanted) for --check-image."""

    def mutate(offset, value):
        data = bytearray(image)
        data[offset:offset + len(value)] = value
        return bytes(data)

    kernel = LAYOUT["BOOT_KERNEL_OFFSET"]
    dtb_bytes = LAYOUT["DTB_BYTES"]
    g0_dtb = len(image) - 2 * dtb_bytes
    g1_dtb = len(image) - dtb_bytes
    pins = {"pins": FIXTURE_PINS}
    large = synthetic_image(pins=FIXTURE_PINS._replace(
        kernel_bytes=LAYOUT["BOOT_IMAGE_MAX"] - kernel))
    return [
        ("board image", image, FIXTURE_PAYLOAD, pins, True),
        ("board image without the flat image", image, None, {}, True),
        ("another monitor", image, bytes(BYTES), {}, False),
        ("flat image short", image, FIXTURE_PAYLOAD[:-8], {}, False),
        ("QEMU's k3-address text_offset", synthetic_image(
            LAYOUT["UBOOT_TEXT_OFFSET"] + LAYOUT["UBOOT_RAM_BASE"] -
            0x80000000), FIXTURE_PAYLOAD, {}, False),
        ("B5's text_offset", synthetic_image(0x200000), FIXTURE_PAYLOAD, {},
         False),
        ("larger than the boot image limit", large, FIXTURE_PAYLOAD, {},
         False),
        ("image_size not the file", mutate(16, struct.pack(
            "<Q", len(image) - 0x1000)), FIXTURE_PAYLOAD, {}, False),
        ("file not a 4 KiB multiple", image + b"\0" * 8, FIXTURE_PAYLOAD,
         {}, False),
        ("kernel magic2", mutate(kernel + IMAGE_MAGIC2_OFFSET, b"RSC\x04"),
         FIXTURE_PAYLOAD, {}, False),
        ("kernel text_offset", mutate(kernel + 8, struct.pack(
            "<Q", 0x400000)), FIXTURE_PAYLOAD, {}, False),
        ("kernel image_size not the pin", mutate(kernel + 16, struct.pack(
            "<Q", FIXTURE_PINS.image_size + 0x1000)), FIXTURE_PAYLOAD, pins,
         False),
        ("kernel size not the pin", image, FIXTURE_PAYLOAD, {
            "pins": FIXTURE_PINS._replace(kernel_bytes=FIXTURE_PINS
                                          .kernel_bytes + 0x1000)}, False),
        ("G0's DTB magic", mutate(g0_dtb, b"\xd0\x0d\xfe\xee"),
         FIXTURE_PAYLOAD, {}, False),
        ("G1's DTB magic", mutate(g1_dtb, b"\xd0\x0d\xfe\xee"),
         FIXTURE_PAYLOAD, {}, False),
        ("G1's DTB larger", mutate(g1_dtb + 4, struct.pack(">I", 0x2000)),
         FIXTURE_PAYLOAD, {}, False),
        ("the DTBs the same bytes", image[:g1_dtb] + image[g0_dtb:g1_dtb],
         FIXTURE_PAYLOAD, {}, False),
        ("one DTB only", image[:g1_dtb], FIXTURE_PAYLOAD, pins, False),
        ("descriptor destination", mutate(0x48, struct.pack(
            "<Q", 0x102200000)), FIXTURE_PAYLOAD, {}, False),
        ("template damaged", mutate(0x80 + 5, b"X"), FIXTURE_PAYLOAD, {},
         False),
    ]


def self_test():
    image, kexec, cases = capture_cases()
    failed = 0
    for name, text, options, wanted in cases:
        ok, findings, _, _ = evaluate(text, "kexec", **options)
        failed += ok != wanted
        print(f"{'ok  ' if ok == wanted else 'FAIL'} {name}: ok={ok} "
              f"findings={findings[:3]}")
    ok, findings, _, _ = evaluate(kexec, "uboot", pins=FIXTURE_PINS)
    failed += ok
    print(f"{'ok  ' if not ok else 'FAIL'} U-Boot mode refused: ok={ok} "
          f"findings={findings[:1]}")
    lines = b7.pass_lines()[1:]
    size = len(image)
    records = [
        ("record kexec pass", kexec, "PASS", "PASS", "shutdown-requested"),
        ("record failure marker", kexec_capture(
            size, extra_after="BE_B7:FAIL resume\r\n"), "FAIL", "FAIL",
         "fail-marker"),
        ("record missing SHIM", kexec_capture(size, shim=""), "FAIL",
         "FAIL", "shutdown-requested"),
        ("record no handoff", kexec_capture(size, handoff=[]), "FAIL",
         "FAIL", "shutdown-requested"),
        ("record truncated", kexec_capture(size, markers=lines[:5]), "FAIL",
         "FAIL", "none"),
    ]
    for name, text, result, boot, end in records:
        ok, findings, evidence, markers = evaluate(text, "kexec",
                                                   pins=FIXTURE_PINS)
        record = result_record("x", ok, findings, evidence, markers, "gcc",
                               FIXTURE_PINS)
        got = (record["result"], record["boot_marker"], record["terminal"])
        wanted = (result, boot, end)
        failed += got != wanted
        print(f"{'ok  ' if got == wanted else 'FAIL'} {name}: "
              f"result/boot_marker/terminal={got}")
    ok, findings, evidence, markers = evaluate(kexec, "kexec",
                                               pins=FIXTURE_PINS)
    fields = result_record("x", ok, findings, evidence, markers, "gcc",
                           FIXTURE_PINS)["fields"]
    wanted_fields = {"hart": "0x" + "0" * 16,
                     "base": f"0x{STAGING:016x}",
                     "fdt": f"0x{kexec_fdt_for(size):016x}",
                     "kexec_entry": f"0x{STAGING:x}",
                     "kexec_fdt": f"0x{kexec_fdt_for(size):x}",
                     "exits_g0": "503", "exits_g1": "495"}
    for key, value in wanted_fields.items():
        if fields.get(key) != value:
            print(f"FAIL field {key}: {fields.get(key)!r}")
            failed += 1
    if not all(isinstance(value, str) for value in fields.values()):
        print(f"FAIL record fields {fields}")
        failed += 1
    images = image_cases(image)
    for name, data, payload, options, wanted in images:
        image_findings, _ = boot_image_findings(data, payload, **options)
        ok = not image_findings
        failed += ok != wanted
        print(f"{'ok  ' if ok == wanted else 'FAIL'} image {name}: ok={ok} "
              f"findings={image_findings[:3]}")
    placements = [
        ("COM260 L", size, LAYOUT["UBOOT_TEXT_OFFSET"], True),
        ("B5's shim address", size, 0x200000, False),
        ("the largest image", LAYOUT["BOOT_IMAGE_MAX"],
         LAYOUT["UBOOT_TEXT_OFFSET"], True),
    ]
    for name, image_bytes, text_offset, wanted in placements:
        ok = not placement_findings(image_bytes, text_offset)
        failed += ok != wanted
        print(f"{'ok  ' if ok == wanted else 'FAIL'} placement {name}: "
              f"ok={ok}")
    total = len(cases) + 1 + len(records) + len(images) + len(placements) + 1
    print(f"BE_B7_CAPTURE_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
          f"cases={total} failed={failed}")
    return 0 if not failed else 1


def number(value):
    return int(value, 0)


def check_image(spec, pins):
    """--check-image TOOLCHAIN:IMG[:BIN]: a boot image before a run."""
    toolchain, _, rest = spec.partition(":")
    path, _, flat = rest.partition(":")
    data = pathlib.Path(path).read_bytes()
    payload = pathlib.Path(flat).read_bytes() if flat else None
    findings, facts = boot_image_findings(data, payload, pins)
    if toolchain not in ("gcc", "clang"):
        findings.append(f"unknown toolchain {toolchain!r}")
    for finding in findings:
        print(f"finding[{toolchain}]: {finding}")
    print(f"BE_B7_BOOT_IMAGE[{toolchain}]: "
          f"{'PASS' if not findings else 'FAIL'} {path} "
          f"bytes=0x{facts['bytes']:x} sha256={facts['sha256']} "
          f"crc32={facts['crc32']} payload_sha256={facts['payload_sha256']} "
          f"kexec_fdt=0x{facts['kexec_fdt']:x}")
    return 0 if not findings else 1


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("capture", nargs="?")
    parser.add_argument("--mode", choices=("kexec",))
    parser.add_argument("--image")
    parser.add_argument("--kexec-fdt", type=number)
    parser.add_argument("--pins")
    parser.add_argument("--kernel-bytes", type=number)
    parser.add_argument("--image-size", type=number)
    parser.add_argument("--banner")
    parser.add_argument("--toolchain", choices=("gcc", "clang"))
    parser.add_argument("--json")
    parser.add_argument("--check-image", metavar="TOOLCHAIN:IMG[:BIN]")
    parser.add_argument("--write-fixtures", metavar="DIR")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.write_fixtures:
        return write_fixtures(args.write_fixtures,
                              args.pins or b7.DEFAULT_PINS)
    try:
        pins = b7.options_pins(args, parser)
    except (OSError, ValueError) as error:
        parser.error(f"pins: {error}")
    if args.check_image:
        return check_image(args.check_image, pins)
    if args.capture is None or args.mode is None:
        parser.error("a capture file and --mode kexec are required")
    image = image_facts(args.image) if args.image else None
    with open(args.capture, "rb") as handle:
        text = handle.read().decode("utf-8", errors="replace")
    ok, findings, evidence, markers = evaluate(
        text, args.mode, image, args.kexec_fdt, pins)
    record = result_record(args.capture, ok, findings, evidence, markers,
                           args.toolchain, pins)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
    for key in ("kexec_entry", "kexec_hart", "kexec_fdt"):
        if key in evidence:
            print(f"{key}={evidence[key]}")
    for line in evidence.get("b3_lines", ()):
        print(line)
    for line in markers:
        if not line.startswith(B3_TAG):
            print(line)
    for finding in findings:
        print(f"finding: {finding}")
    report = b7.counts_report(markers)
    if report:
        print(report)
    print(f"BE_B7_RESULT: {record['boot_marker']} "
          f"terminal={record['terminal']}")
    print(f"BE_B7_CAPTURE[{args.mode}]: {record['result']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
