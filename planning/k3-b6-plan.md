<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B6 plan: a uniprocessor Linux guest on the COM260

## Decision record

The responsible human accepted this plan at exact commit
`e34ef378b6279300ba5f3aeb8b6102941b432454` (parent
`3bc3ef04e4d9a7d541e6e1ab74ccfd5a8b267e69`) on 2026-10-08. The
instruction, given in reply to the request below to accept, revise, or
defer that exact commit, was `accept e34ef378`, which resolves uniquely to
that commit.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted; only this section
  and the status line below were added afterwards.
- **Authorized:** B6 implementation under this plan, work packages B6-1 to
  B6-6:
  - new code and tests under `bringup/k3-b6/`;
  - fetching and building the pinned upstream Linux `v7.2` as an external
    guest input;
  - the read-only Fedora preflight;
  - the QEMU rehearsals;
  - RAM-only COM260 runs through Linux kexec, plus the optional U-Boot
    run;
  - ending in one result review packet.

  Each [stop condition](#stop-conditions) returns B6 to the responsible
  human.
- **Open questions:** none was answered, so the defaults apply:
  - Q1: 64 MiB of guest RAM.
  - Q2: one extra GCC board run through U-Boot `booti`, without `unzip`.
  - Q3: `flex` and `bison` through B3's pinned Fedora 44 RPM method, with
    no workstation change.
  - Q4: Linux `v7.2` at `8d3ae59288f1e7d58d76558a6ee96d533bc5019f`.
  - Q5: `hedeleg` `0xb15d`.
  - Q6: the `BE_B6:`, `BE_B6_GUEST: `, and `B6INIT` identifiers, the DT
    model and compatible, and SBI implementation ID `0x4245`, version 2.
  - Q7: no board DTB without `sstc`; that stays a stop.
- **Not authorized:** everything the plan excludes, including:
  - SMP or a second guest;
  - devices, MMIO, interrupt controllers, or DMA;
  - guest FP or vector;
  - a development-kernel/BSP selection, or any change to the board's host
    kernel;
  - a change to any accepted R0-R7 byte, retained R8 input, or accepted
    B0-B5 file;
  - root `Makefile`, `be`, or `scripts/check-be.sh` integration;
  - a new HS-to-M SBI call;
  - any persistent firmware, U-Boot environment, flash,
    boot-configuration, or storage change; TFTP loading; or a staged-NVMe
    U-Boot `load`;
  - push, tag, publication, release, or any successor.
- **Evidence status:** acceptance adds no implementation, emulation, or
  board evidence. No B6 implementation has started.

### Direction after a stop: `hedeleg` is WARL (2026-10-08)

The first board run stopped at `BE_B6:FAIL controls`, which is stop
condition 6. This was GCC board run 1 through kexec, record
`20261008T105807Z`, at implementation commit `50a75654`. The capture ends
`BE_B6:03`, then the failure, before any guest entry. The read-only
diagnosis:

- The accepted R3 reset zeroes the other controls, and B5's identical
  `vstimecmp`/`hip` sequence passed on the board.
- The new control is `hedeleg` = `0xb15d`, which B6 checked by exact
  readback. The privileged specification lets bit 0 be read-only zero when
  IALIGN=16, and K3 has C. Fedora reports that K3 performs unaligned
  accesses in hardware. QEMU makes these bits writable.

The responsible human chose `fix-warl` from the offered options. This
narrow change to the plan text below applies to B6 only:

- B6 still writes `0xb15d`, but reads it back as WARL. Causes 0, 4, and 6
  may read zero. Causes 2, 3, 8, 12, 13, and 15 must read set, and no
  other bit may appear.
- The resume tail checks `hedeleg` against the readback checked at arming,
  not the constant.
- `BE_B6:04` prints the actual readback, and the marker checker accepts
  any WARL reading in place of the plan's `hedeleg=0xb15d`.
- A controls failure after arming adds two `BE_B6:DETAIL controls` lines
  with every readback.
- B6 then reruns `make check` and the kexec rehearsal before any further
  board run.

Nothing else in the plan changes.

### Direction during B6-5: automation may type at U-Boot (2026-10-08)

During B6-5, at 13:23 CEST (11:23Z) on 2026-10-08, before the U-Boot run,
the responsible human wrote: `you can also operate the u-boot console by
attaching to picocom session`.

This direction changes two rules, for B6 only:

- [Board safety](#board-safety): for the optional U-Boot run, automation
  may type the U-Boot commands and start the YMODEM transfer in the
  operator's picocom session. The plan had the human do both. The run tool
  still only reads the picocom log, and B3's 75 s post-halt watch stays.
  The same change applies where Q2 and the U-Boot row of
  [Load paths](#load-paths) say the human types.
- [Stop condition 9](#stop-conditions): needing automation to type at
  U-Boot is no longer a stop. The rest of stop 9 stays: any firmware,
  U-Boot environment, flash, boot-configuration, or storage write, TFTP,
  or staged-NVMe `load` is still a stop.

How it was carried out:

- The human restarted picocom inside tmux session `k3serial`, logging to a
  new file.
- Automation used `tmux send-keys` to send only:
  - `s`, to stop autoboot;
  - Ctrl-C, to clear the line;
  - the RAM-only operator line
    `loady 0x140000000 && booti 0x140000000 - ${fdtcontroladdr}`, then
    Enter;
  - picocom's C-a C-s, to open its send-file prompt;
  - the sz arguments `--ymodem -k <image>`, then Enter.
- Automation never sent `saveenv`, `env save`, or any flash or firmware
  command.
- The human kept every reset and the power-off. The power-off came about
  20-23 s after the run's halt, 17 s into the run tool's 75 s watch, so
  the watch covered only about 17 s (`after_reset=no`).
- One slip: on the first try, tmux took the leading `--` of the sz
  arguments as an option and did not send them. The Enter that followed
  made picocom run sz with no file, so nothing reached the board.
  Automation sent the arguments again, correctly, while U-Boot was still
  waiting, and the transfer completed.

Nothing else in the plan changes.

## Decision requested

**Status:** accepted on 2026-10-08; see the [decision record](#decision-record).
As presented, the plan was proposed and not accepted, and no B6
implementation had started: `bringup/k3-b6/` did not exist, and nothing had
been built or run for B6. The research builds and QEMU runs cited below are
planning research only, not B6 evidence.

After B5's acceptance on 2026-10-07 the responsible human asked to
"summarize project status & plan". The summary recommended, as step 2, "a
B6 plan: a bounded step toward a real OS guest (more guest RAM through
B6-owned G-stage tables, a guest device tree, a larger guest such as a
small OS), then QEMU rehearsal and RAM-only COM260 runs". The human replied
`proceed with (1) then (2)`. Step (1), merging B5 into the development
branch and pushing it, is done. Step (2) is this plan; that instruction
authorizes drafting only.

The responsible human is asked to decide on the exact commit that adds this
plan on branch `beryllium/k3-b6-bringup` (parent: development branch tip
`3bc3ef04e4d9a7d541e6e1ab74ccfd5a8b267e69`):

- **Accept:** authorizes B6 implementation under this plan, work packages
  B6-1 to B6-6: new code and tests under `bringup/k3-b6/`; fetching and
  building the pinned upstream Linux as an external guest input; a
  read-only Fedora preflight; QEMU rehearsals; and RAM-only COM260 runs
  through Linux kexec, plus the optional U-Boot run (Q2). It ends in one
  result review packet.
- **Request revisions** or **defer:** B6 stays unstarted.

Acceptance would not authorize:

- SMP or a second guest; devices, MMIO, interrupt controllers, or DMA; or
  FP or vector state for the guest;
- a development-kernel/BSP selection, or any change to the board's host
  kernel;
- a change to any accepted R0-R7 byte, retained R8 input, or accepted
  B0-B5 file, or root `Makefile`, `be`, or `scripts/check-be.sh`
  integration;
- a new HS-to-M SBI call;
- any persistent firmware, U-Boot environment, flash, boot-configuration,
  or storage change; TFTP loading; or a staged-NVMe U-Boot `load`;
- push, tag, publication, release, or any successor.

### Open questions

Each has a default, so acceptance can proceed without answers.

| # | Question | Default if unanswered |
| --- | --- | --- |
| Q1 | Guest RAM size? | 64 MiB. 128 MiB at the same bases is a one-constant change (64 leaves; DTB at GPA `0x87e0_0000`) |
| Q2 | Add one GCC board run through U-Boot `booti`, typed by the human, to show the second loader runs the same bytes? | Yes, without `unzip`. YMODEM moves about 6.2 KB/s, so the transfer takes about 5-6 minutes. "Yes, with `unzip`" lets the operator send a gzip copy and expand it with U-Boot's RAM-only `unzip` (about 2.5 minutes) |
| Q3 | The kernel build needs `flex` and `bison`, which this workstation lacks (`bc`, `perl`, and `gzip` are present). How are they provided? | B3's accepted method, with no workstation change: the system's tools when present, otherwise the same pinned Fedora 44 RPMs (`m4`, `bison`, `flex`, each with NEVRA and SHA-256), downloaded with `dnf download`, checked, and unpacked under `build/` (`bringup/k3-b3/tests/build-uboot.sh:50-57,65-80,101-116`). The alternative is for you to install the Fedora packages `flex` and `bison`. The research container wrapper stays research-only |
| Q4 | Kernel source? | Upstream `v7.2`: commit `8d3ae59288f1e7d58d76558a6ee96d533bc5019f`, annotated tag object `237a1c39e8dfd3e1c6f1f023eea37a48ec04cc63` ("Linux 7.2", 2026-08-16). The LTS `v6.18` (`7d0a66e4bb9081d75c82ec4957c50034cb0ea449`) is a recorded fallback, used only on your direction |
| Q5 | `hedeleg`? | `0xb15d`: KVM's set plus misaligned load and store (4, 6), so a residue OpenSBI cannot emulate reaches the guest. KVM's `0xb10d` (`arch/riscv/kvm/vcpu_config.c:9-15@v7.2`) would make that residue terminal |
| Q6 | Identifiers: `BE_B6:` (monitor lines), `BE_B6_GUEST: ` (guest lines), `B6INIT` (init lines), DT model "Beryllium K3 B6 guest" and compatible "beryllium,k3-b6-guest", and SBI implementation ID `0x4245` with version 2? | Yes; all B6-only and unregistered. Version 2, not B5's 1, because guest-visible behaviour changes (reboot requests become terminal; DBCN checks the window, not B5's pages), and the version is the only Base answer that tells the two apart in a capture |
| Q7 | If the guest's own VS-mode `stimecmp` writes fail on the board, may B6 continue with a board DTB without `sstc`, so Linux uses SBI TIME through the monitor (rehearsed in QEMU as `sbi-time`)? | No: it stays a [stop](#stop-conditions) |

## Goal and pass criterion

B6 runs an unmodified upstream Linux kernel, built uniprocessor from a
pinned commit, as the only guest on the COM260: VS mode on hart 0, inside a
B6-owned G-stage that maps 64 MiB of RAM, with a device tree that names no
device and B5's SBI subset. An in-tree init sleeps on the guest's own Sstc
timer and powers off. B6 passes when every required line in
[Markers](#markers) appears in order, ending with the init's `RESULT pass`
and the monitor's `SHUTDOWN` line, and no rejected pattern appears, in the
QEMU rehearsals and in three GCC and one Clang RAM-only COM260 runs through
Linux kexec.

## Base and inputs

- **Base:** development branch `beryllium/single-hart-runtime-r0` at
  `3bc3ef04`, holding accepted B0-B5 and the accepted-tool fixes.
- **Reused unchanged:** B2's `scripts/port.py` (accepted `898af4e0`) and
  its pinned output; B1's `src/b1-handoff.S`; B3's `src/b3-shim.S`; B0's
  `tests/retain-results.py`, `tests/summarize-runs.py`, and rehearsal
  `mkcpio.py`. Counted copies are listed under
  [Tests and evidence](#tests-and-evidence).
- **External input, never committed:** Linux `v7.2` (GPL-2.0) source,
  fetched by B6, and the `Image` built from it: a test guest payload,
  **not** a development-kernel/BSP selection for the board, which stays
  undecided and unauthorized (`planning/roadmap.md:475`).
- **Platform facts:** 8 X100 harts with H, Sstc, and Svade (not Svadu);
  `sstc` on all 8, a 24 MHz timebase, and Sv39 only
  (`bringup/k3-b5/results/20261007-com260/preflight.txt:6-24`); 8 GiB of
  DRAM at `0x1_0000_0000`, OpenSBI 1.6 in its first 32 MiB, and S-mode RAM
  from `0x1_0200_0000`, also U-Boot's `booti` RAM base; Fedora `7.1.5`
  with `kexec_load`, no lockdown, a tmpfs `/tmp`, and the `/proc/iomem`
  map below (`bringup/k3-b0/results/20261006-com260/preflight.txt:6,11,18-38,58-62`).
  OpenSBI's SRST shutdown halts the board without powering it off.
- **Research:** two B6 research reports, written for this plan on
  2026-10-07 and kept outside the repository, are cited as "platform
  research §N" and "runtime research §N"; their scratch is under
  `build/k3-b6-research/` (gitignored). *Fact* marks what a cited file,
  record, or run shows, and *inference* marks reasoning from facts.
  Upstream Linux is cited as `path:line@v7.2`. Board results will be
  diagnostic bring-up evidence, never hardware validation.

## Architecture

### Option chosen: R3 through `BE_R3:06`, then a B6-owned root

| Option | Shape | Verdict |
| --- | --- | --- |
| **(i)** | The accepted R3 prelude through `BE_R3:06`; a B6 root installed by a second call to the accepted install function; Linux entered through B6's own tail | **Chosen** |
| (ii) | All of B5, then a loader guest asks HS to switch roots | Rejected: a root switch on the exit path, a private hand-off ABI, and two control regimes, for little new evidence; B5 already has 4 of 4 board runs of that path |
| (iii) | Bypass R3 | Rejected: loses the accepted R0-R3 chain and the R3 HS/VS reset check after the K3 hand-off |

The accepted install function is exactly `csrw hgatp, a0`;
`hfence.gvma zero, zero`; `csrr a0, hgatp`; `ret`
(`arch/riscv/be/privileged.S:203-218`). It is stateless, so a second call
with the B6 value is sound, and every `hgatp` write and `hfence.gvma`
stays in accepted code (runtime research §2.4-2.5). The accepted R3 code
stays byte-identical; R4/R5 are not linked; the protected root is built
and re-walked but never entered, as in B5.

### Boot sequence

1. A loader places the B6 boot image at L = `0x1_0800_0000` and enters its
   first byte with `a0` = hart and `a1` = FDT. B3's shim copies only the
   monitor's `0x34000`-byte flat image to `0x1_0200_0000`, runs `fence.i`,
   prints its `SHIM` line, and jumps there
   (`bringup/k3-b3/src/b3-shim.S:101-153`); `be_reset` calls B1's quiesce
   and then `be_b6_runtime_main`.
2. The accepted R3 sequence prints `BE_R3:01`-`:06`: boot contract, R1, R2
   build and re-walk, the HS/VS reset with B6's vector, the R3 check,
   binding, and the management `hgatp` install, fence, and publication.
3. B6 builds and independently re-walks its root (`BE_B6:01`), installs it
   with a second call to the accepted install function, and checks the
   readback (`BE_B6:02`); a refusal or mismatch is `BE_B6:FAIL gstage`.
4. B6 arms and reads back `henvcfg` (`BE_B6:03`) and the
   [guest controls](#guest-state-and-controls) (`BE_B6:04`), checks the
   payload's shape, zeroes the window (`BE_B6:05`), copies the kernel and
   the DTB (`BE_B6:06`), and runs `fence.i` once.
5. C fills the management saved page as the first-entry frame (`sepc`
   `0x8020_0000`, `a0` = 0, `a1` = the DTB GPA, other GPRs 0), prints
   `BE_B6:07`, and calls B6's resume tail, which checks every control and
   executes B6's one `sret`. The accepted `be_r3_arch_enter_management`
   zeroes `a1`, so it is not used; `BE_R3:07` is dropped, because no
   management entry happens.

### Port rules

As in B5, `scripts/port.py` checks B2's port with B2's own
`port.py --check` and pinned manifest, copies it into `build/k3-b6/port/`,
and applies only these rules, each with an exact count (runtime research
§2.5, §6.6); `--check` re-derives the tree byte for byte.

| Rule | Count |
| --- | --- |
| `r5-entry.S`: `call be_r5_runtime_main` becomes `call be_b6_runtime_main` | 1 |
| `r5-entry.S`: `tail be_r5_arch_halt` becomes `tail be_r3_arch_halt` | 1 |
| Linker script: `be_r5_trap_vector` becomes `be_b6_trap_vector` | 3 |
| Linker script: `PHDRS` gains a `b6_pool` entry | 1 block |
| Linker script: a NOLOAD `.gstage.root.b6` section at `0x1_0203_4000` (32 KiB, 16 KiB aligned) after the protected guest page, with its `ASSERT`s | 1 block |

Every other accepted `ASSERT` stays. The management fixture stays in its
page, unused, so B5's three fixture rules go. The link set is B5's (B2's
port without `r4.c`, `r5.c`, `r5-runtime.c`, and `r5-trap.S`, plus B1's
quiesce) with the B6 layer.

### Budgets

Every budget is hard; an overrun is a [stop](#stop-conditions).

| Budget | Limit | Basis |
| --- | --- | --- |
| Monitor text | Below `0x1_0200_8000` (accepted `ASSERT`) | B5: `0x5660` (GCC), `0x5c30` (Clang). Prototype: G-stage `0x354`/`0x3c0`, payload checks `0x28e`/`0x2c4` bytes. Inference: about `0x6250`-`0x6550` and `0x68b0`-`0x6bb0` (runtime research §7.3) |
| Monitor data and BSS | End at or below `0x1_0200_f000` (accepted `ASSERT`) | B5 ends at `0x1_0200_a998`; B6 adds under `0x200` |
| Flat image; pool | Exactly `0x34000` bytes at `0x1_0200_0000`; `0x8000` bytes at `0x1_0203_4000` | B2's six `PT_LOAD` segments; the NOLOAD pool (root `0x4000`, level-1 page `0x1000`, the rest zero) follows their end |
| Kernel `Image` | File at most 4 MiB; `image_size` at most 8 MiB | Research: 1,553,332 bytes, `image_size` `0x1af628` (platform research §1e-1f) |
| DTB; boot image | Exactly 4 KiB (`dtc -S 4096`); at most 4 MiB | Research DTBs: 769-1,299 bytes. Inference: boot image about 1.8 MB |
| Exits | Ceiling 2^20 | Fact: 139 SBI calls in the research reference boot (platform research §1c). Earlier inference: 250-450 (runtime research §4.5) |
| Guest time | 2^32 ticks after entry (179 s at 24 MHz) | The research guest powered off about 1.4 s after it started |

### Guest state and controls

B6 writes these after `BE_R3:06`, reads each back before entry, and checks
them again at every resume (runtime research §1.1).

| State | At the R3 check | During the guest run | Checked |
| --- | --- | --- | --- |
| `hstatus` under the R3 mask `0x73f380` | `0x700180` | `0x180` (SPV, SPVP). VTVM, VTW, and VTSR are cleared: Linux writes `satp`, runs `sfence.vma` and `sret`, and idles in `wfi` | Arm and resume |
| `hedeleg`, `hideleg` | 0, 0 | `0xb15d` (Q5: causes 0, 2, 3, 4, 6, 8, 12, 13, 15); `0x40` (VSTI only) | Arm and resume |
| `henvcfg` | 0 | STCE only; CBIE, CBCFE, CBZE, PBMTE, ADUE, and PMM stay 0 | Arm and resume |
| `hcounteren`, `htimedelta` | 0, 0 | `0x2` (TM only), 0 | Arm and resume |
| `vstimecmp` | Outside the R3 matrix | `~0` at arm, after which `hip` must read 0; then the guest's own | Arm |
| `hvip`, `hgeie`, `sie`, `sstatus.SIE`; `hie` | 0 | 0: HS takes and injects no interrupt; `hie` at most VSTIE, the guest's `vsie.STIE` | Arm and resume |
| HS `sstatus.FS`, `.VS` | Off | Off: the guest has no FP or vector. B6 adds VS (bits 9-10), which the R3 mask omits (`include/be/r3.h:77-80`) | Arm and resume |
| `hgatp` | Management root | B6 root `0x8000000000102034` (Sv39x4, VMID 0) | Readback and resume |
| `satp`, `stvec`, `sscratch` | 0, vector, 0 | 0, `be_b6_trap_vector`, trusted-stack top (a B6 arm helper) | Resume |
| `vs*`, including `vsatp` | 0 | Guest-owned; after the R3 reset HS writes only `vstimecmp` | Image check |
| `scounteren`, `senvcfg` | 0 | Not aliased in VS (runtime research §1.1), so guest writes reach the real CSRs. Linux writes `scounteren` = 2 (`arch/riscv/kernel/head.S:244-245@v7.2`) and never `senvcfg` under the [DT contract](#device-tree); HS runs no U-mode | No |
| `hstateen0`, `hvictl`, `hvien`, `hviprio1`/`2` | Outside the R3 matrix | Neither written nor read; the DT contract avoids every feature they gate | [Risk](#risks), [stop](#stop-conditions) |

A read-only diagnostic of `hstateen0` or `hvictl` is safe for the board
(the worst outcome is a terminal trap and a halt) but not for a pass run:
inference from the privileged specification is that with `mstateen0.SE0`
or `.AIA` clear the HS read returns as an illegal-instruction trap. So no
B6 image reads them; if a run stops on a gated CSR, such a read is the
first diagnostic step, with your agreement.

### Exits and resume

B5's vector, dispatch, and resume tail are adapted. The vector saves the
accepted 320-byte `struct be_r4_frame` (`include/be/r4.h:57`), then
`hstatus`, `htinst`, `vsatp`, and `time`; it requires `hstatus.SPV` = 1
and writes neither `hie` nor `hvip`. Every exit counts against the ceiling
and the guest-time budget. Only a VS `ecall` (cause 10) resumes, through
the SBI core; every other exit at HS is terminal with a `BE_B6:DETAIL`
line, classed as in [Markers](#markers). Access faults reach HS because
OpenSBI redirects them by `hedeleg`, which leaves them clear; an
unexpected `ecall`, such as a VU `ecall` (8), is `exception`. Fact:
OpenSBI v1.6 delegates causes 0, 3, 8, 12, 13, and 15 to S and redirects
2, 4, and 6 by `hedeleg` (runtime research §1.3; QEMU reports
`MEDELEG 0xf4b509`; the board's OpenSBI prints no banner), so the guest
takes its own page faults, system calls, breakpoints, illegal
instructions, and misaligned residue, as under KVM. The resume tail checks
the controls above, the B6 `hgatp`, and `sstatus` SIE, SPIE, XS, SUM, MXR,
FS, and VS all 0, but no longer `vsatp`; it returns to `sepc` + 4 with the
SBI result through one `sret`, writing no `vs*` CSR, `hgatp`, or fence.

## Memory and load paths

| HPA | Use | Basis |
| --- | --- | --- |
| `0x1_0000_0000`-`0x1_01ff_ffff` | OpenSBI 1.6, no-map | B0-B5 records |
| `0x1_0200_0000`-`0x1_0203_3fff`; `0x1_0203_4000`-`0x1_0203_bfff` | B6 monitor flat image (accepted layout); B6 G-stage pool (NOLOAD) | Copied by the shim; new |
| `0x1_0220_0000`-`0x1_05df_ffff` | Fedora's kernel, under kexec | B0 `preflight.txt:19-25` |
| L = `0x1_0800_0000`, then the kexec FDT copy at L + image rounded up to 2 MiB | Staging, the same for every loader; the FDT (at most 2 MiB) only under kexec | New |
| `0x1_1000_0000`-`0x1_13ff_ffff` | Guest RAM window, 64 MiB | New |
| `0x1_4000_0000` | U-Boot `loady` buffer | B3 and B5 records |
| `0x2_ee04_8000`-`0x2_ffff_ffff` | Fedora reservations; U-Boot's relocation, FDT copy, and framebuffer | B0 `preflight.txt:26-38`; platform research §3 |

Fact: no Fedora `/proc/iomem` child lies in
`0x1_05e0_0000`-`0x2_ee04_7fff`, and outside its own top reservation
U-Boot's `booti` path writes only the `loady` buffer, the move target, and
its FDT copy (platform research §3). Inference: staging and the window are
free under both loaders. The B6 preflight re-checks `/proc/iomem`.

### One boot image at a fixed address

The B6 boot image is a Linux RISC-V Image built from B3's shim source,
compiled unchanged with `BE_B3_TEXT_OFFSET` = `0x0600_0000`, and linked by
a counted copy of `b3-shim.lds`:

| Offset | Contents | Placed by |
| --- | --- | --- |
| `0x0` | Shim page: B3's header, descriptor, and stub | Runs in place |
| `0x1000` | The monitor flat image, exactly as linked at `0x1_0200_0000` (`0x34000` bytes) | The shim copies only this, to `0x1_0200_0000` |
| `0x35000` | Kernel `Image`, then the DTB, each 4 KiB aligned | Stays at L; the monitor copies it into the window |

The `.lds` copy adds a read-only guest section and its `PHDRS` entry
before `__be_b3_image_end` and replaces the image-size `ASSERT`
(`bringup/k3-b3/src/b3-shim.lds:66`) with guest `ASSERT`s; the payload
`ASSERT`s (`:64-65`) stay, and `image_size` covers the whole file, so
`booti` moves all of it. The monitor takes the payload's HPA and sizes
from link-time constants generated from the pinned payload. Static
`ASSERT`s and the image checker refuse any overlap among the monitor
image, the pool, the staged image, the kexec FDT slot, and the window.

A fixed staging address keeps the monitor small and clear of Fedora's
kernel at `0x1_0220_0000` and of the default `booti` shim location, and
lets both loaders run byte-identical bytes. Rejected: the payload inside
the monitor image (runtime research §3.2), which B0's kexec rule refuses
beside Fedora's kernel; and a kexec segment straight into the window
(platform research §2e), which U-Boot, placing one file, cannot match.

### Load paths

| Path | How the image reaches L | Operator | Status |
| --- | --- | --- | --- |
| **Linux `kexec_load`** from Fedora | A counted copy of B0's `kexec-load.py` raw mode loads the image at L and the host FDT after it, 2 MiB aligned, below the window. B0's other checks stay: page alignment, one System RAM range, no `/proc/iomem` child, no FDT reservation (`bringup/k3-b0/scripts/kexec-load.py:279-304`). The image starts with B3's header, not FDT magic, so Linux passes the FDT segment in `a1` (`arch/riscv/kernel/machine_kexec.c:52,60@v7.2`) | Automation stages and loads over SSH, as in B0-B2; the human only resets the board after each run | **Primary:** 3 GCC and 1 Clang runs |
| U-Boot `booti` | `text_offset` `0x0600_0000` places the image at `0x1_0200_0000` + `0x0600_0000` = L | The human types `loady` and `booti`; YMODEM takes about 5-6 minutes (`bringup/k3-b3/README.md:82-83`) | Optional (Q2): 1 GCC run |
| QEMU direct boot | The boot ELF, linked at L, is OpenSBI's next stage, as B5 boots its ELF | None | Rehearsal |

`unzip` is RAM-only and allowed only through Q2. TFTP and a staged-NVMe
`load` are not authorized (platform research §2c-2d).

### Guest-physical layout and payload checks

| GPA | HPA | Contents |
| --- | --- | --- |
| `0x8000_0000`-`0x801f_ffff` | `0x1_1000_0000` | Zeroed RAM; Linux may use it |
| `0x8020_0000` | `0x1_1020_0000` | Kernel `Image` (2 MiB aligned, matching `text_offset` `0x200000`), then its BSS span |
| `0x83e0_0000` | `0x1_13e0_0000` | DTB, at the start of the last 2 MiB |

The rest is zeroed RAM. Linux needs a 2 MiB-aligned kernel, `a0` = hart,
`a1` = DTB address, and `satp` = 0
(`Documentation/arch/riscv/boot.rst:26-27,34,46-48@v7.2`). Before it
touches the window, the monitor checks shape, not content, failing with
`BE_B6:FAIL payload`: the kernel's `magic`, `magic2`, `text_offset`
`0x200000`, little-endian flag, and an `image_size` at least the file size
that ends below the DTB slot
(`Documentation/arch/riscv/boot-image-header.rst:12-22@v7.2`); the DTB's
magic, 4 KiB `totalsize`, version 17, and block offsets; and the link-time
sizes. There is no runtime hash: the pins, the loaders' file checks, and
the pinned banner bind the content. It zeroes the whole window, copies the
kernel and the DTB, and prints the ticks each took. The monitor owns all
guest RAM; nothing a loader leaves in the window survives.

## G-stage

The accepted R2 builder cannot be reused: it fixes VPN[2] = 1, VPN[1] = 0,
4 KiB leaves, and three mappings, and rejects level-1 leaves
(`arch/riscv/be/sv39x4.c:48-52,224-227,337`). B6 adds its own builder and
an independent walker (runtime research §2).

- **Mapping:** GPA `0x8000_0000`-`0x83ff_ffff` linearly onto HPA
  `0x1_1000_0000`-`0x1_13ff_ffff`, as 32 leaves of 2 MiB (root index 2,
  level-1 indices 0-31); nothing else is mapped. The 16 KiB root is at
  `0x1_0203_4000` and the level-1 page at `+0x4000`; the rest of the pool
  stays zero; `hgatp` = `0x8000000000102034`.
- **Leaf bits:** V, R, W, X, U, A, D (`0xdf`); G, RSW, PBMT, and N are 0.
  A and D are pre-set because K3 has Svade, not Svadu. All RAM is RWX: the
  G-stage isolates the host, and the guest decides what is code.
- **Builder and walker:** the builder scrubs the pool first, also on
  refusal, and refuses a misaligned or zero size, a misaligned GPA or HPA,
  a 1 GiB crossing, a GPA at or above 2^41, and a window covering the pool.
  The walker shares only a byte loader with it, parses every root and
  level-1 entry and the spare pages, derives `(gpa, hpa, size)` from the
  bytes, and compares it with the descriptor before `hgatp` changes. DBCN
  translation uses the walked window.
- **Fences:** the accepted install function's `hfence.gvma zero, zero`; no
  `hfence.vvma`, since the guest starts with Bare `vsatp`, no VS-stage
  translation has run under VMID 0 on this boot, and the guest's own
  `sfence.vma` (VTVM = 0) covers it afterwards.

Fact (planning research, not B6 evidence): a prototype builder, walker, and
translation passed 8 scenarios and 15,106 assertions with identical GCC and
Clang output, in 852 and 960 bytes of text (runtime research, prototype).

## Guest SBI subset

B5's subset (`planning/k3-b5-plan.md`, Guest SBI subset) is kept with these
changes. It selects no SBI profile, guest ABI, or Linux interface.

| Item | B5 | B6 |
| --- | --- | --- |
| Base `get_impl_version` | 1 | 2 (Q6) |
| DBCN write range | One readable management 4 KiB leaf | The re-walked B6 window. Linux never lets one write cross a 4 KiB page (`arch/riscv/kernel/sbi.c:604-605@v7.2`) |
| SRST cold or warm reboot | -2 | Terminal `guest-reboot` |
| Tagged console | CR becomes `?` | CR is dropped; hvc sends CR before LF (`drivers/tty/hvc/hvc_console.c:166-175@v7.2`) |
| Exit limit | 1,024, with 53 exits pinned | Ceiling 2^20, the guest-time budget, and per-class counters |

Everything else is unchanged: probes answer 1 for Base, TIME, DBCN, and
SRST and 0 otherwise; machine IDs are 0; TIME `set_timer` writes
`vstimecmp`; DBCN reads return -4; DBCN copies at most 256 bytes; every
other call returns -2. No guest request reaches M-mode, and the HS-to-M
allowlist stays as accepted.

Fact (QEMU, planning research): the research reference boot made 139 SBI
calls: 3 Base IDs; probes for TIME, IPI, RFENCE, SRST, and DBCN answered 1,
0, 0, 1, 1; 6 machine-ID reads; 89 DBCN writes; 35 DBCN reads denied with
-4; and one SRST (platform research §1c). With `sstc` in the DT, Linux
makes no TIME call (`drivers/clocksource/timer-riscv.c:193-196@v7.2`); a
uniprocessor kernel never calls IPI or RFENCE
(`arch/riscv/kernel/sbi.c:152-176,670-681@v7.2`) and skips FWFT below SBI
3.0 (`:696-697`); hvc polling never hangs up on -4
(`drivers/tty/hvc/hvc_console.c:684-702@v7.2`).

## Guest software

- **Source:** an external input only. `LINUX_GIT` names a git URL or local
  mirror, by default the public upstream
  `https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git`.
  `scripts/fetch-linux.sh` fetches only the pinned commit, as a shallow
  clone of tag `v7.2` under `build/k3-b6/` (as B3 fetches U-Boot), and
  requires Q4's commit and tag object and a clean tree. No personal path is
  committed.
- **Configuration:** `tinyconfig` plus the platform research fragment
  (§1b), merged with `scripts/kconfig/merge_config.sh`: `ARCH_RV64I`, an
  explicit `MMU=y`, `SMP=n`, `NONPORTABLE=y`, `RISCV_ISA_C=y`, `FPU=n`,
  `RISCV_ISA_V=n`, `RISCV_SBI_V01=n`, `BLK_DEV_INITRD=y` with an
  uncompressed `INITRAMFS_SOURCE`, `PRINTK`, `PRINTK_TIME`, `TTY`,
  `HVC_RISCV_SBI`, `SERIAL_EARLYCON_RISCV_SBI`, `BINFMT_ELF`, and no
  `MODULES`, `NET`, or `BLOCK`. `MMU=y` must be explicit because
  `NONPORTABLE` drops `PORTABLE`, which forced it
  (`arch/riscv/Kconfig:1344-1349@v7.2`; `drivers/tty/hvc/Kconfig:109-112@v7.2`).
  The build requires every requested value in the final `.config`.
- **Command line:**
  `earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1`, so a
  panic, Oops, or WARN ends in an SRST reboot request, which is terminal.
  The research reference boot printed no WARN, error, or panic line
  (`build/k3-b6-research/platform/runs/cons-64m/console.log`).
- **Init:** `guest/init.c`, one GPL-3.0-only static program with raw
  system calls and no libc, after B0's rehearsal init, built by GCC only
  (`rv64imac`, `lp64`) and embedded in both monitor images. It prints
  `B6INIT 01 START`, `02 UNAME`, `03 SLEEP` (a 1 s `nanosleep` timed by
  `clock_gettime`; `ok=1` for 1000-1999 ms of guest time),
  `04 RESULT pass` or `RESULT fail`, and `05 POWER_OFF`, then calls
  `reboot(LINUX_REBOOT_CMD_POWER_OFF)`, which becomes SRST shutdown.
- **Initramfs:** embedded from a `gen_init_cpio` list with `/dev/console`
  and the init as `/init`, `/init-exit`, and `/init-rdcycle`; the init
  dispatches on `argv[0]`, and the two variants run only when a QEMU-only
  DTB selects them with `rdinit=`. Kbuild fixes every mtime
  (`usr/Makefile:62-68@v7.2`). The init is a separate program inside an
  archive; the built `Image` is never committed or distributed.

### Device tree

One DTB serves QEMU and the board. `scripts/gen-dts.py` renders it from the
monitor constants, so it cannot drift from the G-stage, and the pinned
tree's own `scripts/dtc` compiles it with `-S 4096`:

```dts
/ {
	#address-cells = <2>; #size-cells = <2>;
	compatible = "beryllium,k3-b6-guest"; model = "Beryllium K3 B6 guest";
	chosen { bootargs = "earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1"; };
	cpus { #address-cells = <1>; #size-cells = <0>; timebase-frequency = <24000000>;
		cpu@0 { device_type = "cpu"; reg = <0>; compatible = "riscv";
			mmu-type = "riscv,sv39"; riscv,isa-base = "rv64i";
			riscv,isa-extensions = "i", "m", "a", "c", "zicsr", "zifencei",
				"zihintpause", "zba", "zbb", "zbs", "sstc", "svade";
			interrupt-controller { compatible = "riscv,cpu-intc";
				interrupt-controller; #interrupt-cells = <1>; }; }; };
	memory@80000000 { device_type = "memory"; reg = <0x0 0x80000000 0x0 0x4000000>; };
};
```

- No PLIC, APLIC, IMSIC, CLINT, or UART node: Linux needs only the
  timebase (`arch/riscv/kernel/time.c:27-30@v7.2`) and the hart's
  interrupt controller (`arch/riscv/kernel/irq.c:153-154@v7.2`).
  `mmu-type` skips the `satp` mode probe (`arch/riscv/mm/init.c:835-850@v7.2`).
- With tinyconfig a legacy `riscv,isa` alone is silently ignored and Sstc
  is lost; passing the full K3 list enables the AIA, `h`, and CBO paths
  (platform research §1d, §4). Hence this short list.
- **Timebase:** QEMU `virt` counts at 10 MHz, so with this 24 MHz DTB a
  guest second takes about 2.4 s of QEMU wall time. Guest time stays
  self-consistent, so the init's check holds on both. No QEMU check may
  depend on wall-clock time.

### Build, pins, and reproducibility

- `scripts/build-guest.sh` provides `flex` and `bison` as Q3 says, and
  stops with a clear message if one is still missing or an RPM does not
  match its pin. It then builds the init, the initramfs list, `Image`,
  `dtc`, and the DTB, and writes a record of the cross and host tools, as
  B3's `B3-BUILD.txt` does.
- **Reproducibility:** `KBUILD_BUILD_TIMESTAMP`, `KBUILD_BUILD_USER`,
  `KBUILD_BUILD_HOST`, `KBUILD_BUILD_VERSION=1`, `LOCALVERSION=`,
  `SOURCE_DATE_EPOCH` from the `v7.2` commit, and `-ffile-prefix-map`
  (runtime research §5.4). The init, `Image`, and DTB SHA-256 values are
  pinned; the pin covers this workstation's cross toolchain.
- **Repeat build:** `make -C bringup/k3-b6 kernel-repro` builds again in a
  second object directory and requires identical bytes. It runs at the B6-1
  exit and before the result packet, not in every `make check`, since each
  kernel build takes about 3.5-4 minutes on 8 CPUs; `make check` builds
  once, caches by pin, and checks every pin.
- **Reference boot:** the same `Image` under the pinned OpenSBI v1.6
  `fw_dynamic` that B5's QEMU runs use, with no monitor. A small stub, as
  in platform research §1f, enters the kernel with `a1` set to a reference
  DTB. `gen-dts.py` renders that DTB from the same template with one
  change: its memory node starts at `0x8020_0000`, because QEMU places
  OpenSBI at `0x8000_0000`. The reference boot must reach `RESULT pass`.
  It separates guest problems from monitor problems, and B6-1 can run it
  before the monitor exists.

**Negative variants**, each one change (GCC, QEMU only):

| Variant | Change | Expected |
| --- | --- | --- |
| `payload` | Boot image with the kernel's `magic2` altered | `BE_B6:FAIL payload` after `BE_B6:04` |
| `memory` | DTB memory node of 128 MiB on the 64 MiB window | `BE_B6:FAIL guest-page-fault`, faulting GPA (`htval` << 2) at or above the window end |
| `init-exit` | `rdinit=/init-exit`: init returns, so Linux panics | `BE_B6:FAIL guest-reboot` |
| `rdcycle` | `rdinit=/init-rdcycle`: a VU `rdcycle` | `BE_B6:FAIL virtual-instruction`, cause 22 |
| `exit-budget` | Monitor exit ceiling of 64 | `BE_B6:FAIL exit-budget` |
| `guest-timeout` | Monitor guest-time budget of 2^20 ticks | `BE_B6:FAIL guest-timeout` |

## Markers

Each run first prints B3's `SHIM` line, which must show
`shim=0x0000000108000000`, `dest=0x0000000102000000`, and
`bytes=0x0000000000034000`. A passing capture then holds these lines in
order. The R3 lines are the accepted text, re-derived from accepted
`arch/riscv/be/r5-runtime.c` (`165f4d00`) as B2 and B5 do.

```text
BE_R3:01 BOOT_VALIDATED
BE_R3:02 R1_DERIVED
BE_R3:03 R2_BUILT_REWALKED
BE_R3:04 HS_VS_STATE_VERIFIED
BE_R3:05 BINDING_PREPARED
BE_R3:06 HGATP_FENCED_PUBLISHED
BE_B6:01 GSTAGE_BUILT_REWALKED gpa=0x80000000 hpa=0x110000000 size=0x4000000 leaves=32 pool=0x102034000
BE_B6:02 HGATP_INSTALLED hgatp=0x8000000000102034
BE_B6:03 SSTC_STCE_READBACK henvcfg=0x8000000000000000
BE_B6:04 GUEST_CONTROLS_CHECKED hstatus_controls=0x180 hedeleg=0xb15d hideleg=0x40 hcounteren=0x2 fs=0x0 vs=0x0 vstimecmp=0xffffffffffffffff
BE_B6:05 GUEST_RAM_CLEARED gpa=0x80000000 size=0x4000000 ticks=<T>
BE_B6:06 PAYLOAD_PLACED kernel=0x80200000 kernel_bytes=<K> image_size=<S> dtb=0x83e00000 dtb_bytes=0x1000 ticks=<T>
BE_B6:07 ENTER_GUEST pc=0x80200000 a0=0x0 a1=0x83e00000
BE_B6_GUEST: [<s>] Linux version 7.2.0 <banner>
BE_B6_GUEST: [<s>] SBI implementation ID=0x4245 Version=0x2
BE_B6_GUEST: [<s>] Kernel command line: earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1
BE_B6_GUEST: [<s>] riscv-timer: Timer interrupt in S-mode is available via sstc extension
BE_B6_GUEST: [<s>] Memory: <m>K/65536K available <rest>
BE_B6_GUEST: [<s>] Run /init as init process
BE_B6_GUEST: B6INIT 01 START pid=1
BE_B6_GUEST: B6INIT 02 UNAME release=7.2.0 machine=riscv64
BE_B6_GUEST: B6INIT 03 SLEEP requested_ms=1000 elapsed_ms=<e> ok=1
BE_B6_GUEST: B6INIT 04 RESULT pass
BE_B6_GUEST: B6INIT 05 POWER_OFF
BE_B6_GUEST: [<s>] reboot: Power down
BE_B6:08 GUEST_SHUTDOWN type=0 reason=0 exits=<N> base=<N> time=0 dbcn_write=<N> dbcn_read=<N> dbcn_byte=0 srst=1 refused=0 ticks=<T>
BE_B6:09 SHUTDOWN type=0 reason=0
```

- **Other lines:** any other `BE_B6_GUEST: ` line may appear between
  `BE_B6:07` and `BE_B6:08`; the required ones keep this order. Only loader
  output and the shim line may precede `BE_R3:01`; nothing may follow
  `BE_B6:09`.
- **Placeholders:** `<K>`, `<S>` (the pinned `Image`'s file size and
  `image_size`), and `<banner>` are fixed at B6-1 by the reproducible
  build. `<T>` (hex ticks), `[<s>]` (printk time), `<m>`, `<rest>`, `<e>`
  (1000-1999), and each `<N>` vary. `exits` is the sum of the other
  counters and at most 2^20; `base`, `dbcn_write`, and `dbcn_read` are
  bounded, not pinned, and GCC and Clang need not agree.
- **Rejected** in any guest line, as case-sensitive substrings: `panic`
  (except in the pinned `Kernel command line` line), `Oops`, `WARN`,
  `BUG:`, `kernel BUG`, `Attempted to kill init`, `cut here`,
  `Call Trace:`, `Unable to handle kernel`, `rcu: INFO:`, `soft lockup`,
  `blocked for more than`, `segfault`, `unhandled signal`,
  `extension is not available in SBI`, `sbi_srst_reset`,
  `No working init found`, `Failed to execute`, `Out of memory`, and
  `RESULT fail`. Also rejected: an untagged line between the first and
  last monitor lines, a tag inside a guest line after its prefix, any
  `BE_B6:FAIL`, and a missing required line.
- A failure prints `BE_B6:FAIL <class>`; exit failures add

  `BE_B6:DETAIL cause=0x… pc=0x… tval=0x… htval=0x… htinst=0x… spvp=<0|1> vsatp=0x… exits=<N>`.

  The monitor then requests its SRST shutdown and prints
  `BE_B6:SRST_RETURNED` if that returns. On K3, OpenSBI 1.6 halts the
  board and a human resets it; in QEMU, SRST powers QEMU off.
- Classes: `boot` (every boot-contract, R1, R2, R3-check, binding, and R3
  install failure), `gstage`, `sstc`, `controls`, `payload`, `interrupt`
  (any interrupt at HS), `guest-page-fault` (causes 20, 21, 23),
  `virtual-instruction` (22, such as VU `rdcycle` or a gated CSR),
  `access-fault` (1, 5, 7), `illegal-instruction` (2), `exception` (any
  other cause), `exit-budget`, `guest-timeout`, `resume`, `console`,
  `guest-failure`, `guest-reboot`, and `shutdown-returned`. The run tools'
  terminal regex is `BE_B6:09 SHUTDOWN|BE_B6:FAIL|BE_K3_B3: FAIL`.

## Tests and evidence

| Layer | Check | Pass criterion |
| --- | --- | --- |
| Host | `tests/b6-gstage-test.c` (independent byte model, every single-bit flip of every non-zero PTE, bad descriptors, translation edges); `tests/b6-payload-test.c` (header and layout rules); `tests/b6-sbi-test.c` (B5's rows plus window edges, CR drop, counters, budgets, new classes, and a replay of the research call census) | Identical GCC and Clang output with pinned counts |
| Guest inputs | `build-guest.sh` pins; `kernel-repro` | Pins match; the second build is identical |
| Port | `scripts/port.py --check` | Byte-identical; 5 rules, 7 substitutions; B2's manifest matches |
| Image | `tests/check-b6-image.py` and its mutation test | The rules below, for GCC and Clang |
| Markers | `tests/check-b6-markers.py --self-test` and `--check-sources` | R3 lines from the pinned accepted source; the rest from this plan and the B6 sources |
| Reference | The reference boot | `RESULT pass`, then SRST power-off |
| QEMU | `tests/run-qemu.sh` (direct boot); `tests/run-qemu-uboot.py` with `tests/check-b6-capture.py`; `make kexec-rehearsal` | The scenarios and variants below; the GCC `k3-address` image through U-Boot; GCC and Clang through kexec |
| Board tools | `tests/run-tool-dry-run.sh`; `tests/test-kexec-load.py` | Dry-run cases pass; the loader's layout rules pass on B0's recorded `/proc/iomem` |
| Board | `k3-preflight` (read-only over SSH: B5's Sstc check, the `/proc/iomem` staging and window check, and kexec availability); `k3-load-check`; `k3-campaign`; optionally `k3-uboot-run` | Preflight passes; 3 GCC and 1 Clang kexec runs pass |

`make -C bringup/k3-b6 check` runs every row except `kernel-repro`, the
kexec rehearsal, and the board, and is self-contained: no root `Makefile`,
`./be`, or `scripts/check-be.sh` integration. The U-Boot rehearsal uses
B3's QEMU U-Boot v2022.10 and B5's `k3-address` method: `text_offset` =
L - `0x8000_0000` = `0x8800_0000`, so QEMU's `booti` places the image at
L. The kexec rehearsal uses B0's method on the k3-like CPU: a Linux host
under QEMU loads the B6 image in raw mode with B6's layout and reboots
into it. It needs a host kernel with `CONFIG_KEXEC`, by default B0's GCC
rehearsal kernel as in B1 and B2; unlike theirs it fails rather than skips
without one, and B6-4 records that kernel's version and SHA-256.

**Image checker** (B6-specific like B5's, from decoded instruction words):

- **Monitor:** seven `PT_LOAD` segments (B2's six and the NOLOAD pool),
  W^X, every accepted R5 linker `ASSERT` but the counted renames, a flat
  image of exactly `0x34000` bytes, B2's guest pages, `be_reset` calling
  `be_b1_quiesce` first, and no R4 or R5 mechanism symbol. The three R3
  functions are byte-identical to B2's; the install function has exactly
  two call sites, and `be_r3_arch_enter_management` and
  `be_r3_arm_management_entry` have none.
- **Instructions and CSRs:** one `ecall` (the accepted SBI helper); three
  `sret` (the dead R3 entry, B6's tail, B1's skip); `hgatp` writes and
  `hfence.gvma` only in the R3 functions; one `fence.i`; no `hfence.vvma`,
  `mret`, H load or store, or F, D, or V instruction. After the R3 reset,
  B6's arm helpers alone write `henvcfg`, `hedeleg`, `hideleg`,
  `hcounteren`, and `hstatus`; `vstimecmp` is also written by the TIME
  helper, `sscratch` by the vector, and `sepc` and `sstatus.SPP` by the
  tail. No other `vs*` write, no `hstateen0`, `hvictl`, `hvien`,
  `hviprio*`, or `hvip` access, and only boot code forms the pool address.
- **Boot image:** B3's header with `text_offset` `0x0600_0000` (QEMU's
  `k3-address`: `0x8800_0000`) and `image_size` equal to the file; the
  descriptor (`0x1_0200_0000`, `0x34000`, `0x1000`); the flat image at
  `0x1000`; the pinned kernel at `0x35000` and the pinned DTB after it;
  identical bytes from links at L and at `0x8600_0000`; payload constants
  equal to these offsets; and the five ranges disjoint.
- **Guest inputs:** an independent kernel-header reader, and an FDT reader
  for the DT contract: one memory node equal to the window, one `cpu@0`
  with the pinned ISA list and interrupt controller, the timebase, the
  exact `bootargs`, and no other device node.
- **Mutation test:** in-memory defects, each rejected for its own reason,
  such as a changed `hedeleg` immediate, a missing `fence.i`, an extra
  `hfence.vvma`, `sret`, or install call, a payload byte flip, a larger
  DTB memory node, and a kexec FDT slot overlapping the window.

**QEMU scenarios** use QEMU 10.2.2, `-smp 1 -m 8G`, and OpenSBI v1.6
`fw_dynamic` as `-bios`, as in B5, with a 300 s timeout per run; outcomes
are judged in guest terms, never wall time.

| Scenario | Machine; CPU | Toolchains | Expected |
| --- | --- | --- | --- |
| `k3-like` | `virt,aia=aplic-imsic,aia-guests=7`; `rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true` | GCC, Clang | Pass |
| `rva23` | `virt,aia=aplic-imsic`; `rva23s64` | GCC, Clang | Pass |
| `plic` | `virt`; `rv64,h=true` | GCC, Clang | Pass |
| `no-sstc` | `virt,aia=none` with the accepted R5 CPU (`sstc=false`), as in B5 | GCC, Clang | `BE_B6:FAIL sstc` after `BE_B6:02` |
| `sbi-3.0` | `k3-like` with QEMU's bundled OpenSBI 1.7 | GCC, Clang | `BE_B6:FAIL boot` before `BE_R3:01` |
| `sbi-time` | `k3-like` with a DTB without `sstc` | GCC | Pass, with `time` above 0 |
| Variants | `k3-like` | GCC | The [negative variants](#build-pins-and-reproducibility) |

**Copied tools**, each with a counted change table in the B6 README, as
B5's are:

| B6 file | From | Main counted changes |
| --- | --- | --- |
| `src/b6.h`, `src/b6-sbi.c`, `src/b6-runtime.c`, `src/b6-trap.S`, `src/b6-platform.h` | B5's `b5*` files | The SBI changes above; steps after `BE_R3:06`, control values, vector extras, resume checks, first entry, and the `fence.i` helper |
| `src/b6-boot.lds` | B3's `b3-shim.lds` | Guest section and `PHDRS` entry; image-size and guest `ASSERT`s |
| `tests/b6-sbi-test.c`, `tests/check-b6-image.py`, `tests/check-b6-markers.py`, `tests/run-qemu.sh`, `tests/run-qemu-uboot.py`, `tests/run-tool-dry-run.sh`, `scripts/k3-uboot-run.sh` | B5's | As above: names, terminal regex, scenarios, variants, timeouts, transfer time |
| `tests/check-b6-capture.py` | B5's | B6 shim placement and markers; a kexec mode for Fedora's handoff (`Will call new kernel`, `arch/riscv/kernel/machine_kexec.c:173@v7.2`) beside the U-Boot mode; self-tests with Linux noise and each rejected pattern |
| `scripts/k3-preflight.sh` | B5's | Adds every `System RAM` child of `/proc/iomem` (B0's preflight keeps 24 lines), a stop on any child in the staging region or the window, and B0's kexec checks |
| `scripts/kexec-load.py`, `tests/test-kexec-load.py`; `scripts/k3-run.sh`, `scripts/k3-campaign.sh` | B0's | Raw layout only: the image at L, at most 4 MiB, the FDT after it, 2 MiB aligned, below the window; B6's loader, checker, terminal regex, and names |
| `tests/kexec-rehearsal.sh`, `tests/kexec-rehearsal/init.c` | B2's, B0's | Names, address, checker, and CPU; the file limit and B6's raw layout |

New files: `src/b6-gstage.{h,c}`, `src/b6-payload.{h,c}`,
`src/b6-guest-payload.S`, their host tests, `guest/`, the reference-boot
stub and its reference DTB, `scripts/port.py`, `fetch-linux.sh`,
`build-guest.sh`, `gen-dts.py`, the `Makefile`, and `README.md`. B0's
Fedora rehearsal may also run the kexec tools if a Fedora riscv64 disk
image is at hand; `k3-load-check` exercises them on the board without a
kexec.

**R6 and R7** do not apply, as for B5: both concern R5's checked switch,
which B6 does not link. B6 adds unproven privileged assembly and makes no
R6 or R7 claim.

## Accepted decisions B6 departs from

Each departure applies to B6 only and changes no accepted byte.

| # | Accepted decision or rule | B6 departure | How it is accounted for |
| --- | --- | --- | --- |
| 1 | No Linux boot; Linux-class guest SBI needs a separate plan (`planning/single-hart-runtime-plan.md:21,295,310-313,770,829,831`); B5's subset served only the B5 guest | A uniprocessor Linux guest uses B5's subset with the changes above | This is that separate plan, for this test guest only: emulation in HS, no M-mode forwarding or hart masks, Sstc, only the VS timer interrupt, DBCN as the one shared-memory operand, no service delegation |
| 2 | R0 lists thirteen resources and R2 builds the only roots, three 4 KiB mappings each (`arch/riscv/be/r0-layout.h:143-196`); runtime root edits are excluded (`planning/single-hart-runtime-plan.md:775`) | A B6 root maps 64 MiB outside the R0 resources, after R3 publication | B6 builder and independent walker, host tests, runtime re-walk, image checker; the accepted roots are still built and re-walked; no R1 or R2 claim covers it |
| 3 | R3 publishes, arms, and enters the management binding (`virt/be/r3.c:405,429`) | A second install with the B6 root; no R3 arm or entry; no `BE_R3:07` | Call-site counts in the image checker; the marker checker requires exactly `BE_R3:01`-`:06` |
| 4 | `hstatus` control `0x700180` (`include/be/r3.h:65-67`); VS stage 1 Bare with VTVM (`planning/single-hart-runtime-plan.md:488`); B5's `0x300180` and Bare `vsatp` | `0x180`; `vsatp` guest-owned | R3 check unchanged; arm and resume checks |
| 5 | Every guest exception traps to HS (`hedeleg` 0 in R3 and B5) | `hedeleg` `0xb15d` (Q5) | Guest-page, access, and virtual-instruction faults and all interrupts stay terminal |
| 6 | No delegated interrupts, timers, or Sstc; counters closed (`planning/single-hart-runtime-plan.md:481-485`) | As B5, and the guest now writes its own `stimecmp` | HS gates closed; STCE readback; `no-sstc`; Q7 |
| 7 | B5's 1,024-exit budget and 53-exit pin (`bringup/k3-b5/src/b5.h:60`; `bringup/k3-b5/tests/check-b5-markers.py:122`), its exact 22 lines, and -2 for reboots (`bringup/k3-b5/src/b5-sbi.c:234-236`) | Ceiling, time budget, counters, required lines among others, terminal reboot | Marker checker; `exit-budget`, `guest-timeout`, `init-exit` |
| 8 | F, D, and V absent or fully saved (`planning/single-hart-runtime-plan.md:486-487`) | Present on K3, left Off | Guest FPU and V off; a guest FP or vector instruction is an illegal instruction the guest handles; none in the monitor |
| 9 | The R5 linker script; B3's `.lds` pins `0x35000` bytes (`bringup/k3-b3/src/b3-shim.lds:66`); B0's raw loader caps images at 1 MiB with the FDT 1 MiB above (`bringup/k3-b0/scripts/kexec-load.py:50,285-288`) | Counted port rules and counted copies of the `.lds` and the loader | Shim source unchanged; image checker; loader host test; preflight |
| 10 | R6, R7, and R8 (B5's rows 12-13) | Not applicable | B6 sits outside R8; no R6 or R7 claim |

## Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| First VS-stage paging, native `sfence.vma` and `wfi`, misaligned handling, and Svade A/D on the X100; QEMU does not model K3 | Early terminal exit or a hang | `DETAIL` lines; the first board run is diagnostic; stop 6 |
| First VS-mode `stimecmp` writes on the COM260 (B5's guest armed its timer through SBI TIME) | `virtual-instruction`, or no timer interrupt | STCE and TM read back before entry; `sbi-time` rehearsed; Q7 |
| `hstateen0`, `hvictl`, `hvien`, `hviprio*` unwritten, and Fedora's KVM module loaded before a kexec | `virtual-instruction` on a gated CSR | DT contract; B5's guest used `sie`/`sip` from VS under U-Boot; stop 4 |
| Kexec hand-off state (a pending Linux timer, KVM's H CSRs) | A boot check fails | B1's quiesce and the R3 reset and check, as in B1 and B2's kexec runs |
| Guest panic or hang | A run that never ends | `panic=-1` turns a panic into a terminal reboot; the guest-time budget; the run tools' wall timeout catches a guest that stops exiting |
| Stale window contents; overlap with live memory | Masked bugs; corruption | The whole window is zeroed; preflight `/proc/iomem` check, static `ASSERT`s, stop 7 |
| `Image` drift or a toolchain change | Pin mismatch | Pins, `kernel-repro`, build record; stop 5 |
| Clang monitor text growth | Over `0x8000` | Measured at B6-3; stop 3 |
| Linux log variance; timebase mismatch | Flaky checks | Required lines only; no wall-clock checks |
| Unreliable network | No kernel source | `LINUX_GIT` may name a local mirror; the commit check keeps the source identical |
| `make check` time | Slow iteration | Inference: about 15-25 minutes, mostly the first kernel build, Linux under emulated H, and the QEMU YMODEM transfer |

## Non-claims and non-selections

- **Evidence:** QEMU results are emulation; board results are diagnostic
  bring-up evidence for one board, firmware, Fedora kernel, and U-Boot
  build, never hardware validation, qualification, or formal verification.
  QEMU, Model, Helium, R-series, and B0-B5 claims do not transfer.
- **Not selected:** a development kernel or BSP; a Linux guest interface,
  SBI profile, hypercall ABI, or stable guest ABI; OpenSBI as the long-term
  firmware boundary; the roadmap's "One protected domain and OS boundary"
  phase (`planning/roadmap.md:660`); a VS control-plane shape.
- **Not included or changed:** everything acceptance would not authorize
  (above); guest networking, block storage, and modules; policy; and any
  isolation claim beyond the G-stage window. The board's firmware, U-Boot,
  storage, and Fedora installation stay unchanged.

## Work packages

The packages run in order; one result review packet follows B6-6.

| Package | Work | Exit criteria |
| --- | --- | --- |
| B6-1 Guest software and reference boot | `fetch-linux.sh`; fragment, init, initramfs list, DTS template, `gen-dts.py`; `build-guest.sh`; `kernel-repro`; reference boot | Init, `Image`, and DTB pins; identical repeat build; reference boot reaches `RESULT pass`; sizes inside budget |
| B6-2 Pure-C mechanisms | `b6-gstage`, `b6-payload`, `b6-sbi`, and their host tests | Identical GCC and Clang output, pinned counts |
| B6-3 Monitor and image | `port.py`; runtime, trap, and platform files; boot `.lds` and payload object; `Makefile`; image checker; README | Port and image checks pass for both toolchains; every budget holds |
| B6-4 QEMU rehearsals and `make check` | Scenarios and variants; marker and capture checkers; U-Boot and kexec rehearsals; board-tool copies and dry run | `make -C bringup/k3-b6 check` and `make -C bringup/k3-b6 kexec-rehearsal` pass |
| B6-5 Preflight and board runs | `k3-preflight`; `k3-load-check`; `k3-campaign`: three GCC runs, one Clang run; the optional U-Boot run (Q2) | Every capture passes `check-b6-capture.py`, or a stop applies |
| B6-6 Result packet | Retention with B0's tool (default kexec handoff; `--handoff 'Moving Image from'` for U-Boot); README results; `kernel-repro` again; `planning/k3-b6-result-review-summary.md`; status documents | One exact result commit and packet for your decision |

## Stop conditions

Each returns B6 to the responsible human, with the evidence so far, before
any workaround:

1. A needed change to an accepted R0-R7 byte, retained R8 input, accepted
   B0-B5 file (including B2's `port.py`, B1's quiesce, B3's shim source,
   and B0's retention tool), or root integration (`Makefile`, `be`,
   `scripts/check-be.sh`).
2. A needed new HS-to-M SBI call, HS interrupt path, `hvip` injection,
   second entered domain, other hart, device, MMIO, or DMA path.
3. A budget overrun.
4. A needed CSR write outside the B6 inventory, such as `hstateen0` or
   `hvictl`.
5. An init, `Image`, or DTB that does not rebuild byte for byte or match
   its pin, or a missing host tool (Q3).
6. A board outcome QEMU did not show: an unexpected exit class, a missing
   line, a hang, or a watchdog reset. B6 diagnoses it read-only first.
7. A preflight `/proc/iomem` child or FDT reservation inside the staging
   region or the window.
8. The preflight lacks `sstc` on hart 0, or a run prints `BE_B6:FAIL sstc`.
9. Any step that would write firmware, the U-Boot environment, flash, boot
   configuration, or board storage, use TFTP or a staged-NVMe `load`, or
   need automation to type at U-Boot.
10. The guest probes and uses SBI outside the subset: a refused call, or an
    extension it needs present beyond Base, TIME, DBCN, and SRST.
11. A needed switch to `v6.18` (Q4), or to the DTB without `sstc` on the
    board (Q7).

## Board safety

- **RAM only:** under kexec, the image and loader are staged in Fedora's
  tmpfs `/tmp`, and `kexec_load` places the segments in RAM; under U-Boot,
  `loady` writes `0x1_4000_0000` and `booti` moves the image to L. The
  shim writes only the monitor image and its own report line; the monitor
  writes only its image, its pool, and the guest window. No `saveenv` or
  `env save`, `gzwrite`, flash, firmware, boot-configuration, or storage
  write; no TFTP; no staged NVMe file.
- **Human control:** the human resets the board after every run, because
  OpenSBI 1.6 halts it after SRST, and Fedora then autoboots. Automation
  reads the serial port output-only and uses SSH to Fedora only for the
  read-only preflight and B0's staging, load, and `systemctl kexec` steps.
  For the optional U-Boot run the human types every command and starts the
  YMODEM transfer; automation only reads the picocom log, and B3's 75 s
  post-halt watch stays.
