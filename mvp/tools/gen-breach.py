#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""The hostile-monitor attempts of the breach images (M11-7).

  gen-breach.py table --declaration FILE --layout H --header H --domain N
                [--discriminate] --out mvp-breach-table.h
  gen-breach.py plan --declaration FILE --layout H --header H --domain N
                [--discriminate] --image NAME --elf ELF --bin BIN
                --boot-img IMG --dtb0 DTB --dtb1 DTB --nm NM
                [--descriptor JSON] --out PLAN --words WORDS
  gen-breach.py counts --declaration FILE --domain N
  gen-breach.py --self-test --scratch DIR

Purpose: planning/mvp-m11-plan.md, D-10's VS-domain column, as anchor's
breach images run it. table writes, before the link, the C table the
hook (src/mvp-breach.c) runs: one row per attempt of the declaration
(scenarios/anchor/breach.json), VS domain 1's rows its own where it names
them, each row's access address made from its physical target by its
translation mode, and the five modes' satp, hgatp, and vsatp; under
--discriminate, the rows with a witness alone. plan writes, after the
link, what a run of the linked image must show (tests/check-boundary.py
breach): for each slot, its trap's cause and stval, the value it kept, and
the call's error; each witness word's value at the end; and the device
registers'; with the oracle's words file (tests/qemu_oracle.py --words).
For a boundary-on image (--descriptor) each row is checked against the
hooked hart's profile first: denied needs a right the profile lacks
(an access's own, or its translation's walk), allowed every right it
needs, refused a call the empty list refuses. counts gives the expected
commit-record counts.
Trust: a generator and a checker of its own declaration. It refuses a
row of unknown form, a target its mode cannot reach, two witnessed rows
whose written or read bytes meet (so each effect is one row's), a row in
the hook's own record or roots, and a declaration that does not fit the
record. The record's layout is read from src/mvp-breach.h.
Scope: anchor's breach-g0 and breach-g1 and their -off copies.
"""

import argparse
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True

SCHEMA = "be-mvp-breach-v1"
PLAN_SCHEMA = "be-mvp-breach-plan-v1"
WORDS_SCHEMA = "be-mvp-oracle-words-v1"
DEFINE = re.compile(r"^#define\s+BE_MVP_(\w+)\s+BE_MVP_C\((0x[0-9a-fA-F]+|"
                    r"[0-9]+)\)", re.M)
OPS = {"load": 1, "store": 2, "jump": 3, "amoadd": 4, "lrsc": 5,
       "cbo.zero": 6, "cbo.inval": 7, "hlv": 8, "hsv": 9, "ecall": 10}
MODES = {"bare": 0, "satp": 1, "gstage-own": 2, "gstage-other": 3,
         "vs-forged": 4}
OUTCOMES = ("denied", "illegal", "refused", "allowed")
COPIES = ("image", "boot-image", "dtb", "pages", "zero", "end", "device")
READS = ("load", "hlv")
WRITES = ("store", "amoadd", "lrsc", "cbo.zero", "hsv")
WIDTHS = (1, 4, 8)
ROW_KEYS = {"row", "target", "op", "width", "mode", "at", "value",
            "outcome", "witness", "call"}
CALL_KEYS = {"eid", "fid", "a0", "a1", "a2"}
DEVICE_KEYS = {"uart", "aplic-m", "aplic-s", "aplic-source", "imsic-m",
               "imsic-m-stride", "imsic-s", "imsic-s-stride", "test", "mtime",
               "mtimecmp", "m-memory", "unnamed-ram"}
AT = re.compile(r"(?P<name>[a-z][a-z0-9.-]*?)(?:\+(?P<offset>0x[0-9a-f]+))?")
HEX = re.compile(r"0x[0-9a-f]+")
NM_LINE = re.compile(r"([0-9a-f]+)(?: ([0-9a-f]+))? ([A-Za-z]) (\S+)")
MASK = (1 << 64) - 1
SATP_SV39 = 8 << 60
VMID_SHIFT = 44
CAUSES = {"load": 5, "hlv": 5, "jump": 1, "store": 7, "amoadd": 7,
          "lrsc": 7, "cbo.zero": 7, "hsv": 7}
ILLEGAL = 2
DENIED = (-4) & MASK
SECRET_SYMBOL = "be_mvp_secret"
ATTEMPT_HELPER = "be_mvp_breach_arch_attempt"
TABLE_SYMBOL = "be_mvp_breach_attempts"
MODES_SYMBOL = "be_mvp_breach_modes"
# The QEMU direct boot's staging: the boot image's first byte.
PAGE = 0x1000


class Refused(Exception):
    """A declaration or input the generator refuses."""


def require(condition, message):
    if not condition:
        raise Refused(message)


def defines(path):
    return {name: int(value, 0) for name, value in
            DEFINE.findall(pathlib.Path(path).read_text(encoding="utf-8"))}


def number(text, label):
    require(isinstance(text, str) and HEX.fullmatch(text),
            f"{label} {text!r} is not lowercase hexadecimal")
    return int(text, 16)


def pattern(row_number):
    """A written word's value: the row's number in each half."""
    return 0xb5ea << 48 | row_number << 32 | 0xb5ea << 16 | row_number


class Facts:
    """The layout's and the header's constants, the declaration's devices,
    and the hooked VS domain."""

    def __init__(self, layout, header, devices, domain):
        require(domain in (0, 1), f"VS domain {domain} is not 0 or 1")
        self.layout, self.header, self.domain = layout, header, domain
        own, other = domain, 1 - domain
        self.hart = layout[f"DOMAIN{own}_HART"]
        self.other_hart = layout[f"DOMAIN{other}_HART"]
        require(set(devices) == DEVICE_KEYS,
                f"the devices are {sorted(devices)}, not "
                f"{sorted(DEVICE_KEYS)}")
        device = {key: (value if key == "aplic-source" else
                        number(value, f"device {key}"))
                  for key, value in devices.items()}
        require(isinstance(device["aplic-source"], int) and
                1 <= device["aplic-source"] <= 96,
                "the APLIC source is not 1 to 96")
        dtb = layout["DTB_GPA"] - layout["GUEST_GPA"]
        names = {
            "park": layout["PARK_ENTRY_HPA"],
            "request": layout["SHARED_PAGES_HPA"],
            "response": layout["SHARED_PAGES_HPA"] + PAGE,
            "secret": layout["SHARED_PAGES_HPA"] + 2 * PAGE,
            "monitor.boot-text": layout["MONITOR_BOOT_TEXT_HPA"],
            "monitor.shared-text": layout["MONITOR_SHARED_TEXT_HPA"],
            "monitor.vs-text": layout["MONITOR_DOMAIN_TEXT_HPA"],
            "monitor.rodata": layout["MONITOR_RODATA_HPA"],
            "mvp.control-text": layout["MVP_CONTROL_TEXT_HPA"],
            "mvp.vs-text": layout["MVP_DOMAIN_TEXT_HPA"],
            "mvp.boot-text": layout["MVP_BOOT_TEXT_HPA"],
            "mvp.boot-rodata": layout["MVP_BOOT_RODATA_HPA"],
            "sealed": layout["MVP_SEALED_HPA"],
            "log": layout["MVP_LOG_HPA"],
            "region-tail": layout["MVP_LOG_HPA"] + layout["MVP_LOG_BYTES"],
            "staging": layout["STAGING_HPA"],
            "control.padding": layout["DIAGNOSTIC_HPA"] +
            layout["DIAGNOSTIC_BYTES"],
            "uart": device["uart"],
            "aplic-m": device["aplic-m"],
            "aplic-s": device["aplic-s"],
            "aplic-s.source": device["aplic-s"] + 4 * device["aplic-source"],
            "imsic-m.hart0": device["imsic-m"],
            "imsic-s.hart0": device["imsic-s"],
            "imsic-s.other": device["imsic-s"] +
            self.other_hart * device["imsic-s-stride"],
            "test": device["test"],
            "mtime": device["mtime"],
            "mtimecmp.hart0": device["mtimecmp"],
            "m-memory": device["m-memory"],
            "unnamed-ram": device["unnamed-ram"],
        }
        for side, index in (("own", own), ("other", other)):
            names.update({
                f"{side}.window": layout[f"G{index}_HPA"],
                f"{side}.dtb": layout[f"G{index}_HPA"] + dtb,
                f"{side}.pool": layout[f"G{index}_ROOT_HPA"],
                f"{side}.published": layout[f"G{index}_PUBLISHED_HPA"],
                f"{side}.control-mailbox":
                    layout[f"G{index}_CONTROL_MAILBOX_HPA"],
                f"{side}.hart-mailbox": layout[f"G{index}_HART_MAILBOX_HPA"],
                f"{side}.block": layout[f"G{index}_BLOCK_HPA"],
            })
        self.names = names
        self.devices = {device["uart"] + 7: 1,
                        names["aplic-s.source"]: 4}
        self.mailbox = layout[f"G{own}_HART_MAILBOX_HPA"]
        self.control_mailbox = layout[f"G{own}_CONTROL_MAILBOX_HPA"]
        self.windows = {layout[f"G{index}_HPA"]: index for index in (0, 1)}
        self.window_bytes = layout["GUEST_BYTES"]
        self.record = self.mailbox + header["BREACH_RECORD_OFFSET"]
        self.gigapage = header["BREACH_GIGAPAGE"]
        hgatp_own = SATP_SV39 | header["BREACH_VMID"] << VMID_SHIFT | \
            (self.mailbox + header["BREACH_SV39X4_OFFSET"]) >> 12
        keep = header["BREACH_KEEP"]
        self.modes = (
            (keep, keep, keep),
            (SATP_SV39 | (self.mailbox + header["BREACH_SV39_OFFSET"]) >> 12,
             keep, keep),
            (keep, hgatp_own, 0),
            (keep, SATP_SV39 | header["BREACH_VMID"] << VMID_SHIFT |
             layout[f"G{other}_ROOT_HPA"] >> 12, 0),
            (keep, hgatp_own, SATP_SV39 |
             (header["BREACH_FORGED_VS_ROOT"] - self.gigapage +
              header["BREACH_FORGED_GPA"]) >> 12),
        )

    def address(self, text, label, symbols=None):
        """An address expression's value: NAME or NAME+0xOFFSET, a hex
        number, or the secret's source, the ELF's SYMBOLS' when given."""
        if isinstance(text, str) and HEX.fullmatch(text):
            return int(text, 16)
        match = AT.fullmatch(text) if isinstance(text, str) else None
        require(match is not None, f"{label}: address {text!r} is not of "
                f"its form")
        offset = int(match.group("offset") or "0x0", 16)
        name = match.group("name")
        if name == "secret-source":
            require(symbols != {}, f"{label}: a call names the secret's "
                    f"source")
            return None if symbols is None else symbols[SECRET_SYMBOL] + offset
        require(name in self.names, f"{label}: no address is named {name!r}")
        return self.names[name] + offset

    def access(self, mode, target, label):
        """The address an attempt names to reach TARGET under MODE."""
        if mode == "bare":
            return target
        if mode == "gstage-other":
            base = self.layout[f"G{1 - self.domain}_HPA"]
            require(base <= target < base + self.window_bytes,
                    f"{label}: the other's root reaches its own window "
                    f"alone, not 0x{target:x}")
            return target - base + self.layout["GUEST_GPA"]
        require(self.gigapage <= target < self.gigapage + (1 << 30),
                f"{label}: 0x{target:x} is outside the hook's gigapage")
        offset = target - self.gigapage
        return offset + {"satp": self.header["BREACH_ALIAS_VA"],
                         "gstage-own": self.header["BREACH_FORGED_GPA"],
                         "vs-forged": 0}[mode]

    def walk(self, mode):
        """The memory MODE's translation reads: (what, address)."""
        own_root = self.mailbox + self.header["BREACH_SV39X4_OFFSET"]
        return {"bare": (),
                "satp": (("the hook's Sv39 root",
                          self.mailbox + self.header["BREACH_SV39_OFFSET"]),),
                "gstage-own": (("the hook's Sv39x4 root", own_root),),
                "gstage-other": (("the other's G-stage root", self.layout[
                    f"G{1 - self.domain}_ROOT_HPA"]),),
                "vs-forged": (("the hook's Sv39x4 root", own_root),
                              ("hart 0's forged VS-stage root",
                               self.header["BREACH_FORGED_VS_ROOT"]))}[mode]

    def initial(self, word):
        """A word's value before any attempt: a fill, or zero."""
        header = self.header
        control = (self.control_mailbox + header["BREACH_FILL_BLOCK"],
                   self.control_mailbox + header["BREACH_FILL_WORDS"] +
                   8 * header["BREACH_FILL_COUNT"])
        hook = (self.mailbox + header["BREACH_CONTROL_OFFSET"],
                self.mailbox + header["BREACH_CONTROL_OFFSET"] +
                header["BREACH_BLOCK_BYTES"] + 16)
        for low, high, base in (control + (self.control_mailbox,),
                                hook + (self.mailbox,)):
            if low <= word < high:
                return header["BREACH_FILL"] | (word - base)
        return 0


def load(path):
    try:
        value = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Refused(f"{path}: {error}") from error
    require(isinstance(value, dict) and value.get("schema") == SCHEMA,
            f"{path} is not a {SCHEMA} declaration")
    return value


def declared_rows(declaration, domain):
    """The declaration's rows for VS DOMAIN: VS domain 1's own in place."""
    rows = declaration.get("rows")
    require(isinstance(rows, list) and rows, "the declaration has no rows")
    replacements = declaration.get("g1", {})
    own = replacements if domain == 1 else {}
    names = [row.get("row") if isinstance(row, dict) else None
             for row in rows]
    require(len(set(names)) == len(names) and None not in names,
            "two rows share a name, or a row has none")
    require(isinstance(replacements, dict) and
            set(replacements) <= set(names) and
            all(isinstance(row, dict) and row.get("row") == name
                for name, row in replacements.items()),
            "g1 replaces a row the rows lack, or under another name")
    out = []
    for row in rows:
        row = own.get(row["row"], row)
        require(isinstance(row, dict) and set(row) <= ROW_KEYS,
                f"row {row.get('row')!r} has a key outside {sorted(ROW_KEYS)}")
        out.append(row)
    return out


def shape(row, label):
    """A row's op, width, mode, outcome, and witness, checked."""
    op = row.get("op")
    require(op in OPS, f"{label}: op {op!r}")
    outcome = row.get("outcome")
    require(outcome in OUTCOMES, f"{label}: outcome {outcome!r}")
    mode = row.get("mode", "bare")
    require(mode in MODES, f"{label}: mode {mode!r}")
    width = row.get("width", 0)
    if op in ("load", "store"):
        require(width in WIDTHS, f"{label}: width {width!r}")
    elif op in ("amoadd", "lrsc", "hlv", "hsv"):
        require(width == 8, f"{label}: an {op} is 8 bytes")
    else:
        require("width" not in row, f"{label}: {op} has no width")
    require((op in ("hlv", "hsv")) == mode.startswith(("gstage", "vs")),
            f"{label}: an H load or store, and only one, names a G-stage")
    require(op not in ("hlv", "hsv", "jump", "ecall", "cbo.zero",
                       "cbo.inval") or mode in ("bare", "gstage-own",
                                                "gstage-other", "vs-forged"),
            f"{label}: a {op} under satp")
    require((op == "ecall") == ("call" in row) and
            (op == "ecall") != ("at" in row),
            f"{label}: a call names call, and an access at")
    require((op == "ecall") == (outcome == "refused") and
            (op == "cbo.inval") == (outcome == "illegal"),
            f"{label}: a call is refused, and cbo.inval illegal")
    require("value" not in row or op == "store",
            f"{label}: a value for a store alone")
    witness = row.get("witness")
    if witness is not None:
        require(isinstance(witness, dict) and len(witness) == 1,
                f"{label}: witness {witness!r}")
        kind, value = next(iter(witness.items()))
        require(kind in ("copy", "word", "device"),
                f"{label}: witness {kind!r}")
        require(kind != "copy" or (op in READS and value in COPIES),
                f"{label}: a copy is a load's or an hlv's, of {COPIES}")
        require(kind != "word" or (op in WRITES and (
            value is True or isinstance(value, list) and value)),
                f"{label}: a word is a write's")
        require(kind != "device" or (op == "store" and value is True),
                f"{label}: a device witness is a store's")
    require(outcome != "allowed" or witness is not None,
            f"{label}: a control shows its effect")
    require(op not in ("jump", "cbo.inval", "ecall") or witness is None,
            f"{label}: a {op} has no witness")
    return op, width, mode, outcome, witness


def resolve(declaration, facts, discriminate=False, symbols=None):
    """Each row of the table: a dict with its name, number, operation,
    address, and the row's table words; the secret's source left None
    without SYMBOLS."""
    rows = []
    seen_device = {}
    for number_, row in enumerate(declared_rows(declaration,
                                                facts.domain), 1):
        label = f"row {row['row']}"
        op, width, mode, outcome, witness = shape(row, label)
        if discriminate and witness is None:
            continue
        item = {"row": row["row"], "number": number_, "op": op,
                "width": width, "mode": mode, "outcome": outcome,
                "witness": witness, "target": row["target"]}
        if op == "ecall":
            call = row["call"]
            require(isinstance(call, dict) and set(call) <= CALL_KEYS and
                    {"eid", "fid"} <= set(call),
                    f"{label}: call {call!r}")
            arguments = [facts.address(call[key], label, {})
                         if key in call else 0 for key in ("a0", "a1", "a2")]
            item.update(at=None, access=arguments[0], value=arguments[1],
                        extra=arguments[2],
                        call=number(call["eid"], label) << 32 |
                        number(call["fid"], label))
        else:
            target = facts.address(row["at"], label, symbols)
            require(mode == "bare" or not str(row["at"]).startswith(
                "secret-source"),
                    f"{label}: the secret's source is reached directly")
            item.update(at=target, extra=0, call=0)
            item["access"] = None if target is None else \
                facts.access(mode, target, label)
            if op in ("store", "amoadd", "lrsc", "hsv"):
                item["value"] = number(row["value"], label) if \
                    "value" in row else pattern(number_)
            else:
                item["value"] = 0
            if target is not None and target in facts.devices:
                require(width == facts.devices[target] or op == "jump",
                        f"{label}: the device register at 0x{target:x} is "
                        f"{facts.devices[target]} bytes wide")
                if op == "store":
                    seen_device[target] = item["value"] & \
                        ((1 << 8 * width) - 1)
                elif witness == {"copy": "device"}:
                    require(target in seen_device,
                            f"{label}: no earlier row writes the device")
                    item["device"] = seen_device[target]
            require(not (witness and "device" in witness) or
                    target in facts.devices,
                    f"{label}: 0x{target or 0:x} is not a device register "
                    f"the oracle reads")
        item["kind"] = number_ << 32 | OPS[op] << 16 | MODES[mode] << 8 | \
            width
        rows.append(item)
    require(len(rows) <= facts.header["BREACH_SLOTS"],
            f"{len(rows)} rows, more than the record's "
            f"{facts.header['BREACH_SLOTS']} slots")
    check_bytes(rows, facts)
    return rows


def span(item):
    """The bytes a row's own access reaches: [(low, high)]."""
    if item["at"] is None or item["op"] in ("jump", "ecall", "cbo.inval"):
        return []
    if item["op"] == "cbo.zero":
        low = item["at"] & ~(64 - 1)
        return [(low, low + 64)]
    return [(item["at"], item["at"] + item["width"])]


def check_bytes(rows, facts):
    """No witnessed row's bytes meet another's written bytes, and none
    reaches the hook's own record or roots."""
    record = (facts.mailbox + facts.header["BREACH_RECORD_OFFSET"],
              facts.mailbox + facts.layout["HART_MAILBOX_BYTES"])
    control = (facts.mailbox + facts.header["BREACH_CONTROL_OFFSET"],
               facts.mailbox + facts.header["BREACH_CONTROL_OFFSET"] +
               facts.header["BREACH_BLOCK_BYTES"] + 16)
    for item in rows:
        for low, high in span(item):
            inside = record[0] < high and low < record[1]
            require(not inside or (control[0] <= low and high <= control[1]),
                    f"row {item['row']} reaches the hook's own record or "
                    f"roots")
    witnessed = [item for item in rows if item["witness"] is not None]
    for index, item in enumerate(witnessed):
        if item["at"] in facts.devices:
            continue
        for other in witnessed[index + 1:]:
            if other["at"] in facts.devices or not (
                    item["op"] in WRITES or other["op"] in WRITES):
                continue
            for low, high in span(item):
                for low2, high2 in span(other):
                    require(high <= low2 or high2 <= low,
                            f"rows {item['row']} and {other['row']} meet "
                            f"at 0x{max(low, low2):x}")


# ------------------------------------------------------------------ table
def c_address(item, facts, row):
    if item["at"] is None and item["op"] != "ecall":
        offset = AT.fullmatch(row["at"]).group("offset") or "0x0"
        return f"(be_u64)(unsigned long)be_mvp_secret + {offset}UL"
    return f"0x{item['access']:x}UL"


def table_text(declaration, facts, discriminate):
    rows = resolve(declaration, facts, discriminate)
    by_name = {row["row"]: row for row in declared_rows(declaration,
                                                        facts.domain)}
    lines = ["/* Generated by tools/gen-breach.py: do not edit. */",
             "#ifndef BE_MVP_BREACH_TABLE_H",
             "#define BE_MVP_BREACH_TABLE_H",
             "",
             f"#define BE_MVP_BREACH_ROWS {len(rows)}U",
             "",
             "static const be_u64 be_mvp_breach_modes[BE_MVP_BREACH_MODES]"
             "[3] = {"]
    for mode in facts.modes:
        lines.append("\t{ " + ", ".join(f"0x{value:x}UL" for value in mode) +
                     " },")
    lines += ["};", "",
              "static const struct be_mvp_breach_attempt "
              "be_mvp_breach_attempts[BE_MVP_BREACH_ROWS] = {"]
    for item in rows:
        lines.append(f"\t/* {item['row']}: {item['target']} */")
        lines.append(f"\t{{ 0x{item['kind']:x}UL, "
                     f"{c_address(item, facts, by_name[item['row']])}, "
                     f"0x{item['value']:x}UL, 0x{item['extra']:x}UL, "
                     f"0x{item['call']:x}UL }},")
    lines += ["};", "", "#endif", ""]
    return "\n".join(lines)


# ------------------------------------------------------------------- plan
def nm_symbols(nm, elf):
    """{name: (address, size or None)} of ELF's defined symbols."""
    output = subprocess.run([str(nm), "-S", "--defined-only", str(elf)],
                            capture_output=True, text=True,
                            check=True).stdout
    symbols = {}
    for line in output.splitlines():
        match = NM_LINE.fullmatch(line.strip())
        if match:
            symbols.setdefault(match.group(4), (
                int(match.group(1), 16),
                int(match.group(2), 16) if match.group(2) else None))
    return symbols


def rights(descriptor, hart):
    """The hooked hart's profile: [(low, high, {rights})]; and whether its
    role's call list is empty."""
    extents = {extent["name"]: (int(extent["base"], 16),
                                int(extent["size"], 16))
               for extent in descriptor["extents"]}
    profiles = [profile for profile in descriptor["profiles"]
                if profile.get("hart") == hart]
    require(len(profiles) == 1, f"the descriptor has no one profile for "
            f"hart {hart}")
    out = []
    for access in profiles[0]["access"]:
        base, size = extents[access["extent"]]
        out.append((base, base + size, set(access["rights"])))
    calls = [role for role in descriptor["calls"]
             if role.get("role") == "vs-domain"]
    require(len(calls) == 1, "the descriptor has no one vs-domain call list")
    return out, calls[0]["allow"] == []


def has(profile, low, high, right):
    """The first byte of [LOW, HIGH) the profile does not give RIGHT, or
    None."""
    address = low
    while address < high:
        found = [end for start, end, given in profile
                 if start <= address < end and right in given]
        if not found:
            return address
        address = max(found)
    return None


def judged(item, facts, profile, empty_calls):
    """(outcome, stval) a boundary-on run must show for ITEM."""
    op = item["op"]
    if op == "ecall":
        return ("refused" if empty_calls else "allowed"), None
    if op == "cbo.inval":
        return "illegal", None
    for what, address in facts.walk(item["mode"]):
        if has(profile, address, address + 8, "read") is not None:
            return "denied", item["access"]
    needs = []
    if op in ("load", "hlv"):
        needs = [("read", span(item))]
    elif op == "lrsc":
        needs = [("read", span(item)), ("write", span(item))]
    elif op == "jump":
        needs = [("execute", [(item["at"], item["at"] + 4)])]
    else:
        needs = [("write", span(item))]
    for right, ranges in needs:
        for low, high in ranges:
            if has(profile, low, high, right) is not None:
                # QEMU checks PMP over all of an access's bytes at its
                # address and does not split it, so a denied access's
                # stval is its own address, a misaligned edge's too (K1):
                # accel/tcg/cputlb.c mmu_lookup() looks up the first page
                # with the access's whole size before it splits a page
                # crossing, and target/riscv/pmp.c fails an access only
                # partly inside an entry (M11-7's first run, 2026-11-16).
                return "denied", item["access"]
    return "allowed", None


def flat_word(data, base, address, width):
    offset = address - base
    require(0 <= offset and offset + width <= len(data),
            f"0x{address:x} is outside the image")
    return int.from_bytes(data[offset:offset + width], "little")


def pages_bytes(facts, secret, low, high):
    """The shared pages' bytes [LOW, HIGH) as hart 0 places them, and the
    unnamed page after them, zero."""
    base = facts.names["request"]
    out = b""
    for address in range(low, high):
        page = (address - base) // PAGE
        require(0 <= page <= 3, f"0x{address:x} is outside the pages")
        offset = address - base - page * PAGE
        out += bytes([secret[offset] if page == 2 and offset < len(secret)
                      else 0])
    return out


def copy_value(item, facts, inputs):
    """The value a load of ITEM reads in a run with no boundary."""
    source = item["witness"]["copy"]
    low, high = span(item)[0]
    if source == "image":
        return flat_word(inputs["flat"], facts.layout["MONITOR_HPA"], low,
                         high - low)
    if source == "boot-image":
        return flat_word(inputs["boot"], facts.layout["STAGING_HPA"], low,
                         high - low)
    if source == "dtb":
        window = [base for base in facts.windows
                  if base <= low < base + facts.window_bytes]
        require(len(window) == 1, f"row {item['row']}: 0x{low:x} is in no "
                f"window")
        dtb = inputs["dtbs"][facts.windows[window[0]]]
        start = window[0] + facts.layout["DTB_GPA"] - \
            facts.layout["GUEST_GPA"]
        require(start <= low and high <= start + facts.layout["DTB_BYTES"],
                f"row {item['row']}: 0x{low:x} is outside the DTB's page")
        data = dtb + bytes(facts.layout["DTB_BYTES"] - len(dtb))
        return int.from_bytes(data[low - start:high - start], "little")
    if source == "pages":
        return int.from_bytes(pages_bytes(facts, inputs["secret"], low,
                                          high), "little")
    if source == "zero":
        return 0
    if source == "device":
        return item["device"]
    require(low % 8 == 0 and high - low == 8,
            f"row {item['row']}: an end read is one aligned word")
    return {"end": f"0x{low:x}"}


def written(item, facts):
    """[(word, initial, after)] of a write's witness words with no
    boundary."""
    words = item["witness"]["word"]
    if item["op"] == "cbo.zero":
        low = item["at"] & ~63
        changes = {word: 0 for word in range(low, low + 64, 8)}
    else:
        data = (item["value"] if item["op"] != "amoadd" else 0)
        changes = {}
        for index in range(item["width"]):
            address = item["at"] + index
            word = address & ~7
            changes.setdefault(word, facts.initial(word))
            shift = 8 * (address - word)
            byte = (data >> 8 * index) & 0xff
            changes[word] = changes[word] & ~(0xff << shift) & MASK | \
                byte << shift
        if item["op"] == "amoadd":
            word = item["at"]
            changes = {word: (facts.initial(word) + item["value"]) & MASK}
    if words is not True:
        named = [facts.address(text, f"row {item['row']}") for text in words]
        require(set(named) <= set(changes),
                f"row {item['row']}: a witness word it does not write")
        changes = {word: changes[word] for word in named}
    return [(word, facts.initial(word), after)
            for word, after in sorted(changes.items())]


def plan_rows(rows, facts, boundary, inputs, profile=None,
              empty_calls=True):
    """Each slot's expectation and each witness, for a run of the image."""
    out, words, devices = [], {}, {}
    illegal = inputs["illegal"]
    for slot, item in enumerate(rows):
        label = f"row {item['row']}"
        outcome = "allowed"
        stval = None
        if boundary:
            outcome, stval = judged(item, facts, profile, empty_calls)
            require(outcome == item["outcome"],
                    f"{label}: declared {item['outcome']}, but the profile "
                    f"gives {outcome}")
        expect = {"cause": "none", "stval": "0x0", "value": "sentinel",
                  "error": "sentinel"}
        if outcome == "denied":
            expect.update(cause=f"0x{CAUSES[item['op']]:x}",
                          stval=f"0x{stval:x}")
        elif outcome == "illegal":
            expect.update(cause=f"0x{ILLEGAL:x}", stval=f"0x{illegal:x}")
        elif outcome == "refused":
            expect.update(value="0x0", error=f"0x{DENIED:x}")
        if item["op"] == "lrsc":
            expect["value"] = f"0x{facts.initial(item['at']):x}"
            if outcome == "allowed":
                expect["error"] = "0x0"
        elif item["op"] == "amoadd" and outcome == "allowed":
            expect["value"] = f"0x{facts.initial(item['at']):x}"
        elif item["op"] in READS and outcome == "allowed":
            value = copy_value(item, facts, inputs)
            expect["value"] = value if isinstance(value, dict) else \
                f"0x{value:x}"
        witness = item["witness"] or {}
        if "word" in witness:
            for word, initial, after in written(item, facts):
                require(word not in words, f"{label}: word 0x{word:x} is "
                        f"another row's witness")
                value = after if outcome == "allowed" else initial
                words[word] = {"row": item["row"], "address": f"0x{word:x}",
                               "expected": f"0x{value:x}"}
        if "device" in witness:
            width = facts.devices[item["at"]]
            value = item["value"] & ((1 << 8 * width) - 1) \
                if outcome == "allowed" else 0
            devices[item["at"]] = {
                "row": item["row"], "address": f"0x{item['at']:x}",
                "width": width, "expected": f"0x{value:x}"}
        out.append(dict(expect, row=item["row"], number=item["number"],
                        slot=slot, op=item["op"], mode=item["mode"],
                        outcome=outcome, access=f"0x{item['access']:x}"))
    counts = {"pmp_faults": sum(row["outcome"] == "denied" for row in out),
              "blocked_calls": sum(row["outcome"] == "refused"
                                   for row in out),
              "failed_calls": 0}
    return out, sorted(words.values(), key=lambda word: word["address"]), \
        sorted(devices.values(), key=lambda device: device["address"]), \
        counts


def word_name(*parts):
    """A word's name in the oracle's form (tests/qemu_oracle.py's NAME,
    lower case), which tests/check-boundary.py breach reads it by."""
    return "-".join(("breach",) + tuple(str(part) for part in parts)).lower()


def words_document(plan):
    """The oracle's --words: the record's header and slots, the witness
    words, each end read, and the device registers."""
    record = int(plan["record"], 16)
    header = plan["header_words"]
    words = [{"name": word_name("header", index),
              "address": f"0x{record + 8 * index:x}", "expected": None}
             for index in range(header)]
    slots = record + 8 * header
    for row in plan["rows"]:
        for index, field in enumerate(("cause", "stval", "value", "error")):
            words.append({"name": word_name(row["row"], field),
                          "address": f"0x{slots + 32 * row['slot'] + 8 * index:x}",
                          "expected": None})
        if isinstance(row["value"], dict):
            words.append({"name": word_name(row["row"], "end"),
                          "address": row["value"]["end"], "expected": None})
    words += [{"name": word_name("word", word["address"]),
               "address": word["address"], "expected": None}
              for word in plan["words"]]
    devices = [{"name": word_name("device", device["row"]),
                "address": device["address"], "expected": None}
               for device in plan["devices"]]
    return {"schema": WORDS_SCHEMA, "words": words, "devices": devices}


def illegal_word(flat, base, symbols):
    """The attempt helper's one cbo.inval word, which an illegal row's
    stval names."""
    address, size = symbols[ATTEMPT_HELPER]
    require(size is not None, f"{ATTEMPT_HELPER} has no size")
    words = [flat_word(flat, base, address + offset, 4)
             for offset in range(0, size, 4)]
    found = [word for word in words
             if word & 0x707f == 0x200f and word >> 20 == 0]
    require(len(found) == 1, f"{ATTEMPT_HELPER} holds {len(found)} "
            f"cbo.inval words, not one")
    return found[0]


def make_plan(declaration, facts, discriminate, image, symbols, inputs,
              descriptor=None):
    require((descriptor is None) == discriminate,
            "a boundary-on plan needs its descriptor, and an -off plan none")
    plain = {name: value[0] for name, value in symbols.items()}
    rows = resolve(declaration, facts, discriminate, plain)
    secret = plain.get(SECRET_SYMBOL)
    require(secret is not None, f"the image has no {SECRET_SYMBOL}")
    inputs = dict(inputs, secret=inputs["flat"][
        secret - facts.layout["MONITOR_HPA"]:
        secret - facts.layout["MONITOR_HPA"] +
        facts.layout["SECRET_BYTES"]],
        illegal=illegal_word(inputs["flat"], facts.layout["MONITOR_HPA"],
                             symbols))
    profile, empty = rights(descriptor, facts.hart) if descriptor else \
        (None, True)
    out, words, devices, counts = plan_rows(
        rows, facts, not discriminate, inputs, profile, empty)
    plan = {"schema": PLAN_SCHEMA, "image": image, "domain": facts.domain,
            "hart": facts.hart,
            "boundary": "off" if discriminate else "on",
            "record": f"0x{facts.record:x}",
            "header_words": facts.header["BREACH_HEADER_BYTES"] // 8,
            "magic": f"0x{facts.header['BREACH_MAGIC']:x}",
            "done": facts.header["BREACH_STATE_DONE"],
            "no_trap": f"0x{facts.header['BREACH_NO_TRAP']:x}",
            "sentinel": f"0x{facts.header['BREACH_SENTINEL']:x}",
            "rows": out, "words": words, "devices": devices,
            "counts": counts}
    return plan


def expected_counts(declaration_path, domain):
    """The commit record's counts a boundary-on breach run of VS DOMAIN
    declares: denied rows, refused rows, and no failed call."""
    declaration = load(declaration_path)
    rows = declared_rows(declaration, domain)
    return {"pmp_faults": sum(row.get("outcome") == "denied"
                              for row in rows),
            "blocked_calls": sum(row.get("outcome") == "refused"
                                 for row in rows),
            "failed_calls": 0}


def write_new(path, text):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


# -------------------------------------------------------------- self-test
HERE = pathlib.Path(__file__).resolve().parent
SOURCES = HERE.parent / "src"
DECLARATION = HERE.parent / "scenarios" / "anchor" / "breach.json"
# anchor's two VS-domain profiles as its descriptor states them
# (tools/gen-partition.py): (extent base, size, rights) per hart.
ANCHOR_PROFILES = {
    1: ((0x102008000, 0x2000, "rx"), (0x10200a000, 0x2000, "rx"),
        (0x102020000, 0x8000, "r"), (0x102028000, 0x1000, "r"),
        (0x102029000, 0x1000, "r"), (0x10202a000, 0x2000, "r"),
        (0x10202c000, 0x4000, "r"), (0x102040000, 0x10000, "rw"),
        (0x102060000, 0x4000, "rw"), (0x102070000, 0x8000, "rx"),
        (0x110000000, 0x4000000, "rwx"), (0x118000000, 0x1000, "rw"),
        (0x118001000, 0x1000, "r")),
    2: ((0x102008000, 0x2000, "rx"), (0x10200a000, 0x2000, "rx"),
        (0x102030000, 0x8000, "r"), (0x102038000, 0x1000, "r"),
        (0x102039000, 0x1000, "r"), (0x10203a000, 0x2000, "r"),
        (0x10203c000, 0x4000, "r"), (0x102050000, 0x10000, "rw"),
        (0x102064000, 0x4000, "rw"), (0x102070000, 0x8000, "rx"),
        (0x114000000, 0x4000000, "rwx"), (0x118000000, 0x1000, "r"),
        (0x118001000, 0x1000, "rw"), (0x118002000, 0x1000, "r")),
}
RIGHT_NAMES = {"r": "read", "w": "write", "x": "execute"}


def synthetic_descriptor(changes=None):
    """A descriptor of anchor's two VS-domain profiles, with CHANGES:
    {hart: [(base, size, rights)]} added."""
    extents, profiles = [], []
    for hart, rows in ANCHOR_PROFILES.items():
        access = []
        for base, size, given in rows + tuple((changes or {}).get(hart, ())):
            name = f"x{hart}-{base:x}-{size:x}"
            extents.append({"name": name, "base": f"0x{base:x}",
                            "size": f"0x{size:x}"})
            access.append({"extent": name, "rights": [
                RIGHT_NAMES[letter] for letter in given]})
        profiles.append({"name": f"g{hart - 1}", "hart": hart,
                         "access": access})
    return {"extents": extents, "profiles": profiles,
            "calls": [{"role": "vs-domain", "allow": []}]}


def synthetic_inputs(facts, symbols):
    """A flat image with an attempt helper holding one cbo.inval word,
    a boot image, two DTBs, all of known bytes."""
    base = facts.layout["MONITOR_HPA"]
    flat = bytearray(index * 7 & 0xff for index in
                     range(facts.layout["IMAGE_BYTES"]))
    helper, size = symbols[ATTEMPT_HELPER]
    flat[helper - base:helper - base + size] = bytes(size)
    flat[helper - base + 8:helper - base + 12] = (0x6a00f).to_bytes(4,
                                                                    "little")
    secret = symbols[SECRET_SYMBOL][0] - base
    flat[secret:secret + 32] = bytes(range(0x41, 0x61))
    boot = bytes(index * 3 & 0xff for index in range(0x2000))
    dtbs = (bytes([0xd0, 0x0d, 0xfe, 0xed]) + bytes(range(1, 200)),
            bytes([0xd0, 0x0d, 0xfe, 0xed]) + bytes(range(201, 255)))
    return {"flat": bytes(flat), "boot": boot, "dtbs": dtbs}


def oracle_reads(scratch, documents):
    """(ok, detail): tests/qemu_oracle.py's own reader and configuration
    check accept each words DOCUMENT, boundary-on under plain PMP and
    boundary-off."""
    path = pathlib.Path(__file__).resolve().parents[1] / "tests" / \
        "qemu_oracle.py"
    spec = importlib.util.spec_from_file_location("mvp_qemu_oracle", path)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    try:
        for index, document in enumerate(documents):
            words = scratch / f"words-{index}.json"
            words.unlink(missing_ok=True)
            write_new(words, json.dumps(document, indent=1) + "\n")
            named, devices = oracle.words_from_file(words)
            for on in (True, False):
                oracle.OracleConfig(
                    8, "k3-like", on, "readable", "readable", "absent",
                    0x80000000, 0x200000000, named,
                    "plain" if on else "none", devices).validate()
    except oracle.OracleError as error:
        return False, str(error)
    return True, f"{len(documents)} documents"


def self_test(scratch):
    scratch = pathlib.Path(scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    layout = defines(SOURCES / "mvp-layout.h")
    header = defines(SOURCES / "mvp-breach.h")
    declaration = load(DECLARATION)
    cases = []

    def case(name, call, want=None):
        try:
            result = call()
        except (Refused, KeyError, ValueError) as error:
            cases.append((name, want is not None and want in str(error),
                          str(error)))
            return None
        ok = want is None and (result is None or result is True or
                               result == () or result)
        cases.append((name, ok if result is not False else False,
                      "accepted" if want is not None else "passes"))
        return result

    facts = {domain: Facts(layout, header, declaration["devices"], domain)
             for domain in (0, 1)}
    symbols = {SECRET_SYMBOL: (0x102080688, 32),
               ATTEMPT_HELPER: (0x102071000, 0x200)}
    plain = {name: value[0] for name, value in symbols.items()}
    for domain, witnessed in ((0, 63), (1, 62)):
        rows = resolve(declaration, facts[domain], False, plain)
        off = resolve(declaration, facts[domain], True, plain)
        outcomes = [row["outcome"] for row in rows]
        cases.append((f"VS domain {domain}: 112 rows, 76 denied, 30 "
                      f"refused, one illegal, five controls; {witnessed} "
                      f"witnessed",
                      len(rows) == 112 and outcomes.count("denied") == 76
                      and outcomes.count("refused") == 30 and
                      outcomes.count("illegal") == 1 and
                      outcomes.count("allowed") == 5 and
                      len(off) == witnessed,
                      f"{len(rows)} {len(off)}"))
        counts = expected_counts(DECLARATION, domain)
        cases.append((f"VS domain {domain}'s counts",
                      counts == {"pmp_faults": 76, "blocked_calls": 30,
                                 "failed_calls": 0}, str(counts)))
    g0 = {row["row"]: row for row in resolve(declaration, facts[0], False,
                                             plain)}
    g1 = {row["row"]: row for row in resolve(declaration, facts[1], False,
                                             plain)}
    cases.append(("the modes: the hook's roots in its own mailbox",
                  facts[0].modes[1][0] == SATP_SV39 | 0x102049 and
                  facts[0].modes[2][1] == SATP_SV39 | 0x3fff << 44 |
                  0x10204c and facts[1].modes[3][1] == SATP_SV39 |
                  0x3fff << 44 | 0x102020 and facts[0].modes[4][2] ==
                  SATP_SV39 | 0xc2016, str(facts[0].modes)))
    cases.append(("addresses by mode: the alias VA, the forged GPA, the "
                  "other's GPA, the VS-stage VA",
                  g0["L1"]["access"] == 0x58002000 and
                  g0["L3"]["access"] == 0xd8002008 and
                  g0["L5"]["access"] == 0x83e00000 and
                  g0["L7"]["access"] == 0x18002010 and
                  g1["L5"]["access"] == 0x83e00000 and
                  g1["L5"]["at"] == 0x113e00000,
                  str([g0[name]["access"] for name in ("L1", "L3", "L5",
                                                         "L7")])))
    cases.append(("a store's pattern and a device store's value",
                  g0["A2"]["value"] == 0xb5ea0002b5ea0002 and
                  g0["I1"]["value"] == 0xa5 and g0["I3"]["at"] ==
                  0x0d000024 and g1["I6"]["at"] == 0x28008000 and
                  g0["I6"]["at"] == 0x28010000, ""))
    cases.append(("a call's registers", g0["M21"]["access"] == 8 and
                  g0["M21"]["value"] == 0x118002000 and g0["M3"]["value"]
                  == layout["PARK_ENTRY_HPA"] and g0["M29"]["call"] ==
                  0x800424600000000, hex(g0["M29"]["call"])))
    text = table_text(declaration, facts[0], False)
    cases.append(("the table names the secret's source by its symbol",
                  "#define BE_MVP_BREACH_ROWS 112U" in text and
                  text.count("be_mvp_secret + 0x0UL") == 1 and
                  text.count("\t{ 0x") == 112 + 5, ""))
    descriptor = synthetic_descriptor()
    inputs = synthetic_inputs(facts[0], symbols)
    plans = []
    for domain in (0, 1):
        plan = case(f"VS domain {domain}'s rows judged by its profile",
                    lambda domain=domain: make_plan(
                        declaration, facts[domain], False,
                        f"breach-g{domain}", symbols, inputs, descriptor))
        if plan:
            plans.append(plan)
            by_row = {row["row"]: row for row in plan["rows"]}
            stval = {0: ("K1", "0x118001ffc", "K2", "0x10205fffc"),
                     1: ("K1", "0x118002ffc", "K2", "0x102063ffc")}[domain]
            cases.append((f"VS domain {domain}: an edge's stval is its "
                          f"access's own address (QEMU checks the whole "
                          f"access)",
                          by_row[stval[0]]["stval"] == stval[1] and
                          by_row[stval[2]]["stval"] == stval[3],
                          by_row[stval[0]]["stval"]))
            cases.append((f"VS domain {domain}: a walk's fault names the "
                          f"access", by_row["L5"]["stval"] == "0x83e00000"
                          and by_row["L5"]["cause"] == "0x5" and
                          by_row["L8"]["cause"] == "0x7",
                          by_row["L5"]["stval"]))
            cases.append((f"VS domain {domain}: the illegal row's stval is "
                          f"the helper's cbo.inval",
                          by_row["H5"]["cause"] == "0x2" and
                          by_row["H5"]["stval"] == "0x6a00f", ""))
            cases.append((f"VS domain {domain}: a refused call's error and "
                          f"value", by_row["M26"]["error"] ==
                          "0xfffffffffffffffc" and by_row["M26"]["value"]
                          == "0x0" and by_row["M26"]["cause"] == "none",
                          ""))
            fill = header["BREACH_FILL"]
            words = {word["address"]: word["expected"]
                     for word in plan["words"]}
            control = layout[f"G{domain}_CONTROL_MAILBOX_HPA"]
            cases.append((f"VS domain {domain}: a denied write's word keeps "
                          f"its fill, a control's shows its write",
                          words[f"0x{control + 0x3fc0:x}"] ==
                          f"0x{fill | 0x3fc0:x}" and
                          by_row["P5"]["error"] == "0x0" and
                          by_row["P5"]["value"] == f"0x{fill | 0x8fc0:x}"
                          and by_row["H3"]["value"] ==
                          f"0x{fill | 0x3fd0:x}", ""))
    off = case("VS domain 0's -off plan: every witnessed row runs",
               lambda: make_plan(declaration, facts[0], True,
                                 "breach-g0-off", symbols, inputs))
    if off:
        by_row = {row["row"]: row for row in off["rows"]}
        words = {word["address"]: word["expected"] for word in off["words"]}
        fill = header["BREACH_FILL"]
        secret = bytes(range(0x41, 0x61))
        cases.append(("-off: no trap, the copies' known bytes",
                      all(row["cause"] == "none" for row in off["rows"]) and
                      by_row["B1"]["value"] ==
                      f"0x{int.from_bytes(secret[:8], 'little'):x}" and
                      by_row["K3"]["value"] ==
                      f"0x{int.from_bytes(secret[1:9], 'little'):x}" and
                      by_row["K1"]["value"] ==
                      f"0x{int.from_bytes(bytes(4) + secret[:4], 'little'):x}"
                      and by_row["A1"]["value"] ==
                      f"0x{int.from_bytes(inputs['dtbs'][1][:8], 'little'):x}"
                      and by_row["D5"]["value"] == {"end": "0x102084000"} and
                      by_row["I2"]["value"] == "0xa5" and
                      by_row["I4"]["value"] == "0x1", str(by_row["K1"])))
        cases.append(("-off: each write's word after it",
                      words["0x10205fff8"] == "0xb5ea004300000000" and
                      words["0x102038f00"] == "0xb5ea00450000" and
                      words[f"0x{0x10202c000 + 0x3fc8:x}"] ==
                      f"0x{(fill | 0x3fc8) + 0xb5ea0025b5ea0025 & MASK:x}"
                      and
                      words[f"0x{0x10202c000 + 0x3f80:x}"] == "0x0" and
                      words["0x117e00ff8"] == "0xb5ea0002b5ea0002" and
                      off["devices"][0]["expected"] == "0xa5",
                      str({key: words[key] for key in ("0x10205fff8",
                                                       "0x102038f00")})))
        document = words_document(off)
        names = [word["name"] for word in document["words"] +
                 document["devices"]]
        cases.append(("the oracle's words: unique names, the record and "
                      "every witness", len(names) == len(set(names)) and
                      document["words"][0]["address"] == "0x102048100" and
                      len(document["devices"]) == 2, str(len(names))))
        cases.append(("the oracle reads each plan's words file as a "
                      "boundary-on or -off run's", *oracle_reads(
                          scratch, (words_document(off),) + tuple(
                              words_document(plan) for plan in plans))))

    def edited(change, domain=0, discriminate=False, symbols_=plain):
        def call():
            copied = json.loads(json.dumps(declaration))
            change(copied)
            return resolve(copied, facts[domain], discriminate, symbols_)
        return call

    def row_edit(name, **values):
        def change(copied):
            row = next(row for row in copied["rows"] if row["row"] == name)
            row.update(values)
            for key in [key for key, value in values.items() if value is None]:
                del row[key]
        return change
    for name, change, want in (
            ("an op of no kind", row_edit("A1", op="probe"), "op"),
            ("a jump with a width", row_edit("A3", width=8), "no width"),
            ("a store of two bytes", row_edit("A2", width=2), "width"),
            ("a write meeting another row's bytes",
             row_edit("A2", at="other.dtb+0xff0"), "meet"),
            ("a row in the hook's record",
             row_edit("P2", at="own.hart-mailbox+0x8200"),
             "own record"),
            ("a device read with no earlier write",
             lambda copied: copied["rows"].remove(next(
                 row for row in copied["rows"] if row["row"] == "I1")),
             "no earlier row"),
            ("a control without a witness", row_edit("P1", witness=None),
             "shows its effect"),
            ("a jump under satp", row_edit("A3", mode="satp"),
             "under satp"),
            ("a target the alias cannot reach",
             row_edit("L1", at="m-memory"), "gigapage"),
            ("the other's root beyond its window",
             row_edit("L5", at="secret"), "own window alone"),
            ("g1 replacing a row the rows lack",
             lambda copied: copied["g1"].update(Z9={"row": "Z9"}),
             "lack"),
            ("two rows sharing a name", row_edit("A2", row="A1"),
             "share a name"),
            ("an unknown address name", row_edit("A1", at="nowhere"),
             "named"),
            ("a call that is not refused", row_edit("M1", outcome="denied"),
             "refused"),
            ("a call naming the secret's source",
             row_edit("M21", call={"eid": "0x4442434e", "fid": "0x0",
                                   "a0": "0x8", "a1": "secret-source"}),
             "secret's source"),
            ("the secret's source under a translation",
             row_edit("C1", mode="satp"), "reached directly")):
        case(f"refused: {name}", edited(change), want)
    case("refused: a declared outcome the profile does not give",
         lambda: make_plan(declaration, facts[0], False, "breach-g0",
                           symbols, inputs, synthetic_descriptor(
                               {1: ((0x118002000, 0x1000, "r"),)})),
         "but the profile gives allowed")
    case("refused: a boundary-on plan without its descriptor",
         lambda: make_plan(declaration, facts[0], False, "breach-g0",
                           symbols, inputs), "needs its descriptor")
    failed = [item for item in cases if not item[1]]
    for name, ok, detail in cases:
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")
    print(f"BE_MVP_BREACH_SELF_TEST: {'FAIL' if failed else 'PASS'} "
          f"cases={len(cases)}")
    return 1 if failed else 0


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch")
    commands = parser.add_subparsers(dest="command")
    for name in ("table", "plan", "counts"):
        command = commands.add_parser(name)
        command.add_argument("--declaration", required=True)
        command.add_argument("--domain", type=int, required=True)
        if name == "counts":
            continue
        command.add_argument("--layout", required=True)
        command.add_argument("--header", required=True)
        command.add_argument("--discriminate", action="store_true")
        command.add_argument("--out", required=True)
        if name == "plan":
            for option in ("--image", "--elf", "--bin", "--boot-img",
                           "--dtb0", "--dtb1", "--nm", "--words"):
                command.add_argument(option, required=True)
            command.add_argument("--descriptor")
    args = parser.parse_args(argv[1:])
    try:
        if args.self_test:
            if args.command is not None or not args.scratch:
                parser.error("--self-test requires --scratch and no command")
            return self_test(args.scratch)
        if args.command is None:
            parser.error("table, plan, counts, or --self-test")
        if args.command == "counts":
            print(json.dumps(expected_counts(args.declaration, args.domain),
                             sort_keys=True))
            return 0
        declaration = load(args.declaration)
        facts = Facts(defines(args.layout), defines(args.header),
                      declaration.get("devices", {}), args.domain)
        if args.command == "table":
            write_new(args.out, table_text(declaration, facts,
                                           args.discriminate))
            print(f"BE_MVP_BREACH_TABLE: PASS domain={args.domain} "
                  f"discriminate={int(args.discriminate)} out={args.out}")
            return 0
        symbols = nm_symbols(args.nm, args.elf)
        inputs = {"flat": pathlib.Path(args.bin).read_bytes(),
                  "boot": pathlib.Path(args.boot_img).read_bytes(),
                  "dtbs": (pathlib.Path(args.dtb0).read_bytes(),
                           pathlib.Path(args.dtb1).read_bytes())}
        descriptor = json.loads(pathlib.Path(args.descriptor).read_text(
            encoding="utf-8")) if args.descriptor else None
        plan = make_plan(declaration, facts, args.discriminate, args.image,
                         symbols, inputs, descriptor)
        write_new(args.out, json.dumps(plan, indent=1, sort_keys=True) +
                  "\n")
        write_new(args.words, json.dumps(words_document(plan), indent=1) +
                  "\n")
        print(f"BE_MVP_BREACH_PLAN: PASS image={args.image} "
              f"boundary={plan['boundary']} rows={len(plan['rows'])} "
              f"words={len(plan['words'])} counts={plan['counts']}")
        return 0
    except (Refused, OSError, ValueError, KeyError,
            subprocess.CalledProcessError) as error:
        print(f"BE_MVP_BREACH: FAIL {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
