<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M12-2, the questions: packet and record

This page is the packet and the record of M12-2, the questions, a work
package of the [M12 plan](mvp-m12-plan.md) (its section 6). It is step 1
of the plan's section 1: questions for the specification's authors on
behaviours that a model needs and that the text leaves open.

The page names the step's exit commit in the lane's tests' repository,
which holds the questions document. It records the readings that the
plan's rules 1 and 11 require, and lists the questions by subject.

M12-2 ran together with M12-3, the directed tests
([its page](mvp-m12-3-tests.md)), as the plan orders: writing the tests
found the questions.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. His sign-off of that
commit on the public `main` is M12-2's acceptance (the plan's section
6). The lane's own commits stay unsigned until he offers them.

The document is for the responsible human to send with first contact
(section 6; rule 10). Nothing has been sent.

The page has no entry yet in the planning site's navigation or index;
a later commit adds them.

## The exit commit

| Repository | Branch | Commit | Tree |
| --- | --- | --- | --- |
| The tests' repository (the plan's section 5) | `main` | `6594ad624345f215db5cdb35fddb58bc9fb0c40a` | `e9e785919867fd955b3d7f2c56621b0837fe2180` |

M12-2 and M12-3 end in this one commit. Since M12-1's exit
(`d3a04a45`), the repository has four more commits:

| Commit | Subject |
| --- | --- |
| `f461b1fa2efa7de713c2672911d6c08543873e6b` | tests: the harness and its cases, in seven groups |
| `d941497ca3f0fe02e064279b671720ff5f3b306a` | env: the runners, and the decoder of the results |
| `6c4c3209ae4e2212b964ce2130f4a8fa9ef82c4e` | questions: a first draft for the specification's authors |
| `6594ad624345f215db5cdb35fddb58bc9fb0c40a` | tests, questions: cite the lines that state each rule |

Each is authored and committed as the responsible human. Each carries
Q3's trailer (`Assisted-by: GitHub Copilot CLI 1.0.113-0 (model
claude-opus-5.5)`) and no sign-off.

The repository is still local, with no remote. The exit commit is also
kept as a bundle outside this repository:
`sd-tests-m12-2-3-6594ad624345.bundle`, SHA-256
`739bb815ec7f37abc72cf3bf67489761fc1973e96f9106b097cd0d6d6612e2b4`.

## Readings (rules 1 and 11), 2026-11-16 (UTC)

Read when the step started, at about 22:55, and again at its exit, at
23:52. Nothing had changed between the two readings.

| What | Read |
| --- | --- |
| The specification | Tag `v0.9.0`, commit `017f696b`, is still its latest release. The questions cite its text at that tag. Its `main` is `6549f944` (2026-11-16), 32 commits after the tag. In the chapters that the questions and the tests cite (2, 3, 4, and the introduction), those commits change wording, image formats, and one figure's label: `msdcfg` bits 21:6, from "NZR" to "0 (NZR)". They change no rule |
| The privileged specification | Tag `20250508` (`riscv/riscv-isa-manual` `584390d9`), for the rules that this specification relies on and does not state |
| The specification's contribution rules | `CONTRIBUTING.md` at `main` `6549f944`: CC-BY-4.0, and a Developer Certificate of Origin sign-off in the submitter's real name. No rule on AI-written content was found. The file is unchanged since `03af1144` (2023-04-10), so it is the same as at the plan's reading at `8168a644` |
| Its open issues and pull requests | Issue 327 (whether `Bare`'s zero `PPN` binds software or hardware), issue 323 (a move to the current document template), and pull request 326 (a proposed future extension) |
| Its closed issues | The answers of the eighteen that bear on a question or a case: 99, 118, 141, 142, 159, 177, 191, 202, 216, 228, 234, 262, 279, 280, 294, 318, 322, and 325 |
| The fences' encodings | `riscv/riscv-opcodes` pull request 389, by the specification's editor: open, head `18ea30ce`, not merged |

Stop 5 (the specification moves, or its authors give an answer that
changes an expected result) is not met. The text's `main` changes no
rule that a question or a case relies on. No answer in the closed
issues contradicts a specified case. Where an answer outside the text is
the only basis for a behaviour, the case that probes it is open, and the
question asks whether the text will state it (section 7).

Rule 11: `LLM_POLICY_ALIGNMENT.md` was rechecked, and its partner matrix
gained the specification's repository, with the revision of its policy
that was read. That was done by its own commit, made before the step's
work and since rebased onto the public `main` (`f28da999`).

## The questions document

The document is `questions.md` at the exit commit: 231 lines, under
CC-BY-4.0, the specification's own licence (the plan's section 5). It
carries an SPDX line, a copyright line that names the responsible human,
and rule 8's notice. Each question:

- names the text that it concerns, by chapter and line, at `v0.9.0` or
  at the privileged specification's `20250508`;
- says why a model needs the answer; and
- says what two implementations did in M12-3's open cases (the plan's
  section 6). They are Spike's pull request 2336 and the Sail model's
  pull request 1727, each named by its head commit and configuration.

| No. | Subject | Issues it cites |
| --- | --- | --- |
| 1 | Whether `medeleg` and `hedeleg` delegate an MPT access fault, which the informative text has always taken in M-mode | |
| 2 | What `mmpt` reads after a write of an unsupported `MODE` | 118, answered; 327 |
| 3 | Whether `SDID` holds its bits under `Bare`, so that `SDIDLEN` can be found in any mode | 294, 318, and 322, answered |
| 4 | Which permission tuples the lookup checks for a reserved encoding | 325, answered |
| 5 | Whether bit 11 of an RV64 NAPOT leaf is reserved, as it is in Smmpt34 | |
| 6 | What a hart may do when the MPTEs of one NAPOT range differ | |
| 7 | Bits 63:32 of `msdcfg` when MXLEN is 64 | |
| 8 | Whether HLVX needs execute permission in the MPT as well as read | 202, answered |
| 9 | Which exception the two fences raise below M-mode, in VS and VU modes too | 191, answered |
| 10 | The fences' funct7 values | 228 and 141, answered; `riscv/riscv-opcodes` pull request 389 |
| 11 | Where shared directed tests should live: the plan's Q1 | |

Issue 327, which is open, is referenced and not asked again. Where a
closed issue has answered a question that the text does not yet answer,
the document cites the answer and asks whether the text will state it.

**A choice made by judgement.** Section 6 has each question list what
the implementations did, and section 5 keeps the document in the tests'
repository. Section 5 also keeps every step's results out of the lane's
repositories, and section 8 keeps them out of this repository until
their authors have seen them. The lane reads the open-case observations
in the document as part of the questions, as section 6 defines them.
They are not the result tables that section 8 holds back: those are
kept outside every repository. So this page does not repeat the
observations. The document reports what each implementation did in an
open case, and it judges none. Sending it before or with the result
tables is the responsible human's choice at first contact.

## Publication gate

Run on each repository that the step changed, before its exit:

- the tests' repository: `publication-gate audit --repo . --all-refs`
  gave `PASS` (exit 0), with no advisory finding;
- this repository's branch `m12`, including the commit that adds this
  page: `publication-gate audit --repo . m12` gave `PASS` (exit 0).

A pass is not approval to publish.

## What this step does not do

It sends nothing to anyone, adds no remote, and pushes nothing. The
document goes with first contact, by the responsible human, in his
name, with its tools disclosed; the message that offers it is his own
writing (rule 7). It makes no claim: the plan's section 8 holds. It
names no Beryllium unit a supervisor domain (S3-D's stop (k)).

## Status record

```text
mvp_m12_2=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main
mvp_m12_2_exit=tests-repository;main;6594ad624345f215db5cdb35fddb58bc9fb0c40a;tree-e9e785919867fd955b3d7f2c56621b0837fe2180;shared-with-M12-3
mvp_m12_2_bundle=sd-tests-m12-2-3-6594ad624345.bundle;sha256-739bb815ec7f37abc72cf3bf67489761fc1973e96f9106b097cd0d6d6612e2b4
mvp_m12_2_document=questions.md;CC-BY-4.0;11-questions;issue-327-referenced
mvp_m12_2_text=v0.9.0-017f696b;privileged-20250508-584390d9
mvp_m12_2_readings=2026-11-16;rule-1;rule-11;LLM_POLICY_ALIGNMENT-row-specification-repository
mvp_m12_2_sends=nothing;for-the-responsible-human-at-first-contact
mvp_m12_2_stops=none
```
