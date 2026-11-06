/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B7 G-stage contract: one Sv39x4 root per guest, each in its
 *          own B6-shaped 32 KiB pool, mapping one linear guest-RAM window
 *          with 2 MiB leaves through one level-1 table, under the guest's
 *          own VMID; a builder, an independent re-walker that derives the
 *          window from each pool's bytes, the check that two walked roots
 *          share no page, window, or VMID, and the guest-range translation
 *          the SBI core uses for DBCN.
 * Trust:   restricted C. No CSR, fence, or I/O: each pool is reached only
 *          through bounded little-endian byte helpers, and the runtime
 *          installs each walked hgatp through the accepted R3 function.
 * Scope:   B7 only (planning/k3-b7-plan.md, "G-stage and VMIDs"). Per root:
 *          one level-1 table, no level-0 table, no per-page rights.
 */

#ifndef BE_B7_GSTAGE_H
#define BE_B7_GSTAGE_H

#include <be/types.h>

#include "b7-layout.h"

/* Sv39x4 geometry: 2 MiB leaves in one level-1 table under a 16 KiB root. */
#define BE_B7_GSTAGE_LEAF_BYTES		BE_B7_GUEST_LEAF_BYTES
#define BE_B7_GSTAGE_GIB		(BE_U64_C(1) << 30)
#define BE_B7_GSTAGE_GPA_LIMIT		(BE_U64_C(1) << 41)
#define BE_B7_GSTAGE_PA_LIMIT		(BE_U64_C(1) << 56)
#define BE_B7_GSTAGE_POOL_BYTES		BE_B7_GUEST_POOL_BYTES
#define BE_B7_GSTAGE_POOL_ALIGN		BE_U64_C(0x4000)
#define BE_B7_GSTAGE_L1_OFFSET		BE_B7_ROOT_BYTES
#define BE_B7_GSTAGE_SPARE_OFFSET	(BE_B7_ROOT_BYTES + BE_U64_C(0x1000))
#define BE_B7_GSTAGE_ROOT_ENTRIES	2048U
#define BE_B7_GSTAGE_L1_ENTRIES		512U
#define BE_B7_GSTAGE_HGATP_SV39X4	(BE_U64_C(8) << 60)
/* hgatp.VMID: bits 44-57, 14 bits on QEMU and on K3. */
#define BE_B7_GSTAGE_VMID_SHIFT		44U
#define BE_B7_GSTAGE_VMID_LIMIT		(BE_U64_C(1) << 14)

/* G-stage PTE bits. */
#define BE_B7_PTE_V			(BE_U64_C(1) << 0)
#define BE_B7_PTE_R			(BE_U64_C(1) << 1)
#define BE_B7_PTE_W			(BE_U64_C(1) << 2)
#define BE_B7_PTE_X			(BE_U64_C(1) << 3)
#define BE_B7_PTE_U			(BE_U64_C(1) << 4)
#define BE_B7_PTE_G			(BE_U64_C(1) << 5)
#define BE_B7_PTE_A			(BE_U64_C(1) << 6)
#define BE_B7_PTE_D			(BE_U64_C(1) << 7)
#define BE_B7_PTE_PPN_SHIFT		10U
#define BE_B7_PTE_PPN_MASK		((BE_U64_C(1) << 44) - 1U)
/* Every leaf: V R W X U A D (0xdf); G, RSW, PBMT, N, and reserved bits 0. */
#define BE_B7_PTE_LEAF_FLAGS \
	(BE_B7_PTE_V | BE_B7_PTE_R | BE_B7_PTE_W | BE_B7_PTE_X | \
	 BE_B7_PTE_U | BE_B7_PTE_A | BE_B7_PTE_D)

/**
 * struct be_b7_gstage_desc - one guest-RAM window, its table pool, its VMID
 * @gpa_base: 2 MiB-aligned guest-physical base
 * @hpa_base: 2 MiB-aligned host-physical base
 * @size: nonzero multiple of 2 MiB inside one 1 GiB GPA region
 * @pool_pa: 16 KiB-aligned host-physical base of the 32 KiB pool, outside
 *           the window
 * @vmid: the guest's VMID, below 2^14
 */
struct be_b7_gstage_desc {
	be_u64 gpa_base;
	be_u64 hpa_base;
	be_u64 size;
	be_u64 pool_pa;
	be_u64 vmid;
};

/**
 * struct be_b7_gstage_map - the window as the walker derived it
 * @hgatp: Sv39x4, the VMID, and the root PPN of the walked pool
 * @gpa_base: first mapped GPA
 * @hpa_base: host-physical address of @gpa_base
 * @size: mapped bytes
 * @leaves: 2 MiB leaves found
 * @pool_pa: host-physical base of the walked pool
 * @vmid: the VMID in @hgatp
 *
 * All zero unless the walk succeeded.
 */
struct be_b7_gstage_map {
	be_u64 hgatp;
	be_u64 gpa_base;
	be_u64 hpa_base;
	be_u64 size;
	be_u64 leaves;
	be_u64 pool_pa;
	be_u64 vmid;
};

/**
 * enum be_b7_gstage_error - stable G-stage results
 * @BE_B7_GSTAGE_OK: success
 * @BE_B7_GSTAGE_NULL: a required pointer is absent
 * @BE_B7_GSTAGE_DESC: the descriptor breaks an alignment, range, or VMID
 *                     rule
 * @BE_B7_GSTAGE_POOL: wrong pool size or placement, or the window covers it
 * @BE_B7_GSTAGE_ROOT: a root entry is not the one expected pointer
 * @BE_B7_GSTAGE_L1: a level-1 entry is neither an exact leaf nor zero
 * @BE_B7_GSTAGE_SPARE: a spare pool byte is not zero
 * @BE_B7_GSTAGE_MISMATCH: the walked window differs from the descriptor
 * @BE_B7_GSTAGE_PAIR: two walked roots share a pool page, a window byte, a
 *                     VMID, or a root, or a window covers the other's pool
 */
enum be_b7_gstage_error {
	BE_B7_GSTAGE_OK = 0,
	BE_B7_GSTAGE_NULL,
	BE_B7_GSTAGE_DESC,
	BE_B7_GSTAGE_POOL,
	BE_B7_GSTAGE_ROOT,
	BE_B7_GSTAGE_L1,
	BE_B7_GSTAGE_SPARE,
	BE_B7_GSTAGE_MISMATCH,
	BE_B7_GSTAGE_PAIR,
};

/**
 * be_b7_gstage_build - scrub the pool, then write the root and leaves
 * @desc: the window
 * @pool: monitor-owned pool bytes, the memory at @desc->pool_pa
 * @pool_size: exactly %BE_B7_GSTAGE_POOL_BYTES
 *
 * The whole pool is zeroed first, also when the descriptor is refused; a
 * pool of the wrong size is never written. The builder refuses a zero or
 * misaligned size, a misaligned GPA or HPA, a 1 GiB crossing, a GPA at or
 * above 2^41, a PA at or above 2^56, a misaligned pool, a VMID at or above
 * 2^14, and a window that covers the pool.
 *
 * Return: %BE_B7_GSTAGE_OK, or the refusal with the pool scrubbed.
 */
enum be_b7_gstage_error
be_b7_gstage_build(const struct be_b7_gstage_desc *desc, be_u8 *pool,
		   be_u64 pool_size);

/**
 * be_b7_gstage_walk - parse every pool byte and derive the window
 * @desc: the window the walk must find
 * @pool: pool bytes
 * @pool_size: exactly %BE_B7_GSTAGE_POOL_BYTES
 * @map: zeroed first; filled only on success
 *
 * The walker shares only the byte loader with the builder. It accepts
 * exactly one root entry, a pointer to this pool's level-1 page; only exact
 * 2 MiB leaves forming one contiguous linear run in the level-1 page; and
 * zero in every other pool byte. It derives (gpa, hpa, size) from the bytes
 * and compares them with @desc, whose VMID it places in the hgatp.
 *
 * Return: %BE_B7_GSTAGE_OK or the first error found.
 */
enum be_b7_gstage_error
be_b7_gstage_walk(const struct be_b7_gstage_desc *desc, const be_u8 *pool,
		  be_u64 pool_size, struct be_b7_gstage_map *map);

/**
 * be_b7_gstage_pair_check - require two walked roots to be disjoint
 * @first: one walked map
 * @second: the other walked map
 *
 * Refuses two maps that are not both walked, whose pools share a byte,
 * whose host windows share a byte, where either window covers either pool,
 * whose VMIDs are equal or zero, or whose hgatp values are equal.
 *
 * Return: %BE_B7_GSTAGE_OK, %BE_B7_GSTAGE_NULL, or %BE_B7_GSTAGE_PAIR.
 */
enum be_b7_gstage_error
be_b7_gstage_pair_check(const struct be_b7_gstage_map *first,
			const struct be_b7_gstage_map *second);

/**
 * be_b7_gstage_translate - translate one guest range for an HS access
 * @map: a walked map
 * @gpa: guest-physical start
 * @length: nonzero byte count
 * @hpa: host-physical start on success, unchanged otherwise
 *
 * Return: 1 when [@gpa, @gpa + @length) lies inside the window, else 0.
 */
int be_b7_gstage_translate(const struct be_b7_gstage_map *map, be_u64 gpa,
			   be_u64 length, be_u64 *hpa);

#endif
