/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: frozen R0 complete physical memory and G-stage layout for the fixed
 *          single-hart Beryllium runtime. This is the full thirteen-resource
 *          runtime profile: the eleven-resource Model 0.2 core projection plus
 *          two R-X guest-code overlays and their execute authorities.
 * Trust:   reviewable non-authoritative declaration. R0 installs no mapping and
 *          adds no privileged code; a host-side checker validates alignment,
 *          non-overlap, W^X, monitor exclusion, and page-table pool sizing.
 * Scope:   R0 freeze only. The two guest-code resources (12, 13) and their R-X
 *          authorities are an explicit operational extension and proof cut
 *          point. They are NOT covered by the Model 0.2 proof or the
 *          eleven-resource C fixture; the full profile is not a Model 0.2
 *          refinement. Any future hard-coded mapping must flow from sealed
 *          authority, not from a constant outside that authority.
 */

#ifndef BE_R0_LAYOUT_H
#define BE_R0_LAYOUT_H

#include <be/manifest.h>
#include <be/r0-config.h>

/* Fixed QEMU virt DRAM window for -m 128M and the OpenSBI-reserved prefix. */
#define BE_R0_DRAM_BASE			BE_U64_C(0x80000000)
#define BE_R0_DRAM_END			BE_U64_C(0x88000000)
#define BE_R0_OPENSBI_RESERVED_BASE	BE_U64_C(0x80000000)
#define BE_R0_OPENSBI_RESERVED_END	BE_U64_C(0x80200000)
#define BE_R0_IMAGE_ENTRY		BE_R0_PA_MONITOR_CODE

/* HS-owned diagnostic page: the final page contained inside monitor data. */
#define BE_R0_PA_DIAGNOSTIC		BE_U64_C(0x8020f000)

/* Guest-code overlays and their identity-shaped guest-physical addresses. */
#define BE_R0_PA_GUEST_CODE_MANAGEMENT	BE_U64_C(0x80232000)
#define BE_R0_PA_GUEST_CODE_PROTECTED	BE_U64_C(0x80233000)
#define BE_R0_GPA_GUEST_CODE_MANAGEMENT	BE_U64_C(0x40010000)
#define BE_R0_GPA_GUEST_CODE_PROTECTED	BE_U64_C(0x40011000)

/*
 * Sv39x4 page-table pool accounting. Each domain reserves one 32 KiB
 * (eight 4 KiB page) pool, 16 KiB aligned. The complete pool for the fixed
 * mapping set is: a 16 KiB (four page) Sv39x4 root, one 4 KiB level-1 table,
 * and one 4 KiB level-0 table. Two pages remain as explicit bounded spare.
 * A 16 KiB root alone is NOT a complete pool; the lower-level tables are
 * required to reach 4 KiB leaves.
 */
#define BE_R0_POOL_PAGES		8U
#define BE_R0_POOL_ROOT_PAGES		4U
#define BE_R0_POOL_LEVEL1_PAGES		1U
#define BE_R0_POOL_LEVEL0_PAGES		1U
#define BE_R0_POOL_USED_PAGES \
	(BE_R0_POOL_ROOT_PAGES + BE_R0_POOL_LEVEL1_PAGES + \
	 BE_R0_POOL_LEVEL0_PAGES)
#define BE_R0_POOL_SPARE_PAGES \
	(BE_R0_POOL_PAGES - BE_R0_POOL_USED_PAGES)

#define BE_R0_SV39X4_ROOT_ALIGN		BE_U64_C(0x4000)

/**
 * enum be_r0_class - R0 physical-extent classes for offline layout checking
 * @BE_R0_CLASS_OPENSBI: firmware-reserved region below the image
 * @BE_R0_CLASS_MONITOR_CODE: trusted HS code (R-X)
 * @BE_R0_CLASS_MONITOR_DATA: trusted HS data including the diagnostic page (RW)
 * @BE_R0_CLASS_ROOT_POOL: Sv39x4 root and lower-level table storage
 * @BE_R0_CLASS_TRUSTED_STACK: HS transition stack storage
 * @BE_R0_CLASS_SAVED_STATE: HS saved-register storage
 * @BE_R0_CLASS_PRIVATE: one-domain private and guest-stack backing (RW)
 * @BE_R0_CLASS_SHARED: directional channel backing
 * @BE_R0_CLASS_GUEST_CODE: R-X guest-code overlay (extension resource)
 * @BE_R0_CLASS_GUARD: reserved guard/overflow gap, mapped nowhere
 */
enum be_r0_class {
	BE_R0_CLASS_OPENSBI = 0,
	BE_R0_CLASS_MONITOR_CODE,
	BE_R0_CLASS_MONITOR_DATA,
	BE_R0_CLASS_ROOT_POOL,
	BE_R0_CLASS_TRUSTED_STACK,
	BE_R0_CLASS_SAVED_STATE,
	BE_R0_CLASS_PRIVATE,
	BE_R0_CLASS_SHARED,
	BE_R0_CLASS_GUEST_CODE,
	BE_R0_CLASS_GUARD,
};

/**
 * struct be_r0_extent - one frozen physical extent for offline checking
 * @id: stable extent identity; nonzero for the thirteen runtime resources
 * @name: stable reporting name
 * @base: page-aligned physical base
 * @size: nonzero page-multiple size
 * @class: R0 physical-extent class
 * @monitor_owned: nonzero when the extent must be unreachable by any VS root
 * @core_projection: nonzero for the eleven Model 0.2 core-projection resources
 */
struct be_r0_extent {
	be_u32 id;
	const char *name;
	be_u64 base;
	be_u64 size;
	enum be_r0_class class;
	be_u8 monitor_owned;
	be_u8 core_projection;
};

/**
 * struct be_r0_leaf - one frozen derived G-stage leaf for pool sizing
 * @gpa: identity-shaped guest-physical page
 * @pa: backing physical page
 * @rights: derived R/W/X PTE rights
 */
struct be_r0_leaf {
	be_u64 gpa;
	be_u64 pa;
	be_u32 rights;
};

/**
 * struct be_r0_root - one frozen derived root and its leaves for pool sizing
 * @root_id: root identity
 * @pool_base: 16 KiB-aligned page-table pool base
 * @domain: bound domain
 * @leaf_count: complete derived leaf count
 * @leaves: exact frozen leaves
 */
struct be_r0_root {
	be_u32 root_id;
	be_u64 pool_base;
	enum be_domain_id domain;
	be_size leaf_count;
	struct be_r0_leaf leaves[4];
};

#define BE_R0_RX	(BE_RIGHT_READ | BE_RIGHT_EXECUTE)
#define BE_R0_RW	(BE_RIGHT_READ | BE_RIGHT_WRITE)
#define BE_R0_RO	(BE_RIGHT_READ)

static const struct be_r0_extent be_r0_extents[] = {
	{ 0U, "opensbi-reserved", BE_R0_OPENSBI_RESERVED_BASE,
	  BE_U64_C(0x200000), BE_R0_CLASS_OPENSBI, 0U, 0U },
	{ 1U, "monitor-code", BE_R0_PA_MONITOR_CODE, BE_R0_SIZE_MONITOR_CODE,
	  BE_R0_CLASS_MONITOR_CODE, 1U, 1U },
	{ 2U, "monitor-data", BE_R0_PA_MONITOR_DATA, BE_R0_SIZE_MONITOR_DATA,
	  BE_R0_CLASS_MONITOR_DATA, 1U, 1U },
	{ 0U, "guard-image", BE_U64_C(0x80210000), BE_U64_C(0x4000),
	  BE_R0_CLASS_GUARD, 1U, 0U },
	{ 3U, "root-pool-management", BE_R0_PA_ROOT_POOL_MANAGEMENT,
	  BE_R0_SIZE_ROOT_POOL, BE_R0_CLASS_ROOT_POOL, 1U, 1U },
	{ 4U, "root-pool-protected", BE_R0_PA_ROOT_POOL_PROTECTED,
	  BE_R0_SIZE_ROOT_POOL, BE_R0_CLASS_ROOT_POOL, 1U, 1U },
	{ 0U, "guard-root", BE_U64_C(0x80224000), BE_PAGE_SIZE,
	  BE_R0_CLASS_GUARD, 1U, 0U },
	{ 5U, "trusted-stack-management", BE_R0_PA_STACK_MANAGEMENT,
	  BE_R0_SIZE_TRUSTED_STACK, BE_R0_CLASS_TRUSTED_STACK, 1U, 1U },
	{ 0U, "guard-stack-management", BE_U64_C(0x80227000), BE_PAGE_SIZE,
	  BE_R0_CLASS_GUARD, 1U, 0U },
	{ 6U, "trusted-stack-protected", BE_R0_PA_STACK_PROTECTED,
	  BE_R0_SIZE_TRUSTED_STACK, BE_R0_CLASS_TRUSTED_STACK, 1U, 1U },
	{ 0U, "guard-stack-protected", BE_U64_C(0x8022a000), BE_PAGE_SIZE,
	  BE_R0_CLASS_GUARD, 1U, 0U },
	{ 7U, "saved-state-management", BE_R0_PA_SAVED_MANAGEMENT,
	  BE_R0_SIZE_SAVED_STATE, BE_R0_CLASS_SAVED_STATE, 1U, 1U },
	{ 8U, "saved-state-protected", BE_R0_PA_SAVED_PROTECTED,
	  BE_R0_SIZE_SAVED_STATE, BE_R0_CLASS_SAVED_STATE, 1U, 1U },
	{ 0U, "guard-saved", BE_U64_C(0x8022d000), BE_PAGE_SIZE,
	  BE_R0_CLASS_GUARD, 1U, 0U },
	{ 9U, "private-management", BE_R0_PA_PRIVATE_MANAGEMENT, BE_R0_SIZE_PAGE,
	  BE_R0_CLASS_PRIVATE, 0U, 1U },
	{ 10U, "private-protected", BE_R0_PA_PRIVATE_PROTECTED, BE_R0_SIZE_PAGE,
	  BE_R0_CLASS_PRIVATE, 0U, 1U },
	{ 11U, "shared", BE_R0_PA_SHARED, BE_R0_SIZE_PAGE,
	  BE_R0_CLASS_SHARED, 0U, 1U },
	{ 0U, "guard-wx", BE_U64_C(0x80231000), BE_PAGE_SIZE,
	  BE_R0_CLASS_GUARD, 1U, 0U },
	{ 12U, "guest-code-management", BE_R0_PA_GUEST_CODE_MANAGEMENT,
	  BE_R0_SIZE_PAGE, BE_R0_CLASS_GUEST_CODE, 0U, 0U },
	{ 13U, "guest-code-protected", BE_R0_PA_GUEST_CODE_PROTECTED,
	  BE_R0_SIZE_PAGE, BE_R0_CLASS_GUEST_CODE, 0U, 0U },
};

static const struct be_r0_root be_r0_roots[] = {
	{ 1U, BE_R0_PA_ROOT_POOL_MANAGEMENT, BE_DOMAIN_MANAGEMENT, 3U, {
		{ BE_R0_GPA_MANAGEMENT_PRIVATE, BE_R0_PA_PRIVATE_MANAGEMENT,
		  BE_R0_RW },
		{ BE_R0_GPA_SHARED, BE_R0_PA_SHARED, BE_R0_RW },
		{ BE_R0_GPA_GUEST_CODE_MANAGEMENT,
		  BE_R0_PA_GUEST_CODE_MANAGEMENT, BE_R0_RX },
	} },
	{ 2U, BE_R0_PA_ROOT_POOL_PROTECTED, BE_DOMAIN_PROTECTED, 3U, {
		{ BE_R0_GPA_PROTECTED_PRIVATE, BE_R0_PA_PRIVATE_PROTECTED,
		  BE_R0_RW },
		{ BE_R0_GPA_SHARED, BE_R0_PA_SHARED, BE_R0_RO },
		{ BE_R0_GPA_GUEST_CODE_PROTECTED,
		  BE_R0_PA_GUEST_CODE_PROTECTED, BE_R0_RX },
	} },
};

#endif
