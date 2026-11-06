// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: non-privileged R2 Sv39x4 page-table builder, independent walker,
 *          and read-only re-walk for the bounded single-hart Beryllium runtime.
 * Trust:   non-privileged implementation only. R2 runs entirely as a host
 *          program and does not write CSRs, boot, trap, or execute in QEMU.
 *          Pool memory is accessed exclusively through LE byte-buffer helpers
 *          with bounded offsets and no pointer casts.
 * Scope:   accepted R2 non-privileged mechanism only (RISC-V Sv39x4 G-stage).
 *          Composes over const R1 state with separate one-way R2 state.
 */
#include <be/r0-config.h>
#include <be/r2.h>

/* --- Internal constants --- */

#define SV39X4_ROOT_ENTRIES	2048U	/* 11-bit VPN[2], 4 pages */
#define SV39X4_L1_ENTRIES	512U	/* 9-bit VPN[1] */
#define SV39X4_L0_ENTRIES	512U	/* 9-bit VPN[0] */
#define PTE_SIZE		8U

/* Pool page offsets. */
#define POOL_ROOT_OFFSET	BE_U64_C(0x0000)
#define POOL_L1_OFFSET		BE_U64_C(0x4000)
#define POOL_L0_OFFSET		BE_U64_C(0x5000)
#define POOL_SPARE6_OFFSET	BE_U64_C(0x6000)
#define POOL_SPARE7_OFFSET	BE_U64_C(0x7000)

/* PTE bit positions. */
#define PTE_V			(BE_U64_C(1) << 0)
#define PTE_R			(BE_U64_C(1) << 1)
#define PTE_W			(BE_U64_C(1) << 2)
#define PTE_X			(BE_U64_C(1) << 3)
#define PTE_U			(BE_U64_C(1) << 4)
#define PTE_G			(BE_U64_C(1) << 5)
#define PTE_A			(BE_U64_C(1) << 6)
#define PTE_D			(BE_U64_C(1) << 7)
#define PTE_RSW_MASK		(BE_U64_C(3) << 8)
#define PTE_PPN_SHIFT		10U
#define PTE_HIGH_MASK		(BE_U64_C(0x3FF) << 54)

/* 16 KiB alignment mask. */
#define ALIGN_16K_MASK		BE_U64_C(0x3FFF)

/* Fixed VPN indices for this profile. */
#define FIXED_VPN2		1U
#define FIXED_VPN1		0U

/* Fixed expected leaf count per root. */
#define FIXED_LEAVES_PER_ROOT	3U

/* --- LE byte-buffer PTE helpers --- */

static void pte_store_le64(be_u8 *dst, be_u64 value)
{
	dst[0] = (be_u8)(value & 0xFFU);
	dst[1] = (be_u8)((value >> 8) & 0xFFU);
	dst[2] = (be_u8)((value >> 16) & 0xFFU);
	dst[3] = (be_u8)((value >> 24) & 0xFFU);
	dst[4] = (be_u8)((value >> 32) & 0xFFU);
	dst[5] = (be_u8)((value >> 40) & 0xFFU);
	dst[6] = (be_u8)((value >> 48) & 0xFFU);
	dst[7] = (be_u8)((value >> 56) & 0xFFU);
}

static be_u64 pte_load_le64(const be_u8 *src)
{
	be_u64 v = 0U;

	v |= (be_u64)src[0];
	v |= (be_u64)src[1] << 8;
	v |= (be_u64)src[2] << 16;
	v |= (be_u64)src[3] << 24;
	v |= (be_u64)src[4] << 32;
	v |= (be_u64)src[5] << 40;
	v |= (be_u64)src[6] << 48;
	v |= (be_u64)src[7] << 56;
	return v;
}

/* --- Zero helper --- */

static void zero_bytes(be_u8 *buf, be_u64 count)
{
	be_u64 i;

	for (i = 0U; i < count; ++i)
		buf[i] = 0U;
}

/* --- Frame resolution --- */

static enum be_check_result
resolve_frame_pa(const struct be_canonical_state *canonical,
		 be_u32 frame_id,
		 be_u64 *pa_out)
{
	be_size i;
	be_size found_index = canonical->frame_count;
	be_size found_count = 0U;

	for (i = 0U; i < canonical->frame_count; ++i) {
		if (canonical->frames[i].id == frame_id) {
			found_index = i;
			++found_count;
		}
	}

	if (found_count == 0U)
		return BE_CHECK_UNDECLARED_MAPPING;
	if (found_count > 1U)
		return BE_CHECK_DUPLICATE_RESOURCE;

	{
		const struct be_frame_desc *frame =
			&canonical->frames[found_index];

		/* Frame class must be a leaf-mappable class. */
		if (frame->class != BE_FRAME_PRIVATE &&
		    frame->class != BE_FRAME_SHARED &&
		    frame->class != BE_FRAME_GUEST_CODE)
			return BE_CHECK_UNSUPPORTED;

		/* Mapped frame must be exactly one page. */
		if (frame->size != BE_PAGE_SIZE)
			return BE_CHECK_UNSUPPORTED;

		/* Page-aligned. */
		if ((frame->base & (BE_PAGE_SIZE - 1U)) != 0U)
			return BE_CHECK_UNSUPPORTED;

		/* 56-bit PA width. */
		if (frame->base > BE_SV39X4_PA_MASK)
			return BE_CHECK_UNSUPPORTED;

		/* Last byte within PA space. */
		if (frame->size - 1U > BE_SV39X4_PA_MASK - frame->base)
			return BE_CHECK_UNSUPPORTED;

		/* 64-bit overflow. */
		if (frame->base + frame->size < frame->base)
			return BE_CHECK_UNSUPPORTED;

		/* PPN within 44-bit width. */
		if ((frame->base >> 12) > BE_SV39X4_PPN_MASK)
			return BE_CHECK_UNSUPPORTED;

		*pa_out = frame->base;
	}

	return BE_CHECK_OK;
}

/* --- VPN extraction --- */

static void extract_vpn(be_u64 gpa, be_u32 *vpn2, be_u32 *vpn1, be_u32 *vpn0)
{
	*vpn2 = (be_u32)((gpa >> 30) & 0x7FFU);  /* 11 bits */
	*vpn1 = (be_u32)((gpa >> 21) & 0x1FFU);  /* 9 bits */
	*vpn0 = (be_u32)((gpa >> 12) & 0x1FFU);  /* 9 bits */
}

/* --- Per-root builder --- */

static enum be_check_result
build_one_root(const struct be_canonical_state *canonical,
	       const struct be_root_image *root,
	       struct be_r2_pool_desc *pool,
	       be_size *leaf_count_out)
{
	be_size mapping_index;
	be_size installed = 0U;
	be_u64 l1_ppn = (pool->base + POOL_L1_OFFSET) >> 12;
	be_u64 l0_ppn = (pool->base + POOL_L0_OFFSET) >> 12;

	/* Verify pointer PPNs fit in 44 bits. */
	if (l1_ppn > BE_SV39X4_PPN_MASK)
		return BE_CHECK_UNSUPPORTED;
	if (l0_ppn > BE_SV39X4_PPN_MASK)
		return BE_CHECK_UNSUPPORTED;

	for (mapping_index = 0U; mapping_index < root->mapping_count;
	     ++mapping_index) {
		const struct be_mapping_desc *mapping =
			&root->mappings[mapping_index];
		be_u64 gpa = mapping->gpa;
		be_u32 rights = mapping->rights;
		be_u64 pa;
		be_u32 vpn2, vpn1, vpn0;
		be_u64 root_pte_off, l1_pte_off, l0_pte_off;
		be_u64 existing;
		be_u64 ptr_pte;
		be_u64 leaf_pte;
		enum be_check_result rc;

		/* GPA range check: bits [63:41] must be zero. */
		if ((gpa & ~BE_SV39X4_GPA_MASK) != 0U)
			return BE_CHECK_UNSUPPORTED;

		/* GPA page alignment. */
		if ((gpa & (BE_PAGE_SIZE - 1U)) != 0U)
			return BE_CHECK_UNSUPPORTED;

		/* Frame resolution. */
		rc = resolve_frame_pa(canonical, mapping->frame_id, &pa);
		if (rc != BE_CHECK_OK)
			return rc;

		/* Rights check: nonzero, no W without R, subset of R|W|X. */
		if (rights == 0U)
			return BE_CHECK_EXCESS_RIGHTS;
		if ((rights & ~(be_u32)BE_RIGHT_ALL) != 0U)
			return BE_CHECK_UNSUPPORTED;
		if ((rights & BE_RIGHT_WRITE) != 0U &&
		    (rights & BE_RIGHT_READ) == 0U)
			return BE_CHECK_UNSUPPORTED;

		/* VPN extraction. */
		extract_vpn(gpa, &vpn2, &vpn1, &vpn0);

		/* Fixed geometry: VPN[2] must be 1, VPN[1] must be 0. */
		if (vpn2 != FIXED_VPN2)
			return BE_CHECK_UNSUPPORTED;
		if (vpn1 != FIXED_VPN1)
			return BE_CHECK_UNSUPPORTED;

		/* Root pointer PTE at buf[vpn2 * 8]. */
		root_pte_off = (be_u64)vpn2 * PTE_SIZE;
		ptr_pte = PTE_V | (l1_ppn << PTE_PPN_SHIFT);
		existing = pte_load_le64(pool->buf + root_pte_off);
		if (existing == 0U) {
			pte_store_le64(pool->buf + root_pte_off, ptr_pte);
		} else if (existing != ptr_pte) {
			return BE_CHECK_INTEGRITY;
		}

		/* L1 pointer PTE at buf[0x4000 + vpn1 * 8]. */
		l1_pte_off = POOL_L1_OFFSET + (be_u64)vpn1 * PTE_SIZE;
		ptr_pte = PTE_V | (l0_ppn << PTE_PPN_SHIFT);
		existing = pte_load_le64(pool->buf + l1_pte_off);
		if (existing == 0U) {
			pte_store_le64(pool->buf + l1_pte_off, ptr_pte);
		} else if (existing != ptr_pte) {
			return BE_CHECK_INTEGRITY;
		}

		/* Leaf PTE at buf[0x5000 + vpn0 * 8]. */
		l0_pte_off = POOL_L0_OFFSET + (be_u64)vpn0 * PTE_SIZE;
		existing = pte_load_le64(pool->buf + l0_pte_off);
		if (existing != 0U)
			return BE_CHECK_DUPLICATE_RESOURCE;

		/* Encode leaf PTE. */
		{
			be_u64 ppn = pa >> 12;
			be_u64 r_bit = ((rights & BE_RIGHT_READ) != 0U)
					       ? PTE_R
					       : 0U;
			be_u64 w_bit = ((rights & BE_RIGHT_WRITE) != 0U)
					       ? PTE_W
					       : 0U;
			be_u64 x_bit = ((rights & BE_RIGHT_EXECUTE) != 0U)
					       ? PTE_X
					       : 0U;
			be_u64 d_bit = (w_bit != 0U) ? PTE_D : 0U;

			leaf_pte = PTE_V | PTE_U | PTE_A | d_bit | r_bit |
				   w_bit | x_bit |
				   (ppn << PTE_PPN_SHIFT);
		}
		pte_store_le64(pool->buf + l0_pte_off, leaf_pte);
		++installed;
	}

	if (installed != root->mapping_count)
		return BE_CHECK_INCOMPLETE;

	*leaf_count_out = installed;
	return BE_CHECK_OK;
}

/* --- Per-root walker --- */

static enum be_check_result
walk_one_root(const struct be_r2_pool_desc *pool,
	      const struct be_canonical_state *canonical,
	      const struct be_root_image *root,
	      struct be_r2_leaf_set *leaf_set)
{
	be_u64 expected_l1_ppn = (pool->base + POOL_L1_OFFSET) >> 12;
	be_u64 expected_l0_ppn = (pool->base + POOL_L0_OFFSET) >> 12;
	be_u64 pte;
	be_u64 ppn;
	be_u32 entry_index;
	be_size leaf_count = 0U;

	/* 1. Read root pointer at entry index 1 (VPN2=1). */
	pte = pte_load_le64(pool->buf + (be_u64)FIXED_VPN2 * PTE_SIZE);

	/* Must be a valid pointer PTE: V=1, R=W=X=0, other bits zero except PPN. */
	if ((pte & PTE_V) == 0U)
		return BE_CHECK_INTEGRITY;
	if ((pte & (PTE_R | PTE_W | PTE_X)) != 0U)
		return BE_CHECK_UNSUPPORTED; /* L2 leaf rejected */
	if ((pte & (PTE_U | PTE_G | PTE_A | PTE_D | PTE_RSW_MASK |
		    PTE_HIGH_MASK)) != 0U)
		return BE_CHECK_INTEGRITY;

	ppn = (pte >> PTE_PPN_SHIFT) & BE_SV39X4_PPN_MASK;
	if (ppn > BE_SV39X4_PPN_MASK)
		return BE_CHECK_UNSUPPORTED;
	if (ppn != expected_l1_ppn)
		return BE_CHECK_INTEGRITY;

	/* 2. Verify ALL OTHER root entries are zero (0, 2..2047). */
	for (entry_index = 0U; entry_index < SV39X4_ROOT_ENTRIES;
	     ++entry_index) {
		be_u64 off;

		if (entry_index == FIXED_VPN2)
			continue;
		off = (be_u64)entry_index * PTE_SIZE;
		pte = pte_load_le64(pool->buf + off);
		if (pte != 0U)
			return BE_CHECK_INTEGRITY;
	}

	/* 3. Read L1 entry at index 0 (VPN1=0). */
	pte = pte_load_le64(pool->buf + POOL_L1_OFFSET +
			    (be_u64)FIXED_VPN1 * PTE_SIZE);

	if ((pte & PTE_V) == 0U)
		return BE_CHECK_INTEGRITY;
	if ((pte & (PTE_R | PTE_W | PTE_X)) != 0U)
		return BE_CHECK_UNSUPPORTED; /* L1 leaf rejected */
	if ((pte & (PTE_U | PTE_G | PTE_A | PTE_D | PTE_RSW_MASK |
		    PTE_HIGH_MASK)) != 0U)
		return BE_CHECK_INTEGRITY;

	ppn = (pte >> PTE_PPN_SHIFT) & BE_SV39X4_PPN_MASK;
	if (ppn > BE_SV39X4_PPN_MASK)
		return BE_CHECK_UNSUPPORTED;
	if (ppn != expected_l0_ppn)
		return BE_CHECK_INTEGRITY;

	/* 4. Verify ALL OTHER L1 entries (1..511) are zero. */
	for (entry_index = 1U; entry_index < SV39X4_L1_ENTRIES;
	     ++entry_index) {
		be_u64 off = POOL_L1_OFFSET + (be_u64)entry_index * PTE_SIZE;

		pte = pte_load_le64(pool->buf + off);
		if (pte != 0U)
			return BE_CHECK_INTEGRITY;
	}

	/* 6. Walk L0 entries [0..511]. */
	for (entry_index = 0U; entry_index < SV39X4_L0_ENTRIES;
	     ++entry_index) {
		be_u64 off = POOL_L0_OFFSET + (be_u64)entry_index * PTE_SIZE;

		pte = pte_load_le64(pool->buf + off);
		if (pte == 0U)
			continue;

		/* Must be a valid leaf: V=1 and at least one of R/W/X. */
		if ((pte & PTE_V) == 0U)
			return BE_CHECK_INTEGRITY;
		if ((pte & (PTE_R | PTE_W | PTE_X)) == 0U)
			return BE_CHECK_INTEGRITY;

		/* Structural checks. */
		if ((pte & PTE_U) == 0U)
			return BE_CHECK_INTEGRITY;
		if ((pte & PTE_A) == 0U)
			return BE_CHECK_INTEGRITY;
		if ((pte & PTE_G) != 0U)
			return BE_CHECK_INTEGRITY;
		if ((pte & PTE_RSW_MASK) != 0U)
			return BE_CHECK_INTEGRITY;
		if ((pte & PTE_HIGH_MASK) != 0U)
			return BE_CHECK_INTEGRITY;

		/* D must be 1 iff W=1. */
		if ((pte & PTE_W) != 0U) {
			if ((pte & PTE_D) == 0U)
				return BE_CHECK_INTEGRITY;
		} else {
			if ((pte & PTE_D) != 0U)
				return BE_CHECK_INTEGRITY;
		}

		/* Extract PPN. */
		ppn = (pte >> PTE_PPN_SHIFT) & BE_SV39X4_PPN_MASK;
		if (ppn > BE_SV39X4_PPN_MASK)
			return BE_CHECK_UNSUPPORTED;

		/* Bounded leaf set. */
		if (leaf_count >= BE_MAX_MAPPINGS)
			return BE_CHECK_INTEGRITY;

		{
			struct be_r2_leaf *leaf =
				&leaf_set->leaves[leaf_count];

			/* Reconstruct GPA: VPN2=1, VPN1=0, VPN0=entry_index */
			leaf->gpa = ((be_u64)FIXED_VPN2 << 30) |
				    ((be_u64)FIXED_VPN1 << 21) |
				    ((be_u64)entry_index << 12);
			leaf->pa = ppn << 12;
			leaf->rights = 0U;
			if ((pte & PTE_R) != 0U)
				leaf->rights |= BE_RIGHT_READ;
			if ((pte & PTE_W) != 0U)
				leaf->rights |= BE_RIGHT_WRITE;
			if ((pte & PTE_X) != 0U)
				leaf->rights |= BE_RIGHT_EXECUTE;
		}
		++leaf_count;
	}

	/* 7. Verify leaf count == root->mapping_count. */
	if (leaf_count != root->mapping_count)
		return BE_CHECK_INTEGRITY;

	/* 8. Verify spare pages (6, 7) are entirely zero. */
	{
		be_u64 spare_off;

		for (spare_off = POOL_SPARE6_OFFSET;
		     spare_off < BE_SV39X4_POOL_SIZE; ++spare_off) {
			if (pool->buf[spare_off] != 0U)
				return BE_CHECK_INTEGRITY;
		}
	}

	/* 9. Exact match each enumerated leaf against root->mappings. */
	{
		be_size mi;

		for (mi = 0U; mi < root->mapping_count; ++mi) {
			const struct be_mapping_desc *mapping =
				&root->mappings[mi];
			be_u64 expected_pa;
			enum be_check_result rc;
			be_size li;
			int found = 0;

			rc = resolve_frame_pa(canonical, mapping->frame_id,
					      &expected_pa);
			if (rc != BE_CHECK_OK)
				return rc;

			for (li = 0U; li < leaf_count; ++li) {
				const struct be_r2_leaf *leaf =
					&leaf_set->leaves[li];

				if (leaf->gpa == mapping->gpa &&
				    leaf->pa == expected_pa &&
				    leaf->rights == mapping->rights) {
					found = 1;
					break;
				}
			}
			if (!found)
				return BE_CHECK_INTEGRITY;
		}
	}

	leaf_set->count = leaf_count;
	return BE_CHECK_OK;
}

/* --- R1 integrity revalidation --- */

static enum be_check_result
revalidate_r1(const struct be_runtime *runtime)
{
	enum be_check_result rc;

	/* Phase must be DERIVED. */
	if (runtime->phase != BE_RUNTIME_PHASE_DERIVED)
		return BE_CHECK_INVALID_PHASE;

	/* check_result must be OK. */
	if (runtime->check_result != BE_CHECK_OK)
		return BE_CHECK_INTEGRITY;

	/* Sealed must be nonzero. */
	if (runtime->sealed == 0U)
		return BE_CHECK_INTEGRITY;

	/* validated_identity must be nonzero. */
	if (runtime->validated_identity == 0U)
		return BE_CHECK_INTEGRITY;

	/* sealed_identity must be nonzero. */
	if (runtime->sealed_identity == 0U)
		return BE_CHECK_INTEGRITY;

	/* validated_identity == sealed_identity. */
	if (runtime->validated_identity != runtime->sealed_identity)
		return BE_CHECK_INTEGRITY;

	/* canonical.configuration_id == sealed_identity. */
	if (runtime->canonical.configuration_id != runtime->sealed_identity)
		return BE_CHECK_INTEGRITY;

	/* enforcement.configuration_id == sealed_identity. */
	if (runtime->enforcement.configuration_id != runtime->sealed_identity)
		return BE_CHECK_INTEGRITY;

	/* Recompute configuration identity. */
	if (be_configuration_identity(&runtime->canonical) !=
	    runtime->canonical.configuration_id)
		return BE_CHECK_INTEGRITY;

	/* be_check_canonical. */
	rc = be_check_canonical(&runtime->canonical);
	if (rc != BE_CHECK_OK)
		return rc;

	/* be_check_enforcement. */
	rc = be_check_enforcement(&runtime->canonical, &runtime->enforcement);
	if (rc != BE_CHECK_OK)
		return rc;

	return BE_CHECK_OK;
}

/* --- Frozen fixed-profile validation --- */

static enum be_check_result
validate_frozen_profile(const struct be_canonical_state *canonical,
			const struct be_enforcement_state *enforcement)
{
	/* Scalar checks. */
	if (canonical->configuration_version != BE_CONFIGURATION_VERSION)
		return BE_CHECK_UNSUPPORTED;
	if (canonical->architecture != BE_ARCH_RISCV64)
		return BE_CHECK_UNSUPPORTED;
	if (canonical->profile != BE_PROFILE_FIXED_SINGLE_HART_TWO_DOMAIN)
		return BE_CHECK_UNSUPPORTED;
	if (canonical->hart_id != BE_CONFIGURATION_HART_ID)
		return BE_CHECK_UNSUPPORTED;
	if (canonical->domain_count != 2U)
		return BE_CHECK_INCOMPLETE;
	if (canonical->frame_count != 13U)
		return BE_CHECK_INCOMPLETE;
	if (canonical->authority_count != 6U)
		return BE_CHECK_INCOMPLETE;
	if (canonical->saved_state_count != 2U)
		return BE_CHECK_INCOMPLETE;
	if (canonical->channel_count != 1U)
		return BE_CHECK_INCOMPLETE;
	if (enforcement->root_count != 2U)
		return BE_CHECK_INCOMPLETE;

	/* Domain binding checks. */
	{
		const struct be_domain_desc *d0 = &canonical->domains[0];
		const struct be_domain_desc *d1 = &canonical->domains[1];

		/* Management domain. */
		if (d0->id != BE_DOMAIN_MANAGEMENT)
			return BE_CHECK_BINDING;
		if (d0->vcpu_id != 1U)
			return BE_CHECK_BINDING;
		if (d0->root_id != 101U)
			return BE_CHECK_BINDING;
		if (d0->root_table_frame != 3U)
			return BE_CHECK_BINDING;
		if (d0->vmid != 0U)
			return BE_CHECK_BINDING;
		if (d0->trusted_stack_frame != 5U)
			return BE_CHECK_BINDING;
		if (d0->saved_state_id != 1U)
			return BE_CHECK_BINDING;
		if (d0->saved_state_frame != 7U)
			return BE_CHECK_BINDING;

		/* Protected domain. */
		if (d1->id != BE_DOMAIN_PROTECTED)
			return BE_CHECK_BINDING;
		if (d1->vcpu_id != 2U)
			return BE_CHECK_BINDING;
		if (d1->root_id != 102U)
			return BE_CHECK_BINDING;
		if (d1->root_table_frame != 4U)
			return BE_CHECK_BINDING;
		if (d1->vmid != 0U)
			return BE_CHECK_BINDING;
		if (d1->trusted_stack_frame != 6U)
			return BE_CHECK_BINDING;
		if (d1->saved_state_id != 2U)
			return BE_CHECK_BINDING;
		if (d1->saved_state_frame != 8U)
			return BE_CHECK_BINDING;
	}

	/* Exact frozen frame checks (13 frames in canonical sorted order). */
	{
		/* Guest-code PAs not in r0-config.h public interface. */
		static const be_u64 pa_guest_code_mgmt =
			BE_U64_C(0x80232000);
		static const be_u64 pa_guest_code_prot =
			BE_U64_C(0x80233000);

		struct frozen_frame {
			be_u32 id;
			be_u64 base;
			be_u64 size;
			enum be_frame_class class;
			be_u32 owner_mask;
		};
		static const struct frozen_frame expected[13] = {
			{ 1U, BE_R0_PA_MONITOR_CODE, BE_R0_SIZE_MONITOR_CODE,
			  BE_FRAME_MONITOR_CODE, BE_OWNER_MONITOR },
			{ 2U, BE_R0_PA_MONITOR_DATA, BE_R0_SIZE_MONITOR_DATA,
			  BE_FRAME_MONITOR_DATA, BE_OWNER_MONITOR },
			{ 3U, BE_R0_PA_ROOT_POOL_MANAGEMENT,
			  BE_R0_SIZE_ROOT_POOL, BE_FRAME_ROOT_TABLE,
			  BE_OWNER_MONITOR },
			{ 4U, BE_R0_PA_ROOT_POOL_PROTECTED,
			  BE_R0_SIZE_ROOT_POOL, BE_FRAME_ROOT_TABLE,
			  BE_OWNER_MONITOR },
			{ 5U, BE_R0_PA_STACK_MANAGEMENT,
			  BE_R0_SIZE_TRUSTED_STACK, BE_FRAME_TRUSTED_STACK,
			  BE_OWNER_MONITOR },
			{ 6U, BE_R0_PA_STACK_PROTECTED,
			  BE_R0_SIZE_TRUSTED_STACK, BE_FRAME_TRUSTED_STACK,
			  BE_OWNER_MONITOR },
			{ 7U, BE_R0_PA_SAVED_MANAGEMENT,
			  BE_R0_SIZE_SAVED_STATE, BE_FRAME_SAVED_STATE,
			  BE_OWNER_MONITOR },
			{ 8U, BE_R0_PA_SAVED_PROTECTED,
			  BE_R0_SIZE_SAVED_STATE, BE_FRAME_SAVED_STATE,
			  BE_OWNER_MONITOR },
			{ 9U, BE_R0_PA_PRIVATE_MANAGEMENT, BE_R0_SIZE_PAGE,
			  BE_FRAME_PRIVATE, BE_OWNER_MANAGEMENT },
			{ 10U, BE_R0_PA_PRIVATE_PROTECTED, BE_R0_SIZE_PAGE,
			  BE_FRAME_PRIVATE, BE_OWNER_PROTECTED },
			{ 11U, BE_R0_PA_SHARED, BE_R0_SIZE_PAGE,
			  BE_FRAME_SHARED, 0U },
			{ 12U, pa_guest_code_mgmt, BE_R0_SIZE_PAGE,
			  BE_FRAME_GUEST_CODE, BE_OWNER_MANAGEMENT },
			{ 13U, pa_guest_code_prot, BE_R0_SIZE_PAGE,
			  BE_FRAME_GUEST_CODE, BE_OWNER_PROTECTED },
		};
		be_size fi;

		for (fi = 0U; fi < 13U; ++fi) {
			const struct be_frame_desc *f =
				&canonical->frames[fi];
			const struct frozen_frame *e = &expected[fi];

			if (f->id != e->id)
				return BE_CHECK_BINDING;
			if (f->base != e->base) {
				if (f->base > BE_SV39X4_PA_MASK)
					return BE_CHECK_UNSUPPORTED;
				return BE_CHECK_BINDING;
			}
			if (f->size != e->size)
				return BE_CHECK_UNSUPPORTED;
			if (f->class != e->class)
				return BE_CHECK_UNSUPPORTED;
			if (f->owner_mask != e->owner_mask)
				return BE_CHECK_BINDING;
		}
	}

	/* Exact frozen saved-state checks (2 descriptors). */
	{
		const struct be_saved_state_desc *s0 =
			&canonical->saved_states[0];
		const struct be_saved_state_desc *s1 =
			&canonical->saved_states[1];

		if (s0->id != 1U)
			return BE_CHECK_BINDING;
		if (s0->owner != BE_DOMAIN_MANAGEMENT)
			return BE_CHECK_BINDING;
		if (s0->frame_id != 7U)
			return BE_CHECK_BINDING;

		if (s1->id != 2U)
			return BE_CHECK_BINDING;
		if (s1->owner != BE_DOMAIN_PROTECTED)
			return BE_CHECK_BINDING;
		if (s1->frame_id != 8U)
			return BE_CHECK_BINDING;
	}

	/* Exact frozen authority checks (6 authorities in canonical order). */
	{
		struct frozen_authority {
			enum be_domain_id domain;
			be_u64 gpa;
			be_u32 frame_id;
			be_u32 rights;
		};
		static const struct frozen_authority exp_auth[6] = {
			{ BE_DOMAIN_MANAGEMENT,
			  BE_R0_GPA_MANAGEMENT_PRIVATE, 9U,
			  BE_RIGHT_READ | BE_RIGHT_WRITE },
			{ BE_DOMAIN_MANAGEMENT,
			  BE_R0_GPA_SHARED, 11U,
			  BE_RIGHT_READ | BE_RIGHT_WRITE },
			{ BE_DOMAIN_MANAGEMENT,
			  BE_U64_C(0x40010000), 12U,
			  BE_RIGHT_READ | BE_RIGHT_EXECUTE },
			{ BE_DOMAIN_PROTECTED,
			  BE_R0_GPA_PROTECTED_PRIVATE, 10U,
			  BE_RIGHT_READ | BE_RIGHT_WRITE },
			{ BE_DOMAIN_PROTECTED,
			  BE_R0_GPA_SHARED, 11U,
			  BE_RIGHT_READ },
			{ BE_DOMAIN_PROTECTED,
			  BE_U64_C(0x40011000), 13U,
			  BE_RIGHT_READ | BE_RIGHT_EXECUTE },
		};
		be_size ai;

		for (ai = 0U; ai < 6U; ++ai) {
			const struct be_authority_desc *a =
				&canonical->authorities[ai];
			const struct frozen_authority *ea = &exp_auth[ai];

			if (a->domain != ea->domain)
				return BE_CHECK_BINDING;
			if (a->gpa != ea->gpa)
				return BE_CHECK_BINDING;
			if (a->frame_id != ea->frame_id)
				return BE_CHECK_BINDING;
			if (a->rights != ea->rights)
				return BE_CHECK_BINDING;
		}
	}

	/* Exact frozen channel check (1 channel). */
	{
		const struct be_channel_desc *ch = &canonical->channels[0];

		if (ch->id != 1U)
			return BE_CHECK_BINDING;
		if (ch->source != BE_DOMAIN_MANAGEMENT)
			return BE_CHECK_BINDING;
		if (ch->target != BE_DOMAIN_PROTECTED)
			return BE_CHECK_BINDING;
		if (ch->frame_id != 11U)
			return BE_CHECK_BINDING;
		if (ch->source_rights !=
		    (BE_RIGHT_READ | BE_RIGHT_WRITE))
			return BE_CHECK_BINDING;
		if (ch->target_rights != BE_RIGHT_READ)
			return BE_CHECK_BINDING;
	}

	/* Root checks. */
	{
		const struct be_root_image *r0 = &enforcement->roots[0];
		const struct be_root_image *r1 = &enforcement->roots[1];

		if (r0->root_id != 101U)
			return BE_CHECK_BINDING;
		if (r0->domain != BE_DOMAIN_MANAGEMENT)
			return BE_CHECK_BINDING;
		if (r0->vcpu_id != 1U)
			return BE_CHECK_BINDING;
		if (r0->vmid != 0U)
			return BE_CHECK_BINDING;
		if (r0->root_table_frame != 3U)
			return BE_CHECK_BINDING;
		if (r0->mapping_count != FIXED_LEAVES_PER_ROOT)
			return BE_CHECK_INCOMPLETE;

		if (r1->root_id != 102U)
			return BE_CHECK_BINDING;
		if (r1->domain != BE_DOMAIN_PROTECTED)
			return BE_CHECK_BINDING;
		if (r1->vcpu_id != 2U)
			return BE_CHECK_BINDING;
		if (r1->vmid != 0U)
			return BE_CHECK_BINDING;
		if (r1->root_table_frame != 4U)
			return BE_CHECK_BINDING;
		if (r1->mapping_count != FIXED_LEAVES_PER_ROOT)
			return BE_CHECK_INCOMPLETE;
	}

	/* Exact mapping checks (6 mappings total). */
	{
		const struct be_root_image *r0 = &enforcement->roots[0];
		const struct be_root_image *r1 = &enforcement->roots[1];

		/* Management root mappings. */
		if (r0->mappings[0].gpa != BE_U64_C(0x40000000))
			return BE_CHECK_BINDING;
		if (r0->mappings[0].frame_id != 9U)
			return BE_CHECK_BINDING;
		if (r0->mappings[0].rights !=
		    (BE_RIGHT_READ | BE_RIGHT_WRITE))
			return BE_CHECK_BINDING;

		if (r0->mappings[1].gpa != BE_U64_C(0x40002000))
			return BE_CHECK_BINDING;
		if (r0->mappings[1].frame_id != 11U)
			return BE_CHECK_BINDING;
		if (r0->mappings[1].rights !=
		    (BE_RIGHT_READ | BE_RIGHT_WRITE))
			return BE_CHECK_BINDING;

		if (r0->mappings[2].gpa != BE_U64_C(0x40010000))
			return BE_CHECK_BINDING;
		if (r0->mappings[2].frame_id != 12U)
			return BE_CHECK_BINDING;
		if (r0->mappings[2].rights !=
		    (BE_RIGHT_READ | BE_RIGHT_EXECUTE))
			return BE_CHECK_BINDING;

		/* Protected root mappings. */
		if (r1->mappings[0].gpa != BE_U64_C(0x40001000))
			return BE_CHECK_BINDING;
		if (r1->mappings[0].frame_id != 10U)
			return BE_CHECK_BINDING;
		if (r1->mappings[0].rights !=
		    (BE_RIGHT_READ | BE_RIGHT_WRITE))
			return BE_CHECK_BINDING;

		if (r1->mappings[1].gpa != BE_U64_C(0x40002000))
			return BE_CHECK_BINDING;
		if (r1->mappings[1].frame_id != 11U)
			return BE_CHECK_BINDING;
		if (r1->mappings[1].rights != BE_RIGHT_READ)
			return BE_CHECK_BINDING;

		if (r1->mappings[2].gpa != BE_U64_C(0x40011000))
			return BE_CHECK_BINDING;
		if (r1->mappings[2].frame_id != 13U)
			return BE_CHECK_BINDING;
		if (r1->mappings[2].rights !=
		    (BE_RIGHT_READ | BE_RIGHT_EXECUTE))
			return BE_CHECK_BINDING;
	}

	return BE_CHECK_OK;
}

/* --- Pool descriptor validation --- */

static int pool_is_scrub_safe(const struct be_r2_pool_desc *pool)
{
	return pool->buf != (be_u8 *)0 &&
	       pool->buf_size == BE_SV39X4_POOL_SIZE;
}

static void scrub_pool(struct be_r2_pool_desc *pool)
{
	zero_bytes(pool->buf, BE_SV39X4_POOL_SIZE);
}

static enum be_check_result
validate_pool_desc(const struct be_r2_pool_desc *pool)
{
	/* 16 KiB alignment. */
	if ((pool->base & ALIGN_16K_MASK) != 0U)
		return BE_CHECK_UNSUPPORTED;

	/* 56-bit PA space. */
	if (pool->base > BE_SV39X4_PA_MASK)
		return BE_CHECK_UNSUPPORTED;

	/* Last byte within PA space. */
	if (pool->buf_size - 1U > BE_SV39X4_PA_MASK - pool->base)
		return BE_CHECK_UNSUPPORTED;

	/* 64-bit overflow. */
	if (pool->base + pool->buf_size < pool->base)
		return BE_CHECK_UNSUPPORTED;

	/* PPN within 44 bits. */
	if ((pool->base >> 12) > BE_SV39X4_PPN_MASK)
		return BE_CHECK_UNSUPPORTED;

	return BE_CHECK_OK;
}

/* --- Pool-to-root binding --- */

static enum be_check_result
validate_root_pool_binding(const struct be_canonical_state *canonical,
			   const struct be_root_image *root,
			   const struct be_r2_pool_desc *pool)
{
	be_size i;
	be_size found_count = 0U;
	be_size found_index = 0U;

	for (i = 0U; i < canonical->frame_count; ++i) {
		if (canonical->frames[i].id == root->root_table_frame) {
			found_index = i;
			++found_count;
		}
	}

	if (found_count == 0U)
		return BE_CHECK_UNDECLARED_MAPPING;
	if (found_count > 1U)
		return BE_CHECK_DUPLICATE_RESOURCE;

	{
		const struct be_frame_desc *frame =
			&canonical->frames[found_index];

		if (frame->class != BE_FRAME_ROOT_TABLE)
			return BE_CHECK_UNSUPPORTED;
		if (frame->owner_mask != BE_OWNER_MONITOR)
			return BE_CHECK_BINDING;
		if (frame->size != BE_SV39X4_POOL_SIZE)
			return BE_CHECK_UNSUPPORTED;
		if (frame->base != pool->base)
			return BE_CHECK_BINDING;
	}

	return BE_CHECK_OK;
}

/* --- Top-level R2 build --- */

enum be_check_result
be_r2_build(const struct be_runtime *runtime,
	    struct be_r2_pool_desc pools[BE_MAX_ROOTS],
	    struct be_r2_output *output)
{
	enum be_check_result rc;
	int scrub_safe[BE_MAX_ROOTS] = { 0, 0 };
	struct be_r2_result candidate[BE_MAX_ROOTS] = { { 0U, 0U },
							{ 0U, 0U } };
	be_size root_index;

	/* 1. Validate output is non-NULL. */
	if (output == (struct be_r2_output *)0)
		return BE_CHECK_NULL;

	/* 2. Validate output->state == EMPTY. */
	if (output->state != BE_R2_STATE_EMPTY)
		return BE_CHECK_INVALID_PHASE;

	/* 3. Zero output results. */
	output->results[0] = (struct be_r2_result){ 0U, 0U };
	output->results[1] = (struct be_r2_result){ 0U, 0U };

	/* 4. Validate runtime is non-NULL. */
	if (runtime == (const struct be_runtime *)0) {
		output->state = BE_R2_STATE_FAILED;
		return BE_CHECK_NULL;
	}

	/* 5. Validate pools pointer. */
	if (pools == (struct be_r2_pool_desc *)0) {
		output->state = BE_R2_STATE_FAILED;
		return BE_CHECK_NULL;
	}

	/* 6. Determine scrub safety. */
	scrub_safe[0] = pool_is_scrub_safe(&pools[0]);
	scrub_safe[1] = pool_is_scrub_safe(&pools[1]);

	/* 7. If either is not scrub-safe, best-effort scrub safe ones. */
	if (!scrub_safe[0] || !scrub_safe[1]) {
		if (scrub_safe[0])
			scrub_pool(&pools[0]);
		if (scrub_safe[1])
			scrub_pool(&pools[1]);
		output->state = BE_R2_STATE_FAILED;
		/* Determine error: NULL buf takes priority. */
		if (pools[0].buf == (be_u8 *)0 ||
		    pools[1].buf == (be_u8 *)0)
			return BE_CHECK_NULL;
		return BE_CHECK_UNSUPPORTED;
	}

	/* 8. Both are scrub-safe: scrub at attempt entry. */
	scrub_pool(&pools[0]);
	scrub_pool(&pools[1]);

	/* --- Full validation; any failure scrubs both and sets FAILED. --- */

	/* 9. Revalidate R1 integrity. */
	rc = revalidate_r1(runtime);
	if (rc != BE_CHECK_OK)
		goto fail;

	/* 10. Full pool-descriptor validation. */
	rc = validate_pool_desc(&pools[0]);
	if (rc != BE_CHECK_OK)
		goto fail;
	rc = validate_pool_desc(&pools[1]);
	if (rc != BE_CHECK_OK)
		goto fail;

	/* Distinct pool bases. */
	if (pools[0].base == pools[1].base) {
		rc = BE_CHECK_DUPLICATE_RESOURCE;
		goto fail;
	}

	/* Distinct host buffers. */
	if (pools[0].buf == pools[1].buf) {
		rc = BE_CHECK_DUPLICATE_RESOURCE;
		goto fail;
	}

	/* 11. Validate frozen fixed profile. */
	rc = validate_frozen_profile(&runtime->canonical,
				     &runtime->enforcement);
	if (rc != BE_CHECK_OK)
		goto fail;

	/* 12. Verify enforcement root count and domain ordering. */
	if (runtime->enforcement.root_count != 2U) {
		rc = BE_CHECK_INCOMPLETE;
		goto fail;
	}
	if (runtime->enforcement.roots[0].domain != BE_DOMAIN_MANAGEMENT) {
		rc = BE_CHECK_BINDING;
		goto fail;
	}
	if (runtime->enforcement.roots[1].domain != BE_DOMAIN_PROTECTED) {
		rc = BE_CHECK_BINDING;
		goto fail;
	}
	if (runtime->enforcement.roots[0].vmid != 0U ||
	    runtime->enforcement.roots[1].vmid != 0U) {
		rc = BE_CHECK_BINDING;
		goto fail;
	}
	if (runtime->enforcement.roots[0].mapping_count !=
		    FIXED_LEAVES_PER_ROOT ||
	    runtime->enforcement.roots[1].mapping_count !=
		    FIXED_LEAVES_PER_ROOT) {
		rc = BE_CHECK_INCOMPLETE;
		goto fail;
	}

	/* 13. Build and walk each root. */
	for (root_index = 0U; root_index < 2U; ++root_index) {
		const struct be_root_image *root =
			&runtime->enforcement.roots[root_index];
		struct be_r2_pool_desc *pool = &pools[root_index];
		struct be_r2_leaf_set walk_set = { 0U, { { 0U, 0U, 0U } } };
		be_size leaf_count = 0U;

		/* Pool-to-root binding. */
		rc = validate_root_pool_binding(&runtime->canonical, root,
						pool);
		if (rc != BE_CHECK_OK)
			goto fail;

		/* Build. */
		rc = build_one_root(&runtime->canonical, root, pool,
				    &leaf_count);
		if (rc != BE_CHECK_OK)
			goto fail;

		/* Walk. */
		rc = walk_one_root(pool, &runtime->canonical, root, &walk_set);
		if (rc != BE_CHECK_OK)
			goto fail;

		/* Store candidate result. */
		candidate[root_index].hgatp = BE_HGATP_MODE_SV39X4 |
					      (pool->base >> 12);
		candidate[root_index].leaf_count = leaf_count;
	}

	/* 14. Both roots passed: publish output. */
	output->results[0] = candidate[0];
	output->results[1] = candidate[1];
	output->state = BE_R2_STATE_BUILT;
	return BE_CHECK_OK;

fail:
	scrub_pool(&pools[0]);
	scrub_pool(&pools[1]);
	output->results[0] = (struct be_r2_result){ 0U, 0U };
	output->results[1] = (struct be_r2_result){ 0U, 0U };
	output->state = BE_R2_STATE_FAILED;
	return rc;
}

/* --- Public read-only re-walk --- */

enum be_check_result
be_r2_walk_and_check(const struct be_runtime *runtime,
		     const struct be_r2_pool_desc pools[BE_MAX_ROOTS],
		     const struct be_r2_output *output,
		     struct be_r2_leaf_set leaf_sets[BE_MAX_ROOTS])
{
	enum be_check_result rc;
	be_size root_index;

	/* NULL pointer checks. */
	if (runtime == (const struct be_runtime *)0)
		return BE_CHECK_NULL;
	if (pools == (const struct be_r2_pool_desc *)0)
		return BE_CHECK_NULL;
	if (output == (const struct be_r2_output *)0)
		return BE_CHECK_NULL;
	if (leaf_sets == (struct be_r2_leaf_set *)0)
		return BE_CHECK_NULL;

	/* Zero leaf sets at entry before any subsequent return. */
	for (root_index = 0U; root_index < BE_MAX_ROOTS; ++root_index)
		zero_bytes((be_u8 *)&leaf_sets[root_index],
			   (be_u64)sizeof(struct be_r2_leaf_set));

	/* Output must be BUILT. */
	if (output->state != BE_R2_STATE_BUILT)
		return BE_CHECK_INVALID_PHASE;

	/* Revalidate R1 integrity. */
	rc = revalidate_r1(runtime);
	if (rc != BE_CHECK_OK)
		return rc;

	/* Validate frozen profile. */
	rc = validate_frozen_profile(&runtime->canonical,
				     &runtime->enforcement);
	if (rc != BE_CHECK_OK)
		return rc;

	/* Validate pool descriptors: distinguish NULL buf from wrong size. */
	for (root_index = 0U; root_index < BE_MAX_ROOTS; ++root_index) {
		if (pools[root_index].buf == (const be_u8 *)0)
			return BE_CHECK_NULL;
		if (pools[root_index].buf_size != BE_SV39X4_POOL_SIZE)
			return BE_CHECK_UNSUPPORTED;
		rc = validate_pool_desc(&pools[root_index]);
		if (rc != BE_CHECK_OK)
			return rc;
	}

	/* Distinct pools. */
	if (pools[0].base == pools[1].base)
		return BE_CHECK_DUPLICATE_RESOURCE;
	if (pools[0].buf == pools[1].buf)
		return BE_CHECK_DUPLICATE_RESOURCE;

	/* Validate HGATP and leaf counts from output. */
	for (root_index = 0U; root_index < BE_MAX_ROOTS; ++root_index) {
		be_u64 expected_hgatp = BE_HGATP_MODE_SV39X4 |
					(pools[root_index].base >> 12);

		if (output->results[root_index].hgatp != expected_hgatp)
			return BE_CHECK_INTEGRITY;
		if (output->results[root_index].leaf_count !=
		    FIXED_LEAVES_PER_ROOT)
			return BE_CHECK_INTEGRITY;
	}

	/* Walk each root. */
	for (root_index = 0U; root_index < BE_MAX_ROOTS; ++root_index) {
		const struct be_root_image *root =
			&runtime->enforcement.roots[root_index];

		/* Pool-to-root binding. */
		rc = validate_root_pool_binding(&runtime->canonical, root,
						&pools[root_index]);
		if (rc != BE_CHECK_OK)
			return rc;

		/* Walk. */
		rc = walk_one_root(&pools[root_index], &runtime->canonical,
				   root, &leaf_sets[root_index]);
		if (rc != BE_CHECK_OK)
			return rc;
	}

	return BE_CHECK_OK;
}
