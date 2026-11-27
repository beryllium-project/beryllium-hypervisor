<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# MVP 2.0 milestone M15 design: the first device path, under emulation

This page is M15-2's design (the [M15 plan](mvp-m15-plan.md), section 6
and work package M15-2). It answers the plan's twenty-one questions
within the bounds that the plan sets, and lists the facts that it rests
on, the evidence that the build will give for each invariant of
[Revision 5 of the security model](security-model-v1.md#revision-5-2026-11-25-the-device-and-dma-object-model),
the proof-impact review, and the build's work packages, gates, and soft
limits. It rests on a characterization under emulation, in scratch, in
which each run that a fact rests on was made twice with the witness
outside the machine, and on prototypes of the path in that scratch, made
in four steps, A to D, of which D, the last, is the closest to this
design. Both are scratch, outside the project's repositories (the
prototypes were local commits of a scratch clone, never pushed: section
8, item 4), and neither is evidence for a claim (the plan's rule 3).

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. If that commit is on the
public `main` with the responsible human's `Signed-off-by`, this design
is accepted as written, with its questions at their defaults (section
9), and with the decisions that section 8 lists. That sign-off
authorizes M15-3, the build, as section 7 lists it, and nothing else.
Any other answer needs a revised commit before the sign-off. The
project's internal records keep the commit IDs and the instruction.

The commit that adds this page changes no accepted text, and nothing
outside `planning/`. The commit before it adds the AI-assistance
disclosure's section (the plan's rule 12), and the responsible human
signs off both.

## 1. In short

One NVMe function of QEMU's `virt` machine is given, for a whole boot,
to an I/O service VS domain, which serves one other VS domain through
two declared pages. Every request and every message of the function
passes QEMU's system IOMMU model, whose state the monitor's boot code
installs before the unit is exposed and which no confined hart can reach
afterwards. The function's messages go straight into the owner hart's
guest interrupt file. The monitor answers the owner's PCI configuration
accesses from a copy, and the function's own controller stop quiesces it
when its owner stops. No M-mode code is added. Everything runs under
emulation; nothing runs on the board.

| Row | The question (plan, section 6) | The design |
| --- | --- | --- |
| 1 | The machine | QEMU `virt` at the locked build, with `iommu-sys` and one `nvme` function at `00:02.0`, for M15's scenario's runs alone |
| 2 | The unit | That function, closed by itself |
| 3 | The scenario, and the guest's kernel | A scenario of M15's own, `io-service`; one Image for every plain scenario, with the options that the device needs |
| 4 | Who installs the state of I32, and what keeps it | The monitor's boot code, before activation: hart 0 prepares it, the owner's hart arms it; K6's candidate (2), no confined hart's profile includes it |
| 5 | The recorded reach | The I/O service VS domain's private window, in tables of the element's own |
| 6 | Interrupts | Each MSI-X vector, and the function's `INTx`, routed into the owner hart's guest interrupt file; `INTx` kept silent by the function's own disable |
| 7 | The owner's mappings, and what is done for it | BAR0 mapped; the configuration page answered from a copy; nothing done for the owner on the device |
| 8 | The handoff | In Revision 5's order: quiesced, cleared, confined and routed, exposed |
| 9 | What quiesces the unit after its owner stops | The function's own controller stop, from the owner's hart; a stop that fails fails the run |
| 10 | Reset, and the next boot | No system reset executes in a run; each boot's handoff clears what a reset leaves |
| 11 | The service's protocol | Request and response rings in two declared pages; the service copies |
| 12 | The evidence | Section 5 |
| 13 | The records and identities | Section 4.13 |
| 14 | The triggers | Neither fires |
| 15 | Execution contexts and firmware calls | None added; no change to what a guest can call |
| 16 | The accepted decisions that the build changes | Section 8 |
| 17 | The claim's words | Section 4.17 |
| 18 | Work packages, proofs re-run, gates, soft limits | Section 7 |
| 19 | CHERI | The device path off for the CHERI variant; its emulator has no IOMMU model |
| 20 | The first configuration in the security model | Not proposed (Q13's default) |
| 21 | Which of Revision 5's inventory M15 lands | Section 4.21 |

## 2. The facts that the design rests on

Each fact is a premise of the design, not evidence for M15's claim:
rule 3 has each established again by a committed test in the build
(plan:247-251), and each is about one version of the machine (rule 5).

**Pins.** QEMU 10.2.2 (`qemu-10.2.2-1.fc44`, its SHA-256 the tool
lock's), its source at `v10.2.2` (`f8ed8165`), cited by path in its
tree, the model's files under `hw/riscv/`; OpenSBI `ed70256d`; Linux
`v7.2` (`8d3ae592`); the IOMMU specification (*spec*) at `054005f4`;
the project's tree (*tree*) at `4e0daa11`.

**Evidence.** *src*: a source at its pin. *run*: R0 to R14 are the
characterization's runs (`RUNS.md`, each made as `a` and `b`); a
prototype's runs are named by image, with both copies (`d-run1/2`).
*source alone*: no run. `FACTS.md`, `RUNS.md`, `PROTO.md`, and the runs'
records are the characterization's, and are scratch, outside the
project's repositories. **Rows** are the plan's section 6
(plan:197-219).

**The machine**:
`-machine virt,aia=aplic-imsic,aia-guests=7,iommu-sys=on`, the gates'
`k3-like` CPU, `-smp 8 -m 8G`, `-bios`, `-kernel`, `-no-reboot`, one raw
drive, and `-device nvme,…,addr=02.0`. Hart 0 is the control hart, hart
1 the served VS domain's, and hart 2 the I/O service VS domain's, the
owner's.

| # | Fact | Evidence | Rows |
| --- | --- | --- | --- |
| **The machine and its masters** | | | |
| F-1 | The locked build offers `iommu-sys` and `riscv-iommu-pci`, and the functions `nvme`, `edu`, `virtio-blk-pci`, the PCIe root port, and two bridges. | run R0 | 1, 2 |
| F-2 | Eight harts with H, Sstc, Smstateen, `Ssaia` (`GEILEN` 7), and `Smaia`; RAM at `0x8000_0000`; the M-level APLIC at `0x0c00_0000` and the S-level at `0x0d00_0000`, both in MSI mode; per hart, an M file at `0x2400_0000` + hart × `0x1000`, and an S file at `0x2800_0000` + hart × `0x8000` with guest files 1 to 7 above it; ECAM at `0x3000_0000`; `time` at 10 MHz. | src `virt.c:82-103`, `hw/intc/riscv_imsic.c:375-389`; run R1 | 1, 6, 9 |
| F-3 | `iommu-sys=on` adds the IOMMU model as one 4 KiB register page at `0x0301_0000`, outside RAM, with no BAR, configuration page, or gate of its own; it serves every function of the one PCI host. With `riscv-iommu-pci` as well the tree loses its node (source alone), so the design uses `iommu-sys` alone. | src `virt.c:909-913`, `1876-1912`, `riscv-iommu-sys.c:179`, `riscv-iommu.c:2752-2761`; runs R0, R1 | 1, 4 |
| F-4 | The unit's function is `nvme` (`1b36:0010`, class `0x0108`) at 00:02.0: configuration page `0x3001_0000`; BAR0 64-bit, 16 KiB, which the boot code places at `0x4000_0000`; MSI-X with 65 vectors; `INTx` pin A; no controller memory buffer, persistent memory region, or virtual function. | run R1 (`info qtree`); `d-run1/2` (`info pci`) | 1, 2, 7 |
| F-5 | The host bridge's own function (`1b36:0008`) is at 00:00.0 (page `0x3000_0000`), with no BAR and no pin. Its identity `0x0000` has no device context, so the model refuses any request of it: a device with no holder, quiesced. | runs R1, R4; `d-run1/2` (`info pci`) | 1, 2 |
| F-6 | The other bus masters are both APLICs (their MSIs), the firmware-configuration device (its DMA), eight `virtio-mmio` transports (no backend), and the model (its own requests). Only a PCI function's requests pass the model, behind the function's gate; the rest, the model's table reads, records, `IOFENCE.C` words, and MSIs among them, reach memory untranslated. | src `hw/pci/pci.c:132-160`, `2878-2956`, `riscv-iommu.c:2571-2577`, `hw/intc/riscv_aplic.c:448`, `hw/nvram/fw_cfg.c:347-418`; runs R1, R2, R3, R11 | 1, 4, 12, 17 |
| F-7 | Four ways past the model, none a guest's write: a controller memory buffer or persistent memory region (neither configured), a host bridge's `bypass-iommu` (off; no `virt` option), class `0x0806` (read-only), and a function whose device model does not use its bus-master space for its DMA, as `virtio-blk-pci` without `iommu_platform=on` (in R12 its transfers landed outside every reach, with no record). The machine holds none of them, and the platform description's check refuses each (4.13). No device model issues a translated request or a page request, and nothing marks a device's fetch. | src `hw/nvme/ctrl.c:517-611`, `hw/pci/pci.c:647-660`, `2943`, `hw/pci/pci_host.c:240`, `include/hw/pci/pci.h:143`, `690`, `713`, `include/exec/memattrs.h:58`, `hw/virtio/virtio-bus.c:50`, `86`; runs R1, R12; source alone (`FACTS.md` 6.3, 10) | 1, 12, 13, 17 |
| F-8 | A device's transfer runs on QEMU's own loop, whatever the harts do: the function can rewrite the I/O service VS domain's memory while hart 2 runs the monitor's code (K8). | src `hw/misc/edu.c:180-189`; runs R2, R6, R9, `b2-run1/2` | 11, 12, 15 |
| F-9 | The pinned OpenSBI programs no IOMMU and no PCI function, and sets up each hart's M-level file alone. It writes the APLICs' delegation and MSI addresses without the lock bit; read outside: source 34 delegated (`sourcecfg` `0x400`), `smsicfgaddr` `0x28000`, `smsicfgaddrh` `0x300000` (LHXS 3). | src OpenSBI `lib/utils/irqchip/aplic.c:250-357`, `lib/utils/irqchip/imsic.c:255-300`; `d-run1/2` | 4, 6, 15 |
| F-10 | The MVP boots by `-bios` and `-kernel`; neither flash bank has a drive, and no device has a `bootindex`, so no PCI function is a boot source. The namespace is a raw image file outside the machine, which outlives the run. | run R1 (`drive = ""` on both `cfi.pflash01`); the runs' command lines | 2, 10, 13 |
| F-11 | Each hart has 16 PMP entries; under plain PMP a VS-domain hart's profile inherits five (the firmware's two, the M-level APLIC and IMSIC, the timer). With the file's page out (F-50), anchor's VS domain 1 needs 10 (11 with that page in, as prototype B had it), or 9 with two declared pages; the control profile and VS domain 0 need 8. The descriptor tools allow a profile ten, as Smepmp does, so the owner's keeps one free under either. | counted on D's images, twice (`pmp-count-d-final-1/2`); `b2-run1/2` | 3, 5, 6, 18 |
| F-12 | As built in D, no S-mode access of harts 0 to 2 reaches the model's page, the tables' extent, the ECAM window, any S or guest interrupt file, or either APLIC (the M-level one by an M-only entry); hart 2 alone reaches BAR0, rw. The PMP registers read outside equal M-mode's record. D put the model's fault queue outside the tables' extent (32 KiB at `0x1_1811_0000`), where no PMP entry of harts 0 to 2 reached it either; the design puts it inside the extent (4.4). | `d-run1/2` (`pmp-decode.json`) | 4, 6, 7 |
| F-13 | Under the boundary, a hostile monitor on hart 2 that stores to the model's `tr_req_iova` and `ddtp`, the device context's `ta`, and a leaf of the device's table traps each time (`scause` 7; `pmp_faults=4`), and nothing changes. With the boundary off they land, and the leaf gives the device a page of the served VS domain. | `c-run1/2` against `c-hookoff-run1/2` | 4, 12 |
| F-14 | Code that the owner's hart runs after its confinement must lie in its executable extents: a VS-domain hart's profile holds no boot-only text. (In one run of a prototype a call into the boot text faulted, cause 1; this fact does not rest on that run.) Boot code that it runs before must lie in the boot text: placed in the VS-domain-hart text, the handoff gave four C10 findings. | tree `planning/mvp-m11-plan.md:523` (D-5's profiles); `rolecheck-d` (twice) | 15, 18 |
| F-15 | On `d` and `d-armfail` the image checker gives no C7 or C10 finding, and 37 others, each a rule that the design changes: the stub's shape (2: D calls the handoff from the confine entry, before the confine), the resume tail's checks, the CSRs `vsiselect`, `vsireg`, `hstateen0`, `hstatus`, and `hideleg`, and the scratch hook. C7 judges calls alone, so hart 0's poll passes unseen. | tree `mvp/tests/check-image.py:7280-7327`; `rolecheck-d` (twice each) | 8, 15, 18 |
| **The IOMMU model** | | | |
| F-16 | It reads `capabilities` `0x0000_0078_e2cf_4f10` and `fctl` 0: version 1.0, second stage Sv32x4 to Sv57x4, `MSI_FLAT`, `MSI_MRIF`, `ATS`, `DBG`, `PAS` 56; no `Svpbmt`, `AMO_HWAD`, or `T2GPA`. Only `fctl.BE` and `fctl.WSI` are writable. | src `riscv-iommu.c:2441-2508`, `2525-2527`; runs R2, R3 | 4, 5, 6 |
| F-17 | At reset it goes to `Off`, its queues off, `ipsr` 0, both caches empty; `Off` with no context cached refuses every request (`DMA_DISABLED`). After a system reset it read `Off` and refused edu's queued transfer, with no record. | src `riscv-iommu.c:1020-1219`, `2605-2638`; runs R3, R9 | 4, 8, 10 |
| F-18 | Nothing locks a register, and every write is taken whatever its attributes. The mode register goes from `Off` or `Bare` to any mode, and from a directory mode to `Off`, `Bare`, or the same mode with another directory. So whoever can write the page, a device whose reach maps it among them, can turn translation off, repoint the directory, or make the model write anywhere (F-23). | src `riscv-iommu.c:1739-1776`, `2207-2323`; run R7; `c-reach-run1/2` | 4 |
| F-19 | It caches device contexts and translations; a cached entry applies without reading memory until `IODIR.INVAL_DDT` or `IOTINVAL.GVMA`, or a reset, empties it. Identity translations and MSIs are not cached. Two contexts with one `GSCID` share translations (source alone). | src `riscv-iommu.c:1285-1331`, `1604-1612`, `2636-2637`; run R6 | 4, 5, 8 |
| F-20 | With `MSI_FLAT` a device context is the 64-byte form; a one-level directory indexes 6 bits of device ID, so it holds `0x10`, refuses an ID of 64 or more (`TTYPE_BLOCKED`), and refuses one below 64 whose context is invalid (`DDT_INVALID`). A context with `tc.V` 0 refuses every request of its device once no valid copy is cached (`DDT_INVALID`); with bus mastering off as well, the unit is quiesced twice over (F-33). | src `riscv-iommu.c:1020-1219`, `1068-1078`, `1130-1131`; runs R4, R6 | 4, 5, 8 |
| F-21 | The second stage (`iohgatp` Sv39x4, 16-bit `GSCID`) checks the address's width before the walk, `R` for a read and `W` for a write, and A and D, which it never sets; it does not check `U` (source alone). A 2 MiB leaf works; the monitor's leaves are V R W X U A D (`0xdf`). | src `riscv-iommu.c:253-514`, `449-456`; tree `mvp/src/mvp-gstage.h:72-77`; run R2 | 5 |
| F-22 | The MSI page table is used only when the first stage is `Bare`: a write whose address matches the pattern under the mask is an MSI, and a basic-mode entry writes its data to its page. Only a write that carries a requester ID is one: a function's MSI-X message, not its data writes, so a data write to the route's address raises nothing. | src `riscv-iommu.c:221-238`, `278-295`, `556-707`, `2392-2416`, `hw/pci/pci.c:419-437`; spec `iommu_data_structures.adoc:684-693`; runs R5, R10 | 6, 12 |
| F-23 | The command queue takes `IOTINVAL.VMA` and `.GVMA`, `IODIR.INVAL_DDT` and `.INVAL_PDT`, `IOFENCE.C`, `ATS.INVAL`, and `ATS.PRGR`. An `IOFENCE.C` with `AV` writes 4 bytes of its choosing to any address, untranslated. | src `riscv-iommu.c:1670`, `1778-1959`; run R11 | 4, 8 |
| F-24 | A refused read returns zeros and a refused write is dropped; a refused transfer is split into 4-byte pieces, each recorded (but F-59). Records go to the queue's base, wherever software put it; none is written while the queue is off, and once it is full the model sets `FQOF` and drops the rest. | src `riscv-iommu.c:111-145`, `system/physmem.c:423-472`, `3169-3194` (the split), `system/memory.c:1335-1362`; runs R2, R3 (8,191 records, then `FQOF`), R10 | 4, 12 |
| F-25 | The debug registers translate one address for any device ID that software writes, through the cached context and translation where there are ones: they report the state in force, and a query that faults leaves a record. | src `riscv-iommu.c:1585-1596`, `2052-2090`; runs R14, `a-run1/2` | 4, 8, 12 |
| F-26 | The model signals a fault by a pulse on wired source 36 + vector (delegated to the S level), or by a 4-byte store of its MSI table's data to that table's address, untranslated, and only when its `ipsr` bit goes from 0 to 1. With `fqcsr.FIE` 0 it signals nothing and still records. | src `riscv-iommu-sys.c:118-120`, `144-161`, `riscv-iommu.c:93-109`; runs R11, `a-run1/2` | 6, 12 |
| **The handoff** | | | |
| F-27 | Hart 0's part, before `publish_blocks()`: `ddtp` read `Off`; FLR, `COMMAND` 0 read back; BAR0 placed, the copy taken, MSI-X enabled; the tables written with `tc.V` 0; `ddtp` 1LVL; `IODIR.INVAL_DDT`, `IOTINVAL.GVMA`, and `IOFENCE.C`, waited on; `COMMAND` `0x402` (decode, `INTX_DISABLE`, no bus mastering); the `INTx` route (F-46); its part of the record. It reads nothing back through the debug interface (with `tc.V` 0 that would leave a record). | `a-run1/2`; `d-run1/2` (the record) | 4, 8 |
| F-28 | The owner's part, run by hart 2 from the boot text before its confinement: hart 0's state checked; its guest file 1 cleared through `vsiselect`/`vsireg` (every word read back 0), and source 34's pending bit; `tc.V` 1, read back; `IODIR.INVAL_DDT` and `IOFENCE.C`; the window's first page and the MSI page table's entry (`0xa004407`) read back; bus mastering (`COMMAND` `0x406`); the record, then the arming word. The record's ticks from the FLR put the steps in the design's order but for two: the route's enable, which D made in hart 0's part (tick 10,618), and bus mastering, which D's owner set (tick 42,546) before its arming word; the design moves the first to the owner's part and the second after hart 0's *go* (4.8): hart 0's 0 to 12,665, the owner's 37,395 to 42,853, and its first guest entry at 17,025,550, which includes a hold of 2^24 ticks that D's images kept before that entry for the witness (section 5). | `d-run1/2` | 4, 6, 8 |
| F-29 | Hart 0 starts the owner's hart first, polls the arming word (one load; bound 2^24 ticks), and starts hart 1 only on `ARMED`: its poll ended 16,287 ticks after the owner's start, and it started hart 1 at 16,483 (`d-run1`; `d-run2`: 14,932 and 16,132). A failed step of the owner's puts bus mastering off and `tc.V` 0 back, invalidates, and marks the word failed. D's hart 0 wrote no word that the owner's hart waited for; the design adds one (4.8), which no run has shown. | `d-run1/2` (`be_mvp_m15_starts`) | 8, 15 |
| F-30 | With a read-back seeded to fail (step 4), neither VS domain is entered (both blocks' `entered` 0, both rings empty, hart 1 in the firmware's wait loop); hart 0 sets `ddtp` Off, invalidates every device, fences, and prints `BE_MVP:DETAIL m15-arm …` and `BE_MVP:FAIL boot`. Outside: `ddtp` 0, `tc` 0, `COMMAND` `0x402`, `CC` 0. | `d-armfail-run1/2` | 8 |
| **The function** | | | |
| F-31 | On the root bus the function's identity at the model is its BDF, `0x0010`, for transfers and MSIs alike. Behind a root port or a PCIe-to-PCI bridge, functions carried `0x0000` for transfers and their bus number for MSIs; behind a PCI bridge, the bridge's. No device model picks its identity; software sets only a bridge's bus number, and the machine has no bridge. | src `riscv-iommu.c:1341-1377`, `2742-2764`, `hw/pci/pci.c:1212-1280`; runs R4, `c-run1/2` | 1, 2, 5, 12 |
| F-32 | Every queue, PRP list, transfer, and MSI-X message of the function passes the model, and its driver chooses each address, so its owner can aim its requests anywhere. The addresses are the owner's GPAs: a GPA of the served VS domain's named the I/O service VS domain's own page. | src `hw/pci/pci.c:419-437`, `hw/nvme/ctrl.c` (`FACTS.md` 2); runs R10, `a-run1/2`, `c-run1/2` | 2, 5, 11, 12 |
| F-33 | The 4 KiB configuration page holds the BARs, the bus-master gate (`COMMAND`), the power state (PM capability at `0x60`), FLR, MSI-X enable and mask, and `INTX_DISABLE`. With the gate closed a request reads 0 and writes nothing, before any model, with no record. | src `hw/pci/pci.c:132-136`, `1798-1812`, `hw/nvme/ctrl.c:8898-8916`, `8963`; runs R8, R9 | 4, 7, 8 |
| F-34 | FLR clears `COMMAND`, the power state (to D0), the BARs, MSI, and MSI-X (its table and PBA zeroed, every vector masked), and runs the controller's reset (namespaces drained, queues freed); it leaves the bus-master gate open (F-56) and the namespace's data. | src `hw/pci/pcie.c:956-963`, `hw/pci/pci.c:539-581`, `hw/pci/msix.c:560-571`, `hw/nvme/ctrl.c:7888-7958`, `9477-9490`; run R9 | 8, 9 |
| F-35 | BAR0 holds the controller's registers and doorbells, then the MSI-X table, then the PBA, each 4 KiB-aligned, and nothing of another device or of the state of I32. `CC.EN` there controls the function alone: a controller reset changes no PCI state. | src `hw/nvme/ctrl.c:7888-7958`, `8162`, `8844-8870`; runs R10, `a-run1/2` | 7, 9 |
| F-36 | D3hot leaves BAR0 undecoded (all-ones, no fault) and keeps `COMMAND` and the gate; D1 from D3hot is refused; D0 decodes again at the old base, with no reset. Nothing in QEMU's NVMe stops its queues at D3hot (source alone). | src `hw/pci/pci.c:478-512`, `1718`, `1798-1805`; run R8 | 7, 12 |
| F-37 | `CC.EN` 0 drains each namespace (a fetched command completes: source alone), frees every queue (unfetched entries and held event requests are dropped), and writes `CSTS` 0; while it is 0 the controller issues no request. Run before any inbound PAUSE or TERMINATE is served, the stop kept queued commands from landing, and `TERMINATED` followed `CSTS.RDY` 0; left out, they landed. | src `hw/nvme/ctrl.c:1538-1539`, `7888-7955`, `hw/nvme/ns.c:693-696`; `d-run1/2` against `dc-run1/2`; `b2-run1/2` against `b2c-run1/2` | 9 |
| F-38 | Without its `CC.EN` write, `CSTS.RDY` stays 1 and the stop fails through the existing path: `BE_MVP:FAIL controls`, no `DOMAIN_TERMINATED`, no answer, no RESULT; the unit runs on. Hart 0's DETAIL reads `register=invalid wanted=0x460001 readback=0x1`: its table knows `henvcfg`, `hgatp`, and the VCSRs alone. The stop's bound must stay below the window of the VS domain that asked for the pause or the termination, 2^24 ticks, which restarts only when hart 0 takes one of that VS domain's records; D's bound, 2^22 ticks, does: with one tick of the owner's hart and one of hart 0's (2^18 ticks each) beside it, the answer comes within about 2^22 + 2 × 2^18 ticks (source and arithmetic). Only hart 2 can read `CSTS` (F-12). | `d-fail-run1/2`; tree `mvp/src/mvp-runtime.c:839-863`, `mvp/src/mvp-hartmain.c:466-508`, `mvp/src/mvp-layout.h:261`, `277` | 9, 15 |
| F-39 | Linux v7.2's PCI host driver reads and writes every function's configuration page on its buses, sizing BARs and writing `COMMAND` even with `linux,pci-probe-only`; its NVMe driver enables decode and bus mastering and needs one interrupt vector. Answered from hart 0's copy, the guest's writes left `COMMAND` `0x0406` and BAR0 `0x4000_0004`; passed through, they moved BAR0, and the stop failed. Releasing the driver leaves bus mastering and MSI-X on. | src Linux `drivers/pci/of.c:255-300`, `drivers/pci/controller/pci-host-common.c:228-255`, `drivers/nvme/host/pci.c:3197-3219`; `a-run1/2`; `c-run1/2` against `c-pass-run1/2`; `b2-run1/2` | 3, 7, 9 |
| F-40 | For a guest's load or store guest-page fault QEMU writes the transformed instruction to `htinst`, so the monitor decodes a trapped configuration access, or a store to the file's page, without reading guest memory. | src `target/riscv/cpu_helper.c:1908-2100`, `2229`; `a-run1/2`, `d-run1/2` | 7, 15 |
| F-41 | The I/O service VS domain's guest needs `CONFIG_PCI`, `CONFIG_PCI_HOST_GENERIC`, `CONFIG_BLOCK`, and `CONFIG_BLK_DEV_NVME`; its tree, written by `mvp/tools/gen-dts.py`, a path that the proofs' records bind, needs `ssaia`, a `riscv,imsics` node, and an ECAM host node with `msi-parent`. One Image for both VS domains (D's: `kernel_bytes` `0x2452a4`, 2,380,452 bytes; the base's `0x1f7cc4`, 2,063,556) changes payload sizes compiled into `be_mvp_runtime_main` in every image, which the litmus record pins; stage 1's readings check passes (100 citations). | src Linux `arch/riscv/Kconfig:191`, `drivers/pci/controller/Kconfig:147-154`, `drivers/nvme/host/Kconfig:5-8`; `a-run1/2`; `d-checks` (`litmus-check-*`, `readings-check-d*`) | 3, 16, 18, 21 |
| **Interrupts** | | | |
| F-42 | A 4-byte write of an identity at the start of an interrupt file's page makes it pending; no model checks who writes. A guest file's other state is reached only through its own hart's CSRs (`vsiselect`/`vsireg` with `VGEIN`, or the guest's own), so hart 0 cannot clear hart 2's file. | src `hw/intc/riscv_imsic.c:285-328`; runs R5, `d-run1/2` | 6, 8 |
| F-43 | With `smstateen`, VS-mode access to `stopei` needs `hstateen0` bit 58, to the other AIA CSRs bit 59, and to `siselect`/`sireg` bit 60; without them, or with `VGEIN` 0 or above `GEILEN`, it is a virtual-instruction exception. The owner's hart read back `hstateen0` `0x1c00_0000_0000_0000`, `VGEIN` 1, `hideleg` `0x440`. | src `target/riscv/csr.c:49-80`, `355-370`, `2674-2689`; `a-run1/2` | 6, 15, 16 |
| F-44 | The accepted entry reset writes `hstatus`'s controls, `hideleg`, `hie`, `hvip`, and `hgeie`, but not `hstateen0`; the accepted monitor delegates only VSTI, checks `hideleg` VSTI and `hgeie` 0, and never writes `hstateen0`. So the route's controls are set after the confinement: READY carries them as read before the route (`hideleg=0x40`), and the owner's resume tail checks them at every resume. | tree `arch/riscv/be/privileged.S:83-130`, `mvp/src/mvp-sbi.c:165-171`; `d-run1/2` | 6, 15, 16 |
| F-45 | The function's MSI-X message to the route's GPA lands in hart 2's guest file 1 through the MSI page table (vector 0, identity 2; Linux keeps 1 for its IPI), whatever the owner's G-stage root maps. Aimed at hart 1's guest file 1 or hart 2's S file it is refused, one record each; in `Bare`, or with the reach widened, it lands where aimed. | runs R5, R10, `a-run1/2`, `d-run1/2`, `c-run1/2` against `c-reach-run1/2` | 6, 12 |
| F-46 | The function's `INTx` pin A reaches S-level source 34 through the host's `interrupt-map`; no other function with a pin is on the bus. Hart 0 routes source 34, in MSI mode, to hart 2's guest file 1 at identity 255 (`sourcecfg` 6, `target` `0x810ff`, `domaincfg` `0x80000104`); `INTX_DISABLE` keeps it silent (`setip` 0). Raised once (`d3x`), it was pending in that file alone (`eip6` bit 63; every `hgeip` 0). | run R1 (`sys.dts`); `d-run1/2`, `d3x-run1/2` | 2, 6 |
| F-47 | Linux v7.2's IMSIC driver takes `riscv,num-ids` only if 63 ≤ n < 2048 and n & 63 = 63; 254 stopped the driver. The guest's tree gives 191, so identities 192 to 255 lie outside its range: 255 for `INTx`, 250 and 251 for a probe in D's images. | src Linux `drivers/irqchip/irq-riscv-imsic-state.c:749-753`; `d-run1/2` | 6 |
| F-48 | No confined hart's profile reaches either APLIC (F-12): only the firmware and the boot code, before activation, write the route. The owner hart's `VGEIN`, `hideleg`, `hstateen0`, and its own file's bits decide only what its own guest sees, and a hostile monitor there reaches neither the tables nor the model (F-13). | `d-run1/2`; `c-run1/2` | 6 |
| F-49 | Under direct delivery a VS-level external interrupt is taken only while the hart runs with V=1, and with `hgeie` 0 a guest file's pending identity raises no HS-level guest-external interrupt: the unit's messages do not interrupt the monitor on hart 2, and no other hart works for them. The build's flood run (NC-32) shows it on this machine. | src `target/riscv/cpu_helper.c:488-498`, `525-532`, `target/riscv/cpu.c:1071-1072` | 6, 12 |
| F-50 | The file's page is in neither the owner's G-stage root nor its hart's profile. A 4-byte VS-mode store to `seteipnum` or `seteipnum_be` (`htinst` a transformed `sw`) is emulated through `vsiselect`/`vsireg`; any other access from VS mode, and by source a store whose `htinst` is 0, reaches `be_mvp_handle_exit()`, and the VS domain fails (`guest-page-fault`); one from VU mode is denied there as any unmapped guest physical address is, and the VS domain runs on (by source; not run). Linux writes the page only to retrigger, and for IPIs only with Linux's `CONFIG_SMP`: it made no store to it here. | src Linux `drivers/irqchip/irq-riscv-imsic-platform.c:63`; tree `mvp/src/mvp-sbi.c:284`, `637-638`; `d-run1/2` (the probe's two stores), `d-file-run1/2` (`cause=0x15 htval=0x10004000 htinst=0x2781`) | 6, 7 |
| **Reset** | | | |
| F-51 | QEMU's system reset is a cold reset of the whole device tree, and RAM keeps its contents. With `-no-reboot`, as the gates and the prototypes' runs have it, a reset request ends the run, so no system reset executes. | src `system/runstate.c:507-547`; sm:2959; run R9 (made without `-no-reboot`) | 10 |
| F-52 | Neither interrupt controller has a reset handler, and a hart's reset writes none of `mip`, `hgeip`, `hgeie`, `hstatus`, `hideleg`, `hgatp`, and `satp`: an identity pending and enabled in a guest file before a reset was delivered after it, and an APLIC source kept its configuration and pending bit. Only the owner's handoff clears a guest file. | src `hw/intc/riscv_imsic.c:425-438`, `target/riscv/cpu.c:683-799`; run R13 | 8, 10 |
| F-53 | At a system reset the function's reset drains its namespaces and frees its queues, and every function's `COMMAND` is cleared with its gate left open, so what reaches memory before the next boot's handoff rests on the model's reset to `Off` (F-17). The order of the controller's reset and the model's was not read. | src `hw/nvme/ctrl.c:9456-9462`, `hw/pci/pci.c:539-568`; run R9 | 10 |
| **The CHERI variant** | | | |
| F-54 | The CHERI check's emulator, at its pin (`008944fe`, QEMU 8.1.0), has no RISC-V IOMMU model: no `riscv-iommu` source, no Kconfig option, and no `iommu-sys` option on its `virt` machine, which has the IMSIC. | src (that emulator's tree at its pin, its archive's SHA-256 the CHERI stack's pin) | 19 |
| **QEMU's defects and oddities, not relied on** (`FACTS.md` 11.1 to 11.14; `PROTO.md` 15 to 19; nothing sent, rule 15) | | | |
| F-55 | (11.1, 11.3) `edu`'s DMA buffer is not bounded (a transfer outside it is copied on, into the emulator's memory), and `edu` has no reset handler (a queued transfer survives a system reset). Not relied on: `edu` is never the unit; in NC-17's test build hart 0's boot code drives it before the starts, as the test's attacker, and no VS-domain hart starts (section 5). | src `hw/misc/edu.c:106-125`; run R9 | 2, 10, 12 |
| F-56 | (11.2) A function's reset reads `COMMAND` 0 but leaves the bus-master gate open until the next `COMMAND` write. Not relied on: the handoff writes `COMMAND` after its FLR, and the model refuses until the owner's arm. | src `hw/pci/pci.c:539-568`; run R9 | 8, 9, 10 |
| F-57 | (11.4, 18) The model serves a cached valid context whatever `ddtp`'s mode: its cache lookup comes before the mode, which it reads only on a miss, so `Off` passes requests until `IODIR.INVAL_DDT`. The specification's `Off` allows no inbound transaction, and lets an IOMMU keep what it cached until software invalidates it. Not relied on: each change of mode or context is followed by its invalidation and a fence, the arming failure's path among them (F-30). | src `riscv-iommu.c:1033`, `1296-1302`, `1739-1776`; spec `iommu_registers.adoc:367-369`, `434-437`; run R7 | 4, 8, 9 |
| F-58 | (11.5, 11.9, 16) Every untranslated fault record is typed a write, refused reads included, with `PV` set; a fault on the context's path is recorded as a read with `iotval` 0. Not relied on: records are read for their cause (21 or 23) and device ID alone. | src `riscv-iommu.c:516-554`, `1326`, `1642-1648`; runs R2, `c-run1/2` | 12 |
| F-59 | (11.6) A write through a cached read-only translation is refused with no record. Not relied on: an empty fault queue is never a witness; the witness reads the target. | src `riscv-iommu.c:1556-1657`; run R2 | 12 |
| F-60 | (11.7) The model takes only writes as MSIs; a read of an MSI address is walked through the second stage. Not relied on: the design's tables map no file's GPA, so such a read is refused. | src `riscv-iommu.c:289`; spec `iommu_data_structures.adoc:1230-1236` | 5, 6, 12 |
| F-61 | (11.8) The system model's `iommu-map` has a first entry of length 0, and a second that covers IDs 0 to `0xfffe`. Not relied on: the platform description takes identities from the source and run R4. | src `virt.c:909-913`; run R1 | 1, 13 |
| F-62 | (11.10) Functions behind a bridge carry `0x0000` (F-31). Not relied on: the machine has no bridge. | src `riscv-iommu.c:1345`, `2405`; run R4 | 1, 2 |
| F-63 | (11.11) The interrupt controllers and a hart's interrupt CSRs keep their state across a system reset (F-52). Not relied on: each boot's handoff clears the owner's file and source 34's pending bit before it arms the context. | run R13 | 8, 10 |
| F-64 | (11.12) The system model's MSI table ignores its mask bit. Not relied on: the model's interrupt stays off (`fqcsr.FIE` 0). | src `riscv-iommu-sys.c:148-161`; run R11 | 6 |
| F-65 | (11.13) The controller uses an MSI-X vector for a queue only if MSI-X was enabled when the queue was created. Not relied on: hart 0 enables MSI-X at its installation, before any queue exists (F-27). | src `hw/nvme/ctrl.c:5560-5562`; run R10; `a-run1/2` | 6, 8 |
| F-66 | (11.14, 19) The debug registers report every context fault as `DMA_DISABLED`, and answer an MSI address with itself (their MSI check comes before the tables). Not relied on: the read-back judges fault or no fault and the PPN, never the cause, and the owner reads the MSI page table's entry from memory (F-28). | src `riscv-iommu.c:221-238`, `288-294`, `2066-2069`; runs R14, `d-run1/2` | 8, 12 |
| F-67 | (15) A write of zero to `tr_req_ctl` starts a debug translation. Not relied on: no reach and no profile includes the model's page (F-12). | src `riscv-iommu.c:2052-2089`, `2307-2310`; `c-reach-run1/2` | 4 |
| F-68 | (17) A refused DMA buffer is bounced: one record for its mapping and one for each 4-byte access (129 for 512 bytes), and the controller completes the command with status 0. Not relied on: the evidence reads the queue and the witness, never a completion's status. | src `system/physmem.c:3711-3765`, `3779-3803`; runs R10, R12, `c-run1/2` | 4, 12 |

Counts: 68 facts: 53 of the machine (F-1 to F-53), of which the build's
runs show one on this machine (F-49); one of the CHERI emulator (F-54);
and 14 defects and oddities, not relied on (F-55 to F-68), which hold
every defect and oddity of QEMU's that the characterization found; the
one of Linux's that it found is in F-47.

## 3. The requirements, and where each is met

| Requirement | Met by |
| --- | --- |
| M15-R1, one unit, one owner, a whole boot | 4.2, 4.3; the records are static (4.14) |
| M15-R2, the platform description | 4.13, with its independent check |
| M15-R3, every device and master accounted for | 4.1, 4.4 ("Outside it"), 4.13 |
| M15-R4, each master of the unit confined | 4.5, 4.6; evidence in section 5 |
| M15-R5, the state that confines them | 4.4, 4.8 (the read-back and its offline check) |
| M15-R6, interrupts | 4.6 |
| M15-R7, controls, and what is done for the owner | 4.7 |
| M15-R8, the first handoff in I35's order | 4.8 |
| M15-R9, the unit follows its owner | 4.9 |
| M15-R10, the next boot | 4.10 |
| M15-R11, the owner's hart | 4.3 (its profile), 4.7; the hostile-monitor images (section 5) |
| M15-R12, the service | 4.11; the service's attacks (section 5) |
| M15-R13, evidence by a witness outside | Section 5 |
| M15-R14, the records | 4.13, 4.21 |
| M15-R15, proofs, and the CHERI variant | Section 6; 4.19 |
| M15-R16, records that name no kind of element | 4.13: the scenario's records speak of a unit, a reach, a route, and grants; the model's facts live in the generator and the installer alone |
| M15-R17, the monitor's reads | Section 6 lists the paths; section 5 has the test |

## 4. The decisions, row by row

### 4.1 The machine (row 1)

- **Options.** QEMU's `virt` machine at the locked build, with
  `aia=aplic-imsic,aia-guests=7,iommu-sys=on`, one raw image behind a
  `-drive if=none` node, and one `-device nvme` at `addr=02.0` on the
  root bus: no `cmb_size_mb`, no `pmrdev`, no bridge or port, no
  `riscv-iommu-pci`, and nothing that sets `bypass-iommu`. They belong
  to `io-service`'s runs alone; every other scenario keeps its machine,
  so no accepted record that names a machine changes.
- **The IOMMU model** is QEMU's system one (`iommu-sys`): one fixed 4
  KiB register page at `0x0301_0000`, wired sources 36 to 39, and the
  PCI host's `iommu-map`. Unlike QEMU's other RISC-V IOMMU model it is
  no PCI function, so it adds none to the bus (F-3).
- **The machine rows** are `k3-like`, with both toolchains, and
  `k3-like-smepmp`, with GCC, as for every accepted scenario (the M11
  plan's Q10): the boundary must be on (the plan's rule 17), and only
  those rows have PMP and IMSIC guest files (the `rva23` row's CPU has
  no PMP registers, and the `plic` row no IMSIC). Under Smepmp a profile
  has ten entries, and the owner's needs nine (4.3; F-11).
- **What the options add** (4.13 lists each): the model, itself a master
  (its reads and writes of its tables and queues); the NVMe function, a
  master; and the raw image, the function's persistent state, outside
  the machine. The masters already there stay: the harts, both APLICs
  (their messages), the firmware-configuration device (its DMA), and
  eight `virtio-mmio` transports, masters only with a backend, which
  none has (F-6).

### 4.2 The unit (row 2)

The one NVMe function at `00:02.0`, closed by itself (I30): its
configuration page (`0x3001_0000`) and BAR0 (16 KiB, at `0x4000_0000`)
are its own at the 4 KiB grain; on the root bus it carries its own
identity for transfers and messages alike, which no other function's
requests carry (F-31); it shares no extent of registers, no bus, and no
medium; and its reset and its controller's stop act on it alone (F-34,
F-37). Its `INTx` pin reaches APLIC source 34, which the swizzle also
gives to pins of other slots, all empty (4.6). It is no boot source: the
MVP boots by `-bios` and `-kernel`, and nothing in the boot chain reads
the image (I37 (b)). Q5's criteria, in order: every request that it can
issue passes the model, by the source and by runs; its owner can aim its
requests at any address; it serves blocks that another VS domain can
use; and Linux's own driver drives it, so the guest needs no new driver.

### 4.3 The scenario and the guest's kernel (row 3)

- **A scenario of M15's own, `io-service`**, beside the accepted three,
  with their layout's harts and windows. VS domain 0, on hart 1, is
  served; VS domain 1, on hart 2, is the I/O service VS domain and owns
  the unit. Two declared pages join them, as `anchor`'s do: a request
  page (VS domain 0 read and write, VS domain 1 read) and a response
  page (VS domain 1 read and write, VS domain 0 read). As in `anchor`,
  VS domain 0 holds the grants to pause and to terminate VS domain 1,
  through the accepted management extension and hart 0's decision
  against the sealed grants, so that the unit's stop is tested at its
  owner's pause and termination as well as at its shutdown and failure
  (4.9). With BAR0, and with its interrupt file's page in no profile
  (4.6), the owner's physical access profile needs nine PMP entries,
  within the descriptor tools' ten (F-11).
- **One Image for every plain scenario** (the MVP plan's D16 stands),
  its fragment gaining `CONFIG_PCI`, `CONFIG_PCI_HOST_GENERIC`,
  `CONFIG_BLOCK`, and `CONFIG_BLK_DEV_NVME`: in the characterization,
  2,063,556 bytes at the base became 2,380,452 (about 15% more) in D,
  whose Image's initramfs also held D's test programs (F-41). A second
  Image for the I/O service alone would need a second kernel in the boot
  image's payload, a change of its format, and a further raise of its
  budget. Every plain scenario's images change, as they did when the
  guest gained `/proc`, and the guest's pins, the kernel's
  reproducibility record, and the measurement references are derived
  again. Only `io-service`'s trees hold a PCI host or an `riscv,imsics`
  node, so in every other scenario the options find no device. The CHERI
  guest's fragment is unchanged (4.19).
- **The trees.** The I/O service VS domain's tree gains `ssaia` in its
  ISA list, an `riscv,imsics` node for its guest interrupt file's guest
  physical page with `riscv,num-ids` 191 (Linux takes only a count of
  the form 64k - 1, and the identities above it are the monitor's: 4.6),
  and a `pci-host-ecam-generic` node with `msi-parent` and
  `linux,pci-probe-only`. The device-tree generator is a path that the
  proofs' records bind (the plan's rule 11; section 7).

### 4.4 Who installs the state of I32, and what keeps it (row 4)

- **What it is** (I32 (d)): the model's register page; its tables in RAM
  (the device directory, the function's second-stage tables, its MSI
  page table, the command and fault queues, all in one extent, the
  tables' extent) and what it has cached of them; the function's
  configuration page (its BAR, its decode and bus-master gates, its
  power state, its reset, its MSI-X enable, its `INTx` disable); and the
  APLIC's state for the unit's and the model's sources. The owner hart's
  `hstatus.VGEIN`, `hideleg`, and `hstateen0` are not among it: by
  Revision 5's definitions a route ends at its delivery point, where the
  interrupt "first becomes pending in an interrupt file", and those
  controls act after it, on that hart's own guest alone (F-43, F-48).
- **Derived offline**, from the sealed configuration and the platform
  description, by a generator. The boot code installs what was derived,
  and checks nothing of it against a VS domain, a device, or a confined
  hart.
- **Installed by the monitor's boot code, before activation** (I32 (b);
  Q9). Hart 0, before it starts any VS-domain hart, writes all of it but
  the context's valid bit and source 34's enable, with the function's
  device context invalid, so that every request and message of the
  function is refused. The owner's hart, in its boot code before its own
  confinement, clears its guest interrupt file and source 34's pending
  bit, enables source 34, and arms the context, and, on hart 0's *go*,
  turns the function's bus-master gate on (4.8). Between its starts and
  its own confinement hart 0 reads one word that a VS-domain hart
  writes, and writes one that such a hart reads, both in the handoff's
  record in the tables' extent: the owner hart's arming word, which hart
  0 zeroes before the barrier and then only that hart's boot code
  writes, before its activation; and hart 0's decision word, which only
  that boot code reads, before its activation (4.8; section 8, items 4
  and 5). No hart installs anything after its activation (rule 17), and
  no M-mode code is added (rule 9).
- **Kept by K6's candidate (2)**: no confined hart's physical access
  profile includes the model's page, the tables' extent, the ECAM window
  (which holds the configuration page), or the APLICs' pages, and no VS
  domain's mappings do; the descriptor's check and the oracle's read of
  every hart's PMP registers show it (F-12). The model has no lock, and
  whatever writes its page can set it back to `Off` or `Bare` at any
  time (F-18), so this keeping is the whole of it. The function's reach
  holds none of them (I31 (c)), and its messages pass only to its route.
- **Outside it**, the masters that pass no element (the APLICs'
  messages, the firmware-configuration device's DMA) could reach the
  page and the tables (F-6). The APLICs' message addresses are the
  firmware's, in the M-level APLIC's page, which no confined hart's
  profile includes, and nothing drives the firmware-configuration device
  after the boot chain. The limit names each with what it can reach
  (I29), and every statement about the unit holds only while they leave
  the state alone.

### 4.5 The recorded reach (row 5)

The recorded reach of the function is the I/O service VS domain's
private window (64 MiB), read and write, with no execute, in
second-stage tables of the element's own: 32 leaves of 2 MiB, with A and
D set, under a `GSCID` of its own. The tables are built by the boot code
(section 4.4) in the extent that holds the state of I32. They map no
declared page, so the service copies (section 4.11), and nothing of I31
(c): not the monitor's memory or M-mode's, no device's registers, no
state of I32, and no interrupt file. The owner's own G-stage root is not
used as the element's: it maps the declared pages, with the owner's
rights, and it would put the reach under whatever writes that root.

### 4.6 Interrupts (row 6)

- **The sources** (the platform description): the function's MSI-X
  vectors (65), and its `INTx` pin on APLIC source 34. The model's own
  fault interrupt (sources 36 to 39, or its message table) is the
  element's, not the unit's.
- **The route of each MSI-X vector: direct delivery.** One MSI
  page-table entry maps the guest physical page of the I/O service VS
  domain's interrupt file to the owner hart's guest interrupt file 1
  (`0x2801_1000`). The function's messages pass the model only to that
  file, whatever address and data its owner writes in the MSI-X table
  (I31 (d); F-22, F-45). The owner hart sets `hstatus.VGEIN`, `hideleg`
  VSEI, and `hstateen0` bits 58 to 60 after its entry reset, and its
  resume tail checks them on every resume, with `hie`, whose VSEIE its
  guest's own enable of its external interrupt sets. So the owner's
  guest takes the interrupt itself: no hart takes a trap or does work
  for it, the monitor reads nothing that the device writes there, and
  its tick is untouched, since an interrupt pending at VS level is not
  taken while the hart runs the monitor (I33 (b), (c), (e)). This is the
  first of the three deliveries that section 13 of the plan leaves to
  this sign-off (section 8, item 1).
- **The file's page is in no mapping.** The guest's tree names its
  interrupt file's guest physical page, but neither its G-stage root nor
  its hart's profile maps it (A8's, A10's, and I22's lists have no place
  for it), which frees a PMP entry. A 4-byte store by the guest to its
  `seteipnum` faults to the monitor, which makes that identity pending
  in the guest's own file through `vsiselect` and `vsireg` (the third
  delivery). Any other access from the guest's kernel reaches the
  monitor's accepted exit path unchanged, which ends the VS domain, as
  an access outside its mappings does today; one from its programs is
  denied there as any unmapped guest physical address is, and the VS
  domain runs on. Linux made no such store in the characterization's
  runs; the emulation serves the driver's way of raising an interrupt
  again, and a test exercises it (F-50). The function's messages are
  unaffected: the MSI page table, not the G-stage, carries them.
- **The function's `INTx`: a route of its own**, so that A13 ("every
  interrupt source of an assigned unit has one route") holds as written.
  Hart 0's boot code routes source 34 through the S-level APLIC, in MSI
  mode, to the owner hart's guest interrupt file 1, at identity 255,
  which is above the 191 that the guest's tree gives it (the monitor's
  identity; the second delivery); the owner hart's boot code enables the
  source once it has cleared its file (4.8). The firmware has already
  delegated the source and set the APLIC's message addresses; no
  confined hart's profile includes either APLIC's page. The function's
  `INTX_DISABLE`, a control kept from the owner, keeps the source from
  being raised; with it cleared in a test build, `INTx` lands in that
  file alone (F-46). No other function sits on a pin that the swizzle
  gives source 34, so the route joins nothing to the unit (I30 (b)).
  Leaving the source unrouted would have rested on I30 (b) against A13,
  where Revision 5 is not of one mind (the plan, Q7).
- **The model's own fault interrupt: off** (`FQCSR.FIE` 0, sources 36 to
  39 inactive). It signals nothing, to any hart, at any rate (I33 (f)).
  Its refusals are recorded in its fault queue, which the witness reads
  where R5.3 allows. The tests do not rest on it: they read the targets
  (F-24, F-26).

### 4.7 The owner's mappings, and what is done for it (row 7)

- **BAR0 is in the owner's G-stage root and in its hart's physical
  access profile** (16 KiB: the registers and doorbells, the MSI-X
  table, the PBA). All of it is the function's own, and none of it is
  state of I32 (I34 (a)): the MSI-X table's addresses decide nothing,
  since the model decides where a message lands (I31 (d)).
- **The configuration page is in neither.** The guest's accesses to its
  configuration window fault to the monitor on the owner's hart, which
  answers them from a copy and keeps the guest's writes in it. Hart 0's
  boot code takes the copy when it installs the function's
  configuration, before it publishes the blocks; from then on the copy
  is the owner hart's own word, as I15 has a block's words change writer
  at the barrier. So no access and no control operation is made for the
  owner (I34 (b) is not engaged), and the manifest records no grant of
  either. The function keeps the configuration that the boot code gave
  it: decode on, `INTx` disabled, MSI-X enabled with every vector masked
  until the owner's driver unmasks it in BAR0. The bus-master gate, the
  power state, and the function's reset are controls kept from the
  owner: with the window passed through, the guest moved BAR0, and the
  stop could no longer reach the function (F-39).
- **Nothing else is done for it.** It asks for no control operation, and
  stops its function's controller itself, in BAR0 (4.9).

### 4.8 The handoff (row 8)

In Revision 5's order, `with the boot chain`, `quiesced`, `cleared`,
`confined and routed`, `exposed` (R5.8, Part 6), shown from the boot
code's own record. In the characterization's form of it, timed from hart
0's reset of the function, hart 0's part took about 1.3 and 1.2 ms in
its two runs, the owner's about 0.5 and 0.4 ms (reading back one leaf),
and hart 0's wait for the owner about 1.6 and 1.5 ms (F-27 to F-29):

| State | Who | What, and its record |
| --- | --- | --- |
| Quiesced | Hart 0, before any VS-domain hart starts | `ddtp` read `Off` before the launch measurement (any other mode is a failure: something ran before); the function's identity, BAR0's type, and its MSI-X table's place checked (fields that its reset does not change), and BAR0's size probed by the usual write of all-ones and read back; the function reset (FLR), which clears the BAR, its `COMMAND` read back 0; BAR0 placed and checked, the copy taken, MSI-X enabled with every vector masked, and `COMMAND` set to decode, with `INTx` disabled and bus mastering off; the state of I32 written with the function's context invalid, `ddtp` set, the directory invalidated, a fence waited on. Every request and message is refused |
| Cleared | Hart 0, then the owner's hart, before its confinement | Sources 36 to 39 inactive; source 34 given its route's configuration, disabled and not pending (hart 0); the owner hart's guest file 1 cleared, delivery off, every identity disabled and not pending, each word read back, and source 34's pending bit cleared again (the owner's hart: only that hart can clear its own file). A reset leaves the file as it was (F-52) |
| Confined and routed | The owner's hart, before its confinement | The context made valid; source 34 enabled; the directory invalidated for the function and a fence waited on; the translation in force read back through the model's debug interface for each leaf of the reach, and the MSI page table's entry from memory, since that interface answers an MSI address with itself (F-66); the arming word written armed |
| Exposed | The owner's hart, once hart 0's decision word reads *go* | Bus mastering on, read back; the hart confined (M11); its route's controls set; its first guest entry, from which its guest can reach BAR0 |

Each step of the boot code writes its time and result in the tables'
extent, which no confined hart's profile includes; the witness reads
that record after the run, and an offline check, independent of the
generator, compares the read-back with what was derived. The Exposed
row's later steps, after the hart's confinement, show in its READY, its
block's `entered`, and M-mode's records. Five of the table's steps are
the design's, and no run has shown them: `ddtp` read before the launch
measurement (the prototypes read it after); sources 36 to 39 made
inactive by hart 0 (the prototypes wrote none of them, and found them
inactive); a read-back of every leaf of the reach (the prototypes read
back the window's first page); source 34's enable in the owner's part,
after the clearing, so that the route comes into force in Revision 5's
order (the prototypes enabled it in hart 0's part, with its pending bit
cleared and the function's `INTx` disabled, so that nothing could
cross); and hart 0's decision word, with the owner's wait for it before
bus mastering (the prototypes' owner turned bus mastering on before it
wrote its arming word, and waited for nothing).

**The start order.** Hart 0 starts the owner's hart first, and then
waits, bounded, for that hart's arming word. It polls only the tables'
extent, which only boot code before its hart's activation writes, and
it makes no firmware call while it waits. The decision is hart 0's
alone, and it writes it once, in a word of the record that only hart 0
writes: *go*, once the arming word reads armed; *abandoned*, when that
word reads failed or the bound passes. The owner's boot code, once it
has armed, waits for that word, with no bound of its own, before it
turns bus mastering on: on *go* it exposes the unit and goes on to its
confinement; on *abandoned* it makes the context invalid again,
invalidates the directory, waits on a fence, records the undoing, and
stops: it posts no READY and never enters its guest. It never undoes
its arming on its own: hart 0's bound ensures that the word is written,
and if hart 0 fails first, its failure ends the run. Hart 0 starts the
other VS-domain hart only once it has written *go*. So no VS domain
starts unless the unit's master is confined and routed: R5.3's case
for I35, "A master's confinement cannot be installed, seeded: the unit
stays quiesced and no VS domain starts"; and while the owner's boot
code may still be writing the unit's state, hart 0 writes none of it.
M11's image rule that keeps hart 0 from reading what a VS-domain hart
can write between its starts and its own confinement (its D-6) judges
the calls on those paths, and the poll makes none; a rule of
`io-service`'s own checks that the poll loads the arming word alone and
stores the decision word alone (section 8, item 3). The owner's
handoff is boot code that a VS-domain hart runs, so it lies in the boot
text, and hart 0 starts the owner at an entry of `io-service`'s own.
That entry runs the handoff and then joins the accepted confine entry,
whose rule stays as it is; a rule of its own checks the new entry.

**Each failure fails closed** (I35 (e)):
- Every wait on a failure path is bounded, and at its bound hart 0
  still prints its `BE_MVP:FAIL` line and requests shutdown.
- A failure on hart 0, before it starts the owner's hart, has hart 0 set
  `ddtp` to `Off`, invalidate the directory, wait on a fence, print a
  `BE_MVP:FAIL` line, and request shutdown. (On its own failures the
  prototypes' hart 0 set `ddtp` to `Off` alone, which was safe since no
  context was yet valid; the design invalidates and fences on every
  failure.)
- A failure on the owner's hart before it has armed makes the context
  invalid again, invalidates the directory, waits on a fence, and writes
  the arming word failed; bus mastering is not yet on. That hart sends
  no READY and never enters its guest. Hart 0, once it reads failed,
  writes *abandoned*, and then, the owner's last write of the unit's
  state behind it, sets `ddtp` to `Off`, invalidates, fences, prints
  `BE_MVP:FAIL`, and requests shutdown (F-30).
- An arming that does not finish within hart 0's bound has hart 0 write
  *abandoned*, print a `BE_MVP:FAIL` line, and request shutdown, and
  write nothing of the unit's state, which the owner's boot code may
  still be writing. Bus mastering stays off, since the owner turns it on
  only on *go*, so the unit stays quiesced whatever that hart has armed;
  if it reaches its wait, it undoes its arming as above.
- A failure after *go*, in bus mastering's read-back, has the owner's
  hart turn bus mastering off and fail as a VS-domain hart fails before
  its READY today, with a FAIL record on which hart 0 ends the run. In
  the other failures after *go* (a refused `confine`, which parks the
  hart in HS mode at once; a route control's check; a READY check) bus
  mastering stays on, but the unit stays confined and routed, and its
  controller is off since the FLR (`CC.EN` 0: F-34, F-37), with every
  vector masked, so it issues no request and no message; hart 0 ends the
  run on the owner's FAIL record, or, after a refused `confine`, at the
  bound on READY, as today. In each, the unit was confined and routed
  before any other VS domain started.

In each case before *go*, no VS domain starts, as when a validation
fails (I6).

### 4.9 What quiesces the unit after its owner stops (row 9)

- **The unit's own stop, from the owner's hart.** At its owner's pause,
  termination, shutdown, or failure, the monitor there clears `CC.EN`,
  waits for `CSTS.RDY` to read 0, and masks every MSI-X vector, before
  it publishes the record that reports its owner stopped. At a pause or
  a termination it reads its inbound records once more, through a copy
  of its reader's view, to stop the unit before the request is answered
  (section 8, item 4). Hart 0 reports the pause or the termination done
  only once it has that record (I36 (b)). In the characterization, a
  command queued just before the termination did not land; in a control
  image without the stop, it landed after the termination had been
  reported (F-37).
- **The boundary is `CSTS.RDY`.** QEMU's controller completes a command
  that it has fetched before `CSTS.RDY` reads 0 (by the source alone),
  and drops one that it has not (F-37). The design relies on nothing
  after that boundary, and on nothing about the commands before it.
- **A stop that fails fails the run.** If `CSTS.RDY` does not read 0
  within the bound (2^22 ticks, well inside the window of the VS domain
  that asked: F-38), the owner's hart posts the existing FAIL record,
  through the ring's own functions, and hart 0's lines name the unit's
  stop and `CSTS` (F-38). The pause or the termination is never reported
  done, and no SBI result code is added.
- **What it holds against.** The stop is HS-mode code on the owner's
  confined hart, through registers in its profile: it holds against
  every VS domain, every other confined hart, and the device. It does
  not hold against Revision 4's attacker on the owner's hart, which
  "keeps its own VS domain" and that VS domain's units (I36 (b)'s
  exception); I31 to I33 still bound the unit, since the state of I32
  does not change. The stop installs, protects, and enforces nothing
  (rule 17).
- **Not taken:** an element below HS mode that invalidates the unit's
  context (M-mode code, which the static case does not need); and the
  end of the run alone, which covers no pause or termination after which
  the run goes on.

### 4.10 Reset, and the next boot (row 10)

- **No system reset executes in a run**: the gates run QEMU with
  `-no-reboot`, so a reset request ends the run (R5.9).
- **What a reset leaves** (F-51 to F-53): the model `Off`, refusing
  every request and message until the boot code installs its state; the
  NVMe controller drained; the function's bus-master gate open; and the
  interrupt files and the APLIC as they were, a pending identity among
  them. So every boot's handoff clears the owner hart's guest file and
  the APLIC's sources of the unit and of the model before anything is
  routed (4.8), whatever the boot before left (I36 (d)).
- **The interval of a reset.** Whether the function's requests drain
  under the model's state before the model's own reset or after it was
  not read, so the platform description does not establish that a reset
  bounds the unit's master, and the limit names the unit's owner (I37
  (c); 4.17).
- **The next boot's sources.** The unit is no boot source, by the
  platform description and by the boot chain's own configuration (I37
  (b)).

### 4.11 The service's protocol (row 11)

- **The rings.** The request page holds a ring that VS domain 0 alone
  writes, and the response page one that VS domain 1 alone writes. A
  record has a sequence number, an operation (read or write), a block
  number, and one 512-byte block (a write's data, or a read's answer),
  with a status in a response. The monitor reads neither page and
  interprets no record (M15-R12).
- **The service copies.** VS domain 1's program copies each block
  between the declared page and a buffer in its private memory, where
  the kernel's NVMe block device reads or writes it. The device's reach
  holds no declared page, so nothing that the device does touches VS
  domain 0's view but through the service's own writes to the response
  page.
- **Both ends are programs** that map the declared pages through
  `/dev/mem`, as `te-poc`'s and `anchor`'s do. Nothing of the protocol
  is the guest kernel's, and a VS domain that is not Linux (S3-C.2's
  step (6)) could serve or use it unchanged. They are user programs in
  the guest's initramfs, `GPL-3.0-only` as `mvp/guest/mvp-init.c` is;
  the plan's rule 10, which makes a file "built into, or loaded by, the
  guest's kernel" `GPL-2.0-only`, is read as code that runs in the
  kernel, as the management module does (section 8, item 4).
- **What it takes from MVP 1.0**: the discipline of one writer for each
  page, and nothing of M7's console contract (its rings and its DBCN
  read), since the monitor is no party to it (section 8).
- **What VS domain 0 relies on**: the monitor, for its private memory
  and the declared pages' rights; not the service, which may answer
  wrongly or not at all. Its program checks each answer's sequence
  number and status, and runs on when the service withholds one
  (M15-R12).

### 4.13 The records and identities (row 13)

- **The platform description** is a record of its own, generated offline
  by a new tool from the machine row's options and a table of the `virt`
  machine's layout at the pinned QEMU tag. It lists every device and
  every master with what R5.8's row for it asks, and what is not
  established. It is checked against a source that its generator does
  not use: the running machine's own `dumpdtb`, `info qtree`,
  `info mtree -f`, and `query-pci`, read by the harness. The check
  refuses each way past the model that F-7 lists: a function whose model
  does not use its bus-master space, a host bridge with `bypass-iommu`,
  a function of class `0x0806`, and a controller memory buffer or a
  persistent memory region. Its identity, the SHA-256 of its canonical
  form, is bound into the configuration identity (M15-R14).
- **The scenario's format and the manifest** gain the unit's records
  (R5.8's row for the manifest): its assignment; its registers' extents
  in its owner's G-stage root; each route; each master's recorded reach;
  the unit's registers that its requests may reach (none); its grants of
  control operations and of accesses (none); the acts that quiesce,
  clear, and restart it; every other master's kind under I29; and the
  owner whom I37 (c) has the limit name.
- **The partition descriptor** gains, in `devices`, the unit and BAR0's
  extent for hart 2's profile alone, and, in `interrupts`, the unit's
  sources (R5.8's row for it). No element below HS mode installs
  anything, so it has no entry of that kind. Its identity is its own, as
  today.
- **The measurement log** keeps its format, its record kinds, and its
  streams, and records neither the platform description's identity nor
  the descriptor's, which R5.8 leaves to this plan. `io-service`'s
  images take `te-poc`'s record sequence (`v2`), whose
  `configuration-identity` record is informational and build-recorded,
  never extended into a register, as today: the platform description
  reaches the log through it. The log profile gains `io-service`'s row
  and nothing else. No measurement is added, so I19 and I20 are
  unchanged and S3-C's stop (c) does not apply.
- **The authority report** gains, additively, an entry for a unit as a
  subject, a unit's register extents, and a route's delivery point,
  for which R5.8, Part 4, finds no place in its schema and says that
  "The plan that builds a generator extends it". A scenario without a
  unit has today's report, byte for byte.
- **What the boot code checks, and where.** R5.8, Part 4, leaves to this
  plan "which of these checks the monitor's boot code repeats before it
  seals". None runs before the seal: they read the machine, not the
  configuration, which `seal_config()` seals before any of them could
  run (`mvp/src/mvp-runtime.c:3148`). Each runs after the seal and
  before any VS domain is entered, and each that fails fails the boot
  closed (4.8): that `ddtp` reads `Off`, before the launch measurement;
  that the function at the recorded identity has the recorded vendor and
  device, BAR0's recorded type, and the recorded MSI-X table, before its
  reset (fields that the reset does not change), and BAR0's recorded
  size, probed by the usual write of all-ones and read back, before the
  reset clears the BAR; that BAR0 is at the recorded address, once hart
  0 has placed it; that the model offers the one-level directory, the
  second stage's mode, and the MSI page table, before hart 0 writes its
  state; that the owner hart's G-stage root holds BAR0's leaves and no
  other root holds a device's, by the walker's own check (section 8,
  item 3), which is A9's check in the extensional form of R5.8, Part 7;
  and, last, on the owner's hart, after its start, that the route's
  guest interrupt file exists, before its boot code clears it. Each
  register is read at the offset that the platform description records,
  and no pointer that the code reads is followed. A9 to A13 run offline
  only. These checks are the design's: the prototypes made them after
  the seal, followed the function's capability pointers, and read none
  of the model's capability bits.

### 4.14 The triggers (row 14)

Neither fires for `io-service` (Revision 5, Part 5, U4). The capability
trigger: the assignment, the reach, the route, and the grants (none) are
static records of the manifest; nothing is designated, delegated,
attenuated, or revoked while the system runs. The runtime-check trigger:
every denial follows from derived state alone (the absence of an entry
in the model's tables or its MSI page table, of a route, or of a leaf
for a register); no case exists in which the derived state allows and
the policy denies.

### 4.15 Execution contexts and firmware calls (row 15)

None is added. No M-mode code is added, and no firmware call: each role
and phase makes the calls that it makes today. The owner hart's boot
code does its part of the handoff before its confinement, in the boot
OpenSBI domain, by loads, stores, and its own hart's CSRs, with no
firmware call. Nothing changes in what a guest can call, so the SBI
implementation version does not change (D8). D8's "exact accepted-exit
set per scenario" holds: `io-service`'s set (its `scenario.json`'s
`accepted_exits`, which the scenario generator and the image checker
hold) is `anchor`'s with two kinds of exit added, both on the owner's
hart alone: loads and stores to its configuration window, and the store
to its interrupt file's page. The monitor's new paths on the owner's
hart (those two exits, answered in the monitor, and the unit's stop)
are HS-mode code on that hart, in its role's extents.

### 4.17 The claim's words (row 17)

Fixed now, within the plan's section 10; the result's page uses these
words, with each `[n]` replaced by its count.

> **Clause.** Under emulation, in one fixed scenario (`io-service`) on
> QEMU's `virt` machine at the pinned build, with its system IOMMU
> model, the pinned firmware, and the pinned Linux guests, by a witness
> outside the machine (its memory, its devices' and harts' registers,
> and the disk's image file, read after it had stopped): each of [n]
> tested requests of the assigned NVMe function that was aimed outside
> its recorded reach read nothing and changed nothing; each of [n]
> tested messages of the function that was aimed anywhere but its
> route's delivery point made nothing pending and changed nothing; its
> tested interrupts were delivered to its owner's guest interrupt file
> and nowhere else; in each of [n] tested boots its first handoff passed
> through quiesced, cleared, confined and routed, and exposed, in that
> order, once, by the boot code's own record, checked offline; in each
> of [n] tested pauses and terminations of its owner it was stopped
> before the pause or the termination was reported done; and each of [n]
> tested attacks of the I/O service VS domain on the VS domain that it
> serves left that VS domain's private memory unchanged.

> **Limit.** Nothing is claimed of hardware, of the K3, or of a board,
> and nothing of every request, message, or attack: the claim speaks of
> each tested one. The emulator's IOMMU model is trusted, and its
> correctness is not shown. So are Revision 5's other new trusted rows
> on which `io-service` rests (R5.5): the boot code of hart 0 and of the
> owner's hart, which writes the state of I32 before its own hart's
> activation, and the confinement of every hart, which keeps that state
> from every hart after it; the interrupt controllers, and whatever
> writes the routes, the firmware among them, which writes the
> controllers' delegation and message addresses without their lock; the
> platform description, its generator, and its offline check, and the
> offline check of the state read back; the boot chain, for the state in
> which it leaves every device, the function's own reset, for what it
> clears, and the path between the function and what it addresses,
> through the model, for bringing to an end every request that was
> issued before, whether or not the model has passed it; the devices,
> and the holders of devices, that no configuration of the project's
> controls; and the platform's reset. R5.5's row on whatever performs
> control operations, and accesses made for an owner, is not engaged
> here: none is made for the owner (4.7). The masters that pass no
> enforcing element are named, with what they can reach: both interrupt
> controllers, whose messages can reach every interrupt file, at
> addresses that only M-mode and the boot code write; the
> firmware-configuration device, whose DMA can reach, untranslated, all
> of memory and every device's registers and controls, the monitor's
> memory and M-mode's, the state of I32, and every interrupt file among
> them, though nothing drives it after the boot chain; and the IOMMU
> model itself, whose own reads and writes go where its state directs,
> in the tables' extent alone. Every statement of the clause holds only
> while they leave those alone. The unit's owner is named as able to
> change what a later boot runs (I37 (c)). Revision 4's attacker on the
> owner's hart keeps that VS domain's unit (I36 (b)). This machine
> cannot show, and the claim does not speak of: an IOPMP, which it does
> not model; a request that calls itself translated; a fetch by a
> device; a device that picks its own identity; an identity that a
> register field sets, since the machine has no bridge; caches, so
> neither a master that is not coherent with the harts nor an owner's
> cache-block operations; a clock or transceiver control of one device;
> and a system reset, since none executes in a run: not in the middle of
> a handoff or of a transfer, with an interrupt pending or a route
> installed, or with a master that issues requests from the reset on.
> M15 builds no restart of an owner with its unit kept, and no second
> assigned unit. The design's own choices leave out, as the sign-off of
> the design accepted: a table in an owner's memory that an element
> reads for the master, since the model reads only tables of its own;
> and the state in force after a reset that an owner asked for, since no
> owner is granted one. Stage 1's theorems are not asserted of
> `io-service`'s images: their hart 0 starts the I/O service VS domain's
> hart first and waits for its arming, and their owner's monitor serves
> two kinds of fault that those theorems do not describe. Availability
> is outside the claim.

### 4.19 CHERI (row 19)

The device path is off for the CHERI variant (Q14's default), and its
check stays a gate. Its emulator, the CHERI QEMU at its pin (a QEMU
8.1.0 base), has no RISC-V IOMMU model, by its source
(F-54), so this machine's path could not run there. No
CHERI mechanism is used. A unit's register extent, a master's reach, and
a route are each a bounded authority that a capability could carry;
whether one should is for the CHERI platform line.

### 4.20 The first configuration in the security model (row 20)

Not proposed (Q13's default): the claim's page, the ledger, and the
result are its record. Revision 5's Instance 4, worked by hand, already
has the shape of `io-service`; the result says where they differ.

### 4.21 Which of Revision 5's inventory M15 lands (row 21)

| R5.8, Part 7's row | In M15 |
| --- | --- |
| The abstract model | Not in M15 (Q16): no accepted model file is edited |
| The executable model and the MVP's policy checker | The MVP's checker (`mvp/tools/policy-check.py`) lands (Q16): the `device` class, a unit as a subject, A9 to A13, and A1, A3, A5, A6, and A8 as R5.7 reads them. It is a path that the proofs' records bind (section 7). The executable model (`model/src/`) is not in M15 |
| Model 0.2's validator, and what the monitor's boot code validates | What the boot code validates: 4.13's checks. Model 0.2's validator is not in M15 |
| The scenario's format | Lands (Q16) |
| The partition descriptor | Lands (Q16) |
| Fixtures | Instance 4's ten failing variants land as the MVP checker's seeded defects, beside `io-service`'s own; as `model/` fixtures, not in M15 |

The plan's row 21 also asks how the model's differential check treats
the new scenario: it keeps its four accepted instances, and no model
file is edited. The MVP checker's own tests check `io-service`'s policy,
against its seeded defects and Instance 4's failing variants.

## 5. The evidence for each invariant

R5.3's rule for a negative case, and the plan's:

> the test passes when the forbidden request "reads nothing and
> changes nothing", by a witness outside the device, its owner, and
> every hart that the test treats as breached. (sm:2417-2419)

> Each negative case of R5.3 is tested, or the design lists it with
> its reason. One that this machine cannot show goes to the limit by
> name. One that the design's own choices leave out is a drop, which
> the design names for its sign-off (stop 5). (plan:186)

`sm:` is `planning/security-model-v1.md` and `plan:` is
`planning/mvp-m15-plan.md`, at `origin/main` (`4e0daa11`). NC-1 to
NC-60 number R5.3's negative cases in the order of its table
(sm:2448-2457); F-n are section 2's. **Classes:** *tested*;
*limit*: this machine cannot show it, and the limit names it
(plan:366-371); *not M15's*: it needs a restart (plan:122) or a second
assigned unit (plan:395-398); *drop*: the design's own choices leave it
out, named for the sign-off (stop 5).

**The witness** is read outside, after the machine has stopped: QMP
reads of memory and of device registers (ECAM, BAR0, the model's page,
the APLICs), each hart's registers, M-mode's records, and the image
file. *Canaries* are words that hart 0 writes before its confinement;
*receivers* are files armed so that a message shows in `hgeip` or `mip`.
*The hold*: in the test images of NC-34 and NC-45, the owner's hart,
after it has set its route's controls and before its READY (so before
its first guest entry), waits 2^24 ticks, and then reads its guest
file's pending and enable words into its state page, which no reach
includes, so that the witness sees the file as the guest would first
find it (D's images kept such a hold: F-28). The model's records, and
the handoff's record with its arming and decision words, lie in the
tables' extent, which no profile and no reach includes (F-12; the design
puts the fault queue there, 4.4). The records count only as R5.3 allows
(sm:2423-2430), and, against masters that pass no element, only while
those leave the extent alone (sm:2388); the APLICs write only the files
that the firmware set (F-9). A hart's monitor is a witness where the
test does not treat that hart as breached.

**The control** is the form without the protection (plan:186):
`c-reach` (the reach widened over the targets), `c-hookoff` (the
boundary off), `c-pass` (the configuration page passed through), `dc`
(the stop left out), `Bare`, or a named seed. *From* names the scratch
runs that show the mechanism; none is evidence for a claim. Hart 0 is
the control hart, hart 1 the served VS domain's, and hart 2 the owner's.

### 5.1 The negative cases

| NC | Case | Inv. | Class | Attack; witness; control, or the reason | From |
| --- | --- | --- | --- | --- | --- |
| 1 | A master left out of the platform description, seeded | I29 | tested | Offline: one master removed (the firmware-configuration device; the model). Witness: the independent check refuses it, from `dumpdtb`, `info qtree`, `info mtree -f`, and `query-pci` of the running machine. Control: the description unseeded passes. | R1 |
| 2 | A second holder of a device, seeded | I29; A12 | tested | Offline: a second holder of the function (the firmware; the served VS domain). Witness: the check and A12 refuse it (plan:125). Control: as NC-1. | R1 |
| 3 | A VS domain, a breached hart, and a master of another unit wake a quiesced master through its registers | I29; I36 (b) | tested | After the owner's termination, the served VS domain stores `CC.EN` 1 at BAR0's address (no leaf), and hostile monitors on harts 0 and 1 store it (no PMP entry: F-12); in NC-17's build, `edu` writes it before the starts, and the run ends. Witness: `CC`, `CSTS`, the masks, the disk; M-mode's `pmp_faults`. Control: a leaf for BAR0 in the served VS domain's G-stage root (its store lands); `c-hookoff`; for `edu`, a context whose reach covers BAR0. | R3, R7, `c-hookoff-run1/2` |
| 4 | The same three, through a control | I29; I34 (a) | tested | The same actors write the function's configuration page (`COMMAND`, FLR, `PMCSR`, the MSI-X control) at its ECAM address. Witness: the page through ECAM; M-mode's records. Control: `c-hookoff`; for `edu`, a reach over the page. | `c-run1/2`, `c-hookoff-run1/2` |
| 5 | An owner acts on a device outside its unit through a neighbouring register | I30 (b) | tested | The owner's guest reads and writes every other BDF through its emulated window (00:00.0 among them: F-5), and the pages beside BAR0. Witness: 00:00.0's page and those pages. Control: a build that passes the whole ECAM window through. | `a-run1/2` |
| 6 | The same, through a control request | I30 (b); I34 (b) | tested | No call for a control operation exists (4.7); the owner's only request is a configuration write, here to 00:00.0's `COMMAND`. Witness and control: as NC-5. | `a-run1/2` |
| 7 | The same, through a shared line | I30 (b) | tested | Offline: A11's closure is the function alone, since no other function's pin reaches source 34 (F-46). Run, in `d3x`'s test image, where hart 0 leaves `INTX_DISABLE` clear and MSI-X off and the owner hart's boot code has the function raise `INTx`: identity 255 is pending in hart 2's guest file 1 alone. Witness: that file, by hart 2's monitor's read into its state page; every other hart's `hgeip` and `mip`, unchanged. Control: a platform description with `edu` at a slot whose pin the swizzle gives source 34, which the closure check refuses. In every other image the owner cannot raise `INTx`: its writes of `INTX_DISABLE` and of MSI-X's enable stay in the copy (4.7). | `d-run1/2`, `d3x-run1/2` |
| 8 | The owner makes its device read and write the monitor's memory | I31 (c) | tested | NVMe Write (the device reads) and Read (it writes) commands with a PRP at a canary page of the monitor's. Witness: the canaries; the disk's sink block; the records (causes 21, 23). Control: `c-reach`. | `c-run1/2`, `c-reach-run1/2`, R2, R10 |
| 9 | … M-mode's memory | I31 (c) | tested | The same, at a page of the firmware's text. Witness: the page equals the pinned binary; the sink block zero. Control: `c-reach` widened over it. | — |
| 10 | … another VS domain's memory | I31 (b), (c) | tested | The same, at canary pages of the served VS domain by host address; its GPAs name the owner's own pages (F-32). Witness: its canaries; the sink. Control: `c-reach`. | `c-run1/2`, `c-reach-run1/2` |
| 11 | … a declared page beyond the owner's right | I31 (b) | tested | The reach holds no declared page: the device writes the request page (the owner may only read it), and reads and writes the response page. Witness: both pages; the sink. Control: a reach that maps the request page writable. | R2, R10 |
| 12 | … a register of a device outside its unit | I31 (c), (e) | tested | Read and Write commands at 00:00.0's configuration page. Witness: that page through ECAM. Control: `c-reach` widened over it. | R11 |
| 13 | … a register of its own unit in an extent with another's control, or state of I32 | I31 (c), (e) | tested | The device writes and reads its own configuration page (`COMMAND`, `INTERRUPT_LINE`) and its own BAR0, which its reach does not map. Witness: both. Control: `c-reach` widened over them. | R11 |
| 14 | … the state of I32 | I31 (c); I32 (d) | tested | The device writes and reads the model's page, the directory, its context, the MSI page table, its G-stage tables, the queues, and the handoff's record. Witness: each; `ddtp`. Control: `c-reach` (the debug registers zeroed). | `c-run1/2`, `c-reach-run1/2`, R11 |
| 15 | … an interrupt file that is not its route's (data reads and writes) | I31 (c), (d) | tested | Read and Write commands at hart 1's guest file 1, hart 2's S file, an M-level file, and the route's own GPA (a data write, not an MSI: F-22). Witness: the receivers' `hgeip` and `mip`. Control: `c-reach` widened over the files. | R5 |
| 16 | A request partly outside the reach: nothing outside read or changed | I31 | tested | A PRP list that runs from the reach's last page onto the next. Witness: the inside half lands; the canaries past it unchanged; the records. Control: `c-reach`. | R2 |
| 17 | A request under an identity that has no recorded reach | I31; I30 (a) | tested | A test build with `edu` at 00:03.0 (plan:127) and no context for `0x0018`: hart 0 has it write a canary page before the starts, and the run ends. Witness: the canary; one record naming `0x0018`. Control: a context for `0x0018` whose reach maps the canary. That build starts no VS-domain hart: hart 0's boot code drives `edu` there as the test's attacker, as it seeds NC-34's, NC-44's, and NC-46's states, so it is no configuration whose unit has the monitor as its holder (the plan's stop 3 bounds the design's configuration). | R4 |
| 18 | A request that calls itself already translated | I31's readings | limit | No device model of this build issues one (F-7; plan:131-139). | — |
| 19 | A table in the owner's memory that an element reads for the master, made to lead outside the reach | I31's readings | drop | The model reads tables of its own, which no reach and no profile includes (F-12): no element reads a table in the owner's memory. NC-14 and NC-22 test the tables that it reads. | — |
| 20 | An address beyond the width that an element decodes | I31 | tested | A transfer at 2^41 plus a canary's GPA inside the reach. Witness: the canary unchanged (no truncation); one record. Control: the same at the canary's GPA (it lands). | R2 |
| 21 | A fetch | I31 | limit | Nothing marks a device's fetch (F-7). | — |
| 22 | A VS domain, a device of an assigned unit, and a breached, confined hart change the state of I32 | I32 (c) | tested | The device: NC-14. Hostile monitors on harts 0, 1, and 2 store to the model's page, the tables, and the ECAM page; both guests store at those addresses as GPAs (no leaf). Witness: each target; M-mode's `pmp_faults`. Control: `c-hookoff`, `c-reach`. | `c-run1/2`, `c-hookoff-run1/2` |
| 23 | The same three change a master's identity | I32 (c), (d) | limit | The machine has no bridge, so no register sets an identity (F-31): plan:126's "or has no bridge". The limit names "an identity that a register field sets" (sm:2967). | R4 |
| 24 | The same three move a device's registers | I32 (c), (d) | tested | The owner's guest writes BAR0 (kept in the copy); the served VS domain and hostile monitors write the ECAM page; the device writes its configuration page (NC-13). Witness: BAR0's base through ECAM. Control: `c-pass` (BAR0 moved), `c-hookoff`. | `c-run1/2`, `c-pass-run1/2`, R11 |
| 25 | The same three make a request bypass the element | I32 (c) | tested | `iohgatp` set `Bare`, the one bypass that a write can make, by the device (NC-14), hostile monitors on harts 0 to 2, and the guests' stores; then a transfer outside the reach. Witness: the context; the canaries. Control: `c-hookoff`. The other bypasses need an option, a class, or a function whose model does not use its bus-master space (F-7), each refused by the platform description's check. | `c-hookoff-run1/2` |
| 26 | The same three turn the enforcement off | I32 (c); I32's readings | tested | As NC-25, with `ddtp` set `Bare`. Witness: `ddtp`; the canaries. Control: `c-hookoff`. | `c-run1/2`, R7, R11 |
| 27 | The owner aims its device's MSI at another VS domain's interrupt file | I33 (a); I31 (d) | tested | A vector re-aimed at hart 1's guest file 1, with a receiver; the served VS domain is given no file. Witness: hart 1's `hgeip` 0; one record. Control: `c-reach`. | `c-run1/2`, `c-reach-run1/2`, R5 |
| 28 | … at M-mode's | I33; I31 (d) | tested | A vector aimed at an M-level file. Witness: the model's record; the file is not readable from outside, so that nothing was raised rests on R5.5's first row (sm:2428-2430). Control: `c-reach`. | R5 |
| 29 | … at a controller's port for messages | I33; I31 (d) | tested | A vector aimed at each APLIC's `setipnum_le`. Witness: the APLIC's `setip`. Control: `c-reach` widened over the APLIC's page. | R11 |
| 30 | … at a file of the monitor's: nothing is raised | I33 (a); I31 (d) | tested | A vector aimed at hart 2's S file and at hart 0's, with receivers. Witness: `mip.SEIP` clear; the records. Control: `c-reach`. | `c-run1/2`, `c-reach-run1/2`, R10 |
| 31 | Its device writes every identity to its own delivery point, each attributed to its own unit alone | I33 (d), (e) | tested | The owner's guest holds delivery off and has the function send each identity of its file to the route's GPA; in `d3x`'s form, `INTx` once (identity 255). Witness: hart 2's monitor, not treated as breached, reads the file's pending bits into its state page; no other file's `hgeip`; no hart's trap count changed. Control: an MSI page-table entry that leads to hart 1's file (they arrive there). | `a-run1/2`, `d3x-run1/2`, R5 |
| 32 | Under a flood of the unit's interrupts, the other harts' work is unchanged, and a pause of the owner still takes effect | I33 (b), (f) | tested | The function sends messages without pause; the served VS domain runs a fixed workload and pauses the owner mid-flood. Witness: its counters and hart 0's records against a run without the flood; the pause served (`DOMAIN_PAUSED`; `CC`, `CSTS` 0). Control: a test image whose route leads to a file that a monitor takes (hart 2's S-level file, with its external interrupt enabled), so that the flood reaches that monitor: its trap count rises with the flood. Counts, not times: the emulator's timing is its own (plan:111). | — |
| 33 | … and of its refused requests | I33 (f) | tested | Refused transfers until the fault queue is full. Witness: `FQOF` and the records; no hart's `mip` or `hgeip` changed (the model's interrupt off: F-26); APLIC sources 36 to 39 not pending; the pause as NC-32. Control: `fqcsr.FIE` 1 with source 36 routed to hart 0. | R3 |
| 34 | No interrupt of an earlier holder arrives | I33; I35 (b) | tested | Hart 0's boot code makes an identity pending in hart 2's guest file 1 before the handoff. Witness: the handoff's record (every word 0 after the clear) and the hold's read-back before the first guest entry. Control: the handoff without the clear (the identity reaches the guest). | `d-run1/2`, `b2-run1/2`, R13 |
| 35 | An owner asks for a control operation on another unit | I34 (b) | tested | Through NC-6: no call exists (4.7), and a configuration write to another function's controls is the owner's only request. Witness and control: as NC-6. | `a-run1/2` |
| 36 | … for one that it has no grant for | I34 (b) | tested | The owner, which has no grant, writes its function's FLR, D3hot (plan:124), `BME` 0, and MSI-X enable through its window. Witness: the page through ECAM; `PMCSR` D0; BAR0 decoded; the controller running. Control: `c-pass`. | `a-run1/2`, `c-run1/2`, `c-pass-run1/2`, R8 |
| 37 | … for an access beyond its grant | I34 (b) | tested | No access is made for the owner (4.7); it writes outside the copy's mask and to other BDFs. Witness: the function's page equals hart 0's values. Control: `c-pass`. | `a-run1/2` |
| 38 | Through an access, a change to a control | I34 (b) | tested | The owner writes `COMMAND` 0, the MSI-X control, `INTX_DISABLE` clear, and `PMCSR` D3hot. Witness: `COMMAND` `0x0406` and the MSI-X control `0x8040`. Control: `c-pass`. | `a-run1/2`, `c-run1/2`, `c-pass-run1/2` |
| 39 | … or to state of I32 | I34 (b) | tested | The owner writes BAR0's base. Witness: BAR0 through ECAM, unchanged. Control: `c-pass` (BAR0 at `0x5000_0004`). | `c-run1/2`, `c-pass-run1/2` |
| 40 | From its own hart it reads and writes a register that I34 (a) keeps from it | I34 (a) | tested | The owner's guest loads and stores at the ECAM page's, the model's page's, and the tables' addresses as GPAs (the page emulated, the others with no leaf). Witness: each. Control: `c-pass` for the page; a leaf for the model's page. | `c-run1/2` |
| 41 | After a reset that an owner asked for, the state of I32 is in force before any request | I34 (b) | drop | The design grants no reset (no `reset` permission, R5.6): the owner's FLR writes stay in the copy (NC-36), and its `CC.EN` changes no state of I32 (F-35). | — |
| 42 | An owner with the read right on a declared page cannot make what its writer stored be lost | I34 (c) | limit | QEMU models no cache (plan:123). | — |
| 43 | No owner's invalidate brings back what the monitor cleared | I34 (c) | limit | As NC-42. | — |
| 44 | The boot chain leaves the device active, with a request queued: nothing reaches the owner, and no request lands before confinement | I35 (a), (b), (c) | tested | Seeded, in a build whose guests leave the function alone: before its FLR, hart 0, with the context briefly valid, enables the controller, holds event requests, and queues behind them an Identify into a canary page of the owner's window and a Format; after the run an event is raised from outside. Witness: the canary page, the disk, `hgeip`. Control: the FLR left out (they land, as in `b2c`). | `b2-run1/2`, `b2c-run1/2`, R9 |
| 45 | … with an interrupt pending | I35 (b) | tested | As NC-34, with identity 255 pending in the file and source 34 at the APLIC before the handoff (the APLIC takes a pending bit for a level-high source only while its line is high, so the seed raises the function's `INTx`). Witness: the handoff's record and the hold's read-back (255 not pending); `setip`. Control: the handoff without its clears (255 still pending). | `d-run1/2`, R13 |
| 46 | … with data in it | I35 (b) | tested | Seeded: before its FLR, hart 0 enables MSI-X, writes a pattern into its table, and creates an I/O queue pair; FLR clears `COMMAND`, the power state, the BARs, MSI and MSI-X, and frees the queues (F-34). Witness: the handoff's record of the MSI-X control and table, `CC`, and `CSTS`, read back after the FLR. Control: no FLR (the seed is read back). The namespace is persistent state (I37 (a); NC-55). | R9 |
| 47 | A confinement that cannot be installed, seeded: the unit stays quiesced, and no VS domain starts | I35 (e) | tested | `d-armfail`: the owner's read-back seeded to fail at step 4. Witness: `ddtp` 0, `tc` 0, `COMMAND` `0x402`, `CC` 0; both blocks' `entered` 0, both rings empty, hart 1 in the firmware's wait loop; `BE_MVP:FAIL boot`. Control: `d` (both VS domains entered). Seeds at hart 0's steps (a refused `ddtp`, a fence that never completes) likewise. And a seeded slow arming, which ends after hart 0's bound: hart 0's decision word reads *abandoned*; `COMMAND` `0x402` (bus mastering off); both blocks' `entered` 0; `BE_MVP:FAIL boot`. Its control: the owner's wait for the decision left out, with hart 0's shutdown held back in that image, so that the owner turns bus mastering on and enters its guest (`COMMAND` `0x406`; its block's `entered` set). | `d-armfail-run1/2`, `d-run1/2`, R7 |
| 48 | For a master that is not coherent with the harts, what was cleared is not read back | I35 (d) | limit | QEMU models no cache (plan:123). | — |
| 49 | A request queued before a termination does not land after it | I36 (b) | tested | Commands held behind event requests, the termination, the stop before the serve, an event raised from outside. Witness: the disk, the window, the canary page, `hgeip`, the controller; `TERMINATED` after `CSTS.RDY` 0. Control: `dc` (they land). | `d-run1/2`, `dc-run1/2`, `b2-run1/2`, `b2c-run1/2` |
| 50 | … or before a restart | I36 (c) | not M15's | No restart (plan:122; Q8). | — |
| 51 | A system reset in the middle of a handoff: the next boot's handoff does I35's steps in order | I36 (d) | limit | Every run uses `-no-reboot`, so no system reset executes (F-51; sm:2959; plan:128). Each boot's handoff reads `ddtp` `Off` first (F-17). | R9 |
| 52 | … or of a restart | I36 (c), (d) | not M15's | No restart. | — |
| 53 | A system reset with an interrupt pending: no interrupt of the run before reaches a VS domain | I36 (d) | limit | As NC-51. Interrupt state survives a reset here (F-52), so each boot's handoff clears the owner's file and source 34's pending bit, tested within a boot (NC-34, NC-45). | R13 |
| 54 | … or a route installed | I36 (d) | limit | As NC-51. The tables are in RAM, which a reset keeps; the model resets to `Off` (F-17), and the APLIC keeps its route (F-52). | R9, R13 |
| 55 | An owner rewrites its persistent state: every boot source is unchanged while that boot runs | I37 (b) | tested | The owner's guest writes every block of its namespace. Witness: the SHA-256 of the boot sources (the firmware binary, the boot image, the tree: files outside the machine) before and after; their copies in RAM are NC-8's and NC-9's. Control: none: no option makes the namespace a boot source (F-10). | `a-run1/2` |
| 56 | … and the values that the launch gate compares (I20) | I37 | tested | As NC-55. Witness: the launch gate's expected values in the monitor's image and the log page equal their references, and the log's lines the reference. Control: as NC-55. | — |
| 57 | After a system reset mid-transfer, nothing read or changed before boot code quiesces the unit | I37 (c) | limit | No system reset executes (NC-51); the order of the controller's and the model's resets was not read (F-53). | R9 |
| 58 | … with a master that issues requests from the reset on | I37 (c) | limit | As NC-57; the function issues no request while `CC.EN` is 0 (F-37). | R9 |
| 59 | A hostile-monitor image on the owner's hart drives the unit toward memory outside that hart's profile | I38 | tested | A hostile monitor on hart 2 drives the function from BAR0: transfers at the served VS domain's memory, the monitor's, the tables, and the model's page; messages at other files; the hook's four stores (F-13). Witness: the canaries, the records, `ddtp`, `hgeip` and `mip`, M-mode's records. Control: `c-hookoff`, `c-reach`. | `c-run1/2`, `c-hookoff-run1/2`, `c-reach-run1/2` |
| 60 | … also once its owner is paused | I38; I36 (b)'s reading | tested | As NC-59, after the owner is paused and the stop is done; the image enables the controller again, as Revision 4's attacker may "also while the owner is paused" (sm:2527-2529). Witness and control: as NC-59. | — |

### 5.2 Tests that no row covers

1. **The handoff's order** (R5.3's row for I35; M15-R8). An offline
   check reads the record and requires I35's order (quiesced, cleared,
   confined and routed, exposed), each state once, as R5.8 has it ("in
   that order, once"), the start order, and that hart 0 wrote its
   decision word only after the arming word read armed. Control: two
   steps swapped, which it refuses. From: `d-run1/2`.
2. **The platform description, the closure, and the boot sources**
   (R5.3's rows for I29, I30, and I37). Offline: the description passes
   the independent check; A11's closure is the function alone (no
   other pin on source 34); the boot chain's configuration names no
   unit (F-10). Controls: NC-1, NC-2, and NC-7's.
3. **Requests inside the reach succeed** (R5.3's row for I31): the
   service's writes and reads (the disk's block, read from the image
   file), and a transfer into each 2 MiB leaf of the reach. From:
   `a-run1/2`.
4. **The state in force** (R5.3's row for I32): the read-back of the
   reach and the route, with the tables' extent and the model's
   registers read outside, compared offline with the sealed records by
   a check independent of the generator. Control: a seeded difference
   (a leaf, `msi_addr_pattern`).
5. **Delivery to the owner alone, and the tick under a flood** (R5.3's
   row for I33, and I33 (c); M15-R6): each vector, and `INTx`, pending
   in hart 2's guest file 1 alone, with no other hart's trap count
   changed; under NC-32's flood, the pause served. From: `a-run1/2`,
   `d3x-run1/2`.
6. **The stop at pause, shutdown, and failure** (R5.3's row for I36;
   M15-R9): NC-49's flow with a pause, a shutdown, and a seeded failure
   of the owner; and the failed stop: `BE_MVP:FAIL controls`, hart 0's
   DETAIL naming the stop (a branch that the design adds), no
   `DOMAIN_TERMINATED`, no answer. Control: `dc`. From:
   `d-fail-run1/2`.
7. **A buffer rewritten during a call** (M15-R17). The accepted images'
   one path that reads the window while the device can act is DBCN
   write's buffer, copied once (`mvp/src/mvp-hartmain.c:315-329`);
   placement and measurement precede exposure, and the configuration and
   file exits decode from `htinst` (F-40). The device rewrites the
   buffer during a DBCN write. Witness: the console capture holds no raw
   control byte and no forged line; the test passes only once the
   capture holds a line that mixes the two patterns, which shows a write
   during a copy. Control: a test image whose `console_write`
   (`mvp-hartmain.c`, which M8 does not pin), under a test define,
   passes the window itself to a test-only feed that checks one load of
   each byte and stores another, waiting between the two loads for
   longer than the device takes to rewrite the buffer, and posts its own
   lines through `be_mvp_ring_post()` (`mvp-ring.c`, which it calls and
   does not change) and publishes them through `mvp-hartmain.c`'s own
   `publish()` (a `fence w, w`, then `be_mvp_ring_publish()`), so that
   `mvp-sbi.c` stays byte for byte: a line with a raw byte then reaches
   hart 0, which refuses it (`line_printable`, `mvp/src/mvp-hart.c:756`)
   and fails the run. The control counts only when its run ends so.
8. **The service attacks the VS domain that it serves** (M15-R12): by
   its own accesses, through its device (NC-10), through the declared
   pages (writes to the request page; malformed and oversized
   responses), and by withholding service. Witness: the canaries of
   the served VS domain, unchanged; it runs on to its end, by hart 0's
   console. Control: `c-reach` for the device; the accepted denial
   path's own controls for the rest.
9. **The interrupt file's page** (4.6; F-50). The owner's guest stores
   an identity to its file's `seteipnum`: the identity is pending in
   that file alone, by hart 2's monitor's read into its state page. Its
   kernel loads from the page: the VS domain ends
   (`guest-page-fault`). A program of its loads from the page: the
   accepted denial path refuses it, with a DENIAL record and an access
   fault injected, and the VS domain runs on. Each outcome is the
   others' control.

R5.3's row for I34 asks nothing more of `io-service`: no control
operation and no access is made for the owner (4.7).

### 5.3 Counts

- Tested: 45 (NC-1 to NC-17, NC-20, NC-22, NC-24 to NC-40, NC-44 to
  NC-47, NC-49, NC-55, NC-56, NC-59, NC-60).
- Limit: 11 (NC-18, NC-21, NC-23, NC-42, NC-43, NC-48, NC-51, NC-53,
  NC-54, NC-57, NC-58).
- Not M15's: 2 (NC-50, NC-52).
- Drop: 2 (NC-19, NC-41), for the sign-off (stop 5).

## 6. The proof-impact review

The plan asks for this review before any accepted proof is re-run, and
for it to take up K8: "With a master, an owner's private memory can
change while its hart runs the monitor's code" (plan:159; M15-R15,
plan:188). Stop 8 is a broken premise or a changed verdict
(plan:411-413). As M11's was, it was made by reading alone: the public
line at `4e0daa11`, this page, and the prototypes A to D. `sm:` is
`planning/security-model-v1.md`, `spec:`
`planning/mvp-m8-specifications.md`, `PROTO.md:` the characterization's
report, `proto-d.diff:` D's diff (both scratch, outside the project's
repositories).

**Result.** Under 6.5's conditions the design breaks no premise of an
accepted proof: every proof rests on no master writing the monitor's
words, which no reach includes (6.3). D shows conditions 1, 2, 7, and
10, and 4 but for the decision word, and what a run can of 3, 5, 6, and
9. Three points go to the sign-off: stage 1 is not asserted of
`io-service`'s images (the limit, 4.17); the handoff's record is a kind
of shared word that I16 does not describe (section 8, item 5); and the
stop reads through a copy of the reader's view (section 8, item 4). The
shared guest Image changes `be_mvp_runtime_main` in every image (6.6).

### 6.1 The accepted proofs and records

| # | What it is, and its last result | What it rests on |
| --- | --- | --- |
| P-1 | M8's Leaf A, `be_mvp_denial_decide` and four helpers (`mvp-sbi.c:204-327`), against spec section 4 as Revision 1 (`93a8d136`): WP OPEN 130 of 134; CN OPEN 5 of 55; CBMC 336 properties, a bounded check (`mvp/results/20261118-verify-m11-candidate/verify.txt`) | The pins of `mvp/verify/target-digests.txt:12-42` (`defines=none`); inputs "read through a `const` pointer" (spec:237-238); results "functions of the four inputs' values alone" (spec:323-324); WP's literal "mvp-sbi.c line 321" (`mvp/verify/tools/wp-arm.py:775`) |
| P-2 | M8's Leaf B, CBMC on `mvp-ring.c`'s 14 functions: OPEN, 13,547 of 14,931 properties | The same pins; "One writer view and one reader view per ring" (spec:357-358) |
| P-3 | Stage 1: 26 theorems, 100 readings by symbol, `ConcreteLayout.v` generated from `mvp-layout.h` | Sequentially consistent traces over the words `W` (spec:70-73); L1 to L5; each reading's meaning, which the gate does not check; the layout's SHA-256 (`model/tests/check-concrete-readings.sh:8-9`) |
| P-4 | The litmus record: 55 symbols of the `two-guests` monitors; five tests, `never=5` | The programs without debug sections; `--write` only where `INPUTS` hold (`mvp/verify/tools/litmus.py:89-92`); the scan of te-poc's and anchor's sites (`:119-124`) |
| P-5 | `Policy.v`, `Binding.v`, `PolicyClaims.v`: M3's 22 theorems; the differential, four instances and 91 mutations | Instances from te-poc and anchor (`model/tools/gen-policy-fixtures.mjs:54-65`), exactly four (`model/tests/differential.sh:59`); `policy-check.py`'s details (`model/tests/check-reports.mjs:270-273`) |
| P-6 | Model 0.2: 24 theorems | `model/` alone; no master |
| P-7 | M7's input-ring proof, `model/proof/InputRing.v`: four theorems, each with a closed assumption report (`InputRingAssumptions.v`, `model/tests/run-input-ring.sh`) | "an input step writes domain memory only on that domain's own hart" (`InputRing.v:128-129`); the policy and the binding of P-5 |
| R0 to R7 | Records of the single-hart runtime's images (not the characterization's runs), which M15 neither builds nor changes | Their own sources, under `include/be/`, `virt/be/`, `arch/riscv/be/`, and `tests/r0` to `tests/r7`, which M15 does not change; the MVP's port of six of those headers is pinned in `mvp/verify/target-digests.txt:14-19` |

### 6.2 What the design changes that they read

| Change | Where (monitor code under `io-service`'s define) | What reads it |
| --- | --- | --- |
| The owner's dispatch: the configuration exit and the file page's store, before `be_mvp_handle_exit` (4.6, 4.7) | `be_mvp_dispatch` (`mvp-hartmain.c:549-610`; proto-d.diff:337-347) | `exit_decide`, "be_mvp_handle_exit with the dispatch" (`Concrete.v:1579`): condition 3 |
| The route's controls, after `be_mvp_controls_valid` and on resume (4.6) | After `mvp-hartmain.c:700`; `mvp-trap.S:888-916` | No proof (stage 1 models no trap assembly: the claim ledger's U-18); the image checker's CSR lists |
| The new extents; BAR0's leaves in the owner's G-stage root (4.7; section 8, item 3) | `io-service`'s layout header; `mvp-gstage.c`'s builder and walker, under the define | No proof reads them; `mvp-gstage.h` and `mvp-layout.h`, which M8 pins, stay: conditions 1, 2, 10 |
| Hart 0's installation, before `publish_blocks()` (4.4) | `mvp-runtime.c:3186-3188` (proto-d.diff:1490-1507) | "be_mvp_runtime_main's order is unchanged (the placement, the log, the fence, publish_blocks)" (`Concrete.v:37-38`); I15, I16: condition 4 |
| The owner's handoff, at an entry of its own; hart 0's start order, its poll, and its decision word (4.8) | The boot text; `start_harts()` (proto-d.diff:1367-1423) | Stage 1's start steps (`Concrete.v:1998-2006`); C7: conditions 3, 4, 9 |
| The unit's stop before the serve (4.9) | `tick`, `wait_serve` (proto-d.diff:293, :280) | Leaf B's premise: condition 7 |
| The scenario, its generators, the policy checker (4.13, 4.21) | `mvp/scenarios`, `mvp/tools` | P-4's `INPUTS`; P-5: condition 8 |
| One guest Image with the device's options (4.3) | `mvp/guest` | `be_mvp_runtime_main` in every image (PROTO.md:1043-1057): 6.6 |

### 6.3 K8, and "a fact that a master ends"

"Until a VS domain owns a unit with a master, nothing but its own hart
writes its private memory, so that memory does not change while that
hart runs the monitor's code. A master of the unit can write it then."
(sm:3044-3047). I8, I16, and I19 each need I31 (c) (sm:3034-3036).

- **P-1, P-2, P-4: no.** Their inputs are monitor memory, kept by
  condition 5: the hart's block, whose saved page the vector fills from
  CSRs and registers (`mvp-trap.S:633-803`), its published page, the
  rings, and the barrier's words.
- **P-3: one premise, and one meaning.** Each read sees "the most recent
  write to its word in the trace" (spec:73): no master writes `W`. Of
  it, `WGuest d` alone is a VS domain's memory (`Concrete.v:385`), which
  `gate_verdict` reads (`:1701-1702`): the bytes entered are the bytes
  measured only under condition 6. Any other value from a VS domain is
  "a step's argument" (`Concrete.v:66`).
- **P-5, P-6: no.** Neither reads a VS domain's memory: P-5 reads
  policies and their instances, and P-6 `model/` alone.
- **P-7: no.** "an input step writes domain memory only on that domain's
  own hart" (`InputRing.v:128-129`): a master's write is no input step,
  and "A master's write counts as its owner's" (sm:3009). **I9** names
  no theorem (sm:163): it asks for M15-R17's list.

### 6.4 M15-R17: the monitor's reads of memory that a master can write

The function can write its owner's window at any time (4.5), and a named
master any VS domain's memory that it reaches (sm:3047-3049).

| Read | Path | What it reads | Once; checked before use |
| --- | --- | --- | --- |
| 1 | DBCN write | `sbi_dbcn` checks the extent in the window, at most 256 bytes (`mvp-sbi.c:469`, `:474-475`); `console_write` copies each byte by one volatile load (`mvp-hartmain.c:319-327`); the feed checks and uses the copy (`mvp-sbi.c:1055`, `:1073`) | Yes; hart 0 checks each line again (`mvp-hart.c:754-757`) |
| 3 | Hart 0's launch measurement | One pass over each window's Image and tree, before every start (`mvp-runtime.c:1774-1787`, `:1881`) | Yes; the bytes hold by condition 6 |
| 4 | The configuration exit (4.7) | The saved `htinst` (`mvp-trap.S:787-788`) and register; any other form goes to `be_mvp_handle_exit` | No guest memory; checked first |
| 5 | The interrupt file's page (4.6) | A 4-byte VS-mode `sw` to `seteipnum` or `seteipnum_be` alone, from `htinst` and the register, identities 1 to 255 (proto-d.diff:915-960); any other access goes to `be_mvp_handle_exit` unchanged (PROTO.md:1120-1132) | No guest memory; checked first |
| 6 | The copy and the owner's state | Its hart-written mailbox, outside every reach (I31 (c), sm:2340) | No master writes it |
| 7 | The installation and the arming | The function's identity, BAR0, and MSI-X table against the records (4.13); the owner's read-backs; the arming word, one load per poll on hart 0, and the decision word, one per poll on the owner's hart, before its activation | Each compared with a derived value, read at the offset that the platform description records; no pointer read is followed (4.13) |
| 8 | The unit's stop (4.9) | `CSTS`, `CC`, and the vector controls, under a bound | `CSTS.RDY` alone decides |

Read 2, the DBCN read, reads no guest byte (`mvp-input.c:356`); other
calls and exits read registers and the saved page (`mvp-trap.S:24`); the
breach hook's `hlv.d` is test code (`mvp-breach-arch.S:12`). Reads 7 and
8 take I9's untrusted inputs, not a VS domain's memory.

**The test** (5.2, item 7) shows something only if a device write
lands during a copy: its witness should count lines that mix the two
patterns, refused bytes as `?` (`mvp-sbi.c:1073`), and it passes only
once it has counted such a line.

### 6.5 Conditions, and what D showed

Each keeps an accepted statement unchanged, or its package stops.

1. **M8's pinned files stay byte for byte**
   (`target-digests.txt:12-42`), the route set after
   `be_mvp_controls_valid` (`mvp-hartmain.c:700`). **D:** all 13 hash to
   their pins, with no `-D` for the two units, and READY keeps its eight
   words (PROTO.md:1013-1034, :1063).
2. **`mvp-layout.h` stays byte for byte**, the extents in `io-service`'s
   own header. **D:** ten static assertions; the readings check passes,
   the layout's hash the base's (PROTO.md:1018-1027, :1040-1042).
3. **Stage 1 is not asserted of `io-service`'s images**: the owner's
   dispatch serves two faults that `ConcreteClaims.v:342-343` would
   fail, and hart 0 starts VS domain 1 first and waits, where the
   model's hart 0 starts VS domain 0 first (`Concrete.v:1998-2006`).
   4.17's limit names the images.
4. **After the barrier hart 0 reads one word of the unit's record, the
   arming word, and writes one, the decision word**, which only the
   owner's boot code reads, before its activation. **D:** the read
   shown, the rest written before the barrier (PROTO.md:1099-1118); the
   decision word is the design's (4.8), which no run has shown. The
   record's words have writers in turn, which I16 (sm:817) does not
   describe: section 8, item 5 names it. C7 passes the poll by judging
   calls alone (PROTO.md:1200-1213), and a rule of `io-service`'s own
   checks its loads and stores (section 8, item 3).
5. **No reach or confined hart's profile includes a word that a proof
   reads** (I31 (c)). The masters that pass no element could write one
   in any image, as before M15, and the limit names them (4.4, 4.17).
   **D:** the file's page in neither the owner's G-stage root nor its
   profile; the S-level APLIC in no profile (PROTO.md:994, :1238-1239).
6. **No request of the function reaches memory from the launch
   measurement until the owner's guest sets `CC.EN`**, so the bytes
   that each VS domain first enters are the bytes measured: the model
   refuses every request from its reset until it is given its state
   (K4, plan:155; F-17), and `ddtp` is read `Off` before the
   measurement (4.8); after the installation, the FLR leaves the
   controller disabled (F-34), and while `CC.EN` is 0 the controller
   issues no request (F-37), which only the owner's guest, after its
   first entry, can change. **D:** measurement, installation, barrier,
   arming, entry, in that order, by the console (PROTO.md:1099-1101),
   and from the FLR on by the record (PROTO.md:1155-1175). D read
   `ddtp` after the measurement; the design reads it before (4.8),
   which no run has shown.
7. **The rings' discipline stands:** no record type, class, or answer
   code; no ring word, and no field of the hart's views, written outside
   `mvp-ring.c`. **D:** shown (PROTO.md:1076-1097). **A reading:** the
   stop reads through a copy of the reader's view
   (proto-d.diff:995-1006), which writes nothing shared, where Leaf B's
   premise has one reader view (spec:357-358): section 8, item 4. 4.9's
   DETAIL, naming the stop, is a branch in `be_mvp_detail_line()`
   (`mvp-runtime.c:839`, which no proof pins), under the define.
8. **The accepted scenarios' inputs stay byte for byte**, and the
   model's differential keeps its four instances (4.21), so neither
   `gen-policy-fixtures.mjs:54-65` nor `differential.sh:59` is edited.
9. **Orders that no premise states are named:** the HSM start before the
   handoff (not modelled, `Concrete.v:62`), the device's fences, and the
   litmus scan over `io-service`'s sites. **D:** the order strict; a
   seeded read-back failure left the context invalid and no other hart
   started (PROTO.md:1153-1196).
10. **Every monitor change is compiled into `io-service`'s monitors
    alone**, under its define (section 8, item 3), so that without the
    define each changed source compiles to the base's text. **D:**
    without the define each source that D changed is the base's text,
    so the accepted images keep every reading (PROTO.md:1035-1039).

**What would be stop 8:** for an accepted image, a changed statement of
the 26 or of a definition that one names; an L1 to L5 test program that
must change; an unnamed edit of an accepted model file; a changed leaf
contract or verdict (a count past a time limit read run by run, as M11).

### 6.6 The points where proofs are re-run

7.2's points stand (`./be model-check` at the ends of M15-3b, 3c, and
3d and at the candidate, its readings read again; `verify` at M15-3d at
a scratch commit; the litmus record again at the candidate). Notes:
- At M15-3d, under conditions 1, 2, 8, and 10 and the base's guest, the
  `two-guests` monitors equal the record's: run `verify` on the records
  as they stand first; a failure there shows a broken condition.
- From M15-3e `be_mvp_runtime_main` differs in every image: `verify`'s
  first suite (`mvp/tools/verifier/verify.sh:204`) fails until the
  candidate's derivation, at a signed commit holding its `INPUTS`,
  `mvp/guest` among them (`litmus.py:89-92`; 7.2): so M15-3e is signed
  first. Stop 8 only if a test must change. The CHERI check is a gate:
  its monitors and guest are unchanged (4.3).

## 7. The build

### 7.1 Work packages (M15-3)

Each package ends with its own exit, and a checkpoint report to the
responsible human that asks for no decision. A package that changes a
file that the claim ledger pins reads that row's claim again, and, in
the commit that changes the file, refreshes the pin with a note or
points the row's evidence at another record, or it stops.

| Package | Delivers | Exit |
| --- | --- | --- |
| M15-3a | The platform description: its format, its generator, its independent check against the running machine | The description of `io-service`'s machine generated and checked; seeded defects refused |
| M15-3b | The policy checker's `device` class, a unit as a subject, A9 to A13, and A1, A3, A5, A6, and A8 with a unit | Instance 4 passes; its ten failing variants and `io-service`'s seeded defects are refused; every accepted scenario's checks and report unchanged |
| M15-3c | `io-service`: its scenario, its policy, its declared pages, its records (the authority report's additions, the log profile's row), the descriptor's entries, the derivation of the state of I32 | The records generated and checked; the descriptor's check passes with nine entries for hart 2 |
| M15-3d | The monitor: hart 0's part of the handoff, the owner hart's part, the route's controls, the configuration copy, the interrupt file's page, the unit's stop, and the failure paths | `io-service` runs to its end under QEMU with the boundary on |
| M15-3e | The guest: the kernel's options, the trees, the service's and the served VS domain's programs | The plain guest builds twice alike; the guest's pins and the kernel's reproducibility record derived again |
| M15-3f | The negative cases, the hostile-monitor images on the owner's hart, the builds that show discrimination, and the oracle's reads (section 5) | Each test passes, each control fails, by the witness |
| M15-3g | The re-proof and the gates (7.2, 7.3) | The proofs' verdicts unchanged at each point |

M15-4, the words and the gates, is the plan's.

### 7.2 The points at which accepted proofs are re-run

The build changes paths that the proofs' records bind: the monitor's
sources (`mvp/src`, though not M8's pinned files or `mvp-layout.h`:
section 6's conditions), the device-tree generator, the scenario
generator, and the policy checker (the litmus record's inputs), and the
guest, whose new Image changes every monitor's launch values. So:

- `./be model-check`, with stage 1's readings gate, runs at the ends of
  M15-3b, M15-3c, and M15-3d, and at the candidate. Its citations of the
  monitor's symbols are read again by hand at each point.
- At the end of M15-3d, `verify` runs with every suite at a scratch
  commit of the range's content, with the records derived in place on
  that commit, before any pin is re-derived (S3-C's stop (i)). A changed
  verdict is stop 8. The target digests and the litmus record are then
  derived again **at the responsible human's signed commit**, never at
  an unsigned one, as a small range of their own.
- At M15-4's candidate, after M15-3e's guest, the litmus record is
  derived again and `verify` runs as one of the gates.

Section 6 lists what may not change at those points.

### 7.3 The gates

The nine that the M11 candidate passed, and what each gains:

- **The tool lock:** nothing. The device path uses the locked QEMU, and
  the harness writes the disk's image file itself; a role that the
  build finds it needs is a stop of its package.
- **`check`:** `io-service`'s runs, on the `k3-like` row with both
  toolchains and on the `k3-like-smepmp` row with GCC, under the
  boundary; its negative cases, their controls, and the tests that no
  row covers (section 5); the platform description's generation and
  independent check; and the policy checker's tests.
- **`evaluate`:** `io-service`'s images join its byte-for-byte
  comparison, as every scenario's do.
- **The U-Boot rehearsal:** its cases are unchanged, and their images
  change with the guest's Image (4.3); `io-service` is not among them,
  since the rehearsal tries the board's boot path, and the board has no
  device path.
- **`kernel-repro`:** the guest's Image is built twice with its new
  fragment, and its record is derived again (M15-3e).
- **`model-check`:** no model file changes. Its differential runs the
  MVP policy checker that M15-3b changes on its four accepted instances,
  whose verdicts stay as they are (section 6, condition 8), and stage
  1's readings gate reads the monitor's symbols again at 7.2's points.
- **The model's evaluator:** the same differential, in its pinned image;
  its evidence records the changed checker's new SHA-256 among its MVP
  inputs.
- **`verify`:** at 7.2's points, with every suite.
- **The CHERI check:** unchanged; the device path is off for its variant
  (4.19), and the plain images that it compares change with the guest's
  Image, as every plain image does.

Beside the nine, the board's own gate (`./mvp/mvp k3-board-gate`, tier
2, with the vendor's published files) runs at the candidate, since the
board's images change with the guest's Image; nothing runs on the
board. M15-4 runs a whole `./mvp/mvp check` on the result's whole
content before it is presented.

### 7.4 Soft limits, by kind of code

Proposed here, and set by the sign-off (the plan's section 11). Counted
as the M11 plan counts: added lines that are neither blank nor comment
alone. The basis is the prototypes' sizes: the monitor's path took about
1,524 such lines over the base across the prototypes A to D, its
instruments and tests among them.

| Kind | Soft limit |
| --- | --- |
| The monitor (`mvp/src`), C and assembly | 2,500 |
| M-mode code | 0: none is added |
| The platform description's generator and its independent check | 2,000 |
| The policy checker's class and analyses | 2,500 |
| The scenario, descriptor, and tree generators | 1,500 |
| The harness: checkers, oracle, tests, negative images, and tools | 8,000 |
| The guest: the programs and the kernel's fragment | 1,200 |

## 8. What the sign-off decides

The sign-off of this page's commit decides each of these by name, for
M15 alone:

1. **The MVP plan's stop condition 3, its last part** ("guest-visible
   interrupt injection beyond each domain's own timer"), for
   `io-service`'s committed code, in three forms, each delivered into
   the owner hart's guest interrupt file 1 and nowhere else (4.6): the
   function's MSI-X messages, by the IOMMU model's MSI page table; its
   `INTx`, by the S-level APLIC in MSI mode, on the route that the boot
   code gives source 34, which `INTX_DISABLE` keeps silent in every
   image but the test images of NC-7 and NC-45; and the identity that
   the owner's guest stores to its file's `seteipnum`, which the owner
   hart's monitor makes pending through `vsiselect` and `vsireg`.
2. **D15, "AIA IMSIC deferred"**: lifted for `io-service`'s I/O service
   VS domain, which uses its guest interrupt file.
3. **S3-C's stop (e)**, for these changes to the monitor and no others,
   each compiled into `io-service`'s monitors alone, under its define:
   - hart 0's part of the handoff, its start order, its wait for the
     owner hart's arming word, and its decision word (4.8);
   - the owner hart's part of the handoff, at an entry of `io-service`'s
     own in the boot text, with its wait for hart 0's decision word;
   - BAR0's leaves in the owner's G-stage root: a second root entry, for
     BAR0's gigabyte, whose level-1 and level-0 pages are the two pages
     that the layout leaves spare in that root's pool. The builder in
     `mvp-gstage.c` writes them, and its walker checks them: exactly
     BAR0's four leaves, read and write with U, A, and D, never execute,
     onto BAR0's recorded extent, and nothing else in those pages. The
     walker's rules for every other root stay as they are. D wrote these
     leaves outside the builder, after the walk, so this path is the
     design's, and no run has shown it;
   - the route's controls (`hstatus.VGEIN`, `hideleg`'s VSEI, and
     `hstateen0`), set and checked after the accepted READY check has
     passed; and the resume tail's checks on the owner's hart
     (`mvp-trap.S`), which then admit `VGEIN` 1, `hideleg`'s VSEI, and
     `hie`'s VSEIE, which the guest's own enable of its external
     interrupt sets, and check `hstateen0`;
   - the configuration copy, and the owner's configuration exit (4.7);
   - the emulation of stores to the interrupt file's page (4.6);
   - the unit's stop, its failure path, and its DETAIL line (4.9);
   - a layout header of `io-service`'s own, for its new extents.

   The lift also covers test code that is compiled into `io-service`'s
   test images alone, each named in section 5: the hostile-monitor hook
   on hart 2 and its table (NC-59, NC-60), as M11's hostile-monitor
   images are; hart 0's seeds before the starts (`edu`'s transfers, a
   pending identity, an active controller with held requests, MSI-X's
   table pattern and a queue pair); the seeded read-back failure and the
   seeded slow arming; the hold, and hart 2's monitor's read of its file
   into its state page; NC-7's `INTx` test image (`d3x`); and the
   controls (`dc`, `c-pass`, the handoff without its clears, the owner's
   wait for the decision left out, the model's interrupt on, the route
   to a monitor's file, and the buffer test's feed that checks one load
   and stores another, in `mvp-hartmain.c`), each a variant of one of
   those images. A control that widens a reach, or gives a guest a leaf,
   changes the derivation's data and the walker's admission in that
   image alone.

   `mvp-sbi.c`, `mvp-ring.c`, and every header that M8's target digests
   pin, `mvp-gstage.h` and `mvp-layout.h` among them, stay byte for
   byte (section 6). The image checker changes for `io-service`'s
   monitors alone: a rule of its own for the owner's entry, which then
   joins the accepted confine entry, whose rule stays; a rule of its own
   that hart 0's poll loads the arming word alone and stores the
   decision word alone, beside C7, which judges the calls on hart 0's
   start path and is unchanged; the resume tail's checks above; the
   CSRs that the path writes (`hstateen0`, `hstatus` for its `VGEIN`
   field, `hideleg`, `vsiselect`, and `vsireg`), where today's rule
   keeps every monitor from `hstateen0`; and the hook's rules for hart
   2's hostile-monitor images, by role, as M11's are. No accepted model
   file is edited.
4. **Readings of accepted texts**, for `io-service` alone:
   - **The M11 plan's D-6, for one extent.** D-6 keeps hart 0 from
     reading what a VS-domain hart can write between its starts and its
     own confinement. The tables' extent is written by the owner's hart
     only before its activation, and by no confined hart after it. So
     hart 0's wait reads nothing that a VS-domain hart can write once
     activated, which is D-6's intent; C7, which checks D-6 by the
     calls, stays as it is, and item 3's rule checks the poll's loads.
   - **M8's Leaf B, for one copy of a view.** Its premise is "One writer
     view and one reader view per ring; the writer writes only the
     buffer and the head, the reader only the tail; a view's own index
     is written only by that view." Before it serves its inbound
     records, the owner's hart reads them once more through a copy of
     its reader's view, so that a PAUSE or TERMINATE stops the unit
     before it is answered (4.9). The copy writes only itself, never an
     index or a record, and the serve then takes the same records
     through the hart's own view. The decision reads the premise as
     met.
   - **I32 (d), for the owner hart's delivery controls.** Its
     `hstatus.VGEIN`, `hideleg`, and `hstateen0` are not state of I32:
     a route ends at its delivery point, where an interrupt "first
     becomes pending in an interrupt file", and those controls act
     after it, on that hart's own guest alone (4.4). So the owner's
     monitor may set them after its confinement (F-44), which rule 17
     and stop 14 would bar for state of I32.
   - **The plan's rule 10, for the guest's programs.** "A file that is
     built into, or loaded by, the guest's kernel is `GPL-2.0-only`" is
     read as code that runs in the kernel, as the management module
     does: the service's and the served VS domain's programs are user
     programs in the initramfs, `GPL-3.0-only` as `mvp-init.c` is
     (4.11).
   - **The plan's rule 4, for the prototypes' own commits.** "in files
     that no repository tracks" and "Nothing of it is committed" are
     read as of the project's repositories: the characterization's
     records and its prototypes are scratch, outside the project's
     repositories, and the prototypes were kept as local commits of a
     scratch clone, made for them and never pushed, so that each step
     could be compared with the one before.
5. **Statements that become untrue of `io-service`**, and stay true of
   every other image:
   - security model v1 Part 2's "None exists in any configuration; the
     classes are added when the first does", and I22 (c)'s "No scenario
     assigns one";
   - the M11 plan's F17, "The monitor touches no device";
   - the M11 plan's F15, "After its first guest entry, a VS-domain
     hart's HS-mode code writes nothing but its own block and its VS
     domain's window": the owner's monitor writes BAR0 at the unit's
     stop (4.9);
   - the M11 plan's D-3, whose `devices` row reads "None.": the
     descriptor lists the unit and BAR0's extent for hart 2, as that
     row's second sentence foresees;
   - the M11 plan's D-6, step 5, "Each started hart begins at a stub
     that does one thing", and "Between a hart's start and its
     `confine`, a VS-domain hart executes the stub alone": the owner's
     hart begins at an entry of `io-service`'s own, which runs its part
     of the handoff, as boot code (I26 (c)), before it joins the stub's
     confine;
   - `mvp/src/mvp-gstage.h`'s "Per root: one level-1 table and at most
     one level-0 page" and "the pool's bytes after the level-0 page are
     spare and stay zero": the owner's G-stage root in `io-service`
     holds a second level-1 page and a second level-0 page, for BAR0, in
     those spare bytes (item 3). The header, which M8 pins, does not
     change;
   - I16's "after the barrier the shared words are of two kinds". The
     handoff's record is a third kind: hart 0 zeroes it and writes its
     own part before the barrier; after the barrier the owner hart's
     boot code writes its part and its arming word, and hart 0 its
     decision word, each before the owner hart's activation; hart 0
     reads the arming word, and that boot code the decision word. Once
     the owner's hart is activated, no hart writes the record, and no
     confined hart's profile includes it. So each word has one writer
     in each phase, which is I16's intent.
6. **Every plain scenario's images change** (4.3), as one Image gains
   the device's options; D16 stands.
7. **The service's protocol takes nothing of the console's contract**
   and only the single-writer discipline of M7's rings (4.11).
8. **The claim's words** (4.17): its limit names the unit's owner under
   I37 (c); the masters that pass no enforcing element, with what they
   can reach; Revision 5's trusted rows on which `io-service` rests;
   what this machine cannot show; and the two drops of item 10.
9. **The soft limits** of 7.4, and this page's own: the plan's 900 lines
   (its section 11), which this page passes (stop 10), are re-set for it
   to 1,500; it has 1,467 lines.
10. **Two of R5.3's negative cases left out by the design's own
    choices** (drops, named for this sign-off under the plan's M15-R13
    and stop 5): a table in the owner's memory that the element reads
    for the master, made to lead outside the reach (the element reads
    only tables of its own, which no reach and no profile includes); and
    the state of I32 in force after a reset that the owner asked for (no
    reset is granted to the owner). Section 5 has the tests that stand
    beside each.

## 9. Questions and defaults

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| D-Q1 | The function's `INTx` | A route of its own, kept silent by `INTX_DISABLE` (4.6) | No route: needs the responsible human's reading of A13 against I30 (b), or an erratum, first |
| D-Q2 | The soft limits | 7.4's | The responsible human's |
| D-Q3 | The scenario's name | `io-service` | The responsible human's |
| D-Q4 | The 19 QEMU defects and oddities that the characterization found (listed in its records; the facts that the design does not rest on, in section 2) | Nothing is sent (the plan's rule 15); they stay in section 2 (F-55 to F-68) and in the characterization's scratch records | A report to QEMU, under S3-D.4's rules, in a session of its own |
| D-Q5 | What follows M15 | Not decided here (the plan's Q15) | Decided now |
