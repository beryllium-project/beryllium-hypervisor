#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""
wp-arm.py --run [--out DIR] [--jobs N]
wp-arm.py --retain DIR [--out DIR]
wp-arm.py --self-test

Purpose: the pilot's WP arm on Leaf A (planning/mvp-m8-plan.md, D-4, D-5,
D-7, M8-6; decision A: Alt-Ergo 2.4.3 alone, so D-7 item 7's pair is not
formed; specification sections 4 and 6 as its Revision 1 states them,
SHA-256 aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b,
accepted 2026-11-03 at 93a8d136; the first run judged against the
accepted text of 004f31ae, ade32fa6...). Frama-C's ACSL importer places
mvp/verify/wp/mvp-sbi-leaf.acsl (round 0, the contract's transcription)
and round-1.acsl to round-N.acsl (each round's annotations; at most four)
on the unmodified mvp/src/mvp-sbi.c, compiled with the target's include
directories and the LP64 machdep gcc_x86_64, and WP proves every goal of
the five functions with -wp-rte, -warn-unsigned-overflow, and
-warn-unsigned-downcast, Alt-Ergo through mvp/verify/wp/why3.conf, 60 s per
goal. A round file's `// wp-options:` line sets that round's WP options
and `// wp-lemma-options:` the options of its lemmas' own run (lemmas do
not depend on the code); a round's `at N:` placement is resolved from
its `// anchor:` line for each source (the leaf, each mutant). In order:
the target digests (D-7 item 3); the
WP qualification cases re-run under this configuration (item 2); every
round, its goal counts and wall time (item 5); the vacuity checks on the
final annotations (item 6: WP's smoke tests, which must not doom a
function's preconditions; `ensures \\false` per function, which must not
prove; a contradictory requires per function, which the smoke tests must
doom); the 24 seeded mutants through the final annotations, each killed by
a goal the unmutated leaf closes or else judged by the host test; Q17
(whether WP can print goals for Rocq 9.3); and the digests again. Alt-Ergo
gives no counterexample: a goal it does not prove is recorded with how it
ended, and a clause that fails on the leaf is CBMC's arm's to show
(cbmc-leaf-a.py's defect.txt).
Outputs: in DIR (default build/mvp/verify/wp): rounds.txt, goals.txt,
assumptions.txt, mutants.txt, vacuity.txt, transcription.txt, and each
run's command, output, and report under runs/; last the line
`BE_MVP_WP_ARM: CLOSED|OPEN goals=N proved=M
rounds=R solvers=alt-ergo mutants=K killed=A unobservable=B
contract-findings=C vacuity=ok|not-ok pair=not-formed`. CLOSED means every
goal of the final round proved; OPEN is the arm's recorded non-result.
--retain DIR copies the six records to DIR (mvp/results/<date>-verify/
leaf-a/wp/). --self-test checks the parsing and the judging on recorded
outputs, on the host.
Exit status: 0 the run completed and is recorded (whatever its RESULT); 1
the runner failed; 2 usage.
"""

import argparse
import collections
import concurrent.futures
import importlib.util
import json
import pathlib
import re
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LIB = load("arm_lib", "arm-lib.py")
QUALIFY = load("qualify", "qualify.py")
REPO = LIB.REPO
TAG = "BE_MVP_WP_ARM"
WP_DIR = REPO / "mvp" / "verify" / "wp"
BASE = WP_DIR / "mvp-sbi-leaf.acsl"
WHY3 = WP_DIR / "why3.conf"
MARKER = ".wp-arm-run"
MACHDEP = "gcc_x86_64"
KERNEL = ("-machdep", MACHDEP, "-warn-unsigned-overflow",
          "-warn-unsigned-downcast")
PAR = "6"
PROVE = ("-wp-prover", "alt-ergo", "-wp-timeout", str(LIB.GOAL_SECONDS),
         "-wp-par", PAR, "-wp-cache", "none")
# Only the smoke tests: every category of property left out.
SMOKE = ("-wp-smoke-tests", "-wp-smoke-timeout", str(LIB.GOAL_SECONDS),
         "-wp-prop=-@ensures,-@assigns,-@exits,-@terminates,-@assert,"
         "-@invariant,-@variant,-@requires,-@check,-@lemma")
RUN_SECONDS = 4 * 3600
MAX_ROUNDS = 4
STRATEGIES = {"wp:split", "wp:bitwised", "wp:bitrange", "wp:bittestrange",
              "wp:bitshift", "wp:range"}
NULL_TESTS = 5
CONTRADICTION = {
    "access_fault": "scause < 20 && scause > 23",
    "htinst_accepted": "htinst < 1 && htinst > 1",
    "inside": "bytes < 1 && bytes > 1",
    "leaf_at": "leaves->page[0].bytes < 1 && leaves->page[0].bytes > 1",
    "be_mvp_denial_decide": "map->size < 1 && map->size > 1"}


class Refusal(Exception):
    """A round file or an option this runner refuses."""


# ---------------------------------------------------------------- rounds
def round_files(directory=WP_DIR):
    """[round 0's file, round 1's, ...]: round-1.acsl to round-N.acsl with
    no gap and at most four."""
    numbers = []
    for path in directory.glob("round-*.acsl"):
        match = re.fullmatch(r"round-([1-9][0-9]*)\.acsl", path.name)
        if not match:
            raise Refusal(f"{path.name} is not round-N.acsl")
        numbers.append(int(match[1]))
    if sorted(numbers) != list(range(1, len(numbers) + 1)):
        raise Refusal(f"round files {sorted(numbers)} are not 1 to N")
    if len(numbers) > MAX_ROUNDS:
        raise Refusal(f"{len(numbers)} rounds: D-7 item 5 allows four")
    return [directory / "mvp-sbi-leaf.acsl"] + [
        directory / f"round-{n}.acsl" for n in range(1, len(numbers) + 1)]


def checked_options(words, where):
    """WORDS if every one is -wp-split or -wp-auto=STRATEGIES (an
    allowlist: a round may choose WP's own proof search, nothing else)."""
    for word in words:
        if word == "-wp-split":
            continue
        match = re.fullmatch(r"-wp-auto=([a-z:,]+)", word)
        if not match or not set(match[1].split(",")) <= STRATEGIES:
            raise Refusal(f"{where}: option {word!r} is not allowed")
    return list(words)


def settings(files):
    """(options, lemma options, has lemmas) of the round whose files are
    FILES: each option line's last occurrence among them."""
    options, lemma_options, lemmas = [], [], False
    for path in files:
        text = path.read_text(encoding="utf-8")
        lemmas = lemmas or bool(re.search(r"^lemma ", text, re.M))
        for key, value in re.findall(r"^// (wp-options|wp-lemma-options):"
                                     r"(.*)$", text, re.M):
            words = checked_options(value.split(), path.name)
            if key == "wp-options":
                options = words
            else:
                lemma_options = words
    return options, lemma_options, lemmas


# ---------------------------------------------------------------- anchors
# A round may place an annotation before a statement no call or loop marks
# by the ACSL importer's `at N:`, N the statement's number in the
# function's own numbering, which a change of control flow renumbers (a
# mutant's `||` for `&&`, a dead branch CIL drops). Each such block is
# anchored by the comment line just before it, `// anchor: before TEXT` or
# `// anchor: after TEXT`, TEXT the anchoring statement's first line as
# Frama-C prints the normalized code; for each source (the leaf, a mutant)
# the runner reads the importer's numbers by a probe and rewrites N in a
# scratch copy of the round file. For the leaf the committed N must be the
# one found, so the file says where its annotations are.
ANCHOR = re.compile(r"^\s*// anchor: (before|after) (\S.*?)\s*$")
AT = re.compile(r"^(\s*)at ([0-9]+):(\s*)$")
PROBE_LIMIT = 400
PROBE_MARK = re.compile(r"ANCHOR_PROBE_([0-9]+):")


def anchors(path):
    """[(line index of `at N:`, N, before or after, TEXT)] of PATH, each
    `at N:` with its anchor comment, or refused."""
    lines = path.read_text(encoding="utf-8").split("\n")
    found = []
    for index, line in enumerate(lines):
        match = AT.match(line)
        if not match:
            continue
        anchor = ANCHOR.match(lines[index - 1]) if index else None
        if not anchor:
            raise Refusal(f"{path.name}:{index + 1}: `at {match[2]}:` has "
                          f"no `// anchor:` line before it")
        found.append((index, int(match[2]), anchor[1], anchor[2]))
    return found


def numbering(printed, function="be_mvp_denial_decide"):
    """{statement number: its first line} of FUNCTION in PRINTED, Frama-C's
    print of a source with the probe's ANCHOR_PROBE_N assertion before
    each statement N."""
    lines = printed.split("\n")
    first = None
    for index, line in enumerate(lines):
        if not re.match(rf"^\w[\w ]*\b{function}\(", line):
            continue
        end = index
        while end < len(lines) and not lines[end].rstrip().endswith(
                (")", ");")):
            end += 1
        if end + 1 < len(lines) and lines[end].rstrip().endswith(")") and \
                lines[end + 1] == "{":
            first = end + 1
            break
    if first is None:
        raise Refusal(f"no definition of {function} in the probe's print")
    last = next(i for i in range(first, len(lines)) if lines[i] == "}")
    found = {}
    for index in range(first, last):
        for number in PROBE_MARK.findall(lines[index]):
            later = index + 1
            while later < last and PROBE_MARK.search(lines[later]):
                later += 1
            found[int(number)] = lines[later].strip()
    return found


def resolved(number_of, anchor):
    """The statement number ANCHOR, (before or after, TEXT), names in
    NUMBER_OF ({number: first line}), or refused."""
    where, text = anchor
    matches = [n for n, line in number_of.items() if line == text]
    if len(matches) != 1:
        raise Refusal(f"anchor {where} {text!r}: {len(matches)} statements")
    return matches[0] + (1 if where == "after" else 0)


PROBES = {}


def place(files, source, scratch):
    """FILES with each anchored `at N:` resolved for SOURCE (scratch copies
    of those with any), and the placements [(file, committed N, N found,
    before or after, TEXT)]; for the leaf, a committed N other than the one
    found is refused."""
    blocks = {path: anchors(path) for path in files}
    if not any(blocks.values()):
        return files, []
    key = str(source)
    if key not in PROBES:
        scratch.mkdir(parents=True, exist_ok=True)
        probe = scratch / "anchor-probe.acsl"
        probe.write_text("function be_mvp_denial_decide:\n" + "".join(
            f"  at {n}:\n    assert ANCHOR_PROBE_{n}: \\true;\n"
            for n in range(1, PROBE_LIMIT + 1)), encoding="utf-8")
        printed = scratch / "anchor-probe.c"
        status, output, _ = LIB.execute(
            ["frama-c", f"-acsl-import={probe}", includes(), *KERNEL,
             str(source), "-kernel-warn-key", "annot-error=active",
             "-print", "-ocode", str(printed)], 600, REPO,
            LIB.environment(TMPDIR=str(scratch)))
        if status != 0 or not printed.is_file():
            raise Refusal(f"the anchor probe failed (exit {status}): "
                          f"{LIB.relative(output.strip()[-300:])}")
        PROBES[key] = numbering(printed.read_text(encoding="utf-8"))
    number_of, placed, copies = PROBES[key], [], []
    for path in files:
        if not blocks[path]:
            copies.append(path)
            continue
        lines = path.read_text(encoding="utf-8").split("\n")
        for index, committed, where, text in blocks[path]:
            found = resolved(number_of, (where, text))
            if source == LIB.LEAF and found != committed:
                raise Refusal(f"{path.name}:{index + 1}: at {committed}: "
                              f"the leaf's statement {where} {text!r} is "
                              f"{found}")
            match = AT.match(lines[index])
            lines[index] = f"{match[1]}at {found}:{match[3]}"
            placed.append((path.name, committed, found, where, text))
        scratch.mkdir(parents=True, exist_ok=True)
        copy = scratch / path.name
        copy.write_text("\n".join(lines), encoding="utf-8")
        copies.append(copy)
    return copies, placed


# ------------------------------------------------------------ running WP
def includes():
    return "-cpp-extra-args=" + " ".join(
        f"-I{d}" for d in LIB.target_flags()["include_dirs"])


def commands(files, source, scratch, options, lemma_options, lemmas,
             functions=LIB.FUNCTIONS, select=None, exclude=(),
             lemma_run=True):
    """{kind: command}: the main run (every goal of FUNCTIONS but the
    lemmas when they have a run of their own, and EXCLUDE's names; or
    SELECT's options in place of that choice) and the lemmas' run."""
    imports = "-acsl-import=" + ",".join(
        str(path.relative_to(REPO)) for path in files)
    head = ["frama-c", imports, includes(), *KERNEL,
            str(source.relative_to(REPO)) if source.is_relative_to(REPO)
            else str(source)]
    split = bool(lemmas and lemma_options)
    props = (["-@lemma"] if split else []) + [f"-{name}" for name in exclude]
    if select is None:
        select = ["-wp-prop=" + ",".join(props)] if props else []
    found = {"main": head + ["-wp", "-wp-rte", "-wp-fct=" + ",".join(
        functions), *PROVE, *options, *select, "-wp-out",
        str(scratch / "main-out"), "-wp-report-json",
        str(scratch / "main.json")]}
    if split and lemma_run:
        found["lemma"] = head + ["-wp", "-wp-prop=@lemma", *PROVE,
                                 *lemma_options, "-wp-out",
                                 str(scratch / "lemma-out"),
                                 "-wp-report-json",
                                 str(scratch / "lemma.json")]
    return found


def prover(name):
    return {"qed": "Qed"}.get(name, name.replace(":", " "))


def parse(text):
    """{property: {function, obligations, valid, verdicts, provers,
    smoke}} of a -wp-report-json report."""
    goals = {}
    for entry in json.loads(text):
        goal = goals.setdefault(entry["property"], {
            "function": entry.get("function", "(lemma)"), "obligations": 0,
            "valid": 0, "verdicts": collections.Counter(),
            "provers": set(), "smoke": bool(entry.get("smoke")),
            "line": entry.get("line")})
        goal["obligations"] += 1
        goal["valid"] += entry["verdict"] == "valid"
        goal["verdicts"][entry["verdict"]] += 1
        goal["provers"] |= {prover(p["prover"]) for p in entry.get(
            "provers", []) if p.get("success")}
        if entry.get("tactics"):
            goal["provers"].add("Script")
    return goals


def state(goal):
    """'proved', or the worst verdict among its obligations."""
    if goal["valid"] == goal["obligations"]:
        return "proved"
    for verdict in ("failed", "invalid", "timeout", "unknown", "stepout"):
        if goal["verdicts"][verdict]:
            return verdict
    return next(v for v in goal["verdicts"] if v != "valid")


def run(files, source, scratch, options, lemma_options, lemmas, **keys):
    """(goals, seconds, problems): every job's report merged."""
    scratch.mkdir(parents=True, exist_ok=True)
    files, _ = place(files, source, scratch / "placed")
    jobs = commands(files, source, scratch, options, lemma_options, lemmas,
                    **keys)
    environment = LIB.environment(WHY3CONFIG=str(WHY3),
                                  TMPDIR=str(scratch))
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(len(jobs)) as pool:
        done = {kind: pool.submit(LIB.execute, command, RUN_SECONDS,
                                  REPO, environment)
                for kind, command in jobs.items()}
    goals, problems = {}, []
    for kind, future in done.items():
        status, output, seconds = future.result()
        (scratch / f"{kind}.command").write_text(
            " ".join(jobs[kind]) + f"\nstatus={status} seconds={seconds}\n",
            encoding="utf-8")
        (scratch / f"{kind}.log").write_text(output, encoding="utf-8")
        report = scratch / f"{kind}.json"
        if status != 0 or not report.is_file():
            problems.append(f"{kind}: exit {status}")
            continue
        goals.update(parse(report.read_text(encoding="utf-8")))
    return goals, round(time.monotonic() - started), problems


def counts(goals):
    proper = {n: g for n, g in goals.items() if not g["smoke"]}
    proved = [n for n, g in proper.items() if state(g) == "proved"]
    return (len(proper), len(proved), sorted(set(proper) - set(proved)),
            sum(g["obligations"] for g in proper.values()),
            sum(g["valid"] for g in proper.values()))


def tallies(goals):
    """The round's goals by what closed them and by how the rest ended."""
    proper = [g for g in goals.values() if not g["smoke"]]
    closed = collections.Counter(
        "script" if "Script" in g["provers"] else "alt_ergo" if any(
            p.startswith("Alt-Ergo") for p in g["provers"]) else "qed"
        for g in proper if state(g) == "proved")
    ended = collections.Counter(state(g) for g in proper
                                if state(g) != "proved")
    return " ".join([f"closed_by_{k}={closed[k]}" for k in
                     ("qed", "alt_ergo", "script")] +
                    [f"{k}={v}" for k, v in sorted(ended.items())])


# ---------------------------------------------------------- qualification
def requalify(scratch, options):
    """The WP qualification's five Alt-Ergo cases (mvp/verify/qualify/,
    read only) under this arm's Why3 configuration and OPTIONS, judged by
    qualify.py's own rule: [(case, expected, observed, ok, detail)]."""
    rows = [row for row in QUALIFY.load(QUALIFY.EXPECTATIONS.read_text(
        encoding="utf-8")) if row[:2] == ("wp", "alt-ergo")]
    environment = LIB.environment(WHY3CONFIG=str(WHY3))
    found = []
    for _, solver, case, path, expected in rows:
        directory = scratch / case
        directory.mkdir(parents=True, exist_ok=True)
        command = ["frama-c", "-wp", "-wp-rte", *PROVE, "-wp-out",
                   str(directory / "wp-out"), "-machdep", MACHDEP,
                   *options] + (["-wp-smoke-tests"] if case ==
                                "vacuity-requires" else []) + [str(path)]
        status, output, seconds = LIB.execute(
            command, QUALIFY.WP_RUN_SECONDS, REPO, environment)
        (directory / "output.log").write_text(output, encoding="utf-8")
        observed, detail, exercised = ("error", f"exit {status}", None) \
            if status != 0 else QUALIFY.parse_wp(output, solver, case)
        found.append((case, expected, observed,
                       QUALIFY.judge(expected, observed, exercised),
                       f"{detail} seconds={seconds}"))
    return found


# ------------------------------------------------------------------ vacuity
def with_requires(files):
    """The functions whose imported contract has a requires clause."""
    found = set()
    for path in files:
        for name, block in re.findall(r"^function (\w+):\n((?:[ \t].*\n|\n)*)",
                                      path.read_text(encoding="utf-8"), re.M):
            if re.search(r"^\s+requires\b", block, re.M):
                found.add(name)
    return found


def null_tests(source=LIB.LEAF):
    """The lines of the leaf's tests of its pointers against null, each to
    its early return: what section 4.3's validity precondition (D_valid)
    makes unreachable."""
    lines = source.read_text(encoding="utf-8").splitlines()
    first = next(n for n, text in enumerate(lines, 1)
                 if text.startswith("int be_mvp_denial_decide("))
    last = next(n for n in range(first, len(lines) + 1)
                if lines[n - 1] == "}")
    found = set()
    for number in range(first, last + 1):
        if re.search(r"\b(out|state|map|leaves|record) == "
                     r"\((const )?struct \w+ \*\)0", lines[number - 1]):
            while number <= last:
                found.add(number)
                if "return 0;" in lines[number - 1]:
                    break
                number += 1
    return found


def smoke_check(function, smoke, requiring, expected, problems):
    """(ok, detail) of FUNCTION's smoke goals: its requires (when it has
    one) not doomed; no statement dead but, in the leaf, its five null
    tests (EXPECTED lines), which D_valid makes unreachable."""
    requires = [n for n in smoke if "_wp_smoke_default_requires" in n]
    doomed = [n for n in requires if state(smoke[n]) == "proved"]
    dead = sorted((n.split("_wp_smoke_", 1)[1], smoke[n]["line"])
                  for n in smoke if n not in requires and
                  state(smoke[n]) == "proved")
    excused = function == "be_mvp_denial_decide" and \
        len(dead) <= NULL_TESTS and all(line in expected for _, line in dead)
    ok = not problems and not doomed and \
        bool(requires) == (function in requiring) and (not dead or excused)
    return ok, (f"requires={'yes' if function in requiring else 'none'} "
                f"requires_smoke={len(requires)} doomed={len(doomed)} "
                f"dead={','.join(f'{n}@line{l}' for n, l in dead) or 'none'}"
                f"{' (the null tests D_valid excludes)' if dead and excused else ''}")


def vacuity(files, scratch, options, lemma_options, lemmas):
    """[(check, function, ok, detail)] on the final annotations."""
    found = []
    goals, _, problems = run(files, LIB.LEAF, scratch / "smoke", options,
                             lemma_options, lemmas, select=list(SMOKE),
                             lemma_run=False)
    requiring, expected = with_requires(files), null_tests()
    for function in LIB.FUNCTIONS:
        smoke = {n: g for n, g in goals.items()
                 if g["smoke"] and g["function"] == function}
        found.append(("smoke", function, *smoke_check(
            function, smoke, requiring, expected, problems)))
    for function in LIB.FUNCTIONS:
        for check, clause in (
                ("ensures-false", "ensures VACUITY_false: \\false;"),
                ("contradictory-requires", "requires VACUITY_contradiction: "
                 + CONTRADICTION[function] + ";")):
            directory = scratch / f"{check}-{function}"
            directory.mkdir(parents=True, exist_ok=True)
            extra_file = directory / "vacuity.acsl"
            extra_file.write_text(f"function {function}:\n  contract:\n"
                                  f"    {clause}\n", encoding="utf-8")
            if check == "ensures-false":
                goals, _, problems = run(
                    files + [extra_file], LIB.LEAF, directory, options,
                    lemma_options, lemmas, functions=(function,),
                    select=["-wp-prop=VACUITY_false"], lemma_run=False)
                goal = goals.get(f"{function}_ensures_VACUITY_false")
                ok = goal is not None and state(goal) != "proved" and \
                    not problems
                detail = (f"{goal['valid']}/{goal['obligations']} "
                          f"obligations proved" if goal else "no goal")
            else:
                goals, _, problems = run(
                    files + [extra_file], LIB.LEAF, directory, options,
                    lemma_options, lemmas, functions=(function,),
                    select=list(SMOKE), lemma_run=False)
                doomed = [n for n, g in goals.items() if g["smoke"] and
                          g["function"] == function and
                          "_wp_smoke_default_requires" in n and
                          state(g) == "proved"]
                ok, detail = bool(doomed) and not problems, \
                    f"doomed={','.join(doomed) or 'none'}"
            found.append((check, function, ok, detail))
    return found


# ------------------------------------------------------------------ mutants
def exclusions(function, opened):
    """The ACSL names of FUNCTION's OPENED properties that -wp-prop can
    leave out (a named ensures or assert; not an RTE guard)."""
    return sorted({name[len(function) + 1:].split("_", 1)[1]
                   for name in opened
                   if re.match(rf"{function}_(ensures|assert)_", name) and
                   not name.startswith(f"{function}_assert_rte_")})


def mutant_run(mutant, files, scratch, settings_, baseline):
    """The record line of one mutant: its function's goals under the
    final annotations (the other functions use its contract, not its
    body), those the unmutated leaf leaves open left out by name."""
    options, lemma_options, lemmas = settings_
    function = mutant["function"]
    mine = {n: g for n, g in baseline.items()
            if g["function"] == function and not g["smoke"]}
    opened = sorted(n for n, g in mine.items() if state(g) != "proved")
    exclude = exclusions(function, opened)
    goals, _, problems = run(files, mutant["path"], scratch / mutant["id"],
                             options, lemma_options, lemmas,
                             functions=(function,), exclude=exclude,
                             lemma_run=False)
    closed = {n for n, g in mine.items() if state(g) == "proved"}
    killed = sorted(f"{n}:{state(g)}" for n, g in goals.items()
                    if not g["smoke"] and state(g) != "proved" and
                    (n in closed or n not in baseline))
    if problems:
        killed.append("frama-c:" + ";".join(problems))
    return LIB.classify(mutant, killed, scratch / "oracle", opened)


# -------------------------------------------------------------- the record
TRANSCRIPTION = """\
section 4.1 -> mvp-sbi-leaf.acsl's logic: SPV, SPVP, GVA as BIT(h, 7), BIT(h, 8), BIT(h, 6) with BIT(v, n) = (v >> n) & 1; GPA(htval, stval) = (htval << 2) | (stval & 3); OPCODE(i) = (i >> 2) & 0x1f; HTINST_OK as written; INSIDE(a, base, n) = base <= a < base + n; IN_PAGE and HAS_PAGE (PAGE(gpa) exists) over pages 0 to 2 (the type's three); MAPPED as written, kept and not used by E7; PAGE as PAGE_IS(l, i, gpa), the lowest index i with p.bytes > 0 and INSIDE; W(pte) = BIT(pte, 2) == 1; PAGE_READ_ONLY (PAGE exists and lacks W); ACCESS_FAULT 1, 5, 7 for 20, 21, 23 and 0 elsewhere; VSTVEC_MODE(v) = v & 3
section 4.2 -> predicates E1 to E6; IN_WINDOW (the GPA inside the window); E7 = !IN_WINDOW && (UNMAPPED || READ_ONLY), UNMAPPED its unmapped case (!HAS_PAGE) and READ_ONLY its read-only case (cause 23 and PAGE_READ_ONLY); ENTRY (their conjunction); KIND as D_kind_unmapped (UNMAPPED implies kind 0) and D_kind_read_only (READ_ONLY implies kind 1)
section 4.3 -> be_mvp_denial_decide's requires: D_valid (\\valid_read of the four inputs, \\valid(out)), D_separated (\\separated of all five: "non-aliasing"), D_map_size (map->size > 0), D_map_nowrap and D_pages_nowrap (sums below 2^64); nothing else
section 4.4 Result -> D_result (0 or 1), D_E1 to D_E7 (1 only if each E holds), D_complete (ENTRY implies 1)
section 4.4 On 1 -> D_cause, D_kind_unmapped, D_kind_read_only, D_gpa, D_htval, D_htinst, D_stval, D_sepc, D_vsstatus, D_vstvec, D_time, D_inject_vscause, D_inject_vstval, D_inject_vsepc, D_inject_vsstatus_spp (bit 8 is SPVP(hstatus)), D_inject_vsstatus_spie (bit 5 is bit 1 of vsstatus), D_inject_vsstatus_sie (bit 1 is 0), D_inject_vsstatus_rest (every other bit: (x & ~0x122) == (vsstatus & ~0x122)), D_resume_pc (vstvec & ~3), each under \\result == 1, the inputs read at Pre (\\old)
section 4.4 On 0 -> D_zero_* for the fifteen fields, each under \\result == 0
section 4.4 Frame -> assigns *out; "reads no object but the four inputs" and "Determinism and purity" have no WP goal of their own: the postconditions fix the result and every field of *out as functions of the four inputs' values
section 4.4 Runtime errors -> -wp-rte with -warn-unsigned-overflow and -warn-unsigned-downcast: every access valid, every unsigned operation within range, no signed overflow
section 4.5 access_fault -> AF_cause (scause 20, 21, 23 give ACCESS_FAULT), AF_other (0 for every other cause), assigns \\nothing
section 4.5 htinst_accepted -> HI_iff (1 iff HTINST_OK), HI_bool (0 or 1), assigns \\nothing
section 4.5 inside -> requires IN_nowrap; IN_iff (1 iff INSIDE); IN_bool (0 or 1); assigns \\nothing
section 4.5 leaf_at -> requires LA_valid, LA_nowrap; LA_page (PAGE_IS(i), the lowest-index page holding gpa, implies \\result == &leaves->page[i]); LA_none (no page: \\result == \\null); assigns \\nothing; the loop (its at most three entries): LA_index, LA_before (no earlier page holds gpa), loop assigns index, loop variant 3 - index; LA_null and LA_found, the converse directions (a null result: no page holds gpa; a non-null one is &page[i] for PAGE_IS(i)), consequences of the clauses above for a valid array of three, each a goal
R1-1 -> E7 (IN_WINDOW first, then UNMAPPED or READ_ONLY as the cases), D_E7, D_complete, D_kind_unmapped, D_kind_read_only, D_place_here's !INSIDE (the GPA outside the entry's window at the call of leaf_at)
R1-2 -> requires D_map_size: map->size > 0
R1-3 -> AF_other, HI_bool, IN_bool (the first run's round 1 additions, section 4.5's clauses now); ACCESS_FAULT 0 elsewhere; LA_page by PAGE_IS's lowest index
R1-4 to R1-9 -> section 5 (Leaf B), not this arm's
round 0 -> the first run's annotations through its round 3 re-made against Revision 1, with its options (-wp-split; the lemmas' run with WP's bitwise tactics): the lemmas E3_MASK (the leaf's three-bit test of hstatus is E3), W_MASK ((pte & 4) == 0 is W negated), and HTVAL_SHIFT (htval << 2 stays below 2^64 under E4's bound), proved in the lemmas' own run; the assertions D_E3_here (at the call of htinst_accepted), D_gpa_here and D_window_here (at the call of inside: the GPA, map->gpa_base, and map->size are the entry's), and D_place_here (at the call of leaf_at: the GPA and the cause are the entry's, the GPA is outside the entry's window, and HAS_PAGE, PAGE_IS for each page, and PAGE_READ_ONLY are the same at the call as at entry), each a goal; the first run's three cases of D_complete are not restated (Revision 1's E7 and D_map_size exclude the first two; the third is D_complete itself)
round 1 -> for the true goals round 0 leaves open (the postconditions on the tail, whose accepting paths carry the fifteen stores to *out after the compound literal's copy, with record words read between them): the ladder D_reads_74, D_reads_78, D_reads_82, D_reads_87, D_reads_97, each saying the record's nine words the stores read (frame.scause, frame.htval, htinst, frame.stval, frame.sepc, vsstatus, frame.vstvec, time, hstatus) are their entry values, before the first store and after every few, each a goal, placed by the importer's statement number from its anchor (placements below); no lemma, no option beyond round 0's
D-5, Q8: the ACSL importer route; mvp-sbi-leaf.acsl and round-N.acsl are imported (-acsl-import) onto the unmodified mvp/src/mvp-sbi.c; the importer placed every annotation the leaf needs (the loop's at "at loop 1", the assertions at "at call" and, by statement number, at "at N"), so no annotated copy was needed"""


ASSUMPTIONS = """\
tools: Frama-C 33.0 (WP, RTE, ACSL importer), Why3 1.8.2, Alt-Ergo 2.4.3 (Fedora's alt-ergo-2.4.3-1.fc44, CeCILL-C), all from the verifier image (D-7 item 1)
machine model: -machdep gcc_x86_64 (LP64: long and pointers 8 bytes, int 4) for a RISC-V LP64 target; frama-c parsed the translation unit with every _Static_assert of its headers and of mvp-sbi.c holding under it (sizeof(struct be_mvp_exit) == 360, offsetof vsstatus 352, the be_types sizes); plain char is signed under gcc_x86_64 and unsigned on RISC-V: the five functions read no char object (struct be_mvp_state holds a char array, console.text, which they never read), so the difference does not reach them
preprocessing: gcc -E with the target's -I list (target-digests.txt include_dirs) and no define; mvp-sbi.c and its headers have no architecture conditional
memory model: WP's Typed model (typed pointers, no casts between pointer types in the leaf; its only casts are null-pointer constants)
integer model: mathematical integers in ACSL; C unsigned values as their u64 range with modulo semantics, every unsigned operation checked against the range by -warn-unsigned-overflow (section 4.4: no wrap)
axiomatics: none written; WP's own libraries (memory, integer, and bitwise theories, Qed's simplifications) are trusted; every lemma (E3_MASK, W_MASK, HTVAL_SHIFT) is a goal (goals.txt), proved in a run of their own; WP gives every lemma to the other goals as a hypothesis whether or not it is proved, so a goal's proof is conditional on the lemmas' (goals.txt lists each)
placement: the ACSL importer places an assertion before a call ("at call F"), in a loop ("at loop 1"), or before the function's statement N in its own numbering ("at N"); an "at N" block's statement is named by its `// anchor:` line and N is resolved from it for the leaf and for each mutant (a mutant's change of control flow renumbers the statements), the leaf's N as committed (transcription.txt's placements); an assertion is a goal wherever it is placed
solver trust: Alt-Ergo 2.4.3 alone (decision A), through Why3's driver for Alt-Ergo 2.4.x (why3.conf); WP's tactics (-wp-auto, for the lemmas' run) are WP's own code; D-7 item 7's pair (Z3 and cvc5) is not formed: WP with Z3 4.16.0 is unsound on WP's prelude and WP with cvc5 1.3.4 does not terminate (M8-5)
configuration finding: the image's Why3 configuration names Alt-Ergo with an empty version (Fedora's binary prints 2.4.3-free), so Why3 uses its Alt-Ergo 2.6 driver, whose polymorphic SMT-LIB Alt-Ergo 2.4.3 cannot parse; with it, 65 of round 0's 200 obligations ended in a syntax error (Failure). why3.conf names the version (2.4.3), so Why3 uses its 2.4.x driver; the qualification's five cases are re-run under it (vacuity.txt)
ownership premise: the four inputs and out are valid, pairwise separated objects (section 4.3), stated as requires, not checked by the tool at any caller
not covered: the callers (be_mvp_handle_exit, the vector, the injection helper, the DENIAL record, the resume); compiled execution (claim class (d)): the proof is of the C under Frama-C's semantics with gcc_x86_64, not of the RISC-V object code GCC or Clang emits; the reads half of the frame (no WP goal: the postconditions fix every output from the inputs' values); concurrency (the leaf reads only its own hart's private state)"""


def q17(scratch):
    """Q17: can WP print its goals for Rocq 9.3 through Why3's driver?"""
    environment = LIB.environment(WHY3CONFIG=str(WHY3))
    _, provers, _ = LIB.execute(["why3", "config", "list-provers"], 60,
                                REPO, environment)
    _, coq, _ = LIB.execute(["frama-c", "-wp", "-wp-prover", "coq",
                             "-wp-out", str(scratch / "q17-out"),
                             str(QUALIFY.QUALIFY / "wp" / "known-pass.c")],
                            120, REPO, environment)
    _, rocq, _ = LIB.execute(["rocq", "--version"], 60, REPO, environment)
    data = pathlib.Path("/usr/share/why3/provers-detection-data.conf")
    known = re.findall(r'^version_ok = "(.*)"$', data.read_text(
        encoding="utf-8").split("[ITP coq]", 1)[1].split("[", 1)[0],
        re.M) if data.is_file() else []
    unknown = "Unknown prover coq" in coq
    return [f"Q17 rocq={(rocq.strip().splitlines() or ['absent'])[0]}",
            f"Q17 why3_coq_versions_known={','.join(known) or 'none'} "
            f"(executable coqtop, banner 'The Coq Proof Assistant'; the "
            f"image has rocq and no coqtop)",
            f"Q17 why3_provers={'; '.join(provers.split()) or 'none'}",
            f"Q17 frama-c -wp-prover coq: "
            f"{'Unknown prover coq' if unknown else 'accepted'}",
            f"Q17 answer={'not-qualified' if unknown else 'check'}: Why3 "
            f"1.8.2 cannot target Rocq 9.3 in this image, so the link to "
            f"stage 1 stays a named and reviewed transcription (Q17's "
            f"default fallback)"]


def run_arm(out, jobs):
    out = LIB.prepare(out, MARKER)
    runs = out / "runs"
    started = time.monotonic()
    before = LIB.digests()
    files = round_files()
    final = settings(files)
    qualification = requalify(runs / "qualify", final[0]) + [
        (f"{case}+lemma-options", expected, observed, ok, detail) for
        case, expected, observed, ok, detail in requalify(
            runs / "qualify-lemma", final[0] + final[1])]
    rounds, results = [], []
    # One round at a time: a prover's limit is time, so a run beside
    # others on a loaded host would lose goals near it.
    ran = [run(files[:number + 1], LIB.LEAF, runs / f"round-{number}",
               *settings(files[:number + 1])) for number in range(len(files))]
    for number, (goals, seconds, problems) in enumerate(ran):
        options, lemma_options, _ = settings(files[:number + 1])
        total, proved, opened, obligations, valid = counts(goals)
        results.append(goals)
        rounds.append(
            f"round={number} files={','.join(p.name for p in files[:number + 1])}"
            f" options={' '.join(options) or '-'} lemma_options="
            f"{' '.join(lemma_options) or '-'} goals={total} proved={proved} "
            f"open={len(opened)} {tallies(goals)} obligations={obligations} "
            f"obligations_proved={valid} seconds={seconds}"
            f"{' problems=' + ';'.join(problems) if problems else ''}"
            f" open_goals={','.join(opened) or 'none'}")
        print(f"{TAG}: {rounds[-1]}", flush=True)
    final_goals = results[-1]
    total, proved, opened, _, _ = counts(final_goals)
    goal_lines = [
        f"goal {name} function={goal['function']} status={state(goal)} "
        f"obligations={goal['valid']}/{goal['obligations']} closed_by="
        f"{','.join(sorted(goal['provers'])) or 'none'}"
        for name, goal in sorted(final_goals.items()) if not goal["smoke"]]
    checks = vacuity(files, runs / "vacuity", *final)
    _, placed = place(files, LIB.LEAF, runs / "placement")
    found, generator = LIB.mutants(out / "mutants")
    with concurrent.futures.ThreadPoolExecutor(jobs) as pool:
        lines = list(pool.map(lambda m: mutant_run(
            m, files, runs / "mutants", final, final_goals), found))
    statuses = [status for status, _ in lines]
    killed, unobservable, findings, errors, masked, _ = LIB.tally(statuses)
    after = LIB.digests()
    q17_lines = q17(runs)
    vacuity_ok = all(ok for _, _, ok, _ in checks)
    qualified = all(row[3] for row in qualification)
    result = "CLOSED" if total and proved == total and before[0] and \
        after[0] and qualified else "OPEN"
    reasons = (["open-goals"] if proved < total else []) + (
        [] if before[0] and after[0] else ["digests"]) + (
        [] if qualified else ["not-qualified"])
    seconds = round(time.monotonic() - started)
    LIB.write(out / "rounds.txt", [LIB.HEADER, "# WP arm: one line per "
                                   "annotation round (D-7 item 5: at most "
                                   "four after round 0; 60 s per goal)",
                                   *rounds, f"rounds_used={len(files) - 1}"
                                   f" of at most {MAX_ROUNDS}",
                                   f"wall_seconds={seconds}"])
    LIB.write(out / "goals.txt", [LIB.HEADER, f"# WP arm, final round "
                                  f"{len(files) - 1}: every goal "
                                  f"(property; obligations with -wp-split "
                                  f"are its paths)", *goal_lines,
                                  f"goals={total} proved={proved} "
                                  f"open={len(opened)}"])
    LIB.write(out / "assumptions.txt", [LIB.HEADER, "# WP arm's assumption "
                                        "inventory (D-7 item 4)",
                                        *ASSUMPTIONS.splitlines(), *q17_lines])
    LIB.write(out / "mutants.txt", [
        LIB.HEADER, f"# WP arm: {generator}", "# killed-by names the goals "
        "of the mutant's function the unmutated leaf closes and the mutant "
        "does not, each with how it ended (Alt-Ergo gives no "
        "counterexample: a goal it cannot prove ends in a timeout, so a "
        "kill is a goal not proved, and host_test= says whether the test "
        "sees the change); a goal the unmutated leaf leaves open cannot "
        "kill and is not run (masked-by-open names them when the host "
        "test fails)",
        *[line for _, line in lines],
        f"mutants={len(lines)} killed={killed} unobservable={unobservable} "
        f"contract_findings={findings} compile_errors={errors} "
        f"masked={masked}"])
    LIB.write(out / "vacuity.txt", [
        LIB.HEADER, "# WP arm: the qualification's five cases under this "
        "arm's configuration, then the vacuity checks on the final "
        "annotations (D-7 items 2 and 6): per function, WP's smoke tests "
        "(the requires, when there is one, not doomed; no statement "
        "proved unreachable but, in the leaf, its null tests of the five "
        "pointers, which section 4.3's D_valid excludes), ensures \\false "
        "not proved, and a contradictory requires doomed; a statement the "
        "smoke tests prove unreachable in the leaf at mvp-sbi.c line 318 "
        "is the SPVP ? SPP : 0 arm Revision 1 records as a true "
        "observation of the code, not an erratum (E3 refuses SPVP = 1), and "
        "is not excused",
        *[f"qualify case={case} expected={expected} observed={observed} "
          f"ok={'yes' if ok else 'no'} {LIB.relative(detail)}"
          for case, expected, observed, ok, detail in qualification],
        *[f"vacuity check={check} function={function} "
          f"ok={'yes' if ok else 'no'} {detail}"
          for check, function, ok, detail in checks],
        f"qualified={'yes' if qualified else 'no'}",
        f"vacuity={'ok' if vacuity_ok else 'not-ok'}"])
    LIB.write(out / "transcription.txt", [
        LIB.HEADER, "# WP arm: how each section 4 clause is transcribed "
        "(mvp/verify/wp/mvp-sbi-leaf.acsl and round-N.acsl)",
        *TRANSCRIPTION.splitlines(),
        *[f"placement {name} at {found}: {where} {text}"
          for name, _, found, where, text in placed],
        *[f"file {path.relative_to(REPO)} sha256="
          f"{LIB.sha256(path.read_bytes())}" for path in files + [WHY3]],
        f"digests_before={before[1]}", f"digests_after={after[1]}"])
    print(f"{TAG}_DETAIL: reasons={','.join(reasons) or 'none'} "
          f"qualified={'yes' if qualified else 'no'} masked={masked} "
          f"compile_errors={errors}"
          f" digests={'ok' if before[0] and after[0] else 'differ'} "
          f"wall_seconds={seconds}")
    print(f"{TAG}: {result} goals={total} proved={proved} "
          f"rounds={len(files) - 1} solvers=alt-ergo mutants={len(lines)} "
          f"killed={killed} unobservable={unobservable} "
          f"contract-findings={findings} "
          f"vacuity={'ok' if vacuity_ok else 'not-ok'} pair=not-formed")
    return 0


# ---------------------------------------------------------------- self-test
REPORT = json.dumps([
    {"goal": "typed_f_ensures_A_part1", "property": "f_ensures_A",
     "function": "f", "smoke": False, "verdict": "valid",
     "provers": [{"prover": "qed", "success": 1}]},
    {"goal": "typed_f_ensures_A_part2", "property": "f_ensures_A",
     "function": "f", "smoke": False, "verdict": "timeout",
     "provers": [{"prover": "Alt-Ergo:2.4.3", "success": 0}]},
    {"goal": "typed_f_ensures_B", "property": "f_ensures_B",
     "function": "f", "smoke": False, "verdict": "valid",
     "provers": [{"prover": "Alt-Ergo:2.4.3", "success": 1}]},
    {"goal": "typed_lemma_L", "property": "lemma_L", "smoke": False,
     "verdict": "valid", "provers": [{"prover": "qed", "success": 3}],
     "tactics": 6},
    {"goal": "typed_f_wp_smoke_default_requires",
     "property": "f_wp_smoke_default_requires", "function": "f",
     "smoke": True, "verdict": "unknown", "provers": []}])


def self_test():
    results = []

    def case(name, passed, detail=""):
        results.append(bool(passed))
        print(f"{'ok  ' if passed else 'FAIL'} {name}"
              f"{'' if passed else ': ' + str(detail)[-600:]}")

    goals = parse(REPORT)
    case("a property is proved only with every obligation",
         state(goals["f_ensures_A"]) == "timeout" and
         state(goals["f_ensures_B"]) == "proved", goals)
    case("provers and scripts are named", goals["f_ensures_B"]["provers"]
         == {"Alt-Ergo 2.4.3"} and goals["lemma_L"]["provers"] ==
         {"Qed", "Script"}, goals)
    case("smoke goals are not counted", counts(goals)[:3] ==
         (3, 2, ["f_ensures_A"]), counts(goals))
    case("a round's tallies by closer and by ending", tallies(goals) ==
         "closed_by_qed=0 closed_by_alt_ergo=1 closed_by_script=1 "
         "timeout=1", tallies(goals))
    base = REPO / "build" / "mvp" / "tmp"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=base) as scratch:
        directory = pathlib.Path(scratch)
        (directory / "mvp-sbi-leaf.acsl").write_text("// round 0\n")
        (directory / "round-1.acsl").write_text("// wp-options: -wp-split\n")
        (directory / "round-2.acsl").write_text(
            "lemma X: \\true;\n// wp-lemma-options: -wp-auto=wp:split\n")
        files = round_files(directory)
        case("rounds are 0 to N in order", [p.name for p in files] ==
             ["mvp-sbi-leaf.acsl", "round-1.acsl", "round-2.acsl"], files)
        case("a round's options are the last named", settings(files[:2]) ==
             (["-wp-split"], [], False) and settings(files) ==
             (["-wp-split"], ["-wp-auto=wp:split"], True), settings(files))
        (directory / "round-4.acsl").write_text("\n")
        try:
            round_files(directory)
            case("a gap in the rounds is refused", False)
        except Refusal as why:
            case("a gap in the rounds is refused", "1 to N" in str(why))
        for n in (3, 5):
            (directory / f"round-{n}.acsl").write_text("\n")
        try:
            round_files(directory)
            case("a fifth round is refused", False)
        except Refusal as why:
            case("a fifth round is refused", "allows four" in str(why))
        for word in ("-wp-prover=z3", "-wp-auto=wp:split,wp:admit",
                     "-wp-timeout", "-wp-model=Hoare"):
            try:
                checked_options([word], "x")
                case(f"option {word} is refused", False)
            except Refusal:
                case(f"option {word} is refused", True)
        made = commands(files, REPO / "mvp/src/mvp-sbi.c", directory,
                        ["-wp-split"], ["-wp-auto=wp:split"], True,
                        exclude=("D_E3",))
        main = " ".join(made["main"])
        case("the main run excludes the lemmas and open names, proves the "
             "five functions with RTE and the overflow warnings",
             "-wp-prop=-@lemma,-D_E3" in main and "-wp-rte" in main and
             "-warn-unsigned-overflow" in main and "-machdep gcc_x86_64" in
             main and "-wp-timeout 60" in main and "-wp-fct=access_fault,"
             "htinst_accepted,inside,leaf_at,be_mvp_denial_decide" in main,
             main)
        case("the lemmas run alone with their options", "-wp-prop=@lemma"
             in made["lemma"] and "-wp-auto=wp:split" in made["lemma"] and
             "-wp-rte" not in made["lemma"], made["lemma"])
    case("a mutant's run leaves out its function's open names, not RTE",
         exclusions("be_mvp_denial_decide", [
             "be_mvp_denial_decide_ensures_D_E7",
             "be_mvp_denial_decide_assert_D_E3_here",
             "be_mvp_denial_decide_assert_rte_unsigned_overflow"]) ==
         ["D_E3_here", "D_E7"])
    case("the committed rounds load", len(round_files()) <= MAX_ROUNDS + 1)
    printed = (
        "int be_mvp_denial_decide(struct be_mvp_state const *state,\n"
        "                         struct be_mvp_denial *out);\n"
        "int be_mvp_denial_decide(struct be_mvp_state const *state,\n"
        "                         struct be_mvp_denial *out)\n{\n"
        "  /*@ assert ANCHOR_PROBE_1: \\true; */\n  x = 1;\n"
        "  /*@ assert ANCHOR_PROBE_2: \\true; */\n"
        "  /*@ assert ANCHOR_PROBE_3: \\true; */\n"
        "  if (x) out->a = 1;\n"
        "  /*@ assert ANCHOR_PROBE_4: \\true; */\n  out->b = 2;\n"
        "  return_label: /*@ assert ANCHOR_PROBE_5: \\true; */\n"
        "  return __retres;\n}\n")
    number_of = numbering(printed)
    case("the probe's print gives each number its statement, the "
         "definition's not the declaration's", number_of == {
             1: "x = 1;", 2: "if (x) out->a = 1;", 3: "if (x) out->a = 1;",
             4: "out->b = 2;", 5: "return __retres;"}, number_of)
    case("an anchor before a statement is its number, after it the next",
         resolved(number_of, ("before", "out->b = 2;")) == 4 and
         resolved(number_of, ("after", "x = 1;")) == 2)
    try:
        resolved(number_of, ("before", "if (x) out->a = 1;"))
        case("an anchor two statements share is refused", False)
    except Refusal:
        case("an anchor two statements share is refused", True)
    with tempfile.TemporaryDirectory(dir=base) as scratch:
        sample = pathlib.Path(scratch) / "round-9.acsl"
        sample.write_text("function f:\n  // anchor: after out->b = 2;\n"
                          "  at 4:\n    assert A: \\true;\n  at call g:\n"
                          "    assert B: \\true;\n")
        case("an `at N:` block's anchor is read",
             anchors(sample) == [(2, 4, "after", "out->b = 2;")],
             anchors(sample))
        sample.write_text("function f:\n  at 4:\n    assert A: \\true;\n")
        try:
            anchors(sample)
            case("an `at N:` block with no anchor is refused", False)
        except Refusal as why:
            case("an `at N:` block with no anchor is refused",
                 "no `// anchor:`" in str(why))
    case("the committed rounds' `at N:` blocks are anchored", all(
        isinstance(anchors(path), list) for path in round_files()))
    with tempfile.TemporaryDirectory(dir=base) as scratch:
        sample = pathlib.Path(scratch) / "sample.acsl"
        sample.write_text("lemma L: \\true;\nfunction f:\n  contract:\n"
                          "    ensures A: \\true;\n\nfunction g:\n  "
                          "contract:\n    requires R: x > 0;\n// note\n"
                          "function h:\n  contract:\n    assigns \\nothing;\n")
        case("the functions with a requires are found",
             with_requires([sample]) == {"g"}, with_requires([sample]))
    lines = null_tests()
    source = LIB.LEAF.read_text(encoding="utf-8").splitlines()
    case("the leaf's null tests run to their early returns", lines and all(
        "*)0" in source[n - 1] or "return 0;" in source[n - 1] or
        "accept_denial" in source[n - 1] for n in lines) and
        sum("return 0;" in source[n - 1] for n in lines) == 2 and
        not any("return (const" in source[n - 1] for n in lines), lines)

    def smoke(*entries):
        return {f"{f}_wp_smoke_{k}": {
            "function": f, "obligations": 1, "valid": int(v == "valid"),
            "verdicts": collections.Counter([v]), "provers": set(),
            "smoke": True, "line": line} for f, k, v, line in entries}

    leaf, null = "be_mvp_denial_decide", min(lines)
    for name, function, goals, requiring, wanted in (
            ("a function with no requires and no requires smoke goal",
             "f", smoke(("f", "dead_code_s1", "timeout", 3)), set(), True),
            ("a requires with no smoke goal", "f", smoke(), {"f"}, False),
            ("a doomed requires", "f", smoke(
                ("f", "default_requires", "valid", 2)), {"f"}, False),
            ("a helper's dead statement", "f", smoke(
                ("f", "default_requires", "timeout", 2),
                ("f", "dead_code_s4", "valid", 5)), {"f"}, False),
            ("the leaf's null tests dead under D_valid", leaf, smoke(
                (leaf, "default_requires", "timeout", 1),
                *[(leaf, f"dead_code_s{n}", "valid", null) for n in
                  range(5)]), {leaf}, True),
            ("a sixth dead statement in the leaf", leaf, smoke(
                (leaf, "default_requires", "timeout", 1),
                *[(leaf, f"dead_code_s{n}", "valid", null) for n in
                  range(6)]), {leaf}, False),
            ("a dead statement elsewhere in the leaf", leaf, smoke(
                (leaf, "default_requires", "timeout", 1),
                (leaf, "dead_code_s9", "valid", max(lines) + 1)), {leaf},
             False)):
        ok, detail = smoke_check(function, goals, requiring, lines, [])
        case(f"smoke: {name}", ok == wanted, detail)
    print(f"{TAG}_SELF_TEST: {'PASS' if all(results) else 'FAIL'} "
          f"cases={len(results)}"
          f"{'' if all(results) else f' failed={results.count(False)}'}")
    return 0 if all(results) else 1


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=pathlib.Path,
                        default=REPO / "build" / "mvp" / "verify" / "wp")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--retain", type=pathlib.Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv[1:])
    if sum((args.run, args.self_test, args.retain is not None)) != 1 or \
            args.jobs < 1:
        parser.error("give --run [--out DIR] [--jobs N], --retain DIR, or "
                     "--self-test")
    if args.self_test:
        return self_test()
    try:
        if args.retain:
            names = LIB.retain(args.out.resolve(), args.retain.resolve())
            print(f"{TAG}: RETAINED {len(names)} records in "
                  f"{LIB.relative(args.retain.resolve())}")
            return 0
        return run_arm(args.out.resolve(), args.jobs)
    except (OSError, Refusal, LIB.Refusal, ValueError, KeyError) as why:
        print(f"{TAG}: FAIL {why}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
