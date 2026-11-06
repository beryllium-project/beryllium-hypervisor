/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: non-privileged R2 Sv39x4 backend contract for the bounded
 *          single-hart Beryllium runtime. Given sealed canonical state from
 *          R1, build two concrete Sv39x4 page-table trees in host memory,
 *          produce HGATP values, and verify with an independent leaf walker.
 * Trust:   public R2 contract only. R2 runs entirely as a non-privileged host
 *          program and does not write CSRs, boot, trap, or execute in QEMU.
 * Scope:   accepted R2 non-privileged mechanism only. This header composes
 *          over const R1 state with separate one-way R2 state.
 */

#ifndef BE_R2_H
#define BE_R2_H

#include <be/state.h>

/* --- Sv39x4 architecture constants --- */

/** @BE_SV39X4_GPA_WIDTH: guest-physical address width (41 bits) */
#define BE_SV39X4_GPA_WIDTH	41U
/** @BE_SV39X4_GPA_MASK: valid GPA bit mask */
#define BE_SV39X4_GPA_MASK	((BE_U64_C(1) << BE_SV39X4_GPA_WIDTH) - 1U)

/** @BE_SV39X4_PA_WIDTH: physical address width (56 bits) */
#define BE_SV39X4_PA_WIDTH	56U
/** @BE_SV39X4_PA_MASK: valid PA bit mask */
#define BE_SV39X4_PA_MASK	((BE_U64_C(1) << BE_SV39X4_PA_WIDTH) - 1U)

/** @BE_SV39X4_PPN_WIDTH: PTE PPN field width (44 bits) */
#define BE_SV39X4_PPN_WIDTH	44U
/** @BE_SV39X4_PPN_MASK: valid PPN bit mask */
#define BE_SV39X4_PPN_MASK	((BE_U64_C(1) << BE_SV39X4_PPN_WIDTH) - 1U)

/** @BE_SV39X4_POOL_SIZE: exact 32 KiB pool size */
#define BE_SV39X4_POOL_SIZE	BE_U64_C(0x8000)

/** @BE_HGATP_MODE_SV39X4: HGATP MODE field for Sv39x4 */
#define BE_HGATP_MODE_SV39X4	(BE_U64_C(8) << 60)
/** @BE_HGATP_VMID_ZERO: HGATP VMID field fixed at zero */
#define BE_HGATP_VMID_ZERO	BE_U64_C(0)

/* --- R2 one-way state --- */

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
 * struct be_r2_pool_desc - pool memory descriptor with exact bounds
 * @base: pool physical base (must be 16 KiB aligned)
 * @buf: host-accessible byte buffer (must not be NULL)
 * @buf_size: exact buffer size in bytes (must equal BE_SV39X4_POOL_SIZE)
 */
struct be_r2_pool_desc {
	be_u64 base;
	be_u8 *buf;
	be_u64 buf_size;
};

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
 * be_r2_build - all-or-nothing top-level R2 build operation
 * @runtime: const pointer to a derived R1 runtime (read-only)
 * @pools: exactly two pool descriptors [management, protected]
 * @output: R2 output state (must be in state EMPTY on entry)
 *
 * This single public entry point (sequential single-caller assumption):
 * 1. Validates @output is non-NULL and in state EMPTY.
 * 2. Independently revalidates R1 integrity.
 * 3. Validates both pool descriptors.
 * 4. Validates the frozen fixed profile.
 * 5. For each root: builds Sv39x4 tree and walks to verify.
 * 6. Only after BOTH roots succeed: sets output state to BUILT.
 *
 * On any error: scrubs both pools, zeroes results, sets FAILED.
 * No retry API; FAILED is terminal.
 *
 * Return: BE_CHECK_OK on success; deterministic error code on failure.
 */
enum be_check_result
be_r2_build(const struct be_runtime *runtime,
	    struct be_r2_pool_desc pools[BE_MAX_ROOTS],
	    struct be_r2_output *output);

/**
 * be_r2_walk_and_check - independent read-only walk of built pools
 * @runtime: const pointer to a derived R1 runtime (read-only)
 * @pools: exactly two pool descriptors (read-only)
 * @output: R2 output that must be in state BUILT
 * @leaf_sets: output array of exactly BE_MAX_ROOTS leaf sets, zeroed at entry
 *
 * Revalidates R1 integrity and pool/root bindings. Never mutates runtime
 * state or pool contents. Exposed for testing/reporting only.
 *
 * Return: BE_CHECK_OK on exact match; deterministic error code on any
 *         discrepancy.
 */
enum be_check_result
be_r2_walk_and_check(const struct be_runtime *runtime,
		     const struct be_r2_pool_desc pools[BE_MAX_ROOTS],
		     const struct be_r2_output *output,
		     struct be_r2_leaf_set leaf_sets[BE_MAX_ROOTS]);

#endif
