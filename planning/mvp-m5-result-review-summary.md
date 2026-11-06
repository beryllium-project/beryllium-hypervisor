<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M5 result review and acceptance record

This packet presents the result of M5, "Release candidate 2: boot from
system reset", the milestone the accepted
[Plan revision S3-A](mvp-plan.md#plan-revision-s3-a-boot-from-system-reset-the-board-policy-m5-and-release-candidate-staging)
added to the [MVP plan](mvp-plan.md): MVP 1.0 as one exact commit whose
board campaign boots the candidate's images from system reset through
the board's installed firmware and U-Boot, from a Beryllium partition on
the NVMe, under a boot command installed in U-Boot's saved environment
for the campaign and restored after it; kexec removed from the board
tools and the claim; the U-Boot rehearsal in QEMU in place of the kexec
rehearsal; the clean evidence of the pinned evaluators at the candidate
tree; and the records. It was implemented under the accepted
[M5 plan](mvp-m5-plan.md), whose
[acceptance record](mvp-m5-plan-review-summary.md) holds its
authorization and erratum 1 (the new-code soft limit re-set to 10,000
lines at stop condition 8). It also records the responsible human's
decision on it.

## Decision record

The responsible human accepted exact commit
`3867c66c5df2108e1051d8f8c44c12d62611e485` (the release-candidate commit
`R2`, parent `6dd81ee39dd620a1815605c50c9c916894c9974c`, the candidate
tree `X2`; tree `e70b34ff`) as the M5 result and MVP 1.0 release
candidate 2 on 2026-10-30. The instruction, given in reply to this
packet's request to accept, revise, or defer that exact commit, was
`accept 3867c66c`. The abbreviation was checked to resolve uniquely to
that commit (`git rev-parse --disambiguate=3867c66c`). The instruction
directed nothing else: no push, merge, tag, publication, or release.

- **Scope:** acceptance covers exactly that commit and the claim boundary
  in section 3, the eleven departures of section 3 included. Sections 2
  to 8 are the packet as presented, apart from a note above the section
  8 checklist. Section 1's status rows and the closing lines of section
  9 now show the outcome. The decision itself is recorded only here and
  in the plan's status record.
- **Decision support:** packet commits `653a78f3` and `f685f0be` and
  this acceptance-record follow-up are decision support, not
  implementation; the records and the ledger rows are in `R2` itself.
- **Release candidate 2 supersedes release candidate 1 as the latest
  accepted candidate:** the MVP plan's release path step 1, restated by
  Plan revision S3-A as "the latest release candidate's exact commit is
  accepted", now names `3867c66c`; release candidate 1 (`c5df0cfa`)
  stays accepted history, and its kexec board runs are history (the
  ledger's rows C-29 to C-34, `historical: true`). Steps 2 to 7 (the
  responsible human's selection of what migrates; the clean public
  repository; the gates' re-run there as a new exact commit; the
  human's approval of that commit and its tag; publication; the
  internal repository's archive) each need their own explicit
  instruction, and none follows from this acceptance
  (`LLM_POLICY_ALIGNMENT.md`; S1 H48). Any merge of `beryllium/mvp-m5`
  into the development branch and any push need their own instruction.
- **The standing rule** (`no more kexec unless I approve it`) stays in
  force; M5 used no kexec, and the acceptance changes nothing about it.
- **Push and fast-forward (2026-10-30, the later instruction `approve 1,
  3` on the suggested next steps):** `beryllium/mvp-m5`, through the
  commit that records this push, and `beryllium/mvp-m5-plan`
  (`9b3fa982`) are pushed to the private `origin` as a backup, and the
  development branch `beryllium/single-hart-runtime-r0` is
  fast-forwarded from `fb8accc9` to that same commit (a linear history
  holding the M4 plan, M4, the M5 plan, and M5 with their acceptance
  records) and pushed. The same instruction approved a small debt sweep
  (`mvp/README.md` items 83 and 85; item 80 is the human's, by hand) on
  its own branch, presented as its own exact commit.
- **Evidence status:** the board runs are diagnostic bring-up evidence
  for one board, one reported SBI implementation identity and version,
  and one U-Boot build as its banner reports it, at the candidate's
  images; the firmware and U-Boot are identified by their banners, not
  hashed, and the saved environment is shown restored by what U-Boot
  printed at a fresh prompt, not by its stored bytes. Acceptance adds no
  hardware validation, no qualification, and no formal-verification
  claim, and makes no security claim beyond the required limit of
  `mvp/docs/claim.md`. It does not tag, publish, or release.
- **Open items carried:** `mvp/README.md` 80 (the dongle's power tap,
  the human's, outside the tools), 83 (the record's `Kernel ?` column),
  and 85 (two retained record files end lines in a space; the staging
  tool's fix is a later source change). None blocks the acceptance.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `3867c66c5df2108e1051d8f8c44c12d62611e485` (tree `e70b34ff`), the release-candidate commit `R2`, parent `6dd81ee39dd620a1815605c50c9c916894c9974c`, the candidate tree `X2` (tree `2eaafb36`), on branch `beryllium/mvp-m5` from the M5 plan's acceptance record `9b3fa982`. Comparison base: `9b3fa982`, over the accepted plan `0066794d`; the development branch's tip is `fb8accc9` locally and on the private `origin`. `X2` holds every source change of M5 (M5-2 to M5-4's tools and surfaces, the session's fixes); `R2` adds the two retained records, the ledger rows that cite them, the rendered table, the [evidence record](mvp-m5-evidence.md) and its sidebar entry, the development log's closing entries, and the Git whitespace attributes the retained captures need (`.gitattributes`: M4's exemption widened to `*-rc*/`, and the board excerpts' and staging record's trailing spaces; `mvp/README.md` open item 85), and nothing else (`git diff --stat 6dd81ee3 3867c66c -- mvp ':!mvp/results' ':!mvp/docs/claim-ledger.json' ':!mvp/docs/claim-ledger.md' ':!mvp/README.md'` is empty; the six changed paths outside `mvp/results/` are those named). |
| Current status | Implemented, checked on the host and in the pinned evaluator, rehearsed in QEMU, and run on the board. At `X2`, from this checkout clean at `X2` on `l1` (2026-10-30, 09:09 to 09:23 UTC), the seven gates pass: the lock, `./mvp/mvp check`, `./mvp/mvp evaluate` (253 of 253 images identical between the host and the evaluator), the U-Boot rehearsal (seven cases, six scenario images and the fall-through), `kernel-repro`, `./be model-check`, and `./be evaluate`; `rc-record` made `mvp/results/20261030-rc2/` (430 files) from them. On the responsible human's confirmation that the K3 was free, the release-candidate board session ran at `X2`'s images (07:52 to 08:18 UTC, the human present at the install and the restore): the preflight, the staging, two environment records, the install, twenty runs from system reset (each its own `k3ctl` reset, the saved `bootcmd` loading the selected image from the partition), the restore, the fresh-prompt check equal to the pre-session record, Fedora's autoboot, and the preflight after; twenty of twenty as declared, one stop in the middle (condition 12, a lost `s`, hardened and resumed), no hand reset, no recovery; `mvp/results/20261030-com260-rc2/` (198 files) is its record. `claim-ledger.py check` passes at `R2` (`checks=9 claims=39 boundary=12`; the privacy rule over 549 record files). |
| Decision requested | Accept exact commit `3867c66c` as the M5 result and MVP 1.0 release candidate 2; or request revisions; or defer. The claim's board clause and required limit were fixed by the M5 plan's acceptance (Q7) and are published unchanged in `mvp/docs/claim.md`. Recorded outcome: accepted (instruction `accept 3867c66c`, 2026-10-30); see the [decision record](#decision-record). |
| Successor status | As presented and after the decision: not started and not authorized: every release-path step after the first (the selection of what migrates, the clean public repository, a tag, the gates' re-run there, publication, the archive; MVP plan "Release path" steps 2 to 7); any merge of `beryllium/mvp-m5` into the development branch; any push; any change to a monitor source, a guest input, a scenario, `model/`, or an accepted document's text; root `Makefile`/`be`/`scripts/check-be.sh` integration; development-kernel/BSP selection; any kexec use (the standing rule, decision 8). Acceptance of `R2` is the release path's step 1 restated for the latest candidate and starts no other step. |
| Publication status | Private repository. As presented and after the decision: `beryllium/mvp-m5` and `beryllium/mvp-m5-plan` are local and unpushed (the acceptance instruction directed no push); the development branch `beryllium/single-hart-runtime-r0` is at `fb8accc9` locally and on the private `origin`. No tag, publication, or release. |

As presented: please review exact commit `3867c66c` and accept it,
request revisions, or defer. Outcome: accepted; see the
[decision record](#decision-record).

## 2. Deliverables

| Deliverable | Paths | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| The console tool and the serial-log reader (M5-2, `5aa82ddd`; hardened `b613dd27`, `0bfb1ca8`) | `mvp/tools/k3-console.sh` (659 lines), `mvp/tools/k3-uboot.py` (575) | Typing at U-Boot through the operator's picocom tmux session as fixed templates only, in pieces of at most 60 characters with each echo compared before Enter, every keystroke logged; `s` at `Autoboot in` with a second after 0.5 s; the `k3ctl` reset under the port-open rule; the authorized read-only `diag` | Writes to the board only through U-Boot's prompt, and to its NOR only by `saveenv` at the install, the selects, and the restore; never `env default`, a flash write, `reset`, or `boot` | Is the template set, with `diag`, the whole of what may be typed, and is each refusal (stop 5) real? |
| The environment and staging tools (M5-2, `ccb5e7f4`; the digest witness `09687613`) | `mvp/tools/k3-env.sh` (489), `mvp/tools/k3-stage.sh` (195) | The two records, V, the install, each select, and the restore, each at a fresh prompt with the `printenv` comparison before `saveenv`; the full texts in the private store; the 14 images staged and re-hashed | The restore rule is the claim's "equalled the pre-session record" | Does the comparison before every `saveenv` admit nothing but the declared lines? |
| The run and campaign tools (M5-2, `6252e51b`, `132ef621`; the resume `0bfb1ca8`) | `mvp/tools/k3-run.sh` (207), `mvp/tools/k3-campaign.sh` (93), `mvp/tools/k3-preflight.sh`, `mvp/tools/platform-probe.py` (316) | A run from a reset: the capture, the `uboot` verdict, the five attribution conditions, the banner audit; the group loop; the preflight's partition and `env_k3.txt` checks; kexec removed | The attribution binds a run to its image by the select, the staged SHA-256, the size, the MD5 line, and the verdict | Can a run be credited to an image other than the one that booted? |
| The capture checker's `uboot` mode and the QEMU-only images (M5-2, `d5c04456`, `a4cfb5dd`, `7f26dca2`; `c2b1f850`) | `mvp/tests/check-capture.py` (+739), `mvp/tests/check-image.py` (+96), `mvp/tests/fixtures/*uboot*` | The U-Boot lines in order, the size, one digest line of either form, the move to `0x108000000`, the device tree outside every extent, one SPL and one U-Boot banner, the BSP's noise; the QEMU-only image differs in header bytes 8 to 15 alone | Judges; launches nothing; `kexec` mode kept test-only | Do the mode's rules reject a capture that did not boot from the saved environment? |
| The U-Boot rehearsal in QEMU (M5-3, `02080590`, `3512c280`, `75e7b894`) | `mvp/tests/uboot-rehearsal.sh` (412), `mvp/tests/uboot-rehearsal/run-qemu-uboot.py` (791), the lock roles | B3's pinned upstream U-Boot v2022.10 under OpenSBI on the eight-hart k3-like machine; the session's `be_` lines and `bootcmd` typed, each scenario image booted from an ext4 partition, the missing-image fall-through | Emulation of the boot command, the ext4 load, and `booti`; not of the BSP's environment storage; `crc32` where the board uses `md5sum` | Is the rehearsal's departure from the board (`crc32`, virtio, a typed `boot`) stated wherever it is cited? |
| The fake U-Boot and the dry run (M5-2, `511dd4c0`; cases added through `0bfb1ca8`, `ec6b51d3`) | `mvp/tests/fake-uboot.py` (585), `mvp/tests/fake-board.py`, `mvp/tests/run-tool-dry-run.sh` | Install, select, restore, a run from reset, a campaign with a resume, the characterization, a template refusal, an echo mismatch, a `printenv` mismatch, one, two, and four lost `s`, the pane mode, an unexplained banner, the record with nothing private | Host test; the fake's stamps and noise are the BSP's as recorded | Do the negative cases fail the tools for the right reason? |
| The record writers (M5-2, `0ac1821d`; `ec6b51d3`, `44233488`, `6dd81ee3`) | `mvp/tools/evidence.py` (+343), `mvp/tools/platform-record.py` (+106), `mvp/tools/rc-record.py` | The board record of a U-Boot session; the preflight pair; the cold-boot probe values beside M0's; MAC and `serial#` as code names; the `uboot-rehearsal` gate | Nothing identifying in a record (B0's rule and M4-A's) | Is anything in the two records identifying? |
| The release surfaces (M5-4, `7997bbb0`, `09219507`, `6a5bf337`, `cd597e29`, `55c36876`) | `mvp/docs/claim.md`, `mvp/docs/guide.md`, `mvp/docs/ai-assistance.md`, `mvp/docs/claim-ledger.json`/`.md`, `planning/mvp-rc-walkthrough.md` | The board clause and required limit for a boot from reset; the guide's section 4; the disclosure; the ledger's U-Boot row and the kexec rows as history; the operator's walkthrough | The plan's fixed texts | Does any surface say more than the records support (section 3)? |
| The gates record (M5-5, in `R2`) | `mvp/results/20261030-rc2/` (430 files) | `rc.txt` with `X2`, its tree, the host, the lock's and closure's SHA-256, and each gate's PASS line and times; the bundle; the evaluator record with `compare-images.txt`; the model evidence; the rehearsal records; `kernel-repro`; the manifest | Host, evaluator, and emulation evidence | Does each input name `X2`? |
| The board record (M5-6, in `R2`) | `mvp/results/20261030-com260-rc2/` (198 files) | Twenty runs from reset at `X2`'s images with their captures, verdicts, attribution, and reset records; the keystroke log; the environment verdicts; the staging record; the preflights before and after; the serial-log note; the platform record | Diagnostic bring-up evidence for one board, one SBI identity, one U-Boot build | Do the environment verdicts show the restore the claim states, and nothing else saved? |
| The evidence record (M5-7, in `R2`) | `planning/mvp-m5-evidence.md` | The files and counts, the departures, the characterization, the gates, the records, the campaign, the stop, the limits, the claim boundary | Records what was run and printed | Does it claim anything the records do not hold? |
| The maintenance tool (delivered with the plan; `f3a04a86`) | `mvp/tools/k3-make-partition.sh`, `mvp/tests/test-k3-make-partition.sh` | The human's partition tool; `orphan_present` as mount state | Run by the human with `sudo`, once | Closed by its use (README item 76) |
| The development log and status pages | `mvp/README.md` (M5 entries, open items 71 to 84), `planning/mvp-m5-plan-review-summary.md` (erratum 1), `planning/HANDOFF.md`, `planning/roadmap.md`, `planning/README.md`, `planning/.vitepress/config.mts` | | | |

Exact changed-file inventory outside `mvp/results/`:

```text
# git diff --name-status 9b3fa982 3867c66c | grep -v '^A.mvp/results/'
M	.gitattributes
M	mvp/Makefile
M	mvp/README.md
M	mvp/docs/ai-assistance.md
M	mvp/docs/claim-ledger.json
M	mvp/docs/claim-ledger.md
M	mvp/docs/claim.md
M	mvp/docs/guide.md
M	mvp/mvp
M	mvp/tests/check-capture.py
M	mvp/tests/check-image.py
M	mvp/tests/fake-board.py
M	mvp/tests/fake-partition-tools/k3-nvme.json
A	mvp/tests/fake-uboot.py
A	mvp/tests/fixtures/board-uboot-two-guests-gcc.log
A	mvp/tests/fixtures/qemu-uboot-two-guests-clang-hart6.log
D	mvp/tests/kexec-rehearsal.sh
D	mvp/tests/kexec-rehearsal/init.c
M	mvp/tests/run-tool-dry-run.sh
M	mvp/tests/test-k3-make-partition.sh
R054	mvp/tests/test-kexec-load.py	mvp/tests/test-platform-probe.py
A	mvp/tests/uboot-rehearsal.sh
A	mvp/tests/uboot-rehearsal/run-qemu-uboot.py
M	mvp/tools.mk
M	mvp/tools/claim-ledger.py
M	mvp/tools/evidence.py
M	mvp/tools/k3-campaign.sh
A	mvp/tools/k3-console.sh
A	mvp/tools/k3-env.sh
M	mvp/tools/k3-make-partition.sh
M	mvp/tools/k3-preflight.sh
M	mvp/tools/k3-run.sh
A	mvp/tools/k3-stage.sh
A	mvp/tools/k3-uboot.py
D	mvp/tools/kexec-load.py
M	mvp/tools/lock/tool-lock.conf
M	mvp/tools/lock/tool-lock.py
M	mvp/tools/make-control.py
A	mvp/tools/platform-probe.py
M	mvp/tools/platform-record.py
M	mvp/tools/rc-record.py
M	planning/.vitepress/config.mts
A	planning/mvp-m5-evidence.md
M	planning/mvp-m5-plan-review-summary.md
M	planning/mvp-rc-walkthrough.md
```

`git diff --stat 9b3fa982 3867c66c -- mvp/src mvp/shim mvp/guest
mvp/scenarios mvp/tools/gen-scenario.py mvp/tools/policy-check.py model`
is empty: no monitor source, shim, guest input, scenario, generator,
policy checker, or `model/` file changed; the 14 board images are
byte-identical to release candidate 1's (`mvp/results/20261029-rc/host/
images.sha256`).

## 3. Claim boundary

**Supported by `R2`:** the MVP claim's board clause as published: on the
COM260 the candidate's twenty board images booted from system reset by
the board's installed firmware and U-Boot, which loaded each from the
`beryllium` partition under the installed boot command, twenty of
twenty as declared, each run attributed to its image by the five
conditions; the counts M4 compared equal release candidate 1's and
`anchor`'s equal M2-A's; the environment U-Boot printed at a fresh
prompt after the restore equalled the pre-session record (normalized as
the plan states); the seven gates pass at `X2`; the lock's tools built
every image byte-identically inside the pinned evaluator; the U-Boot
rehearsal passes in QEMU for every scenario image of both toolchains and
falls through on a missing image.

**Trusted or assumed:** the accepted M0 to M4 results and M3's model
work, unchanged; the external Linux input by its pins; the board's
firmware and U-Boot by their banners and the SBI identity Fedora's log
reports (`ID=0x1 Version=0x10006`), not hashed; U-Boot's `md5sum` as the
digest witness (its `crc32` prints nothing on this BSP); the `k3ctl`
client (by its SHA-256) and the dongle, outside the lock; the operator's
picocom session and its log as the serial witness; the responsible
human's statements that the recorded `bootcmd` is their default, that
no one-shot boot was pending, and that the other project stayed off the
board from install to restore.

**Not run or unavailable:** hardware validation, qualification, or
formal verification of any kind; any comparison of the NOR's stored
bytes (the environment is shown restored by what U-Boot prints); any
hash of the firmware; the dongle's power tap as a recovery path (README
item 80; the tools never power the board off or on); the rehearsal's
`aia=none` fallback (not needed); a second board.

**Explicitly not implemented:** any release-path step after the first;
any kexec launch (the standing rule); any monitor, guest, scenario, or
`model/` change; `fw_printenv` or any Linux-side view of the saved
environment; a resume of a stopped session other than at a group
boundary.

**Departures for your attention** (each recorded in the evidence record
and `mvp/README.md`): (1) the digest witness is `md5sum` on the board
and `crc32` in QEMU (the plan: `crc32`); (2) the clean shutdown is
`systemctl reboot` (the plan: `poweroff`, which powers this board off);
(3) the `be_ld` line is typed in two pieces of at most 60 characters;
(4) this BSP prints no `Environment size` trailer; (5) `nvme scan`
precedes the typed load; (6) `diag`, three read-only lines at the
characterization, on your authorization; (7) a session's first reset
may rest on prior state; (8) a second `s` after 0.5 s without a prompt;
(9) the stopped session resumed at a group boundary; (10) the gates ran
once after the campaign at the final `X2` rather than before it (the
board images did not change); (11) `.gitattributes` changed in `R2`,
as in M4's `R`, for the retained captures' whitespace, and two record
files end lines in a space (open item 85).

## 4. Load-bearing invariants

| Property | Contract | Implementation | Evidence |
| --- | --- | --- | --- |
| Only the template lines are typed | M5 plan "Typing at U-Boot", stop 5 | `k3-console.sh`'s templates and parameter patterns | the dry run's refusal case; the session's keystroke log: 93 keys, every line a template |
| Nothing is saved but at a fresh prompt after a passing comparison | "Restore verification", steps 1 to 5 | `k3-env.sh` (`printenv` before each `saveenv`; a bare `setenv` deletes) | `env/install.txt`, 13 `select-*.txt`, `restore.txt`: every check PASS before `saveenv OK`; record 3 = record 1 |
| Every reset is `k3ctl` under the port-open rule | "Resets and the dongle" | `k3-console.sh` can-reset conditions through `k3-uboot.py` | `resets.tsv`: 41 resets, reasons `fedora-down` 1, `idle-prompt` 18, `terminal-marker` 22; 41 banners, none unexplained |
| A run is its image's | "Run attribution and distinctness" | `k3-run.sh`'s five conditions | every `run.txt` `attribution=PASS selected=yes staged_sha256=yes size_md5=yes check=yes`; the 14 MD5s distinct |
| The capture shows a boot from the saved environment | `--mode uboot` | `check-capture.py` | each capture: one SPL and one U-Boot banner, `Autoboot in`, `bytes read`, the MD5 line, the move to `0x108000000`, the device tree outside every extent, `Starting kernel ...`; the mutation fixtures |
| The board images are the candidate's | "The session protocol" step (f) | `k3-stage.sh` re-hashing after a fresh read-only mount | `stage/staging.txt` SHA-256s equal to `X2`'s `images.sha256` and release candidate 1's |
| No identifying string in a record | B0's rule; M4-A; Q8 | `evidence.py` `rewriter`, `b0_sanitize`, `identifying()`; `claim-ledger.py` `check_privacy` | `identifying()` finds nothing in the board record; `claim ledger privacy: PASS` at `R2`; the private store holds the full texts |
| Every gate's evidence binds to `X2` | M5-5 | `rc-record.py` | `BE_MVP_RC_RECORD: PASS … commit=6dd81ee3… files=430`; self-test mutations |
| The retained records are never edited | M0-B's rules | `MANIFEST.sha256`; `--verify` | the five accepted records verify unchanged; the two new ones verify |

## 5. Review history, stops, and errata

| Event | Resolution |
| --- | --- |
| The M5 plan reviewed by `claude-opus-5.5` before presentation: 16 findings | Incorporated in `0066794d`, accepted (the plan's review record) |
| The partition tool's apply exited 5 (`orphan_present` on the mounted F45 `/boot`) | A mount-state flag, ignored like `needs_recovery` (`f3a04a86`); the partition was made correctly; the backups verified |
| **Stop 8** (after M5-2/M5-3): new code 6,865 lines against 5,000 | The human re-set the limit to 10,000 (erratum 1, `154dc810`); 7,439 at `X2` |
| Six characterization attempts stopped on BSP and board facts (`poweroff` powers the board off; the reset does not wake it; no `Environment size` trailer; `nvme scan`; `crc32` silent) | Each fixed with dry-run coverage (`b514df1c`, `5e1d0b49`, `3a9c54ef`, `59d782a4`, `7e833730`, `b613dd27`, `09687613`); the seventh attempt passed |
| The first gates run failed `evaluate` (the partition self-test as root inside the evaluator) | Fixed (`3433643a`); the gates re-run at the final `X2` |
| **Stop 12** (the campaign's fourth select): `s` lost twice | Hardened and resumed (`0bfb1ca8`); 20 of 20; two unplanned boots recorded and not counted |
| `board-evidence` failed B0's retention check (an unredacted root UUID in the preflight after) | Fixed with a dry-run case (`ec6b51d3`); the record re-made |
| A device-tree node rewritten as `<board-ssh>` in the excerpts (seen in your Q8 review) | Fixed with a self-test case (`44233488`) |
| `rc-record` refused the third gates run's record: the new self-test case's own text (`name@unit-address:`, `user@host:`) in the evaluator's retained log read as an ssh target | Reworded (`6dd81ee3`); `X2` moved and the gates ran again |
| `k3ctl power` taps did not wake the powered-off board (by hand) | Recorded (README item 80); outside the tools |

**Open for human judgment:** the eleven departures of section 3; README
item 80 (the dongle's power tap; the power-on's cause not established);
item 83 (the record's run table shows `Kernel ?`, cosmetic); the two
ledger review items, which are judgments, not checks.

**Not run by SOP:** no review of the result by another model; no
separate scope review; no deep security review. Implementation ran on
`claude-opus-5.5` sub-agents at `max` effort with the `long_context`
tier for M5-2 to M5-4 and the digest witness, orchestrated and reviewed
line by line by `claude-fable-5.1`, which also ran the characterization,
the gates, the board session, and the record tools, and wrote the
evidence record and this packet.

## 6. Validation and retained evidence

All on the workstation `l1` (Fedora Linux 44, x86_64), the lock's
tools (`lock_sha256=2f1b732dcf24`), 2026-10-30 UTC. Each line names
what the command covers; the evidence record has the gate table with
times.

| Command | When | Boundary | Result |
| --- | --- | --- | --- |
| `./mvp/mvp tool-lock check` | 09:09, clean at `X2` | the 32 locked roles on this host | `BE_MVP_LOCK: PASS roles=32 host_only_skipped=0 closure=259` |
| `./mvp/mvp check` | 09:09 to 09:14, clean at `X2` | host unit tests, the image and capture checkers with their mutations (283 rejected), the policy checks, the dry run on the fake U-Boot, the QEMU suite (77 attempts), the rehearsal driver's self-test, the ledger (34 rows at `X2`), the record tools' self-tests | `BE_MVP_CHECK: PASS` |
| `./mvp/mvp evaluate` | 09:14 to 09:19, clean at `X2` | the same inside the pinned evaluator; image identity | `BE_MVP_EVALUATE: PASS`; `BE_MVP_IMAGE_IDENTITY: PASS images=253 same=253 differing=0` |
| `./mvp/mvp uboot-rehearsal` | 09:19 to 09:21, clean at `X2` | emulation: B3's pinned U-Boot v2022.10 under OpenSBI, the session's lines typed, six scenario images booted from ext4 and judged in `uboot` mode, the fall-through | `BE_MVP_UBOOT_REHEARSAL: PASS cases=7 attempts=7 refused=0` |
| `make -C mvp kernel-repro` | 09:21, clean at `X2` | the guest kernel's reproducible build | `BE_MVP_KERNEL_REPRO: PASS outputs=15 identical` |
| `./be model-check`, `./be evaluate` | 09:21 to 09:23, clean at `X2` | the accepted M3 model work, unchanged: proofs about the abstract model, differential agreement | `… evidence: PASS`; `BE_EVALUATION: Model 0.2 rootless evidence PASS` |
| `./mvp/mvp rc-record` | 09:23, clean at `X2` | the seven gates' record from named inputs each checked to name `X2` | `BE_MVP_RC_RECORD: PASS … commit=6dd81ee3… files=430`; `--verify` PASS |
| `./mvp/mvp board-evidence` | after the gates, clean at `X2` | the board record from the session's stored captures and logs, each run judged again | `BE_MVP_EVIDENCE: PASS board … runs=20 pass=20 fail=0 refused=0 stop=0`; `source_tree=clean`; `--verify` PASS `files=198` |
| `./mvp/mvp check` | clean at `R2` | the ledger's 39 rows against the committed records; the privacy rule over 549 record files | `BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=39 boundary=12`; `BE_MVP_CHECK: PASS` |
| `make -C mvp lint`, `npm run docs:source-check`, `git diff --check` | before `X2` and before `R2` | shell and Python lint; the documentation source gate (links, routes, privacy); whitespace | PASS |
| The board session (`k3-preflight`, `k3-stage`, `k3-env record`/`install`/`restore`, `k3-campaign`) | 07:52 to 08:18, at `0bfb1ca8`'s images = `X2`'s | diagnostic board runs on one COM260 | 20 of 20 as declared; the restore rule satisfied; `BE_MVP_PREFLIGHT: PASS` before and after |

The gates ran on the exact clean commit `X2`; the board session ran at
an earlier commit whose images are byte-identical to `X2`'s (no
image-bearing file changed between `0bfb1ca8` and `X2`: the four
commits between them touch `evidence.py`, `claim-ledger.py`,
`fake-board.py`, the dry run, the guide, and the README), and its record
was made from the stored captures at `X2`. The retained evidence:
`mvp/results/20261030-rc2/` and `mvp/results/20261030-com260-rc2/`
(manifests `fbe1f4ab…` and `4affd8f2…`), the ledger rows C-10 and C-35
to C-39, and `planning/mvp-m5-evidence.md`. Not retained: the raw
serial log (the operator's, outside the repository), the full
`printenv` texts (the private store), and the gates' driver logs
(`build/mvp/rc2-gates/`).

## 7. Recommended human review sequence

1. Section 1 and the claim boundary (section 3), then
   `mvp/docs/claim.md`'s board clause and required limit against the M5
   plan's "Documents and the claim (M5-4)".
2. The evidence record `planning/mvp-m5-evidence.md`, then
   `mvp/results/20261030-com260-rc2/mvp/session/env/` (the verdicts),
   `platform-record.md`'s preflight pair and resets, and
   `mvp/results/20261030-rc2/rc.txt`.
3. `mvp/docs/claim-ledger.md`: C-10 and the new rows against the
   records they cite; the kexec rows as history.
4. `mvp/tools/k3-console.sh`'s templates and `k3-env.sh`'s comparison
   before `saveenv`; `mvp/tests/check-capture.py`'s `uboot` mode.
5. `mvp/docs/guide.md` section 4 and `mvp/docs/ai-assistance.md`.
6. The development log `mvp/README.md` from item 71 on.

Read-only commands, in a detached worktree so local changes cannot affect
what you read or run:

```sh
git worktree add --detach /tmp/be-m5-review 3867c66c5df2108e1051d8f8c44c12d62611e485
cd /tmp/be-m5-review
git --no-pager log --oneline 9b3fa982..HEAD
git --no-pager diff --stat 6dd81ee3 HEAD -- . ':!mvp/results'
git --no-pager diff --stat 9b3fa982 HEAD -- mvp/src mvp/shim mvp/guest mvp/scenarios model
python3 -B mvp/tools/evidence.py --verify mvp/results/20261030-com260-rc2
python3 -B mvp/tools/rc-record.py --verify mvp/results/20261030-rc2
python3 -B mvp/tools/claim-ledger.py check
cat mvp/results/20261030-com260-rc2/mvp/session/env/records.txt \
    mvp/results/20261030-com260-rc2/mvp/session/env/install.txt \
    mvp/results/20261030-com260-rc2/mvp/session/env/restore.txt
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The scope matches the accepted M5 plan at `0066794d` with Q1 to
      Q16 at their defaults, erratum 1, and Plan revision S3-A.
- [ ] The claim's board clause, the required limit, and the ledger's
      rows and non-claims say no more than the records support.
- [ ] The trust assumptions are acceptable: the firmware and U-Boot by
      their banners and SBI identity, `md5sum` as the witness, the
      `k3ctl` client and dongle outside the lock, the operator's picocom
      log as the serial witness, your own statements about `bootcmd`.
- [ ] The negative paths are covered: the dry run's refusals and
      mismatches, the lost-`s` cases, the five board negatives as
      declared, the checkers' mutations.
- [ ] The eleven departures are acceptable as recorded.
- [ ] Successor work stays excluded: release-path steps 2 to 7, any
      merge or push, any source or accepted-text change, any kexec use.
- [ ] Decision: accept exact commit `3867c66c` as the M5 result and
      MVP 1.0 release candidate 2; request revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `3867c66c5df2108e1051d8f8c44c12d62611e485` and the date. The acceptance record names that SHA;
  the plan's status record and the status documents are updated to
  match. That is the release path's step 1 for the latest candidate;
  steps 2 to 7, any merge of `beryllium/mvp-m5` into the development
  branch, and any push each need their own instruction.
- **Request revisions:** a new commit and a new packet follow;
  `3867c66c` is not treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts.

**Status:** exact commit `3867c66c5df2108e1051d8f8c44c12d62611e485`
(`R2`, over the candidate tree `X2` `6dd81ee3`) is responsible-human
accepted as the M5 result and MVP 1.0 release candidate 2 as of
2026-10-30 (instruction `accept 3867c66c`). It is on branch
`beryllium/mvp-m5`, pushed to the private `origin` with
`beryllium/mvp-m5-plan` on the later instruction `approve 1, 3`, and the
development branch `beryllium/single-hart-runtime-r0` is fast-forwarded
to the commit recording that push (the decision record). Release
candidate 1 (`c5df0cfa`) is accepted history. The release path's step 1
holds for release candidate 2; no later step is started. Its board
evidence is twenty diagnostic runs from system reset on one COM260;
nothing is hardware validation.

**Next:** nothing waits on you; the approved debt sweep (items 83 and
85) follows on its own branch. Any release-path step needs your own
instruction.

**Action required from you:** none; the decision is recorded.
