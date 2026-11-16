<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M12-3, the directed tests: packet and record

This page is the packet and the record of M12-3, the directed tests, a
work package of the [M12 plan](mvp-m12-plan.md) (its section 6). It is
step 2 of the plan's section 1: directed tests that run unchanged on
each implementation that supports the case.

The page names the step's exit commit in the lane's tests' repository
and records the readings that the plan's rule 1 requires. It says how
the suite follows section 7's design rules, and what was run. The
runs' result tables wait for their authors (the plan's section 6): they
are kept outside this repository, for the project's internal records.

M12-3 ran together with M12-2, the questions
([its page](mvp-m12-2-questions.md)).

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. His sign-off of that
commit on the public `main` is M12-3's acceptance (the plan's section
6). The lane's own commits stay unsigned until he offers them.

**The review point before M12-4 is reached** (section 6; stop 9).
M12-2's questions are drafted, and M12-3's groups have run on the two
implementations that M12-3 runs before M12-4. M12-4, the table walk,
does not start until the responsible human says whether first contact
comes before it. M12-1's page records a fact for that decision: the
Sail model's roadmap no longer lists the extension as pull request
1727's author's.

The page has no entry yet in the planning site's navigation or index;
a later commit adds them.

## The exit commit

| Repository | Branch | Commit | Tree |
| --- | --- | --- | --- |
| The tests' repository (the plan's section 5) | `main` | `6594ad624345f215db5cdb35fddb58bc9fb0c40a` | `e9e785919867fd955b3d7f2c56621b0837fe2180` |

M12-3 shares this commit, and its bundle,
`sd-tests-m12-2-3-6594ad624345.bundle` (SHA-256
`739bb815ec7f37abc72cf3bf67489761fc1973e96f9106b097cd0d6d6612e2b4`),
with M12-2. M12-2's page lists the four commits since M12-1's exit.
The last of them changes three citations and no expected result. The
repository is still local, with no remote.

## Readings (rule 1), 2026-11-16 (UTC)

Read at the step's exit, from 23:52 to 23:57. M12-3 started on the
readings of the same items that M12-1's page records, made at 21:20 the
same day.

| What | Read | Since M12-1's reading |
| --- | --- | --- |
| The Sail model's pull request 1727 | Open; head `fc08e2d3`; no review | Unchanged |
| The Sail model's contribution rules | `CONTRIBUTING.md` at `master` `a2ad4b56` | Unchanged |
| Spike's pull request 2336 | Open; head `67df9c24`; no review | Unchanged |
| Spike's contribution rules | At `master` `11848099`: no contribution guide; `LICENSE` a three-clause BSD licence | Unchanged |
| The specification and the fences' encodings | As M12-2's page records | |

Stop 3 (the same work posted by someone else) is not met. The Sail
model's, Spike's, and the architectural test suite's issues and pull
requests were searched for "smmpt", "smsd", and "supervisor domain".
The search found only Spike's pull request 2336 and an unrelated test
of an interrupt controller (`riscv/riscv-arch-test` pull request 1646,
merged 2026-06-05). Stop 4 (the work built on changes) is not met: both
heads are as pinned.

Rule 11: `LLM_POLICY_ALIGNMENT.md`'s rows for the two implementations
(M12-1) and the specification's repository (M12-2) were rechecked. No
change was needed.

**Readings of the implementations' files (rule 4).** No code or test
of either implementation was open while the tests were written. No test
is modelled on another implementation's test. What each implementation
does was learned by running the suite. The only files of theirs that
were read are build and CI files, read for the environment and the
runners. None of their text is copied or paraphrased:

- the Sail model at `fc08e2d3`:
  - `CMakeLists.txt`, `test/CMakeLists.txt`, and the `CMakeLists.txt`
    of `test/first_party` and of the unit tests;
  - the CI and full-test workflows under `.github`, and its Sail setup
    action;
  - `cmake/project_version.cmake`, and the `CMakeLists.txt` of its two
    fetched dependencies;
  - the warnings-as-errors lines of `c_emulator/CMakeLists.txt`;
- Spike at `67df9c24`:
  - pull request 2336's change to `riscv/riscv.mk.in`;
  - its CI workflow, `apt-packages.txt`, and `ci-tests/build-spike`
    and `ci-tests/test-spike`;
  - a search of `Makefile.in`.

Pull request 2336's own test, `riscv/smmpt43.t.cc`, was run in M12-1
and was never read. Each pull request's description was read for its
declared scope (section 8).

## The suite

Section 7's design rules, as the exit commit meets them:

- **An M-mode harness.** For each case, the harness builds the memory
  protection tables, and the page tables where the case needs them. It
  then programs `mmpt`, fences, and enters S, U, VS, or VU mode to make
  one access. Its trap handler records what the access did, as a 64-byte
  record in a signature that the implementation dumps at the end of the
  run.
- **One source, several runners.** One source, with the same expected
  results, is built for each implementation. A runner for each
  implementation supplies its exit device (HTIF's `tohost`) and its
  configuration.
- **The fences' encodings are a build parameter**, as section 7 reads
  S3-D.4. `v0.9.0` gives the CSR numbers of `mmpt` and `msdcfg`, but not
  the fences' funct7 values. The default is the values that
  `riscv/riscv-opcodes` pull request 389 proposes, 0x19 and 0x1b, an
  answer outside the text. Each implementation's values were learned by
  running it. Spike's disassembler, at the head of its pull request,
  names 0x5f and 0x3f. The Sail model, at the head of its pull request,
  executes 0x19 and 0x1b. Each result names the values that it used.
- **Each case cites its text**: a line of the specification at
  `v0.9.0` (`4:199` is line 199 of `chapter4.adoc`), or of the
  privileged specification at `20250508` for a rule that this one
  relies on and does not state.
- **Specified or open.** A specified case is judged; it relies on
  nothing that the text leaves free, and a fence follows every table
  change in it. An open case reports what the hart did. A case that a
  hart cannot run is recorded as not run.
- **The groups**, section 7's seven:
  - register and instruction behaviour;
  - activation and privilege;
  - the permission matrix;
  - the walk's structure;
  - translation and the hypervisor extension;
  - identifiers and fences;
  - delegation.

  The harness finds what the hart provides: the hypervisor extension,
  each table mode (Q7), Svinval, and Sv39. The permission matrix and the
  walk's structure run once for each table mode that the hart supports.
  The other groups run once, under the first table mode that it
  supports.

**What the suite does not cover yet:**

- Translation runs on RV64 only, through Sv39. There are no RV32 cases
  through Sv32 with Smmpt34.
- The groups other than the permission matrix and the walk run under
  one table mode per hart.
- The interrupt part (`Smsdia`), the quality-of-service part
  (`Smsdqosid`, `Smqosid`), and the I/O tables are not covered (section
  6 leaves them out of M12-4 too).

## What was run

On 2026-11-16 from 23:48, in M12-1's image
(`localhost/m12-sd-env:3064213f1120`), at the exit commit, with a clean
tree and no network: the suite was built for each set of encodings and
run, RV64 and RV32, on:

| Implementation | Commit | Configuration | Encodings (funct7) |
| --- | --- | --- | --- |
| Spike, pull request 2336 | `67df9c2461705d52808c80af25c692533c04b5f8` | `--isa=rv64gch_smmpt43_svinval`; `--isa=rv32gch_svinval` | 0x5f, 0x3f |
| The Sail RISC-V model, pull request 1727 | `fc08e2d3d2f3d72b35764197c09683a6c50e65af` | `--enable-experimental-extensions`, with and without `--rv32`; otherwise its default configuration | 0x19, 0x1b |

These are directed tests on emulators, of unmerged implementations of a
draft specification (section 8). The model has no hypervisor
extension, so the cases in VS and VU mode run on Spike only. The
emulator is not run before its series' next version (M12-5).

A table of results was made for each implementation and XLEN, under
section 8's rules. Each names the implementation, its commit, its
configuration and encodings, the draft that it was written to, and its
declared scope, and classes every difference. The tables wait for the
two pull requests' authors (section 6; Q9). They are kept outside this
repository, for the project's internal records; a later record commit
here may carry them, once they have been shown. The tables are made
again at M12-4's exit (section 6).

## Soft limits (section 9)

Added lines by `git diff --numstat`, from the repository's first commit:

| Lane | Lines | Limit |
| --- | --- | --- |
| The directed tests and their harness (`tests/`) | 1,544 | 2,500 |
| The environment, the driver, and the runners (`env/`) | 700 (549 at M12-1's exit) | 1,000 |

Counted apart: the generated `env/opam.lock` and `env/image.record` (334
lines); the Markdown, `README.md` (150) and `questions.md` (231); and
the licences' SPDX texts (BSD-2-Clause, 9; CC-BY-4.0, 156). The Sail
clone has no commit of the lane.

## Publication gate

Run on each repository that the step changed, before its exit:

- the tests' repository: `publication-gate audit --repo . --all-refs`
  gave `PASS` (exit 0), with no advisory finding;
- this repository's branch `m12`, including the commit that adds this
  page: `publication-gate audit --repo . m12` gave `PASS` (exit 0).

A pass is not approval to publish.

## What this step does not do

It sends nothing to anyone, adds no remote, and pushes nothing. It makes
no claim: the plan's section 8 holds. It touches no board, and runs only
under emulation (S3-D's stop (m)). It names no Beryllium unit a
supervisor domain (S3-D's stop (k)).

## Status record

```text
mvp_m12_3=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main
mvp_m12_3_exit=tests-repository;main;6594ad624345f215db5cdb35fddb58bc9fb0c40a;tree-e9e785919867fd955b3d7f2c56621b0837fe2180;shared-with-M12-2
mvp_m12_3_bundle=sd-tests-m12-2-3-6594ad624345.bundle;sha256-739bb815ec7f37abc72cf3bf67489761fc1973e96f9106b097cd0d6d6612e2b4
mvp_m12_3_suite=seven-groups;table-modes-a-parameter;specified-and-open;encodings-a-build-parameter;translation-rv64-only
mvp_m12_3_runs=spike-pr-2336-67df9c24;sail-model-pr-1727-fc08e2d3;rv64-and-rv32;results-held-for-their-authors
mvp_m12_3_readings=2026-11-16;rule-1;rule-4-file-readings-recorded;rule-11-rechecked
mvp_m12_3_review_point=before-M12-4-reached;stop-9
mvp_m12_3_stops=none-other-than-stop-9
mvp_m12_3_soft_limits=tests-1544-of-2500;environment-700-of-1000
```
