<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# S1: Helium-to-Beryllium synthesis

## Decision record

The responsible human accepted this document at exact commit
`fd670dcd54ff4f2c66349d377be914698b9dda3b` (parent
`ef50c005882f1a3698442943158ca3435ee3a1e9`) on 2026-10-18. The instruction,
given in reply to the
[revision review summary](s1-te-trigger-revision-review-summary.md)'s request
for three ordered decisions, was `I accept RP-1 RP-2 RP-3`; the packet maps
RP-1 to this commit, RP-2 to Model 0.1 plan revision M01-A at `95ef0f6c`,
and RP-3 to the revised S2 definition at `1ac7080f`, all accepted by that
instruction in that order.

- **Scope:** acceptance covers exactly the document text at that commit.
  Everything after this section is the synthesis as accepted; only this
  section and the acceptance fields in the status record below were added
  afterwards. The first draft `0fbca0fd` stays superseded and unaccepted.
- **What it decides:** S1, the first step of the planned sequence, is
  complete: its classifications, including the specification role adopted
  in row H59, are accepted planning input to S2 and S3, which may revisit
  any row with new evidence.
- **Not decided:** S2 and S3 stay unauthorized and need their own
  direction; no runtime mechanism is selected; no Helium result transfers;
  no accepted R0-R7 or B0-B7 target changes; nothing is pushed.

## Status

Proposed for responsible-human review; not accepted. This is the revised S1
synthesis: work package RP-1 of the accepted
[S1 and TE-trigger revision plan](s1-te-trigger-revision-plan.md) (exact
commit `07541c59`, accepted 2026-10-18), produced under the 2026-10-17
critique recorded in the accepted
[project review](project-review-2026-10-17.md) (Part 1, S1-F1 to S1-F7)
and the responsible human's `revise-adopt` direction. It replaces the first
S1 draft at `0fbca0fd`, which is superseded and unaccepted. The responsible
human authorized S1 on 2026-10-16 with the instruction
`authorize S1, proceed`. S1 is the first step of the
[planned sequence](roadmap.md#planned-sequence): documentation only, with
one accepted planning document as its exit. This is that document. It
authorizes nothing. S2, S3, any implementation, any board run, any push, and
any publication each still need their own direction.

What changed from `0fbca0fd`: the argument from E03 that the TE PoC scenario
"does not show that the TE trigger fires" is removed everywhere it appeared,
because E03 is evidence about enforcement, not about how the system's
security properties are specified; a new row H59 adopts a central,
declarative policy in the Type Enforcement family as that specification;
H02 moves to Adapt, H08 is reworded as the runtime TE check, H10 moves from
Reject to Defer, and H56 no longer carries "TE should not lead the core"
forward as a lesson; the practice-confirmation rows are condensed into one
table; and the purpose, non-claims, hand-offs, and counts follow.

## Purpose and boundary

S1 classifies each relevant Helium lesson as **adopt**, **adapt**,
**reject**, or **defer**. Each is judged against the K3 bring-up evidence
from B0 to B7 and against Beryllium's recorded decisions, and the result is
handed to S2 (security model v1) and S3 (MVP plan). S1 exists because the
[post-pathfinder comparison](pathfinder-comparison.md) predates both the
Helium fork and all K3 evidence.

S1 recommends one thing beyond classification: that a central, declarative
policy in the Type Enforcement family be the specification against which
the system's security properties are stated, analyzed, and verified, with
enforcement derived from it (H59). That is a specification role. It selects
no runtime mechanism: whether a policy decision is also consulted on any
access path beyond the derived mappings (the runtime TE check), and whether
software capabilities are needed, stay with S2's triggers.

S1 does not:

- select a runtime mechanism: a runtime TE check, software capabilities,
  CHERI, a protected service, an SBI or firmware boundary, a verification
  method, or an MVP scope;
- evaluate the capability trigger or the runtime-check trigger, which S2
  owns under the wording that plan revision M01-A (RP-2) proposes;
- transfer any Helium result to Beryllium: no test, QEMU run, CBMC result,
  review disposition, or release or gate status;
- infer any Helium review, approval, publication, or release status from a
  Helium ref, tag, commit subject, or in-tree gate file; or
- change any accepted R0-R7 or B0-B7 byte, plan, or record, or any other
  planning document.

Accepting this document would accept its classifications, including the
specification role in H59, as planning input to S2 and S3 only. S2 and S3
may revisit any row with new evidence.

## Inputs

| Input | Exact identity | Use |
| --- | --- | --- |
| Beryllium base | development branch `beryllium/single-hart-runtime-r0` at `56e36ae11e47bb08416a44c5647aecd304fd4902` | B0-B7 records and recorded decisions |
| Post-pathfinder comparison | [`pathfinder-comparison.md`](pathfinder-comparison.md) at the base | the five variants, the cost findings, the precedents, and the selected direction |
| TE PoC evidence | [`type-enforcement-pathfinder-evidence.md`](type-enforcement-pathfinder-evidence.md) and the [TE plan](type-enforcement-pathfinder-plan.md) at the base | the fixed TE scenario and its limits |
| Founding policy expectations | the [implementation plan](implementation-plan.md) (L401, L416-L417, L734, L740, L931-L940 at the base) and the [capability policy research](capability-policy-architecture.md) (L36-L44, L240) | the specification role that H59 adopts |
| The critique | the accepted [project review](project-review-2026-10-17.md) at `480dab72` and the accepted [revision plan](s1-te-trigger-revision-plan.md) at `07541c59` | S1-F1 to S1-F7 and the RP-1 change list |
| Helium | `../helium-te-poc` at `1c9e52693abe0072ac9b8ce4e0a3ecb5f8bb9489`, read as evidence only | Helium source, documentation, review and remediation records, and its bounded CBMC work |
| K3 bring-up evidence | the B0-B7 plans, the result review and acceptance records, and `bringup/k3-b*/README.md` at the base | the evidence each row is judged against: E01-E12 below |

### Helium pin

The plan asks for `../helium-te-poc` read at one exact commit. S1 reads
`1c9e526`, the commit at Helium's `v0.6.0` tag and `public/main`, with the
subject `release: approve final Helium snapshot` (2026-09-09).

- Beryllium's records name Helium ref `for-review` as the current
  source-of-truth ref ([handoff](HANDOFF.md#helium-source-of-truth-boundary),
  [orientation](project-orientation.md)), and Helium's own handoff says new
  development continues there. That ref is at
  `f928aac5979b6166f3f68a76a9acf1fc916161d8`: common base `1ab289c` plus two
  commits that change only `HANDOFF.md`.
- `1c9e526` is a separate, 60-commit line from the same base. Compared with
  `f928aac5`, it adds 214 files, modifies 86, and renames 5; the only files
  it removes are 21 generated HTML assets. Its additions include eight tiers
  of bounded CBMC checks, a source refactor, a finalization ledger, and
  `docs/fv-pathfinder-lessons.md`, which carries inputs addressed to "the
  next Be stage".
- S1 reads the pin as content only. Helium's own documents at that commit
  disagree about its status: `publication-gate.conf` records an approval
  while `HANDOFF.md` still describes the gate as blocked, and some pages list
  CBMC coverage only through Tier 6. S1 relies on neither.

[Q1](#open-questions-and-defaults) records this choice and its alternative.

## Classification rubric

Each row classifies one Helium element (a mechanism, design rule, practice,
artifact, or decision) together with the lesson Helium drew from it.

- **Adopt:** carry the element into S2 and S3 as stated. The B-series
  evidence supports it or does not bear on it, and no recorded decision
  conflicts. Many adopted rows confirm a practice Beryllium already follows.
- **Adapt:** keep the element's intent but change its form, because the
  B-series evidence or a recorded decision differs from Helium's fixed QEMU
  setting. The row states the change.
- **Reject:** do not carry the element forward. The B-series has superseded
  it, a recorded decision excludes it, or it was Helium-only scaffolding.
- **Defer:** a named later step decides, at a stated trigger.

"He:" marks a path in `../helium-te-poc` at the pin. E-numbers refer to the
evidence table below.

## K3 bring-up evidence

Every board result is diagnostic bring-up evidence for one COM260 board,
firmware, and Fedora kernel. None is hardware validation, qualification, or
formal verification. QEMU results are emulation, not K3 evidence.

| ID | Evidence | Record | Class |
| --- | --- | --- | --- |
| E01 | B0 entered HS on K3 through Linux `kexec_load`, above OpenSBI 1.6 (SBI 2.0), with H active. SRST shutdown halts the board without powering it off, so a human reset follows every run. | [B0](k3-b0-result-review-summary.md) | COM260, 3 of 3 |
| E02 | B1 ported accepted R3 and R4 through a generator whose counted substitution table re-derives the port byte for byte. It showed the first VS entry, a G-stage-denied load, and an `ecall` exit. A handoff quiesce was needed because Sstc left a supervisor timer interrupt pending. | [B1](k3-b1-result-review-summary.md) | COM260, 3 of 3 |
| E03 | B2 ran the accepted R5 checked switch: `hgatp` write, local `hfence.gvma`, readback. The protected domain's load of a management-private page faulted (cause 21), and its store to the shared page, mapped read-only, faulted (cause 23): "The denied store did not land." The record states that "enforcement is ownership and an explicit read-only channel". | [B2](k3-b2-result-review-summary.md) | COM260, 4 of 4 (3 GCC, 1 Clang) |
| E04 | B3 booted the B2 image through U-Boot `booti` and a small shim, loaded RAM-only over YMODEM. This BSP stops autoboot only on `s`. | [B3](k3-b3-result-review-summary.md) | COM260, 4 of 4 |
| E05 | B4 re-derived R6 (47 entries, 64 traced QEMU runs) and R7 (the bounded exact-byte proof) for the K3 images instead of transferring them. It found two defects in accepted tools, which the accepted-tool fixes repaired with 187 unit cases; audit findings S5-S8 and S10 stay open. | [B4](k3-b4-result-review-summary.md), [tool fixes](accepted-tool-fixes-review-summary.md) | host, QEMU, Rocq; board not run |
| E06 | B5 ran the first real guest, with a B5-only guest SBI subset (Base, DBCN console, TIME through Sstc `vstimecmp`, and SRST), and delivered a VS timer interrupt to it. Its `hstatus` sets `VTW` and `VTVM` and clears `VTSR`. Its seven negative variants ran in QEMU only. | [B5](k3-b5-result-review-summary.md) | COM260, 4 of 4 (U-Boot) |
| E07 | B6 ran an unmodified Linux `v7.2` uniprocessor guest under a B6-owned G-stage over 64 MiB, built and independently re-walked before install, with a device tree that names no device; its `hstatus` clears all three trap bits. `hedeleg` is WARL on K3: `0xb15d` reads back as `0xb15c`. A fail-closed readback stopped the first run, and the `fix-warl` direction resolved it. | [B6](k3-b6-result-review-summary.md) | COM260, 5 of 5 (4 kexec, 1 U-Boot) |
| E08 | B7 ran two Linux guests on hart 0, each with its own 64 MiB window, G-stage root, and VMID (1 and 2). An independent walker re-derives each window before `hgatp` changes, and a pair check refuses shared pages, overlapping windows, and equal VMIDs or roots. Per-guest vCPU state is saved and restored, with 11 CSRs read back. The monitor switches round-robin on a trapped `wfi` (`hstatus.VTW`) and on a 10 ms HS Sstc slice. Every switch goes through the accepted install function with `hfence.gvma` and readback, and none runs `hfence.vvma`. All runs gave identical counts. | [B7](k3-b7-result-review-summary.md) | COM260, 4 of 4 (3 GCC, 1 Clang) |
| E09 | Board procedure and claim wording: RAM-only loading, output-only serial capture, human resets, sanitized retained records with a SHA-256 manifest, and the fixed wording "diagnostic bring-up evidence for one board". | [roadmap](roadmap.md#gates-and-boundaries), [B7 plan](k3-b7-plan.md) | procedure |
| E10 | Not exercised on K3: shared memory or channels between Linux guests; any denial or fault-injection test between them, since B7's isolation is "by construction only"; a VMID-blind TLB case, which "no test isolates"; devices, IOMMU, IOPMP, or DMA; more than one hart; guest console input; guest FP or vector state; and measured launch. | [B7 plan](k3-b7-plan.md), [B7](k3-b7-result-review-summary.md) | gap |
| E11 | The B5-B7 monitor layers have no proof. Bring-up builds use unpinned workstation tools. `bringup/` sits outside the root build and `./be`. R4's 3 s QEMU budget fails on slow hosts. | [roadmap](roadmap.md#open-engineering-risks) | gap |
| E12 | Never recorded: the `htval` value K3 reports on a guest-page fault (R5 accepts zero or the exact address), K3's `htinst`, and per-event costs. | [B2](k3-b2-result-review-summary.md), [B7](k3-b7-result-review-summary.md) | gap |

## Recorded decisions that bound the classification

| Decision | Status | Record |
| --- | --- | --- |
| A small RISC-V HS isolation engine; Linux, the VMM, policy authoring, I/O, and rich services in untrusted VS domains | accepted | [comparison](pathfinder-comparison.md), [Model 0.1](architecture-model-0.1.md) |
| Ownership plus explicit channels as the baseline; capabilities and TE each only when their trigger fires; if both fire, `allow = capability_valid_and_sufficient AND mandatory_policy_allows`, and TE never mints authority. The TE-trigger text is under narrow revision as plan revision M01-A (RP-2 of the accepted revision plan), to separate TE as specification from TE as a runtime check; the Rocq model and the accepted target are untouched | accepted; trigger text under revision | [Model 0.1](architecture-model-0.1.md), [revision plan](s1-te-trigger-revision-plan.md) |
| A policy-neutral core seam: proposal, canonical validation, sealed state, derived enforcement; no policy callback, server, or framework | accepted | [Model 0.2](architecture-model-0.2.md) |
| Restricted GNU C accepted by GCC and Clang, with a thin platform and assembly boundary; Rust outside the initial core | recorded | [implementation plan](implementation-plan.md) |
| Rocq primary and Isabelle selective; Sail for the behavior it supports, plus a bounded Rocq H model; Cerberus as the long-term C semantics reference; the C-refinement verifier still open | recorded | [implementation plan](implementation-plan.md), [open tooling](open-tooling.md) |
| Fully open normative tooling; pinned GCC and Clang trusted early; open source-to-binary correspondence by the assurance release | recorded | [open tooling](open-tooling.md) |
| Device Tree only as an offline input; a bounded platform descriptor plus a capDL-inspired canonical security manifest | recorded | [implementation plan](implementation-plan.md) |
| Single hart first, then static CPU ownership | recorded | [implementation plan](implementation-plan.md) |
| The SBI and firmware boundary and the VS control-plane shape deferred to a later plan | recorded | [implementation plan](implementation-plan.md) |
| No Helium, Model, R-series, or B-series result transfers; TE unselected; no certification claim | recorded | [glossary](glossary.md), [TE evidence](type-enforcement-pathfinder-evidence.md) |
| Generated documentation at milestones; public release only through a new clean repository; AI tools never author, sign, review, or approve | recorded | [planning README](README.md), `LLM_POLICY_ALIGNMENT.md` |
| The sequence S1, S2, S3; the first MVP milestone is expected to be the Helium TE PoC scenario on two Linux guests, after S2, and reproducing that scenario does not select TE | accepted (step 3) | [roadmap](roadmap.md#planned-sequence), [implementation plan](implementation-plan.md) |

## Classification

### Direction and authority

| ID | Helium element and lesson | Class | Basis | Hand-off |
| --- | --- | --- | --- | --- |
| H01 | A small HS monitor, with Linux and rich services in untrusted VS domains: the selected direction | Adopt | Already accepted. E07 and E08 run unmodified Linux as an untrusted VS payload under a small monitor on K3 | S2: TCB and objects |
| H02 | Ownership plus explicit channels as the baseline; capabilities and TE each behind a falsifiable trigger; the composition rule (comparison, "Authority sequence") | Adapt | Keep ownership plus explicit channels as the enforcement baseline and keep the composition rule, both already accepted. E03 shows on K3 both denials of the TE PoC scenario, a cross-private load and a store to a read-only shared page, expressed as mappings derived under ownership and an explicit read-only channel; that is evidence about enforcement, not about how the properties are specified. The change: the TE trigger is being revised by plan revision M01-A (RP-2) to separate TE as specification, which H59 adopts and which is not trigger-gated, from TE as a runtime check, which stays behind the trigger | S2: evaluate the capability trigger and the runtime-check trigger under the M01-A wording; produce the specification per H59 |
| H03 | Identifiers are not authority: types, enums, guest-physical addresses, and VMIDs name things, and only the sealed state and the installed G-stage leaves grant access (He: `docs/concepts.md`, "Identifiers and authority") | Adopt | CHERI alignment; E08's VMIDs are tags, not authority | S2: object model |
| H04 | One fixed policy linked into the image, with no runtime dispatch, parser, plugin, bytecode, or guest-selected callback (He: `docs/policy-models.md`) | Adopt | Matches the Model 0.2 seam, which has no policy callback or server | S2: manifest semantics |
| H05 | Initialize, assign, seal, derive the roots, and verify them before the first guest entry; any labeling error stops the run before VS (He: `docs/architecture.md`, "Boot and initialization") | Adapt | Beryllium seals canonical ownership and channel state (R1), not TE labels, and derives and independently re-walks its roots before install (R2, R3, E07). Helium's seal exists only at its API: other HS C code can still write the sealed state | S2: state what protects the sealed state inside the TCB |
| H06 | Policy gates exposure but cannot create a mapping, and each derived PTE bit is checked against the authority that produced it. Helium handed forward two questions: permission aggregation (POL-FIN-003: must one rule cover a request, or are matches unioned?) and authority without a mapping (DOC-FIN-004: the policy-only `open` permission) (He: `docs/fv-pathfinder-lessons.md`, `docs/finalization-ledger.md`) | Adapt | Beryllium's form is roots derived from authority, with an independent re-walk (R2, E07, E08). Enforcement is the derived G-stage, not a per-access policy lookup, as Helium also notes for itself (He: `docs/faq.md`). Overlapping grants can arise with channels too. Both questions are questions about the policy specification (H59), not about the mappings | S2: state in the policy specification how overlapping grants combine and whether any authority exists without a mapping |
| H07 | A finer type has security meaning only when policy gives it different authority (POL-FIN-001). Helium records that the responsible human accepted this on 2026-09-08 as input to "the next Be stage" (He: `docs/fv-pathfinder-lessons.md`) | Defer | Each B7 guest has one window with no role split (E08). The question is one the policy specification (H59) answers: type granularity follows from which distinctions the policy must express | S2: whether resource roles need distinct types or authority in the specification |
| H08 | The fixed TE mechanism as a runtime check: labels invalid until assigned, a sealed complete set, exact source/target/class keys consulted on an access path, and default deny (He: `src/te.c`; TE evidence) | Defer | A runtime TE check is a policy decision consulted on an access path beyond the derived mappings. It stays behind the trigger under the M01-A wording; E03 is not a test of that trigger. If it fires, the lifecycle costs Helium names (relabeling, updates, caching, revocation, and proof composition) belong in the cost. Helium's label and sealing discipline is also input to the specification that H59 adopts | S2: the runtime-check trigger |
| H09 | Software capabilities (29 lines over ownership, adding attenuation and derivation) and capability plus flow (43 lines) from the minimal variant (comparison, "Cost separation") | Defer | Trigger-gated; no B-series milestone needed delegation or revocation | S2: capability trigger |
| H10 | Helium's six-rule linear scan as a representation for policy lookup, dispatch, decision caching, or dynamic update (He: `docs/fv-pathfinder-lessons.md`) | Defer | Do not transfer Helium's representation: Helium itself says it "does not select a policy representation for Be". Policy compilation to the canonical manifest, lookup, and the analyses the policy proof targets name belong to S2 with the specification (H59); dynamic update and decision caching stay conditional on the runtime-check trigger | S2: compilation and analysis of the specification; lookup where a runtime check is selected; selector authority, generations, invalidation, revocation, and rollback only if dynamic update is selected, designed from scratch |
| H59 | TE as Helium defines it: "a centrally administered, declarative access-control model in which subjects and objects receive security types. Policy authors declare which permissions a source type may use on a target type for a particular object class; subjects do not grant themselves access" (He: `docs/faq.md`), together with Helium's questions for "the next Be stage" (H06, H07), which are questions about such a policy | Adopt | A central, declarative policy in the Type Enforcement family is the specification against which the system's security properties are stated, analyzed, and verified, with enforcement derived from it: the canonical manifest is checked against the policy at validation, and the derived roots follow from the manifest. The implementation plan expects exactly this: a static policy that is "deterministic, analyzable, measurable, and attestable" (L740), FLASK as "the key policy/mechanism precedent" (L734), the policy proof targets (L931-L940), and a pipeline from policy source to "the Rocq configuration used to instantiate integrity and noninterference theorems" (L401, L416-L417). The research inputs distinguish an extensional record of existing authority from an intensional, system-wide policy ([capability policy](capability-policy-architecture.md) L36-L44) and note that seL4 proves its properties relative to configured authority (L240). A sealed manifest of grants alone is extensional and trusts its author by definition; once an untrusted management domain creates guests and channels at runtime, the policy is what bounds it, the "immutable authority ceiling" the plan describes (L890-L901). E03 is consistent with this: its two denials are mappings that such a specification would derive. No runtime decision function is implied | RP-2 (M01-A): separate the specification role from the runtime-check trigger. RP-3: put the specification, its analyses, and its relation to the canonical manifest into S2's scope. S2: produce it; the language form is S2's choice |

### Isolation mechanism

| ID | Helium element and lesson | Class | Basis | Hand-off |
| --- | --- | --- | --- | --- |
| H11 | One G-stage root per subject, with another subject's private pages absent from it (He: `docs/architecture.md`) | Adopt | E08 gives each Linux guest its own root and window; E02 and E03 showed G-stage-denied loads on K3 | S3: tests in the first MVP milestone |
| H12 | Switching between roots that share a VMID needs a global `hfence.gvma`, and a later denied store to the shared page makes stale writable authority observable (He: `docs/concepts.md`, "Root switching") | Adapt | B7 uses distinct VMIDs and still fences and reads back on every switch, but K3's VMID tagging is trusted and untested (E08, E10) | S2: state the VMID and TLB invariant. S3: put Helium's stale-authority check, with distinct VMIDs, into the first MVP milestone on K3 |
| H13 | Exact raw PTE encodings under test: `V`, `U`, and `A` plus R/W/X, `D` on writable leaves, never `G` or reserved bits; `U` stays set (He: `docs/review-remediation.md`, REV-P2-03) | Adopt | R2's independent walker and the B6 and B7 re-walks check derived leaves. Helium found documentation claiming exact-bit coverage that its tests lacked | A later milestone, for any new leaf form |
| H14 | Builder caller and layout preconditions checked at compile and link time: aligned, unique guest addresses, and no overlap between tables and backing pages (He: `docs/review-remediation.md`, REV-P3-04) | Adopt | B-series preflight region checks and linker limits (E07, E08) | Practice |
| H15 | Accept only exact expected traps and end the run on anything else; resume past one instruction only when every recorded field agrees (He: `docs/concepts.md`, "Accepted traps") | Adapt | Failing closed stays: E06-E08 enforce exit ceilings, and E07's fail-closed readback caught `hedeleg`. Linux guests need a defined exit set (SBI calls, `wfi`, timer slices), and the planned MVP scenario injects guest faults and logs them instead of ending the run | S3 and the first MVP milestone: the exit surface |
| H16 | Fault acceptance keyed on `htval`; at the pin, `HTVAL == GPA >> 2`, which rejects high-bit aliases (He: `docs/security-and-limits.md`) | Adapt | K3's `htval` is unrecorded (E12) | S3: record K3's `htval` and `htinst` before any fault-injection design depends on them, then use the alias-rejecting comparison |
| H17 | A defined entry state for every subject (zeroed GPRs apart from `sp`, zeroed VS CSRs, `vsatp` Bare, then `hfence.vvma`) and a per-subject state table that names each row's evidence class. Helium's post-fork P1 defect REV-P1-02 leaked register state between subjects (He: `docs/architecture.md`, `docs/review-remediation.md`) | Adapt | B7 saves and restores per-guest state and reads back 11 CSRs, and with distinct VMIDs runs no `hfence.vvma`, as the specification allows (E08). The guests have no FP or vector state | S2: define the complete per-guest architectural state and what it excludes |
| H18 | Trap privileged guest operations rather than emulate them, through `VTVM`, `VTSR`, and `VTW` (He: `docs/review-remediation.md`, REV-P3-01) | Adapt | B5 sets `VTW` and `VTVM` and clears `VTSR`; B6 clears all three for Linux; B7 sets `VTW` to schedule on `wfi` (E06-E08) | S2: TCB. The trap bits follow the guest profile, with no instruction emulator |
| H19 | Read guest-modified memory once, through an explicit volatile boundary (He: `docs/review-remediation.md`, REV-P2-02) | Adopt | B5-B7 read guest DBCN buffers through a re-walked leaf (E06) | A coding-profile milestone |

### Transition and trusted core

| ID | Helium element and lesson | Class | Basis | Hand-off |
| --- | --- | --- | --- | --- |
| H20 | A tiny, layered privileged transition with written "must not own" lists: the first trap instruction swaps `sp` with `sscratch`, and there is one handler with no nested traps (He: `docs/architecture.md`) | Adapt | B7 takes its own HS timer interrupt at V=1 (E08), so "interrupts off" no longer holds. Layering and no nesting still apply | S2: TCB; the first protected-domain milestone |
| H21 | A restricted GNU C11 profile accepted by GCC and Clang: no libc, heap, recursion, variadics, or uncontrolled function pointers; warnings as errors; fail-closed build tags (He: `docs/engineering-sop.md`) | Adopt | Matches the recorded C-first decision; E03-E08 built with both compilers | A coding-profile milestone |
| H22 | Pure decision functions over captured inputs, transactional rejection without mutation, and one executor for privileged effects. Helium's refactor for checking grew its TCB from 2,689 to 4,598 lines (He: `docs/code-tour.md`, `docs/fv-pathfinder-lessons.md`) | Adapt | A candidate shape for verifiable seams. Captured inputs carry a separate correspondence obligation | S3: whether the MVP restructures the B5-B7 layers this way |
| H23 | Firmware and platform handoff assumptions written down as trusted inputs: hart 0, HS `satp` Bare, the firmware identity, and the SBI calls used (He: `docs/security-and-limits.md`) | Adopt | Extend the list with the K3 facts: OpenSBI 1.6 with SBI 2.0, SRST halting without power-off, `hedeleg` WARL, Sstc on every hart, and the 24 MHz timebase (E01, E06, E07) | S2: trusted assumptions |
| H24 | Sequential subjects with no scheduler, vCPU object, timer, interrupt, or guest SBI (Helium's fixed scope) | Reject | B5-B7 already run a guest SBI subset, Sstc timers, per-guest vCPU state, and a round-robin scheduler on K3 (E06-E08) | S3: the final SBI and scheduling boundaries |

### Testing and evidence

| ID | Helium element and lesson | Class | Basis | Hand-off |
| --- | --- | --- | --- | --- |
| H26 | Validators need exact cardinality: each trace marker exactly once and in order, one parser run per file, and one record per metadata prefix (He: `docs/review-remediation.md` REV-P2-01; `docs/finalization-ledger.md` HA-02, HA-03) | Adopt | Beryllium's open finding S6, where R3 trace checks match the `sret` word as an unanchored substring, is the same class (E05) | Separate direction for S5-S8 and S10. S3: a harness rule |
| H27 | Negative tests as separately linked build-time images with no runtime selector, under both compilers (He: `docs/verification.md`) | Adapt | The B5 and B7 negative scenarios ran in QEMU only (E06, E10) | S3: run selected negative images on the board |
| H29 | An offline, deterministic authority report built from the same sources, which the target never parses and which grants no authority (He: `docs/policy-models.md`) | Adapt | Beryllium's equivalent derives from the sealed manifest and the derived roots (R1, R2). It is not binary-correspondence evidence | S2: the schema. S3: the harness |
| H31 | The evaluator is an attack surface: read-only source, hidden build trees, a pinned image ID, no network, an ordinary checkout, and `GIT_OPTIONAL_LOCKS=0`. Helium's post-fork P1 defect REV-P1-01 was a writable checkout (He: `docs/review-remediation.md`) | Adopt | Beryllium's documented pinned-container gate binds the source tree read-write (`.github/copilot-instructions.md`) | S3: the evaluation harness |
| H32 | Word reproducibility exactly ("digest-pinned base plus recorded closure"), and pin and record the tools (He: `docs/review-remediation.md`, REV-P2-06) | Adopt | Bring-up tools are unpinned (E11); the roadmap already requires pinning before any assurance claim | S3 |

Rows H25, H28, H30, and H33 are in the
[practices already followed](#practices-already-followed) table.

### Assurance and claims

| ID | Helium element and lesson | Class | Basis | Hand-off |
| --- | --- | --- | --- | --- |
| H34 | One fixed claim, a required limit, and a list of forbidden phrasings (He: `docs/verification.md`) | Adopt | The B-series uses fixed claim wording (E09) | S3: the MVP claim and its forbidden phrasings |
| H36 | An exact linked-byte proof of the privileged transition, with the C builder and trap handler as explicit cut points (variant `b3f2631`) | Adopt | R7 uses this method and B4 re-derived it for K3; the B5-B7 layers are not covered (E05, E11) | S3: proof coverage |
| H38 | CBMC over production C against independent specifications, in eight tiers: 18 checks, 152 named claims, and 19,419 properties (He: `docs/formal-verification.md`) | Defer | The recorded stack is Rocq-first, with Cerberus as the C reference and the C-refinement verifier open. Helium chose CBMC for bounded, restricted C and says that choice is "not a claim that Rocq is unsuitable for future Be work" | S3: choose a verification method for each claim |
| H40 | Integration is the unproved part: "A defective trusted caller can therefore violate the intended integration even when the pure modules are correct", and "the live correspondence boundary becomes the real assurance problem" (He: `docs/security-and-limits.md`, `docs/fv-pathfinder-lessons.md`) | Adopt | R7's cut points and the unproved B5-B7 layers (E05, E11) | S3: the assurance plan |
| H41 | Helium's conditional recommendations for a future Beryllium verification effort, which it calls "decision gates, not an adopted Beryllium work plan" (He: `docs/fv-pathfinder-lessons.md`) | Defer | No Beryllium verification beyond R7 is planned | S3 |
| H42 | Five lessons not to transfer: do not generalize fixed bounds; do not conflate CBMC with kernel-checked proof; do not verify synthetic models without correspondence work; do not let evidence automation dominate design; do not claim system or hardware verification (He: `docs/fv-pathfinder-lessons.md`) | Adopt | Consistent with Beryllium's evidence discipline and the B-series claim wording | S2 and S3: constraints |
| H43 | Verification and evidence machinery "can grow faster than the security design it is meant to clarify" (He: `docs/fv-pathfinder-lessons.md`) | Adopt | Consistent with the 2026-10-06 process SOP | S3: a scope guard |

Rows H35, H37, and H39 are in the
[practices already followed](#practices-already-followed) table.

### Tooling

| ID | Helium element and lesson | Class | Basis | Hand-off |
| --- | --- | --- | --- | --- |
| H46 | A second architecture backend, Arm64 with TF-A, for portability (variant `2c0bf53`) | Reject | Arm stays conditional. It added firmware, translation, exception, toolchain, and evaluator surface without strengthening the RISC-V property. If Arm returns, keep Helium's rule: duplicate a thin orchestration layer rather than add runtime dispatch | A later, conditional decision |

Rows H44 and H45 are in the
[practices already followed](#practices-already-followed) table.

### Process, review, and publication

| ID | Helium element and lesson | Class | Basis | Hand-off |
| --- | --- | --- | --- | --- |
| H50 | AI review packages treated as hypotheses checked against repository evidence, with provenance manifests. Helium's execution-backed sixth package found two assurance defects that the five static packages missed (He: `docs/review-remediation.md`, `agent-review/`) | Adapt | The 2026-10-06 SOP does not run separate-model review packages as standard practice. Keep the principle (findings are hypotheses, and humans accept exact commits), not the package machinery | Practice |
| H51 | Documentation as maintained source, with deterministic generated HTML from one command (He: `docs/engineering-sop.md`) | Adapt | Beryllium generates HTML only at milestones, under its source-first policy | Practice |

Rows H47, H48, H49, H52, and H53 are in the
[practices already followed](#practices-already-followed) table.

### Strategy and scope

| ID | Helium element and lesson | Class | Basis | Hand-off |
| --- | --- | --- | --- | --- |
| H54 | Optimize for a small, stable mechanism and a tractable proof boundary, not the lowest line count; assurance can cost more than the runtime (comparison, "Cost separation") | Adopt | R7 and B4 (E05); Helium grew from 2,253 lines at the fork to 4,598 at the pin once checked | S2: TCB; S3 |
| H55 | The fixed TE PoC scenario: writer read-write and reader read-only on one shared page, with private pages denied (TE evidence) | Adapt | Already recorded as the expected first MVP milestone. E03 showed both denials on K3 as mappings derived under ownership and a read-only channel, and E08 provides two Linux guests, which have never shared a page (E10); B7's pair check refuses any shared page, so the scenario needs an explicit channel in the root derivation. The changes: two Linux guests; authority stated by S2's policy specification (H59) and enforced through the derived mappings, with a runtime check only if S2's trigger fires; distinct VMIDs; injected guest faults and logged denials instead of terminal exits; H12's stale-authority check; and board runs | S2: channel semantics in the specification. S3: the milestone |
| H56 | The comparison's precedent lessons: keep the mediation layer narrow (Nitro); memory-only evidence is not complete VM containment (pKVM); Salus and CoVE are the closest RISC-V structure; a capDL-inspired manifest (seL4); and a protected service needs a much larger boundary (OpenHCL). The comparison also read XSM/FLASK as "TE should not lead the initial core" | Adopt | The five precedent lessons are reflected in the recorded decisions. The XSM/FLASK reading is recorded here as the comparison's reading of a precedent about which mechanism leads the core, made before the K3 evidence; S1 does not carry it forward as a lesson. H59 adopts a TE-family policy as the specification, which FLASK's decision/enforcement split supports rather than contradicts | S2: the protected service. S3: CoVE interface reuse at the SBI boundary |
| H57 | Helium's scaling risks: more subjects and roots, dynamic policy, general scheduling, multiple harts, interrupts, devices and DMA, general guests, noninterference, evidence growth, and specification drift (He: `docs/fv-pathfinder-lessons.md`) | Defer | E08 already adds scheduling and interrupts; the rest is unexercised (E10) | S2: threat-model scope. S3: MVP non-goals |
| H58 | Helium's residual risks: optional CSRs and microarchitectural state, side channels (its shared page is an intended channel), and the trusted toolchain, emulator, firmware, and container engine (He: `docs/security-and-limits.md`) | Defer | Unchanged on K3; the board firmware joins the trusted list | S2: threat model |

### Practices already followed

These fourteen rows are classified **Adopt**. Each confirms a practice
Beryllium already follows, so they are condensed here (revision plan Q2);
their IDs are unchanged, and the hand-offs that other sections cite are
kept.

| ID | Helium practice | Beryllium equivalent | Hand-off |
| --- | --- | --- | --- |
| H25 | Test each behavior at the lowest practical layer; run each test exactly once in its gate (He: `docs/engineering-sop.md`) | Already a Beryllium rule | Practice |
| H28 | GCC and Clang parity on every gate | E03-E08 | Practice |
| H30 | Keep dirty development evidence apart from clean exact-commit evidence, bind contents, and never execute a path recorded in a bundle (He: `docs/verification.md`; REV-P2-05) | B-series results are retained at exact result commits with a SHA-256 manifest (E09) | S3: MVP evidence bundles |
| H33 | The build graph is part of the evidence boundary: reject caller overrides, `MAKEFILES`, and `--eval`; accept only exact toolchain values (He: `docs/verification.md`) | The R3-R6 launchers reject hostile Make controls; `bringup/` is outside the root build (E11) | S3: root integration |
| H35 | Name each absent verification method, and never move a claim between variants | B4 re-derived R6 and R7 for the K3 images rather than transferring them (E05) | Practice |
| H37 | Abstract Rocq ownership and H models, with H behavior modeled by hand where mainline Sail lacks H (the original variant) | The recorded proof stack | Practice |
| H39 | Seeded single-defect mutations, each mapped to the named claim that must fail (He: `docs/formal-verification.md`, "Proof sensitivity") | R6's single-defect fixture catalogue applies the same rule to images (E05) | Practice; S3 for any new method |
| H44 | Fully open, recorded tools behind one stable wrapper, `./he` | `./be` and the open-tooling decision; the bring-up targets sit outside it (E11) | S3: root integration |
| H45 | CHERIoT and Chisnall principles without CHERI code: no xmake, CHERIoT runtime, LLVM or Sail forks, or Rego | The recorded CHERI alignment | Practice |
| H47 | A named responsible human; AI never author, signatory, reviewer, or approver; GPL-3.0-only blocks direct Linux submission; AI assistance disclosed on every release surface (He: `docs/policy-and-publication.md`) | `LLM_POLICY_ALIGNMENT.md` | S3: licensing in the release path |
| H48 | Review-only posting is not a release: a human gate decides an exact commit, and any later source change invalidates approval (He: `docs/policy-and-publication.md`) | The recorded clean-repository migration and publication block | S3: the release path |
| H49 | Narrow, separately recorded human checkpoints: design decisions, exact-source review, and release approval are distinct | Plan acceptance, authorization, result acceptance, and push are separate decisions | Practice |
| H52 | Fork and handoff hygiene: scan for absolute paths; never infer approval from a ref name, tag, or commit subject; timestamps are not ordering evidence (He: `HANDOFF.md`) | The source checker rejects private locators; S1 applies the ref rule to its own pin | Practice |
| H53 | A human-review handoff with full commit IDs, frozen branches, a name-status diff, prioritized paths, evidence files, and the next human action (He: `docs/engineering-sop.md`) | The review-summary practice | Practice |

## Summary

| Class | Count | Rows |
| --- | ---: | --- |
| Adopt | 34 | H01, H03, H04, H11, H13, H14, H19, H21, H23, H25, H26, H28, H30-H37, H39, H40, H42-H45, H47-H49, H52-H54, H56, H59 |
| Adapt | 15 | H02, H05, H06, H12, H15-H18, H20, H22, H27, H29, H50, H51, H55 |
| Reject | 2 | H24, H46 |
| Defer | 8 | H07-H10, H38, H41, H57, H58 |

Findings:

- The B-series supports Helium's authority and isolation lessons, and it
  supersedes Helium's single-subject runtime simplifications: B5-B7 already
  run guest SBI calls, timers, per-guest state, and scheduling on K3.
- For S2, E03 is evidence about enforcement: on K3, both denials of the TE
  PoC scenario were expressed as G-stage mappings derived under ownership
  and an explicit read-only channel. It says nothing about how the system's
  security properties are specified, analyzed, or verified. For that role
  S1 adopts a central, declarative policy in the Type Enforcement family
  (H59), with enforcement still derived from it; the capability trigger and
  the runtime-check trigger stay with S2 under the M01-A wording, and E03
  is not a test of either.
- Before any isolation claim between Linux guests, the MVP must close three
  gaps: no shared page or denial test between Linux guests on K3 (E10), K3's
  unrecorded `htval` (E12), and K3's untested VMID tagging (E08).
- The largest Helium input since the comparison is the release line's
  bounded CBMC work and its inputs for "the next Be stage" (H06, H07, H22,
  H38-H43), together with Helium's own definition of TE as a declarative
  policy (H59).

## Hand-off to S2

1. Keep ownership plus explicit channels as the enforcement baseline (H02);
   produce the policy specification, a central, declarative policy in the
   Type Enforcement family, with the analyses the implementation plan's
   policy proof targets name and its relation to the canonical manifest
   (H59); and evaluate the capability trigger and the runtime-check trigger
   against the platform's use cases under the M01-A wording (H02, H08, H09).
   E03 is enforcement evidence, not a test of either trigger.
2. Object model: identifiers versus authority (H03); whether resource roles
   need distinct types or authority in the specification (H07); how
   overlapping grants combine, and whether any authority exists without a
   mapping, stated in the specification (H06).
3. Sealed state: what in the TCB protects it after sealing (H05).
4. Per-guest state and transitions: the complete architectural state that is
   saved, restored, and reset, its evidence class, and its exclusions (H17);
   the trap-bit profile (H18); and transition layering and HS interrupt use
   (H20).
5. The translation invariant for VMIDs, fences, and stale authority across
   switches and sharing (H12).
6. Trusted assumptions and threat-model scope: the K3 firmware and platform
   facts (H23); Helium's scaling and residual risks (H57, H58); and side
   channels through intentionally shared pages.
7. Policy compilation to the canonical manifest and the analyses belong to
   the specification in any case (H10, H59). If the runtime-check trigger
   fires: lifecycle, lookup, caching, update, and revocation obligations,
   designed from scratch (H08, H10).
8. The schema of an authority report derived from the sealed manifest (H29).

## Hand-off to S3

1. The first MVP milestone as adapted in H55: two Linux guests share one page
   (writer read-write, reader read-only), private pages are denied, guest
   faults are injected and denials logged (H15), distinct VMIDs come with a
   stale-authority check (H12), K3's `htval` and `htinst` are recorded first
   (H16), and selected negative images run on the board (H27).
2. The evaluation harness: exact cardinality in validators (H26), clean and
   dirty evidence kept apart (H30), evaluator hardening including read-only
   source mounts (H31), pinned tools and exact reproducibility wording (H32),
   and build-graph controls with a root-integration decision (H33, H44).
3. The assurance plan: a verification method for each claim (H38), proof
   coverage of the B5-B7 layers (H36, E11), correspondence as the central
   problem (H40), Helium's conditional recommendations (H41), the lessons not
   to transfer (H42), a verifiable-seam structure if one is chosen (H22), and
   a scope guard on evidence machinery (H43).
4. Claims: one MVP claim, with its required limit and forbidden phrasings
   (H34, H35).
5. The release path: an exact-commit human gate, clean-repository
   migration, AI-assistance disclosure, and the licensing decision for any
   upstream submission (H47, H48).
6. The SBI, exit-surface, and scheduling boundaries for the first
   protected-domain milestone (H15, H18, H24).

## The comparison's open decisions today

| Open in the comparison (2026-07-20) | Status at the base | Owner |
| --- | --- | --- |
| Acceptance of the R0 freeze | Closed: accepted 2026-07-27 | none |
| The protected-service use case | Open | S2 or S3, inside an accepted scope (decision gate 2) |
| Permanent software-capability representation, delegation, and revocation | Open; trigger-gated | S2, then a later milestone |
| TE's role | Specification role adopted by H59, pending M01-A; whether any selected use case fires the runtime-check trigger stays open. E03 is enforcement evidence, not a trigger test | S2 |
| Runtime manifest encoding and the Linux or management ABI | Open | S2 for semantics and for the relation from the policy specification to the manifest (H59); a later milestone for encoding and ABI |
| Interrupt, timer, SBI, IOMMU, IOPMP, and device boundaries | B5-B7 ran a bounded guest SBI subset, Sstc timers, and an HS timer slice; the rest is unexercised | S3, then the first protected-domain milestone |
| K3 firmware, PMP/ePMP, cache, debug, and hardware behavior | Partly characterized by B0-B7 (OpenSBI 1.6, SRST, `hedeleg` WARL, Sstc, the timebase); PMP, cache, and debug unexamined | S3 |
| Static multicore and later serialized control | Open | a later milestone selected by S3 |
| VBS/VTL, attestation, sealed state, and anti-rollback | Open | S2 for scope; later milestones |
| CHERI backend and CHERI+H model feasibility | Open; trigger-gated | later |
| Final Linux Kbuild placement versus a separate project | Open | later, with community feedback |
| MVP 1.0 scope and assurance claim | Open | S3 |

## Observations outside S1's scope

S1 changes none of these; each needs separate direction.

- The comparison's status and decision lists stop at the runtime plan ("R0
  next"). Its Helium figures (2,253 lines and 16 KiB) predate Helium's
  post-fork growth: 2,689 lines at `f928aac5`, and 4,598 lines with 20,480-
  and 24,576-byte images at the pin.
- The [implementation plan](implementation-plan.md) and the
  [open-tooling policy](open-tooling.md) call the gate that needs an open
  binary-correspondence result milestone 8, but the assurance release is now
  milestone 9 and milestone 8 is portability.
- The documented pinned-container gate binds the source tree read-write
  (H31).
- Beryllium's open audit finding S6 is the same class as Helium's REV-P2-01
  (H26).
- Helium's documents at the pin disagree about its release status and its
  CBMC tier coverage; S1 relies on neither.

## Open questions and defaults

The defaults apply unless the responsible human answers otherwise. The
revision plan's own questions Q1 to Q6 were decided by its acceptance with
their defaults; this revision follows them (the Helium pin, the condensed
practice table, the name "a central, declarative policy in the Type
Enforcement family", the capability trigger's wording unchanged, the
specification language form left to S2, and one packet for RP-1 to RP-3).

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | Which Helium commit does S1 read? | `1c9e526`, read as evidence only, with no Helium status inferred | `f928aac5`, the `for-review` ref that Beryllium's records name. Rows H06, H07, H10, H16, H22, H38-H43, H50, H52, H57, and H59 cite content that only the release line has and would be dropped or narrowed; the other rows stand, because both commits share base `1ab289c` |
| Q2 | Should S1 correct the observations above? | No: each needs separate direction, and S1 changes no other document. The accepted project review has since recorded each of them as a finding | Fold the corrections into the step that next touches each document |

## Non-claims

- S1 is a synthesis. It adds no implementation, emulation, proof, test, or
  board evidence, and it ran nothing.
- No Helium result transfers to Beryllium, including Helium's QEMU runs,
  CBMC results, review dispositions, and release or gate status.
- The classifications are planning input; S2 and S3 decide. S1 recommends
  a specification role for a TE-family policy (H59) and selects no runtime
  mechanism: a runtime TE check, capabilities, CHERI, a protected service,
  an SBI boundary, a verification method, root integration, and the MVP
  scope all stay unselected.
- S1 does not assert that Model 0.1's TE trigger was wrong for the fixed
  synthetic profile it governed; it records that the trigger does not cover
  the specification role, which S2 needs and plan revision M01-A separates.
- B-series results stay diagnostic bring-up evidence for one board.
- Nothing here is formal verification or hardware validation of Beryllium.

## Status record

```text
s1_status=accepted
s1_target=fd670dcd54ff4f2c66349d377be914698b9dda3b
s1_acceptance_instruction=I-accept-RP-1-RP-2-RP-3
s1_acceptance_date=2026-10-18
s1_revision=RP-1
s1_replaces=0fbca0fdc7b9ecca2aaf6635bb04a3335bca72ef
s1_revision_plan=07541c59426865ce8b1eef3c409913923cd5e64b
s1_revision_direction=revise-adopt
s1_critique=480dab72de7a74f8b84c64c2fefee8190cb87b70
s1_authorization_instruction=authorize-S1-proceed
s1_authorization_date=2026-10-16
s1_beryllium_base=56e36ae11e47bb08416a44c5647aecd304fd4902
s1_helium_repository=../helium-te-poc
s1_helium_pin=1c9e52693abe0072ac9b8ce4e0a3ecb5f8bb9489
s1_helium_reading=evidence-only-no-status-inferred
s1_helium_for_review_ref=f928aac5979b6166f3f68a76a9acf1fc916161d8
s1_elements=59
s1_adopt=34
s1_adapt=15
s1_reject=2
s1_defer=8
s1_specification_role=te-family-declarative-policy-adopted-h59
s1_runtime_mechanism_selected=none
s2_authorization=none
s3_authorization=none
```
