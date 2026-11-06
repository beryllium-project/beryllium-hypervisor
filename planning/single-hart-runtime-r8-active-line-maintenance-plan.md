<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium R8 active-line maintenance plan revision R8-ALM1-A

## Status and authority

This document defines **R8 Active-Line Maintenance 1**, short identity
**R8-ALM1**. It is a separate maintenance plan for the private active line.
It is not an R8 K3 core-validation package, not an H0 successor, and not a
revision of the accepted
[`single-hart-runtime-r8-plan.md`](single-hart-runtime-r8-plan.md).

The `R8-B` / Plan revision R8-B label remains reserved and skipped because
repository history already assigns it to an unrelated object. R8-ALM1 does
not import that object's content, status, or authority.

On 2026-09-29, the responsible human selected maintenance decision-packet
**Option B: planning only**. That selection authorizes preparation of this
decision-neutral plan and nothing else.

Original exact plan target
`6bb3349b266a43d4572465379b5892b058e2fe39` (parent
`2b404ca31a07e1a0783a44183d0b2de95d053618`, tree
`730a77942be1079b1d1bb4e13ec1166cd30d4861`) remains immutable,
proposed, and unaccepted. Its decision-neutral
[review packet](single-hart-runtime-r8-active-line-maintenance-plan-review-summary.md)
is exact commit `255aa176923581bf9248bfce5bc94217ff5577a8`.
That packet recommends revisions for two significant findings:

1. a direct child of the original plan target cannot preserve the packet and
   a later acceptance record on the active line; and
2. exact current-line `r8-check` exits silently during launcher
   authentication, while only historical source `102f2b...` reaches the first
   whole-diff fixture.

The responsible human has instructed that those findings be corrected.
**Plan revision R8-ALM1-A** is the resulting narrow planning revision. It
retains the R8-ALM1 identity, remains proposed and not reviewed, and does not
record plan acceptance or implementation authorization.

```text
r8_active_line_maintenance_identity=R8-ALM1
r8_active_line_maintenance_plan_revision=R8-ALM1-A
r8_active_line_maintenance_plan=proposed-not-reviewed
r8_active_line_maintenance_implementation=not-authorized
r8_active_line_maintenance_implementation_base=pending-future-exact-acceptance-record-sha
r8_active_line_maintenance_candidate=none
r8_active_line_r8_check=blocked-preauth-launcher-exit-126
r8_historical_102f2_r8_check=blocked-first-whole-diff-exit-2
r8_h0_accepted_target=1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4
r8_h0_exit=not-met
r8_h1_h4=not-started-unauthorized
r8_k3_hardware=NOT-RUN
r8_publication=blocked
```

No source, checker, launcher, report, lock, acceptance pin, or implementation
change is authorized by this revision target. A later responsible-human
decision must first accept one exact R8-ALM1-A plan commit. A later
acceptance-record/current-line commit must preserve that target and its new
review packet. A separate implementation instruction must then name the full
exact acceptance-record/current-line SHA that becomes the implementation
base. A resulting implementation commit requires its own exact-target review
and decision.

The exact accepted non-privileged H0/R8-C target remains immutable:

```text
target=1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4
parent=d18b1c9c6ca8a0f2285f820ec960258620ae4b50
tree=7a9d80d08d0abb771d43cf76a4a297d9d668b375
status=accepted-BLOCKED-NOT-READY
```

R8-ALM1 neither changes nor re-accepts that target. It transfers no accepted
target evidence, readiness, count, environment, or authority to the active
line.

## Decision inputs

This plan is derived from the following decision-neutral artifacts, all dated
2026-09-29:

| Artifact | Identity | Role |
| --- | --- | --- |
| `r8-rejection-test-correction-decision-2026-09-29.md` | `fbf7a5d8ff82f14421cc2673104f29620b00a5c21b8eddf3ecebb4984fc69d92` | Two-run diagnosis, minimal correction semantics, and stopped four-path route |
| `r8-maintenance-revision-decision-2026-09-29.md` | `2f54637ba1706e5e6c932472880ee2fb329c7e1f58f739d4debd6364b0af62f2` | Option comparison and responsible-human selection surface |
| blocked maintenance metadata | `13340156ceb7920f88f22dfea70976d69cfe189d692e3589c3b961b31c939ed4` | Proof that the four-path direct-child route stopped before implementation |
| original R8-ALM1 review packet | commit `255aa176923581bf9248bfce5bc94217ff5577a8`, tree `58f4079092ed63137f6a960c7c2b9d9f3c25f2e3` | Immutable decision support recording the two revision-required findings |

The artifacts are session-local diagnosis and decision support. They are not
R8 evidence, maintained source inputs, accepted implementation, or
authorization.

The retained environment and diagnosis logs are under the ignored
`build/restore-pinned-validation-environment/` tree. They establish:

- two independent fresh volume-backed reproductions at historical source
  `102f2b0569396bf33ed2177ea5b7558cf5e6fbaa`;
- a deterministic first-fixture failure because the cloned repository already
  contains `tests/r8/`;
- a retained maintenance environment derived from the predecessor OCI archive;
  and
- the current inability to replay the accepted target in its exact recorded
  environment.

These logs remain local maintenance inputs, not accepted evidence.

## Review history and revision effect

The original target and packet remain exact historical decision support:

```text
original_plan_target=6bb3349b266a43d4572465379b5892b058e2fe39
original_plan_parent=2b404ca31a07e1a0783a44183d0b2de95d053618
original_plan_tree=730a77942be1079b1d1bb4e13ec1166cd30d4861
original_review_packet=255aa176923581bf9248bfce5bc94217ff5577a8
original_review_packet_tree=58f4079092ed63137f6a960c7c2b9d9f3c25f2e3
original_review_result=revision-recommended-no-decision-recorded
```

R8-ALM1-A supersedes the original target only as the current proposal for
future review. It does not rewrite the original target or packet and does not
infer that the responsible human accepted, rejected, or deferred either
commit. A new decision-neutral review packet is required for the exact
R8-ALM1-A target before any plan decision.

## Problem statement

The active private branch carries the historical, unaccepted H0 source package
introduced at:

```text
commit=102f2b0569396bf33ed2177ea5b7558cf5e6fbaa
parent=1f6109f0d0371eb3707e296c3416e8c55235683e
tree=67f54d3a34faa5669ea64b6e6be7a76b0e59816f
```

At the plan-preparation boundary, all 23 `tests/r8/` blobs remain identical
to that historical source. The active line has advanced through maintained
decision and documentation commits, so the historical H0 checker's
`1f6109f...` base-only/direct-child identity no longer describes the active
line.

The two failure boundaries are separate and must never be collapsed.

### Exact current-line entry failure

At packet commit `255aa176923581bf9248bfce5bc94217ff5577a8`:

- `tests/r8/**` remains byte-identical to historical source `102f2b...`;
- current `planning/single-hart-runtime-r8-plan.md` is the accepted R8-C blob,
  SHA-256
  `d7a0c4c3633cbd9e50b8f8989b140eaa4a848587e7b4a0ed0ea7fc920bc6e6e0`;
- `tests/r8/run-make.c` still authenticates the historical R8-A plan SHA-256
  `13f1b2482fdf21017a94c957be841477af452d68b4ce628ccd2fdc388b521b14`;
  and
- exact `./tests/r8/run-make.sh r8-check` exits `126` with zero stdout and
  zero stderr before GNU Make, source checking, report generation, or the
  whole-diff fixture.

The immediate active-line maintenance entry defect is therefore stale static
launcher/bootstrap and checker identity closure, not the copy destination.

### Historical whole-diff failure

The checked launcher can separately be restored for historical source
`102f2b...` and its exact tool locks. In two separate fresh volumes, that
historical `r8-check` passed bootstrap, Make control, tools, profile,
inventory, source, launcher, report generation, and report validation, then
failed before exercising the first whole-diff mutation:

```text
SafePathError: copy destination already exists:
.../candidate-whole-diff/tests/r8
```

The sequence is deterministic:

1. `test-rejections.mjs` clones the complete repository;
2. the clone already contains tracked `tests/r8/`;
3. clone modes are normalized;
4. `safeCopyTree(HERE, candidate/tests/r8)` is called; and
5. `safeCopyTree` correctly rejects the existing destination.

The previously selected four-path repair stopped correctly. A candidate that
was one child of `102f2b...` could not satisfy the unchanged
`check-sources.mjs` rule requiring one child of `1f6109f...`. Changing the
identity model, base, or path set exceeded that authorization.

## Objective

R8-ALM1-A retains one bounded maintenance objective with two required repair
layers:

1. restore exact active-line launcher/bootstrap/checker authentication from
   the stale R8-A-bound table to the reviewed R8-C/current-line maintenance
   boundary; and
2. after authentication reaches the rejection suite, preserve and correct the
   historical whole-diff overlay through bounded removal of cloned
   `tests/r8` immediately before the existing copy.

The combined objective is:

> Restore active-line `./tests/r8/run-make.sh r8-check` operability through a
> separately reviewed, explicitly non-claiming maintenance identity; prove
> both the current-line pre-authentication repair and the historical
> whole-diff regression; and preserve the historical H0 source meaning and
> immutable accepted `1999ee70...` target.

The maintenance result may establish only that the active-line host-only
checker and rejection package execute through their existing blocked/not-ready
H0 profile under the exact maintenance target. It must not become a new H0
profile, accepted H0 evidence, an H0 successor, or an H1 entry gate.

## Exact R8-ALM1-A plan-target boundary

The exact R8-ALM1-A plan target prepared under this task must be one clean,
non-merge, documentation-only child of:

```text
branch=beryllium/single-hart-runtime-r0
parent=255aa176923581bf9248bfce5bc94217ff5577a8
parent_tree=58f4079092ed63137f6a960c7c2b9d9f3c25f2e3
```

Its full target and tree identities are reported after the commit exists; the
plan cannot self-embed its own commit hash. The maintained source boundary is
exactly:

```text
100644 planning/single-hart-runtime-r8-active-line-maintenance-plan.md
100644 planning/README.md
100644 planning/HANDOFF.md
100644 planning/implementation-plan.md
100644 planning/roadmap.md
100644 planning/.vitepress/config.mts
100644 pathfinder/tests/check-docs-render.mjs
```

Generated planning derivatives are confined to:

```text
100644 docs/html/**
```

No symlink, executable, special file, non-`100644` generated file, or
generated path outside `docs/html/` belongs to the plan target. In particular,
this target changes no:

- `planning/single-hart-runtime-r8-plan.md`;
- `planning/single-hart-runtime-r8-h0-freeze.md`;
- `planning/single-hart-runtime-r8-active-line-maintenance-plan-review-summary.md`;
- `tests/r8/**`;
- root `Makefile`, `be`, or `scripts/check-be.sh`;
- `package.json` or `package-lock.json`;
- `pathfinder/Makefile`, Helium source, Helium documentation source, or
  `pathfinder/docs/html/**`;
- accepted R0-R7 mechanism, checker, proof, evidence, or acceptance-pin byte;
  or
- `pathfinder/publication-gate.conf`.

The original target `6bb3349...` and packet `255aa176...` remain immutable.
The generated planning filenames are derivative and may include
content-hashed assets. The exact target review must enumerate the resulting
Git path/mode set. The source authority is the seven maintained paths above.

## Future implementation base, parent, and relation

No exact implementation-base SHA exists at this planning revision. None may
be guessed or presented as exact.

The required future relation is:

```text
P = exact R8-ALM1-A plan target
Q = later decision-neutral review-packet commit for P
A = later current-line commit recording responsible-human acceptance of P
B = exact full SHA named by a separate implementation authorization
C = future maintenance implementation candidate
```

The default reviewed formula is:

1. `Q` and `A` preserve `P` in active-line first-parent ancestry and contain
   no R8 maintenance implementation byte;
2. `A` preserves both the new review packet and the plan acceptance record;
3. the separate implementation authorization quotes the full SHA of `A` and
   states `B=A`;
4. development mode starts only with clean `HEAD=B`; and
5. `C` is exactly one clean non-merge child of `B`, with no intermediate
   implementation commit.

The future acceptance-record/current-line SHA is intentionally unknown until
the responsible human accepts one exact R8-ALM1-A target and that decision is
recorded. The new review packet, the acceptance record, and the separate
implementation authorization are ordered gates, not placeholders that
automation may infer.

If the responsible human selects another current-line base or a side-branch
relation, that instruction must name the exact full SHA and the relation must
first be covered by another reviewed plan revision. An abbreviated hash,
current `HEAD`, remembered session value, original target `6bb3349...`, packet
`255aa176...`, accepted H0 target, historical source, or reconstructed tree is
not a substitute.

The future maintenance candidate must be:

1. on the private active `beryllium/single-hart-runtime-r0` line;
2. exactly one clean non-merge child of the exact separately authorized base
   `B`;
3. free of every intermediate commit;
4. limited to the exact implementation inventory below; and
5. reviewed as one exact target, parent, and tree.

If any unrelated active-line commit follows `A` before implementation, the
separate authorization must either name that exact later current-line commit
under an already reviewed formula or work must stop for a new exact base
decision and reviewed plan. Rebasing, merging, cherry-picking, dropping the
packet/acceptance history, or silently widening the checker is forbidden.

## Single non-claiming maintenance identity

The future checker and report must use one maintenance identity model:

```text
schema=be-r8-active-line-maintenance-v1
plan=R8-ALM1
plan_revision=R8-ALM1-A
relation=one-clean-non-merge-child-of-exact-authorized-acceptance-record-base
claim=active-line-r8-check-operability-only
```

The identity envelope must record:

- accepted R8-ALM1-A plan target;
- its decision-neutral review-packet commit;
- the exact acceptance-record/current-line implementation base named by the
  separate authorization;
- exact maintenance target, parent, and tree;
- development or committed-candidate state;
- exact changed path/mode inventory;
- historical H0 source anchor `102f2b...`, parent, and tree;
- immutable accepted H0 reference `1999ee70...`, parent, and tree;
- launcher SHA-256 and byte size;
- report SHA-256 and byte size;
- negative-case counts; and
- the pinned maintenance environment identity.

It must not call the maintenance target an H0 candidate or successor. The
historical active-line H0 profile remains the separate unaccepted 81-blocker
source package. The accepted target remains the separate accepted
80-blocker/118-`UNKNOWN` package. Their counts, profile bytes, source
projections, and status fields must not be combined.

Development mode requires `HEAD` at the exact separately authorized base `B`,
the normal index byte-identical to `HEAD`, and only enumerated worktree
changes. Committed mode requires a clean worktree/index and `HEAD` exactly one
child of `B`. Both modes must derive the same prospective/committed tree and
the same maintenance projection without mutating the normal index.

The checker must continue to authenticate:

- original accepted R8 plan `7d0f0cbf...`;
- accepted R8-A `8fa9d672...`;
- accepted R8-C `f47ae602...` and the current
  `planning/single-hart-runtime-r8-plan.md` bytes;
- the exact accepted R8-ALM1-A plan target and plan bytes;
- the exact new review packet and acceptance-record/current-line base named by
  the separate authorization;
- historical H0 source `102f2b...`; and
- accepted target `1999ee70...` as an inspection-only immutable reference.

No maintenance output may imply that one target's validation or decision
applies to another.

## Correction semantics

The future behavior change is bounded to the whole-diff candidate staging
sequence in `tests/r8/test-rejections.mjs`:

```js
normalizeCloneModes(repository)
safeRemove(resolve(repository, 'tests/r8'))
safeCopyTree(HERE, resolve(repository, 'tests/r8'))
```

The removal is required because the complete clone necessarily contains the
tracked package. It occurs only after mode normalization and immediately
before the existing overlay.

`tests/r8/safe-paths.mjs` remains byte unchanged. The correction relies on its
existing fail-closed properties:

- every path remains lexically and physically confined below `build/r8`;
- every parent is an effective-uid-owned, non-symlink, exact-mode `0700`
  directory;
- regular files are effective-uid-owned, single-link, and in the exact
  removal-mode allowlist;
- a symlink is removed as an owned link and is never followed;
- special objects are rejected;
- directory identity, ownership, mode, and physical stability are rechecked
  during bounded entry-by-entry unlink/rmdir traversal;
- hostile cleanup fails rather than widening deletion; and
- sentinels outside the exact removal target remain unchanged.

After successful removal, `safeCopyTree` must still require the destination to
be absent. The shared primitive must not gain overwrite, merge, replace, or
best-effort behavior. An incomplete removal, racing recreation, wrong owner,
wrong mode, symlinked parent, special object, or unexpected identity remains a
hard failure.

The overlay must not be deleted from the test. Copying files individually is
also forbidden because stale or extra package paths could survive.

## Exact future implementation inventory

The complete implementation and lock closure is:

| Mode | Path | Authorized change |
| --- | --- | --- |
| `100644` | `tests/r8/Makefile` | Keep the target graph unchanged; make PASS text explicitly identify both authenticated active-line entry repair and non-claiming historical regression maintenance rather than a new H0 result |
| `100644` | `tests/r8/README.md` | Document R8-ALM1-A identity, the current exit-126 and historical exit-2 controls, accepted-target separation, environment, commands, and non-claims |
| `100644` | `tests/r8/check-report.mjs` | Independently reconstruct and reject drift in the acceptance-record-based maintenance identity, dual failure attribution, and report envelope |
| `100644` | `tests/r8/check-sources.mjs` | Implement the future exact acceptance-record base / one-child identity, current R8-C plan authentication, historical-source attribution, and exact path/mode enforcement |
| `100644` | `tests/r8/generate-report.mjs` | Emit the non-claiming maintenance envelope while retaining the current launcher repair and historical H0 blocked profile as separately attributed facts |
| `100644` | `tests/r8/h0-ast-contract-v1.json` | Re-derive exact AST contracts only for changed maintained Node modules |
| `100644` | `tests/r8/h0-source-boundary-v2.json` | Add the exact R8-ALM1-A plan/review/acceptance-base/path/bootstrap contract without changing H0 profile authority |
| `100644` | `tests/r8/run-make.c` | Re-derive the static bootstrap table and entry count so current R8-C and accepted R8-ALM1-A inputs authenticate before dynamic execution |
| `100755` | `tests/r8/run-make.sh` | Deterministically rebuild the checked-in static launcher from `run-make.c` |
| `100644` | `tests/r8/test-rejections.mjs` | Add bounded removal, acceptance-base/relation negatives, current stale-launcher control, historical whole-diff control, destination-absence regression, and disposable correction-removal regression |
| `100644` | `planning/README.md` | Record accepted-plan/authorized-candidate status only if supplied by the future responsible-human decisions |
| `100644` | `planning/HANDOFF.md` | Record the exact maintenance target, validation, repository state, and Project Manager return |
| `100644` | `planning/implementation-plan.md` | Keep the maintenance target separate from the R8 H0-H4 program and every hardware/runtime gate |
| `100644` | `planning/roadmap.md` | Record current operability status and exact non-claiming boundary |
| `100644` | `docs/html/**` | Regenerate planning derivatives only; every tracked output remains a regular mode-`100644` file |

The R8-ALM1-A plan source itself is immutable after exact plan review. The
plan target already supplies its VitePress navigation and browser title inventory,
so future implementation must leave these paths byte unchanged:

```text
100644 planning/single-hart-runtime-r8-active-line-maintenance-plan.md
100644 planning/.vitepress/config.mts
100644 pathfinder/tests/check-docs-render.mjs
```

The following files must remain byte and mode identical to the exact
implementation base:

```text
planning/single-hart-runtime-r8-plan.md
planning/single-hart-runtime-r8-h0-freeze.md
tests/r8/check-inventory.mjs
tests/r8/check-launcher.mjs
tests/r8/check-profile.mjs
tests/r8/check-tools.sh
tests/r8/git-tools.mjs
tests/r8/h0-claim-contract-v1.json
tests/r8/h0-profile-v2.json
tests/r8/h0-row-contract-v2.json
tests/r8/make-control.mjs
tests/r8/r0-r7-immutable-manifest-v1.json
tests/r8/safe-paths.mjs
tests/r8/third_party/acorn/LICENSE
tests/r8/third_party/acorn/acorn.mjs
```

There are **zero** authorized predecessor acceptance-pin refreshes. No root
integration or R0-R7 acceptance checker changes are needed. Discovery of an
eleventh R8 implementation/lock path, a fifth current-position path, a
navigation/browser change, a root file, a dependency, a predecessor pin, or
another generated prefix is a stop requiring a reviewed plan change.

The two packet findings were re-evaluated against this closure. Repairing the
current pre-authentication boundary changes the contents and pins already
assigned to `run-make.c`, `run-make.sh`, `h0-source-boundary-v2.json`, and
`check-sources.mjs`; correcting the historical whole-diff fixture remains
inside `test-rejections.mjs`. The acceptance-record base formula and report
attribution remain inside the already enumerated checker/report/AST files.
No eleventh R8 path, fifth current-position path, predecessor acceptance pin,
root path, dependency, or additional generated prefix is required.

## Environment boundary

### Active-line maintenance environment

The historical package was reproduced in a retained open environment:

```text
base_oci_archive_sha256=6aac298509662161ff43063b8b14d848c0cf6d517aba6dfca28e0b3d40682a06
base_image_id=151db305d34985eb57a08f7d2564fc5845694618c9baeb19636ede8d9f4ef39d
base_manifest=sha256:dbf1bc988918e2a3d5ce4ca098f2f07087285a80405dcfbeea0c37d6a9707bbe
derived_image_id=84e69a02784cf0862ee04163df83172727f7161557e478cbcfdd121e5c5bc58a
derived_image_digest=sha256:c4a0447a2374ebcac78f7c164ef9c3c40cdd6589a4c359d74c0e7c2bbfdbc5da
```

The exact active-line locks include GCC 16.1.1, Node.js 22.22.2, and
coreutils 9.10 with the checked hashes recorded in
`build/restore-pinned-validation-environment/`. The derived image adds only
the hashed Fedora 44 `glibc-static` and `libxcrypt-static` RPMs required for
the static launcher rebuild.

Before future implementation validation, the derived image must be exported
to an OCI archive, independently hashed, and retained with its build recipe,
RPM bytes, package/license metadata, image/config identity, and tool probes.
A mutable local tag or Podman store entry alone is insufficient retained
evidence.

Every normative candidate run uses:

- network disabled;
- uid/gid `1000:1000`;
- all capabilities dropped;
- `no-new-privileges=1`;
- explicit `crun`;
- container-only SELinux label disabling;
- a fresh source volume and a distinct fresh build volume; and
- the checked static launcher, never raw Make.

### Missing accepted-target environment

Fresh executable replay of accepted target `1999ee70...` is currently
blocked. The exact selected accepted-target OCI archive
`fcf6c595140a9dd55d6afb633ac7777162492cdae6b77cd27a59e4541c1bd1f5`
is absent, and the accepted target's required 27,944-byte
`/usr/bin/node-22` SHA-256
`1a1ebcd93dc90cf3e3dc37493e8efc04a1f60bddada1402453094214af03e33d`
is unavailable in the searched host, retained OCI, and RPM inputs.

The current host Node and retained predecessor Node hashes are different.
Neither may be substituted. The predecessor archive also does not reproduce
the accepted-target image byte-for-byte.

Therefore the maintenance gate requires unchanged accepted-target **Git
inspection**, not fresh accepted-target execution. If the exact accepted
environment is later recovered, replay is a separate accepted-target
maintenance activity and its results do not transfer to R8-ALM1.

## Future validation plan

### Candidate identity and inventory

Before execution:

1. verify the accepted R8-ALM1-A plan target, its later review packet, the
   exact acceptance-record/current-line implementation base named by the
   separate authorization, future target, sole parent, tree, subject, branch,
   and clean state;
2. require the exact 14 maintained implementation/current-position paths
   above and no other maintained path;
3. require `run-make.sh` mode `100755`; every other maintained path mode
   `100644`; and every generated planning path regular mode `100644`;
4. verify zero merge parents, replacement refs, staged state, index flags,
   hidden worktree changes, submodules, symlinks, and special objects; and
5. verify every frozen path and all R0-R7 accepted inputs remain byte/mode
   unchanged.

### Required pre-implementation failure controls

The validation record must preserve two independent controls before treating a
candidate PASS as meaningful.

#### Current-line launcher-authentication control

From a fresh clean checkout of the exact future implementation base `B`, before
any implementation byte changes:

```sh
./tests/r8/run-make.sh r8-check
```

must reproduce the active-line boundary:

```text
exit=126
stdout_bytes=0
stderr_bytes=0
failure_phase=static-launcher-authentication-before-GNU-Make
current_plan=r8c
launcher_plan_lock=r8a
```

The stdout and stderr SHA-256 values must both equal the empty-file SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
Any output or later failure phase means the control differs and is a stop.

#### Historical whole-diff control

From a separate fresh checkout of exact historical source
`102f2b0569396bf33ed2177ea5b7558cf5e6fbaa` in the retained historical
maintenance environment, `r8-check` must separately reproduce:

```text
exit=2
failure_phase=first-whole-diff-fixture
failure=SafePathError-copy-destination-already-exists
```

That control must first pass historical bootstrap, Make control, tools,
profile, inventory, source, launcher, report generation, and report checking.
It does not describe current active-line entry behavior.

If the historical environment cannot be reconstructed from the retained
archive, RPMs, recipe, and tool locks, the historical control is `NOT RUN` and
candidate validation is blocked. The two retained 2026-09-29 diagnostic runs
remain supporting history, not a substitute for a required future control.

### Two independent fresh worktree/volume runs

Use two separate fresh detached checkouts of the same exact candidate and two
distinct fresh source/build volumes. In each, run:

```sh
/usr/bin/env -i PATH=/usr/bin SHELL=/bin/bash HOME=/ \
  ./tests/r8/run-make.sh r8-rejection-test
/usr/bin/env -i PATH=/usr/bin SHELL=/bin/bash HOME=/ \
  ./tests/r8/run-make.sh r8-check
```

Each run must:

- authenticate current R8-C plan bytes, exact accepted R8-ALM1-A plan bytes,
  the authorized acceptance-record base, the exact bootstrap entry set, and
  six tool entries;
- produce two byte-identical static launcher rebuilds;
- prove the stale-launcher exit-126 control no longer occurs;
- reach and pass the whole-diff baseline;
- reject the whole-diff untracked-path mutation;
- complete at least the existing 111 negative cases, with no existing
  category count reduced;
- pass every added maintenance/base/relation/correction regression;
- retain the historical 147-row/81-H0-blocker active-line profile attribution;
  and
- leave the candidate checkout clean after removal of generated scratch.

### Required correction regressions

The exact future rejection suite must additionally prove:

1. an unrelated pre-existing `safeCopyTree` destination still raises
   `SafePathError`;
2. bounded removal does not follow symlinks or alter an external sentinel;
3. wrong owner, wrong mode, special object, hostile cleanup, incomplete
   removal, and recreated destination remain rejecting;
4. `safe-paths.mjs` is byte unchanged;
5. the overlay stages the exact current candidate package rather than stale
   cloned bytes; and
6. in a disposable uncommitted validation copy, deleting the one bounded
   `safeRemove` call reproduces the historical first whole-diff fixture
   failure only after the updated launcher/bootstrap identity passes.

A separate disposable launcher-table regression must restore the stale R8-A
plan entry while leaving current R8-C plan bytes in place and reproduce silent
exit `126` before GNU Make. That regression proves the current entry repair is
independently load-bearing rather than accidentally masked by the whole-diff
correction.

The disposable regression must not rewrite the candidate, generate a second
candidate commit, or retain mutated source as evidence.

### Cross-run identity

The two successful runs must agree exactly on:

- candidate target, parent, and tree;
- R8-ALM1-A plan target, review packet, authorized acceptance-record base,
  and identity schema;
- changed path/mode inventory;
- launcher byte size and SHA-256;
- deterministic report byte size and SHA-256;
- maintenance projection path count and SHA-256;
- historical H0 source anchor and blocker attribution;
- negative-case total and category counts;
- bootstrap/tool identities; and
- clean post-run repository state.

Raw timing, scratch names, volume names, and host-local paths are excluded
from semantic comparison.

### Active-line and repository gates

At the exact candidate, run the existing checked interfaces without changing
their accepted boundaries:

```sh
./be r0-check
./be r0-freeze
./be r1-check
./be r2-check
./be r3-check
./be r4-check
./be r5-check
./be r6-check
./be r7-check
./be docs-check
make check
```

At least one fresh candidate environment must run the complete list. The
second must independently repeat `r8-check`, the R0-R7 checked gates, and
`make check`; a cached transcript or reused build volume is not a substitute.
Any retained tool-lock mismatch is a blocked validation result, not permission
to refresh an unenumerated lock.

The candidate must also prove active-line integration:

- active branch is `beryllium/single-hart-runtime-r0`;
- candidate is exactly one child of the full exact
  acceptance-record/current-line base named by the separate implementation
  authorization;
- the accepted R8-ALM1-A plan target, its review packet, and its acceptance
  record remain in active-line ancestry;
- no accepted H0 target, packet, or record was merged or cherry-picked;
- root `Makefile`, `be`, and `scripts/check-be.sh` are unchanged;
- no predecessor acceptance pin changed; and
- the target remains local and private until a separate push decision.

### Unchanged accepted-target inspection

From a separate clean detached worktree or direct Git object reads:

1. verify accepted target `1999ee70...`, parent `d18b1c9...`, and tree
   `7a9d80d0...`;
2. verify the accepted target still contains the bounded removal immediately
   before the package overlay;
3. verify no R8-ALM1 path, commit, report, or status was written into that
   target;
4. verify its review/acceptance record still attributes 147 rows,
   118 `UNKNOWN`, 80 H0 blockers, `BLOCKED-NOT-READY`, and
   `r8_h0_exit=not-met`; and
5. record accepted-target executable validation as `NOT RUN` while the exact
   Node/OCI environment remains unavailable.

## Claims, non-claims, and stops

### Supportable maintenance claim

After a separately authorized exact implementation target passes every gate,
the strongest supportable statement is:

> On the private active line and in two independent fresh pinned maintenance
> environments, an exact current-line R8-ALM1 maintenance target authenticates
> the reviewed R8-C/current-line bootstrap and checker closure, completes its
> checked `r8-check` path, and passes at least 111 fail-closed negative cases.
> A separate historical control reproduces the original first whole-diff
> destination failure, and the maintained correction removes only the cloned
> `tests/r8` tree before overlay. The result is an active-line
> tooling-maintenance result only.

Required limit:

> The maintenance target is not accepted H0 evidence, does not change or
> validate accepted target `1999ee70...`, does not establish H0 readiness,
> and supplies no K3, runtime, hardware, proof, or successor result.

### Explicit non-claims

R8-ALM1 does not establish or authorize:

- H0 readiness, exit, successor status, evidence transfer, or new H0 facts;
- H1, H2, H3, or H4 work;
- K3/COM260 execution or hardware evidence;
- any Beryllium runtime semantic, C, assembly, linker, image, CSR, QEMU,
  guest, device, DMA, Linux, service, multicore, policy, or proof change;
- root integration, dependency changes, or predecessor acceptance-pin
  refreshes;
- accepted-target environment reconstruction;
- formal verification, C refinement, whole-system proof, certification, or
  production readiness;
- push, tag, public or private backup, publication, release, migration,
  archival, or publication-gate approval.

### Mandatory stops

Stop before implementation or validation completion if:

- the exact plan target is not accepted or implementation is not separately
  authorized;
- the R8-ALM1-A target, new review packet, later acceptance record, active
  branch, exact separately authorized implementation base, or one-child
  relation differs;
- an unknown or inferred SHA is presented as the implementation base;
- the original plan target or packet is used as an implementation base without
  another explicit reviewed relation;
- any unenumerated path or mode is required;
- `safe-paths.mjs`, H0 freeze/profile/row/claim contracts, accepted R8 plan,
  accepted target, root build/check tooling, dependency, publication gate, or
  R0-R7 accepted input would change;
- an acceptance pin appears necessary;
- the shared copy primitive would overwrite or merge an existing destination;
- an existing negative category decreases below its historical count;
- the exact current-line base does not reproduce silent pre-authentication
  exit `126`, or the exact historical control does not separately reproduce
  the first whole-diff exit `2`;
- the two fresh runs disagree on a required canonical identity;
- a candidate run requires the missing accepted-target Node/OCI bytes or
  silently substitutes another tool;
- planning or Helium generated-state restoration cannot be proven exact; or
- any result would need to be described as H0 readiness, H1 authority,
  hardware evidence, or runtime semantics.

## Decision gates after this plan

The gates remain separate:

1. **Revision review:** prepare a new decision-neutral packet for one exact
   R8-ALM1-A target, then accept, request revision, or defer that exact target.
   Acceptance covers plan text only.
2. **Acceptance record:** if the plan is accepted, record that supplied
   decision in a later documentation-only current-line commit that preserves
   both the revised target and new packet. The exact commit is unknown now.
3. **Implementation authorization:** separately quote the full exact
   acceptance-record/current-line SHA and authorize exactly one direct-child
   implementation under the 14-path inventory. Plan acceptance or the
   acceptance record alone is not implementation authority.
4. **Exact implementation review:** after implementation and validation,
   review one exact maintenance target, parent, tree, complete inventory,
   environment, logs, hashes, non-claims, and repository state.
5. **Implementation decision:** accept, request revision, or defer that exact
   target. A passing check cannot accept itself.

No gate authorizes H1-H4, K3 execution, a COM260-informed H0 successor, push,
tag, publication, release, or migration.

## Primary references

- [R8 K3 core-validation plan](single-hart-runtime-r8-plan.md)
- [R8 plan review and acceptance record](single-hart-runtime-r8-plan-review-summary.md)
- [R8-A review and acceptance record](single-hart-runtime-r8-plan-r8a-review-summary.md)
- [R8-C review and acceptance record](single-hart-runtime-r8-plan-r8c-review-summary.md)
- [R8-H0/R8-C review and acceptance record](single-hart-runtime-r8-h0-review-summary.md)
- [Original R8-ALM1 review packet](single-hart-runtime-r8-active-line-maintenance-plan-review-summary.md)
- [Historical active-line H0 freeze source](single-hart-runtime-r8-h0-freeze.md)
- [Beryllium roadmap](roadmap.md)
- [Open tooling policy](open-tooling.md)
- repository-root `LLM_POLICY_ALIGNMENT.md`
