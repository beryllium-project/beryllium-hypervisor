<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium project orientation

**Status date:** 2026-10-17. **Re-baseline base:** B6 acceptance record
`3acb99ab999d7296276396393b5bcafcdee9ed77`. This guide is a scan-first
re-entry aid for a responsible human returning after time away. It reports
the maintained decisions and gates but does not independently accept a
target, authorize implementation or execution, or replace the linked plans,
evidence, and review records.

## At a glance

```text
Foundations   Helium -> Model 0.1 -> Model 0.2 -> runtime plan
QEMU runtime  R0 -> R1 -> R2 -> R3 -> R4 -> R5 -> R6 -> R7
K3 bring-up   B0 -> B1 -> B2 -> B3 -> B4 -> B5 -> B6 -> B7
Re-baseline   step 3, docs only, accepted
Done          S1 He-to-Be synthesis, accepted at fd670dcd
              (with M01-A 95ef0f6c and the S2 definition 1ac7080f)
Done          S2 security model v1, accepted at 0e3eec8b
              (plan accepted at 5ce7827f)
Done          S3 MVP plan, revision 1, accepted at 93967fba
              (06c35f48 superseded)
Now           M0: MVP line, multi-hart substrate, harness
              (plan accepted at 4d129808;
              implementing)                  <- YOU ARE HERE
Then          M1 to M4: the TE PoC scenario on two Linux guests,
              each on its own hart; the protected domain; the
              policy layer in the model; the release candidate
Dropped       KVM0 and R8 H1-H4 (records kept as history)
```

> **YOU ARE HERE - S3, plan proposed:** R0-R7 and K3 bring-up
> milestones B0-B7 are accepted at their exact targets. The latest, B7, ran
> two copies of the B6 guest, an unmodified uniprocessor upstream Linux
> `v7.2` kernel, interleaved on hart 0, each in its own 64 MiB window under
> its own G-stage root and VMID. Both guests powered off in 4 of 4 RAM-only
> COM260 kexec runs, three GCC and one Clang. Exact result commit
> `7b6b846bf453bacf4c67d986f87c61fdc092e2ee` is accepted as of 2026-10-09
> (instruction `accept 7b6b84, commit and push`); see the
> [B7 result review and acceptance record](k3-b7-result-review-summary.md).
> On 2026-10-08 the responsible human dropped the KVM0 workstream, parked
> since 2026-10-06, with the instruction
> `we will also drop the kvm0 workstream, we can create again if needed`,
> and dropped R8 stages H1-H4 by form answer `r8=drop`. Their records stay
> as history. Form answer `step3=proceed` authorized step 3, this docs-only
> re-baseline, and its exact target
> `ecad45d8eb371218d6f9a0965b330fa5043ea273` is accepted as of
> 2026-10-08 (instruction `accept ecad45`). The bounded B7 plan was
> accepted at `026974fb` (instruction `accept 026974`). On 2026-10-16 the
> instruction `authorize S1, proceed` authorized S1; its
> [synthesis](he-to-be-synthesis.md), revised under the accepted
> [revision plan](s1-te-trigger-revision-plan.md) (`07541c59`), was accepted
> on 2026-10-18 at exact commit `fd670dcd54ff4f2c66349d377be914698b9dda3b`
> (`0fbca0fd` superseded), together with Model 0.1 plan revision M01-A at
> `95ef0f6c` and the revised S2 definition at `1ac7080f`, by the instruction
> `I accept RP-1 RP-2 RP-3` (see the
> [revision review summary](s1-te-trigger-revision-review-summary.md)). S1
> is complete, and the development branch was fast-forwarded to
> `0eb37570` and pushed (`fast-forward dev to 0eb37570 and push`). The
> [S2 plan](s2-security-model-plan.md) was accepted on 2026-10-19 at exact
> commit `5ce7827f` (instruction `accept 5ce782`; see its
> [review summary](s2-security-model-plan-review-summary.md)), with Q1
> answered A and Q2 to Q7 at their defaults. Under it,
> [security model v1](security-model-v1.md) was accepted on 2026-10-22 at
> exact commit `0e3eec8b` (instruction `accept 0e3eec8b`, with V1 to V4
> at their defaults; see its
> [review and acceptance record](security-model-v1-review-summary.md)),
> so S2 is complete. On 2026-10-22 the instruction
> `merge & push, start S3` fast-forwarded the development branch to
> `0096de3e` and pushed it, and directed S3: the [MVP plan](mvp-plan.md),
> revision 1, was accepted on 2026-10-23 at exact commit `93967fba`
> (`accept 93967fba`, Q1 to Q12 at their defaults; see its
> [review and acceptance record](mvp-plan-review-summary.md)), so S3 is
> complete. The revision of 2026-10-23 puts each domain on its own hart
> with a dedicated control hart, and `06c35f48` is superseded. The
> acceptance authorizes writing M0's bounded plan only; that
> [M0 plan](mvp-m0-plan.md) was accepted on 2026-10-23 at exact commit
> `4d129808` (`accept 4d129808, proceed with implementation using
> opus-5.5 model`; see its
> [review and acceptance record](mvp-m0-plan-review-summary.md)), and
> M0 implementation on `beryllium/mvp-m0` stopped at M0-3 by stop
> condition 3 (Clang's monitor text `0x7e0` over the accepted limit) and
> resumed under Plan revision M0-A on your direction of 2026-10-23; M0-1
> to M0-4 are complete at `19c3d455` (the evaluator passes under Plan
> revision M0-B, directed 2026-10-24 by `accept A`); the M0-5 board
> campaign needs you at the COM260.
> Board results are
> diagnostic bring-up evidence for one board, never hardware validation or
> qualification.

| Stage | Status | Meaning and boundary |
| --- | --- | --- |
| **Foundations** | Complete; accepted 2026-07-22 to 2026-07-25 | Five Helium pathfinders, Architecture Models 0.1 and 0.2, and the single-hart runtime plan. Ownership plus explicit channels is the selected baseline; capabilities and TE stay trigger-gated. |
| **R0-R7** | Accepted 2026-07-27 to 2026-08-05 | Fixed single-hart synthetic profile with host, QEMU, and bounded Rocq evidence. R7 is bounded, not whole-system. |
| **B0-B6** | Accepted 2026-10-06 to 2026-10-08 | K3 bring-up sprint under `bringup/k3-bN/`, from an HS boot marker to a uniprocessor Linux guest. Its board runs are diagnostic bring-up evidence for one COM260. |
| **Step 3** | Accepted 2026-10-08 at `ecad45d8` | Docs-only re-baseline: drop KVM0 and R8 H1-H4, make the B-series the K3 path, and list the planned steps. |
| **B7** | Plan accepted 2026-10-08 at `026974fb`; result accepted 2026-10-09 at `7b6b846b` (instruction `accept 7b6b84, commit and push`) | Two copies of the B6 guest, interleaved on hart 0; 4 of 4 RAM-only COM260 kexec runs, diagnostic bring-up evidence for one board. |
| **S1, S2, S3** | S1 authorized 2026-10-16, revised, and accepted 2026-10-18 at `fd670dcd` with M01-A (`95ef0f6c`) and the S2 definition (`1ac7080f`); S2 plan accepted 2026-10-19 at `5ce7827f` and security model v1 accepted 2026-10-22 at `0e3eec8b`; S3 directed 2026-10-22, its [MVP plan](mvp-plan.md) revision 1 accepted 2026-10-23 at `93967fba` (`06c35f48` superseded) | He-to-Be synthesis, security model v1, and the MVP plan. |
| **KVM0, R8 H1-H4** | Dropped 2026-10-08 | Records kept as history. KVM0 can be recreated if needed; an MVP plan may recreate a formal K3 evidence package. |

**State discipline:** `accepted` means a human decision on one exact target;
`ready` means the named gate prerequisites are met; `authorized` means bounded
work may proceed; and `run` means execution evidence exists. These states are
independent, and none implies another.

## Current position in one screen

| Question | Current answer |
| --- | --- |
| What is Beryllium? | Beryllium (`Be` / `be`) is this defensive-security project and the future RISC-V HS-mode isolation-engine direction. The active private repository is `beryllium-project/beryllium-hypervisor`; the root `./be` wrapper is its stable inspection interface. |
| What human identity should future Beryllium work use? | Preferred future Git authorship, review correspondence, and human DCO signoff identity: `James Morris <jmorris@namei.org>`. Source files added to this internal repository continue to use the existing `James Morris <jamorris@linux.microsoft.com>` copyright header required by the accepted plan and source-policy checks. A future clean repository may adopt the new address for source headers after policy review. |
| What is Helium? | Helium (`He` / `he`) is the completed bounded QEMU pathfinder, not the future hypervisor. The current Helium source of truth is the standalone sibling repository `../helium-te-poc`, ref `for-review`, at exact commit `f928aac5979b6166f3f68a76a9acf1fc916161d8` as inspected on 2026-10-08. Beryllium's `historical_he/*` refs and retained `pathfinder/` history are pre-fork or lost-history references and exact historical evidence only. |
| What is accepted? | Architecture Models 0.1 and 0.2; the fixed single-hart runtime plan; R0-R7 at their recorded exact boundaries; the B0-B7 results, the B5, B6, and B7 plans, and the accepted-tool fixes (see the [K3 bring-up path](#k3-bring-up-path)); and exact project-status documentation target `a9bb91df94f7e1df2b0e7f2d3ca057f6516ea511`, accepted on 2026-10-04 for its status text only ([record](k3-project-status-roadmap-review-summary.md)). The accepted records of the dropped workstreams stand as history. |
| What was dropped on 2026-10-08? | The KVM0 workstream and R8 stages H1-H4. Their records stay as history and gate nothing. KVM0 can be recreated if needed, and an MVP plan may recreate a formal K3 evidence package. H1-H4 and KVM0's K0-X/K0-R were never authorized or run. |
| What is the K3 path of record? | The B-series. On 2026-10-06 B0 was decoupled from KVM0 and the series redefined, which superseded the old meanings "B0 / `BE-K3-L0BOOT` gated on KVM0" and "B1 / `BE-K3-VS2SMOKE`". |
| What is authorized now? | M0 implementation under its accepted plan: the accepted [MVP plan](mvp-plan.md) (revision 1, `93967fba`, accepted 2026-10-23 by `accept 93967fba`; one hart per domain and a dedicated control hart; `06c35f48` superseded) selects M0 to M4; the [M0 plan](mvp-m0-plan.md), revision 2, was accepted on 2026-10-23 at `4d129808` (`accept 4d129808, proceed with implementation using opus-5.5 model`; `6e4b9d4a` and `d95b28e9` superseded) on `beryllium/mvp-m0-plan` (from the S3 acceptance record `1fb46419`, also the development-branch tip after the 2026-10-23 fast-forward and push), so work packages M0-1 to M0-6 may run on `beryllium/mvp-m0`, each stop condition returning to you; no MVP milestone result is accepted. S3 was directed on 2026-10-22 by `merge & push, start S3`. S2 is complete. The accepted [S2 plan](s2-security-model-plan.md) (`5ce7827f`, 2026-10-19, `accept 5ce782`) authorized writing `planning/security-model-v1.md` as work packages S2-1 to S2-7, and that [document](security-model-v1.md) was accepted on 2026-10-22 at `0e3eec8b` (`accept 0e3eec8b`), with no code, no `model/` change, and no push. S1 is complete. On 2026-10-16 the instruction `authorize S1, proceed` authorized S1, and its revised [synthesis](he-to-be-synthesis.md) was accepted on 2026-10-18 at `fd670dcd` (`0fbca0fd` superseded). On 2026-10-17 you requested a [project review](project-review-2026-10-17.md) after finding that the draft treats TE only as a runtime denial; on 2026-10-18 the instruction `approve 480d 07541` accepted it at `480dab72` (corrected after the research agents were re-run on `claude-fable-5.1` at your direction; `65fc52e0` superseded) and then the [revision plan](s1-te-trigger-revision-plan.md) at `07541c59`, whose three packages you accepted on 2026-10-18 with `I accept RP-1 RP-2 RP-3` (see the [revision review summary](s1-te-trigger-revision-review-summary.md)): RP-1, the revised S1, at `fd670dcd`; RP-2, Model 0.1 plan revision M01-A, at `95ef0f6c`; and RP-3, the revised S2 definition, at `1ac7080f`. B7 is complete: exact result commit `7b6b846bf453bacf4c67d986f87c61fdc092e2ee` is accepted as of 2026-10-09 (instruction `accept 7b6b84, commit and push`), as are its plan at `026974fb` (instruction `accept 026974`) and step 3 at `ecad45d8` (instruction `accept ecad45`). That instruction also authorized pushing the B6, re-baseline, and B7 branches to the private `origin` (see the branches row below). Each MVP milestone needs its own plan and acceptance. |
| What has run on K3? | B0-B3 and B5-B7 ran RAM-only on one COM260. Those runs are diagnostic bring-up evidence for one board, not hardware validation or qualification. B4 ran nothing on the board. |
| What is `NOT RUN`? | Hardware validation or qualification of Beryllium, B7, KVM0's K0-X/K0-R, and R8 H1-H4. |
| Is the development kernel/BSP a gate? | **No.** It stays `UNDECIDED` but no longer gates the planned sequence: the guests see no devices, and the guest kernel is an external test input. The S3 MVP plan may revisit it if a host or management Linux on K3, or device access, is needed. |
| What is the current project focus? | M0 implementation under its accepted [plan](mvp-m0-plan.md) (`4d129808`) and Plan revision M0-A (directed 2026-10-23 after stop condition 3), the first milestone under the accepted [MVP plan](mvp-plan.md) (S3, revision 1 at `93967fba`). S1, S2, and S3 are complete: S1 accepted at `fd670dcd`, and [security model v1](security-model-v1.md) at `0e3eec8b`. Maintain authoritative Markdown routinely; defer generated HTML and full Chromium rendering checks to milestones so documentation machinery does not displace security and technical work. |
| Where are the branches? | Development branch `beryllium/single-hart-runtime-r0` holds B0-B7, the accepted-tool fixes, and step 3. On 2026-10-09 the instruction `accept 7b6b84, commit and push` authorized pushing `beryllium/k3-b7-bringup`, through the B7 acceptance record, and `beryllium/k3-b6-bringup` (B6) and `beryllium/roadmap-rebaseline` (step 3), whose commits it contains, to the private `origin`; the B7 worker branches stay local. On 2026-10-13 the direction `proceed with these in fleet mode. fast-foward.` fast-forwarded the development branch from `3bc3ef04` to `80ef261ea77b26d1e4e2570157e44f6fcec731fb`, the B7 branch tip, and the responsible human pushed it and the B7 branch to the private `origin` (`push the beryllium backup`). On 2026-10-16 the form answers `fast_forward=ff-push` and `accepted_r8_branch=backup` authorized fast-forwarding the development branch to the B7 branch tip, through the commit that records the `PMR-090` owner return, and pushing both branches and `beryllium/r8-c-h0-pmr-081-v3` (the accepted R8 H0 target and its records) to the private `origin`. `PMR-090` retired superseded, unaccepted candidate `6e93461f`, which stays on its local branch and is never pushed. On 2026-10-18 the instruction `fast-forward dev to 0eb37570 and push` fast-forwarded the development branch from `56e36ae1` to `0eb37570`, the acceptance record of RP-1 to RP-3, and pushed it to the private `origin`; it now holds S1, the project review, the revision plan, M01-A, and the S2 definition, all accepted. On 2026-10-22 the instruction `merge & push, start S3` fast-forwarded the development branch from `0eb37570` to `0096de3e`, the acceptance record of security model v1, and pushed it to the private `origin`; it now also holds the accepted S2 plan and security model v1. The proposed S3 MVP plan is on local branch `beryllium/s3-mvp-plan`, from `0096de3e`, unpushed. |
| What documentation reproducibility decision is current? | Exact 24-path target `7cf4c4a1dff0b3f2dac2c692a2f1d2398ff6771e` is accepted for the selected Nimbus environment. Its packet and acceptance record remain on clean local unpushed side branch `beryllium/doc-repro-option-a-20260929` and are not integrated here. No cross-host/future-package guarantee or runtime/proof/hardware/publication authority follows; the retained OCI remains a single-copy risk. |
| What is the evidence-retention state? | Option A Phase 1 is complete. Phase 2 packet SHA-256 is `94a780ee271f23de1785fed03f5a14f89a713912f60047afd83e06d3bee0b106`, but no store exists and Phase 2 is blocked on independent secondary, key/recovery, index, lifecycle, and restore choices. |
| What remains blocked? | Everything not separately directed: S1-S3 work; the MVP and its first milestone; shared pages, channels, and denial tests; any further merge into the development branch; B-series root integration into `Makefile`, `be`, and `scripts/check-be.sh`; SMP, devices, DMA, and more guest RAM; the LiteBox investigation; Phase 2 evidence-retention choices; any push beyond the one authorized on 2026-10-09, tag, publication, release, migration, and upstream submission. |

The maintained [roadmap](roadmap.md) is the current-position placemat, and
the [glossary](glossary.md) owns definitions. Each B-series result record
owns its exact decision and claim boundary. The
[K3 bring-up path](#k3-bring-up-path) section points to the records of the
dropped workstreams.

Historical review packets may name the former private repository
`jamorris_microsoft/beryllium`, former remotes, or old absolute checkout
paths. Those are packet-time evidence, not current repository identity or
current commands. Use this guide and current `git` state for operational
inspection; do not reinterpret historical remote-containment claims.

## How the project pieces fit

```text
Helium pathfinders
  -> Architecture Model 0.1
  -> Architecture Model 0.2
  -> fixed single-hart runtime R0-R7 (QEMU)
  -> K3 bring-up sprint B0-B7 (COM260)
  -> planned: S1, S2, S3, then MVP milestones

Dropped 2026-10-08, records kept as history:
  KVM0 (K0-P -> K0-I -> K0-S -> K0-X -> K0-R)
  R8 H1-H4 (accepted plan chain and blocked H0 retained)
```

The B-series builds on accepted work instead of replacing it. B1 and B2
port the accepted R4 and R5 images to K3 with a counted substitution table
(`scripts/port.py` in `bringup/k3-b1/` and `bringup/k3-b2/`). B3 adds a
shim so U-Boot `booti` can load the B2 image, and B4 re-derives the
accepted R6 catalogue and R7 bounded proof for those K3 images. B5 and B6
add new monitor layers, guest SBI subsets, and guests under their own
accepted plans, and B7 runs two B6 guests under its own; the B6 and B7
monitor layers have no proof. Each milestone stays outside the root
`Makefile`, `be`, and `scripts/check-be.sh`. No B-series result is a KVM0
result or retained R8 evidence.

| Layer or package | Purpose | Current state and limit |
| --- | --- | --- |
| Helium | Five bounded pathfinder experiments, culminating in a fixed Type Enforcement review-and-test PoC | Completed in its own evidence universe. Current source and release status live in `../helium-te-poc`; no Helium result transfers to Beryllium or K3. |
| Model 0.1 | Static single-hart ownership/channel isolation contract | Accepted non-runtime model with host checks and bounded Rocq obligations; no runtime or hardware result. |
| Model 0.2 | Policy-neutral inventory -> proposal -> canonical sealed state -> derived enforcement boundary | Accepted non-runtime successor with host checks and bounded Rocq obligations; no C refinement, runtime, parser, stable encoding, or hardware claim. |
| R0-R2 | Freeze the fixed profile, validate/seal state, and construct concrete Sv39x4 roots | Accepted. Non-privileged host evidence only; no Beryllium QEMU before R3 and no hardware. |
| R3-R5 | Boot, first VS entry, bounded trap/context handling, and one checked management/protected round trip | Accepted bounded QEMU evidence under the fixed profile; not hardware, Linux, arbitrary guest, or production evidence. |
| R6 | Test-only adversarial-image catalogue over accepted R5 | Accepted; no production mechanism surface and no formal or hardware claim. |
| R7 | Exact linked-byte extraction and fixed-configuration Rocq evidence | Accepted bounded proof/evidence; not C refinement, source-to-binary correctness, whole-system verification, or hardware validation. |
| B0-B3 | B0's HS boot marker, K3 ports of the accepted R4 first-entry and R5 checked-switch images, then the B2 image through U-Boot `booti` | Accepted 2026-10-06. RAM-only COM260 runs; diagnostic bring-up evidence for one board. |
| B4 and accepted-tool fixes | R6 catalogue and R7 bounded proof re-derived for the K3 images; fixes to the accepted R7 extractor and R3/R4/R5 image checkers | Accepted 2026-10-07. Host, QEMU, and Rocq only; B4 ran nothing on the board, and R7's limits still apply. |
| B5 | First real guest: a tiny bare-metal VS guest with a B5 guest SBI subset and its own Sstc timer interrupt | Plan and result accepted 2026-10-07. Not a Linux or other OS guest. |
| B6 | Unmodified uniprocessor upstream Linux `v7.2` guest under a B6-owned G-stage over 64 MiB | Plan and result accepted 2026-10-08. No SMP, devices, DMA, or second guest; Linux is an untrusted test payload. |
| B7 | Two copies of the B6 guest with per-guest windows, G-stages, and vCPU state | Plan accepted 2026-10-08 and result accepted 2026-10-09 at `7b6b846b` (instruction `accept 7b6b84, commit and push`); 4 of 4 RAM-only COM260 kexec runs. Isolation by construction only, with no denial test; no SMP, devices, DMA, or shared page. |
| S1, S2, S3 | He-to-Be synthesis, security model v1, and the MVP plan | S1 accepted 2026-10-18 at `fd670dcd`; security model v1 accepted 2026-10-22 at `0e3eec8b`; the [MVP plan](mvp-plan.md) revision 1 accepted 2026-10-23 at `93967fba` (`06c35f48` superseded). |
| M0 | The MVP line, the multi-hart substrate, and the evaluation harness | The [M0 plan](mvp-m0-plan.md) accepted 2026-10-23 at `4d129808`; implementation in progress on `beryllium/mvp-m0`; no result proposed. |
| R8 | One exact K3 core-validation program, staged H0-H4 | Dropped 2026-10-08. The plan chain, the blocked H0/R8-C target, and the R8-ALM1-A plan text stay accepted history; H1-H4 were never authorized or run. |
| KVM0 | Native Linux/KVM-on-K3 qualification prerequisite | Parked 2026-10-06 and dropped 2026-10-08. Its accepted plans and packages stay history; K0-X/K0-R never ran. |
| Later milestones 3-10 | Protected domain with Linux management, multicore, I/O/DMA, policy, attestation, Arm portability, assurance, and upstream proposal | Candidates only; each waits until the accepted S3 MVP plan selects it. |

## K3 bring-up path

The B-series is the K3 path of record. Each milestone is one self-contained
directory under `bringup/k3-bN/`, built and tested with
`make -C bringup/k3-bN check`, with one exact accepted result:

| Milestone | What it showed | Accepted result | Board runs |
| --- | --- | --- | --- |
| [B0](k3-b0-result-review-summary.md) | HS boot marker `BE-K3-L0BOOT PASS`: entry, stack/BSS, SBI DBCN, and terminal SRST | `bb8fd210758f88640817b5ea8010fe0654e626f3`, 2026-10-06 | 3 of 3, kexec |
| [B1](k3-b1-result-review-summary.md) | The accepted R4 image, re-executing the R3 prelude, ported to K3: all ten accepted markers | `b44c3c6b502d2883e95f53c642f407b577a18829`, 2026-10-06 | 3 of 3, kexec |
| [B2](k3-b2-result-review-summary.md) | The accepted R5 checked switch ported to K3: all 22 accepted markers | `898af4e02fd36744a93b0eef99bc159955409d25`, 2026-10-06 | 4 of 4, kexec |
| [B3](k3-b3-result-review-summary.md) | The B2 image booted from U-Boot `booti` through a small shim | `9b4860a049646d8878a31ecea8957e95b045550f`, 2026-10-06 | 4 of 4, U-Boot |
| [B4](k3-b4-result-review-summary.md) | The R6 catalogue and R7 bounded proof re-derived for the K3 images | `135b1d3ae4def25691472bba0fa0179aa509d532`, 2026-10-07 | None: host, QEMU, and Rocq |
| [Tool fixes](accepted-tool-fixes-review-summary.md) | Fixes to the accepted R7 extractor and R3/R4/R5 image checkers, with unit tests and an acceptance-pin refresh | `c60896e35cb2ddb8d8662c973aa46d4b5d0d8ef2`, 2026-10-07 | None |
| [B5](k3-b5-result-review-summary.md) | First real guest: a tiny bare-metal VS guest, a B5 guest SBI subset, and the Sstc timer ([plan](k3-b5-plan.md) `c3f8ef51`) | `829562395bf14fedbeea0beb82b30da15ec5f7cf`, 2026-10-07 | 4 of 4, U-Boot |
| [B6](k3-b6-result-review-summary.md) | Uniprocessor upstream Linux `v7.2` guest under a B6-owned G-stage over 64 MiB ([plan](k3-b6-plan.md) `e34ef378`) | `e20c55df57551244eab47e0eff59d4c71fe75d20`, 2026-10-08 | 5 of 5: 4 kexec, 1 U-Boot |
| [B7](k3-b7-result-review-summary.md) | Two copies of the B6 guest interleaved on hart 0, each in its own 64 MiB window under its own G-stage root and VMID ([plan](k3-b7-plan.md) `026974fb`) | `7b6b846bf453bacf4c67d986f87c61fdc092e2ee`, 2026-10-09 | 4 of 4, kexec |

B2, B3, B5, and B7 each had three GCC runs and one Clang run; B6 had three
GCC runs and one Clang run through kexec and one GCC run through U-Boot.
Every board run loaded RAM only, through Linux `kexec_load` from the
running Fedora host or through U-Boot YMODEM `loady` and `booti`. Serial
capture was output-only. OpenSBI 1.6 SRST shutdown halts this board without
powering it off, so a human reset followed each run. The board-safety rules
forbid any persistent firmware, U-Boot environment, flash, or
boot-configuration change. Each run starts from state left by running
firmware and a loader on one board, so the runs characterize no cold-boot
state, firmware provenance, or other board. UEFI is neither used nor
selected.

Planned next. Each step needs its own plan and/or acceptance. Step 3 and
B7 are complete and accepted; S1 is complete and accepted; S2 and S3
are not authorized:

1. **Step 3, roadmap re-baseline (docs only):** drop KVM0 and R8 H1-H4,
   with their records kept as history; make the B-series the K3 path; make
   the He-to-Be synthesis depend on B-series evidence; and list the steps
   below. Exit: one docs commit for acceptance.
2. **B7, two Linux guests** (plan accepted 2026-10-08 at `026974fb`;
   result accepted 2026-10-09 at `7b6b846b`): two copies of the B6 guest
   (pinned Linux `v7.2`, uniprocessor, no devices), each with its own
   64 MiB window and G-stage and with its vCPU state saved and restored.
   Hart 0 switches between them round-robin when a guest idles (its `wfi`
   traps, with `hstatus.VTW` set) and on an HS timer slice through Sstc
   `stimecmp`, the monitor's first interrupt of its own. Each guest's
   console output has its own prefix. Userland is small programs built
   with Linux's own `tools/include/nolibc` from the already-pinned tree,
   so there are no new external inputs. Exit: both guests run interleaved
   and power off, in QEMU and then in 3 GCC and 1 Clang kexec runs on K3.
3. **S1, He-to-Be synthesis (docs):** classify each relevant Helium lesson
   as adopt, adapt, reject, or defer against the B0-B7 evidence. Sources:
   the [pathfinder comparison](pathfinder-comparison.md), the TE PoC
   evidence, and current `../helium-te-poc` read at one exact commit. It
   can run alongside B7. Exit: one planning doc for acceptance. Status:
   authorized 2026-10-16; the [synthesis](he-to-be-synthesis.md), revised
   as RP-1 of the accepted revision plan, accepted 2026-10-18 at `fd670dcd`
   (`0fbca0fd` superseded).
4. **S2, security model v1 (docs, plus model changes if needed):** one
   document: objects, invariants, the threat model, and the TCB; the policy
   specification, a central, declarative policy in the Type Enforcement
   family with deterministic and total semantics, default deny, and
   explicit conflict resolution; the analyses the policy proof targets name
   (unreachable, contradictory, over-broad, and non-revocable authority;
   information flow modulo the declared channels; authority
   non-amplification); the relation from the policy to the canonical
   manifest; the capability and runtime-check triggers evaluated against
   the platform's use cases under plan revision M01-A; the authority ceiling
   for the dynamic management case; and any Model 0.2 changes. The language
   form is S2's choice. Exit: one doc for acceptance. Definition revised by
   RP-3 of the accepted [revision plan](s1-te-trigger-revision-plan.md),
   accepted 2026-10-18 at `1ac7080f`. Status: plan accepted 2026-10-19 at
   `5ce7827f`; [security model v1](security-model-v1.md) accepted
   2026-10-22 at `0e3eec8b`.
5. **S3, MVP plan:** the initial security-research-platform release:
   scope, non-goals, milestones, evaluation harness, evidence claims, and
   release path. Exit: one plan for acceptance. Status: directed
   2026-10-22; [plan](mvp-plan.md) revision 1 accepted 2026-10-23 at
   `93967fba` (`accept 93967fba`; `06c35f48` superseded).

The expected first MVP milestone, after S2, is the Helium TE PoC scenario
on two Linux guests: a writer and a reader share one page (writer
read-write, reader read-only), private memory is denied, and the monitor
injects faults and logs the denials. Reproducing that scenario does not
select TE. A static BusyBox and musl userland comes later, for interactive
demos; it would need console input, which B6's SBI subset refuses.
Implementation-plan milestones 3-10 stay gated until the accepted S3 MVP
plan selects them.

Dropped workstreams, with records kept as history:

- **KVM0** (K0-P to K0-R), parked on 2026-10-06 and dropped on 2026-10-08:
  [Plan revision K0-A](k3-kvm0-plan.md) `5227266c`, accepted 2026-09-25
  ([record](k3-kvm0-plan-k0a-review-summary.md));
  [K0-I](k3-kvm0-k0i-review-summary.md) `abd092a1`, accepted 2026-09-26;
  the [K0-S status target](k3-kvm0-k0s-review-summary.md) `c6570558`,
  accepted 2026-09-29; and the [K0-SC](k3-kvm0-k0s-completion-plan.md),
  [K0-SC1, and K0-SC1-A](k3-kvm0-k0sc1-plan.md) plans, accepted as
  planning text. Corrected K0-SC1-B target `13463e4f` stays unaccepted
  ([packet](k3-kvm0-k0sc1-plan-k0sc1b-corrected-review-summary.md)), and
  K0-X and K0-R never ran.
- **R8 H1-H4**, dropped on 2026-10-08: the
  [R8 plan](single-hart-runtime-r8-plan.md) `7d0f0cbf`, R8-A `8fa9d672`,
  and R8-C `f47ae602` stay accepted. So does exact H0/R8-C target
  `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4`, accepted 2026-09-17 and still
  `BLOCKED-NOT-READY` with `r8_h0_exit=not-met`
  ([record](single-hart-runtime-r8-h0-review-summary.md)), and the
  [R8-ALM1-A plan text](single-hart-runtime-r8-active-line-maintenance-plan-r8alm1a-review-summary.md),
  accepted 2026-09-29. H1-H4 were never authorized or run.

## Frozen-profile categories

This page accepts no profile. Each B-series milestone freezes its own
inputs in its `bringup/k3-bN/` directory and, from B5 on, in an accepted
plan. Each result record names the exact commit, images, firmware, and
loaders behind its claims.

| Category to freeze | What it controls | Maintained source to consult |
| --- | --- | --- |
| Governance and names | Stage order, exact base, authority, result labels, and stop conditions | This guide, the [roadmap](roadmap.md), and [HANDOFF](HANDOFF.md) |
| Source and artifacts | Exact commits, port inputs and substitution tables, image identities, and guest pins | Each `bringup/k3-bN/README.md`, the [B5](k3-b5-plan.md) and [B6](k3-b6-plan.md) plans, and each result record |
| Open tools and build environment | Compiler and linker roles, pinned and unpinned workstation tools, and trust limits | [Open tooling](open-tooling.md), each result record's trusted list, and repository-root `LLM_POLICY_ALIGNMENT.md` |
| Platform and firmware | Board, silicon, the BSP's U-Boot and OpenSBI below HS, hart 0, and memory windows | [RISC-V and K3 hardware](riscv-security-hardware.md) and each result record |
| Loading, capture, reset, and recovery | RAM-only kexec or U-Boot `booti`, output-only serial capture, human resets, and no persistent change | Each B-series plan or README and its result record |
| Guest inputs | B5's bare-metal guest; B6's pinned Linux `v7.2`, DTB, and init | The [B5](k3-b5-plan.md) and [B6](k3-b6-plan.md) plans |
| Development kernel/BSP | A host or management Linux baseline, if one is ever needed | `UNDECIDED` and not a gate; the S3 MVP plan may revisit it |
| Manifests, privacy, and replacement | Separate manifests, restricted sensitive data, update triggers, and new-profile rules | Repository-root `LLM_POLICY_ALIGNMENT.md` and future plans |

This page intentionally excludes device identifiers, private remotes, raw
captures, sensitive boot arguments, filesystem UUIDs, and private source
contents.

## Evidence matrix and transfer limits

| Evidence class | What exists | What it supports | What it does not transfer to |
| --- | --- | --- | --- |
| Model host/unit evidence | Model 0.1 and 0.2 C/model checks, fixtures, reports, and bounded Rocq obligations | The exact non-runtime contracts and abstract obligations stated in their evidence records | Runtime C refinement, linked images, QEMU behavior, K3, hardware, or Helium |
| R1-R2 host evidence | GCC/Clang restricted-C tests, adversarial checks, deterministic reports, concrete Sv39x4 construction, and an independent walker | The exact accepted non-privileged mechanisms and fixed inputs | CSR writes, boot, QEMU, hardware, arbitrary configurations, or production assurance |
| R3-R6 QEMU evidence | Pinned GCC/Clang images, QEMU/OpenSBI traces, fixed-profile entry/trap/switch outcomes, and adversarial images | The bounded synthetic scenario at the recorded exact targets | K3 behavior, cold boot, arbitrary guests, Linux, devices/DMA, or whole-system security |
| R7 bounded Rocq/exact-byte evidence | Exact selected linked bytes, relocations, finite trace, theorem set, cut points, and trusted-boundary ledger | The accepted finite linked-byte obligations and report boundary | C refinement, compiler correctness, source-to-binary proof, whole-system verification, hardware, or certification |
| B4 K3-image re-derivation | The R6 catalogue (46 single-defect fixtures, 64 QEMU runs) and the R7 bounded Rocq development, re-derived over B2's K3 images | The accepted R6 and R7 claim boundaries for those exact K3 image bytes, in emulation and Rocq | Board behavior, the B5/B6 monitor layers, C refinement, or whole-system verification |
| K3 board runs (B0-B3, B5-B7) | RAM-only COM260 runs with output-only serial capture (3/3, 3/3, 4/4, 4/4, 4/4, 5/5, and 4/4), recorded under `bringup/k3-bN/results/` and in each result record | The recorded markers and guest output on one COM260 with its BSP firmware and the recorded loaders: diagnostic bring-up evidence for one board | Hardware validation or qualification, other boards or firmware, cold-boot state, SMP, devices, DMA, arbitrary guests, or proof of the B5-B7 monitor layers |
| Helium evidence | Host tests and bounded QEMU experiments in the standalone Helium repository and retained historical checkpoints | Helium's exact pathfinder claims, including the fixed-TE review-and-test PoC | Beryllium architecture/runtime acceptance, selected production TE, the B-series, K3, or hardware |
| KVM0-era private observations | PMR-077's human-reported COM260 bring-up and KVM/Fedora operation, and sanitized private-workspace notes on one candidate boot and the A2 failure/control image | Non-evidentiary history from the dropped KVM0 planning | Any B-series claim, BSP decision, KVM0 result, or hardware validation |
| Hardware validation | **None for Beryllium.** | Nothing yet | No board, silicon, reset, firmware, isolation, portability, performance, or certification claim |

Proof, test, emulation, diagnostic bring-up, and hardware validation are
different evidence classes. A bounded proof establishes only its formal
statement and assumptions; a test observes selected cases; QEMU is
emulation under a trusted software boundary; a diagnostic bring-up run
records what one board printed under the recorded firmware and loader.
Hardware validation, which no Beryllium result claims, would require
retained execution against an accepted validation plan on the named
physical profile. See the [glossary](glossary.md) for the precise terms.

## Exact next decisions and required inputs

| Order | Responsible-human decision | Minimum reviewed input | What it may unlock |
| ---: | --- | --- | --- |
| Done | Step 3 re-baseline accepted 2026-10-08 (instruction `accept ecad45`) | Exact docs commit `ecad45d8eb371218d6f9a0965b330fa5043ea273` over `3acb99ab999d7296276396393b5bcafcdee9ed77` | Accepted maintained documentation of the 2026-10-08 re-baseline; no B7, S1, S2, or S3 authority |
| Done | B7 plan accepted 2026-10-08 (instruction `accept 026974`) and result accepted 2026-10-09 (instruction `accept 7b6b84, commit and push`) | Exact plan commit `026974fb619295482b93a7ae8cffdc4f552825ea` and exact result commit `7b6b846bf453bacf4c67d986f87c61fdc092e2ee` | Accepted diagnostic bring-up evidence for two Linux guests on one hart of one board, and a private push of the B6, re-baseline, and B7 branches; no S1, S2, or S3 authority |
| Done | The revised S1 document at `fd670dcd` (RP-1; S1 authorized 2026-10-16; `0fbca0fd` superseded), Model 0.1 plan revision M01-A at `95ef0f6c` (RP-2), and the revised S2 definition at `1ac7080f` (RP-3), accepted in order on 2026-10-18 (instruction `I accept RP-1 RP-2 RP-3`) | Each relevant Helium lesson classified as adopt, adapt, reject, or defer against the B0-B7 evidence, with a TE-family declarative policy adopted as the specification (H59); the TE trigger split into specification and runtime check; S2's seven-part scope | Synthesis input to S2 and S3; the trigger wording S2 evaluates; the scope S2 fills |
| Done | S2 plan accepted 2026-10-19 (instruction `accept 5ce782`) and security model v1 accepted 2026-10-22 (instruction `accept 0e3eec8b`; V1 to V4 at their defaults) | Exact plan commit `5ce7827f9c2ffc6e0f88568692ab238e5feca49f` and exact document commit `0e3eec8b4fd74003f8cedbf2ca66871c31412624`: objects, invariants, threat model, and TCB; the policy specification (a central, declarative TE-family policy) and its analyses; its relation to the canonical manifest; the capability and runtime-check trigger outcomes; the dynamic authority ceiling | The model that S3 and the expected first MVP milestone build on; no S3 authority |
| 5 | Accept the [MVP plan](mvp-plan.md) at `93967fba`, revision 1 (S3 directed 2026-10-22 by `merge & push, start S3`; revised 2026-10-23; `06c35f48` superseded) | Scope, non-goals, milestones M0 to M4 on three statically owned harts, evaluation harness, evidence claims, and release path, with Q1 to Q12 | Done 2026-10-23 (`accept 93967fba`, Q1 to Q12 at their defaults): MVP milestone selection and M0's bounded plan; no milestone implementation |
| 6 | Accept the [M0 plan](mvp-m0-plan.md) at `4d129808`, revision 2 (proposed 2026-10-23 under the accepted MVP plan; `6e4b9d4a` and `d95b28e9` superseded) | The MVP line, the tool lock and evaluator, the harness, the multi-hart substrate, the platform record, work packages M0-1 to M0-6, Q1 to Q13 | Done 2026-10-23 (`accept 4d129808, proceed with implementation using opus-5.5 model`, Q1 to Q13 at their defaults): M0 implementation under the plan; no M1, push, or release |
| 7 | Accept M0's exact result commit | The `mvp/` line, the substrate, the harness, the platform record, and the board campaign, in one result packet | M1's bounded plan |

Any further merge into the development branch, root integration, and any
push beyond the one authorized on 2026-10-09 each need separate explicit
direction. A review packet is decision support, not
the target. Acceptance applies to one exact immutable target. Exit readiness
is a gate result. Authorization is separate permission to act. None should
be inferred from a passing local command, branch name, packet, or available
board.

## Copyable inspection runbook

Run from the Beryllium repository root:

```sh
git status --short --branch
git show -s --format='commit=%H%nparent=%P%ntree=%T%nsubject=%s' HEAD
git log --oneline \
  3acb99ab999d7296276396393b5bcafcdee9ed77..HEAD
# Accepted B6 result, on branch beryllium/k3-b6-bringup:
git show -s --format='commit=%H%nparent=%P%ntree=%T%nsubject=%s' \
  e20c55df57551244eab47e0eff59d4c71fe75d20
ls bringup

./be
./be help --details
./be status

less planning/project-orientation.md
less planning/roadmap.md
less planning/glossary.md
less planning/k3-b6-result-review-summary.md
less planning/k3-b6-plan.md

git -C ../helium-te-poc status --short --branch
git -C ../helium-te-poc show -s \
  --format='commit=%H%nparent=%P%ntree=%T%nrefs=%D%nsubject=%s' for-review
```

Expected interpretation:

| Command | Expected result |
| --- | --- |
| `git status --short --branch` | Clean worktree after the step 3 commit. The development branch is `beryllium/single-hart-runtime-r0`, which `origin` then held at `3bc3ef04...` (from 2026-10-16, at the B7 branch tip); B6, step 3, and B7 are on branches `beryllium/k3-b6-bringup`, `beryllium/roadmap-rebaseline`, and `beryllium/k3-b7-bringup`, which the 2026-10-09 instruction `accept 7b6b84, commit and push` authorized pushing to the private `origin`. |
| `git show ... HEAD` | The newest commit on the checked-out branch. On `beryllium/roadmap-rebaseline` that is the step 3 re-baseline commit over B6 acceptance record `3acb99ab...`. |
| `git log --oneline 3acb99ab...HEAD` | The step 3 re-baseline commits over the B6 acceptance record; empty before the step 3 commit exists. |
| `git show ... e20c55df...` | Exact accepted B6 result identity, distinct from its packet commit `4611007f...` and its acceptance record `3acb99ab...`. It succeeds in a checkout containing branch `beryllium/k3-b6-bringup` or a descendant. |
| `ls bringup` | One directory per K3 bring-up milestone, `k3-b0` to `k3-b7`. Each `README.md` describes that milestone's build, tests, and results. |
| `./be` | Concise command list plus a status statement that predates the B-series: R0-R7 accepted, H0 accepted but `BLOCKED-NOT-READY`, and K3 `NOT RUN`. B-series root integration is not authorized, so the roadmap and the B-series records carry current state. |
| `./be help --details` | Long milestone history and claim limits. It is explanatory output, not a new decision record. |
| `./be status` | Machine-readable repository and package fields. Some accepted targets deliberately retain pre-decision or historical fields; use the roadmap and review records for later responsible-human decisions. |
| `less planning/roadmap.md` | Current placemat, planned sequence, current gates, and authoritative links. |
| `less planning/k3-b6-result-review-summary.md` | Exact B6 acceptance, board runs, claim boundary, and explicit non-authorizations. |
| `git -C ../helium-te-poc ...` | Clean standalone Helium `for-review` ref at the current exact source-of-truth commit; re-check before relying on the ref because Helium evolves separately. |

Do not run implementation, evaluation, board, push, tag, or publication
commands merely because they are listed elsewhere. Passing inspection or
documentation checks does not grant authority.

## Maintenance contract

- [`roadmap.md`](roadmap.md) is the maintained current-position placemat and
  decision queue.
- This orientation page explains project structure, evidence transfer limits,
  the K3 bring-up path and planned sequence, and the re-entry runbook.
- [`glossary.md`](glossary.md) owns maintained definitions and
  disambiguations.
- Detailed plans define scope and gates; evidence records define observed
  results and claim limits; review/acceptance records define exact
  responsible-human decisions.
- [`HANDOFF.md`](HANDOFF.md) owns operational restart, repository state, and
  Project Manager return detail.
- The standalone `../helium-te-poc` repository owns current Helium source,
  review, remediation, and release status. Beryllium historical refs remain
  historical.
- Markdown under `planning/` is authoritative and routinely maintained.
  Graphviz DOT is authoritative diagram source. Generated SVG is refreshed
  when diagram source changes or at milestones.
- `docs/html/` and `pathfinder/docs/html/` are deferred generated
  milestone/release artifacts, not routine active-line diffs. Their private
  historical snapshot is `archive/generated-docs-2026-09-30` at
  `d4c5ff0616c78d997367a050db85512c44960acb`; it is neither source authority
  nor publication approval.
- Routine documentation-only wording and status changes use fast source
  checks, not VitePress generation or Chromium. Complete docs/browser gates
  remain required at major milestones, where an exact review plan requires
  them, and for release/publication and periodic CI.

Update this page in the same reviewable change whenever the roadmap status
date, exact accepted boundary, readiness, authorization, planned sequence,
source-of-truth repository/ref, evidence class, or next-decision order
changes. Preserve the separation among accepted, exit-ready, authorized,
executed, and published states.
