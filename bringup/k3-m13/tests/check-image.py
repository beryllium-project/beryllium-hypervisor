#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""
check-image.py --image N --expect FILE [--other-base ELF] ELF IMG
check-image.py --self-test --image N --expect FILE --other-base ELF ELF IMG
check-image.py --expand --image N --expect FILE

The M13-4 probe images' image check (planning/mvp-m13-3-review-point.md,
sections 2 and 3; bringup/k3-m13/README.md): what the linked image itself
shows, each property a rule whose tag starts its findings.

[header]  B3's Image header rule (bringup/k3-b3/tests/check-b3-image.py,
          by its path); code0 jumps to be_m13_entry, at base + 0x60; bytes
          0x40 to 0x5F zero.
[extent]  the ELF's entry and lowest address are the board's base; every
          allocated section is PROGBITS and every segment's file size its
          memory size; IMG is the segments' bytes, zero between them; at
          most 64 KiB; the 8 KiB stack ends it.
[base]    the ELF linked at QEMU's 0x80200000 (--other-base) gives IMG's
          bytes.
[table]   the table, decoded from IMG, is the expected list FILE
          (tests/m13list.py), entry for entry and field for field; the
          image's digit; image 1 lists harts 3 and P1 P7, image 2 harts 1
          and P3 P4 P2, any other harts 1.
[writes]  every write of the list and the table is one of the page's:
          P7's sourcecfg[200] (0x1 or 0) and target[200] (0x1000 or 0), P1's
          hgeie (all ones or 0).
[device]  be_m13_access, the only routine that touches a device, is its
          template instruction for instruction, with its sites' labels.
[trap], [p1], [hart-run]  be_m13_trap, be_m13_p1, be_m13_hart_run are
          their templates (the last two in image 1 alone).
[store]   every store of the assembly but the device site is through sp or
          through a register set in its run by an auipc pair to a data
          object, indexed at most by (x & 3) << 6, inside that object;
          be_m13_secondary's s0 is set once so, and written nowhere else.
[c]       no C function holds a CSR access, ecall, sret, wfi, fence.i, AMO,
          other SYSTEM instruction, or an indirect jump but ret and auipc
          pairs; its loads and stores are counted in a fact line.
[csr]     every CSR write is one of: sstatus.SIE cleared and sie 0 (entry,
          secondary), stvec to the hart's own vector, sepc to
          be_m13_access_fault (the vector), hgeie all ones or 0
          (be_m13_p1); every CSR read is of hgeie, time, scause, sepc,
          stval, or satp.
[system]  no mret, ebreak, fence.i, AMO, or other SYSTEM instruction; sret
          in be_m13_trap alone, wfi in be_m13_park alone.
[ecall]   every ecall is at one of its labels, with a7 and a6 (SRST's a0
          and a1 too) set by li in its run as the SBI table has them; HSM's
          in image 1 alone, and no a7 of HSM in any other image.
[hsm]     be_m13_hart_run refuses a hart above 2 before anything, writes no
          a0 before its ecall, and starts it at be_m13_secondary; it, its
          ecall, and be_m13_p1 are in image 1 alone.
[control] every word of .text in one function; no indirect jump but ret
          and auipc pairs; every branch inside its
          function; every jump and call to its own function or a function
          that its caller may call; no jump to a vector, a started hart's
          entry, an ecall label, a site, or be_m13_access_fault.
[data]    no aligned word of .rodata outside the table, or of .data,
          equals an address of the list.

It prints `finding: [rule] ...` lines, which name no directory and no
value of the table, `fact:` lines, then BE_K3_M13_IMAGE: PASS|FAIL image=N
entries=K bytes=S sha256=... md5=..., and exits 0, 1, or 2 (usage).
--self-test checks the image as built (PASS), then each mutation of the
design's section 6.10, made in memory to ELF and IMG alike, and requires
each to fail by its own rule's tag. --expand prints each entry of the
list, one a line with its index, as the table must hold it.

Trust: test-only and read-only. What rests on code review is the
README's list: the C's own pointer accesses first.
"""

import argparse
import copy
import hashlib
import importlib.util
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
BOARD_BASE, QEMU_BASE, IMAGE_MAX, STACK = 0x102200000, 0x80200000, 0x10000, 0x2000
REGS = ("zero ra sp gp tp t0 t1 t2 s0 s1 a0 a1 a2 a3 a4 a5 a6 a7 s2 s3 s4 "
        "s5 s6 s7 s8 s9 s10 s11 t3 t4 t5 t6").split()
CSRS = {"sstatus": 0x100, "sie": 0x104, "stvec": 0x105, "sscratch": 0x140,
        "sepc": 0x141, "scause": 0x142, "stval": 0x143, "satp": 0x180,
        "hgeie": 0x607, "time": 0xC01}
READABLE = {CSRS[n] for n in ("hgeie", "time", "scause", "sepc", "stval",
                              "satp")}
ASM = {"be_m13_entry", "be_m13_trap", "be_m13_access", "be_m13_sbi_base",
       "be_m13_putc", "be_m13_srst", "be_m13_park", "be_m13_read_satp",
       "be_m13_p1", "be_m13_hart_run", "be_m13_secondary",
       "be_m13_secondary_trap"}
C_CALLS = {"be_m13_sbi_base", "be_m13_putc", "be_m13_srst", "be_m13_park",
           "be_m13_read_satp", "be_m13_access", "be_m13_p1",
           "be_m13_hart_run"}
ASM_CALLS = {"be_m13_entry": {"be_m13_main", "be_m13_refuse", "be_m13_park"},
             "be_m13_trap": {"be_m13_trap_fail", "be_m13_park"},
             "be_m13_srst": {"be_m13_park"},
             "be_m13_secondary": {"be_m13_p1", "be_m13_park"},
             "be_m13_secondary_trap": {"be_m13_park"}}
SITES = ("be_m13_site_lw", "be_m13_site_ld", "be_m13_site_sw")
ECALLS = {"be_m13_ecall_base": {"a7": 0x10},
          "be_m13_ecall_dbcn": {"a7": 0x4442434E, "a6": 2},
          "be_m13_ecall_srst": {"a7": 0x53525354, "a6": 0, "a0": 0, "a1": 0},
          "be_m13_ecall_hsm": {"a7": 0x48534D, "a6": 0}}
NO_TARGET = set(SITES) | set(ECALLS) | {
    "be_m13_trap", "be_m13_secondary_trap", "be_m13_secondary",
    "be_m13_access_fault"}
WRITES = {(4, 1, 0x607, 8, (1 << 64) - 1), (4, 1, 0x607, 8, 0),
          (2, 7, 0xE0804320, 4, 1), (2, 7, 0xE0804320, 4, 0),
          (2, 7, 0xE0807320, 4, 0x1000), (2, 7, 0xE0807320, 4, 0)}
ENTRY = struct.Struct("<QQBBBBHHQ32s")
OPS = {"read": 1, "write": 2, "csrr": 3, "csrw": 4, "guard-end": 5,
       "guard-else": 6}

# The templates: the assembly as head.S and harts.S write it. A label that
# names an ELF symbol must be that symbol's address.
ACCESS = """
lla t0, be_m13_table; lla t1, be_m13_table_end; sub t1, t1, t0
srli t1, t1, 6; bgeu a0, t1, 9; slli t1, a0, 6; add t0, t0, t1
ld t2, 0(t0); lbu t3, 16(t0); lbu t4, 17(t0); addi t5, t4, -1
and t5, t5, t2; bnez t5, 9; li t5, 1; beq t3, t5, 1; li t5, 2
bne t3, t5, 9; li t5, 4; bne t4, t5, 9; ld a1, 8(t0); fence iorw, iorw
be_m13_site_sw: sw a1, 0(t2); fence iorw, iorw; li a0, 0; ret
1: li t5, 8; beq t4, t5, 2; li t5, 4; bne t4, t5, 9; fence iorw, iorw
be_m13_site_lw: lwu a1, 0(t2); fence iorw, iorw; li a0, 0; ret
2: fence iorw, iorw
be_m13_site_ld: ld a1, 0(t2); fence iorw, iorw; li a0, 0; ret
be_m13_access_fault: li a0, 1; li a1, 0; ret
9: li a0, 2; li a1, 0; ret
"""
TRAP = """
csrr t0, sepc; csrr t1, scause; lla t2, be_m13_site_lw; beq t0, t2, 1
lla t2, be_m13_site_ld; beq t0, t2, 1; lla t2, be_m13_site_sw
bne t0, t2, 3; li t2, 7; bne t1, t2, 3; j 2
1: li t2, 5; bne t1, t2, 3
2: lla t2, be_m13_fault; sd t1, 0(t2); csrr t1, stval; sd t1, 8(t2)
lla t1, be_m13_access_fault; csrw sepc, t1; sret
3: mv a0, t1; mv a1, t0; csrr a2, stval; lla sp, __be_m13_stack_end
call be_m13_trap_fail; j be_m13_park
"""
P1 = """
andi t0, a0, 3; slli t0, t0, 6; lla t1, be_m13_slots; add t1, t1, t0
csrr t2, hgeie; sd t2, 8(t1); li t2, -1; csrw hgeie, t2; csrr t2, hgeie
sd t2, 16(t1); csrw hgeie, zero; csrr t2, hgeie; sd t2, 24(t1); ret
"""
HART_RUN = """
li t0, 2; bgtu a0, t0, 2; andi t1, a0, 3; slli t1, t1, 6
lla t5, be_m13_slots; add t5, t5, t1; li t1, 1; sd t1, 0(t5)
fence rw, rw; mv a2, a0; lla a1, be_m13_secondary; li a6, 0
li a7, 0x48534d
be_m13_ecall_hsm: ecall; bnez a0, 3; csrr t2, time; li t3, 0x8000000
add t2, t2, t3
1: fence rw, rw; ld a1, 0(t5); li t3, 1; bne a1, t3, 3; csrr t3, time
bltu t3, t2, 1; ret
2: li a0, -3; li a1, 0
3: fence rw, rw; ret
"""
TEMPLATES = (("device", "be_m13_access", ACCESS), ("trap", "be_m13_trap", TRAP),
             ("p1", "be_m13_p1", P1), ("hart-run", "be_m13_hart_run", HART_RUN))


def sext(value, bits):
    return value - (1 << bits) if value >> (bits - 1) & 1 else value


LOADS = dict(enumerate(("lb", "lh", "lw", "ld", "lbu", "lhu", "lwu")))
STORES = dict(enumerate(("sb", "sh", "sw", "sd")))
BRANCHES = {0: "beq", 1: "bne", 4: "blt", 5: "bge", 6: "bltu", 7: "bgeu"}
OP_IMM = {0: "addi", 2: "slti", 3: "sltiu", 4: "xori", 6: "ori", 7: "andi"}
OP = dict(zip(((0, 0), (32, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
               (32, 5), (0, 6), (0, 7), (1, 0), (1, 1), (1, 2), (1, 3),
               (1, 4), (1, 5), (1, 6), (1, 7)),
              "add sub sll slt sltu xor srl sra or and mul mulh mulhsu mulhu "
              "div divu rem remu".split()))
OP32 = dict(zip(((0, 0), (32, 0), (0, 1), (0, 5), (32, 5), (1, 0), (1, 4),
                 (1, 5), (1, 6), (1, 7)),
                "addw subw sllw srlw sraw mulw divw divuw remw remuw".split()))
CSR_OPS = {1: "csrrw", 2: "csrrs", 3: "csrrc", 5: "csrrwi", 6: "csrrsi",
           7: "csrrci"}
SYSTEM = {0x73: "ecall", 0x100073: "ebreak", 0x10200073: "sret",
          0x30200073: "mret", 0x10500073: "wfi"}


def decode(word):
    """(name, rd, rs1, rs2, imm) of an RV64IM, Zicsr, or Zifencei word (a
    CSR's number in imm; fence's fm, pred, succ); the name `system` for any
    other SYSTEM word; None for a word that is no such instruction."""
    op, rd, f3 = word & 0x7F, word >> 7 & 31, word >> 12 & 7
    rs1, rs2, f7, imm = word >> 15 & 31, word >> 20 & 31, word >> 25, \
        sext(word >> 20, 12)
    if op in (0x37, 0x17):
        return ("lui" if op == 0x37 else "auipc", rd, 0, 0,
                sext(word & 0xFFFFF000, 32))
    if op == 0x6F:
        return ("jal", rd, 0, 0, sext(word >> 31 << 20 | (word >> 12 & 0xFF)
                                      << 12 | (word >> 20 & 1) << 11 |
                                      (word >> 21 & 0x3FF) << 1, 21))
    if op == 0x67 and f3 == 0:
        return ("jalr", rd, rs1, 0, imm)
    if op == 0x63 and f3 in BRANCHES:
        return (BRANCHES[f3], 0, rs1, rs2, sext(word >> 31 << 12 | (word >> 7
                                                & 1) << 11 | (word >> 25 &
                                                0x3F) << 5 | (word >> 8 & 0xF)
                                                << 1, 13))
    if op == 0x03 and f3 in LOADS:
        return (LOADS[f3], rd, rs1, 0, imm)
    if op == 0x23 and f3 in STORES:
        return (STORES[f3], 0, rs1, rs2, sext(f7 << 5 | rd, 12))
    if op == 0x13 and f3 in (1, 5) and f7 >> 1 in (0, 16) and \
            (f3 == 5 or f7 >> 1 == 0):
        return ({1: "slli", 5: "srli"}[f3] if f7 >> 1 == 0 else "srai", rd,
                rs1, 0, word >> 20 & 0x3F)
    if op == 0x13 and f3 in OP_IMM:
        return (OP_IMM[f3], rd, rs1, 0, imm)
    if op == 0x1B and f3 == 0:
        return ("addiw", rd, rs1, 0, imm)
    if op == 0x1B and (f7, f3) in ((0, 1), (0, 5), (32, 5)):
        return ({(0, 1): "slliw", (0, 5): "srliw"}.get((f7, f3), "sraiw"),
                rd, rs1, 0, rs2)
    if op in (0x33, 0x3B) and (f7, f3) in (OP if op == 0x33 else OP32):
        return ((OP if op == 0x33 else OP32)[f7, f3], rd, rs1, rs2, 0)
    if op == 0x0F and f3 in (0, 1):
        return ("fence" if f3 == 0 else "fence.i", 0, 0, 0, word >> 20)
    if op == 0x73:
        return (CSR_OPS[f3], rd, rs1, 0, word >> 20) if f3 in CSR_OPS else \
            (SYSTEM.get(word, "system"), 0, 0, 0, 0)
    if op == 0x2F:
        return ("amo", rd, rs1, rs2, 0)
    return None


def writes(ins):
    """The register that INS writes, or None."""
    if ins is None or ins[0] in STORES.values() or ins[0] in \
            BRANCHES.values() or ins[0] in ("fence", "fence.i", "system",
                                             "ecall", "ebreak", "sret",
                                             "mret", "wfi"):
        return None
    return ins[1] or None


def pseudo(name, ops):
    """A template line's instructions, (name, rd, rs1, rs2, imm), imm a
    symbol's ("hi"|"lo", NAME) of an auipc pair or ("to", LABEL)."""
    r = REGS.index
    if name in ("lla", "call"):
        rd, sym = (r(ops[0]), ops[1]) if name == "lla" else (1, ops[0])
        return [("auipc", rd, 0, 0, ("hi", sym)),
                ("addi" if name == "lla" else "jalr", rd, rd, 0, ("lo", sym))]
    if name == "li":
        value = int(ops[1], 0)
        low = sext(value & 0xFFF, 12)
        if -2048 <= value < 2048:
            return [("addi", r(ops[0]), 0, 0, value)]
        return [("lui", r(ops[0]), 0, 0, sext((value - low) & 0xFFFFFFFF,
                                              32))] + \
            ([("addiw", r(ops[0]), r(ops[0]), 0, low)] if low else [])
    if name in ("csrr", "csrw"):
        return [("csrrs", r(ops[0]), 0, 0, CSRS[ops[1]]) if name == "csrr"
                else ("csrrw", 0, r(ops[1]), 0, CSRS[ops[0]])]
    if name == "fence":
        bits = {"iorw": 15, "rw": 3}
        return [("fence", 0, 0, 0, bits[ops[0]] << 4 | bits[ops[1]])]
    if name in ("ret", "sret", "ecall", "j", "mv", "bnez", "bgtu"):
        return [{"ret": ("jalr", 0, 1, 0, 0), "sret": ("sret", 0, 0, 0, 0),
                 "ecall": ("ecall", 0, 0, 0, 0)}.get(name) or
                {"j": lambda: ("jal", 0, 0, 0, ("to", ops[0])),
                 "mv": lambda: ("addi", r(ops[0]), r(ops[1]), 0, 0),
                 "bnez": lambda: ("bne", 0, r(ops[0]), 0, ("to", ops[1])),
                 "bgtu": lambda: ("bltu", 0, r(ops[1]), r(ops[0]),
                                  ("to", ops[2]))}[name]()]
    if name in BRANCHES.values():
        return [(name, 0, r(ops[0]), r(ops[1]), ("to", ops[2]))]
    if name in LOADS.values() or name in STORES.values():
        offset, base = ops[1].rstrip(")").split("(")
        return [(name, 0 if name in STORES.values() else r(ops[0]), r(base),
                 r(ops[0]) if name in STORES.values() else 0, int(offset))]
    if name in ("add", "sub", "and"):
        return [(name, r(ops[0]), r(ops[1]), r(ops[2]), 0)]
    return [(name, r(ops[0]), r(ops[1]), 0, int(ops[2], 0))]


def expand(text):
    specs, labels = [], {}
    for item in text.replace("\n", ";").split(";"):
        if not item.strip():
            continue
        if ":" in item:
            label, item = item.split(":", 1)
            labels[label.strip()] = len(specs)
        name, _, rest = item.strip().partition(" ")
        specs += pseudo(name, [o.strip() for o in rest.split(",") if o])
    return specs, labels


class Image:
    """The ELF's sections, symbols, and segments, and IMG's bytes."""

    def __init__(self, elf, img):
        if elf[:6] != b"\x7fELF\x02\x01":
            raise ValueError("not a little-endian ELF64")
        self.elf, self.img = elf, img
        self.entry, phoff, shoff = struct.unpack_from("<QQQ", elf, 24)
        phsize, phnum, shsize, shnum, shstr = struct.unpack_from("<HHHHH",
                                                                 elf, 54)
        raw = [struct.unpack_from("<IIQQQQII", elf, shoff + i * shsize)
               for i in range(shnum)]
        names = raw[shstr][4]

        def name_at(table, offset):
            end = elf.index(b"\0", table + offset)
            return elf[table + offset:end].decode("ascii")
        self.sections = {name_at(names, s[0]): s for s in raw}
        self.segments = [struct.unpack_from("<IIQQQQQ", elf, phoff + i *
                                            phsize) for i in range(phnum)]
        self.symbols, self.functions = {}, []
        for section in (s for s in raw if s[1] == 2):
            strings = raw[section[6]][4]
            for k in range(1, section[5] // 24):
                sym_name, info, _, _, value, size = struct.unpack_from(
                    "<IBBHQQ", elf, section[4] + 24 * k)
                text = name_at(strings, sym_name)
                self.symbols.setdefault(text, (value, size))
                if info & 15 == 2:
                    self.functions.append((value, size, text))
        self.functions.sort()
        self.base = min((s[3] for s in self.segments if s[0] == 1),
                        default=0)

    def word(self, address):
        offset = address - self.base
        return struct.unpack_from("<I", self.img, offset)[0] \
            if 0 <= offset <= len(self.img) - 4 else 0

    def code(self, name):
        value, size = self.symbols[name]
        return [(value + 4 * k, decode(self.word(value + 4 * k)))
                for k in range(size // 4)]


def flat(image):
    """IMG as the ELF's PT_LOAD segments make it, or None."""
    loads = sorted((s for s in image.segments if s[0] == 1),
                   key=lambda s: s[3])
    if not loads or any(s[5] != s[6] for s in loads):
        return None
    out = bytearray(loads[-1][3] + loads[-1][5] - image.base)
    for s in loads:
        out[s[3] - image.base:s[3] - image.base + s[5]] = \
            image.elf[s[2]:s[2] + s[5]]
    return bytes(out)


def runs(code):
    """The index at which each instruction's straight-line run starts: after
    a branch, jump, or ecall, or at a branch target."""
    targets = {pc + ins[4] for pc, ins in code if ins and
               (ins[0] in BRANCHES.values() or ins[0] == "jal")}
    start, starts = 0, []
    for k, (pc, ins) in enumerate(code):
        if k and (pc in targets or code[k - 1][1] is None or
                  code[k - 1][1][0] in set(BRANCHES.values()) |
                  {"jal", "jalr", "ecall"}):
            start = k
        starts.append(start)
    return starts


def resolve(code, k, reg, low):
    """What REG holds before instruction K, from its run, which starts at
    LOW: ("addr", A) for an auipc pair, ("const", V) for li, ("mask",) for
    x & 3, ("index",) for that shifted by 6, ("indexed", A) for an address
    plus such an index."""
    for j in range(k - 1, low - 1, -1):
        ins = code[j][1]
        if writes(ins) != reg:
            continue
        name, rd, rs1, rs2, imm = ins
        prev = code[j - 1][1] if j > low else None
        if name == "addi" and rs1 == 0:
            return ("const", imm)
        if name in ("addi", "addiw") and prev and prev[1] == rd == \
                rs1 and prev[0] in ("auipc", "lui"):
            return ("addr", code[j - 1][0] + prev[4] + imm) if prev[0] == \
                "auipc" else ("const", sext((prev[4] + imm) & 0xFFFFFFFF, 32))
        if name == "lui":
            return ("const", imm)
        if name == "andi" and imm == 3:
            return ("mask",)
        if name == "slli" and imm == 6 and \
                resolve(code, j, rs1, low) == ("mask",):
            return ("index",)
        if name == "add":
            pair = sorted([resolve(code, j, rs1, low),
                           resolve(code, j, rs2, low)], key=str)
            if pair[0] and pair[0][0] == "addr" and pair[1] == ("index",):
                return ("indexed", pair[0][1])
        return None
    return None


def match(image, tag, name, text, findings):
    expected, labels = expand(text)
    value, size = image.symbols[name]
    code = image.code(name)

    def want(k, spec):
        imm = spec[4]
        if isinstance(imm, tuple):
            pc, sym = value + 4 * k, imm[1]
            target = value + 4 * labels[sym] if sym in labels else \
                image.symbols.get(sym, (-1,))[0]
            delta = target - (pc if imm[0] in ("hi", "to") else pc - 4)
            high = sext((delta + 0x800) & ~0xFFF & 0xFFFFFFFF, 32)
            imm = {"hi": high, "lo": delta - high, "to": delta}[imm[0]]
        return spec[:4] + (imm,)
    if size != 4 * len(expected):
        findings.append(f"[{tag}] {name} is not its template's length")
        return
    for k, spec in enumerate(expected):
        if code[k][1] != want(k, spec):
            findings.append(f"[{tag}] {name}: instruction {k} is not its "
                            "template's")
            return
    for label, k in labels.items():
        if label.startswith("be_m13_") and \
                image.symbols.get(label, (None,))[0] != value + 4 * k:
            findings.append(f"[{tag}] {label} is not at its template's place")


def check_table(image, listing, number, findings):
    table = image.symbols.get("be_m13_table", (0,))[0] - image.base
    end = image.symbols.get("be_m13_table_end", (0,))[0] - image.base
    digit = image.symbols.get("be_m13_image", (0,))[0] - image.base
    entries = [image.img[o:o + 64] for o in range(table, end, 64)]
    if listing.image != number or (listing.harts, listing.probes) != \
            {1: (3, [1, 7]), 2: (1, [3, 4, 2])}.get(number,
                                                     (1, listing.probes)):
        findings.append("[table] the list's image, harts, or probes are not "
                        "this image's")
    if not 0 <= digit < len(image.img) or image.img[digit] != 0x30 + number \
            or len(entries) != len(listing.entries) or (end - table) % 64:
        findings.append("[table] the image's digit or the table's length is "
                        "not the list's")
    for e, raw in zip(listing.entries, entries):
        if raw != ENTRY.pack(e.address, e.value, OPS[e.op], e.width, e.probe,
                             e.hart, e.ref, 0, 0, e.name.encode()):
            findings.append(f"[table] entry {e.index} is not the list's")
    for e in listing.entries:
        if e.op in ("write", "csrw") and (OPS[e.op], e.probe, e.address,
                                          e.width, e.value) not in WRITES:
            findings.append(f"[writes] the list's entry {e.index} is not a "
                            "write of the page's")
    for k, raw in enumerate(entries):
        address, value, op, width, probe = ENTRY.unpack(raw)[:5]
        if op in (2, 4) and (op, probe, address, width, value) not in WRITES:
            findings.append(f"[writes] the table's entry {k} is not a write "
                            "of the page's")
    return len(entries), {e.address for e in listing.entries
                          if e.op in ("read", "write")}


def check_code(image, number, findings, facts):
    sym = image.symbols
    text = image.sections.get(".text", (0,) * 8)
    covered = [f for f in image.functions if f[0] >= text[3]]
    if sum(f[1] for f in covered) != text[5] or any(
            a[0] + a[1] != b[0] for a, b in zip(covered, covered[1:])) or \
            covered[0][0] != text[3]:
        findings.append("[control] .text is not covered by its functions "
                        "once each")
    hsm = number == 1
    if any(hsm != (n in sym) for n in ("be_m13_hart_run", "be_m13_ecall_hsm",
                                       "be_m13_p1")):
        findings.append("[hsm] HSM's start is not in image 1 alone")
    entries = {f[0]: f[2] for f in covered}
    c_functions = {f[2] for f in covered if f[2] not in ASM}
    labels = {sym[n][0]: n for n in NO_TARGET if n in sym}
    ecalls, c_access = 0, {"sp": 0, "other": 0}
    for start, size, name in covered:
        code = image.code(name)
        starts = runs(code)
        for k, (pc, ins) in enumerate(code):
            if ins is None:
                findings.append(f"[control] {name}: a word that is no "
                                "instruction")
                continue
            op, rd, rs1, rs2, imm = ins
            if name not in ASM:
                if op.startswith("csr") or op in ("ecall", "sret", "wfi",
                                                  "mret", "ebreak", "system",
                                                  "fence.i", "amo") or \
                        op == "jalr" and ins != ("jalr", 0, 1, 0, 0) and not (
                            paired(code, k) and rd in (0, 1)):
                    findings.append(f"[c] {name}: a SYSTEM, AMO, fence.i, or "
                                    "indirect jump")
                if op in LOADS.values() or op in STORES.values():
                    c_access["sp" if rs1 == 2 else "other"] += 1
            if op == "jalr" and ins != ("jalr", 0, 1, 0, 0) and \
                    not paired(code, k):
                findings.append(f"[control] {name}: an indirect jump")
            if op in ("mret", "ebreak", "system", "fence.i", "amo") or \
                    op == "sret" and name != "be_m13_trap" or \
                    op == "wfi" and name != "be_m13_park":
                findings.append(f"[system] {name}: a SYSTEM instruction out "
                                "of its place")
            if op.startswith("csr"):
                check_csr(name, code, k, starts, sym, findings)
            if op == "ecall":
                ecalls += 1
                label = labels.get(pc, "")
                need = ECALLS.get(label)
                if need is None or label == "be_m13_ecall_hsm" and not hsm or \
                        any(resolve(code, k, REGS.index(r), starts[k]) !=
                            ("const", v) for r, v in need.items()):
                    findings.append(f"[ecall] {name}: an ecall not at its "
                                    "label with its registers")
            if rd == 17 and not hsm and resolve(code, k + 1, 17, starts[k]) \
                    == ("const", 0x48534D):
                findings.append(f"[hsm] {name}: a7 of HSM in an image that "
                                "starts no hart")
            target = None
            if op == "jal" or op in BRANCHES.values():
                target = pc + imm
            elif op == "jalr" and paired(code, k):
                target = code[k - 1][0] + code[k - 1][1][4] + imm
            if target is None:
                continue
            inside = start <= target < start + size
            allowed = ASM_CALLS.get(name, set()) if name in ASM else \
                C_CALLS | c_functions
            if target in labels or not inside and (
                    op in BRANCHES.values() or entries.get(target) not in
                    allowed):
                findings.append(f"[control] {name}: a jump or call to where "
                                "it may not go")
    if ecalls != len([n for n in ECALLS if n in sym]) or \
            hsm != ("be_m13_ecall_hsm" in sym):
        findings.append("[ecall] the ecalls are not the image's labels")
    facts.append(f"functions={len(covered)} c_loads_stores_sp="
                 f"{c_access['sp']} c_loads_stores_other={c_access['other']} "
                 f"ecalls={ecalls}")


def paired(code, k):
    """Instruction K, a jalr, is the second of an auipc pair."""
    return k > 0 and code[k - 1][1] is not None and \
        code[k - 1][1][:2] == ("auipc", code[k][1][2])


def check_csr(name, code, k, starts, sym, findings):
    op, rd, rs1, _, csr = code[k][1]
    if op in ("csrrs", "csrrc", "csrrsi", "csrrci") and rs1 == 0:
        if csr not in READABLE:
            findings.append(f"[csr] {name}: a read of a CSR out of the list")
        return
    value = resolve(code, k, rs1, starts[k]) if op == "csrrw" else None
    own = {"be_m13_entry": "be_m13_trap",
           "be_m13_secondary": "be_m13_secondary_trap"}
    allowed = (name in own and (
        (op, rd, csr, rs1) in (("csrrci", 0, CSRS["sstatus"], 2),
                               ("csrrw", 0, CSRS["sie"], 0)) or
        (op, rd, csr) == ("csrrw", 0, CSRS["stvec"]) and
        value == ("addr", sym[own[name]][0])) or
        name == "be_m13_trap" and (op, rd, csr) == ("csrrw", 0, CSRS["sepc"])
        and value == ("addr", sym.get("be_m13_access_fault", (-1,))[0]) or
        name == "be_m13_p1" and (op, rd, csr) == ("csrrw", 0, CSRS["hgeie"])
        and (rs1 == 0 or value == ("const", -1)))
    if not allowed:
        findings.append(f"[csr] {name}: a CSR write out of the list")


def check_stores(image, findings):
    sym, objects = image.symbols, {}
    for object_name in ("be_m13_fault", "be_m13_slots"):
        if object_name in sym:
            objects[sym[object_name][0]] = sym[object_name][1]
    s0 = None
    if "be_m13_secondary" in sym:
        code = image.code("be_m13_secondary")
        starts = runs(code)
        setting = [k for k, (_, ins) in enumerate(code) if writes(ins) == 8]
        others = [n for n in ("be_m13_secondary_trap", "be_m13_p1",
                              "be_m13_park") if n in sym and any(
                                  writes(i) == 8 for _, i in image.code(n))]
        if setting and not others and \
                len({starts[k] for k in setting}) == 1:
            s0 = (setting[-1], resolve(code, setting[-1] + 1, 8,
                                       starts[setting[-1]]))
    for name in sorted(ASM & set(sym)):
        code = image.code(name)
        starts = runs(code)
        for k, (pc, ins) in enumerate(code):
            if not ins or ins[0] not in STORES.values() or \
                    pc == sym.get("be_m13_site_sw", (-1,))[0]:
                continue
            width, base, offset = 1 << "bhwd".index(ins[0][1]), ins[2], ins[4]
            if base == 2:
                continue
            value = resolve(code, k, base, starts[k])
            if base == 8 and s0 and (name == "be_m13_secondary_trap" or
                                     name == "be_m13_secondary" and
                                     k > s0[0]):
                value = s0[1]
            spread = 192 if value and value[0] == "indexed" else 0
            if not value or value[0] not in ("addr", "indexed") or \
                    value[1] not in objects or offset < 0 or \
                    spread + offset + width > objects[value[1]]:
                findings.append(f"[store] {name}: a store not inside one of "
                                "the image's data objects")


def check_hsm(image, findings):
    if "be_m13_hart_run" not in image.symbols:
        return
    code = image.code("be_m13_hart_run")
    starts = runs(code)
    calls = [k for k, (_, ins) in enumerate(code) if ins and ins[0] ==
             "ecall"]
    if code[0][1] != ("addi", 5, 0, 0, 2) or code[1][1][:4] != \
            ("bltu", 0, 5, 10) or len(calls) != 1 or \
            any(writes(code[j][1]) == 10 for j in range(2, calls[0])) or \
            resolve(code, calls[0], 11, starts[calls[0]]) != \
            ("addr", image.symbols["be_m13_secondary"][0]):
        findings.append("[hsm] be_m13_hart_run does not bound the hart to 0 "
                        "to 2, or does not start it at be_m13_secondary")


def check_data(image, table, addresses, findings):
    for section in (".rodata", ".data"):
        _, _, _, addr, _, size = image.sections.get(section, (0,) * 8)[:6]
        for offset in range(0, size - 3, 4):
            at = addr + offset
            if table[0] <= at < table[1]:
                continue
            raw = image.img[at - image.base:at - image.base + 8]
            if struct.unpack_from("<I", raw)[0] in addresses or (
                    offset % 8 == 0 and len(raw) == 8 and
                    struct.unpack("<Q", raw)[0] in addresses):
                findings.append(f"[data] a word of {section} is an address "
                                "of the list")


def check(elf, img, other, listing, number, findings, facts):
    try:
        image = Image(elf, img)
    except (ValueError, struct.error, IndexError):
        findings.append("[extent] the ELF cannot be read")
        return 0
    header = []
    got = load("b3", HERE.parents[1] / "k3-b3/tests/check-b3-image.py") \
        .check_header(img, 0x200000, header)
    findings += [f"[header] {h}" for h in header]
    if not got or got["entry"] != 0x60 or img[0x40:0x60] != bytes(32) or \
            image.symbols.get("be_m13_entry", (0,))[0] != image.base + 0x60:
        findings.append("[header] code0 does not jump to be_m13_entry at "
                        "+0x60, or 0x40 to 0x5F are not zero")
    sym = image.symbols
    if image.entry != image.base or image.base != BOARD_BASE or \
            flat(image) != img or len(img) > IMAGE_MAX or any(
                s[2] & 2 and s[1] != 1 for s in image.sections.values()) or \
            sym.get("__be_m13_stack_end", (0,))[0] != image.base + len(img) \
            or sym["__be_m13_stack_end"][0] - \
            sym.get("__be_m13_stack_start", (0,))[0] != STACK:
        findings.append("[extent] the image is not the ELF's segments, "
                        "PROGBITS, at most 64 KiB, at the board's base, "
                        "ending with its stack")
    if other is not None:
        try:
            linked = Image(other, b"")
            if linked.base != QEMU_BASE or flat(linked) != img:
                findings.append("[base] the build at 0x80200000 does not "
                                "give the image's bytes")
        except (ValueError, struct.error, IndexError):
            findings.append("[base] the build at 0x80200000 cannot be read")
    entries, addresses = check_table(image, listing, number, findings)
    for tag, name, text in TEMPLATES:
        if name in sym or tag in ("device", "trap") or number == 1:
            if name not in sym:
                findings.append(f"[{tag}] {name} is missing")
            else:
                match(image, tag, name, text, findings)
    check_code(image, number, findings, facts)
    check_stores(image, findings)
    check_hsm(image, findings)
    check_data(image, (sym.get("be_m13_image", (0,))[0],
                       sym.get("be_m13_table_end", (0,))[0]), addresses,
               findings)
    return entries


def load(name, path, cache={}):
    """A module by its path, once."""
    if name not in cache:
        spec = importlib.util.spec_from_file_location(name, path)
        cache[name] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cache[name])
    return cache[name]


def encode(name, rd=0, rs1=0, rs2=0, imm=0):
    """One instruction's word, for the self-test's mutations."""
    if name in ("addi", "lui"):
        return (imm & ~0xFFF | rd << 7 | 0x37) & 0xFFFFFFFF if name == "lui" \
            else (imm & 0xFFF) << 20 | rs1 << 15 | rd << 7 | 0x13
    if name == "sw":
        return (imm >> 5 & 0x7F) << 25 | rs2 << 20 | rs1 << 15 | 2 << 12 | \
            (imm & 31) << 7 | 0x23
    if name == "csrrw":
        return imm << 20 | rs1 << 15 | 1 << 12 | rd << 7 | 0x73
    return (imm >> 20 & 1) << 31 | (imm >> 1 & 0x3FF) << 21 | \
        (imm >> 11 & 1) << 20 | (imm >> 12 & 0xFF) << 12 | rd << 7 | 0x6F


def self_test(elf, img, other, listing, number):
    image = Image(elf, img)
    sym = image.symbols

    def text_offset(address):
        section = next(s for s in image.sections.values() if s[2] & 2 and
                       s[3] <= address < s[3] + s[5])
        return section[4] + address - section[3]

    def put(state, address, raw):
        state[0][text_offset(address):text_offset(address) + len(raw)] = raw
        state[1][address - image.base:address - image.base + len(raw)] = raw

    def word(state, address, value):
        put(state, address, struct.pack("<I", value))

    def first(name, op, nth=0):
        hits = [pc for pc, ins in image.code(name) if ins and ins[0] == op]
        return hits[nth]

    text = image.sections[".text"][3]
    c_name = next(n for v, _, n in image.functions if v >= text and n not in
                  ASM and any(i and i[0] == "auipc" for _, i in
                              image.code(n)))
    c_call = next(pc for pc, i in image.code(c_name) if i and i[0] ==
                  "auipc")
    device = next(e.address for e in listing.entries if e.op == "read")
    table = sym["be_m13_table"][0]
    write = next((e for e in listing.entries if e.op == "write"), None)
    target = sym["be_m13_ecall_hsm" if number == 1 else SITES[2]][0]
    cases = [
        ("text_offset 0", "header", lambda s: put(s, image.base + 8,
                                                  bytes(8))),
        ("magic2", "header", lambda s: put(s, image.base + 0x38, b"RSC\x06")),
        ("4 bytes short", "extent", lambda s: s[1].__delitem__(
            slice(len(s[1]) - 4, None))),
        ("a byte at 0x80200000", "base", lambda s: s[2].__setitem__(
            text_offset(image.base + 0x100), s[2][text_offset(
                image.base + 0x100)] ^ 1)),
        ("an address + 4", "table", lambda s: put(s, table, struct.pack(
            "<Q", listing.entries[0].address + 4))),
        ("a name", "table", lambda s: put(s, table + 32, b"Q")),
        ("site_sw's fence a store", "device", lambda s: word(
            s, sym[SITES[2]][0] + 4, encode("sw", rs1=7, rs2=11, imm=4))),
        ("the bound a nop", "device", lambda s: word(
            s, first("be_m13_access", "bgeu"), encode("addi"))),
        ("sie made sscratch", "csr", lambda s: word(
            s, sym["be_m13_entry"][0] + 4, encode("csrrw", imm=0x140))),
        ("a C csrw satp", "c", lambda s: word(s, c_call, encode(
            "csrrw", imm=0x180))),
        ("a C ecall", "ecall", lambda s: word(s, c_call, 0x73)),
        ("a store's base", "store", lambda s: word(
            s, first("be_m13_p1" if number == 1 else "be_m13_trap", "sd"),
            encode("sw", rs1=11, rs2=7, imm=8))),
        ("a C jal to a label", "control", lambda s: word(
            s, c_call, encode("jal", rd=1, imm=target - c_call))),
        ("an indirect jump in be_m13_putc", "control", lambda s: word(
            s, first("be_m13_putc", "jalr"), 5 << 15 | 0x67)),
        ("a word of .data", "data", lambda s: put(
            s, image.sections[".data"][3] + 16, struct.pack("<Q", device)))]
    read = next(e.index for e in listing.entries if e.op == "read")
    cases += [("a table read made a write", "writes", lambda s: put(
        s, table + 64 * read + 16, b"\x02")),
        ("the vector resumes any sepc", "trap", lambda s: word(
        s, first("be_m13_trap", "bne"), encode("addi"))),
        ("a wfi outside the park", "system", lambda s: word(
            s, sym["be_m13_putc"][0], 0x10500073))]
    if write is not None:
        cases.append(("a write elsewhere", "writes", None))
    if number == 1:
        cases += [("hart 3", "hsm", lambda s: word(
            s, sym["be_m13_hart_run"][0], encode("addi", rd=5, imm=3))),
            ("P1 writes 0x55", "p1", lambda s: word(
                s, first("be_m13_p1", "addi", 1), encode("addi", rd=7,
                                                         imm=0x55))),
            ("a shorter wait", "hart-run", lambda s: word(
                s, first("be_m13_hart_run", "lui", 1), encode(
                    "lui", rd=28, imm=0x1000)))]
    else:
        srst = first("be_m13_srst", "lui")
        cases += [(f"SRST's a7 HSM's ({tag})", tag, lambda s: (
            word(s, srst, encode("lui", rd=17, imm=0x485000)),
            word(s, srst + 4, 0x34D << 20 | 17 << 15 | 17 << 7 | 0x1B)))
            for tag in ("ecall", "hsm")]
    findings, facts = [], []
    check(elf, img, other, listing, number, findings, facts)
    failed = [f"as built: {f}" for f in findings]
    for name, tag, mutate in cases:
        state = [bytearray(elf), bytearray(img), bytearray(other)]
        mutated = listing
        if mutate is None:
            mutated = copy.deepcopy(listing)
            mutated.entries[write.index].address += 4
            put(state, table + 64 * write.index, struct.pack(
                "<Q", write.address + 4))
        else:
            mutate(state)
        got = []
        check(bytes(state[0]), bytes(state[1]), bytes(state[2]), mutated,
              number, got, [])
        if not any(f.startswith(f"[{tag}]") for f in got):
            failed.append(f"{name}: no [{tag}] finding")
    for line in failed:
        print(f"finding: self-test {line}")
    verdict = "FAIL" if failed else "PASS"
    print(f"BE_K3_M13_IMAGE_SELF_TEST: {verdict} image={number} "
          f"cases={len(cases)}")
    return 1 if failed else 0


def main(argv):
    parser = argparse.ArgumentParser(prog="check-image.py")
    parser.add_argument("--image", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--expect", required=True)
    parser.add_argument("--other-base")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--expand", action="store_true")
    parser.add_argument("elf", nargs="?")
    parser.add_argument("img", nargs="?")
    args = parser.parse_args(argv)
    lists = load("m13list", HERE / "m13list.py")
    if args.expand == bool(args.elf and args.img):
        parser.error("ELF and IMG, or --expand alone")
    try:
        listing = lists.parse(args.expect)
        if args.expand:
            for e in listing.entries:
                print(f"{e.index:3} P{e.probe} {e.op} {e.name} "
                      f"0x{e.address:x} {e.width} 0x{e.value:x} {e.ref}")
            return 0
        elf, img = (pathlib.Path(p).read_bytes() for p in (args.elf,
                                                            args.img))
        other = pathlib.Path(args.other_base).read_bytes() \
            if args.other_base else None
    except OSError:
        print("BE_K3_M13_IMAGE: FAIL an input cannot be read")
        return 2
    except lists.ListError as error:
        print(f"BE_K3_M13_IMAGE: FAIL the list: {error}")
        return 2
    if args.self_test:
        if other is None:
            parser.error("--self-test needs --other-base")
        return self_test(elf, img, other, listing, args.image)
    findings, facts = [], []
    entries = check(elf, img, other, listing, args.image, findings, facts)
    for finding in findings:
        print(f"finding: {finding}")
    for fact in facts + [f"base={'checked' if other else 'not given'}"]:
        print(f"fact: {fact}")
    verdict = "FAIL" if findings else "PASS"
    print(f"BE_K3_M13_IMAGE: {verdict} image={args.image} entries={entries} "
          f"bytes={len(img)} sha256={hashlib.sha256(img).hexdigest()} "
          f"md5={hashlib.md5(img).hexdigest()}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
