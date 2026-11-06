<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B6 result review and acceptance record

This record presents the result of B6: an unmodified upstream Linux
kernel, built uniprocessor, as the only guest on the SpacemiT K3 COM260.
It was implemented and run under the accepted [B6 plan](k3-b6-plan.md) and
the two later directions in the plan's
[decision record](k3-b6-plan.md#decision-record). It also records the
responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`e20c55df57551244eab47e0eff59d4c71fe75d20` (parent
`1a6ab933b92618054b7c5d5b612604959636531e`) as the B6 result on
2026-10-08. The instruction, given in reply to this packet's request to
accept, revise, or defer that exact commit, was `accept e20c55`. The
abbreviation `e20c55` was checked to resolve uniquely to that commit.

- **Scope:** acceptance covers exactly that commit and the claim boundary in
  section 3. Sections 2 to 8 are the packet as presented, apart from a note
  above the section 8 checklist. Section 1's status rows and the closing
  lines of section 9 now show the outcome. The decision itself is recorded
  only here.
- **Decision support:** packet commit
  `4611007fa61d86c64941bae1d11c18baa2661329` and this acceptance-record
  follow-up are decision support, not implementation.
- **Successor:** acceptance starts no successor, and none is authorized.
  Each of these needs separate direction:
  - merging B6 into the development branch, and pushing;
  - SMP, a second guest, devices, or more guest RAM;
  - development-kernel/BSP selection;
  - root `Makefile`/`be`/`scripts/check-be.sh` integration.

  KVM0 and K0-SC1-B remain parked.
- **Evidence status:** the board runs are diagnostic bring-up evidence for
  one board. Acceptance adds no hardware validation, no qualification, and
  no formal-verification claim. It does not push, tag, publish, or
  release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `e20c55df57551244eab47e0eff59d4c71fe75d20`, parent `1a6ab933b92618054b7c5d5b612604959636531e`, branch `beryllium/k3-b6-bringup`. Comparison base: the B6 plan acceptance record `6b4d165bb4699232caa53e00a630245ae9a8e65d`, over accepted plan `e34ef378` on development-branch tip `3bc3ef04`. |
| Current status | Implemented, rehearsed in QEMU, and run on the board. The first board run stopped at `BE_B6:FAIL controls`, which is stop condition 6. After your `fix-warl` direction, the Linux guest reached its init and powered off in 5 of 5 RAM-only COM260 runs: three GCC and one Clang through Linux kexec, and one GCC through U-Boot `booti`. At the exact commit, in a clean clone, `make -C bringup/k3-b6 check`, the kexec rehearsal, and `kernel-repro` pass, and the rebuilt boot images equal the board images. Responsible-human accepted on 2026-10-08 (instruction `accept e20c55`). |
| Decision requested | Accept exact commit `e20c55df` as the B6 result, request revisions, or defer. Recorded outcome: accepted. |
| Successor status | Not started and not authorized. That covers merging B6 into the development branch, SMP or a second guest, devices, more guest RAM, development-kernel/BSP selection, and root integration. |
| Publication status | Private repository. `beryllium/k3-b6-bringup` and its three worker branches are local and unpushed; `origin` holds the development branch at `3bc3ef04`. No tag, publication, or release. |

As presented, the packet asked the human to decide whether exact commit
`e20c55df` is accepted as the B6 result. The
[decision record](#decision-record) above holds that decision.

## 2. Deliverables

B6 was authorized by the acceptance of exact plan commit `e34ef378` on
2026-10-08 (`accept e34ef378`). No open question was answered, so the
defaults apply:

- 64 MiB of guest RAM;
- one GCC U-Boot run, without `unzip`;
- `flex` and `bison` from B3's pinned Fedora 44 RPMs;
- Linux `v7.2` at `8d3ae59288f1e7d58d76558a6ee96d533bc5019f`;
- `hedeleg` `0xb15d`;
- the B6 identifiers, with SBI implementation ID `0x4245` version 2;
- no board DTB without `sstc`.

Two later directions, both in the plan's decision record, change B6 only:

- **`fix-warl`**, after the first board stop: B6 reads `hedeleg` back as
  WARL.
- **Automation may type at U-Boot**, for the optional U-Boot run: `you
  can also operate the u-boot console by attaching to picocom session`
  (13:23 CEST).

Three workers built B6-1 to B6-4 in parallel worktrees: the guest, the
core, and the tools. The orchestrator integrated them and ran the board
steps.

| Commits | Paths under `bringup/k3-b6/` | Purpose and boundary | Key review question |
| --- | --- | --- | --- |
| `52082119` | `src/b6-layout.h` | Every fixed address, size, budget, and limit, read by the C, the assembly, the generators, and the checkers | Do the values match the plan? |
| `f1f7e0fb`, `f514a038` (B6-1) | `guest/`, `guest.mk`, `scripts/fetch-linux.sh`, `build-guest.sh`, `gen-dts.py`, `tests/guest-pins.py`, `run-reference-boot.sh`, `guest-reference-check.py` | Fetch and build the pinned Linux `v7.2`, an external input that is never committed; the configuration, the init, the initramfs list, the device-tree template, the pins, and a reference boot under OpenSBI with no monitor | Is the kernel an unmodified pinned upstream build, and is the device tree the plan's? |
| `fe460e82`, merge `49980c9a`, `8576bb7e`, `440ca916`, `a88db98e`, `ffef36e1` (B6-2, B6-3) | `src/`, `scripts/port.py`, `gen-payload.py`, `tests/b6-*-test.c`, `tests/check-b6-image.py`, `Makefile`, `README.md` | The pure-C G-stage builder and walker, payload checks, and SBI core, with host tests; B2's port with five counted rules; the HS monitor layer (sequence, arm helpers, exit vector, resume tail); the boot image; the image checker | Is the monitor layer correct and as small as the plan allows? |
| `859e95f9`, `68f66af8`, merge `72713521`, `1fdb15b9`, `86e3636d`, `e16c86f5`, `317d13e2`, `15ef418a`, `49c3c1dd`, `cdd4b8e7`, `2d038bd7` (B6-4) | `tests/check-b6-markers.py`, `check-b6-capture.py`, `scripts/kexec-load.py`, `k3-run.sh`, `k3-campaign.sh`, `k3-preflight.sh`, `k3-uboot-run.sh`, `tests/run-qemu.sh`, `run-qemu-uboot.py`, `kexec-rehearsal.sh`, `run-tool-dry-run.sh`, `fake-board.py`, `tools.mk` | The marker and capture checkers; the raw kexec loader; the board, QEMU, U-Boot, and kexec tools, copied from B0, B2, and B5 with counted changes and the same board-safety model | Are the copies faithful and the checks strict? |
| Merge `3e1531a7`, then `50a75654` (integration) | `README.md`, status documents | The tools merged with the monitor; the README's tool rows, board procedure, and counted change tables; the QEMU results | Does the README match the code? |
| `1a6ab933` (WARL change) | `src/b6-trap.S`, `b6-runtime.c`, `b6.h`, `b6-sbi.c`, `b6-platform.h`, the host test, the image and marker checkers, `README.md`, the plan's decision record, status documents | `hedeleg` read back as WARL, under `fix-warl` | Does it do what the direction says, and nothing more? |
| `e20c55df` (B6-5) | `results/20261008-com260/`, `results/20261008-com260-uboot/`, `results/20261008-com260-stopped/`, `README.md`, the plan's decision record, status documents | The sanitized records of the five passing runs, the stopped run, two preflights, and four load checks; the U-Boot direction | Do the records support the claims? |

The monitor layer is about 3,080 lines: `b6.h`, `b6-sbi.c`,
`b6-runtime.c`, `b6-trap.S`, `b6-platform.h`, `b6-gstage.{h,c}`,
`b6-payload.{h,c}`, and `b6-layout.h`. All of it runs in HS, and
`b6-trap.S` (400 lines) is its assembly. The guest's init is 263 lines.

Outside `bringup/k3-b6/`, only four files change: `planning/HANDOFF.md`,
`planning/roadmap.md`, `planning/k3-b6-plan.md` (the two directions, in
its decision record), and `.github/copilot-instructions.md`. No accepted
R0-R7 byte, retained R8 input, or accepted B0-B5 file changes, and
neither does the root `Makefile`, `be`, or `scripts/check-be.sh`. B2's
`port.py`, B1's quiesce, B3's shim source, and B0's retention, summary,
and `mkcpio.py` tools are reused unchanged.

## 3. Claim boundary

**Supported by the exact commit:**

- **On the COM260** (2026-10-08; SpacemiT BSP U-Boot 2022.10, OpenSBI
  1.6 reporting SBI 2.0, Fedora `7.1.5-201.0.riscv64.omni.fc44`), with
  the boot images built at `1a6ab933` (GCC `b17036e7…cb97d4`, Clang
  `e7f096dc…d12915`), in 5 of 5 RAM-only runs:
  - the loader placed the image at L = `0x1_0800_0000` and entered B3's
    shim on hart 0, and the shim copied the monitor to `0x1_0200_0000`.
    Four runs used Linux `kexec_load` from Fedora (three GCC, one Clang),
    and one GCC run used U-Boot `loady` and `booti`;
  - the accepted R3 sequence printed `BE_R3:01`-`06`;
  - B6 built and re-walked its root (32 leaves of 2 MiB, mapping GPA
    `0x8000_0000` to HPA `0x1_1000_0000`), installed it with a second
    call to the accepted install function (`hgatp=0x8000000000102034`),
    and read back `henvcfg.STCE`;
  - the guest controls read back as `BE_B6:04 GUEST_CONTROLS_CHECKED
    hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2
    fs=0x0 vs=0x0 vstimecmp=0xffffffffffffffff`. K3 reads back `0xb15c`
    for the `0xb15d` written: cause 0 is read-only zero;
  - B6 cleared the 64 MiB window (16.6 ms with GCC, 12.5 ms with Clang)
    and placed the kernel and DTB (0.58 to 0.63 ms);
  - the pinned Linux `v7.2` guest ran in VS mode. It printed
    `SBI implementation ID=0x4245 Version=0x2` and `riscv-timer: Timer
    interrupt in S-mode is available via sstc extension`. Its init
    printed `B6INIT 03 SLEEP requested_ms=1000 elapsed_ms=1000 ok=1` and
    `04 RESULT pass`, then powered off;
  - the monitor reported `exits=130` (14 Base, 82 DBCN writes, 33 DBCN
    reads, and the SRST shutdown; `time=0`, `refused=0`) and requested
    its SRST shutdown. The guest ran 1.408 s from first entry to its
    shutdown request;
  - printk times and tick counts aside, the monitor and guest lines were
    identical in all five runs, with one exception: the Clang run's guest
    measured unaligned word access at 5.23x byte access, the GCC runs'
    at 4.94x. The shim's line differed only in the FDT address: U-Boot's
    in the U-Boot run, the kexec loader's `0x1_0820_0000` in the others.
- **The stopped run** (GCC, kexec, images built at `50a75654`) ended at
  `BE_B6:FAIL controls` after `BE_B6:03`, before any guest entry: the
  controls check failed closed.
- **In QEMU 10.2.2** with OpenSBI v1.6 (emulation):
  - the plan's 12 scenarios and 17 runs behave as planned: `k3-like`,
    `rva23`, and `plic` pass for GCC and Clang; `no-sstc` and `sbi-3.0`
    fail with `sstc` and `boot`; `sbi-time` passes with `time` above 0;
    and the six negative variants fail with their planned classes;
  - the U-Boot v2022.10 `booti` rehearsal of the `k3-address` image and
    the kexec rehearsal of both board images pass;
  - the reference boot, with no monitor, reaches `RESULT pass`.
- **Host:** the pure-C cores pass with identical GCC and Clang output:
  the G-stage in 12 scenarios and 16,590 assertions, the payload checks
  in 8 and 451, and the SBI core in 23 and 7,853.
- **Images:** every plan budget holds, and the image checker's rules and
  35-defect mutation test pass for both toolchains:
  - monitor text ends at `0x1_0200_6490` (GCC) and `0x1_0200_6e30`
    (Clang), below `0x1_0200_8000`;
  - data and BSS end at `0x1_0200_ada8` and `0x1_0200_ac88`, below
    `0x1_0200_f000`;
  - the flat image is exactly `0x34000` bytes, and the pool `0x8000`;
  - the kernel file is 1,553,332 bytes with `image_size` `0x1af628`; the
    DTB is 4 KiB; the boot image is `0x1b2000` bytes.
- **Guest inputs:** the init, `Image`, and DTBs match their pins, and a
  second build reproduced all 8 outputs byte for byte.

**Trusted or assumed:**

- The firmware below HS: the BSP's OpenSBI 1.6, which prints no banner
  on this board, its trap delegation, and its `menvcfg.STCE` setting. The
  `henvcfg.STCE` readback and the guest's Sstc timer line show that Sstc
  reaches VS.
- The loaders: Fedora's `kexec_load` and the BSP U-Boot's `loady` and
  `booti`. The preflight's reading of `/proc/iomem` and the FDT
  reservations.
- Linux `v7.2` is a test payload. The monitor does not trust it, and B6
  claims nothing about it beyond the lines it printed.
- This workstation's unpinned tools, as in B2-B5: GCC 16.2.1 (host and
  riscv64 cross), binutils 2.46.1, clang/lld 22.1.8, QEMU 10.2.2, and
  Python 3.14.7. The guest pins hold for this cross toolchain.
- The accepted R1-R3 code as ported by B2, and B1's quiesce and B3's
  shim, all reused unchanged.
- The B6 monitor layer has no proof. Its evidence is host tests, the
  image checker, QEMU, and the board runs.

**Not run or unavailable:**

- R6/R7-style adversarial or proof work for B6: not applicable, as the
  plan states. B6 links none of the R5 switch those concern, and it adds
  unproven privileged assembly.
- The negative variants and `sbi-time` on the board: QEMU only, as
  planned.
- A Clang U-Boot run: not planned (Q2 is one GCC run).
- A hash of the bytes U-Boot received: no `crc32` was run, and the
  transfer most likely used YMODEM's 8-bit checksum.
- U-Boot's watchdog more than about 17 s after the U-Boot run's halt.
- A WARL `hedeleg` reading other than `0xb15d` in QEMU, which makes
  these bits writable. The reduced readings are exercised by the host
  test and the marker self-test, and K3 gave `0xb15c`.
- Any second hart, device, interrupt controller, MMIO, DMA, or guest FP
  or vector state.

**Explicitly not claimed:**

- Hardware validation, qualification, or formal verification.
- A development-kernel or BSP selection. The Linux `Image` is a test
  payload.
- An SBI profile, guest ABI, hypercall ABI, or Linux interface, or
  OpenSBI as the long-term firmware boundary.
- Isolation beyond the G-stage window. The protected root is built and
  re-walked but never entered.
- Any R6, R7, or R8 claim for B6 code. QEMU, Model, Helium, R-series, and
  B0-B5 claims do not transfer.

## 4. Load-bearing invariants

| Property | Contract and implementation | Test or evidence |
| --- | --- | --- |
| Accepted bytes unchanged | A port of B2 with five counted rules; every other accepted file reused unchanged | `scripts/port.py --check` re-derives the port byte for byte (5 rules, 7 substitutions, B2's manifest); the image checker requires the three R3 functions byte-identical to B2's and all 57 accepted R5 linker conjuncts |
| The guest maps only its window | `src/b6-gstage.c`: 32 leaves of 2 MiB, GPA `0x8000_0000`-`0x83ff_ffff` onto HPA `0x1_1000_0000`-`0x1_13ff_ffff`, and nothing else. An independent walker re-derives the window from the pool bytes before `hgatp` changes | Host test, including every single-bit flip of every nonzero entry; `BE_B6:01` on the board; QEMU `memory` variant (`guest-page-fault` above the window) |
| The window is free memory | The monitor image, pool, staging region, kexec FDT slot, and window are pairwise disjoint; the loader refuses any `/proc/iomem` child or FDT reservation in the staging region or the window | Static `ASSERT`s; the image checker; the loader host test; preflight `region_check=PASS` |
| `hgatp` changes only in accepted code | A second call to the accepted install function; no other `hgatp` write or `hfence.gvma` | Image checker: two install call sites, both in boot code; mutation test |
| No guest request reaches M-mode | The SBI subset is emulated in HS; the only `ecall` is the accepted `be_r3_arch_sbi_call`, reached only from the accepted platform helpers | Image checker: one `ecall` site and its callers; host tests of every SBI row and the research call census; `refused=0` on the board |
| DBCN reads only the window | The whole range `[a1, a1 + a0)` must lie in the walked window and the high word must be 0; at most 256 bytes are copied into a monitor buffer | Host tests at every window edge |
| The guest cannot forge monitor lines | HS prefixes `BE_B6_GUEST: `, drops CR, maps every other byte outside `0x20`-`0x7e` but LF to `?`, and ends an open guest line before its own | Host tests; the marker checker rejects a tag inside a guest line and any untagged line |
| HS takes no interrupt | `sie`, `sstatus.SIE`, `hvip`, and `hgeie` stay 0; the guest's timer comes from Sstc through `hideleg` VSTI | Arm and resume checks; the image checker's CSR-writer table; `time=0` and the Sstc line on the board |
| Controls fail closed | `henvcfg.STCE` readback; every control read back at arming, with `hedeleg` within `0xb15d` and holding `0xb10c`; the resume tail rechecks each, `hedeleg` against the armed readback | QEMU `no-sstc` (`FAIL sstc`); host test (eight WARL readings, eleven refusals, every single-bit flip); image checker constant tracking and mutations; the stopped board run |
| Every other exit is terminal | Only a VS `ecall` resumes; every other exit prints its class and a `DETAIL` line, then requests the SRST shutdown | QEMU `memory`, `rdcycle`, and `init-exit` variants |
| Bounded run | An exit ceiling of 2^20 and a guest-time budget of 2^32 ticks | QEMU `exit-budget` and `guest-timeout` variants |
| Payload shape checked before the window | Kernel and DTB headers against link-time constants; the whole window zeroed; both copies compared; one `fence.i` | Host payload test; QEMU `payload` variant; the image checker's payload constants |
| Images within budget | Text, data, flat image, pool, kernel, DTB, and boot-image limits | Image checker; the measured budgets in section 3 |
| Guest inputs pinned | The Linux commit and tag object, the RPMs, and the build identity and timestamps are fixed | `guest-pin-check`; `kernel-repro` (8 of 8 outputs identical) |

## 5. Review history and resolved findings

The scope-review, different-model evaluation, and deep security-review
SOPs are dropped for this repository; no independent review ran. Every
worker used the pinned model.

1. **Workers.** All three workers died in a DNS outage. Each was
   restarted from its committed state and backed-up drafts, and
   finished. Their branches, `beryllium/k3-b6-guest-wip` (`f514a038`),
   `beryllium/k3-b6-core-wip` (`ffef36e1`), and
   `beryllium/k3-b6-tools-wip` (`2d038bd7`), are local.
2. **Worker fixes before integration:**
   - `2d038bd7`: under `--sbi-time`, the marker checker no longer
     requires the Sstc timer line, which a guest whose DTB lacks `sstc`
     cannot print. This was found when the tools were tried on the core
     worker's images.
   - `49c3c1dd`: one `K3_RUN_ROOT` collects all the kexec runs, for B0's
     retention tool.
   - `ffef36e1`: unused code dropped from the image checker; its results
     are unchanged.
3. **Implementation choices beyond the plan's text:**
   - A failed window-clear or placement readback is classed `boot`, as
     B5's guest-RAM clear is. The plan's class list does not name it.
   - Arming also requires Bare `vsatp`. As planned, the resume tail does
     not check `vsatp`.
   - The guest's SRST reboot and failure requests print a `DETAIL` line,
     since they are decided on an exit.
   - lld marks the empty NOLOAD pool section `A`, and GNU ld `WA`. The
     pool segment is RW for both, and the checker requires no X.
   - `k3-run.sh` checks the image before staging, refuses a `/tmp` that
     is not a tmpfs, and checks the image, loader, and layout-header
     hashes on the board.
4. **Estimates and limits.** Clang monitor text, `0x6e30`, is above the
   plan's inferred `0x68b0`-`0x6bb0`; it was `0x6b60` before the WARL
   change. Data and BSS grew by `0x410` (GCC) and `0x388` (Clang) over
   B5's, above the plan's estimate of under `0x200`. Every hard limit
   holds.
5. **The board stop (closed by your direction).** The first board run,
   GCC through kexec (`20261008T105807Z`, images built at `50a75654`),
   stopped at `BE_B6:FAIL controls` after `BE_B6:03`: stop condition 6.
   - The read-only diagnosis: the accepted R3 reset zeroes the other
     controls, and B5's identical `vstimecmp`/`hip` sequence passed on the
     board. The new control was `hedeleg`, checked by exact readback.
     The privileged specification lets bit 0 be read-only zero when
     IALIGN=16, and K3 has C. QEMU makes these bits writable, so every
     rehearsal read back `0xb15d`.
   - You chose `fix-warl` from the four options offered. `1a6ab933` still
     writes `0xb15d`. Arming accepts a readback within `0xb15d` that
     holds causes 2, 3, 8, 12, 13, and 15, and the resume tail checks
     that armed readback. `BE_B6:04` prints the readback, and a controls
     failure after arming prints two `BE_B6:DETAIL controls` lines with
     every readback. The stopped run printed no such line; that monitor
     had none.
   - `make check` and the kexec rehearsal passed again before the next
     board step. All five later runs read `hedeleg=0xb15c`, which differs
     from `0xb15d` only in bit 0, and every other control check passed
     unchanged.
6. **The U-Boot run (closed, with limits).**
   - The keystroke slip: on the first try, the session script's
     `tmux send-keys` lacked tmux's `--`, so tmux took the leading `--`
     of the sz arguments as an option and typed nothing. picocom then ran
     sz with no file, and nothing reached the board. The script resent
     the arguments with `--` about 33 s later, while U-Boot still waited,
     and the transfer completed. The fix is in the session script, which
     is not committed; the README's procedure shows the `--`.
   - The transfer began only after 14 of U-Boot's waits, so it most
     likely used YMODEM's 8-bit checksum rather than CRC-16. No `crc32`
     was run. The `## Total Size` line matched the file, the monitor's
     payload checks passed, and the output matched the GCC kexec runs,
     whose staged copies were hash-checked on the board.
   - The human powered the board off about 20-23 s after the halt, 17 s
     into the run tool's 75 s watch. The watch recorded `after_reset=no`
     and 320 bytes of power-off noise, so it covered only about 17 s.
7. **Excerpt whitespace.** U-Boot ends one line with a space; the
   retained excerpt keeps the board's bytes, as B3's and B5's do, so
   `git diff --check` reports it.

Open for your judgment:

- The WARL `hedeleg` change as implemented. On K3, cause 0 stays with
  HS, so such a trap would end the run as `exception`. Inference: with C
  present, an instruction-address-misaligned trap should not arise.
- The U-Boot run's limits: no hash of the received bytes, and a watchdog
  watch of about 17 s.
- The implementation choices in item 3.
- The provisional, unregistered SBI implementation ID `0x4245`, now
  version 2.

## 6. Validation and retained evidence

**At the exact commit**, in a clean clone (2026-10-08T12:11:26Z to
12:22:44Z), with no `git status --porcelain` line before or after. Two
overrides applied: `LINUX_GIT` named a local Linux mirror, and
`B6_RPM_CACHE` named B3's cached copies of the pinned `m4`, `bison`, and
`flex` RPMs. The fetch and build scripts check the pinned commit, tag
object, and RPM hashes either way.

- `make -C bringup/k3-b6 check`: PASS in 424 s. It cloned and built
  OpenSBI v1.6 and U-Boot v2022.10 (`u-boot.bin` `d96d1c22…`) itself.
  - Guest: Linux `v7.2` at the pinned commit and tag object; the kernel
    built, and all 8 outputs match their pins.
  - Port: 5 rules, 7 substitutions, B2's manifest matched.
  - Host tests: G-stage 12 scenarios and 16,590 assertions, payload 8
    and 451, SBI 23 and 7,853; GCC = Clang.
  - Images: GCC and Clang, the seven variants, the four DTB variants, and
    the three `booti` images pass the image checker; the mutation test
    rejects all 35 defects.
  - Reference boot: `RESULT pass` (`elapsed_ms=1000`).
  - Checkers: the marker self-test passes 263 cases, and the sources
    check finds all 27 lines; the capture self-test passes 101 cases; the
    board-tool dry run passes.
  - QEMU: `BE_K3_B6_QEMU: PASS scenarios=12 runs=17`, and the U-Boot
    rehearsal of the `k3-address` image passes.
- `make -C bringup/k3-b6 kexec-rehearsal`, with B0's GCC rehearsal kernel
  (`7.3.0-rc4-gc1c7e254143f`, `4871aa91…`): PASS for the GCC and Clang
  board images.
- `make -C bringup/k3-b6 kernel-repro`: PASS, 8 of 8 outputs identical.
- The rebuilt boot images equal the board images: GCC
  `b17036e7…cb97d4`, used in all four GCC runs, and Clang
  `e7f096dc…d12915`.
- The four kexec excerpts and the U-Boot excerpt pass
  `check-b6-capture.py` on their own. The stopped excerpt passes the
  marker checker as the expected `controls` failure, and fails the
  capture checker, which checks only for a pass, as expected.
- All three `MANIFEST.sha256` files match (`sha256sum -c`).

**Before the exact commit.** `e20c55df` changes no code after
`1a6ab933`: only the records under `results/`, the README, and the
planning and status documents.

- **At `1a6ab933`**, in the main checkout, after the WARL change:
  `make -C bringup/k3-b6 check` passed. That covered the host tests
  (`sbi` now 7,853 assertions), the image checks (35 mutations per
  toolchain), the marker self-test (263 cases), the capture self-test
  (101 cases), QEMU (12 scenarios, 17 runs), and the U-Boot rehearsal.
  The kexec rehearsal passed for both new board images. QEMU reads back
  `hedeleg=0xb15d`.
- **At `50a75654`**, in the main checkout, from a fresh build:
  - `make -C bringup/k3-b6 check` passed in 9 min 27 s: guest pins, the
    port (5 rules, 7 substitutions), host tests with identical GCC and
    Clang output, image checks with 35 mutations per toolchain, the
    reference boot, QEMU (12 scenarios, 17 runs), and the U-Boot
    rehearsal;
  - the kexec rehearsal passed for GCC and Clang, with B0's rehearsal
    kernel `7.3.0-rc4-gc1c7e254143f` (`4871aa91…edef`);
  - `make -C bringup/k3-b6 kernel-repro` gave 8 of 8 outputs identical.
- **A clean clone of `50a75654`**, with the upstream defaults: Linux from
  git.kernel.org, `dnf download` of the pinned `m4`, `bison`, and `flex`
  RPMs, and fresh clones of OpenSBI v1.6 and U-Boot v2022.10.
  - The first `make check` stopped when a network drop broke the Linux
    fetch (`curl 56 ... Network is unreachable`). The fetch script failed
    closed.
  - The kexec rehearsal then fetched, built, and passed, and a rerun of
    `make check` passed.
  - The boot images were byte-identical to the main checkout's.

**On the board**, 2026-10-08 (UTC):

- Before the change: preflight PASS at 10:57:07, GCC and Clang load
  checks, and the stopped run `20261008T105807Z` (`check_status=1`).
- After the change: preflight PASS at 11:18:53, with `sstc` on hart 0 and
  on 8 of 8 harts, a 24 MHz timebase, `kexec_load` available, a tmpfs
  `/tmp`, and the staging region and window free. Then GCC and Clang
  load checks (image at `0x1_0800_0000`, 41,088-byte FDT at
  `0x1_0820_0000`, `kexec_loaded=1`, then unloaded).
- Kexec runs `20261008T111923Z`, `20261008T112259Z`, and
  `20261008T112436Z` (GCC) and `20261008T112748Z` (Clang): each
  `check_status=0`, in 4 distinct boots, with a human reset after each.
- U-Boot run `20261008T113140Z` (GCC): `check_status=0`. YMODEM moved
  1,777,664 bytes in about 3.5 minutes, about 8.5 KB/s.

**Retained** under `bringup/k3-b6/results/`, by B0's unchanged
`retain-results.py`:

- `20261008-com260/`: the four kexec runs, the post-change preflight,
  and its two load checks;
- `20261008-com260-uboot/`: the U-Boot run;
- `20261008-com260-stopped/`: the stopped run, its preflight, and its two
  load checks.

Each run keeps `run.txt`, `load.txt`, `check.txt`, `result.json`, and a
handoff excerpt. Each directory has `summary.md`, `captures.txt`,
`originals.sha256`, `MANIFEST.sha256`, and a README. The full serial
captures hold the board's machine ID or TLV identity lines, so they are
kept privately.

## 7. Recommended review sequence

1. Claims: section 3 above, then `bringup/k3-b6/README.md` (design,
   budgets, tests, K3 results) and the three results READMEs.
2. The directions: the plan's decision record, then the WARL change in
   `src/`.
3. The monitor layer: `src/b6-trap.S` (arm helpers, exit vector, resume
   tail), then `src/b6-runtime.c` (sequence, G-stage install, controls,
   payload, entry, dispatch), `src/b6-gstage.c`, `src/b6-payload.c`,
   `src/b6-sbi.c`, `src/b6.h`, and `src/b6-layout.h`.
4. The port and the boot image: `scripts/port.py`, `src/b6-boot.lds`,
   and `src/b6-guest-payload.S`.
5. The guest inputs: `guest/` (configuration, init, device tree),
   `scripts/fetch-linux.sh`, `scripts/build-guest.sh`, and
   `guest/pins.txt`.
6. The checkers: `tests/check-b6-image.py`, `tests/check-b6-markers.py`,
   and `tests/check-b6-capture.py`.
7. The board tools: `scripts/kexec-load.py`, `scripts/k3-run.sh`,
   `scripts/k3-preflight.sh`, and `scripts/k3-uboot-run.sh`.
8. The board records.

Read-only commands:

```sh
git --no-pager log --oneline 6b4d165b..e20c55df
git --no-pager diff --stat 6b4d165b..e20c55df -- . ':!bringup/k3-b6/results'
git --no-pager diff 50a75654 1a6ab933 -- bringup/k3-b6/src
git --no-pager show e20c55df:bringup/k3-b6/results/20261008-com260/README.md
git --no-pager show e20c55df:bringup/k3-b6/src/b6-trap.S
```

Exact-commit execution in a fresh worktree. `check` fetches Linux `v7.2`
(or takes `LINUX_GIT`, a local mirror), downloads the pinned RPMs unless
`B6_RPM_CACHE` names them, and clones and builds OpenSBI v1.6 and U-Boot
v2022.10, so it needs network access. The kexec rehearsal needs B0's GCC
rehearsal kernel:

```sh
git worktree add --detach ../be-b6-review e20c55df57551244eab47e0eff59d4c71fe75d20
cd ../be-b6-review
make -C bringup/k3-b6 check
make -C bringup/k3-b6 kexec-rehearsal REHEARSAL_KERNEL=<B0 GCC rehearsal Image>
make -C bringup/k3-b6 kernel-repro
cd - && git worktree remove --force ../be-b6-review
```

## 8. Human decision checklist

The checklist is kept as presented. The decision is recorded in the
[decision record](#decision-record), not in these boxes.

- [ ] B6 matches the accepted plan and its two later directions: an
      unmodified pinned Linux `v7.2` guest, uniprocessor without FP or
      vector, on the accepted R3 prelude, under a B6-owned G-stage over
      64 MiB, with a device tree naming no device, B5's SBI subset with
      the planned changes, and RAM-only COM260 runs.
- [ ] The monitor layer is correct, and the guest cannot reach M-mode,
      map memory outside its window, or forge monitor lines.
- [ ] The WARL `hedeleg` change matches your `fix-warl` direction and
      nothing more.
- [ ] The implementation choices and the U-Boot run's limits in section 5
      are acceptable.
- [ ] The claims in section 3 match the evidence, including the stopped
      run.
- [ ] Unpinned workstation tools, the external Linux input, and no proof
      for the B6 layer are acceptable for this bring-up milestone.
- [ ] Successor work, including the merge into the development branch,
      remains excluded until separately directed.
- [ ] Decision: accept exact commit `e20c55df`, request revisions, or
      defer.

## 9. After the decision

- **Accept:** record acceptance of exact SHA
  `e20c55df57551244eab47e0eff59d4c71fe75d20` with its date and
  instruction in a follow-up record. Acceptance would not start any
  successor; push, tag, publish, or release; merge B6 into the
  development branch; select a development kernel or BSP; or integrate
  with the root `Makefile`, `be`, or `scripts/check-be.sh`. Each still
  needs your direction.
- **Request revisions:** make a new commit and a new packet. `e20c55df`
  is not treated as accepted.
- **Defer:** keep the current status and start no dependent work.

**Status:** exact commit `e20c55df` is responsible-human accepted as of
2026-10-08. After one stop and your `fix-warl` direction, the Linux guest
ran to its shutdown in 5 of 5 RAM-only COM260 runs.

**Next:** a successor needs your direction. Candidates include merging B6
into the development branch and pushing it, and a next step under a new
bounded plan. None is started or authorized.

**Action required from you:** none for B6.
