<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B7 result review and acceptance record

This record presents the result of B7: two copies of the B6 guest, an
unmodified upstream Linux `v7.2` kernel built uniprocessor, run as guests
G0 and G1 on hart 0 of the SpacemiT K3 COM260 under the B7 monitor. It
was implemented and run under the accepted [B7 plan](k3-b7-plan.md),
whose [decision record](k3-b7-plan.md#decision-record) holds its
authorization. It also records the responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`7b6b846bf453bacf4c67d986f87c61fdc092e2ee` (parent
`dd203268280d4aa188399050056cf64ee28689d4`) as the B7 result on
2026-10-09. The instruction, given in reply to this packet's request to
accept, revise, or defer that exact commit, was
`accept 7b6b84, commit and push`. The abbreviation `7b6b84` was checked
to resolve uniquely to that commit.

- **Scope:** acceptance covers exactly that commit and the claim boundary in
  section 3. Sections 2 to 8 are the packet as presented, apart from a note
  above the section 8 checklist. Section 1's status rows and the closing
  lines of section 9 now show the outcome. The decision itself is recorded
  only here.
- **Decision support:** packet commit
  `f69f2203d915bfbdec3b9a1db30c0702ea7f154d` and this acceptance-record
  follow-up are decision support, not implementation.
- **Successor:** acceptance starts no successor, and none is authorized.
  Each of these needs separate direction:
  - merging B6, the re-baseline, and B7 into the development branch;
  - S1 (with the responsible human in a separate session), S2, and S3;
  - the MVP and its first milestone;
  - shared pages, channels, and denial tests;
  - SMP and devices;
  - development-kernel/BSP selection;
  - root `Makefile`/`be`/`scripts/check-be.sh` integration;
  - the LiteBox investigation, a candidate in the [handoff](HANDOFF.md).

  KVM0 and R8 stages H1-H4 stay dropped.
- **Push authorization:** the same instruction authorizes pushing, to the
  private `origin`, branch `beryllium/k3-b7-bringup` through this record,
  plus the `beryllium/k3-b6-bringup` and `beryllium/roadmap-rebaseline`
  refs. Their commits are ancestors of the B7 branch, so the push adds only
  their names. The development branch `beryllium/single-hart-runtime-r0`
  stays at `3bc3ef04` on `origin`; merging into it needs separate
  direction. The B7 worker branches stay local.
- **Evidence status:** the board runs are diagnostic bring-up evidence for
  one board. Acceptance adds no hardware validation, no qualification, and
  no formal-verification claim. It does not tag, publish, or release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `7b6b846bf453bacf4c67d986f87c61fdc092e2ee`, parent `dd203268280d4aa188399050056cf64ee28689d4`, branch `beryllium/k3-b7-bringup`. Comparison base: the B7 plan acceptance record `017c459e32c3e528184e7e8a8804bfd7a9dd344b`, over accepted plan `026974fb` on the step 3 acceptance record `915370aa`. |
| Current status | Implemented, rehearsed in QEMU, and run on the board. Both Linux guests ran interleaved on hart 0 and powered off in 4 of 4 RAM-only COM260 runs through Linux kexec, three GCC and one Clang, with identical counts in every run. No stop condition applied. At the exact commit, in a clean clone, `make -C bringup/k3-b7 check`, the kexec rehearsal, and `kernel-repro` pass, and the rebuilt boot images equal the board images. Responsible-human accepted on 2026-10-09 (instruction `accept 7b6b84, commit and push`). |
| Decision requested | Accept exact commit `7b6b846b` as the B7 result, request revisions, or defer. Recorded outcome: accepted. |
| Successor status | Not started and not authorized. That covers merging B6, the re-baseline, and B7 into the development branch, and pushing it; S1-S3; the MVP and its first milestone; shared pages, channels, and denial tests; SMP and devices; development-kernel/BSP selection; root integration; and the LiteBox investigation. |
| Publication status | Private repository. As presented: `beryllium/k3-b6-bringup`, `beryllium/roadmap-rebaseline`, and `beryllium/k3-b7-bringup`, with B7's three worker branches, local and unpushed, and `origin` holding the development branch at `3bc3ef04`. The instruction `accept 7b6b84, commit and push` then authorized pushing `beryllium/k3-b7-bringup`, through this record, and the `beryllium/k3-b6-bringup` and `beryllium/roadmap-rebaseline` refs to the private `origin`; the development branch stays at `3bc3ef04`, and the worker branches stay local. No tag, publication, or release. |

As presented, the packet asked the human to decide whether exact commit
`7b6b846b` is accepted as the B7 result. The
[decision record](#decision-record) above holds that decision.

## 2. Deliverables

B7 was authorized by the acceptance of exact plan commit `026974fb` on
2026-10-08 (`accept 026974`), recorded at `017c459e`. No open question
was answered, so the defaults apply:

- Q1: a 10 ms slice, 240,000 ticks at 24 MHz;
- Q2: VMIDs 1 (G0) and 2 (G1), with R5's write, fence, and readback on
  every switch;
- Q3: G0's window at HPA `0x1_1000_0000` and G1's at `0x1_1400_0000`,
  each 64 MiB at GPA `0x8000_0000`;
- Q4: no U-Boot run;
- Q5: K = 8 alternations, overlapping `B7INIT 03` phases, and at least
  one `wfi` switch and one slice switch;
- Q6: one static nolibc `/init` that reads its guest ID from `argv`, plus
  B6's two QEMU-only variants;
- Q7: the `BE_B7:`, `BE_B7_G0: `, `BE_B7_G1: `, and `B7INIT`
  identifiers, and SBI implementation ID `0x4245`, version 3;
- Q8: a guest that exhausts its exit ceiling or the time budget fails the
  whole run;
- Q9: B7's own C at `-Os`;
- Q10: HS waits in `wfi` when both guests idle;
- Q11: no `wfi` trap on the board is a stop.

No later direction changed B7. The orchestrator committed the shared
layout header; three workers then built B7-1 to B7-4 in parallel
worktrees (the guest, the core, and the tools), and the orchestrator
integrated them and ran the board steps.

| Commits | Paths under `bringup/k3-b7/` | Purpose and boundary | Key review question |
| --- | --- | --- | --- |
| `6a5f1ac5` | `src/b7-layout.h` | Every fixed address, size, VMID, `hgatp` value, the slice, and every budget and limit, read by the C, the assembly, the generators, and the checkers; fixed before the workers started | Do the values match the plan? |
| `de10c562`, `3ea202e6`, `12b8db77`, `81e80425` (B7-1, guest) | `guest/` (`b7-init.c`, `b7-guest-id.h` and its test, `initramfs.list.in`, `b7-guest.dts.in`, `ref-stub.S`, `pins.txt`), `guest.mk`, `scripts/build-guest.sh`, `gen-dts.py`, `guest-pins.py`, `guest-reference-check.py`, `run-reference-boot.sh` | The nolibc init; B6's pinned Linux `v7.2` build with B6's kernel configuration and fetch script unchanged, an external input that is never committed; the two DTBs, which differ only in the guest digit of `bootargs`; the pins; both reference boots under OpenSBI with no monitor | Is the kernel B6's unmodified pinned build, and do the two guests differ only in their ID? |
| `1f80b503`, `1de5b7f1`, `f920c663`, `4a2da5e4`, `726228f0`, merge `65362626`, `b1648420`, `1b9779b2`, `8c9cbd08`, `1dbb0b03` (B7-2, B7-3, core) | `src/` (`b7-sched.{h,c}`, `b7.h`, `b7-sbi.c`, `b7-gstage.{h,c}`, `b7-payload.{h,c}`, `b7-runtime.c`, `b7-platform.h`, `b7-trap.S`, `b7-boot.lds`, `b7-guest-payload.S`), `scripts/port.py`, `gen-payload.py`, `tests/b7-*-test.c`, `tests/check-b7-image.py`, `Makefile`, `README.md` | The scheduler, SBI core, line console, switch-record logic, G-stage builder and walker with VMIDs and the pair check, and payload checks, all pure C with host tests; B2's port with five counted rules; the HS monitor layer (sequence, switch, dispatch, arm and CSR helpers, deadline, HS wait, exit vector, resume tail); the boot image; the image checker | Is every switch checked, is the new HS interrupt path confined to V=1, and is the layer as small as the plan allows? |
| `b66d9e9c`, `e4463303`, `44f50e93`, `bfa69039`, merge `4d0da81f`, `d4274678`, merge `53e9e88a` (B7-4, tools) | `tests/check-b7-markers.py`, `check-b7-capture.py`, `fixtures/qemu-k3-like.console.log`, `run-qemu.sh`, `kexec-rehearsal.sh`, `kexec-rehearsal/init.c`, `test-kexec-load.py`, `run-tool-dry-run.sh`, `fake-board.py`, `scripts/kexec-load.py`, `k3-run.sh`, `k3-campaign.sh`, `k3-preflight.sh`, `tools.mk` | The marker and capture checkers, with the interleaving floors and the counter sums; the QEMU scenarios; the raw kexec loader and the board tools, copied from B6 with counted changes and the same board-safety model, with both windows in the region check | Are the copies faithful and the checks strict? |
| Merge `b7176f2d`, then `cbcfe13f` (integration) | `README.md`, status documents | The tools merged with the monitor and the guest; the README's guest section, tool rows, board procedure, marker-reading rules, counted change tables, and QEMU results; the known `start_run` gap | Does the README match the code? |
| `dd203268` | None (`planning/HANDOFF.md` only) | Lists a LiteBox guest investigation as a candidate; documentation only | None for B7 |
| `7b6b846b` (B7-5, and B7-6 retention) | `results/20261008-com260/`, `README.md`, status documents | The sanitized records of the four runs, the preflight, and the two load checks; the README's K3 results | Do the records support the claims? |

The monitor layer is about 4,470 lines: `b7.h`, `b7-sbi.c`,
`b7-runtime.c`, `b7-trap.S`, `b7-platform.h`, `b7-gstage.{h,c}`,
`b7-payload.{h,c}`, `b7-sched.{h,c}`, and `b7-layout.h`, against B6's
about 3,080. All of it runs in HS, and `b7-trap.S` (557 lines; B6's has
400) is its assembly. The guest's init is 232 lines. The README's
counted change tables cover every file copied from B6.

Outside `bringup/k3-b7/`, only status text changes:
`.github/copilot-instructions.md`, `planning/HANDOFF.md`,
`planning/roadmap.md`, `planning/glossary.md`,
`planning/implementation-plan.md`, and `planning/project-orientation.md`.
No accepted R0-R7 byte, retained R8 input, or accepted B0-B6 file
changes, and neither does the root `Makefile`, `be`, or
`scripts/check-be.sh`. Reused unchanged: B2's `port.py` and its pinned
output, B1's quiesce, B3's shim, B0's `retain-results.py`,
`summarize-runs.py`, and `mkcpio.py`, and B6's `scripts/fetch-linux.sh`
and `guest/b6-kernel.config`.

## 3. Claim boundary

**Supported by the exact commit:**

- **On the COM260** (2026-10-08; the SpacemiT BSP's U-Boot 2022.10,
  OpenSBI 1.6 reporting SBI 2.0, Fedora `7.1.5-201.0.riscv64.omni.fc44`),
  with boot images whose sources equal the integration merge `b7176f2d`
  (GCC `bd70bc08…452dbc`, Clang `a2b374af…946e44`), in 4 of 4 RAM-only
  runs through Linux `kexec_load`, three GCC and one Clang:
  - the loader placed the image at L = `0x1_0800_0000` and entered B3's
    shim on hart 0, and the shim copied the monitor to `0x1_0200_0000`;
  - the accepted R3 sequence printed `BE_R3:01`-`06`;
  - B7 built and re-walked both roots, each 32 leaves of 2 MiB mapping
    GPA `0x8000_0000` onto its own window (`0x1_1000_0000` for G0,
    `0x1_1400_0000` for G1), and installed them through the accepted
    install function: `BE_B7:02 HGATP_INSTALLED g1=0x800020000010203c
    g0=0x8000100000102034`;
  - the controls read back as `BE_B7:04 GUEST_CONTROLS_CHECKED
    hstatus_controls=0x200180 hedeleg=0xb15c hideleg=0x40
    hcounteren=0x2 sie=0x20 fs=0x0 vs=0x0
    vstimecmp=0xffffffffffffffff`, with `hedeleg` at B6's WARL reading;
  - B7 cleared both 64 MiB windows (about 20.4 ms each with GCC, 15.3 ms
    with Clang) and placed the kernel and each guest's DTB (0.50 to
    0.76 ms per guest);
  - both pinned Linux `v7.2` guests ran in VS mode, interleaved, every
    line whole under its own prefix. Each printed `SBI implementation
    ID=0x4245 Version=0x3`, its own kernel command line ending
    `-- be.guest=<g>`, and `riscv-timer: Timer interrupt in S-mode is
    available via sstc extension`. Each init printed its eight `03 STEP`
    lines, with the two guests' step phases overlapping, then `04 SLEEP
    requested_ms=1000 elapsed_ms=1003 ok=1` (G0) or `elapsed_ms=1011`
    (G1) and `05 RESULT pass`, and powered off;
  - every run printed `BE_B7_COUNTS: g0_exits=583 g0_sbi=160 g0_wfi=356
    g0_slice=67 g1_exits=594 g1_sbi=162 g1_wfi=363 g1_slice=69
    switches=847 wfi_switches=711 slice_switches=135 stop_switches=1
    idle_waits=646 alternations=73`, against the plan's floor of 8
    alternations;
  - K3 trapped the guests' idle VS `wfi` to HS, 356 and 363 times. Each
    trap carried the `wfi` encoding in `stval`, since any other value
    would have ended the run as `virtual-instruction`. HS took its own
    Sstc timer interrupt 136 times while a guest ran, and 135 of those
    led to a switch. The plan's main K3 risks, no `wfi` trap (Q11) and
    no HS timer interrupt (stop 6), did not arise;
  - the monitor reported both shutdowns with `base=14 time=0
    dbcn_byte=0 srst=1 refused=0` per guest (`dbcn_write=98`, and
    `dbcn_read` 47 and 49), then `BE_B7:10 RUN_COMPLETE` and `BE_B7:11
    SHUTDOWN type=0 reason=0`. A run took `0x38030c1`-`0x38030c6` ticks,
    about 2.447 s at 24 MHz, from G0's first entry, of which HS waited
    idle about 1.28 s;
  - all four runs, GCC and Clang alike, gave identical counts and the
    same line order; only printk times, tick values, and some `03 STEP`
    `rounds` values, by 1, differed. No `BE_B7:FAIL`, `BE_B7:DETAIL`, or
    `BE_B7:SRST_RETURNED` line printed.
- **The construction:** two disjoint 64 MiB windows; two roots, each
  re-walked before use and mapping only its own window; distinct VMIDs 1
  and 2; DBCN copies from the calling guest's window only; and no shared
  page or channel.
- **In QEMU 10.2.2** with OpenSBI v1.6 (emulation):
  - the plan's 11 scenarios in 16 runs behave as planned: `k3-like`,
    `rva23`, and `plic` pass for GCC and Clang; `no-sstc` and `sbi-3.0`
    fail with `sstc` and `boot`; `sbi-time` passes with `time` above 0
    for each guest; and the five GCC negative variants fail with their
    planned classes: `payload`, `guest-reboot` naming G1,
    `virtual-instruction` naming G0 with `tval` the `rdcycle`,
    `exit-budget`, and `guest-timeout`;
  - QEMU's counts vary between runs, because its timer follows host
    time;
  - the kexec rehearsal of both board images passes;
  - both reference boots, with no monitor, reach `RESULT pass` with
    their own guest IDs.
- **Host:** the pure-C cores pass with identical GCC and Clang output:
  the scheduler in 16 scenarios and 84,389 assertions, including six
  4,000-step pseudo-random runs checked against an independent reference
  model; the G-stage in 16 and 21,647; the payload checks in 8 and 584;
  and the SBI core in 28 and 11,439.
- **Images:** every plan budget holds, and the image checker's rules and
  59-defect mutation test pass for both toolchains:
  - monitor text ends at `0x1_0200_7000` (GCC) and `0x1_0200_7910`
    (Clang), below `0x1_0200_8000`;
  - data and BSS end at `0x1_0200_b688` and `0x1_0200_b520`, below
    `0x1_0200_f000`;
  - the flat image is exactly `0x34000` bytes, and the pool `0x10000`;
  - the kernel file is 1,553,332 bytes with `image_size` `0x1af628`; the
    two DTBs are 4 KiB each; the boot image is `0x1b3000` bytes
    (1,781,760).
- **Guest inputs:** the init, `Image`, and eight DTBs match their pins,
  and a second build reproduced all 10 outputs byte for byte.

**Trusted or assumed:**

- The firmware below HS: the BSP's OpenSBI 1.6, which prints no banner
  on this board, its trap delegation, and its `menvcfg.STCE` setting.
  The `henvcfg.STCE` readback, the guests' Sstc timer lines, and the 136
  slice exits per run show that Sstc reaches VS and that the supervisor
  timer reaches HS.
- K3's VMID tagging. By the specification, distinct VMIDs make
  `hfence.vvma` unnecessary on a switch, and B7 runs none; every switch
  still runs the accepted install function's full `hfence.gvma`. The
  board runs showed no guest crash suggesting stale translations, but no
  test isolates this.
- The loader: Fedora's `kexec_load`, and the preflight's reading of
  `/proc/iomem` and the FDT reservations.
- Linux `v7.2` is a test payload. The monitor does not trust it, and B7
  claims nothing about it beyond the lines it printed.
- This workstation's unpinned tools, as in B2-B6: GCC 16.2.1 (host and
  riscv64 cross), binutils 2.46.1, clang/lld 22.1.8, QEMU 10.2.2, and
  Python 3.14.7. The guest pins hold for this cross toolchain.
- The accepted R1-R3 code as ported by B2, and B1's quiesce and B3's
  shim, all reused unchanged.
- The B7 monitor layer has no proof. Its evidence is host tests, the
  image checker, QEMU, and the board runs.

**Not run or unavailable:**

- Any denial, fault-injection, or cross-guest access test: excluded by
  the plan, so B6's `memory` variant was not carried over.
- R6/R7-style adversarial or proof work for B7: not applicable, as the
  plan states.
- The negative variants, `no-sstc`, `sbi-3.0`, and `sbi-time` on the
  board: QEMU only, as planned.
- A U-Boot run: not planned (Q4).
- A `wfi` trap with another `stval`, a `switch` readback mismatch, or a
  VMID-blind VS-stage TLB on the board: none arose, and none was
  provoked.
- The `start_run` scheduler refusal path, end to end: see section 5.
- Per-exit or per-switch costs: the records hold counts, run and idle
  ticks, and each guest's shutdown time, not a timed exit or switch.
  Any per-event figure would be derived (inference).
- Any second hart, device, interrupt controller, MMIO, DMA, guest FP or
  vector state, console input, or shared page.

**Explicitly not claimed:**

- Hardware validation, qualification, or formal verification.
- Isolation beyond the construction above. B7 ran no denial or
  fault-injection test.
- A scheduler design, VMID policy, guest ABI, SBI profile, or console
  protocol for Beryllium, or OpenSBI as the long-term firmware boundary.
- A development-kernel or BSP selection. The Linux `Image` is a test
  payload.
- Any R6, R7, or R8 claim for B7 code. QEMU, Model, Helium, R-series,
  and B0-B6 claims do not transfer.

## 4. Load-bearing invariants

| Property | Contract and implementation | Test or evidence |
| --- | --- | --- |
| Accepted bytes unchanged | A port of B2 with five counted rules; every other accepted file reused unchanged | `scripts/port.py --check` re-derives the port byte for byte (32 files, 2 changed, 5 rules, 7 substitutions, B2's manifest); the image checker requires the three R3 functions byte-identical to B2's, both inert R5 guest pages equal to B2's, and all 57 accepted R5 linker conjuncts plus the 4 pool conjuncts |
| Each guest maps only its own window | `src/b7-gstage.c`: per guest 32 leaves of 2 MiB, GPA `0x8000_0000`-`0x83ff_ffff` onto HPA `0x1_1000_0000` (G0) or `0x1_1400_0000` (G1), under VMID 1 or 2, and nothing else. An independent walker re-derives each window from its pool's bytes before `hgatp` changes; the pair check refuses shared pages, overlapping windows or pools, equal or zero VMIDs, and equal roots | Host test (16 scenarios, 21,647 assertions); both `BE_B7:01` lines on the board; the image checker's linked `be_b7_descs` and `be_b7_hgatps` against `src/b7-layout.h` |
| The windows are free memory | The monitor image, pool, staging region, kexec FDT slot, and both windows are pairwise disjoint; the loader refuses any `/proc/iomem` child or FDT reservation in the staging region or either window | Static `ASSERT`s; the image checker's six ranges; the loader host test (15 checks); preflight `region_check=PASS`, twice |
| Every switch is checked | `switch_guest` in `src/b7-runtime.c`: save the outgoing exit record and eleven CSRs; install the incoming root through the accepted install function and require the readback; load the incoming CSRs, read all back, and compare; copy the incoming record in. The resume tail requires the running guest's `hgatp`. A mismatch is `BE_B7:FAIL switch`, with a `DETAIL` naming the register | SBI host test (record copies, SPP from SPVP, the 11-CSR comparison); image checker (the load helper's writes and readback tail, the save helper's reads, the resume tail's checks); 847 switches per board run with no `FAIL` |
| `hgatp` changes only in accepted code | Every `hgatp` write and `hfence.gvma` is inside the accepted R3 functions; the install function has exactly two call sites, R3's and `install_root`; no `hfence.vvma` | Image checker and its mutation test (a third install call, an `hfence.vvma`) |
| HS takes only its timer, and only at V=1 | `sstatus.SIE` stays 0 and `sie` is exactly STIE, so HS takes the supervisor timer only through the vector while a guest runs; any other interrupt is terminal (`interrupt`). `stimecmp` is written only by the deadline helper and B1's quiesce | Arm and resume checks; the image checker's CSR-writer table and mutations (STIE, `stimecmp`); host classification tests; 136 slice exits per board run with no `FAIL` |
| Only an exact VS `wfi` idles a guest | `hstatus.VTW` set by the arm helper alone; cause 22 with `stval` `0x10500073` and SPVP = 1 parks the guest and steps `sepc`; any other cause 22, or a VU `wfi`, is `virtual-instruction` | Host tests (`stval` match and mismatch, SPVP 0 and 1); QEMU `rdcycle` variant (`tval=0xc00027f3`); image checker (VTW, four HS `wfi`); 719 `wfi` exits per board run with no `FAIL` |
| No guest request reaches M-mode | The SBI subset is emulated in HS; the only `ecall` is the accepted `be_r3_arch_sbi_call`, reached only from the accepted platform helpers | Image checker (one `ecall` site); host tests of every SBI row; `refused=0` for both guests on the board |
| DBCN reads only the calling guest's window | The whole range `[a1, a1 + a0)` must lie in that guest's walked window and the high word must be 0; at most 256 bytes are copied | Host tests at every edge of G0's window, and a test that each guest's call reads its own window |
| Lines never mix, and a guest cannot forge monitor lines | Each guest's bytes are buffered until LF, up to 256, and written with its prefix as one line; CR is dropped, and every other byte outside `0x20`-`0x7e` becomes `?`; a full buffer is written as its own line, and a partial line is flushed when its guest stops and before a `FAIL` line | SBI host test (interleaved guests never form a mixed line); the marker checker rejects a mixed line, a tag inside a guest line, an untagged line, and a line over 256 bytes |
| Controls fail closed | `henvcfg.STCE` readback; every shared control read back at arming (`hstatus` `0x200180`, `hedeleg` within `0xb15d` holding `0xb10c`, `sie` STIE); the resume tail rechecks each, with only `hvip`'s VS bits | QEMU `no-sstc` (`FAIL sstc`); host test; image checker constant tracking and mutations |
| Every other exit is terminal for the whole run (Q8) | Only a VS `ecall` that the SBI core answers, an exact VS `wfi`, the slice, and an SRST shutdown with reason 0 continue the run, the last by stopping its guest; every other exit, an SRST reboot included, prints its class and a `DETAIL` line naming the guest, then requests the SRST shutdown | QEMU `init-exit` and `rdcycle` variants; the marker checker's failure modes |
| Bounded run | A per-guest exit ceiling of 2^20 and a run budget of 2^32 ticks; every HS wait ends at the budget at the latest | QEMU `exit-budget` and `guest-timeout` variants; scheduler host test |
| The scheduler fails closed | `src/b7-sched.c`: restricted C with no loop, CSR, SBI call, or I/O; saturating time arithmetic; invalid input fails and stays failed | Scheduler host test (16 scenarios, 84,389 assertions, six pseudo-random runs against an independent reference model) |
| Payload shape checked before the windows | Kernel and both DTB headers against link-time constants; both windows zeroed; every copy compared; one `fence.i` | Host payload test; QEMU `payload` variant; the image checker's payload constants |
| Images within budget | Text, data, flat image, pool, kernel, DTB, and boot-image limits | Image checker; the measured budgets in section 3 |
| Guest inputs pinned | The Linux commit and tag object, the RPMs, the nolibc sysroot digest, and the build identity are fixed | `guest-pin-check`; `kernel-repro` (10 of 10 outputs identical) |

## 5. Review history and resolved findings

Under the 2026-10-06 SOP, no different-model evaluation, separate scope
review, or deep security review ran as standard practice; the
orchestrator reviewed each worker's output before integration. Every
worker ran on the pinned model, `claude-opus-5.5` at max effort, as
launched.

1. **Workers (process history).** The original three workers died in a
   DNS outage about 19 minutes in, having committed nothing. Their
   uncommitted drafts (the guest worker's init and device-tree drafts,
   and the core worker's `port.py` and `gen-payload.py` drafts) were
   backed up outside the repository. New workers restarted in the same
   worktrees, with those drafts to review and finish, from one shared
   brief that told them to commit early and after every component. They
   finished B7-1 to B7-4 on `beryllium/k3-b7-guest-wip` (`81e80425`),
   `beryllium/k3-b7-core-wip` (`1dbb0b03`), and
   `beryllium/k3-b7-tools-wip` (`53e9e88a`), all local.
2. **Changes and fixes before the board runs:**
   - `81e80425`: the guest-ID host test builds with B6's host GCC and
     Clang commands and requires both to print the pinned line.
   - `b1648420`: the payload host-test count is pinned at 8 scenarios
     and 584 assertions, once the test reads the four variant DTBs.
   - `1b9779b2`: the resume tail sets SPP from the saved SPVP without a
     branch.
   - `d4274678`: the checkers' realistic fixture is now the console of
     one QEMU `k3-like` run of the B7 GCC image, emulation output kept
     as test input, in place of one built from B6's Linux log. Both
     self-tests still pass.
   - `8c9cbd08`: the image checker drops an offset only the U-Boot check
     used.
   - `cbcfe13f`, at integration: the README's dry-run count is corrected
     to 11 scenarios covering 14 cases, and the gap in item 5 is
     recorded.
3. **The plan's departures, as implemented.** Each applies to B7 only
   and changes no accepted byte:
   - two guests share hart 0, each with its own window, root, and VMID;
   - HS takes its Sstc timer while V=1: the arm helper alone sets
     `sie.STIE`, and only the deadline helper and B1's quiesce write
     `stimecmp`;
   - `hstatus.VTW` is set, so a VS `wfi` traps and, on the exact `stval`
     match, parks its guest;
   - the load helper writes the eleven per-guest CSRs, `scounteren` and
     `senvcfg` among them, and reads all back;
   - `hgatp` changes on every switch, to the incoming guest's root and
     VMID (1 or 2), only through the accepted install function and with
     readback;
   - only `hvip`'s VSSIP, VSTIP, and VSEIP are tested, because QEMU's
     `hvip` read shows a pending HS timer as bit 5, which the
     specification makes read-only zero;
   - the HS wait adds one `wfi` (Q10), for four in the monitor;
   - B7's own C compiles at `-Os` (Q9); the port's accepted files, B1's
     quiesce, and B3's shim keep their flags. Section 3 gives the
     measured text.
4. **Implementation choices beyond the plan's text:**
   - The initial per-guest CSR set is all zero except `vsstatus.UXL` =
     2 and `vstimecmp` = `~0`. The plan says the sets start at zero; an
     RV64 hart reads UXL back as 2, and the load helper requires every
     readback to equal the value written.
   - The HS deadline follows the plan's formula: the earlier of now +
     10 ms and the other guest's wake time, if that guest is idle. When
     the other guest idled with its timer already due, the deadline is
     already past, and the running guest is preempted at once. The
     scheduler host test covers it.
   - B6's three guest tools, `guest-pins.py`,
     `guest-reference-check.py`, and `run-reference-boot.sh`, moved from
     B6's `tests/` to `scripts/`.
   - `scripts/build-guest.sh` takes a `B6_DIR` argument and reads B6's
     kernel configuration and `fetch-linux.sh` from there, unchanged,
     rather than copying them.
   - `BE_B7_ONE_COPY` keeps `install_root` one function, so the accepted
     install function keeps exactly two call sites.
   - The failure formats, which the plan leaves open, are B6's with the
     guest added: the exit `DETAIL`, a switch `DETAIL`, and the two
     controls lines.
   - The marker checker is stricter than the plan in places: it requires
     the WARL `hedeleg` rule, `wfi_switches + slice_switches` at most the
     guests' `wfi` plus `slice` exits, `idle_ticks` at most `ticks`, each
     guest's `ticks` at most the run's, and the run's `ticks` within the
     2^32 budget.
5. **Known gap (open, recorded in the README).** `start_run` in
   `src/b7-runtime.c` refuses an unexpected first scheduler decision with
   `BE_B7:FAIL scheduler` and no `DETAIL` line, because no guest has
   exited yet. The marker checker requires a `DETAIL` line for
   `scheduler`, so it would reject that capture as malformed rather than
   read it as a clean `scheduler` failure. The run fails closed either
   way. A freshly started scheduler always picks G0, which the host tests
   cover, so the path cannot trigger in practice.
6. **Estimates and limits.**
   - Clang monitor text ends at `0x7910`, above the plan's inferred
     `0x7000`-`0x7600`, and GCC's `0x7000` is at the top of its inferred
     `0x6c00`-`0x7000`. Both are below the `0x8000` limit, with `0x6f0`
     (Clang) and `0x1000` (GCC) to spare.
   - Data and BSS grew by `0x8e0` (GCC) and `0x898` (Clang) over B6's,
     near the plan's estimate of about 2 KiB.
   - Each guest made 583 or 594 exits per board run, below the plan's
     inferred 1,000-1,500; a run took about 2.45 s of guest time, near
     the inferred 2.5 s.
   - `make check` took 597 s and 654 s, below the plan's inferred 15-25
     minutes.
7. **The board runs (closed).** After run 1 the board stayed halted about
   40 minutes until the human reset it. The first session driver had
   stopped waiting by then, so a resumed driver repeated the read-only
   preflight, which passed with the same facts, and ran runs 2-4. Each
   driver first required a clean tree at `dd203268`. `k3-preflight.sh`
   writes one fixed path, so the retained `preflight.txt` is the second
   preflight; the first's output survives in its private driver log.
   After run 4 the human reset the board, and Fedora was back by about
   20:55Z. No run or attempt was set aside.

Open for your judgment:

- The known `start_run` gap in item 5.
- The implementation choices in item 4, in particular the initial
  `vsstatus.UXL` = 2 and the immediate preemption at a past deadline.
- Isolation by construction only, with no denial test, as planned.
- Per-event costs. The plan's
  [S2 and MVP section](k3-b7-plan.md#how-b7-feeds-s2-and-the-mvp)
  mentions board measurements of exit, switch, and idle costs; the
  records hold counts and run, idle, and shutdown ticks, not timed exits
  or switches.
- The provisional, unregistered SBI implementation ID `0x4245`, now
  version 3.

## 6. Validation and retained evidence

**At the exact commit**, in a clean clone (2026-10-08T21:23:52Z to
21:42:41Z), with no `git status --porcelain` line before or after. Three
overrides applied: `LINUX_GIT` named a local Linux mirror, `B7_RPM_CACHE`
named B3's cached copies of the pinned `m4`, `bison`, and `flex` RPMs,
and `OPENSBI_FW` named B1's OpenSBI v1.6 `fw_dynamic.bin` build in the
main checkout, the default there. The fetch and build scripts check the
pinned commit, tag object, and RPM hashes either way.

- `make -C bringup/k3-b7 check`: PASS in 654 s.
  - Guest: Linux `v7.2` at the pinned commit and tag object; the kernel
    built, and all 10 outputs match their pins. The self-tests pass:
    `gen-dts.py` 57 cases, `guest-pins.py` 45, and
    `guest-reference-check.py` 71, and the guest-ID test 27 (GCC =
    Clang).
  - Port: 32 files, 2 changed, 5 rules, 7 substitutions, B2's manifest
    matched.
  - Host tests: scheduler 16 scenarios and 84,389 assertions, G-stage 16
    and 21,647, payload 8 and 584, SBI 28 and 11,439; GCC = Clang.
  - Images: GCC and Clang, the six variants, and the three DTB variants
    pass the image checker; the mutation test rejects all 59 defects.
  - Reference boots: `RESULT pass` for G0 (`elapsed_ms=1004`) and G1
    (`elapsed_ms=1003`).
  - Checkers: the marker self-test passes 439 cases, and the sources
    check finds all 34 lines; the capture self-test passes 86 cases; the
    loader test passes 15 of 15; the board-tool dry run passes its 11
    scenarios (14 cases).
  - QEMU: `BE_K3_B7_QEMU: PASS scenarios=11 runs=16`. The seven passing
    two-guest runs switched 798-867 times with 45-62 alternations, and
    every negative scenario failed with its planned class.
- `make -C bringup/k3-b7 kexec-rehearsal`, with B0's GCC rehearsal kernel
  (`7.3.0-rc4-gc1c7e254143f`, `4871aa91…`) named by `REHEARSAL_KERNEL`:
  PASS in 65 s for the GCC and Clang board images (897 and 837
  switches, 49 alternations each).
- `make -C bringup/k3-b7 kernel-repro`: PASS in 407 s, 10 of 10 outputs
  identical.
- The rebuilt boot images equal the board images: GCC
  `bd70bc08…452dbc`, the `image_sha256` of all three GCC runs, and Clang
  `a2b374af…946e44`, that of the Clang run.
- Each of the four retained excerpts passes `check-b7-capture.py --mode
  kexec` on its own against the rebuilt image (`BE_B7_CAPTURE[kexec]:
  PASS`).
- `MANIFEST.sha256` matches (`sha256sum -c`, 30 entries).

**Before the exact commit.** `7b6b846b` changes no code after
`dd203268`: only the records under `results/`, the README, and status
documents. `cbcfe13f` and `dd203268` change only documentation, so the
image and tool sources at `dd203268` equal the integration merge
`b7176f2d`.

- **At `b7176f2d`**, in the main checkout, from a fresh build
  (2026-10-08, 18:05Z to 18:20Z):
  - `make -C bringup/k3-b7 check` passed in 597 s, covering the same
    parts. In QEMU, the two-guest runs switched 755-777 times with 29-39
    alternations, and every negative scenario failed as expected;
  - the kexec rehearsal passed in 26 s for GCC (`bd70bc08…`) and Clang
    (`a2b374af…`);
  - `kernel-repro` passed in 232 s, 10 of 10 outputs identical.
- **On the worker branches:** the tools branch at `53e9e88a` passed
  `make check` and the kexec rehearsal, and the core worker's smoke
  matrix ran all 16 runs on images built from `1b9779b2`, the last
  commit that changes them. The README's QEMU results hold both.

**On the board**, 2026-10-08 (UTC), every step from a clean tree at
`dd203268`:

- Preflight PASS at 20:00:31 (boot `345141a6`) and again at 20:43:23
  (boot `63154aac`), each `BE_K3_B7_PREFLIGHT: PASS hart0_dt_sstc=yes
  hart0_cpuinfo_sstc=yes dt_sstc_harts=8/8 timebase_frequency=24000000
  kexec_load=available tmp_fstype=tmpfs region_check=PASS`, with the
  staging region and both windows free of the 20 `/proc/iomem` children
  and the 11 FDT reservations.
- GCC and Clang load checks at 20:01:03 and 20:01:34: `loader=kexec_load
  entry=0x108000000 fdt=0x108200000 image_memsz=0x1b3000
  fdt_bytes=41088 kexec_loaded=1`, then `kexec_loaded_after_unload=0`
  and `outcome=load-only`.
- Kexec runs `20261008T200212Z`, `20261008T204333Z`, and
  `20261008T204720Z` (GCC) and `20261008T205033Z` (Clang): each
  `check_status=0`, in 4 distinct boots, with the staged copy's hash on
  the board equal to the image's, and a human reset after each.

**Retained** under `bringup/k3-b7/results/20261008-com260/`, by B0's
unchanged `retain-results.py` (`BE_RETAIN: PASS runs=4 load_checks=2
files=31`):

- each run's `run.txt`, `load.txt`, `check.txt` (ending with the
  `BE_B7_COUNTS:` line), `result.json`, and handoff excerpt;
- the two load checks, and `preflight.txt`, the second preflight;
- `summary.md`, `captures.txt`, `originals.sha256`, `MANIFEST.sha256`,
  and a README.

The full serial captures hold systemd terminal metadata such as the
board's machine ID, so they are kept privately; `captures.txt` and
`originals.sha256` identify them. The session logs of the integration,
board, and clean-clone runs are also kept privately, outside the
repository.

## 7. Recommended review sequence

1. Claims: section 3 above, then `bringup/k3-b7/README.md` (design,
   budgets, tests, markers with the known gap, QEMU and K3 results, and
   non-claims) and `bringup/k3-b7/results/20261008-com260/README.md`.
2. The plan's [departures](k3-b7-plan.md#accepted-decisions-b7-departs-from),
   [stop conditions](k3-b7-plan.md#stop-conditions), and
   [claim boundary](k3-b7-plan.md#claim-boundary-and-non-goals).
3. The switch and the new HS paths: `src/b7-runtime.c` (`switch_guest`,
   `schedule`, `be_b7_dispatch`, `start_run`, `install_root`), then
   `src/b7-trap.S` (arm, save, and load helpers, the deadline, the HS
   wait, the exit vector, and the resume tail).
4. The scheduler: `src/b7-sched.{h,c}` and `tests/b7-sched-test.c`.
5. The rest of the monitor layer: `src/b7-sbi.c`, `src/b7.h`,
   `src/b7-gstage.c`, `src/b7-payload.c`, `src/b7-platform.h`, and
   `src/b7-layout.h`.
6. The port and the boot image: `scripts/port.py`, `src/b7-boot.lds`,
   `src/b7-guest-payload.S`, and `scripts/gen-payload.py`.
7. The guest inputs: `guest/b7-init.c`, `guest/b7-guest-id.h`,
   `guest/b7-guest.dts.in`, `scripts/build-guest.sh`,
   `scripts/gen-dts.py`, and `guest/pins.txt`.
8. The checkers: `tests/check-b7-image.py`, `tests/check-b7-markers.py`,
   and `tests/check-b7-capture.py`.
9. The board tools: `scripts/kexec-load.py`, `scripts/k3-run.sh`, and
   `scripts/k3-preflight.sh`.
10. The board records.

Read-only commands:

```sh
git --no-pager log --oneline 017c459e..7b6b846b
git --no-pager diff --stat 017c459e..7b6b846b -- . ':!bringup/k3-b7/results'
git --no-pager diff --stat b7176f2d 7b6b846b -- bringup/k3-b7 ':!bringup/k3-b7/results'
git --no-pager diff e20c55df:bringup/k3-b6/src/b6-trap.S 7b6b846b:bringup/k3-b7/src/b7-trap.S
git --no-pager show 7b6b846b:bringup/k3-b7/src/b7-sched.c
git --no-pager show 7b6b846b:bringup/k3-b7/results/20261008-com260/README.md
```

Exact-commit execution in a fresh worktree. `check` fetches Linux `v7.2`
(or takes `LINUX_GIT`, a local mirror), downloads the pinned RPMs unless
`B7_RPM_CACHE` names them, and builds OpenSBI v1.6 through B2's
`opensbi` target unless `OPENSBI_FW` names a build, so it needs network
access. The kexec rehearsal needs B0's GCC rehearsal kernel:

```sh
git worktree add --detach ../be-b7-review 7b6b846bf453bacf4c67d986f87c61fdc092e2ee
cd ../be-b7-review
make -C bringup/k3-b7 check
make -C bringup/k3-b7 kexec-rehearsal REHEARSAL_KERNEL=<B0 GCC rehearsal Image>
make -C bringup/k3-b7 kernel-repro
cd - && git worktree remove --force ../be-b7-review
```

## 8. Human decision checklist

The checklist is kept as presented. The decision is recorded in the
[decision record](#decision-record), not in these boxes.

- [ ] B7 matches the accepted plan with the defaults Q1-Q11: two copies
      of the pinned Linux `v7.2` guest, uniprocessor without FP or
      vector, on the accepted R3 prelude, each under its own B7-owned
      G-stage root and VMID over its own 64 MiB window, switched
      round-robin on a trapped `wfi` and a 10 ms HS slice, with
      per-guest line consoles, B6's SBI subset at version 3, and
      RAM-only kexec runs on the COM260.
- [ ] Every switch is checked: the root goes in through the accepted
      install function, and `hgatp` and all eleven per-guest CSRs are
      read back.
- [ ] The new HS paths are confined as claimed: HS takes only its timer,
      only at V=1, and only an exact VS `wfi` idles a guest.
- [ ] Neither guest can reach M-mode, map memory outside its own window,
      or forge or split monitor lines.
- [ ] The plan's departures, and the implementation choices and the
      known `start_run` gap in section 5, are acceptable.
- [ ] The claims in section 3 match the evidence, and isolation by
      construction only, with no denial test, is acceptable for this
      milestone.
- [ ] Unpinned workstation tools, the external Linux input, and no proof
      for the B7 layer are acceptable for this bring-up milestone.
- [ ] Successor work, including the merges into the development branch,
      S1-S3, and the MVP, remains excluded until separately directed.
- [ ] Decision: accept exact commit `7b6b846b`, request revisions, or
      defer.

## 9. After the decision

- **Accept:** record acceptance of exact SHA
  `7b6b846bf453bacf4c67d986f87c61fdc092e2ee` with its date and
  instruction in a follow-up record. Acceptance would not start any
  successor; push, tag, publish, or release; merge B6, the re-baseline,
  or B7 into the development branch; start S1-S3 or the MVP; select a
  development kernel or BSP; or integrate with the root `Makefile`, `be`,
  or `scripts/check-be.sh`. Each still needs your direction.
- **Request revisions:** make a new commit and a new packet. `7b6b846b`
  is not treated as accepted.
- **Defer:** keep the current status and start no dependent work.

**Status:** exact commit `7b6b846b` is responsible-human accepted as of
2026-10-09. Both Linux guests ran interleaved on hart 0 and powered off in
4 of 4 RAM-only COM260 runs, with identical counts.

**Next:** a successor needs your direction; S1 is with you in a separate
session. Other candidates include merging B6, the re-baseline, and B7 into
the development branch and pushing it, and the LiteBox investigation. None
is started or authorized.

**Action required from you:** none for B7.
