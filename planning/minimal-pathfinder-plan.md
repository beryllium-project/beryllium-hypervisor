<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Minimal RISC-V pathfinder plan

## Status

This plan defines the third Helium pathfinder PoC on the
`historical_he/minimal-riscv-poc` branch.  It is intended for direct comparison
with:

1. the original RISC-V, proof-oriented pathfinder;
2. the dual-architecture RISC-V and Arm64 pathfinder; and
3. this RISC-V-only, review-oriented pathfinder.

This branch does not replace the evidence retained on either earlier branch.
It asks a different question: how small and understandable can the same
isolation demonstration be when simplicity, economy of mechanism, and clarity
are treated as security properties?

## Application

The executable behavior remains deliberately unchanged:

```text
OpenSBI M-mode -> Helium HS-mode -> synthetic payload VS-mode
```

The payload:

1. reads one assigned page;
2. traps on one page that was never assigned;
3. reads one revocable page;
4. asks Helium to revoke that page;
5. traps when it reads the revoked page again; and
6. reports completion.

Helium accepts only the exact VS `ECALL` and load guest-page-fault
transitions required by that sequence.  Every other trap, interrupt, address,
program counter, event, or state transition fails closed.

## Security strategy

The design applies economy of mechanism before adding analysis machinery:

- one ISA, one hart, one guest, and one fixed QEMU platform;
- one statically allocated Sv39x4 tree covering one 2 MiB GPA region;
- one private test protocol rather than a general hypercall ABI;
- one explicit trap/return boundary;
- no allocator, scheduler, device model, interrupt injection, timer
  virtualization, DMA, IOMMU programming, Linux guest, or runtime policy
  language;
- no architecture-neutral abstraction retained solely for hypothetical ports;
  and
- no formal-proof, C-verifier, or Sail dependency in this branch.

The implementation remains restricted GNU C plus a thin assembly and
privileged-CSR boundary.  Both GCC/GNU ld and Clang/lld build and run every
configuration.

## Chisnall and CHERIoT alignment

This branch borrows principles and artifact patterns, not CHERI-specific
implementation:

- authority is distinct from a resource identifier;
- delegation is explicit and monotonically attenuated;
- the most-privileged transition path is tiny and directly inspectable;
- sharing and revocation receive more scrutiny than initial isolation;
- component authority is emitted as an offline, machine-readable report; and
- security properties should be understandable from interfaces and authority
  relationships.

The K3 and QEMU targets do not implement CHERI.  The capability experiments
therefore use core-held **software capabilities**.  They are not hardware-tagged
CHERI capabilities, do not provide CHERI spatial or temporal memory safety,
and must not be described as equivalent to CHERI.

The following technology decisions are deliberate:

| Technology | Decision | Reason |
| --- | --- | --- |
| GNU Make | Retain | It is sufficient, locally transparent, and aligned with the prospective Linux/Kbuild destination. |
| Mainline GCC and Clang/lld | Retain | Standard RV64 is the target; the CHERIoT LLVM fork implements a different pure-capability target and ABI. |
| QEMU `virt` and OpenSBI | Retain | They provide the smallest reproducible RV64 H-extension execution chain. |
| Link-time authority JSON | Adapt concept | A small native report generator consumes the same configuration and policy source as the image. |
| `cheriot-audit` and Rego | Defer | The report-and-offline-audit pattern is useful, but the alpha tool and rich policy engine are unnecessary dependencies here. |
| xmake | Reject | CHERIoT itself records problems with its use and may replace it; adding it would increase this PoC's tool surface. |
| CHERIoT RTOS, switcher ABI, sealing, and runtime | Reject as code | They require CHERI mechanisms and a microcontroller execution model that standard RV64 H does not provide. |
| CHERIoT LLVM and Sail forks | Reject for this branch | They target CHERI semantics, not the standard H-extension execution path. |
| TestRIG / RVFI-DII | Defer | Its differential-testing pattern remains useful, but mainline Sail still lacks the complete H semantics exercised here. |
| snmalloc or another heap | Reject | The complete PoC uses static allocation. |

## Fixed mechanism and variable policy

The executable mechanism owns:

- VS entry and exit;
- exact trap validation;
- fixed G-stage PTE installation and removal;
- `HFENCE.GVMA` ordering;
- the test sequence; and
- fail-closed shutdown.

Policy is selected at build time.  Exactly one implementation of a small,
direct C interface is linked:

```text
reset -> authorize(subject, resource, rights) -> revoke(actor, resource)
```

There is no function-pointer dispatch, plugin loader, bytecode interpreter,
policy parser, or policy callback chosen by untrusted input.  The trap path
contains one direct call to the selected implementation.  Changing the model
does not change trap assembly, page-table code, guest code, or the test
protocol.

Three initial experiments exercise that seam:

### Ownership and explicit grants

The monitor owns physical resources and records fixed rights granted to the
guest.  Revocation clears one grant.  This is the smallest baseline.

### Software capabilities

The monitor holds root capabilities and derives attenuated guest capabilities.
Authorization requires an active capability held by the subject for the
resource and requested rights.  Revocation invalidates the selected derived
authority.  Capability state remains private to Helium.

### Software capabilities plus mandatory flow

Capability checks remain necessary.  A second, fixed label rule may deny an
operation even when a software capability exists.  The initial experiment
uses a deliberately tiny two-label model to expose the composition cost; it is
not a selected Type Enforcement architecture or a production information-flow
policy.

These models are experiments, not three supported security products.  New
models may implement the same interface when they can preserve the fixed
mechanism and test behavior.

## Authority report

Each image build also produces a deterministic JSON report from the same
resource table and selected policy source.  It records:

- schema and selected model;
- domains and fixed resources;
- GPA and requested rights;
- authority entries and derivation parents;
- optional subject and object labels; and
- the initial authorization result for each entry.

The report is an offline review artifact.  It is not parsed by Helium and
does not grant runtime authority.  Its design is conceptually aligned with
CHERIoT linker reports and `cheriot-audit`, but it is intentionally much
smaller and does not claim schema compatibility.

## Assurance and claim limits

This branch is not set up for formal verification.  It contains no Rocq proof,
Sail-generated model, CBMC harness, Frama-C contract, Cerberus runner, or
source-to-binary correspondence result.

Supported claims are limited to:

- source review;
- host unit tests;
- GCC and Clang warning-clean builds;
- deterministic QEMU execution of the fixed scenario;
- exact trap, address, PC, and state checks;
- offline inspection of generated authority reports; and
- retained source, binary, disassembly, size, and execution artifacts.

The compilers, linkers, OpenSBI, QEMU, RISC-V architectural implementation,
assembly boundary, and hardware remain trusted or unverified.  No K3 hardware
result, Linux isolation result, CHERI property, formal-verification claim,
certification claim, or production-hardening claim follows from this PoC.

## Comparison evidence

The branch records, for every model and both compiler/linker combinations:

- selected implementation source lines;
- loaded binary and section sizes;
- accepted exit surface;
- complete authority JSON;
- ordered QEMU transcript;
- disassembly; and
- exact tool and source identities.

The meaningful comparison is not only line count.  Review must also compare:

- number and complexity of trusted concepts;
- privileged transition size;
- policy coupling to the mechanism;
- failure behavior;
- dependency and evaluator burden;
- auditability of authority and sharing;
- ease of adding a new policy experiment; and
- the assurance lost by removing the formal and verifier work.

## Success criteria

This pathfinder variant succeeds when:

1. all three models produce the same assigned, unassigned, and revoked QEMU
   behavior under GCC and Clang;
2. every model uses identical mechanism, guest, and assembly sources;
3. each authority report is generated from the exact selected policy source;
4. the implementation and evaluator workflow contain no Arm or formal-tool
   dependency;
5. the complete source, trust boundary, inputs, outputs, assumptions, failure
   behavior, and non-goals are documented for a reviewer unfamiliar with
   RISC-V virtualization; and
6. evidence is sufficient for an explicit comparison with the two earlier
   pathfinder branches.

## Primary references

Accessed 2026-07-18:

- David Chisnall, [Identifiers are not capabilities](https://cheriot.org/cheri/philosophy/2025/01/19/capabilities-not-identifiers.html).
- David Chisnall, [I don't care about memory safety](https://cheriot.org/philosophy/2025/02/07/i-do-not-care-about-memory-safety.html).
- CHERIoT RTOS commit
  [`9ba8deb778520c366fc3582d804ac78a11dba43b`](https://github.com/CHERIoT-Platform/cheriot-rtos/commit/9ba8deb778520c366fc3582d804ac78a11dba43b).
- `cheriot-audit` commit
  [`3e8e66bd7e52b393ff22b2d99195bcc6825c57e8`](https://github.com/CHERIoT-Platform/cheriot-audit/commit/3e8e66bd7e52b393ff22b2d99195bcc6825c57e8).
- CHERIoT LLVM commit
  [`489f372413a0a1b883582f9ab0f3ab88b8643f54`](https://github.com/CHERIoT-Platform/llvm-project/commit/489f372413a0a1b883582f9ab0f3ab88b8643f54).
- CTSRD TestRIG commit
  [`70717956d9a0445a11ac9a070387d119c523d60f`](https://github.com/CTSRD-CHERI/TestRIG/commit/70717956d9a0445a11ac9a070387d119c523d60f).
- RISC-V privileged architecture, ratified hypervisor extension:
  <https://docs.riscv.org/reference/isa/priv/hypervisor.html>.
