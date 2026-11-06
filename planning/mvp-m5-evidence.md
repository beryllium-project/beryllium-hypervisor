<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M5 evidence record

This record holds the evidence of M5, "Release candidate 2: boot from
system reset", on branch `beryllium/mvp-m5`, made under the accepted
[M5 plan](mvp-m5-plan.md) (`0066794d`, accepted 2026-10-30 with M5
implementation authorized; its [erratum 1](mvp-m5-plan-review-summary.md),
the code limit re-set to 10,000) and the accepted
[Plan revision S3-A](mvp-plan.md#plan-revision-s3-a-boot-from-system-reset-the-board-policy-m5-and-release-candidate-staging)
(`0d134bbc`). It records what was run, when, on which commit, and what
it printed; it makes no claim beyond those lines. The candidate tree
`X2` is exact commit `6dd81ee39dd620a1815605c50c9c916894c9974c` (tree
`2eaafb36`); no source change follows it. The release-candidate commit
`R2` is the commit that adds this record's final form with the two
retained records and the ledger rows that cite them, over `X2`; the
review packet names it.

## What M5 adds, by file

All under `mvp/` but the planning documents, the standing rule in
`.github/copilot-instructions.md` and `planning/HANDOFF.md`, and the
roadmap. No monitor source, shim, guest input, scenario, generator,
policy checker, or `model/` file changes: `git diff --stat 9b3fa982
6dd81ee39dd620a1815605c50c9c916894c9974c -- mvp/src mvp/shim mvp/guest mvp/scenarios
mvp/tools/gen-scenario.py mvp/tools/policy-check.py model` is empty. The
image checker gains one rule (the QEMU-only image differs from its board
image in header bytes 8 to 15 alone) and the capture checker one mode
(`uboot`); the lock gains the rehearsal's roles and `tmux` as host-only
and loses the kexec rehearsal kernel's inputs (the enumerated roles stop
condition 6 refers to).

| File | Lines | What it holds |
| --- | --- | --- |
| `tools/k3-console.sh` (new, M5-2) | 659 | The template-driven typing at U-Boot through the operator's picocom tmux session: the fixed line forms, pieces of at most 60 characters with each echo compared before Enter, `s` at `Autoboot in` (after a pane-mode cancel; a second after 0.5 s without a prompt), the `k3ctl` reset under the port-open rule, the authorized read-only `diag`, and the keystroke log |
| `tools/k3-uboot.py` (new, M5-2) | 575 | The serial log's reader: banners, prompts, `Autoboot in`, the fresh-prompt rule, the normalized `printenv` record, the can-reset conditions (idle prompt, terminal marker, Fedora down), and each run's attribution lines |
| `tools/k3-env.sh` (new, M5-2) | 489 | `record`, `install`, `select`, `restore`, `characterize`: the `be_` lines and `bootcmd` at a fresh prompt, the `printenv` comparison before every `saveenv`, V, the private store, and each step's verdict file |
| `tools/k3-stage.sh` (new, M5-2) | 195 | The 14 images onto the `beryllium` partition over `ssh`, `SHA256SUMS` and `MD5SUMS`, re-hashed after a fresh read-only mount; the digests pairwise distinct |
| `tools/k3-run.sh` (rewritten, M5-2) | 207 (−677) | A run from a reset: the capture from just before the reset to the terminal marker, judged in `uboot` mode, the five attribution conditions, the banner audit; the kexec steps gone |
| `tools/k3-campaign.sh` (rewritten) | 93 (−184) | The group loop: a select at a fresh prompt per image group, the group's runs; `K3_CAMPAIGN_SKIP` resumes a stopped session |
| `tools/k3-preflight.sh` (edited) | +122 −43 | The partition check, `env_k3.txt`'s hash and content, the read-only platform probe; the kexec facts gone |
| `tools/platform-probe.py` (new, from `kexec-load.py`) | 316 | The read-only `probe` and `region-check`, without the loader |
| `tools/kexec-load.py`, `tests/kexec-rehearsal.sh`, `tests/kexec-rehearsal/` (deleted) | −646, −237, −268 | The kexec loading code and rehearsal (decision 3 and the standing rule, decision 8) |
| `tests/check-capture.py` (edited, M5-2) | +739 −38 | `--mode uboot`: the U-Boot lines in order, `N bytes read` as the image's size, one digest line (`md5 for … ==> D` or `crc32 … ==> C`) as the image's, `Moving Image … to 0x108000000`, the device tree outside every MVP extent, one SPL and one U-Boot banner, the BSP's noise; `--mode kexec` kept test-only; the fixtures |
| `tests/check-image.py` (edited) | +96 | The QEMU-only image rule |
| `tests/uboot-rehearsal.sh`, `tests/uboot-rehearsal/run-qemu-uboot.py` (new, M5-3) | 412, 791 | The U-Boot rehearsal in QEMU: B3's pinned upstream U-Boot v2022.10 under OpenSBI on the eight-hart k3-like machine, the session's `be_` lines and `bootcmd` typed at its prompt, each scenario image loaded from an ext4 partition and booted, judged in `uboot` mode; the missing-image fall-through |
| `tests/fake-uboot.py` (new), `tests/fake-board.py` (edited), `tests/run-tool-dry-run.sh` (rewritten) | 585, +199 −263, +962 −1,442 | The fake U-Boot behind a fake tmux (stamps, the BSP's noise, a configurable lost `s`, a pane mode) and the dry run's cases: install, select, restore, a run from reset, a campaign with a resume, a template refusal, an echo mismatch, a `printenv` mismatch, one and two lost `s`, four, the pane mode, an unexplained banner, the characterization, the record with nothing private |
| `tools/evidence.py` (edited) | +343 −207 | The board record of a U-Boot session: the launcher, the environment verdicts, the keystroke log, excerpts from `Autoboot in`, the preflight after the session (redacted as B0 redacts), MAC and `serial#` as code names, a device-tree node not an ssh target |
| `tools/platform-record.py` (edited) | +106 −45 | The boot hart from the shim line, the preflight pair, the cold-boot probe values beside M0's kexec-time values |
| `tools/rc-record.py`, `tools/claim-ledger.py`, `tools/make-control.py`, `tools/lock/*`, `tools.mk`, `Makefile`, `mvp` (edited) | +53 −42, +18 −3, +26 −18, +90 −18, +227 −219, +40 −3, +56 −25 | The `uboot-rehearsal` gate in place of `kexec-rehearsal`; the ledger's privacy rule; the new commands; the lock roles |
| `tools/k3-make-partition.sh` (edited after delivery) | +12 −5 | `orphan_present` ignored as a mount-state flag, like `needs_recovery` (README item 76) |
| `docs/claim.md`, `docs/guide.md`, `docs/ai-assistance.md`, `docs/claim-ledger.json`/`.md` (edited, M5-4) | +36 −14, +467 −196, +134 −63, +63 −55 | The board clause and the required limit for a boot from reset; the guide's section 4; the disclosure (automation typed at U-Boot and ran `saveenv`, on direction); C-10 as the U-Boot boot path row, release candidate 1's rows as history; at `R2` the rows below |
| `results/20261030-rc2/` (new, M5-5) | 430 files | The release-candidate record of the seven gates at `X2` |
| `results/20261030-com260-rc2/` (new, M5-6) | 198 files | The release-candidate board record: 20 runs from system reset at `X2`'s images |
| `README.md` (edited) | +668 −57 at `X2`; the log's closing entry and open item 85 at `R2` | The development log's M5 entries, open items 71 to 85 |
| `.gitattributes` (edited at `R2`) | +9 −4 | M4's whitespace exemption for the raw QEMU captures widened to `*-rc*/`, and the board record's excerpts and staging record exempted from the trailing-space check (open item 85); no other file's attributes change |

New code: 7,439 added lines (`git diff --numstat 9b3fa982 6dd81ee3`
over Python, shell, Make, and the wrapper, tests included; 4,386
deleted, the kexec code among them), against the limit re-set to 10,000
by erratum 1 after stop condition 8 fired at 6,865 (README item 71); the
partition tool's own 12 added lines are counted separately. Documents
have no limit.

## The claim, the limit, and the phrasings

`mvp/docs/claim.md` carries the board clause the M5 plan fixed ("booted
from system reset by the board's installed firmware and U-Boot, which
loaded the MVP image from a Beryllium partition on the board's NVMe
under a boot command installed in U-Boot's saved environment for the
campaign and restored after it"), the required limit's "one U-Boot build
as its banner reports it" in place of "one host kernel", and the two
added sentences on the firmware and the saved environment, with the
closing sentence verbatim (M5-4, `7997bbb0`). The forbidden-phrasing
check passes over every document at `X2` (`claim-ledger.py check`).

## Plan-letter departures recorded in the session

Each a tool or plan-detail fact the board taught, fixed with dry-run
coverage and recorded in `mvp/README.md` (items 72, 79, 81, 84); none
changes what the claim says.

| Plan text | As run | Where |
| --- | --- | --- |
| `be_ld` ends in `crc32`; the attribution's digest is the CRC-32 | This BSP's `crc32` prints nothing (the vendor's `common/hash.c` prints through `pr_debug`); the board's `be_ld` ends in `md5sum` and the digest is the MD5; QEMU's rehearsal keeps `crc32` (upstream has no `md5sum`); the checker takes either line matching the image | item 79 (6); `09687613` |
| Clean shutdown `systemctl poweroff` | `systemctl poweroff` powers the COM260 off and a reset pulse does not wake it; the clean shutdown is `systemctl reboot`, which this board halts at `reboot: Restarting system` | item 79 (1, 2); `3a9c54ef` |
| A normalized record ends at `Environment size: N/M bytes` | This BSP's `printenv` prints no trailer; the record is the variable lines | item 79 (4); `59d782a4` |
| Lines of at most 60 characters | The `be_ld` line is 95 characters, typed in two pieces of at most 60 with each echo compared | item 72 |
| `run be_ld` at the characterization | `nvme scan` first: U-Boot knows no NVMe device until it is scanned | item 79 (5); `7e833730` |
| The characterization set | `diag`, a recorded read-only diagnostic line, on the human's `you are authorized to type any needed diagnostic commands`; three lines typed at the sixth attempt | item 79 (6); `b613dd27` |
| A session's first reset on Fedora down | May also rest on the prior session's halt or terminal marker, or an idle prompt | item 79 (3); `5e1d0b49` |
| The autoboot stop: `s` once; a missed `s` retried once, then stop | A second `s` after 0.5 s without a prompt, inside the 3 s window, after a tmux pane-mode cancel; the plan's unplanned-boot rule unchanged and followed at the fourth select | item 81; `0bfb1ca8` |
| No resume | `K3_CAMPAIGN_SKIP=N` resumed the stopped session at its fifth group; the record holds the plan's runs once each | item 81 |
| The gates at `X2` before the board session (step d) | Run once, after the campaign, at the final `X2`, the M4 pattern: a gates run is invalidated by any commit, and the session's findings had to be committed; the board images are byte-identical to release candidate 1's and did not change | below |

## The characterization (M5-6a)

Seven attempts on 2026-10-30, the board on Fedora 45
(`7.3.0-65.1.riscv64.omni.fc45`), the first six stopped by the facts
above (nothing saved, nothing written to the board), the seventh passed
end to end (`build/mvp/k3-sessions/20261030-characterize-7/`, run
`20261030T072654Z`, 07:25 to 07:29 UTC): `version`, `help`, `env info`,
`bdinfo`, `nvme scan`, `fsuuid nvme 0:6` equal to Fedora's `blkid`, `ls
nvme 0:6 /` listing the 14 staged images, `fdt print /reserved-memory`
(16 ranges, none inside an MVP extent), two `printenv` records at
consecutive fresh prompts (identical; V empty), the copy test exact, then
`run be_ld` (`2584576 bytes read`, `md5 for 140000000 ... 140276fff ==>
fc5b0d73…`, the staged `probe-platform` image's MD5) and `run be_go`:
`Moving Image from 0x140000000 to 0x108000000`, the control device tree
loaded to `0x2fbd5d000`, the shim on hart 0, and the probe's cold-boot
facts equal to M0's kexec-time values (harts 1 to 7 HSM `STOPPED`, 14
VMID bits, `htval` = GPA >> 2, IPIs 100 of 100 in HS and V=1, 0 stale
reads). Diagnostic bring-up evidence; README items 79 and 80.

## The gates at `X2`, from this checkout clean at `X2`

Run by a driver under `build/mvp/rc2-gates/` (outside the tree), each
gate's output logged between `start_utc=` and `end_utc=` lines, in the
plan's order (the U-Boot rehearsal in place of M4's kexec rehearsal),
2026-10-30, workstation `l1` (Fedora Linux 44, x86_64), the lock's tools
(`lock_sha256=2f1b732dcf24`), the host's `build/model/evidence` copied aside
between the last two gates:

| Gate | UTC | Result |
| --- | --- | --- |
| `./mvp/mvp tool-lock check` | 09:09:18 to 09:09:20 | `BE_MVP_LOCK: PASS roles=32 host_only_skipped=0 closure=259 lock_sha256=2f1b732dcf24`; `BE_MVP_LOCK_SELF_TEST: PASS cases=50` |
| `./mvp/mvp check` | 09:09:20 to 09:14:28 | `BE_MVP_CHECK: PASS`; the bundle `files=356 images=253 qemu_attempts=77 rehearsals=7`; `BE_MVP_CAPTURE_SELF_TEST: PASS cases=113 failed=0`; `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=283 rejected=283`; `BE_MVP_RUN_TOOL_DRY_RUN: PASS`; `BE_MVP_UBOOT_REHEARSAL_SELF_TEST: PASS cases=49`; `BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=34 boundary=12` (39 at `R2`); `rc-record self-test: PASS mutations=22` |
| `./mvp/mvp evaluate` | 09:14:28 to 09:19:16 | `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`; `BE_MVP_IMAGE_IDENTITY: PASS images=253 same=253 differing=0`; inside, `BE_MVP_LOCK: PASS roles=26 host_only_skipped=6`, `BE_MVP_CHECK: PASS` |
| `./mvp/mvp uboot-rehearsal` | 09:19:16 to 09:21:02 | `BE_MVP_UBOOT_REHEARSAL: PASS cases=7 attempts=7 refused=0 uboot=d96d1c22c67b opensbi=78f14d30c951 qemu=10.2.2`: `two-guests`, `te-poc`, and `anchor` for GCC (QEMU-only images `351ed0e34407`, `edc17c660ee8`, `3d1d2c5d075d`) and Clang (`30eaacf0191f`, `79052a37d75f`, `a3491b5faa4b`), each `session=PASS check=PASS`, and `fallthrough` (the missing image fell through to the stand-in `be_orig_bootcmd`) |
| `make -C mvp kernel-repro LINUX_GIT=<local mirror>` | 09:21:02 to 09:21:33 | `BE_MVP_KERNEL_REPRO: PASS outputs=15 identical; sysroot_files=1065 sysroot_sha256=c931b51b…` |
| `./be model-check` | 09:21:33 to 09:22:30 | `Beryllium Architecture Model 0.2 evidence: PASS`; `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241`; proofs, reports, source policy, tools, and unit tests PASS |
| `./be evaluate` | 09:22:30 to 09:23:27 | `BE_EVALUATION: Model 0.2 rootless evidence PASS` |

Three earlier attempts are development history, not evidence
(`build/mvp/rc2-gates-attempt-1-67a2106d/`, `-attempt-2-67a2106d/`,
`-attempt-3-44233488/`): the first failed `./mvp/mvp evaluate` because
the partition tool's self-test, run as root inside the evaluator,
refused its test hooks (fixed at `3433643a`: it skips as root inside the
evaluator and fails as root elsewhere); the second was stopped by a
commit made during its run (README changes), which invalidates a gates
run; the third passed every gate (08:52 to 09:07 UTC), but `rc-record`
refused its record because a self-test case added at `44233488` printed
`name@unit-address:` and `user@host:` into the evaluator's retained
`check.log`, which the record's scan reads as an ssh target (the class
M4's `42009986` fixed); the case was reworded (`6dd81ee3`), which moved
`X2`.

## The release-candidate record

`./mvp/mvp rc-record` made `mvp/results/20261030-rc2/` at 09:23:37 UTC
from the inputs named explicitly (the host bundle, the evaluator record
`20261030T091428Z`, the host's and the evaluator's model evidence and
the evaluator's logs, the seven rehearsal cases, `kernel-repro`, the
seven gate logs), each checked to name `X2` and the evaluator's identity
checked against `tools/lock/closure.txt` and `tools/evaluator/Containerfile`
at `X2`: `BE_MVP_RC_RECORD: PASS … commit=6dd81ee3… files=430` (3.4 MB).
`rc.txt` names `X2`, its tree, the host's OS and architecture, the lock's
(`2f1b732d…`) and closure's (`2875ddd6…`) SHA-256, and each gate's PASS
line with its times; `host/` is the bundle (`files_rewritten=0`);
`evaluator/` the record with `compare-images.txt`; `model/host/`,
`model/evaluator/`, `model/evaluator-logs/`; seven `rehearsal/<case>/`;
`kernel-repro.txt`; `MANIFEST.sha256` (SHA-256 `fbe1f4aba636f460…`) over
every other file. `--verify` passes (`BE_MVP_RC_RECORD: PASS verify`);
the ledger's privacy rule finds nothing in it. The record is committed
in `R2`, with the board record below.

## The release-candidate board campaign (M5-6)

The session `20261030-com260-rc2` on the COM260, 2026-10-30, 07:52 to
08:18 UTC, from this checkout at `0bfb1ca8`'s images, which are `X2`'s
(no image-bearing file changed between them; `board-evidence` was
re-made at `X2` from the session's stored captures, below). The board
tools were driven from `l1` with `K3_RESET=k3ctl` (the pinned client,
`tools/k3ctl.sha256`), the operator's picocom session `k3-console-1`
holding the serial log, the responsible human present at the install
and the restore and confirming the board free, the saved `bootcmd` as
their default, and no pending one-shot boot. The 14 staged images are
byte-identical to release candidate 1's candidate images
(`mvp/results/20261029-rc/host/images.sha256` lists all 14 SHA-256s):
the bytes the kexec campaign ran now ran from system reset.

| Step | UTC | Result |
| --- | --- | --- |
| (e) preflight before (`k3-preflight`, Fedora up) | 07:52:56 | `BE_MVP_PREFLIGHT: PASS`; partition 6 ext4 `beryllium` 1 GiB unmounted, `fsuuid` kept private; `env_k3.txt` 227 bytes, sets no `bootcmd` or `be_` name; `region_check=PASS` (every MVP extent free); firmware `SBI implementation ID=0x1 Version=0x10006` |
| (f) staging (`k3-stage`) | 07:53 | 14 images, 2,584,576 bytes each, `SHA256SUMS` and `MD5SUMS` re-hashed after a fresh read-only mount; `md5_distinct=yes` |
| (g) clean shutdown | 07:54:21 | `systemctl reboot`, halted at `reboot: Restarting system` |
| (h) two records (`k3-env record`) | 07:54:44, 07:54:50 | two `k3ctl` resets, `s`, `printenv` at each fresh prompt; records 1 and 2 SHA-256 `72443954…` both; V empty; preconditions PASS (`bootdelay=3`, no `preboot`, no `bootcount`); `bootcmd` SHA-256 `0404ae42…` |
| (i) install (`k3-env install`, the human present) | 07:56:57 to 07:57:14 | at a fresh prompt the seven `setenv` lines, `printenv` equal to record 1 plus exactly the declared lines (`be_orig_bootcmd` equal to record 1's `bootcmd`), `saveenv` `OK` |
| (j) the runs (`k3-campaign`) | 07:58:04 to 08:00:08, then 08:09:22 to 08:15:48 | 20 of 20 as declared (table below); 13 selects, each at a fresh prompt with only `be_image` changed and `saveenv` `OK`; one stop (below) |
| (k) restore (`k3-env restore`, the human present) | 08:16:46 to 08:17:02 | at a fresh prompt `setenv bootcmd "${be_orig_bootcmd}"`, the six deletions, `printenv` equal to record 1, `saveenv` `OK` |
| (l) fresh-prompt check | 08:17:04 to 08:17:09 | reset, `s`, `printenv`: record 3 SHA-256 `72443954…`, equal to record 1 byte for byte (V empty) |
| (m) Fedora autoboot and preflight after | 08:17:10, 08:17:57 | one reset, no key; Fedora up with a new boot ID; `BE_MVP_PREFLIGHT: PASS`; the pair differs in `captured_utc`, `boot_id`, and the order of the kernel's concurrent per-CPU lines only (34 of 34 compared rows equal) |
| (n) `board-evidence` | at `X2` | `BE_MVP_EVIDENCE: PASS board … runs=20 pass=20 fail=0 refused=0 stop=0`; 198 files; `identifying()` finds nothing; `--verify` PASS |

The runs, each its own `k3ctl` reset with Fedora down, the saved
`bootcmd` running `be_boot` (`nvme scan`; `2584576 bytes read in 2 ms`;
`md5 for 140000000 ... 140276fff ==> D`, D the staged image's MD5;
`Moving Image from 0x140000000 to 0x108000000, end=108277000`; `Loading
Device Tree to 00000002fbd5d000, end 00000002fbd6f2ef ... OK`; `Starting
kernel ...`), the shim on hart 0 with `fdt=0x2fbd5d000`, and the
terminal marker 12 to 18 s after the reset; each capture judged in
`uboot` mode and passing its five attribution conditions and its banner
audit:

| Run (UTC) | Image | Verdict | What the capture holds |
| --- | --- | --- | --- |
| 07:58:04 | `probe-platform` GCC | PASS | the cold-boot facts of the characterization, equal to M0's kexec-time values |
| 07:58:32 | `probe-vmid-distinct` GCC | PASS | VMID tagging observed: distinct VMIDs, no stale translation |
| 07:59:01 | `probe-vmid-shared` GCC | PASS | the shared-VMID counterpart |
| 07:59:29, 07:59:48, 08:00:07 | `two-guests` GCC ×3 | PASS | `exits=157` on both domain harts, `records=138 wakes=2` (M0's counts) |
| 08:09:38 | `two-guests` Clang | PASS | the same counts |
| 08:10:08, 08:10:28, 08:10:47 | `te-poc` GCC ×3 | PASS | both `MVPINIT 07 CHANNEL` lines; `DENY` `unmapped cause=0x15 injected=0x5 gpa=0x84001000`, `read-only cause=0x17 injected=0x7 gpa=0x84000ff8`, and the reader's second; `exits=163`/`167`, `records=146 wakes=2` (M1-B's) |
| 08:11:17 | `te-poc` Clang | PASS | the same |
| 08:11:47, 08:12:09, 08:12:31 | `anchor` GCC ×3 | PASS | domain 1 `DOMAIN_PAUSED` and `DOMAIN_TERMINATED` at `exits=132` with the measured digest; domain 0 `exits=248 … refused=1`; `records=174 wakes=16` (M2-A's) |
| 08:13:03 | `anchor` Clang | PASS | the same |
| 08:13:36 | `payload` GCC | PASS (fails as declared) | `BE_MVP:FAIL payload` before any hart started |
| 08:14:04 | `reader-write` GCC | PASS (fails as declared) | `BE_MVP:FAIL gstage` with its `DETAIL`, no domain run |
| 08:14:32 | `no-inject` GCC | PASS (fails as declared) | `BE_MVP:FAIL guest-page-fault` |
| 08:15:01 | `wrong-measurement` GCC | PASS (fails as declared) | `BE_MVP:FAIL measurement` |
| 08:15:30 | `no-grant-check` GCC | PASS (fails as declared) | `BE_MVP:FAIL run-timeout`, `DETAIL ticks=0x8000000` |

The counts M4 compared (`two-guests`, `te-poc`) equal release candidate
1's, and `anchor`'s equal the accepted M2-A record's, which release
candidate 1 cited by byte-identical images (ledger C-31); `anchor` ran
on the board at a candidate's images for the first time here.

**The stop.** At the fourth select (`two-guests-clang`, 08:00:21 UTC)
the `s` sent 1.1 s after the U-Boot banner, as for the three selects
that worked, was lost twice in a row; `bootcmd` ran the still-selected
`two-guests-gcc` image to its `BE_MVP:14` marker both times (08:00:32
and 08:00:57, `env/unplanned.txt`; recorded, counted as nothing, the
plan's rule), and the campaign stopped (stop condition 12, `env/
select-04.txt`). Whether the tmux pane swallowed the key (a scrolled
pane in copy mode takes `send-keys` as navigation) or the serial line
dropped it is not established; `0bfb1ca8` covers both (a pane-mode
cancel before any send; a second `s` after 0.5 s without a prompt) and
adds the resume, with dry-run cases for one, two, and four lost `s` and
the pane mode. The session resumed at its fifth group at 08:09:22 UTC
(`K3_CAMPAIGN_SKIP=4`); no later `s` was lost and none was retried. The
session's 41 `k3ctl` resets (1 on Fedora down, 18 at an idle prompt, 22
after a terminal marker) each map to one SPL and one U-Boot banner;
no banner is unexplained; no reset was made by hand; no recovery was
needed.

**The record.** `mvp/results/20261030-com260-rc2/` (198
files): B0's retention of the 20 runs (each `check.txt`, `load.txt`,
`reset.txt`, `result.json`, `run.txt`, `SHA256SUMS`, and the excerpt
from `Autoboot in`) and the preflight before; `mvp/session/` with the
keystroke log (490 lines: 93 keys, 74 sends, 73 echoed lines, 91
prompts, 41 resets and banners, 2 `missed-s`), `resets.tsv`, the staging
record, and `env/` (the records', install's, 13 selects', and restore's
verdicts, `unplanned.txt`, `state.txt`); `mvp/preflight-after.txt`
(redacted as B0 redacts the one before); the hand-written Serial log
paragraph; `platform-record.md` with the preflight pair, the cold-boot
probe values beside M0's, and the resets; `summary.md`; `MANIFEST.sha256`
(`4affd8f2eb682fbc…`). The full `printenv` texts stay in the private
store (`~/.local/state/beryllium/k3-env/20261030-com260-rc2/`, mode
0600) and the picocom log; the record holds their SHA-256s, the `be_`
names and values, V, and the verdicts (Q8). The responsible human
reviewed the draft record before it was committed (`yes, proceed`,
2026-10-30 08:46 UTC).

## Soft limits and stops in M5

| Event | Stop | Outcome |
| --- | --- | --- |
| New code 6,865 lines after M5-2/M5-3 against 5,000 | 8 | Returned; the limit re-set to 10,000 (erratum 1, `154dc810`); 7,439 at `X2` |
| The partition tool's apply exited 5 (`orphan_present`) | none (the tool's own rule) | The flag is mount state; fixed (`f3a04a86`); the partition was made correctly (README item 76) |
| Six characterization attempts stopped on BSP and board facts | 1, 3, 4 by their letter | Each a tool or plan-detail defect fixed with dry-run coverage (the departures table); the seventh attempt passed |
| `crc32` prints nothing on this BSP | 3 (`crc32` error) | The digest witness became `md5sum` on the board (`09687613`), on the human's authorization of the diagnostics |
| `./mvp/mvp evaluate` failed at the first gates run | none (a defect of M5's own self-test) | Fixed (`3433643a`); the gates re-run at the final `X2` |
| The fourth select's `s` lost twice | 12 | Returned; hardened and resumed (`0bfb1ca8`); 20 of 20 |
| `board-evidence` failed B0's retention check on an unredacted root UUID | none (a defect of M5's own record writer) | Fixed (`ec6b51d3`) with a dry-run case; the record re-made |
| A device-tree node rewritten as `<board-ssh>` | none (cosmetic; seen in the Q8 review) | Fixed (`44233488`) with a self-test case |
| `rc-record` refused the third gates run's record: the new self-test case's own text read as an ssh target | none (a defect of M5's own self-test text) | Reworded (`6dd81ee3`); `X2` moved and the gates ran again |
| `k3ctl power` taps did not wake the powered-off board (by hand, outside the tools) | none | Recorded (README item 80); the tools never power the board off or on |

Every soft limit holds at `X2`: new code 7,439 of 10,000; no monitor,
guest, scenario, generator, or `model/` line changed; the lock changed
only in the enumerated roles.

## Open items

From `mvp/README.md`: 71 (stop 8) closed by erratum 1; 72 (M5-2/M5-3
deviations) recorded above; 76, 82, and 84 closed; 73 to 75, 77, and 78
as recorded; 79 (the board's facts) and 81 (the session) closed by this
record; 80 (the dongle's power tap; the cause of the power-on
unestablished) open for the responsible human, outside the board tools;
83 (the run table's `Kernel ?` column) and 85 (two retained record files
end lines in a space; the staging tool's own to fix in a later source
change) cosmetic, open.

## Claim boundary

What is recorded here: unit tests, adversarial tests (seeded mutations
and negative images), deterministic reports, semantic checks (the image
and capture checkers, the ledger checker), emulation (QEMU, the U-Boot
rehearsal included), the proof about the abstract model and the
differential agreement carried over from the accepted M3 result, and the
release-candidate campaign's twenty diagnostic board runs from system
reset at the candidate's images. The board runs are diagnostic bring-up
evidence for one board (the COM260), one reported SBI identity and
version, and one U-Boot build as its banner reports it, at the
candidate's images; the NOR firmware and U-Boot are identified by their
banners and SBI identity before, during, and after the campaign, not
hashed; the saved environment is shown restored by the environment
U-Boot printed at a fresh prompt, not by its stored bytes. Not recorded:
any claim the required limit excludes; any release-path step after the
first, none of which is started; any use of kexec (none; the standing
rule).
