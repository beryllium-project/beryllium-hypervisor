<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B7 plan: two Linux guests on one hart of the COM260

## Decision record

The responsible human accepted this plan at exact commit
`026974fb619295482b93a7ae8cffdc4f552825ea` (parent
`915370aa09e08a48aa351ff891ff892d3ae415b3`) on 2026-10-08. The
instruction, given in reply to the request below to accept, revise, or
defer that exact commit, was `accept 026974`, which resolves uniquely to
that commit.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted; only this section
  and the status line below were added afterwards.
- **Authorized:** B7 implementation under this plan, work packages B7-1 to
  B7-6:
  - new code and tests under `bringup/k3-b7/`;
  - building the pinned upstream Linux `v7.2`, the same external guest
    input as B6, with a userland from its own `tools/include/nolibc`;
  - the QEMU rehearsals, including the kexec rehearsal;
  - the read-only Fedora preflight;
  - RAM-only COM260 runs through Linux kexec, three GCC and one Clang;
  - ending in one result review packet.

  Each [stop condition](#stop-conditions) returns B7 to the responsible
  human.
- **Open questions:** none was answered, so the defaults apply:
  - Q1: a 10 ms slice, 240,000 ticks at 24 MHz.
  - Q2: distinct VMIDs 1 (G0) and 2 (G1), with R5's write, fence, and
    readback on every switch.
  - Q3: G0 at HPA `0x1_1000_0000` and G1 at `0x1_1400_0000`, each 64 MiB
    at GPA `0x8000_0000`.
  - Q4: no U-Boot run; kexec only.
  - Q5: K = 8 alternations, plus overlapping `B7INIT 03` phases and at
    least one `wfi` switch and one slice switch.
  - Q6: one static nolibc `/init` that reads its guest ID from `argv`
    (`-- be.guest=<g>` in `bootargs`), plus B6's two QEMU-only variants.
  - Q7: the `BE_B7:`, `BE_B7_G0: `, `BE_B7_G1: `, and `B7INIT`
    identifiers, the DT model and compatible, and SBI implementation ID
    `0x4245`, version 3.
  - Q8: a guest that exhausts its exit ceiling or the run's time budget
    fails the whole run closed.
  - Q9: B7's own C files compile with `-Os`.
  - Q10: when both guests are idle, HS programs `stimecmp` and waits in
    `wfi`.
  - Q11: no `wfi` traps on the board is a stop.
- **Not authorized:** everything the plan excludes, including:
  - shared memory or channels between the guests, fault injection or
    denial demonstrations, and guest console input or a shell;
  - SMP, more than two guests, guest FP or vector, dynamic configuration,
    and devices, MMIO, interrupt controllers, or DMA;
  - a development-kernel/BSP selection, or any change to the board's host
    kernel;
  - a change to any accepted R0-R7 or B0-B6 byte or retained R8 input;
  - root `Makefile`, `be`, or `scripts/check-be.sh` integration;
  - a new HS-to-M SBI call;
  - a U-Boot run, or automation typing at U-Boot;
  - any persistent firmware, U-Boot environment, flash,
    boot-configuration, or storage change;
  - push, tag, publication, release, or any successor, including S1-S3.
- **Evidence status:** acceptance adds no implementation, emulation, or
  board evidence. No B7 implementation has started.

## Decision requested

**Status:** accepted on 2026-10-08; see the [decision record](#decision-record).
As presented, the plan was proposed and not accepted, and no B7
implementation had started: `bringup/k3-b7/` did not exist, and nothing had
been built or run for B7. The research builds and QEMU runs cited below are
planning research, not B7 evidence.

The accepted [roadmap](roadmap.md) re-baseline lists B7 as the next step
and requires an accepted bounded plan before any B7 implementation. On
2026-10-08 at 16:35 CEST the responsible human wrote: `proceed with B7
here, I will work on S1 in a separate session after some research &
revision`. That instruction authorizes drafting this plan and
planning-only research. It authorizes no implementation, board run, or
push. S1 is with the responsible human in a separate session; this plan
does not depend on it.

The responsible human is asked to decide on the exact commit that adds
this plan on branch `beryllium/k3-b7-bringup` (parent: the step 3
acceptance record `915370aa09e08a48aa351ff891ff892d3ae415b3`, which holds
all of B6 and the accepted re-baseline):

- **Accept:** authorizes B7 implementation under this plan, work packages
  B7-1 to B7-6: new code and tests under `bringup/k3-b7/`; building the
  pinned upstream Linux `v7.2`, the same external guest input as B6, with
  a userland from its own `tools/include/nolibc`; QEMU rehearsals,
  including the kexec rehearsal; the read-only Fedora preflight; and
  RAM-only COM260 runs through Linux kexec, three GCC and one Clang. It
  ends in one result review packet. Each
  [stop condition](#stop-conditions) returns B7 to the responsible human.
- **Request revisions** or **defer:** B7 stays unstarted.

Acceptance would not authorize:

- shared memory or channels between the guests, fault injection or
  denial demonstrations, or guest console input or an interactive shell;
- SMP, more than two guests, guest FP or vector state, dynamic
  configuration, or devices, MMIO, interrupt controllers, or DMA;
- a development-kernel/BSP selection, or any change to the board's host
  kernel;
- a change to any accepted R0-R7 or B0-B6 byte, or to a retained R8 input;
- root `Makefile`, `be`, or `scripts/check-be.sh` integration;
- a new HS-to-M SBI call;
- a U-Boot run (unless Q4 is answered yes), or automation typing at
  U-Boot: B6's direction does not carry over;
- any persistent firmware, U-Boot environment, flash, boot-configuration,
  or storage change;
- push, tag, publication, release, or any successor, including S1-S3.

### Open questions

Each has a default, so acceptance can proceed without answers.

| # | Question | Default if unanswered |
| --- | --- | --- |
| Q1 | Slice length? | 10 ms: 240,000 ticks at 24 MHz. Linux's tick is 4 ms (`CONFIG_HZ=250`, periodic); an idle guest's timer is delivered at its due time whatever the slice ([Scheduler](#scheduler)) |
| Q2 | Distinct VMIDs, or one VMID with a full fence on each switch? | Distinct VMIDs 1 (G0) and 2 (G1), and still R5's discipline on every switch: the accepted install function writes `hgatp`, runs `hfence.gvma zero, zero`, and reads back. No `hfence.vvma` ([G-stage](#g-stage-and-vmids)) |
| Q3 | Window addresses? | G0 at HPA `0x1_1000_0000` (B6's window), G1 at `0x1_1400_0000`; each 64 MiB at GPA `0x8000_0000` |
| Q4 | Add one GCC board run through U-Boot `booti`? | No: kexec only. "Yes" adds one GCC run in which the human types every U-Boot command, as B3 and B5 did; B6's automation direction does not carry over |
| Q5 | Interleave threshold K? | K = 8 alternations between consecutive guest lines, plus overlapping `B7INIT 03` phases and at least one `wfi` switch and one slice switch ([Markers](#markers)) |
| Q6 | The nolibc programs' content? | One static `/init`: guest ID from `argv` (`-- be.guest=<g>` in `bootargs`), eight compute-and-sleep steps, the 1 s sleep check, a result, and power-off; plus B6's two QEMU-only variants. The alternative reads `/proc/cmdline`, which needs `CONFIG_PROC_FS=y` (+82,240 bytes of `Image`) and a mount ([Guest software](#guest-software)) |
| Q7 | Identifiers? | `BE_B7:` (monitor lines), `BE_B7_G0: ` and `BE_B7_G1: ` (guest lines), `B7INIT` (init lines), DT model "Beryllium K3 B7 guest" and compatible "beryllium,k3-b7-guest", and SBI implementation ID `0x4245`, version 3; all B7-only and unregistered |
| Q8 | If one guest exhausts its exit ceiling or the run's time budget? | The whole run fails closed (`BE_B7:FAIL exit-budget` or `guest-timeout`, with a `DETAIL` line naming the guest), as does every other terminal guest exit. The alternative stops only that guest and lets the other finish; it adds a per-guest failure path for no B7 evidence |
| Q9 | Compile B7's own C files with `-Os` rather than the accepted `-O2`? | Yes, to protect the accepted 32 KiB monitor-text limit. The port's accepted files, B1's quiesce, and B3's shim keep their flags ([Budgets](#budgets)) |
| Q10 | When both guests are idle, how does HS wait? | HS programs `stimecmp` to the earlier wake time and executes `wfi` with `sstatus.SIE` = 0 and `sie.STIE` = 1, re-reading `time` in a loop. The alternative polls `time` and adds no `wfi` to the image |
| Q11 | If the board shows no `wfi` traps, because K3 completes a guest `wfi` within its time limit? | A [stop](#stop-conditions). The slice alone would still rotate the guests, but the plan's idle switch would be unshown |

## Goal and pass criterion

B7 runs two copies of the B6 guest (pinned Linux `v7.2`, uniprocessor, no
devices) as G0 and G1 on hart 0 of the COM260, each with its own 64 MiB
window, G-stage root, and VMID. The monitor saves and restores each
guest's vCPU state, and switches round-robin when the running guest idles
(its `wfi` traps) and when an HS timer slice expires: the monitor's first
interrupt of its own. Each guest's console lines carry its prefix, whole
and never mixed. A nolibc init in each guest computes, sleeps, and powers
off. B7 passes when the [marker checker](#markers) accepts the capture,
which must show both guests' complete line sets, at least K alternations,
overlapping init phases, both shutdowns, per-guest exit counts, and the
switch counts. That must hold in the QEMU rehearsals and in three GCC and
one Clang RAM-only kexec runs on the COM260.

## Base and inputs

- **Base:** `beryllium/roadmap-rebaseline` at `915370aa`, which holds
  accepted B0-B6, the accepted-tool fixes, and the accepted re-baseline.
- **Reused unchanged:**
  - B2's `scripts/port.py` and its pinned output, B1's
    `src/b1-handoff.S`, and B3's `src/b3-shim.S`;
  - B0's `tests/retain-results.py`, `tests/summarize-runs.py`, and
    rehearsal `mkcpio.py`;
  - B6's `scripts/fetch-linux.sh` and `guest/b6-kernel.config`.

  Everything else B7 takes from B6 is a counted copy under
  `bringup/k3-b7/` ([Port and copies](#port-and-copies)). `bringup/k3-b6/`
  does not change.
- **External input, never committed:** B6's Linux `v7.2`
  (`8d3ae59288f1e7d58d76558a6ee96d533bc5019f`, tag object
  `237a1c39e8dfd3e1c6f1f023eea37a48ec04cc63`). The userland's headers come
  from the same tree: its UAPI headers (`headers_install`) and
  `tools/include/nolibc`. There is no new external input. The kernel is a
  test payload, not a development-kernel/BSP selection, which stays
  undecided.
- **Platform facts:** B6's records and claim boundary
  ([B6 result](k3-b6-result-review-summary.md)), plus the B6 preflight
  (`bringup/k3-b6/results/20261008-com260/preflight.txt`): the board DT
  lists `sstvala`, `smaia`, `ssstateen`, `sscofpmf`, and `zawrs` on every
  X100 hart (lines 8-22); Fedora reports OpenSBI 1.6, the Sstc S-mode timer,
  Sv39x4, and `VMID 14 bits available` (lines 108-123); and no
  `/proc/iomem` child or FDT reservation lies in
  `0x1_05e0_0000`-`0x2_ee04_7fff` (lines 84-106, 140).
- **Research:** notes written for this plan on 2026-10-08, kept outside
  the repository, are cited as "planning research §N"; their scratch is
  under `build/k3-b7-research/` (gitignored). *Fact* marks what a cited
  file, record, or run shows, *inference* reasoning from facts. Upstream
  sources are `path:line@v7.2`; the H-extension text is `hypervisor.adoc`.

## Architecture

### What B7 adds to B6

| Area | B6 | B7 |
| --- | --- | --- |
| Guests | One | Two, G0 and G1, from one kernel `Image` and two DTBs that differ only in `bootargs` |
| G-stage | One root, VMID 0 | Two roots in two B6-shaped pools; VMIDs 1 and 2; each maps only its guest's window |
| vCPU state | One frame, never switched | Per-guest frame and CSR set, saved on switch-out, restored and read back on switch-in |
| HS interrupts | None | The Sstc HS timer (`stimecmp`, `sie.STIE`), taken only while V=1 |
| `wfi` | Native in the guest (VTW clear) | Traps under `hstatus.VTW`; the guest idles until its own timer is due |
| Console | One prefix, tagged on the fly | Per-guest line buffers and prefixes; whole lines only |
| SBI | Version 2; shutdown ends the run | Version 3; a shutdown stops only the calling guest |

The R3 prelude, the payload checks, the window clear and copy, and the
checked resume tail stay B6's; every `hgatp` write and `hfence.gvma` stays
inside the accepted install function.

### Boot sequence

1. A loader places the boot image at L = `0x1_0800_0000` and enters it on
   hart 0. B3's shim copies the monitor to `0x1_0200_0000`, as in B6.
2. The accepted R3 sequence prints `BE_R3:01`-`:06`.
3. B7 builds and re-walks both roots (`BE_B7:01` per guest). It installs
   G1's root and then G0's through the accepted install function,
   checking each readback (`BE_B7:02`).
4. B7 arms `henvcfg` (`BE_B7:03`) and the shared controls (`BE_B7:04`). It
   checks the payload's shape once, zeroes both windows (`BE_B7:05` per
   guest), and copies the kernel into both windows and each DTB into its
   own (`BE_B7:06` per guest). One `fence.i` follows.
5. B7 fills both first-entry frames: `sepc` `0x8020_0000`, `a0` = 0, `a1`
   = `0x83e0_0000`, other GPRs 0. Both CSR sets start at zero, with
   `vstimecmp` = `~0`. It prints `BE_B7:07`, programs the first slice, and
   enters G0 (`BE_B7:08 guest=0`) through the checked tail. G1's first
   entry happens at the first switch (`BE_B7:08 guest=1`).

### Per-guest state and the switch

The exit vector and the resume tail keep B6's single exit record in the
management saved page; each guest also has a vCPU record in monitor BSS
(a copy of the exit record, and its CSR set), copied in C. Fact (planning
research §3, §4): on every slice, a one-guest QEMU probe saved this CSR
set, loaded poison, installed its root under a second VMID, restored and
read back the set, and switched back; Linux still reached `RESULT pass`,
and every readback was exact.

| State | Per guest | Basis |
| --- | --- | --- |
| x1-x31, `sepc` | Yes: the frame | B6's 320-byte `struct be_r4_frame` |
| `sstatus.SPP`, `hstatus.SPVP` | Yes: the guest's mode at the exit; the tail sets SPP from the saved SPVP | A slice can preempt VU (user) or VS code. B6 always resumed VS |
| `vsstatus`, `vsie`, `vstvec`, `vsscratch`, `vsepc`, `vscause`, `vstval`, `vsatp` | Yes | VS CSRs, as KVM swaps them (`arch/riscv/kvm/vcpu.c:603-621,663-681@v7.2`). With `hideleg` = VSTI, `vsie` is `hie.VSTIE` |
| `vstimecmp` | Yes | The guest's own Sstc timer (`arch/riscv/kvm/vcpu_timer.c@v7.2`) |
| `scounteren`, `senvcfg` | Yes | No VS copy: "Hypervisor software is expected to manually swap the contents of these registers". KVM swaps both (`vcpu.c:754-755,765-766@v7.2`). Linux writes `scounteren` (`arch/riscv/kernel/head.S:245@v7.2`) |
| `hgatp` | Fixed per guest | Root and VMID |
| `vsip` | No | With `hideleg` = VSTI, `vsip.STIP` is read-only (from `vstimecmp`), and SSIP and SEIP read zero |
| Every other control | No: shared and fixed | [Guest controls](#guest-controls) |
| F, D, V; AIA VS CSRs; `hstateen0`; `scontext` | Not used | Off, or outside the DT contract, as in B6 |

A switch from guest c to guest n:

1. copies the exit record into c's vCPU record and saves c's eleven CSRs
   (an assembly helper reads them);
2. installs n's root through the accepted install function and requires
   the readback to equal n's `hgatp`;
3. loads n's eleven CSRs; the helper writes each and reads all back, and
   C requires every readback to equal the saved value;
4. copies n's vCPU record into the exit record;
5. programs the HS deadline ([Scheduler](#scheduler)) and resumes through
   the checked tail, which now also requires n's `hgatp`.

A mismatch is `BE_B7:FAIL switch`, with a `DETAIL` line naming the
register. This is R5's discipline (write the root, fence, read it back,
then restore checked state); R5's own switch, with its fixed management
and protected identities, is not linked.

### Scheduler

A pure-C state machine (`src/b7-sched.c`), host-tested on its own. Each
guest is RUNNABLE, IDLE (with a wake time, its saved `vstimecmp`), or
STOPPED. The dispatcher feeds it one event per exit:

| Exit | Event | Guest after |
| --- | --- | --- |
| VS `ecall`, served by the SBI core | None: resume the same guest | Unchanged |
| Cause 22 with `stval` = `0x10500073` (`wfi`) and SPVP = 1 | WFI; `sepc` += 4 | IDLE until its `vstimecmp` |
| Supervisor timer interrupt (scause `0x8000000000000005`): the slice ended, or the other guest's wake time came | SLICE | Unchanged |
| SRST shutdown (reason 0) | STOP; print `BE_B7:09` | STOPPED |
| Anything else | Terminal for the whole run (Q8) | — |

A guest is ready if it is RUNNABLE, or IDLE and its wake time has passed.
Next, the monitor runs the other guest if it is ready, else the same
guest if it is ready. When both have STOPPED it is done: it prints
`BE_B7:10` and `:11` and requests its SRST shutdown. Otherwise no guest
is ready: HS sets `stimecmp` to the earliest wake time and waits (Q10),
then picks again. The wait never runs past the run's time budget.

Before each resume, HS sets `stimecmp` to the earlier of now + slice (Q1)
and the other guest's wake time, if it is IDLE. So a descheduled idle
guest gets the hart when its timer is due. A descheduled busy guest waits
at most one slice; Linux catches up on a late tick from the `time`
clocksource (inference). Fact (planning research §0): the guest config
has a periodic 250 Hz tick, so an idle guest's next wake is at most 4 ms
away. In a QEMU probe of one guest, the 1 s sleep took about 251 `wfi`
traps, and the longest park was about one tick (planning research §3).

### Timers and `wfi`

- **Guest timers:** each guest arms its own Sstc `vstimecmp`, as in B6;
  hardware raises VSTIP and delivers it through `hideleg` while that guest
  runs. A switch saves and restores `vstimecmp`. A restored value at or
  below `time` raises VSTIP at once, so a late tick is taken on entry.
- **HS slice:** `sie.STIE` is set at arming and `sstatus.SIE` stays 0, so
  HS takes the supervisor timer only while V=1, through B6's vector
  (SPV = 1), never while it runs. Fact (planning research §3): the QEMU
  probe took 15-52 slices per run; with the nolibc init, 6-17 preempted
  VU code and resumed correctly with SPP from the saved SPVP. Fact
  (planning research §5): upstream OpenSBI 1.6 delegates STIP to S and
  sets `menvcfg.STCE`; the board's Fedora uses the Sstc S-mode timer,
  which needs that delegation (inference). HS has never taken an
  interrupt on the board: a [risk](#risks).
- **`wfi`:** `hstatus.VTW` = 1. The specification lets a VS `wfi` complete
  within an "implementation-specific, bounded time limit" before it traps
  (`hypervisor.adoc`, the `hstatus` VTW text). QEMU traps at once, with
  `stval` = the instruction. The board DT claims Sstvala, so `stval`
  should hold `0x10500073` on K3 too. Linux idles in `wfi` with
  interrupts disabled (`kernel/sched/idle.c:110-131@v7.2`). After the
  trap, the other guest may run; the idle guest resumes past its `wfi`
  once its timer is due, and then takes the pending VSTIP. A VU `wfi`,
  or any cause 22 with another `stval`, stays terminal
  (`virtual-instruction`).
- **HS wait:** `wfi` in HS with SIE = 0 wakes on the pending, locally
  enabled STIP, the rule Linux's idle relies on natively on K3 under
  Fedora. The loop re-reads `time`, so an early wake is harmless; upstream
  OpenSBI 1.6 never sets `mstatus.TW` (planning research §5).

### Guest controls

B7 writes these after `BE_R3:06`, reads each back before the first entry,
and checks them again at every resume.

| State | B6 | B7 | Checked |
| --- | --- | --- | --- |
| `hstatus` under the R3 mask `0x73f380` | `0x180` | `0x200180` at arming: VTW set, VTVM and VTSR clear. At resume SPVP is masked out, and the tail sets SPP from the guest's saved SPVP | Arm, resume |
| `hedeleg`, `hideleg` | `0xb15d` (WARL; K3 reads `0xb15c`), `0x40` | Same; the resume tail checks the armed `hedeleg` readback | Arm, resume |
| `henvcfg`, `hcounteren`, `htimedelta` | STCE, `0x2`, 0 | Same | Arm, resume |
| `sie` | 0 | `0x20` (STIE): the HS slice | Arm, resume |
| HS `stimecmp` | Not written after B1's quiesce | The slice or wake deadline, written before every resume and every HS wait | Image checker: one writer |
| `hvip` | 0 | VSSIP, VSTIP, and VSEIP 0; only those bits are tested. Fact (planning research §3): QEMU's `hvip` read shows a pending HS STIP as bit 5, which failed B6's exact check in 7 of 12 one-guest probe runs; the specification makes that bit read-only zero | Arm, resume |
| `hie`, `hgeie`, `sstatus` | `hie` at most VSTIE; 0; SIE, SPIE, FS, VS, XS, SUM, MXR 0 | Same; SPP as above | Arm, resume |
| `hgatp` | B6 root, VMID 0 | The running guest's root and VMID | Switch readback, resume |
| `vs*`, `scounteren`, `senvcfg` | Guest-owned; HS writes only `vstimecmp` | Per guest; written only by the load helper, and `vstimecmp` also by the arm and TIME helpers | Switch readback |
| `satp`, `stvec`, `sscratch` | 0, vector, trusted top | Same | Resume |
| `hstateen0`, `hvictl`, `hvien`, `hviprio1`/`2` | Never accessed | Never accessed | Stop 4 |

### Port and copies

B7's `scripts/port.py` is B6's: the same 5 rules and 7 substitutions on
B2's checked port, with B7 names, and a pool rule grown to a 64 KiB NOLOAD
`.gstage.root.b7` at `0x1_0203_4000` (16 KiB aligned) with its `ASSERT`s.
Every accepted `ASSERT` stays, and `--check` re-derives the tree byte for
byte. Each copy below gets a counted change table in the B7 README.

| B7 file | From | Main counted changes |
| --- | --- | --- |
| `src/b7-layout.h` | `src/b6-layout.h` | Two pools, windows, and VMIDs; two DTB slots; the slice; per-guest exit ceiling; SBI version 3 |
| `src/b7.h`, `src/b7-sbi.c` | B6's | `wfi` and slice classes; per-guest state and counters; shutdown stops one guest; version 3; per-guest line console; the controls check |
| `src/b7-sched.h`, `src/b7-sched.c` | New | The scheduler |
| `src/b7-gstage.{h,c}`, `src/b7-payload.{h,c}` | B6's | VMID in `hgatp`; two DTBs and two windows |
| `src/b7-runtime.c`, `src/b7-platform.h` | B6's | Two roots and windows, the switch, the dispatch loop, per-guest lines, the summary |
| `src/b7-trap.S` | B6's | VTW and STIE armed; SPP from the saved SPVP; the `hvip` VS-bit test; helpers to save and load the CSR set, write the deadline, and wait |
| `src/b7-boot.lds`, `src/b7-guest-payload.S` | B6's | A second DTB |
| `guest/`, `scripts/build-guest.sh`, `gen-dts.py`, `gen-payload.py` | B6's | The nolibc init and its header step; per-guest `bootargs`; two DTBs |
| `tests/`, `scripts/k3-*.sh`, `scripts/kexec-load.py`, `tools.mk` | B6's | Names, markers, terminal regex, both windows in the preflight, the scenarios, and the variants |

B6's U-Boot tools are not copied unless Q4 is answered yes; the boot image
keeps B3's `booti` header all the same.

### Budgets

Every budget is hard; an overrun is a [stop](#stop-conditions).

| Budget | Limit | Basis |
| --- | --- | --- |
| Monitor text | Below `0x1_0200_8000` (accepted `ASSERT`) | B6 ends at `0x6490` (GCC) and `0x6e30` (Clang). A one-guest probe of the new paths added `0x4f0` and `0x500`. `-Os` on the B6-layer C alone cut the probe by `0x1b0` (GCC) and `0x710` (Clang) (planning research §6). Inference: B7 with Q9 lands near `0x6c00`-`0x7000` (GCC) and `0x7000`-`0x7600` (Clang); at `-O2`, Clang would end within about `0x800` of the limit, or past it |
| Monitor data and BSS | At or below `0x1_0200_f000` (accepted `ASSERT`) | B6 ends at `0x1_0200_ada8`; B7 adds about 2 KiB: two vCPU records, two 256-byte line buffers, the scheduler |
| Flat image; pool | Exactly `0x34000` bytes; `0x10000` bytes at `0x1_0203_4000` | Two B6-shaped 32 KiB pools |
| Kernel `Image` | File at most 4 MiB; `image_size` at most 8 MiB | Fact (planning research §2): with B6's fragment and a nolibc `/init`, 1,553,332 bytes, `image_size` `0x1af628`, as B6 |
| DTBs; boot image | Two of exactly 4 KiB; at most 4 MiB | Inference: `0x1b3000` bytes (1,781,760) |
| Exits | 2^20 per guest | Inference: about 1,000-1,500 per guest per run (planning research §7) |
| Guest time | 2^32 ticks after G0's first entry (179 s at 24 MHz) | Inference: a board run of about 2.5 s of guest time |

## Memory and load paths

| HPA | Use | Basis |
| --- | --- | --- |
| `0x1_0000_0000`-`0x1_01ff_ffff` | OpenSBI 1.6, no-map | B0-B6 records |
| `0x1_0200_0000`-`0x1_0203_3fff` | Monitor flat image (accepted layout) | As B6 |
| `0x1_0203_4000`-`0x1_0204_3fff` | Pool: G0 root `0x1_0203_4000` (level-1 page at `+0x4000`), G1 root `0x1_0203_c000` (level-1 page at `0x1_0204_0000`) | New; below Fedora's kernel at `0x1_0220_0000` |
| L = `0x1_0800_0000`; the kexec FDT at L + 2 MiB | Staging, as B6 | B6 records |
| `0x1_1000_0000`-`0x1_13ff_ffff` | G0 window (Q3) | B6's window |
| `0x1_1400_0000`-`0x1_17ff_ffff` | G1 window (Q3) | New; free in every recorded map (planning research §6) |

Each guest sees B6's guest-physical layout in its own window: RAM at GPA
`0x8000_0000`-`0x83ff_ffff`, the kernel at `0x8020_0000`, its DTB at
`0x83e0_0000`. The boot image is B6's plus a DTB: the shim page, the
monitor at `0x1000`, the kernel at `0x35000`, then the G0 and G1 DTBs on
4 KiB boundaries. Static `ASSERT`s and the image checker refuse any
overlap among the monitor, pool, staged image, kexec FDT slot, and the two
windows.

The board path is Linux `kexec_load` from Fedora through B6's raw loader
(image at L, host FDT after it, below the G0 window), for three GCC and
one Clang runs; U-Boot `booti` only if Q4 says yes. QEMU boots the boot
ELF directly, as in B6.

## G-stage and VMIDs

B6's builder and independent walker are reused per pool: each root maps
its guest's 64 MiB as 32 leaves of 2 MiB (`0xdf`: V, R, W, X, U, A, D),
and nothing else. The walker re-derives `(gpa, hpa, size)` from each
pool's bytes before any `hgatp` write. A host test refuses two roots that
share a page or map overlapping windows. `hgatp` is `0x8000100000102034`
for G0 (VMID 1) and `0x800020000010203c` for G1 (VMID 2).

Why distinct VMIDs (Q2), from the H-extension text in `hypervisor.adoc`:

- HFENCE.GVMA "need not flush" a cache of guest-virtual to guest-physical
  translations. With one VMID, G1 could reuse G0's VS-stage entries,
  because both kernels map the same kernel addresses. That would corrupt
  the guest, though not give it the other guest's memory, since
  guest-physical addresses still go through the new root after the fence.
  Correctness would need `hfence.vvma` on every switch, which B6's image
  checker forbids.
- VS-stage and G-stage entries are tagged by VMID, so distinct VMIDs need
  no fence for correctness. B7 keeps the install function's full
  `hfence.gvma` anyway, as R5's discipline.
- Fact (planning research §3): QEMU reads back all 14 VMID bits, and the
  board reports `VMID 14 bits available`. Linux v7.2 records one vendor
  whose VS-stage TLB ignores the VMID (Andes AX66,
  `arch/riscv/kvm/main.c:22-27@v7.2`); SpacemiT is not among them.

## Guest SBI subset

B6's subset is kept, with these changes. It selects no SBI profile, guest
ABI, or Linux interface, and no guest request reaches M-mode.

| Item | B6 | B7 |
| --- | --- | --- |
| Base `get_impl_version` | 2 | 3 (Q7) |
| SRST shutdown, reason 0 | Ends the run | Stops the calling guest; the run ends when both have stopped |
| SRST reboot, or shutdown with reason 1 | Terminal | Terminal for the whole run (Q8) |
| DBCN write | The B6 window | The calling guest's walked window |
| Console | One prefix, bytes tagged as they come | Per-guest line buffers ([Markers](#markers)) |
| Counters | One set | One set per guest |

Otherwise unchanged: probes answer 1 for Base, TIME, DBCN, and SRST; TIME
`set_timer` writes the running guest's `vstimecmp`; DBCN reads return -4;
every other call returns -2.

## Guest software

- **Kernel:** one uniprocessor `Image` from B6's fragment, unchanged,
  built reproducibly as B6 does, with `kernel-repro`; only the built-in
  initramfs differs. Fact (planning research §0): that config has no
  procfs and a periodic 250 Hz tick.
- **Userland:** `guest/b7-init.c`, one GPL-3.0-only static program on
  `tools/include/nolibc` from the pinned tree. GCC builds it, as B6 builds
  its init: `rv64imac`, `lp64`, `-Os`, `-nostdlib`, static. B6's strict
  warnings apply, with the nolibc and UAPI headers given as `-isystem`.
  Fact (planning research §1): with `-I`, nolibc's own headers fail
  `-Wconversion`; with `-isystem`, GCC and Clang build a research init
  cleanly (4,736 bytes; 4,368 with lld), with no libgcc and no F, D, or V
  instruction. The headers come from `headers_install` and nolibc's
  `headers` target, written under `build/`; the source tree stays clean.
- **What `/init` does** (Q6):
  1. Reads `be.guest=<g>` from `argv`. Everything after `--` in the
     command line becomes init's arguments, with no "Unknown kernel
     command line parameters" notice (`init/main.c:478-496,1011-1018@v7.2`).
  2. Prints `01 START` and `02 UNAME`.
  3. Runs eight steps. Each computes for at least 25 ms of
     `CLOCK_MONOTONIC` time (bounded by a round cap), prints `03 STEP`,
     and sleeps 50 ms.
  4. Sleeps 1 s and prints `04 SLEEP` with `ok=1` for 1000-1999 ms.
  5. Prints `05 RESULT pass` or `fail`, then `06 POWER_OFF`, and calls
     `reboot(LINUX_REBOOT_CMD_POWER_OFF)`.

  A missing or malformed guest ID is `RESULT fail`. `/init-exit` and
  `/init-rdcycle` keep B6's QEMU-only variants, selected by `rdinit=`.
- **Device trees:** B6's template, with the B7 model and compatible.
  `gen-dts.py` renders one DTB per guest; they differ only in `bootargs`:
  `earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1 -- be.guest=<g>`.
- **Reference boot:** each guest's reference DTB under plain OpenSBI v1.6,
  with no monitor, as in B6. Fact (planning research §2): booted this way,
  a research kernel with B6's fragment and a nolibc init found its ID in
  `argv`, computed, slept 1004 ms, and powered off after `RESULT pass`; a
  procfs build read `/proc/cmdline` the same way.

## Markers

A passing capture holds B3's `SHIM` line (as in B6), then these lines in
this order:

```text
BE_R3:01 BOOT_VALIDATED
BE_R3:02 R1_DERIVED
BE_R3:03 R2_BUILT_REWALKED
BE_R3:04 HS_VS_STATE_VERIFIED
BE_R3:05 BINDING_PREPARED
BE_R3:06 HGATP_FENCED_PUBLISHED
BE_B7:01 GSTAGE_BUILT_REWALKED guest=0 gpa=0x80000000 hpa=0x110000000 size=0x4000000 leaves=32 root=0x102034000
BE_B7:01 GSTAGE_BUILT_REWALKED guest=1 gpa=0x80000000 hpa=0x114000000 size=0x4000000 leaves=32 root=0x10203c000
BE_B7:02 HGATP_INSTALLED g1=0x800020000010203c g0=0x8000100000102034
BE_B7:03 SSTC_STCE_READBACK henvcfg=0x8000000000000000
BE_B7:04 GUEST_CONTROLS_CHECKED hstatus_controls=0x200180 hedeleg=<h> hideleg=0x40 hcounteren=0x2 sie=0x20 fs=0x0 vs=0x0 vstimecmp=0xffffffffffffffff
BE_B7:05 GUEST_RAM_CLEARED guest=0 gpa=0x80000000 size=0x4000000 ticks=<T>
BE_B7:05 GUEST_RAM_CLEARED guest=1 gpa=0x80000000 size=0x4000000 ticks=<T>
BE_B7:06 PAYLOAD_PLACED guest=0 kernel=0x80200000 kernel_bytes=<K> image_size=<S> dtb=0x83e00000 dtb_bytes=0x1000 ticks=<T>
BE_B7:06 PAYLOAD_PLACED guest=1 kernel=0x80200000 kernel_bytes=<K> image_size=<S> dtb=0x83e00000 dtb_bytes=0x1000 ticks=<T>
BE_B7:07 SCHEDULER_ARMED guests=2 slice_ticks=0x3a980 first=0
BE_B7:08 ENTER_GUEST guest=0 pc=0x80200000 a0=0x0 a1=0x83e00000
BE_B7:10 RUN_COMPLETE switches=<N> wfi_switches=<N> slice_switches=<N> stop_switches=1 idle_waits=<N> idle_ticks=<T> ticks=<T>
BE_B7:11 SHUTDOWN type=0 reason=0
```

Between G0's `BE_B7:08` and `BE_B7:10` come both guests' lines and three
more monitor lines: `BE_B7:08 ENTER_GUEST guest=1 pc=0x80200000 a0=0x0
a1=0x83e00000` before G1's first line, and after each guest's last line
`BE_B7:09 GUEST_SHUTDOWN guest=<g> exits=<N> sbi=<N> wfi=<N> slice=<N>
base=<N> time=0 dbcn_write=<N> dbcn_read=<N> dbcn_byte=0 srst=1 refused=0
ticks=<T>`. Each guest's lines carry its prefix (`BE_B7_G0: ` or
`BE_B7_G1: `) and must hold, in order, among other lines:

```text
[<s>] Linux version 7.2.0 <banner>
[<s>] SBI implementation ID=0x4245 Version=0x3
[<s>] Kernel command line: earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1 -- be.guest=<g>
[<s>] riscv-timer: Timer interrupt in S-mode is available via sstc extension
[<s>] Memory: <m>K/65536K available <rest>
[<s>] Run /init as init process
B7INIT 01 START guest=<g> pid=1
B7INIT 02 UNAME release=7.2.0 machine=riscv64
B7INIT 03 STEP n=<i>/8 rounds=<r> t_ms=<t>
B7INIT 04 SLEEP requested_ms=1000 elapsed_ms=<e> ok=1
B7INIT 05 RESULT pass
B7INIT 06 POWER_OFF
[<s>] reboot: Power down
```

- **Interleaving (Q5):**
  - at least K = 8 alternations, where an alternation is a guest line
    followed by the other guest's next line, with monitor lines ignored;
  - G1 prints a `03 STEP` line between G0's first and last `03 STEP`
    lines, and G0 does the same within G1's;
  - `wfi_switches` and `slice_switches` are each at least 1.

  Inference: every count sits well above its floor, as both guests boot
  and step at once, and a 100-byte line at 115200 baud takes about a slice.
- **Consistency:** each `guest=<g>` matches the line's prefix; each
  `BE_B7:08` and `BE_B7:09` appears once per guest, where stated; both
  guests show `srst=1`; and the counters add up: per guest, `exits` =
  `sbi` + `wfi` + `slice`, with `sbi` the sum of B6's call classes, and
  `switches` = `wfi_switches` + `slice_switches` + `stop_switches`.
- **Console:** HS buffers each guest's bytes until LF (at most 256 bytes)
  and writes prefix, line, and LF in one firmware write. CR is dropped,
  and other bytes outside `0x20`-`0x7e` become `?`. A full buffer is
  written as its own line. A partial line is flushed when its guest stops
  and before a `FAIL` line. So lines never mix, and monitor lines never
  split a guest line. Fact (planning research §6): the longest guest line
  is 190 characters (the Linux banner).
- **Rejected:** B6's rejected substrings in any guest line; an untagged
  line between the first and last monitor lines; a tag inside a guest
  line; any `BE_B7:FAIL`; a missing required line. Only loader output and
  the shim line may precede `BE_R3:01`, and nothing may follow `BE_B7:11`.
- **Failures:** `BE_B7:FAIL <class>`, then a `DETAIL` line with `guest=<g>`
  where a guest is involved, and the SRST request. The classes are B6's,
  with `interrupt` now meaning any interrupt but the supervisor timer,
  plus `switch` and `scheduler`. The run tools' terminal regex is
  `BE_B7:11 SHUTDOWN|BE_B7:FAIL|BE_K3_B3: FAIL`.
- **Placeholders:** `<K>`, `<S>`, and `<banner>` are fixed at B7-1 by the
  reproducible build; the rest vary, and `03 STEP` appears eight times,
  `n=1/8` to `n=8/8`. GCC and Clang need not agree on counts.

## Tests and evidence

| Layer | Check | Pass criterion |
| --- | --- | --- |
| Host | `tests/b7-sched-test.c` (new): every state and event; round-robin order; the deadline as the earlier of slice and the other guest's wake; the both-idle wait; budget-bounded waits; done; saturating time arithmetic; invalid input fails closed | Identical GCC and Clang output with pinned counts |
| Host | `tests/b7-sbi-test.c` (B6's, extended): `wfi` and slice classification (`stval` match and mismatch, SPVP 0 and 1, other interrupts); per-guest SRST; version 3; per-guest counters; interleaved console bytes never forming a mixed line; context save and restore (the record copies, SPP from the saved SPVP, and the readback comparison of all eleven CSRs) | Identical GCC and Clang output with pinned counts |
| Host | `tests/b7-gstage-test.c`, `tests/b7-payload-test.c` (B6's): two pools, VMIDs, disjoint windows; two DTBs | Identical GCC and Clang output with pinned counts |
| Guest inputs | `build-guest.sh` pins; `kernel-repro` | Pins match; a second build is identical |
| Port | `scripts/port.py --check` | Byte-identical; 5 rules, 7 substitutions |
| Image | `tests/check-b7-image.py` and its mutation test | The rules below, for GCC and Clang |
| Markers | `tests/check-b7-markers.py --self-test` and `--check-sources` | The checker rejects every mutation of a passing capture: a missing line for either guest, a guest ID that differs from its prefix, a mixed line, fewer than K alternations, phases that do not overlap, zero `wfi` or slice switches, wrong counter sums, one shutdown only, an extra line after `BE_B7:11` |
| Reference | Both reference boots | Each reaches `RESULT pass` with its own guest ID |
| QEMU | `tests/run-qemu.sh`; `make kexec-rehearsal` | The scenarios and variants below; GCC and Clang through kexec |
| Board tools | `tests/run-tool-dry-run.sh`; `tests/test-kexec-load.py` | Dry-run cases pass; the loader's layout rules pass on B6's recorded `/proc/iomem` |
| Board | `k3-preflight`, `k3-load-check`, `k3-campaign` | Preflight passes; three GCC and one Clang kexec runs pass |

`make -C bringup/k3-b7 check` runs every row except `kernel-repro`, the
kexec rehearsal, and the board. It is self-contained, as B6's is.
Inference: it takes about 15-25 minutes, because every QEMU run now boots
two Linux guests.

**Image checker** (B6's rules, adapted):

- **Instructions:**
  - B6's instruction-site table (three `sret`, one `ecall`, one
    `fence.i`, the accepted halts' three `wfi`), plus one `wfi` in the HS
    wait helper;
  - no `hfence.vvma`, `mret`, H load or store, or F, D, or V instruction;
  - `hgatp` writes and `hfence.gvma` only inside the accepted R3
    functions; the install function has exactly two call sites (R3's and
    B7's root-install helper).
- **CSR writers:**
  - the per-guest CSRs only by the load helper (`vstimecmp` also by the
    arm and TIME helpers);
  - `stimecmp` only by the deadline helper and B1's quiesce;
  - `sie.STIE` and `hstatus.VTW` set only by the arm helper (accepted R3
    and B1 code only clear `sie`);
  - no access to `hstateen0`, `hvictl`, `hvien`, or `hviprio*`.
- **Layout and payload:**
  - B3's header and descriptor; the kernel and two DTBs at their
    offsets; the two DTBs equal but for `/chosen/bootargs`;
  - both `hgatp` values and their VMIDs;
  - the monitor, pool, staging, kexec FDT slot, and two windows pairwise
    disjoint.
- **Mutation test:** in-memory defects, each rejected for its own reason.
  Examples: VTW or STIE missing from an arm immediate; a fifth `wfi`; a
  third install call; an `hfence.vvma`; equal VMIDs or roots; equal
  `bootargs`; overlapping windows.

**QEMU scenarios:** B6's machines and CPUs, QEMU 10.2.2, OpenSBI v1.6
`fw_dynamic`, `-smp 1 -m 8G`, and B6's 300 s timeout per run. Outcomes are
judged in guest terms, never wall time.

| Scenario | Toolchains | Expected |
| --- | --- | --- |
| `k3-like`, `rva23`, `plic` | GCC, Clang | Pass |
| `no-sstc` (the accepted R5 CPU, as in B5 and B6) | GCC, Clang | `BE_B7:FAIL sstc` after `BE_B7:02` |
| `sbi-3.0` (QEMU's OpenSBI 1.7) | GCC, Clang | `BE_B7:FAIL boot` before `BE_R3:01` |
| `sbi-time` (both DTBs without `sstc`) | GCC | Pass, with `time` above 0 for each guest |
| `payload` (kernel `magic2` altered) | GCC | `BE_B7:FAIL payload` after `BE_B7:04` |
| `init-exit` (G1 `rdinit=/init-exit`) | GCC | `BE_B7:FAIL guest-reboot`, `guest=1` |
| `rdcycle` (G0 `rdinit=/init-rdcycle`) | GCC | `BE_B7:FAIL virtual-instruction`, `guest=0`, cause 22, `tval` not `wfi` |
| `exit-budget` (per-guest ceiling 64) | GCC | `BE_B7:FAIL exit-budget` |
| `guest-timeout` (budget 2^20 ticks) | GCC | `BE_B7:FAIL guest-timeout` |

B6's `memory` variant is not carried over: it shows a guest-page fault
beyond the window, which is a denial test, and B7 excludes those. R6 and
R7 do not apply, as for B5 and B6.

## Accepted decisions B7 departs from

Each applies to B7 only and changes no accepted byte. B6's departures 1-10
([B6 plan](k3-b6-plan.md)) carry over for each guest.

| # | Accepted B6 decision | B7 departure | Accounted for by |
| --- | --- | --- | --- |
| 1 | One guest; a second guest excluded | Two guests, one hart, time-shared | This plan; per-guest roots, windows, and VMIDs |
| 2 | HS takes no interrupt (stop 2) | The HS supervisor timer while V=1 | STIE arm and check; the image checker's `stimecmp` writers; QEMU scenarios; stop 6 |
| 3 | VTW clear; native guest `wfi` | VTW set; `wfi` traps and parks | The exact `stval` match; the `rdcycle` variant; stop 6 |
| 4 | HS writes no `vs*` CSR but `vstimecmp` | The load helper writes the per-guest set, plus `scounteren` and `senvcfg` | Readback checks; the image checker's writer table |
| 5 | `hgatp` set once; VMID 0 | Set on every switch; VMIDs 1 and 2 | The accepted install function only, with readback |
| 6 | B6's exact `hvip` = 0 check | Only VSSIP, VSTIP, VSEIP tested | Planning research §3; the specification |
| 7 | No HS `wfi` beyond the accepted halts | One more `wfi`, in the HS wait | Image checker; Q10 |
| 8 | Accepted `-O2` for B6's C | `-Os` for B7's own C (Q9) | Measured text at B7-3 |

## Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| K3 completes a VS `wfi` within its time limit instead of trapping | No idle switches; `wfi_switches` = 0 | The slice still rotates; the checker requires one; stop 6, Q11 |
| K3's `stval` on the trap is not the instruction | `wfi` not recognized: `FAIL virtual-instruction` | The DT claims Sstvala; `DETAIL` prints `tval`; stop 6 |
| HS's first interrupt on the board | No slice, or an unexpected cause | Three QEMU CPU models; `FAIL interrupt` with `DETAIL`; stop 6 |
| A VS-stage TLB that ignores the VMID | Guest crash on the board only | Distinct VMIDs and the full fence; stop 6, diagnosed read-only |
| Clang monitor text | Over `0x8000` | Q9; measured at B7-3; stop 3 |
| Console bandwidth: about 10 KB of guest output at 115200 baud | Longer runs; more slice switches | Line buffers; a 179 s budget |
| Timing-dependent interleaving | A flaky checker | Structural floors (K = 8, overlap, one switch of each kind); no wall-time check |
| QEMU differs from K3; unreliable network | A board behaviour unrehearsed; no kernel source | Stop 6; `LINUX_GIT` may name a local mirror |

## Claim boundary and non-goals

- **Evidence:** QEMU results are emulation, and board results are
  diagnostic bring-up evidence for one board, firmware, and Fedora
  kernel. They are never hardware validation, qualification, or formal
  verification. QEMU, Model, Helium, R-series, and B0-B6 claims do not
  transfer.
- **Isolation:** by construction only. Two disjoint windows, two
  re-walked roots that each map only their own window, distinct VMIDs,
  DBCN copies from the calling guest's window only, and no shared page or
  channel. B7 runs no denial or fault-injection test and makes no
  isolation claim beyond that construction. The B7 layer has no proof.
- **Not selected:** a scheduler design, VMID policy, guest ABI, SBI
  profile, or console protocol for Beryllium; a development kernel or
  BSP; OpenSBI as the long-term firmware boundary.

## Work packages

The packages run in order; one result review packet follows B7-6.

| Package | Work | Exit criteria |
| --- | --- | --- |
| B7-1 Guest userland and pins | nolibc header step; `guest/b7-init.c`; initramfs list; DTS template and `gen-dts.py`; `build-guest.sh` with B6's fragment and `fetch-linux.sh`; pins; `kernel-repro`; both reference boots | Init, `Image`, and DTB pins; an identical repeat build; both reference boots reach `RESULT pass` with their own IDs; sizes within budget |
| B7-2 Pure-C mechanism and host tests | `b7-sched`, `b7-sbi` (with the console and switch-record logic), `b7-gstage`, `b7-payload`, and their host tests | Identical GCC and Clang output with pinned counts |
| B7-3 Monitor and image | `port.py`; runtime, trap, and platform files; boot `.lds` and payload object; `Makefile`; image checker and mutation test; README with counted change tables | Port and image checks pass for both toolchains; every budget holds |
| B7-4 QEMU and `make check` | The scenarios and variants; marker and capture checkers; kexec rehearsal; board-tool copies and dry run | `make -C bringup/k3-b7 check` and `make -C bringup/k3-b7 kexec-rehearsal` pass |
| B7-5 Board runs | `k3-preflight`; `k3-load-check` for GCC and Clang; `k3-campaign`: three GCC runs, then one Clang run; a human reset after each | Every capture passes `check-b7-capture.py`, or a stop applies |
| B7-6 Result packet | Retention with B0's tool; README results; `kernel-repro` again; `planning/k3-b7-result-review-summary.md`; status documents | One exact result commit and packet for your decision |

## Stop conditions

Each returns B7 to the responsible human, with the evidence so far, before
any workaround:

1. A needed change to an accepted R0-R7 or B0-B6 byte or a retained R8
   input, or root integration.
2. A needed new HS-to-M SBI call, `hvip` injection, H load or store
   (`hlv`, `hlvx`), third guest, other hart, device, MMIO, or DMA path.
3. A budget overrun.
4. A needed CSR access outside the B7 inventory, such as `hstateen0` or
   `hvictl`.
5. An init, `Image`, or DTB that does not rebuild byte for byte or match
   its pin; a missing host tool; or a need for a kernel config change
   beyond B6's fragment (other than Q6's procfs alternative, if chosen),
   a libc, or any new external input.
6. A board outcome QEMU did not show, diagnosed read-only first. That
   covers an unexpected exit class, a missing line, a hang, or a watchdog
   reset. It also covers these K3 differences in `wfi` or HS timer
   behaviour:
   - a `wfi` trap whose `stval` is not `0x10500073`;
   - no `wfi` trap at all (Q11);
   - an HS timer interrupt that does not arrive, or arrives with another
     cause;
   - an `hgatp` or per-guest CSR readback mismatch;
   - a guest crash that suggests stale translations.
7. A preflight `/proc/iomem` child or FDT reservation in the staging
   region or either window.
8. The preflight lacks `sstc` on hart 0, or a run prints
   `BE_B7:FAIL sstc`.
9. Any step that would write firmware, the U-Boot environment, flash,
   boot configuration, or board storage; use TFTP or a staged-NVMe
   `load`; or need automation to type at U-Boot.
10. A guest that needs SBI outside the subset.

## Board safety and procedure

- **RAM only:** kexec stages the image and loader in Fedora's tmpfs
  `/tmp`, and `kexec_load` places the segments in RAM. The shim writes
  only the monitor image and its report line. The monitor writes only its
  image, its pool, and the two windows.
- **Human control:** the human powers the board on and resets it after
  every run (OpenSBI 1.6 halts it after SRST); Fedora then autoboots.
  Automation reads the serial log output-only and uses SSH only for the
  read-only preflight and B0's staging, load, and `systemctl kexec` steps;
  it never types at U-Boot.
- **Procedure,** after `make -C bringup/k3-b7 check` and the kexec
  rehearsal pass: the read-only preflight (which also checks both
  windows), both load checks, then three GCC runs and one Clang run, with
  a human reset after each run:

```sh
make -C bringup/k3-b7 k3-preflight
make -C bringup/k3-b7 k3-load-check TOOLCHAIN=gcc
make -C bringup/k3-b7 k3-load-check TOOLCHAIN=clang
K3_SERIAL_LOG=<abs picocom log> K3_RUN_ROOT=$PWD/build/k3-b7/k3-campaigns/<date>-com260 make -C bringup/k3-b7 k3-campaign TOOLCHAIN=gcc RUNS=3
K3_SERIAL_LOG=<abs picocom log> K3_RUN_ROOT=$PWD/build/k3-b7/k3-campaigns/<date>-com260 make -C bringup/k3-b7 k3-campaign TOOLCHAIN=clang RUNS=1
```

## How B7 feeds S2 and the MVP

The roadmap expects the first MVP milestone to be the Helium TE PoC
scenario on two Linux guests, after S2 defines channels. B7 provides that
substrate without any of its policy: two Linux guests on one hart, in
separate windows and roots, with checked switching; the per-guest state
inventory; the first HS interrupt path; and board measurements of exit,
switch, and idle costs.
S1 and S2 may cite B7's result as diagnostic bring-up evidence. Shared
pages, channels, denial logging, fault injection, console input, and a
richer userland stay for the MVP plan.
