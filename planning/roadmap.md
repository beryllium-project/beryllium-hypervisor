<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium roadmap

**Status date:** 2026-11-26. This is the maintained one-page placemat
for the public development line: where the project stands, what comes
next, and the gates. The linked plans, evidence records, and decision
records are authoritative, with the signed commits of this repository's
`main`. Updating this page accepts and authorizes nothing.

> **Reading note.** From MVP 1.0's release (2026-11-08) to 2026-11-23
> this page stood as it was at the release's source commit
> (2026-11-05). It is maintained on the development line from
> 2026-11-23. The release itself is described by `README.md` and
> `RELEASE.md` at the repository's root. The page as it stood at the
> source commit, with its full account of the K3 bring-up and of MVP
> 1.0's milestones, is in Git history: `git show
> mvp-1.0:planning/roadmap.md`.

> **Current position (2026-11-26):**
>
> - **MVP 1.0 is published** (2026-11-08): the tag `mvp-1.0`, on the
>   release commit `0b2a4367`. Its milestones M0 to M10 are complete,
>   and its release candidate 4 is the release. It is a
>   security-research demonstrator: Linux guests, each on its own hart
>   beside a control hart, under static hart ownership, in QEMU and on
>   one K3 COM260 board. Its claim, with its required limit, is
>   `mvp/docs/claim.md`.
> - **Since 2026-11-10 this repository's `main` is the development
>   line.** Each commit is prepared unsigned, and joins `main` only when
>   the responsible human signs it off and pushes it; his sign-off of a
>   plan's proposing commit is that plan's acceptance. The CHERI
>   platform work joined `main` that day (`a0d0b78b`).
> - **MVP 2.0 has begun**, in the order that Plan revision S3-D of the
>   [MVP plan](mvp-plan.md) set (2026-11-10, `b332f658`): first M11, a
>   physical boundary under the monitor, with M12, the supervisor-domain
>   lane, beside it; then the seven steps that Plan revision S3-C named
>   for MVP 2.0.
> - **M11 is complete.** Each hart that the monitor uses is confined by
>   a physical access profile that M-mode programs, under a firmware
>   build of the project's own. Under emulation the M11 candidate passed
>   its nine gates, and that result was accepted on 2026-11-18
>   (`cf79de89`). On one K3 COM260 board, booted from a microSD card
>   with the board's NOR untouched, the monitor's images then ran with
>   the boundary built off and with it on, and that result was accepted
>   on 2026-11-23 (`489efd38`). The claim for the boundary, with its
>   required limit, is `mvp/docs/claim-boundary.md`. The board's runs
>   are diagnostic evidence from one board, and are not hardware
>   validation.
> - **M12**, the supervisor-domain lane (its [plan](mvp-m12-plan.md)
>   accepted 2026-11-15, `5ea5243a`), has ended every step that its plan
>   and its revision 1 set. Its revision 2 (2026-11-21, `87f13d56`)
>   plans a step for each answer from the people whose work it builds
>   on, and none starts before its answer. Nothing goes to another
>   project but through the responsible human.
> - **M13, the first of those seven steps, is complete**: the
>   board's device facts (its IOMMU and IOPMPs, its interrupts, its reset
>   paths, and which device belongs to whom), found before any device is
>   given to a VS domain. Its [plan](mvp-m13-plan.md) was accepted on
>   2026-11-23 (`ac3bd40f`). Its [record](k3-com260-devices.md) holds
>   the facts, each with its source: the vendor's documents and sources,
>   the published images, the board's own Linux, and one probe session
>   on the board. It is diagnostic, and it is evidence for no claim. Its
>   [result](mvp-m13-result.md) was accepted on 2026-11-25
>   (`d6d5492c`). The record shows no mechanism on this board that
>   bounds a device's memory accesses; it does not say what the
>   hardware can do, and the results of two of its probes are held.
> - **M14, the second step, is complete**: the device and DMA object
>   model. Its [plan](mvp-m14-plan.md) was accepted on 2026-11-25
>   (`d0ec2aee`). The model is
>   [Revision 5 of the security model](security-model-v1.md#revision-5-2026-11-25-the-device-and-dma-object-model),
>   accepted on 2026-11-26 (`5206c07a`). It says what a device is to
>   the security model: the objects, who has authority over each, what
>   a device's own memory accesses may reach, how its interrupts reach
>   its owner, and what any device path has to keep. It is
>   specification, asserted of no image. It chooses no device and no
>   mechanism, builds nothing, and had no session on the board. Its
>   [result](mvp-m14-result.md), accepted on 2026-11-26 (`15f884f7`),
>   reads the model against M13's record and against the emulated
>   machine that the project's gates run on.
> - **M15, the third step, has its plan**: the first device path, under
>   emulation. One assignment unit is to be given to one VS domain, the
>   I/O service VS domain, which is to serve one other VS domain. It is
>   to run on the emulated machine that the gates run on, with an IOMMU
>   model of the emulator's in the path of the devices' requests, and
>   it is to be built against Revision 5. It plans nothing on the
>   board: by M14's result, M13's record alone leaves no unit with a
>   bus master there that could be given to a VS domain. Its
>   [plan](mvp-m15-plan.md) is proposed by the commit that adds that
>   page, and is accepted when that commit is on this `main` with the
>   responsible human's sign-off. It asks for three decisions, in
>   order: the plan, a design, and the result. It chooses no device
>   and no mechanism: the design does, and no code is committed before
>   the design is accepted.
> - **Next:** once the plan is accepted, its work package M15-2: a
>   characterization of the emulated machine's IOMMU models and PCI
>   functions, in scratch, and then the design, for a decision of its
>   own.

## At a glance

```text
Helium pathfinders; Models 0.1 and 0.2 .............. accepted (2026-07)
R0-R7: the single-hart runtime in QEMU .............. accepted (2026-07-27 to 2026-08-05)
B0-B7: K3 bring-up .................................. accepted (2026-10-06 to 2026-10-09)
S1 synthesis; S2 security model v1; S3 MVP plan ..... accepted (2026-10-18 to 2026-10-23)
MVP 1.0: M0 to M10 .................................. accepted (2026-10-26 to 2026-11-05)
MVP 1.0 release ..................................... published 2026-11-08 (tag mvp-1.0, 0b2a4367)
The CHERI platform, into main ....................... merged 2026-11-10 (a0d0b78b)
MVP plan revision S3-D: MVP 2.0's order ............. accepted 2026-11-10 (b332f658)
Security model v1, Part 1 Revision 4 ................ accepted 2026-11-11 (0b14b3b6)
MVP plan revision S3-E: the board's firmware ........ accepted 2026-11-16 (8f07d612)
M11: the physical boundary under the monitor ........ complete: emulation 2026-11-18 (cf79de89); one board 2026-11-23 (489efd38)
M12: the supervisor-domain lane ..................... its steps ended; revision 2 (2026-11-21) waits on answers
M13: the board's device facts ....................... complete: plan 2026-11-23 (ac3bd40f); result 2026-11-25 (d6d5492c)
M14: the device and DMA object model ................ complete: plan 2026-11-25 (d0ec2aee); model 2026-11-26 (5206c07a); result 2026-11-26 (15f884f7)
M15: the first device path, under emulation ......... plan proposed 2026-11-26, accepted by its commit's sign-off  <- YOU ARE HERE
MVP 2.0 steps (4) to (7), then its last step ........ planned; each needs its own plan
MVP 3.0 and MVP 4.0 ................................. named in the MVP plan; not planned
```

## Executive position

Beryllium is a small RISC-V HS-mode isolation engine for security
research, with rich services outside its core. Its authority model is
immutable ownership with explicit channels. Security model v1 states
the system's security properties as a central, declarative,
default-deny policy in the Type Enforcement family, with enforcement
derived from it; software capabilities and a runtime TE check stay
trigger-gated. The direction is C-first, Rocq-primary, RISC-V-first,
and open tooling only.

MVP 1.0, published on 2026-11-08, is a security-research demonstrator
on three of the COM260's eight X100 harts, under static ownership.
MVP 2.0 began with the responsible human's direction to assume a breach
inside the monitor: M11 put a physical boundary, enforced by M-mode,
under the monitor's own code. M13 then found the board's device facts,
before the device and DMA object model and the first device path are
planned; its result says what those steps can rely on, and what they
cannot. M14 then wrote that object model, as Revision 5 of the
security model, before any device path is planned; its result reads
the model against M13's record and against the emulated machine. M15
is to build the first device path against that model, and starts
under emulation: on the board, M13's record alone leaves no unit with
a bus master that could be given to a VS domain.

## Milestone status

Short IDs name exact accepted commits. Up to MVP 1.0's release they are
commits of the project's private development history, which each linked
record names in full; from the release on, they are commits of this
repository's `main`.

| Phase | Milestone | Status | Record |
| --- | --- | --- | --- |
| Foundations | Helium pathfinders: five variants, including the fixed TE PoC | Complete. The comparison selected ownership plus explicit channels, with capabilities and TE trigger-gated. Current Helium source is `../helium-te-poc`. | [Comparison](pathfinder-comparison.md) |
| Foundations | Architecture Model 0.1 | Accepted 2026-07-22 | [Model 0.1](architecture-model-0.1.md) |
| Foundations | Architecture Model 0.2 | Accepted 2026-07-24, `e58adc3e` | [Model 0.2](architecture-model-0.2.md) |
| Foundations | Bounded single-hart runtime plan | Accepted 2026-07-25, `a81edbc3` | [Plan](single-hart-runtime-plan.md) |
| QEMU runtime | R0 fixed-profile freeze | Accepted 2026-07-27, `64a88b15` | [Freeze](single-hart-runtime-r0-freeze.md) |
| QEMU runtime | R1 pure-C mechanism | Accepted 2026-07-28, `a6e0bb17` | [Record](single-hart-runtime-r1-review-summary.md) |
| QEMU runtime | R2 Sv39x4 G-stage backend | Accepted 2026-07-28, `6e1cb579` | [Record](single-hart-runtime-r2-review-summary.md) |
| QEMU runtime | R3 boot and first VS entry | Accepted 2026-07-29, `6fb65b28` | [Record](single-hart-runtime-r3-review-summary.md) |
| QEMU runtime | R4 traps and context | Accepted 2026-07-29, `0783dfc6` | [Record](single-hart-runtime-r4-review-summary.md) |
| QEMU runtime | R5 checked domain switch | Accepted 2026-07-30, `165f4d00` | [Record](single-hart-runtime-r5-review-summary.md) |
| QEMU runtime | R6 adversarial images | Accepted 2026-08-05, `7ba3649f`: 47 entries, 64 QEMU runs | [Record](single-hart-runtime-r6-review-summary.md) |
| QEMU runtime | R7 bounded exact-byte proof | Accepted 2026-08-05, `9bf22913`: bounded, not whole-system | [Record](single-hart-runtime-r7-review-summary.md) |
| K3 bring-up | B0 boot marker | Accepted 2026-10-06, `bb8fd210`: 3 of 3 kexec runs | [Record](k3-b0-result-review-summary.md) |
| K3 bring-up | B1 R3/R4 first VS entry and exits | Accepted 2026-10-06, `b44c3c6b`: 3 of 3 | [Record](k3-b1-result-review-summary.md) |
| K3 bring-up | B2 R5 checked switch | Accepted 2026-10-06, `898af4e0`: 4 of 4 | [Record](k3-b2-result-review-summary.md) |
| K3 bring-up | B3 U-Boot `booti` shim | Accepted 2026-10-06, `9b4860a0`: 4 of 4 | [Record](k3-b3-result-review-summary.md) |
| K3 bring-up | B4 R6 and R7 re-derived for the K3 images | Accepted 2026-10-07, `135b1d3a`: host, QEMU, and Rocq only | [Record](k3-b4-result-review-summary.md) |
| K3 bring-up | Accepted-tool fixes | Accepted 2026-10-07, `c60896e3` | [Record](accepted-tool-fixes-review-summary.md) |
| K3 bring-up | B5 first real guest: bare-metal, guest SBI subset, Sstc timer | Accepted 2026-10-07, `82956239`: 4 of 4 | [Plan](k3-b5-plan.md), [record](k3-b5-result-review-summary.md) |
| K3 bring-up | B6 uniprocessor Linux `v7.2` guest | Accepted 2026-10-08, `e20c55df`: 5 of 5 (4 kexec, 1 U-Boot) | [Plan](k3-b6-plan.md), [record](k3-b6-result-review-summary.md) |
| K3 bring-up | B7 two Linux guests on one hart | Accepted 2026-10-09, `7b6b846b`: 4 of 4 kexec runs | [Plan](k3-b7-plan.md), [record](k3-b7-result-review-summary.md) |
| Dropped | R8 formal K3 core validation | Dropped 2026-10-08; see [dropped workstreams](#dropped-workstreams) | [Plan](single-hart-runtime-r8-plan.md), [H0 record](single-hart-runtime-r8-h0-review-summary.md) |
| Dropped | KVM0 Linux/KVM-on-K3 qualification | Dropped 2026-10-08; see [dropped workstreams](#dropped-workstreams) | [Plan](k3-kvm0-plan.md), [K0-S record](k3-kvm0-k0s-review-summary.md) |
| Re-baseline | Step 3 roadmap re-baseline | Accepted 2026-10-08, `ecad45d8` | This page's Git history |
| Synthesis and model | S1: the Helium-to-Beryllium synthesis | Accepted 2026-10-18, `fd670dcd` | [Synthesis](he-to-be-synthesis.md), [record](s1-te-trigger-revision-review-summary.md) |
| Synthesis and model | S2: security model v1 | Accepted 2026-10-22, `0e3eec8b` | [Model](security-model-v1.md), [record](security-model-v1-review-summary.md) |
| Synthesis and model | S3: the MVP plan | Revision 1 accepted 2026-10-23, `93967fba`; Plan revisions S3-A to S3-C, 2026-10-29 to 2026-11-01 | [Plan](mvp-plan.md), [record](mvp-plan-review-summary.md) |
| MVP 1.0 | M0: the MVP line, the multi-hart substrate, and the harness | Accepted 2026-10-26, `b2669725` | [Plan](mvp-m0-plan.md), [record](mvp-m0-result-review-summary.md) |
| MVP 1.0 | M1: the TE scenario on two Linux guests, each on its own hart | Accepted 2026-10-27, `ff84533c` | [Plan](mvp-m1-plan.md), [record](mvp-m1-result-review-summary.md) |
| MVP 1.0 | M2: a static protected VS domain beside an untrusted Linux | Accepted 2026-10-28, `18d552bc` | [Plan](mvp-m2-plan.md), [record](mvp-m2-result-review-summary.md) |
| MVP 1.0 | M3: the policy layer and the hart binding in the model | Accepted 2026-10-28, `b0a0f352` | [Plan](mvp-m3-plan.md), [record](mvp-m3-result-review-summary.md) |
| MVP 1.0 | M4: release candidate 1 | Accepted 2026-10-29, `c5df0cfa` | [Plan](mvp-m4-plan.md), [record](mvp-m4-result-review-summary.md) |
| MVP 1.0 | M5: release candidate 2, booted from system reset | Accepted 2026-10-30, `3867c66c` | [Plan](mvp-m5-plan.md), [record](mvp-m5-result-review-summary.md) |
| MVP 1.0 | M6: release candidate 3, the MVP core profile | Accepted 2026-10-31, `89ef04e9` | [Plan](mvp-m6-plan.md), [record](mvp-m6-result-review-summary.md) |
| MVP 1.0 | M7: interactive guests | Accepted 2026-11-02, `e1a6395e` | [Plan](mvp-m7-plan.md), [record](mvp-m7-result-review-summary.md) |
| MVP 1.0 | M8: the first verification plan | Accepted 2026-11-04, `12b0e71b`: inconclusive under its decision rule; no C-level contract proof, and the claim unchanged | [Plan](mvp-m8-plan.md), [record](mvp-m8-result-review-summary.md) |
| MVP 1.0 | M9: measurement | Accepted 2026-11-03, `892b68c8` | [Plan](mvp-m9-plan.md), [record](mvp-m9-result-review-summary.md) |
| MVP 1.0 | M10: release candidate 4 | Accepted 2026-11-05, `d70a8535` | [Plan](mvp-m10-plan.md), [record](mvp-m10-result-review-summary.md) |
| Release | MVP 1.0 | Published 2026-11-08: the tag `mvp-1.0`, on `0b2a4367` | `RELEASE.md` at the repository's root |
| CHERI | The CHERI platform, a build variant of the monitor for CHERI v0.9.3 under emulation | Merged into `main` 2026-11-10, `a0d0b78b` | [CHERI platform](cheri-platform.md) |
| MVP 2.0 | Plan revision S3-D: M11 first, M12 beside it, and the terminology rule | Accepted 2026-11-10, `b332f658` | [MVP plan](mvp-plan.md) |
| MVP 2.0 | Security model v1, Part 1 Revision 4: the attacker after a hart's activation | Accepted 2026-11-11, `0b14b3b6` | [Security model](security-model-v1.md) |
| MVP 2.0 | M11: the physical boundary under the monitor | Plan accepted 2026-11-11, `77eabce5`; result under emulation accepted 2026-11-18, `cf79de89`; result on one board accepted 2026-11-23, `489efd38`: complete | [Plan](mvp-m11-plan.md), [board addendum](mvp-m11-board-addendum.md), [evidence](mvp-m11-evidence.md) |
| MVP 2.0 | Plan revision S3-E: the board-firmware amendment | Accepted 2026-11-16, `8f07d612` | [MVP plan](mvp-plan.md) |
| MVP 2.0 | M12: the supervisor-domain lane | Plan accepted 2026-11-15, `5ea5243a`; M12-1 to M12-4, M12-7.1 to M12-7.6, and M12-5 (narrowed to its firmware half) ended by 2026-11-21; revision 2 accepted 2026-11-21, `87f13d56`: its steps wait on answers | [Plan](mvp-m12-plan.md), [revision 1](mvp-m12-plan-revision-1.md), [revision 2](mvp-m12-plan-revision-2.md) |
| MVP 2.0 | M13: the board's device facts | Plan accepted 2026-11-23, `ac3bd40f`; result accepted 2026-11-25, `d6d5492c`: complete | [Plan](mvp-m13-plan.md), [record](k3-com260-devices.md), [result](mvp-m13-result.md) |
| MVP 2.0 | M14: the device and DMA object model | Plan accepted 2026-11-25, `d0ec2aee`; the model, security model v1 Revision 5, accepted 2026-11-26, `5206c07a`; result accepted 2026-11-26, `15f884f7`: complete | [Plan](mvp-m14-plan.md), [model](security-model-v1.md#revision-5-2026-11-25-the-device-and-dma-object-model), [result](mvp-m14-result.md) |
| MVP 2.0 | M15: the first device path, under emulation | Plan proposed 2026-11-26, and accepted by the sign-off of its commit on `main` | [Plan](mvp-m15-plan.md) |

## Planned sequence

MVP 2.0's focus is "finalize core architecture and formalize" (Plan
revision S3-C). Plan revision S3-D put M11 first, with M12 beside it;
the seven steps that S3-C named for MVP 2.0 then follow in their order,
each a precondition of the next. Each step needs its own plan, accepted
at its own commit, and none is authorized until then.

| Order | Step | Scope | State |
| --- | --- | --- | --- |
| First | M11: the physical boundary | Each hart that the monitor uses confined by a physical access profile that M-mode programs from a description built offline; the other harts parked | Complete (2026-11-23) |
| Beside M11 | M12: the supervisor-domain lane | The memory protection tables of the RISC-V Supervisor Domains Access Protection specification, under emulation and outside the claim: questions for its authors, directed tests, its model in the Sail RISC-V model, and review of others' series | Every step of its plan and its revision 1 has ended; revision 2's steps wait on answers |
| (1) | M13: the board's device facts | The IOMMU and the IOPMPs, interrupts, reset, and device ownership of the K3 COM260 board, from documents, sources, the board's own Linux, and probe images | Complete (2026-11-25) |
| (2) | M14: the device and DMA object model | What a device is to the security model, as an additive revision of it, with the synthesis's policy questions H06 ("authority without a mapping") and H07 (when a finer type has security meaning) answered where devices and the service VS domain make them concrete. It chooses no device and no mechanism | Complete (2026-11-26): its [result](mvp-m14-result.md) |
| (3) | M15: one static pass-through device path and the I/O service VS domain | The implementation plan's milestone 5, under emulation first, and without the restart, which is step (5)'s. One assignment unit is to be given to one VS domain for a whole boot, with an IOMMU model in the path of its bus masters' requests; each invariant of Revision 5 is to be shown, or what cannot be shown named in the limit. A device path on the board needs a plan of its own afterwards | [Plan](mvp-m15-plan.md) proposed 2026-11-26, and accepted by the sign-off of its commit |
| (4) | The serialized mapping and invalidation protocol | The implementation plan's milestone 4, which the device path and dynamic management both need, with its proof targets | Planned |
| (5) | Dynamic management | Restart, notifications, and a management vocabulary, after the capability and runtime-check triggers (H08, H09) are evaluated for it | Planned |
| (6) | The first non-Linux VS domain | Chosen by a bake-off of runtimes, LiteBox among them, after the service ABI is demonstrated | Planned |
| (7) | Attestation over MVP 1.0's measurement log | A simulated root of trust, after the log's event semantics, the verifier's trust boundary, key custody, freshness, and replay rules are fixed | Planned |
| Last | The compatibility analysis | The identity, ownership, measurement, and ABI boundaries of memory protection tables and of CoVE, against MVP 2.0's architecture; it builds on M12 | Planned |

MVP 2.0 also holds Model 0.3, the generalized model; the synthesis's
scaling and residual-risk analyses (H57, H58); sealed storage and
anti-rollback as features of the simulated root of trust; new object
classes as additive revisions of the security model; and the K3
Mini-ITX as a second platform record. Its "formalize" means stage 2 of
the [project snapshot](project-snapshot-mvp-1.0-rc2.md)'s verification
stages for the proof-bearing subset's decision functions, and stage 3's
cut-point contracts for the trap vector and the resume tail.

## Dropped workstreams

On 2026-10-08 the responsible human dropped two workstreams. Their records
stay as history, exactly as recorded, and a new plan may recreate either.
The B-series results do not stand in for the evidence these workstreams
planned; they are diagnostic bring-up evidence.

- **KVM0**, native Linux/KVM qualification on K3 (packages K0-P to K0-R).
  It was parked on 2026-10-06, when B0 was decoupled from it, and dropped
  on 2026-10-08 by the instruction `we will also drop the kvm0 workstream,
  we can create again if needed`. Accepted at their own boundaries: Plan
  revision K0-A `5227266c` (2026-09-25), the K0-I offline tooling
  `abd092a1` (2026-09-26), the K0-S preparation/status target `c6570558`
  (2026-09-29), and the K0-SC, K0-SC1, and K0-SC1-A plan texts. The
  corrected K0-SC1-B target `13463e4f` and its packet `f2135556` remain
  unaccepted. K0-X and K0-R never ran.
- **R8**, formal K3 core validation (stages H0-H4). It was dropped on
  2026-10-08 by the form answer `r8=drop`. Accepted history: plan
  `7d0f0cbf`, Plan revisions R8-A `8fa9d672` and R8-C `f47ae602`, the
  H0/R8-C target `1999ee70` (2026-09-17, `BLOCKED-NOT-READY`,
  `r8_h0_exit=not-met`), and the R8-ALM1-A plan text (2026-09-29). H1-H4
  were never authorized or run. The accepted MVP plan does not recreate a
  formal K3 evidence package (D4); M0's platform record takes its place
  as diagnostic evidence.

## Other workstreams

- **The CHERI platform:** a build variant of the MVP's monitor for
  CHERI v0.9.3, with CHERI Linux guests, run under emulation and
  checked beside the plain variant, whose images it leaves unchanged.
  It joined `main` on 2026-11-10 (`a0d0b78b`), and its check is one of
  M11's gates. It is outside MVP 1.0's claim. Its page is
  [the CHERI platform](cheri-platform.md); CHERI on hardware stays an
  MVP 3.0 track.
- **As they stood at the release's source commit (2026-11-05), and not
  maintained here:** documentation reproducibility (the exact 24-path
  target `7cf4c4a1`, accepted on 2026-09-30 for one environment only)
  and evidence retention (its first phase's read-only inventory complete;
  its second phase blocked). Both belonged to the private development
  line.

## Gates and boundaries

- **The development line:** this repository's `main`. Each commit is
  prepared unsigned and joins `main` only when the responsible human
  signs it off and pushes it; his sign-off of a plan's proposing commit
  is that plan's acceptance. Automation pushes nothing, tags nothing,
  and publishes nothing, and a publication gate checks every push to a
  public remote.
- **Each step's authority:** a milestone plan, accepted at its own
  commit, authorizes its own work packages, or those of them that it
  names, and nothing else. Its stop conditions return the work to the
  responsible human. Its soft limits stop the work for re-evaluation,
  and never cut it.
- **The board:** the MVP plan's board policy: Plan revision S3-A's
  items 1 to 7, S3-C's item 8, and S3-E's items 9 to 13. Boots are from
  system reset; kexec is not used; U-Boot's saved environment changes
  only within a recorded session, and is restored at its end; no step of
  the project's own writes the NOR beyond that session's recorded
  `saveenv`; and a microSD card session runs only under a milestone
  plan, on the responsible human's word, with him present. Every board
  session waits for his word that the board is free.
- **Claims:** MVP 1.0's claim and its required limit are
  `mvp/docs/claim.md`, and the boundary's are
  `mvp/docs/claim-boundary.md`; the claim ledger beside them maps each
  claim to its method and its evidence. Board results are diagnostic
  evidence from one board, never hardware validation.
- **Work bound for another project** (M12): written only with AI tools
  that can be disclosed by name, under the destination's licence and
  contribution policy. Every offer is the responsible human's, in his
  own name.
- **Development kernel and BSP:** not selected, and not needed so far:
  the guests see no device, and use the pinned upstream Linux as a test
  input. The [M15 plan](mvp-m15-plan.md) keeps that Linux for the first
  device path, under emulation, with the options that the device
  needs. A device path on the board would reopen the question.
- **Root integration:** `bringup/` and `tests/unit` stay outside the
  root `Makefile`, `be`, and `scripts/check-be.sh`, which carry
  predecessor acceptance pins.

## Open engineering risks

| Risk | Current evidence | Required response |
| --- | --- | --- |
| Board results read as hardware validation | B0-B7, MVP 1.0's campaigns, and M11's two sittings ran on one COM260, under the vendor's firmware or a firmware build of the project's own. | Call them diagnostic evidence from one board, and scope every claim to the exact board, firmware, tools, and procedure, as the claim pages' required limits do. |
| Devices' memory accesses | The K3's documents describe nine IOPMPs and an IOMMU; no device tree that this board boots with declares either. M13's record shows no mechanism on this board that bounds a device's memory accesses: as booted the IOMMU is in `Off` mode and three PCIe ports bypass it, and no IOPMP's state is established (the results of two probes are held). | Revision 5 of the security model (M14) says what has to bound them, without naming a mechanism, and gives no VS domain a device whose memory accesses nothing confines (I30 (d)). The [M15 plan](mvp-m15-plan.md), step (3)'s, starts the first device path under emulation, where an IOMMU model can be put in the path of a device's requests, and plans nothing on this board: by [M14's result](mvp-m14-result.md), M13's record alone leaves no unit with a bus master there that could be given to a VS domain ([M13's result](mvp-m13-result.md), section 3, has what the record shows). A device path on the board needs a plan of its own. |
| The firmware below the boundary | The boundary rests on M-mode code: OpenSBI at a pinned commit, with a small series of the project's own additions. | Keep the firmware pinned and its additions small and reviewed, and name it in every board result (the M11 plan and its board addendum). |
| Open audit findings | Low-severity findings S5-S8 and S10 remain open; R4's 3 s QEMU budget fails on slow hosts. | Fix under separate direction (the MVP plan's D11). |
| The verifier's inputs | The verifier image's package closure can no longer be fetched whole from an empty cache (the MVP README's open item 133). | A source for the missing package in the fetch tool, under the responsible human's direction. |
| Generated-asset reproducibility | Browser, link, and static gates work; independent byte identity remains open. | Pin and compare generator inputs, or define a bounded semantic reproducibility claim. |
| Publication and provenance | The development line is public, and every commit on it carries the responsible human's sign-off. | Keep the publication gate on every push, and the AI-assistance disclosure (`mvp/docs/ai-assistance.md`) current. |

## Later phases

The project's longer-range milestones are the
[implementation plan](implementation-plan.md)'s milestones 3 to 10. The
MVP ladder (Plan revision S3-C, re-cut by S3-D) places them. MVP 1.0
took the static part of milestone 4 and measurement. MVP 2.0 takes the
device path (milestone 5), the serialized protocol (milestone 4),
dynamic management (milestone 3's dynamic part), and attestation. MVP
3.0 is a set of research tracks, each with its own trigger and hardware
precondition: memory protection tables and CoVE on hardware, CHERI, and
policy composition. MVP 4.0 is general guests, defined by a guest
profile that its plan fixes. Each rung, and each step in it, needs its
own plan.

| Phase | Goal | Key non-goal | Rung |
| --- | --- | --- | --- |
| One protected VS domain and OS boundary | A Linux management VS domain plus a protected VS domain; guest SBI, hypercall, notification, lifecycle, restart, failure, and measurement boundaries. | No general cloud/VMM product, broad guest SBI, or accidental stable UAPI. | MVP 1.0 took a static protected VS domain (M2); the dynamic part is MVP 2.0's step (5) |
| Serialized multicore | Static CPU ownership, per-core fast paths, and one bounded serialized lifecycle, ownership, and invalidation path. | No fine-grained locking, work stealing, or shared run queue. | MVP 1.0 took the static part; the protocol is MVP 2.0's step (4) |
| I/O service and DMA containment | One restartable service/device class with interrupt, reset, IOMMU/IOPMP, cache, and DMA ownership. | No generic device framework or whole-platform DMA claim. | MVP 2.0's steps (1) to (3); M13 is step (1), M14 is step (2), and M15 is step (3), which starts under emulation and builds no restart |
| Policy triggers | Capabilities only for delegation, attenuation, transfer, or revocation needs; a runtime TE check only for an independent mandatory denial. Under M01-A, the TE-family policy specification comes from S2 and is not trigger-gated. | No policy framework in the core or selection by preference. | Evaluated for dynamic management in MVP 2.0's step (5); policy composition is an MVP 3.0 track |
| Measured launch and attestation | Bind exact core, configuration, and VS-domain artifacts to explicit roots of trust and update/replay rules. | Measurement is not attestation. | Measurement in MVP 1.0 (M9); attestation is MVP 2.0's step (7) |
| Assurance and source-to-binary | Selected refinement, binary correspondence, coverage, traceability, and deployment crosswalks using open normative tools. | No claim of whole-system proof or certification without an evaluator. | MVP 1.0's first verification plan (M8); MVP 2.0's "formalize"; the rest with milestone 9 |
| Clean public migration | A new clean Beryllium repository with selected reviewed source and artifacts, then upstream or foundation disposition. | No direct publication of internal history or automated release approval. | Done for MVP 1.0 (published 2026-11-08, with fresh history); upstream or foundation disposition remains (milestone 10) |
| MVP core profile | Replace the fixed-profile prelude with the MVP's own configuration, validated, sealed, and derived at boot. | — | Retired by M6 (release candidate 3, 2026-10-31) |

Arm portability remains conditional.

## Status legend

| Mark | Meaning |
| --- | --- |
| **ACCEPTED** | Responsible-human decision applies to the cited exact boundary only. |
| **PLANNED** | In the sequence; not authorized until its own plan or decision is accepted. |
| **DROPPED** | Stopped by responsible-human direction; records stay as history; a new plan may recreate it. |
| **BLOCKED** | A required fact, gate, plan, or authorization is missing. |
| **NOT RUN** | The named execution or evidence does not exist. |
| **TRIGGER-GATED** | Consider only after a documented concrete need fires the stated trigger. |

**State discipline:** `accepted` means a human decision on one exact target;
`ready` means the named gate prerequisites are met; `authorized` means bounded
work may proceed; and `run` means execution evidence exists. These states are
independent, and none implies another.

```text
roadmap_status_date=2026-11-26
roadmap_maintained_on=the-public-development-line-from-2026-11-23
roadmap_earlier_version=git-show-mvp-1.0:planning/roadmap.md
mvp_1_0=published-2026-11-08;tag-mvp-1.0;release-commit-0b2a4367;milestones-M0-M10-accepted
development_line=main;each-commit-signed-off-and-pushed-by-the-responsible-human
cheri_platform=merged-into-main-2026-11-10-a0d0b78b;emulation-only;outside-the-claim
mvp_2_0_order=M11-first;M12-beside;then-S3-C-steps-1-to-7;then-the-compatibility-analysis
s3d=accepted-2026-11-10-b332f658
security_model_v1_revision_4=accepted-2026-11-11-0b14b3b6
s3e=accepted-2026-11-16-8f07d612
security_model_v1_revision_5=accepted-2026-11-26-5206c07a
m11=complete;plan-77eabce5;emulation-result-cf79de89-2026-11-18;board-result-489efd38-2026-11-23
m12=plan-5ea5243a-2026-11-15;steps-M12-1-to-M12-5-and-M12-7.1-to-M12-7.6-ended;revision-2-87f13d56-2026-11-21-waits-on-answers
m13=complete;plan-ac3bd40f-2026-11-23;result-d6d5492c-2026-11-25
m14=complete;plan-d0ec2aee-2026-11-25;model-security-model-v1-Revision-5-5206c07a-2026-11-26;result-15f884f7-2026-11-26;no-device-and-no-mechanism-chosen
m15=MVP-2.0-step-3;the-first-device-path;under-emulation;nothing-on-the-board;plan-proposed-2026-11-26-accepted-by-its-commit's-sign-off-on-main
next=M15-2-the-characterization-and-the-design-once-the-M15-plan-is-accepted
board_results=diagnostic-evidence-from-one-board;not-hardware-validation
kvm0=dropped-2026-10-08-records-retained
r8_h1_h4=dropped-2026-10-08-never-authorized
```

## Authoritative records

- Returning after time away: the root `README.md`, with its note on
  `main`; the [project orientation guide](project-orientation.md) and
  the dated [project snapshot](project-snapshot-mvp-1.0-rc2.md), both
  as they stood at the release's source commit
- Maintained definitions and disambiguations: [glossary](glossary.md)
- The MVP ladder, its milestones, and the board policy: the
  [MVP plan](mvp-plan.md), with its Plan revisions S3-A to S3-E
- MVP 2.0's plans and records: the [M11 plan](mvp-m11-plan.md), its
  [board addendum](mvp-m11-board-addendum.md), and its
  [evidence record](mvp-m11-evidence.md); the [M12 plan](mvp-m12-plan.md),
  with its revisions and its steps' records; the
  [M13 plan](mvp-m13-plan.md), its [record](k3-com260-devices.md), and
  its [result](mvp-m13-result.md); the [M14 plan](mvp-m14-plan.md)
  and its [result](mvp-m14-result.md); and the
  [M15 plan](mvp-m15-plan.md)
- MVP 1.0's plans, records, and evidence: the MVP 1.0 rows of
  [milestone status](#milestone-status); its release record,
  `RELEASE.md`
- The security model: [security model v1](security-model-v1.md), with
  its Revisions 1 to 5
- The claims: `mvp/docs/claim.md`, `mvp/docs/claim-boundary.md`, and
  the claim ledger beside them
- Longer-range sequencing and gates:
  [implementation plan](implementation-plan.md)
- Hardware feature inventory and dispositions:
  [RISC-V and K3 security hardware](riscv-security-hardware.md)
- The CHERI line: [the CHERI platform](cheri-platform.md) and
  [CHERI alignment](cheri-alignment.md)
- K3 bring-up plans and records: the B-series rows in
  [milestone status](#milestone-status). Each milestone's directory under
  `bringup/` holds its README, tools, and retained board records.
- Runtime R0-R7 scope:
  [bounded single-hart runtime plan](single-hart-runtime-plan.md)
- Pathfinder evidence and the selected authority baseline:
  [post-pathfinder comparison](pathfinder-comparison.md)
- Policy research inputs:
  [capability policy architecture](capability-policy-architecture.md),
  [supervisory security policy](supervisory-security-policy.md), and
  [isolation-engine policy research](isolation-engine-policy-research.md)
- Dropped workstreams, as history: [R8 plan](single-hart-runtime-r8-plan.md),
  [R8-H0 record](single-hart-runtime-r8-h0-review-summary.md),
  [KVM0 plan](k3-kvm0-plan.md), and
  [K0-S record](k3-kvm0-k0s-review-summary.md)
- Release, licence, and AI-assistance boundary:
  `LLM_POLICY_ALIGNMENT.md` and `mvp/docs/ai-assistance.md`
- The working sessions' handoff is not part of this repository
  ([note](HANDOFF.md)).

Markdown under `planning/` is authoritative. DOT is authoritative diagram
source. Generated HTML is a milestone and release artifact.
