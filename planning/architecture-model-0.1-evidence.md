<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Architecture Model 0.1 implementation and evidence

## Status

The implementation candidate for the selected
[Architecture Model 0.1 contract](architecture-model-0.1.md) lives under
`model/` on branch `beryllium/architecture-model-0.1`.

It adds:

- encoding-independent canonical manifest structures;
- a fail-closed host reference checker;
- a restricted-C executable state machine;
- normalized minimal-ownership and fixed-TE authority fixtures;
- deterministic authority and mapping reports;
- GCC and Clang positive, negative, and adversarial tests;
- a Rocq 9.2 abstract model and nine bounded proof obligations;
- generated proof, report, source, and tool identities; and
- a pinned open rootless evaluator.

This is not a runtime implementation. It changes no Helium C, assembly,
linker, QEMU behavior, or pathfinder claim. Responsible-human review accepted
the Model 0.1 boundary and refinement direction on 2026-07-22; review
continues incrementally. Runtime, multicore, capability, TE, Linux, device,
and MVP implementation remain unauthorized.

## Quick start and evaluator workflow

Run the Model 0.1 gate:

```sh
./be model-check
```

Run the visible host-model sequence and smaller development gates:

```sh
./be demo
./be test
./be proof
./be report
make model-test
make model-proof
make -C model unit
make -C model run
make -C model report-check
```

Run the pinned rootless model/checker/proof evaluator:

```sh
./be evaluate
```

Run the complete repository gate, including unchanged Helium validation and
the planning documentation:

```sh
./be check
```

`./be evaluate-all` runs the Model evaluator and then the retained Helium
evaluator with separate labels and evidence directories. Helium's QEMU
results remain regression evidence for the completed pathfinder and do not
validate Model 0.1.

Generated outputs are retained under:

```text
build/model/host/{gcc,clang}/
build/model/unit/{gcc,clang}/
build/model/reports/
build/model/proof/
build/model/evidence/
build/model-rootless-logs/
```

Generated outputs are evidence, not maintained source. The canonical source
is under `model/` and `planning/`.

### Gate status

| Gate | Status |
| --- | --- |
| Model source/tool policy | Pass |
| GCC restricted-C unit and adversarial tests | Pass |
| Clang restricted-C unit and adversarial tests | Pass |
| GCC and Clang visible state-machine sequences, both fixtures | Pass |
| Byte-identical GCC/Clang reports and strict semantic checker | Pass |
| Nine Rocq obligations and aggregate claim | Pass |
| Eleven closed assumption reports, including pre-fence denial | Pass |
| Standalone `rocq check` of every proof object | Pass |
| Planning HTML, local links, diagrams, and browser rendering | Pass |
| Direct-file static rendering of every planning and Helium page | Pass |
| Final retained source, artifact, and documentation checksums | Pass |
| Complete repository gate, including unchanged Helium | Pass |
| Pinned Model 0.1 rootless evaluation | Pass |
| Pinned Helium regression evaluation | Pass |
| Responsible-human Model 0.1 acceptance | Accepted 2026-07-22; incremental review continues |
| K3 hardware | `NOT RUN` |

The rootless Model 0.1 run retained image ID
`f50fcd0ae612468f99ef008b81215cd0dfb88e90bf66e86f874ffc2706b22c46`
and digest
`sha256:e0dc90771beaa4304bc4694a16ff2721da681daae62e20cfd549d0d573fb4d22`.
The Fedora base is digest-pinned; installed package versions are retained as
evidence rather than inferred from a mutable package repository.

## Trust and privilege architecture

![Model 0.1 trust and authority boundary](/diagrams/model-0.1-architecture.svg)

The diagram answers one question: which state is inside the abstract trusted
HS boundary, and which cross-domain storage path exists?

The model has one active hart and two mutually untrusted VS-domain
abstractions. HS owns:

- the complete checked configuration;
- both G-stage root identities and VMIDs;
- monitor code/data, root-table, and trusted-stack extents;
- one saved register-state slot per domain;
- the active root/domain/stack/state binding;
- the modeled translation cache and fence-completion flag; and
- the only shared-channel declaration.

Management owns one private frame and may read/write the shared frame.
Protected owns a different private frame and may only read the shared frame.
No other cross-domain storage path is declared. The diagram is an abstract
contract, not a claim that a future Beryllium runtime or K3 hardware already
implements it.

## Component and file tour

| Path | Purpose | Trust or evidence role |
| --- | --- | --- |
| `model/include/be/manifest.h` | Versioned canonical vocabulary, bounds, rights, ownership, roots, mappings, saved state, channel, and checker results | Architecture contract consumed by the C reference implementation |
| `model/src/manifest.c` | Complete deterministic reference validation | Host checker; grants no runtime authority |
| `model/include/be/state.h` | Executable phase, register, cache, and operation interface | Abstract host-state contract |
| `model/src/state.c` | Initialization, entry, access, switch, fence, restore, and terminal failure | Independently tested C reference model; not Rocq-refined |
| `model/src/fixtures.c` | Two fixed canonical configurations | Normalized comparison inputs, not policy engines |
| `model/tools/model-run.c` | Visible end-to-end state-machine sequence | Host demonstration only |
| `model/tools/model-report.c` | Deterministic JSON authority/mapping view | Offline audit artifact; never parsed by a runtime |
| `model/tests/unit/test_main.c` | Positive, rejection, hazard, and state-separation tests | GCC and Clang host evidence |
| `model/tests/check-reports.mjs` | Strict report shape and cross-fixture equivalence check | Offline semantic report gate |
| `model/proof/*.v` | Abstract state, transition, isolation, claim, and assumption modules | Machine-checked bounded properties |
| `model/tests/run-proofs.sh` | Deterministic compile, assumption, and independent object-check pipeline | Rocq proof gate |
| `model/Makefile` | Complete local build/test/proof/report/evidence graph | Normative local command graph |
| `model/Containerfile` | Digest-pinned Fedora evaluator with open dependencies | Reproducible rootless environment |

Every C array is statically bounded. The core uses no heap, recursion,
variadic API, runtime dispatch, parser, guest-selected callback, or hidden
fallback authority. Public types and functions are documented in kernel-doc
style.

## Canonical manifest semantics

`struct be_manifest` records:

- model version, RISC-V architecture, fixed profile, and fixture provenance;
- the sole active hart;
- exactly two immutable domain bindings;
- complete physical extents, classes, and ownership;
- complete domain/GPA/frame maximum authority;
- exactly two disjoint saved-state owners; and
- exactly one management-to-protected channel.

`struct be_root_image` is deliberately separate. It represents what a future
root builder claims to have installed. The checker therefore compares
declared authority with constructed mappings rather than treating a mapping
as self-authorizing.

The C structure is an evaluator representation of the semantics. It is not a
selected JSON, source-language, binary, signing, measurement, stable ABI, or
in-HS parser format.

### Fail-closed rejection coverage

The checker returns one deterministic first rejection:

| Required rejection | Result | Automated example |
| --- | --- | --- |
| Duplicate frame identifier | `duplicate-frame` | duplicate frame mutation |
| Overlapping physical extents | `overlapping-frame` | shared/private extent overlap |
| Missing, multiple, or wrong private owner | `private-owner` | two-domain owner mask |
| Monitor code/data, root table, or trusted stack mapped into VS | `excluded-mapping` | one substitution for every excluded class |
| Mapping absent from declared authority | `undeclared-mapping` | changed GPA/frame and missing leaf |
| Installed PTE rights exceed declared rights | `excess-rights` | added execute permission |
| Shared backing is owned or undeclared | `undeclared-shared` | extra shared frame and private channel backing |
| Endpoint rights violate channel direction | `channel-rights` | protected write authority |
| Root, VMID, stack, or saved state is bound to the wrong domain | `binding` | independent field mutations |
| Required fixed-profile record is absent | `incomplete` | missing domain/root/authority |
| Version, architecture, enum, right, or extent is unsupported | `unsupported` | changed version and malformed rights |

The tests also cover null inputs, duplicate domains and mappings, unaligned
extents, write-without-read, complete mapping-set checks, and immutable
copy-on-seal behavior.

## Executable state machine

![Model 0.1 checked state machine](/diagrams/model-0.1-state-machine.svg)

The visible sequence is:

1. Validate the complete configuration, copy it into model-private state, and
   seal it.
2. Select the management root, VMID, trusted stack, and saved state before
   initial entry.
3. Authorize only the management private mapping and management endpoint of
   the shared channel.
4. Save only management registers, select the protected binding, and enter
   `SWITCHING`.
5. Retain old cached translations so the stale-authority hazard remains
   explicit.
6. Complete global `HFENCE.GVMA`, which clears the modeled cache.
7. Restore only protected saved state and permit protected entry.
8. Authorize protected private access and shared read, while denying
   management-private access and shared write.

Skipping the fence, entering from an invalid phase, selecting the current
domain as a target, corrupting a selected binding, exhausting a bounded
cache, or using an invalid state operation enters terminal `FAILED`.
Subsequent operations cannot become allowed. A well-formed but unauthorized
memory request returns `DENIED` without inventing authority.

The cache lookup intentionally uses VMID and GPA rather than root identity.
The fixed-TE fixture gives both roots VMID zero, so correctness depends on the
root-write-then-fence ordering rather than an assumption that VMIDs differ.

## Fixed fixtures and deterministic reports

| Property | Minimal-ownership fixture | Fixed-TE fixture |
| --- | --- | --- |
| Core model | Identical | Identical |
| Domains | management, protected | normalized writer/reader roles as management, protected |
| Private authority | one RW frame per domain | one RW frame per subject role |
| Channel | management RW -> protected R | writer RW -> reader R |
| Root IDs | 101, 102 | 101, 102 |
| Root-table frame IDs | 3, 4 | 3, 4 |
| VMIDs | 1, 2 | 0, 0 |
| Policy mechanism in core | none | none |
| Provenance identifier | `minimal-ownership` | `fixed-te-fixture` |

`model-report` emits schema `be-model-0.1`. GCC and Clang outputs must be
byte-identical. The Node checker validates the complete object shape and then
normalizes only fixture provenance and VMID values; every remaining
authority, extent, channel, root, and mapping must be identical.

The fixed-TE fixture imports the tested topology, not TE semantics or the
pathfinder's QEMU evidence. The ownership fixture expands the minimal
ownership baseline into the fixed two-domain Model 0.1 instance; it does not
claim the older single-subject runtime implemented this architecture.

## Rocq proof boundary

The Rocq development formalizes the bounded abstract state separately from
the C reference model. It includes:

- fixed management/protected domain identities;
- monitor, private, and shared frames;
- immutable ownership, authority, roots, saved-state bindings, and channel;
- uninitialized, sealed, running, switching, and failed phases;
- root/VMID/stack/state selection;
- a conservative VMID-zero binding shared by both abstract roots;
- disjoint saved register values;
- a modeled cached-translation list; and
- explicit root selection, fence completion, cache clearing, and target
  entry.

The proof runner:

1. rejects `Admitted`, `admit`, project `Axiom`, and `Parameter`;
2. compiles maintained modules in dependency order with Rocq 9.2;
3. records `Print Assumptions` output for every public obligation;
4. requires each theorem to be closed under the global context; and
5. asks standalone `rocq check` to validate every generated proof object.

The supporting theorem `pre_fence_target_entry_denied` proves that target
entry fails after a valid root write but before fence completion, including
the conservative shared-VMID-zero projection.

The exact theorem inventory and checked assumption output are retained under
`build/model/proof/`. The theorem-to-obligation matrix is maintained in the
[Model 0.1 contract](architecture-model-0.1.md#rocq-proof-obligations) and in
`model/proof/Claims.v`.

This result does not establish a refinement relation between Rocq and
`model/src/*.c`. The C implementation is a separately tested reference
executable for the same maintained contract.

## Claim and evidence boundary

![Model 0.1 assurance boundary](/diagrams/model-0.1-assurance.svg)

The supportable statement is:

> Beryllium Architecture Model 0.1 machine-checks bounded ownership, monitor
> exclusion, mapping-rights, domain/root/saved-state binding, directional
> channel, switch-freshness, and fail-closed properties for one fixed abstract
> single-hart, two-domain configuration. A host reference checker rejects
> malformed configurations covered by the Model 0.1 manifest semantics.

Required limit:

> Model 0.1 does not prove a Helium or future Beryllium implementation, C or
> assembly refinement, compiler output, firmware, QEMU, K3 hardware, devices,
> multicore behavior, or full information-flow noninterference.

Do not shorten this to “Beryllium is formally verified,” “the checker is
proved,” “the hypervisor is verified,” or “noninterference is proved.”

### Cross-variant claim and assumption trace

| Input evidence | Reused idea or fixture | Explicitly not transferred |
| --- | --- | --- |
| Original RISC-V, `819251e` | ownership model, bounded H cache/fence lesson, fail-closed host testing | abstract theorem and leaf-C verifier results |
| Dual architecture, `2c0bf53` | architecture-specific invalidation must remain an explicit boundary | Arm execution, TF-A, stage-2, or proof evidence |
| Minimal RISC-V, `cc6029a` | smallest ownership representation and separate authority instances | runtime behavior as a two-domain architecture; removed formal setup |
| Exact proof, `b3f2631` | exact wrapper/layout method and explicit C cut points | exact linked-byte, trap-frame, and fixed-isolation theorem claims |
| Fixed TE, `511187f` | two roots, same-VMID switch hazard, separate saved state, asymmetric shared rights | TE enforcement, policy correctness, QEMU behavior, or formal proof |

The new Rocq theorems apply only to `model/proof/` at the exact checked
revision. The new host results apply only to `model/src/`, its fixed fixtures,
and the recorded GCC/Clang builds. Neither result validates a historical
Helium branch or a future runtime.

## Future C and assembly cut-point contracts

Model 0.1 does not implement the following runtime modules. These contracts
bound a later implementation plan.

### Validate and seal static state

| Field | Contract |
| --- | --- |
| Precondition | Complete supported manifest semantics and independently inspectable root construction input |
| Postcondition | One private immutable copy is valid, all roots/mappings correspond to declared authority, and no domain can enter before the copy is sealed |
| Footprint | Manifest copy, ownership/channel tables, initialization phase; no guest memory |
| Failure | Terminal initialization failure; no partial root or domain publication |
| Architecture assumption | None beyond fixed-width extent arithmetic |
| Obligation | Initialization completeness, ownership, exclusion, mapping, binding, and checker rejection tests |
| Current status | Abstract obligation machine checked; host reference validator tested; future in-HS parser/initializer absent |
| Invalidation | Any manifest field, encoding, parser, publication order, root-builder input, or supported-profile change |

### Construct one root from authority

| Field | Contract |
| --- | --- |
| Precondition | Sealed authority for one bound domain; empty private root storage |
| Postcondition | Every installed leaf names the declared GPA/frame and has a nonempty rights subset; no monitor/root/stack extent is reachable |
| Footprint | Sole domain root and subordinate tables; no other root, saved state, or guest backing |
| Failure | Root remains unpublished and the domain cannot enter |
| Architecture assumption | Ratified RISC-V G-stage descriptor, walk, and permission semantics |
| Obligation | Monitor exclusion and mapping soundness; root report must match manifest |
| Current status | Abstract properties machine checked and C root images checked; no Sv39x4 builder or C refinement in Model 0.1 |
| Invalidation | PTE format, page size, aliasing, huge page, A/D-bit, root-memory, or G-stage builder change |

### Select domain root and trusted stack

| Field | Contract |
| --- | --- |
| Precondition | Source domain is active; target is distinct; both bindings were sealed |
| Postcondition | Target root, VMID, trusted stack, and saved-state identifiers are selected together while target execution remains blocked |
| Footprint | Active/pending binding and architecture root/stack selection only |
| Failure | Terminal failure; no target instruction executes |
| Architecture assumption | `HGATP` and trusted-stack selection have the documented architectural effect |
| Obligation | Root/domain binding and switch-phase tests |
| Current status | Abstract property machine checked; restricted-C host transition tested; future privileged wrapper absent |
| Invalidation | Root/VMID reuse, stack ownership, nesting, interrupt, trap-entry, or target-entry ordering change |

### Save and restore domain state

| Field | Contract |
| --- | --- |
| Precondition | Exact source identity and source-owned live frame; distinct sealed target saved-state record |
| Postcondition | Only source saved state is updated; target state is read only after invalidation; no register residue crosses domains |
| Footprint | Source live frame, source saved slot, then target saved slot; no other domain state |
| Failure | Terminal failure on wrong owner, size, offset, source, or return state |
| Architecture assumption | Future exact assembly wrapper preserves the declared complete architectural state |
| Obligation | Saved-state separation and binding |
| Current status | Bounded abstract register projection machine checked and host tested; exact architectural coverage/C handler refinement absent |
| Invalidation | Register set, trap-frame layout, vector/FPU/debug state, nesting, interrupt, or handler contract change |

### Complete translation invalidation

| Field | Contract |
| --- | --- |
| Precondition | Target root/VMID has been selected; target entry remains blocked; prior cached translations may exist |
| Postcondition | Required RISC-V invalidation is globally complete for the fixed hart and no prior-root cached authority can be used |
| Footprint | Translation-cache state and architecture fence boundary |
| Failure | Terminal failure; target cannot enter |
| Architecture assumption | Ratified `HFENCE.GVMA` ordering and completion semantics for the selected scope |
| Obligation | Switch freshness, explicit stale-cache counterstate, and skipped-fence test |
| Current status | Abstract property machine checked and same-VMID C fixture tested; no privileged instruction or hardware result |
| Invalidation | VMID policy, local/global scope, address-selective fence, multicore, remote fence, IOMMU, or frame-reuse change |

### Authorize mapped access

| Field | Contract |
| --- | --- |
| Precondition | Running domain has a correct sealed binding and fence-complete state |
| Postcondition | Allow only if current translation rights cover the request and originate from declared domain/GPA/frame authority; shared access also matches endpoint direction |
| Footprint | Current root mapping, authority record, channel record, and cache entry |
| Failure | Unauthorized requests deny without adding authority; corrupted internal state fails terminally |
| Architecture assumption | Modeled G-stage access rights correspond to the later architecture-specific enforcement |
| Obligation | Mapping soundness, private ownership, monitor exclusion, and channel confinement |
| Current status | Abstract properties machine checked and host access cases tested; no runtime page-table walk or target binary correspondence |
| Invalidation | Rights vocabulary, cache key, aliases, execute policy, channel direction, capability/TE trigger, or hardware permission semantics change |

## Trusted assumptions and explicit non-goals

The result trusts or leaves unverified:

- the maintained contract accurately captures the intended bounded
  architecture;
- Rocq 9.2, its kernel, OCaml runtime, and host platform;
- GCC and Clang compilation of the host checker/model;
- the C implementation's correspondence to the documented semantics;
- the report generator and Node semantic checker;
- the pinned Fedora package repository and container engine;
- ratified RISC-V H-extension behavior used only as a future cut-point
  assumption; and
- human and LLM review quality.

The result excludes:

- a future C/assembly runtime or model-to-C refinement;
- compiler, linker, object, ELF, or source-to-binary correspondence;
- OpenSBI, QEMU, K3, PMP/ePMP, cache, debug, or secure-lifecycle validation;
- interrupts, timers, SBI virtualization, DMA, IOMMU, IOPMP, or devices;
- concurrency, multicore invalidation, scheduling, migration, or availability;
- timing, cache, predictor, power, thermal, or other microarchitectural
  channels;
- capabilities, CHERI, TE enforcement, VBS/VTL, attestation, sealing, or
  rollback;
- arbitrary manifests, dynamic mutation, a stable ABI, or production parser;
  and
- full state, trace, timing, or information-flow noninterference.

K3 remains `NOT RUN`.

## Open and reproducible tool profile

`model/toolchain.conf` records the normative local profile:

- restricted GNU C11;
- GCC and Clang host compilation;
- Rocq 9.2;
- Node.js report validation; and
- a digest-pinned Fedora rootless base.

The evaluator contains only open-source tools and runs the complete model gate
with networking disabled. Installed exact versions, source hashes, checked
proof-object hashes, report hashes, and claim status are generated under
`build/model/evidence/`.

The retained local/rootless profile reports GNU Make 4.4.1, GCC 16.1.1,
Clang 22.1.8, Node.js 22.22.2, and Rocq 9.2.

No proprietary analyzer, hosted proof service, CHERI toolchain, Sail
H-extension model, Cerberus, CN, CBMC, Frama-C, QEMU, or target compiler is
required for Model 0.1. This does not change their longer-term dispositions in
[Open tooling](open-tooling.md).

## Authoritative references

Checked 2026-07-21:

- RISC-V International,
  [Hypervisor Extension](https://docs.riscv.org/reference/isa/priv/hypervisor.html).
- RISC-V International,
  [Privileged Architecture](https://docs.riscv.org/reference/isa/priv/priv-index.html).
- The Rocq Prover,
  [Rocq 9.2 reference manual](https://rocq-prover.org/doc/V9.2.0/refman/).
- seL4,
  [capDL](https://docs.sel4.systems/projects/capdl/).
- Linux kernel,
  [Protected KVM](https://www.kernel.org/doc/html/next/virt/kvm/arm/pkvm.html).
- RISC-V International,
  [Sail RISC-V H-extension status](https://github.com/riscv/sail-riscv/wiki/Hypervisor-Implementation-Status).

Project evidence and policy:

- [Post-pathfinder architecture decision](pathfinder-comparison.md)
- [Fixed TE evidence](type-enforcement-pathfinder-evidence.md)
- [Minimal ownership evidence](minimal-pathfinder-evidence.md)
- [Open tooling policy](open-tooling.md)
- [RISC-V security-hardware roadmap](riscv-security-hardware.md)
- Root `LLM_POLICY_ALIGNMENT.md`
