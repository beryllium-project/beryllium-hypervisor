<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# MVP 2.0 milestone M14 plan: the device and DMA object model

This plan bounds milestone M14. In the [MVP plan](mvp-plan.md)'s
ladder it is the second of MVP 2.0's seven steps (S3-C.2, step (2);
S3-D.3): "the device and DMA object model, with H06's "authority
without a mapping" and H07 answered where devices and the service
domain make them concrete". Step (1), [M13](mvp-m13-result.md), found
the device facts of one board. Step (3), one static pass-through
device path with the I/O service VS domain, builds on this model.

It is written on the responsible human's direction of 2026-11-25,
given once M13's result had been accepted. It writes a model, and
builds nothing. It sends nothing to anyone.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. If that commit is on the
public `main` with the responsible human's `Signed-off-by`, this plan
is accepted as written, with Q1 to Q14 at their defaults, and with the
amendment and the readings of section 11. Any other answer needs a
revised commit before the sign-off. The signed commit differs from the
one reviewed only by that line and its committer date; if it must be
rebased first, the internal record says so. The project's internal
records keep both commit IDs and the instruction.

The commit that adds this page changes the text of no accepted
document. Accepting the plan amends one accepted rule by name, the MVP
plan's stop condition 1, and reads ten others (section 11).

## 1. What M14 is

- **A model, written as text.** It says what a device is to the
  [security model](security-model-v1.md): which objects exist once a
  VS domain is given a device, who has authority over each, which
  invariants any device path has to keep, which attackers a device
  adds, and what joins the trusted computing base. It is an additive
  revision of security model v1, Revision 5.
- **Neutral about the mechanism, and tied to facts.** It says what
  any mechanism has to provide, as Revision 4 did for the physical
  boundary, and chooses none: not an IOMMU, not an IOPMP, and not who
  programs either. It is read against facts before it is proposed:
  M13's record of one board, and the emulated machine that the
  project's gates run on (Q5).
- **It answers two questions that the
  [synthesis](he-to-be-synthesis.md) handed forward.** H06: whether any
  authority exists without a mapping. H07: when a finer type has
  security meaning.
- **It builds nothing.** No code, no tool, no image, no file of the
  abstract model, and no session on the board.
- **It chooses nothing for step (3).** Which device a VS domain gets,
  which mechanism confines that device, who programs the mechanism,
  and how the I/O service VS domain talks to the VS domains that it
  serves are for step (3)'s plan. M14 gives that plan the invariants
  that it has to meet, each with what would show it.
- **It waits for nothing.** M12 runs beside it, as S3-D.3 has it.

What it produces:

| Product | What | Where |
| --- | --- | --- |
| The model | Security model v1 Revision 5: the object classes, the invariants, the threat model's and the trusted computing base's additions, the notation's classes, the analyses, one worked instance, and the answers to H06 and H07 | Appended to `planning/security-model-v1.md`, as its own exact commit (Q2) |
| The result | The model read against M13's record and against the emulated machine: for each bus master and each device, what the model's classes say of it, what a device path would have to show, and what is not established. It binds nothing | A planning page, `planning/mvp-m14-result.md` |
| Three maintained pages kept current | The [glossary](glossary.md)'s rows for the model's terms; the [hardware roadmap](riscv-security-hardware.md)'s lines that name the device path; and the [roadmap](roadmap.md)'s position | Those pages |
| The disclosure | The AI-assistance disclosure's section on M14: who made what | `mvp/docs/ai-assistance.md` |

What it is not: a design of the device path; a choice of a device or
of a mechanism; a proof; a change to the abstract model's files, to an
image, or to a path that the proofs' records bind; hardware
validation; or evidence for any claim.

## 2. Inputs

As read on 2026-11-25. Dates are UTC. M14-1 pins each document that it
reads, and the model names the version that it read.

| Input | Identity |
| --- | --- |
| M13's record and result | `planning/k3-com260-devices.md`, 393 rows, and `planning/mvp-m13-result.md`, section 3, as the public `main` has them at `d6d5492c` |
| The security model | `planning/security-model-v1.md` with Revisions 1 to 4: Part 1's object classes and I1 to I28; Part 2's notation and its three instances; Part 3's analyses; Part 5's triggers; and three places that speak of a device: Part 2's "Device, DMA, IOMMU, or interrupt-injection objects. None exists in any configuration; the classes are added when the first does"; I22 (c), "A device's registers, only where the descriptor assigns that device to the hart's role"; and I28, "Every context is accounted for" |
| The MVP plan and the M11 plan | S3-D.4's requirement M11-R10, by which the partition descriptor "says how interrupts and devices would be assigned". The M11 plan's descriptor (D-3), whose `devices` section is empty and would list an assigned device "with its registers' extent"; and its fact F17, "The monitor touches no device" |
| The boundary's claim | `mvp/docs/claim-boundary.md`: what M11's boundary bounds, and its required limit |
| The synthesis | `planning/he-to-be-synthesis.md`: H06 and H07, with H08, H09, and H57 |
| The implementation plan | Its "Selected static system-description split", its "I/O and service-domain hypothesis", and its milestone 5 |
| The specifications | As M13's record pins them: the RISC-V IOMMU specification, release `20260222`; the Advanced Interrupt Architecture, `1.0`, as its release `20250312` has it; the RISC-V IOPMP specification, `v0.85`, a draft; and the cache-block management chapter of the RISC-V ISA manual, at `3142f66f`. As M12's later steps read it: the RISC-V Supervisor Domains Access Protection specification at its frozen release `v0.9` (`9211c4cf`), for one paragraph on its chapters 6 and 7, which M12's records name for the I/O checker and for the interrupt extension (Q13). The PCI Express specification is not an open document: what the model needs of PCI Express, it takes from M13's record and from upstream Linux's source at the record's pins, `v7.3`, and `v7.4-rc4` where the record cites it |
| The emulated machine | QEMU's `virt` machine in the configuration of the gates' `k3-like` row, `virt,aia=aplic-imsic,aia-guests=7` (`mvp/tests/run-qemu.sh`), whose harts have guest interrupt files as the board's do; and, beside it, the RISC-V IOMMU models and the devices that QEMU offers for that machine, none of which the gates add, or give to a VS domain (Q5). The reading is of upstream QEMU's documentation and source at the tag `v10.2.2`. The tool lock pins Fedora's build of that version, `qemu-10.2.2-1.fc44`, whose patches are not read. Nothing is run |
| Precedents | seL4 and capDL, for device memory, interrupts, and I/O address spaces as objects, which the implementation plan names as the manifest's precedent; and the precedent lessons that the synthesis adopted (H56). Each is read for what it makes an object, and none is copied (Q9) |
| A checklist | An order for giving a device to a new owner, and a list of negative cases, from the project's own analysis notes, which are not public. The model states what it takes from them in its own words (rule 7) |
| This project's rules | The MVP plan's stops and decisions (section 11 names those that M14 amends or reads); the terminology rule (S3-D.2); and the M13 plan's rules 4, 7, 9, and 10 |

## 3. What is known at the start

Each line is a starting point. The model reads it again and cites it.

| Subject | What is known | From |
| --- | --- | --- |
| The security model | It has no device object. Its `interrupt` class has one instance, "the HS supervisor timer interrupt (B7); no injected interrupt", and that authority is "monitor-owned". A profile may include a device's registers only where the descriptor assigns the device to the hart's role, and "No scenario assigns one". Its account of every execution context (I28) leaves out whatever addresses memory without one: R4.3 defers "a device that masters the bus or the debug module, until an inventory shows what they can reach" | Security model v1: Part 1's object classes, I22 (c), I28, R4.3, R4.5 |
| The policy | Four classes: `memory`, `channel`, `domain`, and `manifest`. Of H06, the half on how permissions combine is answered: "unioned across rules, conjunctive across permissions". The half on authority without a mapping is open, and H07 is deferred | Security model v1, Part 2; the synthesis, H06 and H07 |
| The monitor | It touches no device: its console and its reset go through firmware calls. M11's boundary bounds what a hart can reach. It bounds no other bus master | The M11 plan, F17; `mvp/docs/claim-boundary.md` |
| The intended shape | "The core owns IOMMU domains, interrupts, reset authority, and grant/revoke operations"; "Drivers run in Linux or dedicated service domains"; "Device-domain compromise cannot DMA or interrupt outside its grants" | The implementation plan, "I/O and service-domain hypothesis" |
| One board: a device's memory accesses | M13's result: "the record shows no mechanism on this board that bounds the memory accesses of any bus master other than the harts. That says what the record's rows hold, the held results apart; it does not say what the hardware can do." There is an IOMMU, and "neither the boot stages whose sources were read nor the board's Linux uses it"; as booted it is in `Off` mode, and three PCIe ports bypass it. Of the IOPMPs, M13's result says that "nothing in steps (2) and (3) can rest on an IOPMP checking a master's accesses, or on the project being able to program one" | M13's result, section 3 |
| One board: what devices share | Registers of different devices share a 4 KiB page, the G-stage's grain. A device's reset bits and clock gates are in registers of units that it shares: the USB controllers share one register, the storage card controllers share one reset and one clock, and the page that has a device's register has other devices' controls. Devices also share a PHY, a bus, an interrupt source, a power domain, and pins | M13's result, section 3; the record's rows C-14 to C-27 and D-23 to D-37 |
| One board: interrupts | A device's message-signalled interrupt is an ordinary memory write. No row of the record shows anything that stops a device's write to a hart's S-level interrupt file. Harts 0, 1, and 2 each have seven guest interrupt files | M13's result, section 3; the record's rows A-124 to A-127 and B-69 to B-72 |
| One board: who else drives devices | The real-time cores are started at every boot, and M11's limit puts them outside its boundary. Their firmware serves clock, power-domain, and system-reset requests, and it drives the power-management chip on one bus while the board's Linux drives it on another. Whether JTAG is enabled on this board is not established | M13's result, section 3; the record's rows C-30, D-34, and D-71 |
| One board: caches | By the trees that Linux uses, DMA on this SoC is not cache-coherent, but for the eight HDMA instances, which the manual and the vendor's tree make coherent. Under M11's boundary the cache-block operations that Linux's driver path uses trap in a VS domain | M13's result, section 3 |
| One board: its boot media | The MVP's images boot from a partition of the NVMe drive, and M11's board runs booted their firmware from a microSD card. The board's Linux drives the PCIe port that the drive is behind, and the microSD card's controller | The MVP plan, S3-A.1; `mvp/docs/claim-boundary.md`; the record's rows A-87 and A-97 |
| How far the board's facts reach | One board; one boot chain, the resident one. "A step that builds on M11's boundary cannot take an "as booted" row as that chain's state; it has to read the state again under that chain" | M13's result, section 3 |
| The emulated machine | In the project's gates "no domain sees a device", and no run adds an IOMMU. What QEMU offers for the machine is read in M14-1 (Q5) | The MVP plan, D2; `mvp/tests/run-qemu.sh` |

## 4. The questions that the model answers

The model answers each, in the part of the security model that the
question belongs to, or says why it cannot yet.

Three words are used throughout. A device's **holder** is whatever
drives it: a VS domain; the monitor, in a hart's role; the firmware
below the monitor; or an execution context that no configuration of the
project's controls. Its **owner** is a holder that is a VS domain: the
one to which the sealed configuration assigns the device. A device's
**reach** is the set of physical extents, memory and registers alike,
with rights, that its own requests can read or write.

**Objects and ownership.**

1. What a device is, as an object: which of its parts the model names
   (its registers, its interrupt sources, its identity as a bus
   master, and its reset, clock, and power controls), and which of them
   can be assigned separately.
2. What the unit of assignment is. Devices share things (section 3).
   The model defines the **assignment unit**: the smallest set of
   devices that can be assigned to one owner. It is closed over two
   relations: devices whose requests the platform cannot tell apart,
   since they issue them under one identity; and devices that cannot be
   kept apart, since they share a page of registers, a reset, a clock,
   a PHY, or an interrupt source. The model says whether a shared bus,
   power domain, or pin does the same, and what makes a unit one that
   cannot be assigned.
3. Who may be a unit's holder: one VS domain; the monitor, for a hart's
   role; the firmware below it, which drives the console today; an
   execution context that no configuration of the project's controls,
   as the real-time cores' firmware is on the K3; or nobody. What the
   model says of a unit that two holders drive at once, as M13's record
   shows for the power-management chip. And how every device and every
   bus master of a platform is accounted for: I28's rule, carried from
   execution contexts to bus masters.
4. Where the authority is recorded: the records that the manifest
   gains; what the partition descriptor's `devices` and `interrupts`
   sections list; what comes from a description of the platform that is
   built offline, as the implementation plan's "normalized platform
   descriptor" is to be; and which of these the configuration's
   identity, and so the measurement log, covers.

**A device's memory accesses.**

5. What a device's reach may be, relative to its owner: that it has no
   extent, and no right on one, that its owner does not have; and
   whether it may be less, a part of its owner's memory.
6. What no device's reach may include, whoever its owner is: the
   monitor's memory and M-mode's; another VS domain's private memory; a
   declared page beyond its owner's rights; any device's registers; an
   interrupt file, other than by question 10's route; and the state
   that confines the device.
7. What "confined" means for a bus master, in terms that do not depend
   on the mechanism: that the rule is in force before the master can
   issue a request; that it is derived from the sealed configuration
   and can be checked against it; and what can change it afterwards.
   Against Revision 4's attacker, HS-mode code on a confined hart must
   not be able to change it. The model states that as a requirement,
   and names the elements of the trusted computing base that could
   enforce the rule, without choosing one.
8. What the model says of a master that nothing confines, or whose
   confinement is not established: that it stays quiesced; or that its
   holder is an element of the trusted computing base; or that the
   configuration's limit names it. The model defines "quiesced", and
   says what has to keep a master so.
9. H06, authority without a mapping. Which authority over a device
   exists without a G-stage mapping: a device's reach; the delivery of
   its interrupts; its reset, its clocks, and its power; and, for a
   master that is not cache-coherent, the cache-block operations that
   its driver needs, which trap in a VS domain under M11's boundary
   (M13's result). Where each is realized: in state that is derived
   from the sealed configuration; in an operation that the monitor or
   the firmware performs on request; or in a request to another
   execution context. And whether any authority may exist with no
   derived state that enforces it.

**Interrupts.**

10. How a device's interrupt reaches its owner, as authority: the
    source, its route, and the interrupt file that receives it; whether
    a device's interrupt source is an instance of Part 1's `interrupt`
    class, whose one instance today is the monitor's own, or of a new
    class; that a message-signalled interrupt is a memory write by the
    device, so that questions 5 to 7 apply to it; and what may change a
    route.
11. Which interrupts a VS domain that owns a device may receive, and
    from whom.
12. What a device may do to the other VS domains and to the monitor by
    its interrupts alone, by their number and their timing: the allowed
    effects.

**Lifecycle.**

13. The states of an assignment unit, and the order of its first
    handoff: from the boot chain, which has used the device, to its
    owner. The order says when the device is quiesced; when its own
    state, and the buffers that it will reach under its owner, are
    cleared; when its confinement and its interrupt route are
    installed; and when its owner can first touch it. Confinement comes
    before exposure, as I26 has it for a hart. For a master that is not
    cache-coherent, the order also says when what was cleared has
    reached memory.
14. What becomes of a unit when its owner is paused or terminated, or
    fails: whether it is quiesced, and when. It stays assigned to that
    owner: taking it back is question 16's. And what becomes of it at a
    system reset. Which state of a unit survives a system reset: its
    own firmware, its non-volatile memory, and, for a storage device,
    its media. And what an owner can do through that state to the next
    boot. On the K3 the question is concrete, since the board's boot
    media are devices (section 3).
15. The restart of an owner with its unit kept. The implementation
    plan's milestone 5, which S3-C.2 names for step (3), asks for "one
    restartable service" and gates on "reset safety"; S3-C.2 puts
    restart, as a management operation, in step (5). The model states
    what such a restart has to do to the unit (quiesced, reset,
    cleared, and enabled again under the same confinement and route),
    so that either step can build on it. Which step builds a restart is
    for step (3)'s plan to put to the responsible human.
16. What is left to step (5): a unit assigned to another owner, or
    taken back, while the system runs; and hot-plug. The model names
    the states so that those transitions can be added, and lists the
    negative cases that they bring (Q6).

**The threat model and the trusted computing base.**

17. The attackers that a device adds: a VS domain that programs its
    device to reach what the VS domain itself cannot; a device, or its
    firmware, that is hostile or defective, and issues any request
    under any identity that its place on the bus lets it claim; and
    Revision 4's attacker on a hart whose profile includes a device's
    registers. For each, how it reads with the accepted threat model's
    deferred lists (section 11).
18. What containment is required against each, and which effects are
    allowed: among them, what an owner may do through the state of
    question 14.
19. What joins the trusted computing base, and with what evidence
    class: the hardware that confines a master, as a platform
    implements it; the code that programs it; the state that the boot
    chain leaves in a device; and the bus masters, and the holders of
    devices, that no configuration of the project's controls.

**The policy.**

20. The notation's new classes and permissions; and whether a device is
    a subject of the policy (a source type, with rules for what it may
    reach), an object (that is assigned to a VS domain), or both.
21. H07, when a finer type has security meaning: which distinctions
    among an owner's memory, a device's registers, and its interrupt
    sources the policy has to be able to express, because it gives them
    different authority.
22. Which analyses of Part 3 change, and which are new. For example:
    that no rule gives a device more than its owner has; that every
    assignment unit is closed; and that every bus master in the
    platform's description is accounted for.
23. Whether the static device case fires the capability trigger or the
    runtime-check trigger of Part 5. The static device case is a use
    case beside Part 5's U1 to U3: one assignment unit, assigned to one
    VS domain by the sealed configuration, with no change of
    assignment, and no restart, while the system runs. For a restart,
    the plan of the step that builds one evaluates the triggers, as
    S3-C.2 has it for dynamic management.

## 5. Method and rules

1. **Additive.** The model is appended to the security model as a
   revision, as Revisions 1 to 4 are. It quotes the accepted text, and
   edits none of it. It lists every accepted sentence that it reads.
2. **Neutral about the mechanism.** The model's terms are the bus
   master, its identity, its reach, its confinement, and the element
   that enforces that confinement. An IOMMU and an IOPMP appear as what
   a platform may offer, and in the reading of the facts; neither is a
   term of an invariant. Which mechanism a device path uses, and who
   programs it, is for step (3)'s plan.
3. **Every fact has a source.** A statement about the K3 cites a row of
   M13's record, or another accepted record of the board: the
   boundary's claim page, M11's board records, or the MVP plan's
   S3-E.1. A statement about the emulated machine cites the emulator's
   documentation or source (section 2). A statement about what an
   architecture requires cites the specification by section. A
   statement about PCI Express is written as what upstream Linux's
   source does, never as what that specification requires. Nothing in
   the model rests on what M13's record marks "not established".
4. **What is held stays held.** The results of two of M13's probes are
   held under the M13 plan's rule 10. The model does not rest on them,
   says of them only what M13's pages say, and reads the same whatever
   they show.
5. **The model is tried on instances before it is proposed.**
   - A worked instance in the notation: one device that is a bus
     master, signals by one message-signalled interrupt, and has a
     reset of its own; the service VS domain that owns it; one VS
     domain that the service serves; and one declared channel between
     the two. The model says whether the device's reach may include
     that channel. The instance names no device of the board's. The
     analyses are run on it by hand.
   - M13's record: each bus master and each device that it lists,
     whoever drives it, under the model's classes.
   - The emulated machine (Q5): QEMU's `virt` in the configuration
     that section 2 names, with the RISC-V IOMMU models and the devices
     that QEMU offers for it: what the model's classes say of each,
     from the source alone.

   An invariant that no instance can show, and a fact that the model
   cannot express, are reported with the model.
6. **Each invariant comes with what would show it**: the evidence that
   a device path would have to give, and the negative cases that it
   would have to test. For a negative case the rule is M11-R7's,
   carried to a device, in I21's words: the test passes when the
   forbidden request reads nothing and changes nothing, by a witness
   outside the device, its owner, and every hart that the test treats
   as breached. The record of whatever enforces the confinement is such
   a witness when it is kept where no such hart can write it, and is
   read from below HS mode or from outside the machine. What a breached
   hart prints is not (R4.5). A device that merely stops is not a pass.
   These are obligations for step (3)'s plan, which may refine them,
   and returns to the responsible human before it drops one, as S3-D.4
   has it for M11's requirements. M14 writes no test.
7. **The checklist is an input, not a design.** Its order (quiesce the
   device; take the old owner's access away; clear the device's state
   and its buffers; record the new owner; confine the device; route its
   interrupts; and only then enable it; with the reverse order for
   taking a device back) and its negative cases are taken up under
   questions 13 to 16 and rule 6, in the model's own words. The
   project's internal record says which of them the model took, which
   it left, and why.
8. **Words.** S3-D.2's rule and the M13 plan's rule 9 apply. Further:
   - **holder**, **owner**, and **reach** are section 4's;
   - an **assignment unit** is question 2's;
   - **pass-through** means that a VS domain drives the device's own
     registers;
   - a unit is "assigned to" its owner, a rule is "enforced by" an
     element, and a profile "includes" an extent. "Held" is used only
     of the results that rule 4 names;
   - for an IOMMU's per-device state the model uses the IOMMU
     specification's words, "device context" among them, and never
     "IOMMU domain" or "group", which are Linux's.
9. **Nothing is copied.** Specifications and precedents are cited by
   version and section, with short attributed quotations only where the
   wording matters. Nothing of the vendor's is copied (the M13 plan's
   rule 4).
10. **Nothing is built.** M14 changes no code, tool, test, or image;
    no file under `model/`; nothing of the tool lock; no claim text;
    and no path that the proofs' records bind (the M13 plan's rule 7
    lists them, and the policy checker, `mvp/tools/policy-check.py`, is
    among them). Outside `planning/` it changes three files, all under
    `mvp/docs/`:
    - **The claim ledger's source and its rendering, by one pin.** The
      ledger records the SHA-256 of `planning/security-model-v1.md` as
      evidence for one row, and its check compares it. The revision's
      commit refreshes that pin and its note, as Revision 4's did, for
      the responsible human's decision with the revision. The row's
      claim, methods, and non-claim do not change.
    - **The AI-assistance disclosure, by one section**, with the
      result.

    A commit that changes any of them is checked by one whole
    `./mvp/mvp check`.
11. **AI assistance.** The model is written with AI assistance: one AI
    tool writes and reviews it, and another reads the inputs and checks
    the drafts against them. An independent, read-only, automated
    review reads each draft before it is proposed (Q10). The
    disclosure's section names the tools, and says who made what.

## 6. Where the work lives

| What | Where |
| --- | --- |
| This plan, the result, and M14's packets | The public line's `planning/`; the decision records of the packets in the project's internal records |
| The model | `planning/security-model-v1.md`, as an appended section (Q2), with the claim ledger's one pin (rule 10) |
| The disclosure's section | `mvp/docs/ai-assistance.md` (rule 10) |
| Notes from the reading | Scratch on the workstation, outside every repository. The model cites the sources that the notes come from, never the notes |
| What the checklist gave the model | The project's internal records (rule 7) |

## 7. The work packages

| ID | Work | Exit |
| --- | --- | --- |
| M14-1 | **The reading.** The inputs pinned. The specifications and the precedents read for what each makes an object, and what authority it attaches to it. The emulated machine's devices, RISC-V IOMMU models, and interrupt controllers read from its documentation and source (Q5). The model's first draft, with every question of section 4 answered or marked | The draft, with its notes |
| M14-2 | **The model.** The draft tried on the three instances of rule 5. The analyses run by hand on the worked instance. Each invariant given what would show it (rule 6). H06 and H07 answered. Both triggers evaluated (question 23). The inventory of what the abstract model, the policy checker, the scenario's format, and the partition descriptor would gain, with no change made to any of them. Reviewed (Q10) | Security model v1 Revision 5, proposed at its own exact commit, for the responsible human's sign-off |
| M14-3 | **The result.** The model read against M13's record and against the emulated machine, as a table for each: what the model's classes say of each bus master and of each device; its assignment unit; what a device path would have to show for each invariant; and what is not established. The glossary's, the hardware roadmap's, and the roadmap's lines kept current, and the disclosure's section | The result's commits, for his sign-off |

**Order.** M14-1, then M14-2. M14-3 follows the responsible human's
sign-off of the model (Q8), since it reads the facts against the
accepted invariants.

**The board.** M14 has no session on the board, and asks nothing of it.

## 8. What the model says, and what may be said

- The model is specification. It implements, runs, proves, and tests
  nothing, and its invariants are asserted of no image.
- It is evidence for no claim, and it changes no claim text. No page
  says, on the strength of M14, that a device's memory accesses are
  confined on any platform, that the project supports a device, or
  that a device path exists.
- The result reads facts against the model. Where a fact is missing, it
  says "not established", as M13's record does. It chooses no device
  and no mechanism, and a row that shows only one mechanism for a
  master on the board says so as a fact, not as a decision.

## 9. Soft limits

A limit that is passed is a stop for re-evaluation, never a cut to the
work. Only the responsible human re-sets one.

**Counting rule:** added lines by `git diff --numstat` from this
plan's acceptance: for the model, of `planning/security-model-v1.md`;
for the result, of `planning/mvp-m14-result.md`.

| Lane | Limit | Basis |
| --- | --- | --- |
| The model, Revision 5 | 900 lines | Revision 4 added 577 lines for one attacker, four classes, and eight invariants. Revision 5 also adds classes to the notation, analyses, and a worked instance |
| The result page | 450 lines | M13's result has 424 |

## 10. Stop conditions

Each returns the work to the responsible human. The MVP plan's stops
stand beside them, as section 11 reads them.

1. The model cannot be written without editing an accepted sentence of
   the security model, or of another accepted text, other than by the
   changes that section 11 names.
2. An invariant, or the reading of an instance, would rest on a fact
   that M13's record marks "not established", or on a held result; or a
   sentence of the model would read differently for a different held
   result.
3. The model cannot stay neutral: a question of section 4 cannot be
   answered without choosing the device, the mechanism, or who programs
   it. The choice is then put to the responsible human, with the
   options.
4. The static device case fires the capability trigger or the
   runtime-check trigger (the MVP plan's stop condition 4).
5. A reading of an instance shows that an accepted invariant, MVP 1.0's
   claim, or the boundary's claim with its limit is no longer true as
   written once a VS domain owns a device. The model says so; and if an
   accepted claim rests on it, the work stops.
6. A step would need code, a tool, a test, an image, a file under
   `model/`, a session on the board, a firmware build, or a change to
   the tool lock, to the claim, or to a path that the proofs' records
   bind. Rule 10's changes under `mvp/docs/` are not such a change.
7. A text would name a Beryllium unit a supervisor domain (or "SD"), an
   RDSM, or an SDSM, or give one an SDID or an MPT (S3-D's stop (k)).
8. A finding bears on the vendor's product's security, in the sense of
   the M13 plan's rule 10. That rule then applies, as the M13 plan
   states it.
9. Anything would be sent to the vendor, to a specification's authors,
   or to another project.
10. A soft limit is passed.

## 11. Accepted rules: one amended by name, and ten read

### The rule that this plan amends

The MVP plan's stop condition 1 returns the work to the responsible
human at "Any need to change an accepted R0-R7 or B0-B7 byte or an
accepted document's text, other than the additive security model v1
revision that M3 plans, which goes to the responsible human as its own
exact commit". Plan revisions S3-C and S3-D each added to that
exception, by name, inside the MVP plan (S3-C.8; S3-D.8). S3-C.2 puts
among MVP 2.0's contents "new object classes as additive
security-model revisions admitted by name".

**Accepting this plan amends stop condition 1 by name: its exception
list gains the additive security model v1 Revision 5, the device and
DMA object model, which goes to the responsible human as its own exact
commit.**

- This is the first such amendment that a milestone's plan makes, and
  not a Plan revision of the MVP plan. After it, the MVP plan's own
  text no longer lists every exception. Revision 5's status record
  names this plan as what admits it, as the status records of
  Revisions 2 to 4 name S3-C and S3-D.
- Q14's alternative is a Plan revision of the MVP plan, first.
- Other changes ride with the revision and with the result, each for
  the responsible human's decision with its commit: the claim ledger's
  pin of the security model's file and its note (rule 10), which
  Revision 4 called a change to "One accepted document"; and the lines
  of the hardware roadmap that M14-3 brings up to date, which M13's
  result counted as accepted text.

### The rules that this plan reads

It changes the text of none of them. The responsible human's sign-off
of this plan accepts these readings.

| Rule | M14's reading |
| --- | --- |
| Security model v1, Part 2: "Device, DMA, IOMMU, or interrupt-injection objects. None exists in any configuration; the classes are added when the first does". R4.5 restated it on 2026-11-11, after S3-C.2's order had been accepted | Revision 5 adds the classes as specification, before any configuration has a device, so that step (3)'s plan can be written against them. That is S3-C.2's order: the object model, step (2), before the device path, step (3). No configuration uses the classes before step (3)'s plan |
| The MVP plan's stop condition 3: "Any milestone that needs a hart beyond the layout, ... a device, an IOMMU, DMA, or guest-visible interrupt injection beyond each domain's own timer". The M13 plan read it so: "Steps (2) and (3) will need a device, the IOMMU, or DMA; their plans name this stop for the responsible human's decision"; and M13's result says the same | This plan names the stop, and reads step (2) otherwise than those two sentences expected: M14 needs none of them. It writes the model of them, and builds, boots, and assigns nothing, as the M13 plan said of reading the facts about them. Step (3) will need them, and its plan names this stop for the responsible human's decision |
| The MVP plan's stop condition 4: "A scenario that fires the capability trigger or the runtime-check trigger, or that needs dynamic management beyond M2's management calls" | The model evaluates both triggers for the static device case (question 23). If either fires, M14 stops there (stop 4). M14 builds no scenario, so the stop's second half does not arise in it. M2's management calls are `pause` and `terminate`, so a restart is beyond them: a plan that builds question 15's restart names that half for the responsible human's decision |
| S3-C's stop (e): "any change ... to an accepted model file or gate ..." | M14 changes no file under `model/`. The revision lists what the abstract model would gain, as Part 7 did for Model 0.2, and makes no change |
| S3-C's stop (d): "a claim-text change other than those S3-C.7 pre-authorizes" | No claim text changes. The ledger's one pin and its note are refreshed in the revision's commit, and the disclosure gains a section (rule 10) |
| S3-D's stop (k) | The model names no Beryllium unit a supervisor domain, and gives none an SDID or an MPT. Its paragraph on that specification reads it, and decides nothing (Q13) |
| D12: "Each milestone plan states its CHERI alignment in one paragraph; no CHERI mechanism" | The model uses no CHERI mechanism, and changes nothing of the CHERI variant. It records where a device's authority is exactly bounded: a register extent, a master's reach, and an interrupt's route. Those are what a capability could carry. Whether one should is for the CHERI track |
| The M13 plan's rule 10, under which the results of two of M13's probes are held | It stands (rule 4, and stop 8) |
| The threat model's deferred lists. Part 1 defers "physical attacks", "compromised vendor roots", and "a firmware-hostile launch", among others. R4.3 defers "a defective or hostile M-mode firmware, and a boot chain that delivers another firmware or another descriptor", and "the board's other execution contexts, and whatever addresses memory without one, such as a device that masters the bus or the debug module, until an inventory shows what they can reach" | Revision 5 takes up three things from those lists, and the rest of them stays deferred. From the last of R4.3's additions it takes up the bus masters that M13's record lists, that record being the inventory; and those of the board's other execution contexts that the record shows driving a device, which questions 3 and 19 ask the model to account for as holders. From "a firmware-hostile launch" and from R4.3's addition on the boot chain it takes up what an owner changes, through a unit's surviving state, in what the next boot loads: an effect that the model says is contained, or is allowed and named (questions 14 and 18). A hostile or defective device is modelled by the requests that it can issue on the bus, whatever made it so. An attack on the platform's hardware, and a vendor's signing key that signs a hostile image, are not modelled. The model says how each of its attackers reads with those lists, as R4.3 did for its own (question 17) |
| The implementation plan's milestone 5: "Deliver IOMMU-enforced ownership, one restartable service, a minimal queue/grant protocol, and malicious-service tests"; and its hypothesis: "The core owns IOMMU domains, interrupts, reset authority, and grant/revoke operations" | The model is neutral about the mechanism (rule 2): whether ownership is enforced by an IOMMU is for step (3)'s plan, on the facts. Question 7's requirement narrows the hypothesis: against Revision 4's attacker, what enforces a device's confinement after a hart's activation cannot be HS-mode code on a confined hart. That follows from Revision 4, and is no choice of this plan's. The restart is question 15's |

## 12. Questions and defaults

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | Names | M14, and M14-1 to M14-3. "M14" is also a row's label in the hostile-monitor tables (`mvp/scenarios/anchor/breach.json`, `breach-control.json`, and `mvp/k3/breach/`) and in their records, none of which names a milestone | The responsible human's |
| Q2 | The model's form | Revision 5, appended to `planning/security-model-v1.md` as Revisions 1 to 4 are, with the claim ledger's pin of that file refreshed in the same commit, and one whole `./mvp/mvp check` at that commit | A page of its own, which leaves that file and the ledger as they are |
| Q3 | Neutrality | The model chooses no device and no mechanism, and does not say who programs one: those are step (3)'s | The mechanism chosen now for the board, which makes M14 a design, and needs facts that M13's record marks "not established" |
| Q4 | A form that tools can run | None in M14. The analyses are defined, and run by hand on the worked instance. What the policy checker, the scenario's format, the partition descriptor, and the abstract model would gain is listed, and none is changed: the policy checker is a path that the proofs' records bind | The abstract model's policy layer extended now with the new classes, which needs S3-C's stop (e) decided for it, and a soft limit of its own |
| Q5 | The facts that the model is read against | M13's record of one K3 COM260 board; and the emulated machine of the project's gates, QEMU's `virt`, from upstream's documentation and source at the tag `v10.2.2`, with nothing run | The board's record alone; the emulated machine is then read when step (3) is planned |
| Q6 | A change of owner while the system runs, and hot-plug | Named, and left to step (5). The states are defined so that those transitions can be added. The restart of an owner with its unit kept is modelled (question 15) | Modelled now; or the restart left to step (5) too |
| Q7 | The I/O service VS domain | An ordinary VS domain that owns a device and serves others through declared channels. The model adds no class of subject for it | A class of its own |
| Q8 | How the model and the result are put to the responsible human | The model first, as its own exact commit, for his sign-off; then the result | One range, signed once |
| Q9 | The precedents read | seL4 and capDL, and the synthesis's precedent lessons (H56) | The responsible human's list |
| Q10 | Review | An independent, read-only, automated review of the model's drafts and of the result, with its findings and their disposition in the internal packets | None |
| Q11 | The soft limits | Section 9's | The responsible human's |
| Q12 | How this plan's decision is recorded | As its status says: the sign-off of the proposing commit, with the record kept internally | A second commit that sets a decision record here |
| Q13 | The supervisor-domain specification, and CoVE | One paragraph in the model on that specification's chapters 6 and 7, which reads them and decides nothing. CoVE is not read in M14. The compatibility analysis of both stays MVP 2.0's last step (S3-D.3) | A paragraph on CoVE too, with its specification pinned as an input; or more of that analysis now |
| Q14 | How Revision 5 is admitted to stop condition 1's exception | By the sign-off of this plan (section 11) | A short Plan revision of the MVP plan that amends stop condition 1 by name, as S3-C.8 and S3-D.8 did, before the model is proposed |

## What acceptance would authorize

- M14-1 to M14-3.
- Fetching, read-only, the specifications and precedents of section 2,
  and the emulator's documentation and source at the tag that section
  2 names, working around no access control.
- Commits on the public line, unsigned, for the responsible human's
  sign-off: security model v1 Revision 5 as its own exact commit, with
  the claim ledger's pin of that file and its note; the result page
  with its site entries; the glossary's, the hardware roadmap's, and
  the roadmap's lines; and the AI-assistance disclosure's section on
  M14.

It would authorize no code, tool, test, or image; no change to a file
under `model/`, to the tool lock, to the claim's text, or to a path
that the proofs' records bind; no change to an accepted text other
than by the appended revision, by the claim ledger's one pin and its
note, and by the lines of the hardware roadmap that M14-3 brings up to
date; no session on the board, of any kind; no choice of a device, of a
mechanism, or of who programs it; nothing sent to the vendor, to a
specification's authors, or to another project; and no push, merge,
tag, or release step.

## Review record

An independent, read-only, automated review read the drafts of this
plan before it was presented. Its findings and their disposition are in
the plan's review packet, in the project's internal records.

## Status record

```text
mvp_m14_plan=accepted-if-its-proposing-commit-is-on-the-public-main-with-the-responsible-human's-sign-off;otherwise-proposed
mvp_m14_plan_governing_text=mvp-plan.md;S3-C.2-MVP-2.0-step-2;S3-D.3
mvp_m14_plan_direction=2026-11-25
mvp_m14_plan_product=security-model-v1-Revision-5;the-device-and-DMA-object-model;additive;its-own-exact-commit
mvp_m14_plan_answers=H06-authority-without-a-mapping;H07-when-a-finer-type-has-security-meaning
mvp_m14_plan_reads_against=M13's-record-of-one-K3-COM260-board;the-emulated-machine-QEMU-virt-at-upstream's-tag-v10.2.2;one-worked-instance
mvp_m14_plan_work_packages=M14-1-reading;M14-2-the-model;M14-3-result
mvp_m14_plan_questions_of_the_model=23
mvp_m14_plan_rules=11
mvp_m14_plan_stops=10
mvp_m14_plan_questions=Q1-Q14-defaults
mvp_m14_plan_amends=stop-condition-1-by-name;its-exception-gains-the-additive-security-model-v1-Revision-5
mvp_m14_plan_reads=Part-2's-sentence-on-when-the-device-classes-are-added;stop-conditions-3-and-4;S3-C-stops-d-and-e;S3-D-stop-k;D12-stated;the-M13-plan's-rule-10-stands;the-threat-model's-deferred-lists;the-implementation-plan's-milestone-5-and-its-I/O-hypothesis
mvp_m14_plan_mechanism=not-chosen;step-3's
mvp_m14_plan_builds=nothing;no-code;no-model-file;no-bound-path;no-board-session
mvp_m14_plan_ledger=one-pin-of-security-model-v1.md-refreshed-in-the-revision's-commit;the-ledger's-source-and-its-rendering
mvp_m14_plan_disclosure=one-section-of-mvp/docs/ai-assistance.md-with-the-result
mvp_m14_plan_sends=nothing
mvp_m14_plan_claim=none
```
