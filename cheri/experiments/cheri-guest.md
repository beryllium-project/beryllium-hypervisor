<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Experiment: CHERI-enabled guests under the MVP monitor

## Result (2026-11-04)

The sidebar's section "What CHERI-enabled guests would change" was a
prediction from the specification. This experiment measured it on CHERI
v0.9.3, under emulation. A small test guest that uses CHERI ran as both
domains of Beryllium's `te-poc` scenario, under the MVP monitor at
`6ff17c67`: first unchanged, then with two prototype changes made only in
this repository. Then a minimal CHERI Linux guest ran as both domains of
`two-guests`. Every one of the runs' 95 predictions held
(`cheri-guest-results.txt`).

- **Unchanged, the monitor keeps guests CHERI-off.** Its `henvcfg` write
  leaves CRE clear, so a guest's first CHERI instruction is an illegal
  instruction, which the guest takes itself.
- **Turning CHERI on for guests, and changing nothing else, is unsafe.**
  `cheri-guest/monitor-cre.patch` sets `henvcfg.CRE` and the checks that
  read it back: 11 lines added and 6 removed, in four files. With it:
  - **Guest registers lose their capabilities.** A capability that a
    guest holds in a register comes back untagged from any trap the
    monitor serves; here, one SBI call. The monitor saves and restores
    guest registers as integers.
  - **A CHERI fault in a guest ends the run.** The fault is not
    delegated, so it reaches the monitor, which fails the domain
    (`BE_MVP:FAIL exception`, cause `0x1c`).
  - **One guest can write into another guest's memory.** `ddc` is one
    register for every mode, and the monitor's trap vector stores
    through it before anything else. The writer domain bounded `ddc` to
    one page of the reader domain's memory, by host-physical address. It
    set its stack pointer into that page and made one SBI call.
    1. The vector's first store faulted on the bound.
    2. The fault re-entered the vector, which then took the guest's stack
       pointer as its own.
    3. Its next two stores wrote the writer's two chosen words into the
       reader's memory, where the reader read them.
    4. The writer's hart then halted.

    This is a failure of isolation between domains, not only a lost tag.
    The same path reaches any address that HS-mode may access physically,
    the monitor's own memory included; that is an inference, not
    tested.
  - **Capabilities cross the channel page.** The writer stored a
    capability to its own 64-byte object in the channel page. It arrived
    tagged at the reader, with its bounds and permissions. The reader
    loaded through it and got its own memory at that address, not the
    writer's. Nothing in the G-stage stopped the flow.
- **A prototype fix closes the first three.**
  `cheri-guest/monitor-fix.patch` makes four changes:
  - the trap vector enters Capability Pointer Mode before any access;
  - it saves and restores every guest register as a capability;
  - it switches `ddc` to the monitor's own on every trap, and back on
    return;
  - `hedeleg` also delegates cause 28, CHERI v0.9.3's CHERI fault.

  With it, the register keeps its tag, and each guest takes its own CHERI
  fault and recovers. The `ddc` attack fails: the monitor returns to the
  writer, and the reader's page stays zero. The channel flow is unchanged,
  because closing it needs a G-stage capability control that v0.9.3 does
  not have.
- **Beryllium's own Linux guests still run under the fix.** They use no
  CHERI. In `two-guests`, both pass. In `te-poc`, both pass, and all
  three declared denials are delivered and observed, as in the stock run.
  In `anchor`, the host passes and terminates the protected domain as
  designed, with the same response digests and termination digest as the
  stock run.
- **A minimal CHERI Linux guest fits the monitor's guest limits.**
  `build-cheri-linux.sh` configures the pinned CHERI Alliance Linux 7.1 as
  Beryllium configures its own guest kernel (tinyconfig, then Beryllium's
  B6 guest fragment) and adds only CHERI (`cheri-linux/cheri-kernel.config`).
  That is a purecap kernel with the purecap user ABI, the only CHERI mode
  that the RISC-V port offers. Its initramfs holds a purecap `/init`
  (`cheri-linux/init.c`). The kernel file is 2.95 MiB (limit 3.35 MiB),
  and its in-memory size is 3.18 MiB (limit 8 MiB). Beryllium's own guest
  is 1.97 and 2.17 MiB (`cheri-linux-build.txt`). No limit needs to change
  for it.
- **It boots under the fix only with three more changes:**
  1. **The guest device tree must name CHERI.** The kernel enables CHERI
     for user space only when its device tree lists `zcherihybrid` or
     `zcheripurecap`. Beryllium's guest device trees list neither, so these
     runs add both.
  2. **The device tree must arrive as a capability.** A CHERI kernel takes
     the tree's address as a capability in `ca1`, as CHERI firmware passes
     it, but the monitor passes an integer. Under the CRE-only monitor, the
     kernel's first read of the tree takes a CHERI fault. The monitor does
     not delegate it, so the run ends there, before the guest prints
     anything (`BE_MVP:FAIL exception`, cause `0x1c`, at the tree's
     address plus 4). The fix now passes a capability for the tree's
     4 KiB, made from the monitor's `ddc`.
  3. **M-mode firmware must be CHERI-aware.** `ddc` is one register for
     every mode, M-mode included, and the kernel keeps it null.
     Beryllium's OpenSBI v1.6 saves registers on M-mode trap entry with
     integer stores, which go through `ddc`. The monitor's IPI probe is an
     M-mode interrupt. When a hart takes it inside the guest, the first
     save faults, and the fault enters the same save again, without end.
     In the committed run, 3 of the 6 domain boots on OpenSBI v1.6
     stopped there: gdb read `mcause` `0x1c`, and `mepc` at that store.
     Over the six runs whose results were kept tonight (under `build/`,
     not committed), 23 of 34 did. The rest completed. That fits the probe
     arriving while the hart was in the monitor, whose `ddc` is valid, but
     this is an inference. The CHERI Alliance SDK's purecap OpenSBI saves
     through its own capabilities. With it, both domains booted in every
     run, and each hart answered the IPI probe from inside its guest.
- **That firmware reports SBI 3.0, which the monitor refuses.** Beryllium's
  R3 header pins SBI 3.0. The B2 port that the MVP builds on lowers it to
  2.0, for OpenSBI v1.6, and the monitor requires exactly that version.
  `cheri-guest/monitor-sbi30.patch` adds one rule to the MVP's port script,
  10 lines, which restores 3.0. With it and the CHERI firmware,
  Beryllium's own Linux guests still pass under the fix in all three
  scenarios, as on OpenSBI v1.6.
- **CHERI works in the Linux guest from kernel to user space.** Under the
  fix, each kernel reports CHERI support, and `/init` runs as purecap code.
  Its stack buffer and `argv` arrive as tagged capabilities bounded to
  48 bytes each. A child's store one byte past that buffer is delivered
  as `SIGSEGV`. Both domains power off, and the run completes. Under the
  unchanged monitor, the kernel's first CHERI instruction is illegal. The
  guest has not yet set its trap vector, so the run ends with a guest
  page fault at address 0.
- **What the fix costs.**
  - **Code.** 249 lines added and 87 removed, in five files, almost all
    in the trap file. In instructions, the vector grows from 99 to 168,
    the resume tail from 101 to 120, the arm helper from 91 to 109, and
    hart 0's budget helper from 6 to 11. Of the added lines, 84 are CHERI
    instructions (37 `SC`, 35 `LC`, 8 `MODESW`, 3 `SCADDR`, and 1
    `SCBNDSR`), written as encodings because Beryllium's assemblers lack
    the extension, and 5 more read or write `ddc`. The device tree's
    capability is 6 of the arm helper's instructions.
  - **Memory.** Each hart's saved page holds 896 bytes of exit state
    instead of 360. The extra 536 bytes are 31 capability registers and
    the guest's `ddc` at 16 bytes each, the monitor's `ddc`, and 8 bytes
    of alignment.
  - **Assurance.** Beryllium's image check (`mvp/tests/check-image.py`)
    refuses the fixed monitor at its first finding: "be_mvp_trap_vector
    writes unlisted CSR 0x416", which is `ddc`. The check also requires
    the vector's first instruction to be the `sscratch` exchange, and fixes
    where it stores each register; the fix changes both. Adopting it means
    revising that check, and the plan text the check encodes, with the
    code. So Beryllium's harness and checker did not judge these runs.
  - **Firmware.** CHERI v0.9.3 enables CHERI in S-mode only when
    `mseccfg.CRE` and `menvcfg.CRE` are both set, and a CHERI-enabled
    guest also needs firmware that delegates cause 28 to S-mode. The
    CHERI Alliance's OpenSBI (Codasip's branch, `cheri-alliance-opensbi`)
    does all three. Beryllium's OpenSBI v1.6 does none, so these
    runs used it with those three changes (`build-opensbi-cre.sh`).
    Without the delegation, OpenSBI v1.6 hands a guest's CHERI fault back
    to the monitor's vector, which the step-1 monitor then entered over
    and over: 4.3 million faults at the vector's first store in 25
    seconds, on both domain harts, with nothing printed
    (`cheri-guest-firmware-hang.txt`). Those faults are consistent with
    the vector being entered in the guest's Capability Pointer Mode, which
    is an inference. A guest that keeps `ddc` null, as CHERI Linux does,
    also needs M-mode firmware whose trap entry does not store through
    `ddc`; OpenSBI v1.6's does, with or without those changes. The CHERI
    Alliance SDK's OpenSBI meets all four needs, at the cost of the SBI
    3.0 port rule.
  - **Timing.** Not measured. The fix's resume tail compares all 31
    registers on every exit, which a fix with the dispatch's knowledge of
    the registers it writes would avoid.

What this does not cover:

- RVY (v0.9.10), which numbers the CHERI causes and `hedeleg` bits
  differently (the sidebar's bits 32 to 36), or hardware.
- CHERI Linux guests beyond the minimal one. The monitor bounds its guest
  in three ways, all budgets that Beryllium's K3 bring-up plan B6 set and
  its MVP plan M0 kept (`planning/k3-b6-plan.md` and
  `planning/mvp-m0-plan.md`, "Budgets"); none is a hardware limit:
  - the staged boot image, monitor and both device trees included, is at
    most 4 MiB, which leaves the kernel file 3.35 MiB;
  - the kernel's in-memory size is at most 8 MiB;
  - each guest's RAM window is 64 MiB.

  The minimal guest has 349 built-in options, no SMP or networking, and
  runs only its own `/init`. Codasip's CHERI Linux kernel, as built for
  the first experiment, is Linux 7.1 with a broad configuration (1,736
  built-in options). It is 59 MiB on disk and 71 MiB in memory, more than
  a whole window. Nothing between the two was built.
- CPUs with Zcheripte, whose page-table checks this CPU had off.
- How a fault the monitor injects carries `vsepcc`'s capability. The
  monitor accepts a denial only from guest user mode, and the test guest
  runs in guest supervisor mode. The Linux guests' denials above exercise
  the path without CHERI.
- The fix's correctness beyond these tests. It is a prototype in this
  repository, not reviewed against Beryllium's plans, and not a proof.
- A device-tree capability with fewer permissions. The fix's keeps every
  permission of the monitor's `ddc`, bounded to the tree's 4 KiB; whether
  the kernel accepts a read-only one was not tested.
- The CHERI firmware's own correctness. These runs use the SDK's build of
  the pinned OpenSBI as it is, not reviewed; the monitor's firmware
  checks pass with it once it accepts SBI 3.0.
- The emulator's own correctness. It needed the local reset fix that the
  monitor run describes (`monitor-run.md`).

The evidence:

- `cheri-guest-results.txt`: the pins, both firmwares, the guest images
  and the three patches with their digests, each run's monitor and guest
  lines, every prediction and whether it held, the image check's finding,
  and the code sizes.
- `cheri-guest/`: the test guest's source (`head.S`, `guest.c`,
  `guest.ld`) and the three patches against Beryllium at `6ff17c67`: two
  against `mvp/src`, and `monitor-sbi30.patch` against
  `mvp/tools/port.py`.
- `cheri-linux/` and `cheri-linux-build.txt`: the CHERI Linux guest's
  `/init` and kernel fragment, and its build's pins, configuration and
  sizes against the limits.
- `cheri-guest-firmware-hang.txt`: the one diagnostic run behind the
  firmware note above, with its inputs' digests and the trap counts.

## Method

- **The test guest** (`cheri-guest/`, built by `build-cheri-guest.sh` with
  the pinned CHERI Alliance LLVM, `cheri-alliance-llvm`) carries a Linux
  Image header that Beryllium's payload check accepts. One program serves
  both domains; it reads its role from the `be.role=` boot argument in its
  device tree. It prints through SBI DBCN and ends with an SBI SRST
  shutdown, which stops only its own domain. It waits two seconds before
  that shutdown: the monitor requires each domain to answer its IPI probe,
  sent a few milliseconds after entry, before it shuts down. One early run,
  without the wait, failed for that reason (`BE_MVP:FAIL ipi`). It is built
  three times, so that a test that may end its domain has an image of its
  own:
  - `basic`: whether CHERI is available, a capability in `s1` across one
    SBI call, and the channel test;
  - `fault`: a load through a capability bounded to 16 bytes, at offset
    32;
  - `ddc`: the writer's `ddc` probe, while the reader watches the target
    page.
- **The monitor** is `beryllium-integration` (`6ff17c67`), exported with
  `git archive` and checked against its pinned digest. Its guest outputs
  are seeded from the Beryllium checkout as in `monitor-run.sh`, and the
  test guest replaces the guest `Image`. Beryllium's own Makefile builds the
  GCC `te-poc` boot image. Beryllium's monitor code is unchanged at its
  development tip on 2026-11-04 evening, `d776f324`.
- **The patches** are made against `mvp/` at `6ff17c67`: the CRE and fix
  patches against `mvp/src`, and `monitor-sbi30.patch` against
  `mvp/tools/port.py`. The fix's vector:
  1. switches to Capability Pointer Mode (`MODESW.CAP`), exchanges `csp`
     with `sscratchc` whole, and spills `ct0` and `ct1` below the trusted
     top;
  2. checks the top as before;
  3. stores every guest capability register, the guest's `csp`, and the
     guest's `ddc` into a capability frame after the exit record;
  4. installs the monitor's `ddc`;
  5. writes the integer record that Beryllium's C code reads, from the
     frame;
  6. returns to Integer Pointer Mode.

  The resume tail does the checks as before, then:
  1. for each register, keeps the guest's capability unless the dispatch
     changed the register, in which case it returns the new integer,
     untagged;
  2. restores the guest's `ddc` and every register in Capability Pointer
     Mode;
  3. executes `SRET`.

  The arm helper makes `sscratchc` a capability for the trusted top and
  stores the monitor's `ddc`, which is also the guest's first `ddc`. It
  also puts a capability for the device tree, the monitor's `ddc` with
  its address set to the tree's and bounded to its 4 KiB (`SCADDR`,
  `SCBNDSR`), in `ca1`'s slot, which the resume tail keeps because `a1`
  holds the same address. Hart 0's budget helper makes its `sscratchc` a
  capability too.
- **The runs** (`cheri-guest-run.sh`) boot each image on the pinned QEMU
  8.1 with the reset fix, with the CRE firmware: `virt`,
  `-cpu rv64,h=true`, eight harts, as Beryllium's harness boots its `plic`
  machine. A boot whose firmware started on a domain hart is refused by
  the monitor and made again, as in Beryllium's harness. Each run is
  checked against predictions written in the script before the runs.
  Beryllium's Linux guests then boot under the fix the same way.
- **The CHERI Linux guest** (`build-cheri-linux.sh`) merges tinyconfig,
  Beryllium's B6 guest fragment (read from the checkout at the pin) and
  `cheri-linux/cheri-kernel.config` with the kernel's `merge_config.sh`,
  and checks that every value the fragments set is in the final
  configuration. It builds out of tree with the pinned LLVM, with a fixed
  builder, host and timestamp, so two builds give the same `Image`.
  `/init` is a static purecap program, linked against the CHERI Alliance
  musl. The script compares the `Image`'s sizes with the limits in
  Beryllium's `mvp/src/mvp-layout.h`.
- **Its runs** use `two-guests`, with the CHERI kernel as the guest
  `Image` and both guest device trees remade, at the required 4 KiB,
  with the two CHERI extension names. Each monitor variant runs with
  `monitor-sbi30.patch` on the SDK's CHERI OpenSBI. The fix then runs
  three times on OpenSBI v1.6, with QEMU's gdb server: 20 seconds after
  both domains are entered, gdb reads each domain hart's trap registers.
  The prediction there, for each domain, is that it either shut down or
  stopped at OpenSBI v1.6's first register save (`mcause` `0x1c`, `mepc`
  at `_trap_handler_hyp` plus 4); which one varies from run to run. Last,
  Beryllium's own Linux guests run under the fix with
  `monitor-sbi30.patch` on the CHERI OpenSBI.

## Reproduce

1. `experiments/build-qemu-vs-reset.sh` and
   `experiments/build-opensbi-cre.sh`, if the monitor run has not run
   them. The CHERI OpenSBI comes with the CHERI Alliance SDK that the
   first experiment's toolchain build made, under
   `toolchains/cheri/output/cheri-alliance-sdk/opensbi/`.
2. `experiments/build-cheri-guest.sh`.
3. `experiments/build-cheri-linux.sh BERYLLIUM_CHECKOUT`. It takes under
   a minute here, and rewrites `cheri-linux-build.txt`.
4. `experiments/cheri-guest-run.sh BERYLLIUM_CHECKOUT`. It takes about
   four minutes, rewrites `cheri-guest-results.txt`, and ends with
   `BE_CHERI_GUEST_RUN: every prediction holds`. With the CHERI Linux
   runs, it passed three times in a row on 2026-11-04.

The checkout's `build/mvp/guest` must hold Beryllium's pinned guest
outputs, as for the monitor run; the script refuses to rebuild Linux.

## Notes

- **The test guest's loads through a capability run in Capability Pointer
  Mode.** In hybrid code, the CHERI Alliance LLVM compiles a load through
  a `__capability` pointer to `ld.cap` (opcode `0x5b`), which this QEMU's
  v0.9.3 target treats as an illegal instruction. The test guest's first
  run met this, and the guest now switches mode for such loads.
- **In v0.9.3, cause 28 is the only CHERI cause that can be delegated.**
  This QEMU's v0.9.3 target reports capability page faults as ordinary
  page faults, so `hedeleg` gains only bit 28.
- **The `mseccfg.CRE` correction.** This experiment found that the
  monitor run's CRE firmware had left CHERI off: it set `menvcfg.CRE`
  alone. `monitor-run.md` records the correction and the reruns.
- **The CHERI kernel needs frame pointers.** The CHERI port's stack
  walker without them does not compile, so `cheri-kernel.config` sets
  `CONFIG_FRAME_POINTER`, as Codasip's own configurations do.
- **`/init` needs the SDK's bounded-argument ABI features**, which its
  musl was built with and the first experiment's tests used. Without
  them, `printf` reads its arguments wrongly and faults.
- **The guest uses no floating point.** Beryllium's B6 fragment turns the
  kernel's FPU support off, so `/init` avoids floating point too.
