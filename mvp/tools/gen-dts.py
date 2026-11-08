#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Render the MVP guest device tree sources (planning/mvp-m0-plan.md, Guest
software, Q3; B7's scripts/gen-dts.py with MVP names) from
guest/mvp-guest.dts.in and the constants of src/mvp-layout.h, so that no DTB
can drift from the monitor's guest window.

  gen-dts.py --layout H --template T [--guest G] [--variant V] [--output DTS]
  gen-dts.py --layout H --template T --self-test [--plan P] [--b6-plan P]
  gen-dts.py --layout H --query NAME

beryllium-cheri: --guest-flavour linux|cheri-linux (default linux; the
CHERI platform branch's, planning/cheri-platform.md) names the guest
flavour: the CHERI Linux guest's DTBs (tools/build-guest-cheri.sh) also
name CHERI v0.9.3's Zcherihybrid and Zcheripurecap after svade, and its
self-test expects them. That flavour alone also has the variant cap-store,
te-poc's DTB with " rdinit=/init-cap-store" before the "--", G0's, for
te-poc's cap-store image (planning/cheri-enforcement-plan.md, CE-4), the
last of its DTBS and its dtbs query.

Every value comes from a `#define BE_MVP_<NAME> BE_MVP_C(<literal>)` line of
the layout header: the window (BE_MVP_GUEST_GPA, BE_MVP_GUEST_BYTES), the
timebase (BE_MVP_TIMEBASE_HZ), the DTB size for dtc -S (BE_MVP_DTB_BYTES),
the domain count (BE_MVP_DOMAINS, one guest per domain), and, for the
reference boot, the kernel's GPA and the 2 MiB leaf. Each guest window has
the same guest-physical layout, so G0's and G1's DTBs differ only in
bootargs: B6's bootargs, then `-- be.guest=<g>`, which Linux hands to /init
as an argument. Each guest's hart is 0 in its DTB, whatever physical hart
runs its domain. For a role in an M1 scenario (planning/mvp-m1-plan.md,
Scenarios and the harness), role_arguments() renders the init's further
arguments after be.guest=<g>: be.role=, be.channel=, and be.deny=, which
tools/gen-scenario.py requires of a be-mvp-scenario-v2 domain's bootargs;
for an M2 role (planning/mvp-m2-plan.md, Guest software), page_arguments()
renders be.role=, be.pages= (each page's GPA), and be.deny=, which it
requires of a be-mvp-scenario-v3 domain's.

Variants of one guest's DTB, each exactly one change from that guest's
`base` (all but `base`, `te-poc`, and `anchor` are QEMU-only test inputs):
  base       the guest's DTB, for QEMU and the board
  init-exit  " rdinit=/init-exit" before the "--"
  rdcycle    " rdinit=/init-rdcycle" before the "--"
  sbi-time   "sstc" leaves riscv,isa-extensions
  reference  the memory node starts at the kernel's GPA, 0x8020_0000, past
             QEMU's OpenSBI at 0x8000_0000, for the reference boot under
             plain OpenSBI
  te-poc     the te-poc scenario's DTB, for QEMU and the board
             (planning/mvp-m1-plan.md, "Scenarios and the harness"): the
             guest's role arguments after `be.guest=<g>`, TE_POC_ROLES'
             role and denied accesses with the channel page's GPA
             (BE_MVP_CHANNEL_GPA), which scenarios/te-poc/scenario.json's
             bootargs must equal (tools/check-image.py compares them)
  anchor     the anchor scenario's DTB, for QEMU and the board
             (planning/mvp-m2-plan.md, "Scenarios and the harness"): the
             guest's role arguments after `be.guest=<g>`, ANCHOR_ROLES'
             role and denied accesses with Q1's three pages' GPAs, which
             scenarios/anchor/scenario.json's bootargs must equal
  shell      M7's shell (planning/mvp-m7-plan.md, Q4; M7-4): the guest's
             base DTB with " rdinit=/init-shell" before the "--", for
             two-guests' shell variant
  te-poc-shell, anchor-shell
             te-poc's and anchor's DTB with that one change, for their
             shell variants (anchor's G0 alone: its protected domain keeps
             its role, Q27)
  hostile    " rdinit=/init-hostile" before the "--" (M7-4, D-4): G0's,
             for two-guests' QEMU-only hostile variant

DTBS names the DTBs that tools/build-guest.sh makes: both guests' base,
sbi-time, reference, te-poc, anchor, shell, and te-poc-shell DTBs, G1's
init-exit, and G0's rdcycle, anchor-shell, and hostile, as the plans' QEMU
scenarios and images use them.

Queries (for guest.mk, build-guest.sh, and the reference boot): dtb-bytes
(decimal); dtbs (one `NAME GUEST VARIANT` line per DTB); and
reference-kernel, reference-dtb, and reference-size (hexadecimal): the
reference boot loads the kernel at the start of the reference memory node,
which is the window's size, and the DTB at the start of its last 2 MiB, as
the MVP places each DTB in its window.

--self-test renders every DTB and requires each variant to differ from its
guest's `base` in exactly its one change, and G0's base to differ from G1's
in the guest digit alone. Each base DTS must match, token for token, the DTS
block of the accepted B6 plan (--b6-plan, default planning/k3-b6-plan.md)
with the MVP model, compatible, and bootargs, which the accepted MVP M0 plan
(--plan, default planning/mvp-m0-plan.md) must state. It also ties
guest/mvp-guest-id.h to BE_MVP_DOMAINS and checks the layout parser and the
renderer's refusals.
"""

import argparse
import pathlib
import re
import string
import sys

BOOTARGS = "earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1"
GUEST_ARG = "be.guest="
# M7's shell and M7-4's hostile guest, each an rdinit= variant of the init
# (guest/mvp-init.c): the kernel option before the "--".
SHELL_ARG = " rdinit=/init-shell"
HOSTILE_ARG = " rdinit=/init-hostile"
# The init's roles and denied accesses (planning/mvp-m1-plan.md, Guest
# software).
ROLES = ("writer", "reader")
ACCESSES = ("load", "store")
# te-poc's roles (planning/mvp-m1-plan.md, Q3): G0 the writer, whose one
# denial loads from the page beside the channel page; G1 the reader, which
# stores into the channel page's last doubleword and then loads from M0's
# K3 probe GPA. Each GPA is the channel page's plus an offset, or absolute.
TE_POC_ROLES = {
    0: ("writer", (("load", "channel", 0x1000),)),
    1: ("reader", (("store", "channel", 0xff8), ("load", None, 0x90000000))),
}
# anchor's roles (planning/mvp-m2-plan.md, Q9 and Guest software): G0 the
# host, whose child stores into the response page's last doubleword, then
# loads from the secret page, from the protected window's HPA read as a
# GPA, and from the MVP region's base read as a GPA (the measurement's
# stand-in); G1 the protected domain, whose child stores into the request
# page's last doubleword. Each GPA is a page's plus an offset (Q1: page i
# is the channel page plus i 4 KiB pages), or a layout constant's.
PAGE_ROLES = ("host", "prot")
ANCHOR_PAGES, PAGE_BYTES = 3, 0x1000
ANCHOR_ROLES = {
    0: ("host", (("store", 1, 0xff8), ("load", 2, 0), ("load", "G1_HPA", 0),
                 ("load", "REGION_HPA", 0))),
    1: ("prot", (("store", 0, 0xff8),)),
}
MODEL = "Beryllium MVP guest"
COMPATIBLE = "beryllium,mvp-guest"
B6_MODEL = "Beryllium K3 B6 guest"
B6_COMPATIBLE = "beryllium,k3-b6-guest"
ISA_EXTENSIONS = ("i", "m", "a", "c", "zicsr", "zifencei", "zihintpause",
                  "zba", "zbb", "zbs", "sstc", "svade")
# beryllium-cheri: each guest flavour's further extensions, after svade
# (--guest-flavour): the CHERI Linux guest's DTBs also name CHERI v0.9.3's
# Zcherihybrid and Zcheripurecap, without which CHERI Alliance Linux never
# enables CHERI for user space (senvcfg.CRE; arch/riscv/kernel/
# cpufeature.c). main() selects the flavour.
FLAVOUR_EXTENSIONS = {"linux": (),
                      "cheri-linux": ("zcherihybrid", "zcheripurecap")}
FLAVOUR = "linux"
VARIANTS = ("base", "init-exit", "rdcycle", "sbi-time", "reference",
            "te-poc", "anchor", "shell", "te-poc-shell", "anchor-shell",
            "hostile")
DTBS = (
    ("mvp-guest-g0.dtb", 0, "base"),
    ("mvp-guest-g1.dtb", 1, "base"),
    ("mvp-guest-g1-init-exit.dtb", 1, "init-exit"),
    ("mvp-guest-g0-rdcycle.dtb", 0, "rdcycle"),
    ("mvp-guest-g0-sbi-time.dtb", 0, "sbi-time"),
    ("mvp-guest-g1-sbi-time.dtb", 1, "sbi-time"),
    ("mvp-guest-g0-reference.dtb", 0, "reference"),
    ("mvp-guest-g1-reference.dtb", 1, "reference"),
    ("mvp-guest-g0-te-poc.dtb", 0, "te-poc"),
    ("mvp-guest-g1-te-poc.dtb", 1, "te-poc"),
    ("mvp-guest-g0-anchor.dtb", 0, "anchor"),
    ("mvp-guest-g1-anchor.dtb", 1, "anchor"),
    ("mvp-guest-g0-shell.dtb", 0, "shell"),
    ("mvp-guest-g1-shell.dtb", 1, "shell"),
    ("mvp-guest-g0-te-poc-shell.dtb", 0, "te-poc-shell"),
    ("mvp-guest-g1-te-poc-shell.dtb", 1, "te-poc-shell"),
    ("mvp-guest-g0-anchor-shell.dtb", 0, "anchor-shell"),
    ("mvp-guest-g0-hostile.dtb", 0, "hostile"),
)
# beryllium-cheri: each guest flavour's own DTBs, after DTBS
# (select_flavour()): the CHERI Linux guest's cap-store, te-poc's G0 with
# rdinit=/init-cap-store, a link to /init, whose init loads the
# capability-store module before its pattern write (planning/
# cheri-enforcement-plan.md, CE-4).
CAP_STORE_ARG = " rdinit=/init-cap-store"
FLAVOUR_DTBS = {"linux": (),
                "cheri-linux": (("mvp-guest-g0-cap-store.dtb", 0,
                                 "cap-store"),)}
BASE_VARIANTS, BASE_DTBS = VARIANTS, DTBS
REQUIRED = ("DOMAINS", "GUEST_GPA", "GUEST_BYTES", "TIMEBASE_HZ",
            "DTB_BYTES", "KERNEL_GPA", "KERNEL_TEXT_OFFSET",
            "GUEST_LEAF_BYTES")
DEFINE = re.compile(r"^#define\s+BE_MVP_([A-Z0-9_]+)\s+"
                    r"BE_MVP_C\(\s*(0x[0-9a-fA-F]+|[0-9]+)\s*\)\s*$")
GUEST_IDS = re.compile(r"^#define\s+MVP_GUEST_IDS\s+([0-9]+)\s*$", re.M)
U32 = 0xffffffff
U64 = 0xffffffffffffffff


class LayoutError(Exception):
    """The layout header lacks a value or holds an inconsistent one."""


def parse_layout(text):
    """Return {NAME: value} for every BE_MVP_C() define, checked."""
    layout = {}
    for line in text.splitlines():
        match = DEFINE.match(line)
        if not match:
            continue
        name, literal = match.groups()
        if name in layout:
            raise LayoutError(f"BE_MVP_{name} is defined twice")
        layout[name] = int(literal, 0)
    for name in REQUIRED:
        if name not in layout:
            raise LayoutError(f"BE_MVP_{name} is missing")
        if not 0 < layout[name] <= U64:
            raise LayoutError(f"BE_MVP_{name} is out of range")
    if layout["DOMAINS"] != 2:
        raise LayoutError("BE_MVP_DOMAINS is not 2 (G0 and G1)")
    leaf = layout["GUEST_LEAF_BYTES"]
    if layout["GUEST_GPA"] + layout["KERNEL_TEXT_OFFSET"] != layout["KERNEL_GPA"]:
        raise LayoutError("BE_MVP_KERNEL_GPA is not the window plus "
                          "text_offset")
    for name in ("GUEST_GPA", "GUEST_BYTES", "KERNEL_GPA"):
        if layout[name] % leaf:
            raise LayoutError(f"BE_MVP_{name} is not 2 MiB aligned")
    if layout["GUEST_BYTES"] <= layout["KERNEL_TEXT_OFFSET"] + leaf:
        raise LayoutError("BE_MVP_GUEST_BYTES leaves no room for the kernel")
    if layout["TIMEBASE_HZ"] > U32 or layout["DTB_BYTES"] % 8:
        raise LayoutError("BE_MVP_TIMEBASE_HZ or BE_MVP_DTB_BYTES is "
                          "unusable")
    return layout


def reference_memory(layout):
    """The reference node: the window's size, starting at the kernel."""
    return layout["KERNEL_GPA"], layout["GUEST_BYTES"]


def select_flavour(flavour):
    """beryllium-cheri: FLAVOUR's rules: its extensions, and its own
    variants and DTBs after the others (FLAVOUR_DTBS)."""
    global FLAVOUR, VARIANTS, DTBS
    FLAVOUR = flavour
    VARIANTS = BASE_VARIANTS + tuple(variant for _, _, variant in
                                     FLAVOUR_DTBS[flavour])
    DTBS = BASE_DTBS + FLAVOUR_DTBS[flavour]


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


def guest_bootargs(guest, extra="", init=""):
    """B6's bootargs, any option for the kernel, then init's arguments."""
    return f"{BOOTARGS}{extra} -- {GUEST_ARG}{guest}{init}"


def role_arguments(role, channel, deny):
    """The init's arguments after be.guest=<g> for a role (planning/
    mvp-m1-plan.md, Scenarios and the harness): be.role=, be.channel= (the
    channel page's GPA), and be.deny=, each denied access as ACCESS@GPA in
    the order the init makes them, a load or a store (Q3: no fetch)."""
    if role not in ROLES:
        raise ValueError(f"unknown role {role!r}")
    return f" be.role={role} be.channel={channel:#x}" + deny_argument(deny)


def page_arguments(role, pages, deny):
    """The init's arguments after be.guest=<g> for an M2 role (planning/
    mvp-m2-plan.md, Guest software): be.role=, be.pages= (each page's GPA,
    in the pages' order), and be.deny=, as role_arguments() writes it."""
    if role not in PAGE_ROLES or not pages:
        raise ValueError(f"unknown role {role!r}, or no page")
    return (f" be.role={role} be.pages=" +
            ",".join(f"{gpa:#x}" for gpa in pages) + deny_argument(deny))


def deny_argument(deny):
    """be.deny=: each denied access as ACCESS@GPA, or nothing."""
    if any(access not in ACCESSES or not 0 <= gpa <= U64
           for access, gpa in deny):
        raise ValueError(f"a denied access in {deny!r} is not a load or a "
                         "store at a GPA")
    return (" be.deny=" + ",".join(f"{access}@{gpa:#x}"
                                   for access, gpa in deny) if deny else "")


def te_poc_arguments(layout, guest):
    """te-poc's init arguments for one guest (TE_POC_ROLES)."""
    if "CHANNEL_GPA" not in layout:
        raise LayoutError("BE_MVP_CHANNEL_GPA is missing")
    role, accesses = TE_POC_ROLES[guest]
    channel = layout["CHANNEL_GPA"]
    return role_arguments(role, channel, [
        (access, (channel if base == "channel" else 0) + offset)
        for access, base, offset in accesses])


def anchor_arguments(layout, guest):
    """anchor's init arguments for one guest (ANCHOR_ROLES), with Q1's
    three pages from BE_MVP_CHANNEL_GPA."""
    if "CHANNEL_GPA" not in layout:
        raise LayoutError("BE_MVP_CHANNEL_GPA is missing")
    role, accesses = ANCHOR_ROLES[guest]
    pages = [layout["CHANNEL_GPA"] + index * PAGE_BYTES
             for index in range(ANCHOR_PAGES)]
    return page_arguments(role, pages, [
        (access, (pages[base] if isinstance(base, int) else layout[base]) +
         offset) for access, base, offset in accesses])


def values(layout, guest, variant):
    """The template values of one guest's variant: its base plus one change."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}")
    if guest not in range(layout["DOMAINS"]):
        raise ValueError(f"unknown guest {guest!r}")
    bootargs = guest_bootargs(guest)
    isa = list(ISA_EXTENSIONS) + list(FLAVOUR_EXTENSIONS[FLAVOUR])
    base, size = layout["GUEST_GPA"], layout["GUEST_BYTES"]
    if variant == "init-exit":
        bootargs = guest_bootargs(guest, " rdinit=/init-exit")
    elif variant == "rdcycle":
        bootargs = guest_bootargs(guest, " rdinit=/init-rdcycle")
    elif variant == "te-poc":
        bootargs = guest_bootargs(guest,
                                  init=te_poc_arguments(layout, guest))
    elif variant == "cap-store":
        bootargs = guest_bootargs(guest, CAP_STORE_ARG,
                                  te_poc_arguments(layout, guest))
    elif variant == "anchor":
        bootargs = guest_bootargs(guest,
                                  init=anchor_arguments(layout, guest))
    elif variant == "shell":
        bootargs = guest_bootargs(guest, SHELL_ARG)
    elif variant == "te-poc-shell":
        bootargs = guest_bootargs(guest, SHELL_ARG,
                                  te_poc_arguments(layout, guest))
    elif variant == "anchor-shell":
        bootargs = guest_bootargs(guest, SHELL_ARG,
                                  anchor_arguments(layout, guest))
    elif variant == "hostile":
        bootargs = guest_bootargs(guest, HOSTILE_ARG)
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


def flavour_isa_tail():
    """beryllium-cheri: svade and the flavour's further extensions, as the
    DTS's riscv,isa-extensions list ends."""
    return ", ".join(f'"{name}"' for name in
                     ("svade",) + FLAVOUR_EXTENSIONS[FLAVOUR]) + ";"


def mvp_plan_dts(b6_plan_text, guest):
    """B6's accepted DTS with the MVP model, compatible, and bootargs, and
    (beryllium-cheri) the flavour's further extensions after svade."""
    text = plan_dts(b6_plan_text)
    text = replace_once(text, f'"{B6_COMPATIBLE}"', f'"{COMPATIBLE}"')
    text = replace_once(text, f'"{B6_MODEL}"', f'"{MODEL}"')
    if FLAVOUR_EXTENSIONS[FLAVOUR]:
        text = replace_once(text, '"svade";', flavour_isa_tail())
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
    for statement in (f"Kernel command line: {guest_bootargs('<g>')}",
                      f'DT model "{MODEL}" and compatible "{COMPATIBLE}"'):
        expect(statement in plan_text, f"the MVP plan lacks {statement}")
    ids = GUEST_IDS.findall(id_header)
    expect(ids == [str(layout["DOMAINS"])],
           f"mvp-guest-id.h MVP_GUEST_IDS {ids} is not BE_MVP_DOMAINS")

    bases = {}
    for guest in range(layout["DOMAINS"]):
        base = bases[guest] = render(template, layout, guest, "base")
        expect(dts_tokens(base) == dts_tokens(mvp_plan_dts(b6_plan_text,
                                                           guest)),
               f"G{guest}: the base DTS differs from B6's with the MVP "
               "names")
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
        "shell": [("bootargs", '"' + guest_bootargs("{g}", SHELL_ARG) +
                   '";')],
        "hostile": [("bootargs", '"' + guest_bootargs("{g}", HOSTILE_ARG) +
                     '";')],
        "sbi-time": [("riscv,isa-extensions",
                      '"zbs", ' + flavour_isa_tail())],
        "reference": [("memory@", f"memory@{ref_base:x} {{"),
                      ("reg", f"{ref_base & U32:#x} {ref_size >> 32:#x} "
                       f"{ref_size & U32:#x}>;")],
        # beryllium-cheri: the CHERI Linux guest's cap-store, G0's alone.
        "cap-store": [("bootargs", '"' + guest_bootargs(
            "{g}", CAP_STORE_ARG, te_poc_arguments(layout, 0)) + '";')],
    }
    names = [name for name, _, _ in DTBS]
    expect(len(set(names)) == len(names), "DTBS repeats a name")
    for guest in range(layout["DOMAINS"]):
        for variant in ("base", "sbi-time", "reference"):
            expect((guest, variant) in [(g, v) for _, g, v in DTBS],
                   f"DTBS lacks G{guest}'s {variant} DTB")
    for name, guest, variant in DTBS:
        expect(name == f"mvp-guest-g{guest}" +
               ("" if variant == "base" else f"-{variant}") + ".dtb",
               f"{name} is not named for G{guest}'s {variant}")
        if variant == "base":
            continue
        rendered = render(template, layout, guest, variant)
        if variant in ("te-poc", "anchor", "te-poc-shell", "anchor-shell"):
            arguments = (te_poc_arguments if variant.startswith("te-poc")
                         else anchor_arguments)(layout, guest)
            expected = [("bootargs", '"' + guest_bootargs(
                guest, SHELL_ARG if variant.endswith("-shell") else "",
                arguments) + '";')]
        else:
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
        if variant in ("init-exit", "rdcycle", "shell", "te-poc-shell",
                       "anchor-shell", "hostile", "cap-store"):
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
           "the reference DTB is not placed as the MVP places each DTB")
    expect(query(layout, "dtbs").splitlines() ==
           [f"{name} {guest} {variant}" for name, guest, variant in DTBS],
           "the dtbs query is not DTBS")
    expect(guest_bootargs(1, init=role_arguments(
        "reader", 0x84000000, [("store", 0x84000ff8), ("load", 0x90000000)]))
           == f"{BOOTARGS} -- {GUEST_ARG}1 be.role=reader "
           "be.channel=0x84000000 be.deny=store@0x84000ff8,load@0x90000000",
           "the reader's init arguments are not the M1 plan's")
    for guest, arguments in ((0, " be.role=writer be.channel=0x84000000 "
                              "be.deny=load@0x84001000"),
                             (1, " be.role=reader be.channel=0x84000000 "
                              "be.deny=store@0x84000ff8,load@0x90000000")):
        expect(te_poc_arguments(layout, guest) == arguments,
               f"G{guest}'s te-poc arguments are not the M1 plan's")
    pages = "0x84000000,0x84001000,0x84002000"
    for guest, arguments in ((0, f" be.role=host be.pages={pages} "
                              "be.deny=store@0x84001ff8,load@0x84002000,"
                              "load@0x114000000,load@0x102064000"),
                             (1, f" be.role=prot be.pages={pages} "
                              "be.deny=store@0x84000ff8")):
        expect(anchor_arguments(layout, guest) == arguments,
               f"G{guest}'s anchor arguments are not the M2 plan's")

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
            re.sub(r"(?m)^#define\s+BE_MVP_TIMEBASE_HZ\b.*$", "",
                   layout_text))),
        ("duplicate constant", lambda: parse_layout(
            layout_text +
            "#define BE_MVP_GUEST_GPA BE_MVP_C(0x80000000)\n")),
        ("three domains", lambda: parse_layout(re.sub(
            r"(?m)^(#define\s+BE_MVP_DOMAINS\s+)BE_MVP_C\([0-9]+\)",
            r"\1BE_MVP_C(3)", layout_text))),
        ("misaligned window", lambda: parse_layout(re.sub(
            r"(?m)^(#define\s+BE_MVP_GUEST_BYTES\s+)"
            r"BE_MVP_C\(0x[0-9a-fA-F]+\)",
            r"\1BE_MVP_C(0x4001000)", layout_text))),
        ("inconsistent kernel GPA", lambda: parse_layout(re.sub(
            r"(?m)^(#define\s+BE_MVP_KERNEL_GPA\s+)"
            r"BE_MVP_C\(0x[0-9a-fA-F]+\)",
            r"\1BE_MVP_C(0x80400000)", layout_text))),
        ("B6 DTS without its model", lambda: mvp_plan_dts(
            b6_plan_text.replace(B6_MODEL, "x"), 0)),
        ("unknown role", lambda: role_arguments("owner", 0x84000000, [])),
        ("a denied fetch", lambda: role_arguments(
            "writer", 0x84000000, [("fetch", 0x84001000)])),
        ("te-poc without a channel", lambda: te_poc_arguments(
            {name: value for name, value in layout.items()
             if name != "CHANNEL_GPA"}, 0)),
        ("unknown page role", lambda: page_arguments(
            "writer", [0x84000000], [])),
        ("anchor without a channel", lambda: anchor_arguments(
            {name: value for name, value in layout.items()
             if name != "CHANNEL_GPA"}, 1)),
    ]
    for name, action in refusals:
        try:
            action()
        except (LayoutError, ValueError, KeyError):
            expect(True, name)
        else:
            expect(False, f"{name} was not refused")
    for failure in failures:
        print(f"BE_MVP_DTS_SELF_TEST: FAIL {failure}")
    status = "FAIL" if failures else "PASS"
    print(f"BE_MVP_DTS_SELF_TEST: {status} cases={cases} dtbs={len(DTBS)} "
          f"variants={len(VARIANTS)}")
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--layout", required=True, type=pathlib.Path)
    parser.add_argument("--template", type=pathlib.Path)
    parser.add_argument("--guest", type=int, default=0)
    parser.add_argument("--variant", default="base",
                        choices=VARIANTS + tuple(
                            variant for dtbs in FLAVOUR_DTBS.values()
                            for _, _, variant in dtbs))
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--query")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--plan", type=pathlib.Path)
    parser.add_argument("--b6-plan", type=pathlib.Path)
    # beryllium-cheri: the guest flavour.
    parser.add_argument("--guest-flavour", choices=tuple(FLAVOUR_EXTENSIONS),
                        default="linux")
    args = parser.parse_args()
    select_flavour(args.guest_flavour)
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
            planning = args.layout.resolve().parents[2] / "planning"
            plan = args.plan or planning / "mvp-m0-plan.md"
            b6_plan = args.b6_plan or planning / "k3-b6-plan.md"
            id_header = args.template.resolve().parent / "mvp-guest-id.h"
            return self_test(template, layout_text,
                             plan.read_text(encoding="utf-8"),
                             b6_plan.read_text(encoding="utf-8"),
                             id_header.read_text(encoding="ascii"))
        text = render(template, layout, args.guest, args.variant)
    except (LayoutError, ValueError) as error:
        print(f"BE_MVP_DTS: FAIL {error}", file=sys.stderr)
        return 1
    if args.output:
        args.output.write_text(text, encoding="ascii")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
