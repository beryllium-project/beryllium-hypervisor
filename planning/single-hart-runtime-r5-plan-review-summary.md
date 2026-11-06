<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R5 plan review and acceptance record

> **Repository rehoming note (current-line editorial context):** This record
> preserves the packet-time former private repository identity and remote
> state. The current active private repository is
> `beryllium-project/beryllium-hypervisor`; use
> [project orientation](project-orientation.md) for current repository
> guidance.

## Decision record

Responsible-human review **accepted exact plan commit**
`fecae6b62a507bdbb93d211262197a31f5422316` on 2026-07-30, in explicit
response to the question `Do you explicitly accept bounded R5 plan commit
fecae6b62a507bdbb93d211262197a31f5422316?`. The recorded selection was:
`Accept exact R5 plan commit (Recommended)`.

Responsible-human review **separately authorized R5 implementation** under
that accepted plan. The explicit instruction, preserved verbatim and
timestamped 2026-07-30T04:33:03.944+00:00, was: `authorize r5 implementation,
proceed`.

Packet commit `dd41a7571784c6bca3d4ccf4983c04cb7c052375`
(`docs: add R5 plan review packet`) is decision support only; the accepted
plan target remains its exact parent,
`fecae6b62a507bdbb93d211262197a31f5422316`.

These decisions apply only to the exact immutable plan commit. They do not
resolve the open generated-asset byte-reproducibility finding, and they do
not authorize an R5 tag, a private push, public release, R6, R7, or any other
successor work beyond the accepted R5 plan scope. R5 implementation may now
begin under the exact scope defined in the accepted plan; it has **not**
started as of this record.

## 1. Decision summary

| Field | Required content |
| --- | --- |
| Review target | `fecae6b62a507bdbb93d211262197a31f5422316` (`docs: add bounded single-hart R5 plan`), parent `87b136bc4889a04a58c2399e4eb81f7925cba5e0` (`docs: record exact R4 acceptance`). |
| Current status | The R5 bounded plan is **accepted** at exact commit `fecae6b62a507bdbb93d211262197a31f5422316` on 2026-07-30; R5 implementation is **separately authorized** under that accepted plan but has **not started**. |
| Decision recorded | (A) Accept exact plan commit `fecae6b62a507bdbb93d211262197a31f5422316`; (B) Authorize R5 implementation under that accepted plan. |
| Successor status | R5 implementation was later completed and separately accepted at exact target `165f4d001a2b59b582b397bdea79ec4826168fdb` on 2026-07-30; that decision is recorded in [`single-hart-runtime-r5-review-summary.md`](single-hart-runtime-r5-review-summary.md) and was not inferred from these plan decisions. R6 and R7 remain gated and not authorized. |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`; the target is local, unpushed, and untagged (zero remote refs and tags contain it). Push, tag, publication, and release remain blocked. |

**Action expected:** no further plan-acceptance decision is pending for this
exact SHA. Both decisions are recorded. R5 implementation may begin under the
accepted plan scope. Any tag, push, public release, or R6 start requires
separate explicit authorization.

## 2. Deliverables

The exact parent delta contains 90 changed files: 789 insertions and 309
deletions. It has eight non-generated source paths and 82 generated status
entries. There is no R5 implementation/header/assembly/functional-test/
wrapper/Make/evidence/publication-gate change; the sole changed test path is
the documentation browser-render inventory.

| Deliverable | Paths | Purpose | Trust / privilege boundary | Primary human question |
| --- | --- | --- | --- | --- |
| Bounded R5 plan | `planning/single-hart-runtime-r5-plan.md` | Freeze the proposed management→protected→management checked-switch contract, future source split, and evidence boundary. | Plan only; it creates no privileged implementation or executable R5 surface. | Is the narrow scenario, ordering, and terminal behavior sufficient and correctly bounded? |
| Status, entry points, and render inventory | `.github/copilot-instructions.md`, `README.md`, `planning/README.md`, `planning/HANDOFF.md`, `planning/roadmap.md`, `planning/.vitepress/config.mts`, `pathfinder/tests/check-docs-render.mjs` | Make the draft status and plan visible in maintained navigation and browser coverage. | Markdown is authoritative; the browser inventory exercises documentation, not R5 behavior. | Do all status surfaces say plan-only, not accepted, and no implementation authorization? |
| Generated documentation | `docs/html/**`, `pathfinder/docs/html/**` below | Render the changed authoritative Markdown and navigation. | Derivative, non-normative output; hash-named asset byte reproducibility remains open. | Are rendering and links functional without treating generated-asset churn as resolved? |

### Exact changed-file inventory

Non-generated source paths:

```text
.github/copilot-instructions.md
README.md
pathfinder/tests/check-docs-render.mjs
planning/.vitepress/config.mts
planning/HANDOFF.md
planning/README.md
planning/roadmap.md
planning/single-hart-runtime-r5-plan.md
```

Generated status entries under `docs/html/` (renames are `old -> new`):

```text
docs/html/404.html
docs/html/HANDOFF.html
docs/html/architecture-model-0.1-evidence.html
docs/html/architecture-model-0.1.html
docs/html/architecture-model-0.2-evidence.html
docs/html/architecture-model-0.2.html
docs/html/arm64-pathfinder-plan.html
docs/html/assets/HANDOFF.md.Cbz-MBCh.js -> docs/html/assets/HANDOFF.md.eMADngJ7.js
docs/html/assets/HANDOFF.md.Cbz-MBCh.lean.js -> docs/html/assets/HANDOFF.md.eMADngJ7.lean.js
pathfinder/docs/html/assets/app.Bu3JrJEH.js -> docs/html/assets/app.Bg-uvQ1l.js
docs/html/assets/chunks/@localSearchIndexroot.CHAJuByN.js
docs/html/assets/chunks/@localSearchIndexroot.DM8Adh9I.js
docs/html/assets/chunks/VPLocalSearchBox.2_X0hXJO.js -> docs/html/assets/chunks/VPLocalSearchBox.BlqUdFJW.js
docs/html/assets/chunks/theme.BuYd22cV.js -> docs/html/assets/chunks/theme.DnjopixK.js
docs/html/assets/index.md.BGyGpFjP.js
docs/html/assets/index.md.CVn36TDa.js
docs/html/assets/index.md.BGyGpFjP.lean.js -> docs/html/assets/index.md.CVn36TDa.lean.js
docs/html/assets/roadmap.md.D53PGIK-.js
docs/html/assets/roadmap.md.O4sZY6ux.lean.js -> docs/html/assets/roadmap.md.D53PGIK-.lean.js
docs/html/assets/roadmap.md.O4sZY6ux.js
docs/html/assets/single-hart-runtime-r5-plan.md.TajbecYc.js
docs/html/assets/single-hart-runtime-r5-plan.md.TajbecYc.lean.js
docs/html/beryllium-hypervisor-notes.html
docs/html/capability-policy-architecture.html
docs/html/cheri-alignment.html
docs/html/hashmap.json
docs/html/implementation-plan.html
docs/html/index.html
docs/html/isolation-engine-policy-research.html
docs/html/minimal-pathfinder-evidence.html
docs/html/minimal-pathfinder-plan.html
docs/html/open-tooling.html
docs/html/pathfinder-comparison.html
docs/html/pathfinder-evidence.html
docs/html/pathfinder-plan.html
docs/html/research-provenance.html
docs/html/research-synthesis.html
docs/html/riscv-security-hardware.html
docs/html/roadmap.html
docs/html/session-analysis-cap-te-cheri-2026-07-20.html
docs/html/session-analysis-isolation-engine-2026-07-20.html
docs/html/session-analysis-te-vbs-2026-07-20.html
docs/html/session-analysis-transcripts-2026-07-20.html
docs/html/sidebar-dynamic-authority-caches.html
docs/html/sidebar-high-assurance-standards.html
docs/html/sidebar-lvbs-equivalence.html
docs/html/sidebar-minimal-vs-runtimes.html
docs/html/sidebar-rust-vs-components.html
docs/html/single-hart-runtime-plan.html
docs/html/single-hart-runtime-r0-freeze.html
docs/html/single-hart-runtime-r1-evidence.html
docs/html/single-hart-runtime-r1-review-summary.html
docs/html/single-hart-runtime-r2-evidence.html
docs/html/single-hart-runtime-r2-plan-review-summary.html
docs/html/single-hart-runtime-r2-plan.html
docs/html/single-hart-runtime-r2-review-summary.html
docs/html/single-hart-runtime-r3-evidence.html
docs/html/single-hart-runtime-r3-review-summary.html
docs/html/single-hart-runtime-r4-evidence.html
docs/html/single-hart-runtime-r4-review-summary.html
docs/html/single-hart-runtime-r5-plan.html
docs/html/supervisory-security-policy.html
docs/html/type-enforcement-pathfinder-evidence.html
docs/html/type-enforcement-pathfinder-plan.html
```

Generated status entries under `pathfinder/docs/html/`:

```text
pathfinder/docs/html/404.html
pathfinder/docs/html/architecture.html
docs/html/assets/app.DSpVz9Uc.js -> pathfinder/docs/html/assets/app.BIGzEqU7.js
pathfinder/docs/html/assets/chunks/@localSearchIndexroot.CMKEtpSE.js
pathfinder/docs/html/assets/chunks/@localSearchIndexroot.bpO0TwoI.js
pathfinder/docs/html/assets/chunks/VPLocalSearchBox.b3DCd5iO.js -> pathfinder/docs/html/assets/chunks/VPLocalSearchBox.C8jgBuNh.js
pathfinder/docs/html/assets/chunks/theme.Cpx74AMQ.js -> pathfinder/docs/html/assets/chunks/theme.CKjFYZQH.js
pathfinder/docs/html/code-tour.html
pathfinder/docs/html/concepts.html
pathfinder/docs/html/engineering-sop.html
pathfinder/docs/html/evaluation.html
pathfinder/docs/html/index.html
pathfinder/docs/html/policy-and-publication.html
pathfinder/docs/html/policy-models.html
pathfinder/docs/html/quickstart.html
pathfinder/docs/html/references.html
pathfinder/docs/html/security-and-limits.html
pathfinder/docs/html/verification.html
```

Reproduce this inventory without interpretation:

```sh
git diff --name-status -M 87b136bc4889a04a58c2399e4eb81f7925cba5e0 fecae6b62a507bdbb93d211262197a31f5422316
git diff --numstat 87b136bc4889a04a58c2399e4eb81f7925cba5e0 fecae6b62a507bdbb93d211262197a31f5422316
```

## 3. Claim boundary

The target supports only these plan-level statements: it defines a future
fixed one-hart QEMU/OpenSBI management→protected→management transaction,
states the proposed fixture/order/evidence contracts, and keeps planned R5
commands under schema `be-r5-checked-switch-v1` explicitly **NOT IMPLEMENTED
/ NOT RUN**.

Any future R5 claim would trust pinned OpenSBI, GCC, Clang, GNU ld, lld,
QEMU, assembler/disassembler behavior, and inspected-to-executed assembly
correspondence. Hardware and formal proof/refinement are `NOT RUN`. This
target supplies no R5 implementation, host unit test, semantic checker,
emulation result, proof, or hardware validation.

It explicitly does not implement or claim Linux, service, guest-SBI, device,
DMA, interrupt, timer, multicore, policy, CHERI, TE, arbitrary-guest
isolation, R6 adversarial execution, R7 exact-byte proof, publication, or
release. The accepted R4 implementation remains only
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52`; its acceptance-record follow-up
parent `87b136bc4889a04a58c2399e4eb81f7925cba5e0` is not implementation.

## 4. Load-bearing plan invariants

| Invariant | Plan reference | Future evidence boundary |
| --- | --- | --- |
| The current image re-executes the accepted R4 management prelude through R4 `COMPLETE` with `sepc=0x40010034`; it never imports earlier-image runtime state. | [§ Frozen scenario and bindings / Management-to-protected boundary](single-hart-runtime-r5-plan.md#management-to-protected-boundary), [§ State, frame, and failure contract](single-hart-runtime-r5-plan.md#state-frame-and-failure-contract) | Future image/QEMU evidence must establish the exact in-image prelude and only then the R4→R5 seam. |
| The only run is management→protected→management; protected uses the fixed binding and the unchanged 320-byte R4 frame. | [§ Frozen scenario and bindings](single-hart-runtime-r5-plan.md#frozen-scenario-and-bindings), [§ State, frame, and failure contract](single-hart-runtime-r5-plan.md#state-frame-and-failure-contract) | Future host/image/QEMU checks must reject guest-selected binding, frame, page, or trusted-stack selection. |
| Protected slots are fixed from `0x40011000` through `0x40011034`: load denial at `0x40011014` is cause 21; shared-store denial at `0x40011024` is cause 23 and candidate 68 leaves backing 34; event at `0x40011030` is cause 10; restored management event is at `0x40010038`. | [§ Protected fixture](single-hart-runtime-r5-plan.md#protected-fixture), [§ Protected-to-management and completion boundary](single-hart-runtime-r5-plan.md#protected-to-management-and-completion-boundary) | Future semantic image checks and QEMU traces must retain exact PCs, causes, values, three same-domain resumes, and final observations. |
| One-way phases include explicit expected protected switch-event and post-fence/pre-publication states; malformed/partial/duplicate transitions are terminal. | [§ Architecture-neutral phase machine](single-hart-runtime-r5-plan.md#architecture-neutral-phase-machine) | R5 unit checks cover phase/binding/root/readback/frame/publication invariants; R6, not R5, owns broad compiled adversarial fixtures. |
| Each cross-switch validates source, saves a frame, forms pending, writes target HGATP, fences, reads back, resets/prepares target, publishes, then runs a no-call GPR/SRET tail. Roots/PTEs stay immutable. | [§ Exact switch transaction](single-hart-runtime-r5-plan.md#exact-switch-transaction), [§ Planned source and assembly boundary](single-hart-runtime-r5-plan.md#planned-source-and-assembly-boundary) | Future image/QEMU evidence must show exactly two R5 cross-switch HGATP writes/fences/readbacks after initial management installation, target publication before guest execution, and no rollback. |
| There are exactly three VS entries, three same-domain fault resumes, and six planned QEMU runs (three per compiler). | [§ Planned evidence and separation from R6](single-hart-runtime-r5-plan.md#planned-evidence-and-separation-from-r6) | These are planned emulation requirements only; no R5 QEMU run exists at this target. |

## 5. Review history and resolved findings

Five parallel analyses covered scope, switch design, validation, cross-plan
consistency, and ratified ISA semantics; none found an architecture blocker.
Adversarial review found an initially blocking ambiguity between importing
prior R4 execution and re-executing management. The plan now requires the
current-image R4 prelude, specifies the import seam at R4 `COMPLETE`, and
freezes exactly three VS entries. Phase names were corrected to identify the
expected protected switch event and post-fence/pre-publication states. Every
protected slot and denied-store candidate 68 was frozen. Final review found
no remaining substantive defect, and the precommit audit found planning-only
scope.

**Open finding:** generated hash-named asset byte reproducibility remains
unresolved. Functional documentation and browser checks pass; this packet
does not call the byte-reproducibility finding resolved.

## 6. Exact-target validation

On 2026-07-30, an isolated detached worktree at
`fecae6b62a507bdbb93d211262197a31f5422316` passed:

```sh
git diff --check
./be docs-check
tests/r1/check-acceptance.sh --require
tests/r2/check-acceptance.sh --require
tests/r3/check-acceptance.sh --require
tests/r4/check-acceptance.sh --require
./scripts/check-be.sh
./be status
```

An independent transient systemd user service ran `./be check` from that
detached target and passed in 8m19s. That complete repository gate validates
existing R0–R4 components and repository gates; it does **not** execute or
validate R5 implementation, because none exists. The detached inspection
also confirmed no R5 implementation/header/assembly/tests/wrapper/Make/
evidence artifacts. Generated-asset churn was observed, the worktree was
removed, and the main target remained clean.

## 7. Recommended human review sequence

1. Confirm identity, private state, target parent, and absence of remote refs
   or tags.
2. Inspect the eight authoritative source paths and the plan's scope,
   frozen fixture, phase, transaction, and non-claim sections before looking
   at derivative HTML.
3. Review the R4 boundary: accepted implementation is
   `0783dfc6557453fbac0da93a5364f2e6e2cb1f52`; parent
   `87b136bc4889a04a58c2399e4eb81f7925cba5e0` is an acceptance record, not
   implementation.
4. Compare future R5 unit invariants with R6 adversarial fixtures and R7
   exact-byte proof so planned evidence is not overstated.
5. If execution is desired, use an isolated detached worktree. Generated
   hash-named assets may churn; inspect source Markdown and the status diff,
   not asset names alone.

```sh
git show -s --format=fuller fecae6b62a507bdbb93d211262197a31f5422316
git diff --check 87b136bc4889a04a58c2399e4eb81f7925cba5e0 fecae6b62a507bdbb93d211262197a31f5422316
git diff --name-status -M 87b136bc4889a04a58c2399e4eb81f7925cba5e0 fecae6b62a507bdbb93d211262197a31f5422316
git branch -r --contains fecae6b62a507bdbb93d211262197a31f5422316
git tag --contains fecae6b62a507bdbb93d211262197a31f5422316
git worktree add --detach .review-r5-target fecae6b62a507bdbb93d211262197a31f5422316
(cd .review-r5-target && ./be docs-check && ./be status)
git worktree remove .review-r5-target
```

## 8. Human decision checklist

### Decision A: Accept, revise, or defer the exact plan commit

- [ ] The exact target, parent, and 90-path planning/documentation scope are
  acceptable.
- [ ] The current-image R4 prelude, exact bindings/fixtures, three VS entries,
  phase order, immutable roots/PTEs, and terminal partial transitions are
  acceptable.
- [ ] The pinned tool, firmware, assembly, and QEMU trust assumptions are
  acceptable for this future bounded claim.
- [ ] The R5 unit-invariant, R6 adversarial-fixture, and R7 exact-byte-proof
  evidence split is explicit and acceptable.
- [ ] Hardware, proof, Linux, service, device, multicore, policy, publication,
  release, and all implementation work remain excluded.
- [x] **Decision A:** accept exact plan commit
  `fecae6b62a507bdbb93d211262197a31f5422316` / ~~request revisions~~ /
  ~~defer~~.

### Decision B: Authorize or withhold R5 implementation start

> This decision is independent of plan acceptance. Plan acceptance alone does
> NOT authorize implementation.

- [x] R5 implementation may begin under the accepted plan's scope and
  constraints.
- [ ] OR: R5 implementation is withheld pending [reason].

Only the two decision boxes above are checked because those decisions were
explicitly supplied by the responsible human. The technical-judgment
checklist items remain unchecked as review history; no signature is
generated, and checking them is not inferred from either decision.

## 9. After the decision

Both gates are satisfied and recorded on 2026-07-30:

- **Decision A (accept plan):** exact plan commit
  `fecae6b62a507bdbb93d211262197a31f5422316` is accepted.
- **Decision B (authorize implementation):** R5 implementation is authorized
  under the exact scope defined in the accepted plan.

R5 implementation may now begin. It is expected to add its checked
management→protected→management switch-transaction mechanism and RISC-V
boundary under the paths the plan defines, composing over the exact accepted
R4 state (`0783dfc6557453fbac0da93a5364f2e6e2cb1f52`) without modifying any
R0-R4 accepted file.

### Prohibited until separate authorization

- No R5 tag, private push, or public release.
- No R6 or R7 start (adversarial fixtures, exact-byte proof).
- No modification of any R0-R4 accepted file.
- The open generated-asset byte-reproducibility finding remains unresolved;
  acceptance does not resolve it.

---

**Status:** exact plan commit `fecae6b62a507bdbb93d211262197a31f5422316` is
accepted. R5 implementation is separately authorized under the accepted plan
scope, and it was later separately accepted at exact target
`165f4d001a2b59b582b397bdea79ec4826168fdb` on 2026-07-30. The accepted R4
target `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` remains unchanged.

**Next:** keep R6 gated. No tag, push, or public release follows from these
plan decisions or from the separate R5 implementation acceptance.

**Action required from you:** none for these two decisions. Both plan
acceptance and implementation authorization are recorded. Tagging, pushing,
publication, and R6 remain prohibited without separate explicit
authorization.
