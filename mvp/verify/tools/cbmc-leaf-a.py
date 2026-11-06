#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""
cbmc-leaf-a.py --run [--out DIR] [--jobs N]
cbmc-leaf-a.py --retain DIR [--out DIR]
cbmc-leaf-a.py --self-test

Purpose: CBMC's bounded model check of Leaf A (planning/mvp-m8-plan.md,
D-8's last sentence: the specification-debugging, vacuity, and mutant
checks every arm on Leaf A gets; D-7 item 6; specification sections 4
and 6 as its Revision 1 states them, SHA-256
aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b,
accepted 2026-11-03 at 93a8d136; the first run judged against the
accepted text of 004f31ae, ade32fa6...). CBMC 6.8.0 checks
mvp/verify/cbmc/leaf-a/harness.c, which includes mvp/src/mvp-sbi.c whole,
at its entry points check_decide (section 4.4's clauses), check_frame (the
inputs unchanged), and check_helpers (section 4.5's), with every input
nondeterministic under section 4.3's assumptions, --arch riscv64,
--bounds-check, --pointer-check, --signed-overflow-check,
--unsigned-overflow-check, --unwinding-assertions, --unwind 4 (leaf_at's
loop over three entries) and --unwindset memcmp.0:513 (the frame's
comparisons), once with the default SAT solver (MiniSAT 2.2.1) and once
with --cvc5. A property holds when a solver reports SUCCESS and none
FAILURE; a run is killed after 300 s, a killed run no verdict. Then the
vacuity checks (reach_NAME, an assert(0) after each function, must fail;
contradiction_NAME, after a contradictory assumption, must hold;
cover_decide under --cover cover: every case reachable), the 24 seeded
mutants through check_decide and check_helpers (check_frame is not re-run:
a single operator, constant, or condition change writes no input), and,
when a named assertion of check_decide fails on the unmodified leaf (a
finding against Revision 1: stop 2's protocol), CBMC's counterexample
inputs replayed through the leaf by a scratch host test; and the digests
before and after. This is a bounded model check: reported as such, never
as proof.
Outputs: in DIR (default build/mvp/verify/cbmc-leaf-a): the six records,
defect.txt when an assertion fails on the leaf, and every run's command and
output under runs/; last the line `BE_MVP_CBMC_LEAF_A: SUCCESSFUL|FAILED
properties=N failed=M solvers=sat,cvc5 mutants=K killed=A unobservable=B
contract-findings=C vacuity=ok|not-ok unwind=4`.
Exit status: 0 the run completed and is recorded; 1 the runner failed; 2
usage.
"""

import argparse
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
REPO = LIB.REPO
TAG = "BE_MVP_CBMC_LEAF_A"
HARNESS = REPO / "mvp" / "verify" / "cbmc" / "leaf-a" / "harness.c"
MARKER = ".cbmc-leaf-a-run"
CHECKS = ("--arch", "riscv64", "--bounds-check", "--pointer-check",
          "--signed-overflow-check", "--unsigned-overflow-check",
          "--unwinding-assertions", "--unwind", "4", "--unwindset",
          "memcmp.0:513")
SOLVERS = {"sat": (), "cvc5": ("--cvc5",)}
RUN_SECONDS = 300
ENTRIES = ("check_decide", "check_frame", "check_helpers")
MUTANT_ENTRIES = ("check_decide", "check_helpers")
OWN = set(LIB.FUNCTIONS) | {"memcmp"}
# The inputs a counterexample of check_decide is read from.
INPUTS = ("state.accept_denial", "map.gpa_base", "map.size",
          *[f"leaves.page[{i}l].{f}" for i in range(3)
            for f in ("gpa", "bytes", "pte")],
          "record.frame.scause", "record.hstatus", "record.frame.htval",
          "record.frame.stval", "record.htinst", "record.frame.vstvec")


def command(entry, solver, leaf, extra=()):
    """The cbmc command; a --cover run drops --unwinding-assertions, which
    CBMC refuses beside it (the bound is the property runs' to check)."""
    checks = [c for c in CHECKS if "--cover" not in extra or
              c != "--unwinding-assertions"]
    return ["cbmc", *checks, *SOLVERS[solver],
            *[f"-I{d}" for d in LIB.target_flags()["include_dirs"]],
            f'-DLEAF="{leaf}"', "--function", entry, *extra, str(HARNESS)]


def parse(output, entry):
    """(verdict, {property: (status, description)}) of a cbmc run: the
    properties of ENTRY and of the leaf's functions (CBMC lists every
    function's; the others are not reached)."""
    found = {}
    for name, function, line, text, status in re.findall(
            r"^\[(([A-Za-z_0-9]+)\.[a-z_]+\.[0-9]+)\] (?:line (\d+) )?(.*?): "
            r"(SUCCESS|FAILURE)$", output, re.M):
        if function == entry or function in OWN:
            found[name] = (status, text)
    if re.search(r"^VERIFICATION SUCCESSFUL$", output, re.M):
        return "successful", found
    if re.search(r"^VERIFICATION FAILED$", output, re.M):
        return "failed", found
    return "error", found


def covers(output):
    """{goal: covered?} of a --cover cover run."""
    return {name: status == "SATISFIED" for name, status in re.findall(
        r"^\[([A-Za-z_0-9.]+)\] file .*?: (SATISFIED|FAILED)$", output,
        re.M)}


def run(entry, solver, leaf, directory, extra=()):
    directory.mkdir(parents=True, exist_ok=True)
    made = command(entry, solver, leaf, extra)
    status, output, seconds = LIB.execute(
        made, RUN_SECONDS, REPO, LIB.environment(TMPDIR=str(directory)))
    (directory / f"{entry}-{solver}.log").write_text(
        " ".join(made) + f"\nstatus={status} seconds={seconds}\n" + output,
        encoding="utf-8")
    if status == "timeout":
        return "timeout", {}, seconds, output
    verdict, found = parse(output, entry)
    return verdict, found, seconds, output


def merge(results):
    """{property: (state, description)}: holds when a solver reports
    SUCCESS and none FAILURE; fails when one reports FAILURE; else open."""
    names = sorted({n for _, found, _, _ in results.values() for n in found})
    merged = {}
    for name in names:
        seen = [found[name][0] for _, found, _, _ in results.values()
                if name in found]
        text = next(found[name][1] for _, found, _, _ in results.values()
                    if name in found)
        merged[name] = ("fails" if "FAILURE" in seen else "holds" if
                        "SUCCESS" in seen else "open", text)
    return merged


def label(name, text):
    """An assertion's goal name (its description), or the property."""
    return text if ".assertion." in name and re.fullmatch(
        r"[A-Za-z_0-9]+", text) else name


def summary(merged):
    """({assertion's goal name: state}, {other property: state}, the
    names of those not holding)."""
    assertions = {label(n, t): s for n, (s, t) in merged.items()
                  if ".assertion." in n}
    others = {n: s for n, (s, t) in merged.items() if ".assertion." not in n}
    failed = sorted(n for n, s in {**assertions, **others}.items()
                    if s != "holds")
    return assertions, others, failed


def vacuity_ok(verdicts, wanted):
    """A vacuity check holds when a solver gives the WANTED verdict and
    none the other (a killed run gives none)."""
    other = {"failed": "successful", "successful": "failed"}[wanted]
    return wanted in verdicts.values() and other not in verdicts.values()


def run_entries(leaf, directory, entries, jobs):
    """{entry: {solver: (verdict, found, seconds, output)}}."""
    work = [(e, s) for e in entries for s in SOLVERS]
    with concurrent.futures.ThreadPoolExecutor(jobs) as pool:
        done = dict(zip(work, pool.map(
            lambda es: run(es[0], es[1], leaf, directory), work)))
    return {e: {s: done[(e, s)] for s in SOLVERS} for e in entries}


TRANSCRIPTION = """\
section 4.1 -> the harness's C functions bit, gpa_of, opcode, htinst_ok, inside_spec, in_page, has_page (PAGE(gpa) exists), page_index (PAGE, the lowest index), access_fault_spec (1, 5, 7 for 20, 21, 23, else 0), in unsigned __int128 so that no sum or shift of the specification wraps; MAPPED is not needed (E7 does not use it after Revision 1)
section 4.2 -> e2, e3, e6, in_window (the GPA inside the window), unmapped (E7's unmapped case: no page holds the GPA), read_only (its read-only case: cause 23, PAGE exists and lacks W), e7 = !in_window && (unmapped || read_only), entry (E1 and E4 inline)
section 4.3 -> every input a nondeterministic local (valid, distinct, so separated); __CPROVER_assume that the map's size is above 0 and its and each page's sums do not wrap (size <= 2^64 - 1 - base); nothing else; leaf_at's and the helpers' checks assume only the pages' sums (pages_nowrap)
section 4.4 -> check_decide's assertions, named as the WP and CN arms' goals: D_result, D_E1 to D_E7, D_complete, D_cause, D_kind_unmapped (the unmapped case implies kind 0), D_kind_read_only (the read-only case implies kind 1), the eleven fields, D_inject_vsstatus_spp/_spie/_sie/_rest, D_resume_pc, D_zero_* (fifteen); check_frame's D_frame (each input byte for byte unchanged, memcmp); the runtime errors as CBMC's bounds, pointer, signed and unsigned overflow checks on every reached operation
section 4.5 -> check_helpers' AF_cause, AF_other (0 for every other cause), HI_iff, HI_bool (0 or 1), IN_iff and IN_bool (under the no-wrap assumption), LA_page (PAGE's address, the lowest-index page), LA_none
R1-1 -> e7 (the window excluded first, then the unmapped or read-only case), unmapped and read_only as the cases, D_E7, D_complete, D_kind_unmapped, D_kind_read_only; cover_decide's fourth goal: a store to a declared read-only page inside the window, every other entry condition met, refused
R1-2 -> preconditions(): __CPROVER_assume(map.size > 0) for check_decide, check_frame, reach_ and cover_decide
R1-3 -> AF_other, HI_bool, IN_bool; access_fault_spec 0 elsewhere; LA_page by page_index's lowest index
R1-4 to R1-9 -> section 5 (Leaf B), not this arm's
bounds: leaf_at's loop runs three times; --unwind 4 with --unwinding-assertions checks that the bound covers it; memcmp's loop is unwound 513 times (every input structure is shorter)"""


ASSUMPTIONS = """\
tools: CBMC 6.8.0 (Fedora's cbmc-6.8.0-1.fc44) with its SAT solver MiniSAT 2.2.1 and with cvc5 1.3.4, from the verifier image (D-7 item 1; both pairs qualified in M8-5; CBMC with Z3 is not used)
machine model: --arch riscv64 (LP64, unsigned char, the target's); the headers' _Static_asserts hold under it (CBMC's front end rejects a failing one)
preprocessing: CBMC's own (gcc -E) with the target's -I list and -DLEAF=<the leaf's path>, which the harness #includes whole so that its static helpers can be called
memory model: CBMC's (objects with 8 object bits and 56 offset bits); pointer, bounds, and overflow checks on every reached operation
bounds: a bounded model check, never proof: the only loop of the five functions (leaf_at's, three entries) is unwound fully under --unwinding-assertions, so within CBMC's semantics every input is covered; memcmp's loop (the frame check) is unwound past every structure's size
solver trust: MiniSAT 2.2.1 and cvc5 1.3.4; a property holds when one reports SUCCESS and none FAILURE; every FAILURE comes with a concrete trace
ownership premise: section 4.3's validity and separation by construction (distinct locals); nothing at any caller
not covered: the callers; compiled execution (claim class (d)): CBMC's C semantics, not the object code; time limits: a CBMC run is killed after 300 s (all of one entry point's properties are solved together, so the per-goal limit of 60 s is not CBMC's unit)"""


def run_arm(out, jobs):
    out = LIB.prepare(out, MARKER)
    runs = out / "runs"
    started = time.monotonic()
    before = LIB.digests()
    leaf = str(LIB.LEAF)
    baseline = run_entries(leaf, runs / "baseline", ENTRIES, jobs)
    merged = {}
    for entry in ENTRIES:
        merged.update(merge(baseline[entry]))
    assertions, others, failed = summary(merged)
    goal_lines = [f"assertion {n} status={s}" for n, s in
                  sorted(assertions.items())] + [
        f"checks {kind} properties={sum(1 for n in others if f'.{kind}.' in n)} "
        f"holding={sum(1 for n, s in others.items() if f'.{kind}.' in n and s == 'holds')}"
        for kind in sorted({n.split(".")[1] for n in others})]
    run_lines = [f"run entry={e} solver={s} verdict={v} seconds={sec} "
                 f"properties={len(found)}"
                 for e in ENTRIES for s, (v, found, sec, _) in
                 baseline[e].items()]
    checks = []
    for function in LIB.FUNCTIONS:
        for kind, wanted in (("reach", "failed"),
                             ("contradiction", "successful")):
            entry = f"{kind}_{function}"
            results = {s: run(entry, s, leaf, runs / "vacuity")
                       for s in SOLVERS}
            verdicts = {s: v for s, (v, _, _, _) in results.items()}
            checks.append((kind, function, vacuity_ok(verdicts, wanted),
                           " ".join(f"{s}={v}" for s, v in verdicts.items())
                           + f" wanted={wanted}"))
    cover = {}
    for solver in SOLVERS:
        _, _, seconds, output = run("cover_decide", solver, leaf,
                                    runs / "cover", ("--cover", "cover"))
        cover[solver] = covers(output)
    goals = sorted({g for found in cover.values() for g in found})
    all_covered = bool(goals) and all(
        any(found.get(g) for found in cover.values()) for g in goals)
    checks.append(("cover", "be_mvp_denial_decide", all_covered, " ".join(
        f"{s}={sum(c.values())}/{len(c)}" for s, c in cover.items())))
    found, generator = LIB.mutants(out / "mutants")
    holding = {n for n, (s, _) in merged.items() if s == "holds"}

    def mutant_line(mutant):
        directory = runs / "mutants" / mutant["id"]
        results = run_entries(str(mutant["path"]), directory,
                              MUTANT_ENTRIES, 2)
        mine = {}
        for entry in MUTANT_ENTRIES:
            mine.update(merge(results[entry]))
        killed = sorted(label(n, t) for n, (s, t) in mine.items()
                        if s == "fails" and (n in holding or n not in merged))
        silent = [e for e in MUTANT_ENTRIES if all(
            v in ("timeout", "error") for v, _, _, _ in results[e].values())]
        if silent and not killed:
            verdict, werror, detail = LIB.oracle(
                mutant["path"], runs / "oracle" / mutant["id"])
            return "no-verdict", (
                f"{mutant['id']} {LIB.change(mutant)} status=no-verdict "
                f"(no solver's verdict on {','.join(silent)}) "
                f"host_test={verdict} werror={werror} "
                f"{LIB.relative(detail)}")
        masked = sorted(label(n, t) for n, (s, t) in merged.items()
                        if s != "holds" and n.startswith(
                            tuple(f"{e}." for e in MUTANT_ENTRIES)))
        return LIB.classify(mutant, killed, runs / "oracle", masked)

    with concurrent.futures.ThreadPoolExecutor(max(1, jobs // 2)) as pool:
        lines = list(pool.map(mutant_line, found))
    statuses = [status for status, _ in lines]
    killed, unobservable, findings, errors, masked, _ = LIB.tally(statuses)
    failing = sorted(name for name, state in assertions.items()
                     if state == "fails")
    if failing:
        _, _, _, output = run("check_decide", "cvc5", leaf, runs / "trace",
                              ("--trace",))
        cases = []
        for block in re.split(r"^Trace for ", output, flags=re.M)[1:]:
            name = label(block.split(":", 1)[0], merged.get(
                block.split(":", 1)[0], ("", ""))[1])
            if name not in failing:
                continue
            cases.append((name, [(field, match[1]) for field in INPUTS
                                 for match in [re.search(
                                     rf"^  {re.escape(field)}=(\S+) \(",
                                     block, re.M)] if match]))
        LIB.defect(out, failing, cases, "an assertion of check_decide or "
                   "check_helpers fails on the unmodified leaf; CBMC's "
                   "inputs for check_decide's are replayed above, the "
                   "leaf's result and output to be read against section "
                   "4.4; check_helpers' and check_frame's are in "
                   "runs/baseline")
    after = LIB.digests()
    vacuity_all = all(ok for _, _, ok, _ in checks)
    verdict = "SUCCESSFUL" if not failed and before[0] and after[0] else \
        "FAILED"
    seconds = round(time.monotonic() - started)
    LIB.write(out / "rounds.txt", [
        LIB.HEADER, "# CBMC on Leaf A: one round (the harness as "
        "written; a bounded model check has no annotation rounds)",
        f"round=0 goals={len(assertions)} proved={sum(s == 'holds' for s in assertions.values())} "
        f"open={sum(s != 'holds' for s in assertions.values())} "
        f"seconds={seconds}", *run_lines, f"wall_seconds={seconds}"])
    LIB.write(out / "goals.txt", [
        LIB.HEADER, "# CBMC on Leaf A: each named assertion and each kind "
        "of CBMC check, holding when a solver reports SUCCESS and none "
        "FAILURE (a bounded model check, not proof)", *goal_lines,
        f"properties={len(merged)} failed={len(failed)} "
        f"failing={','.join(failed) or 'none'}"])
    LIB.write(out / "assumptions.txt", [
        LIB.HEADER, "# CBMC on Leaf A: assumption inventory (D-7 item 4)",
        *ASSUMPTIONS.splitlines()])
    LIB.write(out / "mutants.txt", [
        LIB.HEADER, f"# CBMC on Leaf A: {generator}", "# killed-by names "
        "assertions or checks of check_decide and check_helpers that hold "
        "for the unmutated leaf and fail for the mutant",
        *[line for _, line in lines],
        f"mutants={len(lines)} killed={killed} unobservable={unobservable} "
        f"contract_findings={findings} compile_errors={errors} "
        f"masked={masked} no_verdict={statuses.count('no-verdict')}"])
    LIB.write(out / "vacuity.txt", [
        LIB.HEADER, "# CBMC on Leaf A: the vacuity checks (D-7 item 6; "
        "section 6)", *[f"vacuity check={k} function={f} "
                        f"ok={'yes' if ok else 'no'} {d}"
                        for k, f, ok, d in checks],
        *[f"cover solver={s} goal={g} covered={'yes' if c else 'no'}"
          for s, found in cover.items() for g, c in sorted(found.items())],
        f"vacuity={'ok' if vacuity_all else 'not-ok'}"])
    LIB.write(out / "transcription.txt", [
        LIB.HEADER, "# CBMC on Leaf A: how each section 4 clause is "
        "checked (mvp/verify/cbmc/leaf-a/harness.c)",
        *TRANSCRIPTION.splitlines(),
        f"file {HARNESS.relative_to(REPO)} sha256="
        f"{LIB.sha256(HARNESS.read_bytes())}",
        f"digests_before={before[1]}", f"digests_after={after[1]}"])
    print(f"{TAG}_DETAIL: reasons="
          f"{'contract-failure' if failing else 'none'} "
          f"failing={','.join(failed) or 'none'} "
          f"masked={masked} compile_errors={errors} wall_seconds={seconds}")
    print(f"{TAG}: {verdict} properties={len(merged)} failed={len(failed)} "
          f"solvers=sat,cvc5 mutants={len(lines)} killed={killed} "
          f"unobservable={unobservable} contract-findings={findings} "
          f"vacuity={'ok' if vacuity_all else 'not-ok'} unwind=4")
    return 0


# ---------------------------------------------------------------- self-test
OUTPUT = """\
[check_decide.assertion.1] line 190 D_result: SUCCESS
[check_decide.assertion.9] line 211 D_complete: FAILURE
[be_mvp_denial_decide.overflow.1] line 287 arithmetic overflow on unsigned << in frame->htval << 2u: SUCCESS
[serve_record.pointer_dereference.1] line 693 dereference failure: pointer NULL in state->phase: SUCCESS
[leaf_at.unwind.0] line 246 unwinding assertion loop 0: SUCCESS
** 1 of 5 failed (2 iterations)
VERIFICATION FAILED
"""


def self_test():
    results = []

    def case(name, passed, detail=""):
        results.append(bool(passed))
        print(f"{'ok  ' if passed else 'FAIL'} {name}"
              f"{'' if passed else ': ' + str(detail)[-600:]}")

    verdict, found = parse(OUTPUT, "check_decide")
    case("the entry's and the leaf's properties, not the unreached",
         verdict == "failed" and sorted(found) == [
             "be_mvp_denial_decide.overflow.1", "check_decide.assertion.1",
             "check_decide.assertion.9", "leaf_at.unwind.0"], found)
    case("an assertion is named by its description", label(
        "check_decide.assertion.9", "D_complete") == "D_complete" and
        label("leaf_at.unwind.0", "unwinding assertion loop 0") ==
        "leaf_at.unwind.0")
    merged = merge({"sat": ("failed", {"p": ("SUCCESS", "P"), "q": (
        "FAILURE", "Q")}, 1, ""), "cvc5": ("timeout", {}, 300, "")})
    case("one solver's verdict suffices; a FAILURE fails", merged ==
         {"p": ("holds", "P"), "q": ("fails", "Q")}, merged)
    merged = merge({"sat": ("failed", {"p": ("SUCCESS", "P")}, 1, ""),
                    "cvc5": ("failed", {"p": ("FAILURE", "P")}, 1, "")})
    case("a disagreement fails", merged["p"][0] == "fails", merged)
    summarised = summary({
        "check_decide.assertion.9": ("fails", "D_complete"),
        "check_decide.assertion.1": ("holds", "D_result"),
        "leaf_at.unwind.0": ("open", "unwinding assertion loop 0")})
    case("the summary names failing assertions and checks",
         summarised == ({"D_complete": "fails", "D_result": "holds"},
                        {"leaf_at.unwind.0": "open"},
                        ["D_complete", "leaf_at.unwind.0"]), summarised)
    case("a vacuity check needs one solver's verdict and no contrary one",
         vacuity_ok({"sat": "timeout", "cvc5": "failed"}, "failed") and
         not vacuity_ok({"sat": "successful", "cvc5": "failed"}, "failed")
         and not vacuity_ok({"sat": "timeout", "cvc5": "error"},
                            "successful"))
    case("cover goals", covers("[cover_decide.coverage.1] file h.c line 9 "
                               "function cover_decide: SATISFIED\n"
                               "[cover_decide.coverage.2] file h.c line 10 "
                               "function cover_decide: FAILED\n") ==
         {"cover_decide.coverage.1": True,
          "cover_decide.coverage.2": False})
    made = " ".join(command("check_decide", "cvc5", "/x/mvp-sbi.c"))
    case("the command checks everything the plan names", all(
        word in made for word in ("--arch riscv64", "--bounds-check",
                                  "--pointer-check",
                                  "--signed-overflow-check",
                                  "--unsigned-overflow-check",
                                  "--unwinding-assertions", "--unwind 4",
                                  "--cvc5", "--function check_decide",
                                  '-DLEAF="/x/mvp-sbi.c"')), made)
    text = HARNESS.read_text(encoding="utf-8")
    case("the harness has every entry point the runner names", all(
        f"void {e}(void)" in text for e in ENTRIES + ("cover_decide",) +
        tuple(f"{k}_{f}" for k in ("reach", "contradiction")
              for f in LIB.FUNCTIONS)))
    print(f"{TAG}_SELF_TEST: {'PASS' if all(results) else 'FAIL'} "
          f"cases={len(results)}"
          f"{'' if all(results) else f' failed={results.count(False)}'}")
    return 0 if all(results) else 1


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=pathlib.Path, default=REPO / "build" /
                        "mvp" / "verify" / "cbmc-leaf-a")
    parser.add_argument("--jobs", type=int, default=6)
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
    except (OSError, LIB.Refusal, ValueError, KeyError) as why:
        print(f"{TAG}: FAIL {why}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
