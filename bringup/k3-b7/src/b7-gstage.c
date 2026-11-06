// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B7 G-stage builder, independent re-walker, pair check, and
 *          guest-range translation for one guest-RAM window per guest,
 *          mapped by 2 MiB Sv39x4 leaves under the guest's own VMID.
 * Trust:   restricted C with explicit bounded loops. No CSR, fence, or I/O;
 *          the builder and the walker share only the byte loader.
 * Scope:   B7 only (planning/k3-b7-plan.md); see b7-gstage.h.
 */
#include "b7-gstage.h"

#define PTE_BYTES		8U
#define LEAF_SHIFT		21U
#define GIB_SHIFT		30U
#define PAGE_SHIFT		12U
#define L1_INDEX_MASK		BE_U64_C(0x1ff)
#define POINTER_FORBIDDEN	(BE_B7_PTE_R | BE_B7_PTE_W | BE_B7_PTE_X | \
				 BE_B7_PTE_U | BE_B7_PTE_G | BE_B7_PTE_A | \
				 BE_B7_PTE_D | (BE_U64_C(3) << 8))
#define PTE_HIGH_MASK		(BE_U64_C(0x3ff) << 54)
#define LOW_FLAGS_MASK		BE_U64_C(0x3ff)
#define LEAF_PPN_ALIGN_MASK	BE_U64_C(0x1ff)
#define LEAF_PPN_STEP		(BE_B7_GSTAGE_LEAF_BYTES >> PAGE_SHIFT)
#define NO_ENTRY		(~BE_U64_C(0))

_Static_assert(BE_B7_GSTAGE_LEAF_BYTES == (BE_U64_C(1) << LEAF_SHIFT),
	       "the leaf size is 2 MiB");
_Static_assert(BE_B7_GSTAGE_ROOT_ENTRIES * PTE_BYTES == BE_B7_ROOT_BYTES,
	       "the Sv39x4 root fills its 16 KiB");
_Static_assert(BE_B7_GSTAGE_L1_ENTRIES * PTE_BYTES ==
	       BE_B7_GSTAGE_SPARE_OFFSET - BE_B7_GSTAGE_L1_OFFSET,
	       "the level-1 table fills one page");
_Static_assert(BE_B7_GSTAGE_SPARE_OFFSET < BE_B7_GSTAGE_POOL_BYTES,
	       "the pool holds the root, the level-1 page, and spare bytes");
_Static_assert(BE_B7_G0_LEVEL1_HPA ==
	       BE_B7_G0_ROOT_HPA + BE_B7_GSTAGE_L1_OFFSET &&
	       BE_B7_G1_LEVEL1_HPA ==
	       BE_B7_G1_ROOT_HPA + BE_B7_GSTAGE_L1_OFFSET,
	       "each level-1 page sits where the layout puts it");
_Static_assert(BE_B7_G0_VMID < BE_B7_GSTAGE_VMID_LIMIT &&
	       BE_B7_G1_VMID < BE_B7_GSTAGE_VMID_LIMIT,
	       "each VMID fits hgatp.VMID");

static void store_le64(be_u8 *destination, be_u64 value)
{
	unsigned int byte;

	for (byte = 0U; byte < PTE_BYTES; ++byte)
		destination[byte] = (be_u8)((value >> (8U * byte)) & 0xffU);
}

static be_u64 load_le64(const be_u8 *source)
{
	be_u64 value = 0U;
	unsigned int byte;

	for (byte = 0U; byte < PTE_BYTES; ++byte)
		value |= (be_u64)source[byte] << (8U * byte);
	return value;
}

static int overlaps(be_u64 first, be_u64 first_size, be_u64 second,
		    be_u64 second_size)
{
	return first < second + second_size && second < first + first_size;
}

static int pool_placement_valid(be_u64 pool_pa)
{
	return (pool_pa & (BE_B7_GSTAGE_POOL_ALIGN - 1U)) == 0U &&
	       pool_pa < BE_B7_GSTAGE_PA_LIMIT &&
	       BE_B7_GSTAGE_POOL_BYTES <= BE_B7_GSTAGE_PA_LIMIT - pool_pa;
}

/* Builder-side descriptor rules. */
static enum be_b7_gstage_error
build_check(const struct be_b7_gstage_desc *desc)
{
	be_u64 leaf_mask = BE_B7_GSTAGE_LEAF_BYTES - 1U;

	if ((desc->gpa_base & leaf_mask) != 0U ||
	    (desc->hpa_base & leaf_mask) != 0U || desc->size == 0U ||
	    (desc->size & leaf_mask) != 0U ||
	    desc->gpa_base >= BE_B7_GSTAGE_GPA_LIMIT ||
	    desc->size > BE_B7_GSTAGE_GPA_LIMIT - desc->gpa_base ||
	    desc->size > BE_B7_GSTAGE_GIB -
			 (desc->gpa_base & (BE_B7_GSTAGE_GIB - 1U)) ||
	    desc->hpa_base >= BE_B7_GSTAGE_PA_LIMIT ||
	    desc->size > BE_B7_GSTAGE_PA_LIMIT - desc->hpa_base ||
	    !pool_placement_valid(desc->pool_pa) ||
	    desc->vmid >= BE_B7_GSTAGE_VMID_LIMIT)
		return BE_B7_GSTAGE_DESC;
	if (overlaps(desc->pool_pa, BE_B7_GSTAGE_POOL_BYTES, desc->hpa_base,
		     desc->size))
		return BE_B7_GSTAGE_POOL;
	return BE_B7_GSTAGE_OK;
}

enum be_b7_gstage_error
be_b7_gstage_build(const struct be_b7_gstage_desc *desc, be_u8 *pool,
		   be_u64 pool_size)
{
	enum be_b7_gstage_error error;
	be_u64 index;
	be_u64 root_index;
	be_u64 l1_first;
	be_u64 count;

	if (pool == (be_u8 *)0)
		return BE_B7_GSTAGE_NULL;
	if (pool_size != BE_B7_GSTAGE_POOL_BYTES)
		return BE_B7_GSTAGE_POOL;
	for (index = 0U; index < BE_B7_GSTAGE_POOL_BYTES; ++index)
		pool[index] = 0U;
	if (desc == (const struct be_b7_gstage_desc *)0)
		return BE_B7_GSTAGE_NULL;
	error = build_check(desc);
	if (error != BE_B7_GSTAGE_OK)
		return error;
	root_index = desc->gpa_base >> GIB_SHIFT;
	l1_first = (desc->gpa_base >> LEAF_SHIFT) & L1_INDEX_MASK;
	count = desc->size >> LEAF_SHIFT;
	store_le64(pool + root_index * PTE_BYTES,
		   BE_B7_PTE_V |
			   (((desc->pool_pa + BE_B7_GSTAGE_L1_OFFSET) >>
			     PAGE_SHIFT) << BE_B7_PTE_PPN_SHIFT));
	for (index = 0U; index < count; ++index)
		store_le64(pool + BE_B7_GSTAGE_L1_OFFSET +
				   (l1_first + index) * PTE_BYTES,
			   BE_B7_PTE_LEAF_FLAGS |
				   (((desc->hpa_base +
				      index * BE_B7_GSTAGE_LEAF_BYTES) >>
				     PAGE_SHIFT) << BE_B7_PTE_PPN_SHIFT));
	return BE_B7_GSTAGE_OK;
}

/* Walker: exactly one root entry, a pointer to this pool's level-1 page. */
static enum be_b7_gstage_error walk_root(const be_u8 *pool, be_u64 pool_pa,
					 be_u64 *slot)
{
	be_u64 index;
	be_u64 found = NO_ENTRY;

	for (index = 0U; index < BE_B7_GSTAGE_ROOT_ENTRIES; ++index) {
		be_u64 pte = load_le64(pool + index * PTE_BYTES);

		if (pte == 0U)
			continue;
		if (found != NO_ENTRY || (pte & BE_B7_PTE_V) == 0U ||
		    (pte & POINTER_FORBIDDEN) != 0U ||
		    (pte & PTE_HIGH_MASK) != 0U ||
		    ((pte >> BE_B7_PTE_PPN_SHIFT) & BE_B7_PTE_PPN_MASK) !=
			    (pool_pa + BE_B7_GSTAGE_L1_OFFSET) >> PAGE_SHIFT)
			return BE_B7_GSTAGE_ROOT;
		found = index;
	}
	if (found == NO_ENTRY)
		return BE_B7_GSTAGE_ROOT;
	*slot = found;
	return BE_B7_GSTAGE_OK;
}

/* Walker: one contiguous linear run of exact 2 MiB leaves, zero elsewhere. */
static enum be_b7_gstage_error walk_l1(const be_u8 *pool, be_u64 *first,
				       be_u64 *leaves, be_u64 *hpa_base)
{
	be_u64 index;
	be_u64 start = NO_ENTRY;
	be_u64 count = 0U;
	be_u64 base_ppn = 0U;

	for (index = 0U; index < BE_B7_GSTAGE_L1_ENTRIES; ++index) {
		be_u64 pte = load_le64(pool + BE_B7_GSTAGE_L1_OFFSET +
				       index * PTE_BYTES);
		be_u64 ppn = (pte >> BE_B7_PTE_PPN_SHIFT) & BE_B7_PTE_PPN_MASK;

		if (pte == 0U)
			continue;
		if ((pte & LOW_FLAGS_MASK) != BE_B7_PTE_LEAF_FLAGS ||
		    (pte & PTE_HIGH_MASK) != 0U ||
		    (ppn & LEAF_PPN_ALIGN_MASK) != 0U)
			return BE_B7_GSTAGE_L1;
		if (start == NO_ENTRY) {
			start = index;
			base_ppn = ppn;
		} else if (index != start + count ||
			   ppn != base_ppn + count * LEAF_PPN_STEP) {
			return BE_B7_GSTAGE_L1;
		}
		++count;
	}
	if (count == 0U)
		return BE_B7_GSTAGE_L1;
	*first = start;
	*leaves = count;
	*hpa_base = base_ppn << PAGE_SHIFT;
	return BE_B7_GSTAGE_OK;
}

enum be_b7_gstage_error
be_b7_gstage_walk(const struct be_b7_gstage_desc *desc, const be_u8 *pool,
		  be_u64 pool_size, struct be_b7_gstage_map *map)
{
	enum be_b7_gstage_error error;
	be_u64 slot = 0U;
	be_u64 first = 0U;
	be_u64 leaves = 0U;
	be_u64 hpa_base = 0U;
	be_u64 gpa_base;
	be_u64 size;
	be_u64 index;

	if (map == (struct be_b7_gstage_map *)0)
		return BE_B7_GSTAGE_NULL;
	*map = (struct be_b7_gstage_map){ 0U, 0U, 0U, 0U, 0U, 0U, 0U };
	if (desc == (const struct be_b7_gstage_desc *)0 ||
	    pool == (const be_u8 *)0)
		return BE_B7_GSTAGE_NULL;
	if (pool_size != BE_B7_GSTAGE_POOL_BYTES ||
	    !pool_placement_valid(desc->pool_pa))
		return BE_B7_GSTAGE_POOL;
	if (desc->vmid >= BE_B7_GSTAGE_VMID_LIMIT)
		return BE_B7_GSTAGE_DESC;
	error = walk_root(pool, desc->pool_pa, &slot);
	if (error != BE_B7_GSTAGE_OK)
		return error;
	error = walk_l1(pool, &first, &leaves, &hpa_base);
	if (error != BE_B7_GSTAGE_OK)
		return error;
	for (index = BE_B7_GSTAGE_SPARE_OFFSET; index < BE_B7_GSTAGE_POOL_BYTES;
	     ++index)
		if (pool[index] != 0U)
			return BE_B7_GSTAGE_SPARE;
	gpa_base = (slot << GIB_SHIFT) | (first << LEAF_SHIFT);
	size = leaves << LEAF_SHIFT;
	if (gpa_base != desc->gpa_base || hpa_base != desc->hpa_base ||
	    size != desc->size || hpa_base >= BE_B7_GSTAGE_PA_LIMIT ||
	    size > BE_B7_GSTAGE_PA_LIMIT - hpa_base ||
	    overlaps(desc->pool_pa, BE_B7_GSTAGE_POOL_BYTES, hpa_base, size))
		return BE_B7_GSTAGE_MISMATCH;
	map->hgatp = BE_B7_GSTAGE_HGATP_SV39X4 |
		     (desc->vmid << BE_B7_GSTAGE_VMID_SHIFT) |
		     (desc->pool_pa >> PAGE_SHIFT);
	map->gpa_base = gpa_base;
	map->hpa_base = hpa_base;
	map->size = size;
	map->leaves = leaves;
	map->pool_pa = desc->pool_pa;
	map->vmid = desc->vmid;
	return BE_B7_GSTAGE_OK;
}

/* A map the walker filled: a nonzero size, and hgatp in Sv39x4 mode. */
static int walked(const struct be_b7_gstage_map *map)
{
	return map->size != 0U &&
	       (map->hgatp >> 60) == (BE_B7_GSTAGE_HGATP_SV39X4 >> 60);
}

enum be_b7_gstage_error
be_b7_gstage_pair_check(const struct be_b7_gstage_map *first,
			const struct be_b7_gstage_map *second)
{
	if (first == (const struct be_b7_gstage_map *)0 ||
	    second == (const struct be_b7_gstage_map *)0)
		return BE_B7_GSTAGE_NULL;
	if (!walked(first) || !walked(second) || first->vmid == 0U ||
	    second->vmid == 0U || first->vmid == second->vmid ||
	    first->hgatp == second->hgatp ||
	    overlaps(first->pool_pa, BE_B7_GSTAGE_POOL_BYTES, second->pool_pa,
		     BE_B7_GSTAGE_POOL_BYTES) ||
	    overlaps(first->hpa_base, first->size, second->hpa_base,
		     second->size) ||
	    overlaps(first->hpa_base, first->size, second->pool_pa,
		     BE_B7_GSTAGE_POOL_BYTES) ||
	    overlaps(second->hpa_base, second->size, first->pool_pa,
		     BE_B7_GSTAGE_POOL_BYTES))
		return BE_B7_GSTAGE_PAIR;
	return BE_B7_GSTAGE_OK;
}

int be_b7_gstage_translate(const struct be_b7_gstage_map *map, be_u64 gpa,
			   be_u64 length, be_u64 *hpa)
{
	be_u64 offset;

	if (map == (const struct be_b7_gstage_map *)0 ||
	    hpa == (be_u64 *)0 || length == 0U || map->size == 0U ||
	    gpa < map->gpa_base)
		return 0;
	offset = gpa - map->gpa_base;
	if (offset >= map->size || length > map->size - offset)
		return 0;
	*hpa = map->hpa_base + offset;
	return 1;
}
