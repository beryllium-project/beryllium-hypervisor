<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M9 plan: measurement

This plan bounds milestone **M9**, measurement, which the accepted
[Plan revision S3-C](mvp-plan.md#plan-revision-s3-c-the-mvp-ladder-and-mvp-1-0-widened-to-interactive-guests-a-first-verification-plan-and-measurement)
(`27d2e557`) of the [MVP plan](mvp-plan.md) defines in its section
S3-C.5 and authorizes writing, under its decision D20 ("measure first,
then attest"; IMA never used). It is proposed on local branch
`beryllium/mvp-m9-plan` from `6fbcc3d1`, the M8 plan's acceptance record,
a linear descendant of the development branch's tip `6105c34d` (Q1), on
the human's `go for m9` (2026-11-02). It is written on the orchestrating
model under the standing split (S3-C's D22); nothing in it is
implementation. This is the **second candidate**: the first, exact commit
`86f1c68b`, is superseded after the independent steering review the human
directed (`have gpt-6-astra review the m9 plan as steering input`,
2026-11-02; Q17 answered), whose five blockers B1 to B5 and recommendations
are incorporated here and recorded in the
[review packet](mvp-m9-plan-review-summary.md)'s review history; the
review's text is kept unedited beside it
([the gpt-6-astra steering review](mvp-m9-plan-review-gpt-6-astra.md)).

## Decision record

The responsible human accepted this plan at exact commit
`4f4a8f760a1ed7e5f9886b4e02e94b7a849bfc33` (parent `d470fb7f`, the first
candidate's packet commit, on branch `beryllium/mvp-m9-plan`) on
2026-11-03 (00:26 in the human's time zone) by the instruction `accept
4f4a8f76`, the reply to the [review packet](mvp-m9-plan-review-summary.md)'s
request; the abbreviation resolves uniquely. Q1 to Q19 apply at their
defaults; Q17 was answered before the acceptance by the steering review
the human directed. The same message said `the board is available now`.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted; only this
  section and the status block's trailing lines were set afterwards.
- **Authorization:** M9-2 to M9-6 on branch `beryllium/mvp-m9` from the
  acceptance-record commit, coding on `claude-opus-5.5` sub-agents at
  the pinned effort and context tier under the session's orchestrating
  model, with the open questions at their defaults, under the stop
  conditions; Part 1 Revision 3 as its own exact commit for the human's
  decision (D-8); item 104's premise record (D-6); the claim's sentences
  as D-9 fixes them, taking effect through the result's acceptance; the
  reading of S3-C.5's "CEL-JSON" as the Beryllium log profile (Q7).
  Nothing else: no board command but Q31's (the human's read-only probe
  on the template; one correlation boot at M9's images in a scheduled
  session), each after the human confirms the board free and with the
  human present; no push, merge, tag, publication, snapshot refresh, or
  kexec use; nothing of M8's lane or of M10. The instruction directed no
  fast-forward or push: the development branch stays at `55047781` (the
  M8 line's push record, which this branch took by merge before the
  acceptance record) and this branch is local.
- **The board:** the human's `the board is available now` satisfies the
  shared-board confirmation gate for M9's Q31 steps when M9 reaches them
  (the probe is the human's own, whenever convenient; the correlation
  boot needs M9-3's and M9-4's images and a scheduled session); no board
  command is issued without announcing it first and the human present.
- **Part 1 Revision 3** (D-8) was proposed at exact commit `4bc079db`
  and accepted by the responsible human on 2026-11-03 (`accept
  4bc079db`; `security-model-v1-revision-3-review-summary.md` is its
  review and acceptance record).
- **Erratum 1 (stop 8, the soft limit):** at the checkpoint after M9-3,
  with M9-4's branch in view, about 7,900 counted lines stood against the
  6,000 of "Soft limits"; on 2026-11-03 the responsible human re-set the
  limit to **10,000**. 9,812 at the result's gates commit `dc07f7d3`.
- **Stop 2, decided `fix now` (2026-11-03):** M9-3's QEMU suites found a
  race in M0's probe fixture (`mvp/src/mvp-probe.c`: one shared IPI
  receipt count zeroed by hart 1's V=1 phase before hart 0 read it for
  its HS line; `delivered=0` once in 25 Clang `probe-platform` runs). The
  human chose to fix it in M9 as a found-and-fixed fixture defect, with a
  host test that fails on the old code (`75459737`, merged `8f6660ab`).
- **Erratum 2 (Q13):** D-7 and Q13 cite Amutable's "one public primary
  document" as "Introducing Amutable Foundations", 2026-09-03. Amutable
  dates "Building New Secure Foundations" 2026-09-03 and "Introducing
  Amutable Foundations" 2026-10-22; the citation joins the second's title
  to the first's date. The crosswalk takes the 2026-09-03 post as the
  primary document and reads the 2026-10-22 post as the same approach in
  full, both by URL and date. Recorded here on the result's acceptance;
  the plan text below is not edited (`mvp/README.md` item 119).
- **The result:** the responsible human accepted the M9 result at exact
  commit `892b68c81dace15d2357e034e859b3eccd130abc` (over the gates'
  commit `dc07f7d3`) on 2026-11-03 by the instruction `accept 892b68c8`
  ([the result review summary](mvp-m9-result-review-summary.md) is its
  review and acceptance record; [the evidence record](mvp-m9-evidence.md)
  the evidence), with the departures the packet's section 5 names (the
  profile's ten choices as version 1, Q7's reading, the two harness
  fixes outside M9's packages, items 93 and 120). The claim's sentences
  as D-9 fixes them, with the slots filled from the recorded outcomes
  (R2 kept; no probe performed as of 2026-11-03; the correlation boot not
  run), take effect. No fast-forward, push, board step, or successor was
  directed; the probe and the correlation boot (Q31, Q10) stay the
  human's to schedule.

## Status

```text
m9_status=accepted
m9_plan_target=4f4a8f760a1ed7e5f9886b4e02e94b7a849bfc33
m9_plan_parent=d470fb7f
m9_acceptance_instruction=accept-4f4a8f76
m9_acceptance_date=2026-11-03
m9_acceptance_record=mvp-m9-plan-review-summary.md
m9_open_questions_answered=Q17-steering-review-directed;Q1-Q16-Q18-Q19-defaults
m9_authorization=M9-2..M9-6-on-beryllium/mvp-m9-from-the-acceptance-record;2026-11-03;Part-1-Revision-3-as-own-commit;item-104-premise-record;no-ff-no-push-directed
m9_implementation_branch=beryllium/mvp-m9
m9_board_availability=the-human's-the-board-is-available-now-2026-11-03;Q31-steps-when-scheduled;announced-first;human-present
m9_first_candidate=86f1c68b78e2d36920ea53721ce80bbb91a7328b;superseded-2026-11-03
m9_steering_review=gpt-6-astra;2026-11-02;Q17-answered-by-the-human;B1-B5-incorporated;text-in-mvp-m9-plan-review-gpt-6-astra.md
m9_plan_branch=beryllium/mvp-m9-plan
m9_plan_base=6fbcc3d1;the-M8-acceptance-record;descendant-of-dev-tip-6105c34d
m9_governing_text=mvp-plan.md-S3-C.5;S3-C.7-M9-lane-and-pre-authorization;S3-C.8-D20-stop-1-amended-stops-a-c-d-e;Q31-Q38-Q39-Q40-Q41-defaults
m9_work_packages=M9-1..M9-6
m9_open_questions=Q1-Q19-defaults;Q17-answered
m9_soft_limit_lines=6000
m9_board=qemu-evidence;the-human's-read-only-probe-counted-as-board-time;one-correlation-boot-folded-into-the-next-scheduled-session
m9_claim_change=the-measurement-clause-and-the-required-limit's-two-additions;fixed-words-below;S3-C.7
m9_authorization_if_accepted=M9-2..M9-6-on-beryllium/mvp-m9-from-the-acceptance-record;Part-1-Revision-3-as-its-own-exact-commit;item-104's-premise-record
m9_part1_revision_3=accepted-4bc079dbb96540cb44008a53df857701696e9bad;2026-11-03;instruction-accept-4bc079db;record-security-model-v1-revision-3-review-summary.md
m9_erratum_1=soft-limit-re-set-10000;2026-11-03;stop-8-at-the-M9-3-checkpoint;9812-at-dc07f7d3
m9_stop_2_decision=fix-now;2026-11-03;probe-IPI-count-race-mvp-probe.c;75459737-merged-8f6660ab;tests/probe-test.c
m9_erratum_2=Q13-citation-title-of-the-2026-10-22-post-with-the-date-of-the-2026-09-03-post;recorded-2026-11-03;plan-text-unedited;item-119
m9_result=accepted-892b68c81dace15d2357e034e859b3eccd130abc;parent-461e9e6f;gates-commit-dc07f7d302e01fb622b53e268f2182c991b0f3e6;2026-11-03;instruction-accept-892b68c8;record-mvp-m9-result-review-summary.md;evidence-mvp-m9-evidence.md
m9_result_gates=seven-PASS-at-dc07f7d3;2026-11-03-20:33-21:04-UTC;main-checkout-clean;evaluate-339-of-339-identical
m9_result_board=probe-not-performed;correlation-boot-not-run;no-board-command;claim-slots-say-so
m9_result_departures=profile-ten-choices-version-1;Q7-reading;probe-race-fix;item-93-window;item-120-bundle;erratum-2-Q13
m9_result_push=none-directed;dev-at-55047781;branches-local
```

## Purpose

Make the launch identities the monitor records explicit, per platform,
in a log a researcher can read and the checker verifies against the
build, and be honest about the bottom: on this board no root of trust is
characterized, SPL, OpenSBI, and U-Boot are unmeasured, the loader offers
an MD5 and nothing better, and nothing here is a chain of trust. Today
the monitor computes one SHA-256, over `anchor`'s protected domain's
kernel Image, device tree, secret page, and the build's configuration
identity, compares it with a value baked into the image before any hart
starts, prints it once, and repeats it when that domain terminates; the
other domain and the other two scenarios measure nothing, the sealed
configuration's core identity is printed by its first sixteen hex digits
and checked offline only by that prefix, and U-Boot's MD5 of the loaded image is the checker's attribution of a board
run to its image. After M9 hart 0 keeps a **bounded, versioned log page**
of what it measured and of the identities the build recorded, extends
one **measurement register** per stream, prints the page losslessly, and
gates each domain's entry on its own launch register; a **post-link
reference manifest** per image says what every record must be; the
checker rebuilds the page from the lines, replays the registers, and
compares every record with the reference; the loader observation and the
human's dated platform probe stand beside the log as separate evidence
classes, never merged into it. The claim gains the measurement clause
S3-C.5 fixes in content and this plan fixes in words; "measured boot",
"attested", and "secure boot" stay forbidden. Attestation is MVP 2.0's.

## Inputs

| Input | Exact commit | Role |
| --- | --- | --- |
| MVP plan with Plan revisions S3-A, S3-B, S3-C | `93967fba`; `0d134bbc`, `f8b77ac9`, `27d2e557` | M9's definition (S3-C.5), D20, the M9 pre-authorization (S3-C.7), stop 1 as amended and stops (a), (c), (d), (e) (S3-C.8), Q31, Q38 to Q41 at their defaults |
| M2 plan and result | `854a5415`, `18d552bc` | the measurement as it is (Q7), the secret page, the management path |
| M5 plan and result | `0066794d`, `3867c66c` | the board policy, the loader's `md5sum` as attribution, the one-boot-per-run rule |
| M6 result (release candidate 3) | `89ef04e9` | the core profile and its identity at boot, the executor, the layer table |
| M7 result | `e1a6395e` | the input ring and markers `:15` to `:18`; the `shell` variants |
| M8 plan | `7a0c74ae` | stage 1 abstracts the measurement as a gate only; the re-proof rule M9's header changes trigger at RC4 |
| Debt sweep 4 | `d162c60d` | the one-autoboot rule (item 100), M9's prerequisite, done |
| Security model v1 with Revisions 1 and 2 | `0e3eec8b`, `019cca64`, `afd395b8` | Part 1, which M9 revises additively (Revision 3) |
| Implementation plan, milestone 7; the hardware roadmap | maintained planning documents | the gate items M9 discharges or defers; "Secure boot and lifecycle"'s disposition question |
| TCG algorithm registry; TCG canonical event log (CEL); `systemd-pcrlock` | external specifications | the algorithm identifier (SHA-256 `0x000B`), the export shape, the reference-manifest shape |

## Facts the design rests on (read-only findings, 2026-11-02)

Every fact was read in the tree at `6fbcc3d1`; the line numbers are that
tree's.

- **One measurement, one domain, one hash.** `measure()`
  (`mvp/src/mvp-runtime.c` L1440-L1495; its contract L1428-L1439) is
  compiled only for v3 scenarios (`BE_MVP_RUN_PAGES`, L106-L116), called
  once after the placements and before `publish_blocks()` and
  `start_run()` (L2447-L2455), never in probe images, and hashes, in
  order, the measured domain's kernel Image as placed, its 4 KiB device
  tree as placed, the secret page as placed, and the 32 bytes of the
  baked configuration identity (L1459-L1471), into
  `be_mvp_measurement` in hart 0's MVP-region BSS (L318-L320). The
  expected value is `BE_MVP_SCENARIO_MEASUREMENT`, computed by
  `tools/policy-check.py`'s `measure()` (L788-L798) over the build
  outputs and written by `tools/gen-scenario.py` (L1531-L1534); a
  mismatch prints `BE_MVP:DETAIL … computed= expected=` and fails the run
  as `measurement` before any hart starts (L1480-L1490);
  `wrong-measurement` flips bit 0 of the expected value's first byte
  (L1475-L1477). Only `anchor` declares a measurement, of domain 1
  (`mvp/scenarios/anchor/scenario.json` L77); `te-poc` (v2) and
  `two-guests` (v1) have none. The digest is printed in `BE_MVP:06
  MEASURED domain= hart= bytes= sha256= expected=match ticks=` (L453-L455)
  and again in the measured domain's `BE_MVP:12 DOMAIN_TERMINATED …
  sha256=` (L543-L546, L1902-L1921).
- **Two identities, neither a measurement of bytes.** The **core
  identity** `CONFIG_SEALED` prints is `be_mvp_core_identity()`
  (`mvp/src/mvp-core.c` L30-L109) over the sealed inventory's and
  proposal's canonical fields (`mvp-core.h` L36-L46), computed at boot by
  `seal_config()` (L921), printed as its first eight bytes (L929), and
  **not compared at runtime**; its printed sixteen hex digits are embedded
  by the generator in the expected `CONFIG_SEALED` line
  (`tools/gen-scenario.py` L1078-L1084) and matched by the checker's line
  regex (`tests/check-capture.py` L833-L840), so the prefix is checked
  offline and the full digest is printed nowhere (the review's correction
  of the first candidate's "compared with nothing"). The **configuration
  identity** the image bakes
  is `policy-check.py`'s SHA-256 of the manifest, policy, and labeling
  identities' hex digests (`identities()` L646-L660), input 4 of the
  measurement, printed in full on `CHANNEL_CHECKED` and `PAGE_CHECKED`.
  Neither covers the console grant (`mvp-core.h` L82-L84; item 108); the
  ported R1 identity does and is not printed. The kernel's and DTBs'
  bytes enter only the measurement.
- **SHA-256 is in the monitor already.** `mvp/src/mvp-sha256.c` (249
  lines; FIPS 180-4) with `init`, `update`, `final`, a one-shot, and
  HMAC (`mvp-sha256.h` L46-L83), linked into the MVP region; "no key is
  held here" (L14-L16). `mvp/tests/sha256-test.c` holds the FIPS and
  RFC 4231 vectors (U-10's note).
- **The checker's side.** `tests/check-capture.py` recomputes the
  measurement from `--kernel` and `--dtb`, the secret page, and the
  report's configuration identity (`measurement_value()` L1888-L1915)
  and requires `MEASURED`'s `expected=match` literal (L609-L611), the
  measured domain's `DOMAIN_TERMINATED` digest, and, for
  `wrong-measurement`, a `DETAIL` whose `expected` differs from
  `computed` in exactly one bit (L1918-L1956); `tools/platform-record.py`
  renders "The measurement" (L1358-L1377) from one row per `anchor` run.
  The authority report carries `measurement` and `measurement_hex`
  (`policy-check.py` L861-L864); it is pre-link.
- **Loader attribution as it is.** `be_ld` runs `load … && md5sum
  0x140000000 ${filesize}` (`tools/k3-env.sh` L91); `k3-stage.sh` records
  each staged image's SHA-256, MD5, and CRC32 and requires distinct MD5s
  (L111-L133); `k3-uboot.py attribution` accepts at most one `Autoboot
  in` line and requires the `N bytes read` and `md5 for … ==> D` lines
  after it to equal the staged size and MD5 (L404-L425; item 100 closed
  by debt sweep 4); `k3-run.sh` dies before any launch if the staged
  SHA-256 is not the local image's (L262-L263), then writes
  `attribution=PASS selected= staged_sha256= size_md5= check=` (L347),
  where `staged_sha256=yes` is a **literal**, true only because the die
  came first (a wording to make computed; item 116). The U-Boot
  rehearsal's witness is `crc32`; direct QEMU boots have none.
- **The U-Boot `help` listing exists under `build/`, not in the tree.**
  Attempt 7's `help.txt` (117 commands, CRLF, SHA-256 `ca42cbc5…`) and
  attempts 4 to 6's listings all show `crc32` and `md5sum` and none of
  `hash`, `sha1sum`, `sha256sum`, `tpm`, or `verify`; the same session
  recorded `U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build:
  jenkins-BSP-build-bsp-deb-395` and `md5 for 140000000 ... ==>` (item
  104's premise).
- **The firmware is identified, never measured.** The preflight requires
  `SBI implementation ID=0x1 Version=0x10006` from Fedora's log
  (`tools/k3-preflight.sh` L263-L282) and hashes only `env_k3.txt` (227
  bytes), the partition UUID, and the `k3ctl` client; the platform record
  compares the SBI identity and the Fedora kernel with M0's record and
  counts the U-Boot banners (`platform-record.py` L340-L364); no digest of
  SPL, OpenSBI, U-Boot, or the board's device tree exists anywhere.
- **Markers and room.** `BE_MVP:00` to `:18` are in use (nineteen); the
  MVP region holds `0xada0` of its `0x40000` bytes at its fullest (Clang
  `anchor`, M7-3), so a 4 KiB page in hart 0's MVP-region BSS fits with
  its alignment; that BSS lives inside the `.mvp.data` output section
  between `__be_mvp_bss_start` and `__be_mvp_bss_end`
  (`mvp/src/mvp-monitor.lds` L209-L244; there is no `.mvp.bss` output
  section, a terminology error of the first candidate). Hart 0's work
  before the barrier is uncounted in `exits`, `records`, and `wakes`; a
  retained RC3 `anchor` run spent `0xc81d8` ticks (34.2 ms at 24 MHz) on
  M2's measurement of a 1,907,940-byte Image
  (`mvp/results/20261031-com260-rc3/20261031T042103Z/handoff-excerpt.log`
  L45); the current Image is 2,063,556 bytes (`mvp/guest/pins.txt` L50),
  and at 115200 baud each KiB of new console text costs about 89 ms.
- **The monitor's read-only ranges are fixed by the link.** The monitor
  linker script places `.monitor.text`, `.monitor.rodata`, and the
  generated `.monitor.input` (the inventory and proposal) and the MVP
  region's text and rodata at fixed addresses and discards dynamic
  relocation sections (`mvp/src/mvp-monitor.lds` L35-L81, L175-L207,
  L273-L277); the boot layout fixes the flat monitor at image offset
  `0x1000` (`mvp/src/mvp-boot.lds` L76-L82), so a post-link reference for
  R2's ranges needs no self-hash fixed point; whether the two toolchains'
  ranges reproduce exactly is M9 work (Q4), not a fact here.
- **The claim's words.** `claim.md` says "the protected domain's
  measurement stayed unaltered" (L25-L33), "the measurement are covered
  by host tests … and by nothing else" (L69-L74), and "The measurement is
  a local identity, not attestation" (L81-L82); its forbidden literals
  include `attested`, `secure boot`, `measured boot`, `verified boot`,
  and `remote attestation` (L102-L119), matched with hyphens and spaces
  equivalent; "chain", "lowest stage", and "measured identity" are not in
  the list, so S3-C.5 keeps them out by fixing the content here. Ledger
  rows C-08, C-16, U-10, and U-12 speak of the measurement; U-10's
  coverage is `host unit test`, `semantic checker`.
- **The hardware roadmap's disposition question** ("MVP planning decides
  whether secure boot is a required profile or documented platform
  assumption", `planning/riscv-security-hardware.md` L111) is open, and
  the implementation plan's milestone 7 gate is "document roots of
  trust, replay/update behavior, and vendor assumptions"
  (`planning/implementation-plan.md` L2090-L2096).

## Design

### D-1 The log page: hart 0's, bounded, versioned, canonical

A 4 KiB page in hart 0's MVP-region BSS, `be_mvp_log`, 4 KiB aligned
and wholly inside `__be_mvp_bss_start..__be_mvp_bss_end` (both checked by
the image checker), zero-initialized, written by hart 0 alone before the
barrier and read by no domain hart (I15's rule; Revision 3's asset), with
**no timing field**, and beside it the four registers,
`be_mvp_log_registers` (128 bytes, hart 0's BSS, outside the page). The
encoding is **explicit** (every field written and read by width at a
fixed offset, little-endian; never a C structure's native layout; every
unused byte canonical zero), written down in `mvp/docs/log-profile.md`
(M9-2) and checked by `tests/log-test.c` offset by offset and by a
host-side rebuild of the whole page byte for byte:

- **Header** (128 bytes; the first candidate's 64 could not hold its
  two 32-byte identities, the review's B1): offset 0 the magic
  `BEMVPLOG` (8 bytes); 8 the version `1` (u16); 10 the header length
  `128` (u16); 12 the record length `96` (u16); 14 the capacity `41`
  (u16; records, the close included); 16 the count (u16; records
  appended, the close included); 18 the state (u8: `0` open, `1`
  closed, `2` overflow); 19 reserved (u8, zero); 20 the algorithm
  identifier from the TCG registry (u16, `0x000B`, SHA-256; the only one
  in 1.0); 22 reserved (10 bytes, zero); 32 the scenario's SHA-256 (the
  generator's `scenario_sha256`, 32 bytes); 64 the build's configuration
  identity (32 bytes; all zero with the `policy-absent` record present,
  below); 96 reserved (32 bytes, zero).
- **Records** (96 bytes each, at `128 + 96·i`; `128 + 41·96 = 4,064`,
  the page's last 32 bytes zero): offset 0 the sequence (u16, from 0,
  equal to `i`); 2 the producer (u8: `0`, hart 0, the only producer in
  1.0); 3 the type (u8: `1` measured, `2` informational, `3` close); 4
  the stream (u8: `0` platform and monitor, `1` configuration, `2`
  domain 0, `3` domain 1; `0xff` for the close); 5 the object (u8, an
  enumeration: `monitor-text`, `monitor-rodata`, `monitor-input`,
  `mvp-text`, `mvp-rodata`, `core-identity`, `console-grants`,
  `configuration-identity`, `policy-identity`, `policy-absent`,
  `kernel-image`, `device-tree`, `secret-page`, `close`; the numbering in
  `log-profile.md`); 6 the representation (u8: `as-placed`,
  `as-computed`, `build-recorded`, `none` for the close); 7 the outcome
  (u8: `recorded`, `gated-pass`, `gated-fail`, `none`); 8 the range base
  (u64) and 16 the range length (u64; both `0` for a build-recorded or
  computed value); 24 the digest length (u16, `32`); 26 the per-stream
  record number (u16, from 0 within the stream; the TCG event log's
  per-index numbering, kept beside the global sequence for the export);
  28 the close's expected count (u16; `0` in every other record); 30
  reserved (u16, zero); 32 the digest (32 bytes; zero for `policy-absent`
  and the close, whose meaning is the object enumeration, never an
  "absent" hash); 64 reserved (32 bytes, zero). Every image's expected
  count is at most 15 (`anchor` with R2 kept: five R2 ranges, four
  configuration records, five launch objects, and the close; Q2), so
  the page never fills; appending when `count = capacity − 1` without a
  close is overflow.
- **Registers**: four, one per stream, `R := SHA-256(R || digest)` from
  zero, extended by `measured` records only; `informational` records are
  typed as such and never extend; stream 0's register stays zero when R2
  is dropped (Q4) and says so. The recurrence commits to each stream's
  ordered digest values and to nothing else: not to a record's object,
  range, type, or header, nor to the interleaving across streams; those
  are bound by the checker's field-by-field comparison with the
  reference (D-4), and the close record is structural, not
  cryptographic. Printed at the barrier and before the run's terminal
  marker (`BE_MVP:14`, not after it, where capture tools stop), called
  **registers**, never PCRs.
- **Close**: a `close` record before the first domain's start, carrying
  the expected count in its field; after it hart 0 appends nothing and
  the page's state is `closed`. **The global rule:** every required
  launch comparison succeeds and the log closes before `BE_MVP:07` and
  before any HSM start, or no domain hart starts: overflow or a page that
  cannot close fails the run (`BE_MVP_CLASS_LOG`, a new class; D-2's
  table names each image's terminal prefix); a duplicate, omission, or
  reordering is the checker's finding.
- **Rendering**: each header field, each record's every field (the
  reserved ones as zero), the close, and the registers are printed as
  hart 0's lines `BE_MVP:19 LOG …` and `BE_MVP:20 REGISTERS …` (Q3),
  losslessly: the checker rebuilds the page's **canonical
  representation** from the lines (the printed fields are the
  observation; the page's padding is covered by the host test's
  byte-for-byte rebuild, not by the lines); the lines are the rendering,
  the page is the log. Records are accepted by the checker only from
  hart 0's unprefixed stream; a `BE_MVP_G<d>:` line can never be a
  record. The image checker's `HART0_ONLY` reachability rule extends to
  the page and the registers, with negative cases.

The log and register code is pure restricted C in new `mvp/src/mvp-log.c`
and `mvp-log.h` (append, close, extend, render into the line builder),
host-tested over captured inputs with GCC = Clang (`tests/log-test.c`:
every offset and width of the encoding above, every field's value, the
sequence and count, the close's expected count, the reserved bytes zero,
overflow when the 41st slot would be a data record, the register
recurrence against `mvp-sha256.c`, the stream-0 register's zero when R2
is absent, and the rendering's losslessness through a host-side rebuild
compared with the page byte for byte).

### D-2 The records per image class (R1 to R4)

| Record | Computed by | Over | Expected value from | Compared by, when | Mismatch |
| --- | --- | --- | --- | --- | --- |
| R1 loader attribution | U-Boot (`md5sum`) on the board; `crc32` in the rehearsal; none in direct QEMU | the whole boot image as loaded (shim, monitor, kernel Image, both device trees) | the staging record's MD5 and SHA-256 | the checker, per run, as today (M5's rule, item 100's one-autoboot rule) | attribution `FAIL`; the run is not evidence |
| R2 the monitor's self-measurement | hart 0 at boot | its own text and read-only data as loaded: the accepted core's and the MVP region's text and rodata ranges, by linker symbols | the post-link reference manifest (the same ranges' digests from the boot image) | the checker, offline; **never gates entry** (an expected value inside the range is a fixed point) | a finding (`self-report differs`); the run continues; the negative is a post-link byte flip inside a rodata range |
| R3 the configuration | hart 0 at boot | the core identity's canonical bytes (`measured`, `as-computed`, the digest the core identity is); the configuration and policy identities (`informational`, `build-recorded`); `policy-absent` for `two-guests` | the reference manifest, which binds the report's identities | the checker: the core identity against the generator's `core_identity`, the recorded identities against the report's, **through the reference, never as one hash** | a finding |
| R4 each domain's launch | hart 0 after the placements, before the barrier | each domain's kernel Image and device tree as placed (`measured`, `as-placed`); `anchor`'s secret page as placed (stream 3) | the image's expected launch register per domain, computed by the generator over the same bytes with the same recurrence | hart 0 compares each domain's register with its expected value before that domain's hart starts (`gated-pass`), as M2's gate does; the checker compares each record's digest and the register with the reference | `BE_MVP:FAIL measurement` with both values in `DETAIL`, before any hart starts |

M2's single combined digest (kernel, DTB, secret, configuration identity
in one hash) becomes per-object records and per-domain registers; the
configuration identity is no longer folded into a domain's launch value
(S3-C.5: the checker binds the two configuration identities through the
reference). `BE_MVP:06 MEASURED` becomes `BE_MVP:06 LAUNCH domain=
hart= register=<64 hex> expected=match ticks=` once per domain, in every
Linux-guest image, and `DOMAIN_TERMINATED`'s `sha256=` becomes the
domain's launch register; `wrong-measurement` keeps its name and flips bit
0 of the protected domain's expected register's first byte (Q16). There
is no initramfs object: both domains boot one Image with an embedded
initramfs, and no cpio parser enters HS. R4 hashes the **destination
bytes** of each domain's placement, once per domain even where the two
source Images are one file, the kernel's file length (not the Image
header's memory size), each 4 KiB device tree, and the zero-padded secret
page, as M2's placement rules have them. R3's `core-identity` record
carries the core identity's digest directly (it is a digest already),
with representation `as-computed`, meaning the SHA-256 over the canonical
serialized fields of `mvp-core.h` L36-L46, not over one contiguous range.
**The console grant joins the measured configuration** (item 108; Q18):
a `console-grants` record, `measured`, stream 1, `as-computed`, the
SHA-256 over the sealed configuration's effective per-domain console-input
facts in a fixed serialization the profile states; the generator expects
it from the variant's effective grants, so a `<scenario>-shell` image's
stream-1 register differs from its base scenario's; the core identity
itself is unchanged, so the printed `CONFIG_SEALED` prefixes and the
accepted scenarios' expectations stay.

**The per-image contract** (the review's B2; written down in
`log-profile.md` in M9-2 as a prerequisite of M9-3 and M9-4), per image
class: the required records in order, whether the gate applies, the
completion state the checker requires, and the permitted terminal prefix:

| Image class | Required records (header; then, in order) | Gate | Completion | Terminal prefix the checker accepts |
| --- | --- | --- | --- | --- |
| `two-guests` (v1) and its `shell`/`live` variants | R2 (if kept); `core-identity`; `console-grants`; `policy-absent` (informational, digest zero: the v1 scenario has no authority report, so neither a configuration identity nor a policy identity exists, and the header's configuration identity is zero); R4 for domains 0 and 1 (kernel, device tree as placed, the variant's own DTBs); close | per domain | closed before `:07` | a complete closed log, both `gated-pass` |
| `te-poc` (v2) and its variants | R2 (if kept); `core-identity`; `console-grants`; `configuration-identity`; `policy-identity` (build-recorded, the report's); R4 for both domains; close | per domain | closed before `:07` | a complete closed log |
| `anchor` (v3) and its variants | as `te-poc`, with `secret-page` (stream 3, as placed) after domain 1's device tree | per domain | closed before `:07` | a complete closed log |
| the probe images (M0's and M7's, on `two-guests`' configuration) | header; R2 (if kept); `core-identity`; `console-grants`; `policy-absent`; close; **no R4** (a probe places a synthetic stub and starts domain 0 alone: no Linux launch evidence is claimed and no stub is relabelled an Image) | none | closed before the probe's start | a complete closed log, no `:06 LAUNCH` |
| negatives that fail before the measurement step (`gstage`, `payload`, and their kin) | the header and the records appended before the failure, or none | not reached | `open` | the declared prefix for that negative, exactly, and no close |
| `wrong-measurement` | the log through the failing domain's last launch record with outcome `gated-fail`, then `BE_MVP:FAIL measurement` | fails | `open`; no close; no hart starts | the declared prefix, the `gated-fail` record, the `DETAIL` with both values |
| `self-report-flip` (D-4) | a complete closed log; the `mvp-rodata` record's digest differs from the reference | per domain | closed | a complete closed log, the run to its terminal marker, and exactly the finding `self-report differs: mvp-rodata` |
| a failure after the launch (a domain fails or terminates in the run) | the closed boot log as above; the terminal registers printed before `:14` | passed | closed | the closed log and the terminal registers; the run's own declared lines |

A record the table requires and the log lacks, a record it does not
list, or a prefix other than the declared one is the checker's finding;
the table is the checker's data (the generator writes each image's
expected sequence from it), not prose it reads.

### D-3 The post-link reference manifest, per image

`tools/gen-reference.py` runs after the link, per image and toolchain,
and writes `build/mvp/references/<toolchain>/<image>.json`: the exact
source commit and tree state, the scenario and variant, the toolchain,
the authority report's SHA-256 (where one exists; `two-guests` and the
probes have none and say so), the ELF's and the boot image's SHA-256, the
**measured range table** (each R2 range as a final loaded HPA range with
its checked image-offset mapping, its base, length, and digest from the
boot image's bytes: `.monitor.text`, `.monitor.rodata`, `.monitor.input`,
and the MVP region's text and rodata, by the linker's symbols; BSS,
mutable data, and the shim excluded by name (Q19); each R4 object's
placement and digest from the build's inputs), the expected records in
order with every field of D-1, and the expected register values, in the
**Beryllium log profile** of `mvp/docs/log-profile.md` (D-4; a JSON
profile derived from the TCG Canonical Event Log, not CEL itself: the
review's B5) with a stated **update rule**: regenerated on every build,
never edited, deterministic (no timestamp, no absolute path; the host's
and the evaluator's references compared byte for byte as the images
are), its SHA-256 pinned by the image checker beside the image's, and
copied into every retained record and evidence bundle. The pre-link
authority report stays an input; the build is acyclic: inputs → the
pre-link launch constants and configuration values in the scenario
header → the link and the boot image → the external reference → check and
stage. **Only pre-link values enter the compiled image** (each domain's
expected launch register, the configuration constants); the self-report
digests, the final image's hash, and the reference's hash stay outside
it, so no self-reference enters R2 (Q4). The manifests are build products
under `build/`, not maintained as source (Q6: "never committed" means
not edited or tracked as source; every retained record carries its
copy).

### D-4 The checker: rebuild, replay, compare, export

`tests/check-capture.py` gains a log module: it parses the `:19` and
`:20` lines from hart 0's unprefixed stream, **rebuilds the page**
(header, records, close) and refuses a line set that does not rebuild
(a missing field, a sequence gap, a count other than the close record's,
a record after the close, two producers, an unsupported version, an
algorithm other than `0x000B`, a duplicate JSON key or an unbounded
input in anything it reads), **replays the registers** from the records
and requires them to equal the printed `:20` values (its replay values
labelled `unprotected` in the report), **recomputes every digest
independently** (each R4 object from the build's inputs the record names,
each R2 range from the boot image's bytes at the recorded range, the
core identity and the console grants from the generator's canonical
inputs) rather than trusting the printed digests, compares **every
field** of the header and of every record, and the per-stream record
numbers, with the image's **reference manifest** (`--reference`;
`check-capture.py`'s historical `PINNED_MEASUREMENT` fallback stays for
the retained M2 to RC3 fixtures only and is never a path for M9
evidence), enforces the global rule (every `:19` line and the barrier's
`:20` before `:07`; each domain's `gated-pass` record and `:06 LAUNCH`,
equal to the reference's register, before that domain's `:08
HART_STARTED`; the terminal `:20` before `:14`), requires the per-image
contract's prefix for the image's class (D-2), and exports the rebuilt
log in the **Beryllium log profile** (`log.json` in the run record).
**The profile (Q7; the review's B5)** is a JSON profile **derived from**
the TCG Canonical Event Log Format, version 1.1 revision 11 (2025-10-09;
the document's SHA-256 recorded in `log-profile.md`), not a conforming
CEL: CEL's `recnum` is per index and its `pcr` field is an index into a
TPM's banks, where the profile carries a global sequence and a
per-stream record number and names a software `register`; `log-profile.md`
maps every profile field to CEL's or lists it as unmapped (the header
and close records, the per-stream numbering, the content type, the
outcome, the representation), states the software-register
interpretation, and claims no interoperability with any TPM-facing tool
(systemd's `.pcrlock` files use `pcr` and `digests`, systemd v259, and
are not read or written). S3-C.5's "CEL-JSON" is read as this derived
profile; the reading is recorded for the human's acceptance like M3's A8
interpretation. A round-trip test (page → lines → rebuild → profile →
rebuild) is part of the checker's self-test. R1 stays in the run record
(`attribution=`; the `staged_sha256` field computed from the recorded
comparison, item 116) and never enters the page or the export; MD5 has
no registry entry.

**The negatives** (S3-C.5's exit requires a wrong digest at **each**
record the monitor controls, and the review's B3 requires an oracle that
does not move with the defect): (1) checker mutations of the retained
and regenerated captures with the **reference frozen** (omission,
duplication, reorder, a wrong producer, object, algorithm, range,
representation, or outcome, an unsupported version, truncation and
overflow, a register that does not replay, a wrong reference image,
toolchain, or variant, a false platform-fact binding, a forged loader
block); (2) **metadata-only mutations the registers cannot see** (a
type or stream changed with the digests kept, two records of different
streams swapped, a forged close and count pair, a record moved after the
first `HART_STARTED`, the terminal registers changed, a guest-prefixed
look-alike of a `:19` line), each of which the field comparison must
catch; (3) **a wrong digest at each monitor-controlled record** as a
capture mutation whose printed registers are recomputed so that the
replay passes and only the reference comparison fails: domain 0's and
domain 1's kernel, each device tree, the secret page, the core identity,
the console grants, and each R2 range; (4) an overflow case showing the
start is not reached; and (5) two image variants: `wrong-measurement` as
D-2 redefines it (Q16) and `self-report-flip`, whose recipe is
deterministic and mechanical: the variant tool flips one bit of a named
inert 16-byte constant `be_mvp_log_canary` in the MVP region's rodata
(no other use; a string, pointer, policy, or SHA-256 constant is never
chosen) after the link; the reference stays the **nominal** build's, and
the variant's generated metadata records the mutated artifact's SHA-256
beside it (`mutated_image_sha256`), so the checker expects the image
hash to differ by that record and the `mvp-rodata` self-report to differ
by exactly that range; the run must reach its terminal marker and the
checker must report exactly `self-report differs: mvp-rodata` and no
other finding; there is no "ignore image mismatch" option and no
hand-edited reference. The platform record gains one section per stream
with the registers across runs and the self-report's comparison.

### D-5 IMA is never used, made testable (D20)

Three checks, each with a negative case: the guest configuration delta
check (`tools/guest-pins.py`) asserts that no Beryllium-built guest
`.config` sets `CONFIG_IMA` (or `CONFIG_IMA_*`, `CONFIG_EVM`); the
checker accepts only the profile's **allowed** record objects and content
types (an allowlist, D-1's enumeration; an IMA measurement list, an
`ima_template` content type, or any name outside the enumeration is
refused, as is a reference manifest naming one); and the ledger's
boundary row says the monitor measures only what it places or seals
before entry. The measurement is of images,
configuration, and policy at the domain boundary, never of files inside
a guest.

### D-6 The loader observation and the platform observation stay beside the log

- **R1** is the checker's, board-only, by an unmeasured U-Boot identified
  by its banner; binding the MD5 to the staged SHA-256 does not upgrade it.
  Item 104's premise record is committed as
  `mvp/results/20261030-uboot-help/` (attempt 7's `help.txt`, `version.txt`,
  and `be_ld.txt` as retained, with their SHA-256s and a `README.md`
  stating what they show: `crc32` and `md5sum` present; `hash`, `sha1sum`,
  `sha256sum`, `tpm`, and `verify` absent) in M9-2. The NOR is not
  rewritten to gain a SHA command (Q38).
- **The platform observation** is the human's read-only probe of the
  board's lifecycle and debug state (Q40): TAP and Debug Module status,
  no halt, no write, outside the tools, recorded on the template
  `planning/mvp-m9-platform-probe.md` (board and probe identity, the
  tool and its version, the exact commands, the raw capture's SHA-256,
  the date, whether an adapter stays attached during evidence runs, and
  one of four outcome classes: Debug Module reachable without
  authentication; authentication required; TAP answers but no Debug
  Module; no connection, cause unknown, **never** recorded as "locked";
  `not determined` is an honest outcome with a disposition). The outcome,
  dated, is a platform assumption in the record and in the claim's
  required limit; it is board time, counted (Q31), and the human's own.
  The **boot-authentication disposition for 1.0** is a documented platform
  assumption (the hardware roadmap's open question answered for MVP 1.0):
  the board runs the vendor's SPL, OpenSBI, and U-Boot from NOR as
  installed; whether the boot ROM authenticates SPL is what the probe and
  the vendor's documentation say, recorded with the date; nothing in 1.0
  depends on it, and the words "secure boot" stay out of release surfaces.

### D-7 The analysis deliverable (Q39: analysed, not implemented)

`planning/mvp-m9-crosswalk.md`: a requirements crosswalk among (a) a later
minimal vTPM with a standard TCG event log, (b) a Beryllium per-domain
measurement-register SBI extension a guest extends and the monitor logs,
and (c) a lossless adapter from the Beryllium log profile to the TCG and
systemd model (`systemd-pcrlock`, `systemd-measure`, `systemd-pcrphase`,
UKIs), mapping for each of `systemd-pcrlock`, `systemd-measure`,
`systemd-pcrphase`, and UKIs the artifact boundaries, the event and
phase semantics, the reference generation and update rule, reset and
replay, and the verifier's trust (systemd pinned at v259, its
`systemd.pcrlock` manual by URL); what the reference manifest already
supplies; what attestation with a simulated root (2.0) needs from the
log (a key, a monotonic counter, registers; the protocol and freshness);
how a guest's own IMA stays out of Beryllium's evidence under (a) and
(b); where the implementation plan's milestone 7 runtime
integrity-monitor experiment belongs under D20's line; and which of
milestone 7's gate items M9 discharges ("document roots of trust,
replay/update behavior, and vendor assumptions": the roots documented as
absent, the replay and update rule stated, the vendor assumptions dated)
and which it defers. Amutable's image- and configuration-as-artifact
approach is design input from one public primary document ("Introducing
Amutable Foundations", 2026-09-03, cited by URL and date; Q13), from
which the crosswalk records one adopted, deferred, or rejected lesson
with the reason it fits or not this non-UEFI, non-TPM monitor; its
product assurances do not transfer. The crosswalk is a deliverable
specification of what was compared, not analysis already done. No claim
of stock systemd compatibility until a TPM-facing interface and adapter
exist.

### D-8 Security model v1 Part 1 Revision 3 (additive; its own exact commit)

Stop 1 as S3-C amended it admits an additive Part 1 revision carried by
this plan, as its own exact commit for the human's decision: the log
page and the registers as **instances of Part 1's existing `measurement`
asset** (security model v1 L117-L128; no new asset class), named by
their storage (hart 0's MVP-region BSS), owned by hart 0 by phase
(written before the barrier, read by no domain hart, I15 and I16;
excluded from every domain's window and shared page under I2; integrity
with no secrecy, the test secrets being public, and no generalization of
"no secrecy" to a future low-entropy secret or confidential policy); the
reference manifests, the generator, and the checker's replay as the
**offline evidence TCB**, distinguished from the running TCB; U-Boot's
loader observation and the human's platform probe as trusted inputs and
dated assumptions, the probe a human input and not HS code; the
self-report's limit (a consistency witness, not evidence against an
adversary who alters the monitor; "read by no domain hart" is a
code-discipline claim within HS, not hardware protection, so U-12 stays
open); two invariants, **I19** (hart 0 alone writes the log, before any
domain hart starts, and closes it with the expected count; no record
follows the close) and **I20** (no domain hart starts unless every
required launch comparison has **succeeded** and the log is closed; each
domain's launch records and its gate's comparison precede its
`HART_STARTED`); and the TCB rows. The earlier text stays byte for byte
and the new obligations are marked unproved, as Revisions 1 and 2 do.
Model 0.2 and M3's modules are not edited (stop (e)); M8's stage 1
abstracts the gate as a predicate, as S3-C.4 says: a pure pre-start
measurement subroutine fits its `launch gate`, the log's close adds a
start condition the predicate must carry, and hart 0's new writes map to
its private-state footprint; the correspondence is re-read at
integration (M10's re-proof rule), and I19 and I20 are specification,
not M8 proofs of the logging.

### D-9 Claim text (pre-authorized by S3-C.7; fixed here)

The claim's blockquote in `mvp/docs/claim.md` gains, after M7's console
sentence, one sentence:

> For the Linux-guest runs the ledger identifies, before any domain
> runs, the control hart records in a bounded log the digests it computes
> over what it placed or sealed on that platform (the sealed
> configuration's core identity and console grants, each domain's kernel
> Image and device tree as placed, and `anchor`'s secret page) and the
> identities the build carries, extends one register per stream with the
> measured records' digests only, and compares each domain's launch
> register with the image's expected value before that domain starts; the
> checker rebuilds the log from its printed lines, replays the registers,
> recomputes every digest from the build's inputs, and compares every
> record with the image's post-link reference.

The required limit's sentence "The measurement is a local identity, not
attestation." is replaced by:

> The log is a local identity, not attestation: it has no key, nonce,
> freshness, or root of trust, so code able to alter the monitor can
> fabricate its records, and a record does not show the bytes unchanged
> after the point of measurement; `<self-report clause>`. On the board,
> U-Boot, identified by its banner and unmeasured, prints an MD5 of the
> loaded boot image, which the checker holds as attribution of the run to
> its image and as nothing more; no loader observation exists in direct
> QEMU boots, and the U-Boot rehearsal records a CRC-32 separately. SPL,
> OpenSBI, and U-Boot are unmeasured. `<platform clause>` `<board
> clause>`

The slots are filled only from the recorded outcome, each from a fixed
pair of forms, so that every permitted outcome of this plan has true
words (the review's B4; the forms are part of this pre-authorization and
choosing between them is not a claim change):

| Slot | When | Fixed form |
| --- | --- | --- |
| `<self-report clause>` | R2 kept (Q4) | "the monitor's digest of its own text and read-only data is a self-report, compared offline and gating nothing" |
| | R2 dropped | "this profile omits a monitor self-report" |
| `<platform clause>` | the probe performed | "The board's lifecycle and debug state is a dated platform assumption from one read-only probe (`<date>`: `<outcome class>`), not a per-boot fact." |
| | not performed | "The board's lifecycle and debug state were not determined as of `<date>`; no probe was performed." (`not determined` after no attempt is distinct from an inconclusive attempted probe, whose outcome class says so) |
| `<board clause>` | the correlation boot run at M9's images | "" (the ledger's board column names the exact images and the run) |
| | not run | "The log and launch-gate evidence is from QEMU; the M9 board correlation has not run." |

The claim's opening "In QEMU and on one … board" is thereby qualified for
the log by the board clause until the correlation boot runs at M9's exact
images; a ledger `not run` entry alone would not qualify it. The words
"chain", "lowest stage", "measured identity", "measured boot",
"attested", and "secure boot" do not appear; the forbidden-phrasing check
must pass; any other claim change is stop (d). The restated C-08 and C-16
keep their historical meaning: "the measurement stayed unaltered" is the
stored digest read again at termination, not a second hash of live guest
memory.
The ledger gains claim rows for the log and the registers, the launch
gate per domain, and the self-report (methods: host unit test,
adversarial test, semantic checker, emulation; the board column only
after a board run at M9's images), restates U-10 and U-12 and C-40's
non-claim as needed, and adds a boundary row for R1 and the platform
observation.

### D-10 Board evidence (Q31) and the lanes (S3-C.7)

QEMU evidence is the gate: every image's log lines judged against its
reference with both toolchains, the U-Boot rehearsal's CRC-32
attribution unchanged. The human's probe is board time, the human's own.
One bounded **correlation boot** (one `anchor` run at M9's images, its
log, registers, and MD5 attribution judged) is folded into the next board
session the human schedules, release candidate 4's campaign by default
(Q10); until then the board column reads `not run`, the loader
attribution at M9's images is recorded as absent, and D-9's board clause
stands; no board-supported M9 sentence appears before that run's
exact-image evidence exists. **Cost is measured, not assumed:** hart 0's
hashing time (`ticks=` per `LAUNCH` line and a total in the `:20` line)
and the new console volume (bytes of `:19`/`:20` text per image) are
recorded in every run and in the evidence record, separately from the
canonical page; the hashing and the complete initial rendering precede
the barrier and the operational budget's arming, so the host boot
timeouts and any watchdog behaviour are checked against them in QEMU and
in the correlation boot. M9 changes `mvp.h`,
`mvp-layout.h`, and `mvp-runtime.c`, the headers and files M8's leaves
and stage 1 read: S3-C.7's merge-order rule and stop (i) apply, and M10's
gates run every M8 proof again at RC4's exact tree before any pin is
re-derived; M9 neither edits M8's files nor waits for M8.

### D-11 What stays the same

The accepted scenarios' counts in QEMU are judged as the capture checker
judges them today, no more and no less: the counts it requires equal
(`exits`, `records`, `denials`, and the others it pins exactly) must
stay equal, and the timing-dependent ones it bounds (the alternation
floor) must stay within their bounds; hart 0's measurement work is
before the barrier and its register lines at the barrier and before the
terminal marker, so the ring-record counts are expected unchanged, while
no new invariant is made of an observed schedule; a count outside the
checker's existing rule is stop 5. The guest-visible SBI does not
change, so the implementation version stays 5 (6 with management). No
monitor behaviour but the log, the per-domain gate, and the self-report
changes; the management path, the denial path, the rings, and the
console path are untouched. The image budget (`0x400000`) and the MVP
region's extents are untouched.

### D-12 What M9 does not do

No eFuse, lifecycle, boot-authentication, or debug-configuration write;
no NOR write beyond S3-A.1 item 3's recorded `saveenv` (stop (a)); no
attestation, key, nonce, counter, vTPM, or SBI measurement extension
(Q39); no measurement of SPL, OpenSBI, U-Boot, or the board's device
tree; no measurement of files inside a guest (D20); no model change
(stop (e)); no claim change beyond D-9; no push, merge, tag,
publication, snapshot refresh, or kexec use; no board command before
the human confirms the board free, and none the plan requires.

## Work packages

| WP | Delivers | Exit |
| --- | --- | --- |
| M9-1 | This plan; the review packet | the plan accepted |
| M9-2 | Part 1 Revision 3 as its own exact commit (D-8); item 104's premise record `mvp/results/20261030-uboot-help/` (D-6); the platform-probe template `planning/mvp-m9-platform-probe.md`; `mvp/docs/log-profile.md`: the encoding offset by offset (D-1), the object and content-type enumerations, the per-image contract table (D-2), the `BE_MVP:19`/`:20` line grammar, and the profile's field-by-field mapping to CEL 1.1 with the unmapped fields and the no-interoperability statement (D-4) | the revision presented to the human; the record and the template committed; the profile document complete before M9-3 and M9-4 start |
| M9-3 | The monitor: `mvp-log.c`/`.h`, the records R2 to R4, the registers, the close, the per-domain gate, the rendering, `BE_MVP_CLASS_LOG`; the generator's expected records and registers in the scenario header; the image checker's rules (the page and the registers in hart 0's MVP-region BSS, aligned and contained, under the `HART0_ONLY` rule; the pre-link expected values in `.mvp.rodata`; `be_mvp_log_canary`; the self-measurement ranges' symbols); `tests/log-test.c`; the IMA allowlist (D-5); the `self-report-flip` variant by its mechanical recipe; the QEMU fixtures regenerated; the hashing and rendering costs recorded per image | `host-test`, `image-check`, and the QEMU runs PASS with every image's log judged against its class's contract (D-2); the counts within the checker's existing rule (D-11) |
| M9-4 | `tools/gen-reference.py` and the reference manifests (D-3); the checker's rebuild, replay, compare, and export with its negatives (D-4); the platform record's register sections; `k3-run.sh`'s `staged_sha256` computed (item 116); the dry run's cases | `./mvp/mvp check` PASS with the mutations rejected; `make -C mvp kernel-repro` PASS |
| M9-5 | The claim's sentences as D-9 fixes them; the ledger rows; the guide's measurement section; the crosswalk (D-7); `mvp/README.md` | `claim-ledger check` PASS; the forbidden-phrasing check PASS |
| M9-6 | The gates from a clean checkout (the lock, `check`, `evaluate`, the U-Boot rehearsal, `kernel-repro`, `model-check`, the model's evaluator); the hashing and rendering costs recorded (D-10); the human's probe outcome recorded when given; the correlation boot when a session is scheduled, else its wait recorded; the evidence record `planning/mvp-m9-evidence.md`; the result packet | the packet presented after the human's decision on Part 1 Revision 3 (or naming that it rests on an undecided revision), with D-9's slots filled from the recorded outcomes, the probe's outcome or "not performed", and the board step recorded or its wait stated |

Order: M9-2 first (the revision and the grammar); M9-3 and M9-4 together
(the generator's expected values and the checker's rules move in step;
the fixtures regenerate once both are in); M9-5; M9-6. Coding runs on
`claude-opus-5.5` sub-agents in worktrees at the pinned effort and
context tier; the session model plans, reviews each merge line by line,
runs the gates, and writes the revision, the crosswalk, the records, and
the packet (the standing split; D22). Part 1 Revision 3 is presented as
soon as it is written.

## Soft limits (re-evaluation stops; Q41 "small to medium")

**Counting rule:** M7's (added lines by `git diff --numstat` from the M9
base in C, assembly, linker scripts, Python, shell, Make, and the
wrapper, tests included; generated files, fixtures, JSON, Markdown, and
the retained records excluded and reported; hand-authored schema and
fixture material reported beside them). Estimate: the monitor's log,
records, registers, gate, and rendering 800 to 1,200; the generator's
expected values and the reference tool 700 to 1,100; the checker's log
module, its independent recomputation, the negatives of D-4's five
kinds, and the platform record 1,500 to 2,300; host tests 700 to 1,000;
the IMA allowlist, the dry run, Make, and glue 300 to 600: 4,000 to
6,200. **Limit: 6,000** (soft; the estimate's top end touches it, so the
checkpoint after M9-4 is where a re-evaluation is likely, and it is
asked for then, never worked around). The monitor's storage, its boot
time, and its serial volume are reported separately (D-10). Revision 3's
guide of 250 lines (Q12) is soft in the same way. Checkpoints after M9-3 and after M9-4. A limit
exceeded is a stop for re-evaluation of the limit, never a cut to the
work (the human's direction of 2026-10-28). The checker-to-monitor size
is reported against M7's 2.083 and not limited.

## Stop conditions (each returns to the human)

1. Any need to write an eFuse or other one-time-programmable bit, to
   change the board's lifecycle, boot-authentication, or debug
   configuration, or to write the NOR other than by S3-A.1 item 3's
   recorded `saveenv` (S3-C's stop (a)).
2. Any need to change an accepted R0-R7 or B0-B7 byte, the B6 kernel
   fragment, an accepted model file or gate, or an accepted document's
   text (this plan's own revision and Part 1 Revision 3's additive text
   excepted; stop 1 as amended, stop (e)).
3. A measured object whose expected value the checker cannot compute
   from the build's inputs (R2's ranges not reproduced post-link drops
   R2 by rule and is recorded, not a stop; any other such object is);
   missing evidence for a platform fact the record claims, or a
   contradicted platform observation (stop (c)); a probe not performed,
   recorded as such with D-9's "not performed" form, is not a stop.
4. Any claim-text change other than D-9's sentences (stop (d)).
5. A count of an accepted scenario outside the capture checker's
   existing rule (D-11), or a change to the guest-visible SBI.
6. The log page overflowing in any declared image, an expected count
   above fifteen, or a declared image whose per-image contract (D-2)
   cannot be stated.
7. Any need to parse guest content in HS (a cpio, an ELF, a kernel
   header beyond the Image header the placement already reads).
8. The soft limit exceeded (checkpoints after M9-3 and M9-4).
9. Any need to edit M8's files, or a merge that changes an accepted M8
   proof's translation unit, headers, flags, or pins without the
   re-proof rule run first (stop (i)); the lanes are separate.
10. A board command before the human confirms the board free, or any
    board step beyond Q31's (the human's probe; one correlation boot in
    a scheduled session).
11. Any push, merge, tag, publication, snapshot refresh, release step,
    or kexec use.
12. Any other finding that changes the plan's claim boundary.

## Open questions and defaults

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | The plan branch's base | `6fbcc3d1`, the M8 acceptance record, a linear descendant of the development tip `6105c34d` (the development branch's fast-forward to it is the human's `ff + push`) | `6105c34d` itself |
| Q2 | The log page | 4 KiB in hart 0's MVP-region BSS, 4 KiB aligned; a 128-byte header and 96-byte records with the explicit little-endian encoding D-1 fixes, capacity 41 (the close included), the registers in their own 128 bytes beside the page, at most 15 expected per image (the first candidate's 64-byte header could not hold its two identities; the review's B1) | a smaller page with a tighter capacity |
| Q3 | The markers | `BE_MVP:19 LOG` for the header, each record, and the close; `BE_MVP:20 REGISTERS` at the barrier and the run's end; `BE_MVP:06 LAUNCH` per domain replaces `:06 MEASURED` | one marker for everything |
| Q4 | R2 | kept, over the text and rodata ranges by linker symbols, if the build reproduces the exact loaded ranges post-link; else dropped and recorded | dropped from the start |
| Q5 | The streams | four registers: platform and monitor, configuration, domain 0, domain 1 | one register |
| Q6 | The reference manifests | build products under `build/mvp/references/`, pinned by the image checker, copied into every retained record, never committed | committed per build (rejected: they change with every image) |
| Q7 | The export shape | the Beryllium log profile: a JSON profile **derived from** TCG CEL 1.1 revision 11, mapped field by field in `mvp/docs/log-profile.md` with the unmapped fields listed, a software `register` and a per-stream record number beside the global sequence, no interoperability claim; S3-C.5's "CEL-JSON" read as this profile, the reading recorded for acceptance (the review's B5) | a conforming CEL export with a documented software-register interpretation (more work, no consumer in 1.0) |
| Q8 | The per-domain gate | compares the domain's launch register with the image's expected register; the checker compares each object's digest too | per-object gates in the monitor |
| Q9 | The probe's record | the template `planning/mvp-m9-platform-probe.md`, filled by the human; its outcome and date fill D-9's slots | a free-form note |
| Q10 | The correlation boot | one `anchor` run at M9's images folded into the next scheduled board session (release candidate 4's campaign by default); `not run` until then | an M9 board session of its own (needs the human's confirmation and presence) |
| Q11 | The soft limit | 6,000 counted lines | 5,000 |
| Q12 | Revision 3's scope | the log asset, the trusted inputs and assumptions, the self-report's limit, I19 and I20, the TCB rows; additive, under 250 lines | I19 and I20 only |
| Q13 | Amutable's source | one public document of Amutable's on image- and configuration-as-artifact, cited by URL and date in the crosswalk | none (rejected: the human asked that it be looked at) |
| Q14 | The boot-authentication disposition | a documented platform assumption as D-6 states it, dated with the probe, in these words: "No 1.0 claim relies on ROM authentication of SPL; correctly installed vendor firmware is a premise, not a measured fact" (debug reachability alone does not establish ROM authentication) | a required profile (rejected for 1.0: no root of trust is characterized) |
| Q15 | Where the IMA checks live | `tools/guest-pins.py`'s delta check, the checker's content-type refusal, and the ledger's boundary row, each with a negative case | a single grep |
| Q16 | `wrong-measurement` | keeps its name; flips bit 0 of the protected domain's expected launch register's first byte; its declared lines updated; S3-C.5's "a wrong digest at each record" is met by D-4's per-record capture mutations with the reference frozen, beside this one image variant and `self-report-flip` | renamed `wrong-launch-register`; or one image variant per record (rejected: eleven images for what capture mutations show) |
| Q17 | A steering review of this plan by another model | **answered:** the human directed one (`have gpt-6-astra review the m9 plan as steering input`, 2026-11-02); its five blockers and recommendations are incorporated in this second candidate and its text is kept beside the packet | none (the SOP's default, S3-C's Q42) |
| Q18 | The console grant in the measured configuration (item 108) | a `console-grants` record (measured, stream 1) over the sealed effective console-input facts, expected per variant by the generator; the core identity and the printed `CONFIG_SEALED` prefixes unchanged | the core identity widened to cover the grant (rejected: every accepted expectation moves); or the omission kept with a non-claim (rejected: the review's B2 and item 108) |
| Q19 | `.monitor.input` in R2 | included as its own range (`monitor-input`): the generated inventory and proposal are read-only monitor input | excluded as scenario data rather than code |

## What acceptance authorizes

M9-2 to M9-6 on branch `beryllium/mvp-m9` from the acceptance-record
commit, with Q1 to Q19 at their defaults unless answered (Q17 answered),
under the stop conditions above; Part 1 Revision 3 as its own exact commit for the
human's decision; item 104's premise record; the claim's sentences as
D-9 fixes them, taking effect through the result's acceptance; no board
command but Q31's, after the human confirms the board free and with the
human present; no push, merge, tag, publication, snapshot refresh, or
kexec use; nothing of M8's lane or of M10.
