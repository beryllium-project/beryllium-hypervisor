# Planning

> **Reading note (MVP 1.0's public release).** This page is part of the
> planning record as it stood at this repository's source commit, before
> the repository existed; its statements of status, repositories, and
> publication are as of the source commit (2026-11-05). The release itself is described by
> `README.md` and `RELEASE.md` at the repository's root.

Returning after time away? Read the
[project orientation guide](project-orientation.md) first, use the
[glossary](glossary.md) for maintained terminology, and use the
[roadmap](roadmap.md) as the current-position placemat. The detailed plans,
evidence, and review records linked from those pages remain authoritative.

The active private GitHub repository is
`beryllium-project/beryllium-hypervisor`. Historical review records preserve
the former private repository identity, remotes, and checkout paths where
those values were part of the packet-time evidence. Use the
[project orientation guide](project-orientation.md) for current repository
identity and runnable inspection commands.

## Maintained outcomes as of 2026-10-22

- On 2026-10-17 the responsible human, having found that the S1 draft
  treats TE only as a runtime denial mechanism, requested a review of the
  draft and of the project against its founding goals. On 2026-10-18 the
  instruction `approve 480d 07541` accepted the
  [project review](project-review-2026-10-17.md) (exact commit `480dab72`;
  18 findings, 8 options; corrected that day after the research agents
  were re-run on `claude-fable-5.1` at the responsible human's direction,
  superseding `65fc52e0`) and then the
  [S1 and TE-trigger revision plan](s1-te-trigger-revision-plan.md) (exact
  commit `07541c59`), recorded in one
  [review summary](project-review-2026-10-17-review-summary.md). The plan's
  documentation packages RP-1 to RP-3 were accepted on 2026-10-18 by the
  instruction `I accept RP-1 RP-2 RP-3` (next item).
- On 2026-10-16 the instruction `authorize S1, proceed` authorized S1, the
  Helium-to-Beryllium synthesis. Its [document](he-to-be-synthesis.md),
  revised as RP-1 of the accepted revision plan, was accepted on 2026-10-18
  at exact commit `fd670dcd54ff4f2c66349d377be914698b9dda3b` (the first
  draft `0fbca0fd` is superseded), together with Model 0.1 plan revision
  M01-A (RP-2, `95ef0f6c`) and the revised S2 definition (RP-3,
  `1ac7080f`), by the instruction `I accept RP-1 RP-2 RP-3`; see the
  [revision review summary](s1-te-trigger-revision-review-summary.md). S1
  is complete; the development branch was fast-forwarded to `0eb37570`
  and pushed to the private `origin` the same day. The
  [S2 plan](s2-security-model-plan.md) was accepted on 2026-10-19 at exact
  commit `5ce7827f` (instruction `accept 5ce782`; see its
  [review summary](s2-security-model-plan-review-summary.md)), with Q1
  answered A and Q2 to Q7 at their defaults. Under it,
  [security model v1](security-model-v1.md) was accepted on 2026-10-22 at
  exact commit `0e3eec8b4fd74003f8cedbf2ca66871c31412624` (instruction
  `accept 0e3eec8b`, with V1 to V4 at their defaults; see its
  [review and acceptance record](security-model-v1-review-summary.md)), so
  S2 is complete. On 2026-10-22 the instruction `merge & push, start S3`
  fast-forwarded the development branch to `0096de3e` and pushed it, and
  directed S3: the [MVP plan](mvp-plan.md), revision 1, was accepted on
  2026-10-23 at exact commit `93967fba` (instruction `accept 93967fba`,
  Q1 to Q12 at their defaults; see its
  [review and acceptance record](mvp-plan-review-summary.md)), so S3 is
  complete. The revision of 2026-10-23 puts each domain on its own hart
  with a dedicated control hart; `06c35f48` is superseded. The acceptance
  authorizes writing M0's bounded plan only; that
  [M0 plan](mvp-m0-plan.md) was accepted on 2026-10-23 at exact commit
  `4d129808` (`accept 4d129808, proceed with implementation using
  opus-5.5 model`; see its
  [review and acceptance record](mvp-m0-plan-review-summary.md)). M0
  implementation on `beryllium/mvp-m0` ran under it and under Plan
  revisions M0-A (directed 2026-10-23, after stop condition 3), M0-B
  (2026-10-24), and M0-C (2026-10-25, after the first board campaign's
  stop condition 6); it is complete through M0-6, with all eight runs of
  the second COM260 campaign passed on 2026-10-25 and 26. Exact result
  commit `b266972563a39b0687ba2ac8c5b4cb943f3c766a` is responsible-human
  accepted as of 2026-10-26 (instruction `accept b26697`), with the three
  revisions; the
  [M0 result review and acceptance record](mvp-m0-result-review-summary.md)
  holds the decision and the claim boundary. On `proceed` the same day
  the development branch was fast-forwarded to the acceptance record
  `6f7b6e7c` and pushed with `beryllium/mvp-m0`, and the
  [M1 plan](mvp-m1-plan.md) was proposed at exact commit `7b2c055c` on
  local branch `beryllium/mvp-m1-plan` and accepted the same day
  (instruction `accept 7b2c055c`, Q1 to Q19 at their defaults; see its
  [review and acceptance record](mvp-m1-plan-review-summary.md)),
  authorizing M1 implementation, work packages M1-1 to M1-6, on branch
  `beryllium/mvp-m1` from the acceptance record. M1 is implemented
  through M1-6 under Plan revisions M1-A (2026-10-27, the denied accesses
  in a forked child of the init, after stop condition 6 in QEMU) and
  M1-B (2026-10-27, a failed domain hart's wait for hart 0 measures its
  progress, after stop condition 6 in the first board campaign's
  `no-inject` run); the second COM260 campaign passed 6 of 6 RAM-only
  kexec runs with `k3ctl` resets. Exact result commit
  `ff84533cb3c13d89063be77652575347c2a82757` is responsible-human
  accepted as of 2026-10-27 (instruction `approve ff84533c and
  revisions, accept your recommendations, authorize proceeding per
  those`), with the two revisions; the
  [M1 result review and acceptance record](mvp-m1-result-review-summary.md)
  holds the decision and the claim boundary. The same instruction
  accepted the recommendations that followed: the development branch's
  fast-forward and push, the model-split paragraph in the instructions,
  and the M2 plan as a proposal on a new branch. The
  [M2 plan](mvp-m2-plan.md), a protected research domain beside an
  untrusted Linux, was proposed at exact commit `854a5415` on local
  branch `beryllium/mvp-m2-plan` (from `ccf70a3d`) and accepted the same
  day (instruction `accept 854a5415 , gpl 2.0 only ok`: Q20, the guest
  module's `GPL-2.0-only` license, answered as its default; Q1 to Q19 at
  their defaults; see its
  [review and acceptance record](mvp-m2-plan-review-summary.md)),
  authorizing M2 implementation, work packages M2-1 to M2-7, on branch
  `beryllium/mvp-m2` from the acceptance record. M2 is implemented
  through M2-7 on that branch, with Plan revision M2-A (directed
  2026-10-28 after the first board campaign stopped on stop condition
  6; harness only); its exact result commit
  `18d552bc4cf3a463bc4dc491e5e346989e5a521c` (parent `397670e5`) is
  responsible-human accepted as of 2026-10-28 (instruction `accept
  18d552bc`), with the revision; the
  [M2 result review and acceptance record](mvp-m2-result-review-summary.md)
  holds the decision and the claim boundary. On `approve 1 & 2.
  proceed` the development branch was fast-forwarded to `50b77c00` and
  pushed with the M2 branches, and the [M3 plan](mvp-m3-plan.md), the
  policy layer and the hart binding in the model, was proposed at exact
  commit `c2c249f4` on local branch `beryllium/mvp-m3-plan` (from
  `50b77c00`; its first candidate `9952e765` is superseded, the limits
  made soft on the responsible human's direction) and accepted the same
  day (instruction `accept c2c249f4`, Q1 to Q12 at their defaults; see
  its [review and acceptance record](mvp-m3-plan-review-summary.md)),
  authorizing M3-1, the additive security model v1 revision, as its own
  exact commit for decision on branch `beryllium/mvp-m3`, and M3-2 to
  M3-6 only after that revision is accepted. M3-1 is proposed at exact
  commit `019cca64` (Revision 1 appended to
  [security model v1](security-model-v1.md); its first candidate
  `32298add` superseded after a second review) and accepted the same day
  (instruction `accept 019cca64`; see its
  [review and acceptance record](security-model-v1-revision-1-review-summary.md)).
  M3-2 to M3-6 are complete: exact result commit
  `b0a0f352d7969a8f8cf28cf0d25b89fc372e70f2` (parent `d35813c7`, at
  which `./be model-check` and `./be evaluate` pass from a clean tree)
  is responsible-human accepted as of 2026-10-28 (instruction `6000 per
  lane, so 12,000 combined soft limit. accept b0a0f352`, which also
  fixed the two re-set soft limits as 6,000 per lane, a combined 12,000
  against the measured 6,492; plan erratum 12); the
  [M3 result review and acceptance record](mvp-m3-result-review-summary.md)
  holds the decision and the claim boundary, and the
  [M3 evidence record](mvp-m3-evidence.md) the evidence. M0 to M3 are
  accepted. On `push all work` and `then proceed with (1) and (2)` the
  development branch was fast-forwarded to `fb8accc9` and pushed with
  the M3 branches, and the [M4 plan](mvp-m4-plan.md), the release
  candidate, is proposed at exact commit `0d02df72` on local branch
  `beryllium/mvp-m4-plan` (from `fb8accc9`, unpushed) with its
  [review summary](mvp-m4-plan-review-summary.md), after the first
  candidate `91f4a820` was reviewed by `gpt-5.6-sol` on the responsible
  human's session SOP of 2026-10-28 (planning steps are reviewed by that
  model at `max` with the `long_context` tier) and its nine findings
  incorporated; the responsible human accepted it the same day and
  authorized M4 (instruction `accept 0d02df27, authorize M4`, read as
  `accept 0d02df72`; Q1 to Q13 at their defaults; see its
  [review and acceptance record](mvp-m4-plan-review-summary.md)), so
  work packages M4-1 to M4-6 ran on `beryllium/mvp-m4` from the
  acceptance record on 2026-10-28 and 29, with two stops decided by the
  responsible human (plan erratum 1, the new-code soft limit re-set to
  2,000; Plan revision M4-A, the board record's redaction to code names,
  presented with the result). The candidate tree `X` is `d42b9ec0`, on
  which the seven gates pass (247 of 247 images identical); the
  release-candidate board campaign ran at `X`'s images on the human's
  confirmation, eleven of eleven runs as declared; the release-candidate
  commit `c5df0cfa` (`R`, over `X`) is responsible-human accepted as the
  M4 result and the MVP 1.0 release candidate as of 2026-10-29
  (instruction `accept c5df0cfa, commit & push, I will review in
  detail`), with Plan revision M4-A; the
  [M4 result review and acceptance record](mvp-m4-result-review-summary.md)
  holds the decision and the claim boundary, the
  [M4 evidence record](mvp-m4-evidence.md) the evidence, and the
  [release-candidate walkthrough](mvp-rc-walkthrough.md) is the
  operator's guide for the human's detailed review. M0 to M4 are
  accepted: MVP 1.0's milestones are complete. The acceptance is the
  release path's step 1; steps 2 to 7 each need their own instruction,
  and none is started. `beryllium/mvp-m4` and `beryllium/mvp-m4-plan`
  are on the private `origin`; the development branch stays at
  `fb8accc9`. It fixes the MVP claim's wording with its
  required limit and forbidden phrasings, defines the claim ledger, the
  researcher guide, the AI-assistance disclosure, and the clean
  release-candidate evidence from the pinned evaluators, and plans one
  board campaign at the candidate's images that waits on the
  responsible human's confirmation that the K3 is free.
- **M5, release candidate 2 (boot from system reset): Plan revision
  S3-A and the M5 plan are responsible-human accepted as of 2026-10-29
  and M5 implementation is authorized** (instruction `accept 0d134bbc
  and 066794d, authorize m5`, read as `0066794d`; Q1 to Q16 at their
  defaults; the [M5 plan review and acceptance record](mvp-m5-plan-review-summary.md)
  holds the decision). **The M5 result, exact commit
  `3867c66c5df2108e1051d8f8c44c12d62611e485` (`R2`, over the candidate
  tree `X2` `6dd81ee3`), is responsible-human accepted as MVP 1.0
  release candidate 2 as of 2026-10-30** (instruction `accept 3867c66c`;
  the [M5 result review and acceptance record](mvp-m5-result-review-summary.md)
  holds the decision and the claim boundary, the
  [M5 evidence record](mvp-m5-evidence.md) the evidence); it is on
  branch `beryllium/mvp-m5` (from the acceptance record `9b3fa982`),
  pushed with `beryllium/mvp-m5-plan` to the private `origin` on
  `approve 1, 3` (2026-10-30), when the development branch was
  fast-forwarded from `fb8accc9` to the commit recording the push;
  release candidate 1 is accepted history, and the release path's step
  1 holds for release candidate 2 with steps 2 to 7 not started; debt
  sweep 1 (`mvp/README.md` items 83 and 85; the ledger-pin fix
  `466c29f4` for item 86) is accepted at exact commit `80ef8a13` on
  `beryllium/mvp-debt-1` (2026-10-30), to which the development branch
  is fast-forwarded through its acceptance record and pushed. At `X2`
  the seven gates
  pass from a clean checkout (253 of 253 images identical; the U-Boot
  rehearsal's seven cases), recorded in `mvp/results/20261030-rc2/`;
  on the human's confirmation the board session ran at `X2`'s images on
  2026-10-30 (the human present at the install and the restore): twenty
  runs booted from system reset by the COM260's installed firmware and
  U-Boot from the `beryllium` partition under the installed boot
  command, twenty of twenty as declared with the accepted records'
  counts, U-Boot's saved environment restored to the pre-session record
  byte for byte, one stop in the middle (condition 12, a lost `s`,
  hardened and resumed); `mvp/results/20261030-com260-rc2/` is its
  record. The characterization (M5-6a) passed on its seventh attempt
  after six stopped on BSP facts (`poweroff` powers the board off; no
  `Environment size` trailer; `nvme scan`; a silent `crc32`, so the
  digest witness is `md5sum`); stop condition 8 fired at 6,865 added
  code lines and the human re-set the limit to 10,000 (erratum 1;
  7,439 at `X2`). Diagnostic bring-up evidence for one board, not
  hardware validation; no release step or kexec use; any further merge
  or push needs its own instruction. On 2026-10-29 the responsible human asked whether the
  MVP boots by kexec or from system reset, was told every board run of
  M0 to M4 was a Linux `kexec_load` from the board's Fedora under the
  resident OpenSBI, and directed `modify the plan so that the mvp
  candidate boots from system reset. I don't know where those safety
  rules came from.` The rules were traced to automation's own B0
  README (`62060e2d`), never human-directed. The human then chose the
  mechanism (one ext4 partition `beryllium` on the board's NVMe carved
  from p3 by a delivered dry-run-first tool the human runs; U-Boot's
  saved environment changed within a recorded session and restored;
  automation typing fixed templates into the operator's picocom session
  with every keystroke recorded; `k3ctl` or human resets; kexec removed
  from the MVP tools and claim; a U-Boot rehearsal in QEMU; one
  `saveenv` per image group; an M5 code soft limit of 5,000) and set the
  standing rule `no more kexec unless I approve it`, clarified as `don't
  use this from here, unless it is truly needed for something`.
  [Plan revision S3-A](mvp-plan.md#plan-revision-s3-a-boot-from-system-reset-the-board-policy-m5-and-release-candidate-staging)
  of the MVP plan (the board policy, M5, release-candidate staging with
  RC1 `c5df0cfa` as accepted history and RC2 as M5's result, D17) and
  the [M5 plan](mvp-m5-plan.md) (Q1 to Q16 with defaults; M5-1 to M5-7
  with an attended characterization M5-6a; 13 stop conditions) are on
  local branch `beryllium/mvp-m5-plan` from `6a5f6fed`, unpushed, with
  the partition tool `mvp/tools/k3-make-partition.sh` and its host
  self-test, presented as ordered decisions in that record. The plan's
  draft was reviewed for steering by `claude-opus-5.5` at the human's
  request; its two blockers (the QEMU rehearsal's relocation address;
  run-to-image attribution, since every board image has one size) are
  fixed in the plan. (At the plans' acceptance nothing of M5 had touched
  the board; the board work above followed.)
- **M6, the MVP core profile as release candidate 3: Plan revision S3-B
  and the M6 plan are responsible-human accepted as of 2026-10-30 and M6
  implementation is authorized** (instruction `accept f8b77ac9 and
  f8b77ac9`, the second decision confirmed by the form answer
  `accept-and-authorize`; Q1 to Q11 at their defaults; the
  [M6 plan review and acceptance record](mvp-m6-plan-review-summary.md)
  holds the decisions). On 2026-10-30, after
  release candidate 2's acceptance, the responsible human directed `we
  will go with RC3 first`: the "MVP core profile" debt (M0 Plan revision
  M0-A.5: the monitor re-executes the frozen single-hart fixed profile and
  builds fixture roots and pages it never uses) is to be retired before
  the release path's steps 2 to 7, its result presented as release
  candidate 3. [Plan revision S3-B](mvp-plan.md#plan-revision-s3-b-release-candidate-3-and-milestone-m6-the-mvp-core-profile)
  (exact commit `f8b77ac9`; D18) and the [M6 plan](mvp-m6-plan.md)
  (exact commit `b2c62d54`: the MVP's real configuration generated per
  scenario from the authority report and validated, sealed, and derived
  at boot by the ported, widened accepted R1 mechanism; the derived
  mappings driving the Sv39x4 builder; the fixture roots, pages, guest
  code, and the control hart's VS-entry steps removed; extents, image
  base and size, and the board path unchanged; one executor for the
  privileged effects with the proof-bearing subset named; an additive
  model instance if its shape admits one; the gates, a 20-run board
  campaign, records, and a packet; M6-1 to M6-8; a 4,000-line soft
  limit; eleven stop conditions; Q1 to Q11 with defaults) are on local
  branch `beryllium/mvp-m6-plan` from `cd9cfa5f`, unpushed. **The M6
  result, exact commit `89ef04e9354c08ebadbaeb88d553c5081a00b84d`
  (`RC3`, over the candidate tree `X3` `ebc49a88`), is responsible-human
  accepted as MVP 1.0 release candidate 3 as of 2026-10-31**
  (instruction `accept 89ef04e9, proceed`; the
  [M6 result review and acceptance record](mvp-m6-result-review-summary.md)
  holds the decision and the claim boundary, the
  [M6 evidence record](mvp-m6-evidence.md) the evidence); it is on local
  branch `beryllium/mvp-m6` from the acceptance record `366c8af4`,
  unpushed (no push or merge was directed); release candidates 1 and 2
  are accepted history, the "MVP core profile" debt is retired, and the
  release path's step 1 holds for release candidate 3 with steps 2 to 7
  not started. M6-2 (the core profile: each scenario's own configuration
  generated from the authority report and validated, sealed, and derived
  at boot by the ported, widened accepted R1 mechanism; `BE_MVP:00
  BOOT_VALIDATED` and `CONFIG_SEALED`; the fixture roots and pages gone)
  and M6-3 (the executor, 28 functions behind one file, with the image
  checker's seam rule and the layer table: 6,285 proof-bearing code
  lines) were implemented by `claude-opus-5.5` sub-agents and reviewed
  line by line; M6-4 (the model instance) is deferred with its reason
  (`Model.v`'s `frame` and `gpa` are closed enumerations; ledger U-13;
  no theorem changed); M6-5 added the guide's boot story, the disclosure,
  and ledger rows C-40, C-41, and U-13. At `X3` the seven gates pass
  from a clean checkout on 2026-10-31 (253 of 253 images identical;
  `mvp/results/20261031-rc3/`), after a first run at `4cc5c53a` found
  that the model's generated policy instances follow the scenarios and
  their pinned identities had not (two test files refreshed; `mvp/README.md`
  item 88). On the human's confirmation (`the k3 is yours to operate`)
  the board session ran at `X3`'s images on 2026-10-31 (04:12 to 04:38
  UTC; the human present at the install and the restore): twenty runs
  from system reset, twenty of twenty as declared with release candidate
  2's counts and the M6 prelude in every run, the saved environment
  restored byte for byte, no stop, no lost `s`
  (`mvp/results/20261031-com260-rc3/`). New code 3,258 lines of 4,000;
  thirteen departures for the human's attention (the model deferral, the
  model test pins, a tmux window target, the preflight pair's kernel
  after a hand-typed test boot, among them), accepted with the result;
  `./mvp/mvp check` passes at `RC3` (46 ledger claims). Diagnostic
  bring-up evidence for one board, not hardware validation; no release
  step, merge, push, or kexec use. On 2026-10-31 the human directed a
  fresh-history review snapshot of release candidate 3 (`give me a clean
  RC3 snapshot repo which I will put up until the main repo is ready`):
  the private history moved to `beryllium-project/beryllium-hypervisor-internal`,
  and `mvp/tools/snapshot.sh` made the snapshot from `5c693b88` (one
  commit `11705111`; `pathfinder/`, `.github/`, and `planning/HANDOFF.md`
  excluded; `./mvp/mvp check`, `evaluate`, the U-Boot rehearsal,
  `kernel-repro`, and the model's targets pass in it) for the human to
  publish under the former name. The same day (`proceed with 7447cb92
  5c693b88 ee631263`) the human accepted debt sweep 2 (`7447cb92`: the
  console tool finds picocom's pane among the session's windows; the
  wrapper refuses stray arguments) and the snapshot support (`5c693b88`,
  `ee631263`), merged on `beryllium/mvp-post-rc3`, and directed a recheck
  of upstream LLM policies: the Linux kernel dropped its `Assisted-by` tag
  on 2026-10-14 (`1e035297ffda`), disclosure now belonging in the cover
  letter under `generated-content.rst`; `LLM_POLICY_ALIGNMENT.md` and
  `mvp/docs/ai-assistance.md` follow. On `accept 3fe427b7 77511d99, ff
  dev and push` (2026-10-31) the human accepted the snapshot tool's
  `update` mode and the refreshed snapshot's record, and the development
  branch was fast-forwarded from `cd9cfa5f` to the acceptance record
  and pushed to the private `origin`; the public review snapshot's
  `main` (`1ae5fd8c`, the human's push) carries the rechecked policy. Two
  Rhyolite read-only reviews of that snapshot, consolidated by the human
  into twelve verified root causes (rows A to L, none in `mvp/src/`), are
  remediated by debt sweep 3, **responsible-human accepted as of
  2026-11-01 at exact commit `3b7ab0e3e43bdad48772c0ae5eb8d831f218c29f`**
  (instruction `accept 3b7ab0e3, fast fwd, push, use your best
  judgement`) on branch `beryllium/rc3-review-remediation` from the
  development tip `8b7559d2`, under the human's five answers of
  2026-11-01 (`harden_and_gate`, `gate_variable`, `exclude_from_snapshot`,
  `defer_to_migration`, `tier1_now`); the
  [debt sweep 3 review and acceptance record](rc3-review-remediation-review-summary.md)
  holds the decision, the per-row dispositions, the departures, and the
  gates. The same instruction fast-forwards the development branch to
  the commit recording the decision and pushes it and the sweep's branch
  to the private `origin`; the human's local clone of the public review
  snapshot is refreshed from the accepted content for the human's own
  push. `mvp/README.md` open items 94 to 97 (the M0 plan's `hgatp`
  erratum, the closure's remedies, the B-series READMEs, the ledger's
  tool pins) stay open; item 98 is corrected and closed: the two
  reviews the human awaited are independent design reviews of Plan
  revision S3-C, not of the snapshot, and are processed on the S3-C plan
  branch `beryllium/mvp-s3c-plan`.
- **Debt sweep 4 is responsible-human accepted as of 2026-11-01 at exact
  commit `d162c60db4aab7bda77f2a557f91ac7446cca37c`** (instruction
  `accept d162c60d & ff + push`) on branch `beryllium/mvp-debt-4` from
  the debt sweep 3 acceptance record `b53c02a8`; the
  [debt sweep 4 review and acceptance record](mvp-debt-4-review-summary.md)
  holds the decision. On the
  responsible human's directions of 2026-11-01 (`update the security.md
  as you feel best, fix code issues`; `then let's focus on updating the
  snapshot with fixes & security md`) it fixes the code defects among
  the open items the S3-C review processing registered: the capture
  checker read U-Boot's loader lines after the last autoboot line, so a
  forged block could be read in place of U-Boot's (item 100; now exactly
  one autoboot line per run, four mutations rejected, the 40 retained
  captures re-judged read-only with no finding, C-10's pin refreshed);
  the model gate's escape pattern matched singular keywords only (item
  102; the plural forms join both patterns with a test, a change to
  accepted M3 gate bytes under `fix code issues`); the snapshot tool
  wrote one session's id into every snapshot commit (item 105; now from
  `BE_SNAPSHOT_SESSION` or omitted); `evaluate` ignored the wrapper's
  `MVP_RPM_CACHE=DIR` argument. It adds the root `SECURITY.md` the human
  directed for the public review snapshot (item 99: an early pre-release
  snapshot for external review only; security issues may be filed openly
  for now), which the snapshot carries and its README names. No monitor
  source, claim, accepted plan text, board command, or kexec. The
  acceptance confirms `fix code issues` as the authorization for the two
  accepted M3 gate scripts' change. The same instruction fast-forwards
  the development branch to the commit recording the decision and pushes
  it and the sweep's branch to the private `origin`; the human's local
  clone of the public snapshot holds the snapshot of the sweep's packet
  commit, and its push is the human's.
- **Debt sweep 5 is responsible-human accepted as of 2026-11-01 at exact
  commit `e8ab73b712a974dc25d6cd8eab9bad24bd129405`** (instruction
  `accept  & ff + push , and  re-refresh`, the reply to the packet's
  request) on branch `beryllium/mvp-debt-5` from the development tip
  `486fd5a9`; the
  [debt sweep 5 review and acceptance record](mvp-debt-5-review-summary.md)
  holds the decision. On
  `summarize item 95` and `do A` (2026-11-01) it closes `mvp/README.md`
  item 95: Fedora's updates archive, which keeps every update build
  pushed to stable for a supported release, becomes the closure fetch's
  third source (after the `fedora` and `updates` repositories, before
  koji; a file still enters the cache only on a SHA-256 match with the
  closure), so the evaluator's whole closure fetches from public sources
  again (`fedora:116, updates:124, updates-archive:19` on 2026-11-01)
  and a third party can run `./mvp/mvp evaluate` without the development
  host's cache; the documents that said otherwise are corrected, and
  item 106 records the residual (Fedora 44's end of life). No lock,
  closure, image, monitor, claim, or plan change. The same instruction
  fast-forwards the development branch to the commit recording the
  decision and pushes it and the sweep's branch to the private `origin`,
  and re-refreshes the human's snapshot clone from the acceptance record
  for the human's own push.
- **Plan revision S3-C is responsible-human accepted as of 2026-11-01 at
  exact commit `27d2e557f069edf8dd714f5ac9b5ccb9b204a801`** (instruction
  `accept 27d2e557, defaults ff + push`, Q27 to Q46 at their defaults;
  its second candidate, on branch `beryllium/mvp-s3c-plan`; the
  [MVP plan revision S3-C review and acceptance record](mvp-plan-s3c-review-summary.md)
  holds the decision). Its acceptance authorizes writing the bounded
  plans of M7, M8, and M9, each on its own branch, and M10's after their
  results, and nothing else; none is started.
  On 2026-10-31, with release candidate 3 published as a review snapshot,
  the responsible human directed more time for a useful MVP 1.0, read the
  [one-page comparison](post-rc3-candidates-2026-10-31.md), and gave the
  MVP ladder's shape and three directions (measure first, then attest;
  IMA never; a simulated hardware root of trust for the proof of
  concept). S3-C records them: MVP 1.0, a security-research demonstrator,
  widens to M7 interactive guests (console input through the control hart
  on a dedicated input ring, a focus protocol, a pinned BusyBox with musl,
  scripted sessions, no shell in the anchor's protected domain), M8 the
  first verification plan (a concrete Rocq model on M3's modules and a
  Frama-C/WP versus CN pilot on `be_mvp_denial_decide` with the ring as
  the second leaf, resolving S1 H38 and H41, negative outcomes admitted),
  M9 measurement (the monitor's log with measurement registers beside a
  checker-held loader attribution and a dated platform assumption, never
  one chain), and M10 release candidate 4; MVP 2.0, 3.0, and 4.0 are
  named with an order (D19 to D22; Q27 to Q46; stop 1 amended by name;
  S3-A.1 item 8). The first candidate `95c9ab24` (2026-10-31) was read by
  three independent design reviews under the packet's section 8 brief
  (the Copilot CLI session's own, a Codex CLI session's, a Claude Code
  session's; the reports are in this directory unedited) and is
  superseded; the
  [reconciliation](mvp-plan-s3c-review-reconciliation.md) maps their
  findings onto 43 rows with the adjudications, and the second candidate
  answers them (the human's direction of 2026-11-01, `also now process
  the claude cli and codex reviews and iterate as appropriate`). The
  branch holds the development tip by merge (`b53c02a8`, then `44112dec`
  with debt sweeps 4 and 5 before the acceptance record), and the
  development branch is fast-forwarded to the acceptance record and
  pushed on the same instruction. LiteBox was re-analysed for MVP 2.0
  (the comparison page).
- **The M7 plan, interactive guests, is responsible-human accepted as
  of 2026-11-01 at exact commit
  `4f4d094efb3985435673f7bda62f35ad51c6165e`** (instruction `accept
  4f4d094e`, Q1 to Q16 at their defaults) on local branch
  `beryllium/mvp-m7-plan` from the development tip `f5dc770b`; the
  [MVP M7 plan review and acceptance record](mvp-m7-plan-review-summary.md)
  holds the decision. Written on the human's `go` (2026-11-01) after
  S3-C's acceptance, it bounds
  S3-C.3 under Q27 to Q46's defaults: hart 0 polls the firmware console
  on its own Sstc timer and routes typed bytes by a two-byte focus
  sequence (`~0`, `~1`, `~~`) through a dedicated input-only ring per
  domain hart to a served DBCN read under the write path's window rule,
  drops counted and never a failure; the output path unchanged and its
  two invariants tested claims; a pinned static BusyBox with musl (soft
  float, the locked GCC's `lp64` multilib) in the one guest Image, the
  shell an `argv[0]` variant of the in-tree init in new `shell` variant
  images; the console grant a configuration fact; the triggers found not
  to fire; Part 1's additive revision as its own commit; `InputRing.v`
  or a gap row; scripted sessions with a run nonce judged in QEMU as a
  gate; one typed board characterization under item 8, no campaign; the
  claim's pre-authorized sentences fixed in words; six work packages,
  an 8,000-line soft limit, thirteen stops, Q1 to Q16 with defaults.
  Its acceptance authorizes M7-2 to M7-6 on `beryllium/mvp-m7` from the
  acceptance-record commit, under its stops; no fast-forward or push was
  directed, so the development branch stays at `f5dc770b`.
- **The M7 result is responsible-human accepted as of 2026-11-02 at
  exact commit `e1a6395e038d4dd095960f7a942a87399bdbce18`** (parent
  `8418a377`, the gates' commit; instruction `accept e1a6395e, move k3ctl
  pin to v1.1`, whose pin part the human reversed two minutes later with
  `stop, keep k3ctl pin where it was for now, clone a copy if needed`) on
  branch `beryllium/mvp-m7`; on `ff + push M7` (2026-11-02) the
  development branch `beryllium/single-hart-runtime-r0` was fast-forwarded
  from `f5dc770b` to the commit recording that push, over the acceptance
  record `1b3f2e10`, and pushed to the private `origin` with
  `beryllium/mvp-m7` and `beryllium/mvp-m7-plan` (`ae3e9537`); the
  [MVP M7 result review and acceptance record](mvp-m7-result-review-summary.md)
  holds the decision and the [M7 evidence record](mvp-m7-evidence.md) the
  evidence. The `k3ctl` pin is unchanged (the tools run a copy of the
  pinned bytes when the checkout's client differs; `mvp/README.md` item
  114).
  M7-2 to M7-6 are implemented under the accepted plan with Q1 to Q16 at
  their defaults, erratum 1 (the soft limit re-set to 9,500 on `limit
  9500`; 9,092 counted lines), and the `model/Makefile` hook (`your
  choice`): the BusyBox and musl userland as pinned, signature-verified
  inputs; the monitor's input path (the input ring, the focus parser,
  hart 0's Sstc poll, the served DBCN read under the write-authority
  rule, `console_input` in the sealed state, `BE_MVP:15` to `:18`); the
  harness (each scenario's `shell` variant and session, the QEMU typist
  with a run nonce, the capture checker's console rules with 399
  rejected mutations, the hostile variant); `InputRing.v`'s four
  theorems; the claim's three fixed sentences and ledger rows C-47 to
  C-50, U-14, U-15; the board tooling (`probe-console-input`, the console
  tool's typing modes under `K3_GUEST_TYPING=human-authorized`, the
  characterization's driver and judge). The seven gates pass at
  `8418a377` from a clean tree (2026-11-02, 06:14 to 06:39 UTC; the first
  run at `058fee76` failed `evaluate` at the snapshot self-test's missing
  git identity, fixed in `8418a377`), and on the COM260, the human
  present, the typed characterization classed the firmware console
  `supplies` at 10 and 1 ms per byte (256 of 256 bytes) and one
  `two-guests` shell session passed with its accounting reconciled
  against the keystroke log (`mvp/results/20261102-com260-m7/`); the
  environment was restored and the board is free. Eighteen departures
  are in the packet's section 3, item 112's plan erratum (D-11's
  `two-guests` session, now the M7 plan's erratum 2) among them. The M7
  line is on the development branch and the private `origin` (`ff + push
  M7`, above); the M8 plan is proposed (below) and the M9 plan waits for
  the human's `go`; M10 after their results.
- **The M8 plan, the first verification plan, is responsible-human
  accepted as of 2026-11-02 at exact commit
  `7a0c74ae329c09282c5cf159076f5e99934ac4c2`** (parent `1b3f2e10`, the
  M7 acceptance record; instruction `accept 7a0c74ae wuth CN, go for
  m9`, Q10 answered `with CN` and the rest at their defaults) on local
  branch `beryllium/mvp-m8-plan`, unpushed; the
  [MVP M8 plan review and acceptance record](mvp-m8-plan-review-summary.md)
  holds the decision. Written on the human's `go` (2026-11-02) from S3-C.4
  and two read-only fact sheets of the tree, it bounds stage 1 (a
  concrete operational model of harts 0 to 2 under `model/` importing
  `Binding.v` and `Policy.v` unedited: the blocks and generation words,
  the three single-writer rings with 64-bit indices, the barrier, the
  denial path, `pause` and `terminate`, the measure-before-entry gate;
  the two first obligations; the lineage table; the layout generated
  from `mvp-layout.h` with a drift check; the ordering premises L1 to
  L5 as theorem premises discharged by litmus tests on the compiled
  sequences) and stage 2 (Frama-C/WP and CN on `be_mvp_denial_decide`
  with its static helpers, CBMC on `mvp-ring.c`, a registered decision
  rule, the specifications drafted from the plans and the claim and
  frozen by hash with the human as reviewer of record, a separate
  verifier image from Fedora 44's packaged tools and pinned sources,
  three recorded outcomes, the claim's pre-authorized sentence fixed in
  words for a positive result), the H38 and H41 resolution, M8-1 to
  M8-7, soft limits per lane, twelve stops, and Q1 to Q17 with defaults.
  Its acceptance authorizes M8-2 to M8-7 on `beryllium/mvp-m8` from the
  acceptance-record commit (stage 1's target), the specification
  document as its own exact commit for the human's review of record, and
  item 103's two corrections, and nothing else; no fast-forward or push
  was directed (the development branch stays at `6105c34d`). The same
  instruction directed the M9 plan (`go for m9`). **The M8 result is
  responsible-human accepted as of 2026-11-04 at exact commit
  `12b0e71b908e36041745601d214c03a5be34ad1e`** (instruction `accept
  12b0e71b`; over the gates' commit `f1813841`) on local branch
  `beryllium/mvp-m8`; the
  [MVP M8 result review summary](mvp-m8-result-review-summary.md) is its
  review and acceptance record and the
  [M8 evidence record](mvp-m8-evidence.md) the evidence.
  **Its outcome is inconclusive under the plan's own decision rule**: the
  specification was frozen and accepted (`004f31ae`; Revision 1
  `93a8d136`) and found fourteen errata and no code defect; stage 1's 26
  theorems are closed with 92 symbol readings gate-checked; the five
  ordering premises are `Never` under herd7's RVWMO; the verifier
  qualified 6 of 9 (arm, solver) pairs; and on the two leaves WP is OPEN
  130 of 134 (four true goals time out), CN OPEN 5 of 55 (tool limits),
  CBMC's bounded check of the denial decision SUCCESSFUL 336 of 336 and of
  the ring OPEN at its bound, so no monitor function has a C-level
  contract proof, the claim is unchanged, and the ledger gains the stage-1
  rows C-51 to C-55, U-16, and the third review item. The seven gates,
  `verify` among them, pass at `f1813841` from a standalone clean clone
  (2026-11-04). M7's, M8's, and M9's results are accepted; M10's plan
  (release candidate 4) follows on the human's `go`.
- **The M9 plan, measurement, is responsible-human accepted as of
  2026-11-03 at exact commit `4f4a8f760a1ed7e5f9886b4e02e94b7a849bfc33`**,
  its second candidate (instruction `accept 4f4a8f76`; Q1 to Q19 at
  their defaults, Q17 answered; parent `d470fb7f`, over the superseded
  first candidate `86f1c68b` and the M8 acceptance record `6fbcc3d1`) on
  local branch `beryllium/mvp-m9-plan`, unpushed; the
  [MVP M9 plan review summary](mvp-m9-plan-review-summary.md) is its
  review and acceptance record (acceptance record `bc80b620`, which
  merged the development tip `55047781`). **The M9 result is responsible-human
  accepted as of 2026-11-03 at exact commit
  `892b68c81dace15d2357e034e859b3eccd130abc`** (instruction `accept
  892b68c8`; over the gates' commit `dc07f7d3`) on local branch
  `beryllium/mvp-m9`, unpushed; the
  [MVP M9 result review summary](mvp-m9-result-review-summary.md) is its
  review and acceptance record and the
  [M9 evidence record](mvp-m9-evidence.md) the evidence:
  Part 1 Revision 3 accepted at `4bc079db`; the log profile, the premise
  record, and the probe template (M9-2); the monitor's log, its gate,
  and the self-report with the probe-race fix the human directed
  (M9-3); the references and the checker's log module (M9-4); the
  claim's D-9 sentences with the slots filled, the ledger's C-51 to
  C-53, U-16, U-17, the guide, and the crosswalk (M9-5); the bundle's
  exports and references, the dry run's window, and the seven gates at
  `dc07f7d3` (M9-6); 9,812 of the re-set 10,000 counted lines; no board
  step (the probe not performed, the correlation boot not run; the
  claim's slots say so). The acceptance records erratum 2 of the M9
  plan (the Q13 citation, item 119) in the plan's decision record; the
  claim's D-9 sentences take effect; no fast-forward, push, board step,
  or successor was directed. The first candidate was written on `go for m9` (2026-11-02)
  from S3-C.5 and a read-only fact sheet of the tree; on the human's
  `have gpt-6-astra review the m9 plan as steering input` an independent
  review ([the gpt-6-astra steering review](mvp-m9-plan-review-gpt-6-astra.md),
  kept unedited) found five blockers (an impossible 64-byte header; no
  per-image measurement contract; a negative whose oracle moved with the
  defect; claim words false under permitted outcomes; "CEL-shaped"
  mistaken for CEL), and the second candidate incorporates them with
  the review's recommendations (the packet's section 5 holds the
  disposition table). It bounds: a bounded, versioned log page of hart
  0's with an explicit encoding, four measurement registers, a close
  record before any domain hart starts, and lossless `BE_MVP:19 LOG` and
  `:20 REGISTERS` lines; the records R1 to R4 (the loader's MD5 held by
  the checker and never in the page; the monitor's self-measurement as
  an offline self-report; the core identity measured and the
  configuration and policy identities build-recorded; each domain's
  kernel Image and device tree as placed, and `anchor`'s secret page,
  gated per domain on its launch register; the console grant as a
  measured record, item 108); a per-image contract for every image
  class; a post-link per-image reference manifest in the Beryllium log
  profile (derived from TCG CEL 1.1, no interoperability claimed); the
  checker's rebuild, replay, independent recomputation, field-by-field
  comparison, and export with the negatives in five kinds;
  IMA never used, made testable; the human's read-only platform probe
  as a dated assumption with four outcome classes and the
  boot-authentication disposition for 1.0; the crosswalk analysis;
  Part 1 Revision 3 as its own exact commit; item 104's premise record
  committed; the claim's measurement clause fixed in words with fixed
  conditional forms for every permitted outcome; M9-1 to M9-6, a
  6,000-line soft limit, twelve stops, Q1 to Q19 with defaults (Q17
  answered). Its acceptance would authorize M9-2 to M9-6 on
  `beryllium/mvp-m9` from the acceptance-record commit and nothing else.
- **The M8 and M9 lines are integrated into the development branch
  (2026-11-04, instruction `go with ff & push, use your best judgment on
  remaining issues`):** `beryllium/single-hart-runtime-r0` was
  fast-forwarded from `55047781` to the M9 acceptance record `680b6241`
  and the M8 acceptance record `0d103a38` merged into it. The merge
  changes no monitor source: the two lines' tools, tests, records, and
  documents are their union, and the one shared artifact, the claim
  ledger, takes M9's rows at their accepted numbers and M8's renumbered
  (C-51 to C-55 became C-54 to C-58, U-16 became U-18, `mvp/README.md`
  item 124); M8's evidence record, result packet, and plan decision
  record keep M8's numbers as assigned at acceptance. On the merged tree
  the tool lock, `check` (after two latent defects of M9's
  `gen-reference.py --compare` were fixed, `mvp/README.md` items 126 and
  128),
  `claim-ledger check`, and `evaluate` pass; `./be model-check` fails by
  design at stage 1's readings gate, M9 having replaced the `measure`
  the concrete model reads, and `verify`'s digests would move: M10's
  re-proof (S3-C.7; item 127). The development branch is pushed at
  `331a0e9a` with `beryllium/mvp-m8`, `beryllium/mvp-m9`, and
  `beryllium/mvp-m9-plan`.
- Exact K3 B7 result commit `7b6b846bf453bacf4c67d986f87c61fdc092e2ee` is
  responsible-human accepted as of 2026-10-09 by instruction
  `accept 7b6b84, commit and push`. Its
  [review and acceptance record](k3-b7-result-review-summary.md) holds the
  claim boundary. Under the accepted B7 plan, two copies of the B6 guest,
  an unmodified upstream Linux `v7.2` kernel built uniprocessor, ran
  interleaved on hart 0, each in its own 64 MiB window under its own
  G-stage root and VMID, switched round-robin on a trapped `wfi` and an HS
  timer slice. Both guests powered off in 4 of 4 RAM-only COM260 runs
  through Linux kexec, three GCC and one Clang, with identical counts. The
  runs are diagnostic bring-up evidence for one board, not hardware
  qualification, and acceptance starts no successor.
- Exact K3 B7 plan commit `026974fb619295482b93a7ae8cffdc4f552825ea` is
  responsible-human accepted as of 2026-10-08 by instruction
  `accept 026974`. The [plan](k3-b7-plan.md) and its decision record
  authorized B7 implementation: two copies of the B6 Linux guest on hart 0,
  each in its own 64 MiB window under its own G-stage root and VMID,
  switched round-robin on a trapped `wfi` and an HS timer slice, rehearsed
  in QEMU and then run RAM-only on the COM260 through Linux kexec.
  Acceptance added no implementation, emulation, or board evidence.
- On 2026-10-08 the responsible human dropped the KVM0 workstream
  (`we will also drop the kvm0 workstream, we can create again if needed`)
  and R8 stages H1-H4 (form answer `r8=drop`). Their records stay as
  history, and a new plan may recreate either; H1-H4 were never authorized,
  and K0-X and K0-R never ran. The same day, the form answer
  `step3=proceed` directed a docs-only re-baseline: the
  [roadmap](roadmap.md) makes the K3 bring-up B-series the K3 path and lists
  the planned sequence B7 (two Linux guests), S1 (Helium-to-Beryllium
  synthesis), S2 (security model v1), and S3 (MVP plan). Exact re-baseline
  commit `ecad45d8eb371218d6f9a0965b330fa5043ea273` is responsible-human
  accepted as of 2026-10-08 by instruction `accept ecad45`; its acceptance
  authorized none of those steps.
- Exact K3 B6 result commit `e20c55df57551244eab47e0eff59d4c71fe75d20` is
  responsible-human accepted as of 2026-10-08 by instruction
  `accept e20c55`. Its
  [review and acceptance record](k3-b6-result-review-summary.md) holds the
  claim boundary. Under the accepted B6 plan and its two later directions,
  an unmodified upstream Linux `v7.2` kernel, built uniprocessor, ran as
  the only guest under a B6-owned G-stage over 64 MiB of guest RAM. After
  one stop and the `fix-warl` direction, it reached its init and powered
  off in 5 of 5 RAM-only COM260 runs: three GCC and one Clang through
  Linux kexec, and one GCC through U-Boot `booti`. The runs are diagnostic
  bring-up evidence for one board, not hardware qualification, and
  acceptance starts no successor.
- Exact K3 B6 plan commit `e34ef378b6279300ba5f3aeb8b6102941b432454` is
  responsible-human accepted as of 2026-10-08 by instruction
  `accept e34ef378`. The [plan](k3-b6-plan.md) and its decision record
  authorized B6 implementation: an unmodified upstream Linux `v7.2` kernel,
  built uniprocessor, as the only guest on K3 under a B6-owned G-stage over
  64 MiB of guest RAM, rehearsed in QEMU and then run RAM-only on the
  COM260 through Linux kexec. Acceptance added no implementation,
  emulation, or board evidence.
- Exact K3 B5 result commit `829562395bf14fedbeea0beb82b30da15ec5f7cf` is
  responsible-human accepted as of 2026-10-07 by instruction
  `accept 829562`. Its
  [review and acceptance record](k3-b5-result-review-summary.md) holds the
  claim boundary. Under the accepted B5 plan, a tiny separately built VS
  guest ran on the accepted R3 path with a B5-only guest SBI subset and
  reached its shutdown, with its own VS timer interrupt through Sstc, in 4
  of 4 RAM-only COM260 runs through U-Boot `booti` (three GCC, one Clang).
  Acceptance is diagnostic bring-up evidence for one board, not hardware
  qualification, and starts no successor.
- Exact K3 B5 plan commit `c3f8ef518850b55341cfd4ee0876b7f9ecf33859` is
  responsible-human accepted as of 2026-10-07 by instruction
  `accept c3f8ef51`. The [plan](k3-b5-plan.md) and its decision record
  authorized B5 implementation: a tiny bare-metal guest on K3 using a
  B5-only guest SBI subset, rehearsed in QEMU and then run RAM-only on the
  COM260. Acceptance added no implementation, emulation, or board
  evidence.
- Exact accepted-tool fixes commit `c60896e35cb2ddb8d8662c973aa46d4b5d0d8ef2`
  is responsible-human accepted as of 2026-10-07 by instruction `accept`.
  Its [review and acceptance record](accepted-tool-fixes-review-summary.md)
  holds the claim boundary. The accepted R7 extractor now prints addresses
  at and above 2^32 exactly. The R3, R4, and R5 image checkers derive symbol
  references, CSR writes, and jumps from instruction words instead of
  objdump annotations. 187 unit cases cover both. The corrected tools give
  the accepted results on every accepted input tested, and only the
  acceptance pins bound to the changed bytes move. After acceptance, the
  pinned-container gates passed on the development branch, except R4's
  traced QEMU step, which fails the same way before the fixes. Acceptance
  re-accepts no R3-R7 or B4 result, adds no hardware validation or
  formal-verification claim, and starts no successor.
- Exact K3 B4 result commit
  `135b1d3ae4def25691472bba0fa0179aa509d532` is responsible-human accepted
  as of 2026-10-07 by instruction `accept 135b1d3a`. Its
  [review and acceptance record](k3-b4-result-review-summary.md) holds the
  claim boundary. On B2's K3 port and images, the accepted R6 adversarial
  catalogue matches 47 of 47 entries in QEMU, host, and static checks. The
  accepted R7 bounded exact-byte proof passes in Rocq with accepted R7's
  counts. Acceptance adds no hardware validation or formal-verification
  claim, and starts no successor.
- Exact K3 B3 result commit
  `9b4860a049646d8878a31ecea8957e95b045550f` is responsible-human accepted
  as of 2026-10-06 by instruction `accept 9b486`. Its
  [review and acceptance record](k3-b3-result-review-summary.md) holds the
  claim boundary. Booted from the COM260's U-Boot `booti` through the B3
  shim, the accepted B2 image printed the SHIM line and all 22 accepted B2
  markers in 4 of 4 RAM-only runs (three GCC, one Clang). Acceptance is
  diagnostic bring-up evidence for one board, not hardware qualification,
  and starts no successor.
- Exact K3 B2 result commit
  `898af4e02fd36744a93b0eef99bc159955409d25` is responsible-human accepted
  as of 2026-10-06 by instruction `acctp 898af`, read as `accept 898af`. Its
  [review and acceptance record](k3-b2-result-review-summary.md) holds the
  claim boundary. All 22 accepted R3/R4/R5 markers reproduced in 4 of 4
  RAM-only COM260 runs (three GCC, one Clang), covering the checked switch
  to the protected domain, its denied load and denied shared-page store,
  and the checked return switch. Acceptance is diagnostic bring-up evidence
  for one board, not hardware qualification, and starts no successor.
- Exact K3 B1 result commit
  `b44c3c6b502d2883e95f53c642f407b577a18829` is responsible-human accepted
  as of 2026-10-06 by instruction `accept b44c3, proceed with b2`. Its
  [review and acceptance record](k3-b1-result-review-summary.md) holds the
  claim boundary. All ten accepted R3/R4 markers reproduced in 3 of 3
  RAM-only COM260 runs. Acceptance is diagnostic bring-up evidence for one
  board, not hardware qualification, and starts no successor beyond the
  separately authorized B2.
- Exact K3 B0 / `BE-K3-L0BOOT` result commit
  `bb8fd210758f88640817b5ea8010fe0654e626f3` is responsible-human accepted
  as of 2026-10-06 by instruction `accept`. Its
  [review and acceptance record](k3-b0-result-review-summary.md) holds the
  claim boundary. The boot marker reproduced in 3 of 3 RAM-only COM260 runs.
  Acceptance is diagnostic bring-up evidence for one board, not hardware
  qualification, and starts no successor.
- Exact K3 project-status roadmap target
  `a9bb91df94f7e1df2b0e7f2d3ca057f6516ea511` is responsible-human accepted
  as of 2026-10-04 by instruction `accept a9bb91`. Its
  [review and acceptance record](k3-project-status-roadmap-review-summary.md)
  preserves the parent, tree, four-path inventory, validation boundary, and
  explicit non-claims. Acceptance covers documentation status only and grants
  no K0-S readiness, hardware, successor, release-definition,
  paper/collaboration/venue, push, publication, or release authority.
- R8-ALM1-A exact plan target
  `95cce2f692543da67054ec2d6061eb08a4061253` is accepted as planning text
  only. Packet `788b0b6752b706ece8dc51dc2c0c5dca3e56376f`, acceptance record
  `0c5b468b642c0faee10cd7abaadd6166ca5637c0`, and clock follow-ups
  `aa83764a70c6a21052c90122e885485634662b5e`,
  `8f27c6a7da9a9a0c2c6307ef04e44f9c62afe4c9`, and
  `d1edb3ff4bd1e7a937aec05e16c33f30503e051d` carry the final history.
  Pre-correction skew-window times are non-authoritative; Git ancestry and
  hashes are primary. Implementation remains separately gated, H0 remains
  accepted but blocked, H1-H4 remain unauthorized, and hardware is `NOT-RUN`.
  The historical nonclaiming-repair path stopped without an implementation
  candidate and is superseded by this accepted planning path.
- Documentation reproducibility target
  `7cf4c4a1dff0b3f2dac2c692a2f1d2398ff6771e` is accepted on 2026-09-30 for
  exactly 24 paths and the selected Nimbus environment. Packet
  `73c6aee8bb1d69ec942b8cf74b7f3b7978352505` and acceptance record
  `c6fa7a7cd2e9ee9bc68c9f356d091541f8aee6b2` remain on clean local,
  unpushed branch `beryllium/doc-repro-option-a-20260929`; they are not
  integrated into this active line. There is no cross-host/future-package
  guarantee, and the retained OCI remains a single-copy risk. No
  cherry-pick, push, publication, runtime, proof, or hardware authority
  follows.
- K0-S target `c65705582c243dd908ff47d3189df07601167400`
  is accepted and privately pushed. The selected exact-Git route privately
  remote-contains source target
  `c1c7e254143f99d4ad3cdbf25021a76364d6d75a`. The current package has 46
  files, 53 inventory paths, 45 checksums, `FILES.modes` SHA-256
  `003f8f79b7bf97f9699d995292089521dee0f255834ff253774bc90dfd44c195`,
  `SHA256SUMS` SHA-256
  `21b1ea3ef1b246aff7c27b3728a41a415be80aa677699837f106bb025c343060`,
  and passing 45+17 host-only tests. K0-S remains not ready because the
  deferred K3/offline payload and external archive are missing. On
  2026-10-04 the responsible human separately authorized bounded
  readiness-completion from exact Beryllium base
  `a8e137ebbbeeff2a5475050b047a8ec6109d22e0`: source-owner assembly and
  finalization of already-retained offline payload bytes and the external
  archive only. The recorded base/candidate/tree/14-patch/release relation is
  not accepted, and the authority grants no rebuild, board access, live
  FDT/initramfs capture, destination import/install, K0-X, push, publication,
  or release. PMR-077's human-reported COM260/KVM/Fedora operation remains
  non-evidentiary planning input and changes no KVM0 gate, BSP decision, or K3
  `NOT-RUN` state. The bounded readiness-completion work reached its
  missing-byte/provenance stop and is paused. The responsible human later
  authorized drafting the proposed
  [K0-S completion plan](k3-kvm0-k0s-completion-plan.md), which separates
  custody/selection, offline replacement inputs, and read-only board
  characterization. Exact target
  `33f35981483bccbc4e3a1c87f4a5af52e0e15d41` is responsible-human accepted
  as planning text only as of 2026-10-04. Its
  [review and acceptance record](k3-kvm0-k0s-completion-plan-review-summary.md)
  retains K0SC-R1/R2/R3 as unresolved and unwaived. No package is authorized;
  K0-S remains not ready and K0-X/K0-R remain blocked.
- At `2026-10-04T20:28:37.102+02:00`, the responsible human reported the K3
  hardware online and available and instructed `proceed as appropriate`.
  This is non-evidentiary scheduling input and authorizes drafting the
  proposed [K0-SC1 custody and selection plan](k3-kvm0-k0sc1-plan.md) only.
  K0-SC1 implementation, custody, selection, network ref checks, board access,
  K0-SC3, readiness, K0-X/K0-R, push, publication, and release remain
  unauthorized or blocked. Exact K0-SC1 target
  `9b9923f8a58fe7102a108cb2a976ea09979427a1` is responsible-human accepted
  as planning text only as of 2026-10-04. Its
  [review and acceptance record](k3-kvm0-k0sc1-plan-review-summary.md)
  retains K0SC1-F1/F2/F3 and K0SC-R1/R2/R3 as unresolved and unwaived.
  Later overnight and read-only board-access steering was not consumed as
  implementation or K0-SC3 authority.
- Proposed Plan revision K0-SC1-A updates the maintained
  [K0-SC1 plan](k3-kvm0-k0sc1-plan.md) to narrow C5 to selection-only fields,
  add finite directory/mode/row bounds, and bind exact ref records plus all
  16 stop IDs. Exact target
  `c00f4d000c845a7c3d62921c1d7939fc158744e2` is responsible-human accepted
  as planning corrections only as of 2026-10-05. Its
  [review and acceptance record](k3-kvm0-k0sc1-plan-k0sc1a-review-summary.md)
  retains K0SC-R1/R2/R3 as unresolved and unwaived. The revision authorizes
  no implementation.
- Proposed Plan revision K0-SC1-B updates the same maintained
  [K0-SC1 plan](k3-kvm0-k0sc1-plan.md) with a uniform manifest-row host
  custody path and mandatory final-tree raw/NFC/casefold uniqueness checks.
  Exact proposed target
  `1ce71e73078a65a271949d84db47343e4eaacf14` has a
  [decision-neutral review packet](k3-kvm0-k0sc1-plan-k0sc1b-review-summary.md).
  On October 5, 2026, the responsible human requested revisions for
  K0SC1B-F1 through K0SC1B-F4. The target remains unaccepted, all findings
  remain open and unwaived. At `2026-10-05T22:58:19.170+02:00`,
  correction drafting from exact base
  `e1cd15a72e84304812a7c893d5b3a8c4990ea628` was separately authorized
  for those four findings only. A corrected target is proposed, not reviewed
  or accepted. Exact corrected target
  `13463e4f8473e4a5497ef60f92f284ea4f9944f5` has a
  [decision-neutral review packet](k3-kvm0-k0sc1-plan-k0sc1b-corrected-review-summary.md);
  independent review recommends revisions for four high and three medium
  findings. Custody, selection, implementation, remote query, board access,
  and successor work remain unauthorized.
- Evidence-retention Option A Phase 1 is complete. Phase 2 packet SHA-256 is
  `94a780ee271f23de1785fed03f5a14f89a713912f60047afd83e06d3bee0b106`;
  Phase 2 is blocked on independent secondary, encryption/key recovery,
  private-index, retention/lifecycle, and restore choices. No store exists.
- **The M10 plan, release candidate 4, is responsible-human accepted as
  of 2026-11-04 at exact commit `600b78c5198c7462ca76fdb30113f3770fdf5fa7`**
  (instruction `accept 600b78c5`; Q1 to Q15 at their defaults; written
  on the human's `re-refresh then go`; parent `c59003e7`) on local branch
  `beryllium/mvp-m10-plan`, unpushed; the
  [MVP M10 plan review and acceptance record](mvp-m10-plan-review-summary.md)
  holds the decision, which authorizes M10-2 to M10-7 on
  `beryllium/mvp-m10` from the acceptance-record commit and the target
  digests' re-write at `X4`; implementation started the same day
  (`proceed with development`). It bounds release candidate 4 as S3-C.6
  defines it: `X4` one commit at which eight gates pass from a clean
  checkout (the lock, `check`, `evaluate`, the U-Boot rehearsal,
  `kernel-repro` with BusyBox and musl, `model-check` with stage 1 green
  at `X4`, the model's evaluator, and `verify` with every suite); the
  re-proof at `X4` under the M8 plan's D-2 and S3-C.7 (stage 1 re-read
  and re-proved with every statement unchanged, the target digests
  re-written at `X4` on the plan's acceptance, the arms re-run at the base
  and at `X4` line for line); the board campaign of 25 runs at `X4`'s
  images under S3-A.1 with item 8 (four probes, twelve scenario runs, six
  negatives with `self-report-flip`, the three shell images with their
  sessions typed, the log judged in every run, which subsumes M9's
  correlation boot); the release surfaces through the ledger's release
  object; a per-component licence manifest with corresponding-source
  pointers; items 115, 118, 121, and 122; a 2,500-line soft limit with
  the M8 lanes' limits for the Rocq and the annotations; thirteen stops;
  Q1 to Q15 with defaults. It changes no monitor source. Its acceptance
  would authorize M10-2 to M10-7 on `beryllium/mvp-m10` from the
  acceptance record and the digests' re-write, and nothing else: no
  release-path step beyond the first, no merge, push, snapshot refresh,
  or kexec.

- **The M10 result, release candidate 4, is responsible-human accepted as
  of 2026-11-05 at exact commit `d70a8535474a690920ff152e7b38a25c589adba9`**
  (instruction `accept d70a8535`; parent `f3f8c8d8`; exact
  candidate tree `X4` `a6eaa88501b1d08b9e83c734d692c82376117e77`) on local branch
  `beryllium/mvp-m10`, unpushed; the
  [MVP M10 result review and acceptance record](mvp-m10-result-review-summary.md)
  holds the decision and the [M10 evidence record](mvp-m10-evidence.md)
  the evidence. All eight clean-checkout gates pass at `X4`, including
  stage 1 and `verify` (the M8 verdicts unchanged); the 25-run COM260
  campaign passes in 19 groups with three typed sessions and M9's log
  judged in every applicable run; the environment restores and the
  preflight pair is equal; `./mvp/mvp check` passes at exact `RC4`.
  Plan errata 1 and 2, the licence-manifest readings and the evidence
  record's departures stand. M8 remains inconclusive; the result claims
  no C-level contract proof, hardware validation or attestation.
  Release-path step 1 holds for RC4; M0 to M10 are complete and accepted.
  No merge, push, tag, publication, release-path step 2 or MVP 2.0 work
  was directed.

This branch preserves the research, completed pathfinder comparison inputs,
Architecture Model 0.1 implementation, and provisional roadmap for Beryllium.
The Helium pathfinder implementation phase is complete. Model 0.1 is accepted,
and responsible-human review accepted the non-runtime Model 0.2
checker/model/proof boundary and evidence on 2026-07-24. Responsible-human
direction selected the bounded single-hart runtime-planning phase later that
day. Responsible-human review accepted the exact plan and separately
authorized its fixed implementation profile on 2026-07-25. The R0 fixed
profile and layout freeze was accepted by responsible-human review on
2026-07-27. Responsible-human review accepted exact R1 pure-C mechanism
commit `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` on 2026-07-28. R2 bounded
plan commit `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` was accepted and R2
implementation separately authorized on 2026-07-28. Responsible-human review
accepted exact R2 implementation commit
`6e1cb579257c5dbe3234bd484fd091629e87181b` on 2026-07-28. Responsible-human
instruction `proceed with R3` separately authorized R3 on 2026-07-29. The
R3 boot-and-first-entry implementation is responsible-human accepted at exact
target `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` on 2026-07-29. The
[R3 review and acceptance record](single-hart-runtime-r3-review-summary.md)
preserves the exact instruction. Packet follow-up
`fcc0f267a1f59241f872c0a1d2a371a95a58cba6` is decision support, not
accepted implementation.
The responsible human accepted exact R4 target
[`0783dfc6557453fbac0da93a5364f2e6e2cb1f52`](single-hart-runtime-r4-review-summary.md)
on 2026-07-29. The acceptance-record follow-up HEAD
`87b136bc4889a04a58c2399e4eb81f7925cba5e0` is not implementation.
Responsible-human review accepted the
[bounded R5 plan](single-hart-runtime-r5-plan.md) target
`fecae6b62a507bdbb93d211262197a31f5422316` on 2026-07-30 and separately
authorized R5 implementation under that accepted plan; its
[review and acceptance record](single-hart-runtime-r5-plan-review-summary.md)
preserves both decisions. R5 implementation is an exact commit: accepted
target [`165f4d001a2b59b582b397bdea79ec4826168fdb`](single-hart-runtime-r5-review-summary.md)
over parent `9312c1355a23d411e3bdafb2183be342683a8ab9`. It is exact-target
validated and was responsible-human accepted on 2026-07-30 (see
[R5 checked-switch evidence](single-hart-runtime-r5-evidence.md) and the
[R5 review and acceptance record](single-hart-runtime-r5-review-summary.md));
the review packet commit `9bb89fe196740c5e3252bdccced6fb202df65e55` and the
acceptance-record follow-up are decision support, not implementation.
Responsible-human instructions `proceed to implement R6 exact` and
`proceed with all r6 implementation work` were received on 2026-07-30 and
authorize R6 implementation work under the master-plan R6 row.
Responsible-human review then **accepted** the
[bounded R6 plan](single-hart-runtime-r6-plan.md) target
`609867fdad75279c0913022909efd65c4a838909` on 2026-07-30; its
[review and acceptance record](single-hart-runtime-r6-plan-review-summary.md)
preserves both decisions and remains accepted history. Fixture D-15 exposed a
defect in that original plan, and the corrected plan target — exact commit
`75269f058ae578b0a76a113d6c05c0aaceeac8ec` (parent
`4bff41764cf8ec9275e771cd3c1ce124961da93a`), carrying Plan revision R6-A — was
**accepted on 2026-07-30**; its
[plan revision review and acceptance record](single-hart-runtime-r6-plan-revision-review-summary.md)
records that decision. D-15 implementation may resume under the two
already-recorded implementation authorization instructions, within the
accepted corrected plan's scope; local R6 implementation remains unreviewed,
unaccepted, and incomplete, and complete R6 requires its own exact-commit
review and separate acceptance. Resumed D-15 work then exposed two
bookkeeping defects in that accepted corrected plan — a false `.monitor.text`
layout claim and an impossible raw-trace retention rule — so narrow
[Plan revision R6-B](single-hart-runtime-r6-plan.md#plan-revision-r6-b-d-15-image-layout-and-trace-retention)
at exact target `6d6464c6c937abccd59df932006c1049fd79fac6` (parent
`4d6c3c9b0899c7a30b2150ff0d4067369ccef774`) was **accepted on 2026-07-30**,
recorded in its
[R6-B plan revision review and acceptance record](single-hart-runtime-r6-plan-r6b-review-summary.md);
R6 integration and evidence work may resume under the already-recorded
implementation authorization, with every pinned value re-derived from a
checked run at the exact implementation commit. Under that authorization the
R6 package is now complete, root-integrated, fully checked, and
**responsible-human accepted at exact target
`7ba3649f03cf13b65df33020e345d361cce2993a` on 2026-08-05**:
`./be r6-check` and `./be r6-evidence` pass
(see [R6 adversarial-image evidence](single-hart-runtime-r6-evidence.md)).
R6 implementation spans exact target
`7ba3649f03cf13b65df33020e345d361cce2993a` and parent/initial implementation
`9ed5ad7069b6067f03e1923c09937fe218240a59` over base
`4012d794e769fd4029b11f6f45e366ed0ef117f5`, and it was validated on that exact
commit in standalone and full fresh detached worktrees. The
[R6 review and acceptance record](single-hart-runtime-r6-review-summary.md)
records the explicit instruction `Accept exact commit
7ba3649f03cf13b65df33020e345d361cce2993a`. Its packet commit
`e0daa12b34ca4e30a601bd435ef038d5bc4088f1` and the acceptance-record
follow-up are decision support rather than implementation.
The responsible-human instruction `once complete, commit and push, then
commence R7` authorized R7 after the R6 acceptance record was committed and
privately pushed. The
[bounded R7 proof and evidence plan](single-hart-runtime-r7-plan.md) is
responsible-human accepted at exact target
`18c43596d308052cfad67edc6e2cb8f543f75600` on 2026-08-05; its
[review and acceptance record](single-hart-runtime-r7-plan-review-summary.md)
records the decision. The bounded `tests/r7/` package is complete,
committed, and **responsible-human accepted at exact implementation target
`9bf22913d67e9b72286813cd5f7993a9ad3857a8`** on 2026-08-05 (immediate parent
and superseded first candidate `95639afb0ab57959a32d055f7b7f9bdb474fe762`),
after exact-target
validation in two independent fresh detached worktrees;
[Plan revision R7-A](single-hart-runtime-r7-plan.md#plan-revision-r7-a-authorized-predecessor-acceptance-pin-refresh),
which enumerates exactly six predecessor acceptance-pin refreshes and applies
none, is separately accepted at exact target
`0605028220e3795d99393156d0bfb7d6a7d631a4` (parent
`014b0f654ed65758bb99112f401529975d2dfd44`) on 2026-08-05 and recorded in its
[review and acceptance record](single-hart-runtime-r7-plan-r7a-review-summary.md).
Root integration is applied within that enumeration, with all six pins
re-derived at the exact prospective content and no seventh acceptance update;
the results are recorded in the
[R7 bounded exact-proof and evidence record](single-hart-runtime-r7-evidence.md),
and the exact-target decision is carried by the
[R7 review and acceptance record](single-hart-runtime-r7-review-summary.md).
Its packet commit `a4cc49d3d41e4bc22a7b17def836e6c4746f3c82` and the
acceptance-record follow-up are decision support, not implementation.
The proof is bounded rather than whole-system formal verification, C
refinement is not claimed, hardware validation remains `NOT RUN`, the
accepted target's retained `r7_acceptance=not-reviewed` fields stay
pre-decision exact-target evidence,
and public push, tag, publication, and release remain blocked. Responsible-
human direction on 2026-08-07 authorized R8 planning and selected the combined
single-hart K3 core-validation direction. The
[`single-hart-runtime-r8-plan.md`](single-hart-runtime-r8-plan.md) is accepted
at exact target `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` as of
2026-08-07, and its
[review and acceptance record](single-hart-runtime-r8-plan-review-summary.md)
carries the plan decision and the separate instruction `Authorize R8
implementation under accepted plan 7d0f0cbf…; proceed with R8-H0`.
Implementation is authorized only for non-privileged H0. Local unaccepted H0
work exposed a documentation-path and exact-candidate identity defect, so
[Plan revision R8-A](single-hart-runtime-r8-plan.md#plan-revision-r8-a-h0-documentation-boundary-and-candidate-identity)
is accepted at exact target
`8fa9d672cfcfb81ab68d9ed9553a5af48b884932` over parent
`cb0ac2a0f818ac57f2866cb7815767145608cf58` as of 2026-08-07. The
[R8-A review and acceptance record](single-hart-runtime-r8-plan-r8a-review-summary.md)
records the exact instruction
`accept exact 8fa9d672cfcfb81ab68d9ed9553a5af48b884932`. The immutable
target's proposed/paused fields remain frozen pre-decision content. Acceptance
only unpauses already authorized non-privileged H0 after the
acceptance-record commit, whose full SHA is the required H0 base; work is not
started or accepted by this record and every candidate identity must be
freshly derived.
Plan revision R8-C is responsible-human accepted at exact target
`f47ae60266a467ca1a7704fd9a50b140e0f31bb0` over parent
`fc6795b03b5f68849fe5ef882d7e2cae77ab4e90` as of 2026-09-17 by the exact
instruction quoted in the
[R8-C review and acceptance record](single-hart-runtime-r8-plan-r8c-review-summary.md).
The immutable target's `r8_plan_revision_r8c=proposed-not-reviewed` field
remains frozen pre-decision content.

The responsible human accepted exact bounded non-privileged H0/R8-C target
`1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` (parent
`d18b1c9c6ca8a0f2285f820ec960258620ae4b50`, tree
`7a9d80d08d0abb771d43cf76a4a297d9d668b375`) on 2026-09-17 by the
instruction `accept exact target
1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4`. The responsible human confirmed
that existing instruction and record as genuine on 2026-09-24; this
reconciles current status and does not create a second acceptance date. The
[H0/R8-C review and acceptance record](single-hart-runtime-r8-h0-review-summary.md)
carries the exact decision.

The accepted target remains blocked and not exit-ready: 147 rows, 118
`UNKNOWN` values, 80 H0-acceptance blockers, 33 H1-completion blockers, three
H2-entry blockers, `BLOCKED-NOT-READY`, and `r8_h0_exit=not-met`. The
historical active-line H0 source at
`102f2b0569396bf33ed2177ea5b7558cf5e6fbaa` reports 81 blockers and remains
unaccepted; its count is not the accepted-target count. COM260 read-only
inventory and troubleshooting on 2026-09-24 are session-local discovery, not
retained R8 hardware evidence; K3 remains `NOT RUN` and the development
kernel/BSP remains `UNDECIDED`. Prospective tree
`8f192c530b03ea33496b95f11ea46537ac02d0b6` is uncommitted diagnostic
content only. A separately reviewed plan, exact base and relation, and
explicit authorization are required before any H0 successor may incorporate
COM260 facts. H1-H4 remain not started and unauthorized.

On 2026-09-29, the responsible human selected maintenance packet Option B:
planning only. The separate
[R8 active-line maintenance plan](single-hart-runtime-r8-active-line-maintenance-plan.md)
uses identity `R8-ALM1`. It is not R8-B, is not a revision of the accepted R8
K3 core-validation plan, and transfers no accepted H0 evidence/readiness.
Independent
[plan review](single-hart-runtime-r8-active-line-maintenance-plan-review-summary.md)
found two significant open defects and recommends revisions: the future
direct-child relation cannot preserve the review and a later acceptance record
on the active line, and exact current-line `r8-check` rejects silently during
launcher authentication rather than reaching the historical first whole-diff
fixture. The historical `102f2b...` package separately reaches that fixture in
the retained maintenance environment. The original exact plan target remains
proposed and unaccepted. Proposed **Plan revision R8-ALM1-A** corrects both
findings: a future implementation may start only from the exact later
acceptance-record/current-line SHA named by a separate implementation
authorization, and validation must independently cover current-line silent
exit `126` and historical whole-diff exit `2`. Independent
[R8-ALM1-A review](single-hart-runtime-r8-active-line-maintenance-plan-r8alm1a-review-summary.md)
of exact revised target `95cce2f692543da67054ec2d6061eb08a4061253`
(parent `255aa176923581bf9248bfce5bc94217ff5577a8`, tree
`f826204b12701114993743f949c6ee71a72def5c`) finds both first-packet
findings resolved, finds no significant open plan defect, and recommends
acceptance as plan text only. The responsible human accepted that exact
target as plan text only on 2026-09-29 by the exact instruction `accept`.
The [R8-ALM1-A review and acceptance record](single-hart-runtime-r8-active-line-maintenance-plan-r8alm1a-review-summary.md)
carries the decision while the immutable target retains
`r8_active_line_maintenance_plan=proposed-not-reviewed` and
`r8_active_line_maintenance_implementation=not-authorized` as frozen
pre-decision content. Packet commit
`788b0b6752b706ece8dc51dc2c0c5dca3e56376f`, original target
`6bb3349b...`, and first packet `255aa176...` remain immutable decision
support, not accepted plan text or implementation authority.

Acceptance authorizes no implementation. Any future R8-ALM1 implementation
requires a separate exact instruction naming the full SHA of the later plan
acceptance-record/current-line base, the exact candidate relation, and the
complete plan inventory. Accepted H0 target `1999ee70...` remains accepted
but `BLOCKED-NOT-READY`; no H0 evidence or readiness transfers. H1-H4 remain
not started, K3 and hardware remain `NOT RUN`, and root integration,
dependencies, pins, tool locks, runtime/proof paths, push, tag, publication,
release, and migration remain unchanged or blocked.

Independent review requested revisions to the first KVM0 proposal at exact
target `459184dd8fe9c5da20e27a9e277a076685a520cb`; its first packet commit
`8348b18a2c00c992e8fbf744f2004dfcd55500e6` remains historical and
unaccepted. [Plan revision K0-A](k3-kvm0-plan.md) is now the current
accepted planning boundary at exact target
`5227266ceddb664a1595e22e5a92da57a013652f`. Responsible-human review
accepted that exact target on 2026-09-25 by the instruction
`5227266ceddb664a1595e22e5a92da57a013652f is accepted exactly`; the
[K0-A review and acceptance record](k3-kvm0-plan-k0a-review-summary.md)
carries the decision. The immutable plan retains its proposed pre-decision
fields. Separate K0-I authority selected exact base
`e4e0209f19596e0cbccbb6bb4de84c50bbd11f92` and the plan's exact ten-path
destination offline-tooling inventory. Responsible-human review accepted
exact K0-I target `abd092a1f2734c720a205803c29496fe2245b0ef` on 2026-09-26
by the instruction
`accept exact target abd092a1f2734c720a205803c29496fe2245b0ef`; the
[K0-I implementation review and acceptance record](k3-kvm0-k0i-review-summary.md)
carries that decision. K0-P and K0-I are satisfied at their exact boundaries.
At `2026-09-28T00:17:59.413Z`, the responsible-human instruction
`Fleet deployed: proceed with K0-S per above` separately authorized bounded
K0-S source-owner preparation. The private locator for
`k0s-source-owner-workspace-1` was supplied at
`2026-09-28T02:06:12.937Z` and is intentionally omitted; `continue` followed at
`2026-09-28T02:07:09.427Z`, and the conditional instruction
`if repairable, proceed to repair` followed at
`2026-09-28T03:15:09.437Z`. The
[K0-S authorization-record draft](k3-kvm0-k0s-authorization-record.md)
records that exact sequence. Read-only audit and profile drafting have
completed bounded repair. Exact target
`c65705582c243dd908ff47d3189df07601167400` records
`k0s-source-owner-profile-v1` with 35 files and 41 path/type/mode entries; its
private locator is omitted and is not evidence. Its target-time `FILES.modes`
SHA-256 is
`f8f130dbcbddfa557298bab1a9bcac859a4ec8af8adb219d271e467c52ffa5db`
and its target-time `SHA256SUMS` SHA-256 is
`57d0753ab55333ca29198d894e176c5a270e52747e29303b6ad1d2bb8cd606b3`;
target-time source-profile SHA-256 is
`aaa4b83d216cd932fd77c32230dded6ff206f6224224670bcac2169bd5a36238`.
The target-time restricted provenance map is mode `0600`, 42,570 bytes,
SHA-256
`eb734dc9dad08a2ec5e73d4f5b50a4fe59ed9100580dcf0490687dfb2f8943c4`,
and had complete 43-of-43 coverage; exact-minimum provenance remains
access-controlled, hash-bound, publication-excluded, and not printed.
Static/profile checks, controller self-hash preflight, and 25 host-only fake
tests passed for that exact target. Its draft/not-reviewed fields, old hashes,
and zero-ref observations remain frozen target-time evidence. The external
package has since evolved outside Git and remains mutable and unaccepted.
Proposed commit
`c1c7e254143f99d4ad3cdbf25021a76364d6d75a` and tree
`a5f77b5acef26d8975fe756512edbd2413fa1239` remain an
unaccepted/unretained preparation input, not rejected source. No
destination import/install, real selftest/K0-X, serial, hardware, readiness,
result, K3 host, accepted R8 byte, H0 row, BSP, successor, root integration,
dependency, pin, or publication state changes. The literals
`branch_label=main` and `source-ready-not-run` remain future K0-I contract
values and do not state current K0-S readiness.

Exact bounded preparation/status target
`c65705582c243dd908ff47d3189df07601167400` (parent
`478d5886e8dc261546e3373421e0ab428062f82a`, tree
`a3f1f74c42d2c583aae8c6aa486f1f97f5379439`) was responsible-human accepted
on 2026-09-29 by the exact instruction
`accept c65705582c243dd908ff47d3189df07601167400`. Its
[review and acceptance record](k3-kvm0-k0s-review-summary.md) carries that
decision. Acceptance covers only the target's accuracy as bounded
preparation/status documentation; it does not accept the external package,
source candidate, route, bundle, artifacts, readiness, import, execution, or
result.

## Latest decision records

> **Exact KVM0 K0-S preparation/status target
> `c65705582c243dd908ff47d3189df07601167400` was responsible-human accepted
> on 2026-09-29** over parent
> `478d5886e8dc261546e3373421e0ab428062f82a`, tree
> `a3f1f74c42d2c583aae8c6aa486f1f97f5379439`, by the exact instruction
> `accept c65705582c243dd908ff47d3189df07601167400`. The
> [K0-S source-owner preparation review and acceptance record](k3-kvm0-k0s-review-summary.md)
> carries the decision. Packet commit
> `d3499c3a7cd4b339fd5f24b145a651844a72d672` and the acceptance-record
> follow-up are decision support, not accepted target content. The immutable
> target retains its `draft-not-reviewed`, no-documentation-target, old hash,
> and zero-ref fields as target-time evidence. Acceptance does not make K0-S
> ready or complete and does not accept source candidate
> `c1c7e254143f99d4ad3cdbf25021a76364d6d75a`, current package bytes, an
> immutable route, bundle, artifacts, missing inputs, import/install, real
> selftests, serial, K0-X/K0-R, B0/B1, R8 successors/H1-H4, hardware, BSP,
> push, tag, publication, or release. Those route and containment statements
> are frozen target-time evidence. Current follow-up status is that the target
> is privately pushed, source `c1c7e254...` is private-remote-contained, and
> the selected exact-Git route is complete at that boundary. The current
> package remains unaccepted and not ready because the deferred K3/offline
> payload and external archive are absent. K3/Beryllium/R8 hardware remain
> `NOT-RUN`; the development
> kernel/BSP remains `UNDECIDED`.

> **Bounded KVM0 K0-S source-owner preparation was responsible-human
> authorized at `2026-09-28T00:17:59.413Z`** by the exact instruction
> `Fleet deployed: proceed with K0-S per above`, under accepted K0-A plan target
> `5227266ceddb664a1595e22e5a92da57a013652f` and accepted K0-I target
> `abd092a1f2734c720a205803c29496fe2245b0ef`. The
> [K0-S source-owner preparation authorization-record draft](k3-kvm0-k0s-authorization-record.md)
> records the exact session evidence and boundary. The private locator for
> `k0s-source-owner-workspace-1` was supplied at
> `2026-09-28T02:06:12.937Z` and is intentionally omitted; `continue` and the later conditional
> repair instruction allowed read-only audit, profile drafting, and bounded
> repair. Exact target `c65705582c243dd908ff47d3189df07601167400` records
> `k0s-source-owner-profile-v1` at target-time deterministic
> file/mode/checksum identities and passed static/profile checks, controller
> self-hash preflight, complete 43-of-43 restricted mapping coverage, and 25
> host-only fake tests; its private locator is not evidence.
> The draft/no-target fields remain frozen target-time content; the later
> review and acceptance record carries the 2026-09-29 decision.
> The package is outside Git and mutable; authorization, preparation, and
> status-target acceptance do not make K0-S ready or complete. Proposed
> candidate containment is zero checked local branches and zero checked tags,
> the current authorized checkout is unrelated, and no clean immutable
> referenced source target exists. The source commit
> `c1c7e254143f99d4ad3cdbf25021a76364d6d75a`, tree
> `a5f77b5acef26d8975fe756512edbd2413fa1239`, remains an
> unaccepted/unretained preparation input, not rejected source. Missing
> retained `SUMMARY.tsv`/skip-output bytes and `UNKNOWN`
> operational values remain blockers. `branch_label=main` and
> `source-ready-not-run` remain future K0-I contract literals, not current
> readiness. No destination import/install, real
> selftest/K0-X, serial, or hardware execution occurred or is authorized.
> K0-R, K0-G, B0/B1,
> R8 successors/H1-H4, root integration, BSP selection, push, tag,
> publication, migration, release, and upstream work remain blocked or
> unauthorized. KVM0 and all Beryllium/R8 K3 hardware results remain
> `NOT-RUN`.

> **Exact KVM0 K0-I destination offline-tooling target
> `abd092a1f2734c720a205803c29496fe2245b0ef` was responsible-human accepted
> on 2026-09-26** over parent
> `d490183d0177a5ba38276c572685f0c2e4ee3863`, tree
> `f683c1b634e8cd07ba967960d9e00ef2c6a76efa`, from authorized base
> `e4e0209f19596e0cbccbb6bb4de84c50bbd11f92`, by the exact instruction
> `accept exact target abd092a1f2734c720a205803c29496fe2245b0ef`. The
> [K0-I implementation review and acceptance record](k3-kvm0-k0i-review-summary.md)
> records the decision and the two retained low-severity observations.
> Prior candidates `1795400868c6d6cb3a6a9fed8ce069424c7bc2ef` and
> `d490183d0177a5ba38276c572685f0c2e4ee3863` remain superseded and
> unaccepted. The acceptance-record follow-up is decision support, not
> implementation, imported evidence, or result bytes. K0-I scope is
> offline-tooling-only. At that decision, K0-S, K0-X, K0-R, K0-G,
> K3/private-source access, hardware execution, B0/B1, R8 successors, root
> integration, dependency/pin changes, persistent Fedora guest qualification,
> push, tag, publication, migration, release, and upstream work remained
> blocked or unauthorized. The later K0-S record above changes only bounded
> source-preparation authority; all other exclusions remain.
> KVM0, Beryllium K3, and R8 hardware remain `NOT-RUN`.

> **Exact KVM0 Plan revision K0-A target
> `5227266ceddb664a1595e22e5a92da57a013652f` was responsible-human accepted
> on 2026-09-25** over parent
> `8348b18a2c00c992e8fbf744f2004dfcd55500e6`, tree
> `2a716a0ca69a7d0ada92b978bd77704fbfc8910b`, by the exact instruction
> `5227266ceddb664a1595e22e5a92da57a013652f is accepted exactly`. The
> [K0-A review and acceptance record](k3-kvm0-plan-k0a-review-summary.md)
> preserves the pre-decision review history and records the decision. The
> immutable target retains its proposed fields. Packet commit
> `6369804904eb28554c65886db93f0d30be80fcab` and the acceptance-record
> follow-up are decision support, not plan text, implementation, execution, or
> result evidence. That 2026-09-25 decision satisfied K0-P only; the later
> K0-I acceptance is recorded immediately above. At the K0-A decision, K0-S,
> K0-X, K0-R, K3 access, B0/B1, an H0 successor, H1-H4, BSP selection,
> integration, checker or pin changes, push, tag, publication, migration,
> release, and upstream work remained blocked or unauthorized. The later K0-S
> record changes only bounded source-preparation authority. KVM0, Beryllium
> K3, and R8 hardware remain `NOT-RUN`.

> **Exact bounded non-privileged H0/R8-C target
> `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` was responsible-human accepted
> on 2026-09-17** by the instruction `accept exact target
> 1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4`. On 2026-09-24, the responsible
> human confirmed that existing instruction and record as genuine; this is a
> current-line reconciliation, not a second acceptance. The
> [H0/R8-C review and acceptance record](single-hart-runtime-r8-h0-review-summary.md)
> preserves the target, parent, tree, packet, acceptance-record commit,
> reported exact-target gates, and residuals. Acceptance does not erase 80 H0
> blockers, 118 `UNKNOWN` values, `BLOCKED-NOT-READY`, or
> `r8_h0_exit=not-met`, and it does not authorize H1-H4, K3 execution, root
> integration, predecessor-pin refresh, dependencies, a successor, push,
> tag, publication, release, or migration.

> **Exact R8-C plan-revision target
> `f47ae60266a467ca1a7704fd9a50b140e0f31bb0` was responsible-human accepted
> on 2026-09-17** by the exact instruction `Accept exact R8-C plan commit
> f47ae60266a467ca1a7704fd9a50b140e0f31bb0. Record this decision only; do not
> implement R8-C or start a successor H0 candidate.` The
> [R8-C review and acceptance record](single-hart-runtime-r8-plan-r8c-review-summary.md)
> carries the decision. The immutable target remains byte unchanged and
> retains its proposed pre-decision field. R8-C implementation authorization
> is none, no implementation base or relation is selected, the blocked H0
> candidate remains unchanged and unaccepted, and successor H0, H1-H4, K3
> execution, push, tag, publication, release, and migration remain
> unauthorized, `NOT RUN`, or blocked. That sentence records the plan-only
> boundary at the time of the R8-C decision; the later exact H0/R8-C
> acceptance and current status are recorded in the block above.

> **Exact R8-A plan-revision target
> `8fa9d672cfcfb81ab68d9ed9553a5af48b884932` was responsible-human accepted
> on 2026-08-07** by the explicit instruction
> `accept exact 8fa9d672cfcfb81ab68d9ed9553a5af48b884932`. The
> [R8-A review and acceptance record](single-hart-runtime-r8-plan-r8a-review-summary.md)
> carries the decision. The immutable target plan remains byte unchanged and
> retains its proposed/paused pre-decision fields. Acceptance only unpauses
> the already authorized non-privileged H0 work after this record commit,
> whose full SHA is exact H0 implementation base
> `1f6109f0d0371eb3707e296c3416e8c55235683e`. H0 has since resumed locally
> from that base as exact candidate
> `6e93461f6ea097cb095e31558f6956dc6c0c2708`, but it remains not reviewed,
> blocked, and unaccepted; H1, K3 execution, root integration, dependencies,
> public push, tag, publication, release, and every successor remain blocked.
> This is retained pre-H0-acceptance history; current status is recorded above.

> **Exact R8 plan target
> `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` was responsible-human accepted
> on 2026-08-07** by the explicit instruction
> `accept exact 7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`. The
> [R8 plan review and acceptance record](single-hart-runtime-r8-plan-review-summary.md)
> carries the decision. Acceptance covers the plan only. A later separate
> instruction, `Authorize R8 implementation under accepted plan 7d0f0cbf…;
> proceed with R8-H0`, authorizes only the non-privileged H0 freeze. Plan
> revision R8-A is separately accepted at exact target
> `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`. This is the original plan and
> authorization boundary; the later exact H0/R8-C acceptance is recorded
> above. K3 execution remains `NOT RUN`.

> **Exact R5 implementation target
> `165f4d001a2b59b582b397bdea79ec4826168fdb` was responsible-human accepted
> on 2026-07-30**, by the explicit instruction
> `accept exact 165f4d001a2b59b582b397bdea79ec4826168fdb`, under accepted
> plan commit `fecae6b62a507bdbb93d211262197a31f5422316` and its separate
> implementation authorization. The
> [R5 plan review and acceptance record](single-hart-runtime-r5-plan-review-summary.md)
> preserves both earlier decisions, and the
> [R5 review and acceptance record](single-hart-runtime-r5-review-summary.md)
> preserves this one. The accepted implementation spans that target and
> parent `9312c1355a23d411e3bdafb2183be342683a8ab9`, exact-target validated
> (see [R5 evidence](single-hart-runtime-r5-evidence.md)); status is
> `r5_acceptance=accepted` with
> `r5_accepted_commit=165f4d001a2b59b582b397bdea79ec4826168fdb`. The review
> packet commit `9bb89fe196740c5e3252bdccced6fb202df65e55` and the
> acceptance-record follow-up are not implementation. Do not infer R6
> acceptance, hardware, formal, push, tag, publication, or release authority.
> The recorded `proceed to implement R6 exact` and
> `proceed with all r6 implementation work` instructions authorize R6
> implementation work under the master-plan R6 row; the
> [bounded R6 plan](single-hart-runtime-r6-plan.md) target
> `609867fdad75279c0913022909efd65c4a838909` was accepted on 2026-07-30, and
> its
> [review and acceptance record](single-hart-runtime-r6-plan-review-summary.md)
> records both decisions. R6 implementation then started locally. Fixture D-15 exposed a defect in
> that original plan; the corrected plan target, exact commit
> `75269f058ae578b0a76a113d6c05c0aaceeac8ec`, was **accepted on 2026-07-30**,
> its
> [plan revision review and acceptance record](single-hart-runtime-r6-plan-revision-review-summary.md)
> records that decision, and D-15 may resume under the already-recorded
> implementation authorization. Resumed D-15 work then exposed two
> bookkeeping defects in that accepted corrected plan, so narrow
> [Plan revision R6-B](single-hart-runtime-r6-plan.md#plan-revision-r6-b-d-15-image-layout-and-trace-retention)
> at exact target `6d6464c6c937abccd59df932006c1049fd79fac6` was **accepted
> on 2026-07-30**, so R6 integration and evidence work may resume with every
> pinned value re-derived at the exact implementation commit. The R6 package
> is now complete, root-integrated, fully checked, and accepted at exact
> target `7ba3649f03cf13b65df33020e345d361cce2993a` on 2026-08-05 (parent
> `9ed5ad7069b6067f03e1923c09937fe218240a59`), as recorded in the
> [R6 review and acceptance record](single-hart-runtime-r6-review-summary.md).
> R7 was then separately authorized, its
> [bounded plan](single-hart-runtime-r7-plan.md) was **accepted at exact
> target `18c43596d308052cfad67edc6e2cb8f543f75600` on 2026-08-05**, and its
> narrow
> [Plan revision R7-A](single-hart-runtime-r7-plan.md#plan-revision-r7-a-authorized-predecessor-acceptance-pin-refresh)
> was **accepted at exact target
> `0605028220e3795d99393156d0bfb7d6a7d631a4` on 2026-08-05** by the explicit
> instruction `Accept exact 0605028220e3795d99393156d0bfb7d6a7d631a4`, as
> recorded in its
> [review and acceptance record](single-hart-runtime-r7-plan-r7a-review-summary.md).
> That acceptance authorizes resuming R7 root integration under exactly six
> freshly re-derived predecessor acceptance pins and no seventh; it accepts no
> R7 implementation, evidence, proof, or hardware result, and R8, push, tag,
> publication, and release remain blocked. The exact R7 implementation target
> `9bf22913d67e9b72286813cd5f7993a9ad3857a8` is committed, exact-target
> validated, and **responsible-human accepted on 2026-08-05** by the explicit
> instruction `Accept exact 9bf22913d67e9b72286813cd5f7993a9ad3857a8`, as
> recorded in the
> [R7 review and acceptance record](single-hart-runtime-r7-review-summary.md).
> That acceptance covers only that exact commit and its bounded claim
> boundary: it adds no hardware, C-refinement, or whole-system verification
> evidence, and R8, push, tag, publication, and release stay blocked.

Current decision records:
[R3 review and acceptance record](single-hart-runtime-r3-review-summary.md),
[R4 review and acceptance record](single-hart-runtime-r4-review-summary.md),
the
[R5 plan review and acceptance record](single-hart-runtime-r5-plan-review-summary.md),
and the
[R5 implementation review and acceptance record](single-hart-runtime-r5-review-summary.md).
The R5 plan is accepted, its implementation was separately authorized, and
the exact implementation target `165f4d001a2b59b582b397bdea79ec4826168fdb`
is responsible-human accepted as of 2026-07-30
(see [R5 checked-switch evidence](single-hart-runtime-r5-evidence.md)). The
[R6 bounded plan](single-hart-runtime-r6-plan.md) is accepted at exact target
`609867fdad75279c0913022909efd65c4a838909`, and its
[plan review and acceptance record](single-hart-runtime-r6-plan-review-summary.md)
records that acceptance, the separate implementation authorization, and the
post-acceptance D-15 discovery; R6 implementation is complete, committed, and
accepted at its exact target. The corrected plan target
`75269f058ae578b0a76a113d6c05c0aaceeac8ec`, carrying Plan revision R6-A, is
**accepted** as of 2026-07-30, and its
[plan revision review and acceptance record](single-hart-runtime-r6-plan-revision-review-summary.md)
records that decision. Narrow
[Plan revision R6-B](single-hart-runtime-r6-plan.md#plan-revision-r6-b-d-15-image-layout-and-trace-retention),
correcting the D-15 layout facts and the raw-trace retention rule, is
**accepted** at exact target `6d6464c6c937abccd59df932006c1049fd79fac6` as of
2026-07-30; its
[R6-B plan revision review and acceptance record](single-hart-runtime-r6-plan-r6b-review-summary.md)
records that decision, under which R6 integration and evidence work may
resume with every pinned value re-derived at the exact implementation commit.
The resulting R6 package is complete, root-integrated, fully checked, and
accepted at exact target
`7ba3649f03cf13b65df33020e345d361cce2993a` (parent
`9ed5ad7069b6067f03e1923c09937fe218240a59`); its
[R6 adversarial-image evidence](single-hart-runtime-r6-evidence.md) is a
pre-decision evidence record rather than an acceptance, and its
[R6 review and acceptance record](single-hart-runtime-r6-review-summary.md)
carries the 2026-08-05 decision.
Supporting accepted target evidence:
[R3 boot and first-entry evidence](single-hart-runtime-r3-evidence.md) and
[R4 trap-and-context evidence](single-hart-runtime-r4-evidence.md).
The R4 acceptance-record follow-up HEAD
`87b136bc4889a04a58c2399e4eb81f7925cba5e0` is not implementation.
The [R7 bounded plan](single-hart-runtime-r7-plan.md) is **accepted** at exact
target `18c43596d308052cfad67edc6e2cb8f543f75600`, recorded in its
[plan review and acceptance record](single-hart-runtime-r7-plan-review-summary.md),
and its narrow
[Plan revision R7-A](single-hart-runtime-r7-plan.md#plan-revision-r7-a-authorized-predecessor-acceptance-pin-refresh)
is **accepted** at exact target `0605028220e3795d99393156d0bfb7d6a7d631a4` as
of 2026-08-05, recorded in the
[R7-A plan revision review and acceptance record](single-hart-runtime-r7-plan-r7a-review-summary.md).
The `tests/r7/` package is **accepted** at exact implementation target
`9bf22913d67e9b72286813cd5f7993a9ad3857a8` as of 2026-08-05, over superseded
first candidate `95639afb0ab57959a32d055f7b7f9bdb474fe762`;
root integration is applied within that six-constant enumeration, its
results are recorded in the
[R7 bounded exact-proof and evidence record](single-hart-runtime-r7-evidence.md),
and the exact-target decision is carried by the
[R7 review and acceptance record](single-hart-runtime-r7-review-summary.md).

Previously accepted records include:
[R2 implementation review and acceptance record](single-hart-runtime-r2-review-summary.md)
for `6e1cb579257c5dbe3234bd484fd091629e87181b`, accepted on 2026-07-28, and the
[R2 plan review and acceptance record](single-hart-runtime-r2-plan-review-summary.md)
for `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce`, accepted on 2026-07-28;
R2 implementation separately authorized on the same date.

## Project names

- **Helium** (`He` / `he`) is the completed bounded pathfinder.
- **Beryllium** (`Be` / `be`) is the repository, project, and future
  hypervisor name.
- Active Beryllium technical identifiers use `be_` / `BE_`; the RFC Linux
  layout uses `virt/be/`, `arch/<arch>/be/`, `drivers/virt/be/`, and
  `include/uapi/linux/be.h`.

Helium 0.5.0 removes the former pathfinder identity from active code,
interfaces, artifacts, documentation, and private branch refs. Exact earlier
evidence commits are not rewritten and retain their historical strings.

The current private repository is the internal development history. A future
public release will migrate reviewed code and selected artifacts into a clean
Beryllium project repository and then archive this internal repository. That
is a separate human-approved release operation, not authorization for a
public push now.

## Documents

- `project-orientation.md`: scan-first returning-human guide to current
  status, package hierarchy, the K3 bring-up path, evidence
  transfer limits, next decisions, and copyable inspection commands.
- `project-snapshot-mvp-1.0-rc2.md`: a dated (2026-10-30) overview as of
  MVP 1.0 release candidate 2: the goal, the milestone ladder, the MVP
  milestones, the release path and position, what the MVP demonstrates
  and how to record it, the formal-verification status, the gap from the
  Helium pathfinder, and a likely verification route for the monitor. A
  snapshot subordinate to the roadmap, the plans, and the handoff.
- `post-rc3-candidates-2026-10-31.md`: decision support, one page, on
  the responsible human's direction of 2026-10-31 to take more time for
  a useful MVP 1.0: the candidates after release candidate 3
  (interactive guests, the first verification plan, milestone 3's
  dynamic part, measured launch, a device path, the I/O service domain,
  the later milestones, the release path) compared by what a researcher
  gains, size, board time, dependencies, and risk to the claim and the
  model. It selects nothing. Its later sections record the responsible
  human's directions of the same day and the LiteBox re-analysis.
- `rc3-review-remediation-review-summary.md` and
  `mvp-debt-4-review-summary.md`: the review packets of debt sweeps 3
  (the twelve rows of the Rhyolite reviews of the public RC3 snapshot;
  accepted 2026-11-01 at `3b7ab0e3`, the packet carrying the decision
  record) and 4 (items 99, 100, 102, and 105 and `SECURITY.md`;
  accepted 2026-11-01 at `d162c60d`, likewise); and
  `mvp-debt-5-review-summary.md`, the review and acceptance record of
  debt sweep 5 (item 95, the closure from public sources; accepted
  2026-11-01 at `e8ab73b7`).
- `mvp-plan-s3c-review-summary.md`: the decision packet for Plan
  revision S3-C of the MVP plan (the MVP ladder; MVP 1.0 widened to M7
  interactive guests, M8 the first verification plan, M9 measurement,
  and M10 release candidate 4), with a brief for the independent review
  the responsible human directed; the review and acceptance record
  (accepted 2026-11-01 at `27d2e557`, Q27 to Q46 at their defaults).
- `mvp-m7-plan.md`: the bounded plan of milestone M7, interactive guests
  (console input through the control hart, the focus sequence, the
  input ring, the served DBCN read, BusyBox and musl, scripted sessions,
  the typed characterization; D-1 to D-12, the trigger evaluation, the
  claim words, M7-1 to M7-6, Q1 to Q16). Accepted 2026-11-01 at
  `4f4d094e`.
- `mvp-m7-plan-review-summary.md`: its review and acceptance record.
- `mvp-m7-evidence.md`: the M7 evidence record (the packages, the
  departures, the model, the gates at `8418a377`, the board step, the
  stops and the soft limit, the open items, the claim boundary).
- `mvp-m7-result-review-summary.md`: the M7 result review and
  acceptance record (exact commit `e1a6395e`, accepted 2026-11-02).
- `mvp-m8-plan.md`: the bounded plan of milestone M8, the first
  verification plan (stage 1's concrete operational model and its
  obligations, premises, and gate; stage 2's pilot of Frama-C/WP, CN,
  and CBMC on two leaves under a registered decision rule; the fixed
  claim sentence; D-1 to D-13, M8-1 to M8-7, Q1 to Q17). Accepted
  2026-11-02 at `7a0c74ae`.
- `mvp-m8-plan-review-summary.md`: its review and acceptance record.
- `mvp-m8-specifications.md`: M8-2's specification document, drafted
  from the plans and the claim: the stage-1 property list P1 to P9 with
  the memory semantics and the protocol steps, Leaf A's contract
  (`be_mvp_denial_decide` and its helpers), Leaf B's per-call properties
  (`mvp-ring.c`), the mutation and vacuity expectations, the claim
  classes. Frozen at `004f31ae` (SHA-256 `ade32fa6…`) and accepted by the
  responsible human as reviewer of record on 2026-11-02 (`accept
  004f31ae`), the hash unchanged; three errata the stage-1 proofs found
  (S-1 to S-3: P1 scoped to the block's immutable words, P5 below the
  exit ceiling, P6's parked domain still taking TERMINATE) are recorded
  in the M8 plan's decision record, not in the document. **Revision 1**
  (`93a8d136`, SHA-256 `aeb75682…`; accepted 2026-11-03, `accept
  93a8d136`, acceptance record `928b07bd`): nine clauses of sections 4
  and 5 corrected where the pilot's arms found the accepted wording to
  disagree with the leaves as the M1 plan and the ring header fix them
  (specification errata, not code defects); sections 1 to 3, 6, and 7
  unchanged; the re-run's further erratum S-5 (the `room` row) is
  recorded in the plan's decision record, not in the document.
- `mvp-m8-specifications-revision-1-review-summary.md`: the decision
  packet for the specification's Revision 1 (the nine rows with their
  evidence; the claim boundary; the re-run that follows acceptance).
- `mvp-m8-evidence.md`: the M8 evidence record (the outcome first; the
  packages; the specification's errata; stage 1's lineage; the premises
  and the litmus tests; the qualification matrix; the arms' two runs; H38
  and H41; the departures; the gates at `f1813841`; the lanes and the
  stops; the open items; the claim boundary).
- `mvp-m8-result-review-summary.md`: the M8 result's review and
  acceptance record (exact commit `12b0e71b` over the gates' commit
  `f1813841`; accepted 2026-11-04, `accept 12b0e71b`; the outcome
  inconclusive, the claim unchanged).
- `mvp-m9-plan.md`: the bounded plan of milestone M9, measurement (the
  log page and registers, the records R1 to R4, the reference manifests,
  the checker's replay and export, the platform probe, the crosswalk,
  the claim words; D-1 to D-12, M9-1 to M9-6, Q1 to Q19). Accepted
  2026-11-03 at `4f4a8f76`, its second candidate; the first, `86f1c68b`
  (2026-11-02), is superseded.
- `mvp-m9-plan-review-summary.md`: its review and acceptance record.
- `mvp-m9-plan-review-gpt-6-astra.md`: the independent steering review
  of the first candidate the human directed, unedited, with a
  provenance note; steering input, not a decision.
- `mvp-m9-platform-probe.md`: the form the responsible human fills after
  one read-only probe of the COM260's lifecycle and debug state (M9-2;
  the M9 plan's D-6, Q9, Q14): the record's fields, what the probe may
  and may not do, the four outcome classes and the "not performed" state
  with what each establishes, the claim's words for each, and the
  boot-authentication disposition for MVP 1.0. Not performed as of
  2026-11-03.
- `mvp-m9-crosswalk.md`: M9's analysis deliverable (the M9 plan's D-7,
  Q39: analysed, not implemented; M9-5): the Beryllium log against systemd
  v259's `systemd-pcrlock`, `systemd-measure`, `systemd-pcrphase`, and
  UKIs on five dimensions; what the reference manifest already supplies;
  the requirements crosswalk among a minimal vTPM, a measurement-register
  SBI extension, and a lossless offline adapter; what attestation with a
  simulated root needs from the log; how a guest's IMA stays outside
  Beryllium's evidence; milestone 7's items placed and its gate
  discharged for 1.0 (roots documented as absent, the replay and update
  rules stated, the vendor assumptions dated); one Amutable lesson with
  its reason. Selects nothing; no systemd compatibility is claimed.
- `mvp-m9-evidence.md`: the M9 evidence record (the packages and their
  exact commits, the claim's sentences with the slots filled, the log as
  built against D-1 to D-12, the departures, the seven gates at
  `dc07f7d3`, the costs, the soft limits and the stops, the open items,
  the claim boundary).
- `mvp-m9-result-review-summary.md`: the M9 result's review and
  acceptance record (exact commit `892b68c8` over the gates' commit
  `dc07f7d3`; accepted 2026-11-03, `accept 892b68c8`).
- `mvp-m10-plan.md`: the bounded plan of milestone M10, release
  candidate 4 (the eight gates, the re-proof at `X4`, the 26-run board
  campaign with the sessions and the log, the release surfaces, the
  licence manifest, items 115, 118, 121, 122; D-1 to D-7, M10-1 to
  M10-7, Q1 to Q15). Accepted 2026-11-04 at `600b78c5` (`accept
  600b78c5`; Q1 to Q15 at their defaults).
- `mvp-m10-plan-review-summary.md`: its review and acceptance record.
- `mvp-m10-evidence.md`: the M10 evidence record (the exact line, the
  re-proof, tools and release surfaces, X4's eight gates and records, the
  board campaign, soft limits/stops/departures, and claim boundary).
- `mvp-m10-result-review-summary.md`: the M10 result's review and
  acceptance record (RC4 `d70a8535` over X4 `a6eaa885`; accepted
  2026-11-05, `accept d70a8535`).
- `security-model-v1-revision-2-review-summary.md`: the decision packet
  for security model v1's Revision 2, the console path (M7-5's Part 1
  revision, appended to the accepted text; I17, I18, the operator and
  the typing tool as trusted inputs, three TCB rows); the review and
  acceptance record (accepted 2026-11-01 at `afd395b8`, instruction
  `accept afd395b8`).
- `security-model-v1-revision-3-review-summary.md`: the decision packet
  for security model v1's Revision 3, the measurement log (M9-2's Part 1
  revision, appended to the accepted text; the `measurement` asset
  instantiated; I19, I20; the reference manifest, the loader
  observation, and the platform observation as trusted inputs that are
  never one chain; the running TCB told from the offline evidence TCB);
  the review and acceptance record (accepted 2026-11-03 at `4bc079db`,
  instruction `accept 4bc079db`).
- `glossary.md`: comprehensive maintained definitions and disambiguations for
  project identities, milestone codes, status vocabulary, RISC-V/K3 terms,
  assurance language, Linux/upstream terms, commands, and artifact locations.
- `roadmap.md`: one-page current-position placemat: milestone status, the
  planned sequence, dropped workstreams, gates, risks, and later phases.
- `HANDOFF.md`: concise session handoff, current decisions, ready tasks, and restart sequence.
- `pathfinder-comparison.md`: cross-variant evidence matrix, broad
  security-monitor comparison, and selected isolation-engine/authority
  direction.
- `architecture-model-0.1.md`: selected first post-pathfinder deliverable, a
  static single-hart architecture contract with bounded model, proof, checker,
  and claim gates.
- `architecture-model-0.1-evidence.md`: Model 0.1 implementation, evaluator
  workflow, component tour, manifest rejection coverage, proof boundary,
  claim/assumption trace, and future C/assembly cut-point contracts.
- `architecture-model-0.2.md`: accepted non-runtime phase separating
  policy-neutral configuration proposals, canonical sealed HS state, and
  derived enforcement without selecting a service or policy model.
- `architecture-model-0.2-evidence.md`: Model 0.2 implementation, evaluator
  workflow, inventory/proposal/canonical/derived tour, rejection coverage,
  neutral fixture equality, bounded proof matrix, claim limits, and future
  cut-point contracts.
- `single-hart-runtime-plan.md`: accepted fixed QEMU/OpenSBI/HS/VS profile,
  cut-point contracts, evidence requirements, non-goals, authorized R0-R7
  work packages, and the R0 freeze gate before privileged code.
- `single-hart-runtime-r0-freeze.md`: authoritative R0 fixed-profile-and-layout
  freeze; tool/firmware lock, QEMU command, physical/linker map, inventory and
  proposal constants, register matrix, SBI allowlist, fixture/evidence plan,
  and claim/cut-point ledger. No privileged code.
- `single-hart-runtime-r1-evidence.md`: local R1 pure-C mechanism tour,
  thirteen-resource/six-authority/two-root derivation, phase and failure
  contract, adversarial coverage, deterministic report/evidence, command
  surface, claim ledger, and explicit R2 boundary.
- `single-hart-runtime-r1-review-summary.md`: exact-commit responsible-human
  review and acceptance record for R1, including deliverables, claim
  boundaries, invariants, resolved findings, validation, review sequence, and
  the explicit decision for
  `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb`.
- `single-hart-runtime-r2-plan.md`: accepted R2 bounded plan for the
  non-privileged host-tested Sv39x4 backend; fixed page-table storage, root
  builder, independent leaf walker/recheck, HGATP encoding, test matrix,
  claim ledger, and explicit R3 boundary. Accepted on 2026-07-28;
  implementation separately authorized.
- `single-hart-runtime-r2-plan-review-summary.md`: evidence-bound
  responsible-human review and acceptance record for the R2 plan commit;
  deliverables, claim boundaries, resolved findings, validation, review
  sequence, and recorded decisions (plan acceptance + implementation
  authorization).
- `single-hart-runtime-r2-evidence.md`: R2 Sv39x4 backend implementation
  and evidence record; component/API tour, exact fixed profile, pool/root/leaf
  layout, HGATP computation, R1 preservation, failure/scrub/terminal contract,
  test coverage, deterministic report, defects found and fixed, command surface,
  claim ledger, and explicit R3 boundary. Accepted 2026-07-28.
- `single-hart-runtime-r2-review-summary.md`: exact-commit responsible-human
  review and acceptance record for R2 implementation at
  `6e1cb579257c5dbe3234bd484fd091629e87181b`, including deliverables, claim
  boundaries, security invariants, resolved findings, validation, review
  sequence, and the recorded acceptance decision.
- `single-hart-runtime-r3-evidence.md`: authorized, complete R3
  boot-and-first-entry implementation and evidence; executable linker map,
  handoff/SBI/R1/R2/HS validation, exact management binding and
  HGATP/fence/readback plus an exact `SPP=1 -> SRET` sequence that precedes
  bounded QEMU `V=1` evidence, exact artifact/report integrity checks, claims/non-claims,
  resolved findings, self-reference-safe base/HEAD/source-state identity, and
  explicit R4 boundary. Exact implementation target
  `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` is accepted on 2026-07-29;
  generation HEAD and packet follow-up remain separate identities.
- `single-hart-runtime-r3-review-summary.md`: evidence-bound
  responsible-human review and acceptance record for exact immutable R3 target
  `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`; exact inventory,
  claim/trust/non-claim boundary, invariants, all resolved findings plus the
  open VitePress finding, exact-target validation, review sequence, historical
  checklist, and the explicit 2026-07-29 acceptance decision.
- `single-hart-runtime-r4-evidence.md`: accepted R4 trap-and-context evidence;
  exact frame/state/CSR treatment, GCC/Clang host and QEMU evidence,
  deterministic/integrity controls, non-claims, and explicit R5 boundary.
  The accepted target, implementation parent, and decision-support follow-up
  remain separately identified. Publication remains blocked.
- `single-hart-runtime-r4-review-summary.md`: review packet for
  exact R4 target `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` and parent
  `6e5c55c59e94bbaba136269c784db28ec1b53f54`; it records validation,
  boundaries, findings, decision history, and the responsible-human
  acceptance of that exact target. The current acceptance-record follow-up
  HEAD is `87b136bc4889a04a58c2399e4eb81f7925cba5e0`, not implementation.
- `single-hart-runtime-r5-plan.md`: accepted bounded R5 checked-switch plan.
  It freezes one management→protected→management scenario, two target-root
  write/fence/readback transitions, exact fixture slots, pending/publication
  rules, planned evidence, and explicit R6/R7 separation. Accepted
  2026-07-30; implementation separately authorized. See
  `single-hart-runtime-r5-evidence.md` and
  `single-hart-runtime-r5-review-summary.md` for the resulting exact
  accepted implementation target.
- `single-hart-runtime-r5-plan-review-summary.md`: evidence-bound
  responsible-human review and acceptance record for the R5 plan commit;
  deliverables, claim boundaries, resolved findings, validation, review
  sequence, and recorded decisions (plan acceptance + implementation
  authorization). It keeps R6/R7 and
  publication gated.
- `single-hart-runtime-r5-evidence.md`: R5 checked-switch evidence for the
  exact accepted implementation target. Exact bounded switch behavior,
  host/image/QEMU evidence terms, reproducible commands, and
  claims/exclusions. Implementation passes `./be r5-check`/
  `./be r5-evidence`/`make check` from the exact target, an independent
  core/runtime review found no significant issue, and the responsible human
  accepted that exact commit on 2026-07-30. It does not itself accept R5,
  authorize R6, or claim hardware/formal-verification results.
- `single-hart-runtime-r5-review-summary.md`: evidence-bound
  responsible-human review and acceptance record for exact R5 implementation
  target `165f4d001a2b59b582b397bdea79ec4826168fdb` (parent
  `9312c1355a23d411e3bdafb2183be342683a8ab9`): decision summary,
  deliverables, claim boundary, load-bearing invariants, resolved findings,
  exact-target validation, review sequence, and the recorded 2026-07-30
  acceptance. Only the acceptance box is checked, no signature is generated,
  and it keeps R6+, push, tag, publication, and release gated.
- `single-hart-runtime-r6-plan.md`: bounded R6 adversarial-images plan
  accepted at exact target
  `609867fdad75279c0913022909efd65c4a838909`. It fixes a 47-entry single-defect
  fixture catalogue partitioned into static-rejection and dynamic
  fail-closed fixtures over the byte-immutable accepted R5 target, adds no
  production surface under `include/`, `virt/`, or `arch/`, and defines
  detection layers, outcome taxonomy, report schema, and claim boundaries.
  It authorizes one tightly bounded refresh of six predecessor
  acceptance-pin constants in `tests/r1/`, `tests/r3/`, and `tests/r4/`, the
  same refresh the accepted R5 implementation performed, so that the required
  root `Makefile`, `be`, and `scripts/check-be.sh` integration does not
  regress R1-R5 acceptance status; no accepted mechanism byte changes.
  It was **accepted** on 2026-07-30, and the separately recorded
  `proceed to implement R6 exact` and `proceed with all r6 implementation
  work` instructions authorize R6 implementation work under the master-plan
  R6 row. The plan additionally carries **Plan revision R6-A**, a
  narrow correction of fixture D-15's injection site, whose
  base moves from `arch/riscv/be/r5-runtime.c` to `arch/riscv/be/r5-trap.S`;
  the corrected plan target is exact commit
  `75269f058ae578b0a76a113d6c05c0aaceeac8ec`, **accepted on 2026-07-30**.
  Local implementation is unreviewed, unaccepted, and incomplete, and D-15
  may resume under the already-recorded implementation authorization. It
  further carries **Plan revision R6-B**, which withdraws a false D-15
  `.monitor.text` layout claim, pins D-15's exact L8 delta, and makes raw QEMU
  traces ephemeral scratch extracted into canonical semantics, digests, byte
  counts, and bounded excerpts inside the unchanged 512 MiB evidence gate;
  revision R6-B is **accepted at exact target
  `6d6464c6c937abccd59df932006c1049fd79fac6`** as of 2026-07-30, under which
  R6 integration and evidence work may resume with every pinned value
  re-derived at the exact implementation commit. R7 and
  publication remain blocked.
- `single-hart-runtime-r6-plan-review-summary.md`: review and acceptance
  record for exact plan target `609867fdad75279c0913022909efd65c4a838909`
  (parent `0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d`), retaining the original
  decision-support material. It records the 2026-07-30 plan acceptance and
  the separate implementation authorization, checks only those two decision
  boxes, generates no signature, and additionally records the post-acceptance
  D-15 discovery and the accepted corrected plan target: local R6
  implementation is unreviewed, unaccepted, and incomplete, with R7 and
  publication gated.
- `single-hart-runtime-r6-plan-revision-review-summary.md`: review and
  acceptance record for exact **corrected** plan target
  `75269f058ae578b0a76a113d6c05c0aaceeac8ec` (parent
  `4bff41764cf8ec9275e771cd3c1ce124961da93a`), which carries Plan revision
  R6-A. It records the 2026-07-30 acceptance of that exact commit, checks only
  that one supplied decision box, generates no signature, keeps the original
  plan acceptance record historical and byte unchanged, and records that no
  retained corrected-placement
  build or QEMU result exists: the corrected expected-result table is
  `NOT RUN / unverified as retained R6 evidence`. D-15 may resume under the
  already-recorded implementation authorization, local implementation stays
  unreviewed, unaccepted, and incomplete, and R7,
  hardware validation, formal verification, push, tag, publication, and
  release stay blocked. It also carries a navigation-only note that successor
  **Plan revision R6-B** was accepted at its own exact commit
  `6d6464c6c937abccd59df932006c1049fd79fac6` on 2026-07-30; that note records
  no decision and leaves the recorded acceptances exact and byte unchanged.
- `single-hart-runtime-r6-plan-r6b-review-summary.md`: review and acceptance
  record for exact **Plan revision R6-B** target
  `6d6464c6c937abccd59df932006c1049fd79fac6` (parent
  `4d6c3c9b0899c7a30b2150ff0d4067369ccef774`), which withdraws the false D-15
  `.monitor.text` growth claim, pins the L8 delta to exactly 2 differing runs
  and 10 differing bytes per toolchain over unchanged allocated sections and
  checker-fixed/required allocated symbols, explicitly excludes non-allocated
  debug/symbol-table changes, and makes raw QEMU traces ephemeral scratch
  extracted into canonical semantics, digests, byte counts, and bounded
  excerpts inside the unchanged hard 512 MiB gate. It records the 2026-07-30
  acceptance of that exact commit, checks only that one supplied decision box,
  generates no signature, and keeps the original and R6-A acceptance records
  exact and byte unchanged: its pinned values remain local unreviewed
  implementation discovery requiring re-derivation at the exact implementation
  commit, R6 integration and evidence work may resume under the
  already-recorded implementation authorization, local R6 implementation stays
  unreviewed, unaccepted, and incomplete, and R7, hardware validation, formal
  verification, push, tag, publication, and release stay blocked.
- `single-hart-runtime-r6-evidence.md`: authoritative R6 adversarial-image
  implementation and pre-decision evidence record for the accepted exact target: status and evidence boundary, the accepted plan chain
  (`609867f...`, R6-A `75269f0...`, R6-B `6d6464c6...`), the six authorized
  predecessor acceptance-pin refreshes and their target-to-current formula,
  the test-only no-production-surface decision, the 47-entry catalogue with
  its 14/17/15/1 partitions and 11 detection layers, static/host/dynamic
  results including D-06 and the pinned D-15 delta, framework/tool-lock/
  scratch/kernel-lock/authority guards, report and evidence schema, digests
  and counts, exact reproducible commands, findings and resolutions, claims,
  non-claims, and reproducibility boundaries. It is an evidence record only;
  the linked review record carries the 2026-08-05 acceptance. Hardware and
  formal results `NOT RUN`; R7 is authorized only at the planning boundary,
  and public push, tag, publication, and release remain blocked.
- `single-hart-runtime-r6-review-summary.md`: review and acceptance record for
  the exact R6 target
  `7ba3649f03cf13b65df33020e345d361cce2993a` (parent and initial
  implementation `9ed5ad7069b6067f03e1923c09937fe218240a59`, whole-R6 base
  `4012d794e769fd4029b11f6f45e366ed0ef117f5`): decision summary, deliverables
  and exact inventory, claim boundary, load-bearing invariants, review history
  and resolved findings, exact-target standalone and full validation with
  per-scenario report and manifest digests, recommended review sequence, an
  preserved technical checklist, and the 2026-08-05 responsible-human
  acceptance decision.
- `single-hart-runtime-r7-plan.md`: bounded R7 proof-and-evidence plan started
  under the 2026-08-05 responsible-human instruction to commence R7 after the
  private R6 acceptance-record push. It pins the accepted R5/R6 inputs,
  enumerates the exact linked symbols and bounded RV64/Rocq obligations,
  separates proved bytes from C/configuration cut points, and defines the
  claim ledger, evaluator, report, reproducibility bundle, non-goals, and
  acceptance gates. The plan is accepted at exact target
  `18c43596d308052cfad67edc6e2cb8f543f75600`. Plan revision R7-A,
  appended to the same file and **separately accepted** at exact target
  `0605028220e3795d99393156d0bfb7d6a7d631a4`, enumerates exactly six
  authorized predecessor acceptance-pin refreshes with their exact formulas,
  re-derivation rule, ordering, and validation gates. Implementation is local
  and unaccepted, all six pins are re-derived and applied, and root integration
  stays within that enumeration.
- `single-hart-runtime-r7-plan-review-summary.md`: review and acceptance
  record for exact R7 plan target
  `18c43596d308052cfad67edc6e2cb8f543f75600` over parent
  `2cc6e96413ab4d426bbf2327dc6c9b309b3f3aac`. It records the 2026-08-05
  responsible-human decision, preserves the implementation/proof `NOT RUN`
  boundary, and keeps R8 and publication blocked.
- `single-hart-runtime-r7-plan-r7a-review-summary.md`: review and acceptance
  record for exact Plan revision R7-A target
  `0605028220e3795d99393156d0bfb7d6a7d631a4` over parent
  `014b0f654ed65758bb99112f401529975d2dfd44`. It preserves the technical
  review history — the defect statement, the six-constant enumeration, the
  exact binding formulas, the re-derivation rule, the ordering, the validation
  gate, and the non-evidence boundary around the blocked diagnostic — and
  records the 2026-08-05 responsible-human acceptance. Packet commit
  `402afc824fde0458bf1dce0c3e291cadc2319fba` and the acceptance-record
  follow-up are decision support, neither plan nor implementation; the
  acceptance authorizes resuming root integration under exactly six freshly
  re-derived pins and accepts no R7 implementation, evidence, proof, or
  hardware result.
- `single-hart-runtime-r7-evidence.md`: bounded R7 exact-proof and evidence
  record for the accepted `tests/r7/` package. It records
  both accepted plan identities, the six freshly re-derived acceptance pins
  with their exact formulas and ordering, the two pinned R5 allocated-image
  digests, the
  22 scoped symbols / 1,420 words / 144 targets, the 9 Rocq modules and 135
  theorems with 4 lemmas, the generated fixed-configuration facts, the nine
  evidence classes,
  fifteen cut points, ten trusted boundaries, one plan-obligation
  substitution, fourteen non-claims,
  and the 31-file reproducibility bundle. It is an implementation and
  pre-decision evidence record, not a decision record: the proof is
  bounded and is not whole-system formal verification, hardware is `NOT RUN`,
  its retained `r7_acceptance=not-reviewed` fields are the exact-target
  pre-decision measurement, and R8, push, tag, publication, and release
  remain blocked.
- `single-hart-runtime-r7-review-summary.md`: review and acceptance record for
  exact R7 target
  `9bf22913d67e9b72286813cd5f7993a9ad3857a8` (immediate parent and superseded
  first candidate `95639afb0ab57959a32d055f7b7f9bdb474fe762`, whole-R7 base
  `3ee8a20a3ab7e3673b88a502476f39559909a12e`). It maps the 20 maintained
  `tests/r7/` paths, the claim boundary and its explicit substitution, the
  load-bearing invariants, the resolved findings, the exact-target validation,
  the preserved technical checklist, and the 2026-08-05 responsible-human
  acceptance. It carries the decision for that exact commit only; packet
  commit `a4cc49d3d41e4bc22a7b17def836e6c4746f3c82` and the acceptance-record
  follow-up are decision support, not implementation, and R8, push, tag,
  publication, and release stay blocked.
- `single-hart-runtime-r8-plan.md`: combined K3 core-validation plan accepted
  at exact target `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` on
  2026-08-07. It defines an ordered H0-H4
  single-hart sequence: exact non-privileged board/firmware/profile freeze,
  read-only platform characterization, additive execution of the fixed
  two-domain synthetic scenario, canonical QEMU/K3 comparison, and
  exact-target evidence/review. Accepted Plan revision R8-A narrowly adds the
  exact H0 documentation-support paths and pre-/post-commit candidate identity
  semantics at exact target
  `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`. A separate instruction
  authorizes only the non-privileged H0 freeze; R8-A acceptance unpauses that
  work only after its acceptance-record commit. Plan revision R8-C is accepted
  at exact target
  `f47ae60266a467ca1a7704fd9a50b140e0f31bb0` and defines only the
  content-based retired-parent scan correction, exact three-path
  implementation boundary, regression obligations, and successor identity
  gate. Exact bounded non-privileged H0/R8-C target
  `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` is accepted as of 2026-09-17,
  remains blocked and not exit-ready, and does not authorize H1-H4. Hardware
  remains `NOT RUN`.
- `single-hart-runtime-r8-h0-freeze.md`: historical active-line H0 freeze
  source introduced at `102f2b0569396bf33ed2177ea5b7558cf5e6fbaa`. It
  records 147 profile rows and 81 H0 blockers for that unaccepted package.
  Its count is not the accepted-target count and its hash-bound bytes remain
  unchanged.
- `single-hart-runtime-r8-plan-review-summary.md`: review and acceptance
  record for exact R8 plan target
  `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` over parent
  `742ce4450dc85fc632d2ca7ff1061de09f3cf171`. It records the exact inventory,
  planning claim boundary, load-bearing plan invariants, resolved findings,
  validation boundary, open generated-asset finding, recommended review
  sequence, preserved technical checklist, and the supplied 2026-08-07
  responsible-human acceptance decision plus the later separate
  authorization to proceed only with non-privileged H0.
- `single-hart-runtime-r8-plan-r8a-review-summary.md`: review and acceptance
  record for exact R8-A target
  `8fa9d672cfcfb81ab68d9ed9553a5af48b884932` over parent
  `cb0ac2a0f818ac57f2866cb7815767145608cf58`. It preserves the exact support
  boundary, candidate-identity protocol, claim boundary, validation record,
  unchecked technical-review questions, and the supplied 2026-08-07
  responsible-human acceptance decision. Packet commit
  `9ad001bdbcb41aa7c86b406b80f62a6c9820e08c` and the acceptance-record
  follow-up are decision support, not plan text or H0 implementation.
- `single-hart-runtime-r8-plan-r8c-review-summary.md`: review and acceptance
  record for exact R8-C target
  `f47ae60266a467ca1a7704fd9a50b140e0f31bb0` over parent
  `fc6795b03b5f68849fe5ef882d7e2cae77ab4e90`. It preserves the exact binary
  diagnostic, content-based scan semantics, three-path future implementation
  inventory, generated regression obligations, unchanged H0/predecessor
  boundary, validation record, unchecked technical-review questions, and the
  supplied 2026-09-17 responsible-human acceptance decision. Packet commit
  `0b8fdad1b4052791baae0327c52a37d9ec3a76e1` and the acceptance-record
  follow-up are decision support, not plan text or implementation.
- `single-hart-runtime-r8-h0-review-summary.md`: review and acceptance record
  for exact bounded non-privileged H0/R8-C target
  `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4`, parent
  `d18b1c9c6ca8a0f2285f820ec960258620ae4b50`, tree
  `7a9d80d08d0abb771d43cf76a4a297d9d668b375`. It preserves the exact
  inventory, 147-row/118-`UNKNOWN`/80-blocker blocked readiness boundary,
  reported pre-decision exact-target gates, trusted-tool and generated-asset
  residuals, the 2026-09-17 acceptance decision, and the 2026-09-24
  current-line confirmation. H1-H4 and K3 remain unauthorized or `NOT RUN`.
- `single-hart-runtime-r8-active-line-maintenance-plan.md`: immutable
  `R8-ALM1` planning-only target carrying Plan revision `R8-ALM1-A`, accepted
  as plan text only at exact commit
  `95cce2f692543da67054ec2d6061eb08a4061253` on 2026-09-29. Its target bytes
  retain `proposed-not-reviewed` and `not-authorized` as frozen pre-decision
  content. The revision replaces the incoherent plan-target
  direct-child rule with a future exact acceptance-record/current-line base
  named by separate implementation authorization and separates current
  launcher-authentication exit `126` from historical whole-diff exit `2`.
  The plan retains the finite ten-path R8/four-path current-position closure,
  bounded `safeRemove`-before-overlay semantics, zero predecessor pin
  refreshes, and explicit evidence/readiness/hardware/runtime/publication
  non-claims. It is not R8-B, not an H0 successor, and not implementation
  authority.
- `single-hart-runtime-r8-active-line-maintenance-plan-review-summary.md`:
  decision-neutral review packet for exact R8-ALM1 target
  `6bb3349b266a43d4572465379b5892b058e2fe39`, parent
  `2b404ca31a07e1a0783a44183d0b2de95d053618`, tree
  `730a77942be1079b1d1bb4e13ec1166cd30d4861`. It records the exact
  seven-source/104-generated target boundary, independent documentation and
  source checks, and two revision-required findings. It recommends requesting
  revisions and records no acceptance or implementation authority. Exact
  packet commit `255aa176923581bf9248bfce5bc94217ff5577a8` is immutable
  decision support for the original target; it is not the R8-ALM1-A target or
  a future implementation base.
- `single-hart-runtime-r8-active-line-maintenance-plan-r8alm1a-review-summary.md`:
  current review and acceptance record for exact R8-ALM1-A target
  `95cce2f692543da67054ec2d6061eb08a4061253`, parent
  `255aa176923581bf9248bfce5bc94217ff5577a8`, tree
  `f826204b12701114993743f949c6ee71a72def5c`. It confirms that the revised
  acceptance-record/current-line base model and independent exit-126/exit-2
  controls resolve both first-packet findings, records no significant open
  plan defect, and records the responsible-human 2026-09-29 instruction
  `accept`. Exact packet commit
  `788b0b6752b706ece8dc51dc2c0c5dca3e56376f` and the acceptance-record
  follow-up are decision support. Acceptance covers plan text only and grants
  no implementation authority.
- `k3-kvm0-plan.md`: immutable K3 CoM260 Linux/KVM qualification plan carrying
  **Plan revision K0-A**, accepted at exact target
  `5227266ceddb664a1595e22e5a92da57a013652f` on 2026-09-25. It preserves the
  first proposal as superseded and unaccepted, fixes cycle-free report/bundle
  hashing, separates KVM0-B implementation from KVM0-G documentation/review
  paths, exposes K0-P/K0-I/K0-S/K0-X/K0-R separately, transcribes the supplied
  live discovery and missing hashes without promoting them to evidence, and
  reconciles provenance with privacy through opaque identifiers plus a
  restricted mapping. The fixed run remains three attended sessions, one
  16-command KVM selftest set per session, and two eight-case guest matrices
  per session (48 guest cases total). Its proposed/pending fields are frozen
  pre-decision history; K0-P is satisfied by that exact plan decision. The
  later accepted K0-I implementation and separate K0-S preparation
  authorization are recorded below. K0-S readiness is blocked; K0-X and K0-R
  remain unauthorized or blocked.
- `k3-kvm0-k0s-completion-plan.md`: K0-S completion plan accepted as planning
  text only at exact target
  `33f35981483bccbc4e3a1c87f4a5af52e0e15d41`. It defines separately
  authorized K0-SC1 custody/selection, K0-SC2
  offline replacement inputs, and K0-SC3 read-only board characterization.
  It changes no accepted K0-A/K0-I/K0-S boundary and authorizes no
  implementation, board access, import, readiness, K0-X, push, or publication.
- `k3-kvm0-k0s-completion-plan-review-summary.md`: review and acceptance
  record for exact plan target
  `33f35981483bccbc4e3a1c87f4a5af52e0e15d41`. Packet
  `25e0f39f510c2b6da2dc0bb644939eaff0631fc5` remains decision support.
  K0SC-R1/R2/R3 remain unresolved and unwaived; K0-SC1/2/3 remain
  unauthorized.
- `k3-kvm0-k0sc1-plan.md`: package-specific custody and human-selection plan
  accepted as planning text only at exact target
  `9b9923f8a58fe7102a108cb2a976ea09979427a1`. It defines six disposition
  classes, finite K0-SC1 formulas, ordinary/restricted separation, and exact
  later authorization requirements. It authorizes no copying, selection,
  network query, board access, readiness, successor, push, publication, or
  release.
- `k3-kvm0-k0sc1-plan-review-summary.md`: review and acceptance record for
  exact K0-SC1 target `9b9923f8a58fe7102a108cb2a976ea09979427a1`.
  Packet `695ab65770303ee09ebe863f179bdffea73b9c64` remains decision support.
  One high and two medium-high findings plus K0SC-R1/R2/R3 remain unresolved
  and unwaived; K0-SC1 implementation remains unauthorized.
- The same `k3-kvm0-k0sc1-plan.md` now carries proposed Plan revision
  K0-SC1-A over base `0c8a625df9d49254332b2105ae4b3c9cbe60a982`.
  K0-SC1-A proposes exact F1/F2/F3 corrections but is not reviewed or
  accepted; the original target and acceptance record remain immutable
  accepted history.
- `k3-kvm0-k0sc1-plan-k0sc1a-review-summary.md`: decision-neutral review
  and acceptance record for exact K0-SC1-A target
  `c00f4d000c845a7c3d62921c1d7939fc158744e2`. Packet
  `8a24fa4a33d5e0c94583e85d478c51a4cea624af` remains decision support.
  Acceptance covers planning corrections only and authorizes no
  implementation.
- The same `k3-kvm0-k0sc1-plan.md` now carries proposed Plan revision
  K0-SC1-B over base `06cda3814426de940afadb05cd5cf59ee8253688`.
  K0-SC1-B proposes a collision-safe host custody pathname formula while
  preserving accepted K0-SC1-A as immutable history. Exact proposed target
  `1ce71e73078a65a271949d84db47343e4eaacf14` is unaccepted after the
  responsible human requested revisions for K0SC1B-F1 through K0SC1B-F4.
  The maintained plan now also carries a proposed corrected K0-SC1-B
  revision from exact base
  `e1cd15a72e84304812a7c893d5b3a8c4990ea628`; exact target
  `13463e4f8473e4a5497ef60f92f284ea4f9944f5` is proposed and
  unaccepted.
- `k3-kvm0-k0sc1-plan-k0sc1b-corrected-review-summary.md`:
  decision-neutral packet for exact corrected target
  `13463e4f8473e4a5497ef60f92f284ea4f9944f5`. It records exact-target
  validation, four high and three medium open findings, review sequence,
  unchecked checklist, and the accept/revise/defer boundary without
  authorizing implementation.
- `k3-kvm0-k0sc1-plan-k0sc1b-review-summary.md`: decision-neutral review
  packet and revisions-requested decision record for exact K0-SC1-B target
  `1ce71e73078a65a271949d84db47343e4eaacf14`. It records exact-target
  validation, one high and three medium findings, review sequence, unchecked
  checklist, the October 5, 2026 decision, and unchanged non-authorizations.
- `k3-kvm0-plan-review-summary.md`: historical decision-neutral review packet
  for the superseded, unaccepted first KVM0 plan target
  `459184dd8fe9c5da20e27a9e277a076685a520cb` over parent
  `80345e18df94eb9e58b1b7861b3f12856832b1b2`. It records the exact
  planning/generated inventory, source-evidence caveat, claim/non-claim and
  safety boundaries, exact-target documentation validation, review order,
  unchecked human checklist, and the three permitted plan decisions. It
  records no acceptance and grants no authority. K0-A requires a fresh
  revision-specific packet.
- `k3-kvm0-plan-k0a-review-summary.md`: review and acceptance record for exact
  K0-A plan target
  `5227266ceddb664a1595e22e5a92da57a013652f` over parent
  `8348b18a2c00c992e8fbf744f2004dfcd55500e6`, tree
  `2a716a0ca69a7d0ada92b978bd77704fbfc8910b`. It records the exact inventory,
  all five independent-review findings and resolutions, exact-target
  documentation validation, generated-byte limit, claim/non-claim boundary,
  review order, retained unchecked technical-review checklist, and the
  responsible-human 2026-09-25 acceptance instruction. Packet commit
  `6369804904eb28554c65886db93f0d30be80fcab` and the acceptance-record
  follow-up are decision support, not plan text or implementation. Acceptance
  satisfies K0-P only and grants no later authority.
- `k3-kvm0-k0i-review-summary.md`: authoritative review and acceptance record
  for exact K0-I destination offline-tooling target
  `abd092a1f2734c720a205803c29496fe2245b0ef`, parent
  `d490183d0177a5ba38276c572685f0c2e4ee3863`, tree
  `f683c1b634e8cd07ba967960d9e00ef2c6a76efa`, authorized base
  `e4e0209f19596e0cbccbb6bb4de84c50bbd11f92`, and accepted K0-A plan
  `5227266ceddb664a1595e22e5a92da57a013652f`. It records the exact cumulative
  ten-path/mode scope, final seven-path correction, target validation, two
  open low-severity observations, and the responsible-human 2026-09-26
  acceptance instruction. K0-I acceptance grants no later KVM0, K3,
  successor, integration, or publication authority by itself.
- `k3-kvm0-k0s-authorization-record.md`: frozen target-time draft,
  not-reviewed record of the
  exact 2026-09-28 K0-S session sequence beginning with
  `Fleet deployed: proceed with K0-S per above`. It records
  `k0s-source-owner-workspace-1`, whose exact private locator is intentionally
  omitted, plus `continue`, the conditional repair instruction, target-time
  local package file/mode/checksum identities, verified 14-commit/11-path
  relation, clean candidate worktree, complete 43-of-43 restricted mapping
  coverage, controller self-hash preflight, static/profile checks, and 25
  host-only fake tests. It limits current work to source-owner preparation,
  read-only audit, profile drafting, and bounded repair under accepted K0-A target
  `5227266ceddb664a1595e22e5a92da57a013652f` and accepted K0-I target
  `abd092a1f2734c720a205803c29496fe2245b0ef`, while preserving K0-I as a
  separate destination-tooling boundary. Those draft fields, hashes, and
  source-containment observations remain frozen target-time evidence inside
  accepted target `c65705582c243dd908ff47d3189df07601167400`; its private
  locator is not evidence.
  proposed commit
  `c1c7e254143f99d4ad3cdbf25021a76364d6d75a` / tree
  `a5f77b5acef26d8975fe756512edbd2413fa1239` remains unaccepted
  evidence input. The draft's no-documentation-target field remains
  historical target content and grants no
  destination import, K0-S readiness/acceptance claim, real selftest/K0-X,
  serial, K0-R/K0-G, hardware, BSP, integration, successor, or publication
  authority.
- `k3-kvm0-k0s-review-summary.md`: authoritative review and acceptance record
  for exact preparation/status target
  `c65705582c243dd908ff47d3189df07601167400`, parent
  `478d5886e8dc261546e3373421e0ab428062f82a`, tree
  `a3f1f74c42d2c583aae8c6aa486f1f97f5379439`. It records the finite target
  inventory, target-time external-package hashes, claim boundary, resolved
  findings, validation, review sequence, retained unchecked technical
  checklist, and the responsible-human 2026-09-29 acceptance instruction.
  Packet commit `d3499c3a7cd4b339fd5f24b145a651844a72d672` remains decision
  support. Acceptance does not make K0-S ready, accept current package bytes
  or source candidate `c1c7e254143f99d4ad3cdbf25021a76364d6d75a`, or
  authorize K0-X.
- `implementation-plan.md`: requirements, architecture options, milestones, and upstream strategy.
- `research-synthesis.md`: source-backed findings and representative references.
- `isolation-engine-policy-research.md`: post-pathfinder working hypotheses for
  a small multi-hart HS isolation engine, VBS-style secure domains, CAP+TE
  composition, and CHERI/software-capability refinement.
- `capability-policy-architecture.md`: capability graphs as extensional
  authority policy, their relationship to system-wide rule and information-flow
  policy, candidate composition boundaries, and the separate research
  hypothesis of TE over capability possession and lifecycle.
- `supervisory-security-policy.md`: Rego, signed supervisory manifests, code
  integrity, image composition, attestation, confidential-computing policy,
  alternatives, and a bounded possible future Beryllium relationship.
- `beryllium-hypervisor-notes.md`: curated user-provided design input on
  Arm/RISC-V differences, M-mode, SBI versus OpenSBI, firmware decomposition,
  VS-to-HS guest SBI routing, and the future
  monolithic-versus-service-oriented VS control-plane gate.
- `sidebar-high-assurance-standards.md`: certification regimes, assurance
  cases, formal-method precedents, open-tool equivalents, and evidence gaps.
- `sidebar-rust-vs-components.md`: bounded safe-Rust options for future VS
  components, safe privileged-wrapper boundaries, and separate-domain versus
  CHERI mixed-language isolation while the HS isolation TCB remains restricted
  C, with Verus and comparable Rust-verification dispositions.
- `sidebar-lvbs-equivalence.md`: optional Linux VBS-equivalent service
  decomposition, limits, open precedents, dynamic code integrity, protected
  logging, driver domains, and future experiments.
- `sidebar-dynamic-authority-caches.md`: Chompie AVC overwrite provenance,
  cache corruption versus freshness, concrete EL2/VTL/VMPL isolation
  precedents, and CHERI/VS design options.
- `sidebar-minimal-vs-runtimes.md`: LiteBox classification and a bounded
  shortlist for future RISC-V VS runtime evaluation.
- `sidebar-cheri-mvp.md`: RISC-V CHERI (RVY v0.9.10.1) against MVP 1.0's
  mechanisms: what fits today, what CHERI-enabled guests would change, a
  purecap compile-and-test of M8's two leaves on a v0.9.3 stack, and
  questions for CHERITech, from the beryllium-cheri investigation.
- `session-analysis-transcripts-2026-07-20.md`: index of verbatim significant
  session outputs retained as research provenance, with separate full-text
  pages for TE/VBS assessment, HS isolation, and CAP+TE/CHERI composition.
- `cheri-alignment.md`: standing strategic and technical alignment with
  CTSRD-CHERI, RISC-V CHERI, David Chisnall's public design guidance, and
  generic CHERI component isolation inside a future VS.
- `open-tooling.md`: mandatory open-source tooling policy, high-assurance evidence strategy, and candidate baseline.
- `pathfinder-plan.md`: Helium, the quick PoC and experimentation phase before MVP 1.0 is defined.
- `pathfinder-evidence.md`: Helium executable results, assumptions, formal/tooling findings, policy comparison, and K3 disposition.
- `arm64-pathfinder-plan.md`: bounded implementation handoff for an Arm64
  backend with RISC-V parity preserved.
- `minimal-pathfinder-plan.md`: third, RISC-V-only Helium variant that
  preserves the isolation application while minimizing implementation,
  technology, and review complexity and exposing build-time policy
  experiments.
- `minimal-pathfinder-evidence.md`: executable results, authority-model
  comparison, size/tool-surface measurements, assumptions, and exact claim
  limits for the minimal RISC-V variant.
- `type-enforcement-pathfinder-plan.md`: fifth and final bounded pathfinder
  experiment, with two fixed VS subjects, sealed labels, one shared memory
  object, and a static default-deny TE matrix.
- `type-enforcement-pathfinder-evidence.md`: exact fixed labels, roots, QEMU
  behavior, unit/report coverage, measurements, assumptions, and claim limits.
- `riscv-security-hardware.md`: K3/RISC-V security hardware inventory and staged usage roadmap.
- `research-provenance.md`: confidence, limitations, and artifact-retention notes.

Selected significant session outputs are retained verbatim in this repository.
Other raw research outputs remain in the Copilot session artifact store.
Curated conclusions should be updated here when they are confirmed,
superseded, or rejected.

## Documentation policy

Markdown under `planning/` is the authoritative and routinely maintained
project documentation. Keep status, architecture, evidence boundaries,
navigation, references, and assurance language current as engineering work
changes. This source-first policy supports the present priority: K3 bring-up,
final transfer of relevant learning from Helium, and selection of the overall
Beryllium direction. It prevents generated-site churn and full-browser runs
from displacing early security and technical work without relaxing claim
discipline.

Graphviz DOT under `planning/diagrams/` is authoritative diagram source.
Generated SVG under `planning/public/diagrams/` may be updated when its DOT
source changes or as part of a milestone build; routine prose-only changes do
not require SVG regeneration.

Generated planning and retained-Helium HTML under `docs/html/` and
`pathfinder/docs/html/` is deferred from active-line maintenance. The private
historical snapshot is branch `archive/generated-docs-2026-09-30` at
`d4c5ff0616c78d997367a050db85512c44960acb`. That ref records generated
output as it existed on 2026-09-30; it is not authoritative source,
publication approval, or permission to publish the private repository.
The active line no longer tracks those generated HTML trees. They may be
generated into ignored local output for milestone, release, publication, or
targeted UX validation, but must not be committed as routine active-line
documentation. Never edit generated HTML or SVG by hand.

Routine documentation changes require fast source checks covering whitespace,
Markdown links and navigation, references, configuration or instruction
syntax, and privacy/retired-name policy. Documentation-only wording or status
updates do not require VitePress generation, HTML regeneration, or Chromium.
Run targeted VitePress and browser checks when changing documentation theme,
configuration, renderer behavior, or user experience and the check is needed
to evaluate that change.

The complete generated-site commands remain milestone gates:

```sh
npm ci
./be docs-check
./be docs
./be docs-dev
```

Use the complete docs/browser gates at major milestones, for exact
review/acceptance targets when the governing plan or packet specifically
requires them, for release/publication candidates, and in periodic CI.
Release and publication checks are not weakened. Set `DOCS_BASE` when a
milestone or publication build targets a URL prefix, for example:

```sh
DOCS_BASE=/beryllium/ npm run docs:build
```

## Stable project interface

`./be` is the maintained project-level interface. It encapsulates the current
Model 0.2 build, demonstration, tests, proof, reports, evidence, complete
local gate, pinned evaluator, documentation servers, and retained Helium
entry point:

```sh
./be help
./be status
./be demo
./be model-check
./be r1-check
./be r1-evidence
./be r2-check
./be r3-check
./be r3-evidence
./be evaluate
./be helium help
```

Direct Make, npm, Podman, and `./pathfinder/he` commands remain inspectable
implementation details and targeted developer interfaces.

R3's checked targeted interface is `./tests/r3/run-make.sh TARGET`. Raw
`make -C tests/r3 TARGET` is parse-time guarded when its Makefile loads, but
the checked launcher or `./be` is normative when external Make controls are
not already trusted.

## Selected planning direction

- Use [`roadmap.md`](roadmap.md) as the maintained current-position placemat,
  [`project-orientation.md`](project-orientation.md) to explain project
  structure and re-entry, and [`glossary.md`](glossary.md) for definitions;
  follow their links to authoritative plans, evidence, and review records.
- Use a small RISC-V HS isolation engine with Linux, VMM, policy, I/O, and
  rich services in VS domains.
- Use static ownership and explicit channels as the Model 0.1 baseline.
- Treat Model 0.1 as accepted, with incremental review continuing.
- Treat the implemented policy-neutral Model 0.2 core mechanism boundary as
  accepted on 2026-07-24.
- Treat the bounded single-hart runtime plan as the selected planning phase.
  Responsible-human review accepted it and separately authorized its exact
  fixed implementation profile on 2026-07-25.
- Treat the processed Verus, intra-VS CHERI compartment, and
  TE-over-capability-lifecycle feedback as non-authorizing research outside
  the fixed implementation profile.
- Treat the exact R0 fixed profile and layout as accepted on 2026-07-27. It
  adds no privileged runtime source.
- Treat exact R1 pure-C mechanism commit
  `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` as accepted on 2026-07-28. It
  remains non-privileged pure restricted-C only, with thirteen resources, six
  authorities, and two abstract derived roots with three mappings each; it is
  not an Sv39x4 backend, linked image, or QEMU result. Acceptance did not
  authorize tagging, pushing, public release, or R2.
- Treat exact R2 implementation commit
  `6e1cb579257c5dbe3234bd484fd091629e87181b` as accepted on 2026-07-28.
  It remains non-privileged and does not itself validate R3.
- Treat R3 as separately authorized on 2026-07-29 with implementation content
  complete and responsible-human accepted at exact target
  `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` on that date. Its linked-image
  inspection and six bounded traces establish the exact R3
  `SPP=1 -> SRET` sequence before the management block where QEMU reports
  `V=1`; acceptance does not expand that evidence. Packet follow-up
  `fcc0f267a1f59241f872c0a1d2a371a95a58cba6` is not accepted
  implementation. Exact R4 target `0783dfc6557453fbac0da93a5364f2e6e2cb1f52`
  is accepted. The R5 bounded plan is accepted at exact commit
  `fecae6b62a507bdbb93d211262197a31f5422316` on 2026-07-30, and R5
  implementation is separately authorized under that accepted plan. Exact R5
  implementation target `165f4d001a2b59b582b397bdea79ec4826168fdb`
  over parent `9312c1355a23d411e3bdafb2183be342683a8ab9` is accepted as of
  2026-07-30 (see `single-hart-runtime-r5-evidence.md` and
  `single-hart-runtime-r5-review-summary.md`); the review packet commit and
  acceptance-record follow-up are not implementation. Recorded instructions
  `proceed to implement R6 exact` and `proceed with all r6 implementation
  work` authorize R6 implementation work under the master-plan R6 row, but
  the R6 bounded plan was separately accepted at exact target
  `609867fdad75279c0913022909efd65c4a838909` on 2026-07-30 and again at
  corrected exact target `75269f058ae578b0a76a113d6c05c0aaceeac8ec`, while
  exact R6 implementation target
  `7ba3649f03cf13b65df33020e345d361cce2993a` is accepted as of 2026-08-05.
  R7 is authorized under
  `single-hart-runtime-r7-plan.md`; exact plan target
  `18c43596d308052cfad67edc6e2cb8f543f75600` is accepted and Plan revision
  R7-A is accepted at exact target
  `0605028220e3795d99393156d0bfb7d6a7d631a4`, its bounded package
  is accepted at exact implementation target
  `9bf22913d67e9b72286813cd5f7993a9ad3857a8` as of 2026-08-05 over superseded
  first candidate `95639afb0ab57959a32d055f7b7f9bdb474fe762`, and root
  integration is applied
  within the accepted six-constant enumeration with every pin freshly
  re-derived (see `single-hart-runtime-r7-evidence.md` and
  `single-hart-runtime-r7-review-summary.md`). The R8 plan is accepted at
  exact target `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`;
  Plan revision R8-A is accepted at exact target
  `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`; Plan revision R8-C is accepted
  at exact target `f47ae60266a467ca1a7704fd9a50b140e0f31bb0`; exact bounded
  non-privileged H0/R8-C target
  `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` is accepted as of
  2026-09-17. It remains blocked and not exit-ready with 80 H0 blockers, 118
  `UNKNOWN`, and `r8_h0_exit=not-met`. The 2026-09-24 confirmation reconciles
  current status only. H1-H4 remain unauthorized and K3 remains `NOT RUN`;
  any COM260-informed H0 successor requires a separately reviewed exact
  plan/base/relation and explicit authorization.
- Add software capabilities only when a concrete use case requires
  delegation, attenuation, holder transfer, or revocation.
- Add TE only when a concrete mandatory property cannot be expressed
  acceptably through ownership, channels, and capability rights.
- Keep rich policy interpretation and security-model evaluation outside the
  accepted models until an explicit successor phase authorizes them.

## Delivery stages and required outputs

The following table restates the candidate roadmap in
`implementation-plan.md`. The fixed-profile R0-R7 dependency graph is
complete and accepted, and the K3 bring-up milestones B0-B7 are accepted.
R8 stages H1-H4 and KVM0 were dropped on 2026-10-08; the accepted R8 plan
chain and exact H0/R8-C target `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4`
(`BLOCKED-NOT-READY`, `r8_h0_exit=not-met`) stay accepted history. Listing
any later stage is not authorization.

| Stage | Status | Required delivery | Exit or next gate |
| --- | --- | --- | --- |
| Evidence base | Complete | Curated research, threats, architecture options, assumptions, and assurance crosswalk | Enough evidence to bound pathfinders |
| Helium pathfinders | Complete | Five isolated experiments, reproducible QEMU/proof/test evidence, and cross-variant comparison | Select architecture direction and Model 0.1 |
| Architecture Model 0.1 | Complete and accepted; incremental review continues | Static single-hart contract, canonical semantics, C checker/model, fixtures, reports, tests, bounded Rocq proof, and future cut-point contracts | Refine the core mechanism/policy boundary without selecting policy semantics |
| Architecture Model 0.2 | Complete and accepted 2026-07-24 | Policy-neutral proposed/canonical/derived state split, nine-phase model, checker, adversarial fixtures, exact reports, and 23 bounded proof obligations | Select a bounded successor phase without granting implementation authority |
| Bounded single-hart runtime plan | Complete and accepted 2026-07-25; exact fixed implementation authorized | One-hart QEMU profile, OpenSBI below HS, two role-neutral synthetic VS domains, no guest SBI, cut-point/evidence contracts, and R0-R7 work packages | Execute only the authorized dependency graph |
| R0 fixed profile and layout | Complete and accepted 2026-07-27 | Exact tools, QEMU CPU command, linker map, inventory, proposal, register matrix, SBI allowlist, fixtures, and Model 0.2 trace; no privileged code (see [`single-hart-runtime-r0-freeze.md`](single-hart-runtime-r0-freeze.md)) | Superseded as latest review gate by accepted R1 |
| R1 pure-C mechanism | Complete and accepted 2026-07-28 at `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` | Non-privileged pure restricted-C copy/validate/canonicalize/seal/abstract-derive/report/fail contract; fixed 13-resource full profile including 2 R-X guest-code resources; 6 authorities; 2 abstract derived roots with 3 mappings each; adversarial GCC/Clang tests; deterministic reports; retained evidence (see [`single-hart-runtime-r1-evidence.md`](single-hart-runtime-r1-evidence.md)) | Superseded as latest review gate by accepted R2 plan |
| R2 bounded plan | Complete and accepted 2026-07-28 at `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce`; implementation separately authorized | Non-privileged host-tested Sv39x4 backend plan: fixed page-table storage, root builder, independent leaf walker/recheck, HGATP encoding, test matrix, claim ledger, explicit R3 exclusion (see [`single-hart-runtime-r2-plan.md`](single-hart-runtime-r2-plan.md) and [`single-hart-runtime-r2-plan-review-summary.md`](single-hart-runtime-r2-plan-review-summary.md)) | R2 implementation accepted 2026-07-28; evidence in [`single-hart-runtime-r2-evidence.md`](single-hart-runtime-r2-evidence.md); no tag/push/publication/R3 |
| R2 implementation | Complete and accepted 2026-07-28 at `6e1cb579257c5dbe3234bd484fd091629e87181b` | Concrete non-privileged Sv39x4 builder, independent walker, exact HGATP computation, adversarial tests, deterministic report, and retained evidence | R3 separately authorized 2026-07-29; R2 acceptance itself granted no R3/publication authority |
| R3 boot and first entry | Complete and accepted 2026-07-29 at exact target `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` | Privileged linked GCC/Clang images; exact OpenSBI/image/SBI/R1/R2/HS validation; management HGATP write, local fence, readback, publication, deterministic GPR state, and six traces where the exact R3 `SPP=1 -> SRET` sequence precedes QEMU `V=1`; report identity separates the fixed implementation base, dynamic generation HEAD, source state/hashes, accepted target, and packet follow-up (see [`single-hart-runtime-r3-evidence.md`](single-hart-runtime-r3-evidence.md) and the [acceptance record](single-hart-runtime-r3-review-summary.md)) | R4 target `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` is accepted; the R5 bounded plan is accepted at exact commit `fecae6b62a507bdbb93d211262197a31f5422316`, and R5 implementation is separately authorized. Exact R5 implementation target `165f4d001a2b59b582b397bdea79ec4826168fdb` is accepted 2026-07-30. R6+ remain gated; publication remains blocked. |
| R5 checked switching | Plan accepted 2026-07-30 at exact commit `fecae6b62a507bdbb93d211262197a31f5422316`; implementation separately authorized and accepted 2026-07-30 at exact target `165f4d001a2b59b582b397bdea79ec4826168fdb` | Pending binding, target-root write, local fence/readback, checked restore and publication, re-entry, state separation, and a terminal final event. The exact target passes `./be r5-check`/`./be r5-evidence`/`make check` from fresh detached worktrees (see [`single-hart-runtime-r5-evidence.md`](single-hart-runtime-r5-evidence.md) and the [review and acceptance record](single-hart-runtime-r5-review-summary.md)). | R5 implementation is responsible-human accepted at that exact commit only (`r5_acceptance=accepted`, `r5_accepted_commit=165f4d001a2b59b582b397bdea79ec4826168fdb`); the review packet commit and acceptance-record follow-up are not implementation. R6/R7 remain gated; publication remains blocked. |
| R6 adversarial images | Exact implementation target `7ba3649f03cf13b65df33020e345d361cce2993a` accepted 2026-08-05 under accepted Plan revision R6-B | Finite 47-entry single-defect fixture catalogue over the byte-immutable accepted R5 target, with no new production surface under `include/`, `virt/`, or `arch/` (see [`single-hart-runtime-r6-evidence.md`](single-hart-runtime-r6-evidence.md) and its [review and acceptance record](single-hart-runtime-r6-review-summary.md)) | R7 was separately authorized after the acceptance record was privately pushed; hardware and publication remain blocked. |
| R7 proof and evidence | Exact plan accepted 2026-08-05 at `18c43596d308052cfad67edc6e2cb8f543f75600` and Plan revision R7-A accepted 2026-08-05 at `0605028220e3795d99393156d0bfb7d6a7d631a4`; **exact implementation target `9bf22913d67e9b72286813cd5f7993a9ad3857a8` accepted 2026-08-05** | Enumerated exact linked-byte proof adaptation, finite configuration trace, claim/cut-point ledger, evaluator, reports, documentation, and reproducibility bundle under [`single-hart-runtime-r7-plan.md`](single-hart-runtime-r7-plan.md); accepted revision R7-A enumerates exactly six authorized predecessor acceptance-pin refreshes and all six are re-derived and applied, with results in [`single-hart-runtime-r7-evidence.md`](single-hart-runtime-r7-evidence.md) and the exact-target decision carried by the [`R7 review and acceptance record`](single-hart-runtime-r7-review-summary.md) | Acceptance covers that exact commit only; the proof is bounded rather than whole-system formal verification, C refinement is not claimed, and hardware is `NOT RUN` |
| R8 K3 core validation | Dropped 2026-10-08; records kept as history | Ordered H0-H4 K3 validation under [`single-hart-runtime-r8-plan.md`](single-hart-runtime-r8-plan.md). R8, R8-A, and R8-C are accepted planning boundaries. Exact H0/R8-C target `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` is accepted as of 2026-09-17; its [review and acceptance record](single-hart-runtime-r8-h0-review-summary.md) attributes 147 rows, 118 `UNKNOWN`, 80 H0 blockers, 33 H1-completion blockers, three H2-entry blockers, `BLOCKED-NOT-READY`, and `r8_h0_exit=not-met`. | None. H1-H4 were never authorized or run. A new plan may recreate a formal K3 evidence package if the MVP plan needs one. |
| K3 bring-up B0-B6 | Complete and accepted 2026-10-06 to 2026-10-08 | RAM-only COM260 bring-up under `bringup/k3-b0` to `k3-b6`, each with its own plan or authorization and result record: boot marker (B0), the accepted R3/R4 entry (B1) and R5 checked switch (B2) ported to K3, U-Boot `booti` (B3), R6 and R7 re-derived for the K3 images (B4), a tiny bare-metal guest (B5), and an unmodified uniprocessor Linux `v7.2` guest (B6). Board results are diagnostic bring-up evidence for one board. | See the [roadmap](roadmap.md) milestone status. |
| Step 3 roadmap re-baseline | Complete and accepted 2026-10-08 at `ecad45d8eb371218d6f9a0965b330fa5043ea273` (instruction `accept ecad45`) | Docs-only: drop KVM0 and R8 H1-H4 with records kept as history, make the B-series the K3 path, and list the planned sequence in the [roadmap](roadmap.md). | Satisfied. |
| B7 two Linux guests | Complete and accepted 2026-10-09 at `7b6b846bf453bacf4c67d986f87c61fdc092e2ee` (instruction `accept 7b6b84, commit and push`); plan accepted 2026-10-08 at `026974fb` | Two B6 Linux guests, each in its own 64 MiB window and G-stage, sharing hart 0 round-robin, with nolibc demo programs; QEMU, then RAM-only COM260 runs | Satisfied; see the [review and acceptance record](k3-b7-result-review-summary.md). |
| S1-S3 synthesis, security model, MVP plan | **S1 accepted 2026-10-18 at `fd670dcd` with M01-A (`95ef0f6c`) and the S2 definition (`1ac7080f`); S2 plan accepted 2026-10-19 at `5ce7827f` and [security model v1](security-model-v1.md) accepted 2026-10-22 at `0e3eec8b`; S3 [MVP plan](mvp-plan.md) revision 1 accepted 2026-10-23 at `93967fba` (`06c35f48` superseded); the [M0 plan](mvp-m0-plan.md) accepted 2026-10-23 at `4d129808` - YOU ARE HERE: M0 implementation in progress** | S1 classifies Helium lessons against B0-B7 evidence; S2 defines security model v1; S3 plans the initial security-research-platform MVP, one domain per hart with a dedicated control hart; M0's plan bounds the MVP line, the multi-hart substrate, and the harness | Implement M0 under its plan; decide on its result. |
| Later Linux protected-domain milestone | Not authorized; deferred until the S3 MVP plan selects it | Linux management and protected domains, guest SBI/notifications, service semantics, and local measurement beyond the synthetic core-validation boundary | Approve a separate Linux/service plan and review TCB, exits, failures, and measurement protection |
| RISC-V multicore and extended K3 | Not authorized | Serialized multicore model/refinement, common conformance tests, and extended measured K3 results | Re-establish isolation properties and portability boundary after single-hart K3 validation |
| External I/O service | Not authorized | IOMMU ownership, one restartable service, bounded queue/grant protocol, and malicious-service tests | DMA containment, reset safety, and bounded parsing |
| Policy extension | Trigger-gated; not authorized | Only the capability or mandatory-policy mechanism justified by a concrete use case, with offline tooling and evidence | Demonstrate that added policy is necessary and bounded |
| Measured launch and attestation | Not authorized | Measured configuration/policy and architecture-specific evidence adapters | Document roots of trust, replay/update behavior, and vendor assumptions |
| Portability expansion | Conditional; not authorized | An Arm backend only if RISC-V evidence and maintenance value justify it | Reassess architecture and proof cost |
| Assurance release | Not authorized | Selected machine-checked invariants, fully open binary correspondence, reproducible dynamic evidence, and bounded assurance case | Open binary correspondence is mandatory |
| Upstream or foundation proposal | Not authorized | RFC/patch series or stable integration specification, tests, documentation, governance, and security process | Maintainer/community disposition |

## Remaining decision gates

The KVM0 gates (K0-S readiness, K0-X, and K0-R) and the R8 gates (an
exit-ready H0 successor and H1-H4) closed when the responsible human dropped
both workstreams on 2026-10-08; their records stay as history. The
controlling gates now follow the planned sequence in the
[roadmap](roadmap.md):

1. **Step 3:** satisfied by acceptance of exact commit
   `ecad45d8eb371218d6f9a0965b330fa5043ea273` on 2026-10-08 (`accept ecad45`).
2. **B7:** satisfied by acceptance of exact plan commit
   `026974fb619295482b93a7ae8cffdc4f552825ea` on 2026-10-08
   (`accept 026974`) and exact result commit
   `7b6b846bf453bacf4c67d986f87c61fdc092e2ee` on 2026-10-09
   (`accept 7b6b84, commit and push`).
3. **S1:** accept one Helium-to-Beryllium synthesis document. Done: S1
   was authorized (2026-10-16), and its revised
   [document](he-to-be-synthesis.md) was accepted on 2026-10-18 at exact
   commit `fd670dcd` (RP-1; `0fbca0fd` superseded), with Model 0.1 plan
   revision M01-A (`95ef0f6c`) and the revised S2 definition (`1ac7080f`)
   accepted in the same ordered instruction.
4. **S2:** accept security model v1. Under its revised definition (RP-3 of
   the accepted [revision plan](s1-te-trigger-revision-plan.md), accepted
   2026-10-18 at `1ac7080f`),
   S2 produces the policy specification, a central, declarative policy in
   the Type Enforcement family, with the analyses the policy proof targets
   name and its relation to the canonical manifest; the capability and
   runtime-check trigger evaluation, tested against the platform's use
   cases, and the dynamic authority ceiling belong here, and
   protected-service selection belongs here or in S3. Done: the
   [S2 plan](s2-security-model-plan.md) was accepted on 2026-10-19 at
   exact commit `5ce7827f`, and [security model v1](security-model-v1.md)
   on 2026-10-22 at exact commit `0e3eec8b` (`accept 0e3eec8b`). It
   selects no protected service, so that selection remains for S3 or a
   later plan.
5. **S3:** accept the MVP plan for the initial security-research platform.
   It selects any later milestone, including development-kernel/BSP
   selection, root integration, and a formal K3 evidence package. Done:
   the [plan](mvp-plan.md), revision 1, was accepted on 2026-10-23 at
   exact commit `93967fba` (`accept 93967fba`; `06c35f48` superseded). It
   selects M0 to M4 on three statically owned harts, decides no
   development kernel/BSP (D2), a self-contained MVP line (D3), no formal
   K3 package (D4), and M2's protected research domain as the
   protected-service use case (D10), and authorizes writing M0's bounded
   plan only. That [M0 plan](mvp-m0-plan.md) was accepted on 2026-10-23
   at exact commit `4d129808`; M0 implementation stopped at M0-3 by
   stop condition 3 and resumed under Plan revision M0-A (directed
   2026-10-23); M0-4 is complete at `19c3d455` under Plan revision M0-B
   (directed 2026-10-24; the evaluator builds from a verified local
   closure cache and passes with every image identical to the host's),
   and M0-5 needs the responsible human at the board.
6. Gather community feedback on the boundary and Linux integration form.
7. Require a separate later plan before Linux management or service
   semantics, guest SBI expansion beyond the accepted B5/B6 subset,
   services, multicore beyond the accepted MVP plan's static hart
   ownership, devices, policy integration, or any MVP milestone's
   implementation.
