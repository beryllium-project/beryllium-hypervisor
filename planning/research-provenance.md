<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Research provenance

## Tracks completed

1. Linux upstream fit and KVM/pKVM strategy.
2. Intel, AMD, Arm, and RISC-V virtualization hardware.
3. Mainstream, minimal, partitioning, and high-assurance hypervisors.
4. Language and formal-assurance options.
5. Foundational security principles, FLASK/TE, XSM, capabilities, CHERI, and integrity monitoring.
6. Conference and community trends.
7. AWS Nitro architecture.
8. Comparable cloud, DPU, driver-domain, and ultravisor systems.
9. Emerging open-source policy systems.
10. CTSRD-CHERI repositories, formal models, test infrastructure, and RISC-V CHERI alignment.
11. David Chisnall's attributed CHERI/CHERIoT writing, GitHub identity, and verified Mastodon source stream.
12. High-assurance and certification tooling, open-source licensing, community maturity, and tool-qualification practice.
13. AWS Nitro Isolation Engine primary-source verification.
14. SpacemiT K3 security hardware, secure lifecycle, IOPMP, crypto/TRNG, debug, RAS, and virtualization inventory.
15. Linux Plumbers Conference and Linux Security Summit Europe October 2026 community checkpoint research.
16. Independent review of the bounded RISC-V pathfinder PoC and its redirect criteria.
17. Post-pathfinder isolation-engine, VBS-style secure-domain, CAP+TE,
    FLASK-composition, multicore, and CHERI/software-capability synthesis.
18. Cross-variant evidence comparison and primary-source monitor review leading
    to the isolation-engine, ownership-first, and Model 0.1 planning decision.
19. Complete active-interface rename of the pathfinder to Helium 0.5.0, with
    Beryllium established as the parent project/future hypervisor and exact
    earlier evidence commits preserved without history rewriting.
20. Retirement of the former project namespace in favor of Beryllium / Be /
    `be`, including the RFC Linux layout and the clean-public-repository
    migration and internal-archive policy.
21. Curated incorporation of user-provided hypervisor architecture notes on
    Arm/RISC-V virtualization, M-mode, SBI versus OpenSBI, and VS
    control-plane decomposition, including the VS-to-HS SBI trap path and
    nested-virtualization distinction.
22. High-assurance certification regimes, assurance-case practice, formal
    technologies, and open-source qualification/correspondence gaps.
23. Safe Rust for future VS services, including `no_std`, audited safe
    privileged wrappers, unsafe perimeter, C/Rust channels, verification
    tools, and CHERI versus separate-domain isolation.
24. Optional Linux VBS-equivalent protected services and comparison with VSM,
    OpenHCL, pKVM, CoVE, and SVSM patterns, plus bounded dynamic-code,
    protected-logging, and driver-domain candidates.
25. SELinux AVC cache-corruption provenance, dynamic authority freshness, and
    what CHERI or protected VS placement can and cannot solve, grounded in
    concrete pKVM, VBS/VTL, and VMPL/SVSM isolation precedents.
26. LiteBox and current minimal RISC-V VS runtime candidates, with category and
    proof-scope distinctions.
27. The bounded single-hart runtime-planning phase, including its proposed
    OpenSBI/HS boundary, synthetic two-domain profile, absence of guest SBI,
    Model 0.2 cut-point trace, evidence plan, and implementation prohibition
    pending exact plan acceptance. Responsible-human review accepted the plan
    and separately authorized its exact fixed implementation profile on
    2026-07-25.
28. Verus and comparable Rust verification approaches for future bounded VS
    service logic, including low-level case studies, trusted tool boundaries,
    `no_std` uncertainty, and the lack of direct Verus-to-Rocq proof exchange.
29. Generic CHERI isolation among components inside one VS, including the
    linker/loader/switcher/allocator/IPC TCB and the conditions that still
    require separate G-stage VS roots.
30. TE over capability possession and lifecycle, including SELinux/Xen near
    precedents, candidate transfer/use semantics, counterexamples, proof
    obligations, and unresolved human policy intent.
31. R0 fixed-profile-and-layout freeze for the bounded single-hart runtime,
    including the pinned Fedora 44 tool/firmware lock (QEMU 10.2.2, OpenSBI
    v1.7 packaged blob pinned by SHA-256, host and cross GCC/Clang), the
    verified F/D/V-excluding QEMU command (base ISA `rv64imach`), the complete
    thirteen-resource physical/linker map with Sv39x4 pool sizing, the
    eleven-resource Model 0.2 core-projection trace, the VS/HS register matrix,
    and the HS-to-M SBI allowlist. R0 adds no privileged code; its acceptance
    was recorded on 2026-07-27. Responsible-human review accepted exact R1
    pure-C mechanism commit
    `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` on 2026-07-28. R2 is next by
    dependency and has not started; acceptance did not authorize R2.

## Quality controls

- Primary papers, official documentation, specifications, repositories, conference programs, kernel documentation, and mailing-list archives were preferred.
- Facts and inference were separated.
- Incorrect secondary attributions were corrected or excluded.
- Nitro-specific EL2 claims were rejected because no AWS primary source was found.
- A purported public NSA KIM repository was rejected because it could not be verified.
- CHERI hardware capabilities are kept distinct from Beryllium software capability handles on the non-CHERI K3 target.
- CHERI sealing and object types are kept distinct from TE policy.
- No novelty is claimed for TE over capabilities; the bounded search found
  close precedents but no general result sufficient to establish novelty.
- David Chisnall's Mastodon identity was verified through the public profile RSS; older technical threads remain incompletely indexed.
- The 2026-07-20 isolation-engine synthesis separates recorded project
  decisions from working hypotheses and implementation candidates.
- Nitro Isolation Engine claims are limited to AWS/Amazon primary disclosures;
  unpublished source, proofs, and hardware integration are not inferred.
- VBS is treated as an architectural comparison, not evidence that the
  proposed Beryllium design already provides a VTL or enclave security boundary.
- The imported hypervisor notes are design input rather than primary-source
  evidence. Their “formally verified” wording was rejected, SBI compatibility
  was separated from OpenSBI selection, and firmware/control-plane placement
  was retained as a future decision gate.
- The five 2026-07-23 sidebars remain non-authorizing research. They separate
  certification from assurance evidence, Rust memory safety from service
  correctness, VBS analogy from compatibility, AVC corruption from semantic
  freshness, and a library OS/VMM from a bootable VS runtime.
- Chompie attribution is limited to the public AVC cache-overwrite PoC. No
  separate public primary source was found for a generalized semantic-cache
  critique.
- LiteBox was inspected at commit
  `28918b641a5654b4a319a128cf9e7345ff8932b1`; its current LVBS platform is
  x86-only and it is not described as a ready RISC-V VS runtime.

## Confidence

High:

- Nitro component separation.
- pKVM as the leading in-tree precedent.
- FLASK policy/mechanism separation.
- Capability-based minimal enforcement as a strong candidate.
- Shared security invariants with architecture-specific backends.
- Incremental formal assurance.
- CTSRD-CHERI Sail semantics and CHERI architectural rules as alignment references.
- David Chisnall's recurring positions on safe-language composition, explicit authority, and compartmentalization.
- The separation of capability designation/attenuation, mandatory TE policy,
  and G-stage/IOMMU enforcement as distinct concerns.
- A small HS isolation engine, VS service domains, immutable ownership, and
  explicit channels as the least-commitment post-pathfinder baseline.

Medium:

- Best upstream form before maintainer feedback.
- Current status of rapidly changing confidential-computing and RISC-V features.
- Future kernel acceptance of each language strategy.

Incomplete:

- Social-media consensus.
- Full grassroots and offensive-security conference coverage.
- Proprietary Nitro and KIM details.
- Nitro-specific Graviton EL2 internals.
- Historical Mastodon discussions not exposed by the current public RSS window.
- A composed CHERI + RISC-V H-extension formal model and verified hypervisor implementation.
- Refinement of one abstract capability model to both protected software
  capability spaces and CHERI tagged/sealed representations.
- End-to-end VBS-style isolation against a compromised host or guest kernel.
- Multicore remote G-stage/IOMMU invalidation and frame-reuse proof.
- Open MC/DC coverage and open source-to-binary validation suitable for certification evidence.

## Artifact retention

- Curated planning material is committed on this branch.
- The user-provided `beryllium-hypervisor-notes.md` conversation export is
  incorporated in curated form as
  `planning/beryllium-hypervisor-notes.md`; the external source file is not
  a normative repository artifact.
- The five maintained `planning/sidebar-*.md` pages are curated summaries;
  larger raw research reports remain session artifacts.
- Three significant 2026-07-20 analysis exchanges are committed as verbatim
  transcript pages and indexed by
  `planning/session-analysis-transcripts-2026-07-20.md`.
- Raw large reports remain in the Copilot session artifact store.
- Future research should add evidence and mark superseded claims rather than silently replacing prior conclusions.
