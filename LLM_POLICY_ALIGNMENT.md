<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# LLM policy alignment

## Purpose

This is the maintained policy crosswalk for this repository, Beryllium's
MVP 1.0 clean repository, and for every parent or partner open-source
project with which Beryllium collaborates. It records binding upstream
rules separately from local safeguards, and it states the conditions under
which this repository's commits are published.

**Beryllium** (`Be` / `be`) is the repository, project, and future
hypervisor name and the umbrella name for project-wide policy. **Helium**
(`He` / `he`) is the name of the bounded pathfinder whose lessons the
planning record cites; it is not part of this repository (below).

**This repository's publication status:** a commit of this repository is
published only once the responsible human has reviewed and approved that
exact commit; automation neither approves nor publishes ("Beryllium public
GitHub release boundary", below).

The responsible human for Beryllium is:

```text
James Morris <jmorris@namei.org>
```

An AI system is an assisting tool, not the author, copyright holder, DCO
signatory, reviewer, or public-release approver.

## Maintained partner matrix

| Project | Relationship | Policy revision checked | Local status |
| --- | --- | --- | --- |
| Linux kernel | Primary prospective parent/integration project | `36aad21d50d1af3f6954bb0c988257a908202477` (v7.3-19809), 2026-10-31; rechecked 2026-11-06 against mainline `d48723711bae9b8cdc56719c448ba42fef28cbee`, at which `coding-assistants.rst`, `generated-content.rst`, and `submitting-patches.rst` are byte for byte those of the revision checked; before that `481ed5dd3ed7136f627b8ec372ba39f5b2e7d27f`, 2026-07-16 | Process aligned; the `Assisted-by` tag the earlier revision required was dropped upstream on 2026-10-14 and this document follows (below); current Beryllium license incompatible for direct code inclusion |

## Linux kernel alignment

### Binding upstream requirements

The Linux kernel's
[`coding-assistants.rst`](https://github.com/torvalds/linux/blob/36aad21d50d1af3f6954bb0c988257a908202477/Documentation/process/coding-assistants.rst)
at the revision checked requires:

- normal kernel development, submission, and coding-style processes;
- GPL-2.0-compatible contributions;
- responsible-human review of all AI-generated code;
- a human `Signed-off-by` certifying the Developer Certificate of Origin;
- full human responsibility for the contribution; and
- for an AI assistant used to find and fix bugs, its "Procedure for finding
  and fixing bugs": the process documentation read whole, the commit
  identified, a reproducer for any non-trivial bug, a built and verified
  fix with a `Fixes` tag and no `Signed-off-by`, the maintainers found
  with `scripts/get_maintainer.pl`, what could not be done stated, and
  the vulnerability question answered per `threat-model.rst` and left to
  the reporter; the assistant never sends anything itself.

Its
[`generated-content.rst`](https://github.com/torvalds/linux/blob/36aad21d50d1af3f6954bb0c988257a908202477/Documentation/process/generated-content.rst)
asks that a contribution a meaningful part of which a tool wrote be
transparent about it in the cover letter and changelog: what tools were
used, their inputs or, for a long session, a summary of the prompts and the
assistance, which portions of the content they affected, and how the
submission was tested; maintainers may treat such a contribution as any
other, reject it, review it with extra scrutiny or at lower priority, or
ask how the tool or model was trained. The submitter must understand and be
able to defend everything submitted.

AI agents must not add `Signed-off-by` tags. They are also not represented as
human co-developers. For a Linux patch derived from this work, the disclosure
belongs in the cover letter and changelog in the form above (the tools, the
prompts or their summary, the affected portions, the testing), with the
human's own certification:

```text
Signed-off-by: James Morris <jmorris@namei.org>
```

Only James Morris may add that `Signed-off-by`, after completing the human
review and DCO assessment. The assisting system must never generate or apply
it autonomously.

**History of the attribution rule.** The revision this document first
checked
([`78d979db`](https://github.com/torvalds/linux/blob/78d979db6cef557c171d6059cbce06c3db89c7ee/Documentation/process/coding-assistants.rst),
2026-07-16) required an `Assisted-by: AGENT_NAME:MODEL_VERSION
[SPECIALIZED_TOOLS...]` tag, and `submitting-patches.rst` said that omitting
it could impede acceptance; eight commits of this repository, of 2026-07-16
to 18, carry `Assisted-by: GitHub-Copilot-CLI:gpt-5.6-sol`. Upstream commit
`816d9992d9ed` (2026-08-03, "coding-assistants: simplify attribution")
reduced the tag to `Assisted-by: LLM`, and commit `1e035297ffda`
(2026-10-14, "docs: remove Assisted-by references", after the 2026
Maintainers Summit) removed it from `coding-assistants.rst`,
`submitting-patches.rst`, and `checkpatch.pl`: the tag was carried by about
10% of the 7.3 cycle's commits while use was far wider, so it gave no
signal, and the transparency expected of contributors moved to the cover
letter under `generated-content.rst`; the DCO and the submitter's
responsibility were not changed. A future Linux-facing patch from this work
therefore carries no `Assisted-by` tag unless the destination's policy at
that time asks for one; the recheck before any RFC or series (the TODO
below) decides.

### License boundary

Beryllium, this repository's MVP line, models, planning, and tooling among
it, is intentionally licensed `GPL-3.0-only`; one file, the guest
management module `mvp/guest/mgmt/be-mgmt.c`, is `GPL-2.0-only`, because
it is built against the guest's Linux kernel (`COPYING`). Linux is
`GPL-2.0-only`, and its
[`license-rules.rst`](https://github.com/torvalds/linux/blob/78d979db6cef557c171d6059cbce06c3db89c7ee/Documentation/process/license-rules.rst)
requires every in-tree source license to be GPL-2.0 compatible.

Therefore:

- Current Beryllium implementation text must not be submitted directly for
  Linux inclusion.
- Helium remains a separate research/evaluation component and cannot be
  treated as Linux-ready Beryllium core source.
- Any future in-tree Beryllium implementation requires an explicit,
  responsible-human licensing decision and provenance review before code is
  copied, relicensed, dual-licensed, or independently reimplemented.
- Interface discussion, behavioral evidence, specifications, and test ideas
  do not by themselves authorize copying GPL-3.0-only implementation text into
  Linux.

This incompatibility is a deliberate and visible integration boundary, not a
claim that current Beryllium or Helium source is already suitable for upstream
submission.

## Beryllium public GitHub release boundary

This repository holds only material the responsible human selected and
reviewed (`RELEASE.md`). Its commits are published under these rules:

1. The responsible human reviews and approves each exact commit before it
   is published, with its tag where it has one; any later change to the
   source invalidates that approval, and the changed commit needs its own.
2. Each published commit carries the responsible human's own
   `Signed-off-by` ("Local authorship rules", below).
3. Automation may prepare commits and run checks. It never approves, tags,
   pushes, or publishes a commit, and it never adds a human
   `Signed-off-by`.
4. A change that changes what the project may claim follows the claim's
   own rules (`mvp/docs/claim.md`).

### Helium

Helium is not part of this repository. Its current source is the separate
helium-te-poc repository, and its own publication gate stays with it:
nothing of Helium enters this repository without that gate and a separate
decision of the responsible human.

Generated HTML is not committed here; the planning site is built from its
Markdown sources (`./be docs`).

## This repository's provenance

This repository is the clean repository the release path's step 3 made
(the MVP plan, "Release path"): a fresh-history copy of the responsible
human's selection from one commit of the project's private internal
repository, MVP 1.0 release candidate 4's tree with its acceptance record,
then the adaptations that let its gates run here. `RELEASE.md` records the
source, the copy commit, each adaptation with its reason, the exclusions,
the scans with the human's classification, and the gates' results. The
private internal repository's history, its development handoff, and its AI
operating instructions are not part of it; historical records here may
name that repository and a former private identity as packet-time
evidence.

Before this release, from 2026-10-31, the responsible human published
fresh-history review snapshots of accepted commits for external review;
they were review copies, not releases, and `mvp/README.md` records their
selection and checks ("Snapshot support").

Automation must not:

- push, tag, or publish this repository without the responsible human's
  explicit instruction for that exact commit;
- infer that any material is approved for publication;
- select what migrates from the internal repository;
- add material from Helium or from the internal history; or
- archive the internal repository on the responsible human's behalf.

## Local authorship rules

- The identity for Beryllium Git authorship, review correspondence, and
  human DCO sign-offs is `James Morris <jmorris@namei.org>`.
- Files copied from the internal repository keep their bytes, their
  copyright lines naming James Morris `<jamorris@linux.microsoft.com>`
  among them; they identify the same responsible human and are kept as
  historical evidence or exact accepted bytes. Files new in this repository
  name `James Morris <jmorris@namei.org>`, except where a checker binds the
  old line, as it binds this document's (the release path's step 2, Q13).
- Every commit is authored and committed as
  `James Morris <jmorris@namei.org>`. A commit that automation prepares
  carries the trailer
  `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`
  and the session's `Copilot-Session` trailer, which disclose the
  assistance. The responsible human adds his own `Signed-off-by` to each
  commit published, after his review and DCO assessment, and only he may.
- LLM systems are acknowledged in commit/submission metadata where the
  destination policy requires it; they are not listed as source-code authors.
- Generated artifacts identify their source and generator and are reviewed
  with the source.
- Third-party source, specifications, and tools retain their own authorship and
  licenses.
- No public assurance, certification, upstream-readiness, or formal-verification
  claim may exceed the evidence documented for the exact reviewed revision.

## Review triggers

Recheck this document when:

- a partner project's contribution, AI-assistance, DCO, or licensing policy
  changes;
- Beryllium adds a new collaboration, destination, model provider, agent, or
  code-generation tool;
- source is prepared for a public GitHub push or upstream submission;
- the responsible human or publication process changes; or
- the GPL-3.0-only boundary is reconsidered.

## TODO

- [ ] Revisit this matrix before adding each parent or partner project.
- [ ] Add a dedicated policy-maintenance agent only after its authority is
      constrained so it cannot approve public release or add human sign-offs.
- [ ] Recheck the Linux policy revision immediately before preparing any Linux
      RFC or patch series.
- [x] Rechecked 2026-10-31 (the responsible human's `recheck any upstream LLM
      policies and update as needed`, at the review snapshot's publication,
      a review trigger above): `coding-assistants.rst`,
      `generated-content.rst`, and `submitting-patches.rst` at
      `36aad21d50d1` read against the pinned `481ed5dd3ed7`; the
      `Assisted-by` tag dropped upstream, the bug-fixing procedure added, the
      transparency rule in `generated-content.rst`; this document and
      `mvp/docs/ai-assistance.md` section 6 updated. No other partner
      project is in the matrix.
- [x] Rechecked 2026-11-06 (the release path's step 3, its plan's Q10,
      before this repository's release record): the same three documents
      at mainline `d48723711bae` are byte for byte those of `36aad21d50d1`,
      so nothing bears on this repository's disclosure, licence, or
      sign-off. No other partner project is in the matrix.
