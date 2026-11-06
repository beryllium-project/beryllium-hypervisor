#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Render the K3 B7 guest device tree sources (planning/k3-b7-plan.md, Guest
software, Q7) from guest/b7-guest.dts.in and the constants of
src/b7-layout.h, so that no DTB can drift from the monitor's guest window.

  gen-dts.py --layout H --template T [--guest G] [--variant V] [--output DTS]
  gen-dts.py --layout H --template T --self-test [--plan P] [--b6-plan P]
  gen-dts.py --layout H --query NAME

Every value comes from a `#define BE_B7_<NAME> BE_B7_C(<literal>)` line of the
layout header: the window (BE_B7_GUEST_GPA, BE_B7_GUEST_BYTES), the timebase
(BE_B7_TIMEBASE_HZ), the DTB size for dtc -S (BE_B7_DTB_BYTES), the guest
count (BE_B7_GUESTS), and, for the reference boot, the kernel's GPA and the
2 MiB leaf. Each guest window has the same guest-physical layout, so G0's and
G1's DTBs differ only in bootargs: B6's bootargs, then `-- be.guest=<g>`,
which Linux hands to /init as an argument.

Variants of one guest's DTB, each exactly one change from that guest's
`base` (all but `base` are QEMU-only test inputs):
  base       the guest's DTB, for QEMU and the board
  init-exit  " rdinit=/init-exit" before the "--"
  rdcycle    " rdinit=/init-rdcycle" before the "--"
  sbi-time   "sstc" leaves riscv,isa-extensions
  reference  the memory node starts at the kernel's GPA, 0x8020_0000, past
             QEMU's OpenSBI at 0x8000_0000, for the reference boot under
             plain OpenSBI

DTBS names the DTBs that scripts/build-guest.sh makes: both guests' base,
sbi-time, and reference DTBs, G1's init-exit, and G0's rdcycle, as the
plan's QEMU scenarios use them.

Queries (for guest.mk, build-guest.sh, and the reference boot): dtb-bytes
(decimal); dtbs (one `NAME GUEST VARIANT` line per DTB); and
reference-kernel, reference-dtb, and reference-size (hexadecimal): the
reference boot loads the kernel at the start of the reference memory node,
which is the window's size, and the DTB at the start of its last 2 MiB, as
B7 places each DTB in its window.

--self-test renders every DTB and requires each variant to differ from its
guest's `base` in exactly its one change, and G0's base to differ from G1's
in the guest digit alone. Each base DTS must match, token for token, the DTS
block of the accepted B6 plan (--b6-plan, default planning/k3-b6-plan.md)
with the B7 model, compatible, and bootargs, which the accepted B7 plan
(--plan, default planning/k3-b7-plan.md) must state. It also ties
guest/b7-guest-id.h to BE_B7_GUESTS and checks the layout parser and the
renderer's refusals.
"""

import argparse
import pathlib
import re
import string
import sys

BOOTARGS = "earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1"
GUEST_ARG = "be.guest="
MODEL = "Beryllium K3 B7 guest"
COMPATIBLE = "beryllium,k3-b7-guest"
B6_MODEL = "Beryllium K3 B6 guest"
B6_COMPATIBLE = "beryllium,k3-b6-guest"
ISA_EXTENSIONS = ("i", "m", "a", "c", "zicsr", "zifencei", "zihintpause",
                  "zba", "zbb", "zbs", "sstc", "svade")
VARIANTS = ("base", "init-exit", "rdcycle", "sbi-time", "reference")
DTBS = (
    ("b7-guest-g0.dtb", 0, "base"),
    ("b7-guest-g1.dtb", 1, "base"),
    ("b7-guest-g1-init-exit.dtb", 1, "init-exit"),
    ("b7-guest-g0-rdcycle.dtb", 0, "rdcycle"),
    ("b7-guest-g0-sbi-time.dtb", 0, "sbi-time"),
    ("b7-guest-g1-sbi-time.dtb", 1, "sbi-time"),
    ("b7-guest-g0-reference.dtb", 0, "reference"),
    ("b7-guest-g1-reference.dtb", 1, "reference"),
)
REQUIRED = ("GUESTS", "GUEST_GPA", "GUEST_BYTES", "TIMEBASE_HZ", "DTB_BYTES",
            "KERNEL_GPA", "KERNEL_TEXT_OFFSET", "GUEST_LEAF_BYTES")
DEFINE = re.compile(r"^#define\s+BE_B7_([A-Z0-9_]+)\s+"
                    r"BE_B7_C\(\s*(0x[0-9a-fA-F]+|[0-9]+)\s*\)\s*$")
GUEST_IDS = re.compile(r"^#define\s+B7_GUEST_IDS\s+([0-9]+)\s*$", re.M)
U32 = 0xffffffff
U64 = 0xffffffffffffffff


class LayoutError(Exception):
    """The layout header lacks a value or holds an inconsistent one."""


def parse_layout(text):
    """Return {NAME: value} for every BE_B7_C() define, checked."""
    layout = {}
    for line in text.splitlines():
        match = DEFINE.match(line)
        if not match:
            continue
        name, literal = match.groups()
        if name in layout:
            raise LayoutError(f"BE_B7_{name} is defined twice")
        layout[name] = int(literal, 0)
    for name in REQUIRED:
        if name not in layout:
            raise LayoutError(f"BE_B7_{name} is missing")
        if not 0 < layout[name] <= U64:
            raise LayoutError(f"BE_B7_{name} is out of range")
    if layout["GUESTS"] != 2:
        raise LayoutError("BE_B7_GUESTS is not 2 (G0 and G1)")
    leaf = layout["GUEST_LEAF_BYTES"]
    if layout["GUEST_GPA"] + layout["KERNEL_TEXT_OFFSET"] != layout["KERNEL_GPA"]:
        raise LayoutError("BE_B7_KERNEL_GPA is not the window plus text_offset")
    for name in ("GUEST_GPA", "GUEST_BYTES", "KERNEL_GPA"):
        if layout[name] % leaf:
            raise LayoutError(f"BE_B7_{name} is not 2 MiB aligned")
    if layout["GUEST_BYTES"] <= layout["KERNEL_TEXT_OFFSET"] + leaf:
        raise LayoutError("BE_B7_GUEST_BYTES leaves no room for the kernel")
    if layout["TIMEBASE_HZ"] > U32 or layout["DTB_BYTES"] % 8:
        raise LayoutError("BE_B7_TIMEBASE_HZ or BE_B7_DTB_BYTES is unusable")
    return layout


def reference_memory(layout):
    """The reference node: the window's size, starting at the kernel."""
    return layout["KERNEL_GPA"], layout["GUEST_BYTES"]


def query(layout, name):
    base, size = reference_memory(layout)
    if name == "dtb-bytes":
        return str(layout["DTB_BYTES"])
    if name == "dtbs":
        return "\n".join(f"{dtb} {guest} {variant}"
                         for dtb, guest, variant in DTBS)
    if name == "reference-kernel":
        return f"{base:#x}"
    if name == "reference-dtb":
        return f"{base + size - layout['GUEST_LEAF_BYTES']:#x}"
    if name == "reference-size":
        return f"{size:#x}"
    raise ValueError(f"unknown query {name!r}")


def guest_bootargs(guest, extra=""):
    """B6's bootargs, any option for the kernel, then init's argument."""
    return f"{BOOTARGS}{extra} -- {GUEST_ARG}{guest}"


def values(layout, guest, variant):
    """The template values of one guest's variant: its base plus one change."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}")
    if guest not in range(layout["GUESTS"]):
        raise ValueError(f"unknown guest {guest!r}")
    bootargs = guest_bootargs(guest)
    isa = list(ISA_EXTENSIONS)
    base, size = layout["GUEST_GPA"], layout["GUEST_BYTES"]
    if variant == "init-exit":
        bootargs = guest_bootargs(guest, " rdinit=/init-exit")
    elif variant == "rdcycle":
        bootargs = guest_bootargs(guest, " rdinit=/init-rdcycle")
    elif variant == "sbi-time":
        isa.remove("sstc")
    elif variant == "reference":
        base, size = reference_memory(layout)
    if base + size > U64 + 1:
        raise ValueError("the memory node wraps")
    return {
        "BOOTARGS": bootargs,
        "TIMEBASE_HZ": str(layout["TIMEBASE_HZ"]),
        "ISA_EXTENSIONS": ", ".join(f'"{name}"' for name in isa),
        "MEMORY_UNIT": f"{base:x}",
        "MEMORY_REG": (f"{base >> 32:#x} {base & U32:#x} "
                       f"{size >> 32:#x} {size & U32:#x}"),
    }


def render(template, layout, guest, variant):
    """The DTS text; every ${NAME} must be known, and every value used."""
    filled = values(layout, guest, variant)
    names = {match.group("named") or match.group("braced")
             for match in string.Template.pattern.finditer(template)
             if match.group("named") or match.group("braced")}
    if names != set(filled):
        raise ValueError("template placeholders "
                         f"{sorted(names)} differ from {sorted(filled)}")
    return string.Template(template).substitute(filled)


# ------------------------------------------------------------- self-test
TOKEN = re.compile(r'"[^"]*"|[<>{};,=]|[^\s<>{};,="]+')


def dts_tokens(text):
    """DTS tokens without comments, the /dts-v1/ tag, or layout."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    text = text.replace("/dts-v1/;", " ")
    return TOKEN.findall(text)


def plan_dts(plan_text):
    blocks = re.findall(r"^```dts\n(.*?)^```", plan_text, flags=re.S | re.M)
    if len(blocks) != 1:
        raise ValueError(f"the plan has {len(blocks)} dts blocks, not 1")
    return blocks[0]


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"{old!r} occurs {text.count(old)} times, not once")
    return text.replace(old, new)


def b7_plan_dts(b6_plan_text, guest):
    """B6's accepted DTS with the B7 model, compatible, and bootargs."""
    text = plan_dts(b6_plan_text)
    text = replace_once(text, f'"{B6_COMPATIBLE}"', f'"{COMPATIBLE}"')
    text = replace_once(text, f'"{B6_MODEL}"', f'"{MODEL}"')
    return replace_once(text, f'"{BOOTARGS}"', f'"{guest_bootargs(guest)}"')


def changed_lines(base, other):
    left, right = base.splitlines(), other.splitlines()
    if len(left) != len(right):
        return None
    return [(a, b) for a, b in zip(left, right) if a != b]


def self_test(template, layout_text, plan_text, b6_plan_text, id_header):
    failures = []
    cases = 0

    def expect(condition, message):
        nonlocal cases
        cases += 1
        if not condition:
            failures.append(message)

    layout = parse_layout(layout_text)
    for statement in (f"`{guest_bootargs('<g>')}`",
                      f'DT model "{MODEL}" and compatible "{COMPATIBLE}"'):
        expect(statement in plan_text, f"the B7 plan lacks {statement}")
    ids = GUEST_IDS.findall(id_header)
    expect(ids == [str(layout["GUESTS"])],
           f"b7-guest-id.h B7_GUEST_IDS {ids} is not BE_B7_GUESTS")

    bases = {}
    for guest in range(layout["GUESTS"]):
        base = bases[guest] = render(template, layout, guest, "base")
        expect(dts_tokens(base) == dts_tokens(b7_plan_dts(b6_plan_text,
                                                          guest)),
               f"G{guest}: the base DTS differs from B6's with the B7 names")
        window = (f"<{layout['GUEST_GPA'] >> 32:#x} "
                  f"{layout['GUEST_GPA'] & U32:#x}")
        expect(window in base, f"G{guest}: the base memory node is not "
               "the window")
    changes = changed_lines(bases[0], bases[1])
    expect(changes is not None and len(changes) == 1 and
           [a.replace(f"{GUEST_ARG}0", f"{GUEST_ARG}1") for a, _ in changes]
           == [b for _, b in changes] and "bootargs" in changes[0][0],
           f"G0 and G1 differ beyond the guest digit: {changes!r}")

    ref_base, ref_size = reference_memory(layout)
    one_change = {
        "init-exit": [("bootargs", '"' + guest_bootargs(
            "{g}", " rdinit=/init-exit") + '";')],
        "rdcycle": [("bootargs", '"' + guest_bootargs(
            "{g}", " rdinit=/init-rdcycle") + '";')],
        "sbi-time": [("riscv,isa-extensions", '"zbs", "svade";')],
        "reference": [("memory@", f"memory@{ref_base:x} {{"),
                      ("reg", f"{ref_base & U32:#x} {ref_size >> 32:#x} "
                       f"{ref_size & U32:#x}>;")],
    }
    names = [name for name, _, _ in DTBS]
    expect(len(set(names)) == len(names), "DTBS repeats a name")
    for guest in range(layout["GUESTS"]):
        for variant in ("base", "sbi-time", "reference"):
            expect((guest, variant) in [(g, v) for _, g, v in DTBS],
                   f"DTBS lacks G{guest}'s {variant} DTB")
    for name, guest, variant in DTBS:
        expect(name == f"b7-guest-g{guest}" +
               ("" if variant == "base" else f"-{variant}") + ".dtb",
               f"{name} is not named for G{guest}'s {variant}")
        if variant == "base":
            continue
        rendered = render(template, layout, guest, variant)
        expected = [(key, ending.replace("{g}", str(guest)))
                    for key, ending in one_change[variant]]
        changes = changed_lines(bases[guest], rendered)
        expect(changes is not None and len(changes) == len(expected),
               f"{name}: {changes!r} is not exactly its one change")
        for (old, new), (key, ending) in zip(changes or [], expected):
            expect(key in old and key in new and new.rstrip().endswith(ending),
                   f"{name}: {new.strip()!r} does not end {ending!r}")
        if variant == "sbi-time":
            expect('"sstc"' in bases[guest] and '"sstc"' not in rendered,
                   f"{name} still names sstc")
        if variant in ("init-exit", "rdcycle"):
            expect(rendered.index("rdinit=") < rendered.index(" -- "),
                   f"{name}: rdinit= is not a kernel option before --")
    dtb = int(query(layout, "reference-dtb"), 16)
    expect(query(layout, "reference-kernel") == f"{ref_base:#x}" and
           query(layout, "reference-size") == f"{ref_size:#x}" and
           ref_size == layout["GUEST_BYTES"] and
           ref_base < dtb < ref_base + ref_size and
           dtb % layout["GUEST_LEAF_BYTES"] == 0,
           "the reference DTB is not 2 MiB aligned inside its node")
    expect("DTB_GPA" in layout and
           dtb - ref_base == layout["DTB_GPA"] - layout["GUEST_GPA"],
           "the reference DTB is not placed as B7 places each DTB")
    expect(query(layout, "dtbs").splitlines() ==
           [f"{name} {guest} {variant}" for name, guest, variant in DTBS],
           "the dtbs query is not DTBS")

    refusals = [
        ("unknown variant", lambda: render(template, layout, 0, "nonesuch")),
        ("removed variant", lambda: render(template, layout, 0, "memory")),
        ("third guest", lambda: render(template, layout, 2, "base")),
        ("negative guest", lambda: render(template, layout, -1, "base")),
        ("unknown query", lambda: query(layout, "nonesuch")),
        ("extra placeholder", lambda: render(template + "${EXTRA}\n",
                                             layout, 0, "base")),
        ("missing placeholder", lambda: render(
            template.replace("${BOOTARGS}", "x"), layout, 0, "base")),
        ("missing constant", lambda: parse_layout(
            re.sub(r"(?m)^#define\s+BE_B7_TIMEBASE_HZ\b.*$", "",
                   layout_text))),
        ("duplicate constant", lambda: parse_layout(
            layout_text + "#define BE_B7_GUEST_GPA BE_B7_C(0x80000000)\n")),
        ("three guests", lambda: parse_layout(re.sub(
            r"(?m)^(#define\s+BE_B7_GUESTS\s+)BE_B7_C\([0-9]+\)",
            r"\1BE_B7_C(3)", layout_text))),
        ("misaligned window", lambda: parse_layout(re.sub(
            r"(?m)^(#define\s+BE_B7_GUEST_BYTES\s+)BE_B7_C\(0x[0-9a-fA-F]+\)",
            r"\1BE_B7_C(0x4001000)", layout_text))),
        ("inconsistent kernel GPA", lambda: parse_layout(re.sub(
            r"(?m)^(#define\s+BE_B7_KERNEL_GPA\s+)BE_B7_C\(0x[0-9a-fA-F]+\)",
            r"\1BE_B7_C(0x80400000)", layout_text))),
        ("B6 DTS without its model", lambda: b7_plan_dts(
            b6_plan_text.replace(B6_MODEL, "x"), 0)),
    ]
    for name, action in refusals:
        try:
            action()
        except (LayoutError, ValueError, KeyError):
            expect(True, name)
        else:
            expect(False, f"{name} was not refused")
    for failure in failures:
        print(f"BE_B7_DTS_SELF_TEST: FAIL {failure}")
    status = "FAIL" if failures else "PASS"
    print(f"BE_B7_DTS_SELF_TEST: {status} cases={cases} dtbs={len(DTBS)} "
          f"variants={len(VARIANTS)}")
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--layout", required=True, type=pathlib.Path)
    parser.add_argument("--template", type=pathlib.Path)
    parser.add_argument("--guest", type=int, default=0)
    parser.add_argument("--variant", default="base", choices=VARIANTS)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--query")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--plan", type=pathlib.Path)
    parser.add_argument("--b6-plan", type=pathlib.Path)
    args = parser.parse_args()
    layout_text = args.layout.read_text(encoding="ascii")
    try:
        layout = parse_layout(layout_text)
        if args.query:
            print(query(layout, args.query))
            return 0
        if args.template is None:
            parser.error("--template is required")
        template = args.template.read_text(encoding="ascii")
        if args.self_test:
            planning = args.layout.resolve().parents[3] / "planning"
            plan = args.plan or planning / "k3-b7-plan.md"
            b6_plan = args.b6_plan or planning / "k3-b6-plan.md"
            id_header = args.template.resolve().parent / "b7-guest-id.h"
            return self_test(template, layout_text,
                             plan.read_text(encoding="utf-8"),
                             b6_plan.read_text(encoding="utf-8"),
                             id_header.read_text(encoding="ascii"))
        text = render(template, layout, args.guest, args.variant)
    except (LayoutError, ValueError) as error:
        print(f"BE_B7_DTS: FAIL {error}", file=sys.stderr)
        return 1
    if args.output:
        args.output.write_text(text, encoding="ascii")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
