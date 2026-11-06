<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Transcript: multi-hart HS isolation engine

## Provenance and status

- Date: 2026-07-20
- Session: `90e28972-e41b-41ee-8432-420c6cdbaabd`
- Turn: 7
- Assistant: GitHub Copilot CLI, GPT-5.6 Sol
- Status: verbatim research input; not an approved architecture or claim

## User prompt

<!-- VERBATIM USER START -->

right, I am trying to determine if this architecture direction provides an option for a VBS style (but better) layer in the future. re. (3), what is the simplest way to approach this, let's just focus on hv isolation. mutiple HARTs? a security monitor / enforcer in an EL.2 equivalent (c.f. nitro hv recently)

<!-- VERBATIM USER END -->

## Assistant output

<!-- VERBATIM ASSISTANT START -->

**The simplest credible direction is a tiny isolation engine in RISC-V HS-mode—the EL2 equivalent—executing on every active hart, with all rich hypervisor functionality moved into VS domains.**

```text
M-mode: OpenSBI / measured boot
    |
HS-mode: xh Isolation Engine
    - trap entry/return
    - frame ownership
    - G-stage roots
    - hart ownership
    - explicit sharing
    - compact policy enforcement
    |
VS-mode domains
    - management Linux/VMM
    - protected security domain
    - later I/O/service domains
```

## First multicore increment

Use only **two harts and two statically configured domains**:

| Hart | VS domain |
|---|---|
| 0 | Untrusted management Linux/VMM |
| 1 | Protected security service |
| Others | Parked |

The HS monitor runs locally on both harts. It has:

- common read-only code;
- one private trusted stack and current-domain record per hart;
- two immutable G-stage roots;
- one immutable frame-ownership/manifest table;
- one directional shared page;
- no scheduler, migration, overcommit, device model, or runtime mapping changes.

The boot hart validates the fixed manifest and constructs everything before releasing the second hart. After release, there is no shared mutable control state in the steady-state path.

A dedicated “monitor hart” is **not required initially**. Every hart running VS code necessarily needs a local HS trap path and `HGATP` state. Centralizing all enforcement on one hart would add an IPI/message protocol and availability dependency. A dedicated control hart may become useful later, but it is not the simplest starting point.

## Enforcement model

Make hardware ownership primary:

1. Every private frame has exactly one owner.
2. Monitor frames appear in no VS root.
3. Every PTE is a subset of the validated manifest.
4. Each hart may enter only its statically assigned domain/root.
5. Sharing exists only through explicit channel records.
6. The management domain cannot directly edit roots or ownership state.

TE should initially be a **boot-time mandatory policy ceiling**, not a general runtime policy engine. Compile the fixed labels/rules into a canonical manifest, validate it in HS, and construct the roots. Capabilities or bounded handles can later designate individual objects; TE can then deny operations even when a handle exists.

## Multicore evolution

Only after immutable two-hart isolation is proved should dynamic operations be added. Use one serialized global control path:

```text
acquire global control lock
  -> validate ownership/capability/TE
  -> update mappings
  -> send invalidation requests
  -> affected harts execute HFENCE.GVMA
  -> collect acknowledgements
  -> publish/reuse the frame
release lock
```

Fast-path state remains per-hart. Avoid migration, shared run queues, and fine-grained locking initially.

## Proof target

The static two-hart configuration is still tractable:

- private-frame uniqueness;
- monitor-memory exclusion;
- policy-to-PTE soundness;
- hart-to-domain binding;
- per-hart transition correctness;
- cross-hart confidentiality/integrity;
- noninterference except for the explicit directional shared page.

Because mappings never change after launch, the first proof avoids concurrent revocation and remote TLB-shootdown reasoning.

## Nitro analogy

This follows the publicly described Nitro Isolation Engine pattern: a small separation/isolation kernel owns security-relevant VM state and exposes a narrow interface to a larger resource-management environment. A potentially stronger `xh` variant would place that larger environment entirely in an untrusted VS management domain rather than relying on an intra-HS software boundary.

AWS’s disclosed methodology is relevant, but its complete source and project proofs were still unpublished in the reviewed material, so it should be treated as architectural/formal-method precedent rather than reusable implementation evidence.

## VBS path

This foundation leaves a clean future route to VTL-like contexts:

- normal Linux/guest kernel in one root;
- secure kernel/service/enclave in another;
- HS-controlled entry, root, stack, register state, and interrupt handling;
- explicit shared call buffers;
- enclave-private pages never mapped to the normal kernel.

The key architectural choice is therefore **not TE versus capabilities yet**. It is establishing a tiny, exclusive HS isolation engine whose state cannot be bypassed by the management kernel. Once that exists, TE becomes a viable optional policy layer for VBS-style secure domains.

<!-- VERBATIM ASSISTANT END -->

