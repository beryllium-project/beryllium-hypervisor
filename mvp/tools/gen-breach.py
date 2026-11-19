#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""The hostile-monitor attempts of the breach images (M11-7, M11-8).

  gen-breach.py table --declaration FILE --layout H --header H --domain N
                [--discriminate] [--platform-file F] --out mvp-breach-table.h
  gen-breach.py plan --declaration FILE --layout H --header H --domain N
                [--discriminate] [--platform-file F] --image NAME --elf ELF
                --bin BIN --boot-img IMG --dtb0 DTB --dtb1 DTB --nm NM
                [--descriptor JSON] --out PLAN --words WORDS
  gen-breach.py counts --declaration FILE --domain N
  gen-breach.py board-check --declaration FILE --layout H --header H
                --domain N --platform-file F [--devices F] [--mutations]
  gen-breach.py expect --declaration FILE --domain N --candidate F
                --image NAME --out F
  gen-breach.py --self-test --scratch DIR

  N is the hooked VS domain, 0 or 1, or control, the control hart (M11-8).

Purpose: planning/mvp-m11-plan.md, D-10's VS-domain column and, for the
control role, its control-hart column, as anchor's breach images run them.
table writes, before the link, the C table the hook (src/mvp-breach.c)
runs: one row per attempt of the declaration (scenarios/anchor/
breach.json, or breach-control.json for the control role), VS domain 1's
rows its own where it names them, each row's access address made from its
physical target by its translation mode, and the role's modes' satp,
hgatp, and vsatp; under --discriminate, the rows with a witness alone.
plan writes, after the link, what a run of the linked image must show
(tests/check-boundary.py breach): for each slot, its trap's cause and
stval, the value it kept, and the call's error; each witness word's value
at the end; and the device registers'; with the oracle's words file
(tests/qemu_oracle.py --words). For a boundary-on image (--descriptor)
each row is checked against the hooked hart's profile and its role's call
list first: denied needs a right the profile lacks (an access's own, or
its translation's walk), allowed every right it needs, refused a call the
list does not hold, rejected a listed console write whose buffer or upper
address word the firmware refuses (with that error), and zero a listed
console write of no byte. counts gives the expected commit-record counts.
M11-B (planning/mvp-m11-board-addendum.md, B-10): board-check, and table
and plan with --platform-file, check a board declaration (k3/breach/) on
the board's description (k3/platform.json) and its list or --devices;
--mutations makes B9's. expect writes a board image's expectation.
Trust: a generator and a checker of its own declaration. It refuses a
row of unknown form, a target its mode cannot reach, a cache-block row
(cbo.zero, cbo.inval) whose address is not its block's first byte, a row
it would judge allowed whose bytes lie in more than one extent of the
profile (an access must lie wholly inside one PMP entry), two witnessed
rows whose written or read bytes meet (so each effect is one row's), a
row in the hook's own record or roots, a listed call that would succeed
with an effect (a console write of bytes, a shutdown) or that it does not
model, a declaration of the other role, and a declaration that does not
fit the record. The record's layout is read from src/mvp-breach.h.
For a board declaration (stop B9) it requires B-10's five devices held by
their facts' nodes alone, enabled, its devices the description's, no
device witness, each row's bytes and named call arguments wholly in one of
the five, the firmware's place, or memory outside low_reserved, meeting no
other device, and an effects entry for each write, jump, or call on a
device or the firmware's memory, and none for a row that only reads.
Scope: anchor's breach-g0, breach-g1, and breach-c and their -off copies;
M11-B's k3-breach-g1 and k3-breach-c.
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
# M11-8: the control role, hart 0 (breach-c), and its modes: its own
# forged hgatp, each VS domain's own G-stage root, and its forged hgatp
# with the VS-stage root in forbidden memory.
CONTROL = "control"
CONTROL_MODES = {"bare": 0, "satp": 1, "gstage-forged": 2, "gstage-g0": 3,
                 "gstage-g1": 4, "vs-forged": 5}
OUTCOMES = ("denied", "illegal", "refused", "rejected", "zero", "allowed")
# A call's outcomes: refused by the list (SBI_ERR_DENIED, blocked_calls),
# listed and rejected by the firmware with ERRORS' error (failed_calls),
# or listed, of no byte, and successful with value 0.
CALL_OUTCOMES = ("refused", "rejected", "zero")
ERRORS = {"failed": -1, "invalid-param": -3}
COPIES = ("image", "boot-image", "dtb", "pages", "zero", "end", "device",
          "fill")
READS = ("load", "hlv")
WRITES = ("store", "amoadd", "lrsc", "cbo.zero", "hsv")
WIDTHS = (1, 4, 8)
ROW_KEYS = {"row", "target", "op", "width", "mode", "at", "value",
            "outcome", "error", "witness", "call"}
CALL_KEYS = {"eid", "fid", "a0", "a1", "a2"}
DEVICE_KEYS = {"uart", "aplic-m", "aplic-s", "aplic-source", "imsic-m",
               "imsic-m-stride", "imsic-s", "imsic-s-stride", "test", "mtime",
               "mtimecmp", "m-memory", "unnamed-ram"}
# M11-B: a board declaration's devices (B-10).
BOARD_DEVICE_KEYS = {"console", "console-scratch", "console-scratch-width",
                     "aplic-m", "imsic-m", "imsic-s", "imsic-s-stride",
                     "mtime", "mtimecmp", "timer-width", "m-memory",
                     "unnamed-ram"}
WIDTH_KEYS = ("aplic-source", "console-scratch-width", "timer-width")
PLATFORM_SCHEMA = "be-mvp-k3-platform-v1"
DEVICES_SCHEMA = "be-mvp-k3-devices-v1"
# B-10's five devices by kind, each with its root device (None: the breach
# facts'), the kinds that hold persistent state, and the rows that change
# something.
FIVE = {"console": "console", "interrupt-controller-m": "aplic-m",
        "interrupt-file-m": "imsic-m", "timer": "clint",
        "interrupt-file-s": None}
PERSISTENT = ("spi-flash-controller", "efuse", "i2c", "power-management",
              "storage")
CHANGES = WRITES + ("cbo.inval", "jump", "ecall")
AT = re.compile(r"(?P<name>[a-z][a-z0-9.-]*?)(?:\+(?P<offset>0x[0-9a-f]+))?")
HEX = re.compile(r"0x[0-9a-f]+")
NM_LINE = re.compile(r"([0-9a-f]+)(?: ([0-9a-f]+))? ([A-Za-z]) (\S+)")
MASK = (1 << 64) - 1
SATP_SV39 = 8 << 60
VMID_SHIFT = 44
CAUSES = {"load": 5, "hlv": 5, "jump": 1, "store": 7, "amoadd": 7,
          "lrsc": 7, "cbo.zero": 7, "hsv": 7}
# The cache block that cbo.zero and cbo.inval name (QEMU's cboz and cbom
# block sizes): a row's address is its first byte, so that the stval QEMU
# reports, the block-aligned address, is the row's own (judged()).
CACHE_BLOCK = 64
ILLEGAL = 2
DENIED = (-4) & MASK
# The console write (DBCN function 0), the one listed call whose result
# the generator models (M11-8).
DBCN_WRITE = (0x4442434E, 0)
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
    and the hooked role: VS domain 0 or 1, or the control hart (CONTROL;
    M11-8), whose names call each VS domain's extents g0 and g1."""

    def __init__(self, layout, header, devices, domain):
        require(domain in (0, 1, CONTROL),
                f"the hooked role {domain!r} is not VS domain 0 or 1 or "
                f"the control hart")
        self.layout, self.header, self.domain = layout, header, domain
        self.control = domain == CONTROL
        # M11-B: a board declaration's devices, chosen by its keys.
        self.board = set(devices) == BOARD_DEVICE_KEYS
        require(self.board or set(devices) == DEVICE_KEYS,
                f"the devices are {sorted(devices)}, not "
                f"{sorted(DEVICE_KEYS)}, or the board's")
        device = {key: (value if key in WIDTH_KEYS else
                        number(value, f"device {key}"))
                  for key, value in devices.items()}
        require(self.board or isinstance(device["aplic-source"], int) and
                1 <= device["aplic-source"] <= 96,
                "the APLIC source is not 1 to 96")
        dtb = layout["DTB_GPA"] - layout["GUEST_GPA"]
        names = {
            "park": layout["PARK_ENTRY_HPA"],
            "monitor.control-text": layout["MONITOR_CONTROL_TEXT_HPA"],
            "monitor.input": layout["MONITOR_INPUT_HPA"],
            "mvp.boot-data": layout["MVP_BOOT_DATA_HPA"],
            "diagnostic": layout["DIAGNOSTIC_HPA"],
            "control.tail": layout["CONTROL_STACK_HPA"] +
            layout["CONTROL_STACK_BYTES"],
            "core.padding": layout["CONTROL_PROFILE_HPA"] +
            layout["CONTROL_PROFILE_BYTES"],
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
            "aplic-m": device["aplic-m"],
            "imsic-m.hart0": device["imsic-m"],
            "imsic-s.hart0": device["imsic-s"],
            "mtime": device["mtime"],
            "mtimecmp.hart0": device["mtimecmp"],
            "m-memory": device["m-memory"],
            "unnamed-ram": device["unnamed-ram"],
        }
        if self.board:
            scratch = device["console"] + device["console-scratch"]
            names.update({"console": device["console"],
                          "console.scratch": scratch})
            # The registers whose width the board's register forms fix.
            self.devices = {scratch: device["console-scratch-width"],
                            device["mtime"]: device["timer-width"],
                            device["mtimecmp"]: device["timer-width"]}
        else:
            names.update({"uart": device["uart"],
                          "aplic-s": device["aplic-s"],
                          "aplic-s.source": device["aplic-s"] +
                          4 * device["aplic-source"],
                          "test": device["test"]})
            self.devices = {device["uart"] + 7: 1,
                            names["aplic-s.source"]: 4}
        if self.control:
            self.hart = layout["CONTROL_HART"]
            sides = (("g0", 0), ("g1", 1))
        else:
            own, other = domain, 1 - domain
            self.hart = layout[f"DOMAIN{own}_HART"]
            self.other_hart = layout[f"DOMAIN{other}_HART"]
            sides = (("own", own), ("other", other))
        for side, index in sides:
            names[f"imsic-s.{side}"] = device["imsic-s"] + \
                layout[f"DOMAIN{index}_HART"] * device["imsic-s-stride"]
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
        self.windows = {layout[f"G{index}_HPA"]: index for index in (0, 1)}
        self.window_bytes = layout["GUEST_BYTES"]
        self.gigapage = header["BREACH_GIGAPAGE"]
        keep = header["BREACH_KEEP"]
        vmid = header["BREACH_VMID"] << VMID_SHIFT
        if self.control:
            self.mode_names = CONTROL_MODES
            self.record = header["BREACH_CONTROL_RECORD_HPA"]
            self.slots = header["BREACH_CONTROL_SLOTS"]
            forged = SATP_SV39 | vmid | \
                header["BREACH_CONTROL_SV39X4_HPA"] >> 12
            self.modes = (
                (keep, keep, keep),
                (SATP_SV39 | header["BREACH_CONTROL_SV39_HPA"] >> 12, keep,
                 keep),
                (keep, forged, 0),
                (keep, SATP_SV39 | vmid | layout["G0_ROOT_HPA"] >> 12, 0),
                (keep, SATP_SV39 | vmid | layout["G1_ROOT_HPA"] >> 12, 0),
                (keep, forged, SATP_SV39 |
                 (header["BREACH_CONTROL_VS_ROOT_HPA"] - self.gigapage +
                  header["BREACH_FORGED_GPA"]) >> 12),
            )
            count = header["BREACH_CONTROL_MODES"]
        else:
            self.mode_names = MODES
            self.mailbox = layout[f"G{own}_HART_MAILBOX_HPA"]
            self.control_mailbox = layout[f"G{own}_CONTROL_MAILBOX_HPA"]
            self.record = self.mailbox + header["BREACH_RECORD_OFFSET"]
            self.slots = header["BREACH_SLOTS"]
            hgatp_own = SATP_SV39 | vmid | \
                (self.mailbox + header["BREACH_SV39X4_OFFSET"]) >> 12
            self.modes = (
                (keep, keep, keep),
                (SATP_SV39 | (self.mailbox + header["BREACH_SV39_OFFSET"]) >>
                 12, keep, keep),
                (keep, hgatp_own, 0),
                (keep, SATP_SV39 | vmid | layout[f"G{other}_ROOT_HPA"] >> 12,
                 0),
                (keep, hgatp_own, SATP_SV39 |
                 (header["BREACH_FORGED_VS_ROOT"] - self.gigapage +
                  header["BREACH_FORGED_GPA"]) >> 12),
            )
            count = header["BREACH_MODES"]
        require(len(self.modes) == len(self.mode_names) == count,
                f"the role's {len(self.modes)} modes are not the header's "
                f"{count}")

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
        if mode in ("gstage-other", "gstage-g0", "gstage-g1"):
            index = 1 - self.domain if mode == "gstage-other" else \
                int(mode[-1])
            base = self.layout[f"G{index}_HPA"]
            require(base <= target < base + self.window_bytes,
                    f"{label}: VS domain {index}'s root reaches its own "
                    f"window alone, not 0x{target:x}")
            return target - base + self.layout["GUEST_GPA"]
        require(self.gigapage <= target < self.gigapage + (1 << 30),
                f"{label}: 0x{target:x} is outside the hook's gigapage")
        offset = target - self.gigapage
        return offset + {"satp": self.header["BREACH_ALIAS_VA"],
                         "gstage-own": self.header["BREACH_FORGED_GPA"],
                         "gstage-forged": self.header["BREACH_FORGED_GPA"],
                         "vs-forged": 0}[mode]

    def walk(self, mode):
        """The memory MODE's translation reads: (what, address)."""
        if self.control:
            header = self.header
            forged = ("the hook's forged Sv39x4 root",
                      header["BREACH_CONTROL_SV39X4_HPA"])
            return {"bare": (),
                    "satp": (("the hook's Sv39 root",
                              header["BREACH_CONTROL_SV39_HPA"]),),
                    "gstage-forged": (forged,),
                    "gstage-g0": (("VS domain 0's G-stage root",
                                   self.layout["G0_ROOT_HPA"]),),
                    "gstage-g1": (("VS domain 1's G-stage root",
                                   self.layout["G1_ROOT_HPA"]),),
                    "vs-forged": (forged, (
                        "the forged VS-stage root",
                        header["BREACH_CONTROL_VS_ROOT_HPA"]))}[mode]
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

    def hook_regions(self):
        """The hook's own record and roots, which no row may reach:
        [(low, high)], and the parts of them its control rows may."""
        header = self.header
        if self.control:
            record = (self.record, self.record +
                      header["BREACH_HEADER_BYTES"] +
                      self.slots * header["BREACH_SLOT_BYTES"])
            roots = [(address, address + size) for address, size in (
                (header["BREACH_CONTROL_SV39_HPA"], PAGE),
                (header["BREACH_CONTROL_SV39X4_HPA"], 4 * PAGE),
                (header["BREACH_CONTROL_VS_ROOT_HPA"], PAGE))]
            return [record] + roots, []
        control = self.mailbox + header["BREACH_CONTROL_OFFSET"]
        return [(self.record, self.mailbox +
                 self.layout["HART_MAILBOX_BYTES"])], \
            [(control, control + header["BREACH_BLOCK_BYTES"] + 16)]

    def initial(self, word):
        """A word's value before any attempt: a fill, or zero."""
        header = self.header
        if self.control:
            block = header["BREACH_CONTROL_BLOCK_HPA"]
            fills = [(block, block + header["BREACH_CONTROL_FILL_BYTES"],
                      self.record)]
            for index in (0, 1):
                mailbox = self.layout[f"G{index}_HART_MAILBOX_HPA"]
                low = mailbox + header["BREACH_MAILBOX_FILL"]
                fills.append((low, low + header["BREACH_MAILBOX_FILL_BYTES"],
                              mailbox))
            for low, high, base in fills:
                if low <= word < high:
                    return header["BREACH_FILL"] | (word - base)
            return 0
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


def load(path, schema=SCHEMA, what="declaration"):
    try:
        value = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Refused(f"{path}: {error}") from error
    require(isinstance(value, dict) and value.get("schema") == schema,
            f"{path} is not a {schema} {what}")
    return value


def declared_rows(declaration, domain):
    """The declaration's rows for the hooked role DOMAIN: VS domain 1's own
    in place; a control declaration (its role CONTROL) the control hart's
    alone, and a VS-domain one never the control hart's; one that names
    its VS domain (M11-B) that domain's alone."""
    role = declaration.get("role", "vs-domain")
    want = CONTROL if domain == CONTROL else "vs-domain"
    require(role == want, f"the declaration is the {role} role's, not "
            f"the {want} role's")
    named = declaration.get("domain", domain)
    require(named == domain, f"the declaration names VS domain {named!r}, "
            f"not the hooked role {domain!r}")
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


def shape(row, label, modes=None):
    """A row's op, width, mode, outcome, and witness, checked: its mode one
    of MODES (the hooked role's, by name)."""
    op = row.get("op")
    require(op in OPS, f"{label}: op {op!r}")
    outcome = row.get("outcome")
    require(outcome in OUTCOMES, f"{label}: outcome {outcome!r}")
    mode = row.get("mode", "bare")
    require(mode in (MODES if modes is None else modes),
            f"{label}: mode {mode!r}")
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
                       "cbo.inval") or mode != "satp",
            f"{label}: a {op} under satp")
    require((op == "ecall") == ("call" in row) and
            (op == "ecall") != ("at" in row),
            f"{label}: a call names call, and an access at")
    require((op == "ecall") == (outcome in CALL_OUTCOMES) and
            (op == "cbo.inval") == (outcome == "illegal"),
            f"{label}: a call is refused, rejected, or of no byte, and "
            f"cbo.inval illegal")
    require(("error" in row) == (outcome == "rejected") and
            row.get("error", "failed") in ERRORS,
            f"{label}: a rejected call names its error, one of "
            f"{sorted(ERRORS)}, and no other row names one")
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
        op, width, mode, outcome, witness = shape(row, label,
                                                  facts.mode_names)
        if discriminate and witness is None:
            continue
        item = {"row": row["row"], "number": number_, "op": op,
                "width": width, "mode": mode, "outcome": outcome,
                "witness": witness, "target": row["target"],
                "error": row.get("error")}
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
            require(op not in ("cbo.zero", "cbo.inval") or target is None or
                    target % CACHE_BLOCK == 0,
                    f"{label}: a {op} at 0x{target or 0:x}, not the first "
                    f"byte of a {CACHE_BLOCK}-byte cache block")
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
        item["kind"] = number_ << 32 | OPS[op] << 16 | \
            facts.mode_names[mode] << 8 | width
        rows.append(item)
    require(len(rows) <= facts.slots,
            f"{len(rows)} rows, more than the record's {facts.slots} slots")
    check_bytes(rows, facts)
    return rows


def span(item):
    """The bytes a row's own access reaches: [(low, high)]."""
    if item["at"] is None or item["op"] in ("jump", "ecall", "cbo.inval"):
        return []
    if item["op"] == "cbo.zero":
        low = item["at"] & ~(CACHE_BLOCK - 1)
        return [(low, low + CACHE_BLOCK)]
    return [(item["at"], item["at"] + item["width"])]


def check_bytes(rows, facts):
    """No witnessed row's bytes meet another's written bytes, and none
    reaches the hook's own record or roots."""
    own, open_ = facts.hook_regions()
    for item in rows:
        for low, high in span(item):
            inside = any(start < high and low < end for start, end in own)
            require(not inside or any(start <= low and high <= end
                                      for start, end in open_),
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
             "static const be_u64 be_mvp_breach_modes"
             "[BE_MVP_BREACH_ROLE_MODES][3] BE_MVP_BREACH_RODATA = {"]
    for mode in facts.modes:
        lines.append("\t{ " + ", ".join(f"0x{value:x}UL" for value in mode) +
                     " },")
    lines += ["};", "",
              "static const struct be_mvp_breach_attempt "
              "be_mvp_breach_attempts[BE_MVP_BREACH_ROWS] "
              "BE_MVP_BREACH_RODATA = {"]
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


def rights(descriptor, hart, role="vs-domain"):
    """The hooked hart's profile: [(low, high, {rights})]; and its ROLE's
    call list: [(extension, function, argument index or None for any,
    maximum)]."""
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
    calls = [entry for entry in descriptor["calls"]
             if entry.get("role") == role]
    require(len(calls) == 1, f"the descriptor has no one {role} call list")
    allow = []
    for entry in calls[0]["allow"]:
        argument = entry["argument"]
        require(argument == "any" or isinstance(argument, int) and
                0 <= argument < 6, f"a {role} list entry's argument "
                f"{argument!r}")
        allow.append((number(entry["extension"], "an extension"),
                      number(entry["function"], "a function"),
                      None if argument == "any" else argument,
                      number(entry["maximum"], "a maximum")))
    return out, allow


def listed(calls, eid, fid, arguments):
    """Whether the call list CALLS holds a call (the firmware's
    sbi_dcommit_call_allowed()): an entry of its extension and function
    whose argument is any, or whose argument is at most its maximum."""
    return any((extension, function) == (eid, fid) and (
        argument is None or arguments[argument] <= maximum)
        for extension, function, argument, maximum in calls)


def judged_call(item, profile, calls):
    """(outcome, error) a boundary-on run must show for a call: refused
    where CALLS do not list it; a listed console write as the firmware's
    handler decides it (lib/sbi/sbi_ecall_dbcn.c): an upper address word
    not zero, rejected FAILED; no byte, zero; a buffer that wraps, or is
    not readable and writable in the profile, rejected INVALID_PARAM. Any
    other listed call would have an effect, or is not modelled."""
    eid, fid = item["call"] >> 32, item["call"] & 0xFFFFFFFF
    length, buffer, upper = item["access"], item["value"], item["extra"]
    # The attempt helper's a3 to a5 hold a0 to a2 at its ecall.
    if not listed(calls, eid, fid, (length, buffer, upper) * 2):
        return "refused", None
    require((eid, fid) == DBCN_WRITE, f"row {item['row']}: a listed call "
            f"of extension 0x{eid:x}, function {fid}, which this generator "
            f"does not model")
    if upper:
        return "rejected", ERRORS["failed"]
    if length == 0:
        return "zero", None
    if buffer + length > MASK or \
            has(profile, buffer, buffer + length, "read") is not None or \
            has(profile, buffer, buffer + length, "write") is not None:
        return "rejected", ERRORS["invalid-param"]
    raise Refused(f"row {item['row']}: a listed console write of {length} "
                  f"bytes, which the console would print")


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


def within_one(profile, low, high, right):
    """Whether one extent of the profile gives RIGHT to all of [LOW, HIGH).
    An access that is not wholly inside one PMP entry fails whatever the
    entries allow (F-23), and two extents may be two entries, so only then
    can a row be judged allowed (W-1)."""
    return any(start <= low and high <= end and right in given
               for start, end, given in profile)


def judged(item, facts, profile, calls):
    """(outcome, detail) a boundary-on run must show for ITEM: a denied
    access's stval, a rejected call's error, or None."""
    op = item["op"]
    if op == "ecall":
        return judged_call(item, profile, calls)
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
    for right, ranges in needs:
        for low, high in ranges:
            require(within_one(profile, low, high, right),
                    f"row {item['row']}: its bytes 0x{low:x} to 0x{high:x} "
                    f"lie in more than one extent that gives {right}, "
                    f"which may be more than one PMP entry: a row this "
                    f"generator cannot judge")
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
            f"row {item['row']}: an end or fill read is one aligned word")
    if source == "fill":
        value = facts.initial(low)
        require(value != 0, f"row {item['row']}: 0x{low:x} holds no fill")
        return value
    return {"end": f"0x{low:x}"}


def written(item, facts):
    """[(word, initial, after)] of a write's witness words with no
    boundary."""
    words = item["witness"]["word"]
    if item["op"] == "cbo.zero":
        low = item["at"] & ~(CACHE_BLOCK - 1)
        changes = {word: 0 for word in range(low, low + CACHE_BLOCK, 8)}
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


def plan_rows(rows, facts, boundary, inputs, profile=None, calls=()):
    """Each slot's expectation and each witness, for a run of the image."""
    out, words, devices = [], {}, {}
    illegal = inputs["illegal"]
    for slot, item in enumerate(rows):
        label = f"row {item['row']}"
        outcome = "allowed"
        stval = None
        if boundary:
            outcome, stval = judged(item, facts, profile, calls)
            source = "the call list" if item["op"] == "ecall" else \
                "the profile"
            require(outcome == item["outcome"],
                    f"{label}: declared {item['outcome']}, but {source} "
                    f"gives {outcome}")
            require(outcome != "rejected" or
                    stval == ERRORS[item["error"]],
                    f"{label}: declared the error {item['error']}, but the "
                    f"firmware gives {stval}")
        expect = {"cause": "none", "stval": "0x0", "value": "sentinel",
                  "error": "sentinel"}
        if outcome == "denied":
            expect.update(cause=f"0x{CAUSES[item['op']]:x}",
                          stval=f"0x{stval:x}")
        elif outcome == "illegal":
            expect.update(cause=f"0x{ILLEGAL:x}", stval=f"0x{illegal:x}")
        elif outcome == "refused":
            expect.update(value="0x0", error=f"0x{DENIED:x}")
        elif outcome == "rejected":
            expect.update(value="0x0", error=f"0x{stval & MASK:x}")
        elif outcome == "zero":
            expect.update(value="0x0", error="0x0")
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
              "failed_calls": sum(row["outcome"] == "rejected"
                                  for row in out)}
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
    role = CONTROL if facts.control else "vs-domain"
    profile, calls = rights(descriptor, facts.hart, role) if descriptor \
        else (None, [])
    out, words, devices, counts = plan_rows(
        rows, facts, not discriminate, inputs, profile, calls)
    # The record's domain word: the hooked VS domain, or the control
    # role's word.
    domain = facts.header["BREACH_CONTROL_ROLE"] if facts.control else \
        facts.domain
    plan = {"schema": PLAN_SCHEMA, "image": image, "domain": domain,
            "role": role, "hart": facts.hart,
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
    """The commit record's counts a boundary-on breach run of the hooked
    role DOMAIN declares: denied rows, refused rows, and rejected rows."""
    declaration = load(declaration_path)
    rows = declared_rows(declaration, domain)
    return {"pmp_faults": sum(row.get("outcome") == "denied"
                              for row in rows),
            "blocked_calls": sum(row.get("outcome") == "refused"
                                 for row in rows),
            "failed_calls": sum(row.get("outcome") == "rejected"
                                for row in rows)}


def write_new(path, text):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


# ------------------------------------------------------------------ board
def board_devices(platform):
    """A board declaration's devices but unnamed-ram: the facts of the
    board's description PLATFORM (k3/platform.json)."""
    roots, breach = platform["root_devices"], platform["breach"]
    scratch, imsic = breach["console_scratch"], breach["imsic_s"]
    return {"console": roots["console"]["base"],
            "aplic-m": roots["aplic-m"]["base"],
            "imsic-m": roots["imsic-m"]["base"],
            "console-scratch": scratch["offset"],
            "console-scratch-width": scratch["width"],
            "imsic-s": imsic["base"], "imsic-s-stride": imsic["stride"],
            "mtime": breach["mtime"], "mtimecmp": breach["mtimecmp"],
            "timer-width": breach["timer_width"],
            "m-memory": platform["firmware"]["load"]}


def meets(ranges, low, high):
    """Whether [LOW, HIGH) meets RANGES; a range of size 0 meets nothing."""
    return any(start < min(end, high) and low < end for start, end in ranges)


def ranges(device):
    """A listed device's reg (the description's list, or the recipe's
    devices.json) as ranges, [(low, high)]."""
    return [(number(base, "a reg"), number(base, "a reg") +
             number(size, "a reg")) for base, size in device["reg"]]


def targets(item, row, facts):
    """The bytes that a board row names: an access's, a jump's four, a
    cache block, a byte for each call argument written as an address name
    (a number is none), and for the secret's source the monitor's image."""
    if item["op"] == "ecall":
        values = zip(("a0", "a1", "a2"),
                     (item["access"], item["value"], item["extra"]))
        return [(value, value + 1) for key, value in values
                if not HEX.fullmatch(str(row["call"].get(key, "0x0")))]
    low = item["at"]
    if low is None:
        low = facts.layout["MONITOR_HPA"]
        return [(low, low + facts.layout["IMAGE_BYTES"])]
    size = {"jump": 4, "cbo.zero": CACHE_BLOCK, "cbo.inval": CACHE_BLOCK}
    return [(low, low + size.get(item["op"], item["width"]))]


def admit(low, high, place, label):
    """The board's target rule (B-10, stop B9), an allowlist: the class of
    [LOW, HIGH), or a refusal, its most specific reason first."""
    where = f"{label}: its bytes 0x{low:x} to 0x{high:x}"
    met = [device for device in place["devices"]
           if meets(ranges(device), low, high)]
    held = [f"{device['kind']} {device['path']}" for device in met
            if device["kind"] in PERSISTENT]
    require(not held, f"{where} meet a device that holds persistent "
            f"state: {', '.join(held)}")
    other = [device["path"] for device in met if device["kind"] not in FIVE]
    require(not other, f"{where} meet {', '.join(other[:1])}, a device "
            f"that B-10 does not list")
    if met:
        require(len(met) == 1 and any(start <= low and high <= end for
                                      start, end in ranges(met[0])),
                f"{where} are not wholly inside one range of one of B-10's "
                f"devices: {', '.join(device['path'] for device in met)}")
        return "device"
    (begin, end), (base, top) = place["firmware"], place["low_reserved"]
    if begin <= low and high <= end:
        return "firmware"
    require(not meets(((base, begin), (end, top)), low, high),
            f"{where} are in the real-time cores' memory")
    first, last = place["memory"]
    require(first <= low and high <= last and
            not meets(((base, top),), low, high), f"{where} lie in no "
            f"listed device, nor wholly in the firmware's place or in "
            f"memory outside low_reserved")
    return "memory"


def board_rules(declaration, facts, platform, listed):
    """A board declaration's rules (M11-B; B-10, stop B9) on the board's
    description PLATFORM and its device list LISTED: the number of the
    rows' targets in each class, or a refusal."""
    named = declaration.get("platform")
    require(named == platform.get("platform") and facts.board,
            f"the declaration's platform {named!r} or devices are not the "
            f"description's")
    require(facts.control or "domain" in declaration,
            "the board's declaration of a VS domain names no domain")
    breach, roots = platform["breach"], platform["root_devices"]
    clint = number(roots["clint"]["base"], "the CLINT's base")
    require(platform["harts"]["cache_block"] == CACHE_BLOCK and (number(
        breach["mtime"], "mtime"), number(breach["mtimecmp"], "mtimecmp"))
            == (clint + 0xbff8, clint + 0x4000), f"the description's cache "
            f"block is not {CACHE_BLOCK} bytes, or its mtime and hart 0's "
            f"mtimecmp not its CLINT's (base + 0xbff8, base + 0x4000)")
    for kind, fact in FIVE.items():
        path = (breach["imsic_s"] if fact is None else roots[fact])["path"]
        held = [(d["path"], d["status"]) for d in listed if d["kind"] == kind]
        require(held == [(path, "okay")], f"the kind {kind} is held by "
                f"{held}, not by {path} alone, enabled")
    wrong = sorted(key for key, value in board_devices(platform).items()
                   if declaration["devices"][key] != value)
    require(not wrong, f"the declaration's devices {wrong} are not the "
            f"description's")
    rows = {row["row"]: row for row in declared_rows(declaration,
                                                      facts.domain)}
    place = {"devices": listed, "firmware": tuple(number(
        platform["firmware"][key], key) for key in ("load", "end_max"))}
    for key in ("memory", "low_reserved"):
        base = number(platform[key]["base"], key)
        place[key] = (base, base + number(platform[key]["size"], key))
    found = {}
    for item in resolve(declaration, facts):
        witness = item["witness"] or {}
        require("device" not in witness and witness.get("copy") != "device",
                f"row {item['row']}: a device witness, which no board row "
                f"has")
        found[item["row"]] = item["op"], [
            admit(low, high, place, f"row {item['row']}")
            for low, high in targets(item, rows[item["row"]], facts)]
    effects = declaration.get("effects")
    require(isinstance(effects, dict), "the board's declaration has no "
            "effects, {row: text} (T-4)")
    for name, (op, classes) in found.items():
        require(op not in CHANGES or name in effects or not {
            "device", "firmware"} & set(classes), f"row {name}: a {op} on "
            f"a device or the firmware's memory, which effects does not name")
    for name in effects:
        require(found.get(name, ("",))[0] in CHANGES, f"effects names "
                f"{name!r}, no row that writes, jumps, or calls")
    classes = [kind for _, row in found.values() for kind in row]
    return {kind: classes.count(kind) for kind in ("device", "firmware",
                                                   "memory")} | {
        "effects": len(effects), "listed": len(listed)}


def board_mutations(declaration, facts, platform, listed):
    """B9's mutations (the design's 6.3): each one change at a path in a
    copy of the declaration (0), the description (1), or the list (2), its
    address taken from the list, refused by its own reason alone:
    [(name, ok, detail)]."""
    base = number(platform["memory"]["base"], "memory")
    memory = ((base, base + number(platform["memory"]["size"], "memory")),)

    def kinds(at):
        return {device["kind"] for device in listed
                if meets(ranges(device), at, at + 4)}

    def start(device):
        return next((low for low, high in ranges(device)[:1]
                     if low < high), None)
    free = [at for at in sorted({0, memory[0][1]} | {
        high for device in listed for _, high in ranges(device)})
            if not kinds(at) and not meets(memory, at, at + 4)]
    edge = [high for kind in FIVE for device in listed if device["kind"]
            == kind for low, high in ranges(device)
            if low + 4 <= high and high in free]
    r, e, spare, specs = (0, "rows", "I1"), (0, "effects"), None, []
    for kind in PERSISTENT + ("other",):
        device = next((d for d in listed if d["kind"] == kind and start(d)
                       is not None and (kind != "other" or kinds(start(d)) ==
                                        {"other"})), None)
        spare = device["path"] if device and kind == "other" else spare
        want = device and (f"meet {device['path']}," if kind == "other"
                           else f"{kind} {device['path']}")
        specs.append((f"a row on the first {kind}", r, device and {
            "at": hex(start(device))}, want))
    imsic = (2, platform["breach"]["imsic_s"]["path"])
    specs += [
        ("the real-time cores' memory", r,
         {"at": platform["firmware"]["end_max"]}, "real-time cores'"),
        ("an address that nothing holds", r, free and {"at": hex(free[0])},
         "in no listed device"),
        ("off the end of one of the five", r, edge and {
            "at": hex(edge[0] - 4), "width": 8}, "not wholly inside"),
        ("a device witness", r, {"witness": {"device": True}}, "a device "
         "witness"),
        ("an 8-byte timer access", (0, "rows", "J4"), {"width": 8},
         "4 bytes wide"),
        ("the S-level files disabled", imsic, {"status": "x"}, "s is held"),
        ("a device not the description's", (0, "devices"),
         {"mtime": "0x0"}, "devices ['mtime']"),
        ("another cache block", (1, "harts"), {"cache_block": 32},
         "cache block"),
        ("mtime not the CLINT's", (1, "breach"), {"mtime": "0x0"},
         "cache block"),
        ("another platform", (0,), {"platform": "x"}, "platform 'x'"),
        ("no effects", (0,), {"effects": None}, "no effects"),
        ("a device store with no effect", e, {"I1": None}, "I1: a store"),
        ("an effect of a load", e, {"I2": "a"}, "names 'I2'"),
        ("an effect of no row", e, {"Z9": "a"}, "names 'Z9'")]
    specs += [(f"a name the board lacks: {name}", r, {"at": name},
               f"named '{name}'") for name in ("test", "aplic-s")]
    specs += [(f"a sixth device of the kind {kind}", (2, spare),
               {"kind": kind}, f"the kind {kind} is held") for kind in FIVE]
    specs += [] if facts.control else [
        ("a VS domain's declaration without it", (0,), {"domain": None},
         "names no domain")]
    out = []
    for name, path, changes, want in specs:
        if not changes or None in path:
            out.append((name, False, "the list holds no address for it"))
            continue
        copies = target = json.loads(json.dumps([declaration, platform,
                                                 listed]))
        for key in path:
            target = target[key] if isinstance(key, int) or isinstance(
                target, dict) else next(item for item in target if key in (
                    item.get("row"), item.get("path")))
        for key, value in changes.items():
            target.pop(key) if value is None else target.update({key: value})
        try:
            board_rules(copies[0], Facts(facts.layout, facts.header, copies[
                0]["devices"], facts.domain), *copies[1:])
            out.append((name, False, "accepted"))
        except Refused as error:
            out.append((name, want in str(error), str(error)))
    return out


def board_input(declaration, facts, platform_file, devices_file=None,
                discriminate=False):
    """A board declaration's description, list, and rules' counts (M11-B),
    from --platform-file and --devices; None for QEMU's, which takes none.
    A board declaration has no -off copy."""
    board = "platform" in declaration
    require(board == (platform_file is not None) and not (
        board and discriminate), "a board declaration, and only one, takes "
            "--platform-file, and it has no -off copy")
    if not board:
        return None
    platform = load(platform_file, PLATFORM_SCHEMA, "description")
    listed = load(devices_file, DEVICES_SCHEMA, "list")["list"] if \
        devices_file else platform["devices"]["list"]
    return platform, listed, board_rules(declaration, facts, platform,
                                         listed)


def board_expectation(path, domain, candidate, image):
    """The expectation of the board's image IMAGE (M11-B; the design's
    6.6): CANDIDATE, its candidate's, with image, where, toolchains,
    change, and the boundary's counts replaced, the counts PATH's."""
    name = "breach-c" if domain == CONTROL else f"breach-g{domain}"
    require("platform" in load(path) and image == f"k3-{name}" and
            candidate.get("image") == name == candidate.get(
                "boundary", {}).get("pair"), f"{image} is not the board's "
            f"image of {name}, {path} a board declaration, or the "
            f"candidate's expectation {name}'s with the boundary on")
    out = json.loads(json.dumps(candidate))
    out.update(image=image, where=["qemu", "board"], toolchains=["gcc"],
               change=f"{name}'s image with the attempts of "
               f"{pathlib.Path(path).resolve().relative_to(HERE.parent)} "
               f"(planning/mvp-m11-board-addendum.md, B-10), the board's "
               f"devices in place of QEMU's, under {name}'s descriptor and "
               f"identity. {name}: {candidate['change']}")
    out["boundary"]["counts"] = {str(candidate["breach"]["hart"]): {
        key: value for key, value in expected_counts(path, domain).items()
        if value}}
    return out


# -------------------------------------------------------------- self-test
HERE = pathlib.Path(__file__).resolve().parent
SOURCES = HERE.parent / "src"
DECLARATION = HERE.parent / "scenarios" / "anchor" / "breach.json"
CONTROL_DECLARATION = HERE.parent / "scenarios" / "anchor" / \
    "breach-control.json"
# M11-B: the board's two declarations, and its fragments' directory.
K3 = HERE.parent / "k3"
BOARD_DECLARATIONS = {1: K3 / "breach" / "breach-g1.json",
                      CONTROL: K3 / "breach" / "breach-c.json"}
# anchor's control profile in step 2 (M11-8) and its two VS-domain
# profiles as its descriptor states them (tools/gen-partition.py):
# (extent base, size, rights) per hart.
ANCHOR_PROFILES = {
    0: ((0x102004000, 0x2000, "rx"), (0x102008000, 0x2000, "rx"),
        (0x102010000, 0x2000, "rw"), (0x102012000, 0x1000, "rw"),
        (0x102013000, 0x1000, "rw"), (0x102014000, 0x2000, "rw"),
        (0x102016000, 0x2000, "rw"), (0x10202c000, 0x4000, "rw"),
        (0x10203c000, 0x4000, "rw"), (0x102040000, 0x10000, "r"),
        (0x102050000, 0x10000, "r"), (0x102068000, 0x8000, "rx"),
        (0x102084000, 0x2000, "r"), (0x102086000, 0x2000, "r")),
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
    """A descriptor of anchor's control and two VS-domain profiles, with
    CHANGES: {hart: [(base, size, rights)]} added, and their call lists:
    the control role's anchor's (the console write, and the shutdown of
    type 0), the VS role's empty."""
    extents, profiles = [], []
    for hart, rows in ANCHOR_PROFILES.items():
        access = []
        for base, size, given in rows + tuple((changes or {}).get(hart, ())):
            name = f"x{hart}-{base:x}-{size:x}"
            extents.append({"name": name, "base": f"0x{base:x}",
                            "size": f"0x{size:x}"})
            access.append({"extent": name, "rights": [
                RIGHT_NAMES[letter] for letter in given]})
        profiles.append({"name": f"g{hart - 1}" if hart else "control",
                         "hart": hart, "access": access})
    return {"extents": extents, "profiles": profiles,
            "calls": [{"role": "control", "allow": [
                {"argument": "any", "extension": "0x4442434e",
                 "function": "0x0", "maximum": "0x0"},
                {"argument": 0, "extension": "0x53525354",
                 "function": "0x0", "maximum": "0x0"}]},
                      {"role": "vs-domain", "allow": []}]}


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


def control_cases(case, cases, layout, header, symbols, inputs, scratch):
    """The control role's cases (M11-8): its declaration's rows, modes,
    and counts; its plan judged by anchor's control profile and call list;
    its -off plan; and its refusals."""
    declaration = load(CONTROL_DECLARATION)
    facts = Facts(layout, header, declaration["devices"], CONTROL)
    plain = {name: value[0] for name, value in symbols.items()}
    rows = resolve(declaration, facts, False, plain)
    off = resolve(declaration, facts, True, plain)
    outcomes = [row["outcome"] for row in rows]
    cases.append(("control: 132 rows, 88 denied, two illegal, 28 refused, "
                  "seven rejected, two of no byte, five controls; 73 "
                  "witnessed",
                  len(rows) == 132 and outcomes.count("denied") == 88 and
                  outcomes.count("illegal") == 2 and
                  outcomes.count("refused") == 28 and
                  outcomes.count("rejected") == 7 and
                  outcomes.count("zero") == 2 and
                  outcomes.count("allowed") == 5 and len(off) == 73,
                  f"{len(rows)} {len(off)}"))
    counts = expected_counts(CONTROL_DECLARATION, CONTROL)
    cases.append(("control: its counts, each rejected call a failed one",
                  counts == {"pmp_faults": 88, "blocked_calls": 28,
                             "failed_calls": 7}, str(counts)))
    vmid = 0x3fff << VMID_SHIFT
    cases.append(("control: the modes, its Sv39 root in its padding page, "
                  "its forged roots in VS domain 0's mailbox and pool",
                  facts.modes[1][0] == SATP_SV39 | 0x102013 and
                  facts.modes[2][1] == SATP_SV39 | vmid | 0x10204c and
                  facts.modes[3][1] == SATP_SV39 | vmid | 0x102020 and
                  facts.modes[4][1] == SATP_SV39 | vmid | 0x102030 and
                  facts.modes[5] == (header["BREACH_KEEP"],
                                     facts.modes[2][1],
                                     SATP_SV39 | 0xc2026),
                  str(facts.modes)))
    by_row = {row["row"]: row for row in rows}
    cases.append(("control: addresses by mode",
                  by_row["L1"]["access"] == 0x58002000 and
                  by_row["L3"]["access"] == 0xd8002008 and
                  by_row["L5"]["access"] == 0x83e00000 and
                  by_row["L6"]["access"] == 0x83e00ff0 and
                  by_row["L7"]["access"] == 0x18002010 and
                  by_row["P3"]["access"] == 0xc2084000 and
                  by_row["I5"]["at"] == 0x28008000 and
                  by_row["I6"]["at"] == 0x28010000,
                  str([hex(by_row[name]["access"]) for name in
                       ("L1", "L3", "L5", "L6", "L7", "P3")])))
    descriptor = synthetic_descriptor()
    plan = case("control: its rows judged by the control profile and its "
                "call list", lambda: make_plan(
                    declaration, facts, False, "breach-c", symbols, inputs,
                    descriptor))
    fill = header["BREACH_FILL"]
    if plan:
        got = {row["row"]: row for row in plan["rows"]}
        cases.append(("control: the record's place and role word, and the "
                      "plan's counts",
                      plan["record"] == "0x102016000" and plan["hart"] == 0
                      and plan["domain"] == 0xc0 and
                      plan["role"] == CONTROL and plan["counts"] == counts,
                      str(plan["counts"])))
        cases.append(("control: a listed write's buffer refused by the "
                      "firmware, its upper word not zero, and no byte",
                      got["R1"]["error"] == f"0x{(-3) & MASK:x}" and
                      got["R5"]["error"] == f"0x{(-3) & MASK:x}" and
                      got["R6"]["error"] == f"0x{(-3) & MASK:x}" and
                      got["R7"]["error"] == f"0x{(-1) & MASK:x}" and
                      got["R1"]["value"] == "0x0" and
                      got["Z2"]["error"] == "0x0" and
                      got["Z2"]["value"] == "0x0" and
                      got["M22"]["error"] == f"0x{DENIED:x}",
                      str(got["R7"])))
        cases.append(("control: edges, walks, and the read-only mailbox",
                      got["K1"]["stval"] == "0x102087ffc" and
                      got["K1"]["cause"] == "0x5" and
                      got["K2"]["stval"] == "0x102017ffc" and
                      got["L5"]["stval"] == "0x83e00000" and
                      got["L7"]["cause"] == "0x5" and
                      got["L8"]["cause"] == "0x7" and
                      got["H3"]["value"] == f"0x{fill | 0xbfd0:x}" and
                      got["H5"]["cause"] == "0x2" and
                      got["P1"]["value"] == f"0x{fill | 0x1f40:x}" and
                      got["P5"]["error"] == "0x0",
                      str(got["K1"])))
    off_plan = case("control: its -off plan, every witnessed row run",
                    lambda: make_plan(declaration, facts, True,
                                      "breach-c-off", symbols, inputs))
    if off_plan:
        words = {word["address"]: word["expected"]
                 for word in off_plan["words"]}
        cases.append(("control -off: the straddling write's two words, the "
                      "mailbox's zeroed block, and its own block",
                      words["0x102017ff8"] == "0xb5ea005000000000" and
                      words["0x102018000"] == "0xb5ea0050" and
                      words[f"0x{0x102040000 + 0xbf80:x}"] == "0x0" and
                      words["0x102017f00"] == "0x0" and
                      words["0x102017f48"] == "0xb5ea0081b5ea0081",
                      str({key: words[key] for key in
                           ("0x102017ff8", "0x102018000")})))
        cases.append(("control: the oracle reads its plans' words files",
                      *oracle_reads(scratch / "control", (
                          words_document(off_plan),) + ((
                              words_document(plan),) if plan else ()))))

    def edited(change, domain=CONTROL, source=declaration):
        def call():
            copied = json.loads(json.dumps(source))
            change(copied)
            role = Facts(layout, header, copied["devices"], domain)
            return make_plan(copied, role, False, "breach-c", symbols,
                             inputs, descriptor) if domain == CONTROL \
                else resolve(copied, role, False, plain)
        return call

    def row_edit(name, **values):
        def change(copied):
            row = next(row for row in copied["rows"] if row["row"] == name)
            row.update(values)
            for key in [key for key, value in values.items()
                        if value is None]:
                del row[key]
        return change
    write = {"eid": "0x4442434e", "fid": "0x0", "a0": "0x8",
             "a1": "diagnostic"}
    for name, change, want in (
            ("a listed console write of bytes",
             row_edit("R1", call=write, outcome="rejected"),
             "a listed console write of 8 bytes"),
            ("a listed shutdown",
             row_edit("M23", call={"eid": "0x53525354", "fid": "0x0",
                                   "a0": "0x0"}),
             "which this generator does not model"),
            ("a rejected call declaring another error",
             row_edit("R7", error="invalid-param"),
             "declared the error invalid-param, but the firmware gives -1"),
            ("a rejected call naming no error", row_edit("R1", error=None),
             "names its error"),
            ("a refused call naming an error",
             row_edit("M1", error="failed"), "names its error"),
            ("a listed call declared refused",
             row_edit("Z1", outcome="refused"),
             "declared refused, but the call list gives zero"),
            ("a row in its own record",
             row_edit("P2", at="control.tail+0x100"),
             "reaches the hook's own record or roots"),
            ("a row in its own Sv39 root",
             row_edit("P2", at="control.padding+0x8"),
             "reaches the hook's own record or roots"),
            ("a row in its forged VS-stage root",
             row_edit("E2", at="g0.pool+0x6008"),
             "reaches the hook's own record or roots"),
            ("a fill read where no fill lies",
             row_edit("P1", at="control.tail+0x1fe0"), "holds no fill"),
            ("a VS role's mode", row_edit("L3", mode="gstage-own"),
             "mode 'gstage-own'")):
        case(f"control refused: {name}", edited(change), want)
    case("control refused: its declaration for a VS domain",
         edited(lambda copied: None, domain=0),
         "the declaration is the control role's, not the vs-domain role's")
    case("control refused: a VS-domain declaration for the control hart",
         edited(lambda copied: None,
                source=load(DECLARATION)),
         "the declaration is the vs-domain role's, not the control role's")


def board_cases(case, cases, layout, header, symbols, inputs):
    """The board's rules (M11-B) on the partition backend's stand-in
    description (every value made up), with the timer's registers and a
    power-management block over its eFuse block: each board declaration
    with the stand-in's devices, its targets, table, plan, and mutations;
    the refusals of the interface, the domain rule, and expect."""
    platform = load(K3 / "fixtures" / "partition" / "platform.json",
                    PLATFORM_SCHEMA, "description")
    clint = number(platform["root_devices"]["clint"]["base"], "the CLINT")
    platform["breach"].update(mtime=hex(clint + 0xbff8),
                              mtimecmp=hex(clint + 0x4000))
    listed = platform["devices"]["list"]
    listed.append(dict(next(device for device in listed if device["kind"]
                            == "efuse"), path="/soc/pmu",
                       kind="power-management"))
    for role, want in ((1, [10, 3, 73, 33, 0]), (CONTROL, [10, 4, 85, 31, 7])):
        declaration = dict(load(BOARD_DECLARATIONS[role]),
                           platform=platform["platform"])
        declaration["devices"].update(board_devices(platform))
        facts = Facts(layout, header, declaration["devices"], role)
        made = case(f"board {role}: its rules, table, and plan", lambda: (
            board_rules(declaration, facts, platform, listed),
            table_text(declaration, facts, False),
            make_plan(declaration, facts, False, "k3", symbols, inputs,
                      synthetic_descriptor())))
        rows = f"_ROWS {len(declared_rows(declaration, role))}U"
        cases.append((f"board {role}: targets on devices and in the "
                      f"firmware's place, its table's rows, M-mode's counts",
                      bool(made) and [made[0]["device"], made[0][
                          "firmware"]] + list(made[2]["counts"].values()) ==
                      want and rows in made[1], str(made and made[0])))
        cases += [(f"board {role} refused: {name}", ok, detail) for
                  name, ok, detail in board_mutations(declaration, facts,
                                                      platform, listed)]
        # T4-1: a jump's 4 bytes and a cache block's 64 across an end (the
        # firmware's place made to end 32 bytes into a block), each refused
        # where its first byte alone would be admitted.
        end = ranges(next(d for d in listed if d["kind"] == "console"))[0][1]
        top = number(platform["firmware"]["end_max"], "end_max")
        shifted = dict(platform, firmware=dict(platform["firmware"],
                                               end_max=hex(top + 32)))
        for name, at, want in (("I8", end - 2, "not wholly inside"),
                               ("H4", top, "real-time cores'"),
                               ("H5", top, "real-time cores'")):
            copied = json.loads(json.dumps(declaration))
            copied["effects"].setdefault(name, "a stand-in")
            next(row for row in copied["rows"] if row["row"] == name)[
                "at"] = hex(at)
            case(f"board {role} refused: {name}'s last bytes past an end",
                 lambda: board_rules(copied, facts, shifted, listed), want)
    real, qemu, path = load(BOARD_DECLARATIONS[1]), load(DECLARATION), \
        K3 / "platform.json"
    facts = Facts(layout, header, real["devices"], 1)
    candidate = {"image": "breach-g1", "change": "C.", "kept": 1,
                 "breach": {"domain": 1, "hart": 2},
                 "boundary": {"pair": "breach-g1", "record": True}}

    def expect(board="k3-breach-g1", file=BOARD_DECLARATIONS[1], **changes):
        return board_expectation(file, 1, dict(candidate, **changes), board)
    made = case("expect: the candidate's, five keys replaced", expect)
    board = dict(candidate, image="k3-breach-g1", where=["qemu", "board"],
                 toolchains=["gcc"], boundary={"pair": "breach-g1", "record":
                                               True, "counts": {"2": {
                                                   "pmp_faults": 73,
                                                   "blocked_calls": 33}}})
    cases.append(("expect: every other key the candidate's", bool(made) and
                  made == dict(board, change=made["change"]) and
                  "k3/breach/breach-g1.json" in made["change"], str(made)))
    for name, call, want in (
            ("expect: an image not named after the candidate's",
             lambda: expect("k3-breach-g0"), "is not the board's"),
            ("expect: QEMU's declaration", lambda: expect(file=DECLARATION),
             "is not the board's"),
            ("VS domain 1's declaration for VS domain 0", lambda:
             expected_counts(BOARD_DECLARATIONS[1], 0), "names VS domain 1"),
            ("devices of neither form", lambda: Facts(layout, header, dict(
                real["devices"], uart="0x0"), 1), "the devices are"),
            ("no --platform-file", lambda: board_input(real, facts, None),
             "takes --platform-file"),
            ("QEMU's declaration with one", lambda: board_input(qemu, Facts(
                layout, header, qemu["devices"], 1), path),
             "takes --platform-file"),
            ("an -off copy", lambda: board_input(real, facts, path, None,
                                                 True), "no -off copy"),
            ("a device list of another schema", lambda: board_input(
                real, facts, path, path), DEVICES_SCHEMA)):
        case(f"board refused: {name}", call, want)


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
             row_edit("C1", mode="satp"), "reached directly"),
            ("a cbo.zero off its cache block's first byte",
             row_edit("H4", at="own.control-mailbox+0x3f88"),
             "not the first byte of a 64-byte cache block"),
            ("a cbo.inval off its cache block's first byte",
             row_edit("H5", at="own.control-mailbox+0x3f48"),
             "not the first byte of a 64-byte cache block")):
        case(f"refused: {name}", edited(change), want)
    case("refused: a declared outcome the profile does not give",
         lambda: make_plan(declaration, facts[0], False, "breach-g0",
                           symbols, inputs, synthetic_descriptor(
                               {1: ((0x118002000, 0x1000, "r"),)})),
         "but the profile gives allowed")

    def split_window(hart, at):
        """The synthetic descriptor, HART's window two extents at AT."""
        descriptor = synthetic_descriptor()
        base, size = {1: (0x110000000, 0x4000000),
                      2: (0x114000000, 0x4000000)}[hart]
        name = f"x{hart}-{base:x}-{size:x}"
        halves = ((base, at - base), (at, base + size - at))
        descriptor["extents"] = [
            extent for extent in descriptor["extents"]
            if extent["name"] != name] + [
                {"name": f"x{hart}-half-{low:x}", "base": f"0x{low:x}",
                 "size": f"0x{length:x}"} for low, length in halves]
        profile = next(profile for profile in descriptor["profiles"]
                       if profile["hart"] == hart)
        profile["access"] = [
            access for access in profile["access"]
            if access["extent"] != name] + [
                {"extent": f"x{hart}-half-{low:x}",
                 "rights": ["read", "write", "execute"]}
                for low, _ in halves]
        return descriptor
    case("refused: an allowed row whose bytes span two extents that both "
         "give its right (W-1)",
         lambda: make_plan(declaration, facts[0], False, "breach-g0",
                           symbols, inputs,
                           split_window(1, g0["P1"]["at"] + 4)),
         "lie in more than one extent that gives read")
    case("refused: a boundary-on plan without its descriptor",
         lambda: make_plan(declaration, facts[0], False, "breach-g0",
                           symbols, inputs), "needs its descriptor")
    control_cases(case, cases, layout, header, symbols, inputs, scratch)
    board_cases(case, cases, layout, header, symbols, inputs)
    failed = [item for item in cases if not item[1]]
    for name, ok, detail in cases:
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")
    print(f"BE_MVP_BREACH_SELF_TEST: {'FAIL' if failed else 'PASS'} "
          f"cases={len(cases)}")
    return 1 if failed else 0


def hooked_role(text):
    """--domain's value: the hooked VS domain, 0 or 1, or CONTROL."""
    if text in ("0", "1"):
        return int(text)
    if text == CONTROL:
        return CONTROL
    raise argparse.ArgumentTypeError(f"{text!r} is not 0, 1, or {CONTROL}")


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch")
    commands = parser.add_subparsers(dest="command")
    for name in ("table", "plan", "counts", "board-check", "expect"):
        command = commands.add_parser(name)
        command.add_argument("--declaration", required=True)
        command.add_argument("--domain", type=hooked_role, required=True)
        if name == "expect":
            for option in ("--candidate", "--image", "--out"):
                command.add_argument(option, required=True)
        if name in ("counts", "expect"):
            continue
        command.add_argument("--layout", required=True)
        command.add_argument("--header", required=True)
        command.add_argument("--platform-file",
                             required=name == "board-check")
        if name == "board-check":
            command.add_argument("--devices")
            command.add_argument("--mutations", action="store_true")
            continue
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
            parser.error("a command, or --self-test")
        if args.command == "counts":
            print(json.dumps(expected_counts(args.declaration, args.domain),
                             sort_keys=True))
            return 0
        if args.command == "expect":
            out = board_expectation(args.declaration, args.domain, load(
                args.candidate, "be-mvp-expect-v3", "expectation"),
                args.image)
            write_new(args.out, json.dumps(out, indent=1, sort_keys=True) +
                      "\n")
            print(f"BE_MVP_BREACH_EXPECT: PASS image={args.image} "
                  f"counts={json.dumps(out['boundary']['counts'])}")
            return 0
        declaration = load(args.declaration)
        facts = Facts(defines(args.layout), defines(args.header),
                      declaration.get("devices", {}), args.domain)
        board = board_input(declaration, facts, args.platform_file,
                            getattr(args, "devices", None),
                            getattr(args, "discriminate", False))
        if args.command == "board-check":
            platform, listed, counts = board
            results = board_mutations(declaration, facts, platform,
                                      listed) if args.mutations else []
            for name, ok, detail in results:
                print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")
            failed = sum(not ok for _, ok, _ in results)
            print(f"BE_MVP_BREACH_BOARD: {'FAIL' if failed else 'PASS'} "
                  f"domain={args.domain} " + " ".join(
                      f"{key}={value}" for key, value in counts.items()) +
                  f" list={'devices' if args.devices else 'platform'} "
                  f"mutations={len(results)}")
            return 1 if failed else 0
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
