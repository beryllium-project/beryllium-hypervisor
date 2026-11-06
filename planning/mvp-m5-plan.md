<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M5 plan: release candidate 2, boot from system reset

## Decision record

The responsible human accepted this plan at exact commit
`0066794dbec22807d46cc274f2ad00fb79b555ae` (parent `0d134bbc`, Plan
revision S3-A's commit, on branch `beryllium/mvp-m5-plan` from
`6a5f6fed`, the tip of `beryllium/mvp-m4`) on 2026-10-29, and separately
authorized M5 implementation. The instruction, given in reply to the
[review packet](mvp-m5-plan-review-summary.md)'s request to decide on
`0d134bbc` and then on `0066794d`, was `accept 0d134bbc and 066794d,
authorize m5`. The written `066794d` matches no object
(`git rev-parse --disambiguate=066794d` returns nothing); `0066794d`
resolves uniquely to this commit and was the only decision-2 target the
packet presented, so it is read as `0066794d` with its leading zero
dropped, as the M4 plan's `0d02df27` was read as `0d02df72`. The same
instruction accepted Plan revision S3-A at exact commit `0d134bbc`, the
ordered decision this plan depends on. The first cut of this plan,
`3d38dafd`, was rewritten before presentation (one line, the partition
tool's line counts) and was never presented or accepted.

- **The result (2026-10-30):** the M5 result, exact commit
  `3867c66c5df2108e1051d8f8c44c12d62611e485` (`R2`, over the candidate
  tree `X2` `6dd81ee3`), is responsible-human accepted as MVP 1.0
  release candidate 2 by the instruction `accept 3867c66c`; the
  [M5 result review and acceptance record](mvp-m5-result-review-summary.md)
  carries the decision and the eleven plan-letter departures, and the
  [M5 evidence record](mvp-m5-evidence.md) the evidence. Only the
  status record's trailing lines below were added afterwards; the plan
  text is as accepted.
- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted, including the
  pre-decision status text below; only this section and the acceptance
  fields in the status record were set afterwards.
- **Open questions:** Q1 to Q16 were not answered, so their defaults
  apply: the partition from p3 by the delivered tool (Q1); the literal
  load address (Q2); the fall-through `bootcmd` (Q3); the checker's
  `kexec` mode kept test-only (Q4); 20 counted runs, the probes first
  (Q5); the kexec code removed with the read-only probe kept and the
  `KEXEC_*`/`kexec_fdt` names unchanged (Q6); the claim's clause and
  limit text (Q7); hashes and verdicts committed, full environment texts
  private (Q8); B3's pinned U-Boot for the rehearsal (Q9); the fixed
  templates (Q10); the probes from reset (Q11); the picocom tmux session
  (Q12); the model split (Q13); `k3ctl` or human resets only (Q14); the
  human present at install, restore, and recovery (Q15); release
  candidate 1 as accepted history (Q16).
- **Authorized** (`authorize m5`): work packages M5-2 to M5-7 and the
  characterization M5-6a under this plan, on branch `beryllium/mvp-m5`
  from this acceptance-record commit, ending in one review packet for
  the release candidate 2 commit `R2`. M5-6a and M5-6 issue no board
  command before the human has created the partition with the delivered
  tool and confirmed that the board is free, and the human is present at
  the install, the restore, and any recovery. Each
  [stop condition](#stop-conditions) returns M5 to the responsible
  human; a soft limit exceeded returns the limit for re-evaluation (stop
  condition 8). The repository's model split applies.
- **Not authorized:** any release-path step; any push, merge, or tag;
  any kexec use (S3-A policy item 2; stop condition 11); any write to
  SPL, OpenSBI, U-Boot, or the environment partition outside the recorded
  session; any change to a monitor source, the shim, a guest input, a
  scenario, the generator, an expectation, the checker's rules beyond the
  new mode, the lock beyond the enumerated roles, `model/`, or an accepted
  document's text; root `Makefile`/`be`/`scripts/check-be.sh`
  integration; U-Boot's `reset` or `boot`; a second serial reader; an SD
  card.
- **Evidence status:** acceptance adds no implementation or evidence.
  Nothing of M5 has been built; the partition tool's one `--apply` on the
  board is the human's act and had not happened at acceptance. Hardware
  is `NOT RUN` for M5.

## Decision requested

**Status:** accepted on 2026-10-29, with M5 implementation authorized;
see the [decision record](#decision-record). As presented, the plan was
proposed and not accepted, as the paragraph below states.

**Status as presented:** proposed for responsible-human review; not
accepted. No M5 work has started: nothing under `mvp/` has changed for M5 except the
delivered partition tool and its host self-test
(`mvp/tools/k3-make-partition.sh`, `mvp/tests/test-k3-make-partition.sh`,
`mvp/tests/fake-partition-tools/`), which the human reviews and runs, and
which no Makefile target or wrapper command runs yet; nothing has been
built; no board command of M5 has been issued. The board facts below come
from the retained B3, B5, B6, M0 to M2, and release candidate 1 records,
the board's serial log, the human's board-information wiki, and a
read-only listing of the board's NVMe taken over `ssh` on 2026-10-29
(`lsblk`, `blkid`, `sfdisk --dump`, `btrfs filesystem show`,
`dumpe2fs -h`; no mount, no write; kept in the session's private files,
not the repository). *Fact* marks what a record or source shows,
*inference* reasoning from facts, *review* a measurement or finding of
this plan's steering review.

This plan is the bounded plan for **M5**, the milestone
[Plan revision S3-A](mvp-plan.md#plan-revision-s3-a-boot-from-system-reset-the-board-policy-m5-and-release-candidate-staging)
of the [MVP plan](mvp-plan.md) adds on the responsible human's direction
of 2026-10-29, `modify the plan so that the mvp candidate boots from
system reset. I don't know where those safety rules came from.` S3-A
states the board policy (boot from reset; kexec not used from here on
unless the human approves a stated need; the NOR firmware never written;
U-Boot's saved environment changed only within a recorded session and
restored; one Beryllium partition; `k3ctl` or human resets; templated,
recorded U-Boot typing), the release-candidate staging (release candidate
1, exact commit `c5df0cfa`, accepted history; release candidate 2, M5's
result), and decision D17. This plan carries the policy out: it is
presented with S3-A as the second of two ordered decisions, and it is
void without S3-A.

M5 changes no monitor source, no shim byte, no guest input, no scenario,
no generator, no expectation, and no `model/` file. It rewrites the MVP
line's board tools for a boot from reset (a console tool that types fixed
line templates into the operator's picocom session; staging, environment,
run, and campaign tools; the capture checker's `uboot` mode), removes the
kexec loader, its test, its rehearsal, and the load check while keeping
the read-only platform probe, replaces the kexec rehearsal in QEMU with a
U-Boot rehearsal, rewrites the claim's board clause and the release
surfaces, characterizes the board from a cold boot, runs one board
campaign under the policy after the human creates the partition, runs the
clean gates, and presents the result as release candidate 2 in the form
M4 used: the candidate tree `X2`, then one commit `R2` that records the
evidence made against it.

Accepting this plan would authorize work packages M5-1 to M5-7 under it,
on branch `beryllium/mvp-m5` from this plan's acceptance record, ending
in one review packet for `R2`, with the characterization (M5-6a) and the
campaign (M5-6) each waiting on the human's confirmation that the board
is free and, for the campaign, that the partition exists. It would fix
the claim's new board clause and required-limit text (Q7). It would not
authorize any release-path step, a tag, a push, a merge, a public
repository, root `Makefile`/`be`/`scripts/check-be.sh` integration, any
kexec use, any write to the NOR firmware, or any change to a monitor
source, the shim, a guest input, a scenario, the generator, `model/`, or
an accepted document's text (the maintained status documents and
`mvp/README.md` are not accepted documents). Each
[stop condition](#stop-conditions) returns M5 to the responsible human.

The steering review of this plan's draft (`claude-opus-5.5`, 2026-10-29,
at the responsible human's request) returned "ready with corrections",
with two blockers and fourteen should-fix or consider findings; all are
incorporated here and listed in the [review packet](mvp-m5-plan-review-summary.md).
The two blockers were real: a U-Boot rehearsal in QEMU with the board
images would put them at the wrong address (`booti` relocates to QEMU's
RAM base plus `text_offset`), and no capture could tell which image a
boot from reset ran, since every board image of one candidate has the
same size (fact: all sixteen `image_check` lines of the release
candidate 1 and M2 board records show `bytes=0x277000`, and M0's
`0x223000`).

### Open questions

Each has a default this plan applies if the responsible human does not
answer it. The human's answers of 2026-10-29 that this plan already
records are in [Base and inputs](#base-and-inputs).

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | The partition | **Label `beryllium`, ext4, 1 GiB, carved from p3** (the Fedora 44 root, btrfs label `fedora`, not mounted on the running Fedora 45; the human's choice, `use p3`) by the delivered tool, which the human runs with `sudo`, dry run first; the tool names the new partition's number (the first free GPT entry, 6 on the listing of 2026-10-29) and `be_part` takes it, checked at the prompt with `fsuuid` against Fedora's `blkid` | A larger partition; another source partition (the tool takes the source explicitly and refuses any identity mismatch, so this needs no plan change) |
| Q2 | The load address | **`0x1_4000_0000`**, written as a literal in `be_ld` and `be_go` (the board-information recipe's `kernel_addr_r`, B3's `loady` address); `booti` moves the image from there to `L` = `0x1_0800_0000` | `${kernel_addr_r}` by name, one more indirection through the BSP's environment |
| Q3 | Fall-through | **`bootcmd` runs the human's original boot command whenever the MVP image cannot be loaded** (`run be_boot; run be_orig_bootcmd`; `be_boot` is `nvme scan; if run be_ld; then run be_go; fi`), so a missing or unreadable image boots Fedora | A `be_enable` guard variable; one more thing to restore |
| Q4 | The checker's `kexec` mode | **Kept, test-only**, to re-judge the retained kexec captures of M0 to M2 and release candidate 1 that are the checker's fixtures; it launches nothing, and removing it would orphan those fixtures | Removed with its fixtures |
| Q5 | The run plan | **20 counted runs, the three probe images first**: the three M0 probe images (`probe-platform`, `probe-vmid-distinct`, `probe-vmid-shared`, GCC) once each from a cold boot; the three scenarios, three GCC and one Clang run each (12); the five board negatives once each with GCC (`payload`; `reader-write`, `no-inject`; `wrong-measurement`, `no-grant-check`). That is 14 image groups, 15 `saveenv`s (install, 13 selects, restore), and about 36 `k3ctl` resets (each select and each environment record needs a reset to a prompt), at about 1.5 min each | Fewer probes; the scenarios only |
| Q6 | What of the kexec code goes | **The loading and unloading code, `tests/kexec-rehearsal.sh` and `tests/kexec-rehearsal/`, the `k3-load-check`, `kexec-loader-check`, and `kexec-rehearsal` targets and wrapper commands, `tests/test-kexec-load.py`'s kexec cases, the dry run's kexec cases, `evidence.py`'s `kexec-loader` record and rehearsal section, and `rc-record`'s `kexec-rehearsal` gate.** `kexec-load.py`'s read-only `probe` and `region-check`, which the preflight, the platform record, and the fake board use, move to a non-kexec `tools/platform-probe.py`. The `KEXEC_*` layout constants and the scenarios' `kexec_fdt` object keep their names (renaming them changes the configuration identity: stop condition 6); the object becomes an unused reserved region under the new path and the guide says so. The retained records stay | Delete everything with "kexec" in its name, which changes the configuration identity and orphans the fixtures |
| Q7 | The claim's board clause and required limit | **The texts in [Documents and the claim](#documents-and-the-claim-m5-4)**, fixed by this plan's acceptance; checked against `claim.md`'s forbidden phrasings (none appears). "Unmodified" is not claimed of the firmware: no hash of the NOR exists, and the banners are the firmware's self-reports | Another wording the human supplies |
| Q8 | Environment records | **Committed:** the SHA-256 of each normalized `printenv` record, the `be_*` names and values, the human's `bootcmd` as its SHA-256, the set V of runtime-varying names, each comparison's verdict, and the capture excerpts from `Autoboot in` onward. **Private** (outside the repository and outside `build/`, mode 0600, and in picocom's own log): the full texts. The human reviews the first release candidate 2 board record before it is committed. The rewriter and `identifying()` gain MAC-address and `serial#` patterns as a backstop | A redacted copy of the environment in the record, which still shows the human's boot configuration |
| Q9 | The rehearsal's U-Boot | **B3's pinned upstream v2022.10 build** (`bringup/k3-b3/tests/build-uboot.sh`, `qemu-riscv64_smode_defconfig`, the release the BSP's U-Boot is based on), an external input like the guest kernel, never committed, its binary's SHA-256 recorded in the lock. A departure from the human's answer naming Fedora's `uboot-images-riscv64` package (fact: Fedora 44's x86_64 repositories carry `uboot-images-armv8` and `uboot-images-x86_64` only, checked 2026-10-29); the packaged image is the alternative only if it can be fetched from koji and locked by NEVRA and SHA-256 | The Fedora package from koji, if lockable |
| Q10 | Typing | **Fixed line templates** (the list in [Typing at U-Boot](#typing-at-u-boot-the-console-tool-m5-2)), each at most 60 characters, sent with `tmux send-keys -l --`, the echo compared with what was sent before Enter, Ctrl-C and one retry on a mismatch, then stop | A command allowlist with free arguments |
| Q11 | Probe images from reset | **Yes, once each, before the scenarios**: the probe facts in the platform record were made after a kexec, and a cold boot is a different initial state (HSM states, TLBs, clocks); the cold-boot values are recorded beside M0's, both labelled | Scenarios only |
| Q12 | Where the typing happens | **The operator's picocom tmux session** (`k3-console-1`), as B6's session did on direction; the tool checks the session, the pane's command, the log path, and that the log grows; it never sends `C-a`; the human does not type while automation runs | A second serial reader, which B3 found competes with picocom |
| Q13 | The model split | **The repository's:** this plan, the review of every document, and the packet on the orchestrating model; the tools, tests, and document drafts on `claude-opus-5.5` (`max`, `long_context`); the plan's steering review by `claude-opus-5.5` on the human's request | As the human directs |
| Q14 | Resets | **`k3ctl reset` (the opt-in of M1) or the human's, only**; U-Boot's `reset` and `boot` are never typed (fact: a Linux `reboot` on this board stopped at `reboot: Restarting system` until the operator pressed reset; U-Boot's `reset` may take the same path, and `boot` re-runs `bootcmd` from RAM and proves nothing about the saved environment); the dongle's port is opened only under the rule in [Resets and the dongle](#resets-and-the-dongle) | Human resets only, about 36 of them |
| Q15 | Human presence | **Required at the environment's install and restore and at any recovery**; the unattended runs between them need no one | Fully attended |
| Q16 | Release candidate 1 during M5 | **Stays accepted history**; no release step proceeds from release candidate 1 or 2 unless the human directs it; the ledger marks the kexec campaigns historical when `R2` is made | Withdraw release candidate 1 |

## Goal and pass criterion

**Goal.** MVP 1.0 exists as one exact commit, release candidate 2, whose
board evidence was made by boots from system reset: the board's resident
firmware and U-Boot, a boot command in U-Boot's saved environment, and the
MVP image loaded from a Beryllium partition on the board's NVMe, with the
environment recorded before and restored after, and with kexec gone from
the MVP line's tools and claim.

**Pass criterion.** All of:

1. `./mvp/mvp check` passes at `X2` from a clean checkout, with the
   `uboot` checker mode, the console, staging, environment, run, and
   campaign tools' dry-run cases, the partition tool's self-test, the
   QEMU-only image rule, and no kexec target.
2. `./mvp/mvp uboot-rehearsal` passes at `X2` for every scenario on both
   toolchains and for the missing-image fall-through case.
3. `./mvp/mvp evaluate`, `./be evaluate`, `make -C mvp kernel-repro`,
   and `./be model-check` pass at `X2` as they did at `X`; `rc-record`
   verifies.
4. The characterization (M5-6a) found no surprise: the relocation target
   is `L`, U-Boot's own memory use lies outside the MVP extents, the
   copy test is exact, and `probe-platform` boots from a typed
   `run be_ld` and `run be_go`.
5. The board session (M5-6) ran 20 of 20 counted runs as declared, each
   attributed to its image by the rule in
   [Run attribution and distinctness](#run-attribution-and-distinctness),
   and the restore rule held: the fresh-prompt `printenv` after the
   restore equalled the pre-session record except for the names in V,
   Fedora autobooted, and the preflight after equalled the preflight
   before.
6. The release surfaces carry the new board clause, pass the ledger and
   phrasing checks, and the ledger's rows for release candidate 2 cite
   the new records.
7. The soft limits of [Soft limits](#soft-limits) hold or were re-set by
   the human.
8. `R2` is one commit over `X2` holding the records, the ledger rows,
   and the evidence record, and nothing else; `./mvp/mvp check` passes
   at `R2`.

## Base and inputs

**Base.** The branch `beryllium/mvp-m5-plan` starts at `6a5f6fed`, the
tip of `beryllium/mvp-m4`: release candidate 1 (`c5df0cfa`), its
acceptance record, and the operator walkthrough. The development branch
`beryllium/single-hart-runtime-r0` is at `fb8accc9` (the M3 acceptance
and push record) locally and on the private `origin`; its fast-forward to
the M4 result needs its own instruction and is offered in the packet.
Implementation runs on `beryllium/mvp-m5` from this plan's acceptance
record. Line references are to `6a5f6fed`.

**The human's answers of 2026-10-29** (two question rounds, then the
instructions quoted in S3-A): the images live on a dedicated NVMe
partition, not an SD card; U-Boot's saved environment is changed during a
work session and restored at its end; a script we deliver creates the
partition and the human runs it; automation types at U-Boot through the
picocom session with every keystroke recorded; kexec is removed from the
board tools and the claim, and not used from here on unless truly needed
and approved; the structure is an MVP plan revision and a new milestone
with the MVP staged as release candidates; image selection is one
`saveenv` per image group followed by unattended resets; a U-Boot
rehearsal in QEMU replaces the kexec rehearsal; the source partition is
p3; the M5 code soft limit is 5,000 lines.

**Facts about the board** (the serial log `boot-7.log`; the wiki pages
`Fedora-45-Recipe`, `Console-and-Recovery`, `Hardware-and-Setup`; the
listing of 2026-10-29; B3's, B5's, B6's, and release candidate 1's
records):

- The boot chain is boot ROM (SD first, then NOR) → U-Boot SPL → OpenSBI
  (the BSP's; SBI implementation ID `0x1`, version `0x10006`; it prints
  no banner on this board) → U-Boot 2022.10 (`jenkins-BSP-build-bsp-deb-395`,
  non-UEFI; its console lines carry three-decimal `[ 246.129]` stamps)
  → `Loading Environment from mtdENV` (the QSPI NOR) → `load env_k3.txt
  from bootfs successful` (the UFS `sda2`) → `Autoboot in 3 seconds`,
  stopped only by `s` → `bootcmd`. The live boot is `booti` of Fedora's
  `Image-7.3.0-65.1…`, its initramfs, and the kernel package's
  `k3-com260-ifx.dtb` at `fdt_addr_r` from `nvme 0:4`, Fedora 45's
  `/boot`. GRUB is installed and not in the path.
- The saved environment is the human's: `env_k3.txt` names the BSP's
  Bianbu kernel, yet the board autoboots Fedora 45 (inference: the saved
  `bootcmd` is custom). Its text is readable only with `printenv` at the
  prompt (fact: Fedora has no `fw_printenv` and no `/proc/mtd`). The wiki
  says "never `saveenv`" for its temporary-boot recipes; S3-A's policy
  replaces that rule for Beryllium's sessions.
- The NVMe (`WD Red SN700 500GB`, 500,107,862,016 bytes, GPT, 512-byte
  sectors): p1 500 MiB vfat `EFI`; p2 2 GiB ext4 `BOOT` (Fedora 44
  `/boot`); p3 396.3 GiB btrfs `fedora` (Fedora 44 root; 13.87 GiB
  allocated, 7.68 GiB used; not mounted); p4 3 GiB ext4 `F45BOOT`
  (`/boot`); p5 64 GiB btrfs `fedora45` (`/`, `/var`, `/home`). No free
  space. p3 (sectors 5,122,048 to 836,263,935) and p4 (from 836,263,936)
  are contiguous, so shrinking p3 by 1 GiB frees sectors 834,166,784 to
  836,263,935, 1 MiB aligned, for GPT entry 6 between p3 and p4. The
  board has `sfdisk`, `partx`, `btrfs`, `mkfs.ext4`, `dumpe2fs`, and
  `e2fsck`, not `sgdisk` or `parted`; the `fedora` account has
  passwordless `sudo`. p4's ext4 feature set, which this U-Boot reads,
  is the reference for the new filesystem.
- The MVP shim is B3's `booti` wrapper: a RISC-V Image header whose
  `text_offset` is `0x6000000`; `booti` moves an in-RAM image to the
  RAM base plus `text_offset`, so on the board (RAM base
  `0x1_0200_0000`) it lands at `L` = `0x1_0800_0000`. All nine recorded
  U-Boot boots of this image family (B3 ×4, B5 ×4, B6 ×1) used `loady
  0x140000000 && booti 0x140000000 - ${fdtcontroladdr}`, entered the
  shim on hart 0, and received U-Boot's relocated control device tree
  (`Loading Device Tree to 00000002fbd6b000`), not a kernel DTB. The
  monitor never parses the device tree; the shim records `a1`.
- In QEMU (RAM base `0x8000_0000`) the same header puts the image at
  `0x8600_0000` (review). `mvp/src/mvp-layout.h` L141-L142 already
  defines `BE_MVP_QEMU_TEXT_OFFSET` as `0x88000000` and asserts that
  QEMU's base plus it is `L`; nothing builds such an image. The direct
  QEMU runs are unaffected: they boot the ELF with `-kernel`.
- Every board image of one candidate has the same size (fact above), and
  the SHIM line's `bytes=0xa4000` is the flat image's fixed size, so a
  capture cannot tell images, or toolchains, apart by size; release
  candidate 1 attributed each run by `remote_image_sha256` taken on
  Fedora. U-Boot's `crc32` command exists in this build (B3's `help`
  record).
- U-Boot's own memory use at boot is near `0x2_f8xx_xxxx` (ramdisk and
  device tree) and the bootlogo framebuffer high in RAM, outside the MVP
  extents `0x1_0200_0000` to `0x1_1800_3000`; `0x1_4000_0000` is above
  them too. The preflight's `/proc/iomem` is Fedora's view; U-Boot's own
  (`bdinfo`, the control device tree's `/reserved-memory`) is read at the
  prompt in M5-6a. U-Boot leaves the display scan-out running and may
  leave the NVMe controller enabled; the watchdog was observed stopped
  (B3: no reset in 80 s after `Starting kernel ...`; B5: 4 of 4 runs).
- Multi-hart start from a U-Boot boot has never run on this board.
  Fedora starts harts 1 to 7 through HSM at every boot (M0's preflight:
  `online_cpus=0-7`), which lowers the HSM risk; the new test is harts 1
  and 2 entering with S/VS/H CSRs that Linux never initialized, clean
  TLBs (the VMID facts may differ), clocks as U-Boot left them (the
  timing counters), and a small `time` value. PMP is the same on both
  paths; the shim clears `SIE`; U-Boot never enables S-mode interrupts.
- A Linux `reboot` on this board stopped at `reboot: Restarting system`
  until the operator pressed reset (the recipe); the dongle's `k3ctl
  reset` worked at every one of release candidate 1's 11 runs and M1's,
  M2's, and M0's campaigns before it.
- The board-information wiki records that long chained lines typed at
  this U-Boot were truncated and that input sent while a command ran was
  lost; B6's session's first `send-keys` attempt misfired before the
  recorded run (B6 results README).

**Inputs it reuses unchanged:** the accepted B3 shim contract and
`booti` procedure; B3's `tests/run-qemu-uboot.py` (a PTY driver that
types at a real U-Boot in QEMU) and `tests/build-uboot.sh` as the
patterns for the rehearsal; B6's recorded tmux typing as the pattern for
the console tool; M1's "The remote reset" for `k3ctl`, narrowed by Q14;
M4's release surfaces, ledger, `rc-record`, and campaign form; the
pinned evaluators.

## Design

### The boot path of release candidate 2

```text
reset → ROM → SPL → OpenSBI (NOR, resident) → U-Boot (NOR) → saved env
  bootcmd         = run be_boot; run be_orig_bootcmd
  be_boot         = nvme scan; if run be_ld; then run be_go; fi
  be_ld           = load nvme 0:${be_part} 0x140000000 /${be_image} && crc32 0x140000000 ${filesize}
  be_go           = booti 0x140000000 - ${fdtcontroladdr}
  be_part         = <the beryllium partition's number>
  be_image        = <the image group's file name>
  be_orig_bootcmd = <the human's bootcmd, byte for byte>
→ booti moves the image to L → B3 shim → MVP (hart 0; HSM starts 1 and 2)
→ … → SBI SRST shutdown (the board halts) → the next k3ctl reset = the next run
```

- Short variables with literal addresses keep every typed line under 60
  characters. `crc32` prints the loaded image's CRC-32, the run's witness
  of which image booted. `if run be_ld; then …; fi` is the pattern
  U-Boot's own distro boot uses; a second `nvme scan` on a probed device
  is a no-op.
- Fail-safe: a missing or unloadable image, or a `booti` that fails
  before `Starting kernel ...`, returns to `bootcmd`, which runs the
  human's boot command. A `booti` that hangs, or an MVP that hangs,
  repeats at every reset and is recovered at the prompt with `s`.
- Restore: `setenv bootcmd "${be_orig_bootcmd}"`, then `setenv be_boot`,
  `setenv be_ld`, `setenv be_go`, `setenv be_part`, `setenv be_image`,
  `setenv be_orig_bootcmd` (a bare `setenv NAME` deletes a variable in
  every U-Boot; `env delete` is not relied on), the pre-save `printenv`
  check, `saveenv`, then the fresh-prompt comparison and one autoboot
  into Fedora.
- Never written: SPL, OpenSBI, U-Boot, the environment partition outside
  the session's install, select, and restore `saveenv`s, any partition but
  `beryllium`, `env_k3.txt`, the UFS. Never typed: `env default`,
  `env erase`, `sf` or `mtd` writes, any `*write`, network commands,
  `mw`, `cp`, `go`, `fastboot`, `ums`, `reset`, `boot`.
- Never used: kexec, anywhere (S3-A policy item 2). The loader's loading
  code and the kexec rehearsal are removed; the wrapper has no kexec
  command.

### Typing at U-Boot: the console tool (M5-2)

`tools/k3-console.sh` is the only path from automation to the U-Boot
prompt.

- It drives the operator's picocom tmux session (`k3-console-1`, Q12):
  it checks that the session exists, that the pane's command is picocom,
  that picocom's log file is the configured serial log, and that the log
  grows; it never sends `C-a`; the human does not type while it runs.
- **Templates, not a command allowlist.** It types only these forms, the
  named parameters filled from its configuration and checked against a
  fixed pattern each: `s` (at `Autoboot in`); `printenv`;
  `printenv <be_name>`; `setenv be_orig_bootcmd "${bootcmd}"`;
  `setenv be_part <n>`; `setenv be_image <file>`; `setenv be_ld '<the
  fixed text>'`; `setenv be_go '<the fixed text>'`; `setenv be_boot
  '<the fixed text>'`; `setenv bootcmd 'run be_boot; run be_orig_bootcmd'`;
  `setenv bootcmd "${be_orig_bootcmd}"`; `setenv <be_name>`; `saveenv`;
  and the characterization set `version`, `help`, `env info`, `bdinfo`,
  `nvme scan`, `fsuuid nvme 0:<n>`, `ls nvme 0:<n> /`, `fdt addr
  ${fdtcontroladdr}`, `fdt print /reserved-memory`, `setenv be_t
  "${bootcmd}"`, `printenv be_t`, `run be_ld`, `run be_go`. Any other
  line is refused (stop condition 5).
- Each line is at most 60 characters, sent with `tmux send-keys -l --`
  and paced; before Enter the tool reads the echo from the log, strips
  the BSP stamps, and compares it with what it sent; on a mismatch it
  sends Ctrl-C, retries once, then stops (stop condition 12). Every
  keystroke, every prompt, and every command's output are logged with
  timestamps into the campaign record.
- Install, each select, and the restore happen only at a **fresh
  prompt** (a reset, `s`, and nothing else before), so that `filesize`,
  `fileaddr`, and other session variables are never saved. Before every
  `saveenv` the tool runs `printenv` and requires the difference from
  the pre-session record to be exactly the declared `be_*` lines and the
  new `bootcmd` (install), exactly `be_image` (select), or nothing but
  the names in V (restore).
- U-Boot's hush re-parses a command containing a substitution and
  re-quotes its arguments, so a `bootcmd` containing `'`, a newline, or
  a non-printable byte would be corrupted by the install copy and again
  by the restore copy: the tool stops if the recorded `bootcmd` holds
  any (stop condition 3). The characterization's copy test (`setenv be_t
  "${bootcmd}"; printenv be_t`, in RAM only) proves the copy exact
  before the first `saveenv`.

### Resets and the dongle

- Every reset is a `k3ctl reset` (M1's opt-in, `K3_RESET=k3ctl`, the
  pinned client) or the human's (Q14).
- Opening the dongle's port can cause transients on its lines (M1 plan),
  and a transient during a `saveenv` could interrupt a NOR write. The
  port is opened only when one of these holds: a run ended with a
  terminal marker and its tail wait is over; the console tool reports an
  idle prompt after a completed command, never during `saveenv`; Fedora
  is cleanly down.
- Before a session's first reset, after staging and the preflight,
  Fedora is shut down cleanly over `ssh` (`systemctl poweroff`; the
  board halts and the next `k3ctl reset` boots it).
- After a run's timeout, the tool resets only if the capture shows
  `Starting kernel ...` and no later U-Boot or Fedora line (an MVP hang);
  otherwise it stops. Every SPL and U-Boot banner in the session must
  map to a recorded reset; a banner no reset explains (a watchdog, a
  glitch) is stop condition 12. A missed `s` leads to an unplanned boot:
  the tool records it, does not count it, retries once, then stops.
- "A new boot" is a new SPL/U-Boot banner within a bounded time of the
  reset reply, replacing M1's Fedora boot-ID rule.

### The restore rule

1. Each environment record is taken at a fresh prompt: a reset, `s`,
   then `printenv` as the first command.
2. Normalize: strip carriage returns and a leading `[ nnn.nnn] ` stamp;
   keep the lines after the echoed command up to and including
   `Environment size: N/M bytes` (U-Boot prints the variables sorted).
3. Take **two** pre-session records from consecutive resets; V is the set
   of names whose values differ between them (the BSP's runtime values).
   V is expected empty; if not, the names are recorded and the tool
   stops unless the human accepts them (stop condition 2).
4. The install `printenv`, before its `saveenv`, must equal record 1
   plus exactly the declared `be_*` lines and the new `bootcmd`;
   `be_orig_bootcmd` must equal record 1's `bootcmd` byte for byte; at
   the restore, `bootcmd` must equal `be_orig_bootcmd`.
5. The post-restore fresh-prompt record must equal record 1 byte for byte
   except for the names in V.

The claim says only that the environment U-Boot printed at a fresh prompt
after the restore equalled the pre-session record; the stored NOR bytes
are not compared (a redundant environment's flag byte changes on every
save), and the required limit says so. Preconditions recorded before the
install, each a stop if violated: no `bootcount`, `upgrade_available`,
`altbootcmd`, or `bootlimit`; no `preboot` that boots; `bootdelay` > 0;
`env_k3.txt`, read read-only from Fedora with its SHA-256 recorded, sets
neither `bootcmd` nor any `be_*` name; the human confirms that the
recorded `bootcmd` is their normal default with no pending one-shot
boot, and that their other project stays off the board from the install
to the restore.

### Recovery

The human is present for the install, the restore, and any recovery
(Q15).

- An MVP hang: `k3ctl reset` under the rule above. A bad image: it falls
  through to Fedora; stop; clean shutdown; recovery at the prompt.
- A corrupted environment (U-Boot reports a bad CRC and uses its built-in
  default, which probably boots Bianbu from the UFS): at the prompt,
  re-set from the private record the variables that differ, one short
  line each, `saveenv`, fresh-prompt check. Never `env default`.
- The full `printenv` texts live outside the repository and outside
  `build/` (`~/.local/state/beryllium/k3-env/`, mode 0600) and in
  picocom's log.

### Run attribution and distinctness

A run belongs to image I only if all hold: the last select record names
`be_image` = I; the staged SHA-256 of I equals the build's `images.sha256`
entry; the capture's `N bytes read` shows I's size; the printed
`crc32 … ==> C` equals I's CRC-32 (staging records the 14 CRCs and
requires them pairwise distinct); and the capture passes I's expectation.
Each run's capture is the byte range of the serial log from just before
its launching reset; the ranges are disjoint and increasing; each holds
one SPL banner, one U-Boot banner (its stamps restarting near zero), one
`Starting kernel ...`, and one terminal marker, with the reset reply
before the first boot line.

### The session protocol (M5-6)

The order, with who acts:

| Step | Who | What |
| --- | --- | --- |
| a | human | Creates the partition with the delivered tool (dry run, then `--apply`), on a day the board is theirs; sends the tool's summary (the partition number) |
| b | automation | M5-2 and M5-3 complete; `./mvp/mvp check` and `uboot-rehearsal` pass |
| c | both | **Characterization (M5-6a)**, attended, below; no `saveenv` |
| d | automation | `X2` fixed; the clean gates run (M5-5) |
| e | automation | Preflight before (Fedora, read-only): kernel, firmware identity, the partition present, ext4, labelled, its `fsuuid`, `env_k3.txt`'s hash and content check, the platform probe |
| f | automation | Staging: mount the partition by label, copy the 14 images, `SHA256SUMS`, and the CRC list, `sync`, unmount, re-hash after a fresh read-only mount, unmount |
| g | automation | Clean shutdown of Fedora over `ssh` |
| h | automation | Two environment records (reset, `s`, `printenv`; twice) |
| i | both | Install (human present): `be_orig_bootcmd`, `be_part`, `be_image` (the first group's), `be_ld`, `be_go`, `be_boot`, `bootcmd`; the pre-save `printenv` check; `saveenv` |
| j | automation | The runs: the three probes, then the scenarios, then the negatives; each group's select at a fresh prompt (`setenv be_image <next>`, `printenv be_image`, `saveenv`), then N `k3ctl` resets, each run judged in `uboot` mode and recorded with `launcher=uboot-autoboot-nvme` |
| k | both | Restore (human present), as above |
| l | automation | The fresh-prompt comparison |
| m | automation | Fedora autoboots; `ssh` answers; preflight after equals preflight before |
| n | automation | `board-evidence` → `mvp/results/<date>-com260-rc2/`; the human reviews the first record before it is committed (Q8) |

**M5-6a, the characterization** (after this plan's acceptance and step
a, before `X2`; recorded in the result packet, not counted as a campaign
run): at a fresh prompt, `version`, `help`, `env info`, `bdinfo` (the
relocation address, the framebuffer, the LMB regions), `nvme scan`,
`fsuuid nvme 0:<p>` against Fedora's `blkid`, `ls nvme 0:<p> /`,
`fdt addr ${fdtcontroladdr}` and `fdt print /reserved-memory` (checked
against the MVP extents), `printenv` at two fresh boots (V), the copy
test, then `setenv be_part`, `setenv be_image probe-platform…`,
`setenv be_ld '…'`, `setenv be_go '…'` in RAM only, `run be_ld`, and
`run be_go`: one typed boot of `probe-platform` from the partition,
judged in `uboot` mode. The `Moving Image from 0x140000000 to
0x108000000` line must appear. Any surprise is stop condition 4.

### Tool changes (M5-2), all under `mvp/`

- `tests/check-capture.py --mode uboot`: the capture holds, once each
  and in order, `N bytes read` (N the image's size), `crc32 … ==> C`,
  `Moving Image from 0x140000000 to 0x108000000, end=…`, `## Flattened
  Device Tree blob at A`, `Booting using the fdt blob at 0xA`, `Loading
  Device Tree to F, end E ... OK` (the board) or `Using Device Tree in
  place at F, end E` (QEMU), and `Starting kernel ...`; the shim's `fdt`
  equals F and `[F, E)` lies outside every MVP extent; exactly one SPL
  and one U-Boot banner; the BSP's lines (`fail to get alias node
  efuse_power`, `Removing MTD device #0 (nor0)…`, three-decimal stamps)
  are allowed; the boot hart by launcher as today (board: hart 0, else
  stop condition 6; QEMU: any non-domain hart, a domain hart `REFUSED`
  and the run repeated); no `kexec_fdt` expectation. The expectation
  JSON needs no change (the SHIM pattern accepts any `fdt=`);
  `--write-fixtures` builds the `uboot` fixtures from B6's recorded board
  output and the characterization capture. `--mode kexec` stays
  test-only for the retained records (Q4).
- `tools/k3-console.sh` (new): the template-driven tmux interaction
  above.
- `tools/k3-run.sh` becomes a reset launch: `k3ctl reset` or the
  human's; follow the serial log from the reset to the terminal marker;
  judge; record. The kexec steps (`scp`, the loader, `systemctl kexec`,
  the load check) go. `tools/k3-campaign.sh`: the group loop (select,
  `saveenv`, N runs).
- `tools/k3-stage.sh` (new): stage the images and the CRC list over
  `ssh` and verify. `tools/k3-env.sh` (new): record, install, select,
  and restore through the console tool; the normalization and the
  comparison; the private store.
- `tools/k3-preflight.sh`: the partition checks, the `env_k3.txt` check,
  the read-only platform probe; the kexec facts dropped.
- `tools/platform-probe.py` (new, from `kexec-load.py`'s `probe` and
  `region-check`), used by the preflight, `platform-record.py`, and the
  fake board; the loading and unloading code, `tests/test-kexec-load.py`'s
  kexec cases, `tests/kexec-rehearsal.sh`, `tests/kexec-rehearsal/`, the
  `k3-load-check`, `kexec-loader-check`, and `kexec-rehearsal` targets,
  `evidence.py`'s `kexec-loader` record and rehearsal section,
  `rc-record.py`'s `kexec-rehearsal` gate (→ `uboot-rehearsal`), the
  dry run's kexec cases, `make-control.py`'s kexec entries, and the
  wrapper's kexec commands are removed or replaced (Q6). The `KEXEC_*`
  constants and the scenarios' `kexec_fdt` object keep their names.
- `tools/evidence.py --board`: the new launcher, the environment verdict
  records, the keystroke log, capture excerpts from `Autoboot in`, and
  MAC-address and `serial#` patterns in the rewriter and `identifying()`.
  `tools/platform-record.py`: the boot hart from the shim line, the
  preflight pair, the cold-boot probe values beside M0's.
- `tests/run-tool-dry-run.sh`, `tests/fake-board.py`, a new fake U-Boot
  (a scripted pty standing in for tmux and picocom, with the BSP's
  stamps and noise), and `tests/fake-k3ctl.py`: cases for the install,
  select, and restore sequence, a template refusal, an echo mismatch, a
  `printenv` mismatch after the restore, a run from reset, a missed `s`,
  and an unexplained banner.
- `tools/make-control.py`, `tools.mk`, `Makefile`, `mvp`, `rc-record.py`:
  the new commands and gates; `tools/claim-ledger.py`: MAC and serial
  privacy patterns. The lock: `ssh` and `scp` stay (staging, the
  preflight); `tmux` is a host-only role; the rehearsal's U-Boot binary,
  `mke2fs`, and `sfdisk` for the rehearsal disk are added; the kexec
  rehearsal kernel's inputs go. These are the enumerated lock roles stop
  condition 6 refers to.
- **QEMU-only images** for the rehearsal: a Makefile rule emits, for each
  scenario image, a copy that differs only in header bytes 8 to 15
  (`text_offset` = `BE_MVP_QEMU_TEXT_OFFSET`); `tests/check-image.py`
  requires byte-equality outside those bytes. No source changes.
- The partition tool, `tools/k3-make-partition.sh`, and its self-test
  are delivered with this plan ([The partition tool](#the-partition-tool-m5-1));
  M5-2 adds the self-test to `check`.

### The U-Boot rehearsal in QEMU (M5-3)

`tests/uboot-rehearsal.sh` with a PTY driver after B3's
`run-qemu-uboot.py`: QEMU `virt` with the k3-like machine (8 harts, AIA;
`aia=none` only as a declared fallback, stop condition 13), OpenSBI
`fw_dynamic` as `-bios`, U-Boot as `-kernel`, and a raw disk with one
ext4 partition holding the QEMU-only images. The driver stops the
autoboot and **types the session's exact `be_*` lines and `bootcmd`**
(in RAM; `saveenv` is impossible in QEMU and the rehearsal says so), then
`boot`; the capture is judged in `uboot` mode, with `Moving Image from …
to 0x108000000` required. A missing-image case must fall through to a
stand-in original `bootcmd`. The rehearsal exercises the hush text, the
ext4 load from a partition, `booti`'s relocation, and a boot from a
U-Boot environment; it does not exercise the BSP's saved-environment
storage, which only the board does. The U-Boot is B3's pinned upstream
v2022.10 build (Q9), an external input: `bringup/k3-b3/tests/build-uboot.sh`
builds it from a pinned shallow clone, and the lock records the binary's
SHA-256.

### The partition tool (M5-1)

`mvp/tools/k3-make-partition.sh`, delivered with this plan as its own
commit for the human's review, is a human-run maintenance tool: the
human runs it with `sudo` on the board, dry run first, then `--apply`.
It is not a campaign tool and no automation runs it.

- Dry run by default; `--apply` performs the change.
- **No default source**: the human names the partition to shrink by its
  `/dev/disk/by-id/` path and its filesystem UUID and label, and for
  `--apply` also the disk's model, serial, and size and an
  acknowledgement string that names the partition and the size; any
  mismatch is a refusal, and every failed precondition is listed before
  it exits.
- Preconditions: GPT and 512-byte sectors; the source is btrfs, not
  mounted, with no holder; the freed space is 1 MiB aligned; the
  filesystem's used bytes plus a 1 GiB margin fit the shrunken size; no
  filesystem or partition already carries the label; the first free GPT
  entry is reported; the reference partition (p4) is ext4; for
  `--apply`, the backup directory is writable and not on the source.
- Order: backups (`sfdisk --dump`, the primary and backup GPT sectors by
  `dd`, `blkid`, `lsblk`, the reference's feature list) into the
  human's backup directory; `btrfs check --readonly`; the filesystem
  shrunk first (`btrfs filesystem resize` on a temporary `subvolid=5`
  mount, by the new size plus a 64 MiB margin); then the partition with
  `sfdisk --no-reread --no-tell-kernel` (the source's size, then the new
  entry with explicit start, size, type, and name) and `partx -u`/`-a`,
  never `partprobe` on the busy disk; the kernel's view verified before
  `mkfs.ext4 -L beryllium` with p4's feature set (`dumpe2fs -h`); after,
  `btrfs check --readonly`, `blkid` and `lsblk` again, and the
  untouched partitions' `blkid` lines byte-identical.
- No automatic rollback of a partition-table write: on a failure it
  prints the state, the backup paths, and the restore command.
- Its host self-test (`mvp/tests/test-k3-make-partition.sh`) runs the
  tool against fake block tools and a synthetic fixture modelled on the
  listing of 2026-10-29 (a dry run, six refusals, the apply sequence
  against a golden command list, a feature mismatch, a mid-apply
  failure, and the non-root refusal); it needs no root and no device.
  Its dry run on the board is the human's first command.

### Documents and the claim (M5-4)

- `mvp/docs/claim.md`, the board clause, fixed by this plan's acceptance:
  "booted from system reset by the board's installed firmware and
  U-Boot, which loaded the MVP image from a Beryllium partition on the
  board's NVMe under a boot command installed in U-Boot's saved
  environment for the campaign and restored after it" replaces "RAM-only
  load through Linux kexec from the board's Fedora host". The required
  limit's "one host kernel" becomes "one U-Boot build as its banner
  reports it", and it gains: "The board's installed firmware and
  U-Boot, identified by their banners and SBI identity, were the same
  before, during, and after the campaign; no campaign step wrote them.
  U-Boot's saved environment, data in the same NOR, was changed for the
  campaign and restored: the environment U-Boot printed at a fresh
  prompt after the restore equalled the pre-session record, normalized
  as the M5 plan states; the stored bytes were not compared." The
  closing sentence stays verbatim. None of the forbidden phrasings
  appears in the new text (checked against the list at `6a5f6fed`).
- The guide's §4 is rewritten for the boot from reset, the session
  protocol, and what the human does; §2, §7, and §8 adjusted; the
  walkthrough's board section rewritten; the disclosure states that
  automation typed at U-Boot and ran `saveenv` on direction with the
  human present at the install and the restore; the ledger: C-10
  replaced by a U-Boot loader row, C-24 to C-26 and C-29 to C-34 marked
  historical, the `release` block moved to `X2`, rows for release
  candidate 2's records; `mvp/README.md`; the planning status pages.
- The `.github/copilot-instructions.md` "Board safety for B0 runs" lines
  and the kexec commands it lists are revised to the board policy and the
  standing rule when this plan is accepted (M5-1 edits the instructions
  file only for the standing rule now, which the human has already set).

### What M5 does not do

No monitor, shim, guest, scenario, generator, expectation, or `model/`
change. No kexec, anywhere. No write to SPL, OpenSBI, U-Boot, the
environment partition outside the recorded session, any other partition,
`env_k3.txt`, or the UFS. No `env default`, `env erase`, flash, MTD, or
firmware command. No U-Boot `reset` or `boot`. No second serial reader.
No SD card. No board command before the human's confirmation that the
board is free, and none of M5-6 before the partition exists. No release
step, tag, push, or merge. No re-run of release candidate 1's campaigns.
No security model or `model/` revision.

## Soft limits

Limits are for re-evaluation (M3's rule): exceeding one is stop condition
8, a return to the human to re-set the limit, never a reason to drop a
check, a record, or a claim row.

| Item | Soft limit | Counting rule |
| --- | --- | --- |
| New code | **5,000 lines for M5** (the human's figure, 2026-10-29) | Added lines by `git diff --numstat` from this plan's acceptance record to `X2`, in Python, shell, Make, and the wrapper, tests and fakes included; fixtures, generated JSON and Markdown, and documents excluded. The partition tool and its self-test, delivered with this plan, are counted and reported separately: 1,219 and 361 lines, with 571 lines of fake block tools, 14 eight-line wrappers, and a 126-line fixture under `tests/fake-partition-tools/`. The count is reported after M5-2 |
| Board time | About one hour of resets per campaign attempt | 36 resets at about 1.5 min |
| New gate wall time | `uboot-rehearsal` under about 10 min on `l1`; the dry-run cases and the self-test under about 2 min together | Measured directly, three runs |
| Monitor, guest, scenario, `model/` lines | 0 | By construction |

Review estimate of the new code: the checker mode with its fixtures 250
to 350, the console tool 250 to 350, the run and campaign tools about
300, the staging and environment tools 300 to 400, the evidence and
platform record 250 to 350, the fake U-Boot and dry-run cases 400 to
600, the rehearsal with the QEMU-image rule 200 to 300, `rc-record`, the
wrapper, and Make about 150: 2,300 to 3,300, inside the limit.

## Tests and evidence

| Layer | What | Where |
| --- | --- | --- |
| Host | The partition tool's self-test; the checker's `uboot` self-test on the B6 and characterization fixtures; the dry-run cases on the fake U-Boot and fake `k3ctl`; the QEMU-image byte-equality check | `./mvp/mvp check` |
| Emulation | The U-Boot rehearsal, all scenarios, both toolchains, and the fall-through case | `./mvp/mvp uboot-rehearsal` |
| Board | The characterization capture; 20 counted runs with their keystroke logs, environment verdicts, and attribution; the preflight pair; the platform record with the cold-boot probe values | `mvp/results/<date>-com260-rc2/` |
| Clean gates | `check`, `evaluate`, `uboot-rehearsal`, `kernel-repro`, `./be evaluate`, `./be model-check`, `rc-record` at `X2` from a clean checkout | `mvp/results/<date>-rc2/` |
| Mutation | The `uboot` mode's self-test rejects captures missing each required line, a wrong CRC, a wrong relocation address, a device tree inside an MVP extent, a second banner, and a domain boot hart | `check-capture.py --self-test` |

## Accepted decisions M5 departs from

| # | Accepted decision or recorded guidance | Departure | Accounted for by |
| --- | --- | --- | --- |
| 1 | The B-series board safety boundary and every plan's "RAM-only, no `saveenv`, no U-Boot environment change, human resets" lines, M0's "Board safety and procedure", M4's Q8 | Boot from reset; `saveenv` within a recorded session; `k3ctl` resets | S3-A's board policy; the human's direction of 2026-10-29 |
| 2 | The MVP plan's harness "Run" row: "automation never types at U-Boot" | Templated, recorded typing by automation | S3-A; B6's precedent on direction; Q10, Q12 |
| 3 | M1's "The remote reset" preconditions (Linux's handoff, Fedora boot IDs) | Reset preconditions restated for a boot from reset | [Resets and the dongle](#resets-and-the-dongle); Q14 |
| 4 | M4's Q6: the claim's wording is fixed; "a later change is a plan revision" | The board clause and the required limit change | This plan is that revision, with S3-A; Q7 |
| 5 | The human's answer naming Fedora's `uboot-images-riscv64` for the rehearsal | B3's pinned upstream build | Q9: the package is not in the x86_64 repositories |
| 6 | M4's Q2: the probe images are not re-run | The three probes run once from a cold boot | Q11: a cold boot is a different initial state |

## Risks

| Risk | Response |
| --- | --- |
| A `saveenv` interrupted by a reset or a port transient corrupts the environment and the board boots the BSP's default | The port-open rule; the human present; recovery from the private record one line at a time; never `env default` |
| The saved `bootcmd` cannot be copied exactly by hush | The copy test before the first `saveenv`; stop condition 3 |
| Harts 1 and 2 do not start, or start differently, from a cold boot | The probes first; a finding under stop condition 4, never a loosening |
| The MVP image hangs before SRST and every reset repeats it | The reset rule; recovery with `s`; the image never becomes the default because `bootcmd` falls through only on a load failure, so the human is present at the install and the first boot |
| The partition tool damages the boot disk | Dry run first; no default source; identity checks; backups and the restore command; the filesystem shrunk before the partition; no rollback automation; the self-test against the real geometry |
| The rehearsal's U-Boot cannot be pinned or does not boot the 8-hart machine | Stop condition 13; `aia=none` declared, never silent |
| A run is attributed to the wrong image | The attribution rule's five conditions, the CRC among them |
| The environment record exposes the human's configuration | Q8: hashes and verdicts in the repository, full texts private; the human reviews the first record |
| The other project's one-shot boots collide with the session | The human's confirmation before the install; the `be_` prefix; the restore returns `bootcmd` byte for byte |
| The code limit is reached while the kexec code is still being disentangled | Stop condition 8 as a checkpoint after M5-2 |

## Claim boundary and non-goals

Release candidate 2's board evidence is diagnostic bring-up evidence for
one board, one reported SBI identity and version, and one U-Boot build as
its banner reports it, made by boots from system reset. It does not show
that the NOR firmware is unmodified (no hash of it exists), that the
stored environment bytes were restored (only the printed environment is
compared), that a boot from reset works on another board or firmware, or
anything about the harts never started. The U-Boot rehearsal in QEMU is
emulation evidence of the hush text, the ext4 load, and the relocation,
not of the BSP's environment storage. Nothing here is formal
verification, hardware validation, or certification; the forbidden
phrasings stand.

## Work packages

| WP | Delivers | Exit |
| --- | --- | --- |
| M5-1 | Plan revision S3-A; this plan; the partition tool with its self-test (its own commit); the standing rule in `.github/copilot-instructions.md` and `planning/HANDOFF.md`; the packet | S3-A and this plan accepted; the tool delivered |
| M5-2 | The tool changes above, the kexec removal, the QEMU-only image rule, the dry-run cases, the self-test in `check`; the line count reported | `./mvp/mvp check` PASS |
| M5-3 | The U-Boot rehearsal, its driver, the lock roles | PASS on both toolchains, all scenarios, and the fall-through case |
| M5-4 | The claim, guide, disclosure, ledger, README, walkthrough | ledger and phrasing checks PASS |
| M5-6a | The characterization on the board, attended, after the human's partition and a free board | No surprise; the copy test exact; `probe-platform` boots from a typed `run be_ld` and `run be_go` |
| M5-5 | `X2` fixed; the clean gates; `rc-record` | The records verify |
| M5-6 | The board session: staging, records, install, 20 runs, restore, verification, board evidence | 20 of 20 as declared; the restore rule satisfied |
| M5-7 | The evidence record; the ledger rows; `R2` over `X2`; `check` at `R2`; the packet | The packet presented |

## Stop conditions

Each returns M5 to the responsible human.

1. The ROM, SPL, or U-Boot does not reach the prompt after a reset.
2. An install or restore `printenv` check fails; V is not empty and not
   accepted; Fedora does not autoboot after the restore; U-Boot reports a
   bad environment CRC.
3. The recorded `bootcmd` holds `'`, a newline, or a non-printable byte;
   a precondition variable is present; `env_k3.txt` sets `bootcmd` or a
   `be_*` name; `saveenv`, `load`, or `crc32` reports an error; the
   partition is missing, not ext4, unlabelled, or its `fsuuid` differs
   from `blkid`'s.
4. A verdict other than declared; a count M4 compared that differs from
   release candidate 1's and is not explained by the captures; an HSM
   start failure; a characterization surprise (the relocation target not
   `L`, a `/reserved-memory` or `bdinfo` region inside the MVP extents,
   the copy test inexact).
5. The console tool needs a line outside its templates.
6. Any need to change a monitor source, the shim, a guest input, a
   scenario, the generator, an expectation, the checker's rules beyond
   the new mode, the lock beyond the enumerated roles, the `KEXEC_*` or
   `kexec_fdt` names, or `model/`.
7. A claim clause the records cannot support as written.
8. A soft limit exceeded (the code count is checked after M5-2).
9. The board unavailable or in the other project's use: wait; no board
   command before the human's confirmation.
10. Any push, merge, tag, publication, or release step.
11. Any need for kexec: stated to the human; nothing proceeds without
    their approval (S3-A policy item 2).
12. An unexplained SPL or U-Boot banner; an echo mismatch after the
    retry; a second missed `s`.
13. The rehearsal's U-Boot cannot be pinned, or the 8-hart k3-like
    machine does not boot it.

## How M5 feeds the release path

Release candidate 2's acceptance satisfies the release path's step 1 as
S3-A restates it ("the latest release candidate's exact commit is
accepted"). It starts no later step: the selection of material, the
public repository, the public commit and tag, the publication, and the
archive each need their own instruction, as the MVP plan says. Release
candidate 1 stays accepted history.

## Status record

```text
m5_status=accepted
m5_plan_target=0066794dbec22807d46cc274f2ad00fb79b555ae
m5_plan_parent=0d134bbc49377576b961989831a02c068b479355
m5_acceptance_instruction=accept-0d134bbc-and-066794d-authorize-m5-read-as-0066794d
m5_acceptance_date=2026-10-29
m5_acceptance_record=mvp-m5-plan-review-summary.md
m5_first_cut=3d38dafd-rewritten-before-presentation-never-presented
m5_plan_branch=beryllium/mvp-m5-plan
m5_plan_base=6a5f6fed1bc57605c116ca5ba6c631d8b7e67671
m5_revision_s3a=directed-not-accepted
m5_direction_date=2026-10-29
m5_direction=modify-the-plan-so-that-the-mvp-candidate-boots-from-system-reset
m5_standing_rule=no-more-kexec-unless-approved
m5_mechanism=nvme-partition-beryllium-ext4-1gib-from-p3
m5_env=be_-prefixed-saved-env-installed-and-restored-per-session
m5_typing=templated-recorded-tmux-picocom
m5_resets=k3ctl-or-human
m5_kexec=removed-from-mvp-tools-and-claim
m5_checker_kexec_mode=kept-test-only
m5_rehearsal=uboot-qemu-b3-pinned-v2022.10
m5_run_plan=3-probes,12-scenario-runs,5-negatives
m5_image_groups=14
m5_saveenvs=15
m5_resets_estimate=36
m5_soft_limit_lines=5000
m5_open_questions=Q1-Q16-defaults
m5_steering_review=claude-opus-5.5-2026-10-29-ready-with-corrections
m5_authorization=M5-2..M5-7-and-M5-6a-on-beryllium/mvp-m5-from-acceptance-record;2026-10-29;board-steps-after-partition-and-human-confirmation
m5_partition_tool=952f9e0c-delivered;apply-on-board-is-the-humans-act
rc1=c5df0cfa-accepted-history
rc2=m5-result
m5_errata=1-code-limit-10000-after-stop-8-at-6865-2026-10-29
m5_result=accepted-3867c66c5df2108e1051d8f8c44c12d62611e485;parent-X2-6dd81ee39dd620a1815605c50c9c916894c9974c;2026-10-30;instruction-accept-3867c66c;record-mvp-m5-result-review-summary.md;evidence-mvp-m5-evidence.md
m5_departures=11
m5_stops_fired=8,12
m5_code_lines=7439-of-10000
m5_release_path=step-1-holds-for-rc2;steps-2-7-not-started-each-needs-instruction
```
