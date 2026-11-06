<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M9 evidence record

This record holds the evidence of M9, "Measurement", on branch
`beryllium/mvp-m9`, made under the accepted [M9 plan](mvp-m9-plan.md)
(`4f4a8f76`, its second candidate, accepted 2026-11-03 with M9-2 to M9-6
authorized at the acceptance record `bc80b620`, the M9 base) and the
accepted
[Plan revision S3-C](mvp-plan.md#plan-revision-s3-c-the-mvp-ladder-and-mvp-1-0-widened-to-interactive-guests-a-first-verification-plan-and-measurement)
(`27d2e557`, its section S3-C.5 and S3-C.7), with the MVP plan's D20
(`measure first, then attest`; IMA never used). It records what was run,
when, on which commit, and what it printed; it makes no claim beyond those
lines. The gates ran on exact commit `dc07f7d302e01fb622b53e268f2182c991b0f3e6` (`X`; tree clean), and the
commits after it hold only this record, the README's records, and the
packet: no monitor, guest, test, tool, scenario, or model byte follows
`X`. The result commit `R` adds this record and the README's records over
`X`; the packet, committed after it, names it.

## What M9 adds, by work package

Each package's files and counts are in `mvp/README.md`'s M9 entries; this
is the index.

| Package | Exact commits | Delivers |
| --- | --- | --- |
| Part 1 Revision 3 (M9-2, first) | `4bc079db`, **accepted** 2026-11-03 (`accept 4bc079db`; record `f4f9cbfb`) | Security model v1's measurement log: the log page and the registers as instances of Part 1's `measurement` asset, hart 0's by phase; the offline evidence TCB beside the running TCB; the loader observation and the human's probe as trusted inputs and dated assumptions; the self-report's limit; I19 and I20; six TCB rows; 252 lines appended, the accepted text byte for byte |
| M9-2 the documents | `ca48456f` (merged); record `0e9ed66a` | `mvp/docs/log-profile.md`, version 1 (1,176 lines: the encoding offset by offset, the enumerations, the per-image contract, the line grammar, the JSON profile and the reference manifest, the CEL 1.1 mapping with the unmapped fields and the no-interoperability statement, the allowlist, the ten choices made where the plan left them open); `mvp/results/20261030-uboot-help/` (item 104's premise: `help.txt` SHA-256 `ca42cbc5…`, 117 commands, `crc32` and `md5sum` present, `hash`, `sha1sum`, `sha256sum`, `tpm`, `tpm2`, and `verify` absent; CRLF kept); `planning/mvp-m9-platform-probe.md` (the probe template: the four outcome classes, the fifth "not performed", Q14's words) |
| M9-3 the monitor | `b92b9308`, `fac813f1`, `6cbdcaf1`, `9d20ba35`, `f620ee7b`, `3957665b`, `d6aa0f82` (merged `39bb5ab2`) | `src/mvp-log.c`/`.h` (the page, append, close, extend, gate, the console grants' serialization, the lines); `measure_log()` in `src/mvp-runtime.c` (R2, R3, R4, the gate per domain, the close, the block and both `:20` lines; `BE_MVP_CLASS_LOG`); the generator's expected records, launch registers, count, lines, and run class per image, and the 172-byte log constants; the image checker's rules with a mutation each; `self-report-flip` (`tools/flip-canary.py`); `guest-pins.py --check`'s IMA refusal (D-5); `tests/log-test.c` (47 scenarios, 874 assertions); the M9 fixtures and `tests/fixtures/pre-m9/` |
| M9-3 found and fixed | `75459737` (merged `8f6660ab`) | The probe's IPI count race (`src/mvp-probe.c`: each phase counts in its own word) and `tests/probe-test.c` (65 scenarios, 779 assertions; 17 of 64 schedules fail on the old code); the four GCC probe fixtures made again. The plan's stop 2 protocol; the human decided `fix now` (2026-11-03) |
| M9-4 the references and the checker | `849c484b`, `b591466c`, `79881e37`, `c56022e6`, `d8aa0339` (merged `1edc3652`) | `tools/gen-reference.py` (one post-link reference per image and toolchain; 29 images per toolchain `constants=linked expectation=same`; a 31-case self-test); `tests/log_module.py` (rebuild, replay, recompute, compare, order, prefix, allowlist, export; 105 module cases); `tests/check-capture.py` on M9's fixtures with each image's reference and the build, M7's against `pre-m9/` (self-test `cases=300`, `mutations=459` rejected); the platform record's measurement-log sections; `k3-run.sh`'s `staged_sha256` computed (item 116); the dry run serving M9's captures |
| M9-5 the words | `f5e7925e`, `3b1d6a1f`, `5ec2c609`, `6c2e1f9f`, `eef77b50`, `a8636087` | The ledger's pins C-10, C-40, C-41, C-48 refreshed; the claim's sentences as D-9 fixes them with the slots filled; C-51 to C-53, U-16, U-17; U-10, U-12, U-14, C-16, C-40 restated; the guide's measurement section; `planning/mvp-m9-crosswalk.md` (D-7); the README's records and items |
| M9-6 | ``b7e059b5`, `7ed829c1`` (item 93, merged ``dc07f7d3``), ``74b02017`, `dc6bef1f`` (item 120, merged ``1d91b829`; the profile's 5.3 sentence `45ce8e8c`, C-51's pin `cbbdcb17``); this record; the packet | The dry run's autoboot window made the board's; the evidence bundle carrying the log exports and the references; the gates from the clean tree; the costs; the probe's state; the correlation boot's wait |

## The claim, the limit, and the phrasings

`mvp/docs/claim.md` changed exactly as the plan's D-9 fixes (`3b1d6a1f`):
the blockquote gained the one measurement sentence after M7's console
sentence, and the required limit's "The measurement is a local identity,
not attestation." was replaced by D-9's text with its three slots filled
from the recorded outcomes, each from its fixed pair of forms:

| Slot | Outcome | Form used |
| --- | --- | --- |
| `<self-report clause>` | R2 kept (Q4; the five ranges reproduce byte for byte across clean rebuilds, both toolchains) | "the monitor's digest of its own text and read-only data is a self-report, compared offline and gating nothing" |
| `<platform clause>` | no probe performed | "The board's lifecycle and debug state were not determined as of 2026-11-03; no probe was performed." |
| `<board clause>` | the correlation boot not run | "The log and launch-gate evidence is from QEMU; the M9 board correlation has not run." |

No other word of the claim changed (stop 4 was not reached); the words
"chain", "lowest stage", "measured identity", "measured boot", "attested",
and "secure boot" do not appear in it. The forbidden-phrasing check passes
over every release surface at `X` (`claim-ledger.py check`,
`BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=53 boundary=17`). The ledger's
rows C-51 (the log and the registers), C-52 (the launch gate per domain,
citing I19 and I20), and C-53 (the self-report) carry the methods host
unit test, adversarial test, semantic checker, and emulation and no board
method, as D-9 says until a board run at M9's images; U-16 is the boundary
row for R1 and the platform observation; U-17 is D-5's third check.

## The log, as built, against the plan

| Plan | As built | Where seen |
| --- | --- | --- |
| D-1: 4 KiB page, 128-byte header, 96-byte records, capacity 41, registers beside the page, ≤ 15 records per image | as stated; the page 4 KiB aligned in hart 0's MVP-region BSS; the constants 172 bytes in `.mvp.rodata` | `src/mvp-log.h`; `check-image.py`'s rules; `log-test.c` |
| D-2: the records per image class R1 to R4 | v1 13 records, v2 14, v3 15, a probe 9 (8, 9, 10, 4 without R2); R1 beside the log, never in it | `log-profile.md` 3.1; the fixtures' `count=` |
| D-3: the post-link reference per image | `build/mvp/references/<toolchain>/<image>.json`, 29 per toolchain, regenerated every build, never committed (Q6) | `gen-reference.py`; `records/references.txt` |
| D-4: rebuild, replay, compare, export | the checker's log module; `log.json` beside `result.json`; `(unprotected)` on the replayed line | `log_module.py`; `BE_MVP_LOG*` lines |
| D-5: IMA never used, three checks | `guest-pins.py` refuses `CONFIG_IMA*`/`CONFIG_EVM*` (six planted, refused); the allowlist refuses any object, content type, schema, or algorithm outside the profile's; U-17 | `6cbdcaf1`; `log-profile.md` 7; the ledger |
| D-6: the loader observation and the platform observation beside the log | U-Boot's MD5 held as attribution (C-10); the probe template committed, not performed; Q14's disposition in the template | U-16; `mvp-m9-platform-probe.md` |
| D-7: the crosswalk | `planning/mvp-m9-crosswalk.md` | `eef77b50` |
| D-8: Part 1 Revision 3 | accepted `4bc079db` | `f4f9cbfb` |
| D-9: the claim's sentences | as above | `3b1d6a1f` |
| D-10: costs measured, not assumed | hashing about 46 ms per domain for the 2 MB kernel in QEMU (`:06 LAUNCH ticks=0x70793`, `0x6f67c`), `0xe3b44` ticks at the barrier for `te-poc`; the log's text 4,556 bytes of a `te-poc` run's console; the hashing and the rendering precede the barrier and the budget's arming | `BE_MVP_LOG_TICKS`; `BE_MVP_LOG: … bytes=`; the costs table below |
| D-11: the accepted scenarios' counts within the checker's rule | `records` exact (138, 146, 174), `wakes` and `exits` within the rule as the checker judges them (`exits` the sum over the accepted exits; the per-domain `exits` of the M9 captures differ from M7's by the `dbcn_read` polls' timing, 157/160, 164/167, 125/239, each accepted by the unchanged rule); the SBI version stays 5 (6 with management) | the fixtures; `capture-check` |
| D-12: what M9 does not do | no eFuse, lifecycle, or NOR write; no attestation, key, nonce, counter, vTPM, or SBI measurement extension; no measurement of SPL, OpenSBI, U-Boot, the board's device tree, or any file inside a guest; no model change; no push, merge, tag, publication, snapshot refresh, or kexec use; no board command | this record |

## Departures from the plan's letter, recorded in the session

Each recorded in `mvp/README.md`'s M9 entries and open items; none
changes what the claim says beyond the fixed sentences.

| Plan text | As done | Where |
| --- | --- | --- |
| Soft limit 6,000 (checkpoints after M9-3 and M9-4) | Stop 8 fired at the checkpoint after M9-3 (about 7,900 counted with M9-4's branch in view); the human re-set the limit to 10,000 (erratum 1, 2026-11-03); 9,240 at `a8636087`, `9,812` at `X` | the plan's decision record; `mvp/README.md` |
| Stop 2 (a code defect found by M9's work) | the probe's IPI count race in `mvp-probe.c` (fixture code, not the monitor), 1 in 25 Clang `probe-platform` runs; the human decided `fix now`; fixed with a host test that fails on the old code | `75459737`; item in the M9-3 entry |
| D-4's `self-report-flip` "one variant" | made `anchor`'s rather than `two-guests`' (the longest, v3, log carries it); both scenarios' images changed by the move (the scenario digest in the log constants) and their M9 fixtures were made again | `3957665b`, `d6aa0f82` |
| Q7: S3-C.5's "CEL-JSON" | read as the Beryllium log profile derived from CEL 1.1, not a conforming CEL; recorded for acceptance with this result | `log-profile.md` 1 and 6 |
| The profile's open choices | ten choices made in M9-2 where the plan left them open (the enumerations' numbers; the console grants' serialization; the gate on a domain's last launch record; the close's count rule; three rendering paths; the `magic=` field and `0x` prefixes; the barrier line's saturated hashing total; the lines' places and `FAIL log` without `DETAIL`; stream 0 compared through its records only; the JSON names and bounds), presented for review with this result | `log-profile.md` 1 |
| Q13: "Introducing Amutable Foundations", 2026-09-03 | the title is the 2026-10-22 post's, the date the 2026-09-03 post's ("Building New Secure Foundations"); the crosswalk takes the dated post as primary and reads the other as the same approach in full; the accepted text is not edited | item 119; `mvp-m9-crosswalk.md` 8 |
| M9-4's reader against M9-3's writer | the generator and the monitor taken as the implementation of record; the log module reads the expectation's `log` section as the generator writes it (its exact keys), derives the run class by the generator's rule, and binds the domains' harts as the generator does | `c56022e6` |
| `./mvp/mvp check` under load | `run-tool-check`'s autoboot timing cases (item 93) failed under the M8 solvers' load after every other step passed; the dry run's window made the board's 3 s on its own branch and merged (``dc07f7d3``); no board tool and no judgement changed | item 93; ``b7e059b5`, `7ed829c1`` |
| The reference "copied into every retained record and evidence bundle" (profile 5.3) | the bundle did not carry the exports or the references until item 120's change (``74b02017`, `dc6bef1f``), made in M9-6 before the gates | item 120 |
| Q10: the correlation boot in the next scheduled board session | not yet run; the human has said the board is available and no session has been scheduled; the board clause stands | the claim; U-16; the packet's next action |
| D-6: the human's probe | not performed as of the gates; the platform clause's "not performed" form; Q14's disposition stands as a premise | `mvp-m9-platform-probe.md` |

## The gates at `X` = `dc07f7d302e01fb622b53e268f2182c991b0f3e6`, from a standalone clean checkout

The gates ran in this checkout (the main one; `git status --porcelain`
empty at `X`; the development branch's worktree held no other checkout of
the branch), driven by a script outside the tree
(`build/mvp/m9-gates/run-gates.sh`, M7-6's retargeted), each gate's output
logged between `start_utc=` and `end_utc=` lines under
`build/mvp/m9-gates/final/`; the host's load average was 1.3 to 8.1 during
the run (the M8 solver jobs had finished). Every line below is from those
logs.

| Gate | Command | Result | When (UTC, 2026-11-03) |
| --- | --- | --- | --- |
| The tool lock | `./mvp/mvp tool-lock check` | PASS (`roles=32 host_only_skipped=0 closure=259 lock_sha256=2f1b732dcf24`) | 20:33:04 to 20:33:08 |
| Every off-board check | `./mvp/mvp check` | `BE_MVP_CHECK: PASS` in 12 min 36 s: the port; the eleven host tests, among them `BE_MVP_HOST: PASS log scenarios=47 assertions=874 gcc=clang` and `… probe scenarios=65 assertions=779 gcc=clang`; the image checker and its mutations on every image; `make references` (`BE_MVP_LOG_REFERENCES: PASS toolchain=gcc images=29 failed=0`, the same for clang, each `--check` byte-identical); the QEMU suite (`BE_MVP_QEMU: PASS runs=64 attempts=79 refused=15`, 32 runs per toolchain) and the 6 sessions (`BE_MVP_SESSIONS: PASS sessions=6 attempts=6 refused=0`), each capture judged with its reference; `BE_MVP_CAPTURE_SELF_TEST: PASS cases=300 failed=0`, `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=459 rejected=459 seed=0x4d30`; the budgets (`measured=50`); the dry run (`BE_MVP_RUN_TOOL_DRY_RUN: PASS`; its autoboot check: 25 boards inside their 3 s windows, the latest `s` 1.26 s after `Autoboot in`, 23 windows ended by their deadline); the licences, the platform-record and platform-probe checks; `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=53 boundary=17`; the evidence bundle `BE_MVP_EVIDENCE: PASS development … files=530 images=339 qemu_attempts=79 session_attempts=6 rehearsals=0 log_exports=58 references=58` (`bundle.txt`: `source_commit=dc07f7d3…`, `source_tree=clean`; `MANIFEST.sha256` SHA-256 `9dba8547…`) | 20:33:08 to 20:45:44 |
| The evaluator | `./mvp/mvp evaluate` | `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`; `host PASS roles=32 host_only_skipped=0 closure=259`; the closure fetched from the verified cache (`rpms=259 … sources=fedora:116,updates:143`); `check` passing inside the image from the clean source mount; `BE_MVP_IMAGE_IDENTITY: PASS images=339 same=339 differing=0` (every image the evaluator built byte-identical with the host's, the probe images, the variants, and the DTB variants' monitors among them); the record `build/mvp-evaluator/record/20261103T204544Z` | 20:45:44 to 20:58:16 |
| The U-Boot rehearsal | `./mvp/mvp uboot-rehearsal` | `BE_MVP_UBOOT_REHEARSAL: PASS cases=7 attempts=8 refused=1 uboot=d96d1c22c67b opensbi=78f14d30c951 qemu=10.2.2`: each scenario image of both toolchains booted by B3's pinned U-Boot v2022.10 under QEMU with the session's `be_` lines, judged in uboot mode with its log (the CRC-32 attribution unchanged, the log's lines judged as in a direct boot), and the missing-image fall-through | 20:58:16 to 21:00:35 |
| The guest's reproducibility | `make -C mvp kernel-repro LINUX_GIT=<local mirror>` | `BE_MVP_KERNEL_REPRO: PASS outputs=23 identical` (the Image, the DTBs, the init, the module, BusyBox and musl's tree; `sysroot_files=1065`) | 21:00:35 to 21:01:26 |
| The model's gate | `./be model-check` | PASS: `Beryllium Architecture Model 0.2 proofs: PASS`, `Beryllium security model v1 policy and hart binding proofs: PASS instances=generated`, `Beryllium MVP input ring proofs: PASS theorems=4 assumptions_closed=4`, `Beryllium policy layer unit tests: PASS checks=169 instances=4 mutations=91`, `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241`, the escape-hatch patterns, the source policy, the reports; M9 changes no model file (M8's stage 1 is on M8's branch, not this one) | 21:01:26 to 21:02:48 |
| The model's evaluator | `./be evaluate` | `BE_EVALUATION: Model 0.2 rootless evidence PASS` | 21:02:48 to 21:04:06 |

Of the seven, `check` and `evaluate` judge M9's log in every image: 29
images per toolchain, each capture's `:19` block rebuilt and compared with
the image's reference, each gate's `LAUNCH … expected=match` or
`wrong-measurement`'s `gated-fail` as declared, `self-report-flip`'s one
finding, every record `reference=equal recomputed=equal`. The board column
of every M9 row stays empty: no board command was issued (stop 10 not
reached), the correlation boot has not run, and the probe is not performed.

## The costs (D-10)

Measured in the QEMU suite of `check` at `X` (`build/mvp/qemu/suite/*.check.txt`,
the checker's `BE_MVP_LOG` and `BE_MVP_LOG_TICKS` lines; ticks at QEMU's
10 MHz clock; the suite's attempts run beside one another, so the ticks
follow the host's scheduling and vary between runs, as B7's switch counts
did). `bytes` is the console volume of the `:06 LAUNCH`, `:19`, and `:20`
text in a run; the hashing precedes the barrier and the operational
budget's arming, so no run budget or guest timeout includes it, and every
attempt's budget held. The profile's rendering is bounded by the 320-byte
line buffer; the longest line is the registers' (4 × 64 hex digits).

| Image (toolchain) | Contract | Records | `:19`/`:20` lines | Bytes | Hashing at the barrier (ticks; ms at 10 MHz) | Domain 0 launch (ticks; ms) | Domain 1 launch (ticks; ms) | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clang-anchor-k3-like | v3/complete (R2 kept) | 15 | 18 | 4817 | 0xb2500; 73.0 | 0x572b5; 35.7 | 0x57f9d; 36.0 | PASS |
| clang-anchor-plic | v3/complete (R2 kept) | 15 | 18 | 4817 | 0xb2b72; 73.2 | 0x577f8; 35.8 | 0x5807b; 36.1 | PASS |
| clang-anchor-rva23 | v3/complete (R2 kept) | 15 | 18 | 4817 | 0xb74b2; 75.1 | 0x5a144; 36.9 | 0x59fa6; 36.9 | PASS |
| clang-exit-budget | v1/post-launch-failure (R2 kept) | 13 | 16 | 4272 | 0xb6197; 74.6 | 0x59002; 36.5 | 0x59ad6; 36.7 | PASS |
| clang-hart-start | v1/post-launch-failure (R2 kept) | 13 | 16 | 4272 | 0xb7030; 75.0 | 0x59ddd; 36.8 | 0x59a61; 36.7 | PASS |
| clang-hostile | v1/complete (R2 kept) | 13 | 16 | 4272 | 0xcc095; 83.6 | 0x609e1; 39.6 | 0x67ea9; 42.6 | PASS |
| clang-init-exit | v1/post-launch-failure (R2 kept) | 13 | 16 | 4272 | 0xb662f; 74.7 | 0x597e1; 36.7 | 0x596c8; 36.6 | PASS |
| clang-k3-like | v1/complete (R2 kept) | 13 | 16 | 4272 | 0xb6460; 74.7 | 0x58fc0; 36.4 | 0x59bfc; 36.8 | PASS |
| clang-no-grant-check | v3/post-launch-failure (R2 kept) | 15 | 18 | 4817 | 0xb191f; 72.7 | 0x56df3; 35.6 | 0x5782f; 35.8 | PASS |
| clang-no-inject | v2/post-launch-failure (R2 kept) | 14 | 17 | 4557 | 0xe56a4a; 1503.5 | 0x7130ac; 741.8 | 0x713b52; 742.1 | PASS |
| clang-plic | v1/complete (R2 kept) | 13 | 16 | 4272 | 0xb6b01; 74.8 | 0x59a89; 36.7 | 0x5984b; 36.7 | PASS |
| clang-probe-console-input | probe/complete (R2 kept) | 9 | 12 | 3220 | 0x2c46; 1.1 | -; - | -; - | PASS |
| clang-probe-platform | probe/complete (R2 kept) | 9 | 12 | 3220 | 0x2b89; 1.1 | -; - | -; - | PASS |
| clang-probe-vmid-distinct | probe/complete (R2 kept) | 9 | 12 | 3220 | 0x2b4a; 1.1 | -; - | -; - | PASS |
| clang-probe-vmid-shared | probe/complete (R2 kept) | 9 | 12 | 3220 | 0x2bc8; 1.1 | -; - | -; - | PASS |
| clang-rdcycle | v1/post-launch-failure (R2 kept) | 13 | 16 | 4272 | 0xb6d57; 74.9 | 0x59abe; 36.7 | 0x59a69; 36.7 | PASS |
| clang-ring-full | v1/post-launch-failure (R2 kept) | 13 | 15 | 3968 | 0xb71eb; 75.0 | 0x59cfb; 36.8 | 0x59cd1; 36.8 | PASS |
| clang-run-timeout | v1/post-launch-failure (R2 kept) | 13 | 16 | 4272 | 0xb6e46; 74.9 | 0x59ba3; 36.8 | 0x59a99; 36.7 | PASS |
| clang-rva23 | v1/complete (R2 kept) | 13 | 16 | 4272 | 0xd6a0f; 87.9 | 0x588ee; 36.3 | 0x7aab4; 50.2 | PASS |
| clang-sbi-time | v1/complete (R2 kept) | 13 | 16 | 4272 | 0xb7932; 75.2 | 0x59e2a; 36.8 | 0x5a228; 36.9 | PASS |
| clang-self-report-flip | v3/self-report-flip (R2 kept) | 15 | 18 | 4817 | 0xb58e2; 74.4 | 0x5974b; 36.6 | 0x58e4e; 36.4 | PASS |
| clang-shim-rule | v1/complete (R2 kept) | 13 | 16 | 4272 | 0xbb9f3; 76.8 | 0x59f04; 36.8 | 0x5e2c2; 38.6 | PASS |
| clang-te-poc-k3-like | v2/complete (R2 kept) | 14 | 17 | 4556 | 0xba78e; 76.4 | 0x5b930; 37.5 | 0x5b9a8; 37.5 | PASS |
| clang-te-poc-plic | v2/complete (R2 kept) | 14 | 17 | 4556 | 0xb69bf; 74.8 | 0x59cbf; 36.8 | 0x59949; 36.7 | PASS |
| clang-te-poc-rva23 | v2/complete (R2 kept) | 14 | 17 | 4556 | 0xb715d; 75.0 | 0x59cc7; 36.8 | 0x59fa8; 36.9 | PASS |
| clang-wrong-measurement | v3/gate-fail (R2 kept) | 14 | 15 | 3948 | none; - | 0x5693b; 35.5 | -; - | PASS |
| gcc-anchor-k3-like | v3/complete (R2 kept) | 15 | 18 | 4817 | 0xbcee1; 77.4 | 0x5cb62; 38.0 | 0x5cd6c; 38.0 | PASS |
| gcc-anchor-plic | v3/complete (R2 kept) | 15 | 18 | 4818 | 0x54c6db; 555.6 | 0x2975a0; 271.7 | 0x29c9ad; 273.9 | PASS |
| gcc-anchor-rva23 | v3/complete (R2 kept) | 15 | 18 | 4817 | 0xbdd44; 77.8 | 0x5d47b; 38.2 | 0x5d23f; 38.2 | PASS |
| gcc-exit-budget | v1/post-launch-failure (R2 kept) | 13 | 16 | 4272 | 0xbcde0; 77.4 | 0x5c81e; 37.9 | 0x5d256; 38.2 | PASS |
| gcc-hart-start | v1/post-launch-failure (R2 kept) | 13 | 16 | 4272 | 0xbc9f2; 77.3 | 0x5c8d0; 37.9 | 0x5ce13; 38.0 | PASS |
| gcc-hostile | v1/complete (R2 kept) | 13 | 16 | 4272 | 0xbcf9c; 77.4 | 0x5cdc0; 38.0 | 0x5cea1; 38.1 | PASS |
| gcc-init-exit | v1/post-launch-failure (R2 kept) | 13 | 16 | 4272 | 0xbd16f; 77.5 | 0x5cf97; 38.1 | 0x5ce94; 38.1 | PASS |
| gcc-k3-like | v1/complete (R2 kept) | 13 | 16 | 4272 | 0xbc868; 77.2 | 0x5cabd; 38.0 | 0x5ca4f; 37.9 | PASS |
| gcc-no-grant-check | v3/post-launch-failure (R2 kept) | 15 | 18 | 4818 | 0x5532b6; 558.4 | 0x29e0df; 274.5 | 0x29cbe8; 273.9 | PASS |
| gcc-no-inject | v2/post-launch-failure (R2 kept) | 14 | 17 | 4557 | 0x16e7cb; 150.1 | 0x5cdae; 38.0 | 0x10e528; 110.7 | PASS |
| gcc-plic | v1/complete (R2 kept) | 13 | 16 | 4272 | 0xbc42d; 77.1 | 0x5c572; 37.8 | 0x5cb60; 38.0 | PASS |
| gcc-probe-console-input | probe/complete (R2 kept) | 9 | 12 | 3220 | 0x4899; 1.9 | -; - | -; - | PASS |
| gcc-probe-platform | probe/complete (R2 kept) | 9 | 12 | 3220 | 0x33d8; 1.3 | -; - | -; - | PASS |
| gcc-probe-vmid-distinct | probe/complete (R2 kept) | 9 | 12 | 3220 | 0x2d63; 1.2 | -; - | -; - | PASS |
| gcc-probe-vmid-shared | probe/complete (R2 kept) | 9 | 12 | 3220 | 0x2cba; 1.1 | -; - | -; - | PASS |
| gcc-rdcycle | v1/post-launch-failure (R2 kept) | 13 | 16 | 4272 | 0xbd20f; 77.5 | 0x5c8a3; 37.9 | 0x5d63e; 38.3 | PASS |
| gcc-ring-full | v1/post-launch-failure (R2 kept) | 13 | 15 | 3968 | 0xbc208; 77.1 | 0x5c7fa; 37.9 | 0x5c6fd; 37.9 | PASS |
| gcc-run-timeout | v1/post-launch-failure (R2 kept) | 13 | 16 | 4272 | 0xbc4d6; 77.1 | 0x5c74c; 37.9 | 0x5ca57; 37.9 | PASS |
| gcc-rva23 | v1/complete (R2 kept) | 13 | 16 | 4272 | 0xbc81f; 77.2 | 0x5c975; 37.9 | 0x5cb45; 38.0 | PASS |
| gcc-sbi-time | v1/complete (R2 kept) | 13 | 16 | 4272 | 0xbc8d5; 77.2 | 0x5ca16; 37.9 | 0x5cb8a; 38.0 | PASS |
| gcc-self-report-flip | v3/self-report-flip (R2 kept) | 15 | 18 | 4817 | 0xb8072; 75.4 | 0x59fb3; 36.9 | 0x5ac70; 37.2 | PASS |
| gcc-shim-rule | v1/complete (R2 kept) | 13 | 16 | 4272 | 0xb7c95; 75.3 | 0x59fd7; 36.9 | 0x5ab61; 37.2 | PASS |
| gcc-te-poc-k3-like | v2/complete (R2 kept) | 14 | 17 | 4556 | 0xbcba2; 77.3 | 0x5c836; 37.9 | 0x5cef1; 38.1 | PASS |
| gcc-te-poc-plic | v2/complete (R2 kept) | 14 | 17 | 4556 | 0xb79a1; 75.2 | 0x59dc6; 36.8 | 0x5a8a4; 37.1 | PASS |
| gcc-te-poc-rva23 | v2/complete (R2 kept) | 14 | 17 | 4556 | 0xda151; 89.3 | 0x78d9f; 49.5 | 0x5de47; 38.5 | PASS |
| gcc-wrong-measurement | v3/gate-fail (R2 kept) | 14 | 15 | 3948 | none; - | 0x5ba44; 37.5 | -; - | PASS |

In the `-m9` fixtures (GCC, boot hart 0, made by M9-3 on an idle host):
`te-poc` `0xe3b44` ticks (93 ms) at the barrier, `0x70793` and `0x6f67c`
per domain; `two-guests` and `anchor` of the same order. The MVP region's
use at `X`: `mvp_bytes=0xd000` (`two-guests`, GCC) and `0xe000` (`anchor`,
GCC), `0xc4d0` and `0xd4b0` (Clang), of `0x40000`; the monitor's text ends
`0x102002e10` (GCC) and `0x102002ff0` (Clang) against the accepted
`0x102008000` limit, unchanged by M9 (the log lives in the MVP region and
hart 0's BSS).

## Soft limits and stops in M9

| Limit or stop | Outcome |
| --- | --- |
| Counted lines (C, assembly, linker scripts, Python, shell, Make, the wrapper; tests included) | `9,812` of the re-set 10,000 at `X` (Python `6,545`, C `2,820`, Make `169`, shell `254`, linker script 24); excluded and reported: fixtures and records `14,744`, Markdown `2,667`, JSON `178` |
| The checker-to-monitor size ratio (reported, not limited; M7's 2.083) | `**2.294** at `X` by M7's set with `tests/log_module.py` added to the checkers (the monitor, `src/*` and `shim/mvp-shim.S`, 16,417 lines; the checking code 37,653: the five checkers 14,116, the log module 2,701, the eleven host tests 15,878, the eight harness drivers 4,958); 2.083 at the M9 base; M9's increment 1,058 monitor lines and 5,664 checking lines, 5.35 per monitor line, the recomputation and replay being the design; `tools/gen-reference.py` (1,035) and `tools/evidence.py` stay outside the rows as `gen-scenario.py` and `evidence.py` did` |
| Revision 3's 250-line guide (Q12) | 252 lines appended |
| Stop 1 (eFuse, lifecycle, NOR) | not reached |
| Stop 2 (accepted bytes) | not reached; the one found defect is in M0's probe fixture code, changed under the M9 plan's stop 2 protocol with the human's decision |
| Stop 3 (an object the checker cannot compute) | not reached; R2 kept |
| Stop 4 (claim text beyond D-9) | not reached |
| Stop 5 (counts outside the rule; the SBI) | not reached |
| Stop 6 (overflow; count above fifteen; a contract that cannot be stated) | not reached; the largest image is v3 with 15 |
| Stop 7 (guest content parsed in HS) | not reached |
| Stop 8 (the soft limit) | fired once; re-set to 10,000 (erratum 1) |
| Stop 9 (M8's files) | not reached; M9 edits `mvp.h`, `mvp-layout.h`, and `mvp-runtime.c` as D-10 foresaw, and M8's lane is separate; M10's re-proof rule applies at integration |
| Stop 10 (board commands) | not reached; none issued |
| Stop 11 (push, merge, tag, publication, snapshot, kexec) | not reached |
| Stop 12 (claim boundary) | not reached |

## Open items

Opened or closed by M9 in `mvp/README.md` (118 is M8's and is kept free
here):

| Item | State | What |
| --- | --- | --- |
| 93 | closed (M9-6, `b7e059b5`) | the dry run's autoboot window is the board's 3 s, run to its deadline; the deadline-dependent cases give the console tool its default 5 s wait; each `s` logged with its time, a late one reported as lateness under load; ten dry runs passed under load, two at once among them |
| 104 | closed (M9-2) | the premise record `mvp/results/20261030-uboot-help/` |
| 108 | closed (M9-5) | the console grants are a measured record of stream 1 |
| 116 | closed (M9-4, `b591466c`) | `k3-run.sh` computes `staged_sha256` |
| 119 | open (for the packet) | the M9 plan's Q13 citation joins one post's title to another's date |
| 120 | closed (M9-6, `74b02017`) | the evidence bundle carries the log exports and the references |
| 121 | open | a code reading of the console tool's second `s` landing at a late prompt (not reproduced; the board tools unchanged by item 93; a later sweep's) |
| 122 | open | `tools/rc-record.py` copies a rehearsal attempt's files by `evidence.REHEARSAL_FILES`, which M9-6 extended for the bundle but which the release-candidate record tool reads without `log.json`; M10's, with the record's other M9 additions |
| 123 | open | the hashing times in QEMU follow the host's scheduling (`no-inject`'s launches took 742 ms per domain on Clang in one run of the suite, against 36 to 38 ms elsewhere); the costs are recorded per run and judged against nothing, and the board's figures wait for the correlation boot |

## Claim boundary

What this record supports: in QEMU, for both toolchains, every image's
control hart kept the log the profile defines and closed it before any
domain hart started; each domain's launch register equalled the image's
expected value, and the one image built to differ failed closed at its
gate before any hart started; the checker rebuilt every log byte for byte
from the printed lines, replayed the registers, recomputed every digest
from the build's inputs, and found every record and register equal to the
image's post-link reference, except the one record the `self-report-flip`
image was built to change, which it reported as its one finding.

What it does not support: attestation of any kind (no key, nonce,
freshness, counter, or root of trust; the expected values and the code
that compares with them are in the same image); the integrity of the
measured bytes after the point of measurement; the integrity of SPL,
OpenSBI, U-Boot, or the boot ROM, none of which is measured; the
protection of the log and the registers inside HS against code that can
write hart 0's memory (U-12 stays open); any board evidence at M9's
images (the correlation boot has not run); the board's lifecycle or debug
state (no probe performed); any interoperability with a TPM event-log or
systemd tool; any claim about files inside a guest. It is not formal
verification, hardware validation, or certification.
