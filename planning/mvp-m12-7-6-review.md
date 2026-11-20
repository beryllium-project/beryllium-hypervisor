<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M12-7.6, the deeper review: packet and record

This page is the packet and the record of M12-7.6, the last sub-step of
M12-7, the Supervisor Domains model in Sail, which the [M12 plan's
revision 1](mvp-m12-plan-revision-1.md) adds to the [M12
plan](mvp-m12-plan.md): "M12-2's questions revisited on the model under
each reading, and a review of the text, for the specification's authors
through the responsible human", whose exit is "A document, as M12-2's".

The document is `review.md`, in the tests' repository, beside M12-2's
`questions.md`, which gains three questions from writing the model.
This page names the exit commits, records the readings, and says what
the review holds and what was drafted from it.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. His sign-off of that
commit on the public `main` is M12-7.6's acceptance. It rests on the
revision's and M12-7.1 to M12-7.5's acceptance, on the public `main` at
`f87ea59d` since 2026-11-20T05:29Z.

With it, M12-7 is complete: M12-7.4 and M12-7.5 [record why their
extensions are not modelled](mvp-m12-7-4-7-5-not-modelled.md), and the
other sub-steps have exits.

The page has no entry yet in the planning site's navigation or index;
the owner session adds them.

## The exit commits

| Repository | Branch | Commit | Tree |
| --- | --- | --- | --- |
| The tests' repository | `main` | `a67c1749b01604f16574622e398bab9ac1ba0d45` | `ea8d3efaa18424e150cf9d216d15277e3608e953` |

It adds two commits to M12-7.3's exit `9371bc56`:

| Commit | Subject |
| --- | --- |
| `149a7be930b90cf6e08d4519f447edcf07ac3850` | questions: three more, from writing the model |
| `a67c1749b01604f16574622e398bab9ac1ba0d45` | review: v0.9 revisited on the model |

Each is authored and committed as the responsible human, with Q3's
trailer and no sign-off. The model's branch is unchanged: `m12-smsd` at
M12-7.3's exit `1e2d2aca`, which he pushed to his fork. The tests'
repository is also kept as a bundle outside this repository:

| Bundle | SHA-256 | Needs |
| --- | --- | --- |
| `sd-tests-m12-7-6-a67c1749b016.bundle` | `130bc9c328733292849cd19a6d74822af6db4bd94929ccdef11f77eab925c059` | Nothing: the whole history |

## Readings (rules 1 and 11), 2026-11-20 (UTC)

| What | Read |
| --- | --- |
| The specification | `v0.9` (`9211c4cf`): its book, the introduction, the glossary, and chapters 2, 3, 4, and 9 in full; chapter 6, and the parts of chapter 7 that the model does not implement, for slips only. Its `main` at `8f8b5d5b` changes only headings, cross-references, and image paths, and still has each point of the review |
| Its issues | Open: 323, 327, 340, 341, and 342. Two were opened on 2026-11-20: 341, on chapter 6's effective `RCID` and `MCID`, which bears on question 12; and 342, on `MFENCE.PA` and translations cached under `Bare`, which follows issue 318's answer to question 3. Each question's status is in the review's table |
| Its contribution rules, and `LLM_POLICY_ALIGNMENT.md` | `CONTRIBUTING.md` is unchanged since `03af1144` (2023-04-10), so the specification's row stands |
| The Sail model | `master` still `ec5200bd`; the model's branch unchanged |
| The privileged specification | Tag `20250508`: the reset rules, the `MODE` rules of `satp` and `hgatp`, `HFENCE.GVMA`'s operand, Svinval, the HS-qualified rule, and the WARL rule, each cited in the review |

## What the review holds

**Part 1, the questions revisited.** For each of questions 1 to 18:
the model's default reading and its others, what the cases show under
each (from M12-7.3's runs), how the question stands in the
specification's issues, and a suggestion. The points that the model
adds:

- **Question 12.** Chapter 6 checks a device's `RCID` and `MCID`
  against the supervisor domain's range when they are used (6:818-840);
  nothing does so for a hart's `srmcfg` under the answer to issue 295,
  so an ID outside the range left in `srmcfg` would accompany a
  domain's requests from a hart, though not from a device.
- **Question 2.** Each reading of a write of an unsupported `MODE`,
  and `satp`'s rule too, leaves a hazard for an RDSM that does not read
  `mmpt` back; under two of them, the next domain runs with no MPT.
- **Question 1.** To take MPT faults in M-mode while other access
  faults are delegated, a hart has to route them by origin, since
  `medeleg` delegates by cause.
- **Question 15.** The text's own note on a dedicated QRI (9:259-265)
  gives the configuration under which `srmcfg` behaves as `Ssqosid`
  alone defines it, a candidate reset value.
- **Questions 16 to 18, new:** `mmpt`'s value at reset; how the fences
  name a physical address above 4 GiB on RV32, where `HFENCE.GVMA`
  shifts its address; and whether `MINVAL.PA`, which only Svinval's
  instructions order, requires Svinval, as the text did until
  `ff5069f` (2026-07-27).

**Part 2, the text.** Ten points of consistency and clarity (among
them: chapter 2 omits `Smgeien` and `Ssgeien`; `Smmpt` is still named
as an extension; `0 (NZR)` is never defined; the rule for page-table
accesses names only VS-stage and G-stage tables), and 23 slips, each
with its line.

The review shows only the model's own results, which section 6 does not
hold back. It adds nothing on Spike's or pull request 1727's behaviour
to what `questions.md` already says.

## What was drafted from it

In `contact/`, for him to edit and post, each through
`~/scripts/m12-contact.sh` with its name:

- new: `smmtt-q16-q18-mmpt-fences`, an issue for questions 16 to 18;
  and `smmtt-text-review`, an issue that lists part 2's points and
  slips for the editors, rather than a pull request of AI-written text
  for the specification;
- revised: `smmtt-q2-q3-mmpt`, with question 2's hazard; and
  `smmtt-q12-q13-srmcfg`, with chapter 6's check and issue 341;
- every line link to an AsciiDoc file now carries `?plain=1`, so that
  GitHub shows the line rather than the rendered chapter.

All seventeen drafts were READY at 2026-11-20T06:05Z. The lane posted
nothing.

## What was run

No new runs. The review rests on M12-7.3's runs of the model at
`1e2d2aca` under the defaults and the thirteen readings (the [M12-7.3
record](mvp-m12-7-3-qos.md)).

## Publication gate

- The tests' repository: `publication-gate audit --repo . --all-refs
  --advisory` gave `PASS` (exit 0), with no advisory item.
- The drafts: each passed `m12-contact.sh`'s checks, the gate's
  advisory pass among them.
- This repository's branch `m12`, including the commit that adds this
  page: `publication-gate check --repo . --remote origin m12` gave
  `PASS` (exit 0).

A pass is not approval to publish.

## What this step does not do

It sends nothing to anyone, adds no remote, and pushes nothing. It
makes no claim: the plan's section 8 holds. It touches no board, and
names no Beryllium unit a supervisor domain (S3-D's stop (k)).

## Status record

```text
mvp_m12_7_6=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main
mvp_m12_7_6_exit=tests-repository;main;a67c1749b01604f16574622e398bab9ac1ba0d45;tree-ea8d3efaa18424e150cf9d216d15277e3608e953;questions-16-18-149a7be9;review-md
mvp_m12_7_6_bundle=sd-tests-m12-7-6-a67c1749b016.bundle;sha256-130bc9c328733292849cd19a6d74822af6db4bd94929ccdef11f77eab925c059
mvp_m12_7_6_readings=2026-11-20;rules-1-and-11;smmtt-v0.9-9211c4cf;smmtt-main-8f8b5d5b;smmtt-issues-341-342-opened-2026-11-20;contributing-unchanged-since-03af1144;sail-master-ec5200bd
mvp_m12_7_6_findings=q12-chapter-6-checks-device-ids-at-use-not-hart;q2-every-reading-leaves-a-hazard-without-read-back;q1-route-by-origin;q15-note-gives-reset-candidate;q16-mmpt-reset;q17-rv32-fence-address;q18-minval-without-svinval;ten-consistency-points;twenty-three-slips
mvp_m12_7_6_contacts=new-smmtt-q16-q18-mmpt-fences;new-smmtt-text-review;revised-smmtt-q2-q3-mmpt;revised-smmtt-q12-q13-srmcfg;line-links-plain;seventeen-drafts-ready;nothing-posted
mvp_m12_7=complete;m12-7-4-and-m12-7-5-not-modelled
```
