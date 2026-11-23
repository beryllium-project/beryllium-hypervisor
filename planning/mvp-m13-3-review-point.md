<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M13-3: the review point (probes)

This page is work package M13-3 of the [M13 plan](mvp-m13-plan.md): the
questions of M13's [record](k3-com260-devices.md) that are still open
after the reading (M13-1) and the read session of the board's own Linux
(M13-2), and, for each that a probe image could settle, the probe. It is
put to the responsible human as one reply: `probes: go`, `probes: no`,
or a narrowed list (section 6). It decides nothing else, and changes no
accepted text. Its citations use the record's names for the inputs
(UM, VL, UL74, UB, OS, ES, BL2, and the specifications) and the
record's row numbers; a path without a name is this project's tree at
this page's commit.

**Status: proposed by the commit that adds this page,** on the public
development line. Signing off that commit publishes the question; his
reply decides it. The reply's record is kept in the project's internal
records, with the decision records of M13's packets (the plan's
section 6).

## 1. What a probe could settle

The record's "Not established" list has twenty items. A probe image,
under the plan's rule 6 (HS-mode, harts 0 to 2, the reads that this page
names, and no write but the probe's own CSRs and the registers that this
page names), could settle parts of five of them:

| Record item | What is open | Probe |
| --- | --- | --- |
| 1, 2 (A3) | Each IOPMP's state as booted, and whether HS-mode on an application hart can read an IOPMP's or the Secure Configuration unit's registers | P5, P6 (rule 10: section 4) |
| 6 (A2) | The IOMMU's version, capabilities, and `ddtp`, and the PCIe ports' IOMMU bypass bits, as booted | P2, P3 |
| 12 (B3) | The guest interrupt files of harts 0, 1, and 2: GEILEN, by `hgeie` | P1 |
| 12 (B4) | Whether this S-level APLIC can target a guest interrupt file: whether its Guest Index field holds a nonzero value (P7 sends no MSI) | P7 |
| 15 | Which clocks are on for the IOMMU, the IOPMPs, and the Secure Configuration unit. At probe time, a value that matches the block's documented constants (section 2) shows that the block answered; a stall is consistent with a gated clock, but has other causes. Either shows the state after U-Boot, not under Linux | P2, P5, P6 |

**P4 settles no item.** Item 8 asks what an inbound PCIe request that
matches no inbound region does, and what the root port's BARs map; a
read of the registers answers neither. P4 checks, against U-Boot's
source, the state that U-Boot leaves in port A's inbound translation
and its root port's BARs, which a later step inherits. U-Boot programs
outbound regions alone (UB `drivers/pci/pcie_dw_spacemit.c` and
`drivers/pci/pcie_dw_common.c` program no inbound region), and writes
0 to the address bits of the root port's BAR0 and BAR1 (UB
`drivers/pci/pcie_dw_common.c`:277-289, called from
`pcie_dw_spacemit.c`:519). It writes BAR0's type before it enables
writes to read-only fields (:305-310), so the BARs' low four bits read
as the hardware has them; A-113 and A-114 suggest two 32-bit memory
BARs. So P4 is expected to find no inbound region enabled, and both
BARs' address bits 0. That check is its whole worth; the reply may
leave it out (section 6).

**The other items** need what rule 6 does not allow, or what no probe
can read:

- a device's own memory accesses (items 4, 5, 7, 10, and 11), and an
  inbound request's own path, with the controller's databook, which is
  not among the inputs (8);
- the real-time cores' own view (13);
- for item 14, an enabled IOPMP, which rule 6 forbids making, and, for
  its other parts, documents that are not among the inputs;
- the board kernel's own source (16);
- U-Boot's environment, which stays private (17, rule 8);
- for item 18, rule 6's own sentence, "Facts about harts 3 to 15 come
  from documents, sources, and the board's Linux", and the eFuses,
  which rule 6 forbids reading;
- documents that are not among the inputs (3, 9, and 19).

Item 20 could be settled by a load from `0xF181_C000`, but no input
documents that block's registers, and its driver only writes them (UL74
`drivers/irqchip/irq-aclint-sswi.c`:24, 29). Under this page's reading
of rule 6 (section 2), no probe is proposed for it. M13-5 lists every
item that stays open as not established.

**Clocks and power domains.** Rule 6 bars any read of a block whose
clock or power domain the read session found off. The session found the
clock of none of these blocks off, and no power domain on or off at
all, since Linux registers no generic power domain (C-54). For each
block:

- P2, the IOMMU: the clock summary names no clock for it (C-52), and
  Linux's clock driver models its clock as a fixed factor of
  `pll2_d6`, with no gate (A-64). On at probe time by inference:
  U-Boot drives port A, whose clock it takes from the same PLL (UB
  `drivers/clk/spacemit/ccu-k3.c`:2183-2186), and the `be_`
  environment's load from the NVMe drive makes it do so before every
  probe boot (`mvp/tools/k3-env.sh`:96-100). Whether the IOMMU has
  another gate, or a power domain, was not found.
- P3, a register of the AP PMU: Linux binds the AP PMU's clock unit
  (D-65). On at probe time by inference: U-Boot's and Linux's clock
  drivers write AP PMU registers at every boot (UB `ccu-k3.c`:2183-2186;
  C-44).
- P4, port A: its DBI, master, and slave clocks are enabled for a
  driver (C-49). On at probe time by inference: U-Boot's PCIe and NVMe
  drivers have no remove method, so `booti` leaves port A as U-Boot set
  it (UB `arch/riscv/lib/bootm.c`:37-63;
  `drivers/pci/pcie_dw_spacemit.c`:631-639;
  `drivers/nvme/nvme_pci.c`:36).
- P5, the IOPMPs: the summary names no clock for an IOPMP (C-52), and
  nothing read names one.
- P6, the Secure Configuration unit: the summary names no clock whose
  name holds `sec` or `ciu` (BL2 2026-11-23, clk-summary), and the
  board's Linux binds no driver to the "SEC APB Bus Clock Unit" at
  `0xF061_0000` (UM 6.1, `06_address_map.md`:186), the second APB
  clock unit that the vendor's tree gives it (D-65 against C-25). Which
  clock feeds the unit is not documented.
- P7, the S-level APLIC: Linux binds it (D-66); chapters 7 and 17 name
  no clock for it.
- P1 reads a CSR of its own hart.

A read of a block whose clock or power domain is off may stall. A stall
is a result (rule 6); section 3 says how the session ends one.

## 2. The probes

Each read is of the register's documented width: a CSR access for P1,
and a load at an address that this page names for the others. Rule 6
asks that each read have its documented effect. An input documents every
register below, and no effect when it is read, but for two kinds:
`hgeie`, a CSR that rule 6 itself names and the AIA names once
(`IMSIC.adoc`:550); and P4's address-translation registers, since the
controller's databook is not among the inputs. For such a register this
page reads "its documented effect" as the use that a driver in the
vendor's or upstream's trees makes of it: a probe reads it only where
such a driver reads it, at the driver's width, and so with the effect
that the driver relies on, none. Linux's KVM reads `hgeie` as P1 does
(B-41); Linux's DesignWare driver reads two of each inbound region's
eight registers, so P4 reads those two; and item 20's block, whose
driver only writes, gets no probe (section 1). Section 6 lists this
reading among what `probes: go` accepts.

| Probe | Question | Reads | Writes | Why it is safe |
| --- | --- | --- | --- | --- |
| P1 | B3 | `hgeie` (CSR `0x607`) on each of harts 0, 1, and 2: as booted, then after each write | `hgeie` itself: all ones; then, once it has been read back, 0. Linux's KVM finds GEILEN so (B-41) | A CSR of the hart's own. Every probe hart runs with `sstatus.SIE` clear, as B0's entry leaves it (`bringup/k3-b0/src/head.S`:48-50), so no guest external interrupt is taken whatever the guest files hold; `hgeie` is left 0 |
| P2 | A2 | The IOMMU at `0xC0F0_0000`: `capabilities` (`+0x00`, 8 bytes), `fctl` (`+0x08`, 4 bytes), `ddtp` (`+0x10`, 8 bytes) | None | Read-only fields or plain registers, and the specification allows 8-byte accesses (IOMMU `iommu_registers.adoc`:7-13); the vendor's driver reads the first two (A-60) and the common driver the third (A-62) |
| P3 | A2 | `PCIE_SUBSYS_MGMT`, offset `0x1D8` of the AP PMU at `0xD428_2800`, 4 bytes: the IOMMU bypass bits of ports A to C (A-72; the record's Disagreements 15 and 16) | None | A register with no documented read effect, which the vendor's Linux reads and writes from S-mode (A-75) |
| P4 | None (section 1) | Port A's inbound address-translation regions 0 to 30, the 31 that lie wholly inside its `atu` range of `0x3F20` bytes (A-140): for region i, `CTRL2` and `LOWER_TARGET`, at `0x8030_0000 + 0x200·i + 0x100` plus `0x04` and `0x14`, 4 bytes each (VL `drivers/pci/controller/dwc/pcie-designware.h`:158-184; the base, D-28); the last read ends at `0x8030_3D17`. Then the root port's BAR0 and BAR1 (DBI `0x8000_0000` + `0x10`, `+ 0x14`), which the manual lists (A-113) | None | No input documents the region registers (section 2's reading): Linux's DesignWare driver reads each inbound region's `CTRL2`, for its enable bit, and `LOWER_TARGET` (VL `drivers/pci/controller/dwc/pcie-designware.c`:586, 623, 830), and P4 reads those two alone. The BARs are configuration registers of the root port, with no effect when read. A read-only probe cannot count the implemented regions: Linux counts them by writing each region and reading it back (:802-831), and found 31 (A-139). So P4 reports, for each of the 31, whether it is enabled and its lower target, as booted |
| P5 | A3 | Each of the nine IOPMPs (A-12): `VERSION` (`0x0000`), `IMPLEMENT` (`0x0004`), `HWCFG0` to `HWCFG2` (`0x0008`, `0x000C`, `0x0010`), `ENTRYOFFSET` (`0x0014`), `MDLCK` (`0x0040`), `MDLCKH` (`0x0044`), `ENTRYLCK` (`0x004C`), `ERR_CFG` (`0x0060`), `ERR_REQINFO` (`0x0064`), `DEVICEIDCFG` (`0x0200`), and `SRCMD_EN(0)` (`0x1000`), 4 bytes each (UM `15_security.md`:377-442) | None | Registers whose types are read-only, read-write, write-1-to-set, and write-1-to-clear only: none is cleared or changed by its read. Rule 6 forbids any write |
| P6 | A3 | The Secure Configuration unit at `0xF058_0000`: `DMA_SEC_CTRL_KEY_SEL` (`+0x0`), `MAS_SEC_CTRL` (`+0x8`), `NSAID_CTRL0` (`+0x10`), `NSAID_CTRL1` (`+0x14`), `DDRPORT_USER_CTRL` (`+0x78`), 4 bytes each (UM `15_security.md`:182-322) | None | Read-write or read-only fields, none changed by its read. Two fields select a key: `ECO_KEY_SEL`, bit 31 of the first register, chooses between two values in the one-time-programmable memory, a key's hash and a key, and `BOM_REE_KEY_SEL`, bits 10:8 of `NSAID_CTRL0`, is a "key select" (UM `15_security.md`:189, 219). Each selects; neither holds a key or a key's hash, and this page does not count either as key material (section 6). `MAS_SEC_CTRL`'s bits 2:1 are also described as "DDRC TrustZone disable" and "DDRC TrustZone lock" (UM `15_security.md`:286-287; Disagreement 7); P6 reads them and changes nothing. Rule 6 forbids any write |
| P7 | B4 | The S-level APLIC at `0xE080_4000` (B-08, B-09): `domaincfg` (`0xE080_4000`); and, for source 200, `sourcecfg[200]` (`0xE080_4320`) and `target[200]` (`0xE080_7320`) (AIA `AdvPLIC.adoc`:283-318). Chapter 7's table has no row for sources 197 to 209 (UM `07_interrupts.md`:214-215: its rows for 196 and 210 are adjacent); B-52 to B-58 do not list 200; the firmware delegates sources 1 to 512 to this APLIC (B-06) | Only if `domaincfg` reads `0x8000_0004` (bits 31:24 `0x80`, as every APLIC's do, `AdvPLIC.adoc`:383; IE = 0; DM = 1; BE = 0) and `sourcecfg[200]` reads 0: `sourcecfg[200]` = `0x1` (Detached), read back, and if it does not read back as `0x1`, `sourcecfg[200]` = 0 and no more. Then `target[200]` = `0x1000` (Hart Index 0, Guest Index 1, EIID 0), read back; then `target[200]` = 0, then `sourcecfg[200]` = 0, each read back | With IE = 0, as read, nothing pending is signalled or forwarded (`AdvPLIC.adoc`:392-394). A Detached source's wire is ignored, and its pending bit is set only by a write to `setip` or `setipnum` (:527, 991-993); P7 writes neither, nor `genmsi`. An MSI with EIID 0 would change no interrupt file (AIA `IMSIC.adoc`:58, 209). `target` is cleared while the source is still active, since an inactive source's `target` is read-only zero (`AdvPLIC.adoc`:516-521). P7's own write-back restores both registers, without relying on a reset. The firmware's own tree marks this APLIC disabled (B-08); the vendor's and the board's trees enable it (B-09), and Linux's driver writes both registers (VL `drivers/irqchip/irq-riscv-aplic-main.c`:59-61, 121-123; `irq-riscv-aplic-msi.c`:92-94, 125-130) |

**What P7's read-back shows.** Guest Index is read-only zero unless the
interrupt domain's harts implement the H extension, and must then hold
every value from 0 to GEILEN (`AdvPLIC.adoc`:948-949). A read-back of 1
shows that the field holds a nonzero value. A read-back of 0 leaves B4
open: the field may be read-only zero in an interrupt domain that also
serves harts without the H extension, as this one does in the vendor's
tree (B-46), a case that the AIA's text does not settle. In every case
P7 sends no MSI.

**What the probes write.** Nothing but `hgeie` (P1) and P7's two named
registers of the S-level APLIC, besides the hart's own trap and status
CSRs and the probe image's own memory. In rule 6's words, they write no
IOPMP's or the IOMMU's registers; nothing in the Secure Configuration
unit (`0xF058_0000` to `0xF05F_FFFF`); no eFuse; none of the clock,
reset, and power blocks that the manual's chapter 17 lists; no mailbox;
no I2C, SPI, or QSPI controller; no other hart's interrupt files, and
no M-level interrupt controller; and nothing in the NOR. They read
nothing in the eFuses or in the crypto engine (`0xF070_0000` to
`0xF07F_FFFF`).

**What counts as a read of the register.** A read that returns without
a fault is not necessarily a read of the register: a "Fabric Default
Slave" answers failed checks in the IOPMPs' ranges (A-26), and the
IOPMPs' and the Secure Configuration unit's ranges are both marked
Secure (A-13, A-36). So a value counts as a read of the register only
where it is consistent with the block's documented constants:

- for P5, `HWCFG0` to `HWCFG2` against each instance's configuration
  (A-02 to A-10);
- for P2, the `version` field of `capabilities`, which names the
  specification's version (`0x10` for version 1.0;
  `iommu_registers.adoc`:175-181);
- for P6, whose fields all reset to zero, only a nonzero value in a
  defined field, with every reserved field zero (UM
  `15_security.md`:273, 317).

Zeros everywhere, or values that match nothing documented, leave the
question not established. For rule 10, any value from P5 or P6 is
taken as meeting the trigger (section 4).

**A denied read.** IOPMP2 lists "CPU" among its masters, with source ID
`0x1` (A-03, A-16), and whether an enabled IOPMP checks the harts'
accesses is not established (items 1 and 3). If one does, and denies a
probe's read, the manual's consequences follow: the error is recorded
(`ERR_REQINFO.v` and the error counters, A-24) and signalled on both
the application side and the real-time side (A-29, A-30). That would
change state outside the probe. A read-only search of the real-time
firmware's source (ES, at `e5cd0455`) for `iopmp`, `f2m`, and `m2f`
finds no handler of those sources by name.

## 3. How they are built and booted

- **Three probe images**, so that a stall ends no more than one group.
  Within an image a stall also ends the reads after it: so in image 2,
  P2, whose block's clock rests on the weakest inference, comes last:
  - image 1: P1, then P7;
  - image 2: P3, then P4, then P2;
  - image 3: P6, then P5, its nine IOPMPs in the order of their
    addresses, so that a stall at one IOPMP loses only those after it;
    held under rule 10 (section 4).
- **A boot path of their own** (rule 6), built apart from every path
  that the proofs' records bind (rule 7), in a new directory,
  `bringup/k3-m13/`, with its own build rules and checks; its check
  joins `./mvp/mvp check` through `mvp/tools.mk`. It takes B0's pattern
  (`bringup/k3-b0/`: the entry, the SBI wrapper, DBCN, and SRST) and
  the MVP shim's HSM start (`mvp/shim/mvp-shim.S`), neither under a
  bound path:
  - a RISC-V Image header for U-Boot's `booti`, compared field by field
    with B3's, the header that `booti` accepted in B3's four runs on
    this board (`bringup/k3-b3/README.md`:10-31); B0's ran only by
    kexec;
  - an entry under the resident firmware, which reports SBI 2.0 with
    DBCN and HSM (B-30). The entry reads its hart from `a0` and clears
    `sstatus.SIE`. On a hart above 2 it prints one line and ends by
    SRST before any read (rule 6). Image 1 starts, by SBI HSM,
    whichever two of harts 0 to 2 it did not enter on, and each started
    hart checks `a0` again; images 2 and 3 run on the entry hart alone;
  - SBI DBCN for each line; a trap vector that records a faulting
    read's cause and address and goes on to the next read, since the
    resident firmware hands an S-mode load fault back to S-mode when no
    platform emulates the load, and none of its platforms does (OS
    `lib/sbi/sbi_trap.c`:343-345, `lib/sbi/sbi_trap_ldst.c`:321-334,
    `include/sbi/sbi_platform.h`:653-662; for v1.6, see the QEMU bullet
    below); and SBI SRST at the end.
  - It links at `0x1_0220_0000`: `booti` places an Image at U-Boot's RAM
    base, `0x1_0200_0000` on this board (`mvp/src/mvp-layout.h`:209),
    plus its `text_offset`, here `0x20_0000` (UB
    `arch/riscv/lib/image.c`:36-62), as B3's image ran there. That is
    clear of the resident firmware's PMP regions for DRAM (OS
    `platform/generic/spacemit/spacemit_k3.c`:160-178), and the owner's
    check of the memory that the boot stages reserve, which rule 8 keeps
    private, finds it clear of that too. The preflight's `region-check`
    reads only the MVP layout's extents (`mvp/tools/k3-preflight.sh`:57,
    71), so it does not check this one.
- **The image check** shows, from each linked image, that its table of
  accesses is section 2's list, entry for entry; that its only device
  stores are P7's two registers, and its only CSR writes are `hgeie`
  and the hart's own trap and status CSRs; that image 1's HSM starts
  name harts 0 to 2 alone, and images 2 and 3 make none; and that its
  header and extent are this section's.
- **Each line** names its probe, its register, and either its value or
  the fault's cause and address. The capture check judges the lines'
  form, the entry line, and the run's end, not the values: the values
  are the facts.
- **QEMU first** (M13-4). In the MVP's QEMU rows the probes' addresses
  are RAM: it runs from `0x8000_0000` (`mvp/src/mvp-layout.h`:211) for
  8 GiB (`mvp/tests/run-qemu.sh`:719, 784), to `0x2_7FFF_FFFF`. So the
  probes run under QEMU as B0's rows run
  (`bringup/k3-b0/tests/run-qemu.sh`:33-45, 63-67): with 256 MiB of RAM,
  ending at `0x8FFF_FFFF`, from a second build linked at `0x8020_0000`,
  which differs from the board's build in its link address alone, under
  the firmware of the MVP's firmware-version row, upstream OpenSBI v1.6
  at `bd613dd9`, which the tool lock pins
  (`mvp/tools/lock/tool-lock.conf`:223-225; "v1.6" below). It reports
  SBI 2.0, as the board's firmware does (v1.6
  `include/sbi/sbi_ecall.h`:16-17). All three run on the MVP's `k3-like`
  machine and CPU (`virt` with AIA and seven guest files, and the H
  extension; `mvp/tests/run-qemu.sh`:255-256), image 1 with three harts
  and images 2 and 3 with one. There:
  - P2, P3, P5, P6, and P7 read addresses past RAM. What QEMU does at
    them, a fault or a value, is not established from the inputs, and
    M13-4 records what it does. A fault or a zero fails P7's checks, so
    it writes nothing there;
  - P4's BAR reads at `0x8000_0010` and `0x8000_0014` lie in the
    firmware's own memory, which v1.6 keeps from S-mode (v1.6
    `lib/sbi/sbi_domain.c`:804-814) and whose fault it hands back to
    S-mode (v1.6 `lib/sbi/sbi_trap.c`:343-345,
    `lib/sbi/sbi_trap_ldst.c`:321-337,
    `include/sbi/sbi_platform.h`:653-662): a known fault, which shows
    the trap path from end to end. P4's region reads lie in RAM there,
    and show only that they complete. If QEMU raises no fault past RAM,
    the fault path is shown by P4's BAR reads and by the host tests;
  - this is the pinned v1.6 binary's second use. `mvp/Makefile`'s
    comment, which names its first (`mvp/Makefile`:108-114), lies under
    a bound path, so `bringup/k3-m13/`'s README records the second.
- **On the board**, in one session under the MVP plan's board policy:
  S3-A.1's items 1 to 7, and S3-E.3's items 9 to 13, which stand for
  every session, item 13's never-list among them; with the responsible
  human present at the environment's install and restore (M13-4):
  - the three images staged on the Beryllium partition, under names that
    the stage tool accepts. The stage tool removes every other staged
    image from the partition (`mvp/tools/k3-stage.sh`:211-219), so the
    session replaces the MVP's staged images, which a later MVP session
    stages again;
  - U-Boot's saved environment recorded, the `be_` variables installed,
    and each image selected and booted from system reset in turn:
    images 1, 2, then 3 (section 4);
  - the environment restored, and the environment's record at a fresh
    prompt equal to the first.
- **A run tool of its own**, beside the board tools, which it calls
  unchanged. The MVP's run tool admits only images that the capture
  checker's image check accepts, and changing either checker would move
  the claim ledger's pins (C-10, C-41, C-48, C-52, M11-C02, M11-C03,
  M11-C08). So no ledger pin moves, and no bound path changes. The run
  tool follows the project's rules for privileged tooling, with a
  self-test that shows each refusal, as M13-2's read tool does. It also
  makes the session's public board record, since the MVP's
  `evidence.py --board` refuses an image that its build did not make;
  what is private stays out (rule 8), and so does what section 4 holds.
- **The end of each run, and a stall.** The console tool resets the
  board only for a named reason, and its terminal markers are the MVP's
  and B3's end lines (`mvp/tools/k3-uboot.py`:198-199), which no probe
  prints. So the run tool ends every run, a passing one (the board
  halted by SRST) or a stalled one, with the console tool's
  `reset --hang`, after its own wait. That reason needs U-Boot's
  `Starting kernel ...` with no later line of U-Boot or Fedora; the MVP
  README's open items 145 and 146 bear on it. The dry run shows both
  ends, with the fake U-Boot extended to play a capture that ends
  normally and one that stops after a line (rule 6). If the dry run
  shows that the tools cannot reset the board then, he is told before
  the session, and resets it by hand. Whether a reset ends a stalled bus
  access is not established: if neither the dongle's reset nor a reset
  by his hand ends one, the session stops there, and he power-cycles the
  board.

## 4. Rule 10

A read by P5 or P6 that returns a value meets rule 10's first trigger:
it would show that software in HS-mode on an application hart can read
the registers of an IOPMP or of the Secure Configuration unit. Section
2 says when a value counts as such a read; for the stop, any value from
P5 or P6 is taken as meeting the trigger. A faulting or stalling read
meets none. So, for image 3:

- **Its source**, its table of reads and the code that prints them, is
  kept in the project's internal records from the start, not on the
  public line; section 2 already publishes every read that it makes. It
  is built on the boot path that images 1 and 2 use, at a named commit
  of the public line, and checked and run under QEMU there from the
  internal copy. Its lines count toward the lane's limit (section 5).
- **It runs last** in the session, after images 1 and 2. Its capture is
  read, privately, only after the environment's restore and the
  session's closing steps: no tool judges its values as they come. It
  reads its whole table in its one run, and the stop takes effect when
  its capture is read; the plan allows one probe session, so reads lost
  to an earlier stop could not be made again.
- **If any of its reads returned a value**, that is stop 6: the work
  stops, and he is told, privately, before anything else of M13-4 is
  done. Once he has been told, rule 10's third bullet applies, and
  M13-4 goes on with image 3's results held.
- **Its capture, its run record, and everything from its boot**: each
  line, the run's outcome, the console tool's reset record and its
  reason, any count, and the time of each step. They are kept in the
  private store on the workstation and in the internal records, whatever
  they show, a fault included, so that the holding shows nothing.
- **The session's public record** holds of image 3 only that it was
  staged and ran.
- **M13's record** says of P5 and P6 only what he decides that it says,
  and until then lists them as run and held.

No other probe meets a trigger: none reads or writes an IOPMP, the
Secure Configuration unit, an eFuse, or key material, and P3, P4, and
P7 read or drive devices that the vendor's trees give to S-mode, as
their drivers use them. The owner's check of every probe against each
of rule 10's triggers and the exemption's conditions is in the internal
records.

## 5. Size

The plan's soft limit for "The probe images, their build rules, and
their checks" is 2,000 lines, and the review point estimates it again.
By the work's parts (added lines, tests included; image 3's held table
counted with them, from its internal copy, by the same rule, and
reported in M13's result, M13-5, as a count alone):

| Part | Range | This design |
| --- | --- | --- |
| The boot path: the header, the entry and its hart check, three harts by HSM, the trap path that records a fault and goes on, DBCN, SRST | 600 to 950 | 950 |
| The probes' tables and bodies, all seven | 200 to 400 | 400 |
| Build rules: GCC alone, the QEMU build, and image 3's build from its internal table | 80 to 160 | 100 |
| The image check and the capture check | 350 to 750 | 550 |
| The QEMU driver, with its own build | 70 to 150 | 150 |
| Host tests, with B0's formatting reused | 100 to 250 | 125 |
| The run tool, the session's record, the dry run, and the fake U-Boot's extension | 250 to 700 | 700 |
| **In all** | **1,650 to 3,360** | **about 2,975** |

So `probes: go` comes with the lane's limit re-set from 2,000 to 3,500
lines, which leaves room above this design's estimate; a limit of 3,000
would likely be passed, and stop 10 fire again.

## 6. The reply

- **`probes: go`**: all seven probes, in the three images of section 3,
  under section 4 for image 3, and the soft limit of "The probe images,
  their build rules, and their checks" re-set from 2,000 to 3,500
  lines. It also accepts this page's readings:
  1. for a register that no input documents, rule 6's "documented
     effect" is a driver's use of it: a probe reads it only where a
     driver in the vendor's or upstream's trees reads it (section 2);
  2. P7 writes the S-level APLIC's two registers that section 2 names;
     the plan's rule 6 does not name that APLIC among the blocks never
     written;
  3. the two key-select fields that P6 reads select a value and hold
     none, and are not key material;
  4. image 3 is held whatever it shows, and reads its whole table in
     its one run, the stop taking effect when its capture is read;
  5. item 20 is left without a probe, under the first reading;
  6. a run tool of its own, which also makes the session's public
     record.

  M13-4 follows: the probes written, run under QEMU, the dry run, then
  one board session, with him present at the environment's install and
  restore.
- **`probes: go, limit N`**: the same, with the limit re-set to N.
- **A narrowed list**, for example `probes: P1 P2 P3 P4 P7` (without
  the probes that rule 10 bears on), or `probes: P1 P2 P3 P7` (without
  P4 as well), with the same limit, and with the readings that bear on
  the probes kept.
- **`probes: no`**: no probe; M13-5, the result, follows.

If he prefers image 3 to end at its first read that returns a value, as
rule 10's "the work stops there" may also be read, he adds it to his
reply, as in `probes: go; image 3 stops at its first value`; image 3
then loses every read after that one.

## Status record

```text
mvp_m13_3=proposed-by-the-commit-that-adds-this-page;its-sign-off-publishes-the-question;his-reply-decides-it
mvp_m13_3_items=1;2;6;12;15-in-part;P4-checks-booted-state-only
mvp_m13_3_probes=P1-hgeie;P2-iommu;P3-pcie-iommu-bypass;P4-port-a-inbound-enable-target-and-bars;P5-iopmps;P6-secure-configuration-unit;P7-s-level-aplic-source-200
mvp_m13_3_images=1-P1-P7;2-P3-P4-P2;3-P6-P5-held-under-rule-10-and-run-last
mvp_m13_3_limit=probes-lane-re-set-from-2000-to-3500-with-probes-go
mvp_m13_3_reply=probes-go|probes-go-limit-N|a-narrowed-list|probes-no
```
