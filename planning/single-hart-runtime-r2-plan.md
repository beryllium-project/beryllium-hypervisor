<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R2 bounded plan

## Status and decision required

R2 is proposed and **awaiting responsible-human review**. No implementation,
tagging, pushing, public release, or R3 start is authorized.

**Decision required:** responsible-human acceptance of this exact plan and
separate explicit authorization to begin R2 implementation. Until both are
recorded, no R2 source, test, Makefile target, or wrapper command may be added.

## Immutable prerequisites

| Prerequisite | Status | Evidence |
| --- | --- | --- |
| Accepted runtime plan | accepted 2026-07-25 | `planning/single-hart-runtime-plan.md` on branch `beryllium/single-hart-runtime-plan` |
| Accepted R0 freeze | accepted 2026-07-27 | commit `64a88b15a6c35d522fa997699c4fb514b15da314`; `planning/single-hart-runtime-r0-freeze.md` |
| Accepted R1 mechanism | accepted 2026-07-28 | commit `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb`; `planning/single-hart-runtime-r1-evidence.md` |
| R1 acceptance did NOT authorize R2 | explicit record | R1 evidence §7, runtime plan §work-packages, HANDOFF.md |
| Branch | `beryllium/single-hart-runtime-r0` | HEAD `feeb819` |

R2 depends directly on R1 sealed canonical state and R0 frozen layout. It does
not depend on R3–R7.

## Objective

R2 is the **non-privileged host-tested Sv39x4 backend**: given the sealed
canonical state produced by the accepted R1 mechanism, build two concrete
Sv39x4 page-table trees in host memory, produce HGATP values, and verify the
result with an independent leaf walker. R2 runs entirely as a non-privileged
host program and does not write CSRs, boot, trap, or execute in QEMU.

Specifically, R2 must:

1. Consume exactly the R1 `struct be_enforcement_state` (2 roots, 3 mappings
   each, 6 total mappings) through the const-derived `struct be_runtime`.
2. Independently revalidate the R1 runtime integrity (sealed, configuration
   identity match, enforcement consistency) using only the existing public R1
   checker API before R2 proceeds.
3. Resolve each abstract `frame_id` to the frozen physical address through the
   sealed canonical `struct be_canonical_state`.
4. Write Sv39x4 page-table entries into each domain's 32 KiB pool using only
   the first 6 of 8 available pages (root: 4 pages, L1: 1 page, L0: 1 page).
5. Produce one `HGATP` value per root encoding `MODE=Sv39x4`, `VMID=0`, and
   the 16 KiB-aligned PPN of the root table.
6. Provide an independent walker that enumerates every valid leaf and confirms
   exact GPA→PA mapping and rights without referencing the builder's internal
   state.
7. Enter terminal failure with both pools zeroed and both results zeroed on any
   error, with no retry API.
8. Pass exhaustive host tests under strict GCC and Clang.

## R1 preservation contract

The accepted R1 mechanism commit `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` is
checked by `tests/r1/check-acceptance.sh`, which verifies that the following
paths are unchanged from that commit:

```text
Makefile
arch/riscv/be/r0-layout.h
include/be/r0-config.h
include/be/manifest.h
include/be/r1-config.h
include/be/state.h
include/be/types.h
tests/Makefile
tests/r1/check-report.mjs
tests/r1/r1-check.c
tests/r1/r1-report.c
virt/be/manifest.c
virt/be/r1-config.c
virt/be/state.c
```

**R2 must NOT modify any of these files.** In particular:

- `include/be/state.h` and `virt/be/state.c` define the R1 phase machine and
  `struct be_runtime`. R2 does not add phases, APIs, or fields to R1 state.
- `tests/Makefile` contains R0 and R1 build targets. R2 does not alter its
  existing targets, sources, flags, or dependency lists.
- The root `Makefile` delegates to `tests/Makefile`. R2 does not alter its
  existing target semantics.

### R2 composition over R1

R2 composes over a **const, derived** `struct be_runtime` that has completed
the R1 mechanism (phase `BE_RUNTIME_PHASE_DERIVED`). R2 does not mutate or
extend the R1 runtime; it reads from R1 state through the existing public
`be_check_*` API and the struct's sealed canonical and enforcement members.

R2 owns a **separate one-way state** tracking only R2 progress:

```c
enum be_r2_state {
    BE_R2_STATE_EMPTY = 0,   /* no R2 work has been attempted */
    BE_R2_STATE_BUILT,       /* both roots built and walked successfully */
    BE_R2_STATE_FAILED,      /* terminal: R2 encountered an error */
};
```

On failure, R1 remains exact and unchanged; R2 state becomes
`BE_R2_STATE_FAILED` terminally. There is no recovery API. R3 later treats the
composite as non-runnable unless R1 is derived/sealed/integrity-valid AND R2 is
built.

### Build-graph approach

R2 uses a **self-contained `tests/r2/Makefile`** that:

- Compiles R2 sources independently from a fresh `tests/r2/` directory.
- Includes R1 source files as compile dependencies (read-only inputs) using
  the same `R1_SOURCES` and `R1_HEADERS` variable pattern as `tests/Makefile`.
- Defines only `r2-test`, `r2-report`, `r2-evidence`, and `r2-check` targets.
- Does **not** modify `tests/Makefile` targets, variables, or behavior.

**R2 does not modify the root `Makefile` or `tests/Makefile`.** R2 is
reachable only through `tests/r2/Makefile` and the `./be` wrapper commands
`r2-check` and `r2-evidence`. The required complete pre-commit validation
sequence is:

```sh
make check && ./be r2-check
```

(or the equivalent explicit order). R2 evidence production requires all of:

1. `make check` passes (R0, R1, Model 0.2, Helium gates).
2. `./be r2-check` passes (R2-specific tests, reports, evidence).
3. `tests/r1/check-acceptance.sh --require` reports
   `r1_accepted_mechanism_match=yes`.

Integrating R2 into the root `Makefile`'s `check` target would require
evolving R1 acceptance semantics (adding `tests/r2/` paths to the accepted
set under a new gate). That evolution is **not R2 scope** and requires a
separately reviewed plan. R2 does not propose, condition on, or defer that
integration; it simply does not modify the root build graph.

## Fixed inputs

### From R1 sealed canonical state

```text
2 roots × 3 mappings each = 6 total leaf mappings
```

| Root | Domain | Mapping | GPA | Frame ID | PA | Rights |
| --- | --- | --- | --- | --- | --- | --- |
| 101 | management | 1 | `0x40000000` | 9 | `0x8022e000` | RW |
| 101 | management | 2 | `0x40002000` | 11 | `0x80230000` | RW |
| 101 | management | 3 | `0x40010000` | 12 | `0x80232000` | R-X |
| 102 | protected | 1 | `0x40001000` | 10 | `0x8022f000` | RW |
| 102 | protected | 2 | `0x40002000` | 11 | `0x80230000` | R |
| 102 | protected | 3 | `0x40011000` | 13 | `0x80233000` | R-X |

### From R0 frozen layout

| Domain | Pool base (16 KiB aligned) | Pool size |
| --- | --- | --- |
| management | `0x80214000` | 32 KiB (8 pages) |
| protected | `0x8021c000` | 32 KiB (8 pages) |

### Frame-ID-to-PA resolution contract

The R2 builder resolves `frame_id` → physical address using only the sealed
canonical `frames[]` array in `struct be_canonical_state`. Lookup is a bounded
linear scan of `canonical->frame_count` entries, matching on
`frames[i].id == mapping.frame_id`. Resolution must:

- fail closed if the frame ID is absent, duplicated, or zero-sized;
- fail closed if the resolved frame size is not exactly `BE_PAGE_SIZE` (4 KiB);
- fail closed if the resolved frame class is not `BE_FRAME_PRIVATE`,
  `BE_FRAME_SHARED`, or `BE_FRAME_GUEST_CODE`;
- fail closed if the resolved frame's physical base is not page-aligned;
- fail closed if the resolved PA exceeds the 56-bit physical address width;
- never read from the pool, proposal, or any mutable storage; and
- produce exactly one `be_u64` physical page address per mapping.

## Sv39x4 architecture rules

All references are to the RISC-V Privileged Architecture specification,
ratified version 20240411. The Hypervisor extension is **Chapter 17**;
`hgatp` is §17.2.10; two-stage address translation is §17.5 and §17.5.1.
Supervisor page-table format (shared with G-stage leaf/pointer encoding) is
**Chapter 9** (§9.3.1 PTE format, §9.4 translation algorithm).

Note: R0 and R1 did not pin or reference the 20240411 specification chapter
numbers; this R2 plan is the first to do so. The 20240411 ratified version is
R2's explicit pin; it does not retroactively pin R0 or R1.

### Address geometry

| Level | Name | Index bits | Entry count | Table size |
| --- | --- | --- | --- | --- |
| 2 | root | GPA[40:30] | 2048 (Sv39x4: 11 bits, 4× base Sv39 512 entries) | 16 KiB |
| 1 | middle | GPA[29:21] | 512 | 4 KiB |
| 0 | leaf | GPA[20:12] | 512 | 4 KiB |

### GPA width and range check

Sv39x4 translates a 41-bit guest-physical address space: GPA bits [40:0].
Bits [63:41] of any GPA input must be zero; otherwise the builder rejects the
mapping.

```c
#define BE_SV39X4_GPA_WIDTH  41U
#define BE_SV39X4_GPA_MASK   ((BE_U64_C(1) << BE_SV39X4_GPA_WIDTH) - 1U)
```

### Physical address width

RISC-V Sv39x4 uses a 44-bit PPN field in PTEs, yielding a 56-bit maximum
physical address (44 PPN bits + 12 page-offset bits). Every resolved PA and
every pointer PPN must satisfy:

```c
#define BE_SV39X4_PA_WIDTH   56U
#define BE_SV39X4_PA_MASK    ((BE_U64_C(1) << BE_SV39X4_PA_WIDTH) - 1U)
#define BE_SV39X4_PPN_WIDTH  44U
#define BE_SV39X4_PPN_MASK   ((BE_U64_C(1) << BE_SV39X4_PPN_WIDTH) - 1U)
```

Any PA or PPN that exceeds these widths is rejected.

### HGATP PPN field

The `hgatp` register's PPN field is 44 bits (§17.2.10). The encoded PPN must
satisfy `(pool_base >> 12) <= BE_SV39X4_PPN_MASK`. Both fixed pool bases
(`0x80214000` and `0x8021c000`) have PPN values well within 44 bits.

### VPN extraction

```text
VPN[2] = GPA[40:30]   (11 bits, index into the 16 KiB root)
VPN[1] = GPA[29:21]   (9 bits, index into L1)
VPN[0] = GPA[20:12]   (9 bits, index into L0)
```

### PTE format (G-stage leaf, 4 KiB page)

```text
Bits [63:54]  profile-forbidden (zero in this fixed profile; Svnapot bit 63
              and Svpbmt bits 62:61 may be defined by those extensions but this
              profile requires them zero and does not claim they are universally
              reserved)
Bits [53:10]  PPN (physical page number of the mapped frame, 44 bits)
Bits [9:8]    RSW (reserved for software; must be 0 in this profile)
Bit  [7]     D (dirty; set to 1 exactly when W=1)
Bit  [6]     A (accessed; set to 1 for all valid leaves)
Bit  [5]     G (global; 0 for this fixed-VMID-zero profile)
Bit  [4]     U (user; MUST be 1 for G-stage leaves per §17.5.1)
Bits [3:1]    R, W, X (read, write, execute permissions)
Bit  [0]     V (valid; 1 for installed entries)
```

A valid **non-leaf** PTE (pointer to next level) has exactly: `V=1`,
`R=W=X=0`, PPN encoding the next-level table's 4 KiB-aligned physical page
number (within the bounded pool), all other bits zero.

A valid **leaf** PTE (4 KiB page mapping) has exactly: `V=1`, at least one of
R/W/X set, `U=1`, `A=1`, `D=1` if and only if W=1, `G=0`, `RSW=0`,
bits [63:54] zero, PPN encoding the target physical page within 44 bits.

**Profile-exact values:**
- Non-leaf: `V` + PPN only; all other bits including R/W/X/U/G/A/D/RSW/high
  must be zero.
- Leaf: `V` + `U` + `A` + {R,W,X as granted} + {D iff W} + PPN; G/RSW/high
  bits zero.

**W without R is reserved and rejected.** If W=1 then R must also be 1.

### HGATP encoding

```text
Bits [63:60]  MODE = 8 (Sv39x4)
Bits [59:58]  reserved (must be zero)
Bits [57:44]  VMID = 0 (14-bit field; fixed zero in this profile)
Bits [43:0]   PPN = root_pool_base >> 12
```

The 44-bit PPN field encodes the physical page number of the 16 KiB root table
base. Since both pool bases are 16 KiB-aligned, `pool_base >> 12` yields a
valid 4 KiB-granule PPN where the low two bits of the 4-page root are
implicitly 0b00 (i.e., the root physically occupies pages PPN+0 through PPN+3).

```c
#define BE_HGATP_MODE_SV39X4  (BE_U64_C(8) << 60)
#define BE_HGATP_VMID_ZERO    BE_U64_C(0)
```

## Pool-memory model

Each 32 KiB pool is treated as 8 consecutive 4 KiB pages at the frozen base:

| Pool page | Offset | Role | Written by R2 |
| --- | --- | --- | --- |
| 0 | `+0x0000` | Root entry [0..511] | yes (one pointer PTE at index 1) |
| 1 | `+0x1000` | Root entry [512..1023] | no (zeroed) |
| 2 | `+0x2000` | Root entry [1024..1535] | no (zeroed) |
| 3 | `+0x3000` | Root entry [1536..2047] | no (zeroed) |
| 4 | `+0x4000` | Level-1 table | yes (one pointer PTE at index 0) |
| 5 | `+0x5000` | Level-0 table (leaves) | yes (3 leaf PTEs) |
| 6 | `+0x6000` | Spare | zeroed, verified unused |
| 7 | `+0x7000` | Spare | zeroed, verified unused |

### VPN indices for the fixed mappings

All six GPAs share VPN[2]=1 and VPN[1]=0:

| GPA | VPN[2] (bits 40:30) | VPN[1] (bits 29:21) | VPN[0] (bits 20:12) |
| --- | --- | --- | --- |
| `0x40000000` | 1 | 0 | 0 |
| `0x40001000` | 1 | 0 | 1 |
| `0x40002000` | 1 | 0 | 2 |
| `0x40010000` | 1 | 0 | 16 |
| `0x40011000` | 1 | 0 | 17 |

**VPN[2]=1 selects root entry index 1, which is in pool page 0 at byte offset
8** (each PTE is 8 bytes; entry 1 is at offset 1×8=8 within the 16 KiB root).
The entire 16 KiB root spans pages 0–3; only page 0 entries 0–511 can include
index 1.

VPN[1]=0 selects L1 entry index 0.
VPN[0] selects the leaf slot within the L0 table.

### Fixed geometry constraint

All fixed mappings share VPN[2]=1 and VPN[1]=0. The R2 builder **rejects any
mapping that would require a different VPN[2] or VPN[1]**, because the fixed
32 KiB pool allocates exactly one L1 page and one L0 page. A mapping needing a
second L1 table (different VPN[2]) or a second L0 table (different VPN[1]) is
physically impossible in this pool layout.

This confirms the frozen pool sizing: one root pointer PTE (page 0, entry 1),
one L1 pointer PTE (page 4, entry 0), and exactly 3 leaf PTEs in L0 (page 5)
per root.

## Pool descriptor and memory safety

### Pool descriptor

```c
#define BE_SV39X4_POOL_SIZE  BE_U64_C(0x8000)  /* exactly 32 KiB */

/**
 * struct be_r2_pool_desc - pool memory descriptor with exact bounds
 * @base: pool physical base (must be 16 KiB aligned)
 * @buf: host-accessible byte buffer (must not be NULL)
 * @buf_size: exact buffer size in bytes (must equal BE_SV39X4_POOL_SIZE)
 */
struct be_r2_pool_desc {
    be_u64 base;
    be_u8  *buf;
    be_u64 buf_size;
};
```

### Validation requirements

The top-level R2 build operation validates both pool descriptors:

- `buf` is not NULL.
- `buf_size` equals exactly `BE_SV39X4_POOL_SIZE` (32768).
- `base` is 16 KiB aligned: `(base & 0x3FFF) == 0`.
- `base` does not exceed 56-bit PA space: `base <= BE_SV39X4_PA_MASK`.
- `base + buf_size - 1` does not exceed 56-bit PA space (last byte stays
  within the PA range): `buf_size - 1 <= BE_SV39X4_PA_MASK - base`.
- `base >> 12` fits in 44-bit PPN: `(base >> 12) <= BE_SV39X4_PPN_MASK`.
- `base + buf_size` does not overflow 64 bits.
- The two pool descriptors have distinct `base` values (no PA aliasing).
- The two pool descriptors have distinct `buf` pointers (no host-buffer
  aliasing as far as bounded C can check by comparing start pointer values;
  see trusted assumption below).

**Trusted assumption (host-buffer non-overlap):** The caller provides valid
host storage of the declared `buf_size` bytes for each pool, and the two
32 KiB regions do not partially overlap. Portable restricted C can reject
identical start pointers (`pools[0].buf != pools[1].buf`) but **cannot prove
that two arbitrary declared 32 KiB allocations do not partially overlap** —
comparing interior or end pointers across distinct allocations is undefined
behavior under the C standard. This is an explicit trusted-caller cut point.
R2 host tests use distinct `static be_u8` arrays, which the language
guarantees are non-overlapping objects. In R3+ runtime, the monitor owns the
physical extents and derives pointers from the PA identity mapping, providing a
stronger guarantee. R2 does not overclaim that the portable C check rejects
all aliasing scenarios.

### Byte-buffer access contract

The pool buffer is accessed exclusively as `be_u8` bytes. PTE values are
loaded and stored using explicit little-endian 64-bit helpers:

```c
static void pte_store_le64(be_u8 *dst, be_u64 value);
static be_u64 pte_load_le64(const be_u8 *src);
```

These decompose/recompose the 64-bit PTE into/from 8 individual bytes in
little-endian order, avoiding:

- Strict-aliasing undefined behavior (no `*(be_u64 *)buf` casts).
- Unaligned access (byte-at-a-time is always aligned).
- Host-endian dependence (explicit LE byte order regardless of host).

No heap allocation appears in R2 source or tests. All pool storage is fixed
static `be_u8` arrays in the test programs.

### Builder zeroing

The top-level operation (not the caller) zeroes both pool buffers at attempt
entry, after both descriptors have been validated as scrub-safe. On any
subsequent failure, both pool buffers and both result structures are re-zeroed
before returning. Pool contents may not remain partially usable after a failure.
If one descriptor is scrub-safe and the other is not, only the safe descriptor
is zeroed.

## Deterministic allocation

The builder uses **no allocator**. Table pages are assigned by fixed offset
from the pool base:

```c
root_base  = pool_base + 0x0000   /* pages 0-3, 16 KiB */
l1_base    = pool_base + 0x4000   /* page 4, 4 KiB */
l0_base    = pool_base + 0x5000   /* page 5, 4 KiB */
```

The builder addresses entries as byte offsets within the pool buffer:

```c
root_pte_offset = vpn2 * 8
l1_pte_offset   = 0x4000 + vpn1 * 8
l0_pte_offset   = 0x5000 + vpn0 * 8
```

## Source and API design

### R2 state and top-level operation

**`include/be/r2.h`** — R2 contract header (new file, not modifying R1):

```c
/**
 * enum be_r2_state - one-way R2 backend state
 * @BE_R2_STATE_EMPTY: no R2 work has been attempted
 * @BE_R2_STATE_BUILT: both roots built and walked successfully
 * @BE_R2_STATE_FAILED: terminal failure; no retry
 */
enum be_r2_state {
    BE_R2_STATE_EMPTY = 0,
    BE_R2_STATE_BUILT,
    BE_R2_STATE_FAILED,
};

/**
 * struct be_r2_result - output for one domain root
 * @hgatp: computed HGATP value (MODE=Sv39x4, VMID=0, PPN of pool base)
 * @leaf_count: number of valid leaf PTEs installed (3 per root)
 */
struct be_r2_result {
    be_u64 hgatp;
    be_size leaf_count;
};

/**
 * struct be_r2_output - complete R2 backend output
 * @state: current one-way R2 state (empty -> built | failed)
 * @results: per-root output (valid only when state == BUILT)
 */
struct be_r2_output {
    enum be_r2_state state;
    struct be_r2_result results[BE_MAX_ROOTS];
};

/**
 * be_r2_build - atomic top-level R2 build operation
 * @runtime: const pointer to a derived R1 runtime (read-only)
 * @pools: exactly two pool descriptors [management, protected]
 * @output: R2 output state (must be in state EMPTY on entry)
 *
 * This single public entry point:
 * 1. Validates @output is non-NULL and in state EMPTY.
 * 2. Independently revalidates R1 integrity by reconstructing the private
 *    sealed_integrity_result: runtime must be in phase DERIVED with
 *    check_result BE_CHECK_OK, sealed nonzero, validated_identity nonzero,
 *    sealed_identity nonzero, validated_identity == sealed_identity ==
 *    canonical.configuration_id == enforcement.configuration_id, plus
 *    be_configuration_identity(canonical) == canonical.configuration_id,
 *    plus both be_check_canonical and be_check_enforcement pass.
 * 3. Validates both pool descriptors (size, alignment, PA range, non-NULL,
 *    non-alias, 56-bit extent bounds).
 * 4. Validates the frozen fixed profile: exact scalar and profile-equivalence
 *    checks for every binding, count, and resource constant.
 * 5. For each of the exactly two enforcement roots (management first,
 *    protected second):
 *    a. Binds the root to its canonical domain and verifies
 *       root/domain/vCPU/root-table-frame/VMID/stack/saved-state through
 *       the existing be_check_enforcement result.
 *    b. Resolves root_table_frame to the canonical frame; requires exactly
 *       one monitor-owned BE_FRAME_ROOT_TABLE of exact 32 KiB size, exact
 *       frozen pool base, equality with the supplied pool descriptor base.
 *    c. Requires VMID == 0 and the management/protected ordering.
 *    d. Builds the Sv39x4 root into the pool (private builder).
 *    e. Independently walks and rechecks the built root (private walker).
 * 6. Only after BOTH roots succeed: atomically sets output state to BUILT
 *    and writes both results.
 *
 * On any error at any step:
 * - Scrubs both pool buffers (any whose buf is non-NULL and exact buf_size).
 * - Zeroes both results in output.
 * - Sets output state to FAILED.
 * - Returns a deterministic BE_CHECK_* error code mapped as follows:
 *   NULL pointer (output, runtime, pools, buf) → BE_CHECK_NULL
 *   Non-EMPTY output or wrong R1 phase → BE_CHECK_INVALID_PHASE
 *   Identity / sealed / walker structural mismatch → BE_CHECK_INTEGRITY
 *   Domain / root / pool binding mismatch → BE_CHECK_BINDING
 *   Wrong counts (roots, mappings, resources) → BE_CHECK_INCOMPLETE
 *   Unsupported value (alignment, PA width, rights, geometry) → BE_CHECK_UNSUPPORTED
 *   Duplicate PA / host-buffer / GPA → BE_CHECK_DUPLICATE_RESOURCE
 *   Overlapping PA extents → BE_CHECK_OVERLAPPING_RESOURCE
 *   Absent frame ID → BE_CHECK_UNDECLARED_MAPPING
 *   Zero rights → BE_CHECK_EXCESS_RIGHTS
 *   (Since manifest.h cannot change, no new enum values are added.
 *    If a future R2 rejection cannot map coherently, a separate R2
 *    enum in a new header is defined instead.)
 * - No retry API exists; FAILED is terminal.
 *
 * Return: BE_CHECK_OK on success; deterministic error code on failure.
 */
enum be_check_result
be_r2_build(const struct be_runtime *runtime,
            struct be_r2_pool_desc pools[BE_MAX_ROOTS],
            struct be_r2_output *output);
```

Low-level per-root builder and walker helpers are **private** (file-static in
the implementation). The only public API beyond the walker is a narrow
read-only checker for testing/reporting:

```c
/**
 * struct be_r2_leaf - one enumerated leaf from the walker
 * @gpa: reconstructed guest-physical address
 * @pa: physical address from leaf PTE PPN field
 * @rights: extracted R/W/X permission bits
 */
struct be_r2_leaf {
    be_u64 gpa;
    be_u64 pa;
    be_u32 rights;
};

/**
 * struct be_r2_leaf_set - bounded fixed-capacity leaf enumeration
 * @count: number of valid entries (always <= BE_MAX_MAPPINGS)
 * @leaves: fixed array zeroed before work; only [0..count-1] are valid
 *
 * The fixed struct avoids unchecked caller leaf arrays. The walker zeroes the
 * entire struct before work and writes only within the bounded array.
 */
struct be_r2_leaf_set {
    be_size count;
    struct be_r2_leaf leaves[BE_MAX_MAPPINGS];
};

/**
 * be_r2_walk_and_check - independent read-only walk of a built pool
 * @runtime: const pointer to a derived R1 runtime (read-only)
 * @pools: exactly two pool descriptors (read-only)
 * @output: R2 output that must be in state BUILT
 * @leaf_sets: output array of exactly BE_MAX_ROOTS leaf sets, zeroed at entry
 *
 * Requires enough context to establish successful R2 output: a const derived
 * runtime, two valid pools, and a BUILT output. Revalidates R1 integrity
 * and pool/root bindings. Never mutates runtime state or pool contents.
 *
 * This is exposed for testing/reporting only. The top-level be_r2_build
 * already calls the internal walker; this allows independent re-walk of
 * successfully built pools without re-executing the builder.
 *
 * Return: BE_CHECK_OK on exact match; deterministic error code on any
 *         discrepancy.
 */
enum be_check_result
be_r2_walk_and_check(const struct be_runtime *runtime,
                     const struct be_r2_pool_desc pools[BE_MAX_ROOTS],
                     const struct be_r2_output *output,
                     struct be_r2_leaf_set leaf_sets[BE_MAX_ROOTS]);
```

### Implementation file

**`arch/riscv/be/sv39x4.c`** — Sv39x4 builder and walker implementation:

Sv39x4 is RISC-V architecture-specific pure C. Although R2 performs no
privileged instruction, it implements a RISC-V G-stage page-table format and
produces RISC-V HGATP values. Per the accepted source boundary, it belongs
under `arch/riscv/be/`. A private freestanding contract header
`include/be/r2.h` provides the public API.

File-static internal helpers (not exposed in the header):
- `pte_store_le64` / `pte_load_le64`: byte-buffer LE access.
- `resolve_frame_pa`: bounded linear scan with class/size/PA validation.
- `encode_leaf_pte`: leaf PTE construction with all invariant checks.
- `encode_pointer_pte`: non-leaf PTE for L2→L1 and L1→L0 links.
- `extract_vpn`: GPA to VPN[2]/VPN[1]/VPN[0] decomposition.
- `build_one_root`: per-root builder (consumes zeroed pool, writes PTEs).
- `walk_one_root`: per-root walker with safe pointer validation.

### Pool-to-root binding

For each enforcement root, the top-level operation performs the following
binding verification:

1. Locate the root's canonical domain in `canonical->domains[]`.
2. Verify root/domain/vCPU/root ID/root-table-frame/VMID/stack/saved-state
   binding through the existing full `be_check_enforcement` (called once for
   the complete enforcement state).
3. Resolve `root_table_frame` through `canonical->frames[]`; require:
   - Exactly one frame with that ID exists.
   - Frame class is `BE_FRAME_ROOT_TABLE`.
   - Frame owner is monitor (`BE_OWNER_MONITOR`).
   - Frame size is exactly `BE_SV39X4_POOL_SIZE` (32 KiB).
   - Frame base matches the frozen pool base.
   - Frame base equals the supplied pool descriptor's `base`.
4. Require exactly two roots total.
5. Require exactly three mappings per root.
6. Require distinct pool frame IDs, distinct pool base addresses, and distinct
   host buffers between the two roots.
7. Require VMID zero for both roots.
8. Require the management/protected domain ordering already guaranteed by R1
   derivation.

### Mapped frame resolution

For each mapping within a root, frame resolution performs:

1. Linear scan of `canonical->frames[]` for `frame_id`.
2. Reject absent ID (not found after full scan).
3. Reject duplicate ID (found more than once — should not happen in valid
   canonical state but fail-closed).
4. Reject wrong frame class: only `BE_FRAME_PRIVATE`, `BE_FRAME_SHARED`, or
   `BE_FRAME_GUEST_CODE` are valid mapping targets.
5. Reject non-4 KiB size: mapped frames must be exactly one page.
6. Reject misalignment: `(frame.base & (BE_PAGE_SIZE - 1)) != 0`.
7. Reject PA exceeding 56-bit width: `frame.base > BE_SV39X4_PA_MASK`.
8. Reject last byte exceeding PA space:
   `frame.size - 1 > BE_SV39X4_PA_MASK - frame.base`
   (boundary-crossing check distinct from 64-bit overflow).
9. Reject PA overflow: `frame.base + frame.size` wraps 64 bits.
10. Reject PPN out of range: `(frame.base >> 12) > BE_SV39X4_PPN_MASK`.
11. The canonical/enforcement checks (called at the top level) already ensure
    monitor exclusion, shared-channel-only backing, exact rights, and duplicate
    GPA rejection. R2 does not re-implement these checks incorrectly; it relies
    on `be_check_enforcement` having passed.

## Complete top-level algorithm

The all-or-nothing publication guarantee is transaction-like: either all outputs
are written atomically at success, or all are zeroed at failure. This is a
single-caller sequential contract, not C11 concurrency atomicity; R2 assumes no
concurrent observer reads `pools` or `output` during the call.

```text
be_r2_build(runtime, pools, output):

  --- Precondition rejection (cannot mark state or scrub) ---

  1. Validate output is non-NULL.
     On failure: return BE_CHECK_NULL.
     (Cannot write output->state or zero pools; both are unreachable.)

  2. Validate output->state == BE_R2_STATE_EMPTY.
     On failure: return BE_CHECK_INVALID_PHASE.
     (Non-EMPTY output is an invalid call; R2 does not change terminal
     state from a prior attempt or interfere with an already-built output.)

  --- From here, output is valid and EMPTY; zero results immediately ---

  3. Zero output->results[0] and output->results[1].

  4. Validate runtime is non-NULL.
     On failure: set output->state = FAILED, return BE_CHECK_NULL.
     (Cannot scrub pools without knowing whether pools is valid.)

  5. Validate pools pointer is non-NULL.
     On failure: set output->state = FAILED, return BE_CHECK_NULL.
     (Cannot inspect pool descriptors if the array pointer is NULL.)

  --- Structurally inspect pool descriptors for scrub safety ---

  6. For each pool descriptor pools[i] (i = 0, 1):
     a. If pools[i].buf is non-NULL and pools[i].buf_size equals exactly
        BE_SV39X4_POOL_SIZE: mark descriptor i as scrub-safe.
     b. Otherwise: mark descriptor i as not scrub-safe.
     (This pass only determines scrub safety; full validation follows.)

  7. If either descriptor is not scrub-safe:
     - Best-effort scrub each descriptor marked scrub-safe.
     - Set output->state = FAILED.
     - Return the appropriate error (BE_CHECK_NULL for NULL buf,
       BE_CHECK_UNSUPPORTED for wrong buf_size).
     (Never dereference a NULL buf or write beyond declared buf_size.)

  --- Both descriptors are scrub-safe; scrub both at attempt entry ---

  8. Zero pools[0].buf and pools[1].buf (BE_SV39X4_POOL_SIZE bytes each).

  --- Full validation (any failure scrubs both and sets FAILED) ---

  9. Revalidate R1 integrity — reconstruct sealed_integrity_result:
     a. runtime->phase must be BE_RUNTIME_PHASE_DERIVED.
     b. runtime->check_result must be BE_CHECK_OK.
     c. runtime->sealed must be nonzero.
     d. runtime->validated_identity must be nonzero.
     e. runtime->sealed_identity must be nonzero.
     f. runtime->validated_identity must equal runtime->sealed_identity.
     g. runtime->canonical.configuration_id must equal
        runtime->sealed_identity.
     h. runtime->enforcement.configuration_id must equal
        runtime->sealed_identity.
     i. be_configuration_identity(&runtime->canonical) must equal
        runtime->canonical.configuration_id.
     j. be_check_canonical(&runtime->canonical) must return BE_CHECK_OK.
     k. be_check_enforcement(&runtime->canonical, &runtime->enforcement)
        must return BE_CHECK_OK.
     On any failure: scrub both pools, set output->state = FAILED,
     return the appropriate error (BE_CHECK_INTEGRITY for identity/sealed
     mismatch, BE_CHECK_INVALID_PHASE for wrong phase, or the checker's
     own result code).

  10. Full pool-descriptor validation:
      a. pools[0].base and pools[1].base must be 16 KiB aligned.
      b. pools[0].base and pools[1].base must be <= BE_SV39X4_PA_MASK.
      c. For each pool: buf_size - 1 <= BE_SV39X4_PA_MASK - base
         (last byte stays within 56-bit PA space).
      d. (base >> 12) must fit in 44-bit PPN for both.
      e. base + buf_size must not overflow 64 bits for both.
      f. pools[0].base != pools[1].base (distinct PA).
      g. pools[0].buf != pools[1].buf (no host-buffer start-pointer alias).
      On any failure: scrub both pools, set output->state = FAILED,
      return the appropriate error.

  11. Validate the frozen fixed profile (see §Frozen fixed-profile
      validation below).
      On any failure: scrub both pools, set output->state = FAILED, return
      the appropriate error.

  12. Require runtime->enforcement.root_count == 2.
      Verify roots[0].domain == BE_DOMAIN_MANAGEMENT,
             roots[1].domain == BE_DOMAIN_PROTECTED.
      Verify roots[0].vmid == 0 and roots[1].vmid == 0.
      Verify roots[0].mapping_count == 3 and roots[1].mapping_count == 3.
      On any failure: scrub both pools, set output->state = FAILED, return
      the appropriate error.

  13. For root_index in [0, 1]:
      a. Resolve root->root_table_frame in canonical->frames[]:
         - Must be class BE_FRAME_ROOT_TABLE.
         - Must be monitor-owned.
         - Must have size == BE_SV39X4_POOL_SIZE.
         - frame.base must equal pools[root_index].base.
      b. Call build_one_root(canonical, root, pool) → builds PTEs into buf.
      c. Call walk_one_root(pool, canonical, root) → independent recheck.
      d. If build or walk fails: goto failure path.

  14. After BOTH roots pass:
      - Compute HGATP for each: BE_HGATP_MODE_SV39X4 | (pool.base >> 12).
      - Write output->results[0] and output->results[1].
      - Set output->state = BE_R2_STATE_BUILT.
      - Return BE_CHECK_OK.

  Failure path (reached from any step 9–13):
     - Zero pools[0].buf (BE_SV39X4_POOL_SIZE bytes).
     - Zero pools[1].buf (BE_SV39X4_POOL_SIZE bytes).
     - Zero output->results[0] and output->results[1].
     - Set output->state = BE_R2_STATE_FAILED.
     - Return the deterministic error code.
```

## Frozen fixed-profile validation

R2 independently validates that the sealed canonical and derived enforcement
state match the exact frozen fixed profile. These are **rejection constraints**
that reject any input not equivalent to the accepted R0/R1 profile; the
constants are not authority sources. Table entries in the enforcement state are
still derived only from sealed authority.

The configuration identity is a deterministic reporting scalar; R2 does
**not** claim it is a security or integrity measurement.

### Scalar and profile-equivalence checks

```text
  canonical.configuration_version == BE_CONFIGURATION_VERSION (1)
  canonical.architecture == BE_ARCH_RISCV64
  canonical.profile == BE_PROFILE_FIXED_SINGLE_HART_TWO_DOMAIN
  canonical.hart_id == BE_CONFIGURATION_HART_ID (0)
  canonical.domain_count == 2
  canonical.frame_count == 13
  canonical.authority_count == 6
  canonical.saved_state_count == 2
  canonical.channel_count == 1
  enforcement.root_count == 2
```

### Exact domain binding checks

For management domain (domains[0]):
```text
  id == BE_DOMAIN_MANAGEMENT, vcpu_id == 1, root_id == 101
  root_table_frame == 3, vmid == 0, trusted_stack_frame == 5
  saved_state_id == 1, saved_state_frame == 7
```

For protected domain (domains[1]):
```text
  id == BE_DOMAIN_PROTECTED, vcpu_id == 2, root_id == 102
  root_table_frame == 4, vmid == 0, trusted_stack_frame == 6
  saved_state_id == 2, saved_state_frame == 8
```

### Exact frame checks

All 13 canonical frames are validated for ID, base, size, class, and
owner_mask against the frozen R0 layout constants. The relevant mapped and
pool frames include:

| Frame ID | Base | Size | Class | Owner |
| --- | --- | --- | --- | --- |
| 3 | `0x80214000` | `0x8000` | ROOT_TABLE | MONITOR |
| 4 | `0x8021c000` | `0x8000` | ROOT_TABLE | MONITOR |
| 9 | `0x8022e000` | `0x1000` | PRIVATE | MANAGEMENT |
| 10 | `0x8022f000` | `0x1000` | PRIVATE | PROTECTED |
| 11 | `0x80230000` | `0x1000` | SHARED | (no owner) |
| 12 | `0x80232000` | `0x1000` | GUEST_CODE | MANAGEMENT |
| 13 | `0x80233000` | `0x1000` | GUEST_CODE | PROTECTED |

All 13 frames (including monitor-code, monitor-data, stacks, saved-state)
are checked. The complete list is deterministic from `virt/be/r1-config.c`.

### Exact root and mapping checks

Enforcement roots must match:

| Root | root_id | domain | vcpu_id | vmid | root_table_frame |
| --- | --- | --- | --- | --- | --- |
| roots[0] | 101 | MANAGEMENT | 1 | 0 | 3 |
| roots[1] | 102 | PROTECTED | 2 | 0 | 4 |

Six root mappings must appear in exact order:

| Root | Index | GPA | frame_id | Rights |
| --- | --- | --- | --- | --- |
| 101 | 0 | `0x40000000` | 9 | RW |
| 101 | 1 | `0x40002000` | 11 | RW |
| 101 | 2 | `0x40010000` | 12 | R-X |
| 102 | 0 | `0x40001000` | 10 | RW |
| 102 | 1 | `0x40002000` | 11 | R |
| 102 | 2 | `0x40011000` | 13 | R-X |

### What frozen-profile validation does NOT claim

- It does not replace or duplicate `be_check_canonical` or
  `be_check_enforcement`; both public checkers must pass independently.
- The constants are rejection constraints (reject if different), not
  authority (the runtime does not derive rights from them).
- The reporting configuration identity is not security evidence, integrity
  measurement, or attestation.
- Canonical-valid but non-frozen alternatives (e.g. swapped domain order,
  different root IDs, different GPAs) are tested as negative cases if
  constructible and rejected by the frozen-profile check even if they would
  pass the generic R1 checkers.

## Mapped-frame extent bounds

For each mapping within a root, frame resolution performs:

```text
build_one_root(canonical, root, pool):

  For each mapping i in root->mappings[0..mapping_count-1]:
    a. GPA range check: (gpa & ~BE_SV39X4_GPA_MASK) == 0.
    b. GPA page alignment: (gpa & (BE_PAGE_SIZE - 1)) == 0.
    c. Frame resolution: resolve_frame_pa(canonical, mapping.frame_id)
       → pa, with class/size/alignment/PA-width checks.
    d. Rights check: nonzero, no W without R, subset of (R|W|X).
    e. Extract VPN: vpn2 = gpa[40:30], vpn1 = gpa[29:21], vpn0 = gpa[20:12].
    f. Fixed geometry check: vpn2 must equal 1; vpn1 must equal 0.
       Reject any mapping that would need another L1 or L0 page.
    g. Install root pointer PTE at buf[vpn2 * 8] if not already present:
       - Expected pointer PPN = (pool.base + 0x4000) >> 12.
       - Verify expected PPN fits in 44 bits.
       - If slot is zero: write pointer PTE (V=1, RWX=0, PPN only).
       - If slot already holds the exact expected pointer PTE: continue.
       - If slot holds a different nonzero value: fail (conflict).
    h. Install L1 pointer PTE at buf[0x4000 + vpn1 * 8] if not already present:
       - Expected pointer PPN = (pool.base + 0x5000) >> 12.
       - Verify expected PPN fits in 44 bits.
       - If slot is zero: write pointer PTE (V=1, RWX=0, PPN only).
       - If slot already holds the exact expected pointer PTE: continue.
       - If slot holds a different nonzero value: fail (conflict).
    i. Install leaf PTE at buf[0x5000 + vpn0 * 8]:
       - If slot is nonzero: fail (duplicate GPA mapping).
       - Verify PA PPN fits in 44 bits.
       - Encode: PPN = pa >> 12, V=1, U=1, A=1,
         R = (rights & READ) ? 1 : 0,
         W = (rights & WRITE) ? 1 : 0,
         X = (rights & EXECUTE) ? 1 : 0,
         D = (W == 1) ? 1 : 0,
         G=0, RSW=0, bits[63:54]=0.
       - Write leaf PTE via pte_store_le64.
    j. Increment installed leaf count.

  After all mappings: installed count must equal mapping_count.
  Return BE_CHECK_OK.
```

## Independent leaf walker (private, with public read-only re-walk)

```text
walk_one_root(pool, canonical, root):

  1. Read root pointer at buf[1 * 8] (VPN2=1 is the only expected root entry).
     - Decode via pte_load_le64.
     - Must be a valid pointer PTE: V=1, R=W=X=0, all other bits zero except PPN.
     - Extract PPN; verify PPN == (pool.base + 0x4000) >> 12 exactly.
       (Never turn an arbitrary PTE PPN into an unchecked host pointer.)
     - Compute L1 buffer offset: since PPN must equal the exact page-4 PA >> 12,
       index into buf at offset 0x4000.

  2. Verify ALL OTHER root entries (0, 2..2047) are zero.
     Reject any nonzero unexpected root entry.

  3. Read L1 entry at buf[0x4000 + 0 * 8] (VPN1=0 is the only expected L1 entry).
     - Must be a valid pointer PTE: V=1, R=W=X=0, other bits zero except PPN.
     - Extract PPN; verify PPN == (pool.base + 0x5000) >> 12 exactly.
     - Compute L0 buffer offset: 0x5000.

  4. Verify ALL OTHER L1 entries (1..511) are zero.
     Reject any nonzero unexpected L1 entry.

  5. Reject L2 leaves (root entries with V=1 and any R/W/X set — no huge pages).
     Reject L1 leaves (L1 entries with V=1 and any R/W/X set — no superpages).
     Reject malformed pointer encodings (V=1, R=W=X=0, but nonzero
     G/U/A/D/RSW/high bits).
     Reject nonzero PPN width beyond 44 bits.

  6. Walk L0 entries [0..511]:
     For each entry at buf[0x5000 + k * 8]:
       If entry is zero: continue (empty slot).
       If entry is a valid leaf (V=1, at least one R/W/X set):
         - Verify U=1, A=1, D=1 iff W=1, G=0, RSW=0, bits[63:54]=0.
         - Extract PPN; verify within 44-bit width.
         - Reconstruct GPA: (1 << 30) | (0 << 21) | (k << 12).
         - Compute PA: PPN << 12.
         - Extract rights: R/W/X bits.
         - Append to enumerated leaves; increment count.
       Else (nonzero but invalid — malformed non-leaf at L0 or structural error):
         Fail.

  7. Verify enumerated leaf count == root->mapping_count (must be 3).

  8. Verify spare pages (6, 7) are entirely zero:
     buf[0x6000..0x7FFF] must all be 0x00.
     Reject nonzero spare storage.

  9. For each enumerated leaf, find exact match in root->mappings:
     - GPA must equal mapping.gpa.
     - PA must equal resolve_frame_pa(canonical, mapping.frame_id).
     - Rights (R/W/X) must match mapping.rights exactly.
     If any mismatch, duplicate, unmatched canonical mapping, or extra leaf: fail.

  10. Return BE_CHECK_OK.
```

The walker reads only from `pool->buf` and the sealed canonical state. It
shares no mutable state, index, or intermediate variable with the builder. It
never converts an arbitrary PPN from a PTE into a host pointer — it only
indexes into the bounded buffer after verifying that the PPN matches the exact
known page-4 or page-5 physical address.

## Terminal failure semantics

- **No partial publication.** Results (HGATP values and leaf counts) are
  written only after BOTH roots succeed. On any error after output is
  established as valid and EMPTY, both results are zeroed. The all-or-nothing
  guarantee is transaction-like (single-caller sequential contract), not C11
  concurrency atomicity; R2 assumes no concurrent observer reads `pools` or
  `output` during the call.
- **NULL output returns early.** If `output` is NULL, R2 returns
  `BE_CHECK_NULL` immediately. It cannot mark state or scrub pools because the
  output pointer is unreachable.
- **Non-EMPTY output returns early.** If `output->state` is not
  `BE_R2_STATE_EMPTY`, R2 returns `BE_CHECK_INVALID_PHASE` without changing
  the terminal state or touching pools. This distinguishes a precondition
  rejection from an accepted R2 attempt.
- **Both pools scrubbed on failure.** Once both pool descriptors are validated
  as scrub-safe (non-NULL buf, exact buf_size), they are zeroed at attempt
  entry. On any subsequent failure, both are re-zeroed so no partial PTE
  content remains observable.
- **One-valid/one-invalid descriptor.** If exactly one descriptor has valid
  buf/buf_size, R2 scrubs the valid one and sets FAILED. It never dereferences
  a NULL buf or writes beyond a declared buf_size.
- **R2 state is terminal.** `BE_R2_STATE_FAILED` is permanent. No retry,
  reset, or re-entry API exists.
- **R1 is unchanged.** The R1 `struct be_runtime` is accessed through a const
  pointer. R2 failure does not alter R1 phase, sealed state, or enforcement
  state. R1 remains valid and at phase `DERIVED`.
- **Composite failure for R3.** A later R3 package treats the composite as
  non-runnable unless: (a) R1 is in phase `DERIVED`, sealed, and passes
  integrity checks, AND (b) R2 output state is `BE_R2_STATE_BUILT`. A failed
  R2 terminates the runtime without entering R3.
- **No R1 phase change.** R2 does not set or read any R1 phase beyond verifying
  `runtime->phase == BE_RUNTIME_PHASE_DERIVED`. The R1 phase machine has no
  `built` state; that concept is modeled entirely in the separate R2 state.

## R2 output contract

R2 produces the following determinate outputs (available after successful
`BE_R2_STATE_BUILT`):

| Output | Type | Meaning |
| --- | --- | --- |
| `output.results[0].hgatp` | `be_u64` | HGATP for management root |
| `output.results[1].hgatp` | `be_u64` | HGATP for protected root |
| `output.results[0].leaf_count` | `be_size` | 3 (management) |
| `output.results[1].leaf_count` | `be_size` | 3 (protected) |
| Both pools populated | host buffers | Ready for CSR write at R3 |

R2 does **not** write `hgatp`, execute `HFENCE.GVMA`, or enter VS mode.

## Bounded implementation packages

R2 is a single bounded package with internal ordering:

| Step | Deliverable | Depends on |
| --- | --- | --- |
| R2.1 | `include/be/r2.h` header | R1 public API (read-only) |
| R2.2 | `arch/riscv/be/sv39x4.c` builder + walker + top-level operation | R2.1 |
| R2.3 | `tests/r2/r2-check.c` — complete host test suite | R2.1–R2.2 |
| R2.4 | `tests/r2/r2-report.c` — deterministic JSON report | R2.3 |
| R2.5 | `tests/r2/check-report.mjs` — report semantic checker | R2.4 |
| R2.6 | `tests/r2/generate-evidence.sh` — retained evidence | R2.3–R2.5 |
| R2.7 | `tests/r2/Makefile` targets: `r2-test`, `r2-report`, `r2-evidence`, `r2-check` | R2.3–R2.6 |
| R2.8 | `./be r2-check` and `./be r2-evidence` wrapper integration | R2.7 |
| R2.9 | `planning/single-hart-runtime-r2-evidence.md` | R2.3–R2.8 |

**No root `Makefile` or `tests/Makefile` deliverable.** R2 does not modify
the root build graph. Later root-graph integration requires a separately
reviewed evolution of R1 acceptance semantics and is not R2.

All steps are non-privileged host code. No image, assembly, linker script,
QEMU execution, or R3 material may appear in R2.

## Deterministic error mapping

Since `include/be/manifest.h` is an R1-accepted file and **cannot be
modified** by R2, every R2 rejection is mapped coherently onto the existing
`enum be_check_result` values. If a future R2 rejection cannot map coherently
onto an existing value, a separate R2 error enum is defined in a new header
(`include/be/r2.h`); the test expectations must be updated accordingly.

| R2 rejection class | BE_CHECK_* mapping | Examples |
| --- | --- | --- |
| NULL pointer | `BE_CHECK_NULL` | NULL output, runtime, pools, pool buf |
| Wrong phase / wrong R2 state | `BE_CHECK_INVALID_PHASE` | Non-EMPTY output, non-DERIVED runtime |
| Identity / sealed / structural mismatch | `BE_CHECK_INTEGRITY` | sealed==0, identity mismatch, walker structural/content mismatch |
| Domain / root / pool binding mismatch | `BE_CHECK_BINDING` | Swapped pools, wrong root-table-frame base, frozen-profile domain/root binding |
| Wrong counts | `BE_CHECK_INCOMPLETE` | root_count!=2, mapping_count!=3, resource_count mismatch |
| Unsupported value | `BE_CHECK_UNSUPPORTED` | Alignment, PA width, geometry, W-without-R, huge pages, wrong frame class/size, boundary crossing |
| Duplicate PA / host-buffer / GPA | `BE_CHECK_DUPLICATE_RESOURCE` | Same pool base, same buf pointer, duplicate GPA |
| Overlapping PA extents | `BE_CHECK_OVERLAPPING_RESOURCE` | Physical alias between frames |
| Absent frame ID | `BE_CHECK_UNDECLARED_MAPPING` | Frame ID not found in canonical frames |
| Zero rights | `BE_CHECK_EXCESS_RIGHTS` | Mapping with no R/W/X bits |

## Exhaustive test matrix

### Positive tests

| ID | Test | Verifies |
| --- | --- | --- |
| P1 | Build both roots; walker confirms 3 leaves each with exact GPA/PA/rights | End-to-end builder+walker correctness |
| P2 | Management root HGATP == `(8<<60) \| (0x80214000>>12)` exactly | HGATP encoding for management pool |
| P3 | Protected root HGATP == `(8<<60) \| (0x8021c000>>12)` exactly | HGATP encoding for protected pool |
| P4 | Walker leaf count == 3 for each root | Complete enumeration |
| P5 | Full end-to-end: R1 seal+derive → R2 build → output state BUILT | Top-level state transition |
| P6 | GCC and Clang produce byte-identical reports | Compiler independence |
| P7 | Builder installs exactly 1 root pointer, 1 L1 pointer, and 3 leaf PTEs per pool | Pool-page usage |
| P8 | All root entries except index 1 are zero | Unused root verification |
| P9 | All L1 entries except index 0 are zero | Unused L1 verification |
| P10 | Spare pages (6, 7) are entirely zero | Spare-page cleanliness |
| P11 | Independent re-walk via be_r2_walk_and_check matches builder output | Public walker consistency (requires BUILT output, const runtime, two pools, two leaf sets) |
| P12 | R1 acceptance check passes with R2 files present | `r1_accepted_mechanism_match=yes` |

### Adversarial/negative tests — R1 integrity

| ID | Test | Expected result |
| --- | --- | --- |
| N1 | NULL runtime pointer | `BE_CHECK_NULL`, output FAILED |
| N2 | Runtime in wrong phase (SEALED, not DERIVED) | `BE_CHECK_INVALID_PHASE`, output FAILED |
| N3 | Runtime in wrong phase (EMPTY) | `BE_CHECK_INVALID_PHASE`, output FAILED |
| N4 | Runtime with canonical identity mismatch (configuration_id mutated) | `BE_CHECK_INTEGRITY`, output FAILED |
| N5 | Runtime with enforcement configuration_id mismatch | `BE_CHECK_INTEGRITY`, output FAILED |
| N6 | Runtime not sealed (sealed == 0) | `BE_CHECK_INTEGRITY`, output FAILED |
| N7 | Output not in state EMPTY (already BUILT) | `BE_CHECK_INVALID_PHASE` (no state/pool change) |
| N8 | Output not in state EMPTY (already FAILED) | `BE_CHECK_INVALID_PHASE` (no state/pool change) |
| N8a | NULL output pointer | `BE_CHECK_NULL` (no state/pool change possible) |
| N8b | Runtime with validated_identity zeroed | `BE_CHECK_INTEGRITY`, output FAILED |
| N8c | Runtime with sealed_identity zeroed | `BE_CHECK_INTEGRITY`, output FAILED |
| N8d | Runtime with validated_identity != sealed_identity | `BE_CHECK_INTEGRITY`, output FAILED |
| N8e | Runtime with sealed_identity != canonical.configuration_id | `BE_CHECK_INTEGRITY`, output FAILED |
| N8f | Runtime with be_configuration_identity(canonical) != configuration_id | `BE_CHECK_INTEGRITY`, output FAILED |
| N8g | Runtime with check_result != BE_CHECK_OK (e.g. INCOMPLETE) | `BE_CHECK_INTEGRITY`, output FAILED |

### Adversarial/negative tests — pool descriptors

| ID | Test | Expected result |
| --- | --- | --- |
| N9 | NULL pool buf (one or both) | `BE_CHECK_NULL`, scrub any scrub-safe descriptor, output FAILED |
| N9a | NULL pools pointer (array itself is NULL) | `BE_CHECK_NULL`, output FAILED |
| N10 | Pool base not 16 KiB aligned | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, output FAILED |
| N11 | Pool buf_size != 32768 (undersized) | `BE_CHECK_UNSUPPORTED`, scrub any scrub-safe descriptor, output FAILED |
| N12 | Pool buf_size != 32768 (oversized) | `BE_CHECK_UNSUPPORTED`, scrub any scrub-safe descriptor, output FAILED |
| N13 | Duplicate pool base (both pools same PA) | `BE_CHECK_DUPLICATE_RESOURCE`, both pools scrubbed, output FAILED |
| N14 | Host-buffer start-pointer alias (both pools same buf) | `BE_CHECK_DUPLICATE_RESOURCE`, both pools scrubbed, output FAILED |
| N15 | Pool base PPN exceeds 44 bits | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, output FAILED |
| N16 | Pool base + size overflows 64 bits | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, output FAILED |
| N16a | Pool base exceeds 56-bit PA space | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, output FAILED |
| N16b | Pool last byte exceeds 56-bit PA space (boundary crossing, not 64-bit wrap) | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, output FAILED |
| N16c | One valid descriptor, one invalid (NULL buf): valid one scrubbed | `BE_CHECK_NULL`, scrub-safe descriptor zeroed, output FAILED |
| N16d | Early runtime failure after valid pools established: both pools scrubbed | Error code, both pools zeroed, output FAILED |

### Adversarial/negative tests — root and mapping

| ID | Test | Expected result |
| --- | --- | --- |
| N17 | Enforcement with root_count != 2 | `BE_CHECK_INCOMPLETE`, both pools scrubbed, output FAILED |
| N18 | Root with mapping_count != 3 | `BE_CHECK_INCOMPLETE`, both pools scrubbed, output FAILED |
| N19 | Frame ID absent from canonical frames | `BE_CHECK_UNDECLARED_MAPPING`, both pools scrubbed, FAILED |
| N20 | Frame with non-4 KiB size | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N21 | Frame with wrong class (e.g. ROOT_TABLE as a leaf target) | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N22 | Frame PA not page-aligned | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N23 | Frame PA exceeds 56-bit width | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N23a | Frame last byte exceeds 56-bit PA space (boundary crossing, not 64-bit wrap) | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N24 | Mapping GPA with bits [63:41] nonzero | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N25 | Mapping GPA not page-aligned | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N26 | Mapping rights == 0 | `BE_CHECK_EXCESS_RIGHTS`, both pools scrubbed, FAILED |
| N27 | Mapping rights W without R | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N28 | Mapping with VPN2 != 1 (would need another L1 page) | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N29 | Mapping with VPN1 != 0 (would need another L0 page) | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N30 | Duplicate GPA in one root | `BE_CHECK_DUPLICATE_RESOURCE`, both pools scrubbed, FAILED |
| N31 | Swapped pools (management pool for protected root) | `BE_CHECK_BINDING` (pool base != frame base), FAILED |
| N32 | Wrong pool (same pool descriptor for both roots) | `BE_CHECK_DUPLICATE_RESOURCE`, FAILED |
| N32a | Physical alias: two mapped frames with overlapping PA extents | `BE_CHECK_OVERLAPPING_RESOURCE`, both pools scrubbed, FAILED |

### Adversarial/negative tests — walker structural

| ID | Test | Expected result |
| --- | --- | --- |
| N33 | Pool with corrupted root pointer PPN (not equal to page-4 PA) | `BE_CHECK_INTEGRITY`, both pools scrubbed, FAILED |
| N34 | Pool with out-of-pool L1 pointer PPN | `BE_CHECK_INTEGRITY`, both pools scrubbed, FAILED |
| N35 | Pool with L2 leaf (root entry with V=1 and R/W/X set) | `BE_CHECK_UNSUPPORTED` (no huge pages), both pools scrubbed, FAILED |
| N36 | Pool with L1 leaf (L1 entry with V=1 and R/W/X set) | `BE_CHECK_UNSUPPORTED` (no superpages), both pools scrubbed, FAILED |
| N37 | Pool with unexpected extra leaf in L0 | `BE_CHECK_INTEGRITY` (walker/canonical mismatch), both pools scrubbed, FAILED |
| N38 | Pool with missing leaf (entry zeroed after build) | `BE_CHECK_INTEGRITY` (walker/canonical mismatch), both pools scrubbed, FAILED |
| N39 | Leaf with wrong PA (PPN modified) | `BE_CHECK_INTEGRITY` (walker/canonical mismatch), both pools scrubbed, FAILED |
| N40 | Leaf with wrong rights | `BE_CHECK_INTEGRITY` (walker/canonical mismatch), both pools scrubbed, FAILED |
| N41 | Leaf with U=0 | `BE_CHECK_INTEGRITY` (structural), both pools scrubbed, FAILED |
| N42 | Leaf with A=0 | `BE_CHECK_INTEGRITY` (structural), both pools scrubbed, FAILED |
| N43 | Writable leaf with D=0 | `BE_CHECK_INTEGRITY` (structural), both pools scrubbed, FAILED |
| N44 | Leaf with bits [63:54] nonzero | `BE_CHECK_INTEGRITY` (structural), both pools scrubbed, FAILED |
| N45 | Leaf with G=1 | `BE_CHECK_INTEGRITY` (structural), both pools scrubbed, FAILED |
| N46 | Leaf with RSW nonzero | `BE_CHECK_INTEGRITY` (structural), both pools scrubbed, FAILED |
| N47 | Nonzero root entry at index != 1 | `BE_CHECK_INTEGRITY`, both pools scrubbed, FAILED |
| N48 | Nonzero L1 entry at index != 0 | `BE_CHECK_INTEGRITY`, both pools scrubbed, FAILED |
| N49 | Nonzero spare page content (page 6 or 7) | `BE_CHECK_INTEGRITY`, both pools scrubbed, FAILED |
| N50 | Malformed pointer PTE (V=1, RWX=0 but U/A/D/G/RSW nonzero) | `BE_CHECK_INTEGRITY` (structural), both pools scrubbed, FAILED |
| N51 | Pointer PTE PPN exceeds 44 bits | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |

### Adversarial/negative tests — failure isolation

| ID | Test | Expected result |
| --- | --- | --- |
| N52 | First root build fails → verify BOTH pools zeroed and BOTH results zeroed | Failure zeroing covers second pool even if never built |
| N53 | Second root build fails → verify BOTH pools zeroed | Failure zeroing re-zeroes first pool |
| N54 | Walker fails on second root → verify both pools/results zeroed | Late failure is still total |
| N55 | After failure, output state is FAILED and no retry is possible | Terminal state verified |
| N56 | After failure, R1 runtime phase remains DERIVED and unchanged | R1 isolation |

### Adversarial/negative tests — frozen-profile divergence

| ID | Test | Expected result |
| --- | --- | --- |
| N57 | Canonical-valid but non-frozen root IDs (e.g. 201/202 instead of 101/102) | `BE_CHECK_BINDING`, both pools scrubbed, FAILED |
| N58 | Canonical-valid but non-frozen domain ordering (protected first) | `BE_CHECK_BINDING`, both pools scrubbed, FAILED |
| N59 | Canonical-valid but non-frozen mapping GPA (different frozen-valid address) | `BE_CHECK_BINDING`, both pools scrubbed, FAILED |
| N60 | Non-frozen configuration_version | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N61 | Non-frozen architecture value | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N62 | Non-frozen profile value | `BE_CHECK_UNSUPPORTED`, both pools scrubbed, FAILED |
| N63 | Frame ID physically aliasing another frame's PA range | `BE_CHECK_OVERLAPPING_RESOURCE`, both pools scrubbed, FAILED |
| N64 | Canonical-valid alternative with 4 mappings per root (exceeds frozen 3) | `BE_CHECK_INCOMPLETE`, both pools scrubbed, FAILED |

R2 preserves exactly 2 roots × 3 leaves = 6 total leaf mappings. R3, QEMU,
and hardware validation are explicitly NOT RUN and not claimed.

## GCC/Clang/restricted-C/report/evidence gates

The following commands are proposed future targets. They are **NOT AVAILABLE**
until implementation is complete:

```sh
# Self-contained R2 Makefile targets (proposed)
make -C tests/r2 r2-test        # GCC+Clang strict host tests
make -C tests/r2 r2-report      # Deterministic JSON report
make -C tests/r2 r2-evidence    # Retained evidence bundle
make -C tests/r2 r2-check       # r2-test + r2-report + r2-evidence

# Stable wrapper (proposed)
./be r2-check                   # Delegates to make -C tests/r2 r2-check
./be r2-evidence                # Delegates to make -C tests/r2 r2-evidence

# Required complete pre-commit validation (proposed)
make check && ./be r2-check     # R0+R1+Model+Helium then R2
```

Requirements for the gate:

- Warning-clean GCC and Clang with existing strict flags.
- Byte-identical deterministic JSON reports between GCC and Clang builds.
- Report semantic validation via `check-report.mjs`.
- Retained evidence: `source.sha256`, `artifacts.sha256`,
  `tool-versions.txt`, `source-state.txt`, `claim-status.txt`.
- `tests/r1/check-acceptance.sh --require` must report
  `r1_accepted_mechanism_match=yes` (R1 mechanism unchanged).
- Complete pre-commit validation: `make check && ./be r2-check` must both
  pass. R2 evidence requires both results plus the R1 acceptance check.
- All existing R0, R1, Model 0.2, and Helium gates must continue to pass.
- No regressions in any prior check.
- QEMU Beryllium result: `NOT RUN`. Hardware validation: `NOT RUN`.

## Evidence model

### Pre-acceptance R2 evidence

R2 implementation evidence is producible while `r2_acceptance=review-required`.
The evidence script (`tests/r2/generate-evidence.sh`) records:

- Source hashes, tool versions, and report outputs.
- Test pass/fail status under GCC and Clang.
- R1 acceptance status (`r1_accepted_mechanism_match=yes` required).
- `r2_acceptance=review-required` (no accepted commit yet).
- `r2_accepted_commit=none`.

This allows the responsible human to review implementation evidence before
deciding whether to accept the R2 commit. Pre-review evidence does not require
a nonexistent accepted commit.

### Post-acceptance R2 evidence

If a responsible-human exact-commit decision later pins acceptance:

- `r2_acceptance=accepted`
- `r2_accepted_commit=<exact commit hash>`
- `r2_accepted_at=<date>`
- A check script (similar to `tests/r1/check-acceptance.sh`) verifies the
  R2-specific source paths against the accepted commit.

This two-stage model matches R1's pattern. Implementation is reviewable first;
exact-commit acceptance is a separate human decision.

### Retained claim-status fields (proposed)

```text
r2_sv39x4_backend=complete
r2_acceptance=review-required
r2_accepted_commit=none
r1_accepted_mechanism_match=yes
privileged_code=no
linked_image=no
sv39x4_roots=2
sv39x4_leaves_per_root=3
sv39x4_total_leaves=6
hgatp_csr_written=no
qemu_beryllium_result=NOT-RUN
hardware_validation=NOT-RUN
r3_status=not-started
public_release=blocked
```

## Documentation, evidence, and claim ledger

### What R2 will support saying

- R2 implementation is complete locally and `make check && ./be r2-check`
  passes: all R0/R1/Model/Helium gates pass, plus R2-specific strict
  GCC and Clang host builds, adversarial builder/walker/state tests,
  byte-identical deterministic reports, report semantic checking, and
  retained source/artifact evidence.
- R2 builds two Sv39x4 page-table trees from sealed canonical authority and
  produces HGATP values for the fixed profile: 2 roots × 3 leaves each =
  6 total mappings at 4 KiB granularity.
- An independent walker confirms every leaf matches canonical authority
  exactly with no unexpected or missing entries, no nonzero unused storage,
  and all pointer PPNs verified against exact known pool addresses.
- R2 remains non-privileged: no CSR write, no QEMU execution, no image, no
  boot, no trap.
- R2 is not formally verified, not a Model 0.2 refinement, not hardware
  validated, and not a production hypervisor.
- R1 accepted mechanism is unchanged: `r1_accepted_mechanism_match=yes`.

### What R2 will NOT support saying

- That R2 starts R3, boots, writes HGATP to the CSR, or runs in QEMU.
- That QEMU Beryllium or K3 hardware results exist.
- That acceptance transfers claims or authorizes tagging, pushing, public
  release, or R3.
- That the Sv39x4 page tables are proved correct (they are host-tested only).
- That Model 0.2 Rocq proof applies to the R2 page-table builder.
- That R2 required or produced changes to R1 source files.

### Planned evidence record

`planning/single-hart-runtime-r2-evidence.md` will record:

- Component tour and API summary.
- Exact fixed inputs and outputs.
- Test coverage and passing output.
- Deterministic report structure.
- Claim/assumption/cut-point ledger.
- Retained evidence identities.
- Explicit R3 boundary.

## Trusted assumptions

| Assumption | Scope | Mitigation |
| --- | --- | --- |
| Host buffer of declared buf_size represents physical memory faithfully | R2 host test only | R3 uses actual pool PA; walker re-runs on real memory |
| Pool buffer declared buf_size is actually allocated | Caller/platform contract (cut point) | R2 tests use fixed static arrays; R3 monitor owns physical extent |
| Two declared pool host-buffers do not partially overlap | Caller/platform contract (cut point) | Portable restricted C rejects identical start pointers but cannot prove arbitrary 32 KiB allocations do not partially overlap; R2 tests use distinct static arrays; R3 derives pointers from non-overlapping physical extents |
| Sealed canonical state is intact | R1 guarantee + R2 independent revalidation | Full sealed_integrity_result reconstruction at R2 entry |
| No concurrent observer reads pools/output during call | Single-caller sequential contract | Transaction-like semantics, not C11 atomicity |
| GCC/Clang encode byte-buffer LE operations correctly | Compiler trust | Two-compiler byte-identical check; no strict-aliasing UB |
| Sv39x4 format matches ratified specification | Specification trust | R4+ QEMU G-stage faults validate interpretation |
| RISC-V defines no additional required PTE bits in 20240411 | Specification boundary | Bits [63:54] are profile-forbidden, not universally reserved; Svnapot/Svpbmt may define them |

## Exclusions and explicit R3+ boundary

R2 explicitly excludes and defers to later packages:

- Writing the `hgatp` CSR (R3).
- `HFENCE.GVMA` execution (R3).
- Booting, entering VS mode, or any privileged instruction (R3).
- Linking an ELF image or producing a binary (R3).
- Context switching, saving, or restoring any register (R4).
- Fault handling or trap classification (R4).
- Assembly code of any kind (R3+).
- A QEMU Beryllium run (R3+).
- K3 hardware validation (deferred indefinitely).
- Formal verification, Rocq proof, or C refinement (R7 or later).
- Runtime domain creation, destruction, or policy update (never in scope).
- Huge pages, superpages, aliases, demand paging, or runtime root edits (never).
- Page-table caches, TLB management beyond HFENCE, or ASID/VMID logic (never
  in the fixed profile).
- Modification of any R1 source file (never in R2 scope).

R3 consumes R2's `be_r2_output` and pool contents to write the actual
`hgatp` CSR and fence. R2 must not collapse R3 material into its scope.

## Review order

Recommended review sequence for the responsible human:

1. **R1 preservation** — confirm no R1 source/API/phase files are modified;
   R2 composes over const R1 state with separate one-way R2 state.
2. **Top-level API** — confirm single atomic entry point, independent R1
   revalidation, both-pools-zeroed failure, terminal state.
3. **Pool memory safety** — confirm exact buf_size, LE byte-buffer access,
   builder zeroing, no strict-aliasing UB, no heap.
4. **Pool-to-root binding** — confirm root_table_frame resolution, monitor
   ownership, exact size/base match, distinct pools/buffers.
5. **Sv39x4 rules** — confirm GPA width, PA width, PTE format, HGATP encoding
   against Chapter 17 (§17.2.10, §17.5.1) and Chapter 9 (§9.3.1, §9.4).
6. **Pool layout** — confirm VPN[2]=1 is root entry 1 in page 0; fixed
   geometry; one root pointer, one L1 pointer, three leaves.
7. **Builder algorithm** — confirm fail-closed ordering, fixed-geometry
   enforcement, no partial publication, correct PTE bit construction.
8. **Walker safety** — confirm pointer PPN verified against exact known PA
   before buffer indexing; no arbitrary PPN→pointer conversion; spare-page
   and unused-entry verification.
9. **Test matrix** — confirm coverage of every failure mode including both-pool
   zeroing, terminal state, R1 isolation, and no retry.
10. **Build graph** — confirm self-contained tests/r2/Makefile, no R1 file
    modification, no root Makefile or tests/Makefile change, R1 acceptance
    preserved, composite pre-commit is `make check && ./be r2-check`.
11. **Boundaries** — confirm no R3 collapse, no privileged code, no QEMU, no
    claims beyond host testing, correct spec references.

## Acceptance, revision, and deferral outcomes

| Outcome | Effect |
| --- | --- |
| **Accept** | R2 plan is frozen. Separate explicit authorization to begin implementation is still required. |
| **Accept with revision** | Identified revisions are applied; revised plan re-enters review. |
| **Defer** | R2 is not accepted; no implementation starts; blocking questions are recorded. |

**Implementation must not start until this plan is accepted AND separate
explicit implementation authorization is recorded.** This is the same two-gate
structure used for R0 and R1.

## Primary references

- [Bounded single-hart runtime plan](single-hart-runtime-plan.md)
- [R0 fixed profile and layout freeze](single-hart-runtime-r0-freeze.md)
- [R1 pure-C mechanism evidence](single-hart-runtime-r1-evidence.md)
- `include/be/manifest.h` — R1 contract definitions (read-only input)
- `include/be/state.h` — R1 phase machine (read-only, not modified by R2)
- `arch/riscv/be/r0-layout.h` — frozen pool layout and VPN indices
- `virt/be/r1-config.c` — exact fixed mapping constants
- RISC-V Privileged Architecture, ratified 20240411, Chapter 17
  (Hypervisor Extension): §17.2.10 (`hgatp`), §17.5 and §17.5.1
  (Two-stage address translation, Sv39x4)
- RISC-V Privileged Architecture, ratified 20240411, Chapter 9
  (Supervisor-Level Address Translation): §9.3.1 (PTE format), §9.4
  (Virtual Address Translation Process)
