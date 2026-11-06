<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M7 evidence record

This record holds the evidence of M7, "Interactive guests", on branch
`beryllium/mvp-m7`, made under the accepted [M7 plan](mvp-m7-plan.md)
(`4f4d094e`, accepted 2026-11-01 with M7-2 to M7-6 authorized at the
acceptance record `ae3e9537`, the M7 base) and the accepted
[Plan revision S3-C](mvp-plan.md#plan-revision-s3-c-the-mvp-ladder-and-mvp-1-0-widened-to-interactive-guests-a-first-verification-plan-and-measurement)
(`27d2e557`, its section S3-C.3, S3-C.7, and S3-C.9 item 8). It records
what was run, when, on which commit, and what it printed; it makes no
claim beyond those lines. The gates ran on exact commit
`8418a3777b005debbed8fb5d2d9de54c2bc55250` (`X`: the board record's
commit `058fee76` plus the snapshot self-test fix the first gates run
found; tree clean), and the commits after it hold only this record, the
ledger's rows that cite the board record, the README's records, and the
packet: no monitor, guest, test, tool, scenario, or model byte follows
`X`. The result commit `R` adds this record, the ledger's rows, and the
README's records over `X`; the packet, committed after it, names it.

## What M7 adds, by work package

Each package's files and counts are in `mvp/README.md`, "M7
implementation: M7-2 to M7-6"; this is the index.

| Package | Exact commits | Delivers |
| --- | --- | --- |
| Part 1 Revision 2 (M7-5, first) | `afd395b8`, **accepted** 2026-11-01 (`accept afd395b8`; record `f640275b`) | Security model v1's console path: I17, I18, the operator and the typing tool as trusted inputs, three TCB rows; 199 lines appended, the accepted text byte-identical |
| M7-2 the userland | `7db37366` (merged `ca26940e`; pins `a00e14f7`) | BusyBox 1.36.1 and musl 1.2.6 as pinned, signature-verified external inputs; a soft-float `rv64imac`/`lp64` static BusyBox in the one guest Image (2,063,556 bytes of the `0x300000` budget); `/init-shell` and the verbs `be-chan`, `be-deny`, `be-anchor`; `LICENSES/MIT`; `kernel-repro` 23 outputs |
| M7-3 the monitor's input path | `ba7d0f33` (merged `1d5e3a6e`; pins `165d4c4d`) | The input ring (`0xd000`, `0x1000`; record type 16), the pure focus parser, hart 0's Sstc poll (2^18 ticks) and executor read, the served DBCN read with the write-authority rule and a 256-byte stage, the flush on pause and terminate, `console_input` through the ported R1 request, binding, and root into the sealed state, `BE_MVP:15` to `:18`, SBI implementation versions 5 and 6; host test `input` (17 scenarios, 5,188 assertions) |
| M7-4 the harness | `4c44d244`, `0a9fa026`, `ccb1658e`, `e357711e` (merged `672adff6`; pins `77783693`) | Each scenario's `shell` variant and its session file, the QEMU typist with a per-run nonce, the capture checker's console rules and the hostile variant (`cases=164`, `mutations=399`), the authority report's `configuration` section (`-v2`), the session bound check, `./mvp/mvp sessions` in `check`, `./mvp/mvp live` |
| M7-5 the words and the model | `ad93667d` (merged `a2910c78`), `c0170f4c`, `5ec00ee7`, `873b178b`, `431b7821` | `model/proof/InputRing.v` (386 lines, four theorems, no axiom) with its gate and the `model/Makefile` hook; the claim's console sentences; ledger rows C-47 to C-49, U-14, U-15; the guide's console section; the README's records; erratum 1 |
| M7-5 the board tooling | `0e696c2b`, `e16f9627`, `10559a36`, `cac16240`, `c53cdd9c`, `597ef669` (merged `ff6cff6c`; pins `0dcc2271`) | `probe-console-input` (probe 4); the console tool's `guest-type` and `probe-type` modes under `K3_GUEST_TYPING=human-authorized`; `tools/k3-input-characterize.sh`; `tools/k3-uboot.py` `session`, `gate`, `guest-wait`, `input-judge`; the dry run's two new cases over the fake MVP; the board record's typed-run judgement; staging of the probe and the shell image |
| M7-6 | `058fee76` (the board record), `8418a377` (the snapshot self-test fix); this record; the packet | The gates from the clean tree; the typed characterization and one shell session on the COM260; the records |

## The claim, the limit, and the phrasings

`mvp/docs/claim.md` changed exactly as the plan's "Claim text" fixes
(`c0170f4c`): the blockquote gained the one console sentence after the
sentence on the tested accesses, and the required limit gained the two
sentences on the guests' software and the trusted inputs; no other word
of the claim changed (stop condition 2 was not reached). The
forbidden-phrasing check passes over every document at `X`
(`claim-ledger.py check`, 10 checks; `BE_MVP_CLAIM_LEDGER: PASS checks=10
claims=49 boundary=15`). The ledger's rows C-47 to C-49 and the boundary
rows U-14 and U-15 are M7-5's; after the gates, `R` makes C-47 and C-48
cite the board record and adds C-50, the console's characterization as a
platform fact (below, "After the gates").

## Departures from the plan's letter, recorded in the session

Each recorded in `mvp/README.md`'s M7 entries and open items; none
changes what the claim says beyond the fixed sentences.

| Plan text | As done | Where |
| --- | --- | --- |
| Soft limit 8,000 (checkpoint after M7-4) | Stop condition 9 fired at the checkpoint (7,625 counted then); the human re-set the limit to 9,500 (`limit 9500`); erratum 1 in the plan's decision record. By the counting rule as run at `X`, M7 adds **9,092** lines (C 3,477, Python 4,239, shell 1,089, Make 238, linker scripts 22, the wrapper 21, assembly 6; Rocq 399 reported separately; by the same count the checkpoint stood at 7,548, recorded as 7,625 with `initramfs.list.in` and the licence file counted) | item 111; the plan's decision record |
| Stop 4: no edit to an accepted model gate file | The one-line `model/Makefile` hook (`tests/run-input-ring.sh` after `tests/run-proofs.sh` under `proof`) was added on the human's `your choice`, recorded in the plan's decision record | item 109; U-15 |
| D-3: the parser's three outputs (delivered, dropped, selected) | A fourth, "held": the `~` at line start is held until the next byte decides it, so that read = delivered + dropped + held + selected | M7-3 entry |
| D-11: `two-guests`' session "writes and reads the channel" and names denials | `two-guests` has no role, channel, or denial; its session is the nonce in each domain, `ls /bin \| wc -l`, the `bad-sequence` and `literal` negatives, and the exits; the channel and denial demonstrations are `te-poc`'s and `anchor`'s | item 112 (a plan erratum for the acceptance record to note) |
| D-9's verb list | `be-anchor pause\|terminate` added so that `anchor`'s session can end the protected domain through M2's management path | M7-4 entry |
| D-11: a 300-byte negative provoking `ring-full` | Not provokable in QEMU (the firmware's FIFO and the guest's polling keep the ring from filling); the drop rule is host-tested alone | item 113 |
| Q12: a `live` variant with 2^35 ticks | `./mvp/mvp live` keeps the accepted 2^32 budget (a per-image switch not made) | item 110 |
| D-5 and stop 5: the printed identities unchanged | `policy-check.py`'s manifest hash and the printed `CONFIG_SEALED` identity leave `console_input` out (the sealed canonical R1 identity covers it), so a `shell` variant prints its base scenario's identity | item 108 (M9's) |
| The scenario schema | Versions not bumped: the accepted `model/tools/gen-policy-fixtures.mjs` admits the v2 and v3 strings only; `console_input` is required in all three | M7-3 entry |
| D-1: served reads counted | The served-read counter `dbcn_input` is inside `BE_MVP:12`'s `sbi=` and not its own printed field; `dbcn_read` counts refused reads | M7-3 entry |
| D-3: `BE_MVP:16` on a focus change | Printed on every valid selection, a re-selection included, for the typist's lockstep | M7-3 entry |
| D-1: a firmware read error | Ends the run as `FAIL console` in granting images | M7-3 entry |
| Q4: the shells as variants | The images are named `<scenario>-shell` (image names are unique across scenarios); `prefix=0x7e` printed in `:15` | M7-4 entry |
| D-9: `anchor`'s 260-byte command | Split at 256 by the monitor, as the expectation models | M7-4 entry |
| Q6: the latest stable releases | BusyBox 1.36.1 is busybox.net's latest release marked stable (1.37.0 and 1.38.0 are marked unstable); musl 1.2.6 | M7-2 entry |
| The lock (Q6's pins) | The lock rejects new keys, so the BusyBox and musl pins live in `guest/pins.txt` only; `evaluate.sh` copies the host's verified tarballs into the hidden tree, where the build re-verifies them | M7-2 entry |
| D-9: the init | `-fno-link-libatomic` for GCC 16's driver; `waitpid(-1)` since nolibc lacks `wait4` | M7-2 entry |
| Q10: three to five theorems | Four; the accounting theorem was dropped to stay under 400 lines; `InputRing.v` does not model the setup before the barrier, the firmware read, the range check, timing, fences, or the `:16` to `:18` accounting | U-15; M7-5 entry |
| D-12: the probe "prints each received byte's hex and running counts" | A line per 64 bytes (`bytes=<count so far> hex=…`), the rest at the window's end, then the counts and a SHA-256; the window 2^29 ticks | M7-5 tooling entry |
| D-12: "hart 0 polls" | Hart 0 alone polls; domain 0's hart runs the probe stub's VMID sequence without the switch and parks, as the other probes' harts do | M7-5 tooling entry |
| D-12: the characterization's typist | The console tool's `probe-type` (the human chose not to type); the pacing measured at the typist, 11.7 ms per byte for "10 ms" and 2.7 ms for "1 ms", the tmux and picocom path's overhead | the board record |
| D-12: "the record classifies the firmware console" | `tools/k3-uboot.py input-judge` writes the class into the run's `characterization.txt`; `tools/platform-record.py` accepts the probe's values but has no console-input section (the values are in the run's files) | item 115 |
| Board policy: the pinned `k3ctl` client | The session ran the pinned bytes from a copy under the session's directory because the human's checkout had moved to v1.1 during the session; the pin is unchanged and the new client was not used | item 114; the board record |
| Board policy: the tools type at U-Boot | The human typed `saveenv` by hand at record 2's prompt (storing the recorded environment, no `be_` variable); the install attempt of that moment stopped at the port-open rule and was repeated | the board record's Serial log paragraph |
| M7-5's dry run | Its `uboot-rehearsal.sh` is not extended for probe 4 (the rehearsal's seven cases are unchanged) | M7-5 tooling entry |
| M7-6: the gates from a clean checkout | The first run at `058fee76` failed `evaluate` at the snapshot self-test (no git identity in the evaluator; the self-test had always skipped itself before, in linked worktrees and snapshot clones); `tools/snapshot.sh self_test` now carries its own identity (`8418a377`, outside M7's packages, not a pinned file), and the gates ran again from the start at `8418a377` | M7-6 entry; below |

## The model (M7-5): `InputRing.v` beside `Binding.v`

`model/proof/InputRing.v` (386 lines) and `InputRingAssumptions.v`
import the accepted `Binding.v` unedited and prove four statements over
their own sum types (Binding.v's ring and step types are closed
inductives): one writer per input-ring word; the input ring's
transitions write no control-ring object and the control rings' write
no input-ring object, with the ring's extent computed apart from every
control ring, window, and shared page for `mvp_binding`; the drop rule
conserves bytes and never overruns; a delivered byte goes to the current
focus, a granted and running domain. No axiom; four closed assumption
reports; the accepted gate's counts (24 theorems, 22 assumption reports)
unchanged. `model/tests/run-input-ring.sh` prints `Beryllium MVP input
ring proofs: PASS theorems=4 assumptions_closed=4`, and `make -C model
proof` runs it after `run-proofs.sh` (the hook, above). What the module
does not model is U-15's note.

## The gates at `X` = `8418a377`, from this checkout clean at `X`

Run by a driver under `build/mvp/m7-gates/final/` (outside the tree;
M6-6's driver retargeted), each gate's output logged between
`start_utc=` and `end_utc=` lines, in the plan's order, 2026-11-02,
workstation `l1` (Fedora Linux 44, x86_64), the lock's tools
(`lock_sha256=2f1b732dcf24`, unchanged since M5), the host's
`build/model/evidence` copied aside between the last two gates:

| Gate | UTC | Result |
| --- | --- | --- |
| `./mvp/mvp tool-lock check` | 06:14:21 to 06:14:24 | `BE_MVP_LOCK: PASS roles=32 host_only_skipped=0 closure=259 lock_sha256=2f1b732dcf24`; `BE_MVP_LOCK_SELF_TEST: PASS cases=50`; `BE_MVP_FETCH_SELF_TEST: PASS cases=48` |
| `./mvp/mvp check` | 06:14:24 to 06:24:21 | `BE_MVP_CHECK: PASS`; the bundle `files=367 images=315 qemu_attempts=83 session_attempts=6`; `BE_MVP_QEMU: PASS runs=62 attempts=83 refused=21`; `BE_MVP_SESSIONS: PASS sessions=6 attempts=6 refused=0`; `BE_MVP_CAPTURE_SELF_TEST: PASS cases=164 failed=0`; `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=399 rejected=399`; the nine host suites `gcc=clang` (`input scenarios=17 assertions=5188`, `config scenarios=42 assertions=180`, `sbi scenarios=133 assertions=16291` among them); `BE_MVP_IMAGE_CHECK: PASS gcc clang`; `BE_MVP_GUEST_PINS: PASS files=23 image_bytes=2063556 image_budget=0x300000`; `BE_MVP_LICENSES: PASS identifiers=3 files=884 texts=3 external=2`; `BE_MVP_RUN_TOOL_DRY_RUN: PASS`; `BE_MVP_TOOLS_CHECK: PASS`; `BE_MVP_BUDGETS: PASS measured=40`; `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=49 boundary=15` |
| `./mvp/mvp evaluate` | 06:24:21 to 06:33:50 | `BE_MVP_EVALUATE: host PASS roles=32 …`; `fetch PASS … rpms=259 sources=fedora:116,updates:143` (the host's cache); `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`; `BE_MVP_IMAGE_IDENTITY: PASS images=315 same=315 differing=0`; the snapshot self-test ran inside and passed (`cases=33`) |
| `./mvp/mvp uboot-rehearsal` | 06:33:50 to 06:35:56 | `BE_MVP_UBOOT_REHEARSAL: PASS cases=7 attempts=10 refused=3 uboot=d96d1c22c67b opensbi=78f14d30c951 qemu=10.2.2`: `two-guests`, `te-poc`, and `anchor` for GCC and Clang, and `fallthrough` |
| `make -C mvp kernel-repro LINUX_GIT=<local mirror>` | 06:35:56 to 06:36:38 | `BE_MVP_KERNEL_REPRO: PASS outputs=23 identical; sysroot_files=1065 sysroot_sha256=c931b51b…; musl_tree=files=231 …` |
| `./be model-check` | 06:36:38 to 06:37:49 | `Beryllium Architecture Model 0.2 evidence: PASS`; `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241`; `Beryllium security model v1 policy and hart binding proofs: PASS instances=generated`; `Beryllium MVP input ring proofs: PASS theorems=4 assumptions_closed=4` (the hook); `BE_POLICY_RUN: PASS instances=4 mutations=91` |
| `./be evaluate` | 06:37:49 to 06:38:53 | `BE_EVALUATION: Model 0.2 rootless evidence PASS` |

The first run of the gates is development history, not this evidence
(`build/mvp/m7-gates/attempt-1-058fee76/`, 05:55 to 06:10 UTC): at
`058fee76` the lock and `check` passed and `./mvp/mvp evaluate` failed
at `snapshot-check` inside the evaluator (`BE_MVP_SNAPSHOT: FAIL no
commit was made … git has no identity`; `fatal: unable to auto-detect
email address (got 'root@…(none)')`): this checkout is a standalone
clone mounted at its own path, so the self-test found a repository and
ran, where every earlier `evaluate` had run from a linked worktree or a
snapshot clone and the self-test had skipped itself. The fix,
`8418a377`, was verified in the evaluator image first (`BE_MVP_SNAPSHOT:
PASS self-test cases=33`), and the gates ran again from the start.
Earlier runs of `./mvp/mvp check` on the branch are development history
too: at `77783693` (02:08 to 02:16 UTC; the first attempt stopped at
item 93's timing case under a load average of 7) and at `0dcc2271`
(05:18 to 05:33 UTC, PASS on the first run, with the images the board
session then staged).

## The board step (M7-6): the typed characterization, 2026-11-02

Under board policy item 8 (S3-C.9) and the plan's D-12, after the
human's release of the COM260 (`proceed, K3 board is yours`, 2026-11-01)
and confirmation of the recorded `bootcmd` (`confirm 0404ae42737d`), the
human present at the install and the restore, with the images of
`0dcc2271` (byte-identical to `X`'s: the two commits between add the
board record under `mvp/results/` and the snapshot self-test fix, which
no image reads). The record is
`mvp/results/20261102-com260-m7/` (92 files; `make -C mvp
board-evidence` at 05:53 UTC, its bundle `source_commit=0dcc2271
source_tree=clean`; every run's capture judged again in `uboot` mode with
its keys, nonce, and session file; `BE_MVP_EVIDENCE: PASS board … runs=2
pass=2 fail=0 refused=0 stop=0`; its Serial log paragraph written by
hand from the operator's log). In order:

| Step | UTC | Result |
| --- | --- | --- |
| `k3-preflight` (before) | 03:08 | PASS; Fedora on kernel `7.3.1-300.0…fc45` (the saved `f45_rel` now names it); every MVP extent free; firmware `ID=0x1,Version=0x10006`; partition 6 `ext4`; the `k3ctl` client matching the pin |
| `k3-stage` | 05:34 | PASS `images=16` on `/dev/nvme0n1p6` (`nosymfollow`; by UUID): the fourteen of release candidate 3 rebuilt with the M7 userland (every image 2,748,416 bytes, from 2,584,576), `probe-console-input`, and `two-guests-shell`; MD5 and CRC32 distinct |
| `k3-console.sh check` | 05:34 | **stop 1** once: the client in the human's checkout had moved to v1.1 (SHA-256 `9c11b4f8…` against the pin `7ca3d78a…`); nothing typed, no reset. The pinned bytes were copied under the session (`git show 9fcc1ed:tools/k3ctl/k3ctl`, SHA-256 equal to the pin) and `K3CTL` set to the copy; recorded in `session-note.txt` (item 114) |
| `k3-env record` | 05:35 to 05:36 | PASS: Fedora's clean halt (`systemctl reboot`), two `k3ctl` resets, two records equal (SHA-256 `32753344…`; V empty; `bootcmd_sha256=0404ae42737d…`, equal to release candidates 2 and 3; `variance=none`); the records differ from release candidate 3's only in the human's own `f45_rel`. A first attempt had been refused for `K3_ENV_ACCEPT_V` set empty (it must be unset) |
| The human's `saveenv` | 05:42:20 | At record 2's prompt the human typed `saveenv` by hand (`Saving Environment to mtdENV... OK`), storing the recorded environment: no `be_` variable, `bootcmd` unchanged; the install attempt of 05:42:18 stopped at the port-open rule (no idle prompt while the human typed; no reset; nothing typed) and was repeated |
| `k3-env install` | 05:43 | PASS: `s`, the seven `setenv` lines, `printenv`, `saveenv` (`OK`); `be_image=be-mvp-probe-platform-gcc.img be_part=6` |
| `k3-input-characterize` | 05:43 to 05:44 | select `probe-console-input` (PASS); run `20261102T054405Z` from reset; `probe-type` typed the 64-byte text four times (256 keys, each in `keys.log` and `typed.txt`); `BE_MVP:PROBE console-input total=256 polls=2049 nonzero_polls=209 max_per_poll=5 errors=0 sha256=27576c0c829bf762`; `characterization.txt`: **`class=supplies`**, `pacing_10ms=supplies fast_pacing=supplies`, repetitions `1:64/64,2:64/64,3:64/64,4:64/64`, `pacing_ms=11.7,11.7,11.7,2.7`, `verdict=PASS` (stop 10 did not apply); capture PASS, attribution PASS, banner audit PASS |
| the shell session (the driver's second step) | 05:44 to 05:45 | select `two-guests-shell` (PASS); run `20261102T054456Z` from reset; `guest-type` typed `two-guests/sessions/shell.json` (16 steps, 100 keys, nonce `a95d14ec1c364221`) after `BE_MVP:15 INPUT_ARMED grants=g0,g1 prefix=0x7e`; each domain echoed the nonce in its own focus period alone, `ls /bin \| wc -l` printed `18`, `~x` dropped (`BE_MVP:17 INPUT_DROP bad-sequence`), `~~/bin/echo literal` read literally, both shells exited 0 and powered off; `BE_MVP:18 INPUT read=100 g0=43:29bf01b7f09b6324 g1=46:83304396a376991e dropped=bad-sequence:1`; `BE_MVP:12` `exits=344 sbi=343 dbcn_write=134 lines=63 ring_peak=0x12b8` and `exits=361 sbi=360 dbcn_write=137 lines=63 ring_peak=0x1308` (`dbcn_read=0`: no read refused; the served reads inside `sbi=`); `BE_MVP:13 RUN_COMPLETE domains=2 records=134 wakes=525`; capture PASS in `uboot` mode with `--typed`, `--nonce`, `--session`; attribution PASS; banner audit PASS; 19 s from reset to the terminal marker |
| `k3-env restore` | 05:45 to 05:47 | PASS: `setenv bootcmd "${be_orig_bootcmd}"`, the six deletions, `printenv`, `saveenv` (`OK`); record 3 equal to record 1 (`32753344…`); Fedora autobooted from the restored `bootcmd` to its login prompt |
| `k3-console.sh audit` | 05:47 | `banners=10 resets=10 findings=0` (the first reset on Fedora down, seven at an idle prompt, two after a run's terminal marker; no hand reset; no unplanned boot; no `s` lost) |
| `k3-preflight` (after) | 05:48 | PASS, equal to the preflight before in every fact the MVP depends on, the kernel line included (the boot ID and dmesg timings differ, as they must) |
| `board-evidence` | 05:53 | `BE_RETAIN: PASS runs=2 load_checks=0 files=81`; `BE_MVP_PLATFORM_RECORD: PASS … runs=2 … resets=human:0,k3ctl:2`; `BE_MVP_EVIDENCE: PASS board … runs=2 pass=2`; no ssh target, address, or home path in the record (6 `<home>` rewrites) |

The board is restored and on Fedora. This is a typed characterization
and one session on one board, as the plan bounds it (D-12: no campaign;
release candidate 4's campaign runs the `shell` variants); it is
diagnostic bring-up evidence, never hardware validation. The
environment records' texts stay in the private store
(`~/.local/state/beryllium/k3-env/20261102-com260-m7/`); the record
holds their verdicts and digests.

## After the gates: the ledger's rows cite the board record

In `R`, over `X`, the ledger (`mvp/docs/claim-ledger.json`, rendered
`claim-ledger.md`) changes in three rows and nothing else: C-47 and C-48
gain an evidence entry citing `mvp/results/20261102-com260-m7/MANIFEST.sha256`
(the shell session's routing reconciled with the keystroke log; the
console rules over the whole board capture), C-47's non-claim names the
characterization as done and the board method as still waiting for
release candidate 4's campaign, and **C-50** is added: the console's
characterization as a platform fact (`diagnostic board run`), with
`characterization.txt` and the manifest as its evidence. `./mvp/mvp
claim-ledger render` (`claim ledger render: PASS claim-ledger.md
claims=50 boundary=15`) and `check` (`BE_MVP_CLAIM_LEDGER: PASS checks=10
claims=50 boundary=15`) were run on `R`'s content; the other gates read
no ledger byte and were not run again.

## Soft limits and stops in M7

| Condition | Fired | Disposition |
| --- | --- | --- |
| Stop 9, the soft limit (checkpoint after M7-4) | yes, 2026-11-01 | Returned to the human; re-set to 9,500 (erratum 1); 9,092 at `X` |
| Stop 4, an accepted model gate file | no (the hook is the human's `your choice`, a recorded departure) | — |
| Stop 6, a byte delivered outside the announced focus, in QEMU or on the board; an accounting not reconciling with the keystroke log | no: every session's `:18` reconciled (QEMU 6 of 6; the board's one) | — |
| Stop 10, the firmware console absent, blocking, losing, or corrupting at 10 ms per byte; a banner during a session | no: `class=supplies` at both pacings; no banner during either typed run | — |
| Stop 11, the board unavailable | no: released 2026-11-01, the human present | — |
| Stop 13, a typed line not in its file; typing during U-Boot | no (the console tool's own stop 1 and the port-open rule fired once each, at the tool level, nothing typed) | — |
| Stops 1, 2, 3, 5, 7, 8, 12 | no | — |

The checker-to-monitor size, reported and not limited (the plan, "Soft
limits"; M2's bound was 2.3): at `X`, by M2-5's method with the
harness drivers of the same kind added since (`tests/fake-uboot.py`,
`tests/uboot-rehearsal.sh`, `tests/session-typist.py`,
`tests/guest-shell-smoke.py`), the monitor (`src/*`, `shim/mvp-shim.S`)
is 15,359 lines and the checking code 31,989: **2.083** lines of checking
code per monitor line (2.049 at the M7 base `ae3e9537`; M7's increment
1,511 monitor lines and 3,621 checking lines, 2.40 per monitor line).

## Open items

`mvp/README.md` open items 108 (the printed identity does not cover the
console grant; M9's), 110 (`live` keeps the 2^32 budget), 112 (the D-11
plan erratum), 113 (`ring-full` not provokable in QEMU), 114 (the `k3ctl`
client v1.1 in the human's checkout against the pin), and 115 (the
platform record has no console-input section) are M7's residuals; 109
and 111 are closed. Item 107 (the snapshot push's shape) is the human's,
unrelated to M7.

## Claim boundary

M7's evidence is: host unit tests with GCC and Clang output identical;
the image checker; six scripted sessions typed and judged in QEMU per
toolchain pair; the capture checker's console rules with 399 rejected
mutations; the abstract model's four theorems over the input ring's
discipline; and, on one board, one typed characterization of the
firmware console and one two-guests shell session. It shows that in
those runs each typed byte reached the announced focus and no other
domain, that the accounting reconciled with the keystroke log, and that
no guest byte outside printable ASCII and no guest byte at a line's
start reached the terminal. It does not show that arbitrary guests are
contained (the shell is a demonstration), does not cover what the
operator or the typing tool relays between domains, does not bound the
loss of bytes the firmware does not buffer or the availability of a
domain that fills its output ring, and is not hardware validation of the
COM260 or of K3 parts in general. The ledger's methods for C-47 and C-48
stay QEMU-side until release candidate 4's campaign; C-50 is one board's
fact.
