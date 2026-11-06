#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# A copy of B5's tests/check-b5-image.py (accepted at 82956239) with the
# counted changes listed in bringup/k3-b6/README.md.
"""Check K3 B6 images (planning/k3-b6-plan.md, "Tests and evidence").

  check-b6-image.py --pins PINS --kernel IMAGE --dtb DTB [--base B]
                    [--lds ACCEPTED_R5_LDS]
                    --image TOOLCHAIN:ELF:BIN:BOOT_ELF:BOOT_IMG [--image ...]
  check-b6-image.py --pins PINS --kernel IMAGE --dtb DTB
                    --reference gcc:ELF:BIN:BOOT_ELF:BOOT_IMG
                    [--variant-dtb NAME:DTB ...]
                    [--variant NAME:BOOT_ELF:BOOT_IMG ...]
                    [--uimage NAME:TEXT_OFFSET:BIN:IMG ...]
  check-b6-image.py --pins PINS --kernel IMAGE --dtb DTB
                    --mutation-test TOOLCHAIN:ELF:BIN:BOOT_ELF:BOOT_IMG

B6 links none of the R5 switch, so this is a B6-specific checker, as B1's,
B2's, and B5's are. Every address and budget comes from src/b6-layout.h.

Monitor (ELF and its flat image):

- a little-endian RV64 ET_EXEC whose entry is be_reset at 0x1_0200_0000;
  the six PT_LOAD segments of the accepted R5 PHDRS, in order, with their
  flags, vaddr == paddr, and no segment both writable and executable, then
  the seventh, the B6 pool: NOLOAD, RW, exactly 0x8000 bytes at
  0x1_0203_4000; a flat image of exactly 0x34000 bytes holding every
  segment's file bytes in place and zeros elsewhere;
- every conjunct of every ASSERT in the accepted R5 linker script
  (arch/riscv/be/r5-beryllium.lds at 165f4d00, SHA-256 pinned) with every
  symbol moved back by 0x81e00000, its three trap-vector conjuncts renamed
  to be_b6_trap_vector (the port's counted rule), and the port's four pool
  conjuncts at the K3 addresses;
- monitor text ending at or below 0x1_0200_8000 and data and BSS at or
  below 0x1_0200_f000 (the plan's budgets);
- be_reset first calls be_b1_quiesce, then runs the accepted first entry
  instruction (mv s0, a0), and calls or tails nothing but be_b1_quiesce,
  be_b6_runtime_main, and be_r3_arch_halt;
- both guest pages equal to B2's (pinned): the inert R5 fixtures;
- be_r3_arch_reset_state, be_r3_arch_install_management, and
  be_r3_arch_enter_management byte-identical to B2's (pinned); the install
  function has exactly two call sites, both in boot code, and
  be_r3_arch_enter_management and be_r3_arm_management_entry have none;
- no R4 or R5 mechanism symbol: no be_r4_* symbol, and no be_r5_* symbol
  but the two inert fixtures' four;
- from the monitor-text instruction words, decoded function by function
  (padding between functions may hold only nops and zeros): exactly one
  ecall, in be_r3_arch_sbi_call, which only the accepted platform helpers
  call; exactly three sret (the dead R3 entry, B6's resume tail, B1's
  skip); exactly one fence.i, in be_b6_arch_fence_i; sfence.vma, hgatp
  writes, and hfence.gvma only in the R3 functions; no hfence.vvma, H load
  or store, mret, ebreak, or F, D, or V instruction; no access at all to
  hstateen0, hvictl, hvien, hviprio1, or hviprio2; and every CSR write in
  the functions of the table below, exactly: after the R3 reset, henvcfg,
  hedeleg, hideleg, hcounteren, and hstatus are written only by B6's arm
  helpers, vstimecmp also by the TIME helper, sscratch by the arm helper
  and the vector, sepc and sstatus by the resume tail, no other vs* CSR,
  and hie and hvip only by the R3 halts;
- the values B6's arm helpers write (henvcfg STCE only; vstimecmp ~0, then
  hip read, then hedeleg 0xb15d (read back as WARL), hideleg 0x40,
  hcounteren 0x2, hstatus
  VTVM/VTW/VTSR cleared, sscratch the trusted top) and every control they
  read back into its struct be_b6_controls slot, derived from the decoded
  words by constant tracking;
- the vector: sscratch exchanged first, the 31 GPRs and the eight trap
  CSRs at their struct be_r4_frame offsets, the sealed reserved word,
  hstatus, htinst, vsatp, and time at 320-344, a fail-closed test of
  hstatus.SPV, and the call to be_b6_dispatch;
- the resume tail: call free, leaving only to the terminal; exactly the
  plan's checks (satp, stvec, sscratch, sie, sstatus under its mask,
  hstatus under the R3 mask, hedeleg against the armed readback in its
  third argument, hideleg, hie at most VSTIE, hvip, hcounteren,
  htimedelta, henvcfg, hgeie, and the hgatp argument), no
  vsatp check, one SPP set, sepc and every GPR from the frame, ending in
  its one sret;
- only boot code forms an address inside a G-stage pool (the accepted
  roots, or the B6 pool).

Boot image (the board file and the ELF QEMU boots):

- B3's header (bringup/k3-b3/tests/check-b3-image.py, imported unchanged)
  with text_offset 0x0600_0000 (QEMU's k3-address: 0x8800_0000) and
  image_size equal to the file; B3's descriptor (0x1_0200_0000, 0x34000,
  0x1000) and report templates;
- the five ranges pairwise disjoint and in S-mode RAM: the monitor image,
  the pool, the staged image at L, the kexec FDT slot (2 MiB at the
  image's end rounded up to 2 MiB), and the guest window;
- the monitor flat image at 0x1000, the kernel at 0x35000, zeros, then the
  4 KiB DTB at the next 4 KiB boundary, which ends the file (at most
  4 MiB);
- the kernel through an independent RISC-V Image header reader, and the
  DTB through an FDT reader for the DT contract: one memory node equal to
  the window, one cpu@0 with the pinned ISA list and its interrupt
  controller, the timebase, the exact bootargs, and no other node; then
  both against guest/pins.txt;
- with the monitor ELF, the payload constants (be_b6_payload_layout) equal
  to these offsets and sizes; with the boot ELF, its entry at L, four
  PT_LOAD segments (R-X, RW, R, R) whose bytes are the file, and its
  kernel and DTB labels; and, when present beside it, the second link
  (be-k3-b6-boot-pic.img) byte-identical.

--variant checks a QEMU-only negative variant against the reference GCC
images: it must pass the boot-image rules with its own one change and
differ from the reference only there (payload: the kernel's magic2 byte;
a DTB variant: the DTB, equal to its pin and its variant contract;
exit-budget and guest-timeout: the monitor's one run-limit word).
--uimage checks a board or QEMU booti image with its text_offset, and a
k3-address image differs from the reference only in text_offset.
--mutation-test applies known defects in memory and requires each to be
rejected for its own reason.
"""

import argparse
import hashlib
import importlib.util
import pathlib
import re
import struct
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve()
B6_DIR = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
ACCEPTED_LDS = REPO_ROOT / "arch" / "riscv" / "be" / "r5-beryllium.lds"
B3_CHECKER = REPO_ROOT / "bringup" / "k3-b3" / "tests" / "check-b3-image.py"
LAYOUT_H = B6_DIR / "src" / "b6-layout.h"


def layout_constants(path=LAYOUT_H):
    """Every BE_B6_* literal in b6-layout.h, as integers."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    return {name[len("BE_B6_"):]: int(value, 0) for name, value in re.findall(
        r"^#define\s+(BE_B6_\w+)\s+BE_B6_C\((0x[0-9a-fA-F]+|\d+)\)", text,
        re.M)}


LAYOUT = layout_constants()
BASE = LAYOUT["MONITOR_HPA"]
SPAN = LAYOUT["MONITOR_BYTES"]
POOL = LAYOUT["POOL_HPA"]
POOL_BYTES = LAYOUT["POOL_BYTES"]
STAGING = LAYOUT["STAGING_HPA"]
WINDOW = LAYOUT["GUEST_HPA"]
WINDOW_BYTES = LAYOUT["GUEST_BYTES"]
KERNEL_OFFSET = LAYOUT["BOOT_KERNEL_OFFSET"]
MONITOR_OFFSET = LAYOUT["BOOT_MONITOR_OFFSET"]
DTB_BYTES = LAYOUT["DTB_BYTES"]
PAGE = LAYOUT["PAYLOAD_ALIGN"]
DELTA = 0x81E00000
CODE_PAGE = 0x32000
PROTECTED_PAGE = 0x33000
MONITOR_TEXT_LIMIT = 0x102008000
MONITOR_DATA_LIMIT = 0x10200F000
# S-mode RAM on the COM260: above OpenSBI, to the end of its 8 GiB.
SMODE_RAM = (0x102000000, 0x300000000)
ACCEPTED_LDS_SHA256 = \
    "0df278b45d33500af08204b364a3f3e61178a7cd9981cb499025d95411baa56a"
ACCEPTED_CONJUNCTS = 57
PF_X, PF_W = 1, 2
RISCV_MV_S0_A0 = 0x00050413
MASK64 = (1 << 64) - 1

# The port's counted ASSERT changes (scripts/port.py): three renamed
# trap-vector conjuncts, and the new pool block at the K3 addresses.
TRAP_VECTOR_CONJUNCTS = 3
POOL_CONJUNCTS = (
    f"__be_b6_pool_start == 0x{POOL:x}",
    f"__be_b6_pool_end == 0x{POOL + POOL_BYTES:x}",
    "(__be_b6_pool_start & 0x3fff) == 0",
    "__be_guest_protected_end <= __be_b6_pool_start",
)
POOL_PHDR = ("b6_pool", 6)

# From the accepted B2 images (bringup/k3-b2/README.md: GCC 9c145f00...,
# Clang 47be17e3...): both guest pages, and the R3 functions B6 reuses.
B2_PAGE_SHA256 = {
    ("gcc", CODE_PAGE):
        "c61ea0146498624a8d66b0e2c8009dc92ef79f581949c3cfd8e1f3f4dde60f9d",
    ("clang", CODE_PAGE):
        "c61ea0146498624a8d66b0e2c8009dc92ef79f581949c3cfd8e1f3f4dde60f9d",
    ("gcc", PROTECTED_PAGE):
        "1bec687dabe929d676d5ed0d3cecb601c8932a034520fbe7f05ec8c47d67edd5",
    ("clang", PROTECTED_PAGE):
        "788d045042a98214b781c98884b139356f450a0ec4eaba0961144bc94876b3b0",
}
B2_R3_FUNCTIONS = {
    "gcc": {
        "be_r3_arch_reset_state": (
            0x1aa,
            "0e32a04aab3cd1b900639e53495ef8879909b712436fa369c6d4c6f906ad840a"),
        "be_r3_arch_install_management": (
            0xe,
            "d928179d49757046c40c5ed17e8fda517ec041707cdee758c33182942f2d2f52"),
        "be_r3_arch_enter_management": (
            0x56,
            "d406f12926032eacda7c8e2d80d5d1609ea9251c6dabd95d38bbd7b12cd5c610"),
    },
    "clang": {
        "be_r3_arch_reset_state": (
            0x1aa,
            "aba92183d42684c487d1e14e054e366c707b308c224d8f9b6086d3ab1cf88427"),
        "be_r3_arch_install_management": (
            0xe,
            "d928179d49757046c40c5ed17e8fda517ec041707cdee758c33182942f2d2f52"),
        "be_r3_arch_enter_management": (
            0x56,
            "d406f12926032eacda7c8e2d80d5d1609ea9251c6dabd95d38bbd7b12cd5c610"),
    },
}

R3_RESET = "be_r3_arch_reset_state"
R3_INSTALL = "be_r3_arch_install_management"
R3_ENTER = "be_r3_arch_enter_management"
R3_ARM = "be_r3_arm_management_entry"
R3_SBI = "be_r3_arch_sbi_call"
R3_UNEXPECTED = "be_r3_unexpected_trap"
R3_HALT = "be_r3_arch_halt"
B1_QUIESCE = "be_b1_quiesce"
B1_SKIP = "be_b1_skip"
B1_HALT = "be_b1_halt"
B6_STCE = "be_b6_arch_arm_stce"
B6_ARM = "be_b6_arch_arm_controls"
B6_TIMER = "be_b6_arch_set_timer"
B6_TIME = "be_b6_arch_read_time"
B6_FENCE_I = "be_b6_arch_fence_i"
B6_VECTOR = "be_b6_trap_vector"
B6_RESUME = "be_b6_arch_resume"
B6_MAIN = "be_b6_runtime_main"
B6_DISPATCH = "be_b6_dispatch"
B6_TERMINAL = "be_b6_runtime_terminal"
B6_LAYOUT_SYMBOL = "be_b6_payload_layout"
B6_CONTROL_SYMBOL = "be_b6_control"
PLATFORM_HELPERS = {"sbi_value_call", "be_r3_platform_get_spec_version",
                    "be_r3_platform_probe_extension", "be_r3_platform_write",
                    "be_r3_platform_reset"}
REQUIRED_SYMBOLS = (
    "be_reset", B1_QUIESCE, B6_MAIN, B6_DISPATCH, B6_VECTOR, B6_RESUME,
    B6_STCE, B6_ARM, B6_TIMER, B6_TIME, B6_FENCE_I, B6_TERMINAL,
    "be_b6_exit_terminal", B6_LAYOUT_SYMBOL, B6_CONTROL_SYMBOL,
    "__be_b6_pool_start", "__be_b6_pool_end", R3_RESET, R3_INSTALL, R3_ENTER,
    R3_SBI, R3_HALT,
)
ALLOWED_R5_SYMBOLS = {"be_r5_management_fixture",
                      "be_r5_management_fixture_end",
                      "be_r5_protected_fixture", "be_r5_protected_fixture_end"}

CSR_NAMES = {
    0x100: "sstatus", 0x104: "sie", 0x105: "stvec", 0x106: "scounteren",
    0x10A: "senvcfg", 0x140: "sscratch", 0x141: "sepc", 0x142: "scause",
    0x143: "stval", 0x144: "sip", 0x14D: "stimecmp", 0x150: "siselect",
    0x151: "sireg", 0x180: "satp",
    0x200: "vsstatus", 0x204: "vsie", 0x205: "vstvec", 0x240: "vsscratch",
    0x241: "vsepc", 0x242: "vscause", 0x243: "vstval", 0x244: "vsip",
    0x24D: "vstimecmp", 0x280: "vsatp",
    0x600: "hstatus", 0x602: "hedeleg", 0x603: "hideleg", 0x604: "hie",
    0x605: "htimedelta", 0x606: "hcounteren", 0x607: "hgeie",
    0x608: "hvien", 0x609: "hvictl", 0x60A: "henvcfg", 0x60C: "hstateen0",
    0x643: "htval", 0x644: "hip", 0x645: "hvip", 0x646: "hviprio1",
    0x647: "hviprio2", 0x64A: "htinst", 0x680: "hgatp", 0xC01: "time",
}
# Never accessed, read or written: the DT contract avoids what they gate.
FORBIDDEN_CSRS = {"hstateen0", "hvictl", "hvien", "hviprio1", "hviprio2"}
VS_RESET_ONLY = ("vsstatus", "vsie", "vstvec", "vsscratch", "vsepc",
                 "vscause", "vstval", "vsip", "vsatp")
# Every CSR the monitor writes, and exactly the functions that write it.
CSR_WRITERS = {
    "satp": {R3_RESET},
    "sstatus": {R3_RESET, R3_ENTER, B1_QUIESCE, B1_HALT, B6_RESUME},
    "stvec": {R3_RESET, B1_QUIESCE},
    "sscratch": {R3_RESET, R3_ENTER, B6_ARM, B6_VECTOR},
    "sepc": {R3_RESET, R3_ENTER, B1_SKIP, B6_RESUME},
    "scause": {R3_RESET},
    "stval": {R3_RESET},
    "sie": {R3_RESET, R3_UNEXPECTED, R3_HALT, B1_QUIESCE, B1_HALT},
    "sip": {B1_QUIESCE},
    "senvcfg": {R3_RESET},
    "scounteren": {R3_RESET},
    "stimecmp": {B1_QUIESCE},
    "siselect": {B1_QUIESCE},
    "sireg": {B1_QUIESCE},
    "hstatus": {R3_RESET, B6_ARM},
    "hedeleg": {R3_RESET, B6_ARM},
    "hideleg": {R3_RESET, B6_ARM},
    "hie": {R3_RESET, R3_UNEXPECTED, R3_HALT},
    "hvip": {R3_RESET, R3_UNEXPECTED, R3_HALT},
    "hcounteren": {R3_RESET, B6_ARM},
    "htimedelta": {R3_RESET},
    "henvcfg": {R3_RESET, B6_STCE},
    "hgeie": {R3_RESET},
    "htval": {R3_RESET},
    "hgatp": {R3_RESET, R3_INSTALL},
    "vstimecmp": {B6_ARM, B6_TIMER},
    **{name: {R3_RESET} for name in VS_RESET_ONLY},
}
INSTRUCTION_SITES = {
    "ecall": {R3_SBI: 1},
    "sret": {R3_ENTER: 1, B6_RESUME: 1, B1_SKIP: 1},
    "hfence.gvma": {R3_RESET: 1, R3_INSTALL: 1},
    "sfence.vma": {R3_RESET: 1},
    "wfi": {R3_UNEXPECTED: 1, R3_HALT: 1, B1_HALT: 1},
    "fence.i": {B6_FENCE_I: 1},
    "hfence.vvma": {},
    "hlsv": {},
    "mret": {},
    "ebreak": {},
}
NOP = 0x00000013
C_NOP = 0x0001
FENCE_I = 0x0000100F
CSRRW_SP_SSCRATCH_SP = 0x14011173
SHF_WRITE, SHF_ALLOC, SHF_EXECINSTR = 1, 2, 4
# The accepted R5 checker's section table, moved by 0x81e00000:
# (address or None, size or None, required flags, forbidden flags).
EXPECTED_SECTIONS = {
    ".monitor.text": (0x80200000, None, "AX", "W"),
    ".monitor.input": (0x80208000, None, "A", "WX"),
    ".monitor.rodata": (None, None, "A", "WX"),
    ".monitor.data": (None, None, "WA", "X"),
    ".diagnostic": (0x8020F000, 0x1000, "WA", "X"),
    ".gstage.root.management": (0x80214000, 0x8000, "WA", "X"),
    ".gstage.root.protected": (0x8021C000, 0x8000, "WA", "X"),
    ".stack.management": (0x80225000, 0x2000, "WA", "X"),
    ".stack.protected": (0x80228000, 0x2000, "WA", "X"),
    ".saved.management": (0x8022B000, 0x1000, "WA", "X"),
    ".saved.protected": (0x8022C000, 0x1000, "WA", "X"),
    ".private.management": (0x8022E000, 0x1000, "WA", "X"),
    ".private.protected": (0x8022F000, 0x1000, "WA", "X"),
    ".shared": (0x80230000, 0x1000, "WA", "X"),
    ".guest.code.management": (0x80232000, 0x1000, "AX", "W"),
    ".guest.code.protected": (0x80233000, 0x1000, "AX", "W"),
    # lld gives an output section without input sections the previous
    # section's flags masked to A and W, so after the R-X guest page the
    # pool is A in Clang's image and WA in GCC's; its PT_LOAD is RW in both.
    ".gstage.root.b6": (POOL - DELTA, POOL_BYTES, "A", "X"),
}
MAP_SECTIONS = (".saved.management", ".saved.protected",
                ".private.management", ".private.protected", ".shared",
                ".gstage.root.management", ".gstage.root.protected",
                ".gstage.root.b6", ".guest.code.management",
                ".guest.code.protected", ".stack.management",
                ".stack.protected")
# The frame offsets of the eight trap CSRs (struct be_r4_frame), then the
# four words struct be_b6_exit adds after the 320-byte frame.
TRAP_CSRS = ("vstvec", "vsepc", "vscause", "vstval", "scause", "sepc",
             "stval", "htval")
FRAME_TRAP_CSRS = 248
FRAME_RESERVED = 312
FRAME_SEPC = 288
EXIT_WORDS = (("hstatus", 320), ("htinst", 328), ("vsatp", 336),
              ("time", 344))
HSTATUS_SPV = 0x80
# Only boot code may name a G-stage pool: the accepted roots or B6's.
ROOT_POOL_USERS = {B6_MAIN, "run_r2", "build_image_layout"}
B6_POOL_USERS = {B6_MAIN, "build_gstage"}
INSTALL_CALLERS = {B6_MAIN, "build_gstage"}
INSTALL_CALL_SITES = 2

# What B6's arm and timer helpers write, in order: (CSR, operation, value).
ARG_A0, ARG_A1, ARG_A2 = ("arg", "a0"), ("arg", "a1"), ("arg", "a2")
HELPER_WRITES = {
    B6_STCE: [("henvcfg", "w", ("const", 1 << 63))],
    B6_ARM: [("vstimecmp", "w", ("const", MASK64)),
             ("hedeleg", "w", ("const", 0xB15D)),
             ("hideleg", "w", ("const", 0x40)),
             ("hcounteren", "w", ("const", 0x2)),
             ("hstatus", "c", ("const", 0x700000)),
             ("sscratch", "w", ARG_A1)],
    B6_TIMER: [("vstimecmp", "w", ARG_A0)],
}
# The arm helper's readback: struct be_b6_controls offset -> CSR.
CONTROL_SLOTS = {0: "hip", 8: "hstatus", 16: "hedeleg", 24: "hideleg",
                 32: "hie", 40: "hvip", 48: "hcounteren", 56: "htimedelta",
                 64: "henvcfg", 72: "hgeie", 80: "vstimecmp", 88: "sie",
                 96: "sstatus", 104: "hgatp", 112: "vsatp", 120: "sscratch"}
# struct be_b6_state run-limit words (b6.h), which the two monitor
# variants change; b6-runtime.c asserts these offsets.
RUN_LIMIT_SLOTS = {"exit-budget": (72, "EXIT_CEILING", "VARIANT_EXIT_CEILING"),
                   "guest-timeout": (80, "GUEST_TIME_BUDGET",
                                     "VARIANT_GUEST_TIME_BUDGET")}

# The guest DT contract (planning/k3-b6-plan.md, Device tree) and the
# change each DTB variant makes to it.
BOOTARGS = "earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1"
ISA_EXTENSIONS = ("i", "m", "a", "c", "zicsr", "zifencei", "zihintpause",
                  "zba", "zbb", "zbs", "sstc", "svade")
DTB_VARIANTS = ("memory", "init-exit", "rdcycle", "sbi-time")
MONITOR_VARIANTS = ("exit-budget", "guest-timeout")
VARIANTS = ("payload",) + DTB_VARIANTS + MONITOR_VARIANTS
KERNEL_MAGIC2_AT = 0x3B
FDT_MAGIC = 0xD00DFEED


class ImageError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ImageError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def align_up(value, alignment):
    return (value + alignment - 1) // alignment * alignment


# ---------------------------------------------------------- linker script
def strip_comments(text):
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.S)


def parse_phdrs(text):
    block = re.search(r"\bPHDRS\s*\{(.*?)\}", text, re.S)
    require(block is not None, "accepted linker script has no PHDRS")
    phdrs = re.findall(r"(\w+)\s+PT_LOAD\s+FLAGS\((\d+)\)\s*;", block.group(1))
    require(len(phdrs) == 6, f"accepted PHDRS has {len(phdrs)} PT_LOAD, not 6")
    return [(name, int(flags)) for name, flags in phdrs]


def split_top(text, separator):
    """Split at separator outside parentheses and string literals."""
    parts, depth, quoted, start, index = [], 0, False, 0, 0
    while index < len(text):
        char = text[index]
        if char == '"':
            quoted = not quoted
        elif not quoted and char == "(":
            depth += 1
        elif not quoted and char == ")":
            depth -= 1
        elif not quoted and depth == 0 and text.startswith(separator, index):
            parts.append(text[start:index])
            index += len(separator)
            start = index
            continue
        index += 1
    parts.append(text[start:])
    return parts


def parse_asserts(text):
    """Return the condition conjuncts of every ASSERT(condition, message)."""
    conjuncts = []
    for match in re.finditer(r"\bASSERT\s*\(", text):
        depth, index, quoted = 1, match.end(), False
        while depth:
            require(index < len(text), "unterminated ASSERT")
            char = text[index]
            if char == '"':
                quoted = not quoted
            elif not quoted and char == "(":
                depth += 1
            elif not quoted and char == ")":
                depth -= 1
            index += 1
        body = text[match.end():index - 1]
        parts = split_top(body, ",")
        require(len(parts) == 2, f"ASSERT without one message: {body!r}")
        conjuncts.extend(" ".join(part.split())
                         for part in split_top(parts[0], "&&"))
    return conjuncts


TOKEN = re.compile(r"\s*(0[xX][0-9a-fA-F]+|\d+|[A-Za-z_]\w*|==|<=|>=|[<>()&-])")


def tokenize(expression):
    tokens, index = [], 0
    while index < len(expression):
        match = TOKEN.match(expression, index)
        require(match is not None, f"cannot parse {expression!r}")
        tokens.append(match.group(1))
        index = match.end()
        while index < len(expression) and expression[index].isspace():
            index += 1
    return tokens


def evaluate(conjunct, symbols):
    """Evaluate one ASSERT conjunct: difference CMP difference."""
    tokens = tokenize(conjunct)
    position = 0

    def take():
        nonlocal position
        require(position < len(tokens), f"truncated {conjunct!r}")
        position += 1
        return tokens[position - 1]

    def primary():
        token = take()
        if token == "(":
            value = conjunction()
            require(take() == ")", f"unbalanced {conjunct!r}")
            return value
        if token[0].isdigit():
            return int(token, 0)
        require(symbols.get(token) is not None,
                f"symbol {token} is missing or ambiguous")
        return symbols[token]

    def difference():
        value = primary()
        while position < len(tokens) and tokens[position] == "-":
            take()
            value -= primary()
        return value

    def conjunction():
        value = difference()
        while position < len(tokens) and tokens[position] == "&":
            take()
            value &= difference()
        return value

    left = difference()
    operator = take()
    right = difference()
    require(position == len(tokens), f"trailing tokens in {conjunct!r}")
    outcomes = {"==": left == right, "<=": left <= right, ">=": left >= right,
                "<": left < right, ">": left > right}
    require(operator in outcomes, f"unknown comparison in {conjunct!r}")
    return outcomes[operator]


def b6_layout(lds_path):
    """The accepted PHDRS and ASSERT conjuncts with B6's counted changes."""
    data = open(lds_path, "rb").read()
    require(sha256(data) == ACCEPTED_LDS_SHA256,
            f"{lds_path} is not the accepted R5 linker script")
    text = strip_comments(data.decode())
    phdrs = parse_phdrs(text)
    accepted = parse_asserts(text)
    require(len(accepted) == ACCEPTED_CONJUNCTS,
            f"parsed {len(accepted)} ASSERT conjuncts, expected "
            f"{ACCEPTED_CONJUNCTS}")
    conjuncts, renamed = [], 0
    for conjunct in accepted:
        if "be_r5_trap_vector" in conjunct:
            conjuncts.append(conjunct.replace("be_r5_trap_vector",
                                              "be_b6_trap_vector"))
            renamed += 1
        else:
            conjuncts.append(conjunct)
    require(renamed == TRAP_VECTOR_CONJUNCTS, f"renamed={renamed}")
    return phdrs + [POOL_PHDR], conjuncts, POOL_CONJUNCTS


# -------------------------------------------------------------------- ELF
class Elf:
    def __init__(self, data):
        require(data[:7] == b"\x7fELF\x02\x01\x01", "not little-endian ELF64")
        e_type, e_machine = struct.unpack_from("<HH", data, 16)
        require(e_type == 2 and e_machine == 243, "not a RISC-V ET_EXEC")
        self.data = data
        self.entry, phoff, shoff = struct.unpack_from("<QQQ", data, 24)
        phentsize, phnum, shentsize, shnum, shstrndx = struct.unpack_from(
            "<HHHHH", data, 54)
        self.segments = []
        self.program_types = []
        for index in range(phnum):
            (p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz,
             _align) = struct.unpack_from("<IIQQQQQQ", data,
                                          phoff + index * phentsize)
            self.program_types.append(p_type)
            if p_type == 1:  # PT_LOAD
                self.segments.append((p_vaddr, p_paddr, p_offset, p_filesz,
                                      p_memsz, p_flags))
        sections = [struct.unpack_from("<IIQQQQIIQQ", data,
                                       shoff + index * shentsize)
                    for index in range(shnum)]
        names = sections[shstrndx][4]
        self.sections = {}
        for section in sections:
            end = data.index(b"\0", names + section[0])
            self.sections[data[names + section[0]:end].decode()] = section
        self.symbols = {}
        self.functions = []
        self.undefined = []
        for section in sections:
            if section[1] != 2:  # SHT_SYMTAB
                continue
            sym_offset, sym_size, sym_link = section[4], section[5], section[6]
            strtab = sections[sym_link][4]
            for entry in range(sym_offset, sym_offset + sym_size, 24):
                st_name, st_info, _, st_shndx, value, size = \
                    struct.unpack_from("<IBBHQQ", data, entry)
                end = data.index(b"\0", strtab + st_name)
                name = data[strtab + st_name:end].decode()
                if name and st_shndx == 0:
                    self.undefined.append(name)
                if not name or name.startswith("$") or st_shndx == 0:
                    continue
                # A name defined twice (two local statics) is unusable.
                self.symbols[name] = value if self.symbols.get(
                    name, value) == value else None
                if st_info & 0xF == 2 and size:  # STT_FUNC
                    self.functions.append((value, size, name))

    def section_bytes(self, name):
        section = self.sections.get(name)
        if section is None or section[1] == 8:  # absent or SHT_NOBITS
            return b""
        return self.data[section[4]:section[4] + section[5]]

    def architecture(self):
        """Tag_RISCV_arch from .riscv.attributes, or None."""
        attributes = self.section_bytes(".riscv.attributes")
        start = attributes.find(b"rv64")
        if start < 0:
            return None
        return attributes[start:attributes.index(b"\0", start)].decode()


def instructions(flat, start, end, base):
    """Decode [start, end) as RISC-V instructions: [(pc, size, word)]."""
    decoded, pc = [], start
    while pc < end:
        offset = pc - base
        require(0 <= offset and offset + 2 <= len(flat),
                f"instruction at 0x{pc:x} is outside the image")
        half = struct.unpack_from("<H", flat, offset)[0]
        if half & 3 == 3:
            require(pc + 4 <= end, f"instruction at 0x{pc:x} crosses its end")
            decoded.append((pc, 4, struct.unpack_from("<I", flat, offset)[0]))
            pc += 4
        else:
            decoded.append((pc, 2, half))
            pc += 2
    return decoded


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def system_kind(word):
    """Classify one 32-bit SYSTEM-opcode word, or None."""
    if word & 0x707F == FENCE_I:
        return "fence.i"
    if word & 0x7F != 0x73:
        return None
    funct3 = (word >> 12) & 7
    if funct3 == 0:
        if word == 0x00000073:
            return "ecall"
        if word == 0x00100073:
            return "ebreak"
        if word == 0x10200073:
            return "sret"
        if word == 0x30200073:
            return "mret"
        if word == 0x10500073:
            return "wfi"
        funct7 = word >> 25
        if word & 0x7FFF == 0x73 and funct7 == 0x09:
            return "sfence.vma"
        if word & 0x7FFF == 0x73 and funct7 == 0x31:
            return "hfence.gvma"
        if word & 0x7FFF == 0x73 and funct7 == 0x11:
            return "hfence.vvma"
        return "system-other"
    if funct3 == 4:
        return "hlsv"
    return "csr"


def csr_write(word):
    """The CSR number a CSR instruction writes, or None for a pure read."""
    funct3 = (word >> 12) & 7
    source = (word >> 15) & 0x1F
    if funct3 in (1, 5) or source != 0:
        return word >> 20
    return None


def floating_point(word, size):
    """Whether a word is an F, D, or V instruction (RV64 encodings)."""
    if size == 4:
        return word & 0x7F in (0x07, 0x27, 0x43, 0x47, 0x4B, 0x4F, 0x53,
                               0x57)
    quadrant, funct3 = word & 3, (word >> 13) & 7
    return quadrant in (0, 2) and funct3 in (1, 5)


CALLER_SAVED = (1, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 28, 29, 30, 31)


def decode(word, size, pc):
    """The accepted R5 checker's word decoder (tests/r5/check-image.mjs).

    Keys: rd, base and offset (an address formed from a base register),
    value (an auipc result), jump/branch targets, call, stop, indirect,
    narrow, and unknown.
    """
    def field(high, low):
        return (word >> low) & ((1 << (high - low + 1)) - 1)

    if size == 4:
        rd, funct3, base = field(11, 7), field(14, 12), field(19, 15)
        offset = signed(word >> 20, 12)
        opcode = word & 0x7F
        if opcode == 0x17:
            return {"rd": rd, "value": pc + signed(word & 0xFFFFF000, 32)}
        if opcode == 0x37:
            return {"rd": rd}
        if opcode == 0x6F:
            target = pc + signed(field(31, 31) << 20 | field(19, 12) << 12 |
                                 field(20, 20) << 11 | field(30, 21) << 1, 21)
            return {"rd": rd, "jump": target, "call": rd != 0,
                    "stop": rd == 0}
        if opcode == 0x67:
            return {"rd": rd, "base": base, "offset": offset,
                    "indirect": True, "call": rd != 0, "stop": rd == 0}
        if opcode == 0x63:
            return {"branch": pc + signed(field(31, 31) << 12 |
                                          field(7, 7) << 11 |
                                          field(30, 25) << 5 |
                                          field(11, 8) << 1, 13)}
        if opcode == 0x03:
            return {"rd": rd, "base": base, "offset": offset}
        if opcode == 0x23:
            return {"base": base,
                    "offset": signed(field(31, 25) << 5 | field(11, 7), 12)}
        if opcode == 0x2F:
            return {"rd": rd, "base": base, "offset": 0}
        if opcode == 0x13:
            return {"rd": rd, "base": base, "offset": offset} \
                if funct3 == 0 else {"rd": rd}
        if opcode == 0x1B:
            return {"rd": rd, "base": base, "offset": offset,
                    "narrow": True} if funct3 == 0 else {"rd": rd}
        if opcode in (0x33, 0x3B):
            return {"rd": rd}
        if opcode == 0x0F:
            return {}
        if opcode == 0x73:
            if funct3 == 0:
                return {"call": word == 0x73,
                        "stop": word in (0x10200073, 0x30200073)}
            return {"rd": rd}
        return {"unknown": True}
    rd, rs2 = field(11, 7), field(6, 2)
    rdc, rs1c = 8 + field(4, 2), 8 + field(9, 7)
    scaled4 = field(12, 10) << 3 | field(6, 6) << 2 | field(5, 5) << 6
    scaled8 = field(12, 10) << 3 | field(6, 5) << 6
    kind = (word & 3) << 3 | field(15, 13)
    if kind == 0:
        return {"rd": rdc, "base": 2, "offset": field(10, 7) << 6 |
                field(12, 11) << 4 | field(5, 5) << 3 | field(6, 6) << 2} \
            if word else {"unknown": True}
    if kind == 2:
        return {"rd": rdc, "base": rs1c, "offset": scaled4}
    if kind == 3:
        return {"rd": rdc, "base": rs1c, "offset": scaled8}
    if kind == 6:
        return {"base": rs1c, "offset": scaled4}
    if kind == 7:
        return {"base": rs1c, "offset": scaled8}
    if kind == 8:
        return {"rd": rd, "base": rd,
                "offset": signed(field(12, 12) << 5 | rs2, 6)} if rd else {}
    if kind == 9:
        return {"rd": rd, "base": rd,
                "offset": signed(field(12, 12) << 5 | rs2, 6), "narrow": True}
    if kind in (10, 16):
        return {"rd": rd}
    if kind == 11:
        if rd == 2:
            return {"rd": rd, "base": rd, "offset": signed(
                field(12, 12) << 9 | field(4, 3) << 7 | field(5, 5) << 6 |
                field(2, 2) << 5 | field(6, 6) << 4, 10)}
        return {"rd": rd}
    if kind == 12:
        return {"rd": rs1c}
    if kind == 13:
        return {"jump": pc + signed(field(12, 12) << 11 | field(11, 11) << 4 |
                                    field(10, 9) << 8 | field(8, 8) << 10 |
                                    field(7, 7) << 6 | field(6, 6) << 7 |
                                    field(5, 3) << 1 | field(2, 2) << 5, 12),
                "stop": True}
    if kind in (14, 15):
        return {"branch": pc + signed(field(12, 12) << 8 |
                                      field(11, 10) << 3 |
                                      field(6, 5) << 6 | field(4, 3) << 1 |
                                      field(2, 2) << 5, 9)}
    if kind == 18:
        return {"rd": rd, "base": 2, "offset": field(12, 12) << 5 |
                field(6, 4) << 2 | field(3, 2) << 6}
    if kind == 19:
        return {"rd": rd, "base": 2, "offset": field(12, 12) << 5 |
                field(6, 5) << 3 | field(4, 2) << 6}
    if kind == 20:
        if rs2:
            return {"rd": rd} if field(12, 12) else \
                {"rd": rd, "base": rs2, "offset": 0}
        if not rd:
            return {}
        if field(12, 12):
            return {"rd": 1, "base": rd, "offset": 0, "indirect": True,
                    "call": True}
        return {"base": rd, "offset": 0, "indirect": True, "stop": True}
    if kind == 22:
        return {"base": 2, "offset": field(12, 9) << 2 | field(8, 7) << 6}
    if kind == 23:
        return {"base": 2, "offset": field(12, 10) << 3 | field(9, 7) << 6}
    return {"unknown": True}


def references(decoded, owner="function"):
    """Every jal target and auipc-formed address: [(pc, target, link)].

    An auipc result is tracked per register until the register is written,
    a call clobbers it, or control reaches a jump or branch target inside
    the function, where nothing is known. An auipc whose result is never
    used as a base while tracked fails closed: a reference this decoding
    cannot see is rejected rather than missed.
    """
    insns = [(pc, decode(word, size, pc)) for pc, size, word in decoded]
    joins = {insn.get("jump", insn.get("branch")) for _, insn in insns}
    found, state, pending = [], {}, {}
    for pc, insn in insns:
        if pc in joins:
            state.clear()
        if insn.get("jump") is not None:
            found.append((pc, insn["jump"], insn.get("rd", 0)))
        base = insn.get("base")
        if base in state:
            origin, value = state[base]
            pending.pop(origin, None)
            address = value + insn["offset"]
            if insn.get("narrow"):
                address = signed(address & 0xFFFFFFFF, 32)
            if insn.get("indirect"):
                address &= ~1
            found.append((pc, address & 0xFFFFFFFFFFFFFFFF,
                          insn.get("rd", 0) if insn.get("indirect")
                          else None))
        if insn.get("unknown"):
            state.clear()
        state.pop(insn.get("rd"), None)
        if insn.get("call"):
            for register in CALLER_SAVED:
                state.pop(register, None)
        if insn.get("value") is not None and insn.get("rd"):
            state[insn["rd"]] = (pc, insn["value"])
            pending[pc] = insn["rd"]
    require(not pending,
            f"auipc at {', '.join(hex(pc) for pc in sorted(pending))} in "
            f"{owner} is not used as a base while its result is known")
    return found


def function_map(elf, start, end):
    """Function symbols inside [start, end), merged by identical extent."""
    extents = {}
    for value, size, name in elf.functions:
        if start <= value < end:
            require(value + size <= end,
                    f"function {name} leaves monitor text")
            extents.setdefault((value, size), []).append(name)
    ordered = sorted(extents.items())
    for (left, right) in zip(ordered, ordered[1:]):
        require(left[0][0] + left[0][1] <= right[0][0],
                f"functions {left[1]} and {right[1]} overlap")
    return [(value, size, sorted(names)) for (value, size), names in ordered]


def check_padding(flat, base, start, end):
    for pc, size, word in instructions(flat, start, end, base):
        require((size == 4 and word == NOP) or
                (size == 2 and word in (C_NOP, 0)),
                f"instruction 0x{word:x} at 0x{pc:x} is outside every "
                f"function")


# ----------------------------------------------------- value tracking
def track(decoded):
    """Constant and CSR-value tracking over B6's straight-line assembly.

    A register holds ("const", n), ("csr", name, mask), ("arg", "a0"),
    ("arg", "a1"), or ("arg", "a2") (the incoming arguments), or
    nothing known. Returns
    (writes, reads, checks, stores): CSR writes [(index, csr, op, value)]
    with op w, s, or c; CSR reads [(index, csr)]; conditional branches on
    a tracked value [(index, kind, subject, mask, value)], kind "eq" when
    falling through requires equality (bne) and "ne" when it requires
    inequality (beq); and doubleword stores [(index, base, offset, value)].
    State is dropped at every jump or branch target and after any call or
    stop, so a join never carries a value it might not hold.
    """
    joins = set()
    for pc, size, word in decoded:
        insn = decode(word, size, pc)
        for key in ("jump", "branch"):
            if insn.get(key) is not None:
                joins.add(insn[key])
    initial = {0: ("const", 0), 10: ARG_A0, 11: ARG_A1, 12: ARG_A2}
    regs = dict(initial)
    writes, reads, checks, stores = [], [], [], []
    for index, (pc, size, word) in enumerate(decoded):
        if pc in joins:
            regs = {0: ("const", 0)}
        if size != 4:
            regs = {0: ("const", 0)}
            continue
        opcode, rd = word & 0x7F, (word >> 7) & 0x1F
        funct3, rs1, rs2 = (word >> 12) & 7, (word >> 15) & 0x1F, \
            (word >> 20) & 0x1F
        imm = signed(word >> 20, 12)
        result, writes_rd = None, True
        a, b = regs.get(rs1), regs.get(rs2)
        if opcode == 0x37:
            result = ("const", signed(word & 0xFFFFF000, 32) & MASK64)
        elif opcode == 0x17:
            result = ("const", (pc + signed(word & 0xFFFFF000, 32)) & MASK64)
        elif opcode == 0x13:
            if funct3 == 0 and a and a[0] == "const":
                result = ("const", (a[1] + imm) & MASK64)
            elif funct3 == 0 and imm == 0:
                result = a
            elif funct3 == 7 and a and a[0] == "const":
                result = ("const", a[1] & imm & MASK64)
            elif funct3 == 7 and a and a[0] == "csr":
                result = ("csr", a[1], a[2] & imm & MASK64)
            elif funct3 == 1 and word >> 26 == 0 and a and a[0] == "const":
                result = ("const", (a[1] << ((word >> 20) & 0x3F)) & MASK64)
        elif opcode == 0x1B:
            if funct3 == 0 and a and a[0] == "const":
                result = ("const",
                          signed((a[1] + imm) & 0xFFFFFFFF, 32) & MASK64)
        elif opcode == 0x33:
            if funct3 == 7 and word >> 25 == 0:
                for x, y in ((a, b), (b, a)):
                    if x and y and x[0] == "csr" and y[0] == "const":
                        result = ("csr", x[1], x[2] & y[1])
        elif opcode == 0x73 and funct3 not in (0, 4):
            csr = CSR_NAMES.get(word >> 20, f"0x{word >> 20:x}")
            operation = {1: "w", 2: "s", 3: "c"}[funct3 & 3]
            value = ("const", rs1) if funct3 >= 5 else a
            if funct3 in (1, 5) or rs1 != 0:
                writes.append((index, csr, operation, value))
            if rd != 0 or funct3 not in (1, 5):
                reads.append((index, csr))
            result = ("csr", csr, MASK64)
        elif opcode == 0x63:
            writes_rd = False
            kind = {0: "ne", 1: "eq"}.get(funct3)
            for x, y in ((a, b), (b, a)):
                if kind and x and y and x[0] in ("csr", "arg") and \
                        y[0] in ("const", "arg") and x != y:
                    subject = x[1] if x[0] == "csr" else f"arg:{x[1]}"
                    mask = x[2] if x[0] == "csr" else MASK64
                    value = y[1] if y[0] == "const" else f"arg:{y[1]}"
                    checks.append((index, kind, subject, mask, value))
                    break
        elif opcode == 0x23:
            writes_rd = False
            if funct3 == 3:
                stores.append((index, a, signed((word >> 25) << 5 |
                                                (word >> 7) & 0x1F, 12), b))
        elif opcode in (0x6F, 0x67):
            regs = {0: ("const", 0)} if rd == 0 else {
                register: value for register, value in regs.items()
                if register not in CALLER_SAVED}
        elif opcode == 0x73 and word in (0x10200073, 0x30200073):
            regs = {0: ("const", 0)}
            writes_rd = False
        if writes_rd and rd != 0 and opcode not in (0x6F, 0x67):
            if result is None:
                regs.pop(rd, None)
            else:
                regs[rd] = result
    return writes, reads, checks, stores


def function_words(elf, flat, name, base):
    """The decoded instructions of one named function."""
    found = [(value, size) for value, size, label in elf.functions
             if label == name]
    require(len(found) == 1, f"{name} is not one function")
    return instructions(flat, found[0][0], found[0][0] + found[0][1], base)


def check_helpers(elf, flat, base, symbols):
    """The values B6's arm and timer helpers write, and the readback."""
    for name, expected in HELPER_WRITES.items():
        decoded = function_words(elf, flat, name, base)
        writes, reads, _, stores = track(decoded)
        actual = [(csr, operation, value) for _, csr, operation, value
                  in writes]
        for (csr, operation, value), wanted in zip(actual, expected):
            require((csr, operation) == wanted[:2] and value == wanted[2],
                    f"{name}: {csr} written as {value!r}, expected "
                    f"{wanted[2]!r}")
        require(actual == expected,
                f"{name} writes {actual}, expected {expected}")
        if name != B6_ARM:
            continue
        slots = {offset: value[1] for _, base_value, offset, value in stores
                 if base_value == ARG_A0 and value and value[0] == "csr" and
                 value[2] == MASK64}
        require(slots == CONTROL_SLOTS,
                f"{name} reads back {sorted(slots.items())}, expected "
                f"{sorted(CONTROL_SLOTS.items())}")
        order = {csr: index for index, csr, _, _ in reversed(writes)}
        first_read = {csr: index for index, csr in reversed(reads)}
        require(order["vstimecmp"] < first_read["hip"] < order["hideleg"],
                f"{name} does not disarm vstimecmp, then read hip, before "
                f"delegating VSTI")


def check_instructions(elf, flat, base, code_start, code_end, symbols):
    """The ecall/sret/fence/CSR rules over monitor text."""
    functions = function_map(elf, code_start, code_end)
    require(functions, "no function symbols in monitor text")
    cursor = code_start
    sites = {kind: {} for kind in INSTRUCTION_SITES}
    writers = {}
    decoded_all = []
    for value, size, names in functions:
        check_padding(flat, base, cursor, value)
        owner = names[0] if len(names) == 1 else "/".join(names)
        decoded = instructions(flat, value, value + size, base)
        decoded_all.append((owner, decoded))
        for pc, width, word in decoded:
            require(not floating_point(word, width),
                    f"F, D, or V instruction 0x{word:x} at 0x{pc:x} in "
                    f"{owner}")
            if width == 2:
                require(word != 0x9002, f"c.ebreak at 0x{pc:x} in {owner}")
                continue
            kind = system_kind(word)
            if kind is None:
                continue
            require(kind != "system-other",
                    f"unknown SYSTEM word 0x{word:08x} at 0x{pc:x} in "
                    f"{owner}")
            if kind == "csr":
                name = CSR_NAMES.get(word >> 20)
                require(name not in FORBIDDEN_CSRS,
                        f"{owner} accesses {name} at 0x{pc:x}")
                csr = csr_write(word)
                if csr is None:
                    continue
                name = CSR_NAMES.get(csr)
                require(name is not None and name in CSR_WRITERS,
                        f"{owner} writes unlisted CSR 0x{csr:x}")
                writers.setdefault(name, set()).add(owner)
                continue
            sites[kind][owner] = sites[kind].get(owner, 0) + 1
        cursor = value + size
    check_padding(flat, base, cursor, code_end)
    for kind, expected in INSTRUCTION_SITES.items():
        require(sites[kind] == expected,
                f"{kind} sites {sorted(sites[kind].items())} != "
                f"{sorted(expected.items())}")
    for name, expected in CSR_WRITERS.items():
        actual = writers.get(name, set())
        require(actual == expected,
                f"{name} written by {sorted(actual)}, expected "
                f"{sorted(expected)}")
    # Pool addresses, the ecall site's callers, R3 call sites, be_reset.
    pools = ((symbols["__be_root_management_start"],
              symbols["__be_root_protected_end"], ROOT_POOL_USERS,
              "a G-stage root pool"),
             (symbols["__be_b6_pool_start"], symbols["__be_b6_pool_end"],
              B6_POOL_USERS, "the B6 G-stage pool"))
    sbi_call = symbols[R3_SBI]
    reset = [(value, size) for value, size, names in functions
             if "be_reset" in names]
    require(len(reset) == 1, "be_reset is not one function")
    callers, reset_targets = set(), set()
    install_sites, forbidden_sites = [], []
    for owner, decoded in decoded_all:
        for pc, target, link in references(decoded, owner):
            for start, end, users, label in pools:
                require(not start <= target <= end or owner in users,
                        f"{owner} names {label} at 0x{pc:x}")
            if target == sbi_call:
                callers.add(owner)
            if target == symbols[R3_INSTALL]:
                install_sites.append((owner, pc))
            if target == symbols[R3_ENTER] or \
                    target == symbols.get(R3_ARM, -1):
                forbidden_sites.append((owner, pc))
            if owner == "be_reset" and link is not None and not \
                    reset[0][0] <= target < reset[0][0] + reset[0][1]:
                reset_targets.add(target)
    require(callers and callers <= PLATFORM_HELPERS,
            f"{R3_SBI} is reached from {sorted(callers)}, not only the "
            f"accepted platform helpers")
    require(len(install_sites) == INSTALL_CALL_SITES and
            {owner for owner, _ in install_sites} <= INSTALL_CALLERS,
            f"install call sites {install_sites}, expected "
            f"{INSTALL_CALL_SITES} in boot code")
    require(not forbidden_sites,
            f"{R3_ENTER} or {R3_ARM} has call sites {forbidden_sites}")
    expected_targets = {symbols[B1_QUIESCE], symbols[B6_MAIN],
                        symbols[R3_HALT]}
    require(reset_targets == expected_targets,
            "be_reset calls or tails something other than be_b1_quiesce, "
            "be_b6_runtime_main, and be_r3_arch_halt")
    by_name = {owner: decoded for owner, decoded in decoded_all}
    check_trap_entry(by_name[B6_VECTOR], symbols)
    resume = [(value, size) for value, size, names in functions
              if B6_RESUME in names][0]
    check_resume(by_name[B6_RESUME], symbols, resume[0],
                 resume[0] + resume[1])
    check_helpers(elf, flat, base, symbols)
    total = sum(len(decoded) for _, decoded in decoded_all)
    return len(functions), total


def store_fields(word):
    """(source, base, offset) of an sd, or None."""
    if word & 0x707F != 0x3023:
        return None
    return ((word >> 20) & 0x1F, (word >> 15) & 0x1F,
            signed((word >> 25) << 5 | (word >> 7) & 0x1F, 12))


def load_fields(word):
    """(destination, base, offset) of an ld, or None."""
    if word & 0x707F != 0x3003:
        return None
    return (word >> 7) & 0x1F, (word >> 15) & 0x1F, signed(word >> 20, 12)


def check_structure(elf):
    """The accepted R5 checker's structure rules, moved to the K3 base."""
    require(3 not in elf.program_types, "image requests an interpreter")
    require(2 not in elf.program_types, "image carries a dynamic segment")
    for name, section in elf.sections.items():
        require(section[1] not in (4, 9),
                f"image carries relocations ({name})")
    require(not elf.undefined,
            f"unresolved symbols: {sorted(set(elf.undefined))}")
    architecture = elf.architecture()
    require(architecture is not None, "missing RISC-V architecture attributes")
    for part in ("_h1p0", "_zicsr2p0", "_zifencei2p0"):
        require(part in architecture, f"ELF attributes omit {part}")
    for pattern in (r"_f\d", r"_d\d", r"_v\d"):
        require(re.search(pattern, architecture) is None,
                f"ELF attributes include {pattern}")
    for name in elf.symbols:
        require(re.search(r"(^|_)r6(_|$)|be_r6", name, re.I) is None,
                f"hidden R6 symbol {name}")
    for name, (address, size, required, forbidden) in \
            EXPECTED_SECTIONS.items():
        section = elf.sections.get(name)
        require(section is not None, f"missing section {name}")
        have = {"W": section[2] & SHF_WRITE, "A": section[2] & SHF_ALLOC,
                "X": section[2] & SHF_EXECINSTR}
        if address is not None:
            require(section[3] == address + DELTA, f"{name} address moved")
        if size is not None:
            require(section[5] == size, f"{name} size changed")
        for flag in required:
            require(have[flag], f"{name} lost flag {flag}")
        for flag in forbidden:
            require(not have[flag], f"{name} gained flag {flag}")
    require(elf.sections[".gstage.root.b6"][1] == 8,  # SHT_NOBITS
            "the B6 pool is not NOLOAD")
    require(elf.sections[".monitor.text"][5] <= 0x8000,
            "monitor text outgrew its reserved window")
    data = elf.sections[".monitor.data"]
    require(data[3] + data[5] <= 0x8020F000 + DELTA,
            "monitor data overruns the diagnostic page")
    return architecture


def check_trap_entry(decoded, symbols):
    """Sscratch pivot, the whole record, SPV, and the dispatch call."""
    require(all(size == 4 for _, size, _ in decoded),
            "trap entry holds a compressed instruction")
    words = [word for _, _, word in decoded]
    require(words[0] == CSRRW_SP_SSCRATCH_SP,
            "trap entry does not first exchange sp with sscratch")
    stores = {fields for fields in map(store_fields, words) if fields}
    frame = 5  # t0 holds the saved page
    for number in range(1, 32):
        offset = (number - 1) * 8
        if number in (2, 5, 6):  # sp, t0, t1 arrive through scratch
            saved = any(base == frame and at == offset
                        for _, base, at in stores)
        else:
            saved = (number, frame, offset) in stores
        require(saved, f"trap entry does not save x{number} at {offset}")
    _, _, checks, tracked = track(decoded)
    saved_page = ("const", symbols["__be_saved_management_start"])
    stored = {(offset, value[1]) for _, base, offset, value in tracked
              if base == saved_page and value and value[0] == "csr" and
              value[2] == MASK64}
    words_after = [(name, FRAME_TRAP_CSRS + index * 8)
                   for index, name in enumerate(TRAP_CSRS)] + \
        list(EXIT_WORDS)
    for name, offset in words_after:
        require((offset, name) in stored,
                f"trap entry does not store {name} at {offset}")
    require((0, frame, FRAME_RESERVED) in stores,
            "trap entry does not seal the reserved frame word")
    require([check[1:] for check in checks] ==
            [("ne", "hstatus", HSTATUS_SPV, 0)],
            f"trap entry does not fail closed on hstatus.SPV: {checks}")
    require(any(target == symbols[B6_DISPATCH] and link == 1
                for _, target, link in references(decoded)),
            "trap entry does not call be_b6_dispatch")


def resume_checks(symbols):
    """Every check the resume tail must make, and nothing else."""
    return {
        ("eq", "arg:a0", MASK64, symbols["__be_saved_management_start"]),
        ("eq", "satp", MASK64, 0),
        ("eq", "stvec", MASK64, symbols[B6_VECTOR]),
        ("eq", "sscratch", MASK64, symbols["__be_stack_management_end"]),
        ("eq", "sie", MASK64, 0),
        ("eq", "sstatus", 0xDE722, 0x100),
        ("eq", "hstatus", 0x73F380, 0x180),
        ("eq", "hedeleg", MASK64, "arg:a2"),
        ("eq", "hideleg", MASK64, 0x40),
        ("eq", "hie", MASK64 & ~0x40, 0),
        ("eq", "hvip", MASK64, 0),
        ("eq", "hcounteren", MASK64, 0x2),
        ("eq", "htimedelta", MASK64, 0),
        ("eq", "henvcfg", MASK64, 1 << 63),
        ("eq", "hgeie", MASK64, 0),
        ("eq", "hgatp", MASK64, "arg:a1"),
    }


def check_resume(decoded, symbols, start, end):
    """Call free; sepc and the GPRs; one SRET; the plan's checks."""
    require(all(size == 4 for _, size, _ in decoded),
            "resume tail holds a compressed instruction")
    words = [word for _, _, word in decoded]
    loads = [load_fields(word) for word in words]
    frame = 31  # t6 holds the saved page
    for number in range(1, 32):
        require((number, frame, (number - 1) * 8) in loads,
                f"resume tail does not restore x{number} from the frame")
    sepc = [index for index, fields in enumerate(loads)
            if fields and fields[1:] == (frame, FRAME_SEPC)]
    require(len(sepc) == 1 and index_writes(words, sepc[0] + 1, 0x141,
                                            loads[sepc[0]][0]),
            "resume tail does not restore sepc from the frame")
    terminal = symbols[B6_TERMINAL]
    pairs = {pc: (target, link)
             for pc, target, link in references(decoded, B6_RESUME)}
    for pc, _, word in decoded:
        opcode = word & 0x7F
        if opcode == 0x63:
            offset = (word >> 31) << 12 | ((word >> 7) & 1) << 11 | \
                ((word >> 25) & 0x3F) << 5 | ((word >> 8) & 0xF) << 1
            target = pc + signed(offset, 13)
            require(start <= target < end,
                    f"resume tail branches out at 0x{pc:x}")
        elif opcode == 0x6F:
            require((word >> 7) & 0x1F == 0 and
                    start <= pairs[pc][0] < end,
                    f"resume tail calls or jumps out at 0x{pc:x}")
        elif opcode == 0x67:
            require((word >> 7) & 0x1F == 0 and pc in pairs and
                    pairs[pc][0] == terminal,
                    f"resume tail leaves other than to the terminal at "
                    f"0x{pc:x}")
    srets = [index for index, word in enumerate(words) if word == 0x10200073]
    last_load = max(index for index, fields in enumerate(loads) if fields)
    require(len(srets) == 1 and srets[0] == last_load + 1,
            "resume tail does not end its GPR restore in its one SRET")
    writes, reads, checks, _ = track(decoded)
    require([(csr, operation, value) for _, csr, operation, value in writes]
            == [("sstatus", "s", ("const", 0x100)), ("sepc", "w", None)],
            "resume tail does not set sstatus SPP exactly once and then "
            "only sepc")
    found = {check[1:] for check in checks}
    wanted = resume_checks(symbols)
    require(len(checks) == len(found) and found == wanted,
            f"resume checks differ: missing "
            f"{sorted(map(str, wanted - found))}, extra "
            f"{sorted(map(str, found - wanted))}")
    require("vsatp" not in {csr for _, csr in reads},
            "resume tail reads vsatp, which the guest owns")


def index_writes(words, index, csr, register):
    """Whether words[index] writes csr from register."""
    if index >= len(words):
        return False
    word = words[index]
    return system_kind(word) == "csr" and csr_write(word) == csr and \
        (word >> 15) & 0x1F == register and (word >> 12) & 7 == 1


def call_target(flat, offset, pc):
    """Target of an auipc ra / jalr ra pair at offset, or None."""
    auipc, jalr = struct.unpack_from("<II", flat, offset)
    if auipc & 0xFFF != 0x097 or jalr & 0xFFFFF != 0x080E7:
        return None
    return pc + signed(auipc & 0xFFFFF000, 32) + signed(jalr >> 20, 12)


def check_layout(elf, flat, base, layout):
    phdrs, conjuncts, pool_conjuncts = layout
    require(elf.entry == base, f"entry 0x{elf.entry:x} != base 0x{base:x}")
    require(elf.symbols.get("be_reset") == base, "be_reset is not the base")
    require(len(elf.segments) == len(phdrs),
            f"{len(elf.segments)} PT_LOAD segments, expected {len(phdrs)}")
    require(len(flat) == SPAN,
            f"flat image is 0x{len(flat):x} bytes, not 0x{SPAN:x}")
    covered = bytearray(SPAN)
    previous_end = base
    for (vaddr, paddr, offset, filesz, memsz, flags), (name, wanted) in zip(
            elf.segments, phdrs):
        require(vaddr == paddr, f"{name} 0x{vaddr:x} has paddr 0x{paddr:x}")
        require(not (flags & PF_W and flags & PF_X),
                f"{name} 0x{paddr:x} is writable and executable")
        require(flags == wanted, f"{name} flags {flags} != expected {wanted}")
        if (name, wanted) == POOL_PHDR:
            require(paddr == POOL and memsz == POOL_BYTES and filesz == 0,
                    f"B6 pool segment 0x{paddr:x}+0x{memsz:x} (file "
                    f"0x{filesz:x}) is not NOLOAD 0x{POOL_BYTES:x} bytes at "
                    f"0x{POOL:x}")
            continue
        require(previous_end <= paddr and paddr + memsz <= base + SPAN,
                f"{name} 0x{paddr:x}+0x{memsz:x} is out of order or leaves "
                f"the span")
        start = paddr - base
        require(flat[start:start + filesz] ==
                elf.data[offset:offset + filesz],
                f"flat image differs from {name} at 0x{paddr:x}")
        covered[start:start + filesz] = b"\1" * filesz
        previous_end = paddr + memsz
    require(all(byte == 0 for byte, inside in zip(flat, covered)
                if not inside),
            "flat image has nonzero bytes outside the loaded segments")
    moved = {name: None if value is None else value - DELTA
             for name, value in elf.symbols.items()}
    for conjunct in conjuncts:
        require(evaluate(conjunct, moved),
                f"ASSERT fails at +0x{DELTA:x}: {conjunct}")
    for conjunct in pool_conjuncts:
        require(evaluate(conjunct, elf.symbols),
                f"B6 pool ASSERT fails: {conjunct}")


def check_pages(toolchain, flat):
    """Both guest pages are B2's: the inert R5 fixtures."""
    for name, page in (("management", CODE_PAGE),
                       ("protected", PROTECTED_PAGE)):
        require(sha256(flat[page:page + PAGE]) ==
                B2_PAGE_SHA256[(toolchain, page)],
                f"{name} page differs from B2's")


def payload_constants(elf, flat, base):
    """struct be_b6_payload_layout as linked into the monitor."""
    address = elf.symbols.get(B6_LAYOUT_SYMBOL)
    require(address is not None and base <= address and
            address + 56 <= base + len(flat),
            f"{B6_LAYOUT_SYMBOL} is not in the flat image")
    names = ("staging_hpa", "kernel_offset", "kernel_bytes",
             "kernel_image_size", "dtb_offset", "dtb_bytes", "image_bytes")
    return dict(zip(names, struct.unpack_from("<7Q", flat, address - base)))


def check_monitor(toolchain, elf_data, flat, base, layout, map_text=None):
    elf = Elf(elf_data)
    symbols = elf.symbols
    architecture = check_structure(elf)
    if map_text is not None:
        for section in MAP_SECTIONS:
            require(section in map_text, f"link map lacks {section}")
    for name in REQUIRED_SYMBOLS:
        require(symbols.get(name) is not None, f"symbol {name} is missing")
    for name in symbols:
        require(not name.startswith("be_r4_"),
                f"R4 mechanism symbol {name} is linked")
        require(not name.startswith("be_r5_") or name in ALLOWED_R5_SYMBOLS,
                f"R5 mechanism symbol {name} is linked")
    check_layout(elf, flat, base, layout)
    code_start = symbols["__be_monitor_code_start"]
    code_end = symbols["__be_monitor_code_end"]
    require(code_end <= MONITOR_TEXT_LIMIT, "monitor text overflow")
    require(symbols["__be_bss_end"] <= MONITOR_DATA_LIMIT,
            "monitor data overflow")
    quiesce = symbols[B1_QUIESCE]
    require(code_start <= quiesce < code_end,
            "be_b1_quiesce is outside monitor text")
    require(call_target(flat, 0, base) == quiesce,
            "be_reset does not first call be_b1_quiesce")
    require(struct.unpack_from("<I", flat, 8)[0] == RISCV_MV_S0_A0,
            "the accepted be_reset sequence does not follow the call")
    for name, (size, digest) in B2_R3_FUNCTIONS[toolchain].items():
        function = [(value, length) for value, length, label in elf.functions
                    if label == name]
        require(len(function) == 1 and function[0][1] == size,
                f"{name} is not one function of 0x{size:x} bytes")
        start = function[0][0] - base
        require(sha256(flat[start:start + size]) == digest,
                f"{name} differs from B2's")
    functions, words = check_instructions(elf, flat, base, code_start,
                                          code_end, symbols)
    check_pages(toolchain, flat)
    return {
        "architecture": architecture,
        "text_end": code_end,
        "data_end": symbols["__be_bss_end"],
        "functions": functions,
        "instructions": words,
        "payload": payload_constants(elf, flat, base),
        "elf": elf,
    }


# ----------------------------------------------------------- guest inputs
def read_pins(path):
    """guest/pins.txt: {file name: (sha256, bytes)} and the kernel facts."""
    files, kernel = {}, {}
    for number, line in enumerate(pathlib.Path(path).read_text(
            encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"file (\S+) sha256=([0-9a-f]{64}) "
                             r"bytes=([0-9]+)", line)
        if match:
            files[match.group(1)] = (match.group(2), int(match.group(3)))
            continue
        match = re.fullmatch(r"kernel (image_size|text_offset)=(0x[0-9a-f]+)",
                             line)
        if match:
            kernel[match.group(1)] = int(match.group(2), 16)
    for name in ("Image", "b6-guest.dtb") + tuple(
            f"b6-guest-{variant}.dtb" for variant in DTB_VARIANTS):
        require(name in files, f"{path} has no pin for {name}")
    require(set(kernel) == {"image_size", "text_offset"},
            f"{path} lacks the kernel image_size or text_offset pin")
    return files, kernel


def kernel_facts(kernel):
    """An independent RISC-V Image header reader: (bytes, image_size)."""
    require(len(kernel) >= 64, "kernel is shorter than its header")
    (_, _, text_offset, image_size, flags, _, _, _, magic, magic2,
     _) = struct.unpack_from("<IIQQQIIQ8s4sI", kernel)
    require(magic == b"RISCV\0\0\0", f"kernel magic {magic!r}")
    require(magic2 == b"RSC\x05", f"kernel magic2 {magic2!r}")
    require(text_offset == LAYOUT["KERNEL_TEXT_OFFSET"],
            f"kernel text_offset 0x{text_offset:x}")
    require(flags & 1 == 0, "kernel is big-endian")
    require(len(kernel) <= LAYOUT["KERNEL_FILE_MAX"],
            f"kernel file 0x{len(kernel):x} exceeds its budget")
    require(len(kernel) <= image_size <= LAYOUT["KERNEL_IMAGE_SIZE_MAX"],
            f"kernel image_size 0x{image_size:x} is below the file or over "
            f"its budget")
    require(LAYOUT["KERNEL_GPA"] + image_size <= LAYOUT["DTB_GPA"],
            "kernel span reaches the DTB slot")
    return len(kernel), image_size


def parse_fdt(blob):
    """An FDT reader: (reserve-map entries, {path: {property: bytes}})."""
    require(len(blob) >= 40, "DTB is shorter than its header")
    (magic, total, off_struct, off_strings, off_rsvmap, version, _, _,
     size_strings, size_struct) = struct.unpack_from(">10I", blob)
    require(magic == FDT_MAGIC, f"DTB magic 0x{magic:x}")
    require(total == len(blob) == DTB_BYTES,
            f"DTB totalsize 0x{total:x}, file 0x{len(blob):x}")
    require(version == 17, f"DTB version {version}")
    for offset, size in ((off_struct, size_struct),
                         (off_strings, size_strings), (off_rsvmap, 16)):
        require(40 <= offset and offset + size <= total,
                "DTB block leaves the blob")
    reserved, at = [], off_rsvmap
    while True:
        address, size = struct.unpack_from(">QQ", blob, at)
        if address == 0 and size == 0:
            break
        reserved.append((address, size))
        at += 16
    nodes, path, at = {}, [], off_struct
    end = off_struct + size_struct
    while at < end:
        token = struct.unpack_from(">I", blob, at)[0]
        at += 4
        if token == 1:  # FDT_BEGIN_NODE
            name_end = blob.index(b"\0", at)
            path.append(blob[at:name_end].decode("ascii"))
            at = align_up(name_end + 1, 4)
            key = "/" + "/".join(path[1:])
            require(key not in nodes, f"DTB node {key} appears twice")
            nodes[key] = {}
        elif token == 2:  # FDT_END_NODE
            require(path, "DTB ends a node it never began")
            path.pop()
        elif token == 3:  # FDT_PROP
            length, name_offset = struct.unpack_from(">II", blob, at)
            at += 8
            name_end = blob.index(b"\0", off_strings + name_offset)
            name = blob[off_strings + name_offset:name_end].decode("ascii")
            require(path, f"DTB property {name} outside a node")
            nodes["/" + "/".join(path[1:])][name] = blob[at:at + length]
            at = align_up(at + length, 4)
        elif token == 4:  # FDT_NOP
            continue
        elif token == 9:  # FDT_END
            break
        else:
            raise ImageError(f"DTB token 0x{token:x}")
    require(not path, "DTB leaves a node open")
    return reserved, nodes


def strings(*values):
    return b"".join(value.encode("ascii") + b"\0" for value in values)


def cells(*values):
    return b"".join(struct.pack(">I", value) for value in values)


def dt_contract(variant=None):
    """The plan's device tree, with one DTB variant's change."""
    gpa, size = LAYOUT["GUEST_GPA"], LAYOUT["GUEST_BYTES"]
    bootargs, isa = BOOTARGS, ISA_EXTENSIONS
    if variant == "memory":
        size *= 2
    elif variant in ("init-exit", "rdcycle"):
        bootargs += " rdinit=/" + \
            ("init-exit" if variant == "init-exit" else "init-rdcycle")
    elif variant == "sbi-time":
        isa = tuple(name for name in isa if name != "sstc")
    return {
        "/": {"#address-cells": cells(2), "#size-cells": cells(2),
              "compatible": strings("beryllium,k3-b6-guest"),
              "model": strings("Beryllium K3 B6 guest")},
        "/chosen": {"bootargs": strings(bootargs)},
        "/cpus": {"#address-cells": cells(1), "#size-cells": cells(0),
                  "timebase-frequency": cells(LAYOUT["TIMEBASE_HZ"])},
        "/cpus/cpu@0": {"device_type": strings("cpu"), "reg": cells(0),
                        "compatible": strings("riscv"),
                        "mmu-type": strings("riscv,sv39"),
                        "riscv,isa-base": strings("rv64i"),
                        "riscv,isa-extensions": strings(*isa)},
        "/cpus/cpu@0/interrupt-controller": {
            "compatible": strings("riscv,cpu-intc"),
            "interrupt-controller": b"", "#interrupt-cells": cells(1)},
        f"/memory@{gpa:x}": {"device_type": strings("memory"),
                             "reg": cells(gpa >> 32, gpa & 0xFFFFFFFF,
                                          size >> 32, size & 0xFFFFFFFF)},
    }


def check_dt(blob, variant=None):
    """The DT contract: these nodes and properties exactly, no reserve."""
    reserved, nodes = parse_fdt(blob)
    require(not reserved, f"DTB reserves memory: {reserved}")
    wanted = dt_contract(variant)
    require(set(nodes) == set(wanted),
            f"DTB nodes {sorted(nodes)} != {sorted(wanted)}")
    for path, properties in wanted.items():
        for name, value in properties.items():
            have = nodes[path].get(name)
            label = "memory node" if path.startswith("/memory") else \
                f"{path} {name}"
            require(have == value, f"DTB {label} is {have!r}, expected "
                    f"{value!r}")
        require(set(nodes[path]) == set(properties),
                f"DTB {path} has properties {sorted(nodes[path])}")


# ------------------------------------------------------------- boot image
def load_b3():
    spec = importlib.util.spec_from_file_location("check_b3_image",
                                                  B3_CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_ranges(image_size):
    """The five ranges pairwise disjoint and inside S-mode RAM."""
    fdt = align_up(STAGING + image_size, LAYOUT["KEXEC_FDT_ALIGN"])
    ranges = (("the monitor image", BASE, SPAN),
              ("the pool", POOL, POOL_BYTES),
              ("the staged image", STAGING, image_size),
              ("the kexec FDT slot", fdt, LAYOUT["KEXEC_FDT_MAX"]),
              ("the window", WINDOW, WINDOW_BYTES))
    for index, (name, start, size) in enumerate(ranges):
        require(SMODE_RAM[0] <= start and start + size <= SMODE_RAM[1],
                f"{name} 0x{start:x}+0x{size:x} leaves S-mode RAM")
        for other, other_start, other_size in ranges[index + 1:]:
            require(not (start < other_start + other_size and
                         other_start < start + size),
                    f"{other} 0x{other_start:x}+0x{other_size:x} overlaps "
                    f"{name} 0x{start:x}+0x{size:x}")


def boot_parts(data, kernel_bytes):
    """(flat, kernel, gap, dtb) of a boot image, by the layout rules."""
    dtb_offset = align_up(KERNEL_OFFSET + kernel_bytes, PAGE)
    require(len(data) == dtb_offset + DTB_BYTES,
            f"boot image is 0x{len(data):x} bytes, not the DTB's end "
            f"0x{dtb_offset + DTB_BYTES:x}")
    return (data[MONITOR_OFFSET:MONITOR_OFFSET + SPAN],
            data[KERNEL_OFFSET:KERNEL_OFFSET + kernel_bytes],
            data[KERNEL_OFFSET + kernel_bytes:dtb_offset],
            data[dtb_offset:])


def check_boot(data, text_offset, flat, pins, kernel_expect, dtb_name,
               variant=None):
    """B3's header and descriptor, the ranges, and the placed payload."""
    b3 = load_b3()
    files, kernel_pins = pins
    findings = []
    header = b3.check_header(data, text_offset, findings)
    image_size = header["image_size"] if header else len(data)
    check_ranges(image_size)
    require(not findings, "; ".join(findings))
    b3.check_descriptor(data, findings)
    for template in b3.TEMPLATES:
        if data[:b3.STUB_PAGE].count(template) != 1:
            findings.append("a B3 report-line template is missing")
    require(not findings, "; ".join(findings))
    require(len(data) <= LAYOUT["BOOT_IMAGE_MAX"],
            f"boot image 0x{len(data):x} exceeds its budget")
    image_pin, image_bytes = files["Image"]
    monitor, kernel, gap, dtb = boot_parts(data, image_bytes)
    require(monitor == flat, "flat image at 0x1000 differs from the monitor")
    require(not any(gap), "bytes between the kernel and the DTB")
    check_dt(dtb, variant if variant in DTB_VARIANTS else None)
    require(sha256(dtb) == files[dtb_name][0], f"DTB differs from {dtb_name}")
    if variant == "payload":
        require(kernel[KERNEL_MAGIC2_AT] == 0 and
                kernel[:KERNEL_MAGIC2_AT] ==
                kernel_expect[:KERNEL_MAGIC2_AT] and
                kernel[KERNEL_MAGIC2_AT + 1:] ==
                kernel_expect[KERNEL_MAGIC2_AT + 1:],
                "payload variant kernel is not the pinned kernel with "
                "magic2 RSC\\0")
    else:
        size, image_size_field = kernel_facts(kernel)
        require(size == image_bytes and sha256(kernel) == image_pin,
                "kernel differs from its pin")
        require(image_size_field == kernel_pins["image_size"],
                "kernel image_size differs from its pin")
    require(kernel_expect is None or sha256(kernel_expect) == image_pin,
            "the --kernel file differs from its pin")
    return {"image_size": image_size, "kernel_bytes": image_bytes,
            "kernel_image_size": kernel_pins["image_size"],
            "dtb_offset": KERNEL_OFFSET + len(kernel) + len(gap)}


def check_payload_constants(constants, boot):
    """The monitor's link-time payload layout equals the boot image's."""
    kernel = boot["kernel_bytes"]
    expected = {"staging_hpa": STAGING, "kernel_offset": KERNEL_OFFSET,
                "kernel_bytes": kernel,
                "kernel_image_size": boot["kernel_image_size"],
                "dtb_offset": boot["dtb_offset"], "dtb_bytes": DTB_BYTES,
                "image_bytes": boot["image_size"]}
    for name, value in expected.items():
        require(constants[name] == value,
                f"payload constant {name} 0x{constants[name]:x} != "
                f"0x{value:x}")


def check_boot_elf(elf_data, data, boot):
    """The QEMU boot ELF: linked at L, and its loads are the file."""
    elf = Elf(elf_data)
    require(elf.entry == STAGING, f"boot ELF entry 0x{elf.entry:x} is not L")
    require([flags for *_, flags in elf.segments] == [5, 6, 4, 4],
            "boot ELF PT_LOAD flags are not R-X, RW, R, R")
    image = bytearray(len(data))
    for vaddr, paddr, offset, filesz, memsz, _ in elf.segments:
        require(vaddr == paddr and filesz == memsz and STAGING <= paddr and
                paddr + filesz <= STAGING + len(data),
                f"boot ELF segment 0x{paddr:x} leaves the image")
        image[paddr - STAGING:paddr - STAGING + filesz] = \
            elf.data[offset:offset + filesz]
    require(bytes(image) == data, "boot ELF loads differ from the boot image")
    for name, offset in (("be_b6_guest_kernel", KERNEL_OFFSET),
                         ("be_b6_guest_dtb", boot["dtb_offset"]),
                         ("__be_b3_image_end", len(data))):
        require(elf.symbols.get(name) == STAGING + offset,
                f"boot ELF {name} is not at L+0x{offset:x}")


def check_pic(img_path, data):
    """The second link, when the build left it beside the image."""
    pic = pathlib.Path(img_path).with_name("be-k3-b6-boot-pic.img")
    if pic.is_file():
        require(pic.read_bytes() == data,
                "the second link's image differs")


BOOT_TEXT_OFFSET = LAYOUT["UBOOT_TEXT_OFFSET"]
QEMU_TEXT_OFFSET = LAYOUT["QEMU_TEXT_OFFSET"]


def check_image(toolchain, elf_data, flat, boot_img, pins, kernel, layout,
                map_text=None, boot_elf_data=None, img_path=None):
    """One toolchain's monitor and board boot image, together."""
    report = check_monitor(toolchain, elf_data, flat, BASE, layout, map_text)
    boot = check_boot(boot_img, BOOT_TEXT_OFFSET, flat, pins, kernel,
                      "b6-guest.dtb")
    check_payload_constants(report["payload"], boot)
    if boot_elf_data is not None:
        check_boot_elf(boot_elf_data, boot_img, boot)
    if img_path is not None:
        check_pic(img_path, boot_img)
    return report, boot


def outside(data, reference, allowed):
    """Offsets where data and reference differ outside the allowed spans."""
    require(len(data) == len(reference),
            f"size 0x{len(data):x} differs from the reference's "
            f"0x{len(reference):x}")
    edges = [0]
    for start, size in sorted(allowed):
        edges += [start, start + size]
    edges.append(len(data))
    for start, end in zip(edges[::2], edges[1::2]):
        if data[start:end] != reference[start:end]:
            return next(index for index in range(start, end)
                        if data[index] != reference[index])
    return None


def check_variant(name, boot_elf_data, data, reference, pins, kernel,
                  img_path=None):
    """A negative variant: the boot rules with its change, and no other."""
    require(name in VARIANTS, f"unknown variant {name}")
    flat = data[MONITOR_OFFSET:MONITOR_OFFSET + SPAN]
    dtb_name = f"b6-guest-{name}.dtb" if name in DTB_VARIANTS else \
        "b6-guest.dtb"
    boot = check_boot(data, BOOT_TEXT_OFFSET, flat, pins, kernel, dtb_name,
                      name)
    check_boot_elf(boot_elf_data, data, boot)
    if img_path is not None:
        check_pic(img_path, data)
    if name == "payload":
        allowed = [(KERNEL_OFFSET + KERNEL_MAGIC2_AT, 1)]
    elif name in DTB_VARIANTS:
        allowed = [(boot["dtb_offset"], DTB_BYTES)]
    else:
        offset, reference_key, variant_key = RUN_LIMIT_SLOTS[name]
        address = reference["elf"].symbols[B6_CONTROL_SYMBOL] + offset - BASE
        require(struct.unpack_from("<Q", reference["flat"], address)[0] ==
                LAYOUT[reference_key] and
                struct.unpack_from("<Q", flat, address)[0] ==
                LAYOUT[variant_key],
                f"variant {name} does not hold 0x{LAYOUT[variant_key]:x} "
                f"where the reference holds 0x{LAYOUT[reference_key]:x}")
        allowed = [(MONITOR_OFFSET + address, 8)]
    stray = outside(data, reference["boot"], allowed)
    require(stray is None,
            f"variant {name} differs from the reference at 0x{stray:x}"
            if stray is not None else "")
    require(data != reference["boot"], f"variant {name} is the reference")
    return boot


def check_uimage(name, text_offset, flat, data, pins, kernel, reference):
    """A booti image: the boot rules at its text_offset."""
    check_boot(data, text_offset, flat, pins, kernel, "b6-guest.dtb")
    if text_offset != BOOT_TEXT_OFFSET:
        require(text_offset == QEMU_TEXT_OFFSET,
                f"{name}: text_offset 0x{text_offset:x} places the image "
                f"elsewhere than L under QEMU's booti")
        stray = outside(data, reference["boot"], [(8, 8)])
        require(stray is None,
                f"{name} differs from the reference beyond text_offset "
                f"at 0x{stray:x}" if stray is not None else "")


# ---------------------------------------------------------- mutation test
def patch(elf_data, flat, boot_img, address, value, base):
    """Write value at address in the ELF segment, the flat image, and the
    boot image's copy of it."""
    elf = Elf(bytes(elf_data))
    for vaddr, _, offset, filesz, _, _ in elf.segments:
        if vaddr <= address and address + len(value) <= vaddr + filesz:
            start = offset + address - vaddr
            elf_data[start:start + len(value)] = value
            break
    else:
        raise ImageError(f"0x{address:x} is not in a loaded segment")
    at = address - base
    flat[at:at + len(value)] = value
    boot_img[MONITOR_OFFSET + at:MONITOR_OFFSET + at + len(value)] = value


def function_start(elf, name):
    found = [(value, size) for value, size, label in elf.functions
             if label == name]
    require(len(found) == 1, f"{name} is not one function")
    return found[0]


def nth_word(elf, flat, name, base, index=0):
    """Address of the index-th 32-bit instruction of a function."""
    value, size = function_start(elf, name)
    words = [pc for pc, width, _ in instructions(flat, value, value + size,
                                                 base) if width == 4]
    require(len(words) > index, f"{name} is too short")
    return words[index]


def word_slots(elf, flat, name, base, count):
    """Address of the first run of count adjacent 32-bit instructions."""
    value, size = function_start(elf, name)
    decoded = instructions(flat, value, value + size, base)
    for index in range(len(decoded) - count + 1):
        if all(width == 4 for _, width, _ in decoded[index:index + count]):
            return decoded[index][0]
    raise ImageError(f"no {count} adjacent 32-bit instructions in {name}")


# The resume tail's copy of its third argument, the armed hedeleg
# readback (addi t4, a2, 0), and the mutation's copy of a1 instead.
MV_T4_A2 = 12 << 15 | 29 << 7 | 0x13
MV_T4_A1 = 11 << 15 | 29 << 7 | 0x13


def matching_word(elf, flat, name, base, predicate):
    """Address of the first 32-bit instruction of name that matches."""
    value, size = function_start(elf, name)
    for pc, width, word in instructions(flat, value, value + size, base):
        if width == 4 and predicate(word):
            return pc, word
    raise ImageError(f"{name} has no matching instruction")


def add_immediate(value):
    """addi or addiw with this 12-bit immediate."""
    return lambda word: word & 0x707F in (0x13, 0x1B) and \
        signed(word >> 20, 12) == value


def with_immediate(word, value):
    return word & 0xFFFFF | (value & 0xFFF) << 20


def call_pair(pc, target, register=1):
    """auipc register + jalr ra, register: call target from pc."""
    delta = target - pc
    upper = (delta + 0x800) & ~0xFFF
    lower = delta - upper
    return struct.pack("<II", (upper & 0xFFFFF000) | register << 7 | 0x17,
                       (lower & 0xFFF) << 20 | register << 15 | 1 << 7 |
                       0x67)


def pool_reference(pc, address, register):
    """auipc register + addi register: form address at pc."""
    delta = address - pc
    upper = (delta + 0x800) & ~0xFFF
    lower = delta - upper
    return struct.pack("<II", (upper & 0xFFFFF000) | register << 7 | 0x17,
                       (lower & 0xFFF) << 20 | register << 15 |
                       register << 7 | 0x13)


def mutation_test(toolchain, elf_path, bin_path, boot_path, pins, kernel,
                  layout):
    elf_data = open(elf_path, "rb").read()
    flat = open(bin_path, "rb").read()
    boot_img = open(boot_path, "rb").read()
    check_image(toolchain, elf_data, flat, boot_img, pins, kernel, layout)
    elf = Elf(elf_data)
    symbols = elf.symbols
    word = lambda value: struct.pack("<I", value)  # noqa: E731
    arm_hedeleg, arm_word = matching_word(elf, flat, B6_ARM, BASE,
                                          add_immediate(0x15D))
    resume_hedeleg, _ = matching_word(
        elf, flat, B6_RESUME, BASE, lambda value: value == MV_T4_A2)
    dispatch_slot = word_slots(elf, flat, B6_DISPATCH, BASE, 2)
    spv_test = matching_word(elf, flat, B6_VECTOR, BASE,
                             lambda value: value & 0x707F == 0x7013 and
                             signed(value >> 20, 12) == HSTATUS_SPV)[0]
    monitor = [
        ("hedeleg immediate", arm_hedeleg,
         word(with_immediate(arm_word, 0x15F)), "hedeleg written as"),
        ("resume hedeleg check", resume_hedeleg, word(MV_T4_A1),
         "resume checks differ"),
        ("missing fence.i", symbols[B6_FENCE_I], word(NOP), "fence.i sites"),
        ("extra hfence.vvma", nth_word(elf, flat, B6_RESUME, BASE, 1),
         word(0x22000073), "hfence.vvma sites"),
        ("extra sret", nth_word(elf, flat, B6_RESUME, BASE, 1),
         word(0x10200073), "sret sites"),
        ("extra install call", dispatch_slot,
         call_pair(dispatch_slot, symbols[R3_INSTALL]), "install call sites"),
        ("R3 entry called", dispatch_slot,
         call_pair(dispatch_slot, symbols[R3_ENTER]), "has call sites"),
        ("vector writes hvip", nth_word(elf, flat, B6_VECTOR, BASE, 1),
         word(0x64501073), "hvip written by"),
        ("resume writes vsatp", nth_word(elf, flat, B6_RESUME, BASE, 1),
         word(0x28001073), "vsatp written by"),
        ("resume writes hgatp", nth_word(elf, flat, B6_RESUME, BASE, 1),
         word(0x68001073), "hgatp written by"),
        ("extra hfence.gvma", nth_word(elf, flat, B6_RESUME, BASE, 1),
         word(0x62000073), "hfence.gvma sites"),
        ("extra ecall", nth_word(elf, flat, B6_DISPATCH, BASE),
         word(0x00000073), "ecall sites"),
        ("henvcfg outside arm", nth_word(elf, flat, B6_TIMER, BASE),
         word(0x60A01073), "henvcfg written by"),
        ("hstateen0 read", nth_word(elf, flat, B6_DISPATCH, BASE),
         word(0x60C022F3), "accesses hstateen0"),
        ("F instruction", nth_word(elf, flat, B6_DISPATCH, BASE),
         word(0x02000053), "F, D, or V instruction"),
        ("R3 install changed", symbols[R3_INSTALL] + 4, word(NOP),
         "differs from B2's"),
        ("entry without quiesce", BASE, word(NOP) + word(NOP),
         "first call be_b1_quiesce"),
        ("management page", BASE + CODE_PAGE + 4, b"\x00\x00",
         "management page differs"),
        ("vector skips s2", matching_word(
            elf, flat, B6_VECTOR, BASE,
            lambda value: store_fields(value) == (18, 5, 136))[0],
         word(NOP), "does not save x18"),
        ("vector skips htinst", matching_word(
            elf, flat, B6_VECTOR, BASE,
            lambda value: store_fields(value) == (6, 5, 328))[0],
         word(NOP), "does not store htinst"),
        ("vector skips SPV", spv_test, word(NOP),
         "does not fail closed on hstatus.SPV"),
        ("resume skips s3", matching_word(
            elf, flat, B6_RESUME, BASE,
            lambda value: load_fields(value) == (19, 31, 144))[0],
         word(NOP), "does not restore x19"),
        ("resume calls out", nth_word(elf, flat, B6_RESUME, BASE, 1),
         word(0x000000EF), "calls or jumps out"),
        ("exit path names a root pool", dispatch_slot,
         pool_reference(dispatch_slot,
                        symbols["__be_root_management_start"] + 0x40, 15),
         "names a G-stage root pool"),
        ("exit path names the B6 pool", dispatch_slot,
         pool_reference(dispatch_slot, symbols["__be_b6_pool_start"] + 0x40,
                        15), "names the B6 G-stage pool"),
        ("unused auipc", nth_word(elf, flat, B6_DISPATCH, BASE),
         word(0x00000F17), "is not used as a base"),
        ("payload constant", symbols[B6_LAYOUT_SYMBOL] + 16,
         struct.pack("<Q", pins[0]["Image"][1] + 8),
         "payload constant kernel_bytes"),
    ]
    dtb_offset = align_up(KERNEL_OFFSET + pins[0]["Image"][1], PAGE)
    dtb = boot_img[dtb_offset:]
    window_cells = cells(0, LAYOUT["GUEST_GPA"], 0, WINDOW_BYTES)
    memory_at = dtb_offset + dtb.index(window_cells) + 12
    bootargs_at = dtb_offset + dtb.index(b"panic_on_warn=1") + 14
    boot = [
        ("payload byte flip", KERNEL_OFFSET + 0x1000,
         bytes([boot_img[KERNEL_OFFSET + 0x1000] ^ 0x40]),
         "kernel differs from its pin"),
        ("kernel magic2", KERNEL_OFFSET + KERNEL_MAGIC2_AT, b"\x00",
         "kernel magic2"),
        ("larger DTB memory node", memory_at, cells(2 * WINDOW_BYTES),
         "DTB memory node"),
        ("kexec FDT slot overlapping the window", 16,
         struct.pack("<Q", WINDOW - STAGING - PAGE), "kexec FDT slot"),
        ("bootargs", bootargs_at, b"0", "bootargs"),
        ("text_offset", 8, struct.pack("<Q", 0x200000), "text_offset"),
        ("descriptor destination", 0x48, struct.pack("<Q", WINDOW),
         "descriptor destination"),
        ("monitor copy", MONITOR_OFFSET + 0x100,
         bytes([boot_img[MONITOR_OFFSET + 0x100] ^ 1]),
         "flat image at 0x1000 differs"),
    ]
    results = []
    for name, address, value, expected in monitor + boot:
        mutated_elf, mutated_flat = bytearray(elf_data), bytearray(flat)
        mutated_boot = bytearray(boot_img)
        if (name, address, value, expected) in monitor:
            patch(mutated_elf, mutated_flat, mutated_boot, address, value,
                  BASE)
        else:
            mutated_boot[address:address + len(value)] = value
        require(bytes(mutated_elf) != elf_data or
                bytes(mutated_boot) != boot_img,
                f"mutation {name!r} changed nothing")
        try:
            check_image(toolchain, bytes(mutated_elf), bytes(mutated_flat),
                        bytes(mutated_boot), pins, kernel, layout)
        except ImageError as error:
            require(expected in str(error),
                    f"mutation {name!r} rejected for another reason: {error}")
            results.append(name)
            continue
        raise ImageError(f"mutation {name!r} was accepted")
    return results


# ------------------------------------------------------------------- main
def number(text):
    return int(text, 0)


def read_map(elf_path):
    """The link map beside an ELF (NAME.map for NAME.elf), when present."""
    path = pathlib.Path(elf_path).with_suffix(".map")
    return path.read_text() if path.is_file() else None


def read(path):
    return open(path, "rb").read()


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", type=number, default=BASE)
    parser.add_argument("--lds", default=str(ACCEPTED_LDS))
    parser.add_argument("--pins", required=True)
    parser.add_argument("--kernel", required=True)
    parser.add_argument("--dtb", required=True)
    parser.add_argument("--image", action="append", default=[])
    parser.add_argument("--reference")
    parser.add_argument("--variant-dtb", action="append", default=[])
    parser.add_argument("--variant", action="append", default=[])
    parser.add_argument("--uimage", action="append", default=[])
    parser.add_argument("--mutation-test")
    args = parser.parse_args(argv[1:])
    if not (args.image or args.variant or args.uimage or args.mutation_test
            or args.variant_dtb):
        parser.error("nothing to check")
    if (args.variant or args.uimage) and not args.reference:
        parser.error("--variant and --uimage need --reference")
    checked = []
    try:
        require(args.base == BASE, f"base 0x{args.base:x} is not 0x{BASE:x}")
        pins = read_pins(args.pins)
        kernel = read(args.kernel)
        dtb = read(args.dtb)
        require(sha256(kernel) == pins[0]["Image"][0],
                "the --kernel file differs from its pin")
        kernel_facts(kernel)
        check_dt(dtb)
        require(sha256(dtb) == pins[0]["b6-guest.dtb"][0],
                "the --dtb file differs from its pin")
        layout = b6_layout(args.lds)
        asserts = len(layout[1]) + len(layout[2])
        flats = {}
        for spec in args.image:
            toolchain, elf_path, bin_path, boot_elf, boot_path = \
                spec.split(":")
            require(toolchain in ("gcc", "clang"),
                    f"unknown toolchain {toolchain}")
            flat, boot_img = read(bin_path), read(boot_path)
            report, boot = check_image(
                toolchain, read(elf_path), flat, boot_img, pins, kernel,
                layout, read_map(elf_path), read(boot_elf), boot_path)
            flats[toolchain] = flat
            print(f"{toolchain}: text_end=0x{report['text_end']:x} "
                  f"data_end=0x{report['data_end']:x} functions="
                  f"{report['functions']} words={report['instructions']} "
                  f"asserts={asserts} boot_bytes=0x{len(boot_img):x} "
                  f"dtb_offset=0x{boot['dtb_offset']:x} "
                  f"bin_sha256={sha256(flat)} boot_sha256={sha256(boot_img)}")
            checked.append(toolchain)
        if len(flats) == 2:
            require(flats["gcc"] != flats["clang"],
                    "GCC and Clang flat images are identical")
        reference = None
        if args.reference:
            toolchain, elf_path, bin_path, boot_elf, boot_path = \
                args.reference.split(":")
            require(toolchain == "gcc", "the reference is the GCC image")
            flat, boot_img = read(bin_path), read(boot_path)
            report, _ = check_image(toolchain, read(elf_path), flat,
                                    boot_img, pins, kernel, layout,
                                    read_map(elf_path), read(boot_elf),
                                    boot_path)
            reference = {"elf": report["elf"], "flat": flat,
                         "boot": boot_img}
        for spec in args.variant_dtb:
            name, path = spec.split(":")
            require(name in DTB_VARIANTS, f"unknown DTB variant {name}")
            data = read(path)
            check_dt(data, name)
            require(sha256(data) == pins[0][f"b6-guest-{name}.dtb"][0],
                    f"the {name} DTB differs from its pin")
            checked.append(f"dtb-{name}")
        for spec in args.variant:
            name, boot_elf, boot_path = spec.split(":")
            data = read(boot_path)
            check_variant(name, read(boot_elf), data, reference, pins,
                          kernel, boot_path)
            print(f"variant {name}: boot_sha256={sha256(data)}")
            checked.append(f"variant-{name}")
        for spec in args.uimage:
            name, text_offset, bin_path, image_path = spec.split(":")
            data = read(image_path)
            check_uimage(name, number(text_offset), read(bin_path), data,
                         pins, kernel, reference)
            print(f"uimage {name}: text_offset={text_offset} "
                  f"bytes=0x{len(data):x} sha256={sha256(data)}")
            checked.append(f"uimage-{name}")
        if args.mutation_test:
            toolchain, elf_path, bin_path, _, boot_path = \
                args.mutation_test.split(":")
            results = mutation_test(toolchain, elf_path, bin_path, boot_path,
                                    pins, kernel, layout)
            print(f"{toolchain}: mutations rejected: {len(results)}")
            checked.append(f"mutations={len(results)}")
    except (ImageError, OSError, ValueError, KeyError, IndexError,
            struct.error) as error:
        print(f"BE_B6_IMAGE_CHECK: FAIL {error}")
        return 1
    print(f"BE_B6_IMAGE_CHECK: PASS {' '.join(checked)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
