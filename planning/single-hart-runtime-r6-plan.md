<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R6 bounded plan

## Status and decision

Exact plan commit `609867fdad75279c0913022909efd65c4a838909` was the
originally accepted R6 plan target; it **remains accepted history and byte
unchanged**. This document is that accepted plan as narrowly revised twice,
and both revisions were **responsible-human accepted on 2026-07-30** at their
own exact commits: `75269f058ae578b0a76a113d6c05c0aaceeac8ec` (parent
`4bff41764cf8ec9275e771cd3c1ce124961da93a`), carrying
[Plan revision R6-A](#plan-revision-r6-a-d-15-injection-site), and
`6d6464c6c937abccd59df932006c1049fd79fac6` (parent
`4d6c3c9b0899c7a30b2150ff0d4067369ccef774`), carrying
[Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention).
The twice-revised plan is therefore the **plan of record for D-15 and for R6
trace retention**; the decisions are recorded in
[`single-hart-runtime-r6-plan-revision-review-summary.md`](single-hart-runtime-r6-plan-revision-review-summary.md)
and
[`single-hart-runtime-r6-plan-r6b-review-summary.md`](single-hart-runtime-r6-plan-r6b-review-summary.md).
This document intentionally names no self-referential revision SHA in its
body text beyond those recorded acceptances.

Bounded R6 implementation **has started locally** under the accepted plan and
the two recorded proceed instructions. That local work is **not reviewed, not
accepted, and not complete**: no exact R6 implementation commit exists, no R6
evidence bundle or claim is asserted, and nothing below reports an
implementation result as accepted evidence.

Implementing dynamic fixture D-15 exposed a **defect in the originally
accepted plan**: the injection site that plan named for D-15 cannot produce
the error class it declared for it. The correction is specified in
[Plan revision R6-A](#plan-revision-r6-a-d-15-injection-site) and is applied
throughout the D-15 specification below. With the corrected plan accepted,
**D-15 implementation may resume** under the already-recorded R6
implementation authorization, strictly within this plan's scope. No other
fixture, partition, count, layer, class, or boundary changes.

Continued implementation then found **two further defects in the corrected
plan**, both about how R6 *records* D-15 and its runs rather than about what
D-15 constructs: the plan's `.monitor.text` layout arithmetic for the two
inserted instructions was factually wrong, and its raw-QEMU-trace retention
rule is arithmetically impossible inside the plan's own 512 MiB evidence
bound. The correction is
[Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention),
and the exact commit carrying it,
`6d6464c6c937abccd59df932006c1049fd79fac6` (parent
`4d6c3c9b0899c7a30b2150ff0d4067369ccef774`), was **responsible-human accepted
on 2026-07-30**; the decision is recorded in
[`single-hart-runtime-r6-plan-r6b-review-summary.md`](single-hart-runtime-r6-plan-r6b-review-summary.md).
With revision R6-B accepted, **R6 integration and evidence work may resume**
under the already-recorded R6 implementation authorization, strictly within
this plan's scope, and every value revision R6-B pins must be re-derived from
a checked run at the exact implementation commit rather than trusted from this
text. D-15's plan construction itself — the base file and the exact
two-instruction defect of
[Plan revision R6-A](#plan-revision-r6-a-d-15-injection-site) — is unaffected:
it remains accepted, and local implementation reproduced it.

Two responsible-human instructions are recorded:

| Instruction | Timestamp |
| --- | --- |
| `proceed to implement R6 exact` | 2026-07-30T20:34:36.241+00:00 |
| `proceed with all r6 implementation work` | 2026-07-30T20:36:53.931+00:00 |

Those instructions are treated as **separate implementation authorization for
R6 under the master-plan R6 row only**. They are not a plan acceptance. They
did not accept the original plan or either revision — all three were accepted
by their own exact-commit decisions — and they do not authorize any work
outside the master-plan R6 row.

**Remaining decisions:** a complete R6 evidence bundle, report claim, or
implementation review packet still requires its own exact-commit review and a
separate responsible-human acceptance; no R6 implementation is accepted.
Nothing in this document, in the dependency order, in the accepted R5 record,
in the accepted original R6 plan target, in the accepted corrected plan
target, in the accepted revision B target, or in the two recorded proceed
instructions authorizes a tag, a push, publication, release, R7, or an
implementation-acceptance claim.

## Plan revision R6-A: D-15 injection site

This is the only substantive change from accepted plan target
`609867fdad75279c0913022909efd65c4a838909`. It is **narrow**: it changes the
base file and the exact single defect of dynamic fixture D-15 and nothing else.
Every count, layer, class, disposition, ledger entry, claim, and non-claim in
this plan is preserved.

### The defect in the accepted plan

The accepted plan placed D-15's single defect in a copied
`arch/riscv/be/r5-runtime.c`, arming `hvip[2]` and `hie[2]` inside
`switch_domain` after publication and before the tail. That placement cannot
reach the declared `interrupt` class, because the accepted, immutable
`be_r5_switch_tail` re-reads both control registers on the published no-call
path and rejects a non-zero value before it can reach `SRET`:

```text
csrr t0, hie      bnez t0, .Lrestore_bad_controls
csrr t0, hvip     bnez t0, .Lrestore_bad_controls
```

Any arming that happens **before** those readbacks is therefore detected by the
accepted mechanism itself and terminates as `entry-controls` with last marker
`BE_R5:04`, never as `interrupt`. The declared class is unreachable at the
named site under any restricted-C spelling, so it is a plan defect and not an
implementation defect. The accepted plan's own rule for this situation is the
wrong-error-class gate: the harness must not relax the expectation, and the
plan must be revised. **That gate is preserved unchanged.**

The superseded runtime-C injection statement is removed from this plan
entirely; it survives only as this historical justification.

### The corrected placement

D-15's base file changes from `arch/riscv/be/r5-runtime.c` to
`arch/riscv/be/r5-trap.S`. D-10 through D-14 are untouched and remain copied
`arch/riscv/be/r5-runtime.c` monitor defects.

The single defect is placed **after** every `be_r5_switch_tail` entry-control
readback (`satp`, `sstatus`, `stvec`, `sscratch`, `sie`, `scounteren`,
`hstatus`, `hie`, `hvip`, `vsatp`, `hgatp`) and **after** the last frame
restore pair (`ld t0, FR_HTVAL(t6)` / `csrw htval, t0`), immediately before the
`.option pop` and the jump to the shared `be_r5_enter_guest_tail`. Exactly two
instructions are inserted, in this order, as one contiguous `+2 / -0` hunk:

```text
csrsi hvip, 4
csrsi hie, 4
```

Both are required:

- `csrsi hvip, 4` alone sets `VSSIP` but leaves `hie.VSSIE` clear, so no
  HS-destined interrupt is enabled and the fixture is architecturally
  indistinguishable from the control image — that is, **no defect at all**
  for the `hvip`-only variant, by register semantics alone and not by an
  unretained exploratory measurement;
- `csrsi hie, 4` alone enables an interrupt that is never pending;
- together they make a VS software interrupt both pending and enabled at HS
  level while `hideleg` remains `0`, so the interrupt is HS destined.

`csrsi` takes a 5-bit unsigned immediate, so **neither instruction reads or
writes any GPR**: `t6` (frame pointer), `t5` (target root), `t4` (trusted
stack), and the `t0`/`t1` scratch pair are all untouched, and the guest
register restore in `be_r5_enter_guest_tail` is byte-for-byte the accepted
sequence. Both instructions sit inside the `.option arch, +h` region the
accepted tail already opens, so no assembler option changes and the defect
copy assembles under the accepted `MARCH`/`MABI` flags.

Architecturally, the interrupt becomes pending and enabled after the monitor's
own verification and before `SRET`. An interrupt destined for a privilege level
higher than the current one is always taken regardless of the lower level's
global enable, so it is taken immediately after `SRET` transitions to VS mode
at `0x40011000`, before any protected guest instruction retires. HS traps to
`be_r5_trap_vector`, and `be_r5_handle_exit` sees the interrupt bit in the
recorded `scause` and terminates with `BE_R5:FAIL interrupt`.

### Expected deterministic result

This table is the corrected placement's **normative expected result**, not a
report of a verified measurement. It is `NOT RUN / unverified as retained R6
evidence` until D-15 implementation resumes after the responsible human
accepts an exact commit containing this revision, and a checked `tests/r6/`
build and run against the corrected `r5-trap.S` placement reproduces it with
retained images, logs, and digests.

For both pinned toolchains and both runs, with the pinned QEMU and firmware
matrix unchanged:

| Property | Expected value |
| --- | --- |
| L3 source inventory, L4 compile, L5 link | pass |
| L6 accepted image check | `pass` disposition, unchanged checker |
| L7 accepted parity | runs and passes |
| L8 differential | exactly the one declared `monitor-range` delta and no other differing byte, pinned to the exact runs, count, and offsets fixed by [Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention) |
| Console | accepted prefix through `BE_R5:04 PROTECTED_TARGET_VERIFIED pc=0x40011000`, then `BE_R5:FAIL interrupt` |
| Last marker | `BE_R5:04` |
| Forbidden markers observed | none; no `BE_R5:05`, no `BE_R5:12`, no `BE_R5:SRST_RETURNED` |
| Recorded exit | `scause=0x8000000000000002`, `sepc=0x40011000`, `stval=0`, `htval=0`, `hideleg=0` |
| Protected guest instructions retired | zero; no `V=1` protected entry dump in the trace |
| Error class | `interrupt` |
| Shutdown | monitor-issued SBI SRST, QEMU status `0` |

The wrong-error-class gate still applies to this corrected expectation: if the
measurement differs in class, cause, marker, or disposition, the fixture fails
as `wrong-error-class`, the harness must not relax it at run time, and the plan
must be revised again.

### Accepted-checker compatibility

The corrected placement is compatible with the accepted, unmodified
`tests/r5/check-image.mjs`, `tests/r5/check-sources.mjs`, and
`arch/riscv/be/r5-beryllium.lds`:

1. **No call.** `csrsi` is not `jal`, `jalr`, `call`, or `tail`, and no new
   `jr` is introduced, so the call-free tail rule and its permitted tail-jump
   set are unchanged.
2. **Ordered verification preserved.** The insertion is strictly after the last
   item of the pinned readback order, which ends at `csrr t0,hgatp`, so the
   ordered switch-tail verification sequence still matches.
3. **All eight restore adjacency windows intact.** The checker requires each
   `ld <reg>,<248 + 8i>(<reg>)` to be followed on the next line by
   `csrw <csr>,` for the eight trap CSRs ending at `htval` at offset `304`.
   The insertion is after the eighth pair, so no window is split.
4. **No HGATP write, no fence.** Neither instruction matches `csrw hgatp` or
   `hfence.gvma`; the image-wide HGATP writer set, the paired fence-site set,
   and the exactly-four HGATP-write count are unchanged.
5. **No site, symbol, or marker change.** `switch_domain` is not edited, so
   `be_r5_publish_target` and `be_r5_switch_tail` keep exactly one call site
   each, the pre-publication marker set is unchanged, no G-stage root pool is
   referenced, and no `be_r6`/`BE_R6` identifier is introduced.
6. **SRET invariants hold.** `be_r5_switch_tail` still reaches
   `be_r5_enter_guest_tail`, which still sets `SPP` exactly once and ends in
   the single R5 `sret`; the image-wide `sret` count stays `2`, and the L3
   source rule that `r5-trap.S` contains exactly one `sret` still holds for the
   defect copy.
7. **Layout unchanged.** The two inserted instructions are absorbed by the
   alignment padding the accepted tail already emits, so `.monitor.text` does
   not change size and nothing after the insertion point moves. See
   [Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention)
   for the corrected arithmetic and the pinned L8 byte expectation; the
   earlier "grows by 8 bytes" statement was factually wrong and is withdrawn.
   Every linker `ASSERT`, every pinned section address and size, every guest
   page, root pool, saved page, private page, shared page, the `0x34000` flat
   extent, and every fixed symbol address stay byte identical, and monitor
   text stays far inside its `0x8000` window.
8. **Accepted bytes remain immutable.** The defect exists only as
   `tests/r6/fixtures/D-15/r5-trap.S.defect` and is overlaid into the confined
   scratch copy by `tests/r6/prepare-scratch.sh`; no accepted file is edited,
   and `tests/r5/check-acceptance.sh --require` still reports the accepted R5
   target unchanged.

### Empirical status of this revision

Retained local artifacts support one checkable fact: fixture D-15, built at
the accepted plan's original injection site (a copied
`arch/riscv/be/r5-runtime.c` arming `hvip`/`hie` inside `switch_domain`),
deterministically fails as `BE_R5:FAIL entry-controls` with last marker
`BE_R5:04` under both pinned toolchains. That superseded-placement fixture,
its build outputs, and its run semantics remain on disk and are independently
reproducible through the checked `tests/r6/` targets; they are the retained
evidence for the plan defect described above.

During development-session exploratory work, the corrected two-instruction
placement in a copied `arch/riscv/be/r5-trap.S` was **reported** to build
under both pinned toolchains and to yield the expected `interrupt` result
under the pinned QEMU and firmware. The scratch images, console/trace logs,
and digests from that exploratory session were **not retained**. Because no
raw artifact for the corrected placement survives to re-derive, hash, or diff
against the accepted checkers, that report is **not independently checkable
evidence for this exact plan revision target**, and it must not be cited as a
reason for responsible-human acceptance of this revision.

The [expected deterministic result](#expected-deterministic-result) table
above is this revision's normative expected result, not the exploratory
report. It stays `NOT RUN / unverified as retained R6 evidence` until resumed
D-15 implementation runs a checked `tests/r6/` build and run against the
corrected placement that reproduces it with retained images, logs, and
digests. Acceptance of the corrected plan target rested on the architecture
and code reasoning in [the corrected placement](#the-corrected-placement) and
[accepted-checker compatibility](#accepted-checker-compatibility) above, and
on the fail-closed measurement gate the checked D-15 targets apply once
implementation resumes — never on the unretained exploratory report. The
wrong-error-class gate is unchanged: once D-15 resumes and is measured, if the
observed cause, class, marker, or disposition differs from the expected table,
the fixture fails as `wrong-error-class`, the harness must not relax the
expectation at run time, and the plan must be revised again.

D-15 implementation has since resumed under the accepted corrected plan and
has built and run the corrected placement locally. That local run is
**unreviewed, unaccepted implementation output, not retained R6 evidence**:
it is not covered by any accepted exact commit, no evidence bundle or claim
is asserted over it, and the expected-result table above stays `NOT RUN /
unverified as retained R6 evidence`. What that local work *did* establish is
recorded, with the same non-evidential status, in
[Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention),
which corrects two factual defects it exposed in this revision's own
bookkeeping and was itself accepted at its own exact commit,
`6d6464c6c937abccd59df932006c1049fd79fac6`, on 2026-07-30.

Exact commit `75269f058ae578b0a76a113d6c05c0aaceeac8ec`, containing this
revised plan, was responsible-human accepted on 2026-07-30, so D-15
implementation may resume under it and the already-recorded R6 implementation
authorization. Resumption accepts no implementation and produces no accepted
evidence by itself.

## Plan revision R6-B: D-15 image layout and trace retention

**Status: accepted at exact commit `6d6464c6c937abccd59df932006c1049fd79fac6`
(parent `4d6c3c9b0899c7a30b2150ff0d4067369ccef774`) on 2026-07-30**, recorded
in
[`single-hart-runtime-r6-plan-r6b-review-summary.md`](single-hart-runtime-r6-plan-r6b-review-summary.md).
R6 integration, the R6 evidence bundle, and the R6 report claim may proceed
under the already-recorded implementation authorization and within this plan's
scope; every value pinned below must still be re-derived from a checked run at
the exact implementation commit, and no R6 implementation, evidence, or
acceptance follows from this plan acceptance.

This revision is narrower than [R6-A](#plan-revision-r6-a-d-15-injection-site).
It changes **no fixture construction**: not D-15's base file, not its exact
`+2 / -0` two-instruction defect, not its declared class, layer, marker set,
disposition, or safety argument. R6-A is unchanged, remains accepted, and was
reproduced by local implementation. What this revision corrects is two
statements this plan makes *about* evidence — one factually wrong, one
arithmetically impossible — that continued implementation exposed.

Preserved without change: the 47-entry catalogue and its 46 single-defect
fixtures, 52 image build attempts, 44 successful links, 8 link failures, 64
QEMU runs, 14 static / 17 host / 15 dynamic / 1 control partitioning, the 29
primary classes with 0 uncovered and 4 secondary claims, the detection layers,
the outcome taxonomy and marker vocabulary, the wrong-error-class and
layer-shift gates, the acceptance-pin refresh scope, the recorded R6
implementation authorization, and every R7, publication, hardware, and formal
non-claim and gate.

### Defect 1: the D-15 layout arithmetic was factually wrong

The accepted corrected plan asserted that D-15's two inserted instructions
make `.monitor.text` "grow by 8 bytes" and "deterministically shift the
monitor code after the insertion point". **Both statements are false**, and an
L8 expectation written from them would have declared a delta that cannot
occur.

The accepted `arch/riscv/be/r5-trap.S` ends `be_r5_switch_tail` with
`j be_r5_enter_guest_tail` and then aligns the shared entry tail with
`.align 4`, i.e. to a 16-byte boundary. That alignment already emits **12
bytes of `nop` padding** (three `00000013` words) between the end of
`be_r5_switch_tail` and the start of `be_r5_enter_guest_tail`. The two
inserted 4-byte `csrsi` instructions consume **8 of those 12 padding bytes**;
4 bytes of padding remain, and `be_r5_enter_guest_tail` keeps its accepted
address. Consequently:

- `.monitor.text`'s **allocated size does not change**: it stays `0x7610`
  under GCC and `0x7640` under Clang, exactly as in the same-toolchain control
  image, and the flat image extent stays `212992` bytes under both;
- **runtime/flat-image invariant**: every allocated section relevant to
  execution — address, file offset, size, flags, and content outside the
  pinned flat delta below — is unchanged from the same-toolchain control
  image in both toolchains;
- the tail `j` **moves 8 bytes later inside the same padding window** and its
  immediate changes from `+0x10` to `+0x8`, still targeting the unmoved
  `be_r5_enter_guest_tail`;
- **symbol invariant, corrected**: every defined allocated `FUNC`/`OBJECT`
  symbol that this plan's accepted checker fixes by address (`be_reset`,
  `be_r5_management_fixture[_end]`, `be_r5_protected_fixture[_end]`) or
  requires by presence (including `be_r5_switch_tail`,
  `be_r5_enter_guest_tail`, and the rest of the accepted L8 required set)
  keeps its accepted **address** in both toolchains. This is *not* a claim
  that every named symbol in the image is unchanged: `be_r5_switch_tail`'s
  address is unchanged, but its recorded `st_size` grows from `212` to `220`
  bytes in both toolchains, because the two inserted instructions extend the
  function's own byte range before the unchanged unconditional jump. A
  symbol-table `st_size` is not an address, not an allocated-section size, and
  not a flat-image byte, and it is the only defined allocated `FUNC`/`OBJECT`
  symbol whose recorded entry differs at all.

### Explicit non-runtime changes: debug and symbol-table sections

D-15's two inserted instructions are compiled into the accepted GCC/Clang
toolchains along with unmodified DWARF debug information for
`arch/riscv/be/r5-trap.S`, so the assembled object's **non-allocated** debug
and symbol/string sections necessarily record two more instructions' worth of
line-number and mapping data. These sections carry no `SHF_ALLOC` flag, are
never loaded, never mapped into the flat image extracted for the runtime, and
are never executed; they are confirmed by `readelf` on the built D-15 and
control images to differ as follows, and only as follows:

- **GCC**: `.debug_line` grows from `0xe89c` to `0xe8a8` bytes (+12). This
  shifts the file offset of every later non-allocated section —
  `.debug_str`, `.debug_frame`, `.symtab`, `.strtab`, `.shstrtab` — and the
  ELF section header table itself, and the whole ELF file grows by a net
  **+8 bytes** (`.debug_frame`'s 8-byte alignment padding absorbs 4 of the 12
  added bytes). No allocated section, no symbol address, and no flat-image
  byte outside the pinned delta is affected.
- **Clang**: `.debug_line` grows from `0x6e0e` to `0x6e10` bytes (+2), and
  `.debug_aranges`'s file offset shifts by the same +2 bytes. `.symtab`,
  `.shstrtab`, `.strtab`, and the total ELF file size are unchanged, because
  `.symtab`'s 8-byte alignment padding absorbs the +2 growth before it.
  Twelve **local `$d` mapping symbols** inside these non-allocated debug
  sections move (ten pointing into `.debug_str`'s content, two into
  `.debug_line`'s); each is a zero-size (`st_size 0`) address-only marker used
  by the debugger/disassembler to delimit data within a debug section, not a
  defined `FUNC`/`OBJECT` symbol, not required or fixed by the accepted L8
  checker, and not part of the flat image.

None of these are runtime, flat-image, or accepted-checker-relevant facts:
they exist only in non-allocated ELF metadata consumed by offline tooling
(debuggers, `objdump -g`, symbolizers), never by the monitor at boot or by any
accepted R1-R5 mechanism. `tests/r6/check-fixture-image.mjs` does not pin
them and must not start pinning them; they are excluded from every R6
runtime/flat-image/symbol invariant above. They may optionally be recorded in
report metadata as observed facts, never as a pinned expectation or a runtime
claim.

### Corrected D-15 L8 expectation, pinned exactly

L8 compares the D-15 flat image against the same-toolchain control flat image.
Both are `212992` bytes. The **normative pinned expectation** is exactly **10
differing bytes in exactly 2 differing runs** per toolchain:

| Toolchain | Differing runs (flat-image offsets) | Differing bytes | `.monitor.text` size |
| --- | --- | --- | --- |
| GCC | `{start: 30032, length: 9}`, `{start: 30042, length: 1}` | 10 | `0x7610`, unchanged |
| Clang | `{start: 30080, length: 9}`, `{start: 30090, length: 1}` | 10 | `0x7640`, unchanged |

Flat offset `30032` is `0x7550`, i.e. virtual address `0x80207550` under GCC;
`30080` is `0x7580`, i.e. `0x80207580` under Clang. The delta decomposes as:

```text
control:  <off+0>  0100006f   j    <tail>+0x10      defect:  64526073  csrsi hvip,4
          <off+4>  00000013   nop                            60426073  csrsi hie,4
          <off+8>  00000013   nop                            0080006f  j <tail>+0x8
          <off+12> 00000013   nop                            00000013  nop
```

The two inserted words plus the first byte of the relocated `j` opcode form
the 9-byte run at `+0`. The byte at `+9` is coincidentally equal in both
images (`0x00`), and the jump immediate's next byte differs (`0x00` -> `0x80`),
which is the 1-byte run at `+10`. That coincidence is why the delta is two
runs rather than one, and why the pinned expectation is `{9}` then `{1}` and
not a single 11-byte range.

`tests/r6/check-fixture-image.mjs` must **pin all of this and fail closed**:
the toolchain's exact differing-run count (`2`), exact total differing-byte
count (`10`), and exact `{start, length}` pairs above, plus the unchanged
`.monitor.text` allocated size and the unchanged addresses of the accepted
checker's fixed and required allocated `FUNC`/`OBJECT` symbol sets. It pins
exactly those allocated sections and that fixed/required symbol set — never
the local `$d` debug-mapping symbols or any other non-allocated debug/symbol
content, which is out of scope for L8 by construction. Any extra differing
byte, any missing declared byte, any relocated offset, any third run, and any
`.monitor.text` size change is a **rejection**, not a tolerated variation.
The harness **must not** relax, widen, recompute, or auto-adopt an
observed delta at run time; a mismatch fails R6 and requires a further plan
revision, exactly like the wrong-error-class gate. Existing L8 mutation
self-tests remain mandatory and are extended to prove an extra byte, a missing
declared byte, and a wrong-offset delta are each rejected for D-15 under both
toolchains.

### Defect 2: the planned raw-trace retention is impossible

The accepted plan required retaining "the first trace log of each
fixture/toolchain pair (32 traces)" while also holding retained evidence to
**512 MiB**. A single R6 QEMU run traces `in_asm,cpu` for the whole boot,
which produces a raw log of roughly **310-370 MiB**. Thirty-two of them are
about **10.6-11.5 GiB**, and all 64 would be about **21 GiB** — 20x to 40x
over the plan's own cap. The two requirements are mutually unsatisfiable, so
the retention rule, not the cap, is wrong.

### Corrected retention rule: raw traces are ephemeral

Raw QEMU trace logs are **build scratch, never evidence**. For each of the 64
runs, `tests/r6/run-qemu.sh` writes the raw trace to a scratch path under
`build/r6/`, and `tests/r6/check-dynamic.mjs --extract` then derives from that
one raw trace, before the next run starts:

1. the **canonical semantics record** (`be-r6-run-semantics-v1`): console
   lines, marker sequence, failure line, VS entries, guest exits, root
   installs, final registers, any outside-guest-page observation, per-symbol
   execution counts, and the CPU-dump count;
2. the raw trace's **SHA-256**;
3. the raw trace's exact **byte count**;
4. a **bounded head/tail excerpt**: at most the first 400 and the last 800
   trace lines, each side labelled with fixture, toolchain, and run.

The raw trace is then **deleted**. It is never copied into
`build/r6/evidence/`, never digested into `artifacts.sha256` as a file, and
never published.

Retention under `build/r6/evidence/` is therefore: the report; all 64 console
logs; all 64 exit-status files; all **64** canonical semantics records (one
per run, each carrying its raw-trace SHA-256 and byte count); all **64**
bounded trace excerpts (one per run, matching the implemented safe design, so
no run's evidence is silently thinner than another's); the fixture catalogue
and per-fixture manifests; static rejection transcripts; the 30 scratch
preparation banners; image manifests; the coverage ledger; the claim ledger;
and `artifacts.sha256` over every retained byte. **No raw trace log is
retained under any circumstance.**

`<= 512 MiB` remains a **hard gate**, unchanged and unrelaxed: exceeding it is
a failure requiring plan revision, never a larger cap chosen after the fact.
The corrected set is comfortably inside it — the per-run retained artifacts
are tens of kilobytes each — but the gate is enforced by measurement, not by
this estimate. `tests/r6/generate-evidence.sh` must additionally fail closed
if any file matching a raw-trace path reaches the evidence tree, and
`tests/r6/check-report.mjs` must fail closed if any of the 64 runs lacks its
semantics record, its raw-trace digest, its raw-trace byte count, or its
bounded excerpt.

Report schema consequences (`be-r6-adversarial-images-v1`): each `dynamic[]`
and the `control` entry records `trace_sha256[]` **and** `trace_bytes[]`, one
per run, together with `trace_excerpt_sha256[]` and the explicit
`raw_trace_retained: false`. The R5 semantic-versus-byte boundary is inherited
unchanged, and **raw QEMU trace byte identity across launches remains an
explicit non-claim**: the per-run `trace_sha256` values are recorded as
observed facts about deleted scratch files, they are not expected to be equal
across runs or toolchains, and nothing in R6 asserts, verifies, or claims
byte-reproducible raw traces. Canonical semantics, console digests, and the
generated report remain the reproducible artifacts.

### Status of the measurements behind this revision

The dynamic implementation review that produced this revision observed, in the
local unreviewed working tree, that the resumed D-15 fixture builds and runs
as R6-A expects, that the flat-image delta is exactly the 10 bytes and two
runs pinned above under both pinned toolchains, that `.monitor.text` keeps its
accepted size, and that the harness already streams each raw trace into a
canonical semantics record, a SHA-256, a byte count, and a bounded excerpt
before deleting it.

Those observations are **local, unreviewed implementation discovery. They are
not accepted evidence, not a retained R6 evidence bundle, and they were not a
reason to accept this revision.** No R6 implementation commit exists, no
evidence bundle or claim is asserted, and the
[expected deterministic result](#expected-deterministic-result) table stays
`NOT RUN / unverified as retained R6 evidence`. This revision was accepted on
whether its corrected layout arithmetic, its pinned fail-closed L8
expectation, and its bounded retention rule are *right*, and the pinned values
must still be re-derived from a checked run at the exact implementation commit
rather than trusted from this text. If a checked run at that commit disagrees
with any pinned value, the fixture fails and the plan is revised again; the
harness must not adapt.

## Prerequisites and objective

| Prerequisite | Status |
| --- | --- |
| Fixed bounded runtime plan | accepted 2026-07-25 |
| R0 non-privileged freeze | accepted at `64a88b15a6c35d522fa997699c4fb514b15da314` |
| R1 pure-C mechanism | accepted at `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` |
| R2 Sv39x4 backend | accepted at `6e1cb579257c5dbe3234bd484fd091629e87181b` |
| R3 boot-and-first-entry | accepted at `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` |
| R4 trap-and-context | accepted at `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` |
| R5 plan | accepted at `fecae6b62a507bdbb93d211262197a31f5422316` |
| R5 decision record | `a8161e639af4a141e0d3ca1322202c91129724c7` |
| R5 checked switch | accepted at `165f4d001a2b59b582b397bdea79ec4826168fdb`, parent `9312c1355a23d411e3bdafb2183be342683a8ab9` |
| R5 review packet | `9bb89fe196740c5e3252bdccced6fb202df65e55`, not implementation |
| R5 acceptance record | `0cdd0736e9b56f83b4d2e96d3f93318acdc8cc9d`, not implementation |
| R6 plan | original target accepted at `609867fdad75279c0913022909efd65c4a838909`, accepted history and byte unchanged; corrected target carrying D-15 revision R6-A **accepted at `75269f058ae578b0a76a113d6c05c0aaceeac8ec`** on 2026-07-30; [revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention) **accepted at `6d6464c6c937abccd59df932006c1049fd79fac6`** on 2026-07-30 |
| R6 implementation | authorized; started locally, unreviewed, unaccepted, incomplete; D-15 resumed under the accepted corrected plan, and R6 integration and evidence work may continue under the accepted revised plan with every pinned value re-derived at the exact implementation commit |
| R7 | gated, undefined, not authorized |

The master plan defines R6 as exactly one row:

```text
R6: adversarial images | malformed input, partial publication, wrong binding,
    skipped fence, unexpected trap/event, and denied-access fixtures | R1-R5
```

R6 is therefore **test and evidence work over the accepted R5 mechanism**, not
a new production runtime architecture. It adds no runtime behavior, no policy,
no scheduling, no restart, no rollback, no dynamic binding, no root edit, no
PTE write, no guest SBI, and no later-package behavior.

R6's objective is a finite, separately linked, single-defect adversarial fixture
catalogue that demonstrates the accepted R5 assurance surface either **rejects
the defective construction before execution** or **terminates fail-closed with
the exact stable error class**, for every defect family named in the master-plan
row.

## Decision: no new production-like R6 surface

**Decision (must be confirmed at review):** R6 adds **no** `include/be/r6.h`,
**no** `virt/be/r6.c`, and **no** `arch/riscv/be/r6-*` file. R6 modifies no byte
of `include/`, `virt/`, or `arch/`. Every R6 artifact lives under `tests/r6/`,
plus bounded integration lines in the root `Makefile`, the root `be` wrapper,
and `scripts/check-be.sh`.

Justification:

1. **Scope fidelity.** The master-plan row is adversarial *images*, i.e. inputs
   presented to the accepted mechanism. Adding a production header or core file
   would create R6 runtime behavior the row does not authorize.
2. **Accepted gates already forbid it.** `tests/r5/check-sources.mjs` rejects
   any `be_r6`/`BE_R6` identifier in the R5 source inventory, and
   `tests/r5/check-image.mjs` rejects any image symbol matching
   `(^|_)r6(_|$)` or `be_r6`. A production R6 surface would either break the
   accepted R5 gates or force edits to accepted files.
3. **No defect-injection path in the mechanism under test.** Any R6 hook inside
   accepted R5 runtime would place a test-only branch inside the exact bytes
   whose behavior R6 claims to measure, and would invalidate the R5 acceptance
   boundary.
4. **Stronger evidence.** A separately built fixture image proves the defect
   exists only in that image, while `tests/r5/check-acceptance.sh` independently
   proves the accepted image inputs are unchanged.

**Corollary (mandatory).** Fixture sources must keep every accepted R5 symbol
name verbatim. R6 identity appears only in paths, manifests, report fields, and
harness output. A fixture that renamed symbols to `be_r6_*` would be rejected by
the accepted image checker for the wrong reason and would mask its single
intended defect.

### Immutable accepted bytes

The following must be byte-and-mode identical to accepted R5 target
`165f4d001a2b59b582b397bdea79ec4826168fdb` for the entire R6 package, as
verified by `tests/r5/check-acceptance.sh --require` before any fixture is
built:

- the 43 immutable paths pinned by `tests/r5/check-accepted-content.mjs`,
  covering `arch/riscv/be/{freestanding.c,platform.c,privileged.S,r0-layout.h,
  r0-registers.h,r5-beryllium.lds,r5-entry.S,r5-guest.S,r5-platform.h,
  r5-runtime.c,r5-trap.S,sv39x4.c}`, `include/be/{manifest.h,r1-config.h,r2.h,
  r3.h,r4.h,r5.h,state.h,types.h}`, `virt/be/{manifest.c,r1-config.c,r3.c,r4.c,
  r5.c,state.c}`, and the whole `tests/r5/` harness inventory;
- the 6 mixed R5 acceptance-record files bound by exact approved
  target-to-current deltas, plus `tests/r5/check-accepted-content.mjs` itself,
  which is bound through the deterministic content digest and its own asserted
  identities;
- every accepted R0-R4 mechanism input bound by `tests/r1/check-acceptance.sh`,
  `tests/r2/check-acceptance.sh`, `tests/r3/check-accepted-content.mjs`, and
  `tests/r4/check-accepted-content.mjs`, including `include/be/r0-config.h`,
  `include/be/r1.h`, `virt/be/r1.c`, and `virt/be/r2.c`.

R6 deliberately does **not** claim that every file under `tests/r0/` through
`tests/r4/` is immutable. Six predecessor acceptance-pin constants in three
predecessor files are in scope, and only for the exact refresh authorized in
the next section.

R6 may modify only: `tests/r6/**` (new), root `Makefile`, root `be`,
`scripts/check-be.sh`, the six enumerated acceptance-pin constants in
`tests/r1/check-acceptance.sh`, `tests/r3/check-accepted-content.mjs`, and
`tests/r4/check-accepted-content.mjs`, `planning/**` documentation,
`planning/.vitepress/**`, `pathfinder/tests/check-docs-render.mjs`,
`README.md`, `.github/copilot-instructions.md`, and generated `docs/html/**`.

### Authorized acceptance-pin refresh

The root integration this plan requires is not free: three predecessor
acceptance checkers bind the exact files R6 must edit.

| Bound file | Bound by | Binding form |
| --- | --- | --- |
| root `Makefile` | `tests/r1/check-acceptance.sh` | one exact successor mode (`644`) and one exact SHA-256 |
| `be` | `tests/r3/check-accepted-content.mjs`, `tests/r4/check-accepted-content.mjs` | approved target-to-current delta SHA-256, one per checker |
| `scripts/check-be.sh` | `tests/r3/check-accepted-content.mjs`, `tests/r4/check-accepted-content.mjs` | approved target-to-current delta SHA-256, one per checker |
| `tests/r1/check-acceptance.sh` | `tests/r3/check-accepted-content.mjs` | approved target-to-current delta SHA-256 |

Because `tests/r5/check-acceptance.sh` reports `r5_dependencies_match` only
when R1-R4 all report `--require` success, an unrefreshed pin would flip
`r1_acceptance` to `review-required` and therefore flip
`r5_acceptance` to `review-required` and `r5_accepted_mechanism_match` to
`no`. That is a dependency-status regression, not an R5 mechanism change.

**Authorized refresh (exactly six constants, no others).** This follows the
accepted R5 precedent: implementation commit
`9312c1355a23d411e3bdafb2183be342683a8ab9` edited the root `Makefile`, `be`,
and `scripts/check-be.sh`, then refreshed `successor_makefile_sha256` in
`tests/r1/check-acceptance.sh` and the `be`, `scripts/check-be.sh`, and
`tests/r1/check-acceptance.sh` approved deltas in
`tests/r3/check-accepted-content.mjs` and
`tests/r4/check-accepted-content.mjs`.

| # | File | Constant | Reason |
| --- | --- | --- | --- |
| 1 | `tests/r1/check-acceptance.sh` | `successor_makefile_sha256` | root `Makefile` gains the R6 targets and the R6 `check` step |
| 2 | `tests/r3/check-accepted-content.mjs` | approved delta for `tests/r1/check-acceptance.sh` | constant 1 changed that file |
| 3 | `tests/r3/check-accepted-content.mjs` | approved delta for `be` | `be` gains R6 subcommands, help, and status fields |
| 4 | `tests/r3/check-accepted-content.mjs` | approved delta for `scripts/check-be.sh` | `scripts/check-be.sh` gains R6 assertions |
| 5 | `tests/r4/check-accepted-content.mjs` | approved delta for `be` | same `be` edit, second binding |
| 6 | `tests/r4/check-accepted-content.mjs` | approved delta for `scripts/check-be.sh` | same `scripts/check-be.sh` edit, second binding |

The R5 precedent additionally had to teach
`tests/r4/test-acceptance-content.mjs` to copy `tests/r1/check-acceptance.sh`
and the root `Makefile` into its isolated negative worktree, and to refresh
that file's `addedFiles` delta, because R5 was the first successor to edit the
shared successor command graph. That structural fix is permanent and already
accepted: `tests/r4/test-acceptance-content.mjs` copies every `mixedFiles` and
`addedFiles` path plus those two files, and
`tests/r3/test-acceptance-content.mjs` already copies and drift-tests the root
`Makefile`. Independently, the accepted `tests/r5/test-acceptance-content.mjs`
declares a `supportingPaths` list holding exactly `be`,
`scripts/check-be.sh`, `tests/r1/check-acceptance.sh`,
`tests/r3/check-accepted-content.mjs`, `tests/r4/check-accepted-content.mjs`,
and `Makefile`, and copies the **current** worktree versions into its isolated
baseline for the stated reason that otherwise "the bound R3/R4 packages would
report drift for reasons unrelated to the R5 mutation under test". The
accepted R5 self-tests are therefore already structurally prepared for exactly
this refresh. R6 makes the same three root edits and therefore needs **no**
change to any predecessor self-test and **no** seventh constant. If a future
check proves otherwise, R6 must stop and request an amended authorization
rather than widen the refresh set on its own.

No other byte of `tests/r1/`, `tests/r3/`, or `tests/r4/` may change. In
particular the R1 accepted-commit constant, the R3/R4 accepted-commit,
parent, packet, and date constants, every `immutablePaths` entry, every other
`mixedFiles` entry, and every `addedFiles` entry stay exactly as accepted.

**Mandatory ordering.** The R6 implementation commit must perform these steps
in this order, and `tests/r6/check-baseline.sh` must refuse to proceed if any
step is out of order or incomplete:

1. Record pre-edit evidence: `tests/r1/check-acceptance.sh --require`,
   `tests/r2/check-acceptance.sh --require`,
   `tests/r3/check-acceptance.sh --require`,
   `tests/r4/check-acceptance.sh --require`, and
   `tests/r5/check-acceptance.sh --require` all pass, with
   `r5_acceptance=accepted` and `r5_accepted_mechanism_match=yes`, and retain
   `r5_implementation_content_digest`.
2. Edit root `Makefile`, `be`, and `scripts/check-be.sh` only.
3. Recompute and replace exactly the six constants above.
4. Re-run all five acceptance checkers; every one must pass, with
   `r1_accepted_mechanism_match=yes`, `r3_accepted_mechanism_match=yes`,
   `r4_accepted_mechanism_match=yes`, `r5_acceptance=accepted`,
   `r5_accepted_mechanism_match=yes`, `r5_dependencies_match=yes`, and an
   unchanged `r5_implementation_content_digest`.
5. Only then create `tests/r6/**`.

**Mandatory negative checks.** `tests/r6/check-baseline.sh` and
`tests/r6/test-acceptance-pins.mjs` must prove, in a scratch worktree and
without editing accepted files:

- `git diff --numstat <accepted-R5-target> -- <every immutable R5 path>` is
  empty, and the same holds for every path bound by the R1, R2, R3, and R4
  checkers except the four files in the table above;
- exactly the six enumerated constants differ from the accepted R5 target in
  `tests/r1/check-acceptance.sh`, `tests/r3/check-accepted-content.mjs`, and
  `tests/r4/check-accepted-content.mjs`, each matching
  `^[0-9a-f]{64}$` and each differing from its pre-R6 value;
- reverting any one of the six constants makes its owning checker fail
  `--require`, proving the pins are live rather than decorative;
- reverting the R6 lines in root `Makefile`, `be`, or `scripts/check-be.sh`
  without reverting the matching constant also fails, proving the refresh is
  bound in both directions;
- `r5_implementation_content_digest` is byte-identical before and after the
  R6 package, proving no accepted R5 mechanism byte moved.

R6 must not add, remove, or reorder any entry in `immutablePaths`,
`mixedFiles`, `addedFiles`, or `acceptancePaths`, and must never edit
`tests/r5/check-acceptance.sh`, `tests/r5/check-accepted-content.mjs`, or any
other R5 acceptance surface.

## Inherited frozen facts

Every value below is inherited from accepted R0-R5 and must not be redefined by
R6. Fixtures cite these values; they do not invent alternatives except where the
"newly selected" table says so.

### Domains and roots

| Property | Management | Protected |
| --- | --- | --- |
| Root identifier | `101` | `102` |
| Root pool PA | `0x80214000` | `0x8021c000` |
| HGATP | `0x8000000000080214` | `0x800000000008021c` |
| VMID | `0` | `0` |
| vCPU identifier | `1` | `2` |
| Saved-state identifier | `1` | `2` |
| Saved-state PA | `0x8022b000` | `0x8022c000` |
| Trusted SP | `0x80227000` | `0x8022a000` |
| Initial guest SP | `0x40001000` | `0x40002000` |
| Entry PC | `0x40010000` | `0x40011000` |

### G-stage mappings

| Root | GVA/GPA | PA | Rights |
| --- | --- | --- | --- |
| Management | `0x40000000` | `0x8022e000` | read, write |
| Management | `0x40002000` | `0x80230000` | read, write |
| Management | `0x40010000` | `0x80232000` | read, execute |
| Protected | `0x40001000` | `0x8022f000` | read, write |
| Protected | `0x40002000` | `0x80230000` | read only |
| Protected | `0x40011000` | `0x80233000` | read, execute |

`htval = GPA >> 2`. Inherited: `0x40000000` -> `0x10000000`, `0x40001000` ->
`0x10000400`, `0x40002000` -> `0x10000800`.

### Frozen instruction slots

Management fixture at `0x40010000` (`.guest.r5.management`, 16 slots,
`0x40` bytes):

| PC | Instruction |
| --- | --- |
| `0x40010000` | `lui t0, 0x40000` |
| `0x40010004` | `addi t1, zero, 17` |
| `0x40010008` | `sw t1, 0(t0)` |
| `0x4001000c` | `lw s0, 0(t0)` |
| `0x40010010` | `lui t2, 0x40001` |
| `0x40010014` | `lw s1, 0(t2)` (denied, R4 fault PC) |
| `0x40010018` | `lui t2, 0x40002` |
| `0x4001001c` | `addi t1, zero, 34` |
| `0x40010020` | `sw t1, 0(t2)` |
| `0x40010024` | `lw a1, 0(t2)` |
| `0x40010028` | `addi a0, s0, 0` |
| `0x4001002c` | `addi a7, zero, 1` |
| `0x40010030` | `ecall` (R4 private event) |
| `0x40010034` | `addi a7, zero, 3` |
| `0x40010038` | `ecall` (final event) |
| `0x4001003c` | `j .` (must not execute) |

Protected fixture at `0x40011000` (`.guest.r5.protected`, 14 slots,
`0x38` bytes):

| PC | Instruction |
| --- | --- |
| `0x40011000` | `lui t0, 0x40001` |
| `0x40011004` | `addi t1, zero, 51` |
| `0x40011008` | `sw t1, 0(t0)` |
| `0x4001100c` | `lw s0, 0(t0)` |
| `0x40011010` | `lui t2, 0x40000` |
| `0x40011014` | `lw s1, 0(t2)` (denied load, cause 21) |
| `0x40011018` | `lui t2, 0x40002` |
| `0x4001101c` | `lw a1, 0(t2)` (reads 34) |
| `0x40011020` | `addi t1, zero, 68` |
| `0x40011024` | `sw t1, 0(t2)` (denied store, cause 23) |
| `0x40011028` | `addi a0, s0, 0` |
| `0x4001102c` | `addi a7, zero, 2` |
| `0x40011030` | `ecall` (switch event) |
| `0x40011034` | `j .` (saved, not executed) |

Both slot tables are frozen **by encoding**, not by mnemonic. The accepted
`tests/r5/check-image.mjs` pins the exact little-endian words:

```text
management  400002b7 01100313 0062a023 0002a403 400013b7 0003a483 400023b7
            02200313 0063a023 0003a583 00040513 00100893 00000073 00300893
            00000073 0000006f
protected   400012b7 03300313 0062a023 0002a403 400003b7 0003a483 400023b7
            0003a583 04400313 0063a023 00040513 00200893 00000073 0000006f
```

Every guest-opcode R6 fixture changes exactly one of these 30 words, and the
manifest records the base word, the defect word, and the file offset. This is
also why the accepted image checker rejects those images before QEMU, which
the per-partition applicability rules below handle explicitly.

### Accepted console marker sequence

The exact 22-line accepted sequence, verbatim from the accepted
`tests/r5/check-qemu-artifacts.mjs` `expectedConsole` array. R6 fixtures cite
these lines; no fixture may invent a marker name.

```text
 1  BE_R3:01 BOOT_VALIDATED
 2  BE_R3:02 R1_DERIVED
 3  BE_R3:03 R2_BUILT_REWALKED
 4  BE_R3:04 HS_VS_STATE_VERIFIED
 5  BE_R3:05 BINDING_PREPARED
 6  BE_R3:06 HGATP_FENCED_PUBLISHED
 7  BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000
 8  BE_R4:01 ENTRY_ARMED_IMPORTED
 9  BE_R4:02 EXPECTED_DENIED_LOAD pc=0x40010014 resume=0x40010018
10  BE_R4:03 PRIVATE_EVENT pc=0x40010030 resume=0x40010034
11  BE_R5:01 R4_COMPLETE_IMPORTED sepc=0x40010034
12  BE_R5:02 PENDING_PROTECTED direction=management-to-protected
13  BE_R5:03 PROTECTED_HGATP_WRITTEN_FENCED_READBACK
14  BE_R5:04 PROTECTED_TARGET_VERIFIED pc=0x40011000
15  BE_R5:05 EXPECTED_DENIED_LOAD pc=0x40011014 resume=0x40011018
16  BE_R5:06 EXPECTED_DENIED_SHARED_STORE pc=0x40011024 resume=0x40011028
17  BE_R5:07 SWITCH_EVENT pc=0x40011030 saved=0x40011034
18  BE_R5:08 PENDING_MANAGEMENT direction=protected-to-management
19  BE_R5:09 MANAGEMENT_HGATP_WRITTEN_FENCED_READBACK
20  BE_R5:10 MANAGEMENT_TARGET_VERIFIED pc=0x40010034
21  BE_R5:11 FINAL_EVENT pc=0x40010038 s0=17 a0=17 a1=34 shared=34 protected=51
22  BE_R5:12 SHUTDOWN type=0 reason=0
```

Emission points that fix every declared "last marker" below, read from
`arch/riscv/be/r5-runtime.c`:

- line 8 (`BE_R4:01`) is emitted before `be_r3_arch_enter_management`, so it
  precedes the first guest instruction;
- line 9 (`BE_R4:02`) is emitted only after the accepted R4 phase machine
  validated the management denied load;
- line 10 (`BE_R4:03`) is emitted only after `be_r4_handle_trap` accepted the
  management private event, so an R4-rejected private event stops at line 9;
- lines 12-14 and 18-20 are emitted inside `switch_domain` after
  `be_r5_prepare_pending`, after `be_r5_note_target_fenced`, and after the
  `be_r5_arch_reset_target` saved-page check, all strictly before
  `be_r5_publish_target`;
- lines 15-17 and 21 are emitted only after `be_r5_handle_exit` accepted the
  corresponding exit, so a rejected exit stops at the preceding line.

The accepted forbidden set is `BE_R3:FAIL`, `BE_R4:FAIL`, `BE_R5:FAIL`,
`BE_R5:SRST_RETURNED`, `GENERAL_GUEST_SBI`, `HGATP_WRITE_AFTER_ENTRY`,
`HFENCE_AFTER_ENTRY`, `PROTECTED_PRIVATE_READ_BY_MANAGEMENT`, and
`SHARED_STORE_BY_PROTECTED`. A dynamic R6 fixture inverts exactly one of
these: it must print `BE_R5:FAIL <error-name>` and then take the accepted
terminal SRST path. `BE_R5:SRST_RETURNED` remains forbidden in every R6 run.

### Stable error vocabulary

The 29 non-`none` values of `enum be_r5_error`, as spelled by
`be_r5_error_name()`:

```text
null            invalid-phase   import          binding         pending
trusted-stack   saved-page      hgatp           vs-origin       vsatp
frame-reserved  frame-state     fence           target-readback target-reset
entry-controls  publication     hart            interrupt       cause
pc              gva             htval-overflow  gpa             trap-metadata
event-args      backing         shutdown-returned               shutdown-rejected
```

Validation order inside `be_r5_handle_exit` (which fixes every expected class):
`state` null -> sticky phase -> exit phase -> remaining nulls (`frame`,
`observation`, `result`) -> identities-intact -> pending-clear -> binding ->
frame reserved -> observation -> interrupt bit -> backing -> phase-specific
(`validate_denied_access`: cause, pc, gva, htval-overflow, gpa;
`validate_event`: cause, pc, trap metadata, event args) -> resume PC.

Order inside `be_r5_note_target_fenced`: pending -> binding -> `hgatp` ->
`fence` -> `target-readback`. Order inside `be_r5_publish_target`: phase ->
null -> import -> pending -> binding -> publication -> entry state -> frame.

### Newly selected R6 values

| Value | Selection | Use |
| --- | --- | --- |
| GPA `0x40003000` | unmapped in both roots | wrong-target denied load (D-03) |
| htval `0x10000c00` | `0x40003000 >> 2` | expected metadata for D-03 |
| GPA `0x00000000` | unmapped, `t2` reset value | wrong-PC denied load (D-07) |
| htval `0x00000000` | `0 >> 2` | expected metadata for D-07 |
| Event id `9` | outside `{1,2,3}` | wrong protected event (D-01) |
| Event id `4` | outside `{1,2,3}` | wrong management final event (D-09) |
| Private value `52` | `51 + 1` | wrong backing observation (D-02) |
| scause `0x8000000000000002` | VS software interrupt, `hideleg=0`, HS destined | unexpected interrupt (D-15) |
| `csrsi hvip, 4` then `csrsi hie, 4` | `VSSIP`/`VSSIE` bit 2 set with a 5-bit immediate, so no GPR is read or written | D-15 injection in the published tail |
| Root pool origin `0x80220000` | `0x8021c000 + 0x4000` | malformed layout (S-01) |
| Guest section origin `0x80234000` | `0x80233000 + 0x1000` | malformed layout (S-02) |
| `.saved.protected` size `0x2000` | `0x1000 * 2` | malformed layout (S-03) |

Guest-slot word selections, each replacing exactly one frozen word:

| Fixture | Slot | Base word | Defect word | Defect instruction |
| --- | --- | --- | --- | --- |
| D-01 | `0x4001102c` | `00200893` | `00900893` | `addi a7, zero, 9` |
| D-02 | `0x40011004` | `03300313` | `03400313` | `addi t1, zero, 52` |
| D-03 | `0x40011010` | `400003b7` | `400033b7` | `lui t2, 0x40003` |
| D-04 | `0x40011014` | `0003a483` | `0093a023` | `sw s1, 0(t2)` |
| D-05 | `0x40011028` | `00040513` | `00038067` | `jr t2` |
| D-06 | `0x40011028` | `00040513` | `68002573` | `csrr a0, hgatp` |
| D-07 | `0x40011010` | `400003b7` | `0003a483` | `lw s1, 0(t2)` |
| D-08 | `0x40010028` | `00040513` | `00000513` | `addi a0, zero, 0` |
| D-09 | `0x40010034` | `00300893` | `00400893` | `addi a7, zero, 4` |

D-07 replaces the `lui t2` that precedes the protected denied load, so the
denied load executes with `t2` at its reset value `0`; the slot at
`0x40011014` itself is untouched, keeping the change to one word.

Every base and defect word above was assembled with the accepted
`-march=rv64imac_zicsr_zifencei -mabi=lp64` and `.option norvc` and verified
against the frozen arrays in `tests/r5/check-image.mjs`. `zicsr` is already in
the accepted `MARCH`, so D-06's `csrr a0,hgatp` assembles under the accepted
flags and cannot fail at compile.


## Fixture model

### Construction

Each fixture is a directory `tests/r6/fixtures/<id>/` containing:

- `fixture.json` — stable identifier, partition, base file path, the single
  declared defect, the expected detection layer, the expected terminal outcome
  and diagnostic, the expected and forbidden markers, `qemu: true|false`, and
  for every image-producing fixture the `accepted_image_check` disposition
  (`pass`, or `reject-with` plus the exact expected assertion message) and the
  `declared_delta` descriptor consumed by the L8 differential checker;
- exactly one `*.defect` file — a full copy of exactly one accepted base file
  carrying exactly one defect;
- pinned digests — accepted-base SHA-256, defect-file SHA-256, unified-diff
  SHA-256, and a bounded change budget of at most 6 added and 6 removed lines.

The base file path is **per fixture**, not per partition: a fixture names
exactly one accepted file from the immutable inventory, and no partition
assumes a shared base. The dynamic partition therefore spans
`arch/riscv/be/r5-guest.S` (D-01..D-09), `arch/riscv/be/r5-runtime.c`
(D-10..D-14), and `arch/riscv/be/r5-trap.S` (D-15). D-15's defect file is
`tests/r6/fixtures/D-15/r5-trap.S.defect`, and its declared change is exactly
one contiguous `+2 / -0` hunk.

Nothing is patched in place. `tests/r6/build-fixture.sh` first runs
`tests/r6/prepare-scratch.sh <id>`, which materializes and confines a scratch
tree under `build/r6/scratch/<id>/` to the contract in the next section, then
overlays the single `*.defect` file and builds there, so the real worktree
stays byte immutable and the *accepted* checkers are the ones that reject the
defect.

### Scratch tree and accepted build reuse

The scratch tree mirrors the repository layout exactly, because the accepted
`tests/r5/check-sources.mjs` resolves its inventory from `../../` relative to
its own location, the accepted `tests/r5/Makefile` resolves `ROOT := ../..`
and `BUILD := $(ROOT)/build/r5` the same way, and the accepted
`tests/r5/tool-lock.mjs` resolves `root` as `../..` and then imports
`../r3/tool-lock.mjs`. A flat or renamed scratch layout would make the
accepted checkers report the wrong thing.

**Scratch source inventory (5 components, all byte-and-mode identical to the
real worktree except the single overlaid `*.defect` file):**

| # | Copied into the scratch root | Why the accepted graph needs it |
| --- | --- | --- |
| 1 | `arch/` | image inventory, `arch/riscv/be/r5-beryllium.lds` read directly by `check-image.mjs` |
| 2 | `include/` | image inventory and `-I$(ROOT)/include` |
| 3 | `virt/` | image inventory and host sources |
| 4 | `tests/r5/` (whole directory) | `check-sources.mjs` reads `tests/r5/Makefile` and `tests/r5/r5-check.c`; the file targets need `check-image.mjs`, `check-image-parity.mjs`, `make-control.mjs`, `tool-lock.mjs`, and `tool-lock.conf` |
| 5 | `tests/r3/tool-lock.mjs` and `tests/r3/tool-lock.conf` | `tests/r5/tool-lock.mjs` statically imports `../r3/tool-lock.mjs` and resolves `baseToolLockPath` as `<root>/tests/r3/tool-lock.conf` |

Component 5 is not optional and is not satisfied by the real worktree copies:
Node resolves the import relative to the scratch file, and
`loadToolLock()` asserts that the scratch `tests/r3/tool-lock.conf` digest
equals both the `R5_BASE_TOOL_LOCK_SHA256` value in `tests/r5/tool-lock.conf`
and the `expectedToolLockSha256` constant frozen inside
`tests/r3/tool-lock.mjs`. `tests/r6/prepare-scratch.sh` therefore verifies the
scratch copy of `tests/r3/tool-lock.conf` against the literal digest
`c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b` **and**
against the real-worktree file, so a dropped, redirected, truncated, or stale
lock file is refused before any pinned executable runs.

No other file of `tests/r3/` is copied. `tests/r3/verify-tool-lock.mjs`,
`tests/r5/check-tools.sh`, `tests/r5/prepare-scratch.sh`, and
`tests/r5/check-acceptance.sh` are reached only from accepted phony targets,
which R6 never invokes in the scratch tree.

**Scratch and output components (16, created parent-first).**
`tests/r6/prepare-scratch.sh <fixture-id>` is the single creator; every other
R6 checker validates and never creates. It holds the same contract as the
accepted `tests/r5/prepare-scratch.sh` and extends it to the scratch root:

| Order | Component | Rooted at |
| --- | --- | --- |
| 1-4 | `build`, `build/r6`, `build/r6/scratch`, `build/r6/scratch/<id>` | repository root |
| 5-11 | `build`, `build/r3`, `build/r5`, `build/r3/tool-home`, `build/r3/tmp`, `build/r5/home`, `build/r5/tmp` | `build/r6/scratch/<id>/` |
| 12-16 | `build/r6/reports`, `build/r6/evidence`, `build/r6/static`, `build/r6/dynamic`, `build/r6/control` | repository root |

Components 5-11 are exactly, and in the same order as, the `scratchComponents`
array exported by the accepted `tests/r5/tool-lock.mjs`. Its `requireScratch()`
helper is the load-bearing fail-closed check: it is invoked by both
`cleanEnvironment()` and `inheritedCleanEnvironment()` and inspects all seven
R3/R5 scratch components before either returns. The accepted `tests/r5/Makefile`
does run a parse-time `make-control.mjs` probe with
`HOME="$(CURDIR)/../../build/r5/home"` and
`TMPDIR="$(CURDIR)/../../build/r5/tmp"`, but that probe validates the calling
cwd, the pinned-Make ancestry, Make flag words, and the ambient environment;
it never calls `stat` on either path, so it does not establish, and cannot
substitute for, scratch-directory existence. Accepted checker invocations such
as `check-image.mjs` import `cleanEnvironment` and call it at module load, so
they unconditionally require `requireScratch()` to pass and therefore refuse
missing, symbolic-linked, or otherwise unusable scratch before any semantic
check runs. R6 materialization and preparation must therefore complete before
any accepted file target is invoked, and a resulting `requireScratch()` fault
must be diagnosed as a scratch fault under its own component name, never
mistaken for tool version drift (see Diagnostics below).

For each component, in order, `tests/r6/prepare-scratch.sh` must refuse a
symbolic link before traversing it, create it with the pinned `/usr/bin/mkdir`,
re-check that it did not become a symbolic link, require a directory, require
it to be writable and searchable, and require its physical `pwd -P` path to
equal the expected path, so no component can be redirected outside the
repository. Files are materialized by `tests/r6/materialize-scratch.mjs` under
the pinned `/usr/bin/node`, because `cp` and `chmod` are deliberately not bound
roles in the accepted R3 lock; it copies content and mode and then re-reads
each destination to assert byte and mode equality with its source.

**Environment.** `tests/r6/prepare-scratch.sh` prints
`BE_R6_SCRATCH: PASS id=<ID> components=16 sources=5 base-lock=verified
copies=<n>` on success and exports nothing implicitly. `build-fixture.sh`
derives and passes exactly:

```text
R6_SCRATCH_ROOT=<repo>/build/r6/scratch/<id>
HOME=$R6_SCRATCH_ROOT/build/r5/home
TMPDIR=$R6_SCRATCH_ROOT/build/r5/tmp
PATH=/usr/bin  LC_ALL=C  LANG=C
```

and invokes the accepted graph as
`/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C HOME=... TMPDIR=...
/usr/bin/make -C "$R6_SCRATCH_ROOT/tests/r5" <file-target>`, which is the same
launcher shape the accepted `tests/r5/run-make.sh` uses. `HOME` and `TMPDIR`
are never the real-worktree `build/r5` paths, so an R6 run cannot disturb
accepted R5 scratch, and never `/tmp`.

**Diagnostics: a missing scratch is never version drift.** The accepted R3
clean environment names `build/r3/tool-home` and `build/r3/tmp` without
creating them, and the accepted R3 version reader prefers stderr, so an absent
component makes a pinned tool's warning look like an executable identity
failure. R6 therefore requires that:

1. every fault above is reported as
   `R6 scratch environment: <component> <detail>` on stderr with a non-zero
   exit, and every base-lock fault as
   `R6 scratch environment: tests/r3/tool-lock.conf <detail>`;
2. `build-fixture.sh` refuses to invoke any accepted target for a fixture
   until `prepare-scratch.sh` has printed its PASS banner for that fixture in
   the same run;
3. a scratch or base-lock fault is recorded as the forbidden outcome
   `scratch-fault` and is never recorded as a layer rejection, a declared
   disposition, a `layer-shift`, a `wrong-error-class`, or a tool version
   drift, and never counted in any fixture, layer, or coverage total.

R6 does **not** invoke the accepted phony targets in the scratch tree.
`r5-toolcheck` ends with `./check-acceptance.sh --require`, which is a
statement about the real worktree and cannot hold for a deliberately mutated
copy, and `r5-host-test`, `r5-image`, `r5-image-check`, `r5-qemu`,
`r5-report`, `r5-evidence`, and `r5-check` all depend on it. R6 instead
invokes the accepted **file** targets, which have no such dependency:

- `$(BUILD)/gcc/beryllium.elf` and `$(BUILD)/clang/beryllium.elf` for compile
  and link, giving byte-identical `TARGET_FLAGS`, `LINK_FLAGS`, linker script,
  `objcopy`, `objdump`, and `size` invocations by reuse rather than by copy;
- `$(BUILD)/image-check/gcc.json`, `$(BUILD)/image-check/clang.json`, and
  `$(BUILD)/image-check/parity.txt` for L6 and L7.

The accepted phony targets stay unused for every mutated image, and
`tests/r6/check-sources.mjs` must prove it: no R6 file may name
`r5-toolcheck`, `r5-host-test`, `r5-image`, `r5-image-check`, `r5-qemu`,
`r5-report`, `r5-evidence`, `r5-check`, or `tests/r5/run-make.sh` as a target
or command for a scratch tree. The accepted R5 QEMU graph is invoked only for
the unmutated R5 baseline in the real worktree.

Accepted `tests/r5/check-sources.mjs` is invoked directly in the scratch tree
for L3, under the same R6 pinned, hardened environment and scratch and
source-boundary controls described above. This direct invocation parses no
Makefile, so the accepted `tests/r5/Makefile`'s parse-time `make-control.mjs`
guard does not apply on this path; nothing here should be read as claiming
that it does.

Accepted `$(BUILD)/...` file-target invocations for compile, link, image
check, and parity (L4 through L7) are different: each is a
`make -C "$R6_SCRATCH_ROOT/tests/r5" <file-target>` call as shown above, so it
does parse the accepted `tests/r5/Makefile` in the scratch tree and therefore
inherits its parse-time hostile-control guards in `make-control.mjs`, in
addition to the R6 launcher controls described elsewhere. R6 never copies the
accepted flags into an R6-owned recipe, so accepted build semantics cannot
drift.

For fixtures declared to fail at L3 or L5, R6 asserts that the corresponding
build artifacts do not exist afterwards, so "rejected" cannot silently mean
"built anyway".

`tests/r6/check-fixtures.mjs` proves, for every catalogue entry, that the base
digest matches the current accepted file, that exactly one file differs, that
the diff is within budget, and that the declared defect description matches the
diff. A fixture whose defect file equals its base is rejected as `no-defect`; a
fixture with a second undeclared change is rejected as `multiple-defects`.

`tests/r6/check-sources.mjs` additionally proves, for every fixture actually
built, that the scratch tree held all 5 source components with byte-and-mode
identical content apart from the single overlaid defect file, that all 16
components existed and were confined, and that the scratch `tests/r3` copy
contained exactly `tool-lock.mjs` and `tool-lock.conf` at the verified digest.

### Detection layers

The layers below are the accepted R5 pipeline in its real execution order, as
defined by `tests/r5/Makefile` (`r5-toolcheck` -> `r5-host-test` ->
`r5-image` -> `r5-image-check` -> `r5-qemu` -> `r5-report`), with the six
R6-owned layers (L1, L2, L8, L9, L10, L11) placed where they actually run.
Source inventory is deliberately first: the accepted
`tests/r5/check-sources.mjs` runs inside `r5-toolcheck`, strictly before any
compilation. Scratch preparation is a **precondition of L3 through L10, not a
layer**: it runs before L3 for every image-path fixture, it detects no defect,
and a failure there is a `scratch-fault` rather than any layer result.

| Layer | Stage | Mechanism | Owner | Role |
| --- | --- | --- | --- | --- |
| L1 | baseline immutability | `tests/r6/check-baseline.sh` over `tests/r5/check-acceptance.sh --require` | R6 | pass-through gate |
| L2 | catalogue integrity | `tests/r6/check-fixtures.mjs` | R6 | pass-through gate |
| L3 | source inventory and generation | accepted `tests/r5/check-sources.mjs` in the scratch tree | accepted R5 | rejection layer |
| L4 | compile | pinned `riscv64-linux-gnu-gcc` / `clang --target=riscv64` | pinned toolchains | pass-through invariant |
| L5 | link | pinned GNU `ld` / `lld` with `arch/riscv/be/r5-beryllium.lds` `ASSERT`s | accepted R5 | rejection layer |
| L6 | static image semantics | accepted `tests/r5/check-image.mjs` | accepted R5 | rejection layer, and mandatory disposition check for every image |
| L7 | toolchain parity | accepted `tests/r5/check-image-parity.mjs` | accepted R5 | pass-through invariant |
| L8 | single-delta differential | `tests/r6/check-fixture-image.mjs` | R6 | rejection layer for undeclared drift |
| L9 | QEMU artifact production | `tests/r6/run-qemu.sh` | R6 | execution stage |
| L10 | dynamic semantics | `tests/r6/check-dynamic.mjs` | R6 | rejection layer |
| L11 | host mechanism | `tests/r6/r6-check.c` over accepted `virt/be/r5.c` | R6 driver, accepted mechanism | rejection layer |

There are no gaps and no reserved numbers. Every layer is either a **rejection
layer** (some catalogue fixture is declared to be caught there) or a
**pass-through invariant** (no catalogue fixture is caught there; it must
still hold, and it is exercised by a checker self-test rather than by a
catalogue entry).

Layers run in order per fixture. For a **static** or **host** fixture the
pipeline stops at the declared rejection layer. For a **dynamic** or
**control** fixture every layer runs to completion: a declared L6
`reject-with` disposition is a recorded expectation, not a stop, and L7, L8,
L9, and L10 still execute. **Rejection at a layer other than the declared
one, or a disposition other than the declared one, is a fixture-design
failure** (`layer-shift`) that fails the R6 run and requires plan revision; it
is never silently accepted.

### Per-partition layer applicability

The accepted R5 image checker (L6) is mandatory for every image R6 builds. It
is never bypassed, disabled, or replaced. What differs per partition is the
**declared disposition** of that mandatory check.

| Partition | L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 | L9 | L10 | L11 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Control `C-01` | pass | pass | pass | pass | pass | must pass | must pass | identity delta | run | accepted sequence | n/a |
| Static `S-*` | pass | pass | declared | declared | declared | declared | n/a | n/a | forbidden | n/a | n/a |
| Dynamic `D-*` | pass | pass | must pass | must pass | must pass | declared disposition | conditional | must pass | run | declared class | n/a |
| Host `H-*` | pass | pass | n/a | pass | n/a | n/a | n/a | n/a | forbidden | n/a | declared class |

Rules that make this exact rather than a bypass:

1. **L6 disposition is declared, enumerated, and finite.** Every dynamic
   fixture manifest carries `accepted_image_check` with one of two values:
   `pass`, or `reject-with` plus the **exact single** assertion message the
   accepted checker must produce. Any other message, a pass where a rejection
   was declared, or a rejection where a pass was declared, is `layer-shift`
   and fails R6.
2. **The allowlist is per fixture and is a single message, not a pattern.**
   The nine guest-opcode fixtures (D-01..D-09) alter one frozen instruction
   slot, which the accepted checker's frozen-fixture rule detects. Their
   allowlisted message is exactly
   `<toolchain>: <domain> fixture slot <gpa> is <actual>, expected <expected>`
   with all four fields fixed in the manifest. The six monitor-side fixtures
   (D-10..D-14 in a copied `arch/riscv/be/r5-runtime.c`, D-15 in a copied
   `arch/riscv/be/r5-trap.S`) are constructed so the accepted checker passes
   unchanged.
3. **A declared rejection is not a waiver of the remaining invariants.** The
   accepted checker fails fast, so it cannot verify the rules after the one it
   rejects. L8 therefore supplies the missing assurance: the fixture image is
   compared against the control image built by the **same** toolchain in the
   same run, and must differ in exactly the declared delta and nowhere else.
   The control image is the one that passed the complete accepted checker, so
   every other R5 image invariant is preserved by identity rather than by
   assumption.
4. **L8 is mandatory for every dynamic and control image**, and its
   comparison set is fixed: ELF type, machine, entry, section table (names,
   addresses, sizes, flags), program headers, symbol addresses for every
   symbol the accepted checker pins, flat-image length, and a byte comparison
   of the flat image. For a guest-opcode fixture exactly one 4-byte word at
   one declared file offset may differ, and every section size must be
   identical. For a monitor-side fixture the declared delta is a bounded byte
   range inside `.monitor.text`, `.monitor.rodata`, and `.monitor.data`, whose
   sizes are not pinned by the accepted checker; every pinned section address
   and size, every guest page, root pool, saved page, private page, shared
   page, the `0x34000` flat extent, and every fixed symbol address must be
   byte identical. D-15's two inserted instructions are absorbed by the
   alignment padding the accepted tail already emits, so `.monitor.text` keeps
   its accepted size and nothing after the insertion point moves;
   [Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention)
   pins D-15's exact differing-run count, differing-byte count, and offsets
   per toolchain, and any deviation from them is a rejection rather than a
   tolerated variation.
5. **L3, L4, and L5 are never waived for a dynamic fixture.** A dynamic
   fixture that fails the source inventory, fails to compile, or fails to link
   is a fixture-design failure, not a result.
6. **L7 is conditional because the accepted parity checker consumes the
   accepted image checker's JSON output.** It runs, and must pass, for the
   control and for every monitor-side dynamic fixture, whose L6 disposition is
   `pass`. For a guest-opcode fixture the accepted checker produces a declared
   rejection instead of JSON, so parity cannot run; R6 instead requires that
   both toolchains produce the **same declared delta** (same slot, same file
   offset, same base word, same defect word) and that L8 succeeds against each
   toolchain's own control image, which itself passed both L6 and L7. Parity
   assurance is therefore preserved, not skipped.
7. **QEMU is executable-gated, not convention-gated.** `tests/r6/run-qemu.sh`
   reads the catalogue, refuses any identifier whose partition is not
   `dynamic` or `control`, refuses any image that did not reach L8 with the
   declared delta, refuses any image whose L6 disposition differs from the
   manifest, and refuses any image outside `build/r6/dynamic/` or
   `build/r6/control/`. Static and host fixtures cannot reach it even if a
   later target were written incorrectly.

R6 does not reuse the accepted `r5-qemu` graph for any fixture image. That
target runs `tests/r5/run-qemu.sh`, which ends by invoking the accepted
`tests/r5/check-qemu-artifacts.mjs` and therefore requires the complete
accepted 22-line console and the accepted trace; every dynamic fixture would
fail it for the wrong reason. R6 owns `tests/r6/run-qemu.sh` and
`tests/r6/check-dynamic.mjs`, and it invokes the accepted R5 QEMU graph only
for the R5 baseline itself.

### Partitions

- **Static-rejection fixtures** (`S-*`, `H-*`) must be rejected before any
  guest executes. `S-*` fixtures are image-construction defects; `H-*` fixtures
  are host-mechanism defects driven through the architecture-neutral core. QEMU
  is **forbidden** for both.
- **Dynamic fail-closed fixtures** (`D-*`) run under QEMU only when the defect
  is provably safe: the monitor either refuses before the guest is entered, or
  the guest executes only inside its own immutable G-stage map and the monitor
  terminates through the accepted `BE_R5:FAIL` + SBI SRST shutdown path.
- **Control fixture** (`C-01`) is the unmutated accepted build driven through
  the R6 path, proving the R6 harness reproduces accepted R5 semantics.

## Fixture catalogue

Counts are fixed: **14 static image fixtures, 17 host fixtures, 15 dynamic
fixtures, 1 control = 47 catalogue entries, 46 of them carrying exactly one
defect.**

### Static image fixtures (QEMU forbidden)

| ID | Base | Single defect | Layer | Expected rejection (exact) |
| --- | --- | --- | --- | --- |
| S-01 | `r5-beryllium.lds` | protected root pool origin `0x8021c000` -> `0x80220000` | L5 link | `ASSERT` `R5 protected root moved` |
| S-02 | `r5-beryllium.lds` | `.guest.code.protected` origin `0x80233000` -> `0x80234000` | L5 link | `ASSERT` `R5 protected guest moved` |
| S-03 | `r5-beryllium.lds` | `.saved.protected` extent `0x1000` -> `0x2000` | L5 link | `ASSERT` `R5 protected saved moved` |
| S-04 | `r5-trap.S` | second `sret` added to the guest-return tail | L3 source | `R5 source inventory: r5-trap.S does not contain exactly one sret` |
| S-05 | `r5-trap.S` | `hfence.gvma` removed from `be_r5_arch_install_root` | L6 image | `<tc>: HGATP writes and fences are not paired: be_r3_arch_install_management,be_r3_arch_reset_state,be_r5_arch_reset_state` |
| S-06 | `r5-trap.S` | second `csrw hgatp` in `be_r5_arch_install_root` | L6 image | `<tc>: expected 4 HGATP writes in the image, found 5` |
| S-07 | `r5-runtime.c` | `marker_final_event` emitted inside `switch_domain` after `be_r5_publish_target` | L6 image | `<tc>: switch transaction emits unexpected markers: marker_final_event,marker_management_fenced,marker_management_verified,marker_pending_management,marker_pending_protected,marker_protected_fenced,marker_protected_verified` |
| S-08 | `r5-runtime.c` | second **reachable** `be_r5_switch_tail` call site | L6 image | `<tc>: be_r5_switch_tail has more than one call site in the switch transaction` |
| S-09 | `r5-trap.S` | `be_r5_switch_tail` gains an outbound `call` | L6 image | `<tc>: be_r5_switch_tail calls out` |
| S-10 | `r5-trap.S` | `be_r5_arch_restore_active` references `__be_root_protected_start` | L6 image | `<tc>: unexpected G-stage root pool reference: be_r5_arch_restore_active,be_r5_runtime_main` |
| S-11 | `r5-guest.S` | `.option norvc` removed | L3 source | `R5 source inventory: guest fixtures do not pin non-compressed encodings` |
| S-12 | `r5-guest.S` | `nop` inserted at protected `+0x10` | L5 link | `ASSERT` `R5 protected fixture slot count changed` |
| S-13 | `virt/be/r5.c` | inline `asm volatile` CSR read added to the neutral core | L3 source | `R5 source inventory: virt/be/r5.c embeds assembly in neutral core` |
| S-14 | `tests/r5/Makefile` | an undeclared translation unit is added to the image | L3 source | `R5 source inventory: Makefile declares unlisted input <path>` |

Layer distribution: four source-inventory fixtures (S-04, S-11, S-13, S-14),
four link fixtures (S-01, S-02, S-03, S-12), six image-semantics fixtures
(S-05..S-10). No static fixture is assigned to compile (L4) or parity (L7);
those are pass-through invariants covered by checker self-tests, because a
single-defect construction that fails only at compile would test the pinned
compiler rather than an accepted R5 guarantee.

S-01, S-02, and S-03 move a section origin or extent that several `ASSERT`s
observe, so GNU `ld` and `lld` may report more than one assertion. The manifest
therefore records the **complete expected set** of assertion messages, all of
which must appear and none other; the table names the primary one. S-12
produces exactly one assertion.

S-05's expected message lists the three remaining paired fence sites in sorted
order after the fence is removed from `be_r5_arch_install_root`. S-07 must
reference a marker outside the six pre-publication markers; `marker_final_event`
is chosen because it already exists, so the fixture adds a call rather than a
symbol. S-10 must place the root-pool reference in a block whose name begins
with `be_r5`, so the sorted `rootWriters` assertion fires first and
deterministically; `be_r5_arch_restore_active` satisfies this and is on the
trap-driven path.

S-08 needs care: `be_r5_switch_tail` is `noreturn`, so a second call appended
after the first is dead code and is removed at `-O2` before the checker sees
it, which would make the fixture silently pass. The construction is therefore
**two reachable call sites with textually distinct argument setup**, so neither
arm is dead and neither can be folded by tail merging or cross-jumping. The
single accepted call

```c
be_r5_switch_tail(target_frame, transition.active.hgatp,
                  transition.trusted_sp);
```

becomes

```c
if (outbound)
        be_r5_switch_tail(target_frame, transition.active.hgatp,
                          transition.trusted_sp);
else
        be_r5_switch_tail(target_frame, transition.active.hgatp,
                          entry.trusted_sp);
```

`outbound` is already computed in `switch_domain`, and `entry.trusted_sp` is an
existing field of the `struct be_r5_entry_state` local that
`be_r5_arch_reset_target` filled a few statements earlier, so both arms are
well typed, both are reachable, and the two argument setups differ, which is
what defeats cross-jumping. The disassembled `switch_domain` then contains two
`<be_r5_switch_tail>` references and the accepted checker fails with
`<toolchain>: be_r5_switch_tail has more than one call site in the switch
transaction`. The earlier per-symbol `be_r5_publish_target` assertions still
pass, so this exact message is the first and only failure.
`tests/r6/check-fixtures.mjs` additionally requires that S-08's disassembled
`switch_domain` block contains two references before L6 runs, so a future
optimizer change that folds the arms anyway is reported as `no-defect` rather
than passing as a false negative.

S-05 is the **static skipped-fence probe**. It proves the accepted image checker
rejects a construction whose root write is not paired with `HFENCE.GVMA`. It is
never executed; R6 makes no claim about hardware behavior under a genuinely
skipped fence.

Forbidden side effects for every `S-*` fixture: no QEMU invocation, no console
log, no trace log, no exit-status file, no image promoted out of
`build/r6/static/<id>/<toolchain>/rejected/`, and no mutation of any accepted
path. `tests/r6/check-static.mjs` and `tests/r6/generate-evidence.sh` both
assert these absences.

S-04, S-11, S-13, and S-14 are rejected at source inventory before a build is
attempted, so they produce no object and no ELF. S-01, S-02, S-03, and S-12
compile but do not link, so they produce objects and no ELF. S-05 through S-10
link, so they produce an ELF that is built and immediately quarantined.

### Host mechanism fixtures (no image, no QEMU)

Each host fixture calls the accepted architecture-neutral mechanism in
`virt/be/r5.c` from `tests/r6/r6-check.c` with **exactly one malformed
argument, or exactly one malformed field of one otherwise well-formed
argument**, and requires the exact error class. Several accepted validators
take a whole structure, so a single scalar field is the smallest honest unit of
malformation; the fixture manifest names the structure, the field, the accepted
value, and the malformed value. These cover the classes that cannot be produced
safely or at all inside the fixed QEMU profile.

| ID | Call | Malformed field | Expected class | Role |
| --- | --- | --- | --- | --- |
| H-01 | `be_r5_handle_exit` | one of `state`, `frame`, `observation`, `result` is `NULL` | `null` | primary |
| H-02 | `be_r5_handle_exit` | `state->pending.direction` `BE_R5_DIRECTION_NONE` -> `BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT`, rest of `pending` cleared | `pending` | primary |
| H-03 | `be_r5_handle_exit` | `observation->active.vcpu_id = 3` | `binding` | primary |
| H-04 | `be_r5_publish_target` | `entry->trusted_sp = 0x80227000` for the protected target | `trusted-stack` | primary |
| H-05 | `be_r5_publish_target` | `entry->saved_state_pa = 0x8022d000` | `saved-page` | secondary (D-14 is primary) |
| H-06 | `be_r5_handle_exit` | `observation->hstatus` clears the VS-origin bit (`V=0` exit) | `vs-origin` | primary |
| H-07 | `be_r5_handle_exit` | `observation->vsatp = 0x8000000000080000` | `vsatp` | primary |
| H-08 | `be_r5_handle_exit` | `frame->reserved = 1` | `frame-reserved` | primary |
| H-09 | `be_r5_publish_target` at `MANAGEMENT_FENCED` | `state->management_frame.gpr[BE_R4_GPR_A1]` `34` -> `35` | `frame-state` | primary |
| H-10 | `be_r5_publish_target` | one of `entry->vstvec`, `entry->vsepc`, `entry->vscause`, `entry->vstval` set to `0x40011000` | `target-reset` | primary |
| H-11 | `be_r5_publish_target` | `entry->sstatus` clears `SPP`, or `entry->hstatus` clears `SPV` | `entry-controls` | primary |
| H-12 | `be_r5_publish_target` at `PROTECTED_FENCED` | `state->switch_count` `0` -> `1` | `publication` | primary |
| H-13 | `be_r5_handle_exit` | `observation->hart_id = 1` | `hart` | primary |
| H-14 | `be_r5_handle_exit` | `frame->htval = 0x4000000000000000` | `htval-overflow` | primary |
| H-15 | `be_r5_handle_exit` | correct `frame->stval`, `frame->htval = 0x10000c00` (reconstructs `0x40003000`) | `gpa` | primary |
| H-16 | `be_r5_handle_exit` | ecall exit with `frame->stval = 4` | `trap-metadata` | primary |
| H-17 | `be_r5_note_shutdown_returned` | SRST returns `BE_R3_ERROR_SRST_RETURNED`, then returns any other SBI error | `shutdown-returned`, `shutdown-rejected` | primary (two outcomes) |

Field-level accuracy notes, taken from the accepted headers and validators:

- `be_r5_handle_exit` takes exactly four pointers, `state`, `frame`,
  `observation`, and `result`. There is no `transition` parameter; that name
  belongs to `be_r5_publish_target`. H-01 cycles those four and no other.
- `struct be_r5_pending` has members `direction`, `frame_mode`, `source`, and
  `target` only. There is no `valid` member. `be_r5_handle_exit` rejects a
  non-cleared record through `pending_clear`, which requires
  `direction == BE_R5_DIRECTION_NONE`, `frame_mode == BE_R5_FRAME_MODE_NONE`,
  and a zeroed `source` and `target`. H-02 therefore sets exactly
  `state->pending.direction` to `BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT`
  (enum value `2`) in an otherwise cleared record of a running protected
  world, and leaves `frame_mode`, `source`, and `target` zero. That mutation
  is reached because `pending_clear` is evaluated after the phase switch, the
  three remaining null checks, and `identities_intact`, and strictly before
  the active-binding check, so `pending` is the first failure. The accepted
  `tests/r5/r5-check.c` already proves this exact shape in
  `test_exit_state_corruption`.
- `struct be_r5_observation` has no `stval` and no `htval`. The trap metadata
  classes therefore belong to `struct be_r4_frame`, which carries
  `gpr[31]`, `vstvec`, `vsepc`, `vscause`, `vstval`, `scause`, `sepc`, `stval`,
  `htval`, and `reserved` in 320 bytes. H-14, H-15, and H-16 are expressed
  against that frame.
- `struct be_r4_frame` deliberately has **no `htinst`**. R6 must not reference
  one.
- `frame-state` is not produced by `be_r5_handle_exit` at all. The only
  producers are `be_r5_prepare_pending` on the return leg and
  `be_r5_publish_target` in `BE_R5_FRAME_MODE_SAVED`. H-09 therefore calls
  `be_r5_publish_target` on a state at `BE_R5_PHASE_MANAGEMENT_FENCED`, with
  the accepted management entry state and the accepted retained frame passed
  as `target_frame`, and mutates exactly one field of `state->management_frame`:
  `gpr[BE_R4_GPR_A1]`, accepted `BE_R4_SHARED_VALUE` = `34`, malformed `35`.
  `validate_management_frame` returns `BE_R5_ERROR_EVENT_ARGS` internally and
  `be_r5_publish_target` rewrites every internal frame verdict to
  `BE_R5_ERROR_FRAME_STATE` before returning, so the observed class is exactly
  `frame-state`. `state->management_frame` is examined by none of the earlier
  checks (phase, nulls, `identities_intact`, `pending_exact`, `binding_equal`,
  the publication guard, `validate_entry_state`), so the mutation is reached
  by construction. The accepted host driver proves the same rewrite for
  `management_frame` mutations at `be_r5_prepare_pending` and for
  `target_frame` mutations at `be_r5_publish_target`.
- `publication` has exactly one producer: the single guard
  `state->active.published != 1 || state->pending.target.published != 0 ||
  state->switch_count != (management-to-protected ? 0 : 1)` in
  `be_r5_publish_target`. Of the three fields it reads, only `switch_count`
  is reachable by a single mutation. `state->active.published = 0` fails the
  earlier `binding_equal(&state->pending.source, &state->active)` check and
  yields `binding`; `state->pending.target.published = 1` fails the earlier
  `pending_exact` check and yields `pending`. H-12 therefore uses a state at
  `BE_R5_PHASE_PROTECTED_FENCED` with direction management-to-protected,
  accepted `state->switch_count = 0`, malformed `state->switch_count = 1`.
  No earlier check in `be_r5_publish_target` reads `switch_count`, so the sole
  publication guard is the first failure. The accepted `tests/r5/r5-check.c`
  proves all three dispositions in `test_publish_state_corruption`.
- `target-reset` is produced only by `validate_entry_state` when one of
  `entry->vstvec`, `entry->vsepc`, `entry->vscause`, or `entry->vstval` is
  non-zero. A non-zero GPR does not produce it, so H-10 mutates a reset CSR
  field of `struct be_r5_entry_state` and does not touch frame state; this also
  keeps H-10 disjoint from H-08 and H-09.
- `validate_denied_access` checks `scause`, then `sepc`, then `stval`, then
  the `htval` reconstruction. H-15 must therefore leave `stval` correct, or
  `gva` fires first and the fixture is a `layer-shift`.
- `validate_entry_state` checks `hgatp`, then entry controls, then `vsatp`,
  then the reset CSRs, then `trusted_sp`, then `saved_state_pa`, and it runs
  only after the publication guard. H-04, H-05, H-10, and H-11 each mutate
  exactly one field at a distinct position in that order, so each expected
  class is the first failure by construction, and none of them can be reached
  by H-12's mutation or reach H-12's class.

H-17 covers the two shutdown classes at the host layer because producing them
under QEMU would require forging the digest-pinned OpenSBI firmware, which R6
forbids. R6 explicitly does not claim dynamic coverage of those two classes.

**Host negative self-tests.** Every host fixture carries exactly one paired
negative self-test, seventeen in total, so the driver cannot report a class it
did not observe:

- the same call is issued with the declared field restored to its accepted
  value and must return `BE_R5_ERROR_NONE`, proving the class is caused by the
  declared defect and not by the harness setup;
- the driver is then asked to accept a deliberately wrong class for the
  malformed call, and must reject it as `wrong-error-class`, proving the
  assertion is a real comparison rather than an unconditional pass;
- for H-01 the restored case additionally cycles all four pointers, `state`,
  `frame`, `observation`, and `result`, and for H-17 the restored case is a
  successful SRST that never returns.

Every host fixture's declared world is constructed only through the accepted
API sequence (`be_r5_import_r4_complete`, `be_r5_prepare_pending`,
`be_r5_note_target_fenced`, `be_r5_publish_target`, `be_r5_handle_exit`), and
exactly one field is then mutated before the named call. No host fixture
hand-builds a phase, and none mutates a second field to make the first
reachable; a fixture that would need two mutations is a fixture-design failure
and requires plan revision.

`tests/r6/r6-check.c` is built by both pinned host toolchains and both
binaries are run; their complete stdout must be byte identical, matching the
accepted R5 host discipline. Host scenario executions are therefore
`(17 fixtures + 17 self-tests) x 2 binaries = 68`.

R6 host fixtures are new, additional coverage. They do not restate, re-run, or
re-count the accepted R5 host result (32 scenarios, 9,707 assertions).

### Dynamic fail-closed fixtures (QEMU allowed)

All fifteen terminate through `BE_R5:FAIL <class>` followed by the accepted SBI
SRST shutdown, so QEMU exits with status `0`. `BE_R5:12`, `BE_R5:SRST_RETURNED`,
any marker after the failure line, and any marker out of order are forbidden in
every dynamic run.

Guest-driven fixtures (defect in a copy of `arch/riscv/be/r5-guest.S`). Each
changes exactly one frozen word, so each is declared `reject-with` at L6 and
carries a single exact allowlisted message of the form
`<tc>: <domain> fixture slot <gpa> is <actual>, expected <expected>`:

| ID | Slot | Offset | Base -> defect | Architectural effect | Class | Last marker |
| --- | --- | --- | --- | --- | --- | --- |
| D-01 | `0x4001102c` | `0x3302c` | `00200893` -> `00900893` | `addi a7,zero,9`; ecall at `0x40011030`, cause 10, `a7=9` | `event-args` | `BE_R5:06` |
| D-02 | `0x40011004` | `0x33004` | `03300313` -> `03400313` | protected private page holds 52 at the first protected exit | `backing` | `BE_R5:04` |
| D-03 | `0x40011010` | `0x33010` | `400003b7` -> `400033b7` | cause 21 at `0x40011014`, `stval=0x40003000`, `htval=0x10000c00` | `gva` | `BE_R5:04` |
| D-04 | `0x40011014` | `0x33014` | `0003a483` -> `0093a023` | `sw s1,0(t2)`; cause 23 where 21 is expected, `stval=0x40000000` | `cause` | `BE_R5:04` |
| D-05 | `0x40011028` | `0x33028` | `00040513` -> `00038067` | `jr t2` into read-only shared `0x40002000`, cause 20 | `cause` | `BE_R5:06` |
| D-06 | `0x40011028` | `0x33028` | `00040513` -> `68002573` | `csrr a0,hgatp` from VS, cause 22 at `0x40011028` | `cause` | `BE_R5:06` |
| D-07 | `0x40011010` | `0x33010` | `400003b7` -> `0003a483` | `t2=0` at entry, cause 21 at `0x40011010`, `stval=0`, `htval=0` | `pc` | `BE_R5:04` |
| D-08 | `0x40010028` | `0x32028` | `00040513` -> `00000513` | R4 private event reports `a0=0`, so `be_r4_handle_trap` returns `event-args` and the R5 runtime terminates with `import` | `import` | `BE_R4:02` |
| D-09 | `0x40010034` | `0x32034` | `00300893` -> `00400893` | final ecall carries event id 4 | `event-args` | `BE_R5:10` |

Cause coverage: `21` at D-03/D-07, `22` at D-06, `23` at D-04, `20` at D-05, and
`10` in the wrong-argument path at D-01/D-09. Every guest-driven fixture stays
inside its own immutable G-stage map; none can write another domain's private
page, because the accepted roots, not the fixture, define reachability.

D-04 mutates the denied-load slot itself, D-07 mutates the `lui` that
establishes `t2` for it. Both keep the change to one word, and both keep every
other frozen word intact, which is what the L8 differential checker verifies.

Monitor-side fixtures. D-10 through D-14 carry their defect in a copy of
`arch/riscv/be/r5-runtime.c`; D-15 carries its defect in a copy of
`arch/riscv/be/r5-trap.S` (see
[Plan revision R6-A](#plan-revision-r6-a-d-15-injection-site)). All
six are declared `pass` at L6: they change monitor logic, not a frozen guest
word, a pinned symbol address, a marker set, a call site, an HGATP writer, or
a fence site, so the accepted image checker must still pass. A monitor-side
fixture that the accepted checker rejects is a `layer-shift` and a
fixture-design failure.

| ID | Base | Single defect | Class | Last marker | Guest entered |
| --- | --- | --- | --- | --- | --- |
| D-10 | `r5-runtime.c` | `switch_domain` passes `BE_R3_MANAGEMENT_HGATP` to `be_r5_arch_install_root` instead of `pending.target.hgatp` | `target-readback` | `BE_R5:02` | no |
| D-11 | `r5-runtime.c` | one added line after `be_r5_arch_install_root` sets `ack.fence_completed = 0U` | `fence` | `BE_R5:02` | no |
| D-12 | `r5-runtime.c` | one added line after `be_r5_arch_install_root` sets `ack.source_hgatp = ack.hgatp_written` | `hgatp` | `BE_R5:02` | no |
| D-13 | `r5-runtime.c` | the single `be_r5_publish_target` call site is placed in a bounded loop whose trip count is 2 | `invalid-phase` | `BE_R5:04` | no |
| D-14 | `r5-runtime.c` | `be_r5_arch_reset_target` is passed the management trusted SP `0x80227000` | `saved-page` | `BE_R5:03` | no |
| D-15 | `r5-trap.S` | inside `be_r5_switch_tail`, after every entry-control readback and after the last frame restore (`csrw htval,t0`), immediately before `.option pop` and the jump to `be_r5_enter_guest_tail`, exactly `csrsi hvip, 4` then `csrsi hie, 4` | `interrupt` | `BE_R5:04` | `SRET` into VS at `0x40011000`, preempted before any instruction retires |

Placement rationale, so each fixture reaches its declared layer:

- D-11 and D-12 are **not** placed in `arch/riscv/be/r5-trap.S`. The accepted
  image checker pins the exact instruction order of `be_r5_arch_install_root`
  (`csrr t0,hgatp; sd t0,0(a0); csrw hgatp,a1; sd a1,8(a0); hfence.gvma;
  csrr t0,hgatp; sd t0,16(a0); ret`), so an assembly-level change would be
  rejected at L6 rather than reaching QEMU. Placing the single added line in
  `switch_domain` leaves the privileged sequence, the write, and the fence
  exactly as accepted; only the acknowledgement the monitor reasons about is
  corrupted.
- D-13's second publication must be **reachable and dynamically executed while
  remaining a single static call site**, because the accepted checker requires
  exactly one `<be_r5_publish_target>` reference in `switch_domain`. A second
  written call site would be rejected at L6 as S-08's message. The construction
  is a `static volatile int` trip counter initialized to `2` guarding a `while`
  loop around the existing call, so neither GCC nor Clang can prove the trip
  count at `-O2` and neither can unroll it into two references. The first
  iteration publishes and advances the phase; the second re-enters
  `be_r5_publish_target` with the phase no longer `PROTECTED_FENCED`, which is
  exactly `invalid-phase`. `tests/r6/check-fixtures.mjs` asserts that D-13's
  built image contains exactly one `<be_r5_publish_target>` reference, so an
  optimizer change that unrolls the loop is reported rather than silently
  turned into a different fixture. If a future toolchain makes a single static
  call site impossible, D-13 moves to the static partition as an S-fixture with
  the S-08 message and `invalid-phase` loses its dynamic primary; the plan must
  then be revised rather than the expectation relaxed.
- D-15 is the one monitor-side fixture that **cannot** live in
  `arch/riscv/be/r5-runtime.c`. The accepted `be_r5_switch_tail` re-reads `hie`
  and `hvip` and rejects a non-zero value before `SRET`, so any arming inside
  `switch_domain` terminates as `entry-controls`, not `interrupt`. D-15 is
  therefore a copy of `arch/riscv/be/r5-trap.S` whose two inserted instructions
  sit after every entry-control readback and after the last frame restore, so
  the accepted no-call, ordered-verification, ordered-restore, single-`sret`,
  and no-HGATP-write rules on the tail all still hold, and `switch_domain` is
  not edited at all. [Plan revision R6-A](#plan-revision-r6-a-d-15-injection-site)
  states the exact delta, the requirement for both `csrsi` instructions, the
  absence of any GPR clobber, and the complete accepted-checker disposition;
  [Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention)
  states the corrected image-layout consequence — the insertion is absorbed by
  the accepted `.align 4` padding, so `.monitor.text`'s allocated size is
  unchanged and every checker-fixed/required allocated symbol keeps its
  address (`be_r5_switch_tail`'s `st_size` alone grows `212`->`220`) — and
  pins the exact L8 delta.
- No fixture may introduce a `be_r6` or `BE_R6` identifier into any accepted
  image source. The accepted `check-sources.mjs` bans them, and every dynamic
  fixture must pass L3, so such a fixture would be rejected at the wrong layer.

D-11 is the **safe dynamic skipped-fence probe**. The fence is still executed,
so no unfenced guest ever runs; only the acknowledgement is withheld, proving
the monitor refuses to proceed without a completed local fence. Together with
static S-05 this discharges the master-plan "skipped fence" family without
executing an unsafe image.

D-15 asserts `scause=0x8000000000000002`, `sepc=0x40011000`, `stval=0`,
`htval=0`, class `interrupt`, last marker `BE_R5:04`, and zero retired
protected guest instructions. Its `guest_entered` field is `true` in the exact
architectural sense that `SRET` completed into VS mode; the dynamic expectation
additionally requires that no protected guest instruction retires and that the
trace contains no `V=1` protected entry dump, so the declared trace entries for
D-15 are the two management entries only. It must also emit no `BE_R5:05` and
no `BE_R5:12`. Its L8 delta is pinned to exactly 2 differing runs and 10
differing bytes at the per-toolchain offsets fixed by
[Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention).
If the observed cause, class, marker, or
disposition differs, the fixture fails as `wrong-error-class` and the plan must
be revised; the harness must not relax the expectation at run time. D-06
asserts cause `22`
(virtual instruction) for a VS-mode `csrr hgatp`; the same rule applies if QEMU
reports cause `2` instead, because the accepted expected class is `cause`
either way but the recorded architectural justification must remain true.

Forbidden side effects for every `D-*` fixture: no unapproved guest entry after
a malformed publication, fence, or binding defect (D-10 through D-14 must never
emit `BE_R5:05`); no `BE_R5:12`; no `BE_R5:SRST_RETURNED`; no timeout; no
non-zero QEMU status; no marker from a later phase than the declared last
marker; no write to any accepted path.

### Control fixture

| ID | Content | Requirement |
| --- | --- | --- |
| C-01 | unmutated accepted sources built and run through the R6 path | the exact 22-line accepted sequence `BE_R3:01..07`, `BE_R4:01..03`, `BE_R5:01..12`, identical line for line to the normative table above and to the accepted `expectedConsole` array in `tests/r5/check-qemu-artifacts.mjs`, QEMU status `0`, no `BE_R5:FAIL` |

C-01 is harness self-validation only. It is **not** new R5 evidence and **not**
an R5 re-acceptance.

### Coverage ledger

Coverage is **disjoint by construction**: every one of the 29 non-`none` error
classes has exactly one **primary** fixture at exactly one layer. Additional
fixtures that happen to produce an already-covered class are listed separately
as **secondary** coverage and are never counted toward completeness.

Primary dynamic coverage, 12 classes:

| Class | Primary fixture |
| --- | --- |
| `event-args` | D-01 |
| `backing` | D-02 |
| `gva` | D-03 |
| `cause` | D-04 |
| `pc` | D-07 |
| `import` | D-08 |
| `target-readback` | D-10 |
| `fence` | D-11 |
| `hgatp` | D-12 |
| `invalid-phase` | D-13 |
| `saved-page` | D-14 |
| `interrupt` | D-15 |

Primary host coverage, 17 classes across 16 fixtures:

| Class | Primary fixture |
| --- | --- |
| `null` | H-01 |
| `pending` | H-02 |
| `binding` | H-03 |
| `trusted-stack` | H-04 |
| `vs-origin` | H-06 |
| `vsatp` | H-07 |
| `frame-reserved` | H-08 |
| `frame-state` | H-09 |
| `target-reset` | H-10 |
| `entry-controls` | H-11 |
| `publication` | H-12 |
| `hart` | H-13 |
| `htval-overflow` | H-14 |
| `gpa` | H-15 |
| `trap-metadata` | H-16 |
| `shutdown-returned`, `shutdown-rejected` | H-17 |

Deliberate secondary coverage, 4 claims, none counted toward completeness:

| Class | Secondary fixture | Why it is retained |
| --- | --- | --- |
| `cause` | D-05 | distinct architectural cause 20 (instruction guest-page fault) |
| `cause` | D-06 | distinct architectural cause 22 (virtual instruction) |
| `event-args` | D-09 | management final event, a different phase from D-01 |
| `saved-page` | H-05 | host-layer coverage of `validate_entry_state`, where D-14 covers the `switch_domain` check |

Totals: `12 + 17 = 29` primary classes, `0` uncovered, `4` secondary claims.
`tests/r6/check-report.mjs` fails if any class lacks a primary fixture, if two
fixtures claim the same class as primary, or if a fixture recorded as secondary
is counted toward completeness.

Master-plan family mapping (a fixture may appear in more than one family; this
mapping is descriptive and is not the coverage ledger):

| Family | Fixtures |
| --- | --- |
| malformed input | S-11, S-12, S-13, S-14, H-01..H-17, D-01..D-09 |
| partial publication | S-07, S-08, S-09, D-13, H-12 |
| wrong binding | D-10, D-14, H-03, H-04, H-05, H-13 |
| skipped fence | S-05, S-06, D-11, D-12 |
| unexpected trap/event | D-04, D-05, D-06, D-15, H-16 |
| denied access | D-03, D-07, H-14, H-15 |
| malformed image/layout | S-01, S-02, S-03, S-04, S-10 |

## Outcome taxonomy and marker vocabulary

Permitted per-fixture outcomes:

```text
rejected-at-source-inventory rejected-at-link
rejected-by-image-check      rejected-by-host-mechanism
terminated-fail-closed       control-accepted
```

Permitted per-image L6 dispositions, recorded but not terminal for dynamic
fixtures:

```text
accepted-image-check-pass    accepted-image-check-declared-rejection
```

Forbidden outcomes, each an immediate R6 failure:

```text
built-and-accepted   entered-guest-after-defect   timeout
qemu-nonzero         srst-returned                marker-out-of-order
wrong-error-class    layer-shift                  missing-diagnostic
undeclared-image-delta            unexpected-image-check-pass
scratch-fault
```

`scratch-fault` covers an absent, redirected, unusable, or unconfined scratch
or output component, and a dropped, redirected, or stale scratch copy of
`tests/r3/tool-lock.mjs` or `tests/r3/tool-lock.conf`. It is never attributed
to a fixture and never counted as a layer result.

R6 harness vocabulary (R6 must never print a `BE_R5:` marker itself):

```text
BE_R6_TOOLS: PASS ...
BE_R6_SCRATCH: PASS id=<ID> components=16 sources=5 base-lock=verified copies=<n>
BE_R6_BASELINE: PASS r5_accepted_commit=165f4d001a2b59b582b397bdea79ec4826168fdb immutable=yes pins-refreshed=6
BE_R6_FIXTURES: PASS entries=47 defects=46 control=1 digest=<sha256>
BE_R6_HOST: PASS fixtures=17 class-outcomes=18 self-tests=17 executions=68 gcc-clang-deterministic=yes
BE_R6_STATIC: PASS id=<ID> toolchain=<tc> layer=<layer> outcome=<outcome>
BE_R6_DIFFERENTIAL: PASS id=<ID> toolchain=<tc> delta=<declared> disposition=<disposition>
BE_R6_DYNAMIC: PASS id=<ID> toolchain=<tc> runs=2 class=<class> last-marker=<marker>
BE_R6_COVERAGE: PASS classes=29 dynamic-primary=12 host-primary=17 secondary=4 uncovered=0
BE_R6_SELFTEST: PASS stages=11 mutations=<n>
BE_R6_REPORT: PASS schema=be-r6-adversarial-images-v1
BE_R6_EVIDENCE: PASS artifacts=<n>
BE_R6_CHECK: PASS fixtures=46 control=1
BE_R6:FAIL <reason>
```

Any failure prints exactly one `BE_R6:FAIL <reason>` line and exits non-zero.
There is no partial-success banner.

## Planned source boundary

Architecture-neutral, test-only (no RISC-V knowledge):

```text
tests/r6/fixtures.json              catalogue manifest, 47 entries
tests/r6/check-fixtures.mjs         manifest and single-defect delta validation
tests/r6/r6-check.c                 17 host fixtures over virt/be/r5.c
tests/r6/generate-report.mjs        deterministic canonical report
tests/r6/check-report.mjs           report semantics and coverage ledger
tests/r6/test-report-rejection.mjs  report mutation self-tests
tests/r6/check-acceptance.sh        R6 acceptance status reporting
tests/r6/generate-evidence.sh       retention, digests, claim ledger
```

RISC-V and image aware, test-only:

```text
tests/r6/fixtures/<id>/fixture.json  per-fixture declaration
tests/r6/fixtures/<id>/*.defect      single defective copy of one accepted file
tests/r6/build-fixture.sh            scratch materialization and build
tests/r6/check-static.mjs            declared-layer rejection enforcement
tests/r6/check-fixture-image.mjs     differential image checker
tests/r6/run-qemu.sh                 bounded dynamic runs
tests/r6/check-dynamic.mjs           console and trace semantics
```

Harness and binding:

```text
tests/r6/run-make.sh                 checked launcher, exact target allowlist
tests/r6/Makefile                    parse-time guarded graph
tests/r6/make-control.mjs            hostile Make control validation
tests/r6/tool-lock.conf              be-r6-tool-lock-v1
tests/r6/tool-lock.mjs               lock loader
tests/r6/check-tools.sh              executable and firmware verification
tests/r6/prepare-scratch.sh          16 confined components, 5 source components, R3 base-lock verification
tests/r6/materialize-scratch.mjs     byte-and-mode identical scratch copies
tests/r6/check-baseline.sh           accepted-R5 immutability precondition
tests/r6/check-sources.mjs           R6 inventory, scratch inventory, and accepted-path guard
tests/r6/test-fixture-mutation.mjs   fixture self-tests
tests/r6/test-scratch-prerequisites.mjs  scratch and R3 base-lock fault self-tests
tests/r6/test-qemu-artifact-integrity.mjs
tests/r6/test-tool-binding.mjs
tests/r6/test-fresh-bootstrap.mjs
```

No file outside `tests/r6/` is created by the fixture package. `tests/r6/` must
contain no `include/`, `virt/`, or `arch/` file and no build product; all
products live under `build/r6/`. A `*.defect` file is a copy of one accepted
base file, named after it and never installed into an accepted path: the
dynamic partition's bases are `arch/riscv/be/r5-guest.S` (D-01..D-09),
`arch/riscv/be/r5-runtime.c` (D-10..D-14), and `arch/riscv/be/r5-trap.S`
(D-15).

## Build, toolchain, and run matrix

Host: `gcc` and `clang` build `tests/r6/r6-check.c` against the accepted
neutral core. Two binaries, 17 host fixtures plus 17 paired negative
self-tests each, byte-identical output streams required.

Image toolchains, both from `tests/r3/tool-lock.conf` (SHA-256
`c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b`):

| Toolchain | Compiler | Linker |
| --- | --- | --- |
| `gcc` | pinned `riscv64-linux-gnu-gcc` | pinned GNU `ld` |
| `clang` | pinned `clang --target=riscv64` | pinned `lld` |

Fixed counts:

| Quantity | Value | Derivation |
| --- | --- | --- |
| Catalogue entries | 47 | 14 static + 17 host + 15 dynamic + 1 control |
| Single-defect fixtures | 46 | 47 minus the control |
| Host binaries | 2 | gcc, clang |
| Host scenario executions | 68 | (17 fixtures + 17 self-tests) x 2 binaries |
| Source-inventory evaluations without build | 4 | S-04, S-11, S-13, S-14, toolchain independent |
| Scratch trees materialized | 30 | 14 static + 15 dynamic + 1 control, one per image-path fixture, both toolchains built inside it |
| Scratch trees for host fixtures | 0 | host fixtures compile against the real accepted neutral core |
| Confined components per scratch tree | 16 | 4 outer + 7 inherited accepted + 5 R6 output |
| Scratch source components per tree | 5 | `arch/`, `include/`, `virt/`, `tests/r5/`, the two `tests/r3/` lock files |
| Image build attempts | 52 | (4 link-layer + 6 image-layer + 15 dynamic + 1 control) x 2 |
| Expected link failures | 8 | (S-01, S-02, S-03, S-12) x 2 |
| Successful links | 44 | 52 minus 8 |
| Static ELFs built and quarantined | 12 | (S-05..S-10) x 2 |
| Dynamic ELFs | 30 | 15 x 2 |
| Control ELFs | 2 | 1 x 2 |
| Accepted image-checker (L6) invocations | 44 | one per successful link |
| L6 declared rejections | 18 | (D-01..D-09) x 2 |
| L6 declared passes | 14 | (D-10..D-15 + C-01) x 2 |
| L6 static rejections | 12 | (S-05..S-10) x 2 |
| Accepted parity (L7) invocations | 7 | D-10..D-15 and C-01, one per fixture |
| Differential (L8) invocations | 32 | (15 dynamic + 1 control) x 2 |
| QEMU runs | 64 | (15 + 1) x 2 toolchains x 2 runs |
| QEMU runs for static or host fixtures | 0 | executable-gated |

Every count in this table is asserted by `tests/r6/check-report.mjs` against
the generated report; a divergence fails R6 rather than being reconciled by
editing the report.

QEMU/firmware matrix, unchanged from accepted R5:

```text
timeout --foreground 120s qemu-system-riscv64 \
  -machine virt,aia=none \
  -cpu rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,\
sstc=false,smstateen=false,svadu=false,debug=false \
  -smp 1 -m 128M -bios default -kernel <elf> -nographic -no-reboot \
  -d in_asm,cpu -D <trace>
```

with pinned `qemu-system-riscv64` 10.2.2 from
`qemu-system-riscv-core-10.2.2-1.fc44.x86_64` and pinned OpenSBI
`/usr/share/qemu/opensbi-riscv64-generic-fw_dynamic.bin` SHA-256
`49bdf7b939bda11321132d1042bf99d7324fb190f1feef423171fed3573f8705`. Every
dynamic run must exit `0`; a timeout is a failure, never a pass.

## Locks, launcher, and hostile controls

`tests/r6/tool-lock.conf` uses schema `be-r6-tool-lock-v1` and binds:

- `R6_BASE_TOOL_LOCK=tests/r3/tool-lock.conf` with its exact SHA-256
  `c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b`, the same
  value `tests/r6/prepare-scratch.sh` verifies in every scratch tree;
- every normative executable by absolute command path, resolved path, version
  string, SHA-256, and owning package;
- the OpenSBI firmware blob digest;
- `R6_ACCEPTED_R5_COMMIT=165f4d001a2b59b582b397bdea79ec4826168fdb`.

`tests/r6/run-make.sh` is the normative interface and accepts exactly:

```text
r6-toolcheck  r6-baseline  r6-host-test  r6-fixture-check
r6-static     r6-dynamic   r6-report     r6-evidence
r6-check      clean
```

Raw `make -C tests/r6 TARGET` remains a parse-time-guarded developer interface
only, because GNU Make can exit or select another `-f` file before the R6
Makefile loads.

Required refusals, mirroring accepted R3-R5 practice: at least 40 launcher
control cases, at least 20 command-line control cases, and at least 20
environment cases must be rejected, covering `-f`, `--file`, `-C`, `-e`,
`--eval`, `-I`, `--include-dir`, `-o`, `-W`, `MAKEFLAGS`, `MFLAGS`,
`GNUMAKEFLAGS`, `PATH`, `SHELL`, `CC`, `LD`, `QEMU`, `HOME`, `TMPDIR`,
`SOURCE_DATE_EPOCH`, and locale overrides. `tests/r6/test-fresh-bootstrap.mjs`
must prove a fresh detached worktree passes with no pre-existing `build/`, and
that any symlinked input, output, scratch, or evidence path is rejected.

`tests/r6/run-make.sh` refuses every control above **before** it calls
`tests/r6/prepare-scratch.sh`, so a rejected invocation creates nothing, and it
then execs GNU Make with `HOME` and `TMPDIR` inside the R6 build tree. This is
the accepted `tests/r5/run-make.sh` ordering, and R6 does not relax it. R6
never reuses, removes, or recreates the real-worktree `build/r3` or `build/r5`
scratch of a live accepted stage.

`tests/r6/check-baseline.sh` must run first in every target and must fail
closed unless `tests/r5/check-acceptance.sh --require` reports
`r5_acceptance=accepted` and `r5_accepted_mechanism_match=yes`.

## Mutation and self-tests

| Self-test | Minimum cases |
| --- | --- |
| Report mutation rejection | 28 |
| QEMU artifact mutation rejection | 8 per toolchain |
| Fixture manifest mutation (`no-defect`, `multiple-defects`, wrong base digest, wrong layer, wrong class, wrong L6 disposition, wrong declared delta, budget overrun) | 16 |
| Layer-shift detection (fixture rejected earlier or later than declared, or a declared disposition observed as its opposite) | 6 |
| Acceptance-pin refresh (revert each of the six constants; revert each of the three edited root files) | 9 |
| Static fixture that unexpectedly builds and passes every accepted checker | 1 per static fixture (14) |
| Dynamic fixture that emits a forbidden marker | 1 per dynamic fixture (15) |
| Host fixture forged or wrong-class result | 1 per host fixture (17) |
| Compile-stage (L4) mutation: an input that must fail to compile does | 2 |
| Parity-stage (L7) mutation: a forged divergent JSON pair is rejected | 2 |
| Differential-stage (L8) mutation: an undeclared extra byte delta, a missing declared delta, and a delta at the wrong offset are each rejected | 6 |
| D-15 pinned-delta mutation: an extra differing byte, a missing pinned byte, a relocated pinned run, and a `.monitor.text` size change are each rejected per toolchain | 8 |
| QEMU executable gate: a static and a host identifier are refused by `run-qemu.sh` | 2 |
| Scratch and R3 base-lock prerequisites: each of the 16 confined components made absent, a symbolic link, unusable, or redirected outside the repository; plus a dropped `tests/r3/tool-lock.mjs`, a dropped, a redirected, and a stale `tests/r3/tool-lock.conf` | 20 |
| Scratch source integrity: a dropped, truncated, or mode-altered copy of each of the 5 source components, and an undeclared second file difference in a scratch tree | 6 |
| Tool binding and Make control | 80 combined |
| Fresh worktree and symlink rejection | 6 |

Every fault kind (absent, symbolic link, unusable mode, redirected physical
path) must appear at least once in the scratch self-tests, every one of the 16
components must be covered by at least one case, and every case must be
reported as `scratch-fault` under its own component name rather than as tool
version drift, a layer rejection, or a `layer-shift`. Mutating the scratch
preparation hook out of `tests/r6/run-make.sh` or `tests/r6/build-fixture.sh`
must reintroduce the original failure, so the hook is proved load-bearing
rather than decorative.

Every layer has explicit evidence that it can fail. The four layers with no
catalogue fixture are covered here rather than by inventing fixtures for them:
**L1** by the acceptance-pin reverts, **L2** by the manifest mutations, **L4**
by the compile-stage mutation, and **L7** by the parity-stage mutation. These
are checker self-tests, not catalogue entries, so the catalogue stays a finite
list of exactly 47 real single-defect constructions and its counts stay stable.

## Report, retention, and reproducibility

Canonical report: `build/r6/reports/adversarial-images.json`, schema
`be-r6-adversarial-images-v1`. Required fields:

```text
schema, generated_by, accepted_r5_commit, accepted_r5_parent_commit,
r5_acceptance, r5_mechanism_match, baseline_immutable,
r5_implementation_content_digest, acceptance_pins_refreshed,
tool_lock_digest, base_tool_lock_digest, firmware_sha256,
scratch { trees, components_per_tree, source_components,
          base_tool_lock_sha256, byte_and_mode_verified, faults: 0 },
catalogue_digest, entries, defect_fixtures, control_fixtures,
toolchains[], host { binaries, fixtures, class_outcomes, self_tests,
                     executions, assertions },
static[] { id, base, defect_sha256, diff_sha256, layer, outcome,
           expected_messages[], toolchain_results[], qemu_invoked: false },
dynamic[] { id, base, defect_sha256, diff_sha256, layer, class, last_marker,
            forbidden_markers[], accepted_image_check, declared_delta,
            differential_result, runs[], console_sha256, trace_sha256[],
            trace_bytes[], trace_excerpt_sha256[], raw_trace_retained: false,
            qemu_status, guest_entered },
control { marker_sequence[], console_sha256, qemu_status },
coverage { classes, dynamic_primary, host_primary, secondary, uncovered,
           primary_by_class {} },
counts { build_attempts, link_failures, successful_links,
         image_check_invocations, parity_invocations,
         differential_invocations, qemu_runs, scratch_trees },
outcomes { permitted[], observed[] },
scope { hardware: "NOT-RUN", proof: "NOT-RUN-not-claimed",
        formal_verification: "not-claimed", execution: "QEMU-only",
        multicore: "out-of-scope", linux: "out-of-scope",
        services: "out-of-scope", devices: "out-of-scope",
        guest_sbi: "absent", r7_content: "excluded" },
authority { r6_plan_acceptance, r6_package_authorization,
            r6_authorization_source: "accepted-r5-package-historical",
            acceptance: "not-reviewed", publication: "blocked",
            release: "blocked" }
```

The report must be generated twice from fixed inputs and be byte identical.
Canonical semantic tuples must match across both runs and both toolchains, and
the four console logs of each dynamic fixture (2 toolchains x 2 runs) must share
one SHA-256. Raw QEMU trace logs are **not** byte identical across launches;
R6 inherits the accepted R5 semantic-versus-byte boundary unchanged and claims
no byte reproducibility for raw traces, evidence bundles, or generated HTML.
Each run's `trace_sha256` and `trace_bytes` are recorded as observed facts
about a deleted scratch file, and equality across runs or toolchains is
neither required nor claimed.

Retention under `build/r6/evidence/`, corrected by
[Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention):
the report, all 64 console logs, all 64 exit-status files, all 64 canonical
semantics records (each carrying its raw-trace SHA-256 and byte count), all 64
bounded trace excerpts (at most the first 400 and last 800 trace lines of each
run), the fixture catalogue and per-fixture manifests, static rejection
transcripts, the 30 scratch preparation banners, image manifests, a coverage
ledger, a claim ledger, and `artifacts.sha256` over every retained byte.
**No raw QEMU trace log is retained.** Each raw trace is ephemeral scratch:
`tests/r6/check-dynamic.mjs --extract` derives the semantics record, the
SHA-256, the byte count, and the bounded excerpt from it, and
`tests/r6/run-qemu.sh` deletes it before the next run starts, so the ~310-370
MiB per-run trace never enters the evidence tree. Retained evidence must not
exceed 512 MiB; that gate is hard, enforced by measurement, and exceeding it
is a failure requiring plan revision rather than a larger cap. Scratch trees
themselves are build products under `build/r6/scratch/` and are not retained
as evidence.

`tests/r6/check-acceptance.sh` must report, at implementation time:

```text
r6_plan_acceptance=<state>
r6_package_authorization=authorized
r6_implementation=<state>
r6_acceptance=not-reviewed
r6_hardware_validation=NOT-RUN
r6_formal_verification=NOT-RUN-not-claimed
r6_publication_scope=blocked
```

`r6_plan_acceptance` names the exact accepted plan state and never a summary of
it: `accepted` is reportable only while the implemented package matches an
accepted exact plan target, and any plan revision awaiting acceptance must be
reported as not accepted rather than folded into the accepted value.
[Plan revision R6-A](#plan-revision-r6-a-d-15-injection-site) is itself
accepted at exact corrected plan target
`75269f058ae578b0a76a113d6c05c0aaceeac8ec`, and
[Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention)
is accepted at exact plan-revision target
`6d6464c6c937abccd59df932006c1049fd79fac6`, so an implemented package matching
the accepted plan text carried by those targets may report `accepted`; any
later unaccepted revision may not, and a package depending on such a revision
must report `r6_plan_acceptance` as not accepted.

**The field is `r6_package_authorization`, not `r6_authorization`.** The
accepted R5 package owns the literal `r6_authorization=not-authorized`: it is
printed by `tests/r5/check-acceptance.sh`, required verbatim by the
`requiredAuthoritySnippets` list in `tests/r5/check-accepted-content.mjs`,
asserted again in `tests/r5/test-acceptance-content.mjs`,
`tests/r5/check-report.mjs`, `tests/r5/generate-report.mjs`,
`tests/r5/test-report-rejection.mjs`, and `tests/r5/generate-evidence.sh`, and
the string `r6_authorization=authorized` is explicitly listed in
`forbiddenAuthorityClaims`. That is a deliberate, accepted historical
statement about what the R5 package itself authorized, and R6 must neither
contradict it nor rewrite it.

R6 therefore owns a **distinct live key**. The two facts coexist without
ambiguity:

| Key | Owner | Meaning | May R6 change it |
| --- | --- | --- | --- |
| `r6_authorization=not-authorized` | accepted R5 | R5 acceptance did not authorize R6 | never |
| `r6_package_authorization=authorized` | R6 | the responsible human separately authorized the R6 package after exact plan acceptance | R6 sets it |

`tests/r6/check-acceptance.sh` must never print `r6_authorization=` in any
form, so no duplicate semantic key can appear in any single output stream. It
must never print an acceptance, and it must never be edited to assert one.

**Scope of the `r6_authorization=authorized` prohibition.** The prohibition is
on *emitting or claiming* that string from an authority-bearing surface, not on
*mentioning* it. This mirrors the accepted R5 enforcement exactly: R5's
`forbiddenAuthorityClaims` list is evaluated only against `authoritySource`,
which `tests/r5/check-accepted-content.mjs` binds to the content of
`tests/r5/check-acceptance.sh`, and only as the exact printf statement
`printf 'r6_authorization=authorized\n'`. R5 does not scan the repository, the
planning documents, or the review packets for the literal, and R6 must not
either.

R6's enforcement is therefore narrow and enumerated:

| Enforcement point | Checked object | Rule |
| --- | --- | --- |
| `tests/r6/check-sources.mjs` | source text of `tests/r6/check-acceptance.sh`, `tests/r6/generate-report.mjs`, `tests/r6/generate-evidence.sh`, `tests/r6/check-report.mjs`, `tests/r6/r6-check.c`, `tests/r6/Makefile`, `tests/r6/run-make.sh`, and the R6 lines of `be` and `scripts/check-be.sh` | no statement that emits `r6_authorization=authorized`, and no occurrence of the literal `r6_authorization=` outside the exactly one `be`/`scripts/check-be.sh` assertion of the accepted R5-sourced `r6_authorization=not-authorized` line |
| `tests/r6/check-acceptance.sh` self-check | emitted stdout of `tests/r6/check-acceptance.sh` | zero occurrences of `r6_authorization=` |
| `tests/r6/check-report.mjs` | emitted `build/r6/reports/adversarial-images.json` | `authority` carries `r6_package_authorization` and no `r6_authorization` key |
| `tests/r6/generate-evidence.sh` claim ledger | emitted evidence lines | same rule as the report |
| `scripts/check-be.sh` | emitted `be status` and `be r6-check` output | `r6_authorization=` appears exactly once and its value is `not-authorized`; `r6_package_authorization` appears exactly once |
| `tests/r6/test-report-rejection.mjs` | mutated report | a forged `authority.r6_authorization = 'authorized'` and a forged `r6_package_authorization = 'accepted'` must both be rejected |

Planning documents, review packets, evidence prose, and this plan may quote
the forbidden literal in order to explain it; that is documentation, not an
authority claim, and no R6 checker may fail because of it. Nothing in this
plan authorizes a repository-wide textual ban, and R6 must not add one.

`r6_package_authorization=authorized` is true only once the responsible human
has accepted an exact plan commit; that gate was satisfied by accepted target
`609867fdad75279c0913022909efd65c4a838909`. **A commit that records a plan
decision must not itself claim that implementation is complete or accepted:**
it may state plan state in the planning documents, and it must leave
`r6_implementation` reported honestly, stage no `tests/r6/` implementation, and
assert no R6 evidence, coverage, or acceptance result.

## Root integration

Planned, and inert until R6 is implemented:

- root `Makefile`: `r6-check` and `r6-evidence` targets delegating to
  `tests/r6/run-make.sh`, and an R6 step appended after the R5 step in `check`;
- root `be`: `r6-check` and `r6-evidence` subcommands, `be help` lines, and
  `be status` fields `r6_authorization_source`, `r6_plan_acceptance`,
  `r6_package_authorization`, `r6_implementation`, `r6_acceptance`,
  `r6_hardware_validation=NOT-RUN`,
  `r6_formal_verification=NOT-RUN-not-claimed`,
  `r6_publication_scope=blocked`;
- `scripts/check-be.sh`: exact assertions for each new help and status string,
  including `r6_package_authorization=authorized`, added **alongside** the
  existing `r6_authorization=not-authorized` assertion rather than replacing
  it.

### `be status` without a duplicate semantic key

`be` today validates the R5 checker output, requires the literal
`r6_authorization=not-authorized` inside it, emits that checker block verbatim
into `be status`, and then prints its own fields, including
`r5_implementation_review=responsible-human-accepted` and
`r6_implementation=not-started`. `scripts/check-be.sh` asserts
`r6_authorization=not-authorized` in `be status`.

R6 must preserve all of that byte for byte. The R5-sourced block is emitted
unchanged, and the R6 fields are added to the existing `be`-owned section that
already follows it, with one provenance line so a reader can tell which
package owns which statement:

```text
...                                     (R5 checker block, unchanged)
r6_authorization=not-authorized
r5_publication_scope=blocked
r5_hardware_validation=NOT-RUN
r5_formal_verification=NOT-RUN-not-claimed
r5_implementation_review=responsible-human-accepted
r6_authorization_source=accepted-r5-package-historical
r6_plan_acceptance=<state>
r6_package_authorization=<state>
r6_implementation=<state>
r6_acceptance=not-reviewed
r6_hardware_validation=NOT-RUN
r6_formal_verification=NOT-RUN-not-claimed
r6_publication_scope=blocked
...                                     (remaining be-owned fields, unchanged)
```

No key is printed twice, so no consumer has to decide which line wins.
`r6_authorization_source` names the provenance of the historical line without
restating or contradicting its value. `scripts/check-be.sh` asserts the exact
historical line, the exact new lines, and additionally asserts that
`r6_authorization=` appears exactly once in `be status`. R6 keeps the accepted
`NOT-RUN` and `NOT-RUN-not-claimed` spellings rather than introducing a new
form.

R6 must not change, remove, or reinterpret the R5-sourced line, and must not
emit `r6_authorization=authorized` from any authority-bearing surface listed in
the enforcement table above. Quoting the literal in planning prose to explain
the prohibition remains permitted and is not a violation.

### Effect on accepted acceptance status

Root `Makefile`, `be`, and `scripts/check-be.sh` are **not** in the accepted R5
`immutablePaths` set, but they are bound by the R1, R3, and R4 acceptance
checkers as described under **Authorized acceptance-pin refresh**. The six
enumerated constants are refreshed in the same commit and in the stated order,
and the mandatory negative checks prove that R1, R2, R3, R4, and R5 all still
report acceptance with matching mechanisms and that
`r5_implementation_content_digest` is unchanged. R6 must not proceed to create
`tests/r6/**` until those checks pass.

## Validation commands and acceptance criteria

Targeted:

```sh
./tests/r6/run-make.sh r6-toolcheck
./tests/r6/run-make.sh r6-baseline
./tests/r6/run-make.sh r6-host-test
./tests/r6/run-make.sh r6-fixture-check
./tests/r6/run-make.sh r6-static
./tests/r6/run-make.sh r6-dynamic
./tests/r6/run-make.sh r6-report
./tests/r6/run-make.sh r6-evidence
./tests/r6/run-make.sh r6-check
./be r6-check
./be r6-evidence
```

Complete gate:

```sh
make check && ./be r5-check && ./be r6-check
npm run docs:build && ./be docs-check && scripts/check-be.sh
```

Acceptance criteria for a future R6 implementation commit:

1. `tests/r5/check-acceptance.sh --require` reports `r5_acceptance=accepted`
   and `r5_accepted_mechanism_match=yes` before and after the R6 package, with
   an unchanged `r5_implementation_content_digest`.
2. `tests/r1/check-acceptance.sh --require`, `tests/r2/check-acceptance.sh
   --require`, `tests/r3/check-acceptance.sh --require`, and
   `tests/r4/check-acceptance.sh --require` all pass, each reporting its
   accepted mechanism match as `yes`.
3. No byte of any accepted R0-R5 **mechanism** path changed. The only
   predecessor edits are the six enumerated acceptance-pin constants, each
   proven live by its revert self-test.
4. All 47 catalogue entries present; 46 carry exactly one declared defect.
5. Every `S-*` and `H-*` fixture rejected at its declared layer, with zero QEMU
   invocations for the static and host partitions.
6. Every `D-*` fixture reaches its declared L6 disposition, passes the L8
   differential with exactly its declared delta, and terminates fail-closed
   with the declared class, declared last marker, no forbidden marker, and QEMU
   status `0`, across 2 toolchains x 2 runs. For D-15 specifically, L8 records
   exactly 2 differing runs and 10 differing bytes at the exact per-toolchain
   offsets pinned by
   [Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention),
   with `.monitor.text` allocated size unchanged and every defined allocated
   `FUNC`/`OBJECT` symbol in the accepted checker's fixed and required sets
   keeping its address from the same-toolchain control image
   (`be_r5_switch_tail`'s address is unchanged; only its `st_size` differs,
   `212`->`220`). Non-allocated debug/symbol-table changes (GCC `.debug_line`,
   `.debug_str`, `.debug_frame`, `.symtab`, `.strtab`, `.shstrtab`; Clang
   `.debug_line`, `.debug_aranges`, and 12 local `$d` mapping symbols) are
   excluded from this criterion.
7. Control C-01 reproduces the exact 22-line accepted marker sequence
   `BE_R3:01..07`, `BE_R4:01..03`, `BE_R5:01..12`, line for line.
8. Coverage ledger shows 29 primary classes, 0 uncovered, and 4 secondary
   claims not counted toward completeness.
9. Every fixed count in the build matrix matches the generated report.
10. Report generated twice, byte identical, schema
    `be-r6-adversarial-images-v1`.
11. All self-test minima met, including one negative self-test per host
    fixture, the L1, L2, L4, L7, and L8 stage mutations, and the scratch and
    R3 base-lock prerequisite cases; all hostile-control and fresh-worktree
    cases pass.
12. Every one of the 30 scratch trees held all 5 source components byte-and-mode
    identical apart from its single overlaid defect, all 16 confined components
    existed, the scratch `tests/r3/tool-lock.conf` matched
    `c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b`, and the
    report records `scratch.faults = 0`. No accepted R5 phony target was
    invoked for a mutated image.
13. `be status` prints `r6_authorization=` exactly once, sourced from the
    accepted R5 checker and valued `not-authorized`, and prints the distinct
    live `r6_package_authorization` field; no R6 authority-bearing surface
    emits `r6_authorization=authorized`.
14. `make check` passes; `./be docs-check` and `scripts/check-be.sh` pass.
15. Hardware validation and formal verification remain `NOT RUN`.
16. Acceptance reported as `not-reviewed`; publication reported as `blocked`.
17. Every one of the 64 runs contributes a canonical semantics record, a
    raw-trace SHA-256, a raw-trace byte count, and a bounded trace excerpt; no
    raw QEMU trace log is present anywhere under `build/r6/evidence/`; and the
    measured retained evidence is at or under 512 MiB.
18. The implemented package matches an accepted exact plan target: the
    accepted plan text carried by `75269f058ae578b0a76a113d6c05c0aaceeac8ec`
    as revised by
    [Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention),
    accepted at `6d6464c6c937abccd59df932006c1049fd79fac6`. If any later plan
    revision is unaccepted, `tests/r6/check-acceptance.sh` must report
    `r6_plan_acceptance` as not accepted, and no R6 integration, evidence
    bundle, report claim, or acceptance may be presented as satisfying this
    plan.

## Trust assumptions

1. Pinned GCC, Clang, GNU `ld`, `lld`, GNU Make, `bash`, and Node are trusted
   and digest-bound.
2. Pinned QEMU 10.2.2 and pinned OpenSBI are trusted and digest-bound; R6 does
   not model firmware defects and does not forge firmware.
3. The accepted R0-R5 mechanism is trusted as the measurement instrument; R6
   measures inputs against it and never modifies it.
4. QEMU faithfully models the bounded RISC-V H-extension behavior exercised
   here; QEMU is not hardware.
5. A single hart, no DMA, no external device, and no concurrency.

## Supported claims

If this plan is accepted, implemented, and validated, R6 supports exactly:

> In the fixed single-hart QEMU `virt` profile, with pinned OpenSBI and the
> byte-immutable accepted R5 target `165f4d001a2b59b582b397bdea79ec4826168fdb`,
> 46 separately constructed single-defect adversarial fixtures were each
> rejected or terminated fail-closed at their declared layer: 14
> image-construction defects were rejected before any execution, four by the
> accepted source inventory (extra `sret`, removed non-compressed pin,
> neutral-core assembly, undeclared build input), four by accepted linker
> assertions (moved root pool, moved guest section, resized saved page,
> changed fixture slot count), and six by the accepted image checker (unpaired
> root write, duplicate root write, post-publication diagnostic, duplicate
> publication tail site, calling tail, root-pool reference on the trap path);
> 17 host-mechanism defects produced their exact stable error class; and 15
> dynamic defects each terminated at the declared phase with the exact stable
> error class, the declared last console marker, no forbidden marker, and a
> monitor-issued SBI SRST shutdown, over two toolchains and two runs each.
> Each dynamic image additionally differed from its same-toolchain control
> image by exactly the one declared delta and in no other byte.

## Explicit non-claims and exclusions

R6 does **not** claim:

- that malicious or arbitrary guests are universally contained; the catalogue
  is finite and enumerated, not exhaustive;
- that a declared accepted-image-checker rejection makes a dynamic fixture
  safe on its own; safety for those images rests on the L8 single-delta
  comparison against a control image that passed the complete accepted
  checker, plus the immutable accepted G-stage roots;
- that the accepted R1, R3, and R4 acceptance checkers were left untouched;
  exactly six enumerated pin constants are refreshed, and no accepted
  mechanism byte changes;
- any hardware or emulator behavior for a genuinely skipped `HFENCE.GVMA`; only
  that the accepted checker rejects the unpaired construction (S-05) and the
  monitor refuses an unacknowledged fence (D-11);
- formal verification, refinement, or proof of the mechanism or the fixtures;
- coverage of `shutdown-returned` or `shutdown-rejected` under QEMU;
- general asynchronous interrupt handling; exactly one monitor-injected VS
  software interrupt is exercised, with no timer, external, or nested case;
- byte-identical raw QEMU traces, evidence bundles, or generated HTML;
- any property of a raw QEMU trace beyond its recorded SHA-256, byte count,
  bounded excerpt, and the canonical semantics derived from it; raw traces are
  ephemeral scratch, are deleted after extraction, and are never retained,
  digested as evidence files, or published;
- hardware validation, K3 results, multi-hart behavior, DMA/IOMMU behavior, or
  device isolation;
- Linux, service, driver, scheduling, restart, rollback, policy, capability,
  Type Enforcement, or CHERI behavior;
- any R7 result, any acceptance, or any publication readiness.

Hardware validation: **NOT RUN**. Formal verification: **NOT RUN**. Multi-hart:
**out of scope**. The open generated-asset reproducibility finding remains
unresolved.

## Publication, R7, and governance

- Publication, push, tag, and release remain **blocked**. R6 does not touch
  `pathfinder/publication-gate.conf` and cannot infer approval.
- R7 remains gated and undefined; R6 acceptance would not authorize it.
- No automated agent may add a human `Signed-off-by`, record acceptance, or
  represent itself as a human co-developer.
- The two recorded proceed instructions authorize R6 implementation work under
  the master-plan R6 row; they do not accept this plan and cannot accept the
  future exact commit that contains it.

## Review-gate checklist

The responsible human should confirm, at an exact commit:

1. The no-production-surface decision and its four justifications are correct.
2. The immutable accepted-byte list is complete and correct, and the
   authorized six-constant acceptance-pin refresh with its ordering and
   negative checks is acceptable and matches the accepted R5 precedent.
3. The 47-entry catalogue is finite, exact, and within the master-plan row.
4. Every static fixture proves checker rejection rather than executing an
   unsafe image, and each is assigned to the layer that actually rejects it.
5. Every dynamic fixture is safe, deterministic, terminating, and fail-closed,
   and the per-partition applicability rules are a bounded declared
   disposition rather than a bypass of the accepted image checker.
6. The skipped-fence treatment (static S-05 plus acknowledgement-withheld D-11)
   is acceptable and free of over-claim.
7. The fixed RISC-V values, opcodes, causes, and expected classes match
   accepted R1-R5, and the 22-line accepted console sequence is reproduced
   exactly.
8. The outcome taxonomy, marker vocabulary, and layer-shift rule are sound.
9. The counts, toolchains, matrix, self-tests, and locks are sufficient, and
   every layer has explicit failure evidence.
10. The scratch contract is complete: 5 source components including the two
    `tests/r3/` lock files, 16 confined components, verified base-lock digest,
    and a `scratch-fault` diagnostic that can never be mistaken for tool
    version drift or a fixture result.
11. Every host fixture names a real member of a real accepted structure, and
    each declared mutation is the first failure at the named API by the
    recorded validation order.
12. The coverage ledger is disjoint, with one primary fixture per class and
    secondary coverage listed separately.
13. Introducing the distinct live key `r6_package_authorization` while
    preserving the accepted R5 `r6_authorization=not-authorized` line is the
    right resolution of the status collision, and scoping the
    `r6_authorization=authorized` prohibition to authority-bearing surfaces
    rather than to all repository prose matches the accepted R5 enforcement.
14. The report schema, retention, and reproducibility boundary are honest.
15. The claims, non-claims, and `NOT RUN` boundaries are accurate.
16. Whether to accept this revised plan, and separately whether the recorded
    authorization remains sufficient to resume implementation at the accepted
    commit. Accepting this revision does not accept any implementation; the
    acceptance commit must contain no staged `tests/r6/` implementation and
    must claim no R6 evidence, coverage, or acceptance result.
17. [Plan revision R6-A](#plan-revision-r6-a-d-15-injection-site) specifically:
    that the accepted D-15 injection site was genuinely unreachable, that the
    corrected two-instruction insertion in a copied `arch/riscv/be/r5-trap.S`
    is the narrowest correction, that its expected deterministic result and
    accepted-checker disposition are right, that the wrong-error-class gate is
    preserved, and that the unretained development-session exploratory report
    of the corrected placement is not cited as evidence or as a reason for
    acceptance.
18. [Plan revision R6-B](#plan-revision-r6-b-d-15-image-layout-and-trace-retention)
    specifically: that withdrawing the false "grows by 8 bytes" layout claim
    and replacing it with the alignment-padding account is correct; that
    pinning D-15's L8 delta to exactly 2 runs, 10 bytes, and the stated
    per-toolchain offsets, with no run-time relaxation, is the right
    fail-closed rule; that making raw QEMU traces ephemeral — extracted into
    canonical semantics, a SHA-256, a byte count, and a bounded excerpt, then
    deleted — resolves the impossible 32-trace retention requirement without
    weakening the hard 512 MiB gate or claiming raw-trace byte identity; that
    retaining 64 semantics records and 64 bounded excerpts matches the
    implemented safe design; that every preserved count, class, gate, and
    authorization is genuinely unchanged; and that the local unreviewed
    measurements behind this revision are correctly excluded from evidence.
    Accepting revision R6-B accepts no implementation and no R6 evidence.
