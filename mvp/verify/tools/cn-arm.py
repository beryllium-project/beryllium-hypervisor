#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""
cn-arm.py --run [--out DIR] [--jobs N]
cn-arm.py --retain DIR [--out DIR]
cn-arm.py --self-test

Purpose: the pilot's CN arm on Leaf A (planning/mvp-m8-plan.md, D-4, D-5,
D-7, M8-6; the arm that can give a positive result under decision A;
specification sections 4 and 6 as its Revision 1 states them, SHA-256
aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b,
accepted 2026-11-03 at 93a8d136; the first run judged against the
accepted text of 004f31ae, ade32fa6...). It proves the annotated copy
mvp/verify/cn/mvp-sbi-leaf.c after the token gate shows its code is
mvp/src/mvp-sbi.c's five functions. A clause tagged `goal NAME` is one
goal: each runs alone (the function's other goals left out, its requires,
ownership, and the other functions' contracts kept) under `cn verify
--only=FUNCTION`, once with --solver-type=z3 and once with cvc5, each run
limited to 60 s by the process's timeout (CN has no per-query timeout);
a goal is closed when at least one solver passes and neither fails. A
clause tagged `rN` belongs to annotation round N; round k's copy keeps the
clauses of rounds 0 to k. CN's front end needs four preprocessor
settings, recorded as assumptions: GCC's __builtin_offsetof as C11's
offsetof (<stddef.h>), __attribute__ erased (the ring index's alignment,
outside the leaf's types), and the parameter `map`, a CN keyword, renamed
be_cn_map throughout. In order: the digests (D-7 item 3); the token gate;
the CN qualification cases re-run with these settings (item 2); every
round (item 5); the vacuity checks on the final copy (item 6: an
assert(false) at each function's entry must fail; with a contradictory
requires it must pass; an `ensures false` must fail); the 24 seeded
mutants, each carried into the copy by token position, each function's
goals re-run for its own mutants (the other functions use its contract,
not its body); the digests again. A goal CN does not close is recorded
with CN's reason; CN gives no counterexample, and a clause that fails on
the leaf is CBMC's arm's to show (cbmc-leaf-a.py's defect.txt).
Outputs: in DIR (default build/mvp/verify/cn): the six records and every
run under runs/; last the line
`BE_MVP_CN_ARM: CLOSED|OPEN goals=N proved=M rounds=R solvers=z3,cvc5
mutants=K killed=A unobservable=B contract-findings=C vacuity=ok|not-ok
pair=formed|not-formed`. A mutant whose function has no goal closed is
recorded not-checked (the arm has no goal to kill it with) and counted
apart.
Exit status: 0 the run completed and is recorded; 1 the runner failed; 2
usage.
"""

import argparse
import collections
import concurrent.futures
import importlib.util
import pathlib
import re
import sys
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
TAG = "BE_MVP_CN_ARM"
COPY = REPO / "mvp" / "verify" / "cn" / "mvp-sbi-leaf.c"
MARKER = ".cn-arm-run"
SOLVERS = ("z3", "cvc5")
FRONT_END = ("-D__builtin_offsetof(t,m)=offsetof(t,m)", "--include=stddef.h",
             "-D__attribute__(x)=", "-Dmap=be_cn_map")
PREFIX = {"AF": "access_fault", "HI": "htinst_accepted", "IN": "inside",
          "LA": "leaf_at", "D": "be_mvp_denial_decide"}
CLAUSE = re.compile(r"//\s*(?:goal\s+([A-Za-z0-9_]+))?\s*(?:\br([1-9])\b)?"
                    r"\s*$")
CONTRADICTION = {
    "access_fault": "scause < 20 && scause > 23",
    "htinst_accepted": "htinst < 1 && htinst > 1",
    "inside": "bytes < 1 && bytes > 1",
    "leaf_at": "gpa < 1 && gpa > 1",
    "be_mvp_denial_decide": "is_null(state) && !is_null(state)"}
MAX_ROUNDS = 4


class Refusal(Exception):
    """A copy whose tags or functions this runner cannot read."""


# --------------------------------------------------------------- the copy
def clauses(lines):
    """[(first, last, goal or None, round)] of the tagged clauses: a tag
    comment on a clause's first line, the clause running to the first line
    whose code ends with ';'."""
    found, index = [], 0
    while index < len(lines):
        code, sep, comment = lines[index].partition("//")
        match = CLAUSE.fullmatch("//" + comment) if sep else None
        if match and (match[1] or match[2]):
            last = index
            while not lines[last].partition("//")[0].rstrip().endswith(";"):
                last += 1
                if last == len(lines):
                    raise Refusal(f"line {index + 1}: a clause with no ';'")
            found.append((index, last, match[1], int(match[2] or 0)))
            index = last + 1
        else:
            index += 1
    return found


def goals_of(lines, round_number):
    """{goal: function} of the copy's round."""
    found = {}
    for _, _, goal, number in clauses(lines):
        if goal and number <= round_number:
            if goal.split("_")[0] not in PREFIX or goal in found:
                raise Refusal(f"goal {goal} has no function or repeats")
            found[goal] = PREFIX[goal.split("_")[0]]
    return found


def variant(lines, round_number, goal=None, function=None):
    """The copy's text for ROUND_NUMBER, with GOAL's function's other
    goals left out when GOAL is given, or every goal of FUNCTION."""
    drop = set()
    if goal:
        function = PREFIX[goal.split("_")[0]]
    for first, last, name, number in clauses(lines):
        if number > round_number or (
                function and name and name != goal and
                PREFIX[name.split("_")[0]] == function):
            drop |= set(range(first, last + 1))
    return "\n".join(line for i, line in enumerate(lines)
                     if i not in drop) + "\n"


def rounds_in(lines):
    numbers = sorted({number for *_, number in clauses(lines)} | {0})
    if numbers != list(range(len(numbers))) or numbers[-1] > MAX_ROUNDS:
        raise Refusal(f"rounds {numbers} are not 0 to N with N at most 4")
    return numbers[-1]


def declarator(lines, function):
    """(the index of FUNCTION's declarator line, of its body's brace)."""
    for index, line in enumerate(lines):
        if re.match(rf"^(?:[a-z_ ]+\b)?\*?{function}\(", line) or \
                re.match(rf"^static [a-z_0-9 *]*\b{function}\(", line):
            for later in range(index, len(lines)):
                if lines[later] == "{":
                    return index, later
    raise Refusal(f"no body of {function}")


def entry_line(lines, function):
    """The index of FUNCTION's body's opening brace."""
    return declarator(lines, function)[1]


def with_check(text, function, check):
    """TEXT with a vacuity check on FUNCTION."""
    lines = text.split("\n")
    brace = entry_line(lines, function)
    if check in ("reach", "contradiction"):
        lines.insert(brace + 1, "\t/*@ assert(false); @*/")
    if check == "contradiction":
        spec = next(i for i in range(brace, -1, -1)
                    if lines[i].startswith("/*@ "))
        lines[spec] = lines[spec].replace(
            "/*@ requires ", f"/*@ requires {CONTRADICTION[function]};\n"
            "             ", 1) if "/*@ requires " in lines[spec] else \
            lines[spec].replace("/*@ ", f"/*@ requires "
                                f"{CONTRADICTION[function]};\n    ", 1)
    if check == "ensures-false":
        end = next(i for i in range(brace, -1, -1) if lines[i] == "@*/")
        lines.insert(end, "            false; // goal VACUITY_false")
    return "\n".join(lines)


# ---------------------------------------------------------------- running
def cn(path, function, solver):
    """(verdict, reason, seconds) of one cn verify run: verdict pass,
    fail, timeout, or error."""
    command = ["cn", "verify", f"--solver-type={solver}",
               *[f"-I{d}" for d in LIB.target_flags()["include_dirs"]],
               *FRONT_END, f"--only={function}", str(path)]
    status, output, seconds = LIB.execute(command, LIB.GOAL_SECONDS, REPO,
                                          LIB.environment(
                                              TMPDIR=str(path.parent)))
    path.with_suffix(f".{solver}.log").write_text(
        " ".join(command) + f"\nstatus={status} seconds={seconds}\n" +
        output, encoding="utf-8")
    if status == "timeout":
        return "timeout", "killed after 60 s", seconds
    verdict = re.search(rf"^\[\d+/\d+\]: {function} -- (pass|fail)$",
                        output, re.M)
    if not verdict:
        line = next((l for l in output.splitlines() if "error" in l),
                    "no verdict line")
        return "error", LIB.relative(line.strip())[:160], seconds
    if verdict[1] == "pass":
        return "pass", "", seconds
    for pattern, reason in (
            (r"Unprovable constraint", "unprovable-constraint"),
            (r"Left-over unused resource '([^']*)'", "left-over-resource"),
            (r"Missing resource for reading", "missing-resource"),
            (r"needs to be live", "pointer-liveness"),
            (r"needs allocation ID", "allocation-id")):
        match = re.search(pattern, output)
        if match:
            return "fail", reason, seconds
    return "fail", "other", seconds


def judge(results):
    """A goal's state from its solvers' verdicts: closed when one passes
    and none fails."""
    verdicts = [verdict for verdict, _, _ in results.values()]
    if "pass" in verdicts and "fail" not in verdicts:
        return "closed"
    if "pass" in verdicts:
        return "disagree"
    return "open"


def vacuity_ok(result, wanted):
    """A vacuity check holds when a solver gives the WANTED verdict (a
    fail on the check's own constraint) and none the other."""
    seen = [(v, why) for v, why, _ in result.values()]
    hit = [(v, why) for v, why in seen if v == wanted and
           (wanted == "pass" or why == "unprovable-constraint")]
    other = "fail" if wanted == "pass" else "pass"
    return bool(hit) and all(v != other for v, _ in seen)


def run_goal(text, function, goal, directory):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{goal}.c"
    path.write_text(text, encoding="latin-1")
    return {solver: cn(path, function, solver) for solver in SOLVERS}


def run_round(lines, number, directory, jobs, only=None):
    """{goal: (function, state, {solver: (verdict, reason, seconds)})}."""
    goals = goals_of(lines, number)
    chosen = [g for g in goals if only is None or g in only]
    with concurrent.futures.ThreadPoolExecutor(jobs) as pool:
        done = dict(zip(chosen, pool.map(lambda g: run_goal(
            variant(lines, number, g), goals[g], g, directory), chosen)))
    return {g: (goals[g], judge(r), r) for g, r in done.items()}


# ---------------------------------------------------------------- records
TRANSCRIPTION = """\
section 4.1 -> the copy's CN functions: BIT(v, n) = shift_right(v, n) & 1, SPV, SPVP, GVA as bits 7, 8, 6; GPA = shift_left(htval, 2) | (stval & 3); OPCODE = shift_right(i, 2) & 31; HTINST_OK as written; INSIDE; IN_PAGE and HAS_PAGE (PAGE(gpa) exists) over pages 0 to 2; MAPPED as written, kept and not used by E7; PAGE_IS (the lowest index); W_SET(pte) = BIT(pte, 2) == 1 (CN reserves W, its write-ownership resource); PAGE_READ_ONLY; ACCESS_FAULT (1, 5, 7, else 0); VSTVEC_MODE = v & 3
section 4.2 -> E1 to E6; IN_WINDOW; E7 = !IN_WINDOW && (UNMAPPED || READ_ONLY), UNMAPPED E7's unmapped case (!HAS_PAGE) and READ_ONLY its read-only case (cause 23 and PAGE_READ_ONLY); ENTRY; over the struct values CN's ownership gives (S, M, L, R)
section 4.3 -> be_mvp_denial_decide's requires: take RW of each input (CN's ownership: valid, initialised, pairwise disjoint by the separating conjunction), take W of out (valid, writable, disjoint from the inputs), M.size > 0, the map's and each page's sum below 2^64; nothing else
section 4.4 -> the same goals as the WP arm, by the same names: D_frame (every input unchanged: S2 == S and the others, CN's form of "writes *out and nothing else" for the inputs; ownership of out returned as RW), D_result, D_E1 to D_E7, D_complete, D_cause, D_kind_unmapped (UNMAPPED implies kind 0), D_kind_read_only (READ_ONLY implies kind 1), the eleven field goals, D_inject_vsstatus_spp, _spie, _sie, _rest, D_resume_pc, D_zero_* (fifteen)
section 4.4 Runtime errors -> CN's own checks on every run: undefined behaviour, ownership of every access, and representability of every C integer value (CN's integer mode: C integers as mathematical integers with range constraints)
section 4.5 -> access_fault: AF_cause, AF_other (0 for every other cause); htinst_accepted: HI_iff, HI_bool (0 or 1); inside: requires the sum below 2^64, IN_iff, IN_bool (0 or 1); leaf_at: take RW of leaves returned unchanged (LA_frame), LA_page_0 to LA_page_2 (PAGE_IS(i), the lowest-index page holding gpa, implies ptr_eq(return, &leaves->page[i])), LA_none, and the loop's inv (ownership, index <= 3, no earlier page holds gpa)
R1-1 -> E7 (IN_WINDOW first, then UNMAPPED or READ_ONLY as the cases), D_E7, D_complete, D_kind_unmapped, D_kind_read_only
R1-2 -> the requires M.size > 0
R1-3 -> AF_other, HI_bool, IN_bool (the first run's round 1 additions, section 4.5's clauses now, in round 0); ACCESS_FAULT 0 elsewhere; LA_page_0 to LA_page_2 by PAGE_IS's lowest index
R1-4 to R1-9 -> section 5 (Leaf B), not this arm's
round 0 -> the first run's copy through its round 1, re-made against Revision 1: its round 1's three cases of D_complete are not restated (Revision 1's E7 and D_map_size exclude the first two; the third is D_complete itself); no later round (the tool limits below stand)
D-5: the annotated-copy route, as the plan requires for CN; the copy passes the token gate"""


ASSUMPTIONS = """\
tools: CN at rems-project/cn cbe879c7 with Cerberus 68bdc84b, built in the verifier image (sources.txt pins); Z3 4.16.0 and cvc5 1.3.4 from the image (D-7 item 1)
machine model: Cerberus's implementation for CN (LP64: long and pointers 8 bytes); the five functions read no char object
preprocessing: the target's -I list and four settings CN's front end needs, none in the five functions' own tokens but the renaming: -D__builtin_offsetof(t,m)=offsetof(t,m) with --include=stddef.h (GCC's builtin in the headers' _Static_asserts, which Cerberus then evaluates with C11's offsetof), -D__attribute__(x)= (the one GNU attribute in the translation unit's headers aligns struct be_mvp_ring_index, a type the leaf does not use), -Dmap=be_cn_map (CN reserves map, a keyword of its specification language; renaming the identifier everywhere, the leaf's parameter and the headers' prototype parameters, is an alpha-renaming)
integer model: CN at this commit runs in integer mode (BaseTypes.cnBV is false and its switch is commented out): C integers are mathematical integers with range constraints; &, |, and ^ on them are uninterpreted functions in the SMT problem, so a goal that needs what a bitwise operation computes cannot close; one whose bitwise terms match the code's term for term can
memory model: CN's separation logic (ownership by RW and W, VIP pointer provenance)
axiomatics: none; no lemma, no trusted function in the copy
solver trust: Z3 4.16.0 and cvc5 1.3.4, both on every goal (D-7 item 7's pair); a goal is closed when one passes and neither fails
time limit: 60 s per goal and solver, as a limit on the cn process (killed at 60 s, recorded as a timeout): CN at this commit has no per-goal or per-query limit (its --incremental-solver-timeout only hands a slow incremental query to a non-incremental solver)
ownership premise: section 4.3 as CN ownership; not checked at any caller
tool findings: (1) a compound literal's temporary object is never released: `*out = (struct be_mvp_denial){ 0 }` leaves its fields owned at every return ('Left-over unused resource'), which no annotation can release (a toy with the same statement fails and its named-local twin passes); (2) leaf_at's goals fail first on CN's liveness check of &leaves->page[index], which looks for an Owned or Alloc resource of the allocation and skips iterated ones; with Alloc(leaves) added to the contract (a development run) that check passes and the read of leaves->page[index] at a symbolic index then needs a `focus` ghost statement in the loop's body (CN at this commit satisfies a single-object request only from a single-object resource), and that body is one if-statement without braces: a ghost statement there would become the loop's body, and braces would change the token stream; (3) bitwise operators are uninterpreted (above)
not covered: the callers; compiled execution (claim class (d)); concurrency"""


def run_arm(out, jobs):
    out = LIB.prepare(out, MARKER)
    runs = out / "runs"
    started = time.monotonic()
    before = LIB.digests()
    gate_ok, gate = LIB.LEXER.compare(COPY, LIB.LEAF, LIB.FUNCTIONS)
    lines = COPY.read_text(encoding="latin-1").split("\n")
    final_round = rounds_in(lines)
    rows = [row for row in QUALIFY.load(QUALIFY.EXPECTATIONS.read_text(
        encoding="utf-8")) if row[0] == "cn"]
    qualification = []
    for _, solver, case, path, expected in rows:
        status, output, seconds = LIB.execute(
            ["cn", "verify", f"--solver-type={solver}", *FRONT_END,
             str(path)], LIB.GOAL_SECONDS, REPO, LIB.environment())
        observed, detail, exercised = ("error", f"exit {status}", None) if \
            status == "timeout" else QUALIFY.parse_cn(output, case)
        qualification.append((solver, case, expected, observed,
                              QUALIFY.judge(expected, observed, exercised),
                              f"{detail} seconds={seconds}"))
    rounds, results = [], {}
    for number in range(final_round + 1):
        begun = time.monotonic()
        results[number] = run_round(lines, number, runs / f"round-{number}",
                                    jobs)
        closed = sorted(g for g, (_, s, _) in results[number].items()
                        if s == "closed")
        opened = sorted(set(results[number]) - set(closed))
        verdicts = collections.Counter(
            f"{solver}_{verdict}" for _, _, r in results[number].values()
            for solver, (verdict, _, _) in r.items())
        rounds.append(f"round={number} goals={len(results[number])} "
                      f"proved={len(closed)} open={len(opened)} " +
                      " ".join(f"{k}={v}" for k, v in sorted(
                          verdicts.items())) +
                      f" seconds={round(time.monotonic() - begun)} "
                      f"open_goals={','.join(opened) or 'none'}")
        print(f"{TAG}: {rounds[-1]}", flush=True)
    final = results[final_round]
    closed = {g for g, (_, s, _) in final.items() if s == "closed"}
    goal_lines = [
        f"goal {g} function={f} status={s} " + " ".join(
            f"{solver}={v}{'(' + why + ')' if why else ''}"
            for solver, (v, why, _) in r.items())
        for g, (f, s, r) in sorted(final.items())]
    pair = all(len(r) == len(SOLVERS) and all(
        v in ("pass", "fail") for v, _, _ in r.values())
        for _, _, r in final.values())
    checks = []
    for function in LIB.FUNCTIONS:
        text = variant(lines, final_round, function=function)
        for check, wanted in (("reach", "fail"), ("contradiction", "pass"),
                              ("ensures-false", "fail")):
            directory = runs / "vacuity" / f"{check}-{function}"
            result = run_goal(with_check(text, function, check), function,
                              "check", directory)
            verdicts = {s: v for s, (v, _, _) in result.items()}
            checks.append((check, function, vacuity_ok(result, wanted),
                           " ".join(
                f"{s}={v}{'(' + result[s][1] + ')' if result[s][1] else ''}"
                for s, v in verdicts.items()) + f" wanted={wanted}"))
    found, generator = LIB.mutants(out / "mutants")

    def mutant_line(mutant):
        function = mutant["function"]
        mine = [g for g, (f, _, _) in final.items() if f == function and
                g in closed]
        masked = sorted(g for g, (f, _, _) in final.items() if f == function
                        and g not in closed)
        if not mine:
            verdict, werror, detail = LIB.oracle(
                mutant["path"], runs / "oracle" / mutant["id"])
            status = "not-checked"
            return status, (f"{mutant['id']} {LIB.change(mutant)} status="
                            f"{status} (the arm closes no goal of {function})"
                            f" host_test={verdict} werror={werror} "
                            f"{LIB.relative(detail)}")
        directory = runs / "mutants" / mutant["id"]
        copy = LIB.copy_mutant(COPY.read_text(encoding="latin-1"), mutant,
                               directory)
        mutated = copy.read_text(encoding="latin-1").split("\n")
        killed = []
        for goal in mine:
            result = run_goal(variant(mutated, final_round, goal), function,
                              goal, directory)
            if judge(result) != "closed":
                killed.append(f"{goal}:" + ",".join(sorted(
                    {v for v, _, _ in result.values()})))
        return LIB.classify(mutant, killed, runs / "oracle", masked)

    with concurrent.futures.ThreadPoolExecutor(max(1, jobs // 2)) as pool:
        lines_ = list(pool.map(mutant_line, found))
    statuses = [status for status, _ in lines_]
    killed, unobservable, findings, errors, masked, not_checked = \
        LIB.tally(statuses)
    after = LIB.digests()
    total, proved = len(final), len(closed)
    vacuity_all = all(ok for _, _, ok, _ in checks)
    qualified = all(row[4] for row in qualification)
    result = "CLOSED" if total and proved == total and gate_ok and \
        qualified and before[0] and after[0] else "OPEN"
    reasons = (["open-goals"] if proved < total else []) + (
        [] if gate_ok else ["token-gate"]) + (
        [] if qualified else ["not-qualified"]) + (
        [] if before[0] and after[0] else ["digests"])
    seconds = round(time.monotonic() - started)
    LIB.write(out / "rounds.txt", [
        LIB.HEADER, "# CN arm: one line per annotation round (D-7 item 5); "
        "each goal one run per solver, 60 s each", *rounds,
        f"rounds_used={final_round} of at most {MAX_ROUNDS}",
        f"wall_seconds={seconds}"])
    LIB.write(out / "goals.txt", [
        LIB.HEADER, f"# CN arm, final round {final_round}: every goal with "
        f"each solver's verdict (and CN's reason for a fail)", *goal_lines,
        f"goals={total} proved={proved} open={total - proved} "
        f"pair={'formed' if pair else 'not-formed'}"])
    LIB.write(out / "assumptions.txt", [
        LIB.HEADER, "# CN arm's assumption inventory (D-7 item 4)",
        *ASSUMPTIONS.splitlines()])
    LIB.write(out / "mutants.txt", [
        LIB.HEADER, f"# CN arm: {generator}", "# killed-by names goals the "
        "unmutated copy closes and the mutated copy does not, each with "
        "its solvers' verdicts; each mutant's function's goals only "
        "(callers use its contract)",
        *[line for _, line in lines_],
        f"mutants={len(lines_)} killed={killed} unobservable={unobservable}"
        f" contract_findings={findings} compile_errors={errors} "
        f"masked={masked} not_checked={not_checked}"])
    LIB.write(out / "vacuity.txt", [
        LIB.HEADER, "# CN arm: the qualification's ten cases with the "
        "arm's front-end settings, then the vacuity checks on the final "
        "copy (D-7 items 2 and 6)",
        *[f"qualify solver={solver} case={case} expected={expected} "
          f"observed={observed} ok={'yes' if ok else 'no'} {detail}"
          for solver, case, expected, observed, ok, detail in
          qualification],
        *[f"vacuity check={check} function={function} "
          f"ok={'yes' if ok else 'no'} {detail}"
          for check, function, ok, detail in checks],
        f"qualified={'yes' if qualified else 'no'}",
        f"vacuity={'ok' if vacuity_all else 'not-ok'}"])
    LIB.write(out / "transcription.txt", [
        LIB.HEADER, "# CN arm: how each section 4 clause is transcribed "
        "(mvp/verify/cn/mvp-sbi-leaf.c)", *TRANSCRIPTION.splitlines(),
        f"token_gate={gate}",
        f"file {COPY.relative_to(REPO)} sha256="
        f"{LIB.sha256(COPY.read_bytes())}",
        f"digests_before={before[1]}", f"digests_after={after[1]}"])
    print(f"{TAG}_DETAIL: reasons={','.join(reasons) or 'none'} "
          f"qualified={'yes' if qualified else 'no'} "
          f"masked={masked} not_checked={not_checked} "
          f"compile_errors={errors} "
          f"wall_seconds={seconds}")
    print(f"{TAG}: {result} goals={total} proved={proved} "
          f"rounds={final_round} solvers=z3,cvc5 mutants={len(lines_)} "
          f"killed={killed} unobservable={unobservable} "
          f"contract-findings={findings} "
          f"vacuity={'ok' if vacuity_all else 'not-ok'} "
          f"pair={'formed' if pair else 'not-formed'}")
    return 0


# ---------------------------------------------------------------- self-test
SAMPLE = """\
int f(int x)
/*@ requires x < 4;
    ensures return == 0; // goal D_zero
            return < 5; // goal D_small r1
            return == 0 || // goal D_long
              return == 1;
@*/
{
	return 0;
}
"""


def self_test():
    results = []

    def case(name, passed, detail=""):
        results.append(bool(passed))
        print(f"{'ok  ' if passed else 'FAIL'} {name}"
              f"{'' if passed else ': ' + str(detail)[-600:]}")

    lines = SAMPLE.split("\n")
    case("clauses are tagged lines to their ';'", [
        (a, b, g, r) for a, b, g, r in clauses(lines)] ==
        [(2, 2, "D_zero", 0), (3, 3, "D_small", 1), (4, 5, "D_long", 0)],
        clauses(lines))
    case("round 0 leaves round 1's clauses out", "D_small" not in
         variant(lines, 0) and "D_zero" in variant(lines, 0))
    one = variant(lines, 1, "D_long")
    case("a goal's variant keeps it and its function's requires alone",
         "D_long" in one and "return == 1;" in one and "D_zero" not in one
         and "D_small" not in one and "requires x < 4;" in one, one)
    case("the goals and their rounds", goals_of(lines, 1) ==
         {"D_zero": "be_mvp_denial_decide", "D_small": "be_mvp_denial_decide",
          "D_long": "be_mvp_denial_decide"} and rounds_in(lines) == 1)
    for verdicts, wanted in (((("pass", "", 1), ("pass", "", 1)), "closed"),
                             ((("pass", "", 1), ("timeout", "", 60)),
                              "closed"),
                             ((("pass", "", 1), ("fail", "x", 1)),
                              "disagree"),
                             ((("fail", "x", 1), ("timeout", "", 60)),
                              "open"),
                             ((("error", "", 1), ("error", "", 1)), "open")):
        case(f"judge {verdicts[0][0]} {verdicts[1][0]}", judge(
            dict(zip(SOLVERS, verdicts))) == wanted)
    case("a vacuity check needs one solver's verdict and no contrary one",
         vacuity_ok({"z3": ("fail", "unprovable-constraint", 1),
                     "cvc5": ("timeout", "", 60)}, "fail") and
         not vacuity_ok({"z3": ("fail", "pointer-liveness", 1),
                         "cvc5": ("fail", "pointer-liveness", 1)}, "fail")
         and not vacuity_ok({"z3": ("pass", "", 1),
                             "cvc5": ("fail", "x", 1)}, "pass"))
    checked = with_check(SAMPLE.replace("int f(", "static int inside("),
                         "inside", "contradiction")
    case("a contradiction is a requires and an assert(false) at entry",
         "requires bytes < 1 && bytes > 1;" in checked and
         "{\n\t/*@ assert(false); @*/" in checked, checked)
    ensured = with_check(SAMPLE.replace("int f(", "int be_mvp_denial_decide("),
                         "be_mvp_denial_decide", "ensures-false")
    case("ensures false is a goal before the spec's end",
         "false; // goal VACUITY_false\n@*/" in ensured, ensured)
    committed = COPY.read_text(encoding="latin-1").split("\n")
    goals = goals_of(committed, rounds_in(committed))
    opened = []
    for function in LIB.FUNCTIONS:
        bare = variant(committed, rounds_in(committed),
                       function=function).split("\n")
        first, brace = declarator(bare, function)
        opened.append(any(line.startswith("/*@ ")
                          for line in bare[first:brace]))
    case("each function's specification opens on an untagged line",
         all(opened), opened)
    case("the committed copy's goals cover the five functions",
         set(goals.values()) == set(LIB.FUNCTIONS) and len(goals) > 40,
         goals)
    passed, line = LIB.LEXER.compare(COPY, LIB.LEAF, LIB.FUNCTIONS)
    case("the committed copy passes the token gate", passed, line)
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
                        default=REPO / "build" / "mvp" / "verify" / "cn")
    parser.add_argument("--jobs", type=int, default=8)
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
