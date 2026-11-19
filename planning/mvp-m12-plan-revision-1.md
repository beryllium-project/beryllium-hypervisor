<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M12 plan, revision 1: the Supervisor Domains model in Sail

This page revises the [M12 plan](mvp-m12-plan.md) at the responsible
human's direction of 2026-11-19. It turns the plan's step 3, the table
walk (M12-4), into a model of the Supervisor Domains extensions of the
specification's frozen release, `v0.9`, in the Sail RISC-V model, on
the model's current `master`, which has the hypervisor extension.

Where this page and the plan differ, this page governs; the plan's
other sections stand. It does not change the MVP plan's text. S3-D.4
names the walk on top of pull request 1727 as M12's step 3; whether
S3-D.4 needs an amendment for this page is the owner session's to
judge.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. His sign-off of that
commit on the public `main` is this revision's acceptance.

**Work on M12-7.1 and M12-7.2 began at his direction, before that
acceptance.** Nothing is offered to anyone, and nothing is pushed.

## The responsible human's decisions

All on 2026-11-19 (UTC), at M12-4's exit, which is stop 9's decision.

1. **10:09Z, the direction:** "we will change m12 plan, and begin
   implementing the full supervisor domains v0.9 sail model, starting
   with smsd, against the latest hypervisor-inclusive upstream sail.
   leverage the existing code if appropriate. I want a clean
   implementation that we can then use to revisit questions & also
   perform deeper review of the spec."
2. **About 10:13Z, pull request 1727's code:** "fresh". Smsd's
   registers and fences are written anew to `v0.9`, and the pull
   request is credited as prior work, not used.
3. **About 10:15Z, provenance:** "I want to keep LLM and manual code
   separate."

The direction changes an accepted text (stop 14) and needs a soft limit
re-set (stop 13). Both are his, and this page records them.

## Facts, as read on 2026-11-19

- **The text.** `v0.9` (`9211c4cf`, frozen 2026-11-17) defines `Smsd`,
  which "comprises Memory Protection Tables" (3:5 to 3:7). The
  specification's pull request 293, merged 2026-08-19 with `v0.9.0`,
  folded `Smsdid` and the MPT extensions into it.
- **RISC-V International's tracker.** The specification's Freeze task
  "Add Support into the Sail Golden Model" (RVS-3617) is Not Started.
  The Freeze approval is due 2026-11-28, and Ratification-Ready is
  projected for 2027-01-18.
- **The model.** Its `master`, `dda378c6` (2026-11-18), has the
  hypervisor extension (its pull request 1769, 2026-08-20), on in its
  default configuration, and requires Sail 0.20.3. M12-1's image has
  Sail 0.20.1. The model has `Ssqosid`, and `Sdtrig` without external
  debug; it has no interrupt files (AIA).
- **Pull request 1727.** Its head, `fc08e2d3`, is unchanged since
  2026-05-27. It is written to the text before `v0.9` merged the
  extensions, and on a base without the hypervisor. A scan of the
  model's 326 forks found no other work on the extension, apart from an
  empty branch.
- **The emulator and firmware series.** The QEMU series' v8
  (2026-07-23) is written to `v0.4.9`. The OpenSBI series' v7
  (2026-11-02) is written to `v0.9`, but its cover letter says that
  QEMU does not support `v0.9` yet, and that the series "is only for
  review". So no implementation of `v0.9` exists to run it on.
- **A test suite that the plan's facts missed.** Section 3 has "no
  shared test suite", as read on 2026-11-10. aphlta/smmpt-act, a
  "portable SmMTT v0.9.0 compliance suite", was posted on 2026-09-04.
  It has no licence, so it cannot be built on (stop 3). Only its
  description and commit titles were read (rule 4).

## What changes

### Step 3 becomes M12-7, the Supervisor Domains model

M12-4 stands as its own record has it. M12-7 follows it: the extensions
of `v0.9`'s chapter 2 that a model of a hart can express, in the
model's `master`, in this order. Each sub-step ends as section 6 says:
an exact commit of the lane's clone, a bundle, and a record commit here
for the responsible human's sign-off, with results held for their
authors.

| ID | Work | Exit |
| --- | --- | --- |
| M12-7.1 | **The environment.** M12-1's image made again for the model's `master`, with Sail 0.20.3 from pinned inputs, and a new record | The image's record; the model's own tests at the base |
| M12-7.2 | **`Smsd`.** `mmpt` and `msdcfg`; the SDID; `MFENCE.PA` and `MINVAL.PA`; the MPT lookup in all four modes, checked on every access below M, implicit accesses included; the hypervisor's guest modes, two-stage translation, and HLVX; the translation cache and the SDID; the ISA string and the device tree | The branch; the model's own tests; the suite, its hypervisor cases included, compared with Spike's results; the questions revisited (M12-7.6) |
| M12-7.3 | **`Smsdqosid` and `Smqosid`** (chapter 9), on the model's `Ssqosid` | As M12-7.2, for its cases |
| M12-7.4 | **`Smsdedbga` and `Smsdetrca`** (chapter 8): `msdcfg`'s `SEDA` and `SETA`. The model has no external debug or trace, so the bits hold state and have no other effect | As M12-7.2, for its cases |
| M12-7.5 | **`Smsdia`** (chapter 7), only if the model then has the interrupt files that it needs. Otherwise the sub-step records why not | As M12-7.2, or a record |
| M12-7.6 | **The deeper review.** M12-2's questions revisited on the model under each reading, and a review of the text, for the specification's authors through the responsible human | A document, as M12-2's |

The I/O MPT checker (chapter 6) is a device outside the hart, and is
not modelled.

### The base

The model's `master` at `dda378c60fa0ad1bf13af5929bebee344a2e0a75`
(2026-11-18), on a new branch, `m12-smsd`, of the lane's clone. The
base moves only at a sub-step's start, with a record.

### Pull request 1727, and keeping LLM and manual code apart

- **Pull request 1727's code is not used** (decision 2). This departs
  from D27, which rules out a parallel implementation, for its
  registers and fences, by the responsible human's decision. The
  reasons: the pull request predates both `v0.9`'s merge of the
  extensions and the model's hypervisor; its commit lacks the sign-off
  that the model requires; and it has been idle since 2026-05-27. It is
  credited as prior work in M12-7.2's commits and record. Its author
  still hears from him first: nothing of M12-7 is offered before the
  author has answered, unless he decides otherwise.
- **LLM-written and manually written code are kept apart**
  (decision 3):
  - M12-7's code is written only by the lane's AI tool, which rule 3's
    trailer names on every commit. It lives in files of its own under
    the model's `extensions/`. Each hook into the model's existing
    files is a small commit of its own.
  - No commit mixes AI-written and manual changes. Manual work, if any,
    goes in commits or branches of its own.
  - Pull request 1727's files are not open while M12-7 is written. This
    session read them for M12-4, so M12-7 is written from `v0.9`'s text
    and the model's `master`, and from M12-4's walk, which is the lane's
    own AI-written code. The walk's uses of the pull request's
    definitions are replaced, not carried over.

### Open behaviours as configuration

Each behaviour that M12-2's questions find the text leaves open is an
option in the model's configuration. Its default is the lane's reading,
as M12-4 chose it, and its description names the question. The suite
can then be run under each reading (M12-7.6). Behaviours that the text
leaves to the implementation, such as which modes are supported and the
SDID's width, are options as well.

### The suite

Its hypervisor cases now run on the model. Expected results still come
from the text (rule 5). A case whose result depends on an open
behaviour names the question it rests on, as now.

### The firmware series on the model (for his decision)

Since the OpenSBI series' v7 has no implementation of `v0.9` to run on,
M12-5's firmware half may run on the model once M12-7.2 boots firmware,
rather than wait for the emulator series. No code is written for the
firmware series (stop 8 stands). Accepting this page with this
subsection accepts that; he may strike it.

## Soft limits (section 9)

Counted as section 9 says, in the lane's clone from the base:

| Lane | Limit | Basis |
| --- | --- | --- |
| `Smsd` in Sail, with its unit tests (M12-7.2) | 1,600 lines | M12-4's walk was 422 lines over a 206-line pull request. The registers, the fences, the hypervisor's interactions, the translation cache, and the options add to it |
| Each of M12-7.3 to M12-7.5 | 400 lines | Register fields and their checks |

The other rows stand.

## Stops

Section 10's stops stand. Stop 3 also covers a Supervisor Domains model
for Sail posted by someone else, and the task group starting its own
(RVS-3617). Stop 4 covers pull request 1727's closure or a new head of
it, and the model's `master` only at a sub-step's start.

## What acceptance would authorize

- M12-7.1 to M12-7.6, under section 4's rules and section 10's stops:
  the branch `m12-smsd` in the lane's clone, and the image made again
  from pinned inputs.
- With the subsection above, M12-5's firmware half on the model.

It would authorize nothing sent, offered, posted, or pushed; no fork of
the emulator; no code for the emulator or the firmware series; no
board command; and no claim.

## Status record

```text
mvp_m12_revision_1=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main
mvp_m12_revision_1_direction=2026-11-19T10:09Z;full-supervisor-domains-v0.9-sail-model;smsd-first;model-master-with-hypervisor;clean-implementation;revisit-questions;deeper-review
mvp_m12_revision_1_pr_1727=fresh;not-used;credited-as-prior-work;departs-from-D27-for-its-registers-and-fences-by-his-decision
mvp_m12_revision_1_provenance=llm-and-manual-code-kept-apart;own-files;hooks-in-own-commits;no-mixed-commits
mvp_m12_revision_1_base=sail-riscv-master-dda378c60fa0ad1bf13af5929bebee344a2e0a75;branch-m12-smsd;sail-0.20.3
mvp_m12_revision_1_steps=M12-7.1-environment;M12-7.2-Smsd;M12-7.3-Smsdqosid-Smqosid;M12-7.4-Smsdedbga-Smsdetrca;M12-7.5-Smsdia-if-the-model-allows;M12-7.6-review
mvp_m12_revision_1_open_behaviours=configuration-options;defaults-the-lane's-readings
mvp_m12_revision_1_firmware_on_the_model=proposed;M12-5-firmware-half;no-code-for-the-series
mvp_m12_revision_1_soft_limits=M12-7.2-1600-lines;M12-7.3-to-M12-7.5-400-lines-each
mvp_m12_revision_1_sends=nothing
```
