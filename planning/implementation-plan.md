# Provisional implementation and upstream plan

## Status

**Current position (2026-10-09).** The K3 bring-up sprint (section 2.15)
is the K3 path of record. B0-B7 are accepted at their exact result
commits; the latest, B7, ran two copies of an unmodified uniprocessor
upstream Linux `v7.2` guest, interleaved on hart 0 of the COM260. On
2026-10-08 the responsible human dropped the KVM0 workstream and R8
stages H1-H4, and their records stay as history (section 2.14). The
docs-only step 3 roadmap re-baseline is accepted at exact target
`ecad45d8` (2026-10-08). The B7 plan was accepted at `026974fb` on
2026-10-08, and exact B7 result commit
`7b6b846bf453bacf4c67d986f87c61fdc092e2ee` is accepted as of 2026-10-09
(instruction `accept 7b6b84, commit and push`). S1 (section 2.16) is
complete: its revised [synthesis](he-to-be-synthesis.md) was accepted on
2026-10-18 at `fd670dcd`. S2 is complete: its plan was accepted on
2026-10-19 at `5ce7827f` and [security model v1](security-model-v1.md) on
2026-10-22 at `0e3eec8b`. S3 is complete: its [MVP plan](mvp-plan.md),
revision 1, was accepted on 2026-10-23 at `93967fba` (`accept 93967fba`;
`06c35f48` superseded); the revision puts each domain on its own hart
with a dedicated control hart, and the acceptance authorizes writing M0's
bounded plan only. That [M0 plan](mvp-m0-plan.md) was accepted on
2026-10-23 at `4d129808`; M0 implementation stopped at M0-3 by stop
condition 3 (Clang's monitor text over the accepted limit) and resumed
under Plan revision M0-A.
Board results are diagnostic bring-up evidence for one board, not
hardware validation or qualification. The chronology follows.

This began as a research-backed planning draft. Five bounded Helium
pathfinder variants, their build/test/evaluator systems, and the first
cross-variant comparison are now complete.

The selected planning direction is a small RISC-V HS isolation engine with
rich services in VS domains, static ownership and explicit channels first,
and capability or TE extensions only when concrete trigger conditions are
met. The selected first deliverable is the non-runtime
`architecture-model-0.1.md`; its checker, executable model, fixtures, reports,
tests, and bounded Rocq proof are implemented under `model/` and were accepted
by responsible-human review on 2026-07-22, with incremental review continuing.

The selected successor to Model 0.1 was
[`architecture-model-0.2.md`](architecture-model-0.2.md): a non-runtime,
single-hart refinement of the policy-neutral core mechanism boundary. It
separates configuration proposals, canonical sealed HS state, and derived
enforcement before selecting a protected service, evaluating a policy
framework, or composing security models. Its implementation and bounded
evidence are complete under `model/`, documented in
[`architecture-model-0.2-evidence.md`](architecture-model-0.2-evidence.md),
and accepted by responsible-human review on 2026-07-24. No successor phase is
automatically authorized by that acceptance.

Responsible-human direction subsequently selected a bounded single-hart
runtime-planning phase. Responsible-human review accepted its exact contract
and separately authorized the fixed implementation profile on 2026-07-25.
[`single-hart-runtime-plan.md`](single-hart-runtime-plan.md) is the binding
scope. R0 fixed profile and layout added no privileged runtime code and was
accepted by responsible-human review on 2026-07-27. Responsible-human review
accepted exact R1 pure-C mechanism commit
`a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` on 2026-07-28. The R2 plan was
accepted at `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce`, implementation was
separately authorized, and responsible-human review accepted exact R2
implementation commit `6e1cb579257c5dbe3234bd484fd091629e87181b`
on 2026-07-28. Responsible-human instruction separately authorized R3 on
2026-07-29. The bounded R3 boot-and-first-entry implementation is complete and
responsible-human accepted at exact target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` on 2026-07-29. Packet follow-up
`fcc0f267a1f59241f872c0a1d2a371a95a58cba6` is not accepted implementation.
The responsible human accepted exact R4 target
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52` on 2026-07-29. Its implementation
parent is `6e5c55c59e94bbaba136269c784db28ec1b53f54`; decision-support packet
follow-up `ec7be2f146a851e7608e77eb2875076e66aab2e6` is not accepted
implementation. The responsible human accepted the bounded R5 plan at exact
commit `fecae6b62a507bdbb93d211262197a31f5422316` on 2026-07-30 and
separately authorized R5 implementation under that accepted plan. R5
implementation is exact accepted target
`165f4d001a2b59b582b397bdea79ec4826168fdb` over parent
`9312c1355a23d411e3bdafb2183be342683a8ab9`:
`./be r5-check`, `./be r4-check`, and `make check` each passed first-try
from separate fresh detached worktrees at that target, an
independent core/runtime review found no significant issue, and the
responsible human accepted that exact commit on 2026-07-30
(see [`single-hart-runtime-r5-evidence.md`](single-hart-runtime-r5-evidence.md)
and [`single-hart-runtime-r5-review-summary.md`](single-hart-runtime-r5-review-summary.md),
whose review packet commit `9bb89fe196740c5e3252bdccced6fb202df65e55` and
acceptance-record follow-up are decision support, not implementation).
R6 implementation work is authorized under the master-plan R6 row by the
recorded `proceed to implement R6 exact` and `proceed with all r6
implementation work` instructions, and the
[bounded R6 plan](single-hart-runtime-r6-plan.md) is accepted at original exact
target `609867fdad75279c0913022909efd65c4a838909` and at corrected exact
target `75269f058ae578b0a76a113d6c05c0aaceeac8ec` as of 2026-07-30, and D-15
resumed under the already-recorded implementation authorization. Narrow
[Plan revision R6-B](single-hart-runtime-r6-plan.md#plan-revision-r6-b-d-15-image-layout-and-trace-retention)
is accepted at exact target `6d6464c6c937abccd59df932006c1049fd79fac6` as of
2026-07-30 (see its
[R6-B plan revision review and acceptance record](single-hart-runtime-r6-plan-r6b-review-summary.md)),
so R6 integration and evidence work resumed with every pinned value
re-derived at the exact implementation commit; that work is now complete,
fully checked, and committed at exact implementation target
`7ba3649f03cf13b65df33020e345d361cce2993a` (parent and initial implementation
`9ed5ad7069b6067f03e1923c09937fe218240a59`), recorded in the
[R6 adversarial-image evidence](single-hart-runtime-r6-evidence.md), and
responsible-human accepted on 2026-08-05 by explicit instruction `Accept exact
commit 7ba3649f03cf13b65df33020e345d361cce2993a`, as recorded in the
[R6 review and acceptance record](single-hart-runtime-r6-review-summary.md).
R7 was separately authorized on 2026-08-05 by the responsible-human
instruction `once complete, commit and push, then commence R7`. Its
[bounded proof and evidence plan](single-hart-runtime-r7-plan.md) is accepted
at exact target `18c43596d308052cfad67edc6e2cb8f543f75600` as of
2026-08-05, and its narrow Plan revision R7-A is separately accepted at exact
target `0605028220e3795d99393156d0bfb7d6a7d631a4` as of 2026-08-05, recorded
in the
[R7-A plan revision review and acceptance record](single-hart-runtime-r7-plan-r7a-review-summary.md).
The bounded package is complete, committed, and **responsible-human accepted
at exact implementation target `9bf22913d67e9b72286813cd5f7993a9ad3857a8`** on
2026-08-05 (immediate
parent and superseded first candidate
`95639afb0ab57959a32d055f7b7f9bdb474fe762`, whole-R7 base
`3ee8a20a3ab7e3673b88a502476f39559909a12e`), after exact-target validation in
two independent fresh detached worktrees. Root integration is applied under that accepted enumeration of
exactly six authorized predecessor acceptance-pin refreshes, all re-derived at
the exact prospective content, its results are recorded in the
[R7 bounded exact-proof and evidence record](single-hart-runtime-r7-evidence.md),
and the exact-target decision is carried by the
[R7 review and acceptance record](single-hart-runtime-r7-review-summary.md).
That acceptance adds no hardware, C-refinement, or whole-system verification
evidence.

**R8 history (dropped 2026-10-08).** Responsible-human direction on
2026-08-07 authorized R8 planning and selected
the combined single-hart K3 core-validation direction. The
[`single-hart-runtime-r8-plan.md`](single-hart-runtime-r8-plan.md) is accepted
at exact target `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` on
2026-08-07. A later separate instruction authorizes implementation only for
non-privileged H0 under that exact plan. Plan revision R8-A repairs a
discovered documentation-path and pre-/post-commit identity defect and is
responsible-human accepted at exact target
`8fa9d672cfcfb81ab68d9ed9553a5af48b884932` over parent
`cb0ac2a0f818ac57f2866cb7815767145608cf58` as of 2026-08-07. The immutable
target's proposed/paused fields remain frozen pre-decision content. Acceptance
only unpauses the already authorized non-privileged H0 work after the
acceptance-record commit, whose full SHA is its required base; every candidate
identity must be freshly derived.
Plan revision R8-C is responsible-human accepted at exact target
`f47ae60266a467ca1a7704fd9a50b140e0f31bb0` over parent
`fc6795b03b5f68849fe5ef882d7e2cae77ab4e90` as of 2026-09-17. The immutable
target retains its proposed pre-decision field.

Exact bounded non-privileged H0/R8-C target
`1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` (parent
`d18b1c9c6ca8a0f2285f820ec960258620ae4b50`, tree
`7a9d80d08d0abb771d43cf76a4a297d9d668b375`) is responsible-human accepted
as of 2026-09-17. The
[H0/R8-C review and acceptance record](single-hart-runtime-r8-h0-review-summary.md)
preserves the exact decision, packet, reported exact-target validation, and
residuals. On 2026-09-24, the responsible human confirmed that existing
instruction and record as genuine; this reconciles current status and does
not create a second acceptance date.

The accepted target remains blocked and not exit-ready: 147 rows, 118
`UNKNOWN`, 80 H0-acceptance blockers, 33 H1-completion blockers, three
H2-entry blockers, `BLOCKED-NOT-READY`, and `r8_h0_exit=not-met`. COM260
read-only inventory and troubleshooting on 2026-09-24 were session-local
discovery, not retained R8 hardware evidence, and prospective tree
`8f192c530b03ea33496b95f11ea46537ac02d0b6` is uncommitted diagnostic
content only. No H0 successor was authorized, and H1-H4 were never
authorized or run before the 2026-10-08 drop.

Separately, responsible-human selection of maintenance packet Option B on
2026-09-29 authorizes preparation only of
[`single-hart-runtime-r8-active-line-maintenance-plan.md`](single-hart-runtime-r8-active-line-maintenance-plan.md).
That document defines the distinct `R8-ALM1` non-claiming active-line
operability plan. Original target `6bb3349b...` remains immutable and
unaccepted. Independent
[review](single-hart-runtime-r8-active-line-maintenance-plan-review-summary.md)
at exact packet commit `255aa176923581bf9248bfce5bc94217ff5577a8`
recommended revisions because the plan's direct-child implementation base
cannot preserve the review and a later acceptance record on the active line,
and because exact current-line `r8-check` exits silently during launcher
authentication rather than reaching the historical first whole-diff fixture.
Historical source `102f2b...` separately reproduces that fixture defect.
Plan revision `R8-ALM1-A` corrects both findings by requiring a future
exact acceptance-record/current-line base named by separate implementation
authorization and independent exit-126/exit-2 controls. Exact revised target
`95cce2f692543da67054ec2d6061eb08a4061253` is independently reviewed in the
[R8-ALM1-A review and acceptance record](single-hart-runtime-r8-active-line-maintenance-plan-r8alm1a-review-summary.md);
both findings are resolved, no significant open plan defect was found, and
acceptance as plan text only was recommended. The responsible human accepted
that exact target as plan text only on 2026-09-29 by the exact instruction
`accept`. Its immutable `proposed-not-reviewed` and `not-authorized` fields
remain frozen pre-decision content. The revision is not R8-B, is not a
revision of the accepted R8 K3 core-validation plan, and grants no
implementation authority.

Any future implementation requires a separate exact instruction naming the
full later acceptance-record/current-line base SHA, exact relation, and
complete plan inventory. Accepted target `1999ee70...`, H0 readiness, H1-H4,
K3/hardware, runtime/proof semantics, root integration, dependencies, pins,
tool locks, publication, and every successor boundary remain unchanged.
After the 2026-10-08 R8 drop, R8-ALM1-A stays accepted plan-text history;
its implementation was never authorized.

**K3 bring-up sprint and re-baseline (2026-10-06 to 2026-10-09).** On
2026-10-06 the responsible human decoupled B0 from KVM0, parked KVM0, and
started the K3 bring-up sprint: one self-contained directory per milestone
under `bringup/k3-bN/`, outside the root `Makefile`, `be`, and
`scripts/check-be.sh`. B0-B7 and the accepted-tool fixes are each
responsible-human accepted at one exact commit (section 2.15). On
2026-10-08 the responsible human dropped the KVM0 workstream with the
instruction
`we will also drop the kvm0 workstream, we can create again if needed`,
and dropped R8 stages H1-H4 by form answer `r8=drop`; both keep their
records as history. Form answer `step3=proceed` authorized step 3, a
docs-only roadmap re-baseline accepted at exact target `ecad45d8` on
2026-10-08 (instruction `accept ecad45`). The B7 plan is accepted at
`026974fb` and the B7 result at `7b6b846b` (2026-10-09, instruction
`accept 7b6b84, commit and push`); S1, S2, and S3 are planned, not
authorized (section 2.16). Development-kernel/BSP selection stays
`UNDECIDED` but no longer gates the planned sequence, because the guests
see no devices and the guest kernel is an external test input. Public
push, tag, publication, and release remain blocked.

This document does not itself authorize MVP 1.0, B7, S1-S3, multicore,
devices, a new runtime variant, policy-framework integration, or a
permanent capability/TE architecture.

The objective is to turn a broad security-research vision into:

1. Core and non-core requirements.
2. Viable Linux-upstream integration strategies.
3. An architecture and assurance decision process.
4. Independently useful milestones.
5. An early community engagement plan.

## Problem statement

Create a minimal, RISC-V-focused virtualization security monitor/hypervisor for Linux-oriented systems. Its primary purpose is to provide a trustworthy and experimentally useful substrate for security research and development while exploiting distinctive RISC-V platform mechanisms.

The trusted core should enforce isolation and resource ownership while keeping drivers, I/O stacks, orchestration, rich policy evaluation, and other non-essential functions in separate security domains or optional components. The common mechanisms should remain portable by design, but Arm is only a conditional future target and x86 is not initial scope.

The exact upstream form remains open:

- Introduce a new in-tree virtualization/security subsystem.
- Load or launch the independent monitor from Linux and then deprivilege Linux.
- Maintain the monitor as a separate project with narrowly scoped in-tree Linux interfaces.
- Provide optional KVM/pKVM compatibility or interoperability adapters where they add value.

## Provisional Linux upstream objective

The primary objective is for the Beryllium core and architecture backends to live in the Linux kernel source tree while Kbuild produces a separate bootable hypervisor image.

This objective is provisional until direct maintainer/community validation. There is no current in-tree precedent for the combined hypervisor-first boot plus separate-image build model. pKVM is precedent for a small monitor protecting domains from a compromised host, not for this boot or source-tree structure.

This does not make Linux part of the Beryllium trusted core:

- Beryllium boots first and launches Linux as an untrusted management/service domain.
- The Linux source tree is the development, review, build, test, and distribution home for both artifacts.
- Beryllium does not depend on runtime Linux kernel services.
- Shared source or headers are allowed only when they preserve the independent hypervisor boundary and do not import unnecessary Linux complexity.

Prototype and RFC strategy:

- Use this repository for the pre-RFC implementation, formal models, proofs, emulation, and experiments.
- Keep code structured for eventual Kbuild integration and Linux coding/licensing requirements.
- Publish an architecture RFC before assuming a final directory name or subsystem ownership.
- Use the selected `virt/be/` plus `arch/<arch>/be/` layout as the RFC strawman; final placement remains a maintainer decision.
- Demonstrate Kbuild producing a separate image in an integration branch before requesting broad code review.
- Maintain a reproducible mapping between prototype commits, proof artifacts, and RFC patch series.
- Avoid a long-lived private fork of Linux as the primary development model.

Fallback trigger:

- If relevant maintainers reject a separate pre-Linux image in the kernel tree after an RFC-quality prototype and discussion, make the independent monitor a separate open project and upstream only bounded Linux guest, management, service-domain, attestation, and interoperability interfaces.
- Do not distort the minimal security architecture solely to imitate KVM or pKVM internals.

Expected in-tree surfaces:

- Common Beryllium core.
- Per-architecture boot, entry, translation, interrupt, timer, and IOMMU backends.
- Kbuild/Kconfig integration for the separate image.
- Shared UAPI or protocol definitions only where Linux management/service domains need them.
- Documentation, tests, emulation targets, CI, `MAINTAINERS`, and security process.
- Optional Linux guest/management drivers and KVM interoperability adapters.

Open details:

- Exact source-tree layout and maintainers.
- Whether the separate image is built in the normal kernel build or a dedicated Kbuild target.
- Which headers or low-level helpers may be shared with Linux.
- Licensing of core code, proof artifacts, generated code, and external tooling.
- How proof-bearing restricted C and normal GCC/Clang kernel builds remain synchronized.

### Selected proof repository boundary

Use a hybrid layout modeled on seL4 and `l4v`.

In the Linux tree:

- C and assembly implementation.
- Kbuild/Kconfig integration.
- Machine-readable contracts needed by code generation or checking.
- Public protocol and configuration schemas.
- Conformance and regression tests.
- Proof-status manifest for each supported configuration.
- Hashes/identifiers for source, configuration, generated proof input, companion proof commit, tool manifest, and validated binary.
- Documentation of proved properties, assumptions, and unverified features.

In the open companion proof repository:

- Rocq abstract specification and refinement proofs.
- Sail integration and generated definitions.
- Security-property proofs.
- C verifier experiments and annotations not suitable for the kernel tree.
- Translation-validation tooling and proof artifacts.
- Tool source locks, reproducible environments, validation suites, and qualification evidence.
- Deployment assurance crosswalk templates.

Synchronization rules:

- Every proof claim names an exact Linux commit, configuration, compiler/tool manifest, and companion proof commit.
- In-tree manifests cannot claim verification when the matching companion proof CI has not passed.
- Releases pair Linux and proof-repository tags.
- Interface or proof-bearing source changes invalidate affected proof status until rechecked.
- Proof-bearing code is isolated behind a narrow stable internal interface to reduce unrelated Linux-tree churn.
- Tree-wide refactors cannot mechanically change proof-bearing code without proof-impact review.
- Proof status may temporarily downgrade to `unverified` after upstream changes; stale proofs never remain advertised as current.
- The proof repository remains fully open and reproducible without a hosted service.
- `MAINTAINERS` and security documentation identify both code and proof maintainers.

This repository initially hosts code, research, and proofs together. If the core enters Linux, it should evolve into or seed the companion proof/research repository.

### Selected Linux source-tree strawman

The first RFC proposes:

- `virt/be/`
  - Architecture-neutral mechanism core.
  - Domain/object lifecycle.
  - Ownership and explicit-channel enforcement initially; later
    authorization extensions only after their decision gates.
  - Memory ownership and grant logic.
  - Static configuration loader.
  - Measurement state.
  - Freestanding support code.
  - Kbuild rules for the separate image.

- `arch/<arch>/be/`
  - Reset and boot handoff.
  - Linker script and image layout.
  - Trap entry/return and vCPU context.
  - Stage-2 translation implementation.
  - Interrupt, timer, TLB, cache, and IOMMU primitives.
  - Architecture feature discovery and conformance tests.

- `drivers/virt/be/`
  - Linux management/service-domain driver.
  - Shared-memory, notification, lifecycle-request, and attestation transport.
  - No direct access to private Beryllium or protected-domain state.

- `include/uapi/linux/be.h`
  - Versioned Linux/userspace-visible protocol definitions.
  - Fixed-width fields, explicit endianness, reserved fields, and size/version negotiation.
  - No internal pointer, compiler layout, or architecture-private types.

- `include/linux/be.h`
  - Linux-internal adapter interfaces only; not linked into the hypervisor image.

- `Documentation/virt/be/`
  - Architecture, threat model, boot chain, UAPI, configuration, proof status, and assumptions.

- `tools/testing/selftests/be/`
  - Linux management/UAPI tests.

- `tools/be/`
  - Open userspace inspection, packaging, attestation, and development tools where needed.

Build separation:

- A dedicated Kbuild target links a Beryllium image with its own linker script and entry point.
- Linux `vmlinux` and the Beryllium image have distinct object graphs.
- No Linux scheduler, allocator, driver, filesystem, networking, or general kernel service is linked into Beryllium.
- Any shared helper must be explicitly audited for freestanding use and proof impact.
- The proof manifest records the exact Kbuild target, configuration, source set, compiler, linker, and output hash.
- Exact target names and final directory placement remain subject to maintainer review.

## Selected static system-description split

Use two distinct inputs:

1. **Device Tree**
   - Describes discoverable platform hardware, addresses, interrupts, clocks, buses, and boot topology as an offline/build-time input.
   - Is consumed by open tooling before boot to generate a bounded normalized platform descriptor.
   - Does not grant domain authority merely because a device or memory node exists.
   - Runtime overlays are not part of the baseline security model.
   - A general FDT parser is not part of the baseline Beryllium TCB.

2. **capDL-inspired Beryllium system description**
   - Defines domains and vCPUs.
   - Assigns CPUs, memory, interrupts, timers, and devices.
   - Defines immutable ownership and explicit channel rights in the baseline.
   - May carry software-capability, delegation, revocation, or mandatory-policy
     data only in a later profile whose trigger and plan are approved.
   - Defines shared-memory grants and notification channels.
   - Binds images, configuration, policy, and expected measurements.
   - Declares the trusted platform profile and architecture feature requirements.

Offline compilation pipeline:

`system source + board Device Tree/description + policy source -> typed IR -> normalized platform descriptor + canonical security manifest + Rocq configuration + authority graph + audit report + measurement inputs`

Core consumption:

- Beryllium receives a minimal fixed boot header that locates images, the normalized platform descriptor, and the security manifest.
- Beryllium parses only compact, fixed-format, versioned descriptors.
- The parser uses bounded lengths, explicit endianness, reserved fields, and no recursive or general-purpose data model.
- The manifest is signed or otherwise authenticated and included in measured boot.
- Beryllium independently validates object uniqueness, resource non-overlap, the selected authorization constraints, device/IOMMU ownership, channel endpoints, feature requirements, and policy generation.
- The compiler is not trusted to create authority that the manifest validator would reject.
- The core either activates the complete initial configuration atomically or fails closed.
- If early bring-up temporarily requires an in-core FDT parser, it is confined to the platform boundary, limited to a documented strict subset, marked unverified, and tracked for replacement.

Audit and proof:

- Generate a stable JSON authority graph for human and tool analysis, aligned where practical with CHERIoT linker reports and `cheriot-audit`.
- Generate the Rocq configuration used to instantiate integrity and noninterference theorems.
- Trace every manifest field to source, proof assumptions, and attestation measurements.
- Validate compiler determinism and, where practical, prove or differentially check source-to-manifest preservation.

The final language name, syntax, and binary encoding remain implementation decisions; the semantic split is selected.

## Selected project identity

Beryllium is an independent new hypervisor architecture. KVM, pKVM, SeKVM, and related systems are references, comparison points, and possible integration adapters, not the implementation base or the identity of the project.

Consequences:

- The core owns its own domain model, lifecycle, security interfaces, and architecture-neutral invariants.
- The design must not inherit KVM APIs or internal state models unless they independently fit the minimal core.
- Linux may act as an initial loader, management domain, service domain, or guest, but it is not inherently part of the trusted core.
- A Linux-tree proposal must justify a genuinely new subsystem or a carefully bounded loader/management interface.
- Upstream risk is higher than a pKVM extension, so maintainer engagement and an independently useful prototype must happen early.
- Optional adapters may expose KVM-compatible management, reuse suitable userspace tooling, or interoperate with protected-virtualization facilities without making them foundational.

## Selected baseline boot chain

The baseline architecture boots Beryllium before Linux:

`platform firmware -> bootloader or firmware handoff -> Beryllium -> Linux management/service domain and protected domains`

Required properties:

- Beryllium enters and retains the architecture's highest virtualization privilege before Linux executes.
- Beryllium initializes the minimum CPU, memory-translation, interrupt, timer, and IOMMU state required to establish isolation.
- The bootloader or firmware supplies the Linux kernel, initramfs, device description, initial domain configuration, and policy as measured artifacts or modules.
- Linux receives explicitly assigned CPUs, memory, interrupts, and devices and is untrusted from its first instruction.
- Linux cannot modify Beryllium, protected-domain private state, stage-2 ownership metadata, policy state, or measurements.
- Linux may request later domain creation, but Beryllium validates ownership, image/configuration authorization, and finalization independently.
- A Linux-first activation path remains optional for development, compatibility, and DRTM/late-launch research; it is not the baseline security claim.

### Staged M-mode and SBI decomposition

RISC-V requires M-mode, but Beryllium does not require OpenSBI as an
architectural component. SBI is an interface; OpenSBI is one implementation.
The completed Helium chain uses OpenSBI for bounded bring-up evidence.

A later Linux-profile runtime plan must compare:

1. OpenSBI below Beryllium HS;
2. a Beryllium-owned M-mode component; and
3. a separately maintained minimal M-mode runtime.

That later plan must separately define:

- the SBI implementation used by HS during platform boot;
- the virtualized SBI interface exposed to Linux-class VS domains;
- the HS-to-M-mode forwarding and ownership contract;
- timer, interrupt, hart, reset, and power request mediation;
- exact trusted firmware and delegation assumptions; and
- fail-closed behavior for unsupported or malicious requests.

The accepted first fixed profile uses pinned OpenSBI below HS, a bounded
HS-facing Base/Debug-Console/System-Reset allowlist, and no guest-visible SBI.
That authorization does not select the firmware or virtual-SBI boundary for a
later Linux profile. Model 0.2 contains no SBI, M-mode, interrupt, timer,
hart-lifecycle, or power operation. See
[`single-hart-runtime-plan.md`](single-hart-runtime-plan.md) and
[`beryllium-hypervisor-notes.md`](beryllium-hypervisor-notes.md).

## Threat model v0

### Trusted computing base

- Beryllium core code and the selected architecture backend.
- Minimal boot and exception-entry assembly.
- CPU virtualization, memory-translation, interrupt, timer, and IOMMU hardware used by the baseline profile.
- Processor microcode.
- Platform firmware and verified-boot chain in the baseline profile.
- Initial measured configuration and policy.

### Potential attackers

- Linux management/service domain, including kernel and userspace, from its first instruction.
- Every protected research domain.
- Every I/O, policy, or service domain added later.
- Malformed boot artifacts or management requests that fail authentication, measurement, ownership, or structural validation.

All non-Beryllium domains may be mutually hostile and may attack Beryllium.

### Protected assets and properties

- Confidentiality and integrity of each domain's private memory and private vCPU state.
- Integrity of Beryllium code, metadata, page tables, IOMMU state, capability state, policy state, and measurements.
- Isolation between every pair of domains.
- Authenticity and integrity of domain identity, configuration, policy generation, results, and attestation evidence.
- Explicit authorization and revocation for shared memory, notifications, interrupts, and devices.

### Allowed attacker effects

- Linux may pause, starve, or terminate protected work.
- A hostile domain may crash itself.
- Architectural timing differences and documented microarchitectural leakage remain possible under the initial side-channel scope.
- A service domain may withhold its service.

### Required containment

- No domain may read or modify another domain's private state.
- No domain may DMA or inject interrupts outside explicit ownership.
- No domain may forge capabilities, labels, policy generations, core-held measurements or results, or attestation evidence once attestation is enabled.
- No compromised domain may gain authority merely because it performs management or I/O work.
- All hypercalls, exits, shared queues, descriptors, and configuration artifacts are untrusted inputs.
- Shared writable memory exists only through explicit, revocable grants.
- Compromise of one non-Beryllium domain must not compromise Beryllium or another domain's confidentiality or integrity.

### Explicitly deferred or out of scope

- Host-independent availability.
- Comprehensive microarchitectural noninterference.
- Physical and invasive hardware attacks.
- Malicious fabrication or compromised vendor roots.
- Firmware-hostile launch in the baseline profile; an optional DRTM/late-launch profile is planned.

## Selected architecture sequence

1. RISC-V is the lead architecture.
2. The pathfinder PoC and MVP 1.0 planning are RISC-V-only.
3. Arm is a conditional future portability target if the RISC-V design and community feedback justify it.
4. Intel VMX and AMD SVM are optional long-term research targets, not roadmap commitments.

The first emulator target is QEMU `virt`; the first planned hardware target is the SpacemiT K3 X100 cluster.

### SpacemiT K3 target profile

Verified public properties:

- Eight X100 RV64 cores with RVH 1.0.
- Sv39 virtual memory, implying an Sv39x4 G-stage baseline rather than Sv48x4/Sv57x4.
- AIA with M/S/VS interrupt support, IMSIC/APLIC topology, and GEILEN = 8.
- Sstc and the RVA23 hypervisor subextensions listed in the upstream device tree.
- Hardware IOMMU, PMP/ePMP/Smepmp, and IOPMP support.
- Only the X100 cluster is a hypervisor target; the A100 AI cores explicitly omit the H extension.

Constraints and checks:

- Do not encode an Sv48-sized guest-physical address space into the common core.
- Treat guest-physical width, VMID width, ASID width, and interrupt-file count as discovered backend properties.
- The SoC device tree reports non-coherent DMA, so cache maintenance and shared-queue coherency are explicit backend obligations.
- IOMMU hardware is documented, but public mainline device-tree and driver integration must be verified on the actual board before device assignment work.
- On arrival, verify the H bit, `hgatp` modes and VMID width, AIA guest files, Sstc delegation, PMP state, IOMMU visibility, and OpenSBI handoff.

### RISC-V emulator baseline

Use QEMU `virt` under TCG before hardware arrives:

- The default RV64 CPU exposes the H extension.
- Use AIA with `aia=aplic-imsic` and an explicit guest interrupt-file count.
- Use `riscv-iommu-pci` or the platform IOMMU model for later DMA work.
- Constrain the emulated profile to Sv39 and other K3-relevant features rather than relying on QEMU's broadest CPU model.
- Boot OpenSBI in M-mode, hand off to Beryllium in HS-mode, and launch a synthetic payload in VS-mode; Linux is a stretch PoC outcome and later management-domain target.
- Use Spike only as a secondary CSR/ISA cross-check; QEMU is the functional platform baseline.

### RISC-V security-hardware workstream

The project inventories every relevant K3/RISC-V security feature and assigns it to the PoC, K3 bring-up, MVP planning, later research, or unsupported status.

Near-term focus:

- RVH and G-stage isolation.
- AIA/IMSIC/APLIC and Sstc as required by the payload.
- State-enable and counter gating.
- PMP/Smepmp handoff from OpenSBI.
- Cache-management behavior.
- Secure-boot, eFuse, TRNG, crypto, debug/trace, RAS, IOMMU, and IOPMP discovery.

Later research:

- DMA-safe device domains.
- Crypto-backed remote attestation.
- RAS/RERI containment.
- GPU/accelerator partitioning.
- CHERI-RISC-V and CoVE/Smmtt-class future hardware.

The full inventory is in `riscv-security-hardware.md`.

## Completed phase: Helium pathfinder comparison

Five bounded variants now cover:

- the original proof-oriented RISC-V isolation spine;
- an Arm64/TF-A portability reference;
- a minimal RISC-V ownership/capability/flow comparison;
- exact linked-byte transition, trap, and fixed-isolation proofs; and
- a fixed two-subject TE experiment.

The comparison and its claim boundaries are recorded in
`pathfinder-comparison.md`. It selects the isolation-engine shape and an
ownership-first static baseline for the next architecture deliverable, not a
permanent policy architecture.

The accepted `architecture-model-0.1.md` implementation provides the
static single-hart contract, executable model, host checker, bounded Rocq
obligations, and future C/assembly cut-point definitions. It adds no HS
runtime behavior. Responsible-human review accepted Model 0.1 on 2026-07-22;
later review remains incremental.

## Deferred protected-domain use-case hypothesis

The following remains a candidate later evaluation scenario, not a selected
next phase or a requirement on Architecture Model 0.2.

Choosing the service before the policy-neutral core mechanism boundary is
explicit would risk overfitting core objects, transitions, and interfaces.
Protected-service selection is therefore deferred until it tests a concrete
unresolved core or policy-model question.

The first usable system will run a protected security-research domain whose confidentiality and integrity remain enforced after host Linux is compromised.

Initial implications:

- Host Linux is not trusted to read or modify protected-domain private memory, vCPU state, policy state, or measurement identity.
- Host Linux is untrusted from its first instruction because Beryllium boots first.
- The privileged monitor owns protected-domain stage-2 mappings and validates every host request affecting protected resources.
- The first protected domain has no directly emulated general-purpose devices.
- Communication uses an explicit, revocable shared-memory and notification channel.
- Host denial of service is explicitly allowed in the first milestone: Linux may pause, starve, or terminate the protected domain.
- Termination or loss of service must be detectable in core-held state; the host must not alter a protected result or measurement. Cryptographic remote evidence is deferred to the attestation milestone.
- Firmware, hardware, boot root of trust, microcode, and the monitor itself remain candidate trusted assumptions to document rather than silently accept.
- The first persuasive demo should place a secret and an integrity-sensitive computation in the protected domain, then show that a hostile host cannot read or alter either or modify the immutable core-held domain measurement.

### Initial availability scope

- Confidentiality and integrity are security goals.
- Availability against the Linux management domain is not an initial security goal.
- No initial claim is made that the domain continues running after host failure or compromise.
- The monitor must preserve fail-closed behavior and evidence integrity when the host withholds resources or requests termination.
- CPU reservation, independent scheduling, restartable I/O services, and host-independent progress remain optional later milestones.

### Initial side-channel scope

- The first milestone claims architectural isolation, not comprehensive microarchitectural noninterference.
- Cache, predictor, SMT, memory-controller, power, thermal, timing, and other shared-resource channels must be listed in the threat model rather than silently ignored.
- Architecture-recommended transition mitigations should be applied where they do not undermine minimality or portability.
- The test plan should measure representative leakage and timing behavior without treating absence of observed leakage as proof.
- Stronger profiles may reserve cores, disable SMT, flush selected state, partition caches or memory bandwidth, or use hardware isolation features.
- Research on covert-channel bandwidth and cross-domain side channels remains a first-class optional workstream.

### Initial platform trust

Baseline profile:

- Trust the processor virtualization implementation, microcode, IOMMU, platform firmware, boot firmware, and verified-boot chain.
- Defend against malicious or compromised Linux and its userspace from the moment Linux is launched as a management/service domain.
- Treat physical attacks, invasive hardware attacks, malicious fabrication, and compromised vendor signing roots as out of scope.
- Record exact firmware, microcode, configuration, and monitor measurements so the trusted assumptions are inspectable.

Optional stronger launch profile:

- Trust the processor, microcode, required root-of-trust hardware, and isolation hardware, but do not trust general platform firmware.
- Use DRTM, late launch, a measured handoff, or an equivalent architecture-specific mechanism to establish the monitor after potentially untrusted firmware.
- Keep this profile architecturally planned from the start, but do not make it a first-milestone portability requirement.

## Planning principles

1. Keep the minimal core distinct from optional research extensions.
2. Share security invariants and interfaces across ISAs without hiding irreducible hardware differences.
3. Put mandatory enforcement mechanisms in the core and rich policy evaluation outside it.
4. Apply economy of mechanism, fail-safe defaults, complete mediation, open design, separation of privilege, least privilege, and least common mechanism.
5. Make every milestone useful before the next milestone exists.
6. Seek upstream feedback before interfaces harden.
7. Distinguish verified facts, strategic inference, and open questions.
8. State proof assumptions for boot code, assembly, compiler, hardware, firmware, DMA, and concurrency.
9. Keep each phase narrowly scoped; add hardware features, policy complexity, architectures, and assurance claims only after an explicit evidence gate.
10. Design the core hypervisor on policy-neutral terms before evaluating
    policy frameworks or integrating security models.
11. Treat the policy seam as bounded data proposed to the trusted mechanism,
    not as a selected callback, language, or runtime server.

## Strategic CHERI alignment

Beryllium must remain conceptually and technically aligned with CTSRD-CHERI and the evolving RISC-V CHERI ecosystem even though the SpacemiT K3 is not CHERI hardware.

Selected alignment rules:

- Use `riscv/sail-riscv` for the RISC-V behavior it currently supports. Until
  its H implementation is complete and merged, use the ratified H
  specification plus a bounded Rocq model for the required H behavior; track
  `CTSRD-CHERI/sail-cheri-riscv` and `riscv/riscv-cheri`.
- Model software capabilities using CHERI-compatible provenance, monotonic attenuation, root-authority, intentionality, and sealed-entry concepts without claiming hardware CHERI semantics.
- Evaluate capability-only and capability+TE compositions; do not assume a mandatory label layer before the pathfinder comparison.
- Keep stage-2, IOMMU, vCPU context, ABI, and attestation designs extensible to tagged, wider purecap contexts.
- Generate an auditable authority graph and evaluate CHERIoT's audit tooling as prior art.
- Prefer direct reuse, compatible artifact formats, thin adapters, and upstream contributions for Chisnall/CHERI tooling over Beryllium-only replacements.
- Align RISC-V instruction testing with Sail and TestRIG/RVFI-DII methods where practical.
- Design the build report and offline policy audit around CHERIoT authority-graph concepts while keeping rich policy engines outside the core.
- Use a reproducible devcontainer-style environment for the compiler, Sail model, simulator, proof tools, and tests.
- Treat David Chisnall's attributed writing and talks as authoritative project perspective, while specifications and formal models remain normative.
- Apply his recurring guidance that safe languages and CHERI compose, memory safety is foundational, capabilities are not identifiers, safe sharing is the hard problem, and most-privileged transition code must remain tiny.
- Do not transfer CHERIoT's microcontroller-specific mechanisms directly to application-class multicore systems without revalidation.

The detailed source and design map is in `cheri-alignment.md`.

## Initial conclusions

### Upstream positioning

- pKVM is the strongest in-tree precedent for a small monitor that protects guests from a compromised Linux host.
- RISC-V pKVM work and x86 prototypes show cross-architecture interest.
- Jailhouse, Bao, and ACRN demonstrate useful minimal or partitioning designs but remain separate projects.
- The first RFC should describe a functional gap such as a "minimal protected virtualization monitor" rather than lead with type-1/type-2 terminology.
- Beryllium will prototype an independent core while using these projects to define interoperability and upstream comparison points.
- pKVM is not precedent for Beryllium's hypervisor-first boot or separate Kbuild image; the upstream placement argument must stand independently.

### Nitro and service-domain separation

- AWS publicly describes a KVM-derived Nitro Hypervisor limited to CPU/memory partitioning, VM lifecycle, device assignment, and hardware-error responsibilities.
- Networking, storage, control-plane APIs, encryption keys, and management live on physically separate Nitro Cards.
- The Nitro Hypervisor has no network stack, general-purpose filesystem, peripheral drivers, shell, or interactive operator access.
- No public source found in this research pass documents a Nitro-specific EL2 mechanism / EL1 policy split on Graviton.
- Transferable rules are narrow authenticated interfaces, no device stack in the core, passive command handling, dedicated I/O domains, measured loading, and independent recovery/update boundaries.

### Policy and authority

- FLASK is the key policy/mechanism precedent: object managers enforce, a security server decides, opaque labels identify subjects and objects, and generation-aware caches accelerate decisions.
- The Model 0.1 baseline is immutable ownership plus explicit channels; the
  permanent runtime authority mechanism remains trigger-gated.
- Model 0.2 is not a policy evaluation. It defines how policy-neutral
  configuration input is copied, validated, sealed, and refined into
  enforcement without selecting its producer or semantics.
- Static boot policy should be deterministic, analyzable, measurable, and attestable.
- Dynamic policy belongs in an optional or separately trusted domain. Failure and stale policy must deny.
- Cedar is a useful model for formal semantics, deterministic total evaluation, schema validation, SMT analysis, and differential testing. Its full runtime, OPA/Rego, and other application policy engines do not belong in the core.
- The completed pathfinder comparison retains software capabilities and
  capability+TE as later options only when their recorded triggers fire.

## Draft core boundary

The common core should own:

- Domain identity, lifecycle, and ownership.
- CPU allocation and vCPU lifecycle.
- Stage-2/second-stage translation ownership and permissions.
- Controlled shared-memory grants.
- Interrupt and timer injection contracts.
- IOMMU/DMA protection-domain ownership.
- Policy-neutral validation of ownership/channel state and complete mediation.
- Measurement identity and attestation handoff.
- Failure, reset, and recovery state transitions.

Architecture backends should own:

- RISC-V HS/VS context initially; future backends own their architecture-specific context.
- Exit and trap decoding.
- Page-table formats, invalidation, and confidential-memory transitions.
- AIA, timer, and RISC-V IOMMU/IOPMP details initially.
- SBI boot/power paths initially.
- Future Arm or x86 backends own GIC/SMMU/PSCI or APIC/IOMMU/ACPI and confidential-computing protocols.

## Mandatory requirements

- The trusted core must be small enough to audit and formally model.
- Every security-sensitive operation must pass a documented mediation point.
- Missing, ambiguous, stale, or unavailable policy must fail closed.
- Authority must be explicit and non-ambient.
- The core must enforce CPU, memory, interrupt, and DMA ownership.
- Shared memory and notifications must be explicit, attributable, and revocable.
- Common interfaces must not preclude future Arm portability, but immediate conformance targets are RISC-V only.
- Confidential-computing modes must remain architecture adapters.
- Boot, configuration, and policy identity must be measurable.
- Debug and introspection must be absent by default or policy mediated.
- External interfaces must be bounded and versioned.
- Contributors must have a QEMU-based path that does not require special hardware.

## Outside the minimal core by default

- Network and storage stacks.
- General drivers and device models.
- Filesystems and shells.
- Rich policy parsers, compilers, and interactive policy engines.
- Orchestration and fleet management.
- Telemetry aggregation.
- Live migration.
- Overcommit and complex scheduling policy.
- Nested virtualization.
- Broad legacy firmware and hardware emulation.
- Research instrumentation that weakens production isolation.

## Architecture options

### A. Independent in-tree hypervisor subsystem

Place the new core and per-architecture backends in the Linux source tree while producing a hypervisor image that boots before and launches Linux.

Strengths: satisfies the project identity and can reuse kernel build, review, architecture, and test infrastructure.

Risks: highest upstream burden, unusual kernel-tree build/deployment semantics, duplication objections, and difficult boot/ownership transitions.

Status: selected hard upstream target, subject to maintainer feedback on source-tree form.

### B. Linux-launched independent monitor

Use Linux for boot and hardware discovery, then activate the independent monitor and deprivilege Linux into a management or service domain.

Strengths: practical hardware bring-up and an independent security architecture.

Risks: security-critical ownership transfer and uncertain upstream placement.

### C. Standalone monitor with in-tree Linux interfaces

Keep the independent monitor in its own project and upstream only loader, management, guest, attestation, or service-domain interfaces.

Strengths: maximum language, proof, release, and governance freedom.

Risks: weaker "within the Linux tree" result and duplicated hardware/platform work.

### D. Optional KVM/pKVM interoperability

Provide adapters that reuse selected KVM userspace interfaces, protected-VM conventions, tests, or management tooling without making KVM the core architecture.

Strengths: lowers integration cost and creates a migration path for users.

Risks: compatibility pressure can contaminate the minimal design.

### E. Firmware or hardware security-module deployment

Align with TDX Module, Arm RMM, RISC-V TSM, ultravisors, or DPU firmware.

Strengths: strong isolation from a compromised host.

Risks: hardware availability, opaque roots, and portability.

## Selected policy/mechanism separation

Policy/mechanism separation is a first-class architectural and formal-assurance goal, not an optional afterthought.

### Current core-first sequencing

Architecture Model 0.2 designs the hypervisor core on its own terms before
policy evaluation:

- no protected-service scenario is selected;
- no capability, TE, MLS/MCS, RBAC, identity, or flow model is integrated;
- no Rego, Cedar, FLASK, or other framework is evaluated;
- no policy callback or runtime policy server is defined; and
- no policy model may directly mutate trusted roots, mappings, bindings, or
  canonical authority.

The current seam is only:

```text
bounded configuration proposal
  -> HS canonical validator
  -> sealed authoritative state
  -> derived roots, transitions, and access enforcement
```

The core proves structural safety of accepted state. It does not prove that an
accepted proposal expresses an operator's intended higher-level policy.

### Trusted mechanism

The minimal core implements:

- Domain, memory, vCPU, interrupt, and device object identity.
- Explicit bounded authority references or ownership records.
- Complete mediation at every resource transition and shared operation.
- Stage-2 and IOMMU ownership enforcement.
- Policy-generation tracking, atomic activation, and revocation where the selected policy model requires them.
- Fail-closed handling for missing, malformed, stale, unavailable, or unauthorized decisions.

### Policy components outside the core

- Policy language and authoring tools.
- Schema and configuration validation.
- Policy compilation and optimization.
- Capability delegation, Type Enforcement, information-flow, ownership, or attestation-policy decisions according to the selected model.
- Runtime policy service, if enabled.
- Analysis, explanation, audit presentation, and administrative workflow.

### Policy invariant retained during evaluation

- The measured boot policy and initial authority graph define an immutable authority ceiling for a running configuration.
- A runtime policy domain is not trusted to preserve Beryllium or cross-domain isolation.
- It cannot create root authority, relabel or reassign core-owned objects outside delegated rules, alter the active boot-policy measurement, or bypass complete mediation.
- Every dynamic grant must be a subset of authority already delegated to the issuing policy domain.
- Dynamic authorization artifacts bind issuer, subject, object, rights, policy generation, and revocation lineage where applicable.
- Beryllium validates structure, authority ancestry, generation freshness, and rights subset before enforcement.
- A strict profile permits the policy domain only to narrow or revoke authority after boot.
- A delegated-administration profile permits grants within an explicit boot-authorized envelope; compromise can misuse that delegated authority but cannot amplify it.
- Policy-domain failure, timeout, malformed output, stale generation, or unverifiable ancestry fails closed.
- Attestation identifies the boot authority ceiling, active profile, policy generation, and optional policy-domain measurement.

### Pathfinder policy result and initial baseline

The completed comparison found:

1. immutable ownership plus explicit grants is the smallest sufficient
   baseline for the tested isolation properties;
2. software capabilities add useful designation, attenuation, and derivation
   semantics when delegation is required; and
3. mandatory flow or TE can independently deny designated authority, but adds
   state, lifecycle, proof, and usability obligations.

Model 0.1 therefore uses ownership and explicit channels. It defines
falsifiable capability and TE triggers without implementing either mechanism.
Type Enforcement, direct TE, and CAP+TE remain unselected for a runtime core.

### Formal assurance split after selection

Mechanism proof targets:

- Complete mediation over the modeled operation set.
- Authority non-forgeability and non-amplification for the selected model.
- Domain memory and vCPU isolation.
- Stage-2 and IOMMU ownership invariants.
- Grant and revoke correctness.
- Policy-generation and decision-cache freshness.
- Fail-closed behavior.
- Architectural noninterference for selected single-hart static configurations.

Policy proof targets:

- Deterministic and total policy semantics.
- Default-deny and explicit conflict resolution.
- Schema validity and bounded evaluation.
- Compiler preservation from source policy to the compact artifact.
- Static checks for unreachable, contradictory, over-broad, or non-revocable authority.
- Attestation binding between policy source identity, compiled artifact, and active generation.
- Authority non-amplification across every delegation chain.
- Monotonic restriction for the strict runtime profile.

Development method:

- Keep an executable formal model of both the mechanism and policy semantics.
- Differential-test production implementations against the model, following the Cedar verification-guided pattern.
- Model policy update, revocation, and cache invalidation as concurrent protocols before code.
- Give each architecture backend explicit proof obligations for translation, invalidation, interrupt, and IOMMU operations.
- Do not claim that policy verification proves hardware, firmware, assembly, or backend correctness.

## Policy architecture decision gate

The comparison closes the question of which authority baseline to use for
Model 0.1: immutable ownership and explicit channels.

The permanent runtime authority model remains open, and Model 0.2 deliberately
does not evaluate it. A software-capability extension eventually requires a
selected use case with runtime delegation, attenuation, holder transfer, or
revocation needs. TE eventually requires a concrete independently mandatory
denial that ownership, channel separation, and capability rights cannot
express acceptably.

The default CAP+TE candidate keeps capability designation and canonical-object
TE independently observable. Applying TE to capability receipt, possession,
transfer, delegation, invocation, attenuation, or revocation is a separate
research hypothesis with close SELinux/Xen precedents. It requires explicit
responsible-human decisions about label location, possession versus use,
transfer semantics, relabeling, revocation, and the mandatory denial being
modeled; no novelty or runtime selection is claimed.

Before a policy architecture or protected-service plan is approved, the later
selected use case and trigger result must update:

- Core object representation.
- Manifest semantics.
- Authorization API.
- Revocation.
- Audit schema.
- Formal properties.
- CHERI mapping.

## I/O and service-domain hypothesis

1. The core owns IOMMU domains, interrupts, reset authority, and grant/revoke operations.
2. Drivers run in Linux or dedicated service domains.
3. Initial I/O uses assigned devices, virtio-style queues, or a minimal message/grant protocol.
4. The core validates memory ownership and notification endpoints, not network or storage protocols.
5. Device-domain compromise cannot DMA or interrupt outside its grants.
6. Service domains are restartable where hardware permits.
7. SR-IOV, vDPA, DPUs, and vendor offload are optional; software domains provide a commodity fallback.

### Deferred VS control-plane decomposition

Rich management and policy behavior remains outside the HS core, but the first
runtime plan must decide whether it needs:

- one Linux/VMM management domain; or
- multiple isolated lifecycle, device, scheduling-policy, attestation, and
  orchestration services.

The decision must be driven by one bounded workload and explicit fault,
authority, restart, and protocol requirements. Do not introduce multiple
services merely to imitate a microservice architecture. CHERI capabilities,
capability IPC, memory tagging, and software fault isolation remain possible
future compartmentalization inputs, not selected mechanisms.

## Selected C-first language direction

The initial trusted core is C-first.

Rationale:

- C has the most mature whole-system and hypervisor proof precedents.
- seL4 demonstrates that restricted C, ordinary open compilers, theorem proving, and separate translation validation can support very high assurance.
- Focused pKVM/CN, SeKVM, and TF-RMM work demonstrates selected-module proof and model checking over ordinary GNU/Clang C.
- Frama-C, CBMC, Cerberus/CN, VST's open distribution, RefinedC, KLEE, and related tools provide candidate complementary analyses.
- CTSRD-CHERI, CheriBSD, CHERIoT, CHERI-seL4, and current CHERI hypervisor work are predominantly C/C++ plus assembly and Sail.
- A C-first core simplifies future CHERI Clang purecap/hybrid experiments.
- Rust remains strategically valuable, but its CHERI toolchain and whole-system formal-verification path are less mature.
- The Nitro Isolation Engine demonstrates a credible restricted-Rust/Isabelle alternative, but its source and project proofs were not yet public and its AutoCorrode C frontend is experimental.

Open-source correction:

- CompCert is excluded because the full compiler is licensed for non-commercial use and does not satisfy the project requirement.
- No proof, release, or certification claim may depend on CompCert or another field-of-use-restricted tool.
- Proprietary tools are permitted only as time-limited exploratory blockers under the escalation policy in `open-tooling.md`; their output is non-normative.

Initial C discipline:

- Define and document a small freestanding C subset for the core.
- Avoid undefined behavior by construction and machine-checked analysis.
- Keep implementation-defined and compiler-extension-dependent behavior isolated and specified.
- Minimize pointer arithmetic, aliasing, mutable global state, inline assembly, and implicit integer conversion.
- Use explicit-width types, checked arithmetic, explicit ownership/state transitions, and generated or verified layout assertions.
- Keep boot, trap entry, context switch, and special-instruction assembly in a narrow reviewed boundary.
- Avoid a general heap in the first core milestone; use static or region-based allocation unless the proof plan demonstrates otherwise.
- Maintain the abstract state machine independently of C.

### Selected C implementation boundary

All Beryllium C code uses a documented restricted GNU C dialect accepted by both GCC and Clang and suitable for eventual Kbuild integration.

The proof boundary has three layers:

1. **Proof-bearing mechanism subset**
   - Domain and object lifecycle state machine.
   - Capability creation, derivation, attenuation, invocation, and revocation.
   - Selected authorization checks and policy-generation validation.
   - Memory ownership and grant transitions.
   - Architecture-neutral stage-2 and IOMMU mapping preconditions/postconditions.
   - Measurement and attestation state transitions.
   - Serialized control-path operations.

   This subset avoids unnecessary GNU extensions, opaque aliasing, unbounded recursion, variadic functions, implicit allocation, uncontrolled function pointers, and representation-dependent behavior. Exact rules will be generated as a machine-checkable coding profile.

2. **Restricted core support code**
   - Data-structure implementations.
   - Per-core run state.
   - Bounded queues and logs.
   - Parsers for fixed, versioned boot and management formats.
   - Architecture-independent glue.

   This code receives broad open static analysis, bounded model checking, fuzzing, and tests. Selected modules may graduate into the proof-bearing subset.

3. **Thin platform and assembly boundary**
   - Reset/entry code.
   - Trap entry/return and register save/restore.
   - Privileged CSR/system-register operations.
   - TLB/IOMMU invalidation instructions.
   - Interrupt-controller and timer primitives.
   - Linker script and image handoff.

   Every function in this boundary has an explicit contract and architecture-model assumption. Keep C compiler extensions and inline assembly isolated here where possible.

Rules:

- The proof-bearing subset and support code are compiled by both GCC and Clang.
- Generated/preprocessed proof inputs are traceable to the exact source and configuration.
- Open translation validation connects selected compiled functions to their C-level proofs.
- The linked image and measured artifact are reproducible.
- Code cannot move from the platform boundary into the mechanism core without satisfying the stronger subset.

Verification plan:

1. Sail/Isla or equivalent for ISA and critical assembly behavior.
2. Rocq/Coq for the abstract mechanism, security properties, and refinement.
3. Use Cerberus as the C semantic reference; pilot CN on sequential leaf modules; evaluate VST's BSD opam distribution and RefinedC after license and community gates.
4. Frama-C open plugins and CBMC for broad static and bounded checks.
5. Develop or reuse a fully open translation-validation path for proof-bearing functions compiled with GCC and Clang.
6. Differential, property-based, fuzz, sanitizer, and hardware/QEMU tests for the full build.
7. Explicit reconciliation between abstract proof, C proof, compiler output, linked image, and measured artifact.

### Selected proof ecosystem

Rocq/Coq is the primary proof environment.

Primary stack:

- Sail-generated Coq/Rocq definitions for RISC-V and later CHERI ISA semantics.
- A Rocq abstract specification for domains, ownership/authority, memory ownership, policy generations, and lifecycle transitions.
- Refinement proofs from the abstract state machine to the restricted C implementation.
- Cerberus defines the restricted C semantics.
- CN is a non-load-bearing pilot for sequential ownership-heavy modules.
- VST's open distribution, RefinedC, or direct Rocq proofs remain candidates for load-bearing C refinement after final audits.
- Coq-Sail, Isla/Islaris, or equivalent bridges for critical instruction and assembly reasoning.

Complementary tools:

- Isabelle/HOL for comparison with seL4 and CHERI proof artifacts and for selected imported or independently checked properties.
- TLA+/PlusCal or equivalent model checking for concurrent protocols and state-machine exploration.
- Frama-C, CBMC, KLEE, sanitizers, fuzzing, and property tests for broader implementation coverage.
- Differential testing against Sail, QEMU, and hardware.

Proof-management rule:

- Do not maintain complete duplicate Rocq and Isabelle proofs.
- State every imported theorem, generated definition, trusted translation, and version pin.
- Keep executable specifications and counterexample-producing tools available even when a theorem is proved.
- Require every mandatory proof and analysis dependency to pass the open-tooling scorecard in `open-tooling.md`.

### Selected Cerberus/CN role

- Cerberus is the semantic oracle for C pointer provenance, undefined behavior, memory layout, and CHERI-aligned C semantics.
- CN is evaluated on allocators, page-table helpers, capability-table operations, and bounded parsers.
- CN results supplement, but do not replace, Rocq refinement proofs, Frama-C, CBMC, fuzzing, or translation validation.
- CN's sequential logic cannot justify shared multicore state.
- Stage-2 CN use requires single-hart execution or a proved precondition that the caller owns the global control lock or exclusive per-core state.
- Promotion requires independently checked proof logs for the relevant obligations, a stable open release, broader maintenance, and a concurrency story.

## Open tooling and certification strategy

All project tooling is fully open source and reproducible. Broadly adopted, multi-maintainer projects are preferred; narrow research tools must have replaceable roles and independently checked outputs. Hosted services may mirror results but cannot be the sole way to produce them.

The project will maintain an open tool-qualification evidence set:

- Operational requirements.
- Intended-use and impact classification.
- Versioned source and reproducible build.
- Validation suite.
- Known limitations.
- Configuration-management and change-impact process.
- Independent result checks.
- Requirements-to-evidence traceability.

High-assurance profiles may draw on DO-333/DO-330, Common Criteria, ISO 26262, IEC 61508, EN 50716, and multicore interference guidance, but no certification claim is made until a specific target and evaluator are selected.

The detailed policy and candidate baseline are in `open-tooling.md`.

### Selected binary-assurance staging

- Early prototypes explicitly trust pinned GCC and Clang plus the linker.
- Build with both compilers and compare behavior, layouts, disassembly, and conformance results.
- Preserve exact source, configuration, preprocessed proof input, objects, image, and measurement provenance.
- Align with open seL4 `l4v`/AutoCorres/binary-verification and Cambridge REMS/Isla/Islaris work.
- Treat direct seL4 artifact reuse as an evaluated option, not an assumption: the seL4 binary work is Isabelle-based.
- Isabelle may be load-bearing for the bounded binary-validation workstream without duplicating the Rocq functional proof.
- The assurance release requires fully open source-to-binary correspondence for the proof-bearing subset.
- Until that exists, mark binary-level properties as unverified rather than implying compiler correctness.
- A missing open tool becomes a tracked side-project candidate.
- A proprietary tool is a temporary exploratory last resort only; using one triggers a direction review and cannot support a normative claim.
- Milestone 8 cannot complete without an open binary-correspondence result; otherwise the compiler remains an explicit assumption and the release is pre-assurance.

### Selected profile-neutral assurance model

Beryllium follows seL4's proof-as-reusable-evidence approach:

- The core proof is not tied to one regulator or certificate.
- Functional correctness, integrity, confidentiality/noninterference, authority confinement, policy/mechanism separation, and selected binary correspondence are reusable evidence.
- Proof assumptions and unverified features are published as first-class artifacts.
- Security properties are parameterized by a machine-readable domain, capability, TE-label, memory, interrupt, and device configuration.
- A verified or validated initializer must instantiate the specified configuration before untrusted domains run.
- Each deployment combines the reusable Beryllium evidence with its own hazard/threat analysis, application evidence, hardware evidence, processes, tests, and evaluator requirements.

Required reusable artifacts:

- Formal abstract specification.
- Executable reference model.
- Restricted-C refinement proof.
- Security-property proofs.
- Architecture-backend obligations.
- Configuration and authority-graph description.
- Initializer and boot-state correspondence.
- Compiler/binary translation evidence.
- Assumption and trusted-base ledger.
- Tool validation and qualification evidence.
- Requirements-to-proof/test traceability.
- Reproducible source, proof, binary, and measurement bundle.

Deployment crosswalks:

- Common Criteria.
- DO-178C/DO-333/DO-330 and multicore guidance.
- ISO 26262.
- IEC 61508.
- EN 50716.
- NIST SSDF and supply-chain requirements.

No document may describe Beryllium as certified unless a named product/configuration has received a certificate from a named evaluator.

### Selected concurrency model

Stage 1 is single-hart:

- One Beryllium execution context.
- One Linux management vCPU and one protected-domain vCPU may be time-multiplexed for functional bring-up.
- No interprocessor interrupts, cross-core TLB invalidation, shared run queues, or concurrent policy updates.
- The first refinement and noninterference proofs target this configuration.
- Validate the Sail-to-Rocq RISC-V H-extension path during this stage; do not assume backend maturity.

Stage 2 adds serialized multicore support:

- CPUs are statically assigned to domains or the management role.
- Guest-entry, exit, register, timer, and interrupt fast-path state is per-core.
- Shared mutable state is limited to lifecycle, capability, grant/revoke, policy-generation, ownership-transfer, and global invalidation operations.
- One global control lock establishes a total order for those rare operations.
- No lock is held across guest execution or an untrusted-domain call.
- Critical sections are bounded and do not wait on host-controlled resources.
- Cross-core TLB/IOMMU invalidation and interrupt-routing updates occur through the serialized protocol.
- Lock contention and control-path starvation are availability issues and remain outside the first security claim.

Proof targets:

- Single-hart functional correctness and isolation first.
- Refinement from the serialized multicore implementation to an atomic control-operation model.
- Per-core state separation.
- Lock invariant, bounded critical sections, and absence of untrusted blocking while locked.
- Correct invalidation ordering before authority or memory reuse.

Deferred:

- Fine-grained locking.
- Work stealing and shared run queues.
- Concurrent policy activation.
- A multikernel/per-core-instance redesign.

Rust later:

- Prefer Rust first for untrusted or separately trusted policy tooling, analysis tools, service domains, and test infrastructure.
- Consider Rust inside the trusted core only after defining a mechanically checkable C/Rust FFI contract and demonstrating a net reduction in TCB/proof burden.
- Track Verus as the leading practical future verifier for a safe bounded VS
  service/protocol core, Kani as complementary bounded checking, and
  Aeneas/Charon as the direct Rocq extraction experiment.
- Treat Verus's rustc/SMT/specification stack, external bodies, layouts, FFI,
  assembly, MMIO, and hardware contracts as explicit assumptions; no Verus
  result transfers to the C HS core or Rocq architecture proof.
- Continue tracking Rust+CHERI as possible later service-component work, not
  as a current runtime dependency.

Any later Rust or mixed-language reassessment should compare:

- Binary and source size.
- Unsafe, assembly, and FFI boundaries.
- Architecture support.
- Stage-2 and IOMMU clarity.
- Concurrency and interrupt safety.
- Toolchain reproducibility.
- Kernel review and maintenance burden.
- Formal-model and proof suitability.

Assurance should progress through:

1. Threat model and attack-surface inventory.
2. Executable lifecycle, ownership, and policy models.
3. Concurrency and invalidation model checking.
4. Differential and property-based tests.
5. KUnit, kselftest, fuzzing, and sanitizers.
6. Bounded verification of critical operations.
7. Deductive proof of selected isolation and revocation invariants.
8. Proof-to-binary work for a bounded configuration, required before the assurance-release milestone can complete.

## Roadmap status

The pathfinder phase and automated Architecture Model 0.1 implementation are
complete, and responsible-human review accepted Model 0.1 on 2026-07-22. The
Architecture Model 0.2 boundary and evidence are also complete and were
accepted on 2026-07-24. The bounded single-hart runtime-planning phase is now
complete and accepted, and its exact fixed implementation profile was
separately authorized on 2026-07-25. The exact non-privileged R0 freeze was
accepted on 2026-07-27. Exact bounded R1 pure-C mechanism commit
`a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` was accepted on 2026-07-28.
The R2 plan and implementation are also complete and accepted: plan commit
`cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` and implementation commit
`6e1cb579257c5dbe3234bd484fd091629e87181b`. R3 was separately authorized on
2026-07-29 and its boot-and-first-entry implementation content and evidence
are complete. Exact implementation target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` is responsible-human accepted on
that date. In-tree evidence records the fixed comparison base, dynamic
generation HEAD, source identities, repository state, accepted target, and
separate packet follow-up. The
[R3 review and acceptance record](single-hart-runtime-r3-review-summary.md)
preserves the exact decision. Immediate non-implementation work includes
acceptance-record review, K3 evidence planning, and community feedback.
Responsible-human review accepted exact R4 target
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52` on 2026-07-29. The implementation
parent `6e5c55c59e94bbaba136269c784db28ec1b53f54` and decision-support packet
follow-up `ec7be2f146a851e7608e77eb2875076e66aab2e6` remain distinct.
Responsible-human review accepted the bounded R5 plan at exact commit
`fecae6b62a507bdbb93d211262197a31f5422316` on 2026-07-30 and separately
authorized R5 implementation under that accepted plan. R5 implementation is
exact accepted target `165f4d001a2b59b582b397bdea79ec4826168fdb` over
parent `9312c1355a23d411e3bdafb2183be342683a8ab9`, exact-target validated
(`./be r5-check`, `./be r4-check`, `make check`), with no
significant issue found by an independent core/runtime review, and
responsible-human accepted on 2026-07-30
(see [`single-hart-runtime-r5-evidence.md`](single-hart-runtime-r5-evidence.md)
and [`single-hart-runtime-r5-review-summary.md`](single-hart-runtime-r5-review-summary.md)).
R6 implementation work is authorized under the master-plan R6 row by the
recorded `proceed to implement R6 exact` and `proceed with all r6
implementation work` instructions, and the
[bounded R6 plan](single-hart-runtime-r6-plan.md) is accepted at original exact
target `609867fdad75279c0913022909efd65c4a838909` and at corrected exact
target `75269f058ae578b0a76a113d6c05c0aaceeac8ec` as of 2026-07-30, and D-15
resumed under the already-recorded implementation authorization. Narrow
[Plan revision R6-B](single-hart-runtime-r6-plan.md#plan-revision-r6-b-d-15-image-layout-and-trace-retention)
is accepted at exact target `6d6464c6c937abccd59df932006c1049fd79fac6` as of
2026-07-30 (see its
[R6-B plan revision review and acceptance record](single-hart-runtime-r6-plan-r6b-review-summary.md)),
so R6 integration and evidence work resumed with every pinned value
re-derived at the exact implementation commit; that work is now complete,
fully checked, and committed at exact implementation target
`7ba3649f03cf13b65df33020e345d361cce2993a` (parent and initial implementation
`9ed5ad7069b6067f03e1923c09937fe218240a59`), recorded in the
[R6 adversarial-image evidence](single-hart-runtime-r6-evidence.md), and
accepted on 2026-08-05 as recorded in the
[R6 review and acceptance record](single-hart-runtime-r6-review-summary.md).
R7 is authorized under
[the bounded R7 plan](single-hart-runtime-r7-plan.md), which is accepted at
exact target `18c43596d308052cfad67edc6e2cb8f543f75600`, with Plan revision
R7-A accepted at exact target `0605028220e3795d99393156d0bfb7d6a7d631a4`. Its
package is
accepted at exact implementation target
`9bf22913d67e9b72286813cd5f7993a9ad3857a8` as of 2026-08-05, over superseded
first candidate `95639afb0ab57959a32d055f7b7f9bdb474fe762`, and root
integration is applied within
the accepted six-constant enumeration. The combined K3 core-validation plan
was accepted at exact target
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`, with implementation authorized
only for non-privileged H0, and Plan revision R8-A was accepted at exact
target `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`. Plan revision R8-C was
accepted at exact target `f47ae60266a467ca1a7704fd9a50b140e0f31bb0`. Exact
bounded non-privileged H0/R8-C target
`1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` was accepted on 2026-09-17 but
remains `BLOCKED-NOT-READY` with 80 H0 blockers, 118 `UNKNOWN`, and
`r8_h0_exit=not-met`.

From 2026-10-06 the K3 bring-up sprint (section 2.15) became the K3 path of
record: B0 was decoupled from KVM0, and B0-B7 and the accepted-tool fixes
were each accepted at one exact commit by 2026-10-09. On 2026-10-08 the
responsible human dropped the KVM0 workstream and R8 stages H1-H4, keeping
their records as history; H1-H4 were never authorized or run. The B-series
board runs are diagnostic bring-up evidence for one board, and hardware
validation is `NOT RUN`. The docs-only step 3 re-baseline is accepted at
`ecad45d8`, the B7 plan at `026974fb`, and the B7 result at `7b6b846b`;
S1-S3 (section 2.16) are complete and accepted, with the S3 MVP plan at
`93967fba` (2026-10-23), and publication remains blocked.

The milestones below remain a flexible candidate roadmap, not an approved
MVP 1.0 plan. The accepted S3 [MVP plan](mvp-plan.md) selects MVP 1.0's
milestones M0 to M4, bounded by the accepted Model 0.2 boundary, the
B-series evidence, S1, and S2; it takes the smallest static form of
milestone 3 (as M2) and the static part of milestone 4's concurrency
model into MVP 1.0 and leaves the rest of milestones 3 to 10 to later
plans. Protected-service selection is made by that plan (D10: M2's
protected research domain, no service runtime); under its revised
definition (RP-3 of the accepted revision plan, accepted 2026-10-18), S2
produced the policy specification and its analyses and recorded whether
the platform's use cases fire the capability and runtime-check triggers.

## Candidate post-pathfinder milestones

Sections 1 to 2.15 record accepted or dropped work, and section 2.16 lists
the planned next sequence, now complete. Milestones 3 to 10 remain
candidates: the accepted S3 MVP plan takes bounded static parts of 3 and
4 into MVP 1.0, and each milestone otherwise waits for its own plan after
MVP 1.0; none is authorized.

### 0. Evidence base and problem statement

Deliver a curated literature map, threat-model candidates, architecture option matrix, upstream problem statement, community map, assumptions ledger, and profile-neutral assurance crosswalk skeleton.

User benefit: a reliable field map and a concrete proposal to critique.

Gate: pathfinder inputs are sufficient to start the PoC.

### 1. Architecture Model 0.1

Status: complete and accepted on 2026-07-22; incremental review continues.

Deliver the static single-hart, two-domain isolation contract; canonical
manifest semantics; executable state machine; host reference checker;
adversarial tests; bounded Rocq ownership, exclusion, mapping, state-separation,
channel, switch-freshness, and fail-closed obligations; cross-variant trace;
and future C/assembly cut-point contracts.

User benefit: one inspectable architecture and evidence boundary before new
privileged behavior exists.

Gate: complete. Continue with the policy-neutral core mechanism boundary.

### 2. Architecture Model 0.2

Status: complete and accepted on 2026-07-24.

Deliver the policy-neutral separation of copied configuration proposals,
canonical sealed HS state, and derived enforcement; explicit core phases;
adversarial validation fixtures; deterministic reports; bounded Rocq
obligations; and a claim/assumption trace to Model 0.1.

User benefit: an inspectable hypervisor mechanism that can later evaluate
different policy and security models without embedding one prematurely.

Gate: complete. Responsible-human direction selected bounded single-hart
runtime planning as the successor.

### 2.5 Bounded single-hart runtime plan

Status: complete and accepted on 2026-07-25; exact fixed implementation
profile separately authorized.

Deliver the exact fixed QEMU/OpenSBI/HS/VS profile, two role-neutral synthetic
VS domains, no guest-visible SBI, boot and memory layout, configuration and
root contracts, complete register-state disposition, model-to-runtime cut
points, work packages, evidence gates, claim limits, and explicit non-goals.

User benefit: one reviewable bridge from the accepted abstract mechanism to a
future privileged implementation without first importing Linux, services,
policy, devices, or multicore.

Gate: complete. Implement only the accepted R0-R7 dependency graph in
[`single-hart-runtime-plan.md`](single-hart-runtime-plan.md).

### 2.6 R0 fixed profile and layout

Status: complete and accepted on 2026-07-27; no privileged runtime source.

Deliver exact QEMU, OpenSBI, compiler, linker, and supporting-tool revisions;
the one-hart CPU command and forbidden optional ISA state; complete linker and
physical-memory layout; generated inventory and proposal constants; complete
register-state matrix; exact HS-to-M SBI allowlist and failures; fixture plan;
and a trace to Model 0.2.

User benefit: a frozen and reviewable implementation target before C or
assembly can acquire accidental platform assumptions.

Gate: complete. Responsible-human review accepted exact freeze commit
`64a88b15a6c35d522fa997699c4fb514b15da314` on 2026-07-27. Exact R1 pure-C
mechanism commit `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` was accepted on
2026-07-28.

### 2.7 R1 pure-C mechanism

Status: complete and accepted on 2026-07-28 at exact commit
`a6e0bb178c10a7e68c9447a8e58affb94b8ecadb`.

Deliver restricted-C-only copy, validation, canonicalization, one-way
sealing, abstract derivation, deterministic reporting, retained evidence, and
terminal fail-closed phase logic for the accepted fixed profile; preserve the
thirteen-resource full profile, six canonical authorities, and two abstract
derived roots with three mappings each; and keep the Model 0.2 projection
explicitly non-refining.

User benefit: one complete, reviewable, non-privileged runtime-mechanism step
before any Sv39x4 backend, boot, trap, or QEMU execution work begins.

Gate: responsible-human review accepted exact commit
`a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` on 2026-07-28. R2 depends on
R1; its separately reviewed plan and implementation are now accepted.

### 2.8 R2 Sv39x4 backend

Status: complete and accepted on 2026-07-28 at exact implementation commit
`6e1cb579257c5dbe3234bd484fd091629e87181b`; bounded plan accepted at
`cdcf1603b97e0ef4da3e571e43fd7045116ea1ce`.

Deliver fixed non-privileged Sv39x4 page-table storage and construction, an
independent leaf walker/recheck, HGATP computation, adversarial GCC/Clang host
tests, deterministic reporting, and retained evidence derived from R1 sealed
canonical state.

User benefit: a reviewable concrete G-stage translation backend before any
CSR write, image, boot, trap, or Beryllium QEMU execution.

Gate: complete and accepted at the R2 boundary. R3 was separately authorized
on 2026-07-29; R2 acceptance itself did not authorize tagging, pushing, public
release, or R3.

### 2.9 R3 boot and first entry

Status: implementation content complete and responsible-human accepted on
2026-07-29 at exact target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`.

Deliver the pinned OpenSBI hart-zero handoff, executable frozen linker map,
required SBI discovery and bounded DBCN/SRST path, accepted R1 flow, R2 roots
in actual linker pools with independent re-walk, complete bounded HS/VS reset
and readback, exact management binding publication, management HGATP write,
local `HFENCE.GVMA x0,x0`, CSR readback, deterministic guest GPR state, and
the exact R3 `sstatus.SPP=1 -> SRET` sequence before QEMU `V=1` at the first
management PC under repeated GCC and Clang traces.

User benefit: the first privileged, linked, reviewable bridge from accepted
R1/R2 state to real VS execution without importing trap handling, switching,
Linux, services, devices, policy, or multicore.

Gate: exact implementation target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` is accepted; dynamic generation
HEAD and packet follow-up remain distinct. Exact R4 target
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52` is accepted on 2026-07-29; its
implementation parent `6e5c55c59e94bbaba136269c784db28ec1b53f54` and
decision-support follow-up `ec7be2f146a851e7608e77eb2875076e66aab2e6` remain
distinct. Responsible-human review accepted the bounded R5 plan at exact
commit `fecae6b62a507bdbb93d211262197a31f5422316` on 2026-07-30 and
separately authorized R5 implementation under that accepted plan. R5
implementation is exact accepted target
`165f4d001a2b59b582b397bdea79ec4826168fdb` over parent
`9312c1355a23d411e3bdafb2183be342683a8ab9`
(see [`single-hart-runtime-r5-evidence.md`](single-hart-runtime-r5-evidence.md)
and [`single-hart-runtime-r5-review-summary.md`](single-hart-runtime-r5-review-summary.md));
it is exact-target validated and responsible-human accepted on
2026-07-30. R6 implementation work is authorized under the master-plan R6
row by the recorded `proceed to implement R6 exact` and `proceed with all r6
implementation work` instructions, and the
[bounded R6 plan](single-hart-runtime-r6-plan.md) is accepted at original exact
target `609867fdad75279c0913022909efd65c4a838909` and at corrected exact
target `75269f058ae578b0a76a113d6c05c0aaceeac8ec` as of 2026-07-30, and D-15
resumed under the already-recorded implementation authorization. Narrow
[Plan revision R6-B](single-hart-runtime-r6-plan.md#plan-revision-r6-b-d-15-image-layout-and-trace-retention)
is accepted at exact target `6d6464c6c937abccd59df932006c1049fd79fac6` as of
2026-07-30 (see its
[R6-B plan revision review and acceptance record](single-hart-runtime-r6-plan-r6b-review-summary.md)),
so R6 integration and evidence work resumed with every pinned value
re-derived at the exact implementation commit; that work is now complete,
fully checked, and committed at exact implementation target
`7ba3649f03cf13b65df33020e345d361cce2993a` (parent and initial implementation
`9ed5ad7069b6067f03e1923c09937fe218240a59`), recorded in the
[R6 adversarial-image evidence](single-hart-runtime-r6-evidence.md), and
accepted on 2026-08-05 as recorded in the
[R6 review and acceptance record](single-hart-runtime-r6-review-summary.md).
R7 is authorized under
[the bounded R7 plan](single-hart-runtime-r7-plan.md), which is accepted at
exact target `18c43596d308052cfad67edc6e2cb8f543f75600`, with Plan revision
R7-A accepted at exact target `0605028220e3795d99393156d0bfb7d6a7d631a4`. Its
package is
accepted at exact implementation target
`9bf22913d67e9b72286813cd5f7993a9ad3857a8` as of 2026-08-05, over superseded
first candidate `95639afb0ab57959a32d055f7b7f9bdb474fe762`, and root
integration is applied within
the accepted six-constant enumeration. The combined K3 core-validation plan
is accepted at exact target
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`; non-privileged H0
implementation was separately authorized, and Plan revision R8-A is accepted
at exact target `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`. Plan revision
R8-C is accepted at exact target
`f47ae60266a467ca1a7704fd9a50b140e0f31bb0`, and exact bounded H0/R8-C target
`1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` is accepted as of
2026-09-17 but remains blocked and not exit-ready. H1-H4 were dropped on
2026-10-08 without ever being authorized (section 2.14), the later K3 board
runs are B-series diagnostic bring-up evidence (section 2.15), and
publication remains blocked.
R3 acceptance
itself does not authorize tagging, pushing, public release, hardware claims,
R6 plan acceptance (recorded separately on 2026-07-30), or any later
behavior.

### 2.10 R4 trap and context

Status: accepted on 2026-07-29 at exact target
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52`; implementation parent
`6e5c55c59e94bbaba136269c784db28ec1b53f54` and decision-support follow-up
`ec7be2f146a851e7608e77eb2875076e66aab2e6` remain distinct.

Deliver the exact 320-byte monitor-owned frame; import only exact accepted R3
management state; classify the fixed denied protected-private load and private
VS event; preserve the complete frame while advancing only the validated
return PC; restore only the same management binding; and fail terminally on
every unexpected path. Require GCC/Clang host tests, semantic image checks,
six bounded QEMU runs, deterministic report/evidence integrity, and locked
tool/Make controls.

User benefit: a reviewable two-exit trap/context boundary before switching,
protected entry, adversarial runtime images, or proof work.

Gate: evidence is recorded in
[`single-hart-runtime-r4-evidence.md`](single-hart-runtime-r4-evidence.md).
It is QEMU-only functional evidence, not hardware validation, a
protected-entry result, R5 authorization, or an exact-byte/formal proof.

### 2.11 R5 checked switching

Status: plan accepted at exact commit
`fecae6b62a507bdbb93d211262197a31f5422316` on 2026-07-30; implementation
separately authorized under that accepted plan and accepted on 2026-07-30 at
exact target `165f4d001a2b59b582b397bdea79ec4826168fdb` over parent
`9312c1355a23d411e3bdafb2183be342683a8ab9`: `./be r5-check`,
`./be r4-check`, and `make check` each passed first-try from separate fresh
detached worktrees at that target, an independent
core/runtime review found no significant issue, and the recorded status is
`r5_acceptance=accepted`.

Deliver one fixed management→protected→management scenario: validate the
pending target-root binding, write the selected HGATP, perform the required
local fence, restore management state, re-enter VS, and demonstrate the
fixed shared-page/private-page access outcomes across six bounded QEMU runs
(three GCC, three Clang), with GCC/Clang host tests, semantic image checks,
and a deterministic report/evidence bundle under locked tool/Make controls.

User benefit: a reviewable, bounded checked-switch mechanism before
adversarial runtime images or proof work, without importing Linux, service,
device, policy, capability, TE, or multicore behavior.

Gate: evidence is recorded in
[`single-hart-runtime-r5-evidence.md`](single-hart-runtime-r5-evidence.md).
It is QEMU-only functional evidence produced from the exact accepted
target, not hardware validation, formal proof/refinement, R6 plan
acceptance (recorded separately on 2026-07-30), or any acceptance beyond that
exact commit.

### 2.12 R6 adversarial images

Status: implementation work authorized under the master-plan R6 row by the
recorded `proceed to implement R6 exact` and `proceed with all r6
implementation work` instructions of 2026-07-30. The bounded plan
[`single-hart-runtime-r6-plan.md`](single-hart-runtime-r6-plan.md) was
**accepted** at exact target `609867fdad75279c0913022909efd65c4a838909` on
2026-07-30, so both gates are satisfied. R6 implementation started **locally**
under that accepted plan and was at that point **neither reviewed, accepted,
nor complete**. Dynamic fixture D-15 exposed a defect in that original accepted
plan, corrected narrowly by Plan revision R6-A. Its
[review and acceptance record](single-hart-runtime-r6-plan-review-summary.md)
records both original decisions and the post-acceptance discovery, and the
corrected plan target — exact commit
`75269f058ae578b0a76a113d6c05c0aaceeac8ec`
(parent `4bff41764cf8ec9275e771cd3c1ce124961da93a`) — was **accepted on
2026-07-30**, with a
[plan revision review and acceptance record](single-hart-runtime-r6-plan-revision-review-summary.md)
that retains no corrected-placement build or QEMU evidence. **D-15 may
resume** under the already-recorded implementation authorization; a future R6
implementation requires its own exact-commit review and separate acceptance.
Resumed D-15 work then exposed two bookkeeping defects in that accepted
corrected plan — a false `.monitor.text` layout claim and a raw-trace
retention rule that cannot fit the plan's own 512 MiB bound — so narrow
[Plan revision R6-B](single-hart-runtime-r6-plan.md#plan-revision-r6-b-d-15-image-layout-and-trace-retention)
was **accepted at exact target `6d6464c6c937abccd59df932006c1049fd79fac6`**
(parent `4d6c3c9b0899c7a30b2150ff0d4067369ccef774`) on 2026-07-30, and its
[R6-B plan revision review and acceptance record](single-hart-runtime-r6-plan-r6b-review-summary.md)
records that decision; R6 integration and evidence work may resume under the
already-recorded implementation authorization, with every pinned value
re-derived from a checked run at the exact implementation commit. That
integration and evidence work is now complete, fully checked, and committed at
exact implementation target `7ba3649f03cf13b65df33020e345d361cce2993a` (parent
and initial implementation `9ed5ad7069b6067f03e1923c09937fe218240a59`, base
`4012d794e769fd4029b11f6f45e366ed0ef117f5`), and its decision-neutral
[R6 implementation review packet](single-hart-runtime-r6-review-summary.md)
presents that exact target for a decision, records none, and is itself
decision support rather than implementation.

Deliver a finite single-defect adversarial fixture catalogue over the
byte-immutable accepted R5 target: static-rejection fixtures for malformed
image, layout, instruction, publication, fence, and binding defects that must
be rejected before QEMU, and dynamic fail-closed fixtures for unexpected
traps/events and denied accesses that terminate through the accepted monitor
failure and SBI shutdown path. The plan adds no production surface under
`include/`, `virt/`, or `arch/`. It authorizes one tightly bounded refresh of
six predecessor acceptance-pin constants in `tests/r1/check-acceptance.sh`,
`tests/r3/check-accepted-content.mjs`, and
`tests/r4/check-accepted-content.mjs`, matching the accepted R5 precedent, so
that the required root `Makefile`, `be`, and `scripts/check-be.sh` integration
does not regress R1-R5 acceptance status; no accepted mechanism byte changes.

User benefit: bounded evidence that the accepted mechanism rejects or fails
closed on defective inputs, without claiming universal containment of
malicious guests or any hardware behavior for a genuinely skipped fence.

Gate: satisfied. The responsible human accepted exact R6 implementation
target `7ba3649f03cf13b65df33020e345d361cce2993a` on 2026-08-05. Hardware
validation and formal verification remain `NOT RUN`; that acceptance did not
itself authorize publication or a successor.

### 2.13 R7 proof and evidence

Status: separately authorized on 2026-08-05 by the responsible-human
instruction `once complete, commit and push, then commence R7`. The bounded
plan [`single-hart-runtime-r7-plan.md`](single-hart-runtime-r7-plan.md) is
accepted at exact target `18c43596d308052cfad67edc6e2cb8f543f75600`. The
`tests/r7/` package is complete, committed, and **responsible-human accepted
at exact implementation target `9bf22913d67e9b72286813cd5f7993a9ad3857a8`** on
2026-08-05 (immediate
parent and superseded first candidate
`95639afb0ab57959a32d055f7b7f9bdb474fe762`), after exact-target validation in
two independent fresh detached worktrees. Plan
revision R7-A, which enumerates exactly six authorized predecessor
acceptance-pin refreshes, is accepted at exact target
`0605028220e3795d99393156d0bfb7d6a7d631a4` as of 2026-08-05, so root
integration is applied within that enumeration with every constant re-derived
at the exact prospective content and no seventh acceptance update;
results are recorded in
[`single-hart-runtime-r7-evidence.md`](single-hart-runtime-r7-evidence.md),
and the exact-target decision is carried by the
[`R7 review and acceptance record`](single-hart-runtime-r7-review-summary.md).
The accepted target's own machinery is unchanged, so its
`r7_acceptance=not-reviewed` and `r7_accepted_commit=none` fields remain
pre-decision exact-target evidence.

Deliver a test-only exact-byte adaptation over enumerated privileged-wrapper
symbols in both pinned R5 images, a bounded RV64/Rocq model, a generated fixed
configuration trace, an explicit claim and cut-point ledger, evaluator,
reports, documentation, and a hash-covered reproducibility bundle. Change no
accepted runtime source or R0-R6 mechanism byte.

User benefit: a precise account of which fixed-profile properties are
machine-checked from exact linked bytes, which finite configuration facts are
checked, and which C, tool, firmware, emulation, and hardware boundaries
remain trusted or `NOT RUN`.

Gate: satisfied. The exact R7 plan commit, the exact commit carrying Plan
revision R7-A, and the exact implementation target
`9bf22913d67e9b72286813cd5f7993a9ad3857a8` are each separately
responsible-human accepted, the last on 2026-08-05. Acceptance covers that
exact commit and its bounded claim boundary only; hardware validation, C
refinement, and whole-system verification remain `NOT RUN` or not claimed, and
public push, tag,
publication, and release remain blocked. The combined K3 core-validation plan
is accepted at exact target
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`, and non-privileged H0
implementation was separately authorized. Plan revision R8-A is accepted at
exact target `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`; Plan revision R8-C
is accepted at exact target `f47ae60266a467ca1a7704fd9a50b140e0f31bb0`;
and exact bounded H0/R8-C target
`1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` is accepted as of
2026-09-17. It remains blocked and not exit-ready, and R8 produced no
hardware result. H1-H4 were dropped on 2026-10-08 (section 2.14).

### 2.14 R8 K3 core validation

Status: dropped on 2026-10-08 (form answer `r8=drop`), like KVM0, with the
records kept as history. The accepted plan chain (plan `7d0f0cbf`, R8-A
`8fa9d672`, R8-C `f47ae602`), the accepted H0/R8-C target
`1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` (accepted 2026-09-17, still
`BLOCKED-NOT-READY` with `r8_h0_exit=not-met`), and the R8-ALM1-A plan
text (accepted 2026-09-29) all remain accepted history. H1-H4 were never
authorized or run. An MVP plan may recreate a formal K3 evidence package if
one is needed. The rest of this section is retained history.

History: responsible-human direction on 2026-08-07 authorized R8 planning and
selected the combined K3 core-validation direction. The
[`single-hart-runtime-r8-plan.md`](single-hart-runtime-r8-plan.md) is
responsible-human accepted at exact target
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` on 2026-08-07;
the separate instruction `Authorize R8 implementation under accepted plan
7d0f0cbf…; proceed with R8-H0` authorizes only non-privileged H0 work. H0
was paused because local unaccepted work exposed a documentation-support path
and exact-candidate identity defect.
[Plan revision R8-A](single-hart-runtime-r8-plan.md#plan-revision-r8-a-h0-documentation-boundary-and-candidate-identity)
is responsible-human accepted at exact target
`8fa9d672cfcfb81ab68d9ed9553a5af48b884932` on 2026-08-07. Its immutable
target retains the proposed/paused pre-decision fields, while the
[R8-A review and acceptance record](single-hart-runtime-r8-plan-r8a-review-summary.md)
carries the decision. Acceptance retains the existing H0 authorization and
unpauses work only after the acceptance-record commit, whose full SHA is the
required implementation base; every candidate value must be freshly
re-derived. The
[R8 plan review and acceptance record](single-hart-runtime-r8-plan-review-summary.md)
carries both decisions.

[Plan revision R8-C](single-hart-runtime-r8-plan.md#plan-revision-r8-c-content-based-retired-parent-scan)
is responsible-human accepted at exact target
`f47ae60266a467ca1a7704fd9a50b140e0f31bb0` over parent
`fc6795b03b5f68849fe5ef882d7e2cae77ab4e90` as of 2026-09-17. The
[R8-C review and acceptance record](single-hart-runtime-r8-plan-r8c-review-summary.md)
carries the exact decision while the immutable target retains
`r8_plan_revision_r8c=proposed-not-reviewed` as pre-decision history.
Acceptance covered the plan for a content-based retired-parent scan correction
and exact three-path regression boundary.

The responsible human then accepted exact bounded non-privileged H0/R8-C
target `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` over parent
`d18b1c9c6ca8a0f2285f820ec960258620ae4b50` on 2026-09-17. The
[H0/R8-C review and acceptance record](single-hart-runtime-r8-h0-review-summary.md)
carries that exact decision and the 2026-09-24 confirmation that the existing
instruction/record is genuine. The target's exact R8-C paths are
`pathfinder/Makefile`,
`pathfinder/tests/check-source-policy-regression.mjs`, and
`pathfinder/tests/check-source-policy.sh`.

Deliver an ordered single-hart H0-H4 program:

1. freeze one exact K3 X100 board, firmware, boot, tool, capture, memory,
   feature, and claim profile without privileged implementation;
2. characterize the real H-extension, CSR/WARL, optional-state, PMP/Smepmp,
   AIA/Sstc, cache, debug, and external-master boundary without VS entry;
3. only after separate gates, execute the fixed two-domain synthetic
   management-to-protected-to-management scenario through an additive K3
   platform/profile boundary;
4. compare canonical QEMU and K3 access, fault, root-switch, and saved-state
   semantics under exact ratified required/permitted-field rules; and
5. retain a core-design consequence ledger, deterministic report, bounded
   evidence bundle, and exact-target review packet.

The accepted R0-R7 source and mechanism bytes remain immutable. Any need to
change an accepted architecture-neutral mechanism, widen the event surface,
save previously unmodeled optional state, activate another hart, or add a
device/DMA path is a stop requiring a separately reviewed plan revision.

User benefit: real-hardware evidence and explicit design feedback for the
small core before OS support, without treating one board as production
validation or importing Linux, multicore execution, devices, policy, or a
broader proof claim.

Gate: closed by the 2026-10-08 drop. At the drop, exact plan, R8-A, R8-C,
and exact H0/R8-C target acceptance were satisfied at their cited
boundaries, and the accepted target remained blocked and not exit-ready
with 147 rows, 118 `UNKNOWN`, 80 H0 blockers, `BLOCKED-NOT-READY`, and
`r8_h0_exit=not-met`. No COM260-informed H0 successor and no R8-H1 or later
privileged work was ever authorized, and R8 retained no hardware
measurement.

The separate
[R8-ALM1 active-line maintenance plan](single-hart-runtime-r8-active-line-maintenance-plan.md)
now carries Plan revision `R8-ALM1-A` and is accepted as plan text only at
exact target `95cce2f692543da67054ec2d6061eb08a4061253` as of 2026-09-29.
The target's `proposed-not-reviewed` and `not-authorized` fields remain frozen
pre-decision content. The plan remains limited to restoring active-line
host-only `r8-check` operability. It is not part of the H0-H4 package graph
and does not change accepted target `1999ee70...`. Its future implementation
base is intentionally unknown until a later acceptance-record/current-line
commit exists and a separate exact instruction names that full SHA, exact
relation, and complete plan inventory. Its
[original decision-neutral review packet](single-hart-runtime-r8-active-line-maintenance-plan-review-summary.md)
at exact commit `255aa176923581bf9248bfce5bc94217ff5577a8` remains immutable
history for original target `6bb3349b...`; it recommended the two corrections
now incorporated by R8-ALM1-A. The
[current R8-ALM1-A review and acceptance record](single-hart-runtime-r8-active-line-maintenance-plan-r8alm1a-review-summary.md)
records the exact revised target, both resolved findings, no significant open
plan defect, packet commit `788b0b6752b706ece8dc51dc2c0c5dca3e56376f`,
and responsible-human instruction `accept`. Acceptance authorizes no
implementation and transfers no H0 evidence or readiness.

### 2.15 K3 bring-up sprint (B0-B7)

Status: complete through B7. Each milestone was separately authorized, and
its exact result commit separately responsible-human accepted, between
2026-10-06 and 2026-10-09. On 2026-10-06 the responsible human decoupled B0
from KVM0 and redefined the series, superseding the earlier meanings
"B0 / `BE-K3-L0BOOT` gated on KVM0" and "B1 / `BE-K3-VS2SMOKE`". Each
milestone is one self-contained directory under `bringup/k3-bN/`, built and
tested with `make -C bringup/k3-bN check` and kept outside the root
`Makefile`, `be`, and `scripts/check-be.sh`.

Accepted milestones:

1. **B0:** an HS boot image (entry, stack/BSS, SBI DBCN, terminal SRST);
   the boot marker `BE-K3-L0BOOT PASS` reproduced in 3 of 3 kexec runs.
   Accepted 2026-10-06 at `bb8fd210758f88640817b5ea8010fe0654e626f3`
   ([record](k3-b0-result-review-summary.md)).
2. **B1:** the accepted R4 image, which re-executes the R3 prelude, ported
   to K3; all ten accepted markers in 3 of 3 runs. Accepted 2026-10-06 at
   `b44c3c6b502d2883e95f53c642f407b577a18829`
   ([record](k3-b1-result-review-summary.md)).
3. **B2:** the accepted R5 checked switch ported to K3; all 22 accepted
   markers in 4 of 4 runs (three GCC, one Clang). Accepted 2026-10-06 at
   `898af4e02fd36744a93b0eef99bc159955409d25`
   ([record](k3-b2-result-review-summary.md)).
4. **B3:** the B2 image booted from U-Boot `booti` through a small
   position-independent shim; 4 of 4 runs. Accepted 2026-10-06 at
   `9b4860a049646d8878a31ecea8957e95b045550f`
   ([record](k3-b3-result-review-summary.md)).
5. **B4:** the accepted R6 catalogue and R7 bounded proof re-derived for
   the K3 images, in host tests, QEMU, and Rocq only. Accepted 2026-10-07
   at `135b1d3ae4def25691472bba0fa0179aa509d532`
   ([record](k3-b4-result-review-summary.md)).
6. **Accepted-tool fixes:** fixes to the accepted R7 extractor and the
   R3/R4/R5 image checkers, with unit tests and the matching acceptance-pin
   refresh. Accepted 2026-10-07 at
   `c60896e35cb2ddb8d8662c973aa46d4b5d0d8ef2`
   ([record](accepted-tool-fixes-review-summary.md)).
7. **B5:** the first real guest, a tiny bare-metal VS guest with a bounded
   B5 guest SBI subset and the Sstc timer, under the
   [B5 plan](k3-b5-plan.md) accepted at
   `c3f8ef518850b55341cfd4ee0876b7f9ecf33859`; 4 of 4 runs through U-Boot
   `booti`. Accepted 2026-10-07 at
   `829562395bf14fedbeea0beb82b30da15ec5f7cf`
   ([record](k3-b5-result-review-summary.md)).
8. **B6:** an unmodified uniprocessor upstream Linux `v7.2` guest under a
   B6-owned G-stage over 64 MiB, under the [B6 plan](k3-b6-plan.md)
   accepted at `e34ef378b6279300ba5f3aeb8b6102941b432454`. The guest
   reached its init and powered off in 5 of 5 runs: three GCC and one
   Clang through kexec, and one GCC through U-Boot `booti`. Accepted
   2026-10-08 at `e20c55df57551244eab47e0eff59d4c71fe75d20` (instruction
   `accept e20c55`; [record](k3-b6-result-review-summary.md)).
9. **B7:** two copies of the B6 guest interleaved on hart 0, each in its
   own 64 MiB window under its own G-stage root and VMID, switched
   round-robin on a trapped `wfi` and an HS timer slice, under the
   [B7 plan](k3-b7-plan.md) accepted at
   `026974fb619295482b93a7ae8cffdc4f552825ea`. Both guests powered off in
   4 of 4 kexec runs, three GCC and one Clang, with identical counts.
   Accepted 2026-10-09 at `7b6b846bf453bacf4c67d986f87c61fdc092e2ee`
   (instruction `accept 7b6b84, commit and push`;
   [record](k3-b7-result-review-summary.md)).

Every board run loaded RAM only, through Linux `kexec_load` from the
running Fedora host or U-Boot YMODEM `loady` and `booti`, with output-only
serial capture and a human reset or power-off after each run, because
OpenSBI 1.6 SRST shutdown halts this board without powering it off. The board-safety rules
forbid any persistent firmware, U-Boot environment, flash, or
boot-configuration change.

User benefit: Beryllium's accepted boot, entry, and switch paths, then a
bare-metal guest, an unmodified upstream Linux guest, and two such guests
sharing one hart, running on one real K3 board, with each claim bounded
to its exact result.

Gate: satisfied for B0-B7 at their exact accepted results. The board runs
are diagnostic bring-up evidence for one board, not hardware validation or
qualification, and acceptance adds no formal-verification claim; the B6
and B7 monitor layers have no proof. B7 acceptance started no successor.
On 2026-10-13 a separate direction fast-forwarded the development branch
to the B7 branch tip, carrying B6, the re-baseline, and B7, and the
responsible human pushed it to the private `origin`; on 2026-10-16 a form
answer authorized fast-forwarding it again, with the later status
records, and pushing it. Each of these needs separate direction: any
further merge into it; the MVP milestones; shared pages, channels, and
denial tests; SMP and devices; root
integration; and the LiteBox investigation. Development-kernel/BSP
selection stays `UNDECIDED` and is not a gate for the planned sequence.

### 2.16 Next sequence: B7, S1-S3

Status: step 3, B7, S1, and S2 are complete and accepted. S1 was
authorized on 2026-10-16 (`authorize S1, proceed`), and its revised
[synthesis](he-to-be-synthesis.md) was accepted on 2026-10-18 at exact
commit `fd670dcd` (`0fbca0fd` superseded). The S2 plan was accepted on
2026-10-19 at `5ce7827f`, and [security model v1](security-model-v1.md)
on 2026-10-22 at exact commit `0e3eec8b`. S3 was directed on 2026-10-22
(`merge & push, start S3`), and its [MVP plan](mvp-plan.md), revision 1,
was accepted on 2026-10-23 at exact commit `93967fba`
(`accept 93967fba`; `06c35f48` superseded).
Form answer
`step3=proceed` authorized only step 3, the docs-only roadmap re-baseline,
which is accepted at exact target
`ecad45d8eb371218d6f9a0965b330fa5043ea273` as of 2026-10-08 (instruction
`accept ecad45`). B7's plan was accepted on 2026-10-08, and its exact
result commit `7b6b846bf453bacf4c67d986f87c61fdc092e2ee` on 2026-10-09
(instruction `accept 7b6b84, commit and push`). Each later step needs its
own plan and/or acceptance.

1. **Step 3, roadmap re-baseline (docs only):** drop KVM0 and R8 H1-H4,
   with their records kept as history; make the B-series the K3 path; make
   the He-to-Be synthesis depend on B-series evidence; and list the steps
   below. Exit: one docs commit for acceptance.
2. **B7, two Linux guests** (plan accepted 2026-10-08 at
   `026974fb619295482b93a7ae8cffdc4f552825ea`; see
   [`k3-b7-plan.md`](k3-b7-plan.md)): two copies of the B6 guest (pinned Linux
   `v7.2`, uniprocessor, no devices), each with its own 64 MiB window and
   G-stage. Per-guest vCPU state is saved and restored. Hart 0 switches
   between the guests round-robin when a guest idles (its `wfi` traps, with
   `hstatus.VTW` set) and on an HS timer slice through Sstc `stimecmp`, the
   monitor's first interrupt of its own. Each guest's console output has
   its own prefix. Userland is small programs built with Linux's own
   `tools/include/nolibc`, which supports riscv at `v7.2`, from the
   already-pinned tree, so there are no new external inputs. A static
   BusyBox and musl userland comes later, for interactive demos; it would
   need console input, which B6's SBI subset refuses. Exit: both guests run
   interleaved and power off, in QEMU and then in 3 GCC and 1 Clang kexec
   runs on K3. Status: complete and accepted. On 2026-10-08 all four
   RAM-only COM260 kexec runs passed with identical counts; they are
   diagnostic bring-up evidence for one board, and their records are in
   `bringup/k3-b7/results/20261008-com260/`. Exact result commit
   `7b6b846bf453bacf4c67d986f87c61fdc092e2ee` is accepted as of 2026-10-09
   (instruction `accept 7b6b84, commit and push`); see the
   [B7 result review and acceptance record](k3-b7-result-review-summary.md).
3. **S1, He-to-Be synthesis (docs):** classify each relevant Helium lesson
   as adopt, adapt, reject, or defer against the B0-B7 evidence. Sources:
   [`pathfinder-comparison.md`](pathfinder-comparison.md), the TE PoC
   evidence, and current `../helium-te-poc` read at one exact commit. S1
   can run alongside B7. Exit: one planning doc for acceptance. Status:
   authorized 2026-10-16; the revised document accepted 2026-10-18 at
   `fd670dcd` (RP-1; `0fbca0fd` superseded).
4. **S2, security model v1 (docs, plus model changes if needed):** one
   document containing (1) objects, invariants, the threat model, and the
   trusted computing base; (2) the policy specification: a central,
   declarative policy in the Type Enforcement family (types or labels,
   object classes, permissions, rules) with deterministic and total
   semantics, default deny, and explicit conflict resolution; (3) the
   analyses the [policy proof targets](#formal-assurance-split-after-selection)
   name: unreachable, contradictory, over-broad, and non-revocable
   authority; information flow modulo the declared channels; and authority
   non-amplification; (4) the relation from the policy to the canonical
   manifest (compile or validate), restoring the
   [offline pipeline](#selected-static-system-description-split) as a
   goal, with the Rocq configuration as its intended consumer; (5) the
   capability trigger and the runtime-check trigger, evaluated against the
   platform's use cases under Model 0.1 plan revision M01-A; (6) the
   authority ceiling for the dynamic management case
   ([policy invariant](#policy-invariant-retained-during-evaluation)); and
   (7) which of Model 0.2's seam, fixtures, or proofs change, if any. The
   specification language form is S2's choice. Exit: one doc for
   acceptance. This definition is work package RP-3 of the accepted
   [S1 and TE-trigger revision plan](s1-te-trigger-revision-plan.md),
   accepted on 2026-10-18 at exact commit `1ac7080f` (instruction
   `I accept RP-1 RP-2 RP-3`); the prior definition read "objects;
   authority (a sealed static manifest with ownership plus explicit
   channels); invariants; threat model; TCB; and whether the platform's
   use cases fire the capability or TE triggers". Status: plan accepted
   2026-10-19 at `5ce7827f`; [security model v1](security-model-v1.md)
   accepted 2026-10-22 at `0e3eec8b` (instruction `accept 0e3eec8b`).
5. **S3, MVP plan:** the initial security-research-platform release:
   scope, non-goals, milestones, evaluation harness, evidence claims, and
   release path. Exit: one plan for acceptance. Status: directed
   2026-10-22; [plan](mvp-plan.md) revision 1 accepted 2026-10-23 at
   `93967fba` (`accept 93967fba`; `06c35f48` superseded), with Q1 to Q12
   at their defaults; it authorizes writing M0's bounded plan only.

The first MVP milestone is M0, the MVP line, the multi-hart substrate, and
the evaluation harness, under the accepted S3 MVP plan (`93967fba`); the
Helium TE PoC scenario on two Linux guests, each on its own hart, is M1: a
writer and a reader share one page (writer read-write, reader read-only),
private memory is denied, and the monitor injects faults and logs the
denials. Reproducing that scenario does not select TE. The accepted MVP
plan selects M0 to M4 and takes the static part of milestone 4's
concurrency model (one domain per hart, a dedicated control hart) into
MVP 1.0; milestones 3 to 10 below otherwise wait for their own plans
after MVP 1.0.

User benefit: a short, evidence-led path from one Linux guest to the first
security-research MVP milestone, with the Helium lessons and the security
model recorded before the MVP scope is set.

Gate: step 3, B7, S1, S2, and S3 are accepted; each MVP milestone needs
its own plan and acceptance; the [M0 plan](mvp-m0-plan.md) was accepted
on 2026-10-23 at `4d129808`; M0 implementation stopped at M0-3 by stop
condition 3 and resumed under Plan revision M0-A; M0-4 is complete at
`19c3d455`, with the evaluator passing under Plan revision M0-B
(directed 2026-10-24); M0-5 needs the responsible human at the board. The
accepted S3 MVP plan decides no development-kernel/BSP selection (D2),
does not recreate KVM0 (D6), and does not recreate a formal K3 evidence
package (D4).

### 3. One protected domain on a lead ISA

Status: deferred; the accepted S3 MVP plan (`93967fba`) takes its smallest
static form into MVP 1.0 as M2 and leaves the dynamic management
vocabulary, notifications, and lifecycle here; not authorized.

Deliver hypervisor-first boot, a Linux management domain, minimal protected-domain vCPU entry, stage-2 isolation, a single-hart proof configuration, shared memory, notifications, hostile-domain containment, and an immutable core-held measurement of the monitor, manifest, and protected-domain image/configuration.

User benefit: a practical secret-holding, integrity-monitoring, or exploit-containment substrate with local measured identity. Remote attestation is not yet claimed.

Gate: review TCB size, exit surface, failure behavior, language evidence, and protection of the local measurement state.

### 4. RISC-V multicore and extended hardware validation

Deliver the serialized multicore model, its refinement to atomic control
operations, K3 hardware validation, and RISC-V common conformance tests.
The accepted S3 MVP plan (`93967fba`) takes the static part of this
milestone's concurrency model, one domain per hart under static ownership
with a dedicated control hart, into MVP 1.0 and leaves the dynamic part
(the global control lock, the dynamic mapping protocol, migration,
overcommit, and multicore hardware validation) here; not authorized.

User benefit: credible multicore and hardware-backed RISC-V semantics.

Gate: re-establish the selected isolation properties for serialized multicore operation and identify which interfaces are truly portable.

### 5. External I/O service domain

Deliver IOMMU-enforced ownership, one restartable service, a minimal queue/grant protocol, and malicious-service tests.

User benefit: a realistic workload without drivers in the core.

Gate: prove DMA containment, reset safety, and bounded core parsing.

### 6. First-class policy substrate

If a concrete use case fires a capability or mandatory-policy trigger, deliver
the approved extension, measured static policy, offline tooling, revocation
where applicable, and audit records.

User benefit: reproducible authorization and information-flow research with an explicit comparison trail.

Gate: verify that the selected default policy is understandable, usable, and no larger than justified.

### 7. Measured launch, attestation, and integrity research

Deliver measured core/configuration/policy, architecture-specific evidence adapters, and a runtime integrity-monitor experiment.

User benefit: cryptographically verifiable remote evidence that the intended monitor, domain image, configuration, and policy are running.

Gate: document roots of trust, replay/update behavior, and vendor assumptions.

### 8. Conditional portability expansion

If justified by pathfinder evidence and RISC-V maturity, add an Arm backend to test the portability boundary. Intel and AMD remain optional later research.

User benefit: evidence about which core mechanisms generalize beyond RISC-V.

Gate: decide whether further architecture expansion provides enough benefit to justify its maintenance and proof cost.

### 9. Assurance release

Deliver selected machine-checked invariants, fully open binary correspondence for the proof-bearing subset, bounded verification, reproducible fuzzing/sanitizer evidence, and an explicit assurance case.

User benefit: a credible high-assurance target with bounded claims.

Gate: this milestone is complete only if open binary correspondence passes; otherwise issue only a clearly labeled pre-assurance release and continue the open-tooling side project.

### 10. Upstream or foundation-grade proposal

Deliver an RFC design and patch series or stable integration specification, tests, documentation, maintainership, security process, and governance.

User benefit: a maintainable community project rather than a research code drop.

Gate: land a new subsystem, land bounded Linux interfaces for the independent monitor, or retain a separately governed project with documented interoperability.

## Community strategy

1. Publish the problem statement before a large implementation.
2. Engage linux-riscv, KVM/RISC-V, OpenSBI, RISC-V virtualization/security groups, IOMMU, Linux security, and relevant architecture maintainers first.
3. Use LPC, Linux Security Summit, KVM Forum, RISC-V events, FOSDEM, embedded, automotive, space, and high-assurance venues; engage Arm communities only when portability work becomes concrete.
4. Submit small RFC series with tests and documentation.
5. Record decisions and objections publicly.
6. State the unsolved research gap without dismissing existing projects.
7. Recruit concrete research users before proposing generic infrastructure.
8. Retain a separate-project path if kernel maintainers accept interfaces but not the core.

### October 2026 informal checkpoint

- Linux Plumbers Conference: 5-7 October 2026, Prague.
- Linux Security Summit Europe: 8 October 2026, Prague.

Target artifacts:

- Reproducible pathfinder demo.
- Two-page problem statement.
- TCB and exit-surface report.
- Threat model and non-goals.
- K3 security-hardware matrix.
- Policy-option comparison.
- Open questions about upstream placement and proof tooling.

Use BoF, microconference/unconference opportunities where available and hallway discussions. Do not make the checkpoint depend on a formal accepted talk.

## Future research sidebars

The following non-authorizing pages preserve candidate questions for later
bounded plans:

- [High-assurance standards and open formal tooling](sidebar-high-assurance-standards.md)
- [Rust for future VS components](sidebar-rust-vs-components.md)
- [Optional Linux VBS-equivalence](sidebar-lvbs-equivalence.md)
- [CHERI, protected VS services, and dynamic authority caches](sidebar-dynamic-authority-caches.md)
- [LiteBox and minimal VS runtimes](sidebar-minimal-vs-runtimes.md)

The accepted fixed runtime implementation does not select any of them or
authorize a later implementation stage.

## Immediate decision gates

1. Preserve the accepted distinction between proposed configuration,
   canonical sealed state, and derived enforcement.
2. Do not evaluate policy frameworks, compose security models, or select a
   protected service outside an accepted S2 or S3 scope. Under S2's revised
   definition (RP-3, accepted 2026-10-18), the policy specification, its
   analyses, and its relation to the canonical manifest are inside S2's
   scope; the specification language form, any runtime mechanism, and the
   protected service are selected only there or in S3.
3. Step 3 is accepted at `ecad45d8`, the B7 plan at `026974fb`, the B7
   result at `7b6b846b`, S1 at `fd670dcd`, the S2 plan at `5ce7827f`, and
   security model v1 at `0e3eec8b`. S3 was directed on 2026-10-22, and its
   plan, revision 1, was accepted on 2026-10-23 at `93967fba`
   (`06c35f48` superseded); it authorizes writing M0's bounded plan only,
   and no MVP milestone is implemented until
   that milestone's own plan is accepted.
4. Keep the dropped KVM0 and R8 records, including exact accepted H0/R8-C
   target `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4`, as history.
   Recreating KVM0 or a formal K3 evidence package needs a new decision,
   for example in the S3 MVP plan.
5. Gather community feedback on the core boundary and Linux integration form.
6. Approve a separate later plan before a second guest (B7), guest SBI
   expansion, services, multicore, devices, DMA, or policy integration.
