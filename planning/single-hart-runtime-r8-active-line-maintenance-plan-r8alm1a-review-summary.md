<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium R8 active-line maintenance plan revision R8-ALM1-A review and acceptance record

This document began as the decision-neutral responsible-human review packet
for exact R8-ALM1-A plan target
`95cce2f692543da67054ec2d6061eb08a4061253`, whose immediate parent is the
first review-packet commit
`255aa176923581bf9248bfce5bc94217ff5577a8` and whose Git tree is
`f826204b12701114993743f949c6ee71a72def5c`. It now also records the
responsible-human decision on that exact target. The target remains byte
unchanged. Its authoritative plan is
[`single-hart-runtime-r8-active-line-maintenance-plan.md`](single-hart-runtime-r8-active-line-maintenance-plan.md).
Its retained target-content status is `proposed-not-reviewed`.

Packet commit `788b0b6752b706ece8dc51dc2c0c5dca3e56376f` is the direct
child of the target and remains decision support. Neither that packet nor
this documentation-only acceptance-record follow-up is the accepted plan
target, implementation authority, an implementation base, or implementation
evidence.

The packet superseded the
[first R8-ALM1 review packet](single-hart-runtime-r8-active-line-maintenance-plan-review-summary.md)
for consideration of the revised target. Original plan target
`6bb3349b266a43d4572465379b5892b058e2fe39` and first packet
`255aa176923581bf9248bfce5bc94217ff5577a8` remain immutable superseded
decision support. They are not rewritten, accepted, or converted into
implementation authority by the later decision.

Independent review finds that R8-ALM1-A resolves both significant findings
from the first packet. No significant open plan defect was found. The
responsible human subsequently accepted exact target
`95cce2f692543da67054ec2d6061eb08a4061253` as plan text only. Plan
acceptance authorizes no implementation.

Except where a statement is explicitly marked current or post-decision,
sections 1 through 8 retain the review history and evidence boundary on which
the decision rests.

## Decision record

The responsible human accepted exact R8-ALM1-A plan target
`95cce2f692543da67054ec2d6061eb08a4061253` as planning text only on
September 29, 2026, by the exact instruction:

```text
accept
```

The immutable target's
`r8_active_line_maintenance_plan=proposed-not-reviewed` and
`r8_active_line_maintenance_implementation=not-authorized` fields remain
frozen pre-decision content. Current acceptance is carried by this later
review and acceptance record, not by rewriting those bytes.

Acceptance selects no implementation base, relation, candidate, checker
change, or implementation inventory. Any future implementation requires a
separate exact responsible-human instruction that names the full SHA of the
later plan acceptance-record/current-line base, states the exact target-to-
candidate relation, and names the complete plan-governed implementation
inventory. No abbreviated SHA, branch tip, remembered value, target, packet,
or inferred current `HEAD` may substitute for that instruction.

Current decision status is:

```text
r8_active_line_maintenance_identity=R8-ALM1
r8_active_line_maintenance_plan_revision=R8-ALM1-A
r8_active_line_maintenance_plan_target=95cce2f692543da67054ec2d6061eb08a4061253
r8_active_line_maintenance_plan_parent=255aa176923581bf9248bfce5bc94217ff5577a8
r8_active_line_maintenance_plan_tree=f826204b12701114993743f949c6ee71a72def5c
r8_active_line_maintenance_plan_target_status=accepted-plan-text-only
r8_active_line_maintenance_acceptance_date=2026-09-29
r8_active_line_maintenance_acceptance_instruction=accept
r8_active_line_maintenance_packet=788b0b6752b706ece8dc51dc2c0c5dca3e56376f
r8_active_line_maintenance_target_frozen_status=proposed-not-reviewed
r8_active_line_maintenance_implementation=not-authorized
r8_active_line_maintenance_implementation_base=pending-separate-full-sha-instruction
r8_active_line_maintenance_implementation_relation=pending-separate-exact-relation
r8_active_line_maintenance_implementation_inventory=pending-complete-plan-inventory
r8_h0_accepted_target=1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4
r8_h0_readiness=BLOCKED-NOT-READY
r8_h0_exit=not-met
r8_h1_h4=not-started-unauthorized
r8_k3_hardware=NOT-RUN
r8_publication=blocked
```

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `95cce2f692543da67054ec2d6061eb08a4061253` (`docs: revise R8 active-line maintenance plan`), parent `255aa176923581bf9248bfce5bc94217ff5577a8`, tree `f826204b12701114993743f949c6ee71a72def5c` |
| Plan identity | `R8-ALM1`, Plan revision `R8-ALM1-A`; plan blob `65939288f6abd108657504bd578b06417e668513`; SHA-256 `b52d3579103752e2f74f926a2d7489aea38660964c881e9bb5752a394c6474ee`; 37,347 bytes / 838 lines |
| Review history | Original plan target `6bb3349b266a43d4572465379b5892b058e2fe39`; first decision-neutral packet `255aa176923581bf9248bfce5bc94217ff5577a8`; both remain immutable and unaccepted |
| Branch and repository | `beryllium/single-hart-runtime-r0`; private repository `beryllium-project/beryllium-hypervisor`; target was the clean branch HEAD and three local commits ahead of its private upstream at review start |
| Packet | Exact commit `788b0b6752b706ece8dc51dc2c0c5dca3e56376f`, direct child of the target; decision support only |
| Current status | Exact target `95cce2f692543da67054ec2d6061eb08a4061253` is responsible-human accepted as plan text only as of 2026-09-29. Its immutable `proposed-not-reviewed` field remains frozen pre-decision content; implementation remains `not-authorized` |
| Packet review verdict (historical) | **Accept plan text only recommended.** Both first-packet findings are resolved, the future path/mode and identity closure is finite, and no significant new plan defect was found |
| Decision | Accepted as plan text only by exact instruction `accept` on 2026-09-29 |
| Successor status | No R8-ALM1 implementation exists or is authorized. R8-H1 through R8-H4, a COM260-informed H0 successor, K3 execution, and hardware validation remain blocked or `NOT RUN` |
| Publication status | Target, packet, and this acceptance-record follow-up are private and local. No push, tag, publication, release, migration, archive, or `pathfinder/publication-gate.conf` change is authorized |

**Action taken:** the responsible human accepted exact target
`95cce2f692543da67054ec2d6061eb08a4061253` as plan text only. No
implementation authority, base, relation, candidate, changed checker, root
integration, dependency, pin, runtime, proof, hardware, successor, or
publication action follows.

## 2. Deliverables and exact target inventory

With rename detection disabled, the target changes **114 paths**:

- seven maintained paths, all regular mode `100644`; and
- 107 generated planning-site paths under `docs/html/**`, with every present
  generated path regular mode `100644`.

With Git's default rename detection, the same delta is reported as 104 changed
entries. The no-renames inventory is the complete path-level review boundary.

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
| Revised R8-ALM1 plan | `planning/single-hart-runtime-r8-active-line-maintenance-plan.md` | Corrects only the future base/relation and dual-failure validation model while retaining the separate, non-claiming maintenance identity and all original stops. It changes no checker or implementation byte | Does the `P/Q/A/B/C` relation preserve plan, review, and acceptance history while requiring a separately authorized full exact implementation-base SHA? |
| Current-position integration | `planning/README.md`, `planning/HANDOFF.md`, `planning/implementation-plan.md`, `planning/roadmap.md` | Records the proposed revision and the two corrected findings without changing accepted R8/R8-A/R8-C/H0, K0-S, H1-H4, hardware, or publication status | Do these pages distinguish original review history, revised proposal, current exit `126`, historical exit `2`, and the absence of implementation authority? |
| Navigation and browser inventory | `planning/.vitepress/config.mts`, `pathfinder/tests/check-docs-render.mjs` | Keeps the maintained plan reviewable through the planning site. The shared renderer change is planning-page inventory only and changes no Helium page, claim, or component behavior | Is the route/title update limited to the revised planning page and decision-neutral status? |
| Generated planning site | `docs/html/**` | Reviewable derivative of maintained Markdown and navigation | Does the rendered planning site correspond functionally while retaining the known generated-byte reproducibility finding? |

The target changes no:

- accepted R8 plan, R8-A, R8-C, or H0 target byte;
- `planning/single-hart-runtime-r8-plan.md` or
  `planning/single-hart-runtime-r8-h0-freeze.md`;
- first review packet
  `planning/single-hart-runtime-r8-active-line-maintenance-plan-review-summary.md`;
- file under `tests/r8/**`;
- root `Makefile`, `be`, or `scripts/check-be.sh`;
- dependency manifest or lock;
- accepted R0-R7 mechanism, proof, checker, evidence input, or acceptance pin;
- KVM0/K0-S source, route, package, readiness, execution, or result record;
- Helium source, Helium documentation source, or Helium generated path; or
- publication configuration.

## 3. Claim boundary

### What the exact target supports saying

- `R8-ALM1` remains a separate active-line tooling-maintenance identity.
  `R8-ALM1-A` is its plan-revision label. Neither is R8-B, an H0 successor,
  or a revision of the accepted R8 K3 core-validation plan.
- Original target `6bb3349...` and first packet `255aa176...` remain immutable
  history. R8-ALM1-A is the current proposal for review.
- The future implementation base is intentionally unknown now. After one
  exact R8-ALM1-A target is accepted and that decision is recorded, a
  separate implementation instruction must name one full exact
  acceptance-record/current-line SHA `B`. The implementation candidate `C`
  must be exactly one clean non-merge child of `B`.
- The default relation preserves the exact revised plan `P`, new review packet
  `Q`, and later acceptance record `A` in active-line first-parent ancestry.
  An abbreviated hash, current `HEAD`, remembered session value, original
  target, first packet, accepted H0 target, historical source, or reconstructed
  tree is not an exact implementation base.
- Exact current-line `r8-check` is blocked before GNU Make by stale launcher
  authentication: the active line carries R8-C plan SHA-256
  `d7a0c4c3633cbd9e50b8f8989b140eaa4a848587e7b4a0ed0ea7fc920bc6e6e0`,
  while `tests/r8/run-make.c` pins historical R8-A plan SHA-256
  `13f1b2482fdf21017a94c957be841477af452d68b4ce628ccd2fdc388b521b14`.
  The exact checked launcher exits `126` with empty stdout and stderr.
- Historical source `102f2b0569396bf33ed2177ea5b7558cf5e6fbaa`
  separately reaches the first whole-diff fixture and exits `2` because
  `safeCopyTree` rejects the already present cloned `tests/r8` destination.
  That historical result does not describe current active-line entry behavior.
- Future validation must preserve both controls independently before treating
  a candidate PASS as meaningful. If the historical environment cannot be
  reconstructed, the historical control is `NOT RUN` and validation is
  blocked rather than inferred.
- The complete future changed surface is ten R8 behavior/lock paths, four
  current-position paths, and generated planning derivatives only. The one
  executable maintained path is `tests/r8/run-make.sh` at mode `100755`; all
  other maintained paths are mode `100644`.
- There are zero root changes, dependency changes, predecessor
  acceptance-pin refreshes, or future navigation/browser changes in the
  implementation candidate.
- The correction keeps `tests/r8/safe-paths.mjs` byte unchanged, removes only
  the cloned `tests/r8` tree after clone-mode normalization, and preserves
  `safeCopyTree`'s destination-absence requirement.

### Trusted or assumed

- Git commit, parent, tree, blob, path, mode, index, first-parent ancestry, and
  replacement-ref behavior are trustworthy within the stated checks.
- The static launcher, Node.js, GCC, coreutils, Fedora OCI inputs, Podman/crun
  isolation, VitePress, Chromium, and ordinary host filesystem semantics
  behave as observed at their recorded identities.
- The current `safe-paths.mjs` confinement, ownership, exact-mode, link-count,
  symlink, identity-revalidation, and bounded cleanup checks are correct.
- The accepted R0-R8 and K0-S records mean exactly what their existing review
  and acceptance records state.
- A future separately authorized implementation can update the already
  enumerated checker/report/bootstrap paths without requiring an unenumerated
  lock, root, dependency, or acceptance-pin change.

### Evidence unavailable or `NOT RUN`

- No R8-ALM1 implementation target, report, launcher rebuild, maintenance
  projection, candidate result, or implementation review exists.
- Fresh executable replay of accepted target `1999ee70...` remains unavailable
  because its exact selected OCI archive and exact `/usr/bin/node-22` bytes
  are absent. Accepted-target executable validation remains `NOT RUN`; Git
  object inspection is not a substitute.
- R8-H1 through R8-H4 have not started.
- K3 execution and all Beryllium hardware validation remain `NOT RUN`.
- Generated planning bytes remain non-reproducible in the current
  documentation environment even though build, link, direct-file, browser,
  and responsive/mobile gates pass.

### What the target does not implement, prove, or authorize

- No plan acceptance or implementation authorization.
- No H0 acceptance, readiness, successor status, evidence transfer, new H0
  fact, or change to accepted target `1999ee70...`.
- No privileged Beryllium C, assembly, linker, image, CSR, QEMU, guest,
  device, DMA, Linux, service, multicore, policy, proof, or hardware behavior.
- No accepted-target environment reconstruction or accepted-target rerun.
- No KVM0/K0-S route, source, package, readiness, import, execution, result,
  BSP, or hardware change.
- No root integration, dependency change, predecessor-pin refresh, push, tag,
  publication, release, migration, archive, or publication-gate approval.

## 4. Security and correctness invariants

| Invariant | Contract or implementation point | Review result |
| --- | --- | --- |
| Revised plan and first packet remain immutable history | R8-ALM1-A `Review history and revision effect`; exact target ancestry | **PASS.** Target is one documentation-only child of first packet `255aa176...`; original target and packet remain byte unchanged |
| Future implementation base is exact and history-preserving | `Future implementation base, parent, and relation`; accepted R8-A precedent | **PASS.** `P/Q/A/B/C` is coherent, default `B=A` is named only by later separate authorization, and no unknown SHA is presented as exact |
| Current and historical failures remain distinct | `Problem statement`; `Required pre-implementation failure controls` | **PASS.** Current line requires silent pre-Make exit `126`; historical `102f2b...` separately requires first whole-diff exit `2`; neither result substitutes for the other |
| Maintenance identity is non-claiming | `Single non-claiming maintenance identity`; report-envelope obligations | **PASS.** The only future positive claim is active-line `r8-check` operability; historical 81-blocker and accepted 80-blocker states remain separately attributed |
| R8-B collision is not reused | Status section; accepted R8-C history | **PASS.** Repository history assigns R8-B to exact non-ancestor object `c6e0da62f99a5bf0cb3435f7495129962a3be21b`; R8-ALM1/R8-ALM1-A imports no status or semantics from it |
| Future path and mode authority is finite | Exact ten-path R8 table, four current-position paths, generated prefix, frozen-path and stop lists | **PASS.** No eleventh R8 path, fifth current-position path, root path, dependency, predecessor pin, or additional generated prefix is required |
| Copy correction stays fail closed | Planned `normalizeCloneModes` / `safeRemove` / `safeCopyTree` sequence; unchanged `safe-paths.mjs` | **PASS as a plan obligation.** Removal is bounded to cloned `tests/r8`; shared copy still rejects an existing destination; overwrite, merge, replace, best-effort cleanup, and stale overlay are forbidden |
| Environment evidence does not transfer | Active-line maintenance environment and missing accepted-target environment sections | **PASS.** Retained historical inputs are maintenance support only; accepted-target Node/OCI absence remains explicit; substitution is forbidden |
| Negative and cross-run validation remains load-bearing | Two fresh runs, launcher-table and correction-removal regressions, cross-run identity, R0-R7 and `make check` gates | **PASS as a plan obligation.** Both repair layers have independent failure controls and canonical cross-run comparison |
| Accepted H0 target remains protected | Unchanged accepted-target inspection section; exact target/parent/tree and status record | **PASS.** Inspection is read-only; no maintenance path or result is written into the accepted object; executable replay remains `NOT RUN` |
| Publication and human decisions remain human-controlled | `LLM_POLICY_ALIGNMENT.md`; decision gates and explicit non-claims | **PASS.** No human signoff, acceptance inference, implementation authority, push, tag, publication, or gate change is present |

## 5. Review history and findings

### Authoritative review inputs

The review compared exact target `95cce2f...` against:

- original R8-ALM1 target
  `6bb3349b266a43d4572465379b5892b058e2fe39`;
- first R8-ALM1 packet
  `255aa176923581bf9248bfce5bc94217ff5577a8`;
- accepted R8 plan target
  `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`;
- accepted R8-A target
  `8fa9d672cfcfb81ab68d9ed9553a5af48b884932` and its
  acceptance-record-base convention;
- accepted R8-C target
  `f47ae60266a467ca1a7704fd9a50b140e0f31bb0`;
- accepted H0/R8-C target
  `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4`;
- historical active-line H0 source
  `102f2b0569396bf33ed2177ea5b7558cf5e6fbaa`;
- current `tests/r8/**`, launcher bootstrap table, source boundary, profile,
  report generator/checker, rejection suite, and filesystem primitives;
- the maintained roadmap, handoff, implementation plan, and planning index;
  and
- repository-root `LLM_POLICY_ALIGNMENT.md`.

The three session-local decision inputs were independently rehash-verified:

```text
fbf7a5d8ff82f14421cc2673104f29620b00a5c21b8eddf3ecebb4984fc69d92  r8-rejection-test-correction-decision-2026-09-29.md
2f54637ba1706e5e6c932472880ee2fb329c7e1f58f739d4debd6364b0af62f2  r8-maintenance-revision-decision-2026-09-29.md
13340156ceb7920f88f22dfea70976d69cfe189d692e3589c3b961b31c939ed4  blocked-metadata-2026-09-29.json
```

They remain session-local diagnosis and decision support, not maintained R8
evidence.

### Resolved finding 1 - implementation base and active-line relation

The first packet found that a future candidate could not remain a direct child
of the original plan while also preserving the review packet and a later
acceptance record on the active line.

R8-ALM1-A resolves that defect by defining:

```text
P = exact R8-ALM1-A plan target
Q = later decision-neutral review-packet commit for P
A = later current-line commit recording responsible-human acceptance of P
B = exact full SHA named by a separate implementation authorization
C = future maintenance implementation candidate
```

The default formula requires `Q` and `A` to preserve `P`, requires the
separate authorization to quote the full SHA of `A` and state `B=A`, and
requires `C` to be exactly one clean non-merge child of `B`. The plan
explicitly says the future SHA is unknown now and forbids guessed,
abbreviated, remembered, current-HEAD, original-target, packet, historical,
accepted-H0, or reconstructed-tree substitutes.

This matches the accepted R8-A precedent: the later acceptance-record commit,
not the immutable proposed plan target or its packet, became the exact
implementation base. The revised rule preserves decision history and provides
stable pre-commit and post-commit identity.

**Resolution:** closed. No further plan revision is required for this finding.

### Resolved finding 2 - current-line and historical failure boundaries

The first packet found that the original plan attributed the historical
whole-diff failure to the exact current line even though current execution
stops earlier.

R8-ALM1-A now records two independent controls:

1. **Current-line launcher authentication:** from exact future base `B`,
   unchanged pre-implementation execution must exit `126` with empty stdout
   and stderr before GNU Make because current R8-C plan bytes differ from the
   R8-A launcher lock.
2. **Historical whole-diff fixture:** from exact source `102f2b...` in the
   retained historical environment, `r8-check` must pass bootstrap, tools,
   profile, inventory, source, launcher, report generation, and report
   checking, then exit `2` at the first whole-diff fixture because the copy
   destination already exists.

Future candidate validation must prove that the first control is repaired,
that the whole-diff baseline is reached and passes, that removing the one
bounded `safeRemove` call recreates the historical first-fixture failure only
after updated authentication succeeds, and that restoring the stale R8-A
launcher entry independently recreates silent exit `126`.

The plan blocks validation if the historical environment cannot be
reconstructed. Retained command output associated with the 2026-09-29
decision package remains supporting history rather than a substitute for the
required future control. Its identity and content are bound by Git parentage,
hashes, and byte counts. It belongs to the earlier skew window by explicit
instruction ordering, so any embedded or surrounding wall-clock value remains
non-authoritative. Accepted-target execution is separate and remains
`NOT RUN`.

**Resolution:** closed. Current and historical behavior, future controls, and
evidence non-transfer are stated accurately.

### Additional review results

1. **Naming and collision handling:** PASS. `R8-ALM1` is distinct from the
   non-ancestor R8-B object and accepted R8-C/H0 history.
2. **Identity model:** PASS. The future schema records exact plan, packet,
   authorized base, candidate, historical source, accepted target, path/mode,
   launcher, report, negative-count, and environment identities while limiting
   the positive claim to active-line checker operability.
3. **Implementation inventory:** PASS. The ten R8 paths cover Make output,
   evaluator documentation, independent report generation/checking,
   source/relation enforcement, AST/source-boundary contracts, static launcher
   source/binary, and rejection behavior. Four current-position paths and
   planning derivatives cover status integration. No additional checker,
   lock, root, dependency, pin, or navigation path was identified.
4. **Filesystem correction:** PASS as a plan obligation. Existing
   `safeRemove` recursively validates bounded entries and rejects special
   objects; existing `safeCopyTree` still requires an absent destination.
   The accepted H0 target independently demonstrates the same bounded
   remove-before-overlay ordering without transferring its result.
5. **Environment boundary:** PASS. Retained active-line artifacts, RPMs,
   image identities, tool probes, and network-disabled execution assumptions
   are explicit. The derived image must be exported and independently hashed
   before future candidate evidence. Missing accepted-target assets remain a
   hard non-substitution boundary.
6. **Validation, claims, and stops:** PASS as plan obligations. Two fresh
   source/build volumes, at least 111 fail-closed negative cases, independent
   repair regressions, cross-run canonical identity, R0-R7 gates, root
   `make check`, accepted-target protection, no evidence transfer, and
   explicit stop conditions are all present.

### Retained open generated-output finding

A clean exact-target planning rebuild passes functional checks but changes 86
`docs/html/**` entries in the current documentation environment. The drift is
confined to generated planning output. This is the existing generated-byte
reproducibility finding, not an R8-ALM1-A plan, scope, or identity defect.

### Open questions for human judgment

- Is the acceptance-record/current-line base plus separate full-SHA
  authorization model the desired operational gate?
- Is the exact ten-R8/four-current-position path boundary complete and
  minimal?
- Are the static launcher, retained OCI/tool inputs, Git semantics, and
  same-euid filesystem residual acceptable trusted boundaries?
- Do the dual controls and at least 111 negative cases adequately cover both
  repair layers without creating success-shaped evidence transfer?
- Is inspection-only accepted-target protection sufficient while its exact
  Node/OCI environment remains unavailable?
- Is functional documentation validation sufficient while generated planning
  bytes remain non-reproducible?

No significant open automated-review finding remains. These questions require
responsible-human judgment rather than another mandatory plan correction.

## 6. Validation and retained evidence

The applicable responsible-human decision date for this record is
**2026-09-29**, taken from the responsible-human session instruction rather
than from the host clock. During the earlier validation and acceptance-record
window, the responsible human reported that the hardware RTC/system clock was
wrong. All host or system wall-clock values from that earlier skew window
remain non-authoritative supporting metadata, including `date` output,
command start/end wall times, filesystem mtimes and ctimes, log timestamps,
and Git commit display dates derived from that clock.

The responsible human later reported that the hardware and system clocks are
now correct. The explicit responsible-human correction instruction, not any
wall-clock value, defines the boundary. New timestamps observed after that
instruction may be treated normally. They do not retroactively authenticate
or reorder timestamps, mtimes/ctimes, logs, or commit display dates from the
earlier skew window.

Historical identity and ordering remain anchored to exact Git parentage and
object identities, cryptographic hashes, byte counts, explicit
responsible-human instructions, and monotonic durations where available.
Retained command output from the earlier window supports a result through its
content, hash, and byte count, not through any wall-clock text it contains.
No earlier-window wall-clock value or apparent local chronology establishes
identity, ancestry, ordering, or the decision date. No check changed the
immutable target.

| Command or check | Execution boundary | Result and coverage |
| --- | --- | --- |
| Commit, parent, tree, plan blob, subject, authorship, recorded Git dates, ancestry, remote, and tag audit | Exact Git objects | PASS: supplied target/parent/tree and ancestry match; preferred James Morris authorship is present; target is private, local, unpushed, untagged, and contained by zero remote-tracking branches. Author/committer display dates from the earlier skew window remain non-authoritative; post-correction display dates may be treated normally, but Git parentage and hashes remain the primary historical ordering evidence |
| `git fsck --no-dangling 95cce2f...` | Fresh detached exact target | PASS |
| `git diff --check 255aa176... 95cce2f...` | Exact target | PASS |
| Exact changed-path, mode, immutable-boundary, and privacy audit | Exact target | PASS: 114 no-renames paths; seven maintained and 107 generated planning paths; every present target path mode `100644`; no symlink, executable, special, runtime, R8 checker, root, dependency, pin, Helium-generated, private-locator, credential, or publication path |
| Session decision-input SHA-256 verification | Session-local read-only inputs | PASS: all three hashes match the revised plan |
| R8-B history and accepted-boundary audit | Exact Git objects and maintained records | PASS: R8-B belongs to non-ancestor object `c6e0da62...`; accepted R8/R8-A/R8-C/H0 identities and gates remain unchanged |
| R8 source/blob comparison | Exact Git objects | PASS: all 23 current `tests/r8/**` blobs equal historical source `102f2b...`; current plan SHA-256 is R8-C `d7a0c4...`; launcher still pins R8-A `13f1b248...` |
| Independent profile count derivation | Exact historical and accepted JSON blobs | PASS: historical/current source has 147 rows / 119 `UNKNOWN` / 81 H0 blockers; accepted target has 147 / 118 / 80; both retain 33 H1-completion blockers, three H2-entry blockers, and `r8_h0_exit=not-met` |
| Historical whole-diff record inspection | Two retained fresh volume-backed runs at exact source `102f2b...` | PASS as retained historical diagnosis: both reached the first whole-diff fixture and exited `2` on `SafePathError: copy destination already exists`; this was not rerun or promoted to target evidence |
| Accepted-target object inspection | Exact target `1999ee70...` and acceptance record | PASS: exact parent/tree match; bounded `safeRemove` precedes `safeCopyTree`; accepted status remains 147/118/80, `BLOCKED-NOT-READY`, `r8_h0_exit=not-met`; executable replay remains `NOT RUN` |
| Exact current-line checked-launcher probe | Fresh detached worktree at `95cce2f...` | Expected control confirmed: exit `126`, zero stdout bytes, zero stderr bytes, both SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `npm ci`; `node --check pathfinder/tests/check-docs-render.mjs`; `node --check planning/.vitepress/config.mts` | Fresh detached exact target | PASS |
| `HE_CHROMIUM=... npm run docs:check` | Fresh detached exact target | PASS: planning diagrams, portable and HTTP planning builds, 77 Markdown sources, 78 HTML pages, no broken local targets, and 77-page Chromium `154.0.8037.57` HTTP/direct-file/responsive rendering |
| Exact-target planning rebuild drift audit | Same detached worktree | Known finding reproduced: 86 dirty entries, all confined to `docs/html/**`; maintained sources and Helium paths remained unchanged |
| `HE_CHROMIUM=... ./be docs-check` | Restored fresh detached exact target | PASS: planning and Helium build, link, browser, direct-file, and responsive/mobile gates |
| Helium generated-state preservation | Exact-target root documentation run | PASS: 71 generated HTML/SVG files retained byte/mode-identical pre/post manifest SHA-256 `6c968bec28904bac94945a40c62c1391a793bc4812be759a055f9c589e612d5e`; zero Helium generated dirty entries; final exact-target worktree clean |
| `git diff --check`; JS/TS syntax; exact candidate path/mode/privacy/immutable-input audit | Final pre-commit packet content | PASS: 113 no-renames paths; seven maintained mode-`100644` paths and 106 generated planning paths; revised plan and first packet remain byte unchanged; no runtime, R8 checker, root, dependency, pin, Helium-generated, credential, private-locator, or publication path |
| `npm run docs:build`; `HE_CHROMIUM=... npm run docs:check` | Final pre-commit packet content | PASS: planning diagrams, portable and HTTP builds, 78 Markdown sources, 79 HTML pages, no broken local targets, and 78-page Chromium `154.0.8037.57` HTTP/direct-file/responsive rendering |
| `HE_CHROMIUM=... ./be docs-check` plus explicit Helium snapshot restoration | Final pre-commit packet content | PASS: root planning and Helium documentation gate; Helium 12-source/13-page link and browser checks; 71-file HTML/SVG snapshot restored byte/mode-identically at manifest SHA-256 `6c968bec28904bac94945a40c62c1391a793bc4812be759a055f9c589e612d5e`; zero Helium generated dirty entries |

These checks validate the revised planning target, review facts, and
documentation integration only. They do not accept the plan, authorize
implementation, create an acceptance record, validate a future candidate,
rerun accepted H0, establish H0 readiness, authorize H1-H4, or produce K3,
runtime, proof, hardware, publication, or release evidence.

### Acceptance-record follow-up boundary

The documentation-only acceptance-record follow-up is validated separately
with exact target/packet ancestry checks, `git diff --check`,
JavaScript/TypeScript syntax checks, `npm run docs:build`, the planning link
checker, the complete planning HTTP/direct-file/responsive browser gate, and
root `./be docs-check`. Pre/post manifests bind the retained Helium generated
bytes and modes; if root documentation validation changes those generated
assets, the exact pre-check state is restored and rechecked before commit.

The evidence order for this follow-up is explicit. Exact Git parentage and
object identities, hashes, byte counts, explicit instructions, and monotonic
durations where available are primary for identity and ordering. Retained
command output is used by content, hash, and byte count. The applicable
responsible-human decision date `2026-09-29` comes from the session
instruction.

The hardware RTC/system clock was treated as wrong during the earlier skew
window. All wall-clock values from that window -- including `date` output,
command wall times, file mtimes/ctimes, log timestamps, and commit display
dates -- remain non-authoritative. The responsible human now reports the
hardware and system clocks corrected. Values observed after the explicit
correction instruction may be treated normally; the instruction sequence,
not a timestamp, determines which side of the boundary an observation falls
on. Git parentage and hashes remain the primary historical ordering evidence.

This later documentation-only RTC/system-clock status update changes only the
evidentiary treatment of time metadata. It changes no Git identity, retained
command result, responsible-human decision, acceptance boundary, or
authorization gate.

Those commands validate only this decision/status documentation, navigation,
browser-title inventory, generated planning HTML, and privacy/path/mode
boundary. They do not rerun or extend accepted plan target
`95cce2f692543da67054ec2d6061eb08a4061253`, authorize or validate an
R8-ALM1 implementation, rerun accepted H0, transfer H0 evidence or readiness,
start H1-H4, or supply K3, hardware, runtime, proof, publication, or release
evidence.

Applicable responsible-human decision date: **2026-09-29**, supplied by the
session instruction and not inferred from the RTC/system clock, `date`
output, file metadata, logs, commit display dates, or apparent local
ordering.

| Command or check | Follow-up result and boundary |
| --- | --- |
| Exact target, packet, parent, tree, and first-parent ancestry audit | PASS: target `95cce2f...` has parent `255aa176...` and tree `f826204b...`; packet `788b0b67...` is its direct child with tree `f9421606...`; the active branch began clean at that exact packet |
| RTC/system-clock correction-boundary audit | PASS: the explicit responsible-human instruction defines the correction boundary; earlier-window wall-clock values, mtimes/ctimes, log timestamps, commit display dates, and apparent chronology remain non-authoritative; newly observed post-correction timestamps may be treated normally; Git parentage/object identities, hashes, byte counts, explicit instructions, and monotonic durations remain primary for historical identity and ordering; decision date `2026-09-29` remains instruction-sourced |
| `git diff --check`; `node --check pathfinder/tests/check-docs-render.mjs`; `node --check planning/.vitepress/config.mts` | PASS for the maintained acceptance-record sources |
| Maintained path, mode, immutable-target, privacy, and publication-boundary audit | PASS: the complete status union is 125 no-renames paths comprising nine maintained regular mode-`100644` paths and 116 generated planning paths; the maintained inventory is exactly this record, six current-position sources, planning navigation, and the shared browser-title inventory; no private locator, credential, human `Signed-off-by`, publication-gate, accepted-plan, accepted-R8-plan, runtime, root, dependency, pin, tool-lock, or proof path changes |
| `npm run docs:build` and `npm run docs:build:http` | PASS with VitePress 1.6.4 and maintained planning diagrams |
| `node docs/check-links.mjs` | PASS: 78 Markdown sources, 79 HTML pages, and no broken local targets |
| `HE_CHROMIUM=/usr/lib64/chromium-browser/headless_shell node pathfinder/tests/check-docs-render.mjs planning` | PASS: 78 planning pages under Chromium `154.0.8037.57`, including HTTP, direct-file, desktop, and mobile/responsive checks; two intrinsic-overflow pages were recorded by the passing gate |
| `HE_CHROMIUM=/usr/lib64/chromium-browser/headless_shell ./be docs-check` | PASS: complete planning and Helium generation, links, HTTP rendering, direct-file rendering, and responsive browser gates; Helium reported 12 sources, 13 HTML pages, 12 rendered pages, and zero intrinsic-overflow pages |
| Helium generated-state snapshot and restoration audit | PASS after restoring four hash-named generated assets: 71 files match content-manifest SHA-256 `776ae55a66a56adc4f5990798ddd644edcd11526f5b6c40aa1ccadc1cf88de38`, mode-manifest SHA-256 `bf0049dc46da5d127ac643407f6c6eb09066e1439943a28d94da244528faad7f`, and empty scoped-status SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## 7. Recommended human review sequence

1. **Read the prior findings and their revised resolution.** Review this
   packet's two resolved-finding sections, then the revised plan's `Status and
   authority`, `Future implementation base, parent, and relation`, and
   `Required pre-implementation failure controls`.
2. **Inspect the exact revised target.**

   ```sh
   git show --no-ext-diff --stat --summary \
     95cce2f692543da67054ec2d6061eb08a4061253
   git diff --name-status --no-renames \
     255aa176923581bf9248bfce5bc94217ff5577a8 \
     95cce2f692543da67054ec2d6061eb08a4061253
   git ls-tree \
     95cce2f692543da67054ec2d6061eb08a4061253 \
     planning/single-hart-runtime-r8-active-line-maintenance-plan.md
   ```

3. **Compare the base model with accepted R8-A precedent.**

   ```sh
   git show \
     8fa9d672cfcfb81ab68d9ed9553a5af48b884932:planning/single-hart-runtime-r8-plan.md
   less planning/single-hart-runtime-r8-plan-r8a-review-summary.md
   ```

   Confirm that a later acceptance-record commit, followed by a separate
   full-SHA implementation authorization, preserves decision history.

4. **Inspect current versus historical failure facts.**

   ```sh
   git diff --quiet \
     102f2b0569396bf33ed2177ea5b7558cf5e6fbaa \
     95cce2f692543da67054ec2d6061eb08a4061253 \
     -- tests/r8

   git show \
     95cce2f692543da67054ec2d6061eb08a4061253:planning/single-hart-runtime-r8-plan.md |
     sha256sum

   git show \
     95cce2f692543da67054ec2d6061eb08a4061253:tests/r8/run-make.c |
     grep -A1 -B1 'planning/single-hart-runtime-r8-plan.md'
   ```

5. **Review inventory and fail-closed semantics.** Confirm the ten R8 paths,
   four current-position paths, exact modes, frozen paths, zero root/pin/
   dependency changes, and unchanged `safe-paths.mjs`.
6. **Review environment and evidence separation.** Confirm that current-line,
   historical, and accepted-target facts are independently attributed and
   that missing accepted-target assets remain a hard `NOT RUN` boundary.
7. **Review claims, stops, and successor exclusions.** Confirm no H0
   readiness, H1-H4, K3, runtime, proof, K0-S, publication, or successor
   authority follows.
8. **Confirm the recorded decision boundary.** Acceptance as plan text only
   is now recorded. Any implementation still requires a separate instruction
   naming the full exact implementation-base SHA, exact relation, and complete
   plan inventory.

For any rerun, use an isolated detached worktree:

```sh
git worktree add --detach \
  ../beryllium-r8-alm1a-plan-review \
  95cce2f692543da67054ec2d6061eb08a4061253
```

## 8. Human decision checklist

- [ ] The exact target, parent, tree, plan blob, and 114-path no-renames
      boundary are understood.
- [ ] The first packet remains immutable history and this packet is the
      current decision surface for R8-ALM1-A.
- [ ] `R8-ALM1` / `R8-ALM1-A` is appropriately distinct from R8-B, accepted
      R8-C/H0, K0-S, and the H0-H4 package sequence.
- [ ] The future `P/Q/A/B/C` relation preserves plan, review, and acceptance
      records and requires a separately authorized full exact base SHA.
- [ ] The current silent launcher exit `126` and historical whole-diff exit
      `2` are accurately separated and both remain mandatory future controls.
- [ ] The ten R8 paths, four current-position paths, exact modes, generated
      planning prefix, frozen paths, and zero root/pin/dependency changes are
      complete and minimal.
- [ ] The bounded `safeRemove` / destination-absent `safeCopyTree` semantics
      and named negative regressions are acceptable.
- [ ] The active-line maintenance environment and unavailable accepted-target
      environment are represented without evidence transfer or substitution.
- [ ] Two fresh runs, cross-run identity, R0-R7 gates, root `make check`,
      accepted-target inspection, and mandatory stops are adequate.
- [ ] Claims match evidence and do not imply H0 readiness, H1-H4 authority,
      K3/hardware execution, runtime behavior, proof, K0-S progress,
      publication, or release.

### Recorded decision

- [x] **Accept** exact target
      `95cce2f692543da67054ec2d6061eb08a4061253` as plan text only on
      2026-09-29 by the responsible-human instruction `accept`.
- [ ] Request revisions and require a new exact plan commit and packet.
- [ ] Defer and preserve the prior unaccepted state.

Only the acceptance-decision box is checked because the responsible human
explicitly supplied that decision. The technical-review boxes remain
unchecked as retained review history. No signature or human `Signed-off-by`
is generated.

## 9. After the decision

### Recorded outcome: exact plan target accepted as planning text only

Exact R8-ALM1-A plan target
`95cce2f692543da67054ec2d6061eb08a4061253` (parent
`255aa176923581bf9248bfce5bc94217ff5577a8`, tree
`f826204b12701114993743f949c6ee71a72def5c`) was accepted on 2026-09-29 by
the exact instruction quoted above. Packet commit
`788b0b6752b706ece8dc51dc2c0c5dca3e56376f` and this acceptance-record
follow-up are decision support, not accepted plan text or implementation.

The target remains immutable. Its
`r8_active_line_maintenance_plan=proposed-not-reviewed` and
`r8_active_line_maintenance_implementation=not-authorized` fields remain
frozen pre-decision content. This record carries the later acceptance without
rewriting them.

### Future implementation remains separately gated

This acceptance authorizes no implementation. Before any R8-ALM1
implementation begins, a separate exact responsible-human instruction must:

- name the full SHA of the later plan acceptance-record/current-line commit
  that becomes implementation base `B`;
- state the exact base-to-candidate relation required by the accepted plan;
- name the complete plan-governed implementation inventory; and
- preserve the accepted target, packet, acceptance record, dual exit-126/
  exit-2 controls, frozen paths, and all stop conditions.

Only after that separate instruction may one bounded candidate be prepared.
That candidate would still require its own exact-target validation, review,
and decision.

### Unchanged gates and non-authorizations

- Accepted H0/R8-C target
  `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` remains accepted but
  `BLOCKED-NOT-READY`, with 147 rows, 118 `UNKNOWN`, 80 H0-acceptance
  blockers, 33 H1-completion blockers, three H2-entry blockers, and
  `r8_h0_exit=not-met`.
- No H0 evidence, readiness, count, environment, implementation status, or
  authority transfers to R8-ALM1.
- R8-H1 through R8-H4 remain not started and unauthorized. K3 execution and
  all Beryllium hardware validation remain `NOT RUN`.
- Root `Makefile`, `be`, `scripts/check-be.sh`, dependencies, acceptance
  pins, tool locks, runtime paths, proof paths, accepted R0-R8 bytes, and
  `pathfinder/publication-gate.conf` remain unchanged.
- No push, tag, publication, release, clean-repository migration, archive, or
  upstream action is authorized.
- This plan and decision are not R8-B and do not start an H0 successor.

Had revisions been requested, a new target and packet would have been
required. Had review been deferred, this target would have remained
unaccepted. Neither alternative occurred.

**Status:** exact R8-ALM1-A plan target
`95cce2f692543da67054ec2d6061eb08a4061253` is responsible-human accepted
as plan text only as of 2026-09-29. Its immutable proposed status remains
retained pre-decision content. Implementation remains not authorized.

**Next:** preserve the exact accepted plan boundary. Do not begin
implementation unless a separate exact instruction names the full later
acceptance-record/current-line base SHA, exact relation, and complete plan
inventory.

**Action required from you:** none for this recorded acceptance.
Implementation, H0 successors, H1-H4, K3/hardware execution, integration,
dependencies, pins, tool locks, runtime/proof changes, push, tag,
publication, release, and migration remain behind their separate gates.
