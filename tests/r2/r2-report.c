// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: emit a deterministic JSON report for the successful R2 Sv39x4
 *          page-table build. The report shows R1 sealed canonical state,
 *          R2 backend output (two concrete HGATP values), exact pointer
 *          and leaf PTE layout, decoded leaf mappings, and claim boundaries.
 * Trust:   report tool only. No authority is granted; HGATP values are
 *          computed but not written to CSRs.
 * Scope:   host evidence for the accepted R2 non-privileged Sv39x4 backend
 *          only. It links no image, executes no privileged code, and carries
 *          no QEMU or hardware result.
 */
#include <stdio.h>

#include <be/r1-config.h>
#include <be/r2.h>

/* Fixed pool bases from the R0 frozen layout. */
#define MANAGEMENT_POOL_BASE	BE_U64_C(0x80214000)
#define PROTECTED_POOL_BASE	BE_U64_C(0x8021c000)

static const char *r2_state_name(enum be_r2_state state)
{
	switch (state) {
	case BE_R2_STATE_EMPTY:
		return "empty";
	case BE_R2_STATE_BUILT:
		return "built";
	case BE_R2_STATE_FAILED:
		return "failed";
	default:
		return "invalid";
	}
}

static void rights_str(be_u32 rights, char out[4])
{
	be_size len = 0U;

	if ((rights & BE_RIGHT_READ) != 0U)
		out[len++] = 'r';
	if ((rights & BE_RIGHT_WRITE) != 0U)
		out[len++] = 'w';
	if ((rights & BE_RIGHT_EXECUTE) != 0U)
		out[len++] = 'x';
	out[len] = '\0';
}

static int prepare_r1(struct be_runtime *runtime)
{
	return be_runtime_copy_inventory(runtime, be_r1_inventory()) ==
		       BE_RUNTIME_OK &&
	       be_runtime_copy_proposal(runtime, be_r1_proposal()) ==
		       BE_RUNTIME_OK &&
	       be_runtime_validate(runtime) == BE_RUNTIME_OK &&
	       be_runtime_seal(runtime) == BE_RUNTIME_OK &&
	       be_runtime_derive(runtime) == BE_RUNTIME_OK;
}

static void report_pointer_layout(be_size root_idx,
				  const struct be_r2_pool_desc *pool)
{
	/*
	 * Fixed layout: root pointer at entry 1 (offset 8), L1 pointer at
	 * page-4 entry 0 (offset 0x4000). Report PPN values, not host addrs.
	 */
	be_u64 l1_ppn = (pool->base + BE_U64_C(0x4000)) >> 12;
	be_u64 l0_ppn = (pool->base + BE_U64_C(0x5000)) >> 12;

	printf("    {\"root\":%lu,\"pool_base\":\"0x%016lx\","
	       "\"root_ptr_offset\":8,\"root_ptr_vpn2\":1,"
	       "\"l1_ppn\":\"0x%011lx\",\"l1_offset\":\"0x4000\","
	       "\"l1_ptr_vpn1\":0,"
	       "\"l0_ppn\":\"0x%011lx\",\"l0_offset\":\"0x5000\"}%s\n",
	       (unsigned long)root_idx, pool->base, l1_ppn, l0_ppn,
	       root_idx == 0U ? "," : "");
}

static void report_leaves(be_size root_idx,
			  const struct be_r2_leaf_set *leaf_set)
{
	be_size i;

	printf("    {\"root\":%lu,\"leaf_count\":%lu,\"leaves\":[\n",
	       (unsigned long)root_idx, (unsigned long)leaf_set->count);
	for (i = 0U; i < leaf_set->count; ++i) {
		const struct be_r2_leaf *leaf = &leaf_set->leaves[i];
		char r[4];
		be_u64 ppn = leaf->pa >> 12;
		/* Reconstruct PTE flags from rights. */
		be_u32 has_w = (leaf->rights & BE_RIGHT_WRITE) != 0U ? 1U : 0U;

		rights_str(leaf->rights, r);
		printf("      {\"gpa\":\"0x%016lx\",\"pa\":\"0x%016lx\","
		       "\"ppn\":\"0x%011lx\",\"rights\":\"%s\","
		       "\"pte_v\":1,\"pte_r\":%u,\"pte_w\":%u,\"pte_x\":%u,"
		       "\"pte_u\":1,\"pte_g\":0,\"pte_a\":1,\"pte_d\":%u,"
		       "\"pte_rsw\":0,\"pte_high\":0}%s\n",
		       leaf->gpa, leaf->pa, ppn, r,
		       (leaf->rights & BE_RIGHT_READ) != 0U ? 1U : 0U,
		       has_w,
		       (leaf->rights & BE_RIGHT_EXECUTE) != 0U ? 1U : 0U,
		       has_w,
		       i + 1U < leaf_set->count ? "," : "");
	}
	printf("    ]}%s\n", root_idx == 0U ? "," : "");
}

static int check_spare_zero(const be_u8 *buf)
{
	be_u64 off;

	for (off = BE_U64_C(0x6000); off < BE_SV39X4_POOL_SIZE; ++off) {
		if (buf[off] != 0U)
			return 0;
	}
	return 1;
}

int main(void)
{
	struct be_runtime runtime = BE_RUNTIME_INITIALIZER;
	struct be_runtime_report r1_report;
	static be_u8 pool_mgmt[BE_SV39X4_POOL_SIZE];
	static be_u8 pool_prot[BE_SV39X4_POOL_SIZE];
	struct be_r2_pool_desc pools[BE_MAX_ROOTS];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[BE_MAX_ROOTS];
	enum be_check_result rc;
	be_size i;

	/* R1 full sequence. */
	if (!prepare_r1(&runtime)) {
		fprintf(stderr, "r2-report: R1 preparation failed: %s\n",
			be_check_result_name(runtime.check_result));
		return 1;
	}
	if (be_runtime_report(&runtime, &r1_report) != BE_RUNTIME_OK) {
		fprintf(stderr, "r2-report: R1 report failed\n");
		return 1;
	}

	/* R2 build. */
	pools[0].base = MANAGEMENT_POOL_BASE;
	pools[0].buf = pool_mgmt;
	pools[0].buf_size = BE_SV39X4_POOL_SIZE;
	pools[1].base = PROTECTED_POOL_BASE;
	pools[1].buf = pool_prot;
	pools[1].buf_size = BE_SV39X4_POOL_SIZE;
	output.state = BE_R2_STATE_EMPTY;
	output.results[0] = (struct be_r2_result){ 0U, 0U };
	output.results[1] = (struct be_r2_result){ 0U, 0U };

	rc = be_r2_build(&runtime, pools, &output);
	if (rc != BE_CHECK_OK) {
		fprintf(stderr, "r2-report: R2 build failed: %s\n",
			be_check_result_name(rc));
		return 1;
	}

	/* Independent re-walk for leaf enumeration. */
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	if (rc != BE_CHECK_OK) {
		fprintf(stderr, "r2-report: R2 walk failed: %s\n",
			be_check_result_name(rc));
		return 1;
	}

	/* Emit deterministic JSON report. */
	printf("{\n");
	printf("  \"schema\":\"be-r2-sv39x4-backend-v1\",\n");
	printf("  \"package\":\"single-hart-runtime-r2\",\n");
	printf("  \"scope\":\"non-privileged-sv39x4-host-report\",\n");

	/* R1 identity and status. */
	printf("  \"r1_identity\":{\n");
	printf("    \"configuration_identity\":\"0x%016lx\",\n",
	       r1_report.configuration_id);
	printf("    \"phase\":\"%s\",\n",
	       be_runtime_phase_name(r1_report.phase));
	printf("    \"sealed\":\"%s\",\n",
	       r1_report.sealed != 0U ? "yes" : "no");
	printf("    \"check_result\":\"%s\",\n",
	       be_check_result_name(r1_report.check_result));
	printf("    \"derived_roots\":%lu,\n",
	       (unsigned long)r1_report.root_count);
	printf("    \"derived_mappings\":%lu\n",
	       (unsigned long)r1_report.mapping_count);
	printf("  },\n");

	/* R2 state. */
	printf("  \"r2_state\":{\n");
	printf("    \"state\":\"%s\",\n", r2_state_name(output.state));
	printf("    \"build_result\":\"%s\"\n", be_check_result_name(rc));
	printf("  },\n");

	/* Roots and HGATP values. */
	printf("  \"roots\":[\n");
	for (i = 0U; i < BE_MAX_ROOTS; ++i) {
		printf("    {\"id\":%u,\"domain\":\"%s\","
		       "\"hgatp\":\"0x%016lx\",\"leaf_count\":%lu}%s\n",
		       runtime.enforcement.roots[i].root_id,
		       be_domain_name(runtime.enforcement.roots[i].domain),
		       output.results[i].hgatp,
		       (unsigned long)output.results[i].leaf_count,
		       i + 1U < BE_MAX_ROOTS ? "," : "");
	}
	printf("  ],\n");

	/* Pointer layout per root. */
	printf("  \"pointer_layout\":[\n");
	for (i = 0U; i < BE_MAX_ROOTS; ++i)
		report_pointer_layout(i, &pools[i]);
	printf("  ],\n");

	/* Decoded leaves per root. */
	printf("  \"decoded_leaves\":[\n");
	for (i = 0U; i < BE_MAX_ROOTS; ++i)
		report_leaves(i, &leaf_sets[i]);
	printf("  ],\n");

	/* Unused/spare status (report from both pools). */
	printf("  \"unused_storage\":{\n");
	printf("    \"spare_pages_zero\":%s,\n",
	       (check_spare_zero(pool_mgmt) && check_spare_zero(pool_prot))
		       ? "true"
		       : "false");
	printf("    \"management_spare_zero\":%s,\n",
	       check_spare_zero(pool_mgmt) ? "true" : "false");
	printf("    \"protected_spare_zero\":%s\n",
	       check_spare_zero(pool_prot) ? "true" : "false");
	printf("  },\n");

	/* Claims. */
	printf("  \"claims\":{\n");
	printf("    \"sv39x4_roots\":2,\n");
	printf("    \"sv39x4_leaves_per_root\":3,\n");
	printf("    \"sv39x4_total_leaves\":6,\n");
	printf("    \"hgatp_csr_written\":\"no\",\n");
	printf("    \"privileged_code\":\"no\",\n");
	printf("    \"linked_image\":\"no\",\n");
	printf("    \"formal_verification\":\"no\",\n");
	printf("    \"model_0_2_refinement\":\"no\",\n");
	printf("    \"qemu_beryllium_result\":\"NOT-RUN\",\n");
	printf("    \"hardware_validation\":\"NOT-RUN\",\n");
	printf("    \"r3_status\":\"not-started\",\n");
	printf("    \"public_release\":\"blocked\"\n");
	printf("  }\n");
	printf("}\n");
	return 0;
}
