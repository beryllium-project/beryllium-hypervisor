#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""The MVP platform record (planning/mvp-m0-plan.md, "Platform record:
probes and negative images"; work package M0-6; planning/mvp-m1-plan.md,
"Platform record"; work package M1-6; planning/mvp-m2-plan.md, "Platform
record"; work package M2-5; planning/mvp-m5-plan.md, "Tool changes (M5-2)").

  platform-record.py --record DIR [--qemu-suite DIR]
  platform-record.py --self-test

Purpose: the facts a board record (tools/evidence.py --board) holds for
M1's design and the MVP claim, each with its source, as DIR/platform-
record.json and .md. Nothing in it is a claim. Since M9
(planning/mvp-m9-plan.md, D-4, D-6, D-10) its measurement sections are
the log's, from each run's result.json (the capture checker's log record):
one per stream, each register at the barrier and the terminal beside the
checker's replay (unprotected), stream 0's self-report against the
reference (equal, differs, declared, or dropped), each domain's launch
register and DOMAIN_TERMINATED digest, the hashing ticks, and the loader
observation beside them, unchanged; a record whose runs carry no log
renders the log as not run, M2's measurement table no longer. Its
"Console input on K3" section (mvp/README.md, item 115) holds each typed
characterization's class, pacing, and counts per repetition (the run's
characterization.txt, tools/k3-input-characterize.sh's) and each typed
session's steps and keys (run.txt's typist line, session.txt, typed.txt)
beside its BE_MVP:15 to :18 lines and the capture checker's input
accounting (result.json); a record with neither renders it as not run.
--self-test renders those sections from synthetic runs.
Inputs: the record's own files, M1's among them: each run's reset record
(mvp/resets/<run>.txt, M5's, tools/k3-console.sh's: the method, k3ctl or
human; the port-open rule's reason; the client's SHA-256; both `status`
replies and the `reset` reply, with their UTC times; the log offsets of
the reset and of the SPL and U-Boot banners after it), the preflight after
the session (mvp/preflight-after.txt) beside the one before
(preflight.txt), each run's boot hart (its SHIM line's hart=, as
result.json records it), and the campaign's
Serial log paragraph (mvp/serial-log-note.txt, written by hand for each
campaign from the operator's serial log, outside the repository, so each
record states its own reading); for each run of a scenario the record
keeps in a directory of its own (M1's te-poc, mvp/scenario/te-poc/), its
expectation and the authority report the expectation names by SHA-256:
each te-poc run's DENY lines (result.json) beside its guests' MVPINIT 08
reports (handoff-excerpt.log) and the expectation's denials, paired as
tests/check-capture.py pairs them, and each such run's CHANNEL_CHECKED
and CHANNEL_CLEARED lines beside the report's channel, with its guests'
MVPINIT 07 lines; for each run of a scenario with pages (M2's anchor and
its negatives, mvp/scenario/anchor/), its PAGE_CHECKED lines beside the
report's pages and its PAGE_CLEARED and SECRET_PLACED lines, its
MEASURED line with its ticks beside the report's offline value and the
measured domain's DOMAIN_TERMINATED value, each BE_MVP:MGMT line with
the requester's state, the result, the target's state, and service=,
beside its guest's MVPINIT 10 report, the DOMAIN_PAUSED and
DOMAIN_TERMINATED lines with their exit counts, and each request's and
response's digest (MVPINIT 09) beside the expectation's offline one; and
each anchor run's BE_MVP:11 IPI_PROBE lines beside the capture checker's
costs (check.txt), a probe it recorded as served inside a management wait
of its hart (Plan revision M2-A: g<d>_ping_in_mgmt_wait, g<d>_ping_mgmt_seq)
with the BE_MVP:MGMT line whose wait holds it; M0's
accepted record's preflight (mvp/results/
20261025-com260/preflight.txt, M1's platform input), whose firmware
identity in Fedora's log and Fedora kernel release this record's are set
beside; QEMU's probe values beside the board's, as emulation facts: the
in-tree GCC probe captures, judged again by tests/check-capture.py, and
the QEMU suite's Clang probe records (--qemu-suite) if they ran the
record's images; M0's accepted record's platform record (M0's board probe
values, made after a kexec, beside this record's from a boot from reset,
each labelled); src/mvp-layout.h, for tools/platform-probe.py
region-check on the record's preflight, the shared pages (M2's three-page
extent, M1's channel page its first) among its extents.
Trust: it runs those two tools at fixed paths, and nothing it reads; a
missing or malformed input, or an existing record, refuses it.
Determinism: sorted keys, no time but the inputs', and paths relative to
the record or the repository.
"""

import argparse
import collections
import hashlib
import itertools
import json
import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True
MVP_DIR = pathlib.Path(__file__).resolve().parents[1]
REPO = MVP_DIR.parent
CHECKER = MVP_DIR / "tests" / "check-capture.py"
PROBE_TOOL = MVP_DIR / "tools" / "platform-probe.py"
LAYOUT = MVP_DIR / "src" / "mvp-layout.h"
FIXTURES = MVP_DIR / "tests" / "fixtures"
SCHEMA = "be-mvp-platform-record-v3"
OUTPUTS = ("platform-record.json", "platform-record.md")
PROBES = ("probe-platform", "probe-vmid-distinct", "probe-vmid-shared")
PAIR = re.compile(r"([a-z_0-9]+)=(\S*)")
# The plan's probe table's "Expected on K3", quoted; then each probe
# value's label, in the plan's order.
PLAN = {
    "hsm": "All `STOPPED` (1); otherwise stop 6",
    "hgatp": "Sv39x4 with 14 VMID bits (B7 records); other modes recorded "
             "as facts",
    "gpf": "`htval` = GPA >> 2 for each (S1 H16); `htinst` recorded; a "
           "different `htval` is stop 6",
    "ipi": "100 and 100; a miss is stop 6",
    "order": "0 with fences (otherwise stop 6); the unfenced count is a "
             "fact",
    "vmid-distinct": "B's value (tagging by VMID); A's value is stop 6",
    "vmid-shared": "A fact either way: A's value shows a cached "
                   "translation that needs the fence; B's shows none was "
                   "cached",
}
LABELS = {"hsm": "hsm", "hgatp": "hgatp", "gpf-load": "gpf",
          "gpf-store": "gpf", "gpf-fetch": "gpf", "ipi-hs": "ipi",
          "ipi-vs": "ipi", "order-unfenced": "order", "order-fenced": "order",
          "vmid-distinct": "vmid-distinct", "vmid-shared": "vmid-shared"}
# M7-5's probe-console-input (planning/mvp-m7-plan.md, D-12): its values,
# which no row of M0's probe table holds; its judgement is the run's
# characterization.txt (tools/k3-input-characterize.sh).
INPUT_LABELS = ("console-input-window", "console-input-total")
# A typed run's records (tools/k3-console.sh probe-type and guest-type), the
# characterization's fields (k3-uboot.py input-judge's, the driver's), and
# the repetitions' nominal pacing (planning/mvp-m7-plan.md, Q14).
TYPING = ("characterization.txt", "session.txt", "typed.txt")
CHARACTERIZATION = ("class", "pacing_10ms", "fast_pacing", "total",
                    "typed_bytes", "polls", "nonzero_polls", "max_per_poll",
                    "errors", "slow_received_before_fourth", "verdict")
REPETITION_MS = {"1": "10", "2": "10", "3": "10", "4": "1"}
MODES = {0: "Bare", 8: "Sv39x4", 9: "Sv48x4", 10: "Sv57x4"}
COUNTS = ("boot_hart", "records", "wakes", "alternations", "overlap_ticks",
          "shorter_ticks")
SHUTDOWN = ("hart", "domain", "exits", "sbi", "ipi", "base", "time",
            "dbcn_write", "dbcn_read", "dbcn_byte", "srst", "refused",
            "lines", "ring_peak", "entered", "ticks", "elapsed_ms")
# The campaign's Serial log paragraph (M0 open item 40, as M1 makes it an
# input), written by hand and kept by tools/evidence.py --board.
SERIAL_NOTE = pathlib.Path("mvp") / "serial-log-note.txt"
# A k3ctl status reply (the firmware's, as the client relays it).
STATUS = re.compile(r"OK status rst=(\d+) fcrec=(\d+) pwr=(\d+) k3=(\S+) "
                    r"up=(\d+) ver=(\S+)")
STATUS_FIELDS = ("rst", "fcrec", "pwr", "k3", "up", "ver")
RESET_COLUMNS = ("run", "method", "reason", "outcome", "client_sha256",
                 "status_before", "reset_reply", "status_after",
                 "reset_utc", "banner_utc", "offset_before",
                 "spl_banner_offset", "uboot_banner_offset")
# The preflight's lines that change from boot to boot, which the pair
# before and after the session does not compare.
VOLATILE = ("captured_utc", "boot_id")
# M0's accepted board record, M1's platform input (planning/mvp-m1-plan.md,
# "Platform record", Q13): its preflight, beside which this record's
# firmware identity and Fedora kernel release are set.
M0_RECORD = MVP_DIR / "results" / "20261025-com260"
# The firmware's identity (tools/k3-preflight.sh's stop 8 reads it) and its
# SBI specification, in Fedora's log.
FEDORA_LOG = (
    ("SBI implementation",
     re.compile(r"\] SBI implementation (ID=0x[0-9a-fA-F]+ "
                r"Version=0x[0-9a-fA-F]+)$")),
    ("SBI specification", re.compile(r"\] SBI specification (\S+) "
                                     r"detected$")))
# A file name the record's scenario copies may hold (tools/evidence.py's
# EXPECT_FORM, which an authority report's name also fits).
NAME_FORM = re.compile(r"[a-z0-9][a-z0-9.-]{0,63}\.json")
# M1's lines (planning/mvp-m1-plan.md, "Markers"), each with its fields in
# tests/check-capture.py's order: hart 0's DENY line; the guest's MVPINIT 08
# report, unchanged= after a store only; the channel's two boot lines; and
# each guest's MVPINIT 07 line, a writer's with its flag, a reader's with
# its polls and match.
DENY = "BE_MVP:DENY "
DENY_FIELDS = ("hart", "domain", "seq", "kind", "cause", "injected", "gpa",
               "htval", "htinst", "stval", "sepc", "vsstatus", "vstvec",
               "ticks", "service")
DENIED = "MVPINIT 08 DENIED "
DENIED_FIELDS = ("n", "kind", "gpa", "va", "pc", "signo", "code",
                 "observed", "unchanged")
CHECKED = "BE_MVP:03 CHANNEL_CHECKED "
CHECKED_FIELDS = ("channel", "writer", "reader", "gpa", "hpa", "bytes",
                  "level0", "writer_pte", "reader_pte", "config")
CLEARED = "BE_MVP:05 CHANNEL_CLEARED "
CLEARED_FIELDS = ("channel", "hpa", "bytes", "ticks")
CHANNEL = "MVPINIT 07 CHANNEL "
CHANNEL_FIELDS = {"writer": ("role", "gpa", "bytes", "digest", "flag"),
                  "reader": ("role", "gpa", "bytes", "digest", "polls",
                             "match")}
CHANNEL_COLUMNS = ("role", "gpa", "bytes", "digest", "flag", "polls",
                   "match")
# The counts of a te-poc run beside M0's: each domain's DENY lines.
DENIAL_COUNTS = ("denials_g0", "denials_g1")
FAIL, DETAIL = "BE_MVP:FAIL ", "BE_MVP:DETAIL "
GUEST_LINE = re.compile(r"BE_MVP_G[0-9]+: ")
# M2's lines (planning/mvp-m2-plan.md, "Markers", "Platform record"):
# hart 0's page, placement, measurement, request, and transition lines;
# the guests' call and digest reports; the SBI results (Q3); and an
# anchor run's counts beside te-poc's, each domain's requests on hart 0.
PAGE_CHECKED = "BE_MVP:03 PAGE_CHECKED "
PAGE_COLUMNS = ("kind", "writer", "reader", "gpa", "hpa", "bytes",
                "writer_pte", "reader_pte", "config")
PLACED = ("BE_MVP:05 PAGE_CLEARED ", "BE_MVP:05 SECRET_PLACED ")
MEASURED = "BE_MVP:06 MEASURED "
MGMT = "BE_MVP:MGMT "
MGMT_FIELDS = ("hart", "domain", "seq", "fid", "target", "result",
               "target_state", "ticks", "service")
ENDS = ("BE_MVP:12 DOMAIN_PAUSED ", "BE_MVP:12 DOMAIN_TERMINATED ",
        "BE_MVP:12 DOMAIN_SHUTDOWN ")
SBI_RESULTS = {"0": "SBI_SUCCESS", "-2": "SBI_ERR_NOT_SUPPORTED",
               "-3": "SBI_ERR_INVALID_PARAM", "-4": "SBI_ERR_DENIED",
               "-10": "SBI_ERR_INVALID_STATE"}
GUEST_CALL = re.compile(r"MVPINIT 10 MGMT (?:burst=(\d+) )?fid=(\S+) "
                        r"target=(\S+) results?=(-?\d+)(?:x\d+)?")
GUEST_DIGEST = re.compile(r"MVPINIT 09 (REQUEST|RESPONSE) n=(\d+) "
                          r"(?:digest=([0-9a-f]{64})|timeout=1)")
MGMT_COUNTS = ("mgmt_g0", "mgmt_g1")
# Plan revision M2-A (planning/mvp-m2-plan.md): the IPI probe's line, and
# the capture checker's costs for a probe served inside a management wait
# of its hart (M2-A.1), by domain.
IPI_PROBE = "BE_MVP:11 IPI_PROBE "
IPI_FIELDS = ("hart", "domain", "sent", "received", "answered", "spv")
IN_WAIT, WAIT_SEQ = "g{}_ping_in_mgmt_wait", "g{}_ping_mgmt_seq"


class Refused(Exception):
    """An input the record cannot be made from."""


def pairs(text):
    """The k=v fields of one line, in order; anything else refuses."""
    found = PAIR.findall(text)
    if " ".join(f"{key}={value}" for key, value in found) != text.strip():
        raise Refused(f"not k=v fields: {text[:80]!r}")
    return [list(pair) for pair in found]


def line_fields(text, names, optional=0):
    """The k=v fields of TEXT by name, which must be NAMES in order, the
    last OPTIONAL of them only where present; anything else refuses."""
    found = pairs(text)
    keys = tuple(key for key, _ in found)
    if keys not in [names[:len(names) - drop]
                    for drop in range(optional + 1)]:
        raise Refused(f"not the fields {' '.join(names)}: {text[:80]!r}")
    return dict(found)


def number(value):
    return int(value, 16) if value.startswith("0x") else \
        int(value) if value.isdigit() else None


def span(values):
    """One value, or the lowest..highest of several."""
    ordered = sorted(set(values), key=lambda value: (
        number(value) is None, number(value) or 0, value))
    return ordered[0] if len(ordered) == 1 else f"{ordered[0]}..{ordered[-1]}"


def tool(*arguments):
    return subprocess.run(
        [sys.executable, "-B", *map(str, arguments)], capture_output=True,
        text=True, check=False,
        env={"PATH": "/usr/bin", "LC_ALL": "C", "LANG": "C"}).stdout


class Inputs:
    """Every file read, by section, with its SHA-256."""

    def __init__(self, record):
        self.record, self.used = record, {}

    def name(self, path):
        if path.is_relative_to(self.record):
            return str(path.relative_to(self.record))
        return f"<repo>/{path.relative_to(REPO)}"

    def text(self, section, path):
        data = path.read_bytes()
        self.used.setdefault(section, {})[self.name(path)] = \
            hashlib.sha256(data).hexdigest()
        return data.decode("utf-8", errors="replace")


def report(text):
    """The capture checker's report: probe values by label, counts, costs,
    and the result."""
    found = {"values": {}, "BE_MVP_COUNTS": [], "BE_MVP_COSTS": []}
    for line in text.splitlines():
        head, _, rest = line.partition(": ")
        if head == "BE_MVP_PROBE_VALUES":
            label, _, rest = rest.partition(" ")
            if label not in LABELS and label not in INPUT_LABELS or \
                    label in found["values"]:
                raise Refused(f"probe value {label!r} unknown or repeated")
            found["values"][label] = pairs(rest)
        elif head in ("BE_MVP_COUNTS", "BE_MVP_COSTS"):
            found[head] = pairs(rest)
        elif head == "BE_MVP_RESULT":
            found["result"] = rest
    if "result" not in found:
        raise Refused("a checker report without BE_MVP_RESULT")
    return found


def preflight(inputs):
    path = inputs.record / "preflight.txt"
    lines = inputs.text("preflight", path).splitlines()
    begin = lines.index("iomem_system_ram_begin")
    end = lines.index("iomem_system_ram_end")
    out = {"facts": [], "dt_cpus": [], "extensions": {}, "links": {},
           "cpu_map": {}, "caches": [], "topology": [], "cpuinfo": {},
           "log": [], "iomem": lines[begin + 1:end]}
    for line in lines[:begin] + lines[end + 1:]:
        kind, _, rest = line.partition(" ")
        if kind == "dt_cpu_extensions":
            node, _, extensions = rest.partition(" ")
            out["extensions"][node.removeprefix("node=")] = extensions
        elif kind in ("dt_cpu", "dt_cpu_links", "dt_cpu_map",
                      "cpu_topology", "cpuinfo"):
            fields = dict(pairs(re.sub(r"\s*=\s*", "=", rest)))
            if kind == "dt_cpu_links":
                out["links"][fields["node"]] = fields
            elif kind == "dt_cpu_map":
                out["cpu_map"][fields["cpu_phandle"]] = fields["path"]
            elif kind == "cpuinfo":
                out["cpuinfo"].setdefault(int(fields.pop("processor")),
                                          {}).update(fields)
            else:
                out["dt_cpus" if kind == "dt_cpu" else "topology"].append(
                    fields)
        elif kind == "dt_cache" or line.startswith("["):
            out["caches" if kind == "dt_cache" else "log"].append(
                rest if kind == "dt_cache" else line)
        elif re.fullmatch(r"[A-Za-z_0-9]+=.*", line):
            out["facts"].append(line.split("=", 1))
        elif line.strip():
            raise Refused(f"preflight.txt line {line[:60]!r}")
    facts = dict(out["facts"])
    if not out["dt_cpus"] or not facts["timebase_frequency"].isdigit() or \
            not {"kernel", "hsm_detected", "fdt_reserved"} <= set(facts):
        raise Refused("preflight.txt lacks a hart, timebase, kernel, HSM, "
                      "or FDT reservation line")
    inputs.text("preflight", LAYOUT)
    out["region_check"] = tool(PROBE_TOOL, "region-check", LAYOUT,
                               path).splitlines()
    if not re.fullmatch(r"region_check=(PASS|STOP)",
                        (out["region_check"] or [""])[-1]):
        raise Refused("tools/platform-probe.py region-check did not finish")
    page = [line for line in out["region_check"]
            if line.startswith("region shared-pages=")]
    if len(page) != 1:
        raise Refused("tools/platform-probe.py region-check has no line for "
                      "the shared pages")
    out["shared_pages"] = page[0]
    ram = [[int(part, 16) for part in line.split(" : ")[0].split("-")]
           for line in out["iomem"] if line.endswith(" : System RAM")]
    out["reservations"] = [
        [item, "inside System RAM" if any(
            low <= int(item.split("-")[0], 16) and
            int(item.split("-")[1], 16) <= high + 1 for low, high in ram)
         else "outside every System RAM range"]
        for item in facts["fdt_reserved"].split(",")]
    return out


def baseline(inputs, pre, board):
    """The firmware's identity and SBI specification in Fedora's log, and
    the Fedora kernel release (the preflight's first kernel=, its `uname
    -r`), this record's beside M0's record's (planning/mvp-m1-plan.md,
    "Platform record", Preflight); tools/k3-preflight.sh's own firmware
    lines; and the kernel each run's run.txt names, by run count."""
    path = M0_RECORD / "preflight.txt"
    m0 = inputs.text("preflight", path).splitlines()
    logs = (pre["log"], [line for line in m0 if line.startswith("[")])
    rows = [[label] + ["; ".join(sorted({
        match.group(1) for match in map(pattern.search, lines) if match}))
        or None for lines in logs] for label, pattern in FEDORA_LOG]
    rows.append(["Fedora kernel release",
                 next((value for key, value in pre["facts"]
                       if key == "kernel"), None),
                 next((line.split("=", 1)[1] for line in m0
                       if line.startswith("kernel=")), None)])
    for row in rows:
        row.append("equal" if row[1] and row[1] == row[2] else "differs")
    facts = dict(pre["facts"])
    return {"m0": inputs.name(path), "rows": rows,
            "firmware_lines": [[key, facts.get(key)] for key in (
                "firmware_identity", "firmware_expected")],
            "uboot_banners": sorted(collections.Counter(
                run["uboot_banner"] or "none" for run in board).items())}


def preflight_pair(inputs):
    """The preflight after the session beside the one before
    (planning/mvp-m5-plan.md, "The session protocol (M5-6)", step m): each
    fact but VOLATILE's, then the hart, topology, cache, and /proc/iomem
    lines as one row; Fedora's log, whose times differ, aside."""
    found = []
    for name in ("preflight.txt", "mvp/preflight-after.txt"):
        lines = inputs.text("preflight", inputs.record / name).splitlines()
        found.append((dict(line.split("=", 1) for line in lines
                           if re.fullmatch(r"[A-Za-z_0-9]+=.*", line)),
                      [line for line in lines if not line.startswith("[")
                       and not re.fullmatch(r"[A-Za-z_0-9]+=.*", line)]))
    (one, rest), (two, rest_after) = found
    rows = [[key, one.get(key), two.get(key),
             "equal" if one.get(key) == two.get(key) else "differs"]
            for key in sorted(set(one) | set(two)) if key not in VOLATILE]
    rows.append(["the hart, topology, cache, and /proc/iomem lines",
                 f"{len(rest)} lines", f"{len(rest_after)} lines",
                 "equal" if rest == rest_after else "differs"])
    return rows


def runs(inputs):
    lines = inputs.text("runs", inputs.record / "mvp" / "runs.tsv") \
        .splitlines()
    header = lines[0].split("\t")
    out = []
    for line in lines[1:]:
        run = dict(zip(header, line.split("\t")))
        if not re.fullmatch(r"\d{8}T\d{6}Z", run["run"]) or \
                not run["expect"].endswith(".json"):
            raise Refused(f"runs.tsv row {line!r}")
        directory = inputs.record / run["run"]
        fields = {}
        for entry in inputs.text("runs", directory / "run.txt").splitlines():
            key, separator, value = entry.partition("=")
            if separator and re.fullmatch(r"[a-z_0-9]+", key):
                fields.setdefault(key, value)
        recorded = json.loads(inputs.text("runs", directory / "result.json"))
        excerpt = inputs.text("runs", directory / "handoff-excerpt.log")
        run.update(typist=fields.get("typist"), typing={
            name: inputs.text("console input", directory / name)
            for name in TYPING if (directory / name).is_file()})
        run.update(report(inputs.text("runs", directory / "check.txt")),
                   image=run["expect"][:-len(".json")],
                   markers=recorded["markers"], facts=recorded["fields"],
                   log=recorded.get("log"),
                   log_declared=recorded.get("log_declared") or [],
                   attribution=fields.get("attribution"),
                   excerpt=excerpt, uboot_banner=fields.get("uboot_banner"),
                   elapsed=dict(re.findall(
                       r"^BE_MVP_G(\d): MVPINIT 04 SLEEP requested_ms=\d+ "
                       r"elapsed_ms=(\d+) ok=1$", excerpt, re.M)))
        hart = recorded["fields"].get("hart")
        run["boot_hart"] = None if hart is None else str(int(hart, 16))
        run["row"] = [run["run"], run["image"], run["toolchain"],
                      run["image_sha256"][:12], run["verdict"],
                      run["stop"]] + [fields.get(key) for key in (
                          "launcher", "be_image", "serial_range", "reset_utc",
                          "terminal_marker_utc")] + [
            (fields.get("attribution") or "none").split(" ")[0],
            run["boot_hart"]]
        out.append(run)
    return sorted(out, key=lambda run: run["run"])


def markers(run, prefix):
    """The k=v fields of each of RUN's hart 0 lines that start PREFIX."""
    return [dict(pairs(line.split(" ", 2)[2])) for line in run["markers"]
            if line.startswith(prefix + " ")]


def status_fields(reply):
    """A k3ctl status reply's line flags, power sense, uptime, and version,
    or Nones when it is no status reply (an ERR, a device error, none)."""
    match = STATUS.fullmatch(reply or "")
    return list(match.groups()) if match else [None] * len(STATUS_FIELDS)


def resets(inputs, board):
    """Each run's reset (mvp/resets/<run>.txt): its fields, by run, and
    the table rows; the dongle's protocol versions, from its status
    replies."""
    rows, records, versions = [], {}, set()
    for run in board:
        fields = {}
        for line in inputs.text("resets", inputs.record / "mvp" / "resets" /
                                f"{run['run']}.txt").splitlines():
            key, separator, value = line.partition("=")
            if not separator or not re.fullmatch(r"[a-z_0-9]+", key) or \
                    key in fields:
                raise Refused(f"resets/{run['run']}.txt line {line[:60]!r}")
            fields[key] = value
        if fields.get("method") not in ("human", "k3ctl"):
            raise Refused(f"resets/{run['run']}.txt method "
                          f"{fields.get('method')!r}")
        for when in ("before", "after"):
            values = status_fields(fields.get(f"status_{when}"))
            fields[f"status_{when}_fields"] = dict(zip(STATUS_FIELDS,
                                                       values))
            versions.update({values[-1]} - {None})
        records[run["run"]] = fields
        rows.append([run["run"]] + [fields.get(key) for key in
                                    RESET_COLUMNS[1:]])
    return {"rows": rows, "records": records, "versions": sorted(versions)}


def qemu(inputs, probe, suite, images):
    """QEMU's values of PROBE: the in-tree GCC capture, judged again, and
    the suite's last Clang attempt, if it ran the record's image."""
    fixture = FIXTURES / f"qemu-{probe}-gcc.log"
    expect = inputs.record / "mvp" / "scenario" / "expect" / f"{probe}.json"
    gcc = {"source": inputs.name(fixture), "values": {}, "result": "absent"}
    if fixture.is_file():
        inputs.text("qemu", fixture)
        inputs.text("qemu", expect)
        found = report(tool(CHECKER, fixture, "--expect", expect, "--mode",
                            "direct", "--toolchain", "gcc"))
        gcc.update(values=found["values"], result=found["result"])
    clang = {"source": "no QEMU suite", "values": {}, "result": "absent"}
    if suite and (suite / "attempts.tsv").is_file():
        rows = [line.split("\t") for line in inputs.text(
            "qemu", suite / "attempts.tsv").splitlines()]
        last = ([dict(zip(rows[0], row)) for row in rows[1:]
                 if row[:2] == ["clang", probe]] or [{}])[-1]
        elf = f"probes/clang/{probe}/be-mvp-boot.elf"
        clang["source"] = (f"not used: the suite's last attempt ran "
                           f"{last.get('elf_sha256', 'none')[:12]}, the "
                           f"record's {elf} is {images.get(elf, 'none')[:12]}")
        if (last.get("elf"), last.get("elf_sha256")) == (elf, images.get(elf)):
            check = suite / f"clang-{probe}.{last['attempt']}.check.txt"
            found = report(inputs.text("qemu", check))
            clang.update(source=inputs.name(check), values=found["values"],
                         result=found["result"])
    return gcc, clang


def hgatp(word):
    value = int(word, 16)
    return (f"{MODES.get(value >> 60, value >> 60)} VMID "
            f"0x{(value >> 44) & 0x3fff:x} PPN 0x{value & (1 << 44) - 1:x}")


def reading(label, v, started):
    """Matched, differs, or fact: the board's value against the plan's
    expectation for LABEL, with what the plan records as facts."""
    note, ok = "", None
    if label == "hsm":
        ok = all(state == ("0" if hart == started else "1") for hart, state
                 in (pair.split(":") for pair in v["status"].split(",")))
    elif label == "hgatp":
        ok = int(v["sv39x4"], 16) >> 44 == 8 << 16 | int(v["vmid"], 16) and \
            v["vmid_bits"] == "14"
        note = "; the readbacks decode as " + ", ".join(
            f"{key} {hgatp(v[key])}" for key in ("sv39x4", "sv48x4",
                                                 "sv57x4", "restored"))
    elif label.startswith("gpf-"):
        ok = int(v["htval"], 16) == int(v["gpa"], 16) >> 2
        note = f"; `htinst` {v['htinst']}"
    elif label.startswith("ipi-"):
        ok = v["delivered"] == v["sent"] == "100"
    elif label == "order-fenced":
        ok = v["stale"] == "0"
    elif label.startswith("vmid-"):
        seen = {v["value_a"]: "A's", v["value_b"]: "B's"}.get(v["after"],
                                                               "neither's")
        ok = seen == "B's" if label == "vmid-distinct" else None
        note = f"; {seen} value after the switch" + (
            ", a translation cached under the shared VMID"
            if label == "vmid-shared" and seen == "A's" else "")
    return ("fact" if ok is None else "matched" if ok else
            "differs (stop 6)") + note


def scenario(board, timebase, image="two-guests", counts=COUNTS):
    """IMAGE's runs, M0's two-guests, M1's te-poc, or M2's anchor (whose
    COUNTS add DENIAL_COUNTS, and anchor's MGMT_COUNTS): their counts,
    costs, and shutdown records (DOMAIN_SHUTDOWN; anchor's transitions are
    the M2 sections'); what every passing run shares and what varies; the
    ring and run budgets."""
    rows, domains, costs, seen, peaks, ticks = [], [], {}, {}, [], []
    for run in [run for run in board if run["image"] == image]:
        first = {prefix: (markers(run, prefix) or [{}])[0]
                 for prefix in ("BE_MVP:01", "BE_MVP:07", "BE_MVP:13")}
        rows.append([run["run"], run["toolchain"], run["verdict"]] + [
            dict(run["BE_MVP_COUNTS"], boot_hart=run["boot_hart"]).get(key)
            for key in counts] + [
            first["BE_MVP:13"].get(key) for key in ("ticks", "idle_ticks")])
        costs[run["run"]] = run["BE_MVP_COSTS"]
        observed = run["BE_MVP_COUNTS"] + run["BE_MVP_COSTS"] + [
            [f"complete_{key}", value]
            for key, value in first["BE_MVP:13"].items()]
        pings = {line["domain"]: line for line in markers(run, "BE_MVP:11")}
        for shutdown in markers(run, "BE_MVP:12 DOMAIN_SHUTDOWN"):
            domain = shutdown["domain"]
            shutdown["elapsed_ms"] = run["elapsed"].get(domain, "-")
            domains.append([run["run"]] + [shutdown.get(key) for key in
                                           SHUTDOWN] + [", ".join(
                pings.get(domain, {}).get(key, "-")
                for key in ("sent", "received", "answered"))])
            observed += [[f"g{domain}_{key}", shutdown.get(key, "-")]
                         for key in SHUTDOWN]
            peaks += [shutdown["ring_peak"]] if run["verdict"] == "PASS" \
                else []
        if run["verdict"] == "PASS":
            for key, value in observed:
                seen.setdefault(key, []).append(value)
            ring = first["BE_MVP:01"]["ring_bytes"]
            limit = first["BE_MVP:07"]["budget_ticks"]
            ticks.append(first["BE_MVP:13"]["ticks"])
    budgets = [
        f"`ring_peak` {span(peaks)} against half the {ring}-byte outbound "
        f"ring, 0x{number(ring) // 2:x} (BE_MVP:12, BE_MVP:01)",
        f"run ticks {span(ticks)}, the longest "
        f"{max(map(number, ticks)) / timebase:.3f} s at {timebase} Hz, "
        f"against the budget {limit} ({number(limit) / timebase:.3f} s) "
        f"(BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`)"] if ticks else []
    return {"runs": rows, "domains": domains, "costs": costs,
            "budgets": budgets, "passing": len(ticks),
            "identical": {key: values[0] for key, values in seen.items()
                          if len(set(values)) == 1},
            "varied": {key: span(values) for key, values in seen.items()
                       if len(set(values)) > 1}}


def scenario_inputs(inputs, board):
    """{run: its expectation, its name, and its scenario's directory} of
    each run whose expectation the record keeps in a scenario directory of
    its own (tools/evidence.py: M1's te-poc, at mvp/scenario/te-poc/; M0's
    two-guests is mvp/scenario/ itself, and its runs need neither)."""
    root = inputs.record / "mvp" / "scenario"
    found, loaded = {}, {}
    for run in board:
        if not NAME_FORM.fullmatch(run["expect"]):
            raise Refused(f"runs.tsv expectation {run['expect']!r}")
        paths = [directory / "expect" / run["expect"]
                 for directory in sorted(root.iterdir())
                 if directory.is_dir() and directory.name != "expect" and
                 (directory / "expect" / run["expect"]).is_file()]
        if len(paths) > 1:
            raise Refused(f"expectation {run['expect']} is in two "
                          f"scenarios")
        if paths:
            if paths[0] not in loaded:
                loaded[paths[0]] = json.loads(inputs.text("scenario",
                                                          paths[0]))
            found[run["run"]] = {"expect": loaded[paths[0]],
                                 "name": inputs.name(paths[0]),
                                 "directory": paths[0].parents[1]}
    return found


def guest_lines(run, prefixes, head):
    """RUN's domain lines (handoff-excerpt.log) that start HEAD after their
    domain's prefix (PREFIXES, the expectation's, by domain), in capture
    order: [(domain, the text after HEAD)]."""
    return [(domain, line[len(prefix + head):])
            for line in run["excerpt"].splitlines()
            for domain, prefix in enumerate(prefixes)
            if line.startswith(prefix + head)]


def report_channel(inputs, expect, directory):
    """The authority report EXPECT names, which must have the SHA-256 it
    names: its channel as BE_MVP:03 CHANNEL_CHECKED shows it, derived as
    tests/check-capture.py derives it (the send and receive grants'
    domains; the channel object's memory grants' GPA and size, the last
    one's, and the object's HPA; each endpoint's leaf, (HPA >> 12) << 10
    with its grant's derived flags; the configuration identity)."""
    want = expect["report"]
    if not NAME_FORM.fullmatch(want["file"]):
        raise Refused(f"an expectation names the report {want['file']!r}")
    path = directory / want["file"]
    report = json.loads(inputs.text("scenario", path))
    if inputs.used["scenario"][inputs.name(path)] != want["sha256"]:
        raise Refused(f"{inputs.name(path)} is not the report its "
                      f"expectation names (SHA-256)")
    index = {subject["name"]: subject["domain_index"]
             for subject in report["subjects"]}
    base = {item["name"]: int(item["extent"]["base"], 16)
            for item in report["objects"]}
    channels = [item for item in report["labeling"]["objects"]
                if item["class"] == "channel"]
    if len(channels) != 1:
        raise Refused(f"{inputs.name(path)} declares {len(channels)} "
                      f"channels")
    ends = {permission: index[grant["subject"]]
            for grant in report["grants"]
            if grant["object"] == channels[0]["name"]
            for permission in grant["permissions"]}
    leaves, page = {}, None
    for grant in report["grants"]:
        derived = grant.get("derived")
        if grant["class"] != "memory" or not derived or \
                grant["object"] != channels[0]["object"]:
            continue
        hpa = base[grant["object"]]
        page = (derived["gpa"], hex(hpa), derived["size"])
        leaves[index[grant["subject"]]] = hex(
            (hpa >> 12) << 10 | int(derived["flags"], 16))
    if page is None:
        raise Refused(f"{inputs.name(path)} grants no memory on its channel")
    return dict(zip(("report", "channel", "writer", "reader", "gpa", "hpa",
                     "bytes", "writer_pte", "reader_pte", "config"),
                    (inputs.name(path), channels[0]["name"],
                     str(ends["send"]), str(ends["receive"])) + page +
                    (leaves[ends["send"]], leaves[ends["receive"]],
                     report["identity"]["configuration_identity"])))


def denial(domain, deny, report, entry):
    """One denial: its DENY line, its guest's MVPINIT 08 report, and the
    expectation's entry, each None where missing, with which of
    tests/check-capture.py's rule 2 comparisons hold and which do not:
    gpa (the line's, the report's, and the entry's), htval (the entry's
    GPA >> 2), stval=va, and sepc=pc."""
    equal, differ = [], []
    if deny and report:
        gpa = number(entry["gpa"] if entry else deny["gpa"])
        for name, holds in (
                ("gpa", number(deny["gpa"]) == number(report["gpa"]) == gpa),
                ("htval", number(deny["htval"]) == gpa >> 2),
                ("stval=va", number(deny["stval"]) == number(report["va"])),
                ("sepc=pc", number(deny["sepc"]) == number(report["pc"]))):
            (equal if holds else differ).append(name)
    return {"domain": domain, "deny": deny, "report": report,
            "expected": entry and {key: entry[key]
                                   for key in ("access", "kind", "gpa")},
            "equal": equal, "differ": differ}


def denials(board, scenarios):
    """Each te-poc run's denials, paired as tests/check-capture.py pairs
    them (planning/mvp-m1-plan.md, "The denial log against the guests'
    reports"): for each domain, its i-th DENY line in capture order (hart
    0's lines, result.json), its guest's i-th MVPINIT 08 report
    (handoff-excerpt.log), and the expectation's i-th denial."""
    out = []
    for run in [run for run in board if run["image"] == "te-poc"]:
        if run["run"] not in scenarios:
            raise Refused(f"{run['run']}: no te-poc expectation in a "
                          f"scenario directory")
        expect = scenarios[run["run"]]["expect"]
        prefixes = [binding["prefix"] for binding in expect["domains"]]
        log, reports = {}, {}
        for line in run["markers"]:
            if line.startswith(DENY):
                deny = line_fields(line[len(DENY):], DENY_FIELDS)
                log.setdefault(int(deny["domain"]), []).append(deny)
        for domain, text in guest_lines(run, prefixes, DENIED):
            reports.setdefault(domain, []).append(
                line_fields(text, DENIED_FIELDS, 1))
        out.append({"run": run["run"], "toolchain": run["toolchain"],
                    "verdict": run["verdict"],
                    "expect": scenarios[run["run"]]["name"], "denials": [
                        denial(domain, *entries)
                        for domain in sorted(set(range(len(prefixes))) |
                                             set(log))
                        for entries in itertools.zip_longest(
                            log.get(domain, []), reports.get(domain, []),
                            expect["denials"].get(str(domain), []))]})
    return out


def channel(inputs, board, scenarios):
    """Each run of a scenario with a channel (its expectation names an
    authority report): its BE_MVP:03 CHANNEL_CHECKED lines beside the
    report's channel, with the fields that differ from it; its BE_MVP:05
    CHANNEL_CLEARED lines; and each guest's MVPINIT 07 line, with whether
    the run's one writer's and one reader's digests are equal."""
    reports, checked, cleared, guests = {}, [], [], []
    for run in board:
        found = scenarios.get(run["run"], {"expect": {}})
        expect = found["expect"]
        # M2's scenarios have pages, not one channel: the M2 sections'.
        if "report" not in expect or "pages" in expect:
            continue
        want = report_channel(inputs, expect, found["directory"])
        reports[want["report"]] = want
        for line in [line_fields(marker[len(CHECKED):], CHECKED_FIELDS)
                     for marker in run["markers"]
                     if marker.startswith(CHECKED)] or [None]:
            checked.append({
                "run": run["run"], "image": run["image"],
                "report": want["report"], "line": line,
                "differ": line and [
                    key for key in CHECKED_FIELDS[1:]
                    if key != "level0" and (line[key] != want[key]
                                            if key == "config" else
                                            number(line[key]) !=
                                            number(want[key]))]})
        cleared += [[run["run"], run["image"]] + [
            (line or {}).get(key) for key in CLEARED_FIELDS]
            for line in [line_fields(marker[len(CLEARED):], CLEARED_FIELDS)
                         for marker in run["markers"]
                         if marker.startswith(CLEARED)] or [None]]
        lines = []
        for domain, text in guest_lines(run, [
                binding["prefix"] for binding in expect["domains"]],
                CHANNEL):
            role = dict(pairs(text)).get("role")
            if role not in CHANNEL_FIELDS:
                raise Refused(f"{run['run']}: an MVPINIT 07 line with role "
                              f"{role!r}")
            lines.append((domain, line_fields(text, CHANNEL_FIELDS[role])))
        digests = [[fields["digest"] for _, fields in lines
                    if fields["role"] == role] for role in CHANNEL_FIELDS]
        same = None if list(map(len, digests)) != [1, 1] else \
            "equal" if digests[0] == digests[1] else "differ"
        guests += [[run["run"], domain] + [
            (fields or {}).get(key) for key in CHANNEL_COLUMNS] + [same]
            for domain, fields in lines or [(None, None)]]
    return {"reports": [reports[name] for name in sorted(reports)],
            "checked": checked, "cleared": cleared, "guests": guests}


def same(value, wanted):
    """Whether a line's field is a report's value, numbers by value."""
    if value == wanted:
        return True
    return None not in (value, wanted) and number(str(value)) is not None \
        and number(str(value)) == number(str(wanted))


def report_pages(inputs, expect, directory):
    """The authority report EXPECT names, which must have the SHA-256 it
    names: each page as BE_MVP:03 PAGE_CHECKED shows it, derived as
    tests/check-capture.py derives it (a channel page's send and receive
    grants' domains, a secret page's one reader; its memory grants' GPA
    and size and its object's HPA; each end's leaf, (HPA >> 12) << 10 with
    its grant's derived flags; the configuration identity), and the
    offline measurement (planning/mvp-m2-plan.md, Q7)."""
    want = expect["report"]
    if not NAME_FORM.fullmatch(want["file"]):
        raise Refused(f"an expectation names the report {want['file']!r}")
    path = directory / want["file"]
    report = json.loads(inputs.text("scenario", path))
    if inputs.used["scenario"][inputs.name(path)] != want["sha256"]:
        raise Refused(f"{inputs.name(path)} is not the report its "
                      f"expectation names (SHA-256)")
    names = [page["name"] for page in expect["pages"]]
    index = {subject["name"]: subject["domain_index"]
             for subject in report["subjects"]}
    base = {item["name"]: int(item["extent"]["base"], 16)
            for item in report["objects"]}
    channels = {item["name"]: item["object"]
                for item in report["labeling"]["objects"]
                if item["class"] == "channel"}
    ends, leaves, extents = {}, {}, {}
    for grant in report["grants"]:
        if grant["class"] == "channel":
            for permission in grant["permissions"]:
                ends.setdefault(channels[grant["object"]], {})[
                    permission] = str(index[grant["subject"]])
        derived = grant.get("derived")
        if grant["class"] == "memory" and derived and \
                grant["object"] in names:
            hpa = base[grant["object"]]
            leaves.setdefault(grant["object"], {})[
                str(index[grant["subject"]])] = hex(
                    (hpa >> 12) << 10 | int(derived["flags"], 16))
            extents[grant["object"]] = (derived["gpa"], derived["size"])
    pages = []
    for page in expect["pages"]:
        name, kind = page["name"], page["kind"]
        own = leaves.get(name, {})
        writer, reader = (ends[name]["send"], ends[name]["receive"]) \
            if kind == "channel" else (None, next(iter(own), None))
        pages.append(dict(zip(("page", "name") + PAGE_COLUMNS, (
            str(page["index"]), name, kind, writer, reader,
            extents[name][0], hex(base[name]), extents[name][1],
            own.get(writer), own.get(reader),
            report["identity"]["configuration_identity"]))))
    return {"report": inputs.name(path), "pages": pages,
            "measurement_hex": report.get("measurement_hex")}


def guest_calls(run, prefixes):
    """RUN's management calls as each guest reports them (MVPINIT 10), a
    burst line standing for its count: {domain: [(fid, target, result,
    the line)]}."""
    calls = {}
    for domain, text in guest_lines(run, prefixes, "MVPINIT 10 MGMT "):
        match = GUEST_CALL.fullmatch("MVPINIT 10 MGMT " + text)
        if match:
            calls.setdefault(domain, []).extend(
                [(match.group(2), match.group(3), match.group(4),
                  "MVPINIT 10 MGMT " + text)] * int(match.group(1) or 1))
    return calls


def ipi_probes(run, timebase):
    """RUN's BE_MVP:11 IPI_PROBE lines (result.json) beside the capture
    checker's costs (check.txt; Plan revision M2-A.1): each probe's times
    and SPV, and, for one the checker recorded as served inside a
    management wait of its hart (IN_WAIT, WAIT_SEQ), the BE_MVP:MGMT line
    of that domain and seq whose wait, [ticks, ticks + service], holds
    its received=: the request's function, ticks, and service, the
    receipt's offset into the wait, and both in milliseconds at
    TIMEBASE."""
    costs = dict(run["BE_MVP_COSTS"])
    waits = {(fields["domain"], fields["seq"]): fields for fields in (
        line_fields(mark[len(MGMT):], MGMT_FIELDS)
        for mark in run["markers"] if mark.startswith(MGMT))}
    rows = []
    for mark in run["markers"]:
        if not mark.startswith(IPI_PROBE):
            continue
        probe = line_fields(mark[len(IPI_PROBE):], IPI_FIELDS)
        domain = probe["domain"]
        inside = costs.get(IN_WAIT.format(domain))
        wait = waits.get((domain, costs.get(WAIT_SEQ.format(domain))))
        if inside is not None and (inside != "1" or wait is None):
            raise Refused(f"{run['run']}: the costs put G{domain}'s probe "
                          f"in no BE_MVP:MGMT line's wait")
        start = number(wait["ticks"]) if wait else None
        end = start + number(wait["service"]) if wait else None
        rows.append([run["run"], run["toolchain"],
                     f"G{domain} (hart {probe['hart']})"] + [
            probe[key] for key in IPI_FIELDS[2:]] + [inside] + (
            [wait["seq"], wait["fid"], wait["ticks"], wait["service"],
             hex(number(probe["received"]) - start)] if wait else
            [None] * 5) + [
            milliseconds(probe["received"], timebase),
            f"{milliseconds(wait['ticks'], timebase)}.."
            f"{milliseconds(hex(end), timebase)}" if wait else None])
    return rows


def anchor_facts(inputs, board, scenarios, timebase):
    """M2's facts (planning/mvp-m2-plan.md, "Platform record"), for each
    run of a scenario with pages (its expectation names them: anchor and
    its negatives): its PAGE_CHECKED lines beside the report's pages, and
    its PAGE_CLEARED and SECRET_PLACED lines; the measurement (MEASURED
    with its ticks, the report's offline value, the measured domain's
    DOMAIN_TERMINATED value, and a measurement failure's DETAIL); each
    management request (hart 0's line: the requester and its state as hart
    0's transitions before the line give it, the function, the target, the
    result, the target's state, and the ticks from the request to the
    answer, service=) beside its guest's report of the call, and each call
    its hart answered alone; the paused and terminated transitions with
    their exit counts; each request's and response's digest beside
    the offline one (the expectation's); and each anchor run's IPI
    probes beside the checker's costs (ipi_probes(); Plan revision
    M2-A)."""
    out = {key: [] for key in ("reports", "pages", "placed", "measurement",
                               "requests", "transitions", "digests",
                               "ipi_runs", "ipi_probes")}
    reports = {}
    for run in board:
        found = scenarios.get(run["run"])
        if not found or "pages" not in found["expect"]:
            continue
        expect = found["expect"]
        want = report_pages(inputs, expect, found["directory"])
        reports[want["report"]] = want
        marks, name = run["markers"], [run["run"], run["image"]]
        prefixes = [binding["prefix"] for binding in expect["domains"]]
        checked = {line.get("page"): line for line in (
            dict(pairs(mark[len(PAGE_CHECKED):])) for mark in marks
            if mark.startswith(PAGE_CHECKED))}
        out["pages"] += [{"run": run["run"], "image": run["image"],
                          "page": page["page"],
                          "line": checked.get(page["page"]), "differ": None
                          if page["page"] not in checked else [
                              key for key in PAGE_COLUMNS if not same(
                                  checked[page["page"]].get(key),
                                  page[key])]} for page in want["pages"]]
        out["placed"] += [name + [mark.split(" ", 2)[1]] + [
            dict(pairs(mark.split(" ", 2)[2])).get(key)
            for key in ("page", "hpa", "bytes", "ticks")]
            for mark in marks if mark.startswith(PLACED)]
        measured = next((dict(pairs(mark[len(MEASURED):])) for mark in marks
                         if mark.startswith(MEASURED)), {})
        detail = next((dict(pairs(mark[len(DETAIL):])) for mark in marks
                       if mark.startswith(DETAIL) and " computed=" in mark),
                      {})
        states, rows, domain = {}, [], str(expect["measurement"]["domain"])
        calls = guest_calls(run, prefixes)
        used = {}
        for mark in marks:
            end = next((head for head in ENDS if mark.startswith(head)),
                       None)
            if end:
                fields = dict(pairs(mark[len(end):]))
                states[fields["domain"]] = end.split()[1][len("DOMAIN_"):] \
                    .lower()
                if end != ENDS[2]:
                    out["transitions"].append(name + [
                        end.split()[1], fields.get("hart"),
                        fields.get("domain"), fields.get("by"),
                        fields.get("exits"), fields.get("sha256", "-"),
                        fields.get("ticks"), milliseconds(
                            fields.get("ticks"), timebase)])
            if not mark.startswith(MGMT):
                continue
            fields = line_fields(mark[len(MGMT):], MGMT_FIELDS)
            requester = int(fields["domain"])
            named = [call for call in calls.get(requester, [])
                     if call[0] in ("pause", "terminate")]
            at = used[requester] = used.get(requester, 0) + 1
            rows.append(name + [
                f"G{requester} (hart {fields['hart']})",
                states.get(fields["domain"], "running"), fields["seq"],
                fields["fid"], fields["target"], fields["result"],
                SBI_RESULTS.get(fields["result"], "-"),
                fields["target_state"], fields["ticks"], fields["service"],
                milliseconds(fields["service"], timebase),
                named[at - 1][3] if at <= len(named) else None])
        rows += [name + [f"G{requester}", "running", "-", call[0], call[1],
                         call[2], SBI_RESULTS.get(call[2], "-"), "-", "-",
                         "-", "-", call[3]]
                 for requester, own in sorted(calls.items())
                 for call in own if call[0] not in ("pause", "terminate")]
        out["requests"] += rows
        out["measurement"].append(name + [
            run["toolchain"], run["verdict"], measured.get("bytes"),
            measured.get("sha256") or detail.get("computed"),
            measured.get("ticks"), milliseconds(measured.get("ticks"),
                                                timebase),
            want["measurement_hex"], next(
                (row[7] for row in out["transitions"]
                 if row[:2] == name and row[2] == "DOMAIN_TERMINATED" and
                 row[4] == domain), None), detail.get("expected")])
        digests = {}
        for _, text in guest_lines(run, prefixes, "MVPINIT 09 "):
            match = GUEST_DIGEST.fullmatch("MVPINIT 09 " + text)
            if match:
                digests[match.group(1), match.group(2)] = \
                    match.group(3) or "timeout=1"
        for item in expect["requests"]["messages"] if digests else ():
            key = str(item["n"])
            got = [digests.get((kind, key)) for kind in ("REQUEST",
                                                         "RESPONSE")]
            offline = item.get("digest", "unanswered")
            out["digests"].append(name + [key] + got + [
                offline, "equal" if got[0] == got[1] == offline else
                "-" if None in got else "differ"])
        if run["image"] == "anchor":
            out["ipi_runs"].append(run["run"])
            out["ipi_probes"] += ipi_probes(run, timebase)
    out["reports"] = [reports[report] for report in sorted(reports)]
    return out


def milliseconds(ticks, timebase):
    """TICKS (hex) as milliseconds at TIMEBASE, or None."""
    value = number(ticks or "")
    return None if value is None else f"{value * 1000 / timebase:.3f}"


# M9's measurement log (planning/mvp-m9-plan.md, D-4, D-6, D-10;
# mvp/docs/log-profile.md): each run's log as the capture checker rebuilt
# it (result.json's log), by stream; R2's stream 0 a self-report.
LOG_STREAMS = (
    (0, "Stream 0: the platform and monitor (R2, a self-report)"),
    (1, "Stream 1: the configuration (R3)"))
ZERO = "0" * 64


def log_facts(board, timebase):
    """M9's facts, one row per run whose result.json carries the checker's
    log record: each stream's register at the barrier and the terminal
    and its replay (unprotected); stream 0's self-report against the
    reference (equal, differs and which, declared by self-report-flip, or
    dropped); each launched domain's LAUNCH register and DOMAIN_TERMINATED
    digest; the hashing ticks and the log's console volume; the loader
    observation beside them, as the run's own facts give it; and, per
    image, how many register values its runs show."""
    out = {"runs": len(board), "logged": [], "streams": {0: [], 1: []},
           "launch": [], "ticks": [], "loader": [], "images": []}
    seen = {}
    for run in board:
        log = run.get("log")
        if not log:
            continue
        name = [run["run"], run["image"], run["toolchain"]]
        registers = log.get("registers") or {}
        barrier, terminal, replayed = (registers.get(key) or [None] * 4
                                       for key in ("barrier", "terminal",
                                                   "replayed"))
        found = [item.split(": ", 1)[-1] for item in
                 log.get("self_report") or []]
        report = "dropped" if log.get("r2") == "dropped" else \
            "differs: " + ", ".join(found) + (
                " (declared)" if run.get("log_declared") else "") \
            if found else "equal"
        out["logged"].append(run["run"])
        out["streams"][0].append(name + [log.get("r2"), barrier[0],
                                         terminal[0], replayed[0], report])
        out["streams"][1].append(name + [barrier[1], terminal[1],
                                         replayed[1]])
        launched = (log.get("contract") or {}).get("sequence") != "probe"
        for domain in (0, 1) if launched else ():
            terminated = [dict(pairs(mark.split(" ", 2)[2])).get("sha256")
                          for mark in run["markers"] if mark.startswith(
                              "BE_MVP:12 DOMAIN_TERMINATED ") and
                          f" domain={domain} " in mark]
            out["launch"].append(name + [
                domain, (log.get("launch") or {}).get(str(domain)),
                barrier[2 + domain], terminal[2 + domain],
                replayed[2 + domain], terminated[0] if terminated else None])
        ticks = log.get("ticks") or {}
        launch = ticks.get("launch") or {}
        out["ticks"].append(name + [
            ticks.get("barrier"), milliseconds(ticks.get("barrier"),
                                               timebase),
            launch.get("0"), milliseconds(launch.get("0"), timebase),
            launch.get("1"), milliseconds(launch.get("1"), timebase),
            log.get("lines"), log.get("volume_bytes")])
        facts = run.get("facts") or {}
        out["loader"].append(name + [
            facts.get("load_digest_kind", "none"), facts.get("load_digest"),
            (run.get("attribution") or "none").split(" ")[0],
            log.get("boot_image")])
        runs, values = seen.setdefault((run["image"], run["toolchain"]),
                                       ([], [set() for _ in range(4)]))
        runs.append(run["run"])
        for index, value in enumerate(replayed):
            values[index].add(value)
    out["images"] = [[image, toolchain, len(runs)] + [
        "zero" if values[index] == {ZERO} else
        f"one: {next(iter(values[index]))[:16]}" if
        len(values[index]) == 1 else f"{len(values[index])} values"
        for index in range(4)]
        for (image, toolchain), (runs, values) in sorted(seen.items())]
    return out


def log_sections(facts):
    """M9's sections (log_facts()), or one that says the log was not run
    when no run carries it (a record made before M9)."""
    if not facts["logged"]:
        return [f"## The measurement log\n\nNot run: none of this record's "
                f"{facts['runs']} runs carries M9's measurement log "
                f"(planning/mvp-m9-plan.md; mvp/docs/log-profile.md), so it "
                f"has no register, launch register, self-report, or hashing "
                f"time to show. The loader observation, where a run has "
                f"one, is the runs' own (Runs, Attribution).\n"]
    out = [f"## The measurement log\n\nEach run's log as the capture "
           f"checker rebuilt it from hart 0's `BE_MVP:19` and `:20` lines "
           f"and compared it with the image's reference manifest "
           f"(`result.json`'s log; `check.txt`'s `BE_MVP_LOG` lines; "
           f"mvp/docs/log-profile.md): {len(facts['logged'])} of the "
           f"record's {facts['runs']} runs. Each register is printed at the "
           f"barrier and before the terminal line, and replayed from the "
           f"records by the checker, a value labelled unprotected; the "
           f"registers are software values in hart 0's memory, not PCRs, "
           f"and the log is a local identity, not evidence of the bytes "
           f"after the point of measurement. Per image, the values its "
           f"runs show:\n",
           table(["Image", "Toolchain", "Runs", "`r0`", "`r1`", "`r2`",
                  "`r3`"], facts["images"])]
    for stream, title in LOG_STREAMS:
        out += [f"### {title}\n\n" + (
            "Stream 0's digests are the monitor's own report of its text "
            "and read-only data, compared offline with the reference and "
            "gating nothing: `equal`, `differs` with the ranges that do "
            "(self-report-flip's run declares its one), or `dropped` when "
            "the profile keeps no R2 record.\n" if stream == 0 else
            "The core identity and the console grants, measured, and the "
            "build's identities, informational, are this stream's "
            "records.\n"),
            table(["Run", "Image", "Toolchain"] + (["R2"] if stream == 0
                                                   else []) +
                  ["At the barrier", "At the terminal", "Replay"] + (
                      ["Self-report"] if stream == 0 else []),
                  facts["streams"][stream])]
    out += ["### Streams 2 and 3: each domain's launch register (R4)\n\n"
            "Each launched domain's `BE_MVP:06 LAUNCH` register beside its "
            "stream's register at the barrier and the terminal, the replay, "
            "and its `DOMAIN_TERMINATED` digest where it was terminated (the "
            "stored register read again, not a second hash; `-` for none):\n",
            table(["Run", "Image", "Toolchain", "Domain", "LAUNCH",
                   "At the barrier", "At the terminal", "Replay",
                   "`DOMAIN_TERMINATED`"], facts["launch"]),
            "### The hashing time and the console volume\n\nHart 0's "
            "hashing ticks before the barrier (the barrier's total, "
            "saturated at `0xffffffff`, and each domain's LAUNCH line's), "
            "recorded and judged by their form alone, in milliseconds at "
            "the platform's timebase, and the log's lines and bytes:\n",
            table(["Run", "Image", "Toolchain", "Barrier `ticks`", "ms",
                   "Domain 0", "ms", "Domain 1", "ms", "Lines", "Bytes"],
                  facts["ticks"]),
            "### The loader observation, beside the log\n\nU-Boot's digest "
            "of the loaded boot image (`md5` on the board, `crc32` in the "
            "rehearsal, none in a direct QEMU boot) and the run's "
            "attribution, as the run's facts give them: attribution of the "
            "run to its image and nothing more, never in the log; and the "
            "boot image the checker bound to the reference:\n",
            table(["Run", "Image", "Toolchain", "Digest kind", "Digest",
                   "Attribution", "Boot image"], facts["loader"])]
    return out


def typing_fields(text):
    """A typing record's key=value fields, a value running to the next
    ` key=` (k3-uboot.py input-judge's `fast_pacing=lost 2` among them);
    the first of each key."""
    found = {}
    for line in text.splitlines():
        for key, value in re.findall(r"(?:^| )([a-z_0-9]+)=(.*?)"
                                     r"(?= [a-z_0-9]+=|$)", line):
            found.setdefault(key, value)
    return found


def console_facts(board):
    """Console input on K3 (mvp/README.md, item 115): each typed
    characterization (a run with characterization.txt: the class, the
    pacing results, the counts, and each repetition's bytes received with
    its nominal and measured pacing) and each typed session (a run whose
    typist typed a session: its steps and keys, the session file, the
    BE_MVP:15 grants, the :16 focus lines, the :17 drops, and the :18
    accounting the capture checker recorded, beside the keys typed)."""
    out = {"runs": len(board), "characterizations": [], "repetitions": [],
           "sessions": []}
    for run in board:
        name = [run["run"], run["image"], run["toolchain"]]
        typing = run.get("typing") or {}
        if "characterization.txt" in typing:
            facts = typing_fields(typing["characterization.txt"])
            out["characterizations"].append(
                name + [facts.get(key) for key in CHARACTERIZATION])
            pacing = (facts.get("pacing_ms") or "").split(",")
            for index, item in enumerate(
                    (facts.get("repetitions") or "").split(",")):
                repetition, _, received = item.partition(":")
                if repetition:
                    out["repetitions"].append([
                        run["run"], repetition,
                        REPETITION_MS.get(repetition), received,
                        pacing[index] if index < len(pacing) else None])
        typist = run.get("typist") or ""
        if not typist.startswith("session "):
            continue
        steps = re.search(r"guest-type steps=(\d+) keys=\d+", typist)
        session = typing_fields(typing.get("session.txt", ""))
        keys = sum(line.startswith("+") for line in
                   typing.get("typed.txt", "").splitlines())
        marks, facts = run.get("markers") or [], run.get("facts") or {}
        armed = [dict(pairs(mark.split(" ", 2)[2])).get("grants")
                 for mark in marks if mark.startswith("BE_MVP:15 ")]
        read = facts.get("input_read")
        out["sessions"].append(name + [
            run.get("verdict"),
            pathlib.PurePosixPath(session.get("session", "")).name or None,
            (session.get("sha256") or "")[:12] or None,
            steps.group(1) if steps else None, keys,
            armed[0] if armed else None,
            sum(mark.startswith("BE_MVP:16 ") for mark in marks),
            ", ".join(mark.split(" ", 2)[2] for mark in marks
                      if mark.startswith("BE_MVP:17 ")) or "none",
            read, facts.get("input_delivered"), facts.get("input_dropped"),
            None if read is None else
            "equal" if read == str(keys) else "differs"])
    return out


def console_sections(facts):
    """Console input on K3 (console_facts()), or a section that says it
    was not run when no run typed into the MVP."""
    if not facts["characterizations"] and not facts["sessions"]:
        return [f"## Console input on K3\n\nNot run: none of this record's "
                f"{facts['runs']} runs is a typed characterization of the "
                f"firmware console's input (`characterization.txt`, "
                f"tools/k3-input-characterize.sh) or a typed session "
                f"(tools/k3-console.sh guest-type; planning/mvp-m7-plan.md, "
                f"D-11, D-12; board policy item 8).\n"]
    out = ["## Console input on K3\n\nThe console tool's typing into the "
           "MVP under board policy item 8 (Plan revision S3-C; "
           "planning/mvp-m7-plan.md, D-11 and D-12), from each run's own "
           "records: diagnostic bring-up facts for this board's firmware "
           "console and the typing path, not hardware validation. The "
           "operator at the console and the typing tool are trusted "
           "inputs (the claim's required limit).\n"]
    if facts["characterizations"]:
        out += ["### The typed characterization\n\nEach "
                "`characterization.txt` (tools/k3-uboot.py input-judge, then "
                "the driver's lines): the class (supplies, absent, blocks, "
                "loses, or corrupts) at the plan's 10 ms per byte and at "
                "1 ms, the bytes the probe received of those typed, its "
                "polls, and the verdict (stop 10 unless the 10 ms "
                "repetitions supply):\n",
                table(["Run", "Image", "Toolchain", "Class", "10 ms",
                       "1 ms", "Received", "Typed", "Polls",
                       "Nonzero polls", "Max per poll", "Errors",
                       "Before the fourth", "Verdict"],
                      facts["characterizations"]),
                "Each repetition of Q14's 64-byte text: its nominal pacing, "
                "the bytes received of those typed (by the greedy match), "
                "and the pacing measured at the typist, in ms per byte:\n",
                table(["Run", "Repetition", "Nominal ms", "Received",
                       "Measured ms"], facts["repetitions"])]
    else:
        out.append("### The typed characterization\n\nNot run in this "
                   "record (M7's record holds the board's).\n")
    if facts["sessions"]:
        out += ["### The typed sessions\n\nEach session typed into a "
                "shell image's run (tools/k3-console.sh guest-type, a fresh "
                "nonce each): its file, its steps and the keys in "
                "`typed.txt`, hart 0's `BE_MVP:15` grants, `:16` focus lines, "
                "and `:17` drops, and the capture checker's `:18` "
                "accounting (bytes read, each domain's delivered, the drops "
                "by reason), the bytes read beside the keys typed:\n",
                table(["Run", "Image", "Toolchain", "Verdict", "Session",
                       "SHA-256", "Steps", "Keys typed", "`:15` grants",
                       "`:16` lines", "`:17` drops", "`:18` read",
                       "Delivered", "Dropped", "Read and keys"],
                      facts["sessions"])]
    else:
        out.append("### The typed sessions\n\nNot run in this record.\n")
    return out


def self_test():
    """log_facts() and log_sections() on synthetic runs: a record with no
    M9 run renders its log as not run; one with a complete te-poc run, a
    self-report-flip run, a probe, and a run with R2 dropped renders each
    stream's values, the launch registers, the self-report, the ticks in
    milliseconds, and the loader observation. console_facts() and
    console_sections() likewise (item 115): a record with no typed run
    renders console input as not run; a typed characterization and two
    typed sessions render each field from its record."""
    def run(name, image, log, declared=(), facts=None, markers=()):
        return {"run": name, "image": image, "toolchain": "gcc", "log": log,
                "log_declared": list(declared), "facts": facts or {},
                "markers": list(markers), "attribution": "PASS selected=yes"}

    def log(sequence, values, self_report=(), r2="kept"):
        registers = [value * 64 for value in values]
        return {"contract": {"sequence": sequence, "run": "complete"},
                "r2": r2, "registers": {"barrier": registers,
                                        "terminal": registers,
                                        "replayed": registers},
                "self_report": list(self_report), "lines": 17,
                "volume_bytes": 4557, "boot_image": "nominal",
                "ticks": {"barrier": "0x2a3f10", "launch": {
                    "0": "0x10a2c0", "1": "0x10a1f8"}} if sequence !=
                "probe" else {"barrier": "0x1000", "launch": {}},
                "launch": {"0": registers[2], "1": registers[3]}
                if sequence != "probe" else {}}
    flip = "self-report differs: mvp-rodata"
    board = [run("20261103T000000Z", "te-poc", log("v2", "abcd"),
                 facts={"load_digest_kind": "md5", "load_digest": "f" * 32},
                 markers=["BE_MVP:12 DOMAIN_TERMINATED hart=2 domain=1 by=0 "
                          "exits=4 sha256=" + "d" * 64 + " ticks=0x10"]),
             run("20261103T000100Z", "self-report-flip", log(
                 "v2", "ebcd", [flip]), [flip]),
             run("20261103T000200Z", "probe-platform", log("probe", "ab00")),
             run("20261103T000300Z", "two-guests", log(
                 "v1", "0bcd", r2="dropped")),
             run("20261103T000400Z", "te-poc", log("v2", "abcd"))]
    facts, empty = log_facts(board, 24000000), log_facts(board[:0] + [
        dict(board[0], log=None)], 24000000)
    text, none = "\n".join(log_sections(facts)), "\n".join(log_sections(
        empty))
    checks = [
        ("no M9 run: the log not run, and nothing else",
         none.startswith("## The measurement log\n\nNot run: none of this "
                         "record's 1 runs") and "|" not in none),
        ("five logged runs, each stream's rows",
         len(facts["logged"]) == 5 and len(facts["streams"][0]) == 5 and
         len(facts["streams"][1]) == 5),
        ("the self-report: equal, declared, and dropped",
         [row[-1] for row in facts["streams"][0]] == [
             "equal", "differs: mvp-rodata (declared)", "equal", "dropped",
             "equal"]),
        ("each launched domain's register; none for the probe",
         [(row[1], row[3]) for row in facts["launch"]] == [
             (image, domain) for image in ("te-poc", "self-report-flip",
                                           "two-guests", "te-poc")
             for domain in (0, 1)] and facts["launch"][1][4:] == [
                 "d" * 64] * 5 and facts["launch"][0][-1] is None),
        ("the ticks in milliseconds at the timebase",
         facts["ticks"][0][3:9] == ["0x2a3f10", "115.361", "0x10a2c0",
                                    "45.427", "0x10a1f8", "45.418"]),
        ("the loader observation beside the log, as the run gives it",
         facts["loader"][0][3:] == ["md5", "f" * 32, "PASS", "nominal"] and
         facts["loader"][1][3:5] == ["none", None]),
        ("per image: te-poc's two runs, one value each",
         ["te-poc", "gcc", 2, "one: " + "a" * 16, "one: " + "b" * 16,
          "one: " + "c" * 16, "one: " + "d" * 16] in facts["images"]),
        ("the rendering: the four sections and their tables",
         all(heading in text for heading in (
             "### Stream 0: the platform and monitor (R2, a self-report)",
             "### Stream 1: the configuration (R3)",
             "### Streams 2 and 3: each domain's launch register (R4)",
             "### The hashing time and the console volume",
             "### The loader observation, beside the log")) and
         "differs: mvp-rodata (declared)" in text)]
    # Console input on K3 (item 115): a typed characterization and two
    # typed sessions, each field from its record.
    characterization = (
        "class=supplies\npacing_10ms=supplies\nfast_pacing=lost 2\n"
        "total=254\npolls=2049\nnonzero_polls=209\nmax_per_poll=5\n"
        "errors=0\nreceived_bytes=254\ntyped_bytes=256\n"
        "repetitions=1:64/64,2:64/64,3:64/64,4:62/64\n"
        "slow_received_before_fourth=yes\npacing_ms=11.7,11.7,11.7,2.7\n"
        "capture=<repo>/s/serial.log capture_sha256=" + "a" * 64 + "\n"
        "typed_sha256=" + "b" * 64 + " keys=256\nsession=s run=r "
        "run_status=0\nverdict=PASS\n")
    typed = "# k3-console.sh guest-type\n" + "".join(
        f"+0.{index} 2026-11-04T00:00:00.000Z step=0 key=0x7e\n"
        for index in range(3))
    marks = ["BE_MVP:15 INPUT_ARMED grants=g0,g1 prefix=0x7e",
             "BE_MVP:16 FOCUS none", "BE_MVP:16 FOCUS g0",
             "BE_MVP:17 INPUT_DROP bad-sequence",
             "BE_MVP:18 INPUT read=3 g0=1:" + "c" * 16 + " g1=0:" + "d" * 16 +
             " dropped=bad-sequence:1"]

    def typed_run(name, read, characterized=False):
        out = dict(run(name, "probe-console-input" if characterized else
                       "two-guests-shell", None), verdict="PASS")
        if characterized:
            return dict(out, typist="probe typist_status=0 BE_MVP_K3_CONSOLE:"
                        " PASS probe-type repetitions=4 keys=256",
                        typing={"characterization.txt": characterization,
                                "typed.txt": typed})
        return dict(out, markers=marks, typist="session typist_status=0 "
                    "BE_MVP_K3_CONSOLE: PASS guest-type steps=16 keys=3",
                    facts={"input_read": read, "input_delivered": "g0=1,g1=0",
                           "input_dropped": "bad-sequence:1"},
                    typing={"session.txt": "session=<repo>/mvp/scenarios/"
                            "two-guests/sessions/shell.json sha256=" +
                            "e" * 64 + "\n", "typed.txt": typed})
    typing = console_facts([typed_run("20261104T000000Z", None, True),
                            typed_run("20261104T000100Z", "3"),
                            typed_run("20261104T000200Z", "4")])
    unrun = "\n".join(console_sections(console_facts(board[:1])))
    shown = "\n".join(console_sections(typing))
    alone = "\n".join(console_sections(console_facts(
        [typed_run("20261104T000100Z", "3")])))
    row, sessions = typing["characterizations"][0], typing["sessions"]
    checks += [
        ("no typed run: console input not run, and nothing else",
         unrun.startswith("## Console input on K3\n\nNot run: none of this "
                          "record's 1 runs") and "|" not in unrun),
        ("the characterization's class and its pacing results",
         row[3:6] == ["supplies", "supplies", "lost 2"]),
        ("the characterization's counts and verdict",
         row[6:] == ["254", "256", "2049", "209", "5", "0", "yes", "PASS"]),
        ("each repetition's bytes received, nominal and measured pacing",
         typing["repetitions"] == [
             ["20261104T000000Z", str(index), "10" if index < 4 else "1",
              "64/64" if index < 4 else "62/64",
              "11.7" if index < 4 else "2.7"] for index in range(1, 5)]),
        ("each session's file, steps, and keys typed",
         [item[4:8] for item in sessions] == [
             ["shell.json", "e" * 12, "16", 3]] * 2),
        ("each session's input records: :15 grants, :16 lines, :17 drops",
         [item[8:11] for item in sessions] == [["g0,g1", 2,
                                                "bad-sequence"]] * 2),
        ("the :18 accounting beside the keys typed: equal, and differs",
         [item[11:] for item in sessions] == [
             ["3", "g0=1,g1=0", "bad-sequence:1", "equal"],
             ["4", "g0=1,g1=0", "bad-sequence:1", "differs"]]),
        ("the rendering: both subsections, and sessions alone",
         "### The typed characterization\n\nEach" in shown and
         "### The typed sessions\n\nEach" in shown and
         "| 20261104T000000Z | 4 | 1 | 62/64 | 2.7 |" in shown and
         "### The typed characterization\n\nNot run in this record" in alone
         and "### The typed sessions\n\nEach" in alone)]
    for name, ok in checks:
        print(f"{'ok  ' if ok else 'FAIL'} {name}")
    failed = sum(not ok for _, ok in checks)
    status = "PASS" if not failed else "FAIL"
    print(f"BE_MVP_PLATFORM_RECORD_SELF_TEST: {status} cases={len(checks)} "
          f"failed={failed}")
    return 1 if failed else 0


def failures(others):
    """Each other run's BE_MVP:FAIL and :DETAIL lines among hart 0's, as
    the capture checker splits the capture (where a domain hart's own
    fallback lines would count too: Plan revision M1-B); its first FAIL
    and the DETAIL after it; each domain's lines the checker counted
    (g0=, g1= in BE_MVP_COUNTS); and the domains' lines after the first
    FAIL in handoff-excerpt.log."""
    rows = []
    for run in others:
        marks = run["markers"]
        first = next((index for index, line in enumerate(marks)
                      if line.startswith(FAIL)), None)
        excerpt = run["excerpt"].splitlines()
        cut = next((index for index, line in enumerate(excerpt)
                    if line.startswith(FAIL)), None)
        counts = dict(run["BE_MVP_COUNTS"])
        rows.append([run["run"], run["image"],
                     sum(line.startswith(FAIL) for line in marks),
                     sum(line.startswith(DETAIL) for line in marks)] + (
            [None, None] if first is None else [marks[first], next(
                (line for line in marks[first + 1:]
                 if line.startswith(DETAIL)), None)]) + [
            counts.get("g0"), counts.get("g1"),
            None if cut is None else sum(bool(GUEST_LINE.match(line))
                                         for line in excerpt[cut + 1:])])
    return rows


def m0_probes(inputs):
    """M0's board probe values, made after a kexec, by probe and label."""
    data = json.loads(inputs.text("probes", M0_RECORD /
                                  "platform-record.json"))
    return {(row["probe"], row["label"]): row for row in data["probes"]}


def collect(record, suite):
    inputs = Inputs(record)
    bundle = dict(line.split("=", 1) for line in inputs.text(
        "runs", record / "mvp" / "bundle.txt").splitlines())
    images = {path: digest for digest, _, path in (
        line.partition("  ") for line in inputs.text(
            "runs", record / "mvp" / "images.sha256").splitlines())}
    pre = preflight(inputs)
    pre["pair"] = preflight_pair(inputs)
    board = runs(inputs)
    probes, probe_runs, m0 = [], [], m0_probes(inputs)
    for probe in PROBES:
        mine = [run for run in board if run["image"] == probe]
        if not mine:
            continue
        probe_runs += [[run["run"], probe, run["result"], [
            line for line in run["markers"] if line[:9] in (
                "BE_MVP:02", "BE_MVP:08", "BE_MVP:09", "BE_MVP:10")]]
            for run in mine]
        last = mine[-1]
        gcc, clang = qemu(inputs, probe, suite, images)
        for label in [label for label in LABELS if label in last["values"]]:
            fields = last["values"][label]
            earlier = m0.get((probe, label), {})
            probes.append({
                "probe": probe, "label": label, "run": last["run"],
                "expected": PLAN[LABELS[label]],
                "reading": reading(label, dict(fields), last["facts"].get(
                    "started", "none")),
                "m0": [earlier.get("run"), earlier.get("reading")],
                "values": [fields, (earlier.get("values") or [None])[0],
                           gcc["values"].get(label),
                           clang["values"].get(label)],
                "qemu": [[gcc["source"], gcc["result"]],
                         [clang["source"], clang["result"]]]})
    serial = inputs.text("serial", inputs.record / SERIAL_NOTE).strip()
    if not serial:
        raise Refused(f"{SERIAL_NOTE} is empty")
    timebase = int(dict(pre["facts"])["timebase_frequency"])
    scenarios = scenario_inputs(inputs, board)
    others = [run for run in board if run["image"] not in
              PROBES + ("two-guests", "te-poc", "anchor")]
    pre["baseline"] = baseline(inputs, pre, board)
    data = {"schema": SCHEMA, "campaign": bundle["campaign"],
            "preflight": pre, "runs": [run["row"] for run in board],
            "probe_runs": probe_runs, "probes": probes,
            "serial_log": " ".join(serial.split()),
            "resets": resets(inputs, board),
            "scenario": scenario(board, timebase),
            "te_poc": scenario(board, timebase, "te-poc",
                               COUNTS + DENIAL_COUNTS),
            "anchor": scenario(board, timebase, "anchor",
                               COUNTS + DENIAL_COUNTS + MGMT_COUNTS),
            "m2": anchor_facts(inputs, board, scenarios, timebase),
            "log": log_facts(board, timebase),
            "console": console_facts(board),
            "denials": denials(board, scenarios),
            "channel": channel(inputs, board, scenarios),
            "other_runs": [run["row"][:6] + [run["result"], " / ".join(
                run["markers"][-2:])] for run in others],
            "failures": failures(others)}
    data["sources"] = inputs.used
    return data


def table(header, rows):
    def cell(value):
        return "-" if value in (None, "") else str(value).replace("|", "\\|")
    return "\n".join(["| " + " | ".join(header) + " |",
                      "|" + " --- |" * len(header)] +
                     ["| " + " | ".join(map(cell, row)) + " |"
                      for row in rows]) + "\n"


def block(lines):
    return "```text\n" + "\n".join(lines) + "\n```\n"


def code(names):
    """NAMES, each in backquotes, comma-separated."""
    return ", ".join(f"`{name}`" for name in names)


def baseline_section(base, runs):
    """The firmware and kernel beside M0's record (baseline())."""
    return [
        "### Firmware and kernel beside M0's record\n\nThe firmware's "
        "identity and SBI specification in Fedora's log (the lines the "
        "preflight kept, under Fedora's log below) and the Fedora kernel "
        "release (the preflight's first `kernel=`, its `uname -r`), this "
        "record's beside M0's accepted record's "
        f"(`{base['m0']}`; planning/mvp-m1-plan.md, \"Platform record\", "
        "Preflight, and Q13):\n",
        table(["Fact", "This record", "M0's record", "Against M0's"],
              base["rows"]),
        "tools/k3-preflight.sh's own lines for the first, its stop 8: " +
        (", ".join(f"`{key}={value}`" for key, value in
                   base["firmware_lines"] if value is not None) or "none") +
        ". The U-Boot banner each run's `run.txt` names (`uboot_banner`, "
        "the firmware's own report): " +
        ("; ".join(f"`{value}` in {count} of {runs} runs"
                   for value, count in base["uboot_banners"]) or "none") +
        ".\n"]


def scenario_section(sc, counts):
    """One scenario's runs' tables (scenario()), its COUNTS first."""
    costs = sc["costs"]
    return [table(["Run", "Toolchain", "Verdict",
                   *[f"`{key}`" for key in counts], "`:13 ticks`",
                   "`:13 idle_ticks`"], sc["runs"]),
            "Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and "
            "its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):\n",
            table(["Run", *[f"`{key}`" for key in SHUTDOWN],
                   "PING sent, received, answered"], sc["domains"]),
            "The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; "
            "recorded only, no performance claim):\n",
            table(["Cost", *costs],
                  [[f"`{key}`"] + [dict(values).get(key)
                                   for values in costs.values()]
                   for key in dict.fromkeys(key for values in costs.values()
                                            for key, _ in values)]),
            "".join(f"- {line}.\n" for line in sc["budgets"]),
            f"The same in all {sc['passing']} passing runs:\n",
            table(["Field", "Value"], sorted(sc["identical"].items())),
            "Varied across them (lowest..highest):\n",
            table(["Field", "Range"], sorted(sc["varied"].items()))]


def denial_section(runs):
    """Denials on K3 (denials()): each te-poc run's table, then the
    comparisons' counts and the htinst values by the guest's kind."""
    header = (["Domain"] + [f"`{key}`" for key in DENY_FIELDS
                            if key != "domain"] +
              [f"Guest `{key}`" for key in DENIED_FIELDS] +
              ["Expected", "Equal", "Differs"])
    out = [
        "## Denials on K3\n\nFor each te-poc run, each of hart 0's "
        "`BE_MVP:DENY` lines (`result.json`) beside its guest's `MVPINIT 08 "
        "DENIED` report (`handoff-excerpt.log`) and the expected denial "
        "(`denials` in the run's expectation), paired as "
        "tests/check-capture.py pairs them (planning/mvp-m1-plan.md, \"The "
        "denial log against the guests' reports\"): for each domain, its "
        "i-th DENY line in capture order, its guest's i-th report, and the "
        "i-th expected denial; `-` marks one a run lacks. `ticks` is the "
        "exit's time since the barrier and `service` the post's time "
        "minus the exit's (planning/mvp-m1-plan.md, \"Markers\"). The plan "
        "records these as VU-mode accesses through Linux's VS stage, whose "
        "`htinst` M0's probe, run in VS mode with `vsatp` Bare, did not "
        "record (planning/mvp-m1-plan.md, \"Platform record\"). Equal and "
        "Differs sort the checker's rule 2 comparisons: `gpa`, the line's, "
        "the report's, and the expected one's; `htval`, the expected GPA "
        ">> 2; `stval=va`; and `sepc=pc`.\n"]
    found, holds, htinst = collections.Counter(), collections.Counter(), \
        collections.Counter()
    for run in runs:
        rows = []
        for item in run["denials"]:
            deny, report = item["deny"] or {}, item["report"] or {}
            entry = item["expected"]
            rows.append([item["domain"]] + [
                deny.get(key) for key in DENY_FIELDS if key != "domain"] + [
                report.get(key) for key in DENIED_FIELDS] + [
                entry and " ".join(entry[key] for key in (
                    "access", "kind", "gpa")),
                code(item["equal"]), code(item["differ"])])
            found.update(name for name in ("deny", "report", "expected")
                         if item[name])
            if deny and report:
                found["pairs"] += 1
                holds.update(item["equal"])
                htinst[report["kind"], deny["htinst"]] += 1
        out += [f"### `{run['run']}` ({run['toolchain']}, {run['verdict']}; "
                f"`{run['expect']}`)\n", table(header, rows)]
    out.append(
        f"Of the {found['deny']} DENY lines, {found['report']} reports, and "
        f"{found['expected']} expected denials in the {len(runs)} runs, "
        f"{found['pairs']} DENY lines have their report: `gpa` equal in "
        f"{holds['gpa']}, `htval` the expected GPA >> 2 in "
        f"{holds['htval']}, `stval=va` in {holds['stval=va']}, and "
        f"`sepc=pc` in {holds['sepc=pc']}. `htinst` by the guest's `kind`: "
        + ("; ".join(f"`{kind}` `{value}` in {count}" for (kind, value),
                     count in sorted(htinst.items())) or "none") + ".\n")
    return out


def channel_section(found):
    """The channel (channel()): each report's channel, each run's
    CHANNEL_CHECKED and CHANNEL_CLEARED lines, each guest's MVPINIT 07
    line, then the counts of the comparisons."""
    names = CHECKED_FIELDS[:6] + CHECKED_FIELDS[7:]
    lines = [item for item in found["checked"] if item["line"]]
    both = {row[0]: row[-1] for row in found["guests"]
            if row[-1] is not None}
    return [
        "## The channel\n\nEach run of a scenario with a channel (its "
        "expectation names an authority report, which must have the SHA-256 "
        "the expectation names): hart 0's `BE_MVP:03 CHANNEL_CHECKED` and "
        "`BE_MVP:05 CHANNEL_CLEARED` lines (`result.json`) and its guests' "
        "`MVPINIT 07 CHANNEL` lines (`handoff-excerpt.log`); `-` marks a "
        "line a run lacks. The report's channel, derived as "
        "tests/check-capture.py derives it (planning/mvp-m1-plan.md, \"The "
        "channel and the report\"): the domains of its `send` and `receive` "
        "grants; the GPA and size of its memory grants and the object's "
        "HPA; each endpoint's leaf, (HPA >> 12) << 10 with its grant's "
        "derived flags; and `identity.configuration_identity`:\n",
        table(["Report", *[f"`{key}`" for key in names]],
              [[f"`{item['report']}`"] + [item[key] for key in names]
               for item in found["reports"]]),
        "Each run's `CHANNEL_CHECKED` line, and the fields that differ "
        "from its report's (every field above but `channel`, a name in the "
        "report and an index in the line):\n",
        table(["Run", "Image", *[f"`{key}`" for key in CHECKED_FIELDS],
               "Differs from the report's"],
              [[item["run"], item["image"]] + [
                  (item["line"] or {}).get(key) for key in CHECKED_FIELDS] + [
                  None if item["differ"] is None else
                  code(item["differ"]) or "none"]
               for item in found["checked"]]),
        "Each run's `CHANNEL_CLEARED` line:\n",
        table(["Run", "Image", *[f"`{key}`" for key in CLEARED_FIELDS]],
              found["cleared"]),
        "Each guest's `MVPINIT 07 CHANNEL` line, and whether its run's "
        "writer's and reader's digests are equal (where it has one line "
        "of each):\n",
        table(["Run", "Domain", *[f"`{key}`" for key in CHANNEL_COLUMNS],
               "Writer's and reader's digests"], found["guests"]),
        f"Of the {len(lines)} `CHANNEL_CHECKED` lines, "
        f"{sum('config' not in item['differ'] for item in lines)} show "
        f"their report's configuration identity, and "
        f"{sum(not item['differ'] for item in lines)} differ from their "
        f"report's channel in no field compared. The writer's and the "
        f"reader's digests are equal in "
        f"{list(both.values()).count('equal')} of the {len(both)} runs "
        f"with one line of each.\n"]


def failure_section(rows):
    """The other runs' failure lines and guest line counts
    (failures())."""
    return [
        "Each other run's `BE_MVP:FAIL` and `BE_MVP:DETAIL` lines among "
        "hart 0's (`result.json`, as the capture checker splits the "
        "capture, where a domain hart's own fallback lines would count "
        "too: planning/mvp-m1-plan.md, Plan revision M1-B), its first FAIL "
        "and the DETAIL after it, each domain's lines the checker counted "
        "(`g0`, `g1` in `BE_MVP_COUNTS`, `check.txt`), and the domains' "
        "lines after the first FAIL (`handoff-excerpt.log`):\n",
        table(["Run", "Image", "FAIL lines", "DETAIL lines", "First FAIL",
               "The DETAIL after it", "`g0`", "`g1`",
               "Domain lines after the first FAIL"], rows)]


def probe_summary(m2):
    """The IPI probe in a management wait (ipi_probes()), as a fact where
    a run shows it and as not observed otherwise."""
    rows, runs = m2["ipi_probes"], len(m2["ipi_runs"])
    inside = [row for row in rows if row[7] == "1"]
    ones = f"Of the {len(rows)} probes, " \
        f"{sum(row[6] == '1' for row in rows)} show `spv=1`.\n"
    if not inside:
        return (f"Not observed: no probe of the {runs} anchor runs was "
                f"served inside a management wait. " + ones)
    return (f"Observed: a probe served inside a management wait in "
            f"{len({row[0] for row in inside})} of the {runs} anchor runs: "
            + "; ".join(f"`{row[0]}` {row[2]}, `received={row[4]}` "
                        f"({row[13]} ms) inside request {row[8]}'s "
                        f"(`{row[9]}`) wait, `ticks={row[10]}` "
                        f"`service={row[11]}` ({row[14]} ms), its PONG "
                        f"`spv={row[6]}`" for row in inside) + ". " + ones)


def anchor_sections(m2):
    """M2's sections (anchor_facts()): the pages, the management requests
    with the IPI probe in a management wait, the transitions, and the
    digests; M2's one measurement is M9's log's now (log_sections())."""
    checked = [item for item in m2["pages"] if item["line"]]
    paused = {(row[0], row[4]): row[6] for row in m2["transitions"]
              if row[2] == "DOMAIN_PAUSED"}
    answered = [row for row in m2["digests"] if row[-1] != "-"]
    return [
        "## The pages\n\nEach run of a scenario with pages "
        "(planning/mvp-m2-plan.md, \"Markers\"): hart 0's `BE_MVP:03 "
        "PAGE_CHECKED` lines (`result.json`) beside its report's pages, "
        "derived as tests/check-capture.py derives them (a channel page's "
        "`send` and `receive` grants' domains, a secret page's one reader; "
        "its memory grants' GPA and size and its object's HPA; each end's "
        "leaf, (HPA >> 12) << 10 with its grant's derived flags; and "
        "`identity.configuration_identity`):\n",
        table(["Report", "`page`", "Name", *[f"`{key}`" for key in
                                            PAGE_COLUMNS]],
              [[f"`{report['report']}`", page["page"], page["name"]] +
               [page[key] for key in PAGE_COLUMNS]
               for report in m2["reports"] for page in report["pages"]]),
        "Each run's `PAGE_CHECKED` line for each page, and the fields that "
        "differ from its report's (`-` marks a line a run lacks: a page "
        "check that refused prints none):\n",
        table(["Run", "Image", "`page`", *[f"`{key}`" for key in
                                           PAGE_COLUMNS],
               "Differs from the report's"],
              [[item["run"], item["image"], item["page"]] +
               [(item["line"] or {}).get(key) for key in PAGE_COLUMNS] +
               [None if item["differ"] is None else
                code(item["differ"]) or "none"] for item in m2["pages"]]),
        "Each run's `PAGE_CLEARED` and `SECRET_PLACED` lines (the secret "
        "page's address and bytes, never its contents):\n",
        table(["Run", "Image", "Line", "`page`", "`hpa`", "`bytes`",
               "`ticks`"], m2["placed"]),
        f"Of the {len(checked)} `PAGE_CHECKED` lines, "
        f"{sum(not item['differ'] for item in checked)} differ from their "
        f"report's page in no field compared.\n",
        "## Management requests\n\nEach of hart 0's `BE_MVP:MGMT` lines "
        "(`result.json`; planning/mvp-m2-plan.md, Q3, Q14): the requester "
        "and its state (`running`, unless one of hart 0's transitions "
        "before the line says otherwise), the function, the target as the "
        "guest named it, the result and its SBI name, the target's state "
        "the line shows after the request (`-` for none), the request's "
        "ticks since the barrier, and `service`, the answer's time minus "
        "the request's, in ticks and milliseconds; beside its guest's "
        "report of the call (`handoff-excerpt.log`; a burst line stands "
        "for its count of calls), paired in order as "
        "tests/check-capture.py pairs them; then each call its hart "
        "answered alone, which hart 0 never logs:\n",
        table(["Run", "Image", "Requester", "Its state", "`seq`", "`fid`",
               "`target`", "`result`", "SBI", "`target_state`", "`ticks`",
               "`service`", "ms", "The guest's report"], m2["requests"]),
        "### The IPI probe in a management wait\n\nEach anchor run's "
        "`BE_MVP:11 IPI_PROBE` lines (`result.json`) beside the capture "
        "checker's costs (`BE_MVP_COSTS` in `check.txt`; "
        "planning/mvp-m2-plan.md, Plan revision M2-A): a domain hart that "
        "waits in HS for hart 0's answer to its management request serves "
        "a PING it finds meanwhile, and its PONG shows `spv=0`; the checker "
        "admits that only where the probe's `received` lies inside "
        "`[ticks, ticks + service]` of a `BE_MVP:MGMT` line of the same "
        "hart, and then records `g<d>_ping_in_mgmt_wait=1` and that "
        "request's `g<d>_ping_mgmt_seq`, whose line gives the wait below. "
        "Ticks since the barrier, and milliseconds at the platform's "
        "timebase:\n",
        table(["Run", "Toolchain", "Domain", "`sent`", "`received`",
               "`answered`", "`spv`", "In a wait", "`seq`", "`fid`",
               "Wait `ticks`", "`service`", "`received` - `ticks`",
               "`received` (ms)", "Wait (ms)"], m2["ipi_probes"]),
        probe_summary(m2),
        "## Paused and terminated\n\nEach `BE_MVP:12 DOMAIN_PAUSED` and "
        "`DOMAIN_TERMINATED` line (`result.json`; planning/mvp-m2-plan.md, "
        "Q4, Q15), with its exit count and, for a terminated domain that "
        "was paused, whether the count is the one it had paused with:\n",
        table(["Run", "Image", "Transition", "`hart`", "`domain`", "`by`",
               "`exits`", "`sha256`", "`ticks`", "ms",
               "Exits as when paused"],
              [row + ["-" if row[2] != "DOMAIN_TERMINATED" or
                      (row[0], row[4]) not in paused else "equal" if
                      paused[row[0], row[4]] == row[6] else "differ"]
               for row in m2["transitions"]]),
        "## Requests and responses\n\nEach request's digest as the "
        "requester (`MVPINIT 09 REQUEST`) and the server (`MVPINIT 09 "
        "RESPONSE`) print it (`handoff-excerpt.log`), beside the offline "
        "HMAC-SHA-256 (the expectation's `requests`; planning/mvp-m2-plan.md, "
        "Q6, Q8); `timeout=1` is the unanswered request's, `-` a line a run "
        "lacks:\n",
        table(["Run", "Image", "`n`", "Requester's", "Server's", "Offline",
               "All three"], m2["digests"]),
        f"Of the {len(answered)} requests both sides printed, "
        f"{sum(row[-1] == 'equal' for row in answered)} show the offline "
        f"digest on both.\n"]


def render(data):
    pre, sc, te = data["preflight"], data["scenario"], data["te_poc"]
    out = [f"# MVP platform record: {data['campaign']}\n",
           f"Written by `mvp/tools/platform-record.py` (`{SCHEMA}`) from "
           "this board record's files, for the MVP claim "
           "(planning/mvp-m0-plan.md, \"Platform record: probes and "
           "negative images\"; planning/mvp-m1-plan.md, \"Platform "
           "record\"). Nothing in it is a claim; every value is "
           "recorded with its source, and Sources lists every file read. "
           "The board's values are diagnostic bring-up facts for one "
           "COM260, its firmware, and its Fedora kernel, not hardware "
           "validation or qualification; QEMU's are emulation facts. Ticks "
           "count each platform's own timebase.\n", "## Runs\n",
           table(["Run", "Image", "Toolchain", "Image SHA-256", "Verdict",
                  "Stop", "Launcher", "`be_image`", "Serial range",
                  "Reset (UTC)", "Terminal marker", "Attribution",
                  "Boot hart (SHIM)"],
                 data["runs"]),
           "## Preflight\n\n`preflight.txt`'s `key=value` lines, in order:\n",
           table(["Key", "Value"], pre["facts"]),
           "### The preflight after the session\n\n`mvp/preflight-after.txt` "
           "beside `preflight.txt` (planning/mvp-m5-plan.md, \"The session "
           "protocol (M5-6)\", step m): every fact but `captured_utc` and "
           "`boot_id`, then the other lines but Fedora's log as one row. "
           f"{sum(row[3] == 'equal' for row in pre['pair'])} of "
           f"{len(pre['pair'])} rows are equal.\n",
           table(["Fact", "Before", "After", "Before and after"],
                 pre["pair"])]
    out += baseline_section(pre["baseline"], len(data["runs"])) + [
        "### Harts and topology\n"]
    links = [pre["links"].get(cpu["node"], {}) for cpu in pre["dt_cpus"]]
    out.append(table(
        ["DT node", "reg", "status", "compatible", "h", "sstc", "phandle",
         "next-level-cache", "`/cpus/cpu-map` path"],
        [[cpu.get(key) for key in ("node", "reg", "status", "compatible",
                                   "h", "sstc")] +
         [link.get("phandle"), link.get("next_level_cache"),
          pre["cpu_map"].get(link.get("phandle"))]
         for cpu, link in zip(pre["dt_cpus"], links)]))
    for title, values in (("Device-tree `riscv,isa-extensions`",
                           pre["extensions"]),
                          ("`/proc/cpuinfo` isa", {
                              key: value.get("isa") for key, value in
                              pre["cpuinfo"].items()})):
        out.append(f"{title}, the same for all {len(values)}: "
                   f"`{next(iter(values.values()))}`\n"
                   if len(set(values.values())) == 1 else
                   table([title, "Value"], sorted(values.items())))
    names = ("hart", "h", "sstc", "mmu", "uarch", "mvendorid", "marchid",
             "mimpid")
    out.append(table(["Linux CPU (`/proc/cpuinfo`)", *names],
                     [[key] + [value.get(name) for name in names]
                      for key, value in sorted(pre["cpuinfo"].items())]))
    names = ("cpu", "physical_package_id", "cluster_id", "core_id",
             "cluster_cpus_list", "core_cpus_list", "package_cpus_list")
    out += [table([f"`{name}`" for name in names],
                  [[entry.get(name) for name in names]
                   for entry in pre["topology"]]),
            "Cache nodes: " + ("; ".join(f"`{line}`" for line in pre["caches"])
                               if pre["caches"] else
                               "none recorded; the preflight found no "
                               "device-tree node whose name holds `cache` "
                               "(to depth 3), so the cpu nodes' "
                               "`next-level-cache` phandles above are the "
                               "record's cache topology.") + "\n",
            "### Fedora's log\n\nThe lines the preflight kept "
            f"(`hsm_detected={dict(pre['facts'])['hsm_detected']}`):\n",
            block(pre["log"]),
            "### Memory\n\n`/proc/iomem`, each System RAM range with its "
            "children:\n", block(pre["iomem"]),
            "FDT reservations (`fdt_reserved`):\n",
            table(["Range [low, high)", "Lies"], pre["reservations"]),
            "The MVP extents against both (`tools/platform-probe.py "
            "region-check` with `src/mvp-layout.h` on `preflight.txt`):\n",
            block(pre["region_check"]),
            "The shared pages among them, M1's channel page their first "
            "(planning/mvp-m2-plan.md, \"Memory and load paths\"): "
            f"`{pre['shared_pages']}`.\n",
            "## Probe images\n\nEach probe run's hart 0 lines before its "
            "probe values (`result.json`):\n"]
    for run, probe, result, lines in data["probe_runs"]:
        out += [f"`{run}` ({probe}), `{result}`:\n", block(lines)]
    for row in data["probes"]:
        (gcc, gcc_result), (clang, clang_result) = row["qemu"]
        values = [dict(entry or []) for entry in row["values"]]
        out += [f"### `{row['label']}` ({row['probe']})\n\n"
                f"- Expected on K3 (plan): {row['expected']}\n"
                f"- On K3 from a cold boot (`{row['run']}`): {row['reading']}\n"
                f"- On K3 after a kexec, M0's record (`{row['m0'][0]}`): "
                f"{row['m0'][1]}\n"
                f"- QEMU, GCC: `{gcc}`, judged again: `{gcc_result}`\n"
                f"- QEMU, Clang: `{clang}`: `{clang_result}`\n",
                table(["Field", "K3, cold boot (GCC)", "K3, M0 after kexec",
                       "QEMU, GCC", "QEMU, Clang"],
                      [[f"`{key}`"] + [entry.get(key) for entry in values]
                       for key in dict.fromkeys(key for entry in values
                                                for key in entry)])]
    out.append(f"## Serial log\n\n{data['serial_log']}\n")
    # M0's two-guests section, as before, but in a record of te-poc or
    # anchor runs that holds no two-guests run.
    if sc["runs"] or not (te["runs"] or data["anchor"]["runs"]):
        out += ["## Scenario runs\n"] + scenario_section(sc, COUNTS)
    if te["runs"]:
        out += ["## te-poc runs\n\nThe te-poc scenario's own image's runs "
                "(planning/mvp-m1-plan.md, \"Scenarios and the harness\"), "
                "tabled as the two-guests scenario's are, with each "
                "domain's DENY lines as the capture checker counts them "
                "(`denials_g0`, `denials_g1`) and each denial's service "
                "ticks among its costs:\n"] + scenario_section(
                    te, COUNTS + DENIAL_COUNTS) + denial_section(
                        data["denials"])
    if data["channel"]["checked"]:
        out += channel_section(data["channel"])
    if data["anchor"]["runs"]:
        out += ["## anchor runs\n\nThe anchor scenario's own image's runs "
                "(planning/mvp-m2-plan.md, \"Scenarios and the harness\"), "
                "tabled as the two-guests scenario's are, with each "
                "domain's DENY lines and its requests on hart 0 as the "
                "capture checker counts them (`mgmt_g0`, `mgmt_g1`), and "
                "each denial's and request's service ticks among its costs "
                "(the protected domain ends by termination, so only the "
                "host has a `DOMAIN_SHUTDOWN` record):\n"] + scenario_section(
                    data["anchor"], COUNTS + DENIAL_COUNTS + MGMT_COUNTS)
    if data["m2"]["pages"]:
        out += anchor_sections(data["m2"])
    out += console_sections(data["console"])
    out += log_sections(data["log"])
    out += ["## Other runs\n",
            table(["Run", "Image", "Toolchain", "Image SHA-256", "Verdict",
                   "Stop", "Result", "Last two hart 0 lines"],
                  data["other_runs"])]
    if data["failures"]:
        out += failure_section(data["failures"])
    out += ["## Resets\n\nThe reset that launched each run "
            "(`mvp/resets/<run>.txt`, the run's `reset.txt`, "
            "tools/k3-console.sh's record; planning/mvp-m5-plan.md, \"Resets "
            "and the dongle\"): `k3ctl` when the tools reset the board "
            "through the pinned client, `human` when a human did; the reason "
            "is the port-open rule's condition that held. The replies are "
            "the dongle firmware's as the client relays them; an `OK` "
            "acknowledges a command, and the SPL and U-Boot banners after "
            "the reply, at the log offsets shown, are the evidence of the "
            "board's new boot. Protocol versions in the `status` replies: "
            + (", ".join(f"`{version}`" for version in
                         data["resets"]["versions"]) or "none") + ".\n",
            table(["Run", "Method", "Reason", "Outcome", "Client SHA-256",
                   "`status` before", "`reset` reply", "`status` after",
                   "Reset (UTC)", "Banner (UTC)", "Log offset",
                   "SPL banner offset", "U-Boot banner offset"],
                  [row[:4] + [(row[4] or "")[:12]] + row[5:]
                   for row in data["resets"]["rows"]]),
            "Each `status` reply's fields:\n",
            table(["Run", "When", *[f"`{key}`" for key in STATUS_FIELDS]],
                  [[run, when] + [record[f"status_{when}_fields"][key]
                                  for key in STATUS_FIELDS]
                   for run, record in sorted(
                       data["resets"]["records"].items())
                   for when in ("before", "after")
                   if record.get(f"status_{when}")]),
            "## Sources\n",
            table(["Section", "File", "SHA-256"],
                  [[section, f"`{name}`", digest] for section, files in
                   sorted(data["sources"].items())
                   for name, digest in sorted(files.items())])]
    return "\n".join(out)


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--record", type=pathlib.Path)
    parser.add_argument("--qemu-suite", type=pathlib.Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv[1:])
    if args.self_test:
        return self_test()
    if args.record is None:
        parser.error("--record is required")
    record = args.record.resolve()
    try:
        if any((record / name).exists() for name in OUTPUTS):
            raise Refused(f"{record} already holds a platform record")
        data = collect(record, args.qemu_suite.resolve()
                       if args.qemu_suite else None)
        texts = (json.dumps(data, indent=1, sort_keys=True) + "\n",
                 render(data))
        for name, text in zip(OUTPUTS, texts):
            (record / name).write_text(text, encoding="utf-8")
    except (Refused, OSError, ValueError, KeyError, IndexError,
            TypeError) as error:
        print(f"BE_MVP_PLATFORM_RECORD: FAIL {type(error).__name__}: {error}")
        return 1
    m2 = data["m2"]
    if m2["pages"]:
        print(f"BE_MVP_PLATFORM_RECORD_M2: anchor_runs="
              f"{len(data['anchor']['runs'])} page_lines="
              f"{sum(item['line'] is not None for item in m2['pages'])} "
              f"measured="
              f"{sum(row[6] is not None for row in m2['measurement'])} "
              f"requests={sum(row[4] != '-' for row in m2['requests'])} "
              f"transitions={len(m2['transitions'])} digests="
              f"{sum(row[-1] == 'equal' for row in m2['digests'])} "
              f"pings_in_wait="
              f"{sum(row[7] == '1' for row in m2['ipi_probes'])}")
    print(f"BE_MVP_PLATFORM_RECORD: PASS {record} runs={len(data['runs'])} "
          f"probe_values={len(data['probes'])} scenario_runs="
          f"{len(data['scenario']['runs'])} te_poc_runs="
          f"{len(data['te_poc']['runs'])} denials=" + str(sum(
              item["deny"] is not None for run in data["denials"]
              for item in run["denials"])) + " channel_checked=" + str(sum(
                  item["line"] is not None
                  for item in data["channel"]["checked"])) +
          " qemu_gcc,clang=" + ",".join(
              str(sum(bool(row["values"][index]) for row in data["probes"]))
              for index in (1, 2)) + " resets=" + ",".join(
              f"{method}:" + str(sum(row[1] == method
                                     for row in data["resets"]["rows"]))
              for method in ("human", "k3ctl")) + " typed=" + ",".join(
              f"{kind}:{len(data['console'][kind])}"
              for kind in ("characterizations", "sessions")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
