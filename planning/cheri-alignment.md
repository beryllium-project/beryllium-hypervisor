# CHERI strategic and technical alignment

## Standing requirement

All architecture, language, policy, ABI, memory, compartment, and assurance decisions for Beryllium must be evaluated for conceptual or technical alignment with:

- https://github.com/CTSRD-CHERI
- https://github.com/riscv/riscv-cheri
- https://github.com/CTSRD-CHERI/sail-cheri-riscv
- https://github.com/CHERI-Alliance/sail-riscv
- https://github.com/riscv/sail-riscv
- https://www.cl.cam.ac.uk/research/security/ctsrd/cheri/
- Adjacent CHERI-Alliance and CHERIoT-Platform work where relevant.

The SpacemiT K3 is not CHERI hardware. Initial Beryllium capabilities are software kernel-object capabilities, not hardware-tagged CHERI pointers. Alignment must not overstate equivalence.

## Source hierarchy

1. Ratified or current draft ISA specifications and formal models.
2. Primary project repositories, papers, architecture documents, and verified artifacts.
3. Attributed writing and talks by project leaders and implementers.
4. Attributed mailing-list, GitHub, Mastodon, and other social discussions as design and community signals.
5. Secondary summaries only as discovery aids.

## David Chisnall source stream

David Chisnall is treated as an authoritative source for CHERI/CHERIoT design perspective, particularly safe-language composition, compartmentalization, authority, and practical adoption. His statements remain distinct from normative specifications.

Verified sources:

- GitHub: https://github.com/davidchisnall
- Cambridge: https://www.cl.cam.ac.uk/~dc552/
- Mastodon: https://infosec.exchange/@david_chisnall
- Mastodon RSS: https://infosec.exchange/@david_chisnall.rss
- CHERIoT blog: https://cheriot.org/
- "CHERI Myths: I don't need CHERI if I have safe languages":
  https://cheriot.org/cheri/myths/2024/08/28/cheri-myths-safe-languages.html
- "Identifiers are not capabilities":
  https://cheriot.org/cheri/philosophy/2025/01/19/capabilities-not-identifiers.html
- "I don't care about memory safety":
  https://cheriot.org/philosophy/2025/02/07/i-do-not-care-about-memory-safety.html
- "Rust coming to CHERIoT!":
  https://cheriot.org/rtos/publication/2025/11/21/rust-coming-to-cheriot.html

Recurring guidance to apply:

- Safe languages and CHERI are complementary.
- Memory safety is an axiom for higher-level reasoning, not the final security goal.
- Capabilities are unforgeable authority, not identifiers.
- Isolation is easier than safe, explicit sharing.
- Most-privileged transition code should remain tiny and constrained.
- Third-party and supply-chain code should be treated as potentially malicious.
- Delegation should be explicit, attenuated, and inspectable.
- Security properties should be auditable from component interfaces and authority graphs.
- CHERIoT's microcontroller-specific mechanisms must not be copied blindly into an application-class multicore hypervisor.

## CTSRD-CHERI technical alignment

### Formal ISA and test oracle

- Use `riscv/sail-riscv` for supported base RISC-V semantics. It has modelled
  the H extension since release 0.14 (2026-09-05), and release 0.14.1
  (2026-09-16) fixed page-straddling HLV/HSV accesses; pin the release used.
  Whether it replaces or cross-checks the bounded Rocq H model is a separate
  decision.
- Reuse the TestRIG / RVFI-DII differential-testing pattern where practical.
- Track the RVY Sail model in `CHERI-Alliance/sail-riscv`, a fork of `riscv/sail-riscv` with the CHERI code under `model/cheri/` (the archived `CHERI-Alliance/sail-cheri-riscv` points there). It does not model H: it diverged from upstream on 2025-07-08, before upstream added H.
- Track `CTSRD-CHERI/sail-cheri-riscv`, the CHERI v9 overlay, and its Coq/Rocq, Isabelle, and SMT verification artifacts.
- Prefer the Coq/Rocq extraction and proof path for Beryllium; use Isabelle snapshots for comparison and selected imported properties.
- Track the official `riscv/riscv-cheri` specification and version every CHERI assumption.
- The RVY Sail model and the RISC-V H model are not yet a single composed CHERI+H oracle; this is a research gap, not an existing dependency.

### Capability vocabulary and invariants

Use CHERI concepts precisely where they apply:

- Provenance validity.
- Monotonic bounds and permission reduction.
- Root authority established at boot.
- Intentionality and confused-deputy resistance.
- Sealed entry capabilities and object types.
- Explicit load, store, execute, capability-load/store, invocation, and system-register rights.
- Atomic integrity of authority metadata.

For non-CHERI hardware, describe Beryllium objects as software capabilities or capability handles. Reserve "CHERI capability" for tagged architectural capabilities.

### Candidate hybrid capability + Type Enforcement model

One policy option to evaluate is:

- Capabilities provide designation and bounded authority.
- TE labels could provide mandatory classification and flow constraints.
- Holding a capability is necessary but not sufficient when TE applies.
- A TE denial overrides capability possession.
- A TE allow never creates authority without a valid capability.
- A hybrid design would define both the root capability graph and the mandatory label/flow envelope in measured policy.
- Runtime policy may only narrow or delegate within that immutable ceiling.
- Complete mediation checks capability validity, rights, authority ancestry, labels, operation class, and policy generation.

Illustrative authorization rule, not a selected design:

`allow = valid_capability && rights_cover_operation && authority_is_derived && te_allows_flow && policy_generation_is_current`

Formal composition targets:

- Capability unforgeability and non-amplification.
- TE confinement and information-flow properties.
- No confused-deputy authority substitution.
- Correct grant, attenuation, sealing, invocation, and revocation.
- Consistency between the capability graph, labels, stage-2 mappings, IOMMU mappings, and attestation evidence.

The pathfinder phase must compare this hybrid against capability-only and simpler ownership/grant models before MVP 1.0 selects a policy architecture.

### Relationship to virtualization

- CHERI capabilities protect in-address-space references and compartments.
- RISC-V H stage-2 translation protects guest-physical ownership between domains.
- The RISC-V IOMMU protects DMA ownership.
- None replaces the others.
- Future CHERI support must preserve tags and capability width across vCPU context, guest memory, sharing, paging, DMA, migration, and attestation.

### CHERI isolation between components in one VS

CHERI can provide component-scale isolation inside one future CHERI-enabled
VS domain. Each component would receive only bounded and permission-reduced
capabilities for its:

- code and sealed entry points;
- private globals, heap objects, and stack;
- explicitly shared objects and call arguments;
- allocator quota and delegation authority;
- MMIO, interrupt, and IPC endpoints where applicable; and
- capability-bearing imports and exports.

A compromised component cannot forge a wider tagged capability or directly
enter another component's private code or data. This is finer-grained than
ordinary process memory protection, but it is not equivalent to a separate VS
domain.

A credible one-VS design requires a capability-aware:

1. **Linker and loader:** enumerate compartments, imports, exports, sealed
   objects, static capabilities, MMIO, interrupts, and allocator authority;
   derive tagged capabilities from trusted roots; and populate only declared
   authority.
2. **Switcher and call ABI:** use sealed entry or sentry capabilities, select
   the target PCC/globals/stack, protect return state, clear non-authorized
   registers, and bound every argument capability.
3. **Allocator and revoker:** return exactly bounded allocations, enforce
   quotas and rights attenuation, and define quiescence and revocation before
   memory or component identity is reused.
4. **IPC and callback layer:** treat capability transfer as delegation, with
   explicit direction, rights, object type, lifetime, generation,
   cancellation, timeout, forwarding, and restart behavior.
5. **Scheduler, trap, and fault path:** save every capability register and
   tag-bearing context, protect trusted return stacks, contain faults without
   exposing another component's state, and specify termination or restart.

CHERIoT supplies valuable primary prior art for this shape: its build creates
import/export tables and sealed objects, its switcher mediates compartment
calls, and its allocator requires explicit authority. These mechanisms are
microcontroller-specific inputs, not an application-class Beryllium design:

- [CHERIoT architecture](https://github.com/CHERIoT-Platform/cheriot-rtos/blob/4164801d7676f887eb7879086774559f8bd2da40/docs/architecture.md)
- [CHERIoT compartments](https://cheriot.org/book/compartments.html)
- [CHERIoT allocator](https://github.com/CHERIoT-Platform/cheriot-rtos/blob/4164801d7676f887eb7879086774559f8bd2da40/docs/Allocator.md)
- [CHERIoT software capabilities](https://github.com/CHERIoT-Platform/cheriot-rtos/blob/4164801d7676f887eb7879086774559f8bd2da40/docs/SoftwareCapabilities.md)

The containment boundary remains explicit:

| Mechanism | What it isolates | What it still trusts or shares |
| --- | --- | --- |
| CHERI compartment in one VS | CPU references, entry points, and explicitly delegated in-address-space objects | VS kernel/runtime, loader, switcher, allocator, scheduler, page tables, shared IPC, and device authority |
| VS process/stage-1 mapping | guest-controlled process address spaces | the VS kernel and its page-table authority |
| Separate G-stage VS root | domain memory and saved state from a shared HS mechanism | HS, firmware/hardware assumptions, and explicitly shared channels |
| IOMMU/IOPMP domain | device DMA reachability | device firmware, reset, interrupt, and buffer protocol assumptions |

Separate VS roots remain necessary when components require isolation from a
common guest kernel/runtime, independent boot or restart, separate device/DMA
ownership, a different ABI or OS, an independently trusted scheduler, or a
boundary that remains meaningful without a CHERI compartment runtime. CHERI
may reduce the number of VS domains for a narrower threat model; it does not
remove their architectural role.

CHERI also does not establish component semantic correctness, availability,
safe shared mutable state, declassification policy, or microarchitectural
noninterference. A component holding broad capabilities can misuse that
authority without violating CHERI.

CHERI sealing, sentries, and version-specific object types are not Type
Enforcement. They constrain interpretation or invocation of a capability but
do not supply a mandatory subject-type/target-type/class decision or a
capability possession and transfer policy. The separate research hypothesis
is documented in
[Capability mechanisms and holistic security policy](capability-policy-architecture.md#separate-research-hypothesis-te-over-capability-lifecycle).

No Beryllium CHERI-VS claim is supportable until an exact application-class
CHERI-RISC-V+H platform establishes:

- capability register and tag preservation across VS traps and switches;
- tag behavior through stage-1 and G-stage mappings;
- capability-aware paging, copying, snapshots, and restart;
- DMA and IOMMU/IOPMP interaction;
- loader/switcher/allocator/IPC authority construction; and
- fault containment and revocation before resource reuse.

Current CHERI-seL4 and CheriBSD compartment work remains experimental prior
art rather than transferable assurance:

- [CHERI-Microkit](https://github.com/CHERI-Alliance/CHERI-Microkit/blob/299fb1b21a626a01a1b159b003211b059c27784e/README.md)
- [CHERI-seL4](https://github.com/CHERI-Alliance/CHERI-seL4/blob/406ad0297c2b2330a0309b7e4cf8a40bbbf442a5/README.md)
- [CheriBSD compartmentalization prototype](https://github.com/CTSRD-CHERI/cheribsd/blob/88f39900c32928d807dba245fba138808c666f34/share/man/man7/compartmentalization.7)

The selected single-hart runtime plan uses two non-CHERI VS domains and does
not authorize this work.

## Concrete alignment before CHERI hardware

- Use CHERI-style derivation and attenuation rules for software capability handles.
- Generate an auditable authority graph as a build artifact.
- Evaluate `cheriot-audit` as prior art for offline policy and authority inspection:
  https://github.com/CHERIoT-Platform/cheriot-audit
- Keep guest and hypervisor ABIs width- and metadata-extensible for future purecap contexts.
- Keep stage-2 and IOMMU interfaces independent of guest pointer representation.
- Add Sail-based instruction and trap tests to the RISC-V validation plan.
- Keep each evaluated capability, TE, or ownership policy model in an executable formal model.

## Chisnall and CHERI tooling alignment

Default strategy:

- Reuse existing tools where they fit.
- Produce compatible artifacts where direct reuse is not possible.
- Contribute missing general-purpose functionality upstream when maintainers agree.
- Build thin adapters before creating independent replacements.
- Document intentional divergence and the application-class requirement that caused it.

Priority tooling surfaces:

1. **Sail models and generated simulators**
   - Use `riscv/sail-riscv` as an executable ISA oracle.
   - Track and contribute to the RVY Sail model (`CHERI-Alliance/sail-riscv`) where CHERI+H composition becomes practical.
   - Keep Beryllium architecture tests expressible against Sail semantics.

2. **TestRIG / RVFI-DII methodology**
   - Reuse differential instruction-testing protocols and trace formats where practical.
   - Avoid inventing a private instruction-oracle framework without first evaluating the CHERI tooling.

3. **CHERI LLVM/Clang and C conventions**
   - Keep the verified C subset compatible with eventual CHERI Clang purecap/hybrid experiments.
   - Follow CHERI provenance, bounds, and intentionality guidance in pointer and object APIs.
   - Isolate code that depends on conventional integer-address assumptions.

4. **Authority-graph and policy audit**
   - Produce a linker/build report describing domains, entry points, shared objects, capabilities, labels, MMIO, interrupts, devices, and policy generations.
   - Aim for conceptual or schema-level compatibility with `cheriot-audit`.
   - Support offline signing/compliance decisions without placing Rego or another rich engine in the trusted core.
   - Align the capDL-inspired system description and generated authority graph with CHERIoT linker-report and `cheriot-audit` concepts.

5. **Reproducible development environments**
   - Follow the CHERIoT devcontainer pattern for pinned compilers, Sail models, simulators, proof tools, and tests.
   - Do not automatically adopt CHERIoT's current build system; its own documentation notes possible build-system changes.

6. **Rust+CHERI later work**
   - Track `CHERIoT-Platform/cheri-rust` for future service-domain, policy-tooling, and mixed-language compartment research.
   - Do not make the developing CHERIoT Rust target an initial core dependency.

7. **CHERIoT RTOS architecture and switcher**
   - Study the tiny privileged switcher, compartment interfaces, sealing, revocation, and failure containment.
   - Reuse principles and proof structure, not microcontroller-specific ABI, scheduler, MMU-free, or temporal-safety mechanisms without validation.

Tooling compatibility should be included in milestone acceptance criteria and community review.

## Future CHERI targets

- CHERI-RISC-V Sail and simulator target.
- CheriBSD purecap and hybrid guests.
- CHERI-seL4 / CHERI-Microkit guests, noting their current verification status separately from mainline seL4.
- CVA6-CHERI or another application-class CHERI-RISC-V FPGA platform after confirming H-extension support.
- Any published Bao-CHERI artifact after independently verifying its repository, paper, and H-extension behavior.

## Language implications

- Current mature CHERI operating-system and hypervisor work is predominantly C/C++ plus assembly, with Sail specifications.
- Rust-on-CHERI is active but remains a developing toolchain.
- Chisnall's stated direction is safe languages on CHERI, not safe languages instead of CHERI.
- A Rust-first Beryllium core can align strongly with CHERI principles, but CHERI Rust support and formal tooling must be treated as evolving.
- A mixed C/Rust core adds a cross-language authority, provenance, aliasing, and proof boundary. Use it only when a specific verified or indispensable C component justifies the cost.
- Formal ISA semantics should remain language-independent through Sail.
- Rocq/Coq is the selected primary proof ecosystem because it aligns Sail-generated definitions, direct Rocq developments, and open C-verification candidates. Isabelle remains a secondary source and may be load-bearing for a bounded binary-validation workstream.

## Watch items

- RISC-V CHERI specification and ratification status.
- CHERI+H-extension formal-model composition.
- CHERI tag behavior under stage-2 translation and DMA.
- Application-class CHERI-RISC-V cores with H extension.
- Rust+CHERI compiler upstreaming and formal-tool support.
- David Chisnall's CHERIoT posts, GitHub activity, and public Mastodon CHERI threads.
- Capability-only, capability+TE, and alternative mandatory-policy composition research.
- CHERIoT tooling interfaces, artifact schemas, build reproducibility, and opportunities for upstream contribution.
