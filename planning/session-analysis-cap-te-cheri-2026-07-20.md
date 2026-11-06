<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Transcript: CAP+TE, FLASK, and CHERI backends

## Provenance and status

- Date: 2026-07-20
- Session: `90e28972-e41b-41ee-8432-420c6cdbaabd`
- Turn: 8
- Assistant: GitHub Copilot CLI, GPT-5.6 Sol
- Status: verbatim research input; not an approved architecture or claim

## User prompt

<!-- VERBATIM USER START -->

also, are you suggesting we layer TE on top of capabilities as a general purpose policy mechanism? or should we consider a new TE+CAP model? or compose them via something like Flask? we need to compose MLS/MCS as well in a real system, and potentially some form of IBAC & RBAC. but let's keep it to TE & CHERI caps for now. We also want to look at emulating or hybridizing cheri caps when there is no cheri h/w.

<!-- VERBATIM USER END -->

## Assistant output

<!-- VERBATIM ASSISTANT START -->

**Recommendation: compose capabilities and TE, but do not fuse them into a new authority primitive.** Define a formal `CAP+TE` profile and use a FLASK-like decision/enforcement split.

## Separation of responsibilities

| Layer | Purpose |
|---|---|
| Capability | Designates the object and supplies bounded, derived authority |
| TE | Applies a mandatory source-type → target-type policy ceiling |
| Enforcement | Encodes the intersection in G-stage/IOMMU mappings and call gates |

```text
cap_ok =
    valid && held_by_subject && active &&
    derived_from_root && rights_cover(operation) &&
    generation_current

te_ok =
    allow(subject.type, object.type, object.class, operation)

allow = cap_ok && te_ok
effective_rights = capability_rights intersect TE_access_vector
```

A TE allow must never create authority without a capability. Possessing a capability must never override a TE denial.

## FLASK-like composition

Borrow the architecture, not the complete SELinux runtime:

1. The object manager resolves a capability to a canonical internal object.
2. Subject identity/type comes from monitor-held domain state.
3. Object type/class comes from monitor-held object metadata.
4. Capability validity, lineage, rights, and generation are checked.
5. A small security server returns the TE access vector.
6. The enforcer intersects both results and performs the operation.

The caller must not supply trusted labels, object classes, or requested policy identities.

Initially, compile policy offline into bounded immutable tables. Avoid a parser, dynamic policy server, or access-vector cache in HS. MLS/MCS, RBAC, and IBAC can later extend the security contexts and decision server without changing capability semantics:

```text
capability
AND TE
AND MLS/MCS constraints
AND transition/administrative rules
```

## A useful composition experiment

Make each mechanism independently observable:

- Give the reader an RW capability to `shared_t`, but let TE deny write.
- Give another subject a TE allow for `shared_t`, but no capability designating it.
- Both must be denied for different reasons.
- Writer receives both capability and TE authorization, so its PTE becomes RW.

That proves the composition rather than merely encoding identical permissions twice.

## Without CHERI hardware

Use **software capabilities**, not “emulated CHERI capabilities.”

The simplest representation is a per-domain capability space:

```text
slot -> {
    object,
    maximum rights,
    parent/root,
    generation,
    revocation lineage,
    active
}
```

The guest receives an opaque slot/generation handle. The handle is only an identifier; authority comes from the protected HS table and current domain identity. Derivation may only attenuate rights.

Prefer this over cryptographic bearer tokens initially: it is easier to revoke, reason about, and formally model.

## With CHERI hardware

Keep the same abstract capability model, but add a CHERI backend:

- tagged/bounded capabilities for monitor-internal references;
- sealed capabilities for opaque object handles;
- monotonic hardware permission attenuation;
- a protected object table for TE labels, lifecycle, generations, and revocation.

The table likely remains useful even with CHERI because architectural capabilities alone do not provide general revocation, VM lifecycle, TE labels, or policy generations.

Prove both backends refine one abstract capability model:

```text
AbstractCap
  <- software CSpace implementation
  <- CHERI tagged/sealed implementation
```

Do not expose direct CHERI-like pointer semantics on non-CHERI systems. Keep operations monitor-mediated.

## Relationship to VM isolation

CHERI, TE, and virtualization mechanisms solve different problems:

- **CHERI capabilities:** in-address-space reference integrity and bounded authority.
- **G-stage translation:** isolation between VMs/security domains.
- **IOMMU/IOPMP:** DMA isolation.
- **TE:** mandatory policy over domains, objects, and channels.

A VBS-like call would therefore resolve a capability, apply TE, switch to a protected root, and expose only explicitly authorized shared buffers.

The best initial architecture is thus:

```text
HS isolation engine:
    ownership + capability spaces + compact TE evaluator
    + G-stage enforcement

VS domains:
    management, protected service, later I/O domains

Offline:
    policy/manifest compiler and audit tooling
```

This gives a clean path to MLS/MCS and RBAC later without embedding every policy concept into capabilities or weakening CHERI alignment.

<!-- VERBATIM ASSISTANT END -->
