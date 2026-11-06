#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Check K3 B5 images (planning/k3-b5-plan.md, "Image checker").

  check-b5-image.py [--base B] [--lds ACCEPTED_R5_LDS]
                    --image TOOLCHAIN:ELF:BIN [--image ...]
                    [--variant NAME:ELF:BIN:GUEST_BIN ...]
  check-b5-image.py --image TOOLCHAIN:IMG [--image ...]
                    [--uimage-variant NAME:TOOLCHAIN:TEXT_OFFSET:IMG ...]
  check-b5-image.py --check-guest TOOLCHAIN:GUEST_ELF:GUEST_BIN [...]
  check-b5-image.py --mutation-test TOOLCHAIN:ELF:BIN

B5 links none of the R5 switch that tests/r5/check-image.mjs is built
around, so this is a B5-specific checker, as B1's and B2's are. For each
monitor image (TOOLCHAIN:ELF:BIN), it requires:

- layout: a little-endian RV64 ET_EXEC whose entry is be_reset at the base
  0x1_0200_0000; the six PT_LOAD segments of the accepted R5 PHDRS, in
  order, with their flags, vaddr == paddr, and no segment both writable and
  executable; and a flat image of exactly 0x34000 bytes holding every
  segment's file bytes in place and zeros elsewhere;
- every conjunct of every ASSERT in the accepted R5 linker script
  (arch/riscv/be/r5-beryllium.lds at 165f4d00, SHA-256 pinned) with every
  symbol moved back by 0x81e00000, except the port's counted replacements:
  its three trap-vector conjuncts name be_b5_trap_vector, and its three
  management-fixture conjuncts are the payload conjuncts (be_b5_payload at
  the page start, non-empty, inside the page);
- be_reset first calls be_b1_quiesce, then runs the accepted first entry
  instruction (mv s0, a0), and calls or tails nothing but be_b1_quiesce,
  be_b5_runtime_main, and be_r3_arch_halt;
- the management code page equal to the pinned guest binary of the image's
  toolchain plus zero padding, and the protected page equal to B2's;
- be_r3_arch_reset_state, be_r3_arch_install_management, and
  be_r3_arch_enter_management byte-identical to B2's (pinned);
- no R4 or R5 mechanism symbol: no be_r4_* symbol, and no be_r5_* symbol
  but the inert protected fixture's two;
- from the monitor-text instruction words, decoded function by function
  (padding between functions may hold only nops and zeros): exactly one
  ecall, in be_r3_arch_sbi_call, which only the accepted platform helpers
  call; exactly three sret (R3 entry, B5 resume tail, B1 skip);
  sfence.vma, hgatp writes, and hfence.gvma only in the R3 functions; no
  hfence.vvma, H load/store, mret, or ebreak; and every CSR write in the
  functions of the table below, exactly: outside the R3 reset, henvcfg,
  vstimecmp, hideleg, hcounteren, and hstatus are written only by B5's arm
  and timer helpers, no other vs* CSR is written, and hie and hvip only by
  the R3 halts.

A variant (NAME:ELF:BIN:GUEST_BIN) must pass the same rules with its own
guest binary, and its flat image must differ from the GCC image's only in
the code page. --image TOOLCHAIN:IMG checks a U-Boot image (B3's unchanged
shim wrapping the flat image): B3's header and descriptor rules
(bringup/k3-b3/tests/check-b3-image.py, imported unchanged) and a payload
whose pages pass the flat-image rules above (code page, protected page,
and the pinned R3 function bytes at their B5 addresses are not visible
without the ELF, so the payload is compared with the checked flat image
beside it when present). --check-guest checks a guest ELF and its payload:
entry and layout, no initialized writable data, no F, D, V, or CBO
instruction, and the pinned SHA-256. --mutation-test applies known
defects to one image in memory and requires each to be rejected.
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
REPO_ROOT = HERE.parents[3]
ACCEPTED_LDS = REPO_ROOT / "arch" / "riscv" / "be" / "r5-beryllium.lds"
B3_CHECKER = REPO_ROOT / "bringup" / "k3-b3" / "tests" / "check-b3-image.py"

BASE = 0x102000000
DELTA = 0x81E00000
SPAN = 0x34000
CODE_PAGE = 0x32000
PROTECTED_PAGE = 0x33000
PAGE = 0x1000
MONITOR_TEXT_LIMIT = 0x102008000
MONITOR_DATA_LIMIT = 0x10200F000
ACCEPTED_LDS_SHA256 = \
    "0df278b45d33500af08204b364a3f3e61178a7cd9981cb499025d95411baa56a"
ACCEPTED_CONJUNCTS = 57
PF_X, PF_W = 1, 2
RISCV_MV_S0_A0 = 0x00050413

# The port's counted ASSERT replacements (scripts/port.py).
TRAP_VECTOR_CONJUNCTS = 3
FIXTURE_CONJUNCTS = (
    "be_r5_management_fixture == 0x80232000",
    "be_r5_management_fixture_end - be_r5_management_fixture == 0x40",
    "be_r5_management_fixture_end <= __be_guest_management_end",
)
PAYLOAD_CONJUNCTS = (
    "be_b5_payload == 0x80232000",
    "be_b5_payload_end > be_b5_payload",
    "be_b5_payload_end <= __be_guest_management_end",
)

# The guest payload (.text and .rodata) of each toolchain's guest build.
GUEST_SHA256 = {
    "gcc": "965f78044a6597c09ea85e91f16795d4d77cbaf402d83626d41c58229962d5f9",
    "clang": "05b7276918762bcc7db6146fffac13093c84a23a0039f69560788cc4d07a2252",
}
GUEST_ENTRY = 0x40010000
GUEST_CODE_END = 0x40011000
GUEST_PRIVATE = 0x40000000
GUEST_BSS_LIMIT = 0x40000400

# From the accepted B2 images (bringup/k3-b2/README.md: GCC 9c145f00...,
# Clang 47be17e3...): the protected page, and the R3 functions B5 reuses.
B2_PROTECTED_PAGE_SHA256 = {
    "gcc": "1bec687dabe929d676d5ed0d3cecb601c8932a034520fbe7f05ec8c47d67edd5",
    "clang": "788d045042a98214b781c98884b139356f450a0ec4eaba0961144bc94876b3b0",
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
R3_SBI = "be_r3_arch_sbi_call"
R3_UNEXPECTED = "be_r3_unexpected_trap"
R3_HALT = "be_r3_arch_halt"
B1_QUIESCE = "be_b1_quiesce"
B1_SKIP = "be_b1_skip"
B1_HALT = "be_b1_halt"
B5_STCE = "be_b5_arch_arm_stce"
B5_ARM = "be_b5_arch_arm_controls"
B5_TIMER = "be_b5_arch_set_timer"
B5_VECTOR = "be_b5_trap_vector"
B5_RESUME = "be_b5_arch_resume"
PLATFORM_HELPERS = {"sbi_value_call", "be_r3_platform_get_spec_version",
                    "be_r3_platform_probe_extension", "be_r3_platform_write",
                    "be_r3_platform_reset"}
REQUIRED_SYMBOLS = (
    "be_reset", "be_b1_quiesce", "be_b5_runtime_main", "be_b5_dispatch",
    B5_VECTOR, B5_RESUME, B5_STCE, B5_ARM, B5_TIMER, "be_b5_payload",
    "be_b5_payload_end", R3_RESET, R3_INSTALL, R3_ENTER, R3_SBI, R3_HALT,
)
ALLOWED_R5_SYMBOLS = {"be_r5_protected_fixture", "be_r5_protected_fixture_end"}

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
    0x60A: "henvcfg", 0x643: "htval", 0x644: "hip", 0x645: "hvip",
    0x680: "hgatp",
}
VS_RESET_ONLY = ("vsstatus", "vsie", "vstvec", "vsscratch", "vsepc",
                 "vscause", "vstval", "vsip", "vsatp")
# Every CSR the monitor writes, and exactly the functions that write it.
CSR_WRITERS = {
    "satp": {R3_RESET},
    "sstatus": {R3_RESET, R3_ENTER, B1_QUIESCE, B1_HALT, B5_RESUME},
    "stvec": {R3_RESET, B1_QUIESCE},
    "sscratch": {R3_RESET, R3_ENTER, B5_VECTOR},
    "sepc": {R3_RESET, R3_ENTER, B1_SKIP, B5_RESUME},
    "scause": {R3_RESET},
    "stval": {R3_RESET},
    "sie": {R3_RESET, R3_UNEXPECTED, R3_HALT, B1_QUIESCE, B1_HALT},
    "sip": {B1_QUIESCE},
    "senvcfg": {R3_RESET},
    "scounteren": {R3_RESET},
    "stimecmp": {B1_QUIESCE},
    "siselect": {B1_QUIESCE},
    "sireg": {B1_QUIESCE},
    "hstatus": {R3_RESET, B5_ARM},
    "hedeleg": {R3_RESET},
    "hideleg": {R3_RESET, B5_ARM},
    "hie": {R3_RESET, R3_UNEXPECTED, R3_HALT},
    "hvip": {R3_RESET, R3_UNEXPECTED, R3_HALT},
    "hcounteren": {R3_RESET, B5_ARM},
    "htimedelta": {R3_RESET},
    "henvcfg": {R3_RESET, B5_STCE},
    "hgeie": {R3_RESET},
    "htval": {R3_RESET},
    "hgatp": {R3_RESET, R3_INSTALL},
    "vstimecmp": {B5_ARM, B5_TIMER},
    **{name: {R3_RESET} for name in VS_RESET_ONLY},
}
INSTRUCTION_SITES = {
    "ecall": {R3_SBI: 1},
    "sret": {R3_ENTER: 1, B5_RESUME: 1, B1_SKIP: 1},
    "hfence.gvma": {R3_RESET: 1, R3_INSTALL: 1},
    "sfence.vma": {R3_RESET: 1},
    "wfi": {R3_UNEXPECTED: 1, R3_HALT: 1, B1_HALT: 1},
    "hfence.vvma": {},
    "hlsv": {},
    "mret": {},
    "ebreak": {},
}
NOP = 0x00000013
C_NOP = 0x0001
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
}
MAP_SECTIONS = (".saved.management", ".saved.protected",
                ".private.management", ".private.protected", ".shared",
                ".gstage.root.management", ".gstage.root.protected",
                ".guest.code.management", ".guest.code.protected",
                ".stack.management", ".stack.protected")
# The frame offsets of the eight trap CSRs (struct be_r4_frame).
TRAP_CSRS = (0x205, 0x241, 0x242, 0x243, 0x142, 0x141, 0x143, 0x643)
FRAME_TRAP_CSRS = 248
FRAME_RESERVED = 312
FRAME_SEPC = 288
# Only boot code may name a G-stage root pool.
ROOT_POOL_USERS = {"be_b5_runtime_main", "run_r2", "build_image_layout"}


class ImageError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ImageError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


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


def b5_layout(lds_path):
    """The accepted PHDRS and the ASSERT conjuncts with B5's replacements."""
    data = open(lds_path, "rb").read()
    require(sha256(data) == ACCEPTED_LDS_SHA256,
            f"{lds_path} is not the accepted R5 linker script")
    text = strip_comments(data.decode())
    phdrs = parse_phdrs(text)
    accepted = parse_asserts(text)
    require(len(accepted) == ACCEPTED_CONJUNCTS,
            f"parsed {len(accepted)} ASSERT conjuncts, expected "
            f"{ACCEPTED_CONJUNCTS}")
    conjuncts, renamed, replaced = [], 0, 0
    for conjunct in accepted:
        if conjunct in FIXTURE_CONJUNCTS:
            conjuncts.append(PAYLOAD_CONJUNCTS[FIXTURE_CONJUNCTS.index(
                conjunct)])
            replaced += 1
        elif "be_r5_trap_vector" in conjunct:
            conjuncts.append(conjunct.replace("be_r5_trap_vector",
                                              "be_b5_trap_vector"))
            renamed += 1
        else:
            conjuncts.append(conjunct)
    require(renamed == TRAP_VECTOR_CONJUNCTS and
            replaced == len(FIXTURE_CONJUNCTS),
            f"replacements renamed={renamed} replaced={replaced}")
    return phdrs, conjuncts, len(accepted) - renamed - replaced


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


def check_instructions(elf, flat, base, code_start, code_end, symbols):
    """The ecall/sret/fence/CSR-write rules over monitor text."""
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
    # Calls and address uses of the one ecall site, and be_reset's calls.
    pool_start = symbols["__be_root_management_start"]
    pool_end = symbols["__be_root_protected_end"]
    for owner, decoded in decoded_all:
        for pc, target, _ in references(decoded, owner):
            require(not pool_start <= target <= pool_end or
                    owner in ROOT_POOL_USERS,
                    f"{owner} names a G-stage root pool at 0x{pc:x}")
    by_name = {owner: decoded for owner, decoded in decoded_all}
    check_trap_entry(by_name[B5_VECTOR], symbols)
    resume = [(value, size) for value, size, names in functions
              if B5_RESUME in names][0]
    check_resume(by_name[B5_RESUME], symbols, resume[0],
                 resume[0] + resume[1])
    sbi_call = symbols[R3_SBI]
    reset = [(value, size) for value, size, names in functions
             if "be_reset" in names]
    require(len(reset) == 1, "be_reset is not one function")
    callers, reset_targets = set(), set()
    for owner, decoded in decoded_all:
        for pc, target, link in references(decoded):
            if target == sbi_call:
                callers.add(owner)
            if owner == "be_reset" and link is not None and not \
                    reset[0][0] <= target < reset[0][0] + reset[0][1]:
                reset_targets.add(target)
    require(callers and callers <= PLATFORM_HELPERS,
            f"{R3_SBI} is reached from {sorted(callers)}, not only the "
            f"accepted platform helpers")
    expected_targets = {symbols["be_b1_quiesce"],
                        symbols["be_b5_runtime_main"], symbols[R3_HALT]}
    require(reset_targets == expected_targets,
            "be_reset calls or tails something other than be_b1_quiesce, "
            "be_b5_runtime_main, and be_r3_arch_halt")
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


def csr_read(word):
    """The CSR a csrr (csrrs rd, csr, x0) reads, or None."""
    if word & 0x7F == 0x73 and (word >> 12) & 7 == 2 and \
            (word >> 15) & 0x1F == 0:
        return word >> 20
    return None


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
    require(elf.sections[".monitor.text"][5] <= 0x8000,
            "monitor text outgrew its reserved window")
    data = elf.sections[".monitor.data"]
    require(data[3] + data[5] <= 0x8020F000 + DELTA,
            "monitor data overruns the diagnostic page")
    return architecture


def check_trap_entry(decoded, symbols):
    """Sscratch pivot, the whole frame, the sealed word, and the dispatch."""
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
    reads = {csr_read(word) for word in words}
    for index, csr in enumerate(TRAP_CSRS):
        offset = FRAME_TRAP_CSRS + index * 8
        require(csr in reads, f"trap entry does not capture CSR 0x{csr:x}")
        require(any(base == frame and at == offset for _, base, at in stores),
                f"trap entry does not store CSR 0x{csr:x} at {offset}")
    require((0, frame, FRAME_RESERVED) in stores,
            "trap entry does not seal the reserved frame word")
    require(any(target == symbols["be_b5_dispatch"] and link == 1
                for _, target, link in references(decoded)),
            "trap entry does not call be_b5_dispatch")


def check_resume(decoded, symbols, start, end):
    """Call free; hgatp verified; sepc and the GPRs from the frame; one SRET."""
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
    sstatus = [word for word in words
               if system_kind(word) == "csr" and csr_write(word) == 0x100]
    require(len(sstatus) == 1 and (sstatus[0] >> 12) & 3 == 2,
            "resume tail does not set sstatus SPP exactly once")
    require(0x680 in {csr_read(word) for word in words},
            "resume tail does not verify hgatp")
    srets = [index for index, word in enumerate(words) if word == 0x10200073]
    last_load = max(index for index, fields in enumerate(loads) if fields)
    require(len(srets) == 1 and srets[0] == last_load + 1,
            "resume tail does not end its GPR restore in its one SRET")
    terminal = symbols["be_b5_runtime_terminal"]
    pairs = {pc: (target, link)
             for pc, target, link in references(decoded, B5_RESUME)}
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
    phdrs, conjuncts, _ = layout
    require(elf.entry == base, f"entry 0x{elf.entry:x} != base 0x{base:x}")
    require(elf.symbols.get("be_reset") == base, "be_reset is not the base")
    require(len(elf.segments) == len(phdrs),
            f"{len(elf.segments)} PT_LOAD segments, accepted {len(phdrs)}")
    require(len(flat) == SPAN,
            f"flat image is 0x{len(flat):x} bytes, not 0x{SPAN:x}")
    covered = bytearray(SPAN)
    previous_end = base
    for (vaddr, paddr, offset, filesz, memsz, flags), (name, wanted) in zip(
            elf.segments, phdrs):
        require(vaddr == paddr, f"{name} 0x{vaddr:x} has paddr 0x{paddr:x}")
        require(previous_end <= paddr and paddr + memsz <= base + SPAN,
                f"{name} 0x{paddr:x}+0x{memsz:x} is out of order or leaves "
                f"the span")
        require(not (flags & PF_W and flags & PF_X),
                f"{name} 0x{paddr:x} is writable and executable")
        require(flags == wanted, f"{name} flags {flags} != accepted {wanted}")
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


def check_pages(toolchain, flat, guest, symbols, pinned):
    """The code page is the guest plus zeros; the protected page is B2's."""
    payload = symbols.get("be_b5_payload")
    payload_end = symbols.get("be_b5_payload_end")
    require(payload == BASE + CODE_PAGE,
            "be_b5_payload is not the management code page")
    length = payload_end - payload
    require(0 < length <= PAGE, f"payload is 0x{length:x} bytes")
    code = flat[CODE_PAGE:CODE_PAGE + PAGE]
    require(code[:length] == guest, "code page differs from the guest binary")
    require(not any(code[length:]), "code page has bytes after the guest")
    if pinned:
        require(sha256(guest) == GUEST_SHA256[toolchain],
                f"{toolchain} guest SHA-256 {sha256(guest)} is not pinned")
    protected = flat[PROTECTED_PAGE:PROTECTED_PAGE + PAGE]
    require(sha256(protected) == B2_PROTECTED_PAGE_SHA256[toolchain],
            "protected page differs from B2's")
    return length


def check_monitor(toolchain, elf_data, flat, base, layout, guest=None,
                  map_text=None):
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
    quiesce = symbols["be_b1_quiesce"]
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
    if guest is None:
        payload = symbols["be_b5_payload"] - base
        guest = flat[payload:symbols["be_b5_payload_end"] - base]
        length = check_pages(toolchain, flat, guest, symbols, True)
    else:
        length = check_pages(toolchain, flat, guest, symbols, False)
    return {
        "architecture": architecture,
        "text_end": code_end,
        "data_end": symbols["__be_bss_end"],
        "functions": functions,
        "instructions": words,
        "guest": length,
    }


# ------------------------------------------------------------------ guest
def guest_instructions_clean(data, start, end):
    """No F, D, V, or CBO instruction in the guest's code."""
    pc = start
    while pc < end:
        half = struct.unpack_from("<H", data, pc - start)[0]
        if half & 3 == 3:
            word = struct.unpack_from("<I", data, pc - start)[0]
            opcode = word & 0x7F
            require(opcode not in (0x07, 0x27, 0x43, 0x47, 0x4B, 0x4F, 0x53,
                                   0x57),
                    f"guest F/D/V instruction 0x{word:08x} at 0x{pc:x}")
            require(not (opcode == 0x0F and (word >> 12) & 7 == 2),
                    f"guest CBO instruction 0x{word:08x} at 0x{pc:x}")
            pc += 4
        else:
            quadrant, funct3 = half & 3, (half >> 13) & 7
            require(not ((quadrant in (0, 2)) and funct3 in (1, 5)),
                    f"guest compressed FP instruction 0x{half:04x} at "
                    f"0x{pc:x}")
            pc += 2


def check_guest(toolchain, elf_path, bin_path, pinned=True):
    elf = Elf(open(elf_path, "rb").read())
    payload = open(bin_path, "rb").read()
    require(elf.entry == GUEST_ENTRY, f"guest entry 0x{elf.entry:x}")
    require(elf.symbols.get("_start") == GUEST_ENTRY, "_start moved")
    text = elf.sections.get(".text")
    rodata = elf.sections.get(".rodata")
    bss = elf.sections.get(".bss")
    require(text is not None and text[3] == GUEST_ENTRY,
            "guest .text is not at 0x40010000")
    for name, section in elf.sections.items():
        if section[2] & 2 and section[5]:  # SHF_ALLOC, non-empty
            require(name in (".text", ".rodata", ".bss"),
                    f"guest has allocated section {name}")
    require(bss is None or (bss[3] == GUEST_PRIVATE and
                            bss[3] + bss[5] <= GUEST_BSS_LIMIT),
            "guest .bss leaves its reserve below the stack")
    end = (rodata[3] + rodata[5]) if rodata is not None and rodata[5] else \
        text[3] + text[5]
    require(end <= GUEST_CODE_END, f"guest code ends at 0x{end:x}")
    require(len(payload) == end - GUEST_ENTRY,
            "guest binary is not .text through .rodata")
    image = bytearray(end - GUEST_ENTRY)
    for section in (text, rodata):
        if section is not None and section[5]:
            start = section[3] - GUEST_ENTRY
            image[start:start + section[5]] = \
                elf.data[section[4]:section[4] + section[5]]
    require(bytes(image) == payload, "guest binary differs from its ELF")
    guest_instructions_clean(payload[:text[5]], GUEST_ENTRY,
                             GUEST_ENTRY + text[5])
    if pinned:
        require(sha256(payload) == GUEST_SHA256[toolchain],
                f"{toolchain} guest SHA-256 {sha256(payload)} is not pinned")
    return len(payload), (bss[5] if bss is not None else 0)


# ----------------------------------------------------------------- U-Boot
def load_b3():
    spec = importlib.util.spec_from_file_location("check_b3_image",
                                                  B3_CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_uimage(toolchain, image_path, text_offset):
    b3 = load_b3()
    data = open(image_path, "rb").read()
    findings = []
    require(len(data) == b3.IMAGE_SIZE,
            f"U-Boot image is 0x{len(data):x} bytes, not 0x{b3.IMAGE_SIZE:x}")
    b3.check_header(data, text_offset, findings)
    b3.check_descriptor(data, findings)
    for template in b3.TEMPLATES:
        if data[:b3.STUB_PAGE].count(template) != 1:
            findings.append("a B3 report-line template is missing")
    require(not findings, "; ".join(findings))
    payload = data[b3.PAYLOAD_OFFSET:]
    require(len(payload) == SPAN, "payload is not the flat image")
    flat_path = pathlib.Path(image_path).with_name("be-k3-b5.bin")
    if flat_path.is_file():
        require(payload == flat_path.read_bytes(),
                f"payload differs from {flat_path}")
    code = payload[CODE_PAGE:CODE_PAGE + PAGE]
    length = len(code.rstrip(b"\0"))
    matches = [length_ for length_ in range(length, PAGE + 1)
               if sha256(code[:length_]) == GUEST_SHA256[toolchain]]
    require(matches, "payload code page is not the pinned guest")
    require(sha256(payload[PROTECTED_PAGE:]) ==
            B2_PROTECTED_PAGE_SHA256[toolchain],
            "payload protected page differs from B2's")
    require(call_target(payload, 0, BASE) is not None,
            "payload does not start with be_reset's call")
    return sha256(data)


# ---------------------------------------------------------- mutation test
def patch(elf_data, flat, address, value, base):
    """Write value at address in both the ELF's segment and the flat image."""
    elf = Elf(bytes(elf_data))
    for vaddr, _, offset, filesz, _, _ in elf.segments:
        if vaddr <= address and address + len(value) <= vaddr + filesz:
            start = offset + address - vaddr
            elf_data[start:start + len(value)] = value
            break
    else:
        raise ImageError(f"0x{address:x} is not in a loaded segment")
    flat[address - base:address - base + len(value)] = value


def first_word(elf, flat, name, base):
    """Address of the first 32-bit instruction of a function."""
    for value, size, label in elf.functions:
        if label == name:
            for pc, width, _ in instructions(flat, value, value + size, base):
                if width == 4:
                    return pc + 4 if name == B5_RESUME else pc
    raise ImageError(f"no 32-bit instruction in {name}")


def word_slots(elf, flat, name, base, count):
    """Address of the first run of count adjacent 32-bit instructions."""
    for value, size, label in elf.functions:
        if label != name:
            continue
        decoded = instructions(flat, value, value + size, base)
        for index in range(len(decoded) - count + 1):
            if all(width == 4 for _, width, _ in decoded[index:index + count]):
                return decoded[index][0]
    raise ImageError(f"no {count} adjacent 32-bit instructions in {name}")


def frame_access(elf, flat, name, base, fields, wanted):
    """Address of the instruction in name whose decoded fields match."""
    for value, size, label in elf.functions:
        if label == name:
            for pc, width, word in instructions(flat, value, value + size,
                                                base):
                if width == 4 and fields(word) == wanted:
                    return pc
    raise ImageError(f"{name} has no instruction {wanted}")


def pool_reference(pc, address, register):
    """auipc register + addi register: form address at pc."""
    delta = address - pc
    upper = (delta + 0x800) & ~0xFFF
    lower = delta - upper
    return struct.pack("<II", (upper & 0xFFFFF000) | register << 7 | 0x17,
                       (lower & 0xFFF) << 20 | register << 15 |
                       register << 7 | 0x13)


def mutation_test(toolchain, elf_path, bin_path, base, layout):
    elf_data = open(elf_path, "rb").read()
    flat = open(bin_path, "rb").read()
    check_monitor(toolchain, elf_data, flat, base, layout)
    elf = Elf(elf_data)
    word = lambda value: struct.pack("<I", value)  # noqa: E731
    mutations = [
        ("guest byte", base + CODE_PAGE + 16, b"\xff",
         "guest SHA-256"),
        ("code-page tail", base + CODE_PAGE + PAGE - 8, b"\x01",
         "code page has bytes after the guest"),
        ("vector writes hvip", first_word(elf, flat, B5_VECTOR, base) + 4,
         word(0x64501073), "hvip written by"),
        ("resume writes vsatp", first_word(elf, flat, B5_RESUME, base),
         word(0x28001073), "vsatp written by"),
        ("resume writes hgatp", first_word(elf, flat, B5_RESUME, base),
         word(0x68001073), "hgatp written by"),
        ("extra hfence.gvma", first_word(elf, flat, B5_RESUME, base),
         word(0x62000073), "hfence.gvma sites"),
        ("extra sret", first_word(elf, flat, B5_RESUME, base),
         word(0x10200073), "sret sites"),
        ("extra ecall", first_word(elf, flat, "be_b5_dispatch", base),
         word(0x00000073), "ecall sites"),
        ("henvcfg outside arm", first_word(elf, flat, B5_TIMER, base),
         word(0x60A01073), "henvcfg written by"),
        ("R3 entry changed", elf.symbols[R3_ENTER] + 8, word(NOP),
         "differs from B2's"),
        ("entry without quiesce", base, word(NOP) + word(NOP),
         "first call be_b1_quiesce"),
        ("protected page", base + PROTECTED_PAGE + 4, b"\x00\x00",
         "protected page differs"),
        ("vector skips s2", frame_access(elf, flat, B5_VECTOR, base,
                                         store_fields, (18, 5, 136)),
         word(NOP), "does not save x18"),
        ("resume skips s3", frame_access(elf, flat, B5_RESUME, base,
                                         load_fields, (19, 31, 144)),
         word(NOP), "does not restore x19"),
        ("resume calls out", first_word(elf, flat, B5_RESUME, base),
         word(0x000000EF), "calls or jumps out"),
        ("exit path names a root pool",
         word_slots(elf, flat, "be_b5_dispatch", base, 2),
         pool_reference(word_slots(elf, flat, "be_b5_dispatch", base, 2),
                        elf.symbols["__be_root_management_start"] + 0x40,
                        15), "names a G-stage root pool"),
        ("unused auipc", word_slots(elf, flat, "be_b5_dispatch", base, 1),
         word(0x00000F17), "is not used as a base"),
    ]
    results = []
    for name, address, value, expected in mutations:
        mutated_elf, mutated_flat = bytearray(elf_data), bytearray(flat)
        patch(mutated_elf, mutated_flat, address, value, base)
        try:
            check_monitor(toolchain, bytes(mutated_elf), bytes(mutated_flat),
                          base, layout)
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


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=number, default=BASE)
    parser.add_argument("--lds", default=str(ACCEPTED_LDS))
    parser.add_argument("--image", action="append", default=[])
    parser.add_argument("--variant", action="append", default=[])
    parser.add_argument("--uimage-variant", action="append", default=[])
    parser.add_argument("--check-guest", action="append", default=[])
    parser.add_argument("--mutation-test")
    args = parser.parse_args(argv[1:])
    if not (args.image or args.variant or args.uimage_variant or
            args.check_guest or args.mutation_test):
        parser.error("nothing to check")
    checked = []
    try:
        require(args.base == BASE, f"base 0x{args.base:x} is not 0x{BASE:x}")
        layout = None
        if args.mutation_test or args.variant or any(
                spec.count(":") == 2 for spec in args.image):
            layout = b5_layout(args.lds)
        for spec in args.check_guest:
            toolchain, elf_path, bin_path = spec.split(":")
            require(toolchain in GUEST_SHA256, f"unknown toolchain {toolchain}")
            size, bss = check_guest(toolchain, elf_path, bin_path)
            print(f"{toolchain}: guest code=0x{size:x} bss=0x{bss:x} "
                  f"sha256={sha256(open(bin_path, 'rb').read())}")
            checked.append(f"guest-{toolchain}")
        flats = {}
        for spec in args.image:
            fields = spec.split(":")
            toolchain = fields[0]
            require(toolchain in GUEST_SHA256, f"unknown toolchain {toolchain}")
            if len(fields) == 2:
                digest = check_uimage(toolchain, fields[1], 0x200000)
                print(f"{toolchain}: uimage bytes=0x35000 sha256={digest}")
                checked.append(f"uimage-{toolchain}")
                continue
            require(len(fields) == 3, f"bad --image {spec!r}")
            elf_data = open(fields[1], "rb").read()
            flat = open(fields[2], "rb").read()
            report = check_monitor(toolchain, elf_data, flat, args.base,
                                   layout, map_text=read_map(fields[1]))
            flats[toolchain] = flat
            print(f"{toolchain}: text_end=0x{report['text_end']:x} "
                  f"data_end=0x{report['data_end']:x} "
                  f"guest=0x{report['guest']:x} functions="
                  f"{report['functions']} words={report['instructions']} "
                  f"asserts={len(layout[1])} bin_sha256={sha256(flat)}")
            checked.append(toolchain)
        for spec in args.variant:
            name, elf_path, bin_path, guest_path = spec.split(":")
            elf_data = open(elf_path, "rb").read()
            flat = open(bin_path, "rb").read()
            guest = open(guest_path, "rb").read()
            check_monitor("gcc", elf_data, flat, args.base, layout, guest,
                          read_map(elf_path))
            require(sha256(guest) != GUEST_SHA256["gcc"],
                    f"variant {name} embeds the pass guest")
            gcc_path = pathlib.Path(bin_path).parents[2] / "gcc" / \
                "be-k3-b5.bin"
            if gcc_path.is_file():
                reference = gcc_path.read_bytes()
                require(flat[:CODE_PAGE] == reference[:CODE_PAGE] and
                        flat[CODE_PAGE + PAGE:] ==
                        reference[CODE_PAGE + PAGE:],
                        f"variant {name} differs from the GCC image "
                        f"outside the code page")
            print(f"variant {name}: guest=0x{len(guest):x} "
                  f"bin_sha256={sha256(flat)}")
            checked.append(f"variant-{name}")
        for spec in args.uimage_variant:
            name, toolchain, text_offset, image_path = spec.split(":")
            digest = check_uimage(toolchain, image_path, number(text_offset))
            print(f"uimage variant {name}: text_offset={text_offset} "
                  f"sha256={digest}")
            checked.append(f"uimage-{name}")
        if args.mutation_test:
            toolchain, elf_path, bin_path = args.mutation_test.split(":")
            results = mutation_test(toolchain, elf_path, bin_path, args.base,
                                    layout)
            print(f"mutations rejected: {len(results)}")
            checked.append(f"mutations={len(results)}")
        if len(flats) == 2:
            require(flats["gcc"] != flats["clang"],
                    "GCC and Clang flat images are identical")
    except (ImageError, OSError, ValueError, KeyError, struct.error) as error:
        print(f"BE_B5_IMAGE_CHECK: FAIL {error}")
        return 1
    print(f"BE_B5_IMAGE_CHECK: PASS {' '.join(checked)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
