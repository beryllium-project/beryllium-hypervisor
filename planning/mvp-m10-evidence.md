<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M10 evidence record

This record holds the evidence of M10, release candidate 4, on branch
`beryllium/mvp-m10`, made under the accepted
[M10 plan](mvp-m10-plan.md) (exact commit `600b78c5`, accepted
2026-11-04; acceptance record `b5842520`) and the accepted
[Plan revision S3-C](mvp-plan.md#plan-revision-s3-c-the-mvp-ladder-and-mvp-1-0-widened-to-interactive-guests-a-first-verification-plan-and-measurement)
(`27d2e557`). It records what was run, when, on which commit, and what it
printed; it makes no claim beyond those lines.

The candidate tree `X4` is exact commit
`a6eaa88501b1d08b9e83c734d692c82376117e77`. No monitor source, guest
input, scenario, expectation, M8 specification, theorem statement, or
accepted R0-R7 or B0-B7 byte follows it. The release-candidate commit
`RC4` is the commit that adds this record's final form with the board
record and the ledger rows that cite them, over `X4`; the review packet
names it.

## Outcome first

M10's required result holds at `X4`:

- all eight gates passed from a clean standalone checkout;
- stage 1 was re-read at the integrated monitor and all 26 theorem
  statements were re-proved unchanged;
- every M8 verifier suite was run again at `X4`, and every verdict and
  count equals M10-2's base run and the accepted M8 result's;
- the release-candidate record verifies (641 files);
- one RAM-only board session from **system reset** ran 25 of 25 declared
  runs at `X4`'s images, including three typed shell sessions and M9's
  measurement log in every applicable run; every capture passed, every
  negative failed as declared, the environment was restored, and the
  preflight after equalled the one before; and
- the board record verifies (314 files).

This is diagnostic bring-up and evaluation evidence on one COM260, its
resident firmware, and one Fedora kernel. It is not hardware validation,
qualification, certification, attestation, or whole-monitor formal
verification. The M8 outcome remains **inconclusive** under its plan's
decision rule: no monitor function has a C-level contract proof.

## Exact line

| Boundary | Exact identity |
| --- | --- |
| Plan | `planning/mvp-m10-plan.md` at `600b78c5`; accepted 2026-11-04, Q1 to Q15 at their defaults |
| Acceptance record / implementation base | `b5842520` |
| Re-proof at the base | stage 1 `23d09b95`; digests `52e816cb`; verify record `dd2d6da7`; merged `575eafab`; ledger pins `c64853a3` |
| Tools | M10-3 through `8c110901`; merged `f3d56369`; image-check pins `3953a01c`; record `058ec3fe` |
| Release surfaces | `9ba30105` |
| Candidate tree `X4` | `a6eaa88501b1d08b9e83c734d692c82376117e77` |
| Gates and verifier record | `mvp/results/20261105-rc4/` (641 files), `mvp/results/20261105-verify-rc4/` (33 files), added at `6d55bc42` |
| Board record | `mvp/results/20261105-com260-rc4/` (314 files), source commit `X4` |
| Release candidate `RC4` | the commit that adds the board record, this evidence record, and the final ledger updates over `X4`; named by the packet |

The first post-surface candidate, `7a5c7062`, passed all eight gates, but
`rc-record` exposed one integration defect: M7's kernel-repro correctly
carried 23 outputs, including standalone `busybox` and `musl-libc.a`,
while the development bundle's guest manifest carried 21. The fix
`a6eaa885` adds those outputs to the bundle and both focused self-tests
(`evidence.py`: 51/51; `rc-record.py`: 28 mutations), so `7a5c7062` is
superseded and every gate was rerun at `X4`.

## M10-2: the re-proof

### Stage 1

M9 replaced the one measured-domain `measure()` with `measure_log()` and
a launch gate per domain. M10-2 re-read stage 1 at the integrated tree:
of the accepted 92 citations, 89 symbols remain as at the M8 target,
`be_mvp_runtime_main` calls `measure_log()` where it called `measure()`,
and `measure` is gone. The 99 citations now name:

- `be_mvp_log_constants`, `be_mvp_log`, `be_mvp_log_registers`, and
  `measure_log` for the log and its constants;
- `log_launch` and `be_mvp_log_gate` for the per-domain launch gate; and
- `be_mvp_log_append` and `be_mvp_log_close` for M9's global rule.

The abstraction changes only there: the expected register and gate are
per domain, the configuration records whether the log closes, and
hart 0's prepare step is guarded by the global rule (both gates pass and
the log closes, or no domain hart starts). The log page is outside stage
1's word set as a reading: hart 0 alone writes it before the barrier.
Two lemmas, `global_rule_gates` and `global_rule_false_no_start`, make
the existing theorem `gate_false_no_start` a short corollary.

All **26 theorem statements are byte-identical** to M8's `X`
(`f1813841`), checked mechanically by the orchestrating session; the
other 25 proofs are byte-identical, and no theorem statement was
weakened. The gate printed:

```text
Beryllium MVP concrete model (stage 1): PASS theorems=26 assumptions_closed=26 citations=99 layout_sha256=c50da8ad3b06
```

`./be model-check` passed (including the model differential,
`comparisons=241`). The accepted lineage classification remains:
Model 0.2's 24 claims: 9 re-proved, 15 inapplicable; M3's 22 claims:
13 inherited, one strengthened (`binding_h3_single_writer` to
`single_writer_carried`), 8 inapplicable. The only re-proof whose target
now rests on re-read code is `failed_validation_no_publication` to
`gate_false_no_start`; the rest map as M8's evidence record states.

### Digests, litmus and arms

`mvp/verify/target-digests.txt` was re-written at target `c43ba773`
(whose proved bytes equal `X4`'s): only the target line, `mvp-sbi.c`
(M9's class-name string outside Leaf A), and `mvp.h` moved; the
specification pin stays Revision 1 `93a8d136`, SHA-256 `aeb75682…`.
The CN copy needs no byte change: M9's one line is outside the five
functions, and token equality passes (`tokens=686`, range 201-324).

The monitors moved, so 49 of 55 litmus excerpts were re-extracted and
30 symbols' digests moved; L1 to L5 changed only in comments that cite
the new addresses and digests, while their initial states, programs and
conditions are byte-identical. The WP arm's SPVP note moved by one line.
No solver, bound, round, or arm setting changed.

The base-tree `verify` (2026-11-05 03:03 to 06:49 UTC,
`wall_seconds=13554`) and `X4`'s gate run (13:51 to 17:32 UTC,
`wall_seconds=13254`) each pass in the accepted image
`localhost/beryllium-mvp-verifier:ce7ca11cb755-b71721530f48-36eaf6d2362b`.
Every verdict and count equals the accepted M8 result's:

| Suite | Result at `X4` |
| --- | --- |
| sequences | PASS, `elfs=2 symbols=55 lines=206` |
| digests | PASS, `files=13` |
| token equality | self-test PASS 28; copy PASS `tokens=686` |
| qualification | PASS, `arms=9 qualified=6` |
| litmus | PASS, `premises=5 never=5` |
| WP | OPEN, `goals=134 proved=130 rounds=1`, Alt-Ergo, mutants 24/killed 18 |
| CN | OPEN, `goals=55 proved=5`, Z3+cvc5, mutants 24/killed 1/unobservable 1 |
| CBMC Leaf A | SUCCESSFUL bounded model check, `properties=336 failed=0`, sat+cvc5, unwind 4, mutants killed 22/unobservable 1/contract finding 1 |
| CBMC ring | OPEN bounded model check, `properties=14931 checked=13547 open=1384`, capacities 512/4096, sat+cvc5, mutants killed 22/unobservable 1/harness finding 1 |

`mvp/results/20261104-verify-rc4-base/` (33 files) is the base run;
`mvp/results/20261105-verify-rc4/` (33 files) is the `X4` run. Raw logs
and mutant sources are not retained; the room finding's bounded excerpt
says what it omits.

## M10-3: tools and licence manifest

M10-3 changes no monitor source. It delivers:

- the campaign's optional ninth `SESSION` field, the three GCC shell
  groups, `self-report-flip`, session-to-expectation SHA-256 binding,
  the pre-board `K3_GUEST_TYPING=human-authorized` gate, and the typist's
  own stop before the banner audit;
- item 121's late-prompt handling (`after-stop --retried` recognizes a
  quiet prompt echoing the retry `s`, records it and clears it with
  Ctrl-C; the dry-run case fails on the old tool);
- item 118's per-CBMC-job temporary directory removed in a `finally`,
  timeout included;
- item 122's release-candidate references and QEMU/session/rehearsal
  log exports, required and copied by `rc-record.py`;
- item 115's “Console input on K3” platform-record section; and
- `mvp/docs/licence-manifest.md`, generated from the pins: Linux,
  nolibc, this repository's init/device trees and module, BusyBox, musl,
  OpenSBI and U-Boot, each with its licence, notice and corresponding
  source; no binary distributed.

A latent image-check defect found by the session groups is fixed:
`dtb_plan()` inserted `rdinit=/init-shell` a second time into
`te-poc-shell`'s and `anchor-shell`'s own expectations, which would have
refused their first board run; it inserts it only when absent. C-41 and
C-52's pins moved to that fix.

The tool work adds 1,429 counted lines of the 2,500 limit (Python 972,
shell 393, Make 60, wrapper 4). Excluded and reported: records/fixtures
123,413; licence texts 906; Markdown 578; Rocq 111; JSON 86; the litmus
text/assembly and `COPYING`. The checker-to-monitor ratio is **2.349**
(monitor 16,417 lines; checking code 38,563 by M9's set with M10's
licence-manifest checker added), reported and not limited.

The licence manifest's two readings for review with the result:

- U-Boot's row says `GPL-2.0-or-later`, the project-level identifier its
  `Licenses/README` states, and notes that the whole can be redistributed
  under version 2 while most files also allow a later version; and
- nolibc is a row because it is compiled into the init, `LGPL-2.1 OR
  MIT`, so `LICENSES/LGPL-2.1` is a third new text beyond Q7's two.

## M10-4: release surfaces

At `X4`, the ledger's release object names “MVP 1.0 release candidate
4” and `X4`; the release-candidate commit remains `null` (a commit
cannot hold its own SHA), as RC3 did until the later acceptance record.
The claim's text changes only in the metadata S3-C.7 pre-authorized:
the header names release candidate 4, moves RC3 to accepted history, and
the evidence paragraph names M10's board session and evidence record.
M9's fixed slots are filled from the retained outcomes: the platform
probe is not performed as of 2026-11-05; the M9 board-correlation
qualifier is removed because the `anchor` runs at `X4`'s images exist.

The guide names RC4, describes the 25-run campaign, adds sections on the
verifier and the licence manifest, and the walkthrough adds “What changed
since release candidate 3” (the shell/focus sequence, log, verifier,
campaign and manifest). The AI disclosure covers M7 to M10, the M9 plan's
`gpt-6-astra` steering review, and the three S3-C design reviews by their
tools. `claim-ledger check`'s release-surfaces and phrasing checks pass.

## M10-5: the eight gates and release-candidate record

All eight gates passed at exact `X4` from a clean standalone checkout
on the development workstation:

| Gate | Time (UTC, 2026-11-05) | Result |
| --- | --- | --- |
| tool lock | 13:22 | PASS, roles 32, closure 259 |
| `check` | 13:22-13:33 | `BE_MVP_CHECK: PASS` |
| `evaluate` | 13:33-13:44 | PASS; every one of 339 images byte-identical |
| U-Boot rehearsal | 13:44-13:46 | PASS, cases 7, attempts 12, refused 5 |
| kernel-repro | 13:46-13:47 | PASS, outputs 23 identical (kernel, BusyBox, musl included) |
| `model-check` | 13:47-13:49 | PASS, stage 1 included |
| model rootless evaluator | 13:49-13:51 | PASS |
| `verify` | 13:51-17:32 | PASS, `wall_seconds=13254`, the table above |

`mvp/results/20261105-rc4/` (641 files) holds the host and evaluator
bundles (M9's references and log exports included), model evidence and
logs, rehearsal, kernel-repro, and gate records; `rc-record --verify`
passes. The first all-green run at `7a5c7062` is retained under
`build/mvp/m10-gates/attempt-1-7a5c7062/` as diagnosis only, never
evidence of `X4`.

## M10-6: the COM260 campaign

### First attempt (stopped, restored, not evidence)

The first attended session's environment install recorded a real missed
autoboot stop: the prompt was followed immediately by NUL bytes and ROM
boot output, so `after-stop` correctly returned its fail-closed status 4
and sent no retry `s`. This was not item 121's late-prompt shape. The
human chose `restore-fix-restart`; the environment was restored, the
preflights passed, and no campaign image ran. The private local session
is preserved under `build/mvp/k3-sessions/20261105-com260-rc4-stopped/`;
it is not committed or evidence. The human then directed `try again`.

### Passing session

The passing session ran at `X4`'s images on 2026-11-05, 22:20 to 22:42
UTC. The human confirmed `board free; present now`, was present at the
install and the restore, and did not type during the tools' session.
The preflight before passed; 19 SHA-256-bound images were staged; the two
fresh-prompt environment records were equal and `V` empty; the install
changed only the declared `be_` variables and `bootcmd` and made one
attended `saveenv`.

The campaign result is:

```text
BE_MVP_K3_CAMPAIGN: PASS runs=25 groups=19 sessions=3
```

The plan's D-3/Q2 “26” is erratum 1: its own composition is 4 probes +
12 scenario runs + 6 negatives + 3 sessions = **25**.

| Group | Runs | Result and stable counts |
| --- | --- | --- |
| `probe-platform`, `probe-vmid-distinct`, `probe-vmid-shared`, `probe-console-input` | GCC once each | PASS; all tested HSM entries enabled, HS/VS IPI 100/100, zero stale reads in both 10,000-iteration orderings, expected load/store/fetch fault reports; VMID and console probes no finding |
| `two-guests` | GCC ×3, Clang ×1 | PASS; each domain exits 157 (`sbi=156`, `refused=0`, 65 lines); records 138, wakes 2; log records/lines/bytes 13/16/4273 |
| `te-poc` | GCC ×3, Clang ×1 | PASS; representative GCC domains exit 162/165 (`refused=0`, 67/68 lines); records 146, wakes 2; the declared denials and channel result pass; log 14/17/4557 |
| `anchor` | GCC ×3, Clang ×1 | PASS; protected domain paused and terminated at exits 132, host exits 247 with `refused=1`, 83 lines; records 174, wakes 16; the measurement is unchanged; log 15/18/4818 |
| `payload`, `reader-write`, `no-inject`, `wrong-measurement`, `no-grant-check`, `self-report-flip` | GCC once each | each fails as declared; self-report-flip runs to completion and the checker reports exactly the one expected offline self-report difference |
| `two-guests-shell` | GCC once | PASS; typist 16 steps/130 keys; domains exit 342/367; records 134, wakes 532 |
| `te-poc-shell` | GCC once | PASS; typist 16 steps/130 keys; domains exit 516/518; records 143, wakes 805; the declared denials pass |
| `anchor-shell` | GCC once | PASS; typist 16 steps/130 keys; protected domain paused/terminated at exits 187, host exits 642; records 148, wakes 601; the declared denials and management requests pass |

Every appropriate run's log page and registers were rebuilt, replayed,
recomputed from the build's inputs and compared with its post-link
reference; every loader attribution, selected-image digest, size check,
capture check and banner audit passed. The three session files were the
ones their expectations name by SHA-256; each typist passed; the focus,
delivered/dropped input and denial accounting passed; no reset or banner
occurred while a session typed. There was no late prompt, missed stop,
unplanned boot, hand reset, unexplained banner or recovery action.

The original environment was restored with one attended `saveenv`;
record 3 equals record 1 under the tool's `V` rule; Fedora autobooted.
The preflight after passed with the same kernel and every region,
firmware, partition, environment and pinned k3ctl check equal to the one
before. The session recorded 49 resets and corresponding banners, no
finding. The board is restored, free, and on Fedora.

`mvp/results/20261105-com260-rc4/` (314 files) is the retained record:
25 run records, the log exports and references, the “Console input on K3”
and “The measurement log” sections, the preflight pair, staging, the
environment state and audit, the hand-written notes, and
`MANIFEST.sha256`; `evidence.py --verify` and the ledger privacy check
pass. This is diagnostic board evidence from one board, not hardware
validation.

## Soft limits and stops

| Limit | Result |
| --- | --- |
| M10 counted lines | 1,429 of 2,500 (Python 972, shell 393, Make 60, wrapper 4) |
| M8 model lane | 8,655 of 12,000 (111 added lines at M10-2) |
| M8 bridge lane | 12,248 of the human-re-set 13,000 (erratum 2; 437 added, 392 deleted, mostly the litmus excerpts' re-transcription) |
| checker-to-monitor | 2.349 (38,563 / 16,417), reported and not limited |

Stops returned to the human:

1. **Stop 7, bridge lane.** At 12,248 of 12,000 by the accepted
   added-lines rule; the human chose `reset-13000`; nothing was cut.
2. **Stop 6, first board attempt.** One genuine missed autoboot stop;
   the human chose `restore-fix-restart`, the environment was restored,
   diagnosis found the fail-closed parser correct, and the human directed
   `try again`. The passing session is a new root.

No other stop condition applied. M10-3's item 121 fix is characterized
by the passing session's 49 resets: no late prompt, missed stop or
unplanned boot. Items 115, 118, 121 and 122 are closed. Item 129 (the
human's JTAG hardware, pinmux decision and platform probe), item 106
(Fedora 44's post-EOL repository move), and items 117/125 (the human's
upstream reports) stay open.

## Departures and readings for review

1. **Plan erratum 1:** 25 runs, not 26 (arithmetic above).
2. **Plan erratum 2:** bridge lane re-set to 13,000.
3. **Target digest:** written at `c43ba773`, whose proved `mvp/src` and
   headers equal `X4`'s; the `X4` gate's digest suite passes. Re-writing
   the target line again to a later commit that changes no proved byte
   would add no evidence.
4. **Release commit field:** `RC4` leaves the ledger's
   `release_candidate_commit` null, as RC3 did (a commit cannot hold its
   own SHA); the later acceptance record fills it if the human accepts
   `RC4`.
5. **Item 122's premise:** `REHEARSAL_FILES` never included `log.json`;
   M9-6 generated the rehearsal export through `evidence.py`'s own list.
   M10's fix makes `rc-record.py` require and copy the references and the
   QEMU, session and rehearsal exports.
6. **Licence manifest:** U-Boot's project row reads
   `GPL-2.0-or-later`, with its `Licenses/README` caveat; nolibc gets its
   own `LGPL-2.1 OR MIT` row and third new licence text.
7. **Item 115 tests:** eight grouped self-test cases assert every field
   of the console-input section, rather than one case per field.
8. **M10-5 integration fix:** the evidence bundle's guest manifest gains
   standalone `busybox` and `musl-libc.a`; no image byte or verdict
   changes, but every gate was rerun at the new `X4`.

## Claim boundary

Release candidate 4 combines the accepted M7, M8 and M9 results at one
exact tree and one board campaign:

- console input is evidenced by host tests, adversarial tests, the
  semantic checker, QEMU emulation, M7's typed characterization, and
  RC4's three diagnostic board sessions;
- the measurement log and per-domain launch gate are evidenced by host
  tests, adversarial tests, the semantic checker, QEMU emulation, and
  RC4's diagnostic board runs; M9's board-correlation qualifier is
  removed, and the ledger names the exact images and record;
- stage 1 is a proof about the abstract model under sequentially
  consistent interleaving and the five stated ordering premises, whose
  compiled sequences pass the RVWMO litmus tests at `X4`; it is not a
  C refinement; and
- M8's WP and CN arms stay OPEN, Leaf A's CBMC is a bounded model check,
  and the ring's bounded model check is OPEN; the required limit's
  implementation sentence remains unnarrowed.

The platform probe was not performed as of 2026-11-05. SpacemiT's
vendor documentation says the BootROM verifies the FSBL certificate
chain against a per-device ROTPK hash in eFuse when Secure Boot is
enabled, and that enablement is irreversible; it does not say this
board's state. No MVP 1.0 claim depends on ROM authentication. The log
is a local identity, never attestation: it has no key, nonce, freshness,
counter or root of trust; SPL, OpenSBI and U-Boot are unmeasured; the
monitor's digest of itself is an offline self-report that gates nothing.

Release candidate 4, if accepted, satisfies release-path step 1. Steps 2
to 7 (the human's selection of what migrates, the clean public
repository, a tag, re-running the gates there, publication, the archive)
each need their own explicit instruction. No automation selects,
publishes, tags, archives, pushes, or starts MVP 2.0 from this result.
