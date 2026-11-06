<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Sidebar: CHERI-RISC-V and the MVP's mechanisms

## Status and scope

Non-authorizing future research, like every `planning/sidebar-*.md` page.
It selects nothing: CHERI remains the MVP 3.0 research track (`mvp-plan.md`,
Plan revision S3-C), and Type Enforcement remains the policy specification.
It summarizes the beryllium-cheri investigation, a separate repository
(local, not yet published), at commit `2c0689d` and, for the monitor run,
`4cf40e3`:

- a design-impact table of the RISC-V CHERI specification against MVP 1.0's
  mechanisms, with questions for CHERITech;
- a compile-and-test of the two M8 leaves;
- a run of the monitor itself, unchanged, on an emulated CHERI hart with
  the hypervisor extension.

That research was produced with AI assistance and checked against its cited
sources. An AI review then corrected it (the dossier's section 8).

The specification read is `riscv/riscv-cheri` v0.9.10.1-ar20261013,
"Stable", in architecture review, and not ratified. Its hypervisor chapter
is experimental and outside the first ratification package (riscv-cheri
#802). Every statement here is tied to that version and expires with it.

## Fit today

On an RVY hart with Zyhybrid, with firmware handing S-mode root PCC/DDC,
MVP 1.0 runs every guest with CHERI off and needs no change. This is read
from the specification and the source. It has not been run on RVY; its
v0.9.3 form has, under emulation (What was tested).

- The STCE-only `henvcfg` write leaves `henvcfg.Y` at its reset value 0, so
  guests run with CHERI disabled. Without Zyhybrid, `henvcfg.Y` reads one,
  the readback check fails, and the hart does not arm.
- The G-stage builder writes the reserved PTE field as zero, as the
  specification requires; it defines no capability control in G-stage PTEs.
- The management SBI ABI and the rings carry no pointers.
- The denial decision applies unchanged to capability accesses. One that
  misses the G-stage raises the ordinary guest-page fault, with `htval` set
  and `htinst` zero.

## What CHERI-enabled guests would change

- **The trap vector and the exit record.** Guest registers become
  capabilities with tags. `ddc` is one CSR shared by every mode, so the
  vector would have to:
  - enter in Capability Pointer Mode;
  - switch `ddc` on every trap;
  - save and restore capabilities;
  - inject faults by moving `sepc` and `vsepc` as capabilities.

  The exit record's register area roughly doubles. No proof covers the
  MVP's vector today, so this is new, unproved code.
- **Delegation and firmware.** This needs `hedeleg` bits 32–36, plus
  firmware that sets `menvcfg.Y` and delegates CHERI causes to HS. The
  CHERI Alliance's OpenSBI does this only for v0.9.3.
- **Channel pages.** Nothing in the G-stage controls the flow of
  capabilities. Two CHERI-enabled guests could therefore pass valid
  capabilities through a channel page: an authority flow that the security
  model's analysis A6 does not model.
  - Such a capability reaches only addresses in the reader's own
    translation, so it does not widen any domain's G-stage reach. What it
    breaks is capability provenance inside the reader.
  - Today the only levers are `henvcfg.Y` = 0 on one end, or platform
    Tag-Strip memory. The task group lists G-stage capability control as
    future work (riscv-cheri #1178).

A purecap build of the monitor itself would also need start-up code that
derives capabilities from firmware's roots. Wherever the monitor now casts
integers to pointers, it would need pointers derived from capabilities
instead: hart pages, ring views, console copies, and image placement.

## What was tested

At commit `6fbcc3d1`, the two source files that hold M8's leaves,
`mvp/src/mvp-sbi.c` and `mvp/src/mvp-ring.c`, compile unchanged as purecap
CHERI-RISC-V v0.9.3 code with the CHERI Alliance LLVM. They were compiled
under Beryllium's recorded flags, with only `-march`/`-mabi` changed, and
produced no warnings or errors, including with the 11 CHERI warning groups
that compiler accepts.

The host tests `deny-test` and `ring-test`, built unchanged as static
purecap Linux programs, pass in user mode on CHERI Linux under QEMU
`codasip-latest`, CPU model `codasip-x730-lux`, which has no hypervisor
extension. Both reach Beryllium's pinned counts and give the same output as
the host build.

That covers two source files and two tests, for v0.9.3 under emulation. It
says nothing about RVY, the hypervisor extension, the leaves' callers, the
trap vector, or hardware. Read with the sections above, it places the
porting cost in the callers, the start-up code, and the vector, not in the
two leaves.

Then the monitor itself ran (2026-11-04), at commit `55047781`, the
development tip until the M9 and M8 lines were integrated. Its boot images
(`two-guests`, `te-poc`, and `anchor`, GCC and Clang, byte-identical to
M7's record) ran unchanged under Beryllium's own harness and checker on
its `plic` machine, on the same QEMU's CHERI v0.9.3 hart with the
hypervisor extension on. Every scenario passes, including with firmware
that turns CHERI on in HS-mode: the monitor's `henvcfg` write keeps the
guests CHERI-off. The same runs pass at `6ff17c67`, the development tip
after that integration. The emulator showed two defects. At its pinned
commit, `008944fe`, it resets `vstvecc` and `vsepcc` to untagged values
instead of the infinite capability the CHERI CSR tables require, and no
guest boots until that is fixed. And in up to about one run in a hundred
it leaves an idle guest halted in `wfi` with its timer interrupt pending
and enabled, which the specification says must wake it. This is "Fit
today" in its v0.9.3 form, under emulation; it says nothing about RVY or
hardware.

## Questions for CHERITech

1. G-stage capability control (riscv-cheri #1178): is it planned for the
   first RVY hypervisor specification? With which PTE bits, and what cause
   and `htval` for a denial?
2. For a hybrid HS-mode monitor hosting CHERI-enabled guests, is a `ddc`
   switch at every trap entry and return the intended pattern, or is a VS
   copy of `ddc` planned?
3. Is any application-class CHERI-RISC-V core with the H extension
   available or planned?
4. When will RVY with H be specified (riscv-cheri #802), and is an RVY Sail
   model with H planned?
5. What RVY software is planned for hypervisor work: firmware, a Linux user
   space, the compiler, and an emulator with RVY and H?
6. Will the RISC-V IOMMU or IOPMP gain per-device tag control, or will tag
   control for DMA stay a static platform attribute?

## Sources

- beryllium-cheri at `2c0689d`:
  - `docs/dossier/cheri-rvy-x-beryllium-mvp-2026-11-02.md` (its section 8
    governs);
  - `docs/reviews/2026-11-03-dossier-review.md`;
  - `experiments/README.md`, with its evidence and pins.
- beryllium-cheri at `4cf40e3`: `experiments/monitor-run.md`, with its
  evidence and pins.
- The RISC-V CHERI specification v0.9.10.1-ar20261013 (tag commit
  `ad5ad9dd`):
  <https://github.com/riscv/riscv-cheri/releases/tag/v0.9.10.1-ar20261013>;
  issues <https://github.com/riscv/riscv-cheri/issues/802> and
  <https://github.com/riscv/riscv-cheri/issues/1178>.
- `cheri-alignment.md` holds Beryllium's standing CHERI position. The
  commit that adds this page also corrects that page's two stale statements
  about Sail.
