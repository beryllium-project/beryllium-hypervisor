<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Minimal RISC-V pathfinder evidence

## Purpose and scope

This document records the third Helium pathfinder variant on
`historical_he/minimal-riscv-poc`.  It preserves the earlier pathfinders' bounded
assigned, denied, and revoked application while deliberately removing:

- the Arm64 backend and TF-A build;
- architecture-neutral portability scaffolding;
- Rocq and Sail integration;
- CBMC, Frama-C, Cerberus, and CN integration;
- the separate proof-oriented C state machine; and
- every runtime component not required by the fixed RV64 scenario.

The exact `cc6029a` checkpoint predates the Helium 0.5.0 rename. It retains
the historical Beryllium / `be` wrapper and `be-authority-v1` schema; those
names below describe immutable evidence, not current interfaces.

It adds one comparison facility: ownership, software-capability, and
capability-plus-flow experiments selected at build time behind the same direct
policy interface and reported through offline authority JSON.

This is a review-and-test PoC.  It is not an MVP, general hypervisor, Linux
isolation result, hardware result, formal-verification result, CHERI
implementation, production policy, or upstream proposal.

## Exact executable chain

```text
QEMU 10.2.2 virt
  -> packaged OpenSBI M-mode
  -> Helium HS-mode
  -> synthetic payload VS-mode
```

One hart runs with interrupts disabled.  VS-stage translation is Bare.  One
fixed Sv39x4 tree maps code, stack, assigned data, and revocable data in a
single 2 MiB GPA region.  The unassigned page has no leaf.

## Gate status

The 2026-07-18 local branch run produced:

| Gate | Status | Evidence |
| --- | --- | --- |
| OpenSBI -> HS -> VS | Pass on QEMU | All model/compiler images enter VS |
| Writable stack | Pass on QEMU | Payload stores and reloads one stack sentinel |
| VS -> HS -> VS event | Pass on QEMU | Cause 10 at exact event PC and phase |
| Assigned page | Pass on QEMU | Read-only sentinel load succeeds |
| Unassigned page | Pass on QEMU | Cause 21, exact GVA/GPA/PC, current policy denial |
| Revocation | Pass on QEMU | Authority removed, exact leaf cleared, global `HFENCE.GVMA` |
| Post-revocation denial | Pass on QEMU | Cause 21 and current policy denial |
| Ownership model | Pass | Host GCC/Clang unit tests and target GCC/Clang QEMU |
| Software-capability model | Pass | Host GCC/Clang unit tests and target GCC/Clang QEMU |
| Capability-plus-flow model | Pass | Host GCC/Clang unit tests and target GCC/Clang QEMU |
| Authority report | Pass | All three `be-authority-v1` documents parse and meet cross-model checks |
| Documentation | Pass locally | Diagrams, 12 Markdown pages, 13 HTML pages, links, desktop/mobile Chromium |
| Rootless evaluation | Pass | Digest-pinned Fedora base, runtime network disabled, resulting image identity retained |
| K3 hardware | `NOT RUN` | No hardware result is inferred from QEMU |

Each target model/compiler cell runs three times.  The target matrix is:

| Model | GCC/GNU ld | Clang/lld |
| --- | --- | --- |
| Ownership | Pass | Pass |
| Software capability | Pass | Pass |
| Capability + flow | Pass | Pass |

The rootless run produced image ID
`e96850719995617728e779cbf3a42505cc26d77e6a907308a07b388bf8045c94`
and digest
`sha256:2304610f70a36724c00a4d2c2d2fe95b18a0b3200d01dacb73db82e94d1c3ae3`.
The exact tool versions and complete logs are retained with the generated
evidence.  The base image is pinned by digest; installed Fedora package
versions are recorded outputs rather than claimed reproducible solely from the
human-readable tag.

## Accepted exit surface

Every model has the same exit surface:

| Cause | Accepted use |
| --- | --- |
| 10, environment call from VS | Assigned event, revoke event, completion event, explicit failure event, each at one exact PC |
| 21, load guest-page fault | Unassigned and post-revocation loads, each at one exact PC and GPA |

Every interrupt and every other synchronous cause is terminal.  There is no
guest SBI proxy, general hypercall ABI, timer, interrupt injection, device
model, or recovery path.

## Policy/mechanism result

The mechanism sources are identical for all models:

- resource configuration;
- G-stage construction and removal;
- runtime phase and exact trap checks;
- privileged CSR/SBI boundary;
- reset, trap, and payload assembly; and
- linker script.

Make links exactly one policy source.  There is no runtime model dispatcher,
function pointer, plugin, guest-selected callback, parser, or bytecode.

### Ownership

Immutable entries record monitor ownership/revocation rights and four guest
grants.  One active-bit mask records revocation.  No derivation graph is
claimed.

### Software capability

Immutable entries record monitor roots and one-level attenuated guest software
capabilities.  Authorization checks active state, parent bounds, matching
resource, monitor root ownership, and rights subset.  One bit mask records
revocation.

These are protected software records in HS memory, not hardware-tagged CHERI
capabilities.

### Capability plus flow

The capability checks remain necessary.  Guest use also requires matching
WORKLOAD labels.  An active guest capability naming the unassigned CONTROL
resource is independently denied by the label rule, making the extra
mediation visible in source and JSON.

This is not a complete information-flow model or selected Type Enforcement
architecture.

## Authority-report result

For each model:

```text
build/pathfinder/<model>/authority.json
```

The native host generator links the same `src/config.c` and selected
`src/policy/<model>.c` as the target.  It reports:

- domains and fixed resources;
- GPAs and least-privilege requested rights;
- initial mapping intent;
- immutable authority entries;
- derivation parents and optional labels;
- active state; and
- initial guest authorization decisions.

The report is not parsed by Helium, does not grant runtime authority, is not
a target measurement, and does not establish source-to-binary correspondence.

## Size comparison

The earlier dual-architecture evidence measured the RISC-V selected
implementation at:

- 1,983 implementation C/assembly/header/linker lines; and
- a 12,288-byte loaded binary under both GCC and Clang.

Using the same source categories, this branch measures:

| Selected model | Source lines | Reduction from 1,983 | GCC loaded binary | Clang loaded binary |
| --- | ---: | ---: | ---: | ---: |
| Ownership | 1,608 | 375 (18.9%) | 12,288 bytes | 12,288 bytes |
| Software capability | 1,637 | 346 (17.4%) | 12,288 bytes | 12,288 bytes |
| Capability + flow | 1,651 | 332 (16.7%) | 12,288 bytes | 12,288 bytes |

The common mechanism and public headers are 1,481 lines before one selected
policy source is added.

The loaded binary does not shrink because both implementations occupy the same
three loaded 4 KiB regions after linker alignment.  The useful result is
reduced source/concept/tool surface while fitting all policy variants inside
the prior 12 KiB loaded size, not a claim of binary-size reduction.

Line count is not a security proof.  The full comparison must also account for:

- removal of Arm and formal/verifier dependencies;
- simpler source and build topology;
- explicit authority visibility;
- unchanged exit surface;
- model-specific state and proof burden;
- lost machine-checked and targeted C evidence; and
- unchanged trust in compiler, firmware, emulator, and hardware.

## Tool-surface comparison

Normative executable/evaluator tools retained:

- GNU Make;
- mainline GCC and GNU binutils;
- mainline Clang and lld;
- QEMU and OpenSBI;
- host GCC and Clang unit tests;
- Node.js for authority JSON and documentation checks;
- Graphviz;
- VitePress, Playwright, and Chromium; and
- rootless Podman for the pinned complete evaluation.

Removed from this branch:

- AArch64 compiler/binutils/QEMU;
- TF-A source and FIP tooling;
- Rocq;
- Sail;
- CBMC;
- Frama-C, Why3, and Z3;
- Cerberus containers; and
- associated proof/verifier harnesses.

This removal narrows evidence as well as dependencies.

## Formal and assurance status

This branch contains no formal-verification setup.

There is no theorem proving, bounded model checking, deductive C verification,
C-semantics execution, model-to-C refinement, assembly proof, translation
validation, or binary proof.

Supported wording:

> The minimal RISC-V Helium pathfinder is a review-and-test PoC.  Its three
> build-time policy experiments pass host unit tests and the same exact
> assigned, denied, and revoked QEMU scenario under GCC and Clang.  It is not
> formally verified and has not been validated on hardware.

The earlier statement about machine-checked abstract models and targeted
verification of one sequential C module applies only to the exact earlier
pathfinder implementation.  It must not be transferred to this branch.

## Assumptions

This branch trusts or leaves unverified:

- GCC, GNU binutils, Clang, lld, and generated target binaries;
- OpenSBI entry, console, and reset behavior;
- QEMU RVH, Sv39x4, trap, fence, and SBI behavior;
- the RISC-V architecture implementation;
- reset, VS-entry, and trap assembly;
- linker layout and identity-mapped HS addresses;
- single-hart, interrupts-disabled execution;
- absence of DMA and devices; and
- human and LLM review quality.

It does not establish:

- arbitrary hostile-guest containment;
- Linux management-domain isolation;
- DMA, interrupt, timer, device, or multicore correctness;
- side-channel resistance;
- secure boot, measurement, or attestation;
- CHERI provenance, bounds, tags, sealing, or temporal safety;
- complete information-flow enforcement;
- K3 hardware behavior;
- availability;
- certification; or
- production readiness.

## Reproduction

```sh
./pathfinder/be test
./pathfinder/be report --model all
./pathfinder/be docs-check
./pathfinder/be check
./pathfinder/be evaluate --arch all
```

Generated evidence is retained under `build/pathfinder/evidence/`.  It records
source state, exact tools, hashes, line and section sizes, accepted exits,
browser screenshots, and variant metadata.

The current local evidence records a dirty implementation working tree.  A
clean reviewed commit requires a fresh complete run before any publication
decision.

## Policy conclusion

All three models fit behind the same mechanism and preserve the same QEMU
behavior.

- Ownership remains the smallest baseline.
- Software capabilities add explicit attenuation and derivation semantics.
- The tiny flow model demonstrates that mandatory policy can deny authority
  already designated by a capability, at additional state and review cost.

This result does not select a permanent policy model.  It supplies a clearer
base for further human/LLM-reviewed experiments and a direct comparison input
for later MVP planning.
