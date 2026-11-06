#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""
arm-lib.py: what M8-6's three Leaf A runners share (wp-arm.py, cn-arm.py,
cbmc-leaf-a.py); loaded by path, never run.

Purpose: the parts of MVP M8's decision rule (planning/mvp-m8-plan.md, D-7
items 3 to 6; specification SHA-256
aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b (Revision 1, accepted 2026-11-03 at 93a8d136; the first freeze ade32fa6... at 004f31ae was the first run's), accepted
at 93a8d136 as Revision 1, sections 4 and 6) that do not depend on the arm: the target
digests checked before and after a run (digests.py --check); the seeded
mutants of Leaf A (mutate.py, seed 0x4d38, 24, the five functions); a
mutant carried into an annotated copy by token position (token-equal.py's
lexer), the result checked by the token gate against the mutant itself;
the equivalence oracle, the leaf's host test mvp/tests/deny-test.c built
with the host-test flags target-digests.txt records (HOST_FLAGS) and the
mutant in place of mvp/src/mvp-sbi.c, again without -Werror when it does
not compile with it, and judged by mvp/Makefile's pinned PASS, scenario,
and assertion lines; a mutant's classification (killed by a goal the
unmutated leaf closed, else unobservable when the host test passes or a
contract finding when it fails, compile-error when -Werror refuses it);
a failing assertion's record (stop 2's protocol: CBMC's counterexample
inputs replayed through the unmodified leaf by a scratch host test,
generated here); and the record directory: this run's, replacing the
last, and the retained excerpts (the six text files and defect.txt when
there is one, tree-relative paths only).
Trust: tools are the verifier image's, run from the tree under env -i (the
suites' environment); nothing here writes outside the record directory
but --retain's destination.
"""

import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import time

REPO = pathlib.Path(__file__).resolve().parents[3]
TOOLS = REPO / "mvp" / "verify" / "tools"
LEAF = REPO / "mvp" / "src" / "mvp-sbi.c"
DIGESTS = REPO / "mvp" / "verify" / "target-digests.txt"
MAKEFILE = REPO / "mvp" / "Makefile"
SPECIFICATION_SHA256 = ("aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf"
                        "8a484c69693b8b")
SPECIFICATION_COMMIT = "93a8d136d38547a8c581197315f7607b5eef7bad"
FUNCTIONS = ("access_fault", "htinst_accepted", "inside", "leaf_at",
             "be_mvp_denial_decide")
SEED, COUNT, GOAL_SECONDS = 0x4D38, 24, 60
RECORDS = ("rounds.txt", "goals.txt", "assumptions.txt", "mutants.txt",
           "vacuity.txt", "transcription.txt")
HOST_SOURCES = ("mvp/src/mvp-ring.c", "mvp/src/mvp-gstage.c")
HEADER = (f"# planning/mvp-m8-plan.md D-7, M8-6; specification "
          f"planning/mvp-m8-specifications.md Revision 1, sections 4 and 6, "
          f"SHA-256 {SPECIFICATION_SHA256}, accepted at "
          f"{SPECIFICATION_COMMIT[:8]}")


class Refusal(Exception):
    """A record directory, a mutant, or an input this module refuses."""


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LEXER = load("token_equal", "token-equal.py")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def relative(text):
    """TEXT with the tree's absolute path made tree-relative."""
    return str(text).replace(str(REPO) + "/", "").replace(str(REPO), ".")


def execute(command, seconds, cwd=REPO, environment=None):
    """(status, output, seconds): status the exit code or 'timeout'."""
    started = time.monotonic()
    try:
        done = subprocess.run(command, cwd=cwd, env=environment,
                              stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=seconds,
                              check=False)
        status, output = done.returncode, done.stdout
    except subprocess.TimeoutExpired as expired:
        status, output = "timeout", expired.stdout or b""
    return (status, output.decode("utf-8", "replace"),
            round(time.monotonic() - started, 1))


def prepare(out, marker):
    """OUT, emptied if it is this tool's (holds MARKER), else refused."""
    if out.is_symlink() or (out.exists() and not out.is_dir()):
        raise Refusal(f"{out} is a symbolic link or not a directory")
    if out.is_dir() and any(out.iterdir()) and not (out / marker).is_file():
        raise Refusal(f"{out} is not empty and not this tool's")
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    (out / marker).touch()
    return out


def write(path, lines):
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")


def digests():
    """(passed, line) of digests.py --check: D-7 item 3, the leaf
    unchanged."""
    status, output, _ = execute(["/usr/bin/python3", "-I", "-B",
                                 str(TOOLS / "digests.py"), "--check"], 300)
    lines = [line for line in output.splitlines()
             if line.startswith("BE_MVP_TARGET_DIGESTS: ")]
    line = lines[-1] if lines else f"no result line (exit {status})"
    return status == 0 and " PASS " in line + " ", line


def target_flags():
    """{'include_dirs': [...], 'host_test_flags': [...]} as
    target-digests.txt records them."""
    found = {}
    for line in DIGESTS.read_text(encoding="utf-8").splitlines():
        for key in ("include_dirs", "host_test_flags"):
            if line.startswith(f"flag {key}="):
                found[key] = line.split("=", 1)[1].split()
    if set(found) != {"include_dirs", "host_test_flags"}:
        raise Refusal("target-digests.txt lacks its include_dirs or "
                      "host_test_flags line")
    return found


def host_pins():
    """The deny test's pinned lines, from mvp/Makefile."""
    text = MAKEFILE.read_text(encoding="utf-8")
    pins = {}
    for key in ("PREFIX", "SCENARIOS", "ASSERTIONS"):
        match = re.search(rf"^HOST_{key}_deny := (\S+)$", text, re.M)
        if not match:
            raise Refusal(f"mvp/Makefile has no HOST_{key}_deny")
        pins[key] = match[1]
    return [f"{pins['PREFIX']}: PASS",
            f"{pins['PREFIX']}: scenarios={pins['SCENARIOS']}",
            f"{pins['PREFIX']}: assertions={pins['ASSERTIONS']}"]


# ------------------------------------------------------------------ mutants
def mutants(directory):
    """The seeded mutants of the five functions, generated into DIRECTORY:
    [{'id', 'family', 'rule', 'function', 'line', 'column', 'original',
    'replacement', 'path'}], and the generator's result line."""
    status, output, _ = execute(
        ["/usr/bin/python3", "-I", "-B", str(TOOLS / "mutate.py"), str(LEAF),
         "--functions", *FUNCTIONS, "--seed", hex(SEED), "--count",
         str(COUNT), "--out", str(directory)], 300)
    if status != 0:
        raise Refusal(f"mutate.py failed: {output.strip()[-400:]}")
    rows = (directory / "mutants.tsv").read_text(encoding="utf-8")
    found = []
    for row in rows.splitlines()[2:]:
        ident, family, rule, function, line, column, original, \
            replacement = row.split("\t")
        found.append({"id": ident, "family": family, "rule": rule,
                      "function": function, "line": int(line),
                      "column": int(column),
                      "original": json.loads(original),
                      "replacement": json.loads(replacement),
                      "path": directory / ident / LEAF.name})
    return found, relative(output.strip().splitlines()[-1])


def change(mutant):
    return (f"{mutant['function']}:{mutant['line']}:{mutant['column']} "
            f"{mutant['rule']} {json.dumps(mutant['original'])} -> "
            f"{json.dumps(mutant['replacement'])}")


def offsets(text):
    """The offset of each line's first character, from line 1."""
    starts = [0, 0]
    for index, character in enumerate(text):
        if character == "\n":
            starts.append(index + 1)
    return starts


def copy_mutant(copy_text, mutant, scratch):
    """COPY_TEXT, an annotated copy of the five functions, with MUTANT's
    one change made at the same token, checked by the token gate against
    the mutant source itself; refused if the change cannot be placed."""
    if "\\\n" in copy_text:
        raise Refusal("the copy has a line splice")
    picked, _, _ = LEXER.extract(LEAF, FUNCTIONS)
    starts = [i for i, token in enumerate(picked)
              if (token.line, token.column) == (mutant["line"],
                                                mutant["column"])]
    wanted = re.sub(r"\s+", "", mutant["original"])
    if len(starts) != 1:
        raise Refusal(f"{mutant['id']}: no token of the extract at "
                      f"{mutant['line']}:{mutant['column']}")
    first, joined, last = starts[0], "", starts[0]
    while last < len(picked) and len(joined) < len(wanted):
        joined += picked[last].text
        last += 1
    if joined != wanted:
        raise Refusal(f"{mutant['id']}: the extract's tokens there are not "
                      f"{mutant['original']!r}")
    tokens = LEXER.tokens_of(copy_text)
    prologue = 0
    while prologue < len(tokens) and tokens[prologue].kind == "directive":
        prologue += 1
    body = tokens[prologue:]
    if [t.text for t in body[first:last]] != \
            [t.text for t in picked[first:last]]:
        raise Refusal(f"{mutant['id']}: the copy's tokens differ there")
    lines = offsets(copy_text)
    begin = lines[body[first].line] + body[first].column - 1
    end_token = body[last - 1]
    end = lines[end_token.line] + end_token.column - 1 + len(end_token.text)
    mutated = copy_text[:begin] + mutant["replacement"] + copy_text[end:]
    scratch.mkdir(parents=True, exist_ok=True)
    target = scratch / f"{mutant['id']}-copy.c"
    target.write_text(mutated, encoding="latin-1")
    passed, line = LEXER.compare(target, mutant["path"], FUNCTIONS)
    if not passed:
        raise Refusal(f"{mutant['id']}: the mutated copy fails the token "
                      f"gate against the mutant: {line}")
    return target


# ------------------------------------------------------------------- oracle
def build(sources, binary, werror=True):
    flags = target_flags()["host_test_flags"]
    if not werror:
        flags = [flag for flag in flags if flag != "-Werror"]
    status, output, _ = execute(["gcc", "-B/usr/bin/", *flags, *sources,
                                 "-o", str(binary)], 300)
    return status == 0, output


def oracle(source, scratch):
    """(verdict, werror, detail) of the deny host test with SOURCE in
    place of mvp/src/mvp-sbi.c: verdict 'pass' or 'fail'; werror 'ok' or
    'error' (the build with -Werror refused it; the verdict is then the
    build without it's)."""
    scratch.mkdir(parents=True, exist_ok=True)
    binary = scratch / "deny-test"
    sources = ["mvp/tests/deny-test.c", str(source), *HOST_SOURCES]
    built, output = build(sources, binary)
    werror = "ok"
    if not built:
        werror = "error"
        (scratch / "werror.log").write_text(output, encoding="utf-8")
        built, output = build(sources, binary, werror=False)
        if not built:
            (scratch / "build.log").write_text(output, encoding="utf-8")
            return "fail", werror, "does not compile without -Werror either"
    status, output, _ = execute([str(binary)], 120)
    (scratch / "run.log").write_text(output, encoding="utf-8")
    passed = status == 0 and output.splitlines() == host_pins()
    last = (output.strip().splitlines() or ["no output"])[-1]
    return ("pass" if passed else "fail"), werror, \
        f"exit={status} last={last[:160]}"


def classify(mutant, killed_by, scratch, masked_by=()):
    """The mutant's record line: killed by goals the unmutated leaf
    closed, else the oracle's word. A survivor whose function has goals
    the unmutated leaf leaves open (MASKED_BY) is masked when the host test
    fails: one of those goals might have seen it, so the miss is not the
    contract's."""
    verdict, werror, detail = oracle(mutant["path"], scratch / mutant["id"])
    if killed_by:
        status = "killed-by:" + ",".join(killed_by)
    elif werror == "error":
        status = f"compile-error (without -Werror: host test {verdict})"
    elif verdict == "pass":
        status = "unobservable"
    elif masked_by:
        status = "masked-by-open:" + ",".join(masked_by)
    else:
        status = "contract-finding"
    return status, (f"{mutant['id']} {change(mutant)} status={status} "
                    f"host_test={verdict} werror={werror} "
                    f"{relative(detail)}")


def tally(statuses):
    """(killed, unobservable, contract findings, compile errors, masked,
    not checked)."""
    return (sum(s.startswith("killed-by:") for s in statuses),
            sum(s == "unobservable" for s in statuses),
            sum(s == "contract-finding" for s in statuses),
            sum(s.startswith("compile-error") for s in statuses),
            sum(s.startswith("masked-by-open:") for s in statuses),
            sum(s.startswith("not-checked") for s in statuses))


# ------------------------------------------------------------------- defect
REPLAY_HEAD = r"""/* Generated by mvp/verify/tools/arm-lib.py: a scratch host test that
 * replays CBMC's counterexample inputs through the unmodified
 * mvp/src/mvp-sbi.c (planning/mvp-m8-specifications.md section 4 as its
 * Revision 1 states it, SHA-256 %s; the plan's stop 2), printing the
 * leaf's result and every field of its output for each case, to be read
 * against section 4.4. Fields CBMC's trace does not name are zero. */
#include <stdio.h>
#include <string.h>

#include "mvp.h"

static struct be_mvp_state state;
static struct be_mvp_gstage_map map;
static struct be_mvp_gstage_leaves leaves;
static struct be_mvp_exit record;

static void show(const char *name)
{
	struct be_mvp_denial out;
	int result = be_mvp_denial_decide(&state, &map, &leaves, &record,
					  &out);

	printf("BE_MVP_LEAF_A_REPLAY: case=%%s result=%%d cause=%%lu kind=%%lu "
	       "gpa=%%#lx inject_vscause=%%lu inject_vsstatus=%%#lx "
	       "resume_pc=%%#lx\n", name, result, (unsigned long)out.cause,
	       (unsigned long)out.kind, (unsigned long)out.gpa,
	       (unsigned long)out.inject_vscause,
	       (unsigned long)out.inject_vsstatus,
	       (unsigned long)out.resume_pc);
}

static void clear(void)
{
	memset(&state, 0, sizeof(state));
	memset(&map, 0, sizeof(map));
	memset(&leaves, 0, sizeof(leaves));
	memset(&record, 0, sizeof(record));
}

int main(void)
{
""" % SPECIFICATION_SHA256
# A field CBMC's trace names: an input structure's member, its index
# written as CBMC prints it (0l), its value a C integer literal.
FIELD = re.compile(r"^(state|map|leaves|record)((?:\.[a-z_]+|\[[0-2]l?\])+)$")
VALUE = re.compile(r"^[0-9]+u?l?$")


def replay(directory, cases):
    """Build and run DIRECTORY/defect/replay.c, the replay of CASES
    [(name, [(field, value)])] through the unmodified leaf, and return
    the record's lines (its path, its exit, its output)."""
    scratch = directory / "defect"
    scratch.mkdir(parents=True, exist_ok=True)
    body = []
    for name, fields in cases:
        body.append("\tclear();")
        for field, value in fields:
            match = FIELD.match(field)
            if not match or not VALUE.match(value):
                raise Refusal(f"a trace field {field}={value} this replay "
                              f"cannot write")
            body.append(f"\t{match[1]}{match[2].replace('l]', ']')} = "
                        f"{value};")
        body.append(f'\tshow("{name}");')
    source = scratch / "replay.c"
    source.write_text(REPLAY_HEAD + "\n".join(body) + "\n\treturn 0;\n}\n",
                      encoding="utf-8")
    built, output = build([str(source), str(LEAF), *HOST_SOURCES],
                          scratch / "replay")
    if not built:
        return [f"replay={relative(source)}", "replay_build=failed",
                *[relative(line) for line in output.strip().splitlines()
                  [-5:]]]
    status, output, _ = execute([str(scratch / "replay")], 60)
    return [f"replay={relative(source)} (scratch; built with "
            "target-digests.txt's host_test_flags and the unmodified "
            "mvp/src/mvp-sbi.c)", f"exit={status}",
            *[relative(line) for line in output.strip().splitlines()]]


def defect(directory, failing, cases, reading):
    """Write DIRECTORY/defect.txt: FAILING (the assertions of the leaf's
    contract that fail on it), CBMC's counterexample inputs CASES, their
    replay through the unmodified leaf, and READING."""
    write(directory / "defect.txt", [
        HEADER, "# A clause of the contract fails on the unmodified leaf "
        "against Revision 1: a finding (planning/mvp-m8-plan.md, stop 2: "
        "the human's); the leaf and the specification are not changed.",
        f"failing={','.join(failing)}",
        *[f"cbmc_counterexample {name} " + " ".join(
            f"{field}={value}" for field, value in fields)
          for name, fields in cases],
        *replay(directory, cases), f"reading: {reading}",
        "result=finding"])


# ----------------------------------------------------------------- records
def retain(out, destination):
    """Copy OUT's six records, and defect.txt when there is one, to
    DESTINATION (a new or empty directory), refusing a record with an
    absolute path or a home directory in it."""
    if destination.exists() and any(destination.iterdir()):
        raise Refusal(f"{destination} is not empty")
    texts = {}
    for name in RECORDS + (("defect.txt",) if (out / "defect.txt").is_file()
                           else ()):
        text = (out / name).read_text(encoding="utf-8")
        if re.search(r"(^|[\s=:'\"(])/(home|root|tmp|var)/", text, re.M) or \
                str(REPO) in text:
            raise Refusal(f"{out / name} holds an absolute path")
        texts[name] = text
    destination.mkdir(parents=True, exist_ok=True)
    for name, text in texts.items():
        (destination / name).write_text(text, encoding="utf-8")
    return sorted(texts)


def environment(**extra):
    """The run's environment: the caller's (the suite's env -i one) with
    EXTRA."""
    found = dict(os.environ)
    found.update(extra)
    return found
