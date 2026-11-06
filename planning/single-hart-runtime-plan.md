<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium bounded single-hart runtime plan

## Status and authorization boundary

Responsible-human direction selected this **runtime-planning phase** on
2026-07-24 after accepting Architecture Model 0.2. Responsible-human review
accepted this exact plan and separately authorized implementation of its fixed
profile on 2026-07-25. The accepted planning checkpoint lives on branch
`beryllium/single-hart-runtime-plan`.

The authorization covers only the fixed profile and ordered R0-R7 work
packages in this document. It defines the eligible dependency graph; R3 and
each successor package still require separate responsible-human authorization
before starting. It does **not** authorize:

- privileged behavior outside the accepted profile or work-package graph;
- a sixth Helium pathfinder or another policy variant;
- Linux boot or a stable management, guest, or UAPI contract;
- selection of a protected service or motivating workload;
- guest-visible SBI virtualization beyond the fixed plan below;
- interrupts, timers, multicore, scheduling, migration, or overcommit;
- devices, DMA, IOMMU, IOPMP, or driver domains;
- capabilities, TE, CAP+TE, runtime policy, or an AVC;
- Rust, CHERI, VBS/VTL, attestation, measured launch, or key sealing;
- K3 hardware claims, MVP 1.0, public release, or upstream submission.

R0, the fixed-profile-and-layout package, pinned the exact QEMU, OpenSBI,
tool, CPU, linker, memory, proposal, register-state, and SBI-allowlist values.
Responsible-human review accepted the exact freeze on 2026-07-27 and exact R1
pure-C mechanism commit `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb`
on 2026-07-28. R2 bounded plan was accepted at exact commit
`cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` and R2 implementation separately
authorized on 2026-07-28. Responsible-human review accepted exact R2
implementation commit `6e1cb579257c5dbe3234bd484fd091629e87181b` on
2026-07-28. Responsible-human instruction `proceed with R3` separately
authorized R3 on 2026-07-29. The R3 boot-and-first-entry implementation
content is complete and documented in
[`single-hart-runtime-r3-evidence.md`](single-hart-runtime-r3-evidence.md);
exact implementation target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` was responsible-human accepted on
2026-07-29, and the
[`single-hart-runtime-r3-review-summary.md`](single-hart-runtime-r3-review-summary.md)
record preserves the exact decision. Packet follow-up
`fcc0f267a1f59241f872c0a1d2a371a95a58cba6` is not accepted implementation.
The responsible human accepted exact R4 target
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52` on 2026-07-29. Its implementation
parent is `6e5c55c59e94bbaba136269c784db28ec1b53f54`; decision-support packet
follow-up `ec7be2f146a851e7608e77eb2875076e66aab2e6` is not accepted
implementation. R5 and every successor remain separately gated, not
authorized, and not started.
R2/R3 acceptance does not itself authorize tagging, pushing, public release,
or hardware claims.

## Human review feedback

Responsible-human review on 2026-07-24 raised three research topics. They were
processed before plan acceptance and are now part of the maintained research
pool, not the fixed runtime profile:

| Feedback | Disposition | Maintained location |
| --- | --- | --- |
| Evaluate Verus and similar Rust verification for Beryllium and low-level systems work | Retain Verus as the leading future bounded verifier for safe VS service/protocol logic; compare Kani, Aeneas/Charon, Creusot, Flux, RefinedRust, Prusti, and RustBelt; do not add Rust or Verus to this runtime | [Rust for future VS components](sidebar-rust-vs-components.md), [Open tooling](open-tooling.md) |
| Capture CHERI isolation among components in one VS | Make linker/loader/switcher/allocator/IPC authority and the remaining shared VS TCB explicit; retain separate G-stage roots where isolation from the VS runtime, independent restart, or DMA ownership is required | [CHERI alignment](cheri-alignment.md) |
| Revisit applying TE to capabilities | Preserve ordinary capability-and-object-TE conjunction as the conservative baseline; separately research monitor-held TE over capability possession, transfer, delegation, invocation, attenuation, and revocation without claiming novelty | [Capability mechanisms and holistic policy](capability-policy-architecture.md) |

The TE-over-capability hypothesis requires further human policy semantics,
including whether a label attaches to the canonical object, one capability
record, one holder slot, or a transfer edge, and whether mandatory policy
controls possession, invocation, or both.

None of this feedback changes the accepted one-hart
QEMU/OpenSBI/two-synthetic-VS profile. Its research topics remain
unimplemented and separately gated.

## Relationship to the accepted models

Architecture Model 0.1 was accepted on 2026-07-22. Architecture Model 0.2 was
accepted on 2026-07-24. The runtime plan must preserve their exact evidence
boundary:

```text
bounded platform inventory
        +
copied non-authoritative proposal
        |
        v
complete canonical validation
        |
one-way seal
        |
derived roots and bindings
        |
checked activation and transitions
```

The Model 0.2 Rocq proof applies only to its fixed abstract model. Its
restricted-C validator and state machine are separately tested host programs,
not a proved refinement. Neither result transfers to future privileged code.

The first runtime must therefore implement the accepted seam without claiming
that:

- the runtime refines Model 0.2;
- the C validator or root builder is proved;
- the assembly implements the abstract transition until exact evidence exists;
- OpenSBI, QEMU, compilers, firmware, or hardware are verified; or
- the tested configuration proves arbitrary-domain noninterference.

## Phase question

> What is the smallest privileged RISC-V runtime that can expose every
> load-bearing Model 0.2 C/assembly/architecture cut point in one fixed
> single-hart QEMU configuration, without importing Linux, service, policy,
> device, or multicore complexity?

The output of the completed planning phase is this accepted
implementation-ready contract.

## Why this planning phase came next

Model 0.2 made proposed, canonical, sealed, and derived state explicit. It did
not establish:

- an OpenSBI-to-HS boot contract;
- a privileged memory layout;
- an Sv39x4 root builder;
- an exact trap and context frame;
- complete accessible VS register separation;
- an `HGATP` and `HFENCE.GVMA` switch implementation;
- real G-stage access and fault behavior; or
- correspondence between any runtime bytes and the abstract model.

Selecting a policy model or protected service before exposing those cut points
would overfit the trusted runtime to an unproved interface. Booting Linux would
also add timers, interrupts, virtual SBI, page tables, devices, and a broad
guest ABI before the mechanism spine is bounded.

The accepted first runtime is therefore deliberately synthetic and
policy-neutral. It is a Beryllium refinement milestone, not another Helium
experiment.

## Accepted fixed runtime profile

The following baseline was accepted and authorized for implementation on
2026-07-25.

| Axis | Fixed choice | Reason |
| --- | --- | --- |
| ISA and platform | RV64 H extension on pinned QEMU `virt`, with F, D, V, and unsupported optional state absent | Reuses the established open functional platform while keeping K3 and unmodeled register files unclaimed |
| Hart count | QEMU `-smp 1`; hart zero is the only instantiated hart | Preserves the accepted proof boundary and excludes remote translation state and concurrency |
| M-mode | Pinned OpenSBI below Beryllium | Smallest existing bring-up dependency; avoids creating a new M-mode runtime |
| HS | New restricted-C Beryllium runtime plus a thin RISC-V assembly/platform boundary | Implements the accepted mechanism without carrying Helium identity or claims |
| VS domains | Two sequential role-neutral synthetic domains | Exposes root, state, sharing, fault, and switch behavior without selecting Linux or a service |
| VS stage-1 | Bare | Avoids a guest page-table and address-space ABI |
| G-stage | Two fixed Sv39x4 roots, both using VMID zero | Forces an all-GPA/all-VMID local-hart fence and preserves the stale-translation hazard |
| Configuration | One generated fixed inventory and proposal compiled into a non-authoritative input section | Exercises copy/validate/seal/derive without selecting a parser or stable encoding |
| Authority | One private page per domain plus one explicit directional shared page | Reuses the accepted ownership/channel instance with no policy framework |
| Dynamic state | Active binding, saved context, bounded translation state, and terminal failure only | No lifecycle, allocation, grant, revoke, or policy update |
| Output | Trusted ordered diagnostics and offline authority/layout evidence | Review aid only; output grants no authority |

The identifiers `management` and `protected` may remain in the fixed
configuration to preserve Model 0.2 traceability. They describe topology, not
Linux, a secure kernel, a protected service, or different trust in guest
behavior. Both VS domains are malicious for the isolation claim.

## Fixed execution scenario

The authorized runtime must execute one exact sequence:

1. OpenSBI enters Beryllium in HS-mode on hart zero.
2. Beryllium validates the fixed entry state, image layout, hart identity, and
   required H/Sv39x4 features.
3. It binds a generated normalized inventory and copies the complete fixed
   proposal into private bounded storage.
4. It validates inventory closure, non-overlap, monitor exclusion, private
   ownership, root/stack/saved-state bindings, channel direction, and rights.
5. It seals canonical state exactly once.
6. It derives both G-stage roots only from sealed canonical authority and
   independently rechecks the complete mapping set before publication.
7. It installs the management binding and enters the management VS stub.
8. The management stub reads and writes its private page, is denied access to
   the protected private page, and writes the shared page.
9. One exact VS `ecall` reports the expected management state.
10. HS saves only management context, selects the protected root, stack, and
    saved-state slot atomically, writes `HGATP`, executes
    `HFENCE.GVMA x0,x0` on the local hart, and enters the protected stub.
11. The protected stub reads and writes its private page, is denied access to
    the management private page, reads the shared value, and is denied a
    shared-page write.
12. One exact VS `ecall` reports the expected protected state.
13. HS switches back through the same checked save/select/fence/restore path
    and confirms management state restoration.
14. HS emits the final bounded result and requests platform shutdown.

Each positive access must execute as a real VS load or store. Each denied
access must check:

- `scause` for the exact instruction, load, or store/AMO guest-page-fault
  cause (20, 21, or 23 as applicable);
- `sepc` for the exact faulting instruction;
- the active domain, root, VMID, and transition phase;
- `stval` as the faulting GVA;
- `htval << 2` as the GPA when the architecture supplies it; and
- unchanged denied-access backing state.

The fixed VS-stage-Bare fixtures intentionally use identity-shaped addresses,
so their expected GVA and GPA are equal. The plan does not generalize that
equality or require nonzero `htinst`, which the architecture may report as
zero. A modeled software access check is not a substitute for QEMU G-stage
behavior.

Any unexpected hart, phase, root, VMID, PC, trap, fault address, mapping,
register state, event, or SBI result enters terminal failure. No permissive
recovery path is in scope.

## M-mode and OpenSBI boundary

### Accepted first-runtime selection

The fixed profile uses:

```text
pinned OpenSBI in M-mode
        |
new Beryllium runtime in HS-mode
        |
two sequential synthetic VS domains
```

OpenSBI is a trusted external firmware dependency for this profile. It is not
part of Beryllium, is not proved by Model 0.2, and is not an architectural
requirement for later profiles.

The plan defers:

- a Beryllium-owned M-mode component;
- a new independent minimal M-mode runtime;
- firmware-hostile launch;
- PMP/ePMP reprogramming after handoff; and
- a general HS-to-M forwarding framework.

Those alternatives add a different firmware and assurance question and require
their own bounded plan.

### HS-facing SBI allowlist

The first runtime may use only a pinned, documented HS-to-M SBI allowlist:

| Purpose | Candidate SBI behavior | Security role |
| --- | --- | --- |
| Extension discovery | SBI Base probing for the required fixed profile | Initialization check only |
| Diagnostics | Debug Console extension with bounded HS-owned physical ranges and complete partial-write handling | Test evidence only; authority and isolation correctness must not depend on console availability |
| Termination | System Reset shutdown request | Ends the fixed run after pass or terminal failure |

No timer, IPI, remote-fence, hart-state, performance, suspend, PMU, or vendor
extension is required. SBI Base must report DBCN and SRST availability
explicitly; the SBI version alone is not evidence that either optional
extension exists. Missing or malformed required behavior fails the profile
rather than selecting an undocumented fallback. Legacy console or shutdown
calls may be retained only in Helium; they are not the accepted Beryllium
interface.

DBCN receives a physical address split across SBI arguments, not a guest
virtual pointer. The complete diagnostic range must:

- lie inside one HS-owned monitor diagnostic extent;
- be range-checked without overflow;
- satisfy the SBI supervisor-access and platform-memory-attribute rules;
- never overlap guest, proposal, canonical, root, stack, or saved-state data;
  and
- remain inaccessible to both VS roots.

A successful DBCN write may consume fewer bytes than requested, including
zero. The architecture boundary must accumulate partial progress with one
fixed retry bound and handle `INVALID_PARAM`, `DENIED`, and `FAILED`
explicitly. Exhausting the bound makes the test evidence unavailable and
enters the fixed failure path; it never changes authority or creates a
success-shaped result.

Every SBI call and return value belongs in the architecture boundary and must
have:

- an exact extension and function identifier;
- bounded arguments and HS-owned memory;
- explicit success and error handling;
- no guest-controlled physical pointer;
- no ambient forwarding; and
- deterministic failure behavior.

### Guest-facing SBI disposition

The two synthetic VS stubs receive **no general SBI implementation**.

Their exact `ecall` events form a private test protocol identified by:

- active domain and vCPU;
- exact guest PC;
- exact execution phase;
- fixed event number;
- fixed argument values; and
- expected memory and saved-state observations.

Unknown extension/function-shaped values, unexpected PCs, or wrong-phase
events fail closed. The protocol is not called SBI, is not a Linux ABI, and
must not be extended into one operation at a time.

Linux-class guest SBI virtualization is deferred to a separate plan. That
later plan must define emulation, M-mode forwarding, hart masks, timers,
interrupts, shared-memory operands, and service delegation from first
principles.

No VS-resident OpenSBI or SBI service exists in this profile.

## Boot and platform contract

The implementation plan must freeze:

- pinned QEMU machine and CPU options;
- pinned OpenSBI source or packaged artifact identity;
- reset and next-stage entry address;
- `a0` hart identifier and `a1` firmware-provided pointer treatment;
- complete physical memory and image layout;
- monitor, root-table, stack, saved-state, guest, private, and shared extents;
- required ISA extensions and forbidden optional state;
- initial delegation, interrupt, counter, debug, and translation controls; and
- linker assertions for every security-sensitive boundary.

The fixed runtime does not parse Device Tree. The QEMU platform inventory
is generated offline and compiled into the fixed profile. The firmware
pointer may be recorded for diagnostics but conveys no authority and is not
dereferenced by the core.

The exact QEMU command must instantiate one hart and a CPU profile without F,
D, V, or another unmodeled register file. The retained configuration and
negative instruction fixtures are part of the evidence. If the selected QEMU
CPU cannot remove one of those facilities, the plan must be revised to save,
restore, and test its complete state before implementation is authorized.

The plan must define and check the M-mode handoff assumptions for PMP/ePMP,
delegation, debug access, and writable monitor memory. QEMU evidence cannot
establish the corresponding K3 behavior.

## Configuration and authoritative-state boundary

### Input representation

The fixed inventory and proposal use restricted-C structures generated at
build time. They live in a distinct read-only input section and are copied
before validation.

This is an internal fixed-profile representation, not:

- a stable manifest encoding;
- a public ABI;
- an authenticated boot artifact;
- a Device Tree schema;
- a parser;
- an attested measurement; or
- proof that an attacker-controlled transport is safe.

Negative host and image fixtures may compile malformed values into the input
section. No VS domain can replace the proposal after entry.

### Authority publication

The privileged runtime must keep separate types and storage for:

1. platform inventory;
2. copied proposal;
3. canonical validated state;
4. sealed authority;
5. unpublished derived roots; and
6. active binding and mutable saved state.

No proposal pointer may remain live after copy. No validation helper may write
a root or active binding. No root may be installed before complete validation,
sealing, derivation, and an independent recheck.

Canonical state becomes immutable after sealing. Runtime diagnostics, reports,
guest memory, and mutable derived state never carry authority.

## G-stage root contract

The fixed profile uses:

- Sv39x4 only;
- a 16 KiB-aligned Sv39x4 root table for each domain;
- 4 KiB leaves only;
- one statically reserved complete page-table pool per domain;
- no allocator, huge pages, aliases, demand paging, runtime A/D-bit fault
  handling, or runtime root edit;
- two distinct root-table extents;
- VMID zero for both roots; and
- `HFENCE.GVMA x0,x0` on the local hart before initial entry and after every
  cross-root `HGATP` write.

In this document, an all-GPA/all-VMID fence means the local-hart
`HFENCE.GVMA x0,x0` operation. It is not a cross-hart or system-global fence.
The fixed QEMU command uses `-smp 1`.

The root builder must:

1. start from zeroed unpublished root storage;
2. consume sealed canonical authority only;
3. reject unaligned, duplicate, overlapping, empty, or unsupported mappings;
4. install only nonempty rights subsets for exact GPA/frame pairs;
5. reject unsupported GPA width and every invalid or reserved PTE encoding;
6. set `U=1` on every valid G-stage leaf because G-stage accesses are checked
   as user accesses;
7. pre-set `A=1` on every valid leaf and `D=1` on every writable leaf so the
   fixed profile needs no A/D fault handler or hardware page-table mutation;
8. exclude monitor, root, trusted-stack, and saved-state extents;
9. permit shared backing only through the one canonical channel;
10. finish the complete root before publication; and
11. independently enumerate the generated leaves and compare them with
   canonical authority.

A failed root build leaves both domains non-runnable. There is no partial
single-domain fallback.

## Trap, transition, and saved-state contract

Before implementation, the plan review must accept an exact register-state
matrix derived from the pinned RISC-V privileged specification.

At minimum, the matrix must account for:

- every integer register visible across the trap boundary;
- guest PC and stack;
- `vsstatus`, `vsie`, `vstvec`, `vsscratch`, `vsepc`, `vscause`, `vstval`,
  `vsip`, and `vsatp`;
- `hstatus`, `hedeleg`, `hideleg`, `hie`, `hip`, `hvip`, `hcounteren`,
  `htimedelta`, `henvcfg`, and implemented state-enable controls;
- HS trap metadata including `scause`, `sepc`, `stval`, `htval`, and `htinst`;
- active `HGATP`, VMID, trusted stack, and saved-state identity;
- all HS- and firmware-controlled counter-access gates;
- floating-point and vector status, with F, D, and V absent from the pinned
  CPU profile rather than merely cleared at entry;
- pending virtual interrupt state even though interrupts are disabled; and
- any QEMU/OpenSBI state assumed constant rather than saved.

AIA or another optional virtual interrupt state must be absent from the pinned
CPU/machine profile or added explicitly to this matrix.

An entry is permitted only when every state element is either:

1. saved and restored for the exact domain;
2. reset to a documented domain-independent value;
3. inaccessible under a checked architecture control; or
4. explicitly excluded from the claim.

Before every VS entry, HS sets and verifies `vsatp.MODE=Bare` and
`hstatus.VTVM=1`. Any VS attempt to write `satp` or execute a trapped
translation-management instruction is an unexpected virtual-instruction event
and enters terminal failure. Merely initializing `vsatp` once is
insufficient.

The context switch must order:

```text
validate source binding
  -> save source-owned state
  -> select target root/VMID/stack/saved-state as one pending binding
  -> write HGATP
  -> execute local-hart HFENCE.GVMA x0,x0
  -> restore target-owned state
  -> publish target active
  -> execute target
```

No target instruction may execute before the fence. Any trap during a partial
transition is terminal in the first profile.

## Interrupt, timer, counter, and optional-state disposition

| Feature | First-runtime disposition |
| --- | --- |
| Asynchronous interrupts | Disabled at every HS-controlled gate, not delegated to VS, and supplied by no enabled QEMU source |
| Virtual interrupts | Cleared and inaccessible to the test stubs |
| Timers and Sstc | Not exposed; no timer SBI |
| IPIs and remote fences | Not required on one hart |
| Counters and PMU | All HS-controlled enable gates cleared and verified; M-mode assumptions recorded; any VS access fails |
| Floating point | F and D absent from the pinned QEMU CPU profile; otherwise the plan must add complete FPR and `fcsr` state |
| Vector state | V absent from the pinned QEMU CPU profile; otherwise the plan must add complete vector state |
| VS stage-1 translation | Bare before every entry; `hstatus.VTVM=1`; any translation-management attempt fails |
| Debug/trace | QEMU development assumption, excluded from isolation claim |
| IOMMU/IOPMP | Absent because the profile has no DMA or devices |

The implementation may not silently emulate an excluded feature merely to
keep a payload running.

## Source and build boundary

The authorized implementation must preserve the RFC layout without pretending
to be a Linux submission:

```text
virt/be/                 architecture-neutral restricted-C mechanism
arch/riscv/be/           entry, trap, G-stage, SBI, linker, and platform code
include/be/              private freestanding contracts
tests/                   host, report, image, and QEMU checks
```

No `drivers/virt/be/` or `include/uapi/linux/be.h` surface is needed because
the fixed profile has no Linux or public ABI. Kbuild integration remains an
RFC objective, not a dependency for the first private runtime.

The root `Makefile` and `./be` wrapper may gain runtime targets only after the
plan is accepted and implementation is authorized. Plain `make` must continue
to build retained Helium until a separately reviewed interface change says
otherwise.

All new source must use:

- `SPDX-License-Identifier: GPL-3.0-only`;
- James Morris `<jamorris@linux.microsoft.com>` as responsible human copyright
  holder;
- restricted GNU C accepted by GCC and Clang;
- no heap, recursion, variadic API, uncontrolled function pointers, or guest
  callback;
- fixed-width types and checked extent arithmetic; and
- one explicit assembly/privileged-instruction boundary.

## Model-to-runtime cut-point matrix

| Accepted model operation | Candidate runtime component | Required evidence | Explicit remaining assumption |
| --- | --- | --- | --- |
| Bind inventory and copy proposal | bounded boot initializer | host mutation tests; image-section/layout checks | fixed compiled input represents the documented profile |
| Canonical validation | restricted-C validator | GCC/Clang unit and adversarial tests; deterministic rejection report | no Rocq-to-C refinement |
| Seal authority | one-way state transition | post-seal mutation tests; writable-range inspection | C memory integrity and compiler behavior |
| Derive roots | Sv39x4 root builder | complete leaf report; positive/negative host tests; QEMU accesses | C/PTE correspondence and QEMU architecture behavior |
| Activate binding | entry preparation and exact wrapper | linked layout checks; exact entry trace | assembly/ISA correspondence until proved |
| Save and restore | trap frame and context switch | domain-state tests; exact frame/layout evidence | completeness of the accepted register matrix |
| Complete invalidation | `HGATP` plus local-hart `HFENCE.GVMA x0,x0` wrapper | skipped-fence negative case; exact instruction evidence | QEMU and ratified local-hart fence semantics |
| Authorize access | installed G-stage leaves | real VS positive and faulting accesses | no arbitrary-code or hardware noninterference claim |
| Terminal failure | bounded failure/shutdown path | wrong phase/root/trap/event fixtures | platform may still deny shutdown or output |

## Planned assurance layers

### Mandatory implementation evidence

The authorized implementation must provide:

- warning-clean GCC/GNU ld and Clang/lld builds;
- host unit and adversarial tests for every C rejection and phase rule;
- at least three complete pinned QEMU runs per compiler;
- exact ordered serial/event validation, not QEMU exit status alone;
- positive private and channel accesses;
- real cross-private and shared-write guest-page faults;
- skipped-fence, wrong-root, wrong-binding, wrong-PC, wrong-event, malformed
  input, and partial-publication negative cases;
- complete source, tool, object, ELF, binary, disassembly, layout, mapping,
  and configuration identities;
- deterministic authority and mapping reports generated offline; and
- the complete open local and pinned rootless evaluator gates.

K3 remains `NOT RUN`.

### Machine-checked evidence

The accepted Model 0.2 proof remains a separate abstract evidence set. The
authorized runtime must add:

1. a fixed configuration trace showing that runtime constants instantiate the
   accepted abstract domains, resources, channel, and rights;
2. exact extraction and checking of the new privileged entry, trap, root-write,
   fence, and return wrapper bytes using the retained Helium exact-proof
   method where it remains applicable; and
3. an explicit ledger of C validator, root-builder, trap-handler, compiler,
   linker, firmware, emulator, and hardware cut points.

No theorem or historical Helium result transfers automatically. If exact-byte
proof adaptation is not completed, the runtime may retain test evidence but
must state the assembly boundary as unproved and cannot claim the corresponding
binary property.

Cerberus, CN, CBMC, Frama-C, Sail, and a C refinement are not silently added as
dependencies. Any load-bearing use requires the open-tooling review and exact
claim update already required by project policy.

## Authorized implementation work packages

Responsible-human authorization on 2026-07-25 covers these packages only, in
dependency order. R0 was accepted on 2026-07-27; exact R1 commit
`a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` and exact R2 implementation
commit `6e1cb579257c5dbe3234bd484fd091629e87181b` were accepted on 2026-07-28.
Responsible-human instruction separately authorized R3 on 2026-07-29. The
R3 implementation content is complete and exact target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` is accepted on that date. The
packet follow-up remains decision support. R4 is accepted at exact target `0783dfc6557453fbac0da93a5364f2e6e2cb1f52`;
its parent `6e5c55c59e94bbaba136269c784db28ec1b53f54` and packet follow-up
`ec7be2f146a851e7608e77eb2875076e66aab2e6` remain distinct. R5 and every
successor remain gated, not authorized, and not started; publication remains
blocked.

| Package | Scope | Depends on |
| --- | --- | --- |
| R0: fixed profile and layout | freeze QEMU/OpenSBI/tool versions, linker map, inventory, proposal, register matrix, and SBI allowlist | accepted plan |
| R1: pure C mechanism | copy, validate, canonicalize, seal, derive, report, and terminal phase logic | R0 |
| R2: Sv39x4 backend | fixed page-table storage, root builder, leaf walker, `HGATP` encoding, and host tests | R1 |
| R3: boot and entry | OpenSBI handoff, image checks, HS setup, initial binding, and first VS entry | R0, R2 |
| R4: trap and context | exact frame, fault classification, private events, save/restore, and terminal failure | R3 |
| R5: checked switching | pending binding, root write, fence, restore, re-entry, and state-separation tests | R4 |
| R6: adversarial images | malformed input, partial publication, wrong binding, skipped fence, unexpected trap/event, and denied-access fixtures | R1-R5 |
| R7: proof and evidence | exact-byte adaptation, claim ledger, evaluator, reports, docs, and reproducibility bundle | R0-R6 |

Every package must leave the tree in a buildable and testable state. Packages
must not be collapsed by importing a broad runtime, Linux compatibility
layer, general SBI emulator, allocator, scheduler, or device model.

### R0 exit and review gate

R0 must produce a reviewable, non-privileged profile freeze containing:

- exact QEMU, OpenSBI, GCC, Clang, linker, and supporting-tool revisions;
- the complete QEMU command, including one hart and forbidden optional ISA
  state;
- the linker script plan and every physical extent with checked alignment and
  non-overlap;
- the generated inventory and copied-proposal constants;
- the complete VS/HS register-state matrix;
- the exact HS-to-M SBI allowlist and error behavior;
- planned positive, negative, image, layout, and evidence fixtures; and
- a trace from every frozen value to this plan and Model 0.2.

R0 adds no privileged runtime C or assembly. Its freeze is the next human
review point. R1 may begin only after the responsible human accepts that exact
freeze. Responsible-human review satisfied this gate on 2026-07-27 for exact
freeze commit `64a88b15a6c35d522fa997699c4fb514b15da314`.

### Current R1 completion note

The local R1 pure-C mechanism now present in this worktree completes the
bounded non-privileged package and is documented in
[`single-hart-runtime-r1-evidence.md`](single-hart-runtime-r1-evidence.md).
Current passing commands are:

```sh
make -C tests r1-test
make -C tests r1-report
make -C tests r1-evidence
make -C tests r1-check
./be r1-check
./be r1-evidence
```

Its precise scope is still restricted-C only: copy, validate, canonicalize,
seal, abstract derive, report, and terminal failure. The full profile is
thirteen resources, six canonical authorities, and two abstract derived roots
with three mappings each. These roots are not Sv39x4 tables and do not start
R2. Responsible-human review accepted exact commit
`a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` on 2026-07-28. This exact-commit
acceptance did not authorize tagging, pushing, public release, or R2.

### Current R2 completion note

The accepted R2 implementation is documented in
[`single-hart-runtime-r2-evidence.md`](single-hart-runtime-r2-evidence.md)
and its
[`review record`](single-hart-runtime-r2-review-summary.md). It remains a
non-privileged, host-tested fixed Sv39x4 builder, independent walker/recheck,
and HGATP encoder. It does not write CSRs, link an image, boot, trap, execute
Beryllium in QEMU, validate hardware, or provide formal proof.
Responsible-human review accepted exact implementation commit
`6e1cb579257c5dbe3234bd484fd091629e87181b` on 2026-07-28. R3 was separately
authorized on 2026-07-29 and its implementation content is complete at the
bounded boot-and-first-entry boundary.

### Current R3 completion note

The R3 package is documented in
[`single-hart-runtime-r3-evidence.md`](single-hart-runtime-r3-evidence.md).
It validates the pinned OpenSBI handoff, exact linked image, SBI Base/DBCN/SRST,
accepted R1 state, physical-pool R2 roots and independent re-walk, bounded
HS/VS reset state, and the management initial binding. It writes management
HGATP, executes local `HFENCE.GVMA x0,x0`, reads the CSR back, publishes the
binding, sets `sstatus.SPP=1` at the final entry boundary, and executes
`sret`. Three GCC and three Clang bounded QEMU traces show SPP in the SRET
CPU state and `V=1` at `pc=0x40010000`; inspected SPP/SRET semantics supply the
VS-versus-VU distinction. R4 now owns the subsequent two-exit
trap-and-context sequence separately.

Current passing commands are:

```sh
./tests/r3/run-make.sh r3-host-test
./tests/r3/run-make.sh r3-image-check
./tests/r3/run-make.sh r3-qemu
./tests/r3/run-make.sh r3-report
./tests/r3/run-make.sh r3-evidence
./tests/r3/run-make.sh r3-check
./be r3-check
./be r3-evidence
```

The checked launcher is normative when external Make control is not already
trusted. Raw `make -C tests/r3 TARGET` remains a parse-time-guarded developer
interface, but it cannot intercept an early GNU Make exit or an alternate
`-f` file that prevents the R3 Makefile from loading.

R3 is privileged and links an image, but implements no trap classification,
context save/restore, event protocol, switch, protected VS entry, access
fault test, or R7 proof. Exact target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` is responsible-human accepted as
recorded in
[`single-hart-runtime-r3-review-summary.md`](single-hart-runtime-r3-review-summary.md);
R3 acceptance itself does not add those excluded behaviors or authorize R4;
the later separately authorized R4 implementation is documented in
[`single-hart-runtime-r4-evidence.md`](single-hart-runtime-r4-evidence.md)
and does not authorize R5.

### Current R4 implementation note

The committed-local implementation/evidence state provides the bounded R4
trap-and-context package in
[`single-hart-runtime-r4-evidence.md`](single-hart-runtime-r4-evidence.md).
It imports the exact accepted R3 management state, uses an exact 320-byte
frame, services only the denied protected-private load and the private VS
event, restores the same management binding at `0x40010018` and
`0x40010034`, and fails terminally on every other path. It neither writes
HGATP nor executes `HFENCE.GVMA` after initial R3 entry.

Current evidence commands are:

```sh
./tests/r4/run-make.sh r4-toolcheck
./tests/r4/run-make.sh r4-host-test
./tests/r4/run-make.sh r4-image
./tests/r4/run-make.sh r4-image-check
./tests/r4/run-make.sh r4-qemu
./tests/r4/run-make.sh r4-report
./tests/r4/run-make.sh r4-evidence
./tests/r4/run-make.sh r4-check
```

The stable root-wrapper commands are `./be r4-check` and
`./be r4-evidence`. The evidence is QEMU-only and has no protected VS entry
or switching. R4 is accepted only at exact target
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52`; R5 and every successor remain
not authorized and not started, and publication remains blocked.

## Planned runtime completion claim

If every implementation and evidence gate passes, the strongest planned
runtime statement is:

> In one pinned single-hart QEMU `virt` configuration, repeated GCC and Clang
> Beryllium images copy and validate one fixed policy-neutral configuration,
> seal canonical authority, derive two Sv39x4 roots, enter two sequential
> role-neutral VS domains, preserve their tested private and saved state,
> enforce one directional shared page, deny the tested cross-private and
> shared-write accesses, and complete each root switch only after the required
> local-hart all-GPA/all-VMID `HFENCE.GVMA x0,x0`.

Required limit:

> This is bounded review, test, and any separately identified exact-wrapper
> proof evidence. It does not prove a C refinement, complete runtime
> correctness, arbitrary-guest isolation, Linux, OpenSBI, QEMU, compilers,
> linker output, K3 hardware, devices, DMA, multicore behavior, policy
> correctness, full noninterference, or formal verification of Beryllium.

The final wording must be regenerated from the exact delivered evidence.

## Explicit non-goals

- A Linux management domain or shell.
- A protected service, secrets workload, logger, code-integrity service, or
  driver domain.
- A stable guest ABI, hypercall ABI, SBI profile, manifest encoding, or UAPI.
- Runtime domain creation, destruction, restart, allocation, or scheduling.
- Runtime root edits, frame transfer, grants, revocation, or policy updates.
- Interrupt injection, timers, IPIs, AIA, Sstc, IOMMU, IOPMP, DMA, or devices.
- Capabilities, TE, labels, roles, identity, policy languages, or caches.
- Rust, CHERI, VBS/VTL, enclave, measured launch, attestation, sealing, or
  anti-rollback.
- Multicore, migration, nested virtualization, availability, or side-channel
  claims.
- K3 execution, performance optimization, production hardening, Linux Kbuild
  integration, public release, or upstream submission.

## Accepted planning-phase deliverables

This phase must deliver:

1. this maintained bounded plan;
2. the fixed runtime and threat boundary;
3. the exact M-mode/OpenSBI/SBI disposition;
4. the boot, memory, configuration, root, register, trap, and switch contracts;
5. the model-to-runtime cut-point matrix;
6. the implementation work-package dependency graph;
7. planned tests, proof adaptation, reports, evaluator, and claim limits;
8. updated roadmap, handoff, repository instructions, provenance, and HTML;
9. a review record accepting the plan on 2026-07-25; and
10. separate responsible-human authorization on 2026-07-25 for implementation
    of only the exact fixed profile.

## Accepted planning exit criteria

Responsible-human review closed these criteria on 2026-07-25:

1. The profile is fixed to one hart, one QEMU machine, two sequential
   role-neutral VS domains, and no Linux or service semantics.
2. OpenSBI is either accepted as the pinned first-profile M-mode dependency or
   replaced by a separately justified bounded choice.
3. The HS-to-M SBI allowlist and absence of guest-visible SBI are explicit.
4. Every physical extent, root, stack, saved-state slot, mapping, channel, and
   linker boundary has one owner and fixed size.
5. Every accessible architectural state element has a save, reset, deny, or
   exclusion disposition.
6. Every Model 0.2 operation maps to a runtime component, evidence obligation,
   and remaining assumption.
7. Host, image, QEMU, report, proof, and evaluator gates cover every planned
   failure class at the lowest practical layer.
8. The supportable runtime claim and required limit match the planned evidence.
9. No Helium, Model 0.2, or exact-proof claim is transferred to future code.
10. Responsible-human review accepts the exact plan and separately authorizes
    implementation before any privileged source is added. Both occurred on
    2026-07-25.

## Implementation authorization boundary

The separate implementation authorization covers only the fixed runtime
implementation described here. It does not authorize:

- Linux boot;
- a protected service or service runtime;
- guest SBI expansion;
- K3 hardware work;
- multicore;
- devices or DMA;
- policy/security-model evaluation; or
- MVP 1.0.

Each remains a later decision after the first runtime evidence is reviewed.

## Primary references

Checked 2026-07-24:

- [Architecture Model 0.2](architecture-model-0.2.md)
- [Architecture Model 0.2 implementation and evidence](architecture-model-0.2-evidence.md)
- [Post-pathfinder architecture decision](pathfinder-comparison.md)
- [M-mode, SBI, and VS decomposition](beryllium-hypervisor-notes.md)
- [RISC-V security-hardware roadmap](riscv-security-hardware.md)
- [Open tooling policy](open-tooling.md)
- RISC-V International, Hypervisor Extension:
  <https://docs.riscv.org/reference/isa/priv/hypervisor.html>
- RISC-V International, SBI specification:
  <https://github.com/riscv-non-isa/riscv-sbi-doc>
- RISC-V SBI Base, Debug Console, and System Reset extensions:
  <https://github.com/riscv-non-isa/riscv-sbi-doc/blob/master/src/ext-base.adoc>,
  <https://github.com/riscv-non-isa/riscv-sbi-doc/blob/master/src/ext-debug-console.adoc>,
  <https://github.com/riscv-non-isa/riscv-sbi-doc/blob/master/src/ext-sys-reset.adoc>
- OpenSBI library and firmware documentation:
  <https://github.com/riscv-software-src/opensbi/tree/master/docs>
- QEMU RISC-V `virt` platform:
  <https://www.qemu.org/docs/master/system/riscv/virt.html>
