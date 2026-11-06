# RISC-V and SpacemiT K3 security hardware roadmap

## Principle

Beryllium is primarily a RISC-V security research hypervisor. Every relevant platform security feature must be inventoried and assigned an explicit use, deferral, verification, or unsupported status.

Using every feature in the minimal core is not the goal. The goal is to use hardware when it strengthens a stated property without obscuring the reference monitor or inflating the TCB.

## Current R8 boundary

Responsible-human direction on 2026-08-07 authorized R8 planning and selected
single-hart K3 core validation before OS support. The
[R8 plan](single-hart-runtime-r8-plan.md) defines an H0-H4 sequence covering
an exact profile freeze, read-only characterization, fixed synthetic runtime
validation, canonical QEMU/K3 comparison, and exact-target review.

The exact plan target `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` was
responsible-human accepted on 2026-08-07. A later separate instruction
authorizes implementation only for the non-privileged H0 profile freeze. H0
work exposed a documentation-support path and exact-candidate identity defect.
[Plan revision R8-A](single-hart-runtime-r8-plan.md#plan-revision-r8-a-h0-documentation-boundary-and-candidate-identity)
is responsible-human accepted at exact target
`8fa9d672cfcfb81ab68d9ed9553a5af48b884932` on 2026-08-07.

[Plan revision R8-C](single-hart-runtime-r8-plan.md#plan-revision-r8-c-content-based-retired-parent-scan)
is responsible-human accepted at exact target
`f47ae60266a467ca1a7704fd9a50b140e0f31bb0` over parent
`fc6795b03b5f68849fe5ef882d7e2cae77ab4e90` on 2026-09-17. Acceptance
covered the plan for a content-based retired-parent scan correction. The
immutable target retains its proposed pre-decision field; the
[R8-C review and acceptance record](single-hart-runtime-r8-plan-r8c-review-summary.md)
carries the later decision.

Exact bounded non-privileged H0/R8-C target
`1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` (parent
`d18b1c9c6ca8a0f2285f820ec960258620ae4b50`, tree
`7a9d80d08d0abb771d43cf76a4a297d9d668b375`) was responsible-human accepted
on 2026-09-17. On 2026-09-24, the responsible human confirmed that existing
instruction and record as genuine; this is a current-status reconciliation,
not a second acceptance date. The
[H0/R8-C review and acceptance record](single-hart-runtime-r8-h0-review-summary.md)
preserves the exact boundary.

The accepted target remains `BLOCKED-NOT-READY`: 147 rows, 118 `UNKNOWN`,
80 H0-acceptance blockers, 33 H1-completion blockers, three H2-entry blockers,
and `r8_h0_exit=not-met`. The separate historical active-line H0 source at
`102f2b0569396bf33ed2177ea5b7558cf5e6fbaa` reports 81 blockers and is not
the accepted target. The accepted target's exact R8-C paths are
`pathfinder/Makefile`,
`pathfinder/tests/check-source-policy-regression.mjs`, and
`pathfinder/tests/check-source-policy.sh`.

A COM260 board is available, and read-only inventory/troubleshooting occurred
on 2026-09-24. Those observations are session-local discovery, not accepted
target content or retained R8 hardware evidence. K3 remains `NOT RUN`, and
the development kernel/BSP remains `UNDECIDED`. Prospective tree
`8f192c530b03ea33496b95f11ea46537ac02d0b6` is uncommitted diagnostic
content only. Before any H0 successor incorporates COM260 facts, require a
separately reviewed plan, exact base and relation, and explicit authorization.
Exact accepted H0 alone does not authorize H1; H1-H4 remain not started and
unauthorized.

The accepted plan selects no Linux, multicore, device, DMA, policy,
attestation, or production-hardware behavior. The generated-asset
reproducibility and trusted-tool/same-euid residuals remain open, and push,
tag, publication, release, and clean-repository migration remain blocked.

## Confirmed K3/X100 foundations

### CPU and memory virtualization

- RVH 1.0.
- Sv39 and Sv39x4 G-stage translation.
- AIA with IMSIC/APLIC and guest interrupt files.
- Sstc.
- State-enable extensions.
- Fine-grained invalidation and page-based memory-type extensions.

Disposition:

- G-stage is the mandatory PoC isolation mechanism.
- AIA and Sstc are introduced only as needed by the execution payload.
- Full interrupt optimization is deferred until after basic isolation.

### Physical and I/O protection

- 16 PMP entries on X100.
- Smepmp/ePMP is documented.
- Nine IOPMP instances are documented for CPU-external bus masters.
- RISC-V IOMMU is documented for selected PCIe roots.

Disposition:

- PoC records and validates the OpenSBI PMP/Smepmp handoff but does not depend on new PMP programming from HS-mode.
- IOMMU and IOPMP are not PoC requirements because the PoC has no DMA.
- K3 bring-up must inventory firmware ownership, register access, SIDs, locked regions, and default-deny behavior.
- Device-domain work requires IOMMU/IOPMP enforcement and violation tests.

### Secure boot and lifecycle

- Boot ROM.
- eFuse-based secure boot.
- 4096-bit eFuse with bank locking and lifecycle states.
- Root-key and protected-key storage.
- Secure/encrypted boot configuration.
- Non-volatile anti-rollback counter.

Disposition:

- Hardware bring-up records the exact verified-boot chain and lifecycle state.
- MVP planning decides whether secure boot is a required profile or documented platform assumption.
- Attestation work binds Beryllium, the platform descriptor, security manifest, and domain images to the root of trust.

### Cryptography and entropy

- SHA-1, SHA-224, SHA-256, and SM3.
- AES-128/192/256 and SM4 with a key ladder.
- RSA-1024/2048/4096, ECC-128/256/512, and SM2.
- 32-bit TRNG.
- RISC-V vector-crypto extensions and data-independent-timing extensions.

Disposition:

- PoC does not depend on cryptography.
- Hardware bring-up tests TRNG quality/interface availability and crypto-engine isolation.
- Measurement and attestation prefer architecturally visible constant-time/vector primitives or a separately isolated security engine.
- Secret keys must not be exposed to the Linux management domain.

### Counters and side-channel controls

- PMU.
- Counter-overflow and privilege filtering.
- Machine counter filtering documented in the datasheet.
- Data-independent-timing extensions.

Disposition:

- Gate guest counter access conservatively.
- Evaluate PMU filtering as a side-channel reduction and research mechanism.
- Do not claim comprehensive side-channel resistance.

### Cache and coherency

- Cache-block management operations.
- Non-coherent SoC DMA.
- Shared L2 clusters.

Disposition:

- Shared-memory correctness requires explicit cache-maintenance contracts.
- PoC avoids DMA but tests CPU-side shared-memory ordering.
- Device-domain milestones must prove cache and DMA ownership together.

### Debug and trace

- RISC-V external debug.
- JTAG/DTM.
- CPU and system-bus access paths.
- N-Trace.
- Debug-trigger support.

Disposition:

- Lab profiles may use debug and trace.
- Security profiles require debug/trace disablement, authentication, or lifecycle locking.
- Debug state becomes a measured platform property.
- System-bus debug access is treated as a potential isolation bypass.

### RAS and RERI

- ECC/data-check/poison capabilities.
- RERI framework.

Disposition:

- Later hardening work records and contains platform error events.
- Protected-domain results must not remain silently valid after an uncontained hardware error.

### GPU and accelerator virtualization

- Up to eight virtual GPU instances.
- Lane isolation and per-context interrupts.
- Dedicated GPU firmware processor.

Disposition:

- Later research only.
- Requires documented GPU isolation, firmware trust analysis, IOMMU/IOPMP enforcement, reset ownership, and fault containment.

## RISC-V features to track beyond K3

- CHERI-RISC-V and application-class CHERI cores.
- CoVE/AP-TEE.
- Smmtt or successor memory-tracking mechanisms.
- RISC-V IOMMU ecosystem maturity and device assignment.
- QoS/capacity and bandwidth identifiers.
- Confidential-computing attestation.
- Future debug, RAS, and platform-security standards.

These features may become future targets but do not define the K3 PoC.

## Hardware-phase mapping

### Pathfinder PoC

- RVH/G-stage.
- Minimal trap and SBI behavior.
- Minimal AIA/Sstc only if required.
- PMP/Smepmp handoff observation.
- Security-feature inventory.

### R8 single-hart K3 core validation

- Preserve exact accepted H0/R8-C target
  `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` and its blocked,
  not-exit-ready evidence.
- Treat COM260 inventory/troubleshooting as session-local discovery until a
  separately reviewed successor plan/base/relation and explicit authorization
  permit those facts to enter maintained H0 evidence.
- Do not start H1-H4 or K3 execution. Exact accepted H0 alone does not
  authorize H1.
- Confirm ISA and CSR behavior.
- Confirm secure-boot/lifecycle state.
- Confirm PMP/Smepmp lockdown.
- Confirm AIA/Sstc/state-enable behavior.
- Confirm TRNG and crypto engine.
- Confirm debug/trace controls.
- Confirm cache-maintenance behavior.
- Locate and characterize IOMMU/IOPMP.
- Keep every non-participating X100 hart parked and measured as a firmware
  assumption.
- Execute no OS, guest-visible SBI, device, or DMA workload.
- Stop for a plan revision if optional architectural state or a common-core
  change is required.

### Candidate MVP 1.0 inputs

- Hypervisor-first boot.
- G-stage protected domain.
- Bounded AIA/Sstc support.
- State-enable and counter gating.
- Local measurement.
- Explicit secure-boot assumptions or profile.
- K3-specific conformance report.

### Later research

- IOMMU/IOPMP device domains.
- Crypto-backed remote attestation.
- RAS/RERI containment.
- GPU/accelerator domains.
- Stronger side-channel profiles.
- CHERI and CoVE-class hardware.

## Open hardware questions

- Exact VMID width and usable AIA guest-file count.
- Mainline and vendor IOMMU description.
- IOPMP ownership and firmware interface.
- PMP/Smepmp lock state after OpenSBI handoff.
- Secure-boot key provisioning and lifecycle state.
- Debug-lockdown behavior.
- TRNG and crypto-engine software interfaces.
- RERI delegation and error routing.
- GPU virtualization programming interface and firmware trust.

Primary sources:

- https://raw.githubusercontent.com/spacemit-com/docs-chip/main/en/key_stone/k3/k3_docs/k3_ds.md
- https://github.com/spacemit-com/docs-chip/blob/main/en/key_stone/k3/k3_docs/k3_usermanual/15_security.md
- https://lore.kernel.org/linux-riscv/20260115-k3-basic-dt-v5-6-6990ac9f4308@riscstar.com/

Controlling project plan:

- [R8 single-hart K3 core-validation plan (accepted incl. R8-A and R8-C)](single-hart-runtime-r8-plan.md)
