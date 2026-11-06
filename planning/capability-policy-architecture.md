<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Capability mechanisms and holistic security policy

## Status and purpose

This document captures the 2026-07-22 analysis of how capability systems
relate to system-wide access control, information flow, privilege management,
and higher-level security policy.

It is research input, not an approved runtime architecture. It does not:

- select capabilities, Type Enforcement (TE), or a combined CAP+TE profile;
- change the ownership and explicit-channel baseline in
  [`architecture-model-0.1.md`](architecture-model-0.1.md);
- authorize a runtime policy engine, capability ABI, or new pathfinder; or
- transfer CHERI, seL4, or information-flow claims to Beryllium.

This material is retained for a later evaluation phase. Architecture Model
0.2 first designs the core hypervisor mechanism on policy-neutral terms; it
does not evaluate or integrate capability, TE, or holistic policy models.

The related
[`isolation-engine-policy-research.md`](isolation-engine-policy-research.md)
records the earlier CAP+TE hypothesis. The follow-on
[`supervisory-security-policy.md`](supervisory-security-policy.md) considers
how an engine-independent policy contract, Rego, code integrity, measurement,
and attestation could fit into a future hyperscale architecture.

## Core conclusion

Capabilities are not merely object-encapsulation machinery. A capability is an
unforgeable designation of an object together with authority to perform
operations on it. The current capability graph, its trusted roots, and the
rules for minting, derivation, transfer, attenuation, and revocation form an
access-control policy.

That policy is usually **extensional**: it records the authority that currently
exists. It does not necessarily provide an **intensional**, system-wide
language explaining why that authority should exist or which future authority
states are permitted.

| Policy view | Example | Natural representation |
| --- | --- | --- |
| Extensional authority | Domain A currently holds read authority to object O | Capability graph, CSpace, ownership/channel table |
| Intensional authorization | Subjects of type `reader_t` may read objects of type `shared_t` | TE, RBAC, ABAC, or another rule model |
| Information-flow policy | Secret-derived data must not reach a public sink without release authority | Label/flow model and declassification rules |
| Administrative policy | Principal P may delegate bounded authority but may not create a new root | Trust-management and lifecycle rules |

The distinction explains both the strength and the limit of capability
systems. A capability distribution can represent a static access matrix and
enforce least authority. A capability token by itself does not define the
desired distribution, future transitions, global flow constraints, or
administrative trust.

## What capability systems handle well

Capability systems naturally support:

- intentional object designation;
- positive authority without ambient namespace access;
- local checks at object invocation;
- monotonic attenuation of rights or bounds;
- explicit delegation when transfer paths are controlled;
- confused-deputy resistance when callers supply the authority to use;
- structural confinement through a bounded authority graph; and
- static reasoning about which subjects can reach which objects.

A complete capability model must include more than the token representation.
It also needs:

- trusted establishment of root authority;
- a holder and transfer model;
- derivation and no-amplification rules;
- revocation, generation, and object-reuse semantics;
- explicit treatment of capability-bearing IPC and memory; and
- initialization and update rules that preserve the authority invariant.

Without these rules, a collection of opaque handles is not a capability
security architecture.

## What capability possession does not settle

Capability possession alone does not naturally settle:

- global prohibitions on future delegation;
- identity, role, time, tenant, or environmental constraints;
- separation of duty and administrative approval;
- transitive information flow through an entity allowed to read one object
  and write another;
- declassification, endorsement, or release authority;
- global revocation across a delegation graph;
- policy changes, rollback, and object-lifecycle transitions;
- audit and accountability;
- resource exhaustion and denial-of-service policy; or
- covert and microarchitectural channels.

These properties can be implemented in a capability system through trusted
brokers, factories, revocable proxies, membranes, policy-bearing objects, and
carefully constructed graphs. Those components are the policy layer even when
there is no central policy language or policy decision point.

Capabilities are therefore not inherently insufficient for access control.
They are insufficient as a complete explanation of holistic security behavior
unless their construction, protocols, lifecycle, and global invariants are
also specified.

## Recurring composition architectures

### Policy compiled into a capability graph

A declarative system description is compiled into an initial capability
distribution. The kernel enforces the resulting graph, and trusted
initialization establishes it.

seL4 and capDL are the strongest relevant precedent. Their value is not that
capDL is a universal policy language, but that a static authority description
can be connected to integrity and information-flow reasoning under explicit
configuration assumptions.

This approach is most tractable when:

- the configuration is static or changes rarely;
- grant rights are tightly controlled;
- authority changes pass through a small trusted manager; and
- the system can validate that initialization matches the declared graph.

### Policy-controlled capability issuance

A policy or trust-management service decides which capabilities may be
created, attenuated, transferred, or revoked. Once issued, the capability
supports local object invocation without repeating every high-level identity
decision.

This pattern is common in capability-oriented services and distributed trust
systems. Its critical security boundary is issuance and transfer, not only
later object use.

### Independent capability and mandatory checks

An operation requires both valid capability authority and a separate mandatory
decision:

```text
operation_allowed =
  valid_designation
  AND sufficient_capability_rights
  AND mandatory_constraints_allow
```

A TE or other mandatory allow must never create designation or authority. A
capability must never override a mandatory denial.

This simple conjunction is not a complete composition proof. Capability
creation, transfer, relabeling, revocation, object reuse, and mapping
installation must also preserve the joint invariant. Capability-bearing IPC
is itself an authority and information-flow operation.

### Separate research hypothesis: TE over capability lifecycle

Partial responsible-human review on 2026-07-24 asked the project to revisit
applying TE to capabilities themselves. This is a distinct future research
hypothesis, not a selected policy architecture and not a novelty claim.

At least four models must remain separate:

| Model | Mandatory decision | Current disposition |
| --- | --- | --- |
| Capability plus object TE | A valid capability designates an object; TE independently checks subject type, object type, class, and actual use | Conservative baseline if both capability and TE triggers fire |
| TE over capability records or slots | TE additionally controls possession, receipt, delegation, attenuation, invocation, or revocation of a monitor-held capability record | New Beryllium research target with close precedents and unresolved human semantics |
| Typed or sealed capability | An object-system or CHERI type controls valid interpretation, unsealing, or entry | Useful mechanism, but not automatically TE or MAC |
| Policy compiled to an initial graph | A compiler emits the initial CSpace/ownership/channel graph | capDL/seL4 precedent; does not by itself constrain later authority transitions |

The ordinary use rule remains:

```text
use(subject, capability, operation) =
  holder_binding_is_valid
  AND capability_is_active_and_current
  AND capability_designates_the_canonical_object
  AND capability_rights_cover(operation)
  AND object_TE_allows(subject_type,
                       object_type,
                       object_class,
                       operation,
                       policy_generation)
```

TE never resolves the object or creates the capability. Capability possession
never overrides an object-TE denial.

A capability-lifecycle TE profile would add trusted monitor metadata such as:

```text
capability_type(capability_record)
holder_slot(capability_record)
capability_generation
derivation_parent
```

and distinct mandatory operations:

```text
receive
hold
delegate
attenuate
invoke
revoke
```

Illustrative transfer semantics are:

```text
transfer(sender, receiver, parent, child) only if:
  sender holds parent
  AND parent includes delegate authority
  AND child rights and bounds are subsets of parent
  AND TE allows sender_type -> capability_type : delegate
  AND TE allows receiver_type -> capability_type : receive
  AND receiver/object/effective-rights remain inside the immutable ceiling
```

Invocation must still check the canonical object's TE decision. Checking only
`capability:receive` or `capability:invoke` would permit an authority-laundering
path in which a recipient uses a capability to reach an object that ordinary
object TE would deny.

This model has close practical precedents:

- SELinux defines an `fd` class with `use`, showing that mandatory policy may
  govern use of a descriptor-like authority separately from underlying file
  permissions.
- Xen XSM/FLASK mediates event-channel and grant create, send, map, copy, and
  transfer operations, showing TE over authority-bearing inter-domain
  mechanisms.
- Capsicum capability mode composes rights-limited descriptors with FreeBSD's
  independent MAC framework.
- seL4/capDL compiles policy into an initial capability graph and proves
  properties relative to that configured authority.
- KeyKOS-family typed keys and CHERI sealing provide typed invocation
  mechanisms, but do not by themselves implement a TE source/target/class
  matrix.
- HiStar, Flume, and Asbestos show that mandatory labels and capability-like
  release or label-change privileges can coexist.

No verified primary source found in the bounded review establishes a general
model named "Type Enforcement over Capabilities." The precedents show that
most ingredients and several transition checks already exist. Any publishable
contribution would require a precise transition calculus, proof, and
implementation result rather than a terminology or conjunction claim.

The model must reject at least:

1. **TE creates designation:** an object-use TE allow installs a mapping when
   the subject holds no valid capability.
2. **Capability defeats TE:** an RW capability or stale mapping permits an
   operation denied by the current object policy.
3. **Transfer laundering:** a recipient passes `capability:receive` and then
   invokes an object whose type it may not use.
4. **Attenuation recovery:** a child drops `write` but retains mint or
   delegation authority that can recover RW access.
5. **Revocation race:** metadata is revoked while a descendant, CPU mapping,
   translation-cache entry, or DMA mapping remains usable.
6. **Relabel race:** object or capability policy changes while an old
   generation decision or mapping remains active.
7. **Sealing misconception:** a valid sealed or sentry capability is copied to
   an unauthorized holder because no outer possession/transfer policy exists.
8. **Compile-only escape:** the initial graph is correct but later mint or
   transfer operations bypass the transition policy.

Candidate proof obligations are:

- every successful use requires both valid designation and mandatory allow;
- capability derivation never amplifies bounds, rights, lifecycle authority,
  or effective TE authority;
- subject, object, object type, capability type, class, operation, holder, and
  generations are monitor-derived;
- receipt, possession, transfer, invocation, relabel, and revocation preserve
  the immutable authority ceiling;
- relabel and policy activation are atomic with decision and mapping
  generation changes;
- revocation denies stale capabilities, descendants, cached decisions, CPU
  mappings, and DMA mappings before reuse;
- software CSpace and any later CHERI backend refine the same abstract
  transition semantics; and
- authorization safety remains separate from information-flow and
  declassification proofs.

Human policy input is indispensable. Before any bounded model, the responsible
human must decide:

1. Does the mandatory label attach to the canonical object, one capability
   record, one holder slot, or one transfer edge?
2. May two capabilities designating the same object have different mandatory
   types, and what prevents label laundering?
3. Does policy govern possession, receipt, invocation, or all three?
4. Is transfer a copy, move, attenuation, delegation, or re-delegation?
5. Who may mint roots, relabel, revoke, or authorize declassification?
6. Which policy generation governs an in-flight transfer and already
   installed mapping?
7. What revocation latency and availability loss are acceptable?
8. What concrete mandatory denial cannot be represented with ownership,
   directional channels, object separation, or capability attenuation?

The default Beryllium composition continues to keep policy context outside the
capability representation. A future lifecycle-TE experiment may use separate
monitor-held `capability_type` metadata, but must not fuse caller-controlled
labels into a guest handle or CHERI pointer.

### Labels with capability-like privileges

Asbestos, HiStar, and Flume demonstrate another composition. Mandatory labels
control information flow, while special privileges permit bounded label
changes, endorsement, or declassification.

This is evidence that capability-like authority and mandatory flow rules can
coexist. It also exposes difficult questions about delegating release
authority, tracking dynamic labels, and proving that authorized
declassification cannot be abused.

## Separate security properties

An operation-level authorization decision is only one part of a security
argument:

```text
operation authorization =
  designation AND rights AND mandatory constraints

reachable-state safety =
  every authority transition preserves the policy invariant

information-flow security =
  permitted execution traces satisfy confidentiality and integrity rules
```

Access control can prevent a subject from opening a channel. It does not by
itself show that an authorized subject cannot copy information between two
open channels. Information-flow security therefore requires a separate
flow/trace model, explicit release edges, and assumptions about timing and
other covert channels.

Privilege management similarly requires transition semantics. A system must
state:

- who may create or designate an object;
- who may delegate each right and to whom;
- whether transfer preserves holder binding or mandatory constraints;
- how authority is revoked;
- how stale references are rejected before object reuse; and
- which policy generation governs each operation.

## Candidate layered architecture

A coherent policy-driven system can separate the layers without treating any
one policy mechanism as universal:

```text
High-level policy
  TE / MLS / roles / attributes / flow / administration
                         |
                  compile or validate
                         v
Canonical authority state
  ownership / channels / capabilities / labels / generations
                         |
                       refine
                         v
Enforcement
  CHERI or software CSpaces / G-stage / IOMMU / call gates
```

The high-level layer states intent and valid transitions. The canonical state
is the reviewable, measurable authority instance. Enforcement mechanisms
realize that state at their respective boundaries.

A dynamic policy service may propose changes, but a small trusted authority
manager should independently validate each change against an immutable
ceiling. Failure or unavailable policy service must not expand authority.

The architecture must define:

- the normative subject, object, operation, and flow vocabulary;
- policy precedence and conflict handling;
- the mapping from intensional rules to extensional authority;
- lifecycle and administrative transitions;
- the relationship between CPU, memory, device, and call authority;
- audit and attestation identities; and
- refinement obligations from policy through concrete enforcement.

## Implications for Beryllium

The current Beryllium trigger-gated direction remains appropriate:

1. Use static ownership and explicit channels for Model 0.1.
2. Add software capabilities only when a concrete use case requires runtime
   designation, attenuation, delegation, holder transfer, or revocation.
3. Add TE only when an independently mandatory denial cannot be represented
   adequately by object separation, channel direction, or capability
   attenuation.
4. If both triggers fire, keep capability and mandatory policy independently
   observable.
5. Keep labels and policy context out of the capability representation by
   default. Any future capability-record TE label remains separate,
   monitor-held metadata with its own accepted transition semantics.
6. Treat capability transfer, policy generation, and mapping installation as
   first-class modeled transitions.
7. Prove information-flow properties separately from local authorization.

The capDL-inspired canonical security manifest is a suitable future place to
describe the instantiated authority graph and its policy generation. Rich
policy authoring or evaluation does not belong in a small HS enforcement
core. Model 0.1 deliberately has no stable manifest encoding, and this
research does not select one.

## Supportable conclusion and required limit

**Supportable conclusion:** capability graphs provide a complete and powerful
representation of current positive authority, while higher-level rule,
flow, administrative, lifecycle, and evidence models can define and constrain
how that graph is created and changed.

**Required limit:** no generally accepted architecture currently unifies
capabilities, MAC, information flow, privilege administration, lifecycle,
audit, and assurance. Neither capabilities nor TE should be presented as a
complete system security policy by itself.

## References

- Lampson,
  [Protection](http://web.mit.edu/Saltzer/www/publications/protection/).
- Watson et al.,
  [CHERI FAQ](https://www.cl.cam.ac.uk/research/security/ctsrd/cheri/cheri-faq.html).
- Kuz et al.,
  [capDL: A Language for Describing Capability-Based Systems](https://www.usenix.org/conference/apsys2010/capdl-language-describing-capability-based-systems).
- Sewell et al.,
  [seL4 Enforces Integrity](https://trustworthy.systems/publications/nicta_full_text/4709.pdf).
- Murray et al.,
  [seL4: from General Purpose to a Proof of Information Flow Enforcement](https://www.ieee-security.org/TC/SP2013/papers/4977a415.pdf).
- Spencer et al.,
  [The Flask Security Architecture](https://www.usenix.org/conference/8th-usenix-security-symposium/flask-security-architecture-system-support-diverse-security).
- SELinux reference policy,
  [`fd` class and access vectors](https://github.com/SELinuxProject/refpolicy/blob/master/policy/flask/access_vectors).
- Linux,
  [SELinux class map](https://github.com/torvalds/linux/blob/master/security/selinux/include/classmap.h).
- Xen Project,
  [XSM/FLASK](https://xenbits.xenproject.org/docs/unstable/misc/xsm-flask.txt).
- Xen Project,
  [FLASK grant and event interfaces](https://github.com/xen-project/xen/blob/master/tools/flask/policy/modules/xen.if).
- Watson et al.,
  [Capsicum](https://www.usenix.org/legacy/events/sec10/tech/full_papers/Watson.pdf).
- Hardy,
  [The KeyKOS Architecture](https://doi.org/10.1145/858336.858337).
- Watson et al.,
  [CHERI: A Hybrid Capability-System Architecture](https://doi.org/10.1109/SP.2015.9).
- Zeldovich et al.,
  [Making Information Flow Explicit in HiStar](https://www.usenix.org/legacy/event/osdi06/tech/full_papers/zeldovich/zeldovich.pdf).
- Krohn et al.,
  [Information Flow Control for Standard OS Abstractions](https://pdos.csail.mit.edu/papers/flume-sosp07.pdf).
