#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Write each image's post-link reference manifest (planning/mvp-m9-plan.md,
D-3; mvp/docs/log-profile.md, 5.3).

  gen-reference.py --toolchain T --build-root BUILD --out DIR
                   [--assume-r2 kept|dropped] [--check]
                   --image NAME:EXPECT:ELF:BOOT:KERNEL:DTB0:DTB1[:MUTATED] ...
  gen-reference.py --compare DIR DIR
  gen-reference.py --self-test

Purpose: for each image, after the link, DIR/NAME.json in the profile's
reference shape (be-mvp-log-reference-v1) and DIR/NAME.sha256, the pin
beside it in sha256sum's form (Q6): the source commit and tree state; the
image, scenario, variant, and toolchain; the run class (3.2) and whether R2
is kept; the authority report's, the monitor ELF's, and the boot image's
SHA-256, and self-report-flip's mutated image's; the measured range table
(each R2 range as a final loaded HPA range from the linker's symbols, its
offset in the boot image checked against the ELF's bytes, and its digest
from the boot image; each R4 object's placement from src/mvp-layout.h and
its digest from the build input, which must be the bytes the boot image
carries); the complete log the build defines, with every field of 2.3; the
registers by 2.6's recurrence; and each launched domain's expected launch
register. Two agreements then hold or the image's reference is refused:
the image's linked be_mvp_log_constants (src/mvp-log.h: the scenario,
configuration, and policy digests, the launch registers, the count, the
sequence, and R2's switch) are the reference's, and the expectation's log
section (tools/gen-scenario.py's apply_log(): its header, records, ranges,
registers, launch constants, terminal line, and lines with their slots)
is the one the reference implies, field by field
(tests/log_module.py's expectation_log()). --check writes nothing and
compares a fresh generation with DIR's files byte for byte. --compare
compares two directories of references (the host's and the evaluator's)
made from the same source commit and tree state; references of another
source state are reported stale and not compared, and a directory of
mixed provenance fails.
Inputs: EXPECT, the image's expectation (tools/gen-scenario.py); beside its
directory, the scenario header (mvp-scenario.h: its one BE_MVP_LOG_R2)
and, for a v2 or v3 image, the authority report the expectation names by
SHA-256; the scenario file (scenarios/<scenario>/scenario.json, the
expectation's scenario_sha256); each R4 object's source, which the
expectation's log.ranges names relative to BUILD; src/mvp-layout.h; and
tools/policy-check.py, whose core() gives the core identity from the
generator's canonical inputs. For self-report-flip, MUTATED and its
metadata beside it (self-report-flip.json, tools/flip-canary.py's): the
nominal and mutated boot images' SHA-256 and the bit flipped. Whether R2
is kept is the expectation's log.r2, which the header's switch and, when
given, --assume-r2 must agree with.
Trust: evidence TCB (security model v1, Revision 3, R3.4): it reads files
and executes nothing it reads but the policy tool at its fixed path; JSON
is read strictly (tests/log_module.py's strict_json()), and every
reference is read back by the profile's strict reader before it is
written. Determinism: no time and no absolute path; sorted keys; 5.1's
form; the build inputs named relative to BUILD.
Scope: the MVP's images; --self-test runs on a synthetic tree (a fake ELF
with the range symbols, a fake boot image, fake inputs) in memory, and
--compare's cases on scratch trees under build/mvp/tmp/reference-self-test,
removed after.
"""

import argparse
import contextlib
import hashlib
import importlib.util
import io
import pathlib
import re
import shutil
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
MVP_DIR = pathlib.Path(__file__).resolve().parents[1]
REPO = MVP_DIR.parent
LAYOUT_H = MVP_DIR / "src" / "mvp-layout.h"
POLICY_TOOL = MVP_DIR / "tools" / "policy-check.py"
GIT = "/usr/bin/git"
SELF_TEST_SCRATCH = REPO / "build" / "mvp" / "tmp" / "reference-self-test"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LOG = load(MVP_DIR / "tests" / "log_module.py", "mvp_log_module")
Refused, require, sha256 = LOG.Refused, LOG.require, LOG.sha256
# 2.7: each R2 range's linker symbols and its output section; the log's
# page; the canary. The profile names monitor-rodata's and mvp-rodata's
# symbols only as "the start and end symbols M9-3 adds": src/mvp-monitor.lds
# adds __be_monitor_rodata_start/_end and __be_mvp_rodata_start/_end.
R2_SYMBOLS = (
    ("monitor-text", "__be_monitor_code_start", "__be_monitor_code_end",
     ".monitor.text"),
    ("monitor-rodata", "__be_monitor_rodata_start", "__be_monitor_rodata_end",
     ".monitor.rodata"),
    ("monitor-input", "__be_input_start", "__be_input_end",
     ".monitor.input"),
    ("mvp-text", "__be_mvp_text_start", "__be_mvp_text_end", ".mvp.text"),
    ("mvp-rodata", "__be_mvp_rodata_start", "__be_mvp_rodata_end",
     ".mvp.rodata"))
LOG_SYMBOL, CANARY = "be_mvp_log", "be_mvp_log_canary"
# src/mvp-log.h's struct be_mvp_log_constants, which the image checker
# reads by these offsets: three digests, two launch registers, then three
# 32-bit values; and the sequence numbers it holds (3.1).
CONSTANTS, CONSTANTS_BYTES = "be_mvp_log_constants", 172
SEQUENCE_NUMBERS = {"v1": 1, "v2": 2, "v3": 3, "probe": 4}
FLIP_METADATA = "self-report-flip.json"
ZERO_DIGEST = "0" * 64
SHT_PROGBITS, SHT_SYMTAB, EM_RISCV = 1, 2, 243
HEADER_VALUE = re.compile(
    r"^#define\s+(BE_MVP_LOG_\w+)\s+BE_MVP_C\((0x[0-9a-fA-F]+|\d+)\)", re.M)


def layout_constants(text):
    return {name: int(value, 0) for name, value in re.findall(
        r"^#define\s+BE_MVP_(\w+)\s+BE_MVP_C\((0x[0-9a-fA-F]+|\d+)\)",
        text, re.M)}


# ------------------------------------------------------------------ ELF
class Elf:
    """A 64-bit little-endian RISC-V ELF's sections and symbols."""

    def __init__(self, data):
        self.data = data
        require(data[:4] == b"\x7fELF" and len(data) >= 64 and
                data[4] == 2 and data[5] == 1, "not a 64-bit little-endian "
                "ELF")
        require(struct.unpack_from("<H", data, 18)[0] == EM_RISCV,
                "not a RISC-V ELF")
        offset = struct.unpack_from("<Q", data, 40)[0]
        size, count, names = struct.unpack_from("<HHH", data, 58)
        require(size == 64 and names < count and
                offset + 64 * count <= len(data), "the section headers lie "
                "outside the ELF")
        rows = [struct.unpack_from("<IIQQQQIIQQ", data, offset + 64 * index)
                for index in range(count)]
        self.sections = {}
        for row in rows:
            name = self.string(rows[names][4], row[0])
            require(name not in self.sections or not name, f"two sections "
                    f"named {name}")
            self.sections[name] = row
        tables = [row for row in rows if row[1] == SHT_SYMTAB]
        require(len(tables) == 1, "not one symbol table")
        table, self.symbols = tables[0], {}
        require(table[6] < count and table[4] + table[5] <= len(data),
                "the symbol table lies outside the ELF")
        for at in range(table[4], table[4] + table[5], 24):
            name, _, _, _, value, _ = struct.unpack_from("<IBBHQQ", data, at)
            name = self.string(rows[table[6]][4], name)
            if name:
                self.symbols.setdefault(name, set()).add(value)

    def string(self, table, offset):
        end = self.data.find(b"\0", table + offset)
        require(end >= 0, "a name without its terminator")
        return self.data[table + offset:end].decode("ascii", "replace")

    def symbol(self, name):
        values = self.symbols.get(name)
        require(values is not None, f"the ELF has no symbol {name}")
        require(len(values) == 1, f"the ELF's symbol {name} has "
                f"{len(values)} values")
        return next(iter(values))

    def extent(self, name):
        row = self.sections.get(name)
        require(row is not None, f"the ELF has no section {name}")
        return row[3], row[3] + row[5]

    def read(self, address, length):
        """The file's bytes at [ADDRESS, ADDRESS + LENGTH), inside one
        PROGBITS section."""
        for row in self.sections.values():
            if row[1] == SHT_PROGBITS and row[3] <= address and \
                    address + length <= row[3] + row[5]:
                return self.data[row[4] + address - row[3]:
                                 row[4] + address - row[3] + length]
        raise Refused(f"0x{address:x}+0x{length:x} lies in no PROGBITS "
                      f"section of the ELF")


# ---------------------------------------------------------- one reference
class Build:
    """One image's inputs: NAME, the expectation, the scenario, the report,
    the header's text, the ELF, the boot image, the kernel and the device
    trees with their sources relative to the build root, the mutated
    image, the layout, the policy tool, the toolchain, and the source."""

    def __init__(self, **values):
        self.__dict__.update(values)


def log_constants(build):
    """The image's log constants as linked, be_mvp_log_constants in
    .mvp.rodata (src/mvp-log.h's layout): the scenario, configuration, and
    policy digests, each domain's expected launch register, the count, the
    sequence, and R2's switch."""
    data = build.elf.read(build.elf.symbol(CONSTANTS), CONSTANTS_BYTES)
    count, sequence, r2 = struct.unpack_from("<III", data, 160)
    return {"scenario": data[0:32].hex(), "configuration": data[32:64].hex(),
            "policy": data[64:96].hex(),
            "launch": [data[96:128].hex(), data[128:160].hex()],
            "count": count, "sequence": sequence, "r2": r2}


def r2_state(build, section, assume):
    """Whether R2 is kept: the expectation's log.r2, which the header's one
    BE_MVP_LOG_R2 and, when given, ASSUME must agree with."""
    # PROFILE READING (3.1, 5.3): the generator emits R2's switch as one
    # unconditional `#define BE_MVP_LOG_R2 BE_MVP_C(1)` (kept) or (0)
    # (dropped) in mvp-scenario.h and as the expectation's log.r2; the
    # image's own value is its linked constants' (log_constants()).
    states = {"the expectation's log.r2": section["r2"]}
    defined = [int(value, 0) for name, value in HEADER_VALUE.findall(
        build.header) if name == "BE_MVP_LOG_R2"]
    require(len(defined) == 1 and defined[0] in (0, 1), f"the header "
            f"defines BE_MVP_LOG_R2 {len(defined)} times, or not as 0 or 1; "
            f"the reference tool reads one unconditional value")
    states["the header's BE_MVP_LOG_R2"] = ("dropped", "kept")[defined[0]]
    if assume:
        states["--assume-r2"] = assume
    require(len(set(states.values())) == 1, f"R2 is {states}")
    return section["r2"]


def r2_ranges(build):
    """[(object, base, length)] from the linker's symbols, each range
    inside the flat monitor and its bytes the boot image's at its
    offset."""
    elf, layout = build.elf, build.layout
    out = []
    for name, start, end, _ in R2_SYMBOLS:
        base, top = elf.symbol(start), elf.symbol(end)
        # PROFILE READING (2.7): an empty range is refused here, a sanity
        # rule of this tool; the profile does not say a range may be empty.
        require(base < top, f"{name}'s range 0x{base:x}-0x{top:x} is empty")
        require(layout["MONITOR_HPA"] <= base and top <= layout[
            "MONITOR_HPA"] + layout["IMAGE_BYTES"], f"{name}'s range "
            f"0x{base:x}-0x{top:x} lies outside the flat monitor")
        offset = base - layout["MONITOR_HPA"] + layout["BOOT_MONITOR_OFFSET"]
        require(offset + top - base <= len(build.boot), f"{name}'s range "
                f"lies outside the boot image")
        require(elf.read(base, top - base) == build.boot[
            offset:offset + top - base], f"{name}'s bytes in the boot image "
            f"at 0x{offset:x} are not the ELF's")
        out.append((name, base, top - base))
    return out


def payload(build):
    """The staged kernel and the two device trees (the --image spec's
    files), each the bytes the boot image carries (the kernel at
    BE_MVP_BOOT_KERNEL_OFFSET, each device tree in its page after it, the
    image ending with the second)."""
    layout, boot = build.layout, build.boot
    at = layout["BOOT_KERNEL_OFFSET"]
    require(boot[at:at + len(build.kernel)] == build.kernel,
            f"{build.sources['kernel']} is not the kernel the boot image "
            f"carries")
    align = layout["PAYLOAD_ALIGN"]
    tree = (at + len(build.kernel) + align - 1) // align * align
    for domain, data in enumerate(build.trees):
        require(len(data) == layout["DTB_BYTES"] and boot[
            tree:tree + len(data)] == data, f"{build.sources[domain]} is "
            f"not domain {domain}'s device tree the boot image carries")
        tree += layout["DTB_BYTES"]
    require(tree == len(boot), "the boot image does not end with the "
            "second device tree")


def flipped_bit(build, ranges):
    """self-report-flip's mutated image: one bit unlike the nominal's,
    inside mvp-rodata's range and the canary's 16 bytes; (its address,
    the bit's place in the canary, its boot-image offset)."""
    nominal, mutated = build.boot, build.mutated
    require(len(mutated) == len(nominal), "the mutated image's length is "
            "not the nominal's")
    differ = [index for index, (one, two) in enumerate(zip(nominal, mutated))
              if one != two]
    require(len(differ) == 1 and bin(nominal[differ[0]] ^
                                     mutated[differ[0]]).count("1") == 1,
            "the mutated image does not differ from the nominal in one bit")
    layout = build.layout
    address = differ[0] - layout["BOOT_MONITOR_OFFSET"] + \
        layout["MONITOR_HPA"]
    _, base, length = next(item for item in ranges if item[0] == "mvp-rodata")
    require(base <= address < base + length, "the flipped bit lies outside "
            "mvp-rodata's range")
    canary = build.elf.symbol(CANARY)
    require(canary <= address < canary + 16, f"the flipped bit lies outside "
            f"{CANARY}")
    bit = (nominal[differ[0]] ^ mutated[differ[0]]).bit_length() - 1
    return address, 8 * (address - canary) + bit, differ[0]


def flip_metadata(build, section, ranges):
    """self-report-flip's metadata (tools/flip-canary.py's, beside the
    mutated image): the nominal and the mutated boot image's SHA-256 these,
    its symbol and bit the expectation's log.mutate and the one bit
    flipped_bit() finds, at its byte's offset."""
    meta = build.flip
    require(meta is not None, f"no {FLIP_METADATA} beside the mutated "
            f"image")
    LOG.shape(meta, ("address", "bit", "byte_offsets", "bytes", "files",
                     "mutated_image_sha256", "nominal_image_sha256",
                     "symbol", "variant"), FLIP_METADATA)
    nominal, mutated = sha256(build.boot), sha256(build.mutated)
    require(meta["variant"] == "self-report-flip" and
            meta["nominal_image_sha256"] == nominal and
            meta["mutated_image_sha256"] == mutated and
            meta["files"].get("be-mvp-boot.img") == {
                "mutated_sha256": mutated, "nominal_sha256": nominal},
            f"{FLIP_METADATA} does not name these nominal and mutated boot "
            f"images")
    address, bit, offset = flipped_bit(build, ranges)
    mutate = section["mutate"]
    require(meta["symbol"] == mutate["symbol"] == CANARY and
            meta["bit"] == mutate["bit"] == bit and meta["bytes"] == 16 and
            meta["address"] == f"0x{build.elf.symbol(CANARY):x}" and
            meta["byte_offsets"].get("be-mvp-boot.img") == f"0x{offset:x}",
            f"{FLIP_METADATA} and log.mutate do not name the bit flipped at "
            f"0x{address:x}, bit {bit} of {CANARY}")


def r4_values(build, section, run, notes):
    """The R4 objects the expectation's log.ranges names, each placed by
    the layout, its digest recomputed from its source under the build root
    (or from the scenario's secret, zero-padded), and each kernel and
    device tree the bytes the boot image stages: ({(object, domain): (base,
    length, digest)}, {(object, domain): source})."""
    # PROFILE READING (2.7, 5.3): the reference's R4 objects are the build
    # inputs the generator measured, the files the expectation's log.ranges
    # names; the boot image must stage exactly those bytes, so that a
    # reference names no input its image does not carry, but in a
    # pre-measurement run, whose image (payload's, with its own kernel) is
    # refused before anything is measured: the difference is noted.
    layout, values, sources, differ = build.layout, {}, {}, []
    staged = {("kernel-image", 0): build.kernel,
              ("kernel-image", 1): build.kernel,
              ("device-tree", 0): build.trees[0],
              ("device-tree", 1): build.trees[1]}
    for index, entry in enumerate(section["ranges"]):
        if not isinstance(entry, dict) or entry.get("domain") is None:
            continue
        where = f"log.ranges[{index}]"
        name, domain = entry.get("object"), entry.get("domain")
        require(name in ("kernel-image", "device-tree", "secret-page") and
                domain in (0, 1), f"{where} names no domain's R4 object")
        source = LOG.source_form(entry.get("source"), name, where)
        if name == "secret-page":
            secret = bytes.fromhex(build.scenario["secret"]["hex"])
            require(secret.hex() == build.expect.get("secret_hex"),
                    "the scenario's secret is not the expectation's")
            page = next(item for item in build.expect["pages"]
                        if item["kind"] == "secret")
            base, data = int(page["hpa"], 16), secret.ljust(
                int(page["bytes"], 16), b"\0")
        else:
            data = build.read(source)
            base = layout[f"G{domain}_HPA"] - layout["GUEST_GPA"] + layout[
                "KERNEL_GPA" if name == "kernel-image" else "DTB_GPA"]
            if data != staged[name, domain]:
                require(run == "pre-measurement", f"{source} is not the "
                        f"{name} the boot image stages for domain {domain}")
                differ.append(f"{name}:{domain}")
        require(entry.get("base") == LOG.hex64(base) and
                entry.get("length") == LOG.hex64(len(data)) and
                entry.get("digest") == sha256(data), f"{where} ({source}) "
                f"is not its placement, length, and digest recomputed")
        values[name, domain] = (base, len(data), sha256(data))
        sources[name, domain] = source
    if differ:
        notes.append("staged=differs:" + ",".join(differ))
    return values, sources


def reference(build, assume=None):
    """The reference value of BUILD's image, read back by the profile's
    strict reader, its linked log constants and the generator's log section
    its own; (value, notes)."""
    expect, layout = build.expect, build.layout
    require(expect.get("image") == build.name, f"the expectation is "
            f"{expect.get('image')}'s, not {build.name}'s")
    require(sha256(build.scenario_bytes) == expect.get("scenario_sha256"),
            "the scenario file is not the expectation's scenario_sha256")
    section = LOG.log_section(expect)
    sequence, run = LOG.contract_of(expect)
    r2 = r2_state(build, section, assume)
    rows = LOG.sequence_of(sequence, r2)
    policy = sequence in ("v2", "v3")
    report = build.report
    require((report is not None) == policy, "an authority report exactly "
            "for a v2 or v3 image")
    if policy:
        require(sha256(build.report_bytes) == expect["report"]["sha256"],
                "the authority report is not the expectation's")
    ranges = r2_ranges(build) if r2 == "kept" else []
    log_values = {"scenario": expect["scenario_sha256"]}
    for name, base, length in ranges:
        offset = base - layout["MONITOR_HPA"] + layout["BOOT_MONITOR_OFFSET"]
        log_values[name, None] = (base, length, sha256(
            build.boot[offset:offset + length]))
    core = LOG.core_identity(expect, build.scenario, layout, build.policy)
    sealed = [re.search(r" identity=([0-9a-f]{16})$", entry["template"])
              for entry in expect.get("control_lines", [])
              if entry["template"].startswith("BE_MVP:00 CONFIG_SEALED ")]
    require(all(match and match.group(1) == core[:16] for match in sealed),
            "the core identity is not the one CONFIG_SEALED's expected line "
            "prints")
    grants = LOG.console_grants(expect, build.scenario)
    log_values["core-identity", None] = core
    log_values["console-grants", None] = sha256(bytes(grants))
    notes = [f"core={core[:16]}", "grants=" + "".join(
        "1" if grant else "0" for grant in grants)]
    if policy:
        identity = report["identity"]
        configured = report.get("configuration", {})
        named = [item for item in configured.get("variants", [])
                 if item.get("image") == build.name]
        facts = named[0]["console_input"] if named else \
            configured.get("console_input", [])
        require([fact.get("console_input") for fact in facts] == grants,
                "the report's console input facts are not the grants")
        require(identity.get("core_identity") == core or
                expect["image"] != expect["scenario"], "the report's core "
                "identity is not the canonical one")
        for name, key in (("configuration-identity",
                           "configuration_identity"),
                          ("policy-identity", "policy_identity")):
            log_values[name, None] = identity[key]
    sources = {}
    if sequence != "probe":
        payload(build)
        values, sources = r4_values(build, section, run, notes)
        log_values.update(values)
    flip = run == "self-report-flip"
    require((build.mutated is not None) == flip, "a mutated image exactly "
            "for self-report-flip")
    if flip:
        require(r2 == "kept", "self-report-flip needs R2 kept")
        flip_metadata(build, section, ranges)
    probe = bool(expect.get("outcome", {}).get("probe"))
    # PROFILE READING (3.2, Q16): a gate-fail image's failing domain, whose
    # expected launch register is the nominal one with bit 0 of its first
    # byte flipped, is the expectation's outcome.domain.
    failing = expect.get("outcome", {}).get("domain") \
        if run == "gate-fail" else None
    meta = {"source": build.source, "image": build.name,
            "scenario": expect["scenario"], "variant": None if build.name ==
            expect["scenario"] or probe else build.name,
            "toolchain": build.toolchain,
            "authority_report_sha256": sha256(build.report_bytes)
            if policy else None,
            "elf_sha256": sha256(build.elf.data),
            "boot_image_sha256": sha256(build.boot),
            "mutated_image_sha256": sha256(build.mutated) if flip else None}
    value = LOG.build_reference(meta, sequence, run, r2, log_values,
                                sources, failing)
    # The image's linked constants (src/mvp-log.h), which hart 0 reads and
    # the gate compares with: the reference's own.
    zero, linked = LOG.ZERO, log_constants(build)
    want = {"scenario": expect["scenario_sha256"],
            "configuration": log_values.get(("configuration-identity",
                                              None), zero),
            "policy": log_values.get(("policy-identity", None), zero),
            "launch": value["launch_expected"] or [zero, zero],
            "count": len(rows), "sequence": SEQUENCE_NUMBERS[sequence],
            "r2": int(r2 == "kept")}
    differ = sorted(key for key in want if linked[key] != want[key])
    require(not differ, f"the image's linked {CONSTANTS} differ from the "
            f"reference's in {', '.join(differ)}")
    # The generator's log section, every field, the reference's.
    found = LOG.differences(LOG.expectation_log(
        LOG.Reference(LOG.render(value)), LOG.log_harts(expect),
        bool((expect.get("outcome") or {}).get("fallback")),
        section.get("mutate")), section, "log")
    require(not found, "the expectation's log section is not the "
            "reference's: " + "; ".join(found))
    notes = [f"{sequence}/{run}", f"r2={r2}", f"records={len(rows)}"] + \
        notes + ["ranges=symbols" if r2 == "kept" else "ranges=none",
                 "constants=linked", "expectation=same"]
    return value, notes


# ------------------------------------------------------------ the inputs
def source_state(repo=REPO):
    """The source commit and tree state, as tools/evidence.py gives them."""
    env = {"PATH": "/usr/bin", "LC_ALL": "C", "LANG": "C",
           "GIT_OPTIONAL_LOCKS": "0"}
    commit = subprocess.run([GIT, "-C", str(repo), "rev-parse", "HEAD"],
                            capture_output=True, text=True, env=env,
                            check=True).stdout.strip()
    changes = subprocess.run([GIT, "-C", str(repo), "status",
                              "--porcelain=v1"], capture_output=True,
                             text=True, env=env, check=True).stdout
    changed = len([line for line in changes.splitlines() if line])
    return {"commit": commit, "tree_state": "clean" if changed == 0 else
            f"dirty changed={changed}"}


def relative(path, root, what):
    path, root = pathlib.Path(path).resolve(), pathlib.Path(root).resolve()
    require(path.is_relative_to(root), f"{what} {path} lies outside the "
            f"build root {root}")
    return str(path.relative_to(root))


def read_build(spec, root, toolchain, source, layout, policy):
    """A Build from NAME:EXPECT:ELF:BOOT:KERNEL:DTB0:DTB1[:MUTATED]."""
    parts = spec.split(":")
    require(len(parts) in (7, 8), f"--image {spec[:80]!r} is not NAME:"
            f"EXPECT:ELF:BOOT:KERNEL:DTB0:DTB1[:MUTATED]")
    name, expect_path, elf, boot, kernel, tree0, tree1 = parts[:7]
    require(LOG.NAME_FORM.fullmatch(name), f"the image name {name!r}")
    expect_path = pathlib.Path(expect_path)
    expect = LOG.strict_json(expect_path.read_bytes(), f"{name}'s "
                             f"expectation", limit=4 << 20, floats=True)
    scenario_path = MVP_DIR / "scenarios" / str(
        expect.get("scenario")) / "scenario.json"
    scenario_bytes = scenario_path.read_bytes()
    report_path = expect_path.parent.parent / "authority-report.json"
    report_bytes = report_path.read_bytes() if "report" in expect else None
    header = expect_path.parent.parent / "mvp-scenario.h"
    return Build(
        name=name, expect=expect, scenario_bytes=scenario_bytes,
        scenario=LOG.strict_json(scenario_bytes, "the scenario",
                                 limit=1 << 20, floats=True),
        report_bytes=report_bytes, report=None if report_bytes is None else
        LOG.strict_json(report_bytes, "the authority report",
                        limit=4 << 20, floats=True),
        header=header.read_text(encoding="utf-8"),
        elf=Elf(pathlib.Path(elf).read_bytes()),
        boot=pathlib.Path(boot).read_bytes(),
        kernel=pathlib.Path(kernel).read_bytes(),
        trees=[pathlib.Path(tree0).read_bytes(),
               pathlib.Path(tree1).read_bytes()],
        sources={"kernel": relative(kernel, root, "the kernel"),
                 0: relative(tree0, root, "DTB0"),
                 1: relative(tree1, root, "DTB1")},
        mutated=pathlib.Path(parts[7]).read_bytes() if len(parts) == 8
        else None, flip=LOG.strict_json(
            (pathlib.Path(parts[7]).parent / FLIP_METADATA).read_bytes(),
            FLIP_METADATA) if len(parts) == 8 else None,
        read=LOG.read_build(root), layout=layout, policy=policy,
        toolchain=toolchain, source=source)


def generate(args):
    """Every --image's reference: written, or compared (--check)."""
    out = pathlib.Path(args.out)
    layout = layout_constants(LAYOUT_H.read_text(encoding="utf-8"))
    policy, source = LOG.policy_tool(POLICY_TOOL), source_state()
    failed, done = 0, set()
    for spec in args.image:
        name = spec.split(":", 1)[0]
        try:
            require(name not in done, f"--image {name} given twice")
            done.add(name)
            build = read_build(spec, args.build_root, args.toolchain,
                               source, layout, policy)
            value, notes = reference(build, args.assume_r2)
            data = LOG.render(value)
            pin = f"{sha256(data)}  {name}.json\n".encode("ascii")
            path, pinned = out / f"{name}.json", out / f"{name}.sha256"
            if args.check:
                same = path.is_file() and path.read_bytes() == data and \
                    pinned.is_file() and pinned.read_bytes() == pin
                require(same, f"{path} or its pin is not the build's")
                verdict = "SAME"
            else:
                out.mkdir(parents=True, exist_ok=True)
                for target, content in ((path, data), (pinned, pin)):
                    scratch = target.with_name(target.name + ".new")
                    scratch.unlink(missing_ok=True)
                    with open(scratch, "xb") as handle:
                        handle.write(content)
                    scratch.replace(target)
                verdict = "PASS"
            print(f"BE_MVP_LOG_REFERENCE[{args.toolchain}/{name}]: {verdict} "
                  f"sha256={sha256(data)[:16]} " + " ".join(notes))
        except (Refused, OSError, KeyError, TypeError, ValueError,
                StopIteration) as error:
            failed += 1
            print(f"BE_MVP_LOG_REFERENCE[{args.toolchain}/{name}]: FAIL "
                  f"{type(error).__name__}: {error}")
    print(f"BE_MVP_LOG_REFERENCES: {'PASS' if not failed else 'FAIL'} "
          f"toolchain={args.toolchain} images={len(args.image)} "
          f"failed={failed}{' check' if args.check else ''}")
    return 1 if failed else 0


def provenance(root):
    """The source states ("COMMIT TREE_STATE", sorted, each once) that the
    references under ROOT name: each JSON file read strictly, its source
    object taken when it has the reference's form (5.3). A file that is
    not JSON, or names no source, names none and is only compared."""
    found = set()
    for path in root.rglob("*.json"):
        if not path.is_file():
            continue
        try:
            value = LOG.strict_json(path.read_bytes(), "a reference")
            require(isinstance(value, dict), "not an object")
            source = LOG.shape(value.get("source"), ("commit", "tree_state"),
                               "its source")
            found.add(LOG.form(source["commit"], LOG.COMMIT_FORM, "commit") +
                      " " + LOG.form(source["tree_state"], LOG.TREE_FORM,
                                     "tree_state"))
        except Refused:
            continue
    return sorted(found)


def compare(first, second):
    """Two directories of references, file for file and byte for byte,
    each file named by its path relative to its directory (TOOLCHAIN/
    IMAGE.json and its pin, as BUILD/references holds them), never by its
    name alone; files= counts the paths either directory holds, and a path
    one of them lacks differs. Only references of one source state are
    comparable, each naming its own (provenance()): a directory whose
    references name more than one fails; two that name one each, not the
    same, are stale and not compared; a directory naming none is compared."""
    roots = [pathlib.Path(directory) for directory in (first, second)]
    states = [provenance(root) for root in roots]
    mixed = [f"under the {side} directory: {', '.join(state)}"
             for side, state in zip(("first", "second"), states)
             if len(state) > 1]
    if mixed:
        print("BE_MVP_LOG_REFERENCE_COMPARE: FAIL mixed provenance " +
              "; ".join(mixed))
        return 1
    if all(states) and states[0] != states[1]:
        print(f"BE_MVP_LOG_REFERENCE_COMPARE: stale (the second directory's "
              f"references are of {states[1][0]}; the first directory's of "
              f"{states[0][0]}; not compared)")
        return 0
    one, two = ({path.relative_to(root).as_posix() for path in root.rglob(
        "*") if path.is_file()} for root in roots)
    names = sorted(one | two)
    differ = [name for name in names
              if name not in one or name not in two or
              (roots[0] / name).read_bytes() !=
              (roots[1] / name).read_bytes()]
    for name in differ:
        print(f"differs {name}")
    print(f"BE_MVP_LOG_REFERENCE_COMPARE: {'PASS' if not differ else 'FAIL'} "
          f"files={len(names)} differ={len(differ)}")
    return 1 if differ else 0


# ------------------------------------------------------------- self-test
def fake_elf(sections, symbols):
    """A minimal RISC-V ELF64: SECTIONS [(name, address, bytes)] as
    PROGBITS, then .symtab, .strtab, and .shstrtab; SYMBOLS {name:
    value}."""
    strtab = b"\0" + b"".join(name.encode() + b"\0" for name in symbols)
    entries, at = bytearray(24), 1
    for name, value in symbols.items():
        entries += struct.pack("<IBBHQQ", at, 0x10, 0, 1, value, 0)
        at += len(name) + 1
    names = [""] + [name for name, _, _ in sections] + [
        ".symtab", ".strtab", ".shstrtab"]
    shstrtab = b"\0".join(name.encode() for name in names) + b"\0"
    body, offsets = bytearray(64), []
    for _, _, data in sections:
        offsets.append(len(body))
        body += data
    tables = []
    for data in (bytes(entries), strtab, shstrtab):
        tables.append(len(body))
        body += data
    shoff = len(body)
    headers = bytearray(64)

    def name_at(name):
        return shstrtab.index(name.encode() + b"\0") if name else 0
    for (name, address, data), offset in zip(sections, offsets):
        headers += struct.pack("<IIQQQQIIQQ", name_at(name), SHT_PROGBITS,
                               2, address, offset, len(data), 0, 0, 16, 0)
    count = len(sections) + 1
    headers += struct.pack("<IIQQQQIIQQ", name_at(".symtab"), SHT_SYMTAB, 0,
                           0, tables[0], len(entries), count + 1, 1, 8, 24)
    for name, offset, data in ((".strtab", tables[1], strtab),
                               (".shstrtab", tables[2], shstrtab)):
        headers += struct.pack("<IIQQQQIIQQ", name_at(name), 3, 0, 0,
                               offset, len(data), 0, 0, 1, 0)
    head = bytearray(b"\x7fELF\x02\x01\x01" + bytes(9))
    head += struct.pack("<HHIQQQIHHHHHH", 2, EM_RISCV, 1, 0x102000000, 0,
                        shoff, 0, 64, 56, 0, 64, count + 3, count + 2)
    body[:64] = head
    return bytes(body + headers)


class FakePolicy:
    """The policy tool's three functions, the core identity a constant."""

    @staticmethod
    def manifest(scenario):
        return scenario

    @staticmethod
    def core_inputs(scenario, sealed):
        return [], []

    @staticmethod
    def core(domains, pages, layout):
        return {"identity": sha256(b"self-test core identity")}


def chain(*digests):
    """2.6's recurrence over DIGESTS from 32 zero bytes."""
    value = bytes(32)
    for item in digests:
        value = hashlib.sha256(value + bytes.fromhex(item)).digest()
    return value.hex()


SELF_HEADER = ("#define BE_MVP_LOG_R2\t\t\tBE_MVP_C(1)\n"
               "#if defined(BE_MVP_PROBE_IMAGE)\n"
               "#define BE_MVP_LOG_EXPECTED_COUNT\tBE_MVP_C(9)\n#else\n"
               "#define BE_MVP_LOG_EXPECTED_COUNT\tBE_MVP_C(14)\n#endif\n")


def self_build(image="te-poc", run="complete", constants=None,
               staged_kernel=None, flip_bits=(0,), section=None, **changes):
    """A synthetic te-poc build of IMAGE in RUN's class, CHANGES applied:
    its sections at 5.4-like addresses, the canary and the linked log
    constants (CONSTANTS over the true ones) in mvp-rodata, the payload
    after the flat monitor (STAGED_KERNEL in the kernel's place), the
    canonical data, and the expectation the generator would write, its
    log section from this self-test's own reference (expectation_log(),
    SECTION applied); for self-report-flip, the boot image with
    FLIP_BITS of the canary flipped and the variant's metadata."""
    layout = layout_constants(LAYOUT_H.read_text(encoding="utf-8"))
    kernel = hashlib.shake_256(b"kernel").digest(0x2345)
    trees = [hashlib.shake_256(b"tree %d" % domain).digest(0x1000)
             for domain in (0, 1)]
    scenario = b'{"domains": [{"console_input": false}, ' \
        b'{"console_input": false}]}'
    identity = {"configuration_identity": sha256(b"configuration"),
                "policy_identity": sha256(b"policy"),
                "core_identity": FakePolicy.core(0, 0, 0)["identity"]}
    report = {"identity": identity, "configuration": {"console_input": [
        {"console_input": False}, {"console_input": False}]}}
    report_bytes = LOG.render(report)
    failing = 1 if run == "gate-fail" else None
    nominal = [chain(sha256(kernel), sha256(tree)) for tree in trees]
    launch = [LOG.flip(value) if domain == failing else value
              for domain, value in enumerate(nominal)]
    linked = dict({"scenario": sha256(scenario),
                   "configuration": identity["configuration_identity"],
                   "policy": identity["policy_identity"], "launch": launch,
                   "count": 14, "sequence": 2, "r2": 1},
                  **(constants or {}))
    rodata = bytearray(hashlib.shake_256(b".mvp.rodata").digest(0x200))
    rodata[0x40:0x40 + CONSTANTS_BYTES] = b"".join(
        bytes.fromhex(item) for item in (
            linked["scenario"], linked["configuration"], linked["policy"],
            *linked["launch"])) + struct.pack(
        "<III", linked["count"], linked["sequence"], linked["r2"])
    sections = [(name, address, hashlib.shake_256(name.encode()).digest(
        length)) for name, address, length in (
        (".monitor.text", 0x102000000, 0x200),
        (".monitor.input", 0x102008000, 0x100),
        (".monitor.rodata", 0x102008100, 0x80),
        (".mvp.text", 0x102064000, 0x300))] + [
        (".mvp.rodata", 0x102064300, bytes(rodata))]
    symbols = {"__be_monitor_code_start": 0x102000000,
               "__be_monitor_code_end": 0x102000200,
               "__be_input_start": 0x102008000,
               "__be_input_end": 0x102008100,
               "__be_monitor_rodata_start": 0x102008100,
               "__be_monitor_rodata_end": 0x102008180,
               "__be_mvp_text_start": 0x102064000,
               "__be_mvp_text_end": 0x102064300,
               "__be_mvp_rodata_start": 0x102064300,
               "__be_mvp_rodata_end": 0x102064500,
               LOG_SYMBOL: 0x102065000, CANARY: 0x102064310,
               CONSTANTS: 0x102064340}
    symbols.update(changes.pop("symbols", {}))
    for name in changes.pop("drop", ()):
        symbols.pop(name)
    flat = bytearray(layout["IMAGE_BYTES"])
    for _, address, data in sections:
        at = address - layout["MONITOR_HPA"]
        flat[at:at + len(data)] = data
    staged = staged_kernel or kernel
    boot = bytes(layout["BOOT_MONITOR_OFFSET"]) + bytes(flat)
    boot += bytes(layout["BOOT_KERNEL_OFFSET"] - len(boot)) + staged
    boot += bytes(-len(boot) % layout["PAYLOAD_ALIGN"]) + b"".join(trees)
    elf = Elf(fake_elf(sections, symbols))
    files = {"guest/Image": kernel, "guest/mvp-guest-g0-te-poc.dtb": trees[0],
             "guest/mvp-guest-g1-te-poc.dtb": trees[1]}
    source = {"commit": "c" * 40, "tree_state": "clean"}
    outcome = {"complete": {"pass": True}, "self-report-flip": {"pass": True},
               "gate-fail": {"fail": "measurement", "after": "BE_MVP:19",
                             "domain": 1, "hart": 2},
               "pre-measurement": {"fail": "payload", "after": "BE_MVP:03"},
               "post-launch-failure": {"fail": "exit-budget",
                                       "after": "BE_MVP:10"}}[run]
    expect = {"image": image, "scenario": "te-poc",
              "schema": "be-mvp-expect-v2", "outcome": outcome,
              "scenario_sha256": sha256(scenario),
              "report": {"sha256": sha256(report_bytes)},
              "domains": [{"index": 0, "hart": 1}, {"index": 1, "hart": 2}]}
    # The self-test's own reference: every value computed here again.
    values = {"scenario": sha256(scenario),
              ("core-identity", None): identity["core_identity"],
              ("console-grants", None): sha256(b"\0\0"),
              ("configuration-identity", None):
              identity["configuration_identity"],
              ("policy-identity", None): identity["policy_identity"]}
    for name, start, end, _ in R2_SYMBOLS:
        if start in symbols and end in symbols:
            base, top = symbols[start], symbols[end]
            at = base - 0x102000000 + 0x1000
            values[name, None] = (base, top - base, sha256(boot[at:top -
                                                                0x102000000 +
                                                                0x1000]))
    sources = {}
    for domain in (0, 1):
        window = layout[f"G{domain}_HPA"] - layout["GUEST_GPA"]
        values["kernel-image", domain] = (window + layout["KERNEL_GPA"],
                                          len(kernel), sha256(kernel))
        values["device-tree", domain] = (window + layout["DTB_GPA"],
                                         0x1000, sha256(trees[domain]))
        sources["kernel-image", domain] = "guest/Image"
        sources["device-tree", domain] = \
            f"guest/mvp-guest-g{domain}-te-poc.dtb"
    mutated = flip = None
    mutate = {"bit": flip_bits[0], "symbol": CANARY}
    if run == "self-report-flip":
        mutated = bytearray(boot)
        for bit in flip_bits:
            mutated[0x1000 + 0x64310 + bit // 8] ^= 1 << (bit % 8)
        mutated = bytes(mutated)
        flip = {"address": "0x102064310", "bit": flip_bits[0],
                "byte_offsets": {"be-mvp-boot.img":
                                 f"0x{0x1000 + 0x64310 + flip_bits[0] // 8:x}"},
                "bytes": 16, "files": {"be-mvp-boot.img": {
                    "mutated_sha256": sha256(mutated),
                    "nominal_sha256": sha256(boot)}},
                "mutated_image_sha256": sha256(mutated),
                "nominal_image_sha256": sha256(boot), "symbol": CANARY,
                "variant": "self-report-flip"}
    try:
        own = LOG.build_reference(
            {"source": source, "image": image, "scenario": "te-poc",
             "variant": None if image == "te-poc" else image,
             "toolchain": "gcc",
             "authority_report_sha256": sha256(report_bytes),
             "elf_sha256": sha256(elf.data), "boot_image_sha256": sha256(boot),
             "mutated_image_sha256": mutated and sha256(mutated)},
            "v2", run, "kept", values, sources, failing)
        expect["log"] = LOG.expectation_log(
            LOG.Reference(LOG.render(own)), [1, 2], False,
            mutate if run == "self-report-flip" else None)
    except (Refused, KeyError):
        own = None
        expect["log"] = LOG.expectation_log(
            LOG.Reference(LOG.render(self_build(image, run).own)), [1, 2],
            False, mutate if run == "self-report-flip" else None)
    if section:
        section(expect["log"])

    def read(name):
        require(name in files, f"no build input {name}")
        return files[name]
    values = dict(
        name=image, expect=expect, scenario_bytes=scenario,
        scenario=LOG.strict_json(scenario, "s"), report_bytes=report_bytes,
        report=report, header=SELF_HEADER, elf=elf, boot=boot,
        kernel=staged, trees=trees, mutated=mutated, flip=flip, read=read,
        sources={"kernel": "guest/Image",
                 0: "guest/mvp-guest-g0-te-poc.dtb",
                 1: "guest/mvp-guest-g1-te-poc.dtb"},
        layout=layout, policy=FakePolicy(), toolchain="gcc", source=source,
        own=own)
    values.update(changes)
    return Build(**values)


def compare_cases(scratch):
    """compare() on two trees per case under SCRATCH, in BUILD/references'
    layout (TOOLCHAIN/IMAGE.json): one name under both toolchains, the
    trees equal; one of the two differing; a file on one side only, either
    side; then references naming their source: of another commit, and of
    the same commit in another tree state, stale; of one source, differing;
    two sources in one directory, and in each; a .json file not JSON; and
    a source on one side only. Each case's exit status and lines, exactly."""
    gcc, clang = b'{"toolchain": "gcc"}\n', b'{"toolchain": "clang"}\n'
    both = {"gcc/a.json": gcc, "clang/a.json": clang}

    def ref(toolchain, commit, tree="clean"):
        return LOG.render({"source": {"commit": commit * 40,
                                      "tree_state": tree},
                           "toolchain": toolchain})

    def refs(commit, tree="clean"):
        return {f"{toolchain}/a.json": ref(toolchain, commit, tree)
                for toolchain in ("gcc", "clang")}
    a, b, c = "a" * 40, "b" * 40, "c" * 40
    verdict = "BE_MVP_LOG_REFERENCE_COMPARE:"
    cases = (
        ("same-name", "--compare: one name under gcc/ and clang/, the trees "
         "equal", both, both, 0,
         ["BE_MVP_LOG_REFERENCE_COMPARE: PASS files=2 differ=0"]),
        ("differs", "--compare: gcc/a.json differs, named by its path",
         both, {**both, "gcc/a.json": clang}, 1,
         ["differs gcc/a.json",
          "BE_MVP_LOG_REFERENCE_COMPARE: FAIL files=2 differ=1"]),
        ("one-side", "--compare: a file on one side only, either side",
         {**both, "clang/b.json": clang}, {**both, "gcc/b.sha256": gcc}, 1,
         ["differs clang/b.json", "differs gcc/b.sha256",
          "BE_MVP_LOG_REFERENCE_COMPARE: FAIL files=4 differ=2"]),
        ("stale-commit", "--compare: references of another commit, stale "
         "and not compared", refs("a"), refs("b"), 0,
         [f"{verdict} stale (the second directory's references are of {b} "
          f"clean; the first directory's of {a} clean; not compared)"]),
        ("stale-tree", "--compare: the same commit in another tree state, "
         "stale and not compared", refs("a"), refs("a", "dirty changed=1"),
         0, [f"{verdict} stale (the second directory's references are of "
             f"{a} dirty changed=1; the first directory's of {a} clean; "
             f"not compared)"]),
        ("same-source-differs", "--compare: one source on both sides, a "
         "difference in another field found", refs("a"),
         {**refs("a"), "gcc/a.json": ref("clang", "a")}, 1,
         ["differs gcc/a.json", f"{verdict} FAIL files=2 differ=1"]),
        ("mixed", "--compare: two sources under one directory fail",
         refs("a"), {**refs("a"), "clang/a.json": ref("clang", "b")}, 1,
         [f"{verdict} FAIL mixed provenance under the second directory: "
          f"{a} clean, {b} clean"]),
        ("both-mixed", "--compare: two sources under each directory, both "
         "named", {**refs("b"), "gcc/a.json": ref("gcc", "a")},
         {**refs("c"), "clang/a.json": ref("clang", "b", "dirty changed=2")},
         1, [f"{verdict} FAIL mixed provenance under the first directory: "
             f"{a} clean, {b} clean; under the second directory: {b} dirty "
             f"changed=2, {c} clean"]),
        ("not-json", "--compare: a .json file not JSON names no source and "
         "is compared", refs("a"),
         {**refs("a"), "gcc/a.json": ref("gcc", "a")[:24]}, 1,
         ["differs gcc/a.json", f"{verdict} FAIL files=2 differ=1"]),
        ("one-source", "--compare: a source on one side only, the trees "
         "compared", refs("a"), both, 1,
         ["differs clang/a.json", "differs gcc/a.json",
          f"{verdict} FAIL files=2 differ=2"]))
    results = []
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        scratch.mkdir(parents=True, mode=0o700)
    except OSError as error:
        return [(name, False, f"the scratch tree: {error}")
                for _, name, _, _, _, _ in cases]
    try:
        for key, name, first, second, status, lines in cases:
            roots = [scratch / key / side for side in ("first", "second")]
            output = io.StringIO()
            try:
                for root, files in zip(roots, (first, second)):
                    for relative, data in files.items():
                        (root / relative).parent.mkdir(parents=True,
                                                       exist_ok=True)
                        with open(root / relative, "xb") as handle:
                            handle.write(data)
                with contextlib.redirect_stdout(output):
                    got = compare(*roots)
            except (OSError, ValueError, Refused) as error:
                results.append((name, False,
                                f"{type(error).__name__}: {error}"))
                continue
            results.append((name, got == status and
                            output.getvalue().splitlines() == lines,
                            f"exit {got}: {output.getvalue()!r}"))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return results


def self_test():
    """The fields of a synthetic build's reference, each computed here
    again; the generator's log section and the linked constants its own;
    two generations byte for byte; each refusal for its own reason; and
    --compare on scratch trees (compare_cases())."""
    results = []
    build = self_build()
    value, notes = reference(build)
    data = LOG.render(value)
    boot, layout = build.boot, build.layout

    def at(address, length):
        offset = address - layout["MONITOR_HPA"] + layout[
            "BOOT_MONITOR_OFFSET"]
        return sha256(boot[offset:offset + length])
    wanted = {
        "monitor-text": (0x102000000, 0x200), "monitor-rodata":
        (0x102008100, 0x80), "monitor-input": (0x102008000, 0x100),
        "mvp-text": (0x102064000, 0x300), "mvp-rodata": (0x102064300, 0x200)}
    records = {(record["content"]["object"], record["register"]): record
               for record in value["expected"]["records"]}
    ranges = {(entry["object"], entry["domain"]): entry
              for entry in value["ranges"]}

    def digest(name, stream):
        return records[name, stream]["digests"][0]["digest"]
    checks = [
        ("the self-test's own reference, field for field", value ==
         build.own),
        ("the identity fields", (value["image"], value["scenario"],
                                 value["variant"], value["toolchain"],
                                 value["r2"], value["contract"],
                                 value["source"]) ==
         ("te-poc", "te-poc", None, "gcc", "kept",
          {"run": "complete", "sequence": "v2"}, build.source)),
        ("the files' SHA-256", (value["elf_sha256"],
                                value["boot_image_sha256"],
                                value["authority_report_sha256"],
                                value["mutated_image_sha256"]) ==
         (sha256(build.elf.data), sha256(boot), sha256(build.report_bytes),
          None)),
        ("each R2 range: symbols, offset, digest", all(
            records[name, 0]["content"]["base"] == LOG.hex64(base) and
            records[name, 0]["content"]["length"] == LOG.hex64(length) and
            digest(name, 0) == at(base, length) and
            ranges[name, None]["image_offset"] == LOG.hex64(
                base - 0x102000000 + 0x1000)
            for name, (base, length) in wanted.items())),
        ("each R4 object: placement, source, digest", all(
            ranges[name, domain]["base"] == LOG.hex64(base) and
            ranges[name, domain]["source"] == source and
            ranges[name, domain]["digest"] == sha256(data)
            for name, domain, base, source, data in (
                ("kernel-image", 0, 0x110200000, "guest/Image",
                 build.kernel),
                ("device-tree", 0, 0x113e00000,
                 "guest/mvp-guest-g0-te-poc.dtb", build.trees[0]),
                ("kernel-image", 1, 0x114200000, "guest/Image",
                 build.kernel),
                ("device-tree", 1, 0x117e00000,
                 "guest/mvp-guest-g1-te-poc.dtb", build.trees[1])))),
        ("the configuration records", (
            digest("core-identity", 1), digest("console-grants", 1),
            digest("configuration-identity", 1),
            digest("policy-identity", 1)) ==
         (sha256(b"self-test core identity"), sha256(b"\0\0"),
          sha256(b"configuration"), sha256(b"policy"))),
        ("the header", value["expected"]["header"]["scenario_sha256"] ==
         build.expect["scenario_sha256"] and value["expected"]["header"][
             "configuration_identity"] == sha256(b"configuration") and
         value["expected"]["header"]["count"] == 14),
        ("the registers and launch_expected", value["expected"][
            "registers"] == LOG.replay([LOG.record_of(record, "r") for
                                        record in value["expected"][
                                            "records"]]) and
         value["launch_expected"] == value["expected"]["registers"][2:]),
        ("the linked constants and the generator's section agree",
         "constants=linked" in notes and "expectation=same" in notes),
        ("two generations, byte for byte", LOG.render(reference(
            self_build())[0]) == data),
        ("read back by the profile's reader",
         LOG.read_reference(data).sha256 == sha256(data))]
    results += [(name, ok, "") for name, ok in checks]

    def refused(case, wanted_text, assume=None, **changes):
        try:
            reference(self_build(**changes), assume)
        except Refused as error:
            results.append((case, wanted_text in str(error), str(error)))
            return
        results.append((case, False, "accepted"))
    two = self_build()
    refused("a missing symbol", "no symbol __be_mvp_rodata_end",
            drop=("__be_mvp_rodata_end",))
    refused("a range outside the image", "outside the flat monitor",
            symbols={"__be_mvp_rodata_end": 0x102000000 + 0xa4000 + 0x10})
    refused("a range whose bytes are not the boot image's", "are not the "
            "ELF's", boot=two.boot[:0x1010] + b"\1" + two.boot[0x1011:])
    refused("an unknown sequence in the expectation's log", "outside the "
            "allowlist", section=lambda log: log.update(sequence="v9"))
    refused("R2 kept by the generator, dropped by --assume-r2", "R2 is ",
            assume="dropped")
    refused("R2's switch defined twice", "defines BE_MVP_LOG_R2 2 times",
            header=SELF_HEADER + "#define BE_MVP_LOG_R2\tBE_MVP_C(1)\n")
    refused("a linked count not the sequence's", "differ from the "
            "reference's in count", constants={"count": 13})
    refused("a linked launch register not the reference's", "in launch",
            constants={"launch": [ZERO_DIGEST, ZERO_DIGEST]})
    refused("a record of the expectation's section unlike the reference's",
            "log.records[9].digests[0].digest is", section=lambda log:
            log["records"][9]["digests"][0].update(digest=ZERO_DIGEST))
    refused("an expected line unlike the reference's",
            "log.lines.terminal is", section=lambda log: log["lines"].update(
                terminal=log["lines"]["terminal"].replace("r1=", "r1=0")))
    refused("a kernel the boot image does not carry", "is not the kernel",
            kernel=two.kernel[:-1] + b"\0")
    refused("an R4 source the boot image does not stage", "is not the "
            "kernel-image the boot image stages for domain 0",
            staged_kernel=two.kernel[:-1] + b"\1")
    refused("a mutated image with two bits flipped", "in one bit",
            image="self-report-flip", run="self-report-flip",
            flip_bits=(0, 9))
    refused("self-report-flip's metadata on another bit", "do not name the "
            "bit flipped", image="self-report-flip", run="self-report-flip",
            flip=dict(self_build("self-report-flip", "self-report-flip").flip,
                      bit=1))
    refused("self-report-flip's metadata on another nominal image",
            "does not name these nominal and mutated boot images",
            image="self-report-flip", run="self-report-flip",
            flip=dict(self_build("self-report-flip", "self-report-flip").flip,
                      nominal_image_sha256=ZERO_DIGEST))
    try:
        LOG.strict_json(b'{"image": "a", "image": "b"}', "the expectation")
        results.append(("a duplicate key", False, "accepted"))
    except Refused as error:
        results.append(("a duplicate key", "duplicate key" in str(error),
                        str(error)))
    try:
        LOG.read_reference(data.replace(b'"object": "close"',
                                        b'"object": "ima-ng"'))
        results.append(("an unknown object in a reference", False,
                        "accepted"))
    except Refused as error:
        results.append(("an unknown object in a reference",
                        "outside the allowlist" in str(error), str(error)))
    flip = self_build("self-report-flip", "self-report-flip")
    flipped, _ = reference(flip)
    results.append(("self-report-flip: the nominal digests, the mutated "
                    "image's SHA-256", flipped["mutated_image_sha256"] ==
                    sha256(flip.mutated) and flipped["contract"]["run"] ==
                    "self-report-flip" and flipped["ranges"] ==
                    value["ranges"], ""))
    gate = self_build("wrong-measurement", "gate-fail")
    failed, _ = reference(gate)
    results.append(("gate-fail: domain 1's launch register flipped in bit 0",
                    failed["launch_expected"] == [
                        value["launch_expected"][0],
                        LOG.flip(value["launch_expected"][1])], ""))
    payload_kernel = two.kernel[:-1] + b"\1"
    staged, notes = reference(self_build(
        "payload", "pre-measurement", staged_kernel=payload_kernel))
    results.append(("a pre-measurement image staging its own kernel: "
                    "noted, the reference the build's", "staged=differs:"
                    "kernel-image:0,kernel-image:1" in notes and
                    staged["ranges"][5]["digest"] == sha256(two.kernel),
                    " ".join(notes)))
    results += compare_cases(SELF_TEST_SCRATCH)
    for name, ok, detail in results:
        print(f"{'ok  ' if ok else 'FAIL'} {name}"
              f"{'' if ok else ' ' + detail[:200]}")
    failures = sum(not ok for _, ok, _ in results)
    print(f"BE_MVP_LOG_REFERENCE_SELF_TEST: {'PASS' if not failures else 'FAIL'}"
          f" cases={len(results)} failed={failures}")
    return 1 if failures else 0


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--toolchain", choices=LOG.TOOLCHAINS)
    parser.add_argument("--build-root")
    parser.add_argument("--out")
    parser.add_argument("--image", action="append", default=[])
    parser.add_argument("--assume-r2", choices=LOG.R2_STATES)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--compare", nargs=2)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv[1:])
    if args.self_test:
        return self_test()
    if args.compare:
        return compare(*args.compare)
    if not (args.toolchain and args.build_root and args.out and args.image):
        parser.error("--toolchain, --build-root, --out, and --image are "
                     "required")
    return generate(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
