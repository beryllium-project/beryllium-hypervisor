#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""
qualify.py --run [--out DIR] [--arm ARM]
qualify.py --self-test

Purpose: the qualification suites of MVP M8's decision rule (planning/
mvp-m8-plan.md, D-7 item 2, H41 stage 3; Q6): before any arm meets a leaf,
each arm is run with each of its solvers on five cases of tiny,
self-contained files under mvp/verify/qualify/ (and the litmus arm's under
mvp/verify/litmus/qualify/), never the leaf: known-pass (a correct
function with a provable contract), known-fail (a false contract),
vacuity-requires (a contradictory precondition, which the tool's own check
must detect: WP's -wp-smoke-tests; for CBMC and CN an assert(false) after
it, which verifies only if no state reaches it; for herd7 a filter no
execution satisfies), vacuity-ensures (`ensures \\false`, or the litmus
"never" claim on an allowed outcome, under a satisfiable precondition),
and wrong-implementation (a planted defect against a true contract). The
arms: WP (frama-c -wp -wp-rte, the LP64 machdep gcc_x86_64) with
Alt-Ergo, Z3, and cvc5 through Why3; CBMC (bounds, pointer, signed and
unsigned overflow, and unwinding checks, --unwind 5) with its SAT solver
and its --z3 and --cvc5 SMT back ends; CN (cn verify) with
--solver-type=z3 and cvc5; and herd7 with the RISC-V model riscv.cat.
Every case runs under the plan's limit of 60 s per goal (WP's
-wp-timeout; CBMC, CN, and herd7 runs are killed after 60 s).
Inputs: expectations.json (schema be-mvp-qualify-v1): one row per arm,
solver, and case, naming its file and its expected verdict, which must be
the case's rule: known-pass proved, known-fail unproved, vacuity-requires
detected, vacuity-ensures unproved, wrong-implementation failed, so that
no expectation can be loosened to match an outcome. The tools come from
PATH (the verifier image's, tools/verifier/Containerfile); WHY3CONFIG and
CERB_INSTALL_PREFIX from the environment.
Verdicts observed: proved (every goal closed; CBMC VERIFICATION
SUCCESSFUL; every CN function pass; herd7 Never over at least one
execution); unproved (a goal left open: WP's Timeout, Unknown,
Unsuccess, or Failed status); failed (refuted: CBMC VERIFICATION FAILED,
a CN fail, herd7 Sometimes or Always); detected and undetected (the
vacuity-requires check); error (no verdict: the run timed out, crashed, or
printed none). The judgement: proved needs proved, detected needs
detected, and unproved and failed (the contract must not prove) each
accept unproved or failed, the record keeping which; error is never
right. A WP proved or detected must also have been reached by the named
solver (a goal it closed, or a smoke goal it doomed), not by WP's
simplifier alone. An (arm, solver) pair is qualified when all five of its
cases are right; a pair whose tool is not in the image is not run, with
the reason.
Outputs: in DIR (default build/mvp/verify): qualification.txt (the
probes: tool versions, the provers Why3 detects, the ACSL importer, the
machdeps; a line per case, a line per pair; last `BE_MVP_QUALIFY: PASS
arms=N qualified=M not_run=K`, N counting (arm, solver) pairs),
qualification.json, and qualify/ARM/SOLVER/CASE/ with each run's command
and output. PASS means the qualification ran and is recorded, whatever its
outcome; the outcome is the qualified count and the lines.
Exit status: 0 PASS; 1 the runner failed (the expectations, a fixture, a
record); 2 usage.
"""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[3]
VERIFY = REPO / "mvp" / "verify"
QUALIFY = VERIFY / "qualify"
EXPECTATIONS = QUALIFY / "expectations.json"
TAG = "BE_MVP_QUALIFY"
SCHEMA = "be-mvp-qualify-v1"
SPECIFICATION_SHA256 = ("ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f"
                        "4c542ecc9dc53d")
GOAL_SECONDS = 60
MARKER = ".qualify-run"
RULE = {"known-pass": "proved", "known-fail": "unproved",
        "vacuity-requires": "detected", "vacuity-ensures": "unproved",
        "wrong-implementation": "failed"}
NOT_PROVED = ("unproved", "failed")
ARMS = {"wp": ("alt-ergo", "z3", "cvc5"), "cbmc": ("sat", "z3", "cvc5"),
        "cn": ("z3", "cvc5"), "litmus": ("herd7",)}
TOOL = {"wp": "frama-c", "cbmc": "cbmc", "cn": "cn", "litmus": "herd7"}
# WP's prover name, and the label its summary gives the prover's goals.
WP_PROVERS = {"alt-ergo": ("alt-ergo", "Alt-Ergo"), "z3": ("z3", "Z3"),
              "cvc5": ("cvc5", "CVC5")}
WP_MACHDEP = "gcc_x86_64"
CBMC_CHECKS = ("--bounds-check", "--pointer-check", "--signed-overflow-check",
               "--unsigned-overflow-check", "--unwinding-assertions",
               "--unwind", "5")
CBMC_SOLVERS = {"sat": (), "z3": ("--z3",), "cvc5": ("--cvc5",)}
# A WP run holds a handful of goals, each limited to GOAL_SECONDS.
WP_RUN_SECONDS = 20 * GOAL_SECONDS


class Refusal(Exception):
    """The expectations, a fixture, or the output directory refused."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------ expectations
def load(text, root=QUALIFY):
    """The expectation rows, each (arm, solver, case, path, expected), once
    the document is the schema's, every row's verdict is its case's rule,
    every file exists inside mvp/verify, and every (arm, solver) pair has
    each case exactly once."""
    try:
        document = json.loads(text)
    except ValueError as error:
        raise Refusal(f"expectations.json is not JSON: {error}") from error
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        raise Refusal(f"expectations.json is not schema {SCHEMA}")
    if document.get("specification_sha256") != SPECIFICATION_SHA256:
        raise Refusal("expectations.json cites another specification")
    if document.get("goal_seconds") != GOAL_SECONDS:
        raise Refusal(f"expectations.json's goal_seconds is not the plan's "
                      f"{GOAL_SECONDS}")
    rows, seen = [], {}
    for number, row in enumerate(document.get("cases") or [], 1):
        if not isinstance(row, dict) or set(row) != {"arm", "solver", "case",
                                                     "file", "expected"}:
            raise Refusal(f"case {number} is not arm, solver, case, file, "
                          "expected")
        arm, solver, case = row["arm"], row["solver"], row["case"]
        if arm not in ARMS or solver not in ARMS[arm]:
            raise Refusal(f"case {number}: no arm {arm!r} with solver "
                          f"{solver!r}")
        if case not in RULE:
            raise Refusal(f"case {number}: no case {case!r}")
        if row["expected"] != RULE[case]:
            raise Refusal(f"case {number}: {arm} {solver} {case} expects "
                          f"{row['expected']!r}, not its rule's "
                          f"{RULE[case]!r}")
        if (arm, solver, case) in seen:
            raise Refusal(f"case {number}: {arm} {solver} {case} repeats "
                          f"case {seen[(arm, solver, case)]}")
        seen[(arm, solver, case)] = number
        path = (root / row["file"]).resolve()
        if not path.is_relative_to(VERIFY) or not path.is_file():
            raise Refusal(f"case {number}: {row['file']} is not a file "
                          "under mvp/verify")
        rows.append((arm, solver, case, path, row["expected"]))
    if not rows:
        raise Refusal("expectations.json has no case")
    for arm, solver in sorted({(a, s) for a, s, *_ in rows}):
        missing = sorted(set(RULE) - {c for a, s, c, *_ in rows
                                      if (a, s) == (arm, solver)})
        if missing:
            raise Refusal(f"{arm} {solver} lacks {', '.join(missing)}")
    return rows


# ------------------------------------------------------------------ parsers
def parse_wp(output, solver, case):
    """(observed, detail, exercised) of a frama-c -wp run's output."""
    label = WP_PROVERS[solver][1]
    match = re.search(r"^\[wp\] Proved goals:\s+(\d+) / (\d+)$", output, re.M)
    if not match:
        return "error", "no `[wp] Proved goals` line", None
    proved, total = int(match[1]), int(match[2])
    counts, smoke = {}, None
    for line in output[match.end():].split("\n")[1:]:
        entry = re.match(r"^  (\S.*?):\s+(\d+)(?: / (\d+))?", line)
        if not entry:
            break
        if entry[1] == "Smoke Tests":
            smoke = (int(entry[2]), int(entry[3] or 0))
        else:
            counts[entry[1].strip()] = int(entry[2])
    by_solver = sum(n for name, n in counts.items()
                    if name.split(" ")[0].lower() == label.lower())
    detail = (f"goals={proved}/{total} {label.lower()}_goals={by_solver} " +
              " ".join(f"{name.lower().replace(' ', '_')}={n}"
                       for name, n in sorted(counts.items())
                       if name in ("Timeout", "Unknown", "Unsuccess",
                                   "Failed", "Stepout", "Invalid")))
    if case == "vacuity-requires":
        doomed = re.findall(r"^\[wp\] \[Failed\] \(Doomed\) (\S+) (.*)$",
                            output, re.M)
        by = sorted({name for _, rest in doomed
                     for name in re.findall(r"\(([A-Za-z0-9-]+)", rest)})
        detail += (f" smoke={smoke[0]}/{smoke[1]}" if smoke else
                   " smoke=none") + f" doomed_by={','.join(by) or 'none'}"
        if "Failed smoke-test" in output and smoke and smoke[0] < smoke[1]:
            return "detected", detail, any(
                name.lower() == label.lower() for name in by)
        return "undetected", detail, None
    if total > 0 and proved == total:
        return "proved", detail, by_solver > 0
    return "unproved", detail, None


def parse_cbmc(output, case):
    """(observed, detail, exercised) of a cbmc run's output."""
    solving = re.findall(r"^(Solving with .*|Running SMT2 .*|Running "
                         r"propositional reduction)$", output, re.M)
    detail = f"solver={solving[-1].replace(' ', '_') if solving else 'none'}"
    failures = len(re.findall(r": FAILURE$", output, re.M))
    if re.search(r"^VERIFICATION SUCCESSFUL$", output, re.M):
        return ("detected" if case == "vacuity-requires" else "proved",
                detail + " failures=0", None)
    if re.search(r"^VERIFICATION FAILED$", output, re.M):
        return ("undetected" if case == "vacuity-requires" else "failed",
                detail + f" failures={failures}", None)
    return "error", detail + " no VERIFICATION line", None


def parse_cn(output, case):
    """(observed, detail, exercised) of a cn verify run's output."""
    results = re.findall(r"^\[(\d+)/(\d+)\]: (\S+) -- (pass|fail)$", output,
                         re.M)
    if not results:
        return "error", "no `[i/n]: function -- pass|fail` line", None
    failing = [name for _, _, name, verdict in results if verdict == "fail"]
    detail = f"functions={len(results)} fail={len(failing)}"
    if case == "vacuity-requires":
        return ("undetected" if failing else "detected"), detail, None
    return ("failed" if failing else "proved"), detail, None


def parse_herd(output, case):
    """(observed, detail, exercised) of a herd7 run's output."""
    match = re.search(r"^Observation (\S+) (Never|Sometimes|Always) (\d+) "
                      r"(\d+)$", output, re.M)
    if not match:
        return "error", "no Observation line", None
    positive, negative = int(match[3]), int(match[4])
    detail = f"observation={match[2]} positive={positive} negative={negative}"
    if case == "vacuity-requires":
        return ("detected" if positive + negative == 0 else "undetected",
                detail, None)
    if positive + negative == 0:
        return "error", detail + " no execution", None
    return ("proved" if match[2] == "Never" else "failed"), detail, None


def judge(expected, observed, exercised):
    """Whether OBSERVED meets EXPECTED (the module's judgement)."""
    if observed == "error" or exercised is False:
        return False
    if expected in NOT_PROVED:
        return observed in NOT_PROVED
    return observed == expected


# ------------------------------------------------------------------- runner
def execute(command, cwd, environment, seconds):
    """(status, output, seconds): status the exit code or 'timeout'."""
    started = time.monotonic()
    try:
        done = subprocess.run(command, cwd=cwd, env=environment,
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=seconds,
                              check=False)
        status, output = done.returncode, done.stdout
    except subprocess.TimeoutExpired as expired:
        status, output = "timeout", expired.stdout or b""
    return (status, output.decode("utf-8", "replace"),
            round(time.monotonic() - started, 1))


def command_for(arm, solver, case, path, scratch):
    if arm == "wp":
        return ["frama-c", "-wp", "-wp-rte", "-wp-prover",
                WP_PROVERS[solver][0], "-wp-timeout", str(GOAL_SECONDS),
                "-wp-cache", "none", "-wp-out", str(scratch / "wp-out"),
                "-machdep", WP_MACHDEP] + (
                    ["-wp-smoke-tests"] if case == "vacuity-requires"
                    else []) + [str(path)], WP_RUN_SECONDS
    if arm == "cbmc":
        return ["cbmc", *CBMC_CHECKS, *CBMC_SOLVERS[solver],
                str(path)], GOAL_SECONDS
    if arm == "cn":
        return ["cn", "verify", f"--solver-type={solver}",
                str(path)], GOAL_SECONDS
    return ["herd7", "-model", "riscv.cat", str(path)], GOAL_SECONDS


def run_case(arm, solver, case, path, directory):
    directory.mkdir(parents=True)
    command, seconds = command_for(arm, solver, case, path, directory)
    environment = dict(os.environ, TMPDIR=str(directory))
    status, output, elapsed = execute(command, directory, environment,
                                      seconds)
    (directory / "command.txt").write_text(
        " ".join(command) + f"\nlimit_seconds={seconds}\nstatus={status}\n"
        f"seconds={elapsed}\n", encoding="utf-8")
    (directory / "output.log").write_text(output, encoding="utf-8")
    if status == "timeout":
        return "error", f"killed after {seconds} s", None, elapsed
    parser = {"wp": lambda: parse_wp(output, solver, case),
              "cbmc": lambda: parse_cbmc(output, case),
              "cn": lambda: parse_cn(output, case),
              "litmus": lambda: parse_herd(output, case)}[arm]
    observed, detail, exercised = parser()
    if observed == "error":
        detail += f" exit={status}"
    return observed, detail, exercised, elapsed


def first_line(command, seconds=60):
    status, output, _ = execute(command, None, dict(os.environ), seconds)
    lines = [line.strip() for line in output.split("\n") if line.strip()]
    return lines[0] if lines and status == 0 else f"unavailable (exit {status})"


def probes():
    """The facts the qualification depends on, from the image's tools."""
    found = {}
    for name, command in (
            ("frama-c", ["frama-c", "-version"]),
            ("why3", ["why3", "--version"]),
            ("alt-ergo", ["alt-ergo", "--version"]),
            ("z3", ["z3", "--version"]), ("cvc5", ["cvc5", "--version"]),
            ("cbmc", ["cbmc", "--version"]),
            ("herd7", ["herd7", "-version"]), ("cn", ["cn", "--version"])):
        found[f"version_{name}"] = (first_line(command) if shutil.which(
            command[0]) else "not in the image")
    if shutil.which("why3"):
        _, output, _ = execute(["why3", "config", "list-provers"], None,
                               dict(os.environ), 60)
        found["why3_provers"] = "; ".join(
            line.strip() for line in output.split("\n") if line.strip())
    if shutil.which("frama-c"):
        _, plugins, _ = execute(["frama-c", "-plugins"], None,
                                dict(os.environ), 60)
        importer = re.search(r"^ACSL importer\s+(.*)$", plugins, re.M)
        found["acsl_importer"] = (f"present: {importer[1].strip()}" if
                                  importer else "absent from frama-c -plugins")
        _, machdeps, _ = execute(["frama-c", "-machdep", "help"], None,
                                 dict(os.environ), 60)
        listed = re.search(r"supported machines are (.*?) \(default",
                           " ".join(machdeps.split()))
        found["machdeps"] = listed[1] if listed else "unlisted"
        _, printed, _ = execute(["frama-c", "-machdep", WP_MACHDEP,
                                 "-print-machdep"], None, dict(os.environ),
                                60)
        facts = [f"{kind}={size}" for kind, size in re.findall(
            r"sizeof\s+(long|pointer|int) =\s+(\d+)", printed)]
        sign = re.search(r"^\s*char is (signed|unsigned)", printed, re.M)
        found["machdep_used"] = (f"{WP_MACHDEP} {' '.join(facts)} char_"
                                 f"{sign[1] if sign else 'unknown'} "
                                 "(RISC-V LP64 has unsigned char)")
    if shutil.which("cbmc"):
        _, helped, _ = execute(["cbmc", "--help"], None, dict(os.environ), 60)
        found["cbmc_riscv64_arch"] = ("available" if re.search(
            r"\briscv64\b", helped) else "absent")
        _, solved, _ = execute(["cbmc", "--verbosity", "9", "--unwind", "5",
                                str(QUALIFY / "cbmc" / "known-pass.c")],
                               None, dict(os.environ), 60)
        solver = re.search(r"^Solving with (.*)$", solved, re.M)
        found["cbmc_sat_solver"] = solver[1] if solver else "unknown"
    return found


def prepare(out):
    """OUT/qualify, emptied if it is this tool's, else refused."""
    runs = out / "qualify"
    if runs.is_symlink() or (runs.exists() and not runs.is_dir()):
        raise Refusal(f"{runs} is a symbolic link or not a directory")
    if runs.is_dir() and any(runs.iterdir()) and \
            not (runs / MARKER).is_file():
        raise Refusal(f"{runs} is not empty and not this tool's")
    shutil.rmtree(runs, ignore_errors=True)
    runs.mkdir(parents=True)
    (runs / MARKER).touch()
    return runs


def run(out, only):
    rows = load(EXPECTATIONS.read_text(encoding="utf-8"))
    if only:
        rows = [row for row in rows if row[0] == only]
    out.mkdir(parents=True, exist_ok=True)
    runs = prepare(out)
    started = time.monotonic()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    facts = probes()
    results, pairs = [], {}
    for arm, solver, case, path, expected in rows:
        tool = TOOL[arm]
        if not shutil.which(tool):
            reason = f"{tool} is not in the image"
            observed, detail, exercised, elapsed = "not-run", reason, None, 0
            ok = None
        else:
            observed, detail, exercised, elapsed = run_case(
                arm, solver, case, path, runs / arm / solver / case)
            ok = judge(expected, observed, exercised)
            if exercised is False:
                detail += " solver_unexercised"
        results.append({"arm": arm, "solver": solver, "case": case,
                        "file": str(path.relative_to(REPO)),
                        "expected": expected, "observed": observed,
                        "ok": ok, "seconds": elapsed, "detail": detail})
        print(f"{TAG}: case arm={arm} solver={solver} case={case} "
              f"expected={expected} observed={observed} ok="
              f"{'not-run' if ok is None else 'yes' if ok else 'no'}",
              flush=True)
    for result in results:
        pair = pairs.setdefault((result["arm"], result["solver"]), [])
        pair.append(result)
    summary = []
    for (arm, solver), cases in pairs.items():
        if any(case["ok"] is None for case in cases):
            state, reason = "not-run", cases[0]["detail"]
        else:
            wrong = [case["case"] for case in cases if not case["ok"]]
            state = "no" if wrong else "yes"
            reason = ",".join(wrong)
        summary.append({"arm": arm, "solver": solver, "qualified": state,
                        "reason": reason})
    qualified = sum(item["qualified"] == "yes" for item in summary)
    not_run = sum(item["qualified"] == "not-run" for item in summary)
    final = (f"{TAG}: PASS arms={len(summary)} qualified={qualified} "
             f"not_run={not_run}")
    expectations_sha = sha256(EXPECTATIONS.read_bytes())
    lines = [f"# MVP M8 qualification (planning/mvp-m8-plan.md, D-7 item 2)",
             f"specification_sha256={SPECIFICATION_SHA256}",
             f"expectations_sha256={expectations_sha}",
             f"started={stamp} seconds={round(time.monotonic() - started)}",
             f"goal_seconds={GOAL_SECONDS}"]
    lines += [f"probe {key}={value}" for key, value in facts.items()]
    lines += [f"case arm={r['arm']} solver={r['solver']} case={r['case']} "
              f"expected={r['expected']} observed={r['observed']} ok="
              f"{'not-run' if r['ok'] is None else 'yes' if r['ok'] else 'no'}"
              f" seconds={r['seconds']} detail={r['detail']}"
              for r in results]
    lines += [f"pair arm={s['arm']} solver={s['solver']} qualified="
              f"{s['qualified']}" + (
                  f" not_qualified_cases={s['reason']}" if s["qualified"] ==
                  "no" else f" reason=not qualified (not run): {s['reason']}"
                  if s["qualified"] == "not-run" else "") for s in summary]
    lines.append(final)
    (out / "qualification.txt").write_text("\n".join(lines) + "\n",
                                           encoding="utf-8")
    (out / "qualification.json").write_text(json.dumps(
        {"schema": "be-mvp-qualification-record-v1",
         "specification_sha256": SPECIFICATION_SHA256,
         "expectations_sha256": expectations_sha, "started": stamp,
         "goal_seconds": GOAL_SECONDS, "probes": facts, "cases": results,
         "pairs": summary}, indent=1) + "\n", encoding="utf-8")
    for item in summary:
        print(f"{TAG}: pair arm={item['arm']} solver={item['solver']} "
              f"qualified={item['qualified']}"
              + (f" ({item['reason']})" if item["reason"] else ""))
    print(final)
    return 0


# ---------------------------------------------------------------- self-test
WP_PROVED = """\
[wp] 17 goals scheduled
[wp] Proved goals:   19 / 19
  Terminating:     1
  Unreachable:     1
  Qed:            12 (1ms-1ms-5ms)
  Alt-Ergo :       5 (5ms-13ms)
"""
WP_QED_ONLY = WP_PROVED.replace("  Alt-Ergo :       5 (5ms-13ms)\n", "")
WP_OPEN = """\
[wp] [Timeout] typed_first_used_ensures (Qed 6ms) (Alt-Ergo)
[wp] Proved goals:   18 / 19
  Qed:            12 (1ms-1ms-6ms)
  Alt-Ergo :       4 (7ms-12ms)
  Timeout:         1
"""
WP_FAILURE = """\
[wp] [Failure] typed_excess_ensures (Qed 0.63ms) (Alt-Ergo)
[wp] Proved goals:    3 / 4
  Terminating:     1
  Unreachable:     1
  Qed:             1 (0.31ms)
  Failed:          1
"""
WP_SMOKE = """\
[wp] [Failed] (Doomed) typed_first_used_wp_smoke_default_requires (Z3 17ms)
[wp] vacuity-requires.c:27: Warning: 
  Failed smoke-test
[wp] Proved goals:    6 / 9
  Qed:             2 (0.58ms-0.60ms-2ms)
  Z3 4.16.0:       2 (9ms-19ms-24ms)
  Failed:          3
  Smoke Tests:     0 / 3
"""
WP_SMOKE_QED = WP_SMOKE.replace("(Z3 17ms)", "(Qed)")
WP_SMOKE_PASSED = """\
[wp] [Timeout] typed_first_used_ensures (Qed 2ms) (CVC5)
[wp] Proved goals:    7 / 9
  Qed:             2 (0.58ms-0.60ms-2ms)
  CVC5 :           3
  Timeout:         2
  Smoke Tests:     3 / 3
"""
HERD = ("Test MP Allowed\nStates 4\nOk\nWitnesses\nPositive: 1 Negative: 3\n"
        "Observation MP {} {} {}\nTime MP 0.00\n")


def self_test():
    results = []

    def case(name, passed, detail=""):
        results.append(bool(passed))
        print(f"{'ok  ' if passed else 'FAIL'} {name}"
              f"{'' if passed else ': ' + str(detail)[-600:]}")

    def refused(name, text, wanted):
        try:
            load(text)
        except Refusal as why:
            case(name, wanted in str(why), why)
        else:
            case(name, False, "not refused")

    text = EXPECTATIONS.read_text(encoding="utf-8")
    try:
        rows = load(text)
    except Refusal as why:
        case("the committed expectations load", False, why)
        rows = []
    pairs = sorted({(arm, solver) for arm, solver, *_ in rows})
    case("the committed expectations load", len(rows) == 45 and pairs == sorted(
        (arm, solver) for arm, solvers in ARMS.items() for solver in solvers),
         (len(rows), pairs))
    case("every pair has its four cases (vacuity's two checks)", all(
        sorted(c for a, s, c, *_ in rows if (a, s) == pair) == sorted(RULE)
        for pair in pairs))
    document = json.loads(text)
    first = json.dumps(document["cases"][0])

    def edited(change):
        copy = json.loads(text)
        change(copy)
        return json.dumps(copy)
    refused("a duplicated case", text.replace(
        first, first + ",\n " + first, 1), "repeats case 1")
    refused("a missing case", edited(lambda d: d["cases"].pop(3)),
            "wp alt-ergo lacks vacuity-ensures")
    refused("an expectation loosened", edited(
        lambda d: d["cases"][1].update(expected="proved")),
        "expects 'proved', not its rule's 'unproved'")
    refused("an unknown arm", edited(
        lambda d: d["cases"][0].update(arm="vst")), "no arm 'vst'")
    refused("an unknown solver", edited(
        lambda d: d["cases"][0].update(solver="yices")), "solver 'yices'")
    refused("an unknown case", edited(
        lambda d: d["cases"][0].update(case="smoke")), "no case 'smoke'")
    refused("a fixture outside mvp/verify", edited(
        lambda d: d["cases"][0].update(file="../../src/mvp-sbi.c")),
        "not a file under mvp/verify")
    refused("a missing fixture", edited(
        lambda d: d["cases"][0].update(file="wp/absent.c")),
        "not a file under mvp/verify")
    refused("another specification", edited(
        lambda d: d.update(specification_sha256="0" * 64)),
        "another specification")
    refused("another per-goal limit", edited(
        lambda d: d.update(goal_seconds=600)), "goal_seconds")
    refused("another schema", edited(lambda d: d.update(schema="v0")),
            "is not schema")
    refused("an extra field", edited(
        lambda d: d["cases"][0].update(note="x")), "is not arm, solver")
    for name, output, solver, kind, wanted in (
            ("WP proved, the solver closing goals", WP_PROVED, "alt-ergo",
             "known-pass", ("proved", True)),
            ("WP proved by its simplifier alone", WP_QED_ONLY, "alt-ergo",
             "known-pass", ("proved", False)),
            ("WP with a goal timed out", WP_OPEN, "alt-ergo", "known-fail",
             ("unproved", None)),
            ("WP with a prover failure", WP_FAILURE, "alt-ergo",
             "vacuity-ensures", ("unproved", None)),
            ("WP smoke test failed by the solver", WP_SMOKE, "z3",
             "vacuity-requires", ("detected", True)),
            ("WP smoke test failed by Qed alone", WP_SMOKE_QED, "z3",
             "vacuity-requires", ("detected", False)),
            ("WP smoke tests passed", WP_SMOKE_PASSED, "cvc5",
             "vacuity-requires", ("undetected", None)),
            ("WP without a summary", "[wp] User Error: x\n", "z3",
             "known-pass", ("error", None))):
        observed, detail, exercised = parse_wp(output, solver, kind)
        case(name, (observed, exercised) == wanted,
             (observed, exercised, detail))
    for name, parsed, wanted in (
            ("CBMC successful", parse_cbmc(
                "Running propositional reduction\nVERIFICATION SUCCESSFUL\n",
                "known-pass"), "proved"),
            ("CBMC successful on a reachability check", parse_cbmc(
                "VERIFICATION SUCCESSFUL\n", "vacuity-requires"), "detected"),
            ("CBMC failed", parse_cbmc(
                "[main.assertion.1] line 41 x: FAILURE\nVERIFICATION FAILED\n",
                "wrong-implementation"), "failed"),
            ("CBMC failed on a reachability check", parse_cbmc(
                "VERIFICATION FAILED\n", "vacuity-requires"), "undetected"),
            ("CBMC with no verdict", parse_cbmc(
                "Running SMT2 QF_AUFBV using Z3\n", "known-fail"), "error"),
            ("CN pass", parse_cn("[1/1]: slot_end -- pass\n", "known-pass"),
             "proved"),
            ("CN fail", parse_cn("[1/2]: f -- pass\n[2/2]: g -- fail\n",
                                 "known-fail"), "failed"),
            ("CN pass on a reachability check", parse_cn(
                "[1/1]: slot_end -- pass\n", "vacuity-requires"), "detected"),
            ("CN with no verdict", parse_cn("error: Type error\n",
                                            "known-pass"), "error"),
            ("herd7 Never", parse_herd(HERD.format("Never", 0, 3),
                                       "known-pass"), "proved"),
            ("herd7 Sometimes", parse_herd(HERD.format("Sometimes", 1, 3),
                                           "known-fail"), "failed"),
            ("herd7 with no execution", parse_herd(
                HERD.format("Never", 0, 0), "vacuity-requires"), "detected"),
            ("herd7 Never with no execution elsewhere", parse_herd(
                HERD.format("Never", 0, 0), "known-pass"), "error"),
            ("herd7 executions under a filter", parse_herd(
                HERD.format("Never", 0, 3), "vacuity-requires"),
             "undetected")):
        case(name, parsed[0] == wanted, parsed)
    for expected, observed, exercised, wanted in (
            ("proved", "proved", True, True), ("proved", "proved", False,
                                               False),
            ("proved", "unproved", None, False),
            ("unproved", "unproved", None, True),
            ("unproved", "failed", None, True),
            ("unproved", "proved", None, False),
            ("failed", "unproved", None, True),
            ("failed", "error", None, False),
            ("detected", "detected", None, True),
            ("detected", "undetected", None, False),
            ("detected", "detected", False, False)):
        case(f"judge {expected} {observed} {exercised}",
             judge(expected, observed, exercised) == wanted)
    print(f"{TAG}_SELF_TEST: {'PASS' if all(results) else 'FAIL'} "
          f"cases={len(results)}"
          f"{'' if all(results) else f' failed={results.count(False)}'}")
    return 0 if all(results) else 1


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--arm", choices=sorted(ARMS))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv[1:])
    if args.self_test == args.run or (args.self_test and (args.out or
                                                          args.arm)):
        parser.error("give --run [--out DIR] [--arm ARM], or --self-test")
    if args.self_test:
        return self_test()
    try:
        return run((args.out or REPO / "build" / "mvp" / "verify").resolve(),
                   args.arm)
    except (OSError, Refusal) as why:
        print(f"{TAG}: FAIL {why}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
