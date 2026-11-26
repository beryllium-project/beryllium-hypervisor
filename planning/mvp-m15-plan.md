<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# MVP 2.0 milestone M15 plan: the first device path, under emulation

This plan bounds milestone M15. In the [MVP plan](mvp-plan.md)'s
ladder it is the third of MVP 2.0's seven steps (S3-C.2, step (3);
S3-D.3): "one static pass-through device path and the I/O service
domain (implementation-plan milestone 5)". Step (1),
[M13](mvp-m13-result.md), found the device facts of one board. Step
(2), [M14](mvp-m14-result.md), wrote the device and DMA object model,
[Revision 5 of the security model](security-model-v1.md#revision-5-2026-11-25-the-device-and-dma-object-model),
and read it against that board and against the emulated machine that
the project's gates run on.

It is written on the responsible human's direction of 2026-11-26,
given once M14's result had been accepted. M15 is the first milestone
in which a VS domain is given a device. It starts under emulation, and
plans nothing on the board. It sends nothing to anyone.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. If that commit is on the
public `main` with the responsible human's `Signed-off-by`, this plan
is accepted as written, with Q1 to Q16 at their defaults, and with the
decision and the readings of section 13. Any other answer needs a
revised commit before the sign-off. The signed commit differs from the
one reviewed only by that line and its committer date; if it must be
rebased first, the internal record says so. The project's internal
records keep both commit IDs and the instruction.

The commit that adds this page changes the text of no accepted
document. Accepting the plan decides one accepted stop by name, for
M15 alone: parts of the MVP plan's stop condition 3 (section 13). It
admits nothing to the exception of the MVP plan's stop condition 1.

## 1. What M15 is

- **The first configuration with a device.** One assignment unit,
  assigned by the sealed configuration to one VS domain for the whole
  of a boot. That VS domain is the I/O service VS domain: it drives
  the unit's devices, and serves one other VS domain through declared
  channels. Revision 5 calls this the static device case (R5.8, U4).
- **Under emulation.** On QEMU's `virt`, the machine that the
  project's gates run on, with an IOMMU model of QEMU's in the path of
  the device's requests. Section 3 says why a device path starts
  there.
- **Not on the board.** By M14's result, on M13's record of the K3
  board "on the record alone I30 (d) leaves no unit with a bus master
  that could be assigned to a VS domain". A device path on the board
  needs facts that the record's rows do not hold, the held results
  apart, and a decision of the responsible human's of its own (Q2, Q3,
  Q15). M11 reached one board in the same order: under emulation
  first, and then by an addendum to its plan. Nothing in this plan
  rests on the results that are held under the M13 plan's rule 10, and
  nothing in it reads differently for what they show.
- **Built against the model.** Revision 5's invariants I29 to I38 bind
  the design. For each of them M15 shows what R5.3 asks; or it says,
  in the limit of whatever it claims, what this machine cannot show,
  and what a decision of the responsible human's left out (M15-R13).
- **Under M11's boundary.** Each hart that the monitor uses is confined
  as in the M11 candidate (rule 17).
- **Static.** No assignment, recorded reach, route, or mapping changes
  while the system runs. M15 has no restart of an owner, no change of
  owner, and no hot-plug: those are step (5)'s. A mapping that changes
  while the system runs needs step (4)'s protocol.
- **Three decisions for the responsible human, in this order:** this
  plan; the design, which is text, before any code is committed; and
  the result.
- **What it is not.** Not a device model for guests in general, not a
  second device, not a driver framework, and not a statement about any
  hardware. Nothing is claimed before the result (section 10).

## 2. Inputs

| Input | As read | Used for |
| --- | --- | --- |
| The [MVP plan](mvp-plan.md) | S3-C.2 and S3-D.3, the ladder; its stop conditions, with those that S3-C.8 and S3-D.8 added; S3-A.1 and S3-E, the board policy, which M15 does not touch | What step (3) is; section 13 |
| The [implementation plan](implementation-plan.md) | Milestone 5, "External I/O service domain"; "I/O and service-domain hypothesis"; "Threat model v0" | What the step delivers, and its gate; M15-R12 |
| [Security model v1](security-model-v1.md), with Revisions 4 and 5 | Revision 4's I22, I27, and I28. R5.1 to R5.10: the classes, I29 to I38 with their clauses and readings, R5.3's obligations, the attackers, the trusted computing base, the notation and Instance 4, the analyses, the records, the triggers, and what Revision 5 leaves to this plan | The requirements; the design's questions |
| [M14's result](mvp-m14-result.md) | Section 3, the board; section 4, the emulated machine; section 5, what this plan inherits | Sections 1, 3, 4, and 6 |
| [M13's result](mvp-m13-result.md) and [record](k3-com260-devices.md) | Section 3 of the result | Only what this plan says of the board (section 3) |
| The [M11 plan](mvp-m11-plan.md) and the boundary's claim page (`mvp/docs/claim-boundary.md`) | The partition descriptor (D-3), the profiles (D-5), the lifecycle (D-6), the firmware's rules (D-2), the evidence under emulation (D-10): the oracle outside the monitor, the hostile-monitor images, and the builds that show that a test discriminates | The form of the build and of its evidence |
| QEMU | Upstream's source at the tag `v10.2.2` (`f8ed8165`), and the distribution's build of that release, which the tool lock pins (`mvp/tools/lock/tool-lock.conf`) | The machine, its IOMMU models, and its PCI functions |
| The RISC-V IOMMU specification and the AIA | At the versions that M13's record names among its inputs | What an IOMMU model is to do |
| The firmware base | OpenSBI at the commit that the firmware's build pins (`mvp/firmware/pins.mk`), with the project's series | What M-mode does, and does not do, with a device |
| The guest's kernel | Upstream Linux at the tag and the commit that the tool lock pins (`MVP_PIN_LINUX_TAG`, `MVP_PIN_LINUX_COMMIT`), built by the MVP's rules; `mvp/guest/pins.txt` pins what is built | The I/O service VS domain's side |

No document of a vendor is an input. The supervisor-domain
specification is not an input: Revision 5 leaves the question of
carrying a device path over to it to MVP 2.0's last step (R5.10).

## 3. Where a device path starts, and why

| Place | What the accepted records give | In M15 |
| --- | --- | --- |
| The K3 board | Read against the model, M13's record establishes enforcing elements for no bus master of the board, the held results apart; that says what the record's rows hold, and not what the hardware can do (M14's result, section 3). M13's result concludes that nothing in steps (2) and (3) "can rest on an IOPMP checking a master's accesses, or on the project being able to program one". And a unit is not assigned to a VS domain "if that description establishes no enforcing elements for a master of it" (I30 (d)) | Not in M15 (Q2, Q3) |
| The emulated machine, as the gates configure it | It "has three kinds of bus master besides the harts (each APLIC, the firmware-configuration device, and in one gate a virtio disk), no enforcing element in the path of any of them, and no device whose holder is the monitor" (M14's result, section 4) | Not as it is |
| The emulated machine, with an IOMMU model added | By its source QEMU offers two RISC-V IOMMU models, each for the requests that a PCI function sends through its bus-master address space, "and not for all of those" (M14's result, sections 4 and 5). It also offers a virtio IOMMU, which M14's result did not read, and which M15 does not use | M15 |

**What emulation gives.** Every fact of the platform can be read from a
source at a pin, and every run can be made again. The model's clauses
can be met and tested one by one, with a witness outside the machine.
M11 was built the same way before its addendum took it to one board.

**What emulation does not give.** Anything about hardware. An
emulator's IOMMU is the emulator's: that it attributes and refuses
requests as the specification says is trusted (R5.5's first row), and
is shown only as far as M15's tests reach. Its timing is its own. And
the machine has no model of an IOPMP (R5.9), so M15 shows nothing of
that kind of enforcing element; M15-R16 keeps the records neutral, so
that a platform with another kind could apply them.

Revision 5 lists "What no instance shows", and says: "A device path's
plan says where it takes R5.3's evidence for each of these" (R5.9).
For M15:

| What no instance shows | Where M15 takes the evidence |
| --- | --- |
| A restart with a unit kept (I36 (c)) | Nowhere: M15 builds no restart (Q8) |
| A master that is not coherent with the harts (I34 (c), I35 (d)) | Nowhere: the emulator models no cache. The limit names it (section 10), and it waits for a platform that has such a master |
| A clock, a power, or a transceiver control of one device | For power, a PCI function's power state, where the chosen function has one (M14's result, section 4): it is a control, which I34 keeps from the owner, and the design tests that. This machine has no clock and no transceiver of one device, and the limit names them |
| A device with two holders | None on this machine. The model bars such a unit (I30 (d)), and the check of the platform description is tested with a second holder seeded (R5.3's row for I29) |
| An identity that a register field sets | On this machine, the bus number behind a bridge alone. The design says whether its machine has a bridge, and tests that identity or has no bridge |
| A device that picks its own identity, as R5.4's second attacker may | No device model that M14's result read does. The design says how it tests R5.3's case of a request under an identity that has no recorded reach: with a second function that has none, or with a function behind a bridge to conventional PCI, which an IOMMU model sees under another identity (M14's result, section 4); or the limit names it |
| A system reset with a master active (I36 (d), I37 (c)) | The gates execute none today. The design says whether a run of M15's executes one (M15-R10); what the result does not show, the limit names |
| The board's "as booted" facts | Not M15's |

One negative case of R5.3 that this machine may not be able to show is
outside that list: "a request that calls itself already translated"
(its row for I31). M14's result did not read such requests. By QEMU's
source at the tag, read for this plan, no device model issues one: the
attribute that would mark it is defined and set nowhere, and the
function that would ask an IOMMU for a translation has no caller
(`include/hw/pci/pci.h`, `hw/pci/pci.c`). The characterization
establishes that, and the case then goes to the limit by name
(M15-R13).

## 4. What is known at the start

Rows K1 to K8 are statements of accepted pages, or of QEMU's source
as M14's result reads it. K9 is two queries of the emulator's own
help. K10, and one statement of section 3, were read in QEMU's source
for this plan. No machine was run for this plan. The design
establishes each fact that it rests on again, first by a run in the
characterization and then by a committed test (rule 3).

| # | Fact | Where |
| --- | --- | --- |
| K1 | No VS domain has a device, and "The monitor touches no device. Its console and its reset go through firmware calls". The partition descriptor's `devices` section holds "None. A device assigned to a role would be listed here with its registers' extent (I22 (c))" | The M11 plan, F17 and D-3 |
| K2 | The guests "see no device, and use the pinned upstream Linux as a test input". "No guest sees an injected interrupt": a guest's only interrupt is its own timer's | The [roadmap](roadmap.md); the MVP plan, "Scope" |
| K3 | Each of the two RISC-V IOMMU models is in the path of a PCI function's bus-master accesses alone. Not in it: the firmware-configuration device, the APLICs' messages, a memory-mapped virtio device, a virtio PCI device's queue and data requests unless its property `iommu_platform` is on, an NVMe controller's transfer "whose address lies in its own controller memory buffer or persistent memory region", a function of the IOMMU's own class, and the model's own requests. A root bus whose host bridge sets `bypass-iommu`, which is off by default, bypasses every IOMMU model | M14's result, section 4; Revision 5, R5.9 |
| K4 | An IOMMU model "leaves reset in `Off`, or in `Bare` by a property, with its queues off. Its mode register can be written back to `Off` or `Bare` from any mode. No lock of its state was found". So what keeps its state from being changed has to be where its registers and its tables lie | M14's result, section 4 |
| K5 | "No model checks who writes an interrupt file", and an IOMMU model redirects a PCI function's message-signalled interrupt only through an MSI page table | Revision 5, R5.9 |
| K6 | In the M11 candidate, under emulation, each of the two harts that run a VS domain is confined before its first guest entry, and the control hart at the end of its boot work, each to a physical access profile that M-mode installs from a partition descriptor built offline. Revision 5 names three candidates for what keeps the state of I32: "state that is locked until a reset; registers and tables that no confined hart's profile allows a write to (I22); and the M-mode firmware, which then takes nothing from HS-mode code (I32)" | The boundary's claim page; Revision 5, R5.5 |
| K7 | For the static device case neither trigger fires. "A design in which an owner changes its device's reach while it runs is not U4" | Revision 5, R5.8, Part 5 |
| K8 | With a master, an owner's private memory can change while its hart runs the monitor's code: "A fact that a master ends". Whether a premise of an accepted proof rests on the old fact is for this plan's proof-impact review | Revision 5, R5.10 |
| K9 | The build of the emulator that the tool lock pins offers both RISC-V IOMMU models, as the device `riscv-iommu-pci` and as the machine option `iommu-sys`, and the PCI functions that M14's result names, `edu`, `nvme`, `virtio-blk-pci`, and `pcie-root-port` among them | The emulator's `-device help` and `-machine virt,help`, queried on 2026-11-26; no machine was started |
| K10 | An IOMMU model keeps two caches: of device contexts, and of translations. It uses a cached device context without reading its directory or its mode register again, and a cached translation without walking its tables again. A write of the mode register changes that register alone. The model's invalidation commands invalidate, each in its own cache, the entries that they name, and its reset empties both. So on this machine a state is in force only once the model has taken up the last change, as R5.3 has it | QEMU's source at the tag: `hw/riscv/riscv-iommu.c` (`riscv_iommu_ctx`, `riscv_iommu_translate`, `riscv_iommu_process_ddtp`, the commands `IODIR.INVAL_DDT` and `IOTINVAL`, and the reset) |

## 5. Requirements

M15-R1 to M15-R17 are what any design of M15 has to meet. Each takes up
clauses of Revision 5, whose R5.3 says what would show each invariant
and names its negative cases. The design "may refine them, and returns
to the responsible human before it drops one" (R5.3). The clauses that
the "From" column names bind in full, and govern wherever a
requirement's words say less.

| # | Requirement | From |
| --- | --- | --- |
| M15-R1 | **One unit, one owner, for a whole boot.** The sealed configuration assigns one assignment unit to one VS domain. The assignment, the extents of the unit's registers, its recorded reach, and its routes do not change while the system runs | I30; I36 (a); R5.8's U4 |
| M15-R2 | **A platform description of the emulated machine.** It is generated offline, has an identity, and is checked against a source that its generator did not use. It lists every device and every bus master, with its holders, its identities, its controls, and what it shares; each enforcing element, with what passes it and what does not; and what is not established. The unit's closure is computed from it offline | I29, I30; R5.1, R5.8 |
| M15-R3 | **Every device and every bus master of the machine is accounted for.** Each device that the platform description lists has one holder, or none, and a device with none is quiesced. Each bus master is one of four things, with its evidence: confined; quiesced, with what keeps it so; one whose holder the trusted computing base names, with what the evidence shows of what it can reach; or one that the limit names as not confined | I29; R5.3 |
| M15-R4 | **Each bus master of the unit is confined.** Every request that it issues, of every kind and under every identity that it can claim, reads or writes only what its recorded reach allows. It writes a message-signalled interrupt only to the delivery point of a route of its own unit, and any other request of its that reaches that delivery point reads nothing and changes nothing (I31 (d)). It reaches a register of its own unit only as I31 (e) allows. The recorded reach allows nothing beyond the mappings of the unit's owner, and nothing of what I31 (c) keeps from every reach: the monitor's memory and M-mode's, a device's registers, the state of I32, and an interrupt file | I31 |
| M15-R5 | **The state that confines them** is derived offline from the sealed configuration and the platform description. It is installed before the unit is exposed. Nothing in deriving or installing it takes an extent, an identity, or a right from a VS domain, from a device, or from HS-mode code on a confined hart after that hart's activation. Nothing that a VS domain, a confined bus master, a quiesced device, or a confined hart can do widens what it allows, or stops its enforcement. The state in force is read back once the enforcing elements have taken up the last change, and compared offline with the sealed configuration and the platform description, by a check that is independent of what derived it; and I31's cases show that the elements apply what was read back | I32; R5.3; R5.5 |
| M15-R6 | **Interrupts.** Each interrupt source of the unit has one route, to a delivery point that the configuration gives the unit's owner, on the hart that the owner is bound to; and no delivery point of one VS domain's is the target of a route of another's unit. An interrupt of the unit arrives at its delivery point or nowhere, whatever the owner writes to its devices and whatever a device does. No other hart takes a trap, or does any work, for it. On the owner's hart it does not keep the monitor from its own tick, nor from what it does on that tick. What the monitor reads at a delivery point that a device can write is untrusted input: it attributes an interrupt to the units that are routed there, and never to a number that a device supplied; and a delivery point at which the monitor takes interrupts has nothing else that the monitor relies on. What an enforcing element signals when it refuses a request goes to the hart that the configuration names for it, at no rate that the unit chooses | I33; A13 |
| M15-R7 | **Controls, and what is done for the owner.** A register that has a control or state of I32 is in no VS domain's mappings and in no confined hart's profile, but where I34 (a) allows it. A control operation, or an access that is made for the owner, is performed by an element of the trusted computing base, only as the sealed configuration grants it, and only on the owner's own unit; from the request it takes only what I34 (b) allows. Where a control operation changes state of I32 on the way, as a reset can, whatever performs it installs that state again before the unit's registers are decoded again, and before any request of the unit's bus masters can read or change anything. A cache-block operation by the owner acts only as I34 (c) allows | I34 |
| M15-R8 | **The first handoff, in I35's order,** shown from the boot code's own record: quiesced; cleared; confined and routed; exposed. Before any VS domain's first guest entry the unit is quiesced, and every bus master that the configuration records as quiesced is so. If the unit cannot be quiesced, no VS domain is entered. If a later step cannot be completed, the unit stays quiesced | I35 |
| M15-R9 | **The unit follows its owner.** Its assignment does not change within the boot. It is quiesced until the owner's first guest entry, and after the owner's pause, termination, shutdown, or failure, in each case by what the design names (section 6, row 9). A pause or a termination is reported as done only once the unit is quiesced. A system reset ends the assignment for that boot, and no interrupt that was raised or left pending before the reset reaches a VS domain | I36 (a), (b), (d) |
| M15-R10 | **The next boot.** The unit is no boot source, by the platform description and by the boot chain's own configuration. The platform description says what the machine's reset leaves each bus master of the unit, and each enforcing element, doing. The design shows that the reset bounds each such bus master, or the limit names the unit's owner | I37 |
| M15-R11 | **The owner's hart.** Its profile includes the unit's registers only as the partition descriptor assigns them. A hostile-monitor image on that hart cannot use the unit to read or change anything outside the hart's profile | I38; I22 (c) |
| M15-R12 | **The service.** The I/O service VS domain is an ordinary VS domain, with no class of its own, and the device's driver runs in it. It serves one other VS domain through declared channels alone, by a protocol of queues and grants whose records the monitor does not interpret. Nothing that the service or its device does reads or changes the other VS domain's private memory. The service may withhold its service. Tests have the I/O service VS domain attack the VS domain that it serves: by its own accesses, through its device, through the declared pages, and by withholding service. The served VS domain's private memory is unchanged, and it runs on, but for the service | The implementation plan: milestone 5, "malicious-service tests" among its deliverables, and the hypothesis's items 2 to 5; Part 1's required containment; R5.6 |
| M15-R13 | **Evidence by a witness outside.** Each negative case of R5.3 is tested, or the design lists it with its reason. One that this machine cannot show goes to the limit by name. One that the design's own choices leave out is a drop, which the design names for its sign-off (stop 5). A test passes only when the forbidden request "reads nothing and changes nothing", by a witness outside the device, its owner, and every hart that the test treats as breached. A hart that merely stops is not a pass, and nor is a device that merely stops. An enforcing element's record is such a witness only under R5.3's conditions. Where it can be built, each test is also run in a form without the protection, to show that it discriminates | R5.3; the M11 plan's D-10 |
| M15-R14 | **The records.** The scenario's format, the manifest, the partition descriptor, and the authority report gain what R5.8 lists for a unit, each with its identity; the configuration identity binds the platform description's. The policy checker gains the `device` class, and a unit as a subject. Before sealing, a tool runs A9 to A13, and A1, A3, A5, A6, and A8 as R5.7 reads them with a unit. Each refuses seeded defects, Instance 4's ten variants among them | R5.6, R5.7, R5.8 |
| M15-R15 | **Proofs, and the CHERI variant.** A proof-impact review comes before any accepted proof is re-run; it takes up K8. Where an interface changes that an accepted specification of M8's covers, a newly accepted specification comes first, with the responsible human as its reviewer of record (the MVP plan's D22). The CHERI check stays a gate, with the device path off for that variant | R5.10; M11-R9; the MVP plan's D12 and S3-C's stop (i) |
| M15-R16 | **Records that name no kind of enforcing element.** The scenario's records and the platform description speak of a unit, a reach, a route, and a grant. A fact of one kind of enforcing element appears only in what derives and installs the state of I32, so that a platform with another kind could apply the records unchanged | Revision 5's neutrality (R5.10); M11-R10 |
| M15-R17 | **The monitor's reads.** Each path of the monitor that reads memory that a bus master can write reads each value once, and checks what it read before it uses it. The design lists those paths, those of the accepted images among them, and a test has the device rewrite a buffer during a call | I9; R5.10, "A fact that a master ends" |

## 6. What the design decides

The design is M15-2's page, `planning/mvp-m15-design.md`. It answers
these, each within the bound that this plan sets.

| # | The design decides | Within |
| --- | --- | --- |
| 1 | The machine: QEMU's options for the device path's runs; which of the two RISC-V IOMMU models; and every device that those options add | M15-R2, M15-R3; rule 5 |
| 2 | The unit: which PCI function, and its closure on this machine | Q5's criteria |
| 3 | The scenario: a new one beside the accepted three, with the I/O service VS domain and the VS domain that it serves on the two harts of the accepted layout. And the guest's kernel: the MVP builds one Image for every scenario, so the design says whether that Image gains the options that the device needs, which changes every scenario's images, or a second Image is built | The MVP plan's D16; the standing parts of stop condition 3 (section 13); rule 7 |
| 4 | Who installs the state of I32, and when: the monitor's boot code, before the activation of the hart that writes it, or an element below HS mode. And what keeps that state from every VS domain, confined bus master, and confined hart: one of K6's candidates | M15-R5; rules 9 and 17; Q9 |
| 5 | The recorded reach: which of the owner's memory. And whether the enforcing element reads tables of its own, or the owner's own G-stage tables, which I31's reading allows only where those tables have nothing that I31 (c) to (e) keep from the master | M15-R4 |
| 6 | Interrupts: the unit's sources, by the platform description; each source's route and its delivery point; how the owner takes the interrupt; and what keeps anything else of the unit's devices from raising one | M15-R6; Q7; section 13, for stop condition 3 and for D15 |
| 7 | Which of the unit's registers the owner's mappings include; which accesses and control operations are made for the owner, and what makes them | M15-R7 |
| 8 | The handoff's steps, with how each failure fails closed | M15-R8 |
| 9 | What the owner's pause, termination, shutdown, and failure do to the unit, and what quiesces it in each case: the unit's own stop, written from the owner's hart; an element below HS mode; or the end of the run | M15-R9; rule 8; Q9 |
| 10 | Reset and the next boot, on this machine | M15-R10 |
| 11 | The service's protocol and its declared pages; what it takes from the rings and the console-read contract that MVP 1.0 has; what the VS domain that it serves relies on, and what it does not; and what of the protocol is the guest's kernel's alone, since step (6), the first VS domain that is not Linux, follows "after the service ABI is demonstrated" (S3-C.2) | M15-R12; section 13 |
| 12 | The evidence for each invariant: the runs, the negative cases with their witness, the builds that show discrimination, and what the oracle reads. And, for each thing that this machine cannot show, the sentence of the limit | M15-R13; R5.3; R5.9 |
| 13 | The records' formats and identities; "which of these checks the monitor's boot code repeats before it seals" (R5.8); and whether the measurement log records the partition descriptor's identity, or the platform description's, within the log's format as it is | M15-R14; section 13, for the log's format and for stop (c) |
| 14 | The triggers, evaluated for the designed configuration | Stop 4 |
| 15 | Every execution context, and every firmware call for each role and phase, that the design adds or changes; and every change to what a guest can call, with the version rule of the MVP plan's D8 | I27, I28; D8 |
| 16 | The accepted decisions that the build changes, each by name | Section 13 |
| 17 | The claim's words: a clause and a limit | Section 10 |
| 18 | The build's work packages and their order; the points at which accepted proofs are re-run; the gates; and the soft limits, by kind of code | Sections 9 and 11 |
| 19 | The CHERI alignment, in one paragraph; and whether the CHERI check's emulator offers an IOMMU model at all | The MVP plan's D12; Q14 |
| 20 | Whether to propose that the first configuration be recorded in the security model as an instance, and with what bound | Q13 |
| 21 | Which elements of Revision 5's inventory M15 lands (R5.8, Part 7): the scenario's format, the partition descriptor's entries, the policy checker with the `device` class and the analyses, the validator and what the boot code validates, the abstract and the executable model, and the fixtures; and how the model's differential check treats the new scenario, by name | Q16; section 13, for stop (e); rule 11 |

**What M14's result hands to this plan.** Its section 5 lists what the
model leaves "to that plan, or to the plan or the step that it names".

| What the plan of step (3) inherits | In M15 |
| --- | --- |
| Whether an IOMMU or an IOPMP confines a master; which device a VS domain is given; who writes the state of I32; how a service speaks to those that it serves | An IOMMU model, since this machine offers no other kind (section 3). The rest is the design's: rows 2, 4, and 11, within Q5, Q6, and Q9 |
| The first configuration that assigns a unit to a VS domain | M15's scenario (row 3; section 13) |
| R5.3's obligations | M15-R13; row 12; stop 5 |
| Where the evidence comes from for what no instance shows | Section 3's table |
| The MVP plan's stop condition 3 | Section 13 |
| Which of A9 to A13 the boot code repeats; whether the log records the descriptor's identity or the platform description's; the authority report's schema | M15-R14; row 13 |
| The proof-impact review | M15-R15; M15-2; stop 8 |
| A unit whose holder is the monitor | Not in M15: no unit is assigned to the monitor (stop 3). An enforcing element whose state the boot code installs, and a bridge or a port whose state it sets, are not such units. Their registers are state of I32 (I32 (d); R5.2, "What does not close a unit"), and an element is a master of I29's third kind, whose holder the trusted computing base names (I29's reading; R5.5) |
| A restart with the unit kept; both triggers, for a restart and for a design in which an owner changes its device's reach while it runs | Not in M15 (Q8; rule 8; stops 3 and 4). The design evaluates both triggers for the static configuration (row 14) |
| A change of a unit's owner, a unit taken back, hot-plug, and who may ask for a restart | Not in M15: step (5)'s |
| A permission for a clock or for power; a type for each master of one unit | Not in M15. No owner asks for a clock or for power: each stays as the configuration set it |
| Whether a device path could be carried over to the supervisor-domain specification | Not in M15: MVP 2.0's last step (section 2) |

## 7. Method and rules

1. **Emulation only.** M15 issues no command to the board, opens no
   session on it, and writes no card. The board policy (S3-A.1, S3-E)
   is not touched.
2. **The model is the authority.** The design meets Revision 5's
   clauses as they are written. A clause that cannot be met, or that
   proves wrong when it is applied, is stop 5; it is not read away.
3. **Facts before design, and tests before claims.** The design lists
   each fact that it rests on, with the kind of evidence behind it:
   a source at a pin, or a run in the characterization. Each is
   established again by a committed test in the build, as the M11
   plan's facts were. No scratch run is evidence for a claim.
4. **The characterization is scratch.** It runs under emulation, in
   files that no repository tracks: the locked QEMU with the options
   that add an IOMMU model and PCI functions; bare-metal payloads; and
   changed copies of the monitor, of the guest, and of the firmware, as
   prototypes. Its prototypes may hold M-mode code, as S3-D.5's
   characterization's did: S3-D's stop (m) excepted "The
   characterization's scratch harnesses, builds, and prototypes, run
   only under emulation". They may also deliver a unit's interrupt to
   its owner, which section 13 decides, for scratch alone. Each run
   that a fact rests on is made twice. Nothing of it is committed. It
   fetches only public sources at their pins.
5. **A statement about the machine is about one version.** Facts of
   QEMU are read from upstream's source at the tag, and checked by a
   run of the build that the tool lock pins. An option or a model that
   this build lacks is stop 11.
6. **The witness rule** is R5.3's (M15-R13). What an owner reports of
   its device, and what a breached hart prints, show nothing.
7. **No more mechanism than the path needs.** One unit, one owner, one
   VS domain served. The design takes the least that lets every
   invariant be shown: no M-mode code unless the design shows the need
   (rule 9), and no change to an accepted scenario's images unless the
   design names it (section 6, row 3).
8. **Static.** No assignment, recorded reach, route, or G-stage
   mapping changes while the system runs. The state of I32 in force
   changes only to quiesce the unit (M15-R9), or on the way of a
   control operation that installs it again (M15-R7), and never to
   widen what it allows. A design that needs more, or a restart, is
   stop 3.
9. **M-mode code.** Any addition to the firmware is written under the
   M11 plan's D-2: by a tool that can be named, afresh from the design,
   with the base's source and the series and nothing else, under the
   firmware's licence, and within a soft limit that the design sets.
   The characterization's prototypes are never a source for it.
   S3-D's stop (n) bars a boundary design "in which M-mode takes a
   physical range, a profile, or a hart from HS-mode code after
   activation, or in which a confined hart can widen its own profile
   by any firmware call". M15 applies it to the device path too, and
   adds: M-mode takes no identity, no reach, and no route from such
   code, and from a request nothing beyond what I34 (b) allows.
10. **Guest code.** A file that is built into, or loaded by, the
    guest's kernel is `GPL-2.0-only`, as the management module is.
11. **Paths that the proofs' records bind.** A change under one of them
    has those records derived again at the points that the design
    names, and `verify` run there (S3-C's stop (i)).
12. **Outside `planning/`, M15-2 changes one file:** the AI-assistance
    disclosure (`mvp/docs/ai-assistance.md`), with one whole
    `./mvp/mvp check` at the commit that changes it. The build's files
    are the design's to list.
13. **Review.** An independent, read-only, automated review reads the
    design's drafts and the result before each is presented. Every line
    of committed code is read before it lands. The disclosure names the
    tools, and says who made what (Q10).
14. **Words.** S3-D.2's terminology rule and Revision 5's terms.
    Nothing of M15's is named by the supervisor-domain specification's
    terms (S3-D's stop (k)), and M15 renames no identifier, image, or
    accepted text (stop (l)).
15. **Nothing is sent.** A defect found in another project's code is
    reported to the responsible human, who decides what to do with it
    (S3-D's stop (o), with S3-D.4's rules for anything bound for
    another project).
16. **The held results** of two of M13's probes stay held (the M13
    plan's rule 10). M15 does not use them, and no text of M15 says
    more of them than M13's public pages do.
17. **Under M11's boundary.** M15's scenario runs with the boundary
    on. Each hart that the monitor uses is confined as in the M11
    candidate: the two that run a VS domain before the first guest
    entry, and the control hart at the end of its boot work. After a
    hart's activation, no HS-mode code on it installs, protects, or
    enforces a device's confinement (I32's reading). A design that
    leaves such a hart unconfined is stop 14. The builds that show that
    a test discriminates are apart (M15-R13).

## 8. Where the work lives

On the public development line: this plan, the design, and the build,
on a working branch `m15`, each range signed off and pushed by the
responsible human. The characterization's files, the drafts, and the
reviews are scratch that no repository tracks. The internal records
hold each decision, with the commit IDs and the instruction.

## 9. Work packages

| WP | Delivers | Exit |
| --- | --- | --- |
| M15-1 | This plan | The plan accepted |
| M15-2 | **The characterization, and the design.** The characterization, under rule 4. Then `planning/mvp-m15-design.md`: the facts, with their evidence; section 6's twenty-one decisions; the evidence table for I29 to I38, with each negative case of R5.3 tested, sent to the limit, or named as a drop; the proof-impact review; the accepted decisions that the build changes, by name; the claim's words; and the build's work packages, gates, and soft limits. With it, the disclosure's section, which covers this plan too | The design accepted, by the sign-off of its commit. That sign-off authorizes M15-3, as the design lists it |
| M15-3 | **The path.** The build, in the work packages that the design lists, within these: the platform description, its generator, and its independent check; the policy checker and the analyses (M15-R14); the scenario and its records; the partition descriptor's entries; the monitor's handoff and lifecycle; the state of I32 and its read-back; the I/O service VS domain's side and the served VS domain's; the negative cases, the hostile-monitor images for the owner's hart, and the builds that show discrimination; the oracle's reads | Each package's exit, as the design states it. A checkpoint report goes to the responsible human after each; none needs a decision |
| M15-4 | **The words and the gates.** The claim's page and the ledger's rows, with the ledger tool's change made before the gates; the guide's section; the disclosure; the glossary's, the hardware roadmap's, and the roadmap's lines; the gates from a clean checkout at one exact candidate commit; the evidence record; the result page | The gates pass at one candidate. M15's result is accepted, by the sign-off of its range |

**The gates** are the nine that the M11 candidate passed: the tool
lock, `check`, `evaluate`, the U-Boot rehearsal, `kernel-repro`,
`model-check`, the model's evaluator, `verify`, and the CHERI check.
The device path's runs join `check`. The design says what each gate
gains, and M15-4 runs a whole `./mvp/mvp check` on the result's whole
content before it is presented.

## 10. What may be said, and when

**Before the result: nothing new.** No page says that a device is
assigned, confined, or supported. MVP 1.0's claim and the boundary's
claim, with their limits, do not change.

**With the result,** M15 may propose a claim of its own, on a page of
its own beside the boundary's, with rows of the claim ledger. The
design fixes its words, so that they are decided before the build. They
are bounded here.

| The claim may say, at most | It may not say |
| --- | --- |
| That, under emulation, in one fixed scenario, with the pinned emulator, firmware, and guest, each tested request of a bus master of the assigned unit outside its recorded reach read nothing and changed nothing, by a named witness outside the machine; and the like for each other invariant that the result shows | Anything of hardware, of the K3, or of a board |
| What was shown of the handoff, of the owner's lifecycle, and of the service, each as "tested", with its method | That a device, a class of devices, or pass-through is supported; or that device memory accesses are protected in general |
| | That the emulator's IOMMU model is correct. It is trusted, and the limit says so |
| | More than was tested: it speaks of each tested request, never of every request |

**The limit names:** each thing that this machine cannot show
(section 3); each negative case of R5.3 that a sign-off of the
responsible human's accepted as a drop (M15-R13); every bus master
that the design accounts for as not confined, with what it can reach
(I29); the unit's owner, if I37 (c) has the limit name it; and the
trusted computing base's new rows (R5.5).

## 11. Soft limits

A limit that is passed is a stop for re-evaluation, never a cut to the
work. Only the responsible human re-sets one.

| What it counts | Soft limit |
| --- | --- |
| The design: lines of `planning/mvp-m15-design.md`, by `git diff --numstat` | 900 |
| A revision of the security model, if one is proposed under Q13 | Set by the decision that admits it |
| The build, by kind of code | Proposed in the design, and set by its sign-off |
| The result page | 450 |

## 12. Stop conditions

Each returns M15 to the responsible human. The MVP plan's stops stand
beside them, as section 13 reads them.

1. A need to change an accepted text. This plan admits none
   (section 13).
2. The characterization finds no device that QEMU offers whose every
   request passes an IOMMU model, or finds that a model does not
   refuse what M15-R4 needs refused.
3. A design that needs a restart; a change of a mapping, a reach, or a
   route while the system runs; a second assigned unit; a unit whose
   holder is the monitor; a third VS domain; a hart beyond the layout;
   or more than one VS domain on a hart.
4. A trigger fires for the designed configuration: the capability
   trigger, or the runtime-check trigger.
5. A requirement of section 5, or a clause of Revision 5, that the
   design would drop or weaken; or a clause that proves wrong when it
   is applied, which needs an erratum or a revision of the model
   first.
6. M-mode code beyond rule 9, the characterization's prototypes
   apart (rule 4); or a design in which M-mode takes a range, a
   profile, a hart, an identity, a reach, or a route from HS-mode code
   after activation, or takes from a request anything beyond what
   I34 (b) allows (S3-D's stop (n)).
7. Any step on the board; any use of the held results.
8. A premise of an accepted proof that the design breaks (the
   proof-impact review), or a verdict that changes at a point where
   proofs are re-run.
9. Anything to send to another project.
10. A soft limit is passed.
11. A change to a tool lock, or a tool, an option, or a model that the
    pinned builds lack.
12. A claim that section 10 does not allow, or a claim text that
    changes before the result.
13. A defect in an accepted image, an accepted record, or the M11
    candidate that the work exposes.
14. A design that leaves a hart that the monitor uses unconfined, or
    that has HS-mode code on a hart install, protect, or enforce a
    device's confinement after that hart's activation (rule 17).

## 13. Accepted rules: one decided by name, and the others read

**Accepting this plan decides parts of the MVP plan's stop condition
3, for M15 alone.** That stop returns to the responsible
human "Any milestone that needs a hart beyond the layout, a domain on
more than one hart or more than one domain on a hart, a hart started or
stopped after the boot barrier, a lock held across guest execution or
an untrusted-domain call, a device, an IOMMU, DMA, or guest-visible
interrupt injection beyond each domain's own timer". M14's plan said
that step (3) "will need them, and its plan names this stop for the
responsible human's decision".

- **Decided here:** M15 may give one VS domain one unit, put an IOMMU
  model in the path of that unit's bus masters, and have them issue
  requests, under emulation, within this plan.
- **Decided here, for the characterization alone:** its prototypes may
  deliver a unit's interrupt to its owner, in scratch, under emulation
  (rule 4).
- **Not decided here:** "guest-visible interrupt injection beyond each
  domain's own timer", for anything that is committed. The design's
  path has a route (Q7; section 6, row 6). The design names that part
  of the stop again, with what delivers the interrupt, and the
  sign-off of the design decides it. Until then nothing that is
  committed delivers a device's interrupt to a VS domain. If that
  sign-off does not decide for the delivery, M15-R6 cannot be met, and
  what is left is Q7's alternative, which needs an erratum of Revision
  5 first.
- **Standing:** every other part of the stop.

The other rules are read, and the text of none is changed. The
responsible human's sign-off of this plan accepts these readings.

| Rule | M15's reading |
| --- | --- |
| The MVP plan's stop condition 1 | This plan's commit changes no accepted text, and its acceptance admits nothing to the stop's exception. M15's later commits change maintained pages and the claim ledger's pins, each for the responsible human's decision with its commit, as in M14. A revision of the security model, if one is wanted (Q13), is admitted to the exception by name only by a later decision of the responsible human's, on a proposal that bounds it |
| The MVP plan's stop condition 4 | The design evaluates both triggers (section 6, row 14). A restart is "dynamic management beyond M2's management calls", and M15 builds none |
| The MVP plan's stop condition 6, on checking machinery that outgrows what a plan justifies | M15 adds a generator of the platform description, an independent check of it, and the analyses. The design sets a soft limit for each kind of code, the tests and the tools among them (section 11). A limit that is passed is stop 10 |
| S3-C's stop (c): "a measured object whose expected value the checker cannot compute from the build's inputs" | It applies, if the design has the log record a further identity (section 6, row 13) |
| S3-C's stop (d), claim text | No claim text changes before the result. The result's claim page is decided by the result's sign-off |
| S3-C's stop (e), the monitor's source and the accepted model files | Not lifted by this plan. The design enumerates the monitor's changes and any edit of a model file, and its sign-off lifts the stop for those and for no others, as the M11 plan's acceptance did for M11 |
| S3-C's stop (i) | Applies as written, at the points that the design names (rule 11) |
| S3-D's stops (k), (l), (m), (n), and (o) | Rules 14, 4, 9, and 15 |
| The board policy (S3-A.1, S3-E), and stops (a), (j), (p), and (q) | Not touched: M15 has no step on the board |
| The M13 plan's rule 10 | It stands (rule 16) |
| Security model v1, Part 2: "None exists in any configuration; the classes are added when the first does"; I22 (c)'s "No scenario assigns one"; and the M11 plan's F17 | M15's scenario is the first configuration with a unit, as R5.2's scope has it: "None exists; the plan of step (3), or a later plan, defines the first". Each sentence stays true of every other image. The design names each of them for its sign-off |
| The implementation plan's milestone 5: "Deliver IOMMU-enforced ownership, one restartable service, a minimal queue/grant protocol, and malicious-service tests", with the gate "prove DMA containment, reset safety, and bounded core parsing" | M15 takes it under emulation, and without the restart, which is step (5)'s (Q8). The enforcing element is an IOMMU model because this machine offers no other kind. The malicious-service tests are M15-R12's and M15-R13's. Its "prove" is read as R5.3's evidence, tests with a witness outside, and not as a proof. Its "reset safety" is I36 (d) and I37 (c), as far as this machine can show them. Its "bounded core parsing" is M15-R12's: the monitor does not interpret the service's records |
| The implementation plan's hypothesis: "The core owns IOMMU domains, interrupts, reset authority, and grant/revoke operations" | As Revision 5 narrowed it (R5.10; I32's reading): against Revision 4's attacker, what installs, protects, and enforces a device's confinement after a hart's activation cannot be HS-mode code on a confined hart (rule 17); nor can what performs a control operation, or an access, for the owner where I34 (a) or I32 keeps its register from the owner (I34 (b); M15-R7). Grants are static records. Of its other items: "Drivers run in Linux or dedicated service domains" is met by the I/O service VS domain; "Service domains are restartable where hardware permits" is not taken up in M15 (Q8) |
| The MVP plan's D2: "Not needed: no domain sees a device, and no Linux runs on the bare board under Beryllium" | Its first reason does not hold of M15's scenario, in which one VS domain sees a device. Its decision stands for M15: the guest stays the pinned upstream Linux, built by the MVP's rules as a test input, with the options that the device needs (section 6, row 3). No development kernel and no board support package is selected. A plan for the board would reopen the question |
| The MVP plan's D8: "the SBI implementation version increases with every change to the guest-visible SBI surface" | It applies. If the design gives the owner a call, for a control operation or for an access that is made for it (I34 (b)), the version increases, and the design names the call (section 6, row 15) |
| The MVP plan's D14: "no global control lock, dynamic mapping protocol, or fine-grained locking" | It stands. M15 is static (rule 8): what confines the unit's bus masters is installed before the unit is exposed, and nothing widens it or maps it anew afterwards. Quiescing the unit after its owner stops may have an element below HS mode make the enforcing element refuse every request of the unit's; that changes the state in force and no record, and it is the design's to choose (section 6, row 9). The serialized mapping and invalidation protocol is step (4)'s, "which dynamic management and the device path both need" (S3-C.2): a device path whose mappings change needs it, and M15's do not change |
| The MVP plan's D15: "AIA IMSIC deferred" | It stands until the design's sign-off. M15's path has a route (Q7). If its delivery point is an interrupt file, the design names this line with stop condition 3's last part, and the sign-off of the design decides both |
| S3-C.2, on the decisions of MVP 1.0 that later rungs inherit: "M7's console-input representation and the DBCN-read contract (2.0's first I/O class builds on them)"; and Q43's default, "a console class is 2.0's first I/O class" | Revision 5 gave the notation its first class for I/O, `device`, for a unit (R5.6), and none for the console, which is no device of a VS domain's or of the monitor's (F17). M15 adds no class: its service is reached through declared pages, which the `memory` and `channel` classes express, as in Instance 3. The console stays monitor mechanism outside the policy, as MVP 1.0 has it; whether it becomes a class is not decided here. The design says what the service's protocol takes from M7's ring and its read contract (section 6, row 11); a design that takes nothing from them names that for its sign-off |
| S3-C.2, on the same: "M9's log format (2.0's attestation covers it; a format change later costs the verifier)" | M15 keeps the log's format. If the design has the log record a further identity, it does so within that format (section 6, row 13); a change of the format is stop 1 |
| S3-C.2, on the same: "M8's relational target for "refinement" (every later C result is stated against it)" | M15 plans no new proof. One that the design adds is stated against that target (M15-R15) |
| The MVP plan's D12: "Each milestone plan states its CHERI alignment in one paragraph; no CHERI mechanism" | M15 uses no CHERI mechanism, and the device path is off for the CHERI variant, whose check stays a gate. A unit's register extent, a bus master's reach, and a route are each a bounded authority that a capability could carry; whether one should is for the CHERI platform line. The design says the same of what it builds |
| S3-C.2: "each step a precondition of the next" | M15 is step (3), under emulation. Whether step (4) waits for a device path on the board is not decided here (Q15) |

## 14. Questions and defaults

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | Names | M15, and M15-1 to M15-4. "M15" is also a row's label in the hostile-monitor tables (`mvp/scenarios/anchor/breach.json`, `breach-control.json`, and `mvp/k3/breach/`) and in their records, none of which names a milestone | The responsible human's |
| Q2 | Where a device path starts | Under emulation (section 3) | On the board first. That needs facts that the rows of M13's record do not hold, and a plan of its own under the board policy; it could use nothing of the held results while they are held. This plan would then be replaced |
| Q3 | The board, afterwards | Not planned here. After M15's result, a plan of its own, when the responsible human directs one | A further characterization on the board beside M15, of what could confine a bus master there under M11's boot chain, under a plan of its own |
| Q4 | How M15 is put to the responsible human | Three sign-offs: this plan, the design, the result. Checkpoint reports between, with no decision asked | The design folded into this plan, which needs the characterization run first; or more points of decision |
| Q5 | The device | Chosen by the design among the PCI functions that QEMU offers, by these criteria, in this order: every request that it can issue passes the IOMMU model, by the source and by a run; its owner can aim its requests at any address, so that M15-R4's cases can be tested; it lets a service be built that another VS domain can use; and it needs the least new code in the monitor and in the guest | The responsible human names one |
| Q6 | What the service offers | Chosen by the design, with the device. A store of blocks is preferred, as the nearest thing to a workload, where its cost is close to that of the least service | The least service that exercises the path, whatever it is |
| Q7 | Interrupts | A route for each interrupt source that the platform description gives the unit, as A13 has it and as Instance 4 has one. How it is delivered is the design's: into an interrupt file that the configuration gives the owner; or taken by the monitor on the owner's hart and made pending for the owner. The sign-off of the design decides it (section 13, for stop condition 3 and for D15) | No route, with a device that is polled. Revision 5 is not of one mind about a source with no route: A13, and R5.1's and R5.3's rows, presume a route for each source; I30 (b), R5.6, and R5.8's Part 5 allow for a source without one. So this alternative needs an erratum of Revision 5 first, as a decision of its own |
| Q8 | A restart of the I/O service VS domain | Not in M15. It is step (5)'s, with both triggers evaluated for it | In M15, which needs stop condition 4's second half decided |
| Q9 | Who installs the state of I32, and what keeps it | Chosen by the design. Installed by the monitor's boot code before the activation of the hart that writes it, or by an element below HS mode: I32 (b)'s first two; rule 17 excludes its third, a hart left unconfined. Kept by one of R5.5's candidates (K6). No M-mode addition unless the design shows the need; with every hart confined, the likeliest needs are the quiescing of the unit after its owner stops, and an access or a control operation that is made for the owner | The responsible human's choice |
| Q10 | Review | An independent, read-only, automated review of the design's drafts and of the result, with its findings and their disposition in the internal records | None |
| Q11 | The soft limits | Section 11's | The responsible human's |
| Q12 | How this plan's decision is recorded | As its status says: the sign-off of the proposing commit, with the record kept internally | A second commit that sets a decision record here |
| Q13 | The first configuration, in the security model | Not recorded there by M15. The claim page, the ledger, and the result are its record. If the design finds that the scenario should stand in the security model as an instance, it proposes that, with what such a revision may add: the configuration as an instance worked by hand, with its analyses; no new invariant; no reading of an accepted sentence. The responsible human then decides whether to admit it to stop condition 1's exception by name | An additive revision planned now, at its own commit in the result's range, which this plan's acceptance would admit to stop condition 1's exception by name, as the M14 plan's acceptance admitted Revision 5 |
| Q14 | The CHERI variant | The device path is off for it, and its check stays a gate | The device path built for it too, under a plan of the CHERI platform line |
| Q15 | What follows M15 | Not decided here. The responsible human says, at M15's result, whether a device path on the board comes before MVP 2.0's step (4) | Decided now |
| Q16 | The abstract model | M15 lands what a configuration with a unit needs before it is sealed: the scenario's and the descriptor's formats; and, in the MVP's tools, the policy checker's `device` class and unit as a subject, with A9 to A13 and with A1, A3, A5, A6, and A8 as R5.7 reads them, as offline checks tested with seeded defects. The abstract model's and the executable model's units (R5.8, Part 7) wait for a plan of their own: the MVP plan lists Model 0.3, the generalized model, among MVP 2.0's contents, apart from its seven steps. M15 edits an accepted model file only where a gate cannot pass without it, and the design then enumerates the edit (section 13, stop (e)) | The abstract and the executable model extended in M15, which makes M15 larger and has the model's proofs run again |

## What acceptance would authorize

- **M15-2, and no more:** the characterization, under emulation, in
  scratch (rule 4), whose prototypes may hold M-mode code and may
  deliver a unit's interrupt to its owner; and the writing of the
  design, with the disclosure's section, as a proposal at its own
  exact commits on the public line.

It would not authorize:

- any committed code, tool, test, or image; any change under `mvp/`
  but the disclosure; any change under `model/`, `bringup/`, or the
  firmware's directory. The build, M15-3, is authorized by the sign-off
  of the design;
- a change to an accepted text, an addition to the exception of the
  MVP plan's stop condition 1, or a claim;
- any step on the board, or any use of the held results;
- anything sent to another project;
- a push: each commit on the public line stays the responsible human's
  to sign off and push.

## Review record

An independent, read-only, automated review read this plan's drafts
before it was presented. Its findings and their disposition are in the
project's internal records.

## Status record

```text
mvp_m15_plan=accepted-if-its-proposing-commit-is-on-the-public-main-with-the-responsible-human's-sign-off;otherwise-proposed
mvp_m15=MVP-2.0-step-3;the-first-device-path;under-emulation;one-unit-one-owner-static
mvp_m15_board=not-in-M15;by-a-decision-of-its-own-of-the-responsible-human's
mvp_m15_decisions=three-in-order;this-plan;the-design;the-result
mvp_m15_work_packages=M15-1-the-plan;M15-2-the-characterization-and-the-design;M15-3-the-path;M15-4-the-words-and-the-gates
mvp_m15_authorizes=M15-2-only;the-build-by-the-sign-off-of-the-design
mvp_m15_requirements=M15-R1-to-M15-R17
mvp_m15_design_decisions=21
mvp_m15_plan_rules=17
mvp_m15_plan_stops=14
mvp_m15_questions=Q1-to-Q16-at-their-defaults
mvp_m15_plan_decides=one-accepted-stop-by-name;parts-of-the-MVP-plan's-stop-condition-3
mvp_m15_plan_reads=22-rows-of-section-13;the-text-of-none-changed;nothing-admitted-to-stop-condition-1's-exception
mvp_m15_stop_condition_3=decided-for-M15-alone;one-unit-an-IOMMU-model-and-DMA-under-emulation;an-interrupt's-delivery-in-the-characterization's-scratch-alone;committed-interrupt-delivery-left-to-the-design's-sign-off
mvp_m15_claim=none-before-the-result
mvp_m15_held_results=not-used;the-M13-plan's-rule-10-stands
mvp_m15_sent=nothing
```
