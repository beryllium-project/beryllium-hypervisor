<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M12-4, the table walk: packet and record

This page is the packet and the record of M12-4, the table walk for the
Sail RISC-V model, a work package of the [M12 plan](mvp-m12-plan.md)
(its section 6). It is step 3 of the plan's section 1: the walk, built
on the model's open pull request 1727 for the registers and the fence
instructions.

The page names the step's exit commit in the lane's clone of the model.
It records the readings that the plan's rules 1 and 11 require, and the
responsible human's decisions that bear on the step. It describes the
walk, lists what it leaves to pull request 1727's author, and says what
was run. The runs' results wait for their authors (the plan's section
6): they are kept outside this repository, for the project's internal
records.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. His sign-off of that
commit on the public `main` is M12-4's acceptance (the plan's section
6). The lane's own commits stay unsigned until he offers them.

**The walk is offered to no one.** The Sail model's maintainers are
weighing a policy that would decline AI-written code (below: stop 2).
The walk waits for that policy, and for the responsible human's first
contact with pull request 1727's author.

**The plan's stop 9 applies again at this exit.** Work is ready to show
and first contact has not been made, so no further step starts until
the responsible human decides.

## The exit commit

| Repository | Branch | Commit | Tree |
| --- | --- | --- | --- |
| The clone of the Sail RISC-V model (the plan's section 5) | `m12-smmpt-walk` | `25069b79f91bda765aca013acf4fb0fa75f0123b` | `f7eb6bb353a460cb14656bf480ff7e50cf738493` |

The branch stands on pull request 1727's head,
`fc08e2d3d2f3d72b35764197c09683a6c50e65af`, and adds two commits:

| Commit | Subject |
| --- | --- |
| `58bc24d866ec977ea35d411a8d2e0beb909518c7` | Add the lookup steps of the Smsdid memory protection table |
| `25069b79f91bda765aca013acf4fb0fa75f0123b` | Check accesses below M-mode against the Smsdid memory protection table |

Each is authored and committed as the responsible human. Each carries
Q3's trailer (`Assisted-by: GitHub Copilot CLI 1.0.114-0 (model
claude-opus-5.5)`) and no sign-off. The clone has no remote of the
lane's, and its push URL is disabled.

The exit commit is also kept as a bundle outside this repository,
`sail-riscv-m12-4-25069b79f91b.bundle`, SHA-256
`5645ccd3ed41be3c0cd5a03bfdc1b5e719995b975288b27c1e67aad80a0d697e`. It
needs pull request 1727's head, which the model's repository serves.

The suite that the walk was run with is the tests' repository at
`2ed52ccffddaedf2117f2d40eb380ee8efe9b52f` (tree
`22e258cb003e85beff9a92aa50341932b6db1bf5`), one commit after M12-3's
exit. That commit pins the suite's text to the specification's frozen
release `v0.9`, where each line that it cites states the same rule as at
`v0.9.0`; it changes no expected result. Its bundle is
`sd-tests-m12-4-2ed52ccffdda.bundle`, SHA-256
`c1839b5875575714ca56662589a0e57026aac2eece3eb03324f7a49a82ed8931`.

## Readings (rules 1 and 11), 2026-11-18 and 2026-11-19 (UTC)

| What | Read |
| --- | --- |
| Pull request 1727 | Open; head `fc08e2d3`; no review; last updated 2026-05-27. Its one commit has no `Signed-off-by`, and GitHub reports it as conflicting with `master` |
| The Sail model's contribution rules | `CONTRIBUTING.md` at `master` `dda378c6`, the same file as read for M12-1: generative-AI use disclosed, "PR text" included; a Developer Certificate of Origin sign-off on every commit, enforced since `29e6158f` (2026-09-05); more intrusive extension pull requests may wait until the specification is "Ratification-Ready" |
| The model's list, tech-golden-model | A thread of 2026-11-09, "Updating contribution guidelines for the Sail Golden Model", started by one of the model's maintainers. The maintainers are contemplating guidelines "roughly based on the Servo policy", or QEMU's. Its rationale says that a sign-off for code assisted by AI tools "is untenable, and such PRs are likely to be rejected". Feedback was asked for within two weeks |
| The specification | Release `v0.9` (`9211c4cf`, 2026-11-17), its freeze; RISC-V International's dashboard has the freeze approval due 2026-11-28 |
| Competing work | The model's pull requests and issues hold none other for the extension, and pull request 1727's author's fork no other branch for it. Elsewhere: the QEMU series is at v8, the OpenSBI series at its RFC v7, and Spike has pull request 2336 |

Stop 3 (the same work posted by someone else) and stop 4 (the work built
on changes) are not met. Stop 5 is not met: `v0.9` changes no rule that
the walk or a case relies on.

Rule 11: `LLM_POLICY_ALIGNMENT.md`'s row for the Sail model was
rechecked. The written policy that it records is unchanged.

**The rule 1 readings missed the model's list at first.** Until
2026-11-19 they read the destination's repository only. The
responsible human found the thread; the readings now include each
destination's list.

## The responsible human's decisions

All were taken in the lane's session, by the plan's stop 9 and stop 2,
and are recorded here with their reasons.

1. **The review point before M12-4 (stop 9).** On 2026-11-17 he chose
   contact first, with the reason "as recommended". The
   recommendation was that D27 rules out a parallel walk, and that one
   message to pull request 1727's author would settle whether one was
   in progress. That moved first contact before step 3, as section 6
   allows.
2. **Stop 2, met on 2026-11-19 by the thread above.** He first paused
   the walk until the maintainers settle their policy. Later that day
   he chose to prepare it locally, in the plan's original order (walk
   first, under `first_contact=work_first`), and to offer it to no one
   until the policy is settled and he has written to the author. The
   reasons: the contacts wait on him, the walk waits on nothing
   outside, and no walk was found in progress. He was told two things
   when he chose:
   - if the maintainers decline AI-written code, the walk cannot be
     offered to the model, though it still serves as a cross-check of
     the tests;
   - if he might write a walk himself later, he should not read this
     one, since a rewrite after reading it could count as derived from
     AI output.
3. **First contact, as of this record.** Not made. The questions are to
   go to the specification's authors as his own issues, with the
   tests' repository private for now, which Q2's default would have
   made public at first contact. A comment for pull request 1727's
   author, drafted by the lane at his request, departed from rule 7's
   "his own writing". It was not posted, and he writes his own.

## The walk

The walk follows the specification at `v0.9`, chapter 4, "MPT access
type permissions lookup process", for the four modes, Smmpt34 on RV32
and Smmpt43, Smmpt52, and Smmpt64 on RV64. It adds two files to the
model's `extensions/Smsdid/` and one unit-test file, and changes two of
the model's own files:

- `smmpt_types.sail`: each mode's geometry, and steps 2 to 7 of the
  lookup as pure functions;
- `smmpt.sail`: the walk, which reads each MPTE and applies those
  steps, and `mptCheck`, the check of an access;
- `unit_tests/test_smmpt.sail`: five unit tests of the pure functions,
  on MPTEs made up for each case;
- `sys/mem.sail`: a forward declaration of `mptCheck`, and its call in
  `phys_access_check` for each access that PMP allows;
- `riscv.sail_project`: the new files' modules.

Pull request 1727's own files are left to their author (Q11). The order
of the two commits is the one that section 6 asks for: the pure
functions with their unit tests first, then the hook into the memory
path. Each builds, and the model's own tests pass at each.

**Choices made by judgement**, where the text leaves room:

1. A reserved XWR encoding in any tuple of a leaf MPTE raises an access
   fault, whether or not the access selects it. That is the plain
   reading of step 3 ("any bits or encodings that are reserved ... set
   within _mpte_"), and the answer of the specification's issue 325.
   The suite's case for it is open (M12-2's question 4).
2. Bit 11 of an RV64 NAPOT leaf, drawn "0" where Smmpt34's is
   "Reserved", is taken as reserved (M12-2's question 5).
3. An MPTE read is an implicit M-mode access, checked by PMP (4:231),
   and by the PMAs as a read of a page-table entry would be. An MPTE
   outside main memory raises an access fault.
4. An access is checked in each page that it touches.
5. The model keeps no MPT cache: each access walks the table as it is
   in memory. So `MFENCE.PA` and `MINVAL.PA`, which do nothing in the
   model, need no change for the walk.
6. A refused access raises the access fault that the model raises for
   PMP, so `medeleg` delegates it as it delegates any access fault.
   Whether that is intended is M12-2's question 1.

**Implicit accesses.** The model's page-table walker reads and writes
page-table entries through the same physical check. So they are checked
against the table as loads and stores, and a fault is reported for the
original access type, as 4:175 to 4:180 require.

**Readings of the model's files (rule 4).** Only the model's own files
were read: pull request 1727's six files; `sys/mem.sail`,
`sys/pma.sail`, `sys/vmem.sail`, `sys/vmem_ptw.sail`,
`pmp/pmp_control.sail`, `core/types.sail`, `core/vmem_types.sail`,
`core/mem_addrtype.sail`, `core/phys_mem_interface.sail`, the prelude,
the project file, and `unit_tests/test_mstatus.sail`; and
`CONTRIBUTING.md`, `CODE_STYLE.md`, `doc/AddingExtensions.md`,
`model/CMakeLists.txt`, and `test/unit_tests/`. No other
implementation's code or tests were open while the walk was written:
not Spike's, not the QEMU series', and not any other.

**What M12-4 does not include:** the interrupt part (`Smsdia`), the
quality-of-service part, and the I/O tables (section 6). The model at
pull request 1727's base has no hypervisor extension, so VS-stage and
G-stage translation, which 4:175 also covers, cannot arise in it. The
model gained one on 2026-08-20 (its pull request 1769), after that
base. A rebase onto `master` brings guest modes, two-stage translation,
and HLVX into scope; the walk has not been run with them.

## What it leaves to pull request 1727's author

As section 6 has it, each difference that a case needs and that the
pull request does not have is listed here for its author, and its cases
wait on it:

1. **`mmpt`'s reserved bits.** v0.9 has them "0 (NZR)", and says that
   they "shall return zero when read" (3:72 to 3:75); the earlier draft
   drew them "0 (WARL)". The case `reg.mmpt.nzr` (RV64 and RV32) waits
   on it.
2. **Bits 2:0 of `mmpt.PPN` under Smmpt64**, which "always read as
   zero" (3:122). The case `reg.mode64.ppn` (RV64) waits on it.
3. **The model's TLB and the SDID.** The SDID augments the ASIDs and
   VMIDs that `SFENCE.VMA` and its kin name (3:232 to 3:240). The
   model's TLB does not record the SDID, so a translation cached under
   one SDID could serve another. Flushing the TLB on each write of
   `mmpt` and on each `MFENCE.PA` would avoid that. No case of the
   suite exercises it.
4. **The extension's scope and name.** When the pull request was
   posted, the text defined `Smsdid` apart from the MPT extensions. The
   specification's pull request 293, merged 2026-08-19 with `v0.9.0`,
   folded both into `Smsd`, which "comprises Memory Protection Tables"
   (3:5 to 3:7). The pull request still has `Smsdid`; and `Bare`'s
   zeroing of `SDID`, which v0.9 dropped (M12-2's question 3).
5. **A sign-off and a rebase.** The pull request's commit needs its
   author's `Signed-off-by` for the model's DCO check, and a rebase
   onto `master`. The walk can be merged only after both.

## What was run

On 2026-11-19, at the exit commit, in M12-1's image
(`localhost/m12-sd-env:3064213f1120`), through the lane's gate for
heavy work, with no network:

- the model's own tests (`ctest`), built at the exit commit with its
  pull-request CI's options, save warnings-as-errors, as in M12-1.
  They include its unit tests, the five new ones among them;
- M12-3's suite at the tests' repository's `2ed52ccf`, on the model
  with the walk, RV64 and RV32. The table of results was made again, as
  section 6 asks, and compared with Spike's at the same suite, case for
  case. Every difference is listed and classed under section 8. No
  expected result was changed after the walk first ran.

These are directed tests and a model's own tests, under emulation, of
an unmerged implementation of a frozen specification (section 8). The
results wait for pull request 1727's author and for Spike's (section 6;
Q9). They are kept outside this repository, for the project's internal
records.

## Soft limit (section 9)

The table walk, in Sail, with its unit tests: 422 added lines of 900,
by `git diff --numstat` from pull request 1727's head. It has no
generated files and no Markdown.

## Publication gate

Run before this exit:

- the clone of the model: `publication-gate scan-tree --advisory` on
  the new and changed files, and on the two commits' messages and
  identities, gave `PASS`, with no advisory item. (Its `check` scans
  nothing, since the clone's push URL is disabled.);
- this repository's branch `m12`, including the commit that adds this
  page: `publication-gate audit --repo . m12` gave `PASS` (exit 0).

A pass is not approval to publish.

## What this step does not do

It sends nothing to anyone, adds no remote, and pushes nothing. It
offers the walk to no one. It makes no claim: the plan's section 8
holds, and the walk is not a reference model (section 8). It touches no
board, and runs only under emulation. It names no Beryllium unit a
supervisor domain (S3-D's stop (k)).

## Status record

```text
mvp_m12_4=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main
mvp_m12_4_exit=sail-riscv-clone;m12-smmpt-walk;25069b79f91bda765aca013acf4fb0fa75f0123b;tree-f7eb6bb353a460cb14656bf480ff7e50cf738493;over-pr-1727-fc08e2d3
mvp_m12_4_bundle=sail-riscv-m12-4-25069b79f91b.bundle;sha256-5645ccd3ed41be3c0cd5a03bfdc1b5e719995b975288b27c1e67aad80a0d697e;needs-fc08e2d3
mvp_m12_4_suite=tests-repository;main;2ed52ccffddaedf2117f2d40eb380ee8efe9b52f;tree-22e258cb003e85beff9a92aa50341932b6db1bf5;bundle-sd-tests-m12-4-2ed52ccffdda.bundle;sha256-c1839b5875575714ca56662589a0e57026aac2eece3eb03324f7a49a82ed8931
mvp_m12_4_text=v0.9-9211c4cf-frozen
mvp_m12_4_readings=2026-11-18;2026-11-19;rule-1;rule-11;tech-golden-model-thread-2026-11-09
mvp_m12_4_decisions=review-point-contact-first-2026-11-17;stop-2-met-2026-11-19;walk-prepared-locally-walk-first-2026-11-19;offered-to-no-one
mvp_m12_4_runs=model-own-tests;suite-2ed52ccf-on-the-walk-rv64-rv32;compared-with-spike;results-held-for-their-authors
mvp_m12_4_left_to_pr_author=mmpt-reserved-bits;smmpt64-ppn-2-0;tlb-and-sdid;extension-name-and-bare-sdid;sign-off-and-rebase
mvp_m12_4_stops=stop-2-met-decided;stop-9-at-exit
mvp_m12_4_soft_limit=walk-422-of-900-lines
```
