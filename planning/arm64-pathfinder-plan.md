<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Arm64 Helium pathfinder plan

## Status

This was the implementation handoff for the functionally equivalent AArch64
Helium backend. Milestones A0-A5 are now implemented on
`historical_he/dual-arch-poc`. It does not authorize broad Arm portability work,
Linux boot, devices, interrupts, or Arm hardware claims.

The retained `2c0bf53` checkpoint predates the Helium 0.5.0 rename and uses
the historical Beryllium / `be` command. The renamed branch ref does not
rewrite that evidence commit.

The RISC-V baseline remains passing. The Arm64 reference backend now makes
Helium a two-platform PoC without selecting Arm as an MVP production target.

## Implemented profile

Validated 2026-07-18:

| Item | Implemented value |
| --- | --- |
| QEMU | 10.2.2 `virt`, `cortex-a57`, one CPU, GICv2 |
| Direct diagnostic | `secure=off,virtualization=on`, ELF at EL2h, `evidence=no` |
| Evidence firmware | TF-A v2.15.0 commit `da738d5eae93af342fdc4995dd3c05acb4c9d757` |
| Evidence boot | BL1 + FIP flash image, BL33 at `0x60000000`, EL2h |
| RAM | 1 GiB; TF-A's default BL33 address is outside the original 128 MiB candidate |
| Console/shutdown | PL011 `0x09000000`; PSCI secure GPIO; no runtime semihosting |
| Stage 2 | `VTCR_EL2=0x80023560`, 32-bit IPA, 4 KiB, L1/L2/L3, VMID 1 |
| Revocation | `DSB ISHST; TLBI VMALLS12E1IS; DSB ISH; ISB` |
| Repetition | Three GCC and three Clang runs for direct and TF-A profiles |

The implementation and evaluator commands are documented under
`pathfinder/docs/`; generated evidence is retained under
`build/pathfinder/evidence/`.

## Goal

Add an Armv8-A/AArch64 execution path with the same bounded defensive claim as
the current RISC-V path:

```text
firmware EL3 -> Helium EL2 -> synthetic payload EL1
```

The Arm path must demonstrate:

1. firmware handoff into Helium at EL2;
2. entry into a synthetic AArch64 payload at EL1;
3. one EL1 -> EL2 -> EL1 `HVC` round trip;
4. successful load from one assigned stage-2 page;
5. a stage-2 translation fault for one unassigned page;
6. successful load from one initially assigned revocable page;
7. exact leaf removal followed by architecturally correct TLB maintenance;
8. a later stage-2 translation fault for that revoked page; and
9. deterministic version, platform, test, and result records.

Functional equivalence means equivalent observable security behavior and
fail-closed validation. It does not require identical page-table shapes,
firmware interfaces, trap registers, or instruction sequences.

## Architecture mapping

| RISC-V Helium | Arm64 equivalent | Purpose |
| --- | --- | --- |
| OpenSBI M-mode | TF-A EL3 runtime | Firmware handoff and system-off service |
| HS-mode | EL2 | Helium monitor |
| VS-mode | EL1h | Synthetic payload |
| Sv39x4 G-stage | AArch64 stage-2 translation | IPA-to-PA ownership |
| `HGATP` | `VTTBR_EL2` + `VTCR_EL2` | Stage-2 root and format |
| VS `ECALL` cause 10 | AArch64 `HVC`, `ESR_EL2.EC=0x16` | Guest event |
| Load guest-page fault 21 | Lower-EL data abort, `EC=0x24` | Denied load |
| `STVAL` | `FAR_EL2` | Faulting guest VA |
| `HTVAL << 2` | `HPFAR_EL2` reconstruction | Faulting IPA |
| `HSTATUS.SPV` | `SPSR_EL2.M` lower-EL mode check | Trap-origin validation |
| `SEPC` / `SRET` | `ELR_EL2` / `ERET` | Guest resume |
| `HFENCE.GVMA` | `DSB` + `TLBI` + `DSB` + `ISB` | Revoke stale translations |
| SBI console/reset | PL011 MMIO + PSCI `SYSTEM_OFF` | Evidence and shutdown |

Arm EL2 and EL1 are distinct exception levels. There is no direct analogue of
RISC-V's virtualization-mode bit; exception class and saved `SPSR_EL2` provide
the origin checks.

## Evidence-bearing boot chain

### Required path

Use QEMU 10.2.2 `virt` with:

- an explicit AArch64 CPU model;
- `secure=on`;
- `virtualization=on`;
- one CPU;
- TF-A BL1/BL2/BL31 from a pinned, source-built release;
- Helium as the non-secure BL33 payload entered at EL2h; and
- flash/FIP loading rather than runtime semihosting.

TF-A's QEMU port enters BL33 at EL2 when EL2 is implemented and masks
exceptions in the saved program status. This is the closest defensible
equivalent of OpenSBI entering the current image in HS-mode.

Use PSCI `SYSTEM_OFF` through `SMC` for shutdown. The evidence configuration
must exercise TF-A's secure GPIO poweroff path, not semihosting.

### Diagnostic-only path

A QEMU-only direct ELF boot with `secure=off,virtualization=on` may be used to
bring up EL2 assembly before TF-A integration. It must be labeled:

```text
BE_PLATFORM: arch=arm64 firmware=none boot=qemu-direct-el2 evidence=no
```

It is not the parity result because it bypasses a realistic reset/firmware
chain and has no PSCI service.

## Fixed QEMU profile

The original candidate profile was:

```text
machine:       QEMU 10.2.2 virt
CPU:           explicit cortex-a57 or another tested fixed AArch64 model
security:      secure=on
virtualization: on
CPUs:          1
RAM:           128 MiB at 0x40000000
guest state:   AArch64 EL1h
EL2 stage 1:   disabled
EL1 stage 1:   disabled
interrupts:    masked
devices used:  PL011 UART only
```

The implementation probe selected Cortex-A57 and TF-A v2.15.0. The evidence
profile uses 1 GiB because the unmodified TF-A QEMU port loads BL33 at
`0x60000000`; the 128 MiB value above remains only the superseded candidate.

QEMU documents only flash base and RAM base as stable for bare-metal use.
PL011 addresses may change between machine versions. Pin QEMU/machine version
and either:

1. validate a fixed PL011 base as an explicit profile assumption; or
2. consume a tiny normalized platform constant generated from the QEMU DTB.

Do not add a general in-core FDT parser.

## Stage-2 translation design

This is new architecture-specific code; do not adapt Sv39x4 descriptors.

Recommended bounded profile:

- 4 KiB granule;
- one fixed IPA range containing code, stack, assigned, unassigned, and
  revocable pages;
- one VMID;
- normal cacheable inner-shareable memory;
- access flag set in installed leaves;
- read/write stage-2 access for data and stack;
- executable code mapping with data mappings execute-never;
- no block mappings; and
- enough fixed tables for one leaf region, allocated statically.

The implementation must explicitly derive and test:

- `VTCR_EL2.T0SZ`;
- `VTCR_EL2.SL0`;
- `VTCR_EL2.TG0`;
- `VTCR_EL2.PS`;
- table-walk shareability/cacheability;
- `VTTBR_EL2.BADDR` alignment;
- stage-2 descriptor output address;
- `S2AP`, `AF`, memory attributes, shareability, and execute-never bits; and
- the exact translation-fault level expected for an absent leaf.

Arm stage-2 format is configurable; there is no single fixed Sv39x4-like shape.
The table builder must expose the selected profile as named constants and
reject every address or mapping outside it.

## Revocation ordering

For the one-CPU, one-VMID PoC, prefer the simple global invalidation analogous
to current global `HFENCE.GVMA`:

```asm
clear expected stage-2 leaf
dsb ishst
tlbi vmalls12e1is
dsb ish
isb
```

The exact sequence must be checked against the selected Arm architecture
revision and tested toolchain before use.

Do not initially optimize to an IPA-scoped invalidation. If later selected,
the implementation must account for combined stage-1+stage-2 cached entries,
following the ordering demonstrated by Linux KVM's
`__kvm_tlb_flush_vmid_ipa()`.

## EL2 exception boundary

Arm requires a 2 KiB `VBAR_EL2` table with sixteen 128-byte slots:

```text
current EL SP0:  sync IRQ FIQ SError
current EL SPx:  sync IRQ FIQ SError
lower EL A64:    sync IRQ FIQ SError
lower EL A32:    sync IRQ FIQ SError
```

Only lower-EL AArch64 synchronous exceptions are expected. Every other vector
must enter a distinct fail-closed path; no vector may contain padding that
falls through into executable state.

The lower-EL synchronous handler must save and restore the complete integer
context required by the AAPCS64 boundary. EL1h retains `SP_EL1`; EL2h uses
`SP_EL2`, so no RISC-V-style `SSCRATCH` stack exchange is required.

Accepted exception classes:

### HVC event

- `ESR_EL2.EC == 0x16`;
- `SPSR_EL2.M` identifies AArch64 EL1h;
- `ELR_EL2` equals the exact exported payload label;
- immediate/event value matches the phase; and
- only the existing positive, revoke, completion, or explicit failure events
  are recognized.

### Stage-2 denied load

- `ESR_EL2.EC == 0x24`;
- data fault status is the expected translation-fault level;
- `WnR == 0`;
- `S1PTW == 0`;
- `FnV == 0`;
- `FAR_EL2` equals the exact expected guest VA;
- IPA reconstructed from `HPFAR_EL2` plus the FAR page offset equals the
  expected IPA;
- `ELR_EL2` equals the exact faulting load label; and
- the shared test-flow phase expects that address.

A64 instructions are fixed at four bytes, so advancing `ELR_EL2` by four is
permitted only after the exact PC checks.

## EL2/EL1 initialization

Before enabling stage 2 or entering EL1, explicitly initialize every register
whose reset value is not part of the claim. At minimum evaluate:

- `VBAR_EL2`;
- `SCTLR_EL2`;
- `HCR_EL2` (`VM=1`, `RW=1`, all unused trap/interrupt controls explicit);
- `VTCR_EL2`;
- `VTTBR_EL2`;
- `CPTR_EL2`;
- `MDCR_EL2`;
- `CNTHCTL_EL2`;
- `SCTLR_EL1`;
- `VBAR_EL1`;
- `SPSR_EL2`; and
- `ELR_EL2`.

The guest uses no EL1 vector, interrupts, timer, floating point, SIMD, SVE,
debug, or PMU. Access must either remain disabled or be explicitly harmless in
the selected profile.

## Source-layout refactor

Do not fork the whole runtime into two copies.

Recommended layout:

```text
pathfinder/
  include/be/
    types.h
    version.h
    test_flow.h
    scenario.h
  src/core/
    test_flow.c
    scenario.c
    evidence.c
  src/arch/riscv/
    entry.S trap.S guest.S platform.c stage2.c
  src/arch/arm64/
    entry.S vectors.S guest.S platform.c stage2.c
  formal/
    Ownership.v
    SecondStage.v
    BoundedH.v
    BoundedArm64.v
```

Share:

- event values;
- page-role layout semantics;
- deterministic state machine;
- banner/result/evidence schema;
- abstract stage-2 operation/result vocabulary; and
- architecture-neutral tests and C-verifier harnesses.

Keep architecture-specific:

- descriptor encodings and table shapes;
- boot/entry assembly;
- exception vectors and context frames;
- privileged register access;
- translation invalidation;
- console/shutdown;
- fault-syndrome reconstruction; and
- ISA model assumptions.

Avoid runtime function-pointer dispatch. Build one statically linked image per
architecture against a compile-time internal contract.

## Build and evaluator interface

Preserve RISC-V as the default:

```sh
./pathfinder/be build
./pathfinder/be demo
./pathfinder/be test
```

Add explicit architecture selection:

```sh
./pathfinder/be build --arch riscv64
./pathfinder/be build --arch arm64
./pathfinder/be demo --arch arm64
./pathfinder/be test --arch all
./pathfinder/be evaluate --arch all
```

Candidate output layout:

```text
build/pathfinder/riscv64/gcc/
build/pathfinder/riscv64/clang/
build/pathfinder/arm64/gcc/
build/pathfinder/arm64/clang/
```

The complete gate must run both compilers and three emulator executions for
each architecture. The rootless image must add open AArch64 cross GCC/binutils,
QEMU system AArch64, and the pinned TF-A source/build dependencies.

## Verification and evidence parity

### Reuse

`test_flow.c`, its ACSL contracts, CBMC harness, Frama-C/WP/Z3 checks, and
Cerberus execution should remain common and continue to pass unchanged after
the refactor.

### Add

- host unit tests for Arm stage-2 descriptor construction, alignment, bounds,
  duplicate mappings, HPA mismatch, corruption, and unmap;
- QEMU negative tests for exact Arm syndrome fields and post-TLBI denial;
- `BoundedArm64.v` for the EL2/EL1 round trip, descriptor permission
  abstraction, stale translation, and TLBI/barrier result;
- a shared abstract second-stage model if it genuinely reduces duplicated
  proof assumptions;
- an Arm ASL/machine-readable-spec viability report analogous to the current
  Sail H report; and
- per-architecture source/image/exit-surface metrics and hashes.

Do not claim the Arm implementation or the multi-platform hypervisor is
formally verified. The existing narrow Helium assurance statement remains.

## Documentation parity

The Arm implementation is incomplete until the standalone site contains:

- an Arm concepts page for EL3/EL2/EL1, IPA/PA, stage 2, exception syndrome,
  vector tables, barriers, TLBI, PSCI, and TF-A;
- side-by-side RISC-V/Arm architecture and execution diagrams;
- exact boot commands and pinned revisions;
- a complete Arm file/function tour;
- verification and assumption matrices per architecture;
- measured exit surfaces and TCB/image sizes; and
- explicit distinction between QEMU-only direct EL2 and evidence-bearing TF-A
  boot.

All pages must pass link checks and real Chromium desktop/mobile rendering.

## Implementation milestones

### A0. Preserve and refactor the baseline — complete

- Create architecture-neutral contracts and build dimensions.
- Move RISC-V files without changing binary behavior.
- Require byte-identical RISC-V binaries where practical; otherwise explain
  every measured difference.
- Keep all current RISC-V tests and evidence passing.

Gate: no Arm code until RISC-V parity is demonstrated after the refactor.

### A1. Diagnostic direct-EL2 bring-up — complete

- Add AArch64 cross build and linker layout.
- Verify QEMU enters at EL2h.
- Print Arm platform/build/assurance records through PL011.
- Enter and return from a trivial EL1 `HVC`.

Gate: label all output `evidence=no`; do not add isolation claims.

### A2. Bounded Arm stage 2 — complete

- Select and document the exact `VTCR_EL2` profile.
- Implement fixed static stage-2 tables.
- Map code, stack, assigned, and revocable pages.
- Demonstrate assigned and unassigned behavior.

Gate: exact `ESR_EL2`, `FAR_EL2`, `HPFAR_EL2`, `ELR_EL2`, and `SPSR_EL2`
validation passes deterministically.

### A3. Revocation — complete

- Clear the expected leaf.
- Execute the selected DSB/TLBI/DSB/ISB sequence.
- Demonstrate post-revocation translation fault.
- Add unit and bounded formal model coverage.

Gate: three GCC and three Clang QEMU runs pass with no alternate fault class.

### A4. TF-A parity boot — complete

- Pin and source-build TF-A.
- Boot BL1/BL2/BL31 from flash/FIP.
- Enter Helium as BL33 at EL2h.
- Use PSCI system-off without semihosting.

Gate: the complete evidence-bearing chain passes with runtime semihosting
disabled.

### A5. Multi-platform evaluator and documentation — complete

- Run `--arch all` in local and rootless gates.
- Retain per-architecture logs, disassembly, hashes, screenshots, sizes, and
  exit surfaces.
- Update all standalone docs/diagrams/references.

Gate: RISC-V and Arm parity evidence is reviewed; K3 and Arm hardware remain
explicitly `NOT RUN`.

## Effort estimate

Assuming one engineer familiar with Helium but learning TF-A:

| Work | Estimate |
| --- | --- |
| Common-core/build refactor with RISC-V parity | 3–5 days |
| Direct EL2 entry, vectors, HVC, console | 3–5 days |
| Stage-2 format and fault handling | 4–7 days |
| Revocation/TLBI ordering | 2–3 days |
| TF-A flash/FIP/PSCI integration | 4–7 days |
| Unit/QEMU/formal/tooling evidence parity | 4–7 days |
| Standalone docs, diagrams, rootless evaluator | 3–5 days |

Expected total: approximately **4–6 focused engineer-weeks** for reviewed,
evidence-producing QEMU parity. A diagnostic direct-EL2 demo could appear in
one to two weeks, but it is not the final parity result.

Arm hardware validation, Linux boot, interrupts, GIC, timers, SMMU, devices,
multicore support, performance, and production hardening are additional
projects.

## Redirect and stop criteria

- If the common-core refactor changes RISC-V security behavior, stop and
  restore RISC-V parity before Arm work.
- If direct EL2 boot obscures the real firmware contract, use it only for
  debugging and move immediately to TF-A.
- If TF-A QEMU shutdown still depends on semihosting, do not call the boot
  evidence-bearing; fix the secure GPIO/PSCI path.
- If the selected `VTCR_EL2` profile requires unexpected concatenation or
  table complexity, revisit the IPA width before coding around it.
- If denied loads do not produce one deterministic translation-fault class,
  stop and explain the architectural cause before broadening accepted faults.
- If a machine-readable Arm architecture model cannot support the bounded
  behavior, retain an explicit non-claiming Rocq model and open-tooling gap.
- If the multi-platform abstraction adds runtime dispatch or obscures the
  architecture proof boundary, duplicate a thin orchestration layer rather
  than weakening auditability.

## Explicit non-goals

- Linux boot.
- EL0 payloads.
- GIC or timer virtualization.
- Interrupt injection.
- SMMU or DMA.
- Devices beyond the fixed evidence UART.
- Multicore.
- Arm hardware.
- RME/CCA.
- Nested virtualization.
- A stable cross-architecture ABI.
- Performance comparison.
- Production policy.
- Whole-hypervisor formal verification.

## First new-session tasks

1. Read `.github/copilot-instructions.md`,
   `LLM_POLICY_ALIGNMENT.md`, `planning/HANDOFF.md`, this document,
   `planning/pathfinder-plan.md`, and the Helium documentation skill.
2. Create a dedicated local branch from the current private checkpoint.
3. Install/provision AArch64 GCC/binutils and QEMU in the pinned evaluator.
4. Build a minimal direct-EL2 probe that reports `CurrentEL` and exits without
   making an isolation claim.
5. Build and test TF-A QEMU flash/FIP handoff to a fixed BL33 address.
6. Record exact QEMU/TF-A revisions and commands before choosing source layout
   or `VTCR_EL2` constants.
7. Present the tested boot evidence and proposed stage-2 profile for review
   before implementing the multi-platform refactor.

## Primary references

- [Arm Architecture Reference Manual, DDI 0487](https://developer.arm.com/documentation/ddi0487/latest/)
- [QEMU 10.2.2 Arm `virt` platform](https://gitlab.com/qemu-project/qemu/-/blob/v10.2.2/docs/system/arm/virt.rst)
- [QEMU 10.2.2 Arm boot loader](https://gitlab.com/qemu-project/qemu/-/blob/v10.2.2/hw/arm/boot.c)
- [TF-A QEMU Armv8-A platform](https://trustedfirmware-a.readthedocs.io/en/latest/plat/qemu.html)
- [TF-A QEMU BL33 entry setup](https://github.com/ARM-software/arm-trusted-firmware/blob/master/plat/qemu/common/qemu_bl2_setup.c)
- [Linux arm64 KVM register definitions](https://github.com/torvalds/linux/blob/481ed5dd3ed7136f627b8ec372ba39f5b2e7d27f/arch/arm64/include/asm/kvm_arm.h)
- [Linux arm64 exception syndrome definitions](https://github.com/torvalds/linux/blob/481ed5dd3ed7136f627b8ec372ba39f5b2e7d27f/arch/arm64/include/asm/esr.h)
- [Linux KVM stage-2 TLB maintenance](https://github.com/torvalds/linux/blob/481ed5dd3ed7136f627b8ec372ba39f5b2e7d27f/arch/arm64/kvm/hyp/vhe/tlb.c)
- [Arm ASL interpreter](https://github.com/ARM-software/asl-interpreter)
