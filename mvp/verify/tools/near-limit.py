#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""
near-limit.py --list DIR [--out FILE]
near-limit.py --self-test [--scratch DIR]

Purpose: list the solver, prover, and model-checker runs in one
./mvp/mvp verify record that completed above nine tenths of their own
time limit, and the runs stopped at their limit (planning/mvp-m11-plan.md,
M11-2, "The host for verify"). The limits come from the runner modules
or from logs that the runner checks against its module. The WP reports
hold each prover run's time, so this list names prover runs as well as
Frama-C jobs. Capability probes that record no time and keep their limit
as a literal inside an arm are not suite runs and are not listed.

Inputs: DIR is a verify record directory, normally build/mvp/verify.
The tool reads the qualification, litmus, WP, CN, CBMC Leaf A, and CBMC
ring records. It never writes under DIR except for the output FILE,
whose default is DIR/near-limit.txt.

Output: a deterministic UTF-8 list with one summary per fixed kind,
then each near or crossed run, and a total. Standard output ends with
`BE_MVP_NEAR_LIMIT: LISTED kinds=N runs=N untimed=N near=N crossed=N
record=FILE`. Every printed path is relative to DIR.

Exit status: 0 the list was written and every expected record was read;
1 the list was written as far as the records allow, with each absent or
unreadable record named on standard error; 2 usage.
"""

import argparse
import contextlib
import importlib.util
import io
import json
import math
import os
import pathlib
import re
import shutil
import stat
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
TAG = "BE_MVP_NEAR_LIMIT"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


QUALIFY = load("near_limit_qualify", "qualify.py")
LITMUS = load("near_limit_litmus", "litmus.py")
WP = load("near_limit_wp_arm", "wp-arm.py")
CN = load("near_limit_cn_arm", "cn-arm.py")
CBMC_LEAF_A = load("near_limit_cbmc_leaf_a", "cbmc-leaf-a.py")
CBMC_RING = load("near_limit_cbmc_ring", "cbmc-ring.py")

KIND_ORDER = (
    "qualify-wp-job",
    "qualify-cbmc",
    "qualify-cn",
    "qualify-litmus",
    "litmus",
    "wp-prover",
    "wp-job",
    "wp-qualify-job",
    "cn",
    "cn-qualify",
    "cbmc-leaf-a",
    "cbmc-ring",
)


class Refusal(Exception):
    """A verify record or self-test scratch directory is refused."""


def number_text(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Refusal(f"the time limit {value!r} is not a number")
    text = str(value) if isinstance(value, int) else repr(value)
    number = Decimal(text)
    if not number.is_finite() or number <= 0:
        raise Refusal(f"the time limit {text} is not positive and finite")
    return text, number


def option_limit(options, option, owner):
    positions = [index for index, word in enumerate(options)
                 if word == option]
    if len(positions) != 1 or positions[0] + 1 == len(options):
        raise Refusal(f"{owner} has no single {option} value")
    text = options[positions[0] + 1]
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        raise Refusal(f"{owner} {option}={text!r} is not a decimal "
                      "number") from None
    if not value.is_finite() or value <= 0:
        raise Refusal(f"{owner} {option}={text!r} is not positive and "
                      "finite")
    return text, value


def derive_limits():
    prove = option_limit(WP.PROVE, "-wp-timeout", "WP.PROVE")
    smoke = option_limit(WP.SMOKE, "-wp-smoke-timeout", "WP.SMOKE")
    if prove[1] != smoke[1]:
        raise Refusal(f"WP.PROVE -wp-timeout={prove[0]} and WP.SMOKE "
                      f"-wp-smoke-timeout={smoke[0]} differ")
    return {
        "qualify-wp-job": number_text(QUALIFY.WP_RUN_SECONDS),
        "qualify-cbmc": number_text(QUALIFY.GOAL_SECONDS),
        "qualify-cn": number_text(QUALIFY.GOAL_SECONDS),
        "qualify-litmus": number_text(QUALIFY.GOAL_SECONDS),
        "litmus": number_text(LITMUS.QUALIFY.GOAL_SECONDS),
        "wp-prover": prove,
        "wp-job": number_text(WP.RUN_SECONDS),
        "wp-qualify-job": number_text(WP.QUALIFY.WP_RUN_SECONDS),
        "cn": number_text(CN.LIB.GOAL_SECONDS),
        "cn-qualify": number_text(CN.LIB.GOAL_SECONDS),
        "cbmc-leaf-a": number_text(CBMC_LEAF_A.RUN_SECONDS),
        "cbmc-ring": number_text(CBMC_RING.RUN_SECONDS),
    }


KIND_LIMITS = {}


def configure_limits():
    global KIND_LIMITS
    KIND_LIMITS = derive_limits()


GROUP_KINDS = {
    "qualify": KIND_ORDER[:4],
    "litmus": ("litmus",),
    "wp": ("wp-prover", "wp-job", "wp-qualify-job"),
    "cn": ("cn", "cn-qualify"),
    "cbmc-leaf-a": ("cbmc-leaf-a",),
    "cbmc-ring": ("cbmc-ring",),
}


@dataclass(frozen=True)
class Run:
    kind: str
    name: str
    state: str
    seconds_text: str | None = None
    seconds: Decimal | None = None


class Inventory:
    def __init__(self, root):
        self.root = root
        self.runs = {kind: [] for kind in KIND_ORDER}
        self.absent = set()
        self.errors = []
        self.seen = set()

    def display(self, path):
        path = pathlib.Path(path)
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return pathlib.Path(os.path.relpath(path, self.root)).as_posix()

    def problem(self, path, reason):
        self.errors.append(f"{self.display(path)}: {reason}")

    def mark_absent(self, group, path):
        self.absent.update(GROUP_KINDS[group])
        self.problem(path, "expected directory is absent")

    def add(self, kind, name, state, seconds_text=None, seconds=None,
            source=None):
        if name.startswith("/") or any(
                character.isspace() or not character.isprintable()
                for character in name):
            self.problem(source or self.root,
                         f"run name {name!r} contains whitespace, a control "
                         "character, or is absolute")
            return
        key = kind, name
        if key in self.seen:
            self.problem(source or self.root,
                         f"run {name!r} repeats in kind {kind}")
            return
        self.seen.add(key)
        self.runs[kind].append(
            Run(kind, name, state, seconds_text, seconds))


def read_text(inventory, path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        reason = getattr(error, "strerror", None) or type(error).__name__
        inventory.problem(path, f"cannot read UTF-8 text ({reason})")
        return None


def decimal_field(inventory, path, field, text, positive=False):
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        inventory.problem(path, f"{field}={text!r} is not a decimal number")
        return None
    if not value.is_finite() or value < 0 or (positive and value == 0):
        condition = "positive and finite" if positive else \
            "finite and non-negative"
        inventory.problem(path, f"{field}={text!r} is not {condition}")
        return None
    return value


STATUS_SECONDS = re.compile(r"status=(\S+) seconds=(\S+)")
LIMIT_SECONDS = re.compile(r"limit_seconds=(\S+)")
STATUS = re.compile(r"status=(\S+)")
SECONDS = re.compile(r"seconds=(\S+)")
ARM_HEADER = "command, then status and seconds on line 2"
LIMIT_HEADER = "command, then limit, status, and seconds on lines 2 to 4"


def log_header(inventory, path, text, form):
    lines = text.split("\n")
    if not lines or not lines[0]:
        inventory.problem(path, "line 1 is not a command")
        return None
    if form == ARM_HEADER:
        if len(lines) < 2 or not (match := STATUS_SECONDS.fullmatch(lines[1])):
            inventory.problem(
                path, "line 2 is not exactly status=<S> seconds=<T>")
            return None
        return None, match[1], match[2]
    if len(lines) < 2 or not (limit := LIMIT_SECONDS.fullmatch(lines[1])):
        inventory.problem(path, "line 2 is not exactly limit_seconds=<L>")
        return None
    if len(lines) < 3 or not (status := STATUS.fullmatch(lines[2])):
        inventory.problem(path, "line 3 is not exactly status=<S>")
        return None
    if len(lines) < 4 or not (seconds := SECONDS.fullmatch(lines[3])):
        inventory.problem(path, "line 4 is not exactly seconds=<T>")
        return None
    return limit[1], status[1], seconds[1]


def collect_log(inventory, path, kind, form):
    text = read_text(inventory, path)
    if text is None:
        return None
    fields = log_header(inventory, path, text, form)
    if fields is None:
        return None
    own_text, status, seconds_text = fields
    if status != "timeout" and not re.fullmatch(r"-?[0-9]+", status):
        inventory.problem(path, f"status={status!r} is not an exit status "
                          "or timeout")
        return None
    seconds = decimal_field(inventory, path, "seconds", seconds_text)
    if seconds is None:
        return None
    expected_text, expected = KIND_LIMITS[kind]
    if form == LIMIT_HEADER:
        own = decimal_field(inventory, path, "limit_seconds", own_text,
                            positive=True)
        if own is None:
            return None
        if own != expected:
            inventory.problem(
                path, f"limit_seconds={own_text} does not equal {kind}'s "
                f"module limit {expected_text}")
            return None
    name = inventory.display(path)
    if status == "timeout":
        inventory.add(kind, name, "crossed", source=path)
    else:
        inventory.add(kind, name, "complete", seconds_text, seconds, path)
    return status


def require_file(inventory, path, description):
    if not path.is_file():
        inventory.problem(path, f"{description} is absent")
        return False
    return True


# qualify.py run_case() and litmus.py run() write captured tool output as
# output.log beside the command.txt whose header is the run record.
SUITE_OUTPUT_LOG = re.compile(r"^[^/]+/[^/]+/[^/]+/output\.log$")
# wp-arm.py requalify() writes these raw Frama-C outputs without a command
# record; their job metadata is in wp/vacuity.txt.
WP_QUALIFY_OUTPUT_LOG = re.compile(
    r"^(?:qualify|qualify-lemma)/[^/]+/output\.log$")
# arm-lib.py oracle() writes host equivalence-test output here. These are
# tests of mutants after a proof arm, not solver or prover runs.
WP_ORACLE_LOG = re.compile(
    r"^mutants/oracle/[^/]+/(?:werror|build|run)\.log$")
LEAF_ORACLE_LOG = re.compile(
    r"^oracle/[^/]+/(?:werror|build|run)\.log$")
# cbmc-ring.py writes the mutant generator's output once and its host
# equivalence-test build/run output below each mutant's host directory.
RING_GENERATOR_LOG = "mutants/generate.log"
RING_HOST_LOG = re.compile(
    r"^mutants/[^/]+/host/(?:build|run)(?:-no-werror)?\.log$")
RING_SOLVER_LOG = re.compile(
    r"^(?:logs/[^/]+|mutants/[^/]+/logs/[^/]+)\.log$")


def unclassified(inventory, path):
    inventory.problem(path, "unclassified .log file")


def collect_qualify(inventory):
    directory = inventory.root / "qualify"
    if not directory.is_dir():
        inventory.mark_absent("qualify", directory)
        return
    require_file(inventory, inventory.root / "qualification.txt",
                 "the qualification record")
    require_file(inventory, inventory.root / "qualification.json",
                 "the qualification JSON record")
    mapping = {
        "wp": "qualify-wp-job",
        "cbmc": "qualify-cbmc",
        "cn": "qualify-cn",
        "litmus": "qualify-litmus",
    }
    for path in sorted(directory.rglob("command.txt")):
        parts = path.relative_to(directory).parts
        if len(parts) != 4 or parts[0] not in mapping:
            inventory.problem(path, "is not ARM/SOLVER/CASE/command.txt")
            continue
        collect_log(inventory, path, mapping[parts[0]], LIMIT_HEADER)
    for path in sorted(directory.rglob("*.log")):
        relative = path.relative_to(directory).as_posix()
        if not SUITE_OUTPUT_LOG.fullmatch(relative) or not (
                path.parent / "command.txt").is_file():
            unclassified(inventory, path)


def collect_litmus(inventory):
    directory = inventory.root / "litmus"
    if not directory.is_dir():
        inventory.mark_absent("litmus", directory)
        return
    require_file(inventory, inventory.root / "litmus.txt",
                 "the litmus record")
    for path in sorted(directory.glob("*/command.txt")):
        collect_log(inventory, path, "litmus", LIMIT_HEADER)
    for path in sorted(directory.rglob("*.log")):
        relative = path.relative_to(directory).as_posix()
        if not re.fullmatch(r"[^/]+/output\.log", relative) or not (
                path.parent / "command.txt").is_file():
            unclassified(inventory, path)


def json_number(inventory, path, value):
    if isinstance(value, bool):
        inventory.problem(path, f"WP prover time {value!r} is a boolean, "
                          "not a JSON number")
        return None
    if not isinstance(value, (int, float)):
        inventory.problem(path, f"WP prover time {value!r} is not a JSON "
                          "number")
        return None
    if isinstance(value, float) and not math.isfinite(value):
        inventory.problem(path, f"WP prover time {value!r} is not finite")
        return None
    text = str(value) if isinstance(value, int) else repr(value)
    return text, decimal_field(inventory, path, "WP prover time", text)


def load_json(inventory, path):
    text = read_text(inventory, path)
    if text is None:
        return None

    def constant(value):
        raise ValueError(f"non-finite constant {value}")

    try:
        return json.loads(text, parse_constant=constant)
    except (json.JSONDecodeError, ValueError) as error:
        inventory.problem(path, f"invalid JSON ({error})")
        return None


def collect_wp_report(inventory, path):
    report = load_json(inventory, path)
    if report is None:
        return
    if not isinstance(report, list):
        inventory.problem(path, "WP report is not a JSON list")
        return
    relative = inventory.display(path)
    for number, entry in enumerate(report, 1):
        if not isinstance(entry, dict):
            inventory.problem(path, f"WP entry {number} is not an object")
            continue
        goal = entry.get("goal")
        verdict = entry.get("verdict")
        provers = entry.get("provers", [])
        if not isinstance(goal, str) or not isinstance(verdict, str):
            inventory.problem(path, f"WP entry {number} lacks a string goal, "
                              "or verdict")
            continue
        if not isinstance(provers, list):
            inventory.problem(path, f"WP entry {number}'s provers are not "
                              "a list")
            continue
        external = []
        bad = False
        for prover in provers:
            if not isinstance(prover, dict) or not isinstance(
                    prover.get("prover"), str):
                inventory.problem(path, f"WP entry {number} has an invalid "
                                  "prover record")
                bad = True
                break
            if prover["prover"].lower() != "qed":
                external.append(prover)
        if bad or not external:
            continue
        several = len(external) > 1
        for prover in external:
            name = f"{relative}#{goal}"
            if several:
                name += f"#{prover['prover']}"
            if verdict == "timeout":
                inventory.add("wp-prover", name, "crossed", source=path)
                continue
            if "time" not in prover or prover["time"] is None:
                inventory.add("wp-prover", name, "untimed", source=path)
                continue
            parsed = json_number(inventory, path, prover["time"])
            if parsed is None or parsed[1] is None:
                continue
            inventory.add("wp-prover", name, "complete",
                          parsed[0], parsed[1], path)


def qualification_fields(inventory, path, line, names):
    pairs = re.findall(r"(?:^| )([A-Za-z_]+)=([^ ]+)", line)
    found = {}
    for name in names:
        values = [value for key, value in pairs if key == name]
        if len(values) != 1:
            inventory.problem(
                path, f"qualification line has "
                f"{'no' if not values else len(values)} {name}= field"
                f"{'s' if len(values) != 1 else ''}")
            return None
        found[name] = values[0]
    return found


def collect_wp_qualification(inventory, path):
    text = read_text(inventory, path)
    if text is None:
        return
    lines = [line for line in text.splitlines()
             if line.startswith("qualify ")]
    if not lines:
        inventory.problem(path, "has no WP qualification run lines")
        return
    for line in lines:
        fields = qualification_fields(
            inventory, path, line, ("case", "observed", "seconds"))
        if fields is None:
            continue
        case, seconds_text = fields["case"], fields["seconds"]
        name = f"{inventory.display(path)}#qualify-{case}"
        if fields["observed"] == "error" and " exit timeout " in \
                f" {line} ":
            inventory.add("wp-qualify-job", name, "crossed", source=path)
            continue
        seconds = decimal_field(inventory, path, "seconds", seconds_text)
        if seconds is not None:
            inventory.add("wp-qualify-job", name, "complete",
                          seconds_text, seconds, path)


def collect_wp(inventory):
    directory = inventory.root / "wp"
    if not directory.is_dir():
        inventory.mark_absent("wp", directory)
        return
    require_file(inventory, directory / "rounds.txt",
                 "the WP final record")
    vacuity = directory / "vacuity.txt"
    require_file(inventory, vacuity, "the WP vacuity record")
    runs = directory / "runs"
    if not runs.is_dir():
        inventory.problem(runs, "the WP runs directory is absent")
        return
    commands = set(runs.rglob("*.command"))
    reports = set()
    for path in sorted(commands):
        status = collect_log(inventory, path, "wp-job", ARM_HEADER)
        report = path.with_suffix(".json")
        if status == "0" and not report.is_file():
            inventory.problem(report, "a completed WP job has no JSON report")
        if report.is_file():
            reports.add(report)
            collect_wp_report(inventory, report)
    for path in sorted(runs.rglob("*.json")):
        if path not in reports:
            inventory.problem(path, "WP JSON report has no sibling .command")
    for path in sorted(runs.rglob("*.log")):
        relative = path.relative_to(runs).as_posix()
        if path.with_suffix(".command") in commands:
            continue
        if WP_QUALIFY_OUTPUT_LOG.fullmatch(relative):
            continue
        if WP_ORACLE_LOG.fullmatch(relative):
            continue
        unclassified(inventory, path)
    if vacuity.is_file():
        collect_wp_qualification(inventory, vacuity)


def collect_cn_qualification(inventory, path):
    text = read_text(inventory, path)
    if text is None:
        return
    lines = [line for line in text.splitlines()
             if line.startswith("qualify ")]
    if not lines:
        inventory.problem(path, "has no CN qualification run lines")
        return
    for line in lines:
        fields = qualification_fields(
            inventory, path, line,
            ("solver", "case", "observed", "seconds"))
        if fields is None:
            continue
        solver, case = fields["solver"], fields["case"]
        seconds_text = fields["seconds"]
        name = (f"{inventory.display(path)}#qualify-{solver}-{case}")
        if fields["observed"] == "error" and " exit timeout " in \
                f" {line} ":
            inventory.add("cn-qualify", name, "crossed", source=path)
            continue
        seconds = decimal_field(inventory, path, "seconds", seconds_text)
        if seconds is not None:
            inventory.add("cn-qualify", name, "complete",
                          seconds_text, seconds, path)


def collect_cn(inventory):
    directory = inventory.root / "cn"
    if not directory.is_dir():
        inventory.mark_absent("cn", directory)
        return
    require_file(inventory, directory / "rounds.txt",
                 "the CN final record")
    vacuity = directory / "vacuity.txt"
    require_file(inventory, vacuity, "the CN vacuity record")
    runs = directory / "runs"
    if not runs.is_dir():
        inventory.problem(runs, "the CN runs directory is absent")
        return
    for path in sorted(runs.rglob("*.log")):
        relative = path.relative_to(runs).as_posix()
        if path.name.endswith((".z3.log", ".cvc5.log")):
            collect_log(inventory, path, "cn", ARM_HEADER)
        elif LEAF_ORACLE_LOG.fullmatch(relative):
            continue
        else:
            unclassified(inventory, path)
    if vacuity.is_file():
        collect_cn_qualification(inventory, vacuity)


def collect_cbmc_leaf_a(inventory):
    directory = inventory.root / "cbmc-leaf-a"
    if not directory.is_dir():
        inventory.mark_absent("cbmc-leaf-a", directory)
        return
    require_file(inventory, directory / "rounds.txt",
                 "the CBMC Leaf A final record")
    runs = directory / "runs"
    if not runs.is_dir():
        inventory.problem(runs, "the CBMC Leaf A runs directory is absent")
        return
    for path in sorted(runs.rglob("*.log")):
        relative = path.relative_to(runs).as_posix()
        if path.name.endswith(("-sat.log", "-cvc5.log")):
            collect_log(inventory, path, "cbmc-leaf-a", ARM_HEADER)
        elif LEAF_ORACLE_LOG.fullmatch(relative):
            continue
        else:
            unclassified(inventory, path)


def collect_cbmc_ring(inventory):
    directory = inventory.root / "cbmc-ring"
    if not directory.is_dir():
        inventory.mark_absent("cbmc-ring", directory)
        return
    require_file(inventory, directory / "summary.json",
                 "the CBMC ring final record")
    logs = directory / "logs"
    if not logs.is_dir():
        inventory.problem(logs, "the CBMC ring logs directory is absent")
        return
    show_loops = logs / "show-loops.log"
    if not show_loops.is_file():
        inventory.problem(show_loops, "the untimed show-loops record is "
                          "absent")
    for path in sorted(directory.rglob("*.log")):
        relative = path.relative_to(directory).as_posix()
        if path == show_loops:
            inventory.add("cbmc-ring", inventory.display(path), "untimed",
                          source=path)
        elif RING_SOLVER_LOG.fullmatch(relative):
            collect_log(inventory, path, "cbmc-ring", LIMIT_HEADER)
        elif relative == RING_GENERATOR_LOG or RING_HOST_LOG.fullmatch(
                relative):
            continue
        else:
            unclassified(inventory, path)


def inventory(root):
    found = Inventory(root)
    collect_qualify(found)
    collect_litmus(found)
    collect_wp(found)
    collect_cn(found)
    collect_cbmc_leaf_a(found)
    collect_cbmc_ring(found)
    return found


HEADER = (
    "# Solver, prover, and model-checker runs near their time limits "
    "(planning/mvp-m11-plan.md, M11-2).",
    "# This list serves the plan's requirement to record each run above "
    "nine tenths of its limit.",
    "# A kind is one suite or arm run unit with one limit; kind order: " +
    ",".join(KIND_ORDER) + ".",
    "# The WP reports hold each prover run's time, so the list names "
    "prover runs as well as Frama-C jobs.",
    "# Untimed means a recorded run with no elapsed time: the CBMC ring "
    "show-loops probe, or a WP prover record without a usable time; no "
    "time is invented.",
    "# Capability probes with no recorded time and a literal limit inside "
    "an arm are not suite runs and are not listed.",
    "# Counts are run metadata that depend on the host and its load, "
    "never a verdict on the code.",
)


def render(found):
    lines = list(HEADER)
    events = []
    totals = {"runs": 0, "untimed": 0, "near": 0, "crossed": 0}
    for kind in KIND_ORDER:
        limit_text, limit = KIND_LIMITS[kind]
        runs = sorted(found.runs[kind], key=lambda run: run.name)
        completed = [run for run in runs if run.state == "complete"]
        near = [run for run in completed
                if Decimal(10) * run.seconds > Decimal(9) * limit]
        crossed = [run for run in runs if run.state == "crossed"]
        untimed = [run for run in runs if run.state == "untimed"]
        slowest = max(completed, key=lambda run: (run.seconds, run.name),
                      default=None)
        line = (f"kind={kind} limit={limit_text} runs={len(runs)} "
                f"untimed={len(untimed)} slowest="
                f"{slowest.seconds_text if slowest else 'none'} "
                f"near={len(near)} crossed={len(crossed)}")
        if kind in found.absent:
            line += " absent=yes"
        lines.append(line)
        totals["runs"] += len(runs)
        totals["untimed"] += len(untimed)
        totals["near"] += len(near)
        totals["crossed"] += len(crossed)
        for run in near:
            events.append((
                KIND_ORDER.index(kind), run.name,
                f"near kind={kind} run={run.name} seconds="
                f"{run.seconds_text} limit={limit_text}"))
        for run in crossed:
            events.append((
                KIND_ORDER.index(kind), run.name,
                f"crossed kind={kind} run={run.name} limit={limit_text}"))
    lines += [line for _, _, line in sorted(events)]
    lines.append("total " + " ".join(
        f"{key}={totals[key]}"
        for key in ("runs", "untimed", "near", "crossed")))
    return "\n".join(lines) + "\n", totals


def record_name(root, output):
    return pathlib.Path(os.path.relpath(output, root)).as_posix()


def output_problem(root, output):
    name = record_name(root, output)
    if output.is_symlink():
        return f"{name}: output is a symbolic link"
    if output.is_dir():
        return f"{name}: output is a directory"
    if not output.parent.is_dir():
        return f"{name}: output parent directory is absent"
    return None


def list_records(root, output):
    if problem := output_problem(root, output):
        print(f"{TAG}: REFUSED {problem}", file=sys.stderr)
        return 1
    found = inventory(root)
    text, totals = render(found)
    try:
        output.write_text(text, encoding="utf-8")
    except OSError as error:
        reason = error.strerror or type(error).__name__
        found.errors.append(f"{record_name(root, output)}: cannot write "
                            f"the list ({reason})")
    for error in found.errors:
        print(f"{TAG}: REFUSED {error}", file=sys.stderr)
    print(f"{TAG}: LISTED kinds={len(KIND_ORDER)} runs={totals['runs']} "
          f"untimed={totals['untimed']} near={totals['near']} "
          f"crossed={totals['crossed']} "
          f"record={record_name(root, output)}")
    return 1 if found.errors else 0


# --------------------------------------------------------------- self-test
SELF_MARKER = ".near-limit-self-test"


def fixed(number):
    text = format(number, "f")
    return text if "." in text else text + ".0"


def samples(kind, delta=Decimal(0)):
    limit = KIND_LIMITS[kind][1]
    exact = limit * Decimal(9) / Decimal(10)
    values = (
        ("below", max(Decimal("0.1"), exact - Decimal("0.1")) + delta, "0"),
        ("exact", exact + delta, "0"),
        ("above", exact + Decimal("0.1") + delta, "0"),
        ("limit", limit + delta, "0"),
        ("crossed", limit + delta, "timeout"),
    )
    return [(name, fixed(value), status) for name, value, status in values]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def command_record(limit, status, seconds, command="checker"):
    return (f"{command}\nlimit_seconds={limit}\nstatus={status}\n"
            f"seconds={seconds}\n")


def arm_record(status, seconds, command="checker"):
    return f"{command}\nstatus={status} seconds={seconds}\n"


def build_tree(root, delta=Decimal(0)):
    root.mkdir(parents=True)
    write(root / "qualification.txt", "BE_MVP_QUALIFY: PASS\n")
    write(root / "qualification.json", "{}\n")
    for arm, kind in (
            ("wp", "qualify-wp-job"),
            ("cbmc", "qualify-cbmc"),
            ("cn", "qualify-cn"),
            ("litmus", "qualify-litmus")):
        limit = KIND_LIMITS[kind][0]
        for name, seconds, status in samples(kind, delta):
            directory = root / "qualify" / arm / "solver" / name
            write(directory / "command.txt",
                  command_record(limit, status, seconds))
            write(directory / "output.log", "captured tool output\n")

    write(root / "litmus.txt", "BE_MVP_LITMUS: PASS\n")
    for name, seconds, status in samples("litmus", delta):
        directory = root / "litmus" / name
        write(directory / "command.txt", command_record(
            KIND_LIMITS["litmus"][0], status, seconds, "herd7"))
        write(directory / "output.log", "captured herd7 output\n")

    write(root / "wp" / "rounds.txt", "rounds=1\n")
    wp_vacuity = []
    for name, seconds, status in samples("wp-qualify-job", delta):
        suffix = ("observed=error ok=no exit timeout" if status == "timeout"
                  else "observed=proved ok=yes")
        wp_vacuity.append(
            f"qualify case={name} expected=proved {suffix} "
            f"seconds={seconds}")
    write(root / "wp" / "vacuity.txt", "\n".join(wp_vacuity) + "\n")
    for family in ("qualify", "qualify-lemma"):
        write(root / "wp" / "runs" / family / "known-pass" / "output.log",
              "captured qualification output\n")
    for name, seconds, status in samples("wp-job", delta):
        path = root / "wp" / "runs" / "jobs" / f"job-{name}.command"
        write(path, arm_record(status, seconds, "frama-c"))
        write(path.with_suffix(".log"), "captured Frama-C output\n")
        if status == "0":
            write(path.with_suffix(".json"), "[]\n")
    for name, seconds, status in samples("wp-prover", delta):
        base = root / "wp" / "runs" / "provers" / f"prover-{name}"
        write(base.with_suffix(".command"),
              arm_record("0", "1.0", "frama-c"))
        write(base.with_suffix(".log"), "captured Frama-C output\n")
        entry = {
            "goal": f"goal_{name}",
            "verdict": "timeout" if status == "timeout" else "valid",
            "provers": [
                {"prover": "qed", "time": 0, "success": 0},
                {"prover": "Alt-Ergo:2.4.3",
                 "time": float(seconds), "success": status == "0"},
            ],
        }
        if name == "below":
            entry["provers"].append(
                {"prover": "qed", "time": 0, "success": 1})
        write(base.with_suffix(".json"), json.dumps([entry]) + "\n")
    write(root / "wp" / "runs" / "mutants" / "oracle" / "m01" /
          "run.log", "host equivalence-test output\n")

    write(root / "cn" / "rounds.txt", "rounds=1\n")
    cn_vacuity = []
    for name, seconds, status in samples("cn-qualify", delta):
        suffix = ("observed=error ok=no exit timeout" if status == "timeout"
                  else "observed=proved ok=yes")
        cn_vacuity.append(
            f"qualify solver=z3 case={name} expected=proved {suffix} "
            f"seconds={seconds}")
    write(root / "cn" / "vacuity.txt", "\n".join(cn_vacuity) + "\n")
    for name, seconds, status in samples("cn", delta):
        write(root / "cn" / "runs" / "round-0" / f"{name}.z3.log",
              arm_record(status, seconds, "cn verify"))
    write(root / "cn" / "runs" / "oracle" / "m01" / "run.log",
          "host equivalence-test output\n")

    write(root / "cbmc-leaf-a" / "rounds.txt", "rounds=1\n")
    for name, seconds, status in samples("cbmc-leaf-a", delta):
        extra = ("status=0 seconds=1.0\nlimit_seconds=1\n"
                 if name == "above" else "")
        write(root / "cbmc-leaf-a" / "runs" / "baseline" /
              f"{name}-sat.log",
              arm_record(status, seconds, "cbmc") + extra)
    write(root / "cbmc-leaf-a" / "runs" / "oracle" / "m01" / "run.log",
          "host equivalence-test output\n")

    write(root / "cbmc-ring" / "summary.json", "{}\n")
    write(root / "cbmc-ring" / "logs" / "show-loops.log",
          "Loop leaf.0:\n")
    for name, seconds, status in samples("cbmc-ring", delta):
        write(root / "cbmc-ring" / "logs" / f"ring-{name}.log",
              command_record(KIND_LIMITS["cbmc-ring"][0], status, seconds,
                             "cbmc"))
    write(root / "cbmc-ring" / "mutants" / "generate.log",
          "mutant generator output\n")
    write(root / "cbmc-ring" / "mutants" / "m01" / "host" / "build.log",
          "host equivalence-test build output\n")
    write(root / "cbmc-ring" / "mutants" / "m01" / "host" / "run.log",
          "host equivalence-test run output\n")


def listed(root, output):
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        status = list_records(root, output)
    return status, stdout.getvalue(), stderr.getvalue(), \
        output.read_text(encoding="utf-8") if output.is_file() else ""


def field_map(line):
    return dict(field.split("=", 1) for field in line.split()
                if "=" in field)


def prepare_scratch(path):
    scratch = path.resolve()
    if REPO.is_relative_to(scratch) or (scratch.is_relative_to(REPO) and
                                        not scratch.is_relative_to(
                                            REPO / "build")):
        raise Refusal("--scratch would hold the source")
    if scratch.exists() and not scratch.is_dir():
        raise Refusal("--scratch is not a directory")
    if scratch.is_dir() and any(scratch.iterdir()) and not (
            scratch / SELF_MARKER).is_file():
        raise Refusal("--scratch is not empty and not this tool's")
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True, mode=0o700)
    with open(scratch / SELF_MARKER, "x", encoding="utf-8") as stream:
        stream.write("near-limit self-test\n")
    return scratch


def invoked(arguments):
    stdout, stderr = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), \
                contextlib.redirect_stderr(stderr):
            status = main(["near-limit.py", *arguments])
    except SystemExit as error:
        status = error.code
    return status, stdout.getvalue(), stderr.getvalue()


def self_test(requested):
    scratch = prepare_scratch(requested)
    results = []
    failures = []

    def case(name, condition, detail=""):
        results.append(bool(condition))
        if not condition:
            failures.append(f"{name}: {detail}")

    def copied(name):
        target = scratch / name
        shutil.copytree(base, target)
        return target

    def refused(name, change, wanted, status_wanted=1):
        tree = copied(name)
        change(tree)
        status, stdout, stderr, _ = listed(
            tree, scratch / f"listed-{name}.txt")
        case(name, status == status_wanted and wanted in stderr,
             f"status={status}\nstdout={stdout}\nstderr={stderr}")
        return tree, status, stdout, stderr

    def add_wp_job(tree, name, report, status="0"):
        base_path = tree / "wp" / "runs" / "extra" / name
        write(base_path.with_suffix(".command"),
              arm_record(status, "1.0", "frama-c"))
        write(base_path.with_suffix(".log"), "captured Frama-C output\n")
        if report is not None:
            write(base_path.with_suffix(".json"), report)
        return base_path

    try:
        base = scratch / "base"
        build_tree(base)
        status, stdout, stderr, text = listed(
            base, scratch / "listed-first.txt")
        case("a complete tree lists", status == 0 and not stderr,
             stderr or stdout)
        kind_lines = {field_map(line)["kind"]: field_map(line)
                      for line in text.splitlines()
                      if line.startswith("kind=")}
        case("every kind is present",
             tuple(kind_lines) == KIND_ORDER, repr(tuple(kind_lines)))
        event_lines = [line for line in text.splitlines()
                       if line.startswith(("near ", "crossed "))]
        for kind in KIND_ORDER:
            own = [line for line in event_lines
                   if f"kind={kind} " in line]
            labelled = [(line, field_map(line)["run"]) for line in own]
            case(f"{kind}: below nine tenths is not near",
                 not any("below" in run for _, run in labelled),
                 "\n".join(own))
            case(f"{kind}: exactly nine tenths is not near",
                 not any("exact" in run for _, run in labelled),
                 "\n".join(own))
            case(f"{kind}: above nine tenths is near",
                 any(line.startswith("near ") and "above" in run
                     for line, run in labelled), "\n".join(own))
            case(f"{kind}: a completed run at the limit is near",
                 any(line.startswith("near ") and "limit" in run
                     for line, run in labelled), "\n".join(own))
            case(f"{kind}: a stopped run is crossed",
                 any(line.startswith("crossed ") and "crossed" in run
                     for line, run in labelled), "\n".join(own))
        crossed = [line for line in event_lines
                   if line.startswith("crossed ")]
        case("crossed lines carry no time",
             all("seconds=" not in line for line in crossed),
             "\n".join(crossed))
        case("a WP timeout ignores its unusable time",
             any("kind=wp-prover" in line and "goal_crossed" in line and
                 "seconds=" not in line for line in crossed),
             "\n".join(crossed))
        case("the untimed ring probe is counted",
             kind_lines["cbmc-ring"]["untimed"] == "1",
             repr(kind_lines["cbmc-ring"]))
        keys = []
        for line in event_lines:
            fields = field_map(line)
            keys.append((KIND_ORDER.index(fields["kind"]), fields["run"]))
        case("events have the fixed order", keys == sorted(keys), repr(keys))
        status2, stdout2, stderr2, text2 = listed(
            base, scratch / "listed-second.txt")
        case("repetition is byte-identical",
             status2 == 0 and not stderr2 and text2 == text,
             stderr2 or stdout2)
        combined = text + stdout + stderr
        case("no absolute path is printed",
             str(scratch) not in combined and " run=/" not in combined and
             " record=/" not in combined, combined)
        total_line = next(line for line in text.splitlines()
                          if line.startswith("total "))
        total = field_map(total_line)
        result = field_map(stdout.strip())
        case("the result line matches the file's totals",
             all(result[key] == total[key]
                 for key in ("runs", "untimed", "near", "crossed")),
             f"{total_line}\n{stdout}")
        case("output-looking lines after a good header are ignored",
             any(line.startswith("near kind=cbmc-leaf-a ") and
                 "run=cbmc-leaf-a/runs/baseline/above-sat.log " in line
                 for line in event_lines), "\n".join(event_lines))

        other = scratch / "other"
        build_tree(other, Decimal("0.01"))
        _, _, _, other_text = listed(other, scratch / "listed-other.txt")
        other_crossed = [line for line in other_text.splitlines()
                         if line.startswith("crossed ")]
        case("crossed lines do not carry host times",
             crossed == other_crossed,
             "\n".join(crossed + ["--"] + other_crossed))

        # The two exact log-header forms, and nothing in tool output after
        # those lines, supply run metadata.
        leaf_log = lambda tree: tree / "cbmc-leaf-a" / "runs" / \
            "baseline" / "below-sat.log"
        ring_log = lambda tree: tree / "cbmc-ring" / "logs" / \
            "ring-below.log"
        refused("outcome-only-in-output",
                lambda tree: write(
                    leaf_log(tree),
                    "cbmc\nsolver output\nstatus=0 seconds=1.0\n"),
                "line 2 is not exactly status=<S> seconds=<T>")
        refused("arm-log-with-limit-form",
                lambda tree: write(
                    leaf_log(tree), command_record("300", "0", "1.0",
                                                   "cbmc")),
                "line 2 is not exactly status=<S> seconds=<T>")
        refused("limit-log-with-arm-form",
                lambda tree: write(
                    ring_log(tree), arm_record("0", "1.0", "cbmc")),
                "line 2 is not exactly limit_seconds=<L>")
        refused("empty-command-line",
                lambda tree: write(leaf_log(tree),
                                   "\nstatus=0 seconds=1.0\n"),
                "line 1 is not a command")
        refused("invalid-status",
                lambda tree: write(leaf_log(tree),
                                   arm_record("passed", "1.0", "cbmc")),
                "status='passed' is not an exit status or timeout")
        refused("non-decimal-seconds",
                lambda tree: write(leaf_log(tree),
                                   arm_record("0", "soon", "cbmc")),
                "seconds='soon' is not a decimal number")
        refused("negative-seconds",
                lambda tree: write(leaf_log(tree),
                                   arm_record("0", "-1.0", "cbmc")),
                "seconds='-1.0' is not finite and non-negative")
        refused("non-finite-seconds",
                lambda tree: write(leaf_log(tree),
                                   arm_record("0", "NaN", "cbmc")),
                "seconds='NaN' is not finite and non-negative")
        refused("missing-limit-line",
                lambda tree: write(ring_log(tree),
                                   "cbmc\nstatus=0\nseconds=1.0\n"),
                "line 2 is not exactly limit_seconds=<L>")
        refused("missing-status-line",
                lambda tree: write(ring_log(tree),
                                   "cbmc\nlimit_seconds=600\n"
                                   "seconds=1.0\n"),
                "line 3 is not exactly status=<S>")
        refused("missing-seconds-line",
                lambda tree: write(ring_log(tree),
                                   "cbmc\nlimit_seconds=600\nstatus=0\n"),
                "line 4 is not exactly seconds=<T>")
        refused("non-decimal-limit",
                lambda tree: write(
                    ring_log(tree), command_record("many", "0", "1.0",
                                                   "cbmc")),
                "limit_seconds='many' is not a decimal number")
        refused("zero-limit",
                lambda tree: write(
                    ring_log(tree), command_record("0", "0", "1.0",
                                                   "cbmc")),
                "limit_seconds='0' is not positive and finite")
        refused("ring-limit-mismatch",
                lambda tree: write(
                    ring_log(tree), command_record("601", "0", "1.0",
                                                   "cbmc")),
                "does not equal cbmc-ring's module limit 600")

        # Every .log below a suite or arm record directory is either a
        # solver record or one of the named auxiliary classes.
        for name, relative in (
                ("unclassified-qualify-log",
                 "qualify/wp/solver/below/other.log"),
                ("unclassified-litmus-log", "litmus/below/other.log"),
                ("unclassified-wp-log", "wp/runs/other.log"),
                ("unclassified-cn-log", "cn/runs/other.log"),
                ("unclassified-leaf-log",
                 "cbmc-leaf-a/runs/other.log"),
                ("unclassified-ring-log", "cbmc-ring/other.log")):
            refused(name, lambda tree, relative=relative: write(
                tree / relative, "not a classified log\n"),
                "unclassified .log file")

        # WP reports are siblings of job records, and their JSON schema and
        # prover records are refused one defect at a time.
        refused("wp-report-without-command",
                lambda tree: write(
                    tree / "wp" / "runs" / "jobs" / "orphan.json", "[]\n"),
                "WP JSON report has no sibling .command")
        refused("wp-completed-job-without-report",
                lambda tree: (tree / "wp" / "runs" / "jobs" /
                              "job-below.json").unlink(),
                "a completed WP job has no JSON report")
        for name, report, wanted in (
                ("wp-invalid-json", "{\n", "invalid JSON"),
                ("wp-report-not-list", "{}\n",
                 "WP report is not a JSON list"),
                ("wp-entry-not-object", "[1]\n",
                 "WP entry 1 is not an object"),
                ("wp-entry-no-goal", json.dumps([{
                    "verdict": "valid", "provers": []}]) + "\n",
                 "lacks a string goal, or verdict"),
                ("wp-entry-no-verdict", json.dumps([{
                    "goal": "g", "provers": []}]) + "\n",
                 "lacks a string goal, or verdict"),
                ("wp-provers-not-list", json.dumps([{
                    "goal": "g", "verdict": "valid",
                    "provers": {}}]) + "\n",
                 "provers are not a list"),
                ("wp-invalid-prover", json.dumps([{
                    "goal": "g", "verdict": "valid",
                    "provers": [{}]}]) + "\n",
                 "has an invalid prover record")):
            refused(name, lambda tree, name=name, report=report: add_wp_job(
                tree, name, report), wanted)

        for name, value, wanted in (
                ("wp-time-string", "1.0", "is not a JSON number"),
                ("wp-time-boolean", True, "is a boolean, not a JSON number"),
                ("wp-time-negative", -1, "is not finite and non-negative")):
            report = json.dumps([{
                "goal": "g", "verdict": "valid",
                "provers": [{"prover": "P", "time": value,
                             "success": 1}]}]) + "\n"
            refused(name, lambda tree, name=name, report=report: add_wp_job(
                tree, name, report), wanted)
        refused("wp-time-non-finite",
                lambda tree: add_wp_job(
                    tree, "wp-time-non-finite",
                    '[{"goal":"g","verdict":"valid","provers":'
                    '[{"prover":"P","time":1e999,"success":1}]}]\n'),
                "WP prover time inf is not finite")
        duplicate = json.dumps([{
            "goal": "g", "verdict": "valid", "provers": [
                {"prover": "P", "time": 1, "success": 1},
                {"prover": "P", "time": 2, "success": 1}]}]) + "\n"
        refused("wp-repeated-run-name",
                lambda tree: add_wp_job(tree, "duplicate", duplicate),
                "repeats in kind wp-prover")

        multiple = copied("wp-multiple-provers")
        report = json.dumps([
            {"goal": "two", "verdict": "valid", "provers": [
                {"prover": "P1", "time": 55, "success": 1},
                {"prover": "P2", "time": 56, "success": 1}]},
            {"goal": "timed-out", "verdict": "timeout", "provers": [
                {"prover": "P1", "time": 0, "success": 0},
                {"prover": "P2", "time": 0, "success": 0}]},
            {"goal": "untimed", "verdict": "unknown", "provers": [
                {"prover": "P1", "success": 0}]}]) + "\n"
        add_wp_job(multiple, "multiple", report)
        multi_status, _, multi_error, multi_text = listed(
            multiple, scratch / "listed-multiple.txt")
        case("two external provers and an untimed prover are named",
             multi_status == 0 and not multi_error and
             all(f"#two#{name}" in multi_text for name in ("P1", "P2")) and
             all(f"#timed-out#{name}" in multi_text
                 for name in ("P1", "P2")) and
             "#untimed" not in "\n".join(
                 line for line in multi_text.splitlines()
                 if line.startswith(("near ", "crossed "))) and
             "kind=wp-prover limit=60 runs=10 untimed=1" in multi_text,
             multi_error or multi_text)

        # Qualification record fields are singular and mandatory.
        def qualification_change(tree, arm, field, duplicate):
            path = tree / arm / "vacuity.txt"
            lines = path.read_text(encoding="utf-8").splitlines()
            prefix = f"{field}="
            if duplicate:
                lines[0] += f" {field}=again"
            else:
                lines[0] = " ".join(
                    word for word in lines[0].split()
                    if not word.startswith(prefix))
            write(path, "\n".join(lines) + "\n")

        for arm, fields in (("wp", ("case", "observed", "seconds")),
                            ("cn", ("solver", "case", "observed",
                                    "seconds"))):
            for field in fields:
                refused(f"{arm}-qualify-missing-{field}",
                        lambda tree, arm=arm, field=field:
                        qualification_change(tree, arm, field, False),
                        f"no {field}= field")
                refused(f"{arm}-qualify-duplicate-{field}",
                        lambda tree, arm=arm, field=field:
                        qualification_change(tree, arm, field, True),
                        f"2 {field}= fields")
        for arm in ("wp", "cn"):
            refused(f"{arm}-vacuity-without-qualification",
                    lambda tree, arm=arm: write(
                        tree / arm / "vacuity.txt", "vacuity=ok\n"),
                    f"{arm.upper()} qualification run lines")

        # Each final record and runs/logs directory is required.
        for name, relative in (
                ("missing-qualification-text", "qualification.txt"),
                ("missing-qualification-json", "qualification.json"),
                ("missing-litmus-record", "litmus.txt"),
                ("missing-wp-rounds", "wp/rounds.txt"),
                ("missing-wp-vacuity", "wp/vacuity.txt"),
                ("missing-cn-rounds", "cn/rounds.txt"),
                ("missing-cn-vacuity", "cn/vacuity.txt"),
                ("missing-leaf-rounds", "cbmc-leaf-a/rounds.txt"),
                ("missing-ring-summary", "cbmc-ring/summary.json")):
            refused(name, lambda tree, relative=relative:
                    (tree / relative).unlink(), "is absent")
        for name, relative, wanted in (
                ("missing-wp-runs", "wp/runs",
                 "the WP runs directory is absent"),
                ("missing-cn-runs", "cn/runs",
                 "the CN runs directory is absent"),
                ("missing-leaf-runs", "cbmc-leaf-a/runs",
                 "the CBMC Leaf A runs directory is absent"),
                ("missing-ring-logs", "cbmc-ring/logs",
                 "the CBMC ring logs directory is absent")):
            refused(name, lambda tree, relative=relative:
                    shutil.rmtree(tree / relative), wanted)
        refused("missing-show-loops",
                lambda tree: (tree / "cbmc-ring" / "logs" /
                              "show-loops.log").unlink(),
                "the untimed show-loops record is absent")
        for group in ("qualify", "litmus", "wp", "cn", "cbmc-leaf-a",
                      "cbmc-ring"):
            refused(f"missing-{group}-directory",
                    lambda tree, group=group: shutil.rmtree(tree / group),
                    "expected directory is absent")

        refused("qualify-command-at-wrong-depth",
                lambda tree: write(
                    tree / "qualify" / "wrong" / "command.txt",
                    command_record("60", "0", "1.0")),
                "is not ARM/SOLVER/CASE/command.txt")
        refused("non-utf8-log",
                lambda tree: (tree / "cn" / "runs" / "round-0" /
                              "below.z3.log").write_bytes(b"\xff"),
                "cannot read UTF-8 text")

        def broken_log(tree):
            path = tree / "cn" / "runs" / "round-0" / "broken.z3.log"
            path.symlink_to(path.parent / "absent")

        refused("unreadable-log", broken_log, "cannot read UTF-8 text")
        refused("run-name-with-space",
                lambda tree: write(
                    tree / "cbmc-ring" / "logs" / "bad name.log",
                    command_record("600", "0", "1.0", "cbmc")),
                "contains whitespace")

        # Output path checks happen before inventory; an actual write error
        # is still returned after the readable list has been formed.
        output_tree = copied("output-refusals")
        target = scratch / "output-target.txt"
        write(target, "keep\n")
        link = scratch / "output-link.txt"
        link.symlink_to(target)
        for name, output, wanted in (
                ("output-symbolic-link", link, "output is a symbolic link"),
                ("output-directory", scratch, "output is a directory"),
                ("output-parent-absent", scratch / "absent-parent" / "x",
                 "output parent directory is absent")):
            status_o, stdout_o, stderr_o, _ = listed(output_tree, output)
            case(name, status_o == 1 and not stdout_o and wanted in stderr_o,
                 f"{stdout_o}\n{stderr_o}")
        too_long = scratch / ("x" * 300)
        status_o, stdout_o, stderr_o, _ = listed(output_tree, too_long)
        case("output-cannot-be-written",
             status_o == 1 and "cannot write the list" in stderr_o,
             f"{stdout_o}\n{stderr_o}")

        # Scratch ownership, mode, marker reuse, source containment, and
        # command-line refusals.
        for name, path, wanted in (
                ("scratch-would-hold-source", REPO.parent,
                 "would hold the source"),
                ("scratch-inside-source", REPO / "mvp",
                 "would hold the source")):
            try:
                prepare_scratch(path)
                case(name, False, "accepted")
            except Refusal as error:
                case(name, wanted in str(error), str(error))
        foreign = scratch / "foreign"
        write(foreign / "keep", "not ours\n")
        try:
            prepare_scratch(foreign)
            case("scratch-foreign-nonempty", False, "accepted")
        except Refusal as error:
            case("scratch-foreign-nonempty", "not empty and not this tool's"
                 in str(error), str(error))
        scratch_file = scratch / "scratch-file"
        write(scratch_file, "file\n")
        try:
            prepare_scratch(scratch_file)
            case("scratch-is-file", False, "accepted")
        except Refusal as error:
            case("scratch-is-file", "not a directory" in str(error),
                 str(error))
        owned = scratch / "owned"
        owned.mkdir()
        write(owned / SELF_MARKER, "marker\n")
        write(owned / "old", "old\n")
        prepared = prepare_scratch(owned)
        case("scratch-owned-recreated",
             not (prepared / "old").exists() and
             (prepared / SELF_MARKER).is_file() and
             stat.S_IMODE(prepared.stat().st_mode) == 0o700)
        shutil.rmtree(prepared)

        status_m, out_m, err_m = invoked(
            ["--list", str(scratch / "absent-tree"),
             "--out", str(scratch / "unused.txt")])
        case("list-absent-directory",
             status_m == 1 and "list directory is absent" in err_m,
             out_m + err_m)
        for name, arguments, wanted in (
                ("usage-list-with-scratch",
                 ["--list", str(base), "--scratch", str(scratch / "x")],
                 "--scratch is the self-test's"),
                ("usage-self-test-with-out",
                 ["--self-test", "--out", str(scratch / "x")],
                 "--out is --list's")):
            status_m, out_m, err_m = invoked(arguments)
            case(name, status_m == 2 and wanted in err_m, out_m + err_m)

        # A stale or missing WP timeout option fails both modes before the
        # corpus or self-test scratch is read.
        saved_prove, saved_smoke = WP.PROVE, WP.SMOKE
        try:
            for label, prove, smoke, wanted in (
                    ("missing", tuple(word for word in WP.PROVE
                                      if word not in ("-wp-timeout",
                                                      str(WP.LIB.GOAL_SECONDS))),
                     WP.SMOKE, "has no single -wp-timeout value"),
                    ("different", WP.PROVE,
                     tuple("61" if word == str(WP.LIB.GOAL_SECONDS) and
                           index == WP.SMOKE.index("-wp-smoke-timeout") + 1
                           else word for index, word in enumerate(WP.SMOKE)),
                     "differ")):
                WP.PROVE, WP.SMOKE = prove, smoke
                for mode, arguments in (
                        ("list", ["--list", str(base), "--out",
                                  str(scratch / f"limit-{label}.txt")]),
                        ("self-test", ["--self-test", "--scratch",
                                      str(scratch /
                                          f"limit-{label}-scratch")])):
                    status_m, out_m, err_m = invoked(arguments)
                    combined_m = out_m + err_m
                    case(f"wp-limit-{label}-{mode}",
                         status_m == 1 and wanted in combined_m and
                         "Traceback" not in combined_m, combined_m)
        finally:
            WP.PROVE, WP.SMOKE = saved_prove, saved_smoke
            configure_limits()
        for name, function, wanted in (
                ("invalid-option-limit",
                 lambda: option_limit(("-wp-timeout", "bad"),
                                      "-wp-timeout", "test"),
                 "is not a decimal number"),
                ("zero-option-limit",
                 lambda: option_limit(("-wp-timeout", "0"),
                                      "-wp-timeout", "test"),
                 "is not positive and finite"),
                ("invalid-module-limit",
                 lambda: number_text(False), "is not a number"),
                ("zero-module-limit",
                 lambda: number_text(0), "not positive and finite")):
            try:
                function()
                case(name, False, "accepted")
            except Refusal as error:
                case(name, wanted in str(error), str(error))
    except Exception as error:
        case("self-test completed without an internal exception", False,
             f"{type(error).__name__}: {error}")

    if all(results):
        shutil.rmtree(scratch)
    for failure in failures:
        print(f"{TAG}_SELF_TEST: FAIL {failure}")
    print(f"{TAG}_SELF_TEST: {'PASS' if all(results) else 'FAIL'} "
          f"cases={len(results)}"
          f"{'' if all(results) else f' failed={results.count(False)}'}")
    return 0 if all(results) else 1


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--list", dest="list_dir", type=pathlib.Path,
                       metavar="DIR")
    modes.add_argument("--self-test", action="store_true")
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--scratch", type=pathlib.Path)
    args = parser.parse_args(argv[1:])
    if args.list_dir is not None:
        if args.scratch:
            parser.error("--scratch is the self-test's")
    elif args.out:
        parser.error("--out is --list's")
    try:
        configure_limits()
    except Refusal as error:
        label = f"{TAG}_SELF_TEST: FAIL" if args.self_test else \
            f"{TAG}: REFUSED"
        stream = sys.stdout if args.self_test else sys.stderr
        print(f"{label} {error}", file=stream)
        return 1
    if args.list_dir is not None:
        root = args.list_dir.resolve()
        output = (pathlib.Path(os.path.abspath(args.out)) if args.out else
                  root / "near-limit.txt")
        if not root.is_dir():
            print(f"{TAG}: REFUSED .: list directory is absent",
                  file=sys.stderr)
            return 1
        return list_records(root, output)
    try:
        return self_test(args.scratch or REPO / "build/mvp/tmp/"
                         "near-limit-self-test")
    except OSError as error:
        text = error.strerror or type(error).__name__
        print(f"{TAG}_SELF_TEST: FAIL {text}")
        return 1
    except Refusal as error:
        text = str(error).replace(str(REPO), ".")
        print(f"{TAG}_SELF_TEST: FAIL {text}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
