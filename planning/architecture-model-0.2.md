<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium Architecture Model 0.2: policy-neutral core mechanism boundary

## Status and authorization boundary

Responsible-human review accepted Architecture Model 0.1 on 2026-07-22.
Review continues incrementally as later models expose omissions or require
changes, but Model 0.1 acceptance is no longer an open gate.

The selected successor to Model 0.1 was **Architecture Model 0.2:
policy-neutral core mechanism boundary**. Responsible-human review accepted
the exact Model 0.2 boundary and evidence on 2026-07-24. Incremental review
continues, and Model 0.2 acceptance is no longer an open gate.

Later on 2026-07-24, responsible-human direction selected a bounded
single-hart runtime-planning phase. Responsible-human review accepted the exact
[`single-hart-runtime-plan.md`](single-hart-runtime-plan.md) contract and
separately authorized its fixed implementation profile on 2026-07-25. R0
fixed profile and layout is the next package.

Model 0.2 is a non-runtime architecture, executable-model, checker, and proof
phase. It does not authorize:

- a privileged Beryllium runtime;
- Linux boot or a stable Linux/management ABI;
- a protected-service use case;
- selection or integration of capabilities, TE, MLS/MCS, RBAC, Rego, Cedar,
  FLASK, or another policy/security model;
- runtime policy loading, callbacks, or a policy server;
- multicore, interrupts, timers, devices, DMA, IOMMU, or IOPMP behavior;
- CHERI, VBS/VTL, enclave, measured-launch, or attestation implementation;
- a sixth Helium pathfinder; or
- MVP 1.0 or public release.

The accepted implementation and evidence live under `model/`. The
restricted-C validator/model, neutral proposal fixtures, deterministic
reports, adversarial tests, and bounded Rocq proof are documented in
[`architecture-model-0.2-evidence.md`](architecture-model-0.2-evidence.md).
Acceptance does not authorize any later stage.

## Why this phase came next

Selecting a protected service or policy framework before this phase would
have risked:

- overfitting core state and interfaces to one workload;
- embedding TE, capability, identity, role, or attestation assumptions in
  mechanism;
- treating a policy-engine API as the hypervisor security model;
- expanding the trusted core before its own invariants are explicit; and
- confusing correct enforcement with correctness of the policy being
  enforced.

The phase question was therefore not which policy Beryllium should implement.
It was:

> What is the smallest policy-neutral state and transition mechanism an HS
> isolation core must own so that later policy models can be evaluated without
> bypassing or redefining its structural safety invariants?

The protected-service and policy-model questions remain deferred, not
rejected. The accepted core mechanism boundary now makes a separately
authorized evaluation meaningful; it does not select one.

## Design rule: policy-neutral, not policy-free

The core cannot be free of all policy. Resource ownership, monitor exclusion,
channel direction, and admissible state transitions are security decisions.
Model 0.2 instead avoids selecting a **policy framework or general security
model**.

The separation is:

| Layer | Model 0.2 responsibility |
| --- | --- |
| Configuration producer | Proposes desired domains, resources, ownership, channels, and rights; identity and implementation are not selected |
| HS validator | Treats the proposal as untrusted for structural safety and either rejects it or produces canonical state |
| Sealed authoritative state | Holds the only core-recognized domain, resource, ownership, channel, and binding facts |
| Enforcement derivation | Builds roots and access decisions only from sealed authoritative state |
| Later policy evaluation | Determines whether a policy framework can produce useful proposals without changing core invariants; out of scope now |

A policy producer may eventually be an offline compiler, firmware input, a
management domain, or a separately trusted policy domain. Model 0.2 must not
depend on which option is selected.

## Trust and privilege boundary

```text
Outside the trusted mechanism

  policy-neutral configuration proposal
  { domains, resources, requested ownership, channels, rights }
                         |
                         v
HS trusted mechanism

  bounded input copy
        -> canonical validation
        -> sealed authoritative state
        -> root and transition derivation
        -> access enforcement

Untrusted domains never write sealed state, roots, or active bindings.
```

The configuration producer is not trusted to preserve:

- extent non-overlap;
- monitor exclusion;
- unique ownership;
- rights attenuation;
- root/domain/state binding; or
- complete initialization.

The HS validator is trusted to reject proposals that violate those
properties. A structurally valid but intentionally over-permissive proposal
may still be a policy error. Model 0.2 must distinguish that policy error from
a mechanism-safety failure.

## Fixed scope

Model 0.2 remains:

- single-hart;
- static after activation;
- bounded to the existing two-domain proof instance;
- encoding-independent;
- Linux-free;
- device-free;
- allocation-free after initialization;
- free of runtime policy interpretation; and
- explicit about architecture-specific cut points.

The fixed two-domain instance prevents premature generalization. The object
vocabulary should be suitable for later bounded expansion, but Model 0.2 does
not prove arbitrary domain or resource counts.

## Inputs and outputs

### Inputs

1. A bounded normalized platform/resource inventory.
2. One copied configuration proposal containing:
   - domain and vCPU identifiers;
   - memory extents and monitor-owned exclusions;
   - requested ownership;
   - translation-root and saved-state bindings;
   - explicit shared-channel endpoints and direction; and
   - requested read, write, and execute rights.
3. Actual core operations such as root construction, domain selection,
   transition completion, and mapped access.

The platform inventory and proposal are distinct. Describing a resource does
not grant authority to it.

### Outputs

The mechanism produces exactly one of:

- a stable rejection class with no published root or runnable domain; or
- canonical, sealed authoritative state plus roots, reports, and transition
  state derived from that state.

The mechanism does not produce a policy-language decision, role assignment,
label, capability token, attestation verdict, or service-specific result.

## Required authoritative state

Model 0.2 should make the following separation explicit:

### Proposed state

- copied desired object and resource declarations;
- requested ownership, channel, and rights relationships; and
- proposal identity sufficient for deterministic reporting.

Proposed state never authorizes execution.

### Canonical sealed state

- canonical object identity;
- complete resource inventory and extent ownership;
- monitor, root, stack, and saved-state exclusion;
- domain/vCPU/root/stack/saved-state bindings;
- explicit channel endpoints and directional rights;
- initialization and activation phase; and
- one immutable configuration identity.

Only canonical sealed state carries authority inside the core.

### Derived enforcement state

- domain translation roots and mappings;
- active and pending domain bindings;
- translation-cache/fence state;
- current trusted-stack and saved-state selection; and
- deterministic authority and mapping reports.

Derived state must be reconstructable from, and no more permissive than,
canonical sealed state.

Model 0.2 does not add dynamic policy generations, delegation lineages,
runtime relabeling, or mutable grant caches. Those require later bounded
plans.

## Core phases

The model should distinguish:

```text
empty
  -> inventory bound
  -> proposal copied
  -> canonical validation complete
  -> sealed
  -> roots derived
  -> active

any invalid transition -> terminal failure
```

No domain may run before validation, sealing, and root derivation complete.
No failed or partially validated proposal may publish authority.

## Mechanism invariants

Model 0.2 must preserve and sharpen the Model 0.1 invariants:

1. **Canonical identity:** every trusted object reference resolves to one
   canonical object of the expected class.
2. **Inventory closure:** every assigned extent exists in the bounded platform
   inventory.
3. **Resource non-overlap:** private, shared, monitor, root, stack, and
   saved-state extents satisfy their required disjointness.
4. **Monitor exclusion:** no domain root maps monitor-owned state.
5. **Unique private ownership:** every private resource has exactly one
   declared owner.
6. **Explicit sharing:** all cross-domain storage is represented by an
   explicit channel with fixed endpoints and direction.
7. **Rights soundness:** every derived mapping right is a nonempty subset of
   the canonical rights for the exact domain, GPA, and frame.
8. **Binding atomicity:** domain, vCPU, root, VMID, trusted stack, and saved
   state are selected as one binding.
9. **Switch freshness:** target execution is blocked until required
   translation invalidation completes.
10. **Saved-state separation:** a domain transition may update only the
    source-owned saved state and may read only the target-owned saved state;
    neither domain can read or modify the other's private saved registers.
11. **Sealed-state authority:** proposed, guest, report, or derived mutable
    data cannot create or modify canonical authority after sealing.
12. **No direct policy mutation:** no future configuration or policy
    component may write roots, mappings, active bindings, or sealed authority
    directly.
13. **Fail-closed behavior:** malformed, incomplete, stale-phase, or
    invariant-violating input cannot publish partial authority or run a
    domain.

## Mechanism versus policy claims

Model 0.2 may support this claim:

> Every accepted configuration satisfies the modeled structural isolation
> invariants, and every modeled enforcement action is derived from and bounded
> by the accepted canonical state.

It must not claim:

> Every accepted configuration implements the operator's intended security
> policy.

The latter requires a policy specification and a proof or analysis connecting
that policy to the proposal. That evaluation belongs after Model 0.2.

## Supportable completion claim and required limit

After all exit criteria pass, the strongest planned statement is:

> Beryllium Architecture Model 0.2 machine-checks, for one fixed abstract
> single-hart two-domain instance, that accepted policy-neutral configuration
> proposals produce complete canonical sealed state and that modeled roots,
> transitions, and access enforcement are derived from and bounded by that
> state.

Required limit:

> Model 0.2 does not prove that an accepted proposal expresses an operator's
> intended security policy, or prove a Beryllium runtime, C/assembly
> refinement, compiler output, firmware, QEMU, K3 hardware, devices, multicore
> behavior, policy framework, composed security model, or full
> information-flow noninterference.

## Required artifacts and implementation status

The accepted implementation delivers:

1. this reviewed architecture contract;
2. a versioned diff from Model 0.1 state and operations;
3. an executable abstract state machine;
4. a restricted-C host validator, internally derived roots, and deterministic
   report path;
5. positive fixtures showing equivalent mechanism state independent of
   policy-source vocabulary;
6. adversarial fixtures for overlap, omission, direct-authority injection,
   wrong binding, excessive rights, partial publication, and invalid phase;
7. Rocq definitions and 23 bounded public obligations for the selected
   invariants;
8. a claim/assumption trace back to Model 0.1;
9. future C and assembly cut-point contracts; and
10. generated evidence and independently runnable open-tool gates.

The maintained `source-a` and `source-b` fixtures differ only in proposal
identity, neutral source vocabulary, and record order. Their canonical and
derived report sections compare exactly without normalization. Neither fixture
selects or executes TE, capabilities, RBAC, Rego, Cedar, or another policy
framework.

## Candidate proof obligations

At minimum:

- validation success implies inventory closure and required non-overlap;
- validation success implies complete ownership and binding;
- sealing is possible only after successful complete validation;
- failed validation cannot publish roots or runnable domains;
- canonical state cannot change after sealing;
- every derived root is sound with respect to canonical state;
- every mapping right is a subset of canonical authority;
- no proposal field can designate monitor-owned state as domain-accessible;
- transition and access behavior depend on canonical state, not on the
  proposal producer or source vocabulary;
- skipped invalidation prevents target entry;
- private and saved state remain separated; and
- explicit channels are the only modeled cross-domain storage path.

These are bounded abstract properties. They do not prove a future privileged C
or assembly implementation, compiler output, hardware, or full
noninterference.

## Failure behavior

Before activation, any structural error is terminal for that boot instance:

- no partial fallback configuration;
- no permissive default;
- no partially constructed or published root;
- no guest-visible recovery parser;
- no policy callback; and
- no domain entry.

After activation, Model 0.2 permits only the existing bounded domain-switch and
access operations. Runtime configuration replacement is outside scope.

## Non-goals

Model 0.2 does not:

- choose a protected workload or service;
- evaluate policy-framework usability or performance;
- compose capabilities with TE or another security model;
- define identities, roles, labels, classifications, or declassification;
- define dynamic delegation, revocation, relabeling, or policy update;
- provide a stable manifest encoding or public ABI;
- model a general VMM, scheduler, interrupt controller, timer, or SBI surface;
- model device assignment or DMA;
- implement or prove a hypervisor runtime;
- generalize to multicore; or
- authorize public release.

The existing capability, CAP+TE, and supervisory-policy documents remain
retained research inputs for later evaluation, not requirements for this
phase.

## Exit criteria

1. The Model 0.1 acceptance status and inherited assumptions are recorded.
2. Proposed, canonical, and derived state are represented separately.
3. Every authoritative field has one trusted owner and mutation phase.
4. Every acceptance rule has positive and adversarial automated coverage.
5. No untrusted producer can directly publish authority or enforcement state.
6. Every derived mapping and transition is bounded by canonical sealed state.
7. Equivalent canonical inputs behave independently of source-policy
   vocabulary.
8. All selected Rocq obligations close without hidden assumptions.
9. Claim and non-claim language matches generated evidence.
10. The complete open model/checker/proof/documentation gate passes.
11. Responsible-human review accepts the Model 0.2 boundary before a later
    runtime or security-model evaluation plan is approved. This occurred on
    2026-07-24. A bounded runtime-planning phase was subsequently selected,
    and its exact plan and fixed implementation profile were approved on
    2026-07-25.

## What follows Model 0.2

Model 0.2 acceptance does not automatically select a service or runtime.
Responsible-human direction selected preparation of a bounded single-hart
runtime plan on 2026-07-24. The accepted plan:

- preserves the accepted proposed/canonical/sealed/derived seam;
- uses one fixed QEMU/OpenSBI profile and two role-neutral synthetic VS
  domains;
- exposes C, assembly, G-stage, trap, context, and fence cut points;
- provides no Linux, service semantics, or guest-visible SBI; and
- was separately accepted and authorized for its exact fixed implementation
  profile on 2026-07-25.

Capabilities, TE, policy frameworks, supervisory policy, and protected-service
selection remain deferred. See
[`single-hart-runtime-plan.md`](single-hart-runtime-plan.md).
