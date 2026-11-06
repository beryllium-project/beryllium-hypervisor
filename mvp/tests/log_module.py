#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""The Beryllium log profile, version 1, for the capture checker and the
reference tool (planning/mvp-m9-plan.md, D-3, D-4, D-5; mvp/docs/
log-profile.md, whose section numbers the comments cite).

Purpose: one Python reading of the profile, shared by the two tools of the
offline evidence TCB that read or write it (security model v1, Revision 3,
R3.4). tests/check-capture.py calls judge() on every capture whose
expectation carries M9's log data (its "log" section): the log's lines are
taken from hart 0's unprefixed stream alone, the canonical page is rebuilt
and a line set that does not rebuild is refused (4.6), the registers are
replayed and their values labelled unprotected, every digest is recomputed
from the run's boot image, the build's inputs, and the generator's
canonical data rather than taken from the printed lines, every header and
record field is compared with the image's reference manifest (4.7), the
global order and the run class's prefix are held (3.2), and the rebuilt log
is exported (5.2). tools/gen-reference.py builds each reference with
expected_log() and build_reference().
Trust: it reads text and JSON and executes nothing it reads but the
generator's policy tool (tools/policy-check.py, at its fixed path), whose
core() gives the core identity. Every JSON file is read by strict_json(): a
size bound, no duplicate key, no NaN or infinity, and no float in the
profile's own files; every name outside section 7's allowlist is refused,
so an IMA measurement list, an IMA template, a CEL content type other than
beryllium-log-v1, or a file path as an object never enters a log, an
export, or a reference.
Scope: version 1 of the profile; any other version is refused. The
recomputation trusts SHA-256 and this module's reading of the inputs, and
nothing printed by the monitor. self_cases() is the capture checker's
self-test of this module: the profile's test vectors, section 5.4's te-poc
example and the round trip, and the plan's five kinds of negatives (D-4) on
that example and on this module's own anchor and two-guests syntheses, each
with its reference frozen.
"""

import hashlib
import importlib.util
import json
import pathlib
import re
import struct

HERE = pathlib.Path(__file__).resolve().parent
MVP_DIR = HERE.parent
PROFILE = MVP_DIR / "docs" / "log-profile.md"
POLICY_TOOL = MVP_DIR / "tools" / "policy-check.py"

# ------------------------------------------------------------ the profile
# 2.2 and 2.3: the header's and each record's constants.
MAGIC, VERSION = "BEMVPLOG", 1
HEADER_BYTES, RECORD_BYTES, CAPACITY, PAGE_BYTES = 128, 96, 41, 4096
DIGEST_BYTES, ALGORITHM, HASH_ALG = 32, 0x000B, "sha256"
CONTENT_TYPE = "beryllium-log-v1"
EXPORT_SCHEMA, REFERENCE_SCHEMA = "be-mvp-log-v1", "be-mvp-log-reference-v1"
# 5.1: the readers' bound; 4.1: hart 0's line buffer less its line feed.
JSON_LIMIT, LINE_LIMIT = 262144, 319
CLOSE_STREAM, ZERO = 255, "0" * 64
# 2.4: the numbers the page holds, the names the lines and the export print.
TYPES = (None, "measured", "informational", "close")
OBJECTS = ("monitor-text", "monitor-rodata", "monitor-input", "mvp-text",
           "mvp-rodata", "core-identity", "console-grants",
           "configuration-identity", "policy-identity", "policy-absent",
           "kernel-image", "device-tree", "secret-page", "close")
REPRESENTATIONS = ("as-placed", "as-computed", "build-recorded", "none")
OUTCOMES = ("recorded", "gated-pass", "gated-fail", "none")
STATES = ("open", "closed", "overflow")
STREAMS = (0, 1, 2, 3, CLOSE_STREAM)
# 5.3 and section 7: the reference's own enumerations.
SEQUENCES = ("v1", "v2", "v3", "probe")
RUNS = ("complete", "pre-measurement", "gate-fail", "self-report-flip",
        "post-launch-failure")
R2_STATES = ("kept", "dropped")
TOOLCHAINS = ("gcc", "clang")
R2 = OBJECTS[:5]
# 2.7: each object's row: its type, streams, representation, whether it has
# a range, whether its digest is zero, and the outcomes 2.9 admits for it.
ROWS = dict(
    {name: ("measured", (0,), "as-placed", True, False, ("recorded",))
     for name in R2},
    **{"core-identity": ("measured", (1,), "as-computed", False, False,
                         ("recorded",)),
       "console-grants": ("measured", (1,), "as-computed", False, False,
                          ("recorded",)),
       "configuration-identity": ("informational", (1,), "build-recorded",
                                  False, False, ("recorded",)),
       "policy-identity": ("informational", (1,), "build-recorded", False,
                           False, ("recorded",)),
       "policy-absent": ("informational", (1,), "build-recorded", False,
                         True, ("recorded",)),
       "kernel-image": ("measured", (2, 3), "as-placed", True, False,
                        OUTCOMES[:3]),
       "device-tree": ("measured", (2, 3), "as-placed", True, False,
                       OUTCOMES[:3]),
       "secret-page": ("measured", (3,), "as-placed", True, False,
                       OUTCOMES[:3]),
       "close": ("close", (CLOSE_STREAM,), "none", False, True, ("none",))})
# 5.3: an R2 range's offset in the boot image, base - MONITOR + OFFSET, and
# the flat monitor's extent there (src/mvp-layout.h's BE_MVP_MONITOR_HPA,
# BE_MVP_BOOT_MONITOR_OFFSET, BE_MVP_IMAGE_BYTES); the U-Boot rehearsal's
# QEMU-only copy differs from its board image in the header's text_offset
# alone (BE_MVP_UBOOT_TEXT_OFFSET, BE_MVP_QEMU_TEXT_OFFSET).
MONITOR_HPA, MONITOR_OFFSET, MONITOR_BYTES = 0x102000000, 0x1000, 0xa4000
BOARD_TEXT_OFFSET, QEMU_TEXT_OFFSET = 0x6000000, 0x88000000
# The fields each line prints, in order (4.2, 4.3), and each decimal's width.
HEADER_FIELDS = ("magic", "version", "hlen", "rlen", "capacity", "count",
                 "state", "alg", "scenario", "config")
RECORD_FIELDS = ("seq", "producer", "type", "stream", "object", "repr",
                 "outcome", "base", "length", "dlen", "srec", "expected",
                 "digest")
WIDTHS = {"version": 16, "hlen": 16, "rlen": 16, "capacity": 16,
          "count": 16, "seq": 16, "producer": 8, "stream": 8, "dlen": 16,
          "srec": 16, "expected": 16}
# 4.1's forms.
DEC = r"(0|[1-9][0-9]*)"
DIG = r"([0-9a-f]{64})"
HEADER_LINE = re.compile(
    rf"BE_MVP:19 LOG header magic=(\S+) version={DEC} hlen={DEC} "
    rf"rlen={DEC} capacity={DEC} count={DEC} state=([a-z0-9_-]+) "
    rf"alg=0x([0-9a-f]{{4}}) scenario={DIG} config={DIG}")
RECORD_LINE = re.compile(
    rf"BE_MVP:19 LOG record seq={DEC} producer={DEC} type=([a-z0-9_-]+) "
    rf"stream={DEC} object=([a-z0-9_./-]+) repr=([a-z0-9_-]+) "
    rf"outcome=([a-z0-9_-]+) base=0x([0-9a-f]{{16}}) "
    rf"length=0x([0-9a-f]{{16}}) dlen={DEC} srec={DEC} expected={DEC} "
    rf"digest={DIG}")
BARRIER_LINE = re.compile(
    rf"BE_MVP:20 REGISTERS at=barrier r0={DIG} r1={DIG} r2={DIG} r3={DIG} "
    r"ticks=(0x(?:0|[1-9a-f][0-9a-f]{0,7}))")
TERMINAL_LINE = re.compile(
    rf"BE_MVP:20 REGISTERS at=terminal r0={DIG} r1={DIG} r2={DIG} "
    rf"r3={DIG}")
HEX = r"(0x(?:0|[1-9a-f][0-9a-f]{0,15}))"
LAUNCH_LINE = re.compile(
    rf"BE_MVP:06 LAUNCH domain={DEC} hart={DEC} register={DIG} "
    rf"expected=match ticks={HEX}")
DETAIL_LINE = re.compile(rf"BE_MVP:DETAIL domain={DEC} hart={DEC} "
                         rf"computed={DIG} expected={DIG}")
TERMINATED_LINE = re.compile(
    rf"BE_MVP:12 DOMAIN_TERMINATED hart={DEC} domain={DEC} by={DEC} "
    rf"exits={DEC} sha256=([0-9a-f]{{64}}|-) ticks={HEX}")
STARTED = re.compile(r"BE_MVP:08 HART_STARTED hart=[0-9]+ domain=([0-9]+) ")
FLIP_FINDING = "self-report differs: mvp-rodata"
LOG_TAGS = ("BE_MVP:19", "BE_MVP:20", "BE_MVP:06 LAUNCH")
LOG_MARKERS = ("BE_MVP:19", "BE_MVP:20")
# The expectations the profile's 3.2 assigns to the run class whose boot
# image is their scenario's own (tests/run-qemu.sh runs both on it).
SCENARIO_IMAGE_RUNS = ("no-sstc", "sbi-3.0")
# 5.1 and section 7's forms.
DIGEST_FORM = re.compile(r"[0-9a-f]{64}")
HEX64_FORM = re.compile(r"0x[0-9a-f]{16}")
COMMIT_FORM = re.compile(r"[0-9a-f]{40}")
TREE_FORM = re.compile(r"clean|dirty changed=[1-9][0-9]*")
NAME_FORM = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*")
SOURCE_PART = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
EXPECT_SCHEMAS = {"be-mvp-expect-v1": "v1", "be-mvp-expect-v2": "v2",
                  "be-mvp-expect-v3": "v3"}
WINDOW_RIGHTS = ["read", "write", "execute"]
# The expectation's log section as tools/gen-scenario.py writes it
# (apply_log()): its keys, self-report-flip's two more, its lines' keys,
# where its terminal registers line stands, and the R2 ranges whose base
# the link fixes at the layout's (src/mvp-monitor.lds's ASSERTs), which the
# expectation holds; every other R2 base, every R2 length and digest, and
# r0 with R2 kept are null there and slots in its lines: <Y> a hex64, <Z>
# a digest, <U> the barrier's ticks, <T> a LAUNCH line's.
EXPECT_LOG_KEYS = ("count", "header", "launch_expected", "lines", "profile",
                   "r2", "ranges", "records", "registers", "run",
                   "sequence", "terminal")
EXPECT_FLIP_KEYS = ("findings", "mutate")
EXPECT_LINE_KEYS = ("barrier", "block", "detail", "launch", "terminal")
TERMINALS = ("none", "before-fail", "before-shutdown")
FIXED_BASES = ("monitor-text", "monitor-input", "mvp-text")
SYMBOL_FORM = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}")
MARKER_FORM = re.compile(r"BE_MVP:[0-9]{2}")


class Refused(Exception):
    """An input the profile does not admit."""


def require(condition, message):
    if not condition:
        raise Refused(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


# ------------------------------------------------------------- JSON (5.1)
def strict_json(data, what, limit=JSON_LIMIT, floats=False):
    """DATA's JSON value, or Refused: above LIMIT bytes, a duplicate key at
    any level, NaN or an infinity, a float unless FLOATS, or no JSON."""
    require(isinstance(data, (bytes, bytearray)), f"{what}: not bytes")
    require(len(data) <= limit, f"{what}: {len(data)} bytes, above the "
            f"{limit}-byte bound")

    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, f"{what}: duplicate key {key!r}")
            out[key] = value
        return out

    def constant(name):
        raise Refused(f"{what}: {name} is not a JSON number")

    def no_float(text):
        raise Refused(f"{what}: the float {text} where the profile has "
                      f"integers")
    try:
        return json.loads(bytes(data).decode("utf-8"),
                          object_pairs_hook=pairs, parse_constant=constant,
                          **({} if floats else {"parse_float": no_float}))
    except (UnicodeDecodeError, ValueError) as error:
        raise Refused(f"{what}: not JSON: {error}") from None


def render(value):
    """5.1's form: Python's json.dumps(value, indent=1, sort_keys=True) and
    one line feed, ASCII."""
    return (json.dumps(value, indent=1, sort_keys=True) + "\n").encode(
        "ascii")


def shape(value, keys, where):
    """VALUE is an object of exactly KEYS."""
    require(isinstance(value, dict), f"{where}: not an object")
    missing, extra = set(keys) - set(value), set(value) - set(keys)
    require(not missing, f"{where}: no {', '.join(sorted(missing))}")
    require(not extra, f"{where}: {', '.join(sorted(extra))}, which the "
            f"schema does not name")
    return value


def form(value, pattern, where, null=False):
    """VALUE is a string of PATTERN's form (or None when NULL)."""
    if null and value is None:
        return value
    require(isinstance(value, str) and pattern.fullmatch(value),
            f"{where}: {str(value)[:70]!r} is not of its field's form")
    return value


def member(value, names, where):
    require(isinstance(value, str) and value in names,
            f"{where}: {str(value)[:40]!r} is outside the allowlist "
            f"(section 7)")
    return value


def hex64(value):
    return f"0x{value:016x}"


# --------------------------------------------------------- page and lines
def encode(header, records):
    """The canonical 4 KiB page (2.1 to 2.3): every integer little-endian
    at its offset, every reserved byte and unused slot zero."""
    require(len(records) <= CAPACITY, f"{len(records)} records, above the "
            f"capacity {CAPACITY}")
    page = bytearray(PAGE_BYTES)
    page[0:8] = header["magic"].encode("ascii")[:8]
    struct.pack_into("<HHHHHBBH", page, 8, header["version"],
                     header["hlen"], header["rlen"], header["capacity"],
                     header["count"], STATES.index(header["state"]), 0,
                     header["alg"])
    page[32:64] = bytes.fromhex(header["scenario"])
    page[64:96] = bytes.fromhex(header["config"])
    for index, record in enumerate(records):
        at = HEADER_BYTES + RECORD_BYTES * index
        struct.pack_into(
            "<HBBBBBBQQHHHH", page, at, record["seq"], record["producer"],
            TYPES.index(record["type"]), record["stream"],
            OBJECTS.index(record["object"]),
            REPRESENTATIONS.index(record["repr"]),
            OUTCOMES.index(record["outcome"]), record["base"],
            record["length"], record["dlen"], record["srec"],
            record["expected"], 0)
        page[at + 32:at + 64] = bytes.fromhex(record["digest"])
    return bytes(page)


def decode(page):
    """(header, records) of a canonical page, or Refused."""
    require(len(page) == PAGE_BYTES, "not a 4 KiB page")
    version, hlen, rlen, capacity, count, state, reserved, alg = \
        struct.unpack_from("<HHHHHBBH", page, 8)
    require(state < len(STATES) and count <= CAPACITY and not reserved,
            "the header's state, count, or reserved byte")
    header = dict(magic=page[0:8].decode("ascii", "replace"),
                  version=version, hlen=hlen, rlen=rlen, capacity=capacity,
                  count=count, state=STATES[state], alg=alg,
                  scenario=page[32:64].hex(), config=page[64:96].hex())
    records = []
    for index in range(count):
        at = HEADER_BYTES + RECORD_BYTES * index
        values = struct.unpack_from("<HBBBBBBQQHHHH", page, at)
        require(0 < values[2] < len(TYPES) and values[4] < len(OBJECTS) and
                values[5] < len(REPRESENTATIONS) and
                values[6] < len(OUTCOMES), f"record {index}: a number "
                f"outside its enumeration")
        records.append(dict(zip(RECORD_FIELDS[:12], (
            values[0], values[1], TYPES[values[2]], values[3],
            OBJECTS[values[4]], REPRESENTATIONS[values[5]],
            OUTCOMES[values[6]]) + values[7:12]),
            digest=page[at + 32:at + 64].hex()))
    return header, records


def header_line(header):
    return ("BE_MVP:19 LOG header " + " ".join(
        f"{name}={header[name]}" if name != "alg" else
        f"alg=0x{header['alg']:04x}" for name in HEADER_FIELDS))


def record_line(record):
    return "BE_MVP:19 LOG record " + " ".join(
        f"{name}={hex64(record[name])}" if name in ("base", "length") else
        f"{name}={record[name]}" for name in RECORD_FIELDS)


def registers_line(at, registers, ticks=None):
    return (f"BE_MVP:20 REGISTERS at={at} " + " ".join(
        f"r{index}={value}" for index, value in enumerate(registers)) +
        (f" ticks={ticks}" if ticks is not None else ""))


def replay(records):
    """2.6: each register from 32 zero bytes, R := SHA-256(R || digest) for
    each measured record of its stream, in sequence order."""
    registers = [bytes(DIGEST_BYTES)] * 4
    for record in records:
        if record["type"] == "measured" and record["stream"] in range(4):
            registers[record["stream"]] = hashlib.sha256(
                registers[record["stream"]] +
                bytes.fromhex(record["digest"])).digest()
    return [value.hex() for value in registers]


# ------------------------------------------------------------ export (5.2)
def export_header(header):
    return {"capacity": header["capacity"],
            "configuration_identity": header["config"],
            "count": header["count"], "hashAlg": HASH_ALG,
            "header_length": header["hlen"], "magic": header["magic"],
            "record_length": header["rlen"],
            "scenario_sha256": header["scenario"], "state": header["state"],
            "version": header["version"]}


def export_record(record):
    return {"content": {"base": hex64(record["base"]),
                        "expected": record["expected"],
                        "length": hex64(record["length"]),
                        "object": record["object"],
                        "outcome": record["outcome"],
                        "producer": record["producer"],
                        "representation": record["repr"],
                        "type": record["type"]},
            "content_type": CONTENT_TYPE,
            "digests": [{"digest": record["digest"], "hashAlg": HASH_ALG}],
            "recnum": record["seq"],
            "register": None if record["stream"] == CLOSE_STREAM else
            record["stream"], "srec": record["srec"]}


def export(header, records, barrier, terminal):
    return {"header": export_header(header),
            "records": [export_record(record) for record in records],
            "registers": {"barrier": barrier, "replayed": replay(records),
                          "replayed_label": "unprotected",
                          "terminal": terminal},
            "schema": EXPORT_SCHEMA}


def header_of(value, where):
    """The page's header from the export's shape, every field checked."""
    shape(value, ("capacity", "configuration_identity", "count", "hashAlg",
                  "header_length", "magic", "record_length",
                  "scenario_sha256", "state", "version"), where)
    for name in ("capacity", "count", "header_length", "record_length",
                 "version"):
        require(integer(value[name]), f"{where}.{name}: not an integer")
    require(value["magic"] == MAGIC and value["version"] == VERSION and
            value["header_length"] == HEADER_BYTES and
            value["record_length"] == RECORD_BYTES and
            value["capacity"] == CAPACITY and value["hashAlg"] == HASH_ALG,
            f"{where}: not version {VERSION}'s magic, lengths, capacity, "
            f"and algorithm")
    require(0 <= value["count"] <= CAPACITY, f"{where}.count: "
            f"{value['count']} outside 0 to {CAPACITY}")
    member(value["state"], STATES, f"{where}.state")
    return {"magic": MAGIC, "version": VERSION, "hlen": HEADER_BYTES,
            "rlen": RECORD_BYTES, "capacity": CAPACITY,
            "count": value["count"], "state": value["state"],
            "alg": ALGORITHM,
            "scenario": form(value["scenario_sha256"], DIGEST_FORM,
                             f"{where}.scenario_sha256"),
            "config": form(value["configuration_identity"], DIGEST_FORM,
                           f"{where}.configuration_identity")}


def record_of(value, where):
    """A page record from the export's shape, every field checked."""
    shape(value, ("content", "content_type", "digests", "recnum",
                  "register", "srec"), where)
    content = shape(value["content"], (
        "base", "expected", "length", "object", "outcome", "producer",
        "representation", "type"), f"{where}.content")
    require(value["content_type"] == CONTENT_TYPE,
            f"{where}.content_type: {str(value['content_type'])[:40]!r} is "
            f"outside the allowlist (section 7)")
    digests = value["digests"]
    require(isinstance(digests, list) and len(digests) == 1,
            f"{where}.digests: not one digest")
    shape(digests[0], ("digest", "hashAlg"), f"{where}.digests[0]")
    require(digests[0]["hashAlg"] == HASH_ALG,
            f"{where}.digests[0].hashAlg: outside the allowlist "
            f"(section 7)")
    for name in ("recnum", "srec"):
        require(integer(value[name]) and 0 <= value[name] <= 0xffff,
                f"{where}.{name}: not a 16-bit integer")
    for name in ("expected", "producer"):
        require(integer(content[name]) and 0 <= content[name] <= 0xffff,
                f"{where}.content.{name}: not an integer of its field")
    register = value["register"]
    require(register is None or (integer(register) and register in
                                 range(4)), f"{where}.register: not 0 to 3 "
            f"or null")
    return {"seq": value["recnum"], "producer": content["producer"],
            "type": member(content["type"], TYPES[1:],
                           f"{where}.content.type"),
            "stream": CLOSE_STREAM if register is None else register,
            "object": member(content["object"], OBJECTS,
                             f"{where}.content.object"),
            "repr": member(content["representation"], REPRESENTATIONS,
                           f"{where}.content.representation"),
            "outcome": member(content["outcome"], OUTCOMES,
                              f"{where}.content.outcome"),
            "base": int(form(content["base"], HEX64_FORM,
                             f"{where}.content.base"), 16),
            "length": int(form(content["length"], HEX64_FORM,
                               f"{where}.content.length"), 16),
            "dlen": DIGEST_BYTES, "srec": value["srec"],
            "expected": content["expected"],
            "digest": form(digests[0]["digest"], DIGEST_FORM,
                           f"{where}.digests[0].digest")}


def registers_of(value, where, null=False):
    if null and value is None:
        return None
    require(isinstance(value, list) and len(value) == 4,
            f"{where}: not four registers")
    return [form(item, DIGEST_FORM, f"{where}[{index}]")
            for index, item in enumerate(value)]


def records_of(values, where):
    require(isinstance(values, list) and len(values) <= CAPACITY,
            f"{where}: not a list of at most {CAPACITY} records")
    return [record_of(value, f"{where}[{index}]")
            for index, value in enumerate(values)]


def read_export(data):
    """An export (log.json), strictly read: (header, records, registers)."""
    value = shape(strict_json(data, "the export"), ("header", "records",
                                                    "registers", "schema"),
                  "the export")
    require(value["schema"] == EXPORT_SCHEMA, "the export's schema is not "
            f"{EXPORT_SCHEMA}")
    registers = shape(value["registers"], ("barrier", "replayed",
                                           "replayed_label", "terminal"),
                      "the export's registers")
    require(registers["replayed_label"] == "unprotected",
            "the export's replayed_label is not unprotected")
    header = header_of(value["header"], "the export's header")
    records = records_of(value["records"], "the export's records")
    findings = structure(header, records)
    require(not findings, f"the export does not rebuild: {findings[:1]}")
    require(registers_of(registers["replayed"], "replayed") ==
            replay(records), "the export's replayed registers are not its "
            "records' replay")
    return header, records, {
        name: registers_of(registers[name], name, null=True)
        for name in ("barrier", "terminal")}


# ---------------------------------------------------- the contract (3.1)
def sequence_of(name, r2):
    """3.1's records for sequence NAME, R2 kept or dropped:
    [(object, stream, carries a gate)]."""
    out = [(name_, 0, False) for name_ in R2] if r2 == "kept" else []
    out += [("core-identity", 1, False), ("console-grants", 1, False)]
    out += [("policy-absent", 1, False)] if name in ("v1", "probe") else [
        ("configuration-identity", 1, False), ("policy-identity", 1, False)]
    if name != "probe":
        out += [("kernel-image", 2, False), ("device-tree", 2, True),
                ("kernel-image", 3, False)]
        out += [("device-tree", 3, False), ("secret-page", 3, True)] \
            if name == "v3" else [("device-tree", 3, True)]
    return out + [("close", CLOSE_STREAM, False)]


def derived_contract(expect):
    """3.2's run class from the expectation's outcome, by the rule of
    tools/gen-scenario.py's run_class() (which the generator pins to the
    profile's table at 4bc079db): a probe's and a passing image's complete
    log, self-report-flip's by the variant's name, a measurement failure's
    gate-fail, a failure declared after no marker or one before BE_MVP:07
    pre-measurement, and any later one a post-launch failure."""
    # PROFILE READING (3.2, 5.3): 3.2 assigns the classes by image; the
    # class is derived from the outcome's keys by the generator's rule, and
    # the expectation's log.sequence and log.run must agree with it
    # (contract_of()).
    outcome = expect.get("outcome") or {}
    if outcome.get("probe"):
        return "probe", "complete"
    sequence = EXPECT_SCHEMAS.get(expect.get("schema"))
    require(sequence is not None, f"the expectation's schema "
            f"{str(expect.get('schema'))[:40]!r} is none the log knows")
    if expect.get("image") == "self-report-flip":
        return sequence, "self-report-flip"
    if outcome.get("pass"):
        return sequence, "complete"
    if outcome.get("fail") == "measurement":
        return sequence, "gate-fail"
    after = outcome.get("after", "none")
    require(after == "none" or (isinstance(after, str) and
                                MARKER_FORM.fullmatch(after)),
            f"the expectation's outcome.after {str(after)[:20]!r} is no "
            f"marker")
    return sequence, ("pre-measurement" if after == "none" or
                      after < "BE_MVP:07" else "post-launch-failure")


def log_section(expect):
    """The expectation's M9 log section as tools/gen-scenario.py writes it
    (apply_log()), of exactly EXPECT_LOG_KEYS (and self-report-flip's
    findings and mutate): the profile's version; the sequence, run class,
    and R2 state; the count, the sequence's (3.1); where the terminal
    registers line stands; each domain's expected launch register; the
    lines' keys; and self-report-flip's one declared finding and the bit
    its variant flips. expectation_log() gives every value the image's
    reference implies, which binding_findings() compares field by field."""
    section = expect.get("log")
    require(isinstance(section, dict), "the expectation's log section is "
            "not an object")
    flipped = section.get("run") == "self-report-flip"
    shape(section, EXPECT_LOG_KEYS + (EXPECT_FLIP_KEYS if flipped else ()),
          "the expectation's log")
    require(integer(section["profile"]) and section["profile"] == VERSION,
            f"the expectation's log.profile is not {VERSION}")
    sequence = member(section["sequence"], SEQUENCES, "log.sequence")
    member(section["run"], RUNS, "log.run")
    r2 = member(section["r2"], R2_STATES, "log.r2")
    rows = len(sequence_of(sequence, r2))
    require(integer(section["count"]) and section["count"] == rows,
            f"the expectation's log.count {str(section['count'])[:20]} is "
            f"not the {sequence} sequence's {rows} with R2 {r2} (3.1)")
    member(section["terminal"], TERMINALS, "log.terminal")
    launch = section["launch_expected"]
    require(isinstance(launch, list) and len(launch) == (
        0 if sequence == "probe" else 2), "the expectation's "
        "log.launch_expected is not one digest per launched domain")
    for index, value in enumerate(launch):
        form(value, DIGEST_FORM, f"log.launch_expected[{index}]")
    shape(section["lines"], EXPECT_LINE_KEYS, "the expectation's log.lines")
    if flipped:
        require(section["findings"] == [FLIP_FINDING], f"the expectation's "
                f"log.findings is not [{FLIP_FINDING!r}] (D-4)")
        mutate = shape(section["mutate"], ("bit", "symbol"),
                       "the expectation's log.mutate")
        require(integer(mutate["bit"]) and 0 <= mutate["bit"] <= 7 and
                isinstance(mutate["symbol"], str) and
                SYMBOL_FORM.fullmatch(mutate["symbol"]),
                "the expectation's log.mutate is not a bit of a symbol")
    return section


def contract_of(expect):
    """(sequence, run): the expectation's log.sequence and log.run, which
    must be derived_contract()'s."""
    section = log_section(expect)
    derived = derived_contract(expect)
    pair = (section["sequence"], section["run"])
    require(pair == derived, f"the expectation declares {pair[0]}/"
            f"{pair[1]}, but its outcome is {derived[0]}/{derived[1]}'s "
            f"(3.2)")
    return pair


def expected_log(sequence, r2, values):
    """The complete log as the build defines it (5.3's `expected`): the
    sequence's records with VALUES, {(object, domain or None): digest, or
    (base, length, digest) for a ranged one, "scenario": digest}."""
    rows, records, counts = sequence_of(sequence, r2), [], {}
    for seq, (name, stream, gate) in enumerate(rows):
        kind, _, representation, ranged, zero, _ = ROWS[name]
        domain = stream - 2 if stream in (2, 3) else None
        value = values.get((name, domain))
        if ranged:
            require(isinstance(value, tuple) and len(value) == 3,
                    f"no range and digest for {name}")
            base, length, digest = value
        else:
            require(zero or isinstance(value, str), f"no digest for {name}")
            base, length, digest = 0, 0, ZERO if zero else value
        records.append({
            "seq": seq, "producer": 0, "type": kind, "stream": stream,
            "object": name, "repr": representation,
            "outcome": "none" if name == "close" else
            "gated-pass" if gate else "recorded",
            "base": base, "length": length, "dlen": DIGEST_BYTES,
            "srec": 0 if name == "close" else counts.get(stream, 0),
            "expected": len(rows) if name == "close" else 0,
            "digest": form(digest, DIGEST_FORM, name)})
        if name != "close":
            counts[stream] = counts.get(stream, 0) + 1
    header = {"magic": MAGIC, "version": VERSION, "hlen": HEADER_BYTES,
              "rlen": RECORD_BYTES, "capacity": CAPACITY,
              "count": len(rows), "state": "closed", "alg": ALGORITHM,
              "scenario": form(values.get("scenario"), DIGEST_FORM,
                               "the scenario digest"),
              "config": values.get(("configuration-identity", None), ZERO)}
    return header, records


def flip(digest):
    """Q16: bit 0 of the first byte flipped."""
    return f"{int(digest[:2], 16) ^ 1:02x}{digest[2:]}"


def build_reference(meta, sequence, run, r2, values, sources,
                    failing=None):
    """5.3's reference: META, {source: {commit, tree_state}, image,
    scenario, variant, toolchain, authority_report_sha256, elf_sha256,
    boot_image_sha256, mutated_image_sha256}; the complete log of
    expected_log(); SOURCES, {(object, domain): source} for each R4
    object; for gate-fail, FAILING, the domain whose expected launch
    register is the nominal one with bit 0 of its first byte flipped."""
    header, records = expected_log(sequence, r2, values)
    registers = replay(records)
    launch = [] if sequence == "probe" else registers[2:]
    if run == "gate-fail":
        require(failing in (0, 1), "a gate-fail reference needs its "
                "failing domain")
        launch[failing] = flip(launch[failing])
    ranges = []
    for record in records:
        if record["repr"] != "as-placed":
            continue
        domain = record["stream"] - 2 if record["stream"] in (2, 3) else None
        ranges.append({
            "base": hex64(record["base"]), "digest": record["digest"],
            "domain": domain, "image_offset": None if domain is not None else
            hex64(record["base"] - MONITOR_HPA + MONITOR_OFFSET),
            "length": hex64(record["length"]), "object": record["object"],
            "source": "boot-image" if domain is None else
            sources[record["object"], domain]})
    value = dict(meta, contract={"run": run, "sequence": sequence},
                 expected={"header": export_header(header),
                           "records": [export_record(record)
                                       for record in records],
                           "registers": registers},
                 launch_expected=launch, r2=r2, ranges=ranges,
                 schema=REFERENCE_SCHEMA)
    read_reference(render(value))
    return value


# ------------------------------------------------------- the reference
class Reference:
    """A reference manifest, strictly read (5.1, 5.3, section 7)."""

    def __init__(self, data):
        self.sha256 = sha256(data)
        value = self.value = shape(strict_json(data, "the reference"), (
            "authority_report_sha256", "boot_image_sha256", "contract",
            "elf_sha256", "expected", "image", "launch_expected",
            "mutated_image_sha256", "r2", "ranges", "scenario", "schema",
            "source", "toolchain", "variant"), "the reference")
        require(value["schema"] == REFERENCE_SCHEMA, f"the reference's "
                f"schema {str(value['schema'])[:40]!r} is not "
                f"{REFERENCE_SCHEMA}")
        source = shape(value["source"], ("commit", "tree_state"),
                       "the reference's source")
        form(source["commit"], COMMIT_FORM, "source.commit")
        form(source["tree_state"], TREE_FORM, "source.tree_state")
        self.image = form(value["image"], NAME_FORM, "image")
        self.scenario = form(value["scenario"], NAME_FORM, "scenario")
        self.variant = form(value["variant"], NAME_FORM, "variant",
                            null=True)
        self.toolchain = member(value["toolchain"], TOOLCHAINS,
                                "toolchain")
        contract = shape(value["contract"], ("run", "sequence"),
                         "the reference's contract")
        self.contract = (member(contract["sequence"], SEQUENCES,
                                "contract.sequence"),
                         member(contract["run"], RUNS, "contract.run"))
        self.r2 = member(value["r2"], R2_STATES, "r2")
        policy = self.contract[0] in ("v2", "v3")
        self.report = form(value["authority_report_sha256"], DIGEST_FORM,
                           "authority_report_sha256", null=not policy)
        require((self.report is None) != policy, "authority_report_sha256 "
                "is null exactly for a v1 image and a probe")
        self.elf = form(value["elf_sha256"], DIGEST_FORM, "elf_sha256")
        self.boot = form(value["boot_image_sha256"], DIGEST_FORM,
                         "boot_image_sha256")
        flipped = self.contract[1] == "self-report-flip"
        self.mutated = form(value["mutated_image_sha256"], DIGEST_FORM,
                            "mutated_image_sha256", null=not flipped)
        require((self.mutated is None) != flipped, "mutated_image_sha256 "
                "is a digest exactly in a self-report-flip reference")
        expected = shape(value["expected"], ("header", "records",
                                             "registers"),
                         "the reference's expected")
        self.header = header_of(expected["header"], "expected.header")
        self.records = records_of(expected["records"], "expected.records")
        self.registers = registers_of(expected["registers"],
                                      "expected.registers")
        self.launch = value["launch_expected"]
        require(isinstance(self.launch, list),
                "launch_expected is not a list")
        for index, item in enumerate(self.launch):
            form(item, DIGEST_FORM, f"launch_expected[{index}]")
        self.check_log()
        self.check_ranges(value["ranges"])

    def check_log(self):
        header, records = self.header, self.records
        found = structure(header, records)
        require(not found, f"the reference's expected log does not "
                f"rebuild: {found[:1]}")
        require(header["state"] == "closed" and header["count"] ==
                len(records), "the reference's expected log is not a "
                "closed, complete one")
        rows = sequence_of(self.contract[0], self.r2)
        require([(record["object"], record["stream"], record["outcome"])
                 for record in records] ==
                [(name, stream, "none" if name == "close" else
                  "gated-pass" if gate else "recorded")
                 for name, stream, gate in rows],
                f"the reference's records are not the {self.contract[0]} "
                f"sequence with R2 {self.r2} (3.1)")
        require(self.registers == replay(records), "the reference's "
                "expected registers are not its records' replay")
        launched = [] if self.contract[0] == "probe" else self.registers[2:]
        require(len(self.launch) == len(launched), f"launch_expected names "
                f"{len(self.launch)} domains, not {len(launched)}")
        differ = [index for index, (got, nominal) in enumerate(
            zip(self.launch, launched)) if got != nominal]
        if self.contract[1] == "gate-fail":
            require(len(differ) == 1 and self.launch[differ[0]] ==
                    flip(launched[differ[0]]), "a gate-fail reference's "
                    "launch_expected is not the nominal registers with one "
                    "domain's bit 0 of its first byte flipped (Q16)")
            self.failing = differ[0]
        else:
            require(not differ, "launch_expected is not the expected log's "
                    "launch registers")
            self.failing = None

    def check_ranges(self, ranges):
        placed = [record for record in self.records
                  if record["repr"] == "as-placed"]
        require(isinstance(ranges, list) and len(ranges) == len(placed),
                f"the range table does not name the {len(placed)} measured "
                f"ranges")
        self.sources = {}
        for index, (entry, record) in enumerate(zip(ranges, placed)):
            where = f"ranges[{index}]"
            shape(entry, ("base", "digest", "domain", "image_offset",
                          "length", "object", "source"), where)
            domain = record["stream"] - 2 if record["stream"] in (2, 3) \
                else None
            require(member(entry["object"], OBJECTS, f"{where}.object") ==
                    record["object"] and entry["domain"] == domain and
                    form(entry["base"], HEX64_FORM, f"{where}.base") ==
                    hex64(record["base"]) and
                    form(entry["length"], HEX64_FORM, f"{where}.length") ==
                    hex64(record["length"]) and
                    form(entry["digest"], DIGEST_FORM, f"{where}.digest") ==
                    record["digest"], f"{where} is not record "
                    f"{record['seq']}'s range")
            source = entry["source"]
            if domain is None:
                require(entry["image_offset"] == hex64(
                    record["base"] - MONITOR_HPA + MONITOR_OFFSET) and
                    source == "boot-image", f"{where}: an R2 range's "
                    f"offset is base - 0x{MONITOR_HPA:x} + "
                    f"0x{MONITOR_OFFSET:x} and its source boot-image")
            else:
                require(entry["image_offset"] is None,
                        f"{where}: an R4 object's image_offset is null")
                source_form(source, record["object"], where)
            self.sources[record["object"], domain] = source


def source_form(source, name, where):
    """Section 7: an R4 source is scenario-secret for the secret page, or a
    path relative to build/mvp/ naming a kernel Image or device tree the
    build made, with no `..` component and no leading `/`."""
    if name == "secret-page":
        require(source == "scenario-secret", f"{where}: the secret page's "
                f"source is scenario-secret")
        return source
    parts = source.split("/") if isinstance(source, str) else [""]
    require(all(SOURCE_PART.fullmatch(part) and part not in (".", "..")
                for part in parts), f"{where}: the source "
            f"{str(source)[:60]!r} is not a path relative to build/mvp/ "
            f"(section 7)")
    require(parts[-1] == "Image" if name == "kernel-image" else
            parts[-1].endswith(".dtb"), f"{where}: the source "
            f"{source[:60]!r} names no {name} the build made")
    return source


def read_reference(data):
    return Reference(data)


# ------------------------------------------ the expectation's log section
def log_harts(expect):
    """Each domain's hart as the image's log binds it: the expectation's
    binding, but a v1 variant's own hart for its domain, which the
    generator binds it to (tools/gen-scenario.py's scenario_logs())."""
    harts = [domain.get("hart") for domain in expect["domains"]]
    outcome = expect.get("outcome") or {}
    if EXPECT_SCHEMAS.get(expect.get("schema")) == "v1" and "hart" in \
            outcome:
        require(outcome.get("domain") in range(len(harts)),
                "the expectation's outcome.hart names no domain")
        harts[outcome["domain"]] = outcome["hart"]
    return harts


def slotted(record):
    """RECORD's BE_MVP:19 line as the expectation holds it: an R2 range's
    length and digest, and the base of one the link does not fix at the
    layout's, slots."""
    line = record_line(record)
    if record["object"] not in R2:
        return line
    if record["object"] not in FIXED_BASES:
        line = line.replace(f" base={hex64(record['base'])} ", " base=<Y> ",
                            1)
    line = line.replace(f" length={hex64(record['length'])} ",
                        " length=<Y> ", 1)
    return line.replace(f" digest={record['digest']}", " digest=<Z>", 1)


def expected_lines(reference, harts):
    """The lines the expectation holds for REFERENCE's image, each domain
    on HARTS[domain] (tools/gen-scenario.py's log_lines()): each launched
    domain's LAUNCH line, the block (a gate-fail's through the gated-fail
    record, its header open), the barrier's and the terminal's registers
    lines, and a gate-fail's DETAIL, each with its slots."""
    sequence, run = reference.contract
    records, header = reference.records, dict(reference.header)
    launched = [] if sequence == "probe" else reference.registers[2:]
    domains, detail = list(range(len(launched))), None
    if run == "gate-fail":
        failing = reference.failing
        end = max(index for index, record in enumerate(records)
                  if record["stream"] == 2 + failing) + 1
        records = [dict(record) for record in records[:end]]
        records[-1]["outcome"] = "gated-fail"
        header.update(state="open", count=len(records))
        domains = [domain for domain in domains if domain < failing]
        detail = (f"BE_MVP:DETAIL domain={failing} hart={harts[failing]} "
                  f"computed={launched[failing]} "
                  f"expected={reference.launch[failing]}")
    values = " ".join(
        f"r{index}={'<Z>' if index == 0 and reference.r2 == 'kept' else value}"
        for index, value in enumerate(reference.registers))
    return {"barrier": f"BE_MVP:20 REGISTERS at=barrier {values} ticks=<U>",
            "block": [header_line(header)] + [slotted(record)
                                               for record in records],
            "detail": detail,
            "launch": [f"BE_MVP:06 LAUNCH domain={domain} "
                       f"hart={harts[domain]} register={launched[domain]} "
                       f"expected=match ticks=<T>" for domain in domains],
            "terminal": f"BE_MVP:20 REGISTERS at=terminal {values}"}


def expectation_log(reference, harts, fallback=False, mutate=None):
    """The expectation's log section that REFERENCE's image implies, in
    tools/gen-scenario.py's shapes (apply_log()): the reference's complete
    log, the export's header and records, each R2 field the link fixes
    null, the ranges without their image offsets, the registers with r0
    null when R2 is kept, the launch constants, where the terminal line
    stands (none for a pre-measurement or gate-fail run and for the
    ring-full FALLBACK), the lines (expected_lines()), and
    self-report-flip's declared finding and MUTATE, the bit its variant
    flips."""
    sequence, run = reference.contract
    records = []
    for record in reference.records:
        item = export_record(record)
        if record["object"] in R2:
            item["content"]["length"] = None
            item["digests"][0]["digest"] = None
            if record["object"] not in FIXED_BASES:
                item["content"]["base"] = None
        records.append(item)
    ranges = []
    for entry in reference.value["ranges"]:
        item = {name: entry[name] for name in (
            "base", "digest", "domain", "length", "object", "source")}
        if entry["domain"] is None:
            item.update(digest=None, length=None, base=entry["base"] if
                        entry["object"] in FIXED_BASES else None)
        ranges.append(item)
    registers = list(reference.registers)
    if reference.r2 == "kept":
        registers[0] = None
    out = {"count": reference.header["count"],
           "header": export_header(reference.header),
           "launch_expected": list(reference.launch),
           "lines": expected_lines(reference, harts), "profile": VERSION,
           "r2": reference.r2, "ranges": ranges, "records": records,
           "registers": registers, "run": run, "sequence": sequence,
           "terminal": "none" if run in ("pre-measurement", "gate-fail") or
           fallback else "before-fail" if run == "post-launch-failure" else
           "before-shutdown"}
    if run == "self-report-flip":
        out.update(findings=[FLIP_FINDING], mutate=mutate)
    return out


def differences(want, got, where, limit=4):
    """The first LIMIT places where GOT is not WANT, a JSON value's path
    (WHERE.key[index]) and both values."""
    out = []

    def walk(one, two, at):
        if len(out) >= limit:
            return
        if isinstance(one, dict) and isinstance(two, dict):
            for key in sorted(set(one) | set(two)):
                if key not in two or key not in one:
                    out.append(f"{at}.{key} is " + ("absent" if key not in
                                                    two else "unexpected"))
                else:
                    walk(one[key], two[key], f"{at}.{key}")
        elif isinstance(one, list) and isinstance(two, list) and \
                len(one) == len(two):
            for index, (first_, second) in enumerate(zip(one, two)):
                walk(first_, second, f"{at}[{index}]")
        elif one != two or type(one) is not type(two):
            out.append(f"{at} is {json.dumps(two)[:90]}, not "
                       f"{json.dumps(one)[:90]}")
    walk(want, got, where)
    return out


# ------------------------------------------------------ rebuild (4.6)
def structure(header, records, number=None):
    """4.6's rules on a header and its records, whatever they came from:
    the constants, the rows of 2.7, srec, the state, and the configuration
    identity. NUMBER(i) names record i's line (or None)."""
    number = number or (lambda index: None)
    out = []

    def at(index):
        line = number(index)
        return f"line {line}: " if line else f"record {index}: "
    if header["magic"] != MAGIC or header["version"] != VERSION or \
            header["hlen"] != HEADER_BYTES or \
            header["rlen"] != RECORD_BYTES or \
            header["capacity"] != CAPACITY or header["alg"] != ALGORITHM:
        out.append(f"{at(-1) if number(-1) else 'the header: '}magic "
                   f"{header['magic']} version {header['version']} hlen "
                   f"{header['hlen']} rlen {header['rlen']} capacity "
                   f"{header['capacity']} alg 0x{header['alg']:04x}: not "
                   f"version {VERSION}'s BEMVPLOG, 128, 96, 41, 0x000b")
    if header["state"] not in STATES:
        out.append(f"the header's state {header['state']!r} is outside "
                   f"the allowlist (section 7)")
    counts = {}
    for index, record in enumerate(records):
        name = record["object"]
        row = ROWS.get(name)
        if record["producer"] != 0:
            out.append(f"{at(index)}producer={record['producer']}, not 0, "
                       f"the only producer")
        if record["dlen"] != DIGEST_BYTES:
            out.append(f"{at(index)}dlen={record['dlen']}, not 32")
        if row is None or record["type"] not in TYPES[1:] or \
                record["repr"] not in REPRESENTATIONS or \
                record["outcome"] not in OUTCOMES or \
                record["stream"] not in STREAMS:
            out.append(f"{at(index)}{record['type']}/{record['stream']}/"
                       f"{name}/{record['repr']}/{record['outcome']}: a "
                       f"name or number outside its enumeration, which "
                       f"the allowlist refuses (section 7)")
            continue
        kind, streams, representation, ranged, zero, outcomes = row
        if (record["type"], record["repr"]) != (kind, representation) or \
                record["stream"] not in streams or \
                record["outcome"] not in outcomes:
            out.append(f"{at(index)}{name} as {record['type']}, stream "
                       f"{record['stream']}, {record['repr']}, "
                       f"{record['outcome']}: outside its row of 2.7")
        if not ranged and (record["base"] or record["length"]):
            out.append(f"{at(index)}{name} has a range, which its row has "
                       f"not")
        if zero and record["digest"] != ZERO:
            out.append(f"{at(index)}{name}'s digest is not zero")
        if name != "close" and record["expected"]:
            out.append(f"{at(index)}expected={record['expected']} in a "
                       f"record other than the close")
        wanted = 0 if name == "close" else counts.get(record["stream"], 0)
        if record["srec"] != wanted:
            out.append(f"{at(index)}srec={record['srec']} is not the "
                       f"{wanted} earlier records of stream "
                       f"{record['stream']}")
        if name != "close":
            counts[record["stream"]] = counts.get(record["stream"], 0) + 1
    closes = [index for index, record in enumerate(records)
              if record["object"] == "close"]
    state = header["state"]
    if state == "closed" and (not records or
                              records[-1]["object"] != "close"):
        out.append("the log is closed without a close as its last record")
    for index in closes:
        if index != len(records) - 1:
            out.append(f"{at(index)}a close that is not the last record")
        if records[index]["expected"] != header["count"]:
            out.append(f"{at(index)}the close's expected="
                       f"{records[index]['expected']} is not the count "
                       f"{header['count']}")
        if state != "closed":
            out.append(f"{at(index)}a close in an {state} log")
    if state == "overflow" and header["count"] != CAPACITY - 1:
        out.append(f"an overflow log with count {header['count']}, not "
                   f"{CAPACITY - 1}")
    identities = [record for record in records
                  if record["object"] == "configuration-identity"]
    absent = [record for record in records
              if record["object"] == "policy-absent"]
    if bool(identities) == bool(absent) and records:
        out.append("the log holds both or neither of configuration-identity "
                   "and policy-absent")
    elif identities and header["config"] != identities[0]["digest"]:
        out.append("the header's config is not the configuration-identity "
                   "record's digest")
    elif absent and header["config"] != ZERO:
        out.append("the header's config is not zero beside policy-absent")
    return out


class Rebuilt:
    """The log as hart 0's lines give it: the block's place, the header,
    the records, the registers lines, the LAUNCH lines, and the findings
    that refuse the rebuild."""

    def __init__(self):
        self.findings, self.records = [], []
        self.header = self.block = self.barrier = self.terminal = None
        self.launches, self.lines, self.volume = [], 0, 0
        self.replayed = replay([])

    @property
    def closed(self):
        return bool(self.header and self.header["state"] == "closed" and
                    self.records and self.records[-1]["object"] == "close")


def parse_fields(match, names, line, out):
    """A matched line's fields by NAMES, decimals as integers and checked
    against their widths."""
    values = {}
    for name, text in zip(names, match.groups()):
        if name in WIDTHS:
            values[name] = int(text)
            if values[name] >> WIDTHS[name]:
                out.append(f"line {line.number}: {name}={text} is wider "
                           f"than its {WIDTHS[name]}-bit field")
        elif name in ("base", "length", "alg"):
            values[name] = int(text, 16)
        else:
            values[name] = text
    return values


def rebuild(monitor):
    """4.6's rebuild of MONITOR, hart 0's unprefixed lines (.number and
    .text): the block (the header line opening a contiguous run of
    BE_MVP:19 lines), its records, the two registers lines, the LAUNCH
    lines, the replay, and every finding that refuses the line set."""
    out = Rebuilt()
    texts = [line.text for line in monitor]
    nineteen = [index for index, text in enumerate(texts)
                if text.startswith("BE_MVP:19")]
    twenty = [index for index, text in enumerate(texts)
              if text.startswith("BE_MVP:20")]
    found = out.findings
    for index in nineteen + twenty:
        out.lines += 1
        out.volume += len(texts[index]) + 1
        if len(texts[index]) > LINE_LIMIT:
            found.append(f"line {monitor[index].number}: "
                         f"{len(texts[index])} characters, above the "
                         f"{LINE_LIMIT} hart 0's line buffer holds")
    if nineteen:
        first = last = nineteen[0]
        while last + 1 < len(texts) and texts[last + 1].startswith(
                "BE_MVP:19"):
            last += 1
        out.block = (first, last)
        found += [f"line {monitor[index].number}: a BE_MVP:19 line outside "
                  f"the block (more than one block, or one that is not "
                  f"contiguous)" for index in nineteen if index > last]
        match = HEADER_LINE.fullmatch(texts[first])
        if match:
            out.header = parse_fields(match, HEADER_FIELDS, monitor[first],
                                      found)
        else:
            found.append(f"line {monitor[first].number}: the block does not "
                         f"open with a header line of 4.2's form")
        numbers = {}
        for position, index in enumerate(range(first + 1, last + 1)):
            line = monitor[index]
            match = RECORD_LINE.fullmatch(line.text)
            if not match:
                found.append(f"line {line.number}: "
                             + ("a second header line in the block"
                                if line.text.startswith(
                                    "BE_MVP:19 LOG header") else
                                "not a record line of 4.3's form"))
                continue
            record = parse_fields(match, RECORD_FIELDS, line, found)
            if record["seq"] != position:
                found.append(f"line {line.number}: seq={record['seq']} is "
                             f"not the line's position {position} in the "
                             f"block")
            numbers[len(out.records)] = line.number
            out.records.append(record)
        if out.header:
            if last - first != out.header["count"]:
                found.append(f"line {monitor[first].number}: "
                             f"{last - first} record lines, not the "
                             f"header's count={out.header['count']}")
            found += structure(out.header, out.records, lambda index:
                               numbers.get(index, monitor[first].number
                                           if index < 0 else None))
    for index in twenty:
        line, text = monitor[index], texts[index]
        barrier = BARRIER_LINE.fullmatch(text)
        terminal = TERMINAL_LINE.fullmatch(text)
        if not (barrier or terminal):
            found.append(f"line {line.number}: " + (
                "the barrier's registers line without its ticks" if
                text.startswith("BE_MVP:20 REGISTERS at=barrier ") and
                " ticks=" not in text else
                "the terminal registers line with ticks" if
                text.startswith("BE_MVP:20 REGISTERS at=terminal ") and
                " ticks=" in text else
                "not a registers line of 4.4's form"))
            continue
        which = "barrier" if barrier else "terminal"
        if getattr(out, which) is not None:
            found.append(f"line {line.number}: a second {which} registers "
                         f"line")
            continue
        groups = (barrier or terminal).groups()
        setattr(out, which, (index, list(groups[:4]),
                             groups[4] if barrier else None))
    if out.barrier:
        index = out.barrier[0]
        if not out.closed:
            found.append(f"line {monitor[index].number}: the barrier's "
                         f"registers line, but the log is not closed")
        if not out.block or index != out.block[1] + 1:
            found.append(f"line {monitor[index].number}: the barrier's "
                         f"registers line does not immediately follow the "
                         f"block")
    if out.terminal:
        index = out.terminal[0]
        if not out.barrier:
            found.append(f"line {monitor[index].number}: a terminal "
                         f"registers line without the barrier's")
        if index + 1 >= len(texts) or not texts[index + 1].startswith(
                ("BE_MVP:14 ", "BE_MVP:FAIL ")):
            found.append(f"line {monitor[index].number}: the terminal "
                         f"registers line does not immediately precede "
                         f"hart 0's terminal line")
    for index, text in enumerate(texts):
        if text.startswith("BE_MVP:06 LAUNCH"):
            match = LAUNCH_LINE.fullmatch(text)
            if not match:
                found.append(f"line {monitor[index].number}: not a LAUNCH "
                             f"line of 4.8's form")
                continue
            out.launches.append((index, int(match.group(1)),
                                 int(match.group(2)), match.group(3),
                                 match.group(4)))
    out.replayed = replay(out.records)
    for which in ("barrier", "terminal"):
        printed = getattr(out, which)
        for register, (got, wanted) in enumerate(zip(
                printed[1] if printed else (), out.replayed)):
            if got != wanted:
                found.append(f"line {monitor[printed[0]].number}: the "
                             f"{which}'s r{register} does not replay: "
                             f"printed {got[:16]}..., the records give "
                             f"{wanted[:16]}... (unprotected)")
    return out


# ------------------------------------------------ the checker's judgment
class Inputs:
    """What the checker recomputes every digest from (4.7): the run's boot
    image (BOOT), the build inputs under build/mvp/ (READ(source) -> bytes),
    the scenario's secret, and the generator's canonical data: the core
    identity (CORE), each domain's console grant (GRANTS), the report's
    identities (IDENTITIES, by object), and the scenario's SHA-256."""

    def __init__(self, boot=None, read=None, secret=None, core=None,
                 grants=None, identities=None, scenario=None):
        self.boot, self.read, self.secret = boot, read, secret
        self.core, self.grants = core, grants
        self.identities, self.scenario = identities or {}, scenario

    def boot_sha256(self):
        return None if self.boot is None else sha256(self.boot)

    def qemu_copy_sha256(self):
        """The boot image's SHA-256 with its text_offset the board's, when
        it is the U-Boot rehearsal's QEMU-only copy (header bytes 8 to 15
        QEMU's text_offset, no other byte changed)."""
        # PROFILE READING (4.7, 5.3): the reference's boot_image_sha256 is
        # the board image's; the U-Boot rehearsal boots a QEMU-only copy
        # differing in the header's text_offset alone, which binds to the
        # same reference when that field, put back, gives its SHA-256.
        if self.boot is None or len(self.boot) < 16 or struct.unpack_from(
                "<Q", self.boot, 8)[0] != QEMU_TEXT_OFFSET:
            return None
        return sha256(self.boot[:8] + struct.pack("<Q", BOARD_TEXT_OFFSET) +
                      self.boot[16:])

    def range_digest(self, offset, length):
        require(self.boot is not None, "no boot image to recompute the "
                "monitor's ranges from")
        require(MONITOR_OFFSET <= offset and offset + length <=
                min(MONITOR_OFFSET + MONITOR_BYTES, len(self.boot)),
                f"0x{offset:x}+0x{length:x} lies outside the boot image's "
                f"monitor")
        return sha256(self.boot[offset:offset + length])

    def source_digest(self, source, length):
        if source == "scenario-secret":
            require(self.secret is not None and len(self.secret) <= length,
                    "no scenario secret to place in the page")
            data = self.secret.ljust(length, b"\0")
        else:
            require(self.read is not None, f"no build input {source}")
            data = self.read(source)
        require(len(data) == length, f"{source} holds {len(data)} bytes, "
                f"not the range's {length}")
        return sha256(data)

    def computed(self, name):
        """A configuration record's digest from the canonical data."""
        if name == "core-identity":
            return self.core
        if name == "console-grants":
            return None if self.grants is None else sha256(bytes(
                1 if grant else 0 for grant in self.grants))
        return self.identities.get(name)


def read_build(root):
    """READ for Inputs: a source under ROOT (build/mvp/), refused unless
    it is of section 7's form and stays inside ROOT; at most 8 MiB."""
    root = pathlib.Path(root).resolve()

    def read(source):
        parts = source.split("/")
        require(all(SOURCE_PART.fullmatch(part) and part not in (".", "..")
                    for part in parts), f"the source {source[:60]!r} is not "
                "a path relative to build/mvp/")
        path = (root / source).resolve()
        require(path.is_relative_to(root) and path.is_file(),
                f"the build input {source} is not a file under {root}")
        require(path.stat().st_size <= 8 << 20, f"{source} is above 8 MiB")
        return path.read_bytes()
    return read


def policy_tool(path=POLICY_TOOL):
    spec = importlib.util.spec_from_file_location("mvp_policy_check_log",
                                                  path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def core_identity(expect, scenario, layout, policy):
    """The core identity from the generator's canonical inputs: the policy
    tool's core() over the expectation's binding (a v1 variant's hart as
    the generator changes it) and a v2 or v3 manifest's pages, as
    tools/gen-scenario.py's core_config() and core_of() give it."""
    try:
        domains = [dict(domain, hart=hart) for domain, hart in zip(
            expect["domains"], log_harts(expect))]
        version = EXPECT_SCHEMAS[expect["schema"]]
        pages = policy.core_inputs(scenario, policy.manifest(scenario))[1] \
            if version != "v1" else []
        return policy.core([dict(domain, rights=WINDOW_RIGHTS)
                            for domain in domains], pages, layout)["identity"]
    except Exception as error:  # the policy tool's own refusals, any type
        raise Refused(f"the core identity cannot be computed: "
                      f"{type(error).__name__}: {error}") from None


def console_grants(expect, scenario):
    """Each domain's console-input grant (2.8): a console variant's grants
    (its expectation's console_input section) or the scenario's own."""
    count = len(expect["domains"])
    section = expect.get("console_input")
    if section is not None:
        grants = section.get("grants")
        require(isinstance(grants, list) and all(
            integer(index) and 0 <= index < count for index in grants),
            "the expectation's console_input.grants are not domain indices")
        return [index in grants for index in range(count)]
    domains = scenario.get("domains")
    require(isinstance(domains, list) and len(domains) == count and all(
        isinstance(domain.get("console_input"), bool) for domain in domains),
        "the scenario's domains do not each grant console input or not")
    return [domain["console_input"] for domain in domains]


def scenario_inputs(expect, report, boot, root, layout, mvp_dir=MVP_DIR):
    """Inputs for a capture of EXPECT's image: its boot image (BOOT, bytes
    or None), the build root ROOT, the scenario file (its SHA-256 the
    expectation's), the report's identities, and the core identity and
    console grants from the generator's canonical inputs."""
    path = mvp_dir / "scenarios" / expect["scenario"] / "scenario.json"
    data = path.read_bytes()
    scenario = strict_json(data, f"scenarios/{expect['scenario']}",
                           limit=1 << 20, floats=True)
    secret = scenario.get("secret", {}).get("hex")
    identities = {}
    if report is not None:
        identity = report.get("identity", {})
        identities = {"configuration-identity":
                      identity.get("configuration_identity"),
                      "policy-identity": identity.get("policy_identity")}
    return Inputs(boot=boot, read=read_build(root),
                  secret=bytes.fromhex(secret) if secret else None,
                  core=core_identity(expect, scenario, layout,
                                     policy_tool(mvp_dir / "tools" /
                                                 "policy-check.py")),
                  grants=console_grants(expect, scenario),
                  identities=identities, scenario=sha256(data))


def is_log_line(text):
    """A line the log module judges and the walk does not: BE_MVP:19,
    BE_MVP:20, and BE_MVP:06 LAUNCH."""
    return text.startswith(LOG_TAGS)


def without_log(expect):
    """EXPECT for the walk: its control, per-domain, and final lines
    without the log's templates, which judge() holds instead; and a
    failure declared after a log line (wrong-measurement's, after
    BE_MVP:19) declared after the walk's line the generator placed the
    log after, the log's own place judge() holding (class_findings(): the
    gate-fail's BE_MVP:FAIL immediately after its block)."""
    def keep(entries):
        return [entry for entry in entries
                if not is_log_line(entry["template"])]
    entries = expect.get("control_lines", [])
    out = dict(expect, control_lines=keep(entries),
               final_lines=keep(expect.get("final_lines", [])))
    if "domain_control_lines" in expect:
        out["domain_control_lines"] = {
            domain: keep(items) for domain, items in
            expect["domain_control_lines"].items()}
    outcome = expect.get("outcome") or {}
    if outcome.get("after") in LOG_MARKERS:
        first = next((index for index, entry in enumerate(entries)
                      if is_log_line(entry["template"])), len(entries))
        before = keep(entries[:first])
        out["outcome"] = dict(outcome, after=before[-1]["template"].split(
            " ", 1)[0] if before else "none")
    return out


def default_paths(root, toolchain, expect):
    """The reference and boot image of EXPECT's image as the build lays
    them out (mvp/Makefile): references/TOOLCHAIN/IMAGE.json, and the
    boot image of the scenario (two-guests', no-sstc's, and sbi-3.0's
    under TOOLCHAIN/, te-poc's and anchor's under TOOLCHAIN/SCENARIO/), a
    variant (variants/TOOLCHAIN/VARIANT/), or a probe (probes/TOOLCHAIN/
    PROBE/); an explicit --reference or --image takes their place."""
    root, image = pathlib.Path(root), expect["image"]
    scenario = expect["scenario"]
    if (expect.get("outcome") or {}).get("probe"):
        boot = root / "probes" / toolchain / image
    elif image == scenario or image in SCENARIO_IMAGE_RUNS:
        boot = root / toolchain / ("" if scenario == "two-guests" else
                                   scenario)
    else:
        boot = root / "variants" / toolchain / image
    return (root / "references" / toolchain / f"{image}.json",
            boot / "be-mvp-boot.img")


def first(texts, prefix, start=0):
    return next((index for index in range(start, len(texts))
                 if texts[index].startswith(prefix)), None)


def judge(monitor, expect, reference, inputs, toolchain):
    """The log module's judgment of one capture: (findings, the self-report
    findings this run declares, the record, the export or None). MONITOR,
    hart 0's unprefixed lines; EXPECT, the expectation with M9's log data;
    REFERENCE, a Reference or None; INPUTS, an Inputs."""
    findings, self_report = [], []
    record = {"reference": None if reference is None else reference.sha256,
              "registers": None, "export_sha256": None}
    try:
        contract = contract_of(expect)
    except Refused as error:
        return [f"log: {error}"], [], record, None
    record["contract"] = {"sequence": contract[0], "run": contract[1]}
    rebuilt = rebuild(monitor)
    findings += rebuilt.findings
    texts = [line.text for line in monitor]
    record.update(
        state=rebuilt.header and rebuilt.header["state"],
        count=rebuilt.header and rebuilt.header["count"],
        lines=rebuilt.lines, volume_bytes=rebuilt.volume,
        registers={"barrier": rebuilt.barrier and rebuilt.barrier[1],
                   "terminal": rebuilt.terminal and rebuilt.terminal[1],
                   "replayed": rebuilt.replayed,
                   "replayed_label": "unprotected"},
        ticks={"barrier": rebuilt.barrier and rebuilt.barrier[2],
               "launch": {str(domain): ticks for _, domain, _, _, ticks
                          in rebuilt.launches}},
        launch={str(domain): register for _, domain, _, register, _
                in rebuilt.launches})
    findings += order_findings(rebuilt, monitor, texts)
    if reference is None:
        findings.append("log: no reference manifest (--reference) to "
                        "compare the log with")
        return findings, self_report, record, None
    record["r2"] = reference.r2
    findings += binding_findings(expect, reference, contract, inputs,
                                 toolchain, record)
    if reference.contract != contract:
        return findings, self_report, record, None
    run = contract[1]
    if run == "pre-measurement":
        if rebuilt.lines or rebuilt.launches:
            findings.append("log: a pre-measurement run whose declared "
                            "prefix is empty printed BE_MVP:19, :20, or "
                            "LAUNCH lines (3.2)")
        return findings, self_report, record, None
    if rebuilt.block is None:
        findings.append(f"log: no BE_MVP:19 block, which the {run} class "
                        f"requires (3.2)")
        return findings, self_report, record, None
    want_header, want = dict(reference.header), [
        dict(item) for item in reference.records]
    if run == "gate-fail":
        failing = reference.failing
        gate = next(index for index, item in enumerate(want)
                    if item["outcome"] == "gated-pass" and
                    item["stream"] == 2 + failing)
        want = want[:gate + 1]
        want[-1]["outcome"] = "gated-fail"
        want_header.update(state="open", count=len(want))
    found, self_report, comparison = compare(rebuilt, monitor, want_header,
                                             want, run)
    findings += found
    record["records"] = comparison
    findings += recompute(rebuilt, monitor, reference, inputs, record)
    findings += launch_findings(rebuilt, monitor, expect, reference,
                                contract)
    findings += class_findings(rebuilt, monitor, texts, expect, reference,
                               contract)
    # Stream 0 is a self-report (4.7): its difference is one finding per
    # record, and self-report-flip's declared outcome is exactly the one.
    # PROFILE READING (3.2, 4.7; D-4): that run's verdict is PASS when its
    # self-report findings are exactly [FLIP_FINDING]; the finding is
    # returned as declared (the report's BE_MVP_LOG_SELF_REPORT ...
    # (declared) line), not as a failure, and any other self-report
    # finding, or none, fails the run.
    record["self_report"] = self_report
    if run != "self-report-flip":
        findings += self_report
        self_report = []
    elif self_report != [FLIP_FINDING]:
        findings.append(f"log: the self-report-flip run's self-report "
                        f"findings are {self_report}, not exactly "
                        f"[{FLIP_FINDING!r}] (D-4)")
        self_report = []
    value = None
    if not rebuilt.findings and rebuilt.header:
        value = export(rebuilt.header, rebuilt.records,
                       rebuilt.barrier and rebuilt.barrier[1],
                       rebuilt.terminal and rebuilt.terminal[1])
        record["export_sha256"] = sha256(render(value))
    return findings, self_report, record, value


def order_findings(rebuilt, monitor, texts):
    """The global rule (D-1, I20): every BE_MVP:19 line and the barrier's
    registers before BE_MVP:07; each domain's LAUNCH line and gate record
    before its HART_STARTED; and no BE_MVP:07 or HART_STARTED without a
    closed log."""
    # PROFILE READING (4.5, 4.6; I20): a BE_MVP:07 or HART_STARTED line in
    # a run whose log did not close is a finding of its own, whatever the
    # run class, since no domain hart starts unless the log closed.
    out = []
    published = first(texts, "BE_MVP:07 ")
    started = {}
    for index, text in enumerate(texts):
        match = STARTED.match(text)
        if match:
            started.setdefault(int(match.group(1)), index)
    if (published is not None or started) and not rebuilt.closed:
        out.append("log: BE_MVP:07 or a HART_STARTED line, but the log is "
                   "not closed: no domain hart starts unless the log "
                   "closed (I20)")
    if published is not None:
        late = [index for index, text in enumerate(texts) if index >
                published and text.startswith(("BE_MVP:19", "BE_MVP:20 "
                                               "REGISTERS at=barrier"))]
        out += [f"line {monitor[index].number}: a log line after "
                f"BE_MVP:07" for index in late]
    for index, domain, _, _, _ in rebuilt.launches:
        if domain in started and started[domain] < index:
            out.append(f"line {monitor[index].number}: domain {domain}'s "
                       f"LAUNCH line after its HART_STARTED")
    if rebuilt.block:
        gates = {record["stream"] - 2: rebuilt.block[0] + 1 + position
                 for position, record in enumerate(rebuilt.records)
                 if record["outcome"] == "gated-pass"}
        out += [f"line {monitor[index].number}: domain {domain}'s gate "
                f"record after its HART_STARTED" for domain, index in
                gates.items() if domain in started and
                started[domain] < index]
    return out


def binding_findings(expect, reference, contract, inputs, toolchain,
                     record):
    """4.7's last rule and the reference's identity: the image, scenario,
    variant, toolchain, contract, R2 state, report, scenario digest, and
    boot image are this run's."""
    out = []
    probe = bool((expect.get("outcome") or {}).get("probe"))
    image, scenario = expect["image"], expect["scenario"]
    variant = None if image == scenario or probe else image
    if (reference.image, reference.scenario, reference.variant) != (
            image, scenario, variant):
        out.append(f"log: the reference is {reference.image}'s (variant "
                   f"{reference.variant}), not this run's {image} (variant "
                   f"{variant})")
    if toolchain is None:
        out.append("log: no --toolchain to bind the run to its reference")
    elif reference.toolchain != toolchain:
        out.append(f"log: the reference is the {reference.toolchain} "
                   f"image's, not the {toolchain} run's")
    if reference.contract != contract:
        out.append(f"log: the reference's contract is "
                   f"{'/'.join(reference.contract)}, not the expectation's "
                   f"{'/'.join(contract)}")
    # The expectation's log section, every field, against what the
    # reference implies (expectation_log()): the generator's expected
    # records, registers, constants, and lines and the reference must be
    # one log.
    section, outcome = expect.get("log") or {}, expect.get("outcome") or {}
    if reference.contract == contract:
        want = expectation_log(reference, log_harts(expect),
                               bool(outcome.get("fallback")),
                               section.get("mutate"))
        out += [f"log: the expectation's log section is not the "
                f"reference's: {difference}" for difference in
                differences(want, section, "log")]
    if contract[1] == "gate-fail" and reference.contract == contract and \
            outcome.get("domain") != reference.failing:
        out.append(f"log: the expectation's failing domain "
                   f"{outcome.get('domain')} is not the reference's "
                   f"{reference.failing}")
    if reference.report != (expect.get("report") or {}).get("sha256"):
        out.append("log: the reference's authority report is not the "
                   "expectation's")
    if reference.header["scenario"] != expect.get("scenario_sha256") or \
            inputs.scenario not in (None, expect.get("scenario_sha256")):
        out.append("log: the scenario digest of the reference, the "
                   "expectation, or the scenario file differs")
    boot = inputs.boot_sha256()
    record["boot_image"] = "absent"
    if boot is None:
        out.append("log: no boot image (--image) to bind the run to the "
                   "reference's")
    elif contract[1] == "self-report-flip":
        record["boot_image"] = "mutated" if boot == reference.mutated \
            else "other"
        if boot != reference.mutated:
            out.append("log: the run's boot image is not the reference's "
                       "mutated_image_sha256")
    elif boot == reference.boot:
        record["boot_image"] = "nominal"
    elif inputs.qemu_copy_sha256() == reference.boot:
        record["boot_image"] = "qemu-only copy"
    else:
        record["boot_image"] = "other"
        out.append(f"log: the run's boot image {boot[:16]}... is not the "
                   f"reference's {reference.boot[:16]}...")
    return out


def compare(rebuilt, monitor, want_header, want, run):
    """4.7's field comparison: the header's every field, the records'
    objects and streams against the class's prefix, then every field of
    each record, srec among them. A stream-0 record whose digest alone
    differs is the self-report finding."""
    # PROFILE READING (4.6, 4.7): the printed registers are compared with
    # the replay (rebuild()), and the records, digests included, field by
    # field with the reference's; the reference's registers then follow,
    # so no third comparison of the printed registers with the reference's
    # is made, which would only repeat a finding the records already give.
    out, self_report, rows = [], [], []
    header, records = rebuilt.header, rebuilt.records
    opening = monitor[rebuilt.block[0]].number
    def shown(name, value):
        return f"0x{value:04x}" if name == "alg" else value
    if header:
        out += [f"line {opening}: header {name}={shown(name, header[name])}"
                f" is not the reference's {shown(name, want_header[name])}"
                for name in HEADER_FIELDS if header[name] != want_header[name]]
    got = [(item["object"], item["stream"]) for item in records]
    wanted = [(item["object"], item["stream"]) for item in want]
    if got != wanted:
        at = next((index for index, pair in enumerate(zip(got, wanted))
                   if pair[0] != pair[1]), min(len(got), len(wanted)))
        out.append(
            f"log: record {at} is {got[at][0]} (stream {got[at][1]}), "
            f"where the {run} prefix has {wanted[at][0]} (stream "
            f"{wanted[at][1]})" if at < min(len(got), len(wanted)) else
            f"log: the log lacks {wanted[at][0]} (stream {wanted[at][1]}), "
            f"which the {run} prefix requires" if at < len(wanted) else
            f"log: the log holds {got[at][0]} (stream {got[at][1]}), which "
            f"the {run} prefix does not list")
    for index, (item, other) in enumerate(zip(records, want)):
        number = monitor[rebuilt.block[0] + 1 + index].number
        differ = [name for name in RECORD_FIELDS
                  if item[name] != other[name]]
        rows.append({"recnum": index, "object": item["object"],
                     "stream": item["stream"], "fields": "equal" if not
                     differ else "differ: " + ",".join(differ)})
        for name in differ:
            if name == "digest" and item["stream"] == 0 and \
                    item["object"] == other["object"]:
                self_report.append(f"self-report differs: {item['object']}")
                continue
            shown = (hex64(item[name]), hex64(other[name])) \
                if name in ("base", "length") else \
                (item[name][:16] + "...", other[name][:16] + "...") \
                if name == "digest" else (item[name], other[name])
            out.append(f"line {number}: {item['object']} {name}={shown[0]} "
                       f"is not the reference's {shown[1]}")
    return out, self_report, rows


def recompute(rebuilt, monitor, reference, inputs, record):
    """4.7: each printed digest against the checker's own, from the boot
    image at the recorded range (R2), the build input the reference names
    (R4), or the generator's canonical data (R3); and the reference's own
    digests against the same inputs, for an image that is the reference's."""
    out, nominal = [], record.get("boot_image") in ("nominal",
                                                    "qemu-only copy")
    rows = record.get("records") or []
    for index, item in enumerate(rebuilt.records):
        number = monitor[rebuilt.block[0] + 1 + index].number
        name = item["object"]
        row = rows[index] if index < len(rows) else {}
        domain = item["stream"] - 2 if item["stream"] in (2, 3) else None
        try:
            if name in R2:
                own = inputs.range_digest(
                    item["base"] - MONITOR_HPA + MONITOR_OFFSET,
                    item["length"])
                source = "the boot image's bytes at its range"
            elif name in ("kernel-image", "device-tree", "secret-page"):
                source = reference.sources.get((name, domain))
                require(source is not None, f"the reference names no "
                        f"source for domain {domain}'s {name}")
                own = inputs.source_digest(source, item["length"])
            elif name in ("core-identity", "console-grants",
                          "configuration-identity", "policy-identity"):
                own = inputs.computed(name)
                source = "the generator's canonical data"
                require(own is not None, f"no canonical value for {name}")
            else:
                continue
        except Refused as error:
            out.append(f"line {number}: {name}'s digest cannot be "
                       f"recomputed: {error}")
            row["recomputed"] = "cannot"
            continue
        row["recomputed"] = "equal" if own == item["digest"] else "differs"
        if own != item["digest"]:
            out.append(f"line {number}: {name}'s printed digest "
                       f"{item['digest'][:16]}... is not the checker's own "
                       f"{own[:16]}... from {source}")
    for entry in reference.value["ranges"]:
        try:
            if entry["domain"] is None:
                if not nominal:
                    continue
                own = inputs.range_digest(int(entry["image_offset"], 16),
                                          int(entry["length"], 16))
            else:
                own = inputs.source_digest(entry["source"],
                                           int(entry["length"], 16))
        except Refused as error:
            out.append(f"log: the reference's {entry['object']} cannot be "
                       f"recomputed: {error}")
            continue
        if own != entry["digest"]:
            out.append(f"log: the reference's {entry['object']} digest "
                       f"{entry['digest'][:16]}... is not its "
                       f"{entry['source']}'s {own[:16]}...")
    for item in reference.records:
        own = inputs.computed(item["object"]) if item["object"] in (
            "core-identity", "console-grants", "configuration-identity",
            "policy-identity") else item["digest"]
        if own is not None and own != item["digest"]:
            out.append(f"log: the reference's {item['object']} is not the "
                       f"generator's canonical value")
    return out


def launch_findings(rebuilt, monitor, expect, reference, contract):
    """4.5 and 4.7: one LAUNCH line per domain whose gate passed, in domain
    order, immediately before the block; its hart the domain's; its
    register the reference's launch_expected and its stream's replay."""
    # PROFILE READING (4.5 path 1): the LAUNCH lines are contiguous, in
    # domain order, and end on the line before the block's header; a
    # gate-fail run prints one for each domain before the failing one.
    out, launched = [], [] if contract[0] == "probe" else [0, 1]
    if contract[1] == "gate-fail":
        launched = launched[:reference.failing]
    found = [domain for _, domain, _, _, _ in rebuilt.launches]
    if found != launched:
        out.append(f"log: LAUNCH lines for domains {found}, where the "
                   f"{contract[1]} class has {launched}")
    if rebuilt.launches and rebuilt.block:
        indices = [index for index, _, _, _, _ in rebuilt.launches]
        if indices != list(range(rebuilt.block[0] - len(indices),
                                 rebuilt.block[0])):
            out.append(f"line {monitor[indices[0]].number}: the LAUNCH "
                       f"lines do not immediately precede the block")
    harts = log_harts(expect)
    for index, domain, hart, register, _ in rebuilt.launches:
        number = monitor[index].number
        if domain >= len(harts) or hart != harts[domain]:
            out.append(f"line {number}: LAUNCH domain={domain} hart={hart} "
                       f"is not a domain's binding")
            continue
        if domain < len(reference.launch) and \
                register != reference.launch[domain]:
            out.append(f"line {number}: domain {domain}'s LAUNCH register "
                       f"is not the reference's launch_expected")
        if register != rebuilt.replayed[2 + domain]:
            out.append(f"line {number}: domain {domain}'s LAUNCH register "
                       f"is not its stream's replay (unprotected)")
    return out


def class_findings(rebuilt, monitor, texts, expect, reference, contract):
    """3.2's per-class lines beside the block: the barrier and the
    terminal registers, BE_MVP:07 after the barrier, a gate-fail's
    BE_MVP:FAIL measurement and DETAIL, and each DOMAIN_TERMINATED line's
    launch register."""
    out, run = [], contract[1]
    last = rebuilt.block[1]
    if run == "gate-fail":
        if rebuilt.barrier or rebuilt.terminal:
            out.append("log: registers lines in a gate-fail run, which "
                       "prints none (4.5)")
        failing = reference.failing
        if last + 1 >= len(texts) or \
                texts[last + 1] != "BE_MVP:FAIL measurement":
            out.append("log: BE_MVP:FAIL measurement does not immediately "
                       "follow the gate-fail block")
        detail = DETAIL_LINE.fullmatch(texts[last + 2]) \
            if last + 2 < len(texts) else None
        if detail is None:
            out.append("log: the gate-fail run has no DETAIL line with "
                       "both values after BE_MVP:FAIL measurement")
            return out
        computed, wanted = detail.group(3), detail.group(4)
        hart = log_harts(expect)[failing]
        if (int(detail.group(1)), int(detail.group(2))) != (failing, hart):
            out.append(f"line {monitor[last + 2].number}: the DETAIL names "
                       f"domain {detail.group(1)} hart {detail.group(2)}, "
                       f"not the failing domain {failing} on hart {hart}")
        if computed != rebuilt.replayed[2 + failing]:
            out.append(f"line {monitor[last + 2].number}: the DETAIL's "
                       f"computed= is not the failing stream's replay "
                       f"(unprotected)")
        if wanted != reference.launch[failing]:
            out.append(f"line {monitor[last + 2].number}: the DETAIL's "
                       f"expected= is not the reference's launch_expected")
        if flip(computed) != wanted:
            out.append(f"line {monitor[last + 2].number}: computed= and "
                       f"expected= differ elsewhere than bit 0 of the "
                       f"first byte (Q16)")
        return out
    if rebuilt.barrier is None:
        out.append(f"log: no barrier registers line, which the {run} class "
                   f"requires")
    elif rebuilt.barrier[0] + 1 >= len(texts) or not texts[
            rebuilt.barrier[0] + 1].startswith("BE_MVP:07 "):
        out.append(f"line {monitor[rebuilt.barrier[0]].number}: BE_MVP:07 "
                   f"does not immediately follow the barrier's registers")
    # PROFILE READING (4.5): the barrier's line is followed at once by
    # BE_MVP:07, and the terminal line precedes BE_MVP:14 (complete,
    # self-report-flip) or a post-launch failure's first BE_MVP:FAIL at
    # once; the ring-full fallback, which prints none, is a post-launch
    # failure whose expectation's log.terminal is none (outcome.fallback,
    # which binding_findings() holds to it).
    fallback = run == "post-launch-failure" and \
        (expect.get("log") or {}).get("terminal") == "none"
    if fallback:
        if rebuilt.terminal:
            out.append("log: a terminal registers line in the ring-full "
                       "fallback, where hart 0 prints no terminal line")
    elif rebuilt.terminal is None:
        out.append(f"log: no terminal registers line, which the {run} "
                   f"class requires before hart 0's terminal line")
    else:
        after = texts[rebuilt.terminal[0] + 1] if \
            rebuilt.terminal[0] + 1 < len(texts) else ""
        terminal = first(texts, "BE_MVP:FAIL ") if run == \
            "post-launch-failure" else first(texts, "BE_MVP:14 ")
        if terminal != rebuilt.terminal[0] + 1:
            out.append(f"line {monitor[rebuilt.terminal[0]].number}: the "
                       f"terminal registers line precedes {after[:30]!r}, "
                       f"not the {run} run's " +
                       ("first BE_MVP:FAIL" if run == "post-launch-failure"
                        else "BE_MVP:14"))
    for index, text in enumerate(texts):
        match = TERMINATED_LINE.fullmatch(text)
        if not match:
            continue
        domain, value = int(match.group(2)), match.group(5)
        if domain > 1 or value != rebuilt.replayed[2 + domain] or \
                domain >= len(reference.launch) or \
                value != reference.launch[domain]:
            out.append(f"line {monitor[index].number}: DOMAIN_TERMINATED "
                       f"sha256={value[:16]} is not domain {domain}'s "
                       f"launch register (D-9)")
    return out


# --------------------------------------------------------------- self-test
# Section 5.4's example and 2.10's vectors, pinned as the profile gives
# them: the page's SHA-256, the export's and the reference's canonical
# files (bytes, SHA-256), the :19 and :20 text's bytes, and 2.8's digests.
EXAMPLE_PAGE = \
    "4435113d8276c4444630b2be8fd3ff60929f68723a121b8c6574f049488b1184"
EXAMPLE_EXPORT = (
    8153, "2337149b55e10cf8b03e464638e686f7a2c0673dc6e8aadc48bfffc09b2142dc")
EXAMPLE_REFERENCE = (
    10993, "608dc4d4de3782cef2c8ca4c79e79865f4225aaee7df42a579e053f351b9a74c")
EXAMPLE_VOLUME = 4557
GRANT_DIGESTS = {
    (False, False):
    "96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7",
    (True, False):
    "47dc540c94ceb704a23875c11273e16bb0b8a87aed84de911f2133568115f254",
    (False, True):
    "b413f47d13ee2fe6c845b2ee141af81de858df4ec549a58b7970bb96645bc8d2",
    (True, True):
    "9dcf97a184f32623d11a73124ceb99a5709b083721e878a16d78f596718ba7b2"}
LABEL = "beryllium-log-profile-v1 example: "
PLACED = ("BE_MVP:06 PAYLOAD_PLACED domain={} kernel=0x80200000 "
          "kernel_bytes=0x1f7cc4 image_size=0x22bfb0 dtb=0x83e00000 "
          "dtb_bytes=0x1000 ticks=0x1000")
PUBLISHED = ("BE_MVP:07 BLOCKS_PUBLISHED region=0x102044000 bytes=0x20000 "
             "generation=1 budget_ticks=0x100000000")
HART_STARTED = ("BE_MVP:08 HART_STARTED hart={1} domain={0} result=0 "
                "status=0 ticks=0x2000")
RUN_COMPLETE = ("BE_MVP:13 RUN_COMPLETE domains=2 records=146 wakes=2 "
                "idle_ticks=0x10 overlap_ticks=0x100 ticks=0x1000")
SHUTDOWN = "BE_MVP:14 SHUTDOWN type=0 reason=0"
EXIT_DETAIL = ("BE_MVP:DETAIL domain=0 hart=1 cause=0x8 pc=0x80200000 "
               "tval=0x0 htval=0x0 htinst=0x0 spvp=1 vsatp=0x0 exits=64")
# The example's and the syntheses' R2 ranges (5.4's bases and lengths).
RANGES = (("monitor-text", 0x102000000, 0x4540),
          ("monitor-rodata", 0x102008610, 0x2e8),
          ("monitor-input", 0x102008000, 0x610),
          ("mvp-text", 0x102064000, 0x6a40),
          ("mvp-rodata", 0x10206aa40, 0x1238))
PLACEMENTS = {("kernel-image", 0): 0x110200000, ("device-tree", 0):
              0x113e00000, ("kernel-image", 1): 0x114200000,
              ("device-tree", 1): 0x117e00000, ("secret-page", 1):
              0x118002000}


class Line:
    """A capture's line as tests/check-capture.py gives it."""

    def __init__(self, number, text):
        self.number, self.text = number, text


def lines_of(texts):
    return [Line(number, text) for number, text in enumerate(texts, 1)]


def label(name):
    return sha256((LABEL + name).encode("ascii"))


def profile_example():
    """Section 5.4's lines and its two JSON displays, and 2.10's three
    dumps, as the profile prints them."""
    text = PROFILE.read_text(encoding="utf-8")
    section = text[text.index("### 5.4 Example"):
                   text.index("## 6. The mapping")]
    blocks = re.findall(r"```(text|json)\n(.*?)```", section, re.S)
    vectors = text[text.index("### 2.10 Test vectors"):
                   text.index("## 3. The per-image contract")]
    return (blocks[0][1].rstrip("\n").split("\n"),
            [body for kind, body in blocks if kind == "json"],
            re.findall(r"```text\n(.*?)```", vectors, re.S))


def dump(page, start, length):
    return "".join(f"{offset:04x}  " + " ".join(
        f"{byte:02x}" for byte in page[offset:offset + 16]) + "\n"
        for offset in range(start, start + length, 16))


class TableInputs(Inputs):
    """5.4's illustrative inputs: each digest a label's, looked up by the
    range or source the reference names; any other range or source gives
    a digest no record has."""

    def __init__(self, reference, **values):
        super().__init__(**values)
        self.digests = {(entry["image_offset"] or entry["source"],
                         entry["length"]): entry["digest"]
                        for entry in reference.value["ranges"]}
        self.boot_digest = reference.boot

    def boot_sha256(self):
        return self.boot_digest

    def qemu_copy_sha256(self):
        return None

    def range_digest(self, offset, length):
        return self.digests.get((hex64(offset), hex64(length)),
                                sha256(b"absent %x %x" % (offset, length)))

    def source_digest(self, source, length):
        return self.digests.get((source, hex64(length)),
                                sha256(b"absent %d" % length +
                                       source.encode()))


# The bit the synthetic self-report-flip variant flips, as the generator
# names its own (log.mutate).
SYNTH_MUTATE = {"bit": 0, "symbol": "be_mvp_log_canary"}


class Synth:
    """A synthetic run of one image's log: its header and records, and
    hart 0's stream around them in the run's SHAPE: complete, probe,
    post-launch, fallback, gate-fail, pre-measurement, or log-failure.
    The printed registers are the records' replay unless overridden."""

    def __init__(self, header, records, shape="complete", harts=(1, 2),
                 ticks=("0x10a2c0", "0x10a1f8"), barrier_ticks="0x2a3f10"):
        self.header, self.records = dict(header), [dict(record) for record
                                                   in records]
        self.shape, self.harts, self.ticks = shape, harts, ticks
        self.barrier_ticks, self.barrier, self.terminal = barrier_ticks, \
            None, None
        self.failing, self.extra, self.detail = 1, [], True

    def log(self):
        return [header_line(self.header)] + [record_line(record) for
                                             record in self.records]

    def texts(self):
        registers = replay(self.records)
        shape, harts = self.shape, self.harts
        if shape == "pre-measurement":
            return [PLACED.format(0), "BE_MVP:FAIL payload"]
        probe = shape == "probe"
        domains = [] if probe else [0, 1] if shape != "gate-fail" else \
            list(range(self.failing))
        texts = ([] if probe else [PLACED.format(domain)
                                   for domain in (0, 1)]) + [
            f"BE_MVP:06 LAUNCH domain={domain} hart={harts[domain]} "
            f"register={registers[2 + domain]} expected=match "
            f"ticks={self.ticks[domain]}" for domain in domains]
        texts += self.log()
        if shape == "gate-fail":
            failing = self.failing
            return texts + ["BE_MVP:FAIL measurement"] + (
                [f"BE_MVP:DETAIL domain={failing} hart={harts[failing]} "
                 f"computed={registers[2 + failing]} "
                 f"expected={flip(registers[2 + failing])}"]
                if self.detail else [])
        if shape == "log-failure":
            return texts + ["BE_MVP:FAIL log"] + self.extra
        texts += [registers_line("barrier", self.barrier or registers,
                                 self.barrier_ticks), PUBLISHED]
        texts += [HART_STARTED.format(domain, harts[domain])
                  for domain in ([0] if probe else [0, 1])] + self.extra
        terminal = registers_line("terminal", self.terminal or registers)
        if shape == "post-launch":
            return texts + [terminal, "BE_MVP:FAIL exit-budget",
                            EXIT_DETAIL]
        if shape == "fallback":
            return texts + ["BE_MVP:FAIL ring", EXIT_DETAIL]
        return texts + ([] if probe else [RUN_COMPLETE]) + [terminal,
                                                            SHUTDOWN]


def example_case():
    """5.4's te-poc example: its expectation, reference, inputs, and run,
    the run's log lines exactly the profile's."""
    lines, displays, _ = profile_example()
    reference = Reference(render(json.loads(displays[1])))
    inputs = TableInputs(reference, core=label("core-identity"),
                         grants=[False, False], scenario=label(
                             "scenario te-poc"),
                         identities={"configuration-identity":
                                     label("configuration-identity"),
                                     "policy-identity":
                                     label("policy-identity")})
    expect = {"image": "te-poc", "scenario": "te-poc",
              "schema": "be-mvp-expect-v2",
              "scenario_sha256": label("scenario te-poc"),
              "outcome": {"pass": True},
              "report": {"sha256": label("authority-report")},
              "domains": [{"index": 0, "hart": 1}, {"index": 1, "hart": 2}]}
    expect["log"] = expectation_log(reference, [1, 2])
    rebuilt = rebuild(lines_of(lines))
    run = Synth(rebuilt.header, rebuilt.records)
    return expect, reference, inputs, run, lines


def synthetic(sequence, image, scenario, run="complete", r2="kept",
              grants=(False, False), failing=1, flipped=False,
              canonical=None):
    """A synthetic build of IMAGE with true digests: a boot image whose
    monitor holds SHAKE-256 bytes, a kernel, two device trees, a secret,
    and the canonical values (CANONICAL's core, identities, scenario,
    report, and secret, where given, else seeded); (reference, inputs,
    header, records). FLIPPED: self-report-flip's mutated boot image, one
    bit flipped in mvp-rodata's range, the reference the nominal build's;
    a gate-fail's log ends at FAILING's gate."""
    canonical, seed = canonical or {}, image.encode()
    boot = bytes(MONITOR_OFFSET) + hashlib.shake_256(
        seed + b" monitor").digest(MONITOR_BYTES)
    kernel = hashlib.shake_256(seed + b" kernel").digest(0x2345)
    trees = [hashlib.shake_256(seed + b" tree %d" % domain).digest(4096)
             for domain in (0, 1)]
    secret = canonical.get("secret") or b"BE-MVP-M2-TEST-SECRET-0000000000"
    files = {"guest/Image": kernel, f"guest/{image}-g0.dtb": trees[0],
             f"guest/{image}-g1.dtb": trees[1]}
    values = {"scenario": canonical.get("scenario") or sha256(
        seed + b" scenario"), ("core-identity", None): canonical.get(
            "core") or sha256(seed + b" core"),
        ("console-grants", None): sha256(bytes(grants))}
    for name, base, length in RANGES:
        at = base - MONITOR_HPA + MONITOR_OFFSET
        values[name, None] = (base, length, sha256(boot[at:at + length]))
    identities = {}
    if sequence in ("v2", "v3"):
        identities = canonical.get("identities") or {
            name: sha256(seed + b" " + name.encode()) for name in (
                "configuration-identity", "policy-identity")}
        values.update({(name, None): value
                       for name, value in identities.items()})
    sources = {}
    for (name, domain), base in PLACEMENTS.items():
        data = kernel if name == "kernel-image" else secret.ljust(
            4096, b"\0") if name == "secret-page" else trees[domain]
        values[name, domain] = (base, len(data), sha256(data))
        sources[name, domain] = "scenario-secret" if \
            name == "secret-page" else "guest/Image" if \
            name == "kernel-image" else f"guest/{image}-g{domain}.dtb"
    mutated = None
    if flipped:
        at = 0x10206aa40 - MONITOR_HPA + MONITOR_OFFSET + 0x10
        mutated = boot[:at] + bytes([boot[at] ^ 1]) + boot[at + 1:]
    report = (canonical.get("report") or sha256(seed + b" report")) \
        if sequence in ("v2", "v3") else None
    meta = {"source": {"commit": "0123456789abcdef" * 2 + "01234567",
                       "tree_state": "clean"}, "image": image,
            "scenario": scenario, "toolchain": "gcc",
            "variant": None if image == scenario or sequence == "probe"
            else image, "authority_report_sha256": report,
            "elf_sha256": sha256(seed + b" elf"),
            "boot_image_sha256": sha256(boot),
            "mutated_image_sha256": mutated and sha256(mutated)}
    reference = Reference(render(build_reference(
        meta, sequence, run, r2, values, sources, failing)))

    def read(source):
        require(source in files, f"no build input {source}")
        return files[source]
    inputs = Inputs(boot=mutated or boot, read=read, secret=secret,
                    core=values["core-identity", None], grants=list(grants),
                    identities=identities, scenario=values["scenario"])
    header, records = expected_log(sequence, r2, values)
    if run == "gate-fail":
        gate = next(index for index, record in enumerate(records)
                    if record["outcome"] == "gated-pass" and
                    record["stream"] == 2 + failing)
        records = records[:gate + 1]
        records[-1]["outcome"] = "gated-fail"
        header.update(state="open", count=len(records))
    if flipped:
        at = 0x10206aa40 - MONITOR_HPA + MONITOR_OFFSET
        records[4]["digest"] = sha256(mutated[at:at + 0x1238])
    return reference, inputs, header, records


def synthesis(sequence, run="complete", r2="kept", grants=(False, False),
              image=None, failing=1, flipped=False, fallback=False):
    """synthetic()'s build of a scenario's image or variant, with its
    expectation (its log section as the generator writes it, from the
    reference, expectation_log()) and its run: (expectation, reference,
    inputs, run). FALLBACK: a post-launch failure in the ring-full
    fallback."""
    scenario = {"v1": "two-guests", "probe": "two-guests", "v2": "te-poc",
                "v3": "anchor"}[sequence]
    image = image or scenario
    reference, inputs, header, records = synthetic(
        sequence, image, scenario, run, r2, grants, failing, flipped)
    outcome = {"probe": True} if sequence == "probe" else \
        {"pass": True} if run in ("complete", "self-report-flip") else \
        {"fail": "measurement", "after": "BE_MVP:06", "domain": failing} \
        if run == "gate-fail" else \
        {"fail": "payload", "after": "BE_MVP:03"} if \
        run == "pre-measurement" else \
        dict({"fail": "ring" if fallback else "exit-budget",
              "after": "BE_MVP:10"}, **({"fallback": True} if fallback
                                       else {}))
    expect = {"image": image, "scenario": scenario,
              "schema": "be-mvp-expect-" + ("v1" if sequence == "probe"
                                            else sequence),
              "scenario_sha256": inputs.scenario, "outcome": outcome,
              "domains": [{"index": 0, "hart": 1}, {"index": 1, "hart": 2}]}
    expect["log"] = expectation_log(
        reference, [1, 2], fallback, dict(SYNTH_MUTATE) if
        run == "self-report-flip" else None)
    if reference.report:
        expect["report"] = {"sha256": reference.report}
    shape = {"probe": "probe"}.get(sequence, {
        "complete": "complete", "self-report-flip": "complete",
        "gate-fail": "gate-fail", "pre-measurement": "pre-measurement",
        "post-launch-failure": "post-launch"}[run])
    synth = Synth(header, records, shape)
    synth.failing = failing
    return expect, reference, inputs, synth


def judged(expect, reference, inputs, texts, toolchain="gcc"):
    """judge() on hart 0's stream of TEXTS, its domain lines (BE_MVP_G)
    left out as tests/check-capture.py splits a capture."""
    monitor = [line for line in lines_of(texts)
               if not line.text.startswith("BE_MVP_G")]
    return judge(monitor, expect, reference, inputs, toolchain)


def outcome(result, wanted=None, absent=()):
    """(ok, findings): no finding when WANTED is None, else a finding
    holding WANTED and none holding any of ABSENT."""
    findings = result[0]
    if wanted is None:
        return not findings, findings
    return (any(wanted in finding for finding in findings) and not any(
        word in finding for finding in findings for word in absent),
        findings)


def edit(texts, index, old, new):
    texts = list(texts)
    assert old in texts[index], (texts[index], old)
    texts[index] = texts[index].replace(old, new, 1)
    return texts


def vector_cases():
    """The profile's test vectors (2.8, 2.10, 4.1, 5.4) and the round
    trip (D-4)."""
    expect, reference, inputs, run, lines = example_case()
    _, displays, dumps = profile_example()
    rebuilt = rebuild(lines_of(lines))
    page = encode(rebuilt.header, rebuilt.records)
    value = export(rebuilt.header, rebuilt.records, rebuilt.barrier[1],
                   rebuilt.terminal[1])
    data = render(value)
    header, records, printed = read_export(data)
    trip = encode(header, records)
    texts = run.texts()
    again = rebuild(lines_of(texts))
    reference_value = json.loads(displays[1])
    values = {"scenario": label("scenario te-poc")}
    for record in rebuilt.records:
        domain = record["stream"] - 2 if record["stream"] in (2, 3) else None
        values[record["object"], domain] = (
            record["base"], record["length"], record["digest"]) if \
            record["repr"] == "as-placed" else record["digest"]
    built = build_reference(
        {key: reference_value[key] for key in (
            "source", "image", "scenario", "variant", "toolchain",
            "authority_report_sha256", "elf_sha256", "boot_image_sha256",
            "mutated_image_sha256")}, "v2", "complete", "kept", values,
        {(entry["object"], entry["domain"]): entry["source"]
         for entry in reference_value["ranges"] if entry["domain"]
         is not None})
    lengths = [len(line) for line in lines if line.startswith("BE_MVP:")]
    return [
        ("vector", "2.10: the example's page has the profile's SHA-256",
         sha256(page) == EXAMPLE_PAGE, sha256(page)),
        ("vector", "2.10: the header, record 9, and the close as dumped",
         [dump(page, 0, 128), dump(page, 992, 96), dump(page, 1376, 96)]
         == dumps, dump(page, 0, 32)),
        ("vector", "5.4: the export, 8,153 bytes, the profile's SHA-256",
         (len(data), sha256(data)) == EXAMPLE_EXPORT and
         json.loads(displays[0]) == value, (len(data), sha256(data))),
        ("vector", "5.4: the reference, 10,993 bytes, the profile's SHA-256"
         ", as build_reference() renders it",
         (len(render(reference_value)), reference.sha256) ==
         EXAMPLE_REFERENCE and render(built) == render(reference_value),
         reference.sha256),
        ("vector", "2.8: the four console-grant digests",
         all(sha256(bytes(pair)) == digest
             for pair, digest in GRANT_DIGESTS.items()), ""),
        ("vector", "4.5: 4,557 bytes of :19 and :20 text; no line above "
         "319 characters", rebuilt.volume == EXAMPLE_VOLUME and
         max(lengths) <= LINE_LIMIT, rebuilt.volume),
        ("vector", "2.6: the registers replay to the printed ones",
         again.replayed == again.barrier[1] == again.terminal[1] ==
         reference.registers and not again.findings, again.findings),
        ("round-trip", "page, lines, rebuild, log.json, rebuild: the page "
         "byte for byte", trip == page and printed["barrier"] ==
         rebuilt.barrier[1] and [header_line(header)] + [
             record_line(record) for record in records] == lines[2:17] and
         encode(again.header, again.records) == page, sha256(trip)),
        ("accept", "te-poc: the profile's example, complete",
         *outcome(judged(expect, reference, inputs, texts)))]


def reader_cases():
    """5.1's reader and section 7's allowlist on the example's reference
    and export, each refused for its own reason."""
    _, displays, _ = profile_example()
    good, plain = render(json.loads(displays[1])), render(json.loads(
        displays[0]))

    def changed(mutate):
        value = json.loads(displays[1])
        mutate(value)
        return render(value)

    def refused(name, data, wanted, reader=read_reference):
        try:
            reader(data)
        except Refused as error:
            return "reader", name, wanted in str(error), str(error)
        return "reader", name, False, "accepted"
    records = ("expected", "records")
    return [
        refused("a duplicate key", good.replace(
            b'"schema":', b'"r2": "kept",\n "schema":'), "duplicate key"),
        refused("NaN", good.replace(b'"variant": null', b'"variant": NaN'),
                "not a JSON number"),
        refused("a float", good.replace(b'"capacity": 41',
                                        b'"capacity": 41.0'), "the float"),
        refused("a key the schema does not name",
                changed(lambda value: value.update(note="x")),
                "does not name"),
        refused("above 262,144 bytes", good + b" " * JSON_LIMIT,
                "262144-byte bound"),
        refused("an ima_template content type", changed(
            lambda value: value[records[0]][records[1]][3].update(
                content_type="ima_template")), "outside the allowlist"),
        refused("a boot_aggregate object", changed(
            lambda value: value[records[0]][records[1]][0][
                "content"].update(object="boot_aggregate")),
                "outside the allowlist"),
        refused("a platform fact as a source: the board's device tree",
                changed(lambda value: value["ranges"][6].update(
                    source="/proc/device-tree")), "(section 7)"),
        refused("a source that leaves build/mvp/", changed(
            lambda value: value["ranges"][5].update(
                source="guest/../../Image")), "(section 7)"),
        refused("another schema", changed(lambda value: value.update(
            schema="be-mvp-log-reference-v2")), "is not be-mvp-log-ref"),
        refused("more than 41 records", changed(
            lambda value: value[records[0]][records[1]].extend(
                value[records[0]][records[1]] * 2)), "at most 41"),
        refused("an export with a duplicate key", plain.replace(
            b'"schema":', b'"header": {},\n "schema":'), "duplicate key",
                read_export)]


def example_kinds():
    """D-4's kinds 1 to 3 on the te-poc example, the reference frozen:
    capture mutations, metadata the registers cannot see (the printed
    registers recomputed), and a wrong digest at each record the monitor
    controls (the printed registers recomputed, so the replay passes)."""
    expect, reference, inputs, run, _ = example_case()
    texts = run.texts()
    record = 5   # record i's line is texts[record + i]

    def case(kind, name, data, wanted, absent=(), **changes):
        own = dict(expect, **changes.get("expect", {}))
        return (kind, name, *outcome(judged(
            own, changes.get("reference", reference), inputs, data,
            changes.get("toolchain", "gcc")), wanted, absent))

    def again(mutate):
        synth = Synth(run.header, run.records)
        mutate(synth)
        return synth.texts()

    def moved(data, source, after):
        data = list(data)
        line = data.pop(source)
        data.insert(after, line)
        return data
    variant = json.loads(PROFILE.read_text(encoding="utf-8").split(
        "```json\n")[2].split("```")[0])
    variant["variant"] = "reader-write"
    replay_ = "does not replay"
    out = [
        case("kind1", "omission", texts[:record + 7] + texts[record + 8:],
             "seq=8 is not the line's position 7"),
        case("kind1", "duplication", texts[:record + 10] +
             texts[record + 9:], "seq=9 is not the line's position 10"),
        case("kind1", "reorder", moved(texts, record + 9, record + 10),
             "seq=10 is not the line's position 9"),
        case("kind1", "a second producer", edit(texts, record + 5,
                                                 "producer=0", "producer=1"),
             "producer=1, not 0"),
        case("kind1", "an IMA template name as the object", edit(
            texts, record + 7, "object=configuration-identity",
            "object=ima-ng"), "outside its enumeration"),
        case("kind1", "another object of the allowlist", edit(
            texts, record + 8, "object=policy-identity",
            "object=policy-absent"), "record 8 is policy-absent"),
        case("kind1", "SHA-1's algorithm", edit(texts, 4, "alg=0x000b",
                                                "alg=0x0004"),
             "alg 0x0004"),
        case("kind1", "a range moved", edit(
            texts, record + 3, "base=0x0000000102064000",
            "base=0x0000000102065000"), "mvp-text base=0x0000000102065000 "
             "is not the reference's 0x0000000102064000"),
        case("kind1", "a representation", edit(texts, record + 5,
                                                "repr=as-computed",
                                                "repr=as-placed"),
             "outside its row of 2.7"),
        case("kind1", "an outcome", edit(texts, record + 10,
                                          "outcome=gated-pass",
                                          "outcome=recorded"),
             "device-tree outcome=recorded is not the reference's "
             "gated-pass"),
        case("kind1", "version 2", edit(texts, 4, "version=1",
                                        "version=2"), "version 2"),
        case("kind1", "a record after the close", moved(
            edit(edit(texts, record + 12, "seq=12", "seq=13"),
                 record + 13, "seq=13", "seq=12"), record + 13,
            record + 12), "a close that is not the last record"),
        case("kind1", "a close whose count is not the header's", edit(
            texts, record + 13, "expected=14", "expected=13"),
             "the close's expected=13 is not the count 14"),
        case("kind1", "truncation", texts[:record + 12],
             "12 record lines, not the header's count=14"),
        case("kind1", "overflow, with the log's 14 records", edit(
            texts, 4, "state=closed", "state=overflow"),
             "an overflow log with count 14, not 40"),
        case("kind1", "a register that does not replay", edit(
            texts, 19, "r2=b89e71c1", "r2=7f68367b"), "the barrier's r2 "
             + replay_),
        case("kind1", "the reference of another image", texts,
             "the reference is te-poc's (variant None), not this run's "
             "te-poc-shell", expect={"image": "te-poc-shell"}),
        case("kind1", "the reference of another toolchain", texts,
             "the reference is the gcc image's, not the clang run's",
             toolchain="clang"),
        case("kind1", "the reference of another variant", texts,
             "variant reader-write", reference=Reference(render(variant))),
        case("kind1", "a false platform-fact binding: the board's device "
             "tree as domain 0's", edit(texts, record + 10,
                                         "base=0x0000000113e00000",
                                         "base=0x00000002fbd6b000"),
             "device-tree base=0x00000002fbd6b000 is not the reference's"),
        case("kind2", "a type changed, the digests kept", again(
            lambda synth: synth.records[7].update(type="measured")),
             "outside its row of 2.7", (replay_,)),
        case("kind2", "a stream changed, the digests kept", again(
            lambda synth: synth.records[12].update(stream=2, srec=2)),
             "device-tree stream=2 is not the reference's 3", (replay_,)),
        case("kind2", "two records of different streams swapped", again(
            lambda synth: synth.records.__setitem__(slice(8, 10), [
                dict(synth.records[9], seq=8),
                dict(synth.records[8], seq=9)])),
             "record 8 is kernel-image (stream 2), where the complete "
             "prefix has policy-identity (stream 1)", (replay_,)),
        case("kind2", "a forged close and count", again(
            lambda synth: (synth.records.__setitem__(slice(11, 14), [
                dict(synth.records[13], seq=11, expected=12)]),
                synth.header.update(count=12))),
             "header count=12 is not the reference's 14", (replay_,)),
        case("kind2", "a record moved after the first HART_STARTED",
             moved(texts, record + 13, 21), "outside the block"),
        case("kind2", "the terminal registers changed", again(
            lambda synth: setattr(synth, "terminal", [
                replay(synth.records)[0]] * 2 + replay(synth.records)[2:])),
             "the terminal's r1 " + replay_),
        case("kind2", "a guest-prefixed look-alike of a record line",
             texts[:record + 6] + ["BE_MVP_G0: " + texts[record + 6]] +
             texts[record + 7:], "seq=7 is not the line's position 6")]
    for index in (0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12):
        name = run.records[index]["object"]
        domain = f" (domain {run.records[index]['stream'] - 2})" if \
            index > 8 else ""
        out.append(case(
            "kind3", f"a wrong digest at {name}{domain}", again(
                lambda synth, at=index: synth.records[at].update(
                    digest=sha256(b"wrong %d" % at))),
            f"self-report differs: {name}" if index < 5 else
            f"{name} digest=", (replay_,)))
    return out


def synthesis_kinds():
    """D-4's kinds 3 to 5 and the run classes on this module's own anchor
    and two-guests syntheses (true digests), each reference frozen."""
    replay_ = "does not replay"

    def case(kind, name, built, data=None, wanted=None, absent=(),
             expect=None):
        expectation, reference, inputs, synth = built
        return (kind, name, *outcome(judged(
            dict(expectation, **(expect or {})), reference, inputs,
            synth.texts() if data is None else data), wanted, absent))

    def variant(built, mutate):
        mutate(built[3])
        return built
    anchor = synthesis("v3")
    gate = synthesis("v3", "gate-fail", image="wrong-measurement")
    gate_texts = gate[3].texts()
    detail = next(index for index, text in enumerate(gate_texts)
                  if text.startswith("BE_MVP:DETAIL "))
    computed = re.search(r"computed=(\S+)", gate_texts[detail]).group(1)
    overflow = synthesis("v2")
    overflow[3].records = overflow[3].records[:9] + [
        dict(overflow[3].records[9 + (index % 2)], seq=9 + index,
             srec=index) for index in range(31)]
    overflow[3].header.update(state="overflow", count=40)
    overflow[3].shape = "log-failure"
    two = synthesis("v1", "post-launch-failure", image="exit-budget")
    fallback = synthesis("v1", "post-launch-failure", image="ring-full",
                         fallback=True)
    fallback[3].shape = "fallback"
    fallback_texts = fallback[3].texts()
    terminal = registers_line("terminal", replay(fallback[3].records))
    probe = synthesis("probe", image="probe-platform")
    probe_texts = probe[3].texts()
    pre = synthesis("v1", "pre-measurement", image="payload")
    flipped = synthesis("v3", "self-report-flip", image="self-report-flip",
                        flipped=True)
    terminated = ("BE_MVP:12 DOMAIN_TERMINATED hart=2 domain=1 by=0 "
                  "exits=40 sha256={} ticks=0x3000")
    shell = synthesis("v2", grants=(True, True), image="te-poc-shell")
    return [
        case("kind3", "a wrong digest at the secret page", variant(
            synthesis("v3"), lambda synth: synth.records[13].update(
                digest=sha256(b"wrong secret"))), None,
            "secret-page digest=", (replay_,)),
        case("kind4", "an overflowing log: the run ends at BE_MVP:FAIL "
             "log, and no hart starts", overflow, None,
             "header state=overflow is not the reference's closed",
             ("not closed: no domain hart starts",)),
        case("kind4", "an overflowing log with a HART_STARTED after it",
             variant(overflow, lambda synth: synth.extra.extend(
                 [PUBLISHED, HART_STARTED.format(0, 1)])), None,
             "not closed: no domain hart starts unless the log closed"),
        case("kind4", "an overflow log of 39 records", variant(
            synthesis("v2"), lambda synth: (
                synth.records.__setitem__(slice(9, None), [
                    dict(synth.records[9], seq=9 + index, srec=index)
                    for index in range(30)]),
                synth.header.update(state="overflow", count=39),
                setattr(synth, "shape", "log-failure"))), None,
            "an overflow log with count 39, not 40"),
        case("kind5", "wrong-measurement's gate-fail, accepted exactly",
             gate),
        case("kind5", "a gate-fail without the DETAIL", gate,
             gate_texts[:detail], "has no DETAIL line"),
        case("kind5", "a gate-fail whose DETAIL expects the nominal value",
             gate, edit(gate_texts, detail, "expected=" + flip(computed),
                        "expected=" + computed),
             "the DETAIL's expected= is not the reference's"),
        case("kind5", "a gate-fail with the barrier's registers", gate,
             gate_texts[:detail - 1] + [registers_line(
                 "barrier", replay(gate[3].records), "0x10")] +
             gate_texts[detail - 1:], "registers lines in a gate-fail run"),
        case("kind5", "a gate-fail followed by a HART_STARTED", gate,
             gate_texts + [HART_STARTED.format(1, 2)],
             "not closed: no domain hart starts unless the log closed"),
        case("accept", "anchor: complete, domain 1 terminated with its "
             "launch register", variant(anchor, lambda synth: synth.extra.
                                        append(terminated.format(replay(
                                            synth.records)[3])))),
        case("accept", "anchor: DOMAIN_TERMINATED sha256=-, refused",
             variant(synthesis("v3"), lambda synth: synth.extra.append(
                 terminated.format("-"))), None,
             "is not domain 1's launch register (D-9)"),
        case("accept", "two-guests: complete", synthesis("v1")),
        case("accept", "exit-budget: a failure after the launch", two),
        case("accept", "exit-budget without the terminal registers, "
             "refused", two, [text for text in two[3].texts()
                              if "at=terminal" not in text],
             "no terminal registers line"),
        case("accept", "ring-full's fallback: the barrier, no terminal",
             fallback, fallback_texts),
        case("accept", "ring-full's fallback with terminal registers, "
             "refused", fallback, fallback_texts[:-2] + [terminal] +
             fallback_texts[-2:], "in the ring-full fallback"),
        case("accept", "payload: pre-measurement, no log line", pre),
        case("accept", "payload with a block, refused", pre,
             [PLACED.format(0)] + pre[3].log() + ["BE_MVP:FAIL payload"],
             "declared prefix is empty"),
        case("accept", "probe-platform: complete, no LAUNCH", probe),
        case("accept", "probe-platform with a LAUNCH line, refused", probe,
             probe_texts[:0] + [f"BE_MVP:06 LAUNCH domain=0 hart=1 "
                                f"register={ZERO} expected=match "
                                f"ticks=0x1"] + probe_texts,
             "LAUNCH lines for domains [0]"),
        case("accept", "self-report-flip: exactly its one declared "
             "self-report finding", flipped),
        case("accept", "self-report-flip with a second difference, "
             "refused", variant(synthesis(
                 "v3", "self-report-flip", image="self-report-flip",
                 flipped=True), lambda synth: synth.records[0].update(
                     digest=sha256(b"other"))), None, "not exactly"),
        case("accept", "two-guests with R2 dropped: no stream-0 record",
             synthesis("v1", r2="dropped")),
        case("accept", "an expectation's R2 unlike the reference's, "
             "refused", synthesis("v1", r2="dropped"), None,
             "log.count is 13, not 8",
             expect={"log": synthesis("v1")[0]["log"]}),
        case("accept", "te-poc-shell: both domains' console grants",
             synthesis("v2", grants=(True, True), image="te-poc-shell")),
        case("accept", "console grants the canonical data does not give, "
             "refused", shell[:2] + (Inputs(**dict(vars(shell[2]), grants=[
                 False, False])), shell[3]), None,
             "console-grants's printed digest")]


def expectation_cases():
    """The expectation's log section as tools/gen-scenario.py writes it:
    read by its keys (log_section(), contract_of()), and compared field by
    field with what the image's reference implies (expectation_log()),
    each section changed in one place against its frozen reference."""
    def case(name, built, change, wanted, texts=None):
        expectation, reference, inputs, synth = built
        expect = json.loads(json.dumps(expectation))
        change(expect)
        return ("expect", name, *outcome(judged(
            expect, reference, inputs, synth.texts() if texts is None
            else texts), wanted))

    def at(path, value):
        def change(expect):
            node = expect["log"]
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = value
        return change
    te_poc, anchor = synthesis("v2"), synthesis("v3")
    gate = synthesis("v3", "gate-fail", image="wrong-measurement")
    fallback = synthesis("v1", "post-launch-failure", image="ring-full",
                         fallback=True)
    # A v1 variant on a hart of its own (hart-start's): its LAUNCH line
    # names that hart, the generator's binding for the log.
    moved = synthesis("v1", "post-launch-failure", image="hart-start")
    moved[0]["outcome"].update(domain=1, hart=9, after="BE_MVP:07")
    moved[0]["log"] = expectation_log(moved[1], [1, 9])
    moved[3].harts = (1, 9)
    moved[3].shape = "post-launch"
    return [
        ("expect", "every synthesis's section is its reference's",
         all(not differences(expectation_log(
             built[1], log_harts(built[0]), bool(
                 built[0]["outcome"].get("fallback")),
             built[0]["log"].get("mutate")), built[0]["log"], "log")
             for built in (te_poc, anchor, gate, fallback, moved)), None),
        case("a key the generator does not write, refused", te_poc,
             at(["extra"], 1), "extra, which the schema does not name"),
        case("no lines, refused", te_poc, lambda expect: expect[
            "log"].pop("lines"), "the expectation's log: no lines"),
        case("profile 2, refused", te_poc, at(["profile"], 2),
             "log.profile is not 1"),
        case("a count other than the sequence's, refused", te_poc,
             at(["count"], 13), "log.count 13 is not the v2 sequence's "
             "14 with R2 kept"),
        case("a run class the outcome does not give, refused", te_poc,
             at(["run"], "post-launch-failure"), "declares "
             "v2/post-launch-failure, but its outcome is v2/complete's"),
        case("self-report-flip's finding in another image, refused",
             te_poc, at(["findings"], [FLIP_FINDING]),
             "findings, which the schema does not name"),
        case("a record's digest unlike the reference's", anchor,
             at(["records", 13, "digests", 0, "digest"], ZERO),
             "log.records[13].digests[0].digest is"),
        case("a measured digest null, where only R2's are", te_poc,
             at(["records", 9, "digests", 0, "digest"], None),
             "log.records[9].digests[0].digest is null"),
        case("an R2 length the link fixes, given", te_poc,
             at(["records", 0, "content", "length"], hex64(0x1000)),
             "log.records[0].content.length is"),
        case("a range's source unlike the reference's", anchor, at(
            ["ranges", 6, "source"], "guest/other.dtb"),
            "log.ranges[6].source is"),
        case("r0 given with R2 kept", te_poc, at(["registers", 0], ZERO),
             "log.registers[0] is"),
        case("a launch constant unlike the reference's", te_poc, at(
            ["launch_expected", 1], flip(te_poc[1].launch[1])),
            "log.launch_expected[1] is"),
        case("a LAUNCH line on another hart", te_poc, lambda expect:
             expect["log"]["lines"]["launch"].__setitem__(1, expect[
                 "log"]["lines"]["launch"][1].replace(" hart=2 ",
                                                      " hart=3 ")),
             "log.lines.launch[1] is"),
        case("a block line unlike the reference's", te_poc, lambda expect:
             expect["log"]["lines"]["block"].__setitem__(
                 0, expect["log"]["lines"]["block"][0].replace(
                     "count=14", "count=15")), "log.lines.block[0] is"),
        case("the ring-full fallback with a terminal line", fallback,
             at(["terminal"], "before-fail"), "log.terminal is "
             "\"before-fail\", not \"none\""),
        case("a gate-fail's failing domain unlike the reference's", gate,
             lambda expect: expect["outcome"].update(domain=0),
             "the expectation's failing domain 0 is not the "
             "reference's 1"),
        case("a gate-fail's DETAIL unlike the reference's", gate,
             lambda expect: expect["log"]["lines"].update(
                 detail=expect["log"]["lines"]["detail"].replace(
                     " hart=2 ", " hart=1 ")), "log.lines.detail is"),
        ("expect", "a v1 variant's own hart in its LAUNCH line: PASS",
         *outcome(judged(moved[0], moved[1], moved[2], moved[3].texts()))),
        ("expect", "that variant's LAUNCH line on the scenario's hart, "
         "refused", *outcome(judged(moved[0], moved[1], moved[2], [
             text.replace("LAUNCH domain=1 hart=9 ", "LAUNCH domain=1 "
                          "hart=2 ") for text in moved[3].texts()]),
             "LAUNCH domain=1 hart=2 is not a domain's binding"))]


def self_cases():
    """Every case: (kind, name, ok, detail)."""
    return vector_cases() + reader_cases() + example_kinds() + \
        synthesis_kinds() + \
        expectation_cases()


if __name__ == "__main__":
    import sys
    results = self_cases()
    for kind, name, ok, detail in results:
        print(f"{'ok  ' if ok else 'FAIL'} [{kind}] {name}"
              f"{'' if ok else ' ' + str(detail)[:300]}")
    failed = sum(not ok for _, _, ok, _ in results)
    print(f"BE_MVP_LOG_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
          f"cases={len(results)} failed={failed}")
    sys.exit(1 if failed else 0)
