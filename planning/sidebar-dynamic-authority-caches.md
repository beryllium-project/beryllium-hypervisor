<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Sidebar: CHERI, protected VS services, and dynamic authority caches

## Status and attribution

This page records a future research question. It does not select an AVC,
policy server, CHERI mechanism, or runtime cache for Beryllium.

The publicly verifiable Chompie artifact is Valentina Palmiotti's
`s8_2019_2215_poc` for CVE-2019-2215. Its SELinux bypass walks AVC cache
entries and overwrites cached `allowed` bitmasks after obtaining kernel memory
read/write primitives.

No public primary source was found in which Chompie separately states a
general architectural critique about semantic AVC freshness. That broader
attribution remains unverified. The PoC itself is sufficient evidence for the
cache-corruption problem.

## What the SELinux AVC actually caches

The kernel AVC keys a decision by:

```text
source SID + target SID + object class
```

The cached `av_decision` includes:

- allowed permission bits;
- audit-allow and audit-deny bits;
- policy sequence number; and
- flags such as permissive-domain state.

The implementation uses RCU for read-side lookup, per-slot locks for mutation,
a policy-generation notification fence, and cache reset on policy changes.
Userspace libselinux has a related AVC and receives policy-change
notifications.

This is a useful precedent: high-rate security decisions require both memory
integrity and an explicit update/coherence protocol.

## Two different problem classes

### Cache memory corruption

The Chompie PoC is a post-exploitation technique:

1. another vulnerability supplies arbitrary kernel read/write;
2. the attacker finds AVC cache nodes;
3. cached permission bits are changed directly; and
4. selected checks return forged grants.

This bypasses legitimate insertion, generation, and invalidation logic. It is
not evidence that SELinux intentionally permits stale or forged decisions.

### Semantic freshness and revocation

The general design problem is different:

- a decision was legitimate under generation N;
- policy, ownership, subject identity, or object state moves to N+1; and
- some enforcement point still holds a generation-N answer.

Questions include:

- What is the linearization point of an update?
- Which operations already in flight may complete under the old generation?
- How does every cache learn that N+1 committed?
- Must invalidation be acknowledged before new operations start?
- What happens when a cache or policy service is unavailable?

Upstream SELinux already implements sequence numbers, RCU ordering, reset,
and notification. This sidebar does **not** assert an exploitable upstream
stale-grant bug. Its update protocol is a case study for a broader class that
Beryllium must model explicitly if it ever adds dynamic cached authority.

## What CHERI can help with

With an appropriate CHERI compilation and allocation model, capabilities can
constrain:

- out-of-bounds writes from adjacent objects;
- pointer forging;
- access through pointers lacking authority;
- compartment entry and object access through sealing; and
- use-after-free when paired with a temporal-safety/revocation design such as
  Cornucopia.

This directly addresses ways an unrelated kernel memory bug can become an AVC
node overwrite or cross-cache attack.

## What CHERI does not solve

CHERI does not know:

- which policy generation is current;
- whether a valid cached `allowed` value still represents operator intent;
- whether a service reply was replayed;
- whether every distributed enforcement point acknowledged invalidation; or
- whether a live object's authority should be semantically revoked.

Heap capability revocation invalidates references to freed allocations. It
does not automatically revoke a live, correctly bounded object whose cached
value became obsolete.

A sealed token may contain a generation and prevent unauthorized
modification, but software must still compare that generation with the
current committed epoch.

## What a protected VS service can help with

Moving policy and decision state to a separately mapped VS domain can protect
it from arbitrary writes by management Linux. Concrete systems establish the
isolation pattern, but not a generic protected AVC or policy-decision cache:

| System | Protected state or service | Relevant mechanism and limit |
| --- | --- | --- |
| Android pKVM / Arm EL2 | EL2 page-ownership state and protected-VM memory | EL2-controlled host and guest stage-2 mappings remove donated pages from host access and make later sharing explicit. This is an ownership and protected-domain precedent, not a documented policy server. Upstream pKVM remains experimental and does not inherit every Android product-level CPU/DMA claim. |
| Windows VBS / VTL | Higher-VTL memory and processor state; HVCI code-integrity validation; Credential Guard secrets | Hyper-V enforces VTL memory protections that VTL0 cannot modify. HVCI validates kernel code in an isolated VBS environment, while Credential Guard exposes a narrow service to normal LSA. This is within a Hyper-V partition and still trusts its hypervisor and firmware. |
| AMD SEV-SNP VMPL / SVSM | A VMPL0 security-service module, with vTPM as one documented service | Less-privileged, higher-numbered-VMPL guest software requests privileged guest-local services from the SVSM. VMPL is intra-confidential-VM compartmentalization, not a platform-wide policy service or cache-coherence protocol. |

These examples show hardware-enforced protected memory or execution contexts
for ownership state, code-integrity decisions, and security services. They do
not show that moving an AVC is sufficient, or solve policy generation,
freshness, replay, recovery, or availability for Beryllium.

A complete design must move or authenticate all security-sensitive cache
state. Protecting only the policy database while leaving writable derived
decisions in ordinary kernel slabs preserves the cache-overwrite path.

A VS service also adds:

- IPC and serialization attack surface;
- cache-miss latency;
- replay and generation-coherence requirements;
- service scheduling and availability dependencies;
- restart and recovery state; and
- a new service-specific TCB.

Isolation protects the decision service's memory. It does not prove the
decision algorithm or update protocol correct.

## Candidate combined pattern

```text
immutable policy generation N
        |
protected decision service
        |
signed/authenticated decision:
  subject, object, class, rights,
  generation N, configuration ID,
  bounded lifetime/nonce
        |
HS or in-domain enforcement adapter
        |
allow only if:
  designation is valid
  AND decision generation == committed generation
  AND mandatory ceiling permits
  AND mapping/operation is structurally authorized
```

Recommended properties:

1. **Immutable generations:** construct N+1 separately; never mutate the active
   policy in place.
2. **Single commit point:** publish N+1 only after validation and required
   invalidation preparation.
3. **Epoch-bound cache entries:** every answer carries configuration and policy
   generation.
4. **Fail-closed mismatch:** stale, unknown, replayed, or unavailable replies
   deny or return a bounded retry result.
5. **Explicit acknowledgement:** each load-bearing cache confirms N before
   N+1-dependent operations become runnable.
6. **Bounded caches:** fixed entry count, deterministic eviction, no ambient
   authority in cache pointers.
7. **Authority ceiling:** cached policy cannot mint designation, ownership, or
   mapping rights.
8. **Audit provenance:** record request identity, generation, decision source,
   and enforcement result.
9. **Recovery:** service restart either reconstructs cache from immutable state
   or starts empty; it never recovers authority from untrusted reports.

## Bounded experiments

1. Reproduce Chompie's cache-overwrite shape against a toy bounded cache and
   show that separate-page or CHERI bounds stop corruption.
2. Model two policy generations and prove that no generation-N reply can
   authorize an N+1 operation.
3. Measure the cost of a generation comparison on every cache hit.
4. Model invalidation acknowledgement, service crash, delayed reply, replay,
   and restart in TLA+ or Rocq.
5. Compare three placements: cache in management Linux, cache in protected VS,
   and small HS cache derived from sealed state.
6. Do not add any cache to the Beryllium runtime until a concrete hot path
   demonstrates that recomputation is inadequate.

## Future research questions

- Can a static or boot-only profile avoid runtime decision caches entirely?
- Which operation first creates a concrete need for dynamic policy generation?
- Is a cache entry an optimization only, or does code accidentally treat it as
  durable authority?
- Can cache invalidation be expressed as an atomic configuration transition
  using the Model 0.2 proposed/canonical/derived seam?
- Which properties belong in HS, which in a protected service, and which in an
  in-domain LSM?
- How are availability and bounded retry specified without fail-open behavior?
- What evidence would justify CHERI over ordinary G-stage service isolation
  for this exact problem?

## Primary references

Checked 2026-07-24:

- Chompie PoC at exact repository commit:
  <https://github.com/chompie1337/s8_2019_2215_poc/blob/34f6481ed4ed4cff661b50ac465fc73655b82f64/poc/selinux_bypass.c>
- Independent exploit-oriented explanation:
  <https://klecko.github.io/posts/selinux-bypasses/>
- Linux AVC source at inspected commit:
  <https://github.com/torvalds/linux/blob/4539944e515183668109bdf4d0c3d7d228383d88/security/selinux/avc.c>
- Linux policy load/commit source at inspected commit:
  <https://github.com/torvalds/linux/blob/4539944e515183668109bdf4d0c3d7d228383d88/security/selinux/ss/services.c>
- SELinux userspace AVC:
  <https://github.com/SELinuxProject/selinux/blob/main/libselinux/src/avc.c>
- CHERI architecture:
  <https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-987.pdf>
- CHERI compartmentalization:
  <https://www.cl.cam.ac.uk/research/security/ctsrd/pdfs/201505-oakland2015-cheri-compartmentalization.pdf>
- Cornucopia temporal safety:
  <https://www.repository.cam.ac.uk/items/b53f2ec6-9857-4411-89a0-0a101e025975>
- Android AVF CPU-memory protection and ownership:
  <https://source.android.com/docs/core/virtualization/architecture#cpu-memory-access-protection>,
  <https://source.android.com/docs/core/virtualization/architecture#memory-ownership>
- Linux pKVM:
  <https://docs.kernel.org/virt/kvm/arm/pkvm.html>
- Hyper-V VSM/VTL protections:
  <https://learn.microsoft.com/en-us/virtualization/hyper-v-on-windows/tlfs/vsm#virtual-trust-level-vtl>
- Microsoft HVCI and Credential Guard:
  <https://learn.microsoft.com/en-us/windows-hardware/drivers/bringup/device-guard-and-credential-guard>,
  <https://learn.microsoft.com/en-us/windows/security/identity-protection/credential-guard/how-it-works>
- Linux SVSM documentation:
  <https://www.kernel.org/doc/html/latest/arch/x86/amd-memory-encryption.html#secure-vm-service-module-svsm>
- Existing project trigger boundary:
  [Capability mechanisms and holistic policy](capability-policy-architecture.md)
