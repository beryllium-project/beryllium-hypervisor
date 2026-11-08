// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the MVP G-stage builder, re-walker, pair
 *          check, and translation: both fixed MVP windows, pools, VMIDs, and
 *          harts against an independent byte model, other windows (128 MiB,
 *          another HPA, the last 2 MiB below a 1 GiB boundary, a full
 *          1 GiB), VMIDs, and harts, every single-bit flip of every nonzero
 *          entry, sampled and targeted nonzero bytes in the zero regions,
 *          whole-entry moves, descriptor and VMID refusals, two roots that
 *          share a page, a window, a VMID, a root, or a hart, or name the
 *          control hart, and translation edges; and, for the channel page
 *          (M1), M0's bytes and maps without one, the plan's pointers and
 *          leaves for both roots, other pages at the edges of their rules,
 *          every page refusal, every walker refusal of the level-1 pointer
 *          and the level-0 leaf, every single-bit flip of a channel root,
 *          every refusal of the channel check with the root it names, and
 *          the plan's three host mutations; and, for the declared pages
 *          (M2), the plan's three leaves in each root with their exact
 *          PTEs against an independent model, the page check's pass and
 *          its refusals with the page and root they name, every rule of
 *          the declared pages, every walker refusal of the level-0 page,
 *          every single-bit flip of a root with pages, and the two
 *          negative images' leaves, secret-shared's and
 *          response-writable's, as their builders write them.
 *          beryllium-cheri: built with BE_MVP_CHERI, as the CHERI-aware
 *          monitor's (planning/cheri-enforcement-plan.md, CE-2), every
 *          case with CW in each window leaf, and CW in every window leaf
 *          of each MVP root and in no other entry, and the walker's
 *          refusals of a window leaf without CW or with another high bit,
 *          a channel or page leaf with CW, and a pointer with CW.
 * Trust:   host evidence only. No CSR, fence, guest entry, QEMU, or hardware
 *          behaviour is exercised.
 * Scope:   the MVP line (planning/mvp-m0-plan.md, planning/mvp-m1-plan.md,
 *          and planning/mvp-m2-plan.md, "G-stage and VMIDs").
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mvp-gstage.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_MVP_GSTAGE_CHECK: assertion failed: %s:%d: %s\n", \
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
/* The channel (M1 plan, Q1), and the PTEs the plan derives for it. */
#define PAGE			BE_U64_C(0x1000)
#define GPA_CHANNEL		BE_U64_C(0x84000000)
#define HPA_CHANNEL		BE_U64_C(0x118000000)
#define L0_G0			BE_U64_C(0x102039000)
#define L0_G1			BE_U64_C(0x102041000)
#define POINTER_G0		BE_U64_C(0x4080e401)
#define POINTER_G1		BE_U64_C(0x40810401)
#define LEAF_WRITER		BE_U64_C(0x460000d7)
#define LEAF_READER		BE_U64_C(0x46000053)
#define RIGHT_R			BE_MVP_GSTAGE_RIGHT_READ
#define RIGHT_W			BE_MVP_GSTAGE_RIGHT_WRITE
#define RIGHT_X			BE_MVP_GSTAGE_RIGHT_EXECUTE
#define RIGHT_RW		(RIGHT_R | RIGHT_W)
/* An absent root page. */
#define NO_ROOT_PAGE		((const struct be_mvp_gstage_root_page *)0)
/* Pool offsets of a level-1 and a level-0 entry. */
#define L1_AT(entry)		(0x4000U + (entry) * 8U)
#define L0_AT(entry)		(0x5000U + (entry) * 8U)
/*
 * A window leaf's high bits, a literal of the test's own: none.
 * beryllium-cheri: in the CHERI-aware monitor (BE_MVP_CHERI), CW, bit 60,
 * the capability-write bit (planning/cheri-enforcement-plan.md, CE-2).
 */
#ifdef BE_MVP_CHERI
#define WINDOW_CW		(BE_U64_C(1) << 60)
#else
#define WINDOW_CW		BE_U64_C(0)
#endif

static be_u8 pool[BE_MVP_GSTAGE_POOL_BYTES];
static be_u8 expected[BE_MVP_GSTAGE_POOL_BYTES];
static be_u8 scratch[BE_MVP_GSTAGE_POOL_BYTES];
static be_u8 pools[2][BE_MVP_GSTAGE_POOL_BYTES];

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
static void model(const struct be_mvp_gstage_desc *desc)
{
	be_u64 root_pte = 1U | (((desc->pool_pa + 0x4000U) / 4096U) << 10);
	be_u64 slot = desc->gpa_base / (BE_U64_C(1) << 30);
	be_u64 first = (desc->gpa_base % (BE_U64_C(1) << 30)) / (2U * MIB);
	be_u64 leaf;

	memset(expected, 0, sizeof(expected));
	put_le64(expected + slot * 8U, root_pte);
	for (leaf = 0U; leaf < desc->size / (2U * MIB); ++leaf) {
		be_u64 pa = desc->hpa_base + leaf * 2U * MIB;

		/* V R W X U A D = 0xdf; G, RSW, and bits 54-63 clear, but CW
		 * in the CHERI build (WINDOW_CW). */
		put_le64(expected + 0x4000U + (first + leaf) * 8U,
			 0xdfU | WINDOW_CW | ((pa / 4096U) << 10));
	}
}

/*
 * The model with a channel page: a pointer at the page's level-1 entry to
 * the pool's page at +0x5000, and there the one leaf, its flags from the
 * plan's table alone: V U A for map, R for read, W D for write.
 */
static void model_page(const struct be_mvp_gstage_desc *desc,
		       const struct be_mvp_gstage_root_page *page)
{
	be_u64 l1 = (page->gpa % (BE_U64_C(1) << 30)) / (2U * MIB);
	be_u64 l0 = (page->gpa % (2U * MIB)) / PAGE;
	be_u64 flags = 0x51U;

	if ((page->rights & RIGHT_R) != 0U)
		flags |= 0x02U;
	if ((page->rights & RIGHT_W) != 0U)
		flags |= 0x84U;
	model(desc);
	put_le64(expected + L1_AT(l1),
		 1U | (((desc->pool_pa + 0x5000U) / PAGE) << 10));
	put_le64(expected + L0_AT(l0), flags | ((page->hpa / PAGE) << 10));
}

/* One domain's fixed MVP window, pool, VMID, and hart (mvp-layout.h). */
static struct be_mvp_gstage_desc mvp_desc(be_u64 domain)
{
	struct be_mvp_gstage_desc desc = { BE_MVP_GUEST_GPA, BE_MVP_G0_HPA,
					   BE_MVP_GUEST_BYTES,
					   BE_MVP_G0_ROOT_HPA, BE_MVP_G0_VMID,
					   BE_MVP_DOMAIN0_HART };

	if (domain != 0U) {
		desc.hpa_base = BE_MVP_G1_HPA;
		desc.pool_pa = BE_MVP_G1_ROOT_HPA;
		desc.vmid = BE_MVP_G1_VMID;
		desc.hart = BE_MVP_DOMAIN1_HART;
	}
	return desc;
}

/* The fixed channel page (mvp-layout.h) with one root's rights. */
static struct be_mvp_gstage_root_page mvp_page(be_u64 rights)
{
	struct be_mvp_gstage_root_page page = { BE_MVP_CHANNEL_GPA,
					   BE_MVP_CHANNEL_HPA,
					   BE_MVP_CHANNEL_BYTES, rights };

	return page;
}

/* Instance 2's sealed record, with @writer sending to the other domain. */
static struct be_mvp_gstage_channel mvp_record(be_u64 writer)
{
	struct be_mvp_gstage_channel record = {
		BE_MVP_CHANNEL_GPA, BE_MVP_CHANNEL_HPA, BE_MVP_CHANNEL_BYTES,
		writer, 1U - writer, RIGHT_RW, RIGHT_R
	};

	return record;
}

/*
 * Both MVP roots with the channel page, @writer's read-write and the
 * other's read-only, built in pools[] and walked.
 */
static void build_pair(be_u64 writer, struct be_mvp_gstage_map *maps,
		       struct be_mvp_gstage_leaf *leaves)
{
	be_u64 domain;

	for (domain = 0U; domain < 2U; ++domain) {
		struct be_mvp_gstage_desc desc = mvp_desc(domain);
		struct be_mvp_gstage_root_page page =
			mvp_page(domain == writer ? RIGHT_RW : RIGHT_R);

		CHECK(be_mvp_gstage_build_channel(&desc, &page, pools[domain],
						  sizeof(pools[domain])) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk_channel(&desc, &page, pools[domain],
						 sizeof(pools[domain]),
						 &maps[domain],
						 &leaves[domain]) ==
		      BE_MVP_GSTAGE_OK);
	}
}

static int map_empty(const struct be_mvp_gstage_map *map)
{
	return map->hgatp == 0U && map->gpa_base == 0U &&
	       map->hpa_base == 0U && map->size == 0U && map->leaves == 0U &&
	       map->pool_pa == 0U && map->vmid == 0U && map->hart == 0U;
}

static int leaf_empty(const struct be_mvp_gstage_leaf *leaf)
{
	return leaf->gpa == 0U && leaf->hpa == 0U && leaf->bytes == 0U &&
	       leaf->pte == 0U && leaf->l0_pa == 0U;
}

/* The root a channel check's refusal names, and its two PTEs. */
static int refusal_is(const struct be_mvp_gstage_refusal *refusal,
		      be_u64 domain, be_u64 hart, be_u64 walked_pte,
		      be_u64 declared_pte)
{
	return refusal->domain == domain && refusal->hart == hart &&
	       refusal->walked == walked_pte &&
	       refusal->declared == declared_pte;
}

/* Walk scratch[] with its page; a refused walk leaves map and leaf zero. */
static enum be_mvp_gstage_error
walk_scratch(const struct be_mvp_gstage_desc *desc,
	     const struct be_mvp_gstage_root_page *page)
{
	struct be_mvp_gstage_map map;
	struct be_mvp_gstage_leaf leaf;
	enum be_mvp_gstage_error error;

	error = be_mvp_gstage_walk_channel(desc, page, scratch,
					   sizeof(scratch), &map, &leaf);
	if (error != BE_MVP_GSTAGE_OK)
		CHECK(map_empty(&map) && leaf_empty(&leaf));
	return error;
}

static void test_constants(void)
{
	SCENARIO();
	CHECK(BE_MVP_GSTAGE_POOL_BYTES == 0x8000U);
	CHECK(BE_MVP_GSTAGE_L1_OFFSET == 0x4000U);
	CHECK(BE_MVP_GSTAGE_L0_OFFSET == 0x5000U);
	CHECK(BE_MVP_GSTAGE_SPARE_OFFSET == 0x6000U);
	CHECK(BE_MVP_GSTAGE_LEAF_BYTES == 2U * MIB);
	CHECK(BE_MVP_GSTAGE_VMID_SHIFT == 44U);
	CHECK(BE_MVP_GSTAGE_VMID_LIMIT == 0x4000U);
	CHECK(BE_MVP_PTE_LEAF_FLAGS == 0xdfU);
	CHECK(BE_MVP_DOMAINS == 2U);
	CHECK(BE_MVP_POOL_HPA == POOL_G0 && BE_MVP_POOL_BYTES == 0x10000U);
	CHECK(BE_MVP_GUEST_POOL_BYTES == 0x8000U);
	CHECK(BE_MVP_G0_ROOT_HPA == POOL_G0 &&
	      BE_MVP_G0_LEVEL1_HPA == POOL_G0 + 0x4000U);
	CHECK(BE_MVP_G1_ROOT_HPA == POOL_G1 &&
	      BE_MVP_G1_LEVEL1_HPA == POOL_G1 + 0x4000U);
	CHECK(POOL_G1 == POOL_G0 + 0x8000U);
	CHECK(BE_MVP_G0_VMID == 1U && BE_MVP_G1_VMID == 2U);
	CHECK(BE_MVP_G0_HGATP == BE_U64_C(0x8000100000102034));
	CHECK(BE_MVP_G1_HGATP == BE_U64_C(0x800020000010203c));
	CHECK(BE_MVP_GUEST_GPA == GPA_G0);
	CHECK(BE_MVP_G0_HPA == HPA_G0 && BE_MVP_G1_HPA == HPA_G1);
	CHECK(BE_MVP_GUEST_BYTES == 64U * MIB && BE_MVP_GUEST_LEAVES == 32U);
	CHECK(sizeof(struct be_mvp_gstage_desc) == 6U * sizeof(be_u64));
	CHECK(sizeof(struct be_mvp_gstage_map) == 8U * sizeof(be_u64));
	CHECK(sizeof(struct be_mvp_gstage_channel) == 7U * sizeof(be_u64));
	CHECK(BE_MVP_CONTROL_HART == 0U && BE_MVP_DOMAIN0_HART == 1U &&
	      BE_MVP_DOMAIN1_HART == 2U);
	CHECK(BE_MVP_G0_LEVEL0_HPA == L0_G0 && BE_MVP_G1_LEVEL0_HPA == L0_G1);
	CHECK(BE_MVP_CHANNELS_MAX == 1U && BE_MVP_CHANNEL_GPA == GPA_CHANNEL &&
	      BE_MVP_CHANNEL_HPA == HPA_CHANNEL &&
	      BE_MVP_CHANNEL_BYTES == PAGE);
}

static void check_window(be_u64 gpa, be_u64 hpa, be_u64 size, be_u64 pool_pa,
			 be_u64 vmid, be_u64 hart)
{
	struct be_mvp_gstage_desc desc = { gpa, hpa, size, pool_pa, vmid,
					   hart };
	struct be_mvp_gstage_map map;
	be_u64 leaf;
	be_u64 out = 0U;

	SCENARIO();
	memset(pool, 0xa5, sizeof(pool));
	CHECK(be_mvp_gstage_build(&desc, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	model(&desc);
	CHECK(memcmp(pool, expected, sizeof(pool)) == 0);
	CHECK(be_mvp_gstage_walk(&desc, pool, sizeof(pool), &map) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(map.hgatp == ((BE_U64_C(8) << 60) | (vmid << 44) |
			    (pool_pa >> 12)));
	CHECK(map.gpa_base == gpa && map.hpa_base == hpa && map.size == size);
	CHECK(map.leaves == size / (2U * MIB) && map.pool_pa == pool_pa);
	CHECK(map.vmid == vmid && map.hart == hart);
	for (leaf = 0U; leaf < map.leaves; ++leaf) {
		be_u64 offset = leaf * 2U * MIB + 0x123U;

		CHECK(be_mvp_gstage_translate(&map, gpa + offset, 1U, &out) == 1);
		CHECK(out == hpa + offset);
		/* A whole 4 KiB page at each leaf's end, as Linux writes. */
		offset = (leaf + 1U) * 2U * MIB - 0x1000U;
		CHECK(be_mvp_gstage_translate(&map, gpa + offset, 0x1000U,
					     &out) == 1);
		CHECK(out == hpa + offset);
	}
	/* Edges: first byte, last byte, whole window, one past, before. */
	CHECK(be_mvp_gstage_translate(&map, gpa, 1U, &out) == 1 && out == hpa);
	CHECK(be_mvp_gstage_translate(&map, gpa + size - 1U, 1U, &out) == 1 &&
	      out == hpa + size - 1U);
	CHECK(be_mvp_gstage_translate(&map, gpa, size, &out) == 1 &&
	      out == hpa);
	out = 7U;
	CHECK(be_mvp_gstage_translate(&map, gpa + size, 1U, &out) == 0 &&
	      out == 7U);
	CHECK(be_mvp_gstage_translate(&map, gpa - 1U, 1U, &out) == 0);
	CHECK(be_mvp_gstage_translate(&map, gpa - 1U, 2U, &out) == 0);
	CHECK(be_mvp_gstage_translate(&map, gpa + size - 1U, 2U, &out) == 0);
	CHECK(be_mvp_gstage_translate(&map, gpa, size + 1U, &out) == 0);
	CHECK(be_mvp_gstage_translate(&map, gpa, 0U, &out) == 0);
	CHECK(be_mvp_gstage_translate(&map, gpa + 8U, ALL_ONES, &out) == 0);
	CHECK(be_mvp_gstage_translate(&map, ALL_ONES, 2U, &out) == 0);
	CHECK(be_mvp_gstage_translate(&map, 0U, 1U, &out) == 0);
	CHECK(be_mvp_gstage_translate(&map, hpa, 1U, &out) == 0);
	CHECK(out == 7U);
	CHECK(be_mvp_gstage_translate((const struct be_mvp_gstage_map *)0, gpa,
				     1U, &out) == 0);
	CHECK(be_mvp_gstage_translate(&map, gpa, 1U, (be_u64 *)0) == 0);
}

/*
 * The fixed MVP windows: each pool's root slot, its leaves, and the hgatp
 * its domain hart installs, built in the layout's back-to-back pools.
 */
static void test_mvp_windows(void)
{
	static const struct {
		be_u64 hpa, pool_pa, vmid, hart, hgatp, root_pte, first_leaf;
	} guests[] = {
		{ BE_MVP_G0_HPA, BE_MVP_G0_ROOT_HPA, BE_MVP_G0_VMID,
		  BE_MVP_DOMAIN0_HART, BE_MVP_G0_HGATP, BE_U64_C(0x4080e001),
		  BE_U64_C(0x440000df) | WINDOW_CW },
		{ BE_MVP_G1_HPA, BE_MVP_G1_ROOT_HPA, BE_MVP_G1_VMID,
		  BE_MVP_DOMAIN1_HART, BE_MVP_G1_HGATP, BE_U64_C(0x40810001),
		  BE_U64_C(0x450000df) | WINDOW_CW },
	};
	static be_u8 both[BE_MVP_POOL_BYTES];
	struct be_mvp_gstage_map maps[2];
	be_u64 guest;
	be_u64 leaf;

	SCENARIO();
	memset(both, 0xa5, sizeof(both));
	for (guest = 0U; guest < 2U; ++guest) {
		struct be_mvp_gstage_desc desc = {
			BE_MVP_GUEST_GPA, guests[guest].hpa, BE_MVP_GUEST_BYTES,
			guests[guest].pool_pa, guests[guest].vmid,
			guests[guest].hart };
		be_u8 *own = both + (guests[guest].pool_pa - BE_MVP_POOL_HPA);

		CHECK(be_mvp_gstage_build(&desc, own, BE_MVP_GUEST_POOL_BYTES) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk(&desc, own, BE_MVP_GUEST_POOL_BYTES,
					&maps[guest]) == BE_MVP_GSTAGE_OK);
		CHECK(maps[guest].hgatp == guests[guest].hgatp);
		CHECK(maps[guest].vmid == guests[guest].vmid);
		CHECK(maps[guest].hart == guests[guest].hart);
		CHECK(maps[guest].leaves == BE_MVP_GUEST_LEAVES);
		CHECK(maps[guest].hpa_base == guests[guest].hpa);
		/* Root index 2 points at this pool's own level-1 page. */
		CHECK(get_le64(own) == 0U && get_le64(own + 8U) == 0U);
		CHECK(get_le64(own + 16U) == guests[guest].root_pte);
		CHECK(get_le64(own + 24U) == 0U);
		/* Level-1 indices 0-31: 0xdf leaves onto the guest's window. */
		for (leaf = 0U; leaf < 32U; ++leaf)
			CHECK(get_le64(own + 0x4000U + leaf * 8U) ==
			      (0xdfU | WINDOW_CW |
			       (((guests[guest].hpa + leaf * 2U * MIB) >>
				 12) << 10)));
		CHECK(get_le64(own + 0x4000U) == guests[guest].first_leaf);
		CHECK(get_le64(own + 0x4000U + 32U * 8U) == 0U);
	}
	/* The two roots are disjoint, either way round. */
	CHECK(be_mvp_gstage_pair_check(&maps[0], &maps[1]) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_pair_check(&maps[1], &maps[0]) == BE_MVP_GSTAGE_OK);
	/* G0's window ends where G1's starts. */
	CHECK(maps[0].hpa_base + maps[0].size == maps[1].hpa_base);
}

/*
 * Two walked roots that share a page, a window, a VMID, a root, or a hart,
 * or that name the control hart.
 */
static void test_pairs(void)
{
	struct be_mvp_gstage_desc g0 = { GPA_G0, HPA_G0, 64U * MIB, POOL_G0, 1U,
					 1U };
	struct be_mvp_gstage_desc g1 = { GPA_G0, HPA_G1, 64U * MIB, POOL_G1, 2U,
					 2U };
	struct be_mvp_gstage_desc other;
	struct be_mvp_gstage_map first;
	struct be_mvp_gstage_map second;
	struct be_mvp_gstage_map bad;

	SCENARIO();
	CHECK(be_mvp_gstage_build(&g0, pool, sizeof(pool)) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk(&g0, pool, sizeof(pool), &first) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_build(&g1, pool, sizeof(pool)) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk(&g1, pool, sizeof(pool), &second) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_pair_check(&first, &second) == BE_MVP_GSTAGE_OK);
	/* Equal VMIDs, either zero, and one map against itself. */
	bad = second;
	bad.vmid = first.vmid;
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_PAIR);
	bad = second;
	bad.vmid = 0U;
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_PAIR);
	CHECK(be_mvp_gstage_pair_check(&bad, &first) == BE_MVP_GSTAGE_PAIR);
	CHECK(be_mvp_gstage_pair_check(&first, &first) == BE_MVP_GSTAGE_PAIR);
	/* Equal harts, or either the control hart; any other hart is a name
	 * the firmware decides on. */
	bad = second;
	bad.hart = first.hart;
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_PAIR);
	bad = second;
	bad.hart = BE_MVP_CONTROL_HART;
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_PAIR);
	CHECK(be_mvp_gstage_pair_check(&bad, &first) == BE_MVP_GSTAGE_PAIR);
	bad = second;
	bad.hart = BE_MVP_VARIANT_HART_START_HART;
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_pair_check(&bad, &first) == BE_MVP_GSTAGE_OK);
	/* The same root under two VMIDs: one pool for both domains. */
	other = g1;
	other.pool_pa = POOL_G0;
	CHECK(be_mvp_gstage_build(&other, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk(&other, pool, sizeof(pool), &bad) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_PAIR);
	/* Pools that share one page: G1's pool 16 KiB into G0's. */
	other = g1;
	other.pool_pa = POOL_G0 + 0x4000U;
	CHECK(be_mvp_gstage_build(&other, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk(&other, pool, sizeof(pool), &bad) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_PAIR);
	CHECK(be_mvp_gstage_pair_check(&bad, &first) == BE_MVP_GSTAGE_PAIR);
	/* Pools that touch but do not share a byte are disjoint. */
	other = g1;
	other.pool_pa = POOL_G0 - 0x8000U;
	CHECK(be_mvp_gstage_build(&other, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk(&other, pool, sizeof(pool), &bad) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_OK);
	/* The same window, and windows that share their last 2 MiB. */
	other = g1;
	other.hpa_base = HPA_G0;
	CHECK(be_mvp_gstage_build(&other, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk(&other, pool, sizeof(pool), &bad) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_PAIR);
	other = g1;
	other.hpa_base = HPA_G1 - 2U * MIB;
	CHECK(be_mvp_gstage_build(&other, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk(&other, pool, sizeof(pool), &bad) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_PAIR);
	CHECK(be_mvp_gstage_pair_check(&bad, &first) == BE_MVP_GSTAGE_PAIR);
	/* G1's window covers G0's pool (but not its own). */
	other = (struct be_mvp_gstage_desc){ GPA_G0, BE_U64_C(0x102000000),
					     2U * MIB, BE_U64_C(0x102200000),
					     2U, 2U };
	CHECK(be_mvp_gstage_build(&other, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk(&other, pool, sizeof(pool), &bad) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_PAIR);
	CHECK(be_mvp_gstage_pair_check(&bad, &first) == BE_MVP_GSTAGE_PAIR);
	/* An unwalked map, and absent maps. */
	memset(&bad, 0, sizeof(bad));
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_PAIR);
	bad = second;
	bad.hgatp &= ~(BE_U64_C(0xf) << 60);
	CHECK(be_mvp_gstage_pair_check(&first, &bad) == BE_MVP_GSTAGE_PAIR);
	CHECK(be_mvp_gstage_pair_check((const struct be_mvp_gstage_map *)0,
				      &second) == BE_MVP_GSTAGE_NULL);
	CHECK(be_mvp_gstage_pair_check(&first,
				      (const struct be_mvp_gstage_map *)0) ==
	      BE_MVP_GSTAGE_NULL);
}

/* VMIDs: the full 14-bit range builds and walks; 2^14 and above do not. */
static void test_vmids(void)
{
	static const be_u64 good[] = { 0U, 1U, 2U, 0x2000U, 0x3fffU };
	static const be_u64 refused[] = { 0x4000U, 0x8000U, ALL_ONES };
	struct be_mvp_gstage_desc desc = { GPA_G0, HPA_G0, 64U * MIB, POOL_G0,
					   1U, 1U };
	struct be_mvp_gstage_map map;
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(good); ++index) {
		desc.vmid = good[index];
		CHECK(be_mvp_gstage_build(&desc, pool, sizeof(pool)) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk(&desc, pool, sizeof(pool), &map) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(map.vmid == good[index]);
		CHECK(map.hgatp == ((BE_U64_C(8) << 60) | (good[index] << 44) |
				    (POOL_G0 >> 12)));
	}
	/* A walk against a refused VMID refuses a valid pool. */
	for (index = 0U; index < BE_ARRAY_SIZE(refused); ++index) {
		desc.vmid = refused[index];
		CHECK(be_mvp_gstage_walk(&desc, pool, sizeof(pool), &map) ==
		      BE_MVP_GSTAGE_DESC);
		CHECK(map.hgatp == 0U && map.vmid == 0U && map.hart == 0U);
		memset(pool, 0xa5, sizeof(pool));
		CHECK(be_mvp_gstage_build(&desc, pool, sizeof(pool)) ==
		      BE_MVP_GSTAGE_DESC);
		CHECK(pool[0] == 0U && pool[sizeof(pool) - 1U] == 0U);
		desc.vmid = 1U;
		CHECK(be_mvp_gstage_build(&desc, pool, sizeof(pool)) ==
		      BE_MVP_GSTAGE_OK);
	}
}

/* Every bit of every nonzero entry, and nonzero bytes in the zero regions. */
static void check_mutations(be_u64 gpa, be_u64 hpa, be_u64 size)
{
	static const be_u64 targeted[] = {
		0x0U, 0x8U, 0x18U, 0x3ff8U, 0x3fffU, 0x4100U, 0x4ff8U,
		0x5000U, 0x5fffU, 0x7ff8U, 0x7fffU,
	};
	struct be_mvp_gstage_desc desc = { gpa, hpa, size, POOL_G0, 1U, 1U };
	struct be_mvp_gstage_map map;
	be_u64 offset;
	be_size index;
	unsigned int bit;
	unsigned long flips = 0U;

	SCENARIO();
	CHECK(be_mvp_gstage_build(&desc, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	for (offset = 0U; offset < BE_MVP_GSTAGE_POOL_BYTES; offset += 8U) {
		if (get_le64(pool + offset) == 0U)
			continue;
		for (bit = 0U; bit < 64U; ++bit) {
			memcpy(scratch, pool, sizeof(pool));
			scratch[offset + bit / 8U] ^= (be_u8)(1U << (bit % 8U));
			CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch),
						&map) != BE_MVP_GSTAGE_OK);
			CHECK(map.size == 0U && map.hgatp == 0U);
			++flips;
		}
	}
	for (offset = 0U; offset < BE_MVP_GSTAGE_POOL_BYTES; offset += 61U) {
		if (pool[offset] != 0U)
			continue;
		memcpy(scratch, pool, sizeof(pool));
		scratch[offset] = 0x01U;
		CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch), &map) !=
		      BE_MVP_GSTAGE_OK);
		++flips;
	}
	for (index = 0U; index < BE_ARRAY_SIZE(targeted); ++index) {
		if (pool[targeted[index]] != 0U)
			continue;
		memcpy(scratch, pool, sizeof(pool));
		scratch[targeted[index]] = 0x80U;
		CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch), &map) !=
		      BE_MVP_GSTAGE_OK);
		++flips;
	}
	CHECK(flips > (size / (2U * MIB) + 1U) * 64U);
}

/* Whole-entry moves: a moved root slot or leaf run is another window. */
static void test_moves(void)
{
	struct be_mvp_gstage_desc desc = { GPA_G0, HPA_G0, 64U * MIB, POOL_G0,
					   1U, 1U };
	struct be_mvp_gstage_map map;
	be_u64 leaf4;
	be_u64 leaf5;

	SCENARIO();
	CHECK(be_mvp_gstage_build(&desc, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	/* The root pointer moved from slot 2 to slot 3. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 24U, get_le64(scratch + 16U));
	put_le64(scratch + 16U, 0U);
	CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_MVP_GSTAGE_MISMATCH);
	/* A second root pointer. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 24U, get_le64(scratch + 16U));
	CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_MVP_GSTAGE_ROOT);
	/* The leaf run moved up by one slot: GPA 0x8020_0000. */
	memcpy(scratch, pool, sizeof(pool));
	memmove(scratch + 0x4008U, scratch + 0x4000U, 32U * 8U);
	put_le64(scratch + 0x4000U, 0U);
	CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_MVP_GSTAGE_MISMATCH);
	/* One leaf dropped from the end: 62 MiB. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 0x4000U + 31U * 8U, 0U);
	CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_MVP_GSTAGE_MISMATCH);
	/* One linear leaf added at the end: 66 MiB. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 0x4000U + 32U * 8U,
		 0xdfU | WINDOW_CW | (((HPA_G0 + 64U * MIB) >> 12) << 10));
	CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_MVP_GSTAGE_MISMATCH);
	/* A hole in the run. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 0x4000U + 7U * 8U, 0U);
	CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_MVP_GSTAGE_L1);
	/* Two leaves swapped: no longer linear. */
	memcpy(scratch, pool, sizeof(pool));
	leaf4 = get_le64(scratch + 0x4000U + 4U * 8U);
	leaf5 = get_le64(scratch + 0x4000U + 5U * 8U);
	put_le64(scratch + 0x4000U + 4U * 8U, leaf5);
	put_le64(scratch + 0x4000U + 5U * 8U, leaf4);
	CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_MVP_GSTAGE_L1);
	/* A leaf pointing at the pool itself is not this window. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 0x4000U, 0xdfU | WINDOW_CW |
		 ((BE_U64_C(0x102000000) >> 12) << 10));
	CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_MVP_GSTAGE_L1);
}

static void test_refusals(void)
{
	static const struct {
		be_u64 gpa, hpa, size, pool_pa;
		enum be_mvp_gstage_error error;
	} cases[] = {
		{ GPA_G0 + 0x1000U, HPA_G0, 64U * MIB, POOL_G0,
		  BE_MVP_GSTAGE_DESC },
		{ GPA_G0 + MIB, HPA_G0, 64U * MIB, POOL_G0, BE_MVP_GSTAGE_DESC },
		{ GPA_G0, HPA_G0 + 0x1000U, 64U * MIB, POOL_G0,
		  BE_MVP_GSTAGE_DESC },
		{ GPA_G0, HPA_G0 + MIB, 64U * MIB, POOL_G0, BE_MVP_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 64U * MIB + 0x1000U, POOL_G0,
		  BE_MVP_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 64U * MIB - MIB, POOL_G0, BE_MVP_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 0U, POOL_G0, BE_MVP_GSTAGE_DESC },
		/* Crosses a 1 GiB boundary: would need a second level-1 page. */
		{ BE_U64_C(0xbfe00000), HPA_G0, 4U * MIB, POOL_G0,
		  BE_MVP_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, BE_U64_C(1) << 31, POOL_G0,
		  BE_MVP_GSTAGE_DESC },
		{ (BE_U64_C(1) << 41) - 2U * MIB, HPA_G0, 4U * MIB, POOL_G0,
		  BE_MVP_GSTAGE_DESC },
		{ BE_U64_C(1) << 41, HPA_G0, 2U * MIB, POOL_G0,
		  BE_MVP_GSTAGE_DESC },
		{ ALL_ONES - 2U * MIB + 1U, HPA_G0, 2U * MIB, POOL_G0,
		  BE_MVP_GSTAGE_DESC },
		{ GPA_G0, (BE_U64_C(1) << 56) - 2U * MIB, 4U * MIB, POOL_G0,
		  BE_MVP_GSTAGE_DESC },
		{ GPA_G0, BE_U64_C(1) << 56, 2U * MIB, POOL_G0,
		  BE_MVP_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 64U * MIB, POOL_G0 + 0x1000U,
		  BE_MVP_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 64U * MIB, POOL_G0 + 0x2000U,
		  BE_MVP_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 64U * MIB, BE_U64_C(1) << 56,
		  BE_MVP_GSTAGE_DESC },
		{ GPA_G0, HPA_G0, 64U * MIB, (BE_U64_C(1) << 56) - 0x4000U,
		  BE_MVP_GSTAGE_DESC },
		/* The window covers its own tables. */
		{ GPA_G0, BE_U64_C(0x102000000), 64U * MIB, POOL_G0,
		  BE_MVP_GSTAGE_POOL },
		/* The window's last 2 MiB covers the pool. */
		{ GPA_G0, BE_U64_C(0x100000000), 34U * MIB, POOL_G0,
		  BE_MVP_GSTAGE_POOL },
		/* The window's only 2 MiB covers the pool. */
		{ GPA_G0, BE_U64_C(0x102000000), 2U * MIB, POOL_G0,
		  BE_MVP_GSTAGE_POOL },
	};
	struct be_mvp_gstage_desc good = { GPA_G0, HPA_G0, 64U * MIB, POOL_G0,
					   1U, 1U };
	struct be_mvp_gstage_desc bad;
	struct be_mvp_gstage_map map;
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(cases); ++index) {
		bad = (struct be_mvp_gstage_desc){ cases[index].gpa,
						   cases[index].hpa,
						   cases[index].size,
						   cases[index].pool_pa, 1U,
						   1U };
		memset(pool, 0xa5, sizeof(pool));
		CHECK(be_mvp_gstage_build(&bad, pool, sizeof(pool)) ==
		      cases[index].error);
		/* A refused build leaves a scrubbed pool. */
		memset(expected, 0, sizeof(expected));
		CHECK(memcmp(pool, expected, sizeof(pool)) == 0);
	}
	/* A valid pool walked against another descriptor is refused. */
	CHECK(be_mvp_gstage_build(&good, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	bad = good;
	bad.size = 128U * MIB;
	CHECK(be_mvp_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_MVP_GSTAGE_MISMATCH);
	bad = good;
	bad.size = 62U * MIB;
	CHECK(be_mvp_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_MVP_GSTAGE_MISMATCH);
	bad = good;
	bad.hpa_base += 2U * MIB;
	CHECK(be_mvp_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_MVP_GSTAGE_MISMATCH);
	bad = good;
	bad.gpa_base += 2U * MIB;
	CHECK(be_mvp_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_MVP_GSTAGE_MISMATCH);
	bad = good;
	bad.pool_pa += 0x4000U;
	CHECK(be_mvp_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_MVP_GSTAGE_ROOT);
	bad = good;
	bad.pool_pa += 0x1000U;
	CHECK(be_mvp_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_MVP_GSTAGE_POOL);
	CHECK(map.hgatp == 0U && map.size == 0U && map.pool_pa == 0U);
	/* Size and null refusals; a wrong-size pool is never written. */
	memset(pool, 0xa5, sizeof(pool));
	CHECK(be_mvp_gstage_build(&good, pool, sizeof(pool) - 8U) ==
	      BE_MVP_GSTAGE_POOL);
	CHECK(pool[0] == 0xa5U && pool[sizeof(pool) - 1U] == 0xa5U);
	CHECK(be_mvp_gstage_build(&good, pool, sizeof(pool) + 8U) ==
	      BE_MVP_GSTAGE_POOL);
	CHECK(be_mvp_gstage_build(&good, (be_u8 *)0, sizeof(pool)) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(be_mvp_gstage_build((const struct be_mvp_gstage_desc *)0, pool,
				 sizeof(pool)) == BE_MVP_GSTAGE_NULL);
	CHECK(pool[0] == 0U && pool[sizeof(pool) - 1U] == 0U);
	CHECK(be_mvp_gstage_walk(&good, pool, sizeof(pool),
				(struct be_mvp_gstage_map *)0) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(be_mvp_gstage_walk(&good, (const be_u8 *)0, sizeof(pool), &map) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(be_mvp_gstage_walk((const struct be_mvp_gstage_desc *)0, pool,
				sizeof(pool), &map) == BE_MVP_GSTAGE_NULL);
	CHECK(be_mvp_gstage_walk(&good, pool, sizeof(pool) + 8U, &map) ==
	      BE_MVP_GSTAGE_POOL);
	/* A window that ends where the pool starts is accepted. */
	bad = (struct be_mvp_gstage_desc){ GPA_G0, BE_U64_C(0x101e00000),
					   2U * MIB, BE_U64_C(0x102000000),
					   1U, 1U };
	CHECK(be_mvp_gstage_build(&bad, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk(&bad, pool, sizeof(pool), &map) ==
	      BE_MVP_GSTAGE_OK);
	/* An empty pool has no root pointer; a root alone has no leaves. */
	memset(pool, 0, sizeof(pool));
	CHECK(be_mvp_gstage_walk(&good, pool, sizeof(pool), &map) ==
	      BE_MVP_GSTAGE_ROOT);
	CHECK(be_mvp_gstage_build(&good, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	memset(pool + 0x4000U, 0, 0x1000U);
	CHECK(be_mvp_gstage_walk(&good, pool, sizeof(pool), &map) ==
	      BE_MVP_GSTAGE_L1);
}

/*
 * No channel: both builder entries write M0's bytes, the model's, and
 * refuse M0's descriptors alike; both walker entries derive M0's map and
 * no leaf; and with a record that declares none, the channel check passes
 * the two MVP roots. A declared page that a root does not map is no
 * pointer: the walker finds no leaf, and the channel check refuses that
 * root.
 */
static void test_no_channel(void)
{
	static const struct be_mvp_gstage_root_page none = { 0U, 0U, 0U, 0U };
	static const struct be_mvp_gstage_channel no_record = {
		0U, 0U, 0U, 0U, 0U, 0U, 0U
	};
	static const struct be_mvp_gstage_desc windows[] = {
		{ GPA_G0, HPA_G0, 64U * MIB, POOL_G0, 1U, 1U },
		{ GPA_G0, HPA_G1, 64U * MIB, POOL_G1, 2U, 2U },
		{ GPA_G0, HPA_G0, 128U * MIB, POOL_G0, 1U, 1U },
		{ GPA_G0, HPA_OTHER, 64U * MIB, POOL_G0, 0x3fffU, 7U },
		{ BE_U64_C(0xbfe00000), HPA_G0, 2U * MIB, POOL_G0, 0U, 9U },
		{ GPA_G0, HPA_G0, 1024U * MIB, POOL_G0, 2U, ALL_ONES },
		{ BE_U64_C(0x40000000), HPA_G0, 64U * MIB,
		  BE_U64_C(0x108000000), 1U, 0U },
		/* Refused alike: a misaligned GPA, the window over its pool,
		 * and a VMID of 2^14. */
		{ GPA_G0 + MIB, HPA_G0, 64U * MIB, POOL_G0, 1U, 1U },
		{ GPA_G0, BE_U64_C(0x102000000), 64U * MIB, POOL_G0, 1U, 1U },
		{ GPA_G0, HPA_G0, 64U * MIB, POOL_G0, 0x4000U, 1U },
	};
	struct be_mvp_gstage_map maps[2];
	struct be_mvp_gstage_map plain;
	struct be_mvp_gstage_leaf leaves[2];
	struct be_mvp_gstage_channel record = mvp_record(0U);
	struct be_mvp_gstage_refusal refusal;
	struct be_mvp_gstage_desc desc;
	struct be_mvp_gstage_root_page page;
	enum be_mvp_gstage_error error;
	be_size index;
	be_u64 domain;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(windows); ++index) {
		memset(pool, 0xa5, sizeof(pool));
		error = be_mvp_gstage_build(&windows[index], pool,
					    sizeof(pool));
		memset(scratch, 0x5a, sizeof(scratch));
		CHECK(be_mvp_gstage_build_channel(&windows[index], &none,
						  scratch, sizeof(scratch)) ==
		      error);
		CHECK(memcmp(pool, scratch, sizeof(pool)) == 0);
		if (error != BE_MVP_GSTAGE_OK) {
			CHECK(pool[0] == 0U && pool[sizeof(pool) - 1U] == 0U);
			continue;
		}
		model(&windows[index]);
		CHECK(memcmp(pool, expected, sizeof(pool)) == 0);
		CHECK(be_mvp_gstage_walk(&windows[index], pool, sizeof(pool),
					 &plain) == BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk_channel(&windows[index], &none, pool,
						 sizeof(pool), &maps[0],
						 &leaves[0]) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(memcmp(&plain, &maps[0], sizeof(plain)) == 0);
		CHECK(leaf_empty(&leaves[0]));
	}
	/* The two MVP roots without a channel, under a record without one. */
	for (domain = 0U; domain < 2U; ++domain) {
		desc = mvp_desc(domain);
		CHECK(be_mvp_gstage_build(&desc, pools[domain],
					  sizeof(pools[domain])) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk_channel(&desc, &none, pools[domain],
						 sizeof(pools[domain]),
						 &maps[domain],
						 &leaves[domain]) ==
		      BE_MVP_GSTAGE_OK);
	}
	CHECK(be_mvp_gstage_pair_check(&maps[0], &maps[1]) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_channel_check(maps, leaves, &no_record, &refusal) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(refusal_is(&refusal, BE_MVP_DOMAINS, 0U, 0U, 0U));
	/* G1's root against the page it does not map, beside G0's leaf. */
	desc = mvp_desc(1U);
	page = mvp_page(RIGHT_R);
	CHECK(be_mvp_gstage_walk_channel(&desc, &page, pools[1],
					 sizeof(pools[1]), &maps[1],
					 &leaves[1]) == BE_MVP_GSTAGE_OK);
	CHECK(leaf_empty(&leaves[1]));
	desc = mvp_desc(0U);
	page = mvp_page(RIGHT_RW);
	CHECK(be_mvp_gstage_build_channel(&desc, &page, pools[0],
					  sizeof(pools[0])) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk_channel(&desc, &page, pools[0],
					 sizeof(pools[0]), &maps[0],
					 &leaves[0]) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_channel_check(maps, leaves, &record, &refusal) ==
	      BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 1U, 2U, 0U, LEAF_READER));
}

/*
 * The plan's channel (Q1, "G-stage and VMIDs") in the layout's back-to-back
 * pools: each root M0's, plus level-1 entry 32 pointing to its level-0
 * page, 0x1_0203_9000 (0x4080e401) for G0 and 0x1_0204_1000 (0x40810401)
 * for G1, whose entry 0 is the one leaf onto 0x1_1800_0000, the writer's
 * 0x460000d7 and the reader's 0x46000053; the walked roots pass the channel
 * check against Instance 2's record, and the record with the roles the
 * other way round only when the roots are built that way round.
 */
static void test_channel_roots(void)
{
	static const struct {
		be_u64 rights, root_pte, pointer, leaf, l0_pa;
	} guests[] = {
		{ RIGHT_RW, BE_U64_C(0x4080e001), POINTER_G0, LEAF_WRITER,
		  L0_G0 },
		{ RIGHT_R, BE_U64_C(0x40810001), POINTER_G1, LEAF_READER,
		  L0_G1 },
	};
	static be_u8 both[BE_MVP_POOL_BYTES];
	struct be_mvp_gstage_map maps[2];
	struct be_mvp_gstage_leaf leaves[2];
	struct be_mvp_gstage_channel record = mvp_record(0U);
	struct be_mvp_gstage_refusal refusal;
	be_u64 guest;
	be_u64 offset;
	be_u64 stray;

	SCENARIO();
	memset(both, 0xa5, sizeof(both));
	for (guest = 0U; guest < 2U; ++guest) {
		struct be_mvp_gstage_desc desc = mvp_desc(guest);
		struct be_mvp_gstage_root_page page =
			mvp_page(guests[guest].rights);
		be_u8 *own = both + (desc.pool_pa - BE_MVP_POOL_HPA);

		CHECK(be_mvp_gstage_build_channel(&desc, &page, own,
						  BE_MVP_GUEST_POOL_BYTES) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk_channel(&desc, &page, own,
						 BE_MVP_GUEST_POOL_BYTES,
						 &maps[guest],
						 &leaves[guest]) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(maps[guest].hgatp ==
		      (guest == 0U ? BE_MVP_G0_HGATP : BE_MVP_G1_HGATP));
		CHECK(maps[guest].hpa_base == desc.hpa_base &&
		      maps[guest].leaves == 32U);
		/* Root index 2 and level-1 entries 0-31 are M0's. */
		CHECK(get_le64(own + 16U) == guests[guest].root_pte);
		CHECK(get_le64(own + L1_AT(31U)) ==
		      (0xdfU | WINDOW_CW |
		       (((desc.hpa_base + 62U * MIB) >> 12) << 10)));
		CHECK(get_le64(own + L1_AT(32U)) == guests[guest].pointer);
		CHECK(get_le64(own + L1_AT(33U)) == 0U);
		/* The leaf at entry 0, then nothing to the pool's end. */
		CHECK(get_le64(own + L0_AT(0U)) == guests[guest].leaf);
		stray = 0U;
		for (offset = L0_AT(1U); offset < BE_MVP_GUEST_POOL_BYTES;
		     ++offset)
			stray |= own[offset];
		CHECK(stray == 0U);
		CHECK(leaves[guest].gpa == GPA_CHANNEL &&
		      leaves[guest].hpa == HPA_CHANNEL &&
		      leaves[guest].bytes == PAGE &&
		      leaves[guest].pte == guests[guest].leaf &&
		      leaves[guest].l0_pa == guests[guest].l0_pa);
	}
	CHECK(be_mvp_gstage_channel_check(maps, leaves, &record, &refusal) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(refusal_is(&refusal, BE_MVP_DOMAINS, 0U, 0U, 0U));
	CHECK(be_mvp_gstage_pair_check(&maps[0], &maps[1]) == BE_MVP_GSTAGE_OK);
	/* The roles the other way round: G0's leaf is no reader's. */
	record = mvp_record(1U);
	CHECK(be_mvp_gstage_channel_check(maps, leaves, &record, &refusal) ==
	      BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 0U, 1U, LEAF_WRITER, LEAF_READER));
	build_pair(1U, maps, leaves);
	CHECK(leaves[0].pte == LEAF_READER && leaves[1].pte == LEAF_WRITER);
	CHECK(be_mvp_gstage_channel_check(maps, leaves, &record, &refusal) ==
	      BE_MVP_GSTAGE_OK);
}

/*
 * One root with a channel page: the model's bytes, the walked leaf, M0's
 * window, DBCN's translation of the window alone, and M0's walker
 * refusing the pointer.
 */
static void check_channel_root(const struct be_mvp_gstage_desc *desc,
			       const struct be_mvp_gstage_root_page *page)
{
	struct be_mvp_gstage_map map;
	struct be_mvp_gstage_map plain;
	struct be_mvp_gstage_leaf leaf;
	be_u64 out = 7U;

	SCENARIO();
	memset(pool, 0xa5, sizeof(pool));
	CHECK(be_mvp_gstage_build_channel(desc, page, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	model_page(desc, page);
	CHECK(memcmp(pool, expected, sizeof(pool)) == 0);
	CHECK(be_mvp_gstage_walk_channel(desc, page, pool, sizeof(pool), &map,
					 &leaf) == BE_MVP_GSTAGE_OK);
	CHECK(leaf.gpa == page->gpa && leaf.hpa == page->hpa &&
	      leaf.bytes == PAGE && leaf.l0_pa == desc->pool_pa + 0x5000U);
	CHECK(leaf.pte ==
	      get_le64(expected + L0_AT((page->gpa % (2U * MIB)) / PAGE)));
	CHECK(be_mvp_gstage_build(desc, scratch, sizeof(scratch)) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk(desc, scratch, sizeof(scratch), &plain) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(memcmp(&map, &plain, sizeof(map)) == 0);
	CHECK(be_mvp_gstage_translate(&map, page->gpa, 1U, &out) == 0 &&
	      out == 7U);
	CHECK(be_mvp_gstage_walk(desc, pool, sizeof(pool), &plain) ==
	      BE_MVP_GSTAGE_L1);
	CHECK(map_empty(&plain));
}

/* Pages at the edges of their rules, each accepted. */
static void test_channel_edges(void)
{
	static const struct {
		be_u64 gpa_base, size, gpa, hpa, rights;
	} cases[] = {
		/* The plan's page, read-write and read-only. */
		{ GPA_G0, 64U * MIB, GPA_CHANNEL, HPA_CHANNEL, RIGHT_RW },
		{ GPA_G0, 64U * MIB, GPA_CHANNEL, HPA_CHANNEL, RIGHT_R },
		/* The root entry's last page; a page after 128 MiB. */
		{ GPA_G0, 64U * MIB, BE_U64_C(0xbffff000), HPA_CHANNEL,
		  RIGHT_R },
		{ GPA_G0, 128U * MIB, BE_U64_C(0x88000000), HPA_CHANNEL,
		  RIGHT_RW },
		/* Below the window in its root entry, on level-1 entry 0. */
		{ GPA_G0 + 4U * MIB, 64U * MIB, GPA_G0, HPA_CHANNEL, RIGHT_R },
		{ GPA_G0 + 4U * MIB, 64U * MIB, GPA_G0 + 2U * MIB - PAGE,
		  HPA_CHANNEL, RIGHT_RW },
		/* Directly beside the window's HPA range and the pool. */
		{ GPA_G0, 64U * MIB, GPA_CHANNEL, HPA_G0 - PAGE, RIGHT_R },
		{ GPA_G0, 64U * MIB, GPA_CHANNEL, HPA_G0 + 64U * MIB, RIGHT_R },
		{ GPA_G0, 64U * MIB, GPA_CHANNEL, POOL_G0 - PAGE, RIGHT_R },
		{ GPA_G0, 64U * MIB, GPA_CHANNEL, POOL_G0 + 0x8000U, RIGHT_R },
		/* The last page below 2^56. */
		{ GPA_G0, 64U * MIB, GPA_CHANNEL,
		  (BE_U64_C(1) << 56) - PAGE, RIGHT_RW },
		/* In the first GiB, at GPA 0, the entry an all-zero page
		 * names, which a walk without a page must still refuse. */
		{ 2U * MIB, 64U * MIB, 0U, HPA_CHANNEL, RIGHT_R },
	};
	struct be_mvp_gstage_desc other = { BE_U64_C(0x40000000), HPA_G1,
					    64U * MIB, BE_U64_C(0x108000000),
					    2U, 2U };
	struct be_mvp_gstage_root_page last = {
		BE_U64_C(0x7ffff000), HPA_CHANNEL, PAGE, RIGHT_R
	};
	be_size index;

	for (index = 0U; index < BE_ARRAY_SIZE(cases); ++index) {
		struct be_mvp_gstage_desc desc = { cases[index].gpa_base,
						   HPA_G0, cases[index].size,
						   POOL_G0, 1U, 1U };
		struct be_mvp_gstage_root_page page = { cases[index].gpa,
						   cases[index].hpa, PAGE,
						   cases[index].rights };

		check_channel_root(&desc, &page);
	}
	/* Another root entry, another pool: its level-1 table's last page. */
	check_channel_root(&other, &last);
}

/*
 * Every page rule, refused by the builder, which leaves the pool scrubbed,
 * and by the walker on a valid channel root; and absent pages and outputs.
 */
static void test_page_refusals(void)
{
	static const struct be_mvp_gstage_root_page cases[] = {
		/* Execute: with read, read and write, alone, with write. */
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, RIGHT_R | RIGHT_X },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, RIGHT_RW | RIGHT_X },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, RIGHT_X },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, RIGHT_W | RIGHT_X },
		/* Neither read; write without read; unknown rights. */
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, 0U },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, RIGHT_W },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, RIGHT_R | 8U },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE,
		  RIGHT_R | (BE_U64_C(1) << 63) },
		/* Not exactly 4 KiB. */
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE / 2U, RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL, 2U * PAGE, RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE + 1U, RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL, ALL_ONES, RIGHT_R },
		/* A misaligned GPA or HPA. */
		{ GPA_CHANNEL + PAGE / 2U, HPA_CHANNEL, PAGE, RIGHT_R },
		{ GPA_CHANNEL + 8U, HPA_CHANNEL, PAGE, RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL + PAGE / 2U, PAGE, RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL + 1U, PAGE, RIGHT_R },
		/* Outside the window's root entry, below, above, and beyond
		 * Sv39x4's 2^41. */
		{ GPA_G0 - PAGE, HPA_CHANNEL, PAGE, RIGHT_R },
		{ BE_U64_C(0xc0000000), HPA_CHANNEL, PAGE, RIGHT_R },
		{ BE_U64_C(1) << 41, HPA_CHANNEL, PAGE, RIGHT_R },
		{ ALL_ONES - 0xfffU, HPA_CHANNEL, PAGE, RIGHT_R },
		/* On a level-1 entry of the window's: its first page, the
		 * DTB's, its last. */
		{ GPA_G0, HPA_CHANNEL, PAGE, RIGHT_R },
		{ BE_U64_C(0x83e00000), HPA_CHANNEL, PAGE, RIGHT_R },
		{ GPA_CHANNEL - PAGE, HPA_CHANNEL, PAGE, RIGHT_R },
		/* Over the window: its first page, one inside, its last. */
		{ GPA_CHANNEL, HPA_G0, PAGE, RIGHT_R },
		{ GPA_CHANNEL, HPA_G0 + 0x123000U, PAGE, RIGHT_R },
		{ GPA_CHANNEL, HPA_G0 + 64U * MIB - PAGE, PAGE, RIGHT_R },
		/* Over the pool: the root, the level-1 page, the level-0
		 * page, the last spare page. */
		{ GPA_CHANNEL, POOL_G0, PAGE, RIGHT_R },
		{ GPA_CHANNEL, POOL_G0 + 0x4000U, PAGE, RIGHT_R },
		{ GPA_CHANNEL, POOL_G0 + 0x5000U, PAGE, RIGHT_R },
		{ GPA_CHANNEL, POOL_G0 + 0x7000U, PAGE, RIGHT_R },
		/* At or above 2^56. */
		{ GPA_CHANNEL, BE_U64_C(1) << 56, PAGE, RIGHT_R },
		{ GPA_CHANNEL, ALL_ONES - 0xfffU, PAGE, RIGHT_R },
		/* No page, but a GPA, an HPA, or rights. */
		{ GPA_CHANNEL, 0U, 0U, 0U },
		{ 0U, HPA_CHANNEL, 0U, 0U },
		{ 0U, 0U, 0U, RIGHT_R },
	};
	struct be_mvp_gstage_desc desc = mvp_desc(0U);
	struct be_mvp_gstage_desc bad = mvp_desc(0U);
	struct be_mvp_gstage_root_page good = mvp_page(RIGHT_RW);
	struct be_mvp_gstage_map map;
	struct be_mvp_gstage_leaf leaf;
	be_size index;

	SCENARIO();
	memset(expected, 0, sizeof(expected));
	CHECK(be_mvp_gstage_build_channel(&desc, &good, scratch,
					  sizeof(scratch)) == BE_MVP_GSTAGE_OK);
	for (index = 0U; index < BE_ARRAY_SIZE(cases); ++index) {
		memset(pool, 0xa5, sizeof(pool));
		CHECK(be_mvp_gstage_build_channel(&desc, &cases[index], pool,
						  sizeof(pool)) ==
		      BE_MVP_GSTAGE_PAGE);
		CHECK(memcmp(pool, expected, sizeof(pool)) == 0);
		CHECK(walk_scratch(&desc, &cases[index]) == BE_MVP_GSTAGE_PAGE);
	}
	/* The descriptor's refusal comes first. */
	bad.gpa_base += MIB;
	CHECK(be_mvp_gstage_build_channel(&bad, &cases[0], pool,
					  sizeof(pool)) == BE_MVP_GSTAGE_DESC);
	/* An absent page: the pool scrubbed; absent outputs stay zero. */
	memset(pool, 0xa5, sizeof(pool));
	CHECK(be_mvp_gstage_build_channel(&desc, NO_ROOT_PAGE, pool,
					  sizeof(pool)) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(memcmp(pool, expected, sizeof(pool)) == 0);
	memset(&map, 0xa5, sizeof(map));
	memset(&leaf, 0xa5, sizeof(leaf));
	CHECK(be_mvp_gstage_walk_channel(&desc, NO_ROOT_PAGE, scratch,
					 sizeof(scratch), &map,
					 &leaf) == BE_MVP_GSTAGE_NULL);
	CHECK(map_empty(&map) && leaf_empty(&leaf));
	memset(&map, 0xa5, sizeof(map));
	CHECK(be_mvp_gstage_walk_channel(&desc, &good, scratch,
					 sizeof(scratch), &map,
					 (struct be_mvp_gstage_leaf *)0) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(map_empty(&map));
	memset(&leaf, 0xa5, sizeof(leaf));
	CHECK(be_mvp_gstage_walk_channel(&desc, &good, scratch,
					 sizeof(scratch),
					 (struct be_mvp_gstage_map *)0,
					 &leaf) == BE_MVP_GSTAGE_NULL);
	CHECK(leaf_empty(&leaf));
	CHECK(be_mvp_gstage_walk_channel(&desc, &good, scratch,
					 sizeof(scratch), &map, &leaf) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(leaf.pte == LEAF_WRITER);
}

/*
 * The walker's one new rule, on G1's read-only root: one pointer, exactly,
 * at the page's level-1 entry, to this pool's level-0 page; in that page
 * one leaf, at the page's level-0 entry, onto its HPA, V R U A with W D
 * both or neither; nothing else. It does not compare the leaf's rights
 * with the declared page's.
 */
static void test_channel_walk(void)
{
	static const be_u64 pointer_bits[] = {
		0x02U, 0x04U, 0x08U, 0x10U, 0x20U, 0x40U, 0x80U, 0x100U,
		0x200U, BE_U64_C(1) << 54, BE_U64_C(1) << 61,
		BE_U64_C(1) << 62, BE_U64_C(1) << 63,
	};
	static const be_u64 leaf_bits[] = {
		0x08U, 0x20U, 0x100U, 0x200U, BE_U64_C(1) << 54,
		BE_U64_C(1) << 60, BE_U64_C(1) << 61, BE_U64_C(1) << 62,
		BE_U64_C(1) << 63,
	};
	static const be_u64 missing_bits[] = { 0x01U, 0x02U, 0x10U, 0x40U };
	/* The root, the level-1 page, the spare page, G0's level-0 page,
	 * and the channel page itself. */
	static const be_u64 other_tables[] = {
		POOL_G1, POOL_G1 + 0x4000U, L0_G1 + PAGE, L0_G0, HPA_CHANNEL,
	};
	/* Beside the channel page, two windows, the pool, the level-0
	 * page, and page 0. */
	static const be_u64 other_pages[] = {
		HPA_CHANNEL + PAGE, HPA_CHANNEL - PAGE, HPA_G1, HPA_G0, POOL_G1,
		L0_G1, 0U,
	};
	struct be_mvp_gstage_desc desc = mvp_desc(1U);
	struct be_mvp_gstage_root_page page = mvp_page(RIGHT_R);
	struct be_mvp_gstage_root_page other;
	struct be_mvp_gstage_map map;
	struct be_mvp_gstage_leaf leaf;
	be_size index;

	SCENARIO();
	CHECK(be_mvp_gstage_build_channel(&desc, &page, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(get_le64(pool + L1_AT(32U)) == POINTER_G1 &&
	      get_le64(pool + L0_AT(0U)) == LEAF_READER);
	/* A second pointer, after the channel's or last in the table. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L1_AT(33U), POINTER_G1);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L1);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L1_AT(511U), POINTER_G1);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L1);
	/* The pointer elsewhere: entry 33, entry 511, the run's last. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L1_AT(32U), 0U);
	put_le64(scratch + L1_AT(33U), POINTER_G1);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L1);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L1_AT(32U), 0U);
	put_le64(scratch + L1_AT(511U), POINTER_G1);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L1);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L1_AT(31U), POINTER_G1);
	put_le64(scratch + L1_AT(32U), 0U);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L1);
	/* The pointer onto another table. */
	for (index = 0U; index < BE_ARRAY_SIZE(other_tables); ++index) {
		memcpy(scratch, pool, sizeof(pool));
		put_le64(scratch + L1_AT(32U),
			 1U | ((other_tables[index] >> 12) << 10));
		CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L1);
	}
	/* The pointer with another bit: R W X U G A D, RSW, reserved, PBMT,
	 * N; or without V. */
	for (index = 0U; index < BE_ARRAY_SIZE(pointer_bits); ++index) {
		memcpy(scratch, pool, sizeof(pool));
		put_le64(scratch + L1_AT(32U),
			 POINTER_G1 | pointer_bits[index]);
		CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L1);
	}
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L1_AT(32U), POINTER_G1 & ~BE_U64_C(1));
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L1);
	/* The root moved to slot 3, no longer the page's root entry. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + 24U, get_le64(scratch + 16U));
	put_le64(scratch + 16U, 0U);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L1);
	/* A second leaf: the channel page again, or the next page. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(1U), LEAF_READER);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(511U), LEAF_READER + 0x400U);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	/* The leaf at another entry: GPA 0x8400_1000, or 0x841f_f000. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(0U), 0U);
	put_le64(scratch + L0_AT(1U), LEAF_READER);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(0U), 0U);
	put_le64(scratch + L0_AT(511U), LEAF_READER);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	/* The leaf with another bit: X, G, RSW, reserved, PBMT, N. */
	for (index = 0U; index < BE_ARRAY_SIZE(leaf_bits); ++index) {
		memcpy(scratch, pool, sizeof(pool));
		put_le64(scratch + L0_AT(0U), LEAF_READER | leaf_bits[index]);
		CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	}
	/* W without D and D without W, from the reader's and the writer's. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(0U), LEAF_READER | 0x04U);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(0U), LEAF_READER | 0x80U);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(0U), LEAF_WRITER & ~BE_U64_C(0x80));
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(0U), LEAF_WRITER & ~BE_U64_C(0x04));
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	/* Without V, R, U, or A. */
	for (index = 0U; index < BE_ARRAY_SIZE(missing_bits); ++index) {
		memcpy(scratch, pool, sizeof(pool));
		put_le64(scratch + L0_AT(0U),
			 LEAF_READER & ~missing_bits[index]);
		CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	}
	/* Onto another page. */
	for (index = 0U; index < BE_ARRAY_SIZE(other_pages); ++index) {
		memcpy(scratch, pool, sizeof(pool));
		put_le64(scratch + L0_AT(0U),
			 0x53U | ((other_pages[index] >> 12) << 10));
		CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	}
	/* The pointer to an empty page; the leaf without the pointer. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(0U), 0U);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L1_AT(32U), 0U);
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_SPARE);
	/* A nonzero byte after the level-0 page. */
	memcpy(scratch, pool, sizeof(pool));
	scratch[0x6000U] = 0x01U;
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_SPARE);
	memcpy(scratch, pool, sizeof(pool));
	scratch[0x7fffU] = 0x80U;
	CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_SPARE);
	/* The page declared one page up, one level-1 entry up, onto the
	 * next page, or not at all. */
	memcpy(scratch, pool, sizeof(pool));
	other = page;
	other.gpa += PAGE;
	CHECK(walk_scratch(&desc, &other) == BE_MVP_GSTAGE_L0);
	other = page;
	other.gpa += 2U * MIB;
	CHECK(walk_scratch(&desc, &other) == BE_MVP_GSTAGE_L1);
	other = page;
	other.hpa += PAGE;
	CHECK(walk_scratch(&desc, &other) == BE_MVP_GSTAGE_L0);
	other = (struct be_mvp_gstage_root_page){ 0U, 0U, 0U, 0U };
	CHECK(walk_scratch(&desc, &other) == BE_MVP_GSTAGE_L1);
	CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch), &map) ==
	      BE_MVP_GSTAGE_L1);
	CHECK(map_empty(&map));
	/* No rights compared: the reader's leaf declared read-write, and the
	 * writer's leaf, as a defective builder writes it, declared
	 * read-only. */
	other = page;
	other.rights = RIGHT_RW;
	CHECK(be_mvp_gstage_walk_channel(&desc, &other, scratch,
					 sizeof(scratch), &map, &leaf) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(leaf.pte == LEAF_READER);
	put_le64(scratch + L0_AT(0U), LEAF_WRITER);
	CHECK(be_mvp_gstage_walk_channel(&desc, &page, scratch,
					 sizeof(scratch), &map, &leaf) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(leaf.pte == LEAF_WRITER);
}

/*
 * Every bit of every nonzero entry of a channel root, and nonzero bytes in
 * its zero regions, the level-0 page's included.
 */
static void check_channel_mutations(be_u64 domain, be_u64 rights)
{
	static const be_u64 targeted[] = {
		0x0U, 0x18U, 0x4108U, 0x4ff8U, 0x5008U, 0x5ff8U, 0x5fffU,
		0x6000U, 0x7ff8U, 0x7fffU,
	};
	struct be_mvp_gstage_desc desc = mvp_desc(domain);
	struct be_mvp_gstage_root_page page = mvp_page(rights);
	be_u64 offset;
	be_size index;
	unsigned int bit;
	unsigned long flips = 0U;

	SCENARIO();
	CHECK(be_mvp_gstage_build_channel(&desc, &page, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	for (offset = 0U; offset < BE_MVP_GSTAGE_POOL_BYTES; offset += 8U) {
		if (get_le64(pool + offset) == 0U)
			continue;
		for (bit = 0U; bit < 64U; ++bit) {
			memcpy(scratch, pool, sizeof(pool));
			scratch[offset + bit / 8U] ^= (be_u8)(1U << (bit % 8U));
			CHECK(walk_scratch(&desc, &page) != BE_MVP_GSTAGE_OK);
			++flips;
		}
	}
	for (offset = 0U; offset < BE_MVP_GSTAGE_POOL_BYTES; offset += 61U) {
		if (pool[offset] != 0U)
			continue;
		memcpy(scratch, pool, sizeof(pool));
		scratch[offset] = 0x01U;
		CHECK(walk_scratch(&desc, &page) != BE_MVP_GSTAGE_OK);
		++flips;
	}
	for (index = 0U; index < BE_ARRAY_SIZE(targeted); ++index) {
		if (pool[targeted[index]] != 0U)
			continue;
		memcpy(scratch, pool, sizeof(pool));
		scratch[targeted[index]] = 0x80U;
		CHECK(walk_scratch(&desc, &page) != BE_MVP_GSTAGE_OK);
		++flips;
	}
	/* The root pointer, 32 leaves, the level-1 pointer, and the leaf. */
	CHECK(flips > 35U * 64U);
}

/*
 * The channel check's every refusal, naming the root it refuses, or none
 * for M0's pair rules and the record's own rules, and its absent
 * arguments.
 */
static void test_channel_check(void)
{
	static const struct be_mvp_gstage_channel records[] = {
		/* Not one 4 KiB-aligned 4 KiB page below 2^41 and 2^56. */
		{ GPA_CHANNEL, HPA_CHANNEL, 2U * PAGE, 0U, 1U, RIGHT_RW,
		  RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE / 2U, 0U, 1U, RIGHT_RW,
		  RIGHT_R },
		{ GPA_CHANNEL + 8U, HPA_CHANNEL, PAGE, 0U, 1U, RIGHT_RW,
		  RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL + 8U, PAGE, 0U, 1U, RIGHT_RW,
		  RIGHT_R },
		{ BE_U64_C(1) << 41, HPA_CHANNEL, PAGE, 0U, 1U, RIGHT_RW,
		  RIGHT_R },
		{ GPA_CHANNEL, BE_U64_C(1) << 56, PAGE, 0U, 1U, RIGHT_RW,
		  RIGHT_R },
		/* Endpoints that are not the two domains. */
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, 0U, 0U, RIGHT_RW, RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, 1U, 1U, RIGHT_RW, RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, 2U, 1U, RIGHT_RW, RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, 0U, 2U, RIGHT_RW, RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, ALL_ONES, 1U, RIGHT_RW,
		  RIGHT_R },
		/* A writer that cannot write, a reader that can, execute,
		 * write without read, and no read. */
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, 0U, 1U, RIGHT_R, RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, 0U, 1U, RIGHT_RW, RIGHT_RW },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, 0U, 1U, RIGHT_RW | RIGHT_X,
		  RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, 0U, 1U, RIGHT_RW,
		  RIGHT_R | RIGHT_X },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, 0U, 1U, RIGHT_W, RIGHT_R },
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, 0U, 1U, RIGHT_RW, 0U },
		/* No channel, but a field. */
		{ GPA_CHANNEL, 0U, 0U, 0U, 0U, 0U, 0U },
		{ 0U, HPA_CHANNEL, 0U, 0U, 0U, 0U, 0U },
		{ 0U, 0U, 0U, 0U, 1U, 0U, 0U },
		{ 0U, 0U, 0U, 0U, 0U, RIGHT_RW, 0U },
		{ 0U, 0U, 0U, 0U, 0U, 0U, RIGHT_R },
	};
	static const struct be_mvp_gstage_channel no_record = {
		0U, 0U, 0U, 0U, 0U, 0U, 0U
	};
	struct be_mvp_gstage_map maps[2];
	struct be_mvp_gstage_map bad_maps[2];
	struct be_mvp_gstage_leaf leaves[2];
	struct be_mvp_gstage_leaf bad_leaves[2];
	struct be_mvp_gstage_channel record = mvp_record(0U);
	struct be_mvp_gstage_channel bad;
	struct be_mvp_gstage_refusal refusal;
	struct be_mvp_gstage_desc desc;
	struct be_mvp_gstage_root_page page;
	be_size index;
	be_u64 domain;

	SCENARIO();
	build_pair(0U, maps, leaves);
	CHECK(be_mvp_gstage_channel_check(maps, leaves, &record, &refusal) ==
	      BE_MVP_GSTAGE_OK);
	/* The writer's leaf without W and D, as walked from G0's pool. */
	memcpy(bad_maps, maps, sizeof(maps));
	memcpy(bad_leaves, leaves, sizeof(leaves));
	memcpy(scratch, pools[0], sizeof(scratch));
	put_le64(scratch + L0_AT(0U), LEAF_READER);
	desc = mvp_desc(0U);
	page = mvp_page(RIGHT_RW);
	CHECK(be_mvp_gstage_walk_channel(&desc, &page, scratch,
					 sizeof(scratch), &bad_maps[0],
					 &bad_leaves[0]) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_channel_check(bad_maps, bad_leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 0U, 1U, LEAF_READER, LEAF_WRITER));
	/* G1's leaf missing: its root built without the page. */
	memcpy(bad_maps, maps, sizeof(maps));
	memcpy(bad_leaves, leaves, sizeof(leaves));
	desc = mvp_desc(1U);
	page = mvp_page(RIGHT_R);
	CHECK(be_mvp_gstage_build(&desc, scratch, sizeof(scratch)) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk_channel(&desc, &page, scratch,
					 sizeof(scratch), &bad_maps[1],
					 &bad_leaves[1]) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_channel_check(bad_maps, bad_leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 1U, 2U, 0U, LEAF_READER));
	/* HPAs that differ: G1's leaf onto the next page. */
	page.hpa += PAGE;
	CHECK(be_mvp_gstage_build_channel(&desc, &page, scratch,
					  sizeof(scratch)) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk_channel(&desc, &page, scratch,
					 sizeof(scratch), &bad_maps[1],
					 &bad_leaves[1]) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_channel_check(bad_maps, bad_leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 1U, 2U, LEAF_READER + 0x400U, LEAF_READER));
	/* G0's leaf at another GPA than the record's: one page up. */
	memcpy(bad_maps, maps, sizeof(maps));
	memcpy(bad_leaves, leaves, sizeof(leaves));
	desc = mvp_desc(0U);
	page = mvp_page(RIGHT_RW);
	page.gpa += PAGE;
	CHECK(be_mvp_gstage_build_channel(&desc, &page, scratch,
					  sizeof(scratch)) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk_channel(&desc, &page, scratch,
					 sizeof(scratch), &bad_maps[0],
					 &bad_leaves[0]) == BE_MVP_GSTAGE_OK);
	CHECK(bad_leaves[0].gpa == GPA_CHANNEL + PAGE);
	CHECK(be_mvp_gstage_channel_check(bad_maps, bad_leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 0U, 1U, LEAF_WRITER, LEAF_WRITER));
	/* The record at another GPA, or onto another HPA, than both leaves. */
	bad = record;
	bad.gpa += PAGE;
	CHECK(be_mvp_gstage_channel_check(maps, leaves, &bad, &refusal) ==
	      BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 0U, 1U, LEAF_WRITER, LEAF_WRITER));
	bad = record;
	bad.hpa += PAGE;
	CHECK(be_mvp_gstage_channel_check(maps, leaves, &bad, &refusal) ==
	      BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 0U, 1U, LEAF_WRITER, LEAF_WRITER + 0x400U));
	/* A leaf of another size, or in the other root's level-0 page. */
	memcpy(bad_leaves, leaves, sizeof(leaves));
	bad_leaves[1].bytes = 2U * PAGE;
	CHECK(be_mvp_gstage_channel_check(maps, bad_leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 1U, 2U, LEAF_READER, LEAF_READER));
	memcpy(bad_leaves, leaves, sizeof(leaves));
	bad_leaves[1].l0_pa = L0_G0;
	CHECK(be_mvp_gstage_channel_check(maps, bad_leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 1U, 2U, LEAF_READER, LEAF_READER));
	/* A window over the page, which M0's rules allow: G1's moved up
	 * 2 MiB onto it, or G0's in guest-physical space. */
	memcpy(bad_maps, maps, sizeof(maps));
	bad_maps[1].hpa_base += 2U * MIB;
	CHECK(be_mvp_gstage_pair_check(&bad_maps[0], &bad_maps[1]) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_channel_check(bad_maps, leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 1U, 2U, LEAF_READER, LEAF_READER));
	memcpy(bad_maps, maps, sizeof(maps));
	bad_maps[0].gpa_base += 32U * MIB;
	CHECK(be_mvp_gstage_pair_check(&bad_maps[0], &bad_maps[1]) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_channel_check(bad_maps, leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 0U, 1U, LEAF_WRITER, LEAF_WRITER));
	/* The page over a pool, the record and both leaves agreeing: G1's
	 * spare page, or G0's level-0 page. */
	for (index = 0U; index < 2U; ++index) {
		be_u64 hpa = index == 0U ? POOL_G1 + 0x6000U : L0_G0;

		bad = record;
		bad.hpa = hpa;
		memcpy(bad_leaves, leaves, sizeof(leaves));
		for (domain = 0U; domain < 2U; ++domain) {
			bad_leaves[domain].hpa = hpa;
			bad_leaves[domain].pte =
				(leaves[domain].pte & 0x3ffU) |
				((hpa >> 12) << 10);
		}
		CHECK(be_mvp_gstage_channel_check(maps, bad_leaves, &bad,
						  &refusal) ==
		      BE_MVP_GSTAGE_CHANNEL);
		CHECK(refusal_is(&refusal, 1U - index, 2U - index,
				 bad_leaves[1U - index].pte,
				 bad_leaves[1U - index].pte));
	}
	/* No channel declared: G0's leaf refused, or G1's alone, or a leaf
	 * with any one field. */
	CHECK(be_mvp_gstage_channel_check(maps, leaves, &no_record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 0U, 1U, LEAF_WRITER, 0U));
	memcpy(bad_leaves, leaves, sizeof(leaves));
	bad_leaves[0] = (struct be_mvp_gstage_leaf){ 0U, 0U, 0U, 0U, 0U };
	CHECK(be_mvp_gstage_channel_check(maps, bad_leaves, &no_record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 1U, 2U, LEAF_READER, 0U));
	bad_leaves[1] = bad_leaves[0];
	CHECK(be_mvp_gstage_channel_check(maps, bad_leaves, &no_record,
					  &refusal) == BE_MVP_GSTAGE_OK);
	for (index = 0U; index < 5U; ++index) {
		be_u64 *field = index == 0U ? &bad_leaves[0].gpa :
				index == 1U ? &bad_leaves[0].hpa :
				index == 2U ? &bad_leaves[0].bytes :
				index == 3U ? &bad_leaves[0].pte :
					      &bad_leaves[0].l0_pa;

		*field = PAGE;
		CHECK(be_mvp_gstage_channel_check(maps, bad_leaves, &no_record,
						  &refusal) ==
		      BE_MVP_GSTAGE_CHANNEL);
		CHECK(refusal.domain == 0U && refusal.hart == 1U);
		*field = 0U;
	}
	/* Records that break a rule name no root. */
	for (index = 0U; index < BE_ARRAY_SIZE(records); ++index) {
		CHECK(be_mvp_gstage_channel_check(maps, leaves, &records[index],
						  &refusal) ==
		      BE_MVP_GSTAGE_CHANNEL);
		CHECK(refusal_is(&refusal, BE_MVP_DOMAINS, 0U, 0U, 0U));
	}
	/* M0's pair rules first: equal VMIDs, the control hart, windows
	 * that share 2 MiB, an unwalked map. */
	memcpy(bad_maps, maps, sizeof(maps));
	bad_maps[1].vmid = bad_maps[0].vmid;
	CHECK(be_mvp_gstage_channel_check(bad_maps, leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_PAIR);
	CHECK(refusal_is(&refusal, BE_MVP_DOMAINS, 0U, 0U, 0U));
	memcpy(bad_maps, maps, sizeof(maps));
	bad_maps[1].hart = BE_MVP_CONTROL_HART;
	CHECK(be_mvp_gstage_channel_check(bad_maps, leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_PAIR);
	memcpy(bad_maps, maps, sizeof(maps));
	bad_maps[1].hpa_base -= 2U * MIB;
	CHECK(be_mvp_gstage_channel_check(bad_maps, leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_PAIR);
	memcpy(bad_maps, maps, sizeof(maps));
	memset(&bad_maps[1], 0, sizeof(bad_maps[1]));
	CHECK(be_mvp_gstage_channel_check(bad_maps, leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_PAIR);
	/* Absent arguments; the refusal is reset first. */
	CHECK(be_mvp_gstage_channel_check(maps, leaves, &record,
					  (struct be_mvp_gstage_refusal *)0) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(be_mvp_gstage_channel_check(maps, leaves, &no_record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(be_mvp_gstage_channel_check((const struct be_mvp_gstage_map *)0,
					  leaves, &record, &refusal) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(refusal_is(&refusal, BE_MVP_DOMAINS, 0U, 0U, 0U));
	CHECK(be_mvp_gstage_channel_check(maps,
					  (const struct be_mvp_gstage_leaf *)0,
					  &record, &refusal) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(be_mvp_gstage_channel_check(
		      maps, leaves, (const struct be_mvp_gstage_channel *)0,
		      &refusal) == BE_MVP_GSTAGE_NULL);
}

/*
 * The plan's host mutations (planning/mvp-m1-plan.md, "Mutations"), each
 * refused: a level-0 page holding a second leaf, by the walker's rule in
 * either root; the reader's leaf with W, the reader-write image's defect,
 * which the walker accepts and the channel check refuses with the plan's
 * DETAIL values; and a second page both roots map, through their windows,
 * through both leaves onto one undeclared page, or through one leaf onto a
 * page of the other root's window.
 */
static void test_mutations(void)
{
	struct be_mvp_gstage_map maps[2];
	struct be_mvp_gstage_map bad_maps[2];
	struct be_mvp_gstage_leaf leaves[2];
	struct be_mvp_gstage_leaf bad_leaves[2];
	struct be_mvp_gstage_channel record = mvp_record(0U);
	struct be_mvp_gstage_channel bad;
	struct be_mvp_gstage_refusal refusal;
	struct be_mvp_gstage_desc desc;
	struct be_mvp_gstage_root_page page;
	be_u64 domain;

	SCENARIO();
	build_pair(0U, maps, leaves);
	/* A second leaf: onto the next page, or onto the channel page. */
	for (domain = 0U; domain < 2U; ++domain) {
		desc = mvp_desc(domain);
		page = mvp_page(domain == 0U ? RIGHT_RW : RIGHT_R);
		memcpy(scratch, pools[domain], sizeof(scratch));
		put_le64(scratch + L0_AT(1U), leaves[domain].pte + 0x400U);
		CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
		memcpy(scratch, pools[domain], sizeof(scratch));
		put_le64(scratch + L0_AT(1U), leaves[domain].pte);
		CHECK(walk_scratch(&desc, &page) == BE_MVP_GSTAGE_L0);
	}
	/* The reader's leaf with W (and D). */
	memcpy(bad_maps, maps, sizeof(maps));
	memcpy(bad_leaves, leaves, sizeof(leaves));
	desc = mvp_desc(1U);
	page = mvp_page(RIGHT_R);
	memcpy(scratch, pools[1], sizeof(scratch));
	put_le64(scratch + L0_AT(0U), get_le64(scratch + L0_AT(0U)) | 0x84U);
	CHECK(be_mvp_gstage_walk_channel(&desc, &page, scratch,
					 sizeof(scratch), &bad_maps[1],
					 &bad_leaves[1]) == BE_MVP_GSTAGE_OK);
	CHECK(bad_leaves[1].pte == BE_U64_C(0x460000d7));
	CHECK(be_mvp_gstage_channel_check(bad_maps, bad_leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 1U, 2U, BE_U64_C(0x460000d7),
			 BE_U64_C(0x46000053)));
	/* A second page both roots map: through windows sharing 2 MiB. */
	memcpy(bad_maps, maps, sizeof(maps));
	bad_maps[1].hpa_base = maps[0].hpa_base + 62U * MIB;
	CHECK(be_mvp_gstage_channel_check(bad_maps, leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_PAIR);
	/* Through both leaves onto the next page, the record unchanged. */
	for (domain = 0U; domain < 2U; ++domain) {
		desc = mvp_desc(domain);
		page = mvp_page(domain == 0U ? RIGHT_RW : RIGHT_R);
		page.hpa += PAGE;
		CHECK(be_mvp_gstage_build_channel(&desc, &page, pools[domain],
						  sizeof(pools[domain])) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk_channel(&desc, &page, pools[domain],
						 sizeof(pools[domain]),
						 &bad_maps[domain],
						 &bad_leaves[domain]) ==
		      BE_MVP_GSTAGE_OK);
	}
	CHECK(bad_leaves[0].hpa == HPA_CHANNEL + PAGE &&
	      bad_leaves[1].hpa == HPA_CHANNEL + PAGE);
	CHECK(be_mvp_gstage_channel_check(bad_maps, bad_leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 0U, 1U, LEAF_WRITER + 0x400U, LEAF_WRITER));
	/* Through G0's leaf onto the first page of G1's window. */
	memcpy(bad_maps, maps, sizeof(maps));
	memcpy(bad_leaves, leaves, sizeof(leaves));
	desc = mvp_desc(0U);
	page = mvp_page(RIGHT_RW);
	page.hpa = HPA_G1;
	CHECK(be_mvp_gstage_build_channel(&desc, &page, scratch,
					  sizeof(scratch)) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk_channel(&desc, &page, scratch,
					 sizeof(scratch), &bad_maps[0],
					 &bad_leaves[0]) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_channel_check(bad_maps, bad_leaves, &record,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 0U, 1U, 0xd7U | ((HPA_G1 >> 12) << 10),
			 LEAF_WRITER));
	/* ... and with the record and G1's leaf there too, G1's window is
	 * over the page. */
	bad = record;
	bad.hpa = HPA_G1;
	bad_leaves[1].hpa = HPA_G1;
	bad_leaves[1].pte = 0x53U | ((HPA_G1 >> 12) << 10);
	CHECK(be_mvp_gstage_channel_check(bad_maps, bad_leaves, &bad,
					  &refusal) == BE_MVP_GSTAGE_CHANNEL);
	CHECK(refusal_is(&refusal, 1U, 2U, bad_leaves[1].pte,
			 bad_leaves[1].pte));
}

/*
 * The declared pages (planning/mvp-m2-plan.md, Q1 and "G-stage and
 * VMIDs"): the request page, which G0 (the host) writes and G1 (the
 * protected domain) reads; the response page, the other way round; and
 * the secret page, which G1 alone reads; their PTEs in each root.
 */
#define GPA_SECRET		(GPA_CHANNEL + 2U * PAGE)
#define HPA_SECRET		(HPA_CHANNEL + 2U * PAGE)
#define HOST_REQUEST		BE_U64_C(0x460000d7)
#define HOST_RESPONSE		BE_U64_C(0x46000453)
#define PROT_REQUEST		BE_U64_C(0x46000053)
#define PROT_RESPONSE		BE_U64_C(0x460004d7)
#define PROT_SECRET		BE_U64_C(0x46000853)
#define NO_PAGES		((const struct be_mvp_gstage_page *)0)

static struct be_mvp_gstage_leaves page_leaves[2];

/* The plan's three pages, in page order. */
static void anchor_pages(struct be_mvp_gstage_page *pages)
{
	static const struct be_mvp_gstage_page plan[3] = {
		{ GPA_CHANNEL, HPA_CHANNEL, PAGE, BE_MVP_PAGE_CHANNEL, 0U, 1U,
		  { RIGHT_RW, RIGHT_R } },
		{ GPA_CHANNEL + PAGE, HPA_CHANNEL + PAGE, PAGE,
		  BE_MVP_PAGE_CHANNEL, 1U, 0U, { RIGHT_R, RIGHT_RW } },
		{ GPA_SECRET, HPA_SECRET, PAGE, BE_MVP_PAGE_SECRET,
		  BE_MVP_PAGE_NONE, 1U, { 0U, RIGHT_R } },
	};

	memcpy(pages, plan, sizeof(plan));
}

/*
 * The model with pages: M0's window, then, when the domain has rights on
 * any page, a pointer at the pages' level-1 entry to the pool's page at
 * +0x5000, and there each such page's leaf, its flags from the plan's
 * table alone.
 */
static void model_pages(const struct be_mvp_gstage_desc *desc,
			const struct be_mvp_gstage_page *pages, be_u64 count,
			be_u64 domain)
{
	be_u64 index;
	int mapped = 0;

	model(desc);
	for (index = 0U; index < count; ++index) {
		be_u64 rights = pages[index].rights[domain];
		be_u64 flags = 0x51U;

		if (rights == 0U)
			continue;
		if ((rights & RIGHT_R) != 0U)
			flags |= 0x02U;
		if ((rights & RIGHT_W) != 0U)
			flags |= 0x84U;
		put_le64(expected + L0_AT((pages[index].gpa % (2U * MIB)) /
					  PAGE),
			 flags | ((pages[index].hpa / PAGE) << 10));
		mapped = 1;
	}
	if (mapped)
		put_le64(expected + L1_AT((pages[0].gpa % (BE_U64_C(1) << 30)) /
					  (2U * MIB)),
			 1U | (((desc->pool_pa + 0x5000U) / PAGE) << 10));
}

/* The root a page check's refusal names, its page, and its two PTEs. */
static int page_refusal_is(const struct be_mvp_gstage_refusal *refusal,
			   be_u64 page, be_u64 domain, be_u64 hart,
			   be_u64 walked_pte, be_u64 declared_pte)
{
	return refusal->page == page &&
	       refusal_is(refusal, domain, hart, walked_pte, declared_pte);
}

/* Both MVP roots with @pages, built in pools[] and walked. */
static void build_pages_pair(const struct be_mvp_gstage_page *pages,
			     be_u64 count, struct be_mvp_gstage_map *maps)
{
	be_u64 domain;

	for (domain = 0U; domain < 2U; ++domain) {
		struct be_mvp_gstage_desc desc = mvp_desc(domain);

		CHECK(be_mvp_gstage_build_pages(&desc, pages, count, domain,
						pools[domain],
						sizeof(pools[domain])) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk_pages(&desc, pages, count,
					       pools[domain],
					       sizeof(pools[domain]),
					       &maps[domain],
					       &page_leaves[domain]) ==
		      BE_MVP_GSTAGE_OK);
	}
}

/* Walk scratch[] with @pages; a refused walk leaves map and leaves zero. */
static enum be_mvp_gstage_error
walk_scratch_pages(const struct be_mvp_gstage_desc *desc,
		   const struct be_mvp_gstage_page *pages, be_u64 count)
{
	struct be_mvp_gstage_map map;
	struct be_mvp_gstage_leaves leaves;
	enum be_mvp_gstage_error error;
	be_u64 index;

	error = be_mvp_gstage_walk_pages(desc, pages, count, scratch,
					 sizeof(scratch), &map, &leaves);
	if (error != BE_MVP_GSTAGE_OK) {
		CHECK(map_empty(&map));
		for (index = 0U; index < BE_MVP_PAGES_MAX; ++index)
			CHECK(leaf_empty(&leaves.page[index]));
	}
	return error;
}

/*
 * The plan's pages in the layout's back-to-back pools: each root M0's,
 * plus level-1 entry 32 pointing to its level-0 page, whose entries 0 to
 * 2 are the plan's leaves: G0's request 0x460000d7 and response
 * 0x46000453 and no secret leaf; G1's request 0x46000053, response
 * 0x460004d7, and secret 0x46000853; the walked leaves; and the page check
 * passing them.
 */
static void test_page_roots(void)
{
	static const be_u64 ptes[2][3] = {
		{ HOST_REQUEST, HOST_RESPONSE, 0U },
		{ PROT_REQUEST, PROT_RESPONSE, PROT_SECRET },
	};
	static const be_u64 pointers[2] = { POINTER_G0, POINTER_G1 };
	struct be_mvp_gstage_page pages[3];
	struct be_mvp_gstage_map maps[2];
	struct be_mvp_gstage_map plain;
	struct be_mvp_gstage_refusal refusal;
	be_u64 domain;
	be_u64 index;
	be_u64 out = 7U;

	SCENARIO();
	anchor_pages(pages);
	for (domain = 0U; domain < 2U; ++domain) {
		struct be_mvp_gstage_desc desc = mvp_desc(domain);
		be_u8 *own = pools[domain];

		memset(own, 0xa5, sizeof(pools[domain]));
		CHECK(be_mvp_gstage_build_pages(&desc, pages, 3U, domain, own,
						sizeof(pools[domain])) ==
		      BE_MVP_GSTAGE_OK);
		model_pages(&desc, pages, 3U, domain);
		CHECK(memcmp(own, expected, sizeof(expected)) == 0);
		CHECK(get_le64(own + L1_AT(32U)) == pointers[domain]);
		CHECK(get_le64(own + L1_AT(33U)) == 0U);
		for (index = 0U; index < 3U; ++index)
			CHECK(get_le64(own + L0_AT(index)) ==
			      ptes[domain][index]);
		CHECK(get_le64(own + L0_AT(3U)) == 0U);
		CHECK(be_mvp_gstage_walk_pages(&desc, pages, 3U, own,
					       sizeof(pools[domain]),
					       &maps[domain],
					       &page_leaves[domain]) ==
		      BE_MVP_GSTAGE_OK);
		/* M0's window and hgatp, DBCN's translation of it alone. */
		CHECK(be_mvp_gstage_build(&desc, scratch, sizeof(scratch)) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk(&desc, scratch, sizeof(scratch),
					 &plain) == BE_MVP_GSTAGE_OK);
		CHECK(memcmp(&plain, &maps[domain], sizeof(plain)) == 0);
		CHECK(be_mvp_gstage_translate(&maps[domain], GPA_CHANNEL, 1U,
					     &out) == 0 && out == 7U);
		CHECK(be_mvp_gstage_walk(&desc, own, sizeof(pools[domain]),
					 &plain) == BE_MVP_GSTAGE_L1);
		for (index = 0U; index < 3U; ++index) {
			const struct be_mvp_gstage_leaf *leaf =
				&page_leaves[domain].page[index];

			if (ptes[domain][index] == 0U) {
				CHECK(leaf_empty(leaf));
				continue;
			}
			CHECK(leaf->gpa == pages[index].gpa &&
			      leaf->hpa == pages[index].hpa &&
			      leaf->bytes == PAGE &&
			      leaf->pte == ptes[domain][index] &&
			      leaf->l0_pa == (domain == 0U ? L0_G0 : L0_G1));
		}
	}
	CHECK(be_mvp_gstage_page_check(maps, page_leaves, pages, 3U,
				       &refusal) == BE_MVP_GSTAGE_OK);
	CHECK(page_refusal_is(&refusal, BE_MVP_PAGES_MAX, BE_MVP_DOMAINS, 0U,
			      0U, 0U));
	/* The first page alone: te-poc's channel, as one declared page. */
	build_pages_pair(pages, 1U, maps);
	CHECK(page_leaves[0].page[0].pte == HOST_REQUEST &&
	      page_leaves[1].page[0].pte == PROT_REQUEST &&
	      leaf_empty(&page_leaves[0].page[1]) &&
	      leaf_empty(&page_leaves[1].page[2]));
	CHECK(be_mvp_gstage_page_check(maps, page_leaves, pages, 1U,
				       &refusal) == BE_MVP_GSTAGE_OK);
}

/*
 * The two negative images' leaves, as their builders write them under the
 * unchanged pages (planning/mvp-m2-plan.md, Q10): secret-shared's secret
 * leaf in G0's root, V R U A, and response-writable's W and D in G0's
 * response leaf. The walker accepts each; the page check refuses it with
 * the DETAIL values the images print.
 */
static void test_page_variants(void)
{
	struct be_mvp_gstage_page pages[3];
	struct be_mvp_gstage_map maps[2];
	struct be_mvp_gstage_map bad_maps[2];
	struct be_mvp_gstage_leaves bad_leaves[2];
	struct be_mvp_gstage_refusal refusal;
	struct be_mvp_gstage_desc desc = mvp_desc(0U);

	SCENARIO();
	anchor_pages(pages);
	build_pages_pair(pages, 3U, maps);
	/* secret-shared: walked=0x46000853 declared=0x0, page 2, G0. */
	memcpy(bad_maps, maps, sizeof(maps));
	memcpy(bad_leaves, page_leaves, sizeof(bad_leaves));
	memcpy(scratch, pools[0], sizeof(scratch));
	put_le64(scratch + L0_AT(2U), PROT_SECRET);
	CHECK(be_mvp_gstage_walk_pages(&desc, pages, 3U, scratch,
				       sizeof(scratch), &bad_maps[0],
				       &bad_leaves[0]) == BE_MVP_GSTAGE_OK);
	CHECK(bad_leaves[0].page[2].pte == PROT_SECRET);
	CHECK(be_mvp_gstage_page_check(bad_maps, bad_leaves, pages, 3U,
				       &refusal) == BE_MVP_GSTAGE_PAGES);
	CHECK(page_refusal_is(&refusal, 2U, 0U, 1U, PROT_SECRET, 0U));
	/* response-writable: walked=0x460004d7 declared=0x46000453. */
	memcpy(bad_leaves, page_leaves, sizeof(bad_leaves));
	memcpy(scratch, pools[0], sizeof(scratch));
	put_le64(scratch + L0_AT(1U), HOST_RESPONSE | 0x84U);
	CHECK(be_mvp_gstage_walk_pages(&desc, pages, 3U, scratch,
				       sizeof(scratch), &bad_maps[0],
				       &bad_leaves[0]) == BE_MVP_GSTAGE_OK);
	CHECK(bad_leaves[0].page[1].pte == PROT_RESPONSE);
	CHECK(be_mvp_gstage_page_check(bad_maps, bad_leaves, pages, 3U,
				       &refusal) == BE_MVP_GSTAGE_PAGES);
	CHECK(page_refusal_is(&refusal, 1U, 0U, 1U, BE_U64_C(0x460004d7),
			      HOST_RESPONSE));
	/* The secret page in neither root: G1's leaf missing. */
	memcpy(bad_maps, maps, sizeof(maps));
	memcpy(bad_leaves, page_leaves, sizeof(bad_leaves));
	bad_leaves[1].page[2] = (struct be_mvp_gstage_leaf){ 0U, 0U, 0U, 0U,
							      0U };
	CHECK(be_mvp_gstage_page_check(bad_maps, bad_leaves, pages, 3U,
				       &refusal) == BE_MVP_GSTAGE_PAGES);
	CHECK(page_refusal_is(&refusal, 2U, 1U, 2U, 0U, PROT_SECRET));
}

/*
 * Every rule of the declared pages, refused by the builder, which leaves
 * the pool scrubbed, and by the walker on a valid root; the domain the
 * builder takes; and absent pages and outputs.
 */
static void test_pages_rules(void)
{
	struct be_mvp_gstage_page good[3];
	struct be_mvp_gstage_page bad[3];
	struct be_mvp_gstage_desc desc = mvp_desc(1U);
	struct be_mvp_gstage_map map;
	struct be_mvp_gstage_leaves leaves;
	be_u64 index;

	SCENARIO();
	anchor_pages(good);
	memset(expected, 0, sizeof(expected));
	CHECK(be_mvp_gstage_build_pages(&desc, good, 3U, 1U, scratch,
					sizeof(scratch)) == BE_MVP_GSTAGE_OK);
	/* Each rule, by the page it breaks: 25 cases. */
	for (index = 0U; index < 25U; ++index) {
		be_u64 count = 3U;

		memcpy(bad, good, sizeof(bad));
		switch (index) {
		case 0: count = 0U; break;
		case 1: count = 4U; break;
		case 2: bad[1].bytes = 2U * PAGE; break;
		case 3: bad[1].bytes = 0U; break;
		case 4: bad[1].gpa += 8U; break;
		case 5: bad[2].hpa += 0x800U; break;
		/* Another 2 MiB slot than the first page's. */
		case 6: bad[2].gpa += 2U * MIB; break;
		/* A slot the window uses: all three pages below its end. */
		case 7:
			bad[0].gpa -= 2U * MIB;
			bad[1].gpa -= 2U * MIB;
			bad[2].gpa -= 2U * MIB;
			break;
		/* Outside the window's root entry, and beyond 2^41. */
		case 8: bad[1].gpa = BE_U64_C(0xc0001000); break;
		case 9: bad[0].gpa = BE_U64_C(1) << 41; break;
		/* Over the window, over the pool, at or above 2^56. */
		case 10: bad[1].hpa = BE_MVP_G1_HPA + 0x1000U; break;
		case 11: bad[2].hpa = POOL_G1 + 0x5000U; break;
		case 12: bad[2].hpa = BE_U64_C(1) << 56; break;
		/* Rights: execute, write alone, an unknown bit. */
		case 13: bad[0].rights[0] = RIGHT_RW | RIGHT_X; break;
		case 14: bad[1].rights[1] = RIGHT_W; break;
		case 15: bad[2].rights[0] = 8U; break;
		case 16: bad[2].rights[1] = RIGHT_X; break;
		/* Two pages at one GPA, or on one HPA. */
		case 17: bad[2].gpa = bad[0].gpa; break;
		case 18: bad[1].hpa = bad[0].hpa; break;
		case 19: bad[2].hpa = bad[1].hpa; break;
		/* The first page onto the window's last page. */
		case 20: bad[0].hpa = BE_MVP_G1_HPA + 64U * MIB - PAGE; break;
		case 21: bad[0].bytes = PAGE + 1U; break;
		case 22: bad[0].gpa += PAGE / 2U; break;
		case 23: bad[1].rights[0] = BE_U64_C(1) << 63; break;
		default: bad[2].gpa = GPA_G0; break;
		}
		memset(pool, 0xa5, sizeof(pool));
		CHECK(be_mvp_gstage_build_pages(&desc, bad, count, 1U, pool,
						sizeof(pool)) ==
		      BE_MVP_GSTAGE_PAGE);
		CHECK(memcmp(pool, expected, sizeof(pool)) == 0);
		CHECK(walk_scratch_pages(&desc, bad, count) ==
		      BE_MVP_GSTAGE_PAGE);
	}
	/* The domain: the two the builder takes, and no third. */
	memset(pool, 0xa5, sizeof(pool));
	CHECK(be_mvp_gstage_build_pages(&desc, good, 3U, BE_MVP_DOMAINS, pool,
					sizeof(pool)) == BE_MVP_GSTAGE_PAGE);
	CHECK(memcmp(pool, expected, sizeof(pool)) == 0);
	/* The descriptor's refusal comes first. */
	desc.gpa_base += MIB;
	CHECK(be_mvp_gstage_build_pages(&desc, bad, 0U, 1U, pool,
					sizeof(pool)) == BE_MVP_GSTAGE_DESC);
	desc = mvp_desc(1U);
	/* Absent pages, pool, descriptor, and outputs. */
	memset(pool, 0xa5, sizeof(pool));
	CHECK(be_mvp_gstage_build_pages(&desc, NO_PAGES, 3U, 1U, pool,
					sizeof(pool)) == BE_MVP_GSTAGE_NULL);
	CHECK(memcmp(pool, expected, sizeof(pool)) == 0);
	CHECK(be_mvp_gstage_build_pages(&desc, good, 3U, 1U, (be_u8 *)0,
					sizeof(pool)) == BE_MVP_GSTAGE_NULL);
	CHECK(be_mvp_gstage_build_pages(&desc, good, 3U, 1U, pool,
					sizeof(pool) - 1U) ==
	      BE_MVP_GSTAGE_POOL);
	CHECK(be_mvp_gstage_build_pages((const struct be_mvp_gstage_desc *)0,
					good, 3U, 1U, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(walk_scratch_pages(&desc, NO_PAGES, 3U) == BE_MVP_GSTAGE_NULL);
	memset(&leaves, 0xa5, sizeof(leaves));
	CHECK(be_mvp_gstage_walk_pages(&desc, good, 3U, scratch,
				       sizeof(scratch),
				       (struct be_mvp_gstage_map *)0,
				       &leaves) == BE_MVP_GSTAGE_NULL);
	for (index = 0U; index < BE_MVP_PAGES_MAX; ++index)
		CHECK(leaf_empty(&leaves.page[index]));
	memset(&map, 0xa5, sizeof(map));
	CHECK(be_mvp_gstage_walk_pages(&desc, good, 3U, scratch,
				       sizeof(scratch), &map,
				       (struct be_mvp_gstage_leaves *)0) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(map_empty(&map));
	CHECK(be_mvp_gstage_walk_pages(&desc, good, 3U, scratch,
				       sizeof(scratch) + 1U, &map,
				       &leaves) == BE_MVP_GSTAGE_POOL);
	CHECK(walk_scratch_pages(&desc, good, 3U) == BE_MVP_GSTAGE_OK);
}

/*
 * The walker's rules on a root with pages, G1's: one pointer, exactly, at
 * the pages' level-1 entry, to this pool's level-0 page; in that page at
 * least one leaf, each at a declared page's entry, onto its HPA, V R U A
 * with W D both or neither; nothing else. It reads no rights.
 */
static void test_pages_walk(void)
{
	static const be_u64 leaf_bits[] = {
		0x08U, 0x20U, 0x100U, 0x200U, BE_U64_C(1) << 54,
		BE_U64_C(1) << 61, BE_U64_C(1) << 63,
	};
	struct be_mvp_gstage_page pages[3];
	struct be_mvp_gstage_page other[3];
	struct be_mvp_gstage_desc desc = mvp_desc(1U);
	struct be_mvp_gstage_map map;
	struct be_mvp_gstage_leaves leaves;
	be_size index;

	SCENARIO();
	anchor_pages(pages);
	CHECK(be_mvp_gstage_build_pages(&desc, pages, 3U, 1U, pool,
					sizeof(pool)) == BE_MVP_GSTAGE_OK);
	/* A leaf at a fourth entry, or a second pointer. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(3U), PROT_SECRET + 0x400U);
	CHECK(walk_scratch_pages(&desc, pages, 3U) == BE_MVP_GSTAGE_L0);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L1_AT(33U), POINTER_G1);
	CHECK(walk_scratch_pages(&desc, pages, 3U) == BE_MVP_GSTAGE_L1);
	/* The pointer elsewhere, or with R. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L1_AT(32U), 0U);
	put_le64(scratch + L1_AT(34U), POINTER_G1);
	CHECK(walk_scratch_pages(&desc, pages, 3U) == BE_MVP_GSTAGE_L1);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L1_AT(32U), POINTER_G1 | 0x02U);
	CHECK(walk_scratch_pages(&desc, pages, 3U) == BE_MVP_GSTAGE_L1);
	/* Two pages' leaves swapped: each onto the other's HPA. */
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(0U), HOST_RESPONSE);
	put_le64(scratch + L0_AT(1U), HOST_REQUEST);
	CHECK(walk_scratch_pages(&desc, pages, 3U) == BE_MVP_GSTAGE_L0);
	/* A leaf with another bit; W without D; without R. */
	for (index = 0U; index < BE_ARRAY_SIZE(leaf_bits); ++index) {
		memcpy(scratch, pool, sizeof(pool));
		put_le64(scratch + L0_AT(2U), PROT_SECRET | leaf_bits[index]);
		CHECK(walk_scratch_pages(&desc, pages, 3U) ==
		      BE_MVP_GSTAGE_L0);
	}
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(2U), PROT_SECRET | 0x04U);
	CHECK(walk_scratch_pages(&desc, pages, 3U) == BE_MVP_GSTAGE_L0);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L0_AT(0U), PROT_REQUEST & ~BE_U64_C(0x02));
	CHECK(walk_scratch_pages(&desc, pages, 3U) == BE_MVP_GSTAGE_L0);
	/* The pointer to an empty page; leaves without the pointer; a
	 * nonzero spare byte. */
	memcpy(scratch, pool, sizeof(pool));
	for (index = 0U; index < 3U; ++index)
		put_le64(scratch + L0_AT(index), 0U);
	CHECK(walk_scratch_pages(&desc, pages, 3U) == BE_MVP_GSTAGE_L0);
	memcpy(scratch, pool, sizeof(pool));
	put_le64(scratch + L1_AT(32U), 0U);
	CHECK(walk_scratch_pages(&desc, pages, 3U) == BE_MVP_GSTAGE_SPARE);
	memcpy(scratch, pool, sizeof(pool));
	scratch[0x6000U] = 0x01U;
	CHECK(walk_scratch_pages(&desc, pages, 3U) == BE_MVP_GSTAGE_SPARE);
	/* Fewer pages declared than the root maps: the third leaf's entry
	 * is no declared page's. */
	memcpy(scratch, pool, sizeof(pool));
	CHECK(walk_scratch_pages(&desc, pages, 2U) == BE_MVP_GSTAGE_L0);
	/* The pages declared one level-1 entry up. */
	memcpy(other, pages, sizeof(other));
	for (index = 0U; index < 3U; ++index)
		other[index].gpa += 2U * MIB;
	CHECK(walk_scratch_pages(&desc, other, 3U) == BE_MVP_GSTAGE_L1);
	/* No rights read: G1's root walked under rights it does not hold,
	 * and G0's, without a secret leaf, as G1's pages. */
	memcpy(other, pages, sizeof(other));
	other[2].rights[1] = 0U;
	other[0].rights[1] = RIGHT_RW;
	CHECK(be_mvp_gstage_walk_pages(&desc, other, 3U, scratch,
				       sizeof(scratch), &map, &leaves) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(leaves.page[0].pte == PROT_REQUEST &&
	      leaves.page[2].pte == PROT_SECRET);
	CHECK(be_mvp_gstage_build_pages(&desc, pages, 3U, 0U, scratch,
					sizeof(scratch)) == BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk_pages(&desc, pages, 3U, scratch,
				       sizeof(scratch), &map, &leaves) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(leaves.page[0].pte == HOST_REQUEST &&
	      leaf_empty(&leaves.page[2]));
}

/*
 * Every bit of every nonzero entry of a root with pages, and sampled
 * nonzero bytes in its zero regions: each refused by the walker, or by the
 * page check of the walked pair.
 */
static void check_pages_mutations(be_u64 domain)
{
	struct be_mvp_gstage_page pages[3];
	struct be_mvp_gstage_desc desc = mvp_desc(domain);
	struct be_mvp_gstage_map maps[2];
	struct be_mvp_gstage_leaves leaves[2];
	struct be_mvp_gstage_refusal refusal;
	be_u64 offset;
	unsigned int bit;
	unsigned long flips = 0U;

	SCENARIO();
	anchor_pages(pages);
	build_pages_pair(pages, 3U, maps);
	memcpy(leaves, page_leaves, sizeof(leaves));
	for (offset = 0U; offset < BE_MVP_GSTAGE_POOL_BYTES; offset += 1U) {
		be_u64 at = offset & ~BE_U64_C(7);
		int nonzero = get_le64(pools[domain] + at) != 0U;

		/* Every bit of a nonzero entry; one zero byte in 61. */
		if (!nonzero && offset % 61U != 0U)
			continue;
		for (bit = 0U; bit < 8U; ++bit) {
			if (!nonzero && bit != 0U)
				break;
			memcpy(scratch, pools[domain], sizeof(scratch));
			scratch[offset] ^= (be_u8)(1U << bit);
			CHECK(be_mvp_gstage_walk_pages(&desc, pages, 3U,
						       scratch,
						       sizeof(scratch),
						       &maps[domain],
						       &leaves[domain]) !=
				      BE_MVP_GSTAGE_OK ||
			      be_mvp_gstage_page_check(maps, leaves, pages, 3U,
						       &refusal) !=
				      BE_MVP_GSTAGE_OK);
			++flips;
		}
	}
	/* The root pointer, 32 leaves, the level-1 pointer, the leaves. */
	CHECK(flips > 36U * 64U);
}

/*
 * The page check's every refusal: the pair rules first, naming no root;
 * each page's own rules, naming the page alone; then a walked leaf that
 * differs from the declared one, naming the page and its root; and its
 * absent arguments.
 */
static void test_page_check(void)
{
	struct be_mvp_gstage_page pages[3];
	struct be_mvp_gstage_page bad[3];
	struct be_mvp_gstage_map maps[2];
	struct be_mvp_gstage_map bad_maps[2];
	struct be_mvp_gstage_leaves bad_leaves[2];
	struct be_mvp_gstage_refusal refusal;
	be_u64 index;

	SCENARIO();
	anchor_pages(pages);
	build_pages_pair(pages, 3U, maps);
	CHECK(be_mvp_gstage_page_check(maps, page_leaves, pages, 3U,
				       &refusal) == BE_MVP_GSTAGE_OK);
	/* M0's pair rules first: equal VMIDs, an unwalked map. */
	memcpy(bad_maps, maps, sizeof(maps));
	bad_maps[1].vmid = bad_maps[0].vmid;
	CHECK(be_mvp_gstage_page_check(bad_maps, page_leaves, pages, 3U,
				       &refusal) == BE_MVP_GSTAGE_PAIR);
	CHECK(page_refusal_is(&refusal, BE_MVP_PAGES_MAX, BE_MVP_DOMAINS, 0U,
			      0U, 0U));
	memset(&bad_maps[1], 0, sizeof(bad_maps[1]));
	CHECK(be_mvp_gstage_page_check(bad_maps, page_leaves, pages, 3U,
				       &refusal) == BE_MVP_GSTAGE_PAIR);
	/* No pages, or too many. */
	CHECK(be_mvp_gstage_page_check(maps, page_leaves, pages, 0U,
				       &refusal) == BE_MVP_GSTAGE_PAGES);
	CHECK(page_refusal_is(&refusal, BE_MVP_PAGES_MAX, BE_MVP_DOMAINS, 0U,
			      0U, 0U));
	CHECK(be_mvp_gstage_page_check(maps, page_leaves, pages, 4U,
				       &refusal) == BE_MVP_GSTAGE_PAGES);
	/* Each page's own rules, by the page that breaks one: 16 cases. */
	for (index = 0U; index < 16U; ++index) {
		be_u64 page = 0U;

		memcpy(bad, pages, sizeof(bad));
		switch (index) {
		case 0: bad[0].kind = 2U; break;
		case 1: bad[0].reader = 0U; break;
		case 2: bad[0].writer = 2U; break;
		case 3: bad[0].writer = BE_MVP_PAGE_NONE; break;
		case 4: bad[0].rights[1] = RIGHT_RW; break;
		case 5: page = 1U; bad[1].rights[1] = RIGHT_R; break;
		case 6: page = 1U; bad[1].reader = 2U; break;
		case 7: page = 2U; bad[2].writer = 0U; break;
		case 8: page = 2U; bad[2].rights[0] = RIGHT_R; break;
		case 9: page = 2U; bad[2].rights[1] = RIGHT_RW; break;
		case 10: page = 2U; bad[2].reader = BE_MVP_PAGE_NONE; break;
		case 11: page = 2U; bad[2].hpa = bad[0].hpa; break;
		case 12: page = 1U; bad[1].gpa = bad[0].gpa; break;
		case 13: page = 1U; bad[1].bytes = 2U * PAGE; break;
		case 14: page = 2U; bad[2].hpa = BE_U64_C(1) << 56; break;
		default: page = 1U; bad[1].gpa = BE_U64_C(1) << 41; break;
		}
		CHECK(be_mvp_gstage_page_check(maps, page_leaves, bad, 3U,
					       &refusal) ==
		      BE_MVP_GSTAGE_PAGES);
		CHECK(page_refusal_is(&refusal, page, BE_MVP_DOMAINS, 0U, 0U,
				      0U));
	}
	/* A leaf that differs: its PTE, HPA, GPA, size, or level-0 page. */
	for (index = 0U; index < 5U; ++index) {
		struct be_mvp_gstage_leaf *leaf;

		memcpy(bad_leaves, page_leaves, sizeof(bad_leaves));
		leaf = &bad_leaves[1].page[1];
		if (index == 0U)
			leaf->pte = PROT_REQUEST;
		else if (index == 1U)
			leaf->hpa += PAGE;
		else if (index == 2U)
			leaf->gpa += PAGE;
		else if (index == 3U)
			leaf->bytes = 2U * PAGE;
		else
			leaf->l0_pa = L0_G0;
		CHECK(be_mvp_gstage_page_check(maps, bad_leaves, pages, 3U,
					       &refusal) ==
		      BE_MVP_GSTAGE_PAGES);
		CHECK(page_refusal_is(&refusal, 1U, 1U, 2U, leaf->pte,
				      PROT_RESPONSE));
	}
	/* A leaf beyond the declared pages: the third, with two declared. */
	CHECK(be_mvp_gstage_page_check(maps, page_leaves, pages, 2U,
				       &refusal) == BE_MVP_GSTAGE_PAGES);
	CHECK(page_refusal_is(&refusal, 2U, 1U, 2U, PROT_SECRET, 0U));
	/* G0's response leaf missing. */
	memcpy(bad_leaves, page_leaves, sizeof(bad_leaves));
	bad_leaves[0].page[1] = (struct be_mvp_gstage_leaf){ 0U, 0U, 0U, 0U,
							      0U };
	CHECK(be_mvp_gstage_page_check(maps, bad_leaves, pages, 3U,
				       &refusal) == BE_MVP_GSTAGE_PAGES);
	CHECK(page_refusal_is(&refusal, 1U, 0U, 1U, 0U, HOST_RESPONSE));
	/* A window over a page, which M0's rules allow: G1's moved up onto
	 * the shared pages, or G0's in guest-physical space. */
	memcpy(bad_maps, maps, sizeof(maps));
	bad_maps[1].hpa_base += 2U * MIB;
	CHECK(be_mvp_gstage_pair_check(&bad_maps[0], &bad_maps[1]) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_page_check(bad_maps, page_leaves, pages, 3U,
				       &refusal) == BE_MVP_GSTAGE_PAGES);
	CHECK(page_refusal_is(&refusal, 0U, 1U, 2U, PROT_REQUEST,
			      PROT_REQUEST));
	memcpy(bad_maps, maps, sizeof(maps));
	bad_maps[0].gpa_base += 32U * MIB;
	CHECK(be_mvp_gstage_page_check(bad_maps, page_leaves, pages, 3U,
				       &refusal) == BE_MVP_GSTAGE_PAGES);
	CHECK(page_refusal_is(&refusal, 0U, 0U, 1U, HOST_REQUEST,
			      HOST_REQUEST));
	/* A page over a pool, the pages and the leaves agreeing: G1's spare
	 * page under the secret. */
	memcpy(bad, pages, sizeof(bad));
	memcpy(bad_leaves, page_leaves, sizeof(bad_leaves));
	bad[2].hpa = POOL_G1 + 0x6000U;
	bad_leaves[1].page[2].hpa = bad[2].hpa;
	bad_leaves[1].page[2].pte = 0x53U | ((bad[2].hpa >> 12) << 10);
	CHECK(be_mvp_gstage_page_check(maps, bad_leaves, bad, 3U, &refusal) ==
	      BE_MVP_GSTAGE_PAGES);
	CHECK(page_refusal_is(&refusal, 2U, 1U, 2U, bad_leaves[1].page[2].pte,
			      bad_leaves[1].page[2].pte));
	/* Absent arguments; the refusal is reset first. */
	CHECK(be_mvp_gstage_page_check(maps, page_leaves, pages, 3U,
				       (struct be_mvp_gstage_refusal *)0) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(be_mvp_gstage_page_check((const struct be_mvp_gstage_map *)0,
				       page_leaves, pages, 3U, &refusal) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(page_refusal_is(&refusal, BE_MVP_PAGES_MAX, BE_MVP_DOMAINS, 0U,
			      0U, 0U));
	CHECK(be_mvp_gstage_page_check(maps,
				       (const struct be_mvp_gstage_leaves *)0,
				       pages, 3U, &refusal) ==
	      BE_MVP_GSTAGE_NULL);
	CHECK(be_mvp_gstage_page_check(maps, page_leaves, NO_PAGES, 3U,
				       &refusal) == BE_MVP_GSTAGE_NULL);
}

#ifdef BE_MVP_CHERI
/*
 * beryllium-cheri: the CHERI-aware monitor's capability-write control
 * (planning/cheri-enforcement-plan.md, CE-2): CW in every window leaf and
 * in no other entry, and the walker's refusals of a window leaf without
 * CW or with another high bit, a channel or page leaf with CW, and a
 * pointer with CW. CRG is bit 59, beside CW; bits 54-63 are a PTE's high
 * bits.
 */
#define CRG			(BE_U64_C(1) << 59)
#define HIGH_BITS		(BE_U64_C(0x3ff) << 54)

/* Build one of the six MVP roots in pool[]: M0's (0, 1), te-poc's channel
 * roots (2, 3), anchor's roots with pages (4, 5); domain ROOT % 2. */
static void build_cheri_root(be_u64 root,
			     const struct be_mvp_gstage_page *pages)
{
	struct be_mvp_gstage_desc desc = mvp_desc(root % 2U);
	struct be_mvp_gstage_root_page page =
		mvp_page(root % 2U == 0U ? RIGHT_RW : RIGHT_R);

	if (root < 2U)
		CHECK(be_mvp_gstage_build(&desc, pool, sizeof(pool)) ==
		      BE_MVP_GSTAGE_OK);
	else if (root < 4U)
		CHECK(be_mvp_gstage_build_channel(&desc, &page, pool,
						  sizeof(pool)) ==
		      BE_MVP_GSTAGE_OK);
	else
		CHECK(be_mvp_gstage_build_pages(&desc, pages, 3U, root % 2U,
						pool, sizeof(pool)) ==
		      BE_MVP_GSTAGE_OK);
}

/* Walk scratch[] as ROOT's kind walks it. */
static enum be_mvp_gstage_error
walk_cheri_root(be_u64 root, const struct be_mvp_gstage_page *pages)
{
	static const struct be_mvp_gstage_root_page none = { 0U, 0U, 0U, 0U };
	struct be_mvp_gstage_desc desc = mvp_desc(root % 2U);
	struct be_mvp_gstage_root_page page =
		mvp_page(root % 2U == 0U ? RIGHT_RW : RIGHT_R);

	if (root < 2U)
		return walk_scratch(&desc, &none);
	if (root < 4U)
		return walk_scratch(&desc, &page);
	return walk_scratch_pages(&desc, pages, 3U);
}

/*
 * Each MVP root's entries: its 32 window leaves, the level-1 page's
 * entries with X, each with exactly CW among its high bits; and every
 * other entry with none: its root pointer, and in te-poc's roots the
 * level-1 pointer and the channel leaf, and in anchor's the level-1
 * pointer and the host's two page leaves or the protected domain's three.
 */
static void test_cheri_leaves(void)
{
	static const be_u64 others[6] = { 1U, 1U, 3U, 3U, 4U, 5U };
	struct be_mvp_gstage_page pages[3];
	be_u64 root;
	be_u64 offset;

	SCENARIO();
	anchor_pages(pages);
	CHECK(WINDOW_CW == BE_U64_C(0x1000000000000000));
	for (root = 0U; root < 6U; ++root) {
		be_u64 windows = 0U;
		be_u64 rest = 0U;

		build_cheri_root(root, pages);
		for (offset = 0U; offset < BE_MVP_GSTAGE_POOL_BYTES;
		     offset += 8U) {
			be_u64 pte = get_le64(pool + offset);

			if (pte == 0U)
				continue;
			if (offset >= L1_AT(0U) && offset < L0_AT(0U) &&
			    (pte & 0x3ffU) == 0xdfU) {
				CHECK((pte & HIGH_BITS) == WINDOW_CW);
				++windows;
			} else {
				CHECK((pte & HIGH_BITS) == 0U);
				++rest;
			}
		}
		CHECK(windows == 32U && rest == others[root]);
	}
}

/*
 * The walker's refusals: in each MVP root, a window leaf without CW (the
 * first, the second, a middle one, the last, or all 32, as the
 * development line's builder writes them), with CRG beside CW or in its
 * place, or with any other high bit beside CW; a channel or page leaf
 * with CW, as channel-cw's builder writes it; and the root pointer or
 * the level-1 pointer with CW.
 */
static void test_cheri_walk(void)
{
	static const be_u64 leaves[] = { 0U, 1U, 15U, 31U };
	static const unsigned int bits[] = { 54U, 55U, 56U, 57U, 58U, 59U,
					     61U, 62U, 63U };
	struct be_mvp_gstage_page pages[3];
	be_u64 root;
	be_size index;
	be_size bit;

	SCENARIO();
	anchor_pages(pages);
	for (root = 0U; root < 6U; ++root) {
		be_u64 entry;

		build_cheri_root(root, pages);
		memcpy(scratch, pool, sizeof(pool));
		CHECK(walk_cheri_root(root, pages) == BE_MVP_GSTAGE_OK);
		for (index = 0U; index < BE_ARRAY_SIZE(leaves); ++index) {
			be_u64 at = L1_AT(leaves[index]);
			be_u64 leaf = get_le64(pool + at);

			memcpy(scratch, pool, sizeof(pool));
			put_le64(scratch + at, leaf & ~WINDOW_CW);
			CHECK(walk_cheri_root(root, pages) == BE_MVP_GSTAGE_L1);
			put_le64(scratch + at, (leaf & ~WINDOW_CW) | CRG);
			CHECK(walk_cheri_root(root, pages) == BE_MVP_GSTAGE_L1);
			for (bit = 0U; bit < BE_ARRAY_SIZE(bits); ++bit) {
				put_le64(scratch + at,
					 leaf | (BE_U64_C(1) << bits[bit]));
				CHECK(walk_cheri_root(root, pages) ==
				      BE_MVP_GSTAGE_L1);
			}
		}
		memcpy(scratch, pool, sizeof(pool));
		for (entry = 0U; entry < 32U; ++entry)
			put_le64(scratch + L1_AT(entry),
				 get_le64(pool + L1_AT(entry)) & ~WINDOW_CW);
		CHECK(walk_cheri_root(root, pages) == BE_MVP_GSTAGE_L1);
		/* The root pointer, in root slot 2, with CW. */
		memcpy(scratch, pool, sizeof(pool));
		put_le64(scratch + 16U, get_le64(pool + 16U) | WINDOW_CW);
		CHECK(walk_cheri_root(root, pages) == BE_MVP_GSTAGE_ROOT);
		if (root < 2U)
			continue;
		/* The level-1 pointer, entry 32, with CW. */
		memcpy(scratch, pool, sizeof(pool));
		put_le64(scratch + L1_AT(32U),
			 get_le64(pool + L1_AT(32U)) | WINDOW_CW);
		CHECK(walk_cheri_root(root, pages) == BE_MVP_GSTAGE_L1);
		/* Each channel or page leaf with CW, and all of them. */
		for (entry = 0U; entry < 3U; ++entry) {
			if (get_le64(pool + L0_AT(entry)) == 0U)
				continue;
			memcpy(scratch, pool, sizeof(pool));
			put_le64(scratch + L0_AT(entry),
				 get_le64(pool + L0_AT(entry)) | WINDOW_CW);
			CHECK(walk_cheri_root(root, pages) == BE_MVP_GSTAGE_L0);
		}
		memcpy(scratch, pool, sizeof(pool));
		for (entry = 0U; entry < 3U; ++entry)
			if (get_le64(pool + L0_AT(entry)) != 0U)
				put_le64(scratch + L0_AT(entry),
					 get_le64(pool + L0_AT(entry)) |
					 WINDOW_CW);
		CHECK(walk_cheri_root(root, pages) == BE_MVP_GSTAGE_L0);
	}
}
#endif

int main(void)
{
	test_constants();
	check_window(GPA_G0, HPA_G0, 64U * MIB, POOL_G0, 1U, 1U);
	check_window(GPA_G0, HPA_G1, 64U * MIB, POOL_G1, 2U, 2U);
	check_window(GPA_G0, HPA_G0, 128U * MIB, POOL_G0, 1U, 1U);
	check_window(GPA_G0, HPA_OTHER, 64U * MIB, POOL_G0, 0x3fffU, 7U);
	check_window(BE_U64_C(0xbfe00000), HPA_G0, 2U * MIB, POOL_G0, 0U, 9U);
	check_window(GPA_G0, HPA_G0, 1024U * MIB, POOL_G0, 2U, ALL_ONES);
	check_window(BE_U64_C(0x40000000), HPA_G0, 64U * MIB,
		     BE_U64_C(0x108000000), 1U, 0U);
	test_mvp_windows();
	test_pairs();
	test_vmids();
	check_mutations(GPA_G0, HPA_G0, 64U * MIB);
	check_mutations(GPA_G0, HPA_G0, 128U * MIB);
	check_mutations(GPA_G0, HPA_G1, 64U * MIB);
	test_moves();
	test_refusals();
	test_no_channel();
	test_channel_roots();
	test_channel_edges();
	test_page_refusals();
	test_channel_walk();
	check_channel_mutations(0U, RIGHT_RW);
	check_channel_mutations(1U, RIGHT_R);
	test_channel_check();
	test_mutations();
	test_page_roots();
	test_page_variants();
	test_pages_rules();
	test_pages_walk();
	check_pages_mutations(0U);
	check_pages_mutations(1U);
	test_page_check();
#ifdef BE_MVP_CHERI
	test_cheri_leaves();
	test_cheri_walk();
#endif
	printf("BE_MVP_GSTAGE_CHECK: PASS\n");
	printf("BE_MVP_GSTAGE_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_MVP_GSTAGE_CHECK: assertions=%lu\n", assertions);
	return 0;
}
