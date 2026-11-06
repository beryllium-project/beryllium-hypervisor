# Helium: RISC-V pathfinder and experimentation phase

Implementation evidence and current gate status are recorded in
[`pathfinder-evidence.md`](pathfinder-evidence.md).

## Purpose

The pathfinder sub-project is code-named **Helium** (short name **He**).

This original plan predates both the Helium 0.5.0 rename and the current
Beryllium parent-project identity. Current terminology is applied editorially;
the exact historical implementation commits are not rewritten.
It is a small, throwaway-tolerant PoC that tests the foundations before MVP
1.0 is defined.

It is not:

- MVP 1.0.
- An upstream-ready patch series.
- A completed formal verification.
- A full Linux hosting environment.
- A commitment to Type Enforcement.
- A portability demonstration beyond RISC-V.

The phase converts the largest architectural and tooling uncertainties into reproducible evidence.

## Baseline platform

- QEMU `virt` under TCG.
- RV64 with the H extension and Sv39/Sv39x4 behavior.
- OpenSBI in M-mode.
- Beryllium in HS-mode.
- A synthetic test payload in VS-mode.
- Single hart.
- Restricted GNU C plus a thin assembly entry/exit boundary.
- GCC and Clang builds.
- Fully open normative tooling.

The SpacemiT K3 X100 cluster is the first hardware follow-on, not a PoC completion requirement.

## Mandatory PoC outcomes

### P1. Hypervisor-first handoff

Demonstrate:

`OpenSBI -> Beryllium in HS-mode -> synthetic VS payload`

Required evidence:

- Beryllium retains HS privilege.
- Beryllium enters VS-mode.
- One VS-to-HS-to-VS exit round trip completes.
- Boot log, register-state trace, linked image, and disassembly are reproducible.

### P2. G-stage isolation and revocation

Demonstrate:

- A guest can access an assigned page.
- A guest access to an unassigned protected page traps.
- Beryllium fails closed on the invalid access.
- A previously assigned page can be revoked and a later guest access traps.

This is the central PoC security claim.

### P3. Minimal execution interface

Enumerate:

- Traps and exits required by the synthetic payload.
- Minimal SBI operations needed by the payload.
- Additional SBI surface required to boot Linux.

Booting Linux to a shell is a stretch outcome, not a PoC gate. If the SBI proxy or emulation surface grows beyond the small-core goal, defer it to MVP planning.

### P4. Formal-method investigation

Produce:

- A tiny Rocq ownership model.
- One machine-checked invariant: no physical frame is writable-owned by two domains.
- A Sail RISC-V H-extension to Rocq build/compatibility report.
- An explicit assumptions ledger.

If Sail's Rocq path is immature, keep Sail as an executable oracle and hand-model only the bounded ISA behavior needed by the PoC.

### P5. Restricted-C verification pilot

Select one sequential leaf module, preferably:

- The bounded manifest parser.
- A frame-ownership transition.
- A capability-table operation.

Run:

- Cerberus semantic checks.
- Frama-C open plugins.
- CBMC.
- CN as an optional pilot where the code fits its sequential model.

Record proved properties, trusted assumptions, unsupported constructs, and GCC/Clang behavior.

### P6. Policy-model comparison

Compare at the abstract-model level:

1. Minimal ownership and explicit grants.
2. Software capabilities without Type Enforcement.
3. Software capabilities plus Type Enforcement or another mandatory-flow layer.

Compare:

- Required mediation points.
- Core state and TCB size.
- Proof burden.
- Revocation and delegation.
- Information-flow expressiveness.
- CHERI alignment.
- Default usability.

No policy model is selected merely by implementing the PoC. A recommendation is an output for MVP 1.0 planning.

### P7. RISC-V/K3 mechanism map

Produce a boundary-to-hardware table for:

- G-stage translation.
- AIA and guest interrupt files.
- Sstc.
- State-enable controls.
- Counter/PMU filtering.
- PMP/ePMP/Smepmp.
- IOMMU and IOPMP.
- Cache-management instructions and non-coherent DMA.
- Secure boot/eFuse.
- Crypto engine, vector crypto, and TRNG.
- Debug and trace lockdown.
- RAS/RERI.

Each feature receives one disposition:

- Used in the PoC.
- Required for K3 bring-up.
- Candidate for MVP 1.0.
- Later research.
- Unsupported or unavailable.

## PoC success criteria

The phase succeeds only if:

1. OpenSBI-to-HS-to-VS boot and one exit round trip are reproducible.
2. Positive isolation, negative isolation, and revocation tests pass deterministically.
3. The TCB source size, image size, and exit surface are reported.
4. The Rocq frame-ownership invariant checks.
5. Sail H-extension/Rocq status is documented, including blockers.
6. One leaf C module completes the open verification pilot.
7. The policy-model comparison is delivered without prematurely selecting TE.
8. The K3 security-hardware disposition matrix is delivered.
9. The complete PoC runs from a documented open, rootless build environment.

## Explicit non-goals

- Multicore support.
- DMA or device assignment.
- IOMMU or IOPMP programming.
- General device emulation.
- Production Linux boot.
- Remote attestation.
- Cryptographic key provisioning.
- Full policy engine.
- Type Enforcement selection.
- Arm, Intel, or AMD backends.
- Performance tuning.
- Production hardening.
- Whole-core C refinement.
- Binary-correctness proof.
- Upstream-ready code.

## Redirect criteria

- If hypervisor-first handoff is infeasible on QEMU, investigate Linux-launched activation and reopen the boot-model decision.
- If G-stage negative tests do not fail closed, stop and reassess the core design.
- If the Sail-to-Rocq H path is immature, use mainline Sail only for behavior
  it supports, hand-model the minimal H behavior, and track the upstream H
  implementation without making an unmerged fork normative.
- If no open C tool can analyze the selected leaf module, use explicit placeholders and create an open-tooling side project.
- If Linux boot requires a large SBI/emulation TCB, retain the synthetic payload and defer Linux boot.
- If policy comparison does not clearly favor one model, keep the policy choice open for MVP planning.

## Evidence package

- Reproducible source and tool manifest.
- Boot and isolation test transcript.
- Short demo recording.
- Disassembly and TCB size report.
- Exit and SBI surface report.
- Rocq invariant and assumptions.
- Sail integration report.
- C-verification pilot report.
- Policy-model comparison.
- K3 security-hardware matrix.
- Updated threat-model delta.
- Two-page problem statement and one-slide architecture summary.

## Community checkpoint

Verified event targets:

- Linux Plumbers Conference: 5-7 October 2026, Prague.
- Linux Security Summit Europe: 8 October 2026, Prague.

The objective is informal feedback through a BoF, microconference subtopic if available, unconference opportunity, short-topic opportunity if available, and hallway discussions. The plan does not depend on a formal accepted talk.

Discussion topics:

- Whether a hypervisor-first separate image belongs in the Linux tree.
- Whether RISC-V-specific security opportunities justify a new project.
- Minimal HS/VS and SBI boundary.
- Capability-only versus capability+TE policy models.
- Open formal-tool and binary-validation gaps.
- K3 hardware experience and upstream support.

## MVP 1.0 planning gate

MVP 1.0 is defined only after:

- PoC evidence is reviewed.
- K3 hardware status is known.
- Policy options are compared.
- Open tooling gaps are classified.
- Community feedback is recorded.

The next planning cycle will set concrete MVP 1.0 outcomes, supported hardware, security claims, proof scope, and release criteria.
