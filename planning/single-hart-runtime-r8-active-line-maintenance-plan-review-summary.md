<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium R8 active-line maintenance plan responsible-human review summary

This is the decision-neutral responsible-human review packet for exact
R8-ALM1 plan target `6bb3349b266a43d4572465379b5892b058e2fe39`,
whose immediate parent is
`2b404ca31a07e1a0783a44183d0b2de95d053618` and whose Git tree is
`730a77942be1079b1d1bb4e13ec1166cd30d4861`. The target's authoritative
plan is
[`single-hart-runtime-r8-active-line-maintenance-plan.md`](single-hart-runtime-r8-active-line-maintenance-plan.md).
Its retained status is `proposed-not-reviewed`.

The review target is immutable and remains byte unchanged. Independent review
found two significant open defects. The recommended responsible-human decision
is therefore **request revisions**, not acceptance. This packet does not record
or infer a human decision.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `6bb3349b266a43d4572465379b5892b058e2fe39` (`docs: add R8 active-line maintenance plan`), parent `2b404ca31a07e1a0783a44183d0b2de95d053618`, tree `730a77942be1079b1d1bb4e13ec1166cd30d4861` |
| Plan identity | `R8-ALM1`; plan blob `a08a1ba6e939f4b3cdfe785b36770963a5a5c564`; SHA-256 `3ad6e9d688427204c15852b360e6d54f85d7cb7999f140c6b3759823f51a08f0`; 27,009 bytes / 631 lines |
| Branch and repository | `beryllium/single-hart-runtime-r0`; private repository `beryllium-project/beryllium-hypervisor`; target was one local commit ahead of its private upstream at review start |
| Current status | Planning and documentation target only; exact-target documentation checks pass functionally; target remains `proposed-not-reviewed`; implementation is not authorized; independent review found two revision-required findings |
| Review verdict | **Request revisions recommended.** The future implementation base/relation is not coherent with retained review/acceptance history on the active line, and the target misstates the exact current-line `r8-check` failure boundary |
| Decision requested | Accept the exact target despite the open findings, request a corrected plan target and new packet, or defer |
| Successor status | No R8-ALM1 implementation exists or is authorized. R8-H1 through R8-H4, a COM260-informed H0 successor, K3 execution, and hardware validation remain blocked or `NOT RUN` |
| Publication status | Target and this packet are private and local. No push, tag, publication, release, migration, or `pathfinder/publication-gate.conf` change is authorized |

**Action expected:** review the two open findings first, then explicitly choose
accept, request revisions, or defer for exact target
`6bb3349b266a43d4572465379b5892b058e2fe39`. Plan acceptance alone would
authorize no implementation.

## 2. Deliverables and exact target inventory

The target changes **111 paths** without rename detection:

- seven maintained paths: six modified and one added;
- 104 generated planning-site paths under `docs/html/**`: 77 modified,
  15 added, and 12 deleted; and
- no mode other than regular `100644` for any present target path.

The seven maintained paths are:

```text
100644 pathfinder/tests/check-docs-render.mjs
100644 planning/.vitepress/config.mts
100644 planning/HANDOFF.md
100644 planning/README.md
100644 planning/implementation-plan.md
100644 planning/roadmap.md
100644 planning/single-hart-runtime-r8-active-line-maintenance-plan.md
```

| Deliverable | Paths | Purpose and trust boundary | Highest-value review question |
| --- | --- | --- | --- |
| R8-ALM1 plan | `planning/single-hart-runtime-r8-active-line-maintenance-plan.md` | Defines a planning-only, non-claiming active-line maintenance identity, future path/mode closure, fail-closed correction, environment, validation, and stop rules. It changes no checker or implementation byte | Is the future base/relation implementable without rewriting active-line review history, and are current versus historical failure facts stated exactly? |
| Current-position integration | `planning/README.md`, `planning/HANDOFF.md`, `planning/implementation-plan.md`, `planning/roadmap.md` | Exposes the proposed plan while preserving accepted R8/R8-A/R8-C, accepted H0, K0-S, H1-H4, hardware, and publication boundaries | Do these pages distinguish historical defect reproduction, exact current-line behavior, accepted-target evidence, and implementation authority? |
| Navigation and browser inventory | `planning/.vitepress/config.mts`, `pathfinder/tests/check-docs-render.mjs` | Adds one planning route and exact page title. It changes no Helium page, source, claim, command, or component behavior | Does the route remain planning-only and decision-neutral? |
| Generated planning site | `docs/html/**` | Reviewable derivative of maintained Markdown and navigation | Does the rendered site correspond functionally while retaining the known generated-byte reproducibility finding? |

The target changes no:

- accepted R8 plan, R8-A, R8-C, or H0 target byte;
- `planning/single-hart-runtime-r8-plan.md` or
  `planning/single-hart-runtime-r8-h0-freeze.md`;
- file under `tests/r8/**`;
- root `Makefile`, `be`, or `scripts/check-be.sh`;
- dependency manifest or lock;
- accepted R0-R7 mechanism, proof, checker, evidence input, or acceptance pin;
- KVM0/K0-S source, package, route, readiness, or result record;
- Helium source, Helium documentation source, or Helium generated path; or
- publication configuration.

## 3. Claim boundary

### What the exact target supports saying

- `R8-ALM1` is a clear, separate identity. It is not Plan revision R8-B, not
  an R8 H0 successor, and not part of the H0-H4 implementation sequence.
- The historical active-line H0 package introduced at
  `102f2b0569396bf33ed2177ea5b7558cf5e6fbaa` retains 147 rows, 119
  `UNKNOWN` values, and 81 H0-acceptance blockers.
- Exact accepted H0/R8-C target
  `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` remains separate, immutable,
  accepted, blocked, and not exit-ready with 147 rows, 118 `UNKNOWN` values,
  and 80 H0-acceptance blockers.
- The bounded correction concept is to remove only the cloned
  `tests/r8` tree immediately before the existing package overlay, using the
  unchanged fail-closed `safeRemove` and `safeCopyTree` primitives.
- The proposed future implementation closure contains ten R8 behavior/lock
  paths, four maintained current-position paths, and generated planning
  derivatives only. No root integration or predecessor acceptance-pin refresh
  is necessary for the stated direct checked-launcher objective.
- The proposed active-line validation environment is open and reconstructible
  from retained inputs. The exact accepted-target execution environment is
  unavailable and must not be substituted.

### Trusted or assumed

- Git commit, parent, tree, blob, path, mode, index, and replacement-ref
  behavior are trustworthy within the stated checks.
- The checked static launcher, Node.js, GCC, coreutils, Fedora OCI inputs,
  Podman/crun boundary, VitePress, Chromium, and ordinary host filesystem
  semantics behave as observed at their recorded identities.
- The existing `safe-paths.mjs` confinement, ownership, mode, link-count,
  descriptor, identity-revalidation, and bounded cleanup checks are correct.
- The accepted R0-R8 and K0-S records mean exactly what their existing review
  and acceptance records state.

### Evidence unavailable or `NOT RUN`

- No R8-ALM1 implementation target, report, launcher rebuild, maintenance
  projection, or candidate validation exists.
- Fresh executable replay of accepted target `1999ee70...` remains unavailable
  because its exact selected OCI archive and Node executable are absent.
- R8-H1 through R8-H4 have not started.
- K3 execution and all Beryllium hardware validation remain `NOT RUN`.
- Generated planning bytes are not reproducible at the immutable target in
  the current documentation environment, although functional gates pass.

### What the target does not implement, prove, or authorize

- No H0 acceptance, readiness, successor status, evidence transfer, or new H0
  fact.
- No privileged Beryllium C, assembly, linker, image, CSR, QEMU, guest,
  device, DMA, Linux, service, multicore, policy, proof, or hardware behavior.
- No accepted-target environment reconstruction or accepted-target rerun.
- No KVM0/K0-S route, package, readiness, execution, result, BSP, or hardware
  change.
- No root integration, dependency change, predecessor-pin refresh, push, tag,
  publication, release, migration, archival, or publication-gate approval.

## 4. Security and correctness invariants

| Invariant | Contract or implementation point | Review result |
| --- | --- | --- |
| Maintenance identity remains distinct from R8-B and H0 | R8-ALM1 `Status and authority`; plan identity envelope | **PASS.** Naming is clear and does not import authority from the unrelated R8-B object or accepted H0 |
| Accepted H0 evidence and status do not transfer | Plan status, report-envelope requirements, explicit non-claims | **PASS.** Historical 81-blocker and accepted 80-blocker states remain separately attributed |
| Plan acceptance and implementation authorization are separate | Plan status and four decision gates | **PASS.** The plan repeatedly states that acceptance alone authorizes no implementation |
| Future candidate identity is stable and implementable | Future implementation base/parent/relation sections | **OPEN - REVISION REQUIRED.** The required direct-child relation conflicts with preserving this packet and a later acceptance record on the active line |
| Exact current-line failure is represented accurately | Status fields, current-position pages, problem statement, validation rationale | **OPEN - REVISION REQUIRED.** Exact current target exits silently during launcher authentication; only the historical source reaches the first whole-diff fixture |
| Copy destination absence remains fail closed | Unchanged `tests/r8/safe-paths.mjs`; planned `safeRemove` then `safeCopyTree` sequence | **PASS as a plan obligation.** No overwrite, merge, replace, best-effort cleanup, or shared-primitive weakening is authorized |
| Future implementation path authority is finite | Ten R8 paths, four current-position paths, generated planning prefix | **PASS with the relation finding unresolved.** No additional lock, root, dependency, or pin path was identified during review |
| Accepted target remains protected | Inspection-only reference to `1999ee70...`; no accepted-target execution substitution | **PASS.** Exact Git identity and bounded removal were independently inspected; executable replay remains explicitly unavailable |
| K0-S and current project gates remain separate | Roadmap, handoff, K0-S acceptance record | **PASS.** R8-ALM1 grants no K0-S, K0-X/K0-R, B0/B1, BSP, or hardware authority |
| Publication and human decision remain human-controlled | `LLM_POLICY_ALIGNMENT.md`; plan non-claims | **PASS.** No human signoff, acceptance inference, push, tag, publication, or gate change is present |

## 5. Review history and findings

### Authoritative review inputs

The review compared the target against:

- accepted R8 plan target
  `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`;
- accepted R8-A target
  `8fa9d672cfcfb81ab68d9ed9553a5af48b884932` and its accepted
  acceptance-record-base convention;
- accepted R8-C target
  `f47ae60266a467ca1a7704fd9a50b140e0f31bb0`;
- accepted H0/R8-C target
  `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4`;
- historical H0 source
  `102f2b0569396bf33ed2177ea5b7558cf5e6fbaa` and parent
  `1f6109f0d0371eb3707e296c3416e8c55235683e`;
- the current active-line bytes at the immutable review target;
- the accepted K0-S current project boundary; and
- `LLM_POLICY_ALIGNMENT.md`.

The two session decision packets and blocked metadata were independently
rehash-verified:

```text
fbf7a5d8ff82f14421cc2673104f29620b00a5c21b8eddf3ecebb4984fc69d92  r8-rejection-test-correction-decision-2026-09-29.md
2f54637ba1706e5e6c932472880ee2fb329c7e1f58f739d4debd6364b0af62f2  r8-maintenance-revision-decision-2026-09-29.md
13340156ceb7920f88f22dfea70976d69cfe189d692e3589c3b961b31c939ed4  blocked-metadata-2026-09-29.json
```

These files remain session-local decision support, not maintained R8 evidence.

### Closed review questions

1. **Goal and naming clarity.** `R8-ALM1` avoids the already-used R8-B label
   and clearly excludes H0-successor and implementation authority.
2. **Implementation inventory.** The ten behavior/lock paths close the
   checker, report, AST, bootstrap, launcher, Make output, documentation, and
   rejection-test consequences. The four maintained current-position paths
   and generated planning prefix are sufficient. No root wrapper, dependency,
   predecessor pin, H0 profile/row/claim contract, or navigation change is
   needed in the future implementation candidate.
3. **Correction semantics.** Keeping `safe-paths.mjs` byte unchanged and
   inserting bounded removal only after clone-mode normalization preserves
   confinement, destination-absence, symlink, ownership, mode, special-file,
   identity-revalidation, and sentinel invariants.
4. **Environment separation.** The active-line maintenance environment is
   retained in the ignored isolated validation tree and has an exact base
   archive, package bytes, recipe, image identities, and tool probes. The
   plan correctly requires a newly exported, independently hashed OCI archive
   before candidate evidence. The unavailable accepted-target environment is
   inspection-only and cannot be replaced by the predecessor image.
5. **Validation and exclusions.** Two fresh worktree/volume runs, launcher
   rebuild equivalence, named negative cases, cross-run semantic comparison,
   R0-R7 gates, root `make check`, accepted-target protection, explicit stops,
   and hardware/publication exclusions are appropriately broad for the
   proposed maintenance boundary.

### Open finding 1 - implementation base and active-line relation

**Severity:** significant; plan revision required before acceptance is
recommended.

The target requires a future maintenance candidate to be:

1. on active branch `beryllium/single-hart-runtime-r0`; and
2. exactly one clean non-merge child of the accepted R8-ALM1 plan target
   `6bb3349b266a43d4572465379b5892b058e2fe39`, with no intermediate commit.

This review packet is necessarily a child of that target. A later
responsible-human acceptance record would add another decision-support commit.
After either commit exists on the active line, an implementation candidate
cannot also be the target's direct child while preserving the active-line
history. Producing such a candidate would require a side branch not matching
the stated active-line relation, a history rewrite, dropping the packet and
acceptance record from the branch, or silently changing the parent rule.

Accepted R8-A avoided this conflict by defining the later
acceptance-record commit as the implementation base. That precedent provides
a coherent prospective/committed identity without rewriting decision history.

**Required resolution:** a corrected plan must either:

- define the future acceptance-record commit, or another exact later
  responsible-human-selected current-line commit, as the implementation base;
  or
- explicitly define a reviewed side-branch and later reconciliation model
  that preserves the packet, acceptance record, active-line ancestry, and one
  exact candidate relation.

The corrected relation must still require one exact full SHA, one clean
non-merge child, no intermediate implementation commit, and a new exact-target
review. This packet commit is decision support and must not be inferred to be
an implementation base.

### Open finding 2 - current-line failure boundary is misstated

**Severity:** significant; factual correction and validation revision
required.

The target and its current-position pages say active-line `r8-check` is
blocked at the first whole-diff fixture. That is true only for the restored
historical source at `102f2b...` in the retained maintenance environment.

At exact current target `6bb3349...`:

- all `tests/r8/**` blobs remain identical to historical source `102f2b...`;
- current `planning/single-hart-runtime-r8-plan.md` is the accepted R8-C blob,
  SHA-256
  `d7a0c4c3633cbd9e50b8f8989b140eaa4a848587e7b4a0ed0ea7fc920bc6e6e0`;
- the checked launcher still authenticates the historical R8-A plan SHA-256
  `13f1b2482fdf21017a94c957be841477af452d68b4ce628ccd2fdc388b521b14`;
  and
- direct exact-target execution of
  `./tests/r8/run-make.sh r8-check` exits `126` with zero stdout and zero
  stderr before GNU Make or the first whole-diff fixture.

The retained restoration report already states that the current worktree was
rejected before any R8 check because later planning bytes no longer match the
embedded bootstrap table. Historical source `102f2b...` separately reaches
the first whole-diff fixture and exits `2` on the existing destination.

**Required resolution:** a corrected plan and current-position text must
distinguish:

1. exact current-line pre-authentication rejection caused by authenticated
   plan/support drift; and
2. the historical-package whole-diff defect reproduced at `102f2b...`.

The validation matrix must prove both boundaries: first demonstrate the exact
current-line silent rejection, then prove the future launcher/checker lock
closure authenticates the corrected active-line package and reaches/passes the
whole-diff baseline. The disposable removal regression may continue to prove
the historical first-fixture failure, but it cannot stand in for the
current-line entry-boundary test.

### Retained open generated-output finding

A clean exact-target planning rebuild passes all functional checks but changes
only `docs/html/**`, including hash-named application, search, and theme
assets. This is the existing generated-byte reproducibility finding. It is not
an R8-ALM1 source or identity defect, and the target does not claim to close
it. Any future candidate must still restore and prove exact Helium generated
state and confine committed regenerated output to planning HTML.

## 6. Validation and retained evidence

All review execution below occurred on 2026-09-29. No check changed the
immutable target.

| Command or check | Execution boundary | Result and coverage |
| --- | --- | --- |
| Commit, parent, tree, plan blob, subject, timestamp, ancestry, remote, and tag audit | Exact Git objects | PASS: supplied commit/parent/tree match; target is private, local, unpushed, untagged, and contained by zero remote-tracking branches |
| `git fsck --no-dangling 6bb3349...` | Exact target | PASS |
| `git diff --check 2b404ca... 6bb3349...` | Exact target | PASS |
| Exact changed-path and mode audit | Exact target | PASS: 111 paths; seven maintained paths and 104 `docs/html/**` paths; all present target paths regular mode `100644`; no symlink, executable, special, Helium, runtime, checker, dependency, root, pin, or publication path |
| Session packet and blocked-metadata SHA-256 verification | Session-local read-only inputs | PASS: all three hashes match the plan |
| R8 source/blob comparison at `1f6109...`, `102f2b...`, current target, and accepted `1999ee...` | Exact Git objects | PASS: H0 package introduced after `1f6109...`; current `tests/r8/**` equals `102f2b...`; current plan differs; accepted target contains bounded removal at lines 593-594 |
| Independent profile count derivation | Exact JSON blobs | PASS: historical/current package 147 rows / 119 `UNKNOWN` / 81 H0 blockers; accepted target 147 / 118 / 80 |
| Exact current-line checked-launcher probe | Fresh detached worktree at `6bb3349...` | Expected rejection confirmed: exit `126`, zero stdout, zero stderr, before the historical whole-diff fixture |
| `npm ci`; `node --check pathfinder/tests/check-docs-render.mjs` | Fresh detached worktree at exact target | PASS |
| `HE_CHROMIUM=... npm run docs:check` | Fresh detached exact-target worktree | PASS: planning diagrams, portable and HTTP planning builds, 76 Markdown sources, 77 HTML pages, no broken local targets, 76-page Chromium `154.0.8037.57` HTTP/direct-file/responsive rendering |
| Post-`npm run docs:check` status | Same exact-target worktree | Known open finding reproduced: changes confined to `docs/html/**`; no maintained source or Helium path changed |
| `HE_CHROMIUM=... ./be docs-check` | Restored fresh detached exact-target worktree | PASS: planning and Helium documentation checks, links, browser rendering, direct-file rendering, and responsive/mobile checks |
| Helium generated-state preservation | Exact-target wrapper run | PASS: 66-file pre/post content-and-mode manifest SHA-256 remained `574cdc6622b042c5287b98a745d910324718a222decb08bb23e26fa0f69b93ec`; zero Helium dirty entries before restoration; planning and Helium generated trees restored to exact target; final worktree clean |
| `git diff --check`; JS/TS syntax; immutable-plan audit | Final pre-commit review-packet sources | PASS: review packet and minimum navigation/browser/current-position sources only; `planning/single-hart-runtime-r8-active-line-maintenance-plan.md` remains byte unchanged |
| `npm run docs:build`; `HE_CHROMIUM=... npm run docs:check` | Final pre-commit review-packet content | PASS: planning diagrams, portable and HTTP builds, 77 Markdown sources, 78 HTML pages, no broken local targets, and 77-page Chromium `154.0.8037.57` HTTP/direct-file/responsive rendering |
| `HE_CHROMIUM=... ./be docs-check` plus Helium restoration | Final pre-commit review-packet content | PASS: root planning and Helium documentation gate; Helium 12-source/13-page link and browser checks; 66-file pre/post Helium manifest remained byte/mode identical at SHA-256 `574cdc6622b042c5287b98a745d910324718a222decb08bb23e26fa0f69b93ec`; zero Helium dirty entries before restoration |

These checks validate the planning target, review facts, and documentation
integration only. They do not implement R8-ALM1, validate a future candidate,
replay accepted H0, establish H0 readiness, authorize H1-H4, or produce K3,
runtime, proof, hardware, publication, or release evidence.

## 7. Recommended human review sequence

1. **Review the two open findings first.** Read this packet's finding sections,
   then the target's `Future implementation base, parent, and relation`,
   `Status and authority`, `Problem statement`, and `Future validation plan`.
2. **Inspect the exact target boundary.**

   ```sh
   git show --no-ext-diff --stat --summary \
     6bb3349b266a43d4572465379b5892b058e2fe39
   git diff --name-status --no-renames \
     2b404ca31a07e1a0783a44183d0b2de95d053618 \
     6bb3349b266a43d4572465379b5892b058e2fe39
   git ls-tree \
     6bb3349b266a43d4572465379b5892b058e2fe39 \
     planning/single-hart-runtime-r8-active-line-maintenance-plan.md
   ```

3. **Compare the identity model with accepted R8-A precedent.**

   ```sh
   git show \
     8fa9d672cfcfb81ab68d9ed9553a5af48b884932:planning/single-hart-runtime-r8-plan.md
   less planning/single-hart-runtime-r8-plan-r8a-review-summary.md
   ```

   Confirm why R8-A used the later acceptance-record commit as the
   implementation base.

4. **Inspect current versus historical failure facts.**

   ```sh
   git diff --quiet \
     102f2b0569396bf33ed2177ea5b7558cf5e6fbaa \
     6bb3349b266a43d4572465379b5892b058e2fe39 \
     -- tests/r8

   git diff \
     102f2b0569396bf33ed2177ea5b7558cf5e6fbaa \
     6bb3349b266a43d4572465379b5892b058e2fe39 \
     -- planning/single-hart-runtime-r8-plan.md

   git show \
     102f2b0569396bf33ed2177ea5b7558cf5e6fbaa:tests/r8/run-make.c |
     grep -A1 -B1 'planning/single-hart-runtime-r8-plan.md'
   ```

5. **Review inventory and fail-closed semantics.** Confirm the ten R8 paths,
   four current-position paths, frozen `safe-paths.mjs`, zero root/pin
   refreshes, and named negative tests.
6. **Review claims and exclusions.** Confirm no accepted H0, K0-S, H1-H4,
   hardware, runtime, proof, publication, or successor authority transfers.
7. **Make the decision.** Requesting revisions is recommended. Any corrected
   plan must be a new exact commit with a new review packet.

For any rerun, use an isolated detached worktree:

```sh
git worktree add --detach \
  ../beryllium-r8-alm1-plan-review \
  6bb3349b266a43d4572465379b5892b058e2fe39
```

## 8. Human decision checklist

- [ ] The exact target, parent, tree, plan blob, and 111-path boundary are
      understood.
- [ ] `R8-ALM1` is appropriately distinct from R8-B, accepted R8-C/H0, and
      K0-S.
- [ ] The proposed ten R8 paths, four current-position paths, generated
      planning prefix, frozen paths, and zero root/pin changes are complete
      and minimal.
- [ ] The fail-closed `safeRemove` / destination-absent `safeCopyTree`
      semantics and negative-test obligations are acceptable.
- [ ] The active-line maintenance environment and unavailable accepted-target
      environment are represented without evidence transfer.
- [ ] The future base/relation finding is resolved or is deliberately
      accepted as an open defect.
- [ ] The exact current-line pre-authentication failure and historical
      whole-diff failure are correctly distinguished or are deliberately
      accepted as an open defect.
- [ ] Claims match the available evidence and do not imply H0 readiness,
      H1-H4 authority, K3/hardware execution, K0-S progress, runtime behavior,
      proof, publication, or release.
- [ ] Important negative paths, two fresh runs, cross-run identity,
      accepted-target protection, and stop conditions are adequate.
- [ ] **Accept exact target:** explicitly accept
      `6bb3349b266a43d4572465379b5892b058e2fe39` as plan text only, despite the
      two open findings; do not authorize implementation.
- [ ] **Request revisions:** require a new exact plan commit correcting the
      base/relation and current-line failure boundary, followed by a new
      review packet.
- [ ] **Defer:** preserve the target as proposed/unaccepted and make no
      implementation or successor change.

## 9. After the decision

- **Accept:** the responsible human explicitly authorizes recording acceptance
  of exact SHA `6bb3349b266a43d4572465379b5892b058e2fe39` and date. Acceptance
  covers plan text only and does not cure either finding. Implementation must
  remain blocked until a coherent exact base/relation is separately reviewed
  and a later instruction explicitly authorizes implementation.
- **Request revisions:** create a new plan commit correcting both open
  findings and a new decision-neutral review packet. This target remains
  proposed and must not be silently treated as accepted.
- **Defer:** preserve the current status. Do not implement R8-ALM1, change
  accepted H0, start H1-H4 or hardware, alter K0-S, push, tag, publish, or
  release.

**Status:** exact R8-ALM1 plan target reviewed; two significant open findings;
revision recommended; no acceptance or implementation authority recorded.

**Next:** responsible-human accept, request-revisions, or defer decision on
exact target `6bb3349b266a43d4572465379b5892b058e2fe39`.

**Action required from you:** choose one decision explicitly. The recommended
choice is **request revisions**.
