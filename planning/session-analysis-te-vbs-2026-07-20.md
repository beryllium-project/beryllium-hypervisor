<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Transcript: TE assessment and VBS suitability

## Provenance and status

- Date: 2026-07-20
- Session: `90e28972-e41b-41ee-8432-420c6cdbaabd`
- Turn: 6
- Assistant: GitHub Copilot CLI, GPT-5.6 Sol
- Status: verbatim research input; not an approved architecture or claim

## User prompt

<!-- VERBATIM USER START -->

questions: 1) what is the SLOC for this, vs the minimal risc implementation?  2) would it be feasible to extend formal verification to the TE mechanism?  3) does this seem suitable for decomposing a hypervisor into security domains? 4) and then similarly, at the VM level, for isolation & controlled information flow / access between different VMs?  5) for implementing VBS style enclaves, with critical host/guest kernel function being isolated against kernel attacks, and protection of secrets from kernel attacks?

<!-- VERBATIM USER END -->

## Assistant output

<!-- VERBATIM ASSISTANT START -->

1. **SLOC:** using the same target-TCB definition—C, assembly, headers, and linker script, excluding tests/docs/tools:

| Variant | SLOC | Delta vs TE |
|---|---:|---:|
| Minimal ownership | 1,608 | +645 / +40.1% |
| Minimal capability | 1,637 | +616 / +37.6% |
| Minimal capability+flow | 1,651 | +602 / +36.5% |
| Fixed TE PoC | **2,253** | — |

The TE-specific header/mechanism/policy files total 497 lines. The remaining increase comes from the second root, second subject, root switching, extra fault handling, and changed payload. Binary size rises from 12,288 to 16,384 bytes (+33.3%). See `planning/type-enforcement-pathfinder-evidence.md`.

2. **Formal verification is feasible**, particularly because the model is finite, static, deterministic, allocation-free, and default-deny. A sensible progression would prove:

   1. Label initialization, one-way sealing, and malformed-input denial.
   2. Authorization iff one exact rule covers all requested permissions.
   3. Writer shared RW, reader shared R, and cross-private denial.
   4. Policy-to-PTE soundness: every installed PTE is no more permissive than TE.
   5. Directional noninterference modulo the intended writer-to-reader shared channel.
   6. Root-switch correctness, including VMID-zero `HFENCE.GVMA`.

The abstract Rocq work should be straightforward. C refinement and exact-binary connection are materially harder: the current seal is an API invariant, not hardware immutability, and the exact-proof branch currently treats significant C behavior as assumed.

3. **Hypervisor decomposition:** suitable as a mandatory policy layer, but not as the isolation mechanism itself. If components remain in one HS address space, compromised code can bypass TE or overwrite its state. Meaningful security domains require separate hardware-enforced address spaces/roots, private CPU state, controlled call gates, and fault containment.

A strong design would combine:

```text
hardware-enforced domains
+ capabilities/handles for designation and delegation
+ TE as a mandatory authority ceiling
+ a validated static manifest
```

This is especially plausible for driver, policy, cryptographic, management, and measurement service domains.

4. **VM-level isolation and controlled flow:** this is probably TE’s strongest fit. The hypervisor can mediate VM memory, shared grants, event channels, devices, interrupts, IOMMU mappings, and management operations. Xen XSM/FLASK is direct precedent.

However, TE controls authorized access and channel creation—not arbitrary information flow. A writer-RW/reader-R shared page explicitly permits writer-to-reader flow. Stronger claims require modeling all channels, declassification, devices, DMA, snapshots, migration, interrupts, and covert/timing channels, then proving noninterference modulo the permitted flow graph.

5. **VBS-style enclaves:** feasible as a future architecture, but far beyond this PoC. The current two-root switch is a useful primitive analogous to changing virtual trust contexts. To resist a compromised host or guest kernel:

- enclave/secure-service pages and register state must be owned by the monitor;
- the normal kernel must never execute with those pages mapped;
- enclave entry/exit must switch to a monitor-controlled root through a narrow gate;
- all normal-kernel input must be treated as hostile;
- communication must use explicitly mapped shared buffers with directional permissions;
- DMA/IOMMU, interrupts, debug, paging, crash dumps, migration, and multicore transitions must preserve the boundary;
- measured launch, attestation, key derivation/sealing, rollback protection, and side-channel limits must be defined.

Merely labeling functions inside the same kernel/root would **not** protect them from that kernel. The critical function and its secrets must execute in a distinct VTL-like context or protected service VM. This model is best suited to narrow services—key vaults, credential protection, code-integrity decisions, or small cryptographic operations—not arbitrary state-heavy kernel functions.

Microsoft’s [VBS enclave documentation](https://learn.microsoft.com/en-us/windows/win32/trusted-execution/vbs-enclaves) describes the analogous VTL0/VTL1 boundary.

<!-- VERBATIM ASSISTANT END -->

