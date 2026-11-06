# Initial research synthesis

## Evidence handling

This document records strong findings, design implications, representative sources, and known gaps. It is not yet a publication-quality literature review.

- Fact: supported by primary or official material.
- Inference: derived from multiple sources.
- Open: unverified or actively changing.

## Updated project focus

- RISC-V is the primary project focus.
- QEMU `virt` and SpacemiT K3 are the initial platforms.
- Arm is a conditional future portability target.
- Intel and AMD are optional long-term research targets, not initial roadmap requirements.
- The completed pathfinder comparison selects a small HS isolation engine and
  static ownership/explicit channels as the first architecture baseline.
- Software capabilities require a concrete delegation need; Type Enforcement
  requires a separate mandatory-policy property that ownership and capability
  attenuation cannot express acceptably.
- Responsible-human review accepted the static Model 0.1 contract on
  2026-07-22 and the policy-neutral Model 0.2 boundary and evidence on
  2026-07-24.
- Responsible-human review accepted the bounded single-hart runtime plan and
  separately authorized its exact fixed implementation profile on 2026-07-25.
- Responsible-human review accepted the exact R0 fixed profile and layout on
  2026-07-27 and exact R1 pure-C mechanism commit
  `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` on 2026-07-28. Subsequent
  separate decisions accepted R2 plan and implementation on 2026-07-28 and
  authorized R3 on 2026-07-29. Exact R3 implementation target
  `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` was then responsible-human
  accepted on 2026-07-29. Packet follow-up
  `fcc0f267a1f59241f872c0a1d2a371a95a58cba6` is not accepted
  implementation. The responsible human accepted exact R4 target
  `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` on 2026-07-29. Its implementation
  parent is `6e5c55c59e94bbaba136269c784db28ec1b53f54`; packet follow-up
  `ec7be2f146a851e7608e77eb2875076e66aab2e6` is decision support, not accepted
  implementation. R5, MVP 1.0, and every successor remain gated, not
  authorized, and not started; publication remains blocked.

## Linux upstream direction

Fact:

- pKVM is the strongest in-tree precedent for a small protected monitor.
- Android AVF gives pKVM a production use case.
- RISC-V pKVM was presented at KVM Forum 2025; experimental x86 trees exist.
- Jailhouse, Bao, and ACRN remain separate projects.

Inference:

- Generalizing pKVM or adding KVM privilege separation has the highest upstream credibility for a Linux-first protected monitor, but does not provide precedent for Beryllium's hypervisor-first separate image.
- A standalone monitor remains a valid research path.
- The proposal should lead with functional properties, not type-1 terminology.

Sources:

- https://www.kernel.org/doc/html/next/virt/kvm/arm/pkvm.html
- https://source.android.com/docs/core/virtualization/architecture
- https://kvm-forum.qemu.org/2025/
- https://github.com/siemens/jailhouse
- https://github.com/bao-project/bao-hypervisor
- https://github.com/projectacrn/acrn-hypervisor

## AWS Nitro

Fact:

- Nitro consists of Nitro Cards, Nitro Security Chip, and Nitro Hypervisor.
- Nitro Cards provide outward-facing control and I/O from a physically separate domain.
- Nitro Hypervisor partitions CPU/memory and assigns SR-IOV functions.
- It deliberately omits networking, filesystems, drivers, shells, and interactive access.
- Linux Nitro Enclaves documentation identifies core KVM lineage.
- AWS reports formal methods for early boot and controller message parsing.

Inference:

- Nitro's public policy/mechanism separation is physical and administrative, not a documented EL2/EL1 split.
- Software service domains plus IOMMU isolation can reproduce the security shape without proprietary hardware.

Open:

- Nitro Hypervisor internals and Nitro Card firmware.
- Graviton-specific EL2 design details.

Sources:

- https://docs.aws.amazon.com/whitepapers/latest/security-design-of-aws-nitro-system/security-design-of-aws-nitro-system.html
- https://docs.aws.amazon.com/whitepapers/latest/security-design-of-aws-nitro-system/the-components-of-the-nitro-system.html
- https://docs.kernel.org/virt/ne_overview.html
- https://www.brendangregg.com/blog/2017-11-29/aws-ec2-virtualization-2017.html

## Comparable service-domain systems

Relevant patterns:

- Google Titanium/Titan: hardware offload and root of trust.
- Azure Hyper-V, Cerberus/Pluton, and open OpenVMM/OpenHCL.
- NVIDIA BlueField, AMD Pensando, and VMware DPU infrastructure domains.
- IBM ultravisor-style protected execution.
- Oxide Propolis/Helios/Omicron/Hubris as a substantially open Nitro-like stack.
- Qubes/Xen driver domains and Xoar/Nexen disaggregation.
- seL4 component wiring and capability isolation.

Design implication:

- Define one I/O-domain contract that can be implemented by a Linux VM, dedicated service VM, DPU, firmware component, or confidential-computing service module.

Sources:

- https://github.com/microsoft/openvmm
- https://github.com/oxidecomputer/propolis
- https://github.com/oxidecomputer/hubris
- https://www.qubes-os.org/doc/architecture/
- https://www.cs.ubc.ca/~andy/papers/xoar-sosp-final.pdf
- https://ipads.se.sjtu.edu.cn/_media/publications/nexen-ndss17.pdf
- https://sel4.systems/

## Security monitor and hypervisor precedents

Key systems:

- pKVM, HypSec, SeKVM.
- CloudVisor, SecVisor, TrustVisor, XMHF/uberXMHF, BitVisor.
- Jailhouse, Bao, Xen dom0less/static partitioning.
- seL4, Muen, NOVA/Hedron, CertiKOS, Komodo.
- Xen XSM/FLASK.
- Blue Pill and SubVirt.

Sources:

- https://www.usenix.org/conference/usenixsecurity19/presentation/li-shih-wei
- https://ieeexplore.ieee.org/document/9519447
- https://doi.org/10.1145/2043556.2043571
- https://dl.acm.org/doi/10.1145/1294261.1294264
- https://doi.org/10.1109/SP.2010.17
- https://github.com/codelabs-ch/muen
- https://www.usenix.org/conference/osdi16/technical-sessions/presentation/gu
- https://www.microsoft.com/en-us/research/publication/komodo-using-verification-disentangle-secure-enclave-hardware-software/

## Security principles and policy

Foundations:

- Saltzer and Schroeder's eight principles.
- Anderson reference monitor properties.
- Rushby separation kernels.
- Noninterference and controlled intransitive flows.

FLASK lineage:

- FLASK separates decisions from enforcement.
- SELinux applies FLASK/TE through LSM.
- XSM/FLASK applies the model to Xen domains, grants, events, devices, and hypercalls.

Capability lineage:

- seL4 makes policy the capability graph.
- Capsicum demonstrates incremental capability restriction.
- CHERI offers hardware capability ideas for intra-core memory safety and compartmentalization.

Sources:

- http://web.mit.edu/Saltzer/www/publications/protection/
- https://www.usenix.org/legacy/events/sec99/full_papers/spencer/spencer.pdf
- https://docs.huihoo.com/xen/xsm-summit-041707_Coker.pdf
- https://www.cl.cam.ac.uk/research/security/capsicum/papers/2010usenix-capsicum.pdf
- https://www.cl.cam.ac.uk/research/security/ctsrd/

## Open-source policy systems

Cedar:

- Rust production engine, Lean formalization, differential randomized testing, deterministic total evaluation, schema validation, and SMT analysis.
- Useful as a development and language-design model.
- Too large and application-oriented to run inside the trusted core.

Other lessons:

- OPA/Rego provides policy-as-code patterns but not an EL2 runtime candidate.
- eBPF LSM demonstrates load-time validation but brings a large verifier.
- Landlock demonstrates monotonic restriction and versioned ABIs.
- Keylime and IMA demonstrate measured policy/configuration and remote verification.

Sources:

- https://github.com/cedar-policy/cedar
- https://github.com/cedar-policy/cedar-spec
- https://arxiv.org/abs/2403.04651
- https://arxiv.org/abs/2407.01688
- https://github.com/open-policy-agent/opa
- https://docs.kernel.org/bpf/lsm.html
- https://docs.kernel.org/userspace-api/landlock.html
- https://keylime.dev/

## Architecture substrate

Common shape:

- Privileged guest exits.
- Second-stage translation.
- Virtual interrupts and timers.
- IOMMU-backed DMA isolation.
- Protected or confidential VM modes.

Architecture-specific backends:

- Intel VMX/EPT/APICv/VT-d/TDX.
- AMD SVM/NPT/AVIC/AMD-Vi/SEV-SNP.
- Arm EL2/VHE/nVHE/GIC/SMMUv3/RME/CCA.
- RISC-V H/AIA/IOMMU/CoVE.

Sources:

- https://docs.kernel.org/virt/kvm/x86/intel-tdx.html
- https://docs.kernel.org/arch/arm64/arm-cca.html
- https://docs.riscv.org/reference/isa/v20260120/priv/hypervisor.html
- https://github.com/riscv-non-isa/riscv-sbi-doc/blob/master/src/binary-encoding.adoc
- https://github.com/riscv-software-src/opensbi/blob/master/docs/library_usage.md
- https://lpc.events/event/18/contributions/1865/
- https://github.com/riscv-non-isa/riscv-ap-tee
- https://github.com/rivosinc/salus

### Selected RISC-V lead target

The SpacemiT K3 X100 cluster is suitable as the first planned hardware target:

- Official K3 datasheet V1.5, dated 2026-07-01, states RVH 1.0, GEILEN = 8, AIA, IOMMU, Sv39, PMP/ePMP/IOPMP, and Smepmp support.
- The upstream K3 device-tree series lists `h`, `smaia`, `ssaia`, `sstc`, `shgatpa`, and related hypervisor subextensions for all eight X100 cores.
- The A100 AI cores explicitly omit the H extension and are not initial hypervisor execution targets.
- The K3 uses Sv39 rather than Sv48/Sv57, making Sv39x4 and parameterized guest-physical width mandatory design constraints.
- Public IOMMU software integration is less mature than CPU and interrupt support and must be validated on the delivered board.

QEMU provides the pre-hardware environment:

- `virt` enables the H extension for the default CPU.
- `aia=aplic-imsic` provides AIA emulation.
- `riscv-iommu-pci` and the platform IOMMU model provide RISC-V IOMMU 1.0 emulation.
- The completed pathfinder chain is OpenSBI M-mode -> Helium HS-mode ->
  synthetic VS payload. A future Beryllium runtime is not required to embed or
  retain OpenSBI, but Linux-class VS domains will require an explicitly
  mediated SBI-compatible interface.

Sources:

- https://raw.githubusercontent.com/spacemit-com/docs-chip/main/en/key_stone/k3/k3_docs/k3_ds.md
- https://lore.kernel.org/linux-riscv/20260115-k3-basic-dt-v5-0-6990ac9f4308@riscstar.com/
- https://lore.kernel.org/linux-riscv/20260115-k3-basic-dt-v5-6-6990ac9f4308@riscstar.com/
- https://qemu.readthedocs.io/en/v9.2.4/system/riscv/virt.html
- https://www.qemu.org/docs/master/specs/riscv-aia.html
- https://www.qemu.org/docs/master/specs/riscv-iommu.html

Curated design input:

- [`beryllium-hypervisor-notes.md`](beryllium-hypervisor-notes.md)
  separates SBI compatibility from OpenSBI selection and records M-mode/SBI
  placement plus monolithic-versus-decomposed VS control plane as future
  bounded runtime gates. It is not primary-source evidence.

Guest-SBI placement:

- A VS-mode SBI `ecall` normally traps to HS as the
  environment-call-from-VS exception.
- HS must validate the calling domain and virtual resource request, then
  emulate it, forward a bounded operation to M-mode, invoke a mediated VS
  service, or reject it.
- Ordinary OpenSBI is an M-mode firmware implementation, not a peer VS module.
- A separate VS firmware/control service is possible only behind HS mediation;
  it adds availability and protocol state and does not acquire HS or M-mode
  authority.

## Language and assurance

Precedents:

- seL4: Isabelle/HOL.
- CertiKOS: Coq and certified abstraction layers.
- Komodo: Dafny/Boogie/Z3 and Vale.
- Muen: SPARK/Ada.
- Cedar: Lean plus differential testing.

Candidate tools:

- C: Frama-C, CBMC, KLEE, VST, RefinedC, CompCert.
- Rust: Kani, Verus, Prusti, Creusot, Aeneas, RustBelt.
- Design: TLA+/PlusCal and Alloy.
- Kernel validation: KUnit, kselftest, syzkaller, KASAN, KMSAN, UBSAN, KCSAN.

Proof-boundary lesson:

- Claims must explicitly cover or exclude DMA, IOMMU, SMP, interrupts, firmware, assembly, compiler, and hardware models.

Sources:

- https://docs.kernel.org/rust/arch-support.html
- https://docs.kernel.org/rust/general-information.html
- https://sel4.systems/Verification/
- https://plv.mpi-sws.org/refinedc/
- https://www.cprover.org/cbmc/
- https://model-checking.github.io/kani/
- https://github.com/verus-lang/verus
- https://lamport.azurewebsites.net/tla/tla.html

## CTSRD-CHERI and David Chisnall alignment

Primary findings:

- `CTSRD-CHERI/sail-cheri-riscv` provides CHERI-RISC-V Sail semantics, executable simulators, and theorem-prover artifacts.
- `riscv/sail-riscv` contains partial H scaffolding and merged exception
  causes, but complete mainline H CSRs, instructions, and two-stage
  translation are not yet available; a composed CHERI+H model is also not
  established.
- CHERI's architectural rules emphasize provenance validity, monotonic bounds/permission reduction, root capability derivation from firmware through hypervisor and OS, and intentionality.
- CHERI capabilities, H-extension stage-2 translation, and IOMMU isolation are complementary layers.
- CHERIoT's `cheriot-audit` is useful prior art for producing a linked authority graph and applying offline policy, but its current implementation uses Rego and remains alpha-level.
- The K3 is non-CHERI, so initial Beryllium capability handles are software capabilities.
- Tooling alignment should prioritize Sail, TestRIG/RVFI-DII methods, CHERI LLVM/Clang conventions, CHERIoT authority-graph audit concepts, and reproducible devcontainer-style environments.

David Chisnall's recurring public guidance:

- Safe languages and CHERI are complementary.
- Memory safety is required for meaningful higher-level and formally verified guarantees.
- Identifiers must not be confused with authority-bearing capabilities.
- Isolation is easy; safe sharing and explicit delegation are hard.
- Supply-chain components should be treated as malicious.
- Tiny privileged transition code and auditable authority graphs are central design tools.
- CHERIoT-specific microcontroller mechanisms are not automatically suitable for application-class multicore systems.

Verified source stream:

- https://github.com/davidchisnall
- https://www.cl.cam.ac.uk/~dc552/
- https://infosec.exchange/@david_chisnall
- https://infosec.exchange/@david_chisnall.rss
- https://cheriot.org/cheri/myths/2024/08/28/cheri-myths-safe-languages.html
- https://cheriot.org/cheri/philosophy/2025/01/19/capabilities-not-identifiers.html
- https://cheriot.org/philosophy/2025/02/07/i-do-not-care-about-memory-safety.html
- https://cheriot.org/rtos/publication/2025/11/21/rust-coming-to-cheriot.html
- https://github.com/CTSRD-CHERI/sail-cheri-riscv
- https://github.com/riscv/riscv-cheri
- https://github.com/CHERIoT-Platform/cheriot-audit

Selected language implication:

- The initial Beryllium trusted core is C-first to use the mature CHERI C ecosystem and established whole-system proof tooling.
- Sail remains the language-independent ISA reference.
- Rust is planned first for tooling and separate domains, with trusted-core use deferred until its CHERI and formal-verification boundaries are stronger.
- A mixed C/Rust core is not an initial goal because it adds a difficult FFI proof boundary.
- Rocq/Coq is the primary core-proof ecosystem, with Sail-generated definitions, direct Rocq work, and open C-verification candidates; Isabelle is retained for seL4/CHERI comparison and may support binary validation.

Selected upstream implication:

- The provisional primary objective is an independent Beryllium hypervisor image whose source and Kbuild integration live in the Linux kernel tree.
- This repository remains the pre-RFC prototype and proof workspace.
- Final directory placement, subsystem ownership, and shared-code policy require maintainer feedback.
- There is no in-tree precedent for the combined hypervisor-first and separate-image model; rejection triggers the separate-project plus in-tree-interface fallback.

Selected C boundary:

- Use restricted GNU C across the hypervisor so GCC, Clang, Kbuild, and CHERI Clang remain viable.
- Define a smaller proof-bearing mechanism subset for capability/TE, ownership, mapping, lifecycle, policy-generation, and measurement logic.
- Keep privileged instructions, reset/trap code, invalidation, interrupt/timer primitives, linker behavior, and architecture-specific compiler extensions in a thin explicit boundary.
- Use only fully open proof, analysis, and translation-validation tools.

## High-assurance and fully open tooling

Key findings:

- Certification frameworks qualify a tool's use and evidence; they do not provide one universal approved-tool list.
- Formal methods, proof assistants, static analysis, model checking, requirements traceability, structural coverage, reproducible builds, configuration management, and independent verification are normal high-assurance evidence categories.
- Open-source tools can support certification when the project provides operational requirements, validation tests, known limitations, version control, reproducibility, and change-impact evidence.
- Proof-producing tools can reduce trust and qualification scope when a small open checker independently validates results.
- Proprietary tools dominate many certified programs because vendors sell qualification kits, but Beryllium will create open qualification evidence instead.
- CompCert is not fully open source: its full compiler uses a non-commercial license and is excluded.
- The VST opam distribution is BSD-licensed, but verifying the project's own C with VST needs `clightgen`, whose passes depend on CompCert files outside the open licence, so VST is not a route for Beryllium's C (`mvp/README.md` item 103; corrected 2026-11-02 under the M8 plan's Q13); non-free CompCert subtrees must not be used.
- Cerberus/CN is BSD-licensed and directly relevant to pKVM, but its community is too narrow for immediate load-bearing status.
- Frama-C open plugins, CBMC, Rocq, Isabelle, Sail, TLA+, GCC, Clang, QEMU, OpenSBI, Linux static-analysis tools, and open fuzzing/provenance tools form the strongest current baseline.
- Open MC/DC coverage and source-to-binary validation remain gaps requiring focused work.

Selected blocker policy:

- Align first with open Cambridge/REMS/seL4 tooling.
- Use explicit placeholders and withhold blocked claims while an open replacement is developed.
- Permit proprietary tooling only as a temporary exploratory last resort that triggers project-direction reassessment.
- Never use proprietary output as normative release or certification evidence.
- Trust pinned GCC/Clang initially and require fully open binary correspondence by the assurance-release milestone.

Selected proof repository model:

- Keep contracts, conformance tests, proof manifests, and exact proof references in the Linux tree.
- Keep the full Rocq/Sail proof development and tool qualification artifacts in an open companion repository keyed to exact Linux commits.
- Pair releases and automatically invalidate stale proof claims.

Selected Linux RFC layout:

- Common hypervisor core under `virt/be/`.
- Architecture backends under `arch/<arch>/be/`.
- Linux management/service-domain drivers under `drivers/virt/be/`.
- Narrow shared UAPI under `include/uapi/linux/be.h`.
- Documentation and selftests in normal Linux locations.
- Kbuild links a separate hypervisor image with a distinct object graph from Linux `vmlinux`.

Selected system-description split:

- Use Device Tree as an offline hardware-description input, not as a general in-core parser format.
- Use a separate capDL-inspired source and canonical manifest for domains, resource assignment, selected authorization constraints, channels, and measurements.
- Generate a normalized platform descriptor, Rocq configuration, authority graph, audit report, and measurement inputs from the same typed IR.
- Treat the compiler as untrusted and validate the complete manifest in Beryllium before atomic activation.

Selected Cerberus/CN role:

- Cerberus is the C semantic reference, including pointer provenance, undefined behavior, and CHERI/Morello memory-model work.
- CN is a scoped pilot for sequential ownership-heavy modules.
- CN verified a substantial pKVM buddy allocator, but it is not currently a whole-hypervisor, concurrency, CHERI-C/purecap, or independently certified proof path.
- CN promotion depends on its Rocq proof-log maturity, independent checking, broader maintenance, and concurrency support.

Selected assurance posture:

- Follow seL4's profile-neutral model rather than treating the core as intrinsically Common Criteria, DO-178C, or ISO 26262 certified.
- Produce reusable proofs, explicit assumptions, verified/validated configuration evidence, and binary correspondence.
- Build deployment-specific crosswalks and certification cases around the reusable core evidence.
- Distinguish proof strength from an issued product certificate.

Nitro update:

- The new Nitro Isolation Engine is a Rust separation kernel within the broader Nitro Hypervisor.
- AWS verifies core VM-lifecycle hypercalls with Isabelle/HOL, a restricted `muRust`, separation logic, refinement, and noninterference.
- AutoCorrode is MIT-licensed and open; the Nitro engine source and project-specific proofs were only promised for future release in the reviewed material.
- The broader/original Nitro Hypervisor's implementation language remains publicly unspecified; KVM/C lineage is inference rather than an official language statement.

Primary sources:

- https://aws.amazon.com/blogs/compute/aws-nitro-isolation-engine-formally-verifying-the-hypervisor-in-the-aws-nitro-system/
- https://www.amazon.science/blog/ec2s-formally-verified-isolation-engine-provides-mathematical-assurance-of-virtual-machine-isolation
- https://www.amazon.science/blog/isabelle-hol-the-proof-assistant-behind-the-nitro-isolation-engine
- https://github.com/awslabs/AutoCorrode
- https://raw.githubusercontent.com/AbsInt/CompCert/master/LICENSE
- https://github.com/Frama-C/Frama-C-snapshot
- https://github.com/diffblue/cbmc
- https://github.com/rems-project/cerberus

## Pathfinder and community checkpoint

Mandatory PoC evidence:

- OpenSBI -> HS-mode Beryllium -> synthetic VS payload.
- G-stage positive, negative, and revocation tests.
- TCB and exit-surface report.
- Tiny Rocq ownership proof.
- Sail H-extension/Rocq viability report.
- Open C-verification leaf-module pilot.
- Capability-only, capability+TE, and ownership-policy comparison.
- K3 security-hardware disposition matrix.

Verified events:

- Linux Plumbers Conference, 5-7 October 2026, Prague.
- Linux Security Summit Europe, 8 October 2026, Prague.

The target is informal BoF, microconference/unconference, short-topic if available, and hallway feedback rather than a formal-release commitment.

Sources:

- https://lpc.events/event/20/
- https://events.linuxfoundation.org/linux-security-summit-europe/
- https://github.com/spacemit-com/docs-chip/blob/main/en/key_stone/k3/k3_docs/k3_usermanual/15_security.md

## Integrity monitoring and historical work

Verified public lineage:

- Copilot, USENIX Security 2004.
- JHU APL/NSA LKIM.
- Invary's public CRADA-based NSA KIM statements.
- HyperSentry, SecVisor, HyperSafe, and HookSafe.
- Blue Pill and SubVirt as adversarial motivation.

Evidence warning:

- No public `nsacyber/linux-kernel-integrity-monitor` repository was verified.
- Proprietary KIM details must be limited to public documents.

Sources:

- https://www.usenix.org/legacy/event/sec04/tech/full_papers/petroni/petroni.pdf
- https://secwww.jhuapl.edu/techdigest/Content/techdigest/pdf/V32-N02/32-02-Pendergrass-McGill.pdf
- https://www.invary.com/usecases/dod-and-ic

## Community themes

- Host deprivileging and confidential-computing TCB reduction.
- Static partitioning for mixed-criticality systems.
- Rust in privileged monitors and VMMs.
- Focused formal verification of bounded cores.
- IOMMU ownership, trusted I/O, and service-domain isolation.
- Attestation of code, configuration, and policy.
- Concern over opaque firmware and vendor roots of trust.

Representative events:

- https://kvm-forum.qemu.org/2023/
- https://kvm-forum.qemu.org/2024/
- https://kvm-forum.qemu.org/2025/
- https://lpc.events/event/17/
- https://lpc.events/event/18/contributions/1865/
- https://archive.fosdem.org/2025/schedule/track/microkernel/

## Future-planning sidebars

The 2026-07-23 sidebars preserve five non-authorizing conclusions:

- certification regimes require deployment-specific crosswalks; the reusable
  project output is an open assurance case and exact evidence ledger;
- safe Rust is plausible for future VS services through audited safe wrappers,
  but the unsafe platform perimeter, service-specific TCB, and authorization
  checks remain explicit; CHERI may compartmentalize C and Rust inside a VS
  but does not replace separate G-stage roots;
- an optional Linux VBS-equivalent profile would be a protected-service
  composition over HS mechanisms, not a new implicit privilege hierarchy;
  dynamic code publication, protected logging, and driver domains each have
  distinct integrity, freshness, DMA, reset, and availability prerequisites;
- CHERI can reduce dynamic-cache corruption, while policy freshness,
  generation, replay, and invalidation remain protocol properties; pKVM,
  VBS/VTL, and SVSM are concrete isolation precedents, not proof of a
  protected AVC design; and
- LiteBox is a valuable x86 LVBS/library-OS reference, but current RISC-V VS
  runtime evaluation should compare minimal Linux, Hermit, seL4, and a bounded
  purpose-built stub.

Detailed pages:

- [High-assurance standards and open formal tooling](sidebar-high-assurance-standards.md)
- [Rust for future VS components](sidebar-rust-vs-components.md)
- [Optional Linux VBS-equivalence](sidebar-lvbs-equivalence.md)
- [Dynamic authority caches](sidebar-dynamic-authority-caches.md)
- [LiteBox and minimal VS runtimes](sidebar-minimal-vs-runtimes.md)

## Partial runtime-plan review research

Partial responsible-human review on 2026-07-24 added three non-authorizing
research conclusions:

1. **Verus and Rust verification:** Verus is the leading practical candidate
   for a future safe, bounded VS service/protocol core. It can establish rich
   functional and state-machine properties, including selected low-level and
   concurrent data-structure invariants, but trusts its rustc/SMT/specification
   stack, exports no Rocq proof object, and does not verify assembly, MMIO,
   `ecall`, FFI, cache/fence, or hardware semantics. Kani is complementary
   bounded checking; Aeneas/Charon remains the direct Rocq extraction probe;
   RefinedRust/RustBelt is foundational unsafe-Rust research.
2. **CHERI isolation inside one VS:** CHERI can confine mutually distrusted
   components only with a capability-aware linker, loader, switcher, allocator,
   revoker, scheduler, fault path, and IPC authority graph. The VS runtime
   remains shared and trusted. Separate G-stage roots remain necessary for
   isolation from that runtime, independent boot/restart, or separate DMA and
   device ownership.
3. **TE over capabilities:** ordinary capability-and-object-TE conjunction
   remains the conservative baseline. A separate model may apply monitor-held
   TE metadata to capability receipt, possession, delegation, attenuation,
   invocation, and revocation. SELinux descriptor use and Xen FLASK
   grant/event mediation are close precedents, so no novelty claim is
   supportable without a narrower literature review and new formal result.
   Human policy semantics are required before modeling.

These conclusions do not change or authorize the selected fixed single-hart
runtime profile.

## Research gaps

1. Verify current merge and patch status for confidential-computing and RISC-V features.
2. Expand Linux Security Summit, Black Hat, DEF CON, CCC, BlueHat, TROOPERS, SSTIC, RootedCON, and Phrack coverage.
3. Perform a source-attributed Mastodon/X/social scan.
4. Validate current XSM/FLASK defaults and operational adoption.
5. Seek direct feedback from KVM/pKVM, Rust-for-Linux, IOMMU/VFIO, LSM, Bao, Jailhouse, seL4, and CoVE contributors.
6. Validate CHERI feasibility for privileged virtualization code.
7. Build a licensing matrix for code, proofs, policy tooling, firmware, and external components.
8. Create a publication-quality source ledger.
9. Validate an open RISC-V source-to-binary path and open MC/DC evidence.
10. Run only the fixed synthetic runtime work if its exact plan is accepted
    and implementation is authorized. Rust/VS, LVBS, cache-generation, Linux,
    and service bake-offs still require separate later phase decisions and
    bounded plans.
