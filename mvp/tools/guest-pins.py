#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Check the MVP guest outputs against guest/pins.txt (planning/mvp-m0-plan.md,
Guest software, Budgets, and Tests and evidence; B7's scripts/guest-pins.py
with MVP names), and the facts behind the pins.

  guest-pins.py --check --pins PINS --dir DIR --layout H [--gcc GCC]
  guest-pins.py --print --dir DIR --layout H [--gcc GCC]
  guest-pins.py --match NAME [--match NAME ...] --pins PINS --dir DIR
  guest-pins.py --sources --pins PINS
  guest-pins.py --keyring KEY --fingerprint FPR --output FILE
  guest-pins.py --self-test --layout H

--check re-hashes every output in DIR against its pin and checks:
  - the toolchain: the first line of `GCC --version` equals the pinned one,
    since the pins hold for one cross toolchain;
  - init: a static RV64 soft-float ELF executable, with no interpreter and
    no dynamic section, whose RISC-V arch attribute names only rv64imac,
    Zicsr, and the subsets they imply: no F, D, or V;
  - busybox (planning/mvp-m7-plan.md, D-9, Q5): the same, built against
    musl for rv64imac and lp64;
  - musl-libc.a, musl's static libc as installed: an ar archive whose every
    member header has mtime, uid, and gid 0 (ar's deterministic mode) and
    whose every ELF member is an RV64 soft-float relocatable object;
  - be-mgmt.ko, the management module (planning/mvp-m2-plan.md, Q2, Q16,
    Q20): an RV64 soft-float ELF relocatable object with one .modinfo and
    one .gnu.linkonce.this_module section and no __versions section, no
    signature appended, and a .modinfo of exactly name=be_mgmt,
    license=GPL, an empty depends, an author, a description, and a vermagic
    whose release is the banner's and which names neither mod_unload nor
    modversions (MODULE_UNLOAD, MODVERSIONS, and MODULE_SIG off);
  - Image: the RISC-V Image header (magic, magic2, little-endian flag,
    version 0.2), text_offset equal to BE_MVP_KERNEL_TEXT_OFFSET and the pin,
    image_size equal to the pin, at least the file size, at most
    BE_MVP_KERNEL_IMAGE_SIZE_MAX, and ending below the DTB slot; the file at
    most M7's Image budget, 0x300000 bytes (planning/mvp-m7-plan.md, Q13),
    which is below BE_MVP_KERNEL_FILE_MAX; and exactly one `Linux version`
    banner, equal to the pinned one;
  - every DTB: exactly BE_MVP_DTB_BYTES, a version-17 FDT header with an
    empty reservation map, and a decoded tree with exactly the plan's nodes
    and the values tools/gen-dts.py gives its guest and variant;
  - G0's and G1's DTBs: the same length, differing in one byte, the guest
    digit of bootargs;
  - the kernel's .config as built, DIR/kbuild/.config (planning/
    mvp-m9-plan.md, D-5: IMA is never used): no line sets CONFIG_IMA,
    CONFIG_IMA_*, CONFIG_EVM, or CONFIG_EVM_*, to any value; a "# ... is
    not set" line sets nothing.
Every mode that reads PINS also checks its `source` lines: the external
userland inputs, BusyBox and musl (planning/mvp-m7-plan.md, D-9, Q6), each
once, with its version, tag, commit, release tarball's HTTPS URL and
SHA-256, detached signature's HTTPS URL, public key file under guest/keys/
and its primary key's fingerprint, and licence. --sources reads those
lines alone, so that an unpinned build can fetch its inputs, and prints
them, one line each with the tarball's and signature's file names, for
tools/build-guest.sh and the evaluator.
--print makes the same fact checks without pins and prints the pin lines of
DIR's outputs, for a deliberate pin update. --match checks only the named
files' SHA-256 and size. --keyring reads an ASCII-armored public key,
checks its CRC-24, requires exactly one primary key, a version 4 key whose
fingerprint is FPR, and writes its packets to FILE: a keyring holding that
key alone, for gpgv. --self-test runs the checks on generated inputs and
in-memory defects.
"""

import argparse
import base64
import hashlib
import importlib.util
import pathlib
import re
import struct
import subprocess
import sys

LAYOUT_NAMES = ("KERNEL_FILE_MAX", "KERNEL_IMAGE_SIZE_MAX",
                "KERNEL_TEXT_OFFSET", "KERNEL_GPA", "DTB_GPA", "DTB_BYTES")
FILE_LINE = re.compile(r"^file (\S+) sha256=([0-9a-f]{64}) bytes=([0-9]+)$")
KERNEL_LINE = re.compile(r"^kernel (image_size|text_offset)=(0x[0-9a-f]+)$")
BANNER_LINE = re.compile(r"^kernel banner=(Linux version [ -~]+)$")
TOOLCHAIN_LINE = re.compile(r"^toolchain gcc=([ -~]+)$")
BANNER = b"Linux version "
IMAGE_MAGIC = b"RISCV\0\0\0"
IMAGE_MAGIC2 = b"RSC\x05"
IMAGE_VERSION = 0x2
FDT_MAGIC = 0xd00dfeed
FDT_BEGIN_NODE, FDT_END_NODE, FDT_PROP, FDT_NOP, FDT_END = 1, 2, 3, 4, 9
ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
ELF_PHDR = struct.Struct("<IIQQQQQQ")
ELF_SHDR = struct.Struct("<IIQQQQIIQQ")
EM_RISCV = 243
PT_LOAD, PT_DYNAMIC, PT_INTERP = 1, 2, 3
# The init's -march=rv64imac_zicsr and the subsets the toolchain records
# for it; anything else (F, D, V, ...) is refused.
INIT_ARCH_BASE = "rv64i"
INIT_ARCH_EXTENSIONS = {"m", "a", "c", "zicsr", "zmmul", "zaamo", "zalrsc",
                        "zca"}
TAG_FILE, TAG_RISCV_ARCH = 1, 5
U32 = 0xffffffff
# The management module's file, its object type, its .modinfo's fixed
# values and keys, and the trailer a signed module ends with.
MODULE = "be-mgmt.ko"
ET_REL = 1
SHT_NOBITS = 8
MODULE_INFO = {"name": "be_mgmt", "license": "GPL", "depends": ""}
MODULE_INFO_KEYS = {"name", "license", "depends", "author", "description",
                    "vermagic"}
MODULE_SIGNATURE = b"~Module signature appended~\n"
# M7's userland (planning/mvp-m7-plan.md, D-9): the static BusyBox, musl's
# libc.a, and the Image budget (Q13), below BE_MVP_KERNEL_FILE_MAX.
BUSYBOX, MUSL_LIBC = "busybox", "musl-libc.a"
IMAGE_BUDGET = 0x300000
AR_MAGIC = b"!<arch>\n"
AR_HEADER_BYTES = 60
# The external inputs' pin lines: each source once, with exactly these
# fields, in this order.
SOURCE_NAMES = ("busybox", "musl")
SOURCE_FIELDS = ("version", "tag", "commit", "url", "sha256", "signature",
                 "key", "fingerprint", "license")
SOURCE_FORMS = {
    "version": re.compile(r"[0-9]+(?:\.[0-9]+)+"),
    "tag": re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*"),
    "commit": re.compile(r"[0-9a-f]{40}"),
    "url": re.compile(r"https://[A-Za-z0-9.-]+(?:/[A-Za-z0-9._~-]+)+"),
    "sha256": re.compile(r"[0-9a-f]{64}"),
    "signature": re.compile(r"https://[A-Za-z0-9.-]+(?:/[A-Za-z0-9._~-]+)+"),
    "key": re.compile(r"guest/keys/[a-z0-9-]+\.asc"),
    "fingerprint": re.compile(r"[0-9A-F]{40}"),
    "license": re.compile(r"[A-Za-z0-9][A-Za-z0-9.+-]*"),
}
SOURCE_LINE = re.compile(r"^source (\S+)((?: [a-z0-9]+=\S+)+)$")
# OpenPGP (RFC 4880): the armor, its CRC-24, and the packets of a key.
ARMOR_BEGIN = "-----BEGIN PGP PUBLIC KEY BLOCK-----"
ARMOR_END = "-----END PGP PUBLIC KEY BLOCK-----"
CRC24_INIT, CRC24_POLY = 0xb704ce, 0x1864cfb
TAG_PUBLIC_KEY = 6


# D-5 (planning/mvp-m9-plan.md; mvp/docs/log-profile.md, 7): the guest
# kernel's .config as built, and the symbols it never sets.
KERNEL_CONFIG = pathlib.Path("kbuild") / ".config"
NEVER_SET = re.compile(r"CONFIG_(?:IMA|EVM)(?:_[A-Z0-9_]+)?")


class Finding(Exception):
    """One output or pin breaks a rule."""


def load_gen_dts():
    path = pathlib.Path(__file__).resolve().parent / "gen-dts.py"
    spec = importlib.util.spec_from_file_location("mvp_gen_dts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN_DTS = load_gen_dts()
DTB_FILES = {name: (guest, variant) for name, guest, variant in GEN_DTS.DTBS}
FILES = ("init", MODULE, BUSYBOX, MUSL_LIBC, "Image") + tuple(DTB_FILES)
PAIR = ("mvp-guest-g0.dtb", "mvp-guest-g1.dtb")


def parse_layout(text):
    layout = GEN_DTS.parse_layout(text)
    for name in LAYOUT_NAMES:
        if name not in layout:
            raise Finding(f"BE_MVP_{name} is missing from the layout")
    return layout


def parse_source(number, line):
    """One `source` line: (name, {field: value}), every field in its form,
    the tarball and signature named for the version (planning/
    mvp-m7-plan.md, D-9, Q6)."""
    match = SOURCE_LINE.match(line)
    if not match or match.group(1) not in SOURCE_NAMES:
        raise Finding(f"pins line {number}: not a source pin: {line!r}")
    name = match.group(1)
    pairs = [item.split("=", 1) for item in match.group(2).split()]
    if [key for key, _ in pairs] != list(SOURCE_FIELDS):
        raise Finding(f"pins line {number}: source {name}'s fields are not "
                      f"{' '.join(SOURCE_FIELDS)}, in that order")
    fields = dict(pairs)
    for key, value in fields.items():
        if not SOURCE_FORMS[key].fullmatch(value):
            raise Finding(f"pins line {number}: source {name}'s {key} "
                          f"{value!r} is malformed")
    tarball = fields["url"].rsplit("/", 1)[1]
    if not re.fullmatch(re.escape(f"{name}-{fields['version']}") +
                        r"\.tar\.(?:bz2|gz|xz)", tarball) or \
            fields["signature"] not in (fields["url"] + ".sig",
                                        fields["url"] + ".asc"):
        raise Finding(f"pins line {number}: source {name}'s tarball or "
                      "signature is not its version's")
    return name, fields


def parse_pins(text):
    """Return ({name: (sha256, bytes)}, {kernel/toolchain key: value}); the
    `source` lines must be well formed, each source once."""
    files, facts, sources = {}, {}, {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        if line.startswith("source "):
            name, fields = parse_source(number, line)
            if name in sources:
                raise Finding(f"pins line {number}: source {name} repeated")
            sources[name] = fields
            continue
        match = FILE_LINE.match(line)
        if match:
            name, sha, size = match.groups()
            if name not in FILES or name in files:
                raise Finding(f"pins line {number}: unexpected file {name}")
            files[name] = (sha, int(size))
            continue
        for pattern, key in ((KERNEL_LINE, None), (BANNER_LINE, "banner"),
                             (TOOLCHAIN_LINE, "gcc")):
            match = pattern.match(line)
            if match:
                key = key or match.group(1)
                if key in facts:
                    raise Finding(f"pins line {number}: {key} repeated")
                facts[key] = match.groups()[-1]
                break
        else:
            raise Finding(f"pins line {number}: not a pin: {line!r}")
    missing = [name for name in FILES if name not in files]
    missing += [key for key in ("image_size", "text_offset", "banner", "gcc")
                if key not in facts]
    missing += [f"source {name}" for name in SOURCE_NAMES
                if name not in sources]
    if missing:
        raise Finding(f"pins lack {', '.join(missing)}")
    return files, facts


def parse_sources(text):
    """The `source` lines alone: {name: {field: value}}, each source once;
    the other lines are --check's to judge, so that an unpinned build can
    fetch its inputs."""
    sources = {}
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("source "):
            name, fields = parse_source(number, line)
            if name in sources:
                raise Finding(f"pins line {number}: source {name} repeated")
            sources[name] = fields
    missing = [name for name in SOURCE_NAMES if name not in sources]
    if missing:
        raise Finding(f"pins lack source {', source '.join(missing)}")
    return sources


def source_lines(pins_text):
    """--sources: per source, in SOURCE_NAMES' order, its name and fields
    (as SOURCE_FIELDS orders them, with the tarball's and signature's file
    names after them), separated by spaces."""
    sources = parse_sources(pins_text)
    lines = []
    for name in SOURCE_NAMES:
        fields = sources[name]
        lines.append(" ".join([name] + [fields[key] for key in SOURCE_FIELDS] +
                              [fields["url"].rsplit("/", 1)[1],
                               fields["signature"].rsplit("/", 1)[1]]))
    return lines


def crc24(data):
    """The OpenPGP armor checksum (RFC 4880, 6.1)."""
    crc = CRC24_INIT
    for byte in data:
        crc ^= byte << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= CRC24_POLY
    return crc & 0xffffff


def dearmor(text):
    """An ASCII-armored public key block's packets, its CRC-24 checked."""
    lines = text.replace("\r\n", "\n").split("\n")
    if lines.count(ARMOR_BEGIN) != 1 or lines.count(ARMOR_END) != 1 or \
            lines.index(ARMOR_END) < lines.index(ARMOR_BEGIN):
        raise Finding("key: not one armored public key block")
    block = lines[lines.index(ARMOR_BEGIN) + 1:lines.index(ARMOR_END)]
    if "" not in block:
        raise Finding("key: no blank line after the armor headers")
    body = [line.strip() for line in block[block.index("") + 1:]]
    if len(body) < 2 or not body[-1].startswith("="):
        raise Finding("key: no armor checksum line")
    try:
        data = base64.b64decode("".join(body[:-1]), validate=True)
        checksum = base64.b64decode(body[-1][1:], validate=True)
    except ValueError as error:
        raise Finding(f"key: bad base64 ({error})") from None
    if len(checksum) != 3 or int.from_bytes(checksum, "big") != crc24(data):
        raise Finding("key: the armor checksum does not match")
    return data


def packets(data):
    """[(tag, body)] of an OpenPGP packet sequence; partial and
    indeterminate lengths, which no key uses, are refused."""
    found, position = [], 0
    while position < len(data):
        ctb = data[position]
        if not ctb & 0x80:
            raise Finding(f"key: byte {position} is not a packet header")
        if ctb & 0x40:
            tag = ctb & 0x3f
            first = data[position + 1] if position + 1 < len(data) else None
            if first is None:
                raise Finding("key: a truncated packet header")
            if first < 192:
                length, header = first, 2
            elif first < 224 and position + 2 < len(data):
                length = ((first - 192) << 8) + data[position + 2] + 192
                header = 3
            elif first == 255 and position + 6 <= len(data):
                length = int.from_bytes(data[position + 2:position + 6], "big")
                header = 6
            else:
                raise Finding("key: a partial or truncated packet length")
        else:
            tag, kind = (ctb >> 2) & 0xf, ctb & 3
            if kind == 3:
                raise Finding("key: an indeterminate packet length")
            header = 1 + (1, 2, 4)[kind]
            if position + header > len(data):
                raise Finding("key: a truncated packet header")
            length = int.from_bytes(data[position + 1:position + header],
                                    "big")
        end = position + header + length
        if end > len(data):
            raise Finding("key: a packet runs past the end")
        found.append((tag, data[position + header:end]))
        position = end
    return found


def key_fingerprint(data):
    """The fingerprint of a key's one primary key packet, which must be a
    version 4 key (RFC 4880, 12.2), upper-case hex."""
    primary = [body for tag, body in packets(data) if tag == TAG_PUBLIC_KEY]
    if len(primary) != 1:
        raise Finding(f"key: {len(primary)} primary keys, not 1")
    body = primary[0]
    if not body or body[0] != 4 or len(body) > 0xffff:
        raise Finding("key: the primary key is not a version 4 key")
    return hashlib.sha1(b"\x99" + len(body).to_bytes(2, "big") +
                        body).hexdigest().upper()


def keyring(text, fingerprint):
    """The binary keyring of an armored key whose primary key is
    FINGERPRINT."""
    data = dearmor(text)
    found = key_fingerprint(data)
    if found != fingerprint:
        raise Finding(f"key: primary key {found}, not the pinned "
                      f"{fingerprint}")
    return data


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_init(data, what="init"):
    if len(data) < ELF_HEADER.size or data[:4] != b"\x7fELF":
        raise Finding(f"{what}: not an ELF file")
    (ident, e_type, machine, _version, entry, phoff, _shoff, flags, _ehsize,
     phentsize, phnum, _shentsize, _shnum, _shstrndx) = \
        ELF_HEADER.unpack_from(data, 0)
    if ident[4] != 2 or ident[5] != 1:
        raise Finding(f"{what}: not ELF64 little-endian")
    if e_type != 2 or machine != EM_RISCV:
        raise Finding(f"{what}: not a RISC-V executable (ET_EXEC)")
    if flags & 0x6:
        raise Finding(f"{what}: not the soft-float ABI (lp64)")
    if phentsize != ELF_PHDR.size or phoff + phnum * phentsize > len(data):
        raise Finding(f"{what}: bad program headers")
    executable = False
    for index in range(phnum):
        p_type, p_flags, _offset, vaddr, _paddr, _filesz, memsz, _align = \
            ELF_PHDR.unpack_from(data, phoff + index * phentsize)
        if p_type in (PT_INTERP, PT_DYNAMIC):
            raise Finding(f"{what}: not static (PT_INTERP or PT_DYNAMIC)")
        if p_type == PT_LOAD and p_flags & 1 and vaddr <= entry < vaddr + memsz:
            executable = True
    if not executable:
        raise Finding(f"{what}: the entry is not in an executable segment")
    arch = init_arch(data, what)
    parts = arch.split("_")
    base = re.fullmatch(r"(rv64i)[0-9]+p[0-9]+", parts[0])
    names = [re.fullmatch(r"([a-z]+?)[0-9]+p[0-9]+", part) for part in parts[1:]]
    if (base is None or base.group(1) != INIT_ARCH_BASE or None in names or
            not {name.group(1) for name in names} <= INIT_ARCH_EXTENSIONS):
        raise Finding(f"{what}: arch {arch!r} is not rv64imac_zicsr (no F, D, "
                      "or V)")


def uleb128(data, position, limit, what="init"):
    value = shift = 0
    while True:
        if position >= limit:
            raise Finding(f"{what}: truncated ULEB128 attribute")
        byte = data[position]
        position += 1
        value |= (byte & 0x7f) << shift
        shift += 7
        if not byte & 0x80:
            return value, position


def init_arch(data, what="init"):
    """The Tag_RISCV_arch string of WHAT's .riscv.attributes section."""
    (_ident, _type, _machine, _version, _entry, _phoff, shoff, _flags,
     _ehsize, _phentsize, _phnum, shentsize, shnum, shstrndx) = \
        ELF_HEADER.unpack_from(data, 0)
    if (shentsize != ELF_SHDR.size or shstrndx >= shnum or
            shoff + shnum * shentsize > len(data)):
        raise Finding(f"{what}: bad section headers")
    sections = [ELF_SHDR.unpack_from(data, shoff + index * shentsize)
                for index in range(shnum)]
    names_offset, names_size = sections[shstrndx][4:6]
    if names_offset + names_size > len(data):
        raise Finding(f"{what}: bad section name table")
    found = []
    for name, _type, _flags, _addr, offset, size, *_rest in sections:
        end = data.find(b"\0", names_offset + name, names_offset + names_size)
        if end >= 0 and data[names_offset + name:end] == b".riscv.attributes":
            if offset + size > len(data):
                raise Finding(f"{what}: .riscv.attributes out of bounds")
            found.append(data[offset:offset + size])
    if len(found) != 1:
        raise Finding(f"{what}: {len(found)} .riscv.attributes sections, not 1")
    section = found[0]
    if not section or section[0] != ord("A"):
        raise Finding(f"{what}: .riscv.attributes is not format A")
    arches, position = [], 1
    while position < len(section):
        if position + 4 > len(section):
            raise Finding(f"{what}: truncated attribute subsection")
        end = position + struct.unpack_from("<I", section, position)[0]
        vendor_end = section.find(b"\0", position + 4, end)
        if end <= position + 4 or end > len(section) or vendor_end < 0:
            raise Finding(f"{what}: bad attribute subsection")
        sub = vendor_end + 1
        while section[position + 4:vendor_end] == b"riscv" and sub < end:
            if sub + 5 > end:
                raise Finding(f"{what}: truncated attribute block")
            tag = section[sub]
            sub_end = sub + struct.unpack_from("<I", section, sub + 1)[0]
            if sub_end <= sub + 5 or sub_end > end:
                raise Finding(f"{what}: bad attribute block")
            cursor = sub + 5
            while tag == TAG_FILE and cursor < sub_end:
                attribute, cursor = uleb128(section, cursor, sub_end, what)
                if attribute % 2:
                    string_end = section.find(b"\0", cursor, sub_end)
                    if string_end < 0:
                        raise Finding(f"{what}: unterminated attribute string")
                    if attribute == TAG_RISCV_ARCH:
                        arches.append(section[cursor:string_end].decode(
                            "ascii", errors="replace"))
                    cursor = string_end + 1
                else:
                    _, cursor = uleb128(section, cursor, sub_end, what)
            sub = sub_end
        position = end
    if len(arches) != 1:
        raise Finding(f"{what}: {len(arches)} Tag_RISCV_arch attributes, not 1")
    return arches[0]


def elf_sections(data, what):
    """An ELF64 file's sections: [(name, offset, size)]."""
    (_ident, _type, _machine, _version, _entry, _phoff, shoff, _flags,
     _ehsize, _phentsize, _phnum, shentsize, shnum, shstrndx) = \
        ELF_HEADER.unpack_from(data, 0)
    if (shentsize != ELF_SHDR.size or shstrndx >= shnum or
            shoff + shnum * shentsize > len(data)):
        raise Finding(f"{what}: bad section headers")
    headers = [ELF_SHDR.unpack_from(data, shoff + index * shentsize)
               for index in range(shnum)]
    names_offset, names_size = headers[shstrndx][4:6]
    if names_offset + names_size > len(data):
        raise Finding(f"{what}: bad section name table")
    sections = []
    for name, kind, _flags, _addr, offset, size, *_rest in headers:
        end = data.find(b"\0", names_offset + name, names_offset + names_size)
        if end < 0 or (kind != SHT_NOBITS and offset + size > len(data)):
            raise Finding(f"{what}: a section is out of bounds")
        sections.append((data[names_offset + name:end].decode(
            "ascii", errors="replace"), offset, size))
    return sections


def check_module(data, release):
    """The management module's facts, against the kernel's RELEASE."""
    if len(data) < ELF_HEADER.size or data[:4] != b"\x7fELF":
        raise Finding(f"{MODULE}: not an ELF file")
    (ident, e_type, machine, _version, _entry, _phoff, _shoff, flags,
     *_rest) = ELF_HEADER.unpack_from(data, 0)
    if ident[4] != 2 or ident[5] != 1:
        raise Finding(f"{MODULE}: not ELF64 little-endian")
    if e_type != ET_REL or machine != EM_RISCV:
        raise Finding(f"{MODULE}: not a RISC-V relocatable object (ET_REL)")
    if flags & 0x6:
        raise Finding(f"{MODULE}: not the soft-float ABI (lp64)")
    if data.endswith(MODULE_SIGNATURE):
        raise Finding(f"{MODULE}: signed, though MODULE_SIG is off")
    sections = elf_sections(data, MODULE)
    names = [name for name, _offset, _size in sections]
    for name in (".modinfo", ".gnu.linkonce.this_module"):
        if names.count(name) != 1:
            raise Finding(f"{MODULE}: {names.count(name)} {name} sections, "
                          "not 1")
    if "__versions" in names:
        raise Finding(f"{MODULE}: a __versions section, though MODVERSIONS "
                      "is off")
    _name, offset, size = sections[names.index(".modinfo")]
    info = {}
    for entry in data[offset:offset + size].split(b"\0"):
        if not entry:
            continue
        key, equals, value = entry.decode("ascii", errors="replace") \
            .partition("=")
        if not equals or key in info:
            raise Finding(f"{MODULE}: .modinfo entry {entry!r} is malformed "
                          "or repeated")
        info[key] = value
    if set(info) != MODULE_INFO_KEYS or \
            any(info[key] != value for key, value in MODULE_INFO.items()) or \
            not info["author"] or not info["description"]:
        raise Finding(f"{MODULE}: .modinfo {sorted(info.items())} is not "
                      "the module's")
    words = info["vermagic"].split()
    if not words or words[0] != release or \
            {"mod_unload", "modversions"} & set(words):
        raise Finding(f"{MODULE}: vermagic {info['vermagic']!r} is not "
                      f"release {release} without mod_unload or modversions")


def check_archive(data, what=MUSL_LIBC):
    """musl's libc.a: an ar archive, deterministic (every member header's
    mtime, uid, and gid 0), whose ELF members are all RV64 soft-float
    relocatable objects; the number of members."""
    if not data.startswith(AR_MAGIC):
        raise Finding(f"{what}: not an ar archive")
    position, members = len(AR_MAGIC), 0
    while position < len(data):
        header = data[position:position + AR_HEADER_BYTES]
        if len(header) != AR_HEADER_BYTES or header[58:] != b"`\n":
            raise Finding(f"{what}: bad member header at byte {position}")
        name = header[:16].rstrip(b" ")
        # GNU ar leaves the long-name table's fields but its size blank.
        try:
            mtime, uid, gid, size = (int(field.strip() or b"0") for field in (
                header[16:28], header[28:34], header[34:40], header[48:58]))
        except ValueError:
            raise Finding(f"{what}: bad member header at byte "
                          f"{position}") from None
        if (mtime, uid, gid) != (0, 0, 0):
            raise Finding(f"{what}: member {name!r} has mtime, uid, or gid "
                          "other than 0 (not ar's deterministic mode)")
        body = data[position + AR_HEADER_BYTES:
                    position + AR_HEADER_BYTES + size]
        if len(body) != size:
            raise Finding(f"{what}: member {name!r} runs past the end")
        if name not in (b"/", b"//"):
            if len(body) < ELF_HEADER.size or body[:4] != b"\x7fELF":
                raise Finding(f"{what}: member {name!r} is not an ELF file")
            (ident, e_type, machine, _version, _entry, _phoff, _shoff, flags,
             *_rest) = ELF_HEADER.unpack_from(body, 0)
            if ident[4] != 2 or ident[5] != 1 or e_type != ET_REL or \
                    machine != EM_RISCV or flags & 0x6:
                raise Finding(f"{what}: member {name!r} is not an RV64 "
                              "soft-float relocatable object")
            members += 1
        position += AR_HEADER_BYTES + size + (size & 1)
    if members == 0:
        raise Finding(f"{what}: no object member")
    return members


def kernel_facts(data, layout):
    """Check the Image header and budgets; return (image_size, offset, banner)."""
    if len(data) < 64:
        raise Finding("Image: shorter than its 64-byte header")
    (_code0, _code1, text_offset, image_size, flags, version, _res1, _res2,
     magic, magic2, _res3) = struct.unpack_from("<IIQQQIIQ8s4sI", data, 0)
    if magic != IMAGE_MAGIC or magic2 != IMAGE_MAGIC2:
        raise Finding("Image: bad magic or magic2")
    if flags & 1:
        raise Finding("Image: not little-endian")
    if version != IMAGE_VERSION:
        raise Finding(f"Image: header version {version:#x}, not 0.2")
    if text_offset != layout["KERNEL_TEXT_OFFSET"]:
        raise Finding(f"Image: text_offset {text_offset:#x}, not "
                      f"{layout['KERNEL_TEXT_OFFSET']:#x}")
    if len(data) > IMAGE_BUDGET:
        raise Finding(f"Image: {len(data)} bytes, over the {IMAGE_BUDGET:#x}"
                      "-byte Image budget (planning/mvp-m7-plan.md, Q13; "
                      "stop condition 8)")
    if len(data) > layout["KERNEL_FILE_MAX"]:
        raise Finding(f"Image: {len(data)} bytes, over the "
                      f"{layout['KERNEL_FILE_MAX']:#x}-byte budget")
    if not len(data) <= image_size <= layout["KERNEL_IMAGE_SIZE_MAX"]:
        raise Finding(f"Image: image_size {image_size:#x} is below the file "
                      f"or over {layout['KERNEL_IMAGE_SIZE_MAX']:#x}")
    if layout["KERNEL_GPA"] + image_size > layout["DTB_GPA"]:
        raise Finding("Image: image_size reaches the DTB slot")
    if data.count(BANNER) != 1:
        raise Finding(f"Image: {data.count(BANNER)} '{BANNER.decode()}' strings")
    start = data.index(BANNER)
    end = data.find(b"\n", start)
    banner = data[start:end]
    if end < 0 or not all(0x20 <= byte <= 0x7e for byte in banner):
        raise Finding("Image: the banner is not one printable line")
    return image_size, text_offset, banner.decode("ascii")


def fdt_tree(data, size):
    """Decode a flattened device tree into {path: {property: value}}."""
    if len(data) < 40:
        raise Finding("shorter than an FDT header")
    (magic, total, off_struct, off_strings, off_rsv, version, last_comp,
     boot_cpu, size_strings, size_struct) = struct.unpack_from(">10I", data, 0)
    if magic != FDT_MAGIC or version != 17 or last_comp != 16 or boot_cpu:
        raise Finding("bad FDT magic, version, or boot CPU")
    if len(data) != size or total != size:
        raise Finding(f"{len(data)} bytes, totalsize {total}, not {size}")
    if (off_rsv < 40 or off_rsv % 8 or off_struct % 4 or
            off_rsv + 16 > total or off_struct + size_struct > total or
            off_strings + size_strings > total):
        raise Finding("FDT blocks out of bounds")
    if data[off_rsv:off_rsv + 16] != bytes(16):
        raise Finding("the FDT reservation map is not empty")

    def cstring(offset, limit):
        end = data.find(b"\0", offset, limit)
        if end < 0:
            raise Finding("unterminated FDT string")
        return data[offset:end].decode("ascii"), end + 1

    nodes, path = {}, []
    position, limit = off_struct, off_struct + size_struct
    while True:
        if position + 4 > limit:
            raise Finding("FDT structure overruns its block")
        token = struct.unpack_from(">I", data, position)[0]
        position += 4
        if token == FDT_BEGIN_NODE:
            name, position = cstring(position, limit)
            position = (position + 3) & ~3
            path.append(name)
            key = "/" + "/".join(path[1:])
            if key in nodes:
                raise Finding(f"FDT node {key} repeated")
            nodes[key] = {}
        elif token == FDT_PROP:
            length, name_offset = struct.unpack_from(">II", data, position)
            value = data[position + 8:position + 8 + length]
            position = (position + 8 + length + 3) & ~3
            name, _ = cstring(off_strings + name_offset,
                              off_strings + size_strings)
            if not path or name in nodes["/" + "/".join(path[1:])]:
                raise Finding(f"FDT property {name} misplaced or repeated")
            nodes["/" + "/".join(path[1:])][name] = value
        elif token == FDT_END_NODE:
            if not path:
                raise Finding("unbalanced FDT end of node")
            path.pop()
        elif token == FDT_END:
            break
        elif token != FDT_NOP:
            raise Finding(f"bad FDT token {token:#x}")
    if path:
        raise Finding("unterminated FDT node")
    return nodes


def expected_tree(layout, guest, variant):
    """The decoded tree tools/gen-dts.py renders for one guest's variant."""
    values = GEN_DTS.values(layout, guest, variant)
    reg = [int(cell, 16) for cell in values["MEMORY_REG"].split()]
    isa = re.findall(r'"([^"]*)"', values["ISA_EXTENSIONS"])
    return {
        "/": {"#address-cells": struct.pack(">I", 2),
              "#size-cells": struct.pack(">I", 2),
              "compatible": GEN_DTS.COMPATIBLE.encode() + b"\0",
              "model": GEN_DTS.MODEL.encode() + b"\0"},
        "/chosen": {"bootargs": values["BOOTARGS"].encode() + b"\0"},
        "/cpus": {"#address-cells": struct.pack(">I", 1),
                  "#size-cells": struct.pack(">I", 0),
                  "timebase-frequency": struct.pack(
                      ">I", int(values["TIMEBASE_HZ"]))},
        "/cpus/cpu@0": {"device_type": b"cpu\0",
                        "reg": struct.pack(">I", 0),
                        "compatible": b"riscv\0",
                        "mmu-type": b"riscv,sv39\0",
                        "riscv,isa-base": b"rv64i\0",
                        "riscv,isa-extensions":
                            b"".join(name.encode() + b"\0" for name in isa)},
        "/cpus/cpu@0/interrupt-controller": {
            "compatible": b"riscv,cpu-intc\0",
            "interrupt-controller": b"",
            "#interrupt-cells": struct.pack(">I", 1)},
        "/memory@" + values["MEMORY_UNIT"]: {
            "device_type": b"memory\0", "reg": struct.pack(">4I", *reg)},
    }


def check_dtb(name, data, layout, guest, variant):
    try:
        tree = fdt_tree(data, layout["DTB_BYTES"])
    except Finding as finding:
        raise Finding(f"{name}: {finding}") from None
    expected = expected_tree(layout, guest, variant)
    if tree != expected:
        nodes = sorted(set(tree) ^ set(expected))
        props = sorted(path for path in set(tree) & set(expected)
                       if tree[path] != expected[path])
        raise Finding(f"{name}: tree differs from G{guest}'s {variant} DTS "
                      f"(nodes {nodes}, properties in {props})")


def check_pair(first, second):
    """G0's and G1's DTBs differ in one byte: bootargs' guest digit."""
    differ = [index for index, (a, b) in enumerate(zip(first, second))
              if a != b]
    if (len(first) != len(second) or len(differ) != 1 or
            first[differ[0]] != ord("0") or second[differ[0]] != ord("1") or
            first[differ[0] - len(GEN_DTS.GUEST_ARG):differ[0]] !=
            GEN_DTS.GUEST_ARG.encode()):
        raise Finding(f"{PAIR[0]} and {PAIR[1]} differ in {len(differ)} "
                      "bytes, not only bootargs' guest digit")


def gcc_version(gcc):
    result = subprocess.run([gcc, "--version"], capture_output=True,
                            text=True, check=True)
    return result.stdout.splitlines()[0].strip()


def read_outputs(directory, names=FILES):
    outputs = {}
    for name in names:
        path = directory / name
        if not path.is_file():
            raise Finding(f"{path} is missing")
        outputs[name] = path.read_bytes()
    return outputs


def facts(outputs, layout):
    """Check every output's facts; return the kernel facts."""
    check_init(outputs["init"])
    check_init(outputs[BUSYBOX], BUSYBOX)
    check_archive(outputs[MUSL_LIBC])
    kernel = kernel_facts(outputs["Image"], layout)
    check_module(outputs[MODULE], kernel[2].split()[2])
    for name, (guest, variant) in DTB_FILES.items():
        check_dtb(name, outputs[name], layout, guest, variant)
    check_pair(outputs[PAIR[0]], outputs[PAIR[1]])
    return kernel


def pin_lines(outputs, kernel, gcc):
    image_size, text_offset, banner = kernel
    lines = [f"file {name} sha256={digest(outputs[name])} "
             f"bytes={len(outputs[name])}" for name in FILES]
    lines += [f"kernel image_size={image_size:#x}",
              f"kernel text_offset={text_offset:#x}",
              f"kernel banner={banner}",
              f"toolchain gcc={gcc}"]
    return lines


def check(pins_text, outputs, layout, gcc):
    files, pinned = parse_pins(pins_text)
    if gcc is not None and gcc != pinned["gcc"]:
        raise Finding(f"the pins hold for '{pinned['gcc']}', not '{gcc}'")
    kernel = facts(outputs, layout)
    match(pins_text, outputs, FILES)
    image_size, text_offset, banner = kernel
    if (f"{image_size:#x}", f"{text_offset:#x}", banner) != (
            pinned["image_size"], pinned["text_offset"], pinned["banner"]):
        raise Finding("the Image header or banner does not match its pins")
    return kernel


def check_no_ima(text):
    """The guest kernel's .config (D-5): no line sets an IMA or EVM symbol,
    CONFIG_IMA, CONFIG_IMA_*, CONFIG_EVM, or CONFIG_EVM_*, to any value.
    Returns the number of lines read."""
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        setting = re.fullmatch(r"\s*(CONFIG_[A-Za-z0-9_]+)\s*=.*", line)
        if setting and NEVER_SET.fullmatch(setting.group(1)):
            raise Finding(f".config line {number} sets {setting.group(1)}: "
                          f"IMA is never used (D-5)")
    return len(lines)


def match(pins_text, outputs, names):
    files, _ = parse_pins(pins_text)
    for name in names:
        data = outputs[name]
        if (digest(data), len(data)) != files[name]:
            raise Finding(f"{name} does not match its pin "
                          f"(sha256={digest(data)} bytes={len(data)})")


# ------------------------------------------------------------- self-test
def fdt_blob(tree, size):
    """Serialize {path: {property: value}} (parents first) as an FDT."""
    strings, offsets, body = bytearray(), {}, bytearray()

    def string_offset(name):
        if name not in offsets:
            offsets[name] = len(strings)
            strings.extend(name.encode() + b"\0")
        return offsets[name]

    def emit(path):
        name = path.rsplit("/", 1)[-1] if path != "/" else ""
        body.extend(struct.pack(">I", FDT_BEGIN_NODE) + name.encode() + b"\0")
        body.extend(bytes(-len(body) % 4))
        for prop, value in tree[path].items():
            body.extend(struct.pack(">III", FDT_PROP, len(value),
                                    string_offset(prop)) + value)
            body.extend(bytes(-len(body) % 4))
        prefix = path.rstrip("/") + "/"
        for child in tree:
            if child.startswith(prefix) and "/" not in child[len(prefix):] \
                    and child != path:
                emit(child)
        body.extend(struct.pack(">I", FDT_END_NODE))

    emit("/")
    body.extend(struct.pack(">I", FDT_END))
    off_rsv = 40
    off_struct = off_rsv + 16
    off_strings = off_struct + len(body)
    blob = bytearray(size)
    struct.pack_into(">10I", blob, 0, FDT_MAGIC, size, off_struct, off_strings,
                     off_rsv, 17, 16, 0, len(strings), len(body))
    blob[off_struct:off_struct + len(body)] = body
    blob[off_strings:off_strings + len(strings)] = strings
    return bytes(blob)


def fake_image(layout, banner=b"Linux version 7.2.0 (be@beryllium) (gcc) #1 X\n",
               **fields):
    values = dict(text_offset=layout["KERNEL_TEXT_OFFSET"], image_size=0x3000,
                  flags=0, version=IMAGE_VERSION, magic=IMAGE_MAGIC,
                  magic2=IMAGE_MAGIC2)
    values.update(fields)
    header = struct.pack("<IIQQQIIQ8s4sI", 0, 0, values["text_offset"],
                         values["image_size"], values["flags"],
                         values["version"], 0, 0, values["magic"],
                         values["magic2"], 0)
    return header + banner + bytes(0x2000 - len(header) - len(banner))


def attributes_section(arch):
    """A format-A .riscv.attributes section: stack_align 16, then arch."""
    attributes = b"\x04\x10\x05" + arch.encode() + b"\0"
    block = b"\x01" + struct.pack("<I", 5 + len(attributes)) + attributes
    return b"A" + struct.pack("<I", 10 + len(block)) + b"riscv\0" + block


def fake_init(interp=False, arch="rv64i2p1_m2p0_a2p1_c2p0_zicsr2p0_zca1p0",
              attributes=True):
    names = b"\0.riscv.attributes\0.shstrtab\0"
    attribute_bytes = attributes_section(arch)
    attribute_name = 1 if attributes else names.index(b".shstrtab")
    shoff = 64 + ELF_PHDR.size * 2 + 0x100 + len(attribute_bytes) + len(names)
    header = ELF_HEADER.pack(b"\x7fELF\x02\x01\x01" + bytes(9), 2, EM_RISCV, 1,
                             0x10078, 64, shoff, 0x1, 64, ELF_PHDR.size,
                             2 if interp else 1, ELF_SHDR.size, 3, 2)
    load = ELF_PHDR.pack(PT_LOAD, 5, 0, 0x10000, 0x10000, 0x100, 0x100, 0x1000)
    extra = ELF_PHDR.pack(PT_INTERP if interp else 0, 4, 0, 0, 0, 0, 0, 1)
    attribute_offset = 64 + ELF_PHDR.size * 2 + 0x100
    names_offset = attribute_offset + len(attribute_bytes)
    sections = (ELF_SHDR.pack(0, 0, 0, 0, 0, 0, 0, 0, 0, 0) +
                ELF_SHDR.pack(attribute_name, 0x70000003, 0, 0,
                              attribute_offset, len(attribute_bytes), 0, 0, 1,
                              0) +
                ELF_SHDR.pack(names.index(b".shstrtab"), 3, 0, 0, names_offset,
                              len(names), 0, 0, 1, 0))
    return (header + load + extra + bytes(0x100) + attribute_bytes + names +
            sections)


def fake_module(info=None, e_type=ET_REL, extra=(), signed=False):
    """A relocatable ELF with the module's .modinfo, its this_module
    section, and EXTRA (name, bytes) sections."""
    if info is None:
        info = dict(MODULE_INFO, author="A", description="D",
                    vermagic="7.2.0 preempt riscv")
    modinfo = b"".join(f"{key}={value}".encode() + b"\0"
                       for key, value in info.items())
    sections = [(".modinfo", modinfo), (".gnu.linkonce.this_module",
                                         bytes(64))] + list(extra)
    names = b"\0" + b"".join(name.encode() + b"\0" for name, _ in sections) \
        + b".shstrtab\0"
    body, offsets = bytearray(), []
    for _name, data in sections:
        offsets.append(ELF_HEADER.size + len(body))
        body.extend(data)
    names_offset = ELF_HEADER.size + len(body)
    body.extend(names)
    count = len(sections) + 2
    header = ELF_HEADER.pack(b"\x7fELF\x02\x01\x01" + bytes(9), e_type,
                             EM_RISCV, 1, 0, 0, ELF_HEADER.size + len(body),
                             0x1, ELF_HEADER.size, 0, 0, ELF_SHDR.size, count,
                             count - 1)
    headers, name_at = bytearray(ELF_SHDR.size), 1
    for (name, data), offset in zip(sections, offsets):
        headers.extend(ELF_SHDR.pack(name_at, 1, 0, 0, offset, len(data), 0,
                                     0, 1, 0))
        name_at += len(name) + 1
    headers.extend(ELF_SHDR.pack(name_at, 3, 0, 0, names_offset, len(names),
                                 0, 0, 1, 0))
    module = bytes(header + body + headers)
    return module + MODULE_SIGNATURE if signed else module


def fake_archive(mtime=0, member=None):
    """A GNU ar archive: a symbol table, a long-name table (whose fields
    but its size are blank), and one member, by default an RV64 soft-float
    relocatable object (fake_module's), with MTIME."""
    member = fake_module() if member is None else member

    def entry(name, body, stamp):
        header = (name.ljust(16) + str(stamp).ljust(12) + "0".ljust(6) +
                  "0".ljust(6) + "644".ljust(8) + str(len(body)).ljust(10) +
                  "`\n").encode()
        return header + body + (b"\n" if len(body) % 2 else b"")

    names = b"a-long-member-name.o/\n"
    long_names = ("//".ljust(48) + str(len(names)).ljust(10) +
                  "`\n").encode() + names
    return AR_MAGIC + entry("/", bytes(8), 0) + long_names + \
        entry("/0", member, mtime)


def fake_key(primaries=1, old_format=False, checksum_ok=True):
    """An armored public key block, a version 4 primary key (arbitrary key
    material) PRIMARIES times and a user ID, and the key's fingerprint."""
    body = b"\x04" + struct.pack(">I", 1) + b"\x01\x00\x08\xff\x00\x02\x03"
    ctb = 0x80 | TAG_PUBLIC_KEY << 2 if old_format else 0xc0 | TAG_PUBLIC_KEY
    data = (bytes([ctb, len(body)]) + body) * primaries + b"\xcd\x04test"
    fingerprint = hashlib.sha1(b"\x99" + len(body).to_bytes(2, "big") +
                               body).hexdigest().upper()
    checksum = crc24(data) ^ (0 if checksum_ok else 1)
    text = "\n".join([ARMOR_BEGIN, "Version: self-test", "",
                      base64.b64encode(data).decode(),
                      "=" + base64.b64encode(checksum.to_bytes(3, "big"))
                      .decode(), ARMOR_END, ""])
    return text, fingerprint, data


def fake_sources():
    """Two well-formed source lines, in SOURCE_FIELDS' order."""
    return [f"source {name} version=1.2.3 tag=v1.2.3 commit={'a' * 40} "
            f"url=https://example.org/{name}-1.2.3.tar.gz sha256={'b' * 64} "
            f"signature=https://example.org/{name}-1.2.3.tar.gz.asc "
            f"key=guest/keys/{name}.asc fingerprint={'C' * 40} license=MIT"
            for name in SOURCE_NAMES]


def fake_outputs(layout):
    outputs = {"Image": fake_image(layout), "init": fake_init(),
               MODULE: fake_module(), BUSYBOX: fake_init(),
               MUSL_LIBC: fake_archive()}
    for name, (guest, variant) in DTB_FILES.items():
        outputs[name] = fdt_blob(expected_tree(layout, guest, variant),
                                 layout["DTB_BYTES"])
    return outputs


def self_test(layout_text):
    layout = parse_layout(layout_text)
    failures, cases = [], 0

    def expect_ok(name, action):
        nonlocal cases
        cases += 1
        try:
            action()
        except Finding as finding:
            failures.append(f"{name}: unexpected finding: {finding}")

    def expect_finding(name, action, text):
        nonlocal cases
        cases += 1
        try:
            action()
        except Finding as finding:
            if text not in str(finding):
                failures.append(f"{name}: finding '{finding}' lacks '{text}'")
        else:
            failures.append(f"{name}: no finding")

    good = fake_outputs(layout)
    kernel = facts(good, layout)
    lines = pin_lines(good, kernel, "gcc 1")
    sources = fake_sources()
    pins = "\n".join(["# self-test"] + lines + sources)
    expect_ok("pass", lambda: check(pins, good, layout, "gcc 1"))
    expect_ok("match", lambda: match(pins, good, ["Image", "init"]))
    expect_finding("toolchain", lambda: check(pins, good, layout, "gcc 2"),
                   "pins hold for")
    pin_cases = [
        ("missing file", "\n".join(lines[1:] + sources), "lack init"),
        ("malformed", pins + "\nfile init sha256=00 bytes=1", "not a pin"),
        ("repeated", pins + "\n" + lines[-1], "repeated"),
        ("unknown file", pins + "\nfile x sha256=" + "0" * 64 + " bytes=1",
         "unexpected file"),
        ("missing source", "\n".join(lines + sources[:1]),
         "lack source musl"),
        ("repeated source", pins + "\n" + sources[0], "source busybox "
         "repeated"),
        ("unknown source", pins + "\n" + sources[0].replace(
            "source busybox", "source toybox"), "not a source pin"),
        ("source over HTTP", pins.replace("url=https://example.org/busybox",
                                          "url=http://example.org/busybox"),
         "url 'http://example.org/busybox-1.2.3.tar.gz' is malformed"),
        ("source fields reordered", pins.replace(
            "version=1.2.3 tag=v1.2.3", "tag=v1.2.3 version=1.2.3"),
         "in that order"),
        ("source short digest", pins.replace("sha256=" + "b" * 64,
                                             "sha256=" + "b" * 63, 1),
         "sha256"),
        ("source tarball of another version", pins.replace(
            "musl-1.2.3.tar.gz sha256", "musl-1.2.4.tar.gz sha256"),
         "not its version's"),
        ("source signature of another file", pins.replace(
            "busybox-1.2.3.tar.gz.asc", "busybox-1.2.4.tar.gz.asc"),
         "not its version's"),
    ]
    for name, text, finding in pin_cases:
        expect_finding(f"pins {name}", lambda t=text: parse_pins(t), finding)
    expected_sources = [
        f"{name} 1.2.3 v1.2.3 {'a' * 40} https://example.org/{name}-1.2.3"
        f".tar.gz {'b' * 64} https://example.org/{name}-1.2.3.tar.gz.asc "
        f"guest/keys/{name}.asc {'C' * 40} MIT {name}-1.2.3.tar.gz "
        f"{name}-1.2.3.tar.gz.asc" for name in SOURCE_NAMES]
    # The sources alone, as an unpinned build reads them, and with the pins.
    for text in ("\n".join(sources), pins):
        cases += 1
        if source_lines(text) != expected_sources:
            failures.append(f"sources: {source_lines(text)}")
    expect_finding("sources without musl",
                   lambda: source_lines("\n".join(lines + sources[:1])),
                   "lack source musl")
    text, fingerprint, data = fake_key()
    cases += 1
    if keyring(text, fingerprint) != data:
        failures.append("keyring: the packets differ from the key's")
    old, old_fingerprint, _ = fake_key(old_format=True)
    expect_ok("keyring, old-format packets",
              lambda: keyring(old, old_fingerprint))
    expect_ok("keyring, CRLF", lambda: keyring(text.replace("\n", "\r\n"),
                                               fingerprint))
    two, two_fingerprint, _ = fake_key(primaries=2)
    for name, action, finding in (
            ("another fingerprint", lambda: keyring(text, "D" * 40),
             "not the pinned"),
            ("a bad checksum", lambda: keyring(
                fake_key(checksum_ok=False)[0], fingerprint), "checksum"),
            ("two primary keys", lambda: keyring(two, two_fingerprint),
             "2 primary keys"),
            ("no armor", lambda: keyring(text.replace("PUBLIC KEY", "X"),
                                         fingerprint), "not one armored"),
            ("a truncated packet", lambda: key_fingerprint(data[:-1]),
             "runs past the end")):
        expect_finding(f"keyring {name}", action, finding)
    expect_finding("busybox interpreter",
                   lambda: check_init(fake_init(interp=True), BUSYBOX),
                   "busybox: not static")
    expect_finding("busybox lp64d",
                   lambda: check_init(fake_init(arch="rv64i2p1_m2p0_a2p1_"
                                                "f2p2_d2p2_c2p0"), BUSYBOX),
                   "busybox: arch")
    lp64d = bytearray(fake_module())
    struct.pack_into("<I", lp64d, 48, 0x5)
    for name, data, finding in (
            ("a member's mtime", fake_archive(mtime=1), "deterministic"),
            ("a member not ELF", fake_archive(member=b"x" * 64),
             "not an ELF"),
            ("an lp64d member", fake_archive(member=bytes(lp64d)),
             "soft-float"),
            ("not an archive", b"x" * 64, "not an ar archive"),
            ("no member", AR_MAGIC, "no object member")):
        expect_finding(f"{MUSL_LIBC} {name}",
                       lambda d=data: check_archive(d), finding)
    expect_finding("Image over the M7 budget",
                   lambda: kernel_facts(fake_image(layout) +
                                        bytes(IMAGE_BUDGET), layout), "Q13")
    expect_finding("banner pin",
                   lambda: check(pins.replace("#1 X", "#1 Y"), good, layout,
                                 "gcc 1"), "banner")
    image_cases = [
        ("magic2", dict(magic2=b"RSC\x06"), "magic"),
        ("big-endian", dict(flags=1), "little-endian"),
        ("header version", dict(version=1), "not 0.2"),
        ("text_offset", dict(text_offset=0), "text_offset"),
        ("image_size below file", dict(image_size=0x100), "image_size"),
        ("image_size over budget",
         dict(image_size=layout["KERNEL_IMAGE_SIZE_MAX"] + 1), "image_size"),
        ("two banners", dict(banner=b"Linux version a\nLinux version b\n"),
         "2 'Linux version"),
        ("unterminated banner", dict(banner=b"Linux version \x01\n"),
         "printable"),
    ]
    for name, fields, finding in image_cases:
        data = fake_image(layout, **fields)
        expect_finding(f"Image {name}", lambda d=data: kernel_facts(d, layout),
                       finding)
    big = fake_image(layout) + bytes(layout["KERNEL_FILE_MAX"])
    expect_finding("Image file over budget", lambda: kernel_facts(big, layout),
                   "budget")
    flipped = dict(good)
    flipped["Image"] = bytes([good["Image"][0] ^ 1]) + good["Image"][1:]
    expect_finding("Image byte flip", lambda: match(pins, flipped, ["Image"]),
                   "Image does not match")
    flipped = dict(good)
    flipped["mvp-guest-g0-reference.dtb"] = good["mvp-guest-g0.dtb"]
    expect_finding("DTB swap", lambda: check(pins, flipped, layout, "gcc 1"),
                   "mvp-guest-g0-reference.dtb: tree differs")
    flipped = dict(good)
    flipped["mvp-guest-g1.dtb"] = good["mvp-guest-g0.dtb"]
    expect_finding("guest swap", lambda: check(pins, flipped, layout, "gcc 1"),
                   "mvp-guest-g1.dtb: tree differs from G1's")
    g0, g1 = good[PAIR[0]], good[PAIR[1]]
    expect_ok("pair", lambda: check_pair(g0, g1))
    digit = g0.index(GEN_DTS.GUEST_ARG.encode()) + len(GEN_DTS.GUEST_ARG)
    for name, first, second in (
            ("equal", g0, g0), ("reversed", g1, g0),
            ("extra byte", g0, g1[:-1] + b"\1"),
            ("other digit", g0, g1[:digit] + b"2" + g1[digit + 1:]),
            ("shorter", g0, g1[:-8])):
        expect_finding(f"pair {name}", lambda f=first, s=second:
                       check_pair(f, s), "not only bootargs' guest digit")
    expect_finding("init interpreter",
                   lambda: check_init(fake_init(interp=True)), "static")
    expect_finding("init not ELF", lambda: check_init(bytes(64)), "not an ELF")
    for name, arch in (("F", "rv64i2p1_m2p0_a2p1_f2p2_c2p0_zicsr2p0"),
                       ("D", "rv64i2p1_m2p0_a2p1_f2p2_d2p2_c2p0"),
                       ("V", "rv64i2p1_m2p0_a2p1_c2p0_v1p0"),
                       ("Zve32x", "rv64i2p1_m2p0_a2p1_c2p0_zve32x1p0"),
                       ("Zfinx", "rv64i2p1_m2p0_a2p1_c2p0_zfinx1p0"),
                       ("rv32", "rv32i2p1_m2p0_a2p1_c2p0"),
                       ("RVE", "rv64e2p0_m2p0_a2p1_c2p0"),
                       ("malformed", "rv64i2p1_m")):
        expect_finding(f"init arch {name}",
                       lambda a=arch: check_init(fake_init(arch=a)),
                       "is not rv64imac_zicsr")
    expect_ok("init arch rv64imac", lambda: check_init(fake_init(
        arch="rv64i2p1_m2p0_a2p1_c2p0")))
    expect_finding("init without attributes",
                   lambda: check_init(fake_init(attributes=False)),
                   "0 .riscv.attributes sections")
    expect_ok("module", lambda: check_module(fake_module(), "7.2.0"))
    good_info = dict(MODULE_INFO, author="A", description="D",
                     vermagic="7.2.0 preempt riscv")
    module_cases = [
        ("executable", fake_module(e_type=2), "ET_REL"),
        ("signed", fake_module(signed=True), "signed"),
        ("modversions", fake_module(extra=[("__versions", bytes(64))]),
         "__versions"),
        ("two .modinfo", fake_module(extra=[(".modinfo", b"name=x\0")]),
         "2 .modinfo sections"),
        ("license", fake_module(dict(good_info, license="GPL v2")),
         "is not the module's"),
        ("name", fake_module(dict(good_info, name="be-mgmt")),
         "is not the module's"),
        ("a dependency", fake_module(dict(good_info, depends="x")),
         "is not the module's"),
        ("no author", fake_module({key: value for key, value in
                                   good_info.items() if key != "author"}),
         "is not the module's"),
        ("an alias", fake_module(dict(good_info, alias="char-major-10-243")),
         "is not the module's"),
        ("mod_unload", fake_module(dict(
            good_info, vermagic="7.2.0 preempt mod_unload riscv")),
         "vermagic"),
        ("modversions vermagic", fake_module(dict(
            good_info, vermagic="7.2.0 preempt modversions riscv")),
         "vermagic"),
        ("release", fake_module(dict(good_info,
                                     vermagic="7.2.0+ preempt riscv")),
         "vermagic"),
        ("not ELF", bytes(64), "not an ELF"),
    ]
    for name, data, finding in module_cases:
        expect_finding(f"module {name}",
                       lambda d=data: check_module(d, "7.2.0"), finding)
    flipped = dict(good)
    flipped[MODULE] = good[MODULE][:-1] + bytes([good[MODULE][-1] ^ 1])
    expect_finding("module byte flip",
                   lambda: match(pins, flipped, [MODULE]),
                   f"{MODULE} does not match")
    base = expected_tree(layout, 0, "base")
    size = layout["DTB_BYTES"]
    bad_magic = bytearray(fdt_blob(base, size))
    bad_magic[0] ^= 1
    reserved = bytearray(fdt_blob(base, size))
    reserved[40 + 8] = 1
    b6_names = dict(base)
    b6_names["/"] = dict(base["/"], model=b"Beryllium K3 B6 guest\0")
    dtb_cases = [
        ("short", fdt_blob(base, size - 8), "bytes"),
        ("variant swap", fdt_blob(expected_tree(layout, 0, "sbi-time"), size),
         "differs"),
        ("guest swap", fdt_blob(expected_tree(layout, 1, "base"), size),
         "differs"),
        ("B6 model", fdt_blob(b6_names, size), "differs"),
        ("extra node", fdt_blob(dict(base, **{"/uart@10000000": {}}), size),
         "differs"),
        ("magic", bytes(bad_magic), "magic"),
        ("reservation", bytes(reserved), "reservation"),
    ]
    for name, data, finding in dtb_cases:
        expect_finding(f"DTB {name}",
                       lambda d=data: check_dtb("dtb", d, layout, 0, "base"),
                       finding)
    # D-5: a .config that sets no IMA or EVM symbol passes, names that only
    # begin like one among it; each planted setting is refused.
    config = ("CONFIG_DEVMEM=y\n# CONFIG_IMA is not set\n"
              "# CONFIG_EVM is not set\nCONFIG_IMAGE_BOOT=y\n"
              "CONFIG_IMAX=y\nCONFIG_EVMX=m\n")
    expect_ok("config without IMA", lambda: check_no_ima(config))
    for planted in ("CONFIG_IMA=y", "CONFIG_IMA_APPRAISE=y",
                    "CONFIG_IMA_MEASURE_PCR_IDX=10", "CONFIG_EVM=y",
                    "CONFIG_EVM_ATTR_FSUUID=y", "CONFIG_IMA=m"):
        expect_finding(f"config {planted}",
                       lambda p=planted: check_no_ima(config + p + "\n"),
                       f"sets {planted.split('=')[0]}: IMA is never used")
    for failure in failures:
        print(f"BE_MVP_GUEST_PINS_SELF_TEST: FAIL {failure}")
    status = "FAIL" if failures else "PASS"
    print(f"BE_MVP_GUEST_PINS_SELF_TEST: {status} cases={cases}")
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--print", action="store_true")
    mode.add_argument("--match", action="append", choices=FILES)
    mode.add_argument("--sources", action="store_true")
    mode.add_argument("--keyring", type=pathlib.Path)
    mode.add_argument("--self-test", action="store_true")
    parser.add_argument("--pins", type=pathlib.Path)
    parser.add_argument("--dir", type=pathlib.Path)
    parser.add_argument("--layout", type=pathlib.Path)
    parser.add_argument("--gcc")
    parser.add_argument("--fingerprint")
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    try:
        if args.match:
            if not args.pins or not args.dir:
                parser.error("--match needs --pins and --dir")
            match(args.pins.read_text(encoding="utf-8"),
                  read_outputs(args.dir, args.match), args.match)
            print(f"BE_MVP_GUEST_PINS: MATCH {' '.join(args.match)}")
            return 0
        if args.sources:
            if not args.pins:
                parser.error("--sources needs --pins")
            print("\n".join(source_lines(args.pins.read_text(
                encoding="utf-8"))))
            return 0
        if args.keyring:
            if not args.fingerprint or not args.output:
                parser.error("--keyring needs --fingerprint and --output")
            data = keyring(args.keyring.read_text(encoding="ascii"),
                           args.fingerprint)
            args.output.write_bytes(data)
            print(f"BE_MVP_GUEST_KEY: PASS fingerprint={args.fingerprint} "
                  f"packets={len(packets(data))} bytes={len(data)}")
            return 0
        if not args.layout:
            parser.error("--layout is required")
        layout = parse_layout(args.layout.read_text(encoding="ascii"))
        if args.self_test:
            return self_test(args.layout.read_text(encoding="ascii"))
        if not args.dir:
            parser.error("--dir is required")
        gcc = gcc_version(args.gcc) if args.gcc else None
        outputs = read_outputs(args.dir)
        if args.print:
            kernel = facts(outputs, layout)
            print("\n".join(pin_lines(outputs, kernel, gcc or "unknown")))
            return 0
        if not args.pins:
            parser.error("--check needs --pins")
        kernel = check(args.pins.read_text(encoding="utf-8"), outputs, layout,
                       gcc)
        config_lines = check_no_ima((args.dir / KERNEL_CONFIG).read_text(
            encoding="utf-8"))
    except Finding as finding:
        print(f"BE_MVP_GUEST_PINS: FAIL {finding}", file=sys.stderr)
        return 1
    except (GEN_DTS.LayoutError, ValueError, OSError,
            subprocess.CalledProcessError) as error:
        print(f"BE_MVP_GUEST_PINS: FAIL {error}", file=sys.stderr)
        return 1
    image_size, text_offset, banner = kernel
    print(f"BE_MVP_GUEST_PINS: PASS files={len(FILES)} "
          f"image_bytes={len(outputs['Image'])} "
          f"image_budget={IMAGE_BUDGET:#x} image_size={image_size:#x} "
          f"text_offset={text_offset:#x} init_bytes={len(outputs['init'])} "
          f"module_bytes={len(outputs[MODULE])} "
          f"busybox_bytes={len(outputs[BUSYBOX])} "
          f"musl_libc_bytes={len(outputs[MUSL_LIBC])} "
          f"dtb_bytes={layout['DTB_BYTES']}")
    print(f"BE_MVP_GUEST_PINS: banner={banner}")
    print(f"BE_MVP_GUEST_PINS: config={KERNEL_CONFIG} lines={config_lines} "
          f"ima=none evm=none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
