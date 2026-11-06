#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Render the K3 B6 guest device tree source (planning/k3-b6-plan.md, Device
tree) from guest/b6-guest.dts.in and the constants of src/b6-layout.h, so that
the DTB cannot drift from the monitor's G-stage window.

  gen-dts.py --layout H --template T [--variant V] [--output DTS]
  gen-dts.py --layout H --template T --self-test [--plan PLAN]
  gen-dts.py --layout H --query NAME

Every value comes from a `#define BE_B6_<NAME> BE_B6_C(<literal>)` line of the
layout header: the window (BE_B6_GUEST_GPA, BE_B6_GUEST_BYTES), the timebase
(BE_B6_TIMEBASE_HZ), the DTB size for dtc -S (BE_B6_DTB_BYTES), and, for the
reference boot, the kernel's GPA and the 2 MiB leaf.

Variants, each exactly one change from `base` (all but `base` are QEMU-only
test inputs):
  base       the B6 guest DTB, for QEMU and the board
  memory     a memory node twice the window (128 MiB on the 64 MiB window)
  init-exit  bootargs gain " rdinit=/init-exit"
  rdcycle    bootargs gain " rdinit=/init-rdcycle"
  sbi-time   "sstc" leaves riscv,isa-extensions
  reference  the memory node starts at the kernel's GPA, 0x8020_0000, past
             QEMU's OpenSBI at 0x8000_0000, for the reference boot under
             plain OpenSBI

Queries (for guest.mk and the reference boot): dtb-bytes (decimal), and
reference-kernel, reference-dtb, and reference-size (hexadecimal): the
reference boot loads the kernel at the start of the reference memory node,
which is the window's size, and the DTB at the start of its last 2 MiB, as
B6 places the DTB in its window.

--self-test renders every variant and requires each to differ from `base` in
exactly its one change, and the base DTS to match, token for token, the DTS
block of the accepted plan (--plan, default planning/k3-b6-plan.md beside
the layout's repository); it also checks the layout parser and the
renderer's refusals.
"""

import argparse
import pathlib
import re
import string
import sys

BOOTARGS = "earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1"
ISA_EXTENSIONS = ("i", "m", "a", "c", "zicsr", "zifencei", "zihintpause",
                  "zba", "zbb", "zbs", "sstc", "svade")
VARIANTS = ("base", "memory", "init-exit", "rdcycle", "sbi-time",
            "reference")
REQUIRED = ("GUEST_GPA", "GUEST_BYTES", "TIMEBASE_HZ", "DTB_BYTES",
            "KERNEL_GPA", "KERNEL_TEXT_OFFSET", "GUEST_LEAF_BYTES")
DEFINE = re.compile(r"^#define\s+BE_B6_([A-Z0-9_]+)\s+"
                    r"BE_B6_C\(\s*(0x[0-9a-fA-F]+|[0-9]+)\s*\)\s*$")
U32 = 0xffffffff
U64 = 0xffffffffffffffff


class LayoutError(Exception):
    """The layout header lacks a value or holds an inconsistent one."""


def parse_layout(text):
    """Return {NAME: value} for every BE_B6_C() define, checked."""
    layout = {}
    for line in text.splitlines():
        match = DEFINE.match(line)
        if not match:
            continue
        name, literal = match.groups()
        if name in layout:
            raise LayoutError(f"BE_B6_{name} is defined twice")
        layout[name] = int(literal, 0)
    for name in REQUIRED:
        if name not in layout:
            raise LayoutError(f"BE_B6_{name} is missing")
        if not 0 < layout[name] <= U64:
            raise LayoutError(f"BE_B6_{name} is out of range")
    leaf = layout["GUEST_LEAF_BYTES"]
    if layout["GUEST_GPA"] + layout["KERNEL_TEXT_OFFSET"] != layout["KERNEL_GPA"]:
        raise LayoutError("BE_B6_KERNEL_GPA is not the window plus text_offset")
    for name in ("GUEST_GPA", "GUEST_BYTES", "KERNEL_GPA"):
        if layout[name] % leaf:
            raise LayoutError(f"BE_B6_{name} is not 2 MiB aligned")
    if layout["GUEST_BYTES"] <= layout["KERNEL_TEXT_OFFSET"] + leaf:
        raise LayoutError("BE_B6_GUEST_BYTES leaves no room for the kernel")
    if layout["TIMEBASE_HZ"] > U32 or layout["DTB_BYTES"] % 8:
        raise LayoutError("BE_B6_TIMEBASE_HZ or BE_B6_DTB_BYTES is unusable")
    return layout


def reference_memory(layout):
    """The reference node: the window's size, starting at the kernel."""
    return layout["KERNEL_GPA"], layout["GUEST_BYTES"]


def query(layout, name):
    base, size = reference_memory(layout)
    if name == "dtb-bytes":
        return str(layout["DTB_BYTES"])
    if name == "reference-kernel":
        return f"{base:#x}"
    if name == "reference-dtb":
        return f"{base + size - layout['GUEST_LEAF_BYTES']:#x}"
    if name == "reference-size":
        return f"{size:#x}"
    raise ValueError(f"unknown query {name!r}")


def values(layout, variant):
    """The template values of one variant: base plus exactly one change."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}")
    bootargs = BOOTARGS
    isa = list(ISA_EXTENSIONS)
    base, size = layout["GUEST_GPA"], layout["GUEST_BYTES"]
    if variant == "memory":
        size *= 2
    elif variant == "init-exit":
        bootargs += " rdinit=/init-exit"
    elif variant == "rdcycle":
        bootargs += " rdinit=/init-rdcycle"
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


def render(template, layout, variant):
    """The DTS text; every ${NAME} must be known, and every value used."""
    filled = values(layout, variant)
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


def changed_lines(base, other):
    left, right = base.splitlines(), other.splitlines()
    if len(left) != len(right):
        return None
    return [(a, b) for a, b in zip(left, right) if a != b]


def self_test(template, layout_text, plan_text):
    failures = []
    cases = 0

    def expect(condition, message):
        nonlocal cases
        cases += 1
        if not condition:
            failures.append(message)

    layout = parse_layout(layout_text)
    base = render(template, layout, "base")
    expect(dts_tokens(base) == dts_tokens(plan_dts(plan_text)),
           "the base DTS differs from the plan's DTS")
    window = f"<{layout['GUEST_GPA'] >> 32:#x} {layout['GUEST_GPA'] & U32:#x}"
    expect(window in base, "the base memory node is not the window")

    ref_base, ref_size = reference_memory(layout)
    one_change = {
        "memory": [("reg", f"{2 * layout['GUEST_BYTES']:#x}>;")],
        "init-exit": [("bootargs", f'"{BOOTARGS} rdinit=/init-exit";')],
        "rdcycle": [("bootargs", f'"{BOOTARGS} rdinit=/init-rdcycle";')],
        "sbi-time": [("riscv,isa-extensions", '"zbs", "svade";')],
        "reference": [("memory@", f"memory@{ref_base:x} {{"),
                      ("reg", f"{ref_base & U32:#x} {ref_size >> 32:#x} "
                       f"{ref_size & U32:#x}>;")],
    }
    for variant, expected in one_change.items():
        rendered = render(template, layout, variant)
        changes = changed_lines(base, rendered)
        expect(changes is not None and len(changes) == len(expected),
               f"{variant}: {changes!r} is not exactly its one change")
        for (old, new), (key, ending) in zip(changes or [], expected):
            expect(key in old and key in new and new.rstrip().endswith(ending),
                   f"{variant}: {new.strip()!r} does not end {ending!r}")
    sbi_time = render(template, layout, "sbi-time")
    expect('"sstc"' in base and '"sstc"' not in sbi_time,
           "sbi-time still names sstc")
    dtb = int(query(layout, "reference-dtb"), 16)
    expect(query(layout, "reference-kernel") == f"{ref_base:#x}" and
           query(layout, "reference-size") == f"{ref_size:#x}" and
           ref_size == layout["GUEST_BYTES"] and
           ref_base < dtb < ref_base + ref_size and
           dtb % layout["GUEST_LEAF_BYTES"] == 0,
           "the reference DTB is not 2 MiB aligned inside its node")
    expect("DTB_GPA" in layout and
           dtb - ref_base == layout["DTB_GPA"] - layout["GUEST_GPA"],
           "the reference DTB is not placed as B6 places its DTB")

    refusals = [
        ("unknown variant", lambda: render(template, layout, "nonesuch")),
        ("unknown query", lambda: query(layout, "nonesuch")),
        ("extra placeholder", lambda: render(template + "${EXTRA}\n",
                                             layout, "base")),
        ("missing placeholder", lambda: render(
            template.replace("${BOOTARGS}", "x"), layout, "base")),
        ("missing constant", lambda: parse_layout(
            re.sub(r"(?m)^#define\s+BE_B6_TIMEBASE_HZ\b.*$", "",
                   layout_text))),
        ("duplicate constant", lambda: parse_layout(
            layout_text + "#define BE_B6_GUEST_GPA BE_B6_C(0x80000000)\n")),
        ("misaligned window", lambda: parse_layout(re.sub(
            r"(?m)^(#define\s+BE_B6_GUEST_BYTES\s+)BE_B6_C\(0x[0-9a-fA-F]+\)",
            r"\1BE_B6_C(0x4001000)", layout_text))),
        ("inconsistent kernel GPA", lambda: parse_layout(re.sub(
            r"(?m)^(#define\s+BE_B6_KERNEL_GPA\s+)BE_B6_C\(0x[0-9a-fA-F]+\)",
            r"\1BE_B6_C(0x80400000)", layout_text))),
    ]
    for name, action in refusals:
        try:
            action()
        except (LayoutError, ValueError, KeyError):
            expect(True, name)
        else:
            expect(False, f"{name} was not refused")
    for failure in failures:
        print(f"BE_B6_DTS_SELF_TEST: FAIL {failure}")
    status = "FAIL" if failures else "PASS"
    print(f"BE_B6_DTS_SELF_TEST: {status} cases={cases} "
          f"variants={len(VARIANTS)}")
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--layout", required=True, type=pathlib.Path)
    parser.add_argument("--template", type=pathlib.Path)
    parser.add_argument("--variant", default="base", choices=VARIANTS)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--query")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--plan", type=pathlib.Path)
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
            plan = args.plan or (args.layout.resolve().parents[3] /
                                 "planning" / "k3-b6-plan.md")
            return self_test(template, layout_text,
                             plan.read_text(encoding="utf-8"))
        text = render(template, layout, args.variant)
    except (LayoutError, ValueError) as error:
        print(f"BE_B6_DTS: FAIL {error}", file=sys.stderr)
        return 1
    if args.output:
        args.output.write_text(text, encoding="ascii")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
