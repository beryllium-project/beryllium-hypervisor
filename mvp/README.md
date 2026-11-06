<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M0 to M5: the MVP line

`mvp/` is the maintained MVP source line, seeded once from B7 by B7's
counted port method and changed in place from here on (MVP plan D3). M0 runs
two Linux domains, each on its own hart under static ownership, with hart 0
as the control hart. M1 adds security model v1's Instance 2 as the `te-poc`
scenario: one declared channel page between the two domains, a writer and a
reader, and three declared denied accesses, which the monitor logs and
delivers to the guests as access faults. M2 adds Instance 3 as the `anchor`
scenario: an untrusted Linux host and a protected Linux domain, each on its
own hart, three declared pages (a request and a response channel and a
secret page that only the protected domain maps), the protected domain
measured at boot, and a management extension through which the host may
pause or terminate the protected domain under the sealed manifest's one
static grant, decided by hart 0 alone. M3 added nothing under `mvp/`: its
policy layer, hart binding, and differential check are under `model/` (the
M3 result, `b0a0f352`). M4 adds the release candidate's four release
surfaces under `docs/`, the researcher guide
[`docs/guide.md`](docs/guide.md), the claim with its required limit and
forbidden phrasings [`docs/claim.md`](docs/claim.md), the claim ledger
`docs/claim-ledger.md` with its JSON source, and the AI-assistance
disclosure `docs/ai-assistance.md`, with the ledger's checker
`tools/claim-ledger.py`, and M4-4 the release-candidate record's tool
`tools/rc-record.py`; release candidate 1 (`c5df0cfa`) holds the records
of its gates and its board campaign. M5 makes the board's launch path a
boot from system reset for release candidate 2 (Plan revision S3-A of the
MVP plan): the board's resident firmware and U-Boot load the image from a
Beryllium partition on its NVMe under a boot command that a recorded
session installs in U-Boot's saved environment and restores, each line
typed at U-Boot one of the console tool's templates; the kexec loader and
its rehearsal are gone, and a U-Boot rehearsal in QEMU replaces the
latter. This tree holds M0's work packages M0-1 to M0-5 and its part of
M0-6, M1's M1-1 to M1-5 and its part of M1-6, M2's M2-1 to M2-5, Plan
revision M2-A, and its part of M2-7, M4's M4-1 to M4-5 and Plan revision
M4-A, and M5's M5-1 to M5-7:

- **M0-1:** the counted port with one more rule, the hart region; the
  layout; the G-stage and payload copies with a hart per root; the guest
  inputs, pins, reference boots, and repeat build; the Make controls; the
  `mvp` wrapper; the tool lock and its package closure; and the clean
  evaluator's definition.
- **M0-2:** the pure-C rings, hart blocks and control loop, and changed SBI
  core, host-tested with identical GCC and Clang output and pinned counts.
- **M0-3:** the monitor: hart 0's runtime and the domain harts', the hart
  entry, the vector and resume tail, the shim with the start rule, the
  boot images, the negative variants, the scenario generator, the probe
  module and VS probe stub with the three probe images, the image checker
  with its MVP and probe profiles and its mutation test, the budgets, and
  a provisional eight-hart QEMU driver.
- **Plan revision M0-A:** the MVP region, which holds the MVP layer's C
  outside every accepted extent (the remedy for stop condition 3); the
  boot-hart rule in `BE_MVP:02`; and the `ring-full` variant's drain
  delay (see [Plan revision M0-A](#plan-revision-m0-a)).
- **M0-4:** the capture checker, with its self-test and seeded mutations;
  the QEMU suite, each attempt judged by the checker and a REFUSED attempt
  made again; the eight-hart kexec rehearsal; B7's board tools, ported
  with the layout rule, and their dry run against a fake board; the
  evidence bundle; and the evaluator's image comparison (see
  [Harness](#harness-m0-4)).
- **Plan revision M0-B:** the evaluator's closure source: a SHA-256 for
  each closure RPM, a tool that fetches the closure once into a verified
  local cache, an image built from that cache with every repository
  disabled, and podman, ssh, and scp as host-only lock roles (see
  [Plan revision M0-B](#plan-revision-m0-b)).
- **Plan revision M0-C:** hart 0's drain order: on each wake at most one
  record from each domain's ring in turn, each take inside the ring's
  reader protocol, so the console follows the order in which records
  became visible; K = 8 kept and re-justified; and the first board
  scenario run's capture, which the old order failed, kept as a negative
  fixture (see [Plan revision M0-C](#plan-revision-m0-c)).
- **M0-5:** the board campaign on the one COM260 (K3) with the M0-C
  images: both load checks (load and unload, no kexec), then eight
  RAM-only `kexec_load` runs, each followed by a human reset: the three
  GCC probe runs, three GCC and one Clang scenario runs, and the
  `payload` run; all eight pass (see
  [M0-5's second board campaign](#m0-5s-second-board-campaign-2026-10-25-and-26)).
- **M0-6 (this tree's part):** the platform record's generator,
  `tools/platform-record.py`, which `tools/evidence.py --board` runs into
  every board record; the board record's tree state read before its
  load-check staging directory exists, with the dry run's `tree-state`
  case; the campaign's board record `results/20261025-com260/` with its
  platform record, made against the M0-6 content and committed after it;
  `kernel-repro` again; the gates on `l1`; the checker-to-monitor
  size; and these results (see
  [The board record and the platform record](#the-board-record-and-the-platform-record-m0-6-2026-10-26)).
  The result packet, `planning/mvp-m0-result-review-summary.md`, and the
  status documents are outside `mvp/`.
- **M1-1:** the `te-poc` scenario (schema v2: the policy, the labeling, the
  manifest with its one channel, the accepted exits, the roles, and the
  expected lines and denials) and its two build-time negatives; the offline
  checker `tools/policy-check.py` (A1 to A6 and A8, A7 vacuous) with its
  authority report and configuration identity; `two-guests`' expectations
  unchanged (see
  [M1-1 and M1-2](#m1-1-and-m1-2-at-0174f7a8-and-b591b187-2026-10-26)).
- **M1-2:** the channel page in the G-stage: a level-0 page per root, the
  builder and walker for it, and the channel check, host-tested.
- **M1-3:** the denial path (the pure decision, the injection helper, the
  DENIAL record, and hart 0's DENY line), the channel check and the channel
  page's clear at boot, the denial host test, the image checker's new rules,
  and the `te-poc` images with the `reader-write` and `no-inject` variants
  (see [M1-3](#m1-3-at-d3d28d7e-2026-10-26)).
- **M1-4 and Plan revision M1-A:** the guests' side: the MVP's own Kconfig
  fragment for `/dev/mem` with its `.config` delta check and the init's
  roles; after stop condition 6, the denied accesses in a forked child of
  the init (M1-A); the capture checker's schema-v2 rules, the fixtures, the
  QEMU suite, the rehearsal, and te-poc in the evidence bundle (see
  [M1-4 and its stop](#m1-4-and-its-stop-stop-condition-6-plan-revision-m1-a)).
- **M1-5:** the board tools' remote reset through the pinned `k3ctl` client,
  the te-poc board selector (`SCENARIO=te-poc`), the channel page in the
  loader's layout rule, the firmware identity in the preflight, the
  campaign's pause, and their dry run (see
  [M1-5's tools](#m1-5s-tools-at-9020c4f8-2026-10-27)); and the first board
  campaign, which stopped at stop condition 6.
- **Plan revision M1-B:** a failed domain hart's wait for hart 0's ACK
  restarts on hart 0's progress (see
  [Plan revision M1-B](#plan-revision-m1-b)); the second board campaign ran
  with its images (see
  [M1-5's second board campaign](#m1-5s-second-board-campaign-2026-10-27)).
- **M1-6 (this tree's part):** the platform record's M1 sections and their
  dry-run checks; the second campaign's board record
  `results/20261027-com260-m1b/` with its platform record, made against the
  M1-6 content and committed after it; the checker-to-monitor size; and
  these results (see [M1-6](#m1-6-2026-10-27)). The result packet and the
  status documents are outside `mvp/`.
- **M2-1:** the `anchor` scenario (schema v3: Instance 3's policy, the
  labeling, and a manifest with the three pages, the management grant, the
  secret, and the measured domain) and its two build-time negatives; the
  offline checker's `domain` class and management grants; the generator's
  v3 expectations, with the requests' HMAC digests and the expected
  measurement; and anchor's DTBs (see
  [M2-1 and M2-2](#m2-1-and-m2-2-at-f149eea0-and-d6667862-2026-10-27)).
- **M2-2:** the three shared pages in the G-stage, each root's leaves
  checked at boot; SHA-256 and HMAC-SHA-256 in restricted C; the secret's
  placement and the protected domain's measurement; and the anchor images
  with the `secret-shared`, `response-writable`, and `wrong-measurement`
  variants.
- **M2-3:** the management extension, `pause` and `terminate`: the domain
  harts' request and synchronous wait, hart 0's decision, delivery, and
  log, the paused and terminated states, and the completion rule; the
  page-aware denial decision; the image checker's reachability rule; and
  the `no-grant-check` variant (see [M2-3](#m2-3-at-2d23efe4-2026-10-28)).
- **M2-4 and its follow-up:** the guests' side: the management module, the
  repository's one `GPL-2.0-only` file, with `CONFIG_MODULES=y` and its
  `.config` delta; the init's `host` and `prot` roles; and the host's
  one-second poll deadline (see
  [M2-4 and its follow-up](#m2-4-and-its-follow-up-at-51893419-and-f687b791-2026-10-28)).
- **M2-5:** the harness for `anchor`: the capture checker's schema v3,
  anchor's fixtures, its QEMU runs and kexec rehearsal, the board tools'
  `SCENARIO=anchor` with its two board variants and their dry run, the
  evidence bundle and board record, and the platform record's M2 sections
  (see [M2-5](#m2-5-2026-10-28)).
- **Plan revision M2-A:** after M2-6's first board campaign stopped at
  stop condition 6, the capture checker's rule for the IPI probe
  answered inside a management wait, the generator's `spv=<S>`, the
  stopped board run's capture as a passing fixture with its mutations,
  and the platform record's probe subsection (see
  [M2-6's first board campaign and its stop](#m2-6s-first-board-campaign-and-its-stop-stop-condition-6-plan-revision-m2-a));
  M2-6's second board campaign ran under it with the same images (see
  [M2-6's second board campaign](#m2-6s-second-board-campaign-2026-10-28)).
- **M2-7 (this tree's part):** the second campaign's board record
  `results/20261028-com260-m2a/` with its platform record, to be made
  against the M2-7 content and committed after it; the checker-to-monitor
  size; and these results (see [M2-7](#m2-7-2026-10-28)). The result
  packet and the status documents are outside `mvp/`.
- **M4-1:** the MVP claim, its required limit, and its forbidden
  phrasings, `docs/claim.md`, byte for byte the M4 plan's fixed text; the
  claim ledger, `docs/claim-ledger.json` and the `docs/claim-ledger.md`
  rendered from it; and its checker, `tools/claim-ledger.py` (`check`,
  `render`, `join`, and a seeded self-test), which `check` runs after the
  evidence bundle (see
  [M4-1 to M4-3](#m4-1-to-m4-3-at-30800dd3-c0097a4c-and-90b6b4a5-2026-10-28)).
- **M4-2:** the researcher guide, `docs/guide.md`, in the M4 plan's nine
  sections, every `./mvp/mvp` command one that `mvp help` lists.
- **M4-3:** the AI-assistance disclosure, `docs/ai-assistance.md`; the
  ledger's row C-23 reworded so that its non-claim states only what is not
  claimed; this README's title, opening, and M4 entries, with open items
  63 to 67; and the root `README.md`'s pointer to the guide and the claim.
  M4-4 (the release-candidate record), M4-5 (the board campaign, after the
  responsible human confirms the K3 free), and M4-6 (the evidence record
  and the packet) follow.
- **Plan revision M4-A:** after M4-4's stop condition 9, the board
  record's code names: `tools/evidence.py` rewrites the board's ssh target
  to `<board-ssh>` and its IPv4 address to `<ip>` in every copy and
  refuses a record any file of which still holds either; and the record's
  title, the caller variable `K3_RECORD_TITLE` (see
  [Plan revision M4-A](#plan-revision-m4-a-at-this-commit-2026-10-29)).
- **M4-4 and M4-5:** the release-candidate record's tool,
  `tools/rc-record.py`; the record of the seven gates at the candidate
  tree `d42b9ec0`, `results/20261029-rc/`; and the board campaign's
  record, `results/20261029-com260-rc/`, eleven RAM-only `kexec_load`
  runs at its images (see
  [M4-4's gates](#m4-4s-gates-and-the-release-candidate-record-at-d42b9ec0-2026-10-29)
  and [M4-5's board campaign](#m4-5s-board-campaign-2026-10-29)).
- **M5-1:** the partition tool `tools/k3-make-partition.sh`, which the
  responsible human runs on the board, and its host self-test on fake
  block tools (`tests/test-k3-make-partition.sh`,
  `tests/fake-partition-tools/`), delivered with the M5 plan; the human
  made the partition with it on 2026-10-30 (see
  [M5-1 to M5-4](#m5-1-to-m5-4-2026-10-29-and-30)).
- **M5-2:** the board tools for a boot from reset: the console tool
  `tools/k3-console.sh` and its reader of the serial log
  `tools/k3-uboot.py`; the staging and environment tools
  `tools/k3-stage.sh` and `tools/k3-env.sh`; `tools/k3-run.sh`,
  `tools/k3-campaign.sh`, and `tools/k3-preflight.sh` rewritten for runs
  from a reset; the capture checker's `uboot` mode; the QEMU-only images
  and their image check; the board record of a session, with MAC and
  `serial#` code names; the board tools' dry run on a fake U-Boot; and
  the kexec loader, its test, the kexec rehearsal, and the load check
  removed, with the read-only probe kept as `tools/platform-probe.py`.
- **M5-3:** the U-Boot rehearsal in QEMU, `tests/uboot-rehearsal.sh` with
  its driver `tests/uboot-rehearsal/run-qemu-uboot.py`, and its lock roles
  and U-Boot pins.
- **M5-4:** the four release surfaces for release candidate 2 (the claim's
  board clause and required limit, the guide, the disclosure, and the
  ledger), the operator's walkthrough in `planning/`, and this README's M5
  entries.
- **M5-6a, M5-5, M5-6, and M5-7:** the attended characterization on the
  COM260 (seven attempts, the seventh passing end to end); the seven
  gates at the candidate tree `X2` (`6dd81ee3`) and the release-candidate
  record `results/20261030-rc2/`; the board session of twenty runs from
  system reset at `X2`'s images, the environment installed and restored,
  and its record `results/20261030-com260-rc2/`; the ledger's rows for
  both and the evidence record `planning/mvp-m5-evidence.md` (see
  [M5-5 to M5-7](#m5-6a-m5-5-m5-6-and-m5-7-at-6dd81ee3-2026-10-30)).

M0's accepted plan is
[`planning/mvp-m0-plan.md`](../planning/mvp-m0-plan.md) (accepted at
`4d129808`, record `6ef36d3a`), with Plan revisions M0-A, M0-B, and M0-C
appended to it (directed on 2026-10-23, 2026-10-24, and 2026-10-25, and
accepted as implemented at `30c5e1a8`, `77559def`, and `260ceba6` with M0's
result). M1's is [`planning/mvp-m1-plan.md`](../planning/mvp-m1-plan.md)
(accepted at `7b2c055c` on 2026-10-26, record `41f88795`), with Plan
revisions M1-A and M1-B appended to it (both directed on 2026-10-27, and
accepted as implemented at `00051fc4` and `745c293a` with M1's result).
M2's is [`planning/mvp-m2-plan.md`](../planning/mvp-m2-plan.md) (accepted
at `854a5415` on 2026-10-27, record `35ebe8a7`, by the instruction
`accept 854a5415 , gpl 2.0 only ok`, which answers Q20; Q1 to Q19 take
their defaults), with Plan revision M2-A appended to it (directed on
2026-10-28 after M2-6's first board run, at `adc989fa`, implemented at
`ac0d48dd`, and accepted as implemented with M2's result). M4's is
[`planning/mvp-m4-plan.md`](../planning/mvp-m4-plan.md) (accepted at
`0d02df72` on 2026-10-28, record `4e10fca3`, by the instruction `accept
0d02df27, authorize M4`, read as `accept 0d02df72`; Q1 to Q13 take their
defaults), with Plan revision M4-A appended to it (accepted as
implemented with M4's result). M5's is
[`planning/mvp-m5-plan.md`](../planning/mvp-m5-plan.md) (accepted at
`0066794d` on 2026-10-29, with Plan revision S3-A of the MVP plan at
`0d134bbc`, record `9b3fa982`, by the instruction `accept 0d134bbc and
066794d, authorize m5`, read as `0066794d`; Q1 to Q16 take their
defaults; erratum 1 of its acceptance record re-sets the code limit to
10,000 lines); M3's plan changes nothing here.
Each plan is authoritative for its milestone; where this README and
a plan differ, the plan wins, and [Open items](#open-items) lists every
difference found.

**Status:** M0's result, exact commit `b2669725`, is responsible-human
accepted (2026-10-26, instruction `accept b26697`), which also accepts Plan
revisions M0-A, M0-B, and M0-C as implemented
([`planning/mvp-m0-result-review-summary.md`](../planning/mvp-m0-result-review-summary.md));
`beryllium/mvp-m0` and the development branch are on the private `origin`
at `6f7b6e7c`, M0's acceptance record. In M0, M0-3 had stopped at
stop condition 3 for Clang (its monitor text ended `0x7e0` bytes above the
accepted `0x1_0200_8000`); M0-A moved the MVP layer's C into the MVP region
(`65454598`), admitted the start rule's boot hart in `BE_MVP:02`
(`106062f6`), and made the `ring-full` variant fill a ring (`ebae089d`).
M0-4 had stopped at stop condition 11, its evaluator's image not building
from the pinned base and the recorded closure (open item 7); M0-B records a
digest for each closure RPM, fetches the closure into a verified cache, and
builds the image from it with repositories disabled and five base packages
removed by name (`b364fe92`, `83916b5a`, `67731e4c`). At `67731e4c`,
`./mvp/mvp check`, `./mvp/mvp kexec-rehearsal`, and `./mvp/mvp evaluate`
passed: inside the evaluator the tool lock passed with its three host-only
roles skipped, every gate passed, and all 146 images equalled the host's
byte for byte (see [Results](#results-this-host)). M0-5 began on the COM260
on 2026-10-24: the preflight, both load checks, and the three GCC probe
runs passed, and the first GCC scenario run ran both domains to `BE_MVP:14`
but failed the capture checker's alternation floor (5 alternations, below
K = 8), because hart 0 drained each ring to empty in turn behind the
115200-baud console; the campaign stopped there (stop condition 6; open
item 32). Plan revision M0-C makes the drain round-robin (`129626e0`) and
keeps that capture as a negative fixture (`c5ecedee`). A host update then
failed the tool lock (open item 33); on the direction `refresh the lock`
the closure took the host's new `ca-certificates` (`804fa95f`), and
`./mvp/mvp check`, `./mvp/mvp evaluate` (146 of 146 images identical), and
the kexec rehearsal passed on the M0-C images. M0-5's second board
campaign, on 2026-10-25 and 26 with the M0-C images, passed every run: both
load checks, the three probe runs, three GCC and one Clang scenario runs
(each with 125 alternations in 2 wakes), and the `payload` run as declared,
with no stop (open item 32 resolved). Its first four runs were driven from
the Fedora laptop `lx2`, where every earlier result here was made, and the
last four from the workstation `l1`, to which the workspace and `build/`
moved. On `l1`, on the responsible human's form answers `qemu=install-exact`
and `lock=refresh-ssh-scp`, QEMU and ShellCheck were installed at the
lock's and the closure's NEVRAs and the lock was refreshed for `l1`'s
newer OpenSSH, which also put two packages of `l1`'s installed set in the
closure (259 packages; open item 39). M0-6's
board record, with the platform record that `tools/platform-record.py`
writes into it, is `results/20261025-com260/`: first written on `l1` at
06:53 UTC, before the lock refresh, and made again against the exact
commit `13992d6d` with the refreshed lock (`source_tree=clean`), in the
commit after it.
`tools/evidence.py` now reads a board record's tree state before it
stages the load checks (open item 41); `kernel-repro` passed again on
`l1`. At the M0-6 content, on `l1`, `./mvp/mvp check`, `./mvp/mvp
evaluate` (the evaluator's image built from the 259-package closure; 146
of 146 images identical), and the kexec rehearsal pass (see
[Results](#the-host-move-and-the-lock-refresh-on-l1-2026-10-26)), after
the account's stale rootless podman storage was moved aside (open item
43).

M1-1 to M1-5, Plan revisions M1-A and M1-B, and this tree's part of M1-6
were implemented on the branch `beryllium/mvp-m1`, from the M1 plan's
acceptance record `41f88795`. M1's result, exact commit `ff84533c` (parent
`17ed82f7`), is responsible-human accepted (2026-10-27, instruction
`approve ff84533c and revisions, accept your recommendations, authorize
proceeding per those`), which also accepts Plan revisions M1-A and M1-B
as implemented
([`planning/mvp-m1-result-review-summary.md`](../planning/mvp-m1-result-review-summary.md)).
M1-1 and M1-2 (`b591b187`, `0174f7a8`) added the `te-poc`
scenario with its offline checker and the channel page in the G-stage, and
M1-3 (`d3d28d7e`) the denial path and the te-poc images. M1-4 stopped at
stop condition 6 (`8c2cbbfd`): in QEMU every denial reached the init as
`SIGSEGV` and the init went on, but Linux `v7.2` printed `unhandled signal`
for pid 1 whatever handler it installed; Plan revision M1-A moved the denied
accesses into a forked child of the init, and M1-4 completed under it
(`65648204`). M1-5's tools (`9020c4f8`) passed off the board. Its first
board campaign, on 2026-10-27 with those images, passed the preflight, both
load checks, three GCC and one Clang `te-poc` runs, and the `reader-write`
run, and stopped at the `no-inject` run (stop condition 6): both domain
harts took Q10's fallback, because their wait for hart 0's ACK had a fixed
window that hart 0's output on the 115200-baud console outlasted. Plan
revision M1-B (`804cd24c`) restarts that window each time hart 0 takes a
record from the failed hart's ring. The second campaign, with `804cd24c`'s
images, passed its preflight, both load checks, and all six RAM-only
`kexec_load` runs on the COM260 (K3), each followed by one `k3ctl` reset and
none by hand: three GCC and one Clang `te-poc` runs, each with `exits_g0=163
exits_g1=167 denials_g0=1 denials_g1=2 records=146 wakes=2
alternations=127`, every DENY line matched by its guest's report and the
writer's and the reader's digests equal, and `reader-write` and `no-inject`
as declared (see
[M1-5's second board campaign](#m1-5s-second-board-campaign-2026-10-27)).
That is diagnostic bring-up evidence for one board, not hardware validation
and not a security claim (see [Non-claims](#non-claims)). The board record
and the gates at the exact M1-6 commit are recorded in
[M1-6](#m1-6-2026-10-27).

M2-1 to M2-5 and Plan revision M2-A were implemented on the branch
`beryllium/mvp-m2`, from the M2 plan's acceptance record `35ebe8a7`, on
the workstation `l1`. M2's result, exact commit `18d552bc` (parent
`397670e5`), is responsible-human accepted (2026-10-28, instruction
`accept 18d552bc`), which also accepts Plan revision M2-A as implemented
([`planning/mvp-m2-result-review-summary.md`](../planning/mvp-m2-result-review-summary.md));
on `approve 1 & 2. proceed` the same day the development branch was
fast-forwarded to `50b77c00`, M2's acceptance record, and pushed to the
private `origin` with `beryllium/mvp-m2` and `beryllium/mvp-m2-plan`.
M2-1 (`f149eea0`)
added the `anchor` scenario, Instance 3, and the offline pipeline's v3;
M2-2 (`d6667862`) the three pages, the SHA-256, and the measurement, with
`3b71575d` integrating the two; M2-3 (`2d23efe4`) the management extension
and the page-aware denial; M2-4 (`51893419`, and `f687b791` for the host's
poll deadline) the guests' module and roles; and M2-5 (`da7d270f`) the
harness. On M2-5's working tree over `f687b791` (`source_tree=dirty
changed=19`; `da7d270f` commits those 19 files), before it was committed,
`./mvp/mvp check` (the host tests on their pinned counts, 58 QEMU runs
each judged by the capture checker, 65 self-test cases and 224 mutations
of the checker), the kexec rehearsal (six images), and `./mvp/mvp
evaluate` (247 of 247 images identical between host and evaluator)
passed (see [M2-5](#m2-5-2026-10-28)). In QEMU an `anchor` run prints
every line the plan's Markers name: the measurement equal to the
generator's, five denials logged and injected, fifteen management
requests decided by hart 0 with the declared results, the protected
domain paused and then terminated with its measurement unaltered, four
requests answered with the HMAC values the checker recomputes, and the
host's `RESULT pass` (see
[M2-4 and its follow-up](#m2-4-and-its-follow-up-at-51893419-and-f687b791-2026-10-28)).
M2-6, the board campaign, began on 2026-10-28 (UTC) after the responsible
human confirmed the shared K3 free: the preflight and both `anchor` load
checks passed, and the first `anchor` run (`20261028T023339Z`, GCC)
reached `SHUTDOWN` with every line the plan names but stopped at stop
condition 6 on hart 2's `IPI_PROBE … spv=0`, the PING served inside the
protected domain's first management wait, which plan Q14 describes and
the checker's expectation did not admit. The responsible human directed
Plan revision M2-A (`adc989fa`, implemented at `ac0d48dd`; the checker's
rule, no monitor or image change), and the second campaign, with the
same images under M2-A's checker, passed all six RAM-only `kexec_load`
runs: three GCC and one Clang `anchor` runs with the first run's counts,
hart 2's probe answered inside its first management wait in each, and
`wrong-measurement` and `no-grant-check` as declared (see
[M2-6's second board campaign](#m2-6s-second-board-campaign-2026-10-28)).
After its first run the board came back from the `k3ctl` reset without
network, the run tool stopped (stop 10; M2's stop condition 9), and a
second reset by hand on the responsible human's direction preceded the
resumed campaign (open items 59 and 60). The gates at the exact M2-7
commit and the board record are M2-7's (see [M2-7](#m2-7-2026-10-28)).
That is host evidence and QEMU emulation; a board run is diagnostic
bring-up evidence for one board; neither is a security claim (see
[Non-claims](#non-claims)).

M4-1 (`30800dd3`), M4-2 (`c0097a4c`), and M4-3 (`90b6b4a5`), M4-4's tool
(`0a968bf0`, `ca322220`), and Plan revision M4-A (`0b2ac6fa`) were made on
the branch `beryllium/mvp-m4`, from the M4 plan's acceptance record
`4e10fca3`; they change no monitor, shim, guest, scenario, generator,
checker-rule, or lock byte (see
[M4-1 to M4-3](#m4-1-to-m4-3-at-30800dd3-c0097a4c-and-90b6b4a5-2026-10-28)
and [Plan revision M4-A](#plan-revision-m4-a-at-this-commit-2026-10-29)).
The candidate tree is `d42b9ec0`, and M4's result, the release-candidate
commit `c5df0cfa`, MVP 1.0 release candidate 1, is responsible-human
accepted (2026-10-29, instruction `no worries on the other project,
correct decision. accept c5df0cfa, commit & push, I will review in
detail.`), with Plan revision M4-A as implemented
([`planning/mvp-m4-result-review-summary.md`](../planning/mvp-m4-result-review-summary.md));
`beryllium/mvp-m4` and `beryllium/mvp-m4-plan` are on the private
`origin`. Its board evidence is eleven RAM-only `kexec_load` runs (see
[M4-5's board campaign](#m4-5s-board-campaign-2026-10-29)).

M5, release candidate 2, is implemented on branches from the M5 plan's
acceptance record `9b3fa982` and is neither reviewed nor accepted. M5-2
and M5-3 (merged at `d798b065` and `dd0a5817`, with `0e733e76`) replace
the board's kexec launch with a boot from system reset and the kexec
rehearsal with a U-Boot rehearsal in QEMU, and change no monitor source,
shim, guest input, scenario, generator, or expectation; M5-4 rewrites the
release surfaces, the walkthrough, and this README for it. On 2026-10-30
the responsible human made the `beryllium` partition on the board with
the delivered tool. The characterization (M5-6a), the gates at the
candidate tree `X2` (M5-5), the board session (M5-6), and the
release-candidate commit `R2` with its packet (M5-7) follow; this tree
holds no M5 board record, and nothing is tagged, pushed, published, or
released (see [M5-1 to M5-4](#m5-1-to-m5-4-2026-10-29-and-30)).

## Design

M0 keeps B7's shape where B7 still applies and replaces its single-hart
time sharing with static hart ownership (plan, "Architecture"). M1 adds one
declared channel page between the two domains and a denial path for the
accesses a root does not map and the stores to a channel page it maps
read-only, with no type, rule, or policy at run time (M1 plan,
"Architecture"). M2 grows the channel page into three declared pages, a
request and a response channel and a secret page that only the protected
domain reads; hart 0 measures the protected domain before any domain hart
starts; and a management extension lets a domain ask hart 0 to pause or
terminate another, which hart 0 alone decides against the sealed
manifest's static grants. M2 adds no `decide`, type, or label to HS (M2
plan, "Architecture" and "The triggers for Instance 3").

- **Hart identifiers** (`src/mvp-layout.h`, plan "Hart identifiers"). The
  control hart is 0, fixed by the accepted R3 boot check. The domain harts
  are scenario data, hart 1 for G0 and hart 2 for G1 by default (Q12), and
  the platform has eight. A binding (`struct be_mvp_binding`) names each
  domain's hart, VMID, and root; nothing else depends on the numbers. A
  hart ID is a name: the checks refuse the control hart, ~0 (the all-harts
  IPI base), and a hart or VMID or root shared by both domains, and leave
  existence to the firmware, so the `hart-start` variant's hart 9 is
  left for `hart_start` to refuse, as the plan's table expects.
- **Hart region** (port rule `hart-region`, `src/mvp-layout.h`). A NOLOAD
  region of two 64 KiB blocks at `0x1_0204_4000`, right after B7's pool,
  in the pool's segment (Q1). Each block holds the hart's 8 KiB trusted
  stack, the saved page at the stack top (`0x2000`), the state page
  (`0x3000`), a 4 KiB inbound ring (`0x4000`), a 32 KiB outbound ring
  (`0x5000`), and `0x3000` unused bytes. Static assertions tie every
  offset, keep the region off the staged image and both windows, and the
  payload check refuses a staged image on it.
- **MVP region** (Plan revision M0-A.1; port rules `region-*` and
  `mvp-region`, `src/mvp-layout.h`). The code, constants, data, and BSS
  of the MVP layer's C objects (`mvp-runtime.o`, `mvp-hartmain.o`,
  `mvp-sbi.o`, `mvp-hart.o`, `mvp-ring.o`, `mvp-gstage.o`, `mvp-payload.o`,
  `mvp-sha256.o` in the images whose scenario declares pages (M2-2), and
  `mvp-probe.o` in the probe images) in `.mvp.text`, `.mvp.rodata`,
  and `.mvp.data` (data, then BSS) at `0x1_0206_4000`, right after the
  hart region, at most `0x40000` bytes, in three PT_LOAD segments of their
  own (R-X, R, RW). The assembly (`mvp-trap.o`, `mvp-hartentry.o`, and
  the probe images' `mvp-probe-arch.o`) stays in the accepted code extent,
  where the accepted R3 validation requires the vector. The flat image is
  the bytes from `0x1_0200_0000` to the region's end, exactly `0xa4000`;
  hart 0 checks the linked region against the layout and zeroes its BSS
  before it uses any MVP static, because the accepted entry clears only
  the accepted BSS. See [Plan revision M0-A](#plan-revision-m0-a).
- **Channel page** (`src/mvp-layout.h`, `src/mvp-gstage.{h,c}`; M1 plan,
  "G-stage and VMIDs", Q1; M1-2). At most one MVP-owned 4 KiB page per
  scenario, at HPA `0x118000000`, directly above G1's window, and at GPA
  `0x84000000` in both roots, directly above each window: in the windows'
  root entry and level-1 table at index 32, level-0 index 0. Each root maps
  it through a level-0 page of its own, the page after its level-1 page in
  its pool (`0x102039000` for G0, `0x102041000` for G1), with the rights the
  sealed channel record gives that domain: te-poc's writer, G0, gets the
  leaf `0x460000d7` (V R W U A D) and its reader, G1, `0x46000053` (V R U
  A). Hart 0 builds each root with its leaf (`be_mvp_gstage_build_channel`),
  re-walks every pool byte (`be_mvp_gstage_walk_channel`), and checks that
  the two walked roots share exactly the declared page with its declared
  rights (`be_mvp_gstage_channel_check`, in place of M0's pair check),
  printing `BE_MVP:03 CHANNEL_CHECKED` with both level-0 pages, both leaves,
  and the configuration identity; after both windows it zeroes the page
  through its HS backing and reads it back (`BE_MVP:05 CHANNEL_CLEARED`). A
  scenario without a channel maps the page in neither root, so `two-guests`'
  roots are M0's byte for byte.
- **Shared pages and the measurement** (`src/mvp-layout.h`,
  `src/mvp-gstage.{h,c}`, `src/mvp-sha256.{h,c}`, `src/mvp-runtime.c`; M2
  plan, Q1, "The measurement", "G-stage and VMIDs"; M2-2, not reviewed).
  The MVP-owned extent at `0x118000000` grows to three pages
  (`BE_MVP_SHARED_PAGES_HPA`, `BE_MVP_SHARED_PAGES_BYTES` `0x3000`,
  `BE_MVP_PAGES_MAX` 3), M1's channel page its first; every leaf sits in
  the root's one level-0 page behind level-1 entry 32. A scenario that
  declares pages (schema v3, `BE_MVP_SCENARIO_PAGES`) gives each a record
  (`struct be_mvp_gstage_page`: GPA, HPA, size, kind, writer, reader, and
  each domain's rights, 0 for no leaf); hart 0 builds each root's leaves
  from them (`be_mvp_gstage_build_pages`), re-walks every pool byte
  (`be_mvp_gstage_walk_pages`), and checks that each root's walked leaf is
  the declared one and that a domain without rights has no leaf
  (`be_mvp_gstage_page_check`), printing `BE_MVP:03 PAGE_CHECKED` per
  page. After both windows it clears the channel pages (`BE_MVP:05
  PAGE_CLEARED`) and writes the scenario's 32-byte secret, the rest zero,
  into the secret page (`BE_MVP:05 SECRET_PLACED`); after both payloads it
  hashes, with its own SHA-256, the protected domain's kernel and DTB as
  placed, the secret page, and the configuration identity, keeps the value
  in hart 0's `be_mvp_measurement`, and compares it with the scenario's
  expected value (`BE_MVP:06 MEASURED`, or `BE_MVP:FAIL measurement`). A
  scenario with M1's channel record (v2) or none (v1) keeps M1's lines and
  roots byte for byte.
- **State page** (`struct be_mvp_state_page`, `src/mvp-hart.h`). The four
  ring indices first, each alone in its 64-byte line (inbound head and
  outbound tail are hart 0's; inbound tail and outbound head the domain
  hart's), then the block descriptor hart 0 publishes, the first-entry
  frame, the armed readbacks, the SBI core's state with the 256-byte line
  buffer, and the entry time; 1,216 bytes of the page's 4,096 at M0, and
  1,280 by the structures' layout since M1-3, whose exit record holds
  `vsstatus` and whose SBI state holds the image's denial entry and the
  `denials` counter.
- **Block descriptor and check** (`src/mvp-hart.{h,c}`). Hart 0 fills each
  block's descriptor from the layout and the binding (`be_mvp_block_fill`)
  and writes the generation word last, after `fence w, w`. A domain hart,
  given its hart ID in `a0` and its block in `a1`, checks after
  `fence r, r`, in this order: the bindings, the generation word, the
  domain, the hart against the binding and `a0`, the block against the
  layout and `a1`, every page and ring offset, the ring capacities, and the
  Sv39x4 `hgatp` of its binding (`be_mvp_block_check`).
- **Rings** (`src/mvp-ring.{h,c}`, plan "Hart region", Rings). One
  single-writer, single-reader byte ring per direction and domain, with a
  power-of-two capacity of 512 bytes to 32 KiB, free-running indices, and
  no atomic read-modify-write. A record is a 16-byte header (type, domain,
  length, reserved, the writer's `time`) and at most 256 payload bytes,
  padded to 8. The writer posts, then publishes the head; the reader
  acquires the head, takes, then releases the tail. The memory ordering is
  the caller's, at the places the API splits: `fence w, w` before
  publishing, `fence r, r` after acquiring, and `fence r, w` before
  releasing (see [Open items](#open-items)). A writer that finds no room
  fails and never overwrites; the reader validates every header (type
  carried by the ring, domain, length, reserved word, zero padding, a
  record inside the acquired head) and every head; any refusal fails the
  view and it stays failed. The writer keeps its high-water mark, and
  reads the reader's tail and its own published head
  (`be_mvp_ring_taken`, `be_mvp_ring_published`; Plan revision M1-B),
  each 0 for a failed view or a reader's.
- **Records** (`src/mvp.h`). Outbound: READY (eight armed readbacks),
  ENTERED (pc, `a0`, `a1`), LINE (one console line, no prefix or LF), PONG
  (the PING's time, the receipt, `hstatus.SPV`), SHUTDOWN (the domain's
  ten counters, the ring's high-water mark, the entry time, and since M1-3
  its denial count, and since M2-3 its management requests), DENIAL
  (M1-3; see the denial path below), and FAIL (the class and up to eight
  detail words). Inbound: PING and ACK. The management extension's (M2-3;
  see below): outbound MGMT_REQUEST (the function, the target, the
  request's sequence number), PAUSED and TERMINATED (the exits, the
  requester); inbound MGMT_RESULT (the result, the sequence number), PAUSE
  and TERMINATE (the requester).
- **Control loop** (`struct be_mvp_control`, `src/mvp-hart.{h,c}`). Hart 0's
  state machine over the records it drains, per domain: started, READY,
  ENTERED, LINE records, one PONG, then SHUTDOWN, or FAIL at any point
  after the start. The first LINE of a domain asks for its one PING (Q4);
  SHUTDOWN needs the PONG and names the ENTERED time and the number of
  LINE records hart 0 drained. Records out of order, malformed, or going
  back in time fail the run as `ring`, a PONG not asked for or a SHUTDOWN
  owing one as `ipi`; FAIL ends the run with the domain's class. A wake
  checks the READY wait (2^26 ticks from the start) and the run budget
  (2^32 ticks); a clock behind the start fails as `run-timeout`. Every
  counter saturates and every failure is sticky. Since M1-3 a DENIAL is a
  step of its own, and a SHUTDOWN's denial count must equal the DENIAL
  records drained for its domain (see the denial path below).
- **Concurrency** (Q5). `be_mvp_overlap` intersects the two domains'
  entry-to-shutdown intervals; `be_mvp_concurrent` passes an overlap of at
  least half the shorter interval, exactly half included;
  `be_mvp_control_overlap` gives `BE_MVP:13`'s `overlap_ticks` whether or
  not the floor is met. The alternation floor (K = 8) is the capture
  checker's (M0-4). Plan revision M0-C.2 keeps it and re-justifies it:
  with the round-robin drain, two domains that produce lines at once
  alternate on the console at least once per wake in which both rings
  hold a record, and a console-bound hart 0 lowers the wakes, not the
  alternation within a wake.
- **Drain order** (`struct be_mvp_drain`, `src/mvp-hart.{h,c}`; Plan
  revision M0-C.1). `be_mvp_drain_next` names the ring hart 0 visits
  next, domain 0's then domain 1's in turn (domain 0's alone in the probe
  images), and `be_mvp_drain_visited` counts the visit, which takes at
  most one record; the drain ends once the latest visit to each ring took
  nothing (an empty ring, or a held one in `ring-full`), or after each
  ring's capacity in record headers plus one visit per ring, the bound
  the earlier drain of one ring had, which takes every record a ring held
  when the drain began however fast its writer posts more. Invalid
  arguments leave a drain that is over.
- **SBI core** (`src/mvp.h`, `src/mvp-sbi.c`, from B7's). Per-hart state
  and counters (`exits`, the seven call classes, `ipi`, `lines`, and since
  M1-3 `denials`, and since M2-3 `mgmt`), each
  domain's 2^20 exit ceiling, and B7's SBI subset at version 3, unchanged
  but in an image with the management extension, version 4 (M2-3).
  The supervisor software interrupt at V=1 is the IPI (`ACTION_IPI`,
  resumed at the same `sepc`); `be_mvp_ipi_serve` answers each PING with
  one PONG, and an empty inbound ring or any other record fails the hart as
  `ipi`, a malformed inbound or full outbound ring as `ring`. The console
  posts LINE records instead of writing lines: CR dropped, bytes outside
  `0x20`-`0x7e` but LF as `?`, a full 256-byte buffer as its own line, a
  partial line flushed at shutdown and before a FAIL. SRST shutdown with
  reason 0 stops only the calling hart (`ACTION_SHUTDOWN`); reason 1 and
  reboots are terminal. B7's `wfi` and slice classes are gone: with VTW
  clear a guest `wfi` runs natively, so a virtual-instruction exit for one
  is terminal, and so is the supervisor timer at V=1, as are B7's other
  terminal exits. The run budget is hart 0's alone.
- **Denial path** (`src/mvp-sbi.c`, `src/mvp-hartmain.c`, `src/mvp-trap.S`;
  M1 plan, "The denial path", Q4, Q5; M1-3). In an image whose scenario's
  accepted exits name `denial` (`te-poc`, but not its `no-inject` variant),
  a guest-page fault goes to `be_mvp_denial_decide`, a pure function of the
  exit record and the hart's private walked window and channel leaf (since
  M2-3, its root's walked leaves of every declared page, M1's channel leaf
  as page 0), which consults no type, rule, or policy and writes nothing. It accepts exactly
  the plan's entry: cause 20, 21, or 23 from VU mode (`hstatus` SPV 1, SPVP
  0, GVA 1), `htval` below 2^39, `htinst` zero or the transformed load,
  store, or AMO, `vstvec` Direct or Vectored, and a GPA, `(htval << 2) |
  (stval & 3)`, that the root does not map (kind `unmapped`) or, for a
  store, in the channel page (since M2-3, any page) of a leaf without W
  (`read-only`); anything else, a fault from VS mode among it, stays
  terminal. For an accepted
  denial the domain hart counts it (`denials`); writes `vscause` 1, 5, or 7
  (the instruction, load, or store/AMO access fault), `vstval` = `stval`,
  `vsepc` = `sepc`, and `vsstatus` with SPP 0, SPIE the guest's SIE, and SIE
  0, through `be_mvp_arch_inject`, the only writer of the four after arming,
  which reads each back; posts one DENIAL record (twelve words: the sequence
  number from 1, the cause, the kind, the GPA, `htval`, `htinst`, `stval`,
  `sepc`, the guest's `vsstatus` and `vstvec`, the injected `vscause`, and
  the exit's time) and sends hart 0 an IPI; and resumes the guest in VS mode
  at `vstvec`'s base. The path writes no `hgatp`, executes no fence, and
  touches no other hart's block. Hart 0 takes a DENIAL only between its
  domain's ENTERED and SHUTDOWN, in sequence, with its injected cause and a
  kind that fits its GPA against the sealed record (since M2-3, the sealed
  pages), and prints `BE_MVP:DENY` with the exit's ticks and the service
  time, the post's time minus the exit's.
- **Management extension** (`src/mvp.h`, `src/mvp-sbi.c`,
  `src/mvp-hart.{h,c}`, `src/mvp-hartmain.c`, `src/mvp-runtime.c`; M2 plan,
  Q3, Q4, Q14, Q15, "The management extension", "Control loop and failure
  paths"; M2-3, not reviewed). In an image whose scenario's accepted exits
  name `mgmt` (`BE_MVP_SCENARIO_ACCEPT_MGMT`, anchor), an `ecall` from VS
  with EID `0x08004245` is the extension (`probe_extension` 1, version 4):
  FID 0 `pause`, FID 1 `terminate`, `a0` the target, counted in `mgmt`,
  part of `sbi`; any other FID is `SBI_ERR_NOT_SUPPORTED` on the hart,
  counted in `refused`, without a request. Every other image supports
  none of it, as an unknown extension, at version 3. The domain hart posts
  MGMT_REQUEST (its sequence number the `mgmt` count), publishes, sends
  hart 0 one IPI, and waits in HS: it reads its inbound ring only once the
  SSIP helper's readback (one `csrrc` that returns `sip` as it was) shows
  an IPI, answers a PING found meanwhile with a PONG (SPV 0), and takes the
  MGMT_RESULT of its sequence number (0, -3, -4, or -10), which returns in
  `a0` (`a1` 0) through the SRET tail after the `ecall`; with neither the
  answer nor progress on its outbound ring for 2^24 ticks (M1-B's window)
  it fails as `mgmt`. Hart 0 decides each request with
  `be_mvp_mgmt_decide` (pure): a target that is no domain -3; no sealed
  grant from the requester to the target with the function's permission,
  the requester itself included, -4; a target terminated, shut down, or
  pending (a request delivered to it awaits its transition, or its own
  awaits its answer, so a request to oneself is pending), or `pause` of a
  paused one, -10; otherwise delivery, `terminate` of a paused target
  included. A decision is answered at once (MGMT_RESULT and one IPI) and
  logged as `BE_MVP:MGMT ... target_state=-`; a delivery posts PAUSE or
  TERMINATE to the target's inbound ring with one IPI and stays pending,
  hart 0 never blocking, until the target's PAUSED or TERMINATED, when
  hart 0 prints `BE_MVP:12 DOMAIN_PAUSED` or `DOMAIN_TERMINATED` (with the
  measurement when the target is the measured domain, else `-`), answers
  0, and logs the request with `target_state=paused` or `terminated`; a
  target that shuts down first answers it -10 with `target_state=shutdown`.
  The target hart takes PAUSE or TERMINATE on its IPI exit, posts PAUSED or
  TERMINATED (its exits, the requester), and parks in HS with its guest's
  state left in the saved page: paused, it takes only a TERMINATE; any
  other record then, or any record once terminated, fails it as `ipi`.
  The run completes once every domain has shut down or been terminated; a
  paused domain has not ended. The sealed grants (`be_mvp_grants`,
  `.mvp.rodata`) and hart 0's management state (`be_mvp_mgmt_state`, the
  MVP region's BSS) are hart 0's alone: the image checker requires that no
  code the domain-hart entry reaches names them or the measurement, and
  that it never reaches the decision. The `no-grant-check` variant decides
  without the grants (every well-formed request delivered, the state rules
  kept) under a run budget of 2^27 ticks.
- **Firmware surface** (`src/mvp-sbi.h`). The HSM and IPI identifiers and
  the pure checks of their results (`be_mvp_hsm_stopped`,
  `be_mvp_hsm_started`, `be_mvp_ipi_target`), and `BE_MVP:02`'s census of
  the other harts (`be_mvp_hsm_census_init`, `be_mvp_hsm_census_add`;
  Plan revision M0-A.2). M0-3 makes the calls from one out-of-line
  function, `be_mvp_fw_call`, through the accepted `be_r3_arch_sbi_call`,
  the image's one `ecall`.
- **Hart 0's boot** (`src/mvp-runtime.c`, from B7's runtime; plan "Boot
  sequence on hart 0"). The MVP region's check and BSS clear (M0-A.1);
  the accepted R3 prelude through `BE_R3:06`, with B7's calls and
  markers; `BE_MVP:01` with the MVP region and the flat image's size; the
  firmware probe (HSM and IPI through the accepted probe helper, then
  `hart_get_status` for harts 1 to 7, all printed in `BE_MVP:02` with
  `started=<h>` or `started=none`: both domain harts, the run's, must be
  STOPPED, and every other hart STOPPED but for at most one STARTED, the
  start rule's boot hart; a second STARTED hart, a STARTED domain hart,
  any other state, or an error fails as `firmware`; M0-A.2); the Sstc
  probe (`henvcfg` STCE, else `sstc` with `DETAIL henvcfg=`); both MVP
  roots built in the MVP pool, re-walked, and checked disjoint (`:03`,
  with each domain's hart and VMID), or, with a channel, checked to share
  exactly it (M1-3; see the channel page above), or, with pages, checked
  page by page (`:03 PAGE_CHECKED`, M2-2; see the shared pages above); the
  payload checks (`:04`), both windows and the channel page cleared
  (`:05`; with pages, the channel pages cleared and the secret placed,
  M2-2), both windows placed (`:06`), with pages the protected domain
  measured (`:06 MEASURED`, M2-2), and a `fence rw, rw`. Then the barrier:
  each block's state page zeroed and filled (descriptor, first-entry
  frame, walked window and, since M1-3, channel leaf, since M2-3 its
  root's walked leaf of each page, the SBI core's state with the
  domain's exit ceiling and the image's denial entry, and both sides'
  views of both rings), `fence w, w`, and each generation word last (`:07
  region=0x102044000`).
- **The run** (plan "Control loop"). Hart 0's budget helper writes
  `stimecmp` once, now plus 2^32 ticks, sets `sie` SSIE and STIE
  (`sstatus.SIE` stays 0), and names hart 0's stack top in `sscratch`.
  Each domain hart is started at the hart entry with its block in `a1`
  and polled to STARTED within 2^24 ticks (`:08`, else `hart-start` with
  its result and status). Hart 0 then polls both rings, reading `time`,
  until both domains are READY within 2^26 ticks (open item 4: no second
  timer write), and enters the loop: `wfi` until SSIP or STIP, clear SSIP,
  and drain the two rings round-robin (Plan revision M0-C.1): each visit
  acquires a ring's head, takes at most one record, and releases the tail
  before the record is acted on. A LINE is one DBCN write with
  the domain's prefix, the first LINE of a domain sends it one PING (Q4);
  READY, ENTERED, PONG, and SHUTDOWN print `:09`-`:12`; both SHUTDOWNs end
  in `:13`, `:14`, and the accepted SRST; a domain's FAIL prints its FAIL
  and DETAIL lines, acknowledges it (ACK), and ends the run; a STIP wake
  is `run-timeout` with `DETAIL ticks=`.
- **Domain harts** (`src/mvp-hartentry.S`, `src/mvp-hartmain.c`, new).
  The hart entry checks `a1` is a block of the hart region by arithmetic,
  sets `sp` to the block's stack top before any memory access, and calls
  `be_mvp_hart_main`; anything else parks. The hart reads the generation
  word, executes `fence r, r`, checks the block (`be_mvp_block_check`),
  runs the accepted R3 reset with the MVP vector, writes `henvcfg` STCE,
  installs its own root through the accepted install function and
  requires the readback to equal its block's `hgatp`, arms its controls and
  writes the per-domain CSR set once with readback, executes the image's
  one `fence.i`, posts READY and ENTERED, sends hart 0 an IPI, and enters
  the domain through the resume tail. Each exit goes through the SBI core:
  console bytes as LINE records (one IPI per finished line), TIME into
  `vstimecmp`, the IPI (clear SSIP, drain the inbound ring, PONG each
  PING), SRST shutdown (SHUTDOWN, then an HS `wfi` park), and every other
  action a FAIL. A domain hart's FAIL posts its record and one IPI and
  waits for hart 0's ACK, which parks it. Since Plan revision M1-B the
  wait's 2^24-tick window restarts each time hart 0 takes a record from
  the hart's outbound ring, so it measures hart 0's progress, not its
  latency behind the console (`be_mvp_ack_wait_step`; see
  [Plan revision M1-B](#plan-revision-m1-b)). When the window passes with
  neither an ACK nor a record taken, when the ring's tail is malformed, or
  when the ring cannot carry the FAIL (a full ring has failed its view),
  the hart prints its own FAIL and DETAIL lines through DBCN and requests
  SRST (Q10).
- **Vector and resume** (`src/mvp-trap.S`, from B7's). The vector derives
  the saved page from `sscratch` and requires it to be a block's `0x2000`
  offset in the hart region; hart 0's own stack top there means an HS
  exception on hart 0 (its terminal path), anything else halts. Since M1-3
  it also saves the guest's `vsstatus` in the exit record. The resume
  tail checks every guest control (plan "Guest controls"), this hart's
  `sscratch` and `hgatp`, sets SPP from the saved SPVP, restores the frame,
  and executes the one MVP `sret`. The arm helper alone writes the
  per-domain CSRs (`vstimecmp` also the TIME helper, and `vscause`,
  `vstval`, `vsepc`, and `vsstatus` also the injection helper, once per
  accepted denial; M1-3), the budget helper alone `stimecmp`, and the SSIP
  helper alone clears `sip`; VTW is never set.
- **Ring fences and hart 0's writes** (open items 2 and 3). A writer
  executes `fence w, w` before publishing the head; a reader `fence r, r`
  after acquiring it and `fence r, w` before releasing the tail
  (`be_mvp_arch_fence_*`, called by hart 0's `visit` and `ping`, the
  domain hart's `ipi` and `publish`). After the barrier hart 0 writes a
  domain's block only through its own two ring views: the inbound ring's
  bytes and head (`ping`, `domain_failed`) and the outbound ring's tail
  (`visit`, once per record taken since M0-C), which a failed domain hart
  also reads as hart 0's progress (M1-B).
- **Shim** (`shim/mvp-shim.S`, from B3's; Q2). B3's booti wrapper; a hart
  other than 0 prints `BE_MVP_SHIM: boot_hart=0x<h> starting hart 0`,
  calls HSM `hart_start(0, shim entry, FDT)`, and parks in `wfi`, as does
  a failed start. The QEMU-only `shim-rule` variant (`BE_MVP_SHIM_RULE`)
  makes the first hart in start hart 1 at the shim and stop itself, and
  hart 1 stop itself after its start rule, so hart 1 is always the rule's
  hart and every other hart is STOPPED for hart 0's probe. Since M0-A.2,
  `BE_MVP:02` reports a parked boot hart as `started=<h>`; the variant's
  runs print `started=none`, because its rule hart stops itself.
- **Scenario** (`tools/gen-scenario.py`, `scenarios/two-guests/
  scenario.json`, new; Q9). The domains, harts, windows, roots, VMIDs,
  bootargs, guest programs, and expected outcomes (control-hart lines in
  order, per-domain lines, rejected substrings, counters, exit classes,
  the concurrency floors, each variant's outcome, each probe's lines). The
  generator checks it against `src/mvp-layout.h` and the DT tool and
  writes `build/mvp/gen/mvp-scenario.h` and one expectation file per image
  under `build/mvp/gen/expect/`; a scenario change is a build. Its
  self-test runs 29 cases (34 at M0-4; since M1-1, 36 for `two-guests` and
  41 for `te-poc`; since M2-1, 53 for `anchor`, and 54 since M2-5, in the
  evaluator's log `build/mvp-evaluator/record/20261028T013707Z/check.log`).
  `anchor` (v3, M2-1) is generated in `build/mvp/gen/anchor/`, after its
  policy check, from the measured kernel and DTB.
- **The `te-poc` scenario** (`scenarios/te-poc/`, `tools/policy-check.py`,
  `guest/mvp-init.c`; M1 plan, "Scenarios and the harness" and "Guest
  software", Q3; M1-1, M1-4, Plan revision M1-A). Security model v1's
  Instance 2 as a schema-v2 scenario: the policy (`policy.te`), the
  labeling, and a manifest with one channel, on which the offline checker
  runs A1 to A6 and A8 (A7 vacuous) before the generator writes anything,
  writing the authority report and the configuration identity that the image
  checker matches against the linked record. G0 on hart 1 is the writer and
  G1 on hart 2 the reader; each init reads its role from `be.role=`,
  `be.channel=`, and `be.deny=` after `--` in its DTB's `bootargs`. Through
  `/dev/mem` the writer fills the page's bytes `0x8` to `0xfff` with a
  pattern, executes `fence w, w`, and sets the flag at offset 0; the reader
  polls the flag for at most 10 s, executes `fence r, r`, and reads the
  pattern; each prints `MVPINIT 07 CHANNEL` with the pattern's digest. Then
  a forked child of the init (Plan revision M1-A) makes the declared denied
  accesses, each caught by its SIGSEGV handler and printed as `MVPINIT 08
  DENIED`: G0 one load from the page beside the channel page (`0x84001000`,
  unmapped), and G1 one store into the channel page's last doubleword
  (`0x84000ff8`, read-only) and one load from M0's probe GPA `0x90000000`
  (unmapped).
- **The `anchor` scenario** (`scenarios/anchor/`, `tools/policy-check.py`,
  `guest/mvp-init.c`, `guest/mgmt/be-mgmt.c`; M2 plan, "Architecture",
  "Guest software", "Scenarios and the harness", Q8, Q9, Q12; M2-1,
  M2-4). Security model v1's Instance 3 as a schema-v3 scenario: the
  policy (`policy.te`), the labeling (G0 on hart 1 the untrusted host,
  `host_t`; G1 on hart 2 the protected domain, `prot_t`; the pages
  `req_t`, `resp_t`, and `secret_t`), and a manifest with the three pages
  and each domain's rights, the one management grant (domain 0 on domain
  1, `pause` and `terminate`), the public 32-byte test secret, and the
  measured domain, G1. The offline checker runs A1 to A6 and A8 (A7
  vacuous: the domains hold only `pause` and `terminate`) before the
  generator writes anything, and the report carries the grants, the flows,
  and the expected measurement. Each init reads its role from `be.role=`,
  `be.pages=`, and `be.deny=` (see [Guest](#guest)). The host's forked
  child makes four denied accesses: a store into the response page's last
  doubleword (`0x84001ff8`, read-only) and three loads, each unmapped:
  from the secret page (`0x84002000`), from GPA `0x114000000` (the
  protected window's HPA read as a GPA), and from GPA `0x102064000` (the
  MVP region's base, standing for the measurement); the protected
  domain's child one, a store into the request page's last doubleword
  (`0x84000ff8`, read-only). The host sends four requests, each answered
  with an HMAC-SHA-256 keyed by the secret; makes the calls it is not
  granted (`pause 0` and `terminate 0`, on itself, -4; `pause 2`, -3; FID
  7 on 1, -2; and a burst of eight `terminate 0`, -4 each); pauses the
  protected domain (0); sends a fifth request, which goes unanswered;
  terminates it (0); and powers off. The protected domain's two calls,
  `terminate 0` and `pause 0`, are refused (-4); it never powers off.
- **Probe images** (`src/mvp-probe.{h,c}`, `src/mvp-probe-arch.S`,
  `guest/probe-stub.{S,c,lds}`, new; plan "Platform record"). Hart 0's
  prelude and substrate with the probe module in place of the payload and
  the control loop; only domain 0's hart is started, running the VS probe
  stub (B5's guest style) at the kernel's GPA. `probe-platform` prints
  `BE_MVP:PROBE` lines for the HSM status of harts 1 to 7, the `hgatp`
  modes and VMID width (through one more call site of the accepted install
  function), three guest-page faults, 100 IPIs to hart 1 waiting in HS and
  100 at V=1, and 10,000 ordering iterations without and with fences;
  `probe-vmid-distinct` and `probe-vmid-shared` read X under root A,
  switch `hgatp` to root B with no fence (the one raw `hgatp` write, in
  these two images only), and read X again. Each ends with `BE_MVP:14`.
  The probe images link no LINE, PONG, or SHUTDOWN path.
- **Negative variants** (plan "Platform record: negative images"). One
  compile-time switch each for `exit-budget` (ceiling 64), `run-timeout`
  (2^20 ticks), `ring-full` (1 KiB outbound rings, and hart 0 waits
  `0x2000000` ticks after both domains' ENTERED before its first LINE
  drain; M0-A.3), and `hart-start` (domain 1 on hart 9); the boot image's
  kernel for `payload` (`magic2` altered), its DTBs for `init-exit`,
  `rdcycle`, and `sbi-time`, and its shim for `shim-rule`; `no-sstc` and
  `sbi-3.0` run the scenario image under another QEMU CPU or firmware.
  Every variant is built for both toolchains, beyond the plan's GCC rows.
  M1-3 adds te-poc's two, each a monitor of its own, run in QEMU and on the
  board: `reader-write`, whose root builder writes W and D into the
  reader's channel leaf, which the channel check refuses (`BE_MVP:FAIL
  gstage`), and `no-inject`, without the denial entry, so that the first
  denial is terminal (`BE_MVP:FAIL guest-page-fault`). M2-2 and M2-3 add
  anchor's four, each a monitor of its own, run in QEMU for both
  toolchains: `secret-shared`, whose page builder also maps the secret
  page into the host's root, and `response-writable`, whose page builder
  writes W and D into the host's response leaf, both refused by the page
  check (`BE_MVP:FAIL gstage`, with the walked and declared leaves);
  `wrong-measurement`, whose expected measurement differs in one bit
  (`BE_MVP:FAIL measurement`, before any domain hart starts); and
  `no-grant-check`, whose hart 0 decides without the grants, so that the
  protected domain's `terminate 0` ends the host, under a run budget of
  2^27 ticks (`BE_MVP:FAIL run-timeout`). The last two are also the
  board's (GCC; M2 plan, Q11). M2-1's two build-time negatives,
  `grant-without-rule` and `secret-flow`, stop at the offline check and
  build no image.

| Path | Role | Package |
| --- | --- | --- |
| `tools/port.py` | The counted port: B7's five rules and seven more, the hart region and the MVP region's six (M0-A.1); `mvp-sha256.o` in the MVP region (M2-2) | M0-1, M2-2 |
| `src/mvp-layout.h` | The layout: the flat image and the accepted image in it, pool, hart region and blocks, MVP region, harts, windows, VMIDs, run limits, waits, SBI identity; the channel page and each root's level-0 page (M1-2); the three shared pages (M2-2) | M0-1, M1-2, M2-2 |
| `src/mvp-gstage.{h,c}`, `src/mvp-payload.{h,c}` | B7's G-stage and payload checks with a hart per root, the hart region, and the MVP region; the channel leaf, its walk, and the channel check (M1-2); the staged image off the channel page (M1-3); the page records, their build, walk, and check, the two builder variants, and the staged image off the shared pages (M2-2) | M0-1, M1-2, M1-3, M2-2 |
| `guest/`, `guest.mk`, `tools/{build-guest.sh,gen-dts.py,gen-payload.py,guest-pins.py,guest-reference-check.py,run-reference-boot.sh}` | Guest inputs, pins, reference boots, and the repeat build; the init's role arguments and te-poc's DTBs (M1-1, M1-3); the MVP's Kconfig fragment with the `.config` delta check, the init's roles, and its forked child (M1-4, M1-A); anchor's DTBs (M2-1); the management module (`guest/mgmt/`, `guest/be/types.h`), `CONFIG_MODULES=y` and its `.config` delta, the init's `host` and `prot` roles, and the module in the pins (M2-4) | M0-1, M1-1, M1-3, M1-4, M2-1, M2-4 |
| `tools/make-control.py` | The Make controls (S1 H33); `MVP_SCENARIO_NAME` and `SCENARIO` (M1-1, M1-5) | M0-1, M1-1, M1-5 |
| `tools/lock/` | The tool lock, its tool, and the evaluator's closure; the closure's RPM digests, the host-only roles, and schema v2 (M0-B.1, M0-B.4); refreshed under direction for host updates (`804fa95f`; on `l1` for M0-6) | M0-1, M0-B |
| `tools/evaluator/` | The clean evaluator's Containerfile and runner; the closure fetcher and the build from its verified cache with repositories disabled (M0-B.2, M0-B.3) | M0-1, M0-B |
| `mvp`, `Makefile` | The wrapper and the build graph; M1's two scenarios, `policy-negatives`, the deny test, the te-poc images and variants, and the host tests' new pinned counts, and the wrapper's `SCENARIO` and reset settings; anchor's scenario with its measured inputs, its two policy negatives, and anchor's DTBs in the payload test (M2-1); the SHA-256 objects and test, the anchor images, and their page and measurement variants (M2-2); the `no-grant-check` image and the host tests' counts (M2-3); the wrapper's `SCENARIO=anchor` (M2-5) | M0-1, M1-1 to M1-5, M1-B, M2-1 to M2-3, M2-5 |
| `src/mvp-ring.{h,c}` | The rings (new); the writer's reads of the reader's tail and of its own published head (M1-B) | M0-2, M1-B |
| `src/mvp-sha256.{h,c}` | SHA-256 (FIPS 180-4), incremental and one-shot, and HMAC-SHA-256 (RFC 2104) in restricted C (new) | M2-2 |
| `src/mvp-hart.{h,c}` | Blocks, the state page, the control loop, the drain order (M0-C.1), the overlap (new); the DENIAL step and SHUTDOWN's denial count (M1-3); the DENIAL step against the sealed pages, the management requests, their decisions and pending state, PAUSED and TERMINATED, and the completion rule (M2-3) | M0-2, M0-C, M1-3, M2-3 |
| `src/mvp.h`, `src/mvp-sbi.c`, `src/mvp-sbi.h` | The SBI core with the IPI and LINE records; the firmware surface; the denial decision, the injected values, and DENIAL (M1-3); the ACK wait (M1-B); the `measurement` class and the management permission bits (M2-2); the management extension's records, dispatch, `mgmt` count and class, version 4, decision (`be_mvp_mgmt_decide`), waits, and the denial decision over every page's leaf (M2-3) | M0-2, M1-3, M1-B, M2-2, M2-3 |
| `tests/{ring,hart,sbi,gstage,payload,deny,sha256}-test.c` | Host tests; the drain order's (M0-C.1); the channel's (M1-2); the denials' and the deny test (new) (M1-3); the ACK wait's and the ring's new reads (M1-B); the pages' and the SHA-256 test (new) (M2-2); the management extension's and the denial path's pages (M2-3) | M0-2, M0-C, M1-2, M1-3, M1-B, M2-2, M2-3 |
| `src/mvp-runtime.c`, `src/mvp-platform.h`, `src/mvp-trap.S` | Hart 0's runtime, the privileged boundary, the vector, resume tail, and helpers (from B7's); the round-robin drain (M0-C.1); the channel check and clear, the DENY lines, the denial switch, and the injection helper (M1-3); the pages' check and clear, the secret, and the measurement (M2-2); each block's page leaves, the sealed grants and management state, the requests' answers and deliveries, the `MGMT` and `:12` transition lines, and the SSIP helper's `sip` readback (M2-3) | M0-3, M0-C, M1-3, M2-2, M2-3 |
| `src/mvp-hartentry.S`, `src/mvp-hartmain.c` | The hart entry and the domain harts' runtime (new); the denial executor (M1-3); the ACK wait (M1-B); the management call's request and wait, and the paused and terminated parks (M2-3) | M0-3, M1-3, M1-B, M2-3 |
| `src/mvp-boot.lds`, `src/mvp-guest-payload.S`, `shim/mvp-shim.S` | The boot image: link, payload, and shim with the start rule (from B7's and B3's) | M0-3 |
| `scenarios/two-guests/scenario.json`, `tools/gen-scenario.py` | The scenario and its generator (new); schema v2 and the policy check first (M1-1); schema v3 and `anchor` (M2-1); in v3 expectations the host's exact `refused` in its `DOMAIN_SHUTDOWN` line and the module's kernel line in each domain's lines (M2-5) | M0-3, M1-1, M2-1, M2-5 |
| `scenarios/te-poc/`, `tools/policy-check.py` | The te-poc scenario, its policy and build-time negatives, and the offline checker with its authority report (new); v3 scenarios (the pages with each domain's rights, the management grants, the secret, and the measurement's inputs), the `domain` class in A2, A3, A7, and A8, the expected measurement in the report when given the measured kernel and DTB, and Instance 3's self-test cases and mutations (M2-1) | M1-1, M2-1 |
| `scenarios/anchor/` | The anchor scenario (new): Instance 3's policy, its labeling, and a v3 manifest with the three pages (the request and response channels, each with its writer and reader, and the secret page) and each domain's rights, the management grant from domain 0 to domain 1, the 32-byte secret, and the measurement's domain and inputs; its two build-time negatives | M2-1 |
| `src/mvp-probe.{h,c}`, `src/mvp-probe-arch.S`, `guest/probe-stub.{S,c,lds}` | The probe module and the VS probe stub (new); the SSIP helper's returned `sip` ignored (M2-3) | M0-3, M2-3 |
| `tests/check-image.py` | The image checker and its mutation test (from B7's); the injection helper, the linked channel record and identity, and the te-poc images (M1-3); the linked pages, the secret and the measurement's sections, the shared pages, and the anchor images (M2-2); the domain-hart reach rule, the sealed grants and management state, no channel record with pages, the SSIP helper's readback, and `no-grant-check` (M2-3) | M0-3, M1-3, M2-2, M2-3 |
| `tools/budgets.py` | The budgets (new) | M0-3 |
| `tests/run-qemu.sh` | The eight-hart QEMU driver (from B7's): provisional at M0-3, each attempt judged by the capture checker and a REFUSED attempt made again at M0-4; te-poc's runs and variants (M1-4); anchor's runs and four runtime negatives with the measured inputs (M2-5) | M0-3, M0-4, M1-4, M2-5 |
| `tests/check-capture.py`, `tests/fixtures/` | The capture checker, its self-test and mutations, and its fixtures (new); the regenerated fixtures and the board's stop-6 capture (M0-C.2); schema-v2 expectations, the denials, the channel, the report, and M1's fixtures (M1-4, M1-5, M1-B); schema-v3 expectations, the pages, the measurement, the requests' HMACs, the management log, the transitions and their order, M2's fixtures, and M1's judged against M1's pins (M2-5) | M0-4, M0-C, M1-4, M1-5, M1-B, M2-5 |
| `tests/kexec-rehearsal.sh`, `tests/kexec-rehearsal/init.c` | The eight-hart kexec rehearsal (from B7's); te-poc's image with its report (M1-4); anchor's with its report and measured inputs (M2-5) | M0-4, M1-4, M2-5 |
| `tools/kexec-load.py`, `tools/k3-{preflight,run,campaign}.sh`, `tests/test-kexec-load.py`, `tests/fake-board.py`, `tests/run-tool-dry-run.sh` | The board tools with the layout rule, the loader's test, and the dry run (from B7's); the dry run's `same-second` case (after M0-C's review) and its platform-record checks and `tree-state` and `probe-record` cases (M0-6); the remote reset, the te-poc selector, the channel page, the firmware identity, the pause, and their cases (M1-5); the platform record's M1 checks (M1-6); the shared pages in the layout rule and its test (M2-2); `SCENARIO=anchor` and its variants, a v3 expectation's measured inputs, the loader test's purgatory search before the payload, and the anchor cases (M2-5) | M0-4, M0-6, M1-5, M1-6, M2-2, M2-5 |
| `tools/k3ctl.sha256`, `tests/fake-k3ctl.py` | The `k3ctl` client's pin and the dry run's fake dongle (new) | M1-5 |
| `tools/evidence.py` | The evidence bundle, the board record, and the image comparison (new); the platform record in every board record, and the manifest written again to cover it, and the board record's tree state read before its load-check staging directory exists (M0-6); te-poc in the bundle (M1-4); the resets, the policy records, and the serial-log note in the board record (M1-5); anchor's images, variants, DTBs, and module in the identity set, its scenario, report, and policy records, and the board record's measured inputs and anchor excerpts (M2-5) | M0-4, M0-6, M1-4, M1-5, M2-5 |
| `tools/platform-record.py` | The platform record of a board record (new; plan, "Platform record"); M1's Resets and Serial log (M1-5); M1's Preflight beside M0's record, te-poc runs, Denials on K3, The channel, and the other runs' failure lines (M1-6); the shared pages' region line (M2-2); M2's sections: anchor runs, the pages, the measurement, management requests, paused and terminated, and requests and responses (M2-5) | M0-6, M1-5, M1-6, M2-2, M2-5 |
| `results/20261025-com260/` | M0-5's second campaign's board record, with its platform record, made against the M0-6 content and committed after it | M0-6 |
| `results/20261027-com260-m1b/` | M1-5's second campaign's board record, with its platform record, made against the M1-6 content and committed after it | M1-6 |
| `tools.mk` | The harness, rehearsal, board, and evidence targets (from B7's); te-poc's board images and variants (M1-3), its checks (M1-4), `SCENARIO`, and the remote reset (M1-5); anchor's board scenario and its two board variants (M2-1); the shared pages in the board's layout comment (M2-2); anchor's board images, selectors, and variants, and its report and measured inputs in the harness and board targets (M2-5) | M0-4, M1-3, M1-4, M1-5, M2-1, M2-2, M2-5 |

## Plan revision M0-A

Plan revision M0-A (`planning/mvp-m0-plan.md`, appended section),
directed by the responsible human on 2026-10-23 after M0-3 reported stop
condition 3 and open items 9 and 10, changes the plan in five bounded
places. Its implementation:

- **M0-A.1, the MVP region** (`65454598`). Six more counted port rules
  (below) add the region's three PT_LOAD entries, exclude the MVP layer's
  C objects from the accepted `.monitor.text`, `.monitor.rodata`, and
  `.monitor.data` input patterns, and place exactly those objects'
  sections in `.mvp.text`, `.mvp.rodata`, and `.mvp.data` at
  `0x1_0206_4000`. Each exclusion puts one `EXCLUDE_FILE` before each
  section pattern, the one form GNU ld and lld were found to read alike:
  GNU ld applies an `EXCLUDE_FILE` inside the parentheses to the next
  pattern only and lld to every pattern up to the next `EXCLUDE_FILE`, and
  lld 22 silently ignores the form before the file pattern. The image
  checker requires the result for both toolchains: every MVP C object's
  sections inside the region by symbol and by link map, none in the
  accepted extents. `src/mvp-layout.h` renames the accepted image's
  `0x34000` bytes `BE_MVP_ACCEPTED_IMAGE_BYTES` (the pool still begins at
  the monitor plus `0x34000`) and adds the region (`0x102064000`,
  `0x40000`), the flat image (`0xa4000`), and Fedora's kernel address
  (`0x102200000`), with static assertions: the region starts at the hart
  region's end, ends at the flat image's end, at most `0x1_020a_4000`,
  below Fedora's kernel and the staged image, 16 KiB aligned. The flat
  image is `objcopy -O binary --pad-to=0x1020a4000`, exactly `0xa4000`
  bytes, with the NOLOAD pool and hart region as zeros; the boot image's
  payload is that image, its kernel moves to offset `0xa5000` and its
  DTBs follow (the 4 MiB limit holds, at `0x223000`); the shim's
  descriptor and `bytes=` line follow the payload's size symbol
  unchanged. Hart 0 checks the linked region against the layout and
  zeroes its BSS (`clear_mvp_bss`) before it uses any MVP static, since
  the accepted entry clears only `__be_bss_start` to `__be_bss_end`; it
  does so first, so any hart that later touches that BSS (in the probe
  images, hart 1 after the barrier) finds it zeroed. `BE_MVP:01` gains
  `mvp_region=0x102064000 mvp_bytes=0x40000 image_bytes=0xa4000` from the
  layout constants. With the C gone, both toolchains' monitors fit, and
  `IMAGE_TOOLCHAINS` and the variants cover GCC and Clang.
- **The first `0x34000` bytes** (compared with M0-3's GCC image, rebuilt from
  `30c5e1a8`, whose flat image is the one M0-3 recorded, SHA-256 `1bd94ed8...`).
  Every accepted section keeps its address but `.monitor.data`, which follows
  `.monitor.rodata` and is now empty (`0x1_0200_8750` instead of
  `0x1_0200_9470`); 89 symbols keep their addresses, every symbol of the
  accepted core among them, and only the MVP assembly, B1's handoff, and the
  markers `__be_monitor_code_end`, `__be_bss_start`, and `__be_bss_end` move
  (22); every accepted `ASSERT` holds. `.monitor.text` now holds the accepted
  code, B1's handoff, and the MVP assembly (the vector, the resume tail and
  helpers, and the hart entry; in the VMID probe images also the raw `hgatp`
  switch), which moved down to where the MVP C began, so it ends at
  `0x1_0200_4540` (GCC) or `0x1_0200_4770` (Clang) instead of `0x1_0200_7fe0`
  (GCC). `.monitor.rodata` keeps only the accepted constants (and, in the VMID
  probe images, the VS stub's bytes, which `mvp-probe-arch.o` carries);
  `.monitor.data` holds nothing, so `__be_bss_start` equals `__be_bss_end` and
  the accepted BSS clear does nothing (open item 17). The flat image's first
  `0x34000` bytes differ only below `0x1_0200_8000` (15,207 bytes: the MVP C
  gone, the MVP assembly and B1's handoff moved down) and from there to
  `0x1_0200_f000` (2,568 bytes: the MVP constants and data gone); the NOLOAD
  pages and the two fixture pages are byte-identical.
- **M0-A.2, the boot-hart rule** (`106062f6`). `BE_MVP:02` takes a census
  of harts 1 to 7 (`be_mvp_hsm_census_*` in the SBI core): the run's
  domain harts must be STOPPED, and every other hart STOPPED but for at
  most one STARTED hart, printed as `started=<h>` (`started=none`
  otherwise). A second STARTED hart, a STARTED domain hart, any other
  state, or an error fails as `firmware`. The host test covers every boot
  hart, every second STARTED hart, every other state and error, the
  `hart-start` variant's absent hart, and a one-domain run. The board
  shim is unchanged, and the QEMU driver makes each run once.
- **M0-A.3, the `ring-full` variant** (`ebae089d`). One more switch in
  hart 0's control loop only: after a domain's ENTERED, hart 0 drains
  nothing more of that domain until it has seen both ENTERED records,
  then busy-waits `0x2000000` ticks once before its first LINE drain
  (`BE_MVP_VARIANT_DRAIN_DELAY_TICKS`, asserted beyond the `2^24`-tick
  acknowledgement wait). The domain harts' code is unchanged.
- **M0-A.4, the erratum.** `BE_MVP:07` prints `region=0x102044000` in
  every run (see [Results](#results-this-host)); the plan's
  text is not edited, and open item 1 is closed by M0-A.4.
- **M0-A.5, the claim ledger.** See [Non-claims](#non-claims).

## Plan revision M0-B

Plan revision M0-B (`planning/mvp-m0-plan.md`, appended section), directed
by the responsible human on 2026-10-24 after M0-4's evaluator stopped at
stop condition 11 (open item 7), changes only the plan's "Tool lock and
the clean evaluator". Offered three remedies, the responsible human
answered `accept A`: "keep the closure NEVRAs, add a SHA-256 per RPM,
fetch the exact closure once from the repos/koji into a verified local
cache, build with repos disabled, explicit swap of the base's standalone
sysusers, and record podman/ssh/scp as host-only lock roles" (B was a lock
refresh from the host now; C was to defer). Its implementation:

- **M0-B.1, a SHA-256 for each closure RPM** (`b364fe92`). Each of the
  closure's 257 unchanged NEVRAs now carries the SHA-256 of its RPM file
  as Fedora built and signed it (`<NEVRA> <SHA-256>`; schema
  `be-mvp-tool-lock-v2`). `tools/evaluator/fetch-closure.py --record`
  derived them once, from files verified two ways. First, a good header
  signature by the Fedora 44 key that the host's `fedora-gpg-keys`
  installs (`/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-44-primary`, fingerprint
  `36f612dcf27f7d1a48a835e4dbfcf71c6d9f90a6`, the file's packaged SHA-256
  checked), from `rpmkeys --checksig` against a temporary keyring that
  holds that key alone. rpmkeys passes an unsigned RPM as `digests OK`,
  so the check requires the header signature line by that fingerprint,
  every line `OK`, and the summary `digests signatures OK`; rpmkeys also
  checks the file's header and payload digests. Second, the main header's
  SHA-256, computed from the file's bytes and read by
  `rpm -qp --qf '%{SHA256HEADER}'`, equal to the installed package's
  `rpm -q --qf '%{SHA256HEADER}'`, for the 254 closure packages this host
  has; B3's m4, bison, and flex, which it lacks, must instead equal B3's
  SHA-256 pins (`bringup/k3-b3/tests/build-uboot.sh`). `tool-lock.py`'s
  `bind_closure()` then wrote the digests and re-bound
  `MVP_CLOSURE_SHA256`, changing no other lock line. `refresh` keeps the
  digest of each NEVRA it keeps and leaves a new NEVRA's pending, which
  `check` refuses until `--record` derives it.
- **M0-B.2, the verified cache** (`b364fe92`). `fetch-closure.py` puts
  every closure RPM, by exact NEVRA, in a cache of exact RPMs
  (`build/mvp-evaluator/rpms`, each file named
  `<name>-<version>-<release>.<arch>.rpm`, without the epoch). A file that
  verifies is kept; a missing one comes from `MVP_RPM_CACHE` if it is set
  (as for `tools/build-guest.sh`), then from Fedora's `fedora` and
  `updates` repositories by an unprivileged `dnf download`, then (since
  debt sweep 5, 2026-11-01; item 95) from Fedora's updates archive
  (`fedoraproject-updates-archive.fedoraproject.org/fedora/44/x86_64/`,
  one flat directory per release and base architecture, the `noarch`
  files with the rest, file names fully percent-encoded), which keeps
  every update build pushed to stable after the `updates` repository has
  replaced it, then from koji's copy signed with the Fedora 44 key
  (`data/signed/6d9f90a6/<arch>/`; open item 28), which koji prunes. The
  closure must be the one the lock binds, a file enters the cache only if
  its SHA-256 is the closure's, `SOURCES.tsv` records each file's source,
  and a mismatch or a package in no source fails closed. `evaluate.sh`
  runs it before every build; with the base image's pull it is the
  evaluator's only network use. Its offline self-test (48 cases, run by
  `tool-lock-check`) covers NEVRA parsing with epochs and `noarch`, the
  koji and archive URLs, the source order, the HTTPS sources with curl
  faked, the header digest on synthetic files, a corrupted byte from a
  source and in the cache, a package in no source, and, with rpmkeys and
  rpm mocked, an unsigned file, a missing or another key, a bad digest
  line, a header digest that is not the installed package's, and a B3
  pin mismatch.
- **M0-B.3, the image from the cache** (`67731e4c`). The Containerfile
  checks every cached RPM's SHA-256 against the closure, then installs
  the 257 local files in one `dnf5 do` transaction with every repository
  disabled, weak dependencies off, and `clean_requirements_on_remove`
  off, which removes five base packages by name: the plan's swap,
  `systemd-standalone-sysusers` for the closure's
  `systemd-sysusers-259.10-1.fc44`, and four packages that require exact
  versions the closure replaces (open item 27; the table is under
  [The clean evaluator](#the-clean-evaluator)). No downgrade is needed,
  and no `--allowerasing`, `--skip-unavailable`, `--skip-broken`,
  `--nobest`, or other erasure is used. Every closure NEVRA must then be
  installed exactly; `rpm -qa` and the removals are recorded in the image.
  The reproducibility wording is now "digest-pinned base plus recorded
  closure with per-RPM digests" (S1 H32).
- **M0-B.4, host-only roles** (`83916b5a`). `podman`, `ssh`, and `scp`
  are lock roles with full records, listed in
  `MVP_TOOL_HOST_ONLY_ROLES`. `tool-lock check` verifies all 29 on the
  host and skips the three inside the evaluator, which it recognizes by
  `/etc/mvp-evaluator-rpms.txt`, the image's recorded package list, and
  only if that list names exactly the installed packages; no environment
  variable can claim it. Their packages are not closure roots, so
  podman's stay out (`openssh-clients` was already in the closure; open
  item 29). The self-test (46 cases) checks a missing host-only role
  outside the evaluator (refused) and inside it (skipped), with the
  markers in the build tree, never `/etc`.

## Plan revision M0-C

Plan revision M0-C (`planning/mvp-m0-plan.md`, appended section, at
`260ceba6`) was directed by the responsible human on 2026-10-25 after the
first GCC scenario run of the M0-5 board campaign (`20261025T022152Z`,
host kernel 7.3.0-65.1) failed the capture checker on one finding,
`5 alternations between the domains' lines, fewer than K = 8 (Q5)`, and
the campaign stopped (stop condition 6). Offered a monitor fix (A), a
checker-only change (B), and a stop (C), the responsible human directed
`proceed with A`. The run had otherwise passed: both domains ran to
`BE_MVP:14` with `exits=157`, `ipi=1`, and `srst=1` each, overlapping for
`0x25403a9` of the shorter run's `0x2563c63` ticks; hart 0's `BE_MVP:13`
said `records=138 wakes=3`, and the domains' lines came in six batches
of 41, 57, 20, 4, 4, and 4 lines. The plan finds the cause in hart 0's
drain: it took every record a ring held, printing each LINE through the
firmware console before it took the next, so behind the 115200-baud
console it printed batches, and the alternation count measured the
batching, not the guests' concurrency, which the passing ticks-based
overlap does measure. Its implementation:

- **M0-C.1, the round-robin drain** (`129626e0`). `drain()` in
  `src/mvp-runtime.c` visits domain 0's ring, then domain 1's, and again,
  until a visit to each ring in turn takes nothing; the order and its bound
  are `be_mvp_drain_begin`, `be_mvp_drain_next`, and `be_mvp_drain_visited`
  (`src/mvp-hart.c`, pure C, host-tested). A visit (`visit()`) keeps the
  reader's protocol around its one take: acquire the head, `fence r, r`,
  take, `fence r, w`, release the tail; then `step()` acts on hart 0's copy
  of the record exactly as before, so the ring's bytes are free before the
  console prints the line (open item 34). An acquire that fails on a failed
  view, or a take that is neither a record nor empty, is `FAIL ring`, as
  before. The bound is each ring's capacity in record headers plus one
  visit per ring (4,098 visits for the two 32 KiB rings, 130 for
  `ring-full`'s 1 KiB rings), the bound the earlier drain of one ring had:
  every record a ring held when the drain began is taken, however fast its
  writer posts more, and a record the bound leaves was posted after hart 0
  cleared SSIP, as were the records the earlier drain left behind its
  acquired head. The READY wait, the control loop, and the probe images'
  poll all drain this way; the probe images visit domain 0's ring alone, as
  they drained it alone before. The `ring-full` hold (M0-A.3) is checked
  before each visit, as it was before each take, and a held ring's visit
  takes nothing. `records`, `wakes`, `lines`, `ring_peak`, and every marker
  keep their meanings. `tests/hart-test.c` drives the order on host rings
  as the runtime does: two rings of 0 to 8 records each (81 cases: one take
  from each in turn while both hold one, then the rest of the longer, and
  the end at the first visit after which each ring's latest visit took
  nothing), one ring alone, a held ring released by a later drain, a writer
  as fast as hart 0 on one ring, the bound for the smallest ring and each
  layout ring with both rings kept full, and refused arguments: 652
  scenarios and 140,687 assertions (563 and 67,887 before), GCC = Clang.
  Five single changes to the order (a drain that ends at the first empty
  ring, a bound without its extra visit, no turn-taking, an idle count that
  never resets, a third ring admitted) each fail it. The MVP region's text
  grows by `0xb0` bytes (GCC) and `0xc0` (Clang) in the scenario images;
  the accepted code extent and every other budget are unchanged (see
  [Budgets (measured)](#budgets-measured)).
- **M0-C.2, the floor** (`c5ecedee`). K = 8 keeps its value and
  definition in `scenarios/two-guests/scenario.json`,
  `tools/gen-scenario.py`, the generated expectation, and
  `tests/check-capture.py`, whose docstring now gives M0-C.2's
  justification. The six fixtures whose content the drain order changes
  are fresh QEMU captures of the M0-C images, and the five that stop
  before any drain or drain one ring are kept (the table under
  [Harness](#harness-m0-4)). The named mutations take the new two-guests
  capture's values (G0's timestamps, `overlap_ticks`, `ring_peak`, and
  `:10` ticks), and the `ring-full` mutation that puts a `BE_MVP:11`
  before the fallback now follows the second `BE_MVP:10`, whichever
  hart's it is, since the round-robin order of the two entries depends on
  timing; all 154 mutations are rejected for their own reasons. The
  board's capture, CRs removed, is the new fixture
  `k3-two-guests-gcc-stop6-alternations.log`, which the self-test
  requires to FAIL in kexec mode with the alternation finding alone and
  `records=138 wakes=3`: 36 cases, 34 before.
- **M0-C.3, the checks** (see
  [Results](#plan-revision-m0-c-at-c5ecedee-2026-10-25)). At `c5ecedee`
  the kexec rehearsal and every stage of `check` after the tool lock
  pass; the tool lock does not, on host drift that M0-C did not cause
  (open item 33), so `check` and the evaluator wait on the responsible
  human. The board campaign restarts from the two load checks with the
  M0-C images (the probe images share the drain code and are rebuilt),
  then the three probe runs, three GCC and one Clang scenario runs, and
  the `payload` run, with a human reset after each; the preflight stands.
  The stopped run's record (`build/mvp/k3-campaigns/20261024-com260/`,
  run `20261025T022152Z`, whose `serial.log` has SHA-256
  `bd1842f5dbfb24725934816ecbfbab850340769510ac28092caad171e6767e02`) is
  stop-6 evidence, not a scenario result.

**Counts before and after.** QEMU cannot show the change: there hart 0
wakes nearly once per record (87 to 132 wakes for 138 records in the runs
below), so the old and the new order print alike, and the two images'
alternation counts overlap. The six-run rows were made outside the suite
for this comparison, the old images rebuilt from `260ceba6` byte for
byte:

| Run | Alternations | Wakes |
| --- | --- | --- |
| Board, GCC, old image `bd2841567c78`, the stopped run | 5 | 3 |
| QEMU `k3-like`, GCC, old image, 6 runs | 60, 63, 69, 83, 84, 88 | 111 to 129 |
| QEMU `k3-like`, Clang, old image, 6 runs | 56, 66, 67, 77, 77, 98 | 112 to 120 |
| QEMU `k3-like`, GCC, M0-C image, 6 runs | 51, 52, 56, 72, 84, 89 | 114 to 132 |
| QEMU `k3-like`, Clang, M0-C image, 6 runs | 58, 63, 68, 71, 72, 83 | 109 to 131 |
| QEMU suite before M0-C (old images), `k3-like` GCC, Clang | 94, 94 | 112, 115 |
| QEMU suite at `c5ecedee`, `k3-like` GCC, Clang | 101, 87 | 110, 114 |
| Kexec rehearsal at `c5ecedee`, GCC, Clang | 87, 77 | 87, 103 |
| QEMU suite at `804fa95f`, `k3-like` GCC, Clang | 78, 102 | 112, 112 |
| Board, M0-C images, the second campaign's three GCC and one Clang scenario runs | 125, 125, 125, 125 | 2, 2, 2, 2 |

The order itself is covered by the host test; M0-C.2's justification is
checked by the board's re-run, the last row (see
[M0-5's second board campaign](#m0-5s-second-board-campaign-2026-10-25-and-26)):
behind the same console, hart 0 woke twice for the 138 records, and the
domains' 130 lines alternated 125 times, where the old drain's 3 wakes
gave 5. The plan's list of what M0-C does not change holds: the
hart layout, the hart region, the rings' format and sizes, the IPIs, the
boot sequence, the markers, Q5's floors, the guest SBI and firmware
surfaces, the tool lock, the evaluator, the board procedure, the work
packages, and stop conditions 1 to 12.

## Plan revision M1-B

Plan revision M1-B (`planning/mvp-m1-plan.md`, appended section, after
Plan revision M1-A) was directed by the responsible human on 2026-10-27
after work package M1-5's first board campaign
(`build/mvp/k3-campaigns/20261027-com260/`) stopped at stop condition 6
in its `no-inject` run, `20261027T094024Z` (GCC), the preflight, both load
checks, three GCC and one Clang `te-poc` runs, and the `reader-write` run
having passed. Offered a wider `no-inject` expectation (A), a change to
M0's failure path so that only hart 0 prints (B), and dropping
`no-inject` from the board campaign (C), the responsible human directed
`accept B, proceed`. After both `BE_MVP:10` lines hart 0 printed 89 guest
lines (7,660 bytes on the wire: 7,482 of text, each line ended by the
firmware console's CR and LF; 7,571 in the fixture, CRs removed), then
`BE_MVP:FAIL guest-page-fault`, a `BE_MVP_G1:` line, a second
`BE_MVP:FAIL guest-page-fault`, domain 0's `BE_MVP:DETAIL` (hart 1, cause
`0x15`, `htval=0x21000400`, `htinst=0x3303`, `exits=94`), a `BE_MVP_G0:`
line, and domain 1's (hart 2, cause `0x17`, `htval=0x210003fe`,
`htinst=0x3023`, `exits=94`); then nothing. Both guests had reached their
first denied access, each the declared one. Only hart 0 prints prefixed
guest lines, so it was still draining when the four lines were printed,
and its own terminal path, which prints its FAIL and DETAIL back to back,
is not in the log: both domain harts took Q10's fallback path, and a
domain hart's SRST ended the run before hart 0 took either FAIL record.
The plan finds the cause in the window: M0's Q10 measured hart 0's
latency, 2^24 ticks (0.699 s at 24 MHz) from the FAIL's post, while hart
0, draining one record per domain per pass (M0-C.1) through the
115200-baud console (11,520 bytes a second), needed about 0.66 s for the
guest lines queued ahead of the FAIL records. In QEMU the console is
immediate and the ACK follows the FAIL within microseconds. Its
implementation:

- **M1-B.1, the wait restarts on hart 0's progress.** The decision is
  a pure function in the SBI core, as the denial decision (M1-3) and the
  drain order (M0-C.1) are: `be_mvp_ack_wait_start` and
  `be_mvp_ack_wait_step` (`src/mvp.h`, `src/mvp-sbi.c`), over a record of
  the window's start and the tail last seen (`struct be_mvp_ack_wait`).
  Given the time, the outbound ring's tail and published head, and
  whether the ACK is in the inbound ring, a step answers, in this order:
  an ACK parks the hart; a tail behind the one last seen, or beyond the
  published head, falls back at once; a tail past the one last seen is
  hart 0's progress, and restarts the window; a window of
  `BE_MVP_FAIL_ACK_TICKS` (`0x1000000`, unchanged) or more, the time's
  difference taken modulo 2^64 so that the time CSR's wrap is measured as
  any other, falls back; anything else waits. A step without a record
  falls back. The ring API gains the two reads the decision needs:
  `be_mvp_ring_taken`, the reader's tail as a writer view reads it, and
  `be_mvp_ring_published`, the head the writer view published; each
  reads 0 for an absent, failed, or reader's view, which never reads as
  progress. In `hart_fail()` (`src/mvp-hartmain.c`) the wait starts once
  the FAIL is published and hart 0 told, and each turn of its loop reads
  the ACK, then the time, the tail, and the head, and parks, waits, or
  falls back as the step answers. The flush, the post, the publish, the
  IPI, the fallback lines, the SRST request, the park, and the immediate
  fallback for a ring that cannot carry the FAIL (the `ring-full`
  variant, M0-A.3) are unchanged. The waiting hart publishes nothing, so
  its head is fixed and the tail can restart the window only until it
  reaches it: the wait ends. A healthy hart 0 takes a record from a ring
  that holds one at least once per drain pass, and a pass prints at most
  one line for each domain, about 0.05 s at 115200 baud; only a tail
  still for 2^24 ticks, a wedged hart 0's, leaves the hart printing its
  own lines, the risk Q10 names.
- **M1-B.2, hart 0 unchanged.** Hart 0's control loop, its drain order
  and bound, its terminal path, and its ACK are unchanged: it still ends
  the run on the first FAIL record it takes. Another failed domain's hart
  then prints its own lines only when hart 0 neither takes its records nor
  acknowledges it for 2^24 ticks after hart 0 halted, that is, only when
  the firmware's shutdown did not take effect. The `no-inject`
  expectation, which admits either domain's first denied access, is
  unchanged.
- **M1-B.3, tests and evidence.** `tests/sbi-test.c` covers the decision
  in ten scenarios: the ACK (at once, after progress, and before a window
  long past or a malformed tail); a still tail (the window's last tick
  waits, the window falls back, and a time before the start reads as a
  window long past); progress restarting the window, also when seen at
  its end; a hundred records each taken at the window's last tick; the
  malformed tails (behind, beyond the head, a wait started beyond it, and
  a tail wrapped past 2^64, which reads as behind); the time CSR's wrap;
  no record; the normal end, every record taken and then the ACK; and the
  board's backlog replayed through a real ring, 64 lines a domain of the
  run's mean length, 73 bytes, which hart 0 prints one per domain per pass
  for longer than M0's window, where the hart waits throughout and parks
  on the ACK, and the same with a hart 0 that stops after half of them,
  where the hart falls back one window after the last record taken: 63
  scenarios and 14,655 assertions (53 and 13,677 before), GCC = Clang.
  `tests/ring-test.c` covers the reads on a fresh ring and across a post
  (not yet published), a publish, a take (not yet released), and a
  release, with indices across 2^64, and for a reader's view, a failed
  one, and none; and checks both reads against the queue model at every
  step of the pseudo-random runs: 160 scenarios and 409,413 assertions
  (157 and 343,230). Single changes to the decision (no restart, the
  window before progress, no check behind or beyond the head, `>` for
  `>=`, the ACK after the malformed tail) and to the reads (the cursor
  for the head, the head for the tail, any view answered) each fail one
  of them. The stopped run's capture (its `serial.log`, SHA-256
  `234e196681f76bd778b9e56123ccba33c8324f7f18249c08e6ec7604563b298b`), CRs
  removed, is the new fixture `k3-no-inject-gcc-stop6-fallback.log`
  (SHA-256 `0460b200f40d...`), which the self-test requires to FAIL in
  kexec mode against `no-inject`'s expectation with exactly its six
  findings: the two guest lines after the first FAIL, the first FAIL
  without its DETAIL, and the second FAIL and both DETAIL lines after the
  failure; 47 cases, 45 before. M0's and M1's QEMU fixtures, every
  expectation file, `tools/gen-scenario.py`, and the 170 mutations are
  unchanged: where the ACK arrives at once the change is invisible. The
  image checker has no rule on the wait, and none changed. The board's
  kexec runs restart with the revised images into a new campaign
  directory: the preflight, both load checks, three GCC and one Clang
  `te-poc` runs, `reader-write`, and `no-inject`, each followed by one
  reset. The first campaign's runs stay as the record of the stop, and
  its passing runs are not M1's board evidence.

| File | Change | Why |
| --- | --- | --- |
| `src/mvp-ring.h`, `src/mvp-ring.c` | `be_mvp_ring_taken` and `be_mvp_ring_published`, each 0 for an absent, failed, or reader's view | The decision's inputs: hart 0's progress is the outbound tail, bounded by the published head (M1-B.1) |
| `src/mvp.h`, `src/mvp-sbi.c` | `struct be_mvp_ack_wait`, `enum be_mvp_ack_step`, `be_mvp_ack_wait_start`, and `be_mvp_ack_wait_step`; the header comments | The wait's decision as a pure, host-tested function in the SBI core (M1-B.1) |
| `src/mvp-hartmain.c` | `hart_fail()`'s wait loop takes the decision's answer; the header comment and `hart_fail()`'s | The window measures hart 0's progress, not its latency (M1-B.1); the rest of the terminal path is unchanged |
| `src/mvp-layout.h` | The comment above `BE_MVP_FAIL_ACK_TICKS`; the value unchanged | The window restarts on hart 0's progress (M1-B.1) |
| `tests/sbi-test.c` | The decision's ten scenarios, the board's backlog replayed through a ring among them | M1-B.3 |
| `tests/ring-test.c` | The reads' three scenarios, and both reads against the queue model at every simulated step | M1-B.3 |
| `Makefile` | The `ring` and `sbi` host-test pins: 160 and 409,413, 63 and 14,655 | The counts above |
| `tests/check-capture.py`, `tests/fixtures/k3-no-inject-gcc-stop6-fallback.log` | The stopped run's capture, CRs removed; its self-test case and pinned findings; the docstring | The checker goes on rejecting the shape M1-B removes, as M0-C kept its stopped capture (M1-B.3) |
| `README.md` | This section; the domain harts' Q10 text, the rings' reads, and hart 0's tail under Design; the ring test's row under Tests; the fixture's row under Harness | Documentation |

**Measured.** `tools/budgets.py` before M1-B, on M1-3's monitor
(`build/mvp/m1b-scratch/budgets-before.txt`, 2026-10-27 at 17:09 UTC),
and on the M1-B content (`build/mvp/records/budgets.txt`, from the check
below, 17:39 UTC): M1-B changed the MVP region's text alone, by `0xb0`
bytes in 17 of the 22 images measured and `0xc0` in five (GCC's
`two-guests`, `hart-start`, `reader-write`, and `no-inject` images and
Clang's `no-inject`). GCC's `two-guests` text went from `0x4460` to
`0x4520` and Clang's from `0x4b40` to `0x4bf0`, and the `te-poc` images'
from `0x4930` to `0x49e0` (GCC) and from `0x5030` to `0x50e0` (Clang). The
accepted code extent's text end, the accepted data, the MVP region's
rodata, data, and BSS, the pool, the hart region, and the flat and boot
images are as they were, and all 22 budgets pass (see
[Budgets (measured)](#budgets-measured)).

**The checks.** Before `804cd24c` was committed, `./mvp/mvp check` passed
on its content (the bundle's `source_commit=aaff1b26...` and
`source_tree=dirty changed=13`: M1-B's thirteen files;
`build/mvp/m1b-scratch/check-final.txt`, written at 17:39:30 UTC), among
its rows these, and then `./mvp/mvp kexec-rehearsal` passed for the four
scenario images (`kexec-rehearsal-final.txt`, 17:40:33 UTC):

```text
BE_MVP_HOST: PASS ring scenarios=160 assertions=409413 gcc=clang
BE_MVP_HOST: PASS sbi scenarios=63 assertions=14655 gcc=clang
BE_MVP_IMAGE_CHECK: PASS gcc clang
BE_MVP_IMAGE_CHECK: PASS mutations=97
BE_MVP_IMAGE_CHECK: PASS te-poc-gcc te-poc-clang
BE_MVP_IMAGE_CHECK: PASS mutations=100
BE_MVP_CAPTURE_SELF_TEST: PASS cases=47 failed=0
BE_MVP_CAPTURE_MUTATIONS: PASS mutations=170 rejected=170 seed=0x4d30
BE_MVP_QEMU_TOOLCHAIN[gcc]: runs=22 attempts=30 refused=8
BE_MVP_QEMU_TOOLCHAIN[clang]: runs=22 attempts=27 refused=5
BE_MVP_QEMU: PASS runs=44 attempts=57 refused=13
BE_MVP_BUDGETS: PASS measured=22
BE_MVP_EVIDENCE: PASS development <repo>/build/mvp/evidence/check files=238 images=184 qemu_attempts=57 rehearsals=4
BE_MVP_CHECK: PASS
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=6 image=2d33d5887cc0 kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=6 image=a55a5791b4b4 kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=2 refused=1 kexec_harts=1,5 image=0115b6960b73 kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=2 refused=1 kexec_harts=1,6 image=e32de2439ef0 kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
```

(GCC's `two-guests` and `te-poc` images, then Clang's.) The evaluator
last ran on M1-4's content (`20261027T080219Z`); it runs again at the
exact M1-6 commit. **The board.** The second campaign ran with
`804cd24c`'s images: every run passed, the `no-inject` run with hart 0's
FAIL and DETAIL alone (see
[M1-5's second board campaign](#m1-5s-second-board-campaign-2026-10-27)).

## The monitor's layers (M6-3)

Work package M6-3 (planning/mvp-m6-plan.md, D-5 and Q5; S1 H22; the
project snapshot's stage 0, planning/project-snapshot-mvp-1.0-rc2.md,
section 8) names the monitor's four layers: **proof-bearing decision**,
restricted C over captured inputs and in-memory state; **support**, which
formats, prints, and reports; the **executor**, `src/mvp-executor.c`, the
only C that performs a privileged effect; and the **platform and
assembly** boundary. No contract is written yet; that is the first
verification plan's.

**The executor.** One function per effect, each calling one assembly
helper or one accepted ported helper with its own arguments and returning
what that returns, with no decision of its own:

| Function | Effect | Calls |
| --- | --- | --- |
| `be_mvp_fw_call` | one HS-to-M call beyond the platform helpers', moved from hart 0's runtime unchanged | `be_r3_arch_sbi_call` |
| `be_mvp_exec_sbi_version` | SBI Base `get_spec_version` | `be_r3_platform_get_spec_version` |
| `be_mvp_exec_sbi_probe` | SBI Base `probe_extension` | `be_r3_platform_probe_extension` |
| `be_mvp_exec_hart_start` | HSM `hart_start` | `be_mvp_fw_call` |
| `be_mvp_exec_hart_status` | HSM `hart_get_status` | `be_mvp_fw_call` |
| `be_mvp_exec_send_ipi` | IPI `send_ipi` | `be_mvp_fw_call` |
| `be_mvp_exec_console_write` | hart 0's console write, DBCN through the diagnostic page | `be_r3_platform_write` |
| `be_mvp_exec_dbcn_write` | a domain hart's own DBCN write, from its stack | `be_mvp_fw_call` |
| `be_mvp_exec_system_reset` | the SRST shutdown | `be_r3_platform_reset` |
| `be_mvp_exec_reset_hs_state` | a hart's HS and VS reset, `hgatp` Bare | `be_r3_arch_reset_state` |
| `be_mvp_exec_install_hgatp` | `hgatp`, the local `hfence.gvma`, the readback | `be_r3_arch_install_management` |
| `be_mvp_exec_arm_stce` | `henvcfg` = STCE | `be_mvp_arch_arm_stce` |
| `be_mvp_exec_arm_controls` | a domain hart's controls and per-domain CSR set | `be_mvp_arch_arm_controls` |
| `be_mvp_exec_arm_budget` | hart 0's `stimecmp`, `sie`, and `sscratch` | `be_mvp_arch_arm_budget` |
| `be_mvp_exec_set_timer` | `vstimecmp`, SBI TIME | `be_mvp_arch_set_timer` |
| `be_mvp_exec_inject` | a denial's `vscause`, `vstval`, `vsepc`, `vsstatus` (denial images only) | `be_mvp_arch_inject` |
| `be_mvp_exec_clear_ssip` | `sip.SSIP` cleared | `be_mvp_arch_clear_ssip` |
| `be_mvp_exec_read_time` | the `time` CSR | `be_mvp_arch_read_time` |
| `be_mvp_exec_switch_hgatp` | the raw `hgatp` write (VMID probe images only) | `be_mvp_probe_arch_switch_hgatp` |
| `be_mvp_exec_fence_w_w`, `_r_r`, `_r_w`, `_rw_rw` | `fence w, w`, `r, r`, `r, w`, and `rw, rw` | `be_mvp_arch_fence_w_w` and the rest |
| `be_mvp_exec_fence_i` | the image's one `fence.i` | `be_mvp_arch_fence_i` |
| `be_mvp_exec_wait` | HS `wfi` until an enabled interrupt is pending | `be_mvp_arch_wait` |
| `be_mvp_exec_park` | HS `wfi`, forever | `be_mvp_arch_park` |
| `be_mvp_exec_resume` | the checked `sret` into the domain | `be_mvp_arch_resume` |
| `be_mvp_exec_halt` | the accepted fail-closed halt | `be_r3_arch_halt` |

Hart 0's runtime, the domain harts', and the probe module call these and
perform no privileged effect themselves; `be_mvp_send_ipi`, which decides
a hart's mask and base, stays in hart 0's runtime and calls the executor's
IPI. The executor is built with each monitor, as the runtimes are, and
links the injection only into an image that accepts denials and the raw
switch only into the two VMID probe images. The image checker holds the
seam in every image's instruction words: no function in the MVP region's
text but the executor's names an assembly helper or an accepted
privileged helper, the install's one call site is the executor's and its
caller the domain hart's `be_mvp_hart_main` (and, in `probe-platform`,
`be_mvp_probe_hgatp`), and the injection's one call site is the
executor's and its caller the denial action. Ring publication, the head's
store after the executor's `fence w, w`, stays in the ring code, as do the
barrier's generation words and the memory clears and copies: they are
in-memory state, outside Q5's scope.

**The layers.** Lines are `wc -l` of the tree's files at the M6-3
content; code lines are those neither blank nor comment. A file is in one
layer but for four that mix layers, whose functions are classified one by
one (a function's lines run from its leading comment and forward
declaration to its closing brace), whose named blocks are support, and
whose remaining lines (the header comment, includes, assertions,
constants, and data) are proof-bearing:

| File | Lines | Layer |
| --- | --- | --- |
| `src/mvp.h` | 1,388 | proof-bearing: the SBI core's types, records, and contracts |
| `src/mvp-ring.h`, `src/mvp-ring.c` | 292, 345 | proof-bearing: the rings |
| `src/mvp-hart.h` | 721 | proof-bearing: the hart blocks and the control loop's decisions |
| `src/mvp-hart.c` | 915 | mixed: proof-bearing 892, support 23 |
| `src/mvp-sbi.h` | 117 | proof-bearing: the firmware surface's checks |
| `src/mvp-sbi.c` | 1,269 | mixed: proof-bearing 1,147, support 122 |
| `src/mvp-gstage.h`, `src/mvp-gstage.c` | 568, 1,047 | proof-bearing: the G-stage derivation and re-walk |
| `src/mvp-core.h`, `src/mvp-core.c` | 89, 232 | proof-bearing: the core profile's G-stage inputs and identity |
| `src/mvp-payload.h`, `src/mvp-payload.c` | 165, 211 | proof-bearing: the payload checks |
| `src/mvp-sha256.h`, `src/mvp-sha256.c` | 87, 249 | proof-bearing: SHA-256 and HMAC-SHA-256 |
| `src/mvp-layout.h` | 410 | proof-bearing: the layout's constants and assertions |
| `src/mvp-runtime.c` | 2,194 | mixed: proof-bearing 1,649, support 545 |
| `src/mvp-hartmain.c` | 588 | mixed: proof-bearing 503, support 85 |
| `src/mvp-probe.h`, `src/mvp-probe.c` | 134, 491 | support: the probe module and its reporting |
| `src/mvp-executor.h`, `src/mvp-executor.c` | 236, 190 | executor |
| `src/mvp-platform.h` | 334 | platform/assembly: the helpers' and entry points' declarations |
| `src/mvp-trap.S`, `src/mvp-hartentry.S` | 672, 60 | platform/assembly: the vector, the resume tail, the helpers, the hart entry |
| `src/mvp-probe-arch.S` | 56 | platform/assembly: the stub's bytes and the raw switch |
| `src/mvp-guest-payload.S`, `shim/mvp-shim.S` | 55, 369 | platform/assembly: the boot image |

The mixed files' functions:

| File | Layer | Lines | Functions |
| --- | --- | --- | --- |
| `src/mvp-runtime.c` | proof-bearing | 1,649 | `build_image_layout`, `be_mvp_send_ipi`, `clear_mvp_bss`, `seal_config`, `probe_firmware`, `probe_sstc`, `channel_page`, `check_channel`, `check_pages`, `build_gstage`, `check_payload`, `clear_guest_ram`, `clear_channel`, `place_pages`, `place`, `place_payload`, `measure`, `hart_page`, `ring_views`, `publish_blocks`, `start_harts`, `post_inbound`, `ping`, `answer`, `deliver`, `domain_failed`, both `step`s, `drain_held`, `visit`, `drain`, `wait_ready`, `control_loop`, `start_run`, `be_mvp_runtime_main` (1,176), and the file's declarations and data |
| `src/mvp-runtime.c` | support | 545 | the line formats and value programs (201); `symbol_address`, `be_mvp_line_format`, `be_mvp_detail_line`, `write_text`, `write_line`, `since`, `terminal`, `be_mvp_runtime_terminal`, `fail_detail`, `fail_domain`, `emit_text`, `emit_line`, `line_start`, `emit`, `boot_fail`, `scenario_line`, `line_hex`, `emit_terminated`, `run_complete`, `emit_record`, `emit_denial`, `wake_failed`, and the probe images' four wrappers (344) |
| `src/mvp-hartmain.c` | proof-bearing | 503 | `hart_page`, `publish`, `tell_control_hart`, `acknowledged`, `hart_fail`, `be_mvp_hart_terminal`, `console`, `console_write`, `wait_serve`, `parked`, `ipi`, `stopped`, `mgmt_call`, `deny`, `be_mvp_dispatch`, `be_mvp_hart_main` (423), and the file's declarations |
| `src/mvp-hartmain.c` | support | 85 | the FAIL line's two strings; `symbol_address`, `fallback_write`, `register_fail`, `exit_fail`, `controls_fail`, and the probe images' `be_mvp_dispatch` (83) |
| `src/mvp-sbi.c` | proof-bearing | 1,147 | the classification, the denial decision, the SBI handlers, the exit handler, the IPI and wait service, the management decision, the injection's words, the return, the entry frame, the CSR set, the console's LINE records, the records' posts, the ACK wait, and the HSM checks and census (986 in 51 functions), and the file's declarations |
| `src/mvp-sbi.c` | support | 122 | the class and CSR name tables; `be_mvp_class_name`, `be_mvp_vcsr_name`, `be_mvp_domain_prefix`, and the line builder (`be_mvp_line_reset`, `line_byte`, `be_mvp_line_text`, `be_mvp_line_hex`, `be_mvp_line_decimal`) |
| `src/mvp-hart.c` | proof-bearing | 892 | everything but the printed LINE |
| `src/mvp-hart.c` | support | 23 | `be_mvp_line_output` |

The totals:

| Layer | Lines | Code lines |
| --- | --- | --- |
| proof-bearing decision | 10,112 | 6,285 |
| of which the pure decision files and functions (no executor call) | 7,960 | 4,753 |
| of which hart 0's and the domain harts' decision code (calls the executor) | 2,152 | 1,532 |
| support | 1,400 | 1,105 |
| executor | 426 | 177 |
| platform/assembly | 1,546 | 930 |
| **Total** (`src/` and `shim/`, C and assembly) | **13,484** | **8,497** |

The proof-bearing subset is 10,112 lines (6,285 code lines); its pure
part, the ring, hart-block, control-loop, SBI, denial, management,
G-stage, core-profile, payload, and SHA-256 code with its headers, is
7,960 (4,753). The two linker scripts (`src/mvp-monitor.lds`, 265 lines,
and `src/mvp-boot.lds`, 99) are the platform's layout and are not
counted. The generated scenario files (`mvp-scenario.h`, `mvp-config.c`,
`mvp-payload-layout.h`, under `build/`) are captured inputs.

The images also link the ported accepted sources, as `tools/port.py`
makes them from the tree (`build/mvp/port`), and B1's handoff:

| Ported file | Lines | Layer |
| --- | --- | --- |
| `virt/be/manifest.c`, `virt/be/state.c` | 1,359, 296 | proof-bearing: R1's copy, validation, seal, and derivation, widened by the MVP core profile's rules |
| `virt/be/r3.c` | 602 | proof-bearing: the accepted boot check (its unused R3 steps are not linked) |
| `include/be/types.h`, `manifest.h`, `state.h`, `r0-config.h`, `r2.h`, `r3.h`, `r4.h` | 1,988 in all | proof-bearing: the accepted interfaces the MVP includes |
| `arch/riscv/be/freestanding.c` | 33 | support: `memcpy` and `memset` |
| `arch/riscv/be/platform.c`, `privileged.S`, `r5-entry.S`; `bringup/k3-b1/src/b1-handoff.S`; `arch/riscv/be/r0-layout.h`, `r0-sbi.h`, `r3-platform.h` | 114, 303, 37; 71; 200, 122, 179 | platform/assembly: the accepted SBI helpers, the privileged functions, the entry, B1's quiesce, and their declarations |

`be_r3_arch_enter_management`, unused since M6-2, stays linked: it shares
`privileged.S`'s one `.text` section with the reset, the install, the SBI
call, and the halt, so `--gc-sections` cannot drop it, and a port rule
removing it would change accepted assembly in the port and the image
checker's rules on it (B2's bytes, the `sret` sites, the CSR writers).

## How the port is made

`tools/port.py` is B7's `scripts/port.py` with MVP names. It first runs
B2's unchanged `port.py --check` on B2's port (`build/k3-b2/port`) and
requires B2's manifest to match its pin. It then copies every file B2's
manifest lists and applies B7's five rules and seven substitutions, with
MVP names, and seven more rules, each with its exact count:

- in `r5-entry.S`, the runtime call becomes `be_mvp_runtime_main` and the
  final tail becomes `be_r3_arch_halt`;
- in `r5-beryllium.lds`, the three trap-vector names become
  `be_mvp_trap_vector`;
- the linker script gains an `mvp_pool` PT_LOAD entry;
- it gains the NOLOAD `.gstage.root.mvp` section of 64 KiB at
  `0x1_0203_4000` (`__be_mvp_pool_start`, `__be_mvp_pool_end`), 16 KiB
  aligned, holding G0's 32 KiB pool and then G1's, with B7's `ASSERT`s
  for it;
- `hart-region` (M0-1): it gains the NOLOAD `.hart.mvp` section of
  `0x20000` bytes at `0x1_0204_4000` (`__be_mvp_hart_region_start`,
  `__be_mvp_hart_region_end`) in the same segment, with three `ASSERT`s:
  its start and end, its 16 KiB alignment, and its place after the pool;
- `region-phdrs` (M0-A.1): PHDRS gains `mvp_text` (`FLAGS(5)`), `mvp_ro`
  (`FLAGS(4)`), and `mvp_data` (`FLAGS(6)`) after `mvp_pool` (1 block);
- `region-text-exclude`, `region-rodata-exclude`, `region-data-exclude`,
  and `region-bss-exclude` (M0-A.1): the accepted `*(.text .text.*)`,
  `*(.rodata .rodata.*)`, `*(.data .data.*)`, and `*(.bss .bss.*)` with
  `*(COMMON)` patterns exclude the MVP layer's C objects (1 each);
- `mvp-region` (M0-A.1): `.mvp.text` (`__be_mvp_region_start`,
  `__be_mvp_text_start`, `__be_mvp_text_end`), `.mvp.rodata`, and
  `.mvp.data` (data, then `__be_mvp_bss_start` to `__be_mvp_bss_end`,
  then `__be_mvp_region_end`) at `. = 0x102064000`, holding exactly those
  objects' sections by explicit input patterns, with three `ASSERT`s: its
  start `0x102064000` and end at most `0x1020a4000`, its 16 KiB
  alignment, and its place after the hart region (1 block).

M6-2 (planning/mvp-m6-plan.md, D-1 to D-4) adds the MVP core profile's
43 rules on four more files, 45 substitutions, each with its exact count:

- `control-stack` in `r5-entry.S`: hart 0's stack by its MVP name,
  `__be_control_stack_end`;
- 14 in `include/be/manifest.h`: the MVP port's note; the limits, 24
  resources, 12 authorities, 8 mappings, and 3 channels, with
  `BE_MAX_HARTS` 3 (the control hart and each domain's) and
  `BE_VMID_LIMIT` 16384; `BE_PROFILE_MVP_CORE`; the inventory's and the
  canonical state's platform hart count, and each domain's hart in its
  request, its binding, and its derived root, each field with its
  kernel-doc line;
- 27 in `virt/be/manifest.c`: the profile's validation: at least the
  named harts on the platform; any number of monitor code and data
  extents; nonzero VMIDs below 2^14, the domains' VMIDs and harts
  distinct and neither hart the control hart; channels in either
  direction, the source's read and write and the target's read, each on
  its own shared frame; each authority by its frame's class (its own
  window, read and execute, with write for its RAM; its own private page
  without execute; a channel's shared page with its end's rights); each
  domain's one window and guest-physical ranges disjoint per domain; the
  counts bounded rather than fixed; and each domain's hart in the
  identity and the derived roots;
- `fixture-extents` in `virt/be/r3.c`: the boot check without the fixture
  extents the MVP's linker script no longer places.

Five are span rules: `channels`, `authorities`, `check-channels`, and
`check-authorities` in `manifest.c`, and `fixture-extents`; each replaces
the text from its first line through its last, which must hash to its
pinned SHA-256. `r1-config.c`, `sv39x4.c`, and `r5-guest.S` stay in the
port, and no image links them.

Every accepted `ASSERT` stays. `--check` re-derives the tree byte for
byte, and `--inputs` lists B2's inputs:

```text
BE_MVP_PORT: CHECK PASS files=32 changed=5 rules=55 substitutions=59 b2_manifest=7c43e75b2066
```

M0-3 to M5 link the port's linker script into every image; since M6-2
the images link `src/mvp-monitor.lds`, a counted copy of it (see
[Files copied from B7](#files-copied-from-b7)). Each build measures the
monitor budgets (see [Budgets (measured)](#budgets-measured)).

## Commands

```sh
./mvp/mvp check                 # every off-board check (make -C mvp check)
./mvp/mvp port                  # the port, re-derived byte for byte
./mvp/mvp host-test             # the host tests, GCC = Clang
./mvp/mvp tool-lock check       # every locked role and pin, fail closed
./mvp/mvp tool-lock refresh     # rewrite the lock (responsible human only)
./mvp/mvp evaluate              # mvp check in the clean evaluator, images compared
./mvp/mvp image                 # the monitor and boot images
./mvp/mvp image-check           # the image checker and its mutation test
./mvp/mvp variants              # the negative variants, checked
./mvp/mvp probes                # the probe images, checked
./mvp/mvp budgets               # every budget, measured
./mvp/mvp qemu                  # every scenario, variant, and probe in QEMU
./mvp/mvp uboot-rehearsal       # U-Boot booti of each scenario image in QEMU, 8 harts (M5-3)
./mvp/mvp evidence              # the evidence bundle of the last check
./mvp/mvp k3-preflight          # the board tools, run by the human; K3_PREFLIGHT=before|after (M5-2)
./mvp/mvp k3-stage              # the session's 14 images on the Beryllium partition (M5-2)
./mvp/mvp k3-env record|install|restore  # U-Boot's saved environment, the human present (M5-2)
./mvp/mvp k3-campaign           # the session's 14 image groups, 20 runs from reset (M5-2)
./mvp/mvp k3-probe              # the three probe groups alone, in a session
./mvp/mvp k3-characterize       # M5-6a: the board's U-Boot, attended, no saveenv
./mvp/mvp board-evidence        # a session's board record and platform record under mvp/results/
./mvp/mvp claim-ledger check    # the claim ledger and the release surfaces under docs/ (M4-1)
./mvp/mvp claim-ledger render   # write docs/claim-ledger.md from docs/claim-ledger.json
./mvp/mvp claim-ledger self-test # the checker's seeded mutations and variants
./mvp/mvp rc-record ARGS...     # the release-candidate record under mvp/results/ (M4-4)
./mvp/mvp help
```

The wrapper runs `/usr/bin/make` under `env -i` with `PATH=/usr/bin`,
`LC_ALL=C`, `LANG=C`, `SHELL=/bin/bash`, and the caller variables it is
given. `make -C mvp <target>` works too, from a clean environment:

| Target | What it does |
| --- | --- |
| `check` | `tool-lock-check`, `lint`, `policy-negatives` (M1-1), `port-check`, `guest-pin-check`, `host-test`, `target-check`, `reference-boot`, `image-check`, `variants`, `probes`, `tools-check`, `qemu-test`, `budgets`, `evidence`, and (M4-1) `claim-ledger-check` after the evidence bundle, then `BE_MVP_CHECK: PASS` |
| `claim-ledger-check` | `tools/claim-ledger.py`'s self-test, then its `check`, each recorded under `records/claim-ledger/`; in `check`, after `evidence`, whose bundle both records then join (`claim-ledger.py join`, the bundle's manifest written again); alone, it joins the last bundle (M4-1) |
| `tool-lock-check` | The lock tool's and the closure fetcher's self-tests, then every role and pin |
| `lint` | `bash -n` and `shellcheck` on every shell script, a Python parse of every Python file, the Make controls' self-test, and the policy checker's self-test and mutations, recorded (M1-1) |
| `policy-negatives` | `tools/policy-check.py` on `te-poc`, recorded with its report, which must equal the generator's byte for byte; then the two build-time negatives, `undeclared-flow` and `grant-without-rule`, each failing exactly its declared analyses, with no header written (M1-1, M1-4); since M2-1 the same for `anchor`, given the measured kernel and DTB, and its two, `grant-without-rule` and `secret-flow`, recorded as `anchor-<name>`: four negatives in all |
| `port`, `port-check` | The port, and its byte-for-byte re-derivation |
| `guest`, `guest-pin-check` | The guest outputs (cached by pin), and the self-tests and every output against its pin |
| `reference-boot` | Each guest's Image and DTB under plain OpenSBI v1.6 in QEMU, no monitor |
| `kernel-repro` | A second full guest build elsewhere, compared byte for byte (not in `check`: about 70 s of kernel build) |
| `payload-layout` | The monitor's generated payload layout |
| `host-test` | The seven host tests (`deny` since M1-3, `sha256` since M2-2), GCC and Clang, outputs compared and counts pinned |
| `target-check` | The pure-C mechanism compiled for the target with both toolchains and the accepted flags, at `-Os` |
| `scenario` | The scenario's self-test, header, and expectation files (`tools/gen-scenario.py`): `MVP_SCENARIO_NAME`'s, `two-guests` by default, `te-poc` (M1-1), or `anchor` (M2-1), whose policy check comes first and whose authority report is written beside them (`anchor`'s from the measured kernel and DTB, with the expected measurement); the images' targets generate all three |
| `image` | The monitor ELF and `0xa4000`-byte flat image and the boot ELF and image for each toolchain in `IMAGE_TOOLCHAINS` (GCC and Clang since M0-A.1), with the second link's identical image; and, since M1-3, each toolchain's `te-poc` images under `build/mvp/<toolchain>/te-poc`, and since M2-2 its `anchor` images under `build/mvp/<toolchain>/anchor` |
| `image-check` | `tests/check-image.py` on each toolchain's image with the scenario's binding, then its mutation test on each; then the same for the `te-poc` images with te-poc's DTBs, expectation, and authority report (M1-3), and for the `anchor` images with anchor's DTBs, kernel, expectation, and authority report (M2-2; 111 mutations each since M2-3) |
| `variants` | The nine negative-variant boot images of `two-guests` and, since M1-3, `te-poc`'s two, `reader-write` and `no-inject`, and `anchor`'s four, `secret-shared`, `response-writable`, and `wrong-measurement` (M2-2), and `no-grant-check` (M2-3), for GCC and Clang, each checked against its toolchain's image |
| `probes` | The three probe images for GCC and Clang, each checked with its probe profile, then the profile's mutation test |
| `budgets` | `tools/budgets.py` on every image, and on a measurement link for a toolchain without an image (none since M0-A.1) |
| `tools-check` (`tools.mk`) | `capture-check` (the capture checker's self-test and mutations), `evidence-check` (the bundler's self-test), (M4-4) `rc-record-check` (the release-candidate record tool's self-test), and `run-tool-check` (the board tools' dry run, since M5-2 on a fake U-Boot); and since M5-2 `platform-probe-check` (`tests/test-platform-probe.py`, the layout rule), `partition-tool-check` (the partition tool's self-test), and `uboot-rehearsal-check` (the rehearsal driver's self-test); and since the snapshot support of 2026-10-31 `snapshot-check` (`tools/snapshot.sh self-test`: a snapshot of `HEAD` under the scratch directory, its exclusions, marker, README fields, one commit, its files `HEAD`'s blobs, and the ledger's reading of the marker; then `update` to `HEAD`'s parent and its two refusals). M0-4's `rehearsal-init-check` and `kexec-loader-check` went with the kexec code in M5-2 |
| `qemu-test` | `tests/run-qemu.sh`: every scenario, variant, and probe image, both toolchains, each attempt judged by the capture checker (44 runs since M1-4, 58 since M2-5 with `anchor` and its four runtime negatives) |
| `evidence` | `tools/evidence.py`: the development bundle `build/mvp/evidence/check` |
| `uboot-rehearsal` (M5-3) | `tests/uboot-rehearsal.sh` on each toolchain's `two-guests`, `te-poc`, and `anchor` QEMU-only images and the fall-through, with `UBOOT_REHEARSAL_ALL=1` also the board's probes and negatives (not in `check`); `uboot-build` builds its U-Boot with B3's script when the binary is missing or lacks the lock's SHA-256. M0-4's `kexec-rehearsal` is gone (M5-2) |
| `qemu-images`, `qemu-image-check` (M5-2) | Each scenario image's QEMU-only copy, `be-mvp-boot-qemu.img` (header bytes 8 to 15 `BE_MVP_QEMU_TEXT_OFFSET`), and `tests/check-image.py --qemu-image` on each pair; `image-check` runs it |
| `k3-preflight`, `k3-stage`, `k3-env-record`, `k3-env-install`, `k3-env-restore`, `k3-characterize`, `k3-campaign`, `k3-probe` | The board tools of a session from system reset (M5-2; the M5 plan, "The session protocol (M5-6)"). Every target but `k3-preflight` needs `K3_RUN_ROOT`, the session's directory; `k3-preflight` takes `K3_PREFLIGHT=before` or `after`; `k3-stage` and `k3-campaign` take the session's plan from `tools.mk` (`K3_STAGE`, `K3_PLAN`: 14 images, 14 groups, 20 runs) and no selector; `k3-env-install` needs `K3_ENV_CONFIRM`. With `K3_RESET=k3ctl` the console tool resets the board through the pinned client under the port-open rule; without it the human does. Until M5-2, `k3-load-check` and `k3-campaign` took `SCENARIO`, `VARIANT`, `TOOLCHAIN`, and `RUNS` for a kexec campaign |
| `board-evidence` | The board record of the campaign `K3_RUN_ROOT` under `mvp/results/`, never over an existing one, with its platform record (`tools/platform-record.py`, M0-6); since M1-5 also each run's `reset.txt`, the policy check on `te-poc` and its report, and the campaign's `serial-log-note.txt`, which must be written by hand first; since M2-5 also the policy check on `anchor` and its report, and each `anchor` run's measured inputs checked; since Plan revision M4-A the board's ssh target and IPv4 address only as `<board-ssh>` and `<ip>`, every file checked for both, and the title `K3_RECORD_TITLE`; since M5-2 a session's record: `launcher=uboot-autoboot-nvme`, each run's whole capture judged again in `uboot` mode and its excerpt from `Autoboot in`, the session's keystroke log, resets, staging record, environment verdicts, and preflight after, and a MAC address and a `serial#` value as `<mac>` and `<serial>` |

Caller variables are `TOOLCHAIN` (`gcc` or `clang`), `LINUX_GIT` (a local
mirror, path or URL), `MVP_RPM_CACHE` (a directory with B3's pinned `m4`,
`bison`, and `flex` RPMs), and `K3_SERIAL_LOG`, `K3_RUN_ROOT`, (Plan
revision M4-A.2) `K3_RECORD_TITLE`, the board record's title before the
campaign's name (default `MVP COM260 campaign`; letters, digits, spaces,
and `.`, `,`, `-`), and (M5-2) `K3_PREFLIGHT`, `K3_ENV_CONFIRM`, and
`K3_ENV_ACCEPT_V`, for the board targets (`JOBS` is allowed, but no
target reads it, nor, since M5-2, `TOOLCHAIN`; M5-2 removed `RUNS`,
`VARIANT`, and `SCENARIO`);
`make -C mvp` also takes `MVP_SCENARIO_NAME` (M1-1)
for the `scenario` target (`two-guests`, `te-poc`, or since M2-1
`anchor`). For the `k3-*` commands only, the wrapper also
passes the board tools' own settings from the environment, as M5-2 left
them (`K3_SSH`, `K3_SSH_OPTIONS`, `K3_SUDO`, `K3_WAIT_SECONDS`,
`K3_TAIL_SECONDS`, `K3_ENV_STORE`, `K3_DOWN_SECONDS`, `K3_FEDORA_SECONDS`,
`K3_POLL_SECONDS`; the console tool's `K3_TMUX_SESSION`, `K3_TYPE_DELAY`,
`K3_ECHO_SECONDS`, `K3_PROMPT_SECONDS`, `K3_BOOT_SECONDS`,
`K3_AUTOBOOT_SECONDS`, `K3_IDLE_SECONDS`, `K3_HUMAN_SECONDS`, and
`TMUX_TMPDIR`; the reset's `K3_RESET=k3ctl`, `K3CTL` the pinned client,
and `K3CTL_DEV` its dongle's device), and `SSH_AUTH_SOCK`; no makefile
assigns them, and `uboot-rehearsal` passes `UBOOT_REHEARSAL_ALL`. The board targets pass the pin file `tools/k3ctl.sha256`
themselves (`K3CTL_PIN`), and the guest Image (`K3_KERNEL`), the scenario's
authority report (`K3_REPORT`, anchor's for `anchor` and its variants,
else te-poc's), and since M2-5 anchor's measured DTB (`K3_MEASURED_DTB`),
which `tools/k3-run.sh` needs, with the Image, for a v3 expectation's
measurement and records in each run's `run.txt` (`measured=`). On the
laptop `lx2`, which lacks `m4`, `bison`, and `flex`, the guest kernel was
built with:

```sh
make -C mvp guest LINUX_GIT=/home/jmorris/src/kernel.org/linux \
	MVP_RPM_CACHE=$PWD/build/k3-b7/host-tools/rpms
```

On the workstation `l1`, which has B3's `m4`, `bison`, and `flex` NEVRAs
installed, `MVP_RPM_CACHE` is not needed; `kernel-repro` is not a wrapper
command and runs as `make -C mvp kernel-repro LINUX_GIT=<the same mirror>`
from the wrapper's clean environment (see
[`kernel-repro` again](#kernel-repro-again-on-l1-2026-10-26)).

The two blocks below are history: the kexec procedures of M1 and M2,
whose `k3-load-check` and selectors M5-2 removed; M5's board session is
the block after them. The board procedure as M1-5's second campaign ran
it on `l1`, after `mvp check` and the kexec rehearsal passed (see
[M1-5's second board campaign](#m1-5s-second-board-campaign-2026-10-27)):
`te-poc`'s load checks and runs name `SCENARIO=te-poc`, and each
variant implies its scenario. The board answered SSH as `fedora@k3-f45`,
the dongle was `/dev/ttyACM0`, and `K3CTL` named the client that
`tools/k3ctl.sha256` pins; the serial log is the operator's picocom log.
The M1 plan's own command list ("Board safety and procedure") names no
`SCENARIO` and so would run `two-guests` (open item 44).

```sh
export K3_SSH=fedora@k3-f45 K3_SERIAL_LOG=<the operator's picocom log>
export K3_RESET=k3ctl K3CTL=<the pinned k3ctl client> K3CTL_DEV=/dev/ttyACM0
./mvp/mvp k3-preflight
./mvp/mvp k3-load-check SCENARIO=te-poc TOOLCHAIN=gcc
./mvp/mvp k3-load-check SCENARIO=te-poc TOOLCHAIN=clang
export K3_RUN_ROOT=$PWD/build/mvp/k3-campaigns/20261027-com260-m1b
./mvp/mvp k3-campaign SCENARIO=te-poc TOOLCHAIN=gcc RUNS=3
./mvp/mvp k3-campaign SCENARIO=te-poc TOOLCHAIN=clang RUNS=1
./mvp/mvp k3-campaign TOOLCHAIN=gcc VARIANT=reader-write RUNS=1
./mvp/mvp k3-campaign TOOLCHAIN=gcc VARIANT=no-inject RUNS=1
$EDITOR "$K3_RUN_ROOT/serial-log-note.txt"   # by hand, from the picocom log
./mvp/mvp board-evidence
```

The board procedure for M2-6 (M2 plan, Q11, "Board safety and
procedure"): the shared K3 is used only after the responsible human
confirms that it is free, the preflight included. It is the plan's
list in the wrapper's form from the repository root, with the board
settings M1-5's block exports and the hand-written serial-log note that
`board-evidence` refuses to run without, which the plan's list omits
(open item 57). M2-6 ran it twice: the first campaign
(`build/mvp/k3-campaigns/20261028-com260-m2-stopped/`) passed the
preflight and both load checks and stopped at its first `anchor` run
(stop 6; Plan revision M2-A); the second, under M2-A's checker and the
same images, with the first campaign's preflight and load checks
standing, is `K3_RUN_ROOT=$PWD/build/mvp/k3-campaigns/20261028-com260-m2a`,
whose six runs passed as declared, the first followed by a second
`k3ctl reset` by hand on the responsible human's direction and the
campaign resumed into the same directory (see
[M2-6's second board campaign](#m2-6s-second-board-campaign-2026-10-28));
its `board-evidence` is M2-7's (see [M2-7](#m2-7-2026-10-28)).
`SCENARIO=anchor` selects anchor's images, report, and measured inputs,
and each variant implies `anchor`; with no `K3_RUN_ROOT` a campaign's
directory would be `build/mvp/k3-campaigns/<UTC>-anchor-<toolchain>`.

```sh
export K3_SSH=<the board's Fedora> K3_SERIAL_LOG=<the operator's picocom log>
export K3_RESET=k3ctl K3CTL=<the pinned k3ctl client> K3CTL_DEV=/dev/ttyACM0
python3 -B "$K3CTL" -d "$K3CTL_DEV" status   # by hand
./mvp/mvp k3-preflight
./mvp/mvp k3-load-check SCENARIO=anchor TOOLCHAIN=gcc
./mvp/mvp k3-load-check SCENARIO=anchor TOOLCHAIN=clang
export K3_RUN_ROOT=$PWD/build/mvp/k3-campaigns/<date>-com260-m2
./mvp/mvp k3-campaign SCENARIO=anchor TOOLCHAIN=gcc RUNS=3
./mvp/mvp k3-campaign SCENARIO=anchor TOOLCHAIN=clang RUNS=1
./mvp/mvp k3-campaign TOOLCHAIN=gcc VARIANT=wrong-measurement RUNS=1
./mvp/mvp k3-campaign TOOLCHAIN=gcc VARIANT=no-grant-check RUNS=1
$EDITOR "$K3_RUN_ROOT/serial-log-note.txt"   # by hand, from the picocom log
./mvp/mvp board-evidence
```

The `no-grant-check` run is to end in `BE_MVP:FAIL run-timeout` after its
2^27 ticks (5.6 s at the board's 24 MHz), a terminal marker, after which
the tool resets the board as after every declared failure (the plan's
text).

The board session of M5 (the M5 plan, "The session protocol (M5-6)"),
after the human has made the `beryllium` partition and confirmed the
board free, with the human present at the install, the restore, and any
recovery; the characterization (M5-6a) is `./mvp/mvp k3-characterize`, in
a session directory of its own:

```sh
export K3_SSH=<the board's Fedora> K3_SERIAL_LOG=<the operator's picocom log>
export K3_TMUX_SESSION=k3-console-1
export K3_RESET=k3ctl K3CTL=<the pinned k3ctl client> K3CTL_DEV=/dev/ttyACM0
export K3_RUN_ROOT=$PWD/build/mvp/k3-campaigns/<date>-com260-rc2
./mvp/mvp k3-preflight K3_PREFLIGHT=before
./mvp/mvp k3-stage
./mvp/mvp k3-env record
./mvp/mvp k3-env install K3_ENV_CONFIRM=<12 hex digits k3-env record printed>
./mvp/mvp k3-campaign
./mvp/mvp k3-env restore
./mvp/mvp k3-preflight K3_PREFLIGHT=after
$EDITOR "$K3_RUN_ROOT/serial-log-note.txt"   # by hand, from the picocom log
./mvp/mvp board-evidence
```

Build outputs go under `build/mvp/`; compiler and tool scratch goes to
`build/mvp/tmp` (`TMPDIR`), never the host's `/tmp`. Besides
`tool-lock refresh` and `board-evidence`, the wrapper commands that write
outside `build/` are `claim-ledger render`, which rewrites
`docs/claim-ledger.md` from its JSON source (M4-1), and `rc-record`, which
writes the new release-candidate record its `--out` names (M4-4); since
M5-2 the board session's `k3-env` and `k3-preflight` also keep the full
environment texts and the partition's UUID in the private store
`K3_ENV_STORE` (by default `~/.local/state/beryllium/k3-env/`, outside the
repository), and a session's `K3_RUN_ROOT` may lie anywhere absolute.

### Make controls

`tools/make-control.py` is R5's `tests/r5/make-control.mjs` semantics in
Python (S1 H33), with an allowlist of caller variables instead of none.
Both makefiles run it while they are parsed and stop unless it prints
exactly `BE_MVP_MAKE_CONTROL: PASS`. It reads the nearest Make process
through `/proc` and refuses:

- a Make ancestor that is not the lock's `/usr/bin/make`;
- on the command line and in `MAKEFLAGS`, `GNUMAKEFLAGS`, and `MFLAGS`:
  `-e`, `-i`, `-k`, `-n`, `-q`, `-t`, `-o`, `-W`, `-I`, `-E`/`--eval`,
  clustered short options, bare flag words (`MAKEFLAGS=ki`), and any
  option it does not know; `-f` naming anything but `mvp/Makefile`,
  `mvp/guest.mk`, or `mvp/tools.mk`; with no `-f`, Make running outside
  `mvp/` (after any `-C`);
- an assignment of any name but a caller variable, and a caller variable
  whose value is not of its own form;
- in the environment, `MAKEFILES`, a name that changes the compilers, the
  loader, the shell, or Python, and any variable the makefiles or the lock
  assign (but `PATH`, `SHELL`, `LANG`, `LC_ALL`, and `TMPDIR`, which the
  makefiles reset).

Its self-test runs 59 cases since M5-2 (57 at Plan revision M4-A.2, two
of them `K3_RECORD_TITLE`'s), among them the forms of M5-2's board session
variables. The wrapper remains the normal entry: GNU
Make may honour an alternate file or exit before any makefile runs the
check.

## Tool lock

`tools/lock/tool-lock.conf` (schema `be-mvp-tool-lock-v2` since Plan
revision M0-B) is generated by `tools/lock/tool-lock.py refresh` and
checked by `tool-lock.py check` (plan, "Tool lock and the clean
evaluator", Q8). It is also a makefile fragment: both makefiles include
it, run every tool by its locked absolute command, and set
`PATH=/usr/bin`. Each role records its command, the resolved executable,
the version arguments and first version line, the executable's SHA-256,
and the owning package's NEVRA (`rpm -qf`). `check` re-resolves every
role and compares all five, then the pins and the closure's SHA-256,
failing closed on any drift with one line naming each; `refresh` rewrites
the file from the host and prints what changed. The lock was generated
once, on the laptop `lx2`, on 2026-10-23; on 2026-10-24 M0-B added the closure's
RPM digests by `bind_closure()` (the schema line and `MVP_CLOSURE_SHA256`
change) and the three host-only roles by `refresh`, whose diff was those
roles' lines only (see [Results](#plan-revision-m0-b-at-67731e4c-2026-10-24)).
Two refreshes followed, each on the responsible human's direction: on
2026-10-25 for `lx2`'s `ca-certificates` update (`804fa95f`; see
[Results](#the-lock-refresh-and-the-gates-at-804fa95f-2026-10-25)), and on
2026-10-26 on the workstation `l1`, which changed the `ssh` and `scp`
roles and four closure lines (see
[Results](#the-host-move-and-the-lock-refresh-on-l1-2026-10-26)). The
table is the lock as it now stands.

| Role (32) | Version | Package |
| --- | --- | --- |
| `make` | GNU Make 4.4.1 | `make-1:4.4.1-12.fc44.x86_64` |
| `shell` (`/usr/bin/bash`) | GNU bash 5.3.9(1) | `bash-5.3.9-3.fc44.x86_64` |
| `python3` | Python 3.14.8 | `python3-3.14.8-1.fc44.x86_64` |
| `cross_gcc`, `cross_gcc_cc1`, `cross_gcc_collect2` | riscv64-linux-gnu-gcc 16.2.1 20260819 | `gcc-riscv64-linux-gnu-16.2.1-1.fc44.x86_64` |
| `cross_as`, `cross_ld`, `cross_nm`, `cross_objcopy`, `cross_objdump`, `cross_readelf`, `cross_size` | GNU binutils 2.46.1 | `binutils-riscv64-linux-gnu-2.46.1-1.fc44.x86_64` |
| `clang`, `host_clang` | clang 22.1.8 | `clang-22.1.8-4.fc44.x86_64` |
| `lld` (`ld.lld`) | LLD 22.1.8 | `lld-22.1.8-4.fc44.x86_64` |
| `host_gcc`, `host_gcc_collect2` | gcc 16.2.1 20260819 | `gcc-16.2.1-2.fc44.x86_64` |
| `host_gcc_cc1` | GNU C23 16.2.1 | `cpp-16.2.1-2.fc44.x86_64` |
| `host_as`, `host_ld` | GNU binutils 2.46.1 | `binutils-2.46.1-1.fc44.x86_64` |
| `qemu` (`qemu-system-riscv64`) | QEMU 10.2.2 | `qemu-system-riscv-core-2:10.2.2-1.fc44.x86_64` |
| `dtc` | DTC 1.8.1 | `dtc-1.8.1-6.fc44.x86_64` |
| `sha256sum` | GNU coreutils 9.10 | `coreutils-9.10-5.fc44.x86_64` |
| `rpm` | RPM 6.0.2 | `rpm-6.0.2-1.fc44.x86_64` |
| `git` | git 2.56.0 | `git-core-2.56.0-1.fc44.x86_64` |
| `podman` (host-only) | podman 5.8.9 | `podman-5:5.8.9-1.fc44.x86_64` |
| `ssh` (host-only, `-V`) | OpenSSH_10.2p1, OpenSSL 3.5.9 | `openssh-clients-10.2p1-16.fc44.x86_64` (`-14` until the refresh on `l1`) |
| `scp` (host-only) | its usage line, exit status 1 (no version option) | `openssh-clients-10.2p1-16.fc44.x86_64` (`-14` until the refresh on `l1`) |
| `mke2fs` (host-only, `-V`; M5-3) | mke2fs 1.47.3 (8-Jul-2025) | `e2fsprogs-1.47.3-4.fc44.x86_64` |
| `sfdisk` (host-only; M5-3) | sfdisk from util-linux 2.41.5 | `util-linux-2.41.5-1.fc44.x86_64` |
| `tmux` (host-only, `-V`; M5, `0e733e76`) | tmux 3.8 | `tmux-3.8-2.fc44.x86_64` |

The pins are Linux `v7.2` (commit
`8d3ae59288f1e7d58d76558a6ee96d533bc5019f`, tag object
`237a1c39e8dfd3e1c6f1f023eea37a48ec04cc63`), OpenSBI `v1.6` at the full
commit `bd613dd92113f683052acfb23d9dc8ba60029e0a` (the commit B1's and
B2's makefiles pin as `OPENSBI_COMMIT`, and the `HEAD` of B1's checkout
under `build/k3-b1/opensbi-src`), since M5-3 the U-Boot rehearsal's
U-Boot (`MVP_PIN_UBOOT_TAG` `v2022.10`, `MVP_PIN_UBOOT_COMMIT`
`4debc57a3da6c3f4d3f89a637e99206f4cea0a96`, `MVP_PIN_UBOOT_DEFCONFIG`
`qemu-riscv64_smode_defconfig`, `MVP_PIN_UBOOT_BUILD_SCRIPT`
`bringup/k3-b3/tests/build-uboot.sh`, and `MVP_PIN_UBOOT_BIN_SHA256`
`d96d1c22c67b…`, the binary's), and `MVP_CLOSURE_SHA256`, which binds
the closure below.
Beyond Q8's list, the lock also holds the compilers' `cc1` and `collect2`
and the host assembler and linker, which every build executes, and both
Clang roles, because the cross and host compilers are one executable used
two ways.

The host-only roles (Plan revision M0-B.4), listed in
`MVP_TOOL_HOST_ONLY_ROLES`, are the tools that run on the host only:
podman, which `mvp evaluate` runs by the lock's command, and ssh and scp,
which the board tools run; since M5, mke2fs and sfdisk, which make the
U-Boot rehearsal's disk, and tmux, through which the console tool types
at U-Boot. `check` verifies them with the rest on the
host. Inside the clean evaluator it skips them: it recognizes the
evaluator by `/etc/mvp-evaluator-rpms.txt`, the package list the
Containerfile records, and only if that list names exactly the packages
`rpm -qa` reports, so neither an environment variable nor a stale file
can claim to be the evaluator. Their packages are not closure roots. scp
has no version option; run bare, it prints its usage line and exits 1,
and that line stands in for its version, while its SHA-256 and package
identify it.

```text
BE_MVP_LOCK_SELF_TEST: PASS cases=46
BE_MVP_FETCH_SELF_TEST: PASS cases=39
BE_MVP_LOCK: PASS roles=29 host_only_skipped=0 closure=259 lock_sha256=6e99262f04a1
```

(On `l1`, 2026-10-26, `./mvp/mvp tool-lock check`; the last line read
`closure=257 lock_sha256=9513ece84af3` at M0-B and `closure=257
lock_sha256=8df124b9b362` at `804fa95f`. With M5's roles, in M5-4's
`./mvp/mvp check` on 2026-10-30: `BE_MVP_LOCK_SELF_TEST: PASS cases=50`
and `BE_MVP_LOCK: PASS roles=32 host_only_skipped=0 closure=259
lock_sha256=2f1b732dcf24`.)

`tools/lock/closure.txt` lists 259 packages by exact NEVRA (257 until the
refresh on `l1`), each with the
SHA-256 of its RPM file (Plan revision M0-B.1): the owners of every
locked executable but the host-only roles' and the support packages the
checks run (ShellCheck, bc, rsync, diffutils, findutils, gawk, grep, sed,
and glibc-devel), with their transitive hard requirements resolved
against the installed packages, offline, by
`dnf -C repoquery --installed --providers-of=requires --recursive` (dnf5's
form of `repoquery --resolve --requires --recursive`; weak dependencies
are not followed; without dnf, `rpm -q --requires` is walked through
`rpm -q --whatprovides`). Because the resolution runs against the installed
packages, the closure depends on the host's installed set as well as on
the roles (open item 39). B3's pinned `m4`, `bison`, and `flex` RPMs,
which the kernel build needs and the laptop `lx2` lacks, are added by NEVRA; the
base image's own release, repository, and key packages are left out. The
digests were derived once by `tools/evaluator/fetch-closure.py --record`
from files verified two ways (see [Plan revision M0-B](#plan-revision-m0-b));
`refresh` keeps each kept NEVRA's digest, and a new NEVRA's stays pending,
failing `check`, until `--record` derives it. The file's header records
the method.

## The clean evaluator

`tools/evaluator/evaluate.sh` (`./mvp/mvp evaluate`) runs these steps, each
recorded under `build/mvp-evaluator/record/<UTC stamp>/` and its result in
`evaluate.txt`:

1. **The host's tool lock:** `tool-lock.py check`, all 29 roles, podman
   among them, which the steps below run by the lock's command
   (`lock.txt`).
2. **The host's last check:** its bundle (`build/mvp/evidence/check`) must
   verify and hold the host's images as they are now.
3. **The closure's RPMs** (`fetch.txt`): `tools/evaluator/fetch-closure.py`
   puts each in the verified cache (`MVP_EVALUATOR_RPMS`, default
   `build/mvp-evaluator/rpms`), fetching only what is missing (Plan
   revision M0-B.2).
4. **The image,** if it is absent: `podman build --security-opt
   label=disable -v CACHE:/rpms:ro` of `tools/evaluator/Containerfile`
   (`build.log`), tagged `localhost/beryllium-mvp-evaluator:<12 hex digits
   of the closure's SHA-256>-<12 of the Containerfile's>` and labelled
   with both full digests, which are checked; then the image's package
   list (`rpms.txt`) and removals (`swap.txt`).
5. **`mvp check` inside** (`check.log`), with `podman run --rm --init
   --network=none --security-opt label=disable`: the source tree
   read-only at its own path, a separate writable build tree
   (`build/mvp-evaluator/build`) mounted over `build/`, B1's OpenSBI
   firmware read-only, and a local Linux mirror read-only at
   `/mnt/linux-mirror` as `LINUX_GIT`, under `env -i PATH=/usr/bin
   LC_ALL=C LANG=C SHELL=/bin/bash GIT_OPTIONAL_LOCKS=0`. It runs the tool
   lock first, against the same lock, its host-only roles skipped, and
   ends with its own bundle.
6. **The comparison** (`image-identity.txt`): the evaluator's
   `images.sha256` must equal the host's, image by image
   (`tools/evidence.py --compare-images`).

`tools/evaluator/Containerfile` starts from the same digest-pinned base as
`model/Containerfile`
(`registry.fedoraproject.org/fedora@sha256:daf897be...a000cf0`) and copies
in the closure. One step then checks every cached RPM's SHA-256 against
the closure (`sha256sum --check --strict`), records the base packages it
will remove, and installs the closure's local files (257 through
`804fa95f`, 259 since the refresh on `l1`) from `/rpms` in one
`dnf5 do` transaction with every repository disabled
(`--disablerepo='*'`), no weak dependencies, and
`clean_requirements_on_remove` off, removing exactly these base packages
by name (Plan revision M0-B.3; open item 27; as built at `67731e4c` and
`804fa95f` from the 257-package closure, and on `l1` at the M0-6 content
from the 259-package closure):

| Removed by name | Why | In its place |
| --- | --- | --- |
| `systemd-standalone-sysusers-259.7-1.fc44` | Conflicts with the closure's `systemd-sysusers` | `systemd-sysusers-259.10-1.fc44` (the plan's swap) |
| `glibc-minimal-langpack-2.43-7.fc44` | Requires `glibc = 2.43-7.fc44`; the closure's glibc is `2.43-9` | The closure's `glibc-all-langpacks-2.43-9.fc44`, which provides `glibc-langpack` |
| `rpm-build-libs-6.0.1-2.fc44`, `rpm-sign-libs-6.0.1-2.fc44` | Require `rpm-libs = 6.0.1-2.fc44`; the closure's is `6.0.2-1` | Nothing |
| `dnf5-plugins-5.4.2.1-1.fc44` | Requires `librpmbuild.so.10`, which `rpm-build-libs` provides | Nothing |

It then requires every closure NEVRA with `rpm -q` and each removed
package's absence, runs `dnf5 clean all`, and records the removals and
the swap's install as `/etc/mvp-evaluator-swap.txt` and `rpm -qa | sort`
as `/etc/mvp-evaluator-rpms.txt`. No downgrade is needed, and no
`--allowerasing`, `--skip-unavailable`, `--skip-broken`, or `--nobest` is
used. dnf5 skips OpenPGP checks for local files; the SHA-256 check
against digests recorded from signature-verified files stands in for
them. The reproducibility wording is "digest-pinned base plus recorded
closure with per-RPM digests" (S1 H32): the base is pinned by digest and
each RPM by SHA-256, and the remaining assumption is that some source
keeps the exact bytes, which the digests verify from any source.

```sh
mvp/tools/evaluator/fetch-closure.py              # every closure RPM, verified (evaluate.sh)
mvp/tools/evaluator/fetch-closure.py --record     # derive the digests once (responsible human)
mvp/tools/evaluator/fetch-closure.py --self-test  # offline (tool-lock-check)
```

`evaluate.sh` also takes `MVP_EVALUATOR_BUILD` (the hidden build tree),
`MVP_LINUX_MIRROR` (default the host's `build/mvp/linux-src`),
`MVP_OPENSBI_FW` (default B1's build), and `MVP_RPM_CACHE` (a directory of
exact RPMs the fetch tries first). Run on the laptop `lx2`
(`podman version 5.8.9`), it passed at `67731e4c` and `804fa95f`, and every
image equalled the host's (see
[Results](#plan-revision-m0-b-at-67731e4c-2026-10-24)); on `l1`, whose
podman matches the same lock role byte for byte, it passed at the M0-6
content after the account's stale rootless podman store was moved aside
(see [Results](#the-host-move-and-the-lock-refresh-on-l1-2026-10-26);
open item 43).

## Guest

The guest inputs are B7's, built by B7's method with MVP names: the
pinned upstream Linux `v7.2`, uniprocessor, with B6's unchanged Kconfig
fragment and fetch script (`bringup/k3-b6/guest/b6-kernel.config`,
`bringup/k3-b6/scripts/fetch-linux.sh`, used by path), since M1-4
followed by the MVP's own fragment, `guest/mvp-kernel.config`
(`CONFIG_DEVMEM=y` and `CONFIG_STRICT_DEVMEM=y`; M1 plan, Q2 and Q16; and
since M2-4 `CONFIG_MODULES=y`; M2 plan, Q16); a static nolibc init that
prints `MVPINIT` lines and, since M1-4, runs a writer's or a reader's
role from its arguments (`be.role=`, `be.channel=`, `be.deny=`), its
denied accesses in a forked child (Plan revision M1-A), and since M2-4
the host's or the protected domain's (`be.role=host` or `prot`,
`be.pages=`, `be.deny=`); since M2-4 one out-of-tree module, the
management call; and one DTB per domain with the model `Beryllium MVP
guest`, the compatible `beryllium,mvp-guest`, and `bootargs` ending
`-- be.guest=<g>`, which te-poc's pair (M1-3) and anchor's (M2-1) follow
with each init's role arguments; anchor's G0 DTB ends `-- be.guest=0
be.role=host be.pages=0x84000000,0x84001000,0x84002000
be.deny=store@0x84001ff8,load@0x84002000,load@0x114000000,load@0x102064000`
and its G1 DTB `-- be.guest=1 be.role=prot
be.pages=0x84000000,0x84001000,0x84002000 be.deny=store@0x84000ff8`.
B0's retention, summary, and rehearsal `mkcpio.py` tools
stay where they are and are used by path, as B7 uses them: the
rehearsal's `mkcpio.py`, the campaign's `summarize-runs.py`, and the board
record's `retain-results.py` (M0-4). `guest/pins.txt` pins every output
(at `f687b791`; M0's pins are `tests/fixtures/m0-guest-pins.txt` and M1's
`tests/fixtures/m1-guest-pins.txt`):

| Output | SHA-256 | Bytes |
| --- | --- | --- |
| `init` | `dca88d1861b025c1cfbe283a1339c4f40a3b117bd94936d76193d84908aa7530` | 11,408 |
| `be-mgmt.ko` (M2-4) | `67529a9dca0f682d4130993040fb7c17f88f75a823b96965b3b72da78ae439d1` | 5,736 |
| `Image` | `c7ae03e6b26e1433bb1cdcd995467b5df2dec61cb8ed1c38ede0d4458c4799ed` | 1,899,716 |
| `mvp-guest-g0.dtb` | `f51be0c7c1cf25f11eeb721dc4dcf19d34902794cf3f15cd43df0255523e0783` | 4,096 |
| `mvp-guest-g1.dtb` | `ea0a5196104cbf48001ae1d14fb67a2587f3e1859644072446baad4b6780bcea` | 4,096 |
| `mvp-guest-g1-init-exit.dtb` | `7cc47c2f65499ca72454588b181d7cf8ebf5a9b45818de2f0e054759a0684afd` | 4,096 |
| `mvp-guest-g0-rdcycle.dtb` | `4043572a9cbcdaee41c51d91ed83ebc0b622352167173f7ced97bbcc15c6de66` | 4,096 |
| `mvp-guest-g0-sbi-time.dtb` | `568b90cee8cf8bb9a06f423a0efb212f9ffdd16b2a9384fac983bdf990b79cbf` | 4,096 |
| `mvp-guest-g1-sbi-time.dtb` | `d8c1f4d8f43b7ce569ebe5187237c2c21f945cf3eae8c05e27407d566e7d45e0` | 4,096 |
| `mvp-guest-g0-reference.dtb` | `9a523ff8e0834bca6bc09b09aa43d6c7a0bc94fa307a88105c02ce5469a308e1` | 4,096 |
| `mvp-guest-g1-reference.dtb` | `0e079e289a434d44d9c965617c136c8552de0d0ccad305a9e2ea249f044bceb5` | 4,096 |
| `mvp-guest-g0-te-poc.dtb` (M1-3) | `5aca65d93e8488f44f0c8a746993ce8ceb231542fc9aa64bd491ede90fb9156b` | 4,096 |
| `mvp-guest-g1-te-poc.dtb` (M1-3) | `d761366dce46edb1fe2ecf17bc517c84f79b4630c1af332d5be58855c3cafef0` | 4,096 |
| `mvp-guest-g0-anchor.dtb` (M2-1) | `55acfb900d8e43daee8f5c3d2b1c13e624f8af7e8cc97dd900d6f23d8728c71b` | 4,096 |
| `mvp-guest-g1-anchor.dtb` (M2-1) | `903799a1d59ba17851076a9be688a8db992bd441a737137d64912e0bd6b6a025` | 4,096 |

The `Image`'s size (1,899,716 bytes) and `image_size` (`0x203fb0`) are
those of the kernel built with `CONFIG_MODULES=y` and the module since
M2-4 (M1's: 1,569,716 bytes and `0x1b3628`; B7's and M0's: 1,553,332
bytes and `0x1af628`); its
`text_offset` (`0x200000`) and banner (`Linux version 7.2.0
(be@beryllium) ... #1 PREEMPT Sun Aug 16 21:32:26 UTC 2026`) are B7's,
and its digest differs from B7's through the configuration and the
embedded initramfs, whose init is the MVP's and which since M2-4 holds
the module. The generated payload layout puts the kernel's `0x1cfcc4`
bytes at `0xa5000`, after the `0xa4000`-byte flat image (Plan revision
M0-A.1), G0's DTB at `0x275000`, and G1's at `0x276000`, ending the image
at `0x277000` (M1's, with its `0x17f3b4` kernel bytes, at `0x225000`,
`0x226000`, and `0x227000`; M0's, with its `0x17b3b4`, at `0x221000`,
`0x222000`, and `0x223000`; B7's, with its `0x34000`-byte image, at
`0x35000`, `0x1b1000`, `0x1b2000`, and `0x1b3000`).

**The module** (`guest/mgmt/be-mgmt.c`, M2-4; M2 plan, Q2, Q3, Q20, and
"Guest software"). A misc character device, `/dev/be-mgmt` at minor 243,
the first of the minors reserved for local use; the initramfs list
names the device node (`nod /dev/be-mgmt 0600 0 0 c 10 243`) and the
module's file (`/be-mgmt.ko`). Its one ioctl, `BE_MGMT_IOC_CALL` =
`_IOWR('B', 0x42, struct be_mgmt_call)` = `0xc0184242`, takes the FID
and the target, refuses a FID above `INT_MAX`, calls `sbi_ecall(0x08004245,
fid, target, 0, 0, 0, 0, 0)` through the kernel's exported `__sbi_ecall`,
and returns the call's SBI error code in the structure. The init and the
module each define the call's structure and the ioctl, and each asserts
its number, `0xc0184242` (open item 48). It is the repository's one
`GPL-2.0-only` file (Q20, answered by the responsible human), with
`MODULE_LICENSE("GPL")`; `tools/build-guest.sh`
builds it out of tree with Kbuild's `M=` and `MO=` against the pinned
tree's object directory under the same `KBUILD_BUILD_*` variables, after
vmlinux and before the Image, whose initramfs then holds it, and
`kernel-repro` compares it with the other outputs. Loading it, each
guest's kernel prints `be_mgmt: loading out-of-tree module taints
kernel.` (open item 52).

**The `.config` delta** (M2 plan, Q16). The final `.config` must differ
from M1's (B6's fragment and the MVP's without M2's line) in exactly
sixteen lines, measured at M2-4 and listed in
`guest/mvp-kernel.config`'s comment, which `tools/build-guest.sh`
checks against its own list: `CONFIG_MODULES=y` and the lines it makes
visible, `CONFIG_DRIVER_DEFERRED_PROBE_TIMEOUT=10`, `CONFIG_EXECMEM=y`,
`CONFIG_MODPROBE_PATH="/sbin/modprobe"`, `CONFIG_MODULES_USE_ELF_RELA=y`,
and eleven `is not set` lines (`MODULE_ALLOW_MISSING_NAMESPACE_IMPORTS`,
`MODULE_COMPRESS`, `MODULE_FORCE_LOAD`, `MODULE_SIG`,
`MODULE_SRCVERSION_ALL`, `MODULE_UNLOAD`, `MODVERSIONS`,
`STRICT_MODULE_RWX`, `TEST_ASYNC_DRIVER_PROBE`, `TEST_LOCKUP`,
`TRIM_UNUSED_KSYMS`); M1's own delta from B6's fragment is unchanged.
B6's fragment's `# CONFIG_MODULES is not set` is the one value of B6's
that the MVP's fragment overrides (`config_values_overridden=CONFIG_MODULES`
in `build/mvp/guest/MVP-GUEST-BUILD.txt`).

**The roles' lines** (`guest/mvp-init.c`; M2 plan, "Guest software", Q8,
Q9). With `be.role=host` or `prot`, after `MVPINIT 02` the init loads
the module with `finit_module`, opens `/dev/be-mgmt`, maps through
`/dev/mem` the request and response pages read-write and, for `prot`,
the secret page read-only, and forks M1-A's child for `be.deny`, in
whose line 08 a store's `unchanged=1` now means that the word holds after
the store what it held before (open item 53); a failure prints its own
line 07, `MODULE`, `DEVICE`, or `PAGES`, with `error=`; then:

```text
MVPINIT 07 PAGES role=<host|prot> count=<2|3>
MVPINIT 08 DENIED n=<i> kind=<load|store> gpa=<g> va=<v> pc=<p> signo=<s> code=<c> observed=<0|1>[ unchanged=<0|1>]
MVPINIT 09 REQUEST n=<n> digest=<64 hex>
MVPINIT 09 REQUEST n=<n> timeout=1
MVPINIT 09 RESPONSE n=<n> digest=<64 hex>
MVPINIT 10 MGMT fid=<pause|terminate|f> target=<t> result=<r>
MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=<r>x8
```

The host writes requests 1 to 4 (the 64-byte message
`BE-MVP-M2-REQ-<n>`, zero-padded, at the request page's offset 64, a
fence, and `n` at offset 0), each answered within its deadline, then
calls `pause 0`, `terminate 0`, `pause 2`, FID 7 on 1, and the burst of
eight `terminate 0` (one line, its results run-length as `<r>x8` when all
are equal), then `pause 1`, request 5, which must go unanswered, and
`terminate 1`, then M0's steps, `RESULT`, and power-off. The protected
domain makes its two calls, `terminate 0` and `pause 0`, reads the
32-byte secret, which it never prints, and serves for ever: for each new
sequence number, HMAC-SHA-256 keyed by the secret over `n`'s eight
little-endian bytes and the 64-byte message, the digest at the response
page's offset 64, a fence, and `n` at offset 0. It prints no `RESULT` and
never powers off: the monitor pauses and terminates it. **The deadline**
(M2-4's follow-up, `f687b791`): the host polls the response page 1 ms
apart for at most one second of `CLOCK_MONOTONIC` time, not Q8's "2,000
polls at 1 ms", because the pinned kernel (`CONFIG_HZ=250`, no
high-resolution timers) rounds a 1 ms sleep up to a jiffy, so the fifth
request's bound took 20 s in QEMU (open item 51).

## Tests

| Test | Covers | Scenarios | Assertions |
| --- | --- | --- | --- |
| `tests/ring-test.c` (new) | Index lines and record sizes; every refused setup; every fill level of the smallest ring and each layout ring for eight payload lengths, with the exact refusal of a full ring, which never overwrites; one record at every 8-byte offset of the smallest ring for nine lengths; indices across 2^64; visibility only after publication, room only after release; the high-water mark; every header refusal (type, ring, domain, length, reserved word, padding, records crossing the head) and malformed heads; the writer's tail checks; calls on the other side's view; four 20,000-step pseudo-random runs checked record by record against a queue model, each ending in the exact refusal; the writer's reads of the reader's tail and of its own published head, checked against the queue model at every step (Plan revision M1-B); since M2-3, the management records' numbering and masks | 160 | 409,414 |
| `tests/hart-test.c` (new) | `hgatp`; every malformed binding; descriptors as filled; every block check, in order, both domains; the state page's index lines; every record type in every domain phase (77 cases), out-of-order records included; payload sizes, LINE bytes, times that go back, SHUTDOWN's consistency words; FAIL; the READY wait, the budget, a clock behind the start, a start near 2^64, the run-timeout variant; hart 0's round-robin drain on host rings (M0-C.1): two rings of 0 to 8 records each, one ring alone, a held ring, a writer as fast as the drain, the bound for each layout ring, refused arguments; the overlap at its edges (disjoint, touching, nested, exactly half, odd lengths, extremes); saturating counters; sticky failures; the printed LINE; 400 pseudo-random interleavings of two domains, each replayed with one record dropped, which must fail or stay unfinished; since M1-3, the channel's arguments to the control loop (`be_mvp_control_channel`) and the DENIAL step: the kind against the walked windows and the sealed record, the cause and injected cause, the GPA, the sequence, the exit time, a loop without the record, and SHUTDOWN's denial word reconciled with the records drained; since M2-3, the DENIAL step against anchor's sealed pages and `be_mvp_control_pages`, and the management requests: Instance 3's sequence, each decision answered at once, each delivery pending until its target's PAUSED or TERMINATED, a second request while one is pending, requests to a paused, a terminated, and a shut-down domain, a target that shuts down first, a request to oneself, the `no-grant-check` decision, a paused domain that does not end the run and a terminated one that does, SHUTDOWN's management word, the PING not asked of a domain about to stop, every malformed request and transition, and `be_mvp_control_mgmt`'s input | 843 | 176,870 |
| `tests/sbi-test.c` (from B7's) | B7's SBI rows on one hart's state; the IPI exit from VS and VU; B7's slice and `wfi` exits now terminal; the console's LINE records through the ring and `be_mvp_line_output`, CR, every byte value, a full buffer, flush in any phase, a full ring; two harts' consoles drained in pseudo-random order; PING and PONG, an empty ring, another record, a malformed or full ring; READY, ENTERED, SHUTDOWN, and FAIL through hart 0's control loop; the HSM and IPI checks; `BE_MVP:02`'s census (M0-A.2): every boot hart, every second STARTED hart, every other state and error, the `hart-start` variant's absent hart, a one-domain run; per-hart counters; version 3; the shutdown grid; the census replays per hart with the IPI; since M1-3, the denial action and the counters (`exits = sbi + ipi + denials`), and the DENIAL record's twelve words, its refusals, a full ring, and hart 0's loop reconciling SHUTDOWN's denial word; since Plan revision M1-B, the ACK wait's decision (`be_mvp_ack_wait_step`) in ten scenarios, the board's backlog replayed through a real ring among them; since M2-3, `be_mvp_mgmt_decide` over every row of Instance 3's grant in every target state, other functions, targets and requesters that are no domain, and other tables; the extension absent at version 3 and present at version 4; the calls counted in `mgmt` and the counters' sum; MGMT_REQUEST and its refusals; the requester's wait (a PING served, every answer code, another request's answer, an order while waiting, a malformed or full ring); PAUSE and TERMINATE through the IPI, the paused and terminated waits and what they refuse; SHUTDOWN's management word; and hart 0's loop on the records the harts post | 130 | 16,208 |
| `tests/gstage-test.c` (from B7's) | B7's G-stage cases with a hart per root; the pair check's equal-hart and control-hart refusals; since M1-2, the channel: with none, M0's roots byte for byte from both builder entries and M0's maps from both walker entries; the plan's two roots with their level-1 pointers (`0x4080e401`, `0x40810401`) and leaves (`0x460000d7`, `0x46000053`) checked against Instance 2's record, and the roles the other way round; pages at the edges of their rules; every page rule refused by the builder and the walker; the walker's one new rule; the channel check's every refusal; and the plan's host mutations (a level-0 page with a second leaf, the reader's leaf with `W`, a second page both roots map); since M2-2, the pages: the plan's two roots with their level-0 entries (G0's request `0x460000d7`, response `0x46000453`, no secret leaf; G1's `0x46000053`, `0x460004d7`, and secret `0x46000853`); both builder variants' leaves refused by the page check with the images' DETAIL values; every page rule refused by the builder and the walker; the walker's rules on a root with pages; every bit of every nonzero entry of each root; and the page check's every refusal | 44 | 39,647 |
| `tests/payload-test.c` (from B7's) | B7's payload cases with harts in the windows; the kernel at `0xa5000` after the `0xa4000`-byte flat image (M0-A.1); the hart region and the MVP region against the staged image; the pinned payload and every variant DTB; since M1-3, the channel page against the staged image and the two te-poc DTBs; since M2-2, the whole shared extent, and (M2-1) anchor's two DTBs in each slot | 8 | 646 |
| `tests/deny-test.c` (new, M1-3) | `be_mvp_denial_decide` over te-poc's two roots, built and walked with their channel leaves, and a root without one: every cause on both sides of each region boundary (the window, the channel page, the neighbouring page); every `hstatus` SPV, SPVP, and GVA value; `htval` below 2^39 and each alias bit above it; the GPA from `htval` and `stval`'s low bits; every `htinst` form (zero, a transformed load, store, and AMO, their compressed forms, each pseudoinstruction, a wrong opcode or cause, a value of 2^32 or more); every `vstvec` mode; an image that does not accept denials; the injected values and the `vsstatus` transform for every SIE, SPIE, and SPP combination; that the decision writes nothing but its result; the injection helper's words, readback comparison, and register names; since M2-3, anchor's two roots with their walked leaves of the three pages: every cause at each page's edges and beside them, and both roles' declared denials (`read-only` stores to the response and request pages, `unmapped` loads of the secret page, the protected window, and the MVP region) | 38 | 2,933 |
| `tests/sha256-test.c` (new, M2-2) | SHA-256 on the FIPS 180-4 vectors (`""`, `abc`, the 448-bit and 896-bit messages, one million `a`), every padding boundary from 55 to 65 bytes, the incremental API against the one-shot at every split of a 300-byte message and byte by byte, and HMAC-SHA-256 on RFC 4231 test cases 1 to 7 and keys of 64 and 65 bytes | 16 | 626 |

The seven tests (`HOST_TESTS`; `deny` since M1-3, `sha256` since M2-2)
each print exactly three
lines, `BE_MVP_<NAME>_CHECK: PASS`, `scenarios=<n>`, and
`assertions=<n>`; the GCC and Clang outputs must be identical and the
counts are pinned in the `Makefile`. The tests build
with the accepted warning flags (`-Werror -Wconversion` and the rest) under
both compilers, and `target-check` compiles the six pure-C files for the
target with both toolchains, freestanding, at `-Os`.

## Harness (M0-4)

The plan's harness stages ("Scenarios and the harness") as M0-4 builds
them, as M1-4 and M1-5 extend them for `te-poc` (M1 plan, "Scenarios
and the harness"), and as M2-5 and Plan revision M2-A extend them for
`anchor` (M2 plan, "Scenarios and the harness", "Tests and evidence",
and "Plan revision M2-A"). `make -C mvp check` runs every stage but the
kernel rebuild, the kexec rehearsal, the evaluator, and the board. Since
M5-2 and M5-3 the kexec rehearsal and the kexec board path below are
history: the U-Boot rehearsal in QEMU and the board session from system
reset replaced them, and the capture checker's `kexec` mode stays,
test-only (see [M5-1 to M5-4](#m5-1-to-m5-4-2026-10-29-and-30)).

**Check: `tests/check-capture.py` (new).** One parser run per capture (S1
H26) splits it into hart 0's monitor stream (the shim's, B3's, R3's, and
the `BE_MVP:` lines) and each domain's prefixed stream, and judges each
stream on its own against its image's expectation file, which
`tools/gen-scenario.py` writes from the scenario; the checker names no
scenario line itself. Its rules (its docstring has them in full):

- **The capture:** only loader output before the first marker line; from
  there every line whole, printable, and of one tag; no domain line that
  mixes in a second line.
- **The loader:** direct mode, one banner boot hart and the run's SBI
  version; kexec mode, Linux's handoff lines once each and in order, with
  the loader's FDT slot, which the SHIM line repeats.
- **The start rule (M0-A.2):** a boot hart B other than 0 prints
  `BE_MVP_SHIM: boot_hart=0x<B> starting hart 0` first, B being the
  banner's or the handoff's hart, and `BE_MVP:02` prints `started=<B>`
  (decimal) with B STARTED; without that line it prints `started=none`;
  the `shim-rule` variant prints its rule line and `started=none`.
- **Order and cardinality:** the control lines once each and in order;
  per domain `:09` to `:12` in order, the two domains' chains in either
  hart order; `:13`, `:14`, and no line of any stream after `:14`. Each
  domain's stream holds its required lines once each and in order, with
  its own guest ID, every `MVPINIT` line once, no rejected substring, and
  nothing outside its own `:10` to `:12`.
- **Counters:** exact where the expectation fixes them (`ipi=1`,
  `srst=1`, `time`), within ranges elsewhere (`exits`; `ring_peak` at
  most half the ring, stop condition 3); `exits = sbi + ipi`
  (`+ denials` where the scenario accepts denials, M1-4), `sbi` the
  sum of its classes, `lines` the domain's printed lines, `records` every
  drained line, and every tick count within the budget.
- **Concurrency (Q5):** `overlap_ticks` the intersection of the two
  domains' entered-to-shutdown intervals, at least half the shorter; and
  at least K = 8 alternations between the two domains' lines. With hart
  0's round-robin drain (Plan revision M0-C.2), two domains that produce
  lines at once alternate on the console at least once per wake in which
  both rings hold a record; a console-bound hart 0 lowers the wakes, not
  the alternation within a wake.
- **Fields:** `:01`'s, with `mvp_region=0x102064000 mvp_bytes=0x40000
  image_bytes=0xa4000`; `:04` and `:06` against the guest pins; `:09`'s
  WARL `hedeleg`.
- **Negative variants:** the first `BE_MVP:FAIL` of the declared class
  after the declared group, its `DETAIL` in the class's form, naming the
  binding's domain and hart and a cause that fits, then at most
  `SRST_RETURNED`. `ring-full` (M0-A.3): both `:10`, then nothing from
  hart 0, only each domain hart's `FAIL ring` and its `DETAIL`, which
  names a domain hart, and no `:11` to `:14`.
- **Probe images:** their lines in place, and the probe table's stop
  facts as `STOP`.
- **Denials, the channel, and the report (M1-4; schema-v2
  expectations):** for each domain the DENY lines, its `MVPINIT 08`
  reports, and the expected denials agree in number, order, and fields
  (`seq`; `gpa`; `htval` the GPA shifted right by 2, compared as 64-bit
  values; `stval` = `va`; `sepc` = `pc`; cause and injected cause 21 and
  5, or 23 and 7, by kind; the kind; `htinst` zero or the transformed
  form; one `vstvec`, in Direct mode), each DENY line before its report,
  and each report `signo=11 code=2 observed=1`, the store's also
  `unchanged=1`; the writer's and reader's `MVPINIT 07` digests equal,
  with `match=1`; `:03 CHANNEL_CHECKED` with the report's channel, both
  leaves from its derived flags, and its configuration identity, and each
  window's `:03` line with its grant; and the report given with `--report`
  itself: its SHA-256 the expectation's, six grants with their rules, one
  declared flow, every check `pass`. Only hart 0's lines are terminal, a
  domain line never, whatever it holds. `reader-write`'s channel DETAIL
  and `no-inject`'s exit DETAIL (either domain's declared fault) are
  accepted as declared.
- **The pages, the measurement, the requests, and management (M2-5;
  schema-v3 expectations, `be-mvp-expect-v3`, with M1's rules
  unchanged):** `:03 PAGE_CHECKED` for each of the report's three pages
  (kind, ends, GPA, HPA, size, both leaves from its derived flags, the
  secret page's configuration identity), `:05 PAGE_CLEARED` for each
  channel page and `SECRET_PLACED` for the secret page (`bytes=0x20`),
  and `:06 MEASURED` in their places; the measurement recomputed from the
  build outputs, SHA-256 over the measured domain's kernel and DTB
  (`--kernel`, `--dtb`), its secret page (the expectation's `secret_hex`
  zero-padded to 4 KiB), and the report's configuration identity, equal
  to `MEASURED`'s `sha256=` and `bytes=` and to `DOMAIN_TERMINATED`'s
  `sha256=`; each `MVPINIT 09 REQUEST` and `RESPONSE` digest the
  checker's own HMAC-SHA-256 (Python's `hmac` and `hashlib`; the key the
  secret, the message the request's number as 8 little-endian bytes and
  its text zero-padded to 64 bytes), the requester's and the server's
  equal per request, and the fifth only on the requester's side, as
  `timeout=1`, after the guest's report of its `pause` call; hart 0's
  `BE_MVP:MGMT` lines, per domain and in order, against the guests'
  `MVPINIT 10 MGMT` lines (a burst line standing for its eight calls and
  their run-length results; FID 7 with a guest line, answered -2 on its
  hart, and no line on hart 0) and the expectation's `mgmt` sequences
  (`seq`, `fid`, `target`, `result`, `target_state`), each before its
  call's report, a delivered one after its target's `DOMAIN_PAUSED` or
  `DOMAIN_TERMINATED`, which names its requester; `DOMAIN_TERMINATED`'s
  `exits=` equal to `DOMAIN_PAUSED`'s (the paused hart takes no further
  exit); the order `DOMAIN_PAUSED`, `DOMAIN_TERMINATED`, the host's
  `DOMAIN_SHUTDOWN`, `RUN_COMPLETE`, and no guest line after its domain's
  end; `sbi` the printed terms plus `mgmt` (`sbi_terms`), `mgmt` exact
  (`sbi_derived`: 13 for the host and 2 for the protected domain), and
  `refused` exact (the host's 1, FID 7); and every request a drained
  record. The negatives' outcomes as declared: `secret-shared` and
  `response-writable` fail `gstage` with their exact `DETAIL page=…`,
  `wrong-measurement` fails `measurement` with `computed=` the checker's
  own value and `expected=` the variant's (`expected_hex`), and
  `no-grant-check` shows its required lines (the protected domain's
  delivered `terminate 0`, the host's `DOMAIN_TERMINATED`) before
  `FAIL run-timeout`, M0's DETAIL with `ticks=` at least its 2^27-tick
  budget, and the host's lines, denials, and requests a prefix of its
  own, the server answering only a first run of them. The management
  module's `be_mgmt: loading out-of-tree module taints kernel.` is an
  expected kernel line of each domain (after `UNAME`), not a rejected
  one; the rejected substrings are M1's.
- **The IPI probe in a management wait (Plan revision M2-A.1;
  `ping_findings`):** a `BE_MVP:11 IPI_PROBE` line shows `spv=1`, M0's
  rule, or, only where the expectation is a v3 one with the management
  extension (`mgmt`: `anchor` and its runtime variants, whose probe
  template carries `spv=<S>`), `spv=0` with its `received=` inside a
  management wait of its own hart, `[ticks, ticks + service]` of a
  `BE_MVP:MGMT` line naming that hart, both ticks since the barrier as
  the monitor prints them: a hart that waits in HS for hart 0's
  `MGMT_RESULT` serves a PING it finds meanwhile (Q14), and its PONG
  shows SPV 0. Any other `spv=0` is a finding that names the revision:
  `… spv=0, a PONG answered in HS, but the image has no management
  extension, so its hart never waits in HS`, or `… but received=<r> lies
  in no management wait of hart <h>, [ticks, ticks + service] of a
  BE_MVP:MGMT line naming it`. A probe so served is recorded among the
  costs, `g<d>_ping_in_mgmt_wait=1` and `g<d>_ping_mgmt_seq`, the request
  whose wait holds it. `two-guests` and `te-poc` keep M0's literal
  `spv=1`.

Its verdicts are `PASS`, `FAIL`, `REFUSED`, and `STOP` (exit status 0, 1, 3,
and 4). `REFUSED` is M0-A.2's failed precondition: `:02` names a domain hart
of the run as `started=<h>`, and exactly `BE_MVP:FAIL firmware` follows; it
is never `PASS`. `--self-test` runs 70 cases since Plan revision M2-A (36
at M0-C, 45 at M1-4, 47 at M1-6, 65 at M2-5) on the twenty-three fixtures
in `tests/fixtures/` (below) and on
B7's recorded COM260 kexec handoff (`bringup/k3-b7/results/20261008-com260/`);
each fixture is judged against the guest pins it was captured with: M0's
twelve against `tests/fixtures/m0-guest-pins.txt` (the M0 result's
`guest/pins.txt` verbatim, bound by its SHA-256 `094df1904a1f...`), M1's
five, since M2-5, against `tests/fixtures/m1-guest-pins.txt` (M1's
`guest/pins.txt` at `ff84533c` verbatim, bound by its SHA-256
`229146c1f0a8...`; M2-4's kernel and pins changed under them) and
te-poc's report, and M2's six (since M2-A the first M2 board campaign's
stopped `anchor` capture among them, judged PASS) against
`guest/pins.txt`, anchor's report, and the measured inputs; each keeps
its verdict. `--mutation-test` applies 229 mutations since M2-A (154 at
M0, 170 at M1-4, 224 at M2-5), the plan's named ones and
seeded ones (seed
`0x4d30`), each mapped to the claim it must fail (S1 H39): a missing line in
either stream, a domain or hart other than the binding's, a mixed line, an
overlap below the floor, fewer than K alternations, a missing `ipi=1`, wrong
sums, one shutdown only, a line after `:14`, a `started=` that differs from
the shim's line, and more (M0's 154); and, since M1-4, the M1 plan's fifteen
capture rows on the `te-poc` fixture, one in two forms: a DENY line's `gpa`
changed, removed, duplicated, or moved after its report; a load's
`injected=0x7`; G1's two DENY lines swapped; `kind=read-only` outside the
channel page; a report's `pc` changed; `htval` with bit 39 set; the reader's
`match=0` or the digests differing; the reader's `unchanged=0`;
`reader_pte=0x460000d7`; one digit of `config` changed; a report with a
seventh grant; and a report flow `declared: no`; and, since M2-5, 30 named
rows on the anchor fixtures, one for each new rule: a `REQUEST` or
`RESPONSE` digest one digit off; the timeout before the `pause` call's
report; a response to the fifth request; a `BE_MVP:MGMT` line removed; a
denied request's result `-3` for `-4`; two requests' lines swapped; a
request's line after its call's report; the `pause`'s line before
`DOMAIN_PAUSED`; a burst of 7 with 8 results; FID 7's request on hart 0,
or answered 0; the host's `refused=0`; `sbi` and `exits` one less;
`records` without the requests; `MEASURED` one digit off or one byte
longer; `DOMAIN_TERMINATED`'s `sha256` one digit off, or with one more
exit, or after the host's shutdown; a G0 line after the host's shutdown;
a protected `RESULT` line; the secret page's leaf with W; `SECRET_PLACED`
at the response page; `wrong-measurement`'s `computed=` one digit off;
`no-grant-check`'s DETAIL below 2^27 ticks, its `terminate 0` line
removed, a response to request 3 alone, and a gap in the host's lines; and
a report with `pause` alone among the management grants; and 24 seeded
mutations of the anchor fixture, drawn as for M0's three bases, after
theirs; and, since M2-A, five named rows for the probe's rule: `spv=0` on
`two-guests`' hart 2, with no management extension (M0's named rows 82
to 83), and four of anchor's (30 to 34), the QEMU anchor fixture's hart 2
answering `spv=0` before its first request, and on the board capture
(the mutation base `k3anchor`, judged as the board recorded it; 13 bases)
the PING received a tick before its request, a tick after its answer,
and with the `BE_MVP:MGMT` line whose wait holds it removed. Every one is
rejected for
its own reason. The plan's harness table names `tests/mutate-*.py`; M0 keeps
each checker's mutations in the checker (`check-image.py --mutation-test`
since M0-3, `check-capture.py --mutation-test`), so there is no separate
file.

The fixtures (CRs removed). The QEMU captures are direct boots with
eight harts, on the `k3-like` machine but where noted; the six that the
drain order changes were made again from the M0-C images (Plan revision
M0-C.2), the five that stop before any drain or drain one ring are
M0-4's, the four `te-poc` captures are M1-4's, from its images, and the
five `anchor` captures are M2-5's, each from a run of
`tests/run-qemu.sh` on its GCC image (`anchor/gcc/k3-like` and
`anchor/gcc/<variant>`), copied with CRs removed; the three board
captures are each the run that stopped a campaign, the last that of
M2-6's first (Plan revision M2-A):

| Fixture | Capture | Self-test and mutations |
| --- | --- | --- |
| `qemu-two-guests-gcc.log` | GCC scenario, boot hart 0; M0-C | The passing scenario; with B7's handoff, the kexec cases; the synthetic `exit-budget` case; the base of most named and seeded mutations |
| `qemu-two-guests-clang-hart6.log` | Clang scenario, boot hart 6 and the start rule; M0-C | The start rule, direct and kexec; the `started=` mutations |
| `qemu-shim-rule-gcc.log` | GCC `shim-rule`; M0-C | The rule line with `started=none` |
| `qemu-ring-full-gcc.log` | GCC `ring-full`, boot hart 0, both domain harts' fallbacks in turn; M0-C | The fallback, and cut mid-line; the fallback mutations |
| `qemu-ring-full-clang.log` | Clang `ring-full`, boot hart 4, the second hart's DETAIL cut by the first's shutdown; M0-C | The fallback cut short |
| `qemu-rdcycle-clang.log` | Clang `rdcycle`, boot hart 6; M0-C | A domain's exit failure, cause 22; its mutations |
| `qemu-payload-gcc.log` | GCC `payload`; M0-4 | A failure before any drain; the synthetic `sbi-3.0` case, from its banner |
| `qemu-plic-gcc-refused.log` | GCC scenario on `plic`, boot hart 1; M0-4 | REFUSED, direct and kexec |
| `qemu-probe-platform-gcc.log`, `qemu-probe-vmid-distinct-gcc.log`, `qemu-probe-vmid-shared-gcc.log` | GCC probe images; M0-4 | The probe lines, values, and stops |
| `k3-two-guests-gcc-stop6-alternations.log` | The COM260's first GCC scenario run, `20261025T022152Z`, kexec from hart 0 with Fedora's shutdown before it; stop-6 evidence from the board (M0-C) | FAIL with the alternation finding alone: 5 alternations, `records=138 wakes=3` |
| `k3-no-inject-gcc-stop6-fallback.log` | The COM260's first `no-inject` run, `20261027T094024Z`, GCC, kexec from hart 0 with Fedora's shutdown before it; stop-6 evidence from the board (M1-B) | FAIL against `no-inject`'s expectation with exactly its six findings: the guest lines after the first FAIL, the first FAIL without its DETAIL, and the second FAIL and both DETAIL lines |
| `qemu-te-poc-gcc.log` | GCC `te-poc`, boot hart 0; M1-4 | The channel and three denials, direct, with the report, and in kexec form with B7's handoff; FAIL without the report; a domain line holding `:14`'s text is no terminal line; the base of M1's mutations |
| `qemu-reader-write-gcc.log` | GCC `reader-write`, boot hart 0; M1-4 | The channel check's refusal of the reader's `W`, as declared |
| `qemu-no-inject-gcc.log` | GCC `no-inject`, boot hart 0, domain 0's load first; M1-4 | The first denied access ends the run, as declared |
| `qemu-te-poc-gcc-stop6-pid1.log` | GCC `te-poc` with M1-4's first init, boot hart 5, the denied accesses made by pid 1; stop-6 evidence (M1-A) | FAIL with its three `unhandled signal` findings alone |
| `m0-guest-pins.txt` | Not a capture: the guest pins M0's twelve fixtures were captured with; M1-4 | Bound by SHA-256; M0's fixtures against M0's kernel and DTBs, and `qemu-two-guests-gcc.log` failing the current pins on the kernel alone |
| `qemu-anchor-gcc.log` | GCC `anchor`, boot hart 5 and the start rule; M2-5 | The pages, the measurement, the four requests with their digests, the fifteen requests on hart 0, the pause and the termination, direct, with the report and the measured inputs, and in kexec form with B7's handoff; FAIL without the measured inputs; the eleven edited copies (a wrong digest, a missing `MGMT` line, a wrong result code, FID 7's line on hart 0, `refused=0`, a `MEASURED` mismatch, a `DOMAIN_TERMINATED` sha mismatch, the order swapped, a guest line after the host's shutdown, a protected `RESULT` line, and, since M2-A, the protected domain's PONG `spv=0` before its first request), each FAIL; the base of M2's mutations |
| `qemu-secret-shared-gcc.log` | GCC `secret-shared`, boot hart 7; M2-5 | The page check refuses the secret page in the host's root, `FAIL gstage` with its `DETAIL page=2 …`, as declared |
| `qemu-response-writable-gcc.log` | GCC `response-writable`, boot hart 3; M2-5 | The page check refuses W in the host's response leaf, `FAIL gstage` with its `DETAIL page=1 …`, as declared |
| `qemu-wrong-measurement-gcc.log` | GCC `wrong-measurement`, boot hart 3; M2-5 | `FAIL measurement` before any domain hart starts, `computed=` the checker's own value and `expected=` the variant's, as declared; its mutation |
| `qemu-no-grant-check-gcc.log` | GCC `no-grant-check`, boot hart 4; M2-5 | The protected domain's `terminate 0` delivered, the host terminated, the server's answer to request 1, then `FAIL run-timeout` at `ticks=` at least 2^27, as declared; its mutations |
| `m1-guest-pins.txt` | Not a capture: the guest pins M1's five fixtures were captured with (`git show ff84533c:mvp/guest/pins.txt`); M2-5 | Bound by SHA-256; M1's fixtures against M1's kernel and DTBs, and `qemu-te-poc-gcc.log` failing the current pins on the kernel alone |
| `k3-anchor-gcc-m2a-ping-in-wait.log` | The COM260's first `anchor` run, `20261028T023339Z`, GCC, kexec from hart 0 with Fedora's shutdown before it, 397 lines; stop-6 evidence from the board (M2-A) | PASS under M2-A.1, judged as the board recorded it: hart 2's PONG `spv=0` with `received=0x2359c1` inside its request 1's wait, `[0xa5f3d, 0x154457e]`, the probe among the costs, and the board's counts pinned; PASS with the PING received at the wait's first and at its last tick; the base `k3anchor` of three mutations; with CRLF, `--write-fixtures`' `anchor-k3` capture, the dry run's GCC `anchor` run |

**Run: QEMU.** `tests/run-qemu.sh` (`make -C mvp qemu-test`,
`./mvp/mvp qemu`) boots every scenario, variant, and probe image for both
toolchains with eight harts and judges each attempt with the checker. A
REFUSED attempt is made again, up to eight attempts per run
(`BE_MVP_QEMU_ATTEMPTS`); a run whose every attempt is refused fails, as
does any verdict but `PASS` or a QEMU exit status other than 0. Every
attempt's capture, checker output, and record are kept, and
`attempts.tsv` lists each attempt's boot hart, verdict, capture digest,
boot ELF, and the ELF's SHA-256. Since M1-4 the suite has 44 runs: M0's
34, `te-poc` on `k3-like`, `rva23`, and `plic`, and `reader-write` and
`no-inject` on `k3-like`, for both toolchains, each `te-poc` run judged
against `build/mvp/gen/te-poc/expect` with the authority report
(`--report`). Since M2-5 it has 58: also `anchor` on `k3-like`, `rva23`,
and `plic`, and its four runtime negatives, `secret-shared`,
`response-writable`, `wrong-measurement`, and `no-grant-check`, on
`k3-like`, for both toolchains, each judged against
`build/mvp/gen/anchor/expect` with anchor's report and the measured
domain's kernel and DTB as built (`--kernel build/mvp/guest/Image --dtb
build/mvp/guest/mvp-guest-g1-anchor.dtb`). The first three negatives fail
closed at boot; `no-grant-check` ends in `run-timeout` after its 2^27-tick
budget, about 13.4 s at QEMU's 10 MHz timebase, inside the attempt's
300-second limit (`BE_MVP_QEMU_TIMEOUT`). A run is named
`anchor/<toolchain>/<machine>` or `anchor/<toolchain>/<variant>`.

**Run: kexec rehearsal.** `tests/kexec-rehearsal.sh`
(`./mvp/mvp kexec-rehearsal`) boots B0's GCC rehearsal kernel
(`build/k3-b0/gcc-kernel/arch/riscv/boot/Image`, an external input whose
release and SHA-256 it records) on the k3-like machine with eight harts
and OpenSBI 1.6. Its init (`tests/kexec-rehearsal/init.c`) loads a
toolchain's scenario boot image with `kexec_load` at L, the FDT 4 MiB
above it. Linux stops its other harts and jumps from its boot CPU, so a
kexec hart other than 0 exercises the start rule after a kexec. The
checker judges the capture in kexec mode, and a REFUSED attempt is made
again, up to eight. Since M1-4 it runs four images, each toolchain's
`two-guests` and `te-poc` boot images, a `te-poc` capture judged with
the authority report; since M2-5 six, with each toolchain's `anchor`
boot image, judged with anchor's report and the measured inputs (the
management module is in the guest's initramfs, so the rehearsal needs
nothing more).

**Run: the board tools.** B7's tools, ported (tables below), for the
plan's board procedure: RAM-only kexec from the running Fedora,
output-only serial capture, a human reset after each run, and nothing that
types at U-Boot or writes firmware, the U-Boot environment, flash, or the
board's storage. Since M1-5, with `K3_RESET=k3ctl` in the environment, the
tools reset the board themselves after each passing run through the
pinned `k3ctl` client (`tools/k3ctl.sha256`), `status` and `reset` only,
one per run (M1 plan, Q14 and "The remote reset"; see
[M1-5's tools](#m1-5s-tools-at-9020c4f8-2026-10-27)); without it a human
resets the board, as in M0. `SCENARIO=te-poc` selects M1's images, and,
since M2-5, `SCENARIO=anchor` M2's, with `VARIANT=wrong-measurement` or
`no-grant-check` its board negatives (M2 plan, Q11).

- `tools/k3-preflight.sh` (`k3-preflight`): read-only over SSH. It
  records each hart's DT node and ISA extensions and cpuinfo, the DT CPU
  links, `/cpus/cpu-map` and the cache nodes, the sysfs topology
  (`/sys/devices/system/cpu/*/topology`), HSM's detection in Fedora's log,
  B0's kexec facts, `/proc/iomem`, and the FDT reservations, and checks
  every MVP extent against them. It passes only with `h` and Sstc on harts
  0 to 2 in both the DT and cpuinfo, HSM detected (stop 8), and every
  extent free (stop 7); since M1-5 also only with the firmware identity of
  M0's record, `ID=0x1 Version=0x10006` (M1 stop 8), and it records the
  `k3ctl` client's SHA-256 against the pin.
- `tools/kexec-load.py` (the loader, staged on the board): `kexec_load`
  with the boot image at L (`0x1_0800_0000`) and the FDT at
  `0x1_0840_0000`, after the layout rule finds every MVP extent (the
  accepted image, the pool, the hart region, the MVP region, the staging
  region, both windows, and, since M1-5, the channel page, since M2-2 the
  three shared pages, `shared-pages=0x118000000-0x118003000`) inside one
  System RAM range and clear of every `/proc/iomem` child and FDT
  reservation, at preflight and again on the live map before the load.
- `tools/k3-run.sh` (`k3-load-check`, and each campaign run): checks the
  board image, stages it in the board's tmpfs `/tmp` with hash checks,
  loads it (and, for a load check, unloads it and stops), requests
  `systemctl kexec`, waits for the terminal marker in the serial capture,
  and judges the capture with the checker in kexec mode, a `te-poc` run's
  with the authority report, and, since M2-5, an `anchor` run's (a
  schema-v3 expectation) with anchor's report and the measured domain's
  kernel and DTB as built (`K3_KERNEL`, and `K3_MEASURED_DTB`, new), whose
  names and SHA-256 `run.txt` records (`measured=`); without either it
  stages nothing. A REFUSED run on the board is recorded as
  stop 6, never repeated. Since M1-5 it anchors the terminal expression at
  the start of a line, so that only hart 0's lines end the wait, writes
  `reset.txt` for every run, and, with `K3_RESET=k3ctl`, makes the remote
  reset under the plan's conditions.
- `tools/k3-campaign.sh` (`k3-probe`, `k3-campaign`): RUNS runs of each
  image, each after Fedora returns with a new boot ID (the human resets
  the board after each, or `k3-run.sh` resets it); the first run that does
  not pass ends the campaign, with no reset. `k3-probe` runs the three GCC
  probe images once each, and `k3-campaign` the image of `SCENARIO`
  (`two-guests` by default, `te-poc`, or, since M2-5, `anchor`), or of
  `VARIANT` (`payload`, Q13; `reader-write` or `no-inject`, M1 Q11;
  `wrong-measurement` or `no-grant-check`, M2 Q11), the default
  `K3_RUN_ROOT` named `<UTC>-<scenario>-<toolchain>` for a scenario other
  than `two-guests` (`te-poc-` before M2-5). Since M1-5 a wait for a
  human's reset that times out prints `BE_MVP_K3_CAMPAIGN: PAUSED` with
  the runs left and exits 75 (M1 Q18; open item 38).
- `tests/test-kexec-load.py` checks the layout rule on B7's recorded
  COM260 `/proc/iomem` and FDT reservations (its preflight, pinned by
  SHA-256) and on synthetic overlaps, and places each board image (16
  since M1-4, 22 since M2-5 with anchor's and its two board variants'),
  searching only its shim page and flat image, before the guest payload at
  `BOOT_KERNEL_OFFSET`, for a kexec purgatory (since M2-5: the guest's
  initramfs holds the management module, a RISC-V `ET_REL` object the
  search took for one; open item 56; the payload is checked against the
  guest pins by `tests/check-image.py`); since M1-5 it also checks the
  channel page on that map and
  on M0's board record's, pinned by SHA-256, and since M2-2 the three
  shared pages, each page's interior and both edges. `tests/fake-board.py` stands
  in for the board's SSH, `scp`, and serial output, from B7's record; its
  topology lines are synthetic, as B7 did not record them.
  `tests/run-tool-dry-run.sh` runs the tools on it (fourteen cases at
  M0-4, see [Results](#m0-4-at-9796f79d-2026-10-24); seventeen since M0-6,
  with `same-second`, added after M0-C's review, and `tree-state` and
  `probe-record`, see [M0-6's checks](#m0-6s-checks-on-l1-2026-10-26);
  `tree-state` needs a writable `mvp/tests/` and is skipped inside the
  evaluator, whose source tree is read-only; forty since M1-5, whose 23
  new cases cover the remote reset, against `tests/fake-k3ctl.py`, a fake
  dongle that answers only `ping`, `status`, and `reset`, and the `te-poc`
  runs and records, see
  [M1-5's tools](#m1-5s-tools-at-9020c4f8-2026-10-27); forty-five since
  M2-5, whose five new cases cover `SCENARIO=anchor`: `anchor-selector`
  (`tools.mk`'s anchor and variant specs, load images, and report are the
  dry run's), `load-check-anchor` (each toolchain's anchor image checked
  with the report and the measured inputs, recorded, at L, unloaded),
  `anchor-report` (a mismatched report, or no measured DTB: nothing
  staged), `anchor-campaign` (a passing GCC and Clang anchor run, then
  `wrong-measurement` and `no-grant-check` failing as declared, each with
  its `k3ctl` reset), and `anchor-record` (that campaign's board record
  and its platform record's M2 sections); every earlier case is
  unchanged; since Plan revision M2-A the `anchor-campaign` case's GCC
  `anchor` run is the first M2 board campaign's capture as the board
  recorded it, with the probe in a management wait among the checker's
  costs, and `anchor-record` checks the platform record's probe
  subsection); no case can reach
  a real board or dongle.

**Evidence: `tools/evidence.py` (new).** `make -C mvp evidence`, the last
step of `check`, writes `build/mvp/evidence/check`: `bundle.txt` (the
source commit and tree state, the lock's and the closure's SHA-256, the
scenario, every total), the tool record (`tool-lock.py check`) and the
lock, the scenario and its expectation files, `images.sha256` (each
toolchain's monitor and boot ELFs, flat image, and boot images, each
variant's and probe's, and the guest inputs: 146 files, 184 since M1-4
with the `te-poc` images, their two variants, and their DTBs, 247 since
M2-5 with anchor's four variants and two DTBs (234 at M2-4: the variants
are found by directory and the DTBs by name), each toolchain's six
`anchor` images, and the management module `guest/be-mgmt.ko`; and,
since M1-4, te-poc's scenario, `policy.te`, authority report, and policy
records, since M2-5 anchor's too), the checks'
records (`build/mvp/records/`), every QEMU attempt's capture, checker
output, and record, `refusals.tsv` (each QEMU run's and rehearsal's
attempts, refused attempts, and boot or kexec harts), `costs.tsv`, and
each kexec rehearsal made on the current boot image, under
`MANIFEST.sha256`. For a fixed input set the bundle is byte-identical; it
rewrites the checkout's path and HOME, and it refuses a missing record, an
unfinished suite, or a QEMU attempt whose boot ELF has changed. No path
read from a record is ever run (S1 H30); the only one read at all, each
attempt's boot ELF, must have its run's form inside the build tree and is
only hashed, and a board run's expectation is looked up by its checked
name. `make -C mvp board-evidence
K3_RUN_ROOT=<campaign>` writes the board record `mvp/results/<campaign>`
(never over an existing one): an `mvp/` directory with the same tool
record, scenario, and image digests and `runs.tsv` (each run's image,
expectation, and verdict; a REFUSED run is stop 6), then B0's
`retain-results.py`, unchanged, on the campaign, the preflight, and each
toolchain's latest load check, whose manifest and identifying-data scan
cover the `mvp/` files too; every retained excerpt must then give its
run's recorded verdict again. The record's `bundle.txt` gives the tree's
state as `git status --porcelain=v1` showed it before the load checks'
staging directory beside the record existed (M0-6; open item 41).
Since M0-6 it then runs
`tools/platform-record.py` on the record (below), requires both of the
files it writes to pass B0's identifying-data rule (no home path,
`machineid`, terminal metadata, unredacted UUID, or the checkout's or
HOME's prefix), writes
`MANIFEST.sha256` again, in B0's form, so that it covers them, and
verifies the whole record against it. `--verify DIR` checks a bundle or record
against its manifest. Since M1-5 the board record also holds each run's
`reset.txt` under `mvp/resets/`, the policy check on `te-poc` and its
report under `mvp/policy/`, and the campaign's `serial-log-note.txt`, and
judges a `te-poc` excerpt again with the authority report. Since M2-5 it
holds anchor's policy check and report beside te-poc's (each scenario's
record must equal its report; the bundle's `policy_check_anchor=` line),
requires each `anchor` run's `run.txt` to name the measured inputs
(`measured=`) that its expectation names, each the file in
`build/mvp/guest` with the expectation's SHA-256, and
judges an `anchor` excerpt again with the report and those inputs. The
bundler's self-test has 28 cases (17 at M0-6, 20 at M1-4, 25 at M1-5);
the board record and the platform record are exercised by the dry run's
`campaign`, `same-second`, `tree-state`, `probe-record`, `campaign-stop`,
`reset-human`, `te-poc-record`, and (M2-5) `anchor-record` cases.

**Platform record: `tools/platform-record.py` (new, M0-6).** The plan's
platform record ("Platform record: probes and negative images"):
`platform-record.py --record DIR [--qemu-suite DIR]` reads a board record's
own files and writes `platform-record.json` (schema
`be-mvp-platform-record-v1` at M0-6, `-v2` since M1-5, sorted keys) and
`platform-record.md` beside them. It holds the runs (image, toolchain, image
SHA-256, verdict, stop, the run's `k3_ssh` and serial source, boot ID, board
kernel, and the kexec and terminal times); the preflight's facts, each
hart's DT node, extensions, `/cpus/cpu-map` path, and cache link,
`/proc/cpuinfo`, the sysfs topology, Fedora's kept log lines, `/proc/iomem`,
each FDT reservation against System RAM, and `tools/kexec-load.py
region-check` on the preflight with `src/mvp-layout.h`; each probe value
against the plan's expectation, read as matched, a fact, or a difference
(stop 6), beside QEMU's values as emulation facts, from the in-tree GCC
probe captures judged again by `tests/check-capture.py` and from the QEMU
suite's Clang probe records when the suite's last attempt ran the record's
own Clang probe image; a "Serial log" section on OpenSBI's console lines, a
paragraph written by hand from the operator's serial log (open item 40),
since M1-5 read from the campaign's `serial-log-note.txt`; since M1-5 each
run's reset; each scenario run's counts, shutdown records, PING times, guest
`elapsed_ms`, and costs, with the ring and run budgets and the fields every
passing run shares or varies in; the other runs; and every file read, with
its SHA-256. Nothing in it is a claim. It runs the capture checker and the
loader's region check at fixed paths and nothing it reads, refuses an
existing platform record or a missing or malformed input, and is
byte-identical for a fixed input set. 570 lines at M0-6, 633 at `804cd24c`,
and 1,139 at the M1-6 content.

**M1's additions (M1-6).** Still schema `be-mvp-platform-record-v2`, with
keys only added (`preflight.baseline`, `preflight.channel_page`, `te_poc`,
`denials`, `channel`, `failures`). Under Preflight, the firmware identity
and SBI specification from Fedora's log and the Fedora kernel release (the
preflight's first `kernel=`) are each set beside M0's accepted record's
`preflight.txt`, as equal or differs; beside them the preflight's
`firmware_identity` and `firmware_expected` lines, each run's
`board_kernel`, and the region check's channel-page line, which the tool
requires (since M2-2 the `shared-pages` line, under the key
`preflight.shared_pages`). "te-poc runs" tables the te-poc image's runs as the two-guests
runs are tabled, adding `denials_g0` and `denials_g1` and each denial's
service ticks. "Denials on K3" gives, for each te-poc run, each
`BE_MVP:DENY` line's fields beside its guest's `MVPINIT 08 DENIED` report
and the expected denial, paired as `tests/check-capture.py` pairs them (per
domain, by order; the rule is mirrored, not imported, because the checker
reads `mvp-layout.h` on import); each pair shows which of `gpa`, `htval` =
GPA >> 2, `stval=va`, and `sepc=pc` hold, and a summary gives `htinst` by
the guest's kind. "The channel" shows the authority report's channel,
derived as the checker derives it (the report must have the SHA-256 its
expectation names), then each run's `CHANNEL_CHECKED` line with the fields
that differ from the report's, its `CHANNEL_CLEARED` line, and each guest's
`MVPINIT 07` line with whether the writer's and the reader's digests are
equal. Under Other runs, each run's FAIL and DETAIL lines are counted, so
that a domain hart's own fallback pair would show (Plan revision M1-B), with
its first FAIL and the DETAIL after it, `g0` and `g1` from `BE_MVP_COUNTS`,
and the domain lines after the first FAIL. A record with no te-poc run has
no te-poc section, and its Scenario runs section is as before: the dry run's
`campaign` record's differs from the one M1-4's evaluator run wrote
(`build/mvp-evaluator/`) only in the runs' names, their UTC times. The dry
run's `campaign`, `probe-record`, and `te-poc-record` cases (40 cases in
all) check these additions, and a malformed DENY, `MVPINIT 08`, or channel
line, an unknown `MVPINIT 07` role, or a report whose SHA-256 is not its
expectation's refuses the tool. On a scratch record of campaign
`20261027-com260-m1b` (`build/mvp/scratch-m16/record/`, written by
`tools/evidence.py --board` at `804cd24c` with M1-6's two tool files,
`source_tree=dirty changed=2`) it reported the firmware identity (`ID=0x1
Version=0x10006`), the SBI specification (`v2.0`), and the kernel release
equal to M0's record's, with that kernel in 6 of 6 runs; 12 DENY lines with
their 12 reports, `gpa`, `htval`, `stval=va`, and `sepc=pc` holding in all
12, and `htinst` `0x3303` for the 8 loads and `0x3023` for the 4 stores; 5
`CHANNEL_CHECKED` lines equal to the report's channel (none for
`reader-write`, whose monitor refused the reader's leaf), and the writer's
and the reader's digests (`0xeacaea8433f5c641`) equal in 5 of 5 runs; and
`reader-write` and `no-inject` each with 1 FAIL, 1 DETAIL, and no domain
line after the FAIL (`no-inject` `g0=54 g1=54`). The stopped first
campaign's `no-inject` capture
(`tests/fixtures/k3-no-inject-gcc-stop6-fallback.log`), run through the same
table, shows 2 FAIL and 2 DETAIL lines and 2 domain lines after the first
FAIL.

**M2's additions (M2-5).** Still schema `be-mvp-platform-record-v2`, with
keys only added (`anchor`; `m2` with `reports`, `pages`, `placed`,
`measurement`, `requests`, `transitions`, and `digests`, and, since Plan
revision M2-A, `ipi_runs` and `ipi_probes`) and no key's
meaning changed; a record without an anchor-scenario run (no expectation
with pages) renders as before, as the dry run's `campaign`,
`probe-record`, and `te-poc-record` cases still check. "anchor runs"
tables the `anchor` image's runs as the te-poc runs are tabled, adding
each domain's requests on hart 0 (`mgmt_g0`, `mgmt_g1`) and each request's
service ticks among the costs. "The pages" shows the report's three pages,
derived as the checker derives them (the report must have the SHA-256 its
expectation names), then each run's `PAGE_CHECKED` line for each page with
the fields that differ from the report's, and its `PAGE_CLEARED` and
`SECRET_PLACED` lines (the secret page's address and bytes, never its
contents). "The measurement" gives each run's `MEASURED` line, its ticks
in milliseconds at the platform's timebase, beside the offline value (the
report's `measurement_hex`), the measured domain's `DOMAIN_TERMINATED`
value, and a `wrong-measurement` run's DETAIL `computed=` and `expected=`.
"Management requests" gives each `BE_MVP:MGMT` line: the requester and its
state (as hart 0's transitions before the line give it), `seq`, the
function, the target, the result and its SBI name, the target's state
after the request, `ticks`, and `service=` (the request to the answer) in
ticks and milliseconds, beside the guest's `MVPINIT 10 MGMT` report of the
call; a call its own hart answered (FID 7) has the guest's line alone.
Since M2-A, "The IPI probe in a management wait", under it, sets each
`anchor` run's `BE_MVP:11 IPI_PROBE` lines beside the checker's costs:
each probe's `sent`, `received`, `answered`, and `spv`, and, for a probe
the checker recorded as served inside a management wait
(`g<d>_ping_in_mgmt_wait`, `g<d>_ping_mgmt_seq`), the `BE_MVP:MGMT` line
whose wait holds it, the receipt's offset into the wait, and both in
milliseconds at the platform's timebase; a sentence then says whether
the runs show it (`Observed: …` with each such probe's figures, or `Not
observed: …`) and how many probes show `spv=1`.
"Paused and terminated" gives each `DOMAIN_PAUSED` and `DOMAIN_TERMINATED`
line with its exits, `sha256`, and ticks, and, for a terminated domain that
was paused, whether its exits are the ones it paused with. "Requests and
responses" sets each request's requester's and server's digests beside the
offline HMAC-SHA-256 (the expectation's), `timeout=1` the unanswered one,
for each run with a digest line. Resets and Serial log are M1's. On an
anchor record the tool prints `BE_MVP_PLATFORM_RECORD_M2: anchor_runs=…
page_lines=… measured=… requests=… transitions=… digests=…
pings_in_wait=…` (the last since M2-A) before its PASS line. The dry
run's `anchor-record` case renders the record of a fake anchor campaign
(a GCC and a Clang `anchor` run, `wrong-measurement`, and
`no-grant-check`, from the `--write-fixtures` captures, the GCC `anchor`
run's since M2-A the first M2 board campaign's capture as the board
recorded it) and checks `BE_MVP_PLATFORM_RECORD_M2: anchor_runs=2
page_lines=12 measured=3 requests=32 transitions=5 digests=8
pings_in_wait=1`, the sections' summaries, and, since M2-A, the Observed
sentence with the board's figures (`96.531 ms`, `28.323..929.168 ms`).
1,141 lines at M2-4, 1,492 at M2-5, and 1,585 since M2-A.

**The evaluator.** See [The clean evaluator](#the-clean-evaluator).

## Results (this host)

"This host" in the sections through
[The lock refresh and the gates](#the-lock-refresh-and-the-gates-at-804fa95f-2026-10-25)
is the Fedora laptop `lx2`. M0-5's second board campaign was driven from
`lx2` and then from the workstation `l1`, to which the workspace and
`build/` moved, and the M0-6 sections after it were run on `l1`, as was
everything in M1's sections, from
[M1-1 and M1-2](#m1-1-and-m1-2-at-0174f7a8-and-b591b187-2026-10-26) on,
and in M2's, from
[M2-1 and M2-2](#m2-1-and-m2-2-at-f149eea0-and-d6667862-2026-10-27) on,
and in M4's, from
[M4-1 to M4-3](#m4-1-to-m4-3-at-30800dd3-c0097a4c-and-90b6b4a5-2026-10-28)
on.

### M0-1 and M0-2 (at `8194a18b`)

`make -C mvp check` (and `./mvp/mvp check`) passed:

```text
BE_MVP_LOCK_SELF_TEST: PASS cases=26
BE_MVP_LOCK: PASS roles=26 closure=257 lock_sha256=c30ca22737d1
BE_MVP_MAKE_CONTROL_SELF_TEST: PASS cases=49
BE_MVP_PORT: CHECK PASS files=32 changed=2 rules=6 substitutions=8 b2_manifest=7c43e75b2066
BE_MVP_DTS_SELF_TEST: PASS cases=57 dtbs=8 variants=5
BE_MVP_GUEST_PINS_SELF_TEST: PASS cases=45
BE_MVP_REFERENCE_SELF_TEST: PASS cases=71
BE_MVP_GUEST_ID_TEST: PASS cases=27 gcc=clang
BE_MVP_GUEST_PINS: PASS files=10 image_bytes=1553332 image_size=0x1af628 text_offset=0x200000 init_bytes=4176 dtb_bytes=4096
BE_MVP_HOST: PASS ring scenarios=157 assertions=343230 gcc=clang
BE_MVP_HOST: PASS hart scenarios=563 assertions=67887 gcc=clang
BE_MVP_HOST: PASS sbi scenarios=40 assertions=13261 gcc=clang
BE_MVP_HOST: PASS gstage scenarios=16 assertions=21655 gcc=clang
BE_MVP_HOST: PASS payload scenarios=8 assertions=592 gcc=clang
BE_MVP_TARGET: PASS objects=10 gcc clang
BE_MVP_REFERENCE: PASS guest=0 lines=19 elapsed_ms=1003
BE_MVP_REFERENCE: PASS guest=1 lines=19 elapsed_ms=1003
BE_MVP_REFERENCE: PASS guests=2
BE_MVP_CHECK: PASS
```

Each reference boot ran the pinned `Image` with that domain's reference
DTB under plain OpenSBI v1.6 in QEMU, no monitor, and the guest reached
its init, slept, and powered off (QEMU exit 0, about 4.2 s of wall time
each). The `elapsed_ms` values vary by a few milliseconds between runs.

`kernel-repro` (2026-10-23T20:23:06Z) rebuilt every guest output in a
second tree from the same pinned inputs and compared them:

```text
BE_MVP_KERNEL_REPRO: PASS outputs=10 identical; sysroot_files=1065 sysroot_sha256=c931b51b8789ec8c57c2169a954d421ec8cc7aa3e5c7e5a951ec08a241cc1df0; kernel_build_seconds=69
```

The first kernel build took 70 s. Both used `LINUX_GIT` as the local
mirror and `MVP_RPM_CACHE` as above.

Not run here: building and running the evaluator (M0-4).

### M0-3 (at `de05398a`)

These are M0-3's results before Plan revision M0-A, kept as recorded; [Plan
revision M0-A](#plan-revision-m0-a-at-ebae089d) below supersedes them.
`make -C mvp check` runs every row above, then `image-check`, `variants`,
`probes`, and `budgets`. Every row passed but the last, which reported stop
condition 3 (see [Open items](#open-items), item 8); the M0-1 and M0-2 rows
print as above, and M0-3's print:

```text
gcc: text_end=0x102007fe0 data_end=0x10200a940 functions=161 words=11095 asserts=65 boot_bytes=0x1b3000 dtb0_offset=0x1b1000 dtb1_offset=0x1b2000 bin_sha256=1bd94ed80bbb984511449c4f5d96b1cb86eb7ee867878c3e4c3e6788ee394c3d boot_sha256=06163421830af4c39e949a17064e16b4786d197bac4f625cb9f54fde14c74d94
BE_MVP_IMAGE_CHECK: PASS gcc
gcc: mutations rejected: 76
BE_MVP_IMAGE_CHECK: PASS mutations=76
BE_MVP_IMAGE_CHECK: PASS dtb-init-exit dtb-rdcycle dtb-sbi-time variant-payload variant-init-exit variant-rdcycle variant-sbi-time variant-shim-rule variant-exit-budget variant-run-timeout variant-ring-full variant-hart-start
BE_MVP_IMAGE_CHECK: PASS probe-platform-gcc probe-vmid-distinct-gcc probe-vmid-shared-gcc probe-platform-clang probe-vmid-distinct-clang probe-vmid-shared-clang
BE_MVP_IMAGE_CHECK: PASS probe-platform-gcc-mutations=3 probe-vmid-distinct-gcc-mutations=3 probe-platform-clang-mutations=3 probe-vmid-distinct-clang-mutations=3
BE_MVP_BUDGETS: PASS self-test cases=9
BE_MVP_BUDGET: gcc text_end=0x102007fe0 limit=0x102008000 spare=0x20 data_end=0x10200a940 limit=0x10200f000 pool=0x10000 region=0x20000 flat=0x34000 boot=0x1b3000 limit=0x400000 two_links=identical: PASS
BE_MVP_BUDGET: clang (measurement link) text_end=0x1020087e0 limit=0x102008000 over=0x7e0 data_end=0x10200a870 limit=0x10200f000 pool=0x10000 region=0x20000: FAIL text (stop condition 3)
BE_MVP_BUDGETS: FAIL clang (measurement link):text
```

(Ten more `BE_MVP_BUDGET:` lines, each `PASS`, cover the four monitor
variants and the six probe images.) The mutation test's 76 defects in the
GCC image and its layout include the plan's eight: VTW set by an arm
immediate, a `stimecmp` write outside the budget helper, a third install
call, a raw `hgatp` write, equal VMIDs, a block offset moved (in the
layout, the hart entry, and the vector), a ring size that is not a power
of two, and equal `bootargs`. The probe profile's mutations are a raw
`hgatp` write in the dispatch and another install call in every probe
image, the probe module's install call removed in `probe-platform`, and
a fence after the raw switch in a VMID image.

**QEMU smoke runs** (`tests/run-qemu.sh`, provisional, raw logs under
`build/mvp/qemu/final/`): QEMU 10.2.2, `-smp 8 -m 8G`, OpenSBI v1.6
`fw_dynamic` from B1's build (`--bios`), the boot ELF as `-kernel`, the
plan's k3-like machine (`virt,aia=aplic-imsic,aia-guests=7`, `rv64` with
Sstc, Svade without Svadu, Sv39 only, Smstateen) unless named, 300 s per
attempt. 19 of 20 runs passed in 63 attempts; an attempt whose boot hart
was not 0 and that ended in exactly `BE_MVP:FAIL firmware` was repeated
(open item 9).

| Run | Attempts | Outcome | Terminal line |
| --- | --- | --- | --- |
| GCC `k3-like` | 6 | pass | `BE_MVP:14 SHUTDOWN type=0 reason=0` |
| GCC `rva23` | 3 | pass | `BE_MVP:14 SHUTDOWN type=0 reason=0` |
| GCC `plic` | 1 | pass | `BE_MVP:14 SHUTDOWN type=0 reason=0` |
| GCC `no-sstc` | 1 | as declared, after `:02`, `DETAIL henvcfg=0x0` | `BE_MVP:FAIL sstc` |
| GCC `sbi-3.0` (QEMU's OpenSBI 1.7) | 1 | as declared, before `BE_R3:01` | `BE_MVP:FAIL boot` |
| `payload` | 6 | as declared, after `:03` | `BE_MVP:FAIL payload` |
| `exit-budget` | 1 | as declared, `DETAIL domain=0 hart=1 ... exits=65` | `BE_MVP:FAIL exit-budget` |
| `run-timeout` | 3 | as declared, `DETAIL ticks=0x100373` | `BE_MVP:FAIL run-timeout` |
| `ring-full` | 3 | **not as declared**: passes (open item 10) | `BE_MVP:14 SHUTDOWN type=0 reason=0` |
| `hart-start` | 1 | as declared, `DETAIL domain=1 hart=9 result=-3 status=-3` | `BE_MVP:FAIL hart-start` |
| `init-exit` | 2 | as declared, `DETAIL domain=1 hart=2 cause=0xa ...` | `BE_MVP:FAIL guest-reboot` |
| `rdcycle` | 2 | as declared, `DETAIL domain=0 hart=1 cause=0x16 ... tval=0xc00027f3` | `BE_MVP:FAIL virtual-instruction` |
| `sbi-time` | 2 | pass, `time=851` and `time=853` | `BE_MVP:14 SHUTDOWN type=0 reason=0` |
| `shim-rule` | 1 | pass, `BE_MVP_SHIM: boot_hart=0x1 starting hart 0` then `SHIM hart=0x0` | `BE_MVP:14 SHUTDOWN type=0 reason=0` |
| GCC `probe-platform` | 1 | nine PROBE lines | `BE_MVP:14 SHUTDOWN type=0 reason=0` |
| GCC `probe-vmid-distinct` | 1 | one PROBE line | `BE_MVP:14 SHUTDOWN type=0 reason=0` |
| GCC `probe-vmid-shared` | 4 | one PROBE line | `BE_MVP:14 SHUTDOWN type=0 reason=0` |
| Clang `probe-platform` | 2 | nine PROBE lines | `BE_MVP:14 SHUTDOWN type=0 reason=0` |
| Clang `probe-vmid-distinct` | 9 | one PROBE line | `BE_MVP:14 SHUTDOWN type=0 reason=0` |
| Clang `probe-vmid-shared` | 13 | one PROBE line | `BE_MVP:14 SHUTDOWN type=0 reason=0` |

The GCC `k3-like` run's control-hart lines (each domain also printed its
65 lines, prefixed `BE_MVP_G0: ` and `BE_MVP_G1: `, interleaved):

```text
BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000108000000 fdt=0x000000027fe00000 dest=0x0000000102000000 bytes=0x0000000000034000
BE_R3:01 BOOT_VALIDATED
BE_R3:02 R1_DERIVED
BE_R3:03 R2_BUILT_REWALKED
BE_R3:04 HS_VS_STATE_VERIFIED
BE_R3:05 BINDING_PREPARED
BE_R3:06 HGATP_FENCED_PUBLISHED
BE_MVP:01 SCENARIO name=two-guests domains=2 harts=0,1,2 of=8 ring_bytes=0x8000
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1
BE_MVP:03 GSTAGE_BUILT_REWALKED domain=0 hart=1 gpa=0x80000000 hpa=0x110000000 size=0x4000000 leaves=32 root=0x102034000 vmid=1
BE_MVP:03 GSTAGE_BUILT_REWALKED domain=1 hart=2 gpa=0x80000000 hpa=0x114000000 size=0x4000000 leaves=32 root=0x10203c000 vmid=2
BE_MVP:04 PAYLOAD_CHECKED kernel_bytes=0x17b3b4 image_size=0x1af628
BE_MVP:05 DOMAIN_RAM_CLEARED domain=0 gpa=0x80000000 size=0x4000000 ticks=0x85c78
BE_MVP:05 DOMAIN_RAM_CLEARED domain=1 gpa=0x80000000 size=0x4000000 ticks=0x8b082
BE_MVP:06 PAYLOAD_PLACED domain=0 kernel=0x80200000 kernel_bytes=0x17b3b4 image_size=0x1af628 dtb=0x83e00000 dtb_bytes=0x1000 ticks=0x4995
BE_MVP:06 PAYLOAD_PLACED domain=1 kernel=0x80200000 kernel_bytes=0x17b3b4 image_size=0x1af628 dtb=0x83e00000 dtb_bytes=0x1000 ticks=0x42e3
BE_MVP:07 BLOCKS_PUBLISHED region=0x102044000 bytes=0x20000 generation=1 budget_ticks=0x100000000
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x35b5
BE_MVP:08 HART_STARTED hart=2 domain=1 result=0 status=0 ticks=0x104a
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15d hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x83e00000 ticks=0x9113
BE_MVP:09 HART_READY hart=2 domain=1 hgatp=0x800020000010203c hstatus_controls=0x180 hedeleg=0xb15d hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=2 domain=1 pc=0x80200000 a0=0x0 a1=0x83e00000 ticks=0x91ba
BE_MVP:11 IPI_PROBE hart=2 domain=1 sent=0x34135 received=0x34362 answered=0x34387 spv=1
BE_MVP:11 IPI_PROBE hart=1 domain=0 sent=0x324a6 received=0x32aa5 answered=0x34219 spv=1
BE_MVP:12 DOMAIN_SHUTDOWN hart=2 domain=1 exits=157 sbi=156 ipi=1 base=14 time=0 dbcn_write=98 dbcn_read=43 dbcn_byte=0 srst=1 refused=0 lines=65 ring_peak=0x1c8 entered=0x91ba ticks=0x279e1ac
BE_MVP:12 DOMAIN_SHUTDOWN hart=1 domain=0 exits=157 sbi=156 ipi=1 base=14 time=0 dbcn_write=98 dbcn_read=43 dbcn_byte=0 srst=1 refused=0 lines=65 ring_peak=0x158 entered=0x9113 ticks=0x27a6535
BE_MVP:13 RUN_COMPLETE domains=2 records=138 wakes=122 idle_ticks=0x2724df9 overlap_ticks=0x2794ff2 ticks=0x27a7ad8
BE_MVP:14 SHUTDOWN type=0 reason=0
```

The domains overlapped for `0x2794ff2` ticks: all of domain 1's interval
from entry to shutdown, and all but `0x8430` of domain 0's `0x279d422`. The probe
images' lines (QEMU's values are emulation facts; the GCC and Clang
images agree but for the store fault's `sepc`, the stub's own layout, and
the IPI timings):

```text
BE_MVP:01 SCENARIO name=probe-platform domains=1 harts=0,1 of=8 ring_bytes=0x8000
BE_MVP:PROBE hsm status=1:1,2:1,3:1,4:1,5:1,6:1,7:1
BE_MVP:PROBE hgatp vmid=0x3fff sv48x4=0x8000000000102014 sv57x4=0x8000000000102014 sv39x4=0x83fff00000102014 vmid_bits=14 restored=0x8000000000102014
BE_MVP:PROBE gpf access=load gpa=0x90000000 scause=0x15 stval=0x90000000 htval=0x24000000 htinst=0x3303 sepc=0x80200040 gva=1
BE_MVP:PROBE gpf access=store gpa=0x90000000 scause=0x17 stval=0x90000000 htval=0x24000000 htinst=0x3023 sepc=0x80200054 gva=1
BE_MVP:PROBE gpf access=fetch gpa=0x90000000 scause=0x14 stval=0x90000000 htval=0x24000000 htinst=0x0 sepc=0x90000000 gva=1
BE_MVP:PROBE ipi mode=hs sent=100 delivered=100 min=0x74 median=0x81 max=0x467 spv=100
BE_MVP:PROBE ipi mode=vs sent=100 delivered=100 min=0xe9 median=0x103 max=0x1db spv=100
BE_MVP:PROBE order mode=unfenced iterations=10000 stale=0
BE_MVP:PROBE order mode=fenced iterations=10000 stale=0
BE_MVP:14 SHUTDOWN type=0 reason=0
BE_MVP:PROBE vmid mode=distinct gpa=0x80100000 hgatp_a=0x8000100000102034 hgatp_b=0x800020000010203c value_a=0xa5a5a5a5a5a5a5a5 value_b=0x5a5a5a5a5a5a5a5a reads=10 before=0xa5a5a5a5a5a5a5a5 after=0x5a5a5a5a5a5a5a5a
BE_MVP:PROBE vmid mode=shared gpa=0x80100000 hgatp_a=0x8000100000102034 hgatp_b=0x800010000010203c value_a=0xa5a5a5a5a5a5a5a5 value_b=0x5a5a5a5a5a5a5a5a reads=10 before=0xa5a5a5a5a5a5a5a5 after=0x5a5a5a5a5a5a5a5a
```

(GCC `probe-platform`, then the two VMID images' lines.) In QEMU every
other hart was STOPPED; the Sv48x4 and Sv57x4 writes left `hgatp` as it
was (the k3-like CPU has neither mode), and Sv39x4 kept all 14 VMID
bits; each fault's `htval` is the GPA shifted right by
2; every IPI arrived; no read was stale, fenced or not; and both VMID
images read B's value after the switch, so in QEMU no translation of
root A survived the raw switch, with the same VMID or a distinct one.

Not run here: Clang scenario images (stop condition 3), the capture
checker and the kexec rehearsal (M0-4), and the board.

### Plan revision M0-A (at `ebae089d`)

`make -C mvp clean`, then `./mvp/mvp check`, passed at `ebae089d` in
45.7 s of wall time (the guest outputs are cached by pin; no kernel was
built). Each of the three commits passed `./mvp/mvp check` before it was
made. The rows print as M0-3's, but for these:

```text
BE_MVP_PORT: CHECK PASS files=32 changed=2 rules=12 substitutions=14 b2_manifest=7c43e75b2066
BE_MVP_PAYLOAD: PASS kernel_bytes=0x17b3b4 kernel_image_size=0x1af628 dtb0_offset=0x221000 dtb1_offset=0x222000 image_bytes=0x223000
BE_MVP_HOST: PASS sbi scenarios=41 assertions=13479 gcc=clang
BE_MVP_HOST: PASS payload scenarios=8 assertions=599 gcc=clang
BE_MVP_SCENARIO_SELF_TEST: PASS cases=29
BE_MVP_SCENARIO: PASS name=two-guests harts=0,1,2 images=15 sha256=9978db42902d
gcc: text_end=0x102004540 data_end=0x102008750 mvp_text_end=0x102067bd0 mvp_end=0x102069e00 functions=162 words=11192 asserts=69 flat_bytes=0xa4000 boot_bytes=0x223000 dtb0_offset=0x221000 dtb1_offset=0x222000 bin_sha256=f383ba454cd7de7c530250970d23fc363101a6157f36223effc32008fbc33835 boot_sha256=bd2841567c7899eb471cdcdd696d1ad8b6b14e26adc41717ec063b51a46b611a
clang: text_end=0x102004770 data_end=0x102008710 mvp_text_end=0x102068160 mvp_end=0x10206a350 functions=177 words=12107 asserts=69 flat_bytes=0xa4000 boot_bytes=0x223000 dtb0_offset=0x221000 dtb1_offset=0x222000 bin_sha256=7b469ebdccd668f9351ad13c9ed6cd49e33785f3274d8a5da079d58bbbafe3be boot_sha256=26cf9d82adeebaabb25a2261fa3a18d84ba72e54436d6d1e20d1f4409b40aab3
BE_MVP_IMAGE_CHECK: PASS gcc clang
gcc: mutations rejected: 91
BE_MVP_IMAGE_CHECK: PASS mutations=91
clang: mutations rejected: 91
BE_MVP_IMAGE_CHECK: PASS mutations=91
BE_MVP_IMAGE_CHECK: PASS dtb-init-exit dtb-rdcycle dtb-sbi-time variant-payload variant-init-exit variant-rdcycle variant-sbi-time variant-shim-rule variant-exit-budget variant-run-timeout variant-ring-full variant-hart-start
BE_MVP_IMAGE_CHECK: PASS probe-platform-gcc probe-vmid-distinct-gcc probe-vmid-shared-gcc probe-platform-clang probe-vmid-distinct-clang probe-vmid-shared-clang
BE_MVP_IMAGE_CHECK: PASS probe-platform-gcc-mutations=4 probe-vmid-distinct-gcc-mutations=4 probe-platform-clang-mutations=4 probe-vmid-distinct-clang-mutations=4
BE_MVP_BUDGETS: PASS self-test cases=12
BE_MVP_BUDGET: gcc text_end=0x102004540 limit=0x102008000 spare=0x3ac0 data_end=0x102008750 limit=0x10200f000 pool=0x10000 hart_region=0x20000 mvp_text=0x3bd0 mvp_rodata=0xd60 mvp_data=0x8a8 mvp_bss=0xc28 mvp_bytes=0x5e00 limit=0x40000 spare=0x3a200 flat=0xa4000 boot=0x223000 limit=0x400000 two_links=identical: PASS
BE_MVP_BUDGET: clang text_end=0x102004770 limit=0x102008000 spare=0x3890 data_end=0x102008710 limit=0x10200f000 pool=0x10000 hart_region=0x20000 mvp_text=0x4160 mvp_rodata=0xd20 mvp_data=0x8a8 mvp_bss=0xc28 mvp_bytes=0x6350 limit=0x40000 spare=0x39cb0 flat=0xa4000 boot=0x223000 limit=0x400000 two_links=identical: PASS
BE_MVP_BUDGETS: PASS measured=16
BE_MVP_CHECK: PASS
```

The variants' line prints once per toolchain, and fourteen more
`BE_MVP_BUDGET:` lines, each `PASS`, cover each toolchain's four monitor
variants and the six probe images (see
[Budgets (measured)](#budgets-measured)). The mutation test now rejects 91
defects in each toolchain's image and layout: M0-3's 76 (GCC's only, at M0-3)
and 15 for the MVP region. In the link map, an MVP C function in the accepted
code extent, MVP C constants in the accepted data, and an accepted object's code
in the region; in the ELF, an MVP section inside the accepted image, the
region's data past its end, the hart entry in the region, the dispatch in the
accepted code extent, the region's end past `0x1_020a_4000`, and the region's
constants executable; in the flat image, a page too long; in the boot image, the
descriptor's length the accepted image's; and in the layout, a region over 256
KiB, a region not after the hart region, a flat image the region does not end,
and a staged image on the region. Each probe image's mutation test adds one (4
per image, M0-3's 3): the probe's `hgatp` probe in the accepted code extent, or
the raw switch in the MVP region.

**QEMU runs** (`tests/run-qemu.sh`, provisional, raw logs under
`build/mvp/qemu/m0a-final*`): as for M0-3, but every scenario, variant,
and probe image for both toolchains, each run made once. The suite's 34
runs passed (`BE_MVP_QEMU: PASS runs=34 refused=7`, 49 s); the seven
REFUSED runs, whose boot hart was a domain's hart (open item 13), were
made again by naming them, and every one then ran as declared (three
needed a second repeat). Each cell gives the boot hart of the run that
ran as declared, and, before it, the boot harts of its REFUSED runs:

| Run | GCC | Clang | Outcome and terminal line |
| --- | --- | --- | --- |
| `k3-like` | 0 | 6 | pass, `BE_MVP:14 SHUTDOWN type=0 reason=0` |
| `rva23` | 4 | 6 | pass, `BE_MVP:14` |
| `plic` | 1 R, 7 | 2 R, 5 | pass, `BE_MVP:14` |
| `no-sstc` | 5 | 1 R, 6 | as declared, after `:02`, `DETAIL henvcfg=0x0`, `BE_MVP:FAIL sstc` |
| `sbi-3.0` (QEMU's OpenSBI 1.7) | 0 | 0 | as declared, before `BE_R3:01`, `BE_MVP:FAIL boot` |
| `payload` | 0 | 3 | as declared, after `:03`, `BE_MVP:FAIL payload` |
| `exit-budget` | 3 | 6 | as declared, `DETAIL domain=0 hart=1 ... exits=65`, `BE_MVP:FAIL exit-budget` |
| `run-timeout` | 5 | 5 | as declared, `DETAIL ticks=0x10031e` (GCC), `0x100313` (Clang), `BE_MVP:FAIL run-timeout` |
| `ring-full` | 2 R, 3 | 0 | as declared (M0-A.3): no domain line and no `:11` after `:10`, then each domain hart's own `BE_MVP:FAIL ring` and its `DETAIL domain=<d> hart=<h> cause=0xa ...` (`exits=19` and `24`; in the Clang run the first hart's SRST cut the second hart's DETAIL short) |
| `hart-start` | 1 R, 1 R, 5 | 0 | as declared, `DETAIL domain=1 hart=9 result=-3 status=-3`, `BE_MVP:FAIL hart-start` |
| `init-exit` | 3 | 4 | as declared, `DETAIL domain=1 hart=2 cause=0xa ... exits=96`, `BE_MVP:FAIL guest-reboot` |
| `rdcycle` | 1 R, 1 R, 5 | 0 | as declared, `DETAIL domain=0 hart=1 cause=0x16 ... tval=0xc00027f3`, `BE_MVP:FAIL virtual-instruction` |
| `sbi-time` | 3 | 5 | pass, `time=847` (GCC) and `time=845` (Clang) per domain, `BE_MVP:14` |
| `shim-rule` | 2 | 0 | pass, `BE_MVP_SHIM: boot_hart=0x1 starting hart 0`, `started=none`, `BE_MVP:14` |
| `probe-platform` | 0 | 1 R, 1 R, 6 | nine PROBE lines, `BE_MVP:14` |
| `probe-vmid-distinct` | 7 | 2 | one PROBE line, `BE_MVP:14` (Clang: `started=2`; the probe images run domain 0 alone) |
| `probe-vmid-shared` | 0 | 0 | one PROBE line, `BE_MVP:14` |

(R: REFUSED, `BE_MVP:FAIL firmware` straight after `:02`, as M0-A.2
declares for a STARTED domain hart.) Of these 44 runs, 33 booted on a hart
other than 0. In 22 of them (boot harts 2 to 7, none a domain's hart of
its image) `BE_MVP:02` printed `started=<h>` for the boot hart and the
shim printed `boot_hart=0x<h>`, and each run went on as declared; in 10
(boot hart 1, or 2 in a two-domain image) `:02` printed `started=<h>` and
then `BE_MVP:FAIL firmware`; and in the `shim-rule` run that booted on hart
2 the rule hart stopped itself and `:02` printed `started=none`. Every run
on hart 0 printed `started=none`, but the two `sbi-3.0` runs, which stop
before `:02`. The `ring-full` runs show the M0-A.3 path: each domain hart's
ring view failed at its full 1 KiB ring, so it could not post its FAIL
record and printed its own lines at once, while hart 0, still in its
`0x2000000`-tick wait, printed nothing after `:10` (open item 14). Both
toolchains' `k3-like` runs reached `BE_MVP:14`; their control-hart lines
match M0-3's but for these (GCC, boot hart 0, then Clang, boot hart 6):

```text
BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000108000000 fdt=0x000000027fe00000 dest=0x0000000102000000 bytes=0x00000000000a4000
BE_MVP:01 SCENARIO name=two-guests domains=2 harts=0,1,2 of=8 ring_bytes=0x8000 mvp_region=0x102064000 mvp_bytes=0x40000 image_bytes=0xa4000
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:07 BLOCKS_PUBLISHED region=0x102044000 bytes=0x20000 generation=1 budget_ticks=0x100000000
BE_MVP:12 DOMAIN_SHUTDOWN hart=1 domain=0 exits=157 sbi=156 ipi=1 base=14 time=0 dbcn_write=98 dbcn_read=43 dbcn_byte=0 srst=1 refused=0 lines=65 ring_peak=0x118 entered=0x79f0 ticks=0x277738d
BE_MVP:12 DOMAIN_SHUTDOWN hart=2 domain=1 exits=157 sbi=156 ipi=1 base=14 time=0 dbcn_write=98 dbcn_read=43 dbcn_byte=0 srst=1 refused=0 lines=65 ring_peak=0x1a0 entered=0x7a0e ticks=0x2776fb1
BE_MVP:13 RUN_COMPLETE domains=2 records=138 wakes=96 idle_ticks=0x2713481 overlap_ticks=0x276f5a3 ticks=0x2779e83
BE_MVP_SHIM: boot_hart=0x6 starting hart 0
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:0,7:1 started=6
BE_MVP:12 DOMAIN_SHUTDOWN hart=2 domain=1 exits=157 sbi=156 ipi=1 base=14 time=0 dbcn_write=98 dbcn_read=43 dbcn_byte=0 srst=1 refused=0 lines=65 ring_peak=0x1c8 entered=0x7328 ticks=0x2798a8d
BE_MVP:12 DOMAIN_SHUTDOWN hart=1 domain=0 exits=157 sbi=156 ipi=1 base=14 time=0 dbcn_write=98 dbcn_read=43 dbcn_byte=0 srst=1 refused=0 lines=65 ring_peak=0x220 entered=0x6346 ticks=0x27b9158
BE_MVP:13 RUN_COMPLETE domains=2 records=138 wakes=118 idle_ticks=0x272c5e8 overlap_ticks=0x2791765 ticks=0x27bae9b
```

Each domain printed its 65 lines and exited 157 times in every passing
scenario and `shim-rule` run (one GCC `shim-rule` domain made one more
DBCN read: 158), and 1,003 (GCC) or 1,001 (Clang) times with 64 lines in
`sbi-time`; the outbound rings' high-water marks stayed between `0x118`
and `0x220` bytes of `0x8000`. The ring-full lines (GCC, boot hart 3):

```text
BE_MVP:01 SCENARIO name=two-guests domains=2 harts=0,1,2 of=8 ring_bytes=0x400 mvp_region=0x102064000 mvp_bytes=0x40000 image_bytes=0xa4000
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:0,4:1,5:1,6:1,7:1 started=3
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x83e00000 ticks=0x73c4
BE_MVP:10 DOMAIN_ENTERED hart=2 domain=1 pc=0x80200000 a0=0x0 a1=0x83e00000 ticks=0x73f1
BE_MVP:FAIL ring
BE_MVP:DETAIL domain=1 hart=2 cause=0xa pc=0xffffffff800071ec tval=0x0 htval=0x0 htinst=0x0 spvp=1 vsatp=0x8000000000080385 exits=19
BE_MVP:FAIL ring
BE_MVP:DETAIL domain=0 hart=1 cause=0xa pc=0xffffffff800071ec tval=0x0 htval=0x0 htinst=0x0 spvp=1 vsatp=0x8000000000080385 exits=24
```

The probe images' lines match M0-3's in form; in QEMU every other hart
was again STOPPED or the start rule's, and the VMID images again read B's
value after the raw switch.

Not run here: the capture checker and the kexec rehearsal (M0-4), and
the board.

### M0-4 (at `9796f79d`, 2026-10-24)

`./mvp/mvp check` passed at `9796f79d`, from a clean tree, in 2 min 29 s
of wall time (the guest outputs are cached by pin; no kernel was built),
and each M0-4 commit's checks passed before it was made; `90fc9060`
changes only a docstring. Beyond M0-A's rows it prints these (`<repo>` is
the checkout):

```text
BE_MVP_CAPTURE_SELF_TEST: PASS cases=34 failed=0
BE_MVP_CAPTURE_MUTATIONS: PASS mutations=154 rejected=154 seed=0x4d30
kexec-load self-test: 15/15 PASS images=10
BE_MVP_EVIDENCE_SELF_TEST: PASS cases=17/17
BE_MVP_RUN_TOOL_DRY_RUN: PASS
BE_MVP_TOOLS_CHECK: PASS
BE_MVP_QEMU_TOOLCHAIN[gcc]: runs=17 attempts=29 refused=12
BE_MVP_QEMU_TOOLCHAIN[clang]: runs=17 attempts=19 refused=2
BE_MVP_QEMU: PASS runs=34 attempts=48 refused=14
BE_MVP_EVIDENCE: PASS development <repo>/build/mvp/evidence/check files=189 images=146 qemu_attempts=48 rehearsals=2
BE_MVP_CHECK: PASS
```

**QEMU suite** (66 s for 48 attempts). Every run's last attempt passed
its expectation; each variant failed as declared and each probe image
printed its probe lines, with the outcomes of M0-A's table above. Each
cell gives the boot hart of each attempt in order (R: REFUSED, a domain
hart's boot, M0-A.2):

| Run | GCC | Clang |
| --- | --- | --- |
| `k3-like` | 6 | 6 |
| `rva23` | 2 R, 5 | 7 |
| `plic` | 2 R, 1 R, 1 R, 6 | 3 |
| `no-sstc` | 1 R, 2 R, 1 R, 4 | 6 |
| `sbi-3.0` (fails before `:02`) | 0 | 6 |
| `payload` | 0 | 2 R, 0 |
| `exit-budget` | 1 R, 5 | 5 |
| `run-timeout` | 3 | 4 |
| `ring-full` | 2 R, 4 | 2 R, 3 |
| `hart-start` (domain 1's hart absent) | 1 R, 6 | 2 |
| `init-exit` | 4 | 6 |
| `rdcycle` | 2 R, 4 | 7 |
| `sbi-time` | 2 R, 7 | 3 |
| `shim-rule` | 0 | 7 |
| `probe-platform` | 2 | 6 |
| `probe-vmid-distinct` | 2 | 4 |
| `probe-vmid-shared` | 4 | 7 |

Totals: GCC 17 runs, 29 attempts, 12 refused; Clang 17, 19, 2; all 34,
48, 14. Thirty of the 34 completed attempts booted on a hart other than 0.
The three full checks made while M0-4 was built refused 5, 6, and 14
attempts (34 runs each); no run needed more than four attempts of its
eight. For a two-domain image, all eight attempts refused has probability
(2/8)^8, about 1.5e-5, if QEMU's boot hart is uniform.

**Kexec rehearsal** (`./mvp/mvp kexec-rehearsal`, 29 s): B0's GCC
rehearsal kernel `7.3.0-rc4-gc1c7e254143f` (SHA-256
`4871aa91f05da98c02dfd0375ae3418ff577230675339609109ae0eaa79cedef`) with
eight harts on the k3-like machine and OpenSBI 1.6:

```text
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=0 image=bd2841567c78 kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=5 image=26cf9d82adee kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
```

GCC first, then Clang, whose Linux ran its kexec on hart 5, so the shim
started hart 0 after the kexec:

```text
[    1.632290] Will call new kernel at 108000000 from hart id 5
BE_MVP_SHIM: boot_hart=0x5 starting hart 0
BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000108000000 fdt=0x0000000108400000 dest=0x0000000102000000 bytes=0x00000000000a4000
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:0,6:1,7:1 started=5
BE_MVP:13 RUN_COMPLETE domains=2 records=138 wakes=106 idle_ticks=0x2712d0a overlap_ticks=0x2780aff ticks=0x2795d1b
BE_MVP:14 SHUTDOWN type=0 reason=0
```

At `631c1286` the rehearsal had passed too: GCC on hart 0, and Clang on
hart 0 after one attempt refused on hart 1. B7's own rehearsal, unchanged,
still passes with this kernel (one hart).

**Board tools, dry run** (`tests/run-tool-dry-run.sh`, about 45 s, every
case against `tests/fake-board.py`):

| Case | Result |
| --- | --- |
| `preflight-pass` | B7's recorded COM260 facts: `h` and Sstc on harts 0 to 2 in the DT and cpuinfo, HSM detected, every extent free |
| `preflight-stops` | A `/proc/iomem` child in either window or the hart region, an FDT reservation in the staging region or the MVP region, no Sstc on hart 0, no `h` on hart 2, and no HSM each stop it |
| `load-check` | GCC and Clang loaded at L with the FDT at `0x108400000`, then unloaded; no kexec |
| `probe` | The three GCC probe images, 3 of 3 on distinct boots |
| `campaign` | Three GCC runs, one Clang, then the GCC `payload` run, failing as declared: 5 of 5; its board record (B0's retention: 5 runs, 2 load checks, 58 files) verifies, and every excerpt gives its verdict again |
| `kexec-refused` | A kexec hart that is a domain's: REFUSED, recorded as stop 6, a nonzero exit |
| `campaign-stop` | That capture with RUNS=2: the campaign ends after run 1, with no second kexec; its record says stop 6 |
| `kexec-overlap`, `kexec-fail`, `kexec-timeout` | The shim's overlap refusal, a failure in the domains' run, and no capture each fail the run |
| `kexec-busy` | A child in the staging region, or in the hart region: the loader refuses, before any kexec |
| `kexec-not-tmpfs`, `kexec-tampered` | `/tmp` not a tmpfs, or a staged byte flipped: the tool stops before the load |
| `kexec-control-path` | An SSH control directory too long for a socket: the tool stops before any ssh |

`tests/test-kexec-load.py` passed all 15 cases on the ten board images.
On B7's recorded COM260 `/proc/iomem` (20 System RAM children) and FDT
reservations (11), pinned by the preflight's SHA-256
`c9c27c229128689c32d2780b3ddb68f800ccd6b8a01a273a388cd84818e0867e`, every
MVP extent is free and inside System RAM:

```text
region accepted-image=0x102000000-0x102034000 result=free
region pool=0x102034000-0x102044000 result=free
region hart-region=0x102044000-0x102064000 result=free
region mvp-region=0x102064000-0x1020a4000 result=free
region staging=0x108000000-0x108600000 result=free
region g0-window=0x110000000-0x114000000 result=free
region g1-window=0x114000000-0x118000000 result=free
```

**Evidence.** After the rehearsal, `./mvp/mvp evidence` wrote the bundle
again with both current rehearsals: 186 files (1.3 MB), `MANIFEST.sha256`
of 185 lines, whose SHA-256 is
`9495332b7b0e2adfc6e5bd7006073b4fc81a0e40a37e141fd9ebddfa32049045`, with
`source_commit=9796f79d...` and `source_tree=clean`; two bundles made from
one input set were byte-identical, and `--verify` passes.

**Evaluator** (`./mvp/mvp evaluate`, 47 s): the host side passed (its
bundle verified, its 146 images as now), and the image did not build. With
the pinned base (pulled; created 2026-07-16) and the 257-package closure,
`dnf install` failed:

```text
BE_MVP_EVALUATE: image=localhost/beryllium-mvp-evaluator:1aac6b29ad9d base=registry.fedoraproject.org/fedora@sha256:daf897befd7a78a52f11db5ca2229a4923991bb30709932770cb493f7a000cf0 closure_sha256=1aac6b29ad9dc56dae3eaf270db0f2033dc30868989cbc5708979c61ac42f3c2 closure_packages=257
No match for argument: ca-certificates-2026.2.92_v9.0.319-1.fc44.noarch
Problem: problem with installed package
  - installed package systemd-standalone-sysusers-259.7-1.fc44.x86_64 conflicts with systemd-standalone-sysusers provided by systemd-sysusers-259.10-1.fc44.x86_64 from updates
  - package systemd-sysusers-259.10-1.fc44.x86_64 from updates conflicts with systemd-standalone-sysusers provided by systemd-standalone-sysusers-259.10-1.fc44.x86_64 from updates
  - package systemd-sysusers-259.10-1.fc44.x86_64 from updates conflicts with systemd-standalone-sysusers provided by systemd-standalone-sysusers-259.5-1.fc44.x86_64 from fedora
  - conflicting requests
BE_MVP_EVALUATE: FAIL cannot build localhost/beryllium-mvp-evaluator:1aac6b29ad9d (podman build exited 123; ...)
```

A query of Fedora 44's `fedora` and `updates` repositories found 256 of
the closure's 257 NEVRAs; the host's `ca-certificates`
`2026.2.92_v9.0.319-1.fc44` has been replaced there by `-2.fc44`. So the
lock was not checked inside the evaluator, no gate ran there, and the
images' identity across the host and the evaluator is not shown; nothing
was loosened (stop condition 11; open item 7). Plan revision M0-B
resolves it (below).

**Checker-to-monitor size** (S1 H43). Counted in lines at `90fc9060`:

| Code | MVP | B7 |
| --- | --- | --- |
| Monitor: `src/` and the shim (B7: `src/`, B3's shim reused) | 8,447 | 4,621 |
| Checkers: the capture and image checkers, `tools/budgets.py` (B7: its capture, image, and marker checkers) | 5,333 | 6,244 |
| Host tests | 6,827 | 4,211 |
| Harness drivers and their tests: the QEMU driver, the rehearsal and its init, the dry run, the fake board, the loader's test | 2,275 | 1,926 |
| Checking code | 14,435 | 12,381 |
| Lines of checking code per monitor line | 1.71 | 2.68 |

Without the shim the MVP's ratio is 1.79; with the scenario generator
(753 lines), which writes the expectations B7's marker checker held, and
the evidence bundler (926), it is 1.91. The fixtures are data and are not
counted (MVP 1,445 lines, B7 226). The plan's inference from B7 was about
three to one; M0's harness is smaller per monitor line than B7's, chiefly
because the expectations are data (`tools/gen-scenario.py`) where B7 wrote
them into a 3,116-line marker checker. (Recounted at M0-6 by the same
method: see [M0-6's checks](#m0-6s-checks-on-l1-2026-10-26).)

Not run here: the board (M0-5).

### Plan revision M0-B (at `67731e4c`, 2026-10-24)

**The record** (`fetch-closure.py --record`, before `b364fe92`). The
first run fetched every RPM and verified each both ways in 63 s of wall
time:

```text
BE_MVP_FETCH: --record key=36f612dcf27f7d1a48a835e4dbfcf71c6d9f90a6 file=/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-44-primary sha256=93642aec521a1e5e96dd715f7ae0ec0850ebc9de09a94ce03cae5263f26cc18a package=fedora-gpg-keys-44-2.noarch
BE_MVP_FETCH: source fedora-repositories: fetched 256 of 257
BE_MVP_FETCH: source koji: fetched 1 of 1
BE_MVP_FETCH: RECORDED signatures=257 key=36f612dcf27f7d1a48a835e4dbfcf71c6d9f90a6 header_digests=254 b3_pins=3
BE_MVP_FETCH: RECORDED closure_sha256 1aac6b29ad9dc56dae3eaf270db0f2033dc30868989cbc5708979c61ac42f3c2 -> de566183fff1d9621541300819ff699261bbe7cd13eee7fe873c355c23a70a5f
BE_MVP_FETCH: PASS cache=<repo>/build/mvp-evaluator/rpms rpms=257 bytes=384959945 sources=fedora:116,koji:1,updates:140
```

256 RPMs came from Fedora's repositories (116 from `fedora`, 140 from
`updates`) and one, `ca-certificates-2026.2.92_v9.0.319-1.fc44.noarch`
(SHA-256 `3de32ead7049b1c06f5cbc821d7991051f5d54afd044f2db8b0529584d9d36b3`),
from koji's signed copy. All 257 carry a good header signature by the
Fedora 44 key, the 254 this host has installed have the installed
package's header SHA-256, and m4, bison, and flex equal B3's pins. The
cache holds the 257 files, 384,959,945 bytes. After the closure's header
comment was reflowed, a second `--record` took 11 s from the cache,
verified every file both ways again, derived the same 257 digests, and
re-bound the closure to `50753286...`. Koji's top-level file of the same
build (under `noarch/`, SHA-256 `3d5881b3...`) is unsigned: rpmkeys
reports `digests OK` and exits 0, and the record's check refuses it
(`no header signature by 36f612dc...`), although its header SHA-256 is
the signed copy's and the installed package's, `ca27c56d...`; only the
signature check tells the two apart.

**The lock's diff** since `77559def`: in `tool-lock.conf`, three lines
change, the schema (`be-mvp-tool-lock-v1` to `-v2`), `MVP_TOOL_ROLES`
(`podman ssh scp` appended), and `MVP_CLOSURE_SHA256`
(`1aac6b29ad9d...` to
`50753286bcb4db4dabc49fdc0b7564978596b9c2c606341691cae8fa5b4a3ef5`), and
19 are added, `MVP_TOOL_HOST_ONLY_ROLES` and the three roles' six fields
each; nothing else. In `closure.txt`, the header comment gains a 13-line
paragraph on the digests and each of the 257 lines gains its digest; the
NEVRAs are unchanged. The roles were written by `refresh`. Its first run
with the new roles took podman's package as a closure root and would
have added 31 packages to the closure, so it was discarded: the roots now
leave out the host-only roles (a self-test case covers it), and the
second run's diff was the roles' lines alone, the 26 existing roles' lines
byte for byte unchanged (no host drift). A third `refresh` changed
nothing.

**The host's check** at `67731e4c` (`./mvp/mvp check`, 2 min 35 s) passed
as at M0-4, with the lock's rows above:

```text
BE_MVP_QEMU_TOOLCHAIN[gcc]: runs=17 attempts=20 refused=3
BE_MVP_QEMU_TOOLCHAIN[clang]: runs=17 attempts=26 refused=9
BE_MVP_QEMU: PASS runs=34 attempts=46 refused=12
BE_MVP_EVIDENCE: PASS development <repo>/build/mvp/evidence/check files=180 images=146 qemu_attempts=46 rehearsals=2
BE_MVP_CHECK: PASS
```

**The evaluator** (`./mvp/mvp evaluate`, 5 min 10 s): the host's lock and
bundle in 3 s, the fetch in 2 s (every file kept), the image's build in
47 s, and `mvp check` inside in 4 min 19 s:

```text
BE_MVP_EVALUATE: host PASS roles=29 host_only_skipped=0 closure=257 lock_sha256=9513ece84af3
BE_MVP_EVALUATE: host source=67731e4cc8ad47867c91b94261769579cd7bf1ab tree=clean images=146
BE_MVP_EVALUATE: fetch PASS cache=<repo>/build/mvp-evaluator/rpms rpms=257 bytes=384959945 sources=fedora:116,koji:1,updates:140
BE_MVP_EVALUATE: image=localhost/beryllium-mvp-evaluator:50753286bcb4-009c2eba5655 base=registry.fedoraproject.org/fedora@sha256:daf897befd7a78a52f11db5ca2229a4923991bb30709932770cb493f7a000cf0 closure_sha256=50753286bcb4db4dabc49fdc0b7564978596b9c2c606341691cae8fa5b4a3ef5 containerfile_sha256=009c2eba5655d75193e1e8fc95ea1ae2362d3f583955781a8457aa03423c78ee closure_packages=257
BE_MVP_EVALUATE: image_id=22fc8610385567d404767b7143b9bfcd7c0d9ca6564ea2dbbb1feae43a7c2472 rpms=291 rpms_sha256=d4cae9edef07321d6fb6b2b8c55a3167c807e98591a7154bd92c31f186b84b99
BE_MVP_EVALUATE: swap removed systemd-standalone-sysusers-259.7-1.fc44.x86_64 removed glibc-minimal-langpack-2.43-7.fc44.x86_64 removed rpm-build-libs-6.0.1-2.fc44.x86_64 removed rpm-sign-libs-6.0.1-2.fc44.x86_64 removed dnf5-plugins-5.4.2.1-1.fc44.x86_64 installed systemd-sysusers-259.10-1.fc44.x86_64
BE_MVP_LOCK: PASS roles=26 host_only_skipped=3 closure=257 lock_sha256=9513ece84af3
BE_MVP_TOOLS_CHECK: PASS
BE_MVP_QEMU: PASS runs=34 attempts=41 refused=7
BE_MVP_EVIDENCE: PASS development <repo>/build/mvp/evidence/check files=157 images=146 qemu_attempts=41 rehearsals=0
BE_MVP_CHECK: PASS
BE_MVP_EVALUATE: BE_MVP_IMAGE_IDENTITY: PASS images=146 same=146 differing=0
BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:50753286bcb4-009c2eba5655
```

The build's transaction installed 149 packages, upgraded 35, removed the
five named, and found 73 already at the closure's NEVRA; it downloaded
nothing ("Need to download 0 B"), and dnf5 noted that it skipped OpenPGP
checks for the 184 local packages it installed or upgraded. The image
(1,687,063,829 bytes) holds 291 packages: the 257 of the closure and 34
of the base that the closure does not name (dnf5 and its libraries,
gnupg2 and its libraries, the release, repository, and key packages and
the imported Fedora 44 key, sudo, tar, vim-minimal, and a few more), and
no podman. Inside, every gate passed with the host's counts: the lock,
its three host-only roles skipped, and both self-tests; the Make
controls; B2's port built from the accepted sources
(`BE_B2_PORT: PASS files=32 changed=11 accepted_r5=165f4d001a2b`) and the
MVP port re-derived; the guest kernel built from the read-only mirror,
with m4, bison, and flex from the closure, and every output equal to its
pin (`BE_MVP_GUEST_BUILD: PASS kernel=built pins=match`); both reference
boots; the five host tests (GCC = Clang, the pinned counts); the target
check; the scenario; the image checks and their mutations, the variants,
and the probes; the capture checker's 34 cases and 154 mutations, the
loader's 15 cases, the bundler's 17, and the board tools' dry run; the
QEMU suite (GCC 17 runs, 23 attempts, 6 refused; Clang 17, 18, and 1);
and the budgets. Its bundle, at source `67731e4c` (clean), records the
host's lock and closure SHA-256.

**Image identity:** all 146 images the evaluator built equal the host's:
each toolchain's monitor ELF and flat image, boot ELF and image, and
position-independent boot ELF and image (12); the variants' (88) and the
probes' (36); and the ten guest inputs (`Image`, `init`, and eight DTBs),
which the evaluator built itself. No image differs, so there was nothing
to diagnose.

**Kexec rehearsal** at `67731e4c` (`./mvp/mvp kexec-rehearsal`, 32 s), on
M0-4's boot images, which are unchanged:

```text
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=3 image=bd2841567c78 kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=2 refused=1 kexec_harts=2,5 image=26cf9d82adee kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
```

So M0-4's exit criteria (`mvp check`, `kexec-rehearsal`, and `evaluate`
pass; the images are identical across the host and the evaluator) hold at
`67731e4c`.

Not run here: the board (M0-5).

### M0-5's first board campaign (2026-10-24 and 25)

Run on the COM260 with M0-4's images, a human resetting the board after
each run; the records are in `build/mvp/k3-preflight/`,
`build/mvp/k3-load-checks/`, and `build/mvp/k3-campaigns/20261024-com260/`
(not yet a retained board record), and the board ran Fedora's 7.3.0-65.1
kernel:

| Step | Result |
| --- | --- |
| Preflight | PASS: HSM detected, every MVP extent free in `/proc/iomem` (20 System RAM children) and the FDT reservations (11) |
| Load checks, GCC (`bd2841567c78`) and Clang (`26cf9d82adee`) | Both loaded at L with the FDT at `0x108400000`, then unloaded; no kexec |
| `probe-platform`, `probe-vmid-distinct`, `probe-vmid-shared` (GCC) | PASS, PASS, PASS, each from hart 0 on a distinct boot |
| Scenario, GCC, run 1 (`20261025T022152Z`) | FAIL: 5 alternations, fewer than K = 8; every other rule held. The campaign stopped (stop condition 6) before runs 2 and 3 |

The probe runs' values are facts for the platform record (M0-6). Plan
revision M0-C followed; the campaign restarts from the load checks.

### Plan revision M0-C (at `c5ecedee`, 2026-10-25)

**The tool lock fails on this host** (open item 33). `./mvp/mvp check`
at `c5ecedee`, from a clean tree, stops at its first step in 6 s:

```text
BE_MVP_LOCK_SELF_TEST: PASS cases=46
BE_MVP_FETCH_SELF_TEST: PASS cases=39
BE_MVP_LOCK: FAIL 1 closure packages are not installed at their NEVRA, first ca-certificates-2026.2.92_v9.0.319-1.fc44.noarch
```

The host's `ca-certificates` is now `2026.2.92_v9.0.319-2.fc44`,
installed on 2026-10-24 at 17:02 EDT by a host update (with `tmux`,
`sos`, `socat`, `ntpsec`, and `firefox`, none of them in the closure),
after M0-B's checks and before the board campaign; every one of the 29
roles still passes. Nothing was refreshed or reinstalled.

**Every later stage of `check`** passes at `c5ecedee` in 2 min 39 s:
the same targets in `check`'s order, `lint port-check guest-pin-check
host-test target-check reference-boot image-check variants probes
tools-check qemu-test budgets evidence`, run by Make in the wrapper's
clean environment. Its rows are M0-B's but these:

```text
BE_MVP_HOST: PASS hart scenarios=652 assertions=140687 gcc=clang
BE_MVP_CAPTURE_SELF_TEST: PASS cases=36 failed=0
BE_MVP_CAPTURE_MUTATIONS: PASS mutations=154 rejected=154 seed=0x4d30
BE_MVP_QEMU_TOOLCHAIN[gcc]: runs=17 attempts=19 refused=2
BE_MVP_QEMU_TOOLCHAIN[clang]: runs=17 attempts=24 refused=7
BE_MVP_QEMU: PASS runs=34 attempts=43 refused=9
BE_MVP_EVIDENCE: PASS development <repo>/build/mvp/evidence/check files=163 images=146 qemu_attempts=43 rehearsals=0
```

The bundle records `source_commit=c5ecedee...`, `source_tree=clean`, and
`lock_check_status=1`. Every QEMU run's last attempt passed its
expectation, each variant failing as declared and each probe image
printing its probe lines; Clang's `k3-like` and `rva23` runs each took
four attempts, the first three booting on hart 2. The two-domain runs
that pass, as alternations and wakes, each with 138 records (136 for
`sbi-time`), and every `ring_peak` at most `0x1c8`:

| Run | GCC | Clang |
| --- | --- | --- |
| `k3-like` | 101, 110 | 87, 114 |
| `rva23` | 83, 113 | 110, 97 |
| `plic` | 78, 117 | 78, 125 |
| `shim-rule` | 53, 133 | 77, 119 |
| `sbi-time` | 77, 114 | 94, 96 |

Before `129626e0` was committed, the same stages passed on its content
with `260ceba6`'s fixtures and checker (34 self-test cases; QEMU 34 runs,
44 attempts, 10 refused; `k3-like` 102 alternations and 106 wakes for
GCC, 97 and 91 for Clang). Once, before `c5ecedee`, `tools-check` failed
in the board-tool dry run's campaign case and passed when made again
(open item 35).

**Kexec rehearsal** at `c5ecedee` (`./mvp/mvp kexec-rehearsal`, 31 s):

```text
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=0 image=185396d1db7c kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=0 image=19a5f2d2e89d kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
```

GCC first, then Clang, each Linux running its kexec on hart 0: 87
alternations in 87 wakes (GCC) and 77 in 103 (Clang).

**Evaluator.** `./mvp/mvp evaluate` at `c5ecedee` stops before its
build, at its first step, in 1 s:

```text
BE_MVP_LOCK: FAIL 1 closure packages are not installed at their NEVRA, first ca-certificates-2026.2.92_v9.0.319-1.fc44.noarch
BE_MVP_EVALUATE: FAIL the host's tool lock does not pass (<repo>/build/mvp-evaluator/record/lock.txt)
```

So the M0-C images' identity across the host and the evaluator is not
shown. The evaluator image
`localhost/beryllium-mvp-evaluator:50753286bcb4-009c2eba5655` is
unchanged.

**The board images** at `c5ecedee` (SHA-256), which the restarted
campaign loads in place of M0-4's (the scenario's `bd2841567c78...` for
GCC and `26cf9d82adee...` for Clang):

| Image | SHA-256 |
| --- | --- |
| GCC scenario | `185396d1db7c1a774665342e3a086643a80d719686aaae2980857228a18498ba` |
| Clang scenario | `19a5f2d2e89df83770d60f1731eb6077ca25ec6eb6a2ffacf1d54b276b40925d` |
| GCC `payload` | `f9c47dd08ac8e218be838c012ca1e0c613674a4471cbc63efbc9dfe7a2139d05` |
| GCC `probe-platform` | `cede8006150de162d6d152f850ba7079a708a9cade7eaeb990d255b7b387aa2f` |
| GCC `probe-vmid-distinct` | `1f64375150a26e321d81059b5427f093ffad7ee79b83e497b3eddb46d25488bc` |
| GCC `probe-vmid-shared` | `0c8de5d68db1f4717bb2a31d147553ee6fa02364fcf487895355fec77aae50dc` |

Not run here at `c5ecedee`: the board (M0-5's restart).

### The lock refresh and the gates (at `804fa95f`, 2026-10-25)

Rolling the host's `ca-certificates` back was proposed and the
responsible human declined it as a security issue. On the direction
`refresh the lock`, `./mvp/mvp tool-lock refresh` reproduced all 29 roles
byte for byte and changed one closure line, `ca-certificates`
`2026.2.92_v9.0.319-1.fc44` to `-2.fc44`, re-binding
`MVP_CLOSURE_SHA256`; `fetch-closure.py --record` fetched the new RPM
from Fedora's `updates` repository, verified its signature under the
Fedora 44 key (`6d9f90a6`) and its header digest against the installed
package (`installed=same`), and recorded its SHA-256
(`ce1202707eb5...`). No other role, pin, or closure line changed
(`804fa95f`; lock SHA-256 `8df124b9b362`). The gates then pass on the
M0-C images, the two harness fixes (items 35 and 36) included:

```text
BE_MVP_CHECK: PASS                      (2 min 37 s; QEMU 34 runs, 38 attempts, 4 refused)
BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:56d91c9233e5-009c2eba5655
BE_MVP_LOCK: PASS roles=26 host_only_skipped=3 closure=257 lock_sha256=8df124b9b362   (inside)
BE_MVP_QEMU: PASS runs=34 attempts=39 refused=5                                        (inside)
BE_MVP_IMAGE_IDENTITY: PASS images=146 same=146 differing=0
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=4 image=185396d1db7c
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=3 refused=2 kexec_harts=1,2,5 image=19a5f2d2e89d
```

The evaluator image was rebuilt from the verified cache with
repositories disabled (image id `c388da18d18e...`, 291 packages, the
same five named base removals as M0-B); `evaluate` took 3 min 51 s and
its record is `build/mvp-evaluator/record/20261025T034921Z/`.

### M0-5's second board campaign (2026-10-25 and 26)

With the M0-C images, on the one COM260 (K3), whose Fedora host kernel
was `7.3.0-65.1.riscv64.omni.fc45.riscv64` in every run, with the
preflight of 2026-10-24 (`captured_utc=2026-10-24T21:57:10Z`) standing:
both load checks, then eight RAM-only `kexec_load` runs, each on a
distinct boot, with output-only serial capture and a human reset after
each run; automation never typed at U-Boot. Every Linux handed over from
hart 0 (`Will call new kernel at 108000000 from hart id 0` in each
excerpt), so no run met the start rule. The campaign directory is
`build/mvp/k3-campaigns/20261025-com260/`, whose `summary.md` says
`Boot marker reproduced: 8/8 runs` and `Distinct boots: 8 of 8 runs`; the
load checks are `build/mvp/k3-load-checks/gcc/20261025T035420Z` and
`clang/20261025T035440Z`; the board record is `results/20261025-com260/`
([below](#the-board-record-and-the-platform-record-m0-6-2026-10-26)).

The load checks (2026-10-25, 03:54 UTC) loaded the GCC (`185396d1db7c`)
and Clang (`19a5f2d2e89d`) scenario images at L
(`loader=kexec_load entry=0x108000000 fdt=0x108400000 image_memsz=0x223000
fdt_bytes=49280 kexec_loaded=1`), then unloaded them
(`unload=ok kexec_loaded=0`); no kexec. The runs, in the plan's order
(UTC; image SHA-256 prefixes; boot ID before each run):

| # | Run | From | Image | Boot ID before | Result |
| --- | --- | --- | --- | --- | --- |
| 1 | `20261025T035453Z` | `lx2` | GCC `probe-platform` (`cede8006150d`) | `74408ee4-7008-475d-9fbb-98230d6e32b4` | PASS: harts 1 to 7 STOPPED; Sv39x4 with 14 VMID bits, the Sv48x4 and Sv57x4 modes not taken; `htval` = GPA >> 2 for load, store, and fetch; IPIs 100 of 100 in HS (median `0x1f` ticks) and at V=1 (median `0x21`); 0 stale reads, fenced and unfenced |
| 2 | `20261025T072239Z` | `lx2` | GCC `probe-vmid-distinct` (`1f64375150a2`) | `b76baa66-e68a-4654-a0e8-26c36975fff0` | PASS: B's value after the switch (tagging by VMID) |
| 3 | `20261025T073053Z` | `lx2` | GCC `probe-vmid-shared` (`0c8de5d68db1`) | `1b7855f5-2779-403c-b6d8-a998833f5987` | PASS: A's value after the switch, a translation cached under the shared VMID (a fact either way, by the plan's table) |
| 4 | `20261025T073242Z` | `lx2` | GCC scenario (`185396d1db7c`) | `e2ac365c-7c44-439e-9112-77ce1b437ac6` | PASS |
| 5 | `20261026T022021Z` | `l1` | GCC scenario (`185396d1db7c`) | `8d978154-3d3e-4697-90a7-fd7ee52d5ae0` | PASS |
| 6 | `20261026T052617Z` | `l1` | GCC scenario (`185396d1db7c`) | `b8c9d967-8b37-4d8b-8f8d-ef830d62a0bc` | PASS |
| 7 | `20261026T054220Z` | `l1` | Clang scenario (`19a5f2d2e89d`) | `7a6bc297-b921-4e3d-87b0-d618c92f6062` | PASS |
| 8 | `20261026T061327Z` | `l1` | GCC `payload` (`f9c47dd08ac8`) | `fa6d5aa8-a742-4e9b-a1e1-c4b5adac5ea6` | PASS as declared: `BE_MVP:FAIL payload` after both `BE_MVP:03` lines (`terminal=fail-marker`; no domain ran, `g0=0 g1=0`) |

Each of the four scenario runs passed with `exits_g0=157 exits_g1=157
records=138 wakes=2 alternations=125 g0=65 g1=65` and
`hart0_idle_permille=431` (counts below).

**Two workstations.** Runs 1 to 4 (2026-10-25) were driven from the Fedora
laptop `lx2` (their `run.txt`: `k3_ssh=fedora@k3e`, and the operator's
picocom log `boot-7.log` there as the serial source). The workspace and
`build/` were then copied with rsync to the workstation `l1`, and runs 5
to 8 (2026-10-26, UTC) were driven from `l1` (`k3_ssh=fedora@k3-f45`, the
operator's picocom log `boot-7.log` on `l1`). It was the same board with
the same board kernel and the same images: every run's `image_sha256` is
the M0-C board image of its kind listed under
[Plan revision M0-C](#plan-revision-m0-c-at-c5ecedee-2026-10-25), and on
`l1` each invocation ran the image checker and the variants' checks
again, and the board tool's image check before each run, with the same
digests (`BE_MVP_BOOT_IMAGE[gcc]: PASS ... sha256=185396d1db7c`, `[clang]`
`19a5f2d2e89d`, and the `payload` variant's `f9c47dd08ac8`, in
`k3-campaign-*.console.txt`).

**The campaign tool's two exits.** `k3-campaign.sh` exited twice while it
waited for the human's reset, a tool timeout and not a stop condition
(open item 38): after GCC run 1, `BE_MVP_K3_CAMPAIGN: STOP board did not
return in 36000s` (that invocation set `K3_RETURN_SECONDS=36000`;
2026-10-25), and after GCC run 2, `BE_MVP_K3_CAMPAIGN: STOP board did not
return in 1800s` (the default). Each time it was resumed, after the
reset, into the same `K3_RUN_ROOT=$PWD/build/mvp/k3-campaigns/20261025-com260`
with the operator's picocom log as `K3_SERIAL_LOG` and only the runs not
yet made: `./mvp/mvp k3-campaign TOOLCHAIN=gcc RUNS=2`, then
`TOOLCHAIN=gcc RUNS=1`, `TOOLCHAIN=clang RUNS=1`, and
`TOOLCHAIN=gcc VARIANT=payload RUNS=1`. Each run was made once, in the
plan's order, and the last invocation's `summary.md` lists all eight. The
five invocations' console transcripts (`k3-probe.console.txt`,
`k3-campaign-gcc.console.txt`, `k3-campaign-gcc-resume.console.txt` with
both GCC resumes, `k3-campaign-clang.console.txt`, and
`k3-campaign-payload.console.txt`) stay in the campaign directory; B0's
retention keeps each run's files and the summary, not them, so they are
not in the board record.

**The probe values on K3** (runs 1 to 3; each run's `handoff-excerpt.log`):

```text
BE_MVP:PROBE hsm status=1:1,2:1,3:1,4:1,5:1,6:1,7:1
BE_MVP:PROBE hgatp vmid=0x3fff sv48x4=0x83fff00000102014 sv57x4=0x83fff00000102014 sv39x4=0x83fff00000102014 vmid_bits=14 restored=0x8000000000102014
BE_MVP:PROBE gpf access=load gpa=0x90000000 scause=0x15 stval=0x90000000 htval=0x24000000 htinst=0x3303 sepc=0x80200040 gva=1
BE_MVP:PROBE gpf access=store gpa=0x90000000 scause=0x17 stval=0x90000000 htval=0x24000000 htinst=0x3023 sepc=0x80200054 gva=1
BE_MVP:PROBE gpf access=fetch gpa=0x90000000 scause=0x14 stval=0x90000000 htval=0x24000000 htinst=0x0 sepc=0x90000000 gva=1
BE_MVP:PROBE ipi mode=hs sent=100 delivered=100 min=0x1e median=0x1f max=0x38 spv=100
BE_MVP:PROBE ipi mode=vs sent=100 delivered=100 min=0x20 median=0x21 max=0x23 spv=100
BE_MVP:PROBE order mode=unfenced iterations=10000 stale=0
BE_MVP:PROBE order mode=fenced iterations=10000 stale=0
BE_MVP:PROBE vmid mode=distinct gpa=0x80100000 hgatp_a=0x8000100000102034 hgatp_b=0x800020000010203c value_a=0xa5a5a5a5a5a5a5a5 value_b=0x5a5a5a5a5a5a5a5a reads=10 before=0xa5a5a5a5a5a5a5a5 after=0x5a5a5a5a5a5a5a5a
BE_MVP:PROBE vmid mode=shared gpa=0x80100000 hgatp_a=0x8000100000102034 hgatp_b=0x800010000010203c value_a=0xa5a5a5a5a5a5a5a5 value_b=0x5a5a5a5a5a5a5a5a reads=10 before=0xa5a5a5a5a5a5a5a5 after=0xa5a5a5a5a5a5a5a5
```

Each probe run printed `started=none` and every other hart's status 1
(STOPPED) in `BE_MVP:02`, started hart 1 in `0x482` to `0x484` ticks, and
ended with `BE_MVP:14 SHUTDOWN type=0 reason=0`.

**The scenario runs** (each run's `check.txt` and `BE_MVP:13`; overlap
of the two domains' entered-to-shutdown intervals against the shorter;
hart 0's idle ticks):

| Run | Toolchain | `records` | `wakes` | `alternations` | `overlap_ticks` of `shorter_ticks` | `:13 ticks` | `idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `20261025T073242Z` | GCC | 138 | 2 | 125 | `0x25403a7` of `0x2563c77` | `0x26d240c` | `0x10c46fe` |
| `20261026T022021Z` | GCC | 138 | 2 | 125 | `0x25403f2` of `0x2563ca7` | `0x26d2409` | `0x10c474b` |
| `20261026T052617Z` | GCC | 138 | 2 | 125 | `0x2540339` of `0x2563bf9` | `0x26d233a` | `0x10c4686` |
| `20261026T054220Z` | Clang | 138 | 2 | 125 | `0x2540332` of `0x2563c0e` | `0x26d233b` | `0x10c4695` |

In all four, both domains printed `exits=157 sbi=156 ipi=1 base=14 time=0
dbcn_write=98 dbcn_read=43 dbcn_byte=0 srst=1 refused=0 lines=65` in
`BE_MVP:12`, with `ring_peak=0x1278` for domain 0 and `0x12b0` for domain
1, and each guest's sleep check printed `elapsed_ms=1004`; `:09` read back
`hedeleg=0xb15c` on both domain harts (K3's WARL `hedeleg`, as B6
recorded; `0xb15d` in QEMU). The harts started in `0x384` to `0x484`
ticks; domain 0 entered `0x55a` to `0x57b` ticks after the barrier and
domain 1 `0x23e2c` to `0x23e3a` (in M0-3's QEMU run, `0x9113` and
`0x91ba`). Run 4's hart 0 lines from the PING on:

```text
BE_MVP:11 IPI_PROBE hart=1 domain=0 sent=0x1ce579 received=0x1ce5cf answered=0x1ce5db spv=1
BE_MVP:11 IPI_PROBE hart=2 domain=1 sent=0x23598a received=0x2359ba answered=0x2359c4 spv=1
BE_MVP:12 DOMAIN_SHUTDOWN hart=1 domain=0 exits=157 sbi=156 ipi=1 base=14 time=0 dbcn_write=98 dbcn_read=43 dbcn_byte=0 srst=1 refused=0 lines=65 ring_peak=0x1278 entered=0x56a ticks=0x25641e1
BE_MVP:12 DOMAIN_SHUTDOWN hart=2 domain=1 exits=157 sbi=156 ipi=1 base=14 time=0 dbcn_write=98 dbcn_read=43 dbcn_byte=0 srst=1 refused=0 lines=65 ring_peak=0x12b0 entered=0x23e3a ticks=0x2589673
BE_MVP:13 RUN_COMPLETE domains=2 records=138 wakes=2 idle_ticks=0x10c46fe overlap_ticks=0x25403a7 ticks=0x26d240c
BE_MVP:14 SHUTDOWN type=0 reason=0
```

The capture checker's costs (`BE_MVP_COSTS`, recorded only; ticks of the
board's 24 MHz timebase):

| Cost | `20261025T073242Z` | `20261026T022021Z` | `20261026T052617Z` | `20261026T054220Z` |
| --- | --- | --- | --- | --- |
| `g0_ping_to_receipt_ticks` | 86 | 78 | 84 | 76 |
| `g0_receipt_to_pong_ticks` | 12 | 7 | 7 | 6 |
| `g0_run_ticks` | 39,206,007 | 39,206,055 | 39,205,881 | 39,205,902 |
| `g0_run_ticks_per_exit` | 249,719 | 249,720 | 249,718 | 249,719 |
| `g1_ping_to_receipt_ticks` | 48 | 47 | 55 | 49 |
| `g1_receipt_to_pong_ticks` | 10 | 7 | 6 | 6 |
| `g1_run_ticks` | 39,213,113 | 39,213,513 | 39,213,841 | 39,213,571 |
| `g1_run_ticks_per_exit` | 249,765 | 249,767 | 249,769 | 249,767 |
| `hart0_idle_permille` | 431 | 431 | 431 | 431 |
| `hart0_idle_ticks` | 17,581,822 | 17,581,899 | 17,581,702 | 17,581,717 |
| `hart0_records` | 138 | 138 | 138 | 138 |
| `hart0_run_ticks` | 40,707,084 | 40,707,081 | 40,706,874 | 40,706,875 |
| `hart0_wakes` | 2 | 2 | 2 | 2 |

**Budgets on the board.** The outbound rings' high-water marks,
`ring_peak` `0x1278` and `0x12b0`, are at most 29 percent of the budget,
half the `0x8000`-byte ring (`0x4000`; `BE_MVP:01`'s `ring_bytes`). The
runs took `0x26d233a` to `0x26d240c` ticks (`BE_MVP:13`), the longest
1.696 s at 24 MHz, against the run budget of `0x100000000` ticks
(178.957 s; `BE_MVP:07`'s `budget_ticks`). Each domain exited 157 times
against its ceiling of 2^20. The hart starts (`0x384` to `0x484` ticks)
are far inside their 2^24-tick bound. No budget was overrun (stop
condition 3).

**The board against QEMU.** The outcomes are the ones QEMU showed: the
hart 0 lines the expectation requires, in its order (the two domains'
`:09` to `:12` interleave differently on each platform, which the checker
allows), the same counters (157 exits, 65
lines, `ipi=1`, and `srst=1` per domain; 138 records), the probe lines in
the same form, and the same `payload` failure. The numbers differ, as
facts of each platform:

| Measure | K3 (this campaign) | QEMU (emulation facts) |
| --- | --- | --- |
| Hart 0's wakes for 138 records | 2 | 110 and 114 (`k3-like`, suite at `c5ecedee`); 112 and 112 (at `804fa95f`); 87 and 103 (kexec rehearsal at `c5ecedee`) |
| Alternations (K = 8) | 125 in every run | 101 and 87, 78 and 102, 87 and 77 (the same runs) |
| Hart 0 idle | 431 permille | 985 and 989 permille (`k3-like`, suite at `804fa95f`) |
| `ring_peak` | `0x1278`, `0x12b0` | at most `0x1c8` (suite at `c5ecedee`) |
| PING sent to receipt | 76 to 86 (domain 0), 47 to 55 (domain 1) ticks | 2,265 and 7,637 (domain 0), 892 and 465 (domain 1) ticks (`k3-like`, suite at `804fa95f`) |
| `hgatp` readback after the Sv48x4 write (the first, from the management root `0x8000000000102014`) and the Sv57x4 write, each with VMID `0x3fff` | `0x83fff00000102014`: the mode stayed Sv39x4 and the VMID became `0x3fff` | `0x8000000000102014`: unchanged |
| `vmid-shared` after the raw switch | A's value: a translation of root A cached under VMID 1 | B's value |
| IPI, median and range (ticks) | HS `0x1f` (`0x1e`-`0x38`); V=1 `0x21` (`0x20`-`0x23`) | HS `0x82` (`0x71`-`0x4b9`); V=1 `0xfa` (`0xed`-`0x277`) (GCC fixture) |
| `:09` `hedeleg` | `0xb15c` | `0xb15d` |

The probes' HSM states, fault encodings (`scause`, `stval`, `htval`,
`htinst`, `sepc`, `gva`), stale-read counts, and `vmid-distinct` result
are the same on both for the GCC probe images. QEMU's `c5ecedee` and kexec-rehearsal numbers are
recorded above; its `804fa95f` numbers are that check's `k3-like` runs in
`build/mvp/qemu/suite` (GCC on boot hart 6 after one refused attempt,
Clang on hart 0), the suite whose Clang probe records the platform record
also reads; its IPI numbers are the GCC probe fixture's, as the platform
record gives them. QEMU's ticks count QEMU's timebase, and its free
console wakes hart 0 about once per record; on the board the 115200-baud
console bounds hart 0, which drained the 138 records in two wakes with
the domains alternating 125 times of a possible 129.

**M0-5's exit criterion** ("Every capture passes its checker, or a stop
applies") **is met with no stop**: each of the eight captures passed the
capture checker in kexec mode on the board tool's run
(`BE_MVP_CAPTURE[kexec ...]: PASS`) and again from its retained excerpt
in the board record, the `payload` run by failing as declared; the
probes' facts include none of stop condition 6's; and the procedure ran in
the plan's order, a human resetting the board after each run. The first
campaign's stopped run (`build/mvp/k3-campaigns/20261024-com260/`, run
`20261025T022152Z`) stays stop-6 evidence, kept as the fixture
`k3-two-guests-gcc-stop6-alternations.log`, not a scenario result.

**Claim boundary.** This is diagnostic bring-up evidence from one COM260,
its firmware (Fedora's log: `SBI implementation ID=0x1 Version=0x10006`,
OpenSBI 1.6 in the B-series records), and one Fedora kernel. It is not
hardware validation, qualification, or formal verification, and it makes
no security claim: M0 runs no denial or fault-injection test between the
domains, whose isolation is by construction only (plan, "Claim boundary
and non-goals"). The probe values are facts for this board, and the
costs are recorded only.

### The board record and the platform record (M0-6, 2026-10-26)

**The first record.** On `l1` at 06:53 UTC,
`K3_RUN_ROOT=$PWD/build/mvp/k3-campaigns/20261025-com260 ./mvp/mvp board-evidence`
wrote the campaign's first board record, `results/20261025-com260/`
(`<repo>` is the checkout):

```text
BE_RETAIN: PASS runs=8 load_checks=2 files=73
ok   20261025T035453Z gcc probe-platform.json: recorded PASS, excerpt PASS
ok   20261025T072239Z gcc probe-vmid-distinct.json: recorded PASS, excerpt PASS
ok   20261025T073053Z gcc probe-vmid-shared.json: recorded PASS, excerpt PASS
ok   20261025T073242Z gcc two-guests.json: recorded PASS, excerpt PASS
ok   20261026T022021Z gcc two-guests.json: recorded PASS, excerpt PASS
ok   20261026T052617Z gcc two-guests.json: recorded PASS, excerpt PASS
ok   20261026T054220Z clang two-guests.json: recorded PASS, excerpt PASS
ok   20261026T061327Z gcc payload.json: recorded PASS, excerpt PASS
BE_MVP_PLATFORM_RECORD: PASS <repo>/mvp/results/20261025-com260 runs=8 probe_values=11 scenario_runs=4 qemu_gcc,clang=11,11
BE_MVP_EVIDENCE: PASS board <repo>/mvp/results/20261025-com260 runs=8 pass=8 fail=0 refused=0 stop=0
```

It verified (`./mvp/tools/evidence.py --verify` printed
`BE_MVP_EVIDENCE: PASS verify mvp/results/20261025-com260 files=75`: 75
files, 415,187 bytes, under a 74-line `MANIFEST.sha256`), and no file
matched B0's identifying-data rule. A board record holds each run's `run.txt`,
`load.txt`, `check.txt`, `result.json`, and kexec handoff excerpt; the two
load checks as `load-check/gcc-20261025T035420Z` and
`load-check/clang-20261025T035440Z`; the preflight; B0's `summary.md`,
`originals.sha256`, and `captures.txt`, which gives each raw serial
capture's SHA-256, bytes, and lines (the captures stay private, outside
the repository); `mvp/` with `bundle.txt`, `runs.tsv`, `images.sha256`
(146 images), the tool record and lock, and the scenario with its 15
expectation files; and the platform record, `platform-record.md` (592
lines in the first record) and `platform-record.json`.

The first record's `mvp/bundle.txt` records `source_commit=977dd4ee...` with
`source_tree=dirty changed=4`: the three M0-6 files then uncommitted
(`tools/evidence.py`, `tests/run-tool-dry-run.sh`, and
`tools/platform-record.py`) and one `?? mvp/results/` line, git's single
line for the then wholly untracked directory, which held the record's
load-check staging directory when the state was read (open item 41). It also records
`lock_sha256=8df124b9b362...`, `closure_sha256=56d91c92...`, and
`lock_check_status=1`: the record was written before QEMU was installed on
`l1` and before the lock refresh there (below), so it binds `804fa95f`'s
lock and closure, and its `mvp/tool-record.txt` stops at the first role
that failed, `BE_MVP_LOCK: FAIL qemu: /usr/bin/qemu-system-riscv64 is not
executable` (open item 41). The images it binds are the build's: its
`mvp/images.sha256` equals `tools/evidence.py --images build/mvp` on `l1`
after the refresh, line for line.

**The record at the M0-6 content.** The first record is superseded and
never committed. After the gates below, it is removed and made again by
the same command against the M0-6 content: expected are
`source_tree=clean`, the refreshed lock (`6e99262f04a1`) with
`lock_check_status=0`, and the platform record's Clang QEMU values from
the suite of the 08:16 UTC check. The commit after the M0-6 content adds
it, with its lines:

The gates passed again at the exact commit `13992d6d`, from a clean tree
(`./mvp/mvp check` 08:41:27-08:43:30 UTC: `BE_MVP_CHECK: PASS`,
`BE_MVP_QEMU: PASS runs=34 attempts=41 refused=7`, the dry run's
`tree-state` case `PASS ... changed=0`; `./mvp/mvp evaluate`
08:43:40-08:45:42 UTC: `host source=13992d6d... tree=clean images=146`,
`BE_MVP_IMAGE_IDENTITY: PASS images=146 same=146 differing=0`,
`BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`,
record `build/mvp-evaluator/record/20261026T084340Z`; `./mvp/mvp
kexec-rehearsal` 08:45:42-08:46:03 UTC: both `BE_MVP_KEXEC_REHEARSAL:
PASS`, Linux's kexec on hart 0 for GCC and hart 3 for Clang). Then, from
that clean tree, `K3_RUN_ROOT=$PWD/build/mvp/k3-campaigns/20261025-com260
./mvp/mvp board-evidence` wrote the record that is committed:

```text
BE_RETAIN: PASS runs=8 load_checks=2 files=73
ok   20261025T035453Z gcc probe-platform.json: recorded PASS, excerpt PASS
ok   20261025T072239Z gcc probe-vmid-distinct.json: recorded PASS, excerpt PASS
ok   20261025T073053Z gcc probe-vmid-shared.json: recorded PASS, excerpt PASS
ok   20261025T073242Z gcc two-guests.json: recorded PASS, excerpt PASS
ok   20261026T022021Z gcc two-guests.json: recorded PASS, excerpt PASS
ok   20261026T052617Z gcc two-guests.json: recorded PASS, excerpt PASS
ok   20261026T054220Z clang two-guests.json: recorded PASS, excerpt PASS
ok   20261026T061327Z gcc payload.json: recorded PASS, excerpt PASS
BE_MVP_PLATFORM_RECORD: PASS <repo>/mvp/results/20261025-com260 runs=8 probe_values=11 scenario_runs=4 qemu_gcc,clang=11,11
BE_MVP_EVIDENCE: PASS board <repo>/mvp/results/20261025-com260 runs=8 pass=8 fail=0 refused=0 stop=0
```

`evidence.py --verify` says `PASS verify mvp/results/20261025-com260
files=75`: 75 files, 415,186 bytes, a 74-line `MANIFEST.sha256` (SHA-256
`d56d95853c84b2999817d8acf69ea9d85a7502734358af4c5a222bccbefa9fdc`). Its
`mvp/bundle.txt` records `source_commit=13992d6d902131a6c19978b620724fad0524256f`,
`source_tree=clean`, `lock_sha256=6e99262f04a1...`,
`closure_sha256=2875ddd675b4...`, and `lock_check_status=0`, and its
`mvp/tool-record.txt` ends `BE_MVP_LOCK: PASS roles=29 host_only_skipped=0
closure=259 lock_sha256=6e99262f04a1`. Against the first record, every
run directory, excerpt, `check.txt`, `result.json`, load check, the
preflight, `summary.md`, `captures.txt`, `originals.sha256`, `runs.tsv`,
`images.sha256`, and the scenario are byte-identical; `bundle.txt`,
`tool-lock.conf`, `tool-record.txt`, and the manifest differ by the
provenance above, and the platform record (`platform-record.md` SHA-256
`6c0c90744bf49d331fa4843b5409f372a1fd296de495ccb0b3fc266df77d4946`,
`platform-record.json` `064b0af4abf543612c78c637c917733b5d80b6da9436ea64237e31777200e1aa`)
differs only in QEMU's Clang IPI timings (`ipi-hs` min, median, max
`0x33`, `0x3d`, `0x135` and `ipi-vs` `0x72`, `0x81`, `0xc0`, where the
08:16 UTC suite gave `0x73`, `0x82`, `0x424` and `0xf6`, `0x107`,
`0x195`) and in the three QEMU-suite source digests in Sources, emulation
facts of the suite of the 08:41 UTC check; every K3 value is the same.

**The platform record** answers the plan's "Platform record: probes and
negative images" for this campaign: written by `tools/platform-record.py`
(see [Harness](#harness-m0-4)) inside `board-evidence`, after B0's
retention and the excerpts' second judgement, and covered by the manifest
written again after it, every value with its source and every source file
with its SHA-256. Of its 11 probe values, nine matched the plan's
expectation on K3 (`hsm`, `hgatp`, the three `gpf` faults, both `ipi`,
`order-fenced`, and `vmid-distinct`) and two are facts by the plan's own
table (`order-unfenced`, 0 stale reads; `vmid-shared`, A's value); none
differs, so no stop applies. Each stands beside QEMU's values: the
in-tree GCC probe fixtures, judged again (`PASS
terminal=shutdown-requested`), and the Clang probe records of a QEMU
suite whose Clang probe images are the record's: in the first record,
the suite of `804fa95f`'s check (`qemu_gcc,clang=11,11`). From the preflight it tabulates the topology
the plan asked for (MVP plan Q12): eight `spacemit,x100` harts in two
clusters of four (`/cpus/cpu-map` `cluster0/core0` to `core3` for harts 0
to 3 and `cluster1` for harts 4 to 7; sysfs `cluster_id` 0 and 1 in one
package), each cpu node's `next-level-cache` phandle 1 or 2 by cluster,
and no device-tree node named `cache` to depth 3; `h` and Sstc on every
hart in the DT and cpuinfo, `mmu` `sv39`, `mvendorid=0x710`,
`marchid=0x8000000058000002`, and `mimpid=0x33d8a600`; a 24 MHz timebase;
Fedora's `SBI specification v2.0`, `SBI implementation ID=0x1
Version=0x10006`, HSM, and KVM's `highest G-stage page table mode is
Sv39x4` and `VMID 14 bits available`; System RAM
`0x102000000`-`0x2ffffffff` with 20 children; 11 FDT reservations, nine of
them outside System RAM; and every MVP extent free (`region_check=PASS`).
It then gives the scenario runs' counts, shutdown records, PING times,
guests' `elapsed_ms`, and costs, the ring and run budgets, and the fields
the four passing runs share or vary in, as above, and the `payload` run's
last two hart 0 lines.

**OpenSBI's prints are not in the record.** The plan expected the PMP and
domain regions that OpenSBI prints at power-on in the output-only capture.
Each retained excerpt starts at Linux's kexec handoff, and the operator's
picocom log on `l1` (`boot-7.log`, outside the repository; read on
2026-10-26) shows, after each legible reset, the boot ROM's lines,
`U-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)`, U-Boot proper, and
Fedora's kernel; no line of it holds `OpenSBI`, `Platform Name`,
`Domain0`, `PMP`, `Firmware Base`, or `Runtime SBI`. The U-Boot environment
it printed once names `opensbi_offset=1b0000` and the SPI NOR partition
`384K@1728K(opensbi)`. The firmware is visible only through SBI, as
Fedora's log shows, and its reserved memory through the FDT reservations
and `/proc/iomem`'s Reserved children. The platform record's "Serial log"
section says this in a paragraph written by hand into the generator (open
item 40).

**Determinism.** A copy of the first record without its two platform
files, given to `tools/platform-record.py` as it now stands with
`--qemu-suite build/mvp/qemu/suite` (then the suite of `804fa95f`'s
check), printed `BE_MVP_PLATFORM_RECORD: PASS
... runs=8 probe_values=11 scenario_runs=4 qemu_gcc,clang=11,11` and wrote
both files byte for byte (the first record's `platform-record.md` SHA-256
`6278493cf52d404fbd117c01434869737495eb26bbf0a512c82b2b27101f6b71`,
`platform-record.json`
`cecf0a48f5efc03138d8b3272a8a6f6a0dcae1ab9f0843ed0fa93fb8c1c8f1f0`).

### The host move and the lock refresh (on `l1`, 2026-10-26)

After run 4 the workspace and `build/` moved by rsync from the laptop
`lx2` to the workstation `l1` (32 CPUs). Installed on `l1` before its
first run (`rpm -q --qf '%{INSTALLTIME}'`, UTC) were
`openssh-10.2p1-16.fc44` and `openssh-clients-10.2p1-16.fc44` (2026-10-25
21:55), `glibc-langpack-en-2.43-9.fc44` and
`systemd-rpm-macros-259.10-1.fc44` (21:56), and `rpm-build-6.0.2-1.fc44`
(since 2026-08-02); QEMU and ShellCheck were absent. Runs 5 to 8 and the
board record were made so, the lock then naming `-14` for `ssh` and `scp`
(the board commands do not check the lock; open item 30). On the
responsible human's form answers `qemu=install-exact` and
`lock=refresh-ssh-scp` (2026-10-26):

- **QEMU:** `qemu-system-riscv-core-2:10.2.2-1.fc44` was installed from
  the RPM of Fedora's `fedora` repository, with its dependency
  `edk2-riscv64-20260812-8.fc44` (06:56 UTC);
  `/usr/bin/qemu-system-riscv64` has the lock's SHA-256,
  `df4a9e8a7a8a3f9f8dfa834af228127a722d86428e206728d28e0becb35413b3`.
- **ShellCheck:** `ShellCheck-0.11.0-4.fc44`, a closure support package
  that `l1` lacked, was installed from the verified cache's RPM (07:01
  UTC), whose SHA-256,
  `9de923ba57eac728c7590ba335f21f5f7fb6ccc1d0e9ace33e01dab7c953e122`, is
  the closure's recorded digest.
- **`./mvp/mvp tool-lock refresh`** reproduced 27 roles byte for byte and
  changed `ssh` and `scp`: `openssh-clients-10.2p1-14.fc44` (no longer in
  Fedora's repositories) to `-16.fc44`, `/usr/bin/ssh`'s SHA-256 from
  `ae339eda...` to `16cb2c6a...`, and `/usr/bin/scp`'s from `b40ee5c5...`
  to `87ae632a...`. The closure it derived grew from 257 to 259 packages
  (`closure_added=4 closure_removed=2`): `openssh` and `openssh-clients`
  `-14` to `-16` (in the closure through `git-core`'s requirement; open
  item 29), and two packages that `l1`'s installed set resolves and
  `lx2`'s did not: `glibc-langpack-en-2.43-9.fc44`, a second installed
  provider of `glibc-langpack` beside `glibc-all-langpacks`, and
  `systemd-rpm-macros-259.10-1.fc44.noarch`, since `systemd` requires
  `(systemd-rpm-macros = 259.10-1.fc44 if rpm-build)` and `l1` has
  `rpm-build-6.0.2-1.fc44` (open item 39).
- **`fetch-closure.py --record`** fetched the four new RPMs from Fedora's
  `updates` repository, each `signature=dbfcf71c6d9f90a6:OK` under the
  Fedora 44 key `36f612dcf27f7d1a48a835e4dbfcf71c6d9f90a6` and with an
  `installed=same` header digest, and recorded their SHA-256s (the cache's
  `SOURCES.tsv`: `updates`). `MVP_CLOSURE_SHA256` went from
  `56d91c92...` to `a21eb3dd...` at the refresh and to
  `2875ddd675b49c390159d55ac2847a9eb1990061bfe972693bd8260b2d123009` at the
  record (both files written at 07:02 UTC).

The lock's diff is the two roles' SHA-256 and package lines and
`MVP_CLOSURE_SHA256`; the closure's is the two OpenSSH lines replaced and
the two packages added; no other role, pin, or closure line changed. The
lock passes on `l1`:

```text
BE_MVP_LOCK: PASS roles=29 host_only_skipped=0 closure=259 lock_sha256=6e99262f04a1
```

**Rootless podman on `l1` (2026-10-26, 08:20 UTC).** The first
`./mvp/mvp evaluate` on `l1` stopped before its build:
`Error: default OCI runtime "crun" not found: invalid argument`
(`podman build exited 125`; record
`build/mvp-evaluator/record/20261026T082031Z`), with
`crun-1.28-1.fc44` installed (since 2026-08-02). The cause was the
account's rootless podman state: `~/.local/share/containers/storage/db.sql`,
whose `DBConfig` dates from 2025-12-04, when this account had uid 1000,
pinned `TmpDir=/run/user/1000/libpod/tmp` and
`RunRoot=/run/user/1000/containers`, while the account is now uid 501
(`XDG_RUNTIME_DIR=/run/user/501`), so podman could initialize no OCI
runtime (`podman --log-level=debug info`: `Configured OCI runtime crun
initialization failed: creating OCI runtime exit files directory: mkdir
/run/user/1000: permission denied`). That store held no named image. With
the responsible human asleep, the orchestrating session moved it aside,
reversibly, with
`mv ~/.local/share/containers ~/.local/share/containers.uid1000-stale-20261026`,
and podman then reported `runtime=/usr/bin/crun
runroot=/run/user/501/containers`; `podman system reset` was not run. No
package, lock role, or repository file changed: this is host state outside
the lock (open item 43).

**The gates at the M0-6 content,** all on `l1` from the wrapper. The code
is unchanged since them; the dry run's `tree-state` case changed once,
after `mvp check` and before `evaluate` (see
[M0-6's checks](#m0-6s-checks-on-l1-2026-10-26)), and this README after
them:

```text
BE_MVP_CHECK: PASS                      (08:16:19Z-08:18:23Z, 2 min 4 s; QEMU 34 runs, 37 attempts, 3 refused)
BE_MVP_EVIDENCE: PASS development <repo>/build/mvp/evidence/check files=159 images=146 qemu_attempts=37 rehearsals=2
BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655   (08:27:53Z-08:29:54Z, 2 min 1 s)
BE_MVP_LOCK: PASS roles=26 host_only_skipped=3 closure=259 lock_sha256=6e99262f04a1   (inside)
BE_MVP_QEMU: PASS runs=34 attempts=38 refused=4                                        (inside)
BE_MVP_IMAGE_IDENTITY: PASS images=146 same=146 differing=0
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=4 image=185396d1db7c kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=7 image=19a5f2d2e89d kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
```

`./mvp/mvp check` passed every stage: the lock
(`BE_MVP_LOCK: PASS roles=29 host_only_skipped=0 closure=259
lock_sha256=6e99262f04a1`), the host tests as
[below](#m0-6s-checks-on-l1-2026-10-26), the image checks
(`BE_MVP_IMAGE_CHECK: PASS gcc clang`, 91 mutations rejected for each
toolchain and 4 for each probe image), the variants and probes, the tools
check with the dry run's 17 cases (`tree-state` passing, `changed=7`), the
QEMU suite, the budgets, and the bundle. The suite's `gcc/k3-like` ran at
its first attempt on boot hart 0, `gcc/rva23` on hart 5, and `gcc/plic`
on hart 7 (`build/mvp/qemu/suite/attempts.tsv`). Its 37 attempts ran one
after another, about 1.4 s apart on average (the first capture closed at
08:17:31 UTC and the last at 08:18:22), the two-domain ones including the
guests' 1 s sleeps. The plan inferred 20 to 30 minutes for `mvp check`
(plan, "Tests and evidence"); it took 2 min 29 s to 2 min 39 s on `lx2`
(above) and 2 min 4 s on `l1`. The bundle's two rehearsals are those of
`804fa95f` on the same boot images (`kexec_harts=4`; and `kexec_harts=1,2,5`
after two refusals), which the bundle keeps while the boot image is
unchanged.

`./mvp/mvp evaluate` used the image that the 08:23:49 UTC run had built
from the verified cache with repositories disabled (record
`build/mvp-evaluator/record/20261026T082753Z`):

```text
BE_MVP_EVALUATE: host PASS roles=29 host_only_skipped=0 closure=259 lock_sha256=6e99262f04a1
BE_MVP_EVALUATE: host source=977dd4ee... tree=dirty changed=7 images=146
BE_MVP_EVALUATE: fetch PASS cache=<repo>/build/mvp-evaluator/rpms rpms=259 bytes=385621571 sources=fedora:116,updates:143
BE_MVP_EVALUATE: image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655 base=registry.fedoraproject.org/fedora@sha256:daf897befd7a78a52f11db5ca2229a4923991bb30709932770cb493f7a000cf0 closure_sha256=2875ddd675b4... containerfile_sha256=009c2eba5655d75193e1e8fc95ea1ae2362d3f583955781a8457aa03423c78ee closure_packages=259
BE_MVP_EVALUATE: image_id=05e75d8dea9e4d6cd0e8cde9386b3ae37d428f8e66741769904de53ac306cc53 rpms=293 rpms_sha256=1b9ae877326d14c6cebb827fb6a57564d7842f4760f5dc4766e7dbffdaccbf70
BE_MVP_EVALUATE: swap removed systemd-standalone-sysusers-259.7-1.fc44.x86_64 removed glibc-minimal-langpack-2.43-7.fc44.x86_64 removed rpm-build-libs-6.0.1-2.fc44.x86_64 removed rpm-sign-libs-6.0.1-2.fc44.x86_64 removed dnf5-plugins-5.4.2.1-1.fc44.x86_64 installed systemd-sysusers-259.10-1.fc44.x86_64
BE_MVP_LOCK: PASS roles=26 host_only_skipped=3 closure=259 lock_sha256=6e99262f04a1
BE_MVP_RUN_TOOL[tree-state]: SKIPPED (<repo>/mvp/tests is read-only; the case runs on the host)
BE_MVP_QEMU: PASS runs=34 attempts=38 refused=4
BE_MVP_EVIDENCE: PASS development <repo>/build/mvp/evidence/check files=148 images=146 qemu_attempts=38 rehearsals=0
BE_MVP_CHECK: PASS
BE_MVP_EVALUATE: BE_MVP_IMAGE_IDENTITY: PASS images=146 same=146 differing=0
BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655
```

The fetch kept every cached RPM; the image's transaction made the same
five named removals as M0-B with the 259-package closure, and the image
holds 293 packages, the closure's 259 and 34 of the base (its
`rpms.txt`). Inside, every gate passed with its host-only roles skipped,
the QEMU suite ran GCC's 17 runs in 18 attempts and Clang's in 20, and
the dry run's `tree-state` case was skipped on the read-only source tree;
all 146 images equalled the host's. `./mvp/mvp kexec-rehearsal`
(08:29:54Z-08:30:24Z, 30 s) then passed for both toolchains at their first
attempts, Linux's kexec on hart 4 (GCC) and hart 7 (Clang). So M0-4's
exit criteria hold again at the M0-6 content: `mvp check`, the kexec
rehearsal, and `evaluate` pass, with the images identical across the host
and the evaluator.

### `kernel-repro` again (on `l1`, 2026-10-26)

`make -C mvp kernel-repro` with `LINUX_GIT` naming the local Linux
mirror above, from the wrapper's clean environment on `l1`
(2026-10-26T07:39:02Z, 20 s
of wall time), rebuilt every guest output in a second tree from the same
pinned inputs with `--no-cache` and compared them with the first build:

```text
BE_B6_LINUX: PASS tag=v7.2 tag_object=237a1c39e8dfd3e1c6f1f023eea37a48ec04cc63 commit=8d3ae59288f1e7d58d76558a6ee96d533bc5019f
BE_MVP_GUEST_PINS: PASS files=10 image_bytes=1553332 image_size=0x1af628 text_offset=0x200000 init_bytes=4176 dtb_bytes=4096
BE_MVP_GUEST_BUILD: PASS kernel=built pins=match
BE_MVP_KERNEL_REPRO: PASS outputs=10 identical; sysroot_files=1065 sysroot_sha256=c931b51b8789ec8c57c2169a954d421ec8cc7aa3e5c7e5a951ec08a241cc1df0; kernel_build_seconds=10
```

The ten outputs equal their pins, and the sysroot is M0-1's
(2026-10-23, on `lx2`: the same 1,065 files and SHA-256); the kernel build
took 10 s with 32 jobs (`lx2`: 69 s with 8). Both builds ran on `l1`: its
first build, `build/mvp/guest`, was made there at 06:34 UTC
(`BE_MVP_GUEST_BUILD: PASS kernel=built pins=match`), after an attempt at
06:28 UTC to compare `lx2`'s first build, copied with `build/`, against a
second build on `l1` (`build/mvp/kernel-repro-m0-6-crosshost/`) found the
ten outputs identical and the normalized kernel `.config` different, which
`kernel-repro` refuses (`config.first config.second differ: char 381,
line 14`). `l1` has `rust-1.99.0-1.fc44` (`/usr/bin/rustc`) and
`dwarves-1.32-1.fc44` (`/usr/bin/pahole`), so Kconfig's toolchain probes
there wrote `CONFIG_RUSTC_VERSION=109900`, `CONFIG_RUST_IS_AVAILABLE=y`,
`CONFIG_RUSTC_LLVM_VERSION=220108`, `CONFIG_RUSTC_LLVM_MAJOR_VERSION=22`,
five `CONFIG_RUSTC_HAS_*=y` lines, and `CONFIG_PAHOLE_VERSION=132`, where
`lx2`'s `.config` has `CONFIG_RUSTC_VERSION=0`, `CONFIG_RUSTC_LLVM_VERSION=0`,
`CONFIG_RUSTC_LLVM_MAJOR_VERSION=0`, and `CONFIG_PAHOLE_VERSION=0`. Neither
package is a lock role or in the closure, and the pinned outputs do not
change (open item 42).

### M0-6's checks on `l1` (2026-10-26)

At the M0-6 content, after the lock refresh, none of them a QEMU run.
`./mvp/mvp host-test` (4 s), GCC = Clang, with M0-C's counts:

```text
BE_MVP_HOST: PASS ring scenarios=157 assertions=343230 gcc=clang
BE_MVP_HOST: PASS hart scenarios=652 assertions=140687 gcc=clang
BE_MVP_HOST: PASS sbi scenarios=41 assertions=13479 gcc=clang
BE_MVP_HOST: PASS gstage scenarios=16 assertions=21655 gcc=clang
BE_MVP_HOST: PASS payload scenarios=8 assertions=599 gcc=clang
```

`make -C mvp tools-check` (46 s, from the wrapper's clean environment):
the capture checker, the loader's test, the bundler's self-test, and the
board tools' dry run, sixteen cases in this run and seventeen with the
`tree-state` case of the fix below. The lines, with the `tree-state` line
of the orchestrating session's `make -C mvp lint tools-check` after the
fix in its place after `same-second`:

```text
BE_MVP_CAPTURE_SELF_TEST: PASS cases=36 failed=0
BE_MVP_CAPTURE_MUTATIONS: PASS mutations=154 rejected=154 seed=0x4d30
kexec-load self-test: 15/15 PASS images=10
BE_MVP_EVIDENCE_SELF_TEST: PASS cases=17/17
BE_MVP_RUN_TOOL[preflight-pass]: PASS (recorded COM260 facts, every extent free)
BE_MVP_RUN_TOOL[preflight-stops]: PASS (G0 and G1 window, hart region, staging, MVP region, no sstc, no h, no HSM)
BE_MVP_RUN_TOOL[load-check]: PASS (GCC and Clang at L, FDT at 0x108400000, unloaded)
BE_MVP_RUN_TOOL[probe]: PASS (3 of 3 probe runs, distinct boots)
BE_MVP_RUN_TOOL[campaign]: PASS (3 GCC, 1 Clang, payload as declared; BE_RETAIN: PASS runs=5 load_checks=2 files=58)
BE_MVP_RUN_TOOL[same-second]: PASS (two load checks of one UTC second both retained)
BE_MVP_RUN_TOOL[tree-state]: PASS (a record does not count its own staging directory; changed=7)
BE_MVP_RUN_TOOL[probe-record]: PASS (11 probe values, each matched or a fact)
BE_MVP_RUN_TOOL[kexec-refused]: PASS (a domain hart's boot is stop 6)
BE_MVP_RUN_TOOL[campaign-stop]: PASS (a refused run ends the campaign, not repeated; recorded as stop 6)
BE_MVP_RUN_TOOL[kexec-overlap]: PASS (the shim's overlap refusal fails the check)
BE_MVP_RUN_TOOL[kexec-fail]: PASS (a failure ends the wait and fails the check)
BE_MVP_RUN_TOOL[kexec-timeout]: PASS (no capture, timeout)
BE_MVP_RUN_TOOL[kexec-busy]: PASS (busy staging region and hart region refused)
BE_MVP_RUN_TOOL[kexec-not-tmpfs]: PASS (nothing staged off tmpfs)
BE_MVP_RUN_TOOL[kexec-tampered]: PASS (hash mismatch stops the load)
BE_MVP_RUN_TOOL[kexec-control-path]: PASS (a socket path too long stops before ssh)
BE_MVP_RUN_TOOL_DRY_RUN: PASS
BE_MVP_TOOLS_CHECK: PASS
```

`make -C mvp lint` (with `platform-record.py` among the parsed Python
files and `shellcheck` on the dry run) and `evidence-check` pass too
(`BE_MVP_MAKE_CONTROL_SELF_TEST: PASS cases=49`,
`BE_MVP_EVIDENCE_SELF_TEST: PASS cases=17/17`), before the fix and, in the
orchestrating session's run, after it.

**The tree-state fix** (open item 41). `evidence.py --board` read the
tree's state, `git status --porcelain=v1`, after `staging()` had created
the load checks' staging directory beside the record, so the state could
count the record's own staging directory: under a tracked `mvp/results/`,
which it is once a record is committed there (from the commit that adds
this campaign's record on), each new staging directory is one more `??`
line. Now
`board()` calls `source_state()` before `staging()` and passes the state
to `board_record()` as its last parameter, and `board_record()` no longer
reads it. The dry run's `tree-state` case, after `same-second`, takes
`git -C <repo> status --porcelain=v1 | grep -c .` itself, runs
`evidence.py --board` on the dry run's `campaign` directory with
`--out mvp/tests/.dry-run-tree-state-<pid>` (a tracked directory, standing
for `mvp/results/` once a record is committed there; the dry run's other
records are under `build/`, which git ignores), reads `source_tree=` from
the record's `mvp/bundle.txt` (`clean` as 0, `dirty changed=N` as N),
removes the record, requires that nothing named `*dry-run-tree-state-*`
is left under `mvp/tests/` (the record, or the staging directory, which
`staging()` names `..dry-run-tree-state-<pid>-load-checks.*`; the case
removes the same names before it starts), and fails unless the recorded
count equals git's. It discriminates: with the earlier `evidence.py` it fails,
`tree-state: the record counted changed=8, git status 7 (the staging
directory was counted)`, and with the fix it passes with the line above;
the counts are git's at that run. After the fix the orchestrating
session's `make -C mvp lint tools-check`, in the wrapper's clean
environment, printed `BE_MVP_MAKE_CONTROL_SELF_TEST: PASS cases=49`,
`BE_MVP_EVIDENCE_SELF_TEST: PASS cases=17/17`,
`BE_MVP_RUN_TOOL_DRY_RUN: PASS`, and `BE_MVP_TOOLS_CHECK: PASS`.

**The `tree-state` case inside the evaluator** (a finding during M0-6).
As first written, the case failed in the evaluator, which mounts the
source tree read-only (`evaluate.sh`: `-v "$tree:$tree:ro"`), so
`evidence.py --board` could not make its staging directory under
`mvp/tests/`. The 08:23:49 UTC `./mvp/mvp evaluate` (record
`build/mvp-evaluator/record/20261026T082349Z`) printed
`BE_MVP_EVIDENCE: FAIL [Errno 30] Read-only file system:
'<repo>/mvp/tests/..dry-run-tree-state-614-load-checks.7fkheqrx'`, then
`BE_MVP_RUN_TOOL_DRY_RUN: FAIL tree-state: board-evidence` and
`BE_MVP_EVALUATE: FAIL mvp check failed in
localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655 (exit 2)`. The
case now runs only where `mvp/tests/` is writable, and elsewhere prints
`BE_MVP_RUN_TOOL[tree-state]: SKIPPED (<repo>/mvp/tests is read-only; the
case runs on the host)`, as the comment above it says. So the dry run has
17 cases, one of them skipped inside the evaluator; the case runs in the
host's check. After that change (08:26:58 UTC) the dry run passed again on
the host (`build/mvp/records/run-tool-check.txt`, 08:27 UTC: 17 cases,
`BE_MVP_RUN_TOOL[tree-state]: PASS (a record does not count its own
staging directory; changed=7)`, `BE_MVP_RUN_TOOL_DRY_RUN: PASS`), it
still fails without the `evidence.py` fix (`changed=8`, git 7), the new
name pattern matches a staging-shaped name
(`..dry-run-tree-state-999-load-checks.abc`, checked by hand), and the
evaluator's run at 08:27:53 UTC printed the skip and passed (see
[The gates at the M0-6 content](#the-host-move-and-the-lock-refresh-on-l1-2026-10-26)).

The dry run's cases beyond M0-4's fourteen, and its checks of the
platform record:

| Case | Result |
| --- | --- |
| `campaign` | As at M0-4, and its record's platform record: `BE_MVP_PLATFORM_RECORD: PASS ... runs=5 probe_values=0 scenario_runs=4 qemu_gcc,clang=0,0`, both files listed in `MANIFEST.sha256`, and the ring budget's line |
| `same-second` (after M0-C's review, `f89366bc`) | The two load checks copied under one run directory name, `20000101T000000Z`: the record keeps both, as `load-check/gcc-20000101T000000Z` and `clang-...` (`BE_RETAIN: PASS runs=5 load_checks=2 files=58`) |
| `tree-state` (M0-6) | The campaign's board record made under the tracked `mvp/tests/`: its `source_tree=` count equals git's, taken before it (`changed=7` in the orchestrating session's runs), and nothing named `*dry-run-tree-state-*` is left behind. Skipped where `mvp/tests/` is read-only, as inside the evaluator, where it first failed (above) |
| `probe-record` (M0-6) | The probe campaign's board record: `BE_MVP_PLATFORM_RECORD: PASS ... runs=3 probe_values=11 scenario_runs=0 qemu_gcc,clang=11,11`, each of the 11 probe values `matched` or a `fact` against the plan's expectation |
| `campaign-stop` | As at M0-4, and its platform record: `runs=1 probe_values=0 scenario_runs=1` |

**Checker-to-monitor size** (S1 H43), counted at the M0-6 result content
(`13992d6d`) by M0-4's method, beside M0-4's count at `90fc9060`:

| Code | MVP at M0-6 | MVP at `90fc9060` | B7 |
| --- | --- | --- | --- |
| Monitor: `src/` and the shim (B7: `src/`, B3's shim reused) | 8,562 | 8,447 | 4,621 |
| Checkers: the capture and image checkers, `tools/budgets.py`, and (M0-6) `tools/platform-record.py` (B7: its capture, image, and marker checkers) | 5,931 | 5,333 | 6,244 |
| Host tests | 7,083 | 6,827 | 4,211 |
| Harness drivers and their tests: the QEMU driver, the rehearsal and its init, the dry run, the fake board, the loader's test | 2,375 | 2,275 | 1,926 |
| Checking code | 15,389 | 14,435 | 12,381 |
| Lines of checking code per monitor line | 1.80 | 1.71 | 2.68 |

Each cell is `wc -l` over the files its row names: `src/*` and
`shim/mvp-shim.S`; `tests/check-capture.py`, `tests/check-image.py`,
`tools/budgets.py`, and `tools/platform-record.py`; the five
`tests/*-test.c`; and `tests/run-qemu.sh`, `tests/kexec-rehearsal.sh`,
`tests/kexec-rehearsal/init.c`, `tests/run-tool-dry-run.sh`,
`tests/fake-board.py`, and `tests/test-kexec-load.py` (B7's files
unchanged). Since `90fc9060` the monitor gained M0-C's drain (115 lines in
`src/mvp-hart.{h,c}` and `src/mvp-runtime.c`, `129626e0`); the checkers
M0-C.2's changes to the capture checker (28 net, `c5ecedee`: the floor's
justification, the board's stop-6 fixture case, and the mutations' new
values) and the platform record's generator (570); the host tests the
drain-order test (256 net, `129626e0`); and the harness the dry run's
`same-second` case (30, `f89366bc`) and its platform-record checks and
`tree-state` and `probe-record` cases (70, M0-6). Without the generator
the ratio is 1.73; without the shim, 1.88; with the scenario generator
(753 lines) and the evidence bundler (999, 926 at `90fc9060`), 2.00. The
fixtures are data
and are not counted (MVP 1,803 lines in 12 files, B7 226). The ratio
stays below B7's and below the plan's inference from B7, about three to
one.

### M1-1 and M1-2 (at `0174f7a8` and `b591b187`, 2026-10-26)

M1 is implemented on the local branch `beryllium/mvp-m1`, from the M1
plan's acceptance record `41f88795` (plan `7b2c055c`), every step on the
workstation `l1`. M1-2 and M1-1, which the plan makes independent, were
made in parallel and committed in that order. The rows `mvp check`
printed for them were not kept; the counts below are the commits' pins
and files, and M1-4's checks print them again
([below](#m1-4-and-its-stop-stop-condition-6-plan-revision-m1-a)).

**M1-2, the channel in the G-stage** (`0174f7a8`). `src/mvp-layout.h`
gains the channel page, at most one (`BE_MVP_CHANNELS_MAX`):
`BE_MVP_CHANNEL_GPA` `0x84000000`, `BE_MVP_CHANNEL_HPA` `0x118000000`, and
`BE_MVP_CHANNEL_BYTES` `0x1000`; and each root's level-0 page, the first
spare page of its pool, `0x102039000` (G0) and `0x102041000` (G1). Static
assertions place the page directly above G1's window and outside the flat
image, the pool, the hart region, the MVP region, the staged image, the
kexec FDT, and both windows; its GPA directly above each guest's window;
and both in the windows' root entry and level-1 table, at level-1 index 32
and level-0 index 0. The channel travels in companion structures beside
M0's descriptor and map, whose shapes stay as they were
(`src/mvp-gstage.h`): `struct be_mvp_gstage_page` (the declared page, per
root), `be_mvp_gstage_leaf` (the leaf as walked), `be_mvp_gstage_channel`
(the sealed record), and `be_mvp_gstage_refusal` (the DETAIL fields).
`be_mvp_gstage_build_channel` writes level-1 entry 32's pointer and the one
leaf: the writer's `V R W U A D` (PTE `0x460000d7`), the reader's
`V R U A` (`0x46000053`), `X` in neither. `be_mvp_gstage_walk_channel`
accepts at most one pointer, at the page's index and onto this pool's
level-0 page, and in it exactly one leaf with `V U A R`, and `W` and `D`
both or neither; it refuses a second pointer, a pointer elsewhere, a
second leaf, any other bit, or a leaf when none is declared, and requires
every other pool byte zero. `be_mvp_gstage_channel_check` derives each
endpoint's declared leaf from the sealed record (map `V U A`, read `R`,
write `W D`), sharing nothing with the builder, and refuses any
difference, a window over the page, or the page over a pool; M0's pair
check and its rules stand. With no channel declared the pool bytes are
M0's. `BE_MVP_VARIANT_READER_WRITE` makes the builder write `W` and `D`
into every channel leaf, for the `reader-write` image. The G-stage host
test went from 16 scenarios and 21,655 assertions to 37 and 33,475, GCC =
Clang (the `Makefile`'s pins at `0174f7a8`), the plan's three host
mutation rows among them (a level-0 page holding a second leaf, the
reader's leaf with `W`, a second page both roots map).

**M1-1, the policy offline** (`b591b187`). `scenarios/te-poc/policy.te`
(25 lines) holds security model v1's Instance 2 verbatim in Part 2's
concrete syntax, and `scenarios/te-poc/scenario.json` (187 lines, schema
`be-mvp-scenario-v2`) the rest of the configuration: the labeling (G0
`writer_t`, G1 `reader_t`, the two windows, the shared page, the channel,
and the monitor's six extents), A4's need sets, the manifest (the domains
with their bindings and rights, the objects, and the one channel,
`channel0`, at GPA `0x84000000` and HPA `0x118000000`, the writer `read
write`, the reader `read`), the accepted-exit set with `denial`, each
init's role and denied accesses, and the expected lines, denials, and
report. `scenarios/te-poc/negatives/` holds the two build-time negatives:
`undeclared-flow.te` and `.json` (the policy plus the reader's `write`
rule on `shared_wr_t`) and `grant-without-rule.json` (the reader's rights
on `channel0` widened to `read write`). `tools/policy-check.py`, 890
lines (the plan's limit is 900), implements A1 to A6 and A8 as pure
functions over the parsed policy, labeling, need sets, and manifest,
records A7 as vacuous after checking that it is, checks the extents
against `src/mvp-layout.h`, and writes the authority report
(`be-mvp-authority-report-v1`; `-v2` since M7-4, which adds the `configuration` section). Its self-test has 33 cases, and each of
its seven mutations is rejected by the analysis it names alone. With the
checker, the scenario, and the generator unchanged since `b591b187`, the
final check before `804cd24c` (`build/mvp/m1b-scratch/check-final.txt`)
printed:

```text
BE_MVP_POLICY_SELF_TEST: PASS cases=33
ok A1: a rule naming an undeclared type: rejected by A1
ok A1: an object left unlabeled (hart_region): rejected by A1
ok A2: a rule whose target labels no object: rejected by A2
ok A3 alone: allow writer_t reader_mem_t : memory { map };, need included: rejected by A3
ok A4 alone: the writer's channel rule widened to { send receive }: rejected by A4
ok A5 and A6: a reader write rule on shared_wr_t, need included: rejected by A5,A6
ok A8 alone: the manifest granting G0 execute on shared_page: rejected by A8
BE_MVP_POLICY_MUTATIONS: PASS mutations=7 rejected=7
BE_MVP_POLICY: PASS scenario=te-poc grants=6 flows=1 checks=8 config=9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d
BE_MVP_POLICY_NEGATIVE: PASS name=undeclared-flow fails=A4,A5,A6 source_none=0 undeclared=0
BE_MVP_POLICY_NEGATIVE: PASS name=grant-without-rule fails=A8 source_none=1 undeclared=1
BE_MVP_POLICY_NEGATIVES: PASS negatives=2
```

The authority report (`build/mvp/gen/te-poc/authority-report.json`,
SHA-256 `fcbf210072d30c0d865c5219cc13a1d47ff17825bdd178e463e2c34d4beafdae`)
lists exactly six grants, each with the rule that allows it, and one
flow:

| Subject | Object | Permissions | Rule |
| --- | --- | --- | --- |
| G0 | `g0_window` | `execute map read write` | `allow writer_t writer_mem_t : memory { read write execute map };` |
| G0 | `shared_page` | `map read write` | `allow writer_t shared_wr_t : memory { read write map };` |
| G0 | `channel0` | `send` | `allow writer_t shared_wr_t : channel { send };` |
| G1 | `g1_window` | `execute map read write` | `allow reader_t reader_mem_t : memory { read write execute map };` |
| G1 | `shared_page` | `map read` | `allow reader_t shared_wr_t : memory { read map };` |
| G1 | `channel0` | `receive` | `allow reader_t shared_wr_t : channel { receive };` |

The flow is G0 to G1 through `shared_page`, `declared: yes`; the eight
checks pass, A7 as `vacuous: no domain holds a domain permission and no
delegation exists`, A6 as `F = D = {(writer_t, reader_t)}; F+ = D+`. Its
identities are the manifest's `0b7ff6d9...`, the policy's `4a1fac2b...`
(the SHA-256 of `policy.te`), the labeling's `570d026a...`, and the
configuration identity
`9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d`, which
the te-poc images link and print in `BE_MVP:03 CHANNEL_CHECKED`. The
undeclared-flow negative fails A4, A5, and A6 and the grant-without-rule
negative A8 alone, with one grant whose source is `none` and one flow
declared `no`; for each, `tools/gen-scenario.py` prints `BE_MVP_SCENARIO:
FAIL the policy check fails, so no header` and writes nothing (the
`Makefile`'s `policy-negatives`, in `check`).

`tools/gen-scenario.py` (753 lines, 1,516 since `b591b187`) reads a v1
scenario as before and a v2 one only after the policy check passes, and
writes into `mvp-scenario.h` the channel record in M1-2's structure order,
the accepted-exit set, and the configuration identity, and beside it the
`te-poc`, `reader-write`, and `no-inject` expectations and the report.
Its self-test runs per scenario: 36 cases for `two-guests` (34 at M0-4)
and 41 for `te-poc` (the M1-4 evaluator's run below). `two-guests`'
sixteen expectation files, its fifteen images' and `SCENARIO.txt`, are
byte-identical with M0's board record's (`diff -r build/mvp/gen/expect
mvp/results/20261025-com260/mvp/scenario/expect`, on the build of the M1-B
content). `tools/gen-dts.py` renders the init's role arguments, its eight
M0 renders unchanged. The `Makefile` takes `MVP_SCENARIO_NAME`, which the
Make controls admit (self-test 49 cases to 51), runs the policy check's
self-test and mutations in `lint` and the two negatives in
`policy-negatives`, and generates te-poc only for the offline targets
until M1-3 builds its images.

| File | Change | Why |
| --- | --- | --- |
| `src/mvp-layout.h` | The channel page's GPA, HPA, size, and count; each root's level-0 page; the static assertions above; the pool and scope comments (M1-2) | The plan's Q1 layout, fixed in the constants every tool reads |
| `src/mvp-gstage.h`, `src/mvp-gstage.c` | The page, leaf, channel, and refusal structures; `be_mvp_gstage_build_channel`, `be_mvp_gstage_walk_channel` (the walker's one new rule), and `be_mvp_gstage_channel_check`; the `reader-write` builder switch (M1-2) | The declared channel in each root, re-walked and checked against the sealed record; the plan's accepted-decision departures 1 and 2 |
| `tests/gstage-test.c` | The channel's build and walk, every walker and channel-check refusal, the plan's host mutations, and M0's roots byte for byte with no channel (M1-2) | Identical GCC and Clang output with pinned counts |
| `Makefile` | The G-stage pins (M1-2); `MVP_SCENARIO_NAME`, the policy check before the header, its self-test and mutations in `lint`, and `policy-negatives` in `check` (M1-1) | The counts above; the offline pipeline runs on every check |
| `scenarios/te-poc/policy.te`, `scenarios/te-poc/scenario.json` (new) | Instance 2 verbatim; the v2 scenario (M1-1) | The policy as specification and the configuration as data (Q7, Q8, Q10) |
| `scenarios/te-poc/negatives/` (new) | `undeclared-flow.te`, `undeclared-flow.json`, `grant-without-rule.json` (M1-1) | The two build-time negatives (Q11) |
| `tools/policy-check.py` (new) | A1 to A6 and A8, A7 vacuous; the report; the self-test and mutations (M1-1) | The offline checker (Q7) |
| `tools/gen-scenario.py` | Schema v2; the policy check before any header; the channel record, the accepted exits, and the identity in `mvp-scenario.h`; the te-poc expectations and report (M1-1) | v1 unchanged for `two-guests`; a failing check writes nothing |
| `tools/gen-dts.py` | The init's role arguments (M1-1) | The roles reach `/init` through `bootargs` |
| `tools/make-control.py` | `MVP_SCENARIO_NAME` admitted, with two self-test cases (M1-1) | The Make controls' allowlist |

### M1-3 (at `d3d28d7e`, 2026-10-26)

`d3d28d7e` adds the denial path, the channel on hart 0, and the `te-poc`
images. Its rows of `mvp check` were not kept either; the monitor's
sources did not change from `d3d28d7e` to M1-B, so the budgets measured
before M1-B (`build/mvp/m1b-scratch/budgets-before.txt`, 2026-10-27 at
17:09 UTC, on the M1-5 content) are M1-3's monitor's.

- **Hart 0.** It builds each root with its channel leaf from the sealed
  record the scenario header carries, re-walks it, runs the channel check
  over both walked maps and the record in place of the pair check, and
  prints `BE_MVP:03 CHANNEL_CHECKED` with the page, both level-0 pages,
  both leaf PTEs, and the configuration identity; a refusal is
  `BE_MVP:FAIL gstage` with `DETAIL channel=0 domain=<d> hart=<h>
  walked=<pte> declared=<pte>`, before any domain runs. It zeroes the page
  after the windows (`BE_MVP:05 CHANNEL_CLEARED`) and writes each hart's
  walked leaf into its block beside its map. A scenario with no channel
  boots as M0.
- **The decision.** The vector saves `vsstatus` at offset 352 of the exit
  record. In a scenario that accepts denials, `be_mvp_denial_decide`
  (`src/mvp-sbi.c`), a pure function of the exit record and the hart's
  own map and leaf, accepts exactly the plan's entry: a guest-page fault
  (cause 20, 21, or 23) from VU mode with a guest virtual address,
  `htval` below 2^39, `htinst` zero or the transformed load, store, or
  AMO, `vstvec` in Direct or Vectored mode, at a GPA the root does not
  map, or a store to the channel page whose leaf lacks `W`; everything
  else stays terminal.
- **The injection.** The domain hart writes `vscause` (1, 5, or 7),
  `vstval`, `vsepc`, and `vsstatus` (`SPP` from `SPVP`, `SPIE` from `SIE`,
  `SIE` clear) through `be_mvp_arch_inject` (`src/mvp-trap.S`), the one
  writer of those CSRs after arming, which reads each back (a difference
  is `FAIL controls`); posts one DENIAL record of twelve words and one IPI
  (a refused post is `FAIL ring`); and resumes the guest at `vstvec`'s base
  in VS mode through M0's tail.
- **The log.** SHUTDOWN gains the domain's denial count, which hart 0
  reconciles with the DENIAL records it drained, each printed as one
  `BE_MVP:DENY` line between the domain's `:10` and `:12`.
- **The images.** The `te-poc` images are built for both toolchains beside
  `two-guests`', with the `reader-write` variant (`mvp-gstage.o`
  recompiled with the builder switch) and the `no-inject` variant (the
  denial entry removed); the two te-poc DTBs carry the roles' arguments
  and are pinned (`guest/pins.txt`).

The host tests at `d3d28d7e` (the `Makefile`'s pins), GCC = Clang:

| Test | M0 | `d3d28d7e` |
| --- | --- | --- |
| `deny` (new) | none | 30 scenarios, 2,357 assertions |
| `hart` | 652, 140,687 | 722, 174,246 |
| `sbi` | 41, 13,479 | 53, 13,677 |
| `payload` | 8, 599 | 8, 622 |
| `ring`, `gstage` | 157, 343,230; 16, 21,655 | 157, 343,230; 37, 33,475 (M1-2) |

The image checker holds both new images to the plan's rules: the four
injected CSRs written after the R3 reset only by the arm helper and
`be_mvp_arch_inject`; that helper called from exactly one site in an image
that accepts denials (`te-poc`, `reader-write`) and from none in the
others; the vector's one `vsstatus` read, stored at offset 352; the
channel page disjoint from every other extent; and, in `te-poc`, the
linked channel record and configuration identity equal to the authority
report's. Its mutation test gains six defects for every image (a `vscause`
write outside the helper, a second call site of the helper, the helper's
skipped `vsstatus` readback, `vsepc` written from `a1`, the vector's
skipped `vsstatus`, and the channel page inside G1's window) and three
more where a channel is linked (an `hgatp` write on the denial path, the
linked identity differing from the report, the reader's linked rights
with `write`): 97 rejected for each toolchain's `two-guests` image, 91
before, and 100 for each `te-poc` image. The 22 budgets measured
(`budgets-before.txt`; [Budgets](#budgets-measured) has the current
ones) all passed: the accepted code extent's text ended at
`0x1_0200_4580` (GCC) and `0x1_0200_47b0` (Clang), `0x40` above M0's, and
the MVP region held `0x6798` and `0x6e48` bytes in the `two-guests`
images and `0x6e78` and `0x7508` in the `te-poc` images, of `0x40000`.

M1-3's QEMU runs were made by hand, outside the suite, whose v2 rules
came with M1-4; their captures are kept outside the repository. With
M0's guests still in the images, the `te-poc` monitor lines followed the
expectation through the guests' power-off, and `reader-write` printed
exactly its FAIL and DETAIL lines. A scratch bare-metal guest, not
committed, whose VU code made the accesses and whose VS handler printed
each trap, received every injected fault with the DENY fields the plan
states: loads, a store, an AMO, a compressed load, and a fetch (cause 20,
injected 1).

| File | Change | Why |
| --- | --- | --- |
| `src/mvp.h`, `src/mvp-sbi.c` | The exit record's `vsstatus`; the `denials` counter; the DENIAL record and its codec; the denial action and `be_mvp_denial_decide`; `be_mvp_inject_words`; SHUTDOWN's denial word; `exits = sbi + ipi + denials` | The denial decision as a pure, host-tested function in the SBI core (plan, "The denial path") |
| `src/mvp-trap.S`, `src/mvp-platform.h` | The vector's `vsstatus` store at 352; `be_mvp_arch_inject` with its readbacks; the hart page's channel leaf | One writer of the injected CSRs, with readback (plan, departure 4) |
| `src/mvp-hartmain.c` | `deny()`: decide, inject, post DENIAL, IPI, resume | The denial action's executor on each domain hart |
| `src/mvp-hart.h`, `src/mvp-hart.c` | `be_mvp_control_channel`; the control loop's DENIAL step and the SHUTDOWN reconciliation | Hart 0 checks each denial against its domain's phase and sequence |
| `src/mvp-runtime.c` | The channel's build, check, and clear on hart 0; the channel leaf in each block; `CHANNEL_CHECKED`, `CHANNEL_CLEARED`, and DENY lines | The boot-time channel check and the denial log (plan, "Markers") |
| `src/mvp-payload.h`, `src/mvp-payload.c` | The channel page among the extents a staged image must avoid | The page is an MVP extent |
| `tests/deny-test.c` (new) | The decision over every cause, region boundary, mode bit, `htval` alias, `htinst` form, and `vstvec` mode; the injected values and the `vsstatus` transform | Identical GCC and Clang output with pinned counts |
| `tests/hart-test.c`, `tests/sbi-test.c`, `tests/payload-test.c`, `tests/ring-test.c` | The DENIAL step and reconciliation in the interleavings; the denial action, counters, and codec; the te-poc DTBs and the channel page in the payload checks; the DENIAL record type in the ring's masks | The counts above |
| `tests/check-image.py` | The writer, call-site, vector, extent, and linked-record rules; the nine mutations; the te-poc profile | The plan's image-checker changes |
| `Makefile`, `tools.mk` | The `te-poc` images and their two variants for both toolchains; te-poc generated beside `two-guests`; the `deny` test and pins; the board images and `VARIANT=reader-write` and `no-inject` | The plan's images (Q11) |
| `guest.mk`, `guest/pins.txt`, `tools/gen-dts.py` | The two te-poc DTBs, rendered with the roles' arguments, and their pins | The guests learn their roles from `bootargs` |

### M1-4 and its stop (stop condition 6, Plan revision M1-A)

At `8c2cbbfd` and `65648204`, 2026-10-27. **The guest side**
(`8c2cbbfd`). `guest/mvp-kernel.config` (new) holds
exactly `CONFIG_DEVMEM=y` and `CONFIG_STRICT_DEVMEM=y`, merged after B6's
unchanged fragment (Q2). `tools/build-guest.sh` requires both values in
the final `.config` and compares it with the one B6's fragment alone
gives, stopping (stop condition 5) unless the two differ in exactly those
lines and `# CONFIG_IO_STRICT_DEVMEM is not set`, which STRICT_DEVMEM
makes visible; and it passes Kbuild's `RUSTC`, `BINDGEN`, and `PAHOLE` as
paths under `/dev/null/` (Q16), so the `.config` records
`CONFIG_RUSTC_VERSION=0`, `CONFIG_RUSTC_LLVM_VERSION=0`, and
`CONFIG_PAHOLE_VERSION=0` on every host, `l1` with its Rust and pahole
among them (`build/mvp/guest/kbuild/.config`, `MVP-GUEST-BUILD.txt`; open
item 42). `guest/initramfs.list.in` adds `/dev/mem` (`c 1 1`).
`guest/mvp-guest-id.h` gains the role parser, `mvp_role_args`
(`be.role=`, `be.channel=`, and `be.deny=` with at most two denied
accesses; anything malformed refused), host-tested with the guest-ID
rule in 74 cases (27 at M0), GCC = Clang. `guest/mvp-init.c` gains the
roles. Through `/dev/mem`, the writer fills the channel page with a
seeded 4,088-byte pattern, fences, writes the flag, and prints `MVPINIT
07` with its digest; the reader polls for the flag, fences, and compares
the digest, then makes its denied accesses. A SIGSEGV handler installed
through a raw `rt_sigaction` records `si_signo`, `si_code`, `si_addr`,
and the context's `pc`, and steps past the one fixed instruction of each
denied access, which the init reports as `MVPINIT 08`; without `be.role=`
the init prints exactly M0's lines. New pins: init `75084bb5...` (6,648
bytes), Image `5af37387...` (1,569,716 bytes, `image_size` `0x1b3628`,
from M0's 1,553,332 and `0x1af628`).

**The stop.** In QEMU (`k3-like`, GCC on boot hart 5 and Clang on boot
hart 7), with M1-3's monitor and this guest, every injected fault reached
the init as SIGSEGV with SEGV_ACCERR and `si_addr` at the access's label,
the handler ran, the init went on, both guests printed `RESULT pass`
before `BE_MVP:14`, the three DENY lines matched the guests' `MVPINIT 08`
reports, and `htinst` read `0x3303` for the loads and `0x3023` for the
store, the values M0's probe recorded on K3. But for each denial Linux
printed `init[1]: unhandled signal 11 code 0x2 at ...` and a register
dump: `unhandled_signal()` is true for the global init whatever handler
is installed (`kernel/signal.c:536-538@v7.2`), and `traps.c` prints when
it is (`arch/riscv/kernel/traps.c:119-127@v7.2`), so the plan's reading
held for every process but pid 1, and `unhandled signal` is one of M0's
rejected substrings. That is stop condition 6, and `8c2cbbfd` was
committed as stopped. Offered a child process (A), an exact rule for the
kernel's block (B), and a lower console loglevel (C), the responsible
human directed `A`: Plan revision M1-A (`planning/mvp-m1-plan.md`,
appended section, at `00051fc4`). The GCC capture is the fixture
`qemu-te-poc-gcc-stop6-pid1.log`, which the capture checker must reject
for its three `unhandled signal` lines alone.

**M1-A as implemented** (`65648204`). The init forks once after its
channel step; the child installs the handler, makes the role's denied
accesses in order, prints each `MVPINIT 08` line, and exits with its
failure count; the init waits for it and fails the run (`RESULT fail`) on
a fork failure, an abnormal exit, or a nonzero status. The child is not
pid 1, so the kernel prints nothing for a handled fault. New pins: init
`9682c97f...` (6,832 bytes), Image `17f0e98c...` (1,569,716 bytes); the
`.config` delta stayed the three declared lines, and the guest gates
passed on the M1-A content before `65648204`
(`build/mvp/m14-scratch/guest-gates-m1a.log`):

```text
BE_MVP_GUEST_PINS: PASS files=12 image_bytes=1569716 image_size=0x1b3628 text_offset=0x200000 init_bytes=6832 dtb_bytes=4096
BE_MVP_GUEST_ID_TEST: PASS cases=74 gcc=clang
BE_MVP_REFERENCE: PASS guests=2
BE_MVP_GUEST_BUILD: PASS kernel=built pins=match
BE_MVP_KERNEL_REPRO: PASS outputs=12 identical; sysroot_files=1065 sysroot_sha256=c931b51b8789ec8c57c2169a954d421ec8cc7aa3e5c7e5a951ec08a241cc1df0; kernel_build_seconds=10
```

The capture checker reads schema-v2 expectations and applies the plan's
reconciliation. For each domain the DENY lines, the `MVPINIT 08` reports,
and the expected denials agree in number, order, and fields: `seq`;
`gpa`; `htval` equal to the GPA shifted right by 2, compared as 64-bit
values; `stval` equal to `va` and `sepc` to `pc`; cause and injected
cause 21 and 5 or 23 and 7 by kind; `htinst` zero or the transformed
form; one `vstvec`. Each DENY line comes before its report, and every
report shows `signo=11 code=2 observed=1`, the store's also
`unchanged=1`. The writer's and the reader's digests are equal with
`match=1`; `CHANNEL_CHECKED` shows the report's channel, derived flags,
and configuration identity, and the report itself is checked (its
SHA-256, six grants with their rules, one declared flow, the checks);
`exits = sbi + ipi + denials`; only hart 0's lines are terminal; and
`reader-write`'s DETAIL and `no-inject`'s exit DETAIL are accepted as
declared. M0's twelve fixtures are judged against the guest pins they
were captured with, `tests/fixtures/m0-guest-pins.txt` (the M0 result's
`guest/pins.txt` verbatim, SHA-256 `094df190...`, which the checker
binds), and keep their verdicts, the board's stop-6 capture still failing
on the alternation floor alone. The new fixtures are the passing `te-poc`
GCC capture, `reader-write`'s, `no-inject`'s, and the pid-1 capture. The
self-test has 45 cases (36 before), and all 170 mutations are rejected:
M0's 154 and the plan's 15 rows, one in two forms.

The QEMU suite adds `te-poc` on `k3-like`, `rva23`, and `plic` and
`reader-write` and `no-inject` on `k3-like`, for both toolchains, each
judged with the report: 44 runs, M0's 34 and these ten. The kexec
rehearsal runs both `te-poc` boot images beside `two-guests`'. The
bundle gains the `te-poc` images, scenario, policy, report, and policy
records: 184 images, M0's 146 and 38 (each toolchain's six `te-poc`
monitor and boot files and six for each of its two variants, and the two
te-poc DTBs). On the M1-A content, before `65648204` was committed:

```text
BE_MVP_CAPTURE_SELF_TEST: PASS cases=45 failed=0
BE_MVP_CAPTURE_MUTATIONS: PASS mutations=170 rejected=170 seed=0x4d30
BE_MVP_QEMU_TOOLCHAIN[gcc]: runs=22 attempts=26 refused=4
BE_MVP_QEMU_TOOLCHAIN[clang]: runs=22 attempts=27 refused=5
BE_MVP_QEMU: PASS runs=44 attempts=53 refused=9
BE_MVP_BUDGETS: PASS measured=22
BE_MVP_EVIDENCE: PASS development <repo>/build/mvp/evidence/check files=210 images=184 qemu_attempts=53 rehearsals=0
BE_MVP_CHECK: PASS
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=6 image=28715505ff1a kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=3 image=5d68cdc0c25d kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=5 image=999543dc41be kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=4 image=01d20bfa9d15 kernel=7.3.0-rc4-gc1c7e254143f/4871aa91f05d
```

(`build/mvp/m14-scratch/check-1.log` and `rehearsal-1.log`: GCC's
`two-guests` and `te-poc` images, then Clang's.) Then `./mvp/mvp
evaluate` (record `build/mvp-evaluator/record/20261027T080219Z`, host
`source=00051fc4... tree=dirty changed=13 images=184`) reused the image
`localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`; inside it
the lock passed (`roles=26 host_only_skipped=3`), every gate passed, the
scenario self-tests printed `cases=41` (`te-poc`) and `cases=36`
(`two-guests`), and the QEMU suite ran 44 runs in 53 attempts with 9
refused; `BE_MVP_IMAGE_IDENTITY: PASS images=184 same=184 differing=0`.
In the passing `te-poc` fixture the writer's pattern reached the reader at
its first poll (`digest=0xeacaea8433f5c641`, `match=1`), the writer's load
from `0x84001000` and the reader's store to `0x84000ff8` and load from
`0x90000000` were each logged once, with `htinst` `0x3303` or `0x3023`,
and delivered as access faults that the child observed at its label, and
both guests went on to `RESULT pass`.

| File | Change | Why |
| --- | --- | --- |
| `guest/mvp-kernel.config` (new) | `CONFIG_DEVMEM=y`, `CONFIG_STRICT_DEVMEM=y` (`8c2cbbfd`) | The guest reaches the channel and its denied addresses through `/dev/mem` and nothing of its RAM (Q2) |
| `tools/build-guest.sh` | The fragment merged after B6's; the `.config` delta check; Kbuild's `RUSTC`, `BINDGEN`, and `PAHOLE` naming no executable (`8c2cbbfd`) | Stop condition 5's check; Q16 (open item 42) |
| `guest.mk`, `guest/initramfs.list.in` | The fragment among the guest inputs; `/dev/mem`; the guest-ID test's 74 cases (`8c2cbbfd`) | The kernel build's inputs; the init's device |
| `guest/mvp-guest-id.h`, `guest/mvp-guest-id-test.c` | The role parser and its host test (`8c2cbbfd`) | One parser shared by the init and its test |
| `guest/mvp-init.c` | The roles, the channel steps, the handler, and `MVPINIT 07` and `08` (`8c2cbbfd`); the denied accesses in a forked child, which the init waits for (`65648204`, M1-A) | The plan's guest programs; Plan revision M1-A |
| `guest/pins.txt` | The init's and Image's pins, twice (`8c2cbbfd`, `65648204`) | The rebuilt guest outputs |
| `tests/check-capture.py` | Schema-v2 expectations; the reconciliation; the channel and report rules; M0's fixtures against M0's pins; the new fixtures' cases; the plan's mutations (`65648204`) | The plan's capture checks ("Scenarios and the harness") |
| `tests/fixtures/qemu-te-poc-gcc.log`, `qemu-reader-write-gcc.log`, `qemu-no-inject-gcc.log`, `qemu-te-poc-gcc-stop6-pid1.log`, `m0-guest-pins.txt` (new) | M1's QEMU captures, CRs removed, and the guest pins M0's fixtures were captured with (`65648204`) | The self-test's and mutations' bases; the pid-1 capture stays rejected |
| `tests/run-qemu.sh` | The `te-poc` runs on three machines and its two variants on `k3-like`, each with the report (`65648204`) | 44 runs |
| `tests/kexec-rehearsal.sh` | An optional authority report for a `te-poc` image (`65648204`) | The rehearsal of both `te-poc` images |
| `tools.mk` | The `te-poc` rehearsal and QEMU inputs (`65648204`) | The harness targets |
| `tools/evidence.py` | The `te-poc` images, scenario, policy, report, and policy records in the bundle (`65648204`) | The plan's evidence |
| `Makefile` | The policy check on `te-poc` recorded with its report, and its self-test and mutations recorded, for the bundle (`65648204`) | The evidence of the offline checks |

### M1-5's tools (at `9020c4f8`, 2026-10-27)

Under Q14 and Q18 and the plan's "The remote reset", `9020c4f8` adds
the remote reset, opt-in per invocation (`K3_RESET=k3ctl`), and the board
selector, all off the board.

- **The reset** (`tools/k3-run.sh`). After a run, and only when every
  condition holds in the plan's order: the capture holds Linux's kexec
  handoff and, after it, hart 0's terminal line by the expression anchored
  at the start of a line, within the wait; the capture checker's verdict
  is `PASS` (a negative image failing as declared included); one SSH probe
  on a fresh connection finds Fedora down (no answer, no route, or a
  timeout; the run's own boot ID is stop 10, a new one means the human
  reset the board, and anything else is inconclusive and stops); and
  `status` reads `rst=0 fcrec=0 pwr=0` and `ver=1.0`. Then one `reset`,
  whose reply must be `OK reset`, `status` again, a bounded wait for a new
  boot ID (`K3_RESET_RETURN_SECONDS`, default 300; a timeout is stop 10),
  and M0's settle wait. The client runs only as `status` or `reset`, from
  one function with a case guard and a fixed argument vector, by the
  locked Python 3. Every run writes `reset.txt` (the method, the client's
  SHA-256 and the pin, both `status` replies, the `reset` reply, the UTC
  times, the boot IDs before and after, the seconds to the new one, and
  the outcome); on the default path its method is `human` and the run's
  other files are M0's byte for byte.
- **The pin** (`tools/k3ctl.sha256`, new). The client's SHA-256,
  `7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec`, and
  the forms of its path and device; every board target passes the file
  (`K3CTL_PIN`), and a client that differs stops before any run.
- **The campaign** (`tools/k3-campaign.sh`). It ends at the first run
  that does not pass, with no reset. On the human path a wait that times
  out prints `BE_MVP_K3_CAMPAIGN: PAUSED` with the runs left and exits 75
  instead of `STOP` (Q18; M0 open item 38).
- **The preflight and loader** (`tools/k3-preflight.sh`,
  `tools/kexec-load.py`). The preflight records the firmware identity
  from Fedora's log and stops on one other than M0's record (`ID=0x1
  Version=0x10006`; stop 8), and records the client's SHA-256 against the
  pin; the layout rule gains the channel page as the ninth MVP extent.
- **The selector** (`tools.mk`, `mvp`, `tools/make-control.py`).
  `SCENARIO=two-guests|te-poc` selects the board scenario, `two-guests` by
  default; `VARIANT=reader-write` or `no-inject` implies `te-poc` and
  `payload` `two-guests`; te-poc runs are checked with the authority
  report. The wrapper passes `K3_RESET`, `K3CTL`, `K3CTL_DEV`, and
  `K3_RESET_RETURN_SECONDS` to the `k3-*` commands only, and the Make
  controls admit `SCENARIO` (self-test 51 cases to 55).
- **The records** (`tools/evidence.py`, `tools/platform-record.py`). The
  board record retains each run's `reset.txt` under its manifest (B0's
  retention, whose file list is fixed, does not), the policy check on
  `te-poc` and its report, and the campaign's `serial-log-note.txt`, and
  finds te-poc's expectations; the platform record gains the resets and
  reads its Serial log paragraph from that note, written by hand for each
  campaign (M0 open item 40).
- **The dry run** (`tests/fake-k3ctl.py`, new; `tests/fake-board.py`;
  `tests/run-tool-dry-run.sh`). The fake dongle answers from a JSON spec
  and refuses anything but `ping`, `status`, and `reset`; the fake board
  goes down after a kexec and comes back after an acknowledged reset. The
  dry run gains 23 cases, 40 in all: the `te-poc` campaign with six
  resets and its board record, no terminal marker, a late terminal line, a
  failing run, a domain line holding the terminal text, Fedora answering
  with the run's boot ID, a human's reset first, an inconclusive probe, a
  boot ID that does not change, `fcrec` held, another version, dongle
  errors, an `ERR` reply, `rst` held after the reset, a client that
  differs from the pin, the fake dongle's refusals, the `PAUSED` wait, the
  human path's `reset.txt`, the M1 preflight, the `te-poc` load checks
  and selector, and the command-log assertion that every fake dongle
  received only `ping`, `status`, and `reset`. `tests/test-kexec-load.py`
  checks the channel page on B7's recorded map and on M0's board record's
  (pinned by SHA-256), with every refusal: 16 cases on 16 images.

`./mvp/mvp check` passed at the exact commit, from 09:26:04Z to 09:30:15Z
(`build/mvp/m1-gates/check-9020c4f8.log`), with these rows beyond M1-4's:

```text
BE_MVP_MAKE_CONTROL_SELF_TEST: PASS cases=55
kexec-load self-test: 16/16 PASS images=16
BE_MVP_EVIDENCE_SELF_TEST: PASS cases=25/25
BE_MVP_RUN_TOOL_DRY_RUN: PASS
BE_MVP_TOOLS_CHECK: PASS
BE_MVP_QEMU_TOOLCHAIN[gcc]: runs=22 attempts=27 refused=5
BE_MVP_QEMU_TOOLCHAIN[clang]: runs=22 attempts=25 refused=3
BE_MVP_QEMU: PASS runs=44 attempts=52 refused=8
BE_MVP_EVIDENCE: PASS development <repo>/build/mvp/evidence/check files=223 images=184 qemu_attempts=52 rehearsals=4
BE_MVP_CHECK: PASS
```

The checking code then stood at 1.994 lines per monitor line by M0-6's
count with the six host tests and the fake dongle (19,968 and 10,012;
see [M1-6](#m1-6-2026-10-27)).

| File | Change | Why |
| --- | --- | --- |
| `tools/k3-run.sh` | The anchored terminal expression; the reset path, its conditions, its one function for the client, and `reset.txt`; the te-poc report in the run's check | The remote reset (Q14) |
| `tools/k3-campaign.sh` | No reset after a run that does not pass; `PAUSED` with exit 75 on the human path | Q14; Q18 (M0 open item 38) |
| `tools/k3-preflight.sh` | The firmware identity and its stop; the client's SHA-256 against the pin | Stop 8; the pinned client |
| `tools/kexec-load.py`, `tests/test-kexec-load.py` | The channel page as an MVP extent at preflight and load; its cases on B7's and M0's recorded maps | The plan's "Memory and load paths" |
| `tools/k3ctl.sha256` (new) | The client's pin | `k3ctl` is not a lock role ("Tool lock and the clean evaluator") |
| `tests/fake-k3ctl.py` (new), `tests/fake-board.py`, `tests/run-tool-dry-run.sh` | The fake dongle; the board's boot ID after a reset; 23 more cases | The plan's dry run of the remote reset |
| `tools.mk`, `mvp`, `tools/make-control.py` | `SCENARIO`, the variants' scenarios, and the pin file for every board target; the reset settings passed to the `k3-*` commands | The `te-poc` board runs |
| `tests/check-capture.py` | `--check-image` and `--write-fixtures` with a v2 expectation and the report | The board tools' image check and the dry run's te-poc captures |
| `tools/evidence.py`, `tools/platform-record.py` | `reset.txt`, the policy records, and the serial-log note in the board record; the platform record's resets and its note | The plan's "Platform record" (resets, serial log) |

### M1-5's first board campaign and its stop (stop condition 6, Plan revision M1-B)

On the responsible human's confirmation that the K3 was free
(`planning/HANDOFF.md`), the first campaign ran on 2026-10-27, from 09:31 to
09:41 UTC, on the COM260 (K3) with the images of `9020c4f8`, whose monitor
is M1-3's and guest M1-A's, and the Fedora host kernel
`7.3.0-65.1.riscv64.omni.fc45.riscv64`, through RAM-only `kexec_load` runs
from Fedora, each followed by one `k3ctl` reset; the human reset nothing by
hand during it. Its records are `build/mvp/k3-campaigns/20261027-com260/`
(not a retained board record). The preflight passed, its firmware identity
M0's record's and the channel page free; its record was later overwritten by
the second campaign's preflight at the same path. The two `te-poc` load
checks (`build/mvp/k3-load-checks/gcc/20261027T093101Z` and
`clang/20261027T093122Z`) loaded the GCC (`5d68cdc0c25d`) and Clang
(`01d20bfa9d15`) images at L (`loader=kexec_load entry=0x108000000
fdt=0x108400000 image_memsz=0x227000 fdt_bytes=49280 kexec_loaded=1`) and
unloaded them. Every Linux handed over from hart 0:

| Run | Image | Boot ID before | Result | Reset |
| --- | --- | --- | --- | --- |
| `20261027T093200Z` | GCC `te-poc` (`5d68cdc0c25d`) | `7c610c9b-ed64-4830-beea-145ba82a1b57` | PASS | `reset`, 33 s |
| `20261027T093322Z` | GCC `te-poc` | `6dd01f64-3102-4beb-99f4-83af377b1531` | PASS | `reset`, 34 s |
| `20261027T093444Z` | GCC `te-poc` | `80f84c69-2a86-461c-adf7-7b80ff9addf5` | PASS | `reset`, 34 s |
| `20261027T093652Z` | Clang `te-poc` (`01d20bfa9d15`) | `9e8410e4-078a-4f15-8ea1-fc3d643e2b3e` | PASS | `reset`, 33 s |
| `20261027T093835Z` | GCC `reader-write` (`fd0db550d89e`) | `2ec9ca33-9c2a-4bb4-b4df-910fc8d64c6a` | PASS as declared: `BE_MVP:FAIL gstage` and its channel DETAIL | `reset`, 43 s |
| `20261027T094024Z` | GCC `no-inject` (`34ebc90fdfb7`) | `db502b86-bea4-4445-bd57-550515946643` | FAIL: two FAIL and DETAIL pairs (stop condition 6) | none: `reset_outcome=no-reset-verdict` |

The four `te-poc` runs each passed with `exits_g0=163 exits_g1=167
denials_g0=1 denials_g1=2 records=146 wakes=2 alternations=127 g0=67
g1=68` (`check.txt`); the seconds are each `reset.txt`'s
`seconds_to_new_boot_id`, every `status` before a reset read `rst=0
fcrec=0 pwr=0 k3=n/a` and `ver=1.0`, and every reply was `OK reset`. The
`no-inject` run's capture held, after both `BE_MVP:10` lines and 89 guest
lines, both domain harts' own FAIL and DETAIL lines and no line from hart
0's terminal path ([Plan revision M1-B](#plan-revision-m1-b) gives the
lines and the corrected diagnosis: both domain harts took Q10's fallback,
whose 2^24-tick window measured hart 0's latency behind the 115200-baud
console, not its progress). The tool withheld the reset and ended the
campaign (`BE_MVP_K3_CAMPAIGN: STOP run 1/1 exited 1; a stop condition
applies, and the remaining runs are not made`), and the board stayed
halted until a `k3ctl` reset at 17:45 UTC, before the second campaign's
preflight (its `serial-log-note.txt`). Offered a wider `no-inject`
expectation (A), a change to M0's failure path so that only hart 0
prints (B), and dropping `no-inject` from the board campaign (C), the
responsible human directed `accept B, proceed`: Plan revision M1-B
(`745c293a`, implemented at `804cd24c`). This campaign's six runs are the
record of the stop; its five passing runs are not M1's board evidence,
because their images are not the revised commit's (M1-B.3; open item
46). The stopped run's capture, CRs removed, is the fixture
`k3-no-inject-gcc-stop6-fallback.log`.

### M1-5's second board campaign (2026-10-27)

With the images of `804cd24c` (Plan revision M1-B), on the same COM260 and
Fedora kernel, through the same RAM-only `kexec_load` path with one `k3ctl`
reset after each run, on 2026-10-27 between 17:45 and 18:02 UTC; automation
never typed at U-Boot and the human reset nothing by hand. The campaign
directory is `build/mvp/k3-campaigns/20261027-com260-m1b/`, whose
`summary.md` says `Boot marker reproduced: 6/6 runs` and `Distinct boots: 6
of 6 runs`, with `serial-log-note.txt` written by hand from the operator's
picocom log; this is the campaign M1 presents.

- **The preflight** (`build/mvp/k3-preflight/preflight.txt`,
  `captured_utc=2026-10-27T17:45:56Z`) passed: `firmware_identity=ID=0x1
  Version=0x10006` equal to `firmware_expected`, the client matching its
  pin (`workstation_k3ctl_client=matches-pin`), and every MVP extent free
  (`region-check.txt`: the accepted image, the pool, the hart region, the
  MVP region, the staging region, both windows, and
  `channel-page=0x118000000-0x118001000`, against 20 System RAM children
  and 11 FDT reservations; `region_check=PASS`).
- **The load checks** (`build/mvp/k3-load-checks/gcc/20261027T175222Z` and
  `clang/20261027T175244Z`) loaded the GCC (`a55a5791b4b4`) and Clang
  (`e32de2439ef0`) `te-poc` images at L, each checked with te-poc's
  expectation and report, and unloaded them (`kexec_loaded_after_unload=0`).

The runs (UTC; every Linux handed over from hart 0, `Will call new kernel
at 108000000 from hart id 0`, and every `BE_MVP:02` printed
`started=none`):

| Run | Image | Boot ID before | Result | Reset |
| --- | --- | --- | --- | --- |
| `20261027T175315Z` | GCC `te-poc` (`a55a5791b4b4`) | `42cc2284-9b93-4e19-8064-8eaa3ce7850f` | PASS | `reset`, 43 s |
| `20261027T175447Z` | GCC `te-poc` | `0485b932-d1c2-4f2c-bb15-29ad5945148f` | PASS | `reset`, 34 s |
| `20261027T175609Z` | GCC `te-poc` | `2e3e66da-c0cf-48ad-bfa9-5dae86f8c427` | PASS | `reset`, 47 s |
| `20261027T175803Z` | Clang `te-poc` (`e32de2439ef0`) | `6d736976-b029-4196-9155-b7ae285433ba` | PASS | `reset`, 34 s |
| `20261027T175944Z` | GCC `reader-write` (`c575bc03d456`) | `ce55db02-0d3b-4b73-88d1-178ccbbd046b` | PASS as declared: both `:03 GSTAGE_BUILT_REWALKED` lines, then `BE_MVP:FAIL gstage` and `BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053`; no domain ran (`g0=0 g1=0`) | `reset`, 33 s |
| `20261027T180124Z` | GCC `no-inject` (`4cb0df81bcdb`) | `7f9d0663-788d-4d38-86e6-98e3a20c5d4b` | PASS as declared: after 54 lines from each guest, both `MVPINIT 07 CHANNEL` lines among them, exactly one FAIL and DETAIL pair, hart 0's: `BE_MVP:FAIL guest-page-fault`, `BE_MVP:DETAIL domain=0 hart=1 cause=0x15 ... htval=0x21000400 htinst=0x3303 ... exits=94` | `reset`, 43 s |

Each run's `run.txt` names its image's SHA-256, which the board tool's
image check confirmed before the load (`BE_MVP_BOOT_IMAGE[gcc]: PASS
...`), and its expectation (`te-poc.json` `4aeedbbb6b65...`,
`reader-write.json` `4ef6dffd7f95...`, `no-inject.json`
`ccc747e606a2...`) and authority report (`fcbf210072d3...`); the four
board images equal the bundle's from the M1-B content's check
(`build/mvp/evidence/check/images.sha256`). Each `reset.txt` shows the
probe finding Fedora down (`ssh: connect to host ... Connection timed
out`), `status` before and after the reset at `rst=0 fcrec=0 pwr=0
k3=n/a ver=1.0`, `reset_reply=OK reset`, the new boot ID (the next run's
"before"), and `outcome=reset`; each run's `check.txt` ends
`BE_MVP_CAPTURE[kexec te-poc]: PASS` (or `reader-write`, `no-inject`).
The `no-inject` run is M1-B's check on the board: where the first
campaign's run printed two FAIL and DETAIL pairs, this one printed only
hart 0's, as M1-B.2 says every run that ends in a domain's failure now
does.

**The `te-poc` runs.** All four passed with the same counts:
`exits_g0=163 exits_g1=167 denials_g0=1 denials_g1=2 records=146 wakes=2
alternations=127 g0=67 g1=68`, overlaps of `0x25405a7` to `0x2540615`
ticks of the shorter interval's `0x2563e5e` to `0x2563ed6`. Run 1's
channel and denial lines (GCC; the other three differ only in times and
the guests' virtual addresses):

```text
BE_MVP:03 CHANNEL_CHECKED channel=0 writer=0 reader=1 gpa=0x84000000 hpa=0x118000000 bytes=0x1000 level0=0x102039000,0x102041000 writer_pte=0x460000d7 reader_pte=0x46000053 config=9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d
BE_MVP:05 CHANNEL_CLEARED channel=0 hpa=0x118000000 bytes=0x1000 ticks=0x17
BE_MVP_G0: MVPINIT 07 CHANNEL role=writer gpa=0x84000000 bytes=4088 digest=0xeacaea8433f5c641 flag=0x42454d314348414e
BE_MVP_G1: MVPINIT 07 CHANNEL role=reader gpa=0x84000000 bytes=4088 digest=0xeacaea8433f5c641 polls=1 match=1
BE_MVP:DENY hart=1 domain=0 seq=1 kind=unmapped cause=0x15 injected=0x5 gpa=0x84001000 htval=0x21000400 htinst=0x3303 stval=0x3fb9b55000 sepc=0x112bc vsstatus=0x200000022 vstvec=0xffffffff800af0b8 ticks=0x81111 service=0x24
BE_MVP:DENY hart=2 domain=1 seq=1 kind=read-only cause=0x17 injected=0x7 gpa=0x84000ff8 htval=0x210003fe htinst=0x3023 stval=0x3f941a4ff8 sepc=0x112c8 vsstatus=0x200000022 vstvec=0xffffffff800af0b8 ticks=0xa64b3 service=0x13
BE_MVP_G0: MVPINIT 08 DENIED n=1 kind=load gpa=0x84001000 va=0x3fb9b55000 pc=0x112bc signo=11 code=2 observed=1
BE_MVP_G1: MVPINIT 08 DENIED n=1 kind=store gpa=0x84000ff8 va=0x3f941a4ff8 pc=0x112c8 signo=11 code=2 observed=1 unchanged=1
BE_MVP:DENY hart=2 domain=1 seq=2 kind=unmapped cause=0x15 injected=0x5 gpa=0x90000000 htval=0x24000000 htinst=0x3303 stval=0x3f941a3000 sepc=0x112bc vsstatus=0x200000022 vstvec=0xffffffff800af0b8 ticks=0xa6867 service=0xe
BE_MVP_G1: MVPINIT 08 DENIED n=2 kind=load gpa=0x90000000 va=0x3f941a3000 pc=0x112bc signo=11 code=2 observed=1
BE_MVP:12 DOMAIN_SHUTDOWN hart=1 domain=0 exits=163 sbi=161 ipi=1 base=14 time=0 dbcn_write=102 dbcn_read=44 dbcn_byte=0 srst=1 refused=0 lines=67 ring_peak=0x1420 entered=0x58b ticks=0x2564429
BE_MVP:12 DOMAIN_SHUTDOWN hart=2 domain=1 exits=167 sbi=164 ipi=1 base=14 time=0 dbcn_write=104 dbcn_read=45 dbcn_byte=0 srst=1 refused=0 lines=68 ring_peak=0x1558 entered=0x23e26 ticks=0x25899bc
BE_MVP:13 RUN_COMPLETE domains=2 records=146 wakes=2 idle_ticks=0xdfe899 overlap_ticks=0x2540603 ticks=0x26d35f7
BE_MVP:14 SHUTDOWN type=0 reason=0
```

In every run the writer's 4,088-byte pattern reached the reader at its
first poll with equal digests (`match=1`); the three denied accesses
were each logged once, in the guest's order, with `htval` the GPA
shifted right by 2, `htinst` `0x3303` for the loads and `0x3023` for the
store (K3's values for VU-mode accesses through Linux's VS stage, equal
to M0's VS-mode probe values), `injected` 5 or 7, `vsstatus`
`0x200000022`, and one `vstvec`, and each was observed by the child at
its label (`signo=11 code=2 observed=1`, the store `unchanged=1`); each
domain then ran to its shutdown with `exits = sbi + ipi + denials` (163 =
161 + 1 + 1 and 167 = 164 + 1 + 2). The service ticks (post minus exit)
were `0x1c` to `0x25` for G0's denial and `0xd` to `0x18` for G1's.
`:09` read back `hedeleg=0xb15c` on both domain harts, as in M0. The
outbound rings' high-water marks, `0x1420` and `0x1558`, are at most 34
percent of the budget, half the `0x8000`-byte ring, and the runs took
`0x26d35f4` to `0x26d36c5` ticks, 1.696 s at 24 MHz, against the
`0x100000000`-tick run budget; no budget was overrun. In QEMU the same
images' six `te-poc` suite runs (`build/mvp/qemu/suite`, the M1-B
content's check) gave the same denials, 146 records, and 67 and 68
lines, with `exits_g0=163` (164 in GCC's `plic` run), 93 to 123 wakes,
and 51 to 101 alternations, where the board, behind its 115200-baud
console, gave 2 wakes and 127 alternations.

**The unplanned `two-guests` runs.** Before the `te-poc` load checks, an
invocation that omitted `SCENARIO=te-poc` (the plan's command list
predates the selector; open item 44) made two `two-guests` load checks
(`build/mvp/k3-load-checks/gcc/20261027T174616Z` and
`clang/20261027T174637Z`, images `2d33d5887cc0` and `0115b6960b73`) and
three GCC `two-guests` kexec runs with `804cd24c`'s images,
`20261027T174716Z`, `174838Z`, and `175000Z`, each followed by a `k3ctl`
reset (34, 33, and 43 s). They are set aside in
`build/mvp/k3-campaigns/20261027-com260-m1b-two-guests-unplanned/`, with
no `summary.md`; the third run's `reset.txt` ends at
`seconds_to_new_boot_id=43`, without its settle and outcome lines, and
its directory has no `SHA256SUMS`, so the invocation ended during its
settle wait. All three passed with M0's exact counts, `exits_g0=157
exits_g1=157 records=138 wakes=2 alternations=125 g0=65 g1=65`. They are
an unplanned observation, not M1's evidence (open item 45).

**Claim boundary.** This is diagnostic bring-up evidence from one COM260,
its firmware (`SBI implementation ID=0x1 Version=0x10006`), and one
Fedora kernel, not hardware validation, qualification, or formal
verification. The runs show, in the tested scenario, the declared
channel carrying the writer's data to the reader and the three tested
accesses denied, logged, delivered as access faults, observed, and
survived; isolation beyond the tested accesses remains by construction
(plan, "Claim boundary and non-goals"). The service ticks and the reset
times are recorded only.

### M1-6 (2026-10-27)

M1-6 makes the board record of the second campaign with its platform record,
these results, and the checking-to-monitor size; the result packet and the
status documents are outside `mvp/`. Its change to the tree is
`tools/platform-record.py` (633 to 1,139 lines), the M1 sections the plan
asks of the platform record (see [Harness](#harness-m0-4), "M1's
additions"), `tests/run-tool-dry-run.sh`'s checks of them in three of its 40
cases (1,301 to 1,362 lines), and this README; `tools/evidence.py` is
unchanged. The board record is to be `results/20261027-com260-m1b/`, written
by `K3_RUN_ROOT=$PWD/build/mvp/k3-campaigns/20261027-com260-m1b ./mvp/mvp
board-evidence` from a clean tree at the exact M1-6 commit and committed
after it, never by hand. It holds M0's record's files for the six runs, both
`te-poc` load checks (`load-check/gcc-20261027T175222Z` and
`clang-20261027T175244Z`), and the preflight, each excerpt judged again with
te-poc's expectation and report; in its `mvp/` directory both scenarios
(te-poc's with `policy.te` and the authority report), each run's `reset.txt`
under `resets/`, which B0's retention does not keep, the policy check on
`te-poc` and its report under `policy/`, and `serial-log-note.txt`; and the
platform record, with the resets, that note as its Serial log paragraph, and
M1-6's sections.

| File | Change | Why |
| --- | --- | --- |
| `tools/platform-record.py` | The firmware identity, SBI specification, and kernel release beside M0's record, the channel page's region line, "te-poc runs", "Denials on K3", "The channel", and the other runs' FAIL and DETAIL lines; refusals for malformed M1 lines and a report that is not its expectation's | The plan's "Platform record" for M1 |
| `tests/run-tool-dry-run.sh` | The `campaign` case checks the firmware and kernel beside M0's record, the channel page's region, the payload run's FAIL line, and no te-poc section; `probe-record` the new counters; `te-poc-record` the te-poc sections and the negatives' FAIL lines | The platform record's additions, tested without a board |
| `README.md` | These results; the status, Design, Guest, Tests, Harness, Commands, budgets, copies, new files, open items, and non-claims for M1 | M1-6's record of the tree |

At exact commit `17ed82f7`, from a clean tree on `l1`, the gates passed in
this order, each through the wrapper's clean environment: `./mvp/mvp check`
(19:26:16 to 19:30:23 UTC: `BE_MVP_LOCK: PASS roles=29 host_only_skipped=0
closure=259 lock_sha256=6e99262f04a1`; the six host tests on their pinned
counts, GCC = Clang; `BE_MVP_CAPTURE_SELF_TEST: PASS cases=47 failed=0`;
`BE_MVP_CAPTURE_MUTATIONS: PASS mutations=170 rejected=170`;
`BE_MVP_RUN_TOOL_DRY_RUN: PASS`; `BE_MVP_QEMU: PASS runs=44 attempts=49
refused=5`; `BE_MVP_BUDGETS: PASS measured=22`; `BE_MVP_EVIDENCE: PASS
development … files=220 images=184 qemu_attempts=49 rehearsals=4`;
`BE_MVP_CHECK: PASS`); `./mvp/mvp evaluate` (19:31:41 to 19:36:07 UTC:
`host source=17ed82f7… tree=clean images=184`; inside the evaluator
`BE_MVP_LOCK: PASS roles=26 host_only_skipped=3 …`, `BE_MVP_QEMU: PASS
runs=44 attempts=58 refused=14`, and `BE_MVP_CHECK: PASS`;
`BE_MVP_IMAGE_IDENTITY: PASS images=184 same=184 differing=0`;
`BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`);
`./mvp/mvp kexec-rehearsal` (19:36:14 to 19:37:10 UTC: four
`BE_MVP_KEXEC_REHEARSAL: PASS smp=8 …` lines, images `2d33d5887cc0`,
`a55a5791b4b4`, `0115b6960b73`, and `e32de2439ef0`, the refused domain-hart
boots repeated within the bound); and `make -C mvp kernel-repro
LINUX_GIT=/home/jmorris/src/kernel.org/linux` (19:37:24 to 19:37:46 UTC:
`BE_MVP_KERNEL_REPRO: PASS outputs=12 identical; sysroot_files=1065
sysroot_sha256=c931b51b…`). The board record was then made from the same
clean tree (19:37:54 to 19:37:57 UTC): `BE_RETAIN: PASS runs=6
load_checks=2 files=80`; six `ok … recorded PASS, excerpt PASS` lines;
`BE_MVP_PLATFORM_RECORD: PASS … runs=6 probe_values=0 scenario_runs=0
te_poc_runs=4 denials=12 channel_checked=5 qemu_gcc,clang=0,0
resets=human:0,k3ctl:6`; `BE_MVP_EVIDENCE: PASS board … runs=6 pass=6
fail=0 refused=0 stop=0`; `python3 -B tools/evidence.py --verify
results/20261027-com260-m1b` reports `files=82`. The record's `bundle.txt`
holds `source_commit=17ed82f7217c82328bb6027c294acfd71e73826f`,
`source_tree=clean`, and `lock_check_status=0`; its `MANIFEST.sha256` has
SHA-256 `c4bd1b4900bee961a0bc475366f9c6bf3b28fcaebae101da59ce079d208571e9`.
The record is committed in the commit after `17ed82f7`, with this
paragraph.

**Checker-to-monitor size** (S1 H43; plan, "Budgets", and stop condition 13:
at most 2.2 lines of checking code per monitor line). Counted by M0-6's
method on the M1-6 content, the working tree the M1-6 commit records, each
row's files' lines summed with `wc -l`, with M1's new files of the same
kinds added: the offline checker in the checkers, `tests/deny-test.c` among
the host tests (`tests/*-test.c`, six), and the fake dongle among the
harness drivers:

| Code | MVP at the M1-6 content (`17ed82f7`) | MVP at `804cd24c` | MVP at M0-6 (`13992d6d`) |
| --- | --- | --- | --- |
| Monitor: `src/*` and `shim/mvp-shim.S` | 10,176 | 10,176 | 8,562 |
| Checkers: `tests/check-capture.py`, `tests/check-image.py`, `tools/budgets.py`, `tools/platform-record.py`, and (M1) `tools/policy-check.py` | 8,340 | 7,834 | 5,931 |
| Host tests: `tests/*-test.c` | 9,996 | 9,996 | 7,083 |
| Harness drivers and their tests: M0-6's six and (M1) `tests/fake-k3ctl.py` | 3,467 | 3,406 | 2,375 |
| Checking code | 21,803 | 21,236 | 15,389 |
| Lines of checking code per monitor line | 2.143 | 2.087 | 1.797 |

M1's increment is 1,614 monitor lines and 6,414 checking lines, 3.97 per
monitor line; the plan's inference was 600 to 700 and 2,300 to 2,700. The
monitor grew in `src/mvp-gstage.{h,c}` (492 lines), `src/mvp.h` (275),
`src/mvp-sbi.c` (235), and `src/mvp-runtime.c` (214); the checking code in
`tests/gstage-test.c` (1,125), `tools/policy-check.py` (890),
`tests/run-tool-dry-run.sh` (765), `tests/sbi-test.c` (699),
`tests/check-capture.py` (659), `tests/deny-test.c` (643), and
`tools/platform-record.py` (569). Without the offline checker and the fake
dongle, M0-6's rows alone with the six host tests, the ratio is 2.042; with
the fake dongle but not the offline checker, 2.055 (at `9020c4f8` that count
gave M1-5's 1.994, 19,968 and 10,012). The ratio stays below the plan's 2.2
(stop condition 13 does not apply) and below B7's 2.68; M1-6's two files
moved it from 2.087 to 2.143. At the M1-6 commit the same counts come from
these commands, the commit named in `c` (the first prints the monitor's
lines, the second the checking code's; on the M1-6 content they print 10176
and 21803):

```sh
c=17ed82f7
count() { for f in "$@"; do git show "$c:$f"; done | wc -l; }
count $(git ls-tree -r --name-only $c mvp/src/) mvp/shim/mvp-shim.S
count mvp/tests/check-capture.py mvp/tests/check-image.py mvp/tools/budgets.py \
	mvp/tools/platform-record.py mvp/tools/policy-check.py \
	$(git ls-tree -r --name-only $c mvp/tests/ | grep -- '-test\.c$') \
	mvp/tests/run-qemu.sh mvp/tests/kexec-rehearsal.sh \
	mvp/tests/kexec-rehearsal/init.c mvp/tests/run-tool-dry-run.sh \
	mvp/tests/fake-board.py mvp/tests/test-kexec-load.py mvp/tests/fake-k3ctl.py
```

### M2-1 and M2-2 (at `f149eea0` and `d6667862`, 2026-10-27)

M2 is implemented on the local branch `beryllium/mvp-m2`, from the M2
plan's acceptance record `35ebe8a7` (plan `854a5415`), every step on the
workstation `l1`. M2-1 and M2-2, which the plan makes independent, were
made in parallel, each from `35ebe8a7`, and committed in that order;
`3b71575d` then pinned the payload test's count for the two together, 646
assertions (622 at M1, 642 with M2-1's two DTBs, and four more for M2-2's
shared extent), and on the merged tree the host tests, `target-check`,
`image-check`, `variants`, `budgets` (30 measured), `policy-negatives`
(four), the dry run, and `lint` passed (its message). The rows `mvp check`
printed for the two commits were not kept; the counts below are the
commits' pins, files, and messages, and the records of M2-5's check of
the M2-5 content, which prints them again ([below](#m2-5-2026-10-28)).

**M2-1, the policy and the scenario** (`f149eea0`).
`scenarios/anchor/policy.te` (37 lines) holds security model v1's
Instance 3 as the plan prints it: `host_t` and `prot_t`, the request,
response, and secret pages' types, and `domain { pause terminate }` for
`host_t` on `prot_t`. `scenarios/anchor/scenario.json` (246 lines, schema
`be-mvp-scenario-v3`) holds the rest of the configuration: the labeling,
the need sets, the three pages with each domain's rights, the management
grant (`from` 0 `to` 1, `pause` and `terminate`), the public 32-byte test
secret, the measured domain (1), the roles `host` and `prot` with their
denied accesses, the declared management sequences, and the four request
messages. `scenarios/anchor/negatives/` holds the two build-time
negatives, 17 lines each: `grant-without-rule.json`, the manifest's
management grant with the policy's `domain` rule removed, and
`secret-flow.json`, `host_t` given `read map` on `secret_t` in the
policy, its need sets, and the manifest. `tools/policy-check.py` grows
from 890 to 1,098 lines (Q17's limit is
1,100): the `domain` class, the management grants in A8, A3's rule that a
`domain` rule names another domain's type, and Instance 3 in its
self-test (45 cases, 33 before) and mutations (14, 7 before).
`secret-flow` is refused by A3 alone, not by "A6 and A3" as the plan's
table says: the secret page has no writer, so it adds no pair to A6's
flows, and Instance 3 declares both directions already; the negative's
purpose text records it (open item 47). From the check of the
M2-5 content (`build/mvp/records/policy/`; `anchor-*` are anchor's
negatives):

```text
BE_MVP_POLICY_SELF_TEST: PASS cases=45
BE_MVP_POLICY_MUTATIONS: PASS mutations=14 rejected=14
BE_MVP_POLICY: PASS scenario=anchor grants=12 flows=2 checks=8 config=336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e measurement=e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b
BE_MVP_POLICY_NEGATIVE: PASS name=grant-without-rule fails=A8 source_none=1 undeclared=0
BE_MVP_POLICY_NEGATIVE: PASS name=secret-flow fails=A3 source_none=0 undeclared=0
```

The authority report (`build/mvp/gen/anchor/authority-report.json`,
SHA-256 `418797a29bf5...` at the M2-5 content) lists twelve grants, each
with its allowing rule: each domain's window, request page and channel,
and response page and channel, G0's management grant on G1, and G1's
secret page; and two declared flows, G0 to G1 through `request_page` and
G1 to G0 through `response_page`. A5 reports `req_t: static, not
revocable, single writer host_t; resp_t: static, not revocable, single
writer prot_t`, A6 `F = D = {(host_t, prot_t), (prot_t, host_t)}; F+ =
D+`, and A7 `vacuous: domains hold only pause and terminate, which make
no grant, and no delegation exists`. The configuration identity is
`336bfddc...`; the expected measurement covers the measured domain's
kernel and DTB as built, so it follows the guest: `41aec5e8...` over
1,577,940 bytes with M1's guest, and `e0c6bd23...` over 1,907,940 since
M2-4's. `tools/gen-scenario.py` (1,516 lines to 2,582) reads a v3
scenario only after the policy check passes and writes the page, secret,
measurement, grant, and accepted-exit macros into anchor's header; the
`be-mvp-expect-v3` files for `anchor` and its four runtime negatives, with
the management sequences, the requests' HMAC-SHA-256 digests, and the
measurement it computes from the Image, the protected domain's DTB, the
secret page, and the configuration identity; and the report with the
grants and the measurement. `two-guests`' and `te-poc`'s generated
outputs are byte-identical with M1's. `tools/gen-dts.py` renders anchor's
two DTBs, whose bootargs carry `be.role=`, `be.pages=`, and `be.deny=`
(its self-test 69 cases to 79, 10 DTBs to 12).

**M2-2, the pages and the measurement** (`d6667862`). M1's one-page
extent at HPA `0x118000000` grows to three pages (request, response,
secret), each root mapping its pages through M1's level-0 page behind
level-1 entry 32 with the plan's exact leaves: the host's request
`0x460000d7` and response `0x46000453` and no secret leaf; the protected
domain's request `0x46000053`, response `0x460004d7`, and secret
`0x46000853`. Hart 0 builds each root from the sealed page records,
re-walks it, and checks that each walked leaf is the declared one and
that a domain without rights has none; the `secret-shared` and
`response-writable` builders, which map the secret page into the host's
root and set W in the host's response leaf, are refused at boot, `FAIL
gstage` with the walked and declared leaves. `src/mvp-sha256.{h,c}` (87
and 249 lines) is FIPS 180-4 SHA-256, incremental and one-shot, and
HMAC-SHA-256 in restricted C, host-tested against the standard's vectors
and RFC 4231 (16 scenarios, 626 assertions). After `:05
DOMAIN_RAM_CLEARED` hart 0 clears the two channel pages and writes the
secret, and after both `PAYLOAD_PLACED` lines measures the protected
domain (its kernel and DTB as placed, the secret page, and the
configuration identity) into data only hart 0 names, compares it with the
image's expected value, and prints `:06 MEASURED`, or fails
`measurement`; `wrong-measurement` changes one bit of the expected value.
The G-stage host test went from 37 scenarios and 33,475 assertions to 44
and 39,647, and the SBI test to 14,656 assertions (the `measurement`
class name), GCC = Clang (the `Makefile`'s pins at `d6667862`); the image
checker's anchor profile rejected 104 mutations; the loader's layout rule
and the preflight's region check name
`shared-pages=0x118000000-0x118003000`. `te-poc` and `two-guests` keep
their lines. On the merged tree, with M1's guest, whose init knows
neither role and printed `RESULT fail`, the GCC anchor image ran in QEMU
from `BE_MVP:01` to `BE_MVP:14` (`build/mvp/anchor-smoke-gcc.log`, 23:01
UTC), measuring at QEMU's 10 MHz timebase:

```text
BE_MVP:03 PAGE_CHECKED page=2 kind=secret reader=1 gpa=0x84002000 hpa=0x118002000 bytes=0x1000 level0=0x102039000,0x102041000 reader_pte=0x46000853 config=336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e
BE_MVP:05 PAGE_CLEARED page=0 hpa=0x118000000 bytes=0x1000 ticks=0x1e39
BE_MVP:05 PAGE_CLEARED page=1 hpa=0x118001000 bytes=0x1000 ticks=0x9e
BE_MVP:05 SECRET_PLACED page=2 hpa=0x118002000 bytes=0x20 ticks=0x11b
BE_MVP:06 MEASURED domain=1 hart=2 bytes=1577940 sha256=41aec5e87a5c97bc486169b6f76a57a03caaa6295a4ee497ff0df9b63d009182 expected=match ticks=0x78a15
```

The measurement took `0x78a15` ticks, 49.4 ms of QEMU time (with M2-4's
guest `0x55183`, 34.9 ms; QEMU's timing is not K3's). In the M2-5 fixtures
`secret-shared` stops at `BE_MVP:DETAIL page=2 domain=0 hart=1
walked=0x46000853 declared=0x0`, `response-writable` at `page=1 domain=0
hart=1 walked=0x460004d7 declared=0x46000453`, and `wrong-measurement` at
`BE_MVP:FAIL measurement` and `DETAIL domain=1 hart=2 computed=e0c6bd23...
expected=e1c6bd23...`, before any domain hart starts.

| File | Change | Why |
| --- | --- | --- |
| `scenarios/anchor/policy.te`, `scenarios/anchor/scenario.json` (new) | Instance 3 as the plan prints it; the v3 scenario: labeling, need sets, pages, management grant, secret, measured domain, roles, management sequences, and request messages (M2-1) | The policy as specification and the configuration as data (Q12) |
| `scenarios/anchor/negatives/` (new) | `grant-without-rule.json` and `secret-flow.json` (M2-1) | The two build-time negatives (Q10) |
| `tools/policy-check.py` | The `domain` class, the management grants in A8, A3's extension, Instance 3's self-test cases and mutations; 890 to 1,098 lines (M2-1) | Q17's budget of 1,100 lines |
| `tools/gen-scenario.py` | Schema v3: the policy check first, the page, secret, measurement, grant, and accepted-exit macros, the v3 expectations with the HMAC digests and the recomputed measurement, the report with grants and measurement (M2-1) | v1 and v2 unchanged; a failing check writes nothing |
| `tools/gen-dts.py`, `guest.mk`, `guest/pins.txt` | Anchor's two DTBs with the roles' arguments, among the outputs, pinned (M2-1) | The guests learn their roles from `bootargs` |
| `Makefile` | The third scenario, generated in `$(GEN)/anchor` from the measured kernel and DTB, its four variants' names, and its two negatives in `policy-negatives`; the payload pin, 642 (M2-1); SHA-256 among the MVP's C, the `sha256` test, the G-stage and SBI pins, and the anchor images with `secret-shared`, `response-writable`, and `wrong-measurement` (M2-2); the payload pin, 646 (`3b71575d`) | The offline pipeline runs on every check; the plan's images (Q10) |
| `tools.mk` | Anchor among the board scenarios, with `wrong-measurement` and `no-grant-check` (M2-1); the preflight's comment (M2-2) | Q11's board variants, which M2-5's selector uses |
| `src/mvp-layout.h` | The shared extent's base and size, at most three pages, and the secret's 32 bytes, with their static assertions (M2-2) | Q1's layout in the constants every tool reads |
| `src/mvp-gstage.h`, `src/mvp-gstage.c` | The page records and walked leaves; the build, walk, and page check; the two builder variants (M2-2) | Each declared page in each root, re-walked and checked |
| `src/mvp-sha256.h`, `src/mvp-sha256.c` (new) | SHA-256 and HMAC-SHA-256 (M2-2) | Q6 and Q7: one implementation for the monitor and the guest |
| `src/mvp-runtime.c` | The page check and `PAGE_CHECKED`, the clear and `PAGE_CLEARED`, `SECRET_PLACED`, the measurement and `MEASURED`, their DETAIL lines (M2-2) | The boot additions ("Boot sequence additions on hart 0") |
| `src/mvp.h`, `src/mvp-sbi.c` | The `measurement` class; a grant's permission bits (M2-2) | Hart 0's failure class; the generated header names the bits |
| `src/mvp-payload.h`, `src/mvp-payload.c`, `tools/port.py` | The staged image off the shared extent; `mvp-sha256.o` in the MVP region (M2-2) | The extent is MVP-owned; the MVP layer's C stays in its region |
| `tools/kexec-load.py`, `tools/k3-preflight.sh`, `tools/platform-record.py` | The shared extent in the layout rule, the region line `shared-pages=`, and the platform record's preflight key (M2-2) | "Memory and load paths" |
| `tests/gstage-test.c`, `tests/sha256-test.c` (new), `tests/payload-test.c`, `tests/sbi-test.c`, `tests/deny-test.c`, `tests/test-kexec-load.py`, `tests/run-tool-dry-run.sh` | The pages' tests; the SHA-256 test; the shared extent in the payload and loader tests; M1's page record renamed; the dry run's region lines (M2-2) | Identical GCC and Clang output with pinned counts |
| `tests/check-image.py` | The anchor profile: the linked page records, secret, and expected measurement against the report, their sections, the shared extent, anchor's DTBs and variants; 104 mutations (M2-2) | The plan's image checks |
| `README.md` | The Design, Tests, and file-table rows for M2-2 | Documentation |

### M2-3 (at `2d23efe4`, 2026-10-28)

`2d23efe4` adds the management extension, `pause` and `terminate`, and
the page-aware denial decision, as [Design](#design) describes them: on a
domain hart an `ecall` with EID `0x08004245` from VS (FID 0 `pause`, FID 1
`terminate`, `a0` the target) posts a MGMT_REQUEST, sends hart 0 one IPI,
and waits in HS for its MGMT_RESULT with M1-B's progress-measured window,
reading its inbound ring only after an IPI and answering any PING
meanwhile; another FID is -2 on the hart, counted in `refused`. Hart 0
decides each request with `be_mvp_mgmt_decide` against the sealed grants
only it holds: -3 for no such domain, -4 without a grant, -10 for a target
terminated, shut down, or pending, or `pause` of a paused one, else
delivery by PAUSE or TERMINATE and one IPI; the target hart saves the
exit, posts PAUSED or TERMINATED, and parks, taking only a TERMINATE while
paused; hart 0 prints `:12 DOMAIN_PAUSED` or `DOMAIN_TERMINATED` (with the
measurement for the measured domain), then answers and logs the request.
A terminated domain ends for `RUN_COMPLETE`; a paused one does not. The
records are types 10 to 15 (MGMT_REQUEST, PAUSED, and TERMINATED
outbound; MGMT_RESULT, PAUSE, and TERMINATE inbound); the calls are the
SBI sub-counter `mgmt`, SHUTDOWN's word 13 (fourteen words, thirteen
before), inside `sbi=`; an image whose scenario accepts the extension
reports SBI implementation version 4 and probes it as 1, and every other
image stays at 3 and does not support the EID. The denial decision takes
every page's walked leaf, so a store to a page mapped without W is
`read-only` and a page the root does not map `unmapped`. The one assembly
change is the SSIP helper's: one `csrrci` that returns `sip` as it was,
so that a waiting hart reads its inbound ring only once an IPI has
arrived. The `no-grant-check` variant delivers every well-formed request,
the state rules kept, under a run budget of 2^27 ticks. The image checker
requires that no code the domain-hart entry or the vector reaches names
`be_mvp_measurement`, `be_mvp_mgmt_state`, or the grants, or reaches the
decision; its anchor profile rejects 111 mutations (104 before), and the
`two-guests` and `te-poc` profiles' 97 and 100 are unchanged. The host
tests at `2d23efe4` (the `Makefile`'s pins), GCC = Clang:

| Test | M1 (`35ebe8a7`) | M2-2 and the integration | `2d23efe4` |
| --- | --- | --- | --- |
| `hart` | 722, 174,246 | 722, 174,246 | 843, 176,870 |
| `sbi` | 63, 14,655 | 63, 14,656 | 130, 16,208 |
| `deny` | 30, 2,357 | 30, 2,357 | 38, 2,933 |
| `ring` | 160, 409,413 | 160, 409,413 | 160, 409,414 |
| `gstage`, `payload`, `sha256` | 37, 33,475; 8, 622; none | 44, 39,647; 8, 646; 16, 626 | as before |

A scratch bare VS guest, not committed (`build/mvp/scratch-m2-3/`),
played both roles in QEMU for both toolchains: it read version 4 and
`probe_extension` 1, made the denied accesses (each delivered as an access
fault), and received every result code: -4 for the protected domain's
calls on the host and the host's on itself, the burst among them, -3 for
`pause 2`, -2 for FID 7 with no `BE_MVP:MGMT` line, 0 for `pause 1` and
`terminate 1` with `DOMAIN_PAUSED` and `DOMAIN_TERMINATED` between, and,
in `no-grant-check`, 0 for the protected domain's `terminate 0` and -10
for its `pause 0` after it, the run ending in `FAIL run-timeout` with
`DETAIL ticks=0x80017e8` (GCC) and `0x8001cd3` (Clang), past 2^27. A
first full `./mvp/mvp qemu` on M2-3's tree failed one run,
`gcc/probe-platform`, with `FAIL ipi delivered=0`; it passed on six
isolated reruns and on the full suite's rerun (open item 50).

| File | Change | Why |
| --- | --- | --- |
| `src/mvp.h`, `src/mvp-sbi.c` | The extension's identity, results, records, `mgmt` count and class, phases `PAUSED` and `TERMINATED`, the state's `accept_mgmt`, `by`, `awaiting`, and `answer`; `sbi_mgmt`, the probe, version 4; `be_mvp_wait_serve` and the paused and terminated records in `be_mvp_ipi_serve`; `be_mvp_mgmt_decide`; `be_mvp_post_mgmt_request`; SHUTDOWN's word 13; the denial decision over every page's leaf | The extension's decision and the domain hart's side as pure, host-tested functions ("The management extension") |
| `src/mvp-hart.h`, `src/mvp-hart.c` | `be_mvp_control_pages` and `be_mvp_control_mgmt`; the control loop's MGMT, DELIVER, PAUSED, and TERMINATED steps, the pending state, and the completion rule; the DENIAL step against the sealed pages | Hart 0's control loop ("Control loop and failure paths") |
| `src/mvp-hartmain.c` | The management call's request and wait (`mgmt_call`, `wait_serve`), and the paused and terminated parks | The domain hart's synchronous call (Q14, Q15) |
| `src/mvp-runtime.c` | Each block's page leaves and `accept_mgmt`; the sealed grants and management state; the answers, deliveries, `BE_MVP:MGMT` and `:12` lines | Hart 0's decision, delivery, and log |
| `src/mvp-platform.h`, `src/mvp-trap.S`, `src/mvp-probe.c` | `BE_MVP_RUN_ACCEPT_MGMT`, the hart page's leaves; the SSIP helper's `csrrci` and its readback; the probe discarding it | The waiting hart reads its ring only after an IPI |
| `tests/sbi-test.c`, `tests/hart-test.c`, `tests/deny-test.c`, `tests/ring-test.c` | The decision, calls, waits, records, and transitions; the control loop's management steps; anchor's roots with three pages; the records' numbering and masks | The counts above |
| `tests/check-image.py` | The reach rule, the linked grants against the report, no channel record with pages, the SSIP helper's read of `sip`, `no-grant-check`; 111 anchor mutations | The plan's image-checker rule ("The measurement") |
| `Makefile` | The host tests' pins and sources; `no-grant-check` among anchor's images | The counts above; Q10 |
| `README.md` | The Design rows (records, SBI core, denial path, management extension), the Tests rows, and the file table | Documentation |

### M2-4 and its follow-up (at `51893419` and `f687b791`, 2026-10-28)

M2-4 was made in parallel with M2-3 and committed after it. **The
module** (`guest/mgmt/be-mgmt.c`, 102 lines, with its `Kbuild`): a misc
character device, `/dev/be-mgmt` at minor 243 (the first of the minors
reserved for local use), whose one ioctl, `_IOWR('B', 0x42, struct
be_mgmt_call)` = `0xc0184242`, makes one call of the extension through the
kernel's exported `__sbi_ecall` (`sbi_ecall`) and returns `a0`. It is the
repository's one `GPL-2.0-only` file (Q20, answered `gpl 2.0 only ok`),
with `MODULE_LICENSE("GPL")`, because it is linked into the GPL-2.0-only
guest kernel. The module and the init each define the call's ABI, the
structure and the ioctl, and assert its number, rather than share a
header, so that the one GPL-2.0-only file stands alone (open item 48).
`tools/build-guest.sh` builds it out of tree against the pinned `v7.2`
(Kbuild's `M=`, `MO=`) under the same reproducibility variables, building
the kernel twice around it (vmlinux and its exports first, then the Image
whose initramfs holds the module, `/be-mgmt.ko`), and `kernel-repro`
compares 15 outputs, identical (the commit's message). **The kernel**:
`guest/mvp-kernel.config` gains `CONFIG_MODULES=y`, and the delta check
requires the final `.config` to differ from M1's in exactly the sixteen
lines its comment lists (see [Guest](#guest);
`build/mvp/guest/config-delta-m2.txt`). The Image grows from 1,569,716
bytes to 1,899,716 (`image_size` `0x1b3628` to `0x203fb0`), 330,000
bytes, where the plan inferred tens of KiB (open item 49). **The init**:
the roles `host` and `prot` with `be.pages=` (`guest/mvp-guest-id.h`,
its test 74 cases to 103), the module loaded with `finit_module`, the
pages through `/dev/mem`, M1-A's child for the denied accesses, the four
requests and their HMAC-SHA-256 answers keyed by the secret page, with
`src/mvp-sha256.c` compiled in (`guest/be/types.h` gives it the scalar
types without the monitor's headers), and the management calls through the
ioctl (see [Guest](#guest)). The guests print `be_mgmt: loading
out-of-tree module taints kernel.`, which M2-5's expectations take as an
expected kernel line (open item 52). New pins: init `467f6a96...` (11,360
bytes), module `67529a9d...` (5,736), Image `8b675c00...` (1,899,716);
`guest-pins.py`'s self-test 45 cases to 60. M0's and M1's roles are
unchanged, and the QEMU suite of 44 runs passed with this guest; in QEMU,
before M2-3 was merged, the four digests equalled the generator's and
every call answered -2 (the message).

**The follow-up** (`f687b791`). Q8's bound, "2,000 polls at 1 ms",
meant about two seconds, but the pinned kernel (`CONFIG_HZ=250`, no
high-resolution timers) rounds a 1 ms sleep up to a jiffy (the commit's
message), so the fifth request's bound took 20 s in QEMU and the run 233M
ticks, past the 2^27 that `no-grant-check`'s budget separates from a
hang. The host's poll is now a deadline of one second of
`CLOCK_MONOTONIC` with polls 1 ms apart (open item 51). New pins: init
`dca88d18...` (11,408 bytes), Image `c7ae03e6...` (1,899,716); the
module and the DTBs are unchanged.
`build/mvp/guest/pins-check.txt` (the M2-5 content's guest build) reads
`BE_MVP_GUEST_PINS: PASS files=15 image_bytes=1899716 image_size=0x203fb0
text_offset=0x200000 init_bytes=11408 module_bytes=5736 dtb_bytes=4096`.

**The first whole anchor run** (the orchestrating session, on
`f687b791`'s GCC images, before M2-5's harness judged any;
`build/mvp/anchor-e2e-gcc.log`). In QEMU on the `k3-like` machine, boot
hart 3 by the start rule, both guests loaded the module and mapped their
pages, the host two and the protected domain three, and every line the
plan's Markers name appeared, each delivered request's `BE_MVP:MGMT` line
after its target's transition (open item 54):

```text
BE_MVP:06 MEASURED domain=1 hart=2 bytes=1907940 sha256=e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b expected=match ticks=0x55183
BE_MVP:12 DOMAIN_PAUSED hart=2 domain=1 by=0 exits=124 ticks=0x25870c
BE_MVP:MGMT hart=1 domain=0 seq=12 fid=pause target=1 result=0 target_state=paused ticks=0x258172 service=0x1612
BE_MVP_G0: MVPINIT 09 REQUEST n=5 timeout=1
BE_MVP:12 DOMAIN_TERMINATED hart=2 domain=1 by=0 exits=124 sha256=e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b ticks=0x1946a96
BE_MVP:MGMT hart=1 domain=0 seq=13 fid=terminate target=1 result=0 target_state=terminated ticks=0x1945e7a service=0x1d3d
BE_MVP_G0: MVPINIT 05 RESULT pass
BE_MVP:12 DOMAIN_SHUTDOWN hart=1 domain=0 exits=239 sbi=234 ipi=1 base=14 time=0 dbcn_write=137 dbcn_read=68 dbcn_byte=0 srst=1 refused=1 lines=83 ring_peak=0x250 entered=0x3df9 ticks=0x3e8bb95
BE_MVP:13 RUN_COMPLETE domains=2 records=174 wakes=109 idle_ticks=0x3e103af overlap_ticks=0x1942c9d ticks=0x3e8cfb1
```

The four requests' digests on each side were equal, five DENY lines
matched the guests' reports (the protected domain's store to the request
page and the host's to the response page, `read-only`; the host's loads
of the secret page, of `0x114000000`, and of `0x102064000`, `unmapped`),
and hart 0 printed fifteen `BE_MVP:MGMT` lines, two for the protected
domain's calls and thirteen for the host's (FID 7 answered -2 on its
hart, with no line). The host's exits are `239 = 234 + 1 + 4` (`sbi` with
13 `mgmt` calls, the IPI, the denials), the protected domain's 124 when it
paused and when it was terminated, and the run took `0x3e8cfb1` ticks,
65.6M, under 2^27. The `unchanged=1` of each store's report proves little
here: both stores write zero to a word that holds zero (open item 53).

| File | Change | Why |
| --- | --- | --- |
| `guest/mgmt/be-mgmt.c`, `guest/mgmt/Kbuild` (new) | The module, `GPL-2.0-only`, and its Kbuild file (M2-4) | Q2 and Q20: the guest's SBI call into the extension |
| `guest/be/types.h` (new) | The three scalar types for the init's SHA-256 (M2-4) | `src/mvp-sha256.c` compiled against nolibc |
| `guest/mvp-init.c` | The `host` and `prot` roles, the module, the pages, the requests and HMAC answers, the calls and the burst (M2-4); the request's one-second monotonic deadline (`f687b791`) | The plan's guest programs (Q8, Q9) |
| `guest/mvp-guest-id.h`, `guest/mvp-guest-id-test.c` | The roles, `be.pages=`, four denied accesses, and their test, 103 cases (M2-4) | One parser shared by the init and its test |
| `guest/mvp-kernel.config`, `tools/build-guest.sh` | `CONFIG_MODULES=y` and its sixteen-line delta; the module's out-of-tree build, the two-step delta check, the initramfs with the module, and the init with the SHA-256 (M2-4) | Q16 and stop condition 5 |
| `guest/initramfs.list.in`, `guest.mk` | `/be-mgmt.ko` and `/dev/be-mgmt`; the module among the outputs and its sources among the inputs (M2-4) | The init loads and opens the module |
| `tools/guest-pins.py`, `guest/pins.txt` | The module's pin and checks (an unsigned RISC-V `ET_REL` object with the module's `.modinfo` and the kernel's `vermagic`); the init's, module's, and Image's pins (M2-4, `f687b791`) | The rebuilt guest outputs |

### M2-5 (2026-10-28)

M2-5 is the harness for `anchor` (M2 plan, the M2-5 row; "Scenarios and
the harness", "Markers", "Platform record", "Tests and evidence"): the
capture checker's schema v3, `anchor`'s fixtures from real QEMU runs, its
runs in the QEMU suite and the kexec rehearsal, the board tools'
`SCENARIO=anchor` with its two board negatives and their dry run, the
evidence bundle and board record, and the platform record's M2 sections
(see [Harness](#harness-m0-4) for each). It changes no byte under `src/`
or `guest/` and not `tools/policy-check.py`, and touches no board. Its
results below are from the working tree over `f687b791` on `l1`, before
it was committed (`source_tree=dirty changed=19`); nothing in it is
reviewed.

| File | Change | Why |
| --- | --- | --- |
| `tests/check-capture.py` | Schema v3 (`be-mvp-expect-v3`) beside v1 and v2, M1's rules unchanged: the pages' lines, the measurement recomputed from `--kernel` and `--dtb`, the requests' HMAC-SHA-256, the `BE_MVP:MGMT` lines against the guests' `MVPINIT 10 MGMT` lines and the expectation's `mgmt`, the transitions, the order, `sbi_terms` and `sbi_derived`, exact `refused`, and the negatives' outcomes, `no-grant-check`'s prefix and run-timeout among them; M1's fixtures judged against M1's pins; 18 new self-test cases (47 to 65) and 54 new mutations (170 to 224); `--write-fixtures` writes the anchor kexec captures; 2,605 to 3,582 lines | The plan's M2-5 row; M2-4's kernel and pins changed under M1's fixtures |
| `tests/fixtures/` | `qemu-anchor-gcc.log`, `qemu-secret-shared-gcc.log`, `qemu-response-writable-gcc.log`, `qemu-wrong-measurement-gcc.log`, and `qemu-no-grant-check-gcc.log`, from `tests/run-qemu.sh` runs with CRs removed; `m1-guest-pins.txt` (`git show ff84533c:mvp/guest/pins.txt`) | The checker's v3 rules on real captures; M1's fixtures' pins |
| `tools/gen-scenario.py` | In v3 expectations the host's `DOMAIN_SHUTDOWN` expression takes its exact `refused` (1, FID 7) where it fixed `refused=0`, and each domain's kernel lines hold `be_mgmt: loading out-of-tree module taints kernel.` after `UNAME`; its anchor self-test 53 to 54 cases | Expectation defects M2-3 and M2-4 found; `te-poc`'s and `two-guests`' outputs and anchor's header and report are byte-identical to copies made first (`cmp`) |
| `tests/run-qemu.sh` | `anchor` on `k3-like`, `rva23`, and `plic` and its four runtime negatives on `k3-like`, both toolchains, each judged with anchor's report and the measured inputs; 37 lines | 58 runs |
| `tests/kexec-rehearsal.sh` | The measured inputs after the report, passed to the checker | `anchor` in the rehearsal |
| `tests/test-kexec-load.py` | The purgatory search covers the shim page and the flat image, before the guest payload at `BOOT_KERNEL_OFFSET` | The guest's initramfs holds `be-mgmt.ko`, a RISC-V `ET_REL` object the search took for a purgatory, so `kexec-loader-check` failed once the board images held M2-4's guest, which every board image carries (open item 56) |
| `tools.mk` | `SCENARIO=anchor` maps to anchor's images and `VARIANT=wrong-measurement` or `no-grant-check` to its variants' images and expectations, with anchor's report (`K3_REPORT`) and the measured DTB (`K3_MEASURED_DTB`); anchor's board images; anchor's expectations, report, and measured inputs for `capture-check`, `run-tool-check`, `qemu-test`, `kexec-rehearsal`, and the board targets; the default campaign root names a scenario other than `two-guests` | The board selector mapped `anchor` to `two-guests`' images until now (M2-1) |
| `tools/k3-run.sh` | A v3 expectation needs its report and `K3_KERNEL` and `K3_MEASURED_DTB` (new), which `run.txt` records (`measured=`) and the checker reads | Anchor's board runs |
| `tools/k3-campaign.sh`, `mvp` | Their comments and help for `SCENARIO=anchor` and its variants | The same |
| `tools/evidence.py` | Anchor's images and `be-mgmt.ko` in the identity set (234 to 247 entries), its scenario, report, and policy records in the bundle, the anchor rehearsals; in the board record anchor's policy check and report, each anchor run's measured inputs, and its excerpts judged again with them; three new self-test cases (25 to 28) | The evidence for anchor |
| `tools/platform-record.py` | M2's sections and keys (`anchor`, `m2`; schema still v2), the `BE_MVP_PLATFORM_RECORD_M2` line; 1,141 to 1,492 lines | The plan's "Platform record" for M2 |
| `tests/run-tool-dry-run.sh` | Five anchor cases (`anchor-selector`, `load-check-anchor`, `anchor-report`, `anchor-campaign`, `anchor-record`) and the anchor fake-board captures; every earlier case unchanged; 1,364 to 1,555 lines | The board tools for anchor without a board |
| `README.md` | This section; the Harness, Tests, Commands, and file table rows that M2-3 to M2-5 changed | M2-5's record of the tree |

The fixtures' table rows are in [Harness](#harness-m0-4); each new capture
gives its declared verdict (the four negatives `PASS` as declared, their
failures being the declared ones), M0's twelve and M1's five keep theirs,
the two stop-6 captures rejected for their recorded findings alone. The
checker's v3 rules, one line each:

1. `PAGE_CHECKED` per page against the report's (kind, ends, GPA, HPA,
   size, both leaves, the configuration identity).
2. `PAGE_CLEARED` per channel page and `SECRET_PLACED` for the secret
   page, in place.
3. The measurement recomputed (SHA-256 over the kernel, the measured
   DTB, the secret page, and the configuration identity) equal to
   `MEASURED`'s `sha256=` and `bytes=`.
4. `DOMAIN_TERMINATED`'s `sha256=` equal to it.
5. Each `REQUEST` and `RESPONSE` digest the checker's HMAC-SHA-256 of
   its request.
6. The requester's and the server's digests equal per request.
7. The unanswered request only on the requester's side, `timeout=1`,
   after the report of its `pause` call (`unanswered_after_seq`).
8. Every `BE_MVP:MGMT` line one of its domain's calls, in order, the
   burst line standing for eight; `seq`, `fid`, `target`, `result`, and
   `target_state` the expectation's.
9. Each `MGMT` line before its call's report and inside its domain's
   run; a delivered one after its target's transition, which names the
   requester.
10. FID 7 answered -2 on its hart, with no line on hart 0.
11. `DOMAIN_TERMINATED`'s `exits=` equal to `DOMAIN_PAUSED`'s.
12. The order `DOMAIN_PAUSED`, `DOMAIN_TERMINATED`, the host's
    `DOMAIN_SHUTDOWN`, `RUN_COMPLETE`, each once; no guest line after its
    domain's end.
13. `sbi` the printed terms plus `mgmt`, `mgmt` exact (`sbi_derived`).
14. `refused` exact.
15. Every request a drained record (`records`); the terminated domain's
    end its `DOMAIN_TERMINATED` in the overlap.
16. The report's management grants exactly Instance 3's.
17. The negatives' outcomes: `FAIL gstage` with the exact `DETAIL
    page=…`; `FAIL measurement` with `computed=` the checker's value and
    `expected=` the variant's.
18. `no-grant-check`: its required lines before the FAIL, `FAIL
    run-timeout` with `ticks=` at least 2^27, the host a prefix of its
    own lines, denials, and requests, the server answering a first run.
19. The module's taint line an expected kernel line; M1's rejected
    substrings.

The gates, each through the wrapper's clean environment on `l1`, on
the final working tree: `./mvp/mvp kexec-rehearsal` (01:26:44 to
01:27:56 UTC: six `BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1
refused=0 …` lines, GCC's `two-guests`, `te-poc`, and `anchor` images
`80ac8e334151`, `4f4d684b8689`, and `3b554f2cd0c6` from harts 3, 7, and
0, and Clang's `153e7482d2b0`, `746585fbecb8`, and `37cdfd7064b0` from
harts 5, 0, and 4; the images have not changed since); `./mvp/mvp qemu`
(01:46:18 to 01:48:57 UTC: `BE_MVP_QEMU: PASS runs=58 attempts=71
refused=13`); `./mvp/mvp check` (01:49:07 to 01:55:04 UTC: `BE_MVP_LOCK:
PASS roles=29 host_only_skipped=0 closure=259 lock_sha256=6e99262f04a1`;
the seven host tests on their pinned counts, GCC = Clang;
`BE_MVP_CAPTURE_SELF_TEST: PASS cases=65 failed=0`;
`BE_MVP_CAPTURE_MUTATIONS: PASS mutations=224 rejected=224 seed=0x4d30`;
`kexec-load self-test: 16/16 PASS images=22`;
`BE_MVP_EVIDENCE_SELF_TEST: PASS cases=28/28`;
`BE_MVP_RUN_TOOL_DRY_RUN: PASS`, 45 cases; `BE_MVP_QEMU: PASS runs=58
attempts=89 refused=31`; `BE_MVP_BUDGETS: PASS measured=32`;
`BE_MVP_EVIDENCE: PASS development … files=359 images=247
qemu_attempts=89 rehearsals=6`; `BE_MVP_CHECK: PASS`); and `./mvp/mvp
evaluate` (01:55:15 to 02:01:01 UTC: `host source=f687b791…
tree=dirty changed=19 images=247`; inside the evaluator `BE_MVP_LOCK:
PASS roles=26 host_only_skipped=3 …`, the dry run with `tree-state`
skipped on the read-only source, `BE_MVP_QEMU: PASS runs=58 attempts=69
refused=11`, and `BE_MVP_CHECK: PASS`; `BE_MVP_IMAGE_IDENTITY: PASS
images=247 same=247 differing=0`;
`BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`).
An evaluation before the last two comment changes (in `tools.mk` and
`tools/k3-run.sh`; 01:37:07 to 01:43:46 UTC) built the guest again from
the mirror inside the evaluator with its pins matched
(`BE_MVP_GUEST_BUILD: PASS kernel=built pins=match`) and gave the same
identity line (`attempts=66 refused=8`). Every refused attempt in these
runs was a boot on domain hart 1 or 2, repeated within the bound (at most
four attempts for a run). `no-grant-check` ran to its 2^27-tick budget in
each run, `DETAIL ticks=0x8000304` in the fixture's.

**Checker-to-monitor size** (S1 H43; plan, Q17, "Budgets", and stop
condition 13: at most 2.3 lines of checking code per monitor line).
Counted by M1-6's method on the M2-5 working tree, each row's files'
lines summed with `wc -l`, with no new kind of file:

| Code | MVP at M2-5 (working tree over `f687b791`) | MVP at M2-4 (`f687b791`) | MVP at the M1-6 content (`17ed82f7`) |
| --- | --- | --- | --- |
| Monitor: `src/*` and `shim/mvp-shim.S` | 12,817 | 12,817 | 10,176 |
| Checkers: `tests/check-capture.py`, `tests/check-image.py`, `tools/budgets.py`, `tools/platform-record.py`, and `tools/policy-check.py` | 10,388 | 9,060 | 8,340 |
| Host tests: `tests/*-test.c` (seven) | 12,568 | 12,568 | 9,996 |
| Harness drivers and their tests: M0-6's six and `tests/fake-k3ctl.py` | 3,724 | 3,478 | 3,467 |
| Checking code | 26,680 | 25,106 | 21,803 |
| Lines of checking code per monitor line | 2.082 | 1.959 | 2.143 |

M2-5 adds 1,574 checking lines and no monitor line:
`tests/check-capture.py` 977, `tools/platform-record.py` 351,
`tests/run-tool-dry-run.sh` 191, `tests/run-qemu.sh` 37,
`tests/kexec-rehearsal.sh` 12, and `tests/test-kexec-load.py` 6. M2's
increment over the M1-6 content is 2,641 monitor lines and 4,877 checking
lines, 1.85 per monitor line. The ratio stays below the plan's 2.3 (stop
condition 13 does not apply; 2,799 lines to spare). On the working tree,
the first command prints the monitor's lines, the second the checking
code's (12817 and 26680):

```sh
count() { cat -- "$@" | wc -l; }
count mvp/src/* mvp/shim/mvp-shim.S
count mvp/tests/check-capture.py mvp/tests/check-image.py mvp/tools/budgets.py \
	mvp/tools/platform-record.py mvp/tools/policy-check.py mvp/tests/*-test.c \
	mvp/tests/run-qemu.sh mvp/tests/kexec-rehearsal.sh \
	mvp/tests/kexec-rehearsal/init.c mvp/tests/run-tool-dry-run.sh \
	mvp/tests/fake-board.py mvp/tests/test-kexec-load.py mvp/tests/fake-k3ctl.py
```

### M2-6's first board campaign and its stop (stop condition 6, Plan revision M2-A)

On the responsible human's confirmation that the shared K3 was free
(`conform k3 is free, proceed`, read as `confirm …`, 02:30 UTC on
2026-10-28, the evening of 2026-10-27 for the human), the first campaign
ran on the COM260 (K3) with the images of the M2-5 content, which Plan
revision M2-A later left byte-identical, and the Fedora host kernel
`7.3.0-65.1.riscv64.omni.fc45.riscv64`, through RAM-only `kexec_load`
from Fedora, with the pinned `k3ctl` client for the resets; automation
never typed at U-Boot. Before it, `k3ctl status`, run by hand, read `OK
status rst=0 fcrec=0 pwr=0 k3=n/a … ver=1.0`; Fedora had been up for
8 hours, and the operator's picocom session was logging to its file.

- **The preflight** (`build/mvp/k3-preflight/preflight.txt`,
  `captured_utc=2026-10-28T02:31:25Z`) passed, printing
  `BE_MVP_PREFLIGHT: PASS hart0_dt=h:yes,sstc:yes … dt_sstc_harts=8/8
  timebase_frequency=24000000 hsm_detected=1 kexec_load=available
  tmp_fstype=tmpfs region_check=PASS firmware=ID=0x1,Version=0x10006
  k3ctl_client=matches-pin`: every MVP extent free against 20 System RAM
  children and 11 FDT reservations (`region-check.txt`), with the shared
  pages' line in place of M1's channel page's, `region
  shared-pages=0x118000000-0x118003000 result=free`.
- **The load checks** (`build/mvp/k3-load-checks/gcc/20261028T023207Z`
  and `clang/20261028T023241Z`) staged the GCC and Clang `anchor` images
  (`remote_image_sha256=3b554f2cd0c6…` and `37cdfd7064b0…`), each checked
  with anchor's expectation as M2-5 wrote it (`6b2e9a6b4a85…`), its
  report, and the measured inputs; loaded them at L (`loader=kexec_load
  entry=0x108000000 fdt=0x108400000 image_memsz=0x277000
  fdt_bytes=49280`); and unloaded them (`unload=ok kexec_loaded=0`,
  `outcome=load-only`).

The run (UTC; `build/mvp/k3-campaigns/20261028-com260-m2-stopped/`, the
campaign directory set aside under that name after the stop, whose
`summary.md` still names it `…-com260-m2` and reads `Boot marker
reproduced: 0/1 runs`, its check having failed):

| Run | Image | Boot ID before | kexec requested | Terminal marker | Result | Reset |
| --- | --- | --- | --- | --- | --- | --- |
| `20261028T023339Z` | GCC `anchor` (`3b554f2cd0c6`) | `899a90c8-8c98-4e12-8c26-9f04414238d9` | 02:33:41 | 02:33:54, `BE_MVP:14 SHUTDOWN type=0 reason=0` | FAIL: one finding, hart 2's probe line (stop condition 6) | none: `reset_outcome=no-reset-verdict` |

Linux handed over from hart 0, `BE_MVP:02` printed `started=none`, and
the run printed every line the plan's Markers name (`serial.log`):
`MEASURED … bytes=1907940 sha256=e0c6bd23… expected=match ticks=0xc2a5a`;
five DENY lines, hart 1's `seq=1 kind=read-only gpa=0x84001ff8`, `seq=2
kind=unmapped gpa=0x84002000`, `seq=3 kind=unmapped gpa=0x114000000`, and
`seq=4 kind=unmapped gpa=0x102064000`, and hart 2's `seq=1
kind=read-only gpa=0x84000ff8`; fifteen `BE_MVP:MGMT` lines, the
protected domain's two (`hart=2 domain=1 seq=1 fid=terminate target=0
result=-4 target_state=- ticks=0xa5f3d service=0x149e641` and `seq=2
fid=pause target=0 result=-4`) and the host's thirteen, the twelfth
`fid=pause target=1 result=0 target_state=paused` and the thirteenth
`fid=terminate target=1 result=0 target_state=terminated`; `DOMAIN_PAUSED
hart=2 domain=1 by=0 exits=132`; `DOMAIN_TERMINATED hart=2 domain=1 by=0
exits=132 sha256=e0c6bd23…`; the host's `DOMAIN_SHUTDOWN hart=1 domain=0
exits=248 sbi=243 ipi=1 base=14 time=0 dbcn_write=137 dbcn_read=77
dbcn_byte=0 srst=1 refused=1 lines=83 ring_peak=0x1728`; and
`RUN_COMPLETE domains=2 records=174 wakes=16 idle_ticks=0x3aced6c
overlap_ticks=0x33a5935 ticks=0x59b564e`. The checker counted
`exits_g0=248 exits_g1=132 denials_g0=4 denials_g1=1 mgmt_g0=13
mgmt_g1=2 records=174 wakes=16 alternations=122 g0=83 g1=62` and made one
finding (`check.txt`):

```text
finding: line 343: 'BE_MVP:11 IPI_PROBE hart=2 domain=1 sent=0x23598b received=0x2359c1 answered=0x2359c1 spv=0' is not 'BE_MVP:11 IPI_PROBE hart=2 domain=1 sent=<T> received=<T> answered=<T> spv=1'
BE_MVP_RESULT: FAIL terminal=shutdown-requested
```

Hart 1's probe read `sent=0x1ce576 received=0x1ce5c7 answered=0x1ce5d1
spv=1`. The tool withheld the reset and ended the campaign
(`BE_MVP_K3_CAMPAIGN: STOP run 1/3 exited 1`).

**The cause** (Plan revision M2-A, "The cause"). Hart 0 sends a domain's
PING when it takes that domain's first console line from its ring (M0's
Q4). On the board hart 0 sent hart 2's PING 96.5 ms after the barrier
(`sent=0x23598b`), its own post-barrier lines having taken about the
first 80 ms of the 115200-baud console (domain 0's PING went out at
78.9 ms, `sent=0x1ce576`). The protected guest had made its first
management call, `terminate 0`, which its init makes early to show that
it is refused, at 28.3 ms (`ticks=0xa5f3d`), and its hart was waiting in
HS for hart 0's answer: a 901 ms wait (`service=0x149e641`) that ended
929 ms after the barrier, hart 0 draining both guests' boot lines ahead
of the request record. The PING arrived in that wait, `received=0x2359c1`
lying in `[0xa5f3d, 0xa5f3d + 0x149e641]`, both since the barrier;
`be_mvp_wait_serve` took it and answered a PONG with SPV 0, as its
contract and Q14's "serving any `PING` it finds meanwhile" say, and
hart 0 printed it. In QEMU, whose console is immediate, the PING went out
12.3 ms after the barrier and the first call came at 198 ms
(`build/mvp/anchor-e2e-gcc.log`), so all 58 runs of M2-5's suite showed
`spv=1`, the shape M0's expectation encodes and M2-5 carried forward
unchanged. The monitor behaved as the plan specifies, the expectation was
the defect, and the outcome, which QEMU did not show, is stop
condition 6. That an IPI reaches a domain hart at V=1 is still shown: in
the same run by hart 1's probe (`spv=1`) and by hart 2's `PAUSE`, taken
as an exit from V=1 (`DOMAIN_PAUSED … exits=132`), and on the board by
M0's probe images (IPIs 100 of 100 at V=1).

**The direction.** Offered a harness rule that admits the outcome where
the plan already describes it (A), a monitor change that moves the PING to
the domain's ENTERED record (B), and packaging the stopped campaign (C),
the responsible human chose A with the board's reset (the form answer
`remedy=A, reset_board=true`). A `k3ctl reset` was made by hand at
02:44:32 UTC (`OK reset`; the client the tool uses, the `K3CTL` path the
preflight had checked against the pin), and Fedora was back by 02:48
with boot ID
`0fcd10c9…`, the second campaign's first "before". Plan revision M2-A is
appended to the M2 plan at `adc989fa`: first committed as `b796a8dc`, and
amended before any commit followed it to correct the wait's figure from
"a 929 ms wait" to "a 901 ms wait that ended 929 ms after the barrier"
(`service=0x149e641` is 900.8 ms at 24 MHz). It changes no monitor
source and no image, so the load checks stand; the campaign restarts in a
new directory; and the stopped run stays the record of the stop, cited by
M2's result packet and not M2's board evidence (M2-A.2).

**M2-A as implemented** (`ac0d48dd`, by a `claude-opus-5.5` coding agent
under the repository's model split). The capture checker's new rule,
`ping_findings` (see [Harness](#harness-m0-4)), accepts `spv=0` on a
`BE_MVP:11 IPI_PROBE` line only where the image has the management
extension and the probe's `received=` lies in a management wait of its
own hart, `[ticks, ticks + service]` of a `BE_MVP:MGMT` line naming that
hart, and records a probe so served among the costs
(`g<d>_ping_in_mgmt_wait=1`, `g<d>_ping_mgmt_seq`). The generator writes
`spv=<S>` on the probe line of the images with the extension, `anchor`
and its runtime variants (open item 61). The stopped capture,
`20261028T023339Z/serial.log` with CRs removed (397 lines, as the two
earlier board fixtures were made), is the fixture
`tests/fixtures/k3-anchor-gcc-m2a-ping-in-wait.log`, which `--self-test`
must judge PASS. The counts: self-test cases 65 to 70 (the board
capture; the PING at its wait's first and at its last tick; the smallest
edit, the protected domain's PONG `spv=0` before its first request; and
the board capture's costs and counts); mutations 224 to 229 (named 128
to 133: M0's 82 to 83, te-poc's 16, and anchor's 30 to 34; seeded 96, as
before); the rules' smallest edits 10 to 11; mutation bases 12 to 13
(`k3anchor`, the board capture as the board recorded it); fixtures 22 to
23; and `--write-fixtures` captures 12 to 13 (`anchor-k3`, the board
capture with CRLF). The platform record gains "The IPI probe in a
management wait" and `pings_in_wait=N` on its M2 line, and the dry run's
GCC `anchor` run is the board capture, made with the same image
(`3b554f2c…`).

On the working tree over `b796a8dc`, before `ac0d48dd` was committed
(`source_tree=dirty changed=6`), the gates passed on `l1`: `mvp check`
(its bundle `build/mvp/evidence/check`, written at 03:22 UTC:
`BE_MVP_CAPTURE_SELF_TEST: PASS cases=70 failed=0`,
`BE_MVP_CAPTURE_MUTATIONS: PASS mutations=229 rejected=229 seed=0x4d30`,
`BE_MVP_RUN_TOOL_DRY_RUN: PASS`, `BE_MVP_QEMU: PASS runs=58 attempts=69
refused=11`, `BE_MVP_BUDGETS: PASS measured=32`, and `BE_MVP_CHECK:
PASS`); the kexec rehearsal (six `BE_MVP_KEXEC_REHEARSAL: PASS smp=8 …`
lines, images `80ac8e334151`, `4f4d684b8689`, `3b554f2cd0c6`,
`153e7482d2b0`, `746585fbecb8`, and `37cdfd7064b0`, one refused
domain-hart boot repeated); and `mvp evaluate` (record
`build/mvp-evaluator/record/20261028T032304Z`: host `source=b796a8dc…
tree=dirty changed=6 images=247`; inside the evaluator
`BE_MVP_CAPTURE_SELF_TEST: PASS cases=70`, `BE_MVP_QEMU: PASS runs=58
attempts=78 refused=20`, and `BE_MVP_CHECK: PASS`;
`BE_MVP_IMAGE_IDENTITY: PASS images=247 same=247 differing=0`;
`BE_MVP_EVALUATE: PASS
image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`). The
stopped capture, checked again with `tools/k3-run.sh`'s arguments, gave
`BE_MVP_RESULT: PASS terminal=shutdown-requested` with
`g1_ping_in_mgmt_wait=1 g1_ping_mgmt_seq=1` among its costs. Every
`be-mvp.bin` and all 196 image files under
`build/mvp/{gcc,clang,variants}` were byte-identical before and after,
and of the 32 generated scenario files only anchor's five expectation
files changed (`anchor.json` `6b2e9a6b4a85…` to `97e8b2aca656…`);
`two-guests`' and `te-poc`'s outputs and anchor's header and report are
byte-identical. The README commit `e021e7ec` followed.

| File | Change | Why |
| --- | --- | --- |
| `tests/check-capture.py` | The rule `ping_findings`: `spv=1`, M0's rule, or, for an image with the management extension (a v3 expectation's `mgmt`), `spv=0` with `received=` inside `[ticks, ticks + service]` of a `BE_MVP:MGMT` line of the same hart; its two findings (the image has no management extension; `received=` lies in no management wait of the hart); the costs' `g<d>_ping_in_mgmt_wait=1` and `g<d>_ping_mgmt_seq`; the board fixture's registration (`BOARD_PING_WAIT`, judged as the board recorded it, with its wait, costs, and counts pinned); five self-test cases, five mutations, and the mutation base `k3anchor`; `--write-fixtures`' `anchor-k3` capture; 3,582 to 3,754 lines | Plan revision M2-A.1 and M2-A.2 |
| `tests/fixtures/k3-anchor-gcc-m2a-ping-in-wait.log` (new) | The stopped run's `serial.log`, CRs removed, 397 lines | M2-A.2: a passing `anchor` capture under M2-A.1, and the base of three mutations |
| `tools/gen-scenario.py` | `spv=<S>` on the `BE_MVP:11` line of the images with the extension, under the line's own placeholder map, in which `<S>` is `[01]`; elsewhere `<S>` keeps its meaning, `image_size` on the `:04` and `:06` lines; one more anchor self-test check (54 to 55); 2,594 to 2,623 lines | M2-A.1: the expectation carries `spv=<S>`, which the checker resolves; `two-guests`' and `te-poc`'s expectations byte-identical |
| `tools/platform-record.py` | "The IPI probe in a management wait": each `anchor` run's probe lines beside the checker's costs, with the `BE_MVP:MGMT` line whose wait holds a probe so served, in a per-probe table, and an Observed or Not observed sentence; `pings_in_wait=N` on the `BE_MVP_PLATFORM_RECORD_M2` line; the keys `ipi_runs` and `ipi_probes`; 1,492 to 1,585 lines | M2-A.2: the platform record notes the observation with the run's figures |
| `tests/run-tool-dry-run.sh` | `anchor-campaign`'s GCC `anchor` run on the board capture, checked for the costs; `anchor-record` checks the subsection, its sentence (`96.531 ms`, `28.323..929.168 ms`), and `pings_in_wait=1`; 1,555 to 1,573 lines | The platform record's addition, tested without a board |

### M2-6's second board campaign (2026-10-28)

With the same images (Plan revision M2-A changed none), under M2-A's
checker (`ac0d48dd`), on the same COM260 and Fedora kernel, through the
same RAM-only `kexec_load` path with the pinned `k3ctl` client, on
2026-10-28 between 03:32 and 06:17 UTC; automation never typed at U-Boot.
The campaign directory is
`K3_RUN_ROOT=$PWD/build/mvp/k3-campaigns/20261028-com260-m2a`, whose
`summary.md`, the campaign tool's, says `Boot marker reproduced: 6/6
runs` and `Distinct boots: 6 of 6 runs`, with `serial-log-note.txt`
written by hand from the operator's picocom log; this is the campaign M2
presents. The preflight and both load checks of 02:31 and 02:32 stand and
were not repeated, since no image changed (M2-A.2); they name anchor's
expectation as M2-5 wrote it, and the runs M2-A's (`anchor.json`
`97e8b2aca656…`; M2-A's change to the generator is the probe line's
`spv=<S>`). Every Linux handed over from hart 0 (`kexec_hart=0
started=none` in each `check.txt`; `base=0x108000000 fdt=0x108400000` in
the summary), and every run's boot marker is `PASS`:

| Run | Image | Image SHA-256 | kexec requested | Terminal marker | Result | Reset | Fedora back, boot ID after |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `20261028T033233Z` | GCC `anchor` | `3b554f2cd0c6` | 03:32:35 | 03:32:47, `BE_MVP:14 SHUTDOWN` | PASS: `RUN_COMPLETE … idle_ticks=0x3aceed4 overlap_ticks=0x33a5a2f ticks=0x59b571d`; hart 2's probe `sent=0x235986 received=0x2359ba answered=0x2359ba spv=0` in `seq=1`'s wait, hart 1's `sent=0x1ce573 received=0x1ce5c7 answered=0x1ce5d0 spv=1` | 03:32:52, `OK reset` | Not within 300 s: `reset_outcome=reset-no-new-boot-id`, `stop=10` (below) |
| `20261028T060802Z` | GCC `anchor` | `3b554f2cd0c6` | 06:08:04 | 06:08:17, `SHUTDOWN` | PASS: `ticks=0x59b564c`; hart 2's probe `sent=0x235984 received=0x2359bb spv=0` | 06:08:23, `OK reset` | 06:09:05, 42 s, `57e5ef40…` |
| `20261028T060936Z` | GCC `anchor` | `3b554f2cd0c6` | 06:09:38 | 06:09:50, `SHUTDOWN` | PASS: `ticks=0x59b557c`; hart 2's probe `sent=0x235989 received=0x2359bb spv=0` | 06:09:56, `OK reset` | 06:10:29, 33 s, `eda6ee62…` |
| `20261028T061147Z` | Clang `anchor` | `37cdfd7064b0` | 06:11:49 | 06:12:01, `SHUTDOWN` | PASS: `ticks=0x59b564f`; hart 2's probe `sent=0x23598c received=0x2359c0 spv=0` | 06:12:06, `OK reset` | 06:12:53, 47 s, `2be97499…` |
| `20261028T061356Z` | GCC `wrong-measurement` | `61a3cd8a3c48` | 06:13:58 | 06:14:07, `BE_MVP:FAIL measurement` | PASS as declared: after both `PAYLOAD_PLACED` lines, `BE_MVP:DETAIL domain=1 hart=2 computed=e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b expected=e1c6bd23…`, the variant's one changed bit; no domain hart started (`mgmt_g0=0 mgmt_g1=0 g0=0 g1=0`) | 06:14:12, `OK reset` | 06:14:45, 33 s, `f86e14fb…` |
| `20261028T061549Z` | GCC `no-grant-check` | `9b0aca48af15` | 06:15:51 | 06:16:05, `BE_MVP:FAIL run-timeout` | PASS as declared: `BE_MVP:12 DOMAIN_TERMINATED hart=1 domain=0 by=1 exits=139 sha256=- ticks=0x15445aa`; `BE_MVP:MGMT hart=2 domain=1 seq=1 fid=terminate target=0 result=0 target_state=terminated ticks=0xa60ed service=0x16ba708`, then `seq=2 fid=pause target=0 result=-10 target_state=-` (`SBI_ERR_INVALID_STATE`, the host terminated); `DETAIL ticks=0x8000000`; `denials_g0=4 denials_g1=1 mgmt_g0=0 mgmt_g1=2 g0=59 g1=59` | 06:16:10, `OK reset` | 06:16:53, 43 s, `cb56d28d…` |

Each `run.txt` names its image's SHA-256, which the board tool's image
check confirmed before the load (`BE_MVP_BOOT_IMAGE[gcc]: PASS …`, or
`[clang]`), anchor's report (`418797a29bf5…`), the measured inputs
(`measured=Image kernel_sha256=c7ae03e6b26e… mvp-guest-g1-anchor.dtb
dtb_sha256=903799a1d59b…`), and its expectation (`anchor.json`
`97e8b2aca656…`, `wrong-measurement.json` `afcbdc6d5735…`, or
`no-grant-check.json` `afed1e28c5e9…`); each run's `check.txt` ends
`BE_MVP_CAPTURE[kexec anchor]: PASS` (or `wrong-measurement`,
`no-grant-check`). Each `reset.txt` shows the probe finding Fedora down
(`ssh: connect to host 192.168.2.7 port 22: Connection timed out`),
`status` before and after the reset at `rst=0 fcrec=0 pwr=0 k3=n/a
ver=1.0`, and `reset_reply=OK reset`; all but the first run's then give
the new boot ID, the seconds to it, and `outcome=reset`.

**The `anchor` runs.** All four passed with the first campaign's counts,
`exits_g0=248 exits_g1=132 denials_g0=4 denials_g1=1 mgmt_g0=13 mgmt_g1=2
records=174 wakes=16 alternations=122 g0=83 g1=62`, overlaps of
`0x33a593f` to `0x33a5a2f` ticks, each the whole of the shorter interval
(`shorter_ticks` equal), and `hart0_idle_permille=655`. Each printed
`MEASURED … bytes=1907940 sha256=e0c6bd23… expected=match` (`0xc125e` to
`0xc49ec` ticks, 32.964 to 33.556 ms), the first campaign's five DENY
lines and fifteen `BE_MVP:MGMT` lines with their results, `DOMAIN_PAUSED`
and then `DOMAIN_TERMINATED` for domain 1 with `exits=132` in both and the
measurement unaltered, and the host's `DOMAIN_SHUTDOWN … exits=248
sbi=243 ipi=1 … refused=1 lines=83 ring_peak=0x1728`; the four requests
were answered with the HMAC values the checker recomputes. In every one
hart 2 answered its PING inside its first management wait, with
`g1_ping_in_mgmt_wait=1 g1_ping_mgmt_seq=1` among the costs: the PING was
received 96.530 to 96.531 ms after the barrier, inside the wait of
`seq=1` (`terminate 0`), which began at 28.326 to 28.356 ms and ended at
929.168 ms; hart 1's was received at 78.909 to 78.910 ms and answered
with `spv=1` (each run's `serial.log`; the platform record's "The IPI
probe in a management wait" tables them). The `no-grant-check` run's
hart 2 answered its PING inside its first wait too (`received=0x2359be
spv=0`; open item 62).

**The run time (stop condition 7).** The `anchor` runs took `0x59b557c`
to `0x59b571d` ticks (`RUN_COMPLETE`'s `ticks`, the checker's
`hart0_run_ticks`), 94,066,044 to 94,066,461, 3.919 s at the board's
24 MHz: 70.1 percent of 2^27 = 134,217,728 ticks (5.59 s), so the
`no-grant-check` budget separates the positive run from the hang it
declares by 1.67 s; the run budget is `0x100000000` ticks (178.957 s).
In QEMU the scenario's first whole run took `0x3e8cfb1` ticks, 6.56 s of
QEMU's 10 MHz timebase (M2-4's `build/mvp/anchor-e2e-gcc.log`). The
host's outbound ring's high-water mark, `0x1728`, is 36 percent of the
budget, half the `0x8000`-byte ring, and its 248 exits are within 2^20;
no budget was overrun.

**The reset after the first run (stop 10).** After the first run the
tool's conditions held and it reset the board at 03:32:52 (`OK reset`,
`status` after `rst=0 fcrec=0 pwr=0`), and the operator's log shows the
board booting through the boot ROM, U-Boot SPL, and U-Boot to Fedora's
login prompt. That boot got no IPv4 address: its banner reads `Web
console: https://localhost:9090/` alone, where every other boot in the
log reads `… or https://192.168.2.7:9090/`, and
`NetworkManager-wait-online.service` ran far longer than in the other
boots; the board answered no ARP at 192.168.2.7, and no other host on the
LAN carried its SSH host key. The run tool, which waits for a new boot ID
over SSH, found none within 300 s (`last_probe_detail=ssh: connect to
host 192.168.2.7 port 22: No route to host`), made no second reset, and
stopped (`BE_MVP_K3_RUN: STOP stop=10 no-new-boot-id-within-300-s`;
`reset_outcome=reset-no-new-boot-id` in `run.txt`), and the campaign tool
stopped with it (`BE_MVP_K3_CAMPAIGN: STOP run 1/3 exited 10`); the run's
own check had passed. That is M1 Q14's stop 10 and M2's stop condition 9
("the reset path refusing or failing"), which returned M2 to the
responsible human. The human answered the form `action=reset-resume,
extra_reset_rule=true`: a second `k3ctl reset`, made by hand at
06:05:31 UTC (`OK reset`) with the client the tool uses (the `K3CTL`
path the preflight had checked against the pin, `7ca3d78a…`), after
which Fedora came up at 192.168.2.7
(`end0` up with `192.168.2.7/24`) with boot ID `376c699c…` by 06:07; the
campaign resumed into the same `K3_RUN_ROOT`, the tool appending its
runs, as in M0-5's second campaign; and one extra reset allowed per run
should the event recur, which no later boot needed. Between that boot and
the second run the human logged in at the serial console and ran
`ifconfig`. The event is the board's or its network's, not a monitor
outcome; the second reset is in no `reset.txt`, only in the hand-written
note (open items 59 and 60).

The campaign tool's `summary.md` tables the six runs, each with its boot
ID before, the board kernel, `kexec_load`, the boot marker, the terminal
(`shutdown-requested` four times, `fail-marker` twice), hart 0, and the
image and FDT addresses, and lists the four image SHA-256 values. The
`serial-log-note.txt`, written by hand from the operator's picocom log
(not retained), places the campaign in that log (lines 96,366 to 106,981,
03:32 to 06:17 UTC) and records, for each run, the kexec handoff, the shim
line, and the monitor's lines to the terminal marker, then each reset's
boot ROM, U-Boot, and Fedora lines (seven reboots for six runs, the first
without an IPv4 address, and the human's `ifconfig` at the console), no
OpenSBI banner line (open item 40), and the first campaign's run and its
reset by hand at 02:44:32 UTC.

**Claim boundary.** This is diagnostic bring-up evidence from one COM260,
its firmware (`SBI implementation ID=0x1 Version=0x10006`), and one
Fedora kernel, under a checker rule the responsible human directed after
the board had shown the outcome (Plan revision M2-A); it is not hardware
validation, qualification, or formal verification. The runs show, in the
tested scenario, the protected domain measured with the offline value,
the five tested accesses denied, logged, and delivered as access faults,
the fifteen management requests decided by hart 0 with the declared
results, the protected domain paused and then terminated by the host's
granted requests with its measurement unaltered, the four requests
answered with the HMAC values the checker recomputes, and the two board
negatives failing as declared; isolation beyond the tested accesses
remains by construction (plan, "Claim boundary and non-goals"). The probe
answered inside a management wait is an observation of what Q14
describes, not a new claim. The service ticks, the measurement's time,
and the reset times are recorded only.

### M2-7 (2026-10-28)

M2-7 makes the board record of the second campaign with its platform
record, these results, and the checking-to-monitor size; the result
packet and the status documents are outside `mvp/`. Its change to the
tree is this README: the M2-1 to M2-5 results, the counted copies, and
open items 47 to 58 in `e021e7ec`, and then these sections, the counted
copy of `tests/run-tool-dry-run.sh` at the M2-7 content, and the
statements M2-A and M2-6 change; `tools/evidence.py` and
`tools/platform-record.py` are unchanged from `ac0d48dd`. The board
record is to be `results/20261028-com260-m2a/`, written by
`K3_RUN_ROOT=$PWD/build/mvp/k3-campaigns/20261028-com260-m2a ./mvp/mvp
board-evidence` from a clean tree at the exact M2-7 commit and committed
after it, never by hand. A preview made outside the repository on the
`e021e7ec` tree (`source_tree=clean`) printed `BE_RETAIN: PASS runs=6
load_checks=2 files=91`; six `ok … recorded PASS, excerpt PASS` lines;
`BE_MVP_PLATFORM_RECORD_M2: anchor_runs=4 page_lines=18 measured=5
requests=62 transitions=9 digests=16 pings_in_wait=4`;
`BE_MVP_PLATFORM_RECORD: PASS … runs=6 probe_values=0 scenario_runs=0
te_poc_runs=0 denials=0 channel_checked=0 qemu_gcc,clang=0,0
resets=human:0,k3ctl:6`; and `BE_MVP_EVIDENCE: PASS board … runs=6
pass=6 fail=0 refused=0 stop=0`. Its `mvp/runs.tsv` gives the first run
`PASS 10 k3ctl` (verdict, stop, and reset) and the others `PASS none
k3ctl`; it holds both `anchor` load checks
(`load-check/gcc-20261028T023207Z` and `clang-20261028T023241Z`), the
preflight, each run's `reset.txt` under `mvp/resets/`, the three
scenarios, te-poc's and anchor's each with its `policy.te` and authority
report, the policy checks on both under `mvp/policy/`, and the
serial-log note, which the platform record gives as its Serial log
paragraph.

At exact commit `397670e5`, from a clean tree on `l1`, the gates passed in
this order, each through the wrapper's clean environment: `./mvp/mvp check`
(06:57:10 to 07:03:05 UTC: `BE_MVP_LOCK: PASS roles=29 host_only_skipped=0
closure=259 lock_sha256=6e99262f04a1`; the seven host tests on their pinned
counts, GCC = Clang (ring 160, hart 843, sbi 130, gstage 44, payload 8,
deny 38, sha256 16 scenarios); `BE_MVP_POLICY_MUTATIONS: PASS mutations=14
rejected=14` and the four build-stopping negatives refused;
`BE_MVP_IMAGE_CHECK: PASS mutations=97`, `=100`, and `=111`;
`BE_MVP_CAPTURE_SELF_TEST: PASS cases=70 failed=0`;
`BE_MVP_CAPTURE_MUTATIONS: PASS mutations=229 rejected=229 seed=0x4d30`;
`BE_MVP_RUN_TOOL_DRY_RUN: PASS`; `BE_MVP_QEMU: PASS runs=58 attempts=75
refused=17`; `BE_MVP_BUDGETS: PASS measured=32`; `BE_MVP_EVIDENCE: PASS
development … files=320 images=247 qemu_attempts=75 rehearsals=6`;
`BE_MVP_CHECK: PASS`); `./mvp/mvp evaluate` (07:03:21 to 07:09:14 UTC:
`host source=397670e5… tree=clean images=247`; inside the evaluator
`BE_MVP_LOCK: PASS roles=26 host_only_skipped=3 …`, `BE_MVP_QEMU: PASS
runs=58 attempts=77 refused=19`, and `BE_MVP_CHECK: PASS`;
`BE_MVP_IMAGE_IDENTITY: PASS images=247 same=247 differing=0`;
`BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`);
`./mvp/mvp kexec-rehearsal` (07:09:24 to 07:10:45 UTC: six
`BE_MVP_KEXEC_REHEARSAL: PASS smp=8 …` lines, images `80ac8e334151`,
`4f4d684b8689`, `3b554f2cd0c6`, `153e7482d2b0`, `746585fbecb8`, and
`37cdfd7064b0`, the refused domain-hart boots repeated within the bound);
and `make -C mvp kernel-repro LINUX_GIT=/home/jmorris/src/kernel.org/linux`
(07:10:45 to 07:11:14 UTC: `BE_MVP_KERNEL_REPRO: PASS outputs=15
identical; sysroot_files=1065 sysroot_sha256=c931b51b…`). The board
record was then made from the same clean tree (07:11:24 to 07:11:30 UTC):
`BE_RETAIN: PASS runs=6 load_checks=2 files=91`; six `ok … recorded PASS,
excerpt PASS` lines; `BE_MVP_PLATFORM_RECORD_M2: anchor_runs=4
page_lines=18 measured=5 requests=62 transitions=9 digests=16
pings_in_wait=4`; `BE_MVP_PLATFORM_RECORD: PASS … runs=6 probe_values=0
scenario_runs=0 te_poc_runs=0 denials=0 channel_checked=0
qemu_gcc,clang=0,0 resets=human:0,k3ctl:6`; `BE_MVP_EVIDENCE: PASS board …
runs=6 pass=6 fail=0 refused=0 stop=0`; `python3 -B tools/evidence.py
--verify results/20261028-com260-m2a` reports `files=93`. The record's
`bundle.txt` holds `source_commit=397670e5cced0db733f494beee44518f9d10f706`,
`source_tree=clean`, and `lock_check_status=0`; its `MANIFEST.sha256` has
SHA-256 `1958b249ecd26c2f28bbdb7e36325e306b6adf2d994fc7ae3a490413c104df17`.
The record is committed in the commit after `397670e5`, with this
paragraph.

**Checker-to-monitor size** (S1 H43; plan, Q17, "Budgets", and stop
condition 13: at most 2.3 lines of checking code per monitor line).
Counted by M1-6's method on the M2-7 content, each row's files' lines
summed with `wc -l`; Plan revision M2-A changed only files already
counted, and M2-7 changes none of them:

| Code | MVP at the M2-7 content | MVP at M2-5 (`da7d270f`) | MVP at the M1-6 content (`17ed82f7`) |
| --- | --- | --- | --- |
| Monitor: `src/*` and `shim/mvp-shim.S` | 12,817 | 12,817 | 10,176 |
| Checkers: `tests/check-capture.py`, `tests/check-image.py`, `tools/budgets.py`, `tools/platform-record.py`, and `tools/policy-check.py` | 10,653 | 10,388 | 8,340 |
| Host tests: `tests/*-test.c` (seven) | 12,568 | 12,568 | 9,996 |
| Harness drivers and their tests: M0-6's six and `tests/fake-k3ctl.py` | 3,742 | 3,724 | 3,467 |
| Checking code | 26,963 | 26,680 | 21,803 |
| Lines of checking code per monitor line | 2.104 | 2.082 | 2.143 |

M2-A adds 283 checking lines and no monitor line:
`tests/check-capture.py` 172, `tools/platform-record.py` 93, and
`tests/run-tool-dry-run.sh` 18; the generator's 29 and the fixture's 397
are not counted, as no generator or fixture is. M2's increment over the
M1-6 content is 2,641 monitor lines and 5,160 checking lines, 1.95 per
monitor line. The ratio stays below the plan's 2.3 (stop condition 13
does not apply; 2,516 lines to spare). On the M2-7 content the two
commands in [M2-5](#m2-5-2026-10-28) print 12817 and 26963.

### M4-1 to M4-3 (at `30800dd3`, `c0097a4c`, and `90b6b4a5`, 2026-10-28)

M4-1 to M4-3 are work packages of the accepted M4 plan ("Work packages"),
on the branch `beryllium/mvp-m4` from its acceptance record `4e10fca3`.
M3 changed nothing under `mvp/` (`git diff --stat 18d552bc fb8accc9 --
mvp/` is empty), so M4 begins from the accepted M2 result's tree. The
three write the four release surfaces under `docs/` and the ledger's
checker and change no monitor, shim, guest, scenario, generator,
checker-rule, or lock byte; the `Makefile` and the wrapper change only to
run the checker and render the ledger (`git diff --stat 4e10fca3 30800dd3`
lists seven files, all under `mvp/`; M4 plan, "What M4 does not do").

| Package | Files | What |
| --- | --- | --- |
| M4-1 (`30800dd3`) | `docs/claim.md` | The claim and its required limit, byte for byte the M4 plan's "The MVP claim" (the plan's 14 blockquote lines and its required-limit paragraph equal the file's), without the alternative (b) clause (Q2's default); the "Forbidden phrasings" list, its single source: 35 literals (the MVP plan's 11, its "SELinux, FLASK, or XSM for RISC-V" written as three, and the M4 plan's 24 in 14 groups), 3 conditional phrasings, and 2 review items; 126 lines |
| M4-1 | `docs/claim-ledger.json`, `docs/claim-ledger.md` | 28 claim rows, 66 cited artifacts, each with its SHA-256 and source commit (`b2669725`, `ff84533c`, `18d552bc`, or `b0a0f352`), 6 rows marked historical, 12 unproved-boundary items, and the 2 review items; the release identity's two commits null until M4-4 and M4-6 |
| M4-1 | `tools/claim-ledger.py`, `Makefile`, `mvp` | The checker (682 lines); `claim-ledger-check` (23 lines added to the `Makefile`); `./mvp claim-ledger check`, `render`, and `self-test` (20 lines added to the wrapper) |
| M4-2 (`c0097a4c`) | `docs/guide.md` | The researcher guide in the plan's nine sections, 1,043 lines; its `./mvp/mvp` commands are 19 of those `mvp help` lists, used 39 times, beside `make -C mvp kernel-repro` |
| M4-3 (`90b6b4a5`) | `docs/ai-assistance.md`; `docs/claim-ledger.json` and `docs/claim-ledger.md`; this README; the root `README.md` | The disclosure (Q7), 275 lines; row C-23's non-claim reworded so that the whole field is a non-claim, and the table rendered again; this README's title, opening, M4 entries, the counted `Makefile` copy, and open items 63 to 67; the root README's one pointer to the guide and the claim |

On M4-3's tree before it was committed, on `l1`, through the
wrapper's clean environment, `./mvp/mvp claim-ledger check` and
`./mvp/mvp claim-ledger self-test` printed:

```text
claim ledger schema: PASS
claim ledger methods: PASS
claim ledger evidence: PASS artifacts=66 records=3
claim ledger commits: PASS commits=4
claim ledger rendering: PASS
claim ledger guide commands: PASS commands=39
claim ledger phrasing: PASS surfaces=4 literals=35 conditionals=3 review_items=2
claim ledger privacy: PASS files=4
claim ledger headers: PASS surfaces=4
BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=28 boundary=12
claim ledger self-test: PASS mutations=19 variants=4
```

The phrasing, privacy, and header checks scan the four surfaces (three at
M4-1, before the disclosure existed); the disclosure quotes the commits'
`Co-authored-by` trailer with its address, which the privacy rule's `ssh`
user-and-host forms do not match. The self-test's 19 seeded mutations
each fail exactly their own check, and its 4 variants pass. `check` took
0.14 to 0.16 s and the self-test 2.3 to 3.2 s, three runs each (M4-1
measured 0.14 to 0.15 s and 2.2 to 3.1 s). `make -C mvp lint` passes, and
`make -C mvp claim-ledger-check` passes and joins its two records to the
last bundle, which verifies (`files=328`, as at M4-1). The new checking
code is 725 lines, the checker's 682 and the `Makefile`'s 23 and the
wrapper's 20 added lines, of the M4 plan's soft limit of about 900 for all
of M4's checking and record code (Q10); M4-2 and M4-3 add none. The
records of M4-1 to M4-3 hold no full `./mvp/mvp check`, `./mvp/mvp
evaluate`, kexec rehearsal, `kernel-repro`, or board run: M4-4 runs the
gates from a clean standalone checkout of the candidate tree, and M4-5
the board after the responsible human confirms the K3 free.

### M4-4's tool and the privacy rule's false positives (at `0a968bf0` and `ca322220`, 2026-10-28)

M4-4 begins with its tool, so that every tool is in the candidate tree
(M4 plan, "The release-candidate evidence (M4-4)"): `tools/rc-record.py`
(591 lines), run as `./mvp/mvp rc-record`, with a `rc-record-check`
target in `tools.mk` under `tools-check`. Every input is explicit
(`--commit X --out DIR --host-bundle --evaluator-record --model-host
--model-evaluator --model-evaluator-logs --rehearsal … --kernel-repro
--gate NAME=LOG …`); a path that is a symlink or named `latest` is
refused; each input must name `X` as its clean source commit (the
bundle's `bundle.txt`, the evaluator record's `evaluate.txt`, the model
evidence's `source-state.txt`), each rehearsal's image must be in the
bundle's `images.sha256`, `kernel-repro` must report every pin identical,
the evaluator's `closure_sha256` and `containerfile_sha256` must equal the
SHA-256 of `tools/lock/closure.txt` and `tools/evaluator/Containerfile` at
`X`, and each of the seven gates' logs must carry its PASS line between
`start_utc=` and `end_utc=` lines; a failure refuses before anything is
written. The record is `rc.txt` (the commit, tree, `host_os`,
`host_arch`, the lock's and closure's SHA-256, one line per gate with its
PASS line and duration), `host/` (the bundle, every file through
`evidence.py`'s rewriter), `evaluator/` (the record and a
`compare-images.txt`), `model/host/`, `model/evaluator/`,
`model/evaluator-logs/`, `rehearsal/<label>/`, `kernel-repro.txt`, and
`MANIFEST.sha256` over every other file. Beside `evidence.py`'s rewriting
and `identifying()`, the tool rewrites a `Linux version` banner's build
`(user@host)` to `(<build-user>@<build-host>)`, keeping the guest's
pinned `(be@beryllium)`, because the external rehearsal kernel's banner
names its build machine, and scans every written text with the
claim-ledger checker's privacy rule. The self-test builds a synthetic
input set in a scratch repository and requires 21 seeded single-defect
mutations to be refused: `rc-record self-test: PASS mutations=21`.
Against this host's inputs, which are of two different commits, the tool
refuses with the right line for each case (the bundle not of a clean
tree at `X`; `latest`; an abbreviated commit).

The privacy rule imported from `tools/claim-ledger.py` read two strings
every release-candidate record carries as private: the evaluator's base
image reference by digest (`registry.fedoraproject.org/fedora@sha256:…`,
in `evaluate.txt` and the model evaluator's `image-build.log`) as an ssh
user and host, and a package version after a hyphen
(`dnf5-5.4.2.1-1.fc44`, in `evaluate.txt`, `rpms.txt`, and `swap.txt`) as
an IPv4 address. Neither is what pass criterion 1 forbids, so the two
patterns were narrowed (`ca322220`: no `@sha256:`, `@sha384:`, or
`@sha512:` digest; no address after a hyphen) with three self-test cases
(the digest and the version pass; `fedora@board:/tmp` and `connect to
host 192.0.2.7` fail): `claim ledger self-test: PASS mutations=21
variants=5`, and over every release-candidate input on this host the
rule has no hit. `make -C mvp lint`, `./mvp/mvp claim-ledger check`
(`checks=9 claims=28 boundary=12`), and both self-tests pass.

**The new checking and record code is 1,347 lines** (`git diff --numstat
4e10fca3 ca322220` over `tools/claim-ledger.py` 692, `tools/rc-record.py`
591, `Makefile` 23, `mvp` 28, `tools.mk` 13), against the M4 plan's soft
limit of about 900 for all of it, tests included (Q10); 326 of them are
the two seeded self-tests and 81 the docstrings that define the two
tools' interfaces. That is stop condition 5, returned to the responsible
human with the limit for re-evaluation; nothing was cut. With it goes
stop condition 9, found before any record was made: a release-candidate
board record made with today's board tools would carry the board's ssh
target and IP address ([open items](#open-items) 63 and 64) and the M2
title (65), and the remedy touches `tools/evidence.py` and `tools.mk`
beyond what "What M4 does not do" allows, so it needs the responsible
human's direction and must land in the candidate tree before M4-4's
gates. The candidate tree is not fixed and no gate has run.

### Plan revision M4-A (at this commit, 2026-10-29)

At M4-4, before any release-candidate record was made, the accepted M2
record `results/20261028-com260-m2a/` showed what a board record made with
the board tools carries: the board's ssh target `fedora@k3-f45` 20 times
(the `k3_ssh=` line of the six runs' and the two load checks' `run.txt`,
and six rows each in the runs tables of `platform-record.json` and
`platform-record.md`, which carry that field's value) and its address
`192.168.2.7` 26 times (the reset probe's `ssh: connect to host … port
22: …` in the six `mvp/resets/*.txt`, 7; `mvp/serial-log-note.txt`, 4;
`platform-record.json`, 11; `platform-record.md`, 4), and `tools.mk`
titled every record `MVP M2 COM260 campaign <campaign>` (open items 63
and 65). The privacy rule of pass criterion 1 forbids both strings in a
release-candidate record, and the remedy changes `tools/evidence.py` and
`tools.mk` beyond "What M4 does not do", so stop condition 9 returned it
to the responsible human, who directed `re stop 9, agree with redaction /
code names.`; the plan records it as Plan revision M4-A (`ace52d39`), with
erratum 1 of its acceptance record, the soft limit on new code re-set to
2,000 lines (`re stop 5, increase the limit to 2000.`).

**The code names** (M4-A.1). `tools/evidence.py`'s rewriting, after the
checkout's and HOME's prefixes, rewrites:

- to `<board-ssh>`, a `user@host` (a user of `[\w.+-]`, a host of
  `[A-Za-z0-9]` then `[\w.-]`) in each place the claim-ledger checker's
  privacy rule finds an ssh user and host: the value of an `ssh…=` field
  (`k3_ssh=`), the destination of `ssh` or `scp` after their options,
  after `ssh://` (which goes too), and before a colon (scp's
  `user@host:path`, ssh's `user@host: Permission denied`), but never an
  `@sha256:`, `@sha384:`, or `@sha512:` image digest; the context is kept
  (`k3_ssh=<board-ssh>`, `ssh <board-ssh>`);
- to `<ip>`, an IPv4 literal by the privacy rule's own pattern: four
  decimal octets, not after a word character, a dot, or a hyphen, and not
  before a word character or a dot and a digit.

Every other `@` and dotted number is kept: the guests' banner
`(be@beryllium)`, which the capture checker matches, Fedora's
`(mockbuild@…)`, DT nodes (`cpu@0`), the deny specifications
(`store@0x84000ff8`), MTD partitions (`384K@1728K`), e-mail addresses,
image digests, package versions after a hyphen (`dnf5-5.4.2.1-1.fc44`),
and kernel releases (`7.3.0-65.1.riscv64.omni.fc45.riscv64`, `v7.2`). A
host name alone is not rewritten. The development bundle's writer and a
board record's writer (the `mvp/` files) rewrite as they write; B0's
retention, unchanged, rewrites its copies and excerpts with the prefixes
alone, so `board_record()` then rewrites every file B0 wrote in place,
before the excerpts are checked again and before
`tools/platform-record.py`, which derives the platform record from the
record's own files, so that it inherits the code names. `identifying()`
gains `PRIVATE`, the privacy rule's IPv4 and ssh patterns as
`tools/claim-ledger.py` writes them (a self-test case compares the two),
and a board record is now refused if any of its files is identifying
(before, B0's scan covered B0's rule and `identifying()` the platform
record's two files). The originals' digests stay where they were: B0's
`originals.sha256` and `mvp/resets/originals.sha256`. `--verify` reads the
manifest alone, so the accepted M0, M1, and M2 records, which keep the
board's strings, still verify; they are neither rewritten nor scanned.
`tools/rc-record.py` keeps the prefixes alone (`rewriter`'s default), so
an address or ssh target in a release-candidate input is still refused,
as its self-test requires.

**The title** (M4-A.2). `tools.mk` passes `--title "$(K3_RECORD_TITLE)
$(notdir $(K3_RUN_ROOT))"`, with `K3_RECORD_TITLE ?= MVP COM260 campaign`.
For M4-5 to pass `K3_RECORD_TITLE="MVP 1.0 release candidate COM260
campaign"`, the wrapper passes the variable (its caller list and help),
and the Make controls admit it (`tools/make-control.py`, the form
`^[A-Za-z0-9][A-Za-z0-9 .,-]{0,79}$`, and two self-test cases, 57 in
all), which M4-A's text does not name: without them Make refuses the
assignment while it reads the makefiles. `make -p` on a target that does
not exist, from the wrapper's clean environment, shows the default from
`tools.mk`, a command-line and an environment value as given, and the
recipe's `--title "$(K3_RECORD_TITLE) $(notdir $(K3_RUN_ROOT))"`; a value
with a quote stops Make (`BE_MVP_MAKE_CONTROL: FAIL MVP rejects
command-line K3_RECORD_TITLE value …`). The dry run passes its own title
to `tools/evidence.py` and has no expectation of the Make default. The
guide's description of the wrapper's caller variables, the bundle's
rewriting, and the identifying-data rule follows (`docs/guide.md`).

**Checks**, on `l1`, on this commit's tree before it was committed:

```text
BE_MVP_EVIDENCE_SELF_TEST: PASS cases=34/34
BE_MVP_RUN_TOOL[code-names]: PASS (the ssh target and the address only as <board-ssh> and <ip> in run.txt, both load checks, the reset record, the serial-log note, and the platform record; the reset original's SHA-256 kept; nothing the claim ledger's privacy rule finds; BE_RETAIN: PASS runs=1 load_checks=2 files=61)
BE_MVP_RUN_TOOL_DRY_RUN: PASS
BE_MVP_MAKE_CONTROL_SELF_TEST: PASS cases=57
rc-record self-test: PASS mutations=21
claim ledger self-test: PASS mutations=21 variants=5
BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=28 boundary=12
BE_MVP_EVIDENCE: PASS verify mvp/results/20261025-com260 files=75
BE_MVP_EVIDENCE: PASS verify mvp/results/20261027-com260-m1b files=82
BE_MVP_EVIDENCE: PASS verify mvp/results/20261028-com260-m2a files=93
```

The evidence self-test's six new cases: a record's ssh target and
address are code names in the development bundle; a run record's
`k3_ssh=user@fakehost` is `k3_ssh=<board-ssh>` in its copy; a reset
record's `ssh: connect to host 192.0.2.7 port 22: …` and `user@fakehost:
Permission denied` are `<ip>` and `<board-ssh>`; the kept strings above
are kept and nothing written is identifying; a bracketed host
(`k3_ssh=user@[fe80::1]`), an `ssh://` URL without a user, and an address
under the prefixes alone (rc-record's rewriting) are refused; and
`PRIVATE` is the privacy rule's. With the code names removed 4 of them
fail, and with `PRIVATE` removed 1. The dry run's new `code-names` case
runs one `te-poc` run with `K3_RESET=k3ctl` on a fake board whose probe
answers `ssh: connect to host 192.0.2.1 port 22: No route to host`
(TEST-NET-1) and a serial-log note naming the address and `ssh
fedora@fake-k3-board.invalid`, then its board record: the code names
where the strings were, neither string anywhere in the record, the reset
original's SHA-256 kept, and the claim-ledger
checker's eight privacy patterns, loaded from `tools/claim-ledger.py`,
finding nothing; every other case passes as before, the other records'
`k3_ssh=` now `<board-ssh>` (2 min 41 s, no image rebuilt). `make -C mvp
lint` passes.

Scanned with the new patterns, the accepted M2 record has 8 ssh targets,
each a `k3_ssh=fedora@k3-f45` field, and 26 IPv4 literals, each
`192.168.2.7`, and nothing else (`PRIVATE`: 34); M1's has 8 and 12, the
same strings, and M0's 10 (`fedora@k3e` 6, `fedora@k3-f45` 4) and none.
The platform records' runs-table cells (`"fedora@k3-f45"`,
`| fedora@k3-f45 |`) are none of the privacy rule's forms; a new record's
hold `<board-ssh>` because they are derived from the rewritten `run.txt`.
The M2 campaign's record made again into a scratch directory
(`tools/evidence.py --board build/mvp/k3-campaigns/20261028-com260-m2a`
with the same preflight and load checks, title "M4-A redaction check")
passes (`BE_MVP_EVIDENCE: PASS board … runs=6 pass=6 fail=0 refused=0
stop=0`, each excerpt checked again, 93 files, `--verify` PASS); no file
holds `fedora@` or `192.168`; `<board-ssh>` appears 20 times and `<ip>` 26,
in the same files and lines as the accepted record's strings; the privacy
rule finds nothing. With those two strings mapped to their code names,
every file equals the accepted record's but `MANIFEST.sha256`,
`mvp/bundle.txt` (`source_commit`, `source_tree`), the platform record's
14 input digests (the six `run.txt`, the six reset records, the note, and
`mvp/bundle.txt`), and `summary.md`'s title; both `originals.sha256` are
equal.

**The new code is 229 lines** (`git diff --numstat ca322220` over
`tools/evidence.py` 144, `tests/run-tool-dry-run.sh` 61,
`tools/make-control.py` 12, `tools.mk` 9, and `mvp` 3), so M4's checking
and record code is 1,576 lines of the 2,000 to which erratum 1 re-set
Q10's limit. The counted-copy tables of `tools.mk` and
`tests/run-tool-dry-run.sh` are not recounted here, nor were M4-4's
`tools.mk` lines. M4-A changes no accepted byte, retained record, B0 tool,
monitor, image, scenario, rule of the capture, image, or policy checker,
or the claim-ledger checker's privacy rule; an IPv6 address is neither
rewritten nor refused (open item 69). The plan fixes the candidate tree
`X` after this revision's implementation and the development log's
entries.

### The checkers' findings no longer quote the match (at this commit, 2026-10-29)

The first `rc-record` run on the seven gates at `0b2ac6fa` (the gates
passed; see the next entry) was refused by the record's own privacy
scan, and rightly: the evaluator record's `check.log`, which the record
keeps whole, held the strings `192.0.2.7`, `ssh://`, and `/home/`. They
were not identifying data but the self-tests' own output, which `check`
runs inside the evaluator too: the claim-ledger checker's privacy
finding quoted the matched text (`IPv4 address ('192.0.2.7')`), the
`rc-record` self-test printed those findings for the mutations it
refuses, and one `evidence.py` self-test case was named with the
literal scheme `ssh://`. A privacy finding that quotes what it found puts
the string into the log that reports it, so the three sites changed: the
claim-ledger checker and `rc-record` report the file, the line, and the
kind only, and the case is named without the scheme. The self-tests
still pass (`BE_MVP_EVIDENCE_SELF_TEST: PASS cases=34/34`, `rc-record
self-test: PASS mutations=21`, `claim ledger self-test: PASS
mutations=21 variants=5`) and their outputs no longer contain an
address, a scheme, or a home path; `make -C mvp lint`, `./mvp/mvp
claim-ledger check`, and the board tools' dry run pass. The change is
to M4's own tools only (M4-1's and M4-4's) and to one self-test name;
no rule changes. Because it is a source change, the candidate tree `X`
moves to this commit, and every gate of pass criterion 4 runs again on
it from the clean checkout; the run at `0b2ac6fa` is kept under
`build/mvp/rc-gates/attempt-1-0b2ac6fa/` and `attempt-2-73b1f7f2/` (the tree of `0b2ac6fa` under `mvp/`, after a planning-link fix) as
development history, not evidence.

### M4-4's gates and the release-candidate record (at `d42b9ec0`, 2026-10-29)

The candidate tree `X` is exact commit
`d42b9ec0a6d2f9f32d66ec2a983018e802b2d537` (tree `51f304d7`); no source
change follows it. From this checkout, clean at `X`, a driver under
`build/mvp/rc-gates/` (outside the tree) ran the seven gates of pass
criterion 4 in the plan's order, each logged between `start_utc=` and
`end_utc=` lines, 08:42:12 to 08:58:57 UTC:

| Gate | Result | Seconds |
| --- | --- | --- |
| `./mvp/mvp tool-lock check` | `BE_MVP_LOCK: PASS roles=29 host_only_skipped=0 closure=259 lock_sha256=6e99262f04a1` | 4 |
| `./mvp/mvp check` | `BE_MVP_CHECK: PASS` (the bundle `files=329 images=247 qemu_attempts=76 rehearsals=6`; `BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=28 boundary=12`; `rc-record self-test: PASS mutations=21`) | 382 |
| `./mvp/mvp evaluate` | `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`; `BE_MVP_IMAGE_IDENTITY: PASS images=247 same=247 differing=0` | 378 |
| `./mvp/mvp kexec-rehearsal` | six `BE_MVP_KEXEC_REHEARSAL: PASS smp=8 …` lines (images `80ac8e334151`, `153e7482d2b0`, `4f4d684b8689`, `746585fbecb8`, `3b554f2cd0c6`, `37cdfd7064b0`; the refused domain-hart boots repeated within the bound) | 86 |
| `make -C mvp kernel-repro LINUX_GIT=<mirror>` | `BE_MVP_KERNEL_REPRO: PASS outputs=15 identical; sysroot_files=1065 sysroot_sha256=c931b51b…` | 31 |
| `./be model-check` | `Beryllium Architecture Model 0.2 evidence: PASS` (`BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241`) | 64 |
| `./be evaluate` | `BE_EVALUATION: Model 0.2 rootless evidence PASS` | 60 |

The host's `build/model/evidence` was copied aside between the last two,
because `./be evaluate` rewrites it. `./mvp/mvp rc-record` then made
`results/20261029-rc/` from those inputs, each named explicitly and each
checked to name `X`: `BE_MVP_RC_RECORD: PASS … commit=d42b9ec0… files=422`
(3.4 MB; `rc.txt`, `host/` with the bundle's 11 rewritten files among
its copies, `evaluator/` with `compare-images.txt`, `model/host/`,
`model/evaluator/`, `model/evaluator-logs/`, six `rehearsal/<label>/`,
`kernel-repro.txt`, `MANIFEST.sha256`), and `--verify` passes
(`BE_MVP_EVIDENCE: PASS verify … files=422`). The record names no host,
user, or address: the `Linux version` banner of the external rehearsal
kernel reads `(<build-user>@<build-host>)`, and the ledger checker's
privacy rule finds nothing in it.

Two earlier attempts are development history, not evidence, under
`build/mvp/rc-gates/attempt-1-0b2ac6fa/` and `attempt-2-73b1f7f2/`:
the first stopped at `./be model-check` on a planning link whose
VitePress slug was wrong (fixed at `73b1f7f2`, no `mvp/` change); the
second passed every gate but `rc-record` refused the record because the
self-tests' fixture strings were in the evaluator's retained `check.log`
(fixed at `42009986`, the previous entry), which moved `X`.

**Q2's `anchor` comparison.** `X`'s four `anchor` board images in
`results/20261029-rc/host/images.sha256` (`gcc/anchor/be-mvp-boot.img`
`3b554f2cd0c6…`, `clang/anchor/be-mvp-boot.img` `37cdfd7064b0…`,
`variants/gcc/wrong-measurement/be-mvp-boot.img` `61a3cd8a3c48…`,
`variants/gcc/no-grant-check/be-mvp-boot.img` `9b0aca48af15…`) are
byte-identical to the four the M2-A board record's `summary.md` states,
so by Q2's rule M4-5 is the 11-run campaign for `two-guests` and
`te-poc`, and `results/20261028-com260-m2a/` is the `anchor` evidence at
the candidate's images; the ledger's row for it states both hashes.
M4-5 waits on the responsible human's confirmation that the K3 is free.

**Checker-to-monitor size** (S1 H43; the M4 plan, "Soft limits": the
ratio is reported, not limited), counted by M2-7's method on `X`
(`d42b9ec0`), each row's files' lines summed with `wc -l`, with M4's
additions in a row of their own, because they check documents and
records rather than the monitor; the harness row grows by M4-A's 61
dry-run lines:

| Code | MVP at `X` (`d42b9ec0`) | MVP at the M2-7 content (`18d552bc`) |
| --- | --- | --- |
| Monitor: `src/*` and `shim/mvp-shim.S` | 12,817 | 12,817 |
| Checkers: `tests/check-capture.py`, `tests/check-image.py`, `tools/budgets.py`, `tools/platform-record.py`, and `tools/policy-check.py` | 10,653 | 10,653 |
| Host tests: `tests/*-test.c` (seven) | 12,568 | 12,568 |
| Harness drivers and their tests: M0-6's six and `tests/fake-k3ctl.py` | 3,803 | 3,742 |
| Release-surface and record checkers (M4): `tools/claim-ledger.py`, `tools/rc-record.py` | 1,285 | 0 |
| Checking code | 28,309 | 26,963 |
| Lines of checking code per monitor line | 2.209 | 2.104 |

M4 adds no monitor line (`git diff --stat 18d552bc d42b9ec0 -- src shim`
is empty) and 1,346 checking lines: the two new tools and the dry run's
M4-A case. `tools/evidence.py`'s 144 and `tools/make-control.py`'s 12
M4-A lines are counted against Q10's new-code limit, not here, as
M0-6's method keeps `evidence.py` outside the four rows.

### M4-5's board campaign (2026-10-29)

On `k3 is available for you now, proceed` (2026-10-29, 10:04 local) the
board was reachable, the `k3ctl` client's hash equal to
`tools/k3ctl.sha256`, but running a one-shot boot of another project's
kernel, `7.3.0-k3-kvm-csr1` (`/boot/k3-kvm-csr1/Image`, booted 08:24
UTC), the GRUB default unchanged at `7.3.0-65.1.riscv64.omni.fc45`. The
M4 plan's stop condition 3 names a host kernel that differs from the
records; the responsible human was asked (reset to the default; the
human resets; run on the other kernel as a recorded departure; defer)
and was not available. The orchestrating session made one `k3ctl reset`
before any board command (17:06:55 UTC, `OK reset`;
`build/mvp/k3-campaigns/20261029-com260-rc/pre-campaign-reset.txt`
records the time, the reason, and that the session issued it), because
the campaign's own opted-in reset after its first run would have
rebooted the board into the default kernel in any case and the human had
handed the board over for eleven resets; Fedora returned on the recorded
kernel with boot ID `19befccc…` (over SSH at 17:08 UTC). This reset is
outside the plan's per-run rule and is recorded in the evidence record
for the responsible human's review.

The campaign then ran the plan's procedure, 17:11 to 17:37 UTC, with
`K3_RESET=k3ctl`, `K3_RECORD_TITLE="MVP 1.0 release candidate COM260
campaign"`, and the operator's serial log read output-only: the
preflight (`BE_MVP_PREFLIGHT: PASS`; the recorded kernel and firmware
identity); the two `two-guests` load checks (GCC, Clang: load, unload,
Fedora running); then eleven RAM-only `kexec_load` runs, each judged by
the capture checker and each followed by the tools' reset:

| Run | Image | Result |
| --- | --- | --- |
| `20261029T171402Z`, `…171523Z`, `…171655Z` | GCC `two-guests` `80ac8e334151` | PASS, `exits_g0=157 exits_g1=157 records=138 wakes=2 alternations=125` each |
| `20261029T171932Z` | Clang `two-guests` `153e7482d2b0` | PASS, the same counts |
| `20261029T172145Z` | GCC `payload` `27544cb42108` | PASS as declared: `BE_MVP:FAIL payload`, no hart started |
| `20261029T172416Z`, `…172547Z`, `…172708Z` | GCC `te-poc` `4f4d684b8689` | PASS, `exits_g0=163 exits_g1=167 denials_g0=1 denials_g1=2 records=146 wakes=2 alternations=127` each, the three `DENY` lines and both `CHANNEL` lines |
| `20261029T172931Z` | Clang `te-poc` `746585fbecb8` | PASS, the same counts |
| `20261029T173145Z` | GCC `reader-write` `1e4e43ecf40e` | PASS as declared: `BE_MVP:FAIL gstage` and its `DETAIL`, no domain run |
| `20261029T173409Z` | GCC `no-inject` `88a27e0b67c3` | PASS as declared: `BE_MVP:FAIL guest-page-fault`, hart 0's one `FAIL` and `DETAIL` pair after 54 lines from each guest |

Every image's SHA-256 on the board equals `X`'s in
`results/20261029-rc/host/images.sha256`; the counts equal M0's and
M1-B's accepted records' (the monitor unchanged since). Each reset
answered `OK` and Fedora returned with a new boot ID in 33, 33, 33, 33,
33, 42, 43, 43, 43, 45, and 47 s; no reset was made by hand, no run
needed the plan's extra reset, nothing was typed at the console, and no
stop condition applied. `./mvp/mvp board-evidence` wrote
`results/20261029-com260-rc/` (123 files, 1.2 MB; made from this
checkout clean at `X`, `bundle.txt`'s `source_commit=d42b9ec0…`, after a
first making from a later documentation-only commit, byte-identical but
for that field and the platform record's copy of it, was discarded so
that the record names `X`): `BE_RETAIN: PASS
runs=11 load_checks=2 files=121`, eleven `ok … recorded PASS, excerpt
PASS`, `BE_MVP_PLATFORM_RECORD: PASS … runs=11 probe_values=0
scenario_runs=4 te_poc_runs=4 denials=12 channel_checked=5`,
`BE_MVP_EVIDENCE: PASS board … runs=11 pass=11 fail=0 refused=0
stop=0`; `--verify` passes. Under Plan revision M4-A the record carries
`<board-ssh>` (35) and `<ip>` (22) where the accepted records carry the
board's ssh target and address, and no identifying string (`claim
ledger privacy: PASS files=549`). The serial-log note was written by
hand from the operator's picocom log, without the board's address. The
`anchor` scenario was not run (Q2's rule; the M2-A record's images are
`X`'s). The ledger gains C-32 to C-34 for the record, and C-09, C-11,
and C-15 cite it.

### M5-1 to M5-4 (2026-10-29 and 30)

M5-1 to M5-4 are work packages of the accepted M5 plan
([`planning/mvp-m5-plan.md`](../planning/mvp-m5-plan.md), accepted at
`0066794d` with Plan revision S3-A at `0d134bbc`, acceptance record
`9b3fa982`), on branches from that record merged in order on
`beryllium/mvp-m5`. They change no monitor source, shim, guest input,
scenario, generator, or expectation (`git diff --stat 9b3fa982 154dc810 --
src shim guest scenarios` is empty), and kexec is not used (S3-A, policy
item 2).

| Package | Commits | What |
| --- | --- | --- |
| M5-1 | `952f9e0c` (delivered with the plan), `f3a04a86` | `tools/k3-make-partition.sh` (1,226 lines), the human-run partition tool, with its host self-test `tests/test-k3-make-partition.sh` (22 cases, on the fake block tools of `tests/fake-partition-tools/`), which `check` runs since M5-2. On 2026-10-30 the responsible human ran it with `--apply` on the board: it created partition 6, ext4, labelled `beryllium`, as planned, and exited 5, because the mounted reference partition's feature list carried `orphan_present`, which the fresh filesystem lacks; like `needs_recovery`, that is ext4 mount state, not a format feature, and every format feature matched. `f3a04a86` treats it as `needs_recovery` is treated, and the self-test's fixture now gives the mounted reference both flags (see open item 76) |
| M5-2 | `d5c04456`, `a4cfb5dd`, `7f26dca2` (merged at `68240b77`); `5aa82ddd`, `ccb5e7f4`, `6252e51b`, `0ac1821d`, `132ef621`, `511dd4c0`, `bc41ea6c` (merged at `d798b065`); `26116490` | The capture checker's `uboot` mode (its self-test 108 cases, its mutation test 280 mutations) with two `uboot` fixtures; the image checker's QEMU-only image rule and the `Makefile`'s QEMU-only copies; the console tool `tools/k3-console.sh` and its log reader `tools/k3-uboot.py`; the staging and environment tools `tools/k3-stage.sh` and `tools/k3-env.sh`; `tools/k3-run.sh`, `k3-campaign.sh`, and `k3-preflight.sh` rewritten for runs from a reset, the kexec loader, its test, the kexec rehearsal, and the load check removed, and the read-only probe kept as `tools/platform-probe.py` with `tests/test-platform-probe.py`; the board record of a session (`tools/evidence.py`, `tools/platform-record.py` schema v3), the rehearsal's records in the bundle, and MAC and `serial#` code names; the board targets and commands (`k3-stage`, `k3-env record`, `install`, and `restore`, `k3-characterize`), with `RUNS`, `VARIANT`, and `SCENARIO` out of the caller variables; and the board tools' dry run on a fake U-Boot, `tests/fake-uboot.py` (24 case lines) |
| M5-3 | `75e7b894`, `02080590`, `3512c280`, `cb93e2fe` (merged at `dd0a5817`); `0e733e76` | The U-Boot rehearsal in QEMU, `tests/uboot-rehearsal.sh` with its driver `tests/uboot-rehearsal/run-qemu-uboot.py` (its self-test 49 cases, in `check`); `uboot-build`; the lock's host-only roles `mke2fs` and `sfdisk` and the U-Boot pins (`MVP_PIN_UBOOT_*`), and, for the console tool, `tmux` (`0e733e76`): 32 roles, 6 host-only, the closure unchanged |
| M5-4 | this branch's commits from `154dc810` | The release surfaces for release candidate 2: `docs/claim.md` with the M5 plan's board clause and required-limit text and one sentence more, from open item 72, on `fdtcontroladdr`; `docs/guide.md` (sections 2, 3, 4, 5, 7, and 9); `docs/ai-assistance.md`; the ledger (below); the operator's walkthrough `planning/mvp-rc-walkthrough.md`; and these entries |

At the merge of M5-2 and M5-3 the new code was 6,865 lines against the
M5 plan's soft limit of 5,000 (stop condition 8; open item 71), which the
responsible human re-set to 10,000 (erratum 1 of the plan's acceptance
record); M5-4 adds no code. The four deviations from the plan's letter
that M5-2 and M5-3 made are open item 72.

**The claim and the ledger (M5-4).** `docs/claim.md`'s board clause and
the required limit's new sentences are the M5 plan's, word for word (Q7;
"Documents and the claim (M5-4)"); the limit's "one host kernel" became
"one U-Boot build as its banner reports it", and one sentence more says
that the stored copy of U-Boot's environment may also differ by its
runtime `fdtcontroladdr`, which `saveenv` stores (open item 72). The
closing sentence and the forbidden phrasings are unchanged, and none of
them appears in the new text. In the ledger, C-10, the kexec loader row,
became the U-Boot boot path of release candidate 2 (by construction,
semantic checker, and adversarial test: the M5 plan at `9b3fa982`,
`tools/k3-env.sh` and `tests/check-capture.py` at the M5-2 merge
`d798b065`, and `tests/uboot-rehearsal.sh` at the M5-3 merge `dd0a5817`),
whose non-claim says that no board run of release candidate 2 and no
rehearsal record is retained yet and that every board run the other rows
cite was launched by kexec. C-24 to C-26 and C-29 to C-34, the kexec
campaigns and release candidate 1's records, are marked historical with
the schema's `historical` field, C-29 to C-34 named as release candidate
1's (open item 73). C-20 cites the lock as M5 left it, whose SHA-256 the
M5 lock roles changed, beside the lock checks recorded at M2's and
release candidate 1's trees. The release block names no candidate tree:
release candidate 2's `X2` and `R2` are not fixed, and release candidate
1's `d42b9ec0` is not this claim's tree; the checker allows null, and the
name stays the checker's "MVP 1.0 release candidate". On this branch's
tree, through the wrapper's clean environment:

```text
claim ledger schema: PASS
claim ledger methods: PASS
claim ledger evidence: PASS artifacts=77 records=5
claim ledger commits: PASS commits=9
claim ledger rendering: PASS
claim ledger guide commands: PASS commands=35
claim ledger phrasing: PASS surfaces=4 literals=35 conditionals=3 review_items=2
claim ledger privacy: PASS files=549
claim ledger headers: PASS surfaces=4
BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=34 boundary=12
claim ledger self-test: PASS mutations=23 variants=6
```

Before M5-4 two of the ledger check's nine checks failed: the guide named
the removed `kexec-rehearsal` and `k3-load-check` commands (five uses),
and C-20's `tools/lock/tool-lock.conf` no longer had the SHA-256 it
stated.

**The board images.** A `./mvp/mvp check` in this worktree on 2026-10-30
built 253 images, 247 of them release candidate 1's paths and 6 the new
QEMU-only copies. All 42 board images (`be-mvp-boot.img`) and every flat
image equal release candidate 1's in
`results/20261029-rc/host/images.sha256`; the 32 monitor ELFs
(`be-mvp.elf`) differ, because their debug information holds the
checkout's absolute path and this worktree's is not the main checkout's
(open item 77).

**The checks at M5-4.** At `3fa0cee5`, from this worktree clean at that
commit (`source_tree=clean`), on `l1` on 2026-10-30, `./mvp/mvp check`
passed in 4 min 39 s, ending (the checkout's path written as `<repo>`):

```text
BE_MVP_QEMU: PASS runs=58 attempts=75 refused=17
BE_MVP_EVIDENCE: PASS development <repo>/build/mvp/evidence/check files=294 images=253 qemu_attempts=75 rehearsals=0
claim ledger self-test: PASS mutations=23 variants=6
BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=34 boundary=12
claim ledger join: PASS records/claim-ledger records=2 files=296
BE_MVP_CHECK: PASS
```

with, among its stages, `BE_MVP_LOCK: PASS roles=32`, the capture
checker's 108 cases and 280 mutations, the board tools' dry run on the
fake U-Boot, the partition tool's 22 cases, and the rehearsal driver's 49.
The repository's documentation source check (`npm run
docs:source-check`, which reads `planning/` with the walkthrough) passed
too. M5-4 ran no U-Boot rehearsal, evaluator, or `kernel-repro`, and
issued no board command: the rehearsal's records, the gates at `X2`, and
the board session are M5-5 to M5-7's.

### M5-6a, M5-5, M5-6, and M5-7 (at `6dd81ee3`, 2026-10-30)

The board work and the records of release candidate 2, all on
`beryllium/mvp-m5`, in the order the board allowed rather than the
plan's letter (the gates ran once, after the campaign, at the final
`X2`; open item 81). The evidence record
[`planning/mvp-m5-evidence.md`](../planning/mvp-m5-evidence.md) holds
the detail; this entry is the log.

**M5-6a, the characterization (07:25 to 07:29 UTC, after six stopped
attempts).** Open items 79 and 80: six attempts each stopped on a BSP
or board fact the plan's letter had not foreseen (`poweroff` powers
this board off and a reset does not wake it; no `Environment size`
trailer; `nvme scan` before a load; `crc32` silent), each fixed with a
dry-run case; the seventh passed end to end at
`build/mvp/k3-sessions/20261030-characterize-7/`: the records equal (V
empty), the copy test exact, `fsuuid` = `blkid`, `/reserved-memory`
outside every extent, and one typed boot of `probe-platform` from the
partition with the MD5 witness, the shim on hart 0, and the cold-boot
facts equal to M0's. Nothing was saved.

**M5-6, the board session (`20261030-com260-rc2`, 07:52 to 08:18
UTC).** Open item 81: the preflight before, the staging of the 14
images (byte-identical to release candidate 1's), Fedora's clean
`systemctl reboot`, two `printenv` records at fresh prompts (identical,
SHA-256 `72443954…`), the install with the responsible human present
(`saveenv OK`), 13 selects, 20 runs from system reset each its own
`k3ctl` reset with Fedora down (every capture PASS in `uboot` mode with
its five attribution conditions and its banner audit; the counts equal
to M0's, M1-B's, and M2-A's; the five negatives failing as declared),
the restore with the human present, the fresh-prompt record equal to
record 1 byte for byte, Fedora's autoboot, and the preflight after equal
to the one before. One stop in the middle: the fourth select's `s` was
lost twice (stop condition 12; two unplanned boots recorded and not
counted); the console tool was hardened and the session resumed at its
fifth group (`0bfb1ca8`). 41 `k3ctl` resets, 41 banners, none
unexplained, no hand reset, no recovery.

**M5-5, the gates at `X2` (09:09 to 09:23 UTC).** From this worktree
clean at `6dd81ee3` on `l1`, the seven gates in order: `BE_MVP_LOCK:
PASS roles=32 host_only_skipped=0 closure=259 lock_sha256=2f1b732dcf24`;
`BE_MVP_CHECK: PASS` (the bundle `files=356 images=253 qemu_attempts=77
rehearsals=7`); `BE_MVP_EVALUATE: PASS` with `BE_MVP_IMAGE_IDENTITY:
PASS images=253 same=253 differing=0`; `BE_MVP_UBOOT_REHEARSAL: PASS
cases=7 attempts=7 refused=0 uboot=d96d1c22c67b opensbi=78f14d30c951
qemu=10.2.2`; `BE_MVP_KERNEL_REPRO: PASS outputs=15 identical`;
`Beryllium Architecture Model 0.2 evidence: PASS`; `BE_EVALUATION: Model
0.2 rootless evidence PASS`. Then `./mvp/mvp rc-record` made
`results/20261030-rc2/` (430 files; `BE_MVP_RC_RECORD: PASS …
commit=6dd81ee3…`), and `board-evidence`, from the same clean tree, made
`results/20261030-com260-rc2/` (198 files; `BE_MVP_EVIDENCE: PASS board
… runs=20 pass=20 fail=0 refused=0 stop=0`; `source_tree=clean`); both
verify. Three earlier gates attempts are history, not evidence (the
evidence record names them): the last passed every gate at `44233488`
but `rc-record` refused its record because the self-test case added
there printed two ssh-looking forms into the evaluator's retained log
(reworded at `6dd81ee3`, which moved `X2`).

**M5-7, the ledger and the records (`R2`).** The release-candidate
commit `R2` adds, over `X2`, the two records, the ledger's rows (C-10
updated to the boot path as run, with `md5sum`, `nvme scan`, and the
board record among its evidence; C-35 to C-39 for the gates, the image
identity, the twenty runs, the environment's install and restore, and
the resets; `candidate_tree_commit` = `X2`), the rendered table, the
evidence record, and this entry; `claim-ledger.py check` passes at `R2`
(`checks=9 claims=39 boundary=12`). The result review packet
`planning/mvp-m5-result-review-summary.md` follows `R2` as decision
support and names it.

### Debt sweep 1 (2026-10-30)

On the responsible human's `approve 1, 3` to the suggested next steps
after release candidate 2's acceptance (`accept 3867c66c`): the push of
`beryllium/mvp-m5` and `beryllium/mvp-m5-plan` to the private `origin`
with the development branch fast-forwarded (step 1, recorded in
`planning/HANDOFF.md`), and this sweep of open items 83 and 85 (step 3)
on branch `beryllium/mvp-debt-1` from that tip. Two board-tool lines
and their dry-run cases: `tools/k3-run.sh` records `board_kernel=none
(boot from system reset)`, so B0's run summary names the absent host
kernel instead of `?`; `tools/k3-stage.sh` joins the staged names with
`paste -sd ' '`, so the staging record ends no line in a space. No
monitor source, scenario, record, checker rule, or lock role changes;
the retained records are untouched (a record is never overwritten).
Item 80 (the dongle's power tap) is the human's, by hand, and stays
open. The sweep's first `./mvp/mvp check` found that the acceptance
record had broken the ledger's pin of the M5 plan (item 86, fixed on
`beryllium/mvp-m5` at `466c29f4`, from which this branch continues).
`make -C mvp lint`, `run-tool-check`, and `./mvp/mvp check` pass on the
sweep's tree. **Exact commit
`80ef8a13110525d8e3f9dfb19f5818a8f2dfbe64` is responsible-human accepted as
of 2026-10-30** (instruction `proceed with push & accept 80ef8a13`); the
same instruction pushed the ledger fix `466c29f4` to `beryllium/mvp-m5`
and the development branch, and this record's commit, with the
development branch fast-forwarded to it, follows it to the private
`origin`. No release step, no kexec use.

### M6-2 (at `356150bb`, 2026-10-31)

Work package M6-2 of the accepted M6 plan (planning/mvp-m6-plan.md, D-1
to D-4 and D-7), on branch `beryllium/mvp-m6-a` from the acceptance
record `366c8af4`. The monitor's boot copies, validates, seals, and
derives each scenario's own configuration through the ported R1
mechanism, widened by 43 counted port rules (see
[How the port is made](#how-the-port-is-made)), in place of the fixed
thirteen-resource profile. `tools/policy-check.py`'s `core()` and
`tools/gen-scenario.py` write each scenario's inventory and proposal
(`mvp-config.c`: two-guests 14 resources and 2 authorities, te-poc 15 and
4, anchor 17 and 7), the authorities exactly the authority report's
grants (stop condition 11); hart 0 prints `BE_MVP:00 BOOT_VALIDATED` and
`BE_MVP:00 CONFIG_SEALED inventory=N authorities=N roots=2 harts=0,1,2
identity=X` in place of `BE_R3:01` to `:06`. The G-stage builder, its
re-walk, the pages' placement, the measurement, and the control loop take
the derived roots' records (new `src/mvp-core.c` and `src/mvp-core.h`),
which must equal the records the image links. `run_r1`, `run_r2`,
`r1-config.c`, `sv39x4.c`, `r5-guest.S`, the fixture roots and pages, and
hart 0's binding and `hgatp` publication are gone. The new
`src/mvp-monitor.lds` lays out the core's first `0x34000` bytes: code to
`0x1_0200_2d10` (GCC) or `0x1_0200_2f90` (Clang), below `0x1_0200_8000`;
data; hart 0's stack at `0x1_0201_0000`; the rest zero. Every MVP-owned
extent, the image's base and size, and the shim are unchanged. The
scenarios' `kexec_fdt` object is removed (Q3), which changes te-poc's and
anchor's configuration identities and anchor's measurement.

The checkers: `tests/check-image.py`'s core rules (the script's
`ASSERT`s, each section of the core in its extent, the configuration in
the input section; 99, 102, and 113 mutations); `tests/check-capture.py`'s
two prelude forms, exactly one, whole, before `BE_MVP:01`, with M1's and
M2's fixtures judged against the te-poc and anchor expectations at
`366c8af4` (`tests/fixtures/pre-m6/`), exactly as before, and twelve M6
QEMU fixtures (self-test 129 cases, 317 mutations); and the new
`tests/config-test.c`, the widened validator on every scenario's
configuration with GCC and Clang (36 scenarios, 139 assertions), among
them 29 single defects, each refused for its own class. At `356150bb`
`./mvp/mvp check` passes every stage but `claim-ledger-check`, whose one
finding is C-10's pin of `tests/check-capture.py`, and `uboot-rehearsal`
passes. The QEMU suite's 58 runs keep every scenario's records, denials,
and management counts; exits differ only in the guests' timing-bound SBI
calls (console reads, and `sbi-time`'s TIME calls), within the base
suite's own spread.

Lines by the plan's counting rule: 2,545 added (511 deleted) in C,
assembly, linker scripts, Python, shell, and Make; fixtures, JSON, and
Markdown excluded.

Decided here: `BE_MVP_ACCEPTED_IMAGE_BYTES` and `BE_MVP_KEXEC_FDT_*` stay
in `src/mvp-layout.h`, though D-4 and Q3 remove them, because the
unchanged board tool `tools/platform-probe.py`, its test, and the
capture checker's kexec mode for the retained records read them; nothing
else does. A domain's hart must be distinct and not the control hart, but
is not checked against the platform's count, so the hart-start variant's
hart 9 still fails at its start, as declared. The probe images seal
two-guests' configuration and print `roots=2 harts=0,1,2`. Of `r3.c` the
MVP uses the boot check and the platform helpers; its `be_r3_note_*`
sequence is unused. The board-tool dry run's pin of the probe image's MD5
(`tests/run-tool-dry-run.sh`) follows the image.

### M6-3 (at `acda84bc`, 2026-10-31)

Work package M6-3 of the accepted M6 plan (planning/mvp-m6-plan.md, D-5
and Q5), on branch `beryllium/mvp-m6-c` from `53c9ad8e`. Every privileged
effect the monitor's C performs is the executor's, the new
`src/mvp-executor.c` and `src/mvp-executor.h`: 28 functions, one per
effect, each calling one assembly helper or one accepted ported helper
(see [The monitor's layers](#the-monitors-layers-m6-3), with the layer
of every file and the totals). Hart 0's runtime, the domain harts', and
the probe module call it and perform none themselves; `be_mvp_fw_call`
moved there unchanged, and with it the effects M6-2 left in hart 0's
runtime: the accepted reset, the HSM starts, the IPIs, and the console.
The trap assembly, `src/mvp-platform.h`, and every accepted byte are
unchanged; the core's code ends where M6-2's did (`0x1_0200_2d10` GCC,
`0x1_0200_2f90` Clang), and the MVP region's text grows by `0xe0` to
`0x100` bytes (the region at most `0x9a88` of its `0x40000` bytes, Clang
`anchor`).

The image checker holds the seam in every image: no function in the MVP
region's text but the executor's names an assembly helper or an accepted
privileged helper; the install's one call site is the executor's, whose
caller is the domain hart's `be_mvp_hart_main` (and `be_mvp_probe_hgatp`
in `probe-platform`); the injection's is the executor's, whose caller is
the denial action; and each image's mutation test has one more case, a
time read outside the executor (100, 103, and 114 mutations). Outside the
executor, `src/mvp-platform.h`, and the assembly, a search for
`be_mvp_arch_`, `be_r3_arch_`, `be_r3_platform_`, `asm`, `csr`, and
`fence` finds comments, the per-domain CSR set's pure values and names
(`be_mvp_vcsr_*`, `vcsr`), the executor's fence functions at their call
sites (`be_mvp_exec_fence_*`), and the probe's two ordering-line formats
(`mode=unfenced`, `mode=fenced`); `src/mvp-probe.h` declares the VMID
probes' one assembly helper, as `src/mvp-platform.h` declares the
others.

Behavior is unchanged. `make -C mvp` `port-check`, `lint`, `host-test`
(every count as before, GCC = Clang), `target-check`, `reference-boot`,
`image-check`, `variants`, `probes`, `budgets`, `capture-check`,
`qemu-test`, `evidence-check`, `rc-record-check`, `run-tool-check`, and
`uboot-rehearsal` pass, and so does `./mvp/mvp check`. Three QEMU suites
at `53c9ad8e` and three at `acda84bc` (58 runs each, every one PASS)
agree, run by run, on every count that does not depend on timing: each
domain's `lines`, `dbcn_write`, `base`, `ipi`, `srst`, and `refused`;
`records` (two-guests 138, te-poc 146, anchor 174); te-poc's three
denials; anchor's management log, its pause and termination, and its
measurement; and each negative's FAIL class. The counts that follow the
guests' timing, the console reads, `sbi-time`'s TIME calls, and the exits
a domain made before it was paused or terminated, stay within the spread
the base and the retained records show (two-guests `exits=157`, the base
157 to 158; anchor's host 238 to 241 and its protected domain paused at
124 to 130, the retained records 238 to 248 and 124 to 132). The dry
run's pin of the probe image's MD5 follows the image.

`be_r3_arch_enter_management` stays linked (see the layers section). Lines
by the plan's counting rule: 686 added (212 deleted) in C, assembly,
linker scripts, Python, shell, and Make; Markdown excluded.

### M6-4, the model (2026-10-31): deferred with its reason

The M6 plan's D-6 adds the MVP core profile to the Rocq model only if the
generated instances' shape admits it additively (Q4). It does not:
`model/proof/Model.v` defines `frame` as a closed enumeration of the fixed
single-hart profile's eleven frames (`MonitorCodeFrame` to `SharedFrame`)
and `gpa` as two addresses (`PrivateGPA`, `SharedGPA`), and Model 0.2's
validation, sealing, and derivation proofs are stated over those types;
the MVP's inventory (twelve to seventeen resources, two 64 MiB windows,
up to three shared pages, three harts) is not an instance of them, and
making it one means generalizing the types under proved theorems, which
the plan's stop condition 4 forbids. M3's policy layer (`Policy.v`, the
generated `Instances.v`) is indexed by naturals and already holds the
te-poc and anchor policy instances, so the policy-level claims stand. The
profile is therefore validated by the ported C mechanism (the host tests
on both compilers, the image checker's binding of the linked configuration
to the authority report, the boot's fail-closed path, QEMU, and the board)
and not by the model; the ledger's new boundary item U-13 says so, and the
first verification plan's stage 1 (the project snapshot, section 8) is
where a generalized model belongs. No model structure, proof, or theorem
changes in M6; two of the model's test files follow the scenarios (open
item 88, below).

### M6-5, the release surfaces (2026-10-31)

The guide's section 1 names what hart 0 now does at boot; its section 3
excerpt shows `BE_MVP:00 BOOT_VALIDATED` and `CONFIG_SEALED` with their
explanation and says captures of images built before M6 show the `BE_R3`
prelude, which the checker also takes; its section 6 names the report's
`identity.core_identity`. The disclosure covers release candidate 3 and
M6's two implementation agents. The ledger gains C-40 (the boot validates,
seals, and derives the scenario's own configuration through the ported
accepted mechanism, with the generator's agreement with the authority
report), C-41 (the executor seam, enforced by the image checker), and
U-13 (the model takes no instance of the profile), and its C-10 cites the
capture checker at its M6 form. The claim's text and required limit are
unchanged, as the plan requires. The plan's Q3 says "open item 59
closes" with the `KEXEC_*` and `kexec_fdt` removal; that number is a
transcription error in the accepted plan (open item 87). The roadmap's
"MVP core profile" row and the status pages change with release
candidate 3's packet.

### M6-6, M6-7, and M6-8 (at `ebc49a88`, 2026-10-31)

The gates, the board campaign, and the records of release candidate 3,
all on `beryllium/mvp-m6`, in the plan's order. The evidence record
[`planning/mvp-m6-evidence.md`](../planning/mvp-m6-evidence.md) holds
the detail; this entry is the log.

**M6-6, the gates at `X3` (03:54 to 04:08 UTC).** The first run, at
the intended `X3` `4cc5c53a` (03:31 to 03:44 UTC), passed five gates
and failed `./be model-check` (open item 88); its logs are history
(`build/mvp/rc3-gates-attempt-1-4cc5c53a/`). From this worktree clean at
`ebc49a88` on `l1`, the seven gates in order: `BE_MVP_LOCK: PASS
roles=32 host_only_skipped=0 closure=259 lock_sha256=2f1b732dcf24`;
`BE_MVP_CHECK: PASS` (the bundle `files=320 images=253 qemu_attempts=70
rehearsals=7`; `BE_MVP_QEMU: PASS runs=58 attempts=70 refused=12`;
`BE_MVP_CAPTURE_SELF_TEST: PASS cases=129`, `BE_MVP_CAPTURE_MUTATIONS:
PASS mutations=317 rejected=317`; `BE_MVP_HOST: PASS config scenarios=36
assertions=139 gcc=clang` among the eight host suites); `BE_MVP_EVALUATE:
PASS` with `BE_MVP_IMAGE_IDENTITY: PASS images=253 same=253
differing=0`; `BE_MVP_UBOOT_REHEARSAL: PASS cases=7 attempts=7 refused=0
uboot=d96d1c22c67b opensbi=78f14d30c951 qemu=10.2.2`;
`BE_MVP_KERNEL_REPRO: PASS outputs=15 identical`; `Beryllium
Architecture Model 0.2 evidence: PASS` (`BE_MODEL_DIFFERENTIAL: PASS
instances=4 mutations=91 three_way=73 two_way=22 comparisons=241`;
`instances=generated`); `BE_EVALUATION: Model 0.2 rootless evidence
PASS`. Then `./mvp/mvp rc-record` made `results/20261031-rc3/` (394
files; `BE_MVP_RC_RECORD: PASS … commit=ebc49a88…`), which verifies.

**M6-7, the board session (`20261031-com260-rc3`, 04:12 to 04:38
UTC).** The responsible human confirmed the board free and theirs alone
until the restore, pre-confirmed the install on the recorded `bootcmd`'s
digest (`0404ae42737d`, release candidate 2's), and was present at the
install and the restore (`the k3 is yours to operate`). The preflight
before (04:12), the staging of the 14 images (`X3`'s, each 2,584,576
bytes; none equal to release candidate 2's, as M6 changed every image),
Fedora's clean `systemctl reboot`, two `printenv` records at fresh
prompts (identical to each other and to release candidate 2's records,
SHA-256 `72443954…`; V empty), the install (`saveenv OK`), 13 selects
each at the first attempt, 20 runs from system reset each its own
`k3ctl` reset with Fedora down (every capture PASS in `uboot` mode with
its five attribution conditions and its banner audit; the new prelude
`BE_MVP:00 BOOT_VALIDATED` and `CONFIG_SEALED` on the board in every
run; the counts equal to release candidate 2's, M0's, M1-B's, and
M2-A's; the five negatives failing as declared), the restore (04:36),
the fresh-prompt record equal to record 1 byte for byte, Fedora's
autoboot under the restored `bootcmd`, and the preflight after (04:38),
equal to the one before in every fact but the kernel (open item 90). No
stop, no lost `s`, no unplanned boot, no hand reset, no recovery: 39
`k3ctl` resets, 39 banners, none unexplained. Two tool facts of the
session: the console tool's check stopped once before anything was
typed, because the operator's tmux session had gained a second window
since release candidate 2 (open item 89), and the wrapper took a stray
install argument as a make goal after the install had passed (open item
91). `board-evidence` made `results/20261031-com260-rc3/` (197 files;
`BE_MVP_EVIDENCE: PASS board … runs=20 pass=20 fail=0 refused=0 stop=0`;
re-made once from the stored session so that `source_tree=clean`, the
first copy having been made with the untracked release-candidate record
in the tree); it verifies.

**M6-8, the ledger and the records (`RC3`).** The release-candidate
commit `RC3` adds, over `X3`, the two records, the ledger's rows (C-10
retitled to release candidate 3's board path, which is release candidate
2's unchanged, with the new board record among its evidence; C-35 to
C-39 marked history; C-42 to C-46 for the gates, the image identity,
the twenty runs, the environment's install and restore, and the resets;
`candidate_tree_commit` = `X3`), the rendered table, the evidence record,
`.gitattributes`' board-excerpt exemption widened to every release
candidate's board record, and this entry; `claim-ledger.py check`
passes at `RC3`. The result review packet
`planning/mvp-m6-result-review-summary.md` follows `RC3` as decision
support and names it.

### Debt sweep 2 (2026-10-31)

Open items 89 and 91, the two board-tool defects release candidate 3's
board session found, on branch `beryllium/mvp-debt-2` from `506d2fc3`,
the record of release candidate 3's acceptance. `tools/k3-console.sh`
finds picocom's pane in the tmux session itself: once per invocation it
lists every pane of every window of `K3_TMUX_SESSION` (`tmux list-panes
-s`), takes the one pane whose command is `picocom` and whose process, or
a child of it, holds `K3_SERIAL_LOG` open, and addresses every later tmux
command to that pane by its ID (`%N`), so a session with other windows,
whichever is active, needs no `session:window` target; no such pane, or
more than one, is stop 1 before anything is typed. `check` prints the
pane's ID, and each step that types records it in the keystroke log.
`K3_TMUX_SESSION` may still be given in the `session:window` form
release candidate 3's records cite (`k3-console-1:0`); it names the same
session, whose every pane is searched. The wrapper `mvp/mvp` refuses,
before make runs, an argument of a command that runs make that is not
`VAR=VALUE` for a variable the wrapper passes for that command, printing
the argument and the usage and exiting 2, so a stray word such as a file
name after `k3-env install` no longer becomes a make goal. The dry run's
fake tmux (`tests/fake-uboot.py`) answers `list-panes -s` and the
`session:window` form and refuses a `display` or `send-keys` addressed
to anything but picocom's pane by its ID; `console-check` gains a
second window running another command, the window form, a window that
does not exist, no pane that runs picocom, and two picocom panes writing
the log; the new `console-window` case records and types through a
session with a second window; and the new `wrapper-arguments` case runs a
copy of the wrapper beside a stand-in Makefile that records each goal. Run
against the tools as they were at `506d2fc3`, `console-check` and
`wrapper-arguments` fail, the second with item 91's `No rule to make
target 'be-mvp-probe-platform-gcc.img'`. No monitor source, scenario,
record, checker rule, lock role, or file the ledger pins changes
(`tools/k3-env.sh`, `tests/check-capture.py`, and
`tests/uboot-rehearsal.sh` are as they were); the retained records are
untouched. `make -C mvp lint`, `run-tool-check`, `claim-ledger.py
check`, and `./mvp/mvp check` pass on the sweep's tree.

### Snapshot support (2026-10-31)

On the responsible human's instruction of 2026-10-31 (`give me a clean
RC3 snapshot repo which I will put up until the main repo is ready.
create a new private repo for the current work, then we will delete &
create a new public repo with the same name`), on branch
`beryllium/rc3-snapshot-support` from `506d2fc3`, the record of release
candidate 3's acceptance. The release path (planning/mvp-plan.md,
"Release path") makes a public release a new clean repository populated
with reviewed material, its selection the human's, and
LLM_POLICY_ALIGNMENT.md forbids automation to select what migrates or to
populate a public repository without explicit authorization; the human
was not available to answer the selection form, so its defaults, which
this entry records as the selection of 2026-10-31, were taken: Helium
(`pathfinder/`, under its own publication gate), the AI operating
instructions and skills (`.github/`), and the internal session handoff
(`planning/HANDOFF.md`) excluded; everything else kept byte for byte;
the identifying strings of the development environment (the board's LAN
name and address, home paths, ssh targets; none a secret) kept, since the
records are manifest- and ledger-pinned, and counted in the snapshot's
README; the human pushes the snapshot (`which I will put up`). The
private repository for the current work was created as
`beryllium-project/beryllium-hypervisor-internal` and holds every branch
of the private `origin` at its SHA, the four tags, and the unpushed
`beryllium/mvp-m6`, `beryllium/mvp-m6-plan`, and `beryllium/mvp-debt-2`;
the local-only worker (`*-wip`), superseded (`r8-c-h0-pmr-081*`), dropped
(`kvm0-*`), and never-push (`r8-h0-pmr-080`) branches stay local, as the
standing rules say. A large push failed in transit twice (TLS, `bad
record mac`), so the history was pushed in steps of forty commits.

Two things make a fresh-history snapshot possible without touching a
pinned file. `tools/claim-ledger.py`'s commits check, which resolves
every cited `evidence_source_commit` and the release's commits with `git
cat-file`, would fail in a repository that has none of them; it now reads
`SNAPSHOT.txt` at the repository root (`schema=be-snapshot-v1`,
`source_repository`, a full `source_commit` that is not a commit of the
repository itself) and skips, saying `snapshot of <commit>: the cited
commits are the source repository's`, as it already skipped where git
finds no repository; a malformed marker, or one naming the repository's
own commit, is a finding, so the marker cannot silence the check in the
source repository. The self-test gains five marker cases in a scratch
repository of their own (`variants=7`), and in a snapshot skips its one
mutation that expects the commits check to fail, as it does where git
finds no repository. And `tools/snapshot.sh make
COMMIT OUT` makes the snapshot: `git archive`, the exclusions removed, the
marker written, `README.md` replaced by `tools/snapshot-readme.md` with
its fields filled (the source, the exclusions, the kept paths, a table of
the identifying strings counted over the snapshot, and a place for the
checks run in it), one commit on `main` by git's configured identity with
the disclosure trailer; `snapshot.sh self-test` covers it in
`tools-check` (`snapshot-check`; 22 cases since `update` was added, below).
In a snapshot itself, `make` and `update` refuse (snapshots are made from
the source repository) and the self-test says so and skips, so that
`./mvp/mvp check` runs whole in a snapshot. Nothing in the tool pushes.
The snapshot made for the human is recorded in a following entry, after
its checks ran.

### The RC3 snapshot (2026-10-31)

`tools/snapshot.sh make 5c693b88 <dir>` made the snapshot the responsible
human asked for, at `beryllium-hypervisor-rc3`, beside this checkout in the workspace
on the workstation (outside this repository), from `5c693b88`, the
snapshot-support commit above, whose tree is release candidate 3's
(`89ef04e9`) with the acceptance record's planning edits and the
snapshot support: one commit, `11705111e85a60b6c8ab761d23b595ceb7ac101c`
on `main`, 3,129 files, 38 MB, every file but `README.md` and
`SNAPSHOT.txt` the source commit's blob (`git ls-tree -r` compared);
`pathfinder/`, `.github/`, and `planning/HANDOFF.md` absent; the README
names the source, the exclusions, the kept paths, the identifying strings
counted (3 private addresses in 50 places, 2 board host names in 152, 9
home-path values in 35, the former identity in 31), and the checks run.
In the snapshot, on 2026-10-31 (07:52 to 08:35 UTC): `./mvp/mvp check`
PASS (`BE_MVP_QEMU: PASS runs=58`, the ledger `checks=8`, its commits
check skipped with the marker's reason, the snapshot tool's self-test
skipped); `./mvp/mvp evaluate` PASS with `images=253 same=253
differing=0`, the closure taken from this host's verified cache
(`MVP_RPM_CACHE`) because koji no longer served nine of its exact
packages at their signed paths; `make -C mvp uboot-build` then
`./mvp/mvp uboot-rehearsal` PASS (`cases=7 attempts=8 refused=1`);
`kernel-repro` PASS; `make -C model unit`, `run`, `report-check`,
`proof`, and `differential` PASS. Not run there: `./be model-check`,
`./be evaluate`, and the documentation source check, which read excluded
files; the README says so. No tracked file of the snapshot holds a
credential-shaped string. The snapshot is not pushed: the human said
they would put it up (`which I will put up`), after deleting the private
repository and creating a public one of the same name, which are their
acts, as LLM_POLICY_ALIGNMENT.md requires. The policy document's
sentence naming `beryllium-project/beryllium-hypervisor` as the private
repository, and its release boundary, are the human's to revise for a
review snapshot (open item 92).

### Debt sweep 2 and the snapshot support accepted (2026-10-31)

**Exact commits `7447cb92aad1a6348a4256d6f21b7e14b05a8a0d` (debt sweep 2,
`beryllium/mvp-debt-2`), `5c693b88ec869c9053e6045d3ddd4d84d198864a` (the
snapshot support), and `ee631263cd08cdd5500a1bb9980d85c94d1f5469` (the
snapshot's record; both `beryllium/rc3-snapshot-support`), each from the
release candidate 3 acceptance record `506d2fc3`, are responsible-human
accepted as of 2026-10-31** by the instruction `proceed with 7447cb92
5c693b88 ee631263`, given in reply to the report that named them as
proposed and not accepted and asked for a decision on them; `proceed
with` is read as that decision. The two lines are merged, each by a merge
commit that keeps its exact SHAs, on branch `beryllium/mvp-post-rc3` from
`506d2fc3` (`95ddf935`, then `8fbdfb06`); the merge's three text conflicts
(this log and the open items, where both lines appended; the roadmap's
status fields; HANDOFF's next action, where the later text quotes the
earlier) were resolved by hand, both sides kept in order. The instruction
named no push, merge into the development branch, tag, publication, or
release, so the development branch `beryllium/single-hart-runtime-r0`
stays at `cd9cfa5f` (the integration branch is the fast-forward target
when the human directs it), and the branches are pushed to the private
internal repository as the backup the human's instruction of the same
day created it for. `./mvp/mvp check`, `make -C mvp lint`, and the
documentation source check pass on the merged tree with the policy
recheck below.

### Policy recheck (2026-10-31)

On the responsible human's instruction `recheck any upstream LLM policies
and update as needed`, the partner matrix's one project, the Linux
kernel, was read at `36aad21d50d1` (v7.3-19809, 2026-10-30) against the
pinned `481ed5dd3ed7` (2026-07-16), from the local mirror after a fetch.
`Documentation/process/coding-assistants.rst` changed four times:
`816d9992d9ed` (2026-08-03) reduced the `Assisted-by` tag to `Assisted-by:
LLM`; `3d7c44f73765` (2026-08-04) added the procedure an assistant must
follow when finding and fixing bugs; `fdd100ee60a0` (2026-09-15) changed
pronouns; and `1e035297ffda` (2026-10-14, after the Maintainers Summit)
removed the `Assisted-by` sections from it, from
`submitting-patches.rst`, and from `checkpatch.pl`, the transparency
expected of contributors now being `generated-content.rst`'s (the tools,
the prompts or their summary, the affected portions, the testing, in the
cover letter and changelog), with the DCO and the submitter's
responsibility unchanged. `LLM_POLICY_ALIGNMENT.md` follows: the matrix's
revision, the binding requirements (the tag out, the bug-fixing procedure
and the transparency rule in, the disclosure example now a
`Signed-off-by` alone with the cover-letter form named), a "History of the
attribution rule", the internal repository's name, the review snapshot's
section, and the TODO's record of this recheck; `docs/ai-assistance.md`
section 6 says the same for the MVP's commits. The eight commits of
2026-07-16 to 18 that carry `Assisted-by: GitHub-Copilot-CLI:gpt-5.6-sol`
are history under the rule of their day. The accepted M4 plan's sentence
naming the tag's form, and the retained Helium `pathfinder/AUTHORS.md`,
are frozen accepted or retained text and are not edited (the current
Helium policy is `../helium-te-poc`'s). This repository's own trailers
(`Co-authored-by: Copilot`, `Copilot-Session`) are GitHub's convention,
not Linux's, and are unchanged.

### The snapshot tool's `update` (2026-10-31)

The responsible human published the snapshot made from `5c693b88`
(`beryllium-project/beryllium-hypervisor`, public, `main`, 08:54 UTC)
before the policy recheck above, so the public copy's
`LLM_POLICY_ALIGNMENT.md` and `docs/ai-assistance.md` still state the
Linux `Assisted-by` rule the kernel dropped on 2026-10-14. `tools/snapshot.sh
update COMMIT DIR` refreshes a published snapshot in place: DIR must be a
snapshot the tool made (its `SNAPSHOT.txt`, a clean tree on `main`);
every file but `.git` is replaced by what `make` would write for COMMIT
(`populate`, shared with `make`), and one more commit, by git's configured
identity with the disclosure trailer, names the former and the new
source, so the published repository's history is its snapshots and
nothing else. A refresh that changes nothing is refused, as is a
directory that is no snapshot or a snapshot with a dirty tree, and a
commit that git declines to make is a failure (`commit_snapshot` no
longer runs in a subshell, where the self-test's `||` had hidden it). The
README template's source row is now the commit's subject and a "What it
holds" row (release candidate 3 and the commits accepted after it on the
integration line) in place of a sentence fixed to one commit. The
self-test gains `same_blobs` (the snapshot's committed files are the
source commit's blobs, the exclusions and the two written files aside),
applied after `make` and after an `update` to `HEAD`'s parent, and the
two refusals, each in a subshell because `fail` exits: 22 cases. The
refreshed snapshot made for the human is recorded in a following entry,
after its checks ran.

### The refreshed RC3 snapshot (2026-10-31)

`tools/snapshot.sh update 3fe427b7 <dir>` refreshed the human's local
clone of the published snapshot (`beryllium-hypervisor-rc3`, beside this
checkout in the workspace; its `main` equal to the public repository's)
in place from `3fe427b7`, the `update` commit above, whose tree is the
integration line's (release candidate 3, debt sweep 2, the snapshot
support, the acceptance records, the policy recheck): one more commit,
`1ae5fd8c39e309ee6aa6c11ee066d81cde9c1749` on `main` over the published
`11705111`, every file but `README.md` and `SNAPSHOT.txt` the source
commit's blob (`git ls-tree -r` compared), the three exclusions absent,
16 files changed against the first snapshot. In it, on 2026-10-31 (09:15
to 09:58 UTC, one check at a time): `./mvp/mvp check` PASS
(`BE_MVP_QEMU: PASS runs=58`, the dry run PASS, the ledger `checks=8`
with its commits check skipped on the marker, the snapshot tool's
self-test skipped); `./mvp/mvp evaluate` PASS with `images=253 same=253
differing=0` (the closure from this host's verified cache); the U-Boot
rehearsal PASS (`cases=7 attempts=8 refused=1`); `kernel-repro` PASS; the
model's unit, run, report-check, proof, and differential targets PASS;
the README's table records them. It is not pushed: `git push origin main`
from that clone, a fast-forward of the public `main`, is the human's
act. The public copy as it stands (the first snapshot) states the Linux
`Assisted-by` rule the kernel has dropped; the refreshed one carries the
rechecked policy document and disclosure.

The first gate run at `3fe427b7` in this checkout failed the dry run's
`missed-s` case (`stop=12 a second missed s`) while the refreshed
snapshot's own `./mvp/mvp check` was running on the same machine; run
alone, the gate passes (`BE_MVP_RUN_TOOL_DRY_RUN: PASS`, `BE_MVP_CHECK:
PASS`), as it had at `da8e9e18`, and `3fe427b7` touches no board tool.
The case is timing-bound (open item 93).

### The `update` commits accepted; the development branch moved (2026-10-31)

**Exact commits `3fe427b77f8c52dfd40eeec2f468183a9b485b6b` (the snapshot
tool's `update`) and `77511d99336557677435af06902e8ec480269b38` (the
refreshed snapshot's record and open item 93), on
`beryllium/mvp-post-rc3`, are responsible-human accepted as of
2026-10-31** by the instruction `accept 3fe427b7 77511d99, ff dev and
push`, given in reply to the statement of the one decision left. The
same instruction directed the development branch
`beryllium/single-hart-runtime-r0` fast-forwarded from `cd9cfa5f` (the
project snapshot's Frama-C note, 2026-10-30) to the commit recording
this acceptance over `77511d99`, and pushed to the private `origin`
(`beryllium-project/beryllium-hypervisor-internal`), so the development
branch now holds release candidate 3 (`89ef04e9`) and its acceptance,
debt sweep 2, the snapshot support and its `update`, the policy recheck,
and these records. The human had pushed the refreshed snapshot
(`1ae5fd8c`) to the public repository's `main` before this. No tag,
publication, or release; the board untouched.

### Item 80, the dongle's power line (2026-10-31)

On `proceed with item 80`, a by-hand test outside the board tools, the
human present: with pins 5 and 6 unbridged, a software poweroff, then
`k3ctl power` at 300, 1000, 3000, 6000, and 12000 ms and one `k3ctl
reset`, each acknowledged and each waking nothing; the board was
powered on by the human's power cycle (no physical button is attached).
Item 80 closes: the dongle cannot power this board on from a software
poweroff; the 2026-10-30 power-on is attributed to the removal of the
pin 5/6 short. No tool, document rule, or record changes but this entry,
the item, and one sentence of the guide (section 4, `k3-env record`),
which now says the reset pulse and the dongle's power line do not boot a
powered-off board. The record is
`build/mvp/k3-sessions/20261031-power-test/record.txt` (outside the
tree; this entry carries its facts). The board is up and its saved
environment untouched. **Exact commit
`36a5ff0b4ca481094b0fdf63f2c8cb1932bd7cd8` is responsible-human accepted
as of 2026-10-31** (instruction `accept 36a5ff0b and ff dev`); the same
instruction fast-forwards the development branch to the commit recording
this, over it. Not pushed by that instruction; the push follows the
standing rule that each push has its own instruction, and the human's
`ff dev and push` of earlier today covered that fast-forward only.

### Debt sweep 3: the RC3 snapshot reviews (2026-11-01)

Two read-only Rhyolite reviews of the public review snapshot
(`beryllium-project/beryllium-hypervisor`, `main` `1ae5fd8c`, made from
`3fe427b7`) were consolidated by the responsible human into three
documents outside this repository (`rhyolite-output/repo-review/be-rc3/`:
a README, a comparison report, and agent feedback) naming **twelve
verified root causes, rows A to L**, none in the monitor's guest-facing
code (`src/`), all in the privileged board tooling, the release surfaces,
licensing, and reproducibility. Each row was re-verified at the
development tip `8b7559d2` before work began; all twelve were still
present. On 2026-11-01 the human answered five questions on the
remediation plan: the accepted B0/B6/B7 launchers are hardened in place
**and** gated (`harden_and_gate`, authorized as the accepted-tool fixes of
2026-10-07 were); the retained kexec make targets stay in the graphs but
refuse without an approval variable (`gate_variable`); the checked-in R8
executable leaves the snapshot's selection, its accepted bytes untouched
(`exclude_from_snapshot`); reproducibility is deferred to the
clean-repository migration, with the snapshot README made explicit and
the lock refreshed from the host (`defer_to_migration`); and tier 1 (rows
A, D, E, G, H) ran first (`tier1_now`), tier 2 absorbing the rows of the
Claude CLI and Codex CLI reviews the human is still waiting for. The
work is a debt sweep on branch `beryllium/rc3-review-remediation` from
`8b7559d2`: one commit per row (or pair), each with a negative test built
to misbehave; no monitor behaviour, claim statement, accepted plan text,
or accepted R-series byte changes; no board command, no kexec anywhere
(the 2026-10-29 rule; every launcher test runs on the host or the fake
board), no push, no snapshot refresh. The packet is
`planning/rc3-review-remediation-review-summary.md`; the human decides.

- **Rows A and D, the retained kexec launchers (`e728b27e`).**
  `bringup/k3-b{0,6,7}/scripts/k3-run.sh` ran the remote loader as
  `sudo -n python3 <path>`, so a `ctypes.py` (or any module) planted in
  the loader's remote directory would have been imported as root, and
  built the remote command strings by word-splitting with the image's
  basename inside. Every call site now runs `python3 -I` (no script
  directory on `sys.path`, no `PYTHON*` environment, no user site), the
  remote image has a fixed name (`/tmp/be-k3-bN-image.img`), and every
  remote string is built by one `remote_command()` (`printf '%q'` per
  word); the launchers, their campaign twins, and every kexec-using make
  target (`k3-load-check`, `k3-run`, `k3-campaign`, `kexec-rehearsal`,
  B0's `fedora-rehearsal`) refuse before any board contact unless
  `BE_KEXEC_APPROVED=<the human's instruction>` is set, and record its
  value. Tests: `tests/test-kexec-load.py` (B0, B6, B7) runs the exact
  launcher form against a copied loader with a planted `ctypes.py` that
  writes a marker (absent under `-I`, present under the old form); the
  fake boards accept only the new form; the dry runs cover an
  unapproved run and a hostile image name. The B-series READMEs' kexec
  procedures are not edited (item 96).
- **Row E, the console tool's diagnostic filter (`ab1892a9`).**
  `tools/k3-console.sh`'s `diagnostic()` tested a line's first word
  against a blacklist with exemptions, so `md 0 1; run be_go` passed. It
  is now an anchored allowlist in `template()`'s shape: an alphabet, exact
  strings, and whole-line forms for the read-only commands the
  characterization typed (`help`, `version`, `bdinfo`, `printenv`, `md`,
  `nvme info|scan|detail`, `part list`, `fsuuid`, `ls`, `size`, `fdt
  addr|print|list`, `echo`, `md5sum`, `crc32` with exactly two arguments,
  the `test` forms); `K3_DIAGNOSTICS=human-authorized` and the 120-byte
  bound stay. The dry run's `diagnostic` case types 35 accepted lines and
  refuses 39 (metacharacters, `run`, `mw`, `nvme write`, a third `crc32`
  address, 121 bytes, unauthorized and misauthorized), none reaching the
  fake tmux.
- **Row G, the snapshot tool's `update` (`3c143857`).** `snapshot.sh
  update` deleted the destination's files before it verified the commit
  or that the destination was a snapshot. `verify_source()` now runs in
  `populate` and before the deletion loop; the self-test shows a bad
  commit and an `update` from inside a snapshot leave the destination
  byte-identical (26 cases, then 30 after row H). The in-snapshot case
  copies this very script into a scratch snapshot and committed it
  unconditionally, which passed only while the script had uncommitted
  edits; the sweep's first clean-tree gate run caught it (nothing to
  commit), and the copy is now committed only when it differs. The
  gates were run from a linked worktree, and inside the clean evaluator,
  which mounts the tree without its gitdir, the self-test failed where
  the ledger's commit check skips; it now skips there too, saying so (a
  repository that is present is never skipped).
- **Row H, one release-candidate truth (`306bf666`).** The ledger's
  `release` object had no name and a `null` commit while `claim.md`,
  `guide.md`, `ai-assistance.md`, and the snapshot README named the
  candidate each in its own words, and `claim.md` and `guide.md` said
  every board run so far was a kexec launch. The ledger names release
  candidate 3 at `89ef04e9`; each surface carries that name and short SHA
  in its self-description, says which records were kexec launches (M0 to
  M2, RC1, historical) and which boots from system reset (RC2, RC3); the
  snapshot README takes the name, commit, and commit count from the
  ledger and `git rev-list`; `claim-ledger.py check` gains "release
  surfaces" (whitespace-collapsed text; three self-test mutations), so
  the surfaces cannot drift again (`checks=10`).
- **Row B, the staging tool writes only its partition (`92d14404`).**
  `tools/k3-stage.sh` mounted the first device with `LABEL=beryllium` and
  copied with `cp`, which follows a destination symlink. It binds to the
  partition's UUID (`K3_PARTITION_UUID`, or the newest preflight record's
  stored UUID), checks the label and type as cross-checks, mounts with
  `nosymfollow` where the kernel accepts it (probed, recorded), refuses
  any non-regular entry on the partition before writing, copies with
  `--remove-destination`, and records the UUID's SHA-256 and the mount
  options; the fake board gained the UUID, label, and `nosymfollow`
  settings and five cases.
- **Row C, the partition tool's backups (`7ec20021`).**
  `tools/k3-make-partition.sh` checked that `--backup-dir` was a writable
  empty directory and then wrote its records with plain redirections and
  `dd`. Precondition 11 now admits only a directory the caller owns,
  writable by neither group nor others, not a symbolic link, every
  directory above it root's or the caller's and not group- or
  other-writable unless sticky (sshd's StrictModes rule), still empty and
  off the source partition; every record is created exclusively (`excl`,
  a subshell with noclobber; `dd conv=excl`); the comments say what
  noclobber does not refuse (a link to a device or a fifo) and why the
  ownership rule is the control. The fake `dd` honours `conv=excl` and
  gains a `plant` hook; the self-test grows from 22 to 29 cases, the two
  race cases planting a link after the first GPT copy and stopping the
  tool in step 1 with the victim untouched; removing either exclusive
  write fails its case.
- **Row F, the generator's variant names (`13c7456c`, pin `9e6cdc3e`).**
  `tools/gen-scenario.py` held the scenario's name to a grammar and took
  variant and probe names as given into `expect/<name>.json`. Every
  variant name now meets the scenario's grammar with an interior dot
  allowed (M0's accepted `two-guests` has the variant `sbi-3.0`, a
  departure from the plan's literal grammar, recorded in the packet),
  every probe name `probe-` and letters, no variant or probe may be named
  like the scenario or another image, and the writer requires every
  expect path to resolve inside `expect/`. The three self-tests gain the
  refusals (46, 45, and 57 cases); the generated outputs are unchanged.
  C-40 pins the file, so its entry was refreshed in a second commit, as
  debt sweep 1 did for C-10 (item 97).
- **Row I, C-05's boundary (`2deabaeb`).** The ledger's C-05 said no hart
  writes `hgatp` after the boot barrier; the barrier (`BE_MVP:07`)
  precedes the domain harts' installs (`src/mvp-hartmain.c`). The row
  now states the boundary the code has (one install per hart at its
  entry after observing the published generation word; the install
  function's two call sites; no `hgatp` write after `BE_MVP:08` to `:10`);
  the evidence is unchanged; the accepted M0 plan's sentence is an
  erratum (item 94), the plan not edited.
- **Row L, licences (`5930a67c`).** `guest/mgmt/be-mgmt.c` is
  GPL-2.0-only with no text in `LICENSES/` and no root licence file.
  `LICENSES/GPL-2.0-only` is the Linux kernel's text at the pinned guest
  kernel (`8d3ae592`, SHA-256 `8780e78a…`); root `COPYING` says which file
  is under which licence; the root README and the snapshot README say the
  same; `tools/check-licenses.py` (in `make -C mvp lint`, so in `check`)
  requires a text under `LICENSES/` and a line in `COPYING` for every
  identifier a tracked file's header names, and no unused text. Its
  first gate run caught its own defect (`da9dc9a5` → the fix): once
  `COPYING` was tracked, a sentence of it naming the tag was read as a
  header and its words as identifiers; a header line is now the tag and
  an expression and nothing else but a comment opener and closer (Rocq's
  `(* *)` included) and every token must be an SPDX identifier, and
  `COPYING` names the identifiers without the tag (10 self-test cases;
  `identifiers=2 files=857 texts=2`).
- **Row K, the R8 executable (`f7e58b04`).** `tests/r8/run-make.sh` is a
  checked-in stripped x86-64 ELF; `tests/r8` joins the snapshot's
  exclusions (the human's `exclude_from_snapshot`), `same_blobs` now
  handles an excluded directory below the top level, and the self-test
  asserts the snapshot holds no ELF object (30 cases). The accepted R8
  bytes are unchanged.
- **Row J, reproducibility (`a3d295c8`).** The snapshot README gains "How
  to run the checks": `./mvp/mvp check` and `evaluate` are the entry
  points; the root `Makefile` and `be` are the internal repository's and
  not usable in the snapshot; `evaluate` needs a verified cache of the
  closure's exact RPMs where Fedora no longer serves a build. The lock
  was refreshed from this host and did not move (`changed_keys=0`,
  `closure_added=0`, `closure_removed=0`): the closure is the installed
  set. Measured 2026-11-01: 38 of the 259 closure NEVRAs are no longer in
  Fedora 44's `fedora` and `updates` repositories (`dnf repoquery
  --available` over the closure) and 25 of those are absent from koji's
  signed paths too (one HEAD request each; gcc `16.2.1-2`, libstdc++,
  util-linux `2.41.5-1`, qemu `10.2.2-1`, openssl-libs `3.5.9-1`, xz
  `5.8.2-2` among them), up from the nine the 2026-10-31 record named.
  No root `Makefile` or `be` change (the R1 pin; MVP plan D3). The
  remedies are the human's (item 95).
- **The rules behind the defects.** `.github/copilot-instructions.md`
  gains a "Privileged tooling standard": privileged host tooling gets the
  monitor's input discipline (isolated interpreters, exclusive writes,
  devices by UUID, quoted remote arguments, a negative test per rule);
  safety filters are whole-line anchored allowlists; a retired
  mechanism's live targets are gated or removed when the policy changes;
  release surfaces are checked from one source of truth and "every X so
  far" names its bound; temporal claims name their marker; a grammar
  written for one field applies to its siblings; all validation precedes
  the first destructive step.

Gates at the candidate, from a clean checkout, are in the packet. **Exact
commit `3b7ab0e3e43bdad48772c0ae5eb8d831f218c29f` is responsible-human
accepted as debt sweep 3 as of 2026-11-01** (instruction `accept
3b7ab0e3, fast fwd, push, use your best judgement`); the
[review and acceptance record](../planning/rc3-review-remediation-review-summary.md)
holds the decision. The same instruction fast-forwards the development
branch `beryllium/single-hart-runtime-r0` from `8b7559d2` to the commit
recording this and pushes it and `beryllium/rc3-review-remediation` to
the private `origin`; `use your best judgement` was read as also
refreshing the human's local clone of the public review snapshot
(`beryllium-hypervisor-rc3`, beside this checkout) from the accepted
content with `tools/snapshot.sh update`, the gates run in it and its
record following, the push of the public `main` staying the human's.
Items 94 to 97 stay open; item 98 is corrected and closed (above).

### The RC3 snapshot refreshed from the acceptance record (2026-11-01)

Under `use your best judgement` in the acceptance of debt sweep 3,
`tools/snapshot.sh update b53c02a8 <dir>` refreshed the human's local
clone of the published snapshot (`beryllium-hypervisor-rc3`, beside this
checkout) in place from the acceptance record: one more commit,
`3b6d76da01f062fe5fc894e42427e5c9e5c079f3` on `main` over the published
`1ae5fd8c`, every file but `README.md` and `SNAPSHOT.txt` the source
commit's blob (`git ls-tree -r` compared), the four exclusions absent
(`tests/r8` newly among them), no ELF object in the tree. In it, on
2026-11-01 (15:37 to 15:53 UTC, one check at a time, B1's pinned OpenSBI
build given from this checkout because the snapshot's fresh `build/`
would otherwise fetch it): `./mvp/mvp check` PASS (`BE_MVP_QEMU: PASS
runs=58 attempts=72 refused=14`; `BE_MVP_LICENSES: PASS identifiers=2
files=779 texts=2 source=git`; the ledger `checks=9` with its commits
check skipped on the marker; the snapshot tool's self-test skipped, this
being a snapshot of `b53c02a8`); `./mvp/mvp evaluate` PASS with
`images=253 same=253 differing=0`, run twice: the first attempt, with no
cache seeded, fetched 240 packages from Fedora's repositories and 3 from
koji and stopped at `16 closure packages are in no source` (item 95's
figures); the second took those 16 from this host's verified cache in
`MVP_RPM_CACHE` (an environment variable, which the wrapper's `VAR=VALUE`
form did not set for `evaluate`; fixed in debt sweep 4, below). The U-Boot
rehearsal, `kernel-repro`, and the model's targets were not re-run in
this refresh: their inputs are unchanged since the refresh of 2026-10-31,
whose README records them, and the new README says so. The snapshot
commit's trailer carried the tool's hard-coded session id and was
corrected by hand (item 105). It was not pushed, and debt sweep 4's
refresh (below) supersedes it in the clone. This record was first
written on the S3-C planning branch (`beryllium/mvp-s3c-plan`,
`d5de5a08`), where the three independent S3-C design reviews were
processed the same day and items 99 to 105 were first registered; the
integration line carries both here.

### Plan revision S3-C: the three independent reviews, and the second candidate (2026-11-01)

The three independent design reviews of S3-C's first candidate
`95c9ab24` (the Copilot CLI session's own; a Codex CLI session's, which
had written `planning/mvp-plan-s3c-independent-design-review.md` into the
main checkout on 2026-10-31; a Claude Code session's, with a 107-entry
register and probes outside the tree) were processed on the human's
direction `also now process the claude cli and codex reviews and iterate
as appropriate`: the development tip `b53c02a8` was merged into
`beryllium/mvp-s3c-plan` so that the second candidate is written against
the accepted state (`6cce40fd`); the reports joined the tree unedited but
for a provenance comment with
`planning/mvp-plan-s3c-review-reconciliation.md` (43 rows A to AQ, the
facts re-read in the tree, six adjudications, a false-clearance check,
the findings outside S3-C with their status) and open items 99 to 104
(`81c5e0b6`); and the **second candidate, exact commit
`27d2e557f069edf8dd714f5ac9b5ccb9b204a801`**, rewrote the revision's text
against the rows (`planning/mvp-plan.md`, lines 1142 to the end; the
accepted body is byte-identical). The packet
`planning/mvp-plan-s3c-review-summary.md` presents it. Two findings the
reviews made against `95c9ab24`'s tree, the claim's stale header and the
snapshot template's hard-coded candidate, were already fixed by debt
sweep 3. **Exact commit `27d2e557f069edf8dd714f5ac9b5ccb9b204a801` is
responsible-human accepted as Plan revision S3-C as of 2026-11-01**
(instruction `accept 27d2e557, defaults ff + push`, Q27 to Q46 at their
defaults), after debt sweeps 4 and 5 (below) had been accepted on the
development branch and the development tip `44112dec` merged into the
S3-C branch (`b6e323bd`); the
[review and acceptance record](../planning/mvp-plan-s3c-review-summary.md)
holds the decision, which authorizes writing the bounded plans of M7, M8,
and M9 and M10's after their results, and nothing else. The development
branch is fast-forwarded to the commit recording the decision and pushed.

### The M7 plan proposed (2026-11-01)

On `go` after S3-C's acceptance, `planning/mvp-m7-plan.md` (exact commit
`4f4d094e`, branch `beryllium/mvp-m7-plan` from `f5dc770b`) bounds
milestone M7, interactive guests, within S3-C.3's shape and defaults; the
facts it rests on were read in this tree (the block's 12 KiB unused
region, the ring API and its fail-closed rule, hart 0's wakes, the
domain hart's four inbound-read points, the write path's window rule,
the guest's configuration and initramfs, the `hvc` driver's back-off,
the typing tools, the checker's matching, `Binding.v`'s closed types,
and the locked cross GCC's `lib64/lp64` multilib, which the soft-float
userland needs). Its packet is `planning/mvp-m7-plan-review-summary.md`.
**Exact commit `4f4d094efb3985435673f7bda62f35ad51c6165e` is
responsible-human accepted as the M7 plan as of 2026-11-01** (instruction
`accept 4f4d094e`; Q1 to Q16 at their defaults); the
[review and acceptance record](../planning/mvp-m7-plan-review-summary.md)
holds the decision. M7-2 to M7-6 are authorized on `beryllium/mvp-m7`
from the acceptance-record commit and start the same day; no fast-forward
or push was directed.

### M7 implementation: M7-2 to M7-6 (2026-11-01 to 02)

On branch `beryllium/mvp-m7` from the plan's acceptance record
`ae3e9537`, under the accepted M7 plan's defaults and stops, coded by
`claude-opus-5.5` sub-agents in worktrees and reviewed line by line by
the session model before each merge (the standing split). The COM260 was
released for M7's board step on 2026-11-01 (`proceed, K3 board is
yours`), and the board step ran on 2026-11-02 with the human present
(below). Security model v1 **Revision 2**, the
console path (Part 1: I17, I18, the operator and the typing tool as
trusted inputs, three TCB rows), was written first as its own exact
commit and is **accepted at `afd395b8`** (`accept afd395b8`; record
`f640275b`).

- **M7-2, the userland** (`7db37366`, merged `ca26940e`; pins `a00e14f7`):
  BusyBox 1.36.1 and musl 1.2.6, two external inputs pinned by tag,
  commit, tarball SHA-256, and the maintainer's signature (the keys under
  `guest/keys/`), fetched over HTTPS once into `build/mvp/guest/dist/` and
  verified on every build with `gpgv` against a one-key keyring whose
  primary fingerprint `VALIDSIG` must name; musl built for
  `rv64imac`/`lp64` (soft float; `configured for riscv64-sf`), BusyBox
  static against it from the in-tree `guest/busybox.config` (`sh` and
  twelve applets; the applet table must equal the initramfs's `/bin`
  links; none of musl's advisory functions `regcomp`, `regexec`,
  `iconv`, `iconv_open` linked, for CVE-2026-107891 and CVE-2026-6042),
  byte-reproducible (`ar`/`ranlib` `D`, `SOURCE_DATE_EPOCH`,
  `KCONFIG_NOTIMESTAMP`; `kernel-repro` now 23 outputs). The Image grows
  from 1,899,716 to 2,063,556 bytes within the plan's `0x300000` budget
  (`guest-pins.py` enforces it); `busybox` 141,560 bytes, the init 17,176.
  `/dev/hvc0`, `/dev/null`, `/bin/*`, `/init-shell`, and the verb links join
  the initramfs. `mvp-init.c`'s `/init-shell` forks `sh` on `hvc0` as its
  controlling tty with `BE_ARGS` carrying the `be.*` arguments; the verbs
  `be-chan write|read`, `be-deny load-unmapped|store-shared` (the handled-
  fault child; never BusyBox `devmem`), and `be-anchor request N` reuse
  M1's and M2's code; `RESULT pass` requires the shell's exit 0. No kernel
  configuration change was needed. `LICENSES/MIT` and `COPYING`'s
  external-input paragraph; the licence check counts `external=2`. A smoke
  test without the monitor (`make -C mvp guest-shell-smoke`, QEMU with the
  firmware's own console: 3 boots, 17 steps) passed. Departures: 1.36.1 is
  busybox.net's latest *stable* (1.37.0 and 1.38.0 are marked unstable);
  the lock rejects new keys, so the pins live in `pins.txt` only;
  `evaluate.sh` copies the host's verified tarballs into the hidden tree
  (the evaluator has no network; the build re-verifies them);
  `-fno-link-libatomic` for GCC 16's driver; `waitpid(-1)` since nolibc
  lacks `wait4`.
- **M7-3, the monitor's input path** (`ba7d0f33`, merged `1d5e3a6e`; pins
  `165d4c4d`): `BE_MVP_INPUT_RING_OFFSET 0xd000`, `BE_MVP_INPUT_RING_BYTES
  0x1000` (the unused tail now `0xe000`/`0x2000`), record type
  `BE_MVP_RECORD_INPUT 16` in its own type set, a full ring dropping and
  counting instead of failing (deliverable 5 superseded for this ring
  alone); `src/mvp-input.c`'s pure three-state parser (the `~` at line
  start **held**, a fourth output the plan's three did not name, so that
  read = delivered + dropped + held + selected); hart 0's poll after each
  drain through a new executor read (`BE_MVP_FW_DBCN_READ`), at most 256
  bytes a wake, the timer re-armed through the one `stimecmp` writer to the
  earlier of `BE_MVP_INPUT_POLL_TICKS 0x40000` and the budget's end; the
  served DBCN read for a granted domain (a2, then the whole range through
  `be_mvp_gstage_translate`, before any byte moves) through a 256-byte
  stage in the state page (the hart page 2,176 of 4,096 bytes); the flush
  of a paused or terminated domain's partial line; `console_input` from
  `scenario.json` through `mvp-config.c`, the ported R1 request, binding,
  and derived root (counted port rules) into each hart's state page, read
  from the sealed roots alone; `BE_MVP:15` to `:18`; `BE_MVP_SBI_IMPL_VERSION`
  5 and 6 (the one declared-line change to the accepted scenarios); the
  served-read counter `dbcn_input` (SHUTDOWN word 14). Host tests: `input`
  17 scenarios, 5,188 assertions (the parser over every byte in every
  state against a separate oracle, the write-authority refusals consuming
  nothing, the ring's drop rule, the routing and accounting, the re-arm);
  `sbi`, `hart`, `ring`, and `config` extended; GCC = Clang. The MVP
  region's use rose about 4.6 KiB (`0x9a88` to `0xada0`, Clang `anchor`).
  Every accepted scenario's QEMU records and denial counts are unchanged
  (exits vary only in the guests' timing-dependent DBCN-read polls). A
  granting image hand-typed into in QEMU showed every line and drop
  reason as specified. Departures: the scenario schema versions are not
  bumped (the accepted `model/tools/gen-policy-fixtures.mjs` admits only
  the v2 and v3 strings; `console_input` is a required field of all
  three); `policy-check.py`'s manifest hash leaves `console_input` out so
  that `te-poc`'s and `anchor`'s printed identities and `anchor`'s
  measurement are unchanged, and the printed `CONFIG_SEALED` identity does
  not cover the grant either (the sealed canonical R1 identity does):
  item 108; `BE_MVP:16` prints on every valid selection, a re-selection
  included, for the typist's lockstep; a firmware read error ends the run
  as `FAIL console` in granting images.
- **M7-4, the harness** (`4c44d244` to `e357711e`, merged `672adff6`; pins
  `77783693`): the M7 fixtures regenerated from the merged tree (M2's pins
  kept as `tests/fixtures/m2-guest-pins.txt` for the older captures); each
  scenario's **shell image** `<scenario>-shell` (`rdinit=/init-shell`;
  `anchor`'s protected domain keeps its role and no grant) with its own
  expectation; the **sessions** `scenarios/*/sessions/shell.json`
  (`be-mvp-session-v1`: `focus`, `send`, `expect`, `negative` steps; `NONCE`
  the run nonce): `two-guests` the nonce in each domain and `ls /bin | wc
  -l` (18), the `bad-sequence` and `literal` negatives; `te-poc` the
  `before-focus` negative, the writer's channel write carrying the nonce
  and its denied load at `0x84001000`, the reader's read-back and its
  denied store at `0x84000ff8` and load at `0x90000000`; `anchor` request
  7 answered by the protected domain's role, the host's denied store at
  `0x84001ff8` and load at `0x84002000`, the `no-grant` negative (`~1`),
  then the protected domain paused and terminated through two new verbs
  `be-anchor pause|terminate` (M2's management path; beyond D-9's verb
  list, needed for the run to end); the **QEMU typist**
  `tests/session-typist.py` (a stdio chardev whose own log is the capture;
  one key per 10 ms after 0.5 s of quiet; a 16-hex-digit nonce from
  `os.urandom`; lockstep on the `BE_MVP:16` and echo lines; `typed.txt`,
  `nonce.txt`, `session.txt`; refused domain-hart boots repeated as M0-A.2);
  the **hostile variant** (`/init-hostile`: every byte value, a forged
  `BE_MVP:13` line, a forged `BE_MVP_G1: ` prefix, `ESC[6n` and an OSC
  title, a 300-byte line; the checker rejects a bare forged line); the
  capture checker's console rules (the `:15` to `:18` lines; `:18`
  reconciled against the typed keys through the checker's own routing
  model, per-domain count and SHA-256; the drops the session provokes and
  no other; the nonce only in its focus period's domain; the channel text
  read back; the secret absent raw and in hex; `:15` to `:18` absent from
  non-granting images): `cases=160`, `mutations=395 rejected=395`; the
  authority report's `configuration` section (`be-mvp-authority-report-v2`;
  identities unchanged); the session bound check against the ring's peak
  budget; `./mvp/mvp sessions` in `check` and `./mvp/mvp live` (the QEMU
  command lines for a human session; a demonstration, never evidence).
  **`BE_MVP_SESSIONS: PASS sessions=6 attempts=8 refused=2`**; a `te-poc`
  session: 22 steps, 193 keys, 7.8 s, `BE_MVP:18 INPUT read=193
  g0=86:… g1=83:… dropped=no-focus:18`; no byte reached a domain other
  than the announced focus (stop 6 did not fire). Departures: the images
  are named `<scenario>-shell` (image names must be unique across
  scenarios); `live` keeps the 2^32 budget (Q12's 2^35 would be a three-
  line monitor switch not made: item 110); `prefix=0x7e` in `:15`; the
  plan's D-11 gave `two-guests` a channel demonstration it cannot have
  (item 112); `anchor`'s 260-byte command line is split at 256 by the
  monitor, as the expectation models; the `ring-full` drop is not
  provokable in QEMU (item 113).
- **M7-5 so far**: `model/proof/InputRing.v` (`ad93667d`, merged
  `a2910c78`): 386 lines beside `Binding.v` unedited, four theorems (one
  writer per input-ring word; disjointness from the control rings, the
  ring's extent computed apart from every control ring, window, and shared
  page for `mvp_binding`; the drop rule conserves bytes and never overruns;
  routing to a granted, running focus), no axiom, four closed assumption
  reports, the standalone gate `model/tests/run-input-ring.sh` (`PASS
  theorems=4 assumptions_closed=4`), the accepted gate's counts 24 and 22
  unchanged; the accounting theorem was dropped to stay under Q10's 400
  lines, and the one-line `model/Makefile` hook is the human's (item 109).
  The claim's console sentences as the plan fixes them, ledger rows C-47 to
  C-49 and U-14, U-15 (`c0170f4c`), the guide's console section and inputs
  (`5ec00ee7`).
- **Gates on the merged branch at `77783693`** (2026-11-02, 02:08 to 02:16
  UTC, from a clean tree): `./mvp/mvp check` PASS on the second run
  (`BE_MVP_QEMU: PASS runs=60 attempts=75 refused=15`, `BE_MVP_SESSIONS:
  PASS sessions=6`, `BE_MVP_CAPTURE_SELF_TEST: PASS cases=160`,
  `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=395 rejected=395`,
  `BE_MVP_BUDGETS: PASS measured=38`, `BE_MVP_EVIDENCE: PASS … images=303
  session_attempts=8`, `BE_MVP_CLAIM_LEDGER: PASS checks=10`); the first run
  stopped at item 93's timing case under a load average of 7;
  `kernel-repro` PASS `outputs=23 identical`.
- **Stop condition 9 (the soft limit), returned to the human.** By the
  plan's counting rule M7 is at **7,625 of 8,000** added lines (C 3,340
  with the host tests, Python 3,633, shell 377, Make 198, other 35; the
  monitor 1,466 of them; Rocq 399 and the fixtures, JSON, Markdown, and
  `busybox.config` excluded). The remaining counted work of M7-5, the
  console tool's guest-typing mode with its dry-run cases and the
  `probe-console-input` image, is estimated at 400 to 600 lines and would
  end M7 near 8,100 to 8,300: the generator's session-to-expectation
  derivation and the report came to about 885 lines against an estimate of
  200 to 400, and the checker's reconciliation about 750. Under the
  human's direction a soft limit is re-evaluated, never cut; that code and
  the board characterization wait for the decision (item 111).
- **M7-5, the board tooling** (`0e696c2b` to `597ef669`, merged
  `ff6cff6c`; pins `0dcc2271`, C-10, C-40, C-41, and C-48 at `597ef669`):
  the probe image **`probe-console-input`** (probe 4; `src/mvp-probe.c`,
  `BE_MVP_PROBE_INPUT_TICKS` 2^29, 22 s on the board and 54 s in QEMU):
  hart 0 alone, after the stub's FINISH (domain 0's hart runs the VMID
  sequence without the switch and parks), prints `BE_MVP:PROBE
  console-input window_ticks=0x20000000 prefix=none`, polls the firmware
  read every `BE_MVP_INPUT_POLL_TICKS` on its own Sstc timer as M7's hart
  0 does, with no parser and no routing, 64 bytes a read and at most 256 a
  poll, a line `bytes=<count so far> hex=…` per 64 bytes and the rest at
  the window's end, then `total= polls= nonzero_polls= max_per_poll=
  errors= sha256=<16 hex>`, `BE_MVP:14`, and SRST; in QEMU `total=0
  polls=2030`; every other image byte-identical; the image checker's
  profile; the capture checker's rows (`cases=164`, `mutations=399`;
  direct mode requires `total=0`). The console tool's **`guest-type
  SESSION NONCE OUT`** and **`probe-type OUT`** (`tools/k3-console.sh`;
  each exit 5 without `K3_GUEST_TYPING=human-authorized`, as `diag` is
  without `K3_DIAGNOSTICS`; `template()`, `diagnostic()`, `type`, and
  `diag` unchanged), which type only into the MVP the session's last reset
  booted (`Starting kernel ...` after that reset's banner, then `BE_MVP:15`,
  `BE_MVP:16 FOCUS none`, and each granted domain's shell line or the
  probe's window line, within `K3_GUEST_READY_SECONDS` 120; never at
  U-Boot, stop 13), `guest-type` reading a `be-mvp-session-v1` file through
  `tools/k3-uboot.py session` (the generator's grammar and `session_plan()`;
  `NONCE` 16 hex digits; anything outside the grammar, a focus `BE_MVP:15`
  does not grant, or a byte the mode does not type is stop 13, nothing
  typed), in lockstep (a focus pair, then `BE_MVP:16 FOCUS g<d>`; a line
  and Enter after 0.5 s, the focused domain's echo within 10 s, the expect
  within 30 s; a negative's bytes then its `BE_MVP:17` line or the literal's
  echo); **`tools/k3-uboot.py gate`** before every piece (no SPL, U-Boot, or
  `Autoboot in` line since `Starting kernel ...`, the log's last line hart
  0's, and no terminal line yet: a banner is stop 10, S3-C's stop (b); a
  finished run is stop 13 before the first key, `597ef669`); keys one at a
  time to picocom's pane by its ID, CR as Enter, `K3_GUEST_KEY_DELAY` 0.01 s
  apart, each in `keys.log` (`guest-focus g<d>`, `guest-line N`, `probe-text
  rep=N`; `key=0xHH` per key) and `OUT/typed.txt` in the QEMU typist's form;
  never `s`, Ctrl-C, or C-a, no retry (a differing echo or a missing line is
  stop 6); `steps.txt`, `nonce.txt`, `session.txt`; no reset while a session
  types (`K3_RUN_ROOT/guest-typing.pid`; `reset` refuses). `probe-type`
  types Q14's 64 distinct printable bytes four times into the window, three
  at 10 ms per byte and the fourth at 1 ms, 0.5 s apart, each repetition
  gated. The **driver `tools/k3-input-characterize.sh PROBE_GROUP
  [SHELL_GROUP]`** (`./mvp/mvp k3-input-characterize`; refused without the
  authorization): the probe group's image selected, one run from reset
  through `tools/k3-run.sh` with `K3_GUEST_RUN=probe` (the typist started
  after the launch into the run's directory; `typist=` recorded), checked
  in `uboot` mode and attributed; then `tools/k3-uboot.py input-judge` into
  the run's `characterization.txt` (the class `supplies`, `absent`,
  `blocks`, `loses`, or `corrupts`; the counts; the received per
  repetition by greedy match; the measured pacing; the capture's and the
  keys' SHA-256); stop 10 (`BE_MVP_K3_INPUT: STOP stop=10`, exit 1) unless
  the first three repetitions' 192 bytes were received exactly, before the
  fourth began, with `errors=0`; the 1 ms repetition informational
  (`fast_pacing=lost N` still PASS); then, with `K3_INPUT_SESSION` and the
  shell group, the shell image selected and one run with
  `K3_GUEST_RUN=session` (a nonce from `/dev/urandom`), the capture checked
  with `--typed`, `--nonce`, and `--session`. `tools.mk`:
  `K3_INPUT_PROBE_GROUP`, `K3_INPUT_SHELL_GROUP`, the probe in the plan,
  `be-mvp-two-guests-shell-gcc.img` staged (no campaign group has it).
  `tools/evidence.py --board` judges a run of an image with console input
  with its keys, nonce, and the session file its expectation names (by the
  expectation's SHA-256; no path read from a record) and keeps each run's
  typing records; `tools/platform-record.py` accepts the probe's two
  values. The dry run (`tests/run-tool-dry-run.sh`, `tests/fake-uboot.py`:
  keys reaching the fake MVP are its input, a console variant's QEMU
  capture replayed a step at a time with the faults `garble_echo` and
  `banner_after_step`, the probe's capture playing the probe with the
  faults `input_probe` drop and `absent`; `DIR/faults.json` per boot):
  stage 16 images, 19 partition entries, selectors 15 groups, 21 runs; the
  `guest-type` case (refused at U-Boot's prompt, without the authorization,
  with a bad nonce, with a step outside the grammar; the two-guests session
  from a reset PASS with its 100 keys; a lost character stop 6 and no
  Ctrl-C; a banner after the first step stop 10; a session against a
  finished run stop 13) and the `input-characterize` case (refused without
  the authorization; four runs: all received PASS `class=supplies`, two
  bytes of the 1 ms repetition lost PASS `fast_pacing=lost 2`, one byte at
  10 ms lost stop 10 `loses`, none kept stop 10 `absent`; then the whole
  board flow: the characterization, the shell session with a fresh nonce,
  the restore, the preflight after, and the board record judging all six
  runs again). `BE_MVP_RUN_TOOL_DRY_RUN: PASS`; `./mvp/mvp check` PASS at
  `0dcc2271` (05:18 to 05:33 UTC; `BE_MVP_QEMU: PASS runs=62`,
  `BE_MVP_SESSIONS: PASS sessions=6`, `BE_MVP_EVIDENCE … files=367
  images=315`, `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=49 boundary=15`).
  Departures: the probe prints a line per 64 bytes, not each byte (D-12's
  letter); hart 0 alone polls while domain 0's hart runs the stub and
  parks; the driver selects the images itself (`k3-env select`, as the
  campaign tool does); `tests/uboot-rehearsal.sh` is not extended for probe
  4. The sub-agent that wrote this package was lost once to a runtime
  restart with nothing committed and was relaunched (commit early and
  often); the work is its second run's.
- **The board step (M7-6, 2026-11-02, 03:08 to 05:48 UTC; the record
  `results/20261102-com260-m7/`, 92 files, `058fee76`).** Under board
  policy item 8 and D-12, after the human's release (`proceed, K3 board is
  yours`) and confirmation of the recorded `bootcmd` (`confirm
  0404ae42737d`), the human present at the install and the restore, with
  the images of `0dcc2271`: the preflight before (PASS; Fedora on kernel
  `7.3.1-300.0…fc45`, which the saved `f45_rel` now names; `K3_SSH` must be
  in the environment, the Make controls refusing it on the command line;
  the former alias `k3e` no longer resolves); `k3-stage` PASS `images=16`
  (every image 2,748,416 bytes, from release candidate 3's 2,584,576: the
  userland); the console tool's `check` **stopped once** (its stop 1): the
  human had moved their checkout of the `k3ctl` client to v1.1 (`89f5c717`,
  04:39 UTC) during the session, so its SHA-256 `9c11b4f8…` differed from
  the pin `7ca3d78a…`; the pinned bytes were copied under the session
  (`git show 9fcc1ed:tools/k3ctl/k3ctl`, equal to the pin) and `K3CTL` set
  to the copy, the pin unchanged and the new client unused (item 114);
  `k3-env record` PASS (a first attempt refused for `K3_ENV_ACCEPT_V` set
  empty, which must be unset; then Fedora's clean halt, two resets, two
  equal records, SHA-256 `32753344…`, V empty, `bootcmd_sha256=0404ae42737d…`
  equal to release candidates 2 and 3; the records differ from release
  candidate 3's `72443954…` only in the human's own `f45_rel`); at record
  2's prompt (05:42:20 UTC) **the human typed `saveenv` by hand**, storing
  the recorded environment (no `be_` variable, `bootcmd` unchanged; `I typed
  saveenv`), and the install attempt of that moment stopped at the
  port-open rule (no idle prompt while the human typed; no reset; nothing
  typed) and was repeated; `k3-env install` PASS (`be_image=
  be-mvp-probe-platform-gcc.img be_part=6`); **`k3-input-characterize`**
  with `K3_GUEST_TYPING=human-authorized` and `K3_INPUT_SESSION` the
  two-guests `shell.json`: run `20261102T054405Z` (`probe-console-input`
  from reset; `probe-type` 256 keys): `BE_MVP:PROBE console-input total=256
  polls=2049 nonzero_polls=209 max_per_poll=5 errors=0
  sha256=27576c0c829bf762`, **`class=supplies`** at both pacings
  (`repetitions=1:64/64,2:64/64,3:64/64,4:64/64`,
  `pacing_ms=11.7,11.7,11.7,2.7` measured at the typist for 10, 10, 10,
  and 1 ms: the tmux and picocom path's overhead; `verdict=PASS`, stop 10
  not applying); then run `20261102T054456Z` (`two-guests-shell` from
  reset; `guest-type` 16 steps, 100 keys, nonce `a95d14ec1c364221`): each
  domain echoed the nonce in its own focus period alone, `ls /bin | wc -l`
  printed `18`, `~x` dropped (`BE_MVP:17 INPUT_DROP bad-sequence`),
  `~~/bin/echo literal` read literally, both shells exited 0; `BE_MVP:18
  INPUT read=100 g0=43:29bf01b7f09b6324 g1=46:83304396a376991e
  dropped=bad-sequence:1`; `BE_MVP:12` `exits=344 sbi=343 dbcn_write=134
  dbcn_read=0 lines=63 ring_peak=0x12b8` and `exits=361 sbi=360
  dbcn_write=137 dbcn_read=0 lines=63 ring_peak=0x1308` (the served reads
  inside `sbi=`; `dbcn_read` counts refused reads, none); `BE_MVP:13
  RUN_COMPLETE domains=2 records=134 wakes=525`; capture PASS in `uboot`
  mode with the keys, nonce, and session file, attribution PASS, banner
  audit PASS; `k3-env restore` PASS (record 3 equal to record 1; Fedora
  autobooted from the restored `bootcmd`); `audit` `banners=10 resets=10
  findings=0` (one reset on Fedora down, seven at an idle prompt, two after
  a terminal marker; no hand reset, no unplanned boot, no `s` lost); the
  preflight after PASS and equal to the one before in every fact the MVP
  depends on, the kernel line included; `board-evidence` (`BE_RETAIN: PASS
  runs=2 … files=81`; `BE_MVP_EVIDENCE: PASS board … runs=2 pass=2`; the
  Serial log paragraph written by hand; no address, ssh target, or home
  path in the record). The board is restored and on Fedora. One typed
  characterization and one session on one board: diagnostic bring-up
  evidence under D-12's bound (no campaign; release candidate 4's runs the
  `shell` variants), never hardware validation.
- **The gates (M7-6) at `8418a377`**, from this checkout clean at
  `8418a377` (2026-11-02, 06:14 to 06:39 UTC; the driver and logs under
  `build/mvp/m7-gates/final/`): `./mvp/mvp tool-lock check` (`BE_MVP_LOCK: PASS roles=32 host_only_skipped=0 closure=259 lock_sha256=2f1b732dcf24`); `./mvp/mvp check` (06:14 to 06:24; `BE_MVP_CHECK: PASS`; `BE_MVP_QEMU: PASS runs=62 attempts=83 refused=21`, `BE_MVP_SESSIONS: PASS sessions=6 attempts=6 refused=0`, `BE_MVP_CAPTURE_SELF_TEST: PASS cases=164`, `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=399 rejected=399`, the nine host suites `gcc=clang` (`input scenarios=17 assertions=5188` among them), `BE_MVP_GUEST_PINS: PASS files=23 image_bytes=2063556`, `BE_MVP_LICENSES: PASS identifiers=3 files=884 external=2`, `BE_MVP_RUN_TOOL_DRY_RUN: PASS`, `BE_MVP_BUDGETS: PASS measured=40`, `BE_MVP_EVIDENCE: PASS development … files=367 images=315 qemu_attempts=83 session_attempts=6`, `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=49 boundary=15`); `./mvp/mvp evaluate` (06:24 to 06:33; `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`, the closure fetched `fedora:116,updates:143` from the host's cache, `BE_MVP_IMAGE_IDENTITY: PASS images=315 same=315 differing=0`); `./mvp/mvp uboot-rehearsal` (06:33 to 06:35; `BE_MVP_UBOOT_REHEARSAL: PASS cases=7 attempts=10 refused=3 uboot=d96d1c22c67b opensbi=78f14d30c951 qemu=10.2.2`); `make -C mvp kernel-repro` (06:35 to 06:36; `BE_MVP_KERNEL_REPRO: PASS outputs=23 identical`); `./be model-check` (06:36 to 06:37; `Beryllium Architecture Model 0.2 evidence: PASS`, `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241`, `Beryllium MVP input ring proofs: PASS theorems=4 assumptions_closed=4`); `./be evaluate` (06:37 to 06:38; `BE_EVALUATION: Model 0.2 rootless evidence PASS`). The first run of the gates,
  at `058fee76` (05:55 to 06:10 UTC; `build/mvp/m7-gates/attempt-1-058fee76/`),
  passed the lock and `check` and **failed `evaluate`** at `snapshot-check`
  inside the evaluator: this checkout is a standalone clone mounted at its
  own path, so the snapshot self-test found a repository and ran (every
  earlier `evaluate` had run from a linked worktree or a snapshot clone,
  where it skips itself), and its scratch commits failed for want of a git
  identity (`root@…(none)`). `tools/snapshot.sh self_test` now exports a
  fixed `GIT_AUTHOR_*`/`GIT_COMMITTER_*` identity for its scratch
  snapshots (`make` and `update` keep the configured identity); verified
  in the evaluator image before the commit (`8418a377`; no pinned file);
  the gates ran again from the start. By the plan's counting rule M7 adds
  **9,092** lines at `8418a377` (C 3,477, Python 4,239, shell 1,089, Make
  238, linker scripts 22, the wrapper 21, assembly 6; Rocq 399 reported
  separately) against erratum 1's 9,500; the checker-to-monitor size,
  reported and not limited, is **2.083** (monitor 15,359 lines, checking
  code 31,989, by M2-5's method with the harness drivers of the same kind
  added since; 2.049 at the M7 base). The evidence record is
  [`planning/mvp-m7-evidence.md`](../planning/mvp-m7-evidence.md) and the
  result packet
  [`planning/mvp-m7-result-review-summary.md`](../planning/mvp-m7-result-review-summary.md);
  over the gates' commit the ledger's C-47 and C-48 cite the board record
  and C-50 records the console's characterization (`./mvp/mvp claim-ledger
  check` and `render` run again on that commit), then this entry, the
  evidence record, and the packet. Nothing is pushed or merged; the
  development branch stays at `f5dc770b`.
- **The M7 result, exact commit `e1a6395e038d4dd095960f7a942a87399bdbce18`
  (parent `8418a377`), is responsible-human accepted as of 2026-11-02**
  (instruction `accept e1a6395e, move k3ctl pin to v1.1`, whose second
  part the human reversed two minutes later, before any pin byte had
  changed: `stop, keep k3ctl pin where it was for now, clone a copy if
  needed`); the
  [M7 result review and acceptance record](../planning/mvp-m7-result-review-summary.md)
  holds the decision with the eighteen departures, item 112's plan
  erratum (now the M7 plan's erratum 2) and the snapshot self-test fix
  among them. The `k3ctl` pin is unchanged and item 114 records the
  procedure the decision fixes (a copy of the pinned bytes when the
  checkout's client differs). No fast-forward, push, or successor was
  directed with the acceptance; on `ff + push M7` later that day
  (2026-11-02, 10:10) the development branch
  `beryllium/single-hart-runtime-r0` was fast-forwarded from `f5dc770b`
  to the commit recording that push, over the acceptance record
  `1b3f2e10`, and pushed to the private `origin` with `beryllium/mvp-m7`
  and `beryllium/mvp-m7-plan`; the M8 plan (proposed on `go`, below) is
  on its own local branch, and the M9 plan waits for `go`.

### The M8 plan proposed (2026-11-02)

On the human's `go` after M7's acceptance, `planning/mvp-m8-plan.md`,
the first verification plan, is proposed at exact commit `7a0c74ae` on
local branch `beryllium/mvp-m8-plan` from the M7 acceptance record
`1b3f2e10` (the plan's Q1: a linear descendant of the development tip
`f5dc770b`, so that stage 1's target includes the input ring and the
headers the leaves include); the packet is
`planning/mvp-m8-plan-review-summary.md`. What it fixes for `mvp/`:
nothing changes in the monitor, not a comment (stop (e)); the pilot's
first leaf is `be_mvp_denial_decide` with its four static helpers in
`src/mvp-sbi.c` (113 lines, pure over `const` inputs, one bounded loop,
no volatile, asm, union, bit-field, or pointer cast), its second
`src/mvp-ring.c` (CBMC's bounded per-call properties for the fourteen
public functions at capacities 512 and 4,096, the peer index
nondeterministic); the annotations live beside the source (WP's through
the ACSL importer or a gated copy; CN's in a gated copy whose
comment-stripped token stream must equal the source's); a separate
verifier image under `tools/verifier/` with its own closure (Fedora 44's
`frama-c-33.0`, `why3-1.8.2`, `alt-ergo-2.4.3` under CECILL-C,
`z3-4.16.0`, `cvc5-1.3.4`, `cbmc-6.8.0` by NEVRA and SHA-256; `herdtools7`
and CN from pinned sources built offline) behind `./mvp/mvp verify`, the
accepted evaluator and its 259-NEVRA closure unchanged; the litmus
tests mirror the compiled sequences of the exact symbols at the target
commit; every proof binds the digests of its translation unit, headers,
flags, and pins, and M10's gates run every arm again at RC4's tree
(S3-C's re-proof rule). The ledger would gain stage-1 rows under the
existing `proof about the abstract model` term and, only on a positive
pilot result, the terms `C-level contract proof` and `bounded model
check` with the required limit's sentence narrowed to the plan's fixed
words. Facts recorded for the work: none of the pilot's tools is
installed from an RPM on `l1`, and the unpackaged `cbmc` and `z3` under
the user's `~/.local/bin` (Helium's) must not be used; CN, Cerberus,
`herdtools7`, `isla`, VST, RefinedC, and CompCert are not packaged in
Fedora 44; the layer table above ("The monitor's layers (M6-3)") is a
reading at the M6-3 content and `src/mvp-input.c` is absent from it.
Item 101 (Binding.v's stale line citations) is addressed by the plan's
generated layout and symbol citations without editing `Binding.v`; item
103's two planning sentences would be corrected in M8-2 (the plan's
Q13). **Accepted 2026-11-02** (`accept 7a0c74ae wuth CN, go for m9`,
read as `with CN`: Q10 answered, the CN arm attempted with its recorded
fallback; the rest at their defaults; the plan branch took the
development tip `6105c34d` by merge first): M8-2 to M8-7 are authorized
on `beryllium/mvp-m8` from the acceptance-record commit, stage 1's
target; the same instruction directed the M9 plan.

### M8-2: the specification frozen, the layout generator, the drift check, the mutant generator (2026-11-02)

M8-2 ran on `beryllium/mvp-m8` from the acceptance record `6fbcc3d1`,
stage 1's target commit. **The specification document**,
`planning/mvp-m8-specifications.md` (410 lines), is its own exact commit
`004f31ae`, written by the session model from the M0, M1, and M2 plans,
security model v1, and the claim without opening `src/mvp-sbi.c` or
`src/mvp-ring.c` (D22; the fact sheet's type readings the one recorded
exception): the stage-1 property list P1 to P9 with the theorem names
each proof module must carry, Leaf A's contract (the entry conditions
E1 to E7 of the M1 plan's denial path, the outputs, the four helpers'
contracts), the ring's per-call properties for CBMC, the mutation and
vacuity rules, and the claim classes. Its SHA-256,
`ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d`, is
frozen in the plan's status block at `3c08c90e`, and every proof module
and arm annotation file cites it; it is presented to the responsible
human as reviewer of record (D-6), and proof drafting proceeds against
the frozen hash (Q12): a change from the review re-freezes the hash and
re-runs every proof that cites it. The same commit corrected item 103's
two planning sentences (Q13). **The tooling**, coded by a
`claude-opus-5.5` sub-agent in a worktree, reviewed line by line, and
merged at `4b829fe4`:

- `model/tools/gen-concrete-layout.py` (552 lines) reads
  `src/mvp-layout.h` and writes `model/proof/ConcreteLayout.v` (119
  lines; 96 constants as `N`; two macros not covered and named in the
  header, `BE_MVP_LAYOUT_H` with no value and the literal wrapper
  `BE_MVP_C`; the source's SHA-256 recorded); `--check` requires byte
  equality: `BE_MODEL_CONCRETE_LAYOUT: PASS constants=96 skipped=2
  sha256=c50da8ad3b06`. The generated file is never edited by hand.
- `model/tests/check-concrete-readings.sh` (377 lines), the drift check of
  D-2: every `(* reads: mvp/src/<path>:<symbol> *)` citation in
  `model/proof/Concrete*.v` names a function, type, macro, or file-scope
  data symbol present in that file at the checkout; the layout header's
  SHA-256 equals the generated module's record; the module is byte
  equal. Its self-test plants each refusal (`cases=28`). It reports
  `PASS files=1 citations=0` until M8-3's modules cite.
- `model/tests/check-concrete-tools.sh` (61 lines) runs both self-tests;
  M8-3's `run-concrete.sh` calls it, then the drift check.
- `verify/tools/mutate.py` (594 lines), D-7 item 6's seeded single-defect
  generator: `SOURCE --functions NAME… --out DIR [--seed 0x4d38]
  [--count 24]` with the operator, constant, and dropped-check rules;
  `--list` counts the candidates (Leaf A's `be_mvp_denial_decide` alone:
  72, its helpers more; `src/mvp-ring.c`'s fourteen public functions:
  353); `--oracle` is reserved for M8-6's equivalence oracle (exit 2
  today); `--self-test` `cases=23`, run by `tools.mk`'s
  `verify-tools-check` under `tools-check`. A fact for M8-6: 8 of the
  first 48 generated mutants trip a compiler warning the monitor's
  `-Werror` would reject, so the oracle must build mutants without
  `-Werror` or count such a mutant as killed at compile time, recorded
  either way.

Gates on the merged tree: the two self-tests, the drift check, the
mutant generator's self-test, `make -C model toolcheck`, and
`./mvp/mvp claim-ledger check` (claims=50; no pin moved: none of the
new files is pinned) pass; `./mvp/mvp check` passed every target but
`run-tool-check`, whose session lanes lost one boot's `s` to the fake
U-Boot's 0.8 s autoboot window in each of three runs (`missed-s-retry`,
`bad-environment-crc`, `input-characterize`: `MISSED the boot command
runs: an unplanned boot`), item 93's race, while the two M8 sub-agents'
builds ran on the host (load 1.5 to 3.8; item 93's disposition is one
gate at a time); the gate is run alone again before the M8-3 and M8-5
merges, and nothing on that path changed in M8-2. M8-3 (stage 1 in
Rocq) and M8-5 (the verifier image) run in parallel from `4b829fe4` on
`claude-opus-5.5` sub-agents in worktrees; the session model reviews
each merge.

### M8-5: the verifier image, `./mvp/mvp verify`, and the qualification (2026-11-02)

M8-5 ran on a `claude-opus-5.5` sub-agent in a worktree from `4b829fe4`
while M8-3 ran beside it, was reviewed by the session model (the
Containerfile, `closure.py`, `fetch-sources.py`, `verify.sh`, the token
gate, the digests record, the judging rule, `tools.mk`, the wrapper, and
`make-control.py` line by line; the host-side self-tests re-run by hand),
and is merged at `48652b03`. What it adds:

- `tools/verifier/`: the **verifier image** (D-10) on the MVP evaluator's
  digest-pinned base. None of the pilot's tools is installed on `l1`, so
  the MVP lock's method (a closure resolved against the installed set)
  did not apply: `closure.py resolve` ran **once** inside that base with
  Fedora's repositories reachable and weak dependencies off
  (`dnf5 --setopt=install_weak_deps=False install --downloadonly` on 35
  roots), the host verified every downloaded RPM's header signature by
  the Fedora 44 key alone, its NEVRA against its file name, and its
  header SHA-256 against its bytes (`fetch-closure.py`'s functions,
  imported), and recorded `closure.txt`: **481 NEVRAs** (466 installs
  and 15 upgrades of base packages; none removed), SHA-256
  `ce7ca11c…`. `closure.py fetch` fills the cache by NEVRA through
  `fetch-closure.py`'s sources and SHA-256 admission. `sources.txt`
  pins the **source-built tools** by SHA-256 with their licences:
  `herdtools7` 7.58 (CeCILL-B; the latest numbered release; its SHA-512
  and MD5 equal opam-repository's record), and for CN, which left the
  Cerberus repository in 2025: `rems-project/cn` at commit `cbe879c7`
  (BSD-2-Clause), the Cerberus commit its `cn.opam` pins (`68bdc84b`),
  and `monomorphic` 2.1.0 (MIT), Lem and every other OCaml library from
  Fedora's RPMs. `fetch-sources.py` admits an archive only at its
  pinned SHA-256 (self-test with a planted wrong digest). The
  Containerfile verifies every RPM and archive again before use, installs
  with every repository disabled and no `--allowerasing`, `--skip-*`, or
  `--nobest`, builds herdtools7 into `/opt/verifier/herdtools7` and CN
  into `/opt/verifier/cerberus` with no network, runs `why3 config
  detect` once, and records the installed packages, the source checks,
  and each tool's version line. **Nine of the plan's ten pinned tools**
  (frama-c, why3, alt-ergo, z3, cvc5, cbmc with cbmc-utils, rocq,
  herdtools7, CN). `build-image.sh` tags the image by the closure's, the
  Containerfile's, and `sources.txt`'s hashes (a changed source pin
  cannot reuse an old image). `verify.sh`, behind `./mvp/mvp verify`
  (with `MVP_SRC_CACHE` allowlisted beside `MVP_RPM_CACHE` in the wrapper
  and `tools/make-control.py`), fills the caches, builds the image if
  absent, and runs each suite as `evaluate.sh` runs `mvp check`
  (`--rm --init --network=none --security-opt label=disable`, the tree at
  its own path, `env -i`, `python3 -I -B`), writing `build/mvp/verify/`.
  The accepted MVP evaluator, its closure, and its lock are unchanged.
- `verify/tools/token-equal.py`, the **token-stream gate** (D-5): the
  annotated copy's C token stream with every comment gone must equal the
  source's extract, the five Leaf A functions located by symbol; no
  normalisation; the copy may open only with the source's own `#include`
  directives, token for token, so no macro can change what its tokens
  mean. Self-test `cases=28` (a changed operator, constant, and
  identifier each refused).
- `verify/tools/digests.py` and `verify/target-digests.txt`, the **target
  digests** (D-7 item 3): the two translation units, the eleven headers
  each includes (five in-tree, six of the port), the compile flags as the
  Makefile states them, the include directories, and the three pins (the
  specification, the closure, `sources.txt`): `files=13`, made at a tree
  whose `src/`, `port/`, and `Makefile` equal the target commit
  `6fbcc3d1`'s. Re-written only on the human's direction; a merge that
  changes one of them without the re-proof rule is stop (i).
- `verify/qualify/` and `verify/tools/qualify.py`, the **qualification**
  (D-7 item 2, H41 stage 3): per arm and solver, the four cases on tiny
  C files (known-pass, known-fail, vacuity in two halves, a planted
  defect), judged from the tools' own output lines with per-goal limits
  of 60 s; a "must not prove" case accepts unproved or failed, and WP's
  proof counts only if the named solver, not WP's simplifier, closed the
  goal. `verify/litmus/qualify/` holds the message-passing tests whose
  `Never` with the fences and `Sometimes` without are herd7's
  qualification under `riscv.cat`.

**The recorded outcome** (`./mvp/mvp verify` PASS in 560 s; image
`localhost/beryllium-mvp-verifier:ce7ca11cb755-b71721530f48-36eaf6d2362b`):
`BE_MVP_QUALIFY: PASS arms=9 qualified=6 not_run=0`, "arms" counting the
(arm, solver) pairs. Qualified: CN with Z3 and with cvc5, CBMC with its
SAT solver (MiniSAT 2.2.1) and with cvc5, litmus under herd7, and WP with
Alt-Ergo. Not qualified, each as observed and no expectation changed:
**WP with Z3** (Z3 `4.16.0` answers `unsat` on WP's own integer prelude
with no goal, so it "proves" the known-fail contract, `ensures \false`,
and the planted defect; the sub-agent cut the prelude to seven axioms
the standard model satisfies, which cvc5 answers `unknown` on; the
reproducer is kept under `build/mvp-verifier/dev/`), **WP with cvc5**
(cvc5 `1.3.4` does not terminate under WP's default `-wp-memlimit 1000`;
without the limit it answers in 0.03 s, and at 16,000 MB it proves 2 of
the 5 solver goals), and **CBMC with Z3** (14,768 Z3 calls in 300 s on
the vacuity-ensures case; the suite kills it at 60 s). Why3 `1.8.2`
recognises none of the three provers' versions and uses its newest
drivers. CN built in about two minutes of its three-hour box (the first
build failed only on Lem's library path, `LEMLIB`). Facts for M8-6:
Fedora's frama-c 33.0 ships the ACSL importer (`-acsl-import`, Q8) and
no RISC-V machdep (`gcc_x86_64` is LP64 with a signed `char` where
RISC-V's is unsigned; CBMC has `--arch riscv64`; Q14); CN types
`unsigned long` struct fields as `integer`, so `u64`-suffixed literals
are refused against them; CBMC's `--unsigned-overflow-check` flags the
ring's intended 64-bit wraparound; the image has no RISC-V binutils, so
M8-4's disassembly uses the MVP lock's `riscv64-linux-gnu-objdump` on the
host. `./mvp/mvp check` and `./mvp/mvp evaluate` (315 of 315 images
identical) pass on the branch.

**Decisions of 2026-11-02 recorded in the M8 plan's decision record:**
the WP arm's solver pair cannot be formed (D-7 item 7 names Z3 and
cvc5), stop 5, decided **A**: WP runs with Alt-Ergo alone as a recorded
arm that cannot meet item 7, CN is the arm that can give a positive
result, no plan change. The model lane's soft limit was re-set from
6,000 to **12,000** (erratum 1: the lane counts M8-2's tools, and stood
at 6,278 with `Concrete.v` and `ConcreteRings.v` alone) and the bridge
lane's from 3,000 to **6,000** (erratum 2: 2,793 after M8-5, before the
litmus tests and the harnesses). **The specification is accepted** as
reviewer of record at exact commit `004f31ae` (`accept 004f31ae
004f31ae , ff + push m8 line, proceed`, 19:38): its hash is unchanged,
and the three readings the stage-1 proofs had found are recorded there
as errata S-1 to S-3 of the accepted text (P1 holds for the block's
immutable published words, not the inbound ring's index words, which
hart 0 may write before the target's `ready`; P5 holds below the M0
plan's exit ceiling, at which a deniable exit fails the domain; a parked
domain still takes TERMINATE and posts TERMINATED). On the same
instruction the development branch `beryllium/single-hart-runtime-r0`
was fast-forwarded from `6105c34d` to the commit recording this and
pushed to the private `origin` with `beryllium/mvp-m8` and
`beryllium/mvp-m8-plan`; the worker branches stay local. M8-3's stage 1
(22 theorems closed at `11d14ebd`, two more in progress) is in review;
M8-4 and M8-6 start from the merged tip.
### The M9 plan proposed (2026-11-02)

On the human's `go for m9` (with the M8 plan's acceptance),
`planning/mvp-m9-plan.md`, measurement, is proposed at exact commit
`86f1c68b` on local branch `beryllium/mvp-m9-plan` from the M8 acceptance
record `6fbcc3d1`; the packet is `planning/mvp-m9-plan-review-summary.md`.
What it fixes for `mvp/`: a 4 KiB log page in hart 0's `.mvp.bss` (a
64-byte header, 96-byte records, capacity 42, at most 12 expected per
image, four measurement registers extended by measured records only, a
close record before the first domain's entry, overflow failing closed as
a new class `BE_MVP_CLASS_LOG`), printed losslessly as `BE_MVP:19 LOG`
and `BE_MVP:20 REGISTERS` lines in new `src/mvp-log.c`/`.h` with
`tests/log-test.c`; records for the monitor's own text and rodata (an
informational self-report, offline, kept only if the loaded ranges
reproduce post-link), the core identity (measured) and the configuration
and policy identities (build-recorded; `two-guests` records
`policy-absent`), and each domain's kernel Image and device tree as
placed plus `anchor`'s secret page, each domain gated on its launch
register before its hart starts, so `:06 MEASURED` becomes `:06 LAUNCH`
per domain in every scenario and `DOMAIN_TERMINATED`'s `sha256=` becomes
the domain's register; `wrong-measurement` keeps its name with the flip
on the expected register; a `self-report-flip` variant; the post-link
reference manifests from `tools/gen-reference.py` under
`build/mvp/references/` (CEL-JSON shape, pinned by the image checker,
copied into records); the checker's rebuild, replay (labelled
unprotected), compare, and `cel.json` export with the negatives as
mutations; the platform record's register sections; the IMA checks in
`tools/guest-pins.py`'s delta check and the checker; item 104's `help`
listing committed under `results/20261030-uboot-help/`; `k3-run.sh`'s
`staged_sha256` field computed (item 116). The accepted counts (`exits`,
`records`, `wakes`, `denials`, `alternations`) and the SBI version must
not change (the plan's stop 5). No board command: QEMU is the gate; the
human's read-only probe is their own; one correlation boot folds into
the next scheduled board session. Awaiting the human's decision; nothing
is implemented.

### The M9 plan's second candidate, after the steering review (2026-11-03)

On the human's `have gpt-6-astra review the m9 plan as steering input`
(2026-11-02, 23:12), a `gpt-6-astra` agent reviewed the first candidate
`86f1c68b` in a detached worktree at the packet commit, reading no other
review (`planning/mvp-m9-plan-review-gpt-6-astra.md`, unedited; the
governance hook's required model edited for that one launch and
restored, SHA-256 equal). It recommended a second candidate on five
blockers, two of which the session confirmed against the sources before
writing it: the 64-byte header could not hold the magic and two 32-byte
identities (72 bytes before version, capacity, count, and state), and
"compared with nothing" was wrong of the core identity, whose printed
sixteen hex digits `tools/gen-scenario.py` embeds in the expected
`CONFIG_SEALED` line for `tests/check-capture.py` to match. **The second
candidate is exact commit `4f4a8f76`** (the first superseded). What
changes for `mvp/`: the log page gets an explicit little-endian encoding
(a 128-byte header, 96-byte records at fixed offsets, capacity 41 with
the close included, the registers in their own 128 bytes beside the
page, every unused byte zero, at most 15 records per image), is 4 KiB
aligned and contained in hart 0's MVP-region BSS (there is no `.mvp.bss`
output section; the BSS lies inside `.mvp.data`), and prints its terminal
registers before `BE_MVP:14`; a **per-image contract** fixes for every
image class (the three scenarios and their variants, the probes, the
early-failing negatives, `wrong-measurement`, `self-report-flip`, a
failure after launch) the records required, the gate, the completion
state, and the terminal prefix the checker accepts, under one global
rule (every launch comparison succeeds and the log closes before `:07`,
or no domain hart starts); the console grant joins the measured
configuration as a `console-grants` record (item 108, Q18) with the core
identity and the printed prefixes unchanged; `self-report-flip` flips one
bit of a named inert rodata constant `be_mvp_log_canary` post-link with
the nominal reference frozen and the mutated image's hash recorded, and
the checker expects exactly one finding; S3-C.5's wrong digest at each
monitor-controlled record is met by capture mutations with recomputed
registers; metadata-only mutations the registers cannot see are
negatives; the checker recomputes every digest from the build's inputs
and compares every field (the historical `PINNED_MEASUREMENT` fallback
never serves M9); the export is the **Beryllium log profile**, a JSON
profile derived from TCG CEL 1.1 revision 11 and mapped field by field,
no interoperability claimed, S3-C.5's "CEL-JSON" read as this profile
(Q7, for acceptance); the IMA check is an allowlist of record objects
and content types; D-9's published words carry fixed conditional forms
for the self-report kept or omitted, the probe performed or not, and the
board correlation run or not, so every permitted outcome has true words;
hashing time and console volume are measured and reported; the counts
are judged by the capture checker's existing rule and no new invariant
is made of an observed schedule (D-11; stop 5 reworded); `.monitor.input`
is an R2 range (Q19). The estimate is 4,000 to 6,200 counted lines
against the soft 6,000, the re-evaluation foreseen at the M9-4
checkpoint. **Accepted 2026-11-03** (`accept 4f4a8f76`, Q1 to Q19 at
their defaults, Q17 answered): M9-2 to M9-6 are authorized on
`beryllium/mvp-m9` from the acceptance-record commit; Part 1 Revision 3
comes as its own exact commit; the board is available (the human's
`the board is available now`, the same message), so Q31's steps can be
scheduled when M9 reaches them, under the shared-board gate and item 8.

### M9-2 begins: Part 1 Revision 3 proposed (2026-11-03)

M9 implementation began on `beryllium/mvp-m9` from the acceptance record
`bc80b620` (which took the development tip `55047781` by merge first).
**Part 1 Revision 3 of security model v1, the measurement log, is
proposed at exact commit `4bc079db`** (`planning/security-model-v1.md`,
252 lines appended after Revision 2, 0 removed; the packet is
`planning/security-model-v1-revision-3-review-summary.md`), written by
the session model under the standing split and the M9 plan's D-8: Part
1's existing `measurement` asset instantiated as the log page and the
registers (hart 0's MVP-region BSS; mapped by no domain root under I2;
one writer under I15 and I16; not a secret, and not evidence against an
adversary who alters the monitor); I19 (hart 0 alone writes the log and
the registers, only before any domain hart starts, closing with the
expected count; overflow or a page that cannot close fails the run; no
domain hart reads it) and I20 (no domain hart starts unless every
required launch comparison has succeeded and the log is closed; each
domain's records and gate precede its `HART_STARTED`), with the exact
statement of what the registers bind (each stream's ordered digest
values and nothing else; the checker's field comparison binds the rest;
the close is structural); the threat model's additions (forged `:19`
and `:20` lines bounded by I18; post-measurement alteration unseen by the
log; the reference manifest, the generator, the loader observation, and
the platform observation as trusted inputs that are never one chain; the
hashing and rendering time as measured availability effects; four
containment clauses; the firmware measurement, root of trust, and
boot-ROM question deferred); six TCB rows filling the measurement row,
with the running TCB told from the offline evidence TCB; the scope (not
proved; not a theorem of M8's stage 1, whose gate predicate is re-read
against M9's global rule at integration; no trigger evaluated; the log no
channel, notification, or manifest). M9-2's other deliverables (the log
profile `docs/log-profile.md` with the encoding, the enumerations, the
per-image contract, the `:19`/`:20` grammar, the JSON profile and its
field-by-field mapping to TCG CEL 1.1, and the IMA allowlist; item 104's
premise record `results/20261030-uboot-help/`; the probe template
`planning/mvp-m9-platform-probe.md`) are being written by a
`claude-opus-5.5` sub-agent in a worktree from `4bc079db`. The human
said the board is available (2026-11-03); M9's Q31 steps are scheduled
when M9 reaches them, each announced first with the human present.
**Revision 3 was accepted** the same morning (`accept 4bc079db`, 00:46):
M9-5's claim and ledger rows may cite I19 and I20. **M9-2 is complete at
`ca48456f`**: the sub-agent's three documents were reviewed (the
encoding against D-1 offset by offset; the run classes against the boot
sequence's order in `src/mvp-runtime.c`, `probe_sstc`, `build_gstage`,
`check_payload`, the placements, `measure()`, `publish_blocks()`,
`start_run()`; the line bounds against the 320-byte buffer; the premise
record's bytes, CRLF, and privacy; the template's required words) and
merged: `docs/log-profile.md` (1,176 lines; the TCG CEL 1.1 PDF fetched
again, SHA-256 `142dce15…` equal to the steering review's; its URL not
repeated in `docs/` because its path holds a literal `claim.md` forbids
there; ten choices the plan left open are made and listed in its section
1 for review with the result, among them the console grants' one byte
per domain then SHA-256, the gate outcome on each domain's last launch
record, the three rendering paths, and the barrier line's hashing ticks
saturated so the line fits), `results/20261030-uboot-help/` (item 104's
premise: `help.txt` `ca42cbc5…`, 117 commands, `crc32` and `md5sum`
present, `hash`, `sha1sum`, `sha256sum`, `tpm`, `tpm2`, and `verify`
absent; CRLF kept by a `.gitattributes`; `SHA256SUMS`; the record was
captured by `tools/k3-env.sh characterize` under board policy item 6 on
2026-10-30, not by a `diag` step), and `planning/mvp-m9-platform-probe.md`
(the four outcome classes, (d) never "locked", the fifth "not performed
as of <date>", and Q14's words). M9-3 (the monitor's log) and M9-4 (the
reference manifests and the checker's log module) run in parallel from
`ca48456f` on `claude-opus-5.5` sub-agents, the profile their contract;
`capture-check` is expected red on M9-3's branch until M9-4 lands.

### M9-3 and M9-4: the monitor's log, the references, the checker's log module (2026-11-03)

**M9-3** (`claude-opus-5.5`; merged at `39bb5ab2`, reviewed line by line
against the profile and the plan's D-1 to D-4): `src/mvp-log.c` and
`.h` (pure restricted C: the page's fields written and read by their
widths at fixed offsets, append with the slot count and the stream's
`srec`, the register extended for a measured record only, overflow at
slot 40, the close only at the image's expected count, the gate over all
32 bytes, the console grants' serialization, the lines rendered into
hart 0's 320-byte line builder); `measure_log()` in `src/mvp-runtime.c`
after the placement and before `publish_blocks()` and `start_run()` (R2's
five ranges by link symbols, R3's core identity and console grants
measured with the two build identities informational, each domain's R4
with its gate on its last record, the close, the block and the barrier's
`:20` before `:07`, the terminal `:20` from the barrier's values, a failed
gate printing the block and failing as `measurement` with both values, a
page that cannot close failing as the new class `log`);
`tests/log-test.c` (47 scenarios, 874 assertions, GCC = Clang: every
offset, enumeration, the profile's test vectors verbatim, and the
losslessness of five rendered pages parsed back and rebuilt equal); the
generator's expected records, launch registers by the profile's
recurrence, count, lines, and run class in each expectation and the
header's 172-byte log constants, `wrong-measurement` flipping bit 0 of
the protected domain's expected register (Q16); the image checker's rules
with a mutation each (the page and registers in hart 0's MVP-region BSS
under `HART0_ONLY`, the constants matched to the image's sequence, count,
and report, the launch registers computed independently from the boot
image, the canary unreferenced, the R2 ranges their sections' extents);
`self-report-flip` as `anchor`'s image with bit 0 of the inert
`be_mvp_log_canary` flipped after the link (`tools/flip-canary.py`;
moved from `two-guests` so that the longest, v3 log carries it);
`guest-pins.py --check` refusing `CONFIG_IMA*` and `CONFIG_EVM*` in a
guest `.config` (D-5; six planted settings refused); the M9 fixtures
made again from this tree's images (GCC, boot hart 0; the refused one
Clang's) with `tests/fixtures/pre-m9/` holding the base's expectations
so the M7 captures stay judged against the expectations of their time.
**Q4 determined: R2 is kept**, the five ranges reproducing byte for byte
across clean rebuilds for both toolchains. Hashing cost in QEMU: about
46 ms per domain for the 2 MB kernel (`:06 LAUNCH ticks=0x70793`),
`0xe3b44` ticks at the barrier for `te-poc`; the log's text adds 4,556
bytes to a `te-poc` run's console. The MVP region holds `0xd000`
(`two-guests`, GCC) to `0xe000` (`anchor`) of its `0x40000` bytes; the
core is unchanged.

**A found-and-fixed fixture defect (the plan's stop 2, decided `fix now`
by the responsible human on 2026-11-03).** M9-3's QEMU suites showed
`probe-platform` (Clang) print `ipi mode=hs sent=100 delivered=0 spv=100`
once in 25 runs: hart 1's `FID_IPI_VS` call zeroed the one shared
receipt count as soon as its hundredth HS receipt let it leave
`ipi_hs()`, before hart 0 had read it for its HS line. The fix
(`75459737`, merged `8f6660ab`) gives each phase its own count,
`received[2]`, as `delta` and `spv` already had; a snapshot by hart 0
cannot close the race, since hart 1 can reach that call between hart
0's hundredth send and its first read. `tests/probe-test.c` (host test
`probe`, 65 scenarios, 779 assertions, GCC = Clang) runs hart 0's real
`ipis()` against a modelled domain hart whose V=1 call comes at each of
hart 0's calls after the hundredth receipt: 17 of its 64 schedules fail
on the old code with exactly the captured line, and a snapshot-only
variant fails 5; all pass on the fix. 80 of 80 QEMU probe runs (four
images, both toolchains, ten each) printed `delivered=100` in both
modes. The struct grew 8 bytes, so all eight probe images changed and
the four GCC probe fixtures were made again; nothing else was relinked.
The printed lines, their fields, and their meaning are unchanged, so the
retained board probe records stay comparable.

**M9-4** (`claude-opus-5.5`; reconciled on the merged tree and merged at
`1edc3652`): `tests/log_module.py` (the checker's log module: the page
rebuilt from the `:19` lines byte for byte, the registers replayed and
compared with both `:20` lines and labelled `unprotected`, every digest
recomputed from the build's inputs under `--build-root`, every record and
register compared with the image's reference, the per-image contract and
the lines' positions required, `DOMAIN_TERMINATED`'s digest the domain's
launch register, stream 0's difference the finding `self-report differs:
OBJECT`, the export `log.json` beside `result.json`; 105 module cases);
`tools/gen-reference.py` (one post-link reference per image and
toolchain from the linked image's own 172-byte constants and the linker's
symbols, each R4 object recomputed from the source the expectation names,
`self-report-flip`'s metadata checked, an image whose generator section
is not the reference's own refused; 29 images per toolchain, every one
`constants=linked expectation=same`; a 31-case self-test on a synthetic
image); `tests/check-capture.py` judging M9's fixtures against the
current expectations, each image's reference, and the build, and M7's
against `pre-m9/` (self-test `cases=300`, `mutations=459` each rejected;
every M9 fixture as declared: complete 11, gate-fail 1,
post-launch-failure 2, pre-measurement 2, self-report-flip 1, refused
1); the platform record's measurement-log sections
(`tools/platform-record.py`); `tools/k3-run.sh` computing
`staged_sha256` from its recorded comparison with a dry-run case that
fails it (item 116, closed); the dry run serving M9's captures (M2's
board `anchor` capture, which prints no log, is no longer one). The
reference tool's lines took the tag `BE_MVP_LOG_REFERENCE` so that no
record line names two tools. M9-4 reconciled M9-3's departures from the
first draft of the profile by taking the generator and the monitor as the
implementation of record and adapting the reader to what they emit.

**Gates on the merged tree (`8f6660ab`)**: `./mvp/mvp check` passed every
step through `capture-check`, `references`, `reference-check`, `budgets`
(`measured=50`), `lint` (940 files), the platform-record and
platform-probe checks, and the evidence bundle, and failed only in
`run-tool-check`'s timing-bound autoboot cases (`missed-s-retry`,
`missed-s.record`, `diagnostic.stop`, a different one each run) under a
load average of 15 to 19 from M8's solver jobs on the same host: item
93's known case, which M9-4's own gate run had passed when the host was
idle. The fix item 93 names (the dry run's autoboot window, 0.8 s, made
the board's 3 s so that the tool's 0.5 s retry has the margin the board
gives) is made as a found-and-fixed harness defect on its own branch from
this tip, by a pinned sub-agent, with the run count under load as its
evidence; it changes no board tool and no judgement, and the result
packet records it as a departure. The ledger's C-10, C-40, C-41, and
C-48 cite the moved files at their commits (`f5e7925e`). M9's counted
lines at `eef77b50`: 9,240 of the re-set 10,000 (Python 6,127, C 2,820,
Make 169, shell 100, linker script 24; excluded: fixtures and records
14,744, Markdown 2,362, JSON 178).

### M9-5: the claim's sentences, the ledger's rows, the guide, the crosswalk (2026-11-03)

Written by the session model under the standing split (the plan's work
package table). **The claim** (`3b1d6a1f`): the blockquote gains D-9's one
sentence after M7's console sentence, and the required limit's "The
measurement is a local identity, not attestation." is replaced by D-9's
text with its three slots filled from the recorded outcomes, each from
its fixed pair of forms: the self-report clause for R2 kept, the platform
clause "not determined as of 2026-11-03; no probe was performed", and the
board clause "The log and launch-gate evidence is from QEMU; the M9
board correlation has not run"; the forbidden-phrasing check passes and
no other claim text changes. **The ledger**: C-51 (the log and the
registers: the profile, `mvp-log.c`, `measure_log()`, the host test, the
reference tool, the log module, the `te-poc` and `anchor` captures), C-52
(the launch gate per domain, citing I19 and I20 of Part 1 Revision 3 and
`wrong-measurement`'s capture), and C-53 (the self-report and
`self-report-flip`'s one finding), each with the methods host unit test,
adversarial test, semantic checker, and emulation and no board method;
U-16 (R1, the loader observation, and the platform observation as
evidence classes beside the log, the probe not performed as of
2026-11-03) and U-17 (D-5's third check: the monitor measures only what
it places or seals before entry); U-10 and U-12 restated for the log;
U-14's note closing item 108 (the console grants are a measured record of
stream 1 since M9, while the printed `CONFIG_SEALED` identity stays the
sealed core identity by design); C-16's and C-40's non-claims gain D-9's
sentence that `DOMAIN_TERMINATED`'s digest is the stored launch register
read again. `claim-ledger check` passes (`claims=53 boundary=17`).
**The guide** (`5ec2c609`): a measurement section after the console path
(the records in `measure_log()`'s order, the `te-poc` capture's `:06
LAUNCH`, `:19`, and `:20` lines field by field, the failed gate, the
self-report, what the checker's log module does and its lines with the
hashing cost and the console volume, what the log is not), the
walk-through's pointer, the checker's rules, and the passages that
described M2's single `MEASURED` line and the report's `measurement_hex`,
which the report no longer holds since M9. **The crosswalk**
(`eef77b50`): `planning/mvp-m9-crosswalk.md`, D-7's analysis deliverable
(systemd v259's four pieces on five dimensions; the reference manifest's
contribution to each route; the requirements crosswalk among a vTPM, an
SBI extension, and an offline adapter; what a simulated root needs from
the log; the IMA boundary under each route; milestone 7's items placed
and its gate discharged for 1.0; one Amutable lesson adopted, with what
is deferred and rejected). The plan's Q13 citation joins one post's title
to another's date (item 119). Open for M9-6: the evidence bundle does
not yet copy `log.json` and the references into a run's record (item
120); the profile's ten choices (its section 1) are presented for review
with the result; the human's probe and the correlation boot each wait
for a board session the human schedules.

### M9-6: the bundle, the window, the gates, and the result (2026-11-03)

**Item 120** (`74b02017`, `dc6bef1f`; merged `1d91b829`; `claude-opus-5.5`,
reviewed line by line): `tools/evidence.py` carries each attempt's and
each board run's `log.json` beside its `result.json` and the reference
manifests with their pins (every reference in the development bundle;
a board record those of the images its runs ran), under a stated rule
(required where the image's reference says it logs and the verdict is
`PASS` or `STOP`; absent for a refused attempt and a `pre-measurement`
image; each the one its `result.json` names by SHA-256, judged against
the reference kept; a rehearsal case judged against another left out as
stale); ten new self-test cases (51), fifteen mutations of the new checks
each failing the self-test; the guide's bundle tables; the profile's 5.3
names the two sets (`45ce8e8c`) and C-51's pin follows (`cbbdcb17`).
`./mvp/mvp check` passed on the branch; the bundle grew by 174 files (52
QEMU exports, 6 session exports, 58 references and their pins). **Item
93** (`b7e059b5`, `7ed829c1`; merged `dc07f7d3`; `claude-opus-5.5`): the
dry run's autoboot window is the board's 3 s and runs to its deadline;
the cases whose outcome depends on the deadline (`missed-s`,
`missed-s-twice`, `late-s`) give the console tool its default
`K3_ECHO_SECONDS=5`, the board's value, where the dry run otherwise keeps
1 s for speed; the fake logs each `s` with its time after `Autoboot in`
(`autoboot.log`) and a case failure after a late `s` reads `late by N s
under load … not a tool defect`; a final `autoboot` check prints the
run's latest `s` as its margin (1.26 s in the gates' run; 0.09 s was the
old window's) and fails the run on any late one; a first draft had ended
the window early at a boot's second swallowed `s`, a shortcut the board
does not have, and was replaced before the merge. Ten dry runs passed
under load (two at once among them), five more at `b7e059b5`; the dry
run takes about 20 s longer (23 windows run to their deadline). No board
tool and no judgement changed; item 121 records a code reading of the
console tool for a later sweep.

**The gates at `X` = `dc07f7d3`**, from this checkout clean at `X`
(2026-11-03, 20:33 to 21:04 UTC; `build/mvp/m9-gates/final/`): the lock
(`roles=32 closure=259`), `check` (`BE_MVP_CHECK: PASS`, 12 min 36 s; the
capture checker `cases=300`, `mutations=459`; the references 29 per
toolchain; the sessions 6; the dry run with its autoboot check; the
ledger `claims=53 boundary=17`; the bundle `files=530 … log_exports=58
references=58`), `evaluate` (`BE_MVP_IMAGE_IDENTITY: PASS images=339
same=339 differing=0`; the record `build/mvp-evaluator/record/20261103T204544Z`),
the U-Boot rehearsal (`cases=7 attempts=8 refused=1`), `kernel-repro`
(`outputs=23 identical`), `./be model-check` (the proofs, the input
ring's four theorems, the differential `comparisons=241`), and `./be
evaluate` (`Model 0.2 rootless evidence PASS`): all PASS. By the plan's
counting rule M9 adds **9,812** lines at `X` (Python 6,545, C 2,820,
shell 254, Make 169, linker scripts 24; fixtures and records 14,744,
Markdown 2,667, and JSON 178 excluded and reported) against erratum 1's
10,000; the checker-to-monitor size, reported and not limited, is
**2.294** (monitor 16,417 lines, checking code 37,653 by M7's set with
`tests/log_module.py` added to the checkers; 2.083 at the M9 base; M9's
increment 1,058 monitor lines and 5,664 checking lines, the recomputation
and replay being the design). The costs (D-10) are in the evidence
record: in the suite's run at `X`, hashing took 36 to 38 ms per domain
for the 2 MB kernel and 73 to 88 ms at the barrier in most images, with
outliers that follow the host's scheduling (item 123), and the log's text
adds 3,220 (a probe) to 4,817 (`anchor`) bytes to a run's console. The
evidence record is `planning/mvp-m9-evidence.md`; **the M9 result is the
commit that adds it and this entry over `X`**, presented in
`planning/mvp-m9-result-review-summary.md`. Not run: the human's probe
(the claim's platform clause reads "not determined as of 2026-11-03; no
probe was performed") and the correlation boot (the board clause reads
"The log and launch-gate evidence is from QEMU; the M9 board correlation
has not run"); no board command was issued.

### The M9 result accepted (2026-11-03)

The responsible human accepted the M9 result at exact commit
`892b68c81dace15d2357e034e859b3eccd130abc` (over the gates' commit
`dc07f7d3`) on 2026-11-03 by the instruction `accept 892b68c8`
(`planning/mvp-m9-result-review-summary.md` is its review and acceptance
record; `planning/mvp-m9-evidence.md` the evidence). With it: the
profile's ten choices stand as version 1 and Q7's reading stands; the
probe-race fix and the two harness fixes (items 93 and 120) are accepted
in the result; the Q13 citation mismatch is erratum 2 of the M9 plan,
recorded in its decision record with erratum 1 (the limit re-set to
10,000), the `fix now` decision, and Part 1 Revision 3's acceptance (item
119 closed). The claim's D-9 sentences take effect with their slots
filled from the recorded outcomes (R2 kept; "not determined as of
2026-11-03; no probe was performed"; "the M9 board correlation has not
run"); the ledger's C-51 to C-53 carry no board method until a board run
at M9's images. No fast-forward, push, board step, or successor was
directed: the development branch stays at `55047781`, `beryllium/mvp-m9`
and `beryllium/mvp-m9-plan` stay local, the probe and the correlation
boot stay the human's to schedule, and M10's plan waits for M8's result.

### M8-3: stage 1, the concrete operational model in Rocq (2026-11-02)

Stage 1 ran on a `claude-opus-5.5` sub-agent in a worktree from
`4b829fe4` beside M8-5, in two sessions (the first ended without a reply
after two modules; the worktree's commits were intact and it continued),
and is merged at `5f02a5f3` after the session model's review of the step
table, the `refines` map, the new objects, every theorem statement
against the accepted specification and its errata, the runner, and the
one Makefile line. Five modules under `model/proof/` (none an accepted
file; the accepted six, `InputRing.v`, and the gates are byte-identical):

- `Concrete.v` (2,272 lines): the words of harts 0 to 2, each typed by
  `Binding.v`'s `hart_object` or `InputRing.v`'s objects where one exists
  and otherwise by one of three new objects (a ring's buffer bytes, a
  state page's phase group, its counters), each inside an enclosing
  `Binding.v` object; the ring operations of `mvp-ring.c` on those words
  with 64-bit indices (Q5) and a configured capacity; `be_mvp_denial_decide`
  and `be_mvp_mgmt_decide` as functions; the launch gate as any predicate
  (M9's content abstracted); the specification's twenty steps as one
  labelled transition system (`cstep`), each with its hart, phase, write
  set, and the `Binding.v` transition it refines; traces as the `reach`
  relation under sequentially consistent interleaving at word
  granularity. Every layout constant is `ConcreteLayout.v`'s; 92 source
  readings cite symbols (`(* reads: mvp/src/<file>:<symbol> *)`), which
  the drift check verifies. The header lists each abstraction.
- `ConcreteRings.v` (3,026 lines): the ring invariant `ring_ok` over the
  counters `T ≤ Rc ≤ Rl ≤ H ≤ Wc ≤ T + C`, the pending images byte for
  byte, and a ghost history of posts, publishes, and takes, preserved by
  every operation and reached from the boot (`ring_inv_reach`); the frame
  (`exec_frame`: a step changes only its declared words); the ordering
  premises L1 to L5 as the predicate `respects`, which **every SC trace
  satisfies** (`sc_respects`), so the theorems that carry them make the
  dependency visible without using it, the litmus tests carrying the
  weight for the hardware (the plan's D-3); P3 (`ring_no_overrun`,
  `ring_take_published_only`, `ring_indices_monotone`,
  `control_ring_fails_closed`, `input_ring_drops_under_room`), P4
  (`ring_fifo_integrity`, `ring_type_set`), P8 (`drain_round_robin`,
  `drain_in_order`).
- `ConcreteBridge.v` (717 lines): obligation 1,
  `concrete_step_within_footprint` (every step's declared write set, and
  every word it changes, within `footprint mvp_binding (refines step)`)
  and `single_writer_carried` (H3 over every changed word, the input
  path included); obligation 2, `roots_from_instance` (for `te-poc` and
  `anchor`, with the configuration's roots those the generated
  `Instances.v` derives, each window and page leaf is a memory grant
  whose every right A8 admits, the leaf's `W` bit its write right),
  `flow_is_declared_channel` (A6: the only cross-domain flow is the
  declared channel), `mgmt_grants_from_instance` (the sealed management
  grants are the instance's: none for `te-poc`, domain 0's pause and
  terminate on domain 1 for `anchor`), and `instance_page_numbering`
  (objects 0 and 1 the windows, the pages consecutive from 2, by
  `vm_compute`). Still assumed and stated there: the scenarios list their
  pages in guest-physical order from `be_mvp_channel_gpa` (`Instances.v`
  records no extents).
- `ConcreteClaims.v` (1,275 lines): P1 as `barrier_publication_block`
  (erratum S-1: the block's immutable published words), P5 as
  `denial_iff_entry_below_ceiling` (erratum S-2) and
  `denial_record_before_resume`, P6 as `mgmt_decided_by_control_hart`,
  `mgmt_outcome_from_grants`, `mgmt_one_pending_per_domain`,
  `parked_never_resumes` (erratum S-3), and `mgmt_answered_once` as a
  safety property (erratum S-4: decisions counted; a delivered request's
  later result is the target's progress, not claimed), P7 as
  `entry_after_gate` and `gate_false_no_start`; the lineage index of
  Model 0.2's 24 and M3's 22 theorems (Q15; the evidence record carries
  the table); the record `stage1_claims`.
- `ConcreteAssumptions.v` (41 lines): one `Print Assumptions` per
  theorem; `model/tests/run-concrete.sh` (103 lines) requires the sorted
  theorem names to equal the report names and every report closed, after
  the tools' self-tests, the drift check, the escape pattern, compile,
  and `rocq check`; `model/Makefile`'s `proof:` recipe gains the one line
  `tests/run-concrete.sh` after `tests/run-input-ring.sh`.

The gate: `Beryllium MVP concrete model (stage 1): PASS theorems=26
assumptions_closed=26 citations=92 layout_sha256=c50da8ad3b06` (59 s
alone); `make -C model proof` passes in 115 s with the accepted gates'
lines unchanged (`PASS instances=generated`; Model 0.2 `PASS`; the input
ring `theorems=4`). The two literal properties that are false on the
faithful model, P1 and P5 as the accepted specification words them, keep
their counterexamples in the modules' comments (errata S-1 and S-2); no
code defect was found. The model lane by the plan's rule: **8,425** of
the re-set 12,000 (erratum 1).

### M8-4 and M8-6: the litmus tests, the pilot's first run, and the specification's Revision 1 (2026-11-02 to 03)

**M8-4** (merged `14851913`): the ordering premises L1 to L5 as litmus
tests mirroring the compiled sequences of 55 symbols in both toolchains'
`two-guests` monitors (`verify/litmus/L1.litmus` to `L5.litmus`;
`sequences.txt` with the symbols' digests and the ELFs' with and without
debug sections; `verify/tools/litmus.py`); every premise `Never` under
herd7's RVWMO (`riscv.cat`), and the sub-agent's ablation (each fence or
the writer's branch removed) `Sometimes` for every test, so no `Never` is
vacuous. herd7 7.58 implements neither `bltu` nor `bnez` for RISC-V, so
the tests branch with `blt` and `bne` against `x0` on the same registers
(values below 2^63; herd7's control dependency follows the registers).
The sequences check runs as the first suite of `./mvp/mvp verify`, beside
the target-digests binding, and not in `check`, which stays the
development gate. The record's bound: the `two-guests` monitors; `te-poc`'s
and `anchor`'s own call sites, scanned read-only, have the same fence
shapes and are not recorded.

**M8-6, the pilot's first run** against the accepted specification
`004f31ae` (merged `bc98a875` Leaf A, `0b45698e` Leaf B; the records
under `results/20261103-verify/`): every arm ran and recorded; **none is
a positive result**, and the reason is the same on both leaves. **Leaf
A** (`be_mvp_denial_decide` and its helpers): WP through the ACSL
importer against the unmodified source (Q8; no annotated copy needed),
Alt-Ergo 2.4.3 alone (decision A), OPEN at 123 of 132 goals in three of
four rounds (12,464 s); CN on an annotated copy that passes the token
gate (686 tokens), Z3 and cvc5, OPEN at 5 of 58 (CN never releases the
compound literal `*out = {0}`, `leaf_at` would need a `focus` inside a
braceless loop, and `&`, `|`, `^` are uninterpreted); CBMC with `--arch
riscv64` FAILED at 333 of 336 properties. The three goals every arm
leaves open are **two inputs on which the leaf contradicts the accepted
specification**: a zero-size window (`map.size = 0`), which the leaf
refuses by precondition and `tests/deny-test.c` pins, and a store to a
read-only page **inside** the window, which the leaf refuses first
because the accepted M1 plan's entry says "a fault inside the window …
stay[s] terminal" and E7's accepted wording had dropped the qualifier.
Five more true goals (the `vsstatus` bits and `resume_pc`) time out on
Alt-Ergo at 60 s and are confirmed by CBMC. The vacuity check found the
leaf's `SPVP ? SPP : 0` arm at `src/mvp-sbi.c` L317 dead under E3 (a true
observation; harmless; a comment some day). Mutants: 24 of 24 killed by
WP (every kill a timeout, so the score is weak), 22 killed and 1
equivalent (`m04`) by CBMC. Q17: WP's Rocq export is **not qualified**
(why3 1.8.2 knows `coqtop` 8.16 to 8.20; the image has `rocq` 9.3.0).
**Leaf B** (`mvp-ring.c`, a bounded model check, never proof): 15,037
properties over the fourteen functions and the sequence harness at 512
and 4,096 bytes, SAT and cvc5, two configurations (with and without the
unsigned-overflow check); 13,546 checked, coverage and vacuity ok; OPEN
because the 4,096-byte buffer parts covered 3 of 512 position classes in
the 600 s budget (1,382 properties), the eight index-advance sites wrap
by design where the accepted wording named only the differences (92),
and **seven places where the leaf differs from the accepted wording and
matches its header's contract and `tests/ring-test.c`** (`init` refuses
domain 2 and sets `limit` to the view's own index; `post` and `room`
bound the tail by the published head; `acquire` bounds the head by the
released tail; `taken` is a writer view's reading; `room` is capped at
256 after the header, so "room grows by the released size" is false as
worded). The sequence harness returns the posted record byte for byte
across every wrap class at both capacities. Mutants 22 killed, 1
equivalent (`m18`: `HEADER_TYPE` is 0), 1 harness finding (`m02`: the
test asserts `failed == 1`, the contract says "failed"). The bridge lane
reached about 9,250 of the 6,000 erratum 2 set; the human re-set it to
**12,000** (erratum 3).

**The specification's Revision 1** (stop 2; the human's decision
`spec_mismatches=revision_1_rerun`, 2026-11-03): the session read all
nine disagreements as **errata of the specification, not defects of the
monitor** (it was drafted from the plans without reading the C, D-6's
rule, and the leaves do what the M1 plan and the ring header say), and
wrote Revision 1 as its own exact commit **`93a8d136`** (SHA-256
`aeb75682…`; `planning/mvp-m8-specifications.md`, nine clauses corrected
in place and tabled with their evidence in the document's "Revision 1"
section; sections 1 to 3, 6, and 7 unchanged, so stage 1's modules keep
citing the accepted hash; the packet
`planning/mvp-m8-specifications-revision-1-review-summary.md`). On its
acceptance the three arms are re-run against it (WP about four hours,
CBMC on the ring about two, CN minutes), each annotation re-made to cite
the new hash, and M8-7 follows. Housekeeping found: a timed-out cvc5
leaves about 1 GB of temporary files under `build/mvp/verify/tmp` until
the next run clears them (item 118).

### M8-6's re-run against Revision 1, and M8-7: the outcome (2026-11-03)

**The re-run** (`claude-opus-5.5`, reviewed line by line; merged
`2e298c3a`): every arm re-transcribed to Revision 1's nine clauses
(`transcription.txt` per arm names each) and run in the verifier in
3 h 44 min. WP on Leaf A **OPEN 130 of 134** (round 0 is the first run's
four rounds transcribed; round 1 adds a ladder of assertions that the
record's nine fields hold their entry values between the stores and
closes `D_resume_pc`; the four `vsstatus` goals are true, as CBMC shows,
and time out in Alt-Ergo, which has no bit-level reasoning; a tried round
2 closed three of them and slowed `D_place_here` past the 60 s budget,
so it was not adopted; 18 of 24 mutants killed, two compile errors, four
masked by the open goals; vacuity `not-ok` by its rule on two paths dead
under the contract, the `SPVP` arm under E3 and the `map->size == 0` test
under R1-2's `requires`, the rule not changed after the result). CN on
Leaf A **OPEN 5 of 55** (the same five closed; 44 goals the compound
literal's resource, 5 `leaf_at`'s liveness, 1 the uninterpreted bitwise
operators; the pair formed; the token gate 686 tokens). CBMC on Leaf A
**SUCCESSFUL 336 of 336** at unwind 4 with `sat` and cvc5 (22 mutants
killed, m04 unobservable, m12 a contract finding: the null test on `out`
that the host test exercises outside the contract's domain; vacuity ok,
cover 6 of 6). CBMC on the ring **OPEN 13,547 of 14,931** (the first run's
seven errata closed; the 20 wrap sites intended under R1-9; 1,382 open
properties the 4,096-byte buffer parts' 3 of 512 classes within 600 s;
mutants 22 killed, m18 unobservable, m02 a harness finding) with **one
new finding, stop 2 again**: `room` fails on both solvers at both
capacities because `be_mvp_ring_room` also treats a tail more than a
capacity behind the cursor as malformed and fails the view, as its header
contract says, where Revision 1's R1-6 defines "well formed" by the
published head alone (`leaf-b/defect-room.txt`: a host reproducer,
`CONFIRMED contradictions=4`, the state one no release writes). The human
chose **erratum S-5** (form answer `room_row=erratum_s5`): recorded in
the M8 plan's decision record, no Revision 2 and no re-run, since the
ring arm is OPEN at its bound either way. `digests.py` hashes the host's
export of the pinned specification inside the image, which has no git
(`b2f40b1d`; self-test 18 cases); `verify.sh` exports it with the lock's
git. The records are `results/20261103-verify-r1/` (28 files); the first
run's stay as the errata's evidence.

**The outcome (M8-7; the plan's D-7; the human's `outcome_reading=true`):
inconclusive** for a C-level contract proof of Leaf A in M8's box: no arm
met items 1 to 7 (WP's four timeouts and its Alt-Ergo-only pair since
stop 5; CN's tool limits; CBMC bounded by construction with the `sat` and
cvc5 pair, Z3 having been non-terminating on its vacuity case). Not "no
vehicle fits": CN's grounds are tool limits, not structural. The
recommendation per claim class, non-load-bearing: (a) pure decision
functions: CN, with WP under Alt-Ergo for specification debugging and
CBMC's bounded check beside; (b) ring-class code: CBMC bounded per call
with the protocol in stage 1; (c) the cross-hart protocol: stage 1 with
its litmus premises; (d) compiled execution: assumed. So the claim is
unchanged and the pre-authorized sentence is not added; the ledger
(`a9323ed5`) gains the stage-1 rows C-51 to C-55 (the barrier and the
gate, the single writer, the rings and the drain, the denial, management;
method `proof about the abstract model` with the litmus tests as
`semantic checker`, each saying "the concrete operational model (stage 1)
under sequentially consistent interleaving, with ordering premises L1 to
L5 discharged by litmus tests"), U-16 (what stage 1 does not model),
U-11's litmus note (its coverage now `semantic checker`), U-13's text
superseded as Q35 states (Model 0.3 is 2.0's), C-06's non-claim re-read
at the target commit (item 101 closed), and the third review item,
recording the outcome, in `docs/claim.md`'s list and the ledger
(`review_items=3`). **The ledger IDs are per lane**: M9's accepted line
numbers its rows C-51 to C-53 and U-16, U-17 too, and the second line to
integrate into the development branch renumbers its rows (item 124).

**The gates at `X` = `f1813841`** (the merge `2e298c3a`, the ledger's rows `a9323ed5`, and the cherry-picked `f1813841`), from a standalone clean clone at `X`
(`worktrees/beryllium-hypervisor/m8-gates`; 2026-11-04, 01:50 to 06:00 UTC;
`build/m8-gates/final/` in the clone): the lock (`roles=32 closure=259`); `check` (`BE_MVP_CHECK: PASS`, 10 min 25 s; `BE_MVP_QEMU: PASS runs=62 attempts=74 refused=12`; the capture checker `cases=164`, `mutations=399`; the dry run PASS, its latest `s` 0.78 s after `Autoboot in`; the ledger `claims=55 boundary=16`; the bundle `files=354 images=315`); `evaluate` (`BE_MVP_IMAGE_IDENTITY: PASS images=315 same=315 differing=0`); `claim-ledger check` (`review_items=3`); `./be model-check` (`Beryllium MVP concrete model (stage 1): PASS theorems=26 assumptions_closed=26 citations=92`, the input ring's four theorems, the differential `comparisons=241`; 131 s); `./be evaluate` (`Model 0.2 rootless evidence PASS`); and `./mvp/mvp verify` (`BE_MVP_VERIFY: PASS`, `wall_seconds=13480`: the sequences, the digests, the token gate, `BE_MVP_QUALIFY: PASS arms=9 qualified=6`, `BE_MVP_LITMUS: PASS premises=5 never=5`, and the four arms' verdicts and counts equal to the re-run's line for line): all PASS. Two earlier attempts at `2e298c3a` are kept (`attempt-1/`: `check` PASS, `evaluate` stopped for want of the OpenSBI firmware in the fresh clone, hard-linked in; `attempt-2/`: `check` failed in the dry run's `missed-s-retry` case, item 93, at a load average of 1.5), after which item 93's fix from M9's accepted line was cherry-picked as `f1813841` (`fake-uboot.py`, `run-tool-dry-run.sh`; the case lists resolved without M9's `staged-sha256` case) and the gates ran again from the start. The lanes at `X`:
model 8,544 of 12,000 (Rocq 7,450; the tools and gates 1,094), bridge and
contracts 11,811 of 12,000, tool glue 1,473 of 2,500 (1,954 less the
closure's 481 data lines), 9 of 10 pinned tools; the whole model gate
131 s against the 600 s proof-time limit. The evidence record is `planning/mvp-m8-evidence.md`
(the outcome, the lineage, the premises, the qualification matrix, the
arms, H38 and H41, the departures); **the M8 result is the commit that
adds this entry over it**, presented in
`planning/mvp-m8-result-review-summary.md`. No board step (the plan has
none); no push.

### The M8 result accepted (2026-11-04)

The responsible human accepted the M8 result at exact commit
`12b0e71b908e36041745601d214c03a5be34ad1e` (over the gates' commit
`f1813841`) on 2026-11-04 by the instruction `accept 12b0e71b`
(`planning/mvp-m8-result-review-summary.md` is its review and acceptance
record; `planning/mvp-m8-evidence.md` the evidence). With it: the outcome
stands as recorded, inconclusive under the plan's D-7 (no C-level contract
proof of any monitor function; the claim unchanged; the ledger's stage-1
rows C-51 to C-55, U-16, the restated U-11, U-13, and C-06, and the third
review item; the recommendation per claim class non-load-bearing); the
specification's fourteen errata are errata (S-5 among them); item 93's
dry-run fix cherry-picked from M9's accepted line, item 124's per-lane
ledger IDs (renumbered by the second line to integrate), and item 125's
tool limits (upstream reports the human's choice) are as presented. No
fast-forward, push, or successor was directed: the development branch
stays at `55047781`, `beryllium/mvp-m8` is pushed only through that
commit, and M10's plan, release candidate 4, follows on the human's
`go`, M7's, M8's, and M9's results being accepted.

### The M10 result accepted: release candidate 4 (2026-11-05)

The responsible human accepted exact release-candidate commit
`d70a8535474a690920ff152e7b38a25c589adba9` (`RC4`, parent `f3f8c8d8`, over
`X4` `a6eaa88501b1d08b9e83c734d692c82376117e77`) on 2026-11-05 by the instruction
`accept d70a8535`; `planning/mvp-m10-result-review-summary.md` is its review
and acceptance record and `planning/mvp-m10-evidence.md` the evidence.
With it: plan errata 1 (25 runs, not 26) and 2 (bridge lane 13,000), the
licence manifest's U-Boot and nolibc readings, and the evidence record's
eight departures stand; the ledger's `release_candidate_commit` is
filled; release-path step 1 holds for RC4; M0 to M10 are complete and
accepted. No fast-forward, push, tag, publication, snapshot refresh,
release-path step 2, archive or MVP 2.0 work was directed; the development
branch stays at `dd52368d` locally and on `origin`, and the M10 branches
stay local. The board is restored, free, and on Fedora.

### The M10 result proposed: release candidate 4 (2026-11-05)

Exact release-candidate commit **`d70a8535474a690920ff152e7b38a25c589adba9`**
(`RC4`, parent `f3f8c8d8`, over exact candidate tree `X4`
`a6eaa88501b1d08b9e83c734d692c82376117e77`) is proposed on local branch
`beryllium/mvp-m10`, unpushed; `planning/mvp-m10-result-review-summary.md`
is its review packet and `planning/mvp-m10-evidence.md` the evidence.
All eight gates, the 25-run board campaign, the restore/preflight pair,
the two retained records and exact-RC4 `check` pass as the M10-5 to M10-7
entries state. The result is not accepted; no merge, push, tag,
publication, release-path step 2 or successor is directed. Next human
command: `accept d70a8535`, `revise: …`, or `defer`.

### M10-6 and M10-7: the COM260 campaign and the release candidate 4 result (2026-11-05)

M10-6's first attended session stopped before any campaign run: the
environment install's first autoboot stop was genuinely missed (the empty
prompt followed immediately by NUL bytes and ROM/SD boot output, so the
fail-closed parser returned status 4 and sent no retry `s`), not item
121's late-prompt shape. The human chose `restore-fix-restart`; the
environment was restored, the preflights passed, diagnosis found no
production defect, and the human directed `try again`. That private local
session is preserved under `build/` with `-stopped`, never committed or
used as evidence.

The retry ran at exact `X4`'s images with the human present at the install
and the restore (2026-11-05, 22:20 to 22:42 UTC): preflight before PASS;
19 images staged and SHA-256-bound; two fresh-prompt environment records
equal, `V` empty; the temporary environment installed with one attended
`saveenv`; **`BE_MVP_K3_CAMPAIGN: PASS runs=25 groups=19 sessions=3`**;
the original environment restored with one attended `saveenv`, record 3
equal to record 1 under the V rule, Fedora autobooted; preflight after
PASS, the same kernel and every region, firmware, partition, environment
and pinned k3ctl check equal. Four probes passed; `two-guests`, `te-poc`
and `anchor` passed three GCC and one Clang runs each with their accepted
counts; the six negatives failed as declared, `self-report-flip` with
exactly one expected offline self-report finding; the three GCC shell
images passed their 16-step/130-key sessions under item 8 with the focus,
input accounting, denials and management requests accepted. Every
applicable log page/register set was rebuilt, replayed, recomputed and
compared with its post-link reference; every loader attribution, selected
image digest, size check, capture check and banner audit passed. There
was no late prompt, missed stop, unplanned boot, hand reset, unexplained
banner or recovery action. The session recorded 49 resets and their
banners, no finding. The board is restored, free, and on Fedora.

`mvp/results/20261105-com260-rc4/` (314 files, `f3f8c8d8`) is the retained
record; it verifies and passes the ledger's privacy check. The platform
record includes "Console input on K3" and "The measurement log";
`planning/mvp-m10-evidence.md` is the result's evidence record. M10-7
adds them to the final tree, the ledger's C-47, C-48 and C-51 to C-53
methods gain `diagnostic board run`, C-54 to C-58 cite `X4`'s gate and
verifier records, M9's board-correlation qualifier is removed, and the
platform clause's date becomes 2026-11-05 (the probe remains not
performed). Items 115, 118, 121 and 122 are closed. The result's soft
limits: M10 1,429 of 2,500; the model lane 8,655 of 12,000; the bridge
lane 12,248 of the human-re-set 13,000; checker-to-monitor 2.349,
reported and not limited. The departures and claim boundary are in the
evidence record. The release-candidate commit `RC4` is the commit that
adds these final claim and ledger updates over `X4`; the packet names it.

### M10-5: `X4`, its eight gates, and the release-candidate record (2026-11-05)

The first candidate after M10-4, `7a5c7062`, passed all eight gates from
a clean standalone checkout, but `rc-record` exposed one integration
defect: M7's kernel-repro correctly records 23 outputs, including the
standalone `busybox` and `musl-libc.a`, while the development bundle's
guest manifest still carried 21 (the Image, init, module, and DTBs). The
fix `a6eaa885` adds the two userland outputs to the bundle and to the two
focused self-tests (`evidence.py`: 51/51; `rc-record.py`: 28 mutations),
so `7a5c7062` is superseded and **`X4` is exact commit
`a6eaa88501b1d08b9e83c734d692c82376117e77`**. Every gate was then run
again from a clean standalone checkout at `X4` (2026-11-05, 13:22 to
17:32 UTC; `build/mvp/m10-gates/final/`, the first run under
`attempt-1-7a5c7062/`): the tool lock PASS; `check` PASS; `evaluate` PASS
with every image byte-identical; the U-Boot rehearsal PASS (`cases=7
attempts=12 refused=5`); kernel-repro PASS (`outputs=23 identical`, the
kernel, BusyBox, and musl among them); `model-check` PASS with stage 1
green; the model's rootless evaluator PASS; `verify` PASS in the accepted
image (`wall_seconds=13254`, every suite verdict and count equal to
M10-2 and the accepted M8 result verdict for verdict: WP and CN OPEN,
Leaf A's CBMC bounded check SUCCESSFUL, the ring's bounded check OPEN).
`mvp/results/20261105-rc4/` (641 files, commit `6d55bc42`) is the
release-candidate record: the host and evaluator bundles (M9's log
exports and references included), the host's and evaluator's model
evidence and logs, the rehearsal, kernel-repro, and the seven rc-record
gate logs; `--verify` passes. `mvp/results/20261105-verify-rc4/` is the
final verifier's 33-file retained record. The ledger's release object
now names `X4` (the release-candidate commit stays `null` until `RC4` is
fixed and accepted, as RC3's did), and C-54 to C-58 cite the `X4` run.

### M10-4: the release surfaces for release candidate 4 (2026-11-05)

Work package M10-4 (planning/mvp-m10-plan.md, D-4) was written by the
orchestrating session at `9ba30105` on `beryllium/mvp-m10`: the ledger's
`release` object names `MVP 1.0 release candidate 4` with both commits
`null` until `X4` and `RC4` are fixed (the release-surfaces check reads
`candidate=4 commit=not named yet`, as it did between `X3` and `RC3`);
`docs/claim.md`'s header names release candidate 4 and moves release
candidate 3 to accepted history beside 1 and 2, and its evidence
paragraph names release candidate 4's board session and evidence record;
the guide's first and last sentences name release candidate 4, its
campaign bullet describes the 25 runs in 19 groups with the typed
sessions and the `K3_GUEST_TYPING` gate, and its section 8 gains "The
verifier (M8)" and "The licence manifest"; the disclosure names release
candidate 4 and its three accepted predecessors, extends the model table
through M10 (`claude-opus-5.5` for M7 to M10's implementation and the
re-proof; `claude-fable-5.1` for the plans, Revisions 2 and 3, the M8
specification, and M10-4), adds a `gpt-6-astra` row for the M9 plan's
steering review, and names the three S3-C design reviews by their tools;
the root `README.md` says release candidate 4 is in preparation and
release candidate 3 stays the latest accepted candidate until `RC4` is
accepted; `planning/mvp-rc-walkthrough.md` gains "What changed since
release candidate 3" (the shell and the focus sequence, the measurement
log, the verifier, the campaign, the manifest) and two "Where things are"
rows. The claim's text changes only in RC4's metadata (S3-C.7's M10
clause); `claim-ledger check` passes with the phrasing check. **Plan
reading (D-4):** "`release_candidate_commit` filled at `RC4`'s creation,
as RC3's was" is not quite RC3's history: `RC3` named `X3` as its
candidate tree and left the release-candidate commit `null` (a commit
cannot hold its own SHA), and debt sweep 3's row H filled `89ef04e9`
after the acceptance; `RC4` does the same, naming `X4`, and the
acceptance record fills `RC4`.

### M10-2: the re-proof at the base tree (2026-11-04)

Work package M10-2 (planning/mvp-m10-plan.md, D-2, Q3, Q4) ran on
`beryllium/mvp-m10-wp2` from `b5842520` on a `claude-opus-5.5`
sub-agent, was reviewed, and merged at `575eafab`; the nine ledger pins
of C-54 to C-58 (`Concrete.v`, `ConcreteClaims.v`, L1, L3, L4, L5,
`sequences.txt`) moved at `c64853a3`. No `mvp/src` byte changed. Stage 1
was re-read where M9's log replaced `measure()`: of the 92 accepted
citations, 89 symbols read as at `6fbcc3d1`, `be_mvp_runtime_main` calls
`measure_log()` in its place, and `measure` is gone. The abstraction
changed only there (`23d09b95`): a gate and an expected launch register
per domain, the close a configuration boolean, hart 0's prepare step
guarded by `global_rule` (M9's D-1: every comparison succeeds and the log
closes, or no domain hart starts), and the log page outside stage 1's
words as a reading (I19; hart 0 alone writes it, before the barrier); 99
citations. **All 26 theorems were re-proved with statements byte-identical
to M8's** (checked mechanically against `f1813841` by the orchestrating
session; two lemmas added, `global_rule_gates` and
`global_rule_false_no_start`; `PASS theorems=26 assumptions_closed=26
citations=99`; `./be model-check` PASS). The litmus sequences were
re-extracted at this tree's monitors (`5e4110eb`; 49 of 55 excerpts at
new addresses, 30 symbol digests; L1 to L5 changed in their cited
addresses and digests only, their programs and conditions byte-identical),
the WP arm's vacuity note moved to line 318 (`c43ba773`), and
`target-digests.txt` was re-written at `c43ba773` (`52e816cb`: the target
line, `mvp-sbi.c`, `mvp.h`; the specification pin unchanged). The CN copy
needed no change (M9's one line is outside Leaf A's five functions; the
token gate's range is 201 to 324). `./mvp/mvp verify` at `52e816cb`
(2026-11-05, 03:03 to 06:49 UTC, `wall_seconds=13554`) **matched the
accepted M8 result verdict for verdict**: sequences PASS; digests PASS
`files=13`; token-equal PASS `tokens=686`; qualify `arms=9 qualified=6`;
litmus `never=5`; WP OPEN `goals=134 proved=130`; CN OPEN `goals=55
proved=5`; CBMC Leaf A SUCCESSFUL `properties=336`; the ring OPEN
`checked=13547 open=1384`; the records `results/20261104-verify-rc4-base/`
(33 files; `dd2d6da7`). Lanes: model 8,655 of 12,000; the bridge lane
12,248 of 12,000 by the M8 plan's added-lines rule (re-transcription net
0) is **stop 7**, and the human re-set the limit to 13,000 (plan erratum
2). Not run in the linked worktree: `./be evaluate` (M10-5's clean
checkout runs it). The rows C-54 to C-58 cite this base-tree run until
M10-5's run at `X4`.

### M10-3: the campaign's session groups, four debts, the licence manifest (2026-11-04)

Work package M10-3 (planning/mvp-m10-plan.md, D-3, D-5, D-6) was coded
by a `claude-opus-5.5` sub-agent on branch `beryllium/mvp-m10-wp3` from
the acceptance record `b5842520`, reviewed line by line, and merged at
`f3d56369`; the two ledger pins of `tests/check-image.py` (C-41, C-52)
moved to its fix commit at `3953a01c`. It changes no monitor source. The
sub-agent's `./mvp/mvp check` at its tip (13 min 43 s) passed every
stage but the ledger's (the pins since refreshed): `BE_MVP_QEMU: PASS
runs=64 attempts=82 refused=18`, `BE_MVP_SESSIONS: PASS sessions=6`,
`BE_MVP_RUN_TOOL_DRY_RUN: PASS`, `BE_MVP_LICENSES: PASS identifiers=6
files=1047 texts=6 source=git external=2 manifest=9`,
`BE_MVP_LICENCE_MANIFEST: PASS components=8 identifiers=6 sources=2
outputs=23 pins=3`. Counted lines 1,411 added and 137 deleted of the
2,500 limit (Python 954, shell 393, Make 60, the wrapper 4); the three
licence texts (906), `COPYING`, and the generated manifest are reported
apart. **Plan erratum 1:** D-3 and Q2 total the campaign as 26 runs; the
composition they state (four probes, twelve scenario runs, six negatives,
three sessions) is 25, which is implemented; recorded in the plan's
decision record, the plan text unedited. Two choices to review with the
result: U-Boot's row names `GPL-2.0-or-later`, the identifier U-Boot's
`Licenses/README` declares for the project, with the note that the whole
is redistributable under version 2 and most files also under a later
one; and a `nolibc` row (`LGPL-2.1 OR MIT`, compiled into the init) with
a third licence text beyond Q7's two. The pieces, in the sub-agent's
words:

**Item 118** (`89db0279`): `verify/tools/cbmc-ring.py`'s
`execute()`, which runs every CBMC job, the mutants' host tests, and the
version probes, gives each command a directory of its own under the
runner's `TMPDIR` (`build/mvp/verify/tmp`; `tempfile.mkdtemp`, mode 0700)
as its `TMPDIR` and removes it in a `finally` when the command ends, a
timeout included; `remove_tree()` repeats the removal for up to 5 s while
a process of the killed session still writes there. No verdict, bound,
solver, setting, record, or output line changes, so the ring arm's lines
at M10-2's re-run are as before. Two self-test cases (33): a job that
writes 64 KiB as `smt2_dec_problem_1` into its `TMPDIR` and sleeps past a
1 s budget times out with its directory (a child of the root, mode 700)
gone and the root empty, and a job that finishes is likewise cleaned;
against the runner of `b5842520` the first leaves `smt2_dec_problem_1`
in the root and fails.

**Item 122** (`d278b409`): the item's premise was not the code's:
`evidence.REHEARSAL_FILES` never named `log.json` (M9-6 carried the
rehearsal exports into the development bundle through `evidence.py`'s own
export list), so a release-candidate record's `rehearsal/` would have
held no export, and nothing required the host bundle's `references/` or
its QEMU and session exports. `tools/rc-record.py`'s `make()` now reads
the bundle's references with their pins (`evidence.references()`) and
refuses none, or a count other than `bundle.txt`'s `references=`; holds
each QEMU, session, and rehearsal attempt to `evidence.log_export()`'s
rule against them and refuses a count other than `log_exports=`; copies
each `--rehearsal` attempt's export to `rehearsal/CASE/attempt-N/
log.json`; and writes `references=N log_exports=M
rehearsal_log_exports=K` into `rc.txt`. `evidence.py` is unchanged. Six
seeded inputs are refused with nothing written (no `references/`, a
reference without its pin, a QEMU export missing, a `bundle.txt` counting
two, a rehearsal export missing, one judged against another reference);
with the `make()` of `b5842520` the record case and all six fail
(`mutations=28`, 22 before).

**Item 121** (`9a374aed`): `tools/k3-uboot.py after-stop --retried`,
passed by the console tool after its second `s` only, reads the prompt
with that `s` echoed at it and nothing else (`=> s`, the BSP's stamp
removed, quiet) as status 5, a late prompt, and awaits a stamp cut at a
read's end rather than reading it as other output; the first wait and the
statuses 0, 3, and 4 are as before. On 5 `tools/k3-console.sh` records
`late-prompt` in the keystroke log and `LATE-PROMPT` on stderr, clears the
stray `s` with Ctrl-C (its header says when), waits for the fresh prompt,
and goes on as at 0; the cut line `=> s<INTERRUPT>` is no command, so
`fresh` still holds for `saveenv`. Nothing new is typed and the
templates' allowlist is unchanged. The fake U-Boot's fault `late_prompt`
holds the keys sent while it is stopping and echoes them at the late
prompt (`after-prompt` in its `autoboot.log`); the dry run's case
`late-prompt` (1.5 s, the default `K3_ECHO_SECONDS`) runs the
environment's records and install on it: three late prompts, PASS, no
`MISSED`, no unplanned boot, the `saveenv` at a fresh prompt. With the
console tool and `k3-uboot.py` of `b5842520` the case fails at its first
stop (`MISSED`, an unplanned boot, `STOP stop=1 the unplanned boot did
not end within 20 s`); `missed-s`, `missed-s-twice`, `missed-s-retry`,
and `late-s` are unchanged and pass. Not reproduced on the board.

**The shell images' image check** (`da4fd1b9`): a latent defect found
while building the session groups: `tests/check-image.py`'s `dtb_plan()`
inserted `rdinit=/init-shell` into bootargs that already held it when
given a console variant's own expectation (`te-poc-shell`,
`anchor-shell`, v2 and v3), so `tools/k3-run.sh`'s pre-launch image
check would have refused both at their first board run;
`two-guests-shell` (v1, checked against the built-in scenario, M7's one
board session) and the `variants` target were unaffected. It is now
inserted only when absent; `variants` prints the same lines, and the
dry run's `campaign-session` runs both images through `k3-run.sh`. The
ledger's pins of this file (C-41, C-52) move.

**The campaign's session groups** (`7f3320df`, `8c110901`; D-3, Q2, Q11): `K3_PLAN`
gains `self-report-flip` (anchor's third board variant, staged as
`be-mvp-anchor-self-report-flip-gcc.img`) and the three GCC shell images
once each with a ninth field, the session (`scenarios/S/sessions/
shell.json`): 19 groups and **25 runs** in the plan's order. D-3 and Q2
total the composition (four probes, twelve scenario runs, six negatives,
three sessions) as 26; it is 25, which is implemented and reported (an
erratum for the orchestrating session). `K3_STAGE` is the plan's 19
images (the staging tool's grammar and 44-character bound hold);
`k3-campaign` depends on `references`; `make -C mvp print-k3-plan` prints
`BE_MVP_K3_PLAN: groups=19 runs=25 sessions=3 staged=19`.
`tools/k3-campaign.sh` checks every group first (a session readable and
its expectation's by SHA-256, a console-input expectation with its
session, exit 2) and refuses a plan with a session without
`K3_GUEST_TYPING=human-authorized` before any board command (exit 5);
each session run is M7-5's path (`K3_GUEST_RUN=session`: `guest-type`
with a fresh nonce after the arming and focus lines, re-gated on a line
of hart 0's, no reset while it types, a banner stop 10, the capture
judged with `--typed`, `--nonce`, `--session`), and other runs get both
variables empty. `tools/k3-run.sh` refuses a session other than its
expectation's, records `guest_session=NAME guest_session_sha256=…`, and
records the typist's own stop: it had read the keystroke log's last stop
after the banner audit's own stop 12, so a session ended by a banner was
recorded `stop=12`, not S3-C's stop (b). The fake U-Boot gains the fault
`unarmed`; the dry run gains `campaign-session` (the refusals; then
`self-report-flip` and the three shell groups in one campaign, `PASS
runs=4 groups=4 sessions=3`, each typed from its run's reset and judged
PASS with its keys, nonce, and session, with no reset or banner in the
keystroke log from a session's start to its end (`8c110901`); the board
record re-judges all four) and `campaign-session-stops` (no arming line: nothing typed, stop
13; a banner after the first step: stop 10 with stop (b)'s text), and
`stage` and `selectors` assert the 19 images and 19 groups/25 runs. On
`b5842520` the campaign tool refuses every session group as usage and
the run records `stop=12`.

**The licence manifest** (`6e2f25dc`; D-5, Q7): `tools/licence-manifest.py`
generates `docs/licence-manifest.md` from the pins (the lock's
`MVP_PIN_*`, `guest-pins.py`'s sources, `guest.mk`'s Linux remote, B1's
OpenSBI and B3's U-Boot, whose tags and commits must be the lock's):
eight rows, Linux `v7.2` (`GPL-2.0-only WITH Linux-syscall-note`),
`nolibc` (Linux's `tools/include/nolibc`, `LGPL-2.1 OR MIT`, compiled
into the init; not in the plan's list), the init and the device trees
(`GPL-3.0-only`), the management module (`GPL-2.0-only`), BusyBox 1.36.1
(`GPL-2.0-only`) and musl 1.2.6 (`MIT`) by tarball and SHA-256, OpenSBI
v1.6 (`BSD-2-Clause`) and U-Boot v2022.10 (`GPL-2.0-or-later`), each
board's resident copy named as the human's firmware; the binary
distributed is none in every row, and the manifest states the rule for a
later distribution. `--check`, in `lint` beside `check-licenses.py`,
requires a row per source, output, and lock pin, each identifier's text
under `LICENSES/` and its mention in `COPYING`, B1's and B3's pins the
lock's, and the manifest a fresh generation byte for byte; its self-test
(10 cases) fails a planted source, output, and pin without a row, a
missing text, `COPYING` not naming one, a hand edit, an unstated pin,
and B1's or B3's pin other than the lock's. `LICENSES/` gains
`BSD-2-Clause` (OpenSBI v1.6's `COPYING.BSD`), `GPL-2.0-or-later` (U-Boot
v2022.10's `Licenses/gpl-2.0.txt`), and `LGPL-2.1` (Linux v7.2's), each
verbatim at its pinned commit under the kernel's header lines;
`check-licenses.py` counts the manifest's `licence` lines as uses
(`manifest=9`; three self-test cases, 16). The snapshot README's licence
row points to the manifest; `snapshot-check` passes.

**Item 115** (`ad345b4a`): `tools/platform-record.py`'s section "Console
input on K3" renders, from a board session's records, each typed
characterization's class, its results at 10 ms and 1 ms per byte, the
bytes received and typed, the polls and errors, and the verdict; each
repetition's nominal pacing (Q14), bytes, and the typist's measured
pacing; and each typed session's file and SHA-256, steps and keys typed,
hart 0's `:15` grants, `:16` lines, `:17` drops, and the checker's `:18`
accounting beside the keys (equal or differs). A record with neither
renders "Not run"; one with sessions alone says the characterization was
not run there; the PASS line gains `typed=characterizations:N,
sessions:M`; the schema stays v3 (the key `console` added as M7's and
M9's were). Eight self-test cases (16). A copy of M7's board record under
`build/` renders the section (class supplies at both pacings, 256 of 256,
repetitions at 11.7, 11.7, 11.7, and 2.7 ms; `two-guests-shell`, 16
steps, 100 keys, five `:16` lines, the `bad-sequence` drop, read 100
equal to the keys); the tool of `b5842520` renders it without.

### The M10 plan accepted; implementation started (2026-11-04)

The responsible human accepted the M10 plan at exact commit
`600b78c5198c7462ca76fdb30113f3770fdf5fa7` on 2026-11-04 by the
instruction `accept 600b78c5` (Q1 to Q15 at their defaults;
`planning/mvp-m10-plan-review-summary.md` is its review and acceptance
record) and said `proceed with development`. The acceptance authorizes
M10-2 to M10-7 on branch `beryllium/mvp-m10` from the acceptance-record
commit and is the M8 plan's required direction for the target digests'
re-write at `X4` (Q3); M10-2 (the re-proof at the base tree: stage 1
re-read and re-proved, the digests, the arms, `verify`) and M10-3 (the
tools: the campaign's session groups, items 115, 118, 121, and 122, the
licence manifest) started at once on `claude-opus-5.5` sub-agents in
worktrees, under the plan's thirteen stops and its 2,500-line soft
limit. The board campaign (M10-6) waits for the human's confirmation that
the board is free and their presence at the install and the restore; no
fast-forward or push was directed (the development branch stays at
`d776f324`). The same message confirmed the beryllium-cheri side's
integration of the guest log (`sidebar was imported`; that repository's
`main` at `5f45573`), and the human had pushed the refreshed snapshot
(the public `main` is `fc730b7`).

### The snapshot refreshed, the cheri sidebar imported, the M10 plan proposed (2026-11-04)

On `re-refresh then go` and `Import the beryllium-cheri sidebar`
(2026-11-04, 11:04 onward):

- **The public snapshot clone** (`beryllium-hypervisor-rc3`, beside this
  checkout) was refreshed from the development branch's `6ff17c67` by
  `BE_SNAPSHOT_SESSION=<this session> tools/snapshot.sh update 6ff17c67
  <dir>`, from the public tip `36e2590c` (the human had pushed it): one
  commit, `fc730b7` after the README's checks table was filled and the
  commit amended (unpushed; the published history is untouched), "(was
  f78f161c)", 516 files changed. Its checks ran in
  it one at a time with B1's OpenSBI build, B3's U-Boot build, and M7's
  BusyBox and musl tarballs linked into its `build/` (the clone has no
  network inputs of its own; `kernel-repro`'s Linux mirror as
  `LINUX_GIT`): `./mvp/mvp check` PASS (`BE_MVP_QEMU: PASS
  runs=64 attempts=83 refused=19`; `BE_MVP_SESSIONS: PASS sessions=6`;
  the capture checker `cases=300 mutations=459`; the references' self-test
  `cases=41`; `BE_MVP_LICENSES: PASS identifiers=3 files=963`;
  `BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=58 boundary=18`, its
  commits check skipped on the marker); `./mvp/mvp evaluate` PASS with no
  RPM cache (`rpms=259 sources=fedora:116,updates:115,updates-archive:28`,
  nine more builds having moved from `updates` to the archive since
  2026-11-01; `images=339 same=339`); `make -C model toolcheck unit run
  report-check proof differential` PASS through the input-ring proofs and
  then **FAIL by design** at stage 1's readings gate (item 127; the
  snapshot README says so and why), with `tests/differential.sh` run
  alone PASS (`comparisons=241`); not run: the U-Boot rehearsal,
  `kernel-repro`, and `verify`, each with its reason in the README. The snapshot README's checks table records
  them; the clone's `main` is for the human's own push. The refresh
  predates the sidebar import below, so the public snapshot does not hold
  `planning/sidebar-cheri-mvp.md`; a later refresh would.
- **The beryllium-cheri sidebar** was imported under the
  `cross-repo-collaboration` skill and the research repository's
  `COLLAB.md` "Consumer hints for Beryllium": branch
  `beryllium/cheri-sidebar-import` from `6ff17c67`,
  `docs/import/beryllium-planning.patch` (prepared there against this
  tip; reviewed by the human) applied cleanly, the page routed, and the
  instructions' stale Sail-H sentence corrected to the same fact;
  commit `c59003e7`, fast-forwarded onto the development branch as the
  directed import (the sidebar is non-authorizing research; CHERI stays
  the MVP 3.0 track). The guest log is appended in the research
  repository on `collab/beryllium-copilot-20261104-sidebar-import`
  (`8be864c`), for that repository's owner to integrate. The
  forbidden-phrasing patterns find nothing in the sidebar; the two
  findings in `cheri-alignment.md` predate the patch.
- **The M10 plan**, release candidate 4, is proposed at exact commit
  `600b78c5198c7462ca76fdb30113f3770fdf5fa7` on local branch
  `beryllium/mvp-m10-plan` from `c59003e7` (`planning/mvp-m10-plan.md`;
  `planning/mvp-m10-plan-review-summary.md` its packet): the eight gates
  from a clean checkout with stage 1 and `verify` green at `X4`; the
  re-proof at `X4` before any pin (stage 1 re-read and re-proved with
  every statement unchanged; `target-digests.txt` re-written at `X4` on
  the plan's acceptance; the suites at the base and at `X4` line for
  line); a 26-run board campaign at `X4`'s images with the three shell
  sessions typed under item 8 and the log judged in every run (M9's
  correlation boot four times over); the release surfaces through the
  ledger's release object; a per-component licence manifest
  (`tools/licence-manifest.py`, D-5); items 115, 118, 121, and 122
  (their dispositions of the morning, "M10's", become the plan's D-6);
  a 2,500-line soft limit; thirteen stops; Q1 to Q15. Awaiting the
  human's decision; nothing of M10 has run; no board command was issued
  (the board's availability for the night stands, unused).

### The M8 and M9 lines integrated into the development branch (2026-11-04)

On the instruction `go with ff & push, use your best judgment on
remaining issues` the two accepted lines were integrated. The development
branch `beryllium/single-hart-runtime-r0` was fast-forwarded from
`55047781` to the M9 acceptance record `680b6241` (the M9 line is linear
over the development tip, so its history is kept as it was accepted), and
the M8 acceptance record `0d103a38` was merged into it with one merge
commit, the integration record. The two lines share no monitor source
(M9 added `src/mvp-log.c` and `.h` and changed `mvp-runtime.c`,
`mvp-sbi.c`, `mvp-probe.c`, `mvp-platform.h`, `mvp.h`, and the linker
script, with their tests; M8 changed nothing under `src/` and added
`model/proof/Concrete*.v`, `verify/`, and the verifier's tools) and the merge is the union of their tools, tests,
records, and documents; eight files conflicted, every one a surface both
lines had appended to (`mvp/README.md`, this file; `mvp/docs/claim-ledger.json`
and its rendering; `mvp/tests/run-tool-dry-run.sh`;
`planning/.vitepress/config.mts`; `planning/HANDOFF.md`;
`planning/README.md`; `planning/roadmap.md`; `.github/copilot-instructions.md`),
and each was resolved to hold both lines' facts. Two resolutions are
substantive:

- **The claim ledger.** `tools/claim-ledger.py` requires contiguous IDs,
  and the lanes had each continued from C-50 and U-15 (item 124). The
  merged ledger takes M9's rows at their accepted numbers (C-51 to C-53,
  U-16, U-17; its refreshed pins C-10, C-16, C-40, C-41, C-48 and
  restated U-10, U-12, U-14) and appends M8's renumbered: **C-51 to C-55
  became C-54 to C-58** (the barrier and the gate, the single writer, the
  rings and the drain, the denial decision, management) and **U-16 became
  U-18**; M8's edits to the shared rows (U-11's litmus note, U-13's
  superseded text, C-06's re-read non-claim) are taken, their internal
  cross-reference "(C-52)" now "(C-55)"; `review_items` holds the three
  items, equal to `docs/claim.md`'s list (M9 added none). The rendering
  was regenerated and `claim-ledger check` passes with `claims=58
  boundary=18`. M8's evidence record, result packet, and plan decision
  record keep M8's numbers as assigned at acceptance (accepted records
  are not edited); read them with the mapping above; the ledger is the
  one source. Item 124 is closed.
- **The dry run's case list.** Both lines carried item 93's harness fix
  (M8 by cherry-pick, `f1813841`); M9's version is taken, since it also
  carries the `staged-sha256` case of item 116, and `fake-uboot.py`
  merged identically.

The merged tree's gates, the push, and the dispositions of the remaining
issues are in the entry that follows this one.

### The merged tree's gates, the push, and the remaining issues (2026-11-04)

The gates ran from the main checkout, clean at the integration record
`6095b179`, then at `e1b77cb1`, then at `331a0e9a`
(`build/mvp/integration-gates/`, `fix/`, and `fix2/`):

- `./mvp/mvp tool-lock check`: PASS.
- `./mvp/mvp check` at `6095b179`: **FAIL at `reference-check`**, a latent
  defect of M9's `tools/gen-reference.py --compare` (item 126, below): it
  keyed the two reference directories' files by basename, so in a tree
  where an earlier `evaluate` had left the evaluator's references under
  `build/mvp-evaluator/build/mvp/references/` it read
  `build/mvp/references/anchor-shell.json`, which is under `gcc/`, and
  raised. The accepted gates never met it because they run `check` before
  `evaluate` on a clean checkout, where the evaluator's directory does not
  exist yet and the target prints `none`. Fixed at `0fb76d15` (the pin of
  C-51 refreshed at `e1b77cb1`). `./mvp/mvp check` at `e1b77cb1`: **FAIL at
  the same target**, now comparing and finding 116 of 116 files
  differing: the evaluator's references were `6095b179`'s and every
  manifest embeds its source commit and tree state by design, so the
  gate's "compare when the evaluator's directory exists" was a staleness
  trap (item 128). Fixed at `3ac541d1` (the compare requires one source
  state on both sides and reports `stale` otherwise; C-51's pin refreshed
  at `331a0e9a`). `./mvp/mvp check` at `331a0e9a`: **PASS** (QEMU
  `runs=64 attempts=72 refused=8`; the capture checker `cases=300
  mutations=459`; `sessions=6`; the references 29 per toolchain, the
  tool's self-test `cases=41`; the evidence bundle `files=534 images=339
  log_exports=58`; the compare line `stale (the second directory's
  references are of e1b77cb1… clean; the first directory's of 331a0e9a…
  clean; not compared)`, the evaluator's directory then holding
  `e1b77cb1`'s references).
- `./mvp/mvp claim-ledger check`: PASS `claims=58 boundary=18`.
- `./mvp/mvp evaluate`: PASS at `6095b179`, at `e1b77cb1`, and at `331a0e9a`,
  339 of 339 images identical with the host's each time (the evaluator
  image `2875ddd675b4-009c2eba5655`); inside the evaluator the compare
  line is `none`, its tree having no evaluator directory of its own.
- `./be model-check`: **FAIL by design at stage 1's readings gate**
  (`model/tests/check-concrete-readings.sh`: 1 of 92 citations,
  `model/proof/Concrete.v:1627` reads `mvp/src/mvp-runtime.c:measure`,
  which M9 replaced with `measure_log()` and the per-domain launch gate);
  the Model 0.2 proofs, the policy and binding proofs, and the input-ring
  proofs pass before it. This is the drift the gate exists to catch, and
  the re-reading is M10's (S3-C.7: every M8 proof and arm re-run at RC4's
  tree before any pin is re-derived); item 127, below.
- `./mvp/mvp verify` was not run: its digests suite would stop at
  stop (i) of the M8 plan's D-2, since the merged tree moves two of the
  pilot's target digests (`mvp/src/mvp-sbi.c`, one line, the class name
  `log`; `mvp/src/mvp.h`); the re-proof is M10's with the readings. The
  accepted M8 result holds for the bytes its `target-digests.txt` names.

Pushed to the private `origin` after the gates: `beryllium/single-hart-runtime-r0`
(from `55047781` to `331a0e9a`, the commit recording this following it),
`beryllium/mvp-m8` (`0d103a38`),
`beryllium/mvp-m9` (`680b6241`), and `beryllium/mvp-m9-plan`
(`bc80b620`); `beryllium/mvp-m8-plan` was already at `6fbcc3d1` there.
The worker branches stay local. The stale worktree of debt sweep 5
(`worktrees/beryllium-hypervisor/rc3-review-remediation`, on the merged
`beryllium/mvp-debt-5`) was removed; the branch is kept.

The remaining issues, disposed under `use your best judgment` (each
disposition is recorded in its item; the human may reopen any):

- Item 107, the public snapshot's refresh shape: one commit per refresh
  stays. Its diff against the previous public commit is exactly the source
  range's change outside the exclusions, which is what "see what is
  changing" asks; replaying the private line's commits one by one would
  publish messages written for this repository (its PMR and `Copilot-Session`
  references, its merge records) and needs a tool change for no reader
  the snapshot has. Closed by judgement; the snapshot README's
  "fresh-history snapshot" wording is already true of each refresh.
- Items 118 (the cvc5 temporary files) and 122 (`rc-record.py`'s log
  export) go to M10's plan: both change the verifier's or the
  release-candidate record's tools, which M10 re-runs and re-records
  anyway, so one commit set holds the tool change and its run of record.
- Item 121 (the console tool's second `s` at a late prompt) goes to M10's
  board session: it is a code reading, not reproduced, in no board record,
  and a change to a board tool is characterized on the board with the
  human present before it is relied on; a dry-run case naming the fake's
  `after-prompt` record is written with the fix.
- Items 117 and 125 (WP with Z3's unsoundness; CN's and WP's tool limits):
  automation files no report upstream; a report is the human's own
  external act, and the records under `results/20261103-verify*/` are what
  it would cite. Open as the human's.
- The public snapshot (`main` at the human's last push) is not refreshed:
  a refresh publishes M7, M8, and M9 and is the human's `re-refresh`.
- M9's two board items (the read-only probe; the `anchor` correlation
  boot) and M10's plan (on `go`, from the development tip) are the
  human's. The human's `you have the k3 if needed overnight` (2026-11-04,
  02:2x) confirmed the board free; nothing in the integration needed it,
  and the correlation boot's install and restore need the human present
  (S3-A.1), so no board command was issued on that message.

### The public snapshot's history: normal deltas from now on (2026-11-01)

With the S3-C acceptance the responsible human gave a standing direction:
`note that from now on, we will push changes for the rc3 snapshot as
normal deltas, so people can see what is changing`. What the tool does
today: `tools/snapshot.sh update` replaces the clone's files in place and
commits once, so each refresh is already one commit on top of the public
tip whose diff against the previous commit is exactly the source range's
change outside the exclusions (`git diff 1ae5fd8c 6c71fa4c` in the public
repository shows debt sweeps 3 and 4 and nothing else); what it does not
give is the source commits one by one with their messages, authorship,
and dates. The rule in force from the direction: every change reaches the
public repository as a commit on top of its tip, pushed by the human as a
fast-forward; no reset, rewrite, or collapse (the fold of two unpushed
intermediate commits on 2026-11-01, made before the direction, was the
last, and `update` is run from the public tip from now on). The one
shape question, whether a refresh replays the source commits
individually (a tool change: each source commit's tree minus the
exclusions committed in turn with its message and a `Source-Commit:`
trailer, the README and `SNAPSHOT.txt` refreshed in the last), is item
107, for the human.

### Debt sweep 4: items 99, 100, 102, and 105, and `SECURITY.md` (2026-11-01)

On the responsible human's directions `add todo for the public rc3 repo:
add a security md file to note this is an early pre-release snapshot for
external review purposes only. any security issues may be openly filed
against the repo for now.`, `update the security.md as you feel best, fix
code issues`, and `then let's focus on updating the snapshot with fixes &
security md` (2026-11-01), branch `beryllium/mvp-debt-4` from the debt
sweep 3 acceptance record `b53c02a8` fixes the code defects among the
items the S3-C review processing had registered and writes the security
policy; no monitor source, claim statement, accepted plan text, or board
command. The commits, in order:

- **Item 100, the forged loader block** (`ed0c413d`). `tests/check-capture.py`'s
  uboot mode read U-Boot's load, digest, move, device-tree, and `Starting
  kernel` lines after the *last* autoboot line, so an image printing its
  own autoboot line and a forged block before its first marker had the
  forgery read. It now requires exactly one autoboot line (`k3-run.sh`
  slices each run's serial log from its reset; the QEMU rehearsal prints
  one) and reads after it; the finding is `N U-Boot autoboot lines before
  the markers, expected 1: one boot per run`. Four mutations (no autoboot
  line; a forged block after a second autoboot, board and QEMU, with and
  without the rest) are rejected: `self-test cases=133 mutations=321
  rejected=321`. `tools/k3-uboot.py attribution` reads after the first,
  allows at most one (none for the typed `run be_ld` of a
  characterization), and prints `autoboot_lines=N`; the dry run's two
  expectation lines carry it, and `run-tool-check` passes (27 cases). The
  40 retained RC2 and RC3 serial logs, re-judged read-only, each have
  exactly one autoboot line: no finding against any accepted record.
- **C-10's pin** (`01661500`): the ledger cites `check-capture.py` at
  `ed0c413d` (`b90d1bf5…`); re-rendered; `claim-ledger check` passes
  (item 97's two-commit shape again).
- **Item 102, the model gate's plural keywords** (`97874695`).
  `model/tests/run-proofs.sh`'s escape pattern and
  `model/tests/check-source-policy.sh`'s grep gain `Axioms`, `Parameters`,
  `Variables`, `Hypotheses`, `Conjectures`, and `Conjecture`; the new
  `model/tests/check-escape-pattern.sh` reads each pattern from its script
  and checks it against must-match and must-pass lines (the old patterns
  fail 12), and `make -C model toolcheck` runs it; `toolcheck`,
  `source-check`, and `proof` pass; no proof module changes. The gate
  files are accepted M3 bytes; `fix code issues` is the authorization, as
  the accepted-tool fixes of 2026-10-07 were authorized.
- **Item 105, the snapshot tool's trailer, and `evaluate`'s cache
  argument** (`f1bad063`). `tools/snapshot.sh` takes the `Copilot-Session`
  trailer from `BE_SNAPSHOT_SESSION` (`[0-9a-f-]{8,64}`) and omits it when
  unset, the `Co-authored-by` disclosure staying; the self-test makes with
  a session and reads it back, refuses a malformed id, and updates with
  none and finds no session line (`cases=33`). `tools/evaluator/evaluate.sh`
  exports an `MVP_RPM_CACHE=DIR` argument before the fetch, so the
  wrapper's `./mvp/mvp evaluate MVP_RPM_CACHE=DIR` and the environment form
  mean the same (the refresh above had found the argument form ignored).
- **Item 99, `SECURITY.md`** (`954b8f7f`). A root `SECURITY.md`, in the
  source tree so that every snapshot carries it unchanged: the snapshot is
  an early pre-release snapshot for external review only, one claim read
  with its required limit, not a release or supported software; report
  security issues openly as issues on the repository for now (no private
  channel, embargo, or coordinated disclosure), with the commit, the
  reproduction, the ledger row, and the finding's provenance, or write to
  the responsible human; fixes land in the private repository as exact
  commits and reach the snapshot on its next refresh from an accepted
  commit; no schedule, CVE, or advisory; the policy changes at the release
  path's later steps. The snapshot README template points at it, the
  snapshot self-test requires it and `COPYING` among the kept paths, and
  the root README's layout table names it.

Gates at the candidate, from a clean checkout, are in the packet
`planning/mvp-debt-4-review-summary.md`. Items 99, 100, 102, and 105 are
closed below; 101, 103, and 104 (Binding.v's readings, the VST route, Q38's
premise) are planning and proof matters for M8 and M9 and stay open; 94
to 97 stay open. **Exact commit `d162c60db4aab7bda77f2a557f91ac7446cca37c`
is responsible-human accepted as debt sweep 4 as of 2026-11-01**
(instruction `accept d162c60d & ff + push`); the
[review and acceptance record](../planning/mvp-debt-4-review-summary.md)
holds the decision, which confirms `fix code issues` as the authorization
for the two M3 gate scripts' change and `SECURITY.md` as written. The same
instruction fast-forwards the development branch
`beryllium/single-hart-runtime-r0` from `b53c02a8` to the commit recording
this and pushes it and `beryllium/mvp-debt-4` to the private `origin`; the
push of the public snapshot stays the human's.

### The RC3 snapshot refreshed from the debt sweep 4 packet (2026-11-01)

On `then let's focus on updating the snapshot with fixes & security md`,
`BE_SNAPSHOT_SESSION=<this session> tools/snapshot.sh update 03443dfc
<dir>` refreshed the human's local clone of the published snapshot
(`beryllium-hypervisor-rc3`, beside this checkout) in place from the
sweep's packet commit `03443dfc` (the candidate `d162c60d` with its packet
and registrations): one more commit,
`d4d3955dce1fdccef66a80842480c58479749429` on `main` over the unpushed
`3b6d76da`, two commits ahead of the published `1ae5fd8c`; its trailer
names this session, through the fixed tool, with no hand correction.
Every file but `README.md` and `SNAPSHOT.txt` is the source commit's blob
(`git ls-tree -r` compared over the 3,113 selected paths), the four
exclusions absent, no ELF object in the tree, `SECURITY.md` at the root
and named by the README. `update` replaces every file but `.git`, the
ignored `build/` included, so B1's pinned OpenSBI build was linked again
from this checkout before the checks. In it, on 2026-11-01 (17:57 to
18:11 UTC, one check at a time): `./mvp/mvp check` PASS (`BE_MVP_QEMU:
PASS runs=58 attempts=80 refused=22`; `BE_MVP_CAPTURE_SELF_TEST: PASS
cases=133`; `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=321 rejected=321`;
`BE_MVP_LICENSES: PASS identifiers=2 files=782`; the ledger `checks=9`
with its commits check skipped on the marker; the snapshot tool's
self-test skipped); `./mvp/mvp evaluate MVP_RPM_CACHE=<this host's
verified cache>` PASS with `images=253 same=253 differing=0`, the fetch
taking all 259 closure packages from the cache (`sources=MVP_RPM_CACHE:259`)
through the wrapper's argument form, which `f1bad063` makes work, so the
environment-form workaround of the earlier refresh was not needed; and
the model's own entry points, `make -C model toolcheck unit run
report-check proof differential`, PASS with the new escape-pattern test
among them. The U-Boot rehearsal and `kernel-repro` were not re-run (their
inputs are unchanged since 2026-10-31); the snapshot README's checks table
records all of this. The snapshot was made from the packet commit, before
the decision, as the direction asked for the fixes and the policy in the
snapshot now; the candidate it carries was accepted later the same day
(above), so its planning pages read "proposed" where this line reads
"accepted". It was not pushed, and the re-refresh below superseded it.

### The RC3 snapshot re-made from the acceptance record (2026-11-01)

On `re-refresh` (2026-11-01, after the acceptance), the clone's two
unpushed intermediate snapshot commits of the day (`3b6d76da`, of
`b53c02a8`, and `d4d3955d`, of `03443dfc`), both this automation's and
both superseded, were moved off `main` to the clone's local branch
`superseded-20261101` (reachable, not deleted, not to be pushed), `main`
was reset to the published `1ae5fd8c`, and `BE_SNAPSHOT_SESSION=<this
session> tools/snapshot.sh update 3e263059 <dir>` made the snapshot from
the debt sweep 4 acceptance record: one commit,
`6c71fa4c84c92f1dcb12b24f59109a959d1f2ed7` on `main` over `1ae5fd8c`,
"(was 3fe427b7)", so that the public history gains one commit for the
day rather than three and its planning pages read "accepted". Every file
but `README.md` and `SNAPSHOT.txt` is the source commit's blob (3,113
selected paths compared), the four exclusions absent, no ELF object,
`SECURITY.md` at the root and named by the README; the three accepted
records that mention a development path (the B3 and B5 READMEs' redaction
rule examples, the M1 packet's `sysroot_file`) were already in the
published snapshot, which had five such files. In it, on 2026-11-01
(18:36 to 18:50 UTC, one check at a time, B1's OpenSBI build linked in
again): `./mvp/mvp check` PASS (`BE_MVP_QEMU: PASS runs=58 attempts=70
refused=12`; `BE_MVP_CAPTURE_SELF_TEST: PASS cases=133`;
`BE_MVP_CAPTURE_MUTATIONS: PASS mutations=321 rejected=321`;
`BE_MVP_LICENSES: PASS identifiers=2 files=782`; the ledger `checks=9`
with its commits check skipped on the marker; the snapshot tool's
self-test skipped); `./mvp/mvp evaluate MVP_RPM_CACHE=<this host's
verified cache>` PASS with `images=253 same=253 differing=0`
(`sources=MVP_RPM_CACHE:259`, the argument form); `make -C model
toolcheck unit run report-check proof differential` PASS. The snapshot
README's checks table records all of this. The human pushed it the same
day (`done`): the public `main` is `6c71fa4c`.

### Debt sweep 5: the closure from public sources again (2026-11-01)

On the responsible human's `summarize item 95` and `do A` (2026-11-01),
branch `beryllium/mvp-debt-5` from the debt sweep 4 acceptance line
(`486fd5a9`) closes item 95. A read-only probe first (about 500 HTTP
`HEAD` requests, one 12 MB download): Fedora keeps every update build
pushed to stable for a supported release in a public **updates archive**
(`fedoraproject-updates-archive.fedoraproject.org/fedora/<release>/<basearch>/`,
flat, the `noarch` files under `x86_64` with the rest, `+` served only as
`%2B`), which the fetch tool did not try; all 259 closure NEVRAs were
served that day, 135 by the archive and 124 by the permanent release
repository, and the archive's `cpp-16.2.1-2.fc44` (the first of the 16
the fetch had found in no source) is byte-identical to the closure's
pinned SHA-256. The other remedies (publishing the verified cache; moving
the lock and closure to served builds; publishing the built image) were
laid out for the human, who chose this one, A.

- **`tools/evaluator/fetch-closure.py`** (`41c872b6`): the updates archive
  is the third source, after the `fedora` and `updates` repositories and
  before koji, through the curl path koji uses (`https_source`), the file
  name fully percent-encoded; the order is one function
  (`fetch_sources`), the seed directory first when `MVP_RPM_CACHE` names
  one. Nine self-test cases (archive URLs with an epoch dropped, a
  `noarch` file, the `+` and a `^` encoded; the order with and without a
  seed; through a faked curl, the archive and koji each serving one file
  under its own origin, a served file whose bytes are not the closure's
  refused and kept out of the cache, a failed transfer leaving no file):
  `cases=48`; against the old quoting rule or the old order the self-test
  fails. No trust change: a file still enters the cache only when its
  SHA-256 is the closure's, and the bytes are Fedora's signed ones.
- **The decisive test**, a cache-less fetch of the whole closure from
  public sources into a scratch directory under `build/` with
  `MVP_RPM_CACHE` unset (2026-11-01, 19:06:20 to 19:06:44 UTC):
  `BE_MVP_FETCH: PASS rpms=259 bytes=385621571
  sources=fedora:116,updates:124,updates-archive:19`, koji not needed;
  the log and `SOURCES.tsv` are kept under `build/mvp/tmp/` and the RPMs
  were deleted (the host's cache holds the same bytes).
- **The words that said otherwise**: this section's evaluator paragraphs,
  the file description below, the guide's section 8, and the snapshot
  README template's "How to run the checks" (a third party can now run
  `evaluate` from public sources; the verified cache is an optimization
  and the fallback).
- **Residuals** (item 106): the archive is Fedora's infrastructure, not
  the project's; when Fedora 44 reaches its end of life its release and
  updates repositories move to `archives.fedoraproject.org`, a later
  change to the two repository sources, and the verified cache stays the
  fallback for any build no public source serves. The accepted M0 plan's
  M0-B says "from Fedora's repositories or koji"; the archive is one of
  Fedora's repositories, read as within the letter and noted here.

Gates at the candidate, from a clean tree, are in the packet
`planning/mvp-debt-5-review-summary.md`. Item 95 is closed below; item
106 is opened. **Exact commit `e8ab73b712a974dc25d6cd8eab9bad24bd129405`
is responsible-human accepted as debt sweep 5 as of 2026-11-01**
(instruction `accept  & ff + push , and  re-refresh`, the reply to the
packet's request); the
[review and acceptance record](../planning/mvp-debt-5-review-summary.md)
holds the decision, which takes the M0-B reading (the updates archive is
one of Fedora's repositories) with no plan erratum. The same instruction
fast-forwards the development branch `beryllium/single-hart-runtime-r0`
from `486fd5a9` to the commit recording this and pushes it and
`beryllium/mvp-debt-5` to the private `origin`, and re-refreshes the
human's snapshot clone from the acceptance record (its record follows);
the push of the public snapshot stays the human's.

### The RC3 snapshot re-made from the debt sweep 5 acceptance record (2026-11-01)

On the same instruction, `BE_SNAPSHOT_SESSION=<this session>
tools/snapshot.sh update f78f161c <dir>` re-made the human's local clone
of the published snapshot (`beryllium-hypervisor-rc3`, beside this
checkout) from the debt sweep 5 acceptance record: one commit,
`36e2590c36d101a7f30ff3c44372aa99148078cd` on `main` over the published
`6c71fa4c`, "(was 3e263059)". Every file but `README.md` and
`SNAPSHOT.txt` is the source commit's blob (3,114 selected paths
compared), the four exclusions absent, no ELF object, the session trailer
from the tool. In it, on 2026-11-01 (21:05 to 21:19 UTC, one check at a
time, B1's OpenSBI build linked in, **no `MVP_RPM_CACHE`**): `./mvp/mvp
check` PASS (`BE_MVP_FETCH_SELF_TEST: PASS cases=48`; `BE_MVP_QEMU: PASS
runs=58 attempts=74 refused=16`; `BE_MVP_CAPTURE_MUTATIONS: PASS
mutations=321 rejected=321`; `BE_MVP_LICENSES: PASS identifiers=2
files=783`; the ledger `checks=9`, its commits check skipped on the
marker); `./mvp/mvp evaluate` PASS from a cache-less fetch,
`BE_MVP_FETCH: PASS rpms=259 bytes=385621571
sources=fedora:116,updates:124,updates-archive:19`, then `images=253
same=253 differing=0`, which is what a third party's `evaluate` does
today; `make -C model toolcheck unit run report-check proof differential`
PASS. The snapshot README's checks table records all of this and says
that no cache was given. It is not pushed: `git push origin main` from
that clone is the human's act, a fast-forward of the public `main` from
`6c71fa4c` by one commit.

## Files copied from B7

The plan's "Port and copies" table lists these as counted copies of B7's
files (`bringup/k3-b7/`, accepted at `7b6b846b`; its sources are unchanged
since), and the shim as a counted copy of B3's (`bringup/k3-b3/`, accepted
at `9b4860a0`). Counts are lines removed and added against the original, from GNU
`diff` (normal format). Each table sums to the file's diff totals. "Header
comment" counts every hunk in the file's header comment or docstring.
"Names only" counts the other hunks whose every changed line differs from
the original only by names: `b7`/`B7` becoming `mvp`/`MVP`,
`BE_B7_GUESTS` becoming `BE_MVP_DOMAINS`, the guest-prefix names becoming
domain-prefix names, `scripts/` becoming `tools/`, and the whitespace
realigned after the longer names. Rows group the remaining hunks by the
function, definition, or section in which they start, so a row can carry
a few lines of the neighbouring change.

M5-2 and M5-3 (to `154dc810`) changed eight of the copies and removed or
renamed four, and the counts below are not recounted for them: removed are
`tests/kexec-rehearsal.sh`, `tests/kexec-rehearsal/init.c`, and
`tools/kexec-load.py`, whose read-only probe and layout rule moved to the
new `tools/platform-probe.py`; `tests/test-kexec-load.py` became
`tests/test-platform-probe.py`; and `tools/k3-run.sh`,
`tools/k3-campaign.sh`, `tools/k3-preflight.sh`, `tests/fake-board.py`,
`tests/run-tool-dry-run.sh`, `tools.mk`, the `Makefile`, and
`tests/check-image.py` changed (`git diff --numstat 9b3fa982 154dc810`:
203 and 677, 78 and 185, 122 and 43, 187 and 263, 832 and 1,449, 227 and
219, 40 and 3, and 96 and 1 lines inserted and deleted). Their entries
below, and the totals, are as M4 left them.

M6-2 (to `356150bb`) changed eleven of the copies and added one. Eight
are recounted by the method below from their rows at `366c8af4`, the
M6 base, each row's text naming M6-2's change (or that only the diff's
alignment moved it): `tools/port.py`, `src/mvp-layout.h`,
`src/mvp-runtime.c`, and `src/mvp-platform.h` (4, 1, 0, and 0 more
hunks; 0, 1, 86, and 0 more lines removed; 435, 18, 87, and 1 more
added), and `src/mvp-payload.h`, `src/mvp-payload.c`,
`tests/payload-test.c`, and `src/mvp-trap.S`, whose counts M6-2's
changes, inside lines already changed, leave as they were. Three that M5
left uncounted stay so: `Makefile`, `tests/check-image.py`, and
`tests/run-tool-dry-run.sh` (`git diff --numstat 366c8af4 356150bb`: 51
and 21, 209 and 193, and 2 and 2 lines inserted and deleted). The new
copy, `src/mvp-monitor.lds`, is counted against its origin, the MVP
port's `arch/riscv/be/r5-beryllium.lds` as `tools/port.py` makes it
(SHA-256 `56b7120ec744869ac50be9cc059b65babc49263ae578b27e1e11f2b67af3a7d9`,
366 lines), with no name counted as a name. The totals above stay as M4
left them.

M6-3 (to `acda84bc`) changed five of the copies. Two are recounted from
their rows at M6-2 by the same method, each row's text naming M6-3's
change (or that only the diff's alignment moved it): `src/mvp-runtime.c`
(one hunk fewer; 11 more lines removed and one more added than its rows
at M6-2, which summed to five added lines fewer than its copy had then;
see its entry) and `src/mvp-monitor.lds` (4 more lines added). Three that
M5 left uncounted stay so: the `Makefile`, `tests/check-image.py`, and
`tests/run-tool-dry-run.sh` (`git diff --numstat 53c9ad8e acda84bc`: 15
and 11, 76 and 32, and 2 and 2 lines inserted and deleted). The totals
above stay as M4 left them.

At the M4-1 content (`30800dd3`) the 44 total 32,190 copy lines and 21,571
added, and M0-1 and M0-2's 26, which hold the `Makefile`, 18,526 and
13,167; every other count is as at the M2-7 content below. M4-1 changed
one copy, the `Makefile` (23 lines inserted and 4 deleted against
`18d552bc`; in its count 19 more added lines, in rows 0 and 6, and no
other change), and M4-2 and M4-3 changed none.

At the M2-7 content the 44 copies total 17,008 original lines and 32,171
copy lines: 2,052 hunks, 6,389 lines removed, 21,552 added, and 10,619
unchanged. M0-1 and M0-2's 26 are 9,272 and 18,507: 1,243 hunks, 3,913
removed, 13,148 added, 5,359 unchanged; M0-3's eight are 4,675 and
8,107: 532 hunks, 1,664 removed, 5,096 added, 3,011 unchanged; M0-4's
ten are 3,061 and 5,557: 277 hunks, 812 removed, 3,308 added, 2,249
unchanged. M2 (M2-1 to M2-5 and Plan revision M2-A) changed 34 of the 44:
`git diff --stat 35ebe8a7` against the M2-7 content over the 34 counts
6,129 lines inserted and 766 deleted, 5,363 more copy lines; in the
count, 33 more hunks, 48 more lines removed, 5,411 more added, and 48
fewer unchanged. M2-A changed one of them, `tests/run-tool-dry-run.sh`
(29 lines inserted and 11 deleted against `da7d270f`; in its count one
hunk fewer, one more line removed, 19 more added, and one fewer
unchanged), and M2-7 none. At the M2-5 content (`da7d270f`) the 44
totalled 32,153 copy lines: 2,053 hunks, 6,388 removed, 21,533 added, and
10,620 unchanged; M0-4's ten 5,539: 278 hunks, 811 removed, 3,289 added,
2,250 unchanged; every other count as at the M2-7 content. M2-1 to
M2-5's `git diff --stat 35ebe8a7` over the 34 counted 6,111 lines
inserted and 766 deleted, 5,345 more copy lines; in the count, 34 more
hunks, 47 more lines removed, 5,392 more added, and 47 fewer unchanged.
The other ten are as M1 left them: `tools/gen-payload.py`,
`tools/guest-reference-check.py`, `tools/run-reference-boot.sh`,
`guest/mvp-guest.dts.in`, `guest/ref-stub.S`, `src/mvp-boot.lds`,
`src/mvp-guest-payload.S`, `shim/mvp-shim.S`,
`tests/kexec-rehearsal/init.c`, and `tests/fake-board.py`.
At the M1-6 content (`17ed82f7`, whose copies M2's base `35ebe8a7`
keeps) the 44 totalled 26,808 copy lines: 2,019 hunks, 6,341 removed,
16,141 added, and 10,667 unchanged. M0-1 and M0-2's 26 were 14,570: 1,221
hunks, 3,859 removed, 9,157 added, 5,413 unchanged; M0-3's eight 6,998:
523 hunks, 1,670 removed, 3,993 added, 3,005 unchanged; M0-4's ten 5,240:
275 hunks, 812 removed, 2,991 added, 2,249 unchanged. M1
(M1-1 to M1-6 and Plan revisions M1-A and M1-B) changed 33 of the 44: `git
diff --stat 41f88795` against the M1-6 content over the 33 counts 6,746
lines inserted and 648 deleted, 6,098 more copy lines. M1-6 changed one of
them, `tests/run-tool-dry-run.sh` (68 lines inserted and 7 deleted against
`804cd24c`, 61 more added lines in its count). The other eleven were as M0
left them. At `804cd24c` the 44 totalled 26,747 copy lines and 16,080
added, M0-4's ten 5,179 and 2,930, every other count as at the M1-6
content.
At M0's accepted result (`b2669725`, whose `mvp/` tree M1's base
`41f88795` keeps) the 44 totalled 20,710 copy lines: 1,918 hunks, 6,237
removed, 9,939 added, and 10,771 unchanged. M0-1 and M0-2's 26, with the
`Makefile` as it then stood, were 10,682: 1,191 hunks, 3,794 removed,
5,204 added, 5,478 unchanged; M0-3's eight, with `tests/run-qemu.sh` and
`src/mvp-runtime.c` as they then stood, 6,380: 491 hunks, 1,645 removed,
3,350 added, 3,030 unchanged; M0-4's ten, with `tests/run-tool-dry-run.sh`
as it then stood, 3,648: 236 hunks, 798 removed, 1,385 added, 2,263
unchanged. Before M0-6 (and after M0-C) the 44 totalled 20,610 copy lines
and 9,839 added, `tests/run-tool-dry-run.sh` counted at 497 lines before
the `same-second` case (30 lines) was added after M0-C's review; M0-6 adds
70. Before M0-C the 44 totalled 20,590 copy lines: 1,920 hunks, 6,236
removed, and 9,818 added. At M0-A (`ebae089d`) the 34 then copied totalled
17,136 copy lines: 1,691 hunks, 5,414 removed, and 8,603 added; at M0-3
(`79217ea2`), 16,299: 1,667 hunks, 5,338 removed, and 7,690 added.
B7's `scripts/` become `tools/`. Reused unchanged by path, and so not
listed: B2's `scripts/port.py` and its pinned output, B6's
`scripts/fetch-linux.sh` and `guest/b6-kernel.config`, B1's
`src/b1-handoff.S`, which every image links, and B3's
`tests/check-b3-image.py`, which the image checker loads for B3's header
and descriptor rules; and B0's `tests/retain-results.py`,
`tests/summarize-runs.py`, and rehearsal `mkcpio.py`, which M0-4's tools
run. Not copied: B7's scheduler and its test (M0 has none), and its marker
and capture checkers (`tests/check-b7-markers.py`,
`tests/check-b7-capture.py`), which M0-4's new capture checker replaces.
Rows for M0-3's and M0-4's copies, and for the `Makefile` and
`tests/run-qemu.sh` (recounted at M0-4, the `Makefile` again at M0-B, and
`tests/run-tool-dry-run.sh` again at M0-6 and at `804cd24c`), use
the same method, but also count as names `k3-b7`, `K3 B7`, and `K3_B7`
becoming `mvp` and `MVP`, `guest` becoming `domain`, and (M0-4)
`check-b7-` becoming `check-`; B3's `b3` names are not counted as names,
and M0-4's copies keep B7's names where they name B7's records
(`B7_PREFLIGHT`, `B7_IOMEM`). Plan revision M0-A's changes are counted by
each file's method into its rows, whose text names the revision's part
(M0-A.1, M0-A.2, or M0-A.3), and so is Plan revision M0-C's change to
`src/mvp-runtime.c` (M0-C.1); its two changed `Makefile` lines, the hart
test's pinned counts, lie inside added lines and change no count. M1's
changes are counted the same way into each file's rows, whose text names
the work package or revision (M1-1 to M1-5, M1-A, or M1-B); a row that
M1's change left empty is joined to the row whose hunk took its lines,
and the file's entry says so. Each M1 row was derived from the `41f88795`
rows: the hunks M1 removed taken from their rows, and each hunk it added
placed by the rule above. A change that starts before a file's first row
opens a row of its own. The diff can also align a few unchanged lines
differently once a file changes, which moves a few lines between
neighbouring rows and out of "Names only". M2's changes are counted the
same way, each row derived from the `35ebe8a7` rows (the M1-6 content's,
which every entry reproduced before M2's were placed), and the text names
the work package (M2-1 to M2-5, M2-4's follow-up with M2-4). M2 left
two rows empty, each joined as above: `src/mvp.h`'s exit-handling
constants (M2-3) and `guest/pins.txt`'s pins (M2-4); and it opened one,
`tools/guest-pins.py`'s row 2 (M2-4), the first change to that file
beyond its header and names. A row whose numbers M2 changed only through
the diff's alignment names no M2 change. Plan revision M2-A's change to
its one copy, `tests/run-tool-dry-run.sh`, is counted the same way from
that entry's rows at the M2-5 content, and the text names it (M2-A).

### `tools/port.py` (from B7's `scripts/port.py`)

Original 199 lines, copy 763; 26 hunks, 43 removed, 607 added, 156 unchanged. The MVP names, one more rule, the hart region, and the MVP region's six rules (Plan revision M0-A.1); M2-2 names `mvp-sha256.o` among the MVP region's objects, inside row 3's added lines, which changes no count; M6-2's MVP core profile: its 43 rules and the span rule. Since M6-2 the diff aligns the pool's `ASSERT`s (6 lines each side) on their own, names only, out of row 3.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the MVP core profile's rules (M6-2) | 17 | 54 |
| 1 | Names only | 20 | 20 |
| 2 | Names, the MVP pool comment, and the pool's `ASSERT`s with MVP symbols | 3 | 3 |
| 3 | The hart-region rule: the NOLOAD `.hart.mvp` section at `0x1_0204_4000`, `0x20000` bytes, with three `ASSERT`s (its start and end, 16 KiB alignment, its place after the pool); and the MVP region's six rules (M0-A.1): the `mvp_text`, `mvp_ro`, and `mvp_data` PT_LOAD entries, the MVP C objects excluded from `.monitor.text`, `.monitor.rodata`, and `.monitor.data` by one `EXCLUDE_FILE` per section pattern, and `.mvp.text`, `.mvp.rodata`, and `.mvp.data` (data, then BSS) at `0x1_0206_4000` with three `ASSERT`s; and their rows in `RULES`; `mvp-sha256.o` among the objects (M2-2); the MVP core profile's rules (M6-2): `manifest.h`'s limits, harts, VMID bound, profile, and hart fields, `manifest.c`'s validation with its replaced channel and authority functions, `r3.c`'s boot check without the fixture extents, and `r5-entry.S`'s stack, with their rows in `RULES` | 0 | 518 |
| 4 | `derive`: a span rule's text, from its first line through its last, must hash to its pinned SHA-256 (new, M6-2) | 0 | 9 |
| 5 | The `--inputs` root and the manifest's MVP heading | 3 | 3 |
| | **Total** | **43** | **607** |

### `src/mvp-layout.h` (from B7's `src/b7-layout.h`)

Original 151 lines, copy 411; 25 hunks, 113 removed, 373 added, 38 unchanged. The hart region and blocks, the harts, the ring sizes, M0's run limits and waits, no slice, SBI version 3, and M0-A's MVP region, flat image, and drain delay; M1-2's channel page and each root's level-0 page, and Plan revision M1-B's restarting acknowledgement window (a comment); M2-2's three shared pages, M1's channel page their first, and the secret's size; M6-2's core, its data, and hart 0's stack. Since M1-2 the diff joins the flat image, the pool comment, and the harts, three rows at M0, into one hunk; since M6-2 it opens one more hunk in row 3.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, naming the channel page and each root's level-0 page (M1-2), the three shared pages and the secret's size, and the MVP line from M0 to M2 (M2-2), the core and the line to M6 (M6-2) | 12 | 20 |
| 1 | Names only | 12 | 12 |
| 2 | One hunk since M1-2: the monitor flat image (M0-A.1): the accepted image's `0x34000` bytes renamed `BE_MVP_ACCEPTED_IMAGE_BYTES`, and the flat image's `0xa4000` bytes; the pool comment, with each root's level-0 page after its level-1 page (M1-2); harts and the hart region (new): the control and domain harts, eight harts, each block's pages and rings, the high-water budget, the generation word; the VMIDs and `hgatp` values kept, and each root's level-0 page (M1-2); the MVP region's address and size and Fedora's kernel address (M0-A.1); the core (M6-2): `BE_MVP_CORE_BYTES` `0x34000`, the data at `0x1_0200_8000` (`0x8000` bytes), and hart 0's stack at `0x1_0201_0000` (`0x2000` bytes), with `BE_MVP_ACCEPTED_IMAGE_BYTES` kept, as the board tools' layout rule reads it | 23 | 97 |
| 3 | Staging, loader, window, and guest placement (mixed hunks with names), the kernel at boot-image offset `0xa5000` (M0-A.1); the channel page (M1-2): at most one, GPA `0x84000000`, HPA `0x118000000`, 4 KiB; since M2-2 the first of the shared pages (`BE_MVP_SHARED_PAGES_HPA` `0x118000000`, `BE_MVP_SHARED_PAGES_BYTES` `0x3000`, `BE_MVP_PAGES_MAX` 3) and the secret's `BE_MVP_SECRET_BYTES` (`0x20`), a v3 scenario mapping only the pages it declares; the run limits (Q11), the start, READY, and acknowledgement waits (Q10; the acknowledgement window restarts on hart 0's progress, Plan revision M1-B), the variants' values with the `ring-full` drain delay (M0-A.3), and the SBI identity (Q3), replacing B7's slice; the kexec FDT slot's comment, the slot the board tools' staging region keeps (M6-2) | 42 | 77 |
| 4 | Static assertions: the pool after the accepted image, the per-domain pools, harts that exist and differ, the hart-start variant's absent hart, the region after the pool, its blocks and their pages in order, power-of-two rings, the variant ring, the high-water budget, the region below the staged image and the windows, the MVP region after the hart region, ending the flat image, 16 KiB aligned, and below Fedora's kernel and the staged image, the kernel after the flat image (M0-A.1), the budget in seconds, the waits, and the drain delay beyond the acknowledgement wait (M0-A.3); each level-0 page after its level-1 page and in its own pool, and the channel page: one 4 KiB-aligned page directly above G1's window, outside every other extent, at the GPA directly above each window, in the windows' root entry and level-1 table at index 32, level-0 index 0 (M1-2); since M2-2 the shared pages: three 4 KiB-aligned 4 KiB pages and a secret that fits one, M1's channel page their first, directly above G1's window and outside every other extent, at GPAs directly above each window, all behind the one level-1 entry, from level-0 index 0; since M6-2 the pool after the core and the core's layout: code below `0x1_0200_8000`, data, then hart 0's stack | 24 | 167 |
| | **Total** | **113** | **373** |

### `src/mvp.h` (from B7's `src/b7.h`)

Original 714 lines, copy 1388; 115 hunks, 440 removed, 1114 added, 274 unchanged. The IPI class, per-hart state, LINE records instead of console writes, the record types and their payloads, no `wfi` or slice class, and version 3 unchanged; M1-3's denial entry, decision, injected values, and DENIAL record, and Plan revision M1-B's ACK wait; M2-2's `measurement` class and grant permission bits, and M2-3's management extension (its identity, results, records, classes, phases, state, sealed grants, and contracts), version 4 in an image with it, and the denial decision over every page's leaf. Since M2-3 the diff joins the SBI constants' last hunk and the exit-handling constants, two rows at M1, into one hunk.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the denial entry, the DENIAL record, and the ACK wait (M1-3, M1-B), and the management extension (M2-3) | 14 | 27 |
| 1 | Names only | 65 | 65 |
| 2 | SBI constants: the Base identity comment; the management extension (M2-3): EID `0x08004245`, FID 0 `pause` and FID 1 `terminate`, implementation version 4 (`BE_MVP_SBI_IMPL_VERSION_MGMT`), `SBI_ERR_INVALID_STATE` (-10), at most four grants, and `BE_MVP_MGMT_DELIVER`, beside a grant's permission bits (M2-2); run limits per domain with the budget on hart 0, and `no-grant-check`'s 2^27 ticks (M2-3); one hunk since M2-3 with exit handling: the supervisor software interrupt is the IPI, B7's timer and `wfi` constants removed; the per-hart console whose lines leave as LINE records (an 11-byte prefix, the printed line, `FULL`) | 47 | 86 |
| 3 | Guest controls: VTW clear (`0x180`), `sie` = SSIE on domain harts and SSIE and STIE on hart 0, the `hvip` comment; the denial entry's constants (M1-3): `hstatus.GVA`, the `vsstatus` bits, the `htval` and `htinst` limits, the transformed instruction's opcodes, `vstvec`'s modes, and the two kinds a DENIAL names, a read-only store to any page (M2-3) | 20 | 54 |
| 4 | Structures (one large hunk): the controls and exit record per hart, with the exit's `vsstatus` (M1-3); `enum be_mvp_vcsr`; classes without `switch` and `scheduler`, with `run-timeout`, `firmware`, `hart-start`, `hart-ready`, `ring`, and `ipi`, and `measurement` (M2-2) and `mgmt` (M2-3); phases per hart, with `PAUSED` and `TERMINATED` (M2-3); actions `IPI` and `SHUTDOWN` replacing `WFI`, `SLICE`, and `STOP`, and `DENY` (M1-3) and `MGMT` (M2-3); the record types with DENIAL (M1-3) and MGMT_REQUEST, PAUSED, TERMINATED, MGMT_RESULT, PAUSE, and TERMINATE (M2-3), ring masks, and payload word indices (new), with SHUTDOWN's denial count and DENIAL's twelve words (M1-3), and SHUTDOWN's management count, word 13, and the new records' words (M2-3); B7's `struct be_b7_vcpu` and per-guest state removed | 140 | 331 |
| 5 | Counters per hart with `ipi`, `lines`, and `denials` (M1-3), and `mgmt` (M2-3); the console and state of one hart (no run time budget or guest index), with `accept_denial` (M1-3), and `accept_mgmt`, `by`, `awaiting`, and `answer` (M2-3); new `struct be_mvp_mgmt_grant` and `enum be_mvp_target_state` (M2-3); new `struct be_mvp_denial` and the injection helper's four words (M1-3); the result, with its denial (M1-3), and a management call's function and target (M2-3); the line comment | 47 | 155 |
| 6 | Exit contracts: the ring view; the controls check (SSIE, VTW clear); `be_mvp_classify_cause` for every exit but the IPI; new `be_mvp_denial_decide` (M1-3), over every page's walked leaf (M2-3); `be_mvp_handle_exit` per hart, with the walked channel leaf and the denial (M1-3), every page's leaf and the management call (M2-3); new `be_mvp_ipi_serve`, with PAUSE and TERMINATE (M2-3) | 36 | 98 |
| 7 | Exit-record contracts: new `be_mvp_wait_serve` and `be_mvp_mgmt_decide` (M2-3), in one hunk with `be_mvp_counts_sbi` (with `mgmt`, M2-3) and new `be_mvp_inject_words`, `be_mvp_inject_mismatch`, and `be_mvp_inject_vcsr` (M1-3); `be_mvp_apply_return` (the IPI changes nothing; a management call's answer once the runtime has it, M2-3), the entry frame, SPP, and the CSR set written once at arming; B7's vCPU init, save, and restore removed | 25 | 115 |
| 8 | The console and records: `be_mvp_domain_prefix`, `be_mvp_console_feed` and `be_mvp_console_flush` posting LINE records; new `be_mvp_post_ready`, `_entered`, `_shutdown` (with the domain's denials, M1-3, and its management calls, M2-3), `be_mvp_post_denial` (M1-3), `be_mvp_post_mgmt_request` (M2-3), and `_fail`; the ACK wait, `be_mvp_ack_wait_start` and `be_mvp_ack_wait_step` (Plan revision M1-B), which a requester's wait steps too (M2-3) | 45 | 181 |
| 9 | The line builder's comments | 1 | 2 |
| | **Total** | **440** | **1114** |

### `src/mvp-sbi.c` (from B7's `src/b7-sbi.c`)

Original 609 lines, copy 1269; 118 hunks, 353 removed, 1013 added, 256 unchanged. The IPI class and its PING and PONG, LINE records, the record builders, the firmware result checks with `BE_MVP:02`'s census, and no `wfi` or slice class; M1-3's denial decision, injected values, and DENIAL record, and Plan revision M1-B's ACK wait; M2-3's management extension: the call, the records a hart takes while it waits, paused, or terminated, hart 0's decision, and the denial decision over every page's leaf.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the denial decision, DENIAL, and the ACK wait (M1-3, M1-B), and the management extension (M2-3) | 8 | 19 |
| 1 | Names only | 140 | 140 |
| 2 | Includes; static assertions (`0x180`, SSIE, the printed line, the word records, a full line as one LINE; the exit record's 360 bytes with `vsstatus` at 352, DENIAL's 112 bytes, and the denial entry's constants, M1-3; versions 3 and 4, MGMT_REQUEST's words, PAUSED and TERMINATED sharing their words, and delivery no SBI result, M2-3); the class names, with `measurement` (M2-2) and `mgmt` (M2-3) | 40 | 86 |
| 3 | `be_mvp_controls_valid`: `sie` = SSIE; `be_mvp_classify_cause`'s names, now in one hunk with new `be_mvp_denial_decide` (M1-3): the plan's entry, the transformed `htinst` rule, the window and channel-page tests, and the access fault each cause injects; since M2-3 the page whose walked leaf holds the GPA (`leaf_at`) in place of the channel page | 9 | 135 |
| 4 | The Base probe (M2-3): the management extension available only in an image that accepts it (`accepts_mgmt`), and that image's implementation version 4; DBCN and SRST: a shutdown with reason 0 stops only the calling hart (`SHUTDOWN`); new `sbi_mgmt` (M2-3): `pause` or `terminate` of the target in `a0` a request, any other FID `SBI_ERR_NOT_SUPPORTED` on the hart; a management call counted in `mgmt` (M2-3) | 35 | 66 |
| 5 | `be_mvp_handle_exit`: one hart's state and ceiling, no time budget; the IPI; a guest-page fault offered to the decision, and an accepted one counted (M1-3), with every page's leaf (M2-3); B7's slice and idling `wfi` removed | 38 | 36 |
| 6 | SRST counting and the management extension's dispatch (M2-3); new `be_mvp_ipi_serve`: each PING a PONG, an empty ring or another record `ipi`, a malformed or full ring `ring`; since M2-3 through `serve_record` and `serve`: PAUSE answered with PAUSED and TERMINATE with TERMINATED in an image with the extension, and new `be_mvp_wait_serve`, the requester's wait: a PING answered with a PONG of SPV 0, its MGMT_RESULT taken, a paused hart taking only TERMINATE | 3 | 184 |
| 7 | `be_mvp_counts_sbi` with `mgmt` and new `be_mvp_mgmt_decide` (M2-3), in one hunk with new `be_mvp_inject_words`, `be_mvp_inject_mismatch`, and `be_mvp_inject_vcsr` (M1-3); `be_mvp_apply_return` without `wfi`, and with a management call's answer (M2-3); the CSR set without B7's vCPU init, save, and restore | 36 | 78 |
| 8 | `be_mvp_domain_prefix`; the console posts LINE records (`post_line`, `be_mvp_console_feed`, `be_mvp_console_flush`) instead of writing lines; new `be_mvp_post_ready`, `_entered`, `_shutdown` (with the domain's denials, M1-3, and management calls, M2-3), `be_mvp_post_denial` (M1-3), `be_mvp_post_mgmt_request` (M2-3), `_fail`, the ACK wait's start and step (Plan revision M1-B), the HSM and IPI result checks, `BE_MVP:02`'s census (M0-A.2), and the line builder's place | 44 | 269 |
| | **Total** | **353** | **1013** |

### `src/mvp-gstage.h` (from B7's `src/b7-gstage.h`)

Original 187 lines, copy 568; 34 hunks, 90 removed, 471 added, 97 unchanged. Names and a hart field per root; M1-2's channel page: its records, the build and walk with a level-0 page, and the channel check; M2-2's declared pages: their kinds, records, walked leaves, build, walk, and check.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the channel page (M1-2) and the declared pages (M2-2) | 10 | 21 |
| 1 | Names only | 16 | 16 |
| 2 | The geometry (M1-2): the channel's 4 KiB leaf in a level-0 page after the level-1 page, its offset and 512 entries, and the spare after it; the window leaves' flags comment; a channel endpoint's rights (read, write, and execute, which is only refused), whose leaf flags follow the authority report's table; in hunks that now take in the constants' names; a page's kinds, channel and secret, and no page (M2-2) | 26 | 57 |
| 3 | The descriptor and the map gain `hart`; new `struct be_mvp_gstage_page`, `_leaf`, `_channel`, and `_refusal`, the channel errors, `be_mvp_gstage_build_channel`, `be_mvp_gstage_walk_channel`, and `be_mvp_gstage_channel_check` (M1-2); the pair check refuses equal harts and the control hart; since M2-2 M1's page record renamed `struct be_mvp_gstage_root_page`, new `struct be_mvp_gstage_page` (one declared page: GPA, HPA, size, kind, writer, reader, each domain's rights) and `_leaves`, the page refusal's fields, and new `be_mvp_gstage_build_pages`, `be_mvp_gstage_walk_pages`, and `be_mvp_gstage_page_check` | 38 | 377 |
| | **Total** | **90** | **471** |

### `src/mvp-gstage.c` (from B7's `src/b7-gstage.c`)

Original 298 lines, copy 1047; 51 hunks, 150 removed, 899 added, 148 unchanged. Names and a hart field per root; M1-2's channel leaf in a level-0 page, its walk, the channel check, and the `reader-write` variant's builder defect; M2-2's declared pages: each root's leaves built from their records and walked, the page check, and the `secret-shared` and `response-writable` builder defects. Since M2-2 nine lines of names-only change lie inside the pages' hunks, in rows 2 and 3.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the channel page (M1-2) and the pages (M2-2) | 5 | 13 |
| 1 | Names only | 51 | 51 |
| 2 | The level-0 index, the channel leaf's flags, the `reader-write` variant's builder defect (W and D in the reader's leaf), and their static assertions; the page check, the builder's level-1 pointer and level-0 leaf, and the walker's level-0 step (M1-2), in hunks that now take in their names; since M2-2 the page builder's two defects, `secret-shared` (the secret page in the host's root) and `response-writable` (W in the host's response leaf), the pages' static assertions, the builder split into the window, the level-0 pointer, and each page's leaf, new `be_mvp_gstage_build_pages` with each leaf's flags from its record's rights (`page_flags`), and the walker's level-0 step over every page | 51 | 342 |
| 3 | The walker's zeroed map and its `hart`, and its walked channel leaf (M1-2); the pair check refuses equal harts and the control hart; new `be_mvp_gstage_channel_check`: the sealed record's validity, each root's declared leaf, and every page the two roots share (M1-2); new `be_mvp_gstage_walk_pages` (M2-2), and new `be_mvp_gstage_page_check` (M2-2): each page's declared leaf derived from its record (`endpoint_rights`, `declared_page_leaf`), no leaf for a domain without rights, the records' own rules (`pages_refused`), and the refusal's fields | 43 | 493 |
| | **Total** | **150** | **899** |

### `src/mvp-payload.h` (from B7's `src/b7-payload.h`)

Original 162 lines, copy 165; 21 hunks, 74 removed, 77 added, 88 unchanged. Names, and the staged image kept off the hart region, the MVP region, and (M1-3) the channel page, since M2-2 the three shared pages.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 3 | 3 |
| 1 | Names only | 51 | 51 |
| 2 | The kernel offset's comment (`0xa5000`, M0-A.1) | 1 | 1 |
| 3 | The error and check comments: the hart region, the accepted image (since M6-2 the monitor's core), and the MVP region (M0-A.1), and the channel page (M1-3), since M2-2 the shared pages | 19 | 22 |
| | **Total** | **74** | **77** |

### `src/mvp-payload.c` (from B7's `src/b7-payload.c`)

Original 203 lines, copy 211; 45 hunks, 79 removed, 87 added, 124 unchanged. Names, and the staged image kept off the hart region, the MVP region, and (M1-3) the channel page, since M2-2 the three shared pages.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 3 | 3 |
| 1 | Names only | 72 | 72 |
| 2 | `window_valid` refuses a staged image on the hart region and the MVP region (M0-A.1) and on the channel page (M1-3), since M2-2 on the three shared pages, and names the accepted image's size, since M6-2 the core's | 4 | 12 |
| | **Total** | **79** | **87** |

### `tests/sbi-test.c` (from B7's `tests/b7-sbi-test.c`)

Original 2273 lines, copy 4375; 283 hunks, 1294 removed, 3396 added, 979 unchanged. Adapted to per-hart state, the IPI, LINE records, and the records, with `BE_MVP:02`'s census; B7's slice, `wfi`, time-budget, and switch tests removed. M1-3 adds the walked channel leaf to every exit, the denial entry's decisions, and the DENIAL records; Plan revision M1-B the ACK wait's tests; M2-3 every exit's walked page leaves, the management extension's decision, calls, waits, records, and counts. M2-3 changed rows 5, 6, and 8 only by the diff's alignment around its other changes.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the denials, the DENIAL records, and the ACK wait (M1-3, M1-B), and the management extension (M2-3) | 15 | 41 |
| 1 | Names only | 201 | 201 |
| 2 | Includes (ring, hart, and SBI headers), the IPI cause, windows with harts and their walked channel leaves (M1-3), each as page 0 of the root's leaves (M2-3), a state per hart without an entry time, and `decide` on one hart's counters, whose call sum adds `mgmt` (M2-3) | 42 | 72 |
| 3 | Constants: hart 0's budget, the printed line, the IPI cause, the state's size, the firmware identifiers, the exit record's 360 bytes with `vsstatus` and the eleven counters (M1-3), and the management extension's identity, functions, results, records, and words (M2-3); the class names, with `measurement` (M2-2) and `mgmt` (M2-3) | 37 | 53 |
| 4 | Controls: `hstatus` `0x180` (VTW clear), `sie` = SSIE, each block's stack top | 30 | 39 |
| 5 | The window's VMID and hart; SBI rows on one hart's state, each exit with the walked leaf (M1-3); DBCN refuses the hart region | 36 | 45 |
| 6 | SRST: a shutdown posts SHUTDOWN and stops its hart; a stopped hart's IPI is terminal; each hart's ceiling and an IPI at it; B7's time-budget test removed | 155 | 116 |
| 7 | Terminal exits: the supervisor software interrupt is the IPI, every other interrupt terminal; an IPI not from V=1; an absent leaf terminal (M1-3), absent leaves since M2-3; `be_mvp_apply_return` and the IPI; B7's `wfi` cases removed | 102 | 171 |
| 8 | The console: each hart's LINE records drained through its ring and printed by `be_mvp_line_output`, a full ring, a stopped hart's flush; two harts drained in pseudo-random order | 184 | 231 |
| 9 | The CSR set, SPP, and readback compare, without B7's vCPU save and restore | 77 | 26 |
| 10 | The IPI exit and B7's slice and `wfi` exits now terminal; new: the PING and PONG, the READY, ENTERED, SHUTDOWN, and FAIL records through hart 0's control loop, the HSM and IPI checks, and `BE_MVP:02`'s census (M0-A.2); per-hart counters and failures; the denial entry's decisions and injected values (`test_denials`) and the DENIAL records through hart 0's loop (`test_denial_records`) (M1-3); the ACK wait's steps (`test_ack_wait`, Plan revision M1-B); SHUTDOWN's management word, and new (M2-3): `be_mvp_mgmt_decide` over every grant, state, function, target, and requester and other tables (`test_mgmt_decide`), the calls, waits, PAUSE and TERMINATE, and the paused and terminated harts (`test_mgmt_calls`), and the management records through hart 0's loop (`test_mgmt_records`) | 178 | 2145 |
| 11 | The line builder: the MVP markers and the worst-case DETAIL lines | 108 | 130 |
| 12 | Replays per hart with the IPI probe's IPI: each domain's census, two harts at once, and the `sbi-time` variant | 121 | 109 |
| 13 | `main`: the test list, with M1's three tests and M2-3's three | 8 | 17 |
| | **Total** | **1294** | **3396** |

### `tests/gstage-test.c` (from B7's `tests/b7-gstage-test.c`)

Original 626 lines, copy 2451; 103 hunks, 278 removed, 2103 added, 348 unchanged. Names and the hart field; M1-2's channel page, its walk, the channel check, and the builder's mutations; M2-2's declared pages: the plan's three leaves in each root, the page check, every page rule, the walker's refusals, single-bit flips of a root with pages, and the two builder variants' leaves.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the channel (M1-2) and the declared pages (M2-2) | 7 | 22 |
| 1 | Names only | 165 | 165 |
| 2 | The channel's constants and the PTEs the plan derives for it, and a pool per root (M1-2), in a hunk that now takes in the pools' names, with an absent root page (M2-2); the model with a channel page, the fixed MVP descriptors, page, and sealed record, and the helpers for a channel pair, an empty map or leaf, and a refusal (M1-2), M1's page record as `struct be_mvp_gstage_root_page` (M2-2) | 4 | 148 |
| 3 | Constants: the descriptor and map sizes, the harts; the level-0 page's and the spare's offsets, the channel record's size, each root's level-0 page, and the channel page (M1-2) | 22 | 30 |
| 4 | Each window's descriptor and map with a hart; the pair check's hart cases; the hart in every descriptor; new (M1-2): no channel, the channel roots and their edges, the page refusals, the channel walk, the channel check against each root's mutated leaf, and the builder's mutations; new (M2-2): the plan's two roots with pages and their exact leaves (`test_page_roots`), the builder variants' leaves (`test_page_variants`), every page rule (`test_pages_rules`), the walker on roots with pages (`test_pages_walk`), every bit of every nonzero entry (`check_pages_mutations`), and the page check's every refusal (`test_page_check`) | 69 | 1711 |
| 5 | `main`: a hart for each window; M1-2's tests and M2-2's | 11 | 27 |
| | **Total** | **278** | **2103** |

### `tests/payload-test.c` (from B7's `tests/b7-payload-test.c`)

Original 647 lines, copy 690; 94 hunks, 207 removed, 250 added, 440 unchanged. Names, harts in the windows, the hart region, M0-A's flat image and MVP region, and M1-3's channel page, since M2-2 the whole shared extent.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the channel page (M1-3), since M2-2 the shared pages, and the monitor's core for the accepted image (M6-2) | 4 | 7 |
| 1 | Names only | 133 | 133 |
| 2 | The synthetic image (M0-A.1): the kernel at `0xa5000`, after the stub page and the `0xa4000`-byte flat image, and the DTBs after it | 5 | 7 |
| 3 | The windows' harts; the maps' order comment; the synthetic image's offsets by name (M0-A.1) | 40 | 44 |
| 4 | The staged image against the hart region and the MVP region (M0-A.1), and against the channel page directly above G1's window (M1-3), since M2-2 against the three shared pages: just above them it passes, and at the channel page's end or in the last page it fails | 18 | 52 |
| 5 | The domains' DTBs comment, the kernel's staged address, and the variant comment | 7 | 7 |
| | **Total** | **207** | **250** |

### `Makefile` (from B7's `Makefile`)

Original 400 lines, copy 920; 62 hunks, 251 removed, 771 added, 149 unchanged. B7's flags, host-test method, monitor, boot image, variant, and image-check rules for the MVP; the Make controls, the tool lock, the target check, lint, the scenario, the probe images, the budgets, scratch in `build/mvp/tmp`, M0-4's records and evidence bundle, and M0-B's closure fetcher in the lock check and lint; M1's two scenarios, the deny test, the te-poc images and their variants, and `policy-negatives`; M2's third scenario, `anchor`, with its measured inputs, the SHA-256 test, the anchor images and their four variants, and anchor's two build-time negatives; M4-1's `claim-ledger-check` after the evidence bundle.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with `MVP_SCENARIO_NAME` (M1-1) and the claim ledger's check in `check` (M4-1) | 18 | 37 |
| 1 | Names only | 21 | 21 |
| 2 | The Make controls and the tool lock at parse time, `TMPDIR`, the checks' records (M0-4), the tools from the lock, the accepted flags with `-Os` for the MVP's C, the flat image's `0xa4000` bytes (M0-A.1); the MVP's C and headers, with M2-2's SHA-256, which only an image with pages links; the scenarios two-guests, te-poc, and anchor (M2-1), each one's header and expectations, te-poc's authority report and anchor's with its expected measurement, generated from the measured domain's kernel and DTB (M2-1), anchor's four variants (M2-2, M2-3), and the policy check (M1-1); the payload layout; and the host tests with their pinned counts, with `deny` (M1-3) and `sha256` (M2-2), the counts pinned again at M2-2, at M2-1 and M2-2's integration, and at M2-3 | 128 | 204 |
| 3 | The monitor: B7's link set with the MVP's runtimes, trap, and hart entry, rebuilt per variant and probe; `IMAGE_TOOLCHAINS` and `VARIANT_TOOLCHAINS`, both toolchains since M0-A.1; the object, link, and flat-image rules, the image padded to `0xa4000` bytes; each monitor's scenario header and shared MVP objects, the te-poc monitors and their variants `reader-write` and `no-inject` (M1-3) | 35 | 139 |
| 4 | The boot image (shim flags, payload, both links), the variants' kernel, DTBs, and shim; the anchor images (M2-2): each toolchain's monitor with `mvp-sha256.o`, its boot image with anchor's DTBs, and the variants `secret-shared` and `response-writable` (`mvp-gstage.o` recompiled), `wrong-measurement`, and (M2-3) `no-grant-check`, each its own monitor | 16 | 60 |
| 5 | `image-check` and `variants` with the scenario's binding, the variants for both toolchains, and te-poc's images and variants with te-poc's DTBs, expectation, and authority report (M1-3), and anchor's with its DTBs, expectation, report, and the guest's kernel (M2-2); the probe stub, probe monitors, and boot images with `probes`; the measurement link and `budgets`, with anchor's images (M2-2); each check's output kept as a record (M0-4) | 23 | 189 |
| 6 | The tool lock, `lint`, `check` with the M0-3 rows, `budgets`, and M0-4's evidence bundle last, and `clean` with the records; the closure fetcher's self-test in `tool-lock-check` and its file in `lint` (M0-B); new `policy-negatives` (M1-1): the policy check on te-poc, recorded with its report, and the two build-time negative images, which `check` runs after `lint`; since M2-1 also the policy check on anchor, recorded with its report, and anchor's two build-time negatives, `grant-without-rule` and `secret-flow`; new `claim-ledger-check` (M4-1): the claim ledger's self-test and check, each recorded, which `check` runs after the evidence bundle and whose records join it | 10 | 121 |
| | **Total** | **251** | **771** |

### `guest.mk` (from B7's `guest.mk`)

Original 223 lines, copy 263; 34 hunks, 151 removed, 191 added, 72 unchanged. Names, the Make controls and the lock when run alone, the lock's pins, the RPM cache, and build scratch; te-poc's DTB pair (M1-3), and M1's fragment and the init's role test (M1-4); anchor's DTB pair (M2-1), and the management module, its sources, and the role test's M2 cases (M2-4).

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with te-poc's DTBs (M1-3) and M1's fragment (M1-4), anchor's DTBs (M2-1), and the module and `CONFIG_MODULES=y` (M2-4); since M1-3 its last hunk also takes in the run-alone section's first lines, the Make controls and the tool lock | 27 | 54 |
| 1 | Names only | 68 | 68 |
| 2 | Run alone: build scratch in `TMPDIR` | 3 | 7 |
| 3 | The Linux pins from the tool lock, no longer caller values; the reused B6 files' comment; te-poc's two DTBs among the outputs (M1-3), and anchor's (M2-1); the module, `be-mgmt.ko`, among the outputs (M2-4); `guest/mvp-kernel.config` among the sources and the init's guest-ID and role test's 74 cases (M1-4); the module's sources, `guest/be/types.h`, and `src/mvp-sha256.{h,c}` among the sources, and the test's 103 cases (M2-4) | 44 | 53 |
| 4 | The DTS self-test against the MVP plan | 3 | 3 |
| 5 | `kernel-repro`'s comment; the default goal when run alone | 6 | 6 |
| | **Total** | **151** | **191** |

### `tools/build-guest.sh` (from B7's `scripts/build-guest.sh`)

Original 384 lines, copy 642; 51 hunks, 85 removed, 343 added, 299 unchanged. Names and the MVP paths; M1-4's own fragment merged after B6's, with the `.config` delta check (Q16); M2-4's management module, built out of tree against the kernel's exports, in the initramfs and among the pinned outputs, the delta check in two steps (M1's lines, then `CONFIG_MODULES=y`'s sixteen), and the init built with the monitor's SHA-256.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the kernel's `.config` from both fragments and its delta check (M1-4, Q16), and the module, its two-pass kernel build, the two-step delta check, and the init's SHA-256 (M2-4) | 22 | 60 |
| 1 | Names only | 22 | 22 |
| 2 | Settings (M1-4): the MVP's fragment, Kbuild's tool variables, and the three declared `.config` lines; the module's source and object directories, the fragment's M2 lines, and the sixteen lines `CONFIG_MODULES=y` makes visible (M2-4) | 0 | 32 |
| 3 | The init comment and the missing-tool message name the MVP plan; `check_config` on both fragments, the `.config` delta against B6's fragment alone (stop condition 5), both fragments among the kernel's inputs, and the kernel configured with `merge_config.sh -m` and `allnoconfig` (M1-4); since M2-4 the init's sources with `src/mvp-sha256.c`, `fragment_sets`, `check_config` with symbols the MVP's fragment overrides, `config_delta`, `check_delta`, and `configure` for B6's `.config`, M1's, and the final one, each step checked against its declared lines, the module's source among the kernel's inputs and in the cache check, the initramfs list with the module (`render_list`), the kernel built twice around the module's `M=` build (vmlinux and the module's exports, then the Image), the module copied out, and the record and `touch` with it | 41 | 229 |
| | **Total** | **85** | **343** |

### `tools/gen-dts.py` (from B7's `scripts/gen-dts.py`)

Original 397 lines, copy 551; 42 hunks, 80 removed, 234 added, 317 unchanged. Names, the MVP model and compatible, and the plan's DT statements; the init's role arguments (M1-1) and te-poc's DTB pair (M1-3); anchor's roles, page arguments, and DTB pair (M2-1).

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the role arguments (M1-1) and the `te-poc` DTBs (M1-3), and the M2 roles' arguments and the `anchor` DTBs (M2-1) | 19 | 39 |
| 1 | Names only | 12 | 12 |
| 2 | The model and compatible; `DOMAINS`; the roles and accesses (M1-1); te-poc's roles and denied accesses, the `te-poc` variant, and its two DTBs (M1-3); anchor's roles, `host` and `prot`, with their three pages and denied accesses, the `anchor` variant, and its two DTBs (M2-1) | 18 | 50 |
| 3 | Range checks; `guest_bootargs` with the init's arguments and `role_arguments` (M1-1), `te_poc_arguments` and the `te-poc` values (M1-3); `page_arguments` (`be.role=`, `be.pages=`, `be.deny=`), `deny_argument`, anchor's arguments, and the `anchor` values (M2-1) | 8 | 70 |
| 4 | The self-test: the MVP plan's statements and the layout mutations; the role arguments and te-poc's pair (M1-1, M1-3); the page arguments, their refusals, and anchor's pair (M2-1) | 23 | 63 |
| | **Total** | **80** | **234** |

### `tools/gen-payload.py` (from B7's `scripts/gen-payload.py`)

Original 175 lines, copy 177; 23 hunks, 32 removed, 34 added, 143 unchanged. Names, `DOMAINS`, and M0-A's offsets in the docstring.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 7 | 9 |
| 1 | Names only | 20 | 20 |
| 2 | `DOMAINS` and the generated header's name | 5 | 5 |
| | **Total** | **32** | **34** |

### `tools/guest-pins.py` (from B7's `scripts/guest-pins.py`)

Original 729 lines, copy 891; 28 hunks, 25 removed, 187 added, 704 unchanged. Names; M2-4's management module among the pinned outputs, with its own checks, in a row of its own.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the module (M2-4) | 8 | 15 |
| 1 | Names only | 14 | 14 |
| 2 | The module (M2-4): its file, `be-mgmt.ko`, among the pinned files; its facts (`check_module`, with `elf_sections`): an unsigned RISC-V `ET_REL` object, ELF64 little-endian, soft-float, with one `.modinfo` and one `.gnu.linkonce.this_module` and no `__versions`, its `.modinfo` naming `be_mgmt`, license `GPL`, and no dependencies, and its `vermagic` the kernel's release without `mod_unload` or `modversions`; a fake module for the self-test, with its cases; and `module_bytes=` in the summary line | 3 | 158 |
| | **Total** | **25** | **187** |

### `tools/guest-reference-check.py` (from B7's `scripts/guest-reference-check.py`)

Original 274 lines, copy 274; 18 hunks, 26 removed, 26 added, 248 unchanged. Names, `MVPINIT`, and the MVP model.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 5 | 5 |
| 1 | Names only | 20 | 20 |
| 2 | The model line in the self-test's console | 1 | 1 |
| | **Total** | **26** | **26** |

### `tools/run-reference-boot.sh` (from B7's `scripts/run-reference-boot.sh`)

Original 126 lines, copy 126; 11 hunks, 14 removed, 14 added, 112 unchanged. Names and the timeout variable.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 7 | 7 |
| 1 | Names only | 7 | 7 |
| | **Total** | **14** | **14** |

### `guest/mvp-init.c` (from B7's `guest/b7-init.c`)

Original 232 lines, copy 1034; 25 hunks, 29 removed, 831 added, 203 unchanged. Names and the `MVPINIT` tag; M1-4's roles, with Plan revision M1-A's forked child for the denied accesses; M2-4's `host` and `prot` roles, with the module, the three pages, the requests and their HMAC-SHA-256, and the management calls, and its follow-up's one-second request deadline.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the roles, their lines, and the forked child (M1-4, M1-A), and M2's roles, their lines, the protocol, and the deadline (M2-4 and its follow-up) | 17 | 94 |
| 1 | Names only | 9 | 9 |
| 2 | The roles (M1-4, M1-A): includes, the channel's constants, the xorshift64 pattern and its FNV-1a digest, the writer and the reader through `/dev/mem`, the forked child whose SIGSEGV handler (a raw `rt_sigaction`) records each denied access, and the `MVPINIT 07 CHANNEL` and `MVPINIT 08 DENIED` lines; since M2-4 the `host` and `prot` roles: the ioctl and SHA-256 includes, the protocol's constants (the sequence word at offset 0, the 64-byte message `BE-MVP-M2-REQ-<n>` at 64, the 32-byte digest), the module's file and device, the call's ABI (`_IOWR('B', 0x42, ...)`) and result codes, each role's script of requests and calls, the module loaded with `finit_module`, the pages mapped (`open_anchor`), the requests and their wait (`request`, one second of `CLOCK_MONOTONIC` at 1 ms polls since the follow-up), the calls and the burst (`call_step`, `run_script`), and the protected server's HMAC-SHA-256 answers keyed by the secret page (`answer`, `serve`), with the `MVPINIT 07 PAGES`, `09 REQUEST` and `RESPONSE`, and `10 MGMT` lines | 1 | 719 |
| 3 | `main`: the `rdcycle` comment; the role read from the arguments and run after line 02 (M1-4) | 2 | 9 |
| | **Total** | **29** | **831** |

### `guest/mvp-guest-id.h` (from B7's `guest/b7-guest-id.h`)

Original 57 lines, copy 297; 13 hunks, 21 removed, 261 added, 36 unchanged. Names; M1-4's role rule; M2-4's `host` and `prot` roles with `be.pages=`.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the role rule (M1-4) and M2's roles (M2-4) | 9 | 30 |
| 1 | Names only | 11 | 11 |
| 2 | The role rule (M1-4): the roles, the accesses, `mvp_role_args()`'s three results, and its parser for `be.role=`, `be.channel=`, and `be.deny=`, before the include guard's end; since M2-4 the roles `host` and `prot`, at most four denied accesses (two for M1's roles), three pages, `be.pages=` (`mvp_pages`), and whether a GPA lies in a page the role maps read-write (`mvp_writable`) | 1 | 220 |
| | **Total** | **21** | **261** |

### `guest/mvp-guest-id-test.c` (from B7's `guest/b7-guest-id-test.c`)

Original 84 lines, copy 322; 16 hunks, 35 removed, 273 added, 49 unchanged. Names; M1-4's role cases; M2-4's cases for the `host` and `prot` roles: 103 cases with the ID rule's, 74 before.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the role cases (M1-4) and M2's (M2-4) | 6 | 12 |
| 1 | Names only | 24 | 24 |
| 2 | The role cases (M1-4): te-poc's two argument lists, M0's, and each way a role argument can be absent, repeated, or malformed, with the parsed role, channel, and denials; `main` runs them after the ID cases; since M2-4 anchor's two argument lists and each way `be.pages=` or an M2 role's denials can be malformed | 5 | 237 |
| | **Total** | **35** | **273** |

### `guest/initramfs.list.in` (from B7's `guest/initramfs.list.in`)

Original 14 lines, copy 21; 2 hunks, 7 removed, 14 added, 7 unchanged. Names: the init's name; M1-4's `/dev/mem` node; M2-4's module and its device node. Since M2-4 the header comment is one hunk.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with `/dev/mem` (M1-4) and the module and its device (M2-4) | 6 | 10 |
| 1 | Names only | 0 | 0 |
| 2 | The `/dev/mem` node the roles open (M1-4, Q2), in one hunk with the init's name; the module's device node, `/dev/be-mgmt`, misc major 10 at minor 243, and its file, `/be-mgmt.ko` (M2-4) | 1 | 4 |
| | **Total** | **7** | **14** |

### `guest/mvp-guest.dts.in` (from B7's `guest/b7-guest.dts.in`)

Original 48 lines, copy 49; 3 hunks, 8 removed, 9 added, 40 unchanged. The model and compatible (Q3).

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 6 | 7 |
| 1 | `model` and `compatible` | 2 | 2 |
| | **Total** | **8** | **9** |

### `guest/ref-stub.S` (from B7's `guest/ref-stub.S`)

Original 36 lines, copy 36; 4 hunks, 11 removed, 11 added, 25 unchanged. Names.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 5 | 5 |
| 1 | Names only | 6 | 6 |
| | **Total** | **11** | **11** |

### `guest/pins.txt` (from B7's `guest/pins.txt`)

Original 24 lines, copy 37; 1 hunk, 18 removed, 31 added, 6 unchanged. The MVP outputs' pins; since M1-4 the init's roles and the Image's two fragments; since M2-1 anchor's two DTBs, and since M2-4 the module and the Image with `CONFIG_MODULES=y`. Since M2-4 the diff joins the header comment and the pins, two rows at M1, into one hunk.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | One hunk since M2-4: the header comment, with M1's init and Image (M1-4), anchor's DTBs (M2-1), and the module (M2-4); the init's digest and size (the `MVPINIT` tag; its roles, M1-4; M2's roles, M2-4 and its follow-up), the module's (M2-4), the Image's (both fragments, M1-4; `CONFIG_MODULES=y`, M2-4), both DTBs' and the variants' digests (model, compatible), te-poc's two DTBs' (M1-3) and anchor's (M2-1), and the kernel's `image_size`, `0x203fb0` (M2-4) | 18 | 31 |
| | **Total** | **18** | **31** |

### `src/mvp-runtime.c` (from B7's `src/b7-runtime.c`)

Original 1046 lines, copy 2194; 151 hunks, 777 removed, 1925 added, 269 unchanged. Hart 0 as the control hart: B7's R3 prelude unchanged (until M6-2), then the firmware probes, both roots, the payload, the barrier, the hart starts, the READY wait, and the control loop over two rings, drained round-robin since M0-C.1; B7's scheduler, switch, vCPU save and load, deadline, and slice removed; the probe images' hooks; M1-3's channel record and identity, the channel check, the channel page's clear, and the DENY lines; M2-2's pages, secret, and measurement; M2-3's sealed grants, the requests' decisions, answers, and deliveries, and the paused and terminated domains; M6-2's boot: the accepted boot check, `BE_MVP:00 BOOT_VALIDATED`, the MVP core profile sealed and derived (`BE_MVP:00 CONFIG_SEALED`), and the derived roots' records for every later step, without B7's R1 and R2 steps or hart 0's binding and `hgatp` publication; M6-3's executor: every privileged effect through `src/mvp-executor.c`, to which `be_mvp_fw_call` moved. M6-2's deletions move the diff's alignment through rows 2, 4, 5, 6, 7, and 8, and ten hunks of names (20 lines each side) into the rows around them. M6-3's calls move it through rows 3 to 8, join two hunks of names (2 lines each side) to row 8's, and put `hart_page` and `ring_views` (22 lines of row 6's) in row 5's last hunk. M6-2's rows summed to 1924 added lines where its copy had 1929; the five are counted here, four in row 5 and one in row 8, where a classification of M6-2's change by function places them.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the channel check, the channel page's clear, and the DENY lines (M1-3), the pages and the measurement (M2-2), and the management extension (M2-3), the MVP core profile's seal (M6-2), and the executor (M6-3) | 21 | 67 |
| 1 | Names only | 46 | 46 |
| 2 | Includes; static assertions (controls and exit offsets, the hart region's shifts, page sizes, the budgets); the variants' switches and the probe images' domain count, with a v3 header's pages in place of a channel (M2-2) and `no-grant-check`'s switch (M2-3); the linked payload layout, bindings, and descriptors; the sealed channel record and the configuration identity, and each domain's walked channel leaf (M1-3); the sealed page records, the secret, the expected measurement, and hart 0's measurement (M2-2); each domain's walked page leaves (M2-2), the sealed grants, and hart 0's management state (M2-3); hart 0's run state and ring views; the `BE_MVP:01`-`:14`, PROBE, and DETAIL formats, with `:01`'s MVP region fields (M0-A.1) and `:02`'s `started` (M0-A.2), the CHANNEL_CHECKED, CHANNEL_CLEARED, channel DETAIL, and DENY formats (M1-3), the PAGE_CHECKED, PAGE_CLEARED, SECRET_PLACED, MEASURED, page DETAIL, and measurement DETAIL formats (M2-2), and the MGMT, DOMAIN_PAUSED, and DOMAIN_TERMINATED formats (M2-3); the record value programs, with PAUSED's (M2-3); since M6-2 `mvp-core.h` in place of R1's fixed configuration, no assertion of the R1 trusted stack, no R2 pools, the `BE_MVP:00` formats in place of the R3 markers, and the R1 runtime and the derived roots' records (`be_mvp_sealed_descs`, `be_mvp_sealed_pages`, `be_mvp_sealed_channel`); since M6-3 `mvp-executor.h` | 195 | 420 |
| 3 | The formatter and DETAIL lines (new `be_mvp_line_format`, `be_mvp_detail_line`); `be_mvp_send_ipi`, since M6-3 through the executor's IPI, and `be_mvp_fw_call`, since M6-3 the executor's | 15 | 63 |
| 4 | Console output and the single terminal path with hart 0's own DETAIL lines; B7's per-guest console removed; new `clear_mvp_bss`: the MVP region's symbols against the layout, then its BSS zeroed (M0-A.1); since M6-2 B7's R1 and R2 steps (`run_r1`, `run_r2`) removed, and `line_hex` declared for every image; since M6-3 the console write, the SRST request, and the halt through the executor | 136 | 88 |
| 5 | Boot: R1 and R2 as B7's, the scenario line, the firmware probe with `BE_MVP:02`'s census of the other harts (M0-A.2), the Sstc probe, both roots with harts and VMIDs, each built with its channel leaf from the sealed record and both checked by the channel check in place of M0's pair check, with `BE_MVP:03 CHANNEL_CHECKED` and the configuration identity (M1-3); since M2-2 each root built with its page leaves from the sealed records (`build_gstage`) and checked by the page check (`check_pages`), with one `BE_MVP:03 PAGE_CHECKED` per page; the payload checks, clears, the channel page's clear and readback (M1-3), and placement; the channel pages' clear and the secret's placement (`place_pages`, `PAGE_CLEARED`, `SECRET_PLACED`), and the measurement of the protected domain's kernel and DTB as placed, the secret page, and the configuration identity against the expected value (`measure`, `BE_MVP:06 MEASURED` or `FAIL measurement`) (M2-2); since M6-2 the MVP core profile's seal in place of B7's R1 and R2 (`seal_config`: the image's inventory and proposal copied, validated, sealed, and derived, the builder's inputs from the derived roots required to equal the linked records, and `BE_MVP:00 CONFIG_SEALED` with the identity), the boot layout without the fixture extents, and each root built, re-walked, and checked, the channel page cleared, and the pages placed and measured from the derived roots' records; since M6-3 the firmware probes, the Sstc probe, and the clocks through the executor, and, by the diff's alignment, `hart_page` and `ring_views` (row 6's) in its last hunk | 124 | 578 |
| 6 | The blocks: each state page, with its walked window and channel leaf and the image's denial entry (M1-3), its page leaves (M2-3), and whether the image accepts the management extension (M2-3), both rings' views, the barrier, and the hart starts; since M2-3 a record posted to a domain's inbound ring with its IPI (`post_inbound`), a request's answer, MGMT_RESULT and the `BE_MVP:MGMT` line (`answer`), its delivery, PAUSE or TERMINATE (`deliver`), and the `BE_MVP:12 DOMAIN_PAUSED` and `DOMAIN_TERMINATED` lines, the latter with the measured domain's measurement; M6-2 moved this row only through the diff's alignment; since M6-3 the barrier's fence, the hart starts, and the IPIs through the executor, and `hart_page` and `ring_views` in row 5's last hunk by the diff's alignment | 57 | 197 |
| 7 | The run: PING, the run's end, a domain's FAIL and ACK, the record steps, with each DENIAL's `BE_MVP:DENY` line and the channel record a DENIAL is checked against (M1-3), since M2-3 the sealed pages, and the management steps (a decision answered at once, a delivery, a PAUSED or TERMINATED with the pending request's answer, and the run complete once every domain has shut down or been terminated) with the sealed grants and hart 0's management state, and SHUTDOWN's `sbi=` with its management calls (M2-3), the round-robin drain of one record per visit with its fences (M0-C.1) and the `ring-full` variant's hold and delay (M0-A.3), the READY wait, the `wfi` loop, the budget, and the probe images' wrappers; B7's scheduler loop removed; since M6-2 the control loop given the derived roots' pages or channel, hart 0's stack by its MVP name at the run's start, and, by the diff's alignment, the start of `be_mvp_runtime_main`; since M6-3 the fences, the clocks, the wait, the SSIP clear, the budget, and the SRST request through the executor | 170 | 429 |
| 8 | `be_mvp_runtime_main`: the MVP region's BSS cleared first (M0-A.1), the MVP steps after `BE_R3:06`, the channel page cleared after both windows (M1-3), or the pages placed and, after both payloads, the measurement (M2-2), and the probe images'; since M6-2 the MVP steps after `BE_MVP:00 BOOT_VALIDATED`, the seal, and the accepted reset, with no R3 binding, publication, or entry; since M6-3 the firmware identity's calls, hart 0's reset, and the data fence through the executor | 13 | 37 |
| | **Total** | **777** | **1925** |

### `src/mvp-trap.S` (from B7's `src/b7-trap.S`)

Original 557 lines, copy 672; 78 hunks, 257 removed, 372 added, 300 unchanged. A saved page per domain hart from `sscratch`, VTW clear, the IPI as the HS interrupt, the per-domain CSRs written once; B7's save and load helpers and deadline removed; M1-3's injection helper and the exit's `vsstatus`; M2-3's SSIP helper returning `sip` as it was, its one instruction change, and comments; M6-2's name for hart 0's stack, which moves 27 added lines between row 4's last three hunks by the diff's alignment and no count.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the injection helper and the exit's `vsstatus` (M1-3), and the paused and terminated harts' wait on the IPI (M2-3) | 19 | 24 |
| 1 | Names only | 41 | 41 |
| 2 | Constants: VTVM, VTW, and VTSR cleared, SSIE and hart 0's SSIE and STIE, `stimecmp`, the hart region's shifts, the classes, `struct be_mvp_exit`'s words, with `vsstatus` at 352 (M1-3) | 27 | 42 |
| 3 | The Sstc and arm helpers: the per-domain set written once from `a2` and read back into `a3`, VTW cleared, SSIE set; B7's save and load helpers removed | 85 | 53 |
| 4 | The TIME helper; B7's deadline helper becomes hart 0's budget helper; the wait on a mask, also a paused or terminated domain hart's (M2-3); new SSIP, time, ring-fence, placement-fence, and park helpers, the SSIP helper one `csrrci` that returns `sip` as it was (M2-3); new `be_mvp_arch_inject` (M1-3): `vscause`, `vstval`, `vsepc`, and `vsstatus` written in that order, then each read back | 41 | 137 |
| 5 | The vector: the saved page from `sscratch`, checked as a block's stack top, and the guest's `vsstatus` saved in the exit record (M1-3); hart 0's HS exceptions to its terminal, its stack by its MVP name since M6-2; the dispatch's return to the hart's terminal | 23 | 46 |
| 6 | The resume tail: `sscratch` and the block's stack top, `sie` SSIE only, `hstatus` SPV only, the hart's terminal | 21 | 29 |
| | **Total** | **257** | **372** |

### `src/mvp-platform.h` (from B7's `src/b7-platform.h`)

Original 142 lines, copy 334; 38 hunks, 71 removed, 263 added, 71 unchanged. The hart page, the domain harts' entry points, the firmware calls, and the MVP helpers; M1-3's denial switch, the walked window and leaf in the hart page, and the injection helper; M2-3's management switch, the hart page's page leaves, and the SSIP helper's readback. Since M1-3 the diff aligns B7's helpers one declaration later, which moves the formatter and the DETAIL line into row 3 and the arm, TIME, and injection helpers into row 4; since M2-3 it aligns them again, which moves the Sstc and arm helpers' comments into row 3 and the wait helper's comment into row 4.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the injection helper (M1-3), and a waiting, paused, or terminated domain hart's IPI pending in `sip` (M2-3) | 8 | 14 |
| 1 | Names only | 7 | 7 |
| 2 | Includes; whether the image accepts the denial entry, `BE_MVP_RUN_ACCEPT_DENIAL`, 0 in the `no-inject` variant (M1-3), and the management extension, `BE_MVP_RUN_ACCEPT_MGMT` (M2-3); `struct be_mvp_hart_page`, with the walked window and channel leaf (M1-3), the leaves of every page since M2-3; and the DETAIL forms | 3 | 62 |
| 3 | Entry points: hart 0's runtime and terminal, the hart main, the dispatch, and the hart's terminal; `be_mvp_fw_call` (out of line), `be_mvp_send_ipi`, the formatter, and the DETAIL line; the Sstc and arm helpers' comments | 15 | 91 |
| 4 | The arm helpers, the TIME helper, new `be_mvp_arch_inject` (M1-3), and the budget and wait helpers' comments, the wait also a paused or terminated domain hart's (M2-3); B7's save and load helpers removed | 15 | 38 |
| 5 | The budget, wait, SSIP, time, fence, `fence.i`, and park helpers and the resume tail, the SSIP helper returning `sip` as it was (M2-3); B7's deadline helper removed; the MVP region's linker symbols (M0-A.1), and hart 0's stack's end (M6-2) | 23 | 51 |
| | **Total** | **71** | **263** |

### `src/mvp-boot.lds` (from B7's `src/b7-boot.lds`)

Original 96 lines, copy 99; 4 hunks, 31 removed, 34 added, 65 unchanged. Names, and the `0xa4000`-byte payload with the kernel at `0xa5000`.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 8 | 10 |
| 1 | Names only | 3 | 3 |
| 2 | The payload `ASSERT`s with MVP names: the payload is the `0xa4000`-byte flat image and the kernel follows at `0xa5000` (M0-A.1) | 20 | 21 |
| | **Total** | **31** | **34** |

### `src/mvp-guest-payload.S` (from B7's `src/b7-guest-payload.S`)

Original 55 lines, copy 55; 10 hunks, 37 removed, 37 added, 18 unchanged. Names, and the kernel's offset.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 9 | 9 |
| 1 | Names only | 28 | 28 |
| | **Total** | **37** | **37** |

### `shim/mvp-shim.S` (from B3's `src/b3-shim.S`)

Original 267 lines, copy 369; 11 hunks, 25 removed, 127 added, 242 unchanged. The start rule (Q2) and the QEMU-only `shim-rule` variant; B3's symbols kept.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 18 | 26 |
| 1 | The HSM identifiers and the ASCII zero | 2 | 5 |
| 2 | The entry: the `shim-rule` variant's first pass; a hart other than 0 goes to the start rule, where B3 parked it | 3 | 32 |
| 3 | The start rule (new): its line without leading zeros, HSM `hart_start` for hart 0, and the park; the variant's `hart_stop` | 1 | 48 |
| 4 | The start rule's report line and the variant's flag | 1 | 16 |
| | **Total** | **25** | **127** |

### `src/mvp-monitor.lds` (from the MVP port's `arch/riscv/be/r5-beryllium.lds`)

Original 366 lines, copy 265; 21 hunks, 153 removed, 52 added, 213 unchanged. The MVP's own linker script since M6-2 (planning/mvp-m6-plan.md, D-4), the port's as `tools/port.py` makes it without the accepted fixture roots, stacks, saved, private, and shared pages and guest code: the core's monitor code below `0x1_0200_8000`, its data with the configuration and the diagnostic page, and hart 0's stack, the rest unused and zero; the pool, hart region, and MVP region as before; since M6-3 the executor's object, `mvp-executor.o`, among the MVP region's.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 7 | 12 |
| 1 | PHDRS: the `reserved`, `guest_management`, and `guest_protected` segments removed | 3 | 0 |
| 2 | `.monitor.input`: the configuration, `mvp-config.o`'s constants, in place of `r1-config.o`'s | 1 | 1 |
| 3 | The exclusions from `.monitor.text`, `.monitor.rodata`, and `.monitor.data` (its data, BSS, and `COMMON`) name `mvp-core.o` too (9 patterns), and since M6-3 `mvp-executor.o` on the same lines | 9 | 18 |
| 4 | After the diagnostic page, hart 0's stack: the NOLOAD `.stack.control`, `0x2000` bytes at `0x1_0201_0000`, in place of the accepted root pools, trusted stacks, saved, private, and shared pages, and the two fixture guest pages | 65 | 7 |
| 5 | The pool's third `ASSERT`: after hart 0's stack, no longer after the protected guest page | 2 | 2 |
| 6 | The MVP region's objects name `mvp-core.o` (4 patterns), and since M6-3 `mvp-executor.o` (4 more) | 0 | 8 |
| 7 | `ASSERT`s: the fixture extents', their disjointness, and the fixture slots' removed; hart 0's stack at its address and after the monitor data | 66 | 4 |
| | **Total** | **153** | **52** |

### `tests/check-image.py` (from B7's `tests/check-b7-image.py`)

Original 2301 lines, copy 4022; 213 hunks, 435 removed, 2156 added, 1866 unchanged. The MVP and probe profiles, the hart region, the shim's SBI calls, the mutation test's MVP defects, and M0-A's MVP region and flat image; M1-3's injection helper, the te-poc images with their linked channel record and configuration identity, the channel page, and nine more defects; M2-2's anchor images with their linked pages, secret, and expected measurement, the shared pages, and their defects; M2-3's sealed grants and management state out of the domain harts' reach, the SSIP helper's readback, `no-grant-check`, and their defects.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the injection helper, the te-poc images, their report, and the channel page (M1-3), the anchor images, their pages, secret, and measurement, and the shared pages (M2-2), and the domain harts' reach, the management state, and `no-grant-check` (M2-3) | 68 | 178 |
| 1 | Names only | 52 | 52 |
| 2 | Paths and the layout parser; the flat image's and the accepted image's extents (M0-A.1); the `bisect` import (M2-3) | 6 | 14 |
| 3 | The hart region's constants, blocks, and areas; the pool and hart-region conjuncts and segment; the MVP region's constants, conjuncts, and segments (M0-A.1), with `mvp-sha256.o` among its objects (M2-2) | 9 | 50 |
| 4 | The MVP names, required symbols, callers of the `ecall`, CSR writer and instruction-site tables, and sections; the MVP region's sections and symbols, the MVP C objects, and the assembly that stays in the accepted code extent (M0-A.1); the injection helper, the channel record, and the identity's symbols, and the injected CSRs and their writer (M1-3); the pages', secret's, and measurements' symbols (M2-2), and the grants', the management state's, and the management code's (M2-3), with the domain harts' roots | 47 | 114 |
| 5 | The install callers and the injection helper's one call site (M1-3), the profiles, the raw switch's words, the helpers' values and reads with the injection helper's writes and readback (M1-3), and the SSIP helper's read of `sip` (M2-3), and the variants with te-poc's two (M1-3) and anchor's four (M2-2, M2-3), the channel record's words, and the rights (M1-3), and the v3 expectation, a page record's and a grant's words, the shared pages, the secret's and digest's sizes, and the grants' permissions (M2-2, M2-3) | 29 | 91 |
| 6 | `references` to a fixed point over the control flow; `track` with `a3`, and `a4` (M1-3); the ELF reader's header offsets for the mutation test (M0-A.1) | 22 | 72 |
| 7 | Monitor rules: the helpers' readbacks, the profile's sites and writers, both NOLOAD sections, the vector from `sscratch`, the block arithmetic and the hart entry (new), the resume checks, the segment, the bindings and harts, the hart region (new), and the probe symbols; M0-A.1: the scan over both code extents, the empty accepted data section, the MVP region's sections in order, every MVP C object placed in it by symbol and link map, and its extents; M1-3: the injection helper's call sites, the vector's `vsstatus`, and the linked channel record and configuration identity against the scenario's authority report; M2-2: the linked page records, secret, and expected measurement against the report, in their sections, and no channel record with pages; M2-3: the code the domain-hart entry and the vector reach (`check_domain_reach`) naming neither the grants, the management state, nor the measurement and never reaching the decision, and the linked grants against the report | 79 | 825 |
| 8 | Boot rules: the DTB names, the hart region's range, the shim's SBI calls (new), the start rule's template, the probe images' payload, and the variants with monitor variants; M0-A.1: eight ranges with the MVP region, and the `0xa4000`-byte payload's descriptor; M1-3: te-poc's DTBs with their bootargs from the scenario, the channel page among the ranges, and te-poc's variants; M2-2: anchor's DTBs, the shared pages among the ranges, and anchor's variants | 49 | 225 |
| 9 | The mutation test: the MVP defects, the layout mutations, and the probe profile's; M0-A.1: 15 MVP-region defects in the ELF, the link map, the flat image, the descriptor, and the layout, and one more per probe image; M1-3: six more defects in every image and three more in te-poc's; M2-2: the pages' and the measurement's defects in the anchor images; M2-3: the management state's, the grants', and the reach rule's, with a load encoder (`load_reference`) | 57 | 456 |
| 10 | `main`: `--expect`, `--report` (M1-3), `--probe`, `--mutation-probe`, and monitor variants; either toolchain as the reference; the MVP region's report fields; a v2 expectation's DTBs and label (M1-3), and a DTB without a pin refused (M2-2) | 17 | 79 |
| | **Total** | **435** | **2156** |

### `tests/run-qemu.sh` (from B7's `tests/run-qemu.sh`)

Original 211 lines, copy 354; 26 hunks, 128 removed, 271 added, 83 unchanged. Eight harts; the MVP's scenarios, variants, and probe images for both toolchains; each attempt judged by `tests/check-capture.py`, and a REFUSED attempt (M0-A.2) made again, up to eight attempts; M1-4's te-poc runs and variants, judged with te-poc's authority report; M2-5's anchor runs and four runtime negatives, judged with anchor's report and the measured domain's kernel and DTB.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with te-poc's runs (M1-4) and anchor's runs and negatives, with the measured inputs (M2-5) | 33 | 72 |
| 1 | Names only | 0 | 0 |
| 2 | Arguments and settings: the selected runs, the capture checker and the expectation files, te-poc's directory (M1-4), anchor's and the measured inputs (M2-5), the attempts' bound, and the toolchains for scenarios, variants, and probes | 6 | 17 |
| 3 | The scenarios with their expectation files, the variants and the probes on `k3-like`, te-poc on `k3-like`, `rva23`, and `plic` and its variants on `k3-like` (M1-4), anchor on the same machines and its four runtime negatives on `k3-like` (M2-5); the bound's check, the selection, and the images, expectations, reports, and measured inputs each run needs | 25 | 90 |
| 4 | The summary and the attempts table, with each attempt's boot ELF and its SHA-256 | 0 | 3 |
| 5 | One boot: `-smp 8 -m 8G`, its exit status kept | 11 | 5 |
| 6 | One run: attempts until one is not REFUSED, each judged by the capture checker, with te-poc's report (M1-4), and anchor's report and measured inputs (M2-5), at most `BE_MVP_QEMU_ATTEMPTS`; its summary line (B7's marker counts removed) | 25 | 54 |
| 7 | The totals per toolchain and the final line with runs, attempts, and refused attempts | 28 | 30 |
| | **Total** | **128** | **271** |

### `tools.mk` (from B7's `tools.mk`)

Original 163 lines, copy 349; 15 hunks, 143 removed, 329 added, 20 unchanged. B7's harness, rehearsal, and board targets for the MVP: the capture checker in place of B7's marker and capture checkers, the QEMU suite with REFUSED attempts repeated, eight harts in the rehearsal, the probe target, the evidence bundle, and the board record; te-poc's board images and variants (M1-3), its expectations and report in the checks (M1-4), and `SCENARIO=` and the remote reset (M1-5); anchor's board scenario and variants (M2-1), and its images, expectations, report, and measured inputs in the checks and the board targets (M2-5). Since M1-4 the diff joins B7's checks and its rehearsal, two rows at M0, into one hunk.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with `SCENARIO`, te-poc's variants, and the remote reset (M1-3, M1-5), and anchor and its variants (M2-5) | 45 | 47 |
| 1 | Names only | 0 | 0 |
| 2 | The guard (read only through the Makefile), the expectation directory and stamp, te-poc's expectations and report (M1-4), anchor's expectation stamp and measured inputs (M2-5), the capture checker and the evidence bundler; B0's rehearsal kernel with eight harts | 4 | 25 |
| 3 | The board settings (`RUNS`, `VARIANT`, and `SCENARIO`, M1-5), the board scenarios and their variants (M1-3, M1-5), with anchor's, `wrong-measurement` and `no-grant-check` (M2-1), the `k3ctl` pin (M1-5), the board images with te-poc's (M1-3) and anchor's (M2-5), their `IMAGE:FLAT:EXPECT[:VARIANT]` specs, a variant's scenario's expectations (M2-5), the board tools' environment, with the scenario's report and the measured DTB, `K3_MEASURED_DTB` (M2-5), and the targets | 1 | 82 |
| 4 | B7's marker and capture checks replaced by the capture checker's self-test and mutations; the rehearsal init's include path | 25 | 3 |
| 5 | One hunk since M1-4: the loader's check on every board image (a record), the bundler's self-test, the dry run (a record), `tools-check`, the QEMU suite judged by the capture checker with REFUSED attempts repeated, and the evidence bundle; the rehearsal of each toolchain's scenario image against its expectation, and of te-poc's with its report (M1-4); anchor's expectations, report, and measured inputs in the capture checker's self-test, the dry run's selector, the QEMU suite, and the rehearsal (M2-5) | 46 | 119 |
| 6 | The board targets: `k3-preflight` with the `k3ctl` pin (M1-5); the load check with the flat image and the expectation, of `SCENARIO`'s image (M1-5); `k3-probe` (new; GCC only, plan Q13); `k3-campaign` with the scenario image or a board variant (`payload`; te-poc's image, `reader-write`, and `no-inject`, M1-3 and M1-5; anchor's image, `wrong-measurement`, and `no-grant-check`, M2-5), refused while Make reads the file, its default run root named for any scenario but `two-guests` (M2-5); `board-evidence` (new), titled M2's (M2-5); the preflight's comment names the shared pages (M2-2) | 22 | 53 |
| | **Total** | **143** | **329** |

### `tests/kexec-rehearsal.sh` (from B7's `tests/kexec-rehearsal.sh`)

Original 173 lines, copy 237; 17 hunks, 112 removed, 176 added, 61 unchanged. Eight harts by default; each attempt judged by `tests/check-capture.py` in kexec mode, and a REFUSED attempt made again, up to eight; te-poc's image judged with its authority report (M1-4), anchor's with its report and the measured domain's kernel and DTB (M2-5).

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the authority report (M1-4) and the measured inputs (M2-5) | 25 | 39 |
| 1 | Names only | 3 | 3 |
| 2 | Arguments: the image, its expectation, the output directory, and the authority report a te-poc expectation names (M1-4), or an anchor one with its measured kernel and DTB (M2-5); the MVP's directory, the capture checker, and the layout header | 7 | 21 |
| 3 | Eight harts by default; attempts up to `REHEARSAL_ATTEMPTS` (8) | 5 | 6 |
| 4 | The expectation's check | 2 | 6 |
| 5 | One directory per attempt: the boot, the capture judged in kexec mode, with the report (M1-4), a REFUSED attempt made again (B7's single run and its own marker and capture checks removed), and each attempt's record | 67 | 97 |
| 6 | The final line with attempts, refused attempts, and kexec harts | 3 | 4 |
| | **Total** | **112** | **176** |

### `tests/kexec-rehearsal/init.c` (from B7's `tests/kexec-rehearsal/init.c`)

Original 265 lines, copy 268; 15 hunks, 29 removed, 32 added, 236 unchanged. The MVP's names and layout header; no other change.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 14 | 17 |
| 1 | Names only | 15 | 15 |
| | **Total** | **29** | **32** |

### `tools/kexec-load.py` (from B7's `scripts/kexec-load.py`)

Original 621 lines, copy 646; 21 hunks, 47 removed, 72 added, 574 unchanged. The MVP's layout and the layout rule on every MVP extent, at preflight and at load time; M1-5's channel page among them, since M2-2 the three shared pages.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the channel page (M1-5), since M2-2 the shared pages | 26 | 33 |
| 1 | Names only | 10 | 10 |
| 2 | The layout header's names for the flat image's extents and the channel page's (M1-5), since M2-2 the shared pages' | 1 | 4 |
| 3 | `raw_layout`: the layout rule on the live map and reservations before the load | 2 | 6 |
| 4 | `staging_regions`: every MVP extent (the accepted image, the pool, the hart region, the MVP region, staging, both windows, and the channel page, M1-5, since M2-2 the shared pages, `shared-pages`), `region_findings` over them, and `region-check` | 8 | 19 |
| | **Total** | **47** | **72** |

### `tests/test-kexec-load.py` (from B7's `tests/test-kexec-load.py`)

Original 510 lines, copy 654; 48 hunks, 69 removed, 213 added, 441 unchanged. B7's cases on the MVP's layout, with the hart region, the MVP region, and (M1-5) the channel page in the layout rule, since M2-2 the three shared pages; M2-5's purgatory search ending at the guest payload.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the channel page (M1-5), since M2-2 the shared pages | 9 | 12 |
| 1 | Names only | 15 | 15 |
| 2 | The loader's path; the flat image's extents, the hart region, and the MVP region (M0-A.1), and the channel page (M1-5), since M2-2 the shared pages; B7's recorded preflight, named as B7's, and M0's board preflight, pinned by its SHA-256 (M1-5); the MVP boot image's size, and the guest payload's offset, where the purgatory search ends (M2-5) | 9 | 33 |
| 3 | B7's recorded inputs, named as B7's, and the board image's helpers | 13 | 13 |
| 4 | Placement at L with the FDT slot after the `0x223000`-byte image | 6 | 6 |
| 5 | The layout rule at load time; the recorded map leaves all nine extents free (the channel page since M1-5, the shared pages since M2-2); a child or reservation in any extent, at its edges, or across the windows' boundary stops; the preflight record's region check; new `channel_page_is_an_mvp_extent` on B7's and M0's recorded maps (M1-5), since M2-2 `shared_pages_are_an_mvp_extent`, over each of the three pages; and each board image searched for a purgatory only in its shim page and flat image (M2-5) | 17 | 134 |
| | **Total** | **69** | **213** |

### `tests/fake-board.py` (from B7's `tests/fake-board.py`)

Original 402 lines, copy 524; 33 hunks, 50 removed, 172 added, 352 unchanged. B7's stand-in with the MVP's preflight facts and one capture per loaded image; M1-5's resets, boot IDs, and firmware identity.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the resets and the firmware identity (M1-5) | 19 | 36 |
| 1 | Names only | 2 | 2 |
| 2 | B7's results path and its recorded System RAM and FDT reservations, named as B7's | 6 | 6 |
| 3 | Settings: `h` on hart 2, HSM in the log, a capture per loaded image, the feed delay; the board's state across resets: its boots, the kexec loaded, Fedora up or down, and the resets (M1-5) | 1 | 51 |
| 4 | The preflight's answer: synthetic topology lines (marked as not K3 facts), `h` per hart, HSM detection, and the SBI implementation line (M1-5) | 12 | 52 |
| 5 | kexec: the capture of the image loaded; `feed` with its delay; each SSH and SCP call first applies the resets the fake dongle took, each a new boot (M1-5) | 10 | 25 |
| | **Total** | **50** | **172** |

### `tests/run-tool-dry-run.sh` (from B7's `tests/run-tool-dry-run.sh`)

Original 365 lines, copy 1573; 56 hunks, 233 removed, 1441 added, 132 unchanged. The MVP's preflight, load-check, probe, campaign, and failure cases on the fake board, with the board records; the `same-second` case (after M0-C's review); the platform records' checks and the `tree-state` and `probe-record` cases (M0-6); M1-5's channel-page, firmware-identity, te-poc, `campaign-paused`, and remote-reset cases: 40 cases; and M1-6's checks of the platform record's M1 sections in three of them; M2-2's shared pages in place of the channel page in the preflight, load, and record checks; M2-5's five `anchor` cases, 45 cases; and Plan revision M2-A's board capture for `anchor-campaign`'s GCC `anchor` run, with the probe in a management wait checked in that case and `anchor-record`. Counted at the M2-7 content. Recounted at `804cd24c`: since M1-5 the diff aligns B7's kexec cases with the MVP's remade ones, and B7's preflight cases with M1-5's reset cases, so B7's cases are no longer one deletion (M0's row 5) and the MVP's no longer additions after B7's preflight; the rows follow the new alignment. M1-6 changed three hunks, one each in rows 0, 5, and 7 (at `804cd24c` the copy had 1,301 lines and the rows added 134, 430, and 350). M2-A replaced six hunks with five: two in row 0 (7 more added lines); one in row 3, inside its added lines, which changes no count; and three in row 7, now two, the diff taking B7's blank line 343 into a change (one more line removed, and 12 more added); at the M2-5 content (`da7d270f`) the copy had 1,555 lines, 57 hunks, 232 removed, 1,422 added, and 133 unchanged, row 0 removed 37 and added 172, and row 7 removed 45 and added 523.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the platform record in the `campaign` case and the `same-second`, `tree-state`, and `probe-record` cases (M0-6), M1-5's cases, and the platform record's M1 sections in the `campaign` and `te-poc-record` cases (M1-6), and the anchor cases (M2-5), with the board's recorded capture in `anchor-campaign` and the probe in a management wait in `anchor-record` (M2-A) | 37 | 179 |
| 1 | Names only | 4 | 4 |
| 2 | Arguments and paths; the kexec fixtures from the capture checker, with te-poc's (M1-5) and anchor's (M2-5); the board images and their specs, with te-poc's and its variants' (M1-5) and anchor's and its board variants', with anchor's report and measured inputs (M2-5) | 12 | 66 |
| 3 | Scratch and the SSH control directory; the FDT slot; a fake board that feeds each image's capture, anchor's among them (M2-5), and for the GCC `anchor` image the first M2 board campaign's capture as the board recorded it (M2-A); the fake `k3ctl` client and a fake dongle per case (M1-5) | 7 | 75 |
| 4 | `kexec_run` with the flat image and expectation; the `campaign` helper; `reset_run` and `reset_campaign` (M1-5) | 9 | 63 |
| 5 | B7's cases from `kexec-load-only` to `kexec-campaign`, against the MVP's preflight helper and its cases through `campaign-paused`: `preflight-pass` and `preflight-stops` (the MVP's PASS line, its regions, and the topology; the hart-region, MVP-region, no-`h`, and no-HSM stops), `preflight-m1` (the channel page, stop 7, and the firmware identity, stop 8; M1-5), the shared pages' region and stop since M2-2, `load-check` and `load-check-te-poc` (M1-5), `probe`, `campaign` and its board record, with the firmware and kernel beside M0's record, the channel page's region (the shared pages' since M2-2), the payload run's FAIL line, and no te-poc section in its platform record (M1-6), `reset-human` (M1-5), `same-second`, `tree-state`, `probe-record`, with the platform record's te-poc counters at 0 (M1-6), `kexec-refused`, `campaign-stop`, and `campaign-paused` (M1-5) | 86 | 449 |
| 6 | B7's `kexec-overlap`, `kexec-fail`, and `kexec-timeout` cases (with busy, not-tmpfs, and tampered) against the MVP's: each fake board named for its case, captures from the fixtures, the MVP's result lines, and the busy hart region and channel page (M1-5), the last shared page since M2-2; B7's `preflight` helper's first lines against `kexec-control-path` and M1-5's `te-poc-selector` | 32 | 70 |
| 7 | B7's preflight cases against M1-5's: `te-poc-campaign` and `te-poc-record` (the procedure with `K3_RESET=k3ctl` into one record), with the platform record's te-poc runs, Denials on K3, The channel, and the negatives' FAIL lines in `te-poc-record` (M1-6), M2-5's `anchor-selector`, `load-check-anchor`, `anchor-report`, `anchor-campaign`, and `anchor-record`, with M2-A's checks of the probe in a management wait in the last two (the costs; the platform record's subsection, its sentence, and `pings_in_wait=1`), the fourteen other `reset-*` cases, `fake-k3ctl-refuses`, and `k3ctl-command-log` | 46 | 535 |
| | **Total** | **233** | **1441** |

### `tools/k3-preflight.sh` (from B7's `scripts/k3-preflight.sh`)

Original 161 lines, copy 272; 18 hunks, 35 removed, 146 added, 126 unchanged. `h` and Sstc on harts 0 to 2, HSM in Fedora's log, and the topology for the platform record; M1-5's firmware identity (stop 8), the channel page, and the workstation's `k3ctl` client, recorded; since M2-2 the three shared pages in its comment (its region check is the loader's).

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the firmware identity and the reset variables (M1-5), and the shared pages' region line (M2-2) | 17 | 34 |
| 1 | Names only | 3 | 3 |
| 2 | Per hart: `h` and Sstc in the DT and in cpuinfo; the DT CPU links, `/cpus/cpu-map`, cache nodes, and sysfs topology (new); HSM in Fedora's log | 5 | 49 |
| 3 | B0's kexec facts and the FDT reservations; the firmware's identity in Fedora's log against M0's record's, `ID=0x1 Version=0x10006`, and the workstation's `K3_RESET`, pin, and client digest, recorded only (M1-5); every MVP extent through the loader's region check | 3 | 30 |
| 4 | The PASS rule: `h` and Sstc on harts 0 to 2 in both sources, HSM detected, the region check passing, and the firmware identity M0's (stop 8; M1-5); the summary line | 7 | 30 |
| | **Total** | **35** | **146** |

### `tools/k3-run.sh` (from B7's `scripts/k3-run.sh`)

Original 309 lines, copy 810; 35 hunks, 56 removed, 557 added, 253 unchanged. One MVP run: the flat image and expectation, the SSH control socket in the build tree, the capture checker, and a REFUSED run as stop 6; M1-5's authority report, anchored terminal expression, and remote reset; M2-5's v3 expectation, checked with its report and the measured domain's kernel and DTB, which `run.txt` records.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with the remote reset and its variables (M1-5), and a v3 expectation's measured inputs, `K3_KERNEL` and new `K3_MEASURED_DTB` (M2-5) | 21 | 109 |
| 1 | Names only | 7 | 7 |
| 2 | The usage with `--check-reset`; paths and settings: the capture checker, the anchored terminal expression (M1-5), the flat image, the expectation, the authority report (M1-5), the variant, the kernel, the measured DTB (M2-5), the pins, and the tail; the reset's settings, `reset_settings` (the client against `tools/k3ctl.sha256`; stop 10), and `--check-reset` (M1-5) | 5 | 100 |
| 3 | The SSH control directory under `TMPDIR`, with its length check | 3 | 9 |
| 4 | The image check with the flat image and variant, and a v2 expectation's authority report (M1-5), a v3 one's too, with its measured inputs, refused without them (M2-5); the reset's settings checked before anything touches the board (M1-5); the expectation's record, and the report's and the reset method's (M1-5), and the measured inputs' names and SHA-256 (`measured=`, M2-5) | 3 | 56 |
| 5 | Steps 2 and 4 (M1-5): the boot ID before the run, a UUID with `K3_RESET=k3ctl`; the kexec entry address from the loader's line | 3 | 11 |
| 6 | The MVP's terminal lines and tail; the capture check in kexec mode against the expectation and report, and a v3 one's measured inputs (M2-5); a REFUSED run recorded as stop 6; after a passing run's terminal marker, the one reset through `k3ctl` (`status`, `reset`), Fedora's new boot ID, the settle wait, and `reset.txt` (M1-5) | 14 | 265 |
| | **Total** | **56** | **557** |

### `tools/k3-campaign.sh` (from B7's `scripts/k3-campaign.sh`)

Original 92 lines, copy 224; 19 hunks, 38 removed, 170 added, 54 unchanged. `IMAGE:FLAT:EXPECT[:VARIANT]` specs, and a stop at the first run that does not pass; M1-5's remote reset and the pause when Fedora does not return; M2-5's v3 expectations in its comment.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment, with `K3_RESET=k3ctl`, the waits, and the pause (M1-5), and a v3 expectation's report and measured inputs (M2-5) | 12 | 50 |
| 1 | Names only | 0 | 0 |
| 2 | Arguments: RUNS and the specs, each of readable files; the reset method and the return and poll waits, and the reset's settings and client through `k3-run.sh --check-reset` before anything touches the board (stop 10) (M1-5) | 9 | 44 |
| 3 | The runs: each spec RUNS times, each waiting for a new boot ID not yet used by the campaign, after a human reset for `K3_RETURN_SECONDS` or after `k3-run.sh`'s reset for `K3_RESET_RETURN_SECONDS` (M1-5); the first run that does not pass ends the campaign (B7's counted failures and went on); a board that does not return after a `k3ctl` reset is stop 10, and one that does not return after a human reset pauses the campaign (M1-5) | 13 | 52 |
| 4 | B0's summary; the PAUSED line with the runs left and exit 75 (M1-5); who resets the board next (M1-5); and the STOP line | 4 | 24 |
| | **Total** | **38** | **170** |

## New files

- **`src/mvp-ring.{h,c}`:** the rings (plan, "Hart region", Rings), in
  restricted C with bounded loops and no CSR, fence, SBI call, I/O, lock,
  or atomic read-modify-write. Plan revision M1-B adds the writer's reads
  of the reader's tail and of its own published head
  (`be_mvp_ring_taken`, `be_mvp_ring_published`); M2-3, the management
  records among the types each ring carries.
- **`src/mvp-hart.{h,c}`:** the binding, block descriptor, and state page;
  the block check; the control loop; the drain order (Plan revision
  M0-C.1); the overlap and Q5's floor; the printed LINE. Restricted C, no
  CSR, fence, SBI call, or I/O. M1-3 adds the channel's arguments to the
  control loop (`be_mvp_control_channel`), its DENIAL step, and SHUTDOWN's
  reconciliation of the denial count; M2-3 the sealed pages' arguments
  (`be_mvp_control_pages`), hart 0's management state and the grants
  (`be_mvp_control_mgmt`), the management steps, the pending requests,
  the paused and terminated domains, and the completion rule.
- **`src/mvp-sbi.h`:** the monitor's own HSM and IPI identifiers, the HSM
  states, the pure checks of their results, and `BE_MVP:02`'s census
  (Plan revision M0-A.2).
- **`tests/ring-test.c`, `tests/hart-test.c`:** their host tests, each with
  pseudo-random runs checked against an independent model.
- **`tools/make-control.py`:** the Make controls, R5's semantics in Python
  with an allowlist (see [Make controls](#make-controls)); M1-1 admits
  `MVP_SCENARIO_NAME` and M1-5 `SCENARIO`, and its self-test has 55
  cases (49 at M0). Plan revision M4-A.2 admits `K3_RECORD_TITLE` (57
  cases); M5-2 drops `RUNS`, `VARIANT`, and `SCENARIO` and admits
  `K3_PREFLIGHT`, `K3_ENV_CONFIRM`, and `K3_ENV_ACCEPT_V` (59 cases).
- **`tools/lock/tool-lock.py`, `tool-lock.conf`, `closure.txt`:** the tool
  lock, its tool (check, refresh, and a 26-case self-test), and the
  evaluator's package closure; R3's lock (`tests/r3/tool-lock.conf`) set
  the per-role fields. Plan revision M0-B adds the closure's RPM digests
  and `bind_closure()`, the host-only roles and the evaluator's marker,
  and the version status of a role (scp's); the self-test has 46 cases.
  M5-3 adds the host-only roles `mke2fs` and `sfdisk` and the U-Boot pins
  (`MVP_PIN_UBOOT_TAG`, `_COMMIT`, `_DEFCONFIG`, `_BUILD_SCRIPT`, and
  `_BIN_SHA256`), and `0e733e76` the host-only role `tmux`: 32 roles, 6
  host-only, the closure unchanged; the self-test has 50 cases.
- **`tools/evaluator/Containerfile`, `evaluate.sh`:** the clean evaluator;
  the `FROM` line is `model/Containerfile`'s. M0-4 adds the host bundle's
  check, the records, and the image comparison to `evaluate.sh`; M0-B the
  host's lock check first, the closure's fetch, the build from the
  verified cache with repositories disabled and five base packages removed
  by name, and the Containerfile's SHA-256 in the image's tag.
- **`tools/evaluator/fetch-closure.py` (M0-B):** the closure's RPMs into a
  verified local cache, by exact NEVRA and SHA-256, from `MVP_RPM_CACHE`,
  Fedora's repositories, Fedora's updates archive, or koji's signed copy,
  and, once, `--record`, which derives the digests from files verified by
  the Fedora 44 signature and by the installed packages' header digests
  (or B3's pins); its offline self-test has 48 cases.
- **`mvp`:** the wrapper (`help`, `check`, `port`, `host-test`,
  `tool-lock`, `evaluate`, M0-3's `image`, `image-check`, `variants`,
  `probes`, and `budgets`, and M0-4's `qemu`, `kexec-rehearsal`,
  `evidence`, `board-evidence`, `k3-preflight`, `k3-load-check`,
  `k3-probe`, and `k3-campaign`; a subcommand whose target does not exist
  prints `BE_MVP: not-implemented-until-M0-<n> <name>` and exits 3). M1-5
  adds `SCENARIO` to its caller variables and the remote reset's settings
  to those it passes to the `k3-*` commands; M2-5 names `anchor` among
  `SCENARIO`'s values in its help; M4-1 adds `claim-ledger check`,
  `render`, and `self-test`, and M4-4 `rc-record`; M5-2 drops
  `kexec-rehearsal` and `k3-load-check` and `RUNS`, `VARIANT`, and
  `SCENARIO`, and adds `k3-stage`, `k3-env record|install|restore`,
  `k3-characterize`, the caller variables `K3_PREFLIGHT`, `K3_ENV_CONFIRM`,
  and `K3_ENV_ACCEPT_V`, and the console tool's settings; M5-3 adds
  `uboot-rehearsal`.
- **`src/mvp-hartentry.S`, `src/mvp-hartmain.c` (M0-3):** the hart entry
  with the image's one `fence.i` helper, and the domain harts' runtime:
  the block check, arming, the root's install, READY and ENTERED, the
  first entry, the exit dispatch, and the FAIL path with its fallback.
  M1-3 adds the denial action's executor (`deny()`), Plan revision
  M1-B the FAIL path's wait on `be_mvp_ack_wait_step`, and M2-3 the
  management call's request and wait (`mgmt_call`, `wait_serve`) and the
  paused and terminated parks (`parked`).
- **`scenarios/two-guests/scenario.json`, `tools/gen-scenario.py` (M0-3):**
  the scenario as data (Q9) and its generator, with a 29-case self-test;
  34 cases since M0-4, which writes each probe image's whole control
  sequence into its expectation and `sbi-time`'s nonzero `time` field.
  M1-1 adds schema v2 (`be-mvp-scenario-v2`), the policy check before any
  header, and the channel record, accepted exits, and configuration
  identity in the header; the self-test runs 36 cases for `two-guests` and
  41 for `te-poc`, and `two-guests`' expectation files are M0's byte for
  byte. M2-1 adds schema v3 (`be-mvp-scenario-v3`, `be-mvp-expect-v3`)
  with the pages, the secret, the expected measurement, the grants, and
  `anchor`'s expectations and report, 53 self-test cases for `anchor` (54
  since M2-5's fixes); 2,594 lines at the M2-5 content. Plan revision M2-A
  writes `spv=<S>` on the probe line of the images with the management
  extension (open item 61), with one more `anchor` self-test case, 55;
  2,623 lines at the M2-7 content.
- **`src/mvp-probe.{h,c}`, `src/mvp-probe-arch.S` (M0-3):** the probe
  module, linked only into the probe images: hart 0's driver and printer,
  the domain hart's handler of the stub's exits, the stub's bytes, and,
  in the VMID images only, the raw `hgatp` write.
- **`guest/probe-stub.{S,c,lds}` (M0-3):** the VS probe stub, a bare-metal
  guest in B5's style (`bringup/k3-b5/guest/`): one page at GPA
  `0x8020_0000`, no data or BSS, and its own copy of the probe calls'
  numbers (a mismatch fails the probe run closed).
- **`tools/budgets.py` (M0-3):** the budgets on every image and on a
  measurement link, with a 12-case self-test (M0-A.1 adds the MVP region
  and the exact flat image).
- **`tests/check-capture.py`, `tests/fixtures/` (M0-4):** the capture
  checker (see [Harness](#harness-m0-4)), with its 36-case self-test (34
  at M0-4), its 154 mutations, and its twelve fixtures: eleven QEMU
  captures, six of them made again from the M0-C images, and the first
  board scenario run's capture (Plan revision M0-C.2). Its approach (one
  parse, the kexec handoff, a JSON record) follows B7's capture checker;
  its rules are new. M1-4 adds schema-v2 expectations and the
  reconciliation of the denial log, the channel, and the report, and M1-5
  the te-poc board images' check and dry-run captures; since Plan
  revision M1-B the self-test has 47 cases and the mutations number 170,
  on seventeen fixtures and `m0-guest-pins.txt` (below). M2-5 adds
  schema-v3 expectations, the measurement's recomputation, the requests'
  HMAC-SHA-256, the management log, and the transitions: 65 cases and 224
  mutations on twenty-two fixtures and the two pin files; 3,582 lines.
  Plan revision M2-A adds the IPI probe's rule (`ping_findings`) and the
  first M2 board campaign's stopped `anchor` capture as a passing
  fixture: 70 cases and 229 mutations on twenty-three fixtures and the
  two pin files; 3,754 lines at the M2-7 content. M5-2 adds the `uboot`
  mode, `--image-bytes` and `--image-crc32`, and two `uboot` fixtures
  (`board-uboot-two-guests-gcc.log`, `qemu-uboot-two-guests-clang-hart6.log`):
  108 cases and 280 mutations; `--mode kexec` stays, test-only (M5 plan,
  Q4); 4,361 lines.
- **`tools/evidence.py` (M0-4):** the development bundle, the board
  record, `--verify`, `--images`, and `--compare-images`, with a 17-case
  self-test (25 since M1-5, 28 since M2-5). M1-4 adds the `te-poc` images,
  scenario, policy, report, and policy records to the bundle, and M1-5
  each run's `reset.txt`, the policy records, and the serial-log note to
  the board record; M2-5 anchor's images, the module, scenario, report,
  and policy records, and each anchor run's measured inputs. M0-6 runs
  the platform record's generator in every board
  record, checks its two files against B0's identifying-data rule, and
  writes the manifest again to cover them; and it reads the tree's state
  for a board record before it creates the load checks' staging
  directory (open item 41), which the dry run's `tree-state` case tests.
  M5-2 makes the board record a session's (`launcher=uboot-autoboot-nvme`;
  each run's whole capture judged again in `uboot` mode, its committed
  excerpt from `Autoboot in`; the session's keystroke log, resets,
  staging record, environment verdicts, and preflight after), adds the
  U-Boot rehearsal's records to the development bundle in place of the
  kexec rehearsal's, and adds a MAC address and a `serial#` value to the
  code names and to `identifying()`; 1,660 lines.
- **`tools/platform-record.py` (M0-6):** the platform record of a board
  record (plan, "Platform record: probes and negative images"; see
  [Harness](#harness-m0-4)), 570 lines; the dry run's `campaign`,
  `same-second`, `tree-state`, `probe-record`, and `campaign-stop` cases
  exercise it. M1-5 adds the resets and the Serial log paragraph from the
  campaign's note (schema v2; 633 lines at `804cd24c`), and M1-6 the
  Preflight beside M0's record, te-poc runs, Denials on K3, The channel,
  and the other runs' failure lines (1,139 lines at the M1-6 content),
  which the `te-poc-record` case also exercises; M2-2 the shared pages'
  region line, and M2-5 M2's sections (1,492 lines at the M2-5 content),
  which the `anchor-record` case exercises; Plan revision M2-A "The IPI
  probe in a management wait" and `pings_in_wait=` (1,585 lines at the
  M2-7 content). M5-2 (schema v3) records the reset launches (each run's
  launcher, `be_image`, capture range, reset and terminal times,
  attribution, and boot hart from the shim line), the preflight before
  and after side by side, and a session's cold-boot probe values beside
  M0's, each labelled (1,646 lines).
- **`results/20261025-com260/` (M0-6):** M0-5's second campaign's board
  record, written by `./mvp/mvp board-evidence`, never by hand, against
  the M0-6 content and committed after it (see
  [Results](#the-board-record-and-the-platform-record-m0-6-2026-10-26)).
- **`scenarios/te-poc/policy.te`, `scenarios/te-poc/scenario.json`
  (M1-1):** security model v1's Instance 2 verbatim, in Part 2's concrete
  syntax, and the v2 scenario: the labeling, the need sets, the manifest
  with the one channel, the accepted exits with `denial`, the roles, and
  the expected lines, denials, and report.
- **`scenarios/te-poc/negatives/` (M1-1):** the two build-time negatives,
  `undeclared-flow.te` and `undeclared-flow.json`, and
  `grant-without-rule.json`, each failing exactly its declared analyses.
- **`tools/policy-check.py` (M1-1):** the offline checker: A1 to A6 and A8
  as pure functions, A7 recorded as vacuous, the authority report
  (`be-mvp-authority-report-v1`; `-v2` since M7-4), a 33-case self-test, and seven
  mutations; 890 lines, the plan's limit 900; the Python standard library
  alone. M2-1 adds the `domain` class, the management grants in A8, A3's
  extension, and Instance 3: a 45-case self-test and fourteen mutations,
  1,098 lines, the M2 plan's limit 1,100 (Q17).
- **`tests/deny-test.c` (M1-3):** the denial decision's host test (see
  [Tests](#tests)), 30 scenarios and 2,357 assertions, GCC = Clang; 38
  and 2,933 since M2-3, with anchor's three pages.
- **`guest/mvp-kernel.config` (M1-4):** the MVP's two-option Kconfig
  fragment, `CONFIG_DEVMEM=y` and `CONFIG_STRICT_DEVMEM=y`, merged after
  B6's unchanged fragment (M1 plan, Q2); since M2-4 also
  `CONFIG_MODULES=y`, with the sixteen lines it makes visible listed in
  its comment (M2 plan, Q16).
- **`tests/fixtures/qemu-te-poc-gcc.log`, `qemu-reader-write-gcc.log`,
  `qemu-no-inject-gcc.log`, `qemu-te-poc-gcc-stop6-pid1.log`,
  `m0-guest-pins.txt` (M1-4), and `k3-no-inject-gcc-stop6-fallback.log`
  (Plan revision M1-B):** M1's QEMU captures, the guest pins M0's
  fixtures were captured with, and the first M1 board campaign's stopped
  `no-inject` capture (see [Harness](#harness-m0-4)).
- **`tools/k3ctl.sha256` (M1-5):** the `k3ctl` client's SHA-256 and the
  forms of its path and device; `k3ctl` is not a lock role.
- **`tests/fake-k3ctl.py` (M1-5):** the dry run's fake dongle, answering
  from a JSON spec as the firmware's protocol does, refusing anything but
  `ping`, `status`, and `reset`, and logging every command.
- **`results/20261027-com260-m1b/` (M1-6):** the second M1 campaign's
  board record, to be written by `./mvp/mvp board-evidence`, never by
  hand, against the exact M1-6 commit and committed after it (see
  [M1-6](#m1-6-2026-10-27)).
- **`scenarios/anchor/policy.te`, `scenarios/anchor/scenario.json`
  (M2-1):** security model v1's Instance 3 as the M2 plan prints it, in
  Part 2's concrete syntax (37 lines), and the v3 scenario (246 lines):
  the labeling, the need sets, the three pages with each domain's rights,
  the management grant, the public 32-byte test secret, the measured
  domain, the accepted exits with `denial` and `mgmt`, the roles `host`
  and `prot`, the declared denials and management sequences, and the four
  request messages (see
  [M2-1 and M2-2](#m2-1-and-m2-2-at-f149eea0-and-d6667862-2026-10-27)).
- **`scenarios/anchor/negatives/` (M2-1):** the two build-time negatives,
  `grant-without-rule.json` and `secret-flow.json` (17 lines each), each
  failing exactly its declared analyses, A8 and A3.
- **`src/mvp-sha256.{h,c}` (M2-2):** FIPS 180-4 SHA-256, incremental and
  one-shot, and HMAC-SHA-256 (RFC 2104) in restricted C (87 and 249
  lines): no table but the 64 round constants, bounded loops; linked into
  the images whose scenario declares pages, in the MVP region, and
  compiled into the guest init with `guest/be/types.h`.
- **`tests/sha256-test.c` (M2-2):** its host test (257 lines), 16
  scenarios and 626 assertions, GCC = Clang (see [Tests](#tests)).
- **`guest/mgmt/be-mgmt.c` (M2-4):** the management module (102 lines): a
  misc character device, `/dev/be-mgmt` at minor 243, whose one ioctl,
  `0xc0184242`, makes one call of the management extension through the
  kernel's `__sbi_ecall` and returns its error code. It is the
  repository's one `GPL-2.0-only` file, as the responsible human answered
  Q20 (`gpl 2.0 only ok`): it is linked into the GPL-2.0-only guest kernel
  and calls its exported `__sbi_ecall`. A test input built against the
  external pinned tree, never part of the Beryllium image (see
  [Guest](#guest)).
- **`guest/mgmt/Kbuild` (M2-4):** the module's Kbuild file (8 lines,
  `obj-m := be-mgmt.o`), for the out-of-tree build with `M=` and `MO=`.
- **`guest/be/types.h` (M2-4):** the three scalar types `src/mvp-sha256.h`
  takes (28 lines), for the init, which compiles the SHA-256 against
  nolibc and the UAPI headers alone; the same typedefs under the same
  guard as the monitor's `include/be/types.h`.
- **`tests/fixtures/qemu-anchor-gcc.log`, `qemu-secret-shared-gcc.log`,
  `qemu-response-writable-gcc.log`, `qemu-wrong-measurement-gcc.log`,
  `qemu-no-grant-check-gcc.log`, and `m1-guest-pins.txt` (M2-5):** M2's
  five QEMU captures (266, 77, 77, 88, and 224 lines), CRs removed, and
  the guest pins M1's fixtures were captured with (28 lines, `git show
  ff84533c:mvp/guest/pins.txt`), which the capture checker binds by
  SHA-256 (see [Harness](#harness-m0-4)).
- **`tests/fixtures/k3-anchor-gcc-m2a-ping-in-wait.log` (Plan revision
  M2-A):** the first M2 board campaign's stopped `anchor` run
  (`20261028T023339Z`, GCC), its `serial.log` with CRs removed (397
  lines), which `tests/check-capture.py --self-test` must judge PASS under
  M2-A.1: hart 2's PONG `spv=0` inside its first management wait (see
  [M2-6's first board campaign and its stop](#m2-6s-first-board-campaign-and-its-stop-stop-condition-6-plan-revision-m2-a)).
- **`results/20261028-com260-m2a/` (M2-7):** the second M2 campaign's
  board record, to be written by `./mvp/mvp board-evidence`, never by
  hand, against the exact M2-7 commit and committed after it (see
  [M2-7](#m2-7-2026-10-28)).
- **`docs/claim.md` (M4-1):** the MVP claim and its required limit, byte
  for byte the M4 plan's fixed text, and the "Forbidden phrasings" list,
  its single source, which `tools/claim-ledger.py` reads: 35 literals, 3
  conditional phrasings, and 2 review items; 126 lines. Every other release
  surface links to it rather than restating it.
- **`docs/claim-ledger.json`, `docs/claim-ledger.md` (M4-1):** the claim
  ledger (`be-mvp-claim-ledger-v1`): the JSON the source, the Markdown
  rendered from it by `tools/claim-ledger.py render`; 28 claim rows, each
  with its methods from the fixed vocabulary, its evidence (66 artifacts in
  all, each with its SHA-256 and source commit), and its non-claim, 6 of
  them marked historical; 12 unproved-boundary items; the 2 review items;
  and the release identity, whose two commits stay null until M4-4 and
  M4-6. 889 and 233 lines; M4-3 rewords row C-23's non-claim.
- **`docs/guide.md` (M4-2):** the researcher guide, in the M4 plan's nine
  sections (what this is; build; run in QEMU; run on the board; write a
  scenario; read the authority report; read an evidence bundle and a board
  record; the evaluator; where the rest is), every `./mvp/mvp` command one
  that `mvp help` lists (19 commands, 39 uses); 1,043 lines.
- **`docs/ai-assistance.md` (M4-3):** the AI-assistance disclosure (M4
  plan, Q7): the responsible human; the assisting system, its trailers, and
  its models by role; what the assistance did, including the board resets
  and the pushes it made on the responsible human's direction, and what it
  never did; the acceptances; the destination's rule for a Linux
  submission; and its scope; each statement with its source; 275 lines.
- **`tools/claim-ledger.py` (M4-1):** the ledger's checker. `check` prints
  nine checks: the schema; the methods; each artifact's path and SHA-256,
  a cited `MANIFEST.sha256` verified against its record; the named
  commits, on the host only (skipped, and saying so, where `git` finds no
  repository); the rendering; the guide's `./mvp/mvp` commands against
  `mvp help`; the phrasing rules over `docs/*.md`; the privacy rule over
  `docs/*.md` and `results/*-rc/`; and the SPDX and copyright lines.
  `render` writes the table, `join` adds its records to a verified bundle,
  and `--self-test` runs 19 seeded single-defect mutations, each failing
  exactly its own check, and 4 variants that pass. The Python standard
  library and `tools/evidence.py`'s manifest functions; 682 lines. Since
  M5-2 its privacy rule also finds a MAC address and a `serial#` value,
  and its self-test has 23 mutations and 6 variants (706 lines). M5-4
  rewrites the four surfaces for release candidate 2 (the claim's board
  clause and limit, the guide's sections 2 to 4, 7, and 9, the disclosure
  through M5, and the ledger's C-10, C-20, and historical rows).
- **`tools/rc-record.py` (M4-4):** the release-candidate record of the
  seven gates from explicit inputs, each checked to name the candidate
  tree, with a seeded self-test; since M5-2 its rehearsal gate is the
  U-Boot rehearsal's (602 lines).
- **`results/20261029-rc/`, `results/20261029-com260-rc/` (M4-4, M4-5):**
  release candidate 1's two records, the gates at `d42b9ec0` and the board
  campaign of eleven RAM-only `kexec_load` runs, committed in `c5df0cfa`.
- **`tools/k3-make-partition.sh`, `tests/test-k3-make-partition.sh`,
  `tests/fake-partition-tools/` (M5-1):** the human-run partition tool
  (1,226 lines) and its host self-test (365 lines, 22 cases) on fake block
  tools and a fixture of the board's disk (see
  [M5-1 to M5-4](#m5-1-to-m5-4-2026-10-29-and-30)).
- **`tools/k3-console.sh`, `tools/k3-uboot.py` (M5-2):** the console tool,
  the only path from automation to the U-Boot prompt and the only tool
  that resets the board (551 lines), and its reader of the serial log
  (510 lines): the templates, the echo-checked typing in pieces of at most
  60 characters, the fresh-prompt rule for `saveenv`, the keystroke log,
  the port-open rule, the banner check against the resets, the restore
  rule's normalization and comparisons, and the characterization's
  extents.
- **`tools/k3-stage.sh`, `tools/k3-env.sh` (M5-2):** the session's staging
  of its 14 images with their SHA-256 and CRC-32 lists (181 lines), and
  the record, install, select, restore, and characterization of U-Boot's
  saved environment (468 lines).
- **`tools/platform-probe.py`, `tests/test-platform-probe.py` (M5-2):**
  `tools/kexec-load.py`'s read-only probe of the FDT's reservations and
  its layout rule, kept when the loader went (316 lines), and their tests
  (443 lines), renamed from `tests/test-kexec-load.py`.
- **`tests/fake-uboot.py`, `tests/fixtures/board-uboot-two-guests-gcc.log`,
  `qemu-uboot-two-guests-clang-hart6.log` (M5-2):** the dry run's fake
  U-Boot (510 lines), standing in for the operator's tmux and picocom and
  the board's ROM, SPL, and U-Boot, with the BSP's stamps and noise and
  its faults; and the capture checker's two `uboot` fixtures, each a fixed
  template of U-Boot's lines in front of recorded monitor output.
- **`tests/uboot-rehearsal.sh`, `tests/uboot-rehearsal/run-qemu-uboot.py`
  (M5-3):** the U-Boot rehearsal in QEMU (407 lines) and its driver and
  own checks (789 lines, a 49-case self-test).

## Budgets (measured)

Measured by `tools/budgets.py` (`make -C mvp budgets`) on 2026-10-27 at
17:39 UTC, in the check of Plan revision M1-B's content before
`804cd24c` was committed (`build/mvp/records/budgets.txt`;
`BE_MVP_BUDGETS: PASS measured=22`), against the M0 plan's budgets
("Budgets"), Plan revision M0-A.1's rows, the M1 plan's ("Budgets"), and
the accepted `ASSERT`s: monitor text, the accepted code and the MVP
assembly, ending at or below `0x1_0200_8000`; accepted data and BSS at or
below `0x1_0200_f000`; the MVP pool `0x10000` and the hart region
`0x20000`; the MVP region's text, rodata, data, and BSS together at most
`0x40000`; the flat image exactly `0xa4000` bytes; the boot image at most
4 MiB; and the two links' images identical. Every row passes for both
toolchains:

| Image | Text end | Spare | Data/BSS end | MVP text | rodata | data | BSS | MVP region | Region spare |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GCC `two-guests`; `hart-start` | `0x1_0200_4580` | `0x3a80` | `0x1_0200_8750` | `0x4520` | `0xdb0` | `0x8a8` | `0xce0` | `0x6858` | `0x397a8` |
| GCC `exit-budget`, `run-timeout` | `0x1_0200_4580` | `0x3a80` | `0x1_0200_8750` | `0x4510` | `0xdb0` | `0x8a8` | `0xce0` | `0x6848` | `0x397b8` |
| GCC `ring-full` | `0x1_0200_4580` | `0x3a80` | `0x1_0200_8750` | `0x4580` | `0xdb0` | `0x8a8` | `0xce0` | `0x68b8` | `0x39748` |
| GCC `te-poc`; `reader-write` | `0x1_0200_4580` | `0x3a80` | `0x1_0200_8750` | `0x49e0` | `0xfb8` | `0x8a8` | `0xce0` | `0x6f28` | `0x390d8` |
| GCC `no-inject` | `0x1_0200_4580` | `0x3a80` | `0x1_0200_8750` | `0x4680` | `0xee0` | `0x8a8` | `0xce0` | `0x6ae8` | `0x39518` |
| Clang `two-guests`; `exit-budget`, `run-timeout`, `hart-start` | `0x1_0200_47b0` | `0x3850` | `0x1_0200_8710` | `0x4bf0` | `0xd78` | `0x8a8` | `0xce0` | `0x6ef8` | `0x39108` |
| Clang `ring-full` | `0x1_0200_47b0` | `0x3850` | `0x1_0200_8710` | `0x4c30` | `0xd78` | `0x8a8` | `0xce0` | `0x6f38` | `0x390c8` |
| Clang `te-poc` | `0x1_0200_47b0` | `0x3850` | `0x1_0200_8710` | `0x50e0` | `0xf50` | `0x8a8` | `0xce0` | `0x75b8` | `0x38a48` |
| Clang `reader-write` | `0x1_0200_47b0` | `0x3850` | `0x1_0200_8710` | `0x50d0` | `0xf50` | `0x8a8` | `0xce0` | `0x75a8` | `0x38a58` |
| Clang `no-inject` | `0x1_0200_47b0` | `0x3850` | `0x1_0200_8710` | `0x4d90` | `0xe90` | `0x8a8` | `0xce0` | `0x71a8` | `0x38e58` |
| GCC `probe-platform` | `0x1_0200_4580` | `0x3a80` | `0x1_0200_88b0` | `0x3b70` | `0xe78` | `0x8a8` | `0x1318` | `0x65b0` | `0x39a50` |
| GCC `probe-vmid-distinct`, `-shared` | `0x1_0200_4590` | `0x3a70` | `0x1_0200_88b0` | `0x3510` | `0xb58`, `0xb50` | `0x8a8` | `0x1318` | `0x5c30`, `0x5c20` | `0x3a3d0`, `0x3a3e0` |
| Clang `probe-platform` | `0x1_0200_47b0` | `0x3850` | `0x1_0200_8860` | `0x3f40` | `0xddc` | `0x8a8` | `0x1318` | `0x68e0` | `0x39720` |
| Clang `probe-vmid-distinct`, `-shared` | `0x1_0200_47c0` | `0x3840` | `0x1_0200_8860` | `0x3900` | `0xacf`, `0xac5` | `0x8a8` | `0x1318` | `0x5f90` | `0x3a070` |

Every image's flat image is `0xa4000` bytes and its boot image
`0x227000` (`0x223000` before M1-4, whose guest kernel is `0x4000` bytes
longer: `kernel_bytes=0x17f3b4`, DTBs at `0x225000` and `0x226000`); its
pool is `0x10000` bytes, its hart region `0x20000`, and its two links
identical. The boot image's other variants (`payload`, `init-exit`,
`rdcycle`, `sbi-time`, `shim-rule`) carry their toolchain's `two-guests`
monitor. The measurement link remains for a toolchain left out of
`IMAGE_TOOLCHAINS` and is not used. The MVP region's "data" is the
initialized data and its BSS the zeroed rest (the probe images' larger
BSS holds the probe's words); a probe VMID image's text gains the raw
switch, and each probe image's accepted rodata the VS stub's bytes.

**M1's changes.** M1-3 moved the accepted code extent's text end up by
`0x40` bytes for both toolchains (`0x1_0200_4540` to `0x1_0200_4580` for
GCC, `0x1_0200_4770` to `0x1_0200_47b0` for Clang), where its assembly
changes are the vector's `vsstatus` store and `be_mvp_arch_inject`. M1-2 and
M1-3 grew the MVP region in every image, which links their C (the channel's
build, walk, and check; the decision; the DENIAL codec and step): its text,
its rodata (`0xdb0` and `0xd78` in the `two-guests` images, from `0xd60` and
`0xd20`; `0xfb8` and `0xf50` in `te-poc`), and its BSS, by `0xb8` bytes in
every image. The MVP region now holds at most `0x75b8` of its `0x40000`
bytes (Clang `te-poc`), against the M1 plan's inference of `0x1000` to
`0x2000` more than M0's `0x5eb0` (GCC) and `0x6410` (Clang): `0x1078` and
`0x11a8` more in the `te-poc` images. Plan revision M1-B then added `0xb0`
or `0xc0` bytes of MVP text to every image and changed nothing else (see
[Plan revision M1-B](#plan-revision-m1-b)). The accepted data and every
other measure are as they were at M0-C.

**M2's changes** (`build/mvp/records/budgets.txt`, written by M2-5's
`./mvp/mvp check` on its working tree at 01:55 UTC on 2026-10-28,
`BE_MVP_BUDGETS: PASS measured=32`: the 22 images above, both toolchains'
`anchor` images, and anchor's four variants for each). The accepted code
extent's text end and the accepted data are as they were for every
image. M2-2 and M2-3 grew the MVP region in every image, which links their
C (the management records, decision, and waits; the page check), by
`0x840` (GCC) and `0x7f0` (Clang) bytes in the `two-guests` images and
`0x8e0` and `0x870` in `te-poc`'s (its text by `0x5e0` to `0x6e0` bytes,
its BSS by `0x1d0` in every image); the probe images' by `0x680` and
`0x620`. The `anchor` images, which also link the SHA-256 and hold the
pages, the grants, the secret, and the expected measurement, use
`0x8ac0` (GCC: text `0x5e20`, rodata `0x1510`, data `0x8a8`, BSS `0xee8`)
and `0x90c0` (Clang: `0x64e0`, `0x1448`, `0x8a8`, `0xee8`) of the
region's `0x40000` bytes, `0x1b98` and `0x1b08` more than M1's `te-poc`
images, against the M2 plan's inference of under 8 KiB; the largest is
Clang's `secret-shared` and `response-writable`, `0x90e0`, `0x36f20`
spare. Every boot image is `0x277000` bytes (open item 49).

Among these measures Plan revision M0-C's drain changed only the MVP
region's text: `0xb0` bytes more in GCC's scenario images and `0xc0` in
Clang's (from `0x3bd0` and `0x4160`, measured at `ebae089d` and
unchanged until M0-C), `0x90` and `0x80` in the `ring-full` images, and
`0xc0` in every probe image; the accepted code extent's text end, the
accepted data, and the MVP region's rodata, data, and BSS are as they
were.

Before M0-A, at `de05398a`, GCC's scenario monitor text ended at
`0x1_0200_7fe0` (`0x20` spare) and Clang's at `0x1_0200_87e0`, `0x7e0`
over, so no Clang scenario image existed (stop condition 3; open item 8).
The accepted port's text was `0x44b2` (GCC) and `0x471e` (Clang) bytes and
the MVP layer's own C and assembly text `0x4028` and `0x4664`; with the C
in the MVP region, the accepted code extent holds the accepted code as
linked (`0x3f80` bytes for GCC, `0x41b4` for Clang), the MVP assembly
(about `0x560` bytes), and B1's handoff (`0x60`), and `0x3ac0` (GCC) or
`0x3890` (Clang) bytes, about 14 KiB, stay spare.

## Open items

Each is recorded for the responsible human; none was worked around, and
no accepted byte was changed. Items 1, 8, 9, and 10 are resolved by Plan
revision M0-A; items 13 to 19 are new with it. Items 13 to 16 are resolved
by M0-4 as implemented, item 7 became stop condition 11, and items 20 to
26 are new with M0-4. Items 7 and 23 are resolved by Plan revision M0-B,
and items 27 to 31 are new with it. Items 32 to 37 are new with Plan
revision M0-C and the lock refresh at `804fa95f`: items 33, 35, and 36
are resolved, and item 32 by M0-5's second board campaign. Items 38 to 43
are new with M0-5's completion and M0-6, which also resolves item 24 and
the staging half of item 41. Items 44 to 46 are new with M1, which
resolves item 42 (its Q16, at `8c2cbbfd`) and, as implemented and tested
off the board, item 38's wording (Q18) and item 40's fixed text (M1-5);
item 43 is unchanged. Items 47 to 57 are new with M2's work packages M2-1
to M2-5. Items 63 to 67 are new with M4-1 to M4-3, each an observation
for the responsible human, and item 68 with M4-4's tool; M4-4's tool
resolves items 64 and 67 and closes 68 (`ca322220`), and Plan revision
M4-A resolves items 63 and 65; item 69 is new with it, and item 70 with
M4-4's gates. Items 71 and 72 are new with M5-2 and M5-3, and items 73 to
78 with M5-4, which also closes item 59 for M5's runs and gives item 60
M5's reset rule.

1. **The hart region's address in two plan lines (plan erratum; resolved
   by M0-A.4).** The
   plan places the region at `0x1_0204_4000` (`0x102044000`) in its
   decision record, Q1, "Hart region", "Port and copies", "Budgets", and
   the memory table: right after the pool, which ends there, and below
   Fedora's kernel at `0x1_0220_0000`. Two lines say `0x104044000`
   instead: the `BE_MVP:07` example under "Markers" (line 740) and the
   status record (`mvp_m0_hart_region=0x104044000+0x20000`, line 1037).
   That address is neither after the pool nor below Fedora's kernel: B7's
   preflight (`bringup/k3-b7/results/20261008-com260/preflight.txt`)
   recorded Fedora's running kernel image at `0x1_0220_2000`-
   `0x1_05c0_58f7`, which contains it. As directed, the implementation
   follows `0x102044000` everywhere, and `BE_MVP:07` prints
   `region=0x102044000`. Plan revision M0-A.4 records the two lines as
   transcription errors for `0x102044000` without editing the accepted
   text; every run at `ebae089d` that reached `:07` printed
   `region=0x102044000`.
2. **The reader's fence before releasing the tail (resolved as
   implemented).** Each reader executes `fence r, w` before it releases
   the tail (`be_mvp_arch_fence_r_w`, before `be_mvp_ring_release` in hart
   0's `visit`, its `drain` before M0-C, and the domain hart's `ipi`, and
   in the probe's ordering reader), and each writer `fence w, w` before
   publishing the head; the ring fence helper's comment in
   `src/mvp-trap.S` states the protocol. This adds to the plan's Rings
   text and should be confirmed there.
3. **Hart 0's writes to a block after the barrier (resolved as
   implemented).** After the barrier hart 0 writes a domain hart's block
   only through its own two ring views: the inbound ring's bytes and head
   (`ping`, `domain_failed`) and the outbound ring's tail (`visit`, its
   `drain` before M0-C); nothing else names a block after
   `publish_blocks`, and `src/mvp-runtime.c` says so. The plan's wording should read "except the
   inbound ring and the outbound ring's tail".
4. **Detecting `hart-ready` (resolved as implemented).** After the starts,
   hart 0 polls both rings and the `time` CSR in a bounded loop until both
   domains are READY, failing `hart-ready` at 2^26 ticks (or `run-timeout`
   at the budget), before it enters the `wfi` loop; `stimecmp` is written
   once, at the budget. The `hart-start` variant shows the start's
   failure; no QEMU run reached the READY wait's limit.
5. **Classes (resolved as implemented).** B7's `guest-timeout` is
   `run-timeout`, B7's `switch` and `scheduler` are gone, and the FAIL
   record accepts any class from a domain hart; every MVP class prints as
   the plan's markers name it.
6. **Beyond the task's lists.** The tool lock holds roles beyond Q8's list
   (each compiler's `cc1` and `collect2`, the host assembler and linker,
   and both Clang roles; see [Tool lock](#tool-lock)). The Make controls
   allow `MVP_RPM_CACHE`, B7's RPM-cache variable, beyond the task's
   caller list, because the laptop `lx2` lacks `m4`, `bison`, and `flex`. The
   makefiles set `TMPDIR` to `build/mvp/tmp`, so no build writes to the
   host's `/tmp`; the Make controls treat `TMPDIR` as reset, like `PATH`.
7. **The evaluator's image did not build (stop condition 11; resolved by
   Plan revision M0-B).** M0-4's
   `./mvp/mvp evaluate` found the host side in order, then could not
   build the image from the pinned base and the recorded closure. The
   closure's `ca-certificates-2026.2.92_v9.0.319-1.fc44.noarch` (the
   host's) is no longer in Fedora 44's `fedora` or `updates` repository,
   which hold the other 256 NEVRAs and now `-2.fc44`; and the closure's
   `systemd-sysusers-259.10-1.fc44.x86_64` (the host's) conflicts with the
   base image's installed `systemd-standalone-sysusers-259.7-1.fc44.x86_64`,
   which `dnf install` does not erase. The second holds even with every
   NEVRA available: it is a property of this base and this host's
   closure. Nothing was loosened (no `--allowerasing`,
   `--skip-unavailable`, closure edit, or lock refresh), so the lock was
   not checked inside the evaluator, no gate ran there, and M0-4's exit
   criteria "`evaluate` passes" and "images identical across host and
   evaluator" are not met. Remedies for direction include a package source
   that keeps the exact NEVRAs (a local repository of the host's RPMs, or
   Fedora's updates archive); a lock and closure refresh after a host
   update; a base whose packages do not conflict with the closure; or a
   Containerfile that swaps `systemd-standalone-sysusers` for
   `systemd-sysusers` explicitly. Each changes the lock, the closure, or
   the Containerfile. Inside the image, `mvp check` would also rebuild
   B2's port and the guest kernel from the read-only mirror. The
   responsible human chose remedy A on 2026-10-24, and Plan revision M0-B
   implements it: a SHA-256 for each RPM of the unchanged closure, the
   exact RPMs fetched once into a verified cache (`ca-certificates`'
   signed `-1.fc44` from koji), and the image built from that cache with
   every repository disabled, the standalone sysusers swapped by name, and
   four more base packages removed by name (item 27). At `67731e4c`
   `./mvp/mvp evaluate` passes: the lock inside, every gate, B2's port
   and the guest kernel rebuilt there, and all 146 images byte-identical
   with the host's (see [Results](#plan-revision-m0-b-at-67731e4c-2026-10-24)).
8. **Stop condition 3: Clang's scenario monitor was over its text budget
   (resolved by M0-A.1 at `65454598`).** At M0-3, Clang's monitor text
   ended `0x7e0` bytes above the accepted `0x1_0200_8000` (GCC's `0x20`
   below), so no Clang scenario image existed, the plan's GCC-and-Clang
   scenario rows ran for GCC only, and `make -C mvp check` ended in
   `BE_MVP_BUDGETS: FAIL`. Plan revision M0-A.1 moved the MVP layer's C
   into the MVP region; both toolchains' text now ends at or below
   `0x1_0200_4780`, every budget holds, and both toolchains' images,
   variants, and probe images ran in QEMU (see
   [Budgets (measured)](#budgets-measured) and
   [Results](#plan-revision-m0-a-at-ebae089d)).
9. **A boot hart other than 0 left itself HSM STARTED (resolved by M0-A.2
   at `106062f6`).** QEMU's boot hart is a lottery. A boot hart other than
   0 runs the start rule (Q2): its line, `hart_start(0)`, and a park in
   `wfi`, which leaves it HSM STARTED, and M0-3's `BE_MVP:02` refused
   every STARTED hart, so such a run ended `BE_MVP:FAIL firmware` and the
   provisional QEMU driver repeated it, up to 16 attempts. Plan revision
   M0-A.2 admits at most one STARTED hart that is not a domain's, reported
   as `started=<h>`; the board shim gains no firmware call, and the driver
   now makes each run once. A boot hart that is a domain's hart is still
   refused, as M0-A.2 declares (item 13).
10. **The `ring-full` variant did not fill its ring in QEMU (resolved by
    M0-A.3 at `ebae089d`).** With 1 KiB rings alone, hart 0 drained each
    LINE record as soon as its IPI arrived, so the rings' high-water marks
    stayed between `0xd8` and `0x2d8` bytes and the variant passed like the
    scenario. Plan revision M0-A.3 adds hart 0's `0x2000000`-tick wait
    after both domains' ENTERED; in QEMU, for both toolchains, the domain
    harts' rings filled and each took its fallback path, as declared
    (item 14).
11. **The probe profile's install sites.** `probe-platform` has three
    install call sites (R3's, the domain hart's, and the probe module's
    `be_mvp_probe_hgatp`); the two VMID images have the usual two and the
    raw `hgatp` write instead, since the plan puts the `hgatp`-mode probe
    in `probe-platform` only. The image checker's probe profile holds each
    image to its own set.
12. **The image checker's departures from B7's.** Clang keeps a symbol's
    address in a callee-saved register across a loop (`wait_phase`,
    `emit_record`), which B7's straight-line `references()` rejected; the
    copy follows the control flow to a fixed point and still rejects an
    `auipc` whose result is never used. Clang also inlined
    `be_mvp_fw_call` into its callers, so it is now `noinline` (the GCC
    image is byte-identical) and the `ecall`'s callers stay the accepted
    platform helpers and `be_mvp_fw_call`. Two of the plan's mutations, a
    ring size that is not a power of two and a block offset moved, have no
    linked word in the image to change (the offsets and sizes are
    immediates); they are applied to the layout the image is built from,
    as well as, for the block offset, to the hart entry's and the vector's
    stack-top immediate. Since M0-A.1 the checker also reads each image's
    link map, in GNU ld's and lld's formats, to place every MVP C object's
    input sections, and either toolchain's image can be the reference.
13. **A QEMU run whose boot hart is a domain's hart is refused (resolved
    by M0-4 as implemented).** M0-A.2 keeps "a domain hart not STOPPED" as
    `FAIL firmware`, and the start rule leaves a boot hart other than 0
    STARTED, so a run that QEMU boots
    on hart 1, or on hart 2 in a two-domain image, ends
    `BE_MVP:FAIL firmware` straight after `:02` (10 of the 44 runs at
    `ebae089d`). The provisional driver judges such a run REFUSED: a
    declared outcome, counted apart, that does not exercise the run's own
    expectation. The task's "a non-zero boot hart is now a normal run"
    therefore holds for harts 3 to 7 (and hart 2 where it is not a
    domain's), not for every hart. How M0-4's harness counts a REFUSED run
    (for example, repeating only REFUSED runs until each run has run as
    declared, as was done by hand here, or pinning QEMU's boot hart, which
    would change the QEMU platform inputs) is the responsible human's to
    decide. The board is unaffected: every recorded COM260 run entered on
    hart 0. M0-4 follows Plan revision M0-A's note: `tests/run-qemu.sh`
    and the kexec rehearsal make a REFUSED attempt again, up to eight
    attempts per run, and count every attempt and refusal per run (the
    summary, `attempts.tsv`, and the bundle's `refusals.tsv`); on the
    board a REFUSED run is stop 6 and ends the campaign (item 21).
14. **The `ring-full` fallback starts at once (resolved by M0-4 as
    implemented).** M0-A.3 says the writing hart "posts `FAIL ring`,
    receives no acknowledgement while hart 0
    waits, and takes the fallback path". A full ring fails the domain
    hart's ring view (a writer that finds no room fails and never
    overwrites, and a failed view stays failed), so the FAIL record cannot
    be posted, and the hart takes the fallback at once, as the accepted
    plan's failure paths already say of a ring that cannot carry the FAIL,
    rather than after the `2^24`-tick wait. Both domain harts fill their
    rings, and both print their lines; the first SRST may cut the second
    hart's DETAIL short (the Clang run). The design has no `BE_MVP:ACK`
    console line (ACK is an inbound ring record), so the driver reads
    "no `BE_MVP:ACK` from hart 0 before it" as no domain line and no
    `BE_MVP:11` to `:14` before the first FAIL, every FAIL `ring`, and
    every DETAIL naming a domain hart. M0-4's capture checker holds the
    variant to this reading (Plan revision M0-A's note records it), and
    both toolchains' `ring-full` runs pass it.
15. **The capture checker's `started` rule and the `shim-rule` variant
    (resolved by M0-4 as implemented).**
    M0-A.2 has the capture checker require `started=<h>` to equal the
    shim's `boot_hart=0x<h>` when that line is present and `started=none`
    when it is absent. In the `shim-rule` variant the line is always
    present (`boot_hart=0x1`) while `:02` prints `started=none`, because
    the variant's rule hart stops itself; M0-4's checker must take
    `started=none` for that variant, as the provisional driver does. In
    every other run the driver also requires the shim's line to name the
    OpenSBI banner's boot hart, and to be absent when that hart is 0.
    M0-4's checker takes the rule line and `started=none` for `shim-rule`
    alone, and elsewhere requires `started=<h>` to equal the shim's
    `boot_hart=0x<h>`, which must be the banner's or the kexec handoff's
    hart, and `started=none` without the line; a `started=` that differs
    is one of its mutations.
16. **How `started` prints (resolved by M0-4 as implemented).**
    `started=<h>` prints the hart in decimal,
    as `:02`'s status list and every other `hart=` field print theirs
    (`%d`, no `0x`), while the shim prints `boot_hart=0x<h>` in hex; the
    digits agree for harts 0 to 9. The task asked for hex "like other hart
    fields"; the other hart fields are decimal, so `started` follows them.
    The capture checker converts between the two.
17. **The accepted data section is empty.** With every MVP static in the
    MVP region, `.monitor.data` holds nothing: GNU ld emits the empty
    section without its ALLOC flag (PROGBITS, `W`), lld as NOBITS `WA`, and
    `__be_bss_start` equals `__be_bss_end`, so the accepted entry's BSS
    clear runs no iteration. The image checker requires the section empty
    and does not require its flags. The MVP region's BSS sits inside
    `.mvp.data` (PROGBITS), as the task directs, so the flat image carries
    its zeros; hart 0 still checks and zeroes it.
18. **Beyond the plan's rows.** The negative variants are built, checked,
    and run for Clang as well as GCC (the scenario file still lists GCC
    for them); the MVP region has three PT_LOAD segments (R-X text, R
    rodata, RW data and BSS) where two were suggested, so its constants
    are not executable; and in the probe images, which run domain 0 alone,
    `:02` counts only domain 0's hart as a domain hart, so a probe run may
    boot on hart 2 (one did, `started=2`; at M0-4 two more did). M0-4's
    QEMU suite runs every variant for both toolchains.
19. **No deterministic QEMU run shows two STARTED harts.** The census's
    refusals (a second STARTED hart, a STARTED domain hart) are covered by
    the host test; in QEMU only the boot-hart lottery shows the second,
    as the REFUSED runs of item 13. Adding a variant that starts a second
    hart would widen the plan, so none was added.
20. **The mutation stage's file names.** The plan's harness table names
    `tests/mutate-*.py` for the seeded mutations of the image and capture
    checkers. M0 keeps each checker's mutations inside it
    (`tests/check-image.py --mutation-test` since M0-3,
    `tests/check-capture.py --mutation-test` at M0-4), each mutation named
    with the claim it must fail, so no `mutate-*.py` file exists.
21. **A board campaign ends at the first run that does not pass.** B7's
    `k3-campaign.sh` counted failures and went on. Every board run that
    does not pass is a stop condition (a REFUSED run is stop 6, "not a
    repeat"; another failure is a board outcome QEMU did not show, or stop
    3 or 8), so M0's campaign makes no further run after one, writes its
    summary, and prints `BE_MVP_K3_CAMPAIGN: STOP`; the dry run's
    `campaign-stop` case shows it.
22. **Ring post-to-drain latency is not measured.** The plan's Costs row
    lists it; M0's markers carry no record's post time, so the capture
    checker records per-exit ticks, the PING-to-receipt and
    receipt-to-PONG times, and hart 0's idle ticks and wakes (`costs.tsv`),
    but not this latency. Adding it needs a marker field, a monitor
    change, so none was made.
23. **Tools outside the lock (resolved by Plan revision M0-B.4).**
    `./mvp/mvp evaluate` runs the host's `/usr/bin/podman` (5.8.9), and
    the board tools the host's `ssh` and `scp` (and coreutils' `stty` and
    `timeout`, from a locked role's package). Neither podman nor OpenSSH
    was a lock role or in the closure: both run on the host only, and a
    role the evaluator cannot satisfy would fail `tool-lock check` inside
    it. M0-B.4 makes podman, ssh, and scp host-only roles, checked on the
    host and skipped inside the evaluator (29 roles), and `evaluate.sh`
    runs podman by the lock's command after checking the lock; `stty` and
    `timeout` remain covered only through their package, the `sha256sum`
    role's coreutils. The rehearsal needs no new role: its init makes the
    `kexec_load` call itself (no kexec-tools), built with the locked cross
    compiler and packed by B0's `mkcpio.py`, and its kernel, B0's, is an
    external input recorded by SHA-256.
24. **The fake board's topology is synthetic (resolved by M0-5).** B7 recorded no
    `/cpus/cpu-map`, cache node, or sysfs topology, so `tests/fake-board.py`
    answers the preflight with lines marked synthetic; the preflight's
    reading of them is exercised only in that form, and the platform
    record's topology waits for the real preflight (M0-5). HSM's detection,
    by contrast, is in B7's record (`SBI HSM extension detected`). The
    COM260 preflight of 2026-10-24 recorded the real topology, which the
    platform record tabulates: `/cpus/cpu-map` with two clusters of four
    harts, each cpu node's `next-level-cache` phandle, no device-tree node
    named `cache`, and the sysfs topology. The fake board's lines stay
    synthetic, and the dry run still reads only them.
25. **The board run's SSH control socket.** B7's `k3-run.sh` put its SSH
    control directory under `${TMPDIR:-/tmp}`, which B7's makefiles leave
    as `/tmp`. Through the MVP makefiles `TMPDIR` is `build/mvp/tmp`, so
    M0-4's copy uses a short name there and stops before any ssh if the
    socket path, with the 17 bytes ssh adds while binding, would exceed
    107 bytes (this checkout's is 82); `K3_SSH_CONTROL_DIR` sets another
    directory. The wrapper passes the board settings and `SSH_AUTH_SOCK`
    to the `k3-*` commands only.
26. **The QEMU lottery's refusals vary.** Three full checks at M0-4
    refused 5, 6, and 14 attempts of 39, 40, and 48; no run needed more
    than four of its eight. A suite fails only if some run's eight attempts
    are all refused, about 1.5e-5 per two-domain run if QEMU's boot hart is
    uniform; pinning the boot hart would change the QEMU platform inputs
    (item 13), so it was not done.
27. **Four base packages removed by name beyond the plan's swap.**
    M0-B.3 names one base package to swap, `systemd-standalone-sysusers`,
    and makes "explicit, named, local operations" the boundary, with stop
    condition 11 beyond it. With every repository disabled, the
    transaction also refused four base packages that the closure does not
    name and that require exact versions the closure replaces; M0-4's
    build, with the repositories enabled, would have upgraded them from
    the repositories unannounced. The dnf output with the swap alone
    (every NEVRA otherwise installable):

    ```text
    Problem 1: cannot install both glibc-2.43-9.fc44.x86_64 from @commandline and glibc-2.43-7.fc44.x86_64 from @System
      - installed package glibc-minimal-langpack-2.43-7.fc44.x86_64 requires glibc = 2.43-7.fc44, but none of the providers can be installed
      - conflicting requests
      - problem with installed package
     Problem 2: cannot install both rpm-libs-6.0.2-1.fc44.x86_64 from @commandline and rpm-libs-6.0.1-2.fc44.x86_64 from @System
      - installed package rpm-build-libs-6.0.1-2.fc44.x86_64 requires rpm-libs(x86-64) = 6.0.1-2.fc44, but none of the providers can be installed
      - conflicting requests
      - problem with installed package
     Problem 3: cannot install both rpm-libs-6.0.2-1.fc44.x86_64 from @commandline and rpm-libs-6.0.1-2.fc44.x86_64 from @System
      - package rpm-plugin-selinux-6.0.2-1.fc44.x86_64 from @commandline requires rpm-libs(x86-64) = 6.0.2-1.fc44, but none of the providers can be installed
      - installed package rpm-sign-libs-6.0.1-2.fc44.x86_64 requires rpm-libs(x86-64) = 6.0.1-2.fc44, but none of the providers can be installed
      - conflicting requests
      - problem with installed package
     Problem 4: installed package rpm-libs-6.0.1-2.fc44.x86_64 requires rpm = 6.0.1-2.fc44, but none of the providers can be installed
      - installed package rpm-build-libs-6.0.1-2.fc44.x86_64 requires rpm-libs(x86-64) = 6.0.1-2.fc44, but none of the providers can be installed
      - cannot install both rpm-6.0.2-1.fc44.x86_64 from @commandline and rpm-6.0.1-2.fc44.x86_64 from @System
      - installed package dnf5-plugins-5.4.2.1-1.fc44.x86_64 requires librpmbuild.so.10()(64bit), but none of the providers can be installed
      - conflicting requests
      - problem with installed package
    ```

    Read as explicit, named, local operations, the Containerfile removes
    the four by name in the same transaction: `glibc-minimal-langpack`,
    whose `glibc-langpack` the closure's `glibc-all-langpacks` provides,
    and `rpm-build-libs`, `rpm-sign-libs`, and `dnf5-plugins`, which no
    gate uses; `clean_requirements_on_remove` is off, so nothing else
    goes, and `/etc/mvp-evaluator-swap.txt` records them. The narrower
    reading, the named swap alone, makes this stop condition 11 again, and
    putting their updated versions in the cache would edit the closure.
    For the responsible human to confirm with the result packet.
28. **Koji's signed copy, not its top-level file.** M0-B.2 names koji's
    `packages/<name>/<version>/<release>/<arch>/` directory; the file
    there is koji's unsigned build output (rpmkeys: `digests OK`), which
    M0-B.1's signature check must refuse. Koji keeps the copy signed with
    the Fedora 44 key under the same build's `data/signed/6d9f90a6/<arch>/`,
    and the fetch takes that. Only
    `ca-certificates-2026.2.92_v9.0.319-1.fc44.noarch` came from koji.
29. **The image has ssh and scp.** `openssh-clients` was already in
    M0-1's closure, as `git-core`'s hard requirement. M0-B adds no package
    to the closure and keeps podman's out, so the plan's "the image gains
    no container, SSH, or network tooling" holds for what M0-B adds; the
    image's ssh and scp were there before, no gate runs them, and the
    evaluation has no network. The lock skips the ssh and scp roles
    inside, as M0-B.4 directs.
30. **The board commands do not check the lock themselves.**
    `k3-preflight`, `k3-load-check`, `k3-probe`, and `k3-campaign` run ssh
    and scp without `tool-lock check`; the plan's procedure runs
    `mvp check`, whose first step checks all 29 roles, and `mvp evaluate`,
    which checks them again, before the board. Making the board targets
    check the lock would change the board tools beyond M0-B, so it was not
    done. In M0-5's second campaign runs 5 to 8 ran `l1`'s `ssh` and `scp`
    from `openssh-clients-10.2p1-16.fc44` (installed there on 2026-10-25
    at 21:55 UTC) while the lock named `-14`, and the board record's tool
    record shows the lock failing on `l1` before its refresh (item 41);
    the refresh then recorded `-16` (see
    [Results](#the-host-move-and-the-lock-refresh-on-l1-2026-10-26)). The
    staged image is hash-checked on the board whatever copies it.
31. **Beyond the plan's text.** `evaluate.sh` checks the host's lock
    first and runs podman by the lock's command; the image's tag and
    labels carry the Containerfile's SHA-256 as well as the closure's, so
    a changed recipe never reuses an older image; the fetch tries
    `MVP_RPM_CACHE` first, as `tools/build-guest.sh` does; the header
    digest is also computed from the file's bytes, not only read by rpm,
    and m4, bison, and flex, which the laptop `lx2` lacks, are checked against
    B3's pins; the fetcher's offline self-test runs in `tool-lock-check`;
    the evaluator's marker must match `rpm -qa`; and scp's version line is
    its usage line, printed with exit status 1.
32. **The first board scenario run failed the alternation floor (stop
    condition 6; Plan revision M0-C; resolved by M0-5's second board
    campaign).** On
    2026-10-25 the first GCC scenario run on the COM260
    (`20261025T022152Z`) ran both domains to `BE_MVP:14` with every rule
    holding but one: 5 alternations, below K = 8. Hart 0 drained each
    ring to empty in turn, printing behind the 115200-baud console, and
    woke 3 times for 138 records. M0-4 had relied on the plan's inference
    that both floors sit well below the expected values, which held in
    QEMU, where hart 0 wakes about once per record, and not on the board.
    Plan revision M0-C makes the drain round-robin (`129626e0`) and keeps
    the run's capture as a negative fixture (`c5ecedee`). QEMU cannot
    show the difference (the counts under
    [Plan revision M0-C](#plan-revision-m0-c)), so the item stays open
    until the board's re-run with the M0-C images: the two load checks,
    the three probe runs, three GCC and one Clang scenario runs, and the
    `payload` run, with a human reset after each. The stopped run's record
    (`build/mvp/k3-campaigns/20261024-com260/`, with the preflight and
    load checks beside it under `build/mvp/`) is stop-6 evidence for the
    result packet, not a scenario result, and is not yet a retained board
    record. **Resolved** by M0-5's second board campaign (2026-10-25 and
    26): with the M0-C images all eight runs passed, and each of the four
    scenario runs (three GCC, one Clang) printed 125 alternations in 2
    wakes for 138 records, against K = 8 (see
    [Results](#m0-5s-second-board-campaign-2026-10-25-and-26)). The
    stopped run's capture stays the checker's negative fixture
    `k3-two-guests-gcc-stop6-alternations.log`; its record is not a
    retained board record.
33. **The tool lock fails on host drift (since 2026-10-24).** A host
    update on 2026-10-24 at 17:02 EDT replaced the closure's
    `ca-certificates-2026.2.92_v9.0.319-1.fc44.noarch` with `-2.fc44`
    (its changelog: `emSign Root CS CA - G3` removed from the Microsoft
    code-signing set), so `tool-lock check` fails (`1 closure packages are
    not installed at their NEVRA`), `./mvp/mvp check` stops at its first
    step, and `./mvp/mvp evaluate` stops before its build. The 29 roles
    pass, M0-C changes no lock input, and the board tools do not check
    the lock (item 30). It is stop condition 11 if a closure package
    counts as a role the host cannot satisfy; either way the plan
    reserves `tool-lock refresh` and `fetch-closure.py --record` to the
    responsible human's direction, so neither was run, and the host was
    not changed. Remedies for direction: install the recorded `-1.fc44`
    RPM on the host again from its verified copy in the closure cache
    (`build/mvp-evaluator/rpms`); or refresh the lock and the closure from
    the host, the closure gaining `-2.fc44` and its digest by `--record`,
    which re-binds `MVP_CLOSURE_SHA256` and so retags the evaluator's
    image, to be built again. Either way `./mvp/mvp check` and
    `./mvp/mvp evaluate` must then pass on the M0-C commits before the
    result packet; every stage of `check` after the lock, and the kexec
    rehearsal, pass at `c5ecedee`. **Resolved** on the direction
    `refresh the lock` (2026-10-25), the downgrade having been declined as
    a security issue: the refresh changed the one closure line and its
    digest, the evaluator was rebuilt from the cache, and `check`,
    `evaluate` (146 of 146 images identical), and the kexec rehearsal
    pass at `804fa95f`. That the closure pins the host's security
    packages, so that such host updates drift the lock, is an open
    design question for the result packet and M1 (item 37).
37. **Host security updates drift the evaluator's closure.** The closure
    is derived from the host's installed packages, so a host update to
    any of its NEVRAs (257 then; as `ca-certificates` on 2026-10-24) fails the
    lock until a refresh under direction, and refreshing re-pins the new
    version into an image that then diverges from a host updated again.
    Deciding what the closure should pin (the roles' packages only, with
    the base image's security packages left to the base) is for the
    result packet's open questions and M1's plan, not M0. The refresh on
    `l1` (item 39) is a second instance: `openssh-clients-10.2p1-14.fc44`,
    which the lock named, is no longer in Fedora's repositories.
34. **A visit releases the tail before it prints (a reading of M0-C.1).**
    M0-C.1 has each ring's head "acquired and its tail released around
    each take as before". The implementation reads the take as the ring's
    take, the copy of one record into hart 0's own buffer: `visit()`
    executes `fence r, w` and releases the tail, then `step()` prints the
    line, so a slow console holds no ring bytes. Before M0-C the tail was
    released once per pass, after every take and print. Nothing reads the
    ring's bytes after the take, and a run that fails in `step()` ends as
    before. Releasing after the print instead would change no marker or
    counter but the rings' high-water marks. For the responsible human to
    confirm.
35. **The board-tool dry run's two load checks can share a second.** The
    dry run's `campaign` case requires its board record to hold two load
    checks, and B0's `retain-results.py` (unchanged) files each under its
    run directory's name, a UTC second. Against the fake board both load
    checks can start in the same second; the record then holds one, and
    the case fails (`campaign: the record lacks a load check`). It
    happened once while M0-C was checked, and `tools-check` passed when
    made again. On the board the two load checks of 2026-10-24 started 18 s
    apart. **Resolved** (harness only, after M0-C's review): `evidence.py
    --board` stages copies of the two load checks named
    `<toolchain>-<run>` beside the record and hands those to B0's
    retention, which is unchanged, so the record's `load-check/` holds
    `gcc-<run>` and `clang-<run>` and its `load_checks=` line names both;
    the staging directory is removed whatever happens. The dry run's
    `campaign` case checks the two names, and its new `same-second` case
    retains two load checks whose run directories share one name
    (`20000101T000000Z`) and requires both in the record. The board
    tools' run directories keep their names.
36. **Evaluator records were overwritten.** `evaluate.sh` wrote every run
    into `build/mvp-evaluator/record/`, truncating `evaluate.txt` and
    replacing `check.log`, so an `evaluate` run at 11:49 on 2026-10-24
    (which failed inside the evaluator on item 35's flake) replaced M0-B's
    passing `check.log`; M0-B's `image-identity.txt` (146 of 146
    identical), `build.log`, fetch records, and the README's record of the
    pass survive, and the earlier files are kept under
    `build/mvp-evaluator/record/m0b-flat-20261024/`. **Resolved**: each run
    now records into `build/mvp-evaluator/record/<UTC stamp>/`, never
    reusing a directory (a second run in the same second waits for the
    next), prints `record=<path>` first, and leaves
    `build/mvp-evaluator/record/latest` pointing at the newest.
38. **The campaign tool exits while it waits for a reset.**
    `k3-campaign.sh` waits `K3_RETURN_SECONDS` (default 1,800 s) for
    Fedora to answer with a new boot ID before each run after its first;
    if the human's reset comes later, it prints
    `BE_MVP_K3_CAMPAIGN: STOP board did not return in <n>s` and exits 1
    without writing `summary.md`, in the words of a stop although no run
    failed and no stop condition applies. It happened twice in M0-5's
    second campaign (after 36,000 s and after 1,800 s); each time the
    campaign was resumed into the same `K3_RUN_ROOT` with only the runs
    not yet made, and each run was made once (see
    [Results](#m0-5s-second-board-campaign-2026-10-25-and-26)). A resumed
    invocation takes the first boot ID it finds, since the tool remembers
    only its own runs' boot IDs; the board stays halted after each run
    until the human resets it, and the summary counts 8 distinct boots for
    8 runs. Telling a timeout from a stop, or waiting without a bound,
    would change the board tools, so neither was done. For the responsible
    human. **Resolved as implemented** by M1-5 under the M1 plan's Q18
    (`9020c4f8`): on the human path a wait that times out prints
    `BE_MVP_K3_CAMPAIGN: PAUSED` instead of `STOP`, writes the summary of
    the runs made, names the runs left, and exits 75 (the dry run's
    `campaign-paused` case); with `K3_RESET=k3ctl` the wait after the
    tool's own reset is bounded by `K3_RESET_RETURN_SECONDS` and a timeout
    is stop 10. M1's board campaigns ran with `k3ctl` resets only, so the
    `PAUSED` path has run in the dry run alone.
39. **The closure depends on the host's installed set.** The closure is
    resolved against the installed packages (see [Tool lock](#tool-lock)),
    so it follows the host as well as the roles. The refresh on `l1` added
    `glibc-langpack-en-2.43-9.fc44`, a second installed provider of
    `glibc-langpack` beside the closure's `glibc-all-langpacks`, and
    `systemd-rpm-macros-259.10-1.fc44`, which `systemd` requires where
    `rpm-build` is installed (`(systemd-rpm-macros = 259.10-1.fc44 if
    rpm-build)`; `l1` has `rpm-build-6.0.2-1.fc44`); no locked tool
    changed for either, and neither was in the closure refreshed on
    `lx2`. A closure derived so names what the refreshing host has
    installed, not only what the gates need, and the evaluator's image
    follows it: built from the 259-package closure on `l1`, it holds 293
    packages, two more than at M0-B, with the same five named base
    removals. Whether to derive the closure from its roots on a reference
    package set instead is for the result packet's open questions and
    M1's plan, with item 37.
40. **OpenSBI prints nothing on the console, and the platform record says
    so in fixed text.** The plan's platform record expected "the PMP and
    domain regions OpenSBI prints at power-on, which the output-only
    capture includes before Fedora boots". None reached the console on
    this COM260: the operator's picocom log of the second campaign on
    `l1` holds, after each reset it holds legibly, the boot ROM's, U-Boot
    SPL's, U-Boot's, and Fedora's lines
    and no line with `OpenSBI`, `Platform Name`, `Domain0`, `PMP`,
    `Firmware Base`, or `Runtime SBI`, and the retained excerpts start at
    the kexec handoff. The firmware is identified only by Fedora's log
    (`SBI implementation ID=0x1 Version=0x10006`), and its reserved memory
    shown only by the FDT reservations and `/proc/iomem`. The log is
    outside the repository and is not parsed: `tools/platform-record.py`
    carries the reading as a fixed paragraph (`SERIAL`), written by hand
    on 2026-10-26 for campaign `20261025-com260`, and puts it in every
    platform record it writes, the dry run's included, so a later
    campaign's record would carry it until the generator takes the reading
    as an input. Whether M1 needs the firmware's PMP layout, and from
    where, is for the responsible human. **The fixed text resolved** by
    M1-5 (`9020c4f8`; M1 plan, "Platform record"): the generator reads the
    paragraph from the campaign's `serial-log-note.txt`, written by hand
    for each campaign and kept in its board record, and refuses an empty
    one. The second M1 campaign's note
    (`build/mvp/k3-campaigns/20261027-com260-m1b/serial-log-note.txt`)
    finds, as M0's did, no line with `OpenSBI`, `Platform Name`,
    `Domain0`, `PMP`, `Firmware Base`, or `Runtime SBI` in the operator's
    log; M1 did not need the firmware's PMP layout.
41. **The board record predated the lock refresh on `l1`, and the board
    record's tree state could count its own staging directory (both
    resolved by M0-6).** The campaign's first record,
    `results/20261025-com260/`,
    was written on `l1` at 06:53 UTC, before QEMU was installed there
    (06:56) and the lock refreshed (07:02): its `mvp/bundle.txt` has
    `lock_check_status=1` and `804fa95f`'s lock and closure SHA-256
    (`8df124b9b362...`, `56d91c92...`), and its `mvp/tool-record.txt` the
    check's first failure, `qemu: /usr/bin/qemu-system-riscv64 is not
    executable`. Its runs, excerpts, and platform record do not depend on
    the lock, and the images it binds by SHA-256 are the build's now. It
    is superseded and never committed. **Resolved**, the lock half: after
    the gates passed at the exact commit `13992d6d` from a clean tree, the
    record was made again against it and is the one committed
    (`source_commit=13992d6d...`, `source_tree=clean`,
    `lock_check_status=0`, lock `6e99262f04a1`, closure `2875ddd675b4`;
    see [The board record](#the-board-record-and-the-platform-record-m0-6-2026-10-26)). **Resolved** (M0-6), the staging half:
    `evidence.py --board` read the tree's state, `git status
    --porcelain=v1`, after `staging()` had made the load checks' staging
    directory beside the record. While `mvp/results/` is wholly
    untracked, git prints it as one `?? mvp/results/` line whatever lies
    beneath it: in the record of 06:53 UTC, `changed=4` is
    `tools/evidence.py`, `tests/run-tool-dry-run.sh`,
    `tools/platform-record.py`, and that one line, with the staging
    directory beneath it; in the attempt at 06:15 UTC, whose run created
    `mvp/results/` (born at 06:15:00 UTC, before that attempt's record
    directory), the line stood for the staging directory alone and was
    the whole `changed=1`. Once a record is committed under
    `mvp/results/`, from the commit that adds this campaign's record on,
    the directory is
    tracked and each new staging directory is one more `??` line, so every
    later record would have counted its own staging directory. `board()`
    now reads the state with `source_state()` before `staging()` and
    passes it to `board_record()` as its last parameter. The dry run's
    `tree-state` case makes a record under the tracked `mvp/tests/` and
    requires its count to equal git's: it fails on the earlier code
    (`changed=8` recorded, git 7) and passes with the fix, and it is
    skipped where `mvp/tests/` is read-only, as inside the evaluator (see
    [M0-6's checks](#m0-6s-checks-on-l1-2026-10-26)).
42. **The guest kernel's `.config` depends on tools outside the lock.**
    Kconfig probes the host's Rust and pahole when it configures the
    kernel: on `l1`, which has `rust-1.99.0-1.fc44` and
    `dwarves-1.32-1.fc44`, the guest's `.config` records
    `CONFIG_RUSTC_VERSION=109900`, `CONFIG_RUST_IS_AVAILABLE=y`,
    `CONFIG_PAHOLE_VERSION=132`, and seven more probe lines, where
    `lx2`'s records four of them as `0`. Neither package is a lock role
    or in the closure, and the ten pinned outputs are byte-identical
    either way, but `kernel-repro` compares the two builds' normalized
    `.config` files too, so a first build from one host and a second from
    the other fail it (`differ: char 381, line 14`), while it passes on
    each host alone (see
    [`kernel-repro` again](#kernel-repro-again-on-l1-2026-10-26)). Locking
    the two tools, or normalizing those lines as `CONFIG_INITRAMFS_SOURCE`
    is, would change the lock or `guest.mk`, so neither was done. For the
    responsible human. **Resolved** by the M1 plan's Q16, as implemented at
    `8c2cbbfd`: `tools/build-guest.sh` passes Kbuild's `RUSTC`, `BINDGEN`,
    and `PAHOLE` as paths under `/dev/null/` that name no executable, so
    Kconfig's probes find neither tool, and the `.config` built on `l1`,
    which still has both packages, records `CONFIG_RUSTC_VERSION=0`,
    `CONFIG_RUSTC_LLVM_VERSION=0`, and `CONFIG_PAHOLE_VERSION=0`
    (`build/mvp/guest/kbuild/.config`; the build record
    `MVP-GUEST-BUILD.txt` repeats them), and the build stops unless the
    first and the last are there.
    `kernel-repro` passed on `l1` at M1-4 with twelve outputs identical; no
    build was made on `lx2`, a noncanonical workspace since 2026-10-25, so
    the cross-host comparison was not repeated.
43. **A stale rootless podman store, moved aside on `l1`, awaits the
    responsible human.** The account's rootless podman state
    (`~/.local/share/containers`, its database's `DBConfig` from
    2025-12-04, when the account had uid 1000) pinned its run and
    temporary directories under `/run/user/1000`, while the account is
    now uid 501, so podman could initialize no OCI runtime and the first
    `./mvp/mvp evaluate` on `l1` stopped before its build (see
    [Results](#the-host-move-and-the-lock-refresh-on-l1-2026-10-26)). With
    the responsible human asleep, the orchestrating session moved it aside
    on 2026-10-26, reversibly, as
    `~/.local/share/containers.uid1000-stale-20261026`; it held no named
    image. `podman system reset` was deliberately not run. Deleting the
    stale directory, or restoring it, is the responsible human's. It is
    host state outside the lock: no package, lock role, or repository file
    changed, and the evaluator's image was then built under the account's
    new store. Unchanged through M1: the stale directory is still where it
    was moved, and M1-4's `./mvp/mvp evaluate`
    (`build/mvp-evaluator/record/20261027T080219Z`) reused the image built
    under the new store. **Resolved 2026-10-27:** on the responsible
    human's acceptance of the recommendation to delete it (`approve
    ff84533c and revisions, accept your recommendations, authorize
    proceeding per those`), the orchestrating session deleted
    `~/.local/share/containers.uid1000-stale-20261026` (172 KB, 10 files:
    an empty storage database, lock files, and a blob-info cache; no
    image or container) after M1's three clean `evaluate` runs under the
    new store. Nothing in the repository or the lock changed.
44. **The M1 plan's board commands name no scenario.** The plan's "Board
    safety and procedure" lists `./mvp k3-load-check TOOLCHAIN=gcc` and
    `./mvp k3-campaign TOOLCHAIN=gcc RUNS=3` (and the Clang pair) for the
    `te-poc` load checks and runs. The plan predates the board selector
    that M1-5 added (`SCENARIO=two-guests|te-poc`, `two-guests` by
    default), so those commands load and run M0's `two-guests` images; the
    variant runs are right as listed, since `VARIANT=reader-write` and
    `no-inject` imply `te-poc`. The `te-poc` commands need
    `SCENARIO=te-poc`, as [Commands](#commands) shows and the second
    campaign ran them. An invocation that followed the plan's list made the
    three unplanned runs of item 45. The accepted plan's text is not
    edited; for the responsible human, with the result packet.
45. **Three unplanned `two-guests` runs on the board.** Between the second
    campaign's preflight and its `te-poc` load checks, on 2026-10-27, an
    invocation without `SCENARIO=te-poc` made two `two-guests` load checks
    (`build/mvp/k3-load-checks/gcc/20261027T174616Z` and
    `clang/20261027T174637Z`) and three GCC `two-guests` RAM-only kexec runs
    with `804cd24c`'s images (`2d33d5887cc0`), `20261027T174716Z`,
    `174838Z`, and `175000Z`, each followed by a `k3ctl` reset (34, 33,
    and 43 s to Fedora's new boot ID). All three passed with M0's exact
    counts (`exits_g0=157 exits_g1=157 records=138 wakes=2
    alternations=125 g0=65 g1=65`). Their records are set aside in
    `build/mvp/k3-campaigns/20261027-com260-m1b-two-guests-unplanned/`,
    without a `summary.md`; the third run's `reset.txt` ends at
    `seconds_to_new_boot_id=43` and its directory has no `SHA256SUMS`, as
    the invocation ended during the settle wait. They are not in the plan's
    campaign or M1's board record, and are recorded here as an unplanned
    observation, not evidence: M1's board evidence for `two-guests` is
    M0's, and M1's QEMU suite runs `two-guests` with these images.
46. **The first M1 campaign's passing runs are not M1's board evidence.**
    `build/mvp/k3-campaigns/20261027-com260/` holds five passing runs
    (three GCC and one Clang `te-poc`, and `reader-write`) and the stopped
    `no-inject` run, made with `9020c4f8`'s images. Plan revision M1-B.3
    keeps them as the record of the stop, not as M1's evidence, because
    their images are not the revised commit's; the second campaign, with
    `804cd24c`'s images, is the record M1 presents. They agree with it in
    every count (`exits_g0=163 exits_g1=167 denials_g0=1 denials_g1=2
    records=146 wakes=2 alternations=127 g0=67 g1=68` in each `te-poc`
    run). The first campaign's preflight record is not kept: the preflight
    writes `build/mvp/k3-preflight/` in place, and the second campaign's
    preflight (17:45:56 UTC) replaced it; its passing is recorded in
    `planning/HANDOFF.md`. The stopped run's capture is kept as the
    fixture `k3-no-inject-gcc-stop6-fallback.log`; the campaign is not a
    retained board record.
47. **`secret-flow` is refused by A3 alone (an M2 plan erratum).** The
    plan's "Scenarios and the harness" table declares "A6 and A3 refuse"
    for `secret-flow`. As implemented at M2-1 (`f149eea0`) the negative
    gives `host_t` `read map` on `secret_t` in the policy, the need sets,
    and the manifest's secret leaf, and only A3 fails:
    `BE_MVP_POLICY_NEGATIVE: PASS name=secret-flow fails=A3
    source_none=0 undeclared=0`, with A3's findings that `host_t` maps
    `secret_t`, another domain's private type (I1), and that `secret_t` is
    storage two domain types hold with no channel rule
    (`build/mvp/records/policy/anchor-secret-flow.txt`). A6 passes: the
    secret page has no writer, so the rule adds no pair to F, and Instance
    3 already declares both directions between `host_t` and `prot_t`, so
    `F+ = D+` still holds. Neither analysis was changed to make A6 fire;
    the negative's `purpose` text records the reading. The accepted
    plan's text is not edited; for the responsible human, with the result
    packet.
48. **The management call's ABI is defined on both sides, and the device
    node comes from the initramfs list.** `guest/mgmt/be-mgmt.c` and
    `guest/mvp-init.c` each define `struct be_mgmt_call` (the FID, the
    target, and the result, three 64-bit fields) and `BE_MGMT_IOC_CALL`,
    and each asserts its number, `0xc0184242` (`static_assert` in the
    module, `_Static_assert` in the init), so that the one GPL-2.0-only
    file includes no other repository file and none includes it (M2-4).
    The number encodes the direction and the structure's size, 24 bytes,
    not the fields' order, so an edit that reordered the fields on one
    side alone would still build; the QEMU runs' result codes exercise the
    pair end to end. The plan does not say where the ABI is defined, so
    this is an observation, not a departure: a shared header was an
    implementation option, not plan text, and was not taken.
    The device node: Q2 says the init "creates by `mknod`" the device
    at its fixed minor, and the plan's "Guest software" that the
    initramfs list "also names [it] in a `nod` line". M2-4 follows "Guest
    software": `guest/initramfs.list.in` holds `nod /dev/be-mgmt 0600 0 0
    c 10 243`, and the init only opens the node. For the responsible
    human, with the result packet.
49. **The guest grew more than the plan inferred.** The plan's "Budgets"
    row for the boot image reads "the module loader and the module add
    tens of KiB (inference, measured at M2-4)". Measured at M2-4:
    `CONFIG_MODULES=y` with its sixteen-line `.config` delta and the
    module in the initramfs grew the Image from 1,569,716 bytes to
    1,899,716 (`image_size` `0x1b3628` to `0x203fb0`), 330,000 bytes; the
    module itself is 5,736 bytes, and the init grew from 6,832 bytes (M1)
    to 11,360 (M2-4) and 11,408 (`f687b791`). The payload's kernel bytes
    went from `0x17f3b4` to `0x1cfcc4`, and every boot image from
    `0x227000` to `0x277000` bytes, within the 4 MiB budget with
    `0x189000` bytes to spare (`build/mvp/records/budgets.txt`). The
    plan's "Guest software" put the module at "about eighty lines"; it is
    102. No budget is exceeded. For the responsible human, with the result
    packet.
50. **One probe run failed once in QEMU (`FAIL ipi delivered=0`).** The
    first full `./mvp/mvp qemu` on M2-3's tree failed one run,
    `gcc/probe-platform`, at its IPI phase with `delivered=0`; the run
    passed on six isolated reruns and in the full suite's rerun, and in
    one attempt each in M2-5's last host suite
    (`build/mvp/qemu/suite/attempts.tsv`) and in both of its evaluations
    (`build/mvp-evaluator/record/20261028T013707Z/check.log` and
    `20261028T015515Z/check.log`). The orchestrating session's reading is
    "a read-after-reset race in M0's probe handshake" (`src/mvp-probe.c`,
    `ipis()` on hart 0 and `ipi_hs()` and `receipt()` on hart 1), code
    that M2-3 changed only to discard the SSIP helper's new return value
    (`(void)be_mvp_arch_clear_ssip()`). The failing attempt's capture is
    not retained (`build/mvp/qemu/suite/` holds the last suite's), and the
    reading is not confirmed by a test. M2's board campaign (Q11) runs no
    probe image. For the responsible human.
51. **The host's poll bound is a one-second deadline, not Q8's 2,000
    polls (a reading of Q8).** Q8: "A poll bound of 2,000 polls at 1 ms
    gives 'no answer' (`timeout=1`)". Implemented literally at M2-4, the
    fifth request's 2,000 polls took 20 s in QEMU, 10 ms a poll, because
    the pinned kernel (`CONFIG_HZ=250`, no high-resolution timers) rounds
    a 1 ms sleep up to a jiffy, and the run took 233M ticks, past the
    2^27 below which the plan's "Budgets" puts the positive run so that
    `no-grant-check`'s budget separates it from a hang. The follow-up
    `f687b791` keeps the 1 ms polls and bounds them by one second of
    `CLOCK_MONOTONIC` time (`REQUEST_DEADLINE_NS`), half the two seconds
    Q8's figures imply; the four answered requests are unaffected, and the
    anchor run took `0x3e8cfb1` ticks, 65.6M
    (`build/mvp/anchor-e2e-gcc.log`). For the responsible human, with the
    result packet.
52. **The module's taint line is an expected kernel line.** Loading
    `be-mgmt.ko`, an out-of-tree module, each guest's kernel prints
    `be_mgmt: loading out-of-tree module taints kernel.` once, between
    `MVPINIT 02` and `MVPINIT 07` (`tests/fixtures/qemu-anchor-gcc.log`).
    M2-5's generator (`MODULE_LINE` in `tools/gen-scenario.py`) puts it
    in each v3 domain's expected lines; M1's rejected substrings, which
    name no taint, are unchanged. M2-1's v3 expectations, written before
    M2-3 and M2-4 existed, had two defects M2-5 fixed: they lacked this
    line, and they fixed the host's `refused=0` where its FID 7 call makes
    it 1 (`refused=1` in `DOMAIN_SHUTDOWN`).
53. **`unchanged=1` proves little at anchor's addresses.** In M2's roles a
    denied store's `unchanged=1` means that the word holds after the store
    what it held before (M1's roles compare it with the writer's pattern).
    Both of anchor's declared stores write zero, as M1's do, into a word
    that holds zero: the host's into `0x84001ff8`, the response page's
    last doubleword, and the protected domain's into `0x84000ff8`, the
    request page's; hart 0 cleared both pages (`PAGE_CLEARED`), and the
    protocol writes only offsets 0 to 7 (the sequence number) and 64 to
    127 (the message, or the digest's 32 bytes). So the field would read
    1 whether or not the store took effect. The denial itself is shown by
    the trap (`observed=1`, SIGSEGV with `SEGV_ACCERR` at the store's
    label) and by hart 0's `BE_MVP:DENY … kind=read-only` line, which the
    capture checker reconciles with the report; a nonzero word there, or
    a nonzero stored value, would make `unchanged` discriminate. Neither is
    done; for the responsible human.
54. **The plan's Markers example and Tests table against the
    implementation.** (1) The plan's example prints `PAGE_CHECKED` with no
    `level0=` and with `config=` on the secret page alone; the monitor
    prints both on all three pages (`BE_MVP:03 PAGE_CHECKED page=0
    kind=channel … level0=0x102039000,0x102041000 writer_pte=0x460000d7
    reader_pte=0x46000053 config=336bfddc…`), as M1's `CHANNEL_CHECKED`
    does, whose form Q13 gives the channel pages' lines, and the
    expectations the generator writes, which the capture checker matches,
    hold the monitor's form. (2) The example lists the
    delivered `pause`'s `BE_MVP:MGMT` line before `BE_MVP:12
    DOMAIN_PAUSED`; hart 0 logs a delivered request when its target's
    PAUSED or TERMINATED record arrives, after the transition's line (the
    plan's "The management extension"), so the `MGMT` line follows it, and
    the checker requires that order (M2-5's rule 9;
    `build/mvp/anchor-e2e-gcc.log`, lines 245 and 246). (3) The plan's
    "Tests and evidence" table has `deny-test` unchanged; M2-3 extended it
    for the page-aware decision with anchor's two roots (30 scenarios and
    2,357 assertions to 38 and 2,933), and M2-2 renamed one structure in
    it. The accepted plan's text is not edited; for the responsible human,
    with the result packet.
55. **`no-grant-check`'s required lines are checked as a set.** The plan's
    table lists, for `no-grant-check`, the protected domain's
    `BE_MVP:MGMT … fid=terminate target=0 … result=0`, then
    `DOMAIN_TERMINATED` for domain 0, then `BE_MVP:FAIL run-timeout`. The
    monitor prints the transition first, as in item 54
    (`tests/fixtures/qemu-no-grant-check-gcc.log`, lines 217 and 218).
    The generator writes the two as the outcome's `required_lines`, and
    `tests/check-capture.py` (`required_findings`) requires each exactly
    once among hart 0's lines before the first FAIL, in either order; their
    order is checked by the management log's rule instead
    (`mgmt_findings`, M2-5's rule 9), which, for this variant as for
    `anchor`, requires a delivered request's line after its target's
    transition, the reverse of the plan's table. For the responsible
    human, with the result packet.
56. **The loader test no longer searches the guest payload for a
    purgatory.** `tests/test-kexec-load.py` requires each board image to
    hold no RISC-V `ET_REL` ELF, which would be a `kexec_file`
    purgatory. Since M2-4 the guest Image's uncompressed initramfs holds
    `be-mgmt.ko`, an `ET_REL` object: its 5,736 bytes stand at the
    Image's offset `0xfe70c`, and at `0x1a370c` in every boot image, the
    probe images' included, since all carry the one Image (measured at
    the M2-5 content with the search's own pattern). M2-5 narrows the
    search to the image's own bytes, the shim page and the flat image,
    which end at `BOOT_KERNEL_OFFSET`, where the payload begins; the
    payload is pinned and compared with the guest pins by
    `tests/check-image.py`. The board loader runs no purgatory
    (`tools/kexec-load.py raw`) and analyzes only a host kernel for one
    (`analyze`, `probe`).
57. **The M2 plan's board commands omit the serial-log note.** The plan's
    "Board safety and procedure" list goes from the last
    `./mvp k3-campaign` to `./mvp board-evidence`, with no step writing
    the campaign's `serial-log-note.txt`, which `tools/evidence.py
    --board` refuses to run without since M1-5 ("write the campaign's
    Serial log paragraph there by hand"). [Commands](#commands) adds the
    step, as M1-5's procedure did. The accepted plan's text is not edited;
    for the responsible human, with the result packet.
58. **The IPI probe can be answered inside a management wait (Plan
    revision M2-A).** The plan's "Boot sequence additions" says
    "Everything from `:07` on is M0's", and M2-5 kept M0's `IPI_PROBE …
    spv=1` expectation; but Q14 has the requester's hart "serving any
    `PING` it finds meanwhile" in HS, whose PONG carries SPV 0
    (`be_mvp_wait_serve`'s contract). The board showed it on 2026-10-28
    (`20261028T023339Z`, GCC; stop 6): hart 0's PING, sent when it takes
    a domain's first console line, left at 96.5 ms after the barrier on
    the 115200-baud console, while the protected guest had made its first
    management call at 28.3 ms and waited 901 ms for hart 0's answer,
    until 929 ms after the barrier.
    QEMU's immediate console never produced the order (PING at 12.3 ms,
    first call at 198 ms). M2-A's checker accepts `spv=0` only inside a
    `BE_MVP:MGMT` line's `[ticks, ticks + service]` of the same hart, for
    images with the extension; no monitor source or image changed (see
    [M2-6's first board campaign and its stop](#m2-6s-first-board-campaign-and-its-stop-stop-condition-6-plan-revision-m2-a)).
    The second campaign's four `anchor` runs each showed it again, hart
    2's PING received 96.530 to 96.531 ms after the barrier inside its
    first wait, and so did its `no-grant-check` run (item 62). The
    accepted plan's text is not edited; the revision is appended to it,
    for the responsible human, with the result packet.
59. **The run tool cannot tell a board that did not boot from one that
    booted without network.** After the second M2 campaign's first run
    (`20261028T033233Z`) the `k3ctl` reset was acknowledged and the
    operator's log shows Fedora booting to its login prompt, but with no
    IPv4 address. `tools/k3-run.sh`, which waits for a new boot ID over
    SSH, found none within `K3_RESET_RETURN_SECONDS` (300 s) and stopped
    (`reset_outcome=reset-no-new-boot-id`, stop 10; see
    [M2-6's second board campaign](#m2-6s-second-board-campaign-2026-10-28)):
    it treats "Fedora not back over SSH" as stop 10 whether the board
    failed to boot or booted without network. A boot-ID probe over the
    serial console would distinguish the two; it would type at the
    console, which the board procedure's output-only capture excludes, so
    it needs the responsible human's direction. The tool is not changed;
    for the responsible human. Closed for M5's runs (M5-4): since M5-2 a
    run is launched by a reset and followed in the serial log, and no run
    waits for Fedora over SSH (the M5 plan, Q6); a new boot is an SPL and
    a U-Boot banner after the reset (`tools/k3-console.sh`). The ambiguity
    remains at one step: the restore's last check, that Fedora answers
    over SSH after its autoboot (`tools/k3-env.sh restore`, within
    `K3_FEDORA_SECONDS`), would stop on a Fedora that booted without
    network, which the session's serial log would then tell apart.
60. **The second M2 campaign's second reset is outside the tools'
    record.** The `k3ctl reset` made by hand at 06:05:31 UTC on the
    responsible human's direction (form answer `action=reset-resume,
    extra_reset_rule=true`), after which Fedora returned with boot ID
    `376c699c…`, is in no `reset.txt`: the first run's records end at the
    tool's stop, and the next run's `run.txt` names that boot only as its
    "before". It is evidenced by the campaign's hand-written
    `serial-log-note.txt` and the form answer alone, as is the first
    campaign's reset by hand at 02:44:32 UTC, and the board record's
    `resets=human:0,k3ctl:6` counts the tools' resets only. For the
    responsible human, with the result packet. Since M5-2 every reset of a
    board session is the console tool's, `k3ctl`'s or the human's when the
    tool asks, recorded in `resets.tsv`, and every SPL and U-Boot banner of
    the session must map to one, or the session stops (stop condition 12),
    so a reset outside the tools cannot pass unrecorded; the M2 record is
    unchanged.
61. **`<S>` has two meanings in the generator.** `tools/gen-scenario.py`
    gives `<S>` as `image_size` (lower-case hex) on the `BE_MVP:04` and
    `:06` lines; since Plan revision M2-A the `BE_MVP:11 IPI_PROBE` line
    of an image with the management extension carries `spv=<S>` under a
    placeholder map of its own, in which `<S>` is `[01]`, and the capture
    checker resolves it. Each line's regular expression is unambiguous,
    and the generator's self-test checks that the probe line admits `0`
    and `1` and not `0x1`; the letter was kept because M2-A.1 names
    `spv=<S>`, and a new letter would need a plan edit. For the
    responsible human.
62. **The platform record tables the probe in a wait for `anchor` runs
    only.** "The IPI probe in a management wait" reads the `anchor`
    image's runs and the checker's costs, which a declared failure does
    not compute. In the second M2 campaign the `no-grant-check` run's
    hart 2 also answered its PING inside its first management wait
    (`BE_MVP:11 IPI_PROBE hart=2 domain=1 sent=0x235989 received=0x2359be
    answered=0x2359be spv=0`, inside `seq=1`'s `ticks=0xa60ed
    service=0x16ba708`), which the checker admitted under M2-A.1, as it
    does for every image with the extension; the line is in the run's
    `serial.log` and its excerpt, not in the record's table or in
    `pings_in_wait=4`. Not changed; for the responsible human.
63. **A release-candidate board record would carry the board's `ssh`
    destination and address.** The board tools write the `ssh` destination
    into each run's record (`k3_ssh=<user@host>`, from `tools/k3-run.sh`'s
    `record "k3_ssh=$k3_ssh"`; line 10 of each `run.txt` in
    `results/20261028-com260-m2a/`), and the reset path writes the failed
    `ssh` probe's message, `ssh: connect to host <ip> port 22: …`, into
    each reset record (`probe_detail=` and `last_probe_detail=`, for
    example in `results/20261028-com260-m2a/mvp/resets/20261028T033233Z.txt`).
    The bundle's rewriting replaces only the repository and home paths
    (`tools/evidence.py`, `rewriter`), and `tools/claim-ledger.py check`
    applies the M4 plan's privacy rule (pass criterion 1) to
    `results/*-rc/`, which a board record named `<date>-com260-rc`
    matches; so a board record of M4-5 made by the same tools would fail
    that check (the M4 plan, stop conditions 9 and 10). Recorded for the
    responsible human before M4-4 fixes the candidate tree; nothing is
    changed. Resolved by Plan revision M4-A (this commit; see
    [Plan revision M4-A](#plan-revision-m4-a-at-this-commit-2026-10-29)):
    `tools/evidence.py` rewrites the `k3_ssh=` field's `user@host`, and
    any ssh target the privacy rule finds, to `<board-ssh>`, and every
    IPv4 address to `<ip>`, in every file of a board record, B0's copies
    included, and refuses a record any file of which still holds either;
    the M2 campaign's record, made again with it, holds 20 `<board-ssh>`
    and 26 `<ip>` where the accepted record holds the board's strings, and
    nothing the privacy rule finds. The accepted records are not
    rewritten.
64. **The kexec rehearsal's host kernel names the account and machine that
    built it.** The rehearsal's Linux host is B0's GCC rehearsal kernel
    (`REHEARSAL_KERNEL`, `tools.mk`), an external input whose banner reads
    `Linux version 7.3.0-rc4-… (<user>@<host>) …` in each rehearsal's
    `console.log`, which the development bundle keeps
    (`build/mvp/evidence/check/rehearsal/*/attempt-1/console.log`, six of
    them). A release-candidate record that holds the complete host bundle
    (the M4 plan, "The release-candidate evidence (M4-4)") would carry it,
    and the checker's privacy rule matches the `ssh` forms of a user and
    host (`ssh://`, `user@host:`, `ssh user@`, `ssh…=…@`), not a bare
    `user@host` in parentheses, so `check` would pass with it: the M4
    plan's stop condition 9 ("a host name … that the bundle's rewriting
    and the checker do not catch"). The guests' banners carry the build's
    fixed `be@beryllium` (`tools/build-guest.sh`, `KBUILD_BUILD_USER` and
    `KBUILD_BUILD_HOST`), which names no machine. Recorded for the
    responsible human before M4-4; nothing is changed. Resolved by M4-4's
    tool (`0a968bf0`), not by Plan revision M4-A: `tools/rc-record.py`
    rewrites a `Linux version` banner's build `(user@host)` to
    `(<build-user>@<build-host>)` in every file of a release-candidate
    record, the host bundle's rehearsal consoles among them, and keeps the
    guests' `(be@beryllium)`. The code names leave a banner's
    `(user@host)`, which is none of the privacy rule's ssh forms, so the
    development bundle under `build/` keeps it.
65. **The board record's title names M2.** `tools.mk` passes
    `--title "MVP M2 COM260 campaign $(notdir $(K3_RUN_ROOT))"` to the
    board record's summary (its line 349), as M0's and M1's records were
    titled "MVP M0" and "MVP M1" by the tree of their day (the first line
    of each `results/*/summary.md`), so a board record of M4-5 made by
    this tree would be titled "MVP M2 COM260 campaign …". The M4 plan
    changes `tools.mk` only to run its two new tools ("What M4 does not
    do"). Recorded for the responsible human; nothing is changed.
    Resolved by Plan revision M4-A (this commit): `tools.mk` passes
    `--title "$(K3_RECORD_TITLE) $(notdir $(K3_RUN_ROOT))"`, with
    `K3_RECORD_TITLE ?= MVP COM260 campaign`, and M4-5 passes
    `K3_RECORD_TITLE="MVP 1.0 release candidate COM260 campaign"`; the
    accepted records' titles are history.
66. **Two forbidden words are also command and field names.** The
    phrasing rule matches each literal case-insensitively as a whole
    phrase (`docs/claim.md`, "Forbidden phrasings"), so the literal "TEE"
    matches the shell command `tee` (as in the `Makefile`'s recipes,
    `… | tee $(RECORDS)/…`), and the conditional "SMP" matches the kexec
    rehearsal's `smp=8` field (`BE_MVP_KEXEC_REHEARSAL: PASS smp=8 …`)
    in any release surface without "static hart ownership"; QEMU's
    `-smp 8` does not match, its hyphen being part of the boundary. The
    release surfaces avoid both words, and none quotes such a command or
    line. Recorded for the responsible human; the list is the plan's and
    changes only by revision.
67. **The soft limit leaves about 175 lines for `rc-record`.** The new
    checking code is 725 lines (`tools/claim-ledger.py`'s 682 and the
    `Makefile`'s 23 and the wrapper's 20 added lines) of the M4 plan's soft
    limit of about 900 lines for all of M4's checking and record code,
    tests included (Q10), which leaves about 175 for M4-4's `rc-record`
    and its wrapper and `Makefile` lines. If `rc-record` needs more, that
    is stop condition 5, a return of the limit to the responsible human
    for re-evaluation, never a cut. Recorded for the responsible human.
    Resolved as foreseen: with `rc-record` (`0a968bf0`) the count is 1,347
    (see [M4-4's tool](#m4-4s-tool-and-the-privacy-rules-false-positives-at-0a968bf0-and-ca322220-2026-10-28)),
    and stop condition 5 is returned to the responsible human.
68. **The privacy rule's two false positives.** The claim-ledger
    checker's privacy rule read an `@sha256:` image digest as an ssh user
    and host and a package version after a hyphen as an IPv4 address,
    both present in every release-candidate record. Fixed in `ca322220`
    with self-test cases; not a change to what pass criterion 1 forbids.
    Closed.
69. **An IPv6 address is neither rewritten nor refused.** Pass criterion 1
    forbids "an IP address" in a release-candidate record; the claim-ledger
    checker's privacy rule finds an IPv4 literal only, and Plan revision
    M4-A rewrites an IPv4 literal to `<ip>` and refuses what that rule
    finds. A board record whose reset probe reached the board over IPv6
    (`ssh: connect to host <IPv6 address> port 22: …`) would keep the
    address and pass both. None of the accepted records holds one: every
    probe line names the board's IPv4 address. Recorded for the
    responsible human; nothing is changed.

70. **The self-tests printed their fixture strings into the evaluator's
    retained log.** Found by the first `rc-record` run; fixed at this
    commit by reporting a privacy finding's kind and line without the
    matched text (see
    [the entry](#the-checkers-findings-no-longer-quote-the-match-at-this-commit-2026-10-29)).
    Closed.
71. **M5-2 and M5-3 exceed the M5 code soft limit (stop condition 8,
    2026-10-29).** At the merge of the three M5-2/M5-3 branches
    (`d798b065`, plus the `tmux` lock role) the added code since the M5
    plan's acceptance record `9b3fa982`, by the plan's counting rule
    (`git diff --numstat`; Python, shell, Make, and the wrapper; tests and
    fakes included; fixtures, generated files, documents, and the partition
    tool excluded), is **6,865 lines** against the limit of 5,000: the
    board tools 2,113, the tests and fakes 1,529 (while 1,712 kexec-era
    lines went), the U-Boot rehearsal 1,196, the two checkers 741, the
    other tools 897 (968 removed), Make and the wrapper 320, and 69 other.
    The plan's review estimate was 2,300 to 3,300; the console tool's
    echo-checked chunked typing, its serial-log reader (`k3-uboot.py`, a
    file the plan did not name), the per-attempt rehearsal records, and
    the fake U-Boot with the BSP's stamps and noise are where the estimate
    was low. Nothing was cut and no check was dropped, as the plan's limit
    rule requires. Returned to the responsible human, who re-set the
    limit to 10,000 lines (`reset m5 code limit to 10000, proceed, board
    is free`, 2026-10-29; erratum 1 of the M5 plan's acceptance record).
    Closed.
72. **Four plan-letter deviations of M5-2 and M5-3, for the result
    packet.** (a) The plan's "each line at most 60 characters" cannot hold
    the `setenv be_ld '…'` line (95 characters; `be_boot`'s is exactly 60):
    the console tool types every line in pieces of at most 60 characters,
    compares the echo after each piece, and presses Enter only when the
    whole line's echo matches. (b) Q8's committed excerpts "from `Autoboot
    in`" lack the SPL and U-Boot banners the `uboot` checker mode requires,
    so `evidence.py` re-judges each run's whole private capture and
    requires the excerpt to be its tail. (c) The BSP's U-Boot prints its
    own `227 bytes read` when it imports `env_k3.txt` before the autoboot
    line, so the checker counts the seven required lines after the last
    autoboot line, not over the whole preamble. (d) The QEMU rehearsal
    types `load virtio 0:…` (QEMU has no NVMe), omits `nvme scan`, uses a
    stand-in `be_orig_bootcmd`, and types `boot` with the variables in
    RAM, since QEMU has no `saveenv`; B3's pinned upstream U-Boot v2022.10
    (`d96d1c22…`) is the rehearsal's U-Boot (Q9). Also found: `saveenv`
    stores U-Boot's runtime `fdtcontroladdr`, so the NOR copy after the
    restore can differ from the human's original although `printenv`
    matches; the claim compares `printenv` only, as the plan says, and the
    limit text should say this. Open until recorded in the packet. Since
    M5-4 the required limit says it, in one sentence after the plan's
    fixed text (`docs/claim.md`; see
    [M5-1 to M5-4](#m5-1-to-m5-4-2026-10-29-and-30)).
73. **"Historical" in the ledger now has two senses (M5-4).**
    `tools/claim-ledger.py render` writes, in every rendering, "A row
    marked historical has board evidence made at images other than the
    release candidate's." M5-4 marks C-24 to C-26 and C-29 to C-34
    historical (the M5 plan, "Documents and the claim (M5-4)") because
    they are the kexec campaigns' and release candidate 1's evidence,
    which the new board clause does not describe, while the board images
    are byte-identical to release candidate 1's at this tree (item 77),
    and C-29 and C-30 hold no board run at all. Each of those rows' own
    non-claim says why it is historical; the rendered sentence is the
    tool's, outside M5-4's files, and is not changed. The M5 plan's Q16
    also says that the ledger marks the kexec campaigns historical "when
    `R2` is made"; M5-4 marks them now, because the claim's board clause
    changed now and those rows would otherwise stand as current evidence
    for a boot from reset. For the responsible human, with the result
    packet.
74. **The development bundle does not keep two of M5's check records.**
    `check` writes `records/qemu-image-check.txt` (the QEMU-only images
    against the board images) and `records/uboot-rehearsal-self-test.txt`
    (the rehearsal driver's self-test), but `tools/evidence.py`'s
    `RECORDS` does not name them, so `build/mvp/evidence/check` holds
    neither, though it holds the other checks' records. Recorded for the
    responsible human; no tool is changed in M5-4.
75. **Interfaces M5-2 left behind.** `TOOLCHAIN` is still an accepted
    caller variable (the wrapper's list, `tools/make-control.py`, the
    `Makefile`'s check of its value), but since M5-2 no target reads it,
    as none reads `JOBS`: a board session's plan names each image's
    toolchain itself. `tools/evidence.py`'s usage text still shows
    `--board CAMPAIGN ... --preflight FILE --load-checks ROOT`, which its
    parser no longer takes (the board record reads the session's
    `preflight-before/` and `preflight-after/`). The guide says what is
    read. Recorded for the responsible human.
76. **The partition tool's apply exited 5 on the board (closed).** On
    2026-10-30 the responsible human's `--apply` created partition 6,
    ext4, labelled `beryllium`, as planned, and exited 5 on the reference
    feature comparison: the mounted reference partition (p4, Fedora 45's
    `/boot`) listed `orphan_present`, ext4 mount state that a fresh
    filesystem lacks, as `needs_recovery` is, while every format feature
    matched. `f3a04a86` treats `orphan_present` as `needs_recovery` is
    treated, and the self-test's fixture now gives the mounted reference
    both flags, so that its apply case fails without the change. Closed.
77. **The monitor ELFs carry the checkout's path.** The `be-mvp.elf`
    files hold the checkout's absolute path in their debug information
    (61 strings name this worktree in `build/mvp/gcc/be-mvp.elf`), so a
    build in another checkout gives other SHA-256 values for the 32 monitor
    ELFs, while every flat image and all 42 board images, which the board,
    QEMU's U-Boot, and the image checks use, are byte-identical to release
    candidate 1's at this tree. The evaluator mounts the source at its own
    path, so its image comparison is unaffected, and the clean gates at a
    candidate tree run from one checkout. Recorded for the responsible
    human; not a change.
78. **What M5-4 leaves to `X2` and `R2`.** The claim's board clause and
    the ledger's C-10 describe release candidate 2's board path before its
    board session has run; the disclosure states what the board tools do
    and where a session's keystrokes are recorded, not a session; the
    ledger's release block names no candidate tree (null, which the
    checker allows) until `X2` is fixed; and C-10 cites the M5 plan,
    `tools/k3-env.sh`, `tests/check-capture.py`, and
    `tests/uboot-rehearsal.sh` by their SHA-256 at this tree, so any later
    change to one of them fails the ledger check until its row is updated.
    At `R2` the plan's M5-7 adds the rows for release candidate 2's
    records and states what was typed. Recorded for the result packet.
79. **The characterization's first board contacts (M5-6a, 2026-10-30):
    six stopped attempts, each a tool or plan-detail defect fixed with
    dry-run coverage, and the board's facts.** The board was never
    written to, and nothing was saved. (1) `systemctl poweroff` powers
    the COM260 off, and the UART dies in the kernel's last lines before
    Linux's `reboot: Power down`; the tools waited for that line
    (`b514df1c`). (2) A reset pulse does not boot the powered-off board
    (no banner in 60 s); the plan's step g assumed it would. The clean
    shutdown is now `systemctl reboot`, which this board halts at
    `reboot: Restarting system` until the reset line is pulsed, as the
    board-information recipe records (`3a9c54ef`); the human powered the
    board on by hand (the power button was not connected; `k3ctl power`
    was not used). (3) A session's first reset may rest on the board's
    state before the session (the prior halt or terminal marker, over the
    log's last 64 KiB; an idle prompt is read at the log's end whatever
    the session) (`5e1d0b49`). (4) This BSP's `printenv` prints no
    `Environment size: N/M bytes` trailer; a normalized record is the
    variable lines alone (`59d782a4`). (5) U-Boot knows no NVMe device in
    a boot until `nvme scan`; the typed sequence scans first and gates
    `run be_go` on `be_ld`'s lines (`7e833730`). (6) `run be_ld` loaded
    the image (`2584576 bytes read`, `$?` 0, `filesize=277000`) but
    **this BSP's `crc32` prints nothing** (`crc32 0x140000000
    ${filesize}` directly too; its `help` shows the upstream usage;
    nothing stored in the environment). The cause is in the vendor's
    source: Bianbu's uboot-2022.10 commit `54c83a433039a4846f0ad8def1b5
    49d9d78f8c26` (gitee.com/bianbu-linux) replaces the result printing
    of `common/hash.c` with `pr_debug`, compiled out of the normal
    build, so `crc32` and `hash` compute and print nothing (the
    responsible human's other project found this on 2026-10-29 with the
    same build stamp). `md5sum` prints through `cmd/md5sum.c`'s own code,
    and its `md5sum` prints
    `md5 for 140000000 ... 140276fff ==> fc5b0d73…`, the staged image's
    MD5 exactly. On the responsible human's authorization (`you are
    authorized to type any needed diagnostic commands`) the console tool
    gained `diag`, a recorded read-only diagnostic line (`b613dd27`), and
    the attribution witness becomes a digest line: the board's `be_ld`
    ends in `md5sum`, QEMU's rehearsal keeps `crc32` (its upstream
    U-Boot has no `md5sum`), and the checker accepts either form matching
    the image (landed at `09687613`: the board's `be_ld` ends in
    `md5sum`; the checker accepts one digest line of either form; staging
    records `MD5SUMS`; the attribution rule's digest is the MD5 on the
    board and the CRC-32 in QEMU; a staging record made before it must
    be redone). Also recorded: the board's
    `fsuuid` equals Fedora's `blkid`; `fdt print /reserved-memory` shows
    16 ranges, none inside an MVP extent; the two `printenv` records of
    consecutive boots are identical (V empty); the copy test
    (`setenv be_t "${bootcmd}"`) is exact; `ls nvme 0:6 /` lists the 14
    staged images; the `nvme scan` output shows PCIe link up for the
    NVMe. The session records are under `build/mvp/k3-sessions/
    20261030-characterize*` and the private store; the M5-6a verdict
    waits on the typed boot with the digest witness. Open.
80. **The characterization passed (M5-6a, 2026-10-30 07:25-07:29 UTC),
    and the dongle's power tap did not wake a powered-off board.** The
    seventh attempt, with the digest witness, passed end to end at
    `build/mvp/k3-sessions/20261030-characterize-7/`: Fedora's clean
    `systemctl reboot` halted at `reboot: Restarting system`; the reset,
    the `s`, and the characterization set as before; two identical
    `printenv` records; the copy test exact; `nvme scan`, `run be_ld`
    (`2584576 bytes read`, `md5 for 140000000 ... 140276fff ==>
    fc5b0d73…`, the staged image's MD5), and the typed `run be_go` of
    `probe-platform`: `Moving Image from 0x140000000 to 0x108000000`, the
    control device tree loaded to `0x2fbd5d000` (B6's run saw
    `0x2fbd6b000`: the address is U-Boot's to choose, and the checker
    takes it from the capture), the shim on hart 0 with that `fdt`, then
    the probe lines from a cold boot: harts 1 to 7 all HSM `STOPPED` and
    `started=none`, 14 VMID bits, `htval` = GPA >> 2 for load, store, and
    fetch, IPIs 100 of 100 in HS and in V=1, 0 stale reads unfenced and
    fenced, then `BE_MVP:14 SHUTDOWN`: the same facts M0 recorded after
    a kexec. The capture passed in `uboot` mode and all five attribution
    conditions held; the audit mapped four banners to four resets; no
    `saveenv`. The first Beryllium boot from a filesystem load by the
    board's U-Boot. Afterwards, on the responsible human's `power pins
    are connected, you can test k3ctl power button when ready`, a by-hand
    test outside the tools: Fedora's clean `systemctl poweroff` powered
    the board off (as attempt 3 found), and `k3ctl power` taps of 300,
    1000, and 3000 ms were each acknowledged (`OK power N`) and woke
    nothing (no banner, the log unchanged;
    `build/mvp/k3-sessions/20261030-power-test/record.txt`), as were
    a hold of 6 s (07:49:48Z). The human then found header pins 6 and
    5 shorted (thought required) and removed the short; the SPL and
    U-Boot banners were in the log by 07:51:00Z, after a 12 s hold
    (07:50:39 to 07:50:51Z) and around that removal, and the 300 ms taps
    at 07:50:58Z and 07:51:06Z met a board already booting, so which
    action powered it on is not established; Fedora autobooted
    (`uptime -s` 07:51:05Z). The dongle's SLEEP/WAKE line is a candidate
    by-hand recovery path from a software poweroff for the human,
    outside the board tools, which never power the board off or on; its
    effect is to be confirmed on a later occasion with the short
    removed. Confirmed in the negative on 2026-10-31 (the human's
    `proceed with item 80`), by hand, outside the tools, with the human
    present and pins 5 and 6 unbridged
    (`build/mvp/k3-sessions/20261031-power-test/record.txt`): Fedora's
    `systemctl poweroff` over ssh (21:31 UTC) halted the console
    mid-line at the kernel's power-off and the board went off (ssh down,
    the log static at offset 15,758,886); then `k3ctl power` taps of
    300, 1000, and 3000 ms and holds of 6,000 and 12,000 ms, each
    acknowledged (`OK power N`) and each followed by 25 to 30 s of
    watching, and then one `k3ctl reset` (`OK reset`), woke nothing: the
    log did not grow by a byte, and `k3ctl status` kept `pwr=0 k3=n/a`
    (power sensing is not wired). The human then reported that no
    physical power button is attached and powered the board on by
    unplugging and re-plugging its supply: one SPL and one U-Boot banner,
    Fedora up at 21:41:04 UTC with a new boot ID, nothing typed, the
    saved environment untouched. So the 12 s hold of 2026-10-30 did not
    power the board on; the removal of the pin 5/6 short at that moment
    did (the SpacemiT guide's pin 6 is `AUTO_ON_DIS`), and the dongle's
    SLEEP/WAKE line does not power this carrier on from a software
    poweroff in this configuration, whatever the pulse. The consequences
    stand as the tools already have them: the clean shutdown is
    `systemctl reboot`, never `poweroff`; the tools never power the board
    off or on; the recovery from a software poweroff is a mains power
    cycle by the human. The dongle's own README (`k3-com260-info`,
    "Recorded hardware results") says the power-button pin was "verified
    working" on 2026-10-30 without recording the command or duration;
    this result is for the human to carry there. Closed.
81. **Release candidate 2's board session (M5-6, 2026-10-30 07:52 to
    08:18 UTC) passed: 20 of 20 runs from system reset, the environment
    restored; one stop (condition 12) in the middle.** From this
    checkout at `0bfb1ca8`'s tree (the record re-made at `X2`; "The
    release-candidate board campaign" in the result packet) under
    `build/mvp/k3-sessions/20261030-com260-rc2/`: the preflight before
    (PASS; partition 6 ext4 `beryllium`, `env_k3.txt` as recorded, every
    MVP extent free), the staging of the 14 images with `SHA256SUMS` and
    `MD5SUMS` (PASS; the digests pairwise distinct), Fedora's clean
    `systemctl reboot`, two `printenv` records at fresh prompts
    (identical; V empty), the install at a fresh prompt with the human
    present (`K3_ENV_CONFIRM` the recorded `bootcmd`'s SHA-256 prefix;
    `saveenv` `OK`; the install check PASS), then the 14 groups: the
    three GCC probes, `two-guests`, `te-poc`, and `anchor` each three GCC
    and one Clang, and the five negatives, every run its own `k3ctl`
    reset with Fedora down and the saved `bootcmd` loading the selected
    image from the partition (`2584576 bytes read`, the `md5 for` line
    equal to the staged MD5, `Moving Image from 0x140000000 to
    0x108000000`, the control device tree at `0x2fbd5d000` in all
    twenty); each capture judged in `uboot` mode PASS with its five
    attribution conditions and its banner audit; the counts M4 compared
    equal to the accepted records' (`two-guests` `exits=157` both
    domains, `records=138 wakes=2`; `te-poc` `exits=163`/`167`, the
    three `DENY` lines, `records=146 wakes=2`; `anchor` domain 0
    `exits=248 refused=1`, domain 1 paused and terminated at
    `exits=132`, `records=174 wakes=16`, M2-A's), the negatives failing
    as declared (`payload`, `gstage`, `guest-page-fault`,
    `measurement`, `run-timeout`); the restore at a fresh prompt with
    the human present (`saveenv` `OK`), the fresh-prompt record equal to
    record 1 (SHA-256 `72443954…`), Fedora's autoboot under the restored
    `bootcmd`, the preflight after equal to the one before in every
    compared fact, and `board-evidence` (198 files; 20 of 20). The
    terminal marker came 12 to 18 s after each reset; the session's 41
    `k3ctl` resets each map to one SPL and U-Boot banner pair. **The
    stop:** at the fourth select (`two-guests-clang`, 08:00 UTC) the
    `s` sent 1.1 s after the U-Boot banner, as for the three selects
    before it, was lost twice in a row, `bootcmd` ran the still-selected
    `two-guests-gcc` image to `BE_MVP:14` both times (two unplanned
    boots, in `env/unplanned.txt`, counted as nothing), and the campaign
    stopped (stop condition 12). Whether the keystroke was swallowed by
    the tmux pane (a scrolled pane in copy mode takes `send-keys` as
    navigation) or dropped on the serial line is not established; both
    are covered by `0bfb1ca8`: the console tool cancels a pane mode
    before any send and sends `s` a second time after
    `K3_STOP_RETRY_SECONDS` (0.5 s) if no prompt has appeared, inside
    the 3 s window (a stray `s` at the prompt is caught by the next
    line's echo check), and `K3_CAMPAIGN_SKIP=N` resumes a stopped
    session at its (N+1)th group. The campaign resumed at group 5
    (08:09 UTC); no later `s` was lost, and none was retried. Plan
    departures to record in the packet: the resumed session (the plan
    has no resume) and the second `s` (the plan's "retry once, then
    stop" is for a missed `s` after an unplanned boot, and was followed;
    the second `s` is sent before any boot). The restore's three resets
    (to its prompt, to the fresh-prompt record, and for the autoboot
    into Fedora, `boot` being never typed) are the plan's. Open until
    `R2`.
82. **`board-evidence` copied the preflight after the session
    unredacted (closed).** Its first run over the session failed B0's
    retention check: `mvp/preflight-after.txt` held Fedora's
    `root=UUID=` from the kernel command line. B0's retention redacts it
    in its own copy of the preflight before, and `evidence.py` copied
    the one after through the code-name rewriter alone; the dry run
    never saw it because the fake board answers the preflight from B7's
    already-redacted record. Fixed at `ec6b51d3`: the copy goes through
    `b0_sanitize` as the excerpts do; the fake board prints a root UUID
    of its own, and the campaign case requires it absent and the
    redaction present. The record was re-made; `identifying()` finds
    nothing in its 198 files.
83. **The board record's run table shows `Kernel ?` and `Boot ID
    before` as `reset-N@offset` (closed).** B0's retention writes the run
    summary unchanged (the plan keeps `retain-results.py` as it is), and
    its `Kernel` column is the launching host kernel, which a boot from
    system reset has none of; the tool's `boot_id_before` is the
    launching reset's sequence and log offset, as the plan's "a new
    boot" rule defines a boot. Cosmetic; recorded so the column is not
    read as a missing value. Closed by the debt sweep (approved
    `approve 1, 3`, 2026-10-30): `k3-run.sh` records
    `board_kernel=none (boot from system reset)`, which the summary's
    column shows, with a dry-run case; release candidate 2's record is
    not re-made (a record is never overwritten), so its summary keeps
    the `?`. The `Boot ID before` form is by design and stays.
84. **The code-name rewriting took a device-tree node for an ssh target
    (closed).** In the first board record of release candidate 2 every
    excerpt's `pcie_dw_spacemit pcie@80000000: Port0 has no device detect
    gpio` read `pcie_dw_spacemit <board-ssh>: …`: the `user@host:` form
    of the ssh rule (Plan revision M4-A.1) matched a node name and its
    unit address. Not a leak, and the responsible human saw it in the Q8
    review (`yes, proceed`). The form now passes a host that is
    hexadecimal with a digit (`pcie@80000000:`, `nvme@ca400000:`), in
    `evidence.py`'s rewriting and in its and the ledger's privacy rule,
    which the evidence self-test keeps equal, with a case for both the
    kept node and the rewritten target. A hostname of hexadecimal letters
    and digits alone (`db1`) in that one form would now be kept; the ssh
    command and `K3_SSH=` forms still catch it. The record was re-made
    at `X2`.
85. **Two retained record files end lines in a space (closed).** In release
    candidate 2's board record every run's `handoff-excerpt.log` holds
    the BSP U-Boot's stamped empty line before `Starting kernel ...`
    (`[   6.508] ` with a trailing space, as the serial log has it), and
    `mvp/session/stage/staging.txt`'s `files=` line ends in the space
    `k3-stage.sh`'s `ls | tr '\n' ' '` leaves. Both are byte-exact under
    the record's manifest and are not edited; `.gitattributes` exempts
    exactly those paths from Git's trailing-space check, as M4 did for
    the raw QEMU captures. The staging tool's trailing space is a
    cosmetic defect to fix in a later source change, not after `X2`.
    Closed by the debt sweep (approved `approve 1, 3`, 2026-10-30):
    `k3-stage.sh` joins the names with `paste -sd ' '`, and the dry run
    requires the `files=` line to end in a name and no line of the
    staging record to end in a space; the exemptions for the two
    retained files stay, as the files do.
86. **The acceptance record broke the ledger's pin of the M5 plan
    (closed).** The ledger's C-10 cites `planning/mvp-m5-plan.md` by its
    SHA-256, and the commit recording release candidate 2's acceptance
    (`db2c0bab`) added the result's lines to that plan's decision record
    and status record, so `claim-ledger.py check` (and with it
    `./mvp/mvp check`) failed at `db2c0bab` and at the pushed tip
    `52092935` (the push record), found by the debt sweep's check run.
    C-10's entry is refreshed to the plan's bytes at `db2c0bab`, the
    convention `0097f66a` set when the digest witness changed a cited
    tool; the plan's text as accepted at `0066794d` is unchanged. The
    check passes again at the commit that carries this item. A later
    change to that plan, or to `tools/k3-env.sh`, `tests/check-capture.py`,
    or `tests/uboot-rehearsal.sh`, needs the same refresh.
87. **The M6 plan's Q3 names the wrong open item.** The accepted M6 plan
    (`b2c62d54`) says, in its "Unchanged" section and its Q3 row, that
    removing the `KEXEC_*` constants and the scenarios' `kexec_fdt` object
    closes "open item 59". Item 59 is the run tool's wait for a new boot
    ID, closed by M5-4 for M5's runs, and no open item recorded the kept
    kexec names: M5's Q6 kept them, in the M5 plan's text alone. The
    removal is M6-2's (Q3) and is recorded in its entry; nothing closes.
    The reference is a transcription error in the frozen accepted plan,
    like M0's `0x104044000` (item 1), and is left as written there.
88. **The model's policy instances follow the scenarios, and their pinned
    identities with them.** The first gates run at the intended `X3`
    (`4cc5c53a`, 2026-10-31 03:31 to 03:44 UTC) passed the lock, `check`,
    `evaluate`, the U-Boot rehearsal, and `kernel-repro`, then failed
    `./be model-check` at `model/tests/unit/policy_test.c:559`:
    `seal_view("instance2") == 0x14bf7d9df5ad5475`. M3's policy
    instances 2 and 3 are generated from `mvp/scenarios/te-poc/` and
    `mvp/scenarios/anchor/` (`model/tools/gen-policy-fixtures.mjs`;
    `model/Makefile`'s `POLICY_INPUTS` names both `scenario.json`
    files), so M6-2's removal of the scenarios' `kexec_fdt` object (Q3)
    took one labeled monitor-memory object from each instance: te-poc's
    objects 10 to 9 and labels 13 to 12, anchor's 13 to 12 and 16 to
    15; their labeling identities (`0x06f34f1c…` to `0x784c7507…`,
    `0x41ef864e…` to `0x52a3bf8f…`) and configuration identities
    (`0x14bf7d9d…` to `0x109e99ab…`, `0x5fdcbf76…` to `0x735e5d85…`)
    changed; the view and policy identities did not. The Rocq proofs
    compile the regenerated `Instances.v` and pass unchanged
    (`instances=generated`), every analysis A1 to A8 still passes on
    both instances, and the bindings are `ok`, so stop condition 4 (a
    proved theorem) does not apply; what changed is the value two test
    files pin, `policy_test.c`'s `test_identities` and
    `tests/check-reports.mjs`'s instance rows (the counts, the
    identities, and A1's text), refreshed to the regenerated values, as
    the ledger's pins were. The M6 plan's Q3 says the configuration
    identities change with the rest; it does not say the model's tests
    record them, and the M6-4 entry above first said no `model/` file
    changes. The M6-4 exit (`./be model-check` and `./be evaluate` PASS)
    was not run at M6-4, where it would have shown this hours earlier;
    the gates showed it instead. The first run's logs are kept as
    `build/mvp/rc3-gates-attempt-1-4cc5c53a/` (development history, not
    evidence); `X3` moves to the commit carrying this item, and the
    gates run again there.
89. **The console tool reads the tmux session's active pane, which need
    not be picocom's (closed).** `tools/k3-console.sh check` asks tmux for the
    `pane_current_command` of `K3_TMUX_SESSION` and stops unless it is
    `picocom`. Since release candidate 2's session the operator's
    session `k3-console-1` had gained a second window (a `copilot`
    shell), which was the active one, so release candidate 3's first
    `k3-env record` stopped at the check (`the pane of k3-console-1 runs
    copilot, not picocom`; 04:13 UTC) before any reset or keystroke;
    `records.txt` keeps the stopped attempt's verdict line above the
    passing one. The session was re-run with `K3_TMUX_SESSION=
    k3-console-1:0`, tmux's session-and-window form, which every tmux
    command the tool issues accepts; `session.txt` records it. The
    tool's own rule ("the operator's picocom session") held: nothing was
    typed at a pane that was not picocom's. A later source change may
    let the tool find picocom's pane in the session itself, or document
    the window form; none is made at `X3`. Closed by debt sweep 2
    (2026-10-31): once per invocation, before anything is waited for or
    typed, `check`, `stop-autoboot`, `type`, and `diag` list every pane of
    every window of the session (`tmux list-panes -s`); of the panes whose
    command is `picocom`, exactly one must have its process, or a child of
    it, holding `K3_SERIAL_LOG` open, and every later tmux command of the
    invocation (`display`, `send-keys`, and the pane-mode cancel) targets
    that pane by its tmux pane ID (`%N`), never the session. No pane that
    runs picocom, none that writes the log (`does not write`, as before),
    or more than one is stop 1, and nothing is typed. `check`'s PASS line
    adds `pane_id=`, and each step that types records the pane in the
    keystroke log (`tmux` `pane=%N`). `K3_TMUX_SESSION` may still be given
    in the `session:window` form release candidate 3's records cite
    (`k3-console-1:0`): tmux 3.8's `list-panes -s` takes the target's
    session, its window having to exist, and lists every pane of that
    session, so the form names the same session and the whole session is
    searched. The dry run's `console-check` case covers a second window
    running another command, the session by its name and in its
    `session:window` form (either window), a window that does not exist,
    no pane that runs picocom, and two picocom panes writing the log; the
    new `console-window` case records and types through such a session
    and requires every `display` and `send-keys` to address picocom's pane
    by its ID; and the fake tmux (`tests/fake-uboot.py`) refuses a
    `display` or `send-keys` addressed to anything else, so every case
    that types checks the target too.
90. **The preflight pair differs in the kernel because the Fedora before
    the session had been booted by hand.** Release candidate 3's
    preflight before found Fedora on `7.3.1-300.0.riscv64.omni.fc45`
    and the one after on `7.3.0-65.1.riscv64.omni.fc45`, the release the
    saved `f45_rel` names and release candidate 2's. The serial log
    shows the earlier boot (00:59 UTC, before this session, outside the
    board tools) as a one-shot test typed at the U-Boot prompt (`setenv
    testrel 7.3.1-300.0…`, three `load` lines, `booti`) with nothing
    saved; the restored `bootcmd` then booted what it always boots. The
    platform record shows the pair's `kernel` row and the "Fedora kernel
    release" row against M0's as `differs`, with the kernel's reserved
    extents; every fact the MVP depends on (the partition, the hart and
    extension lines, the firmware identity, the region check,
    `env_k3.txt`) is equal. The environment restore rule concerns the
    saved environment, which is shown restored (record 3 = record 1);
    which kernel the human's own boot command loads is theirs. The
    ledger's C-45 says the pair differs in the kernel and why.
91. **The wrapper passes a stray `k3-env install` argument to make as a
    goal (closed).** `./mvp/mvp k3-env install FILE` is not the interface: the
    `k3-env-install` target takes the plan's first image itself, and
    `K3_ENV_CONFIRM` is the only input. In release candidate 3's session
    the install was invoked with the image's file name after `install`;
    the wrapper's `later` passed it to make, which ran `k3-env-install`
    to its PASS (`saveenv OK`, one attempt in `install.txt`) and then
    failed on the stray goal (`No rule to make target
    'be-mvp-probe-platform-gcc.img'`; exit 2) with nothing further done
    on the board (release candidate 2's install had been invoked
    without the argument; its step log ends `rc=0`). A later source
    change may make the wrapper reject arguments a command does not
    take; none is made at `X3`. Closed by debt sweep 2 (2026-10-31): for
    every command that runs make, the wrapper requires, before make runs,
    each argument to be `VAR=VALUE` with `VAR` of the form
    `[A-Z][A-Z0-9_]*` and one of the variables it passes for that command
    (the caller variables, and for `uboot-rehearsal` and the `k3-*`
    commands their own settings); any other argument, a file name or a
    misspelled name, prints `BE_MVP: refused ARG: …` and the usage and
    exits 2, and nothing runs. `tools/make-control.py` still checks every
    assignment that reaches make, and refuses the board settings there, as
    before. The dry run's new `wrapper-arguments` case runs a copy of the
    wrapper beside a stand-in Makefile that records each goal it runs:
    `k3-env install be-mvp-probe-platform-gcc.img` and `k3-env install
    K3_ENV_CONFRIM=…` exit 2 naming the argument with no make run, and
    `check JOBS=2` and `k3-env install K3_ENV_CONFIRM=…` reach make with
    their assignments.
92. **A review snapshot and the publication policy.** LLM_POLICY_ALIGNMENT.md
    says that pushing any part of the current private repository to a
    public repository is blocked and that a public release uses a new
    clean repository populated with reviewed material, its selection the
    human's; it names `beryllium-project/beryllium-hypervisor` as the
    private repository. On 2026-10-31 the responsible human directed a
    fresh-history snapshot of release candidate 3 for review, to be
    published by them under that name after the private history moves to
    `beryllium-project/beryllium-hypervisor-internal` (done; see the
    snapshot-support entry). The snapshot's README states that it is a
    review copy, not a release, authorized by the human on that date. The
    policy document is not changed by automation: its repository name,
    and whether a review snapshot is an exception to or an instance of
    its release boundary (the release path's steps 2 to 4 in a bounded
    form, with the selection recorded), are the human's to revise. On
    the human's instruction of the same day (`recheck any upstream LLM
    policies and update as needed`) the policy document now names the
    internal repository, records the review snapshot under a section of
    its own as a review copy made and checked by automation and pushed by
    the human, with the release boundary and the clean-repository process
    standing, and records the upstream recheck (the "Policy recheck"
    entry). Whether the document should define a review snapshot as a
    category of its own, rather than record this one, stays the human's
    choice; the record is in.
93. **The dry run's autoboot cases are timing-bound on a loaded host.**
    The fake U-Boot's autoboot window in the dry run is 0.8 s
    (`tests/run-tool-dry-run.sh`, `autoboot_seconds`), against the
    console tool's second `s` after `K3_STOP_RETRY_SECONDS` (0.5 s)
    without a prompt and its polling of the serial log. On 2026-10-31 a
    full `./mvp/mvp check` in this checkout ran while another full check
    ran in the refreshed snapshot on the same workstation, and the
    `missed-s` case (two swallowed `s`, then a boot whose `s` should
    land) stopped with `stop=12 a second missed s`: the third `s`, not
    swallowed, came after the window had closed. Run alone, the same tree
    passes the case, as every earlier gate run did. The board's window is
    3 s and the tool sent its `s` 1.1 s after the banner in every
    campaign, so the margin there is wider; the dry run's is a test
    setting. A later change may widen the fake's window for the
    `missed-s` cases or make the case report the lateness, so that a
    loaded host does not read as a tool defect; until then, run one gate
    at a time on a host. **Closed 2026-11-03** (`b7e059b5`): the dry
    run's window is the board's 3 s (`autoboot_seconds`, the fake's
    default too), which the fake runs to its deadline whatever its
    keystrokes, as the board does, and the fake records each `s` with its
    time after `Autoboot in` (`autoboot.log`). On 2026-11-03, at load
    averages of 1.3 to 14, a first `s` came at most 1.15 s and a second at
    most 1.71 s after it, so the margin inside 3 s was 1.29 s or more; the
    second never came before 0.71 s where measured, which in the 0.8 s
    window had left it 0.09 s at best. The cases whose outcome rests on
    the deadline (`missed-s`, `missed-s-twice`, `late-s`) give the console
    tool its default wait after a second `s`, `K3_ECHO_SECONDS=5`, the
    board's value, which outlasts the window as on the board; the dry
    run's 1 s, for speed, stays for the others. A case's failure on a
    board where an `s` came late names the lateness first (`FAIL late by
    N s under load: ...; not a tool defect (then: ...)`), `missed-s`
    asserts each sub-case's `s` by outcome, the case `late-s` proves the
    report on a 0 s window, and the check `autoboot` fails the dry run on
    any late `s` and prints the run's latest. Two waits the wider window
    reached moved with it: `mvp-hang`'s run waits 6 s, not 2, and
    `input-characterize`'s runs 60 s, not 20 (its probe types 256 keys
    one at a time; its runs took 19 to 25 s under load, over 20 s even
    with the old window, which `missed-s`, failing first in the same
    lane, had hidden). The unmodified dry run failed 2 of 2 runs at load
    averages of 12 to 16; at `b7e059b5`, `make -C mvp run-tool-check`
    passed 5 of 5 at load averages of 1.3 to 5.7, and two dry runs at
    once, item 93's trigger, passed, each dry run 217 to 232 s (the
    unmodified one's earlier passing runs: 177 and 195 s; the window adds
    about 2.2 s to each of the 23 boots per run that run it out). The
    console tool and the other board tools are unchanged (item 121
    records a reading of its second `s`); one gate at a time is no longer
    needed.
94. **C-05 and the accepted M0 plan's `hgatp` sentence (row I of the RC3
    snapshot reviews).** `planning/mvp-m0-plan.md`'s "G-stage and VMIDs"
    says that after the barrier no hart writes `hgatp`; the boot barrier
    (`BE_MVP:07`) precedes each domain hart's one install at its entry
    (`src/mvp-hartmain.c`), so the sentence is an erratum of the accepted
    plan. The ledger's C-05 states the boundary the code has (debt sweep
    3, `2deabaeb`) and its evidence note records the erratum; the pinned
    plan is not edited. Open as a recorded erratum of accepted text.
95. **The evaluator's closure is no longer buildable from public sources
    (row J).** On 2026-11-01, 38 of the 259 closure NEVRAs were no longer
    in Fedora 44's `fedora` and `updates` repositories and 25 of those
    were absent from koji's signed paths too by an ad-hoc probe (the
    sweep's record, above); the tool's own measurement the same day, in
    the refreshed snapshot's fresh `build/` with no cache seeded
    (`fetch-closure.py` through `./mvp/mvp evaluate`), found 19 not in
    the repositories, 3 of those on koji's signed paths (`expat`, `gcc`,
    `util-linux`), and 16 in no public source (`cpp-16.2.1-2.fc44` first),
    so `./mvp/mvp evaluate` on a host without the development host's
    verified cache (`MVP_RPM_CACHE`) cannot build the image; the lock
    refreshed from this host does not move, the closure being the
    installed set. The remedies are the responsible human's: publish the
    verified cache (385 MB of Fedora-signed RPMs) beside the snapshot, or
    update the host's packages and move the lock and closure to served
    builds (a toolchain move, as M3-2's was: GCC, QEMU, and the image
    identities change and the gates are re-run and re-recorded). The
    snapshot README says what a third party needs. **Closed 2026-11-01 in
    debt sweep 5** (`41c872b6`): the fetch tool's own live run had found
    16 of the 259 in no source it tried (the figures above came from a
    looser `dnf repoquery` measurement); Fedora's updates archive serves
    them, byte-identical to the pins, and is now the third source, so the
    whole closure fetches from public sources (`fedora:116, updates:124,
    updates-archive:19` on 2026-11-01); the verified cache is an
    optimization and the fallback, and the residual is item 106.
96. **The B0, B6, and B7 READMEs describe the kexec procedure without the
    gate.** Their launchers and make targets now refuse without
    `BE_KEXEC_APPROVED` (debt sweep 3, `e728b27e`), but the accepted
    READMEs' procedures (`bringup/k3-b{0,6,7}/README.md`) still read as
    if a run followed the command alone. They are accepted records of
    the B-series and were deliberately not edited in the sweep; a note
    at their head, if the human wants one, is a small later change. Open.
97. **A ledger pin on a tool makes every fix two commits.** C-40 pins
    `tools/gen-scenario.py` by SHA-256 with its source commit, so a change
    to the tool is one commit at which `claim-ledger check` fails and a
    second that refreshes the pin (`13c7456c`, then `9e6cdc3e`; debt
    sweep 1's C-10 was the same). Pinning a tool by the commit that holds
    it, or exempting tools from the byte pin while keeping records
    pinned, would make a tool fix one commit; the ledger's schema is the
    human's to change. Open.
98. **Tier 2 of the remediation plan has no pending input (corrected).**
    The plan and the packet as presented described tier 2 as waiting for
    "the Claude CLI and Codex CLI reviews" as further reviews of the
    snapshot. The two reviews the human was comparing against the
    Copilot CLI's are independent design reviews of Plan revision S3-C
    (the S3-C packet's section 8 brief), not of the snapshot's code; they
    are processed on the S3-C plan branch. The register closes at rows A
    to L; a later review of the snapshot's code would open a new sweep
    with new letters in the same per-row shape. Closed 2026-11-01 with
    the sweep's acceptance.
99. **A `SECURITY.md` for the public review snapshot.** The responsible
    human's direction of 2026-11-01: the public review snapshot is to
    carry a `SECURITY.md` saying that it is an early pre-release snapshot
    for external review purposes only, and that, for now, any security
    issue may be openly filed against the repository (there is no private
    disclosure channel yet). Written as a root `SECURITY.md` in the source
    tree, which every snapshot carries unchanged (the tool keeps every
    file but `README.md`), pointed at by the snapshot README and required
    by the snapshot self-test; the published copy is the human's push.
    Closed 2026-11-01 in debt sweep 4 (`954b8f7f`).
100. **The capture checker accepts a forged loader block.**
    `tests/check-capture.py` read U-Boot's load and digest lines only
    after the last autoboot line (`tools/k3-uboot.py` likewise), so an
    image that prints its own autoboot line and a forged loader block
    before its first marker was read in place of U-Boot's lines; the
    Claude Code review of S3-C reproduced it against the checker
    (`planning/mvp-plan-s3c-review-reconciliation.md`, row Z). Harmless for
    M5's purpose, catching staging mix-ups, it disqualified any framing of
    the loader digest as a measurement stage. Fixed by enforcing M5's
    one-boot-per-run attribution rule in the checker (exactly one autoboot
    line per run's loader stream, the lines read after it) with four
    capture mutations that plant a forged block, the 40 retained captures
    re-judged read-only with no finding; C-10's pin refreshed. Closed
    2026-11-01 in debt sweep 4 (`ed0c413d`, `01661500`).
101. **Binding.v's hand-copied source readings are stale at RC3.**
    `model/proof/Binding.v` cites `mvp-runtime.c:2201-2202` (L303) and
    other line numbers of M3's tree; the file has 2,194 lines at RC3.
    C-06's evidence rests on those readings and no gate checks them
    (reconciliation row R and section 6). The M8 plan's stage 1 is to
    re-read them at its target commit, cite symbols rather than lines, and
    add a gate check; until then the readings are M3's, correct at
    `b0a0f352`. **Closed 2026-11-03** (M8-7): stage 1's 92 readings cite
    symbols at the target commit `6fbcc3d1` and `model/tests/check-concrete-readings.sh`
    checks each (`citations=92` in the model gate); C-06's non-claim is
    re-read to say so and to name Binding.v's line numbers as M3's
    history; `single_writer_carried` strengthens H3 over the concrete
    steps (C-52). Binding.v itself, an accepted module, is unedited.
102. **The model gate's escape-hatch pattern matched singular keywords
    only.** `model/tests/run-proofs.sh` banned `Axiom`, `Conjecture`,
    `Parameter`, `Variable`, `Hypothesis`, `Admitted`, `admit`, and
    `Abort`; Rocq also accepts `Axioms`, `Parameters`, `Hypotheses`,
    `Variables`, and `Conjectures`, which the pattern passed (the Claude
    Code review confirmed it). Latent: no proof file used them. Fixed in
    both patterns with `model/tests/check-escape-pattern.sh` as the
    negative test, under `fix code issues`. Closed 2026-11-01 in debt
    sweep 4 (`97874695`).
103. **Two planning documents name a VST route that cannot verify the
    project's own C.** `planning/open-tooling.md` L144 and
    `planning/research-synthesis.md` L376 admit VST "through its
    BSD-licensed opam distribution"; verifying one's own C with VST needs
    `clightgen`, whose passes depend on CompCert files outside the open
    licence (the Copilot CLI and Claude Code reviews reach this by
    different routes; reconciliation row U). S3-C's second candidate says
    so for M8; the two documents' correction is a planning edit for the
    human's direction. Closed 2026-11-02 in M8-2 (`3c08c90e`; the M8
    plan's Q13 made its acceptance the direction): each sentence now says
    that verifying the project's own C with VST needs `clightgen`, whose
    passes depend on CompCert files outside the open licence, so VST is
    not a route for Beryllium's C.
104. **Q38's negative premise is in no committed record.** S3-C says this
    U-Boot has `crc32` and `md5sum` and no `hash`, `sha1sum`, or
    `sha256sum`, from the `help` listing of characterization attempt 7
    (2026-10-30); that session's record lives under `build/`, outside the
    tree. The M9 plan should commit the listing, or a hash of the record,
    as the premise's evidence. Open.
105. **The snapshot tool's commit trailer carried one session's id.**
    `tools/snapshot.sh` wrote `Copilot-Session:
    bd7da407-7682-492f-afbd-5e610657b601`, the session that wrote the
    tool, into every snapshot commit, so a snapshot made by another
    session carried a wrong id; the refresh of 2026-11-01 (`3b6d76da` in
    the human's local clone) had its trailer corrected by hand. Fixed: the
    id comes from `BE_SNAPSHOT_SESSION` and the trailer is omitted when it
    is unset, with three self-test cases. Closed 2026-11-01 in debt sweep
    4 (`f1bad063`).
106. **The closure's public sources end with Fedora 44.** The fetch's
    repository sources are Fedora 44's `fedora` and `updates`
    repositories and its updates archive (item 95). When Fedora 44
    reaches its end of life (about thirteen months after Fedora 45's
    release), its release and updates repositories move to
    `archives.fedoraproject.org`, the `dnf` metalinks follow, and the
    updates archive's retention past that point is not documented; the
    two repository sources then need the archive host, and the lock and
    closure's move to a current release (a toolchain move, as M3-2's) is
    the lasting answer. Until then the verified cache on the development
    host is the fallback for any build no public source serves, and a
    third party's `evaluate` depends on Fedora's retention. Open.
107. **The public snapshot's pushes as normal deltas: the shape.** The
    responsible human's standing direction of 2026-11-01 (`note that
    from now on, we will push changes for the rc3 snapshot as normal
    deltas, so people can see what is changing`) is in force as a rule
    of conduct: commits on top of the public tip, fast-forward pushes by
    the human, no reset or collapse. Open is whether the tool's
    one-commit-per-refresh (whose diff is already the delta) satisfies
    "see what is changing", or whether `tools/snapshot.sh` should gain a
    mode that replays the source range's commits one by one, each
    source commit's tree minus the exclusions committed with its own
    message and a `Source-Commit:` trailer, the snapshot README and
    `SNAPSHOT.txt` refreshed in the last commit, so that the public
    history reads like the private one. The second needs a small tool
    change with self-test cases (the exclusions applied per commit; a
    merge commit on the source line flattened to first-parent order; the
    README template's fields), and the snapshot README's "fresh-history
    snapshot" wording revised. For the human's answer; until then
    refreshes are made by `update` from the public tip. **Closed by
    judgement 2026-11-04** (`use your best judgment on remaining issues`):
    one commit per refresh stays; its diff against the previous public
    commit is exactly the source range's change outside the exclusions,
    which is what "see what is changing" asks, and replaying this
    repository's commits one by one would publish messages written for
    it (PMR and session references, merge records) through a tool change
    no reader of the snapshot needs. The human may reopen it.

108. **The printed configuration identity does not cover the console
    grant.** M7-3 carries `console_input` into the sealed canonical R1
    identity, but neither the identity `BE_MVP:00 CONFIG_SEALED` prints nor
    `policy-check.py`'s manifest and configuration identities include it
    (the latter deliberately, so that the accepted scenarios' printed
    identities and `anchor`'s measurement stay unchanged, the M7 plan's
    stop 5). A `<scenario>-shell` image therefore prints its base
    scenario's identity; the images differ by name, pins, and their
    `BE_MVP:15` line. M9, which redefines the measured identities, is where
    the grant joins them. **Closed 2026-11-03** (M9-5): since M9-3 the
    console grants are a measured record of the log's stream 1
    (`console-grants`: one byte per domain, then SHA-256), extended into
    `r1` and compared with the reference, so a shell variant's log and
    launch-time registers differ from its base's; the printed
    `CONFIG_SEALED` identity stays the sealed core identity by design and
    is itself the log's `core-identity` record (ledger U-14's note; C-40's
    non-claim).
109. **`InputRing.v`'s gate is not run by `make -C model proof`.** The
    module has its own gate (`model/tests/run-input-ring.sh`, PASS) because
    the M7 plan enumerated the module and no edit to the accepted
    `model/Makefile` or `run-proofs.sh` (stop 4). The one-line additive
    hook, `tests/run-input-ring.sh` under `proof:`, is the responsible
    human's decision; until then M7-6's gates run the script explicitly
    (ledger U-15). **Closed 2026-11-01**: the human answered `your
    choice` and the hook is added (`model/Makefile`'s `proof` runs
    `tests/run-input-ring.sh` after `tests/run-proofs.sh`; `make -C model
    proof` prints the new gate's PASS line); recorded as an M7 departure
    in the plan's decision record, and U-15's note is updated.
110. **The `live` images keep the 2^32-tick budget.** Q12's `live`
    variant with 2^35 ticks (24 minutes on the board) needs a per-image
    `BE_MVP_RUN_TIME_BUDGET` switch in `src/mvp.h` that M7-4 did not make;
    `./mvp/mvp live` builds the shell images and prints their QEMU command
    lines with the 178 s budget. A human session must fit it, or the switch
    is a later small change. Open.
111. **M7's soft limit (stop 9).** 7,625 of 8,000 counted lines after
    M7-4; M7-5's remaining tooling (the console tool's guest-typing mode,
    its dry-run cases, the probe image) would exceed the limit. Returned to
    the responsible human for re-evaluation (the plan's rule: never a cut);
    the board characterization waits with it. **Closed 2026-11-01**: the
    human re-set the limit to 9,500 (`limit 9500`; the M7 plan's erratum
    1); M7-5's remaining tooling proceeds.
112. **Plan erratum: the M7 plan's D-11 session for `two-guests`.** It
    says "write and read the channel" and names denials, but `two-guests`'
    domains have no role, channel, or denial (the scenario is policy-free);
    the session made is the nonce, `ls /bin | wc -l`, two typed negatives,
    and the exits, and the channel and denial demonstrations are
    `te-poc`'s and `anchor`'s. Recorded here and in the session file; the
    accepted plan text is not edited. **Closed 2026-11-02**: the M7
    result's acceptance record notes it, and the M7 plan's decision
    record carries it as erratum 2.
113. **The `ring-full` drop cannot be provoked in QEMU.** QEMU's 16550
    FIFO yields at most 16 bytes a poll and the guest reads at least every
    2 s, so neither the 256-byte poll batch nor the 4 KiB input ring fills;
    and which bytes a real overflow would drop depends on timing, so the
    `:18` digest could not be reconciled. The host test covers the drop
    rule (`input-test.c`); the plan's D-11 300-byte negative was left out
    of the sessions. Open as a known limit of the QEMU evidence.
114. **The `k3ctl` client in the human's checkout is v1.1; the pin is
    v1.0's bytes.** During the M7 board session (2026-11-02) the
    responsible human updated their checkout of `k3-com260-info` to
    `89f5c717` (k3ctl v1.1), so the console tool's `check` stopped on the
    client's SHA-256 (`9c11b4f8…` against `mvp/tools/k3ctl.sha256`'s
    `7ca3d78a…`); the session ran the pinned bytes from a copy under its
    own directory (`git show 9fcc1ed:tools/k3ctl/k3ctl`, equal to the
    pin), recorded in the record's Serial log paragraph and
    `session-note.txt`; the dongle's firmware is 1.0. Moving the pin to
    v1.1 is the human's decision after their review of the new client
    (its protocol or `status` fields may have changed); until then the
    tools need `K3CTL` pointed at a copy of the pinned bytes. **Decided
    2026-11-02** (`stop, keep k3ctl pin where it was for now, clone a
    copy if needed`, reversing `move k3ctl pin to v1.1` given two minutes
    earlier, before any pin byte changed): the pin stays at the v1.0
    bytes, and the procedure when the checkout's client differs is the
    session's: `git -C <k3-com260-info> show 9fcc1ed:tools/k3ctl/k3ctl >
    "$K3_RUN_ROOT/k3ctl/k3ctl"`, `sha256sum` of the copy equal to the
    pin's `sha256=` line, `chmod 0755`, and `export K3CTL=<that path>`
    before the first board target (the tools check the copy against the
    pin before every command, as they do any `K3CTL`). For the record,
    v1.1's client diff against v1.0 is confined to the `power` verbs'
    argument handling; `status` and `reset`, the two commands the tools
    issue, are unchanged, and the dongle's firmware was not reflashed
    (`ver=1.0`). Open as a standing procedure until the human directs a
    pin move; a small tool that makes and checks the copy (with a dry-run
    case) would close it.
115. **The platform record has no console-input section.** M7-5's
    `tools/platform-record.py` accepts `probe-console-input`'s two values
    so that a campaign that ran the probe is not refused, and lists the
    probe's run under "Other runs" with its last two lines; the
    characterization's class, pacing, and per-repetition counts are in
    the run's `characterization.txt` (kept in the record) and not in the
    platform record's tables. A section for them, like M1's "Denials on
    K3", is a small later change (release candidate 4's record would use
    it). **Closed 2026-11-04** (M10-3, `ad345b4a`): the section "Console
    input on K3" with eight self-test cases; M7's record renders it.

116. **`k3-run.sh` writes `staged_sha256=yes` as a literal.** The
    attribution verdict `attribution=PASS selected= staged_sha256=
    size_md5= check=` (`tools/k3-run.sh`, the `verdicts=` line) sets
    `staged_sha256=yes` unconditionally; it is true only because the
    script dies earlier (exit 4) when the staging record's SHA-256 is not
    the local image's, so the field is tautological at the point it is
    written rather than computed from the recorded comparison. Found by
    the M9 plan's fact sheet (2026-11-02); the field is to be computed,
    with a dry-run case that fails it, in M9-4. **Closed 2026-11-03**
    (M9-4, `b591466c`): `staged_sha256=` is computed from the recorded
    comparison of the staging record's SHA-256 with the local image's,
    and the dry run's `staged-sha256` case records `staged_sha256=no` and
    stop 4 when they differ.
117. **WP with Z3 `4.16.0` through why3 `1.8.2` is unsound on WP's
    prelude.** M8-5's qualification found Z3 answering `unsat` on WP's
    integer prelude with no goal (the reproducer: seven axioms the
    standard model satisfies, under `build/mvp-verifier/dev/`), so the
    pair proves anything; WP with cvc5 `1.3.4` hangs under WP's default
    memory limit. Recorded as observed, the expectations unchanged; the
    human decided stop 5 as A (the WP arm runs with Alt-Ergo alone and
    cannot meet D-7 item 7). Whether the fault is Z3's, why3's newest
    driver's (why3 recognises none of the provers' versions), or the
    prelude's is not determined here; a report upstream is a later
    choice of the human's. Disposition 2026-11-04: automation files no
    report; the records under `results/20261103-verify*/` and
    `build/mvp-verifier/dev/` are what the human's own report would cite.
    Open as the human's.

118. **A timed-out cvc5 leaves temporary files.** When `cbmc --cvc5` is
    killed at the 600 s budget in the Leaf B suite, about 1 GB of cvc5's
    temporary files stays under `build/mvp/verify/tmp` until the next
    `verify` run clears the directory. A per-job temporary directory
    removed with the job would fix it; M8-6's runner was not changed
    after the run of record. Disposition 2026-11-04: M10's, with the
    re-run of every arm at RC4's tree (S3-C.7), so the runner change and
    its run of record are one commit set. **Closed 2026-11-04** (M10-3,
    `89db0279`): each command gets a temporary directory of its own,
    removed with it, a timeout included; two self-test cases, the first
    failing on the old runner.

119. **Plan erratum: the M9 plan's Q13 citation.** D-7 and Q13 cite
    Amutable's "one public primary document" as "Introducing Amutable
    Foundations", 2026-09-03. Amutable's blog dates "Building New Secure
    Foundations" 2026-09-03 and "Introducing Amutable Foundations"
    2026-10-22; the citation joins the second's title to the first's
    date. `planning/mvp-m9-crosswalk.md` takes the 2026-09-03 post as the
    primary document the plan dates and reads the 2026-10-22 post as the
    same approach stated in full, both by URL and date. Recorded for the
    result packet (`planning/mvp-m9-result-review-summary.md`, section 5,
    and the evidence record's departures); the accepted plan text is not
    edited. **Closed 2026-11-03**: the M9 result's acceptance (`accept
    892b68c8`) records it as erratum 2 in the M9 plan's decision record;
    the accepted plan text stays as written.
120. **The evidence bundle does not yet carry the log's export and the
    references.** `tools/evidence.py` copies a run's `result.json` and
    the checker's records but not the `log.json` the checker writes
    beside it or the image's reference manifest, which the profile (5.3)
    says is copied into every retained record and evidence bundle. To be
    done in M9-6 with a dry-run case, before the clean-checkout gates.
    **Closed 2026-11-03** (M9-6, `74b02017`): the development bundle keeps
    every reference with its pin (`references/<toolchain>/`) and a board
    record those of the images its runs ran (`mvp/references/`), and each
    attempt's or run's export beside its `result.json`
    (`qemu/<stem>.log.json`, `sessions/…/log.json`,
    `rehearsal/…/log.json`, `<run>/log.json`): required where the image's
    reference says it logs (every run class but `pre-measurement`) and the
    verdict is `PASS` or `STOP`, absent for a refused attempt (never
    judged) and a `pre-measurement` image (the checker records
    `export_sha256` null and writes none), each the one its `result.json`
    names by SHA-256 and judged against the reference kept (a rehearsal
    case judged against another is left out as stale). The self-test's
    ten new cases (51 in all) refuse a missing export by its stem, an
    export of another schema, with a header not an object, or not the one
    named, a stray export, and a missing or other reference, and judge a
    board run directory with and without `log.json`; in place of a new
    dry-run case, the dry run's `campaign.record` and
    `input-characterize.record` cases make their records with both,
    unchanged. The profile's 5.3 sentence is unchanged, since the ledger's
    C-51 pins the profile's bytes; the guide states the board record's
    narrower set.
121. **The console tool's second `s` may land at a prompt that reached the
    log late (a code reading, not reproduced).** `tools/k3-console.sh`
    `stop-autoboot` sends `s` at `Autoboot in`, and a second `s` when
    `tools/k3-uboot.py after-stop` sees no prompt within
    `K3_STOP_RETRY_SECONDS` (0.5 s); the tool's comment puts this board's
    prompt within 0.4 s of a taken `s`, so the margin is about 0.1 s (the
    0.5 s counts from the checker's start, a little after the `s`). By
    that reading, if the prompt reaches the serial log after the 0.5 s,
    the second `s` lands at the prompt, which echoes it; `after-stop`,
    then waiting `K3_ECHO_SECONDS` for a prompt with nothing but white
    space before it, reads `=> s` (its stamp removed), which is something
    else, and returns 4; the console tool reports `MISSED` (exit 3) of a
    board that waits at its prompt, and `tools/k3-env.sh` records an
    unplanned boot and waits for its end, which never comes, until stop 1
    after `K3_WAIT_SECONDS`. The tool's comment, that a stray `s` at the
    prompt is caught by the next line's echo check, does not cover this
    path. It is a code reading (2026-11-03, while closing item 93), not
    reproduced, and in no board record. The fake U-Boot now records such
    an `s` as `after-prompt` in its `autoboot.log` (item 93), so a
    dry-run case could name it. The console tool is unchanged by item 93,
    whose scope is the dry run: the board tools are a later debt sweep's,
    by the human's decision. Disposition 2026-11-04: M10's board session,
    with a dry-run case naming the fake's `after-prompt` record written
    with the fix and the fix characterized on the board with the human
    present before it is relied on; not reproduced, so not changed
    blind. **Fixed 2026-11-04** (M10-3, `9a374aed`): `after-stop
    --retried` reads `=> s` at a late prompt as a stopped board (status
    5), the console tool records `late-prompt` and clears the `s` with
    Ctrl-C; the dry run's `late-prompt` case fails on the old tools.
    **Closed 2026-11-05** by M10-6's passing session: across the environment
    records, install, 25-run campaign (49 total resets/banners), restore,
    and preflights there was no late prompt, MISSED, unplanned boot, or
    audit finding. The stopped first session's event was a genuine missed
    stop (prompt followed immediately by NUL bytes and ROM boot output),
    not this shape; the parser correctly refused it and the environment
    was restored before the passing retry.

122. **The release-candidate record tool copies a rehearsal attempt's
    files without its log export.** `tools/rc-record.py` copies each
    U-Boot rehearsal attempt by `evidence.REHEARSAL_FILES`, which M9-6
    extended with `log.json` for the evidence bundle; the record tool
    reads the list but was outside item 120's scope and is M10's, with
    the release-candidate record's other M9 additions (the references
    and the exports in `mvp/results/<date>-rc/`). Found 2026-11-03 by
    the item 120 sub-agent. Disposition 2026-11-04: M10's, confirmed
    (the release-candidate record gains M9's exports and references in
    one change). **Closed 2026-11-04** (M10-3, `d278b409`), with a
    correction of this item's premise: `REHEARSAL_FILES` never named
    `log.json` (M9-6 carried the rehearsal exports into the development
    bundle by `evidence.py`'s own export list), so the gap was the
    release-candidate record's `references/` and its QEMU, session, and
    rehearsal exports; `rc-record.py` now reads, requires, and copies
    them (six refusals in its self-test).

123. **The hashing times in QEMU follow the host's scheduling.** The
    suite's attempts run beside one another, and in the gates' run at
    `dc07f7d3` the Clang `no-inject` image's two launches took 742 ms
    each and its barrier 1,504 ms where every other image of the run took
    36 to 50 ms per launch and 73 to 88 ms at the barrier, and the GCC
    `no-inject`'s second launch 111 ms; the `-m9` fixtures made on an
    idle host show 46 ms per launch. The ticks are recorded per run
    (`BE_MVP_LOG_TICKS`) and judged against nothing (the M9 plan's
    D-10); the hashing precedes the barrier and the budget's arming, so
    no budget includes it. The board's figures, on a 24 MHz clock and a
    real cache, wait for the correlation boot. Open as a note until a
    board figure exists.
124. **The claim ledger's IDs are numbered per lane.** M8's result adds
    C-51 to C-55 and U-16 on `beryllium/mvp-m8` (`a9323ed5`), and M9's
    accepted result adds C-51 to C-53, U-16, and U-17 on
    `beryllium/mvp-m9` (`3b1d6a1f`, `6c2e1f9f`), because
    `tools/claim-ledger.py` requires contiguous IDs on each tree and the
    lanes were parallel. The second line to integrate into the development
    branch renumbers its rows (and re-renders), and the documents that
    cite the IDs keep the numbers as assigned at acceptance with a note;
    the integration record says which. **Closed 2026-11-04** at the
    integration: the development branch was fast-forwarded to the M9
    line (`680b6241`, accepted 2026-11-03) and the M8 line
    (`0d103a38`) merged into it, so M8's rows were renumbered in the
    merged ledger: C-51 to C-55 became **C-54 to C-58** (the barrier and
    the gate, the single writer, the rings and the drain, the denial,
    management) and U-16 became **U-18**; the two cross-references
    inside the ledger (C-06's non-claim and U-13's note, "(C-52)") now
    read "(C-55)"; M9's rows keep their numbers. The M8 evidence record,
    its result packet, the M8 plan's decision record, and this file's M8
    entries keep M8's numbers as assigned at acceptance (read them with
    the mapping above); the ledger is the one source.
125. **Tool limits met by the pilot, candidates for upstream reports.**
    CN (`cbe879c7`): a compound literal (`*out = (struct …){0}`) leaves a
    resource CN never releases (44 goals); `leaf_at`'s pointer liveness
    needs a `focus` a braceless loop cannot hold (5 goals); `&`, `|`, and
    `^` are uninterpreted (`HI_iff`). WP (Frama-C 33.0, why3 1.8.2,
    Alt-Ergo 2.4.3): four true `vsstatus` goals time out at 60 s for want
    of bit-level reasoning (`_rest` needs `&` distributed over `|`); WP
    with Z3 is item 117. Each is recorded in the arms' `goals.txt` and
    `assumptions.txt` under `results/20261103-verify-r1/leaf-a/`. Whether
    to report them upstream, and whether M10's re-proof tries a further
    WP round (Q6 allows four), are the human's choices. Disposition
    2026-11-04: as item 117, no report by automation; the WP round is
    M10's plan's to propose. Open as the human's.

126. **`gen-reference.py --compare` keyed the files by basename.** The
    comparison of the host's and the evaluator's reference directories
    (`make -C mvp reference-check`, run by `check` when
    `build/mvp-evaluator/build/mvp/references/` exists) collected each
    file's name without its toolchain directory and read
    `<host>/<name>`, which does not exist (`FileNotFoundError` at
    `build/mvp/references/anchor-shell.json`), and would have conflated
    `gcc/` and `clang/` files of one name. Found 2026-11-04 at the
    integration of the M8 and M9 lines, the first `check` in a tree
    holding the evaluator's references; the accepted gates run `check`
    before `evaluate` on a clean checkout and never met it. Fixed at
    `0fb76d15`: the files are keyed by their path relative to each root, the
    union of both sides is compared (`files=` counts it), `differs PATH`
    names each path missing on one side or differing, and the self-test
    gains three cases on scratch trees under
    `build/mvp/tmp/reference-self-test` (one name under `gcc/` and
    `clang/` with the trees equal, which raises on the old function; a
    file differing on one side, named by its path; a file on one side
    only, either side), `cases=34` from 31. With a copy of the host's
    references standing in for the evaluator's, the gate printed
    `BE_MVP_LOG_REFERENCE_COMPARE: PASS files=116 differ=0`, and with one
    byte changed and one pin deleted in the copy, `differs
    clang/anchor-shell.json`, `differs gcc/te-poc.sha256`, `FAIL files=116
    differ=2`. C-51's pin of the tool is refreshed at `e1b77cb1` (its note
    names the three cases). **Closed.**
127. **The development branch's stage-1 readings gate and the pilot's
    digests fail by design until M10's re-proof.** After the integration
    of the M8 and M9 lines (2026-11-04), `./be model-check` fails at
    `model/tests/check-concrete-readings.sh` on one of 92 citations
    (`model/proof/Concrete.v:1627`, `mvp/src/mvp-runtime.c:measure`,
    replaced by M9's `measure_log()` and the per-domain launch gate), and
    `./mvp/mvp verify` would stop at its digests suite (stop (i) of the M8
    plan's D-2: `mvp/src/mvp-sbi.c` and `mvp/src/mvp.h` moved). Neither is
    masked: the gate is doing what it is for, and S3-C.7 puts the
    re-reading of stage 1 against the measurement log (the gate is now per
    domain and the global rule holds before `BE_MVP:07`) and the re-run of
    every M8 proof and arm at RC4's tree in M10, before any pin is
    re-derived. The accepted M8 result holds for the bytes its
    `target-digests.txt` and its readings name. Open for M10.
128. **`reference-check` compared the evaluator's references whenever
    their directory existed.** Each reference manifest embeds its source
    commit and tree state (by M9-4's design: the manifest is regenerated
    on every build and pinned beside the image), so the host's and the
    evaluator's references are comparable only when both were made from
    the same source state; `mvp/Makefile`'s target compared them whenever
    `build/mvp-evaluator/build/mvp/references/` existed, so after an
    `evaluate` at one commit every later `check` at another commit, or at
    the same commit with an uncommitted edit (the host's tree then
    `dirty`), failed with every file "differing" in its `source` field
    and its pin. Observed 2026-11-04 at the integration once item 126's
    fix let the compare run: 116 of 116 differing against `6095b179`'s
    evaluator references, the same files byte-identical after `evaluate`
    ran again at the host's commit. Fixed at `3ac541d1`: `compare()` reads
    each side's provenance first and compares only when the two sides
    carry one and the same source state, printing
    `BE_MVP_LOG_REFERENCE_COMPARE: stale (…)` and passing otherwise, as
    the target's `none` does when the directory is absent, and failing on
    a directory of mixed provenance; seven self-test cases (a
    commit apart; a tree state apart; the same source with a real
    difference, which still fails; mixed provenance; an unparsable
    manifest) and the gate exercised with a copy of the host's references
    (`PASS files=116 differ=0`; the copy's commits rewritten, `stale`; one
    rewritten, `FAIL mixed provenance`); and the gate at `331a0e9a` in the
    main checkout, whose evaluator directory held `e1b77cb1`'s references,
    recorded the `stale` line for real before `evaluate` ran again there.
    C-51's pin refreshed at `331a0e9a`; the Makefile's target is unchanged
    (its comment now states the rule). One consequence to know: a
    reference left behind by an image later removed or renamed would make
    its directory mixed provenance, since neither `references` nor
    `evaluate` clears old files; none exists today. **Closed.**
129. **The platform probe: the human's investigation and hardware
    (the human's).** On `Ok, on Q14, and I will investigate, add to the
    todo list, along with acquiring the jtag stuff` (2026-11-04) the
    template `planning/mvp-m9-platform-probe.md` took the vendor's
    answer to its Q14 field (SpacemiT's K3 Secure Boot guide: the BootROM
    verifies the FSBL certificate chain against a ROTPK hash in eFuse bank
    4; opt-in and irreversible; U-Boot has no code to read whether it is
    enabled) and, in its Status, what a probe on this board needs: JTAG is
    on the MMC1 (microSD) pins only, at pinmux function 5, which is a
    debug-configuration change under the template's read-only rule unless
    the running kernel already holds the pins there. The human's items:
    (1) acquire the hardware (the published COM260 setup: an FTDI FT2232H
    Mini Module and a SparkFun microSD Sniffer with press-fit pins and
    jumper wires, VCCIO from the board's 3V3; or the vendor's TF Card
    Debug Expansion Board with a J-Link); (2) investigate the pinmux: a
    the read-only check whether the Fedora kernel's COM260 device tree
    holds MMC1 in the `debug` (JTAG) pinctrl state while no card is
    inserted was made over SSH on the human's `give me the debugfs info
    first` (2026-11-04, 02:41 UTC; the one board command of the day, the
    board idle in Fedora): **it does not** (pads 132 to 137 in
    `mmc1-cfg`, mux 0; `pinctrl-names = "default", "uhs"`; no JTAG
    function in the 13; the template's Status has the values), so the
    decision under the M9 plan's stop 1 remains: a volatile pinmux write
    typed by the human at U-Boot (the four pads' function fields to 5,
    read first), or a device-tree change to the board's Fedora kernel; (3) the probe per the template (IDCODE
    and `dmstatus` by raw JTAG with stock OpenOCD; no halt, no write),
    its record filled by hand. Until then the claim's platform clause
    keeps its "not determined" form (the M10 plan's Q5 fills it from
    whatever record exists at `RC4`). Open; the human's.


## Non-claims

- Every result here is host evidence or emulation, on the laptop `lx2`
  through `804fa95f` and on the workstation `l1` for M0-6, M1, and M2, but
  M0-5's, M1-5's, and M2-6's board campaigns: diagnostic bring-up evidence
  from one COM260, its firmware, and one Fedora kernel. M0-5's first, with
  M0-4's images, stopped at its first scenario run, and its second, with
  the M0-C images, passed its eight runs; M1-5's first, with `9020c4f8`'s
  images, stopped at its `no-inject` run, and its second, with
  `804cd24c`'s, passed its six runs; M2-6's first, with the M2-5 images,
  stopped at its first `anchor` run, and its second, with the same images
  under Plan revision M2-A's checker, passed its six runs. M2-1 to M2-5's
  results are host tests and QEMU only. QEMU's
  harts, IPIs, memory ordering, translation caching, console, and timing
  are not K3's. Nothing here is hardware validation, qualification, or
  formal verification, and Model, Helium, R-series, and B0-B7 claims do
  not transfer. The probe images' values in QEMU are emulation facts, not
  platform facts, and on the board facts for one board, not properties of
  K3 parts in general.
- M4-5's campaign, release candidate 1's, is diagnostic bring-up evidence
  of the same kind, eleven RAM-only `kexec_load` runs at its candidate
  tree's images. Every board run through release candidate 1 was launched
  by Linux kexec from the board's Fedora. M5's board path, a boot from
  system reset, is tested off the board by the dry run on a fake U-Boot
  and, in QEMU, by the U-Boot rehearsal, which is emulation of the boot
  command, the ext4 load, and `booti`, not of the BSP's environment
  storage; and on the board by the M5-6a characterization and release
  candidate 2's session (`mvp/results/20261030-com260-rc2/`): twenty
  boots from system reset on one board, one reported SBI identity, and
  one U-Boot build as its banner reports it, diagnostic bring-up evidence
  of the same kind as the kexec campaigns'. Nothing shows the NOR
  firmware unmodified or the stored environment bytes restored, only the
  environment U-Boot printed at a fresh prompt after the restore, which
  equalled the pre-session record.
- The board runs show the scenarios' outcomes and the probes' facts; they
  make no security claim. M0 runs no denial or fault-injection test between
  the domains. M1 runs one on one declared channel page and three declared
  denied accesses: the writer's and the reader's use of the page, and each
  denied access logged by the monitor, delivered as an access fault, and
  reported by its guest. That is still diagnostic bring-up evidence and no
  security claim. Isolation beyond the declared channel, including every
  access the scenario does not make, remains by construction only: no test
  enumerates the address space, the other causes, or another guest. The
  costs, the denials' service times among them, are recorded only, with no
  performance claim.
- M2's `anchor` runs show the scenario's outcomes in QEMU and, in M2-6's
  second campaign, on one board: four requests
  answered with HMAC values the capture checker recomputes, five declared
  denied accesses logged and injected, fifteen management requests decided
  with the declared results, and the protected domain paused and
  terminated with its measurement unaltered. That is no security claim:
  not confidentiality of the secret, which is a public 32-byte test value
  in `scenarios/anchor/scenario.json` that neither the init nor the
  monitor prints; not availability, since a paused or terminated domain's
  hart parks in HS for the rest of the run; and not microarchitectural
  isolation, since caches, TLBs, and timing between the harts are not
  examined. The measurement's, the requests', and the management calls'
  times are QEMU's and the board's, recorded only, with no performance
  claim; `unchanged=1` proves little at anchor's addresses (open item 53).
- M2-6's second campaign passed its six runs under a checker rule the
  responsible human directed after the board had shown the outcome (Plan
  revision M2-A), with the images the first campaign ran: diagnostic
  bring-up evidence from one COM260, its firmware, and one Fedora kernel.
  The probe answered inside a management wait is an observation of the
  behaviour plan Q14 describes, not a new claim; the claim the probe
  supports is M0's. The boot after that campaign's first reset, which
  reached Fedora's login prompt without an IPv4 address, is an event of
  the board or its network, and nothing about it is a monitor result
  (open item 59).
- The management grants are static. Hart 0 decides each request against
  the sealed manifest's one grant (G0 may pause or terminate G1), which A8
  checked offline against a static rule; nothing is delegated, attenuated,
  transferred, or revoked, and no grant changes at run time. A paused
  domain does not resume (M2 plan, Q4): its state stays in the saved page
  until the run ends or `terminate` follows, and is never restored.
- The measurement is local identity, not attestation: hart 0's SHA-256
  over the protected domain's kernel and DTB as placed, the secret page,
  and the configuration identity, compared with the value the generator
  computed, and printed in the console record at launch (`:06 MEASURED`)
  and at termination (`:12 DOMAIN_TERMINATED`). No key is held, nothing
  is signed or quoted, and no party outside the record can rely on it;
  the plan excludes attestation and a monitor-held key.
- The sealed state's protection inside HS is stated, not closed (security
  model v1's open obligation; the M2 plan's "The measurement"): what
  protects the sealed manifest, the measurement, and the management state
  is I2 (no root maps monitor memory, tested by the host's denied loads),
  hart 0 as their single writer with the image checker's rule that no
  code the domain-hart entry reaches names them, the accepted install
  function's two call sites, and review of the HS C code. Nothing there is
  a proof, and a defect in any HS code path could still write them.
- Neither trigger fires for Instance 3 (the M2 plan's "The triggers for
  Instance 3"): a management call designates its target at run time, but
  its authority is a static grant, and no operation the mappings or the
  grants allow is denied by a further rule. M2 adds no `decide`, type, or
  label to HS; `be_mvp_mgmt_decide` checks the sealed grants and the
  domains' states, not a policy. Nothing here selects a runtime policy
  mechanism, capabilities, or Type Enforcement at run time.
- No formal result: the monitor, the denial decision, the injection, the
  channel and page checks, the SHA-256, and the management decision are
  host-tested and checked in QEMU, and M0's, M1's, and M2's also on one
  board;
  none is proved. The policy checker's A1 to A8 (A7 recorded as vacuous)
  are offline checks of the scenario's labeling, need sets, and manifest
  against its policy, not a proof, and nothing checks the policy itself
  against an intent; the authority report records what was checked, and
  the configuration identity is a name for that configuration, not a
  measurement or an attestation.
- The platform record is a record, not a claim: each value with its source,
  its QEMU values emulation facts, and its serial-log paragraph written by
  hand (open item 40). M1-6's sections set each DENY line beside its guest's
  report and each channel line beside the authority report, and say which
  compared fields agree; they compare those fields only.
- The ring, control-loop, drain-order, channel, and denial host tests
  exercise no fence, cache, CSR, trap, hardware page walk, second hart, or
  IPI; the QEMU runs exercise them only as QEMU
  emulates them, and QEMU's free console cannot show the drain order
  (Plan revision M0-C); the board's runs show it on one board only.
- The tool lock records the tools of the host that last refreshed it,
  `l1` since M0-6. The evaluator runs the same
  packages, by exact NEVRA and RPM digest, in a container from a
  digest-pinned base, on the host's kernel and podman; its 146 identical
  images at `67731e4c` and `804fa95f` on `lx2`, and at the M0-6 content
  on `l1`, and its 184 at M1-4's content on `l1`, show that the builds
  depended on nothing of that host's beyond the
  locked closure and the read-only inputs (the source, the Linux mirror,
  and B1's OpenSBI firmware), not that another toolchain, machine, or
  kernel reproduces them. Its five named removals change only the base
  image (open item 27). One dry-run case, `tree-state`, needs a writable
  source tree and runs on the host only.
- The board tools' dry run runs against `tests/fake-board.py` and, since
  M1-5, the fake dongle `tests/fake-k3ctl.py`, on B7's recorded COM260
  facts and synthetic topology; on the COM260 the tools ran M0-5's,
  M1-5's, and M2-6's two campaigns each, the tools' resets in M1-5 and
  M2-6 went through the pinned `k3ctl` client and its dongle, and M2-6's
  two `k3ctl` resets by hand were made on the responsible human's
  direction (open item 60). The kexec rehearsal is QEMU's emulation of a
  Linux kexec, not K3's.
- M0-2 to M0-4 and Plan revisions M0-A and M0-C select no ring ABI,
  hypercall ABI, scheduler, IPI mechanism, console protocol, or drain
  policy for Beryllium; M1 selects no channel ABI, fault-injection or
  denial-log format, policy language, or runtime policy mechanism (the
  denial is the absent mapping's, and the monitor consults no policy); M2
  selects no management ABI (the extension's EID is in SBI's experimental
  range), measurement or attestation format, or guest driver interface
  (`guest/mgmt/be-mgmt.c` is a test input, never part of the Beryllium
  image); and
  M0-4's
  bundle and board record formats, M0-6's platform record format, and
  M1-1's authority report format are development records, not a release or
  publication format.
- Through release candidate 2 the frozen R0 inventory and the accepted
  R1-R3 validation described the accepted core only (Plan revision
  M0-A.5): the MVP pool, the hart region, the MVP region, the domain
  windows, and the shared pages were MVP-owned extents validated by the
  MVP line's own `ASSERT`s, image checker, and boot-time checks, not by
  R1-R3, and the MVP grew around a frozen synthetic core whose fixture
  roots and pages it built and never used. Since M6-2 (the MVP core
  profile, `planning/mvp-m6-plan.md`) the boot copies, validates, seals,
  and derives the scenario's own inventory and proposal, every MVP extent
  among them, through the ported and widened accepted R1 mechanism, and
  the derived mappings drive the G-stage builder; the fixture roots,
  pages, and guest code are gone. What this does not say: the ported
  copies are the accepted mechanism changed by counted port rules, tested
  by the MVP's host tests on both compilers and not by the accepted R1
  suite, and the Rocq model's proofs are about the abstract model's fixed
  frames, not about this profile (M6-4 records why the model takes no
  instance of it additively).
- A REFUSED QEMU run (open item 13) shows only that `BE_MVP:02` refuses a
  STARTED domain hart; it exercises nothing of the run it replaced.
