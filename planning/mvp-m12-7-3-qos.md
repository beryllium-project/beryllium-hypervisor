<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M12-7.3, `Smqosid` and `Smsdqosid` in the Sail model: packet and record

This page is the packet and the record of M12-7.3, the third sub-step of
M12-7, the Supervisor Domains model in Sail, which the [M12 plan's
revision 1](mvp-m12-plan-revision-1.md) adds to the [M12
plan](mvp-m12-plan.md). It writes the two hart extensions of the
specification's chapter 9, `Smqosid` and `Smsdqosid`, to its frozen
release `v0.9`, in the lane's clone of the Sail RISC-V model, on the
model's `Ssqosid` and on [M12-7.2](mvp-m12-7-2-smsd.md)'s `Smsd`.

The page names the exit commits and records the readings. It describes
what the model's chapter 9 covers, and the options for the behaviours
that the text leaves open, with the four questions that they raise. It
corrects a fault in the model's `Ssqosid`, lists what is not covered,
and says what was run. The suite's results on Spike's pull request, on
the model's pull request 1727, and on M12-4's walk wait for those pull
requests' authors (the plan's section 6). They are kept outside this
repository, for the project's internal records.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. His sign-off of that
commit on the public `main` is M12-7.3's acceptance. It rests on the
revision's, M12-7.1's, and M12-7.2's acceptance, which come before it in
the same range.

**His direction for the Sail work**, at 2026-11-20T00:37Z: "proceed with
the remaining sail work, we will push all of it and seek advice on LLM
policy for sail project. we will use it locally in any case." At 00:50Z
he pushed M12-7.2's branch, `m12-smsd` at `ccd4418f`, to his public fork
of the model, <https://github.com/xjamesmorris/sail-riscv>. The lane
pushes nothing; at this exit it has moved its local `m12-smsd` forward to
M12-7.3's exit, for him to push again. The code is offered to no one:
the lane has drafted, for him to send, a request for the model's
maintainers' advice on AI-assisted code, in their list's thread on
their contribution guidelines.

The page has no entry yet in the planning site's navigation or index;
the owner session adds them.

## The exit commits

| Repository | Branch | Commit | Tree |
| --- | --- | --- | --- |
| The clone of the Sail RISC-V model (the plan's section 5) | `m12-qos`, and `m12-smsd` moved to it | `1e2d2aca1df07cbf2f52f09722422ee6212105e4` | `3123262d6e30e20ba687323e3248425fc5b1b050` |
| The tests' repository | `main` | `9371bc564ced4dc883fdeb9e304aed22a7e19110` | `b804eadf5334792d672e0ce8f97545c6ac68ec92` |

The model's branch adds four commits to M12-7.2's exit `ccd4418f`, which
stands on the model's `master` at `dda378c6`, the revision's base:

| Commit | Subject |
| --- | --- |
| `e2099971b576c3b87f10b934bbde1af74f4c6725` | Fix the positions of srmcfg's RCID and MCID |
| `86981127f73747ef60e7cd404e722b63fc769f96` | Add the Smqosid extension's mrmcfg |
| `46d69cb98a5bc2a5a4eacedecfae4bcf0be6fe2c` | Add the Smsdqosid extension's mnrmcfg and msdcfg fields |
| `1e2d2aca1df07cbf2f52f09722422ee6212105e4` | Constrain srmcfg's identifiers under Smsdqosid |

The tests' repository adds two commits to M12-7.2's exit `41c2bac6`:
`3ddcc341`, a group of cases for chapter 9, and `9371bc56`, questions
12 to 15 and the readings of them.

Each commit is authored and committed as the responsible human, with
Q3's trailer (`Assisted-by: GitHub Copilot CLI 1.0.114-0 (model
claude-opus-5.5)`) and no sign-off. Each of the model's commits had its
tree type-checked with the model's options for Sail before it was
committed. The clone's `origin` still has its push URL disabled; its
one other remote is his fork, which he added to push. The tests'
repository has no remote.

Both are also kept as bundles outside this repository:

| Bundle | SHA-256 | Needs |
| --- | --- | --- |
| `sail-riscv-m12-7-3-1e2d2aca1df0.bundle` (branches `m12-smsd` and `m12-qos`) | `bf04e1e68f90fcb7d878102e94af4b858f381bc5b46d3a8a3efb2a6d6d796bdc` | The model's `dda378c6`, which its repository serves |
| `sd-tests-m12-7-3-9371bc564ced.bundle` | `96a1da0170f5e1f479ca7982ea89bbd7f9a432280899d27808c9dcddfa22a3d1` | Nothing: the whole history |

## Readings (rules 1 and 11), 2026-11-20 (UTC)

| What | Read |
| --- | --- |
| The Sail model's `master` | `ec5200bd` (2026-11-19), nine commits after the base. None changes `Ssqosid`, `Smsd`, the list of extensions, or the project file; one adds options elsewhere in the configuration. The base stays `dda378c6`: moving it would mean running M12-7.2 again, for nothing that this step uses |
| Its contribution rules, and `LLM_POLICY_ALIGNMENT.md` | `CONTRIBUTING.md` is the same at `ec5200bd` as at `dda378c6`, so the Sail model's row stands |
| Its maintainers' policy discussion | The `tech-golden-model` thread of 2026-11-09, by its feed: no message since the two of 2026-11-13. No decision |
| Competing work | The model's pull requests and issues hold nothing on `Smqosid`, `Smsdqosid`, `mrmcfg`, or `mnrmcfg`, and no report of the fault below. Stop 3 does not arise |
| Spike's pull request 2336, and the model's 1727 | Unchanged: open, heads `67df9c24` and `fc08e2d3` |
| The specification | `v0.9`, chapter 9, and chapter 3's `msdcfg`. Its `main` at `8f8b5d5b` changes neither chapter's text but for headings and cross-references. Its issues on chapter 9 that bear on the model: 231 and 237 (now in the text), 283, 287 (now in the text), 291 and 292 (closed by their author, unanswered), 295, 296, 297, and 299, all closed |

A citation N:L below is line L of the text's chapter N at `v0.9`, as in
the code.

## Chapter 9 in the model

- **The fault in `Ssqosid`.** Since the model gained `Ssqosid` (its
  pull request 379, merged 2026-01-16), its `srmcfg` has had `RCID` in
  bits 27:16 and `MCID` in bits 11:0. The ratified privileged
  specification has them the other way round (`supervisor.adoc` at
  `20250508`, lines 2341-2365), as chapter 9 has `mrmcfg` and
  `mnrmcfg`. The first commit swaps them. It comes first because the
  other three rest on it; the lane has drafted an issue to the model
  for him to file, which notes that he could also send the two-line fix
  himself, written by hand.
- **`Smqosid`.** `mrmcfg` (0x381), M-mode only, with `RCID`, `MCID`,
  and `QRID` (9:53-115). Its fields are WARL (9:60-63), and the text
  gives them no widths: each has a configured number of bits, the
  least significant first, as `Ssqosid` does, and the rest read as zero;
  12, 12, and 4 bits by default. Issue 297 was answered that they need
  not match `srmcfg`'s. It resets to zero, as 9:74-80 suggests for
  `RCID` and `QRID`.
- **`Smsdqosid`.** It needs `Smsd` and `Ssqosid`. `mnrmcfg` (0x781),
  M-mode only, WARL (9:132-135), with `RCID` and `MCID` of `srmcfg`'s
  lengths, as issue 296 was answered, and a configured `QRID`; it
  resets to zero. `msdcfg` gains `SSRM`, `SSMM`, `SRL`, and `SML`
  (3:269-280, 9:164-188): `SRL` and `SML` are WARL from 0 to `RCIDLEN`
  and `MCIDLEN`, and below them while `SSRM` or `SSMM` is 1 (9:180-181,
  9:186-187, issues 231 and 237); a larger value written leaves the
  largest legal one. `SSRM` and `SSMM` are independent (issue 283).
  `SIDN` stays read-only zero (M12-7.5). Each write of `srmcfg` that
  the ranges constrain leaves an `RCID` and an `MCID` in the range that
  `msdcfg` gives (9:177-188).
- **The IDs that accompany requests** (9:194-221). The model has no
  shared resource controllers to receive them, so it computes them only
  for its unit tests, which include the text's example (9:223-239).
- **The ISA string.** With `--enable-experimental-extensions`,
  `--print-isa-string` and `--print-device-tree` show `smqosid` and
  `smsdqosid` in all three places, for RV64 and RV32, among the other
  `Sm` extensions in alphabetical order; without it, both are absent.

### The options

Each behaviour that the text leaves open is an option, under
`extensions.Smqosid` or `extensions.Smsdqosid` in the model's
configuration, with the lane's reading as its default. The tests'
repository names each other reading, and the suite was run under each.

| Option | Default | Other values | Text | Question |
| --- | --- | --- | --- | --- |
| `Smqosid.rcid_length`, `.mcid_length`, `.qrid_length` | 12, 12, 4 | 0 to 12, 0 to 12, 0 to 4 | 9:60-63 | Left to the implementation |
| `Smsdqosid.qrid_length` | 4 | 0 to 4 | 9:132-162 | 14 |
| `Smsdqosid.range_scope` | `Smsdqosid_SD_Writes`: the ranges constrain only the writes made below M-mode, as issue 295 was answered | `Smsdqosid_All_Writes`: every write; `Smsdqosid_Held`: every write, and a write of `msdcfg` zeroes an ID held outside its new range | 9:177-190 | 12 |
| `Smsdqosid.out_of_range_write` | `Smsdqosid_Keep`: the field keeps its value | `Smsdqosid_Clamp`: it takes the largest value in the range | None | 13 |

Question 15, `msdcfg`'s value at reset, needs no option yet: the model
resets it to zero, which leaves software below M-mode only `RCID` 0 and
`MCID` 0 until M-mode sets `SRL` and `SML`.

## The questions

The tests' repository's `questions.md` gains questions 12 to 15, for the
specification's authors through the responsible human, as M12-2's:

12. Which writes of `srmcfg` the ranges constrain: the text calls them
    `srmcfg`'s legal values, binding M-mode's writes and what
    `srmcfg` holds (9:177-190), while the answer to issue 295 says that
    they bind only the supervisor domain's writes, and are not.
13. What a write outside a range leaves in the field.
14. The widths of `mnrmcfg`'s fields: issue 296's answer for `RCID` and
    `MCID`, and `QRID`, which issue 291 asked about without an answer.
15. `msdcfg`'s value at reset, on which software written for `Ssqosid`
    alone depends.

Each cites the text and the issues. The lane has drafted two issues
from them, for him to file during the specification's public review
(12 and 13; 14 and 15).

## What it does not cover

- The QoS register interfaces of the capacity and bandwidth controllers
  (9:269-464), which are devices outside the hart, as the I/O MPT
  checker is (the revision).
- The IDs that accompany requests, beyond the unit tests (above).
- `Smsdia`, `Smsdedbga`, and `Smsdetrca`, which [M12-7.4 and
  M12-7.5](mvp-m12-7-4-7-5-not-modelled.md) record as not modelled.

## Pull request 1727

Its files were not open while M12-7.3 was written (the revision's
decision 3). After the four commits were made, a search of its head for
chapter 9's registers, to word `questions.md`, printed two lines of its
`smsdid_regs.sail`: its `msdcfg`'s `SSRM` field, at bit 22 as the text
has it, and the start of a comment. Nothing was written from them, and
the model's code has not changed since; `questions.md` rests on the
suite's runs, which show that it has no `mrmcfg` or `mnrmcfg`.

## What was run

On 2026-11-20, through the lane's gate for heavy work, on CPUs 0 to 31,
with no network. The model and the suite were built in M12-7.1's image
(`localhost/m12-sd-env:560de8f6ed2e`), the model from a clean tree with
the model's pull-request CI's options, save warnings-as-errors and
clang-tidy:

| From (UTC) | At | What | Result |
| --- | --- | --- | --- |
| 01:12 | `1e2d2aca`, the exit | The model's own tests (`ctest`), its unit tests among them | All 9,245 passed; the unit-test program's sixteen tests each pass, among them the five new ones |
| 01:29 | `1e2d2aca` | The suite at the tests' repository's `3ddcc341`, under the defaults | RV64: 677 cases, 533 pass and 144 open. RV32: 267 cases, 208 pass and 59 open. None fails. Against M12-7.2's exit: 31 new cases on each, 25 passing and 6 open; of the others, only `reg.msdcfg.nzr` records a new value, `msdcfg` now having fields, and it still passes |
| 01:30 | `1e2d2aca` | The suite under each of M12-7.2's ten readings | Each changes the same cases, in the same way, as at M12-7.2's exit; none changes a chapter 9 case or fails |
| 01:34 | `1e2d2aca` | The suite under chapter 9's three readings (the tests' `9371bc56`), and `q1-fault-machine` again | Each changes only the cases of its question; none fails. `q1-fault-machine` gives the same tables as at 01:30 |
| 01:30 to 01:37 | Spike's pull request; the model's 1727; M12-4's walk | The same suite | None has `mrmcfg` or `mnrmcfg`: each gives the tables held for it before, with two new not-run cases on each XLEN |

The results on the lane's model are its own, so section 6 does not hold
them back. The tables of the other three show those implementations'
results, so they wait for their authors (section 6; Q9), outside this
repository. These are directed tests and a model's own tests, under
emulation, of an unmerged implementation of a frozen specification
(section 8).

## Soft limits (the revision's, and section 9's)

- `Smqosid` and `Smsdqosid` in Sail, with their unit tests and the fix
  to `Ssqosid`: 363 added lines of the revision's 400, by `git diff
  --numstat` from M12-7.2's exit (10 lines removed). The model's
  branch as a whole adds 1,256 lines to `dda378c6`.
- The environment, the driver, and the runners (section 9): 780 added
  lines of 1,000, counted as at M12-7.2.

## Publication gate

Run before this exit:

- the clone of the model: `publication-gate scan-tree --advisory` on
  the new and changed files of each commit, and on the four commits'
  messages and identities, gave `PASS`, with no advisory item; and
  `publication-gate check --repo . --remote xjamesmorris m12-smsd
  --advisory`, which scans what a push of the moved branch to his
  public fork would publish, gave `PASS` (exit 0), with no advisory
  item;
- the tests' repository: `publication-gate audit --repo . --all-refs
  --advisory` gave `PASS` (exit 0), with no advisory item;
- this repository's branch `m12`, including the commit that adds this
  page: `publication-gate check --repo . --remote origin m12` gave
  `PASS` (exit 0).

A pass is not approval to publish.

## What this step does not do

It sends nothing to anyone, adds no remote, and pushes nothing. It
offers the code to no one. It makes no claim: the plan's section 8
holds, and the code is not a reference model (section 8). It touches
no board, and runs only under emulation. It names no Beryllium unit a
supervisor domain (S3-D's stop (k)).

## Status record

```text
mvp_m12_7_3=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main
mvp_m12_7_3_exit=sail-riscv-clone;m12-qos-and-m12-smsd;1e2d2aca1df07cbf2f52f09722422ee6212105e4;tree-3123262d6e30e20ba687323e3248425fc5b1b050;over-m12-7-2-ccd4418f;four-commits
mvp_m12_7_3_exit_tests=tests-repository;main;9371bc564ced4dc883fdeb9e304aed22a7e19110;tree-b804eadf5334792d672e0ce8f97545c6ac68ec92;cases-3ddcc341;questions-12-15
mvp_m12_7_3_bundles=sail-riscv-m12-7-3-1e2d2aca1df0.bundle;sha256-bf04e1e68f90fcb7d878102e94af4b858f381bc5b46d3a8a3efb2a6d6d796bdc;needs-dda378c6;sd-tests-m12-7-3-9371bc564ced.bundle;sha256-96a1da0170f5e1f479ca7982ea89bbd7f9a432280899d27808c9dcddfa22a3d1
mvp_m12_7_3_text=v0.9-9211c4cf-frozen;chapter-9;chapter-3-msdcfg
mvp_m12_7_3_readings=2026-11-20;rule-1;rule-11;sail-master-ec5200bd-base-kept-dda378c6;tech-golden-model-thread-no-decision;no-competing-work
mvp_m12_7_3_direction=2026-11-20T00:37Z;push-all-sail-work;seek-sail-llm-policy-advice;m12-smsd-ccd4418f-pushed-by-him-00:50Z-to-his-public-fork
mvp_m12_7_3_scope=ssqosid-srmcfg-rcid-mcid-fix;smqosid-mrmcfg;smsdqosid-mnrmcfg;msdcfg-ssrm-ssmm-srl-sml;srmcfg-ranges;request-ids-unit-tests-only;isa-string-device-tree
mvp_m12_7_3_options=smqosid-lengths;smsdqosid-qrid_length-q14;range_scope-q12;out_of_range_write-q13
mvp_m12_7_3_questions=q12-which-writes-the-ranges-constrain;q13-write-outside-the-range;q14-mnrmcfg-widths-qrid;q15-msdcfg-reset
mvp_m12_7_3_runs=1e2d2aca-model-own-tests-9245-of-9245-passed;suite-rv64-677-533-pass-144-open-rv32-267-208-pass-59-open-none-fails;thirteen-readings-each-changes-only-its-question's-cases-none-fails;spike-pr-1727-walk-no-chapter-9-held-for-their-authors
mvp_m12_7_3_pr_1727=files-not-open-while-written;two-lines-seen-after-the-commits;nothing-written-from-them
mvp_m12_7_3_soft_limits=chapter-9-363-of-400-lines;environment-780-of-1000-lines
```
