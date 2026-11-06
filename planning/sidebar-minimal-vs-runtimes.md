<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Sidebar: LiteBox and minimal VS runtime candidates

## Status and question

This page evaluates research candidates only. It does not select the first VS
runtime or authorize runtime implementation.

The key category distinction is:

- **VS runtime/kernel:** boots as a RISC-V guest supervisor, handles traps and
  virtual memory, uses an SBI-compatible interface, and hosts one or more
  services.
- **Library OS:** provides application-facing services on a platform supplied
  below it.
- **VMM/paravisor:** manages or assists other VMs.
- **HS monitor:** occupies Beryllium's own privilege layer, not a VS guest.

Many attractive projects are in the wrong category.

## LiteBox: useful reference, not a current drop-in runtime

Microsoft describes LiteBox as a security-focused library OS with:

- "North" application/API shims;
- a `no_std` Rust core; and
- caller-provided "South" platform implementations.

The repository is active, MIT licensed, and explicitly pre-stable. It includes
Linux, Windows, OP-TEE, SEV-SNP, and LVBS-related paths.

At the inspected commit
`28918b641a5654b4a319a128cf9e7345ff8932b1`:

- `litebox_platform_lvbs` is `x86_64`-only and runs in Hyper-V VTL1 kernel
  mode;
- the syscall rewriter depends on `iced-x86`;
- the SNP runner uses AMD/x86 GHCB and VMPL mechanisms;
- the core requires a platform provider below it; and
- no RISC-V paths were present in the repository tree.

Therefore LiteBox is **not currently a RISC-V VS runtime**. It remains useful
for:

- the North/South interface pattern;
- a small Rust library-OS service surface;
- LVBS/VTL1 design comparison;
- resource accounting and sandbox API ideas; and
- possible future reuse above a new Beryllium-specific platform.

Turning it into a RISC-V VS runtime would require a new platform, startup and
trap path, SBI integration, Sv39 virtual memory, interrupts, and probably a
different syscall-interposition strategy. That is a porting project, not
configuration.

## Candidate matrix

| Candidate | Category | Current RISC-V relevance | Main value | Main concern |
| --- | --- | --- | --- | --- |
| Minimal Linux | general VS kernel | first-class RISC-V guest path | fastest management-domain bring-up and drivers | very large attack and update surface |
| seL4 | microkernel | verified RV64 configurations; not RV64 hypervisor mode | strongest existing formal evidence and components | VS boot/integration and component ecosystem cost |
| Hermit | Rust unikernel | documented `riscv64` build | one small Rust service per VS domain | RISC-V/VS maturity and no formal proof |
| Purpose-built Rust `no_std` runtime | minimal service runtime | can target exact SBI/channel contract | smallest tailored surface | creates a new kernel/runtime to maintain |
| Tock | embedded Rust kernel | RISC-V embedded support | mature safe-Rust component model | MPU/PMP and embedded assumptions do not directly fit RV64 VS |
| Unikraft | unikernel kit | RISC-V readiness must be revalidated | mature library-OS construction ideas | not presently a confirmed first choice |
| Redox | general Rust OS | experimental RISC-V work | Rust microkernel research | too broad for a minimal service |
| LiteBox | library OS | no current RISC-V platform | excellent LVBS/library-OS reference | not a bootable drop-in VS kernel |
| OpenVMM/OpenHCL | VMM/paravisor | no RISC-V | production Rust service architecture | wrong category for the runtime below a service |
| Salus | HS trusted manager | RISC-V H precedent; archived repository | SBI/CoVE and isolation lessons | wrong privilege layer and not maintained |
| Muen/Hubris/Theseus | separation/embedded/research kernels | wrong ISA or machine class | comparison evidence | not realistic K3 VS candidates |

## Shortlist by role

### First management domain: minimal Linux

Linux is the practical baseline because its RISC-V VS/SBI behavior, drivers,
filesystems, networking, and tooling already exist. The cost is a large,
hostile management environment, which Beryllium already assumes.

Use Linux to validate the HS/VS runtime boundary, not as evidence that Linux
belongs in the trusted core.

### Single-purpose Rust service: Hermit or a purpose-built stub

Hermit documents a RISC-V build and links applications with a small Rust
unikernel kernel. It is a credible bake-off candidate for one policy,
measurement, or secrets service per VS domain.

A purpose-built runtime may be smaller, but it creates responsibility for
boot, traps, memory management, timers, interrupts, panic, update, and
debugging. Start with a stub only if existing runtimes impose clearly
measured excess complexity.

### Highest-assurance service environment: seL4

seL4 has verified RISC-V configurations for C-level functional correctness,
access-control integrity/availability, and information-flow confidentiality.
The RISC-V C-level proof excludes the fast path. The official
verified-configuration page also excludes IOMMU/device translation and boot
startup, and RISC-V hypervisor mode is not part of the verified configuration.

Running seL4 as a VS guest is a separate integration hypothesis: Beryllium
would need to provide the required virtual platform and SBI behavior. The
existing proofs do not automatically transfer to that new boot environment or
configuration.

## Minimum VS platform contract

Any candidate must document:

- reset state, entry privilege, image format, and memory map;
- required SBI extensions and error behavior;
- virtual timer, interrupt, and IPI model;
- FDT or normalized platform input;
- page-table and allocator ownership;
- console/debug behavior and whether it is trusted;
- panic, crash, watchdog, and restart protocol;
- channel layout and cache-coherence assumptions;
- update and rollback behavior; and
- exact code, dependencies, licenses, and proof/test claims.

No candidate should force HS to expose a general SBI or device surface merely
for compatibility.

## Bounded bake-off

Evaluate only after a runtime phase is explicitly selected:

1. Boot one image under a surrogate RISC-V H environment without changing HS
   policy semantics.
2. Enumerate and test every required SBI call.
3. Measure compressed image, resident memory, writable state, startup time,
   and externally reachable interface.
4. Run one directional shared-channel request and one denied access.
5. Kill and restart the runtime; demonstrate deterministic recovery.
6. Inventory all unsafe Rust, assembly, C, drivers, and third-party crates.
7. State exactly which upstream proofs remain applicable to the selected
   configuration.
8. Compare maintenance and security-response activity, not only LOC.

## Current disposition

- **LiteBox:** retain as an x86 LVBS/library-OS architecture reference; do not
  select as the RISC-V runtime.
- **Minimal Linux:** baseline for management bring-up if a runtime plan is
  approved.
- **Hermit:** leading existing Rust single-service experiment candidate,
  subject to real VS boot validation.
- **seL4:** leading high-assurance component environment candidate, with
  substantial integration and proof-scope review.
- **Purpose-built Rust stub:** acceptable only as a bounded interface probe,
  not a new production runtime project.

The selected bounded single-hart runtime-planning phase uses role-neutral
synthetic VS stubs and selects no service runtime winner. A Linux, Hermit,
seL4, or purpose-built runtime bake-off remains a separate later decision and
requires its own approved plan.

## Primary references

Checked 2026-07-23:

- LiteBox repository and README:
  <https://github.com/microsoft/litebox>
- LiteBox core:
  <https://github.com/microsoft/litebox/blob/28918b641a5654b4a319a128cf9e7345ff8932b1/litebox/src/lib.rs>
- LiteBox LVBS platform:
  <https://github.com/microsoft/litebox/blob/28918b641a5654b4a319a128cf9e7345ff8932b1/litebox_platform_lvbs/src/lib.rs>
- LiteBox syscall rewriter:
  <https://github.com/microsoft/litebox/blob/28918b641a5654b4a319a128cf9e7345ff8932b1/litebox_syscall_rewriter/Cargo.toml>
- Linux:
  <https://www.kernel.org/>
- seL4 verified configurations:
  <https://docs.sel4.systems/projects/sel4/verified-configurations.html>
- seL4 proofs:
  <https://github.com/seL4/l4v>
- Hermit:
  <https://github.com/hermit-os/kernel>
- Tock:
  <https://github.com/tock/tock>
- Unikraft:
  <https://github.com/unikraft/unikraft>
- OpenVMM/OpenHCL:
  <https://github.com/microsoft/openvmm>
- Salus reference:
  <https://github.com/rivosinc/salus>
- Existing runtime-boundary notes:
  [M-mode, SBI, and VS decomposition](beryllium-hypervisor-notes.md)
