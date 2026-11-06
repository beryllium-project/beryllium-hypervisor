<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Architecture Model 0.2 implementation and evidence

## Status and authorization boundary

The accepted implementation for the selected
[Architecture Model 0.2 contract](architecture-model-0.2.md) lives under
`model/` on branch `beryllium/architecture-model-0.2`.

It replaces the Model 0.1 pre-authorized manifest/root input with:

- a bounded normalized platform inventory;
- a copied, untrusted, policy-neutral proposal;
- canonical state produced by complete structural validation;
- an explicit one-way seal;
- roots and mappings derived only from sealed canonical state; and
- activation and switching checked against both canonical and derived state.

Responsible-human review accepted the exact Model 0.2 boundary and evidence on
2026-07-24. A bounded single-hart runtime-planning phase was subsequently
selected. Responsible-human review accepted that exact plan and separately
authorized its fixed implementation profile on 2026-07-25. This does not
transfer any Model 0.2 proof or host-test claim to the runtime and does not
authorize Linux boot, multicore support, devices, policy-framework evaluation,
a protected service, capabilities, TE, VBS/VTL, CHERI, attestation, MVP 1.0,
or public release.

## Quick start and evaluator workflow

Run the complete Model 0.2 and planning-documentation gate:

```sh
./be model-check
```

Run the visible host sequence and targeted gates:

```sh
./be demo
./be test
./be proof
./be report
make -C model unit
make -C model run
make -C model report-check
make -C model proof
```

Run the digest-pinned open rootless evaluator:

```sh
./be evaluate
```

Run the complete repository gate, including retained Helium regressions:

```sh
./be check
```

Helium is a separately labeled evidence set. Its QEMU results do not validate
Model 0.2.

Generated outputs are under:

```text
build/model/host/{gcc,clang}/
build/model/unit/{gcc,clang}/
build/model/reports/
build/model/proof/
build/model/evidence/
build/model-rootless-logs/
```

Generated output is evidence, not maintained source.

### Gate status

| Gate | Status |
| --- | --- |
| Source and open-tool policy | Pass |
| GCC and Clang unit/adversarial suites | Pass |
| GCC and Clang visible sequences for both neutral fixtures | Pass |
| Byte-identical compiler reports and exact cross-source semantic equality | Pass |
| 23 public Rocq obligations plus aggregate claim | Pass |
| 24 closed assumption reports and standalone proof-object check | Pass |
| Planning and Helium link, diagram, browser, and direct-file gates | Pass |
| Complete repository gate, including retained Helium QEMU regression | Pass |
| Pinned Model 0.2 rootless evaluator | Pass |
| Responsible-human Model 0.2 acceptance | Accepted 2026-07-24 |
| K3 hardware | `NOT RUN` |

The dependency-only rootless image retained image ID
`f50fcd0ae612468f99ef008b81215cd0dfb88e90bf66e86f874ffc2706b22c46`
and digest
`sha256:e0dc90771beaa4304bc4694a16ff2721da681daae62e20cfd549d0d573fb4d22`.
No project source is baked into that image; the exact checked source and
artifacts are recorded separately under `build/model/evidence/`.

## Trust and authority boundary

![Model 0.2 authority boundary](/diagrams/model-0.2-boundary.svg)

The platform inventory describes physical extents and immutable platform
classes. It grants no domain authority.

The proposal contains reporting identity, neutral source vocabulary, requested
domain/vCPU/root/stack/saved-state bindings, requested extent classes and
private owners, one directional channel, and requested mapping rights. It is
copied before validation and remains untrusted.

Only canonical state that has passed validation and sealing carries authority.
Proposal identity, vocabulary, and record order are absent from canonical
state. Derived roots, mappings, active bindings, reports, and mutable cache
state cannot add canonical authority.

The deterministic configuration identity is computed from canonical scalar
fields in fixed order. It is an equivalence and reporting identifier, not a
cryptographic digest, integrity measurement, launch measurement, or
attestation value.

## Component and file tour

| Path | Purpose | Trust or evidence role |
| --- | --- | --- |
| `model/include/be/manifest.h` | Inventory, proposal, canonical, derived, rejection, and naming contracts | Encoding-independent Model 0.2 vocabulary |
| `model/src/manifest.c` | Inventory validation, order-independent canonicalization, identity calculation, root derivation, and independent re-checks | Host reference checker; not a runtime refinement |
| `model/include/be/state.h` | Nine phases, activation/switch state, saved registers, and cache interface | Executable host-state contract |
| `model/src/state.c` | Bind, copy, validate, seal, derive, activate, access, switch, fence, and terminal failure | Independently tested reference model |
| `model/src/fixtures.c` | One inventory and two equivalent neutral proposals | Source-vocabulary/order independence inputs |
| `model/tools/model-run.c` | Visible proposal-to-active sequence and inherited switch scenario | Host demonstration only |
| `model/tools/model-report.c` | Deterministic proposal, canonical, and derived JSON | Offline audit artifact; never runtime authority |
| `model/tests/unit/test_main.c` | Positive, rejection, corruption, phase, access, switch, and separation cases | GCC and Clang host evidence |
| `model/tests/check-reports.mjs` | Exact report-shape and cross-source equality gate | No canonical-field normalization is permitted |
| `model/proof/*.v` | Abstract proposal, canonicalization, derivation, isolation, and transition model | Machine-checked bounded properties |
| `model/tests/run-proofs.sh` | Proof escape-hatch scan, compile, assumption ledger, and independent object check | Rocq proof gate |
| `model/tests/generate-evidence.sh` | Source, artifact, tool, claim, and revision identities | Reproducibility evidence |
| `model/Containerfile` | Digest-pinned Fedora evaluator | Open rootless environment |

Every C array is statically bounded. The core uses no heap, recursion,
variadic API, parser, runtime dispatch, guest callback, policy server, or
permissive fallback.

## Inventory, proposal, and canonical state

The inventory contains eleven disjoint page-aligned extents:

- monitor code and data;
- two G-stage root-table extents;
- two trusted-stack extents;
- two saved-state extents; and
- three assignable extents.

An accepted proposal must close exactly over that inventory. Proposed base and
size values must match the inventory; fixed monitor resources cannot be
reclassified; and assignable resources must become exactly two uniquely owned
private frames and one unowned shared-channel frame.

The validator emits canonical arrays in fixed order:

- management then protected domain;
- resource identifier order;
- domain/GPA/frame authority order;
- one saved-state record per domain; and
- one management-to-protected channel.

The proposal may request VMID zero for both roots. This retains the stale
translation hazard and makes the explicit global fence necessary.

## Initialization and failure phases

![Model 0.2 state machine](/diagrams/model-0.2-state-machine.svg)

The executable sequence is:

```text
empty
  -> inventory-bound
  -> proposal-copied
  -> validated
  -> sealed
  -> roots-derived
  -> active
```

`switching` is the only active-domain transition phase. `failed` is terminal.

Important publication rules are:

1. Failed validation leaves canonical and derived outputs zero.
2. Validated canonical state is inspectable but not authoritative.
3. Sealing fails if any producer-published root, mapping, or active binding is
   present.
4. Derivation writes output only after complete canonical validation.
5. Activation independently checks canonical identity, root bindings, mapping
   completeness, and rights subsets.
6. Failure removes all runnable bindings.

A denied well-formed memory request does not invent authority and need not
terminate the model. An invalid phase transition or corrupted internal
binding enters terminal failure.

## Deterministic rejection coverage

| Rejection | Stable result | Representative automated case |
| --- | --- | --- |
| Missing pointer | `null` | absent inventory or proposal |
| Wrong transition phase | `invalid-phase` | derive before sealing |
| Incomplete fixed profile | `incomplete` | missing domain, resource, authority, channel, root, or mapping |
| Unsupported value | `unsupported` | version, vocabulary, VMID, alignment, right, or zero identity |
| Producer-published enforcement | `direct-authority` | proposed root, mapping, active binding, or pre-derivation root state |
| Duplicate inventory/proposal resource | `duplicate-resource` | repeated resource identifier |
| Overlapping inventory extent | `overlapping-resource` | shared/private base collision |
| Proposal outside inventory | `inventory-closure` | unknown ID or mismatched base/size |
| Invalid private owner | `private-owner` | missing, wrong, or duplicated private ownership |
| Monitor state made domain-accessible | `excluded-mapping` | monitor/root/stack/saved extent authority |
| Mapping without exact authority | `undeclared-mapping` | duplicate, changed, or absent domain/GPA/frame relation |
| Derived right exceeds authority | `excess-rights` | injected execute right before activation |
| Undeclared shared storage | `undeclared-shared` | owned or wrong channel backing |
| Invalid channel direction | `channel-rights` | protected write authority |
| Wrong atomic binding | `binding` | vCPU, root, VMID, stack, saved state, or frame mismatch |
| Post-validation mutation | `integrity` | changed canonical or derived configuration identity |

Tests corrupt the inspectable validated and roots-derived seams before sealing
or activation. Those cases corroborate fail-closed checks; they do not prove
that arbitrary C code in the same address space cannot write a C structure.
The abstract proof carries the stronger structural separation between proposal,
canonical, and enforcement types.

## Equivalent neutral proposal fixtures

| Property | `source-a` | `source-b` |
| --- | --- | --- |
| Proposal identity | `0xa102000000000001` | `0xb102000000000002` |
| Neutral source vocabulary | `relations-a` | `relations-b` |
| Domain order | management, protected | protected, management |
| Resource order | ascending | descending |
| Authority order | canonical | reordered |
| Requested mechanism authority | Identical | Identical |
| Canonical configuration identity | `0x2a4c5a62bc446015` | `0x2a4c5a62bc446015` |
| Canonical state | Byte-for-byte JSON equality | Byte-for-byte JSON equality |
| Derived enforcement | Byte-for-byte JSON equality | Byte-for-byte JSON equality |

The report gate compares complete canonical and derived sections exactly. It
does not erase, rewrite, or normalize any canonical field before comparison.
Permitted differences remain confined to the untrusted proposal section.

Neither fixture selects or executes ownership policy, TE, capabilities, RBAC,
MLS/MCS, Rego, Cedar, FLASK, or another policy framework.

## Derived enforcement and retained behavior

Each derived root copies its domain's canonical vCPU, root identifier,
root-table frame, VMID, trusted stack, saved-state identity, and saved-state
frame. Its mappings are generated from canonical authority in canonical order.
The independent enforcement checker requires:

- one exact root per domain;
- complete atomic binding;
- one nonempty mapping for every canonical authority;
- no duplicate mapping;
- only private or explicit-channel backing;
- nonempty valid rights; and
- every derived right to be a subset of exact canonical authority.

After activation, the inherited Model 0.1 behavior remains:

- management private RW succeeds;
- management access to protected private storage denies;
- management channel RW succeeds;
- the source saved-register projection is stored during switch;
- target root, vCPU, VMID, stack, and saved state are selected atomically;
- stale same-VMID translations remain until global `HFENCE.GVMA`;
- target entry before the fence fails;
- protected private RW and channel read succeed;
- protected channel write and management-private access deny; and
- switching back restores management's saved register value.

This is an abstract host model. It executes no privileged instruction.

## Rocq proof boundary

The Rocq 9.2 development contains 23 public bounded obligations plus one
aggregate claim. The runner records 24 closed assumption reports and asks
standalone `rocq check` to validate every generated proof object.

| Area | Public theorem |
| --- | --- |
| Inventory closure | `validation_success_inventory_closure` |
| Complete ownership and binding | `validation_success_complete_ownership_binding` |
| No producer-published authority | `accepted_proposal_has_no_direct_authority` |
| Seal precondition | `sealing_requires_validation` |
| Derivation precondition | `root_derivation_requires_sealing` |
| Failed validation publication | `failed_validation_no_publication` |
| Activation completeness | `activation_completeness` |
| Unique private ownership | `unique_private_ownership` |
| Resource non-overlap | `canonical_resource_non_overlap` |
| Monitor exclusion | `monitor_exclusion` |
| Derived root correspondence | `derived_root_soundness` |
| Derived rights subset | `derived_rights_bounded` |
| Active access soundness | `mapping_soundness` |
| Explicit directional channel | `directional_channel_confinement` |
| Proposal source/order independence | `proposal_source_independence` |
| Source-independent enforcement | `source_independent_enforcement_behavior` |
| Maintained fixture equality | `maintained_proposals_canonicalize_equally` |
| Atomic target binding | `root_domain_binding` |
| Saved-state separation | `saved_state_separation` |
| Entry denied before fence | `pre_fence_target_entry_denied` |
| Switch freshness | `switch_freshness` |
| Canonical immutability | `canonical_state_immutable_after_sealing` |
| Terminal fail-closed behavior | `terminal_fail_closed_behavior` |
| Aggregate | `architecture_model_0_2_claims` |

The source scan rejects `Admitted`, `admit`, project `Axiom`, `Parameter`,
`Conjecture`, `Hypothesis`, `Variable`, `Abort`, unchecked exact terms, disabled
guard checking, and equivalent configured escape hatches.

The proof formalizes one fixed proposal shape, two source vocabularies, forward
and reverse order, one canonical configuration, one derived enforcement
configuration, and the fixed two-domain transition state. It does not prove
arbitrary proposal languages, counts, parsers, C code, or a future root
builder.

Canonical and derived enforcement state are distinct singleton inductive types
for this fixed proof instance. Partial canonical resources, identity-only
enforcement, and incomplete root sets cannot inhabit those types. Activation
therefore requires the complete structural canonical/derived pair, rather than
accepting two matching numeric identities.

The access transition distinguishes a valid active request that is denied from
an access attempted in an invalid phase or corrupted binding. Ordinary denial
preserves state and grants nothing; invalid-state access enters terminal
failure. The channel theorem additionally proves that any one frame reachable
through canonical mappings by two distinct domains is the explicit shared
frame at the shared GPA, with each endpoint bounded by its directional rights.

## Model 0.1 claim and assumption trace

| Model 0.1 property | Model 0.2 disposition |
| --- | --- |
| Initialization completeness | Sharpened into inventory, copy, validate, seal, derive, and activate phases |
| Unique ownership | Retained and connected to complete inventory assignment |
| Monitor exclusion | Retained; saved-state extents are now explicit inventory resources |
| Mapping soundness | Retained and split into canonical authority, derived-root soundness, and active access |
| Root/domain binding | Retained and extended with vCPU and saved-state frame |
| Saved-state separation | Retained as a first-class theorem |
| Channel confinement | Retained as the only modeled cross-domain storage path |
| Switch freshness | Retained with shared VMID zero and explicit fence |
| Fail-closed behavior | Retained and extended across every initialization phase |

Model 0.1 remains the accepted baseline. Model 0.2 does not rewrite its proof
history or transfer any Helium runtime claim.

## Supportable claim and required limit

The strongest supportable statement is:

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

Do not shorten this to “Beryllium is formally verified,” “the C checker is
proved,” “the runtime is verified,” or “policy correctness is proved.”

## Future C and assembly cut points

Model 0.2 sharpens, but does not implement, future privileged cut points:

| Cut point | Model 0.2 precondition | Required postcondition |
| --- | --- | --- |
| Copy inventory/proposal | Bounded independently owned input buffers | Complete private copies or terminal failure |
| Canonical validation | No published root or runnable binding | Complete canonical state or zero publication |
| Seal canonical state | Valid identity and no producer enforcement | Immutable authoritative state |
| Derive roots | Sealed canonical authority only | Complete unpublished roots bounded by canonical rights |
| Activate binding | Canonical and derived re-check succeeds | Domain/vCPU/root/VMID/stack/saved state selected atomically |
| Switch and invalidate | Active source and sealed target binding | Source-only save, target selection, completed fence before entry |
| Authorize access | Active valid binding | Allow only a canonical-bounded derived mapping |

Any future parser, encoding, signing, measurement, PTE format, root builder,
assembly wrapper, interrupt behavior, VMID policy, frame reuse, multicore
invalidation, or device support invalidates the relevant cut point and
requires a separately approved plan.

## Trusted assumptions and non-goals

The result trusts or leaves unverified:

- the maintained contract captures the intended bounded mechanism;
- Rocq 9.2, its kernel, OCaml runtime, and host platform;
- GCC and Clang compilation of the host checker/model;
- correspondence between the C model and documented semantics;
- Node.js report validation and evidence scripts;
- the pinned Fedora package source and container engine; and
- human and LLM review quality.

It excludes:

- a privileged C/assembly implementation or Rocq-to-C refinement;
- compiler/linker/object/ELF/source-to-binary correspondence;
- OpenSBI, QEMU, K3, PMP/ePMP, cache, debug, or secure-lifecycle validation;
- interrupts, timers, SBI virtualization, DMA, IOMMU, IOPMP, and devices;
- multicore, scheduling, migration, concurrency, and availability;
- timing or other microarchitectural channels;
- a stable manifest encoding, parser, signature, measurement, or ABI;
- policy-framework semantics or operator-policy correctness;
- capabilities, CHERI, TE, VBS/VTL, attestation, sealing, or rollback; and
- full state, trace, timing, or information-flow noninterference.

K3 remains `NOT RUN`.

## Open and reproducible tool profile

`model/toolchain.conf` records restricted GNU C11, GCC, Clang, Node.js, Rocq
9.2, GNU Make, and the digest-pinned Fedora base. The evaluator uses only open
tools and runs with networking disabled after image construction.

Cerberus, CN, CBMC, Frama-C, Sail, QEMU, target compilers, proprietary
analyzers, and hosted proof services are not execution dependencies for Model
0.2. Their longer-term dispositions remain in
[Open tooling](open-tooling.md).

## Authoritative references

- [Architecture Model 0.2 contract](architecture-model-0.2.md)
- [Architecture Model 0.1 evidence](architecture-model-0.1-evidence.md)
- [Post-pathfinder architecture decision](pathfinder-comparison.md)
- [M-mode, SBI, and VS control-plane design input](beryllium-hypervisor-notes.md)
- [Open tooling policy](open-tooling.md)
- [RISC-V security-hardware roadmap](riscv-security-hardware.md)
- RISC-V International,
  [Hypervisor Extension](https://docs.riscv.org/reference/isa/priv/hypervisor.html)
- The Rocq Prover,
  [Rocq 9.2 reference manual](https://rocq-prover.org/doc/V9.2.0/refman/)
- seL4, [capDL](https://docs.sel4.systems/projects/capdl/)
- Root `LLM_POLICY_ALIGNMENT.md`
