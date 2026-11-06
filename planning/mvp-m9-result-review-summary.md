<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M9 result review summary

This packet presents the result of M9, "Measurement", the milestone the
accepted
[Plan revision S3-C](mvp-plan.md#plan-revision-s3-c-the-mvp-ladder-and-mvp-1-0-widened-to-interactive-guests-a-first-verification-plan-and-measurement)
(`27d2e557`) added to the [MVP plan](mvp-plan.md) under its D20
(`measure first, then attest`; IMA never used): the control hart records,
before any domain runs, the digests of what it placed or sealed in a
bounded log with one register per stream, gates each domain's start on
its launch register, and an offline checker rebuilds, replays, recomputes,
and compares every record with a post-link reference. It was implemented
under the accepted [M9 plan](mvp-m9-plan.md) (`4f4a8f76`, its second
candidate), whose [acceptance record](mvp-m9-plan-review-summary.md)
holds its authorization, with Q1 to Q19 at their defaults (Q17 answered),
erratum 1 (the soft limit re-set to 10,000), and the `fix now` decision on
the probe race. It also records the responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`892b68c81dace15d2357e034e859b3eccd130abc` (the M9 result commit `R`,
parent `461e9e6f658b170ddc8150f65bbb32038b718c96`, over the gates'
commit `X` = `dc07f7d302e01fb622b53e268f2182c991b0f3e6`) as the M9 result
on 2026-11-03 (16:23 in the human's time zone). The instruction, given in
reply to this packet's request to accept, revise, or defer that exact
commit, was `accept 892b68c8`; the abbreviation was checked to resolve
uniquely (`git rev-parse --disambiguate=892b68c8`). With it the human
accepted what the packet presented with the result: the departures of
section 5 (the profile's ten choices as version 1; Q7's reading of
S3-C.5's "CEL-JSON" as the Beryllium log profile; the probe-race fix
made on the human's earlier `fix now`; the two harness fixes outside
M9's packages, items 93 and 120), and the Q13 citation mismatch (item
119) is recorded as erratum 2 of the M9 plan in its decision record, the
accepted plan text unedited. The claim's sentences as D-9 fixed them,
with their slots filled from the recorded outcomes, take effect with
this acceptance. The instruction directed no fast-forward, merge, push,
snapshot refresh, board step, or successor: each keeps its own gate; the
development branch stays at `55047781` locally and on the private
`origin`, and `beryllium/mvp-m9` and `beryllium/mvp-m9-plan` stay local.
The two board items stay the human's to schedule: the read-only probe
(the claim's platform clause reads "not determined as of 2026-11-03; no
probe was performed" until a probe is recorded) and the one `anchor`
correlation boot at M9's images (Q10), each announced first and with the
human present. M10's plan waits for M8's result as well.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `892b68c81dace15d2357e034e859b3eccd130abc` (the M9 result commit `R`, parent `461e9e6f`, over the gates' commit `X` = `dc07f7d302e01fb622b53e268f2182c991b0f3e6`), on local branch `beryllium/mvp-m9` from the M9 plan's acceptance record `bc80b620` (which merged the development branch's tip `55047781`). `R` adds over `X` only the evidence record `planning/mvp-m9-evidence.md` and the README's M9-6 record and items 122 and 123; no monitor, guest, test, tool, scenario, or model byte follows `X`. |
| Current status | **Responsible-human accepted on 2026-11-03** (instruction `accept 892b68c8`; the [decision record](#decision-record)). As presented: implemented, checked on the host and in QEMU, reviewed line by line by the session before each merge; the seven gates pass at `X` from this checkout clean at `X` (2026-11-03, 20:33 to 21:04 UTC; `build/mvp/m9-gates/final/`); `./mvp/mvp claim-ledger check` passes at `R` (`claims=53 boundary=17`). **No board run**: the human's probe is not performed and the correlation boot has not run, and the claim's two slots say so. |
| Decision requested | As presented: accept exact commit `892b68c81dace15d2357e034e859b3eccd130abc` as the M9 result; or request revisions; or defer. With it: the departures in section 5 (the Q13 citation erratum, item 119, among them), the profile's ten choices (`mvp/docs/log-profile.md`, section 1), and the two harness fixes made under M9 outside its packages (items 93 and 120). |
| Successor status | As presented and after the decision: not started and not authorized: M10 (release candidate 4) is a plan to write after the M8 and M9 results are accepted (S3-C's authorization); M8-7 (M8's result) follows the arms' re-run on `beryllium/mvp-m8`, a separate lane. The correlation boot at M9's images is folded into the next board session you schedule (Q10) or one you ask for. |
| Publication status | Private repository (the internal one). As presented and after the decision: `beryllium/mvp-m9` and `beryllium/mvp-m9-plan` are local and unpushed; the development branch `beryllium/single-hart-runtime-r0` is at `55047781` locally and on the private `origin`; no tag, publication, release step, or snapshot refresh; nothing of this reaches the public review snapshot (`main` `36e2590c`) unless you direct a refresh. |

As presented: please review exact commit
`892b68c81dace15d2357e034e859b3eccd130abc` and accept it, request
revisions, or defer. Outcome: accepted; see the
[decision record](#decision-record).

## 2. Deliverables

| Deliverable | Paths | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| Part 1 Revision 3 of security model v1 (M9-2, first; `4bc079db`, **accepted** 2026-11-03, record `f4f9cbfb`) | `planning/security-model-v1.md` (252 lines appended), `planning/security-model-v1-revision-3-review-summary.md` | The log page and the registers as instances of the `measurement` asset, hart 0's by phase; the offline evidence TCB beside the running TCB; the loader observation and the probe as trusted inputs and dated assumptions; I19, I20; six TCB rows | Accepted separately; the accepted text byte-identical | Already decided; nothing new here |
| The profile and the premise (M9-2; `ca48456f`) | `mvp/docs/log-profile.md` (new, 1,176 lines), `mvp/results/20261030-uboot-help/` (6 files), `planning/mvp-m9-platform-probe.md` (new) | The Beryllium log profile, version 1: the page's encoding offset by offset, the enumerations, the per-image contract, the line grammar, the JSON export and the reference manifest, the mapping to CEL 1.1 with the unmapped fields and the no-interoperability statement, the allowlist; item 104's premise record (this U-Boot has `crc32` and `md5sum`, no `sha256sum`, `hash`, or `tpm`); the probe template with its four outcome classes and Q14's words | Derived from CEL, not CEL; the premise record was captured on 2026-10-30 under board policy item 6 | Are the ten choices the profile makes where the plan left them open (its section 1) the ones you want frozen as version 1? |
| The monitor's log (M9-3; `b92b9308` to `d6aa0f82`, merged `39bb5ab2`) | `mvp/src/mvp-log.c`/`.h` (new), `mvp-runtime.c` (`measure_log()`), `mvp-monitor.lds`, `mvp-platform.h`, `mvp.h`, `mvp-sbi.c`; `mvp/tests/log-test.c` (new), `sbi-test.c`; `mvp/tools/gen-scenario.py`, `policy-check.py`, `flip-canary.py` (new), `guest-pins.py`; `mvp/tests/check-image.py`, `run-qemu.sh`; `mvp/Makefile`; `mvp/scenarios/anchor/scenario.json`; the `-m9` fixtures and `tests/fixtures/pre-m9/` | The 4 KiB page and the four registers in hart 0's MVP-region BSS; R2's five ranges by link symbols (R2 kept, Q4), R3's sealed core identity and console grants measured with the two build identities informational, each domain's R4 with its gate on its last record, the close with the expected count; the block and both `:20` lines; a failed gate failing closed as `measurement`, a page that cannot close as `log`; the generator's expected values and the 172-byte constants; the image checker's rules with a mutation each; `self-report-flip`; `guest-pins.py`'s IMA refusal (D-5) | The log is a local identity (no key, nonce, freshness, root of trust); the expected values and the gate are in the same image; the page is protected inside HS by code discipline (U-12) | Does every record's digest come from bytes the monitor itself placed or sealed, in place, after the placement and before any domain hart starts, and can nothing after the close extend a register? (`measure_log()`'s position before `publish_blocks()` and `start_run()`; `be_mvp_log_close`; I19) |
| The probe-race fix (M9-3; `75459737`, merged `8f6660ab`) | `mvp/src/mvp-probe.c`, `mvp/tests/probe-test.c` (new), `mvp/Makefile`; the four GCC probe fixtures | Each IPI phase counts in its own word; a host test (65 scenarios, 779 assertions, GCC = Clang) in which 17 of 64 schedules fail on the old code with the captured line; 80 of 80 QEMU probe runs | Fixture code (M0's probe), not the monitor; changed under the M9 plan's stop 2 protocol on your `fix now` | Is a found-and-fixed defect in M0's probe fixture, with its test, acceptable inside M9's result? |
| The references and the checker (M9-4; `849c484b` to `d8aa0339`, merged `1edc3652`) | `mvp/tools/gen-reference.py` (new), `mvp/tests/log_module.py` (new), `check-capture.py`, `platform-record.py`, `k3-run.sh`, `run-tool-dry-run.sh`, `fake-uboot.py`, `tools.mk` | One post-link reference per image and toolchain (29 each); the checker's rebuild of the page from the `:19` lines byte for byte, the replay of the registers (`unprotected`), the recomputation of every digest from the build's inputs, the comparison of every record and register with the reference, the per-image contract and the lines' positions, the export `log.json`; the negatives (`cases=300`, `mutations=459`); the platform record's sections; item 116 | The offline evidence TCB (Revision 3): the checker and the build's inputs, which the running monitor does not see | Does the checker recompute the digests from the build's inputs, independently of what the monitor printed, and does the reference tool read the linked constants rather than trust the generator? (`log_module.py`'s recompute; `gen-reference.py`'s `constants=linked`) |
| The words (M9-5; `f5e7925e` to `a8636087`) | `mvp/docs/claim.md`, `claim-ledger.json`/`.md` (C-51 to C-53, U-16, U-17; U-10, U-12, U-14, C-16, C-40 restated; pins C-10, C-40, C-41, C-48, C-51 refreshed), `guide.md`; `planning/mvp-m9-crosswalk.md` (new) | The claim's sentences exactly as D-9 fixes them, the three slots filled from the recorded outcomes (R2 kept; no probe performed as of 2026-11-03; the correlation boot not run); the ledger rows without a board method; the guide's measurement section; the crosswalk (D-7): systemd v259's four pieces on five dimensions, the three routes' requirements, what a simulated root needs, the IMA boundary, milestone 7 placed, one Amutable lesson | Stop 4 not reached; the forbidden-phrasing check passes | Do the claim's new sentences say what the evidence supports, no more (section 3)? Is the crosswalk's reading of milestone 7's gate as discharged "by documenting the roots as absent" the reading you want? |
| The bundle and the window (M9-6; `74b02017`, `dc6bef1f`, `45ce8e8c`, `cbbdcb17`; `b7e059b5`, `7ed829c1`) | `mvp/tools/evidence.py`, `mvp/docs/guide.md`, `log-profile.md` (one sentence), `mvp/tests/run-tool-dry-run.sh`, `fake-uboot.py`, `mvp/README.md` | The evidence bundle carries the log exports and the references under a stated rule (51 self-test cases); the dry run's autoboot window is the board's 3 s, run to its deadline, with lateness reported as such (item 93) | Harness and bundle code only; no board tool, no judgement, no monitor byte changed | Are two harness fixes outside M9's packages, each with its negative cases, acceptable in M9's result rather than a later sweep? |
| The evidence record and the log (M9-6; `R`) | `planning/mvp-m9-evidence.md`; `mvp/README.md` (the M9 entries; items 119 to 123) | What was run, when, on which commit, and what it printed; the departures; the costs; the stops; the open items | — | Are the departures and the open items complete and honest? |

Exact changed-file inventory from the M9 base, outside the fixtures
(54 files added or changed under `mvp/tests/fixtures/`) and the premise
record (6 files under `mvp/results/20261030-uboot-help/`):

```text
# git diff --name-status bc80b620 892b68c81dace15d2357e034e859b3eccd130abc | grep -v -e 'mvp/tests/fixtures/' -e '^A.mvp/results/'
M	.github/copilot-instructions.md
M	mvp/Makefile
M	mvp/README.md
M	mvp/docs/claim-ledger.json
M	mvp/docs/claim-ledger.md
M	mvp/docs/claim.md
M	mvp/docs/guide.md
A	mvp/docs/log-profile.md
M	mvp/scenarios/anchor/scenario.json
A	mvp/src/mvp-log.c
A	mvp/src/mvp-log.h
M	mvp/src/mvp-monitor.lds
M	mvp/src/mvp-platform.h
M	mvp/src/mvp-probe.c
M	mvp/src/mvp-runtime.c
M	mvp/src/mvp-sbi.c
M	mvp/src/mvp.h
M	mvp/tests/check-capture.py
M	mvp/tests/check-image.py
M	mvp/tests/fake-uboot.py
A	mvp/tests/log-test.c
A	mvp/tests/log_module.py
A	mvp/tests/probe-test.c
M	mvp/tests/run-qemu.sh
M	mvp/tests/run-tool-dry-run.sh
M	mvp/tests/sbi-test.c
M	mvp/tools.mk
M	mvp/tools/evidence.py
A	mvp/tools/flip-canary.py
A	mvp/tools/gen-reference.py
M	mvp/tools/gen-scenario.py
M	mvp/tools/guest-pins.py
M	mvp/tools/k3-run.sh
M	mvp/tools/platform-record.py
M	mvp/tools/policy-check.py
M	planning/.vitepress/config.mts
M	planning/HANDOFF.md
M	planning/README.md
A	planning/mvp-m9-crosswalk.md
A	planning/mvp-m9-evidence.md
A	planning/mvp-m9-platform-probe.md
M	planning/roadmap.md
M	planning/security-model-v1.md
A	planning/security-model-v1-revision-3-review-summary.md
```

No file under `model/`, `tests/r*/`, `bringup/`, `pathfinder/`, or
`mvp/guest/` changes; no accepted R0-R7, B0-B7, or model byte; `mvp.h`,
`mvp-layout.h`, and `mvp-runtime.c`, which M8's leaves and stage 1 read,
change as D-10 foresaw (`mvp-layout.h` does not change in the end; the
log's page is BSS and its constants `.mvp.rodata`), and M10's re-proof
rule applies at integration (stop 9 not reached: M9 edits none of M8's
files).

## 3. Claim boundary

**What `R` supports saying** (the claim's new sentences, `mvp/docs/claim.md`):

> For the Linux-guest runs the ledger identifies, before any domain runs,
> the control hart records in a bounded log the digests it computes over
> what it placed or sealed on that platform (the sealed configuration's
> core identity and console grants, each domain's kernel Image and device
> tree as placed, and `anchor`'s secret page) and the identities the build
> carries, extends one register per stream with the measured records'
> digests only, and compares each domain's launch register with the
> image's expected value before that domain starts; the checker rebuilds
> the log from its printed lines, replays the registers, recomputes every
> digest from the build's inputs, and compares every record with the
> image's post-link reference.

and the required limit's replacement:

> The log is a local identity, not attestation: it has no key, nonce,
> freshness, or root of trust, so code able to alter the monitor can
> fabricate its records, and a record does not show the bytes unchanged
> after the point of measurement; the monitor's digest of its own text
> and read-only data is a self-report, compared offline and gating
> nothing. On the board, U-Boot, identified by its banner and unmeasured,
> prints an MD5 of the loaded boot image, which the checker holds as
> attribution of the run to its image and as nothing more; no loader
> observation exists in direct QEMU boots, and the U-Boot rehearsal
> records a CRC-32 separately. SPL, OpenSBI, and U-Boot are unmeasured.
> The board's lifecycle and debug state were not determined as of
> 2026-11-03; no probe was performed. The log and launch-gate evidence is
> from QEMU; the M9 board correlation has not run.

Each slot's form is the one D-9 fixes for the recorded outcome (R2 kept;
no probe; the correlation boot not run), so choosing it is not a claim
change. The ledger's new rows (C-51 the log and the registers; C-52 the
launch gate per domain, citing I19 and I20; C-53 the self-report) carry
host unit test, adversarial test, semantic checker, and emulation and no
board method; U-16 holds R1 and the platform observation; U-17 is D-5's
third check. The evidence is from QEMU, both toolchains, 29 images each.

**What remains trusted or assumed:** the build's inputs the checker
recomputes from (the guest kernel and device trees as built and pinned,
the generator's canonical inputs, the boot image); the gate's expected
values, which are constants of the same image as the gate; that no domain
hart reads the page or the registers, a code-discipline claim within HS
(U-12 open); the vendor's SPL, OpenSBI, and U-Boot as installed in NOR,
unmeasured and identified by banner and SBI identity; whether the boot
ROM authenticates SPL, which no 1.0 claim relies on (Q14's disposition:
"correctly installed vendor firmware is a premise, not a measured fact").

**What is unavailable or `NOT RUN`:** the human's read-only probe of the
board's lifecycle and debug state (the template waits; the claim says
"not determined as of 2026-11-03"); the correlation boot at M9's images
(every M9 ledger row's board column empty; the claim's board clause
stands); the costs on the board; M8's proofs re-run against M9's tree
(M10's re-proof rule); the retained board records of M0 to M7 and RC1 to
RC3 are at their own images, which print no log.

**What the commit does not implement:** attestation of any kind (no key,
nonce, counter, vTPM, SBI measurement extension; Q39); measurement of
SPL, OpenSBI, U-Boot, the board's device tree, or any file inside a
guest (D20; U-17); any CEL conformance or systemd interoperability (the
crosswalk analyses three routes and selects none); any model change
(stop (e)); any change to the guest-visible SBI (the implementation
version stays 5, 6 with management); any push, merge, tag, publication,
snapshot refresh, kexec use, or board command.

## 4. Security and correctness invariants

| Property | Contract | Implementation | Test or evidence |
| --- | --- | --- | --- |
| Hart 0 alone writes the log and the registers, before any domain hart starts, and closes it with the expected count; no record follows the close (I19) | security model v1 Revision 3, R3.2; the profile's 2.5 and 4.5 | `measure_log()` before `publish_blocks()` and `start_run()` in `mvp-runtime.c`; `be_mvp_log_close()` refusing a count other than the image's; the page and the registers in hart 0's MVP-region BSS | `check-image.py`'s `HART0_ONLY` rule for the page and the registers with a mutation each; `log-test.c`'s close rule and overflow cases; the checker's global order (each `LAUNCH` and `gated-pass` before that domain's `:08`, the close before `:07`, the terminal `:20` before `:14`) on every capture; no proof of the C |
| No domain hart starts unless every required launch comparison has succeeded and the log is closed (I20) | Revision 3, R3.2; the plan's D-2 | `be_mvp_log_gate()` on the domain's last launch record against `be_mvp_log_constants`; a failed gate fails the run as `measurement` before the first SBI HSM start | `wrong-measurement` in QEMU, both toolchains (`gated-fail`, `FAIL measurement`, `DETAIL computed= expected=` one bit apart, no `HART_STARTED`); the capture mutations with the reference frozen; `check-image.py`'s independent computation of the expected launch registers from the boot image |
| Every record's digest is recomputable from the build's inputs, and the printed registers replay from the records | the profile's 4.6 and 4.7; D-3, D-4 | `gen-reference.py` from the linked constants and the linker's symbols; `log_module.py`'s recompute and replay | `BE_MVP_LOG_RECORD: … reference=equal recomputed=equal` for every record of every capture; `BE_MVP_LOG_REGISTERS: at=replayed` equal to both `:20` lines; `mutations=459` rejected; R2 kept because the ranges reproduce byte for byte (Q4; the evaluator's 339 identical images) |
| The self-report sees a post-link change in a covered range and gates nothing | D-4; the profile's 4.7 | `flip-canary.py`; stream 0 compared through its records only | `self-report-flip`'s one finding `self-report differs: mvp-rodata`, the run otherwise complete with `anchor`'s counts; the expectation's declared finding required to be exactly the checker's |
| The monitor measures only what it places or seals; no IMA (D-5) | D20; U-17 | `guest-pins.py --check`; the checker's and the reference reader's allowlist | six planted `CONFIG_IMA`/`CONFIG_EVM` settings refused; any object, content type, schema, or algorithm outside the profile's refused in a line, an export, or a reference |
| The accepted scenarios' counts stay within the checker's existing rule (D-11) | the plan's D-11 | no change to the rings, the denial path, the management path, or the console path | `records` exact (138, 146, 174); `exits` and `wakes` within the rule as the checker judges them; the SBI version unchanged; stop 5 not reached |

## 5. Review history, stops, and errata

- **Steering review (Q17).** The plan's first candidate was reviewed by
  `gpt-6-astra` at your direction; its five blockers shaped the second
  candidate you accepted. No review of the implementation by another
  model was made (the SOP's default).
- **Stop 8, the soft limit** (checkpoint after M9-3): about 7,900 lines
  counted with M9-4's branch in view against 6,000; you re-set the limit
  to 10,000 (erratum 1). 9,812 at `X`, the two harness fixes included.
- **Stop 2, the probe race** (M9-3): `probe-platform` on Clang printed
  `delivered=0` once in 25 runs; a race in M0's probe fixture between
  hart 1's `FID_IPI_VS` call and hart 0's read of the shared count. You
  decided `fix now`; fixed with a host test that fails on the old code
  (section 2). A snapshot by hart 0 would not have closed it.
- **Item 93 under the gates.** `./mvp/mvp check` on the merged tree
  failed only in the dry run's timing-bound autoboot cases under a load
  average of 15 to 19 (M8's solvers on the same host), every other step
  passing; the fix item 93 named (the dry run's window made the board's)
  was made by a pinned sub-agent, whose first draft ended the fake's
  window early at the second swallowed `s`, a shortcut the board does not
  have; it was replaced before the merge by the board's full window with
  the tool's default wait for the deadline-dependent cases. No board tool
  changed; item 121 records a code reading of the console tool for a
  later sweep.
- **Item 120.** The profile's 5.3 said the reference is copied into every
  retained record and bundle before the bundle did so; closed in M9-6
  with a stated rule and 51 self-test cases; the profile's sentence now
  names the two sets.
- **Plan erratum, Q13** (item 119): the plan cites "Introducing Amutable
  Foundations", 2026-09-03; that title is the 2026-10-22 post's and the
  date is "Building New Secure Foundations"'s. The crosswalk takes the
  dated post as the primary document and reads the other as the same
  approach in full; the accepted text is not edited. For your acceptance
  record to note as an erratum.
- **The profile's ten choices** where the plan left them open (its
  section 1), made in M9-2 and implemented as made: the enumerations'
  numbers; the console grants' serialization (one byte per domain, then
  SHA-256); the gate on a domain's last launch record; the close's count
  rule; three rendering paths; `magic=` and the `0x` prefixes; the
  barrier line's saturated hashing total; the lines' places and `FAIL
  log` without `DETAIL`; stream 0 compared through its records only; the
  JSON names and bounds. Presented for your review with the result.
- **Q7's reading** (S3-C.5's "CEL-JSON" as a profile derived from CEL
  1.1, not a conforming CEL), recorded in the profile for acceptance with
  the result.
- **`self-report-flip` moved** from `two-guests` to `anchor` (the longest
  log), both scenarios' images changing by the move; **M9-4 took the
  generator and the monitor as the implementation of record** where
  M9-3's writer departed from the profile's first draft, adapting the
  reader (recorded in `c56022e6`).
- **Open questions for your judgment:** whether milestone 7's gate is
  rightly read as discharged for 1.0 by documenting the roots as absent
  (the crosswalk, section 7); whether item 121 warrants a board-tool
  sweep before release candidate 4; and when the probe and the
  correlation boot run.

## 6. Validation and retained evidence

All at `X` = `dc07f7d302e01fb622b53e268f2182c991b0f3e6`, from this checkout
clean at `X`, 2026-11-03 (UTC), each gate's log under
`build/mvp/m9-gates/final/` (outside the tree): `./mvp/mvp tool-lock
check` PASS (20:33); `./mvp/mvp check` `BE_MVP_CHECK: PASS` (20:33 to
20:45: the eleven host tests, the image checker and its mutations, 29
references per toolchain, the QEMU suite (`runs=64 attempts=79 refused=15`) and 6 sessions each judged
with its reference, `BE_MVP_CAPTURE_SELF_TEST: PASS cases=300`,
`BE_MVP_CAPTURE_MUTATIONS: PASS mutations=459 rejected=459`, the dry run
`BE_MVP_RUN_TOOL_DRY_RUN: PASS`, `BE_MVP_CLAIM_LEDGER: PASS checks=10
claims=53 boundary=17`, `BE_MVP_EVIDENCE: PASS … log_exports=58
references=58`); `./mvp/mvp evaluate` PASS (20:45 to 20:58;
`BE_MVP_IMAGE_IDENTITY: PASS images=339 same=339 differing=0`; the record
`build/mvp-evaluator/record/20261103T204544Z`); `./mvp/mvp
uboot-rehearsal` `PASS cases=7 attempts=8 refused=1` (21:00); `make -C mvp
kernel-repro` `PASS outputs=23 identical` (21:01); `./be model-check` PASS
(21:02; the input ring's four theorems, the differential
`comparisons=241`); `./be evaluate` `Model 0.2 rootless evidence PASS`
(21:04). At `R`: `./mvp/mvp claim-ledger check` PASS (`claims=53
boundary=17`); `node scripts/check-doc-sources.mjs` PASS; `git diff
--check` clean. The evidence record `planning/mvp-m9-evidence.md` holds
the gates' lines, the costs table (D-10), the departures, and the stops.
The retained fixtures `mvp/tests/fixtures/*-m9.log` (GCC, boot hart 0,
made on this tree's images) carry every image class's log and are judged
by the checker's self-test. Not run: any board step.

## 7. Recommended human review sequence

Each command is read-only; for execution, a detached worktree at the exact
commit keeps local changes out:

```sh
git worktree add --detach /tmp/be-m9-review 892b68c81dace15d2357e034e859b3eccd130abc
```

1. **The claim and the limit** (10 min): `git show 892b68c8:mvp/docs/claim.md`
   against the plan's D-9 and its slot table; the ledger's C-51 to C-53,
   U-16, U-17 in `mvp/docs/claim-ledger.md`.
2. **The log's position and the gate** (20 min): `mvp/src/mvp-runtime.c`,
   `measure_log()` and its call before `publish_blocks()`; `mvp/src/mvp-log.c`,
   `be_mvp_log_append`, `be_mvp_log_gate`, `be_mvp_log_close`; the
   profile's sections 2.5, 2.9, and 4.5.
3. **One capture, line by line** (10 min): `mvp/tests/fixtures/qemu-te-poc-gcc-m9.log`
   lines 78 to 96 and 245 to 247, with the guide's new section;
   `qemu-wrong-measurement-gcc-m9.log` lines 94 to 99;
   `qemu-self-report-flip-gcc-m9.log` line 89.
4. **The checker's independence** (20 min): `mvp/tests/log_module.py`,
   the recompute and replay; `mvp/tools/gen-reference.py`, the linked
   constants; run, in the worktree after `make -C mvp references`,
   `python3 -B mvp/tests/check-capture.py mvp/tests/fixtures/qemu-te-poc-gcc-m9.log --expect build/mvp/gen/te-poc/expect/te-poc.json --report build/mvp/records/policy/te-poc.json --toolchain gcc --build-root build/mvp`
   and read its `BE_MVP_LOG*` lines.
5. **The departures** (10 min): the evidence record's table and section
   5 above; the profile's ten choices; item 119.
6. **The crosswalk** (20 min): `planning/mvp-m9-crosswalk.md`, sections
   2.4, 5, 7, and 8.
7. **The harness fixes** (10 min): `git show b7e059b5 -- mvp/tests/fake-uboot.py`
   (the window and the lateness log); `git show 74b02017 -- mvp/tools/evidence.py`
   (the export rule).
8. **The gates** (5 min): `build/mvp/m9-gates/final/driver.txt` and the
   `BE_MVP_*` lines of `check.log` and `evaluate.log`.

## 8. Human decision checklist

- [ ] The scope matches the accepted M9 plan (M9-2 to M9-6, Q1 to Q19 at
      their defaults, erratum 1, the `fix now` decision), and the two
      harness fixes outside its packages are acceptable in its result.
- [ ] The claim's new sentences and the three filled slots say what the
      QEMU evidence supports, no more; the words D-9 forbids are absent.
- [ ] The trust assumptions are acceptable: the gate's expected values
      in the same image; the page's protection by code discipline inside
      HS; the vendor firmware unmeasured; no probe; no board run.
- [ ] The tests cover the negative paths that matter: a failed gate, a
      flipped self-report, a page that cannot close, a forged or missing
      export, a stale reference, the IMA settings.
- [ ] The profile's ten choices and Q7's reading are accepted as version 1.
- [ ] The Q13 citation erratum (item 119) is noted for the acceptance
      record without editing the accepted plan.
- [ ] Successor work stays excluded: M10's plan waits for M8's result too;
      the correlation boot and the probe are scheduled by you.
- [ ] Exact commit `892b68c81dace15d2357e034e859b3eccd130abc` is accepted,
      revisions are requested, or the review is deferred.

## 9. After the decision

- **Accept:** say `accept 892b68c8` (or the full SHA); the session records
  the acceptance in this packet's decision record, the M9 plan's decision
  record and status, the roadmap, the planning README, `HANDOFF.md`, the
  instructions, and `mvp/README.md`, with the Q13 erratum noted; the
  claim's sentences take effect; nothing is fast-forwarded, merged, or
  pushed without its own instruction; M10's plan waits for M8's result.
- **Request revisions:** name them; a new commit and a new packet follow;
  `892b68c8` is not treated as accepted.
- **Defer:** the branch stays as it is; no dependent work starts; the two
  board items stay yours to schedule.

**Status:** M9 implemented through M9-6 at exact commit
`892b68c81dace15d2357e034e859b3eccd130abc`, the seven gates passing at
`X`, no board step run; **responsible-human accepted on 2026-11-03**
(`accept 892b68c8`; the [decision record](#decision-record)).
**Next:** nothing waits on you on M9; the probe and the correlation boot
when you schedule board time; M8-7 when the arms' re-run returns; M10's
plan after M8's result is accepted; any fast-forward or push by its own
instruction.
**Action required from you:** none on M9 (as presented: accept, request
revisions, or defer; outcome: accepted).
