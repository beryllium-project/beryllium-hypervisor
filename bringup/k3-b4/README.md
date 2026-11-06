<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B4: the accepted R6 and R7 checks on the K3 images

B4 re-derives two accepted QEMU-stage assurance packages for the K3 port of
accepted R5 that [B2](../k3-b2/README.md) builds. These are the same images
that ran on the COM260 in B2 and B3:

- [`r6/`](r6/README.md): the accepted R6 adversarial catalogue
  (`7ba3649f`). Its 46 single-defect fixtures and one control are each
  run at their declared layer on the K3 port.
- [`r7/`](r7/README.md): the accepted R7 bounded exact-byte proof
  (`9bf22913`), re-run over the extracted bytes of B2's two K3 images.

Accepted R6 and R7 cover the QEMU R5 images. B2's port changes four
things:

- it rebases the image to `0x1_0200_0000`;
- it pins SBI 2.0;
- it changes the R1 identity;
- it makes `be_reset` call B1's interrupt quiesce first.

So the image bytes differ, the accepted results do not transfer, and B4
measures them again.

B4 was authorized on 2026-10-06 by "ok, as I will be asleep soon, let's go
with R6 and R7 overnight, in parallel if feasible". It is host, QEMU, and
Rocq work only; nothing runs on the board. Nothing outside `bringup/k3-b4/`
changes. Generated output goes only to `build/k3-b4/` and to B2's
`build/k3-b2/`.

**Status:** both halves pass. Exact result commit `135b1d3a` is
responsible-human accepted as of 2026-10-07; see the
[review and acceptance record](../../planning/k3-b4-result-review-summary.md).

| Half | Gate result | Time on this workstation |
| --- | --- | --- |
| R6 | `BE_K3_B4_R6_CHECK: PASS matched=47/47 images=32 qemu_runs=64 layer_shifts=0 findings=0` | about 12 min |
| R7 | `BE_B4_R7_CHECK: PASS` with `proof=PASS`: 22 symbols, 1,420 words, 144 targets, 32 sections, 9 modules, 135 Theorem and 4 Lemma declarations | about 2 min |

Every applicable count equals the accepted package's.

## Method

Both halves follow B2's method:

- Every consumed accepted file is read with `git show` from its accepted
  commit, not from the working tree, pinned by SHA-256, and copied under
  `build/`. Only files B4 uses where they live, such as B2's build files,
  R6's host driver, and the R7 tool locks, are pinned in place.
- Copies change only by counted, documented rules, which each half's README
  lists.
- The only images are B2's, built by B2's Makefile, which requires B2's
  accepted flat-image hashes: GCC `9c145f00…a08c79`, Clang
  `47be17e3…c54fe`.
- The tools are this workstation's, unpinned, as in B2:
  - the accepted R6 and R7 tool locks pin node v22.22.2, GCC 16.1.1, and
    binutils 2.46; this host has node v22.23.1, GCC 16.2.1, and binutils
    2.46.1;
  - Rocq 9.2 matches the accepted digest;
  - no accepted launcher, tool lock, or acceptance-pin checker runs.

## Findings

- **R7: the accepted extractor truncates addresses.** It formats
  addresses with `>>> 0`, which truncates any address at or above 2^32,
  as every K3 address is. The objdump cross-check and the Rocq pins refuse
  the truncated values. The K3 copy uses an exact formatter. B4 still
  derives that copy from the accepted bytes, and the accepted extractor is
  fixed separately; see [the R7 findings](r7/README.md#findings).
- **R6 F-1: a blind spot in the accepted image checker.**
  - The accepted R5 image checker finds marker references only through
    objdump's `<symbol>` annotations.
  - In D-10's GCC image on the K3 layout, the code forms a marker's
    address with an `auipc` followed by `addi rd,rd,0`. objdump prints that
    pair as `mv` with no annotation.
  - So the checker rejected D-10 at L6 instead of passing it.
  - The K3 copy resolves exactly that pair form through the symbol table.
    It resolves one address in 44 images. B4 still derives that copy from
    the accepted bytes, and the accepted checker is fixed separately. See
    [F-1](r6/README.md#f-1-a-blind-spot-in-the-accepted-image-checker-exposed-by-the-k3-layout).
- **B1's quiesce lies outside both packages' assumptions.** It adds
  96 bytes, including its own `sret` in `be_b1_skip`.
  - R6's K3 image checker has one rule for it (F-2).
  - R7's "sole SRET" theorems cover only the scoped symbols. `be_reset`,
    its quiesce call, and the quiesce code are listed cut points.
- **Layout shift.** The quiesce call grows `be_reset`, so R7's scoped
  symbols move by `+0x81e00010` rather than B2's `+0x81e00000`. R6's D-15
  byte-delta pin is translated with those addresses and matches exactly.

## Commands

```sh
make -C bringup/k3-b4 check      # R6 then R7, about 15 minutes
make -C bringup/k3-b4 r6-check   # the R6 half
make -C bringup/k3-b4 r7-check   # the R7 half
make -C bringup/k3-b4 clean
```

R6's 64 traced QEMU runs each write 650 to 700 MB of raw trace, 43 GB in
all. Each trace is deleted after extraction. In a fresh checkout, B2 clones
and builds OpenSBI v1.6, which needs network access; setting `OPENSBI_FW` to
an existing build skips that.

## Claims and non-claims

- **R6 half:** QEMU emulation, host tests, and static checks show that each
  accepted single-defect fixture is detected on the K3 port at its declared
  layer, with the declared class. This matches what accepted R6 measured
  on the QEMU R5 sources.
- **R7 half:** a bounded Rocq proof, as in accepted R7, over the exact
  extracted bytes of the eleven scoped privileged-wrapper symbols in B2's
  two K3 images, together with generated configuration facts.
- **Not claimed:**
  - formal verification of Beryllium, C refinement, whole-ELF coverage, or
    hardware validation;
  - any board claim: these images ran on the COM260 in B2 and B3, but B4
    ran nothing on the board;
  - a re-acceptance of R6 or R7; B4 changes no accepted checker.
