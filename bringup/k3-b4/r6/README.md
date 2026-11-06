<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B4, R6 half: the accepted adversarial catalogue on the K3 port

This directory re-runs the accepted R6 single-defect catalogue (exact
target `7ba3649f03cf13b65df33020e345d361cce2993a`) against the K3 port of
accepted R5. B2 builds that port, accepted at `898af4e0`. The catalogue
has 47 entries:

| Partition | Entries | Detected at |
| --- | --- | --- |
| Static | S-01..S-14 | L3, L5, L6 |
| Host | H-01..H-17 | L11 |
| Dynamic | D-01..D-15 | L6-L10, under QEMU |
| Control | C-01 | the whole pipeline |

Each fixture runs at its declared layer with the K3 form of the accepted
instrument. Its result is compared with the accepted expectation, or with a
documented, mechanically derived K3 translation of it.

Nothing under `include/`, `virt/`, `arch/`, `tests/`, or
`bringup/k3-b0`..`k3-b3` changes. Generated output goes only to
`build/k3-b4/r6/`.

**Status:**

- All 47 entries match: 14 static, 17 host, 15 dynamic, and C-01.
- The dynamic entries are checked against the full accepted L10
  semantics, from the accepted QEMU tracing.
- The gate exits 0 only when every entry and every applicable accepted
  count matches. It has no bypass.
- One finding, [F-1](#f-1-a-blind-spot-in-the-accepted-image-checker-exposed-by-the-k3-layout),
  is a latent blind spot of the accepted R5 image checker that the K3
  layout exposed. B4 fixes it in its K3 copy, which it still derives from
  the accepted checker's bytes; the accepted checker is fixed separately.
- The evidence is QEMU emulation, host tests, and static checks of the K3
  port. Hardware is **NOT RUN**.

## How it works

1. **`make -C bringup/k3-b2 port-check image`** builds B2's port and its
   GCC and Clang images. B2's `port.py` re-derives the port byte for byte.
   Later, the dynamic partition requires C-01's flat images to equal B2's,
   and B2's to equal the accepted B2 digests (`9c145f00…`, `47be17e3…`).
2. **`scripts/derive.py`** writes `build/k3-b4/r6/`:
   - It checks 91 inputs against SHA-256 pins of their accepted bytes
     (`git show <commit>:<path>`):
     - R6 at `7ba3649f`: the catalogue `fixtures.json`, all 47 manifests,
       all 29 defect copies, `r6-check.c`, `check-fixture-image.mjs` (L8
       constants), `check-dynamic.mjs` (L10 constants), and `host.mk`;
     - R5 at `165f4d00`: `check-sources.mjs`, `check-image.mjs`,
       `check-image-parity.mjs`, and `tests/r5/Makefile`;
     - R7 at `9bf22913`: `proof/Exact.v`;
     - B2 at `898af4e0`: `Makefile`, `port.py`, `check-b2-markers.py`,
       and `run-qemu.sh`;
     - B1 at `b44c3c6b`: `b1-handoff.S`.
   - It reads 85 of them, and each fixture's accepted base, from their
     accepted commits, so no working-tree change to an accepted tool can
     alter the derivation. It reads the other 6 in place, because B4 uses
     them where they live: B2's 4 files, `b1-handoff.S`, and `r6-check.c`,
     which the host partition compiles.
   - It then writes the K3 checkers, the F-1 control, one tree per
     image-path fixture, `plan.json`, and `DERIVE-MANIFEST.txt`.
   - Each tree is the control tree (C-01) plus exactly one changed file,
     verified file by file.
3. **`tests/check-r6-k3.py`** runs each partition and records every
   stage's status, stdout, and stderr under
   `build/k3-b4/r6/fixtures/<id>/stages`.
   - Its classifiers are pure functions of those records and `plan.json`.
   - They port the accepted rules: `catalogue-static.mjs`'s
     `classifyRejection`, `check-fixture-image.mjs`, and
     `check-dynamic.mjs` (`extractTrace` and `--verify`).
4. **`tests/run-qemu.sh`** makes one traced run of one image on B2's
   K3-like machine. The dynamic partition starts an image's runs as soon
   as it passes L8, one QEMU and one extraction per core.
5. **The summary** goes to `build/k3-b4/r6/summary.json` and
   `summary.txt`. It holds:
   - per-fixture outcomes;
   - the measured counts, each equal to the accepted one;
   - the derived D-15 pins and the F-1 rule's resolved pairs;
   - the tool versions and the OpenSBI firmware digest.

| Layer | K3 instrument |
| --- | --- |
| L3 | accepted `tests/r5/check-sources.mjs`, unchanged, run in the fixture tree (K3-ported sources and the accepted `tests/r5/Makefile` declaration) |
| L4, L5 | B2's own Makefile (`BUILD=<fixture>`, `PORT_INPUTS=`, `-o PORT-MANIFEST.txt`): the accepted R5 flags; GNU ld and lld enforce the ported linker script's 57 `ASSERT` conjuncts |
| L6 | K3 copy of accepted `tests/r5/check-image.mjs` (substitutions below), over `objdump -d`, the accepted R5 recipe's plain listing |
| L7 | K3 copy of accepted `tests/r5/check-image-parity.mjs` |
| L8 | the accepted `check-fixture-image.mjs` comparison set (ELF header, PT_LOAD, allocated sections, 13 pinned sections, 5 fixed and 15 required symbols, flat bytes, and the D-13 single publication site), with K3 addresses |
| L9 | `tests/run-qemu.sh`: B2's k3-like command with the accepted `-d in_asm,cpu` tracing plus `int`, the accepted traced bound of 120 s, and a 30 s grace after the terminal marker |
| L10 | the accepted `check-dynamic.mjs` semantics extracted from each trace, plus the console, the interrupt log, the terminal SBI call, and QEMU status (see [below](#expectations-that-differ-from-accepted-r6)) |
| L11 | accepted `tests/r6/r6-check.c`, unchanged, built with `host.mk`'s exact GCC and Clang commands against the K3 port |

## Reused unchanged

These are used unchanged:

- 26 of the 29 accepted defect copies, byte for byte;
- `r6-check.c`;
- `check-sources.mjs`;
- the `tests/r5/Makefile` declaration;
- every fixture manifest's expectations: messages, classes, last markers,
  consoles, VS entries, guest exits, final registers, backing witnesses,
  and declared deltas. The one exception is the published root values,
  which follow B2's hgatp rule (see below);
- the accepted L10 constants: tracked symbols, guest pages, and exit
  labels;
- B2's port, build graph, flags, OpenSBI v1.6 (`bd613dd9`), and QEMU
  machine;
- B2's 22-line marker checker, which also judges each C-01 console.

`derive.py` also binds B2's build to the accepted declaration. B2's
`C_SOURCES` and `ASM_SOURCES` must equal the accepted `tests/r5/Makefile`
lists, in order. Its `WARNINGS`, `MARCH`, `TARGET_FLAGS`, and `LINK_FLAGS`
must be the accepted words, with only `$(ROOT)` replaced by `$(PORT)`.

## Substitutions and mutations

`+0x81e00000` is B2's rule: every image-layout literal in
`[0x80200000, 0x80234000]` moves to the K3 window at `0x1_0200_0000`.

| Input | Change | Count |
| --- | --- | --- |
| `check-image.mjs` (L6) | 8-digit layout literals `+0x81e00000` (B2's `port.rebase`) | 24 |
| `check-image.mjs` (L6) | 16-digit layout literals in its JSON output `+0x81e00000` | 7 |
| `check-image.mjs` (L6) | B1's `be_b1_skip` `sret` counted apart ([F-2](#f-2-the-accepted-image-checker-needs-one-k3-rule-for-b1s-code)) | 1 rule |
| `check-image.mjs` (L6) | an `auipc` + `addi rd,rd,0` pair annotated from the ELF symbol table ([F-1](#f-1-a-blind-spot-in-the-accepted-image-checker-exposed-by-the-k3-layout)) | 1 rule |
| `check-image-f1-control.mjs` | the K3 `check-image.mjs` without the F-1 rule. It goes to `checkers/` only, for the self-test, never into a fixture tree | control |
| `check-image-parity.mjs` (L7) | trap-vector window literals `+0x81e00000` | 2 |
| `tests/r5/tool-lock.mjs` | replaced by a shim of the same interface that names `riscv64-linux-gnu-{nm,readelf,size}` by command, as B2 does | new file |
| L8 constants | 13 pinned section addresses and 5 fixed symbol addresses from the accepted `check-fixture-image.mjs`, each `+0x81e00000`; sizes unchanged | 18 |
| L10 root installs | each accepted published HGATP value mapped by B2's two exact `r3.h` rules (`…080214` to `…102014`, `…08021c` to `…10201c`) | 2 values |
| S-01, S-02 defect copies | the B2 port of the lds (41 literals) plus the hunk's one literal (`. = 0x80220000;` to `0x102020000`, `. = 0x80234000;` to `0x102034000`) | 42 each |
| S-03 defect copy | the B2 port of the lds; its hunk (`0x1000` to `0x2000`) has no address | 41 |
| the other 26 defect copies | none: their bases (`r5-trap.S`, `r5-runtime.c`, `r5-guest.S`, `virt/be/r5.c`, `tests/r5/Makefile`) are unported, so the K3 defect copy is the accepted file | 0 |

Every K3 defect copy is the accepted copy passed through B2's own
`port.rebase`. The fixture bases have no other B2 rule. The derivation
requires these to match the accepted ones:

- the hunks, compared with `difflib` (same lines, same shapes);
- the `+`/`-` totals in each manifest;
- the 6/6 change budget.

## Why the K3 detection is equivalent

**L3 (S-04, S-11, S-13, S-14):**

- The accepted checker runs byte for byte. It reads only the tree it sits
  in.
- The K3 tree is B2's port, whose fixture bases are unchanged. S-04, S-11,
  and S-13 mutate the same bytes as accepted R6.
- S-14 mutates the accepted `tests/r5/Makefile` declaration. The binding
  above makes B2 compile exactly the translation units that declaration
  lists, with its flags and linker script.
- The one K3 build input outside the declaration is B1's accepted
  `b1-handoff.S`. B2 compiles it directly, and `derive.py` pins it.
- Each fixture produces the accepted message, and no build runs.

**L5 (S-01, S-02, S-03, S-12):**

- The ported linker script keeps every accepted `ASSERT` and message. Only
  addresses move.
- Both linkers report the complete accepted message set and nothing
  outside the accepted noise list. The list is the accepted one, with B2's
  build paths.
- S-01 reports `R5 protected root moved` and
  `R5 root pools overlap management stack`.
- No ELF is left behind.

**L6 (S-05..S-10):**

- Besides the layout literals, two K3 rules apply: the B1 `sret` rule
  (F-2) and the F-1 annotation rule. The disassembly, symbol, fence, root,
  call, and marker rules are the accepted code.
- The F-1 rule only adds an annotation that objdump omits. Across all 44
  built images it resolves exactly one pair: D-10's GCC `switch_domain`.
  It cannot change a static fixture's outcome, and none changed.
- Each image yields the accepted message for both toolchains, with the
  same sorted symbol lists. For example, S-05's remaining fence sites are
  `be_r3_arch_install_management`, `be_r3_arch_reset_state`, and
  `be_r5_arch_reset_state`.
- The accepted S-08 construction guard holds: two distinct
  `be_r5_switch_tail` call sites per toolchain. It runs before L6 is
  believed.

## Expectations that differ from accepted R6

1. **D-15's layout pin is translated, not adopted.** The accepted pin
   records 2 runs, 10 bytes, and a `.monitor.text` size per toolchain.
   - The accepted R7 `Exact.v` places `be_r5_switch_tail` at `0x80207480`
     (GCC) and `0x802074b0` (Clang). That puts both accepted pins at
     switch-tail offsets +208 (9 bytes) and +218 (1 byte).
   - The K3 pin applies those offsets to the switch tail of the
     same-toolchain K3 C-01 image:
     - GCC: runs at 30048 and 30058, `.monitor.text` 30336;
     - Clang: runs at 30096 and 30106, `.monitor.text` 30384.
   - The `.monitor.text` size must equal C-01's (unchanged), and
     `be_r5_switch_tail` grows only from 212 to 220.
   - The derivation uses only the control image and accepted records.
     Both D-15 images match it exactly.
2. **L10 is the accepted L10, with one value translation and two
   additions.**
   - Each run is traced with the accepted `-d in_asm,cpu`. The accepted
     `extractTrace` reduction, ported line for line, yields:
     - the VS entries (`pc`, `hstatus`, `s0`, `a0`, `a1`);
     - the guest exits (label, `scause`, `sepc`, `stval`, `htval`);
     - the root installs, the final registers, the tracked-symbol counts,
       and any VS execution outside the guest pages.
   - Every accepted `--verify` rule applies:
     - the exact console, class, last marker, and no forbidden marker;
     - entries, exits, roots, and final registers equal to the accepted
       declarations;
     - the backing witnesses;
     - D-15's preempted entry;
     - the entry, exit, and root counts;
     - the accepted comparable projection identical across both runs and
       both toolchains.
   - The value translation: the published HGATP values follow B2's hgatp
     rule. The accepted guest-visible values (`hstatus`, `htval`,
     registers, PCs, causes) are unchanged and match.
   - The first addition: `-d int` in the same log. Its guest exits must
     agree with the trace's, and the last trap must be an SBI `ecall` from
     inside `be_r3_arch_sbi_call`, with QEMU exit 0 and firmware SBI 2.0.
   - The second addition: the traced bound is the accepted 120 s (B2's
     untraced 60 s does not allow for tracing), with a 30 s grace after
     the terminal marker.
   - Raw traces follow accepted R6-B. Each is about 650-700 MB and is
     deleted after extraction. Each run keeps:
     - its semantics record;
     - the raw trace's SHA-256 and byte count;
     - a 400-line head and 800-line tail excerpt.
3. **The machine is B2's.** The accepted run used QEMU's minimal CPU with
   128 MiB and the default firmware. Here it is B2's k3-like machine:
   - the full rv64 CPU with H, AIA/IMSIC, one hart, and 8 GiB;
   - OpenSBI v1.6 `fw_dynamic`, SBI 2.0.
4. **C-01's identity is to B2.** The C-01 flat images must equal B2's
   images, which must equal the accepted B2 digests. Accepted R6 compared
   against the accepted R5 build.
5. **Tools are unpinned, as in B2.** This host's GCC 16.2.1 and binutils
   2.46.1 differ from the accepted locks (16.1.1, 2.46). Accepted R5/R6
   launchers and tool locks are not run. The versions are under
   [Tools](#tools).
6. **Counts.** `components_per_tree` (16) and `source_components` (5)
   describe the accepted scratch framework and do not apply to the K3
   trees. Every other accepted count is measured and must be equal.

## Findings

### F-1: a blind spot in the accepted image checker, exposed by the K3 layout

**The blind spot:** the accepted R5 image checker finds symbol references
only through objdump's `# <address> <symbol>` annotations. objdump prints
an `auipc rd,hi` followed by `addi rd,rd,0` as `mv rd,rd`, with no
annotation. A symbol whose PC-relative low part is exactly 0 is therefore
invisible to every accepted rule.

**How the K3 layout exposed it:** in the K3 GCC image of D-10,
`switch_domain` forms `marker_management_verified` this way:

```text
102005cc0:  00003517  auipc  a0,0x3
102005cc4:  00050513  mv     a0,a0      (addi a0,a0,0; target 0x102008cc0)
```

The unmodified accepted rules then reject D-10 with:

```text
gcc: switch transaction emits unexpected markers: marker_management_fenced,
marker_pending_management,marker_pending_protected,marker_protected_fenced,
marker_protected_verified
```

That is a layer shift against D-10's declared L6 pass.

- C-01 forms the same address with `addi a0,a0,24`, which is annotated.
- The same D-10 defect on the accepted QEMU layout, built with this host's
  GCC 16.2.1, gives `addi a0,a0,14 # 80208cc0 <marker_management_verified>`
  and passes. So this is a layout effect, not a toolchain one.
- Before the fix, a manual diagnostic outside the gate ran each D-10
  image once. Both still ended with `BE_R5:FAIL target-readback`.

**The fix, in the K3 copy:** one counted rule in `derive.py`'s table
(`F1_RULE`) annotates exactly that pair, as objdump annotates a nonzero
offset. The rule:

- decodes both instruction words: an `auipc rd` immediately followed by
  `addi rd,rd,0`, with the same register as source and destination;
- resolves the formed address against the ELF symbol table (`nm -n`, which
  the checker already reads);
- annotates only when exactly one symbol starts at that address.

Nothing else in the listing changes. A missing, wrong, or extra marker is
still rejected. Across all 44 built images the rule resolves exactly one
pair, D-10's. B4 applies the rule to the accepted checker's bytes at
`165f4d00`, read from git; the accepted checker is fixed separately.

**Self-tests** run the real K3 checker and its F-1 control (the same copy
without the rule) over B2's GCC image, with C-01's annotated pair replaced
by forged zero-offset pairs:

- (i) the D-10-style pair to `marker_management_verified` resolves, and
  the image passes;
- (ii) a pair to the wrong marker (`marker_final_event`) or to a non-marker
  (`be_r5_control`) is still rejected. Pairs that form no symbol start,
  use another source register, carry a nonzero `addi` word under `mv` text,
  or are not adjacent stay unresolved and are rejected;
- (iii) the F-1 control still misses the pair and rejects with exactly the
  message above. That documents F-1.

The gate now runs D-10 through every layer. It passes L6 to L8, runs twice
per toolchain, and fails closed with `target-readback` after `BE_R5:02`,
as accepted.

### F-2: the accepted image checker needs one K3 rule for B1's code

B2's `be_reset` first calls B1's `be_b1_quiesce`. Its local skip handler
`be_b1_skip` returns to HS with one `sret`, so the K3 image holds 3. The
accepted check `expected exactly 2 sret in the image` therefore fails on
the unmutated K3 control.

The K3 rule requires `be_b1_skip` to hold exactly one `sret` and keeps the
accepted count of 2 over the rest of the image. No fixture is detected by
that count; S-04's second `sret` is caught at L3. With F-1 and this rule,
the K3 control passes every accepted L6 rule.

## Measured results (2026-10-06 UTC)

| Partition | Result |
| --- | --- |
| Static | 14 of 14 match: 4 at L3, 4 at L5, 6 at L6, both toolchains |
| Host | 17 of 17 match, 18 class outcomes, 1063 assertions, 43 lines; four byte-identical streams (K3 GCC, K3 Clang, accepted-source GCC, accepted-source Clang) |
| Dynamic | 16 of 16 match (C-01 and D-01..D-15), 2 traced runs x 2 toolchains each, with the full accepted L10 semantics |

**Dynamic detail:**

- C-01 reproduces B2's exact 22-line sequence, and B2's marker checker
  passes it.
- Its 6 guest exits, 6 VS entries, 2 root installs (`…10201c`,
  `…102014`), and final registers are the accepted ones.
- D-06 shows cause 22 (`0x16`) at `0x40011028`, with tval `0x68002573`.
- D-05 shows cause 20 at `0x40002000`.
- D-15 shows an asynchronous VS software interrupt (cause 2) at
  `0x40011000`. It has no VS entry dump there, so no protected
  instruction retired.

**Counts against the accepted ones:**

- Every applicable accepted count matches:
  - entries 47, build attempts 52, link failures 8, image checks 44;
  - L6 static rejections 12, L6 declared rejections 18, L6 declared
    passes 14;
  - parity runs 7, L8 differentials 32;
  - dynamic ELFs 30, control ELFs 2, quarantined static ELFs 12;
  - trees 30, L3-only fixtures 4;
  - host executions 68;
  - QEMU runs 64.
- Images: 32 executed (dynamic and control) and 12 static images.
- Timeouts 0, non-zero QEMU statuses 0, layer shifts 0.
- Resolved F-1 pairs: 1.

**Gate:**

- Output: `BE_K3_B4_R6_CHECK: PASS matched=47/47 images=32 qemu_runs=64
  layer_shifts=0 findings=0`.
- `summary.json` and `summary.txt` regenerate byte-identically. Raw trace
  digests stay in the per-run files, not in the summary.
- The checker self-test passes 124 cases. Each of these is refused:
  - a missed detection, a layer shift, or a wrong diagnostic, for every
    static fixture;
  - in L10: a wrong class, a missing or extra marker, a forbidden marker,
    cause 2 instead of 22, a wrong `htval`, a wrong VS-entry `hstatus`,
    the accepted QEMU roots instead of K3's, a wrong final register, VS
    execution outside the guest pages, a trap-vector count mismatch, a
    retired protected instruction, an interrupt after a retirement, an
    interrupt log disagreeing with the trace, a timeout, a non-zero
    status, a missing terminal SBI call, or a run without extracted
    semantics;
  - in L8: an extra guest byte, a byte outside the monitor, a D-15 third
    run or resized tail, an unrolled publication, or a moved symbol;
  - host stdout drift, a class swap, or compiler disagreement;
  - the nine F-1 checker cases above;
  - in the gate, one mismatching entry, a missing result, a deviation
    recorded as documented, or a count short of the accepted one.
- The accepted trace reduction is checked on a forged trace.
- Six end-to-end cases record a classifier's own refusal the way the
  partitions do and require the whole gate to fail: a missed detection, a
  layer shift, a wrong class, a missing marker, an extra marker, and an
  unexpected delta.

## Commands

```sh
make -C bringup/k3-b4/r6 check      # lint, self-test, partitions, summary
make -C bringup/k3-b4/r6 static     # or host, dynamic, self-test, summary
make -C bringup/k3-b4/r6 clean
```

`OPENSBI_FW` resolves as in B2: B1's build when present, otherwise B2's
target clones and builds OpenSBI v1.6 (`bd613dd9`). Its `fw_dynamic.bin`
SHA-256 is `78f14d30…6a42b`, identical to B1's build.

On this workstation, `check` from an empty `build/k3-b4/r6`, with
OpenSBI already built, took 11 min 27 s and 12 min 37 s in two clean
runs. Another session had the machine at a load average of about 9 to 12
on 8 cores. Cloning and building OpenSBI adds about 3 min.

In each clean run, the 64 traced runs:

- took about 19 s to 60 s each, against the 120 s bound;
- wrote 43.3 GB of raw trace (654 MB to 701 MB per run), all deleted
  after extraction.

The two clean runs wrote byte-identical `summary.json` (`5c6aeb95…`) and
`summary.txt` (`26a6400f…`). `build/k3-b4/r6` then holds 168 MB.

## Tools

These are unpinned, used by command name as in B2:

| Tool | Version |
| --- | --- |
| Cross GCC | `riscv64-linux-gnu-gcc` 16.2.1 20260819 |
| GNU binutils | 2.46.1-1.fc44 (`ld`, `objdump`, `readelf`, `nm`, `size`, `objcopy`) |
| Clang and `ld.lld` | 22.1.8 |
| Host GCC | 16.2.1 |
| QEMU | 10.2.2 |
| Node | v22.23.1 |
| Python | 3.14.7 |
| GNU Make | 4.4.1 |
| ShellCheck | 0.11.0 |
| Ruff | 0.15.12 |

## Claims and non-claims

**Claim:** in QEMU emulation of B2's K3-like machine, in host tests, and in
static checks of the K3 port, every accepted R6 entry behaves as accepted
R6 declares:

- each static fixture is rejected at its declared layer with the complete
  accepted diagnostic set, for both toolchains;
- each host fixture produces its accepted stable error class, in
  byte-identical GCC and Clang result streams;
- each dynamic image reaches its declared L6 disposition and differs from
  its same-toolchain control only in its declared delta;
- each dynamic image terminates fail-closed in two traced runs per
  toolchain, through the monitor's SBI call, with QEMU status 0. Each run
  has the accepted console, class, last marker, VS entries, guest exits,
  final registers, and backing witnesses, and the accepted root installs
  translated by B2's hgatp rule;
- C-01 reproduces B2's 22-line sequence.

**Non-claims:**

- No board run: hardware is **NOT RUN**.
- Not an R6 re-acceptance, not formal verification, and not hardware
  validation.
- Accepted R6 claims do not transfer beyond what is re-measured here.
- Raw traces are not retained and are not claimed byte-identical. As in
  accepted R6, the trace dump count is recorded but not compared.
- B4's F-1 rule exists only in its K3 copy. Nothing here changes or
  re-accepts the accepted R5 image checker, which is fixed separately.
- No evidence bundle, acceptance pin, or tool lock is produced.
