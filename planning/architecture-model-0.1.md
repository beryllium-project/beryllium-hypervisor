<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium Architecture Model 0.1: static single-hart isolation contract

## Status and authorization boundary

This is the selected first concrete post-pathfinder deliverable.

Model 0.1 is an architecture, executable-model, proof, and host-checker
deliverable. It does not authorize a new hypervisor runtime, a sixth
Helium variant, multicore implementation, Linux boot, or MVP 1.0.

The plan is based on the decisions and evidence in
[`pathfinder-comparison.md`](pathfinder-comparison.md). Runtime work may begin
only after Model 0.1 closes its decision and refinement gates and a separate
bounded implementation plan is approved.

The implementation candidate is now under `model/` on branch
`beryllium/architecture-model-0.1`. Its restricted-C checker/model, two
fixtures, deterministic reports, adversarial tests, Rocq proof development,
and open evaluator are documented in
[`architecture-model-0.1-evidence.md`](architecture-model-0.1-evidence.md).
The model-local, complete repository, and pinned rootless gates pass.
Responsible-human review accepted the Model 0.1 boundary and refinement
direction on 2026-07-22, with incremental review continuing. Acceptance does
not authorize runtime work.

**Plan revision M01-A: accepted 2026-10-18.** Under the accepted
[S1 and TE-trigger revision plan](s1-te-trigger-revision-plan.md) (exact
commit `07541c59`, accepted 2026-10-18; work package RP-2), the
[TE trigger](#te-trigger) section below is revised to separate TE as the
specification of the system's security policy, which is not trigger-gated,
from TE as a runtime check, which stays behind the trigger. The revision
follows the project's narrow plan-revision pattern (R6-A, R6-B, R7-A, R8-A,
R8-C). It changes that section and this note only: the fixed instance, the
required state, the canonical manifest semantics, the Rocq obligations under
`model/`, the artifacts, the non-goals, the completion claim, and the
software-capability trigger are unchanged, and the Model 0.1 text accepted
on 2026-07-22 stays accepted as history. The responsible human accepted
M01-A at exact commit `95ef0f6c0fc1fe457e93b7d34b48cde5a411e8ab` (parent
`fd670dcd`) on 2026-10-18 with the instruction `I accept RP-1 RP-2 RP-3`,
given in reply to the
[revision review summary](s1-te-trigger-revision-review-summary.md), which
maps RP-2 to that commit; the revised section is now the governing
TE-trigger text, and the earlier text is quoted inside it as history.
Acceptance of M01-A decides the wording of the trigger section and nothing
else: it selects no runtime mechanism, starts no S2 work, and authorizes no
implementation. Only this note's acceptance sentences and the section's
status line were changed after the accepted commit.

## Goal

Turn the common result of the five pathfinders into one architecture-level
contract:

> In a fixed single-hart system, HS owns two isolated VS-domain roots, all
> private frames and saved state are confined to their declared domain,
> monitor state is absent from both roots, and the only cross-domain storage
> channel is one explicitly declared directional shared region.

This is deliberately stronger than another positive/negative QEMU trace and
deliberately narrower than a general hypervisor.

## Fixed instance

```text
M mode
  OpenSBI / firmware handoff assumptions
        |
        v
HS mode: abstract Beryllium isolation engine
  immutable manifest and ownership state
  management root + saved state
  protected root + saved state
  checked root/stack/state transition
        |
        +-- sequential entry --> management VS domain
        |
        +-- sequential entry --> protected VS domain

Declared cross-domain storage:
  one directional shared region only
```

The two domains are:

- an untrusted management-domain abstraction; and
- a protected-service abstraction.

They are not Linux, a complete VMM, a secure kernel, or a selected product use
case. "Static" means that domains, roots, frames, mappings, and channel rights
do not change after initialization. The active domain and saved CPU state do
change during an HS-controlled sequential switch.

## Threat and property boundary

Both VS domains may be malicious. They may supply arbitrary modeled inputs at
their declared entry and shared-memory interfaces.

Model 0.1 protects:

- monitor code, data, roots, trusted stack, and model state;
- each domain's private frames;
- each domain's saved architectural state;
- root/domain binding; and
- channel direction and access rights.

Model 0.1 allows:

- denial of service;
- self-destruction by a domain;
- information transfer through the declared channel in its permitted
  direction; and
- all explicitly listed firmware, architecture, compiler, and refinement
  assumptions.

It excludes timing, cache, predictor, power, thermal, and other
microarchitectural channels.

## Required model state

The abstract state must represent enough behavior to expose, rather than hide,
the root-switch hazard demonstrated by the TE pathfinder:

- initialization and sealed/static status;
- domain and root identities;
- frame ownership and monitor-private ranges;
- each root's complete modeled mappings and rights;
- active domain, root, VMID, and trusted stack;
- disjoint saved register state for both domains;
- modeled cached translations relevant to the fixed roots;
- completion of the required fence before the next domain executes;
- the explicit shared-channel record and direction; and
- a fail-closed error state.

The model must not prove a property by assuming away stale translations,
register residue, or an incorrect active root.

## Canonical manifest semantics

Model 0.1 defines semantics before choosing a final source or binary encoding.
The canonical information is:

- architecture and fixed profile identifier;
- domains and their immutable identifiers;
- the one active hart;
- root identities and VMIDs;
- frames, physical extents, owners, and classes;
- complete GPA-to-frame mappings and requested rights;
- monitor, root-table, and trusted-stack exclusion ranges;
- saved-state ownership;
- explicit shared-channel endpoints, direction, and rights; and
- model and policy-instance identifiers.

The checker must reject:

- duplicate or overlapping frames;
- a private frame with multiple owners;
- monitor or stage-table memory mapped into a VS root;
- a mapping not declared by the manifest;
- PTE rights exceeding declared rights;
- undeclared shared backing;
- channel rights inconsistent with channel direction;
- a root, VMID, stack, or saved-state record bound to the wrong domain;
- incomplete input; and
- unsupported versions or values.

The final format, signing, measurement, and in-HS parser remain later
decisions.

## Executable model and host checker

The deliverable includes:

1. an executable state machine for initialization, domain entry, checked
   switch, modeled access, expected denial, and fail-closed termination;
2. a host-side reference checker for the canonical manifest semantics;
3. adversarial and property tests covering every rejection above;
4. deterministic authority and mapping reports; and
5. fixtures for the minimal-ownership and fixed-TE pathfinder topologies.

The TE fixture supplies a different authority instance. It does not put TE in
the Model 0.1 core or transfer TE runtime evidence into the model proof.

## Rocq proof obligations

Model 0.1 must machine-check the following bounded properties:

1. **Initialization completeness:** no domain entry is possible before the
   complete valid static state is sealed.
2. **Unique ownership:** every private frame has at most one owning domain.
3. **Monitor exclusion:** no VS mapping reaches monitor code, data, roots, or
   trusted stacks.
4. **Mapping soundness:** every successful modeled access is permitted by a
   declared mapping whose rights are a subset of manifest authority.
5. **Root/domain binding:** domain entry selects only that domain's root, VMID,
   stack, and saved state.
6. **Saved-state separation:** one domain's transition cannot read or modify
   the other's private saved register state.
7. **Channel confinement:** shared backing is reachable only through the
   declared channel and only with its directional rights.
8. **Switch freshness:** no cached translation from the previous root grants
   authority after the required root write and fence complete.
9. **Fail-closed behavior:** invalid initialization, state, access, or switch
   cannot become an allowed operation.

The maintained theorem mapping is:

| Obligation | Public theorem | Module |
| --- | --- | --- |
| Initialization completeness | `initialization_completeness` | `model/proof/Initialization.v` |
| Unique ownership | `unique_private_ownership` | `model/proof/Isolation.v` |
| Monitor exclusion | `monitor_exclusion` | `model/proof/Isolation.v` |
| Mapping soundness | `mapping_soundness` | `model/proof/Isolation.v` |
| Root/domain binding | `root_domain_binding` | `model/proof/Transition.v` |
| Saved-state separation | `saved_state_separation` | `model/proof/Transition.v` |
| Channel confinement | `directional_channel_confinement` | `model/proof/Isolation.v` |
| Switch freshness | `switch_freshness` | `model/proof/Transition.v` |
| Fail-closed behavior | `terminal_fail_closed_behavior` | `model/proof/Transition.v` |

`pre_fence_target_entry_denied` separately proves that selecting the target
root while retaining cached translations cannot enter that target before the
required fence, including the conservative shared-VMID-zero projection.
`model/proof/Claims.v` combines these as
`architecture_model_0_1_claims`. `model/proof/Assumptions.v` prints the
logical assumptions of each theorem and the bundle. The proof runner requires
all eleven reports to be closed under the global context and independently
checks all proof objects with `rocq check`.

Full information-flow noninterference is deferred. A later theorem may claim
bounded state-based noninterference only after the model, exact transition
wrappers, translation-cache behavior, saved state, and C cut points are
connected. No timing or microarchitectural noninterference claim is planned
for Model 0.1.

## Cross-variant evidence map

| Input variant | Model 0.1 contribution | Claim boundary retained |
| --- | --- | --- |
| Original RISC-V | Basic transition, mapping, denial, revoke, abstract ownership, and C-verifier workflow | Abstract and leaf-C results apply only to that branch |
| Dual architecture | Identifies which transition and translation obligations are architecture-specific | Arm remains conditional and is not a Model 0.1 execution target |
| Minimal RISC-V | Supplies the smallest ownership baseline and separate authority instances | No formal result transfers from the removed proof setup |
| Exact proof | Supplies exact-wrapper, trap-frame, layout, and fixed-isolation proof method | C G-stage construction and C trap handling remain cut points |
| Fixed TE | Exposes two-root, saved-state, shared-rights, and stale-translation switch hazards | Review-and-test evidence only; TE remains an optional fixture |

Every Model 0.1 theorem and test must identify which input it reuses, which
behavior it newly models, and which prior claim does not transfer.

## Future C refinement boundary

Model 0.1 does not implement these modules. It must define their future
contracts so that the next runtime plan is bounded.

| Abstract operation | Future restricted-C or assembly cut point | Current evidence |
| --- | --- | --- |
| Validate and seal static state | Manifest validator and initializer | TE tests one fixed label seal; no generic manifest validator |
| Construct one root from authority | G-stage builder | QEMU tests roots; exact-proof branch assumes C correspondence |
| Select domain root and trusted stack | Root-switch preparation | TE branch tests one VMID-zero switch |
| Save and restore domain state | Exact trap/transition wrapper plus C handler | Exact wrapper is checked; C handler remains assumed |
| Complete translation invalidation | Architecture fence boundary | Exact-proof models fenced revocation; TE tests a root switch |
| Authorize mapped access | Ownership/channel mechanism | Minimal policies and TE supply separate tested instances |

For each cut point, the deliverable records:

- abstract precondition and postcondition;
- memory and authority footprint;
- failure result;
- architecture assumption;
- proof or test obligation;
- current proved/assumed status; and
- evidence invalidation rule.

## Authority extension triggers

Model 0.1 selects ownership only for its immutable instance. It defines, but
does not fire, later extension triggers for runtime mechanisms. Plan revision
M01-A, below, distinguishes those triggers from the specification of the
security policy, which is not a mechanism and not trigger-gated.

### Software-capability trigger

Add representation-independent software capabilities only if the selected
motivating use case requires runtime designation plus delegation, attenuation,
holder transfer, or revocation that static owner/channel records cannot
express without ambient authority or per-caller special cases.

An opaque integer alone is not a capability. On non-CHERI hardware, authority
must remain in protected monitor state and be bound to the current subject.

### TE trigger

**Revised by plan revision M01-A (accepted 2026-10-18 at exact commit
`95ef0f6c`).** The text accepted on 2026-07-22 conflated two things: the
specification of the system's security policy, and a policy decision
consulted at run time. The 2026-10-17
[project review](project-review-2026-10-17.md) (F-01, F-02) found that
under that wording TE was visible to every later decision only as
an extra runtime denial, and that the specification role the
[implementation plan](implementation-plan.md) expects (an analyzable static
policy, L740; FLASK as the key precedent, L734; the policy proof targets,
L931-L940; a pipeline from policy source to the Rocq configuration, L401,
L416-L417) was never scheduled or owned. The revised section states the
three cases separately.

**TE as specification.** The system's security policy is stated as a
central, declarative policy in the Type Enforcement family: types or labels
on subjects and objects, object classes, permissions, and rules, with
deterministic and total semantics, default deny, and explicit conflict
resolution. The canonical manifest must be shown to conform to that policy,
and the implementation plan's policy proof targets apply to it. This is not
trigger-gated: it is how the system's security properties are specified,
analyzed, and verified, and S2 produces it under the scope that work package
RP-3 of the revision plan defines. Enforcement stays derived, as Model 0.1
and Model 0.2 already require: the manifest is validated against the policy,
the roots are derived from the manifest, and no runtime decision function is
implied by this part. The policy can be proved to say what is intended;
Model 0.1's and Model 0.2's obligations can then be stated relative to it,
in the way seL4 proves its properties relative to configured authority.

**TE as a runtime check.** A policy decision consulted on an access path
beyond the derived mappings. This stays behind the trigger. Add a runtime TE
check only if the selected use case contains a capability-valid or
ownership-valid operation that must still be denied at run time because of
an independent mandatory source/target/class or flow rule, and the review
shows that object separation, channel direction, or capability attenuation
is inadequate. The trigger requires at least one independently observable
case where:

- designation and discretionary rights allow but TE denies; and
- TE allows but no valid designation exists, so access still denies.

That two-case condition is a test of composition with designation, taken
from the isolation-engine research: it shows whether a runtime decision adds
anything that the derived mappings do not already express. It is not a test
of whether a policy is needed; the specification above is needed in every
case. A fixed configuration whose denials are all expressed as derived
mappings, such as B2's K3 result, therefore says nothing about this trigger
either way.

**The dynamic case.** Once an untrusted management domain creates domains or
channels at run time, the specification is what bounds what it may create.
That is the "immutable authority ceiling" the implementation plan already
describes (L890-L901): every dynamic grant must be a subset of authority the
policy delegates, and anything outside it fails closed. The design of that
ceiling, and whether enforcing it needs a runtime check in the sense above,
belong to S2 and to the first protected-domain milestone.

Two notes. The software-capability trigger's wording stands (revision plan
Q4). The post-pathfinder comparison's "Cost separation" measures the lines
and bytes of a TE mechanism in the fixed PoC; it does not price, and was
never meant to price, the specification role.

The text accepted on 2026-07-22, which M01-A supersedes and which is kept
here as history, read:

> Add TE only if the selected use case contains a capability-valid or
> ownership-valid operation that must still be denied because of an
> independent mandatory source/target/class or flow rule, and the review
> shows that object separation, channel direction, or capability attenuation
> is inadequate.
>
> The trigger requires at least one independently observable case where:
>
> - designation and discretionary rights allow but TE denies; and
> - TE allows but no valid designation exists, so access still denies.

The generic protected-service abstraction does not itself fire either
runtime trigger. A narrow motivating use case remains a later separate
planning output. Model 0.2 made the policy-neutral core mechanism boundary
explicit and was accepted on 2026-07-24, but selected no use case or trigger
evaluation.

## Artifacts

The completed deliverable contains:

- this maintained plan and final decision record;
- canonical manifest semantics and fixtures;
- an executable architecture state machine;
- a host reference checker and adversarial tests;
- Rocq source and checked proof objects for the bounded obligations;
- a cross-variant claim/assumption trace;
- generated authority and mapping reports;
- future C/assembly cut-point contracts;
- reproducible open tool manifests and local commands; and
- HTML documentation with explicit claims and limits.

The selected paths and implementation languages are:

| Artifact | Maintained source | Generated evidence |
| --- | --- | --- |
| Canonical semantics and host checker | restricted GNU C under `model/include/be/` and `model/src/manifest.c` | GCC/Clang unit binaries under `build/model/unit/` |
| Executable state machine | `model/src/state.c` | GCC/Clang runners under `build/model/host/` |
| Authority fixtures | `model/src/fixtures.c` | normalized JSON under `build/model/reports/` |
| Adversarial and property tests | C and Node.js under `model/tests/` | test/report gate output |
| Bounded proof | Rocq under `model/proof/` | `.vo`, theorem, assumption, and checker logs under `build/model/proof/` |
| Open tool profile | `model/toolchain.conf` and `model/Containerfile` | exact tool/source/artifact identities under `build/model/evidence/` |
| Documentation and diagrams | `planning/*.md` and `planning/diagrams/*.dot` | `docs/html/` and `planning/public/diagrams/*.svg` |

The in-memory C structure is intentionally not a selected manifest encoding.
There is no runtime parser.

## Non-goals

- New or changed HS runtime behavior.
- A sixth Helium pathfinder.
- Linux or a general SBI virtualization surface.
- Multicore, IPIs, scheduling, migration, or overcommit.
- Runtime domain, mapping, ownership, policy, or manifest mutation.
- Capability or TE enforcement in HS.
- A general policy language, parser, server, or access-vector cache.
- VBS, VTL, enclave, secure-kernel, attestation, key-sealing, or anti-rollback
  behavior.
- Interrupt, timer, device, DMA, IOMMU, or IOPMP behavior.
- K3 hardware claims.
- Final manifest encoding, stable ABI, or Linux-tree placement.
- Whole-implementation, compiler, firmware, hardware, or complete
  noninterference proof.

## Supportable completion claim

After all exit criteria pass, the strongest planned statement is:

> Beryllium Architecture Model 0.1 machine-checks bounded ownership, monitor
> exclusion, mapping-rights, domain/root/saved-state binding, directional
> channel, switch-freshness, and fail-closed properties for one fixed abstract
> single-hart, two-domain configuration. A host reference checker rejects
> malformed configurations covered by the Model 0.1 manifest semantics.

Required limit:

> Model 0.1 does not prove a Helium or future Beryllium implementation, C or
> assembly refinement, compiler output, firmware, QEMU, K3 hardware, devices,
> multicore behavior, or full information-flow noninterference.

## Exit criteria

1. The fixed state and operation vocabulary is complete and versioned.
2. Every manifest rejection rule has positive and negative automated coverage.
3. All nine Rocq obligations check without `Admitted`, `Axiom`, or an
   equivalent unreported assumption.
4. Translation-cache/fence and saved-state switch hazards are represented
   explicitly.
5. Minimal-ownership and fixed-TE topologies instantiate the same isolation
   invariants without changing the core model.
6. The claim/assumption trace preserves every branch-specific evidence limit.
7. Future C and assembly cut points have bounded contracts and explicit
   assumed/proved status.
8. The supportable claim and required limit match generated evidence and HTML.
9. The complete open, reproducible model/proof/checker gate passes.
10. Human review accepts the boundary, ownership baseline, and refinement
    direction before the next model phase begins. This occurred on
    2026-07-22; later review remains incremental.

## Gates after Model 0.1

Model 0.1 did not by itself authorize runtime work. Its selected successor was
[`Architecture Model 0.2`](architecture-model-0.2.md), a policy-neutral
refinement of the core mechanism boundary. Responsible-human review accepted
Model 0.2 on 2026-07-24; that acceptance also authorizes no runtime work.

The Model 0.2 phase was required to:

- separate proposed configuration, canonical sealed state, and derived
  enforcement;
- preserve the Model 0.1 claim and assumption limits;
- avoid selecting a protected service, policy framework, or composed security
  model;
- retain K3 results as `NOT RUN` until measured; and
- require a later separately approved plan before runtime implementation.
