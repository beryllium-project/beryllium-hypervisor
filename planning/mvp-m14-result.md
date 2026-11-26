<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# MVP milestone M14: the result

M14 is the second of MVP 2.0's seven steps: the device and DMA object
model (the [MVP plan](mvp-plan.md)'s S3-C.2, step (2), and S3-D.3). The
[M14 plan](mvp-m14-plan.md) bounds it. Its model is
[Revision 5 of security model v1](security-model-v1.md#revision-5-2026-11-25-the-device-and-dma-object-model).
This page is its result, the plan's work package M14-3:

- what was done;
- what the model holds, and where it answers each of the plan's
  questions;
- the model read against [M13's record](k3-com260-devices.md) of one
  K3 COM260 board, and against the emulated machine that the project's
  gates run on: what its classes say of each bus master and of each
  device, and what a device path would have to show for each
  invariant;
- what is not established, and what the model leaves to the plan of
  MVP 2.0's step (3), the device path;
- and what the result changes.

The model is specification. It implements, runs, proves, and tests
nothing, and its invariants are asserted of no image. This page reads
facts against it, and is evidence for no claim. Nothing here says that
a device's memory accesses are confined on any platform, that the
project supports a device, or that a device path exists (the plan's
section 8). It chooses no device and no mechanism. A row that shows
only one mechanism for a bus master says so as a fact of the record or
of a source, not as a decision.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. If that commit is on the
public `main` with the responsible human's `Signed-off-by`, M14's
result is accepted: this page, and the lines of the glossary, the
hardware roadmap, and the roadmap that come with it. M14 is then
complete. The signed commit differs from the one reviewed only by that
line and its committer date. The project's internal records keep both
commit IDs and the instruction.

The acceptance accepts no claim, chooses no device and no mechanism,
and authorizes no step. MVP 2.0's step (3), the device path, needs a
plan of its own, at the responsible human's direction.

## 1. What was done

| Work package | What | On the public `main` |
| --- | --- | --- |
| The plan | Twenty-three questions, eleven rules, three work packages, ten stops | `d0ec2aee`, 2026-11-25 |
| M14-1, the reading | The inputs of the plan's section 2, each at its pin: the specifications; two precedents; upstream Linux, for PCI devices and the RISC-V IOMMU; the emulated machine, from QEMU's source; and M13's record. Revision 5's "Facts" names each with its version. The notes are scratch, which no repository tracks (the plan's section 6) | No commit of its own: the model cites the sources |
| M14-2, the model | Security model v1 Revision 5, appended to the accepted text, with the claim ledger's pin of that file refreshed in the same commit | `5206c07a`, 2026-11-26 |
| M14-3, the result | The model read against the two instances; the [glossary](glossary.md), the [hardware roadmap](riscv-security-hardware.md), and the [roadmap](roadmap.md) brought up to date; this page | The commit that adds the disclosure's section, and this page's commit |

**No session on the board**, of any kind, and nothing was run: no
build, no emulator, no test. The emulated machine was read from its
source alone.

**The soft limits** (the plan's section 9).

| What it counts | The plan's limit | Re-set to | Counted lines |
| --- | --- | --- | --- |
| The model: lines added to `planning/security-model-v1.md` | 900 | 1,100, by the responsible human's sign-off of the model's commit, whose message says so | 1,061 |
| This page | 450 | 600, by the responsible human's sign-off of this page's commit, whose message says so | 569 |

**Review.** An independent, read-only, automated review read the first
draft of the model, and of this page, as a whole, and each later draft
in what had changed, before each was proposed (the plan's rule 11;
Q10). Its findings and their disposition are in the project's internal
records.

**Nothing was sent** to the vendor, to a specification's authors, or to
another project (the plan's stop 9).

## 2. What the model holds

Revision 5 is appended to the security model's accepted text, which it
quotes and does not edit.

| Part | What it adds |
| --- | --- |
| Terms, and facts | A device, with its controls and its persistent state; a bus master; a holder and an owner; an assignment unit; a reach, an enforcing element, an identity, and "confined"; a route and its delivery point; "quiesced"; a control operation and a boot source; the platform description; and a configuration's limit. Each fact has its source |
| R5.1, object classes | Six: `device`, `unit`, `reach`, `route`, `control`, and `platform_description`; and instances for two accepted classes |
| R5.2, invariants | Ten, I29 to I38, in 35 clauses, with 19 readings |
| R5.3 | What would show each invariant, and the negative cases that a device path would have to test |
| R5.4, threat model | Three attackers; the assets, the allowed effects, the required containment, and what stays deferred |
| R5.5, trusted computing base | Nine rows, each with "none" or "assumed" as its evidence today |
| R5.6, notation | `class device { drive interrupt reset }`; a unit as an object, and a unit with a bus master also as a subject; H06 and H07 answered; a fourth instance |
| R5.7, analyses | Five, A9 to A13, and the accepted A1, A3, A5, A6, and A8 read with a unit; the fourth instance worked by hand, with ten variants that fail |
| R5.8 | The records that hold the authority; both triggers for the static device case; the states of a unit; and what the abstract model, the checkers, the scenario's format, and the partition descriptor would gain, with none of them changed |
| R5.9 | The model tried on three instances before it was proposed |
| R5.10, R5.11 | Its scope, the accepted sentences that it reads, what a device would make untrue, and what it does not change |

**The plan's questions, and where the model answers each** (the plan's
section 4).

| # | The question, in short | Where |
| --- | --- | --- |
| 1 | What a device is, as an object, and which of its parts can be assigned apart | The Terms; R5.1, "No part of a device is assigned apart from the rest"; I30; I34 |
| 2 | The assignment unit, and what makes one that cannot be assigned | I30 (a) to (d); "What does not close a unit"; A11 |
| 3 | Who may hold a unit; two holders at once; every device and every bus master accounted for | I29; I30 (d); R5.2, "A unit whose holder is the monitor"; A12; R5.10, for one device with two holders |
| 4 | Where the authority is recorded, and what the configuration's identity covers | R5.8, Part 4 and "Where the authority is recorded" |
| 5 | A device's reach, relative to its owner | I31 (a), (b); A10 |
| 6 | What no reach may include | I31 (c) to (e) |
| 7 | What "confined" means, without naming a mechanism | The Terms; I32; I35 (c); R5.5 |
| 8 | A bus master that nothing confines | I29, with its readings; the Terms, "quiesced"; I30 (d); A12 |
| 9 | H06: authority without a mapping | R5.6, "H06"; I34 (d) |
| 10 | How an interrupt reaches its owner, and what may change a route | The Terms; R5.1; I31 (d); I32 (d); I33 |
| 11 | Which interrupts an owner may receive | I33 (a); A13 |
| 12 | What a device may do by its interrupts alone | I33 (b), (c), (f); R5.4's allowed effects |
| 13 | The states of a unit, and the order of its first handoff | I35; R5.8, "The states of a unit" |
| 14 | A paused, terminated, or failed owner; a system reset; what survives one | I36 (a), (b), (d); I37 |
| 15 | A restart of an owner with its unit kept | I36 (c) |
| 16 | What is left to step (5) | R5.8, Part 6, and the list after the states |
| 17 | The attackers that a device adds | R5.4 |
| 18 | The containment required, and the effects allowed | R5.4 |
| 19 | What joins the trusted computing base | R5.5 |
| 20 | The notation's classes; a device as a subject, an object, or both | R5.6 |
| 21 | H07: when a finer type has security meaning | R5.6, "H07" |
| 22 | The analyses that change, and the new ones | R5.7 |
| 23 | Whether the static device case fires a trigger | R5.8, Part 5: neither fires |

**Three things that the model decides**, which the responsible human
accepted with its commit:

- A bus master that nothing confines is never a VS domain's (I30 (d)).
- A VS domain is given no boot source (I37 (b)).
- What a unit's bus masters do between a system reset and the next
  boot's handoff is bounded by the platform's reset, or the
  configuration's limit names the unit's owner as able to change what
  a later boot runs (I37 (c)).

It also narrows one hypothesis of the implementation plan, as R5.2's
reading of I32 says: against Revision 4's attacker, what installs and
protects a device's confinement after a hart's activation cannot be
HS-mode code on a confined hart.

## 3. The model read against one K3 COM260 board

The facts are those of [M13's record](k3-com260-devices.md), by its
row numbers; "item n" is an item of its "Not established" list. Three
other accepted records of the board are named where they are used: the
MVP plan's S3-A.1 and S3-E.1, and the boundary's claim page
(`mvp/docs/claim-boundary.md`). Each fact keeps its class. "By the
manual" and "by a tree" say what a document or a source has, which is
not the board. "The board's Linux" is one kernel, as it was read on two
days. "As booted" is one read, at one boot through the board's resident
boot chain; it is not the state under the boot chain that M11's
boundary uses (M13's result, section 3). "Inferred" marks a row that
the record itself marks as an inference. A "unit" standing alone below
is the model's assignment unit: the record's clock and reset units (the
manual's regions, C-12) are called blocks here, and the Secure
Configuration unit keeps its name.

**The board as a whole.** M13's result: "the record shows no mechanism
on this board that bounds the memory accesses of any bus master other
than the harts. That says what the record's rows hold, the held results
apart; it does not say what the hardware can do". So the record
establishes enforcing elements for no bus master, and on the record
alone I30 (d) leaves no unit with a bus master that could be assigned
to a VS domain (R5.9). The units below are what the record's relations
join, as far as it lists them. They are not units that could be
assigned.

The tables refer to these five notes by name.

- **The IOPMPs.** By the manual there are nine (A-01). Each identifies
  a master by a static source ID (A-14), and "passes every access after
  a power-on reset until it is enabled" (M13's result, section 3; A-20,
  A-21). The firmware's tree, the vendor's kernel tree, and the tree
  that the board's Linux received have no node for one, and no code
  that writes one was found in the sources read (A-32, A-33). Not
  established: each IOPMP's state on this board as booted, and whether
  any boot stage enables or locks one (item 1); and what the vendor's
  "secure environment" is, and whether an application hart in M-mode or
  HS-mode can reach the IOPMPs' or the Secure Configuration unit's
  registers (item 2). "P5 and P6 were run on 2026-11-24, and their
  results are held." Also not established: what a master receives on a
  denied access (item 4), and which traffic each IOPMP sees (item 5).
  By the manual, only the "secure world" configures an IOPMP, and the
  manual does not say what that is on this SoC (A-28). From that, and
  from what items 1 and 2 leave not established, M13's result concludes
  that nothing in steps (2) and (3) "can rest on an IOPMP checking a
  master's accesses, or on the project being able to program one".
- **The IOMMU.** The sources read name it for PCIe ports alone (A-69 to
  A-71), and disagree on which (the record's Disagreement 1). As booted
  its mode field read `Off`, and the bypass bits of ports A, B, and C
  were set (A-160, A-163). The firmware's tree and the tree that the
  board's Linux received have no node for it (A-81); no boot stage
  whose source was read writes it (A-80); and the board's Linux
  registers none (A-132). Not established: its state and the bypass
  bits under the board's Linux, and which ports' requests it sees
  (item 6).
- **Identities that a register sets.** By the manual, some masters'
  source IDs are set in registers of the Secure Configuration unit
  (A-36), every field of which resets to 0 (A-55). That is the manual's
  reset value. Of what those registers hold on this board, the public
  pages say only that M13's probes "of the IOPMPs' and the Secure
  Configuration unit's registers, P5 and P6, were run on 2026-11-24,
  and their results are held" (the hardware roadmap's line on IOPMP
  ownership; item 2). By I32 (d), whatever sets a master's identity is
  state of I32.
- **Coherence.** "By the trees that Linux uses, DMA on this SoC is not
  cache-coherent (A-116); the manual and the vendor's tree make the
  eight HDMA instances coherent (A-103, A-104)" (M13's result, section
  3). I35 (d) is about every master that is not coherent with the
  harts. Under M11's boundary, each of the three cache-block operations
  that Linux's path for such a master uses traps in a VS domain (the
  same; A-118, A-121, A-123; A-122 inferred): I34 (c) is about those
  operations.
- **Controls.** "a device's reset or clock cannot be handed over by
  mapping its register: the page holds other devices' controls" (the
  same). The board's Linux names one clock and reset block as a
  supplier of every bus master that it drives (C-44), and drives each
  such block as a whole (D-65). So I34 (a) keeps from every owner's
  mappings each register that has one device's control beside
  another's, and I34 (b) has its operations performed for the owner. By
  the manual, one register of that block has the IOMMU's bypass bits
  beside the PHY lane matrix and other controls (A-72, A-74): state of
  I32 beside controls. Not established: the reset lines of the devices
  other than the bus masters that the board's Linux drives (item 22).

### The bus masters

By the manual's IOPMP table and its device chapters (D-38), and, for
the IOMMU and the APLICs, by the model's reading. The second column
has what the record shows of who drives each master: a boot stage; the
board's Linux, once the boot chain has handed on; or a tree that
enables it. "By (a)", "by (b)", and "by (c)" are I30's clauses.

| Master, with the record's rows | Holders (I29) | Enforcing elements that the sources name for it (I31, I32) | What the record's relations join it to (I30) | Interrupts (I33) | Controls, coherence, and persistent state (I34 to I37) |
| --- | --- | --- | --- | --- | --- |
| PCIe port A: its controller and root port (A-82) | U-Boot, by its source and the firmware's tree (D-08); in the probe session it reported the port's link up (D-72). Then the board's Linux, with bus mastering on for the root port (A-87, A-136) | The IOMMU: every source read puts port A behind it, and its bypass bit was set as booted (A-69 to A-71, A-163); device IDs for the port in the vendor's tree (A-65), and no map in the board's (A-81). The IOPMPs: by the manual, two instances list one master, "PCIe", with a fixed source ID at one and one that a register field sets at the other (A-16, A-50); the lists name no port and no function apart. Not established: what an inbound request that matches no inbound region does, and what the root port's BARs map (item 8) | By (a): where an IOPMP is to confine them, everything that the one identity "PCIe" covers; where the IOMMU is, the vendor's tree gives ports A to C device IDs of their own (A-65 to A-67). Not settled by (b): by the manual's map, the PCIe controllers' registers lie in one range "which the map does not divide" (D-28), in which USB port B's controller also lies (A-94); whether a page has registers of two of them is not in the record | By the manual and the vendor's tree, wired sources, and none in the board's tree (B-31, B-32). Under the board's Linux the root port has one MSI, to an address that the record infers to be hart 5's S-level interrupt file (A-146, A-148) | By the manual and the vendor's tree, its reset bits are in registers that also have its mode, its bus numbers, and clock enables (C-14 to C-16): "Controls". "Coherence" |
| The NVMe drive behind port A (A-87) | U-Boot, by its source and the firmware's tree (D-08). Then the board's Linux, with bus mastering on (A-136) | Port A's. To an IOPMP it is "PCIe"; the record has no IOMMU device ID for the drive itself | By (a), as port A. By (c): under the board's Linux the drive offers a function-level reset, and Linux lists that and a bus reset as its methods (C-46); where the act that a configuration uses is the bus reset, (c) joins the drive with every other function below port A, and the record shows none (A-87) | Under the board's Linux, MSI-X (A-149) | Its media persist. U-Boot loads the MVP's image from the drive (S3-A.1, item 1): a boot source, unless everything that U-Boot reads from it to run or to trust is checked (R5.9). "Coherence" |
| PCIe ports B and C (A-82) | None in the record: not enabled in the vendor's COM260 tree (A-86), disabled in the board's (A-90), and their clocks read off under the board's Linux (C-50) | The IOMMU: device IDs for each in the vendor's tree (A-66, A-67); port B is behind it by every source read, and the sources disagree on port C (Disagreement 1); both ports' bypass bits were set as booted (A-163). The IOPMPs: "PCIe", as port A | As port A. By the manual, the PHYs of USB 3.0 ports B to D serve USB or PCIe, "one at a time" (A-91, D-33); which PCIe ports is not in the record. A PHY that a configuration gives to one of several devices closes no unit ("What does not close a unit") | By the manual and the vendor's tree, wired sources, and none in the board's tree (B-31, B-32) | By the manual and the vendor's tree, reset bits of their own (C-17) |
| PCIe ports D and E: their controllers and root ports (A-82) | Port D is enabled in the firmware's tree, and port E is not (D-09); in the probe session U-Boot reported port D's link down (D-72). The board's Linux drives both: port D has no device behind it, and bus mastering is on for port E's root port (A-88, A-89, A-136) | The IOMMU: port D is "Named by no source read" (M13's result, section 3); port E is named by the datasheet and the PCIe page's overview alone (A-69); the vendor's tree has no map for either (A-68), and, by the manual, the bypass field has no bit for either (A-72). The IOPMPs: "PCIe", as port A | By (a), and not settled by (b), as port A, except that the vendor's tree gives ports D and E no IOMMU device IDs (A-68) | Wired sources, as port A's (B-31, B-32). Under the board's Linux the two root ports have no MSI or MSI-X capability, and Linux gives them no interrupt (A-150) | By the manual and the vendor's tree, reset bits of their own (C-17, C-45) |
| The Wi-Fi card behind port E (A-89) | The board's Linux, with bus mastering on (A-136). Boot stages: not in the record | Port E's. To an IOPMP it is "PCIe" | By (a), as port E. By (c): under the board's Linux the card offers a function-level reset, with the same two methods (C-47); as for the drive, a bus reset joins it only with other functions below its port, and the record shows none (A-89) | Under the board's Linux, one MSI, to the address of port A's root port's (A-147) | "Coherence" |
| The PCIe controllers' DMA engines, one in each by the manual (A-83) | None in the record | "the PCIe DMA engines' path, through the IOMMU or not, and with which device ID" is not established (the record's question A1; item 7) | Not in the record. Where an engine is driven through its controller's registers, (b) puts it in that controller's unit | Not in the record | Not in the record |
| USB: five controllers, by the manual (A-91) | The board's Linux drives three, the ones that the vendor's COM260 tree enables (A-92, A-93); the bus clocks of USB 3.0 ports C and D read off (C-50). Boot stages: not in the record | No IOMMU is named for them (M13's result, section 3). The IOPMPs: by the manual, two instances list "USB3" and "USB OTG", each with a fixed source ID (A-16, A-17); which controller each name means is not stated (A-94) | By (a): where an IOPMP is to confine them, the controllers that one name covers, which is not stated. By (b): by the manual's map, port A's controller has a range of its own (D-27). Not settled by (b): port B's lies in the PCIe controllers' range, which the map does not divide (A-94, D-28). Not by (c): by the manual, the PHYs of ports B to D serve USB or PCIe "one at a time" (A-91, D-33), and such a PHY closes no unit | The board's Linux handles the wired sources of two controllers, and maps a third's with no handler (B-52 to B-54) | By the manual and the vendor's tree, one register has the resets and bus clock enables of all five (C-18): "Controls". The boot ROM's USB mode answers `fastboot` (S3-E.1, statement 5); through which controller is not in the record. "Coherence" |
| UFS (A-95) | The board's Linux, with the device runtime-suspended (A-95, C-50). Boot stages: not in the record | No IOMMU is named. The IOPMPs: by the manual, two instances list "UFS", with a fixed source ID (A-16, A-17) | By (b): by the manual's map, a range of its own (D-27). By (c): by the manual, a reset of its own (C-21) | One wired source, which the board's Linux handles (B-34, B-52) | By the manual and the vendor's tree, its reset bit is beside its clock's enable and divider (C-21). Its media persist. On a boot from a card whose `bootfs` holds the vendor's flashing table, U-Boot writes "the first block device that it finds, which is the UFS on this board" (S3-E.1, statement 6). "Coherence" |
| Three storage card controllers: the microSD card's, an SDIO controller, and a third (A-96) | The board's Linux drives the first (A-97); the other two's clocks read off (C-50). On a boot from a card, the SPL and U-Boot read the card (S3-E.1, statements 2 and 6) | No IOMMU is named. The IOPMPs: by the manual, two instances list `SD`, with a fixed source ID (A-16, A-17); "which controller it means is not stated" (M13's result, section 3) | By (a): where an IOPMP is to confine them, the controllers that `SD` covers, if more than one. By (b): by the manual and the vendor's tree, the first two share a 4 KiB page (D-25). Under the board's Linux the card's detect line is an interrupt through the GPIO block (B-56); the last case of (b) joins the card's controller and the GPIO block where that interrupt has a route and a holder of the GPIO block can stop it or change it by an act that is on neither state of I32 nor a control, and the record does not say whether one can. By (c): by the manual and the vendor's tree, one bus reset and one bus clock enable serve all three, and each has a reset bit of its own (C-19, C-20); where the act that a configuration uses is the shared reset or the shared clock gate, the three are one unit | One wired source, which the board's Linux handles (B-34, B-52) | A microSD card is a boot source: the boot ROM tries one before the NOR, and the SPL takes from it what it runs, unchecked (S3-E.1, statement 2). "Coherence" |
| GMAC0, GMAC1, and GMAC2 (A-98) | The board's Linux drives GMAC1, the one that the vendor's COM260 tree enables (A-98, A-99); the other two's clocks read off (C-50) | No IOMMU is named. The IOPMPs: by the manual, one instance lists all three, with source IDs that register fields set (A-08, A-17, A-44): "Identities" | By (b): by the manual's map, GMAC1 has a range of its own (D-27). By (c): by the manual and the vendor's tree, GMAC1 has a bus reset of its own (C-22) | GMAC1: two wired sources, which the board's Linux handles (B-34, B-52) | By the manual and the vendor's tree, GMAC1's reset bit is beside its PHY interface select, its AXI ID mode, and its clocks (C-22). "Coherence" |
| Two DMA controllers, by the manual (A-100) | The board's Linux drives the one that the vendor's tree enables; the other, which the map calls "Secure DMA Controller Config", is disabled there (A-101, A-102) | No IOMMU is named. The IOPMPs: by the manual, two instances list "Secure DMA" and "Non-secure DMA" with different fixed source IDs (A-16, A-17); at a third the two "share one source ID and count as one device" (A-04, A-18); and by default the Secure DMA shares the other's source ID, with a register's bits that mark channels as secure (A-52) | By (a): one unit, where an element that is to confine them gives both one source ID. By (b): a DMA controller is in the unit of each device for which it moves data; the record has no list of those, and one inferred row cites the serial controllers' DMA properties in the vendor's tree (D-39) | One wired source, which the board's Linux handles (A-101, B-52) | By the manual and the vendor's tree, the driven one's bus reset and bus clock are in one register (C-23). "Coherence" |
| HDMA, eight instances; and HSDMA (A-103, A-105) | HDMA: the vendor's tree enables all eight, and the board's tree has no node for them (A-104); a clock named for them is enabled with no user device (C-51). HSDMA: none in the record | HDMA: "Which IOPMP checks the HDMA instances is not stated" (A-105). HSDMA: by the manual, an instance of its own, with one master (A-06, A-18). No IOMMU is named | HDMA, by (c): by the vendor's tree, the eight instances share one bus reset and one clock, and each has a reset of its own (C-24); where the act that a configuration uses is the shared one, the eight are one unit. HSDMA: not in the record | Not in the record | By its source, the resident firmware releases "the DMA subsystem's reset" at cold boot, in the clock and reset block that has HDMA's (C-24, C-28). HDMA is coherent, by the manual and the vendor's tree: "Coherence" |
| eSPI, the GPU, the VPU, the ISP, the display, ETR, UCIE, and the Security Engine (A-106); audio and the 2D engine (A-08, A-42) | The board's Linux drives none of the first eight (A-107). By the firmware's tree, the SPL drives eSPI (D-07). Otherwise not in the record | No IOMMU is named. The IOPMPs: by the manual, each but the 2D engine is on one instance or two (A-03, A-07, A-08, A-10). Its source ID is fixed, or a register field sets it (A-16, A-17, A-40 to A-49: "Identities"), or, for ETR, the manual's entry is "TBD" (A-43); for the ISP and one display, which field is disputed (the record's Disagreements 8 and 9). "No IOPMP instance lists V2D", the 2D engine (A-42) | Not in the record | Not in the record | The vendor's tree has power domains for the VPU, the GPU, audio, and the two displays (C-32). Their reset lines: item 22 |
| The debug module's bus access (D-38) | By the manual, JTAG "can be routed to the X100 and A100 harts or to the RCPU" (D-47). "Whether JTAG is enabled on this board" is not established (M13's result, section 3; item 18) | The IOPMPs: by the manual, one instance lists it, with source IDs that register fields set (A-07, A-37, D-49) | Not in the record | Not in the record | By the manual, its "sysbus" mode "reaches on-chip resources through the System Bus Access port, past the CPU" (D-48). Revision 5 defers the debug module (R5.4) |
| The real-time side's DMA engines and its GMAC (A-109) | One of the real-time cores' trees enables two of them, and the vendor's COM260 tree enables the third for Linux (A-109, D-19) | "which IOPMP checks them is not stated" (A-109; item 10) | Not in the record | By the manual, the real-time side's audio DMA and GMAC signals are also interrupt sources of the application side (B-49) | Not in the record |
| "CPU", `REE_W`, and `REE_R` among the IOPMPs' masters (A-108); and QSPI, the CAN-FD controllers, and the I2S controllers | None in the record | "The manual lists them as IOPMP masters and does not say what they are" (A-108; item 3). Whether the last three master the bus is not established (item 19) | Not in the record | Not in the record | Not in the record |
| The APLICs, which the record infers to be no masters (D-39). By the model's reading they are: by the manual an APLIC has "MSI output mode only" (B-01), and "An interrupt controller that forwards a wired interrupt as a message issues a write of its own" (R5.2, I29's reading) | The M-level one: the resident firmware, by its source, which keeps it to M-mode (D-17, B-26). The S-level one: the board's Linux, under which it forwards its sources as MSIs (D-66, B-29) | None named | They close no unit: a controller that passes a unit's interrupts on as state of I32 directs closes none ("What does not close a unit"). As a master of the third kind, an APLIC is no VS domain's (I29's reading) | By the firmware's tree, the M-level one has 512 sources, all delegated to the S-level one (B-06) | By its source, the resident firmware writes the M-level APLIC's MSI address configuration for both levels, and does not set its lock bit (B-24); by the AIA, the machine configuration's lock bit locks both (B-25). Its state as booted is not established (item 25). The addresses to which a controller sends its messages are state of I32 (I32 (d), with its reading) |
| The IOMMU (A-56), which the manual's list of masters does not have (D-38). By the model's reading it is one: an IOMMU "is a bus access initiator for its implicit accesses" (R5.2, I29's reading) | None in the record: "The IOMMU", above | None named for its own requests | None: its registers and tables are state of I32, in no recorded reach and no mapping (I31 (c), I32 (c)). As a master of the third kind, it is no VS domain's (I29's reading) | By the manual, five wired sources (A-59); as booted its `fctl` chose wire-signalled interrupts (A-159) | Where it writes of its own accord is state of I32 (I32 (d)). Not established: item 6; and whether its clock is on under the board's Linux (item 15) |

The real-time cores are in the manual's list of masters (D-38). Under
Revision 5 a core that runs software of its own is an execution
context, and no bus master (R5.2, I29's reading): they are in the third
table.

### Devices that are not bus masters

The record infers which devices are not masters (D-39). The last
column asks I30 (d)'s questions of each: whether, once the boot chain
has handed it on, the firmware or another element that M11's limit
trusts drives it, other than to do for it what I32 to I36 have it do,
or depends on it; and whether it is a boot source (I37). Of the
firmware build that M11's boundary uses, the record does not say what
it drives; the column reports the resident firmware, the boot chain,
and the real-time firmware.

| Devices, with the record's rows | Holders (I29) | What the record's relations join (I30) | Interrupts (I33) | The trusted computing base, and boot sources (I30 (d), I37) |
| --- | --- | --- | --- | --- |
| UART0, eight other UARTs, and two infrared receivers (D-23) | UART0: the SPL and U-Boot, by the firmware's tree, and the board's Linux (D-01, D-02). The others: not in the record | By (b): one 4 KiB page, by the manual's map, so one unit | UART0's source, which the board's Linux handles (B-52) | The resident firmware's tree names UART0 as the console (D-01) |
| The power-management chip, with I2C8, the serial controller whose range runs into I2C8's page, and the real-time side's I2C bus (D-24, D-34) | Two at once: the board's Linux drives the chip on I2C8, as the SPL and U-Boot do before it, and the real-time firmware drives it on its own bus, by its source and tree (D-03 to D-05, D-34) | By (b): the chip is driven through both controllers, so one unit with both, and with the controller in I2C8's page | I2C8's source, which the board's Linux handles (B-52). The chip's own source serves two RPMI nodes in the vendor's tree, the real-time clock and the power key, and the chip's own node in the board's, where it is mapped with no handler (D-35, B-36, B-54) | Yes. By their sources, the real-time firmware drives the chip, and the resident firmware's system reset is a request to the real-time firmware (D-04, C-03). On these rows I30 (d) bars the unit: it has a second holder |
| I2C0, with the real-time clock in its page and a Type-C controller on its bus (D-26, D-67) | The board's Linux, for I2C0 and the Type-C controller (D-64, D-67). The clock: not in the record | By (b): one page, and a chip on the bus. Under the board's Linux the Type-C controller's interrupt comes through the GPIO block (B-56): the last case of (b), as for the microSD card's detect line | I2C0's source, which the board's Linux handles (B-52) | By the timer chapter, a watchdog reset spares the real-time clock (C-02); the clock and reset chapter names other registers (C-01; the record's Disagreement 5) |
| I2C6, with the temperature sensor in its page and a sensor chip on its bus; I2C1 and I2C2, each with an EEPROM, and I2C4 in I2C2's page (D-24, D-26, D-67) | The board's Linux, for the controllers and the chips on them (D-64, D-67). I2C4: not in the record | By (b): each page, and each chip on its bus | The sources of I2C1, I2C2, and I2C6, which the board's Linux handles (B-52) | The EEPROMs' contents persist. Which I2C device is the board's identity EEPROM is not in the record |
| The GPIO block with its edge block, and the pad configuration block (D-24, D-37) | The board's Linux drives both, and the real-time cores' trees enable them (D-15, D-16, D-37): M13's result counts them among the devices for which it cannot rely on one owner | By (b): the two GPIO blocks share a page; the GPIO block carries the microSD card's detect line and the Type-C controller's interrupt (B-56). Pins close no unit where only the configuration, or a holder that the trusted computing base names, sets them ("What does not close a unit") | The GPIO block's source, which the board's Linux handles (B-52); by the manual, the real-time side also takes the GPIO signals (B-50) | Yes: by its source, the real-time firmware can shut the board down through a GPIO, where its configuration names one (C-06). On these rows I30 (d) bars the unit: a second holder, or holders that are not established |
| The clock and reset blocks (C-12) | The board's Linux drives five, each as a whole (D-65). One real-time core's tree maps three (C-26); the record infers that both can write two of them (C-27). By their sources, U-Boot writes the register that has the PHY lane matrix as it probes a PCIe port (A-176), and the resident firmware writes one block at cold boot (C-28) | Their registers are controls, and one has state of I32 (A-72): I34 and I32 keep them from every owner. A register that has one device's control beside another's closes no unit where whatever performs the operation changes that device's bits alone ("What does not close a unit") | Not in the record | Yes: whatever performs control operations is in the trusted computing base (I34 (b)) |
| The interrupt files (the IMSICs) and the ACLINT (D-17, D-18) | By its source, the resident firmware configures the M-level files and keeps them to M-mode (D-17, B-26), and builds drivers for two parts of the ACLINT (D-18). The board's Linux drives the S-level files, and claims the ACLINT's third part (D-66, D-18) | None: an interrupt file is where a route can end, and the state that routes an interrupt is state of I32 (I32 (d)) | Not a device's | Yes. Not established: items 11, 12, 13, 20, and 25 |
| The IOPMPs, and the Secure Configuration unit (A-12, A-36). The IOMMU is among the masters, above | None in the record: "The IOPMPs", above | None: their registers are state of I32, in no recorded reach and no mapping (I31 (c), I32 (c)) | By the manual, the IOPMPs signal a violation by wire, on sources that reach both sides (A-25, A-29, B-48) | Whatever writes the state of I32 is in the trusted computing base (R5.5). Not established: items 1, 2, and 15 |
| Boot media that are not masters: the NOR flash and the identity EEPROM; and the eFuses (S3-E.1, statements 1 to 3; D-60) | The boot ROM, the SPL, and U-Boot. The board's Linux has no SPI device (D-68) | Not in the record | Not in the record | Boot sources: the SPL takes what it runs from the NOR, unchecked, and the EEPROM's product name chooses the firmware's device tree (S3-E.1, statement 2). What the boot ROM checks, and the eFuses' state, are not established (statement 7) |
| The watchdog and the DDR controller (C-07, D-07) | The boot chain, before the handoff: by its source U-Boot resets the system through the watchdog, and by the firmware's tree the SPL drives the DDR controller. The board's Linux registers no watchdog (C-41) | Not in the record | Not in the record | The DDR controller: whatever runs from memory depends on it. The watchdog: for after the handoff, the record has that the vendor's tree enables its node (C-08); and that the board's tree has none, the board's Linux registers none, and the watchdog's clock gates read off (C-09, C-41 to C-43) |
| PHYs 2 to 4 (D-33) | Not in the record | By the manual they "serve PCIe or USB 3.0 ports B to D, one at a time" (D-33), chosen by the lane matrix (A-74). A PHY that a configuration gives to one of several devices closes no unit; one that two use at once joins them (I30 (c)) | Not in the record | The lane matrix's register also has state of I32 (A-72) |

By the manual, five interrupt sources each carry two signals (B-38):
by (b), devices that can raise one routed source are one unit. The
record has rows on a few more devices that are not masters. One is
I2C3, which the map marks Secure: the firmware's tree and the vendor's
COM260 tree enable it, and the board's tree has no node for it (D-13,
D-14). For the rest of its list the record shows no holder and no
relation.

### Other holders, and other execution contexts

I29 has every device's holders listed, "whatever outside the
configuration drives it or depends on it" (R5.8), and I28 names the
execution contexts.

| Context | What the record shows it driving | What it can reach, and what is not established |
| --- | --- | --- |
| The boot ROM | It reads the boot information, tries a microSD card before the NOR, and has a USB mode (S3-E.1, statements 1, 2, and 5) | Its code is not among the record's inputs: what it reads or writes of any device is not established (item 24), nor what it checks (S3-E.1, statement 7) |
| The SPL | By the firmware's tree: UART0, the power-management chip, the DDR controller, and eSPI (D-01, D-03, D-07). By its source, it starts the real-time cores' firmware at every boot, takes what it runs from its boot medium, unchecked, and at every boot from the NOR writes the flash's status register (D-06; S3-E.1, statements 2 to 4) | Not in the record |
| U-Boot | By the firmware's tree: UART0 and the power-management chip (D-01, D-03). By its source: PCIe port A and the NVMe drive (D-08); the register that has the PHY lane matrix, and the root port's BARs (A-173, A-176); the eFuses and the watchdog (D-60, C-07). At every boot it clears three bits of a register of the chip, and at every boot from the NOR it writes the flash's status register; it writes a training record to the NOR after every full training of the memory, and the identity EEPROM under conditions (S3-E.1, statement 3) | How it chooses the tree that the board's Linux receives is not established (item 17) |
| The resident firmware, OpenSBI 1.6 (B-66) | By its source: the M-level interrupt controllers and the delegation (D-17); one clock and reset block at cold boot (C-28); a system reset, by a request to the real-time firmware (C-03). It writes no IOMMU (A-80) | "No PMP region of the resident firmware's root OpenSBI domain covers the IOPMPs' registers or the Secure Configuration unit; whether the bus itself refuses an access from S-mode or HS-mode there is not established" (A-35) |
| The firmware build that M11's boundary uses | Not in the record: "the record's rows on what the firmware configures are the resident firmware's and its tree's" (M13's result, section 3) | The boundary's limit trusts it |
| The real-time cores' firmware | The SPL starts it at every boot (D-06). By its source and tree, it drives the power-management chip (D-04). One core's tree maps three of the application side's clock and reset blocks (C-26), and the cores' trees enable the GPIO and pad configuration blocks, a DMA engine, and a GMAC (D-15, D-37, A-109) | By the manual, the cores' address map has "all of DRAM" and most of the application side's address space (D-41). Whether an IOPMP checks its accesses is not established (D-43; item 10). The boundary's limit puts those cores "outside the boundary and trusted" |
| The eight harts without the hypervisor extension | "what runs on the A100 harts on this board" is not established (D-46; item 18) | The boundary's limit: they are "started by nothing in the firmware or the monitor, by their sources" |
| The debug module | By the manual, JTAG can be routed to the harts or to the real-time cores (D-47) | "Whether JTAG is enabled on this board" is not established (item 18). Revision 5 defers it (R5.4) |

### Invariant by invariant

The second column is R5.3's first column, word for word or cut short
where the cut loses no condition. R5.3 also has the negative cases.

| # | What a device path would have to show | What the record has that bears on it | What the record does not establish |
| --- | --- | --- | --- |
| I29 | "The platform description lists every device and every master of the platform, with each device's holders and each master's identities, checked against a source that its generator did not use; each master's kind, with its evidence; and, for each quiesced device, what keeps it so" | The masters, by the manual (D-38); who drives each device, "as far as the sources, the trees, and the board's Linux show it" (M13's result, section 3; D-01 to D-22, D-51 to D-69, with D-20 and D-55 inferred); the other contexts, by the manual, and what the board's Linux shows of the A100 harts (D-40 to D-50) | Items 3, 10, 18, 19, and 24. The record's answers on who drives each device, and on which devices are masters, are partial (its questions D1 and D3) |
| I30 | "Each unit's closure, computed offline from the platform description, whose relations are checked against a source that its generator did not use" | By the manual's map, pages and ranges (D-23 to D-28); by the manual and the vendor's tree, resets and clocks (C-14 to C-24), and the board's Linux's supplier links (C-44); PHYs, by the manual (D-33); a chip on two buses, by the sources, the trees, and the board's Linux (D-34); shared sources, by the manual and the trees (B-38, D-35); identities, by the manual and the vendor's tree (A-14 to A-19, A-36 to A-55, A-65 to A-68) | Items 5, 7, 8, and 22; item 23, the list of what devices share, which is "found so far"; and which controllers the names "USB3", "USB OTG", and `SD` mean (A-94; M13's result, section 3) |
| I31 | "For each master, each identity that it can claim, and each kind of request that it can issue: a request inside the recorded reach succeeds, and one outside is refused" | The sentence of M13's result, above; the IOMMU as booted (A-160, A-163); by the manual, the IOPMPs' address widths and identities (A-02 to A-19); address widths under the board's Linux (A-137, A-138) | Items 1 and 2, with the notes' sentence on P5 and P6; items 4 to 8, and 11 |
| I32 | "The state in force, read back once the elements have taken up the last change, compared offline with the sealed configuration by a check that is independent of what derived it; and, by I31's cases, that the elements apply what was read back" | What sets identities, by the manual (A-36 to A-55); the bypass field, by the manual and as booted (A-72, A-163), in a register that U-Boot writes, by its source (A-176); the IOPMPs' locks, by the manual (A-21 to A-23); the IOMMU's capabilities as booted (A-151 to A-160); the M-level APLIC's MSI address configuration, which the resident firmware writes and does not lock, by its source (B-24), and whose lock, by the AIA, locks both levels' (B-25) | Items 1, 2, 6, 8, 15, and 25. The probes show the IOMMU's state "only as booted" (item 6) |
| I33 | "Each source's interrupt arrives at its owner, on its owner's hart, and nowhere else; no other hart takes a trap for it" | Wired sources, by the manual and the trees (B-31 to B-38); MSIs under the board's Linux (A-146 to A-150, with A-148 inferred); the interrupt files, by the AIA, the manual, the trees, the sources, and the board's Linux (A-124 to A-126, B-10 to B-16); seven guest interrupt files on each of harts 0 to 2, which the record infers from a probe's reads (B-69 to B-73). "No row of the record shows anything that stops a device's write to a hart's S-level interrupt file on this board, the monitor's among them" (M13's result, section 3) | Items 11, 12, 13, 20, 21, and 25 |
| I34 | "Each control operation that an owner may ask for, and each access that is made for it, acts on its unit alone, and leaves what the state of I32 allows as it was" | By the manual and the vendor's tree, resets and clocks, and what else their registers have (C-14 to C-24, A-72, A-74); the blocks as wholes, by the manual, the trees, and the board's Linux (C-12, C-25, C-26, D-65); function-level resets under the board's Linux (C-46 to C-48); cache-block operations, by the documents, the sources, the trees, and the board's Linux (A-116 to A-123, with A-122 inferred) | Items 9, 14, 15, and 22 |
| I35 | "The order, from the boot code's own record, with the unit quiesced before the rest" | What the boot chain hands on, as booted: port A's link up, the bypass bits set, the lane matrix (D-72, A-163, A-165); by the manual, an IOPMP passes every access after a power-on reset until it is enabled (A-20, A-21); coherence, by the manual and the trees (A-103, A-104, A-116) | Items 1, 9, and 24. Each "as booted" row is the resident chain's |
| I36 | "No request of a paused, terminated, or failed owner's unit reads or changes anything, and no interrupt of it is delivered, unless Revision 4's attacker on the owner's hart starts the unit again (I38's row)" | The reset schemes, by the documents (C-01, C-02, C-11); function-level resets under the board's Linux (C-46 to C-48). Under M11's boundary the firmware's reset device only halts (M13's result, section 3) | Item 14: which reset schemes clear an enabled IOPMP and reset the real-time cores. Item 22 |
| I37 | "No assigned unit is a boot source, by the platform description and the boot chain's own configuration"; and, for each assigned unit with a master, "that the platform's reset bounds the master, or the sentence of the limit that names the unit's owner" | The boot sources, as R5.9 lists them. After a power-on reset, by the manual, an IOPMP passes every access (A-20); and, after reset, the record infers that three PCIe ports bypass the IOMMU (A-72, A-73). What the boot chain writes at every boot (S3-E.1, statement 3) | Items 14 and 24; what the boot ROM checks, and the eFuses' state (S3-E.1, statement 7) |
| I38 | "I31's and I33's evidence, with the hart's profile as the bound" | On this board, with plain PMP, "M-mode's printed record showed each of the monitor's three harts confined, with its profile's entries" (the boundary's claim page). That is diagnostic evidence from one board, with what M-mode prints as its only witness | None of this is about a device: "No scenario assigns one" (I22 (c)), so no profile includes a device's registers |

**What the model's terms could not place** on this board: the debug
module, which Revision 5 defers (R5.4); and the devices with more than
one holder, which the model places only as units that I30 (d) bars
(R5.9, R5.10): the power-management chip, and the GPIO and pad
configuration blocks. Every other fact of the record fits a class, a
clause, or a reading, if only as a fact that a platform description
would mark as not established.

## 4. The model read against the emulated machine

QEMU's `virt`, from upstream's source at the tag `v10.2.2`
(`f8ed8165`); a file is cited by its path at that tag, and the
project's own files by their path here. The gates run a
distribution's build of that release (`mvp/tools/lock/tool-lock.conf`;
for the evaluator, `mvp/tools/lock/closure.txt`), whose patches and
build configuration were not read. Nothing was run,
so this section shows no invariant: it says what the source has that a
device path's plan could use, and what it lacks.

### The machine as the gates configure it

The gates' `k3-like` row runs `virt,aia=aplic-imsic,aia-guests=7` with
eight harts, no added device, and no IOMMU (`mvp/tests/run-qemu.sh`).
One gate, the U-Boot rehearsal, adds a disk
(`mvp/tests/uboot-rehearsal/run-qemu-uboot.py`): the table's last row.
The gates' other rows run `virt` in that configuration, or in one of
three more: `rva23`, without guest interrupt files; and `plic` and
`no-sstc`, which have a PLIC in place of the APLICs and the interrupt
files. None of them adds a master, and this section reads the `k3-like`
configuration. The CHERI check's runs use another emulator
(`mvp/tools/cheri-check.sh`), which was not read.

**Holders (I29).** No device has the monitor as its holder: "The
monitor touches no device. Its console and its reset go through
firmware calls" (the M11 plan, F17). Which devices the firmware drives
was not read. In the rehearsal, U-Boot drives the disk before it hands
on. The machine has one array of harts, and no other execution context
(`hw/riscv/virt.c`). The gates' oracle reads two devices' registers
from outside the machine, after a run (`mvp/tests/qemu_oracle.py`). The
hostile-monitor images aim at devices' registers, and expect the hart's
physical access profile to deny each access
(`mvp/scenarios/anchor/breach.json`, `breach-control.json`).

| Device, with its file | A bus master, or not | What it shares: its unit (I30) | Interrupts (I33) | Controls and reset (I34 to I36) | Persistent state; boot source (I37) |
| --- | --- | --- | --- | --- | --- |
| The test device (`hw/misc/sifive_test.c`) | Not one | Alone in its 4 KiB page; no interrupt source | None | Its register asks for the power-off or the reset of the whole machine, whoever writes it. In the gates a reset request ends the run (`mvp/tests/run-qemu.sh`; `system/runstate.c`) | None |
| The real-time clock (`hw/rtc/goldfish_rtc.c`) | Not one | Alone in its page; one wired source of its own | Wired, to the M-level APLIC | Its model defines a reset | Not read |
| The M-level software-interrupt and timer devices (`hw/intc/riscv_aclint.c`) | Not one | One device for all harts: every hart's software-interrupt bit in one page, every hart's timer compare value in another, and one time value for all | Lines to each hart's M-level software and timer interrupts, with no route | Its model defines a reset | None |
| The M-level APLIC (`hw/intc/riscv_aplic.c`) | A master: its MSI writes go to system memory with nothing between, at an address from its own registers, which a lock bit of its own freezes. It writes one for each source that is pending and enabled, whether a wire or a write to a set-pending register made it pending, and one for each write to `genmsi`, which names no source | Several sources' registers in each page; it takes every wired source of the machine | It writes MSIs to M-level interrupt files, or passes a delegated source to the S-level APLIC | Its model defines no reset | None |
| The S-level APLIC (the same file) | A master: MSI writes to system memory, at an address that the M-level APLIC's registers give | As the M-level APLIC. A wire reaches it only by delegation; its registers configure any source, delegated or not | MSIs to S-level and guest interrupt files, by hart and guest index | Its model defines no reset | None |
| The M-level interrupt files, one for each hart (`hw/intc/riscv_imsic.c`) | Not one: each is an interrupt file, M-mode's | One interrupt file to a page | A 4-byte write of an identity at the start of the page makes that identity pending, whoever writes | Its model defines no reset | None |
| The S-level interrupt files: for each hart, one S-level file and seven guest interrupt files (the same file) | Not one | One interrupt file to a page | As above. A hart's first page raises its S-level external interrupt, and each later page a guest external interrupt | Its model defines no reset; each file can be cleared through CSRs | None |
| The PCIe host bridge (`hw/pci-host/gpex.c`), with only its own function on its bus in the gates | Not one: neither the bridge nor its function has a request of its own. Its windows, at fixed addresses, pass harts' accesses on to the registers that bus numbers and BARs place behind them; by the model's Terms those are the harts' accesses | Each function's configuration registers have a 4 KiB page of their own, found by bus and function number (`hw/pci/pcie_host.c`) | The wired interrupts of all functions arrive on four shared APLIC sources | A bus reset of its functions (`hw/pci/pci.c`) | None |
| The UART (`hw/char/serial.c`) | Not one | Alone in its page; one wired source of its own | Wired, to the M-level APLIC | Its model defines a reset | None; its output goes to a host file |
| Eight memory-mapped virtio transports (`hw/virtio/virtio-mmio.c`), empty in the `k3-like` row | Not one while empty | Each alone in its page, with one wired source of its own | Wired, to the M-level APLIC | Its model defines a reset; with a device behind it, a status write of zero resets that device | None while empty |
| The firmware-configuration device (`hw/nvram/fw_cfg.c`) | A master: a DMA engine, which a write to its DMA-address register starts. It reads its descriptor, and writes data and status, through system memory, with nothing between | Alone in its page; no interrupt source | None | Its model defines a reset | Its items come from the host |
| Two flash banks (`hw/block/pflash_cfi01.c`) | Not one | Each in an extent of its own; no interrupt source | None | A reset clears its command state only | In the gates no drive backs either bank: its array is host memory for the run, which only the flash's program and erase commands change, and which survives a system reset. With a drive, the machine boots from the first bank (`hw/riscv/virt.c`), and a write reaches the drive's image: not configured |
| In the U-Boot rehearsal alone: a virtio block device on one of those transports (`hw/virtio/virtio-mmio.c`, `hw/virtio/virtio-bus.c`; the device's own model was not read) | A master: its queue and data requests go to system memory with nothing between, started by a queue-notify write | Its transport's page, and that transport's one source | Wired, to the M-level APLIC | A status write of zero resets it, and so does a system reset. The gate runs with `-no-reboot` | Its disk image, a host file. It is a boot source: U-Boot loads the image from it and runs it with no check before |

A platform bus is created, and is empty. The boot ROM's region is no
device's: the host's loader writes it. The PLIC, the S-level
software-interrupt device, and the system IOMMU model are not created
in this configuration.

So, as the `k3-like` row and the rehearsal configure it, the machine
has three kinds of bus master besides the harts (each APLIC, the
firmware-configuration device, and in one gate a virtio disk), no
enforcing element in the path of any of them, and no device whose
holder is the monitor. A unit with one of those masters could not be
assigned to a VS domain: I30 (d) bars a unit for whose master the
platform description establishes no enforcing elements.

### What QEMU offers for a device path

None of this is configured by any gate. It is what the source has, and
no choice among it is made here.

| Device, with its file | A bus master; and what an IOMMU model sees of its requests | What it shares: its unit (I30) | Interrupts (I33) | Controls and reset (I34 to I36) | Persistent state (I37) |
| --- | --- | --- | --- | --- | --- |
| The RISC-V IOMMU model as a PCI function (`hw/riscv/riscv-iommu-pci.c`, `hw/riscv/riscv-iommu.c`) | An element, and a master too: it reads its device directory, its tables, and its command queue, and writes fault and page-request records, a fence command's data, interrupt files that it keeps in memory, and the notices for those files. Those requests go straight to system memory, past its own bus-master gate. Only its MSI-X passes that gate, untranslated, since a function of its class is exempt | A PCI function: its registers lie where enumeration places them, and it has a configuration page of its own | MSI-X, five vectors | It leaves reset in `Off`, or in `Bare` by a property, with its queues off. Its mode register can be written back to `Off` or `Bare` from any mode. No lock of its state was found | None |
| The same model as a device of the machine (`hw/riscv/riscv-iommu-sys.c`), a machine option | The same. Its MSIs go to system memory. It serves the PCI bus that it finds when it is created | Its registers fill one page of the machine's map | Four wired APLIC sources of its own, or MSIs | As above | None |
| A PCIe root port, and PCI bridges (`hw/pci/pci_bridge.c`, `hw/pci-bridge/`) | A master by its own MSIs alone: a root port signals its slot and error events, and a bridge its slots' events, by MSI-X or MSI, or by a wired interrupt (`hw/pci/pcie.c`, `hw/pci/pcie_aer.c`, `hw/pci/shpc.c`). No other request of its own was found. A function behind a bridge to conventional PCI is seen as the bridge, or as device 0, function 0 of the bus behind it (`hw/pci/pci.c`) | Its secondary-bus number sets the requester identity that the MSIs of every function below it carry, and where their configuration pages are found | It passes the wired interrupts of the functions below it on, by a fixed mapping | Its bus reset resets every function below it; its own reset clears its bus numbers | None |
| `edu`, a test device (`hw/misc/edu.c`) | A master: one transfer of up to 4 KiB, a fixed virtual time after a command write. An IOMMU model sees its transfers under the identity that the model fixed when it built the function's address space; for a device present at start, that is before any bus behind a bridge is numbered. It admits the function's MSI under that identity, and translates it under the requester identity that the MSI carries, which follows the bus number when the MSI is sent | Its registers lie where enumeration places them; a wired interrupt on a shared line, or one MSI | Wired, on one of the four shared sources, or one MSI | Its model defines no reset: a reset clears its configuration space alone, and a queued transfer survives it | None |
| An NVMe controller (`hw/nvme/ctrl.c`) | A master, through its bus-master address space. A transfer whose address lies in its own controller memory buffer or persistent memory region is copied inside the model, and passes no element | As `edu` | Wired, or MSI-X | A function-level reset; a controller reset at a device reset; a power state that software can write | Its namespace's drive image |
| A virtio PCI device (`hw/virtio/virtio-pci.c`, `hw/virtio/virtio-bus.c`) | A master. An IOMMU model sees its MSI-X writes; it sees its queue and data requests only with the device's property `iommu_platform=on` | As `edu` | Wired, or MSI-X | Its model defines a reset; clearing its bus-master enable stops it. Behind a PCI Express port it also has a function-level reset, and a power state that software can write | Its backend's: not read |

QEMU also offers a virtio IOMMU for this machine, which was not read. A
root bus whose host bridge sets `bypass-iommu`, which is off by
default, bypasses every IOMMU model, for every function below it
(`hw/pci/pci_host.c`, `hw/pci/pci.c`). No file of the tree models an
IOPMP.

**One fact that R5.9 does not have.** R5.9's cell on this machine's
controls says "No clock and no power control for one device", and its
list of what no instance shows says the same of a power control. A
closer reading for this page found one: a PCI function's power state,
where a model lets software write it. The NVMe model and two network
models, e1000e and igb, do; so do a virtio PCI device behind a PCI
Express port, and the two models that pass a device through, from the
host or from another process (`hw/nvme/ctrl.c`, `hw/net/e1000e.c`,
`hw/net/igb.c`, `hw/virtio/virtio-pci.c`, `hw/vfio/pci.c`,
`hw/vfio-user/pci.c`). In any state but D0, the regions that the
function's base address registers and its expansion ROM register map
are not decoded. Its configuration registers still are
(`hw/pci/pci.c`, `hw/pci/pci_host.c`), and no check of the state was
found on its requests or on its MSIs; for a device passed through,
what the state does is the device's own. R5.9's text is accepted, and
this page does not edit it; on this point its cell and its list miss a
fact. No invariant turns on that fact. By the Terms a device's power
is one of its controls, which I34 covers; the register lies in the
function's configuration page, which I32 and I34 keep from an owner's
mappings (I30 (b)'s reading); and R5.6 defines no permission for
power.

### Invariant by invariant

What a device path would have to show for each invariant is in section
3's invariant table. This one says what the emulated machine has for
it.

| # | What the source has that bears on it | What the machine lacks, or does not model | Not read |
| --- | --- | --- | --- |
| I29 | The set of devices that the machine creates (`hw/riscv/virt.c`), and its masters: the firmware-configuration device, the APLICs, virtio devices, PCI functions, and the IOMMU models | A second execution context: there is one array of harts | What the firmware drives; the distribution's build configuration |
| I30 | Four shared wired sources for all PCI functions; the identities that functions behind a bridge share; a bridge's bus reset; registers that software places; configuration pages found by bus number | A clock, a PHY, a power domain, or a pin: the machine creates none | |
| I31 | Two IOMMU models, for a PCI function's bus-master accesses; a refused access goes to unassigned memory, and a transfer is checked page by page (`system/physmem.c`); a test master, `edu` | An IOPMP. An element in the path of the firmware-configuration device, the APLICs, or a memory-mapped virtio device. A device model that picks its own identity: none was read | Requests that a function marks as already translated; the virtio IOMMU |
| I32 | An IOMMU model's registers and tables can be read from outside the machine, through QEMU's monitor interface (`hmp-commands.hx`). Its mode register returns to `Off` or `Bare` from any mode; its command queue directs its writes; it fixes a function's identity early; the APLIC's MSI-address lock | A lock of an IOMMU model's state: none was found | |
| I33 | An interrupt file takes any 4-byte write of an identity at the start of its page; an APLIC's forwarding, the writes that make its sources pending, and `genmsi`; an IOMMU model's MSI page tables, which serve only writes that carry a requester's identity; interrupt files that it keeps in memory, with a notice | Real timing, for the flood case: the emulator's timing is its own | The firmware's interrupt setup |
| I34 | Its controls are resets (a bridge's bus reset; a function-level reset in the NVMe model and in a virtio PCI device behind a PCI Express port; the test device's reset or power-off of the whole machine) and a PCI function's power state, where a model lets software write it; configuration registers in pages of their own | A clock or a pin for one device. A cache: its cache-block operations do nothing past their checks (`target/riscv/op_helper.c`) | |
| I35 | An IOMMU model's mode after reset, `Off` by default; a write that closes a function's bus-master gate (`hw/pci/pci.c`); interrupt files that can be cleared through CSRs | A cache, for I35 (d) | The firmware's device setup; the state in which U-Boot leaves the rehearsal's disk |
| I36 | A write that closes a function's bus-master gate stops its requests; for a virtio PCI device, its model stops the device on that write. An IOMMU model's own requests pass no gate. Across a system reset, by the source, `edu`'s queued transfer, each function's gate as it was, and the interrupt files' and the APLICs' state survive, and an IOMMU model that resets to `Off` refuses | A system reset that the gates execute: a reset request ends the run. A restart | |
| I37 | The gates' images come from the host; the rehearsal's disk is a boot source; the first flash bank is one too where a drive backs it | A system reset in the gates | The persistent state of device models other than the flash and the disks |
| I38 | Each hart's PMP (`target/riscv/pmp.c`) beside the IOMMU models; the gates' hostile-monitor rows, which aim at devices' registers | | The hostile images' code beyond their declarations |

**What the model's terms could not place** on this machine: the
emulator's own paths into memory, which are the host's and no device's
(QEMU's loader, its monitor interface, and its debug stub). R5.9 lists
them among what the model does not express. Nothing else was found.

## 5. What is not established, and what the plan of step (3) inherits

### Not established

Sections 3 and 4 name what is missing where it bears on a device or on
an invariant. Across them:

- **On the board, no unit could be assigned to a VS domain on the
  record alone.** I30 (d) bars a unit where the platform description
  marks as not established a fact that its clauses need. The record
  establishes enforcing elements for no bus master (section 3). Its
  list of what devices share is "found so far" (its "Not established"
  list, item 23). What the boot ROM reads or writes of any device is
  not established (item 24). And the reset lines of the devices other
  than the bus masters that the board's Linux drives are not
  established (item 22). That is the state of the record's rows, the
  held results apart. It says nothing of what the hardware can do, and
  it chooses nothing.
- **On the emulated machine, nothing was run.** What a model's source
  does is not what a gate has shown. The distribution's build, the
  CHERI check's emulator, what the firmware drives, the virtio IOMMU,
  and requests that a function marks as already translated were not
  read.
- **What no instance shows** is R5.9's list. Section 4 finds, in
  models that QEMU offers, one thing that the list says the emulated
  machine lacks: a power control of one device, a PCI function's power
  state.

### What the plan of step (3) inherits

The model leaves these to that plan, or to the plan or the step that it
names.

| What | Where the model says so |
| --- | --- |
| "Whether an IOMMU or an IOPMP confines a master, which device a VS domain is given, who writes the state of I32, and how a service speaks to those that it serves" | R5.10, "No device, no mechanism, and nobody to program one" |
| The first configuration that assigns a unit to a VS domain | R5.2, "Scope" |
| R5.3's obligations: what would show each invariant, and its negative cases. That plan "may refine them, and returns to the responsible human before it drops one" | R5.3 |
| Where it takes that evidence for what no instance shows | R5.9, "What no instance shows" |
| The MVP plan's stop condition 3, which that plan names for the responsible human's decision | R5.2, I33's row; the M14 plan's section 11 |
| Which of A9 to A13 the monitor's boot code repeats before it seals | R5.8, Part 4 |
| Whether the log also records the descriptor's identity, or the platform description's own | R5.8, "Where the authority is recorded" |
| The authority report's schema, which "The plan that builds a generator extends" | R5.8, Part 4 |
| The proof-impact review: whether a premise of a proof rests on a VS domain's private memory not changing while its hart runs the monitor's code | R5.10, "A fact that a master ends" |
| For a unit whose holder is the monitor: its interrupts, its controls, its lifecycle, and its analyses, which are for "the plan that first gives the monitor a device" | R5.2, "A unit whose holder is the monitor" |
| A restart of an owner with its unit kept, which is for "the plan that builds a restart"; and both triggers, for a restart and for a design in which an owner changes its device's reach while it runs | R5.2, I36's row; R5.8, Part 5 |
| A change of a unit's owner, a unit taken back, hot-plug, and who may ask for a restart: step (5)'s | R5.8, Part 6 |
| A permission for a clock or for power, and a type for each master of one unit: for a later revision, when a use or a policy needs one | R5.6 |
| Whether a device path could be carried over to the supervisor-domain specification's two chapters on devices and interrupts: for MVP 2.0's last step | R5.10, "The supervisor-domain specification" |

**One mechanism, as a fact** (the plan's section 8). On the board, the
sources read name the IOMMU for PCIe ports alone, so for every other
bus master an IOPMP is the only kind of enforcing element that the
record's sources name, and for some they name none. That is no
decision, and no basis for one: M13's result concludes that nothing in
steps (2) and (3) "can rest on an IOPMP checking a master's accesses,
or on the project being able to program one". On the emulated machine,
the source that was read has enforcing elements only for the requests
that a PCI function sends through its bus-master address space, and
not for all of those, in two IOMMU models.

## 6. What this result changes

- **Maintained pages.** The [glossary](glossary.md): its row for M14,
  rows for the model's terms, and its rows for DMA and for IOMMU and
  IOPMP. The [hardware roadmap](riscv-security-hardware.md): three
  lines on work that gives a VS domain a device, which now state the
  model's requirement and name no mechanism as required. The
  [roadmap](roadmap.md) and the planning index name the model and this
  result.
- **The AI-assistance disclosure** (`mvp/docs/ai-assistance.md`) gains
  its section on M14.

It changes nothing else:

- **No claim.** `mvp/docs/claim.md`, `mvp/docs/claim-boundary.md`, and
  the claim ledger are as the model's commit left them. M14 is evidence
  for none of them.
- **No accepted text** but those three lines of the hardware roadmap,
  which the plan lets M14-3 bring up to date (its section 11): not the
  security model, the MVP plan, the M14 plan, or M13's record and
  result.
- **No code, tool, test, or image**; no file under `model/`; nothing of
  the tool lock; no path that the proofs' records bind (the plan's rule
  10); and nothing on the board.

## Status record

```text
mvp_m14_result=accepted-if-its-proposing-commit-is-on-the-public-main-with-the-responsible-human's-sign-off;otherwise-proposed
mvp_m14_result_plan=mvp-m14-plan.md;accepted-2026-11-25-d0ec2aee
mvp_m14_result_model=security-model-v1-Revision-5;accepted-2026-11-26-5206c07a;1061-lines;six-classes;I29-to-I38;A9-to-A13
mvp_m14_result_questions=23;each-answered-in-the-model
mvp_m14_result_read_against=M13's-record-of-one-K3-COM260-board;QEMU-virt-at-upstream's-tag-v10.2.2-from-its-source
mvp_m14_result_board=the-record-establishes-enforcing-elements-for-no-bus-master;the-held-results-apart;no-unit-assignable-on-the-record-alone
mvp_m14_result_emulated_machine=as-configured-no-enforcing-element-and-no-device-whose-holder-is-the-monitor;two-IOMMU-models-offered-for-PCI-functions;no-IOPMP-model
mvp_m14_result_sessions=none
mvp_m14_result_run=nothing
mvp_m14_result_chooses=no-device;no-mechanism
mvp_m14_result_claim=none
mvp_m14_result_accepted_text_changed=the-hardware-roadmap's-three-lines-as-the-plan-allows;no-other
mvp_m14_result_sent=nothing
mvp_m14_result_next=MVP-2.0-step-3-under-its-own-plan-at-the-responsible-human's-direction
```
