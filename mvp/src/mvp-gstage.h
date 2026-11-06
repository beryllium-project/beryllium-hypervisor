/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP G-stage contract: one Sv39x4 root per domain, each in its
 *          own B6-shaped 32 KiB pool, mapping one linear guest-RAM window
 *          with 2 MiB leaves through one level-1 table and, in a scenario
 *          with a channel, the one 4 KiB channel page through one level-0
 *          page, with that root's own rights, under the domain's own VMID,
 *          for the domain hart that installs it; a builder, an independent
 *          re-walker that derives the window and the channel leaf from each
 *          pool's bytes, the check that two walked roots share no page,
 *          window, VMID, or hart but the declared channel page with its
 *          declared rights, and the guest-range translation the SBI core
 *          uses for DBCN, which serves the window only. For a scenario with
 *          pages (planning/mvp-m2-plan.md, Q1, "G-stage and VMIDs"), the
 *          same for up to three declared 4 KiB pages, channels and a secret
 *          page, each with its own rights per domain, through the same
 *          level-0 page: their builder, walker, and page check.
 * Trust:   restricted C. No CSR, fence, or I/O: each pool is reached only
 *          through bounded little-endian byte helpers, and each domain hart
 *          installs its walked hgatp once through the accepted R3 function.
 * Scope:   the MVP line (planning/mvp-m0-plan.md, planning/mvp-m1-plan.md,
 *          and planning/mvp-m2-plan.md, "G-stage and VMIDs"). Per root: one
 *          level-1 table and at most one level-0 page, which holds the one
 *          channel leaf or the leaves of the declared pages in one 2 MiB
 *          slot; per-page rights on those leaves only.
 */

#ifndef BE_MVP_GSTAGE_H
#define BE_MVP_GSTAGE_H

#include <be/types.h>

#include "mvp-layout.h"

/*
 * Sv39x4 geometry: 2 MiB leaves in one level-1 table under a 16 KiB root;
 * the channel's 4 KiB leaf in the level-0 page after the level-1 page; the
 * pool's bytes after the level-0 page are spare and stay zero.
 */
#define BE_MVP_GSTAGE_LEAF_BYTES	BE_MVP_GUEST_LEAF_BYTES
#define BE_MVP_GSTAGE_PAGE_BYTES	BE_U64_C(0x1000)
#define BE_MVP_GSTAGE_GIB		(BE_U64_C(1) << 30)
#define BE_MVP_GSTAGE_GPA_LIMIT		(BE_U64_C(1) << 41)
#define BE_MVP_GSTAGE_PA_LIMIT		(BE_U64_C(1) << 56)
#define BE_MVP_GSTAGE_POOL_BYTES	BE_MVP_GUEST_POOL_BYTES
#define BE_MVP_GSTAGE_POOL_ALIGN	BE_U64_C(0x4000)
#define BE_MVP_GSTAGE_L1_OFFSET		BE_MVP_ROOT_BYTES
#define BE_MVP_GSTAGE_L0_OFFSET		(BE_MVP_ROOT_BYTES + BE_U64_C(0x1000))
#define BE_MVP_GSTAGE_SPARE_OFFSET	(BE_MVP_ROOT_BYTES + BE_U64_C(0x2000))
#define BE_MVP_GSTAGE_ROOT_ENTRIES	2048U
#define BE_MVP_GSTAGE_L1_ENTRIES	512U
#define BE_MVP_GSTAGE_L0_ENTRIES	512U
#define BE_MVP_GSTAGE_HGATP_SV39X4	(BE_U64_C(8) << 60)
/* hgatp.VMID: bits 44-57, 14 bits on QEMU and on K3. */
#define BE_MVP_GSTAGE_VMID_SHIFT	44U
#define BE_MVP_GSTAGE_VMID_LIMIT	(BE_U64_C(1) << 14)

/* G-stage PTE bits. */
#define BE_MVP_PTE_V			(BE_U64_C(1) << 0)
#define BE_MVP_PTE_R			(BE_U64_C(1) << 1)
#define BE_MVP_PTE_W			(BE_U64_C(1) << 2)
#define BE_MVP_PTE_X			(BE_U64_C(1) << 3)
#define BE_MVP_PTE_U			(BE_U64_C(1) << 4)
#define BE_MVP_PTE_G			(BE_U64_C(1) << 5)
#define BE_MVP_PTE_A			(BE_U64_C(1) << 6)
#define BE_MVP_PTE_D			(BE_U64_C(1) << 7)
#define BE_MVP_PTE_PPN_SHIFT		10U
#define BE_MVP_PTE_PPN_MASK		((BE_U64_C(1) << 44) - 1U)
/*
 * Every window leaf: V R W X U A D (0xdf); G, RSW, PBMT, N, and reserved
 * bits 0.
 */
#define BE_MVP_PTE_LEAF_FLAGS \
	(BE_MVP_PTE_V | BE_MVP_PTE_R | BE_MVP_PTE_W | BE_MVP_PTE_X | \
	 BE_MVP_PTE_U | BE_MVP_PTE_A | BE_MVP_PTE_D)

/*
 * A channel endpoint's rights, which give its leaf's flags by the
 * authority report's table (planning/mvp-m1-plan.md): map gives V U A,
 * read R, and write W D; so read is 0x53 and read and write 0xd7. Execute
 * is named only so that it can be refused: no channel leaf has X.
 */
#define BE_MVP_GSTAGE_RIGHT_READ	BE_U64_C(1)
#define BE_MVP_GSTAGE_RIGHT_WRITE	BE_U64_C(2)
#define BE_MVP_GSTAGE_RIGHT_EXECUTE	BE_U64_C(4)

/*
 * A declared page's kind (struct be_mvp_gstage_page; planning/mvp-m2-plan.md,
 * Q1 and Q5): a channel, which one domain writes and the other reads, or a
 * secret page, which one domain reads and only the monitor writes, before
 * any domain runs; and the endpoint that names no domain, a secret page's
 * writer.
 */
#define BE_MVP_PAGE_CHANNEL		BE_U64_C(0)
#define BE_MVP_PAGE_SECRET		BE_U64_C(1)
#define BE_MVP_PAGE_NONE		BE_U64_C(0xff)

/**
 * struct be_mvp_gstage_desc - one guest-RAM window, its table pool, its
 *                              VMID, and its hart
 * @gpa_base: 2 MiB-aligned guest-physical base
 * @hpa_base: 2 MiB-aligned host-physical base
 * @size: nonzero multiple of 2 MiB inside one 1 GiB GPA region
 * @pool_pa: 16 KiB-aligned host-physical base of the 32 KiB pool, outside
 *           the window
 * @vmid: the domain's VMID, below 2^14
 * @hart: the domain hart that installs the root, an identifier only
 */
struct be_mvp_gstage_desc {
	be_u64 gpa_base;
	be_u64 hpa_base;
	be_u64 size;
	be_u64 pool_pa;
	be_u64 vmid;
	be_u64 hart;
};

/**
 * struct be_mvp_gstage_map - the window as the walker derived it
 * @hgatp: Sv39x4, the VMID, and the root PPN of the walked pool
 * @gpa_base: first mapped GPA
 * @hpa_base: host-physical address of @gpa_base
 * @size: mapped bytes
 * @leaves: 2 MiB leaves found
 * @pool_pa: host-physical base of the walked pool
 * @vmid: the VMID in @hgatp
 * @hart: the domain hart, from the descriptor
 *
 * All zero unless the walk succeeded.
 */
struct be_mvp_gstage_map {
	be_u64 hgatp;
	be_u64 gpa_base;
	be_u64 hpa_base;
	be_u64 size;
	be_u64 leaves;
	be_u64 pool_pa;
	be_u64 vmid;
	be_u64 hart;
};

/**
 * struct be_mvp_gstage_root_page - the channel page one root maps beside
 *                                  its window, as declared
 * @gpa: 4 KiB-aligned guest-physical address in the window's 1 GiB root
 *       entry, on a level-1 entry that none of the window's leaves uses
 * @hpa: 4 KiB-aligned host-physical address below 2^56, over neither the
 *       window nor the pool
 * @bytes: exactly %BE_MVP_GSTAGE_PAGE_BYTES; or 0 for a root without a
 *         channel page, whose every field is then 0
 * @rights: %BE_MVP_GSTAGE_RIGHT_READ, alone or with
 *          %BE_MVP_GSTAGE_RIGHT_WRITE
 */
struct be_mvp_gstage_root_page {
	be_u64 gpa;
	be_u64 hpa;
	be_u64 bytes;
	be_u64 rights;
};

/**
 * struct be_mvp_gstage_page - one declared shared page, as the sealed
 *                             manifest gives it (planning/mvp-m2-plan.md,
 *                             Q1)
 * @gpa: 4 KiB-aligned guest-physical address, the same in every root that
 *       maps it
 * @hpa: 4 KiB-aligned host-physical address
 * @bytes: %BE_MVP_GSTAGE_PAGE_BYTES
 * @kind: %BE_MVP_PAGE_CHANNEL or %BE_MVP_PAGE_SECRET
 * @writer: a channel's sending domain; %BE_MVP_PAGE_NONE for a secret page
 * @reader: a channel's receiving domain, or the one domain that reads a
 *          secret page
 * @rights: each domain's rights on the page, by domain:
 *          %BE_MVP_GSTAGE_RIGHT_READ, alone or with
 *          %BE_MVP_GSTAGE_RIGHT_WRITE; or 0, no leaf in that domain's root
 *
 * The generated scenario header's BE_MVP_SCENARIO_PAGE_INITIALIZER lists
 * the pages in this order.
 */
struct be_mvp_gstage_page {
	be_u64 gpa;
	be_u64 hpa;
	be_u64 bytes;
	be_u64 kind;
	be_u64 writer;
	be_u64 reader;
	be_u64 rights[BE_MVP_DOMAINS];
};

/**
 * struct be_mvp_gstage_leaf - the channel leaf as the walker derived it
 * @gpa: the GPA it maps, from its root, level-1, and level-0 indices
 * @hpa: the host-physical page its PPN names
 * @bytes: %BE_MVP_GSTAGE_PAGE_BYTES
 * @pte: the leaf as walked, its rights in its flags
 * @l0_pa: host-physical address of the level-0 page that holds it
 *
 * All zero when the root maps no channel page, and unless the walk
 * succeeded. A declared page's leaf (struct be_mvp_gstage_leaves) is the
 * same record.
 */
struct be_mvp_gstage_leaf {
	be_u64 gpa;
	be_u64 hpa;
	be_u64 bytes;
	be_u64 pte;
	be_u64 l0_pa;
};

/**
 * struct be_mvp_gstage_leaves - one root's walked leaves for the declared
 *                               pages
 * @page: by page index, the leaf the root holds for that page; all zero
 *        when it holds none, beyond the declared pages, and unless the walk
 *        succeeded
 */
struct be_mvp_gstage_leaves {
	struct be_mvp_gstage_leaf page[BE_MVP_PAGES_MAX];
};

/**
 * struct be_mvp_gstage_channel - the sealed channel record
 * @gpa: the page's guest-physical address, the same in both roots
 * @hpa: the page's host-physical address
 * @bytes: %BE_MVP_GSTAGE_PAGE_BYTES; or 0 when the scenario declares no
 *         channel, whose every field is then 0
 * @writer_domain: the domain that sends
 * @reader_domain: the other domain, which receives
 * @writer_rights: read and write: one writer
 * @reader_rights: read
 */
struct be_mvp_gstage_channel {
	be_u64 gpa;
	be_u64 hpa;
	be_u64 bytes;
	be_u64 writer_domain;
	be_u64 reader_domain;
	be_u64 writer_rights;
	be_u64 reader_rights;
};

/**
 * struct be_mvp_gstage_refusal - the root a channel or page check refused
 * @domain: the domain whose root the refusal names, or %BE_MVP_DOMAINS
 *          when it names no one root (M0's pair rules, the record or the
 *          pages) or the check passed
 * @hart: that domain's hart, from its walked map; else 0
 * @walked: that domain's walked leaf PTE, 0 for none; else 0
 * @declared: the leaf PTE the record or the page declares for that domain,
 *            0 for none; else 0
 * @page: the page a page check's refusal names, which may name no root
 *        (be_mvp_gstage_page_check()); %BE_MVP_PAGES_MAX when it names
 *        none; 0 from be_mvp_gstage_channel_check()
 */
struct be_mvp_gstage_refusal {
	be_u64 domain;
	be_u64 hart;
	be_u64 walked;
	be_u64 declared;
	be_u64 page;
};

/**
 * enum be_mvp_gstage_error - stable G-stage results
 * @BE_MVP_GSTAGE_OK: success
 * @BE_MVP_GSTAGE_NULL: a required pointer is absent
 * @BE_MVP_GSTAGE_DESC: the descriptor breaks an alignment, range, or VMID
 *                      rule
 * @BE_MVP_GSTAGE_POOL: wrong pool size or placement, or the window covers it
 * @BE_MVP_GSTAGE_ROOT: a root entry is not the one expected pointer
 * @BE_MVP_GSTAGE_L1: a level-1 entry is neither an exact leaf of the
 *                    window's run, the one pointer to this pool's level-0
 *                    page at the declared channel page's or pages' index,
 *                    nor zero
 * @BE_MVP_GSTAGE_SPARE: a spare pool byte is not zero, the level-0 page's
 *                       included when no pointer names it
 * @BE_MVP_GSTAGE_MISMATCH: the walked window differs from the descriptor
 * @BE_MVP_GSTAGE_PAIR: two walked roots share a pool page, a window byte, a
 *                      VMID, a hart, or a root, a root is for the control
 *                      hart, or a window covers the other's pool
 * @BE_MVP_GSTAGE_PAGE: the declared channel page breaks a rule of
 *                      &struct be_mvp_gstage_root_page, or the declared
 *                      pages a rule of be_mvp_gstage_build_pages()
 * @BE_MVP_GSTAGE_L0: the level-0 page that the pointer names holds anything
 *                    but one exact channel leaf: no leaf, a second leaf, a
 *                    leaf at another index or onto another page than the
 *                    declared one, or flags other than V R U A with W and D
 *                    both or neither; with pages, anything but exact leaves
 *                    at declared pages' indices onto their pages, at least
 *                    one
 * @BE_MVP_GSTAGE_CHANNEL: the channel check refused the record, a window or
 *                         a pool against the channel page, or a walked leaf
 *                         that differs from the one the record declares
 * @BE_MVP_GSTAGE_PAGES: the page check refused a declared page, a window or
 *                       a pool against a page, or a walked leaf that differs
 *                       from the one a page declares for its root
 */
enum be_mvp_gstage_error {
	BE_MVP_GSTAGE_OK = 0,
	BE_MVP_GSTAGE_NULL,
	BE_MVP_GSTAGE_DESC,
	BE_MVP_GSTAGE_POOL,
	BE_MVP_GSTAGE_ROOT,
	BE_MVP_GSTAGE_L1,
	BE_MVP_GSTAGE_SPARE,
	BE_MVP_GSTAGE_MISMATCH,
	BE_MVP_GSTAGE_PAIR,
	BE_MVP_GSTAGE_PAGE,
	BE_MVP_GSTAGE_L0,
	BE_MVP_GSTAGE_CHANNEL,
	BE_MVP_GSTAGE_PAGES,
};

/**
 * be_mvp_gstage_build - scrub the pool, then write the root and leaves
 * @desc: the window
 * @pool: monitor-owned pool bytes, the memory at @desc->pool_pa
 * @pool_size: exactly %BE_MVP_GSTAGE_POOL_BYTES
 *
 * The whole pool is zeroed first, also when the descriptor is refused; a
 * pool of the wrong size is never written. The builder refuses a zero or
 * misaligned size, a misaligned GPA or HPA, a 1 GiB crossing, a GPA at or
 * above 2^41, a PA at or above 2^56, a misaligned pool, a VMID at or above
 * 2^14, and a window that covers the pool. The root maps no channel page:
 * this is be_mvp_gstage_build_channel() with an all-zero page.
 *
 * Return: %BE_MVP_GSTAGE_OK, or the refusal with the pool scrubbed.
 */
enum be_mvp_gstage_error
be_mvp_gstage_build(const struct be_mvp_gstage_desc *desc, be_u8 *pool,
		   be_u64 pool_size);

/**
 * be_mvp_gstage_build_channel - scrub the pool, then write the root, the
 *                               leaves, and the channel leaf
 * @desc: the window
 * @page: the root's channel page, all zero for none
 * @pool: monitor-owned pool bytes, the memory at @desc->pool_pa
 * @pool_size: exactly %BE_MVP_GSTAGE_POOL_BYTES
 *
 * As be_mvp_gstage_build(); for a channel page, the level-1 entry of the
 * page's GPA then points to the pool's level-0 page, whose entry for the
 * GPA is the one 4 KiB leaf onto the page's HPA: V R U A, and W D when
 * @page->rights grants write (0x53 or 0xd7), never X. It also refuses a
 * page that breaks a rule of &struct be_mvp_gstage_root_page.
 *
 * Return: %BE_MVP_GSTAGE_OK, or the refusal with the pool scrubbed.
 */
enum be_mvp_gstage_error
be_mvp_gstage_build_channel(const struct be_mvp_gstage_desc *desc,
			    const struct be_mvp_gstage_root_page *page,
			    be_u8 *pool, be_u64 pool_size);

/**
 * be_mvp_gstage_build_pages - scrub the pool, then write the root, the
 *                             leaves, and one root's leaves for the
 *                             declared pages
 * @desc: the window
 * @pages: the declared pages, in page order
 * @count: how many, 1 to %BE_MVP_PAGES_MAX
 * @domain: the domain whose root this is; each page's rights for it give
 *          the page's leaf
 * @pool: monitor-owned pool bytes, the memory at @desc->pool_pa
 * @pool_size: exactly %BE_MVP_GSTAGE_POOL_BYTES
 *
 * As be_mvp_gstage_build(); then, when @domain has rights on any page, the
 * level-1 entry of the pages' 2 MiB slot points to the pool's level-0
 * page, whose entry for each such page is one 4 KiB leaf onto its HPA:
 * V R U A, and W D when the rights grant write (0x53 or 0xd7), never X. A
 * page on which @domain has no rights (0) has no leaf. The builder also
 * refuses a domain at or above %BE_MVP_DOMAINS and pages that break a
 * rule: a count of 0 or above %BE_MVP_PAGES_MAX; a page other than one
 * 4 KiB-aligned 4 KiB page in the window's 1 GiB root entry, in the first
 * page's 2 MiB slot, which none of the window's leaves uses, below 2^56,
 * over neither the window nor the pool; any domain's rights other than 0,
 * read, or read and write; or two pages at one GPA or on one HPA.
 *
 * Return: %BE_MVP_GSTAGE_OK, or the refusal with the pool scrubbed.
 */
enum be_mvp_gstage_error
be_mvp_gstage_build_pages(const struct be_mvp_gstage_desc *desc,
			  const struct be_mvp_gstage_page *pages, be_u64 count,
			  be_u64 domain, be_u8 *pool, be_u64 pool_size);

/**
 * be_mvp_gstage_walk - parse every pool byte and derive the window
 * @desc: the window the walk must find
 * @pool: pool bytes
 * @pool_size: exactly %BE_MVP_GSTAGE_POOL_BYTES
 * @map: zeroed first; filled only on success
 *
 * The walker shares only the byte loader with the builder. It accepts
 * exactly one root entry, a pointer to this pool's level-1 page; only exact
 * 2 MiB leaves forming one contiguous linear run in the level-1 page; and
 * zero in every other pool byte. It derives (gpa, hpa, size) from the bytes
 * and compares them with @desc, whose VMID it places in the hgatp and whose
 * hart it places in the map. The root maps no channel page: this is
 * be_mvp_gstage_walk_channel() with an all-zero page, which refuses any
 * level-0 pointer.
 *
 * Return: %BE_MVP_GSTAGE_OK or the first error found.
 */
enum be_mvp_gstage_error
be_mvp_gstage_walk(const struct be_mvp_gstage_desc *desc, const be_u8 *pool,
		  be_u64 pool_size, struct be_mvp_gstage_map *map);

/**
 * be_mvp_gstage_walk_channel - parse every pool byte and derive the window
 *                              and the channel leaf
 * @desc: the window the walk must find
 * @page: the root's channel page, all zero for none
 * @pool: pool bytes
 * @pool_size: exactly %BE_MVP_GSTAGE_POOL_BYTES
 * @map: zeroed first; filled only on success
 * @leaf: zeroed first; filled only on success, when the pool holds a leaf
 *
 * As be_mvp_gstage_walk(), after refusing a page that breaks a rule of
 * &struct be_mvp_gstage_root_page, with one more rule: besides the window's
 * run, the level-1 page may hold one pointer, only at the declared page's
 * level-1 index and only to this pool's level-0 page, which then holds
 * exactly one leaf, at the declared page's level-0 index, onto its HPA,
 * with the flags V R U A and W D both or neither, and zero elsewhere. A
 * level-0 page that no pointer names is spare. The walker does not compare
 * the leaf's rights with @page->rights: be_mvp_gstage_channel_check() does,
 * from the walked leaf.
 *
 * Return: %BE_MVP_GSTAGE_OK or the first error found.
 */
enum be_mvp_gstage_error
be_mvp_gstage_walk_channel(const struct be_mvp_gstage_desc *desc,
			   const struct be_mvp_gstage_root_page *page,
			   const be_u8 *pool, be_u64 pool_size,
			   struct be_mvp_gstage_map *map,
			   struct be_mvp_gstage_leaf *leaf);

/**
 * be_mvp_gstage_walk_pages - parse every pool byte and derive the window
 *                            and the root's leaves for the declared pages
 * @desc: the window the walk must find
 * @pages: the declared pages, in page order
 * @count: how many, 1 to %BE_MVP_PAGES_MAX
 * @pool: pool bytes
 * @pool_size: exactly %BE_MVP_GSTAGE_POOL_BYTES
 * @map: zeroed first; filled only on success
 * @leaves: zeroed first; filled only on success, for each page whose leaf
 *          the pool holds
 *
 * As be_mvp_gstage_walk(), after refusing pages that break a rule of
 * be_mvp_gstage_build_pages(), with one more rule: besides the window's
 * run, the level-1 page may hold one pointer, only at the pages' level-1
 * index and only to this pool's level-0 page, which then holds at least
 * one leaf, each at a declared page's level-0 index, onto that page's HPA,
 * with the flags V R U A and W D both or neither, and zero elsewhere. A
 * level-0 page that no pointer names is spare. The walker reads no page's
 * rights: a leaf for a page on which the root's domain has no rights is
 * walked as any other, and be_mvp_gstage_page_check() compares each walked
 * leaf with the declared one.
 *
 * Return: %BE_MVP_GSTAGE_OK or the first error found.
 */
enum be_mvp_gstage_error
be_mvp_gstage_walk_pages(const struct be_mvp_gstage_desc *desc,
			 const struct be_mvp_gstage_page *pages, be_u64 count,
			 const be_u8 *pool, be_u64 pool_size,
			 struct be_mvp_gstage_map *map,
			 struct be_mvp_gstage_leaves *leaves);

/**
 * be_mvp_gstage_pair_check - require two walked roots to be disjoint
 * @first: one walked map
 * @second: the other walked map
 *
 * Refuses two maps that are not both walked, whose pools share a byte,
 * whose host windows share a byte, where either window covers either pool,
 * whose VMIDs are equal or zero, whose harts are equal or the control hart,
 * or whose hgatp values are equal. These are M0's rules for two roots that
 * map no channel page; be_mvp_gstage_channel_check() applies them too.
 *
 * Return: %BE_MVP_GSTAGE_OK, %BE_MVP_GSTAGE_NULL, or %BE_MVP_GSTAGE_PAIR.
 */
enum be_mvp_gstage_error
be_mvp_gstage_pair_check(const struct be_mvp_gstage_map *first,
			const struct be_mvp_gstage_map *second);

/**
 * be_mvp_gstage_channel_check - require two walked roots to share exactly
 *                               the declared channel page
 * @maps: both domains' walked maps, indexed by domain
 * @leaves: both domains' walked channel leaves, indexed by domain
 * @record: the sealed channel record
 * @refusal: set to name no domain first; filled from the refused root when
 *           a refusal names one
 *
 * Applies be_mvp_gstage_pair_check()'s rules to the two maps. A record
 * without a channel must be all zero, and neither root may hold a channel
 * leaf. A record with one must name one 4 KiB-aligned 4 KiB page, its GPA
 * below 2^41 and its HPA below 2^56, and two distinct domains, the
 * writer's rights read and write and the reader's read; neither window may
 * cover the page, in host-physical or guest-physical space, nor the page
 * either pool; and each root's walked leaf must be exactly the one the
 * record declares for it: at the record's GPA, onto its HPA, in that
 * root's level-0 page, with the flags derived from that domain's rights by
 * the authority report's table, map V U A, read R, write W D. Every page
 * the two roots share is then the declared page with its declared rights.
 * The check shares no code with the builder's leaf.
 *
 * Return: %BE_MVP_GSTAGE_OK, %BE_MVP_GSTAGE_NULL, %BE_MVP_GSTAGE_PAIR, or
 *         %BE_MVP_GSTAGE_CHANNEL.
 */
enum be_mvp_gstage_error
be_mvp_gstage_channel_check(const struct be_mvp_gstage_map *maps,
			    const struct be_mvp_gstage_leaf *leaves,
			    const struct be_mvp_gstage_channel *record,
			    struct be_mvp_gstage_refusal *refusal);

/**
 * be_mvp_gstage_page_check - require two walked roots to map exactly the
 *                            declared pages with their declared rights
 * @maps: both domains' walked maps, indexed by domain
 * @leaves: both domains' walked page leaves, indexed by domain
 * @pages: the sealed pages, in page order
 * @count: how many, 1 to %BE_MVP_PAGES_MAX
 * @refusal: set to name no page and no domain first; filled from the
 *           refused page, and its root when a refusal names one
 *
 * Applies be_mvp_gstage_pair_check()'s rules to the two maps. Each page
 * must be one 4 KiB-aligned 4 KiB page, its GPA below 2^41 and its HPA
 * below 2^56, at a GPA and on an HPA no other page uses; a channel must
 * name two distinct domains, the writer's rights read and write and the
 * reader's read; a secret page no writer, one reader whose rights are
 * read, and no rights for the other domain. Neither window may cover a
 * page, in host-physical or guest-physical space, nor a page either pool.
 * Each root's walked leaf for each page must then be exactly the one the
 * page declares for that root's domain: none, all zero, for no rights;
 * else at the page's GPA, onto its HPA, in that root's level-0 page, with
 * the flags derived from the domain's rights by the authority report's
 * table, map V U A, read R, write W D. Pages are checked in order, and
 * each page's roots in domain order. Every page the two roots map beside
 * their windows is then a declared page with its declared rights. The
 * check shares no code with the builder's leaves.
 *
 * Return: %BE_MVP_GSTAGE_OK, %BE_MVP_GSTAGE_NULL, %BE_MVP_GSTAGE_PAIR, or
 *         %BE_MVP_GSTAGE_PAGES.
 */
enum be_mvp_gstage_error
be_mvp_gstage_page_check(const struct be_mvp_gstage_map *maps,
			 const struct be_mvp_gstage_leaves *leaves,
			 const struct be_mvp_gstage_page *pages, be_u64 count,
			 struct be_mvp_gstage_refusal *refusal);

/**
 * be_mvp_gstage_translate - translate one guest range for an HS access
 * @map: a walked map
 * @gpa: guest-physical start
 * @length: nonzero byte count
 * @hpa: host-physical start on success, unchanged otherwise
 *
 * The window only: the map holds neither the channel page nor a declared
 * page, so DBCN reaches neither.
 *
 * Return: 1 when [@gpa, @gpa + @length) lies inside the window, else 0.
 */
int be_mvp_gstage_translate(const struct be_mvp_gstage_map *map, be_u64 gpa,
			   be_u64 length, be_u64 *hpa);

#endif
