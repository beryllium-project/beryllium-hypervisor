<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Isolation engine and CAP+TE research direction

## Status and purpose

This document preserves the architecture and policy research discussion that
followed the fifth Helium pathfinder experiment on 2026-07-20. It is
curated input for cross-variant assessment, finer-grained planning, and later
decision records.

Disposition on 2026-07-20: the completed comparison in
[`pathfinder-comparison.md`](pathfinder-comparison.md) selects a small HS
isolation engine, VS service domains, and an ownership-first static baseline
as the preferred general direction. Capabilities and TE remain trigger-gated
extensions, and the broader CAP+TE, multicore, and VBS material below remains
research input rather than selected implementation.

Sequencing update on 2026-07-24: responsible-human review accepted the
policy-neutral core mechanism work in
[`architecture-model-0.2.md`](architecture-model-0.2.md). This research is
still not a selected evaluation phase. Protected-service selection,
policy-framework evaluation, and security-model composition remain deferred.
The selected bounded single-hart runtime-planning phase explicitly excludes
them; a later phase and approved plan must authorize any such evaluation.

It does **not**:

- select the Beryllium MVP architecture;
- select Type Enforcement, capabilities, or a combined policy profile;
- authorize a multicore, VBS-like, CHERI, or enclave implementation;
- add a sixth pathfinder experiment;
- claim that Helium proves arbitrary hypervisor or VM isolation; or
- replace the required broad security-monitor review.

The following previously recorded directions remain in force:

- RISC-V is primary.
- Beryllium is hypervisor-first and retains HS privilege before Linux runs.
- Policy/mechanism separation is selected.
- The first proof configuration is single-hart.
- The first multicore model uses static CPU ownership, per-hart fast-path
  state, and one serialized global control path.
- Restricted C and Rocq remain the initial core/proof direction.
- CHERI and RISC-V CHERI alignment must be assessed explicitly.
- Type Enforcement remains an option, not a selected architecture.

## Questions preserved from the discussion

The discussion considered:

1. the size cost of the fixed TE pathfinder relative to the minimal RISC-V
   implementation;
2. whether formal verification can extend to the TE mechanism;
3. whether a small TE-capable monitor can support hypervisor decomposition
   into security domains;
4. whether the same model can isolate VMs and control permitted information
   flow between them;
5. whether it leaves a path to a VBS-style secure-kernel or enclave layer that
   protects critical functions and secrets from a compromised normal kernel;
6. the simplest credible multi-hart HS-mode isolation-engine architecture;
7. whether capabilities and TE should be layered, fused, or composed through a
   FLASK-like policy/mechanism split;
8. how MLS/MCS, RBAC, and identity-based access control could fit later; and
9. how one abstract capability model could use CHERI hardware when available
   and protected software capability tables when it is not.

## Full session-text references

The complete prompts and assistant outputs that led to this synthesis are
retained as research provenance:

1. [TE pathfinder assessment, formal verification, hypervisor decomposition,
   VM flow, and VBS suitability](session-analysis-te-vbs-2026-07-20.md)
2. [Simplest multi-hart HS isolation-engine
   direction](session-analysis-isolation-engine-2026-07-20.md)
3. [CAP+TE composition, FLASK, CHERI, and software capability
   backends](session-analysis-cap-te-cheri-2026-07-20.md)

The [transcript index](session-analysis-transcripts-2026-07-20.md) records
provenance and status. These verbatim outputs preserve rationale; the curated
sections below remain the maintained synthesis and do not convert hypotheses
into selected decisions.

Follow-on analysis is maintained in:

1. [Capability mechanisms and holistic security
   policy](capability-policy-architecture.md), which distinguishes capability
   graphs, rule policy, reachable-state safety, and information flow.
2. [Supervisory security policy and attestable
   enforcement](supervisory-security-policy.md), which evaluates Rego,
   signed policy manifests, code integrity, attestation, confidential
   computing, and alternative policy models.

Both remain non-authorizing research input.

## Pathfinder size evidence

The retained evidence uses one consistent selected-target source category:
target C, assembly, public headers, and linker script. It excludes host tests,
documentation, and report tools.

| Variant | Selected target SLOC | Loaded binary |
| --- | ---: | ---: |
| Minimal ownership | 1,608 | 12,288 bytes |
| Minimal software capability | 1,637 | 12,288 bytes |
| Minimal capability plus flow | 1,651 | 12,288 bytes |
| Fixed two-subject TE | 2,253 | 16,384 bytes |

The TE variant adds:

- 645 lines over minimal ownership (40.1%);
- 616 lines over minimal software capability (37.6%);
- 602 lines over capability plus flow (36.5%); and
- one 4 KiB loaded region (33.3%).

`include/he/te.h`, `src/te.c`, and `src/policy/te.c` account for 497 lines.
The complete delta is not pure policy overhead: it also includes the second
G-stage root, second subject, different payload, fenced root/stack switch,
store-fault path, policy-to-PTE checks, and changed evidence surface.

Line count and binary size measure review surface; they do not establish a
security property.

## Working isolation-engine hypothesis

### Minimal privilege shape

The simplest credible decomposition hypothesis is:

```text
M-mode
  minimal firmware / OpenSBI / measured handoff

HS-mode on every active hart
  Beryllium isolation engine
    trap entry and return
    domain and vCPU identity
    frame ownership
    G-stage root ownership
    hart ownership
    explicit shared-channel enforcement
    compact capability and mandatory-policy checks
    later interrupt and IOMMU ownership

VS-mode
  untrusted Linux management/VMM domain
  protected security domain
  later I/O and service domains
```

The isolation engine, rather than Linux or a richer VMM, must exclusively own
every security-relevant transition. Rich policy authoring, orchestration,
device emulation, drivers, filesystems, networking, and administration remain
outside HS.

This is conceptually similar to the publicly described Nitro Isolation Engine
pattern: a small separation/isolation kernel owns security-relevant VM state
and exposes a narrow interface to a larger resource-management environment.
Beryllium should treat that work as methodology and comparison evidence. The
reviewed AWS material had not yet published the complete engine source and
project proof development.

### Why the monitor executes on every hart

A hart executing VS code has local HS trap state, `HGATP`, VMID, trusted stack,
and translation-cache obligations. Therefore a single dedicated monitor hart
cannot replace the local HS enforcement path on the other harts.

A dedicated control hart may later serialize rare global operations, but it is
not the simplest first design. It adds:

- an inter-hart request queue;
- IPI delivery and acknowledgement;
- an availability dependency;
- additional shared state; and
- another protocol to specify and prove.

The initial monitor code should instead execute in HS on every active hart,
with private per-hart state and no steady-state global mutation.

### Smallest multicore experiment

The next candidate experiment after planning review would use two harts and
two statically configured VS domains:

| Hart | Fixed VS assignment |
| --- | --- |
| 0 | Untrusted Linux management/VMM domain |
| 1 | Protected security-service domain |
| Remaining harts | Parked |

The boot hart would:

1. validate a fixed canonical manifest;
2. initialize the complete frame-ownership map;
3. construct immutable G-stage roots;
4. initialize per-hart trusted stacks and state;
5. bind one root/domain to each active hart;
6. publish the immutable configuration through a boot barrier; and
7. release the secondary hart into its assigned VS context.

After release:

- no domain creation or destruction occurs;
- no frame is reassigned;
- no root is edited;
- no VM migrates;
- no vCPU is overcommitted;
- no shared run queue exists;
- no device or DMA is present;
- interrupts and timers remain absent or strictly bounded; and
- communication uses only a fixed directional shared page.

This deliberately avoids remote invalidation, concurrent revocation, frame
reuse, and lifecycle races in the first multicore proof.

### Per-hart and global state

Per-hart trusted state should contain:

- current domain/vCPU identity;
- trusted trap stack;
- saved vCPU registers;
- active root and VMID;
- local exit reason;
- bounded interrupt/timer state when introduced; and
- no pointer to guest-controlled policy data.

Initially immutable global state should contain:

- validated domain and hart assignments;
- complete frame ownership;
- root physical addresses and VMIDs;
- explicit shared-channel records;
- immutable capability roots and policy ceiling; and
- monitor, stage-table, and trusted-stack exclusion ranges.

The first dynamic multicore stage may add one bounded global control lock for:

- lifecycle;
- capability derivation/revocation;
- grant and ownership transfer;
- policy-generation activation;
- root/IOMMU updates; and
- global invalidation.

No lock is held across guest execution or an untrusted-domain call. Fine-grain
locking, work stealing, concurrent policy updates, and shared scheduling remain
deferred.

### Dynamic mapping protocol

When later required, one serialized operation should perform:

```text
acquire global control lock
  -> validate ownership, capability, and mandatory policy
  -> update every affected G-stage/IOMMU mapping
  -> send invalidation requests to affected harts
  -> each hart executes the required local fence
  -> collect acknowledgements
  -> publish the new generation or permit frame reuse
release global control lock
```

Unique VMIDs reduce unnecessary invalidation but do not remove fencing on VMID
reuse, stale mappings, or ownership transfer.

### Core isolation invariants

Candidate primary invariants are:

1. every private frame has at most one owning security domain;
2. no VS root maps monitor code, data, stage tables, or trusted stacks;
3. every PTE permission is a subset of validated authority;
4. each hart enters only its assigned domain and root;
5. vCPU state is disjoint between domains;
6. every shared page is represented by one explicit channel with directional
   rights;
7. untrusted management requests cannot directly mutate ownership or roots;
8. no frame is reused until all affected translations and DMA mappings are
   invalidated; and
9. failure before atomic publication leaves the old authority state active or
   terminates fail-closed.

## VBS-style future option

### Security shape

The isolation-engine hypothesis preserves a route to a VTL-like system:

```text
normal context
  Linux or guest kernel; treated as compromised

secure context
  secure service, secure kernel subset, or enclave

HS isolation engine
  owns secure pages, vCPU/register state, roots, entry gates, and shared calls
```

The secure context must execute with a monitor-selected root or in a separate
protected VM/security domain. Merely assigning labels to functions that still
execute in the normal kernel address space cannot protect them from that
kernel.

### Required boundary

To protect critical functions and secrets from a compromised host or guest
kernel:

- secure code, data, stack, and saved registers are never mapped into the
  normal context;
- only HS can select the secure root and entry point;
- entry/return validates the complete transition and sanitizes register state;
- normal-kernel input is untrusted and structurally bounded;
- communication uses explicit shared call buffers with directional rights;
- secret-bearing output requires explicit release/declassification policy;
- DMA, interrupt, debug, paging, crash-dump, migration, and reset paths
  preserve the boundary;
- secure boot/measurement identifies the monitor, secure image, manifest, and
  policy;
- key derivation/sealing and anti-rollback are tied to that identity; and
- denial of service by the normal kernel remains explicit unless a stronger
  scheduling profile is added.

### Candidate initial use cases

The model appears most plausible for narrow services with small state and
interfaces:

- key and credential vaults;
- code-integrity or measurement decisions;
- cryptographic operations;
- security-policy decisions;
- protected update/rollback state; and
- integrity-sensitive result checking.

Moving arbitrary state-heavy or latency-sensitive kernel functions behind a
security-domain call gate may create excessive shared state, confused-deputy
risk, and transition overhead.

### Meaning of "better than VBS"

No superiority claim is currently supportable. Candidate assessment criteria
for a future comparison are:

- Linux is untrusted from its first instruction;
- the isolation engine and proof artifacts are fully open;
- the HS TCB and interfaces are smaller and explicitly measured;
- all channels and declassification are represented in one canonical manifest;
- the policy and authority ceiling are attestable;
- architecture assumptions are explicit and profile-neutral;
- proofs cover the selected implementation/configuration rather than only an
  abstract policy; and
- the design remains usable on ordinary RISC-V hardware while preserving a
  migration path to CHERI.

## Capability and TE composition

### Recommendation under evaluation

The working hypothesis is to **compose** capabilities and TE rather than fuse
them into one authority representation.

| Layer | Responsibility |
| --- | --- |
| Capability | Designate a canonical object and provide bounded, derived authority |
| TE | Apply a mandatory source-type to target-type policy ceiling |
| Enforcement | Encode the intersection in G-stage/IOMMU mappings and call gates |

Illustrative composition:

```text
cap_ok =
  valid
  and held by current subject
  and active
  and derived from a root
  and rights cover the operation
  and generation is current

te_ok =
  allow(current_subject.type,
        resolved_object.type,
        resolved_object.class,
        actual_operation)

allow = cap_ok and te_ok
effective_rights = capability_rights intersect TE_access_vector
```

Required composition rules:

- a TE allow never mints authority or resolves an object;
- a capability never overrides a TE denial;
- capability possession never authorizes relabeling;
- the subject comes from monitor-held current-domain state;
- the object and its type/class come from the canonical object resolved by the
  capability;
- the caller cannot supply trusted labels or an operation different from the
  actual enforcement hook;
- mapping rights are a subset of both decisions; and
- policy or capability failure denies.

This may be called a CAP+TE **profile or formal composition model**. It should
not create a new fused "TE capability" whose representation mixes authority,
labels, and policy in ways that obscure independent proof obligations.

### Additional research: TE over capability lifecycle

Partial responsible-human review asked whether TE should also govern the
capability as an authority-bearing object. This does not change the
conservative use-time composition above.

A separately modeled profile could apply mandatory rules to:

- receiving or holding one monitor-resident capability record;
- delegation and attenuation;
- invocation through the capability;
- revocation or relabel authorization; and
- transfer into a differently typed holder slot.

The capability record's type would be separate monitor-held metadata, not a
guest label embedded in an opaque handle or CHERI pointer. Invocation would
still require ordinary object TE; capability-record TE alone must not launder
access to a forbidden target.

SELinux `fd:use` and Xen FLASK grant/event mediation are close precedents.
CHERI sealing and sentries are typed invocation mechanisms, not TE by
themselves. No novelty claim is supported without a narrower literature review
and a new formal result.

The complete candidate semantics, counterexamples, proof obligations, and
human policy questions are maintained in
[Capability mechanisms and holistic security policy](capability-policy-architecture.md#separate-research-hypothesis-te-over-capability-lifecycle).
This research remains outside the selected single-hart runtime plan.

### FLASK-like split

FLASK supplies a useful architectural pattern:

1. an object manager resolves the operation and target;
2. enforcement hooks identify source, target, class, and requested access
   vector;
3. a security server evaluates mandatory policy; and
4. the object manager enforces the result.

For Beryllium, capability validation belongs in the trusted object
manager/isolation mechanism. A compact FLASK-like security server may evaluate
TE from canonical security IDs. The enforcement point intersects both.

The initial implementation should use offline-compiled, immutable, bounded
tables. It should not add:

- a rich policy parser in HS;
- runtime-selectable policy modules;
- an access-vector cache;
- dynamic policy load;
- policy-service availability dependencies; or
- guest-controlled security contexts.

If an access-vector cache is later justified, its key must include source SID,
target SID, class, and policy generation. Capability generation, holder,
lineage, and revocation checks remain separate and current on every use.

### Independent observability

A composition test must make each side independently decisive:

- a subject may hold an RW capability while TE denies write;
- a subject may receive a TE allow but hold no capability designating the
  object; and
- success occurs only when capability and TE both allow.

Encoding identical rights in both mechanisms without such cases would not
demonstrate composition.

### Future policy dimensions

The decision interface should remain extensible to:

```text
capability
AND TE
AND MLS/MCS constraints
AND role/transition constraints
AND identity/administrative constraints
```

MLS/MCS, RBAC, and identity-based access control are deferred. They should
extend subject/object security contexts and policy constraints, not be embedded
into capability provenance or pointer representation.

## CHERI and non-CHERI capability backends

### One abstract capability model

Define one representation-independent authority model containing at least:

- canonical object;
- holder/capability-space slot;
- bounds or resource extent;
- maximum rights;
- root and derivation parent;
- active generation;
- sealing/invocation type where applicable;
- revocation lineage; and
- immutable authority ceiling.

Required abstract properties include:

- root authority established only during trusted initialization;
- no forgery through untrusted input;
- monotonic rights and bounds attenuation;
- no authority amplification during transfer;
- intentional designation of the actual object;
- stale-generation denial;
- explicit invocation and sharing; and
- revocation before object/frame reuse.

### Ordinary non-CHERI hardware

Use a protected per-domain capability space:

```text
opaque slot + generation
  -> HS-private capability record
     { object, rights, parent/root, generation, active }
```

The guest-visible value is a handle and identifier. Authority comes from the
validated HS table, current-domain binding, lineage, and rights checks. It must
be called a **software capability** or **capability handle**, not an emulated
CHERI capability.

A table-backed design is preferred initially over cryptographic bearer tokens
because it makes holder binding, revocation, generation changes, audit, and
formal modeling more direct.

Software capabilities do not provide:

- tagged pointer integrity;
- bounds checked on ordinary C loads/stores;
- CHERI provenance or intentionality enforced by hardware;
- sealed hardware entry capabilities;
- temporal memory safety; or
- protection from memory corruption inside trusted HS C.

### CHERI hardware

A CHERI backend may use:

- tagged and bounded capabilities for monitor-internal object references;
- monotonic architectural permissions;
- sealed capabilities for protected entry or opaque object handles; and
- CHERI-aware C compartments inside the trusted monitor.

A protected object table may remain necessary for:

- TE labels and security IDs;
- lifecycle and ownership;
- policy/capability generations;
- revocation and frame reuse;
- VM/vCPU/device metadata;
- audit and attestation identity; and
- compatibility with the non-CHERI backend.

CHERI capabilities do not replace G-stage VM isolation or IOMMU/IOPMP DMA
isolation. A future CHERI virtualization profile must also preserve tags and
capability state across vCPU context, guest memory, sharing, paging, DMA,
migration, and attestation.

### Refinement goal

Both concrete backends should refine the same abstract model:

```text
Abstract capability semantics
  <- protected software capability-space implementation
  <- CHERI tagged/sealed implementation
```

The claim should be semantic compatibility where proved, not equivalence
between software records and CHERI architectural capabilities.

## Formal-verification direction

### Fixed TE mechanism

The current TE mechanism is a favorable bounded proof target because it has:

- fixed finite arrays;
- no allocation or recursion;
- one-way initialization/sealing;
- deterministic exact-key rule matching;
- one-rule-covers-all-requested-rights semantics; and
- default denial for malformed or absent state.

Candidate Rocq theorems:

- unsealed or invalid state never authorizes;
- sealing succeeds only for complete valid labels;
- API operations cannot relabel after seal;
- authorization is equivalent to one exact valid covering rule;
- writer shared RW and reader shared R are exact;
- cross-private `open`, read, and write are denied; and
- policy-derived PTE rights are a subset of the allow vector.

These theorems alone would not prove that arbitrary trusted C cannot mutate the
public state structure.

### CAP+TE composition

Candidate generic theorems:

- effective rights are a subset of capability rights;
- effective rights are a subset of the TE access vector;
- TE cannot create designation or authority;
- capability possession cannot bypass mandatory policy;
- attenuation cannot amplify effective rights;
- transfer to a differently typed subject may only preserve or reduce
  effective rights;
- stale or revoked capabilities deny even with a TE allow;
- TE policy-generation changes cannot reactivate stale capabilities; and
- every installed mapping is bounded by the composed decision.

### End-to-end progression

1. Prove the abstract fixed TE semantics.
2. Prove abstract capability semantics and CAP+TE composition.
3. Prove the canonical static manifest instantiates both correctly.
4. Refine the TE and software-capability C to the abstract model.
5. Prove policy/capability-to-PTE construction.
6. Connect exact transition/root-switch wrappers and C cut points.
7. Prove single-hart noninterference modulo explicit channels.
8. Prove the static two-hart model using per-hart state separation.
9. Add refinement from serialized dynamic control operations to atomic
   abstract transitions.
10. Add IOMMU/interrupt/device obligations only after CPU/memory isolation.

Compiler, firmware, emulator, hardware, and unproved C/assembly remain explicit
assumptions until connected by separate evidence.

## Candidate staged work, not approved implementation

### A. Cross-variant assessment

- Compare ownership, capability, capability-plus-flow, and direct TE evidence.
- Separate application/two-root cost from policy-decision cost.
- Identify concrete use cases requiring mandatory policy rather than simpler
  ownership/capability constraints.

### B. Abstract CAP+TE model

- Define the representation-independent capability semantics.
- Reproduce independent capability and TE denials.
- Prove rights-intersection and non-amplification properties.
- Generate an auditable authority/policy graph.

### C. Static two-hart isolation model

- One management domain and one protected domain.
- Immutable frame/root/hart assignments.
- One directional shared page.
- No runtime lifecycle or mapping mutation.
- Per-hart transition and cross-hart noninterference proof.

### D. VTL-like transition model

- Normal and secure contexts with distinct roots and saved state.
- Exact controlled entry/return.
- Explicit shared call buffer.
- Hostile normal-kernel tests.
- No key/attestation claim until measured launch is modeled.

### E. Serialized dynamic control

- One global control lock.
- Capability/grant/revoke transitions.
- Policy generations.
- Remote G-stage invalidation and acknowledgement.
- Frame reuse only after completion.

### F. Device and DMA isolation

- Interrupt ownership/routing.
- IOMMU and K3 IOPMP mappings.
- Reset and fault containment.
- Cache/coherency obligations.

Each stage requires a separate approved plan and claim boundary.

## Decision questions for later planning

1. Is the permanent HS core an isolation engine only, with Linux/VMM resource
   management entirely in VS?
2. Which operations are essential in the first narrow isolation-engine API?
3. Is a two-hart immutable configuration sufficient for the first multicore
   assurance target?
4. When does a dedicated control hart justify its IPI/protocol cost?
5. Is frame ownership the primary mechanism, with capabilities designating
   transitions and TE supplying a mandatory ceiling?
6. Which concrete use case needs TE beyond capability attenuation?
7. Should policy remain completely static for the first product profile?
8. What revocation semantics can be shared by software and CHERI backends?
9. Which CHERI properties apply only inside the monitor, and which should cross
   a guest/domain ABI?
10. What secure-service use case provides a persuasive VBS-style demonstration
    without importing a large secure-kernel TCB?
11. Which firmware, PMP/ePMP, debug, boot, and measurement assumptions remain
    above the HS isolation engine?
12. Which information flows are intentional, directional, and subject to
    explicit release/declassification?

## Primary references

Accessed 2026-07-20:

- AWS,
  [Nitro Isolation Engine: formally verifying the hypervisor in the AWS Nitro
  System](https://aws.amazon.com/blogs/compute/aws-nitro-isolation-engine-formally-verifying-the-hypervisor-in-the-aws-nitro-system/).
- Amazon Science,
  [EC2's formally verified isolation engine](https://www.amazon.science/blog/ec2s-formally-verified-isolation-engine-provides-mathematical-assurance-of-virtual-machine-isolation).
- AWS,
  [Nitro Isolation Engine whitepaper](https://d1.awsstatic.com/onedam/marketing-channels/website/aws/en_US/whitepapers/compliance/nitro-isolation-engine-whitepaper.pdf).
- Microsoft,
  [Virtualization-based security enclaves](https://learn.microsoft.com/en-us/windows/win32/trusted-execution/vbs-enclaves).
- Microsoft,
  [Windows silicon-assisted security](https://learn.microsoft.com/en-us/windows/security/book/hardware-security-silicon-assisted-security).
- RISC-V International,
  [Ratified Hypervisor Extension](https://docs.riscv.org/reference/isa/priv/hypervisor.html).
- Spencer et al.,
  [The Flask Security Architecture](https://www.usenix.org/conference/8th-usenix-security-symposium/flask-security-architecture-system-support-diverse-security).
- SELinuxProject,
  [SELinux Notebook: Type Enforcement](https://github.com/SELinuxProject/selinux-notebook/blob/main/src/type_enforcement.md).
- Xen Project,
  [XSM/FLASK configuration and model](https://xenbits.xenproject.org/docs/unstable/misc/xsm-flask.txt).
- CTSRD,
  [CHERI project](https://www.cl.cam.ac.uk/research/security/ctsrd/cheri/).
- RISC-V,
  [RISC-V CHERI specification repository](https://github.com/riscv/riscv-cheri).
- CTSRD,
  [CHERI RISC-V Sail model](https://github.com/CTSRD-CHERI/sail-cheri-riscv).
- David Chisnall,
  [Identifiers are not capabilities](https://cheriot.org/cheri/philosophy/2025/01/19/capabilities-not-identifiers.html).
- seL4,
  [Verified configurations](https://docs.sel4.systems/projects/sel4/verified-configurations.html).
