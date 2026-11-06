<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R6 plan revision review and acceptance record

> **Repository rehoming note (current-line editorial context):** This record
> preserves the packet-time former private repository identity and remote
> state. The current active private repository is
> `beryllium-project/beryllium-hypervisor`; use
> [project orientation](project-orientation.md) for current repository
> guidance.

This document began as the decision-support packet for one exact immutable
commit — the **corrected** bounded R6 plan target
`75269f058ae578b0a76a113d6c05c0aaceeac8ec`, which carries **Plan revision
R6-A** (the D-15 injection site) — and now also records the responsible-human
decision taken on it. The decision-support material below is retained
unchanged as review history; it remains the evidence the decision rests on.
Except where a statement is explicitly marked as current, sections 1 through 9
describe the state **at the time of that decision**.

The earlier acceptance of the **original** R6 plan target
`609867fdad75279c0913022909efd65c4a838909` is untouched by this record. It
remains accepted history in
[`single-hart-runtime-r6-plan-review-summary.md`](single-hart-runtime-r6-plan-review-summary.md),
which stays the historical review-and-acceptance record for that target.

**Successor revision, recorded here for navigation only.** Continued D-15
implementation later exposed two factual/feasibility defects in this accepted
corrected plan's own evidence bookkeeping — a false `.monitor.text`
"grows by 8 bytes" layout claim, and a raw-trace retention rule that cannot
fit the plan's own 512 MiB bound. The narrow correction is
[Plan revision R6-B](single-hart-runtime-r6-plan.md#plan-revision-r6-b-d-15-image-layout-and-trace-retention),
which was **accepted at its own exact commit
`6d6464c6c937abccd59df932006c1049fd79fac6` on 2026-07-30**; that decision is
recorded in
[`single-hart-runtime-r6-plan-r6b-review-summary.md`](single-hart-runtime-r6-plan-r6b-review-summary.md),
not here, and R6 integration and evidence work may resume under the
already-recorded implementation authorization. Revision R6-B changes no
fixture construction and **does not alter, reopen, or qualify the decision
recorded below**: the acceptance of exact corrected plan target
`75269f058ae578b0a76a113d6c05c0aaceeac8ec`, and of the original target before
it, remains exact, complete, and byte unchanged. This note records no decision
on revision R6-B.

## Decision record

Responsible-human review **accepted the exact corrected R6 plan commit**
`75269f058ae578b0a76a113d6c05c0aaceeac8ec` (parent
`4bff41764cf8ec9275e771cd3c1ce124961da93a`) on 2026-07-30, in explicit
response to the exact acceptance question posed for that commit by this
packet. The recorded selection was: `Accept exact corrected R6 plan commit
(Recommended)`.

The corrected plan, carrying [Plan revision R6-A](single-hart-runtime-r6-plan.md#plan-revision-r6-a-d-15-injection-site),
is therefore the **plan of record for D-15**. The original plan target
`609867fdad75279c0913022909efd65c4a838909` (parent
`0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d`, accepted 2026-07-30) remains
**accepted history and byte unchanged**; this acceptance supersedes only the
D-15 injection site it corrects.

No new implementation authorization was requested or given here. Paused D-15
implementation **may resume** under the two already-recorded R6 implementation
authorization instructions, preserved verbatim with their timestamps:

- `proceed to implement R6 exact` (2026-07-30T20:34:36.241+00:00).
- `proceed with all r6 implementation work` (2026-07-30T20:36:53.931+00:00).

Resumption is bounded strictly by the corrected plan's scope, requires
retained images, logs, and digests, and keeps the wrong-error-class gate
enforced: if a measured cause, class, marker, or disposition differs from the
corrected expected result, the plan must be revised again rather than the
expectation relaxed at run time.

Packet commit `fd3e18477da24868edb53d492a0ed7d2636ac79d`
(`docs: add R6 D15 plan revision packet`) and this acceptance-record commit
are **decision support only**. Neither is plan text and neither is
implementation; the accepted corrected plan target remains exactly
`75269f058ae578b0a76a113d6c05c0aaceeac8ec` over parent
`4bff41764cf8ec9275e771cd3c1ce124961da93a`, byte unchanged.

This decision applies only to that exact immutable plan commit. It does
**not** accept any R6 implementation, any local `tests/r6/` work, any R6
evidence, report, or coverage claim; local R6 implementation remains
unreviewed, unaccepted, and incomplete, and D-15 has not been re-run or
reproduced under this record. It does not resolve the open generated-asset
byte-reproducibility finding, and it does not authorize R7, hardware
validation, formal-verification claims, a tag, a push, publication, or
release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `75269f058ae578b0a76a113d6c05c0aaceeac8ec` (`docs: correct bounded R6 D15 fixture plan`), parent `4bff41764cf8ec9275e771cd3c1ce124961da93a` (`docs: accept and authorize single-hart R6 plan`). Branch `beryllium/single-hart-runtime-r0`. |
| Original accepted plan | `609867fdad75279c0913022909efd65c4a838909` (parent `0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d`), responsible-human accepted 2026-07-30. It remains accepted history and **byte unchanged**; its review packet commit `21cf80daa2021590378de81d7a094e14f4e5c8ca` and the acceptance record `4bff41764cf8ec9275e771cd3c1ce124961da93a` are decision support, not plan and not implementation. |
| Current status | The corrected plan target is **accepted** at exact commit `75269f058ae578b0a76a113d6c05c0aaceeac8ec` on 2026-07-30, after automated mechanism and governance review. R6 implementation **has started locally** and remains **unreviewed, unaccepted, and incomplete** (no exact implementation commit, no evidence bundle, no coverage or acceptance claim); **paused D-15 implementation may now resume** under the already-recorded implementation authorization, within the corrected plan's scope. *Current as of this note:* D-15 has since resumed locally and exposed two bookkeeping defects in this accepted plan, so [Plan revision R6-B](single-hart-runtime-r6-plan.md#plan-revision-r6-b-d-15-image-layout-and-trace-retention) was drafted and **accepted at its own exact commit `6d6464c6c937abccd59df932006c1049fd79fac6` on 2026-07-30**, under which R6 integration and evidence work may resume; local R6 implementation remains unreviewed, unaccepted, and incomplete. |
| Decision recorded | Accept exact corrected plan commit `75269f058ae578b0a76a113d6c05c0aaceeac8ec` (recorded selection `Accept exact corrected R6 plan commit (Recommended)`, 2026-07-30). |
| Successor status | R7 is gated, undefined, not authorized, and **not started**. No R6 implementation review packet, evidence bundle, or acceptance record is requested, recorded, or implied here. |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`. The target is local, unpushed, and untagged: zero remote branches and zero tags contain it. Push, tag, publication, and release remain blocked. |

**Action expected:** no further plan-acceptance decision is pending for this
exact SHA. The corrected plan is accepted, and paused D-15 implementation may
resume under the already-recorded R6 implementation authorization. A future R6
implementation still requires its own exact-commit review packet and its own
separate acceptance, and any tag, push, publication, release, or R7 start
requires separate explicit authorization.

## 2. Deliverables and exact inventory

The parent delta is **83 changed files, 774 insertions, 365 deletions**: nine
non-generated source paths and 74 generated `docs/html/` entries (12 of the 83
entries are renames of hash-named assets). No `tests/r6/` implementation, no
`build/` artifact, no `include/`, `virt/`, or `arch/` file, no `Makefile`,
`be`, or `scripts/check-be.sh` change, no acceptance pin, and no
`pathfinder/publication-gate.conf` change is present.

| Deliverable | Paths | Purpose | Trust / privilege boundary | Primary human question |
| --- | --- | --- | --- | --- |
| Corrected bounded R6 plan | `planning/single-hart-runtime-r6-plan.md` | Add [Plan revision R6-A](single-hart-runtime-r6-plan.md#plan-revision-r6-a-d-15-injection-site) and apply it to the D-15 specification: base moves from copied `arch/riscv/be/r5-runtime.c` to copied `arch/riscv/be/r5-trap.S`, single defect becomes one contiguous `+2 / -0` hunk. | Plan text only. It creates no privileged surface, links no image, and executes nothing. | Is the corrected injection site the narrowest correction that reaches the declared `interrupt` class without touching any accepted byte? |
| Post-acceptance discovery record | `planning/single-hart-runtime-r6-plan-review-summary.md` | Time-scope the original decision, record what D-15 implementation found, and state that the revision is not accepted. | Historical decision record; it adds no new decision. | Does the added section leave the original acceptance intact and clearly separate "state at decision time" from "state now"? |
| Status and navigation sources | `.github/copilot-instructions.md`, `README.md`, `planning/README.md`, `planning/HANDOFF.md`, `planning/implementation-plan.md`, `planning/roadmap.md`, `planning/.vitepress/config.mts` | Say plan-accepted-but-revision-pending, implementation started-locally-unaccepted, D-15 and complete R6 paused. | Markdown is authoritative; navigation is documentation only. | Does every status surface avoid implying the revision, or any implementation, is accepted? |
| Generated planning site | `docs/html/**` (74 entries) | Render the changed authoritative Markdown. | Derivative, non-normative output; hash-named asset byte reproducibility remains an open finding. | Is rendering functional without treating generated-asset churn as resolved? |

### Non-generated paths in the target

```text
.github/copilot-instructions.md
README.md
planning/.vitepress/config.mts
planning/HANDOFF.md
planning/README.md
planning/implementation-plan.md
planning/roadmap.md
planning/single-hart-runtime-r6-plan-review-summary.md
planning/single-hart-runtime-r6-plan.md
```

Reproduce the inventory without interpretation:

```sh
git diff --name-status -M 4bff41764cf8ec9275e771cd3c1ce124961da93a 75269f058ae578b0a76a113d6c05c0aaceeac8ec
git diff --shortstat 4bff41764cf8ec9275e771cd3c1ce124961da93a 75269f058ae578b0a76a113d6c05c0aaceeac8ec
git diff --shortstat 609867fdad75279c0913022909efd65c4a838909 75269f058ae578b0a76a113d6c05c0aaceeac8ec -- planning/single-hart-runtime-r6-plan.md
```

Against the **original accepted plan target**, the plan document itself
changes by 306 insertions and 40 deletions in one file.

This packet's own commit `fd3e18477da24868edb53d492a0ed7d2636ac79d` and the
later acceptance-record commit that adds the decision above are decision
support only. Neither is the review target, neither is plan text, and neither
is implementation.

## 3. Claim boundary

### What the exact target supports saying

- It states a **corrected bounded plan**. It fixes one fixture's base file and
  one fixture's single defect, and it records why the accepted plan's D-15
  site cannot produce the class the accepted plan declares for it.
- It preserves every other fixture count, partition, class, detection layer,
  disposition, ledger entry, supported claim, and non-claim from accepted
  target `609867fdad75279c0913022909efd65c4a838909`.
- It supports the architectural argument in
  [the corrected placement](single-hart-runtime-r6-plan.md#the-corrected-placement)
  and
  [accepted-checker compatibility](single-hart-runtime-r6-plan.md#accepted-checker-compatibility),
  which is reasoning about the accepted R5 sources, the accepted checkers, the
  accepted linker script, and ratified RISC-V behavior.

### What it does not support saying

- It is **not corrected-implementation evidence**. No R6 build, run, report,
  digest, coverage number, or evidence bundle is claimed at this target.
- The retained local artifacts for the **superseded** injection site (the
  copied `arch/riscv/be/r5-runtime.c` variant that deterministically fails as
  `BE_R5:FAIL entry-controls`, last marker `BE_R5:04`, under both pinned
  toolchains) live in the untracked `tests/r6/` working tree. They are
  **outside this commit**, they are evidence for the **plan defect** only, and
  they say nothing about the corrected placement.
- A development-session exploratory report that the corrected placement builds
  under both pinned toolchains and yields `interrupt` is **unretained**: its
  scratch images, console/trace logs, and digests were not kept. It is not
  independently checkable and **must not influence acceptance**.
- The corrected
  [expected deterministic result](single-hart-runtime-r6-plan.md#expected-deterministic-result)
  table is this revision's **normative expected result**, explicitly
  `NOT RUN / unverified as retained R6 evidence`.

### Trusted or assumed

Pinned GCC, Clang, GNU ld, lld, QEMU, OpenSBI, and assembler/disassembler
behavior; the accepted R5 sources and checkers as written; ratified RISC-V
interrupt-delivery semantics (an interrupt destined for a higher privilege
level is taken regardless of the lower level's global enable); and the
correspondence between inspected assembly and executed instructions.

### Explicit non-claims

This target does not implement, accept, or claim: any R6 fixture, harness,
report, or evidence bundle; R6 coverage; R6 implementation acceptance; R7
exact-byte proof; hardware validation; formal verification or refinement;
Linux, service, guest-SBI, device, DMA, timer, interrupt-controller,
multicore, policy, CHERI, or TE behavior; resolution of the open
generated-asset byte-reproducibility finding; or any tag, push, publication,
or release authority.

## 4. Load-bearing planned invariants

These are the properties the decision rests on. Each is planned text at this
target, not measured behavior.

| Planned invariant | Plan reference | Evidence boundary |
| --- | --- | --- |
| D-15's defect is a copy of `arch/riscv/be/r5-trap.S` carrying exactly one contiguous `+2 / -0` hunk, placed after **every** `be_r5_switch_tail` entry-control readback (`satp`, `sstatus`, `stvec`, `sscratch`, `sie`, `scounteren`, `hstatus`, `hie`, `hvip`, `vsatp`, `hgatp`) and after the last frame-restore pair (`ld t0, FR_HTVAL(t6)` / `csrw htval, t0`), immediately before `.option pop` and the jump to `be_r5_enter_guest_tail`. | [Corrected placement](single-hart-runtime-r6-plan.md#the-corrected-placement) | Planned. A future checked D-15 build must show exactly this hunk against the pinned accepted base digest. |
| The two instructions are exactly `csrsi hvip, 4` then `csrsi hie, 4`. Both are required: `hvip` alone sets `VSSIP` with `hie.VSSIE` clear, so the image is architecturally indistinguishable from the control image; `hie` alone enables an interrupt that is never pending. With `hideleg = 0` the pending, enabled VS software interrupt is HS destined. `csrsi` uses a 5-bit immediate, so **no GPR is read or written** and `t6`/`t5`/`t4`/`t0`/`t1` and the guest restore sequence are untouched. | [Corrected placement](single-hart-runtime-r6-plan.md#the-corrected-placement) | Planned, argued from register semantics rather than from any measurement. |
| Zero protected guest instructions retire: `SRET` enters VS at `0x40011000`, the interrupt is taken immediately, `scause=0x8000000000000002`, `sepc=0x40011000`, `stval=0`, `htval=0`, `hideleg=0`, last marker `BE_R5:04`, class `interrupt`, no `V=1` protected entry dump, no `BE_R5:05`, no `BE_R5:12`, no `BE_R5:SRST_RETURNED`, monitor-issued SBI SRST with QEMU status `0`. | [Expected deterministic result](single-hart-runtime-r6-plan.md#expected-deterministic-result) | `NOT RUN / unverified as retained R6 evidence` at this target. |
| Accepted checkers stay unmodified and still pass: no call in the tail (`csrsi` is not `jal`/`jalr`/`call`/`tail`), pinned readback order intact, all eight `ld`/`csrw` restore adjacency windows intact, no `csrw hgatp` and no `hfence.gvma` added, exactly four image-wide HGATP writes, one `sret` in `r5-trap.S` and two image-wide, unchanged call sites, marker sets, and symbol addresses (L3–L7). | [Accepted-checker compatibility](single-hart-runtime-r6-plan.md#accepted-checker-compatibility) | Planned disposition. A future run must show L6 `pass` and L7 accepted parity with unchanged checkers. |
| The L8 differential delta is exactly the two inserted instructions plus the deterministic 8-byte shift of the monitor code after them, entirely inside the declared `monitor-range`; the linker script fixes the next origin at `0x80208000`, so every other section address, size, page, pool, symbol, and the `0x34000` flat extent stay byte identical. **Superseded as written, retained as decision history:** the "8-byte shift" arithmetic in this row is factually wrong. The two inserted instructions are absorbed by the accepted `.align 4` padding, so `.monitor.text`'s allocated size is unchanged, the flat image extent is unchanged, and every defined allocated `FUNC`/`OBJECT` symbol the accepted checker fixes or requires keeps its address in both toolchains; the delta is exactly 10 bytes in 2 runs. That is narrower than an unqualified "no symbol moves" or "no other section" claim would suggest: `be_r5_switch_tail`'s address is unchanged but its `st_size` grows `212`->`220` in both toolchains, and non-allocated debug/symbol-table content (GCC `.debug_line`/`.debug_str`/`.debug_frame`/`.symtab`/`.strtab`/`.shstrtab` file offsets and total ELF size; Clang `.debug_line`/`.debug_aranges` offsets and 12 local `$d` mapping symbols) does change. That is confirmed by `readelf` on the built images and is explicitly excluded from the runtime/flat-image/symbol invariants above, because it is never allocated, loaded, or executed. The correction is [Plan revision R6-B](single-hart-runtime-r6-plan.md#plan-revision-r6-b-d-15-image-layout-and-trace-retention), **accepted as plan text at exact commit `6d6464c6c937abccd59df932006c1049fd79fac6` on 2026-07-30**; the values it pins are local unreviewed implementation discovery that must still be re-derived at the exact implementation commit. This annotation corrects a fact; it does not alter the decision recorded above. | [Accepted-checker compatibility](single-hart-runtime-r6-plan.md#accepted-checker-compatibility), [Per-partition layer applicability](single-hart-runtime-r6-plan.md#per-partition-layer-applicability) | Planned. A future L8 run must show the exact delta pinned by revision R6-B and no other differing byte outside the declared runtime/flat-image/allocated-symbol invariants. |
| Accepted R5 bytes remain immutable: the defect exists only as `tests/r6/fixtures/D-15/r5-trap.S.defect`, overlaid into a confined scratch tree; no accepted file is edited, and `tests/r5/check-acceptance.sh --require` still reports accepted target `165f4d001a2b59b582b397bdea79ec4826168fdb` unchanged. | [Accepted-checker compatibility](single-hart-runtime-r6-plan.md#accepted-checker-compatibility), [Immutable accepted bytes](single-hart-runtime-r6-plan.md#immutable-accepted-bytes) | Verified now only in the negative sense that this target changes no accepted file; the R1–R5 acceptance checkers pass (section 6). |
| The wrong-error-class gate is preserved, not weakened: if a future measurement differs in cause, class, marker, or disposition, the fixture fails as `wrong-error-class`, the harness must not relax the expectation at run time, and the plan must be revised again. | [Empirical status of this revision](single-hart-runtime-r6-plan.md#empirical-status-of-this-revision), [Fixture catalogue](single-hart-runtime-r6-plan.md#fixture-catalogue) | This gate is the mandatory future check that replaces the missing corrected-placement measurement. |
| Every other count is unchanged: the 47-entry single-defect catalogue, the static/host/dynamic partitions plus control case, D-10 through D-14 as copied `arch/riscv/be/r5-runtime.c` defects, the detection layers, outcome taxonomy, marker vocabulary, report schema, retention bounds, run matrix, and the acceptance-pin refresh scope. **Annotation:** accepted revision R6-B leaves every one of these counts unchanged, and corrects only how retention is expressed inside the same 512 MiB bound. | [Plan revision R6-A](single-hart-runtime-r6-plan.md#plan-revision-r6-a-d-15-injection-site) | Confirm by diffing the plan against the accepted target (section 7). |
| R7, hardware validation, formal verification, tag, push, publication, and release remain excluded and unclaimed. | [Publication, R7, and governance](single-hart-runtime-r6-plan.md#publication-r7-and-governance) | Unchanged from the accepted plan. |

## 5. Review history and findings

### Closed findings

1. **Accepted-plan placement failure was measured, not assumed.** Local,
   unaccepted D-15 implementation built the accepted plan's injection site (a
   copied `arch/riscv/be/r5-runtime.c` arming `hvip[2]`/`hie[2]` inside
   `switch_domain`) under both pinned toolchains and ran it under the pinned
   QEMU and firmware. It deterministically produced `BE_R5:FAIL
   entry-controls` with last marker `BE_R5:04`, never the declared `interrupt`
   class, because the accepted immutable `be_r5_switch_tail` re-reads `hie`
   and `hvip` on the published no-call path and rejects a non-zero value
   before `SRET`. Those artifacts remain on disk in the untracked `tests/r6/`
   tree and are outside this commit.
2. **Two independent analyses of the accepted tail derived the same safe
   site.** Both concluded that the only placement that reaches `interrupt`
   without touching an accepted byte or breaking an accepted checker rule is
   after every entry-control readback and after the last frame restore,
   immediately before `.option pop`, and both derived the same two-instruction
   `csrsi` delta.
3. **Revision review found unsupported empirical wording and it was fixed
   before this target.** Draft text leaned on the exploratory corrected-
   placement run as if it were evidence. The target now states explicitly that
   the exploratory scratch images, logs, and digests were **not retained**,
   that the report is **not independently checkable**, and that it **must not
   be cited as a reason for acceptance**; the expected-result table is labelled
   normative and `NOT RUN / unverified as retained R6 evidence`; and the
   "both instructions are required" argument is grounded in `hvip`/`hie`
   register semantics rather than in a measurement.
4. **Final mechanism review and final governance/claims review were both
   clean** on the content that became this target: the correction is narrow,
   the accepted-checker disposition is internally consistent, no count or
   non-claim moved, the original acceptance is left intact and byte unchanged,
   and no acceptance, authorization, or evidence claim is asserted.

### Open questions requiring human judgment

- **Accept architecture reasoning without a retained corrected run.** No
  retained, independently checkable build or QEMU result exists for the
  corrected placement at this target. Acceptance therefore rests on the
  register-semantics and accepted-checker reasoning in the plan, plus the
  mandatory future fail-closed measurement gate that applies when D-15 resumes.
  That future gate is not optional: if the measured cause, class, marker, or
  disposition differs, the plan must be revised again rather than the
  expectation relaxed.
- **Open finding, unchanged:** generated hash-named asset byte reproducibility
  remains unresolved. This packet does not call it resolved.

## 6. Validation actually run

On 2026-08-01, against a working tree whose **tracked** content equals exact
target `75269f058ae578b0a76a113d6c05c0aaceeac8ec` plus this packet and its
status/navigation updates — that is, equivalent plan content, not a rerun of
the immutable target itself:

| Command | Result | What it covers |
| --- | --- | --- |
| `npm run docs:build` | pass | VitePress build of the authoritative planning Markdown, including this packet and the corrected plan. |
| `./be docs-check` | pass | Planning and Helium documentation gates, including the static direct-file render inventory. |
| `./scripts/check-be.sh` | pass | Wrapper dispatch graph, SPDX/copyright headers, and retained Helium delegation. |
| `git diff --check` | pass | No whitespace defects in the staged documentation change. |
| `git diff --name-status -M`, `git diff --shortstat` | pass | Exact inventory of the target and of the plan delta against the accepted plan target. |
| `tests/r1..r5/check-acceptance.sh --require` | pass | Accepted R1–R5 targets, including `165f4d001a2b59b582b397bdea79ec4826168fdb`, are unchanged by this documentation work. |

Independent automated mechanism review and governance/claims review of the
plan revision were completed before the target commit; their findings and
resolutions are in section 5.

**Execution boundary.** The review target is the exact immutable commit
`75269f058ae578b0a76a113d6c05c0aaceeac8ec`. The packet commit
`fd3e18477da24868edb53d492a0ed7d2636ac79d` and the later acceptance-record
commit that adds the decision above are **separate follow-up commits**; their
own `npm run docs:build`, `./be docs-check`, `scripts/check-be.sh`, and
`git diff --check` runs validate that decision-support content, not the
target. Neither follow-up changes, amends, or re-validates the target, and
neither is R6 implementation.

**Not run and not retained:**

- No corrected-placement D-15 checked build, image check, or QEMU run is
  retained, reproducible, or accepted as evidence for this target.
- No R6 report, claim ledger, digest set, coverage figure, or evidence bundle
  exists.
- No R6 host, image, or emulation gate ran as part of this documentation
  change; `tests/r6/` is untracked, excluded from the commit, and not
  exercised or cited as acceptance evidence.
- Hardware validation and formal verification remain `NOT RUN` and unclaimed.

## 7. Recommended human review sequence

Use an isolated detached worktree so the concurrently changing untracked
`tests/r6/` tree cannot affect what you read.

1. **Identity and boundary.** Confirm the target, its parent, the private
   repository state, and that no remote ref or tag contains it.
2. **What actually changed against the accepted plan.** Read the plan delta
   against accepted target `609867fdad75279c0913022909efd65c4a838909` first;
   it is the decision.
3. **The correction itself.** Read
   [Plan revision R6-A](single-hart-runtime-r6-plan.md#plan-revision-r6-a-d-15-injection-site)
   end to end: the defect in the accepted plan, the corrected placement, the
   expected deterministic result, accepted-checker compatibility, and the
   empirical status.
4. **The non-evidence boundary.** Read
   [Empirical status of this revision](single-hart-runtime-r6-plan.md#empirical-status-of-this-revision)
   and the post-acceptance section of the historical record, and confirm the
   unretained exploratory report is excluded from the acceptance basis.
5. **Unchanged scope.** Spot-check that counts, partitions, layers, classes,
   dispositions, ledger, claims, and non-claims are preserved, and that D-10
   through D-14 remain copied `arch/riscv/be/r5-runtime.c` defects.
6. **Status surfaces.** Confirm that, at review time, no status document
   claimed the revision, or any local implementation, was accepted.

```sh
git show -s --format=fuller 75269f058ae578b0a76a113d6c05c0aaceeac8ec
git branch -r --contains 75269f058ae578b0a76a113d6c05c0aaceeac8ec
git tag --contains 75269f058ae578b0a76a113d6c05c0aaceeac8ec
git diff --check 4bff41764cf8ec9275e771cd3c1ce124961da93a 75269f058ae578b0a76a113d6c05c0aaceeac8ec
git diff --name-status -M 4bff41764cf8ec9275e771cd3c1ce124961da93a 75269f058ae578b0a76a113d6c05c0aaceeac8ec

# The decision delta: corrected plan against the accepted plan target.
git diff 609867fdad75279c0913022909efd65c4a838909 75269f058ae578b0a76a113d6c05c0aaceeac8ec -- planning/single-hart-runtime-r6-plan.md
git diff 4bff41764cf8ec9275e771cd3c1ce124961da93a 75269f058ae578b0a76a113d6c05c0aaceeac8ec -- planning/single-hart-runtime-r6-plan-review-summary.md

# Isolated read-only inspection at the exact target.
git worktree add --detach .review-r6-plan-revision 75269f058ae578b0a76a113d6c05c0aaceeac8ec
(cd .review-r6-plan-revision && sed -n '/^## Plan revision R6-A/,/^## Prerequisites and objective/p' planning/single-hart-runtime-r6-plan.md)
(cd .review-r6-plan-revision && sed -n '/^| D-10 /,/^| D-15 /p' planning/single-hart-runtime-r6-plan.md)
(cd .review-r6-plan-revision && ./be docs-check && ./be status)
git worktree remove .review-r6-plan-revision
```

The original decision-support material for the accepted plan target remains in
[`single-hart-runtime-r6-plan-review-summary.md`](single-hart-runtime-r6-plan-review-summary.md);
this packet does not restate or replace it.

## 8. Human decision checklist

The technical-judgment items below remain unchecked as review history. Only
the explicitly supplied decision is marked; automation does not answer,
pre-check, or sign for the questions, and checking them is not inferred from
the decision. No signature is generated on the responsible human's behalf.

- [ ] The correction's **scope** is right: only D-15's base file and single
  defect change, and the change is one contiguous `+2 / -0` hunk in a copied
  `arch/riscv/be/r5-trap.S`.
- [ ] The **architecture reasoning** is acceptable: placement after every
  entry-control readback and the last frame restore, both `csrsi` instructions
  required, no GPR touched, `hideleg = 0` making the pending, enabled VS
  software interrupt HS destined, and the accepted-checker disposition
  (no call, ordered verification, restore windows, no HGATP write or fence,
  `sret` counts, fixed layout, `monitor-range`-only L8 delta).
- [ ] The **non-evidence boundary** is acceptable: retained artifacts cover
  only the superseded placement and live outside this commit; the corrected
  placement's exploratory report is unretained and excluded; the expected
  result table is normative and `NOT RUN / unverified as retained R6
  evidence`.
- [ ] The **future wrong-error-class gate** is understood and required: when
  D-15 resumes, any cause/class/marker/disposition mismatch forces another
  plan revision, never a run-time relaxation of the expectation.
- [ ] **Counts and claims are unchanged**: the 47-entry catalogue, partitions,
  layers, classes, dispositions, ledger entries, supported claims, and
  non-claims match the accepted plan target, which remains accepted and byte
  unchanged.
- [ ] **R7 remains excluded**, along with hardware validation, formal
  verification, tag, push, publication, and release; local R6 implementation
  remains unreviewed and unaccepted.
- [x] **Decision:** accept exact commit
  `75269f058ae578b0a76a113d6c05c0aaceeac8ec` / ~~request revisions~~ /
  ~~defer~~.

Only the decision box above is checked, because that decision was explicitly
supplied by the responsible human on 2026-07-30. No signature is generated.

## 9. After the decision

### Recorded outcome: the exact commit is accepted

Exact corrected plan target `75269f058ae578b0a76a113d6c05c0aaceeac8ec` was
accepted on 2026-07-30, and this record names that SHA and date. The corrected
plan is now the plan of record for D-15. Paused D-15 implementation **may
resume** under the **already recorded** R6 implementation authorization
(`proceed to implement R6 exact`, `proceed with all r6 implementation work`),
strictly within the corrected plan's scope, with retained images, logs, and
digests, and with the wrong-error-class gate enforced.

Acceptance of this revision does **not** accept any R6 implementation, any
local `tests/r6/` work, any R6 evidence, report, or coverage claim, or R7. It
does not authorize a tag, a push, publication, or release, and it does not
resolve the open generated-asset byte-reproducibility finding. Local R6
implementation remains unreviewed, unaccepted, and incomplete: no D-15 result
is reproduced or claimed by this record, and a future R6 implementation still
requires its own exact-commit review packet and its own separate acceptance.

### Prohibited until separate authorization

- No R6 tag, private push, public release, or change to
  `pathfinder/publication-gate.conf`.
- No R7 start; R7 remains undefined, gated, and not authorized.
- No acceptance of any R6 implementation, and no presentation of local
  `tests/r6/` output as accepted R6 evidence.
- No run-time relaxation of any fixture expectation: a cause, class, marker,
  or disposition mismatch forces another plan revision.
- No modification of any accepted R0-R5 byte beyond the six enumerated
  acceptance-pin constants the accepted plan authorizes.
- No hardware-validation or formal-verification claim; both remain `NOT RUN`.
- The open generated-asset byte-reproducibility finding remains unresolved;
  this acceptance does not resolve it.

### Not taken: request revisions

Had revisions been requested, a new commit and a new review packet would have
been prepared, this SHA would not have been treated as accepted, and D-15
would have stayed paused.

### Not taken: defer

Had the decision been deferred, the original plan target would have stayed the
only accepted plan, this revision would have stayed unaccepted, D-15 and
complete R6 would have stayed paused, and no dependent work would have
started.

---

**Status:** exact corrected plan target
`75269f058ae578b0a76a113d6c05c0aaceeac8ec` (parent
`4bff41764cf8ec9275e771cd3c1ce124961da93a`) is **accepted** as of 2026-07-30.
Original plan target `609867fdad75279c0913022909efd65c4a838909` remains
accepted history and byte unchanged. R6 implementation is started locally and
remains **unreviewed, unaccepted, and incomplete**; D-15 may resume under the
already-recorded implementation authorization but has not been re-run,
reproduced, or accepted here. R7 is not started; hardware validation and
formal verification are `NOT RUN`; push, tag, publication, and release remain
blocked.

**Next:** bounded D-15 implementation may resume within the accepted corrected
plan's scope, with retained artifacts and the wrong-error-class gate enforced.
No local implementation result may be presented as accepted R6 evidence, and
completion of R6 requires its own exact-commit review and separate acceptance.

**Action required from you:** none for this decision. Plan-revision acceptance
is recorded. R6 implementation acceptance, tagging, pushing, publication,
release, and R7 all remain prohibited without separate explicit authorization.
