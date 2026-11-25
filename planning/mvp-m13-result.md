<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# MVP milestone M13: the result

M13 is MVP 2.0's first step after M11: the device facts of one K3
COM260 board, found before any device is given to a VS domain (the
[MVP plan](mvp-plan.md)'s S3-C.2, step (1), and S3-D.3). The
[M13 plan](mvp-m13-plan.md) bounds it. This page is its result, the
plan's work package M13-5:

- what was done;
- what [the record](k3-com260-devices.md) holds;
- a short account of what MVP 2.0's steps (2) and (3) can rely on, and
  what they cannot;
- and what the result changes.

The record is diagnostic: facts from the vendor's documents, its
sources, and one board. It is not hardware validation, and it is
evidence for no claim of the project's. Nothing here says that a
device's memory accesses on this board are confined, or that the
project supports a device (the plan's section 8).

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. If that commit is on the
public `main` with the responsible human's `Signed-off-by`, M13's
result is accepted: the record as it stands at that commit, and this
page. M13 is then complete. The signed commit differs from the one
reviewed only by that line and its committer date. The project's
internal records keep both commit IDs and the instruction.

The acceptance accepts no claim, chooses no device and no mechanism,
and authorizes no step. MVP 2.0's steps (2) and (3) each need a plan of
their own, at the responsible human's direction.

## 1. What was done

| Work package | What | On the public `main` |
| --- | --- | --- |
| The plan | Ten rules, five work packages, ten stops | `ac3bd40f`, 2026-11-23 |
| M13-1, the reading | The vendor's documents and sources at pinned commits, the published images by their SHA-256, and the inventory of 2026-11-16; the record's first draft | `ba973ed1`, 2026-11-23 |
| M13-2, the board's Linux | The read tool, `mvp/tools/k3-read.py`, with its fixed list of 28 reads and its self-test; one read session, and the session's facts in the record | `81006c36` and `d93275ba`, 2026-11-23 |
| M13-3, the review point | [Seven probes in three images](mvp-m13-3-review-point.md), put to the responsible human, whose reply was `probes: go` | `908b03da`, 2026-11-23 |
| M13-4, the probes | The probe images of `bringup/k3-m13/`, their checks, and their runs under QEMU, with a correction to the frame tool's self-test; the run tool, `mvp/tools/k3-m13-run.py`; one probe session, its public record, and its facts in the record | `b4cb6816`, `3349fbc4`, `df472d22`, and `0caf1df1`, 2026-11-24; `3693d448` and `05d5d03e`, 2026-11-25 |
| M13-5, the result | The record read once more as a whole; the [hardware roadmap](riscv-security-hardware.md) and the [glossary](glossary.md) brought up to date; this page | The commits that complete the record and add the disclosure's section, and this page's commit |

**The sessions on the board.** Each was on the responsible human's word
that the board was free.

- *One read session* of the board's own Linux, on 2026-11-23, from
  08:53:16Z to 08:53:32Z: 32 reads from the read tool's fixed list of
  28, over SSH. It wrote no file of its own on the board, made no
  reset, and typed nothing at a console (the plan's rule 5). The plan
  allowed a second session; it was not needed.
- *One probe session*, on 2026-11-24, with the responsible human
  present. Its first start stopped at the step that stages the images,
  before anything was typed at U-Boot and before any image was booted:
  a fault of the run tool's, which `0caf1df1` corrects. That start was
  closed out, and the session ran again on his word, at 21:14:22Z. In
  it every step passed: U-Boot's environment was recorded and
  installed, each of the three images was booted from system reset, and
  the environment was restored, to the bytes that were recorded; the
  preflight after the session equals the one before it. Its public
  record is `mvp/results/20261124-com260-m13-probes/`.

**The soft limits** (the plan's section 9). The responsible human
re-set both, as each tool's commit says:

| What it counts | The plan's limit | Re-set to | Counted lines |
| --- | --- | --- | --- |
| The read tool and its self-test | 1,000 | 1,500 | 1,037 |
| The probe images, their build rules, and their checks, with the run tool | 2,000 | 3,500, then 6,500 | 5,773, of which 80 are the third image's held table and list |

**Nothing was sent** to the vendor or to another project (the plan's
stop 9 and Q9). What the record finds wrong or unclear in the vendor's
documents and trees is in its "Disagreements", for the responsible
human.

## 2. What the record holds

| What | How much |
| --- | --- |
| Rows, each one fact with its class and its citation | 393: 177 under A (what protects memory from the bus masters other than the harts), 84 under B (interrupts), 57 under C (reset), and 75 under D (which device belongs to whom) |
| Rows by class; a row may have more than one | *document* 166, *source* 127, *board-Linux* 116, *probe* 47, *files* 37 |
| The plan's questions A1 to D4 | 18: three answered (B1, B3, and C3), and fifteen partly answered, each saying what is open, and, where the record can say it, what would settle it |
| "Not established" | 25 items, each with its reason |
| "Disagreements": between the classes, and between the documents | 20 items, each with both sides, none reconciled (the plan's rule 3) |

**Held.** Probes P5 and P6 were run on 2026-11-24, and their results
are held under the plan's rule 10, whatever they show (the review
point's section 4). The record lists them as run and held, and says
nothing more of them: it says of them only what the responsible human
decides that it says. Nothing in this page rests on them. The account
below is written from the record's rows alone, and it would read the
same whatever those probes showed.

**Against records of the project's** (the plan's stop 8). Two lines of
the hardware roadmap differed from what the record finds, and the
record's Disagreement 19 gives both sides; M13-5 brought those lines up
to date. The [implementation plan](implementation-plan.md) lists
"GEILEN = 8" among the K3's properties, where the board shows 7 on each
of harts 0, 1, and 2. The plan lets M13-5 bring two such pages up to
date, the hardware roadmap and the glossary, and the implementation
plan is not one of them; so that line stands as it was, and
Disagreement 19 notes it. The review point's expectation for one
probe's values differed too (Disagreement 20). No accepted claim rests
on any of these lines.

## 3. What steps (2) and (3) can rely on, and what they cannot

Step (2) is the device and DMA object model; step (3) is one static
pass-through device path and the I/O service VS domain (S3-C.2). This
account binds neither: it chooses no device and no mechanism (the
plan's section 1), and each step's plan reads the record for itself.
Both steps will need a device, the IOMMU, or DMA, so their plans name
the MVP plan's stop condition 3 for the responsible human's decision
(the M13 plan's section 11).

"Can rely on" means only this: the record holds the fact, with its
class and its citation. Row numbers are the record's.

### How far a fact reaches

- **One board.** Every board fact is from one COM260 board. Another
  board, or another revision of this one, was not read.
- **A document or a source is not the board.** Where they differ from
  what the board shows, the board's observation decides what this board
  does (the plan's rule 3). The count of guest interrupt files is the
  example: 8 by the documents, 7 on each of the three harts that a
  probe ran on.
- **The board's Linux is one kernel.** The *board-Linux* rows are the
  distribution's kernel `7.3.1`, as read on two days. That kernel's own
  source was not among the inputs, so a row that says why its drivers
  act as they do rests on upstream's and the vendor's sources ("Not
  established", item 16).
- **"As booted" is one boot chain.** A *probe* row is one read, at one
  boot through the board's resident boot chain, of the board as U-Boot
  hands it on under the resident firmware, the vendor's OpenSBI 1.6
  (B-66, B-67); that chain is the NOR's, by the MVP plan's S3-E.1. It
  is not the state under Linux. It is also not the state under the
  firmware build of the project's own that M11's boundary uses, which
  boots from a microSD card ([the M11 plan's board
  addendum](mvp-m11-board-addendum.md)): M13 made no such boot (its
  stop 5), and the record's rows on what the firmware configures are
  the resident firmware's and its tree's (inputs OS and FT). A step
  that builds on M11's boundary cannot take an "as booted" row as that
  chain's state; it has to read the state again under that chain.

### A device's memory accesses

Can rely on:

- **Which devices are bus masters**, by the manual (D-38), and which of
  them the board's Linux drives (A-87 to A-102): PCIe ports A, D, and E,
  three USB controllers, UFS, GMAC1, one DMA controller, and the
  microSD card's controller. The devices of D-39 are not bus masters,
  by an inference that the record marks as one.
- **There is an IOMMU, and neither the boot stages whose sources were
  read nor the board's Linux uses it.** It answers at its documented
  address from HS-mode, as version 1.0 of its specification, with
  second-stage `Sv39x4` and `Sv48x4`, MSI translation in the
  pass-through mode, ATS with `T2GPA`, and a physical address size of
  44 bits (A-151 to A-158). As booted it is in `Off` mode (A-160,
  A-161), and `fctl` chooses wire for its interrupts (A-156, A-159):
  source 234 by the manual and the vendor's tree, beside four more that
  the manual names for it (A-57, A-59, B-34). No boot stage whose
  source was read writes it (A-80), and the board's Linux registers
  none (A-131 to A-133).
- **As booted, PCIe ports A, B, and C bypass it** (A-162 to A-164). The
  bypass bits are in a register that also holds the PHY lane matrix
  (A-74, D-30), in a clock and reset unit that Linux drives as a whole
  and that the real-time firmware also maps (C-25 to C-27, D-65).
- **Every source read puts ports A and B behind the IOMMU; the sources
  disagree on ports C and E** (A-69 to A-72; Disagreement 1). In the
  tree that the board's Linux received, ports B and C are disabled
  (A-90).
- **No PCI function on this board has ATS, PASID, or PRI** (A-142), so
  the IOMMU's ATS and `T2GPA` have no device to use them here. Under
  the board's Linux, the root ports' ACS has source validation, request
  and completion redirect, and upstream forwarding on, the four that
  upstream Linux turns on, and translation blocking and egress control
  off (A-143 to A-145); no probe read it as booted.
- **Address widths**: each IOPMP's (A-02 to A-10); and, as the board's
  Linux uses them, the NVMe drive's 64 bits, the Wi-Fi card's 36, and
  GMAC1's 40 (A-137, A-138).
- **The PCIe controllers have inbound address translation**: on port A,
  at least 31 regions, none enabled as booted, and Linux programs none
  (A-110 to A-112, A-139 to A-141, A-168 to A-170).
- **By the manual, an IOPMP passes every access after a power-on reset
  until it is enabled** (A-20, A-21). The firmware's tree, the vendor's
  kernel tree, and the tree that the board's Linux received have no
  node for one, and none of the sources read writes one (A-32, A-33).

Cannot rely on:

- **That the IOMMU sees or stops any device's request.** M13 wrote
  nothing to it and enabled nothing (the plan's rule 6), so no row shows
  it translating or refusing a request. A port whose bypass bit is set
  bypasses it, so its `Off` mode is no bound for that port (A-72, A-77,
  A-164). Which ports' requests it sees is not established (item 6),
  nor is the path of the PCIe controllers' own DMA engines (item 7).
- **An IOPMP.** Each instance's state on this board as booted, who
  enables one, and whether an application hart can reach their
  registers are not established in the record (items 1 and 2): the two
  probes that the review point aims at those registers, P5 and P6, were
  run, and their results are held. The manual says that only the
  vendor's "secure world" configures them, and not what that is on this
  SoC (A-28). So nothing in steps (2) and (3) can rest on an IOPMP
  checking a master's accesses, or on the project being able to program
  one.
- **The inbound translation as a bound.** What a request that matches
  no inbound region does is not established: the controller's databook
  was not among the inputs (item 8). Nor is what port A's root-port
  BARs map: as booted they are two 32-bit memory BARs at bus addresses
  `0x0800_0000` and `0x1000_0000`, where U-Boot puts them (A-171 to
  A-175).
- **Any bound at all, for the masters other than the PCIe ports.** The
  sources read name the IOMMU for PCIe ports alone (A-69 to A-71). The
  record has no row that puts it in the path of the USB controllers,
  UFS, GMAC1, the DMA controller, or the microSD card's controller, and
  the only check for them that the record holds is an IOPMP's (A-03,
  A-08).
- **That a device cannot write to an interrupt file.** A device's MSI
  is an ordinary memory write (A-124). No row of the record shows
  anything that stops a device's write to a hart's S-level interrupt
  file on this board, the monitor's among them (A-125, A-127; question
  A5). By the AIA, a guest's device MSIs are to be translated by an
  IOMMU that the hypervisor configures (A-130), and this IOMMU
  translates MSIs only through MSI page tables (A-79, A-154).

So the record shows no mechanism on this board that bounds the memory
accesses of any bus master other than the harts. That says what the
record's rows hold, the held results apart; it does not say what the
hardware can do.

The bus masters that the board's Linux drives, with what the record
holds for each. The table chooses nothing.

| Device, on this board | An IOMMU in its path, by the sources | Its IOPMP, by the manual | Reset, and what it shares |
| --- | --- | --- | --- |
| PCIe port A, with the NVMe drive behind it (A-87) | Yes, by every source; device IDs in the vendor's tree (A-65); bypassed as booted (A-164) | IOPMP2 and IOPMP8 list "PCIe" (A-03, A-09) | The drive offers function-level reset (C-46). The controller's three reset bits are in an AP PMU register that also holds its mode and its clocks (C-14, C-15) |
| PCIe port E, with the Wi-Fi card behind it (A-89) | By the datasheet and the PCIe page's overview alone (A-69); no IOMMU map in the vendor's tree (A-68), and no bypass bit (A-72) | The same | The card offers function-level reset (C-47). The controller's reset bits: C-17 |
| PCIe port D, with no device behind it (A-88) | Named by no source read | The same | C-17 |
| Three USB controllers (A-92, A-93) | None named by a source read | IOPMP2 and IOPMP7 list "USB3" and "USB OTG"; which controller each name means is not stated (A-94) | One AP PMU register holds the resets and bus clocks of all five USB controllers (C-18) |
| UFS (A-95) | None named | IOPMP2 and IOPMP7 list "UFS" (A-03, A-08) | Its global reset shares a register with its clock (C-21). Its registers have a range of their own (D-27) |
| GMAC1 (A-98, A-99) | None named | IOPMP7 lists "GMAC1", with a source ID from the Secure Configuration unit (A-08, A-44) | Its bus reset shares a register with its clocks (C-22). A range of its own (D-27) |
| One DMA controller (A-101, A-102) | None named | IOPMP2, IOPMP3, and IOPMP7 list "Secure DMA" and "Non-secure DMA" (A-03, A-04, A-08) | Its reset shares a register with its clock (C-23) |
| The microSD card's controller (A-96, A-97) | None named | IOPMP2 and IOPMP7 list `SD`; which controller it means is not stated (A-03, A-08) | It shares a bus reset and a bus clock with two other storage card controllers (C-19), and its 4 KiB page of registers with one of them (D-25) |

### Interrupts

Can rely on:

- **Seven guest interrupt files on each of harts 0, 1, and 2**, by
  `hgeie`, not the documents' eight (B-69 to B-72; Disagreement 2).
- **The S-level APLIC can be read and written from HS-mode.** As
  booted, it is in MSI delivery mode with IE = 0, so that it delivers
  no interrupt; source 200 is delegated to it; and its Guest Index field
  held a nonzero value (B-74 to B-84). The firmware's tree delegates
  sources 1 to 512 to it (B-06).
- **How the board's Linux uses them**: the wired sources in use, with
  their names and their harts, and the MSIs of the PCIe functions (B-52
  to B-58; A-146 to A-150).
- **The M-level controllers are the firmware's**, by the resident
  firmware's source: it keeps them to M-mode, and it writes the
  supervisor MSI address configuration, which belongs to the root
  interrupt domain (B-24 to B-26).

Cannot rely on:

- **That an MSI from the S-level APLIC reaches a guest interrupt
  file.** The probe wrote the Guest Index field and sent no MSI (B-83;
  item 12).
- **The count on harts 3 to 7** (item 12), or the M-level APLIC's state
  as booted, which M13 did not read: the plan's Q5 leaves a read from
  M-mode to a later step's plan (item 25).
- **The manual's table of wired sources as a whole.** It was compared
  with the trees only for this board's devices (item 21). The number of
  identities in an interrupt file differs between the documents and the
  trees (Disagreement 3).

### Reset, clocks, and power

Can rely on:

- **The NVMe drive and the Wi-Fi card offer function-level reset**; the
  root ports offer none (C-46 to C-48).
- **A device's reset bits and clock gates are in registers of units
  that it shares.** For each bus master that Linux drives, the record
  names the register and what else it holds (C-14 to C-24); the USB
  controllers share one register (C-18), and the storage card
  controllers one reset and one clock (C-19). The units that hold them
  are single blocks that Linux drives as a whole, and the real-time
  firmware maps the Main PMU and the AP PMU as well (C-25 to C-27,
  C-44, D-65). It follows that a device's reset or clock cannot be
  handed over by mapping its register: the page holds other devices'
  controls.
- **At least two agents can reset the board through the
  power-management chip.** By the resident firmware's source and tree,
  a system reset goes through the real-time firmware to that chip (C-03
  to C-05); and the board's Linux binds a driver for the same chip's
  reset register (C-37 to C-40; Disagreement 17). The watchdog's path
  and the real-time subsystem's chip reset are others (C-07 to C-10).

Cannot rely on:

- **What each reset scheme resets**: whether it clears an enabled
  IOPMP, or resets the real-time cores (C-11; item 14).
- **The reset lines of the other devices**, which the record does not
  list (item 22).
- **A clock's state.** The clock rows are what Linux's clock driver
  reported at one read, after the boot stages and its own drivers
  (C-49 to C-53). It names no clock for the IOMMU or for an IOPMP
  (C-52).
- **A system reset under M11's boundary.** The firmware build that the
  board runs under it has a reset device that only halts
  (`mvp/docs/claim-boundary.md`).

### Whose a device is, and what devices share

Can rely on:

- **Who touches each device** at boot and at run time, among the SPL,
  U-Boot, the firmware, the real-time firmware, and Linux, as far as
  the sources, the trees, and the board's Linux show it (D-01 to D-22,
  D-51 to D-69).
- **Registers that share a 4 KiB page**, which is the G-stage's grain:
  UART0 with eight other UARTs and two infrared receivers; the
  temperature sensor with one I2C controller; the microSD card's
  controller with another storage card controller; and others (D-23 to
  D-26). UFS, GMAC1, and one USB controller have ranges of their own
  (D-27). The PCIe controllers' registers lie in one range that the
  address map does not divide (D-28).
- **What else devices share**, found so far: a register, a reset, a
  clock, a PHY, a bus, an interrupt source, a power domain, and pins
  (D-29 to D-37, D-71).

Cannot rely on:

- **The lists being complete.** The record says "found so far" (item
  23). What the boot ROM touches is not established, since its code
  was not among the inputs (item 24); nor whether three kinds of
  controller master the bus (item 19).
- **One owner for a device.** The power-management chip is driven by
  the board's Linux on one bus and by the real-time firmware on another
  (D-34, D-71), and the real-time cores' trees enable the application
  side's GPIO block and pin controller, which the board's Linux drives
  (D-15, D-16, D-37).

### The other execution contexts

- **The real-time cores are started at every boot**, by the SPL's
  source (D-06; the MVP plan's S3-E.1, statement 4). Their address
  map holds all of DRAM and most of the application side's address
  space (D-41). Whether an IOPMP checks their accesses on this board is
  not established (D-43). M11's limit already puts them outside its
  boundary, and trusted (`mvp/docs/claim-boundary.md`); nothing in M13
  changes that.
- **The debug module.** Whether JTAG is enabled on this board is not
  established: M13 reads no eFuse (D-50; item 18).
- **The harts without the hypervisor extension.** What runs on them on
  this board is not established (D-46; item 18).

### Caches

- **By the trees that Linux uses, DMA on this SoC is not
  cache-coherent** (A-116); the manual and the vendor's tree make the
  eight HDMA instances coherent (A-103, A-104). Linux's driver path for
  a master that is not coherent cleans, invalidates, and flushes cache
  blocks (A-118).
- **Under M11's boundary each of those three operations traps in a VS
  domain**, by the monitor's source, the M11 plan, and the cache-block
  chapter (A-121 to A-123). A VS domain that drives a DMA device
  therefore cannot issue them itself as the M11 candidate stands. What
  to do about that is for step (3)'s plan; a change to the candidate is
  not M13's to make.

## 4. What this result changes

- **Three maintained pages**: the record, completed; the hardware
  roadmap, in the lines that the record bears on and in its open
  hardware questions; and the glossary, with a row for M13, rows for
  three terms, and two rows brought up to date. The roadmap page and
  the planning index name this result.
- **The AI-assistance disclosure** (`mvp/docs/ai-assistance.md`) gains
  its section on M13-5.

It changes nothing else:

- **No claim.** `mvp/docs/claim.md`, `mvp/docs/claim-boundary.md`, and
  the claim ledger are as they were. M13 is evidence for none of them.
- **No accepted text** but the hardware roadmap's lines that the plan
  lets M13-5 bring up to date: not the MVP plan, the M11 plan or its
  board addendum, the M13 plan, or the review point. The implementation
  plan's line on GEILEN stands as it was (section 2).
- **No path that the proofs' records bind**, no image of the M11
  candidate's, and nothing of the tool lock (the plan's rule 7).
- **On the board, nothing but what the board policy allows** (S3-A.1).
  U-Boot's environment is as it was before the probe session. The
  Beryllium partition holds the three probe images, where it held the
  MVP's, which the probe session's first start removed as it staged its
  own: a session that boots the MVP's images stages them again, as
  every such session does.

## Status record

```text
mvp_m13_result=accepted-if-its-proposing-commit-is-on-the-public-main-with-the-responsible-human's-sign-off;otherwise-proposed
mvp_m13_result_plan=mvp-m13-plan.md;accepted-2026-11-23-ac3bd40f
mvp_m13_result_record=k3-com260-devices.md;393-rows;A-177;B-84;C-57;D-75
mvp_m13_result_questions=18;answered-3;partly-answered-15
mvp_m13_result_not_established=25
mvp_m13_result_disagreements=20
mvp_m13_result_sessions=one-read-session-2026-11-23;one-probe-session-2026-11-24
mvp_m13_result_probes=P1-P2-P3-P4-P7-in-the-record;P5-P6-run-and-held
mvp_m13_result_account=binds-neither-step-2-nor-step-3;chooses-nothing
mvp_m13_result_claim=none
mvp_m13_result_accepted_text_changed=the-hardware-roadmap's-lines-as-the-plan-allows;no-other
mvp_m13_result_sent=nothing
mvp_m13_result_next=MVP-2.0-step-2-under-its-own-plan-at-the-responsible-human's-direction
```
