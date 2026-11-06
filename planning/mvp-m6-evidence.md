<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M6 evidence record

This record holds the evidence of M6, "The MVP core profile and release
candidate 3", on branch `beryllium/mvp-m6`, made under the accepted
[M6 plan](mvp-m6-plan.md) (`b2c62d54`, accepted 2026-10-30 with M6
implementation authorized at the acceptance record `366c8af4`, the M6
base) and the accepted
[Plan revision S3-B](mvp-plan.md#plan-revision-s3-b-release-candidate-3-and-milestone-m6-the-mvp-core-profile)
(`f8b77ac9`). It records what was run, when, on which commit, and what
it printed; it makes no claim beyond those lines. The candidate tree
`X3` is exact commit `ebc49a889273c811836c3d39fb0fc9bfe808be4c` (tree
`0a60a35f`); no source change follows it. The release-candidate commit
`RC3` is the commit that adds this record's final form with the two
retained records and the ledger rows that cite them, over `X3`; the
review packet names it.

## What M6 adds, by file

All under `mvp/` but the planning documents, the status pages, and two
of the model's test files (below). No guest input, shim, board tool (the
probe's region name apart), scenario policy, model structure, proof, or
theorem, or accepted R0-R7 or B0-B7 byte changes: `git diff --stat
366c8af4 ebc49a88 -- mvp/guest mvp/shim mvp/scenarios/*/policy.te
model/src model/include model/proof model/fixtures include virt arch
bringup tests` is empty. The monitor's boot, its layout
within the core's first `0x34000` bytes, and the home of every
privileged effect change; every MVP-owned extent, the image's base and
size, the staging, window, and shared-page addresses, and the shim's
placement do not (stop condition 3 was not reached).

| File | Lines | What it holds |
| --- | --- | --- |
| `tools/port.py` (edited, M6-2; 328 to 763 lines) | +435 | The counted port of B7's sources gains the accepted R1 declarations, widened by 43 rules pinned by SHA-256 over their spans: `BE_MAX_HARTS 3`, `BE_VMID_LIMIT 16384`, resources 24, authorities 12, mappings 8, channels 3, `BE_PROFILE_MVP_CORE` |
| `src/mvp-core.c`, `src/mvp-core.h` (new, M6-2) | 232, 89 | The derived roots' records as the builder's, the measurement's, and the control loop's input: each derived mapping to a builder descriptor and its pages; the sealed state's counts and identity |
| `src/mvp-runtime.c` (rewritten in part, M6-2) | +220 −229 | `seal_config()`: copy, validate, seal, derive, compare with the linked record, fail closed; `BE_MVP:00 BOOT_VALIDATED` and `CONFIG_SEALED` in place of `BE_R3:01` to `:06`; `run_r1`, `run_r2`, the fixture roots and pages, hart 0's binding and `hgatp` publication gone |
| `src/mvp-monitor.lds` (new, M6-2) | 265 | The core's first `0x34000` bytes laid out by the MVP: code below `0x1_0200_8000` (ends `0x1_0200_2d10` GCC, `0x1_0200_2f90` Clang at `X3`), data from `0x1_0200_8000`, the diagnostic area at `0x1_0200_f000`, hart 0's stack at `0x1_0201_0000`; the pool, hart region, MVP region, and image size unchanged |
| `src/mvp-layout.h`, `src/mvp-hartmain.c`, `src/mvp-probe.c`/`.h`, `src/mvp-payload.c`/`.h`, `src/mvp-platform.h`, `src/mvp-trap.S` (edited) | +39 −23, +54 −52, +32 −26, +9 −6, +2 −2, +2 −2, +1, +1 −1 | `BE_MVP_CORE_BYTES` and `BE_MVP_STAGING_BYTES` (`0x600000`) by their own names; `BE_MVP_ACCEPTED_IMAGE_BYTES` and `BE_MVP_KEXEC_FDT_*` removed; the probes seal two-guests' configuration; the executor's names |
| `src/mvp-executor.c`, `src/mvp-executor.h` (new, M6-3) | 190, 236 | The 28 `be_mvp_exec_*` functions, every privileged effect the MVP's C performs (each SBI call, the accepted HS and VS register helpers, fences, the time read, the console write) behind one file; the trap assembly unchanged |
| `tools/gen-scenario.py`, `tools/policy-check.py` (edited, M6-2) | +259 −45, +115 −8 | `core()` and `core_inputs()`: each scenario's inventory and proposal from its policy, labeling, and layout; `mvp-config.c` generated per scenario (two-guests 14 resources and 2 authorities, te-poc 15 and 4, anchor 17 and 7); `core_agrees()` against the authority report (stop condition 11); the configuration identity (Q6) |
| `tests/config-test.c` (new, M6-2) | 470 | The widened validator on every scenario's configuration with GCC and Clang: 36 scenarios, 139 assertions, 29 single defects each refused for its own class |
| `tests/check-capture.py` (edited, M6-2) | +238 −80 | The two prelude forms (the M6 markers, or the pre-M6 `BE_R3` lines for the retained records and M1's and M2's fixtures), exactly one, whole, before `BE_MVP:01`; the pre-M6 fixtures judged against `tests/fixtures/pre-m6/` (the te-poc and anchor expectations at `366c8af4`); twelve M6 QEMU fixtures; self-test 129 cases, 317 mutations |
| `tests/check-image.py` (edited, M6-2 and M6-3) | +274 −214 | The core rules (each core section in its extent, the configuration in the input section); the executor seam rule (no MVP function but the executor names an assembly or accepted privileged helper); the `KEXEC_FDT_*` constants kept test-only for the retained kexec records |
| `tests/fixtures/*-m6.log` (new), `tests/fixtures/pre-m6/` (new) | 12 files, 1,661 lines; 10 files, 5,292 lines | The M6 QEMU captures; the pre-M6 expectations |
| `Makefile`, `tests/run-tool-dry-run.sh`, `tests/test-platform-probe.py`, `tests/payload-test.c`, `tools/platform-probe.py`, `scenarios/*/scenario.json` (edited) | +65 −31, +3 −3, +8 −11, +2 −2, +14 −16, −4 | The generated configuration's build; the probe-image MD5 pin; the probe's region `core`; the scenarios' `kexec_fdt` object removed (Q3) |
| `docs/guide.md`, `docs/ai-assistance.md`, `docs/claim-ledger.json`/`.md` (edited, M6-5) | +40 −10, +10 −7, +77 −3, +17 −2 | The boot story and the core identity; release candidate 3's disclosure; C-40, C-41, U-13; C-10's capture-checker pin |
| `README.md` (edited) | +468 −42 at `X3` | The development log's M6 entries, the layer table, the counted copies, the port's rules, open items 87 and 88 |
| `model/tests/unit/policy_test.c`, `model/tests/check-reports.mjs` (edited, after the first gates run) | +3 −3, +6 −6 | The pinned identities and counts of policy instances 2 and 3, which are generated from the te-poc and anchor scenarios, refreshed to the regenerated values after Q3's `kexec_fdt` removal (README item 88) |

New code: 3,258 added lines (754 deleted) by the plan's counting rule
(`git diff --numstat 366c8af4 ebc49a88` over C, assembly, linker
scripts, Python, shell, Make, and the wrapper, tests included;
generated files, fixtures, JSON, Markdown, and the model's Rocq
excluded; the model's test pins among the C) against the limit of
4,000; checkpointed after M6-2 (2,545) and after M6-3 (3,231). Reported
separately: 1,661 fixture-log lines, 5,292 lines of pre-M6 expectation
JSON, 80 lines of ledger JSON, 6 JavaScript lines (the report checker's
pins), 535 Markdown lines, and no Rocq. The proof-bearing subset: 6,285 code lines;
support 1,105; the executor 177; platform and assembly 930 (the README's
layer table).

## The claim, the limit, and the phrasings

`mvp/docs/claim.md` is unchanged in M6 (stop condition 2 was not
reached): the board clause, the required limit, and the closing sentence
are release candidate 2's, word for word. The forbidden-phrasing check
passes over every document at `X3` (`claim-ledger.py check`, 9 checks).

## Departures from the plan's letter, recorded in the session

Each recorded in `mvp/README.md`'s M6-2, M6-3, M6-4, and M6-5 entries;
none changes what the claim says.

| Plan text | As done | Where |
| --- | --- | --- |
| D-4 and Q3: `BE_MVP_ACCEPTED_IMAGE_BYTES` and `BE_MVP_KEXEC_FDT_*` removed | Removed from `src/mvp-layout.h` at `32850958`; the capture checker keeps `KEXEC_FDT_*` as test-only constants, because the retained kexec records (M0 to M2, release candidate 1) are still judged in `kexec` mode | M6-2 entry |
| Q1: "harts 3 named plus the platform count" | A domain's hart is checked distinct and not the control hart at the seal, not against the platform's count, which is the firmware's answer at the hart's start; the `hart-start` variant (hart 9) fails at its start, as declared | M6-2 entry |
| D-3 is silent on the probe images' configuration | The probe images seal two-guests' configuration and print `roots=2 harts=0,1,2`, then run their own measurements; the board's probe captures show the new prelude | M6-2 entry |
| Q2: the fixtures regenerated | Regenerated for M6 (twelve); M1's and M2's fixtures kept and judged against the pre-M6 expectations (`tests/fixtures/pre-m6/`) so the checker's two prelude forms are both tested | M6-2 entry |
| D-5 names no enforcement of the seam ("called from the decision code and nowhere else") | The image checker's seam rule enforces it on the linked image, with a mutation (`time read outside the executor`); beyond the plan's letter, within its budget | M6-3 entry |
| Q4 / D-6: the model instance | Deferred with its reason (below) | M6-4 entry; U-13 |
| Q3: "open item 59 closes" | Item 59 is the run tool's boot-ID wait, closed by M5-4; no open item recorded the kept kexec names; nothing closes (a transcription error in the accepted plan) | open item 87 |
| Q3: "the configuration identities change with the rest"; D-6: the model additive only | M3's policy instances 2 and 3 are generated from the scenarios, so Q3 changed their labeling and configuration identities and object counts; the Rocq proofs pass unchanged on the regenerated instances; the two model test files that pin those values are refreshed, found by the first gates run | open item 88 |

## The model (M6-4): deferred with its reason

`model/proof/Model.v` defines `frame` as a closed enumeration of the
fixed single-hart profile's eleven frames and `gpa` as two addresses,
and Model 0.2's validation, sealing, and derivation theorems are stated
over those types. The MVP's inventory (twelve to seventeen resources,
two 64 MiB windows, up to three shared pages, three harts) is not an
instance of them; making it one means generalizing the types under
proved theorems, which stop condition 4 forbids. M3's policy layer
(`Policy.v`, the generated `Instances.v`) is indexed by naturals and
already holds the te-poc and anchor policy instances. No model
structure, proof, or theorem changes in M6; the two test files that pin
the generated instances' identities follow the scenarios (open item 88,
the stops table below); `./be model-check` and `./be evaluate` pass (the
gates below). The ledger's U-13 states the boundary; a generalized
model belongs to the first verification plan's stage 1
([project snapshot](project-snapshot-mvp-1.0-rc2.md), section 8).

## The gates at `X3`, from this checkout clean at `X3`

Run by a driver under `build/mvp/rc3-gates/` (outside the tree; M5-5's
driver retargeted), each gate's output logged between `start_utc=` and
`end_utc=` lines, in the plan's order, 2026-10-31, workstation `l1`
(Fedora Linux 44, x86_64), the lock's tools (`lock_sha256=2f1b732dcf24`,
unchanged since M5), the host's `build/model/evidence` copied aside
between the last two gates:

| Gate | UTC | Result |
| --- | --- | --- |
| `./mvp/mvp tool-lock check` | 03:54:32 to 03:54:35 | `BE_MVP_LOCK: PASS roles=32 host_only_skipped=0 closure=259 lock_sha256=2f1b732dcf24`; `BE_MVP_LOCK_SELF_TEST: PASS cases=50` |
| `./mvp/mvp check` | 03:54:35 to 03:59:34 | `BE_MVP_CHECK: PASS`; the bundle `files=320 images=253 qemu_attempts=70 rehearsals=7`; `BE_MVP_QEMU: PASS runs=58 attempts=70 refused=12`; `BE_MVP_CAPTURE_SELF_TEST: PASS cases=129 failed=0`; `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=317 rejected=317`; the eight host suites `gcc=clang` (`config scenarios=36 assertions=139` among them); `BE_MVP_BUDGETS: PASS measured=32`; `BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=41 boundary=13` |
| `./mvp/mvp evaluate` | 03:59:34 to 04:04:20 | `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`; `BE_MVP_IMAGE_IDENTITY: PASS images=253 same=253 differing=0` |
| `./mvp/mvp uboot-rehearsal` | 04:04:20 to 04:06:03 | `BE_MVP_UBOOT_REHEARSAL: PASS cases=7 attempts=7 refused=0 uboot=d96d1c22c67b opensbi=78f14d30c951 qemu=10.2.2`: `two-guests`, `te-poc`, and `anchor` for GCC and Clang, and `fallthrough` |
| `make -C mvp kernel-repro LINUX_GIT=<local mirror>` | 04:06:03 to 04:06:34 | `BE_MVP_KERNEL_REPRO: PASS outputs=15 identical; sysroot_files=1065 sysroot_sha256=c931b51b…` |
| `./be model-check` | 04:06:34 to 04:07:35 | `Beryllium Architecture Model 0.2 evidence: PASS`; `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241`; `policy and hart binding proofs: PASS instances=generated`; `policy layer unit tests: PASS checks=169 instances=4 mutations=91` |
| `./be evaluate` | 04:07:35 to 04:08:32 | `BE_EVALUATION: Model 0.2 rootless evidence PASS` |

One earlier attempt is development history, not evidence
(`build/mvp/rc3-gates-attempt-1-4cc5c53a/`, 03:31 to 03:44 UTC): at the
intended `X3` `4cc5c53a` the lock, `check`, `evaluate`, the rehearsal,
and `kernel-repro` passed and `./be model-check` failed in the policy
layer's unit tests on a pinned identity (README item 88, "Soft limits and
stops" below); the pins were refreshed (`ebc49a88`), which moved `X3`,
and the gates ran again from the start.

## The release-candidate record

`./mvp/mvp rc-record` made `mvp/results/20261031-rc3/` at 04:09:57 UTC
from the inputs named explicitly (the host bundle, the evaluator record
`20261031T035934Z`, the host's and the evaluator's model evidence and
the evaluator's logs, the seven rehearsal cases, `kernel-repro`, the
seven gate logs), each checked to name `X3` and the evaluator's identity
checked against `tools/lock/closure.txt` and `tools/evaluator/Containerfile`
at `X3`: `BE_MVP_RC_RECORD: PASS … commit=ebc49a88… files=394` (3.3 MB).
`rc.txt` names `X3`, its tree `0a60a35f…`, the host's OS and
architecture, the lock's (`2f1b732d…`) and closure's (`2875ddd6…`)
SHA-256, and each gate's PASS line with its times; `host/` is the bundle
(`files_rewritten=0`); `evaluator/` the record with `compare-images.txt`;
`model/host/`, `model/evaluator/`, `model/evaluator-logs/`; seven
`rehearsal/<case>/`; `kernel-repro.txt`; `MANIFEST.sha256` (SHA-256
`c9674b53ac270816…`) over every other file. `--verify` passes
(`BE_MVP_RC_RECORD: PASS verify`); the ledger's privacy rule finds nothing
in it. The record is committed in `RC3`, with the board record below.

## The release-candidate board campaign (M6-7)

The session `20261031-com260-rc3` on the COM260, 2026-10-31, 04:12 to
04:38 UTC, from this checkout clean at `X3`, whose 14 board images were
staged (`X3`'s; each 2,584,576 bytes; none equal to release candidate
2's, as M6 changed every image's boot, layout, and configuration). The
board tools were driven from `l1` with `K3_RESET=k3ctl` (the pinned
client, `tools/k3ctl.sha256`), the operator's picocom session
`k3-console-1` holding the serial log (its picocom window named as
`k3-console-1:0`; README item 89), the responsible human having
confirmed the board free and theirs alone until the restore and the
recorded `bootcmd`'s digest (`K3_ENV_CONFIRM=0404ae42737d`, release
candidate 2's), present at the install and the restore (`the k3 is yours
to operate`), the saved `bootcmd` as their default, and no pending
one-shot boot.

| Step | UTC | Result |
| --- | --- | --- |
| (e) preflight before (`k3-preflight`, Fedora up) | 04:12 | `BE_MVP_PREFLIGHT: PASS`; partition 6 ext4 `beryllium` 1 GiB unmounted, `fsuuid` kept private; `env_k3.txt` 227 bytes, sets no `bootcmd` or `be_` name; `region_check=PASS`; `firmware=ID=0x1,Version=0x10006`; Fedora on kernel `7.3.1-300.0` (item 90) |
| (f) staging (`k3-stage`) | 04:12 | 14 images, 2,584,576 bytes each, `SHA256SUMS` and `MD5SUMS` re-hashed after a fresh read-only mount; `md5_distinct=yes`; no trailing space in `staging.txt` (debt sweep 1) |
| (g) clean shutdown | 04:14:25 | `systemctl reboot`, halted at `reboot: Restarting system` |
| (h) two records (`k3-env record`) | 04:14:47, 04:14:53 | two `k3ctl` resets, `s`, `printenv` at each fresh prompt; records 1 and 2 SHA-256 `72443954…` both, equal to release candidate 2's records; V empty; preconditions PASS (`bootdelay=3`, no `preboot`); a first attempt at 04:13 had stopped at the console tool's pane check before any reset or keystroke (item 89) |
| (i) install (`k3-env install`, the human present) | 04:15:08 | at a fresh prompt the seven `setenv` lines, `printenv` equal to record 1 plus exactly the declared lines (`be_orig_bootcmd` equal to record 1's `bootcmd`), `saveenv` `OK`; the wrapper then failed on a stray argument after the PASS, with nothing further typed (item 91) |
| (j) the runs (`k3-campaign`) | 04:16:20 to 04:24:47 | 20 of 20 as declared (table below); 13 selects, each at a fresh prompt at the first attempt with only `be_image` changed and `saveenv` `OK`; no stop |
| (k) restore (`k3-env restore`, the human present) | 04:36:17 | at a fresh prompt `setenv bootcmd "${be_orig_bootcmd}"`, the six deletions, `printenv` equal to record 1, `saveenv` `OK` |
| (l) fresh-prompt check | 04:36:40 | reset, `s`, `printenv`: record 3 SHA-256 `72443954…`, equal to record 1 byte for byte (V empty) |
| (m) Fedora autoboot and preflight after | 04:36:47, 04:38 | one reset, no key; Fedora up with a new boot ID on kernel `7.3.0-65.1` (the saved `f45_rel`'s); `BE_MVP_PREFLIGHT: PASS`; the pair differs in `captured_utc`, `boot_id`, the kernel line and its reserved extents (item 90), and nothing the MVP depends on |
| (n) `board-evidence` | at `X3` | `BE_MVP_EVIDENCE: PASS board … runs=20 pass=20 fail=0 refused=0 stop=0`; 197 files; `source_tree=clean` (re-made once from the stored session, the first copy having `source_tree=dirty changed=1` from the untracked release-candidate record; the two differ in that line and the hashes that carry it); `identifying()` finds nothing; `--verify` PASS |

The runs, each its own `k3ctl` reset with Fedora down, the saved
`bootcmd` running `be_boot` (`nvme scan`; `2584576 bytes read in 2 ms`;
`md5 for 140000000 ... 140276fff ==> D`, D the staged image's MD5;
`Moving Image from 0x140000000 to 0x108000000, end=108277000`; `Loading
Device Tree to 00000002fbd5d000, end 00000002fbd6f2ef ... OK`, release
candidate 2's addresses; `Starting kernel ...`), the shim on hart 0 with
`fdt=0x2fbd5d000`, the M6 prelude `BE_MVP:00 BOOT_VALIDATED` and
`BE_MVP:00 CONFIG_SEALED` (two-guests and the probes `inventory=14
authorities=2 roots=2 harts=0,1,2 identity=16bd3ebb3796bb68`, te-poc
`15`, `4`, `6b72438740dba149`, anchor `17`, `7`, `14bfd613098573f2`; no
`BE_R3:` line in the session), and the terminal marker 11 to 18 s after
the reset; each capture judged in `uboot` mode and passing its five
attribution conditions and its banner audit:

| Run (UTC) | Image | Verdict | What the capture holds |
| --- | --- | --- | --- |
| 04:16:20 | `probe-platform` GCC | PASS | the cold-boot facts of M5's characterization, equal to M0's kexec-time values; the prelude seals two-guests' configuration (`roots=2 harts=0,1,2`) |
| 04:16:49 | `probe-vmid-distinct` GCC | PASS | VMID tagging observed: distinct VMIDs, no stale translation |
| 04:17:18 | `probe-vmid-shared` GCC | PASS | the shared-VMID counterpart |
| 04:17:47, 04:18:06, 04:18:25 | `two-guests` GCC ×3 | PASS | `exits=157` on both domain harts, `records=138 wakes=2` (M0's and release candidate 2's counts) |
| 04:18:55 | `two-guests` Clang | PASS | the same counts |
| 04:19:26, 04:19:45, 04:20:04 | `te-poc` GCC ×3 | PASS | both `MVPINIT 07 CHANNEL` lines; `DENY` `unmapped cause=0x15 injected=0x5 gpa=0x84001000`, `read-only cause=0x17 injected=0x7 gpa=0x84000ff8`, and the reader's second; `exits=163` and `167`; `records=146 wakes=2` (M1-B's) |
| 04:20:34 | `te-poc` Clang | PASS | the same |
| 04:21:05, 04:21:26, 04:21:48 | `anchor` GCC ×3 | PASS | domain 1 `DOMAIN_PAUSED` and `DOMAIN_TERMINATED` at `exits=132` with the measured digest; domain 0 `exits=248 … refused=1`; `records=174 wakes=16` (M2-A's) |
| 04:22:20 | `anchor` Clang | PASS | the same |
| 04:22:53 | `payload` GCC | PASS (fails as declared) | `BE_MVP:FAIL payload` before any hart started |
| 04:23:21 | `reader-write` GCC | PASS (fails as declared) | `BE_MVP:FAIL gstage` with its `DETAIL`, no domain run |
| 04:23:49 | `no-inject` GCC | PASS (fails as declared) | `BE_MVP:FAIL guest-page-fault` |
| 04:24:19 | `wrong-measurement` GCC | PASS (fails as declared) | `BE_MVP:FAIL measurement` |
| 04:24:47 | `no-grant-check` GCC | PASS (fails as declared) | `BE_MVP:FAIL run-timeout`, `DETAIL ticks=0x8000000` |

Every count equals release candidate 2's (ledger C-37, now history) and
the accepted M0, M1-B, and M2-A records', at images none of whose bytes
equal release candidate 2's: M6's boot and layout changed what the
monitor prints before `BE_MVP:01` and nothing the scenarios count. The
session's 39 `k3ctl` resets (1 on Fedora down, 18 at an idle prompt, 20
after a terminal marker) each map to one SPL and one U-Boot banner; no
banner is unexplained; no `s` was lost or retried; no unplanned boot; no
reset was made by hand; no recovery was needed.

**The record.** `mvp/results/20261031-com260-rc3/` (197 files): B0's
retention of the 20 runs (each `check.txt`, `load.txt`, `reset.txt`,
`result.json`, `run.txt`, `SHA256SUMS`, and the excerpt from `Autoboot
in`) and the preflight before; `mvp/session/` with the keystroke log
(482 lines: 91 keys, 74 sends, 73 echoed lines, 91 prompts, 39 resets
and banners, 1 stop, no `missed-s`), `resets.tsv`, the staging record,
and `env/` (the records', install's, 13 selects', and restore's
verdicts and `state.txt`; no `unplanned.txt`); `mvp/preflight-after.txt`
(redacted as B0 redacts the one before); the hand-written Serial log
paragraph; `platform-record.md` with the preflight pair (the `kernel`
row `differs`), the cold-boot probe values beside M0's, and the resets;
`summary.md`; `MANIFEST.sha256` (`79460ad716e09120…`). The full
`printenv` texts stay in the private store
(`~/.local/state/beryllium/k3-env/20261031-com260-rc3/`, mode 0600) and
the picocom log; the record holds their SHA-256s, the `be_` names and
values, V, and the verdicts (Q8 of the M5 plan).

## Soft limits and stops in M6

| Event | Stop | Outcome |
| --- | --- | --- |
| New code 2,545 after M6-2, 3,231 after M6-3, 3,258 at `X3`, against 4,000 | 6 (checkpoints) | Within the limit at both checkpoints and at `X3` |
| The Rocq model's `frame` and `gpa` are closed enumerations | 4 (a model instance that cannot be made additively) | M6-4 deferred with its reason (Q4's default); no theorem changed |
| `claim-ledger.py check` failed at `356150bb` on C-10's pin of `tests/check-capture.py` | none (the ledger's own rule) | C-10 refreshed to the checker's M6 bytes (`53c9ad8e`) |
| `claim-ledger.py check` failed on U-13's coverage word `emulation` | none (the ledger's fixed vocabulary) | Reworded to the vocabulary before the M6-5 commit |
| The first gates run at `4cc5c53a` failed `./be model-check`: the model's policy instances 2 and 3 follow the scenarios, and their pinned identities had not | none (4 considered: no theorem changed; the proofs pass on the regenerated instances) | The pins refreshed (`ebc49a88`, README item 88); `X3` moved; the gates re-run. The M6-4 exit had not been run at M6-4 |
| The console tool's check stopped at `k3-env record` (the tmux session's active pane was not picocom's) | the tool's own stop 1 | Nothing typed, no reset; re-run with the window named (`k3-console-1:0`); README item 89 |
| The preflight pair differs in the kernel release | none (7 considered: no run verdict, count, or layout differs) | The Fedora before the session had been booted by hand as a one-shot test; the saved environment is unchanged and shown restored; README item 90; ledger C-45 |
| The wrapper took a stray `k3-env install` argument as a make goal | none | After the install's PASS; nothing further on the board; README item 91 |
| `board-evidence`'s first copy recorded `source_tree=dirty changed=1` | none | The untracked release-candidate record was in the tree; re-made clean from the stored session |

Every soft limit holds at `X3`: new code 3,258 of 4,000; no guest,
scenario policy, model structure, proof, or theorem line changed; the
lock unchanged.

## Open items

From `mvp/README.md`: 87 (the accepted M6 plan's Q3 names open item 59
in error), 88 (the model's pinned instance identities), 89 (the console
tool's pane check and the tmux window form), 90 (the preflight pair's
kernel), and 91 (the wrapper's stray argument) recorded, 89 and 91 as
later source changes if wanted; 80 (the dongle's power tap) open for the
responsible human, outside the board tools; 83 and 85 closed by debt
sweep 1; 86 closed; 59 unchanged (item 87).

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
U-Boot printed at a fresh prompt, not by its stored bytes. The MVP core
profile is validated by the ported C mechanism, its host tests, the
image checker's binding, QEMU, and the board, not by the Rocq model
(U-13). Not recorded: any claim the required limit excludes; any
release-path step after the first, none of which is started; any use of
kexec (none; the standing rule).
