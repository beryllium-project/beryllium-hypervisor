// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the K3 B7 G-stage builder, re-walker, pair
 *          check, and translation: both fixed B7 windows, pools, and VMIDs
 *          against an independent byte model, other windows (128 MiB,
 *          another HPA, the last 2 MiB below a 1 GiB boundary, a full
 *          1 GiB) and VMIDs, every single-bit flip of every nonzero entry,
 *          sampled and targeted nonzero bytes in the zero regions,
 *          whole-entry moves, descriptor and VMID refusals, two roots that
 *          share a page, a window, a VMID, or a root, and translation edges.
 * Trust:   host evidence only. No CSR, fence, guest entry, QEMU, or hardware
 *          behaviour is exercised.
 * Scope:   B7 only (planning/k3-b7-plan.md, "G-stage and VMIDs").
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "b7-gstage.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_B7_GSTAGE_CHECK: assertion failed: %s:%d: %s\n", \
			       __FILE__, __LINE__, #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

#define MIB			(BE_U64_C(1) << 20)
#define GPA_G0			BE_U64_C(0x80000000)
#define HPA_G0			BE_U64_C(0x110000000)
#define POOL_G0			BE_U64_C(0x102034000)
#define HPA_G1			BE_U64_C(0x114000000)
#define POOL_G1			BE_U64_C(0x10203c000)
#define HPA_OTHER		BE_U64_C(0x104000000)
#define ALL_ONES		(~BE_U64_C(0))

static be_u8 pool[BE_B7_GSTAGE_POOL_BYTES];
static be_u8 expected[BE_B7_GSTAGE_POOL_BYTES];
static be_u8 scratch[BE_B7_GSTAGE_POOL_BYTES];

static void put_le64(be_u8 *destination, be_u64 value)
{
	unsigned int byte;

	for (byte = 0U; byte < 8U; ++byte)
		destination[byte] = (be_u8)(value >> (8U * byte));
}

static be_u64 get_le64(const be_u8 *source)
{
	be_u64 value = 0U;
	unsigned int byte;

	for (byte = 0U; byte < 8U; ++byte)
		value |= (be_u64)source[byte] << (8U * byte);
	return value;
}

/* An independent model: the expected pool from the Sv39x4 rules alone. */
static void model(const struct be_b7_gstage_desc *desc)
{
	be_u64 root_pte = 1U | (((desc->pool_pa + 0x4000U) / 4096U) << 10);
	be_u64 slot = desc->gpa_base / (BE_U64_C(1) << 30);
	be_u64 first = (desc->gpa_base % (BE_U64_C(1) << 30)) / (2U * MIB);
	be_u64 leaf;

	memset(expected, 0, sizeof(expected));
	put_le64(expected + slot * 8U, root_pte);
	for (leaf = 0U; leaf < desc->size / (2U * MIB); ++leaf) {
		be_u64 pa = desc->hpa_base + leaf * 2U * MIB;

		/* V R W X U A D = 0xdf; G, RSW, and bits 54-63 clear. */
		put_le64(expected + 0x4000U + (first + leaf) * 8U,
			 0xdfU | ((pa / 4096U) << 10));
	}
}

static void test_constants(void)
{
	SCENARIO();
	CHECK(BE_B7_GSTAGE_POOL_BYTES == 0x8000U);
	CHECK(BE_B7_GSTAGE_L1_OFFSET == 0x4000U);
	CHECK(BE_B7_GSTAGE_SPARE_OFFSET == 0x5000U);
	CHECK(BE_B7_GSTAGE_LEAF_BYTES == 2U * MIB);
	CHECK(BE_B7_GSTAGE_VMID_SHIFT == 44U);
	CHECK(BE_B7_GSTAGE_VMID_LIMIT == 0x4000U);
	CHECK(BE_B7_PTE_LEAF_FLAGS == 0xdfU);
	CHECK(BE_B7_GUESTS == 2U);
	CHECK(BE_B7_POOL_HPA == POOL_G0 && BE_B7_POOL_BYTES == 0x10000U);
	CHECK(BE_B7_GUEST_POOL_BYTES == 0x8000U);
	CHECK(BE_B7_G0_ROOT_HPA == POOL_G0 &&
	      BE_B7_G0_LEVEL1_HPA == POOL_G0 + 0x4000U);
	CHECK(BE_B7_G1_ROOT_HPA == POOL_G1 &&
	      BE_B7_G1_LEVEL1_HPA == POOL_G1 + 0x4000U);
	CHECK(POOL_G1 == POOL_G0 + 0x8000U);
	CHECK(BE_B7_G0_VMID == 1U && BE_B7_G1_VMID == 2U);
	CHECK(BE_B7_G0_HGATP == BE_U64_C(0x8000100000102034));
	CHECK(BE_B7_G1_HGATP == BE_U64_C(0x800020000010203c));
	CHECK(BE_B7_GUEST_GPA == GPA_G0);
	CHECK(BE_B7_G0_HPA == HPA_G0 && BE_B7_G1_HPA == HPA_G1);
	CHECK(BE_B7_GUEST_BYTES == 64U * MIB && BE_B7_GUEST_LEAVES == 32U);
	CHECK(sizeof(struct be_b7_gstage_desc) == 5U * sizeof(be_u64));
	CHECK(sizeof(struct be_b7_gstage_map) == 7U * sizeof(be_u64));
}

static void check_window(be_u64 gpa, be_u64 hpa, be_u64 size, be_u64 pool_pa,
			 be_u64 vmid)
{
	struct be_b7_gstage_desc desc = { gpa, hpa, size, pool_pa, vmid };
	struct be_b7_gstage_map map;
	be_u64 leaf;
	be_u64 out = 0U;

	SCENARIO();
	memset(pool, 0xa5, sizeof(pool));
	CHECK(be_b7_gstage_build(&desc, pool, sizeof(pool)) ==
	      BE_B7_GSTAGE_OK);
	model(&desc);
	CHECK(memcmp(pool, expected, sizeof(pool)) == 0);
	CHECK(be_b7_gstage_walk(&desc, pool, sizeof(pool), &map) ==
	      BE_B7_GSTAGE_OK);
	CHECK(map.hgatp == ((BE_U64_C(8) << 60) | (vmid << 44) |
			    (pool_pa >> 12)));
	CHECK(map.gpa_base == gpa && map.hpa_base == hpa && map.size == size);
	CHECK(map.leaves == size / (2U * MIB) && map.pool_pa == pool_pa);
	CHECK(map.vmid == vmid);
	for (leaf = 0U; leaf < map.leaves; ++leaf) {
		be_u64 offset = leaf * 2U * MIB + 0x123U;

		CHECK(be_b7_gstage_translate(&map, gpa + offset, 1U, &out) == 1);
		CHECK(out == hpa + offset);
		/* A whole 4 KiB page at each leaf's end, as Linux writes. */
		offset = (leaf + 1U) * 2U * MIB - 0x1000U;
		CHECK(be_b7_gstage_translate(&map, gpa + offset, 0x1000U,
					     &out) == 1);
		CHECK(out == hpa + offset);
	}
	/* Edges: first byte, last byte, whole window, one past, before. */
	CHECK(be_b7_gstage_translate(&map, gpa, 1U, &out) == 1 && out == hpa);
	CHECK(be_b7_gstage_translate(&map, gpa + size - 1U, 1U, &out) == 1 &&
	      out == hpa + size - 1U);
	CHECK(be_b7_gstage_translate(&map, gpa, size, &out) == 1 &&
	      out == hpa);
	out = 7U;
	CHECK(be_b7_gstage_translate(&map, gpa + size, 1U, &out) == 0 &&
	      out == 7U);
	CHECK(be_b7_gstage_translate(&map, gpa - 1U, 1U, &out) == 0);
	CHECK(be_b7_gstage_translate(&map, gpa - 1U, 2U, &out) == 0);
	CHECK(be_b7_gstage_translate(&map, gpa + size - 1U, 2U, &out) == 0);
	CHECK(be_b7_gstage_translate(&map, gpa, size + 1U, &out) == 0);
	CHECK(be_b7_gstage_translate(&map, gpa, 0U, &out) == 0);
	CHECK(be_b7_gstage_translate(&map, gpa + 8U, ALL_ONES, &out) == 0);
	CHECK(be_b7_gstage_translate(&map, ALL_ONES, 2U, &out) == 0);
	CHECK(be_b7_gstage_translate(&map, 0U, 1U, &out) == 0);
	CHECK(be_b7_gstage_translate(&map, hpa, 1U, &out) == 0);
	CHECK(out == 7U);
	CHECK(be_b7_gstage_translate((const struct be_b7_gstage_map *)0, gpa,
				     1U, &out) == 0);
	CHECK(be_b7_gstage_translate(&map, gpa, 1U, (be_u64 *)0) == 0);
}

/*
 * The fixed B7 windows: each pool's root slot, its leaves, and the hgatp it
 * installs, built in the layout's back-to-back pools.
 */
static void test_b7_windows(void)
{
	static const struct {
		be_u64 hpa, pool_pa, vmid, hgatp, root_pte, first_leaf;
	} guests[] = {
		{ BE_B7_G0_HPA, BE_B7_G0_ROOT_HPA, BE_B7_G0_VMID,
		  BE_B7_G0_HGATP, BE_U64_C(0x4080e001), BE_U64_C(0x440000df) },
		{ BE_B7_G1_HPA, BE_B7_G1_ROOT_HPA, BE_B7_G1_VMID,
		  BE_B7_G1_HGATP, BE_U64_C(0x40810001), BE_U64_C(0x450000df) },
	};
	static be_u8 both[BE_B7_POOL_BYTES];
	struct be_b7_gstage_map maps[2];
	be_u64 guest;
	be_u64 leaf;

	SCENARIO();
	memset(both, 0xa5, sizeof(both));
	for (guest = 0U; guest < 2U; ++guest) {
		struct be_b7_gstage_desc desc = {
			BE_B7_GUEST_GPA, guests[guest].hpa, BE_B7_GUEST_BYTES,
			guests[guest].pool_pa, guests[guest].vmid };
		be_u8 *own = both + (guests[guest].pool_pa - BE_B7_POOL_HPA);

		CHECK(be_b7_gstage_build(&desc, own, BE_B7_GUEST_POOL_BYTES) ==
		      BE_B7_GSTAGE_OK);
		CHECK(be_b7_gstage_walk(&desc, own, BE_B7_GUEST_POOL_BYTES,
					&maps[guest]) == BE_B7_GSTAGE_OK);
		CHECK(maps[guest].hgatp == guests[guest].hgatp);
		CHECK(maps[guest].vmid == guests[guest].vmid);
		CHECK(maps[guest].leaves == BE_B7_GUEST_LEAVES);
		CHECK(maps[guest].hpa_base == guests[guest].hpa);
		/* Root index 2 points at this pool's own level-1 page. */
		CHECK(get_le64(own) == 0U && get_le64(own + 8U) == 0U);
		CHECK(get_le64(own + 16U) == guests[guest].root_pte);
		CHECK(get_le64(own + 24U) == 0U);
		/* Level-1 indices 0-31: 0xdf leaves onto the guest's window. */
		for (leaf = 0U; leaf < 32U; ++leaf)
			CHECK(get_le64(own + 0x4000U + leaf * 8U) ==
			      (0xdfU | (((guests[guest].hpa + leaf * 2U * MIB) >>
					 12) << 10)));
		CHECK(get_le64(own + 0x4000U) == guests[guest].first_leaf);
		CHECK(get_le64(own + 0x4000U + 32U * 8U) == 0U);
	}
	/* The two roots are disjoint, either way round. */
	CHECK(be_b7_gstage_pair_check(&maps[0], &maps[1]) == BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_pair_check(&maps[1], &maps[0]) == BE_B7_GSTAGE_OK);
	/* G0's window ends where G1's starts. */
	CHECK(maps[0].hpa_base + maps[0].size == maps[1].hpa_base);
}

/* Two walked roots that share a page, a window, a VMID, or a root. */
static void test_pairs(void)
{
	struct be_b7_gstage_desc g0 = { GPA_G0, HPA_G0, 64U * MIB, POOL_G0, 1U };
	struct be_b7_gstage_desc g1 = { GPA_G0, HPA_G1, 64U * MIB, POOL_G1, 2U };
	struct be_b7_gstage_desc other;
	struct be_b7_gstage_map first;
	struct be_b7_gstage_map second;
	struct be_b7_gstage_map bad;

	SCENARIO();
	CHECK(be_b7_gstage_build(&g0, pool, sizeof(pool)) == BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_walk(&g0, pool, sizeof(pool), &first) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_build(&g1, pool, sizeof(pool)) == BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_walk(&g1, pool, sizeof(pool), &second) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_pair_check(&first, &second) == BE_B7_GSTAGE_OK);
	/* Equal VMIDs, either zero, and one map against itself. */
	bad = second;
	bad.vmid = first.vmid;
	CHECK(be_b7_gstage_pair_check(&first, &bad) == BE_B7_GSTAGE_PAIR);
	bad = second;
	bad.vmid = 0U;
	CHECK(be_b7_gstage_pair_check(&first, &bad) == BE_B7_GSTAGE_PAIR);
	CHECK(be_b7_gstage_pair_check(&bad, &first) == BE_B7_GSTAGE_PAIR);
	CHECK(be_b7_gstage_pair_check(&first, &first) == BE_B7_GSTAGE_PAIR);
	/* The same root under two VMIDs: one pool for both guests. */
	other = g1;
	other.pool_pa = POOL_G0;
	CHECK(be_b7_gstage_build(&other, pool, sizeof(pool)) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_walk(&other, pool, sizeof(pool), &bad) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_pair_check(&first, &bad) == BE_B7_GSTAGE_PAIR);
	/* Pools that share one page: G1's pool 16 KiB into G0's. */
	other = g1;
	other.pool_pa = POOL_G0 + 0x4000U;
	CHECK(be_b7_gstage_build(&other, pool, sizeof(pool)) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_walk(&other, pool, sizeof(pool), &bad) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_pair_check(&first, &bad) == BE_B7_GSTAGE_PAIR);
	CHECK(be_b7_gstage_pair_check(&bad, &first) == BE_B7_GSTAGE_PAIR);
	/* Pools that touch but do not share a byte are disjoint. */
	other = g1;
	other.pool_pa = POOL_G0 - 0x8000U;
	CHECK(be_b7_gstage_build(&other, pool, sizeof(pool)) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_walk(&other, pool, sizeof(pool), &bad) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_pair_check(&first, &bad) == BE_B7_GSTAGE_OK);
	/* The same window, and windows that share their last 2 MiB. */
	other = g1;
	other.hpa_base = HPA_G0;
	CHECK(be_b7_gstage_build(&other, pool, sizeof(pool)) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_walk(&other, pool, sizeof(pool), &bad) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_pair_check(&first, &bad) == BE_B7_GSTAGE_PAIR);
	other = g1;
	other.hpa_base = HPA_G1 - 2U * MIB;
	CHECK(be_b7_gstage_build(&other, pool, sizeof(pool)) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_walk(&other, pool, sizeof(pool), &bad) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_pair_check(&first, &bad) == BE_B7_GSTAGE_PAIR);
	CHECK(be_b7_gstage_pair_check(&bad, &first) == BE_B7_GSTAGE_PAIR);
	/* G1's window covers G0's pool (but not its own). */
	other = (struct be_b7_gstage_desc){ GPA_G0, BE_U64_C(0x102000000),
					    2U * MIB, BE_U64_C(0x102200000),
					    2U };
	CHECK(be_b7_gstage_build(&other, pool, sizeof(pool)) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_walk(&other, pool, sizeof(pool), &bad) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_pair_check(&first, &bad) == BE_B7_GSTAGE_PAIR);
	CHECK(be_b7_gstage_pair_check(&bad, &first) == BE_B7_GSTAGE_PAIR);
	/* An unwalked map, and absent maps. */
	memset(&bad, 0, sizeof(bad));
	CHECK(be_b7_gstage_pair_check(&first, &bad) == BE_B7_GSTAGE_PAIR);
	bad = second;
	bad.hgatp &= ~(BE_U64_C(0xf) << 60);
	CHECK(be_b7_gstage_pair_check(&first, &bad) == BE_B7_GSTAGE_PAIR);
	CHECK(be_b7_gstage_pair_check((const struct be_b7_gstage_map *)0,
				      &second) == BE_B7_GSTAGE_NULL);
	CHECK(be_b7_gstage_pair_check(&first,
				      (const struct be_b7_gstage_map *)0) ==
	      BE_B7_GSTAGE_NULL);
}

/* VMIDs: the full 14-bit range builds and walks; 2^14 and above do not. */
static void test_vmids(void)
{
	static const be_u64 good[] = { 0U, 1U, 2U, 0x2000U, 0x3fffU };
	static const be_u64 refused[] = { 0x4000U, 0x8000U, ALL_ONES };
	struct be_b7_gstage_desc desc = { GPA_G0, HPA_G0, 64U * MIB, POOL_G0,
					  1U };
	struct be_b7_gstage_map map;
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(good); ++index) {
		desc.vmid = good[index];
		CHECK(be_b7_gstage_build(&desc, pool, sizeof(pool)) ==
		      BE_B7_GSTAGE_OK);
		CHECK(be_b7_gstage_walk(&desc, pool, sizeof(pool), &map) ==
		      BE_B7_GSTAGE_OK);
		CHECK(map.vmid == good[index]);
		CHECK(map.hgatp == ((BE_U64_C(8) << 60) | (good[index] << 44) |
				    (POOL_G0 >> 12)));
	}
	/* A walk against a refused VMID refuses a valid pool. */
	for (index = 0U; index < BE_ARRAY_SIZE(refused); ++index) {
		desc.vmid = refused[index];
		CHECK(be_b7_gstage_walk(&desc, pool, sizeof(pool), &map) ==
		      BE_B7_GSTAGE_DESC);
		CHECK(map.hgatp == 0U && map.vmid == 0U);
		memset(pool, 0xa5, sizeof(pool));
		CHECK(be_b7_gstage_build(&desc, pool, sizeof(pool)) ==
		      BE_B7_GSTAGE_DESC);
		CHECK(pool[0] == 0U && pool[sizeof(pool) - 1U] == 0U);
		desc.vmid = 1U;
		CHECK(be_b7_gstage_build(&desc, pool, sizeof(pool)) ==
		      BE_B7_GSTAGE_OK);
	}
}

/* Every bit of every nonzero entry, and nonzero bytes in the zero regions. */
static void check_mutations(be_u64 gpa, be_u64 hpa, be_u64 size)
{
	static const be_u64 targeted[] = {
		0x0U, 0x8U, 0x18U, 0x3ff8U, 0x3fffU, 0x4100U, 0x4ff8U,
		0x5000U, 0x5fffU, 0x7ff8U, 0x7fffU,
	};
	struct be_b7_gstage_desc desc = { gpa, hpa, size, POOL_G0, 1U };
	struct be_b7_gstage_map map;
	be_u64 offset;
	be_size index;
	unsigned int bit;
	unsigned long flips = 0U;

	SCENARIO();
	CHECK(be_b7_gstage_build(&desc, pool, sizeof(pool)) ==
	      BE_B7_GSTAGE_OK);
	for (offset = 0U; offset < BE_B7_GSTAGE_POOL_BYTES; offset += 8U) {
		if (get_le64(pool + offset) == 0U)
			continue;
		for (bit = 0U; bit < 64U; ++bit) {
			memcpy(scratch, pool, sizeof(pool));
			scratch[offset + bit / 8U] ^= (be_u8)(1U << (bit % 8U));
			CHECK(be_b7_gstage_walk(&desc, scratch, sizeof(scratch),
						&map) != BE_B7_GSTAGE_OK);
			CHECK(map.size == 0U && map.hgatp == 0U);
			++flips;
		}
	}
	for (offset = 0U; offset < BE_B7_GSTAGE_POOL_BYTES; offset += 61U) {
		if (pool[offset] != 0U)
			continue;
		memcpy(scratch, pool, sizeof(pool));
		scratch[offset] = 0x01U;
		CHECK(be_b7_gstage_walk(&desc, scratch, sizeof(scratch), &map) !=
		      BE_B7_GSTAGE_OK);
		++flips;
	}
	for (index = 0U; index < BE_ARRAY_SIZE(targeted); ++index) {
		if (pool[targeted[index]] != 0U)
			continue;
		memcpy(scratch, pool, sizeof(pool));
		scratch[targeted[index]] = 0x80U;
		CHECK(be_b7_gstage_walk(&desc, scratch, sizeof(scratch), &map) !=
		      BE_B7_GSTAGE_OK);
		++flips;
	}
	CHECK(flips > (size / (2U * MIB) + 1U) * 64U);
}

/* Whole-entry moves: a moved root slot or leaf run is another window. */
static void test_moves(void)
{
	struct be_b7_gstage_desc desc = { GPA_G0, HPA_G0, 64U * MIB, POOL_G0,
					  1U };
	struct be_b7_gstage_map map;
	be_u64 leaf4;
	be_u64 leaf5;

	SCENARIO();
	CHECK(be_b7_gstage_build(&desc, pool, sizeof(pool)) ==
	      BE_B7_GSTAGE_OK);
	/* The root pointer moved from slot 2 to slot 3. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 24U, get_le64(scratch + 16U));
	put_le64(scratch + 16U, 0U);
	CHECK(be_b7_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_B7_GSTAGE_MISMATCH);
	/* A second root pointer. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 24U, get_le64(scratch + 16U));
	CHECK(be_b7_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_B7_GSTAGE_ROOT);
	/* The leaf run moved up by one slot: GPA 0x8020_0000. */
	memcpy(scratch, pool, sizeof(pool));
	memmove(scratch + 0x4008U, scratch + 0x4000U, 32U * 8U);
	put_le64(scratch + 0x4000U, 0U);
	CHECK(be_b7_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_B7_GSTAGE_MISMATCH);
	/* One leaf dropped from the end: 62 MiB. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 0x4000U + 31U * 8U, 0U);
	CHECK(be_b7_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_B7_GSTAGE_MISMATCH);
	/* One linear leaf added at the end: 66 MiB. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 0x4000U + 32U * 8U,
		 0xdfU | (((HPA_G0 + 64U * MIB) >> 12) << 10));
	CHECK(be_b7_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_B7_GSTAGE_MISMATCH);
	/* A hole in the run. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 0x4000U + 7U * 8U, 0U);
	CHECK(be_b7_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_B7_GSTAGE_L1);
	/* Two leaves swapped: no longer linear. */
	memcpy(scratch, pool, sizeof(pool));
	leaf4 = get_le64(scratch + 0x4000U + 4U * 8U);
	leaf5 = get_le64(scratch + 0x4000U + 5U * 8U);
	put_le64(scratch + 0x4000U + 4U * 8U, leaf5);
	put_le64(scratch + 0x4000U + 5U * 8U, leaf4);
	CHECK(be_b7_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_B7_GSTAGE_L1);
	/* A leaf pointing at the pool itself is not this window. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 0x4000U, 0xdfU | ((BE_U64_C(0x102000000) >> 12) << 10));
	CHECK(be_b7_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_B7_GSTAGE_L1);
}

static void test_refusals(void)
{
	static const struct {
		be_u64 gpa, hpa, size, pool_pa;
		enum be_b7_gstage_error error;
	} cases[] = {
		{ GPA_G0 + 0x1000U, HPA_G0, 64U * MIB, POOL_G0,
		  BE_B7_GSTAGE_DESC },
		{ GPA_G0 + MIB, HPA_G0, 64U * MIB, POOL_G0, BE_B7_GSTAGE_DESC },
		{ GPA_G0, HPA_G0 + 0x1000U, 64U * MIB, POOL_G0,
		  BE_B7_GSTAGE_DESC },
		{ GPA_G0, HPA_G0 + MIB, 64U * MIB, POOL_G0, BE_B7_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 64U * MIB + 0x1000U, POOL_G0,
		  BE_B7_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 64U * MIB - MIB, POOL_G0, BE_B7_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 0U, POOL_G0, BE_B7_GSTAGE_DESC },
		/* Crosses a 1 GiB boundary: would need a second level-1 page. */
		{ BE_U64_C(0xbfe00000), HPA_G0, 4U * MIB, POOL_G0,
		  BE_B7_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, BE_U64_C(1) << 31, POOL_G0,
		  BE_B7_GSTAGE_DESC },
		{ (BE_U64_C(1) << 41) - 2U * MIB, HPA_G0, 4U * MIB, POOL_G0,
		  BE_B7_GSTAGE_DESC },
		{ BE_U64_C(1) << 41, HPA_G0, 2U * MIB, POOL_G0,
		  BE_B7_GSTAGE_DESC },
		{ ALL_ONES - 2U * MIB + 1U, HPA_G0, 2U * MIB, POOL_G0,
		  BE_B7_GSTAGE_DESC },
		{ GPA_G0, (BE_U64_C(1) << 56) - 2U * MIB, 4U * MIB, POOL_G0,
		  BE_B7_GSTAGE_DESC },
		{ GPA_G0, BE_U64_C(1) << 56, 2U * MIB, POOL_G0,
		  BE_B7_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 64U * MIB, POOL_G0 + 0x1000U,
		  BE_B7_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 64U * MIB, POOL_G0 + 0x2000U,
		  BE_B7_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 64U * MIB, BE_U64_C(1) << 56,
		  BE_B7_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 64U * MIB, (BE_U64_C(1) << 56) - 0x4000U,
		  BE_B7_GSTAGE_DESC },
		/* The window covers its own tables. */
		{ GPA_G0, BE_U64_C(0x102000000), 64U * MIB, POOL_G0,
		  BE_B7_GSTAGE_POOL },
		/* The window's last 2 MiB covers the pool. */
		{ GPA_G0, BE_U64_C(0x100000000), 34U * MIB, POOL_G0,
		  BE_B7_GSTAGE_POOL },
		/* The window's only 2 MiB covers the pool. */
		{ GPA_G0, BE_U64_C(0x102000000), 2U * MIB, POOL_G0,
		  BE_B7_GSTAGE_POOL },
	};
	struct be_b7_gstage_desc good = { GPA_G0, HPA_G0, 64U * MIB, POOL_G0,
					  1U };
	struct be_b7_gstage_desc bad;
	struct be_b7_gstage_map map;
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(cases); ++index) {
		bad = (struct be_b7_gstage_desc){ cases[index].gpa,
						  cases[index].hpa,
						  cases[index].size,
						  cases[index].pool_pa, 1U };
		memset(pool, 0xa5, sizeof(pool));
		CHECK(be_b7_gstage_build(&bad, pool, sizeof(pool)) ==
		      cases[index].error);
		/* A refused build leaves a scrubbed pool. */
		memset(expected, 0, sizeof(expected));
		CHECK(memcmp(pool, expected, sizeof(pool)) == 0);
	}
	/* A valid pool walked against another descriptor is refused. */
	CHECK(be_b7_gstage_build(&good, pool, sizeof(pool)) ==
	      BE_B7_GSTAGE_OK);
	bad = good;
	bad.size = 128U * MIB;
	CHECK(be_b7_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_B7_GSTAGE_MISMATCH);
	bad = good;
	bad.size = 62U * MIB;
	CHECK(be_b7_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_B7_GSTAGE_MISMATCH);
	bad = good;
	bad.hpa_base += 2U * MIB;
	CHECK(be_b7_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_B7_GSTAGE_MISMATCH);
	bad = good;
	bad.gpa_base += 2U * MIB;
	CHECK(be_b7_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_B7_GSTAGE_MISMATCH);
	bad = good;
	bad.pool_pa += 0x4000U;
	CHECK(be_b7_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_B7_GSTAGE_ROOT);
	bad = good;
	bad.pool_pa += 0x1000U;
	CHECK(be_b7_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_B7_GSTAGE_POOL);
	CHECK(map.hgatp == 0U && map.size == 0U && map.pool_pa == 0U);
	/* Size and null refusals; a wrong-size pool is never written. */
	memset(pool, 0xa5, sizeof(pool));
	CHECK(be_b7_gstage_build(&good, pool, sizeof(pool) - 8U) ==
	      BE_B7_GSTAGE_POOL);
	CHECK(pool[0] == 0xa5U && pool[sizeof(pool) - 1U] == 0xa5U);
	CHECK(be_b7_gstage_build(&good, pool, sizeof(pool) + 8U) ==
	      BE_B7_GSTAGE_POOL);
	CHECK(be_b7_gstage_build(&good, (be_u8 *)0, sizeof(pool)) ==
	      BE_B7_GSTAGE_NULL);
	CHECK(be_b7_gstage_build((const struct be_b7_gstage_desc *)0, pool,
				 sizeof(pool)) == BE_B7_GSTAGE_NULL);
	CHECK(pool[0] == 0U && pool[sizeof(pool) - 1U] == 0U);
	CHECK(be_b7_gstage_walk(&good, pool, sizeof(pool),
				(struct be_b7_gstage_map *)0) ==
	      BE_B7_GSTAGE_NULL);
	CHECK(be_b7_gstage_walk(&good, (const be_u8 *)0, sizeof(pool), &map) ==
	      BE_B7_GSTAGE_NULL);
	CHECK(be_b7_gstage_walk((const struct be_b7_gstage_desc *)0, pool,
				sizeof(pool), &map) == BE_B7_GSTAGE_NULL);
	CHECK(be_b7_gstage_walk(&good, pool, sizeof(pool) + 8U, &map) ==
	      BE_B7_GSTAGE_POOL);
	/* A window that ends where the pool starts is accepted. */
	bad = (struct be_b7_gstage_desc){ GPA_G0, BE_U64_C(0x101e00000),
					  2U * MIB, BE_U64_C(0x102000000),
					  1U };
	CHECK(be_b7_gstage_build(&bad, pool, sizeof(pool)) ==
	      BE_B7_GSTAGE_OK);
	CHECK(be_b7_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_B7_GSTAGE_OK);
	/* An empty pool has no root pointer; a root alone has no leaves. */
	memset(pool, 0, sizeof(pool));
	CHECK(be_b7_gstage_walk(&good, pool, sizeof(pool), &map) ==
	      BE_B7_GSTAGE_ROOT);
	CHECK(be_b7_gstage_build(&good, pool, sizeof(pool)) ==
	      BE_B7_GSTAGE_OK);
	memset(pool + 0x4000U, 0, 0x1000U);
	CHECK(be_b7_gstage_walk(&good, pool, sizeof(pool), &map) ==
	      BE_B7_GSTAGE_L1);
}

int main(void)
{
	test_constants();
	check_window(GPA_G0, HPA_G0, 64U * MIB, POOL_G0, 1U);
	check_window(GPA_G0, HPA_G1, 64U * MIB, POOL_G1, 2U);
	check_window(GPA_G0, HPA_G0, 128U * MIB, POOL_G0, 1U);
	check_window(GPA_G0, HPA_OTHER, 64U * MIB, POOL_G0, 0x3fffU);
	check_window(BE_U64_C(0xbfe00000), HPA_G0, 2U * MIB, POOL_G0, 0U);
	check_window(GPA_G0, HPA_G0, 1024U * MIB, POOL_G0, 2U);
	check_window(BE_U64_C(0x40000000), HPA_G0, 64U * MIB,
		     BE_U64_C(0x108000000), 1U);
	test_b7_windows();
	test_pairs();
	test_vmids();
	check_mutations(GPA_G0, HPA_G0, 64U * MIB);
	check_mutations(GPA_G0, HPA_G0, 128U * MIB);
	check_mutations(GPA_G0, HPA_G1, 64U * MIB);
	test_moves();
	test_refusals();
	printf("BE_B7_GSTAGE_CHECK: PASS\n");
	printf("BE_B7_GSTAGE_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_B7_GSTAGE_CHECK: assertions=%lu\n", assertions);
	return 0;
}
