<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium roadmap

> **Reading note (MVP 1.0's public release).** This page is part of the
> planning record as it stood at this repository's source commit, before
> the repository existed; its statements of status, repositories, and
> publication are as of the source commit (2026-11-05). The release itself is described by
> `README.md` and `RELEASE.md` at the repository's root.

**Status date:** 2026-10-22. This is the maintained project-lead placemat for
the active development line. It records current decisions, the planned
sequence, and gates; the linked plans, evidence, and review records remain
authoritative. Updating this page does not accept or authorize work.

This version is the step 3 re-baseline. Its exact target
`ecad45d8eb371218d6f9a0965b330fa5043ea273` (parent `3acb99ab`) is
responsible-human accepted as of 2026-10-08 by the instruction
`accept ecad45`, which resolves uniquely to that commit. Acceptance covers
that commit's documentation content and authorizes none of B7, S1, S2, or
S3; the follow-up that records it changes only status text. The previous
version, with the full KVM0 and R8 status detail, is in Git history. Its
last accepted documentation target is
`a9bb91df94f7e1df2b0e7f2d3ca057f6516ea511` (2026-10-04); see the
[roadmap review and acceptance record](k3-project-status-roadmap-review-summary.md).

> **Current position (2026-10-28):** the K3 bring-up sprint is the active
> path: one self-contained milestone at a time under `bringup/k3-bN/`, each
> with its own plan or authorization and its own result review. B0 to B7
> are accepted. B7 ran two copies of the B6 guest, an unmodified upstream
> Linux `v7.2` kernel built uniprocessor, interleaved on hart 0, each in
> its own 64 MiB window under its own G-stage root and VMID. Both guests
> powered off in 4 of 4 RAM-only COM260 kexec runs, three GCC and one
> Clang. Exact result commit `7b6b846bf453bacf4c67d986f87c61fdc092e2ee` is
> responsible-human accepted as of 2026-10-09 (instruction
> `accept 7b6b84, commit and push`); see the
> [B7 result review and acceptance record](k3-b7-result-review-summary.md).
> That acceptance started no successor. Board results are diagnostic
> bring-up evidence for one board, not hardware validation.
>
> On 2026-10-08 the responsible human dropped the KVM0 workstream
> (`we will also drop the kvm0 workstream, we can create again if needed`)
> and R8 stages H1-H4 (form answer `r8=drop`). Their records stay as
> history. The same day, the form answer `step3=proceed` directed this
> re-baseline, which was accepted at `ecad45d8`. It set the sequence: two
> Linux guests (B7), then the Helium-to-Beryllium synthesis, a concrete
> security model, and an MVP plan for the initial security-research
> platform. B7 is complete: its bounded [plan](k3-b7-plan.md) was accepted
> on 2026-10-08 (`026974fb`) and its result on 2026-10-09 (`7b6b846b`).
> On 2026-10-16 the instruction `authorize S1, proceed` authorized S1. Its
> [synthesis](he-to-be-synthesis.md) was first proposed at `0fbca0fd`
> (superseded) and, revised, was accepted on 2026-10-18 at exact commit
> `fd670dcd` (RP-1; instruction `I accept RP-1 RP-2 RP-3`; see the
> [revision review summary](s1-te-trigger-revision-review-summary.md)), so
> S1 is complete. On 2026-10-17 the responsible human had found that the
> draft treats TE only as a runtime denial and requested a review of the
> draft and of the project against its founding goals; on 2026-10-18 the
> instruction `approve 480d 07541` accepted the
> [project review](project-review-2026-10-17.md) at exact commit
> `480dab72` (corrected after a second research run on `claude-fable-5.1`;
> `65fc52e0` superseded) and the
> [S1 and TE-trigger revision plan](s1-te-trigger-revision-plan.md) at
> exact commit `07541c59`, recorded in one
> [review summary](project-review-2026-10-17-review-summary.md). The plan's
> three documentation packages were then accepted on 2026-10-18 by the
> instruction `I accept RP-1 RP-2 RP-3`: RP-1, the revised S1, at
> `fd670dcd`; RP-2, Model 0.1 plan revision M01-A (the TE trigger), at
> `95ef0f6c`; and RP-3, the revised S2 scope statement, at `1ac7080f`; see
> the [revision review summary](s1-te-trigger-revision-review-summary.md).
> The revision plan is complete. The development branch was fast-forwarded
> to `0eb37570`, the record of those acceptances, and pushed to the private
> `origin` on 2026-10-18 (`fast-forward dev to 0eb37570 and push`). S2 is
> complete: the instruction `then proceed with S2 plan` directed its
> [plan](s2-security-model-plan.md), which the instruction `accept 5ce782`
> accepted on 2026-10-19 at exact commit `5ce7827f` (see its
> [review summary](s2-security-model-plan-review-summary.md)), with Q1
> answered A (a notation defined in the document) and Q2 to Q7 at their
> defaults. Under it, [security model v1](security-model-v1.md) was
> proposed on 2026-10-19 at exact commit `0e3eec8b` and accepted on
> 2026-10-22 by the instruction `accept 0e3eec8b`, with its open
> questions V1 to V4 at their defaults (see its
> [review and acceptance record](security-model-v1-review-summary.md)).
> S3 is complete: on 2026-10-22 the instruction
> `merge & push, start S3` fast-forwarded the development branch from
> `0eb37570` to `0096de3e`, the acceptance record of security model v1,
> pushed it to the private `origin`, and directed S3. On 2026-10-23 the
> responsible human directed a revision (`revise the plan so that the
> MVP 1.0 is one hart per guest and the security monitor / protected
> domain ... has its own hart as well`) and then accepted the
> [MVP plan](mvp-plan.md), revision 1, at exact commit `93967fba`
> (instruction `accept 93967fba`; see its
> [review and acceptance record](mvp-plan-review-summary.md)), with Q1 to
> Q12 at their defaults. MVP 1.0 runs each domain on its own hart with a
> dedicated control hart, three of the COM260's eight harts under static
> ownership, with no scheduler. The first candidate `06c35f48`,
> single-hart on B7's scheduler, is superseded and was never accepted.
> The acceptance authorizes writing M0's bounded plan only; no MVP
> milestone is authorized. On 2026-10-23 the choice `(b)` directed M0's
> plan, and the later instruction `sure. update that, then proceed with
> (a) and continue development` fast-forwarded the development branch
> from `0096de3e` to `1fb46419`, the S3 acceptance record, and pushed it
> with `beryllium/s3-mvp-plan` to the private `origin`. The
> [M0 plan](mvp-m0-plan.md), revision 2, was accepted the same day at
> exact commit `4d129808` (instruction `accept 4d129808, proceed with
> implementation using opus-5.5 model`; see its
> [review and acceptance record](mvp-m0-plan-review-summary.md)) on
> local branch `beryllium/mvp-m0-plan`, from `1fb46419`; its first
> candidate `6e4b9d4a` and revision 1 `d95b28e9` are superseded. M0
> implementation ran under that plan on branch `beryllium/mvp-m0`: M0-1
> and M0-2 are complete and M0-3 is complete except that stop condition
> 3 fired (Clang's monitor text `0x7e0` over the accepted limit; GCC
> fits), with two design gaps (`mvp/README.md` open items 9 and 10). On
> the responsible human's direction `agreed, proceed with your
> recommendations, planning and implementation` (2026-10-23), Plan
> revision M0-A in the M0 plan adds an MVP-owned code region at
> `0x102064000` by a counted port rule, the boot-hart rule for
> `BE_MVP:02`, the redefined `ring-full` variant, the hart-region
> erratum, and the "MVP core profile" debt item; implementation resumed
> under it. Plan revisions M0-B (the evaluator's closure source, directed
> 2026-10-24) and M0-C (the control hart's drain order, directed
> 2026-10-25 after the first board campaign stopped on stop condition 6)
> followed. M0 is now implemented through M0-6: on 2026-10-25 and 26 the
> second COM260 campaign passed all eight RAM-only kexec runs (both Linux
> domains on their own harts, concurrent, 125 alternations in each of
> four scenario runs; the probes' facts; the `payload` run failing as
> declared), and at exact commit `13992d6d`, from a clean tree, `mvp
> check`, `mvp evaluate` (146 of 146 images identical), and the kexec
> rehearsal pass. Exact result commit
> `b266972563a39b0687ba2ac8c5b4cb943f3c766a` (parent `13992d6d`) is
> responsible-human accepted as of 2026-10-26 (instruction
> `accept b26697`), with Plan revisions M0-A, M0-B, and M0-C; see the
> [M0 result review and acceptance record](mvp-m0-result-review-summary.md).
> On `proceed` (2026-10-26, form answers `ff-dev`, `push`, `m1-plan`,
> `k3ctl`) the development branch was fast-forwarded to `6f7b6e7c` and
> pushed with `beryllium/mvp-m0`, and the
> [M1 plan](mvp-m1-plan.md), the TE PoC scenario on two Linux guests,
> was proposed at exact commit `7b2c055c1587f9582812a575b296cd625746662b`
> on local branch `beryllium/mvp-m1-plan` and accepted the same day
> (instruction `accept 7b2c055c`, Q1 to Q19 at their defaults; see its
> [review and acceptance record](mvp-m1-plan-review-summary.md)). The
> acceptance authorizes M1 implementation, work packages M1-1 to M1-6,
> on branch `beryllium/mvp-m1` from the acceptance record, and nothing
> else. M1 ran under it with Plan revisions M1-A and M1-B; its exact
> result commit `ff84533cb3c13d89063be77652575347c2a82757` was accepted
> on 2026-10-27 (instruction `approve ff84533c and revisions, accept
> your recommendations, authorize proceeding per those`; see the
> [M1 result review and acceptance record](mvp-m1-result-review-summary.md)),
> the development branch was fast-forwarded to `ccf70a3d` and pushed,
> and the [M2 plan](mvp-m2-plan.md), a static protected research domain
> beside an untrusted Linux, was accepted the same day at exact commit
> `854a54152502c4c9a14fe2d1897d907a358a8251` (instruction `accept
> 854a5415 , gpl 2.0 only ok`; see its
> [review and acceptance record](mvp-m2-plan-review-summary.md)). M2 is
> implemented through M2-7 on branch `beryllium/mvp-m2`: on 2026-10-28
> the first COM260 campaign stopped at its first run on stop condition
> 6 (the checker's expectation for the IPI probe, not the monitor; Plan
> revision M2-A, harness only, directed by `remedy=A, reset_board=true`),
> and the second passed 6 of 6 RAM-only kexec runs as declared (three
> GCC and one Clang `anchor` runs with identical counts, the protected
> domain measured, paused, and terminated; `wrong-measurement` and
> `no-grant-check` failing as declared; one board boot without network
> after a reset, resolved by a human-authorized second reset). At exact
> commit `397670e5`, from a clean tree, `mvp check`, `mvp evaluate` (247
> of 247 images identical), the kexec rehearsal, and `kernel-repro`
> pass. Exact result commit `18d552bc4cf3a463bc4dc491e5e346989e5a521c`
> (parent `397670e5`) is responsible-human accepted as of 2026-10-28
> (instruction `accept 18d552bc`), with Plan revision M2-A; see the
> [M2 result review and acceptance record](mvp-m2-result-review-summary.md).
> On `approve 1 & 2. proceed` (2026-10-28) the development branch was
> fast-forwarded to `50b77c00`, the M2 acceptance record, and pushed to
> the private `origin` with `beryllium/mvp-m2` and `beryllium/mvp-m2-plan`,
> and the [M3 plan](mvp-m3-plan.md), the policy layer and the hart
> binding in the model, was proposed at exact commit
> `c2c249f4c3d364590d2e505a4f6fb5e65456ff81` on local branch
> `beryllium/mvp-m3-plan` (its first candidate `9952e765` superseded
> when, on the responsible human's direction, its size and time limits
> became soft limits that stop for re-evaluation) and accepted the same
> day (instruction `accept c2c249f4`, Q1 to Q12 at their defaults; see
> its [review and acceptance record](mvp-m3-plan-review-summary.md)); a
> first draft was reviewed by `gpt-5.6-sol` on the responsible human's
> authorization and its twelve findings incorporated. The acceptance
> authorizes M3-1, the additive security model v1 revision, as its own
> exact commit for decision on branch `beryllium/mvp-m3`, and M3-2 to
> M3-6 only after that revision is accepted. M3-1 is proposed:
> [Revision 1](security-model-v1.md#revision-1-2026-10-28-the-hart-binding-and-the-third-instance)
> of security model v1 (the `hart` class, I13 to I16, Instance 3, Part
> 7's rows, the projection erratum) at exact commit
> `019cca64971d2399faba3d768d6f5b1fc9145198` (its first candidate
> `32298add` superseded after a second `gpt-5.6-sol` review the
> responsible human directed), appended to the accepted text, which is
> byte-identical, and accepted the same day (instruction
> `accept 019cca64`; see its
> [review and acceptance record](security-model-v1-revision-1-review-summary.md));
> seven errata of the accepted M3 plan are recorded in its acceptance
> record. M3-2 refreshed the lock on the host (`12e6fb06`: the accepted
> gate's results identical under GCC 16.2.1 and Rocq 9.3.0; `make -C
> model check` passes), stopped at stop condition 6 (the rootless
> evaluator installs Node.js 22.23.1 where the lock had v22.22.2), and
> completed on the responsible human's remedy A (`0e05d338`: the host
> and the lock on Node.js 22.23.1; `make -C model check` and `./be
> evaluate` pass). M3-3 to M3-6 followed: the Rocq policy layer and the
> MVP's hart binding (T1 to T5, H0 to H3, 22 closed assumption reports
> beside the accepted 24), the executable model and generator, and the
> three-way differential check (91 mutations; `PASS three_way=73
> two_way=22 comparisons=241`); at exact commit `d35813c7` from a clean
> tree `./be model-check` and `./be evaluate` pass. Exact result commit
> `b0a0f352d7969a8f8cf28cf0d25b89fc372e70f2` (parent `d35813c7`) is
> responsible-human accepted as the M3 result (2026-10-28, instruction
> `6000 per lane, so 12,000 combined soft limit. accept b0a0f352`); the
> [M3 result review and acceptance record](mvp-m3-result-review-summary.md)
> carries the decision, and the
> [M3 evidence record](mvp-m3-evidence.md) the evidence. Four stops were
> decided by the responsible human (plan errata 8 to 11), and the
> acceptance fixed the two re-set soft limits as 6,000 per lane, a
> combined 12,000 against the measured 6,492 (erratum 12). M0 to M3 are
> accepted. On `push all work` and `then proceed with (1) and (2)`
> (2026-10-28) the development branch was fast-forwarded to `fb8accc9`
> and pushed with the M3 branches, and the [M4 plan](mvp-m4-plan.md),
> the release candidate, is proposed at exact commit `0d02df72` on
> local branch `beryllium/mvp-m4-plan` with its
> [review summary](mvp-m4-plan-review-summary.md), after its first
> candidate `91f4a820` was reviewed by `gpt-5.6-sol` on the responsible
> human's session SOP of 2026-10-28 and its nine findings incorporated;
> the responsible human accepted it the same day and authorized M4
> (instruction `accept 0d02df27, authorize M4`, read as
> `accept 0d02df72`; Q1 to Q13 at their defaults). M4-1 to M4-6 ran on
> `beryllium/mvp-m4` on 2026-10-28 and 29, with two stops decided by
> the responsible human (the new-code soft limit re-set to 2,000, plan
> erratum 1; Plan revision M4-A, the board record's redaction to code
> names). The candidate tree `X` is `d42b9ec0`, on which the seven
> gates pass with 247 of 247 images identical; the release-candidate
> board campaign ran at `X`'s images on the human's confirmation,
> eleven of eleven runs as declared; the release-candidate commit
> **`c5df0cfa`** (`R`, over `X`) is responsible-human accepted as the
> M4 result and the MVP 1.0 release candidate (2026-10-29, instruction
> `accept c5df0cfa, commit & push, I will review in detail`), with Plan
> revision M4-A; the
> [result review and acceptance record](mvp-m4-result-review-summary.md)
> carries the decision and the [evidence record](mvp-m4-evidence.md) the
> evidence; the [operator's walkthrough](mvp-rc-walkthrough.md) is for
> the human's detailed review. M0 to M4 are accepted: MVP 1.0's
> milestones are complete. The acceptance is the release path's step 1;
> steps 2 to 7 each need their own instruction and none is started.
> `beryllium/mvp-m4` and `beryllium/mvp-m4-plan` are on the private
> `origin`; the development branch stays at `fb8accc9`. **On 2026-10-29
> the responsible human directed that the MVP candidate boot from system
> reset** (`modify the plan so that the mvp candidate boots from system
> reset. I don't know where those safety rules came from.`; the rules
> were automation's own, from B0's README) and set the standing rule
> `no more kexec unless I approve it` (clarified: don't use it from
> here unless truly needed, then stated and approved). Plan revision
> S3-A of the MVP plan (the board policy, M5, release-candidate staging:
> RC1 `c5df0cfa` accepted history, RC2 = M5's result) and the
> [M5 plan](mvp-m5-plan.md) (one ext4 partition `beryllium` on the NVMe
> from p3; U-Boot's saved environment installed and restored per
> recorded session; templated, recorded typing; `k3ctl` resets; kexec
> removed from the MVP tools and claim; a U-Boot rehearsal in QEMU;
> soft limit 5,000) are **responsible-human accepted as of 2026-10-29**
> (instruction `accept 0d134bbc and 066794d, authorize m5`, read as
> `0066794d`; Q1 to Q16 at their defaults;
> [M5 plan review and acceptance record](mvp-m5-plan-review-summary.md)),
> with M5 implementation authorized on `beryllium/mvp-m5`; the
> partition tool is delivered for the human's one `--apply`; the plan
> branch is unpushed. **The M5 result, exact commit `3867c66c` (`R2`,
> over the candidate tree `X2` `6dd81ee3`), is responsible-human
> accepted as MVP 1.0 release candidate 2 as of 2026-10-30** (instruction
> `accept 3867c66c`; the
> [M5 result review and acceptance record](mvp-m5-result-review-summary.md)
> carries the decision and the [M5 evidence record](mvp-m5-evidence.md)
> the evidence); on `approve 1, 3` (2026-10-30) `beryllium/mvp-m5` and
> `beryllium/mvp-m5-plan` are pushed to the private `origin` and the
> development branch is fast-forwarded from `fb8accc9` to the commit
> recording the push; the release path's step 1 now holds for release
> candidate 2, with release candidate 1 accepted history; debt sweep 1
> (`mvp/README.md` items 83 and 85, with the ledger-pin fix `466c29f4`
> for item 86) is accepted at exact commit `80ef8a13` (`proceed with
> push & accept 80ef8a13`, 2026-10-30) on `beryllium/mvp-debt-1`, and
> the development branch is fast-forwarded to its acceptance record and
> pushed. The human made the
> partition on 2026-10-30; the characterization passed on its seventh
> attempt (six stopped on BSP facts, each a tool fix); at `X2` the seven
> gates pass (253 of 253 images identical; the U-Boot rehearsal's seven
> cases; `mvp/results/20261030-rc2/`); the board session ran at `X2`'s
> images with the human present at the install and the restore: twenty
> runs booted from system reset by the COM260's firmware and U-Boot from
> the `beryllium` partition, twenty of twenty as declared with the
> accepted records' counts, the saved environment restored to the
> pre-session record byte for byte, one stop (a lost `s`) hardened and
> resumed (`mvp/results/20261030-com260-rc2/`). Stop 8 fired at 6,865
> code lines; the human re-set the limit to 10,000 (7,439 at `X2`).
> Board results are diagnostic bring-up evidence for one board, not
> hardware validation; no release step, merge, push, or kexec use.
> **On 2026-10-30 the human directed `we will go with RC3 first`:**
> [Plan revision S3-B](mvp-plan.md#plan-revision-s3-b-release-candidate-3-and-milestone-m6-the-mvp-core-profile)
> (`f8b77ac9`, D18) and the [M6 plan](mvp-m6-plan.md) (`b2c62d54`: the
> MVP core profile, the frozen fixed profile replaced by the MVP's own
> configuration validated, sealed, and derived at boot by the ported
> accepted R1 mechanism, the fixture roots and pages dropped, one
> executor for the privileged effects, release candidate 3 with the
> gates and a 20-run board campaign) are **responsible-human accepted as
> of 2026-10-30** (instruction `accept f8b77ac9 and f8b77ac9`, the second
> decision confirmed by the form answer `accept-and-authorize`; Q1 to
> Q11 at their defaults;
> [M6 plan review and acceptance record](mvp-m6-plan-review-summary.md)),
> with M6 implementation authorized on `beryllium/mvp-m6` from the
> acceptance record; the plan branch is unpushed. **M6 is implemented
> and release candidate 3 is responsible-human accepted as of
> 2026-10-31** (instruction `accept 89ef04e9, proceed`): exact commit
> `89ef04e9` (`RC3`, over the candidate tree `X3` `ebc49a88`;
> [M6 result review and acceptance record](mvp-m6-result-review-summary.md),
> [M6 evidence record](mvp-m6-evidence.md)); release candidates 1 and
> 2 are accepted history, the "MVP core profile" debt is retired, and
> the release path's step 1 holds for release candidate 3, with steps
> 2 to 7 not started and each needing its own instruction; no push or
> merge was directed. The monitor's boot now
> validates, seals, and derives each scenario's own configuration
> (`BE_MVP:00 BOOT_VALIDATED`, `CONFIG_SEALED`); the privileged effects
> sit behind one executor; the model instance is deferred with its
> reason (ledger U-13). At `X3` the seven gates pass from a clean
> checkout (`mvp/results/20261031-rc3/`), and on 2026-10-31 twenty board
> runs from system reset at `X3`'s images passed as declared with
> release candidate 2's counts and the saved environment restored byte
> for byte, no stop (`mvp/results/20261031-com260-rc3/`). New code
> 3,258 of 4,000 lines; thirteen departures recorded. Board results are
> diagnostic bring-up evidence for one board, not hardware validation;
> no release step, merge, push, or kexec use. Two read-only Rhyolite
> reviews of the public review snapshot (`1ae5fd8c`), consolidated by
> the human into twelve verified root causes (rows A to L, all in the
> privileged board tooling, the release surfaces, licensing, and
> reproducibility, none in `mvp/src/`), are remediated by debt sweep 3,
> **responsible-human accepted as of 2026-11-01 at exact commit
> `3b7ab0e3`** (`accept 3b7ab0e3, fast fwd, push, use your best
> judgement`; the
> [debt sweep 3 review and acceptance record](rc3-review-remediation-review-summary.md)):
> the retained kexec launchers run isolated behind the standing rule's
> gate, the console tool's diagnostic filter is an anchored allowlist,
> staging binds to the partition's UUID, the partition tool's backups
> are exclusive writes into a directory only the caller can write, the
> generator's variant names have the scenario's grammar, the ledger
> names release candidate 3 and checks every release surface against
> it, C-05 states the `hgatp` boundary the code has, the GPL-2.0 text
> and a root `COPYING` are in with a licence check, `tests/r8` leaves
> the snapshot, and the snapshot README names its entry points; the
> development branch is fast-forwarded to the acceptance record and
> pushed; the public snapshot's refresh is the human's push; open items
> 94 to 97 (the closure no longer buildable from public sources among
> them) are the human's. Debt sweep 4, **responsible-human accepted as
> of 2026-11-01 at exact commit `d162c60d`** (`accept d162c60d & ff +
> push`; the
> [debt sweep 4 review and acceptance record](mvp-debt-4-review-summary.md)),
> fixes the capture checker's forged-loader-block reading, the model
> gate's singular-only escape pattern, the snapshot tool's hard-coded
> session trailer, and the evaluator's ignored cache argument, and adds
> the root `SECURITY.md` the human directed for the public review
> snapshot (open reporting for now); the development branch is
> fast-forwarded to its acceptance record and pushed. Debt sweep 5,
> **responsible-human accepted as of 2026-11-01 at exact commit
> `e8ab73b7`** (`accept  & ff + push , and  re-refresh`; the
> [debt sweep 5 review and acceptance record](mvp-debt-5-review-summary.md)),
> makes the evaluator's closure fetchable from public sources again
> through Fedora's updates archive (item 95 closed; item 106 the
> residual); the development branch is fast-forwarded to its acceptance
> record and pushed, and the public snapshot is re-refreshed from it for
> the human's push.

## At a glance

```text
R0-R7 on QEMU ................................ accepted
K3 bring-up B0-B6 ............................ accepted
Step 3: roadmap re-baseline .................. accepted
B7: two Linux guests ......................... accepted
S1: He-to-Be synthesis ....................... accepted
S2: security model v1 ........................ accepted
S3: MVP plan ................................. accepted
M0: MVP line, multi-hart substrate, harness .. accepted
M1: TE PoC scenario plan ..................... accepted
M1 implementation (M1-1..M1-6) ............... accepted (result ff84533c, 2026-10-27)
M2: static protected domain plan ............. accepted (854a5415, 2026-10-27)
M2 implementation (M2-1..M2-7) ............... accepted (result 18d552bc, 2026-10-28)
M3: policy layer and hart binding plan ....... accepted (c2c249f4, 2026-10-28)
M3-1: security model v1 revision ............. accepted (019cca64, 2026-10-28)
M3 implementation (M3-2..M3-6) ............... accepted (result b0a0f352, 2026-10-28)
M4: release candidate plan ................... accepted (0d02df72, 2026-10-28)
M4 implementation (M4-1..M4-6) ............... accepted (release candidate 1, c5df0cfa, 2026-10-29)
MVP plan revision S3-A: boot from reset ...... accepted (0d134bbc, 2026-10-29)
M5: release candidate 2 plan ................. accepted (0066794d, 2026-10-29)
M5 implementation (M5-2..M5-7, M5-6a) ........ accepted (release candidate 2, 3867c66c over X2 6dd81ee3, 2026-10-30)
MVP plan revision S3-B: RC3 first ............ accepted (f8b77ac9, 2026-10-30; the human's direction "we will go with RC3 first")
M6: MVP core profile plan (release candidate 3) accepted (b2c62d54, 2026-10-30)
M6 implementation (M6-2..M6-8) ................ accepted (release candidate 3, 89ef04e9 over X3 ebc49a88, 2026-10-31)
MVP 1.0 release path, step 1 .................. holds for release candidate 3 (the core profile debt retired; the review snapshot published 2026-10-31)
MVP plan revision S3-C: the ladder, 1.0 widened accepted (27d2e557, 2026-11-01, Q27-Q46 at their defaults, after three independent reviews of the first candidate 95c9ab24; M7 interactive guests, M8 first verification plan, M9 measurement, M10 release candidate 4)
M7 plan: interactive guests ................... accepted (4f4d094e, 2026-11-01, Q1-Q16 at their defaults)
M7 implementation (M7-2..M7-6) ................ accepted (e1a6395e over the gates' commit 8418a377, 2026-11-02; the seven gates pass; the board's typed characterization and one shell session passed; the k3ctl pin unchanged)
M8 plan: the first verification plan ......... accepted (7a0c74ae, 2026-11-02, instruction `accept 7a0c74ae wuth CN, go for m9`; Q10 with CN, the rest at their defaults)
M8 implementation (M8-2..M8-7) ................ accepted (12b0e71b over the gates' commit f1813841, 2026-11-04, instruction `accept 12b0e71b`; the outcome inconclusive under D-7: no C-level contract proof, the claim unchanged, the stage-1 rows and the review item added; the seven gates pass, verify among them; packet mvp-m8-result-review-summary.md)
M9 plan: measurement .......................... accepted (4f4a8f76, the second candidate, 2026-11-03, instruction `accept 4f4a8f76`; Q1-Q19 at their defaults, Q17 answered by the gpt-6-astra steering review the human directed; the first candidate 86f1c68b superseded)
M9 implementation (M9-2..M9-6) ................ accepted (892b68c8 over the gates' commit dc07f7d3, 2026-11-03, instruction `accept 892b68c8`; the seven gates pass; the claim's D-9 sentences in effect with the slots filled; no board step: the probe not performed and the correlation boot not run, each the human's to schedule; packet mvp-m9-result-review-summary.md)
M10: release candidate 4 ...................... accepted (d70a8535, 2026-11-05, instruction `accept d70a8535`; exact X4 a6eaa885; eight gates PASS; 25/25 COM260 runs PASS with three typed sessions; environment restored/preflights equal; exact-RC4 check PASS); MVP 1.0's milestones M0-M10 complete; release-path step 1 holds for RC4; YOU ARE HERE next: private ff/push on the human's word, and release-path step 2 (the human's selection of what migrates) on its own instruction
MVP 1.0 release path, steps 2-7 ............... after release candidate 4 (step 2 is the human's selection of what migrates; each step needs its own instruction)
```

## Executive position

Beryllium is pursuing a small RISC-V HS-mode isolation engine with rich
services outside the core. The baseline authority model is immutable
ownership plus explicit channels. The accepted security model v1 (S2)
specifies the system's security properties as a central, declarative,
default-deny policy in the Type Enforcement family, with enforcement
derived from it (the accepted S1 row H59 and Model 0.1 plan revision
M01-A). It finds that neither the capability trigger nor the
runtime-check trigger fires for the fixed profile or the first MVP
milestone, and that both are undecidable for the dynamic management case
until a management-request vocabulary exists, so software capabilities
and a runtime TE check stay trigger-gated. The core direction is
C-first, Rocq-primary, RISC-V-first, and fully open-tooling oriented. S1,
S2, and S3 are complete; the accepted MVP plan defines a deliberately
limited initial security-research-platform release on three statically
owned harts, and the current priority is M0's implementation under its
accepted bounded plan.

## Milestone status

Short SHAs name exact accepted targets; each linked record holds the full
SHA, the instruction, and the claim boundary.

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
| Other | Documentation reproducibility; evidence retention | See [other workstreams](#other-workstreams) | [Handoff](HANDOFF.md) |
| Re-baseline | Step 3 roadmap re-baseline | Accepted 2026-10-08, `ecad45d8` | This page |
| Next | S1, S2, S3 | S1 authorized 2026-10-16 (`authorize S1, proceed`); the 2026-10-17 [project review](project-review-2026-10-17.md) (`480dab72`; `65fc52e0` superseded) and the [revision plan](s1-te-trigger-revision-plan.md) (`07541c59`) were accepted on 2026-10-18 (`approve 480d 07541`); its three packages were accepted on 2026-10-18 (`I accept RP-1 RP-2 RP-3`): the revised S1 at `fd670dcd` (RP-1; `0fbca0fd` superseded), Model 0.1 plan revision M01-A at `95ef0f6c` (RP-2), and the revised S2 definition at `1ac7080f` (RP-3); S1 is complete; the [S2 plan](s2-security-model-plan.md) was accepted on 2026-10-19 at `5ce7827f` (`accept 5ce782`); [security model v1](security-model-v1.md) was accepted on 2026-10-22 at `0e3eec8b` (`accept 0e3eec8b`), so S2 is complete; S3 was directed on 2026-10-22 (`merge & push, start S3`), and the [MVP plan](mvp-plan.md), revision 1, was accepted on 2026-10-23 at `93967fba` (`accept 93967fba`; `06c35f48` superseded), so S3 is complete. See [planned sequence](#planned-sequence) | [S1 synthesis](he-to-be-synthesis.md), [revision review summary](s1-te-trigger-revision-review-summary.md), [S2 plan review summary](s2-security-model-plan-review-summary.md), [security model v1 record](security-model-v1-review-summary.md), [MVP plan review summary](mvp-plan-review-summary.md) |
| Later | MVP milestones M0 to M4, then implementation-plan milestones 3-10 | The accepted [MVP plan](mvp-plan.md) selects M0 to M4; the [M0 plan](mvp-m0-plan.md) was accepted 2026-10-23 at `4d129808`; M0 is complete and accepted 2026-10-26 at exact commit `b266972563a39b0687ba2ac8c5b4cb943f3c766a` (instruction `accept b26697`) with Plan revisions M0-A, M0-B, and M0-C ([M0 result review and acceptance record](mvp-m0-result-review-summary.md)); M1's plan is accepted 2026-10-26 at `7b2c055c` ([M1 plan](mvp-m1-plan.md), [review and acceptance record](mvp-m1-plan-review-summary.md)), authorizing M1 implementation on `beryllium/mvp-m1`; M1 is implemented through M1-6 with Plan revisions M1-A and M1-B, its second COM260 campaign passed 6 of 6 runs, and exact result commit `ff84533c` is responsible-human accepted 2026-10-27 with Plan revisions M1-A and M1-B ([M1 result review and acceptance record](mvp-m1-result-review-summary.md)); the M2 plan is accepted 2026-10-27 at `854a5415` ([M2 plan](mvp-m2-plan.md), [review and acceptance record](mvp-m2-plan-review-summary.md)), authorizing M2 implementation on `beryllium/mvp-m2`; exact M2 result commit `18d552bc` is responsible-human accepted 2026-10-28 with Plan revision M2-A ([M2 result review and acceptance record](mvp-m2-result-review-summary.md)); the M3 plan is accepted 2026-10-28 at `c2c249f4` ([M3 plan](mvp-m3-plan.md), [review and acceptance record](mvp-m3-plan-review-summary.md)) and its security model v1 Revision 1 at `019cca64`; exact M3 result commit `b0a0f352` is responsible-human accepted 2026-10-28 ([M3 result review and acceptance record](mvp-m3-result-review-summary.md), [M3 evidence record](mvp-m3-evidence.md)); M4, the release candidate, is not started; milestones 3-10 are gated on the MVP; see [later phases](#later-phases) | [MVP plan](mvp-plan.md), [M0 plan review summary](mvp-m0-plan-review-summary.md), [Implementation plan](implementation-plan.md) |

## Planned sequence

Each step needs its own accepted plan or exact-commit decision. None is
authorized until then.

| Step | Scope | Exit |
| --- | --- | --- |
| **3. Re-baseline** (docs only) | Drop KVM0 and R8 H1-H4, keeping their records as history. Make the B-series the K3 path. Make the Helium-to-Beryllium synthesis depend on B-series evidence. List this sequence. | Accepted 2026-10-08 at `ecad45d8` (instruction `accept ecad45`). |
| **B7. Two Linux guests** (plan accepted 2026-10-08; result accepted 2026-10-09) | Two copies of the B6 guest (pinned Linux `v7.2`, uniprocessor, no devices), each with its own 64 MiB window and G-stage. Per-guest vCPU state is saved and restored. Hart 0 switches between the guests round-robin when one idles (its `wfi` traps) and on an HS timer slice, the monitor's first interrupt of its own. Each guest's console output gets its own prefix. Userland: small programs built with Linux's `tools/include/nolibc` from the pinned tree, so no new external input. | Accepted 2026-10-09 at `7b6b846b` (instruction `accept 7b6b84, commit and push`): both guests ran interleaved and powered off, first in QEMU, then in 3 GCC and 1 Clang RAM-only kexec runs on the COM260. |
| **S1. He-to-Be synthesis** (docs; authorized 2026-10-16; revised under the accepted revision plan; accepted 2026-10-18 at `fd670dcd`, instruction `I accept RP-1 RP-2 RP-3`; `0fbca0fd` superseded) | Classify each relevant Helium lesson as adopt, adapt, reject, or defer, against the B0-B7 evidence. Sources: the pathfinder comparison, the TE PoC evidence, and `../helium-te-poc` read at one exact commit. May run alongside B7. | One accepted planning document. |
| **S2. Security model v1** (docs; plan accepted 2026-10-19 at `5ce7827f`, instruction `accept 5ce782`; [document](security-model-v1.md) accepted 2026-10-22 at `0e3eec8b`, instruction `accept 0e3eec8b`) | One document: (1) objects, invariants, the threat model, and the trusted computing base; (2) the policy specification, a central, declarative policy in the Type Enforcement family (types or labels, object classes, permissions, rules) with deterministic and total semantics, default deny, and explicit conflict resolution; (3) the analyses the implementation plan's policy proof targets name: unreachable, contradictory, over-broad, and non-revocable authority, information flow modulo the declared channels, and authority non-amplification; (4) the relation from the policy to the canonical manifest (compile or validate), restoring the plan's pipeline as a goal with the Rocq configuration as its intended consumer; (5) the capability trigger and the runtime-check trigger, evaluated against the platform's use cases under the M01-A wording; (6) the authority ceiling for the dynamic management case; and (7) which of Model 0.2's seam, fixtures, or proofs change, if any. The specification language form is S2's choice. This definition is work package RP-3 of the accepted [revision plan](s1-te-trigger-revision-plan.md), accepted on 2026-10-18 at exact commit `1ac7080f` (instruction `I accept RP-1 RP-2 RP-3`); the prior definition read "objects; authority from a sealed static manifest, with ownership plus explicit channels; invariants; threat model; trusted computing base; and whether the platform's use cases fire the capability or TE triggers". The accepted S2 plan authorized writing this document only, as work packages S2-1 to S2-7. | Accepted 2026-10-22 at `0e3eec8b` (instruction `accept 0e3eec8b`), with V1 to V4 at their defaults: one accepted document. |
| **S3. MVP plan** (directed 2026-10-22 by `merge & push, start S3`; [plan](mvp-plan.md) revision 1 accepted 2026-10-23 at `93967fba`, instruction `accept 93967fba`; `06c35f48` superseded) | The initial security-research-platform release: scope, non-goals, milestones, evaluation harness, evidence claims, and release path. Revision 1 (2026-10-23) puts each domain on its own hart with a dedicated control hart, three of the COM260's eight harts under static ownership, and removes the scheduler; M0 builds that substrate. | Accepted 2026-10-23 at `93967fba` with Q1 to Q12 at their defaults: one accepted plan. It authorizes writing M0's bounded plan only. |
| **M0. The MVP line, the multi-hart substrate, and the harness** ([plan](mvp-m0-plan.md) revision 2 accepted 2026-10-23 at `4d129808`, instruction `accept 4d129808, proceed with implementation using opus-5.5 model`; `6e4b9d4a` and `d95b28e9` superseded; implementation on `beryllium/mvp-m0` stopped at M0-3 by stop condition 3 and resumed under Plan revision M0-A, directed 2026-10-23) | One maintained tree `mvp/` seeded from B7; a tool lock and a digest-pinned evaluator; scenarios as data with B7's two-guest scenario on two domain harts; the control hart, SBI HSM hart start, a boot barrier, single-writer rings, SBI IPIs, native `wfi`, no scheduler; hart IDs as configuration; a K3 platform record from probe and negative images. | Plan accepted; next, an exact result commit and packet. |

The first MVP milestone is M0, the MVP line, the multi-hart substrate, and
the evaluation harness; its bounded [plan](mvp-m0-plan.md) was accepted at
`4d129808` on 2026-10-23, and its implementation is in progress. The
Helium TE PoC scenario on two
Linux guests, each on its own hart, is M1: a writer and a reader share one
page, the reader cannot write it, private memory is denied, and the
monitor injects the faults and logs each denial. Security model v1 writes
it as its Instance 2, the policy from which the shared page's authority is
derived.

A richer guest userland, such as a static BusyBox with musl for interactive
demos, needs two new pinned source inputs and guest console input, which
B6's SBI subset refuses. The accepted MVP plan leaves it out of MVP 1.0
(D5); Plan revision S3-C (accepted 2026-11-01 at `27d2e557`) reverses
D5 with milestone M7, interactive guests, beside M8 (the first
verification plan), M9 (measurement), and M10 (release candidate 4).
M7 is complete and accepted (2026-11-02, `e1a6395e`; the
[M7 result review and acceptance record](mvp-m7-result-review-summary.md),
the [M7 evidence record](mvp-m7-evidence.md)): a pinned BusyBox and
musl userland, console input routed by a focus sequence to a granted
domain, scripted sessions judged in QEMU, and one typed characterization
on the COM260. The [M8 plan](mvp-m8-plan.md), the first verification
plan, is accepted at `7a0c74ae` (2026-11-02; M8-2 to M8-7 authorized on
`beryllium/mvp-m8`), its specification accepted at `004f31ae` the same
day, M8-2 to M8-5 complete and M8-6 in progress, and the development
branch fast-forwarded to the M8 line; the [M9 plan](mvp-m9-plan.md),
measurement, is accepted at `4f4a8f76` (2026-11-03, its second candidate
after the steering review the human directed; M9-2 to M9-6 authorized on
`beryllium/mvp-m9`).

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

- **Documentation reproducibility:** exact 24-path target
  `7cf4c4a1dff0b3f2dac2c692a2f1d2398ff6771e` is accepted as of 2026-09-30
  for the selected Nimbus environment only. It stays on local branch
  `beryllium/doc-repro-option-a-20260929`, unpushed and not integrated, with
  no cross-host or future-package guarantee.
- **Evidence retention:** Option A Phase 1 read-only inventory is complete.
  Phase 2 is blocked; no store exists, and its decision packet has SHA-256
  `94a780ee271f23de1785fed03f5a14f89a713912f60047afd83e06d3bee0b106`.

## Gates and boundaries

- **Development kernel/BSP:** undecided and not needed for MVP 1.0: the
  guests see no devices and use the pinned upstream kernel as an external
  test input, and no Linux runs on the bare board under Beryllium
  (accepted MVP plan D2).
- **Board safety:** RAM-only loading, output-only serial capture, no
  persistent firmware, U-Boot environment, flash, or boot-configuration
  change, and human-performed resets and power-off. Automation typed at
  U-Boot only under B6's own direction; a later milestone needs its own.
- **Root integration:** `bringup/` and `tests/unit` are outside the root
  `Makefile`, `be`, and `scripts/check-be.sh`, which carry predecessor
  acceptance pins. Integration needs separate direction.
- **Branches:** the development branch `beryllium/single-hart-runtime-r0`
  holds B0-B7, the tool fixes, and this re-baseline. On 2026-10-09 the
  instruction `accept 7b6b84, commit and push` authorized pushing
  `beryllium/k3-b7-bringup` (the accepted B7 plan and result), through the
  B7 acceptance record, to the private `origin`, plus the
  `beryllium/k3-b6-bringup` (B6) and `beryllium/roadmap-rebaseline` (this
  re-baseline) refs, whose commits are ancestors of the B7 branch; the B7
  worker branches stay local. On 2026-10-13 the direction
  `proceed with these in fleet mode. fast-foward.` fast-forwarded the
  development branch from `3bc3ef04` to `80ef261e`, the B7 branch tip, and
  the responsible human then pushed it and the B7 branch to the private
  `origin` (`push the beryllium backup`). On 2026-10-16 the form answer
  `fast_forward=ff-push` authorized fast-forwarding the development branch
  to the B7 branch tip, through the commit that records the `PMR-090`
  owner return, and pushing both; the form answer
  `accepted_r8_branch=backup` authorized pushing
  `beryllium/r8-c-h0-pmr-081-v3`, which holds the accepted R8 H0 target
  and its review and acceptance commits, as a backup. `PMR-090` retired
  the superseded, unaccepted PMR-080 candidate `6e93461f`: it is never
  pushed, and its local branch stays. On 2026-10-18 the instruction
  `fast-forward dev to 0eb37570 and push` fast-forwarded the development
  branch from `56e36ae1` to `0eb37570`, the acceptance record of RP-1 to
  RP-3, and pushed it to the private `origin`; the development branch now
  holds S1, the project review, the revision plan, M01-A, and the S2
  definition, all accepted. On 2026-10-22 the instruction
  `merge & push, start S3` fast-forwarded the development branch from
  `0eb37570` to `0096de3e`, through the acceptance record of security model
  v1, and pushed it to the private `origin`; it now also holds the
  accepted S2 plan and security model v1, and the S2 branch ref
  `beryllium/s2-security-model` stays local. The S3 branch
  `beryllium/s3-mvp-plan`, from `0096de3e`, holds the superseded first
  candidate `06c35f48`, its packet, the accepted revision 1 at
  `93967fba`, its review and acceptance record, and the acceptance-record
  follow-up `1fb46419`. On 2026-10-23 the instruction `sure. update
  that, then proceed with (a) and continue development` fast-forwarded
  the development branch from `0096de3e` to `1fb46419` and pushed it and
  `beryllium/s3-mvp-plan` to the private `origin`; local and `origin`
  agree at `1fb46419`. The M0 plan branch
  `beryllium/mvp-m0-plan`, from `1fb46419`, holds the accepted M0 plan,
  its superseded candidates, and its review and acceptance record; the
  M0 implementation branch `beryllium/mvp-m0`, from that record, holds
  the `mvp/` tree with Plan revisions M0-A and M0-B. On 2026-10-24 the
  instruction `push, I will work on this later when k3 is available`
  authorized pushing both to the private `origin` as a backup, through
  the commit recording the push. Any further merge into the
  development branch and any other push each need an explicit
  instruction.
- **Publication:** public push, tag, public release, clean-repository
  migration, paper submission, and upstream submission remain blocked.
  Automation cannot approve publication, add a human `Signed-off-by`, or
  change `pathfinder/publication-gate.conf` to grant approval.

## Open engineering risks

| Risk | Current evidence | Required response |
| --- | --- | --- |
| Board results read as hardware validation | B0-B7 ran on one COM260 with one firmware stack. | Call them diagnostic bring-up evidence and scope every claim to the exact board, firmware, tools, and procedure. |
| Bring-up copies drifting from the accepted core | `bringup/k3-b1` to `k3-b7` reuse accepted R-series code through generators and copies outside the root build. | Keep the port tables counted; the accepted MVP plan keeps the MVP line self-contained (D3) and ends the copy chain with one maintained tree in M0. |
| Unpinned workstation tools | Bring-up milestones build with unpinned host tools; the accepted R6 and R7 tool locks fail on this host's Node.js version. | Record tool versions with each result; the accepted MVP plan's M0 delivers a tool lock the development host can satisfy. |
| Helium learning not yet applied | The pathfinder comparison predates the Helium fork and all K3 evidence. The accepted [S1 synthesis](he-to-be-synthesis.md) (`fd670dcd`) classifies Helium's lessons against B0-B7; the accepted [security model v1](security-model-v1.md) (`0e3eec8b`) cites its rows. | The accepted [MVP plan](mvp-plan.md) applies the S1 and S2 hand-offs; each milestone plan carries its rows forward. |
| Open audit findings | Low-severity findings S5-S8 and S10 remain open; R4's 3 s QEMU budget fails on slow hosts. | Fix under separate direction; outside MVP 1.0 (accepted MVP plan D11). |
| Generated-asset reproducibility | Browser, link, and static gates work; independent byte identity remains open. | Pin and compare generator inputs, or define a bounded semantic reproducibility claim. |
| Publication and provenance erosion | The GPL-3.0-only internal history is not Linux-ready or approved for public release. | Use exact human review, license and provenance resolution, publication checks, and a new clean repository. |

## Later phases

These are [implementation plan](implementation-plan.md) milestones 3-10.
The accepted S3 MVP plan selected M0 to M4 first, S3-A and S3-B added M5
and M6, and all are accepted; each phase here then needs its own bounded
plan and authorization after MVP 1.0. Plan revision S3-C (accepted
2026-11-01 at `27d2e557`) places measurement in MVP 1.0 (M9) and names
MVP 2.0 (the device path and service domain, dynamic management, the
policy questions H06 to H09, attestation with a simulated root of
trust), 3.0 (MPT, CoVE, CHERI, policy composition), and 4.0 (general
guests) as the rungs after it; each rung still needs its own bounded
plan and authorization.

| Phase | Goal | Key non-goal |
| --- | --- | --- |
| One protected domain and OS boundary | A Linux management domain plus a protected domain; guest SBI, hypercall, notification, lifecycle, restart, failure, and measurement boundaries. | No general cloud/VMM product, broad guest SBI, or accidental stable UAPI. |
| Serialized multicore | Static CPU ownership, per-core fast paths, and one bounded serialized lifecycle, ownership, and invalidation path. The accepted MVP plan takes the static part (one domain per hart, a control hart) into MVP 1.0 and leaves the dynamic part here. | No fine-grained locking, work stealing, or shared run queue. |
| I/O service and DMA containment | One restartable service/device class with interrupt, reset, IOMMU/IOPMP, cache, and DMA ownership. | No generic device framework or whole-platform DMA claim. |
| Policy triggers | Capabilities only for delegation, attenuation, transfer, or revocation needs; a runtime TE check only for an independent mandatory denial. Under M01-A, the TE-family policy specification comes from S2 and is not trigger-gated. | No policy framework in the core or selection by preference. |
| Measured launch and attestation | Bind exact core, configuration, and domain artifacts to explicit roots of trust and update/replay rules. | Current Model identities are not measurements or attestation. |
| Assurance and source-to-binary | Selected refinement, binary correspondence, coverage, traceability, and deployment crosswalks using open normative tools. | No umbrella "formally verified Beryllium" or certification claim without an evaluator. |
| Clean public migration | A new clean Beryllium repository with selected reviewed source and artifacts, then upstream or foundation disposition. | No direct publication of internal history or automated release approval. |
| MVP core profile | Replace the fixed-profile prelude the MVP line still runs with an inventory of the MVP's real layout (control hart, domain harts, hart region, MVP region, pools, windows) and drop the unused fixture roots and pages; recorded structural debt from B5-M0 (M0 Plan revision M0-A.5), deferred by the accepted MVP plan (D3) and S1 H22. | M6 and release candidate 3 before the release path's steps 2 to 7 (the human's direction of 2026-10-30; Plan revision S3-B `f8b77ac9` and the [M6 plan](mvp-m6-plan.md) `b2c62d54` accepted 2026-10-30; **retired**: release candidate 3, exact commit `89ef04e9` over `X3` `ebc49a88`, accepted 2026-10-31, the boot validating, sealing, and deriving the MVP's own configuration; the model instance of that configuration is deferred to the first verification plan, ledger U-13); the clean-repository build root stays a migration design. |

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
roadmap_status_date=2026-10-22
roadmap_rebaseline=step3-accepted
roadmap_rebaseline_target=ecad45d8eb371218d6f9a0965b330fa5043ea273
roadmap_rebaseline_acceptance_instruction=accept-ecad45
roadmap_rebaseline_acceptance_date=2026-10-08
roadmap_previous_accepted_target=a9bb91df94f7e1df2b0e7f2d3ca057f6516ea511
active_path=k3-bringup-b-series
k3_bringup_accepted=B0,B1,B2,B3,B4,B5,B6,B7
b6_accepted_target=e20c55df57551244eab47e0eff59d4c71fe75d20
next_sequence=S1,S2,S3
s1_authorization=authorize-S1-proceed
s1_target=fd670dcd54ff4f2c66349d377be914698b9dda3b
s1_status=accepted
s1_acceptance_instruction=I-accept-RP-1-RP-2-RP-3
s1_acceptance_date=2026-10-18
s1_superseded_candidate=0fbca0fdc7b9ecca2aaf6635bb04a3335bca72ef
project_review_2026_10_17=accepted
project_review_target=480dab72de7a74f8b84c64c2fefee8190cb87b70
project_review_acceptance_instruction=approve-480d-07541
project_review_acceptance_date=2026-10-18
project_review_superseded_candidate=65fc52e0b06fc60691669f75d44a1cc9356ac4c0
project_review_rerun_date=2026-10-18
s1_te_trigger_revision_plan=accepted
s1_te_trigger_revision_plan_target=07541c59426865ce8b1eef3c409913923cd5e64b
s1_te_trigger_revision_plan_acceptance_instruction=approve-480d-07541
s1_te_trigger_revision_plan_acceptance_date=2026-10-18
s1_te_trigger_revision_packages=RP-1,RP-2,RP-3
s1_te_trigger_revision_packages_status=accepted
s1_te_trigger_revision_packages_acceptance_instruction=I-accept-RP-1-RP-2-RP-3
s1_te_trigger_revision_packages_acceptance_date=2026-10-18
rp1_target=fd670dcd54ff4f2c66349d377be914698b9dda3b
rp2_target=95ef0f6c0fc1fe457e93b7d34b48cde5a411e8ab
rp3_target=1ac7080f3375dfbfb8358706db767a8a89678a78
model_0_1_revision_m01a=accepted
s2_definition=revised-rp3-accepted
s2_plan=accepted
s2_plan_target=5ce7827f9c2ffc6e0f88568692ab238e5feca49f
s2_plan_direction_instruction=then-proceed-with-S2-plan
s2_plan_acceptance_instruction=accept-5ce782
s2_plan_acceptance_date=2026-10-19
s2_plan_q1_answer=A-notation-defined-in-document
s2_authorization=authorized-by-accepted-plan-documentation-only
s2_document=accepted
s2_document_target=0e3eec8b4fd74003f8cedbf2ca66871c31412624
s2_document_acceptance_instruction=accept-0e3eec8b
s2_document_acceptance_date=2026-10-22
s2_document_open_questions=V1-V4-defaults
s3_direction_instruction=merge-and-push-start-S3
s3_direction_date=2026-10-22
s3_authorization=directed-plan-documentation-only
s3_plan=accepted
s3_plan_revision=1
s3_plan_revision_date=2026-10-23
s3_plan_target=93967fbac926b4fdfdfe636df4d07e8926b625b7
s3_plan_acceptance_instruction=accept-93967fba
s3_plan_acceptance_date=2026-10-23
s3_plan_open_questions=Q1-Q12-defaults
s3_plan_superseded_candidate=06c35f4829f14b4896a5cc46dee77ed8bee0ef9d
s3_plan_concurrency=static-hart-ownership-with-control-hart
mvp_milestones_authorization=m0-bounded-plan-only
m0_plan=accepted
m0_plan_revision=2
m0_plan_acceptance_instruction=accept-4d129808-proceed-with-implementation-using-opus-5.5-model
m0_plan_acceptance_date=2026-10-23
m0_plan_open_questions=Q1-Q13-defaults
m0_plan_target=4d129808979cb54b7e0a7cc0b3e79d39533e0b9c
m0_plan_superseded_candidates=6e4b9d4a1e2da249d68aeb4e1aea5a27cf3755f8,d95b28e953bccbdd489b1e6eec69d48fa028fd29
m0_plan_base=1fb464199dc5ace11c77e4697ff5e13a35f21434
m0_implementation_authorization=M0-1..M0-6-under-accepted-plan
m0_implementation_branch=beryllium/mvp-m0
m0_result=accepted
m0_result_acceptance_instruction=accept-b26697
m0_result_acceptance_date=2026-10-26
m0_result_target=b266972563a39b0687ba2ac8c5b4cb943f3c766a
m0_result_parent=13992d6d902131a6c19978b620724fad0524256f
m0_result_record=mvp-m0-result-review-summary.md
m0_plan_revisions_accepted_with_result=M0-A-30c5e1a8;M0-B-77559def;M0-C-260ceba6
m0_status=M0-1..M0-6-complete;board-campaign-2-8-of-8-pass;gates-pass-at-13992d6d-clean-tree;result-accepted-b2669725
m0_head=b2669725
m1_plan=accepted
m1_plan_acceptance_instruction=accept-7b2c055c
m1_plan_acceptance_date=2026-10-26
m1_plan_target=7b2c055c1587f9582812a575b296cd625746662b
m1_plan_base=6f7b6e7c1fd609299fd88af164d400da3d6435ae
m1_plan_branch=beryllium/mvp-m1-plan
m1_plan_record=mvp-m1-plan-review-summary.md
m1_plan_open_questions=Q1-Q19-defaults
m1_implementation_authorization=M1-1..M1-6-under-accepted-plan
m1_implementation_branch=beryllium/mvp-m1
m1_implementation_status=M1-1-b591b187;M1-2-0174f7a8;M1-3-d3d28d7e;M1-4-65648204-under-M1-A;M1-5-9020c4f8;M1-B-745c293a-804cd24c;M1-6-17ed82f7;result-ff84533c;gates-pass-at-17ed82f7-clean-tree
m1_board_20261027_first=preflight-pass;load-checks-pass;te-poc-4-of-4-pass;reader-write-pass-as-declared;no-inject-stop-6-both-domain-harts-took-q10-fallback;images-9020c4f8;record-of-the-stop-not-evidence
m1_board_20261027_m1b=preflight-pass;te-poc-load-checks-pass;te-poc-4-of-4-pass-exits-163-167-denials-1-2-records-146-alternations-127;reader-write-and-no-inject-pass-as-declared;no-inject-one-fail-detail-pair-from-hart-0;k3ctl-resets-6-of-6-33-to-47s;images-17ed82f7;record-mvp/results/20261027-com260-m1b
m1_plan_revision_m1a=directed-2026-10-27-A;child-of-init-makes-denied-accesses;00051fc4;acceptance-with-result-packet
m1_plan_revision_m1b=directed-2026-10-27-accept-B-proceed;domain-hart-ack-wait-restarts-on-hart-0-progress;745c293a-804cd24c;acceptance-with-result-packet
m1_stop_6=qemu-m1-4-linux-v7.2-prints-unhandled-signal-for-pid-1-despite-handler-resolved-by-M1-A;board-m1-5-no-inject-q10-window-measured-hart-0-latency-resolved-by-M1-B
m1_k3_access=released-by-human-2026-10-27-01:25;used-for-both-campaigns
m1_result=accepted-ff84533cb3c13d89063be77652575347c2a82757;parent-17ed82f7;2026-10-27;instruction-approve-ff84533c-and-revisions-accept-your-recommendations-authorize-proceeding-per-those;record-mvp-m1-result-review-summary.md
m2_plan=accepted
m2_plan_acceptance_instruction=accept-854a5415-gpl-2.0-only-ok
m2_plan_acceptance_date=2026-10-27
m2_plan_target=854a54152502c4c9a14fe2d1897d907a358a8251
m2_plan_base=ccf70a3d3e9ab716ba52e055ccc7882179b50d04
m2_plan_branch=beryllium/mvp-m2-plan
m2_plan_record=mvp-m2-plan-review-summary.md
m2_plan_open_questions=Q1-Q19-defaults;Q20-answered-gpl-2.0-only-ok
m2_implementation_authorization=M2-1..M2-7-under-accepted-plan
m2_implementation_branch=beryllium/mvp-m2
m2_implementation_status=M2-1-f149eea0;M2-2-d6667862;M2-3-2d23efe4;M2-4-51893419-f687b791;M2-5-da7d270f;M2-A-adc989fa-ac0d48dd;M2-7-e021e7ec-397670e5;result-18d552bc;gates-pass-at-397670e5-clean-tree
m2_board_20261028_first=preflight-pass;anchor-load-checks-pass;anchor-run-1-reached-shutdown-stop-6-ipi-probe-spv-0-in-mgmt-wait;checker-expectation-not-monitor;record-of-the-stop-not-evidence
m2_board_20261028_m2a=anchor-4-of-4-pass-exits-248-132-denials-4-1-mgmt-13-2-records-174-alternations-122;wrong-measurement-and-no-grant-check-pass-as-declared;positive-run-3.92s-70-percent-of-2^27;k3ctl-resets-6;run-1-reset-boot-without-network-stop-9;human-reset-resume;one-hand-reset
m2_stop_6=board-m2-6-anchor-ipi-probe-served-in-hs-wait-q14-resolved-by-M2-A
m2_stop_9=board-m2-6-reset-returned-board-without-ipv4-tool-stop-10;human-authorized-second-reset-and-resumption
m2_k3_access=confirmed-free-by-human-2026-10-27-19:30-PDT
m2_result=accepted-18d552bc4cf3a463bc4dc491e5e346989e5a521c;parent-397670e5;2026-10-28;instruction-accept-18d552bc;record-mvp-m2-result-review-summary.md
m2_plan_revision_m2a=directed-2026-10-28-remedy-A-reset-board-true;checker-accepts-spv-0-only-inside-mgmt-wait-of-same-hart;adc989fa-ac0d48dd;harness-only;accepted-with-result-18d552bc-2026-10-28
m3_plan=accepted
m3_plan_target=c2c249f4c3d364590d2e505a4f6fb5e65456ff81
m3_plan_acceptance_instruction=accept-c2c249f4
m3_plan_acceptance_date=2026-10-28
m3_plan_first_candidate=9952e765-superseded
m3_plan_branch=beryllium/mvp-m3-plan
m3_plan_record=mvp-m3-plan-review-summary.md
m3_plan_open_questions=Q1-Q12-defaults
m3_plan_limits=soft;stop-5-reevaluation;human-direction-2026-10-28
m3_plan_review=gpt-5.6-sol-2026-10-28-human-authorized;12-findings-incorporated
m3_implementation_authorization=M3-1-under-accepted-plan;M3-2..M3-6-after-revision-accepted
m3_implementation_branch=beryllium/mvp-m3
m3_implementation_status=M3-1-accepted-019cca64971d2399faba3d768d6f5b1fc9145198;2026-10-28;instruction-accept-019cca64;first-candidate-32298add-superseded;record-security-model-v1-revision-1-review-summary.md;M3-2..M3-6-starting
security_model_v1_revision_1=accepted-019cca64-2026-10-28
m3_2_status=complete-0e05d338;stop-6-remedy-A-host-and-lock-nodejs-22.23.1;check-and-evaluate-pass;lock-gcc-16.2.1-clang-22.1.8-node-22.23.1-python-3.14.8-rocq-9.3.0
m3_3_status=complete-dadc6f63-cef9fad5;rocq-3044-lines;T1-T5-H0-H3;22-closed-reports;stop-5-rocq-limit-6000
m3_4_status=complete-83e850d0-6055b55a-6cfbc9ff;c-3448-lines;169-checks-gcc-eq-clang;stop-5-c-limit-6000;instance-1-two-way
m3_5_status=complete-d35813c7;91-mutations-seed-73;differential-pass-three-way-73-two-way-22-comparisons-241
m3_6_status=complete-b0a0f352;model-check-and-evaluate-pass-at-d35813c7-clean-tree-2026-10-28
m3_result=accepted-b0a0f352d7969a8f8cf28cf0d25b89fc372e70f2;parent-d35813c7;2026-10-28;instruction-accept-b0a0f352;record-mvp-m3-result-review-summary.md
m3_push=2026-10-28;instruction-push-all-work-then-proceed-with-1-and-2;mvp-m3-and-mvp-m3-plan-to-private-origin;dev-ff-50b77c00-to-m3-acceptance-record-and-pushed
m4_plan=accepted-0d02df725541e4e8f93b3fc3de002358827aa1da;parent-95fc0123;2026-10-28;instruction-accept-0d02df27-authorize-M4-read-as-accept-0d02df72;branch-beryllium/mvp-m4-plan;record-mvp-m4-plan-review-summary.md
m4_plan_first_candidate=91f4a820-superseded
m4_plan_review=gpt-5.6-sol-2026-10-28-session-sop;9-findings-incorporated;hook-edited-and-restored
session_sop_2026-10-28=gpt-5.6-sol-max-long-context-reviews-planning-steps
m4_plan_open_questions=Q1-Q13-defaults-unless-answered;flagged-Q2-board-Q6-claim-Q5-review-Q1-location
m4_plan_board=rc-campaign-11-runs-two-guests-te-poc-only-after-human-confirms-k3-free;anchor-if-images-differ-from-m2a;alternatives-none-or-17
m4_implementation_authorization=M4-1..M4-6-on-beryllium/mvp-m4-from-acceptance-record;2026-10-28;board-only-after-human-confirms-k3-free
m4_implementation_branch=beryllium/mvp-m4
m4_release_steps_authorized=none
m4_implementation_status=complete-2026-10-29;X-d42b9ec0a6d2f9f32d66ec2a983018e802b2d537;R-c5df0cfae26ce5529cd1ef112911063fcf5b56d8;gates-pass-at-X;board-11-of-11-at-X-images;anchor-via-M2-A-byte-identity
m4_result=accepted-c5df0cfae26ce5529cd1ef112911063fcf5b56d8;parent-X-d42b9ec0a6d2f9f32d66ec2a983018e802b2d537;2026-10-29;instruction-accept-c5df0cfa-commit-and-push;record-mvp-m4-result-review-summary.md
m4_push=2026-10-29;mvp-m4-and-mvp-m4-plan-to-private-origin;dev-stays-fb8accc9
mvp_1_0_milestones=M0-M5-accepted
release_path=step-1-holds-for-rc3-89ef04e9;steps-2-7-not-started-each-needs-instruction;s3c-accepted-they-follow-rc4
m4_plan_revision_m4a=directed-2026-10-29;implemented-0b2ac6fa;accepted-with-result-c5df0cfa
m4_errata=1-code-limit-2000
s3a_plan_revision=accepted-0d134bbc49377576b961989831a02c068b479355;2026-10-29;boot-from-system-reset;board-policy;rc-staging;D17;standing-rule-no-kexec-without-approval
m5_plan=accepted-0066794dbec22807d46cc274f2ad00fb79b555ae;2026-10-29;instruction-accept-0d134bbc-and-066794d-authorize-m5;Q1-Q16-defaults;record-mvp-m5-plan-review-summary.md;acceptance-record-9b3fa982
m5_implementation_branch=beryllium/mvp-m5
m5_errata=1-code-limit-10000-after-stop-8-at-6865
m5_partition=made-by-human-2026-10-30;p6-ext4-beryllium-1GiB-from-p3;tool-exit-5-orphan_present-benign-fixed-f3a04a86
m5_characterization=passed-attempt-7-2026-10-30;six-stopped-on-bsp-facts;md5sum-witness-crc32-silent;systemctl-reboot-shutdown;no-saveenv
m5_gates=pass-at-X2-6dd81ee39dd620a1815605c50c9c916894c9974c-clean-2026-10-30;images-253-identical;uboot-rehearsal-7-cases;record-mvp/results/20261030-rc2-430-files
m5_board_20261030=session-20261030-com260-rc2;boot-from-reset-20-of-20-at-X2-images;install-and-restore-human-present;record3-eq-record1;stop-12-select-04-lost-s-hardened-0bfb1ca8-resumed;41-k3ctl-resets;record-mvp/results/20261030-com260-rc2-198-files
m5_result=accepted-3867c66c5df2108e1051d8f8c44c12d62611e485;parent-X2-6dd81ee39dd620a1815605c50c9c916894c9974c;2026-10-30;instruction-accept-3867c66c;record-mvp-m5-result-review-summary.md;evidence-mvp-m5-evidence.md
m5_code_lines=7439-of-10000
m5_push=2026-10-30;instruction-approve-1-3;mvp-m5-through-push-record-and-mvp-m5-plan-9b3fa982-to-private-origin;dev-ff-fb8accc9-to-push-record-and-pushed
mvp_debt_sweep_1=accepted-80ef8a13110525d8e3f9dfb19f5818a8f2dfbe64;base-466c29f4;2026-10-30;instruction-proceed-with-push-and-accept-80ef8a13;items-83-85-86-closed;item-80-human-by-hand;branch-beryllium/mvp-debt-1
m5_ledger_fix=466c29f4;item-86;acceptance-record-db2c0bab-broke-C-10-pin-of-m5-plan;check-failed-at-52092935;pushed-2026-10-30
development_branch_tip=debt-sweep-3-acceptance-record-2026-11-01;ff-on-instruction-accept-3b7ab0e3-fast-fwd-push;holds-rc3-89ef04e9-debt-sweeps-1-2-3-snapshot-support-and-update-policy-recheck-item-80-closure;pushed-to-the-private-origin-on-the-same-instruction
m7_push=2026-11-02;instruction-ff-+-push-M7;dev-ff-f5dc770b-to-the-push-record-over-1b3f2e10;mvp-m7-through-the-push-record-and-mvp-m7-plan-ae3e9537-to-private-origin;mvp-m8-plan-stays-local
mvp_item_80=closed-2026-10-31;accepted-36a5ff0b4ca481094b0fdf63f2c8cb1932bd7cd8;dongle-power-line-and-reset-do-not-power-on-after-software-poweroff;pins-5-6-unbridged;power-cycle-by-the-human-is-the-recovery
mvp_release_candidates=rc1-c5df0cfa-accepted-history;rc2-3867c66c-accepted-history;rc3-89ef04e9354c08ebadbaeb88d553c5081a00b84d-over-X3-ebc49a88-accepted-2026-10-31-instruction-accept-89ef04e9-proceed
s3c_plan_revision=accepted-27d2e557f069edf8dd714f5ac9b5ccb9b204a801;2026-11-01;instruction-accept-27d2e557-defaults-ff-push;Q27-Q46-defaults;authorizes-M7-M8-M9-plans-then-M10-after-their-results;none-started;branch-beryllium/mvp-s3c-plan-merged-with-dev-44112dec;record-mvp-plan-s3c-review-summary.md;parent-81c5e0b6;first-candidate-95c9ab24-superseded-reviewed-by-copilot-cli-codex-cli-claude-code;reconciliation-mvp-plan-s3c-review-reconciliation.md-rows-A-AQ;branch-beryllium/mvp-s3c-plan-holding-dev-b53c02a8-by-merge;2026-11-01;the-ladder-MVP-1.0-to-4.0;M7-interactive-guests;M8-first-verification-plan;M9-measurement;M10-rc4;D19-D22-amended;stop-1-amended-by-name;S3-A.1-item-8;Q27-Q46-defaults;packet-mvp-plan-s3c-review-summary.md;authorizes-nothing
m7_plan=accepted-4f4d094efb3985435673f7bda62f35ad51c6165e;base-f5dc770b;2026-11-01;instruction-accept-4f4d094e;Q1-Q16-defaults;branch-beryllium/mvp-m7-plan;record-mvp-m7-plan-review-summary.md;soft-limit-8000;board-typed-characterization-only;no-ff-no-push-directed
m7_implementation=authorized;M7-2..M7-6-on-beryllium/mvp-m7-from-the-acceptance-record;started-2026-11-01;coding-claude-opus-5.5
m7_result=accepted-e1a6395e038d4dd095960f7a942a87399bdbce18;parent-8418a377-gates-commit;2026-11-02;instruction-accept-e1a6395e-move-k3ctl-pin-to-v1.1;pin-part-reversed-stop-keep-k3ctl-pin-where-it-was-for-now-clone-a-copy-if-needed;branch-beryllium/mvp-m7-unpushed;record-mvp-m7-result-review-summary.md;evidence-mvp-m7-evidence.md;gates-PASS-at-8418a377-06:14-06:39-UTC;board-20261102-com260-m7-class-supplies-one-shell-session-PASS;code-lines-9092-of-9500-erratum-1;ratio-2.083;departures-18;erratum-2-item-112;k3ctl-pin-unchanged
m8_plan=accepted-7a0c74ae329c09282c5cf159076f5e99934ac4c2;base-1b3f2e10-M7-acceptance-record;2026-11-02;instruction-accept-7a0c74ae-wuth-CN-go-for-m9;Q10-with-CN;Q1-Q9-Q11-Q17-defaults;branch-beryllium/mvp-m8-plan-unpushed;record-mvp-m8-plan-review-summary.md;soft-limits-model-6000-bridge-3000-glue-2500;stops-12
m8_implementation=complete-through-M8-7;result-accepted-12b0e71b908e36041745601d214c03a5be34ad1e;gates-commit-f181384192bd4a79df52ba7cdb5dfbed55ab3307;2026-11-04;instruction-accept-12b0e71b;outcome-inconclusive-D-7;claim-unchanged;ledger-C-51-C-55-U-16-review-item-3;seven-gates-PASS-verify-13480s;specification-004f31ae-revision-1-93a8d136-errata-S-1-S-5-R1-1-R1-9;stage-1-26-theorems;litmus-5-never;qualified-6-of-9;WP-OPEN-130-134;CN-OPEN-5-55;CBMC-leaf-A-SUCCESSFUL-336;ring-OPEN-13547-14931;no-board;packet-mvp-m8-result-review-summary.md;evidence-mvp-m8-evidence.md
m9_plan=accepted-4f4a8f760a1ed7e5f9886b4e02e94b7a849bfc33;second-candidate;parent-d470fb7f;first-candidate-86f1c68b78e2d36920ea53721ce80bbb91a7328b-superseded;base-6fbcc3d1-M8-acceptance-record;2026-11-03;instruction-accept-4f4a8f76;Q1-Q19-defaults-Q17-answered;steering-review-gpt-6-astra-text-mvp-m9-plan-review-gpt-6-astra.md;branch-beryllium/mvp-m9-plan;record-mvp-m9-plan-review-summary.md
m9_implementation=complete;result-accepted-892b68c81dace15d2357e034e859b3eccd130abc;parent-461e9e6f;gates-commit-dc07f7d302e01fb622b53e268f2182c991b0f3e6;2026-11-03;instruction-accept-892b68c8;seven-gates-PASS;counted-lines-9812-of-10000-erratum-1;Part-1-Revision-3-accepted-4bc079db;erratum-2-Q13-citation;probe-not-performed;correlation-boot-not-run;no-board-command;no-ff-no-push-directed;packet-mvp-m9-result-review-summary.md;evidence-mvp-m9-evidence.md
integration_2026_11_04=dev-fast-forwarded-to-the-M9-line-680b6241;the-M8-line-0d103a38-merged;M8-ledger-rows-renumbered-C-51..C-55-to-C-54..C-58-and-U-16-to-U-18;item-124-closed;on-the-human's-go-with-ff-and-push;gates-at-331a0e9a-lock-check-claim-ledger-evaluate-pass;model-check-fails-by-design-at-stage-1-readings-until-M10-item-127;dev-pushed-at-331a0e9a-with-beryllium/mvp-m8-mvp-m9-mvp-m9-plan
m10_plan=accepted-600b78c5198c7462ca76fdb30113f3770fdf5fa7;2026-11-04;instruction-accept-600b78c5;Q1-Q15-defaults;branch-beryllium/mvp-m10-plan;base-c59003e7;record-mvp-m10-plan-review-summary.md
m10_implementation=authorized;M10-2..M10-7-on-beryllium/mvp-m10-from-the-acceptance-record;started-2026-11-04;coding-claude-opus-5.5;board-campaign-after-the-human's-confirmation-and-presence
m10_result=accepted-d70a8535474a690920ff152e7b38a25c589adba9;parent-f3f8c8d8;X4-a6eaa88501b1d08b9e83c734d692c82376117e77;2026-11-05;instruction-accept-d70a8535;record-mvp-m10-result-review-summary.md;evidence-mvp-m10-evidence.md;release-path-step-1-holds
m10_result_gates=eight-PASS-at-X4;verify-wall-13254;rc-record-files-641;exact-RC4-check-PASS
m10_result_board=25-of-25-PASS;19-groups;3-sessions;record-20261105-com260-rc4-files-314;environment-restored;preflights-equal;board-free-on-Fedora
security_model_v1_revision_3=accepted-4bc079dbb96540cb44008a53df857701696e9bad;2026-11-03;instruction-accept-4bc079db;M9-2;D-8;packet-security-model-v1-revision-3-review-summary.md;I19-I20;measurement-asset-instantiated;running-vs-offline-evidence-TCB;additive-252-lines
mvp_ladder_direction=2026-10-31;measure-first-then-attest;IMA-never;simulated-root-of-trust-in-2.0;systemd-measured-boot-and-ammutable-analysed-where-applicable;litebox-re-analysed-for-2.0-sidebar-disposition-stands;k3-mini-itx-expected-for-2.0
s3b_plan_revision=accepted-f8b77ac94fc6b5a80e68e6a972fa353b800d068b;2026-10-30;instruction-accept-f8b77ac9-and-f8b77ac9;direction-we-will-go-with-RC3-first;D18-core-profile-before-release-path-steps-2-7;record-mvp-m6-plan-review-summary.md
m6_plan=accepted-b2c62d54f21c3cabdad3fefcc562499ace601089;parent-f8b77ac9;2026-10-30;decision-2-confirmed-by-form-accept-and-authorize;branch-beryllium/mvp-m6-plan;base-cd9cfa5f;record-mvp-m6-plan-review-summary.md;Q1-Q11-defaults;soft-limit-4000;board-runs-20
m6_implementation_authorization=M6-2..M6-8-on-beryllium/mvp-m6-from-acceptance-record;2026-10-30;board-only-after-human-confirms-k3-free
m6_implementation_branch=beryllium/mvp-m6
rc3_review_snapshot=published-by-the-human-2026-10-31-main-11705111-from-5c693b88-then-refreshed-1ae5fd8c39e309ee6aa6c11ee066d81cde9c1749-from-3fe427b7-with-the-policy-recheck-pushed-by-the-human;excluded-pathfinder-.github-planning/HANDOFF.md;gates-in-both-mvp-check-evaluate-uboot-rehearsal-kernel-repro-model-targets-PASS;policy-record-in-item-92-wording-the-humans
mvp_debt_sweep_2=accepted-7447cb92aad1a6348a4256d6f21b7e14b05a8a0d;base-506d2fc3;2026-10-31;instruction-proceed-with-7447cb92-5c693b88-ee631263;items-89-91-closed;branch-beryllium/mvp-debt-2
mvp_debt_sweep_3=accepted-3b7ab0e3e43bdad48772c0ae5eb8d831f218c29f;base-8b7559d2;2026-11-01;instruction-accept-3b7ab0e3-fast-fwd-push-use-your-best-judgement;rhyolite-rc3-snapshot-reviews-rows-A-to-L-closed;answers-harden_and_gate-gate_variable-exclude_from_snapshot-defer_to_migration-tier1_now;items-94-98-open;branch-beryllium/rc3-review-remediation;record-rc3-review-remediation-review-summary.md
mvp_debt_sweep_4=accepted-d162c60db4aab7bda77f2a557f91ac7446cca37c;base-b53c02a8;2026-11-01;instruction-accept-d162c60d-ff-push;directions-update-the-security-md-as-you-feel-best-fix-code-issues-then-update-the-snapshot;items-99-100-102-105-closed;101-103-104-open;m3-gate-scripts-change-authorized-by-fix-code-issues;branch-beryllium/mvp-debt-4;record-mvp-debt-4-review-summary.md;dev-fast-forwarded-to-the-acceptance-record-and-pushed
mvp_debt_sweep_5=accepted-e8ab73b712a974dc25d6cd8eab9bad24bd129405;base-486fd5a9;2026-11-01;instruction-accept-ff-push-and-re-refresh;directions-summarize-item-95-do-A;updates-archive-third-fetch-source;closure-259-from-public-sources-fedora-116-updates-124-archive-19;item-95-closed;item-106-open;m0b-reading-archive-is-a-fedora-repository-no-erratum;branch-beryllium/mvp-debt-5;record-mvp-debt-5-review-summary.md;dev-fast-forwarded-to-the-acceptance-record-and-pushed;snapshot-re-refreshed
rc3_snapshot_review_tier_2=no-pending-input;the-awaited-claude-cli-and-codex-cli-reviews-are-s3c-design-reviews-not-snapshot-reviews;register-closed-at-rows-A-L;a-later-snapshot-review-opens-a-new-sweep
rc3_snapshot_support=accepted-5c693b88ec869c9053e6045d3ddd4d84d198864a-and-ee631263cd08cdd5500a1bb9980d85c94d1f5469;base-506d2fc3;2026-10-31;same-instruction;branch-beryllium/rc3-snapshot-support
post_rc3_integration=beryllium/mvp-post-rc3;from-506d2fc3;merges-95ddf935-8fbdfb06;da8e9e18-3fe427b7-77511d99-accepted-2026-10-31;dev-fast-forwarded-to-the-acceptance-record-and-pushed
llm_policy_recheck=2026-10-31;linux-36aad21d50d1-against-pinned-481ed5dd3ed7;assisted-by-tag-dropped-upstream-2026-10-14;bug-fixing-procedure-added;generated-content-transparency;LLM_POLICY_ALIGNMENT.md-and-ai-assistance.md-updated
private_repository=new-private-origin-with-the-internal-suffix;created-2026-10-31;all-origin-branches-and-tags-plus-mvp-m6-mvp-m6-plan-mvp-debt-2-rc3-snapshot-support;former-name-to-be-deleted-and-recreated-public-by-the-human
m6_implementation_status=accepted;RC3-89ef04e9-accepted-2026-10-31-instruction-accept-89ef04e9-proceed;gates-PASS-at-X3-ebc49a88;board-20-of-20-2026-10-31;code-lines-3258-of-4000;M6-4-deferred-U-13;departures-13;record-mvp-m6-result-review-summary.md
m3_soft_limits=rocq-6000-at-3044;c-6000-at-3448;per-lane-combined-12000-at-6492-erratum-12;generator-driver-1500-at-1377
m3_open_items=evaluator-Z-mount-relabels-repository;evaluator-make-clean-deletes-host-build-model;evaluator-vo-and-binaries-embed-/work-path
m3_plan_errata=12-recorded-in-acceptance-record-2026-10-28;1-7-review;8-11-stops;12-limits-per-lane;none-needs-plan-revision
m3_reviews=gpt-5.6-sol-plan-draft;gpt-5.6-sol-second-round-plan-and-revision-1;human-authorized
k3_access=in-use-by-the-humans-other-project-since-2026-10-31-21:59Z-note-k3-is-in-use-by-other-project;no-board-command-until-the-human-says-it-is-free;last-beryllium-contact-item-80-test-21:31-21:41Z-board-left-in-fedora-env-untouched
m2_ff_push=dev-ccf70a3d-to-50b77c00;mvp-m2-50b77c00;mvp-m2-plan-35ebe8a7;origin-2026-10-28T08:53Z
development_branch_pushed=2026-10-30
m0_board_20261025_26=host-7.3.0-65.1;load-check-gcc-clang-pass;probes-3-of-3-pass;scenario-gcc-3-clang-1-pass-alternations-125;payload-fail-as-declared;no-stop;record-mvp/results/20261025-com260
m0_board_20261024=host-7.3.0-65.1;preflight-pass;load-check-gcc-clang-pass;probes-3-of-3-pass;gcc-run-1-alternations-5-below-8-stop-6
m0_stop=clang-monitor-text-0x1020087e0-over-0x102008000-by-0x7e0;gcc-0x102007fe0;resolved-by-M0-A
m0_evaluator=pass-at-13992d6d;lock-26-checked-3-host-only-skipped;closure-259;images-identical-146-of-146
m0_plan_revision_m0b=directed-2026-10-24;closure-sha256-per-rpm;verified-local-cache;repos-disabled;explicit-sysusers-swap;host-only-roles-podman-ssh-scp
m0_plan_revision_m0c=directed-2026-10-25;round-robin-drain;floor-k8-kept;board-stop6-fixture
m0_tool_lock=refreshed-804fa95f-ca-certificates;refreshed-l1-2026-10-26-ssh-scp-16.fc44-closure-259;lock_sha256=6e99262f04a1
m0_plan_revision_m0a=directed-2026-10-23;mvp-region-0x102064000+0x40000;boot-hart-rule;ring-full-redefined;erratum;debt-item
m0_open_items=1,8,9,10-resolved-by-M0-A;mvp-check-pass-gcc-clang-at-b0fd5780
b7_plan=accepted
b7_plan_target=026974fb619295482b93a7ae8cffdc4f552825ea
b7_plan_acceptance_instruction=accept-026974
b7_result=accepted
b7_result_target=7b6b846bf453bacf4c67d986f87c61fdc092e2ee
b7_result_acceptance_instruction=accept-7b6b84
kvm0=dropped-2026-10-08-records-retained
r8_h1_h4=dropped-2026-10-08-never-authorized
r8_h0_accepted_target=1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4
r8_h0_readiness=BLOCKED-NOT-READY
development_kernel_bsp=UNDECIDED-not-required-for-B7-S3
publication=blocked
```

## Authoritative records

- Returning-human structure and inspection:
  [project orientation](project-orientation.md); a dated overview as of
  MVP 1.0 release candidate 2:
  [project snapshot](project-snapshot-mvp-1.0-rc2.md); the candidates
  after release candidate 3 on one page (decision support, selects
  nothing): [post-RC3 candidates](post-rc3-candidates-2026-10-31.md)
- Maintained definitions and disambiguations: [glossary](glossary.md)
- Longer-range sequencing and gates:
  [implementation plan](implementation-plan.md)
- Current handoff and repository state: [handoff](HANDOFF.md)
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
- Hardware feature inventory and dispositions:
  [RISC-V and K3 security hardware](riscv-security-hardware.md)
- Release, license, and assistance boundary:
  `LLM_POLICY_ALIGNMENT.md`

Markdown under `planning/` is authoritative. DOT is authoritative diagram
source. Generated HTML is a deferred milestone/release artifact; the private
2026-09-30 snapshot is `archive/generated-docs-2026-09-30` at
`d4c5ff0616c78d997367a050db85512c44960acb` and grants no publication
approval.

mvp_1_0_milestones=M0-M10-complete-and-accepted;latest-accepted-candidate-RC4-d70a8535;release-path-steps-2-7-not-started
