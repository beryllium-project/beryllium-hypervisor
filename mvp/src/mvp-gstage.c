// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP G-stage builder, independent re-walker, pair and channel
 *          checks, and guest-range translation for one guest-RAM window per
 *          domain, mapped by 2 MiB Sv39x4 leaves under the domain's own
 *          VMID, for the domain's own hart, and at most one 4 KiB channel
 *          leaf per root, in the root's level-0 page; or, for a scenario
 *          with pages (planning/mvp-m2-plan.md), each root's leaves for up
 *          to three declared pages in that level-0 page, and their page
 *          check.
 * Trust:   restricted C with explicit bounded loops. No CSR, fence, or I/O;
 *          the builder and the walker share only the byte loader and the
 *          rules on what may be declared, and the channel and page checks
 *          derive each declared leaf by their own code.
 * Scope:   the MVP line (planning/mvp-m0-plan.md, planning/mvp-m1-plan.md,
 *          and planning/mvp-m2-plan.md); see mvp-gstage.h.
 */
#include "mvp-gstage.h"

#define PTE_BYTES		8U
#define LEAF_SHIFT		21U
#define GIB_SHIFT		30U
#define PAGE_SHIFT		12U
#define L1_INDEX_MASK		BE_U64_C(0x1ff)
#define L0_INDEX_MASK		BE_U64_C(0x1ff)
#define POINTER_FORBIDDEN	(BE_MVP_PTE_R | BE_MVP_PTE_W | BE_MVP_PTE_X | \
				 BE_MVP_PTE_U | BE_MVP_PTE_G | BE_MVP_PTE_A | \
				 BE_MVP_PTE_D | (BE_U64_C(3) << 8))
#define PTE_HIGH_MASK		(BE_U64_C(0x3ff) << 54)
#define LOW_FLAGS_MASK		BE_U64_C(0x3ff)
#define LEAF_PPN_ALIGN_MASK	BE_U64_C(0x1ff)
#define LEAF_PPN_STEP		(BE_MVP_GSTAGE_LEAF_BYTES >> PAGE_SHIFT)
#define NO_ENTRY		(~BE_U64_C(0))
/* The walker's two channel leaves: V R U A, then W D as well. */
#define CHANNEL_READ		(BE_MVP_PTE_V | BE_MVP_PTE_R | BE_MVP_PTE_U | \
				 BE_MVP_PTE_A)
#define CHANNEL_READ_WRITE	(CHANNEL_READ | BE_MVP_PTE_W | BE_MVP_PTE_D)
#define RIGHTS_READ_WRITE	(BE_MVP_GSTAGE_RIGHT_READ | \
				 BE_MVP_GSTAGE_RIGHT_WRITE)

/*
 * The reader-write negative image (planning/mvp-m1-plan.md, "Scenarios and
 * the harness"): a builder that writes W and D into every channel leaf, the
 * reader's included, under the unchanged sealed record. The walker accepts
 * that leaf; the channel check must refuse it.
 */
#if defined(BE_MVP_VARIANT_READER_WRITE)
#define BUILDER_DEFECT		(BE_MVP_PTE_W | BE_MVP_PTE_D)
#else
#define BUILDER_DEFECT		BE_U64_C(0)
#endif

/*
 * The page builder's two negative images (planning/mvp-m2-plan.md,
 * "Scenarios and the harness"), each under the unchanged sealed pages,
 * whose leaves the walker accepts and the page check must refuse:
 * secret-shared, whose builder also maps each secret page, V R U A, into
 * every root whose domain has no rights on it (the host's, in anchor);
 * and response-writable, whose builder writes W and D into domain 0's
 * leaf of each channel page domain 0 reads (the host's response leaf).
 */
#if defined(BE_MVP_VARIANT_SECRET_SHARED)
#define SECRET_SHARED		1
#else
#define SECRET_SHARED		0
#endif
#if defined(BE_MVP_VARIANT_RESPONSE_WRITABLE)
#define RESPONSE_WRITABLE	1
#else
#define RESPONSE_WRITABLE	0
#endif

_Static_assert(BE_MVP_GSTAGE_LEAF_BYTES == (BE_U64_C(1) << LEAF_SHIFT),
	       "the leaf size is 2 MiB");
_Static_assert(BE_MVP_GSTAGE_PAGE_BYTES == (BE_U64_C(1) << PAGE_SHIFT),
	       "the channel leaf maps one 4 KiB page");
_Static_assert(BE_MVP_GSTAGE_ROOT_ENTRIES * PTE_BYTES == BE_MVP_ROOT_BYTES,
	       "the Sv39x4 root fills its 16 KiB");
_Static_assert(BE_MVP_GSTAGE_L1_ENTRIES * PTE_BYTES ==
	       BE_MVP_GSTAGE_L0_OFFSET - BE_MVP_GSTAGE_L1_OFFSET,
	       "the level-1 table fills one page");
_Static_assert(BE_MVP_GSTAGE_L0_ENTRIES * PTE_BYTES ==
	       BE_MVP_GSTAGE_SPARE_OFFSET - BE_MVP_GSTAGE_L0_OFFSET,
	       "the level-0 table fills one page");
_Static_assert(BE_MVP_GSTAGE_SPARE_OFFSET < BE_MVP_GSTAGE_POOL_BYTES,
	       "the pool holds the root, the level-1 and level-0 pages, and "
	       "spare bytes");
_Static_assert(BE_MVP_G0_LEVEL1_HPA ==
	       BE_MVP_G0_ROOT_HPA + BE_MVP_GSTAGE_L1_OFFSET &&
	       BE_MVP_G1_LEVEL1_HPA ==
	       BE_MVP_G1_ROOT_HPA + BE_MVP_GSTAGE_L1_OFFSET,
	       "each level-1 page sits where the layout puts it");
_Static_assert(BE_MVP_G0_LEVEL0_HPA ==
	       BE_MVP_G0_ROOT_HPA + BE_MVP_GSTAGE_L0_OFFSET &&
	       BE_MVP_G1_LEVEL0_HPA ==
	       BE_MVP_G1_ROOT_HPA + BE_MVP_GSTAGE_L0_OFFSET,
	       "each level-0 page sits where the layout puts it");
_Static_assert(BE_MVP_G0_VMID < BE_MVP_GSTAGE_VMID_LIMIT &&
	       BE_MVP_G1_VMID < BE_MVP_GSTAGE_VMID_LIMIT,
	       "each VMID fits hgatp.VMID");
_Static_assert(BE_MVP_CHANNELS_MAX == 1 && BE_MVP_DOMAINS == 2 &&
	       BE_MVP_CHANNEL_BYTES == BE_MVP_GSTAGE_PAGE_BYTES &&
	       BE_MVP_CHANNEL_HPA < BE_MVP_GSTAGE_PA_LIMIT,
	       "one channel, a 4 KiB leaf below 2^56, whose two endpoints are "
	       "the two domains");
_Static_assert(BE_MVP_PAGES_MAX >= 1 &&
	       BE_MVP_PAGES_MAX <= BE_MVP_GSTAGE_L0_ENTRIES &&
	       BE_MVP_SHARED_PAGES_BYTES ==
	       BE_MVP_PAGES_MAX * BE_MVP_GSTAGE_PAGE_BYTES &&
	       BE_MVP_PAGE_NONE >= BE_MVP_DOMAINS,
	       "the declared pages fit one level-0 page, and a page's absent "
	       "endpoint names no domain");

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
	return (pool_pa & (BE_MVP_GSTAGE_POOL_ALIGN - 1U)) == 0U &&
	       pool_pa < BE_MVP_GSTAGE_PA_LIMIT &&
	       BE_MVP_GSTAGE_POOL_BYTES <= BE_MVP_GSTAGE_PA_LIMIT - pool_pa;
}

/* Builder-side descriptor rules. */
static enum be_mvp_gstage_error
build_check(const struct be_mvp_gstage_desc *desc)
{
	be_u64 leaf_mask = BE_MVP_GSTAGE_LEAF_BYTES - 1U;

	if ((desc->gpa_base & leaf_mask) != 0U ||
	    (desc->hpa_base & leaf_mask) != 0U || desc->size == 0U ||
	    (desc->size & leaf_mask) != 0U ||
	    desc->gpa_base >= BE_MVP_GSTAGE_GPA_LIMIT ||
	    desc->size > BE_MVP_GSTAGE_GPA_LIMIT - desc->gpa_base ||
	    desc->size > BE_MVP_GSTAGE_GIB -
			 (desc->gpa_base & (BE_MVP_GSTAGE_GIB - 1U)) ||
	    desc->hpa_base >= BE_MVP_GSTAGE_PA_LIMIT ||
	    desc->size > BE_MVP_GSTAGE_PA_LIMIT - desc->hpa_base ||
	    !pool_placement_valid(desc->pool_pa) ||
	    desc->vmid >= BE_MVP_GSTAGE_VMID_LIMIT)
		return BE_MVP_GSTAGE_DESC;
	if (overlaps(desc->pool_pa, BE_MVP_GSTAGE_POOL_BYTES, desc->hpa_base,
		     desc->size))
		return BE_MVP_GSTAGE_POOL;
	return BE_MVP_GSTAGE_OK;
}

/*
 * The channel page's rules (struct be_mvp_gstage_root_page), which the builder
 * and the walker both apply: none, all zero; or one 4 KiB page, readable
 * and perhaps writable, never executable, in the window's root entry on a
 * level-1 entry the window does not use, below 2^56, over neither the
 * window nor the pool.
 */
static enum be_mvp_gstage_error
page_check(const struct be_mvp_gstage_desc *desc,
	   const struct be_mvp_gstage_root_page *page)
{
	be_u64 slot = page->gpa & ~(BE_MVP_GSTAGE_LEAF_BYTES - 1U);

	if (page->bytes == 0U)
		return (page->gpa | page->hpa | page->rights) == 0U ?
			       BE_MVP_GSTAGE_OK : BE_MVP_GSTAGE_PAGE;
	if (page->bytes != BE_MVP_GSTAGE_PAGE_BYTES ||
	    ((page->gpa | page->hpa) & (BE_MVP_GSTAGE_PAGE_BYTES - 1U)) != 0U ||
	    (page->rights != BE_MVP_GSTAGE_RIGHT_READ &&
	     page->rights != RIGHTS_READ_WRITE) ||
	    (page->gpa >> GIB_SHIFT) != (desc->gpa_base >> GIB_SHIFT) ||
	    overlaps(desc->gpa_base, desc->size, slot,
		     BE_MVP_GSTAGE_LEAF_BYTES) ||
	    page->hpa >= BE_MVP_GSTAGE_PA_LIMIT ||
	    overlaps(desc->hpa_base, desc->size, page->hpa,
		     BE_MVP_GSTAGE_PAGE_BYTES) ||
	    overlaps(desc->pool_pa, BE_MVP_GSTAGE_POOL_BYTES, page->hpa,
		     BE_MVP_GSTAGE_PAGE_BYTES))
		return BE_MVP_GSTAGE_PAGE;
	return BE_MVP_GSTAGE_OK;
}

/* A root without a channel page. */
static const struct be_mvp_gstage_root_page no_page = { 0U, 0U, 0U, 0U };

/* The root's one pointer to this pool's level-1 page, and the window's
 * 2 MiB leaves in it. */
static void write_window(const struct be_mvp_gstage_desc *desc, be_u8 *pool)
{
	be_u64 root_index = desc->gpa_base >> GIB_SHIFT;
	be_u64 l1_first = (desc->gpa_base >> LEAF_SHIFT) & L1_INDEX_MASK;
	be_u64 count = desc->size >> LEAF_SHIFT;
	be_u64 index;

	store_le64(pool + root_index * PTE_BYTES,
		   BE_MVP_PTE_V |
			   (((desc->pool_pa + BE_MVP_GSTAGE_L1_OFFSET) >>
			     PAGE_SHIFT) << BE_MVP_PTE_PPN_SHIFT));
	for (index = 0U; index < count; ++index)
		store_le64(pool + BE_MVP_GSTAGE_L1_OFFSET +
				   (l1_first + index) * PTE_BYTES,
			   BE_MVP_PTE_LEAF_FLAGS |
				   (((desc->hpa_base +
				      index * BE_MVP_GSTAGE_LEAF_BYTES) >>
				     PAGE_SHIFT) << BE_MVP_PTE_PPN_SHIFT));
}

/* The level-1 entry that points to this pool's level-0 page. */
static be_u64 level0_pointer(be_u64 pool_pa)
{
	return BE_MVP_PTE_V |
	       (((pool_pa + BE_MVP_GSTAGE_L0_OFFSET) >> PAGE_SHIFT)
		<< BE_MVP_PTE_PPN_SHIFT);
}

enum be_mvp_gstage_error
be_mvp_gstage_build_channel(const struct be_mvp_gstage_desc *desc,
			    const struct be_mvp_gstage_root_page *page,
			    be_u8 *pool, be_u64 pool_size)
{
	enum be_mvp_gstage_error error;
	be_u64 index;
	be_u64 flags;

	if (pool == (be_u8 *)0)
		return BE_MVP_GSTAGE_NULL;
	if (pool_size != BE_MVP_GSTAGE_POOL_BYTES)
		return BE_MVP_GSTAGE_POOL;
	for (index = 0U; index < BE_MVP_GSTAGE_POOL_BYTES; ++index)
		pool[index] = 0U;
	if (desc == (const struct be_mvp_gstage_desc *)0 ||
	    page == (const struct be_mvp_gstage_root_page *)0)
		return BE_MVP_GSTAGE_NULL;
	error = build_check(desc);
	if (error != BE_MVP_GSTAGE_OK)
		return error;
	error = page_check(desc, page);
	if (error != BE_MVP_GSTAGE_OK)
		return error;
	write_window(desc, pool);
	if (page->bytes == 0U)
		return BE_MVP_GSTAGE_OK;
	/* Level-1: a pointer to the level-0 page; level-0: the page's leaf. */
	flags = BE_MVP_PTE_V | BE_MVP_PTE_R | BE_MVP_PTE_U | BE_MVP_PTE_A |
		BUILDER_DEFECT;
	if ((page->rights & BE_MVP_GSTAGE_RIGHT_WRITE) != 0U)
		flags |= BE_MVP_PTE_W | BE_MVP_PTE_D;
	store_le64(pool + BE_MVP_GSTAGE_L1_OFFSET +
			   ((page->gpa >> LEAF_SHIFT) & L1_INDEX_MASK) *
				   PTE_BYTES,
		   level0_pointer(desc->pool_pa));
	store_le64(pool + BE_MVP_GSTAGE_L0_OFFSET +
			   ((page->gpa >> PAGE_SHIFT) & L0_INDEX_MASK) *
				   PTE_BYTES,
		   flags | ((page->hpa >> PAGE_SHIFT) << BE_MVP_PTE_PPN_SHIFT));
	return BE_MVP_GSTAGE_OK;
}

enum be_mvp_gstage_error
be_mvp_gstage_build(const struct be_mvp_gstage_desc *desc, be_u8 *pool,
		   be_u64 pool_size)
{
	return be_mvp_gstage_build_channel(desc, &no_page, pool, pool_size);
}

/*
 * The declared pages' rules (be_mvp_gstage_build_pages()), which the
 * builder and the walker both apply: one to BE_MVP_PAGES_MAX pages, each
 * one 4 KiB page in the window's root entry and the first page's 2 MiB
 * slot, which the window does not use, below 2^56, over neither the window
 * nor the pool, each domain's rights none, read, or read and write; and no
 * two pages at one GPA or on one HPA, which, for aligned 4 KiB pages, is
 * no two that overlap.
 */
static enum be_mvp_gstage_error
pages_rule(const struct be_mvp_gstage_desc *desc,
	   const struct be_mvp_gstage_page *pages, be_u64 count)
{
	be_u64 slot;
	be_u64 index;
	be_u64 other;
	be_u64 domain;

	if (count == 0U || count > BE_MVP_PAGES_MAX)
		return BE_MVP_GSTAGE_PAGE;
	slot = pages[0].gpa & ~(BE_MVP_GSTAGE_LEAF_BYTES - 1U);
	if (overlaps(desc->gpa_base, desc->size, slot,
		     BE_MVP_GSTAGE_LEAF_BYTES))
		return BE_MVP_GSTAGE_PAGE;
	for (index = 0U; index < count; ++index) {
		const struct be_mvp_gstage_page *page = &pages[index];

		if (page->bytes != BE_MVP_GSTAGE_PAGE_BYTES ||
		    ((page->gpa | page->hpa) &
		     (BE_MVP_GSTAGE_PAGE_BYTES - 1U)) != 0U ||
		    (page->gpa >> GIB_SHIFT) != (desc->gpa_base >> GIB_SHIFT) ||
		    (page->gpa & ~(BE_MVP_GSTAGE_LEAF_BYTES - 1U)) != slot ||
		    page->hpa >= BE_MVP_GSTAGE_PA_LIMIT ||
		    overlaps(desc->hpa_base, desc->size, page->hpa,
			     BE_MVP_GSTAGE_PAGE_BYTES) ||
		    overlaps(desc->pool_pa, BE_MVP_GSTAGE_POOL_BYTES,
			     page->hpa, BE_MVP_GSTAGE_PAGE_BYTES))
			return BE_MVP_GSTAGE_PAGE;
		for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
			if (page->rights[domain] != 0U &&
			    page->rights[domain] != BE_MVP_GSTAGE_RIGHT_READ &&
			    page->rights[domain] != RIGHTS_READ_WRITE)
				return BE_MVP_GSTAGE_PAGE;
		for (other = 0U; other < index; ++other)
			if (pages[other].gpa == page->gpa ||
			    pages[other].hpa == page->hpa)
				return BE_MVP_GSTAGE_PAGE;
	}
	return BE_MVP_GSTAGE_OK;
}

/*
 * The flags of the leaf the builder writes for one page in @domain's root:
 * none for no rights; V R U A, and W D for write. The two negative images'
 * defects apply here alone.
 */
static be_u64 page_flags(const struct be_mvp_gstage_page *page,
			 be_u64 domain)
{
	be_u64 rights = page->rights[domain];
	be_u64 flags;

	if (SECRET_SHARED && page->kind == BE_MVP_PAGE_SECRET && rights == 0U)
		rights = BE_MVP_GSTAGE_RIGHT_READ;
	if (rights == 0U)
		return 0U;
	flags = BE_MVP_PTE_V | BE_MVP_PTE_R | BE_MVP_PTE_U | BE_MVP_PTE_A;
	if ((rights & BE_MVP_GSTAGE_RIGHT_WRITE) != 0U ||
	    (RESPONSE_WRITABLE && page->kind == BE_MVP_PAGE_CHANNEL &&
	     domain == 0U && page->reader == 0U))
		flags |= BE_MVP_PTE_W | BE_MVP_PTE_D;
	return flags;
}

enum be_mvp_gstage_error
be_mvp_gstage_build_pages(const struct be_mvp_gstage_desc *desc,
			  const struct be_mvp_gstage_page *pages, be_u64 count,
			  be_u64 domain, be_u8 *pool, be_u64 pool_size)
{
	enum be_mvp_gstage_error error;
	be_u64 mapped = 0U;
	be_u64 index;

	if (pool == (be_u8 *)0)
		return BE_MVP_GSTAGE_NULL;
	if (pool_size != BE_MVP_GSTAGE_POOL_BYTES)
		return BE_MVP_GSTAGE_POOL;
	for (index = 0U; index < BE_MVP_GSTAGE_POOL_BYTES; ++index)
		pool[index] = 0U;
	if (desc == (const struct be_mvp_gstage_desc *)0 ||
	    pages == (const struct be_mvp_gstage_page *)0)
		return BE_MVP_GSTAGE_NULL;
	error = build_check(desc);
	if (error != BE_MVP_GSTAGE_OK)
		return error;
	if (domain >= BE_MVP_DOMAINS)
		return BE_MVP_GSTAGE_PAGE;
	error = pages_rule(desc, pages, count);
	if (error != BE_MVP_GSTAGE_OK)
		return error;
	write_window(desc, pool);
	/* Level-0: each page's leaf for this root; level-1: one pointer. */
	for (index = 0U; index < count; ++index) {
		be_u64 flags = page_flags(&pages[index], domain);

		if (flags == 0U)
			continue;
		store_le64(pool + BE_MVP_GSTAGE_L0_OFFSET +
				   ((pages[index].gpa >> PAGE_SHIFT) &
				    L0_INDEX_MASK) * PTE_BYTES,
			   flags | ((pages[index].hpa >> PAGE_SHIFT)
				    << BE_MVP_PTE_PPN_SHIFT));
		mapped = 1U;
	}
	if (mapped != 0U)
		store_le64(pool + BE_MVP_GSTAGE_L1_OFFSET +
				   ((pages[0].gpa >> LEAF_SHIFT) &
				    L1_INDEX_MASK) * PTE_BYTES,
			   level0_pointer(desc->pool_pa));
	return BE_MVP_GSTAGE_OK;
}

/* Walker: exactly one root entry, a pointer to this pool's level-1 page. */
static enum be_mvp_gstage_error walk_root(const be_u8 *pool, be_u64 pool_pa,
					 be_u64 *slot)
{
	be_u64 index;
	be_u64 found = NO_ENTRY;

	for (index = 0U; index < BE_MVP_GSTAGE_ROOT_ENTRIES; ++index) {
		be_u64 pte = load_le64(pool + index * PTE_BYTES);

		if (pte == 0U)
			continue;
		if (found != NO_ENTRY || (pte & BE_MVP_PTE_V) == 0U ||
		    (pte & POINTER_FORBIDDEN) != 0U ||
		    (pte & PTE_HIGH_MASK) != 0U ||
		    ((pte >> BE_MVP_PTE_PPN_SHIFT) & BE_MVP_PTE_PPN_MASK) !=
			    (pool_pa + BE_MVP_GSTAGE_L1_OFFSET) >> PAGE_SHIFT)
			return BE_MVP_GSTAGE_ROOT;
		found = index;
	}
	if (found == NO_ENTRY)
		return BE_MVP_GSTAGE_ROOT;
	*slot = found;
	return BE_MVP_GSTAGE_OK;
}

/*
 * Walker: one contiguous linear run of exact 2 MiB leaves, zero elsewhere
 * but at @pointer, the index of the one checked channel pointer, if any.
 */
static enum be_mvp_gstage_error walk_l1(const be_u8 *pool, be_u64 pointer,
				       be_u64 *first, be_u64 *leaves,
				       be_u64 *hpa_base)
{
	be_u64 index;
	be_u64 start = NO_ENTRY;
	be_u64 count = 0U;
	be_u64 base_ppn = 0U;

	for (index = 0U; index < BE_MVP_GSTAGE_L1_ENTRIES; ++index) {
		be_u64 pte = load_le64(pool + BE_MVP_GSTAGE_L1_OFFSET +
				       index * PTE_BYTES);
		be_u64 ppn = (pte >> BE_MVP_PTE_PPN_SHIFT) & BE_MVP_PTE_PPN_MASK;

		if (pte == 0U || index == pointer)
			continue;
		if ((pte & LOW_FLAGS_MASK) != BE_MVP_PTE_LEAF_FLAGS ||
		    (pte & PTE_HIGH_MASK) != 0U ||
		    (ppn & LEAF_PPN_ALIGN_MASK) != 0U)
			return BE_MVP_GSTAGE_L1;
		if (start == NO_ENTRY) {
			start = index;
			base_ppn = ppn;
		} else if (index != start + count ||
			   ppn != base_ppn + count * LEAF_PPN_STEP) {
			return BE_MVP_GSTAGE_L1;
		}
		++count;
	}
	if (count == 0U)
		return BE_MVP_GSTAGE_L1;
	*first = start;
	*leaves = count;
	*hpa_base = base_ppn << PAGE_SHIFT;
	return BE_MVP_GSTAGE_OK;
}

/*
 * Walker: in the level-0 page, exactly one leaf, at @index, onto the page
 * whose PTE PPN field is @ppn_field, with the flags V R U A and W D both or
 * neither and no other bit; zero everywhere else.
 */
static enum be_mvp_gstage_error walk_l0(const be_u8 *pool, be_u64 index,
				       be_u64 ppn_field, be_u64 *leaf)
{
	be_u64 entry;

	*leaf = 0U;
	for (entry = 0U; entry < BE_MVP_GSTAGE_L0_ENTRIES; ++entry) {
		be_u64 pte = load_le64(pool + BE_MVP_GSTAGE_L0_OFFSET +
				       entry * PTE_BYTES);

		if (pte == 0U)
			continue;
		if (entry != index || (pte != (ppn_field | CHANNEL_READ) &&
				       pte != (ppn_field | CHANNEL_READ_WRITE)))
			return BE_MVP_GSTAGE_L0;
		*leaf = pte;
	}
	return *leaf != 0U ? BE_MVP_GSTAGE_OK : BE_MVP_GSTAGE_L0;
}

/*
 * Walker, after the level-1 and level-0 pages: zero in every spare byte,
 * the level-0 page's included when no pointer named it (@pointed 0); the
 * window derived from the level-1 run equal to @desc's; then the map.
 */
static enum be_mvp_gstage_error
walk_window(const struct be_mvp_gstage_desc *desc, const be_u8 *pool,
	    be_u64 slot, be_u64 first, be_u64 leaves, be_u64 hpa_base,
	    int pointed, struct be_mvp_gstage_map *map)
{
	be_u64 gpa_base = (slot << GIB_SHIFT) | (first << LEAF_SHIFT);
	be_u64 size = leaves << LEAF_SHIFT;
	be_u64 index;

	for (index = pointed ? BE_MVP_GSTAGE_SPARE_OFFSET :
			       BE_MVP_GSTAGE_L0_OFFSET;
	     index < BE_MVP_GSTAGE_POOL_BYTES; ++index)
		if (pool[index] != 0U)
			return BE_MVP_GSTAGE_SPARE;
	if (gpa_base != desc->gpa_base || hpa_base != desc->hpa_base ||
	    size != desc->size || hpa_base >= BE_MVP_GSTAGE_PA_LIMIT ||
	    size > BE_MVP_GSTAGE_PA_LIMIT - hpa_base ||
	    overlaps(desc->pool_pa, BE_MVP_GSTAGE_POOL_BYTES, hpa_base, size))
		return BE_MVP_GSTAGE_MISMATCH;
	map->hgatp = BE_MVP_GSTAGE_HGATP_SV39X4 |
		     (desc->vmid << BE_MVP_GSTAGE_VMID_SHIFT) |
		     (desc->pool_pa >> PAGE_SHIFT);
	map->gpa_base = gpa_base;
	map->hpa_base = hpa_base;
	map->size = size;
	map->leaves = leaves;
	map->pool_pa = desc->pool_pa;
	map->vmid = desc->vmid;
	map->hart = desc->hart;
	return BE_MVP_GSTAGE_OK;
}

enum be_mvp_gstage_error
be_mvp_gstage_walk_channel(const struct be_mvp_gstage_desc *desc,
			   const struct be_mvp_gstage_root_page *page,
			   const be_u8 *pool, be_u64 pool_size,
			   struct be_mvp_gstage_map *map,
			   struct be_mvp_gstage_leaf *leaf)
{
	enum be_mvp_gstage_error error;
	be_u64 slot = 0U;
	be_u64 first = 0U;
	be_u64 leaves = 0U;
	be_u64 hpa_base = 0U;
	be_u64 pointer = NO_ENTRY;
	be_u64 pte = 0U;
	be_u64 index;

	if (map != (struct be_mvp_gstage_map *)0)
		*map = (struct be_mvp_gstage_map){ 0U, 0U, 0U, 0U, 0U, 0U, 0U,
						   0U };
	if (leaf != (struct be_mvp_gstage_leaf *)0)
		*leaf = (struct be_mvp_gstage_leaf){ 0U, 0U, 0U, 0U, 0U };
	if (map == (struct be_mvp_gstage_map *)0 ||
	    leaf == (struct be_mvp_gstage_leaf *)0 ||
	    desc == (const struct be_mvp_gstage_desc *)0 ||
	    page == (const struct be_mvp_gstage_root_page *)0 ||
	    pool == (const be_u8 *)0)
		return BE_MVP_GSTAGE_NULL;
	if (pool_size != BE_MVP_GSTAGE_POOL_BYTES ||
	    !pool_placement_valid(desc->pool_pa))
		return BE_MVP_GSTAGE_POOL;
	if (desc->vmid >= BE_MVP_GSTAGE_VMID_LIMIT)
		return BE_MVP_GSTAGE_DESC;
	error = page_check(desc, page);
	if (error != BE_MVP_GSTAGE_OK)
		return error;
	error = walk_root(pool, desc->pool_pa, &slot);
	if (error != BE_MVP_GSTAGE_OK)
		return error;
	/* The one pointer accepted: the declared page's, onto this pool. */
	index = (page->gpa >> LEAF_SHIFT) & L1_INDEX_MASK;
	if (page->bytes != 0U && (page->gpa >> GIB_SHIFT) == slot &&
	    load_le64(pool + BE_MVP_GSTAGE_L1_OFFSET + index * PTE_BYTES) ==
		    (BE_MVP_PTE_V |
		     (((desc->pool_pa + BE_MVP_GSTAGE_L0_OFFSET) >> PAGE_SHIFT)
		      << BE_MVP_PTE_PPN_SHIFT)))
		pointer = index;
	error = walk_l1(pool, pointer, &first, &leaves, &hpa_base);
	if (error != BE_MVP_GSTAGE_OK)
		return error;
	if (pointer != NO_ENTRY) {
		error = walk_l0(pool, (page->gpa >> PAGE_SHIFT) & L0_INDEX_MASK,
				(page->hpa >> PAGE_SHIFT)
					<< BE_MVP_PTE_PPN_SHIFT,
				&pte);
		if (error != BE_MVP_GSTAGE_OK)
			return error;
	}
	error = walk_window(desc, pool, slot, first, leaves, hpa_base,
			    pointer != NO_ENTRY, map);
	if (error != BE_MVP_GSTAGE_OK)
		return error;
	if (pointer != NO_ENTRY) {
		leaf->gpa = (slot << GIB_SHIFT) | (pointer << LEAF_SHIFT) |
			    (((page->gpa >> PAGE_SHIFT) & L0_INDEX_MASK)
			     << PAGE_SHIFT);
		leaf->hpa = ((pte >> BE_MVP_PTE_PPN_SHIFT) &
			     BE_MVP_PTE_PPN_MASK) << PAGE_SHIFT;
		leaf->bytes = BE_MVP_GSTAGE_PAGE_BYTES;
		leaf->pte = pte;
		leaf->l0_pa = desc->pool_pa + BE_MVP_GSTAGE_L0_OFFSET;
	}
	return BE_MVP_GSTAGE_OK;
}

enum be_mvp_gstage_error
be_mvp_gstage_walk(const struct be_mvp_gstage_desc *desc, const be_u8 *pool,
		  be_u64 pool_size, struct be_mvp_gstage_map *map)
{
	struct be_mvp_gstage_leaf leaf;

	return be_mvp_gstage_walk_channel(desc, &no_page, pool, pool_size, map,
					  &leaf);
}

/*
 * Walker: in the level-0 page, at least one leaf, each at a declared
 * page's level-0 index, onto that page's HPA, with the flags V R U A and
 * W D both or neither and no other bit; zero everywhere else. @ptes gets
 * each page's leaf, 0 for none.
 */
static enum be_mvp_gstage_error
walk_l0_pages(const be_u8 *pool, const struct be_mvp_gstage_page *pages,
	      be_u64 count, be_u64 *ptes)
{
	be_u64 found = 0U;
	be_u64 entry;
	be_u64 index;

	for (entry = 0U; entry < BE_MVP_GSTAGE_L0_ENTRIES; ++entry) {
		be_u64 pte = load_le64(pool + BE_MVP_GSTAGE_L0_OFFSET +
				       entry * PTE_BYTES);
		be_u64 ppn_field;

		if (pte == 0U)
			continue;
		for (index = 0U; index < count; ++index)
			if (((pages[index].gpa >> PAGE_SHIFT) &
			     L0_INDEX_MASK) == entry)
				break;
		if (index == count)
			return BE_MVP_GSTAGE_L0;
		ppn_field = (pages[index].hpa >> PAGE_SHIFT)
			    << BE_MVP_PTE_PPN_SHIFT;
		if (pte != (ppn_field | CHANNEL_READ) &&
		    pte != (ppn_field | CHANNEL_READ_WRITE))
			return BE_MVP_GSTAGE_L0;
		ptes[index] = pte;
		++found;
	}
	return found != 0U ? BE_MVP_GSTAGE_OK : BE_MVP_GSTAGE_L0;
}

enum be_mvp_gstage_error
be_mvp_gstage_walk_pages(const struct be_mvp_gstage_desc *desc,
			 const struct be_mvp_gstage_page *pages, be_u64 count,
			 const be_u8 *pool, be_u64 pool_size,
			 struct be_mvp_gstage_map *map,
			 struct be_mvp_gstage_leaves *leaves)
{
	enum be_mvp_gstage_error error;
	be_u64 ptes[BE_MVP_PAGES_MAX];
	be_u64 slot = 0U;
	be_u64 first = 0U;
	be_u64 run = 0U;
	be_u64 hpa_base = 0U;
	be_u64 pointer = NO_ENTRY;
	be_u64 index;

	if (map != (struct be_mvp_gstage_map *)0)
		*map = (struct be_mvp_gstage_map){ 0U, 0U, 0U, 0U, 0U, 0U, 0U,
						   0U };
	for (index = 0U; index < BE_MVP_PAGES_MAX; ++index) {
		ptes[index] = 0U;
		if (leaves != (struct be_mvp_gstage_leaves *)0)
			leaves->page[index] = (struct be_mvp_gstage_leaf){
				0U, 0U, 0U, 0U, 0U };
	}
	if (map == (struct be_mvp_gstage_map *)0 ||
	    leaves == (struct be_mvp_gstage_leaves *)0 ||
	    desc == (const struct be_mvp_gstage_desc *)0 ||
	    pages == (const struct be_mvp_gstage_page *)0 ||
	    pool == (const be_u8 *)0)
		return BE_MVP_GSTAGE_NULL;
	if (pool_size != BE_MVP_GSTAGE_POOL_BYTES ||
	    !pool_placement_valid(desc->pool_pa))
		return BE_MVP_GSTAGE_POOL;
	if (desc->vmid >= BE_MVP_GSTAGE_VMID_LIMIT)
		return BE_MVP_GSTAGE_DESC;
	error = pages_rule(desc, pages, count);
	if (error != BE_MVP_GSTAGE_OK)
		return error;
	error = walk_root(pool, desc->pool_pa, &slot);
	if (error != BE_MVP_GSTAGE_OK)
		return error;
	/* The one pointer accepted: the pages' slot's, onto this pool. */
	index = (pages[0].gpa >> LEAF_SHIFT) & L1_INDEX_MASK;
	if ((pages[0].gpa >> GIB_SHIFT) == slot &&
	    load_le64(pool + BE_MVP_GSTAGE_L1_OFFSET + index * PTE_BYTES) ==
		    (BE_MVP_PTE_V |
		     (((desc->pool_pa + BE_MVP_GSTAGE_L0_OFFSET) >> PAGE_SHIFT)
		      << BE_MVP_PTE_PPN_SHIFT)))
		pointer = index;
	error = walk_l1(pool, pointer, &first, &run, &hpa_base);
	if (error != BE_MVP_GSTAGE_OK)
		return error;
	if (pointer != NO_ENTRY) {
		error = walk_l0_pages(pool, pages, count, ptes);
		if (error != BE_MVP_GSTAGE_OK)
			return error;
	}
	error = walk_window(desc, pool, slot, first, run, hpa_base,
			    pointer != NO_ENTRY, map);
	if (error != BE_MVP_GSTAGE_OK)
		return error;
	for (index = 0U; index < count; ++index) {
		struct be_mvp_gstage_leaf *leaf = &leaves->page[index];

		if (ptes[index] == 0U)
			continue;
		leaf->gpa = (slot << GIB_SHIFT) | (pointer << LEAF_SHIFT) |
			    (((pages[index].gpa >> PAGE_SHIFT) & L0_INDEX_MASK)
			     << PAGE_SHIFT);
		leaf->hpa = ((ptes[index] >> BE_MVP_PTE_PPN_SHIFT) &
			     BE_MVP_PTE_PPN_MASK) << PAGE_SHIFT;
		leaf->bytes = BE_MVP_GSTAGE_PAGE_BYTES;
		leaf->pte = ptes[index];
		leaf->l0_pa = desc->pool_pa + BE_MVP_GSTAGE_L0_OFFSET;
	}
	return BE_MVP_GSTAGE_OK;
}

/* A map the walker filled: a nonzero size, and hgatp in Sv39x4 mode. */
static int walked(const struct be_mvp_gstage_map *map)
{
	return map->size != 0U &&
	       (map->hgatp >> 60) == (BE_MVP_GSTAGE_HGATP_SV39X4 >> 60);
}

/* M0's pair rules: two walked, disjoint roots for two domain harts. */
static int pair_refused(const struct be_mvp_gstage_map *first,
			const struct be_mvp_gstage_map *second)
{
	return !walked(first) || !walked(second) || first->vmid == 0U ||
	       second->vmid == 0U || first->vmid == second->vmid ||
	       first->hart == second->hart ||
	       first->hart == BE_MVP_CONTROL_HART ||
	       second->hart == BE_MVP_CONTROL_HART ||
	       first->hgatp == second->hgatp ||
	       overlaps(first->pool_pa, BE_MVP_GSTAGE_POOL_BYTES,
			second->pool_pa, BE_MVP_GSTAGE_POOL_BYTES) ||
	       overlaps(first->hpa_base, first->size, second->hpa_base,
			second->size) ||
	       overlaps(first->hpa_base, first->size, second->pool_pa,
			BE_MVP_GSTAGE_POOL_BYTES) ||
	       overlaps(second->hpa_base, second->size, first->pool_pa,
			BE_MVP_GSTAGE_POOL_BYTES);
}

enum be_mvp_gstage_error
be_mvp_gstage_pair_check(const struct be_mvp_gstage_map *first,
			const struct be_mvp_gstage_map *second)
{
	if (first == (const struct be_mvp_gstage_map *)0 ||
	    second == (const struct be_mvp_gstage_map *)0)
		return BE_MVP_GSTAGE_NULL;
	if (pair_refused(first, second))
		return BE_MVP_GSTAGE_PAIR;
	return BE_MVP_GSTAGE_OK;
}

/*
 * The sealed record: all zero; or one 4 KiB page, below 2^41 as a GPA and
 * 2^56 as an HPA, between two distinct domains, one writer that reads and
 * writes and one reader that reads.
 */
static int record_valid(const struct be_mvp_gstage_channel *record)
{
	if (record->bytes == 0U)
		return (record->gpa | record->hpa | record->writer_domain |
			record->reader_domain | record->writer_rights |
			record->reader_rights) == 0U;
	return record->bytes == BE_MVP_GSTAGE_PAGE_BYTES &&
	       (record->gpa & (BE_MVP_GSTAGE_PAGE_BYTES - 1U)) == 0U &&
	       (record->hpa & (BE_MVP_GSTAGE_PAGE_BYTES - 1U)) == 0U &&
	       record->gpa < BE_MVP_GSTAGE_GPA_LIMIT &&
	       record->hpa < BE_MVP_GSTAGE_PA_LIMIT &&
	       record->writer_domain < BE_MVP_DOMAINS &&
	       record->reader_domain < BE_MVP_DOMAINS &&
	       record->writer_domain != record->reader_domain &&
	       record->writer_rights ==
		       (BE_MVP_GSTAGE_RIGHT_READ | BE_MVP_GSTAGE_RIGHT_WRITE) &&
	       record->reader_rights == BE_MVP_GSTAGE_RIGHT_READ;
}

/*
 * The leaf the record declares for one endpoint, by the authority report's
 * table (map V U A, read R, write W D): the check's own derivation, which
 * shares nothing with the builder's.
 */
static be_u64 declared_leaf(const struct be_mvp_gstage_channel *record,
			    be_u64 rights)
{
	be_u64 pte = BE_MVP_PTE_V | BE_MVP_PTE_U | BE_MVP_PTE_A;

	if ((rights & BE_MVP_GSTAGE_RIGHT_READ) != 0U)
		pte |= BE_MVP_PTE_R;
	if ((rights & BE_MVP_GSTAGE_RIGHT_WRITE) != 0U)
		pte |= BE_MVP_PTE_W | BE_MVP_PTE_D;
	return pte | ((record->hpa >> PAGE_SHIFT) << BE_MVP_PTE_PPN_SHIFT);
}

enum be_mvp_gstage_error
be_mvp_gstage_channel_check(const struct be_mvp_gstage_map *maps,
			    const struct be_mvp_gstage_leaf *leaves,
			    const struct be_mvp_gstage_channel *record,
			    struct be_mvp_gstage_refusal *refusal)
{
	be_u64 domain;

	if (refusal == (struct be_mvp_gstage_refusal *)0)
		return BE_MVP_GSTAGE_NULL;
	*refusal = (struct be_mvp_gstage_refusal){ BE_MVP_DOMAINS, 0U, 0U,
						   0U, 0U };
	if (maps == (const struct be_mvp_gstage_map *)0 ||
	    leaves == (const struct be_mvp_gstage_leaf *)0 ||
	    record == (const struct be_mvp_gstage_channel *)0)
		return BE_MVP_GSTAGE_NULL;
	if (pair_refused(&maps[0], &maps[1]))
		return BE_MVP_GSTAGE_PAIR;
	if (!record_valid(record))
		return BE_MVP_GSTAGE_CHANNEL;
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		const struct be_mvp_gstage_map *map = &maps[domain];
		const struct be_mvp_gstage_leaf *leaf = &leaves[domain];
		be_u64 declared = 0U;
		be_u64 l0_pa = 0U;

		if (record->bytes != 0U) {
			be_u64 rights = domain == record->writer_domain ?
						record->writer_rights :
						record->reader_rights;

			declared = declared_leaf(record, rights);
			l0_pa = map->pool_pa + BE_MVP_GSTAGE_L0_OFFSET;
		}
		/* No window over the page, nor the page over a pool; then the
		 * leaf exactly as declared, or no leaf when none is. */
		if ((record->bytes != 0U &&
		     (overlaps(map->hpa_base, map->size, record->hpa,
			       record->bytes) ||
		      overlaps(map->gpa_base, map->size, record->gpa,
			       record->bytes) ||
		      overlaps(map->pool_pa, BE_MVP_GSTAGE_POOL_BYTES,
			       record->hpa, record->bytes))) ||
		    leaf->gpa != record->gpa || leaf->hpa != record->hpa ||
		    leaf->bytes != record->bytes || leaf->pte != declared ||
		    leaf->l0_pa != l0_pa) {
			refusal->domain = domain;
			refusal->hart = map->hart;
			refusal->walked = leaf->pte;
			refusal->declared = declared;
			return BE_MVP_GSTAGE_CHANNEL;
		}
	}
	return BE_MVP_GSTAGE_OK;
}

/*
 * The rights a sealed page gives one domain, from its kind and endpoints
 * alone: a channel's writer reads and writes, and its reader, or a secret
 * page's, reads; any other domain has none.
 */
static be_u64 endpoint_rights(const struct be_mvp_gstage_page *page,
			      be_u64 domain)
{
	if (page->kind == BE_MVP_PAGE_CHANNEL && domain == page->writer)
		return BE_MVP_GSTAGE_RIGHT_READ | BE_MVP_GSTAGE_RIGHT_WRITE;
	if (domain == page->reader)
		return BE_MVP_GSTAGE_RIGHT_READ;
	return 0U;
}

/*
 * The sealed pages: each one 4 KiB page, below 2^41 as a GPA and 2^56 as
 * an HPA, at its own GPA and on its own HPA; a channel between two
 * distinct domains, or a secret page with no writer and one reader; each
 * domain's rights those of its endpoints.
 *
 * Return: the first page that breaks a rule, or @count.
 */
static be_u64 pages_refused(const struct be_mvp_gstage_page *pages,
			    be_u64 count)
{
	be_u64 index;
	be_u64 other;
	be_u64 domain;

	for (index = 0U; index < count; ++index) {
		const struct be_mvp_gstage_page *page = &pages[index];
		int valid = page->bytes == BE_MVP_GSTAGE_PAGE_BYTES &&
			    ((page->gpa | page->hpa) &
			     (BE_MVP_GSTAGE_PAGE_BYTES - 1U)) == 0U &&
			    page->gpa < BE_MVP_GSTAGE_GPA_LIMIT &&
			    page->hpa < BE_MVP_GSTAGE_PA_LIMIT &&
			    page->reader < BE_MVP_DOMAINS;

		if (page->kind == BE_MVP_PAGE_CHANNEL)
			valid = valid && page->writer < BE_MVP_DOMAINS &&
				page->writer != page->reader;
		else
			valid = valid && page->kind == BE_MVP_PAGE_SECRET &&
				page->writer == BE_MVP_PAGE_NONE;
		for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
			if (page->rights[domain] !=
			    endpoint_rights(page, domain))
				valid = 0;
		for (other = 0U; other < index; ++other)
			if (pages[other].gpa == page->gpa ||
			    pages[other].hpa == page->hpa)
				valid = 0;
		if (!valid)
			return index;
	}
	return count;
}

/*
 * The leaf a sealed page declares for one domain's root, by the authority
 * report's table (map V U A, read R, write W D), or none for no rights:
 * the check's own derivation, which shares nothing with the builder's.
 */
static be_u64 declared_page_leaf(const struct be_mvp_gstage_page *page,
				 be_u64 domain)
{
	be_u64 rights = page->rights[domain];
	be_u64 pte = BE_MVP_PTE_V | BE_MVP_PTE_U | BE_MVP_PTE_A;

	if (rights == 0U)
		return 0U;
	if ((rights & BE_MVP_GSTAGE_RIGHT_READ) != 0U)
		pte |= BE_MVP_PTE_R;
	if ((rights & BE_MVP_GSTAGE_RIGHT_WRITE) != 0U)
		pte |= BE_MVP_PTE_W | BE_MVP_PTE_D;
	return pte | ((page->hpa >> PAGE_SHIFT) << BE_MVP_PTE_PPN_SHIFT);
}

static int leaf_empty(const struct be_mvp_gstage_leaf *leaf)
{
	return (leaf->gpa | leaf->hpa | leaf->bytes | leaf->pte |
		leaf->l0_pa) == 0U;
}

enum be_mvp_gstage_error
be_mvp_gstage_page_check(const struct be_mvp_gstage_map *maps,
			 const struct be_mvp_gstage_leaves *leaves,
			 const struct be_mvp_gstage_page *pages, be_u64 count,
			 struct be_mvp_gstage_refusal *refusal)
{
	be_u64 index;
	be_u64 domain;

	if (refusal == (struct be_mvp_gstage_refusal *)0)
		return BE_MVP_GSTAGE_NULL;
	*refusal = (struct be_mvp_gstage_refusal){ BE_MVP_DOMAINS, 0U, 0U,
						   0U, BE_MVP_PAGES_MAX };
	if (maps == (const struct be_mvp_gstage_map *)0 ||
	    leaves == (const struct be_mvp_gstage_leaves *)0 ||
	    pages == (const struct be_mvp_gstage_page *)0)
		return BE_MVP_GSTAGE_NULL;
	if (pair_refused(&maps[0], &maps[1]))
		return BE_MVP_GSTAGE_PAIR;
	if (count == 0U || count > BE_MVP_PAGES_MAX)
		return BE_MVP_GSTAGE_PAGES;
	index = pages_refused(pages, count);
	if (index < count) {
		refusal->page = index;
		return BE_MVP_GSTAGE_PAGES;
	}
	for (index = 0U; index < BE_MVP_PAGES_MAX; ++index) {
		for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
			const struct be_mvp_gstage_map *map = &maps[domain];
			const struct be_mvp_gstage_leaf *leaf =
				&leaves[domain].page[index];
			be_u64 declared = 0U;
			int refused;

			/* Beyond the declared pages, no leaf at all. */
			if (index >= count) {
				refused = !leaf_empty(leaf);
			} else {
				const struct be_mvp_gstage_page *page =
					&pages[index];

				declared = declared_page_leaf(page, domain);
				/* No window over the page, nor the page over
				 * a pool; then the leaf exactly as declared,
				 * or none when none is. */
				refused = overlaps(map->hpa_base, map->size,
						   page->hpa, page->bytes) ||
					  overlaps(map->gpa_base, map->size,
						   page->gpa, page->bytes) ||
					  overlaps(map->pool_pa,
						   BE_MVP_GSTAGE_POOL_BYTES,
						   page->hpa, page->bytes) ||
					  (declared == 0U ? !leaf_empty(leaf) :
					   leaf->gpa != page->gpa ||
					   leaf->hpa != page->hpa ||
					   leaf->bytes != page->bytes ||
					   leaf->pte != declared ||
					   leaf->l0_pa !=
						   map->pool_pa +
						   BE_MVP_GSTAGE_L0_OFFSET);
			}
			if (refused) {
				refusal->domain = domain;
				refusal->hart = map->hart;
				refusal->walked = leaf->pte;
				refusal->declared = declared;
				refusal->page = index;
				return BE_MVP_GSTAGE_PAGES;
			}
		}
	}
	return BE_MVP_GSTAGE_OK;
}

int be_mvp_gstage_translate(const struct be_mvp_gstage_map *map, be_u64 gpa,
			   be_u64 length, be_u64 *hpa)
{
	be_u64 offset;

	if (map == (const struct be_mvp_gstage_map *)0 ||
	    hpa == (be_u64 *)0 || length == 0U || map->size == 0U ||
	    gpa < map->gpa_base)
		return 0;
	offset = gpa - map->gpa_base;
	if (offset >= map->size || length > map->size - offset)
		return 0;
	*hpa = map->hpa_base + offset;
	return 1;
}
