<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M5 plan review and acceptance record

This packet presents two ordered decisions for the responsible human:
[Plan revision S3-A](mvp-plan.md#plan-revision-s3-a-boot-from-system-reset-the-board-policy-m5-and-release-candidate-staging)
of the accepted [MVP plan](mvp-plan.md), and the bounded
[M5 plan](mvp-m5-plan.md), "release candidate 2, boot from system reset".
It also delivers, as its own commit for the human's review and use, the
partition tool `mvp/tools/k3-make-partition.sh` with its host self-test.
Both plans carry out the human's directions of 2026-10-29, quoted in the
revision's status paragraph: `modify the plan so that the mvp candidate
boots from system reset. I don't know where those safety rules came
from.`, the two question rounds, and the standing rule `no more kexec
unless I approve it`, clarified `no more kexec means don't use this from
here, unless it is truly needed for something. use p3. make soft limit
5000. proceed.` The packet was written by the orchestrating session under
the repository's model split; at the human's request (`then have opus 5.5
review the plan for steering input`) the plan's draft was reviewed
read-only by `claude-opus-5.5` (`max`, `long_context`), and its findings
and their resolutions are in section 5. It also records the responsible
human's decisions on both targets.

## Decision record

The responsible human accepted exact commit
`0d134bbc49377576b961989831a02c068b479355` (parent `6a5f6fed`, tree
`67e96d05`) as Plan revision S3-A of the MVP plan and exact commit
`0066794dbec22807d46cc274f2ad00fb79b555ae` (parent `0d134bbc`, tree
`c367c601`) as the M5 plan, both on branch `beryllium/mvp-m5-plan`
from `6a5f6fed`, on 2026-10-29, and separately authorized M5
implementation. The instruction, given in reply to this packet's request
to decide on `0d134bbc` and then on `0066794d`, was `accept 0d134bbc and
066794d, authorize m5`. The written `066794d` matches no object in the
repository (`git rev-parse --disambiguate=066794d` returns nothing);
`0066794d` resolves uniquely to the proposed M5 plan commit, which was
the only decision-2 target this packet asked the human to decide on, so
the instruction is read as `accept 0066794d` with its leading zero
dropped, as the M4 plan's `0d02df27` was read as `0d02df72`. Q1 to Q16
were not answered, so their defaults apply.

- **Scope:** acceptance covers exactly the two texts at their commits:
  the appended revision in `planning/mvp-plan.md` at `0d134bbc` and
  `planning/mvp-m5-plan.md` at `0066794d`. Sections 1 to 10 are the
  packet as presented, apart from the status rows of section 1 and the
  closing lines of section 10, which now show the outcome. The decisions
  are recorded only here and in the two plans' own decision records.
- **Decision support:** the packet commit `87587596`, the partition tool
  commit `952f9e0c` (a delivered tool, not a decision), and this
  acceptance-record follow-up are decision support, not plan content.
- **Review:** the plan's draft was reviewed for steering by
  `claude-opus-5.5` at the human's request; its findings are
  incorporated in the accepted text (section 5), and the accepted text
  was not re-reviewed.
- **Authorized** (`authorize m5`): work packages M5-2 to M5-7 and the
  characterization M5-6a under the accepted plan, on branch
  `beryllium/mvp-m5` from this acceptance-record commit, ending in one
  review packet for the release candidate 2 commit `R2`. M5-6a and M5-6
  issue no board command before the human has created the partition
  with the delivered tool and confirmed that the board is free; the
  human is present at the install, the restore, and any recovery. The
  plan's defaults apply (the M5 plan's decision record lists them). Each
  of the plan's thirteen stop conditions returns M5 to the responsible
  human; a soft limit exceeded returns the limit for re-evaluation.
- **Not authorized:** any release-path step; any push, merge, or tag;
  any kexec use (the standing rule; S3-A policy item 2); any write to
  the NOR firmware or to the environment partition outside the recorded
  session; any change to a monitor source, the shim, a guest input, a
  scenario, the generator, an expectation, the checker's rules beyond
  the new mode, the lock beyond the enumerated roles, `model/`, or an
  accepted document's text; root integration; U-Boot's `reset` or
  `boot`; a second serial reader; an SD card.
- **Evidence status:** acceptance adds no implementation or evidence.
  Nothing of M5 has been built; the partition tool's `--apply` on the
  board is the human's act and had not happened at acceptance. Hardware
  is `NOT RUN` for M5.

### Errata and stops under the accepted plan

Recorded here as M4's were; the accepted plan's text at `0066794d` is
not edited.

1. (M5-2 and M5-3, stop condition 8, 2026-10-29.) At the merge of the
   three M5-2/M5-3 branches (`d798b065`, then the `tmux` lock role
   `0e733e76`) the added code since the acceptance record `9b3fa982`, by
   the plan's counting rule, is 6,865 lines against the soft limit of
   5,000 (`mvp/README.md` open item 71 has the breakdown: the board tools
   2,113, the tests and fakes 1,529, the U-Boot rehearsal 1,196, the two
   checkers 741, the other tools 897, Make and the wrapper 320, 69 other).
   Nothing was cut. The responsible human re-evaluated the limit and
   **re-set it to 10,000 lines** (`reset m5 code limit to 10000, proceed,
   board is free`, 2026-10-29); the same instruction confirmed the board
   free for M5-6a. The other soft limits are unchanged.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review targets | **Decision 1:** exact commit `0d134bbc49377576b961989831a02c068b479355` (parent `6a5f6fed`, the tip of `beryllium/mvp-m4`: release candidate 1, its acceptance record, and the walkthrough), on branch `beryllium/mvp-m5-plan`; it appends Plan revision S3-A to `planning/mvp-plan.md` (192 lines added) and changes nothing else. **Decision 2:** exact commit `0066794dbec22807d46cc274f2ad00fb79b555ae` (parent `0d134bbc`); it adds `planning/mvp-m5-plan.md` (774 lines) and nothing else. **Delivered for review, not a decision:** the partition tool commit (section 2), which adds `mvp/tools/k3-make-partition.sh`, its self-test, and fake block tools under `mvp/tests/`, wired into no target yet. This packet and the status pages follow in a fourth commit. |
| Current status | **Responsible-human accepted on 2026-10-29** (instruction `accept 0d134bbc and 066794d, authorize m5`, read as `0066794d`; Q1 to Q16 at their defaults), with M5 implementation authorized; see the [decision record](#decision-record). As presented: documentation and one human-run tool. Both plans were proposed and not accepted; the M5 plan is void without S3-A. Nothing under `mvp/` other than the delivered tool has changed; nothing has been built for M5; no M5 board command has been issued. The board was read once, read-only, over `ssh` on 2026-10-29 for the NVMe listing the tool's self-test is modelled on (`lsblk`, `blkid`, `sfdisk --dump`, `btrfs filesystem show`, `dumpe2fs -h`); the listing is kept in the session's private files, not the repository. The fast source checks pass (whitespace; every link and anchor in the two plans and this packet). Release candidate 1 (`c5df0cfa`) stays accepted and is not reopened. |
| Decisions requested | Recorded outcome: both accepted, M5 authorized. As presented, **in order:** (1) accept exact commit `0d134bbc` as Plan revision S3-A, request revisions, or defer; (2) accept exact commit `0066794d` as the M5 plan and, separately, authorize M5 implementation, request revisions, or defer; answer any of its Q1 to Q16 or let the defaults apply. Decision 2 depends on decision 1. Five defaults are flagged in section 3: Q9 (the rehearsal's U-Boot source, a departure from the human's answer), Q5/Q11 (the run plan: 20 counted runs, probes first, about 36 resets), Q8 (what of the environment record is committed), Q15 (the human's presence at install and restore), and Q1 (the partition: 1 GiB from p3). |
| Successor status | After the decision: M5-2 to M5-7 and M5-6a are authorized on `beryllium/mvp-m5` from the acceptance-record commit, the board steps waiting on the human's partition and confirmation; everything else stays not authorized. As presented, not started and not authorized: M5 implementation (M5-2 to M5-7 and the characterization M5-6a, which decision 2 with `authorize M5` would authorize on `beryllium/mvp-m5` from the acceptance record, the board steps waiting on the human's partition and confirmation); any release-path step; any merge or push; any kexec use. |
| Publication status | Private repository. `beryllium/mvp-m5-plan` is local and unpushed; the development branch `beryllium/single-hart-runtime-r0` is at `fb8accc9` locally and on the private `origin` (its fast-forward to the M4 acceptance record `6a5f6fed` is a separate instruction the human may give); `beryllium/mvp-m4` and `beryllium/mvp-m4-plan` are on `origin`. No tag, publication, or release. |

As presented: please review exact commits `0d134bbc` and then `0066794d`
and decide on each; the partition tool's commit is for your review and
your one `--apply` run on the board, on your schedule. Outcome: both
accepted, M5 authorized; see the [decision record](#decision-record).

## 2. Deliverables

```text
# git diff --name-status 6a5f6fed 0d134bbc     (decision 1)
M       planning/mvp-plan.md
# git diff --name-status 0d134bbc 0066794d     (decision 2)
A       planning/mvp-m5-plan.md
# git diff --name-status 0066794d 952f9e0c     (the partition tool, delivered)
A       mvp/tools/k3-make-partition.sh
A       mvp/tests/test-k3-make-partition.sh
A       mvp/tests/fake-partition-tools/ (14 wrappers, fake-partition-tools.py, k3-nvme.json, 2 golden lists)
# this packet's commit
A       planning/mvp-m5-plan-review-summary.md
M       planning/README.md  planning/roadmap.md  planning/.vitepress/config.mts
M       planning/HANDOFF.md  .github/copilot-instructions.md
```

**Plan revision S3-A** (192 lines appended after the accepted plan's
status record; the accepted text above it is untouched): where the
inherited "board safety boundary" came from (automation's own B0 README,
`62060e2d`, never human-directed); the board policy in seven items (boot
from reset; kexec not used from here on unless the human approves a
stated need; the NOR firmware never written, the saved environment
changed only within a recorded session and restored; one Beryllium
partition; `k3ctl` or human resets; templated, recorded typing by
automation or the human present at install, restore, and recovery;
private environment records); milestone M5 with its goal, deliverables,
and exit, after M4 in the order; release-candidate staging (RC1
`c5df0cfa` accepted history, RC2 = M5's result; release path step 1
restated as "the latest release candidate's exact commit is accepted");
decision D17; a table of the eight accepted lines the revision
supersedes, each quoted with its line number at `6a5f6fed`; the
consequences; and a status-record addendum.

**The M5 plan** (774 lines, in the form of the M4 plan): decision
requested; Q1 to Q16 with defaults and alternatives; goal and an
eight-part pass criterion; base and inputs (the human's answers; the
board facts with their sources; the inputs reused); the design (the boot
path with `bootcmd`, `be_boot`, `be_ld`, `be_go`, `be_part`, `be_image`,
`be_orig_bootcmd`; the console tool's fixed templates; the reset and
dongle rules; the exact restore rule; recovery; run attribution by
U-Boot's `crc32`; the session protocol with who acts at each step and
the attended characterization M5-6a; the tool changes and the kexec
removal; QEMU-only images; the U-Boot rehearsal; the partition tool; the
claim's new board clause and required-limit text; what M5 does not do);
soft limits (5,000 lines for M5 with the counting rule); tests and
evidence; six departures from accepted decisions; risks; the claim
boundary; work packages M5-1 to M5-7; thirteen stop conditions; how M5
feeds the release path; and a status record.

**The partition tool** is described in section 6.

## 3. Claim boundary

**What the targets support saying.** A plan revision exists that, if
accepted, replaces an automation-written board rule with a policy the
responsible human decided, adds a milestone, and stages the MVP as
release candidates; and a bounded plan exists that, if accepted and
authorized, would produce the board tools for a boot from system reset,
remove kexec from the MVP line, rewrite the claim's board clause, and
make release candidate 2's board evidence by boots from reset, each run
attributed to its image. Neither adds evidence: no board command of M5
has been issued, nothing has been built, and release candidate 1's
evidence and acceptance stand as they are.

**What remains the human's judgment, with the defaults flagged.**

- **Q9, the rehearsal's U-Boot.** The human's answer named Fedora's
  `uboot-images-riscv64` package; Fedora 44's x86_64 repositories carry
  only the `armv8` and `x86_64` image packages (checked 2026-10-29), so
  the default is B3's pinned upstream v2022.10 build
  (`qemu-riscv64_smode_defconfig`, the release the BSP's U-Boot is based
  on), an external input whose binary SHA-256 the lock records; the
  Fedora package from koji is the alternative only if it can be locked.
- **Q5 and Q11, the run plan.** 20 counted runs: the three M0 probe
  images once each from a cold boot first (the platform record's probe
  values were made after a kexec), then the three scenarios three GCC
  and one Clang each, then the five board negatives once each. With one
  `saveenv` per image group (the human's decision 6) that is 14 groups,
  15 `saveenv`s, and about 36 `k3ctl` resets, about one hour. The
  reviewer's two-`saveenv` alternative costs a Fedora boot per group and
  was not taken.
- **Q8, the environment record.** The repository gets the normalized
  records' SHA-256s, the `be_*` names and values, the human's `bootcmd`
  as a SHA-256, V, the verdicts, and capture excerpts from `Autoboot in`;
  the full `printenv` texts stay private (outside the repository and
  `build/`), and the human reviews the first release candidate 2 board
  record before it is committed. The alternative, a redacted copy, would
  still show the human's boot configuration.
- **Q15, presence.** The human is present at the environment's install
  and restore and at any recovery; the runs between are unattended.
- **Q1, the partition.** 1 GiB, ext4, label `beryllium`, from p3 (the
  human's `use p3`), by the delivered tool, which the human runs with
  `sudo`, dry run first; its one `--apply` is the human's act, before
  any M5 board command. The listing of 2026-10-29 puts the new partition
  at GPT entry 6 between p3 and p4.

**What the plans explicitly do not do.** No monitor, shim, guest,
scenario, generator, expectation, or `model/` change; no kexec anywhere;
no write to SPL, OpenSBI, U-Boot, the environment partition outside the
recorded session, any other partition, `env_k3.txt`, or the UFS; no
`env default`, `env erase`, flash, MTD, or firmware command; no U-Boot
`reset` or `boot`; no second serial reader; no SD card; no release step,
tag, push, or merge; no re-run of release candidate 1's campaigns; no
security model or `model/` revision; no edit to an accepted document's
text other than the appended revision.

**Evidence status.** No evidence is added. Hardware is `NOT RUN` for M5.
The one board access was the read-only listing named above.

## 4. Load-bearing decisions

| Decision | Where | Why it matters |
| --- | --- | --- |
| kexec is not used from here on; a truly needed use is stated and approved | S3-A policy item 2; M5 plan stop condition 11 | The human's standing rule; the MVP line's tools and claim lose kexec, and the retained records stay history |
| The saved environment is changed only within a recorded session, with `be_`-prefixed variables and a `bootcmd` that falls through to the human's own | S3-A item 3; the boot path | The human's boot stays the default whenever the MVP image cannot load; the restore returns `bootcmd` byte for byte |
| The pre-save `printenv` check and the fresh-prompt rule | "Typing at U-Boot"; "The restore rule" | The environment is compared before every `saveenv`, so a bad copy is caught before it is stored; session variables are never saved |
| Only the printed environment is compared; the stored bytes are not claimed restored | "The restore rule"; Q7's limit text | The claim says exactly what was checked |
| Run attribution by `crc32` with four other conditions | "Run attribution and distinctness" | Every board image of one candidate has the same size (fact from the records), so size proves nothing; the CRC is printed by U-Boot in the capture itself |
| QEMU-only images differing only in `text_offset`; the board images unchanged | "Tool changes"; "The U-Boot rehearsal" | `booti` relocates to the RAM base plus `text_offset`, which puts the board image at the wrong QEMU address; the rule keeps the board bytes the accepted ones |
| `k3ctl` or human resets only; U-Boot's `reset` and `boot` never typed; the port-open rule | Q14; "Resets and the dongle" | Uniform launches; this board's software reset is unreliable; a transient during `saveenv` could corrupt the NOR environment |
| The probes run first from a cold boot | Q5, Q11 | A cold boot is a different initial state from after-kexec; a probe stop ends the session before the scenarios |
| The characterization before the first `saveenv` | M5-6a | The relocation, U-Boot's memory use, and the copy's exactness are proved with nothing stored |
| The partition tool has no default source and refuses on any identity mismatch | "The partition tool" | The boot disk carries the running system; the human names what is shrunk, by identity |
| The `KEXEC_*` names and the `kexec_fdt` object stay | Q6; stop condition 6 | Renaming them changes the configuration identity, which M5 must not change |
| 5,000 lines for M5 as a re-evaluation limit | "Soft limits" | The human's figure; the reviewer's estimate is 2,300 to 3,300 |

## 5. Review history and resolved findings

The plan's draft (the session plan of 2026-10-29) was reviewed read-only
by `claude-opus-5.5` at the human's request. Verdict: **ready with
corrections**, two blockers (F1, F2) and fourteen should-fix or consider
findings (F3 to F16), with answers to the fourteen questions put to it.
The review text is kept in the session's files; every finding and its
resolution:

| # | Finding | Resolution in the plan |
| --- | --- | --- |
| F1 (blocker) | The QEMU U-Boot rehearsal would relocate the board images to `0x8600_0000`, not `L`; every expectation requires `shim=0x108000000` | QEMU-only images differing only in header bytes 8 to 15 (`BE_MVP_QEMU_TEXT_OFFSET`, already defined in `mvp-layout.h`), checked byte-equal elsewhere; `Moving Image from … to 0x108000000` required |
| F2 (blocker) | Every board image is the same size, so no capture can identify its image or toolchain; a failed select would be judged under the wrong label | `be_ld` ends with `crc32`; staging records 14 pairwise-distinct CRCs; the five-condition attribution rule |
| F3 | U-Boot's `reset` may not reset this board; step 3 reset a running Fedora; `boot` proves nothing about the saved environment | `k3ctl` or human resets only; clean shutdown before the first reset; `reset` and `boot` never typed (Q14) |
| F4 | Hush re-quotes on substitution, so a quote in `bootcmd` corrupts the copies; the environment was checked only after `saveenv`; long lines truncate; an allowlist admits any arguments; the B6 precedent was misquoted (its script sent nothing; a session script typed, and misfired once) | Stop on `'`/newline/non-printable in `bootcmd`; fixed templates, 60-character lines, echo compared before Enter, one retry; short variables with literal addresses; pre-save `printenv` check; bare `setenv NAME` to delete; fresh-prompt rule; the precedent restated |
| F5 | "Byte-identical" overclaims: `printenv` shows runtime values and imports, and the redundant environment's flag byte changes every save | The exact restore rule (two pre-records, V, normalization); the claim says only that the printed environment equalled the record |
| F6 | The removal list broke the preflight's own region check (`kexec-load.py probe`/`region-check` used by the preflight, `platform-record.py`, `evidence.py`, `rc-record.py`, `tools.mk`); the scenarios declare `kexec_fdt` | `probe`/`region-check` move to `tools/platform-probe.py`; the dependency list is in Q6; `KEXEC_*` and `kexec_fdt` names unchanged |
| F7 | The preflight reads Fedora's `/proc/iomem`, not U-Boot's memory use; the MVP receives the control DT, not the kernel DTB | `bdinfo` and `fdt print /reserved-memory` in the characterization, checked against the MVP extents |
| F8 | Characterize before the first `saveenv` | M5-6a: version, help, env info, bdinfo, nvme scan, fsuuid, ls, the DT, two `printenv`s, the copy test, one typed boot of `probe-platform` |
| F9 | M1's reset preconditions depend on Linux; the dongle's port transients could hit a `saveenv`; unexplained banners; a missed `s` | "Resets and the dongle": the port-open rule, the timeout rule, every banner mapped to a reset, the missed-`s` rule; "a new boot" redefined |
| F10 | `a1` is the relocated DT (`Loading Device Tree to F`); QEMU prints `Using Device Tree in place`; BSP three-decimal stamps and noise lines; requiring hart 0 would refuse most QEMU runs | The `uboot` mode's exact line set, board/QEMU variants, stamps and noise allowed, boot hart by launcher |
| F11 | "Serial" had no pattern; prior records kept full captures out; `bootcmd` likely carries a UUID; `build/` is fragile for the only copy | Q8: hashes and verdicts committed, full texts private (0600) and in picocom's log; MAC and `serial#` backstop patterns; the human reviews the first record |
| F12 | "Unmodified" is unsupportable (no NOR hash); "one host kernel" no longer describes the launch; changing the claim departs from M4's Q6 | The clause and limit texts in Q7; "unmodified" not claimed; departure 4 |
| F13 | "Seven images" should be 14; 15 `saveenv`s; about 36 resets; stop 4's "any other line differs" unsatisfiable | Q5 counts; probes first; stop condition 4 restated to verdicts and compared counts |
| F14 | Partition script: no default source; `sfdisk --no-reread` + `partx`, not `partprobe`; backups; GPT entry 6 lands between p3 and p4; no board command for the dry run before acceptance | The tool as delivered (section 6); its self-test uses a synthetic fixture modelled on the saved listing |
| F15 | "Revision 2" misnames the form; list every superseded line; two ordered commits; the standing rule in the instructions; ask the scope of "no more kexec" | "Plan revision S3-A"; the superseded-lines table; this packet's two ordered decisions; the rule in `.github/copilot-instructions.md` and `HANDOFF.md`; the human's clarification recorded |
| F16 | Environment and device preconditions (`bootcount`, `preboot`, `bootdelay`, `env_k3.txt`, one-shot boots, the watchdog, display and NVMe left running) | The preconditions in "The restore rule"; the facts in "Base and inputs" |
| Q13 of the review | The code estimate is 2,300 to 3,300, over the then-limit of 3,000 | The human re-set the limit to 5,000; the counting rule is stated |
| Q3 of the review | A two-`saveenv` alternative (a fixed file name rewritten from Fedora between groups) | Not taken: it costs a Fedora boot per group; the human's decision 6 stands with the CRC check |

The accepted-form findings of the review's answers (the exact `uboot`
mode lines, the attribution rule, the distinctness rule, the recovery
steps, the ordering of M5-6) are incorporated as written.

## 6. The partition tool

Exact commit `952f9e0c66c6c9fba3198ee7b1b024531e2dc2b1` (parent
`0066794d`) adds `mvp/tools/k3-make-partition.sh` (1,219 lines, 124 of
them its header), `mvp/tests/test-k3-make-partition.sh` (361), and
`mvp/tests/fake-partition-tools/` (a 571-line Python implementation
behind 14 eight-line wrappers, a 126-line synthetic fixture
`k3-nvme.json`, and two golden call lists); nothing else. No Makefile
target or wrapper command runs the self-test yet (M5-2 adds it to
`check`); the existing lint wildcards already cover the two scripts, and
`make -C mvp lint` passes with them. It is the human's tool, not a
decision: review it, then run its dry run and, when you choose, its
`--apply` on the board.

**What it does.** The human runs it once on the board's Fedora with
`sudo`. It shrinks the btrfs partition the human names (p3, the Fedora
44 root, by `use p3`) by `--new-size` GiB (default 1) and makes the freed
tail of that extent a new GPT partition holding ext4 labelled
`beryllium`, the first free GPT entry (6 on the listing of 2026-10-29,
on disk between p3 and p4); it prints that number as `be_part`.

**How it protects the boot disk.**

- Dry run by default; it executes only `readlink`, `lsblk`, `blkid`,
  `sfdisk --dump`, `findmnt`, reads of `/sys`, `dumpe2fs -h`,
  `btrfs filesystem show`, and `blockdev --getsize64`, and prints every
  command `--apply` would run, in order, with the exact `--ack` string.
  Run the dry run with `sudo` too; without root it lists what it skipped
  and exits 4.
- No default source. `--disk` must be a `/dev/disk/by-id/` name that
  resolves to a whole NVMe namespace; `--source-part`, `--source-uuid`,
  and `--source-label` name the partition and its filesystem; with
  `--apply`, `--expect-model`, `--expect-serial`, and
  `--expect-size-bytes` must match `/sys/class/nvme/<ctrl>/{model,serial}`
  and the disk's size, `--backup-dir` must be an existing, empty,
  writable directory not on the source, and `--ack` must be exactly
  `I accept shrinking <by-id source path> by <N> GiB`.
- Eleven preconditions, every failure listed before it exits 3: GPT with
  512-byte sectors and 128 entries; the source is btrfs with the expected
  UUID and label, not mounted, no holders; the next partition is
  contiguous or the gap is at least the new size; the new start is 1 MiB
  aligned; the filesystem has one device, no larger than its partition,
  and its used bytes plus 1 GiB fit after the shrink; no filesystem,
  partition name, or `by-label`/`by-partlabel` link carries the label;
  a GPT entry is free and the kernel has no partition with its number;
  the reference partition (p4, the F45 `/boot` this U-Boot reads) is
  ext4.
- The `--apply` order: backups into the human's directory (`sfdisk
  --dump`, the primary and backup GPT sectors by `dd` with their `EFI
  PART` headers checked, `blkid`, `lsblk`, the reference's features, and
  every partition's probed TYPE/UUID/LABEL), `sync`; `btrfs check
  --readonly`; the filesystem shrunk first by the new size plus 64 MiB
  (`btrfs filesystem resize <devid>:-<bytes>` on a temporary
  `subvolid=5` mount under `/run`), `sync`, `umount`, the new size
  checked; the table re-read and required to still equal the backup;
  `sfdisk --no-reread --no-tell-kernel -N <source>` with `,<new size>`
  and `--append` with the exact `start=, size=, type=, name=` line; the
  written table compared with the plan; `partx -u`/`-a`; the kernel's
  sizes checked with `lsblk` (a stale view stops before any `mkfs`,
  naming a reboot) and udev's `-part6` link awaited; `mkfs.ext4 -q -L
  beryllium -m 0`; `e2fsck -f -n`; the features, block size, and inode
  size compared with p4's (a difference exits 5 after the records, the
  partition left in place; `--allow-feature-mismatch` accepts it);
  `btrfs check --readonly` again; the after-records; the untouched
  partitions' identity lines required byte-identical; `SHA256SUMS` of
  the backup directory.
- No automatic rollback: a stop (exit 6, also on HUP/INT/TERM) unmounts,
  prints the disk's state, the backup paths, and the restore command
  `sfdisk --no-reread --no-tell-kernel -- DISK <
  DIR/sfdisk-dump.before.txt` then a reboot; the human decides. It never
  deletes a partition, never rereads the whole table, writes to no
  partition but the source (the resize) and the new one (`mkfs`), and
  touches no other disk.
- Test-only hooks `K3MP_ROOT` (prefixes `/dev`, `/sys`, `/run`) and
  `K3MP_FAKE_ROOT_OK=1` are announced loudly when set and refused when
  the tool runs as root.

**Verified on this host** (2026-10-29): `bash mvp/tests/test-k3-make-partition.sh`
→ `k3-make-partition self-test: PASS (22 cases)` (a dry run; twelve
refusals including two wrong values listed in one run; the apply
sequence against the golden call list, whose `sfdisk` lines are
`,829044736` and `start=834166784, size=2097152, type=0FC63DAF-…,
name=beryllium` and whose resize is `1:-1140850688`; a feature mismatch
with exit 5 and no deletion; the resize failing with exit 6, `umount`
called, no `sfdisk` write; a stale kernel view; an identity change on
another partition; the non-root dry run with exit 4; four usage errors;
`shellcheck`). `shellcheck -s bash` is clean on the tool, the test, and
the wrappers with no disable directives. The coding model additionally
ran the exact two `sfdisk` writes with this workstation's `sfdisk`
(util-linux 2.41.5) on a sparse image carrying the board's layout:
partition 6 came out at start 834166784, size 2097152, between p3 and
p4, with the header and the other entries unchanged, and the printed
restore command restored the identical table. The tool has not run on
the board.

**For the human's run.** Copy the backup directory off the board
afterwards. Run on the serial console or inside `tmux`, so a dropped
`ssh` cannot stop it between steps. Expect `btrfs check --readonly` of
the 396 GiB filesystem to take a minute or two, twice. The dry run's
output is the first thing to send back; the `--apply` output and the
backup directory's `SHA256SUMS` are the record M5-6 cites.

## 7. Validation and retained evidence

- Fast source checks at the packet's commit: `git diff --check` clean;
  every Markdown link and anchor in the two plans, this packet, and the
  status pages resolves (checked by script against the headings).
- The partition tool: `bash mvp/tests/test-k3-make-partition.sh` and
  `shellcheck -s bash` on the tool and the test, as section 6 records.
- No build, QEMU run, evaluator run, or board command of M5 was made.
- Retained: the session's private files hold the steering review, the
  pre-review draft, and the read-only board listing; none is repository
  content.

## 8. Recommended review sequence

1. S3-A's status paragraph and "Where the rule came from"; then the
   board policy, item by item.
2. The M5 plan's "Decision requested" and Q1 to Q16, with the five
   flagged defaults (section 3).
3. "The boot path", "Typing at U-Boot", "Resets and the dongle", "The
   restore rule", "Recovery": the safety of the mechanism.
4. "Run attribution and distinctness" and "The session protocol": how a
   run is tied to its image and what you do at each step.
5. "Tool changes" and "The U-Boot rehearsal": the kexec removal (Q6) and
   the QEMU-only images.
6. "Documents and the claim": the new board clause and limit text (Q7).
7. The partition tool (section 6): its preconditions, its order of
   operations, and its self-test; run its dry run on the board when you
   choose.
8. "Soft limits", "Accepted decisions M5 departs from", "Risks", "Claim
   boundary", "Work packages", "Stop conditions".

Read-only commands:

```sh
git show --stat 0d134bbc 0066794d
git show 0d134bbc -- planning/mvp-plan.md | less        # S3-A, appended
git show 0066794d:planning/mvp-m5-plan.md | less
git show 6a5f6fed:planning/mvp-plan.md | sed -n '200,212p;549,556p;660,668p;695,702p;722,730p'   # the superseded lines
git show 6a5f6fed:mvp/docs/claim.md | sed -n '10,30p'   # the clause the plan replaces
bash mvp/tests/test-k3-make-partition.sh
shellcheck -s bash mvp/tools/k3-make-partition.sh
```

## 9. Human decision checklist

- [ ] The board policy's seven items are the rules you want; nothing in
      them widens what you decided on 2026-10-29.
- [ ] The standing rule's recording ("not used from here on; a truly
      needed use is stated and approved") matches your clarification.
- [ ] The eight superseded lines are the right ones, and M0 to M4's
      texts staying as history is acceptable.
- [ ] Release-candidate staging: RC1 stays accepted history; RC2 is
      M5's result; step 1 restated.
- [ ] The M5 plan's Q1 to Q16 defaults, or your answers; the five
      flagged ones in particular (Q9's U-Boot source departs from your
      answer).
- [ ] The restore rule and the claim's limit text say exactly what will
      be checked.
- [ ] The partition tool's design (no default source; identity checks;
      backups; the order) is acceptable for your one `--apply` run.
- [ ] Your presence at install, restore, and recovery (Q15).
- [ ] Decision 1: accept exact commit `0d134bbc` as Plan revision S3-A;
      request revisions; or defer.
- [ ] Decision 2: accept exact commit `0066794d` as the M5 plan, and
      separately authorize M5 implementation; request revisions; or
      defer.

## 10. After the decisions

- **Accept both (and authorize):** the acceptance record names both
  SHAs and the date, with any answers to Q1 to Q16; the status documents
  are updated; M5-2 to M5-4 begin on `beryllium/mvp-m5` from the
  acceptance record (coding on `claude-opus-5.5`); M5-6a and M5-6 wait
  for your partition and your confirmation that the board is free, and
  you are present at the install and restore. No release step, merge,
  or push follows.
- **Accept S3-A only:** the policy and the standing rule are recorded;
  the M5 plan is revised or deferred as you direct.
- **Request revisions:** new commits and a new packet; neither SHA is
  treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts;
  the standing rule on kexec is in force regardless, as your instruction
  already set it.

**Status:** exact commits `0d134bbc49377576b961989831a02c068b479355`
(Plan revision S3-A) and `0066794dbec22807d46cc274f2ad00fb79b555ae` (the
M5 plan) are responsible-human accepted as of 2026-10-29 (instruction
`accept 0d134bbc and 066794d, authorize m5`, read as `0066794d`; Q1 to
Q16 at their defaults), and M5 implementation is authorized. They are on
branch `beryllium/mvp-m5-plan`, local and unpushed; the partition tool
is delivered; the K3 is untouched by M5 and sits on its Fedora kernel.

**Next:** M5-2 to M5-4 begin on `beryllium/mvp-m5` from this
acceptance-record commit (coding on `claude-opus-5.5` per the model
split). M5-6a and M5-6 wait on your partition (the tool's dry run, then
its `--apply`, with the actual command the session gave you) and your
confirmation that the board is free. The result is presented as one
review packet for the release candidate 2 commit `R2`.

**Action required from you:** none for the plans. Run the partition
tool when you choose, and say when the board is free.
