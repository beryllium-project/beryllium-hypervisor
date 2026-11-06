<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R6 plan review and acceptance record

> **Repository rehoming note (current-line editorial context):** This record
> preserves the packet-time former private repository identity and remote
> state. The current active private repository is
> `beryllium-project/beryllium-hypervisor`; use
> [project orientation](project-orientation.md) for current repository
> guidance.

This document began as the decision-support packet for one exact immutable
commit and now also records the responsible-human decisions taken on it. The
decision-support material below is retained unchanged as review history; it
remains the evidence the decisions rest on. Every status statement in sections
1 through 9 describes the state **at the time of that decision**; the current
state is in
[Post-acceptance implementation discovery](#post-acceptance-implementation-discovery-and-accepted-plan-revision).

## Decision record

Responsible-human review **accepted exact plan commit**
`609867fdad75279c0913022909efd65c4a838909` on 2026-07-30, in explicit response
to the question `Do you explicitly accept bounded R6 plan commit
609867fdad75279c0913022909efd65c4a838909?`. The recorded selection was:
`Accept exact R6 plan commit (Recommended)`.

Responsible-human review **separately authorized R6 implementation work** under
the master-plan R6 row. Both instructions are preserved verbatim with their
timestamps:

- `proceed to implement R6 exact` (2026-07-30T20:34:36.241+00:00).
- `proceed with all r6 implementation work` (2026-07-30T20:36:53.931+00:00).

Those two authorization instructions preceded plan acceptance and did not
themselves accept the plan. With the exact plan commit now accepted, both gates
are satisfied and bounded R6 implementation may begin strictly within the
accepted plan's scope. It has **not** started as of this record.

Packet commit `21cf80daa2021590378de81d7a094e14f4e5c8ca`
(`docs: add R6 plan review packet`) and this acceptance-record commit are
decision support only. Neither is the plan and neither is implementation; the
accepted plan target remains exactly `609867fdad75279c0913022909efd65c4a838909`
over parent `0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d`, byte unchanged.

These decisions apply only to that exact immutable plan commit. They do not
accept any future R6 implementation, do not resolve the open generated-asset
byte-reproducibility finding, and do not authorize an R6 tag, a private push,
public release, R7, hardware validation, or formal-verification claims.

## Post-acceptance implementation discovery and accepted plan revision

This section records what happened **after** the decision above. It records no
new decision of its own — the revision decision is recorded in the
[R6 plan revision review and acceptance record](single-hart-runtime-r6-plan-revision-review-summary.md)
— and it leaves accepted plan target
`609867fdad75279c0913022909efd65c4a838909` accepted history and byte
unchanged.

| Fact | State on 2026-08-01 |
| --- | --- |
| Original accepted plan target | `609867fdad75279c0913022909efd65c4a838909`, still accepted history, unchanged |
| Corrected plan target | `75269f058ae578b0a76a113d6c05c0aaceeac8ec` (parent `4bff41764cf8ec9275e771cd3c1ce124961da93a`), carrying Plan revision R6-A, **accepted 2026-07-30**; it is the plan of record for D-15 |
| R6 implementation | started locally; **not reviewed, not accepted, not complete**; no exact implementation commit, no evidence bundle, no coverage or acceptance claim |
| D-15 | **may resume** under the already-recorded R6 implementation authorization, within the corrected plan's scope; not re-run, reproduced, or accepted by any record |
| Complete R6 | **not complete**; completion requires its own exact-commit review and separate acceptance |
| R7, hardware, formal verification, push, tag, publication, release | blocked, unchanged |

What the D-15 work found:

1. The accepted plan places D-15's single defect inside `switch_domain` in a
   copied `arch/riscv/be/r5-runtime.c`, arming `hvip[2]` and `hie[2]` after
   publication and before the tail, and declares the error class `interrupt`.
2. The accepted, immutable `be_r5_switch_tail` re-reads `hie` and `hvip` on the
   published no-call path and rejects a non-zero value before `SRET`, so that
   arming is caught by the accepted mechanism itself.
3. Two independent analyses and actual builds under both pinned toolchains,
   run under the pinned QEMU and firmware, deterministically produced
   `BE_R5:FAIL entry-controls` with last marker `BE_R5:04` instead of the
   declared `interrupt`. The declared class is unreachable at the named site.
   The built fixture, its run outputs, and its digests for this (superseded)
   placement remain retained on disk, so this result is independently
   reproducible through the checked `tests/r6/` targets.
4. This is exactly the situation the accepted plan's wrong-error-class rule
   governs: the harness must not relax the expectation at run time, and the
   plan must be revised. The rule is preserved, not weakened.

The narrow correction is recorded as
[Plan revision R6-A](single-hart-runtime-r6-plan.md#plan-revision-r6-a-d-15-injection-site):
D-15's base changes from `arch/riscv/be/r5-runtime.c` to
`arch/riscv/be/r5-trap.S`, and its single defect becomes exactly
`csrsi hvip, 4` followed by `csrsi hie, 4`, inserted after every
`be_r5_switch_tail` entry-control readback and after the last frame restore,
immediately before `.option pop` and the jump to `be_r5_enter_guest_tail`.
D-10 through D-14 remain copied `arch/riscv/be/r5-runtime.c` defects, and every
count, class, layer, disposition, ledger entry, claim, and non-claim in the
plan is preserved.

During that same development-session exploratory work, the corrected
placement (a copied `arch/riscv/be/r5-trap.S` with the two-instruction
insertion above) was **reported** to build under both pinned toolchains and to
yield the expected `interrupt` result under the pinned QEMU and firmware. The
scratch images, console/trace logs, and digests from that exploratory session
were **not retained**: only the fixture, build outputs, and run artifacts for
the accepted plan's original (superseded) placement survive, matching fact 3
above. Because no raw artifact for the corrected placement survives to
re-derive, hash, or diff against the accepted checkers, that report is **not
independently checkable evidence for this exact plan revision target**. It
must not be cited as a reason for responsible-human acceptance of this
revision; it is recorded only as the implementation discovery that motivated
drafting the revision.

The corrected expectation in
[Plan revision R6-A](single-hart-runtime-r6-plan.md#plan-revision-r6-a-d-15-injection-site)
is a normative expected result, not a verified one: it stays `NOT RUN /
unverified as retained R6 evidence` until resumed D-15 implementation runs a
checked `tests/r6/` build and run that reproduces it with retained images,
logs, and digests. The revision was accepted on the architecture and code
reasoning in the plan, and on that future fail-closed measurement gate, never
on the unretained exploratory report. The wrong-error-class gate applies
unchanged to that future measurement: any cause/class/marker/disposition
mismatch is a wrong error class requiring another plan revision, never a
run-time relaxation.

**Action expected:** none for the revision decision. Corrected exact plan
target `75269f058ae578b0a76a113d6c05c0aaceeac8ec` was reviewed and explicitly
accepted on 2026-07-30, so paused D-15 implementation may resume under the
already-recorded R6 implementation authorization, within the corrected plan's
scope. Nothing here accepts any R6 implementation, claims R6 implementation is
complete or reproduced, or unblocks R7 or publication.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `609867fdad75279c0913022909efd65c4a838909` (`docs: add bounded single-hart R6 plan`), parent `0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d` (`docs: record exact R5 implementation acceptance`). |
| Status at decision time | The bounded R6 plan is **accepted** at exact commit `609867fdad75279c0913022909efd65c4a838909` on 2026-07-30. R6 implementation is **separately authorized** and had **not started** at that moment: no `tests/r6/` tree, no `include/`, `virt/`, or `arch/` R6 file, and no `Makefile`, `be`, or `scripts/check-be.sh` R6 change existed. For the state after that decision see [Post-acceptance implementation discovery](#post-acceptance-implementation-discovery-and-accepted-plan-revision). |
| Decision recorded | (A) Accept exact plan commit `609867fdad75279c0913022909efd65c4a838909`; (B) separately recorded authorization of R6 implementation work under the master-plan R6 row. |
| Authorization instructions | `proceed to implement R6 exact` (2026-07-30T20:34:36.241+00:00) and `proceed with all r6 implementation work` (2026-07-30T20:36:53.931+00:00) are the recorded implementation authorization under the master-plan R6 row. They preceded and are independent of plan acceptance; with the plan now accepted, bounded implementation may begin within the accepted scope. |
| Predecessor status | Accepted R5 implementation remains exactly `165f4d001a2b59b582b397bdea79ec4826168fdb`; the R5 review packet `9bb89fe196740c5e3252bdccced6fb202df65e55` and the acceptance record `0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d` are decision support, not implementation. This record does not restate, revise, or re-open that acceptance. |
| Successor status | R7 is **not started**, undefined, and not authorized. This acceptance does not authorize R7. |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`. The target is local, unpushed, and untagged: zero remote branches and zero tags contain it. Push, tag, publication, and release remain **blocked**. |

**Action expected:** no further plan-acceptance decision is pending for this
exact SHA. Both the acceptance and the separate implementation authorization
are recorded. Bounded R6 implementation may begin within the accepted plan's
scope; any tag, push, public release, or R7 start requires separate explicit
authorization, and a future R6 implementation requires its own exact-commit
review and its own separate acceptance.

## 2. Deliverables

The exact parent delta contains **81 changed files: 2,595 insertions and 282
deletions**, split into **9 non-generated source paths** and **72 generated
`docs/html/` status entries**. There is no change under `include/`, `virt/`,
`arch/`, `tests/`, `model/`, `pathfinder/docs/html/`, the root `Makefile`, the
root `be` wrapper, `scripts/check-be.sh`, or
`pathfinder/publication-gate.conf`. The only changed test path is the
documentation browser-render inventory.

| Deliverable | Paths | Purpose | Trust / privilege boundary | Primary human question |
| --- | --- | --- | --- | --- |
| Bounded R6 plan | `planning/single-hart-runtime-r6-plan.md` (1,823 lines) | Freeze the proposed 47-entry single-defect adversarial-image catalogue, its detection layers, per-partition applicability rules, scratch contract, coverage ledger, report schema, self-test minima, and the authorized six-constant predecessor acceptance-pin refresh. | Plan only. It creates no privileged code, no fixture, no harness, and no executable R6 surface; every future artifact is test-only under `tests/r6/`. | Is a test-only catalogue over byte-immutable accepted R5 the right shape for the master-plan R6 row, and is the catalogue both finite and sufficient? |
| Status and authorization boundary | `.github/copilot-instructions.md`, `README.md`, `planning/README.md`, `planning/HANDOFF.md`, `planning/implementation-plan.md`, `planning/roadmap.md` | Record that R6 implementation work is authorized under the master-plan R6 row while the plan itself is unaccepted and implementation has not started. | Documentation only; it changes no gate, checker, or wrapper. | Does every status surface separate *implementation authorization* from *plan acceptance* without implying either is complete? |
| Navigation and render inventory | `planning/.vitepress/config.mts`, `pathfinder/tests/check-docs-render.mjs` | Publish the plan in the three maintained sidebars and add it to the browser-render coverage list. | The render inventory exercises documentation rendering only; it asserts nothing about R6 behavior. | Is the new document reachable and covered without implying accepted status? |
| Generated documentation | 72 entries under `docs/html/` (including the new `docs/html/single-hart-runtime-r6-plan.html`) | Render the changed authoritative Markdown and navigation. | Derivative, non-normative output. Hash-named asset byte reproducibility remains an open finding. | Do rendering and links work without treating generated-asset churn as resolved? |

### Exact changed-file inventory

Non-generated source paths (9):

```text
.github/copilot-instructions.md
README.md
pathfinder/tests/check-docs-render.mjs
planning/.vitepress/config.mts
planning/HANDOFF.md
planning/README.md
planning/implementation-plan.md
planning/roadmap.md
planning/single-hart-runtime-r6-plan.md
```

Generated `docs/html/` status entries: 72, comprising 52 modified, 8 added, 5
deleted, and 7 renamed paths (`git diff -M`). The added set includes the new
`docs/html/single-hart-runtime-r6-plan.html` page and its asset pair; the
deleted and renamed entries are hash-named VitePress assets. No
`pathfinder/docs/html/` path changed in the target.

Reproduce the inventory without interpretation:

```sh
git diff --name-status -M 0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d 609867fdad75279c0913022909efd65c4a838909
git diff --numstat 0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d 609867fdad75279c0913022909efd65c4a838909
```

## 3. Claim boundary

**What this exact commit supports saying.** It defines a bounded R6 *design,
fixture, and evidence plan*: a finite catalogue of 47 entries (14 static image,
17 host mechanism, 15 dynamic, 1 control; 46 carrying exactly one declared
defect), an eleven-layer detection pipeline in accepted R5 execution order, a
per-partition applicability rule set, a confined scratch contract, a disjoint
coverage ledger over the 29 non-`none` `enum be_r5_error` classes, a
deterministic report schema `be-r6-adversarial-images-v1`, retention bounds,
self-test minima, and an exactly enumerated six-constant predecessor
acceptance-pin refresh. Planned R6 commands are explicitly **NOT IMPLEMENTED /
NOT RUN**.

**What remains trusted or assumed.** Any future R6 result would trust pinned
GCC, Clang, GNU `ld`, `lld`, GNU Make, `bash`, Node, QEMU 10.2.2, and the
digest-pinned OpenSBI blob; it would trust the accepted R0-R5 mechanism as the
measurement instrument rather than re-proving it; and it assumes QEMU models
the bounded H-extension behavior exercised, on a single hart with no DMA, no
external device, and no concurrency. The plan's own architectural expectations
(for example D-06's cause `22` for a VS-mode `csrr hgatp`, and D-15's
`scause=0x8000000000000002`) are stated predictions to be measured, not results.

**What is unavailable or `NOT RUN`.** There is no R6 implementation, no
fixture, no harness, no host unit test, no image build, no QEMU run, no report,
no evidence bundle, and no claim ledger at this target. Hardware validation is
`NOT RUN`. Formal verification and refinement are `NOT RUN` and not claimed.
The open generated-asset byte-reproducibility finding remains unresolved.

**What the commit explicitly does not implement or claim.** It implements no
runtime behavior, no policy, no scheduling, restart, rollback, dynamic binding,
root edit, PTE write, or guest SBI; it adds no Linux, service, driver, device,
DMA/IOMMU, multicore, capability, Type Enforcement, or CHERI behavior; it
provides no R7 content; and it makes no acceptance, publication, or
release-readiness claim. It does not re-open or re-validate accepted R0-R5
targets, and it is not itself R6 implementation.

## 4. Load-bearing planned invariants

Each row is a property the plan makes binding on a future R6 package. The
"Accepted binding" column names an artifact that exists **today** in the
accepted R0-R5 packages and that would enforce or contradict the invariant, so
the review does not rest on the plan's prose alone.

| Planned invariant | Plan reference | Accepted binding that exists today | Future evidence boundary |
| --- | --- | --- | --- |
| **No production R6 surface.** No `include/be/r6.h`, `virt/be/r6.c`, or `arch/riscv/be/r6-*`; no byte of `include/`, `virt/`, or `arch/` changes; every artifact is test-only under `tests/r6/` plus bounded root integration. | [§ Decision: no new production-like R6 surface](single-hart-runtime-r6-plan.md#decision-no-new-production-like-r6-surface), [§ Planned source boundary](single-hart-runtime-r6-plan.md#planned-source-boundary) | `tests/r5/check-sources.mjs:66,75` rejects any `be_r6`/`BE_R6` identifier; `tests/r5/check-image.mjs:140` rejects any `(^\|_)r6(_\|$)` or `be_r6` image symbol. | A future package must show the accepted R5 source and image gates still pass unmodified, with fixture sources keeping every accepted symbol name verbatim. |
| **Accepted R5 bytes immutable, with exactly one bounded exception.** The 43 immutable paths, the 6 mixed acceptance-record files, and every R0-R4 bound input stay byte-and-mode identical; only six enumerated predecessor acceptance-pin constants may be refreshed, in a mandated order, with revert self-tests in both directions. | [§ Immutable accepted bytes](single-hart-runtime-r6-plan.md#immutable-accepted-bytes), [§ Authorized acceptance-pin refresh](single-hart-runtime-r6-plan.md#authorized-acceptance-pin-refresh), [§ Effect on accepted acceptance status](single-hart-runtime-r6-plan.md#effect-on-accepted-acceptance-status) | `tests/r1/check-acceptance.sh:18,52` (`successor_makefile_sha256`); `tests/r3/check-accepted-content.mjs:64,94,99` and `tests/r4/check-accepted-content.mjs:86,91` (approved `be`, `scripts/check-be.sh`, `tests/r1/check-acceptance.sh` deltas); `tests/r5/check-acceptance.sh` (`r5_dependencies_match`). | A future package must show all five acceptance checkers passing before and after, with `r5_implementation_content_digest` byte identical and each of the six pins proven live by revert. |
| **Finite 47-entry catalogue.** 14 static + 17 host + 15 dynamic + 1 control, 46 with exactly one declared defect, each with pinned base/defect/diff digests and a ≤6-added/≤6-removed line budget; `no-defect` and `multiple-defects` are rejections. | [§ Construction](single-hart-runtime-r6-plan.md#construction), [§ Fixture catalogue](single-hart-runtime-r6-plan.md#fixture-catalogue) | The 30 frozen little-endian fixture words in `tests/r5/check-image.mjs:327-332`, which every guest-opcode fixture must alter in exactly one position. | `tests/r6/check-fixtures.mjs` and the report must assert the catalogue digest and every fixed count; a count divergence fails R6 rather than being reconciled in the report. |
| **Unsafe static images are quarantined, never executed.** S-01..S-04 and S-11..S-14 never produce an ELF; S-05..S-10 link and are immediately quarantined under `build/r6/static/<id>/<toolchain>/rejected/`; QEMU is forbidden for every `S-*` and `H-*` entry and is executable-gated, not convention-gated. | [§ Static image fixtures](single-hart-runtime-r6-plan.md#static-image-fixtures-qemu-forbidden), [§ Per-partition layer applicability](single-hart-runtime-r6-plan.md#per-partition-layer-applicability), [§ Partitions](single-hart-runtime-r6-plan.md#partitions) | Accepted linker `ASSERT`s in `arch/riscv/be/r5-beryllium.lds` and the accepted `tests/r5/check-image.mjs` semantic rules are the rejecting mechanisms. | `tests/r6/run-qemu.sh` must refuse non-dynamic identifiers, and `tests/r6/check-static.mjs` plus `generate-evidence.sh` must assert absence of console, trace, and exit-status artifacts. |
| **Dynamic L6 dispositions are single exact messages, not patterns, and every image is single-delta.** Each dynamic manifest declares `pass` or `reject-with` plus one exact assertion message; L8 compares each image against the same-toolchain control image and permits exactly the declared delta and nothing else. | [§ Per-partition layer applicability](single-hart-runtime-r6-plan.md#per-partition-layer-applicability), [§ Dynamic fail-closed fixtures](single-hart-runtime-r6-plan.md#dynamic-fail-closed-fixtures-qemu-allowed) | The accepted image checker is never bypassed; the control image is the one that passed it and `tests/r5/check-image-parity.mjs` in full. | A declared-versus-observed mismatch is `layer-shift` and fails the run; `undeclared-image-delta` and `unexpected-image-check-pass` are forbidden outcomes. |
| **Complete, disjoint primary coverage of all 29 error classes.** 12 dynamic primaries plus 17 host primaries across 16 host fixtures, 0 uncovered, 4 secondary claims never counted toward completeness. | [§ Coverage ledger](single-hart-runtime-r6-plan.md#coverage-ledger), [§ Host mechanism fixtures](single-hart-runtime-r6-plan.md#host-mechanism-fixtures-no-image-no-qemu) | `be_r5_error_name()` in `virt/be/r5.c` defines exactly 30 cases: `none` plus the 29 classes the ledger must cover. | `tests/r6/check-report.mjs` must fail on any uncovered class, any duplicate primary, or any secondary counted toward completeness. |
| **Confined scratch, never mistaken for tool drift.** 16 components created parent-first by one creator, 5 byte-and-mode identical source components, the R3 base tool-lock verified against a literal digest and the real worktree, and every fault reported as `scratch-fault` under its own component name. | [§ Scratch tree and accepted build reuse](single-hart-runtime-r6-plan.md#scratch-tree-and-accepted-build-reuse), [§ Outcome taxonomy](single-hart-runtime-r6-plan.md#outcome-taxonomy-and-marker-vocabulary) | `scratchComponents` and `requireScratch()` in `tests/r5/tool-lock.mjs:88-91,96` fail closed on the seven inherited components; `tests/r3/tool-lock.conf` hashes to `c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b`, exactly the literal the plan pins. | `scratch-fault` is never attributed to a fixture, never counted as a layer result, and must be exercised by at least 20 prerequisite self-tests covering all 16 components and all four fault kinds. |
| **Exact checked launcher and digest-bound tooling.** `tests/r6/run-make.sh` accepts exactly ten targets and refuses hostile controls before creating anything; `tests/r6/tool-lock.conf` (`be-r6-tool-lock-v1`) binds every normative executable, the firmware blob, the R3 base lock, and `R6_ACCEPTED_R5_COMMIT=165f4d001a2b59b582b397bdea79ec4826168fdb`. | [§ Locks, launcher, and hostile controls](single-hart-runtime-r6-plan.md#locks-launcher-and-hostile-controls), [§ Build, toolchain, and run matrix](single-hart-runtime-r6-plan.md#build-toolchain-and-run-matrix) | The accepted R3-R5 launcher and tool-lock practice, including `tests/r5/run-make.sh` ordering, which the plan mirrors rather than relaxes. | At least 40 launcher, 20 command-line, and 20 environment control cases must be refused, plus a fresh-worktree bootstrap and symlink-rejection proof. |
| **A distinct live authorization key, with the accepted historical line preserved.** R6 owns `r6_package_authorization`; the accepted R5 line `r6_authorization=not-authorized` is emitted unchanged, appears exactly once in `be status`, and no R6 authority-bearing surface may emit `r6_authorization=authorized`. | [§ Report, retention, and reproducibility](single-hart-runtime-r6-plan.md#report-retention-and-reproducibility), [§ `be status` without a duplicate semantic key](single-hart-runtime-r6-plan.md#be-status-without-a-duplicate-semantic-key) | `tests/r5/check-acceptance.sh:82` prints the literal; `tests/r5/check-accepted-content.mjs:260,268` requires it and forbids the `authorized` form; `scripts/check-be.sh:191` asserts it in `be status`. | The prohibition is scoped to enumerated authority-bearing surfaces, matching accepted R5 enforcement; quoting the literal in planning prose stays permitted and must not be turned into a repository-wide textual ban. |
| **R7, hardware, formal, and publication boundaries hold.** R6 acceptance would not authorize R7, a tag, a push, publication, or release; hardware validation and formal verification stay `NOT RUN`; `pathfinder/publication-gate.conf` is untouched. | [§ Publication, R7, and governance](single-hart-runtime-r6-plan.md#publication-r7-and-governance), [§ Explicit non-claims and exclusions](single-hart-runtime-r6-plan.md#explicit-non-claims-and-exclusions) | `LLM_POLICY_ALIGNMENT.md` publication gate; the accepted R5 record already states that R5 acceptance authorized no successor. | A future R6 report must carry `acceptance: "not-reviewed"`, `publication: "blocked"`, `hardware: "NOT-RUN"`, and `r7_content: "excluded"`. |

## 5. Review history and resolved findings

The plan was produced and then independently reviewed over several mechanism-
and evidence-focused rounds before this commit. Every substantive finding below
was corrected in the drafted text; none is left open.

**Critical, structural:**

1. **Root acceptance-pin conflict.** The required root integration
   (`Makefile`, `be`, `scripts/check-be.sh`) is bound by predecessor acceptance
   checkers, so an unrefreshed pin would flip `r1_acceptance` and cascade to
   `r5_acceptance=review-required` — a dependency-status regression falsely
   readable as an R5 mechanism change. Resolved by an explicitly authorized,
   exactly six-constant refresh with mandated ordering, bidirectional revert
   self-tests, and an unchanged `r5_implementation_content_digest` requirement.
2. **Dynamic images rejected by the accepted image checker.** An earlier
   construction assumed guest-opcode fixtures would reach QEMU, but the
   accepted checker pins the 30 frozen words and rejects them first. Resolved
   by the per-partition applicability rules: a declared, enumerated,
   single-message `accepted_image_check` disposition, plus mandatory L8
   single-delta comparison against a control image that passed the complete
   accepted checker, so no invariant is waived.
3. **Pipeline, layer, and count errors.** Layer ordering did not match the
   accepted `tests/r5/Makefile` execution order, and derived counts were
   inconsistent. Resolved by re-deriving the eleven layers in real execution
   order (source inventory first), making scratch preparation a precondition
   rather than a layer, and asserting every fixed count in the report.
4. **Wrong R4 markers.** Draft fixtures cited marker text that the accepted
   console does not emit. Resolved by quoting the accepted 22-line
   `expectedConsole` array verbatim and forbidding invented marker names.
5. **Coverage gaps and impossible host fixtures.** Some host fixtures named
   structure members that do not exist (for example `htinst`, an `observation`
   `stval`/`htval`, a `pending.valid` flag) or targeted classes their call
   cannot produce. Resolved by field-level accuracy notes taken from the
   accepted headers and validators, with each fixture proven to be the first
   failure by the recorded validation order.
6. **Dead S-08 construction.** A second `be_r5_switch_tail` call appended after
   a `noreturn` call is dead code removed at `-O2`, so the fixture would have
   passed silently. Resolved by two reachable call sites with textually
   distinct argument setup, plus a pre-L6 assertion that the disassembled
   `switch_domain` really contains two references.
7. **Authorization-key collision.** R6 initially reused `r6_authorization`,
   which the accepted R5 package owns as the historical value
   `not-authorized` and explicitly forbids in the `authorized` form. Resolved
   by the distinct live key `r6_package_authorization`, a provenance line, and
   an exactly-once assertion on the historical line.
8. **Scratch tree missing R3 dependencies.** The scratch inventory omitted
   `tests/r3/tool-lock.mjs` and `tests/r3/tool-lock.conf`, which
   `tests/r5/tool-lock.mjs` statically imports and digest-verifies, so every
   scratch build would have failed for the wrong reason. Resolved by making
   them a mandatory fifth source component with literal-digest and
   real-worktree verification.

**Correctness and honesty corrections:**

9. **Further unreachable or non-existent host fields.** A second pass found
   host fixtures whose mutation could not reach the declared class (notably the
   `publication` guard, reachable by a single mutation only through
   `switch_count`, and `frame-state`, which `be_r5_handle_exit` cannot
   produce). Resolved by re-siting those fixtures on the correct API and phase.
10. **Stale control sequence.** C-01 quoted an outdated marker sequence.
    Resolved by binding it line for line to the accepted 22-line array.
11. **Overbroad forbidden literal.** The draft implied a repository-wide ban on
    the string `r6_authorization=authorized`, which would have failed on
    documentation that quotes it. Resolved by scoping enforcement to an
    enumerated list of authority-bearing surfaces, matching accepted R5
    enforcement exactly.
12. **Two rationale overclaims, both about the accepted harness.** The draft
    claimed the accepted `tests/r5/Makefile` parse-time `make-control.mjs`
    guard applied to a direct `check-sources.mjs` invocation, and that the same
    parse-time probe established scratch-directory existence. Neither is true:
    the direct invocation parses no Makefile, and the probe never `stat`s the
    scratch paths. Both rationales were narrowed to what the accepted code
    actually does.

Both final independent reviewers, after these corrections, reported **no
remaining defect** in the drafted plan.

**Open questions requiring human judgment (not defects):**

- **The no-production-surface decision.** Keeping R6 entirely test-only is a
  deliberate scope choice with four stated justifications. It is the single
  most consequential structural decision in the plan and is explicitly marked
  "must be confirmed at review".
- **The D-06 cause-`22` assumption.** The plan predicts a virtual-instruction
  trap for a VS-mode `csrr hgatp`; if QEMU reports cause `2` instead, the plan
  requires measurement and plan revision rather than a run-time relaxation of
  the expectation. The same rule is written for D-15's asserted
  `scause=0x8000000000000002` and for D-13 if a future optimizer defeats the
  single-static-call-site construction.
- **Sufficiency of a finite catalogue.** 47 enumerated entries are explicitly
  not an exhaustive adversarial argument; whether this is enough evidence for
  the master-plan R6 row is a human judgment.
- **The open generated-asset byte-reproducibility finding** remains unresolved
  and is not closed by this packet, by this acceptance record, or by any
  decision on this target.

## 6. Validation and retained evidence

**On the exact target's content.** The four documentation and repository
commands below were run against pre-commit content equivalent to
`609867fdad75279c0913022909efd65c4a838909` while the plan was prepared:

```sh
npm run docs:build
./be docs-check
scripts/check-be.sh
git diff --check
```

They cover, respectively: the VitePress planning build including the new page
and the three sidebars; the generated-site link, static-render, and
browser-render gates including the new render-inventory entry; the `be`
wrapper's help and `be status` field assertions (unchanged by this target); and
whitespace/conflict hygiene of the diff.

**Independent re-verification performed for this packet, at the target.**
Assembler and disassembler probes under the accepted flags
(`riscv64-linux-gnu-as -march=rv64imac_zicsr_zifencei -mabi=lp64` with
`.option norvc`, then `riscv64-linux-gnu-objdump -d -M no-aliases`) confirmed
every declared base and defect word in the plan, including `00900893`,
`03400313`, `400033b7`, `0093a023`, `00038067`, `68002573`, `00000513`, and
`00400893`. Read-only inspection of the accepted packages also confirmed the
plan's citations: the frozen fixture arrays (`tests/r5/check-image.mjs:327-332`),
the 22-line `expectedConsole` and 9-entry forbidden set
(`tests/r5/check-qemu-artifacts.mjs:21-47`), 30 `be_r5_error_name()` cases
(`none` plus 29 classes), the seven-entry `scratchComponents` order
(`tests/r5/tool-lock.mjs:88-91`), the `tests/r3/tool-lock.conf` digest
`c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b`, the
`r6_authorization` producer/forbidden/assertion sites, and the existence of all
six named acceptance-pin constants.

**What does not exist and was not run.** There is no R6 implementation, so no
R6 host test, image build, image check, differential check, QEMU run, report,
or evidence bundle was or could be executed. Hardware validation and formal
verification are `NOT RUN`. No complete repository gate (`make check`) was run
for this documentation-only packet, and none should be read as validating the
target: the accepted R0-R5 acceptance state is established by its own accepted
records, not by this packet.

**Execution boundary.** The review target is the exact immutable commit
`609867fdad75279c0913022909efd65c4a838909`. The packet commit
`21cf80daa2021590378de81d7a094e14f4e5c8ca` and the later acceptance-record
commit that adds the decision above are **separate follow-up commits**; their
own `npm run docs:build`, `./be docs-check`, `scripts/check-be.sh`, and
`git diff --check` runs validate that decision-support content, not the target.
Neither follow-up changes, amends, or re-validates the target, and neither is
R6 implementation.

## 7. Recommended human review sequence

1. Confirm identity and boundaries: exact target, parent, private repository,
   no remote refs, no tags, and no `tests/r6/` tree.
2. Read the plan's decision-bearing sections first, before any table detail:
   [§ Status and decision](single-hart-runtime-r6-plan.md#status-and-decision),
   [§ Decision: no new production-like R6 surface](single-hart-runtime-r6-plan.md#decision-no-new-production-like-r6-surface),
   and [§ Authorized acceptance-pin refresh](single-hart-runtime-r6-plan.md#authorized-acceptance-pin-refresh).
3. Then review scope and safety:
   [§ Fixture catalogue](single-hart-runtime-r6-plan.md#fixture-catalogue),
   [§ Per-partition layer applicability](single-hart-runtime-r6-plan.md#per-partition-layer-applicability),
   and [§ Coverage ledger](single-hart-runtime-r6-plan.md#coverage-ledger).
4. Then review honesty of the evidence boundary:
   [§ Trust assumptions](single-hart-runtime-r6-plan.md#trust-assumptions),
   [§ Supported claims](single-hart-runtime-r6-plan.md#supported-claims),
   [§ Explicit non-claims and exclusions](single-hart-runtime-r6-plan.md#explicit-non-claims-and-exclusions),
   and [§ Review-gate checklist](single-hart-runtime-r6-plan.md#review-gate-checklist).
5. Confirm the status diff separates authorization from acceptance, and that no
   surface claims R6 implementation started.
6. If execution is desired, use an isolated detached worktree so unrelated
   local changes cannot affect results. Generated hash-named assets may churn;
   inspect source Markdown and the status diff, not asset names.

```sh
git show -s --format=fuller 609867fdad75279c0913022909efd65c4a838909
git diff --check 0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d 609867fdad75279c0913022909efd65c4a838909
git diff --name-status -M 0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d 609867fdad75279c0913022909efd65c4a838909
git diff 0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d 609867fdad75279c0913022909efd65c4a838909 -- planning/single-hart-runtime-r6-plan.md
git branch -r --contains 609867fdad75279c0913022909efd65c4a838909
git tag --contains 609867fdad75279c0913022909efd65c4a838909
git ls-tree -r --name-only 609867fdad75279c0913022909efd65c4a838909 -- tests/r6

git worktree add --detach .review-r6-plan-target 609867fdad75279c0913022909efd65c4a838909
(cd .review-r6-plan-target && npm ci && npm run docs:build && ./be docs-check && ./be status)
git worktree remove --force .review-r6-plan-target
```

## 8. Human decision checklist

The technical-judgment items below remain unchecked as review history. Only the
explicitly supplied decision is marked; automation does not answer, pre-check,
or sign for the questions, and checking them is not inferred from the decision.

### Decision A: Accept, revise, or defer the exact plan commit

- [ ] The exact target `609867fdad75279c0913022909efd65c4a838909`, its parent
  `0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d`, and the 81-path
  planning/documentation scope are acceptable.
- [ ] The plan's scope matches the master-plan R6 row (malformed input, partial
  publication, wrong binding, skipped fence, unexpected trap/event, denied
  access) and adds no runtime behavior beyond it.
- [ ] The no-production-surface decision — no `include/be/r6.h`,
  `virt/be/r6.c`, or `arch/riscv/be/r6-*` — and its four justifications are
  correct.
- [ ] The 47-entry catalogue and its static / host / dynamic / control
  partition are acceptable, finite, and sufficient for this row.
- [ ] The safe/static/dynamic partition is genuinely safe: unsafe constructions
  are quarantined before execution, dynamic fixtures stay inside immutable
  accepted G-stage roots, and QEMU is executable-gated.
- [ ] The declared single-message L6 dispositions plus mandatory L8 single-delta
  differential are a bounded declared expectation rather than a bypass of the
  accepted image checker.
- [ ] The trust assumptions (pinned toolchains, QEMU, OpenSBI, accepted R0-R5
  mechanism as the measurement instrument) and the tooling/lock/launcher
  controls are acceptable.
- [ ] Negative paths are adequately covered: 29 primary error classes with zero
  uncovered, per-host-fixture negative self-tests, layer-shift detection,
  scratch-fault prerequisites, and stage mutations for the layers with no
  catalogue fixture.
- [ ] The authorized six-constant predecessor acceptance-pin refresh, its
  ordering, and its bidirectional revert self-tests are acceptable, and no
  other predecessor byte may change.
- [ ] The `r6_package_authorization` key alongside the preserved accepted
  `r6_authorization=not-authorized` line is the right resolution of the status
  collision.
- [ ] R7 content, hardware validation, formal verification, publication, tag,
  push, and release remain excluded, and the report/retention/reproducibility
  boundary is honest.
- [x] **Decision A:** accept exact plan commit
  `609867fdad75279c0913022909efd65c4a838909` / ~~request revisions~~ /
  ~~defer~~.

### Decision B: Authorize or withhold R6 implementation start

> This decision is independent of plan acceptance. Implementation
> authorization alone does NOT accept the plan, and plan acceptance alone does
> NOT authorize implementation. For R6 the authorization was recorded first,
> under the master-plan R6 row, and the plan acceptance completed the pair.

- [x] R6 implementation work is authorized under the master-plan R6 row and may
  begin within the accepted plan's scope and constraints, per the recorded
  instructions `proceed to implement R6 exact`
  (2026-07-30T20:34:36.241+00:00) and `proceed with all r6 implementation work`
  (2026-07-30T20:36:53.931+00:00).
- [ ] OR: R6 implementation is withheld pending [reason].

Only the two decision boxes above are checked, because those decisions were
explicitly supplied by the responsible human. No signature is generated.

## 9. After the decision

Both gates are satisfied and recorded on 2026-07-30:

- **Decision A (accept plan):** exact plan commit
  `609867fdad75279c0913022909efd65c4a838909` is accepted.
- **Decision B (authorize implementation):** R6 implementation work is
  authorized under the master-plan R6 row by the two recorded proceed
  instructions, and is now bounded by the accepted plan's scope.

Bounded R6 implementation may now begin. It is expected to add its test-only
adversarial-image catalogue, harness, launcher, locks, report, and evidence
under `tests/r6/` plus the bounded root integration the plan defines, over the
byte-immutable accepted R5 target `165f4d001a2b59b582b397bdea79ec4826168fdb`,
changing no byte of `include/`, `virt/`, or `arch/` and touching only the six
enumerated predecessor acceptance-pin constants the plan authorizes. This
acceptance-record commit itself leaves `r6_implementation=not-started` and
creates no `tests/r6/` file.

### Prohibited until separate authorization

- No R6 tag, private push, public release, or change to
  `pathfinder/publication-gate.conf`.
- No R7 start; R7 remains undefined, gated, and not authorized.
- No acceptance of any future R6 implementation: it requires its own
  exact-commit review and its own separate responsible-human acceptance.
- No modification of any accepted R0-R5 byte beyond the six enumerated
  acceptance-pin constants the accepted plan authorizes.
- No hardware-validation or formal-verification claim; both remain `NOT RUN`.
- The open generated-asset byte-reproducibility finding remains unresolved;
  acceptance does not resolve it.

---

**Status (at that decision, 2026-07-30):** exact plan commit
`609867fdad75279c0913022909efd65c4a838909` is **accepted**, and R6
implementation work is **separately authorized**. R6 implementation was **not
started** and no `tests/r6/` tree existed. Accepted R5 implementation remains
exactly `165f4d001a2b59b582b397bdea79ec4826168fdb` and is unchanged by this
record. For the current state — including accepted corrected plan target
`75269f058ae578b0a76a113d6c05c0aaceeac8ec` and started, unaccepted, incomplete
local implementation — see
[Post-acceptance implementation discovery](#post-acceptance-implementation-discovery-and-accepted-plan-revision)
and the
[R6 plan revision review and acceptance record](single-hart-runtime-r6-plan-revision-review-summary.md).

**Next:** bounded R6 implementation may begin within the accepted plan scope.
R7 remains gated; hardware validation and formal verification remain `NOT RUN`;
push, tag, publication, and release remain blocked.

**Action required from you:** none for these two decisions. Both plan
acceptance and implementation authorization are recorded. A future R6
implementation, tagging, pushing, publication, and R7 all remain prohibited
without separate explicit authorization.
