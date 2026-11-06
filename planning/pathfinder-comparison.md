<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Post-pathfinder evidence and architecture decision

## Status

This report completes the first cross-variant assessment and records the
preferred general project direction selected on 2026-07-20.

It does not define MVP 1.0, authorize a new runtime implementation, transfer
proof claims between branches, select Type Enforcement, or close the K3,
Linux-upstream, multicore, device, or motivating-use-case gates.

The selected direction is:

> Build Beryllium as a small RISC-V HS-mode isolation engine. Keep Linux, VMM,
> policy authoring, I/O, and rich services in VS domains. Begin with immutable
> ownership and explicit channels; introduce software capabilities only when
> delegation requires them, and introduce TE only when a concrete mandatory
> property justifies its independent cost.

The first concrete deliverable is
[`Beryllium Architecture Model 0.1`](architecture-model-0.1.md), not another
Helium runtime variant.

Update on 2026-07-22: responsible-human review accepted Model 0.1. The
selected successor phase was
[`Architecture Model 0.2`](architecture-model-0.2.md), which refines the
policy-neutral core mechanism boundary before protected-service selection,
policy-framework evaluation, or security-model composition.

Update on 2026-07-24: responsible-human review accepted the Model 0.2 boundary
and evidence. Later that day, responsible-human direction selected a bounded
single-hart runtime-planning phase. Responsible-human review accepted its
exact plan and separately authorized the fixed implementation profile on
2026-07-25. Protected services, policy evaluation, and security-model
composition remain unauthorized.

## Evidence discipline

The comparison uses each branch only for claims established by that exact
source, configuration, and retained evidence. In particular:

- abstract proof and C-verifier results from the original variant do not apply
  to the minimal or TE implementations;
- exact linked-byte proofs apply only to the exact-proof branch;
- the TE branch supplies review-and-test evidence, not formal verification;
- QEMU results do not establish K3 or other hardware behavior; and
- line counts and image sizes measure review surface, not security.

The cited implementation checkpoints predate the Helium 0.5.0 rename and
retain the former Beryllium identity internally. The private branch refs are
renamed to `helium/*`, but the commits are not rewritten; exact hashes remain
the claim boundary.

Selected target SLOC means target C, assembly, public headers, and linker
script, excluding tests, documentation, host tools, and proof code. The
dual-architecture Arm-only count below is an exact line count at `2c0bf53`
over its Arm target C, assembly, headers, and linker script; it excludes the
shared core and TF-A.

## Cross-variant matrix

| Variant | Fixed application and mechanism | Size | Strongest evidence | Primary lesson and limit |
| --- | --- | ---: | --- | --- |
| Original proof-oriented RISC-V, `819251e` | One VS subject; one Sv39x4 root; assigned, denied, revoked reads | 1,983 SLOC; 12 KiB | Repeated GCC/Clang QEMU; abstract Rocq ownership/H models; one sequential C-verifier pilot | The basic OpenSBI -> HS -> VS spine and staged assurance workflow are feasible. The hypervisor, assembly, compiler output, and hardware were not proved as a whole. |
| Dual architecture, `2c0bf53` | Same security scenario on RISC-V and an Arm64/TF-A reference backend | Retained RISC-V result: 1,983 SLOC, 12 KiB; 1,464 Arm-only target lines added | Repeated QEMU under both compiler families; TF-A boot; bounded Arm model | Portability is feasible but imports another firmware chain, translation format, exception path, invalidation protocol, toolchain, and evaluator surface without strengthening the lead RISC-V property. |
| Minimal RISC-V, `cc6029a` | Same single-root scenario; build-time ownership, software-capability, or capability-plus-flow policy | 1,608 / 1,637 / 1,651 SLOC; all 12 KiB | Host unit tests, repeated GCC/Clang QEMU, authority reports | Ownership is the smallest baseline. Capabilities add attenuation and derivation; mandatory flow can independently deny. This variant intentionally removed formal-verification setup. |
| Exact transition and isolation proof, `b3f2631` | Minimal runtime unchanged; exact privileged wrapper, trap frame, linked layout, and fixed access configuration | Runtime unchanged; 2,188 proof/tool lines | Rocq checks exact extracted wrapper words and bounded transition, trap, layout, isolation, and fenced revocation properties | Exact-binary connection can be added without runtime growth. The C G-stage builder and C trap handler remain explicit cut points. |
| Fixed TE, `511187f` | Two sequential typed subjects; two roots; private pages; writer-RW/reader-R shared page | 2,253 SLOC; 16 KiB | Host TE/root tests, repeated GCC/Clang QEMU, strict TE authority report | TE can independently constrain shared and private mappings. The branch has no formal setup, and its size delta includes a second subject/root and changed application, not pure TE cost. |

## Cost separation

The variants support four distinct conclusions about cost:

1. **Policy representation is not the main isolation mechanism.** All minimal
   policies use the same G-stage, trap, revoke, and fence mechanism.
2. **Ownership to capability is a small source delta but a real semantic
   commitment.** The software-capability variant adds 29 target lines over
   ownership; capability plus flow adds 43. Both introduce lineage or policy
   obligations that line count does not capture.
3. **TE cost is not isolated by the fifth experiment.** Its 602-645 line and
   4 KiB deltas combine label/rule code with a second root, second subject,
   root switch, extra fault class, and changed evidence. The TE files
   themselves total 497 lines, but that is still not a complete lifecycle or
   proof cost.
4. **Assurance can exceed runtime size.** The exact-proof variant adds 2,188
   proof/tool lines while leaving the selected runtime and 12 KiB image
   unchanged. That cost buys the strongest result in the comparison set.

The project should therefore optimize for a small stable mechanism and a
tractable proof/refinement boundary, not for the lowest source count alone.

## Security-monitor comparison

The broad review is sufficient to choose a project shape, but remains subject
to community correction and changing upstream work.

| Precedent | Publicly supported fact | Transferable lesson for Beryllium |
| --- | --- | --- |
| AWS Nitro Isolation Engine | AWS describes a small component inside the Nitro Hypervisor as the sole mediator for VM memory, CPU state, and I/O through restricted APIs, with core lifecycle hypercalls formally verified. AWS states that source and proofs are planned for later publication. | Keep the mediation layer narrow and move non-essential behavior out of its proof boundary. Do not infer a separate hardware privilege boundary or unpublished internals. |
| Linux pKVM | Current kernel documentation describes host stage-2 isolation, page donation, and explicit sharing for protected VMs, while marking the feature experimental and CPU-state and DMA isolation incomplete. | Ownership and explicit sharing are credible first mechanisms, but memory-only evidence must not be promoted to complete VM containment. |
| RISC-V Salus/CoVE direction | Salus runs in HS mode, starts a Linux host in VS mode, owns stage-2/IOMMU configuration, and exposes bounded host/guest SBI interfaces. | This is the closest RISC-V structural precedent for an HS isolation engine with an untrusted VS management environment. Reuse interface lessons where compatible rather than duplicating CoVE work. |
| seL4 and capDL | capDL declaratively describes objects and capability distribution, supports a separate loader, and generates formal-model inputs and graphs. | Define the static system state once, validate it independently, and use it for initialization, proof instantiation, and audit. An Beryllium manifest is capDL-inspired, not capDL-compatible by assertion. |
| Bao | Bao uses static resource assignment, two-stage translation, pass-through I/O, and one-to-one vCPU/pCPU mapping without a privileged Linux VM; its current repository lists RISC-V and K3 support. | Static partitioning validates the low-complexity end of the design space. Beryllium adds a VS management domain only where lifecycle or service requirements justify it. |
| Xen XSM/FLASK | XSM/FLASK can mediate domain, device, event-channel, grant, and privileged operations. Xen also documents security limits in incompletely reviewed disaggregated management interfaces. | TE is credible for VM-level mandatory policy, but it does not make a broad management interface safe and should not lead the initial core. |
| OpenHCL and VBS | OpenHCL runs rich paravisor services in VTL2, isolated from a VTL0 guest, and supports confidential-computing and device-service scenarios. | A protected service context is a plausible later direction. It requires a much larger state, transition, I/O, measurement, and lifecycle boundary than any Helium variant established. |
| CHERI and CHERIoT | CHERI distinguishes authority-bearing capabilities from identifiers and emphasizes explicit, attenuated sharing. | Keep software handles distinct from CHERI capabilities, preserve monotonic authority semantics, and treat safe sharing as a primary design problem. |

Primary sources are listed in
[`research-synthesis.md`](research-synthesis.md),
[`cheri-alignment.md`](cheri-alignment.md), and
[`isolation-engine-policy-research.md`](isolation-engine-policy-research.md).
Key current sources include:

- [AWS Nitro Isolation Engine](https://aws.amazon.com/blogs/compute/aws-nitro-isolation-engine-formally-verifying-the-hypervisor-in-the-aws-nitro-system/)
- [Linux pKVM](https://www.kernel.org/doc/html/next/virt/kvm/arm/pkvm.html)
- [Salus](https://github.com/rivosinc/salus)
- [seL4 capDL](https://docs.sel4.systems/projects/capdl/)
- [Bao](https://github.com/bao-project/bao-hypervisor)
- [Xen XSM/FLASK](https://xenbits.xenproject.org/docs/unstable/misc/xsm-flask.txt)
- [OpenHCL architecture](https://github.com/microsoft/openvmm/blob/main/Guide/src/reference/architecture/openhcl.md)
- [Identifiers are not capabilities](https://cheriot.org/cheri/philosophy/2025/01/19/capabilities-not-identifiers.html)

Sources were checked on 2026-07-20.

## Selected general project approach

### Trusted boundary

The preferred boundary is a small isolation engine in RISC-V HS mode:

```text
M mode
  firmware and measured handoff assumptions

HS mode
  Beryllium isolation engine
    trap entry and return
    domain, vCPU, frame, root, and hart identity
    explicit sharing and mapping enforcement
    later interrupt and DMA ownership

VS mode
  Linux management/VMM
  protected services
  later policy and I/O domains
```

Linux and every other VS domain are untrusted for the isolation properties
owned by HS. The core must not absorb policy authoring, device emulation,
drivers, filesystems, networking, or orchestration merely because those
services need a management interface.

### Functional and assurance sequence

1. Define, check, and accept the static single-hart architecture contract.
2. Refine the policy-neutral single-hart core mechanism boundary without
   selecting a service or security model.
3. Implement a bounded single-hart runtime only under a later approved plan.
4. Add a static multicore model only after the single-hart boundary is closed.
5. Add one serialized global control path only after immutable multicore
   isolation is established.
6. Add interrupt, IOMMU, IOPMP, device, and lifecycle obligations in separate
   stages.

This preserves per-hart fast-path state and keeps global mutation out of the
initial proof.

### Authority sequence

For the first architecture model, immutable ownership and explicit channel
rights are the selected baseline. This is not a permanent rejection of
capabilities or mandatory policy.

A software-capability layer is triggered only when a selected use case needs
runtime designation plus at least one of:

- authority transfer between independently distrusted subjects;
- monotonic attenuation;
- bounded delegation;
- holder binding across a reusable object interface; or
- revocation and generation semantics beyond static ownership.

TE is triggered only when a concrete operation should be denied despite valid
designation and capability rights because of an independently specified
source/target/class or flow constraint. The use case must show why separate
objects, channel rights, or capability attenuation are inadequate.

If both triggers fire, capability and TE remain independently observable:

```text
allow = capability_valid_and_sufficient AND mandatory_policy_allows
```

TE must not mint authority, and capability possession must not bypass TE.
Direct TE and fused "TE capabilities" are not selected.

## Decisions closed through the runtime plan

- The general shape is an HS isolation engine, not a feature-rich trusted VMM.
- Rich management and service functions belong in VS domains.
- The initial architecture instance is static and single-hart.
- Ownership and explicit channels are the Model 0.1 authority baseline.
- Capability and TE introduction require separate, falsifiable triggers.
- Arm remains conditional; RISC-V remains primary.
- The first deliverable is Model 0.1, not multicore or another PoC.
- Models 0.1 and 0.2 and the bounded single-hart runtime plan are accepted;
  implementation of the exact fixed profile is authorized, with R0 next.
- The core mechanism seam is explicit; protected-service and
  policy/security-model evaluation remain deferred until an explicit
  successor phase authorizes them.

## Decisions still open

- Acceptance of the exact R0 fixed-profile-and-layout freeze before R1.
- The protected-service use case, intentionally deferred until an explicit
  post-Model-0.2 evaluation phase.
- Permanent software-capability representation, delegation, and revocation.
- Whether any selected use case actually fires the TE trigger.
- Runtime manifest encoding and the Linux/management ABI.
- Interrupt, timer, SBI, IOMMU, IOPMP, and device boundaries.
- K3 firmware, PMP/ePMP, cache, debug, and hardware behavior.
- Static multicore details and later serialized-control refinement.
- VBS/VTL, attestation, sealed-state, and anti-rollback scope.
- CHERI backend and CHERI+H formal-model feasibility.
- Final Linux Kbuild placement versus a separate open project.
- MVP 1.0 scope and assurance claim.
