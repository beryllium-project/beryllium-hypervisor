// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: non-privileged host-side R0 freeze consistency checker for the
 *          fixed single-hart Beryllium runtime. It traces the eleven-resource
 *          core projection through the accepted Model 0.2 host validator and
 *          independently checks the full thirteen-resource layout, register
 *          matrix, and SBI allowlist for consistency.
 * Trust:   test tool only. It installs nothing and makes no runtime claim.
 *          QEMU G-stage behaviour remains NOT RUN for Beryllium.
 * Scope:   R0 freeze only. It exercises no privileged code and does not build,
 *          link, or execute an image.
 */
#include <stdio.h>

#include <be/manifest.h>
#include <be/state.h>
#include <be/r0-config.h>

#include "../../arch/riscv/be/r0-layout.h"
#include "../../arch/riscv/be/r0-registers.h"
#include "../../arch/riscv/be/r0-sbi.h"

static int failures;

static void fail(const char *message)
{
	printf("BE_R0_CHECK: FAIL %s\n", message);
	++failures;
}

static void require(int condition, const char *message)
{
	if (!condition)
		fail(message);
}

static be_u64 sv39x4_vpn2(be_u64 gpa)
{
	return (gpa >> 30) & BE_U64_C(0x7ff);
}

static be_u64 sv39x4_vpn1(be_u64 gpa)
{
	return (gpa >> 21) & BE_U64_C(0x1ff);
}

static be_u64 sv39x4_vpn0(be_u64 gpa)
{
	return (gpa >> 12) & BE_U64_C(0x1ff);
}

static int extents_overlap(const struct be_r0_extent *a,
			   const struct be_r0_extent *b)
{
	be_u64 a_end = a->base + a->size;
	be_u64 b_end = b->base + b->size;

	return a->base < b_end && b->base < a_end;
}

static int extent_contains(const struct be_r0_extent *extent, be_u64 base,
			   be_u64 size)
{
	return base >= extent->base &&
	       base + size <= extent->base + extent->size;
}

static be_u32 class_rights(enum be_r0_class class)
{
	switch (class) {
	case BE_R0_CLASS_MONITOR_CODE:
	case BE_R0_CLASS_GUEST_CODE:
		return BE_R0_RX;
	case BE_R0_CLASS_MONITOR_DATA:
	case BE_R0_CLASS_ROOT_POOL:
	case BE_R0_CLASS_TRUSTED_STACK:
	case BE_R0_CLASS_SAVED_STATE:
	case BE_R0_CLASS_PRIVATE:
	case BE_R0_CLASS_SHARED:
		return BE_R0_RW;
	case BE_R0_CLASS_OPENSBI:
	case BE_R0_CLASS_GUARD:
	default:
		return 0U;
	}
}

static void check_core_projection(void)
{
	const struct be_platform_inventory *inventory = be_r0_core_inventory();
	const struct be_proposal *proposal = be_r0_core_proposal();
	struct be_model model;
	be_u64 identity;

	be_model_reset(&model);
	require(be_check_inventory(inventory) == BE_CHECK_OK,
		"core inventory rejected by Model 0.2 validator");
	require(be_model_bind_inventory(&model, inventory) == BE_MODEL_OK,
		"core inventory bind failed");
	require(be_model_copy_proposal(&model, proposal) == BE_MODEL_OK,
		"core proposal copy failed");
	require(be_model_validate(&model) == BE_MODEL_OK,
		"core proposal canonicalization failed");
	require(be_model_seal(&model) == BE_MODEL_OK, "core seal failed");
	require(be_model_derive_roots(&model) == BE_MODEL_OK,
		"core root derivation failed");
	require(be_check_canonical(&model.canonical) == BE_CHECK_OK,
		"canonical recheck failed");
	require(be_check_enforcement(&model.canonical, &model.enforcement) ==
			BE_CHECK_OK,
		"enforcement recheck failed");

	identity = be_configuration_identity(&model.canonical);
	require(identity != 0U, "configuration identity is zero");
	require(model.canonical.configuration_id == identity,
		"canonical identity mismatch");
	require(model.enforcement.configuration_id == identity,
		"derived identity mismatch");

	/* Positive core-projection accesses. */
	require(be_model_activate(&model, BE_DOMAIN_MANAGEMENT) == BE_MODEL_OK,
		"management activation failed");
	require(be_model_access(&model, BE_R0_GPA_MANAGEMENT_PRIVATE,
				BE_RIGHT_READ | BE_RIGHT_WRITE) ==
			BE_MODEL_ALLOWED,
		"management private RW denied");
	require(be_model_access(&model, BE_R0_GPA_SHARED,
				BE_RIGHT_READ | BE_RIGHT_WRITE) ==
			BE_MODEL_ALLOWED,
		"management shared write denied");
	require(be_model_access(&model, BE_R0_GPA_PROTECTED_PRIVATE,
				BE_RIGHT_READ) == BE_MODEL_DENIED,
		"management reached protected private page");

	require(be_model_begin_switch(&model, BE_DOMAIN_PROTECTED) ==
			BE_MODEL_OK,
		"begin switch to protected failed");
	require(be_model_complete_fence(&model) == BE_MODEL_OK,
		"fence completion failed");
	require(be_model_finish_switch(&model) == BE_MODEL_OK,
		"finish switch to protected failed");
	require(be_model_access(&model, BE_R0_GPA_PROTECTED_PRIVATE,
				BE_RIGHT_READ | BE_RIGHT_WRITE) ==
			BE_MODEL_ALLOWED,
		"protected private RW denied");
	require(be_model_access(&model, BE_R0_GPA_SHARED, BE_RIGHT_READ) ==
			BE_MODEL_ALLOWED,
		"protected shared read denied");
	require(be_model_access(&model, BE_R0_GPA_SHARED,
				BE_RIGHT_READ | BE_RIGHT_WRITE) ==
			BE_MODEL_DENIED,
		"protected shared write allowed");
	require(be_model_access(&model, BE_R0_GPA_MANAGEMENT_PRIVATE,
				BE_RIGHT_READ) == BE_MODEL_DENIED,
		"protected reached management private page");
}

static void check_layout(void)
{
	be_size count = BE_ARRAY_SIZE(be_r0_extents);
	be_size index;
	be_size other;
	be_size runtime_resources = 0U;
	be_size core_resources = 0U;
	const struct be_r0_extent *monitor_data = (const struct be_r0_extent *)0;

	for (index = 0U; index < count; ++index) {
		const struct be_r0_extent *extent = &be_r0_extents[index];

		require((extent->base & (BE_PAGE_SIZE - 1U)) == 0U,
			"extent base is not page aligned");
		require((extent->size & (BE_PAGE_SIZE - 1U)) == 0U,
			"extent size is not page aligned");
		require(extent->size != 0U, "extent size is zero");
		require(extent->base >= BE_R0_DRAM_BASE &&
				extent->base + extent->size <= BE_R0_DRAM_END,
			"extent is outside pinned DRAM");
		if (extent->class == BE_R0_CLASS_ROOT_POOL) {
			require((extent->base & (BE_R0_SV39X4_ROOT_ALIGN - 1U)) ==
					0U,
				"root pool is not 16 KiB aligned");
			require(extent->size ==
					(be_u64)BE_R0_POOL_PAGES * BE_PAGE_SIZE,
				"root pool size mismatch");
		}
		if (extent->class == BE_R0_CLASS_MONITOR_DATA)
			monitor_data = extent;
		if (extent->id != 0U)
			++runtime_resources;
		if (extent->core_projection != 0U)
			++core_resources;
	}
	require(runtime_resources == 13U,
		"full runtime profile is not 13 resources");
	require(core_resources == 11U,
		"core projection is not 11 resources");

	for (index = 0U; index < count; ++index) {
		for (other = index + 1U; other < count; ++other) {
			if (extents_overlap(&be_r0_extents[index],
					    &be_r0_extents[other]))
				fail("frozen extents overlap");
		}
	}

	require(monitor_data != (const struct be_r0_extent *)0,
		"monitor data extent missing");
	if (monitor_data != (const struct be_r0_extent *)0)
		require(extent_contains(monitor_data, BE_R0_PA_DIAGNOSTIC,
					BE_PAGE_SIZE),
			"diagnostic page is not contained in monitor data");

	/* W^X: no extent is both writable and executable. */
	for (index = 0U; index < count; ++index) {
		be_u32 rights = class_rights(be_r0_extents[index].class);

		if ((rights & BE_RIGHT_WRITE) != 0U &&
		    (rights & BE_RIGHT_EXECUTE) != 0U)
			fail("extent violates W^X");
	}
}

static void check_roots(void)
{
	be_size root;

	for (root = 0U; root < BE_ARRAY_SIZE(be_r0_roots); ++root) {
		const struct be_r0_root *image = &be_r0_roots[root];
		be_size leaf;
		be_u64 vpn2;
		be_u64 vpn1;

		require(image->leaf_count != 0U &&
				image->leaf_count <= BE_U64_C(512),
			"root leaf count out of range");
		vpn2 = sv39x4_vpn2(image->leaves[0].gpa);
		vpn1 = sv39x4_vpn1(image->leaves[0].gpa);
		for (leaf = 0U; leaf < image->leaf_count; ++leaf) {
			const struct be_r0_leaf *entry = &image->leaves[leaf];
			be_size resource;
			int backed = 0;

			/*
			 * All leaves in the fixed set share one level-2 and one
			 * level-1 slot, so one level-1 and one level-0 table
			 * complete the pool: root(4) + L1(1) + L0(1) = 6 used,
			 * 2 spare of the 8 reserved pages.
			 */
			require(sv39x4_vpn2(entry->gpa) == vpn2,
				"leaf does not share the level-2 slot");
			require(sv39x4_vpn1(entry->gpa) == vpn1,
				"leaf does not share the level-1 slot");
			require((entry->rights & BE_RIGHT_WRITE) == 0U ||
					(entry->rights & BE_RIGHT_EXECUTE) ==
						0U,
				"leaf mapping violates W^X");

			/* Monitor exclusion: no leaf backs monitor-owned state. */
			for (resource = 0U;
			     resource < BE_ARRAY_SIZE(be_r0_extents);
			     ++resource) {
				const struct be_r0_extent *extent =
					&be_r0_extents[resource];

				if (entry->pa >= extent->base &&
				    entry->pa < extent->base + extent->size) {
					backed = 1;
					require(extent->monitor_owned == 0U,
						"leaf backs monitor-owned state");
				}
			}
			require(backed == 1, "leaf backing is unknown");
			(void)sv39x4_vpn0(entry->gpa);
		}
	}
}

static void check_registers(void)
{
	be_size count = BE_ARRAY_SIZE(be_r0_registers);
	be_size index;
	be_size group;
	be_size present[BE_R0_GROUP_COUNT] = { 0U };

	for (index = 0U; index < count; ++index) {
		const struct be_r0_register *entry = &be_r0_registers[index];

		++present[entry->group];
		if (entry->group == BE_R0_GROUP_FPV)
			require(entry->disposition == BE_R0_EXCLUDED,
				"floating-point/vector state is not excluded");
	}
	for (group = 0U; group < (be_size)BE_R0_GROUP_COUNT; ++group)
		require(present[group] != 0U,
			"a required register group has no entry");
}

static void check_sbi(void)
{
	be_size calls = BE_ARRAY_SIZE(be_r0_sbi_calls);
	be_size index;
	int base = 0;
	int dbcn = 0;
	int srst = 0;
	int fails_closed = 0;
	int terminus = 0;

	for (index = 0U; index < calls; ++index) {
		be_u64 eid = be_r0_sbi_calls[index].eid;

		if (eid == BE_R0_SBI_EID_BASE)
			base = 1;
		else if (eid == BE_R0_SBI_EID_DBCN)
			dbcn = 1;
		else if (eid == BE_R0_SBI_EID_SRST)
			srst = 1;
		else
			fail("SBI allowlist contains a forbidden extension");
	}
	require(base && dbcn && srst,
		"SBI allowlist is missing a required extension");

	for (index = 0U; index < BE_ARRAY_SIZE(be_r0_sbi_outcomes); ++index) {
		enum be_r0_sbi_disposition disposition =
			be_r0_sbi_outcomes[index].disposition;

		if (disposition == BE_R0_SBI_FAILS_CLOSED)
			fails_closed = 1;
		if (disposition == BE_R0_SBI_TERMINUS)
			terminus = 1;
	}
	require(fails_closed == 1,
		"missing fail-closed disposition for absent extension");
	require(terminus == 1, "missing non-returning SRST disposition");
	require(BE_R0_SBI_DBCN_MAX_ITERATIONS != 0U,
		"DBCN retry bound is zero");
}

int main(void)
{
	check_core_projection();
	check_layout();
	check_roots();
	check_registers();
	check_sbi();

	if (failures != 0) {
		printf("BE_R0_CHECK: FAIL failures=%d\n", failures);
		return 1;
	}
	printf("BE_R0_CHECK: PASS resources=13 core_projection=11 "
	       "roots=2 registers=%lu sbi_extensions=3\n",
	       (unsigned long)BE_ARRAY_SIZE(be_r0_registers));
	return 0;
}
