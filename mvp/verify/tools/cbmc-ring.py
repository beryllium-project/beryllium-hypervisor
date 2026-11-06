#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""
cbmc-ring.py --run [--out DIR] [--jobs N] [--no-mutants] [--only NAME,...]
             [--classes N]
cbmc-ring.py --self-test

Purpose: Leaf B of MVP M8's pilot (planning/mvp-m8-plan.md, D-7 items 1 to
7, D-8, work package M8-6, Q7, Q11, Q14): bounded model checking of
mvp/src/mvp-ring.c's fourteen public functions against the per-call
properties of section 5 of the specification as its Revision 1 states
them (planning/mvp-m8-specifications.md, accepted at 93a8d136, SHA-256
aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b; the
first run judged against the accepted text of 004f31ae, ade32fa6...) with
CBMC 6.8.0, by the harnesses under mvp/verify/cbmc/ring/ (one per function
and one sequence harness), at capacities 512 and 4,096. A bounded model
check, never a proof: every record and line says so.
Each harness runs in configuration B (bounds, pointer, signed-overflow,
undefined-shift, and unwinding checks; the leaf's loops unwound to their
bounds 8, 256, and 32, CBMC's count one more; --arch riscv64) and A (B's
program, --unsigned-overflow-check, only the unsigned-overflow properties
asserted: each flagged site is classified intended-wrap, a difference of
two index values or one of the index advances section 5 names (R1-9:
cursor + 8, cursor + 16, cursor + 16 + i, cursor + size), or a finding),
each with CBMC's SAT solver (MiniSAT) and
with --cvc5, the two qualified pairs (CBMC with Z3 did not qualify), every
run killed after 600 s (a non-result). A property counts as checked only
if no solver reports it false and at least one reports it successful in
every run its row needs. Buffer-writing and buffer-reading conclusions
(post, post_words, take, the sequence) run one CBMC process per position
class: the own index's low bits fixed to one aligned buffer position and
its other bits arbitrary, the classes together every own index (a case
split, so that CBMC folds the buffer positions); their scalar conclusions
run once with the own index wholly arbitrary. For each harness and part,
a coverage run (--cover assertion: every assertion reachable) and a
vacuity run (the assertions dropped, assert(0) after the assumptions,
which must fail). Then the seeded mutants (mutate.py, seed 0x4d38, 24, all
twenty functions of mvp-ring.c): each substituted for mvp-ring.c in the
harnesses (configuration B, both capacities, the mutated function's
harness first, a buffer part on its first class, each run with the solver
that answered the leaf's same run sooner) until one fails; one that
fails none is run against the host test (mvp/tests/ring-test.c with the
host test flags of verify/target-digests.txt, with -Werror, and without
if it does not compile): passing, unobservable (not killed); failing, a
harness finding.
Inputs: the harnesses, mvp-ring.c and its headers (the include directories
of verify/target-digests.txt), mvp-ring.h's public functions (the harness
list must equal them), cbmc and cvc5 and gcc on PATH (the verifier
image's); --jobs, the CBMC processes at once besides the BIG_SLOTS
4,096-byte runs, and the mutants at once (default a third of the
processors, at least 2); --no-mutants, --only (some harnesses), and
--classes N (at most N position classes a class-split part) for
development runs: the record says so, and its line is then PARTIAL.
Outputs: DIR/cbmc-ring/ (default DIR build/mvp/verify), emptied if it is
this tool's: properties.txt, wrap-sites.txt, coverage.txt, vacuity.txt,
mutants.txt, assumptions.txt, sequence.txt, transcription.txt (how each
row of section 5, and each clause Revision 1 corrected, is checked, with
the harnesses' digests), defect-<function>.txt for each
function whose row failed on the unmodified leaf (the reason and CBMC's
trace), summary.json, logs/ with every run's command and output, and
mutants/ (the generated mutants); then the line
BE_MVP_CBMC_RING: <CHECKED|OPEN> functions=14 capacities=512,4096
properties=N checked=M open=K solvers=sat,cvc5 mutants=24 killed=A
unobservable=B harness-findings=C coverage=ok|not-ok vacuity=ok|not-ok.
CHECKED means every row checked; OPEN otherwise. Each command the runner
starts has a TMPDIR of its own (mode 0700) under the runner's TMPDIR,
removed when the command ends, a timeout included: a cvc5 killed at the
budget leaves no temporary files (mvp/README.md, item 118).
Exit status: 0 the run completed and is recorded (whatever its outcome);
1 the runner failed; 2 usage.
"""

import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

REPO = pathlib.Path(__file__).resolve().parents[3]
VERIFY = REPO / "mvp" / "verify"
HARNESS_DIR = VERIFY / "cbmc" / "ring"
LEAF = REPO / "mvp" / "src" / "mvp-ring.c"
LEAF_HEADER = REPO / "mvp" / "src" / "mvp-ring.h"
RING_TEST = REPO / "mvp" / "tests" / "ring-test.c"
TARGET_DIGESTS = VERIFY / "target-digests.txt"
MUTATE = VERIFY / "tools" / "mutate.py"
MAKEFILE = REPO / "mvp" / "Makefile"
TAG = "BE_MVP_CBMC_RING"
SPECIFICATION_SHA256 = ("aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf"
                        "8a484c69693b8b")
SPECIFICATION_COMMIT = "93a8d136"
MARKER = ".cbmc-ring-run"
CAPACITIES = (512, 4096)
SOLVERS = {"sat": (), "cvc5": ("--cvc5",)}
CONFIGURATIONS = ("A", "B")
RUN_SECONDS = 600
CHECKS = ("--bounds-check", "--pointer-check", "--signed-overflow-check",
          "--undefined-shift-check")
ARCH = ("--arch", "riscv64")
# The leaf's loops and their bounds (mvp-ring.c: store_le and load_le by 8
# bytes, the post and take payload loops by 256, post_words by 32). CBMC
# counts one more: its unwinding assertion checks the loop condition after
# the last iteration (a bound of 8 for an 8-iteration loop fails it).
LEAF_LOOPS = {"store_le.0": 8, "load_le.0": 8, "be_mvp_ring_post.0": 256,
              "be_mvp_ring_take.0": 256, "be_mvp_ring_post_words.0": 32}
MUTANT_SEED = 0x4D38
MUTANT_COUNT = 24
# (harness, the function under test, its parts). "all": one run, the own
# index arbitrary; "scalar": the conclusions but those about buffer bytes,
# the own index arbitrary; "buffer": the buffer conclusions, one run per
# position class of the whole buffer; "window": the sequence, one run per
# position class of [C - 512, C), the row's windows.
HARNESSES = (
    ("reset", "be_mvp_ring_reset", ("all",)),
    ("init", "be_mvp_ring_init", ("all",)),
    ("record_bytes", "be_mvp_ring_record_bytes", ("all",)),
    ("post", "be_mvp_ring_post", ("scalar", "buffer")),
    ("room", "be_mvp_ring_room", ("all",)),
    ("post_words", "be_mvp_ring_post_words", ("scalar", "buffer")),
    ("publish", "be_mvp_ring_publish", ("all",)),
    ("acquire", "be_mvp_ring_acquire", ("all",)),
    ("take", "be_mvp_ring_take", ("scalar", "buffer")),
    ("release", "be_mvp_ring_release", ("all",)),
    ("peak", "be_mvp_ring_peak", ("all",)),
    ("taken", "be_mvp_ring_taken", ("all",)),
    ("published", "be_mvp_ring_published", ("all",)),
    ("record_word", "be_mvp_record_word", ("all",)),
    ("sequence", None, ("window",)),
)
# The harnesses this run runs: every one but with --only; and --classes.
HARNESSES_RUN = HARNESSES
DEVELOPMENT_CLASSES = None
PART_DEFINES = {"all": (), "scalar": ("BE_CBMC_PART_SCALAR",),
                "buffer": ("BE_CBMC_PART_BUFFER",), "window": ()}
# Position classes run per (part, capacity): None every class. A whole
# buffer at 4,096 is 512 classes of minutes each, beyond this run's
# budget: its first classes (a record across the buffer's end, at its
# start, and in its last word) run and the row stays OPEN.
CLASS_LIMIT = {("buffer", 512): None, ("buffer", 4096): 3,
               ("window", 512): None, ("window", 4096): None}
# On a class-split part, configuration A and cvc5 run on its first classes
# only: (configuration, solver, capacity) -> classes. cvc5 answers no
# class-split run within 600 s (every one at 512 in the trials): at 4,096
# it runs once, B's first class, to record that.
SAMPLES = {("A", "sat", 512): 3, ("A", "sat", 4096): 3,
           ("A", "cvc5", 512): 1, ("A", "cvc5", 4096): 0,
           ("B", "cvc5", 512): 1, ("B", "cvc5", 4096): 1}
# Runs that read or write a 4,096-byte buffer at arbitrary positions hold
# 6 to 10 GB each (a 512-byte run under 2 GB): they share BIG_SLOTS units,
# take's runs two units (its reads at arbitrary positions), the others one.
BIG_SLOTS = 4
# The harnesses whose reader views may first take a record, and the
# capacities at which they do (a take's reads at arbitrary positions of a
# 4,096-byte buffer exceed the budget: a bound, recorded).
READER_TAKE = {("acquire", 512), ("release", 512)}
# Index values in mvp-ring.c, as CBMC prints its expressions: a difference
# of two of them is section 5's intended wraparound.
INDEX_TERMS = ("head_value", "tail_value", "tail", "head", "released",
               "ring->cursor", "ring->limit", "ring->tail->value",
               "ring->head->value")
# The index advances section 5 names as intended wraparound too (Revision
# 1, R1-9: cursor + 8, cursor + 16, cursor + 16 + i, and cursor + size on
# the free-running counters), as (left, right) operands of the + CBMC
# prints, casts stripped. Any other advance stays a finding.
ADVANCES = {("ring->cursor", "8u"), ("ring->cursor", "16u"),
            ("ring->cursor + 16u", "index"), ("ring->cursor", "size")}
# A reading's host-test reproducer: a scratch C test built with the host
# test flags against the unmodified mvp-ring.c and run, its output in
# defect-<function>.txt beside CBMC's trace (planning/mvp-m8-plan.md, stop
# 2's protocol).
ROOM_REPRODUCER = """/* Generated by mvp/verify/tools/cbmc-ring.py: a scratch host test of
 * planning/mvp-m8-specifications.md section 5's room row as its Revision 1
 * states it (SHA-256 aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b)
 * against the unmodified mvp/src/mvp-ring.c, the plan's stop 2 protocol:
 * a writer view posts one empty record and does not publish it (cursor =
 * limit + 16), then reads a tail BEHIND bytes behind its published head.
 * The row: a tail aligned with limit - t <= C is well formed; then room
 * returns the largest payload that fits (none when cursor - t > C), writes
 * nothing, and never fails the view for want of room. */
#include <stdio.h>

#include "mvp-ring.h"

static be_u8 buffer[4096];
static struct be_mvp_ring_index head;
static struct be_mvp_ring_index tail;

static int check(be_u64 capacity, be_u64 behind)
{
	struct be_mvp_ring writer;
	be_u64 room;
	be_u64 used;
	int well_formed;
	int fits;
	int agrees;

	head.value = 0U;
	tail.value = 0U;
	if (be_mvp_ring_init(&writer, buffer, capacity, &head, &tail,
			     BE_MVP_RECORDS_INPUT, 0U, BE_MVP_RING_WRITER) != 1 ||
	    be_mvp_ring_post(&writer, BE_MVP_RECORD_INPUT, 0U,
			     (const be_u8 *)0, 0U) != 1) {
		printf("BE_MVP_RING_DEFECT: setup failed\\n");
		return 1;
	}
	tail.value = 0U - behind;
	used = writer.cursor - tail.value;
	well_formed = (tail.value & 7U) == 0U &&
		      writer.limit - tail.value <= capacity;
	fits = used <= capacity && used + 16U <= capacity;
	room = be_mvp_ring_room(&writer);
	agrees = well_formed ? writer.failed == 0U && (fits || room == 0U) :
			       room == 0U && writer.failed != 0U;
	printf("BE_MVP_RING_DEFECT: capacity=%lu limit-t=%lu cursor-t=%lu "
	       "room=%lu failed=%u row=%s %s\\n", (unsigned long)capacity,
	       (unsigned long)(writer.limit - tail.value),
	       (unsigned long)used, (unsigned long)room, writer.failed,
	       well_formed ? (fits ? "well-formed,fits,not-failed" :
			      "well-formed,none-fits,not-failed") :
			     "malformed,failed",
	       agrees ? "agrees" : "contradicts");
	return !agrees;
}

int main(void)
{
	static const be_u64 capacities[2] = { 512U, 4096U };
	int contradictions = 0;
	unsigned int index;

	for (index = 0U; index < 2U; ++index) {
		be_u64 capacity = capacities[index];

		/* The row's well-formed tails no record fits: C and C - 8 behind
		 * the published head, the cursor C + 16 and C + 8 past it. */
		contradictions += check(capacity, capacity);
		contradictions += check(capacity, capacity - 8U);
		/* Controls: the cursor exactly C past the tail (well formed,
		 * none fits, not failed), and a tail more than C behind the
		 * published head (malformed, failed). */
		contradictions += check(capacity, capacity - 16U);
		contradictions += check(capacity, capacity + 8U);
	}
	printf("BE_MVP_RING_DEFECT: %s contradictions=%d\\n",
	       contradictions ? "CONFIRMED" : "NONE", contradictions);
	return contradictions ? 1 : 0;
}
"""
# The failures on the unmodified leaf read from their traces (the row is
# OPEN; defect-<function>.txt holds the reason and the trace), keyed by the
# harness and the failing assertion's description: (reason, reading, a
# reproducer's source or None). A failure not listed is OPEN as
# unclassified. The first run's readings (against the accepted text of
# 004f31ae, its seven rows' errata, Revision 1's R1-4 to R1-9) are in
# mvp/results/20261103-verify/leaf-b/.
READINGS = {
    ("room", "room: a well-formed tail the cursor is more than C past (none "
             "fits): 0, writes nothing, the view not failed"): (
        "specification-mismatch",
        "Revision 1's room row calls a tail well formed when it is aligned "
        "with limit - t <= C (its parenthesis, 'as post reads it: aligned, "
        "with limit - t <= C', R1-6) and says room never fails the view "
        "for want of room; be_mvp_ring_room also refuses, as malformed, a "
        "tail the cursor is more than C past (cursor - t > C: mvp-ring.c "
        "line 211; mvp-ring.h: room 'checks it as be_mvp_ring_post() "
        "does') and fails the view. With a record posted and not published "
        "(cursor = limit + 16) a tail C or C - 8 behind the published head "
        "is well formed by the row and refused by the code: the trace's "
        "state and the reproducer's. A reader's release never moves the "
        "tail back, and post keeps cursor - t <= C when it posts, so the "
        "state needs a tail value no release writes; the row's 'for any "
        "peer index value' admits it. The row and the code disagree; "
        "neither is changed here (stop 2: the human's)",
        ROOM_REPRODUCER),
}


class Refusal(Exception):
    """An input, a harness list, or an output directory refused."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def relative(path):
    """PATH from the tree's root, so that no record holds a home path."""
    return os.path.relpath(path, REPO)


def relative_text(text):
    """TEXT with the tree's absolute path made tree-relative."""
    return text.replace(str(REPO) + "/", "")


# ---------------------------------------------------------------- inputs
def target_flags(text):
    """(include directories, host test flags) of target-digests.txt."""
    dirs = re.search(r"^flag include_dirs=(.+)$", text, re.M)
    host = re.search(r"^flag host_test_flags=(.+)$", text, re.M)
    if not dirs or not host:
        raise Refusal("target-digests.txt has no include_dirs or "
                      "host_test_flags line")
    return dirs[1].split(), host[1].split()


def public_functions(header_text):
    """The function names mvp-ring.h declares, in order."""
    text = re.sub(r"/\*.*?\*/", " ", header_text, flags=re.S)
    return re.findall(r"^[A-Za-z_][\w \t\*]*?\b(be_mvp_\w+)\s*\(", text,
                      re.M)


def check_harness_list(functions, files):
    """Refuse a function without a harness or a harness file without a
    function (the sequence harness and harness.h apart)."""
    covered = {function for _, function, _ in HARNESSES if function}
    missing = sorted(set(functions) - covered)
    extra = sorted(covered - set(functions))
    if missing:
        raise Refusal(f"no harness for {', '.join(missing)}")
    if extra:
        raise Refusal(f"a harness for {', '.join(extra)}, which mvp-ring.h "
                      "does not declare")
    expected = {f"{name}.c" for name, _, _ in HARNESSES} | {"harness.h"}
    unknown = sorted(set(files) - expected)
    absent = sorted(expected - set(files))
    if unknown:
        raise Refusal(f"harness files no row names: {', '.join(unknown)}")
    if absent:
        raise Refusal(f"harness files missing: {', '.join(absent)}")


def host_counts(makefile_text):
    scenarios = re.search(r"^HOST_SCENARIOS_ring := (\d+)$", makefile_text,
                          re.M)
    assertions = re.search(r"^HOST_ASSERTIONS_ring := (\d+)$", makefile_text,
                           re.M)
    if not scenarios or not assertions:
        raise Refusal("mvp/Makefile has no HOST_SCENARIOS_ring or "
                      "HOST_ASSERTIONS_ring")
    return int(scenarios[1]), int(assertions[1])


# --------------------------------------------------------------- parsers
RESULT = re.compile(r"^\[(?P<id>[^\]]+)\] (?:line (?P<line>\d+) )?"
                    r"(?P<desc>.*): (?P<status>SUCCESS|FAILURE|UNKNOWN|"
                    r"ERROR)$")
CONTEXT = re.compile(r"^(?P<file>\S+) function (?P<function>\S+)$")
COVER = re.compile(r"^\[(?P<id>[^\]]+)\] file (?P<file>\S+) line "
                   r"(?P<line>\d+) function (?P<function>\S+) (?P<desc>.*): "
                   r"(?P<status>SATISFIED|FAILED)$")


def parse_check(output):
    """(verdict, {id: (status, file, function, line, desc)}) of a CBMC
    property run: verdict successful, failed, or error (no VERIFICATION
    line: a timeout, a crash, a front-end error)."""
    properties, context = {}, ("", "")
    in_results = False
    for line in output.split("\n"):
        if line.startswith("** Results:"):
            in_results = True
            continue
        if not in_results:
            continue
        found = CONTEXT.match(line)
        if found:
            context = (found["file"], found["function"])
            continue
        found = RESULT.match(line)
        if found:
            properties[found["id"]] = (found["status"], context[0],
                                       context[1], int(found["line"] or 0),
                                       found["desc"])
    if re.search(r"^VERIFICATION SUCCESSFUL$", output, re.M):
        verdict = "successful"
    elif re.search(r"^VERIFICATION FAILED$", output, re.M):
        verdict = "failed"
    else:
        verdict = "error"
    return verdict, properties


def parse_cover(output):
    """(covered, total, {id: (status, line, desc)}) of a --cover run, or
    (None, None, {}) without its summary line."""
    goals = {}
    for line in output.split("\n"):
        found = COVER.match(line)
        if found:
            goals[found["id"]] = (found["status"], int(found["line"]),
                                  found["desc"])
    summary = re.search(r"^\*\* (\d+) of (\d+) covered", output, re.M)
    if not summary:
        return None, None, goals
    return int(summary[1]), int(summary[2]), goals


OVERFLOW = re.compile(r"^arithmetic overflow on unsigned (?P<op>\S+) in "
                      r"(?P<expr>.*)$")


def strip_casts(expression):
    return re.sub(r"\((?:be_u64|be_u32|be_u8|unsigned long int|unsigned "
                  r"int|unsigned long)\)", "", expression).strip()


def split_top(expression, operator):
    """EXPRESSION's operands around its top-level OPERATOR, or None."""
    depth = 0
    for index in range(len(expression) - 1, -1, -1):
        character = expression[index]
        if character == ")":
            depth += 1
        elif character == "(":
            depth -= 1
        elif depth == 0 and expression.startswith(f" {operator} ",
                                                  index - 1):
            return (expression[:index - 1].strip(),
                    expression[index + 2:].strip())
    return None


def classify_wrap(file, description):
    """(class, kind) of an unsigned-overflow site: intended-wrap for a
    difference of two index values in the leaf, kind index-difference, and
    for one of the four index advances section 5 names, kind index-advance
    (Revision 1, R1-9: wraparound is the intended semantics of the index
    differences and of those advances); else a finding, kind
    index-advance for another index value plus an offset and other for the
    rest."""
    found = OVERFLOW.match(description)
    if not found:
        return "finding", "not an unsigned-overflow property"
    if pathlib.Path(file).name != LEAF.name:
        return "finding", "harness-site"
    operator = found["op"]
    expression = strip_casts(found["expr"])
    operands = split_top(expression, operator)
    if not operands:
        return "finding", "other"
    left, right = (strip_casts(operand).strip("()").strip()
                   for operand in operands)
    if operator == "-" and left in INDEX_TERMS and right in INDEX_TERMS:
        return "intended-wrap", "index-difference"
    if operator == "+" and (left, right) in ADVANCES:
        return "intended-wrap", "index-advance"
    if operator == "+" and (left in INDEX_TERMS or left.startswith(
            "ring->cursor +") or left == "position"):
        return "finding", "index-advance"
    return "finding", "other"


# ---------------------------------------------------------------- runner
def remove_tree(directory):
    """DIRECTORY and everything in it, again while an entry made during a
    removal (by a process of the killed session not yet gone) keeps it."""
    for _ in range(50):
        shutil.rmtree(directory, ignore_errors=True)
        if not os.path.lexists(directory):
            return
        time.sleep(0.1)


def execute(command, cwd, seconds, tmp_root=None):
    """(status, output, seconds): status the exit code or 'timeout'. The
    command runs in a session of its own, and a timeout kills the session:
    CBMC's solver process (cvc5) with it, not left running. Its TMPDIR is
    a directory of its own (mode 0700) under TMP_ROOT, by default the
    runner's TMPDIR (verify.sh's build/mvp/verify/tmp), removed when the
    command ends, so that a solver killed at the budget leaves none of its
    temporary files (about 1 GB of cvc5's; mvp/README.md, item 118)."""
    started = time.monotonic()
    scratch = tempfile.mkdtemp(prefix="job-",
                               dir=tmp_root or tempfile.gettempdir())
    try:
        with subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              start_new_session=True,
                              env=dict(os.environ, TMPDIR=scratch)) as \
                process:
            try:
                output, _ = process.communicate(timeout=seconds)
                status = process.returncode
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                output, _ = process.communicate()
                status = "timeout"
    finally:
        remove_tree(scratch)
    return (status, output.decode("utf-8", "replace"),
            round(time.monotonic() - started, 1))


def class_order(part, capacity):
    """The position classes of PART at CAPACITY, first classes first."""
    if part == "buffer":
        every = list(range(0, capacity, 8))
        first = [capacity - 136, 0, capacity - 8]
    elif part == "window":
        every = list(range(capacity - 512, capacity, 8))
        first = [capacity - 136, capacity - 512, capacity - 8]
    else:
        return [None]
    return first + [position for position in every if position not in first]


def classes_run(part, capacity):
    order = class_order(part, capacity)
    limit = CLASS_LIMIT.get((part, capacity))
    if DEVELOPMENT_CLASSES is not None:
        limit = min(limit or len(order), DEVELOPMENT_CLASSES)
    return order if limit is None else order[:limit]


class Job:
    """One CBMC run."""

    def __init__(self, harness, part, capacity, solver, configuration,
                 position, mode, source=LEAF, group=None, properties=None):
        self.harness, self.part, self.capacity = harness, part, capacity
        self.solver, self.configuration = solver, configuration
        self.position, self.mode, self.source = position, mode, source
        # A run asserts its group: one harness assertion (--property),
        # the leaf's checks and the unwinding assertions (--no-assertions),
        # the unsigned-overflow properties (configuration A), or all.
        self.group, self.properties_filter = group, properties
        self.label = "-".join(str(item) for item in (
            harness, part, capacity, solver, configuration,
            f"p{position}" if position is not None else "all", mode,
            group or "all"))
        self.trace_property = None
        self.result = None

    def command(self, include_dirs):
        defines = [f"-DBE_CBMC_CAPACITY={self.capacity}"]
        defines += [f"-D{name}" for name in PART_DEFINES[self.part]]
        if self.position is not None:
            defines.append(f"-DBE_CBMC_POSITION={self.position}")
        if (self.harness, self.capacity) in READER_TAKE:
            defines.append("-DBE_CBMC_READER_TAKE")
        unwind = ["--unwind", str(self.capacity + 1), "--unwindset",
                  ",".join(f"{loop}:{bound + 1}" for loop, bound in
                           LEAF_LOOPS.items())]
        common = [*defines, *(f"-I{d}" for d in include_dirs), *ARCH,
                  "--drop-unused-functions"]
        sources = [relative(HARNESS_DIR / f"{self.harness}.c"),
                   relative(self.source)]
        solver = list(SOLVERS[self.solver])
        if self.mode == "cover":
            return ["cbmc", *common, "--no-standard-checks", *unwind,
                    "--slice-formula", *solver, "--cover", "assertion",
                    *sources]
        if self.mode == "cover-wraps":
            return ["cbmc", *common, "-DBE_CBMC_COVER",
                    "--no-standard-checks", *unwind, "--slice-formula",
                    *solver, "--cover", "cover", *sources]
        if self.mode == "vacuity":
            return ["cbmc", *common, "-DBE_CBMC_VACUITY",
                    "--no-standard-checks", *unwind, "--slice-formula",
                    *solver, *sources]
        overflow = (["--unsigned-overflow-check"] if self.configuration == "A"
                    else [])
        if self.mode == "show":
            return ["cbmc", *common, *CHECKS, *overflow, *unwind,
                    "--show-properties", *sources]
        command = ["cbmc", *common, *CHECKS, *overflow,
                   "--unwinding-assertions", *unwind, "--slice-formula",
                   *SOLVERS[self.solver]]
        if self.group == "leaf":
            command.append("--no-assertions")
        for identifier in self.properties_filter or ():
            command += ["--property", identifier]
        if self.mode == "trace":
            command += ["--trace", "--property", self.trace_property]
        return command + sources

    def run(self, include_dirs, logs):
        command = self.command(include_dirs)
        units = big(self)
        BIG_RUNS.acquire(units)
        try:
            status, output, seconds = execute(command, REPO, RUN_SECONDS)
        finally:
            BIG_RUNS.release(units)
        log = logs / f"{self.label}.log"
        log.write_text(" ".join(command) + f"\nlimit_seconds={RUN_SECONDS}"
                       f"\nstatus={status}\nseconds={seconds}\n\n" + output,
                       encoding="utf-8")
        self.result = (status, output, seconds)
        return self


def shown_properties(output):
    """The property ids of a --show-properties output."""
    return re.findall(r"^Property (\S+):$", output, re.M)


def overflow_properties(output):
    """The unsigned-overflow property ids of a --show-properties output."""
    ids, current = [], None
    for line in output.split("\n"):
        found = re.match(r"^Property (\S+):$", line)
        if found:
            current = found[1]
        elif current and line.strip().startswith(
                "arithmetic overflow on unsigned"):
            ids.append(current)
            current = None
    return ids


class Units:
    """A counting semaphore whose holders take several units at once."""

    def __init__(self, units):
        self.free = units
        self.condition = threading.Condition()

    def acquire(self, units):
        with self.condition:
            self.condition.wait_for(lambda: self.free >= units)
            self.free -= units

    def release(self, units):
        with self.condition:
            self.free += units
            self.condition.notify_all()


BIG_RUNS = Units(BIG_SLOTS)


def big(job):
    """The units of BIG_SLOTS a run takes: 0 for one that holds no
    4,096-byte buffer's reads or writes at arbitrary positions."""
    if job.capacity != 4096 or job.mode == "show":
        return 0
    if job.harness == "take":
        return 2
    return 1 if job.part in ("buffer", "window") else 0


def run_jobs(jobs, include_dirs, logs, workers):
    """JOBS, the big ones within BIG_SLOTS units beside the rest."""
    heavy = [job for job in jobs if big(job)]
    rest = [job for job in jobs if not big(job)]
    with concurrent.futures.ThreadPoolExecutor(BIG_SLOTS) as big_pool, \
            concurrent.futures.ThreadPoolExecutor(workers) as pool:
        futures = [big_pool.submit(job.run, include_dirs, logs)
                   for job in heavy]
        futures += [pool.submit(job.run, include_dirs, logs) for job in rest]
        for future in futures:
            future.result()
    return jobs


def prepare(out):
    """OUT/cbmc-ring, emptied if it is this tool's, else refused."""
    runs = out / "cbmc-ring"
    if runs.is_symlink() or (runs.exists() and not runs.is_dir()):
        raise Refusal(f"{runs} is a symbolic link or not a directory")
    if runs.is_dir() and any(runs.iterdir()) and \
            not (runs / MARKER).is_file():
        raise Refusal(f"{runs} is not empty and not this tool's")
    shutil.rmtree(runs, ignore_errors=True)
    (runs / "logs").mkdir(parents=True)
    (runs / MARKER).touch()
    return runs


def first_line(command):
    status, output, _ = execute(command, REPO, 60)
    lines = [line for line in output.split("\n") if line.strip()]
    return lines[0].strip() if lines and status == 0 else \
        f"unavailable (exit {status})"


# ----------------------------------------------------------- aggregation
def row_key(job):
    return (job.harness, job.part, job.capacity)


def answered(job):
    """Whether a cover or vacuity run gave an answer (a cover summary; a
    verdict), not a timeout or an error."""
    if job.mode in ("cover", "cover-wraps"):
        return parse_cover(job.result[1])[0] is not None
    return parse_check(job.result[1])[0] in ("successful", "failed")


def aggregate(jobs):
    """Per (harness, part, capacity): the B property table and the A
    overflow sites, from the check runs."""
    rows = {}
    for job in jobs:
        if job.mode != "check":
            continue
        status, output, seconds = job.result
        verdict, properties = parse_check(output)
        if status == "timeout":
            verdict = "timeout"
        row = rows.setdefault(row_key(job), {"B": {}, "A": {}, "runs": []})
        row["runs"].append((job, verdict, properties, seconds))
        table = row[job.configuration]
        for identifier, (state, file, function, line, desc) in \
                properties.items():
            entry = table.setdefault(identifier, {
                "file": file, "function": function, "line": line,
                "desc": desc, "success": set(), "failure": set(),
                "unknown": set()})
            bucket = {"SUCCESS": "success", "FAILURE": "failure"}.get(
                state, "unknown")
            entry[bucket].add((job.solver, job.position))
    return rows


def property_checked(entry, positions):
    """No solver reports it false; for every position class some solver
    reports it successful."""
    if entry["failure"]:
        return False
    return all(any(position == where for _, where in entry["success"])
               for position in positions)


# ---------------------------------------------------------------- mutants
def host_test(mutant, host_flags, directory, counts):
    """(verdict, detail) of ring-test.c with MUTANT as mvp-ring.c: built
    with the host test flags (-Werror), and without -Werror if it does not
    build; passing means exit 0, the PASS line, and the Makefile's
    scenario and assertion counts."""
    directory.mkdir(parents=True, exist_ok=True)
    outcome = []
    for strict in (True, False):
        flags = host_flags if strict else [flag for flag in host_flags
                                           if flag != "-Werror"]
        suffix = "" if strict else "-no-werror"
        binary = directory / f"ring-test{suffix}"
        command = ["gcc", *flags, relative(RING_TEST), relative(mutant),
                   "-o", relative(binary)]
        status, output, _ = execute(command, REPO, RUN_SECONDS)
        (directory / f"build{suffix}.log").write_text(
            " ".join(command) + f"\nstatus={status}\n\n" + output,
            encoding="utf-8")
        if status != 0:
            outcome.append("compile-error" if strict else
                           "compile-error-without-werror")
            continue
        status, output, _ = execute([str(binary)], REPO, RUN_SECONDS)
        (directory / f"run{suffix}.log").write_text(
            f"status={status}\n\n{output}", encoding="utf-8")
        passed = status == 0 and "BE_MVP_RING_CHECK: PASS" in output and \
            f"scenarios={counts[0]}" in output and \
            f"assertions={counts[1]}" in output
        outcome.append(("host-test-pass" if passed else "host-test-fail") +
                       ("" if strict else "-without-werror"))
        if strict:
            break
    detail = ",".join(outcome)
    if outcome[0] == "compile-error":
        return "compile-error", detail
    return ("unobservable" if outcome[-1] == "host-test-pass" else
            "harness-finding"), detail


def keyed(properties):
    """{(function, line, description): status} of a run's properties: the
    key a mutant's run is compared on (its ids may renumber)."""
    return {(function, line, desc): state for state, _, function, line, desc
            in properties.values()}


def leaf_answers(jobs):
    """{(harness, part, capacity, position, group): {solver: seconds}} of
    the unmodified leaf's B runs that answered (SUCCESSFUL or FAILED)."""
    answers = {}
    for job in jobs:
        if job.mode == "check" and job.configuration == "B" and \
                parse_check(job.result[1])[0] in ("successful", "failed"):
            answers.setdefault((job.harness, job.part, job.capacity,
                                job.position, job.group), {})[
                                    job.solver] = job.result[2]
    return answers


def mutant_jobs(mutant, function, shows, answers):
    """A mutant's runs in order, B: at 512 before 4,096; within each, the
    mutated function's harness first, then the other harnesses' parts that
    run once, then their class-split parts (each on its first class). Each
    run uses the solver that answered the unmodified leaf's same run sooner
    (SAT on a tie); a run neither solver answered on the leaf has no
    baseline and is not run."""
    tested = {harness: name for harness, name, _ in HARNESSES_RUN}
    jobs, skipped = [], 0
    for capacity in CAPACITIES:
        order = sorted(((harness, part) for harness, _, parts in
                        HARNESSES_RUN for part in parts),
                       key=lambda item: (tested[item[0]] != function,
                                         item[1] in ("buffer", "window")))
        for harness, part in order:
            heavy = part in ("buffer", "window")
            for job in check_jobs(harness, part, capacity, "sat", "B", shows,
                                  mutant)[:1 if heavy else None]:
                answered_by = answers.get((harness, part, capacity,
                                           job.position, job.group))
                if not answered_by:
                    skipped += 1
                    continue
                solver = min(answered_by, key=lambda name: (
                    answered_by[name], name != "sat"))
                jobs.append(Job(harness, part, capacity, solver, "B",
                                job.position, "check", mutant, job.group,
                                job.properties_filter))
    return jobs, skipped


def run_mutant(record, mutant, include_dirs, host_flags, counts, runs,
               baseline, shows, answers):
    """(id, change, verdict, detail) of one mutant: killed when a run fails
    a property the unmodified leaf's same run does not (a property that
    fails on the leaf, a specification mismatch, kills nothing), or fails
    a safety check the leaf's run does not have."""
    logs = runs / "mutants" / record["id"] / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    change = (f"{record['function']} line {record['line']}: "
              f"{' '.join(json.loads(record['original']).split())} -> "
              f"{' '.join(json.loads(record['replacement']).split())} "
              f"({record['family']}/{record['rule']}) "
              f"file=mutants/generated/{record['id']}/{LEAF.name} "
              f"sha256={record['mutant_sha256']}")
    planned, skipped = mutant_jobs(mutant, record["function"], shows,
                                   answers)
    ran = {"sat": 0, "cvc5": 0}
    timeouts = 0

    def tally():
        return (f"cbmc_runs=sat:{ran['sat']},cvc5:{ran['cvc5']} "
                f"timeouts={timeouts} not_run={skipped}")
    for job in planned:
        job.run(include_dirs, logs)
        ran[job.solver] += 1
        status, output, _ = job.result
        timeouts += status == "timeout"
        verdict, properties = parse_check(output)
        leaf = baseline.get((job.harness, job.part, job.capacity))
        if verdict == "failed" and leaf is not None:
            new = sorted(key for key, state in keyed(properties).items()
                         if state == "FAILURE" and leaf.get(key) !=
                         "FAILURE")
            if new:
                return (record["id"], change, "killed",
                        f"killed-by={job.harness}/{job.part}/{job.capacity}"
                        f"/{job.solver} property={new[0][2]!r} "
                        f"({new[0][0]} line {new[0][1]}) {tally()}")
        if status != "timeout" and "CONVERSION ERROR" in output:
            break
    verdict, detail = host_test(mutant, host_flags,
                                runs / "mutants" / record["id"] / "host",
                                counts)
    return record["id"], change, verdict, f"{detail} {tally()}"


def read_mutation(path):
    return dict(line.split("=", 1) for line in
                path.read_text(encoding="utf-8").splitlines() if "=" in line)


# ------------------------------------------------------------------- run
def check_jobs(harness, part, capacity, solver, configuration, shows,
               source=LEAF):
    """The check runs of one row. Configuration A: the unsigned-overflow
    properties in one run (a class-split part's first classes). B: a
    class-split part one run per class, every property; another part one
    run per harness assertion and one for the leaf's checks and the
    unwinding assertions (CBMC answers each such group in seconds where it
    may not answer them together)."""
    positions = classes_run(part, capacity)
    split = part in ("buffer", "window")
    sample = SAMPLES.get((configuration, solver, capacity))
    chosen = positions[:sample] if split and sample is not None else \
        positions
    if configuration == "A":
        overflow = overflow_properties(
            shows[(harness, part, capacity, "A")].result[1])
        return [Job(harness, part, capacity, solver, "A", position, "check",
                    source, "overflow", overflow) for position in chosen
                ] if overflow else []
    if split:
        return [Job(harness, part, capacity, solver, "B", position, "check",
                    source) for position in chosen]
    shown = shown_properties(shows[(harness, part, capacity, "B")].result[1])
    return [Job(harness, part, capacity, solver, "B", None, "check", source,
                identifier, [identifier]) for identifier in shown
            if identifier.startswith("main.assertion.")] + [
        Job(harness, part, capacity, solver, "B", None, "check", source,
            "leaf")]


def plan(shows):
    """Every run of the unmodified leaf."""
    jobs = []
    for capacity in CAPACITIES:
        for harness, _, parts in HARNESSES_RUN:
            for part in parts:
                positions = classes_run(part, capacity)
                for configuration in CONFIGURATIONS:
                    for solver in SOLVERS:
                        jobs += check_jobs(harness, part, capacity, solver,
                                           configuration, shows)
                for mode in ("cover", "vacuity") + (
                        ("cover-wraps",) if harness == "sequence" else ()):
                    jobs.append(Job(harness, part, capacity, "sat", "B",
                                    positions[0], mode))
    # The long runs first, so that the pools end together: cvc5's on the
    # class-split parts (often its 600 s), then the class-split parts.
    jobs.sort(key=lambda job: (job.part not in ("buffer", "window"),
                               job.solver != "cvc5", job.capacity != 4096))
    return jobs


def run(out, workers, mutants_wanted):
    started = time.monotonic()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    include_dirs, host_flags = target_flags(
        TARGET_DIGESTS.read_text(encoding="utf-8"))
    functions = public_functions(LEAF_HEADER.read_text(encoding="utf-8"))
    check_harness_list(functions, [path.name for path in
                                   HARNESS_DIR.iterdir()])
    counts = host_counts(MAKEFILE.read_text(encoding="utf-8"))
    for tool in ("cbmc", "cvc5", "gcc"):
        if not shutil.which(tool):
            raise Refusal(f"{tool} is not on PATH (run in the verifier "
                          "image)")
    out.mkdir(parents=True, exist_ok=True)
    runs = prepare(out)
    logs = runs / "logs"
    facts = {"cbmc": first_line(["cbmc", "--version"]),
             "cvc5": first_line(["cvc5", "--version"]),
             "gcc": first_line(["gcc", "--version"])}
    print(f"{TAG}: started {stamp} cbmc={facts['cbmc']} workers={workers} "
          "- a bounded model check, never a proof", flush=True)

    # The leaf's loops are the ones bounded above, and no other.
    status, output, _ = execute(
        ["cbmc", *(f"-I{d}" for d in include_dirs), *ARCH,
         "-DBE_CBMC_CAPACITY=512", "--show-loops",
         relative(HARNESS_DIR / "post_words.c"), relative(LEAF)], REPO,
        RUN_SECONDS)
    (logs / "show-loops.log").write_text(output, encoding="utf-8")
    loops = sorted(set(re.findall(r"^Loop (\S+):\n\s+file \S*mvp-ring\.c",
                                  output, re.M)))
    if loops != sorted(LEAF_LOOPS):
        raise Refusal(f"mvp-ring.c's loops are {loops}, not the bounded "
                      f"{sorted(LEAF_LOOPS)}")

    # The property lists: B's (its harness assertions) and A's (the
    # unsigned-overflow properties), per capacity.
    shows = {}
    for capacity in CAPACITIES:
        for harness, _, parts in HARNESSES_RUN:
            for part in parts:
                for configuration in CONFIGURATIONS:
                    shows[(harness, part, capacity, configuration)] = Job(
                        harness, part, capacity, "sat", configuration,
                        class_order(part, capacity)[0], "show")
    run_jobs(list(shows.values()), include_dirs, logs, workers)
    jobs = plan(shows)
    print(f"{TAG}: runs={len(jobs)}", flush=True)
    run_jobs(jobs, include_dirs, logs, workers)
    # A coverage or vacuity run SAT did not answer runs again with cvc5:
    # either qualified solver's answer stands, as for the properties.
    again = [Job(job.harness, job.part, job.capacity, "cvc5", "B",
                 job.position, job.mode) for job in jobs if job.mode in
             ("cover", "cover-wraps", "vacuity") and not answered(job)]
    run_jobs(again, include_dirs, logs, workers)
    jobs += again
    rows = aggregate(jobs)

    # Traces of the unmodified leaf's failures, one per property.
    traces = []
    for key, row in sorted(rows.items()):
        for identifier, entry in sorted(row["B"].items()):
            if entry["failure"]:
                _, position = sorted(entry["failure"],
                                     key=lambda item: (item[0],
                                                       str(item[1])))[0]
                job = Job(key[0], key[1], key[2], "sat", "B", position,
                          "trace", group=identifier)
                job.trace_property = identifier
                traces.append(job)
    run_jobs(traces, include_dirs, logs, workers)

    mutant_rows = []
    if mutants_wanted:
        # The leaf's states per property on each part's first class: SAT's,
        # and cvc5's where SAT gave none.
        baseline = {}
        for solver in SOLVERS:
            for job in jobs:
                if job.mode == "check" and job.configuration == "B" and \
                        job.solver == solver and job.position == \
                        class_order(job.part, job.capacity)[0]:
                    entry = baseline.setdefault(
                        (job.harness, job.part, job.capacity), {})
                    for key, state in keyed(parse_check(
                            job.result[1])[1]).items():
                        entry.setdefault(key, state)
        answers = leaf_answers(jobs)
        mutant_dir = runs / "mutants" / "generated"
        status, output, _ = execute(
            [sys.executable, "-I", "-B", relative(MUTATE), relative(LEAF),
             "--all-functions", "--seed", hex(MUTANT_SEED), "--count",
             str(MUTANT_COUNT), "--out", relative(mutant_dir)], REPO,
            RUN_SECONDS)
        (runs / "mutants" / "generate.log").write_text(output,
                                                       encoding="utf-8")
        if status != 0:
            raise Refusal(f"mutate.py failed: {output.strip()[-300:]}")
        records = [(read_mutation(path / "mutation.txt"), path / LEAF.name)
                   for path in sorted(mutant_dir.iterdir()) if path.is_dir()]
        with concurrent.futures.ThreadPoolExecutor(
                workers) as pool:
            mutant_rows = list(pool.map(
                lambda item: run_mutant(item[0], item[1], include_dirs,
                                        host_flags, counts, runs, baseline,
                                        shows, answers), records))
    return write_records(runs, rows, jobs, traces, mutant_rows, facts,
                         stamp, started, include_dirs, host_flags,
                         functions)


# --------------------------------------------------------------- records
def trace_text(output):
    """The counterexample of a --trace run: from its first state."""
    found = re.search(r"^(Trace for |Counterexample:)", output, re.M)
    if not found:
        return "(no trace in the output)"
    text = output[found.start():]
    tail = re.search(r"^\*\* \d+ of \d+ failed", text, re.M)
    return text[:tail.start()] if tail else text


def row_lines(rows):
    """properties.txt's run rows, and the counted property rows: (lines,
    total, checked, open lines, the A sites)."""
    lines, open_lines, sites = [], [], {}
    total = checked = 0
    for (harness, part, capacity), row in sorted(rows.items()):
        positions = classes_run(part, capacity)
        every = class_order(part, capacity)
        complete = len(positions) == len(every)
        for configuration in CONFIGURATIONS:
            for solver in SOLVERS:
                runs_here = [item for item in row["runs"] if
                             item[0].configuration == configuration and
                             item[0].solver == solver]
                if not runs_here:
                    continue
                failed = sorted({identifier for _, _, properties, _ in
                                 runs_here for identifier, values in
                                 properties.items() if values[0] ==
                                 "FAILURE"})
                verdicts = sorted({verdict for _, verdict, _, _ in
                                   runs_here})
                completed = all(verdict in ("successful", "failed") for
                                verdict in verdicts)
                if configuration == "B":
                    run_positions = {item[0].position for item in runs_here}
                    yes = completed and not failed and (
                        solver == "cvc5" or run_positions == set(every))
                else:
                    yes = completed and all(classify_wrap(
                        row["A"][identifier]["file"],
                        row["A"][identifier]["desc"])[0] == "intended-wrap"
                        for identifier in failed)
                classes = (f" classes={len(runs_here)}/{len(every)}" if
                           part in ("buffer", "window") else "")
                lines.append(
                    f"row function={harness} part={part} capacity={capacity}"
                    f" solver={solver} configuration={configuration}"
                    f"{classes} properties="
                    f"{len(set().union(*(item[2] for item in runs_here)))} "
                    f"failed="
                    f"{len(failed)} seconds="
                    f"{round(sum(item[3] for item in runs_here), 1)} "
                    f"verdicts={','.join(verdicts)} checked="
                    f"{'yes' if yes else 'no'}" +
                    (f" failed_properties={';'.join(failed)}" if failed
                     else ""))
        not_run = 0
        for identifier, entry in sorted(row["B"].items()):
            total += 1
            if property_checked(entry, positions) and complete:
                checked += 1
                continue
            reading = READINGS.get((harness, entry["desc"]))
            if entry["failure"]:
                reason = reading[0] if reading else "unclassified"
            elif not complete:
                not_run += 1
                continue
            else:
                reason = "no-success (a timeout or an error)"
            open_lines.append(f"open function={harness} part={part} "
                              f"capacity={capacity} property={identifier} "
                              f"reason={reason} desc={entry['desc']}")
        if not_run:
            open_lines.append(f"open function={harness} part={part} "
                              f"capacity={capacity} properties={not_run} "
                              f"reason=classes-not-run ({len(positions)} of "
                              f"{len(every)} run; every property of the "
                              f"part not failed on a class run)")
        for identifier, entry in sorted(row["A"].items()):
            total += 1
            kind = classify_wrap(entry["file"], entry["desc"])
            if entry["failure"]:
                sites.setdefault((entry["file"], entry["function"],
                                  entry["line"], entry["desc"]),
                                 (kind, set()))[1].add(
                                     f"{harness}/{part}/{capacity}")
            if not entry["failure"] and not entry["success"]:
                open_lines.append(f"open function={harness} part={part} "
                                  f"capacity={capacity} property="
                                  f"{identifier} reason=no-success "
                                  f"(configuration A) desc={entry['desc']}")
            elif not entry["failure"] or kind[0] == "intended-wrap":
                checked += 1
            else:
                open_lines.append(f"open function={harness} part={part} "
                                  f"capacity={capacity} property="
                                  f"{identifier} reason=wrap-{kind[0]}-"
                                  f"{kind[1]} desc={entry['desc']}")
    return lines, total, checked, open_lines, sites


def reproduce(runs, function, source, host_flags):
    """The lines of a reading's host-test reproducer: SOURCE written to
    runs/defect-FUNCTION/, built with the host test flags against the
    unmodified leaf, and run."""
    directory = runs / f"defect-{function}"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{function}-reproducer.c"
    path.write_text(source, encoding="utf-8")
    binary = directory / f"{function}-reproducer"
    command = ["gcc", *host_flags, relative(path), relative(LEAF), "-o",
               relative(binary)]
    status, output, _ = execute(command, REPO, RUN_SECONDS)
    lines = [f"reproducer={relative(path)} (scratch; built with "
             "verify/target-digests.txt's host_test_flags and the "
             "unmodified mvp/src/mvp-ring.c)", f"build_status={status}"]
    if status != 0:
        return lines + output.strip().splitlines()[-5:]
    status, output, _ = execute([relative(binary)], REPO, RUN_SECONDS)
    return lines + [f"exit={status}"] + output.strip().splitlines()


def write_records(runs, rows, jobs, traces, mutant_rows, facts, stamp,
                  started, include_dirs, host_flags, functions):
    head = ["# MVP M8 Leaf B: CBMC bounded model check of mvp-ring.c "
            "(planning/mvp-m8-plan.md, D-8): a bounded model check, never "
            "a proof",
            f"specification=planning/mvp-m8-specifications.md revision=1 "
            f"accepted={SPECIFICATION_COMMIT} sha256={SPECIFICATION_SHA256}",
            f"leaf=mvp/src/mvp-ring.c sha256={sha256(LEAF.read_bytes())}",
            f"started={stamp} cbmc={facts['cbmc']} cvc5={facts['cvc5']}"]
    property_lines, total, checked, open_lines, sites = row_lines(rows)
    wrap_lines = [f"site file={pathlib.Path(file).name} function={function} "
                  f"line={line} class={kind[0]} kind={kind[1]} expression="
                  f"{desc.split(' in ', 1)[-1]} flagged_in="
                  f"{','.join(sorted(where))}" for (file, function, line,
                                                     desc), (kind, where) in
                  sorted(sites.items())]
    cover_lines, vacuity_lines = [], []
    coverage_ok = vacuity_ok = True
    first = {}
    for job in jobs:
        if job.mode in ("cover", "cover-wraps", "vacuity"):
            first.setdefault((job.mode, row_key(job), job.position),
                             []).append(job)
    for tried in first.values():
        job = next((item for item in tried if answered(item)), tried[-1])
        status, output, seconds = job.result
        where = (f"function={job.harness} part={job.part} capacity="
                 f"{job.capacity}" + (f" class={job.position}" if
                                      job.position is not None else "") +
                 f" solver={job.solver}" + "".join(
                     f" {item.solver}={item.result[0]}"
                     f"@{item.result[2]}s" for item in tried
                     if item is not job))
        if job.mode in ("cover", "cover-wraps"):
            covered, goals, cover = parse_cover(output)
            ok = covered is not None and covered == goals and goals > 0
            coverage_ok &= ok
            missed = sorted(desc for state, _, desc in cover.values() if
                            state != "SATISFIED")
            cover_lines.append(
                f"{job.mode} {where} criterion="
                f"{'cover' if job.mode == 'cover-wraps' else 'assertion'} "
                f"covered={covered}/{goals} seconds={seconds} ok="
                f"{'yes' if ok else 'no'}" + (
                    f" status={status}" if status != 0 else "") + (
                    f" not_covered={';'.join(missed)}" if missed else ""))
        elif job.mode == "vacuity":
            verdict, _ = parse_check(output)
            ok = verdict == "failed"
            vacuity_ok &= ok
            vacuity_lines.append(
                f"vacuity {where} assert(0)_after_the_assumptions="
                f"{'fails' if ok else verdict} seconds={seconds} "
                f"assumptions_satisfiable={'yes' if ok else 'not-shown'}")
    defects, reproduced = {}, {}
    for job in traces:
        entry = rows[row_key(job)]["B"][job.trace_property]
        reading = READINGS.get((job.harness, entry["desc"]),
                               ("unclassified", "not read: see the trace",
                                None))
        if reading[2] and job.harness not in reproduced:
            reproduced[job.harness] = reproduce(runs, job.harness,
                                                reading[2], host_flags)
        defects.setdefault(job.harness, []).append(
            f"## {job.trace_property}: {entry['desc']}\n"
            f"part={job.part} capacity={job.capacity}" +
            (f" class={job.position}" if job.position is not None else "") +
            f"\nreason={reading[0]}\nreading: {reading[1]}\n"
            f"log=logs/{job.label}.log\n\n" + trace_text(job.result[1]))
    for function, parts in sorted(defects.items()):
        host = reproduced.get(function)
        (runs / f"defect-{function}.txt").write_text(
            "\n".join(head) + "\n# The row's failures on the unmodified "
            "leaf, each a CBMC counterexample (SAT); the leaf is not "
            "changed (planning/mvp-m8-plan.md, stop condition 2: the "
            "human's).\n\n" + ("## host-test reproducer\n" + "\n".join(
                relative_text(line) for line in host) + "\n\n" if host
                else "") + "\n\n".join(parts) + "\n",
            encoding="utf-8")
    killed = sum(row[2] == "killed" for row in mutant_rows)
    unobservable = sum(row[2] == "unobservable" for row in mutant_rows)
    findings = sum(row[2] == "harness-finding" for row in mutant_rows)
    compile_errors = sum(row[2] == "compile-error" for row in mutant_rows)
    open_count = total - checked
    result = "CHECKED" if open_count == 0 and total > 0 else "OPEN"
    if HARNESSES_RUN != HARNESSES or DEVELOPMENT_CLASSES is not None:
        result = "PARTIAL"
        head.append("only=" + ",".join(name for name, *_ in HARNESSES_RUN) +
                    f" classes={DEVELOPMENT_CLASSES}")
    final = (f"{TAG}: {result} functions={len(functions)} capacities="
             f"{','.join(map(str, CAPACITIES))} properties={total} checked="
             f"{checked} open={open_count} solvers={','.join(SOLVERS)} "
             f"mutants={len(mutant_rows)} killed={killed} unobservable="
             f"{unobservable} harness-findings={findings} coverage="
             f"{'ok' if coverage_ok else 'not-ok'} vacuity="
             f"{'ok' if vacuity_ok else 'not-ok'}")
    seconds = round(time.monotonic() - started)

    def write(name, lines):
        (runs / name).write_text("\n".join(head + [f"seconds={seconds}"] +
                                          lines) + "\n", encoding="utf-8")
    write("properties.txt", property_lines + open_lines + [final])
    write("wrap-sites.txt", [
        "# Configuration A's flagged sites: intended-wrap (index-difference: "
        "a difference of two index values; index-advance: one of the four "
        "advances section 5 names, cursor + 8, cursor + 16, cursor + 16 + "
        "i, cursor + size, Revision 1's R1-9) or a finding (index-advance: "
        "another index value plus an offset; other: anything else)"] +
        wrap_lines)
    write("coverage.txt", cover_lines)
    write("vacuity.txt", vacuity_lines)
    write("mutants.txt", [
        f"mutants={len(mutant_rows)} seed={MUTANT_SEED:#x} killed={killed} "
        f"unobservable={unobservable} compile_error={compile_errors} "
        f"harness_findings={findings}"] + [
        f"mutant id={identifier} verdict={verdict} change={change} {detail}"
        for identifier, change, verdict, detail in mutant_rows])
    write("sequence.txt", [line for line in property_lines + open_lines +
                           cover_lines + vacuity_lines if
                           "function=sequence" in line])
    write("assumptions.txt", assumptions(facts, include_dirs, host_flags))
    write("transcription.txt", transcription())
    (runs / "summary.json").write_text(json.dumps(
        {"schema": "be-mvp-cbmc-ring-v1", "specification_sha256":
         SPECIFICATION_SHA256, "result": result, "properties": total,
         "checked": checked, "open": open_count, "mutants": len(
             mutant_rows), "killed": killed, "unobservable": unobservable,
         "harness_findings": findings, "compile_errors": compile_errors,
         "coverage": coverage_ok, "vacuity": vacuity_ok, "seconds": seconds,
         "started": stamp}, indent=1) + "\n", encoding="utf-8")
    print(final, flush=True)
    return 0


TRANSCRIPTION = """\
# How each row of section 5 is checked (mvp/verify/cbmc/ring/), and where each clause Revision 1 corrected is transcribed
common safety -> CBMC's --bounds-check, --pointer-check, --signed-overflow-check, --undefined-shift-check, and --unwinding-assertions on the leaf in every configuration B run; configuration A adds --unsigned-overflow-check and classifies each flagged site (wrap-sites.txt)
reset -> reset.c: both index values 0; the pads unchanged
init -> init.c: the result iff the row's conditions, the cursor, the limit, the peak, failed, no index or buffer byte written
record_bytes -> record_bytes.c: 16 + ((length + 7) & ~7) for length <= 256, else 0, every u64 length
post -> post.c: the result iff the row's conditions (two cases named: the cursor at or past the published head), the cursor, the peak, the index lines, the failed view (scalar part); every buffer byte (buffer part, by position class)
room -> room.c: a well-formed tail's answer relationally (the largest payload that fits; 0 if none), writes nothing; a malformed tail, a reader's, or a failed view: 0 and failed
post_words -> post_words.c: as post with the words little-endian; count > 32 refused
publish -> publish.c: the head set to the cursor, 1; otherwise 0 and failed; no buffer byte
acquire -> acquire.c: limit := h and h - cursor (two cases named: the cursor at or past the released tail); otherwise 0 and failed; a writer's or failed view 0; no index or buffer byte
take -> take.c: EMPTY, RECORD, or INVALID from a model computed from [cursor, limit) alone; the record, the cursor, the failed view; no index or buffer byte
release -> release.c: the tail set to the cursor, 1; otherwise 0 and failed
peak -> peak.c: the writer view's peak; writes nothing
taken -> taken.c: a writer view not failed: the reader's tail, the view unchanged; 0 otherwise
published -> published.c: a writer view not failed: the head; 0 otherwise
record_word -> record_word.c: the little-endian word when 8*index + 8 <= length, else 0
sequence -> sequence.c: post, publish, acquire, take, release across the windows' wraps: the record byte for byte, and the writer's free bytes
R1-1, R1-2, R1-3 -> section 4 (Leaf A), not this arm's
R1-4 -> init.c: domain <= 1 in the conditions of the result; head and tail each absent or valid (nondeterministically), non-null in the conditions; peak == head - tail on 1
R1-5 -> init.c: limit == cursor on 1 (the view's own index)
R1-6 -> post.c, post_words.c: the tail well formed, (t & 7) == 0 and limit - t <= C, then cursor - t <= C and cursor - t + record_bytes(length) <= C, in the result's conditions (and the payload, or the words, non-null when length, or count, > 0); room.c: well formed is (t & 7) == 0 and limit - t <= C alone, the row's parenthesis, and a record of payload n fits when cursor - t <= C and cursor - t + record_bytes(n) <= C (the well-formed case asserted in two cases: cursor - t at most C, or more)
R1-7 -> acquire.c: r the reader's index line at the call; the head accepted when (h & 7) == 0, h - r <= C, and cursor - r <= h - r
R1-8 -> taken.c: a writer view not failed returns the reader's tail from its index line with the view unchanged; 0 for an absent, failed, or reader's view
R1-9 -> sequence.c: free_after == free_before + size, the free bytes C - (cursor - tail) of the writer view just before and after the release (no room call); wrap-sites.txt: the advances cursor + 8, cursor + 16, cursor + 16 + i, and cursor + size classified intended-wrap (cbmc-ring.py's ADVANCES), every other advance a finding"""


def transcription():
    """transcription.txt's lines: the mapping and the harnesses'
    digests."""
    return TRANSCRIPTION.splitlines() + [
        f"file {relative(path)} sha256={sha256(path.read_bytes())}"
        for path in sorted(HARNESS_DIR.iterdir()) if path.is_file()]


def assumptions(facts, include_dirs, host_flags):
    unwind = ",".join(f"{loop}:{bound + 1}" for loop, bound in
                      LEAF_LOOPS.items())
    return [
        "# D-7 item 4: the assumption inventory of Leaf B's bounded model "
        "check",
        f"tool cbmc={facts['cbmc']} solvers=MiniSAT (CBMC's SAT back end) "
        f"and cvc5 ({facts['cvc5']}) through --cvc5: the two qualified "
        "pairs (M8-5); CBMC with Z3 did not qualify and is not run. A "
        "solver's answer is trusted as reported (solver trust): no proof "
        "object is checked.",
        "memory_model CBMC's: a byte-precise object model with pointers as "
        "(object, offset), no concurrency (--mm sc unused: one thread), "
        "volatile objects read as ordinary memory (no --nondet-volatile): "
        "the peer's index is arbitrary at the call, not between two reads "
        "of one call.",
        "integer_model --arch riscv64: LP64, little-endian, unsigned char; "
        "unsigned arithmetic modulo 2^64 (wraparound defined, the "
        "configuration A sites classified: the index differences and the "
        "four index advances section 5 names, R1-9, intended); the leaf's "
        "_Static_asserts hold under it (the leaf type-checks).",
        f"include_dirs={' '.join(include_dirs)} (verify/target-digests.txt;"
        " the leaf and its headers unchanged, digests.py --check)",
        "checks B: --bounds-check --pointer-check --signed-overflow-check "
        "--undefined-shift-check --unwinding-assertions; A: B's program "
        "with --unsigned-overflow-check, its unsigned-overflow properties "
        "only.",
        f"bounds loops unwound to their bounds 8, 256, 32, CBMC's count "
        f"one more: --unwindset {unwind}; the harnesses' own loops "
        "--unwind capacity+1; every unwinding assertion checked (B).",
        "runs each CBMC run limited to 600 s (a timeout is a non-result; "
        "the run's session is killed, its cvc5 with it); a part's harness "
        "assertions one run each (--property) and the leaf's checks with "
        "the unwinding assertions one run (--no-assertions), where CBMC "
        "answers each in seconds and may not answer them together; "
        "--slice-formula on every run (CBMC drops the definitions outside "
        "the checked properties' cone of influence; assumptions kept); "
        "--drop-unused-functions. These options and --arch, --cover, "
        "--unwindset are CBMC's documented ones, beyond the qualification's "
        "command form (the checks, --unwind 5, --cvc5): trusted as CBMC's "
        "(tool trust).",
        "solvers a part run once (all but the class-split ones) runs with "
        "both solvers; a class-split part runs B with SAT on every class "
        "run, and samples: A with SAT on the first three classes, A with "
        "cvc5 on the first class at 512 (not at 4096), B with cvc5 on the "
        "first class at both capacities (cvc5 answered no class-split run "
        "within 600 s in the trials); such a row counts SAT's answers.",
        "coverage --cover assertion (CBMC rewrites the assertions as "
        "assumptions and reports each assertion's location reachable or "
        "not; no unwinding assertions in that mode) on each part's first "
        "class; vacuity: the harness's assertions removed by "
        "-DBE_CBMC_VACUITY and assert(0) after the assumptions, which must "
        "fail; each with SAT, and again with cvc5 where SAT gave no answer "
        "within 600 s (either qualified solver's answer stands).",
        "capacities 512 and 4096; payloads 0 to 256 bytes (any u64 length "
        "offered); words 0 to 32 (any u64 count offered); the own index "
        "any multiple of 8, near 2^64 included; the peer's index any u64 "
        "at the call; types any u64, domain any u32, role writer or reader "
        "(init: any u32).",
        "position_classes post, post_words, and take's buffer conclusions: "
        "one run per own-index position (the low bits; the other bits "
        "arbitrary), every position at 512, the first three at 4096 "
        "(budget: the row stays OPEN); the sequence: every position of "
        "[C - 512, C) at both capacities (the row's windows).",
        "views built by be_mvp_ring_init, perhaps after the side's earlier "
        "calls (a writer: one empty record posted, perhaps published; a "
        "reader: an acquire of any head, for release and acquire at 512 "
        "perhaps a take; at 4096 not, a bound), perhaps failed since; a "
        "view init refused is checked on its own path. The buffer "
        "harnesses restate the buffer, capacity, index lines, and cursor "
        "init stored (the premise that init stores what it is given; the "
        "cursor is section 5's). post's and post_words's buffer parts take "
        "the view as init built it, perhaps failed; their scalar parts add "
        "the prefix's states (the result, cursor, peak, failed view, and "
        "index lines asserted there), whose buffer bytes are not asserted "
        "(a bound: one buffer byte at an arbitrary position there was not "
        "answered in 600 s at 4096).",
        "ownership_premise (section 5, stated, not checked): one writer "
        "view and one reader view per ring; the writer writes only the "
        "buffer and the head, the reader only the tail; each view in its "
        "own memory.",
        "fences outside: the callers' fence w,w / fence r,r / fence r,w "
        "(mvp-ring.h) are not modelled; stage 1's L2 to L4 and the litmus "
        "tests are their evidence.",
        "header_encoding section 5 names a record's header fields, not "
        "their bytes: the harnesses read type at 0, domain at 1, length "
        "16-bit at 2, reserved 32-bit at 4, time 64-bit at 8, "
        "little-endian (mvp-ring.c's HEADER_* offsets).",
        "reads take's 'reads only positions in [cursor, limit)' is checked "
        "as a dependence: its result, record, and view equal a model "
        "computed from those bytes alone (no read hook: an unused read "
        "would not show).",
        f"mutants mutate.py seed {MUTANT_SEED:#x}, {MUTANT_COUNT}, every "
        "function of mvp-ring.c; configuration B, each harness part on its "
        "first position class, both capacities, each run with the solver "
        "that answered the unmodified leaf's same run sooner (SAT on a "
        "tie; a run neither answered is not run: no baseline); killed: a "
        "property failing that the leaf's same run does not fail; the host "
        f"test (ring-test.c, {' '.join(host_flags)}) the equivalence "
        "oracle.",
        "not_covered U-04 (the rings as the monitor runs them, with "
        "fences, on two harts), U-11 (memory ordering), compiled execution "
        "(the compilers and the executor; class (d)), concurrency during a "
        "call, and anything beyond the bounds above.",
        "claim per call, for any peer index, under the ownership premise; "
        "a bounded model check, never a proof (S3-C's Q36).",
    ]


# --------------------------------------------------------------- self-test
SUCCESSFUL = """\
CBMC version 6.8.0 (ad933aa-dirty) 64-bit x86_64 linux
** Results:
mvp/src/mvp-ring.c function be_mvp_ring_publish
[be_mvp_ring_publish.pointer_dereference.1] line 244 dereference failure: pointer NULL in ring->head->value: SUCCESS

mvp/verify/cbmc/ring/publish.c function main
[main.assertion.1] line 42 publish: a writer view not failed: the head set to cursor, 1: SUCCESS

** 0 of 2 failed (1 iterations)
VERIFICATION SUCCESSFUL
"""
FAILED = """\
** Results:
mvp/verify/cbmc/ring/taken.c function main
[main.assertion.1] line 43 taken: a reader view not failed: the tail as it stands, the view unchanged: FAILURE
[main.assertion.2] line 46 taken: 0 for an absent, failed, or writer's view: SUCCESS

** 1 of 2 failed (3 iterations)
VERIFICATION FAILED
"""
TIMEOUT = """\
CBMC version 6.8.0 (ad933aa-dirty) 64-bit x86_64 linux
Running propositional reduction
"""
COVERED = """\
** coverage results:
[main.coverage.1] file mvp/verify/cbmc/ring/init.c line 51 function main init: returns 1 iff the row's conditions, else 0: SATISFIED
[main.coverage.2] file mvp/verify/cbmc/ring/init.c line 54 function main init: on 1 the cursor is the own index's value: FAILED

** 1 of 2 covered (50.0%)
"""
SHOWN = """\
Property be_mvp_ring_init.overflow.1:
  file mvp/src/mvp-ring.c line 129 function be_mvp_ring_init
  arithmetic overflow on unsigned - in head_value - tail_value
  !overflow("-", be_u64, head_value, tail_value)

Property be_mvp_ring_init.pointer_dereference.2:
  file mvp/src/mvp-ring.c line 130 function be_mvp_ring_init
  dereference failure: pointer NULL in ring->buffer
"""
HEADER_TEXT = """\
/* be_mvp_ring_fake(x) in a comment is not a declaration */
void be_mvp_ring_reset(volatile struct be_mvp_ring_index *head,
\t\t       volatile struct be_mvp_ring_index *tail);
int be_mvp_ring_init(struct be_mvp_ring *ring, be_u8 *buffer);
be_u64 be_mvp_record_word(const struct be_mvp_record *record, be_u64 index);
"""


def self_test():
    results = []

    def case(name, passed, detail=""):
        results.append(bool(passed))
        print(f"{'ok  ' if passed else 'FAIL'} {name}"
              f"{'' if passed else ': ' + str(detail)[-400:]}")

    def refused(name, action, wanted):
        try:
            action()
        except Refusal as why:
            case(name, wanted in str(why), why)
        else:
            case(name, False, "not refused")

    verdict, properties = parse_check(SUCCESSFUL)
    case("a successful run parses", verdict == "successful" and len(
        properties) == 2 and properties["main.assertion.1"][0] == "SUCCESS"
        and properties["main.assertion.1"][2] == "main", properties)
    verdict, properties = parse_check(FAILED)
    case("a failed run names its failing property", verdict == "failed" and
         [desc for state, *_, desc in properties.values() if state ==
          "FAILURE"] == ["taken: a reader view not failed: the tail as it "
                         "stands, the view unchanged"], properties)
    verdict, properties = parse_check(TIMEOUT)
    case("a killed run is an error with no property", verdict == "error"
         and not properties, (verdict, properties))
    covered, goals, cover = parse_cover(COVERED)
    case("a cover report parses", (covered, goals) == (1, 2) and cover[
        "main.coverage.2"][0] == "FAILED", (covered, goals, cover))
    case("a run without a cover summary has none", parse_cover(SUCCESSFUL)[
        :2] == (None, None))
    probe = Job("take", "scalar", 4096, "sat", "B", None, "cover")
    probe.result = ("timeout", TIMEOUT, 600.0)
    again = Job("take", "scalar", 4096, "cvc5", "B", None, "vacuity")
    again.result = (10, FAILED, 9.0)
    case("a cover run without a summary has no answer, a failed vacuity "
         "run has one", not answered(probe) and answered(again))
    case("the unsigned-overflow properties are found",
         overflow_properties(SHOWN) == ["be_mvp_ring_init.overflow.1"],
         overflow_properties(SHOWN))
    for description, file, wanted in (
            ("arithmetic overflow on unsigned - in head_value - tail_value",
             "mvp/src/mvp-ring.c", ("intended-wrap", "index-difference")),
            ("arithmetic overflow on unsigned - in ring->limit - tail",
             "mvp/src/mvp-ring.c", ("intended-wrap", "index-difference")),
            ("arithmetic overflow on unsigned - in head - ring->cursor",
             "mvp/src/mvp-ring.c", ("intended-wrap", "index-difference")),
            ("arithmetic overflow on unsigned - in ring->capacity - used",
             "mvp/src/mvp-ring.c", ("finding", "other")),
            ("arithmetic overflow on unsigned - in size - "
             "(unsigned long int)16u", "mvp/src/mvp-ring.c",
             ("finding", "other")),
            ("arithmetic overflow on unsigned + in ring->cursor + "
             "(unsigned long int)8u", "mvp/src/mvp-ring.c",
             ("intended-wrap", "index-advance")),
            ("arithmetic overflow on unsigned + in ring->cursor + "
             "(unsigned long int)16u + index", "mvp/src/mvp-ring.c",
             ("intended-wrap", "index-advance")),
            ("arithmetic overflow on unsigned + in ring->cursor + size",
             "mvp/src/mvp-ring.c", ("intended-wrap", "index-advance")),
            ("arithmetic overflow on unsigned + in ring->limit + "
             "(unsigned long int)8u", "mvp/src/mvp-ring.c",
             ("finding", "index-advance")),
            ("arithmetic overflow on unsigned + in ring->cursor + "
             "(unsigned long int)24u", "mvp/src/mvp-ring.c",
             ("finding", "index-advance")),
            ("arithmetic overflow on unsigned - in ring->cursor - tail",
             "mvp/verify/cbmc/ring/post.c", ("finding", "harness-site"))):
        case(f"the wrap classifier: {description.split(' in ')[1]} in "
             f"{pathlib.Path(file).name}", classify_wrap(file, description)
             == wanted, classify_wrap(file, description))
    names = public_functions(HEADER_TEXT)
    case("mvp-ring.h's declarations are read, comments apart", names == [
        "be_mvp_ring_reset", "be_mvp_ring_init", "be_mvp_record_word"],
        names)
    real = public_functions(LEAF_HEADER.read_text(encoding="utf-8"))
    files = [path.name for path in HARNESS_DIR.iterdir()]
    try:
        check_harness_list(real, files)
        case("the committed harnesses are mvp-ring.h's fourteen functions "
             "and the sequence", len(real) == 14)
    except Refusal as why:
        case("the committed harnesses are mvp-ring.h's fourteen functions "
             "and the sequence", False, why)
    refused("a function without a harness",
            lambda: check_harness_list(real + ["be_mvp_ring_extra"], files),
            "no harness for be_mvp_ring_extra")
    refused("a harness for a function the header does not declare",
            lambda: check_harness_list([name for name in real if name !=
                                        "be_mvp_ring_peak"], files),
            "a harness for be_mvp_ring_peak")
    refused("a harness file no row names",
            lambda: check_harness_list(real, files + ["extra.c"]),
            "harness files no row names: extra.c")
    refused("a missing harness file",
            lambda: check_harness_list(real, [name for name in files if
                                              name != "take.c"]),
            "harness files missing: take.c")
    case("the classes of a whole buffer are every position, first classes "
         "first", class_order("buffer", 512)[:3] == [376, 0, 504] and
         sorted(class_order("buffer", 512)) == list(range(0, 512, 8)),
         class_order("buffer", 512)[:4])
    case("the sequence's classes are the window [C - 512, C)",
         sorted(class_order("window", 4096)) == list(range(3584, 4096, 8)))
    case("every row of the readings names a harness", all(
        harness in {name for name, *_ in HARNESSES} for harness, _ in
        READINGS))
    case("every reading is a reason, a reading, and a reproducer or none",
         all(len(value) == 3 and (value[2] is None or "main(void)" in
                                  value[2]) for value in READINGS.values()))
    dirs, host = target_flags(TARGET_DIGESTS.read_text(encoding="utf-8"))
    case("the target digests give the include directories and host flags",
         "mvp/src" in dirs and "-Werror" in host, (dirs, host))
    refused("target digests without the flags",
            lambda: target_flags("files=0\n"), "no include_dirs")
    # A timed-out command's children (CBMC's cvc5) do not outlive it.
    def running(pid):
        try:
            state = pathlib.Path(f"/proc/{pid}/stat").read_text(
                encoding="utf-8", errors="replace")
        except OSError:
            return False
        return state.rsplit(")", 1)[-1].split()[0] != "Z"
    status, output, _ = execute(["/bin/sh", "-c", "sleep 60 & echo $!; "
                                 "wait"], REPO, 1)
    child = output.split()[0] if output.split() else ""
    deadline = time.monotonic() + 5
    while child.isdigit() and running(child) and \
            time.monotonic() < deadline:
        time.sleep(0.1)
    case("a timeout kills the command's children", status == "timeout" and
         child.isdigit() and not running(child), (status, output))
    # A job's temporary files (cvc5's) do not outlive it (mvp/README.md,
    # item 118): its TMPDIR is a directory of its own, mode 0700, under
    # the run's tmp root, gone when it times out and when it finishes.
    root = pathlib.Path(tempfile.mkdtemp(prefix="cbmc-ring-self-test-"))
    writes = ('printf "%s %s\\n" "$TMPDIR" "$(stat -c %a "$TMPDIR")"; '
              'head -c 65536 /dev/zero >"$TMPDIR/smt2_dec_problem_1"; ')
    for name, tail, limit, wanted in (
            ("a timed-out job's temporary directory, its file in it, is "
             "removed", "exec sleep 60", 1, "timeout"),
            ("a finished job's temporary directory is removed", "true", 60,
             0)):
        status, output, _ = execute(["/bin/sh", "-c", writes + tail], REPO,
                                    limit, root)
        given, mode = (output.split() + ["", ""])[:2]
        case(name, status == wanted and given and
             pathlib.Path(given).parent == root and mode == "700" and
             not os.path.lexists(given) and not any(root.iterdir()),
             (status, output, sorted(path.name for path in root.iterdir())))
    remove_tree(root)
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
    parser.add_argument("--jobs", type=int)
    parser.add_argument("--no-mutants", action="store_true")
    parser.add_argument("--only")
    parser.add_argument("--classes", type=int)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv[1:])
    if args.self_test == args.run or (args.self_test and (
            args.out or args.jobs or args.no_mutants or args.only or
            args.classes)):
        parser.error("give --run [--out DIR] [--jobs N] [--no-mutants] "
                     "[--only NAME,...], or --self-test")
    if args.only:
        names = args.only.split(",")
        unknown = sorted(set(names) - {name for name, *_ in HARNESSES})
        if unknown:
            parser.error(f"no harness {', '.join(unknown)}")
        global HARNESSES_RUN
        HARNESSES_RUN = tuple(row for row in HARNESSES if row[0] in names)
    if args.classes is not None:
        if args.classes < 1:
            parser.error("--classes must be at least 1")
        global DEVELOPMENT_CLASSES
        DEVELOPMENT_CLASSES = args.classes
    if args.self_test:
        return self_test()
    workers = args.jobs or max(2, (os.cpu_count() or 6) // 3)
    if workers < 1:
        parser.error("--jobs must be at least 1")
    try:
        return run((args.out or REPO / "build" / "mvp" / "verify").resolve(),
                   workers, not args.no_mutants)
    except (OSError, Refusal) as why:
        print(f"{TAG}: FAIL {why}", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
