<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Sidebar: Rust for future VS components

## Status and scope

This is a design brainstorm, not runtime authorization. The restricted-C HS
core and Rocq direction remain unchanged.

No current privileged C runtime is proved as a refinement of the Rocq model.
"C isolation TCB" below describes the selected future language and assurance
boundary, not a claim about an implemented verified hypervisor.

Rust is a credible candidate for future VS management and service components.
That does not mean every byte is safe Rust, and it does not automatically keep
all Rust code outside every trusted computing base.

## Separate the trusted bases

| Claim | Required trusted code |
| --- | --- |
| HS structural isolation | restricted-C/assembly HS core, hardware, firmware assumptions |
| One VS service cannot map another | HS core only, if the service is treated as malicious |
| A secrets service returns the right cryptographic result | HS core plus that Rust service and its crypto dependencies |
| A policy service implements operator intent | HS core plus policy service, policy input, compiler, and semantic argument |
| Service availability | HS scheduler/lifecycle mechanism plus service and dependencies |

The **isolation TCB** can remain C. A Rust service becomes part of a
service-specific TCB whenever a claim depends on its correct semantics.

## What "pure Rust" can honestly mean

A realistic bare VS component has four layers:

1. **Safe service logic:** parsers, state machines, bounded queues, policy
   adapters, and application logic can forbid `unsafe`.
2. **`no_std` runtime:** uses `core` and optionally `alloc`; a bounded service
   should prefer fixed pools or `heapless` structures where availability
   matters.
3. **Audited unsafe platform crate:** startup, trap entry, `ecall`, MMIO,
   volatile shared memory, allocator internals, and FFI require unsafe code or
   assembly.
4. **Toolchain and dependency base:** `rustc`, core libraries, proc macros,
   linker, crates, and generated bindings remain trusted or separately
   validated.

The supportable claim is therefore:

> The service logic is safe Rust, while all unsafe and assembly operations are
> confined to a small enumerated platform boundary.

"No unsafe anywhere in the binary" is not a credible bare-metal requirement.

## Can privileged primitives have safe Rust interfaces?

Usually this needs a library boundary, not a Rust language extension. In Rust,
`unsafe` marks memory-safety obligations; it is not a privilege or
authorization marker. A privileged operation can have a safe public function
when a small audited implementation can uphold Rust's aliasing, lifetime,
layout, and initialization rules for every safe input.

A future VS platform crate could therefore:

- keep constructors for MMIO windows, shared mappings, channel endpoints, and
  privileged-call handles private;
- contain the raw pointers, volatile operations, assembly, `ecall`, and FFI;
- expose fixed-size byte messages and validated handle types rather than raw
  addresses or cross-domain Rust references;
- use typestate or ownership to prevent use before initialization, concurrent
  mutable aliases, or reuse after teardown; and
- return explicit authorization, phase, timeout, and platform errors.

This does not make the operation policy-safe. A safe Rust call can still ask
for an unauthorized mapping, leak a secret, deadlock, or implement the wrong
policy. HS must authenticate the current domain and independently validate the
object, rights, channel, generation, and actual operation. Unsafe code must not
serve as the access-control boundary.

Rust-for-Linux demonstrates the useful pattern: concentrate C FFI and unsafe
contracts in reviewed kernel abstractions and expose narrower safe APIs above
them. Its `kernel` crate is not a reusable VS runtime and does not supply
RISC-V VS startup, SBI, trap, or interrupt behavior.

## Why Rust is attractive in VS

- memory-safe parsing and serialization reduce accidental malformed requests;
- ownership and typestate can encode lifecycle transitions;
- `Send`/`Sync` rules constrain data races in safe code;
- `panic=abort` gives a predictable domain failure instead of continuing after
  undefined behavior;
- Rust's crate ecosystem offers reusable protocol and virtio components; and
- an isolated service can be restarted without adding Rust to the HS core.

These benefits do not weaken the Model 0.2 rule: HS validates every VS input
independently of the producer language.

## Risks and costs

- unsafe FFI and hardware wrappers concentrate severe bugs at a narrow but
  powerful boundary;
- dependency and proc-macro supply chains are larger than a small C core;
- panic or allocator exhaustion can become an availability failure;
- async runtimes and unbounded allocation complicate deterministic behavior;
- stable Rust support for RISC-V is good, but VS-specific startup, AIA/IMSIC,
  trap, and SBI integration still needs platform code;
- most Rust VMM projects assume Linux/KVM and cannot be reused as bare VS
  runtimes; and
- memory safety is not functional correctness, policy correctness, or
  noninterference.

Each service needs a watchdog, bounded restart protocol, idempotent channel
operations, and explicit handling for a dead peer.

## C/VS-Rust boundary

The preferred interface shape is a small hypercall/SBI extension plus explicit
directional shared buffers:

```text
safe Rust service logic
        |
audited Rust channel/platform crate
        |
SBI-style ecall + bounded shared message
        |
restricted-C HS validation and enforcement
```

Boundary rules:

- use fixed-width integers and explicit endianness;
- never pass HS pointers or Rust references across the boundary;
- version every message and reject unknown flags or trailing authority;
- bind requests and replies to domain, channel, configuration identity, and
  generation;
- use `#[repr(C)]` only with independent C/Rust layout checks;
- keep payload size and queue depth statically bounded;
- make retry, timeout, duplicate, cancellation, and restart behavior explicit;
- prohibit unwind across FFI; and
- fuzz and model-check both encoders and decoders.

Generating both sides from one schema is attractive only if the generator and
schema semantics are themselves reviewable and reproducible.

## Isolation choices for mixed C and Rust

Putting C and Rust in one conventional address space is not an isolation
boundary. Unsafe C can corrupt safe Rust state through shared memory,
incorrect FFI, or an over-broad pointer. Three different designs should not be
conflated:

| Placement | Isolation mechanism | Main consequence |
| --- | --- | --- |
| Separate VS domains | Distinct G-stage roots plus explicit channels; IOMMU for DMA | Language-independent strong fault boundary, with transition, protocol, lifecycle, and scheduling cost |
| CHERI compartments in one CHERI-enabled VS | Bounded capabilities, explicit sharing, and sealed compartment calls | Finer-grained in-address-space authority, but one runtime and a developing Rust/CHERI ABI and toolchain |
| C and Rust in one ordinary VS address space | Rust type and memory safety only where its assumptions hold | No containment from malicious or memory-unsafe C without another process, stage-1, or software-fault-isolation boundary |

CHERI can isolate C and Rust components inside one VS if each compartment
receives only explicit capabilities and cross-compartment entry uses a
controlled call gate. It does not replace G-stage isolation between VS
domains, IOMMU/IOPMP protection for DMA, or the service's semantic
correctness. On non-CHERI hardware, separate VS domains are the clearer strong
boundary when C and Rust must be mutually distrusted.

Mixed-language CHERI also requires an explicit ABI experiment. Pure-capability
pointers carry bounds, permissions, provenance, and tags; inappropriate
integer fields, copies, alignment, prototypes, or variadic calls can lose or
mis-handle that metadata. Both sides should use the same reviewed purecap ABI,
export only bounded non-variadic types, and independently test layout and
capability behavior. Hybrid mode may ease legacy migration, but it is not a
basis for the strongest compartment claim. HS/VS wire messages should remain
pointer-free regardless of the in-domain ABI.

## Reusable ecosystem, with limits

| Project | Useful lesson | Why it is not a drop-in VS service |
| --- | --- | --- |
| rust-vmm | memory, virtio, queue, and device-model crates | much of the stack assumes Linux/KVM |
| Firecracker | minimal interfaces and explicit threat model | host KVM VMM |
| crosvm | device/process decomposition | host process sandbox architecture |
| Cloud Hypervisor | Rust VMM and experimental RISC-V work | host KVM dependency |
| OpenVMM/OpenHCL | Rust paravisor and service decomposition | no RISC-V; different trust/hardware model |
| Salus | RISC-V `no_std` HS and SBI interface precedent | HS project, not VS runtime; repository is archived |
| Hermit | Rust `no_std` RISC-V unikernel | must be proven to boot correctly as a Beryllium VS guest |
| RustSBI/riscv crates | RISC-V calling and CSR patterns | not a complete service runtime |

The most reusable pieces are likely bounded protocol, virtio, memory, and FDT
crates, not an existing complete VMM.

## Open verification options

| Tool | Useful bounded claim | Important limit |
| --- | --- | --- |
| Kani | bounded panic/UB/assertion checks for safe portable logic | assembly and hardware behavior must be stubbed; bounds matter |
| Verus | SMT-backed functional correctness, protocol/state-machine invariants, and selected concurrent structures | verifier/rustc/Z3/specification TCB; no Rocq proof object or hardware refinement |
| Creusot/Why3 | sequential functional correctness | limited unsafe, concurrent, and platform coverage |
| Flux | refinement types for state and resource invariants | not whole-system verification |
| Aeneas/Charon | extraction of safe sequential Rust to Rocq/Lean/F*/HOL4 | alpha; unsafe, assembly, globals, and concurrency are restricted |
| RefinedRust | Coq/Iris reasoning about safe and unsafe Rust abstractions | research prototype; no demonstrated VS/hypervisor workflow |
| Prusti/Viper | contract, panic, and overflow checking for a Rust subset | prototype backend outside the Rocq strategy; current systems trajectory must be revalidated |
| RustBelt/Iris | foundation for reasoning about Rust and unsafe abstractions | research framework, not a turnkey verifier |

Aeneas/Charon is strategically interesting because it can place safe Rust
logic in the same broad proof ecosystem as the HS Rocq work. It should be
treated as a feasibility experiment, not a selected refinement path.

### Verus disposition

Verus is the strongest current practical candidate for a future bounded Rust
VS service core. It is an active MIT-licensed verifier for a substantial Rust
subset with:

- executable, specification, and proof modes;
- ghost state erased from generated code;
- preconditions, postconditions, loop invariants, and mathematical models;
- linear ghost resources and state-machine support; and
- VerusSync abstractions for selected locks, atomics, cells, and concurrent
  protocols.

The strongest first Beryllium fit would be a safe, sequential, fixed-allocation
crate implementing:

- a bounded wire-message parser and serializer;
- one service lifecycle or channel state machine;
- capability-like handle and rights invariants;
- retry, generation, duplicate, and restart rules; and
- a fixed-size queue or abstract storage invariant.

The SOSP 2024 evaluation includes distributed-system, OS page-table,
replication, crash-safe storage, and concurrent-allocator case studies. This
is credible low-level component evidence. It is not evidence for a verified
RISC-V hypervisor, `HGATP`, assembly, firmware, or hardware refinement.

Important boundaries are:

- async/await, ordinary function pointers, `Pin`, hardware intrinsics,
  printing/I/O, user `Drop`, and several low-level Rust features are
  unsupported or partial;
- raw pointers, statics, casts, unions, FFI-adjacent code, and multi-crate
  verification need special treatment;
- `external_body` assigns an assumed specification to unverified code rather
  than proving that code;
- a `global layout` declaration adds an axiom plus a code-generation check;
  `#[repr(C)]` alone gives Verus no layout theorem;
- `vstd` feature structure makes an `alloc`/non-default-feature experiment
  plausible, but does not establish a supported bare-metal RISC-V VS target;
  and
- a passing run produces Verus/SMT evidence, not a portable Rocq-checkable
  proof certificate.

The trusted evidence base includes the Verus/rustc integration, Z3, verified
specifications, explicit axioms and external bodies, Rust code generation,
linker, and every platform assumption. Assembly, `ecall`, MMIO, volatile
shared memory, cache/fence effects, C FFI, and hardware remain outside the
Verus result unless separately connected.

The recommended future tool split is:

1. **Verus:** unbounded functional protocol and state-machine properties for
   one safe Rust service core.
2. **Kani:** bounded counterexamples and regression checks for integer, ABI,
   panic, and selected unsafe-wrapper behavior.
3. **Aeneas/Charon:** a separately pinned experiment for extracting one safe
   sequential Rust model into the project's Rocq ecosystem.
4. **RefinedRust/RustBelt:** foundational research input when a concrete unsafe
   abstraction justifies the substantially higher proof cost.

No direct Verus-to-Rocq proof exchange is currently established. Rocq remains
primary for the Beryllium architecture, ISA, and refinement argument; Verus
would be a separately labeled service-component evidence set.

## CHERI and CHERIoT alignment

Rust and CHERI are complementary:

- Rust reduces accidental memory-safety failures inside a compartment.
- CHERI can constrain authority and damage when code or dependencies are
  malicious or unsafe.
- Beryllium G-stage roots currently provide domain-scale spatial isolation,
  not CHERI object capabilities.

Writing VS services in Rust departs from a C-first implementation preference,
but not from the deeper alignment principles: explicit authority, narrow
interfaces, bounded sharing, compartmentalization, and fail-closed behavior.

CHERIoT Rust is a useful research input, but its microcontroller target and
calling conventions cannot be assumed to apply to RV64 H-extension systems.
Its current Rust fork is experimental and does not yet provide a
production-ready application-class CHERI-RISC-V VS stack.

## Bounded experiments

1. **Portable safe core:** implement only a parser and lifecycle state machine
   as `no_std`, no-unsafe Rust library code.
2. **Verus protocol probe:** prove transition legality, bounded queue
   invariants, and directional-channel behavior for the portable safe core,
   while enumerating every axiom and external body.
3. **Kani harness:** prove bounded panic freedom and rejection of every invalid
   message shape.
4. **Rocq extraction probe:** run Aeneas/Charon on the safe state-machine crate
   and prove one invariant in the existing Rocq environment.
5. **ABI probe:** generate or hand-maintain one C/Rust message and independently
   check size, alignment, offsets, and byte encoding under GCC, Clang, and
   rustc.
6. **VS boot stub:** only under a new bounded plan, boot one Rust stub, issue
   one SBI-style request, and enumerate every unsafe/assembly line.

## Future decision gate

Rust should be selected for a VS component only if:

- it materially reduces the component's expected attack surface;
- all unsafe and assembly code is enumerated and bounded;
- required RISC-V/VS support exists without a broad compatibility layer;
- the C/Rust protocol is mechanically checked and independently parsed;
- failure and restart behavior is acceptable;
- open verification tools produce useful evidence at sustainable cost; and
- service-specific trust is stated rather than hidden behind "Rust safety."

## Primary references

Checked 2026-07-24:

- Rust Reference, `unsafe`:
  <https://doc.rust-lang.org/reference/unsafe-keyword.html>
- Rustonomicon, safe FFI wrappers and unwinding:
  <https://doc.rust-lang.org/nomicon/ffi.html>
- Rust Reference, type layout:
  <https://doc.rust-lang.org/reference/type-layout.html>
- Rust-for-Linux kernel and safety modules:
  <https://github.com/torvalds/linux/blob/master/rust/kernel/lib.rs>,
  <https://github.com/torvalds/linux/blob/master/rust/kernel/safety.rs>
- Rust embedded RISC-V crates:
  <https://github.com/rust-embedded/riscv>
- rust-vmm:
  <https://github.com/rust-vmm>
- Cloud Hypervisor RISC-V:
  <https://github.com/cloud-hypervisor/cloud-hypervisor/blob/main/docs/riscv.md>
- Firecracker:
  <https://github.com/firecracker-microvm/firecracker>
- crosvm:
  <https://github.com/google/crosvm>
- OpenVMM/OpenHCL:
  <https://github.com/microsoft/openvmm>
- archived Salus reference:
  <https://github.com/rivosinc/salus>
- Hermit kernel:
  <https://github.com/hermit-os/kernel>
- Kani:
  <https://github.com/model-checking/kani>
- Verus:
  <https://github.com/verus-lang/verus>
- Verus guide, supported features, TCB, and unverified-code boundary:
  <https://github.com/verus-lang/verus/blob/main/source/docs/guide/src/features.md>,
  <https://github.com/verus-lang/verus/blob/main/source/docs/guide/src/tcb.md>,
  <https://github.com/verus-lang/verus/blob/main/source/docs/guide/src/calling-unverified-from-verified.md>
- Lattuada et al., Verus systems evaluation:
  <https://www.microsoft.com/en-us/research/publication/verus-a-practical-foundation-for-systems-verification/>
- Creusot:
  <https://github.com/creusot-rs/creusot>
- Flux:
  <https://github.com/flux-rs/flux>
- Aeneas and Charon:
  <https://github.com/AeneasVerif/aeneas>,
  <https://github.com/AeneasVerif/charon>
- RustBelt:
  <https://plv.mpi-sws.org/rustbelt/>
- RefinedRust:
  <https://plv.mpi-sws.org/refinedrust/>
- Prusti:
  <https://github.com/viperproject/prusti-dev>
- David Chisnall, Rust and CHERIoT:
  <https://cheriot.org/rtos/publication/2025/11/21/rust-coming-to-cheriot.html>
- CHERIoT compartment model:
  <https://cheriot.org/book/compartments.html>
- Experimental CHERIoT Rust fork:
  <https://github.com/CHERIoT-Platform/cheri-rust>
- CHERI C/C++ provenance, representation, and calling conventions:
  <https://ctsrd-cheri.github.io/cheri-c-programming/impact/pointer-provenance-validity.html>,
  <https://ctsrd-cheri.github.io/cheri-c-programming/impact/capability-representation.html>,
  <https://ctsrd-cheri.github.io/cheri-c-programming/impact/function-prototypes-and-calling-conventions.html>
- Existing project alignment:
  [CHERI alignment](cheri-alignment.md)
