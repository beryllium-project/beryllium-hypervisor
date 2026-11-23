<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# MVP 2.0 milestone M13 plan: the board's device facts

This plan bounds milestone M13. In the [MVP plan](mvp-plan.md)'s
ladder it is MVP 2.0's first step after M11 (S3-C.2, step (1); S3-D.3):
"characterize the IOMMU/IOPMP, interrupt, reset, and device-ownership
facts of the board". The next two steps build on what it finds: step
(2), the device and DMA object model, and step (3), one static
pass-through device path with the I/O service VS domain.

It is written on the responsible human's direction of 2026-11-23,
given once M11's result had been accepted. It finds facts, and chooses
nothing. It sends nothing to anyone.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. If that commit is on the
public `main` with the responsible human's `Signed-off-by`, this plan
is accepted as written, with Q1 to Q12 at their defaults, and with the
readings of section 11. Any other answer needs a revised commit before
the sign-off. The signed commit differs from the one reviewed only by
that line and its committer date; if it must be rebased first, the
internal record says so. The project's internal records keep both
commit IDs and the instruction. This plan changes no accepted text.

## 1. What M13 is

- **Fact-finding about one board**: the K3 COM260 board of MVP 1.0 and
  M11 (Q2). For each fact, the record says where it comes from. Where
  nothing settles a question, it says "not established", and why.
- **Four subjects**, S3-C.2's: what protects memory from the bus
  masters other than the harts (the IOMMU and the IOPMPs); interrupts;
  reset; and which device belongs to whom.
- **Reading, and as little else as possible.** Documents and sources
  are read on the workstation. On the board: reads from its own Linux;
  and, only on the responsible human's reply at a review point
  (section 7), probe images that read what Linux cannot. Nothing
  persistent on the board is written but what the board policy already
  allows (S3-A.1): images on the Beryllium partition, and U-Boot's
  environment installed and restored around a probe session. A probe
  writes only its own CSRs and the registers that the review point
  names for it (rule 6).
- **It chooses nothing.** Which device a VS domain gets, how a device's
  memory accesses are confined, and which objects the security model
  gains are for steps (2) and (3), each with its own plan. A fact that
  points one way is input to them, not a decision.
- **It waits for nothing.** M12 runs beside it, as S3-D.3 has it.

What it produces:

| Product | What | Where |
| --- | --- | --- |
| The record | The board's device facts under the four subjects, each with its evidence (section 5) | A planning page, `planning/k3-com260-devices.md` |
| The read tool | A script that runs a fixed list of read-only commands on the board's Linux over SSH, with a self-test | `mvp/tools/` and `mvp/tests/`, with its rows in the MVP's README |
| The probe images, if run | HS-mode images that read registers and CSRs that the board's Linux cannot, with their board record | Proposed at the review point (section 7) |
| Two maintained pages brought up to date | The [hardware roadmap](riscv-security-hardware.md)'s "Open hardware questions", and the [glossary](glossary.md)'s rows for the terms that M13 uses | Those pages |

What it is not: hardware validation; evidence for MVP 1.0's claim or
for M11's; a choice of a device for step (3); or a change to any image
of the M11 candidate's, or to any path that the proofs' records bind.

## 2. Inputs

As fetched read-only on 2026-11-23. Dates are UTC. M13-1 pins each
again when it reads it, and the record names the commit that it read.

| Input | Identity |
| --- | --- |
| The vendor's documents | The repository `spacemit-com/docs-chip` at `4879ed5d` (2026-11-11): the K3 datasheet, `en/key_stone/k3/k3_docs/k3_ds.md`, and the K3 user manual under `en/key_stone/k3/k3_docs/k3_usermanual/`: its chapters 5 (boot modes), 6 (address map), 7 (interrupts), 8 (CPU), 9 (memory and storage), 15 (security), and 17 (clock and reset), with its connectivity chapters (`14_connectivity/`, its PCIe page among them) and its peripherals chapters. The repository states no licence, so it is cited and not copied |
| The vendor's Linux | `spacemit-com/linux-6.18`, branch `k3-br-v1.0.y`, at `7d17e358` (2026-10-15): the K3 device trees under `arch/riscv/boot/dts/spacemit/`, and the drivers of the devices in the record |
| The vendor's real-time firmware | `spacemit-com/esos`, branch `k3-br-v1.0.y`, at `e5cd0455` (2026-10-22), under Apache-2.0 |
| The vendor's firmware and U-Boot | Its OpenSBI at `e4d27728` and its U-Boot at `0dcf0d83`: the commits that the board's NOR images correspond to (S3-E.1, statement 1) |
| The board's images | The NOR's five files are S3-E.1's table. Of them, M13 reads the device trees in `u-boot.itb`, of which the firmware takes `k3_com260_ifx`'s, and those in `esos.itb` that are named for this board (`com260_ifx`), the real-time cores' trees. Both files are pinned by SHA-256 in `mvp/k3/published-pins.txt` |
| The board's Linux | Fedora Linux 45 on the board's NVMe drive, as each session finds it. The record names each session's kernel; on 2026-11-16 it was `7.3.1-300.0.riscv64.omni.fc45`. The private record keeps the SHA-256 of the device tree that Linux received, since that tree holds identifiers (rule 8) |
| Upstream | Linux at the board kernel's base, for the drivers that it binds, and for the source of the device tree that Linux receives on this board, which M13-1 finds; OpenSBI at M11's pin `ed70256d`, for its K3 support |
| The specifications | The RISC-V IOMMU specification, release `20260222`; the RISC-V IOPMP specification, `v0.85` (2026-11-20), a draft that the K3's IOPMPs may predate; and the Advanced Interrupt Architecture, `1.0`, as its release `20250312` has it |
| This project's rules | The MVP plan's board policy (S3-A.1, items 1 to 8; S3-E.3, items 9 to 13), its stops and decisions (section 11 names those that M13 reads), and the terminology rule (S3-D.2) |

## 3. What is known at the start

As read on 2026-11-23 from the inputs above, and from the read-only
inventory of the board's Linux of 2026-11-16 (S3-E.1's "board").
Each line is a starting point. The record reads it again and cites it.

| Subject | What is known | From |
| --- | --- | --- |
| The IOPMPs | Nine instances: eight list bus masters, and IOPMP4 lists none. Each listed master's memory accesses are checked by a source ID, fixed or set in the Secure Configuration unit (`0xF058_0000`). The masters: the DMA engines, USB, the storage card controllers, UFS, eSPI, PCIe, the GMACs, audio, UCIe, the GPU, the VPU, the trace buffer, the display, the camera's image processor, the security engine, the real-time cores, the debug module's bus access, and two masters that the manual names `REE_W` and `REE_R`. One instance also lists "CPU". The 2D engine has a source-ID setting, and no instance lists it. After a power-on reset an IOPMP passes every access; once enabled, it cannot be disabled until the next reset. The manual places their configuration registers, at `0xF080_0000` to `0xF088_FFFF`, in the vendor's "secure domain", to be reached only from a "secure environment" | The user manual, 15.4 |
| The IOMMU | The datasheet (2.7.1) and the PCIe page's overview (14.1.1): "PCIeA, PCIeB, and PCIeE support IOMMU for device virtualization". The same page's table of features (14.1.3) marks ports A and B/C, and not D/E, as "connected to IOMMU" and with ATS. The vendor's kernel tree has one IOMMU, `iommu@c0f00000`, compatible `spacemit,k3-iommu`, disabled by default, whose driver is derived from the upstream RISC-V IOMMU platform driver with the unit's clock added; its PCIe controllers 0 to 2 (ports A to C) map to it, and 3 and 4 (ports D and E) do not. So the datasheet and the page's overview say port E, and the page's table and the kernel tree say port C. On this board port A holds the NVMe drive, port D nothing, and port E the Wi-Fi card | The datasheet, 2.7.1; the PCIe page at `4879ed5d`, 14.1.1 and 14.1.3; at `7d17e358`, `k3.dtsi` and `drivers/iommu/riscv/iommu-spacemit-k3.c`; the board, 2026-11-16 |
| DMA protection on this board | Neither the firmware's device tree nor the one that Linux receives has an IOMMU node or an IOPMP node, and Linux's has no `dma-ranges`. No PMP region of the resident firmware denies S-mode the IOPMPs' or the IOMMU's registers; whether the bus itself refuses S-mode there is not established. The vendor's own trees give S-mode drivers devices in regions that the address map marks "Secure", among them an I2C controller and the eFuse block's controller. Whether any boot stage enables an IOPMP is not established | The published tree; the board, 2026-11-16; the vendor's firmware source at `e4d27728`, as read for S3-E; the user manual, chapter 6; `k3.dtsi` and `k3_com260.dtsi` at `7d17e358` |
| Coherence | Linux's tree marks the SoC's bus `dma-noncoherent`, and the hardware roadmap lists non-coherent DMA | The board, 2026-11-16; the [hardware roadmap](riscv-security-hardware.md) |
| Interrupts | The user manual: an ACLINT, and an APLIC with "MSI output mode only" (chapter 7); for the X100 harts, GEILEN = 8 and 64 VS-mode MSI identities (chapter 8). In Linux's tree the M-level APLIC delegates its 512 sources to the S-level APLIC, which forwards them as MSIs to the S-level IMSIC: hart-index bits 4, guest-index bits 6, 511 identities in each interrupt file, and 63 in each guest interrupt file. The firmware's tree gives that IMSIC twice the address space and 511 identities in each guest interrupt file. The PCIe controllers' MSIs target the S-level IMSIC directly. In the firmware's tree the S-level APLIC is disabled. What this board shows of its guest interrupt files is not established | The user manual, chapters 7 and 8; the board, 2026-11-16 (the device tree and the kernel's log); the published tree |
| Reset | The manual names four schemes: power-on, which resets the whole chip; the watchdog's, which resets it but for its pin and debug registers; a module's software reset; and a power island's reset. The firmware's system reset goes through the RPMI mailbox to the real-time cores' firmware (S3-E.1, statement 4). The trees name most devices' reset lines by controller and index, and the three storage card controllers share one. Which register bit each line is, and what else shares that register, is not established. The firmware's tree names a watchdog with a reboot node, and a power-management chip on I2C | The user manual, 17.3.2; S3-E.1; the trees |
| Ownership | The real-time firmware answers the RPMI mailbox, whose services are clocks, voltages, power domains, system suspend, system reset, hart state, the real-time clock, and the power key. By their own trees, the real-time cores' firmware also maps the clock, reset, and power blocks that Linux drives, and so can write them; drives the application side's GPIO and pin controllers; and runs an Ethernet controller of its own. The vendor's kernel tree lists the real-time subsystem's own devices (UARTs, CAN, PWM, I2C, audio DMA) in `k3-rdomain.dtsi`, each disabled by default. Among the bus masters, Linux drives on the board a DMA controller, three USB controllers, one GMAC, UFS, the microSD card's controller, and three PCIe controllers, as above. The monitor touches no device (S3-D.5) | The firmware's tree; `esos.itb`'s trees; `k3-rdomain.dtsi` at `7d17e358`; the board, 2026-11-16 |
| The two trees | The firmware's device tree and the one that Linux receives differ, among other things, in: their harts (16 against 8); the RPMI mailbox, its services, and the real-time cores' nodes (present against absent); the watchdog and its reboot node (present against absent); the M-level interrupt controllers (`okay` against `reserved`); the S-level IMSIC and APLIC (above); their PCIe controllers; and their compatibles. Which entity gives Linux its tree on this board is to be read | The published tree; the board, 2026-11-16 |

## 4. The questions

The record answers each for this board, or says what is not
established, and why.

**A. What protects memory from the bus masters other than the harts**

- **A1.** Every bus master on the SoC, the PCIe controllers' embedded
  DMA engines among them, and which are enabled on this board. For
  each, the path of its memory accesses, and of its accesses to other
  devices' registers: through which IOPMP, with which source ID;
  through the IOMMU or not, with which device ID; and with what address
  width.
- **A2.** The IOMMU: its registers; its version and capabilities, as
  its driver reads them; the PCIe ports whose requests it sees, and
  which of the vendor's sources is right about ports C and E; whether
  it accepts translated (ATS) requests, and with what check; whether it
  translates MSIs; its state after reset; whether any boot stage
  enables it; and who can reach its registers.
- **A3.** The IOPMPs: each instance's configuration; its state on this
  board as booted, passing or enabled, locked or not; who enables or
  configures any of them (the boot ROM, the SPL, the real-time
  firmware, the firmware, U-Boot, or Linux); how one reports a
  violation, and what a denied access returns; the Secure Configuration
  unit's settings for each master; and what the vendor's "secure
  environment" is: which masters, at which privilege, can reach the
  configuration registers, and whether an application hart can, in
  M-mode or in HS-mode. What "CPU", `REE_W`, and `REE_R` are among the
  masters, and which instance checks the 2D engine.
- **A4.** What else bounds a device's memory accesses: the PCIe
  controllers' inbound address translation, and whether it limits what
  a device can reach. The coherence of each master, and, for each that
  is not coherent, which cache operations its driver needs, and which
  of them a VS domain can issue under M11's boundary.
- **A5.** MSIs: whether a device's MSI is an ordinary memory write that
  can reach every hart's interrupt files, the monitor's and M-mode's
  among them.

**B. Interrupts**

- **B1.** The interrupt domains, M-level and S-level, and their
  delegation: as the firmware configures it (its source and its tree),
  and as Linux finds it.
- **B2.** Each device's wired sources, the manual's table against both
  trees, and any source that devices share.
- **B3.** The IMSICs: the interrupt files of each hart; the guest
  interrupt files of harts 0 to 2, as KVM reports one hart's at boot,
  and as a probe reads each; and the identities in each file, against
  the documents and both trees.
- **B4.** Whether an APLIC in MSI mode can deliver a source to a guest
  interrupt file, as the architecture allows.
- **B5.** The real-time subsystem's interrupts, and any source that it
  shares with the application harts.

**C. Reset**

- **C1.** The system's reset paths: the firmware's, through the
  real-time firmware; the watchdog's; the power-management chip's; and
  the reset dongle's line. What each resets: the harts, the devices,
  the IOPMPs, and the real-time cores.
- **C2.** Each device's reset lines: which register bit each is, and
  what else that register holds.
- **C3.** Function-level reset of the PCIe devices on this board, as
  their configuration space reports it, and the PCIe controllers' own
  resets.
- **C4.** Each device's clocks and power domain, and who controls them:
  Linux, directly through a register block; the real-time firmware,
  through the RPMI mailbox or directly; or both.

**D. Which device belongs to whom**

- **D1.** For each device: which agents touch it (the boot ROM, the
  SPL, the real-time firmware, the firmware, U-Boot, Linux), and which
  owns it at run time on this board.
- **D2.** What devices share: a 4 KiB page of registers, the G-stage's
  grain; a clock; a reset register; a power domain; a pin group; a bus;
  an interrupt source.
- **D3.** The devices that are not bus masters, listed apart from those
  that are. The first kind needs no protection of memory from its
  accesses to be given to a VS domain.
- **D4.** The other execution contexts, the real-time cores, the harts
  without the H extension, and the debug module: what each can reach of
  the devices and of memory, and what bounds it.

## 5. Method and rules

1. **Evidence, named for every fact.** Five classes: *document*, the
   vendor's documents; *source*, a source tree at a pinned commit;
   *files*, the published images; *board-Linux*, the board's own Linux
   in a recorded session; and *probe*, a probe image on the board. Each
   fact cites its file and section or line at its commit, or its
   session. A fact without a citation is not in the record.
2. **The order.** Documents and sources first; then the board's Linux;
   then probes, only for what is still open, and only on the
   responsible human's reply (section 7).
3. **Disagreements are findings.** Where two classes disagree, both are
   recorded. What this board does is decided by the board's own
   observation; what the hardware can do, by the documents, unless the
   board shows otherwise. Where documents disagree with each other,
   each is recorded, and none decides. Nothing is reconciled by
   preference.
4. **Nothing of the vendor's is copied into the repository.** Facts are
   written in the project's own words, with their citations, and with
   short attributed quotations only where the wording matters. No file
   of the vendor's is committed.
5. **The board's Linux: the read sessions write nothing of their own
   there.** S3-A.1's item 1 reads: "Linux on the board is used only to
   stage images and to run read-only preflight checks, never to launch
   the MVP". M13's read sessions are read as such read-only preflight
   checks (section 11). A probe session stages its images through the
   board's Linux, as items 1 and 4 allow. The read tool runs a fixed
   list of commands over SSH, as the board's account, and as the
   superuser (root) only for the reads that need it: PCI configuration
   space, the debug file system's summaries of clocks and power
   domains, `/proc/iomem`, and the whole kernel log. The session's
   record holds each command with its output.
   - It writes no file of its own on the board. The board logs the
     login and the superuser's use, as it logs any.
   - It mounts nothing, writes to no file in sysfs or in the debug file
     system, loads or unloads no module, and binds or unbinds no
     driver.
   - It reads registers only through the kernel's own interfaces for
     them. For a PCI device it reads the `config` file alone, never
     `vpd`, `rom`, or a `resource` file. It opens no `/dev/mem`, reads
     no raw dump of registers, such as the debug file system's `regmap`
     files, and reads the contents of no nonvolatile memory (`nvmem`),
     such as the eFuses or an EEPROM.
   - Two reads have effects, both the kernel's own power management,
     which any use of those devices also causes. The clock summary
     makes the kernel resume the clock providers that use runtime power
     management, and ask each clock's driver for its state. Reading
     a PCI device's `config` file makes the kernel resume the device's
     parent bridge, and the device itself if it is in D3cold.
   - Every command has a time limit.
   - A session needs the responsible human's word that the board is
     free. It makes no reset, types nothing at a console, and sends
     nothing to the reset dongle.
6. **The probes, if run.** HS-mode images under the board's resident
   firmware, booted from system reset as the MVP's images are: from the
   Beryllium partition, by U-Boot's saved environment, which a recorded
   session installs and restores (S3-A.1, items 1 to 7).
   - **Their boot path.** Since M11, the MVP's boot prelude requires
     SBI 3.0 and, with the boundary on, the project's own firmware
     extension; the resident firmware reports SBI 2.0, and lacks that
     extension. A probe therefore carries a boot path of its own that
     accepts the resident firmware, built apart from the bound paths
     (rule 7).
   - **Harts.** A probe runs on harts 0 to 2, the MVP layout's harts,
     and starts no other hart (section 11). Facts about harts 3 to 15
     come from documents, sources, and the board's Linux.
   - **Reads.** CSRs, and the registers that the review point names for
     each probe, each with its documented effect. None whose read has an
     effect: a status register cleared by its read, a FIFO or a queue, a
     mailbox. None of a block whose clock or power domain the read
     session found off. None of the eFuses or of the crypto engine
     (`0xF070_0000` to `0xF07F_FFFF`).
   - **Writes.** Only the probe's own CSRs, such as `hgeie`, and the
     registers that the review point names for each probe. Never: an
     IOPMP's or the IOMMU's registers; the Secure Configuration unit
     (`0xF058_0000` to `0xF05F_FFFF`); the eFuses; the clock, reset, and
     power blocks that the manual's chapter 17 lists; a mailbox; an
     I2C, SPI, or QSPI controller; another hart's interrupt files, or
     the M-level interrupt controllers; or the NOR.
   - **A stall.** A read that faults or stalls is a result. Before the
     probe session, its dry run shows whether the board tools reset the
     board after a probe that stops printing. If it shows that they
     cannot, the responsible human is told before the probe session,
     and resets the board by hand in it.
7. **No bound path.** M13 changes no path that the proofs' records bind
   (`mvp/verify/tools/litmus.py`'s `INPUTS`: `mvp/src`,
   `mvp/Makefile`, `mvp/scenarios`, `mvp/tools/gen-scenario.py`,
   `mvp/tools/gen-dts.py`, `mvp/tools/policy-check.py`,
   `mvp/tools/port.py`, `mvp/tools/lock`, `mvp/guest`, and
   `bringup/k3-b2`), no image of the M11 candidate's, and nothing of the
   tool lock. The MVP's own probe images live under two of those paths,
   so M13's probes would be built apart from them. If the board tools
   cannot boot such an image without a change under one of them, the
   review point says so.
8. **Privacy** (S3-A.1, item 7). Identifiers (MAC addresses, serial
   numbers), the kernel's command line, filesystem identifiers, U-Boot's
   environment, the memory map's reservations, and any digest of a file
   that holds one of them stay in the private store on the workstation,
   but for what item 7 lets a board record hold: hashes, the `be_` names
   and values, and verdicts, as the MVP's board records hold them. The
   record holds facts without them.
9. **Words.** S3-D.2's rule applies, with three more uses. An IOPMP's
   "memory domain" (MD) is written "IOPMP memory domain"; its "SID" is
   written "source ID"; and the vendor's "secure domain", "secure
   world", and "secure environment" are quoted as the vendor's words,
   since nothing yet says what they are on this SoC. From the manual's
   sentence on where the IOPMPs' registers may be reached, the record
   quotes those words alone.
10. **A finding that bears on the vendor's product's security.** If a
    document, a source, or a probe shows that software in S-mode or
    HS-mode on an application hart can read the registers of an IOPMP
    or of the Secure Configuration unit; enable, reconfigure, unlock, or
    clear an IOPMP; change a bus master's source ID or "secure" setting;
    write an eFuse; read key material; or reach a range that the
    resident firmware's own configuration keeps from S-mode, the work
    stops there (stop 6).
    - The responsible human decides how it is reported. Nothing about
      it is kept in this repository, a board record among it, before he
      has decided; until then it is kept in the project's internal
      records.
    - Once he has been told of a finding, it does not stop the work
      again. It stays held, as the bullet above says, until he has
      decided; and a new fact about it is told to him and held with it.
    - Reading or driving a device that the vendor's own trees give to
      S-mode, as their drivers use it, is not such a finding, unless it
      writes an eFuse, yields key material, or reaches a range that the
      resident firmware's own configuration keeps from S-mode. Neither
      is the list of the resident firmware's PMP regions in its
      published source. An exempt fact that would show a held finding
      is held with it, until he has decided.

## 6. Where the work lives

| What | Where |
| --- | --- |
| This plan, the record, and M13's packets | The public line's `planning/`; the decision records of the packets in the project's internal records |
| The read tool and its self-test | `mvp/tools/` and `mvp/tests/`, with its rows in the MVP's README. The self-test runs in `./mvp/mvp check`, against a stand-in board |
| The read sessions' outputs | The private store on the workstation, outside every repository, since they hold identifiers |
| The probe images, if run | Proposed at the review point: new files only, built apart from the bound paths (rule 7) |
| A probe session's board record | `mvp/results/`, as the MVP's board records are, with what is private kept out (rule 8), and with nothing that rule 10 holds back |

## 7. The work packages

| ID | Work | Exit |
| --- | --- | --- |
| M13-1 | **The reading.** The inputs pinned again; the documents and sources read; the record's first draft, every fact with its class and its citation; the questions that it leaves open, marked | The record's first draft |
| M13-2 | **The board's Linux.** The read tool, written under the project's rules for privileged tooling, with a self-test that shows each refusal. Then one session on the board, and a second only if the first leaves a read undone | The tool committed, with a whole `./mvp/mvp check` passing at its commit; the session's facts in the record |
| M13-3 | **The review point.** The questions still open. For each that a probe could settle, the probe: what it reads, what it writes, why that is safe, and how it is built and booted; and, for the IOMMU and the IOPMPs, whether the read session found their clocks on. For a probe whose successful read would meet a trigger of rule 10, it says so, and says where the probe's source and its result are then held. Put to the responsible human as one reply. If no open question can be settled by a probe, M13-3 says so in one line, and M13-5 follows without a reply | His reply: `probes: go`, `probes: no`, or a narrowed list |
| M13-4 | **The probes**, on `probes: go` only. Written; run under QEMU first, where the registers are absent, to show each probe's fault path and its output; the dry run of a probe that stops printing (rule 6); then one board session, with him present at the environment's install and restore | The board record; its facts in the record |
| M13-5 | **The result.** The record completed; the hardware roadmap's open questions and the glossary brought up to date; and a short account, binding on neither, of what steps (2) and (3) can rely on and what they cannot | The result commit, for his sign-off |

**Order.** M13-1 first. M13-2's tool can be written beside it, and its
session follows the tool's self-test. M13-3 after both. M13-4 only on
his reply. M13-5 last.

**The board.** Every board session waits for the responsible human's
word that the board is free. A read session needs nothing more of him.
A probe session needs him present, as S3-A.1's item 6 has it.

## 8. What the record says, and what may be said

- One table for each subject, with a row for each device or path, and
  each fact's class and citation.
- A list of what is not established, and why.
- A list of the disagreements between the classes, and between the
  documents.
- No word of a claim. The record is diagnostic: facts from the vendor's
  documents, its sources, and one board. It is not hardware validation,
  it is evidence for no claim of the project's, and it changes no claim
  text. No page says, on the strength of M13, that a device's memory
  accesses on this board are confined, or that the project supports a
  device.

## 9. Soft limits

A limit that is passed is a stop for re-evaluation, never a cut to the
work. Only the responsible human re-sets one.

**Counting rule:** added lines by `git diff --numstat` from this plan's
acceptance, tests included, with Markdown and generated files reported
apart.

| Lane | Limit | Basis |
| --- | --- | --- |
| The read tool and its self-test | 1,000 lines | A fixed list of reads, the decoding of PCI configuration space on the workstation, and a test for each refusal |
| The probe images, their build rules, and their checks | 2,000 lines | M0's three probe images and their checks, with a boot path of their own that accepts the resident firmware and a build apart from the bound paths (rules 6 and 7). The review point estimates it again |

## 10. Stop conditions

Each returns the work to the responsible human. The MVP plan's stops
stand beside them, S3-D's (j) to (o) and S3-E's (p) and (q) among them,
as section 11 reads them.

1. A step would write anything on the board other than what S3-A.1
   allows: images on the Beryllium partition, and U-Boot's environment
   installed and restored in a recorded session.
2. A read would need a command outside the read tool's list, a raw read
   of a device register from the board's Linux, or a read of the
   contents of a nonvolatile memory.
3. A probe would read or write anything that rule 6 and the review
   point do not allow it, or would start a hart other than harts 0 to
   2.
4. The board is in use; or a session finds it in a state that the
   session did not plan for: not on its Fedora, not back on it after a
   probe session, or booted in a way that it did not plan (S3-E's stop
   (q)); or the board stops answering during a read session, in which
   case no reset is made, and the responsible human is told.
5. A step would need M-mode code of the project's own, a firmware
   build, a microSD card, a write to the NOR, anything staged over USB,
   or kexec.
6. A finding bears on the vendor's product's security (rule 10).
7. A step would need a change under a path that the proofs' records
   bind, to an image of the M11 candidate's, to the tool lock, to the
   claim, or to an accepted text.
8. A fact contradicts an accepted record of the project's: the hardware
   roadmap, a platform record, the M11 plan, or its board addendum. The
   record says so; and if an accepted claim rests on the contradicted
   fact, the work stops.
9. Anything would be sent to the vendor or to another project. Errors
   found in the vendor's documents or trees are recorded for the
   responsible human.
10. A soft limit is passed.

## 11. Accepted rules that this plan reads

It changes none of them. The responsible human's sign-off of this plan
accepts these readings, or his answer to Q3 changes the first.

| Rule | M13's reading |
| --- | --- |
| S3-A.1, item 1: "Linux on the board is used only to stage images and to run read-only preflight checks, never to launch the MVP" | M13's read sessions are read-only preflight checks in that sense, as S3-D.6's step 1 read the inventory of 2026-11-16 to be, with rule 5's reads as the superuser |
| The MVP plan's stop condition 3: "Any milestone that needs a hart beyond the layout, ... a device, an IOMMU, DMA, ..." | M13 needs none of them: reading the facts about a device, the IOMMU, or DMA, a probe's reads among them, is not such a need, and its probes run on harts 0 to 2 alone. Steps (2) and (3) will need a device, the IOMMU, or DMA; their plans name this stop for the responsible human's decision |
| D16: "Hart 0 control, harts 1 and 2 domains, harts 3 to 7 never started" | No probe starts a hart other than harts 0 to 2 (rule 6) |
| D12: "Each milestone plan states its CHERI alignment in one paragraph; no CHERI mechanism" | M13 finds facts, uses no CHERI mechanism, and changes nothing of the CHERI variant. Its record is input to the CHERI track as to every later step |

## 12. Questions and defaults

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | Names | M13, and M13-1 to M13-5. "M13" is also a row's label in the hostile-monitor tables (`mvp/scenarios/anchor/breach.json`, `breach-control.json`, and `mvp/k3/breach/`) and in their records, none of which names a milestone | The responsible human's |
| Q2 | Which board | The COM260 alone. The K3 Mini-ITX joins as a second platform record later in MVP 2.0, under its own plan (S3-C.2) | Both now |
| Q3 | The read sessions, and the superuser on the board's Linux | Section 11's reading of S3-A.1's item 1, with rule 5's reads as the superuser, each in the tool's list | No read session: the board's Linux facts come from the inventory of 2026-11-16 alone. Or read sessions without the superuser: PCI capabilities, the clock and power-domain summaries, the addresses in `/proc/iomem`, and perhaps the whole kernel log are then not read |
| Q4 | Probes | Decided at the review point, on the questions then open | None in M13, the probes becoming step (3)'s; or all of them now, with no review point |
| Q5 | Reads from M-mode: the M-level APLIC's state, and an IOPMP read from M-mode | Not in M13. If the record leaves them open, they are for step (2)'s or step (3)'s plan | An M-mode probe on the microSD card's path, by a revision of this plan, under the M11 plan's D-2 rules and S3-E's items 11 and 12 |
| Q6 | The record's form | A planning page | A page and a data file that tools read. The default leaves the file to step (2), which will know what reads it |
| Q7 | The read tool | Committed, with a self-test | Scratch outside the repository, as the inventory of 2026-11-16 was |
| Q8 | Where the sources disagree | Each recorded; the board's observation decides what this board does, and no document decides against another (rule 3) | Each disagreement left open until the vendor answers a question that the responsible human sends |
| Q9 | Errors in the vendor's documents or trees | Recorded for the responsible human; nothing is sent | He reports them to the vendor before M13's result, and the record waits for the answer |
| Q10 | The soft limits | Section 9's | The responsible human's |
| Q11 | The board's kernel changes between sessions | Each session records its kernel; a later session adds to the record and replaces nothing | A kernel pinned for M13's sessions |
| Q12 | How this plan's decision is recorded | As its status says: the sign-off of the proposing commit, with the record kept internally | A second commit that sets a decision record here |

## What acceptance would authorize

- M13-1 to M13-3 and M13-5; and M13-4 only on the responsible human's
  reply at the review point.
- Fetching the pinned documents and sources, read-only, working around
  no access control.
- On the board, each session on his word that the board is free: at
  most two read sessions (M13-2), from its own Linux over SSH, as its
  account, and as the superuser for rule 5's reads; and, after `probes:
  go`, one probe session under S3-A.1, with him present at the
  environment's install and restore.
- Commits on the public line, unsigned, for his sign-off: the record
  and its site entries; the read tool, with its self-test and its rows
  in the MVP's README; after `probes: go`, the probe images and their
  board record, but for what rule 10 holds back; and M13-5's updates of
  the hardware roadmap and the glossary.

It would authorize no write on the board beyond S3-A.1's; no microSD
card, no M-mode code, no firmware build run on the board, no write to
the NOR, nothing staged over USB, and no kexec; no write that enables,
configures, or locks an IOPMP or the IOMMU, or that touches the Secure
Configuration unit, an eFuse, or a clock, reset, or power register;
nothing sent to the vendor or to another project; no change to the
claim, the tool lock, an accepted text, a path that the proofs' records
bind, or an image of the M11 candidate's; and no push, merge, tag, or
release step.

## Review record

An independent, read-only, automated review read the drafts of this
plan before it was presented. Its findings and their disposition are in
the plan's review packet, in the project's internal records.

## Status record

```text
mvp_m13_plan=accepted-if-its-proposing-commit-is-on-the-public-main-with-the-responsible-human's-sign-off;otherwise-proposed
mvp_m13_plan_governing_text=mvp-plan.md;S3-C.2-MVP-2.0-step-1;S3-D.3
mvp_m13_plan_direction=2026-11-23
mvp_m13_plan_board=one-K3-COM260;S3-A.1-items-1-8-and-S3-E.3-items-9-13-stand
mvp_m13_plan_subjects=the-IOMMU-and-the-IOPMPs;interrupts;reset;device-ownership
mvp_m13_plan_work_packages=M13-1-reading;M13-2-the-board's-Linux;M13-3-review-point;M13-4-probes-on-probes-go-only;M13-5-result
mvp_m13_plan_reads=S3-A.1-item-1-read-only-preflight;stop-condition-3-and-D16-unchanged;D12-stated
mvp_m13_plan_sessions=at-most-two-read-sessions;one-probe-session-on-probes-go
mvp_m13_plan_probes=decided-at-the-review-point;harts-0-to-2;a-boot-path-of-their-own-accepting-the-resident-firmware;built-apart-from-the-bound-paths
mvp_m13_plan_rules=10
mvp_m13_plan_stops=10
mvp_m13_plan_questions=Q1-Q12-defaults
mvp_m13_plan_sends=nothing
mvp_m13_plan_claim=none
```
