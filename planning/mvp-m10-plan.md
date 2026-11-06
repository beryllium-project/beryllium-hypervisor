<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M10 plan: release candidate 4

This plan bounds milestone **M10**, release candidate 4, the last of MVP
1.0's milestones, which the accepted
[Plan revision S3-C](mvp-plan.md#plan-revision-s3-c-the-mvp-ladder-and-mvp-1-0-widened-to-interactive-guests-a-first-verification-plan-and-measurement)
(`27d2e557`) of the [MVP plan](mvp-plan.md) defines in its section
S3-C.6 and authorizes writing once M7's, M8's, and M9's **results** are
accepted (they are: `e1a6395e`, 2026-11-02; `12b0e71b`, 2026-11-04;
`892b68c8`, 2026-11-03). It is proposed on local branch
`beryllium/mvp-m10-plan` from `c59003e7`, the development branch's tip
after the integration of the M8 and M9 lines (`6095b179`), its two
harness fixes, its record (`6ff17c67`), and the beryllium-cheri sidebar
import, on the human's `re-refresh then go` (2026-11-04). It is written
on the orchestrating model under the standing split (S3-C's D22);
nothing in it is implementation.

## Decision record

The responsible human accepted this plan at exact commit
`600b78c5198c7462ca76fdb30113f3770fdf5fa7` (parent `c59003e7`, on branch
`beryllium/mvp-m10-plan`) on 2026-11-04 (18:44 in the human's time zone)
by the instruction `accept 600b78c5`, the reply to the
[review packet](mvp-m10-plan-review-summary.md)'s request, given through
the session's form and repeated in the next message; the abbreviation
resolves uniquely. Q1 to Q15 apply at their defaults. The same message
said `proceed with development`, so M10-2 and M10-3 start at once on
branch `beryllium/mvp-m10` from this acceptance record; the human's
`sidebar was imported` confirmed the beryllium-cheri guest log's
integration on that repository's side (its `main` at `5f45573`).

- **Scope:** acceptance covers exactly the plan text at that commit.
- **Authorization:** M10-2 to M10-7 on branch `beryllium/mvp-m10` from the
  acceptance-record commit; the re-write of `mvp/verify/target-digests.txt`
  at `X4` (Q3); board commands only after the human confirms the board
  free, with the human present at the install and the restore; no push,
  merge, tag, publication, snapshot refresh, release-path step beyond the
  first, or kexec use.
- **The target digests (Q3):** this acceptance is the responsible human's
  direction the M8 plan requires for `digests.py --write --target X4`.
- **The probe (Q5):** item 129 of `mvp/README.md` holds the human's own
  items (the hardware, the pinmux decision, the probe); the claim's
  platform clause is filled at `RC4` from whatever record exists.
- **Erratum 1 (D-3, Q2; found by M10-3, 2026-11-04):** the campaign's
  composition the plan states (four probes, twelve scenario runs, six
  negatives, three sessions) totals 25 runs, not the 26 the text says;
  25 is implemented (`make -C mvp print-k3-plan`: `groups=19 runs=25
  sessions=3 staged=19`). The plan text is unedited.
- **The M10 result is responsible-human accepted at exact commit
  `d70a8535474a690920ff152e7b38a25c589adba9`** (`RC4`, parent `f3f8c8d8`; candidate tree
  `X4` `a6eaa88501b1d08b9e83c734d692c82376117e77`) as of 2026-11-05 (instruction
  `accept d70a8535`); `planning/mvp-m10-result-review-summary.md` is its
  review and acceptance record and `planning/mvp-m10-evidence.md` the
  evidence. Plan errata 1 and 2, the licence-manifest readings, and the
  evidence record's departures stand; release-path step 1 holds for RC4.
  No fast-forward, push, tag, publication, snapshot refresh, release-path
  step 2, archive or successor is directed.
- **Erratum 2 (stop 7, the M8 bridge lane; 2026-11-04):** M10-2's
  re-transcription (the litmus sequence excerpts re-extracted at the moved
  monitors, +377 lines net 0) and M10-3's item 118 (+60) put the bridge
  lane, counted as the M8 plan counts it (added lines), at 12,248 of its
  12,000 (11,811 at M8's `X`); nothing was cut. The responsible human
  re-set the lane's soft limit to **13,000** (form answer
  `bridge_lane=reset-13000`), with headroom for the re-extraction at `X4`.

## Status

```text
m10_status=accepted
m10_plan_target=600b78c5198c7462ca76fdb30113f3770fdf5fa7
m10_plan_parent=c59003e7
m10_acceptance_instruction=accept-600b78c5
m10_acceptance_date=2026-11-04
m10_acceptance_record=mvp-m10-plan-review-summary.md
m10_open_questions_answered=Q1-Q15-defaults
m10_authorization=M10-2..M10-7-on-beryllium/mvp-m10-from-the-acceptance-record;2026-11-04;target-digests-re-write-at-X4-directed;board-only-after-confirmation-human-present;no-push-no-merge-no-release-step
m10_implementation_branch=beryllium/mvp-m10
m10_implementation_start=2026-11-04;proceed-with-development;M10-2-and-M10-3-in-parallel
m10_erratum_1=D-3-Q2-campaign-is-25-runs-not-26;found-by-M10-3;plan-text-unedited
m10_wp3=complete;merged-f3d56369;pins-3953a01c;1411-of-2500-lines
m10_wp2=complete;merged-575eafab;pins-c64853a3;stage-1-26-statements-byte-identical;verify-verdict-for-verdict-M8;records-20261104-verify-rc4-base
m10_x4=a6eaa88501b1d08b9e83c734d692c82376117e77;first-candidate-7a5c7062-superseded-after-rc-record-found-missing-busybox-and-musl-libc.a-in-the-bundle;fix-a6eaa885
m10_x4_gates=eight-PASS-2026-11-05-13:22-17:32-UTC;clean-standalone-checkout;verify-wall-13254;verdict-for-verdict-M10-2-and-M8;rc-record-20261105-rc4-files-641;verify-record-files-33
m10_erratum_2=stop-7-bridge-lane-12248-of-12000;re-set-to-13000-by-the-human-2026-11-04;model-lane-8655-of-12000
m10_plan_branch=beryllium/mvp-m10-plan
m10_plan_base=c59003e7;the-development-tip-after-the-M8-M9-integration-6095b179-its-fixes-331a0e9a-its-record-6ff17c67-and-the-cheri-sidebar-import
m10_governing_text=mvp-plan.md-S3-C.6;S3-C.7-order-re-proof-rule-board-time-release-path-and-the-M10-pre-authorization;S3-C.8-D19-D21-D22;S3-A.1-board-policy-with-item-8;M8-plan-D-2-re-proof;M9-plan-D-9-D-10
m10_preconditions=M7-result-accepted-e1a6395e;M8-result-accepted-12b0e71b-inconclusive;M9-result-accepted-892b68c8;both-lines-integrated-6095b179
m10_work_packages=M10-1..M10-7
m10_open_questions=Q1-Q15-defaults
m10_soft_limit_lines=2500;Rocq-and-the-arms'-annotations-reported-in-M8's-lanes
m10_board=complete;X4-a6eaa885;25-runs-19-groups-3-sessions-PASS;record-20261105-com260-rc4-files-314;human-present-install-and-restore;environment-restored;preflights-equal;probe-not-performed
m10_claim_change=RC4's-metadata-only-S3-C.7;M9's-D-9-slots-filled-from-recorded-outcomes;anything-else-stop-(d)
m10_authorization_if_accepted=M10-2..M10-7-on-beryllium/mvp-m10-from-the-acceptance-record;the-target-digests-re-written-at-X4;no-release-path-step-after-the-first;no-merge-no-push
m10_result=accepted-d70a8535474a690920ff152e7b38a25c589adba9;parent-f3f8c8d8;X4-a6eaa88501b1d08b9e83c734d692c82376117e77;board-record-f3f8c8d8;evidence-mvp-m10-evidence.md;record-mvp-m10-result-review-summary.md;2026-11-05;instruction-accept-d70a8535
m10_result_soft_limits=M10-1429-of-2500;model-8655-of-12000;bridge-12248-of-13000;checker-monitor-2.349
m10_result_stops=stop-7-bridge-reset-13000;stop-6-first-board-session-restore-fix-restart;retry-PASS
```

## Purpose

Produce MVP 1.0's candidate for the release path's steps 2 to 7: one
exact commit `RC4`, over a candidate tree `X4`, at which every gate
passes from a clean checkout, including the ones M8 and M9 added and the
one the integration left red by design (stage 1's readings gate, item
127), the board campaign runs at `X4`'s images from system reset with
the interactive sessions typed under item 8 and the measurement log
verified in every run, the release surfaces name release candidate 4
through the ledger's release object, and the guest software's licences
are stated per component with their corresponding source. Release
candidates 1 to 3 stay accepted history. The release path's step 1 moves
to `RC4` when the human accepts it; steps 2 to 7 each need their own
instruction (S3-A.3, S3-B.3, D21) and are not part of M10.

## Inputs

| Input | Exact identity | Used for |
| --- | --- | --- |
| MVP plan with Plan revisions S3-A, S3-B, S3-C | `93967fba`; `0d134bbc`, `f8b77ac9`, `27d2e557` | M10's definition (S3-C.6), the order and the re-proof rule (S3-C.7), D19 to D22, the board policy (S3-A.1 with item 8), the release path |
| Release candidate 3 | `RC3` `89ef04e9` over `X3` `ebc49a88`; `planning/mvp-m6-plan.md`, `-evidence.md`, `-result-review-summary.md`; `mvp/results/20261031-rc3/`, `20261031-com260-rc3/` | The release-candidate shape this plan repeats: the gates from a clean checkout, `rc-record`, the campaign of 20 runs, the records, the packet |
| M7's result | `e1a6395e` (`planning/mvp-m7-evidence.md`); the typed characterization `mvp/results/20261102-com260-m7/` | The shell images, the scripted sessions, the typist, item 8's gate in the console tool, the probe `probe-console-input` |
| M8's result | `12b0e71b` (`planning/mvp-m8-evidence.md`); the specification `93a8d136` (SHA-256 `aeb75682…`) with errata S-1 to S-5; `mvp/verify/target-digests.txt` (target `6fbcc3d1`); `mvp/results/20261103-verify-r1/` | Stage 1 (26 theorems), the verifier and its arms, the re-proof rule (M8 plan D-2; S3-C.7), the ledger rows C-54 to C-58 and U-18 as renumbered |
| M9's result | `892b68c8` (`planning/mvp-m9-evidence.md`); `mvp/docs/log-profile.md` v1; `planning/mvp-m9-platform-probe.md` | The log, the references, the checker's log module, D-9's claim slots and their fixed forms, D-10's correlation boot, the human's probe |
| The integration | `6095b179`; fixes `0fb76d15`, `3ac541d1` (pins `e1b77cb1`, `331a0e9a`); record `6ff17c67` | The merged tree; items 126 to 128; the by-design red gates this plan closes |
| The claim ledger | `mvp/docs/claim-ledger.json` at the base: `claims=58 boundary=18 review_items=3`; `release` = RC3 | The release object M10 moves; the rows M10 refreshes |
| Open items | `mvp/README.md` 114, 115, 118, 121, 122, 127 (this plan's); 106, 117, 125 (not this plan's) | Scope |
| The board tools | `tools/k3-*.sh`, `k3-console.sh` with `guest-type`, `k3-input-characterize.sh`, `k3ctl.sha256` (pin unchanged, item 114) | The campaign |

## Facts the design rests on (read-only findings, 2026-11-04)

1. **The by-design red gates.** At the integrated tree `./be model-check`
   fails at `model/tests/check-concrete-readings.sh`: one of 92
   citations, `model/proof/Concrete.v:1627` reads
   `mvp/src/mvp-runtime.c:measure`, which M9-3 replaced by
   `measure_log()` and the per-domain launch gate. `./mvp/mvp verify`'s
   `digests` suite would stop at the M8 plan's stop (i): two of the
   pilot's thirteen target digests moved (`mvp/src/mvp-sbi.c`, one line,
   the class name `"log"` in a table; `mvp/src/mvp.h`, M9's additions).
   Every other gate passes at `331a0e9a` (item 127). Stage 1's theorems
   are about hart 0's publication, the barrier and the gate, the single
   writer, the rings and the drain, the denial decision, and management;
   M9's log is written by hart 0 before the barrier and judged by the
   checker; the gate stage 1 models (`gate_verdict`, one measured domain
   against an expected digest) is now per domain, on each domain's launch
   register, under the global rule "every comparison succeeds and the log
   closes before `BE_MVP:07`, or no domain hart starts" (M9 plan D-1).
2. **M8's outcome is inconclusive** (D-7: no arm met items 1 to 7 on
   Leaf A); the claim is unchanged; the ledger's stage-1 rows are C-54 to
   C-58 and U-18 after the integration's renumbering (item 124). The
   verifier ran 3 h 44 min at M8's `X` (`wall_seconds=13480`): WP about
   four hours of that in Alt-Ergo's timeouts, the ring's CBMC about two.
   The arms' annotations cite the specification's hash and the leaves'
   digests; `digests.py --write --target COMMIT` re-writes
   `target-digests.txt` and the M8 plan says it is "re-written only on
   the responsible human's direction".
3. **M10 changes no monitor source.** Its code is tools and tests: the
   campaign's session groups, the console tool's second `s` (item 121),
   the verifier runner's temporary directory (item 118), `rc-record.py`'s
   exports and references (item 122), the platform record's console-input
   section (item 115), and the licence manifest. So the leaves' digests at
   `X4` equal the base's, and the re-proof's results at the base hold at
   `X4` if the `digests` suite passes there, which it is run to show.
4. **The board campaign's plan today** (`mvp/tools.mk`'s `K3_PLAN`): the
   four GCC probe images once each (`probe-platform`,
   `probe-vmid-distinct`, `probe-vmid-shared`, `probe-console-input`),
   each scenario's GCC image three times and its Clang image once
   (`two-guests`, `te-poc`, `anchor`), and five negatives with GCC
   (`payload`; `reader-write`, `no-inject`; `wrong-measurement`,
   `no-grant-check`): 21 runs. Release candidate 3's campaign ran 20 (no
   `probe-console-input` then) in 26 minutes with 39 `k3ctl` resets. The
   shell images (`two-guests-shell`, `te-poc-shell`, `anchor-shell`;
   `MVP_SHELL_SCENARIOS`) have scripted sessions under `sessions/` with a
   run nonce, a typist, and the checker's session rules (M7-4); on the
   board only `two-guests-shell` has run, once, typed by
   `k3-input-characterize.sh` under item 8 (M7-6). `self-report-flip`
   (M9's negative on `anchor`) is a QEMU variant and no board variant.
   The staging tool stages 16 images; the partition is Beryllium's own
   (M5).
5. **Measurement on the board.** `check-capture.py`'s log module runs on
   every capture whose expectation has a log section, board captures
   included: it rebuilds the page from the `BE_MVP:19` lines, replays the
   registers, recomputes every digest from the build's inputs, compares
   with the image's reference, and reads the loader's `md5sum` line from
   the one autoboot block (debt sweep 4's rule). So a board campaign at
   `X4`'s images judges the log in every run; M9's one `anchor`
   correlation boot (D-10, Q10) is subsumed by the campaign's four
   `anchor` runs. The human's read-only platform probe (M9 plan D-6; the
   template) is the human's own and has not been performed; the claim's
   platform clause reads "not determined as of 2026-11-03; no probe was
   performed".
6. **The release surfaces** are `mvp/docs/claim.md` (its header and
   evidence paragraph), `mvp/docs/guide.md` (its first sentence, the
   records table, its closing section), `mvp/docs/ai-assistance.md`, the
   rendered `claim-ledger.md`, `mvp/tools/snapshot-readme.md` (the fields
   `@RELEASE_NAME@`/`@RELEASE_COMMIT@` filled by `snapshot.sh`), the
   root `README.md`'s release-candidate sentences, and
   `planning/mvp-rc-walkthrough.md` (written at RC1 and kept current
   through RC3's boot story). `claim-ledger check`'s "release surfaces"
   check requires `claim.md`, `guide.md`, and `ai-assistance.md` to name
   the ledger's current candidate and, once named, the release commit's
   first eight hex digits (debt sweep 3, row H).
7. **Licences today.** `LICENSES/` holds GPL-3.0-only, GPL-2.0-only (the
   guest module `mvp/guest/mgmt/be-mgmt.c`), and MIT (musl's and
   BusyBox's build inputs, M7-2); `mvp/tools/check-licenses.py` requires a
   text under `LICENSES/` and a `COPYING` line for every identifier a
   tracked file's header names. The guest software the MVP builds and
   stages, Linux `v7.2` (GPL-2.0-only with the syscall note), BusyBox
   1.36.1 (GPL-2.0-only), musl 1.2.6 (MIT), and the `nolibc` init and
   module of this repository, is pinned in `mvp/tools/guest-pins.py` and
   `mvp/guest/pins.txt` by tag, commit, or tarball SHA-256; OpenSBI (B1's
   build, BSD-2-Clause) and U-Boot (the board's resident firmware and B3's
   pinned build, GPL-2.0-or-later) are the firmware below HS. No guest
   image is distributed: the review snapshot holds sources and pins, the
   release-candidate record holds digests, and the board records hold
   captures; the kernel `Image` and the initramfs are built from the pins.
8. **The counts the records compare**: `two-guests` `exits=157
   records=138 wakes=2`; `te-poc` `exits=163`/`167 records=146 wakes=2`;
   `anchor` `exits=248 refused=1 records=174 wakes=16`, each as the RC2
   and RC3 records hold them; M7 added the input accounting (`:16` to
   `:18`) and M9 the log lines (`:19`, `:20`) and `:06 LAUNCH`, so RC4's
   declared lines are M9's references and M7's session rules, and its
   counts are compared with M7's record (the last board run at a tree
   with the input path) and RC3's for what is older.

## Design

### D-1 What release candidate 4 is

`X4` is one commit on `beryllium/mvp-m10` at which, from a clean
standalone checkout, these pass (the "eight gates"): `./mvp/mvp tool-lock
check`; `./mvp/mvp check`; `./mvp/mvp evaluate` (every image identical to
the host's); `./mvp/mvp uboot-rehearsal` (its cases as declared);
`./mvp/mvp kernel-repro` (the kernel, BusyBox, and musl outputs
`pins=match`); `./be model-check` (the Model 0.2 proofs, the policy and
binding proofs, the input ring, and **stage 1 green at `X4`**: readings,
layout, 26 theorems); `./be evaluate` (the model's rootless evaluator);
and `./mvp/mvp verify` (every suite: `sequences`, `digests` at `X4`'s
digests, `token-equal`, `qualify`, `litmus`, `wp-arm`, `cn-arm`,
`cbmc-leaf-a`, `cbmc-ring`). `rc-record` writes `mvp/results/<date>-rc4/`
from those runs, with M9's exports and references (item 122). `RC4` is
the commit over `X4` that adds the two records, the ledger rows that
cite them, the evidence record, and nothing that the gates read; `check`
is run at `RC4` as at `RC3`. Release candidate 4 is MVP 1.0's candidate
for the release path's steps 2 to 7 (D21).

### D-2 The re-proof at RC4's tree (S3-C.7; M8 plan D-2)

Every M8 proof and arm runs again at `X4`'s exact tree **before any pin
is re-derived**: the ledger's rows C-54 to C-58 and U-18 cite the re-run
at `X4`, never the accepted M8 result's records, and the M8 records stay
as accepted history.

- **Stage 1 re-read.** The target commit of `model/proof/Concrete*.v`
  moves from `6fbcc3d1` to `X4`: `ConcreteLayout.v` regenerated from
  `mvp-layout.h` (the generator's `--check` passes), every `(* reads:
  … *)` citation made at `X4` (the one that names `measure` is re-made
  against `measure_log` and the launch gate; any other symbol M7 or M9
  renamed likewise), and the abstraction changed **only where the code it
  reads changed**: the gate becomes per domain on the launch register
  (`cfg_gate` per domain; the global rule as a hypothesis of the barrier
  theorem, stated where the current `gate_verdict` is), with M9's log page
  outside stage 1's word set because no hart but hart 0 writes it and
  every write precedes the barrier (stated as a reading, not proved). All
  26 theorems are re-proved **with their statements unchanged**; a
  statement that cannot stand is stop 4. The lineage table of
  `planning/mvp-m8-evidence.md` is re-made for `X4` in M10's evidence
  record (the accepted table unedited). `make -C model proof` is the
  gate; `model/tests/run-concrete.sh`'s PASS line reports the count.
- **The digests.** `mvp/verify/tools/digests.py --write --target X4`
  re-writes `target-digests.txt`: the two moved lines (`mvp-sbi.c`,
  `mvp.h`) and the target line; the specification pin stays `93a8d136`
  / `aeb75682…` (the specification is not revised: S-1 to S-5 stay
  errata in the M8 plan's decision record). **This plan's acceptance is
  the human's direction** the M8 plan requires for that re-write (Q3).
- **The arms.** The CN copy of `mvp-sbi.c` takes the one-line change
  (`token-equal` requires it); the ACSL, CN, and CBMC annotations are
  re-transcribed only where a cited digest or line moved, each file's
  header re-citing `X4`; the litmus sequences are re-extracted from
  `X4`'s monitors (`sequences` compares them); `qualify`, `wp-arm`,
  `cn-arm`, `cbmc-leaf-a`, and `cbmc-ring` run with the accepted M8
  settings (WP four rounds at most, Q6 of the M8 plan; CN; CBMC unwind 4
  with `sat` and cvc5; the ring at its bound). The verifier image is the
  accepted one (`ce7ca11cb755-b71721530f48-36eaf6d2362b`) unless its
  closure or sources changed, in which case the image is rebuilt from the
  pinned closure and the change recorded.
- **What the re-run may show.** The expected outcome is the accepted
  M8 result's, verdict for verdict (the leaves' bytes differ by one string
  in a table Leaf A does not read). A verdict that differs is recorded as
  the re-run's, with the difference explained from the changed bytes if
  it can be; a difference the bytes do not explain is stop 5. The
  outcome's reading does not change: M8's result is inconclusive, M10
  re-establishes the same evidence at `X4` and makes no new claim; the
  pre-authorized M8 sentence is not added (no positive result).
- **Cost.** About four to five hours of verifier time per run, run once
  at the base tree in parallel with M10-3 (the leaves do not change), and
  once more at `X4` from the clean checkout as the gate (the suites'
  results must match the first run's, line for line; a mismatch is stop
  5). Two runs, not more, unless a stop decides otherwise.

### D-3 The board campaign (S3-A.1 with item 8)

One session at `X4`'s images, under the S3-A board policy as RC3 ran it
(preflight before; staging; two environment records at fresh prompts;
the install with the human present; the runs, each from system reset by
its own `k3ctl` reset with the saved `bootcmd` loading the selected
image; the restore with the human present and its fresh-prompt record
equal to the first; the preflight after; `board-evidence`), with these
additions:

- **The sessions.** The three shell images (`two-guests-shell`,
  `te-poc-shell`, `anchor-shell`, GCC) each run once with their scripted
  session typed by the console tool under item 8 (the session file hashed
  into the run record, each line typed only after the arming and focus
  lines, re-gated on a line-start hart-0 line, no reset during a session,
  a banner during a session aborting it: stop (b)), and judged by the
  checker's session rules as in QEMU. The campaign tool gains a per-group
  session (`NAME:RUNS:TOOLCHAIN:IMAGE:FLAT:EXPECT:REPORT[:VARIANT][:SESSION]`,
  M7-5's characterization driver generalized), with a dry-run case per
  rule on the fake board.
- **Measurement in every run.** Every run's capture is judged by the
  checker with its log module (fact 5): the `:19`/`:20` lines rebuilt,
  replayed, and compared with `X4`'s references for the image; the
  loader's `md5sum` line read as the loader observation. The `anchor`
  runs are M9's correlation boot (D-10) four times over; D-9's board
  clause takes its "run" form, and the ledger's board column names the
  exact images and the runs.
- **The negatives.** RC3's five, plus `self-report-flip` with GCC (M9's
  negative: the mutated image's log must be refused by the checker on the
  board as in QEMU; its declared verdict is FAIL at the record the
  reference does not match).
- **The probes.** The four GCC probe images once each; `probe-console-input`
  runs with nothing typed, as the campaign's rule says; its
  characterization is M7's record and is not repeated (Q8 of the M6 plan
  pattern).
- **Counts.** 4 probes + 12 scenario runs + 6 negatives + 3 sessions =
  **26 runs** (Q2). Each run's expectation is `X4`'s; the counts are
  compared with M7's and RC3's records as fact 8 says; a count that
  differs and the captures do not explain is stop 6.
- **Item 121** (the console tool's second `s` at a late prompt): the fix
  lands in M10-3 with its dry-run case (the fake's `after-prompt` record
  named), and the campaign's 26 autoboot stops are its characterization
  on the board; a `MISSED` of a board that waits at its prompt is stop 6
  (the fix did not hold) and the session resumes under the tool's
  `K3_CAMPAIGN_SKIP` rule after the human's decision.
- **The human's probe** (M9 plan D-6, Q5 below): the human may perform
  the read-only platform probe in the same session or at another time;
  if its record exists before `RC4`, M10-4 fills the claim's platform
  clause with D-9's fixed form for the outcome class; if not, the clause
  reads "not determined as of <RC4's date>; no probe was performed".
- **Gates.** No board command before the human confirms the board free;
  the human present at the install and the restore; `k3ctl` or human
  resets only; the k3ctl pin unchanged (item 114's copy procedure if the
  checkout's client differs); kexec never; every keystroke recorded; the
  records private where M5's Q8 says (the `printenv` texts).

### D-4 The release surfaces (the M10 pre-authorization, S3-C.7)

The ledger's `release` object becomes `name` = `MVP 1.0 release
candidate 4`, `candidate_tree_commit` = `X4`, `release_candidate_commit`
= `RC4` (filled at `RC4`'s creation, as RC3's was; `null` between `X4`
and `RC4` with the surfaces' "not yet fixed" wording the check allows).
From it: `claim.md`'s header and evidence paragraph (the records
`mvp/results/<date>-rc4/` and `<date>-com260-rc4/`; the board-records
table gains RC4's row), `guide.md`'s first sentence, records table, and
closing section, `ai-assistance.md`, the root `README.md`'s sentences,
the snapshot README template's fields, and `planning/mvp-rc-walkthrough.md`
(a section for what changed since RC3: the shell and the focus
sequence, the log lines and the reference, the verifier; the boot story
unchanged). The claim's **text** changes only as S3-C.7's M10 clause
allows (RC4's metadata) and as M9's D-9 forms fill their slots from
recorded outcomes (the board clause's "run" form; the platform clause per
Q5); every forbidden phrasing stays forbidden; any other change is stop
(d). The ledger's rows: C-54 to C-58 and U-18 cite the re-run at `X4`;
C-51 to C-53 gain the board column; U-16 and U-17 are restated if the
campaign's outcomes bear on them; the rows RC3's packet refreshed per
candidate (the records' rows) are refreshed per RC4; `claim-ledger
render` and `check` pass with the "release surfaces" check against RC4.

### D-5 The licence manifest (S3-C.6)

A per-component manifest, `mvp/docs/licence-manifest.md`, generated by
a tool (`mvp/tools/licence-manifest.py`) from the pins, never edited by
hand: for Linux `v7.2`, BusyBox 1.36.1, musl 1.2.6, the `nolibc` init and
the management module of this repository, OpenSBI (B1's pinned build),
and U-Boot (B3's pinned build, and the board's resident firmware named as
the human's), each row the component, its version or commit, its licence
identifier, where its notice text is (`LICENSES/` or the component's own
`COPYING` in the pinned source), the corresponding-source pointer (the
upstream URL and tag or commit, or the tarball's name and SHA-256, as the
pins hold them), and whether the MVP distributes a binary of it (today:
none; the snapshot and the records hold sources, pins, digests, and
captures). The tool's `--check` is part of `check`: every component the
guest build touches (`guest-pins.py`'s list) has a row, every identifier
named has its text under `LICENSES/` (BSD-2-Clause and GPL-2.0-or-later
are added for OpenSBI and U-Boot if the check requires the texts; Q7),
and the manifest is byte-identical to a fresh generation; a self-test
with a planted component without a row fails it. The manifest states the
rule for a later distribution: a distributed guest image carries the
manifest and the notices and offers the corresponding source by these
pointers.

### D-6 The small debts this plan closes (items 115, 118, 121, 122)

- **115.** `tools/platform-record.py` gains a "Console input on K3"
  section: the characterization's class, pacing, and per-repetition counts
  from the run's `characterization.txt`, and the sessions' counts from the
  campaign; a self-test case per field.
- **118.** The Leaf B runner gives each CBMC job a temporary directory
  of its own, removed with the job, so a killed cvc5 leaves nothing; the
  runner's self-test covers the removal on a timeout.
- **121.** As D-3 says: the console tool's `stop-autoboot` treats an `s`
  echoed at a prompt that reached the log after `K3_STOP_RETRY_SECONDS`
  as a stopped board (the prompt is there), not as `MISSED`, and records
  the late prompt; a dry-run case on the fake's `after-prompt` record.
- **122.** `rc-record.py` copies each rehearsal attempt's `log.json` and
  the bundle's `references/` into the release-candidate record, and its
  self-test requires them.

Items 106 (Fedora 44's end of life), 117 and 125 (upstream reports) are
not this plan's; item 114 is decided (the pin stays).

### D-7 What does not change

No monitor source (`mvp/src/`), no guest input, no scenario, no
expectation other than the references `X4`'s build regenerates, no
accepted R0-R7 or B0-B7 byte, no accepted document's text (ports and
this plan's own revision excepted), no claim text beyond D-4, no model
theorem statement, no M8 specification text, no tool lock role unless a
tool's version moves (then the lock refresh is recorded as M3-2's was),
no kexec, no push.

## Work packages

| WP | Delivers | Exit |
| --- | --- | --- |
| M10-1 | This plan; the review packet | accepted |
| M10-2 | The re-proof at the base tree: stage 1 re-read and re-proved at the target `X4`-to-be (the leaves and headers unchanged by M10-3), `target-digests.txt` re-written, the arms' annotations re-transcribed, `./mvp/mvp verify` all suites, `./be model-check` green; the lineage table | `verify` PASS with every verdict recorded; `model-check` PASS; a differing verdict explained or stop 5 |
| M10-3 | The tools: the campaign's session groups and their dry-run cases; items 115, 118, 121, 122 with their tests; the licence manifest tool, its check, and the manifest; `./mvp/mvp check` | `check` PASS; the line count reported |
| M10-4 | The release surfaces (D-4): the ledger's release object, the rows, the claim's header and evidence paragraph, the guide, the disclosure, the root README, the snapshot template, the walkthrough's section; `claim-ledger render` and `check` | `claim-ledger check` PASS with the release surfaces check |
| M10-5 | `X4` fixed; the eight gates from a clean standalone checkout, `verify` included (its verdicts equal to M10-2's); `rc-record` with M9's exports and references | records verify; `verify` line for line |
| M10-6 | The board campaign at `X4`'s images (D-3): 26 runs; the human present at the install and the restore; `board-evidence` | 26 of 26 as declared; the restore rule satisfied; the log judged in every run |
| M10-7 | The evidence record (`planning/mvp-m10-evidence.md`: the gates, the re-proof, the campaign, the departures, the lanes, the items, the claim boundary); the ledger rows; `RC4` over `X4`; `check` at `RC4`; the packet | packet presented |

Order: M10-2 and M10-3 in parallel (disjoint files; M10-3 does not touch
`mvp/src/`, `model/`, or `mvp/verify/` but item 118's runner, which
M10-2's `cbmc-ring` run takes before or after it, the result being the
same), then M10-4, M10-5, M10-6, M10-7. Coding and proofs run on
`claude-opus-5.5` sub-agents in worktrees as M8's and M9's did; this
model plans, orchestrates, reviews each merge line by line, runs the
gates and the campaign, and writes the records and the packet (D22).

## Soft limits (re-evaluation stops)

**Counting rule:** added lines by `git diff --numstat` from this plan's
acceptance record in C, Python, shell, Make, and the wrapper, tests
included; generated files (the manifest, fixtures, references), JSON,
Markdown, the model's Rocq, and the arms' annotations excluded and
reported separately. **Limit: 2,500.** Estimate: the campaign's session
groups and dry-run cases 200 to 400; item 121 and its case 80 to 150;
item 118 and its case 40 to 80; item 122 and its cases 80 to 150; item
115 and its cases 150 to 250; the licence manifest tool, check, and
self-test 250 to 400; `rc-record`'s and `evidence.py`'s RC4 fields 50 to
100: 850 to 1,530. The Rocq changes are counted in M8's model lane
(12,000 cumulative; 8,544 at M8's `X`) and the arms' annotations in its
bridge lane (12,000; 11,811 at `X`), each reported against its limit;
exceeding one is stop 7, a re-evaluation of the limit, never a cut.
Documents unlimited. The checker-to-monitor ratio is reported (2.294 at
M9), not limited.

## Stop conditions (each returns to the human)

1. Any need to change an accepted R0-R7 or B0-B7 byte, an accepted
   document's text (ports and this plan's own revision excepted), or the
   M8 specification's text.
2. Any need to change the claim's text beyond D-4 (S3-C's stop (d)), or
   the required limit.
3. Any need to change a monitor source, a guest input, a scenario, or an
   expectation other than a regenerated reference.
4. A stage-1 theorem that cannot be re-proved at `X4` with its statement
   unchanged, or a reading that cannot be re-made (the code it read is
   gone), or a change to the layout generator's output other than its
   target.
5. A verifier verdict at the base or at `X4` that differs from the
   accepted M8 result's and that the changed bytes do not explain, or a
   difference between the base run's and `X4`'s suites (M8 plan stop
   (i) covers the digests).
6. A board run whose verdict differs from the declared one; a count that
   differs and the captures do not explain; a session aborted by a banner
   (S3-C's stop (b)); a `MISSED` of a board at its prompt (item 121's fix
   did not hold); an unexplained reset or banner; a hand reset.
7. A soft limit exceeded (checkpoint after M10-3 and after M10-4; the
   lanes reported after M10-2).
8. The board unavailable or in the other project's use (wait; no board
   command before the human's confirmation), or the human not present at
   the install or the restore.
9. Any push, merge, tag, publication, snapshot refresh, or release-path
   step beyond the first (S3-C's stop 7 for a refresh).
10. Any kexec launch (the standing rule).
11. A privacy finding in a record the redaction rule (Plan revision M4-A)
    does not cover.
12. A component the guest build touches with no licence text available
    under its identifier, or a corresponding-source pointer that cannot be
    stated from the pins.
13. An `evaluate` or `verify` image that cannot be built from the pinned
    closure or sources (a served-RPM or source change; the human decides
    the lock or closure move, as M0-B and M3-2 did).

## Open questions and defaults

| ID | Question | Default |
| --- | --- | --- |
| Q1 | The base | This plan's acceptance record, on the development branch's line (`c59003e7` or its descendant at acceptance) |
| Q2 | The campaign's composition | 26 runs: the four GCC probes once each; each scenario's GCC image three times and its Clang image once; six GCC negatives (RC3's five and `self-report-flip`); the three shell images once each with their sessions typed under item 8 |
| Q3 | The target digests' re-write | Directed by this plan's acceptance: `digests.py --write --target X4`; the specification pin unchanged |
| Q4 | Stage 1's re-reading | Re-targeted to `X4`; the abstraction changed only where the code it reads changed (the per-domain gate; the log page outside the word set, as a reading); every theorem's statement unchanged; a change of statement is stop 4 |
| Q5 | The human's platform probe | The human's own, performed or not; if its record exists before `RC4`, the claim's platform clause takes D-9's form for the outcome class and the record is cited; else the clause reads "not determined as of <RC4's date>; no probe was performed" |
| Q6 | The arms' settings | The accepted M8 settings (WP four rounds at most with Alt-Ergo; CN with Z3 and cvc5; CBMC unwind 4 with `sat` and cvc5; the ring at its bound); no new round of any arm (item 125's choice is the human's and outside M10) |
| Q7 | Licence texts | BSD-2-Clause and GPL-2.0-or-later added under `LICENSES/` with `COPYING` lines, since the manifest names OpenSBI and U-Boot; the check requires a text for every identifier the manifest names |
| Q8 | The verifier image | The accepted image unless the closure or sources changed; a rebuild from the pinned closure is recorded |
| Q9 | Naming | `X4` the candidate tree, `RC4` the release-candidate commit; the records `mvp/results/<date>-rc4/` and `<date>-com260-rc4/` |
| Q10 | A steering review of this plan by another model | None (the SOP); run one if the human asks, recorded in the packet's review history as the M9 plan's was |
| Q11 | The sessions on the board | The three scenarios' sessions as M7-4 fixed them, each once with GCC; typed by the tool under item 8; the Clang shell images not run (the board column names GCC) |
| Q12 | The walkthrough | One section for what changed since RC3 (the shell and the focus sequence, the log lines and the reference, the verifier), the boot story unchanged; M4's and M5's sections stay theirs |
| Q13 | The M8 records | Accepted history, unedited; the re-run's records under `mvp/results/<date>-verify-rc4/`, cited by the ledger's rows |
| Q14 | Soft limit | 2,500 counted lines; the M8 lanes' cumulative limits for the Rocq and the annotations |
| Q15 | The snapshot | Not refreshed by M10 (a refresh is the human's publication act under stop 7 and D21, from an accepted commit) |

## What acceptance authorizes

M10-2 to M10-7 on branch `beryllium/mvp-m10` from the acceptance-record
commit, with Q1 to Q15 at their defaults unless answered, under the stop
conditions above; the re-write of `mvp/verify/target-digests.txt` at
`X4` (Q3); board commands only after the human confirms the board free,
with the human present at the install and the restore; no push, merge,
tag, publication, snapshot refresh, release-path step beyond the first,
or kexec use. `RC4`'s acceptance, when proposed, is the release path's
step 1 for release candidate 4 and nothing more.

m10_result_acceptance=release-path-step-1-holds-for-RC4;plan-errata-1-2-licence-readings-and-evidence-departures-accepted;no-ff-no-push-no-step-2-no-successor
