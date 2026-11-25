# RISC-V and SpacemiT K3 security hardware roadmap

## Principle

Beryllium is primarily a RISC-V security research hypervisor. Every relevant platform security feature must be inventoried and assigned an explicit use, deferral, verification, or unsupported status.

Using every feature in the minimal core is not the goal. The goal is to use hardware when it strengthens a stated property without obscuring the reference monitor or inflating the TCB.

## The R8 boundary (history)

**Status, 2026-11.** This section is history. R8's stages H1 to H4 were
dropped on 2026-10-08 and never run. The B-series bring-up and the MVP
milestones M0 to M10 became the K3 path, and MVP 1.0 was published on
2026-11-08. What the section says about blocked pushes and an undecided
development kernel describes September 2026. The ladder after MVP 1.0
is in the [MVP plan](mvp-plan.md): its Plan revision S3-D puts a
PMP-based physical boundary under the monitor first in MVP 2.0.

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
- AIA with IMSIC/APLIC and guest interrupt files. The K3's documents give the X100 harts GEILEN = 8. On one COM260 board, harts 0, 1, and 2 each have 7 guest interrupt files, by `hgeie`, and the count on harts 3 to 7 is not established ([M13's record](k3-com260-devices.md), B-02, B-69 to B-72, its Disagreement 2, and its "Not established", item 12).
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
- Nine IOPMP instances are documented, to check the accesses of the bus masters other than the harts. The manual also lists "CPU" among one instance's masters, and has source-ID fields named for the application cores; it does not say what master either is ([M13's record](k3-com260-devices.md), A-01 to A-12; for "CPU" and those fields, A-03, A-39, and A-108).
- One RISC-V IOMMU is documented for selected PCIe roots: ports A, B, and E by the datasheet and the PCIe page's overview, and ports A to C by the PCIe page's table, the bypass register, and the vendor's sources ([M13's record](k3-com260-devices.md), A-56, A-69 to A-72, and its Disagreement 1). On one COM260 board, as booted, it implements version 1.0 of its specification and is in `Off` mode, and the bypass bits of ports A to C are set, so those ports bypass it (A-151, A-152, A-160 to A-164).

Disposition:

- MVP 1.0 does not use PMP. It depends on whatever the board's firmware programs, which was never recorded: the handoff observation planned for the pathfinder and for R8 H1 did not happen.
- Use under emulation, and in diagnostic runs on one board (Plan revision S3-D, milestone M11, its candidate): a physical access profile for each of the monitor's three harts, programmed by M-mode, which bounds the monitor's own HS code as well as its guests. HS-mode code cannot program PMP: M-mode does, from the firmware's device tree, which is built offline from a partition descriptor. The firmware is a build of the project's own, OpenSBI at a pinned development commit with a patch series. It is tested in QEMU with plain PMP and with Smepmp; the claim and its required limit are `mvp/docs/claim-boundary.md`. On one COM260 board it ran with plain PMP in the second sitting of the M11 plan's board addendum (2026-11-22), booted from a microSD card under a build of that firmware: M-mode's printed records show the monitor's three harts confined, and, for two hostile-monitor images, the counts that they declare. That is diagnostic evidence from one board, with what M-mode prints as its only witness. It is not hardware validation, and Smepmp has not run there.
- The X100's entry count is documented. On one COM260 board, the banner of the project's firmware build reports sixteen entries, a grain of 4 KiB, and 38 address bits for its boot hart (the board addendum's sittings). The entries that the board's resident firmware uses or locks, and Smepmp's state after its handoff, are not established.
- IOMMU and IOPMP are not PoC requirements because the PoC has no DMA.
- K3 bring-up must inventory firmware ownership, register access, source IDs, locked regions, and default-deny behavior. [M13's record](k3-com260-devices.md) holds part of that inventory, as diagnostic facts from the vendor's documents and sources and from one COM260 board: it is not hardware validation, and it does not say that any device's memory accesses on that board are confined. For the IOPMPs: their source IDs, and the Secure Configuration unit's fields that set some of them (A-14 to A-19, A-36 to A-55); their lock bits, and the default addresses that cannot be written once an instance is enabled (A-22, A-23); by the manual, after a power-on reset an IOPMP passes every access unchecked, and once enabled it checks every access until the next reset (A-20, A-21); and the firmware's tree, the vendor's kernel tree, and the tree that the board's Linux received have no node for one, and none of the sources read writes one (A-32, A-33). For the IOMMU: the vendor's kernel tree describes it, with device IDs for ports A to C, and leaves it disabled (A-57, A-58, A-65 to A-67); no boot stage whose source was read writes it (A-80); and on that board, as booted, it is in `Off` mode, which lets no inbound memory transaction through it, while ports A to C bypass it (A-160 to A-164). Not established: each IOPMP's state as booted, whether any boot stage enables or locks one, what the vendor's "secure environment" is, and whether an application hart in M-mode or HS-mode can reach the IOPMPs' registers (the record's "Not established", items 1 and 2).
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

- Cache-block management operations. The X100 harts list `zicbom`, with 64-byte blocks, in the vendor's tree, in the firmware's, and in the tree that one COM260 board's Linux received; Linux's non-coherent DMA path cleans, invalidates, and flushes cache blocks with `Zicbom`'s instructions; and, by the monitor's source, the M11 plan, and the cache-block chapter, each of those three traps in a VS domain under M11's boundary ([M13's record](k3-com260-devices.md), A-118 to A-123).
- Non-coherent SoC DMA. The vendor's kernel tree, upstream Linux's, and the tree that one COM260 board's Linux received mark the SoC bus `dma-noncoherent`; the firmware's tree does not. The manual and the vendor's tree make the eight HDMA instances cache-coherent with the CPU ([M13's record](k3-com260-devices.md), A-103, A-104, A-116, and its Disagreement 19).
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
- Supervisor domains: the RISC-V Supervisor Domains Access Protection specification (the `Smsd` extension with its memory protection tables, `Smsdia`, and IO-MPT), v0.9.0 of 2026-08-19, not ratified. Its repository is still named `riscv-smmtt`. No upstream emulator, firmware, or reference model had merged it when read on 2026-11-10; work was in progress in each. Milestone M12 builds on that work and contributes to it (Plan revision S3-D).
- SPMP (`Sspmp`), S-mode physical memory protection. S or HS software programs it, so it cannot bound a breached monitor, which is that software. Tracked only.
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

### R8 single-hart K3 core validation (dropped 2026-10-08)

- History: stages H1 to H4 were dropped before any ran; no item below
  was executed under R8.
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

- Exact VMID width and usable AIA guest-file count. Partly answered by [M13's record](k3-com260-devices.md), for one COM260 board: KVM, in the board's own Linux, finds 14 VMID bits (B-61); harts 0, 1, and 2 each have 7 guest interrupt files, by `hgeie`, where the documents give GEILEN = 8 (B-02, B-69 to B-72; its Disagreement 2); which of harts 3 to 7 have 7 is not established (its "Not established", item 12).
- Mainline and vendor IOMMU description. Partly answered by [M13's record](k3-com260-devices.md): the vendor's kernel tree has one IOMMU node, disabled by default, and its COM260 tree leaves it disabled (A-57, A-58); upstream Linux's K3 tree, the firmware's tree, and the tree that one COM260 board's Linux received have none (A-81). On that board, as booted, the IOMMU implements version 1.0 of its specification and is in `Off` mode (A-151 to A-161). Which PCIe ports' requests it sees is not established (its Disagreement 1, and its "Not established", item 6).
- IOPMP ownership and firmware interface. Not established by [M13's record](k3-com260-devices.md). The firmware's tree, the vendor's kernel tree, and the tree that one COM260 board's Linux received have no IOPMP node; none of the sources read writes one; and the published images of the SPL, the firmware, and U-Boot hold no string `iopmp` in their uncompressed bytes (A-32 to A-34). The manual says that only the "secure world" configures them, and does not say what that is on this SoC (A-28). Each IOPMP's state as booted, and whether an application hart can reach their registers, are not established (its "Not established", items 1 and 2). M13's probes of the IOPMPs' and the Secure Configuration unit's registers, P5 and P6, were run on 2026-11-24, and their results are held, whatever they show (the [review point](mvp-m13-3-review-point.md), section 4).
- PMP/Smepmp lock state after OpenSBI handoff; the X100's PMP grain and the entries the vendor's firmware uses. These are preconditions of M11's board step.
- By the vendor's documents and upstream OpenSBI's K3 support, the K3 has other execution contexts: eight A100 harts, which lack the H extension, and RCPU cores, which run the vendor's real-time firmware from memory beside the monitor's. Whether this board runs them, what each can address, and what parks it. Partly answered. By its source, the SPL starts the two real-time cores at every boot (the [MVP plan](mvp-plan.md)'s S3-E.1, statement 4; [M13's record](k3-com260-devices.md), D-06). The record also holds what these contexts are (B-03, B-04, D-40, D-45), and what the real-time cores' address map lets them address (D-41, D-42); which IOPMP checks the real-time cores and their side's DMA engines is not established (D-43, A-109). One COM260 board's Linux uses harts 0 to 7 alone, and what runs on the A100 harts on that board is not established (D-46, D-70). What parks a context is not in the record; for the harts that the monitor does not use, the required limit of `mvp/docs/claim-boundary.md` says what M11's runs on one board showed.
- Which firmware image and which device tree the boot chain hands to OpenSBI, and from where. Answered before M13, for a boot from the NOR, by Plan revision S3-E of the [MVP plan](mvp-plan.md) (S3-E.1, statements 1 and 2): the vendor's published `fw_dynamic.itb`, and the tree in U-Boot's image that the board's identity EEPROM names, `k3_com260_ifx`. [M13's record](k3-com260-devices.md) adds that, on one COM260 board, the firmware reports itself as OpenSBI 1.6, the version of the vendor's source (B-66, B-67), and that the tree that the board's Linux holds is the distribution's file for that board, with U-Boot's additions (D-51 to D-56). How U-Boot chooses that file is not established (its "Not established", item 17).
- Secure-boot key provisioning and lifecycle state.
- Debug-lockdown behavior. Not established. [M13's record](k3-com260-devices.md) holds what the manual says: JTAG can be routed to the X100 and A100 harts or to the RCPU (D-47); in one eFuse lifecycle state, "RMA", JTAG debug is forced on (D-50); the debug module's "sysbus" mode reaches on-chip resources past the CPU (D-48); and IOPMP6 lists two masters, `DBG_AW` and `DBG_AR`, whose source-ID fields are named for the application cores' debug (D-49). One COM260 board's lifecycle state is not established, since M13 reads no eFuse (D-50; its "Not established", item 18).
- TRNG and crypto-engine software interfaces.
- RERI delegation and error routing.
- GPU virtualization programming interface and firmware trust.

Primary sources:

- https://raw.githubusercontent.com/spacemit-com/docs-chip/main/en/key_stone/k3/k3_docs/k3_ds.md
- https://github.com/spacemit-com/docs-chip/blob/main/en/key_stone/k3/k3_docs/k3_usermanual/15_security.md
- https://lore.kernel.org/linux-riscv/20260115-k3-basic-dt-v5-6-6990ac9f4308@riscstar.com/

Controlling project plan:

- [MVP plan](mvp-plan.md): Plan revisions S3-A (the board policy), S3-C (the MVP ladder), and S3-D (the physical boundary first)
- [R8 single-hart K3 core-validation plan (accepted incl. R8-A and R8-C; history)](single-hart-runtime-r8-plan.md)
