#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Check B2 images: the ported R5 layout at the K3 base.

  check-b2-image.py --base B --lds ACCEPTED_R5_LDS --image TOOLCHAIN:ELF:BIN
                    [--image ...]

The expected layout is derived from the accepted R5 linker script
(arch/riscv/be/r5-beryllium.lds at 165f4d00, SHA-256 pinned), not restated:

- its PHDRS give the six PT_LOAD segments and their permissions, in order;
- every ASSERT in it (layout addresses, extents, overflow bounds, page and
  16 KiB root alignment, non-overlap, trap-vector placement, and fixture
  slot extents) must hold for the image's symbols moved back by
  0x81e00000, so every fixed layout symbol sits at its accepted QEMU
  address plus 0x81e00000;
- the span is [be_reset, __be_guest_protected_end) of those ASSERTs.

For each image: little-endian RV64 ET_EXEC; entry == be_reset == base;
PT_LOAD vaddr == paddr inside the span, in address order, no segment both
writable and executable; be_reset's first instructions call be_b1_quiesce
(inside monitor text) and then run the accepted first entry instruction
(mv s0, a0); and the flat binary is exactly the span: every segment's file
bytes in place and zeros elsewhere. All images must share one layout.
"""

import argparse
import hashlib
import re
import struct
import sys

DELTA = 0x81E00000
ACCEPTED_LDS_SHA256 = \
    "0df278b45d33500af08204b364a3f3e61178a7cd9981cb499025d95411baa56a"
# ASSERT conjuncts in the accepted R5 linker script; the parse must find all.
ACCEPTED_CONJUNCTS = 57
PF_X, PF_W, PF_R = 1, 2, 4
RISCV_MV_S0_A0 = 0x00050413  # addi s0, a0, 0: accepted be_reset's first


class ImageError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ImageError(message)


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
    """Evaluate one ASSERT conjunct: difference CMP difference.

    '&' is accepted only inside parentheses, as the accepted script writes
    every alignment test, so C's lower '&' precedence never matters.
    """
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


def accepted_layout(lds_path):
    data = open(lds_path, "rb").read()
    require(hashlib.sha256(data).hexdigest() == ACCEPTED_LDS_SHA256,
            f"{lds_path} is not the accepted R5 linker script")
    text = strip_comments(data.decode())
    phdrs = parse_phdrs(text)
    conjuncts = parse_asserts(text)
    require(len(conjuncts) == ACCEPTED_CONJUNCTS,
            f"parsed {len(conjuncts)} ASSERT conjuncts, "
            f"expected {ACCEPTED_CONJUNCTS}")
    fixed = {}
    for conjunct in conjuncts:
        match = re.fullmatch(r"(\w+) == (0x[0-9a-fA-F]+)", conjunct)
        if match:
            fixed[match.group(1)] = int(match.group(2), 16)
    require("be_reset" in fixed and "__be_guest_protected_end" in fixed,
            "accepted ASSERTs do not fix the image span")
    span = fixed["__be_guest_protected_end"] - fixed["be_reset"]
    return phdrs, conjuncts, fixed, span


# -------------------------------------------------------------------- ELF
def parse_elf(data):
    require(data[:7] == b"\x7fELF\x02\x01\x01", "not little-endian ELF64")
    e_type, e_machine = struct.unpack_from("<HH", data, 16)
    require(e_type == 2 and e_machine == 243, "not a RISC-V ET_EXEC")
    entry, phoff, shoff = struct.unpack_from("<QQQ", data, 24)
    phentsize, phnum, shentsize, shnum = struct.unpack_from("<HHHH", data, 54)
    segments = []
    for index in range(phnum):
        (p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz,
         _align) = struct.unpack_from("<IIQQQQQQ", data,
                                      phoff + index * phentsize)
        if p_type == 1:  # PT_LOAD
            segments.append((p_vaddr, p_paddr, p_offset, p_filesz, p_memsz,
                             p_flags))
    sections = [struct.unpack_from("<IIQQQQIIQQ", data, shoff + index * shentsize)
                for index in range(shnum)]
    symbols = {}
    for section in sections:
        if section[1] != 2:  # SHT_SYMTAB
            continue
        sym_offset, sym_size, sym_link = section[4], section[5], section[6]
        strtab_offset = sections[sym_link][4]
        for entry_offset in range(sym_offset, sym_offset + sym_size, 24):
            st_name, _, _, _, st_value, _ = struct.unpack_from(
                "<IBBHQQ", data, entry_offset)
            end = data.index(b"\0", strtab_offset + st_name)
            name = data[strtab_offset + st_name:end].decode()
            if name and not name.startswith("$"):  # skip mapping symbols
                # A name defined twice (two local statics) is unusable.
                symbols[name] = st_value if symbols.get(
                    name, st_value) == st_value else None
    return entry, segments, symbols


def call_target(flat, offset, pc):
    """Target of an auipc ra / jalr ra pair at offset, or None."""
    auipc, jalr = struct.unpack_from("<II", flat, offset)
    if auipc & 0xFFF != 0x097 or jalr & 0xFFFFF != 0x080E7:
        return None
    upper = auipc & 0xFFFFF000
    upper -= (upper & 0x80000000) << 1
    lower = jalr >> 20
    lower -= (lower & 0x800) << 1
    return pc + upper + lower


def check_image(base, layout, elf_path, bin_path):
    phdrs, conjuncts, fixed, span = layout
    data = open(elf_path, "rb").read()
    flat = open(bin_path, "rb").read()
    entry, segments, symbols = parse_elf(data)
    require(entry == base, f"entry 0x{entry:x} != base 0x{base:x}")
    require(symbols.get("be_reset") == base, "be_reset is not the base")
    require(len(segments) == len(phdrs),
            f"{len(segments)} PT_LOAD segments, accepted {len(phdrs)}")
    require(len(flat) == span, f"flat binary is 0x{len(flat):x} bytes, "
            f"span 0x{span:x}")
    covered = bytearray(span)
    previous_end = base
    for (vaddr, paddr, offset, filesz, memsz, flags), (name, wanted) in zip(
            segments, phdrs):
        require(vaddr == paddr, f"{name} 0x{vaddr:x} has paddr 0x{paddr:x}")
        require(previous_end <= paddr and paddr + memsz <= base + span,
                f"{name} 0x{paddr:x}+0x{memsz:x} is out of order or leaves "
                f"the span")
        require(not (flags & PF_W and flags & PF_X),
                f"{name} 0x{paddr:x} is writable and executable")
        require(flags == wanted, f"{name} flags {flags} != accepted {wanted}")
        start = paddr - base
        require(flat[start:start + filesz] == data[offset:offset + filesz],
                f"flat binary differs from {name} at 0x{paddr:x}")
        covered[start:start + filesz] = b"\1" * filesz
        previous_end = paddr + memsz
    require(all(byte == 0 for byte, inside in zip(flat, covered) if not inside),
            "flat binary has nonzero bytes outside the loaded segments")
    # The accepted ASSERTs, evaluated at the accepted QEMU addresses.
    require(DELTA % 0x4000 == 0, "the K3 delta breaks 16 KiB alignment")
    moved = {name: None if value is None else value - DELTA
             for name, value in symbols.items()}
    for conjunct in conjuncts:
        require(evaluate(conjunct, moved),
                f"accepted ASSERT fails at +0x{DELTA:x}: {conjunct}")
    quiesce = symbols.get("be_b1_quiesce")
    require(quiesce is not None and base <= quiesce <
            symbols["__be_monitor_code_end"],
            "be_b1_quiesce is outside monitor text")
    require(call_target(flat, 0, base) == quiesce,
            "be_reset does not first call be_b1_quiesce")
    require(struct.unpack_from("<I", flat, 8)[0] == RISCV_MV_S0_A0,
            "the accepted be_reset sequence does not follow the call")
    return {name: symbols[name] for name in fixed}, quiesce


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=lambda value: int(value, 0),
                        required=True)
    parser.add_argument("--lds", required=True)
    parser.add_argument("--image", action="append", required=True)
    args = parser.parse_args(argv[1:])
    layouts = []
    try:
        layout = accepted_layout(args.lds)
        require(args.base == layout[2]["be_reset"] + DELTA,
                f"base 0x{args.base:x} is not the accepted entry plus "
                f"0x{DELTA:x}")
        for spec in args.image:
            toolchain, elf_path, bin_path = spec.split(":")
            fixed, quiesce = check_image(args.base, layout, elf_path, bin_path)
            layouts.append(fixed)
            digest = hashlib.sha256(open(bin_path, "rb").read()).hexdigest()
            print(f"{toolchain}: entry=0x{args.base:x} "
                  f"be_b1_quiesce=0x{quiesce:x} asserts={len(layout[1])} "
                  f"fixed_symbols={len(fixed)} bin_sha256={digest}")
        require(all(fixed == layouts[0] for fixed in layouts),
                "toolchain layouts differ")
    except (ImageError, OSError, ValueError, struct.error) as error:
        print(f"BE_B2_IMAGE_CHECK: FAIL {error}")
        return 1
    span = layout[3]
    print(f"BE_B2_IMAGE_CHECK: PASS images={len(layouts)} "
          f"span=0x{args.base:x}-0x{args.base + span:x} "
          f"segments={len(layout[0])} asserts={len(layout[1])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
