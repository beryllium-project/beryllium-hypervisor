<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# MVP 2.0 milestone M11: the board addendum (M11-B)

**Status.** Proposed by the commit that adds this page, on the public
development line. If that commit is on the public `main` with the
responsible human's `Signed-off-by`, this addendum is accepted as
written, with QB1 to QB14 at their defaults. Any other answer needs a
revised commit before the sign-off. The signed commit differs from the
one reviewed by that line, its committer date, and its parent: it is
rebased onto the public `main` as that stands when it is signed, after
M11-E's line has landed there. The project's internal records keep
both commit IDs and the instruction.

This is the board addendum that the [M11 plan](mvp-m11-plan.md) names
in its D-15, and it is part of that plan. It is written on the facts of
the read-only inventory, as
[Plan revision S3-E](mvp-plan.md) of the MVP plan records them, and on
two further readings of the sources, made on the workstation. It plans
M11-B: the M11 candidate on one SpacemiT K3 COM260 board, under a
firmware build of the project's own, booted from a microSD card (below:
a card). It settles each point that D-15 lists, answers the choice that
S3-E.2 left (Q62), fixes the rules for the M-mode code that the board
needs (S3-D's stop (m)), and fixes the words for a board result
(S3-D.7).

It presupposes M11-E: the candidate under emulation, accepted at its
own commit. Nothing here changes that candidate's monitor, its images'
sources, its claim page as it stands, or anything at the tag `mvp-1.0`.
Terms are S3-D.2's and the M11 plan's.

**In short.** No step of this addendum writes the board's NOR, as
S3-E's item 9 defines a write, and none makes the vendor's code write
it. The board gets a card, which holds the vendor's published boot
chain with the project's firmware in the firmware's place. That
firmware is the candidate's, with a device tree built in and one small
addition in M-mode, which gives the board the reset device that every
image needs. The card is put in for a session and taken out again; the
board then boots from its NOR as before.

## What it rests on

Each statement names its evidence, as S3-E.1 does: *source* (the
vendor's published source, or the firmware base at its pin, read on the
workstation); *files* (the vendor's published images); *board* and
*logs* (S3-E.1's readings); *build* (an output of the project's build
of the candidate's sources); *run* (a run of that build under QEMU);
*count* (the base's rules, applied by hand to the board's device tree;
no firmware was run). A statement by source is a reading: it says what
the code would do, and no run on the board has shown it. Nothing below
is hardware validation.

1. **With the firmware as the candidate builds it, no image would run
   on the board, and no record would print, unless a real-time core
   answered a request that the base does not signal to it** (source,
   build).
   - The monitor's first check requires the firmware's system-reset
     call to be present. The base offers that call only when the
     platform has a reset device.
   - The project's additions print the commit records in the reset
     path, and only when a reset device exists.
   - On the board's device tree, the one reset driver of the build
     that matches a node is the one that asks a real-time core, through
     a mailbox. It registers a device only after that core has answered.
     The base does not recognise the mailbox's doorbell as this tree
     names it, so it never rings it. Whether the core answers without
     it is not established.
   - Without answers, the base tries five times at cold boot, about
     100 ms in all, prints eleven error lines, and goes on. Each try
     writes a request into the queues that it shares with the
     real-time core, at an index that it reads from them.
   - Under QEMU the machine has a reset device, so none of this shows
     there.
2. **The base finds its other devices on the board's tree** (source):
   the console, the timer, the interrupt controllers, and the start of
   a hart. It has no stop or suspend for a hart there. It starts no
   hart at cold boot, and has no code for the real-time cores. For
   harts 8 to 15 it sets a boot vector and the interconnect's snoop,
   and wakes none; the vendor's firmware wakes one of them, to park
   it. The base also leaves out part of the vendor's cold-boot setup:
   a reset and a clock for a memory that the harts share, the
   clusters' cache-flush control, their power-down votes, and two
   registers that the vendor's firmware writes at each change of
   mode. Whether the vendor's U-Boot and the guests run without these
   is not established; the first boot under the project's firmware is
   the first test of it.
3. **The entry budget fits if the board has at least fourteen PMP
   entries** (count, build).
   - On the board's tree, the root OpenSBI domain would hold eight
     regions. An OpenSBI domain of the project's inherits six of them,
     or five when the mailbox's node is disabled, which the base
     honours (source); under QEMU it inherits five.
   - At the pin an OpenSBI domain may hold 32 regions (source). D-15's
     "sixteen" is the vendor's tree's limit, not the base's.
   - Under QEMU the confined harts use 11 to 14 PMP entries with plain
     PMP: five inherited, and at most nine of a profile's own (the
     largest is `anchor`'s second VS-domain hart). With the same five
     inherited, the board needs the same.
   - The board's PMP count, grain, and address bits are not
     established. The base prints all three in its banner, for the
     boot hart.
4. **Smepmp cannot be tried without a risk of a silent stop** (source).
   The base takes Smepmp from the tree's ISA string alone, and probes
   nothing. The board's tree lists none. A tree that listed it on
   hardware without the register would stop the boot, likely without
   a line on the console.
5. **The banner prints on the board** (source). The vendor's SPL passes
   no option that silences it. It gives the platform's devices, the
   hart count, each OpenSBI domain's regions, and, for the boot hart,
   the PMP count, grain, and address bits, the privilege version, and
   the ISA extensions.
6. **The capture checker cannot judge such a capture today** (source).
   A firmware banner makes it read the capture as QEMU's. It wants
   commit records for exactly eight harts; on the board's tree, which
   has sixteen, the firmware prints sixteen, and it prints none when
   the tree holds no digest.
7. **A device tree that the firmware carries replaces the SPL's**
   (source). The base copies its built-in tree over the tree that the
   SPL handed it. The SPL's own additions are then gone: the memory
   nodes, the boot hart's ID, and a list of the loaded images. The
   vendor's U-Boot takes the firmware's tree as its own, and sizes
   memory from its memory nodes. The published tree says 2 GiB; the
   board has 8 GiB (board).
8. **The vendor's U-Boot reaches the NOR only through a flash device
   of its own device tree** (source).
   - It writes the memory-training record at each boot that trained
     the memory fully, which every boot from a card does. The write
     goes to the medium that the board's strap selects, the NOR here,
     whichever medium the boot came from.
   - It does so through the first SPI-flash device that its device
     tree gives it. With none, the function writes nothing and
     returns, and the boot goes on. On the way it looks for the
     flash by the name that its build fixes, and prints one line that
     it found no valid device of that name. The line is the sign that
     U-Boot has no flash device; it is no probe, and touches no
     hardware.
   - On a boot from a card it reads its environment from the card. No
     other path to the NOR was found on the way to the MVP's load and
     boot: not the environment's place, the boot mode's detection,
     the splash loader, the fastboot check, or U-Boot's own fallback
     tree. Its generic code was not read whole.
   - On a boot from a card the SPL reads nothing from the NOR (S3-E.1,
     statement 2).
9. **The card's layout** (files, source): the environment at 640 KiB;
   the boot information at 1 MiB; the SPL at 1.5 MiB; the real-time
   cores' image at 4 MiB; the firmware at 7 MiB, in an area of 1 MiB;
   U-Boot at 8 MiB. The SPL finds the last three by offsets in the
   environment. The vendor's own card image has a protective MBR and a
   GPT with three entries, all for its operating system. Whether the
   boot ROM needs a partition table, and which entries, is not
   established; the operator's notes say that other layouts stopped
   the ROM before any output.
10. **What on a card can start a flash, and the autoboot** (source).
    S3-E.1's statement 6 stands: a partition named `bootfs` with the
    vendor's flashing table. Three more facts bear on a card.
    - When a card's first partition table is not valid, the vendor's
      U-Boot reads the backup table at the card's last block. A card
      that once held another image can still have one there, with
      that image's partitions.
    - The published default environment holds three variables that run
      the vendor's flashing command, and boot-menu entries that run
      them. Nothing runs them unless the menu is opened.
    - The published default has no boot delay: U-Boot looks for its
      stop key once, for about 10 ms. A key sent when the autoboot
      line is seen arrives too late.
11. **The firmware's image** (files, source) is a FIT with one image,
    loaded and entered at `0x1_0000_0000`, and one configuration. The
    SPL checks no CRC, hash, or signature of it. The vendor makes it
    with a tool that the workstation lacks. The device-tree compiler,
    which the tool lock holds, writes the same structure from a source
    file (source: the compiler's own format); the image's CRC-32 is
    computed apart. The candidate's firmware, without a tree built in,
    is 278,392 bytes, against the vendor's 269,856 (build, files).
12. **The cache-block control** (source, run). At a hart's
    confinement the additions clear the invalidate control, when the
    privilege version is 1.12 or later, and record the register.
    Whether the instruction then traps on these cores is not
    established; the hostile-monitor images test it.
13. **The trap paths** (source). The base's code for this platform
    sets no hook on an access fault, and no emulation of its own. The
    vendor's hook that emulates some accesses is in neither the
    board's binary nor the base. By Linux's own measurement on the
    board, these cores make misaligned accesses themselves (board);
    whether every form avoids the trap is not established. The base
    emulates a read of the time register only for a hart that lacks
    it; whether these cores have it is not established, and the
    banner's ISA line shows it.
14. **The other execution contexts** (source, files).
    - Two real-time cores are started by the SPL at every boot from
      either medium, with the vendor's image (an inference from the
      source and from the firmware calls that Linux detects, as
      S3-E.1's statement 4 has it). Nothing was found that confines
      them: no PMP, no memory-protection unit, no firewall, in any
      source read. Whether the system-on-chip has a bus firewall for
      them is not established. The vendor's firmware locks their
      memory against the application harts; the base does not.
    - Harts 8 to 15 have no hypervisor extension. The vendor's
      firmware wakes one of them at cold boot to park it; the base
      wakes none.
15. **The hostile-monitor images name devices, in QEMU's forms**
    (build). Their attempts outside the monitor's own layout come
    from a map of the machine, and from rows that carry the machine's
    register forms: one byte of the console's scratch register, an
    interrupt source of the supervisor-level controller, QEMU's power
    device. On the board the console's registers are 32-bit words at
    other offsets, that controller is disabled, and there is no such
    power device. M-mode counts every access fault that it hands back,
    whatever caused it.

## Decisions

### B-1 The firmware base, and how the board's firmware is built (D-15, first point)

The base is the M11 plan's: upstream OpenSBI at
`ed70256dd22c09962d146e433834239825ef0616`, with the project's patch
series, as M11-E's candidate has it. The vendor's tree is not used: it
reports another SBI version than the monitor requires, it prints
nothing, and the additions would have to be made again for it, so the
board would run other firmware than the emulation's evidence is about.

The board's firmware is a second build of the same sources: the
candidate's configuration, the series, and what B-2 adds, built with a
device tree of its own for each image (B-3). The build for QEMU, and
its pinned binary, do not change by a byte.

**D-2's build rule holds for each of the board's builds, read for a
build that is made for one image.** D-2 pins the firmware's binary in
the tool lock, and has every run check it. A build for one image
cannot be in the lock before it exists, and the lock is one of the
paths that the proofs' records bind. So, for these builds: each is
made on the host and inside the evaluator, from the same inputs, and
the two must be equal byte for byte; its SHA-256 is recorded in the
plan's decision record before its card image is made (at M11-B3 for
the first sitting's build, at M11-B4 for the second's three); the
card image's maker refuses a firmware with another, and the card's
read-back shows that the card holds it. The recipe's input, the
vendor's published U-Boot image, is given to both builds by its path
and checked by its SHA-256, as the kernel's source and the firmware
base's are; it is never committed.

### B-2 What the board's build adds in M-mode (S3-D's stop (m))

**One addition: a reset device that halts.** Statement 1 leaves three
ways to give the board's build a reset device: one of the project's
own, which only halts; the vendor's doorbell handling brought to the
base, so that the real-time core carries the reset out; or a node for
a driver that the base already has, which this board has no device
for. This addendum takes the first (QB5).

Its requirements:

1. On the board's tree, the firmware's system-reset call is present,
   and its shutdown type is supported.
2. A shutdown prints the commit records as today, where the tree
   holds a digest. Then the calling hart halts. It returns to no
   caller.
3. It touches no device: no register write, no interrupt to another
   hart, and no message to a real-time core.
4. It is chosen by the board's build configuration alone, and needs no
   node in the device tree. It is registered in the code that the
   base's device-tree platforms share, not in this board's own, so
   that a run under QEMU's machine exercises the same lines. The
   build for QEMU is unchanged, byte for byte.

**The other harts.** The addition sends nothing to them. The base's
own reset path, before it calls any reset device, halts the other
harts of the caller's OpenSBI domain by an interrupt (source). With
the boundary on, the control hart is alone in its OpenSBI domain, so
that reaches no hart: at a scenario's shutdown the two VS-domain
harts have ended their work and wait, parked, in the monitor, each
inside its profile, and stay so until the reset. With the boundary
built off, all three harts are in one OpenSBI domain, and the base's
halt reaches harts 1 and 2, as it does on any platform.

It cannot power the board off or reset it. The resident firmware's
shutdown did not power this board off either: each MVP 1.0 run ended
with the reset dongle's reset, as these will.

**Its rules** are D-2's, unchanged: written afresh from this page by
an AI tool that can be named, with a record in the change; BSD-2-Clause;
one more patch of the series; reviewed line by line, the review going
back to the writer as comments. It acts on nothing outside the
firmware, so D-2's rule that the additions act only on what the
firmware's own device tree names is kept. It lies inside the M11
plan's limit for the firmware additions, of whose 800 lines the series
uses 720.

**Its tests under QEMU** (B-10), with a build of the board's
configuration that has no tree built in: a run on a tree without the
machine's reset devices, in which a scenario ends with its shutdown
line and the records, and the calling hart halts. The machine then
reports no shutdown, so the harness ends the run itself: it stops the
machine through the oracle's channel after the last record's line,
the oracle reads it, and the run passes or fails by the capture's
judgement and the oracle's, not by the machine's exit. And the same
tree under the configuration without the addition, in which the
monitor fails its first check.

Any other M-mode code for the board is a stop (stop B7).

### B-3 The firmware's device tree: one for each image (D-15, seventh point)

A descriptor belongs to one image: the tree carries the descriptor's
digest, and the image refuses a firmware whose digest is not its own.
The trees of one scenario's images differ in that digest and, for an
image with console input, in a call list.

**The firmware carries its tree** (S3-E's item 12, which lets a
milestone plan state this). Each image under test has a firmware build
with that image's tree built in. The card's U-Boot image is the
published file, untouched; a repacked one would need a further
amendment, and is not proposed.

**The tree is made by a recipe, and nothing of the vendor's is
committed.** The recipe's input is the published U-Boot image, by its
SHA-256 (S3-E.1's table). It takes the tree of the configuration named
`k3_com260_ifx`, decompiles it with the tool lock's compiler, and
makes these changes, each one a named step with a test:

1. The memory nodes become what the SPL would write: one node for the
   board's memory, from `0x1_0000_0000` (statement 7). The boot hart's
   ID is added as the SPL adds it.
2. **The SPI flash's controller is disabled** (QB1). The vendor's
   U-Boot then has no flash device, and cannot write or probe the NOR
   (statement 8).
3. The mailbox and its clients are disabled (QB6). The firmware then
   makes no try at the real-time core and writes nothing into the
   shared queues, and an OpenSBI domain inherits five regions, as under
   QEMU.
4. The descriptor's nodes are added, as the backend renders them for
   QEMU: the configuration node, the digest, the regions, and the
   OpenSBI domains.
5. Nothing else changes. The sixteen CPU nodes stay (QB6); the ISA
   strings stay, so the firmware uses plain PMP (B-6).

For a run with the boundary built off, the tree has steps 1 to 3
alone: no descriptor and no digest.

**The descriptor's backend gains the board as a second platform**: its
memory, the firmware's place, sixteen harts in the firmware's count,
and the devices of statement 2. The descriptor itself does not change,
so each image's digest is the one that it has under QEMU. The expected
tables for the board follow from the backend and from the firmware's
own image, as they do for QEMU. They are compared with the banner's
table in the first sitting, before any run with the boundary on (stop
B5).

**Harts 8 to 15 are parked with harts 3 to 7.** D-3 has a descriptor
name every hart of the platform; the descriptor names eight, which is
the monitor's count and QEMU's. On the board the backend puts harts 8
to 15 into the OpenSBI domain of the harts that no role uses, as a
property of the platform. It finds each hart's node by the node's
hart number, since the board's tree names six of them otherwise. That
OpenSBI domain gives S-mode one page, to execute alone: the park
entry. They are never started: the base starts none, and a hart can
be started only by a caller in its own OpenSBI domain (source), which
no code of the monitor's is. In a run with the boundary built off,
where the tree has no OpenSBI domain of the project's, the monitor's
own code starts harts 1 and 2 alone. With a digest in the tree, the
firmware prints sixteen records; the checker requires those of harts
3 to 15 to show no confinement and no count (B-8).

### B-4 The card (S3-E's item 11)

Item 11 stands as written. This addendum fixes what it left, and
narrows it in three places, which statement 10 asks for.

- **The layout** is the vendor's (statement 9): the published boot
  information for a card, SPL, real-time cores' image, and U-Boot, each
  byte for byte at its offset; the firmware's FIT at 7 MiB; the
  environment at 640 KiB.
- **The partition table** is a protective MBR and a GPT whose 128
  entries are all unused (QB11), made for the card's size, with its
  backup at the card's last blocks. The vendor's U-Boot reads such a
  table as valid and finds no partition, so none named `bootfs`; a
  table that declared no entry at all would be invalid to it, and
  would print an error at every lookup (source). The tool lock's
  partitioning tool must read the table as valid, with no partition.
  If the boot ROM does not boot such a card, that is stop B4, and the
  answer is a revised commit.
- **The whole card is written, every time** (narrowing 1). The writing
  tool writes the image, then zeros to the card's last blocks, then
  the backup table there. Nothing of an earlier image stays: no old
  backup table, and no old partition's bytes.
- **The firmware's FIT** has the vendor's structure: one image, loaded
  and entered at `0x1_0000_0000`, one configuration, and a CRC-32 of
  the image. It is written by the tool lock's device-tree compiler.
- **The environment** is the published default with the declared `be_`
  variables. Its `bootcmd` runs the MVP's load and boot, and nothing
  else: if the load fails, the board stays at the prompt. It holds no
  serial number, no MAC address, and no other identity variable.
  **Every variable that runs a flashing command or enters a download
  mode is removed** (narrowing 2), the boot menu's entries with them.
  The maker's test names each one that the published default holds,
  and refuses an environment in which any value names such a command.
- **Each card image names one MVP image, and nothing is typed in a
  session with a card** (narrowing 3). The published default has no
  boot delay (statement 10), so the session does not try to stop the
  autoboot.
- **One card image for each image under test** (B-3). Each is written
  to a card, whole, and read back before the session that uses it.
  With a card for each image of a sitting (QB3), all are written
  before the sitting, so that no card is written while the
  responsible human waits at the board. With fewer, a card is written
  again on the workstation between two sessions, after its read-back.
  Each image is made on the workstation as one file for its card's
  size, with its SHA-256 recorded. None is committed or published:
  each holds the vendor's files.
- **The writing tool** follows the project's standard for privileged
  tools. It takes the card reader by its stable ID path, refuses a
  device that is mounted, that is larger than 64 GiB, or that is not
  removable, and runs dry first. The session writes the card, through
  an access rule for that one reader (QB4). Installing that rule is
  one command for the workstation's superuser, which is the
  responsible human's. He also moves the cards.
- **The read-back** reads the whole card and compares every byte: the
  image, the zeros, and the backup table. It is made after each
  writing of a card, before the card is used, and after every
  session.

### B-5 The NOR in a session with a card: the choice that S3-E.2 left (QB1)

**No boot from a card writes or probes the NOR.** This is S3-E.2's
option B: its rule is chosen, and it is met by the device tree that
item 12 lets this plan state (B-3, step 2), which is a narrowing.
Option B's own mechanism, M-mode code that clears the record's mark,
is not used. S3-D.6's step 4 then stands as it was written: a card
that carries the project's firmware, "with the NOR untouched". Neither
of the two readings that S3-E pre-authorized for option A is taken.

- On a boot from a card, the SPL does not read the NOR, and U-Boot
  has no device through which to reach it (statement 8).
- The readings around each session (S3-E's item 9) must be equal in
  every range.
- A capture of a boot from a card must hold the vendor's line that
  announces the save of the record, then its line that it found no
  valid flash device, and no line that reports a write to the NOR, or
  that a flash was detected (B-8). Each boot's capture is judged for
  these before the next reset, so that a tree which failed to keep
  U-Boot from the NOR costs one boot, not a session's.
- What is not established is U-Boot's generic code (statement 8). If
  it reached the flash some other way, the capture's lines and the
  readings would show it, and that is stop B2.

Why not option A: it is needed only for a session under the vendor's
firmware, before the first. Each of that session's boots erases and
writes ten blocks of the NOR. What is lost without it: that session
would show the vendor's U-Boot from a card, with its memory size and
its reach to the Beryllium partition, before any firmware of the
project's runs. Without it, a card that the boot ROM and the SPL
accept still shows in the SPL's banner; but a failure after that
banner, in the first sitting, cannot be put on the card's path or on
the project's firmware by that sitting alone. If that happens (stop
B5), a session of that kind is how it would be told apart, and it
stays open to the responsible human as QB1's alternative.

Why not option B's own mechanism: it is M-mode code that acts on an
address which no device tree names, against D-2's rules, and the
tree's step does the same without it.

### B-6 PMP's count, grain, and mode on the board (D-15, second and third points)

- **Plain PMP only.** The board's tree lists no Smepmp, and this
  addendum does not add it (statement 4; QB7). The board's evidence is
  for plain PMP. Smepmp stays emulation evidence.
- **The first sitting reads the count, the grain, and the address
  bits** from the firmware's banner, with the privilege version and
  the ISA extensions. The thresholds, each a stop if missed (stop B5):
  at least fourteen entries; a grain of at most 4 KiB, which the
  layout tolerates; a privilege version of 1.12 or later.
- **The banner speaks for the boot hart alone.** Harts 1 and 2 are not
  read there. If one of them had fewer entries or a coarser grain, its
  confinement would fail its own check, the hart would not commit, and
  the run would fail closed (stop B6).
- **The record holds entries 0 to 15.** If the board has more, the
  firmware's own check at a confinement still covers every entry: each
  later one must be off, or the hart does not commit (source). The
  record does not show them.

### B-7 The trap paths and the cache-block control (D-15, fourth and fifth points)

- **The trap paths** are the base's, as under QEMU (statement 13): the
  access fault that M-mode hands back and counts, the emulation of a
  misaligned access, and the emulation of an instruction that the hart
  lacks. If these cores lack the time register, each read of it by a
  confined hart goes through the last; the first sitting's banner
  shows which.
- **The cache-block control** is the one point where the board can show
  what the emulator cannot: these cores have caches. The attempt is in
  the hostile-monitor images. Its declared outcome on the board is the
  one under QEMU: the instruction traps. M-mode takes that trap and
  hands it on, but counts only access faults, so the trap itself is
  shown by the test's own report alone. What M-mode's record does show
  is the control register of each confined hart, with the invalidate
  control clear. If the register shows otherwise, or the test reports
  no trap, that is a finding, recorded before anything else (stop B6).

### B-8 The witness, and the checker's form for a boot from a card (D-15, eighth point; the M11 plan's Q20)

**The witness is what M-mode prints**: the banner, before any HS-mode
code runs, and the commit records, at the halt. A card in the slot
excludes the debug probe, so nothing reads the machine from outside.
HS-mode code on the confined control hart keeps the firmware's console
call, and can print any line through it, a record's among them. The
project's test images do not; an adversary's would. So the board's
evidence is of a lower class than the emulation's, and the limit says
so (B-11). A record that only M-mode could have made needs a design of
its own (QB8), and is not proposed.

**The checker gains one form, for a boot from a card under the
project's firmware.** It requires, in order:

- the boot ROM's lines, and one SPL banner. No boot of this board
  from a card has been logged, so the ROM's lines for one are not
  known: the first boot's are recorded, they must not be those of a
  boot from the NOR, and the decision record takes them before the
  second sitting, whose captures must hold the same;
- one firmware banner, whose fields are compared with the build's
  expectations; in the second sitting the hardware's facts in it (the
  PMP count, grain, and address bits, the privilege version, the ISA
  extensions, and the devices found) must be the first sitting's;
  and the digest's line, exactly when the tree holds a digest;
- one U-Boot banner, with the board's memory size and the board's
  product name;
- the vendor's line that announces the save of the training record,
  then its line that no valid flash device was found;
- the vendor's line that no flashing partition is on the card;
- none of these: a line that a flash was detected; a line of a write
  to the NOR; a line of a rewrite of the identity EEPROM, or the line
  that comes before a new MAC address is written there; a warning
  that the environment is bad and the default is used; an error or a
  fallback of the partition table;
- the load, with its MD5, and U-Boot's device tree outside the MVP's
  extents, as today's rule has it;
- the monitor's lines, by the rules that judge them under QEMU;
- after the monitor's last line, sixteen records exactly when the
  tree holds a digest, those of harts 3 to 15 with no confinement and
  no count; and none when it holds no digest.

Each requirement has a mutation that the checker must refuse. A
capture of a boot from the NOR keeps today's rules, so MVP 1.0's
captures are judged as before.

### B-9 The other execution contexts (D-15, sixth point)

The real-time cores are confined by nothing in M11, and harts 8 to 15
are parked; the board's words say both (B-11).

- **The real-time cores** run throughout. They are trusted for the
  containment, like the firmware: they could reach any memory, as far
  as the sources show. With the mailbox disabled (B-3), the project's
  firmware sends them nothing. The base does not lock their memory; a
  confined hart cannot reach it, because it lies outside every
  profile.
- **Harts 8 to 15** are never started (B-3). What state a core that
  was never woken is in is the hardware's, and is not shown.

### B-10 The images, and the evidence under emulation for the board's work

**The scenario images are the candidate's**, byte for byte: a
descriptor does not depend on the machine, so an image's digest is the
same under both trees (build).

**The hostile-monitor images for the board are images of their own**,
built from the candidate's sources with a declaration for the board
(statement 15).

- Its rows on the monitor's own layout are the candidate's.
- Its rows on devices use the board's register forms, and name only
  devices that the board's tree enables, so that a working device
  cannot refuse the access by itself: the console, the machine-level
  and supervisor-level interrupt files, the machine-level interrupt
  controller, and the timer.
- It has M-mode's own memory at the firmware's place on the board,
  and, for the memory that no extent names, a range that lies outside
  the firmware's and the real-time cores' memory.
- It has no row on a power device, which the board lacks.
- It adds a start of, and a status read of, one hart among 8 to 15.
- It names no witness on a device: the board has no oracle to read
  one. Under QEMU, where these images are run first (below), the
  board's device addresses are memory.
- **No row names a device that holds persistent state**: the SPI
  flash's controller, the eFuse block, an I2C bus, the
  power-management registers, or a storage controller. The generator
  refuses such a row, by the board's device tree (stop B9). If the
  boundary failed, an attempt would then reach memory, an interrupt
  controller's register, the console's scratch register, or the timer,
  and nothing that outlasts a reset.

**The images on the board** (QB2), each in a session of its own (below):

| Sitting | Card image | What runs from it |
| --- | --- | --- |
| First | The project's firmware, boundary off | The candidate's `two-guests`, built without the boundary: three runs |
| Second | `anchor`'s | `anchor`, the scenario with the largest profiles: three runs |
| Second | The board's hostile-monitor image for the second VS-domain hart | That image: one run |
| Second | The board's hostile-monitor image for the control hart | That image: one run |

The images are those built by GCC (QB12). The images built by Clang,
the boundary's negatives, the other scenarios, Smepmp, and the runs
that tell an attempt's effect with the boundary off stay emulation
evidence.

**Before any sitting, under emulation or offline**, at the commit that
holds the board's tools and the addition:

- the addition's two tests (B-2);
- the recipe's tests: each step's effect on the published tree, read
  back through the compiler;
- D-3's independent checker on each of the board's trees and expected
  tables, with its mutations, as it runs on QEMU's;
- the board's two hostile-monitor images under QEMU's `k3-like`
  machine with the boundary on. Every address of theirs lies outside
  every profile there too, so the run tests their declarations, their
  counts, and the hook before any hardware does;
- the generator's refusal of a row outside the list above, with one
  mutation for each kind of device;
- the checker's form for a boot from a card, on synthetic captures: a
  passing one, and one mutation for each requirement;
- the card's tools, on a file in place of a device, and their
  refusals; and the read-back's refusal of a card with an old backup
  table or an old partition's bytes;
- the first sitting's firmware build, on the host and in the
  evaluator, equal byte for byte (B-1). The second sitting's three
  are made at M11-B4, by the same rule, before their card images;
- the candidate's own gates, which must still pass: the board's work
  changes no image of the candidate's and no check's verdict.

**The proofs' records.** The board's work changes nothing under the
paths that those records bind, among them the monitor's sources, its
makefile, the scenarios, the guests, the tool lock, and four tools
(the scenarios' generator, the guests' device-tree generator, the
policy checker, and the port script). Its declarations, build rules,
and tools live beside them; the hostile-monitor images' generator,
which the board's declaration needs changed, is not one of the four.
If one of those paths must change, M11-B's candidate is a re-proof
point as D-11 has them, with its `verify` (stop B7).

### B-11 The words for a board result (S3-D.7)

The M11 plan's "Claim text" has, for after M11-B: "the clause's first
words become 'In QEMU and on one SpacemiT K3 COM260 board, booted there
from'", followed by words that this addendum fixes. Read so, the
clause would say of the board three things that only emulation shows:
that the harts which the monitor does not use stay stopped; that an
attempt "had no effect", which takes a reading from outside the
machine; and what the runs with the boundary built off show. The
board's sessions show none of these. So this addendum proposes another
form, and names the change (below; QB14). It is used only if M11-B's
result is accepted with every session passed.

**The clause keeps its words**, which are about emulation. A paragraph
about the board follows it:

> On one SpacemiT K3 COM260 board, the images that the ledger names
> ran with plain PMP, booted from a microSD card that held the
> vendor's published boot chain and, in the firmware's place, a build
> of that firmware with one more addition, a reset device that only
> halts, and a device tree built in. In each run with the boundary
> on, M-mode's printed record showed each of the monitor's three
> harts confined, with its profile's entries, and, for each hart,
> counts of access faults, of refused calls, and of rejected calls
> equal to the sums that the test declares: none in a scenario's run.

**The limit's second sentence** becomes "Under emulation, PMP's
behaviour is the emulator's, which has no cache." **And the limit
gains**, at its end:

> On the board this is diagnostic evidence from one board, and it is
> not hardware validation. What M-mode prints there is the only
> witness: nothing read the machine from outside, and no
> hostile-monitor image ran with the boundary built off, so no
> attempt's effect was told apart; M-mode's counts are sums for each
> hart, not one for each attempt; and code on the confined control
> hart could print the same lines. A fault on a device's register
> there may have a cause other than PMP. The vendor's boot chain and
> its two real-time cores with their image are outside the boundary
> and trusted, as is the recipe that makes the firmware's device
> tree; nothing in M11 confines those cores. The thirteen harts that
> the monitor does not use, the eight without a hypervisor extension
> among them, are started by nothing in the firmware or the monitor,
> by their sources; with the boundary on, the firmware's banner shows
> them parked, as under emulation. Nothing shows their state.

If a sitting stops and the responsible human accepts a narrower
result, the clause and its limit stay as they are, and the board's
record is cited in the evidence record as a diagnostic record, with
what it showed.

## The sittings, and their sessions

A **sitting** is a time when the responsible human is at the board. A
**session** is S3-E's card session: every boot between one card's
insertion and its removal, both by him. Each card image has a session
of its own, on his word for that session, given as it starts. In each:
boots from system reset; nothing typed while the card is in; no
`saveenv`; a reading of the NOR before the card goes in and after it
comes out (item 9), equal in every range; the card read back
afterwards. S3-A.1's items 1 to 8 and S3-E's items 9 to 13 hold.

**Before the first session:** the rehearsal of S3-E's item 10 has run
and passed (stop B12). It is the staging's step before any card.

**A sitting, in outline:**

1. From the board's own Linux, the preflight, and the staging of the
   sitting's MVP images on the Beryllium partition, as MVP 1.0's
   campaigns staged them.
2. A boot from the NOR to the prompt, and a reading. U-Boot's line
   for the memory size in this boot is the sitting's reference for
   that size.
3. For each card image of the sitting, a session:
   1. his word; he inserts the card; one reset;
   2. the session's boots from the card. A run ends at the monitor's
      last line and, where the tree holds a digest, the records; then
      the halt. Each boot's capture is judged before anything else is
      done (B-5). Each boot but the last is ended by one reset;
   3. after the last boot's halt he removes the card; then one reset;
      a boot from the NOR to the prompt; a reading, which must equal
      the one before it. The same reading serves as the next
      session's first;
   4. the card's read-back on the workstation: after the sitting, or
      at once when the card is to be written again for a later
      session.
4. The board's own Linux, and the preflight again.

**The first sitting: the project's firmware, with the boundary off.**
One session. It shows the chain: the boot ROM and the SPL take the
card; the SPL enters the project's firmware; the banner prints;
U-Boot comes up with the board's memory size and without a flash
device; the candidate's `two-guests`, built without the boundary,
runs to its shutdown line; the halt. Its record holds the banner's
facts (B-6), the root OpenSBI domain's table, and the devices that the
firmware found. They are compared with the backend's expectations for
the board. The plan's decision record takes the facts, with any change
that they force to the board's platform description, before the
second sitting.

**The second sitting: the boundary on.** Three sessions: `anchor`,
then the two hostile-monitor images. Each run's records are compared
with the expected table, entry for entry; the hostile-monitor images'
counts with their declarations.

## Work packages

| WP | Delivers | Exit |
| --- | --- | --- |
| M11-B1 | **The tools.** The tree's recipe, the board as the backend's second platform, and D-3's checker on the board's trees (B-3). The firmware's build for the board, on the host and in the evaluator, and its FIT (B-1). The environment's maker. The card image's maker, the writing tool, and the read-back (B-4). The checker's form for a boot from a card (B-8). The harness's end of a run on a machine that halts (B-2). The session's tools: the readings' templates in the console tool, the session's driver, and their dry runs. The board's hostile-monitor declarations and the generator's rules for them (B-10) | B-10's tests pass |
| M11-B2 | **The addition** (B-2), under D-2's rules, with its tests | Its two tests pass under QEMU. The build for QEMU is unchanged, byte for byte |
| M11-B3 | **The gates** at one commit that holds M11-B1 and M11-B2: B-10's list, and the candidate's gates. The first sitting's card image, written to its card and read back | They pass. The firmware's and the image's SHA-256 are in the decision record |
| M11-B4 | **The first sitting**, after the rehearsal, on the responsible human's word. Then, with its facts, the second sitting's three firmware builds, each made twice and compared (B-1), and their card images, each written to a card and read back before its session (B-4) | It passes, or stops. Its facts are in the decision record, with each build's and each image's SHA-256. If the facts change the board's platform description, M11-B3's gates pass again at the commit that holds the change |
| M11-B5 | **The second sitting**, on his word for each session | Each run passes, or a finding is recorded first |
| M11-B6 | **The result.** The board's records, redacted as MVP 1.0's are; the ledger's rows for the board, with a method for a diagnostic board run; the claim page in the form of B-11; the evidence section; the result packet | M11-B's result is presented at one exact commit |

Code is written by coding sub-agents on a model that can be named,
and reviewed line by line by the owner session, as in M11-E. The
session's commands on the board are the tools', from templates; the
session improvises nothing.

## Soft limits (re-evaluation stops)

The M11 plan's counting rule, counted from M11-E's candidate (QB9).
The firmware addition stays inside the M11 plan's own limit.

| Lane | Soft limit |
| --- | --- |
| The addition | Inside the M11 plan's limit for the firmware additions (80 lines are left) |
| The addition's tests, and the board's build rules | 500 |
| The tree's recipe, the backend's second platform, the checker on the board's trees, and the hostile-monitor declarations with the generator's rules | 1,200 |
| The card's tools and the session's tools, with their dry runs | 3,000 |
| The checker's form for a boot from a card, the harness's end of a halting run, and the ledger tool's method | 1,200 |

A limit exceeded is a stop for re-evaluation of the limit, never a cut
to the work. Only the responsible human re-sets one.

## Stop conditions (each returns to the responsible human)

The MVP plan's stops, S3-E's (j), (p), and (q) among them, and the
M11 plan's stops 1 to 18 stand beside these.

- **B1.** Any board step that this addendum's sittings do not name.
- **B2.** A difference, in any range, between the two readings that
  bracket a session. In a boot from a card: a line that a flash was
  detected, or a line of a write to the NOR; or the vendor's line for
  the record's save without its line that no valid flash device was
  found. That last line is expected, and is no probe. A board that
  does not come back to its boot from the NOR.
- **B3.** S3-E's stop (q), whole: a card that differs from what was
  written when it is read back; a boot from a card outside a session;
  a boot that the session did not plan; U-Boot entering anything other
  than the MVP's images; a boot whose U-Boot prints that it resets the
  identity data, or a product name other than the board's. And the
  lines beside them that B-8's form refuses: a new MAC address, a bad
  environment, a partition table's error or fallback.
- **B4.** A card that the boot ROM or the SPL does not take: no SPL
  banner, or a boot from the NOR with the card in the slot.
- **B5.** In the first sitting: no firmware banner; fewer than
  fourteen PMP entries; a grain above 4 KiB; a privilege version below
  1.12; a reset device other than the addition's, or none; a hart
  count other than sixteen; a memory size other than the one that
  U-Boot printed in the sitting's boot from the NOR; U-Boot's device
  tree inside the MVP's extents; the root OpenSBI domain's table other
  than the backend's expectation; the monitor's first check failing;
  U-Boot or a guest failing in a way that the setup which the base
  leaves out explains (statement 2); any other capture that the form
  refuses.
- **B6.** In the second sitting: a tested attempt that has an effect
  (the M11 plan's stop 4: the counterexample is recorded first); a
  record that differs from its expected table; a hart that does not
  commit; a scenario's run that shows a count other than zero; a
  confined hart's record with the invalidate control set, or a test's
  report that the cache-block instruction did not trap; any other
  capture that the form refuses.
- **B7.** A need for M-mode code beyond B-2; a change to the monitor's
  source or to an image of the candidate's; a change under a path that
  the proofs' records bind, without the re-proof that D-11 asks.
- **B8.** A soft limit exceeded.
- **B9.** A row in a board image's declaration that names a device
  outside B-10's list.
- **B10.** A step that fails twice. The session does not try a third
  way.
- **B11.** Anything that S3-E's item 13 names: among them a `saveenv`
  in a session with a card, a card written on the board, anything
  staged over USB, and a write to the NOR by a step of the project's
  own.
- **B12.** A first session before the rehearsal has passed.

## Open questions and defaults

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| QB1 | The NOR in a session with a card (S3-E's Q62) | Untouched. Option B's rule is chosen, and met by the firmware's tree, which gives the vendor's U-Boot no flash device; no M-mode code; S3-D.6's step 4 stands as written | Option A as well, for one more session before the first, under the vendor's firmware: it would show the card's path alone, and so tell a fault of the card's path from one of the project's firmware; each of its boots writes the vendor's record. Or option B's own mechanism as well, which is M-mode code and needs the address named in the tree |
| QB2 | The images on the board | B-10's table: `two-guests` without the boundary; `anchor`; the hostile-monitor images for the second VS-domain hart and for the control hart | Fewer, or more: each further image is one more session |
| QB3 | The cards | A card for each image of a sitting, each written and read back before the sitting: three serve, the first sitting's being written again for the second. With fewer, a card is written again between two sessions, and the sitting is longer each time by a whole card's write and two read-backs | Only cards that never held another image: four, none written twice |
| QB4 | Who writes the card | The session, through an access rule for the one reader, which the responsible human installs with one command; after a dry run | The responsible human runs the writing command himself |
| QB5 | The reset device | One of the project's own, which only halts | The vendor's doorbell handling brought to the base, so that the real-time core resets the board |
| QB6 | Harts 8 to 15, and the mailbox, in the firmware's tree | The CPU nodes stay, and the board's backend parks the harts with harts 3 to 7; the mailbox and its clients are disabled | The eight CPU nodes removed; or the mailbox kept, with six regions inherited, five tries at cold boot, and the base's writes into the shared queues |
| QB7 | Smepmp on the board | Not tried: plain PMP only | A guarded read of the register in M-mode first, which is more M-mode code |
| QB8 | The witness (the M11 plan's Q20) | What M-mode prints, with its limit stated | A record that only M-mode could have made, designed first |
| QB9 | The soft limits | The table above, counted from M11-E's candidate | The M11 plan's lanes, continued |
| QB10 | A further independent review of this addendum | Those made before it was presented | Another, by a reviewer that the responsible human names |
| QB11 | The card's partition table | A protective MBR and a GPT whose 128 entries are all unused, made for the card's size, with its backup at the card's end | No table; or the vendor's three entries with other names |
| QB12 | Runs, and the compiler | Three runs of a scenario image and one of a hostile-monitor image, as built by GCC | One more session for each image as built by Clang; more runs |
| QB13 | When M11-B's work starts | After M11-E's result is accepted | The tools beside M11-E's gates, on a branch of their own |
| QB14 | The claim's form after M11-B | B-11's: the clause as it is, and a paragraph about the board | The M11 plan's form, which changes the clause's first words and so says of the board what only emulation shows; or no claim text for the board, its record cited in the evidence record alone |

## What acceptance would authorize

- M11-B1 to M11-B6, on a working branch from M11-E's accepted
  candidate, under the stops above.
- The M-mode addition of B-2, under D-2's rules, and no other.
- The two sittings and their four sessions, each session on the
  responsible human's own word for it, with him present, after the
  rehearsal has passed.
- The claim's words of B-11, used only if M11-B's result is accepted.

It would authorize no write to the NOR, by a step of the project's own
or by the vendor's code in a session with a card; neither of option
A's readings; nothing staged over USB; no change to the monitor's
source or to an image of the candidate's; no Smepmp on the board; no
board step outside the two sittings; nothing sent to another project;
and no push, merge, tag, or release step. Each commit on the public
line stays the responsible human's to sign off and push.

## Accepted lines that this addendum changes

| Where | Text | Now |
| --- | --- | --- |
| The M11 plan, D-15 | "Until then stop (j) stands, and no M11 step touches the board" | One paragraph is added that points here. D-15 stands as written until this addendum is accepted; then this page settles its points |
| The M11 plan, the status record | `mvp_m11_board=not-authorized;needs-the-inventory-the-amendment-and-an-addendum` | The line says "not authorized" only for as long as this addendum's commit is not signed, and one line is added for the addendum |
| The M11 plan, D-2 | "The binary's SHA-256 is pinned in the tool lock beside today's firmware pin, and every run checks it before the firmware is used" | It stands for the build for QEMU. A build for the board is made for one image, and is not in the lock: it is made twice and compared, its SHA-256 is recorded before its card image is made, and the card image's maker and the card's read-back check it before it is used (B-1) |
| The M11 plan, Q20 | "Left to the board addendum" | QB8 |
| The M11 plan, "Claim text", the paragraph "After M11-B" | "the clause's first words become 'In QEMU and on one SpacemiT K3 COM260 board, booted there from', followed by the words that the board addendum fixes for the firmware's source and its medium (D-15)" | B-11: the clause keeps its words, and a paragraph about the board follows it. Used only if M11-B's result is accepted |
| The M11 plan, the limit's second sentence | "PMP's behaviour is the emulator's, which has no cache" | With "Under emulation," before it, and the limit's addition of B-11. Used only if M11-B's result is accepted |
| The M11 plan, D-3 | "Every hart of the platform" in the descriptor | On the board, the descriptor's eight, and harts 8 to 15 parked by the backend as a property of the platform (B-3) |
| The MVP plan, S3-E.2, option B | Its rule, and its mechanism: "it clears the record's mark in memory before U-Boot runs" | S3-E's text is not changed. Option B is chosen. Its rule is met by item 12's tree, which is a narrowing, and its own mechanism is not used (B-5) |
| The MVP plan, S3-E's status record | `s3_revision_s3e_choice=not-made;…` | The choice as proposed here, made only if this addendum is accepted (S3-E.2 has this commit record it there) |
| S3-E's item 11 | The card's contents, its environment, and its sessions | Narrowed in three places (B-4): the whole card is written; the environment's flashing variables are removed; nothing is typed while a card is in |
| The capture checker's rule that a firmware banner marks a capture as QEMU's | Any capture | It stands for a boot from the NOR and under QEMU. A boot from a card has a form of its own (B-8) |

Not changed: S3-A.1's items 1 to 8; S3-E's items 9, 10, 12, and 13,
and S3-D.6's steps as they are written; stops (a) and (j) to (q); the
M11 plan's D-1, the rest of D-2, and D-4 to D-14, its stops, and its
limits; the
candidate's monitor, images, and gates; MVP 1.0's claim.

## Review record

Independent, read-only, automated reviews read the drafts of this
addendum before it was presented. Their findings and their disposition
are in its review packet, in the project's internal records.

## Status record

```text
mvp_m11_board_addendum=accepted-if-its-proposing-commit-is-on-the-public-main-with-the-responsible-human's-sign-off;otherwise-proposed
mvp_m11_board_addendum_basis=mvp-m11-plan.md-D-15;mvp-plan.md-Plan-revision-S3-E
mvp_m11_board_firmware=the-M11-base-and-series;one-addition-a-reset-device-that-halts;a-device-tree-built-in-for-each-image
mvp_m11_board_nor=no-boot-from-a-card-writes-or-probes-it;S3-E.2's-option-B-chosen;its-rule-met-by-the-firmware's-tree,-which-gives-U-Boot-no-flash-device;no-M-mode-code-for-it
mvp_m11_board_pmp=plain-PMP-only;count-grain-and-privilege-version-read-in-the-first-sitting
mvp_m11_board_witness=what-M-mode-prints;its-limit-stated
mvp_m11_board_sittings=1-the-project's-firmware-boundary-off-one-session;2-the-boundary-on-three-sessions;the-rehearsal-first
mvp_m11_board_work_packages=M11-B1..M11-B6
mvp_m11_board_stops=B1..B12
mvp_m11_board_open_questions=QB1-QB14-defaults
```
