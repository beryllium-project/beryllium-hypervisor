<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# LLM policy alignment

## Purpose

This is the maintained policy crosswalk for the Beryllium repository,
including its Helium pathfinder component, and every parent or partner
open-source project with which they collaborate. It records binding upstream
rules separately from local safeguards and blocks public GitHub release when
responsible-human review has not been recorded.

**Beryllium** (`Be` / `be`) is the repository, project, and future hypervisor
name and the umbrella name for repository-wide policy. **Helium** (`He` /
`he`) is only the bounded pathfinder component name as of version 0.5.0.
Pre-0.5.0 commits retain their historical identity and remain governed by the
same licensing, assistance, and publication limits.

**Current Beryllium public GitHub release status: BLOCKED.** A review
snapshot of one accepted commit, published on the responsible human's
instruction of 2026-10-31, is not a release; see "Review snapshot
(2026-10-31)" below.

Private internal development is allowed: local/private branches, commits,
builds, reviews, evidence generation, and private evaluator access do not
require gate approval. The repository-wide release boundary applies before
publishing any current Beryllium material. Helium is additionally subject to
its component-specific publication gate.

The responsible human for Beryllium and Helium is:

```text
James Morris <jmorris@namei.org>
```

An AI system is an assisting tool, not the author, copyright holder, DCO
signatory, reviewer, or public-release approver.

## Maintained partner matrix

| Project | Relationship | Policy revision checked | Local status |
| --- | --- | --- | --- |
| Linux kernel | Primary prospective parent/integration project | `36aad21d50d1af3f6954bb0c988257a908202477` (v7.3-19809), 2026-10-31; before that `481ed5dd3ed7136f627b8ec372ba39f5b2e7d27f`, 2026-07-16 | Process aligned; the `Assisted-by` tag the earlier revision required was dropped upstream on 2026-10-14 and this document follows (below); current Beryllium license incompatible for direct code inclusion |

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

The current Beryllium repository, including Model 0.1, planning and tooling,
and the Helium pathfinder, is intentionally licensed `GPL-3.0-only`. Linux is
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

Pushing any part of the current private Beryllium repository to a public
GitHub repository is blocked. A future public release must use the clean
repository process below and contain only responsible-human-reviewed source
and selected artifacts.

If the selected public artifacts include Helium, the following additional
component gate applies.

### Helium component gate

Pushing Helium to a public GitHub repository is blocked unless:

1. the complete source and generated diff have been reviewed by James Morris;
2. the standalone HTML site, diagrams, references, and assurance claims match
   the reviewed source;
3. `./pathfinder/he check` and `./pathfinder/he evaluate` have passed for the
   reviewed commit;
4. generated evidence and dependency/license changes have been inspected;
5. the reviewed source commit is clean and recorded in
   `pathfinder/publication-gate.conf`, followed by a human-created gate-only
   commit;
6. LLM assistance and specialized tools are disclosed appropriately for the
   destination project;
7. the destination license and contribution process have been rechecked; and
8. `./pathfinder/he publication-check` reports `APPROVED`.

Automation may verify a human-authored approval record, but it may never set
`status=approved`, choose the reviewed commit, or sign on the human's behalf.
Any source change after approval invalidates the gate. The checker requires
the reviewed commit to be `HEAD^` and the approval commit to change only
`pathfinder/publication-gate.conf`; this avoids a self-referential hash.

Generated HTML is not a routine active-line deliverable. The private branch
`archive/generated-docs-2026-09-30` at
`d4c5ff0616c78d997367a050db85512c44960acb` preserves the 2026-09-30
historical generated snapshot only; it is not source authority or publication
approval. If a future reviewed release includes generated documentation, the
release candidate must regenerate, validate, and review those selected
artifacts under the complete publication gates above. This source-first
maintenance policy does not weaken any publication requirement.

## Future clean public repository

The private internal development history is the repository
`beryllium-project/beryllium-hypervisor-internal` (since 2026-10-31; before
that `beryllium-project/beryllium-hypervisor`, whose name the responsible
human re-uses for the public review snapshot below). Historical review
records may retain the former private identity `jamorris_microsoft/beryllium`
as packet-time evidence. A future public release still uses a new clean
Beryllium project repository populated only with the
responsible-human-reviewed codebase and selected artifacts.

### Review snapshot (2026-10-31)

On 2026-10-31 the responsible human directed (`give me a clean RC3 snapshot
repo which I will put up until the main repo is ready`) a fresh-history
snapshot of one accepted commit, MVP 1.0 release candidate 3's tree with its
acceptance record (`5c693b88` of the internal repository), to be published
by the human under the name `beryllium-project/beryllium-hypervisor` ahead
of the release path's later steps. `mvp/tools/snapshot.sh` makes it: `git
archive` of the one commit, the human's selection removed (`pathfinder/`,
the Helium pathfinder under its own gate below; `.github/`, the AI
operating instructions and skills; `planning/HANDOFF.md`, the internal
session handoff), a README naming the source, the exclusions, the
identifying strings kept, and the checks run in it, and `SNAPSHOT.txt`
naming the source commit; one commit, no history. It is a review copy, not
a release: the claim stays the one `mvp/docs/claim.md` states with its
required limit, the AI-assistance disclosure `mvp/docs/ai-assistance.md` is
in it, the private history is not pushed, and the release boundary above
and the clean-repository process stand. Automation made the snapshot and
ran its checks on the human's instruction and did not push it; the push is
the human's act. The selection and the gates run are recorded in
`mvp/README.md` ("Snapshot support", "The RC3 snapshot").

After that migration is reviewed and completed, the current internal
repository is archived. Automation must not:

- create or populate the public repository without explicit authorization;
- infer that the current private history is approved for publication;
- select which history or artifacts migrate;
- bypass the Helium publication gate for included pathfinder material; or
- archive the internal repository on the responsible human's behalf.

## Local authorship rules

- The preferred identity for future Beryllium Git authorship, review
  correspondence, and human DCO signoffs is
  `James Morris <jmorris@namei.org>`.
- Existing and newly added source headers in this internal repository
  continue to identify James Morris `<jamorris@linux.microsoft.com>` as
  required by the accepted runtime plan and current source-policy checkers.
  Accepted inputs, tool locks, manifests, package metadata, and historical
  records that identify James Morris
  `<jamorris@linux.microsoft.com>` remain unchanged. They identify the same
  responsible human and are retained as historical evidence or exact accepted
  bytes, not as the preferred future signoff address.
- New Beryllium source in a future clean repository should use
  `James Morris <jmorris@namei.org>` unless the destination's reviewed policy
  requires another identity. Current Helium identity-policy changes must be
  made separately in the authoritative `../helium-te-poc` repository.
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
