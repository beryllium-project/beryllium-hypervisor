<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R2 Sv39x4 backend evidence

## Status and claim boundary

R2 is the non-privileged host-tested Sv39x4 backend package in the accepted
[bounded single-hart runtime plan](single-hart-runtime-plan.md). The
[R2 bounded plan](single-hart-runtime-r2-plan.md) was accepted by
responsible-human review at exact commit
`cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` on 2026-07-28; R2 implementation
was separately authorized on the same date. The acceptance record is
[`single-hart-runtime-r2-plan-review-summary.md`](single-hart-runtime-r2-plan-review-summary.md).

R2 implementation is complete and accepted. Responsible-human review accepted
exact implementation commit `6e1cb579257c5dbe3234bd484fd091629e87181b` on
2026-07-28. The acceptance record is
[`single-hart-runtime-r2-review-summary.md`](single-hart-runtime-r2-review-summary.md).
`tests/r2/check-acceptance.sh` reports `r2_acceptance=accepted` and
`r2_accepted_mechanism_match=yes` when the R2 implementation inputs match
that exact commit.

Precise limits:

- R2 links **no** Beryllium image and adds **no** assembly, boot path,
  privileged instruction, trap path, or Beryllium QEMU execution.
- The HGATP values are computed but **not written** to CSRs.
- R2 is **not** formally verified, not a Model 0.2 Rocq refinement, not
  hardware validated, and not a production hypervisor.
- R2-scoped Beryllium QEMU and K3 hardware evidence remains **NOT RUN**.
  Later R3 QEMU evidence and retained Helium evidence do **not** validate R2.
  Public release remains **blocked**.
- R3 was subsequently separately authorized on 2026-07-29 and is now complete
  locally and review required. That later status does not change R2's accepted
  non-privileged claim boundary; R2 acceptance itself did not authorize
  tagging, pushing, public release, or R3.
- Documentation functional gates pass. Generated VitePress asset
  byte-reproducibility remains **unresolved** (see §8). This finding is not
  accepted, resolved, or harmless.

## 1. Component and API tour

### R2 contract header

- `include/be/r2.h` — Sv39x4 architecture constants (`BE_SV39X4_GPA_WIDTH`,
  `BE_SV39X4_PA_WIDTH`, `BE_SV39X4_PPN_WIDTH`, `BE_HGATP_MODE_SV39X4`),
  one-way R2 state enum (`be_r2_state`), pool descriptor
  (`be_r2_pool_desc`), result/output structs (`be_r2_result`,
  `be_r2_output`), leaf enumeration structs (`be_r2_leaf`,
  `be_r2_leaf_set`), and the two public API functions (`be_r2_build`,
  `be_r2_walk_and_check`).

### RISC-V Sv39x4 implementation

- `arch/riscv/be/sv39x4.c` — non-privileged Sv39x4 page-table builder,
  independent walker, and read-only re-walk. Pool memory is accessed
  exclusively through LE byte-buffer helpers (`pte_store_le64`,
  `pte_load_le64`) with bounded offsets and no pointer casts. File-static
  helpers include `resolve_frame_pa`, `extract_vpn`, `build_one_root`,
  `walk_one_root`, `revalidate_r1`, `validate_frozen_profile`,
  `validate_pool_desc`, and `validate_root_pool_binding`.

### R1 source (read-only compile inputs)

R2 composes over the accepted R1 mechanism commit
`a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` through const pointers only:

- `include/be/types.h`, `include/be/manifest.h`, `include/be/state.h`,
  `include/be/r0-config.h`, `include/be/r1-config.h` — frozen headers.
- `virt/be/manifest.c`, `virt/be/state.c`, `virt/be/r1-config.c` —
  frozen R1 implementations.
- `arch/riscv/be/r0-layout.h` — frozen physical layout.

**R2 does not modify any R1 source file.** `tests/r1/check-acceptance.sh`
confirms `r1_accepted_mechanism_match=yes`.

### Host evidence tools

- `tests/r2/r2-check.c` — 95 test scenarios producing 5511 assertions:
  positive flow, adversarial builder/walker/state, pool/root/mapping
  rejection, frozen-profile divergence, failure isolation, and terminal
  state coverage.
- `tests/r2/r2-report.c` — deterministic JSON report generator with R1
  identity, R2 state, two roots, pointer layout, decoded leaves, unused
  storage, and claim boundaries.
- `tests/r2/check-report.mjs` — semantic checker validating exact report
  structure, HGATP values, PTE flag bits, pointer layout, leaf mappings,
  rights, unused storage, and claim fields.
- `tests/r2/check-acceptance.sh` — R2 acceptance-status checker; reports
  `accepted` when the R2 implementation inputs match the accepted commit
  `6e1cb579257c5dbe3234bd484fd091629e87181b`.
- `tests/r2/generate-evidence.sh` — retained source/tool/artifact identity
  bundle under `build/r2/evidence/`.
- `tests/r2/Makefile` — self-contained build graph with `r2-test`,
  `r2-report`, `r2-evidence`, and `r2-check` targets. Does not modify
  `tests/Makefile` or the root `Makefile`.
- `./be r2-check` and `./be r2-evidence` — stable wrapper entry points.
- `scripts/check-be.sh` — validates R2 wrapper dispatch and status fields.

## 2. Exact fixed profile

R2 consumes the R1 sealed canonical state and builds concrete Sv39x4
page-table trees for the fixed thirteen-resource full profile:

| Resource category | Count | Notes |
| --- | --- | --- |
| Monitor code/data | 2 | trusted monitor-owned extents |
| Root-table storage | 2 | 32 KiB pools, one per domain |
| Trusted stacks | 2 | one per domain |
| Saved-state storage | 2 | one per domain |
| Private data pages | 2 | one management, one protected |
| Shared page | 1 | directional management-RW to protected-R |
| Guest-code pages | 2 | R-X operational-extension resources |
| **Total** | **13** | fixed full profile |

### Canonical authorities (6)

| Domain | Authorities |
| --- | --- |
| management | private `rw`, shared `rw`, guest-code `rx` |
| protected | private `rw`, shared `r`, guest-code `rx` |
| **Total** | **6** |

### Derived enforcement (2 roots × 3 leaves)

| Root | Domain | Mapping | GPA | Frame ID | PA | Rights |
| --- | --- | --- | --- | --- | --- | --- |
| 101 | management | 1 | `0x40000000` | 9 | `0x8022e000` | RW |
| 101 | management | 2 | `0x40002000` | 11 | `0x80230000` | RW |
| 101 | management | 3 | `0x40010000` | 12 | `0x80232000` | R-X |
| 102 | protected | 1 | `0x40001000` | 10 | `0x8022f000` | RW |
| 102 | protected | 2 | `0x40002000` | 11 | `0x80230000` | R |
| 102 | protected | 3 | `0x40011000` | 13 | `0x80233000` | R-X |

### Pool layout

Each 32 KiB pool is 8 consecutive 4 KiB pages:

| Pool page | Offset | Role | Written by R2 |
| --- | --- | --- | --- |
| 0 | `+0x0000` | Root table [0..511] | yes (one pointer PTE at entry 1) |
| 1 | `+0x1000` | Root table [512..1023] | no (zeroed) |
| 2 | `+0x2000` | Root table [1024..1535] | no (zeroed) |
| 3 | `+0x3000` | Root table [1536..2047] | no (zeroed) |
| 4 | `+0x4000` | L1 table | yes (one pointer PTE at entry 0) |
| 5 | `+0x5000` | L0 table (leaves) | yes (3 leaf PTEs) |
| 6 | `+0x6000` | Spare | zeroed, verified unused |
| 7 | `+0x7000` | Spare | zeroed, verified unused |

### Root entry 1 and L1 entry 0

All six GPAs share VPN[2]=1 and VPN[1]=0. The builder installs exactly one
non-leaf pointer PTE in the root table at entry index 1 (VPN[2]=1, byte
offset 8), pointing to the L1 page at pool offset `+0x4000`. One non-leaf
pointer PTE in L1 at entry index 0 (VPN[1]=0, byte offset `+0x4000`) points
to the L0 page at pool offset `+0x5000`. Three leaf PTEs in L0 encode the
mapped frames with exact rights.

### Spare page verification

Pool pages 6 and 7 (`+0x6000` through `+0x7FFF`) must remain entirely zero.
The walker verifies this as part of its structural checks; any nonzero byte
in spare storage fails the walk.

### HGATP computation

```text
Management: MODE=Sv39x4(8) << 60 | VMID=0 | PPN=0x80214000>>12 = 0x8000000000080214
Protected:  MODE=Sv39x4(8) << 60 | VMID=0 | PPN=0x8021c000>>12 = 0x800000000008021c
```

These values are computed and stored in `be_r2_output.results[].hgatp`. They
are **not** written to the `hgatp` CSR. CSR writes, `HFENCE.GVMA`, and VS
entry are R3 scope.

## 3. R1 preservation and const composition

R2 accesses R1 state exclusively through a `const struct be_runtime *`
pointer. R2 does not mutate, extend, or add phases to R1 state. The R1
`struct be_runtime` remains valid and at phase `DERIVED` after R2 completion
or failure.

R2 owns a **separate one-way state** (`enum be_r2_state`) tracking only R2
progress:

```text
EMPTY -> BUILT   (both roots built and walked successfully)
EMPTY -> FAILED  (terminal: R2 encountered an error; no retry)
```

R1 const composition means:

- `be_check_canonical` and `be_check_enforcement` are called as read-only
  validation at R2 entry, not modified.
- Configuration identity `0x771e1e75110201ac` is verified against sealed
  canonical state by full `sealed_integrity_result` reconstruction.
- R2 does not change the R1 phase machine, sealed identity, or enforcement
  state.

### Plan acceptance SHA

The R2 bounded plan was accepted at exact commit
`cdcf1603b97e0ef4da3e571e43fd7045116ea1ce`. The plan file
`planning/single-hart-runtime-r2-plan.md` is byte-identical to that commit.
The acceptance and implementation-authorization decisions are recorded in
[`single-hart-runtime-r2-plan-review-summary.md`](single-hart-runtime-r2-plan-review-summary.md).

## 4. All-or-nothing failure, scrub, and terminal R2 state

R2 enforces an all-or-nothing transaction contract:

- **No partial publication.** HGATP values and leaf counts are written to
  `be_r2_output` only after BOTH roots are built AND independently walked
  successfully.
- **Both pools scrubbed on failure.** After both pool descriptors are
  validated as scrub-safe (non-NULL buf, exact buf_size), they are zeroed at
  attempt entry. On any subsequent failure, both are re-zeroed so no partial
  PTE content remains observable.
- **Terminal state.** `BE_R2_STATE_FAILED` is permanent. No retry, reset, or
  re-entry API exists.
- **R1 unchanged.** R1 remains valid at phase `DERIVED` after R2 failure.
  The const pointer prevents mutation.
- **One-valid/one-invalid descriptor.** If exactly one descriptor has valid
  buf/buf_size, R2 scrubs the valid one and sets FAILED. It never dereferences
  a NULL buf or writes beyond a declared buf_size.
- **NULL output returns early.** If `output` is NULL, R2 returns
  `BE_CHECK_NULL` immediately without touching state or pools.
- **Non-EMPTY output returns early.** If `output->state` is not
  `BE_R2_STATE_EMPTY`, R2 returns `BE_CHECK_INVALID_PHASE` without changing
  terminal state.

### Trusted partial-overlap and concurrency cut points

- **Host-buffer non-overlap:** Portable restricted C can reject identical
  start pointers (`pools[0].buf != pools[1].buf`) but cannot prove that two
  arbitrary declared 32 KiB allocations do not partially overlap.
  Comparing interior or end pointers across distinct allocations is undefined
  behavior under the C standard. R2 host tests use distinct `static be_u8`
  arrays; R3+ derives pointers from non-overlapping physical extents.
- **Sequential single-caller:** The transaction-like guarantee is a
  single-caller sequential contract, not C11 concurrency atomicity. R2
  assumes no concurrent observer reads `pools` or `output` during the call.

## 5. Test coverage

`tests/r2/r2-check.c` contains 95 named test scenarios producing 5511
individual assertions across GCC and Clang strict builds. Categories:

### Positive tests (P1–P11)

Full end-to-end R1 seal/derive → R2 build → independent walk; exact HGATP
encoding for both roots; per-root leaf counts; pool-page structure (one root
pointer, one L1 pointer, three leaf PTEs); unused root/L1 entry verification;
spare-page cleanliness; independent re-walk via `be_r2_walk_and_check`
matching builder output.

### Adversarial/negative tests — R1 integrity (N1–N8g)

NULL runtime; wrong phase (SEALED, EMPTY); canonical identity mismatch;
enforcement identity mismatch; not sealed; already BUILT; already FAILED;
NULL output; validated_identity zero; sealed_identity zero; identity cross
mismatch; sealed ≠ canonical; recompute mismatch; check_result bad.

### Adversarial/negative tests — pool descriptors (N9–N16d)

NULL buf; NULL pools; misaligned base; undersized; oversized; duplicate base;
duplicate buf pointer; PPN overflow; 64-bit overflow; PA exceed; PA boundary
crossing; one-valid/one-invalid scrub; early failure scrub verification.

### Adversarial/negative tests — root and mapping (N17–N32)

Wrong root count; wrong mapping count; absent frame; wrong frame size; wrong
frame class; frame PA alignment; frame PA width; frame PA overflow; GPA width;
GPA alignment; zero rights; W without R; wrong VPN[2]; wrong VPN[1]; duplicate
GPA; swapped pools; same pool.

### Adversarial/negative tests — walker structural (N33–N51)

Corrupt root pointer PPN; corrupt L1 pointer PPN; L2 leaf (no huge pages);
L1 leaf (no superpages); extra leaf; missing leaf; wrong PA; wrong rights;
no U; no A; W without D; high bits; G set; RSW nonzero; unexpected root
entry; unexpected L1 entry; spare nonzero; malformed pointer; pointer PPN
overflow.

### Adversarial/negative tests — failure isolation (N52–N56)

First root failure zeroes both pools; second root failure zeroes both pools;
walker fails on second root; terminal state verified; R1 runtime phase
unchanged.

### Adversarial/negative tests — frozen-profile divergence (N57–N64)

Non-frozen root IDs; non-frozen domain ordering; non-frozen GPA; wrong
configuration version; wrong architecture; wrong profile; excess mappings.

### Audit and walker edge cases

Frozen frame base; frozen saved state; frozen channel; walk wrong bufsize;
walker leafsets zeroed on phase error.

### Passing output

```text
BE_R2_CHECK: starting R2 Sv39x4 backend host tests
BE_R2_CHECK: 5511 tests, 0 failures
BE_R2_CHECK: PASS
Beryllium R2 Sv39x4 backend tests: PASS
```

## 6. Deterministic report and semantic checker

`make -C tests/r2 r2-report`:

1. builds GCC and Clang host report tools with strict warnings;
2. emits compiler-specific JSON (`sv39x4.gcc.json`, `sv39x4.clang.json`);
3. compares the two byte-for-byte (compiler independence);
4. retains `build/r2/reports/sv39x4.json`; and
5. runs `tests/r2/check-report.mjs` for structural and semantic validation.

The deterministic report `build/r2/reports/sv39x4.json` records:

- Schema `be-r2-sv39x4-backend-v1`, package `single-hart-runtime-r2`.
- R1 identity: configuration identity `0x771e1e75110201ac`, phase `derived`,
  sealed `yes`, check result `ok`, 2 derived roots, 6 derived mappings.
- R2 state: `built`, build result `ok`.
- Two roots with exact HGATP values, 3 leaves each.
- Pointer layout: root pointer at offset 8 (VPN[2]=1), L1/L0 PPNs.
- Decoded leaves with GPA, PA, PPN, rights, and all PTE flag bits.
- Unused storage verification (spare pages zero).
- Claims: `sv39x4_roots=2`, `hgatp_csr_written=no`, `privileged_code=no`,
  `formal_verification=no`, `model_0_2_refinement=no`,
  `qemu_beryllium_result=NOT-RUN`, `hardware_validation=NOT-RUN`,
  the then-current historical `r3_status=not-started`, and
  `public_release=blocked`. R3's later separate authorization and
  implementation-content completion do not retroactively change that accepted
  R2 report.

The semantic checker validates exact HGATP values (management
`0x8000000000080214`, protected `0x800000000008021c`), PTE V/R/W/X/U/G/A/D
bits, D=1 iff W=1, PPN consistency, pointer layout, leaf completeness, and
claim boundaries.

## 7. Defects found by adversarial testing

The following substantive defects were found during adversarial test
development and fixed before the current passing state:

1. **Wrong-size re-walk result.** The initial public re-walk reused the
   builder's scrub-safety predicate, which combined a null buffer and an
   incorrect buffer size into one failure. A valid buffer with a size other
   than 32 KiB therefore returned `BE_CHECK_NULL` instead of the planned
   `BE_CHECK_UNSUPPORTED`. The audit test exposed the mismatch; the re-walk
   now checks the pointer and exact size separately.

2. **Stale leaf sets on precondition failure.** The initial public re-walk
   checked whether the R2 output was `BUILT` before zeroing `leaf_sets`.
   An `BE_CHECK_INVALID_PHASE` return could therefore leave caller-provided
   stale leaf data intact. The output sets are now zeroed immediately after
   validating their pointer, before all later return paths.

3. **Explicit fixed-profile tuple gap.** Independent audit found that the
   initial R2-specific profile checker omitted explicit comparisons for the
   13 canonical frame tuples, two saved-state descriptors, six authority
   tuples, and the channel tuple. The earlier generic R1 checkers rejected
   many mutations first, masking this missing R2 rejection layer. R2 now
   checks every tuple explicitly; focused audit tests exercise frame,
   saved-state, and channel mutations, and final code review confirmed the
   complete comparison set.

## 8. Commands and wrapper status

### Direct Make targets

```sh
make -C tests/r2 r2-test        # GCC+Clang strict host tests
make -C tests/r2 r2-report      # Deterministic JSON report
make -C tests/r2 r2-evidence    # Retained evidence bundle
make -C tests/r2 r2-check       # r2-test + r2-report + r2-evidence
```

### Stable wrapper commands

```sh
./be r2-check                   # Delegates to make -C tests/r2 r2-check
./be r2-evidence                # Delegates to make -C tests/r2 r2-evidence
```

### Composite full gate (pre-commit)

```sh
make check && ./be r2-check
```

This runs all R0, R1, Model 0.2, and Helium gates first, then R2-specific
tests, reports, and evidence. R2 evidence production also requires
`tests/r1/check-acceptance.sh --require` to report
`r1_accepted_mechanism_match=yes`.

### Report and evidence artifact paths

| Artifact | Path |
| --- | --- |
| Deterministic report | `build/r2/reports/sv39x4.json` |
| Report semantic check | `build/r2/reports/report-check.txt` |
| Source state | `build/r2/evidence/source-state.txt` |
| Tool versions | `build/r2/evidence/tool-versions.txt` |
| Source hashes | `build/r2/evidence/source.sha256` |
| Artifact hashes | `build/r2/evidence/artifacts.sha256` |
| Claim status | `build/r2/evidence/claim-status.txt` |

### Documentation reproducibility limitation

Documentation functional gates (`./be docs-check`) pass: all planning and
Helium pages render correctly over HTTP and via direct filesystem access.
However, VitePress-generated asset filenames contain content hashes that vary
across builds. This byte-reproducibility limitation is recorded but
**unresolved**. It is not accepted, resolved, or harmless; it remains an
open finding inherited from the VitePress toolchain.

## 9. Claim ledger

### What R2 supports saying now

- R2 implementation is complete locally and `make -C tests/r2 r2-check` /
  `./be r2-check` pass with strict GCC and Clang host builds, adversarial
  builder/walker/state tests, byte-identical deterministic reports, report
  semantic checking, and retained source/artifact evidence.
- R2 builds two Sv39x4 page-table trees from sealed canonical authority and
  produces HGATP values for the fixed profile: 2 roots × 3 leaves each =
  6 total mappings at 4 KiB granularity.
- An independent walker confirms every leaf matches canonical authority
  exactly with no unexpected or missing entries, no nonzero unused storage,
  and all pointer PPNs verified against exact known pool addresses.
- R2 remains non-privileged: no CSR write, no QEMU execution, no image, no
  boot, no trap.
- R1 accepted mechanism is unchanged: `r1_accepted_mechanism_match=yes`.
- R2 plan acceptance SHA `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` is
  recorded; the plan file is byte-identical to that commit.
- R2 acceptance is `accepted`; exact implementation commit
  `6e1cb579257c5dbe3234bd484fd091629e87181b` was accepted on 2026-07-28.

### Retained evidence claim status

```text
package=single-hart-runtime-r2
scope=non-privileged-sv39x4-backend
r2_sv39x4_backend=complete
r2_plan_acceptance=accepted
r2_plan_sha=cdcf1603b97e0ef4da3e571e43fd7045116ea1ce
r2_acceptance=accepted
r2_accepted_commit=6e1cb579257c5dbe3234bd484fd091629e87181b
r2_accepted_at=2026-07-28
r2_accepted_mechanism_match=yes
r1_acceptance=accepted
r1_accepted_commit=a6e0bb178c10a7e68c9447a8e58affb94b8ecadb
r1_accepted_at=2026-07-28
r1_accepted_mechanism_match=yes
privileged_code=no
linked_image=no
full_profile_resources=13
canonical_authorities=6
sv39x4_roots=2
sv39x4_leaves_per_root=3
sv39x4_total_leaves=6
hgatp_csr_written=no
formal_verification=no
model_0_2_refinement=no
qemu_beryllium_result=NOT-RUN
hardware_validation=NOT-RUN
r3_status_at_r2_acceptance=not-started
r3_current_status=accepted-separately-2026-07-29
r3_accepted_commit=6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
r3_review_target=6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
public_release=blocked
```

### What R2 does NOT support saying

- That R2 starts R3, boots, writes HGATP to the CSR, or runs in QEMU.
- That QEMU Beryllium or K3 hardware results exist.
- That R2 acceptance applies to any commit or itself authorized tagging,
  pushing, public release, or R3. R3's later authorization is a separate
  responsible-human decision.
- That the Sv39x4 page tables are formally verified or proved correct.
- That the Model 0.2 Rocq proof applies to the R2 page-table builder.
- That R2 required or produced changes to R1 source files.
- That the documentation byte-reproducibility limitation is resolved.

## 10. Explicit R3 boundary

R3 remains the privileged HS execution package from the runtime plan. It
depends on this accepted R2 backend, was separately authorized on 2026-07-29,
and exact implementation target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` was separately accepted on that
date. Packet follow-up is not accepted implementation. This successor status
does not expand or revise any accepted R2 claim.

R2 therefore stops before:

- writing the `hgatp` CSR;
- executing `HFENCE.GVMA` or any privileged instruction;
- booting, entering VS mode, or any trap handling;
- linking an ELF image or producing a binary;
- any assembly code;
- any Beryllium QEMU or hardware evidence;
- context switching, register saving, or fault handling; and
- modification of any R1 source file.

## Primary references

- [Bounded single-hart runtime plan](single-hart-runtime-plan.md)
- [R2 bounded plan (accepted)](single-hart-runtime-r2-plan.md)
- [R2 plan review summary](single-hart-runtime-r2-plan-review-summary.md)
- [R0 fixed profile and layout freeze](single-hart-runtime-r0-freeze.md)
- [R1 pure-C mechanism evidence](single-hart-runtime-r1-evidence.md)
- `include/be/r2.h`, `arch/riscv/be/sv39x4.c`
- `tests/r2/r2-check.c`, `tests/r2/r2-report.c`,
  `tests/r2/check-report.mjs`, `tests/r2/generate-evidence.sh`
