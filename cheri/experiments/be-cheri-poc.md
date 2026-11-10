<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Experiment: Beryllium's MVP, CHERI-enabled (proof of concept)

## Result (2026-11-05)

On 2026-11-05 the responsible human decided: "we will do a cheri poc of the
Be code, i.e. Cheri enabled version, with TE etc. as normal". This is that
proof of concept, on CHERI v0.9.3 under emulation.

Beryllium's MVP at `d776f324` was changed so that its monitor is
CHERI-aware and its guests are CHERI Linux. Beryllium's own makefiles,
harness, and checkers build and judge it, adapted where CHERI changes what
they check. `d776f324` was the development tip when the work began; its
`mvp/src` is `6ff17c67`'s.

The work began as five commits on a local branch, `beryllium/cheri-poc`,
in a separate Beryllium clone. [`be-cheri-poc/`](be-cheri-poc/) holds
them as a frozen patch series, and `be-cheri-poc-run.sh` rebuilds and
reruns everything from a Beryllium checkout. At that stage nothing was
pushed or written to the canonical checkout. Later on 2026-11-05 the
responsible human decided to carry the work in Beryllium as the
long-lived branch `beryllium/cheri-platform`. Its seven-patch package,
these five commits and two more, is
[`../docs/import/cheri-platform/`](../docs/import/cheri-platform/).
A Beryllium owner session applied it, merged accepted M10, reran the
branch gate, and recorded the resulting branch at `5a5daad1` (tree
`90c95a01`) before the specifically authorized private-origin push.
Ongoing CHERI platform work is now Beryllium owner work on that branch;
[`../COLLAB.md`](../COLLAB.md) holds the exact creation record and claim
limits.

- **Every scenario runs with CHERI on and passes Beryllium's own
  judges**, for the GCC and the Clang monitor
  ([`be-cheri-poc-results.txt`](be-cheri-poc-results.txt)):
  - `two-guests`;
  - `te-poc`, the Type Enforcement policy: each denied access is injected
    into its guest as an access fault, which the guest observes;
  - `anchor`: the measured launch, the request and response digests, and
    the management calls;
  - the ten monitor variants, the four probes, `te-poc`'s two negatives,
    and `anchor`'s five: `BE_MVP_QEMU: PASS runs=48`;
  - M7's three shell sessions per toolchain, typed at a CHERI BusyBox
    shell in each guest: `BE_MVP_SESSIONS: PASS sessions=6`.
- **Beryllium's static checks pass too:**
  - the image check, Beryllium's checker of the monitor's binary, with
    CHERI rules added; it rejects each of its 127, 131, and 140 mutations
    per scenario;
  - the references (29 images per toolchain) and the reference check;
  - the port check, lint, and the policy negatives;
  - the guest self-test and all eleven host tests, with GCC and Clang in
    agreement;
  - the target check, the budgets, and the tool lock;
  - nine of the eleven tool self-tests.

  The CHERI guest build is reproducible: a second build gives the same
  bytes.
- **The monitor's code grows by 616 bytes**, from 50,384 to 51,000 bytes
  of text (GCC, `te-poc`; 1.2%):
  - the trap vector, 396 to 672 bytes;
  - the resume tail, 404 to 480;
  - the arming helper, 364 to 548;
  - the injection helper, 52 to 76.
- **The guest grows more:**
  - the kernel file, 2,063,556 to 3,264,512 bytes;
  - the init, 17,176 to 72,576, being purecap code against musl in
    place of nolibc;
  - BusyBox, 141,560 to 286,280.

  The kernel fits the monitor's limit of 3,510,272 bytes. It exceeds M7's
  Image budget of 3 MiB (3,145,728) by 118,784 bytes ("Findings").
- **Two toolchain defects were found, with their causes**: one in the
  CHERI QEMU and one in CHERI Alliance musl ("Findings"). The QEMU defect
  is why the shell sessions failed before. A two-line local change fixes
  it.

This is not a proof of anything, and not a design for Beryllium. It runs
under emulation only, on v0.9.3 rather than RVY, on a QEMU with two local
changes, and on the `plic` machine instead of `k3-like`. Its CHERI rules
were written by this repository's agent and have not been reviewed, and
several of Beryllium's checks are not adapted ("Gaps").

## What changed

The series makes 1,192 insertions and 193 deletions in 25 files.

**The monitor:** 6 files, +314 and -93, mostly `mvp/src/mvp-trap.S`. It
starts from the prototype fix of [`cheri-guest.md`](cheri-guest.md)
(`cheri-guest/monitor-fix.patch` and `monitor-sbi30.patch`, unchanged).

- **Turning CHERI on for guests:** `henvcfg.CRE` is set, and the resume
  tail requires STCE and CRE.
- **The trap vector** enters Capability Pointer Mode before any access.
  It saves every guest register whole, as a capability, and saves the
  guest's `ddc` before installing the monitor's own. The resume tail
  restores both.
- **Delegated CHERI faults:** `hedeleg` delegates cause 28, CHERI
  v0.9.3's CHERI fault. The monitor refuses at arming a hart that cannot
  delegate it.
- **The device tree** is passed to the guest as a capability in `ca1`.
- **The injection helper** moves `sepcc` to `vsepcc` and `vstvecc` to
  `sepcc` whole. A denial's access fault therefore reaches a CHERI guest's
  handler with its capabilities.
- **The arming helper** clears the capability frame with 33 straight-line
  stores in place of a loop, so that the image check can follow it.
- **One port rule** accepts SBI 3.0 firmware.

**The guests:** 13 files, +579 and -43. `mvp/tools/build-guest-cheri.sh`
builds every guest output as a CHERI program from the pinned CHERI
Alliance SDK and sources, with the same names and initramfs as Beryllium's
build:

- **The kernel** is CHERI Alliance Linux v7.1: a purecap kernel with the
  purecap user ABI. It is configured as Beryllium configures its v7.2,
  plus `guest/cheri-kernel.config`, and its exports are trimmed to the
  management module's six imports.
- **The init** is purecap, built against CHERI musl rather than nolibc.
  It reads the kernel's `ucontext` layout and expects release 7.1.0.
- **BusyBox** is CHERI Alliance BusyBox 1.36.1 with Beryllium's
  configuration.
- **The management module** takes a capability ioctl argument.
- **musl and compiler-rt** are built soft-float from the pinned sources.
- **The device trees** name `Zcherihybrid` and `Zcheripurecap`.

`guest/pins.txt` pins every output.

**The checks and harness:** 6 files, +299 and -57.

- **`tests/check-image.py`** has CHERI rules for the vector, the resume
  tail, and the helpers, and its mutations target them.
- **`tests/check-capture.py`** accepts `hedeleg`'s CHERI reading. It also
  matches a guest banner longer than the monitor's console line by its
  first piece.
- **`tests/run-qemu.sh` and `tests/session-typist.py`** take the
  firmware's SBI version as 3.0. They run `k3-like`'s runs on the `plic`
  machine under `BE_MVP_QEMU_K3_LIKE=plic`.
- **`tests/sbi-test.c`** follows the CHERI monitor's controls, with two
  more assertions.

## Findings

1. **Under a hypervisor, the CHERI QEMU turns a valid user pc invalid.**
   This finding is new. [`be-cheri-poc-vdso.txt`](be-cheri-poc-vdso.txt)
   holds the evidence.
   - **The symptom:** when the guest kernel returns from a trap taken in
     the vDSO, at `0x3f8c623530`, the pc comes back as
     `0xffffffff8c623530`, untagged.
   - **The cause:** the check that converts an invalid address on a
     capability write to `sepcc` (or `mepcc`, `vsepcc`, `mtvecc`,
     `stvecc`, or `ddc`) tests an Sv39 address against bit 37, not bit
     38. `topbit_for_address_mode()` returns a bit index, and
     `SignExtend64()` takes a width. The check reads the translation mode
     from `vsatp`, which only a hypervisor sets, so without one it never
     runs.
   - **The evidence:** the same kernel and binaries without the
     hypervisor return from the same fault correctly.
   - **The fix:** `build-qemu-vs-reset.sh --ia-fix` passes the width.
   - **Where else:** the CHERI Alliance QEMU's `main` (`937b306b`, the
     RVY line) has the same code, read but not run.
   - **What it explains:** before the fix, any return to the vDSO from a
     trap taken there failed. Examples are the page fault on a process's
     first signal return through the vDSO's trampoline, and its first
     `clock_gettime` through musl's vDSO path. That is why the shell
     sessions failed, and why the init carried two workarounds, which the
     last commit removes. It belongs in the Codasip follow-up.
2. **CHERI Alliance musl's `ucontext_t` disagrees with the kernel's.** This
   finding is new. musl puts `uc_mcontext` at offset `0xc0`, and the
   kernel at `0xb0`. So a purecap signal handler that reads registers
   through musl's type reads the slot before: its `REG_PC` is the
   kernel's `ra`.
   - musl intends a 112-byte `sigset_t` under CHERI, which would agree.
     But the guard in `include/alltypes.h.in` tests
     `__CHERI_PURE_CAPABILITY`, which the compiler does not define (it
     defines `__CHERI_PURE_CAPABILITY__`).
   - The init reads the kernel's layout instead. A static assertion stops
     the build if musl's layout changes.
3. **The SDK's purecap userland is hard-float.** Its musl and compiler-rt
   are built for `l64pc128d`, but Beryllium's guests have no FPU support:
   B6 turns the kernel's off. So BusyBox's shell took an illegal
   instruction in `setjmp`. The proof of concept builds both soft-float
   (`l64pc128`) from their pinned sources.
4. **Kernel exports cost a CHERI kernel more.** `anchor`'s management
   module needs loadable modules. With them, the exports add about
   530 KiB: the export table, and a capability relocation for each export.
   That makes a 3.64 MiB kernel, over the monitor's limit. Trimming the
   exports to the module's six imports gives 3,264,512 bytes. That is
   inside the monitor's limit but over M7's 3 MiB Image budget, which
   `guest-pin-check` enforces. The minimal guest of
   [`cheri-guest.md`](cheri-guest.md), without modules, was 2.95 MiB.
5. **A CHERI guest needs its CHERI faults delegated.** Before the last
   commit, the monitor accepted a hart that could not delegate cause 28,
   although the capture checker required it. On such a hart, a guest's
   first CHERI fault would end the domain. The monitor now refuses such a
   hart at arming, as it refuses other missing controls.
6. **Known from [`cheri-guest.md`](cheri-guest.md):**
   - CHERI Linux guests need CHERI-aware M-mode firmware, which today
     reports SBI 3.0;
   - CHERI must be named in each guest's device tree;
   - the device tree must be passed as a capability.

## Gaps

- **Machines:** QEMU 8.1 has no `svade` or `svadu` property and no
  `rva23s64` model. So the `k3-like`, `rva23`, and `no-sstc` runs were not
  made, and `k3-like`'s variants and probes ran on the `plic` machine.
- **Beryllium's checks that fail, and why:**
  - `guest-pin-check`: its fact checks describe Beryllium's non-CHERI
    guest: an `rv64imac` attribute, Beryllium's GCC, and M7's Image
    budget, which the CHERI kernel exceeds.
  - `capture-check`, the capture checker's self-test: 96 of its 300 cases
    fail. Its fixtures are non-CHERI captures, and the checker now
    expects CHERI values.
  - `run-tool-check`, the board tools' dry run: it starts from those
    fixtures, and the board is out of scope.
  - `claim-ledger-check`: Beryllium's claim ledger pins, by SHA-256, six
    files that the proof of concept changes, cited by eight claims. The
    claims are Beryllium's, about its MVP, so they are left alone.
  - `reference-boot` and `kernel-repro`: not adapted. They take their
    QEMU and firmware from Beryllium's tool lock, which a caller cannot
    override. By hand, the same kernel and initramfs boot to the shell
    natively on the CHERI QEMU.
  - `qemu-test` and `sessions`: these make targets take their QEMU and
    firmware from Beryllium's tool lock. `be-cheri-poc-run.sh` runs the
    same tools directly, with the CHERI QEMU, its firmware, and the
    `plic` override.
  - `evidence`, the bundle of every check's records: not made, since it
    needs every check above.
- **The image check's CHERI rules** were written by this repository's
  agent and have not been reviewed. The untagging stores in the merge's
  loop are not proved.
- **Capabilities still cross the channel page**
  ([`cheri-guest.md`](cheri-guest.md)). This QEMU reports no `PTE.CW`
  support, so nothing in the G-stage can stop the flow.
- **Not studied:** performance, timing, and interactive use beyond the
  typed sessions.
- **Not shown:** anything about hardware. The K3 has no CHERI, and
  whether Codasip's cores will have the hypervisor extension is an open
  question.

## Method

**The clone and the branch.** The clone is a `git clone --no-checkout` of
the Beryllium checkout, with its push URL disabled. The branch
`beryllium/cheri-poc` starts at `d776f324`, and its five commits are:

1. **The monitor and the CHERI guests:** the prototype fix, the injection
   helper's capability moves, and the CHERI guest build. It also calls
   `clock_gettime` by system call, which turned out to be a workaround
   for the QEMU defect.
2. **The init's signal path:** the kernel's `ucontext` layout, and a
   second workaround for the QEMU defect, whose cause was not yet known.
3. **Beryllium's checkers judge the CHERI build:** the image check's and
   the capture checker's CHERI rules.
4. **`k3-like`'s runs on the `plic` machine.**
5. **A soft-float userland and M7's shell sessions:**
   - the workarounds removed once the QEMU defect's cause was found;
   - the typist on the `plic` machine with SBI 3.0;
   - cause 28 required at arming.

**The runs** use the CHERI QEMU with both local changes, eight harts, and
the CHERI Alliance SDK's purecap OpenSBI, as Beryllium's harness boots
them. A boot whose firmware started on a domain hart is refused by the
monitor and made again; the harness counts these.

**Finding the QEMU defect took three steps:**

1. The guest kernel's report and QEMU's trap log under the monitor
   showed the pc's address and bounds moved together, with no trap to
   the monitor between.
2. The same kernel and initramfs ran without the hypervisor, forced to
   Sv39 so that the vDSO sat in the same range. There the same fault
   returned correctly.
3. Reading QEMU's capability CSR writes found the conversion and its bit
   index, and arithmetic reproduced all three addresses observed.

## Reproduce

1. **Build the stack** as in [`README.md`](README.md), "Reproduce", steps
   1 and 2: the CHERI Alliance SDK and sources under `toolchains/`.
2. **`experiments/build-qemu-vs-reset.sh --ia-fix`** builds the QEMU with
   both local changes into `build/qemu-ia-fix/`, in under a minute here.
3. **`experiments/be-cheri-poc-run.sh BERYLLIUM_CHECKOUT`** runs
   everything. The checkout must contain `d776f324`, and the host needs
   the tools that Beryllium's own build needs, plus `cmake` and `ninja`.
   - The checkout is only read. The script clones it under
     `build/be-cheri-poc/`, applies the series, and checks the tree. It
     then builds, checks, and runs everything as above.
   - It rewrites `experiments/be-cheri-poc-results.txt` and ends with
     `BE_CHERI_POC_RUN: PASS`. It takes 10 to 12 minutes here, the CHERI
     guest's build included.

For interactive work, use the clone's branch. Its `mvp/Makefile` takes
the CHERI inputs as command-line variables: `CHERI_SDK`,
`CHERI_LINUX_SRC` and `CHERI_LINUX_COMMIT`, and the same pairs for
BusyBox, musl, and LLVM. `be-cheri-poc-run.sh` shows them.

## Notes

- **The arming helper's straight-line stores:** the image check drops its
  tracked registers at every branch target. A loop that cleared the
  capability frame therefore lost the helper's arguments, and the check
  refused the helper.
- **The console banner:** the monitor's console line is 256 bytes. The
  CHERI LLVM's version strings make the guest kernel's banner longer, so
  the banner arrives in pieces, and the capture checker matches its first
  piece.
- **`hedeleg` and `henvcfg` on this QEMU** read back everything the
  monitor writes: `0x1000b15d` and `0x8000000010000000`.
- **Both init workarounds are in the series' history:** reading the vDSO
  page before arming the handler, and calling `clock_gettime` by system
  call. Commit 5 removes them.
- **The series names only public sources**, the CHERI Alliance
  repositories and SDK, and it was scanned for local paths.
