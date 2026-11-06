<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R8 plan revision A review and acceptance record

> **Repository rehoming note (current-line editorial context):** This record
> preserves its packet-time former private repository and remote state. The
> current active private repository is
> `beryllium-project/beryllium-hypervisor`; use
> [project orientation](project-orientation.md) for current repository
> guidance.

This document began as the decision-support packet for one exact immutable
planning commit — `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`, which carries
**Plan revision R8-A**, the narrow repair to the accepted H0
documentation-support and exact-candidate identity rules — and now also
records the responsible-human decision taken on it. The decision-support
material below is retained as review history and remains the evidence the
decision rests on. Except where a statement is explicitly marked as current,
sections 1 through 9 describe the state at the time of that decision.

The accepted original R8 plan remains exact accepted history at
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`. A separate responsible-human
instruction already authorized only non-privileged R8-H0 implementation under
that plan. Local, unaccepted H0 work exposed two plan defects, so H0 was
paused and preserved locally while this narrow revision was reviewed.

## Decision record

Responsible-human review **accepted the exact R8-A plan-revision commit**
`8fa9d672cfcfb81ab68d9ed9553a5af48b884932` (parent
`cb0ac2a0f818ac57f2866cb7815767145608cf58`) on 2026-08-07. The supplied
instruction was exactly:

```text
accept exact 8fa9d672cfcfb81ab68d9ed9553a5af48b884932
```

The accepted target's Git tree is
`7754c5b19a34ed928710e6fe3c6cf716445f2187`, and its subject is
`docs: propose narrow R8-A H0 integration revision`. This decision applies
only to that exact immutable commit. The target remains byte unchanged.

The accepted target's own plan text still reports
`r8_plan_revision_r8a=proposed-not-reviewed` and
`r8_h0=paused-pending-r8a-acceptance`. Those are frozen pre-decision fields
describing the commit as offered. This record and the maintained
current-position documents carry the later acceptance decision; the immutable
plan file is not rewritten after review.

Packet commit `9ad001bdbcb41aa7c86b406b80f62a6c9820e08c`
(`docs: prepare exact R8-A plan review`) and this acceptance-record follow-up
are decision support only. Neither is plan text or H0 implementation. The
accepted R8-A target remains exactly
`8fa9d672cfcfb81ab68d9ed9553a5af48b884932` over parent
`cb0ac2a0f818ac57f2866cb7815767145608cf58`.

This acceptance unpauses only the **already authorized non-privileged H0**
work after this acceptance record is committed. This acceptance-record commit
is the H0 implementation base required by accepted R8-A. H0 must restart from
that base and freshly derive every source, path, mode, hash, tree, count, and
report input. No value or conclusion may be copied from the paused stash.

This decision does **not** accept H0; authorize H1, K3 execution, root
integration, an acceptance-pin refresh, or package-dependency changes;
authorize publication; or start R9 or any successor. Exact H0 acceptance is
still required before any privileged R8 work.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `8fa9d672cfcfb81ab68d9ed9553a5af48b884932` (`docs: propose narrow R8-A H0 integration revision`, tree `7754c5b19a34ed928710e6fe3c6cf716445f2187`) |
| Parent / comparison base | `cb0ac2a0f818ac57f2866cb7815767145608cf58` |
| Original accepted plan | `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` (parent `742ce4450dc85fc632d2ca7ff1061de09f3cf171`), responsible-human accepted 2026-08-07; it is an ancestor of the review target and remains immutable accepted history |
| Branch and repository | `beryllium/single-hart-runtime-r0`; packet-time private repository `jamorris_microsoft/beryllium`; current active private repository `beryllium-project/beryllium-hypervisor` |
| Target publication state | Local, unpushed, and untagged at packet preparation: zero remote branches and zero tags contain the review target |
| Current status | Plan revision R8-A is **accepted at exact target `8fa9d672cfcfb81ab68d9ed9553a5af48b884932` as of 2026-08-07**. The target's retained proposed/paused fields are frozen pre-decision content. The separately authorized non-privileged H0 work may resume only after this record commit and has not been started by this record; H0 is not accepted; K3 execution is `NOT RUN`. |
| Decision | Responsible-human acceptance of exact commit `8fa9d672cfcfb81ab68d9ed9553a5af48b884932` on 2026-08-07 by the explicit instruction `accept exact 8fa9d672cfcfb81ab68d9ed9553a5af48b884932` |
| Successor status | R8-H1 through R8-H4, K3 execution, root integration, package-dependency changes, R9, and every later successor remain blocked |
| Publication status | Public push, tag, publication, release, clean-repository migration, and any `pathfinder/publication-gate.conf` change remain blocked |

**Action taken:** the responsible human accepted exact R8-A target
`8fa9d672cfcfb81ab68d9ed9553a5af48b884932`. That decision covers plan text
only. After this acceptance record is committed, already authorized
non-privileged H0 work may resume from this record commit as its freshly
derived base. H0 remains unaccepted; H1, K3 execution, root integration,
package dependencies, publication, and successors remain blocked.

## 2. Deliverables and exact path inventory

The exact parent-to-target delta changes **96 paths**: **9 non-generated
paths** and **87 generated paths** under `docs/html/`, with 685 insertions and
410 deletions. All changed non-generated paths are planning,
current-position, or VitePress integration sources.

| Deliverable | Paths | Purpose | Trust / privilege boundary | Primary human question |
| --- | --- | --- | --- | --- |
| Plan revision R8-A | `planning/single-hart-runtime-r8-plan.md` (+210 / -16) | State the accepted-plan history, record the two discovered H0 plan defects, enumerate the exact documentation-support boundary, and define stable pre-commit/post-commit candidate identity | Planning text only; no H0 checker, runtime, privileged source, proof, fixture, or report is added | Does the correction solve both defects without widening H0 authority or weakening the original stop rules? |
| Maintained current position | `.github/copilot-instructions.md`, `README.md`, `planning/README.md`, `planning/HANDOFF.md`, `planning/implementation-plan.md`, `planning/roadmap.md`, `planning/riscv-security-hardware.md` | At target-review time, record original-plan acceptance, existing H0-only authorization, proposed R8-A status, paused H0, and K3 `NOT RUN` consistently | Documentation at the immutable target records pre-decision status; this acceptance-record follow-up now records the supplied decision | Did every target surface distinguish original-plan acceptance, R8-A proposal, H0 authorization, H0 acceptance, and hardware execution? |
| VitePress integration | `planning/.vitepress/config.mts` | At target-review time, label the accepted R8 plan with proposed R8-A status in existing navigation | Planning-site navigation only; this follow-up changes the label to review and acceptance record without changing the target | Did the target label remain decision-neutral before the separate decision? |
| Generated planning site | `docs/html/**` (87 changed entries) | Render the authoritative Markdown and navigation | Generated derivative; Markdown remains authoritative and byte-reproducibility remains open | Is the page usable and claim-consistent without treating generated byte churn as resolved? |

### Exact non-generated target inventory

```text
.github/copilot-instructions.md
README.md
planning/.vitepress/config.mts
planning/HANDOFF.md
planning/README.md
planning/implementation-plan.md
planning/riscv-security-hardware.md
planning/roadmap.md
planning/single-hart-runtime-r8-plan.md
```

Reproduce the complete target inventory with:

```sh
git diff --name-status -M \
  cb0ac2a0f818ac57f2866cb7815767145608cf58 \
  8fa9d672cfcfb81ab68d9ed9553a5af48b884932
git diff --numstat -M \
  cb0ac2a0f818ac57f2866cb7815767145608cf58 \
  8fa9d672cfcfb81ab68d9ed9553a5af48b884932 \
  -- . ':!docs/html'
```

The target changes no root `Makefile`, `be`, `scripts/check-be.sh`,
`package.json`, `package-lock.json`, `pathfinder/publication-gate.conf`,
implementation path under `include/`, `virt/`, or `arch/`, Model source,
R0-R7 package or acceptance checker, R8 implementation package, proof source,
or publication configuration.

### Exact R8-A support-boundary count

R8-A's support table contains **10 entries total**:

- **9 maintained support-source files**; and
- **1 generated prefix**, `docs/html/**`.

The nine maintained support sources are:

```text
.github/copilot-instructions.md
README.md
planning/README.md
planning/HANDOFF.md
planning/implementation-plan.md
planning/roadmap.md
planning/riscv-security-hardware.md
planning/.vitepress/config.mts
pathfinder/tests/check-docs-render.mjs
```

`pathfinder/tests/check-docs-render.mjs` is the ninth maintained support
source, but it is not changed by the revision target because no H0 freeze page
is delivered there. R8-A merely enumerates that path for the future H0
candidate's one planning-page inventory and title entry. The target itself
therefore has eight changed support sources, the revised plan, and the
generated prefix.

This record, its links, its navigation/renderer entries, and its generated
page are later decision support. They are not in the review target and do not
alter `planning/single-hart-runtime-r8-plan.md`.

## 3. Precise defect and correction

### Defect 1: documentation integration was required but unauthorized

The accepted H0 package-location table authorizes only
`planning/single-hart-runtime-r8-h0-freeze.md` and host-only sources under
`tests/r8/`. The accepted plan also requires a reviewed revision before any
path outside its inventory is added.

An H0 freeze is a planning Markdown page. Making that page reviewable requires
maintained current-position updates, VitePress navigation, the shared
direct-file planning-page inventory, and generated planning HTML. Without an
enumerated support boundary, either the documentation gate omits or rejects
the H0 page and current position, or the H0 source-boundary checker rejects
the documentation changes needed to pass that gate.

**Proposed correction:** enumerate exactly nine maintained support-source
files plus the generated `docs/html/**` prefix. Keep root dependencies,
wrappers, predecessor acceptance pins, accepted runtime/proof bytes, and every
other path excluded. Classify those support files as integration metadata,
not H0 authority or hardware evidence.

### Defect 2: one exact H0 candidate identity was undefined

The accepted plan did not define an identity relation that is stable before
and after the H0 candidate commit exists. Pinning the development HEAD, a
transient staged-index count, or a locally observed base would become
self-inconsistent at the committed candidate.

**Proposed correction:** define one future accepted base and two fail-closed
checker modes:

1. after exact R8-A acceptance is recorded, that later acceptance-record
   commit becomes the pinned H0 implementation base;
2. development mode requires `HEAD` equal to that base, the normal index equal
   to `HEAD`, and the candidate present only as enumerated worktree changes;
3. committed-candidate mode requires a clean worktree and index, with `HEAD`
   exactly one child of the pinned base and no extra intermediate commit;
4. both modes derive the same complete Git tree, maintained non-generated
   semantic projection, and semantic path count; and
5. generated documentation remains bound by the exact Git tree and path/mode
   boundary but is excluded from deterministic H0 authority, configuration,
   and report semantics.

Every future source, path, mode, hash, tree, count, report input, and base must
be freshly derived after acceptance. No paused diagnostic value may be copied.

## 4. Claim boundary and trusted assumptions

### What the exact target supports saying

- The accepted original R8 plan and its separate H0-only implementation
  authorization remain recorded and unchanged as historical decision
  boundaries.
- Local H0 work exposed a documentation-support deadlock and an unstable
  candidate-identity rule.
- Exact target `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`
  proposes a planning-only correction for those two defects.
- The proposed support boundary is exactly nine maintained source files plus
  one generated prefix.
- The proposed identity rule distinguishes a future accepted base,
  development mode, committed-candidate mode, exact Git identity, and
  deterministic non-generated semantics.
- H0 is paused, H0 is not accepted, and K3 execution is `NOT RUN`.

### What the target does not support saying

- That R8-A has been reviewed or accepted.
- That any H0 implementation, freeze, parser, checker, fixture, report,
  inventory, hash, count, tree, or base is correct, complete, or accepted.
- That the paused H0 stash is evidence or can supply a future pinned value.
- That R8-H1, privileged execution, K3 measurement, root integration,
  package dependencies, or successor work is authorized.
- That any hardware, QEMU/K3 comparison, C refinement, whole-image proof,
  whole-system verification, certification, production, or publication
  result exists.

### Trusted or assumed

- Git commit, parent, tree, blob, path, and mode identity behave as used by
  the proposed checker contract.
- A future H0 checker can construct a prospective tree without mutating the
  normal index and can derive the same semantic projection in both modes.
- The accepted R0-R7 targets and the original R8 plan/authorization records
  mean exactly what their existing acceptance records state.
- VitePress and the shared Chromium renderer are functional documentation
  tools, not security authorities.
- The private repository, local host, future K3 lab procedure, compilers,
  firmware, capture tooling, and eventual H0 implementation remain trusted or
  unevaluated as bounded by the original accepted plan.

### Evidence unavailable or `NOT RUN`

- No H0 candidate or H0 evidence bundle exists for review.
- No H0 exact-target validation exists.
- R8-H1 through R8-H4 have not started.
- K3 execution and hardware validation are `NOT RUN`.
- The generated-asset byte-reproducibility finding remains open.
- The paused local stash is preservation only, not evidence.

## 5. Security and correctness invariants

These are proposed plan obligations. They are not implemented properties.

| Invariant | Contract | Enforcement or evidence point | Current status |
| --- | --- | --- | --- |
| Original accepted plan identity remains immutable history | R8-A `Status and authority`; original R8 review record | Git identity `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`; target ancestry and exact diff | PASS as Git history; R8-A does not rewrite the accepted object |
| Support boundary is exact and finite | R8-A `Exact H0 support-path boundary` | Future H0 path/mode checker and complete candidate inventory | Proposed: 9 source files + 1 generated prefix |
| No root dependency, wrapper, pin, runtime, proof, or R0-R7 widening | R8-A exclusions and stop rules | Future changed-path/mode checks; existing predecessor acceptance interfaces | Target audit passes; future H0 enforcement remains unimplemented |
| H0 base cannot be guessed or copied from paused work | R8-A `Future accepted base` and paused-discovery rules | Future exact full-SHA base pin after a decision-record commit exists | Base intentionally unknown |
| Development and committed modes reject every other repository relation | R8-A `Exact pre-commit and post-commit identity` | Future H0 checker | Proposed; not implemented |
| Prospective and committed candidate semantics are equivalent | R8-A `Prospective/post-commit equivalence` | Future prospective-tree construction and semantic-projection comparison | Proposed; no H0 candidate exists |
| Generated docs affect exact Git identity but not H0 security semantics | R8-A `Generated-documentation exclusion` | Future tree binding plus bounded report fields | Proposed; open generated-byte finding remains |
| H0 remains paused until exact R8-A acceptance is recorded | R8-A status and current-position records | Human decision record and maintained status | Enforced procedurally; H0 stash remains untouched |
| H0 acceptance still precedes H1 or K3 execution | Original accepted plan plus R8-A non-goals | Separate exact H0 review and decision | H0 not accepted; H1-H4 blocked; K3 `NOT RUN` |

## 6. Review history and findings

### Prior decisions

1. The responsible human accepted exact original R8 plan target
   `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` on 2026-08-07.
2. A later separate instruction, `Authorize R8 implementation under accepted
   plan 7d0f0cbf…; proceed with R8-H0`, authorized only non-privileged H0
   work. It did not accept H0 or authorize privileged work.

### Findings that caused the pause

Local, unaccepted H0 implementation and review work found:

1. the accepted path inventory required documentation integration without
   authorizing the support paths needed to perform it; and
2. the accepted identity rule lacked one stable relation spanning prospective
   development content and an exact committed child.

These are plan defects, not permission to widen implementation. H0 was paused
before any candidate was committed or presented for acceptance.

### Local preservation boundary

The paused H0 work remains local in stash object
`03b8ed9dd9c0e2e4514f6e47196a819537acb509`
(`r8-h0-paused-for-r8a`). Packet preparation did not restore, apply, pop,
drop, modify, or inspect the stash contents.

The stash is **not** part of the review target, is **not** H0 evidence, and
must not supply a future source list, mode, hash, path count, tree, report
digest, or base. If R8-A is accepted, H0 restarts from the later
acceptance-record base and re-derives every value.

### Proposed resolution in the exact target

The target supplies only:

- the exact ten-entry support table: nine maintained source files plus one
  generated prefix;
- explicit exclusions and mode requirements;
- a future accepted-base rule;
- development and committed-candidate modes;
- prospective/post-commit equivalence;
- generated-documentation semantic exclusion; and
- H0 candidate gates after acceptance.

### Open questions requiring human judgment

- Is the nine-source-plus-one-prefix boundary complete and minimal?
- Is `pathfinder/tests/check-docs-render.mjs` acceptably limited to one shared
  planning-page inventory/title change with no Helium behavior or claim
  change?
- Is the later acceptance-record commit the correct H0 implementation base?
- Are the clean-index development relation and one-child committed relation
  strict enough without blocking a reviewable workflow?
- Does excluding generated docs from H0 semantics while retaining them in the
  exact Git tree preserve both reviewability and stable security meaning?
- Is a full stop, rather than any automatic widening, still the correct
  response to an eleventh support entry, a root dependency, or another
  repository relation?

### Open generated-asset finding

The planning site remains functionally checked, but hash-named generated
assets are not known to reproduce byte-for-byte across clean rebuilds. R8-A
does not close that finding. Generated HTML remains derivative and confined to
`docs/html/`; authoritative claims remain in Markdown.

## 7. Validation and retained evidence

All checks below were run on 2026-08-07 UTC.

| Command or check | Execution boundary | Result and coverage |
| --- | --- | --- |
| Phase-one changed-path audit | Final pre-commit content that became the exact target | PASS: every changed path was the R8 plan, an enumerated current-position/VitePress source, or `docs/html/**`; no implementation, root wrapper/build, R0-R7 package, dependency, or publication-gate path |
| `git diff --check` | Final pre-commit target content | PASS |
| Original-target resolution and ancestry | Exact Git objects | PASS: `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` resolves as a commit and is an ancestor of the review target |
| `git diff --check cb0ac2a0… 8fa9d672…` | Exact immutable target | PASS |
| `git fsck --no-dangling 8fa9d672…` | Exact immutable target | PASS |
| Exact inventory and mode audit | Exact immutable target | PASS: 96 changed paths = 9 non-generated + 87 generated; all maintained source modes remain regular `100644`; no forbidden path |
| Support-table count | Exact immutable target plan | PASS: 10 entries = 9 maintained support-source files + 1 generated prefix |
| Remote/tag containment | Exact immutable target | PASS: zero remote branches and zero tags contain the target at packet preparation |
| `./be docs-check` | Final pre-commit packet/current-position/navigation/renderer content | PASS: 64 planning Markdown sources, 65 generated HTML pages, no broken local targets, and 64 planning pages rendered in Chromium; 12 Helium sources, 13 pages, and 12 browser-rendered pages also passed |
| `make check` | Final pre-commit packet content | PASS: complete existing repository gate, including the existing Helium, Model, R0-R7, evidence, wrapper, and documentation checks; this adds no R8 runtime or K3 execution evidence |
| `git diff --check` | Final pre-commit packet delta | PASS |
| `git diff --quiet 8fa9d672… -- planning/single-hart-runtime-r8-plan.md` | Packet delta against the exact review target | PASS: the reviewed R8-A plan file is byte unchanged |
| Stash-presence check | Local preservation state after validation | PASS: object `03b8ed9dd9c0e2e4514f6e47196a819537acb509` remains present |

The exact-target Git checks validate the immutable R8-A commit. The later
`./be docs-check` and `make check` executions validate this packet and its
documentation integration in the descendant pre-commit worktree; they do not
substitute for an exact clean-commit H0 run and must not be described as H0 or
K3 evidence.

Retained review evidence consists of:

- exact target, parent, tree, subject, and timestamps in Git;
- exact parent-to-target inventory and diff;
- authoritative revised plan and current-position Markdown;
- generated planning-site derivatives;
- command results from this private preparation session; and
- the retained decision-support packet and this acceptance record.

No H0 report, hardware trace, K3 result, proof, or evidence bundle is retained
because none exists.

## 8. Recommended human review sequence

Use an isolated detached worktree so unrelated local state and the paused H0
stash cannot affect review:

```sh
git worktree add --detach \
  ../beryllium-r8a-review \
  8fa9d672cfcfb81ab68d9ed9553a5af48b884932
cd ../beryllium-r8a-review
git status --short
git show --no-patch --format=fuller \
  8fa9d672cfcfb81ab68d9ed9553a5af48b884932
git diff --check \
  cb0ac2a0f818ac57f2866cb7815767145608cf58 \
  8fa9d672cfcfb81ab68d9ed9553a5af48b884932
```

1. Read the original accepted plan status and the original
   [R8 review and acceptance record](single-hart-runtime-r8-plan-review-summary.md).
   Confirm that original plan acceptance, H0-only implementation authority,
   R8-A acceptance, H0 acceptance, and K3 execution are distinct.
2. Review only the R8-A plan delta first:

   ```sh
   git diff \
     7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5 \
     8fa9d672cfcfb81ab68d9ed9553a5af48b884932 \
     -- planning/single-hart-runtime-r8-plan.md
   ```

3. Review the two defect statements. Confirm that each was a plan
   inconsistency rather than implementation permission.
4. Count and review the exact support table: nine maintained sources plus the
   generated prefix. Pay special attention to the shared renderer exception
   and the root/dependency/pin exclusions.
5. Review future accepted-base, development-mode, committed-candidate, and
   prospective/post-commit equivalence semantics as one identity protocol.
6. Review the generated-documentation exclusion. Confirm that generated bytes
   remain part of exact Git identity without changing H0 authority or report
   semantics.
7. Audit the exact non-generated inventory and current-position claims:

   ```sh
   git diff --name-status \
     cb0ac2a0f818ac57f2866cb7815767145608cf58 \
     8fa9d672cfcfb81ab68d9ed9553a5af48b884932 \
     -- . ':!docs/html'
   git diff \
     cb0ac2a0f818ac57f2866cb7815767145608cf58 \
     8fa9d672cfcfb81ab68d9ed9553a5af48b884932 \
     -- . ':!docs/html'
   ```

8. Confirm the paused stash is irrelevant to the decision. Do not restore it
   for plan review; the target is complete without it.
9. Optionally run the functional documentation gate in the detached
   worktree:

   ```sh
   npm ci
   ./be docs-check
   ```

   Generated `docs/html/` dirtying may reproduce the open byte-reproducibility
   finding. Functional PASS does not close that finding.

## 9. Human decision checklist

### Technical review

- [ ] The exact target is
      `8fa9d672cfcfb81ab68d9ed9553a5af48b884932` over parent
      `cb0ac2a0f818ac57f2866cb7815767145608cf58`.
- [ ] The revision scope matches the accepted original R8 plan and changes no
      implementation, runtime, proof, root wrapper/build, dependency, R0-R7
      package, acceptance pin, or publication gate.
- [ ] The documentation-support deadlock and candidate-identity defect are
      stated accurately.
- [ ] The support boundary is exactly nine maintained source files plus one
      generated prefix, with no missing or unnecessary entry.
- [ ] The future accepted-base rule and the two repository modes are
      unambiguous and fail closed.
- [ ] Prospective and committed candidate semantics are equivalent without
      using a staged index count or copied diagnostic value.
- [ ] Generated documentation is correctly included in exact Git identity
      and excluded from H0 security semantics.
- [ ] Claims match the evidence: this is planning-only, H0 has no accepted
      result, the stash is not evidence, and K3 is `NOT RUN`.
- [ ] Trusted assumptions and the open generated-asset finding are acceptable.
- [ ] Important negative paths are explicit: extra support paths, another
      repository relation, root dependencies, pin refreshes, and common-core
      changes all stop rather than widen.
- [ ] H1, K3 execution, root integration, package dependencies, publication,
      and successor work remain excluded.

### Decision

- [x] **Decision:** accept exact
      `8fa9d672cfcfb81ab68d9ed9553a5af48b884932` /
      ~~request revisions~~ / ~~defer~~.

Only the decision box above is checked because that decision was explicitly
supplied by the responsible human on 2026-08-07. The technical-review boxes
remain unchecked as review history. No signature is generated.

## 10. After the decision

### Recorded outcome: the exact commit is accepted

Exact R8-A plan-revision target
`8fa9d672cfcfb81ab68d9ed9553a5af48b884932` (parent
`cb0ac2a0f818ac57f2866cb7815767145608cf58`) was accepted on 2026-08-07 by
the exact instruction quoted above. Packet commit
`9ad001bdbcb41aa7c86b406b80f62a6c9820e08c` and this acceptance-record
follow-up are decision support, not plan text or H0 implementation.

After this record is committed, the already authorized non-privileged H0 work
may resume under the accepted original R8 plan plus accepted R8-A. The full
SHA of this acceptance-record commit is the required H0 implementation base.
H0 must begin from that base, keep the normal index equal to `HEAD`, and
freshly re-derive every source, path, mode, hash, tree, semantic projection,
count, and report input. The paused stash remains preservation only and must
not supply a value or conclusion.

Acceptance of R8-A accepts **no H0 implementation, freeze, parser, checker,
fixture, report, inventory, digest, tree, or evidence claim**. It authorizes
no H1, K3 execution, root integration, acceptance-pin refresh, dependency
change, Linux, multicore, device, DMA, policy, publication, release, or
successor work. Exact H0 acceptance remains a separate gate before privileged
R8 work.

### Not taken: request revisions

Had revisions been requested, H0 would have remained paused, a new
plan-revision commit and review packet would have been required, and
`8fa9d672cfcfb81ab68d9ed9553a5af48b884932` would not have been treated as
accepted.

### Not taken: defer

Had review been deferred, R8-A would have remained proposed and H0 would have
remained paused. K3 would have stayed `NOT RUN`, and no dependent work would
have started.

---

**Status:** exact R8-A target
`8fa9d672cfcfb81ab68d9ed9553a5af48b884932` (parent
`cb0ac2a0f818ac57f2866cb7815767145608cf58`) is **accepted** as of
2026-08-07. The accepted original R8 plan remains exact and unchanged. H0 is
authorized to resume only after this record commit but is not started or
accepted by this record. K3 execution and hardware validation remain
`NOT RUN`; push, tag, publication, and release remain blocked.

**Next:** the already authorized non-privileged H0 work may resume in a later
task from the full SHA of this acceptance-record commit, with every candidate
input and identity freshly derived. H0 still requires its own exact-commit
review and separate acceptance before H1 or K3 execution.

**Action required from you:** none for this decision. R8-A acceptance is
recorded. H0 implementation, H0 acceptance, H1, K3 execution, root
integration, dependency changes, publication, and successors require their
existing separate gates.
