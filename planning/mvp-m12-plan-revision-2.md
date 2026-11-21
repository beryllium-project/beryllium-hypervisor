<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M12 plan, revision 2: after the first contacts

This page revises the [M12 plan](mvp-m12-plan.md) and its [revision
1](mvp-m12-plan-revision-1.md) at the responsible human's direction of
2026-11-21: what M12 does once Jordan Carlin and the Sail model's
maintainers have answered. Every step of those pages has ended: M12-1
to M12-4, M12-7.1 to M12-7.6, and M12-5, which he narrowed to its
firmware half ([its record](mvp-m12-5-firmware.md)). What is left of
M12's goal depends on answers from others, to contacts that he sends.
This page plans the work for each answer.

Where this page and the earlier ones differ, this page governs; their
other sections stand.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. His sign-off of that
commit on the public `main` is this revision's acceptance.

No step of this page starts before the answer that it waits for. Each
starts with a packet in its record and ends with an exit, as before.

## The responsible human's decisions

All on 2026-11-21 (UTC).

1. **Between 00:00Z and 03:35Z**, asked one at a time:
   - M12-5 is narrowed to its firmware half (recorded in its page);
   - the firmware series' author hears first by a private mail, and
     the series' list later;
   - he sends each contact himself, from plain documents that the lane
     prepares: "just create docs which I can review and copy into
     emails as needed";
   - the tests' public home waits until he has talked with Jordan
     Carlin.
2. **04:49Z, the direction:** draft a plan revision for "what M12 does
   once Jordan Carlin and Sail have answered"; and rebuild and test
   the model on the Sail model's current `master`, on a local branch.

## Facts, as read on 2026-11-21

- **The specification's owner on the model.** On the tech-smmtt list
  on 2026-11-19, the responsible human asked whether anyone works on a
  Sail model of Supervisor Domains, and offered help. Andrew Dellow,
  the specification's owner, replied that there had been no Sail work
  on it for a while, and asked him to coordinate with Jordan Carlin,
  who commits to both the Sail RISC-V model and riscv-arch-test.
- **The Sail model's guidelines.** Its maintainers begin updating its
  contribution guidelines in the week of 2026-11-23; suggestions close
  at the end of the week before (the tech-golden-model list, message
  505). Replies in that thread put the "inclusion, or potential
  inclusion, of material into RISC-V specifications" at the core of
  the question, under ISO's rules, and say that RISC-V International is
  drafting an AI policy, with `Assisted-by` tagging in its draft
  (message 507). Its `CONTRIBUTING.md` is unchanged since `29e6158f`
  (2026-09-05).
- **riscv-arch-test.** Its default branch, `act4`, generates tests
  from test plans, with expected signatures from a reference model, the
  Sail model; so its tests of an extension need that extension in the
  Sail model first. It is Apache-2.0, and every commit needs a
  Developer Certificate of Origin sign-off and a signature. It has an
  `AGENTS.md` for AI agents, and its `CONTRIBUTING.md` (at `3879e7fd`)
  states no rule on AI-written content. It has no Supervisor Domains
  tests.
- **The firmware series.** v7 is still the latest. On its patch 2
  (2026-11-10), Anup Patel proposed that its protection program PMP
  only for M-only and shared regions, and enforce S-only regions
  through the MPT alone. Its author's answer to the lane's notes is
  awaited.
- **The emulator series.** QEMU's is still at v8, written to a draft
  before `v0.9`. M12-5 no longer waits for it.
- **The model.** The lane's branch was rebased on 2026-11-21 onto the
  Sail model's `master` of that day, `71312d53`, without conflict, as
  the local branch `m12-smsd-on-71312d53` (`46548d06`). It builds in
  the environment's image, passes all 9,245 of the model's own tests,
  and gives the suite's tables and signatures, RV64 and RV32, byte for
  byte as at `1e2d2aca`. `m12-smsd` on his fork is unchanged.
- **The specification.** `v0.9`. Its freeze approval is due
  2026-11-28, and Ratification-Ready is projected for 2027-01-18. The
  lane's eleven issue drafts, for its questions and its text, are with
  him.
- **aphlta/smmpt-act**, the unlicensed suite in revision 1's facts, is
  unchanged since 2026-09-04, still with no licence.

## What changes

Four steps follow, each waiting for an answer, and then M12's end.

| ID | Work | Waits for | Exit |
| --- | --- | --- | --- |
| M12-8 | **The model's way upstream** | The Sail model's new guidelines, and Jordan Carlin's answer | A record of what was offered and how, and the answer; or of why nothing was |
| M12-9 | **The tests' public home** | Jordan Carlin's answer | The tests public where he chooses, or a record of why not |
| M12-10 | **The firmware series' follow-up** | Its author's answer, and each new version | The list reply, sent by him; M12-5's runs on each new version, held for its author |
| M12-11 | **The specification's answers** | Answers to the questions, the freeze approval, and any new release | The model's defaults, the suite, and the review follow each answer, each with a record |

### M12-8, the model's way upstream

By what the Sail model's guidelines say:

- **They accept AI-assisted code with disclosure.** The lane prepares
  the model as pull requests in the form that Jordan Carlin and the
  maintainers ask for, on the `master` of the day: for example `Smsd`'s
  registers and fences, the MPT lookup, the hypervisor's interactions,
  and `Smqosid` with `Smsdqosid`. Each commit keeps rule 3's trailer
  and gets his sign-off. He opens each pull request. Pull request
  1727's author still hears first, as revision 1 has it, unless he
  decides otherwise.
- **They decline it.** Nothing AI-written is offered to the Sail model
  (stop 2). The model stays on his fork as a reference, for the
  specification's review and for whoever writes the model by hand, and
  the lane offers that author, through him, the review, the questions,
  and the suite with its results.
- **They limit it**, for example to code that is not quoted in a
  specification: the lane maps the model's files against the limit,
  and asks him before any offer.
- **Someone else starts the model** (Jordan Carlin, the task group, or
  the Freeze task RVS-3617): stop 3. The step becomes running the suite
  on their work and offering its results, as for pull request 1727.

In every case:

- the `srmcfg` defect in the Sail model's `master` (its `RCID` and
  `MCID` in each other's bits) goes as an issue, with a fix only if he
  writes one by hand (revision 1's decision 3);
- the emulator's `--show-times` crash goes as an issue.

**Keeping the branch current.** The lane rebases its branch onto the
model's `master` at this step's start and before each offer, and runs
the model's own tests and the suite each time, as it did on
2026-11-21. A rebased branch is a new local branch; `m12-smsd` on his
fork moves only when he pushes it.

### M12-9, the tests' public home

- **riscv-arch-test**, if Jordan Carlin and its maintainers want the
  cases there and its rules allow AI-written tests (rule 11: its row in
  `LLM_POLICY_ALIGNMENT.md` first). The cases would be rewritten in
  ACT4's form: test plans, generators, and coverpoints, whose expected
  results come from the Sail model. That waits for Supervisor Domains
  in the Sail model (M12-8). It also changes rule 5, under which
  expected results come from the text: there, the model would be
  checked against the text, and the tests against the model. The
  step's packet says how.
- **A repository of their own**, under his account or the
  organization: the tests' repository as it is, made public by him
  after the publication gate's whole-history audit.

Either way, the specification's question about the tests (question 11)
and the offer of the tests in Spike's comment can then be met.

### M12-10, the firmware series' follow-up

- After its author's answer, the reply on the series' list, which the
  lane has drafted, changed to fit the answer and sent by him.
- On each new version of the series (stop 4): M12-5's runs again, on
  the model of the day, under the same descriptor, compared with v7's,
  and held for its author. No code is written for the series (stop 8).
- If QEMU's series reaches `v0.9`, a revision may add the emulator back.
  Nothing is drafted for QEMU (rule 8).

### M12-11, the specification's answers

- Each answer to a question is read as stop 5 has it: an issue's reply,
  a change to the text, the freeze approval, or a release. Where it
  settles an open behaviour:
  - the model's option for it gets the answer as its default;
  - the other reading stays as an option, if the text still allows it;
  - the suite's case that rests on it becomes specified;
  - `questions.md` and `review.md` record the answer.

  Each answer gets a small record, for his sign-off.
- A release after `v0.9` gets a re-pin, as `v0.9` did on 2026-11-19:
  the suite and the model re-pinned, and every citation checked.

### M12-4's walk

The table walk on pull request 1727 stays local and is not offered: the
model of revision 1 replaces it. Accepting this page settles the
question that stop 9 left open at M12-4's exit.

### M12's end

M12 ends when each of M12-8 to M12-11 has reached its exit, or when he
ends it. Its last record says what each part of the plan's goal
became:
- the reference model;
- the emulator, not reached, since QEMU's series did not reach `v0.9`;
- the firmware;
- the contributions.

## Soft limits (section 9)

No code is planned before the answers. Each step that writes code
states its limit in its packet, for his acceptance, before it starts:

- rebasing the model adds no lines of the lane's own, and is not
  counted;
- splitting the model into pull requests counts only new lines;
- ACT4's form of the cases would have a limit of its own.

## Stops

Section 10's stops stand. Here they apply as follows:

- **Stop 2:** the Sail model's new guidelines, if they decline
  AI-written content or the results of AI-written tests; or any
  maintainer's or author's objection.
- **Stop 3:** a Supervisor Domains model or test suite started by
  someone else.
- **Stop 4:** a new version of the firmware series or of QEMU's; a
  change to Spike's pull request 2336.
- **Stop 5:** an answer that changes an expected result. M12-11 plans
  that work; each answer still returns to him first.
- **Stop 12:** nothing is sent, posted, opened, or pushed by
  automation. Every contact is his.

## What acceptance would authorize

- Preparing M12-8 to M12-11 as their inputs arrive:
  - contacts and pull-request text, as documents for him;
  - local branches of the model, rebased and tested;
  - runs of the suite and of the firmware series;
  - their records.
- That M12-4's walk stays local.

It would authorize nothing sent, offered, posted, opened, or pushed; no
fork of the emulator; no code for the emulator or the firmware series;
no board command; and no claim.

## Status record

```text
mvp_m12_revision_2=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main
mvp_m12_revision_2_direction=2026-11-21T04:49Z;what-m12-does-once-jordan-carlin-and-sail-have-answered
mvp_m12_revision_2_steps=M12-8-model-upstream;M12-9-tests-home;M12-10-firmware-follow-up;M12-11-spec-answers;M12-end
mvp_m12_revision_2_waits=sail-guidelines;jordan-carlin;firmware-series-author;spec-authors
mvp_m12_revision_2_model=rebased-2026-11-21;sail-master-71312d53;local-branch-m12-smsd-on-71312d53-46548d06;9245-own-tests-pass;suite-identical-to-1e2d2aca;fork-unchanged
mvp_m12_revision_2_walk=stays-local;not-offered;settles-stop-9
mvp_m12_revision_2_soft_limits=set-in-each-step's-packet;rebases-not-counted
mvp_m12_revision_2_sends=nothing
```
